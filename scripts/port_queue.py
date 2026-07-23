#!/usr/bin/env python3
"""Mechanical work queue over .port/manifest.tsv (stdlib only).

The manifest's ``unit_check`` column is executable shell input.  Its required
``check_inputs`` column names the repository-local control files (scripts,
configs, lockfiles, and goldens) that authorize those checks.  Checks run only
with both ``--run-checks`` and ``--authorize-manifest SHA256``.  The accepted
SHA-256 is an authorization bundle over exact manifest bytes plus the names
and bytes of all expanded check inputs; obtain it with the non-executing
``digest`` command.  Existence-only classification reports targets as
``present``, never ``done``.

Usage, from the target repo root:
  port_queue.py digest [--manifest PATH]
  port_queue.py status --existence-only
  port_queue.py status --run-checks --authorize-manifest SHA256
  port_queue.py next [--batch N] MODE
  port_queue.py verify MODE

``target_paths`` and ``check_inputs`` are comma-separated.  Safe globs and
spaces are supported; literal commas cannot be encoded.  Check-input globs
must match contained regular non-symlink files and cannot overlap another
distinct declaration.  Target implementation outputs are not check inputs by
default.  Absolute paths, traversal, symlink components, and overlapping
target ownership are rejected.

Self-test: python3 scripts/tests/test_port_queue.py
"""
import argparse
import csv
import fnmatch
import glob
import hashlib
import hmac
import io
import json
import ntpath
import os
import signal
import stat
import subprocess
import sys
import tempfile

MANIFEST = os.path.join(".port", "manifest.tsv")
CHECK_TIMEOUT = 300
CHECK_OUTPUT_LIMIT = 64 * 1024
REQUIRED_COLUMNS = (
    "unit_id", "source_scope", "target_paths", "depends_on", "contract_ids",
    "rule_ids", "gap_ids", "check_inputs", "unit_check", "risk",
)
REQUIRED_VALUES = (
    "unit_id", "source_scope", "target_paths", "check_inputs", "unit_check",
    "risk",
)
RISKS = {"low", "medium", "high"}
BUNDLE_DOMAIN = b"port-queue-authorization-bundle\0v1\0"


class ManifestError(ValueError):
    """The manifest cannot be used as a queue."""


class Terminated(BaseException):
    def __init__(self, signum):
        super().__init__(signum)
        self.signum = signum


def dependencies(row):
    return [value for value in row.get("depends_on", "").replace(",", " ").split()
            if value]


def targets(row):
    return [path.strip() for path in row.get("target_paths", "").split(",")
            if path.strip()]


def check_input_declarations(row):
    value = row.get("check_inputs", "")
    parts = value.split(",")
    if any(not part.strip() for part in parts):
        raise ManifestError(
            "check_inputs contains an empty comma-separated declaration")
    return [part.strip() for part in parts]


def manifest_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def _target_key(path):
    return os.path.normcase(os.path.normpath(path)).replace(os.sep, "/")


def _has_symlink_component(repo_root, relative, stop_at_magic=False):
    current = repo_root
    for component in relative.replace("\\", "/").split("/"):
        if not component or component == ".":
            continue
        if stop_at_magic and glob.has_magic(component):
            break
        current = os.path.join(current, component)
        if os.path.lexists(current) and os.path.islink(current):
            return True
    return False


def _validate_target_path(path, repo_root):
    if not path:
        raise ManifestError("empty target path")
    if "\0" in path:
        raise ManifestError("target contains a NUL byte")
    drive, _tail = ntpath.splitdrive(path)
    if os.path.isabs(path) or ntpath.isabs(path) or drive:
        raise ManifestError("absolute target path is forbidden: %s" % path)
    parts = path.replace("\\", "/").split("/")
    if ".." in parts:
        raise ManifestError("target traversal is forbidden: %s" % path)
    normalized = os.path.normpath(path)
    if normalized in ("", "."):
        raise ManifestError("target must name a path below the repository root")
    absolute = os.path.abspath(os.path.join(repo_root, normalized))
    try:
        contained = os.path.commonpath((repo_root, absolute)) == repo_root
    except ValueError:
        contained = False
    if not contained:
        raise ManifestError("target escapes repository root: %s" % path)
    if _has_symlink_component(repo_root, normalized, stop_at_magic=True):
        raise ManifestError("target has a symlink component: %s" % path)
    return normalized


def _validate_check_input_pattern(path, repo_root):
    if not path:
        raise ManifestError("empty check input")
    if "\0" in path:
        raise ManifestError("check input contains a NUL byte")
    if "\\" in path:
        raise ManifestError(
            "check input must use forward slashes (backslashes are ambiguous): %s" %
            path)
    drive, _tail = ntpath.splitdrive(path)
    if os.path.isabs(path) or ntpath.isabs(path) or drive:
        raise ManifestError("absolute check input path is forbidden: %s" % path)
    parts = path.split("/")
    if ".." in parts:
        raise ManifestError("check input traversal is forbidden: %s" % path)
    normalized = os.path.normpath(path).replace(os.sep, "/")
    if normalized in ("", "."):
        raise ManifestError("check input must name a file below the repository root")
    absolute = os.path.abspath(os.path.join(repo_root, normalized))
    try:
        contained = os.path.commonpath((repo_root, absolute)) == repo_root
    except ValueError:
        contained = False
    if not contained:
        raise ManifestError("check input escapes repository root: %s" % path)
    if _has_symlink_component(repo_root, normalized, stop_at_magic=True):
        raise ManifestError("check input has a symlink component: %s" % path)
    return normalized


def _read_regular_check_input(relative, repo_root):
    if _has_symlink_component(repo_root, relative):
        raise ManifestError("check input has a symlink component: %s" % relative)
    absolute = os.path.join(repo_root, relative)
    try:
        before = os.lstat(absolute)
    except OSError as exc:
        raise ManifestError("cannot inspect check input %s: %s" %
                            (relative, exc)) from exc
    if stat.S_ISLNK(before.st_mode):
        raise ManifestError("check input is a symlink: %s" % relative)
    if not stat.S_ISREG(before.st_mode):
        raise ManifestError("check input is not a regular file: %s" % relative)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise ManifestError("cannot open check input %s safely: %s" %
                            (relative, exc)) from exc
    try:
        opened = os.fstat(descriptor)
        identity = lambda info: (info.st_dev, info.st_ino, info.st_mode)
        if identity(before) != identity(opened) or not stat.S_ISREG(opened.st_mode):
            raise ManifestError("check input changed while opening: %s" % relative)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (identity(opened) != identity(after)
                or opened.st_size != after.st_size
                or getattr(opened, "st_mtime_ns", opened.st_mtime) !=
                getattr(after, "st_mtime_ns", after.st_mtime)):
            raise ManifestError("check input changed while reading: %s" % relative)
        data = b"".join(chunks)
        if len(data) != after.st_size:
            raise ManifestError("check input size changed while reading: %s" % relative)
        return data
    finally:
        os.close(descriptor)


def _authorization_files(rows, repo_root):
    declarations = {}
    for row in rows:
        seen_in_row = set()
        for raw in check_input_declarations(row):
            normalized = _validate_check_input_pattern(raw, repo_root)
            key = _target_key(normalized)
            if key in seen_in_row:
                raise ManifestError(
                    "duplicate check input declaration in unit %s: %s" %
                    (row["unit_id"], normalized))
            seen_in_row.add(key)
            declarations.setdefault(key, normalized)

    expanded = {}
    for declaration_key, pattern in sorted(declarations.items()):
        matches = glob.glob(pattern, root_dir=repo_root, recursive=True)
        if not matches:
            raise ManifestError("check input matches zero files: %s" % pattern)
        pattern_matches = set()
        for match in matches:
            normalized = _validate_check_input_pattern(match, repo_root)
            key = _target_key(normalized)
            if key in pattern_matches:
                continue
            pattern_matches.add(key)
            previous = expanded.get(key)
            if previous is not None and previous[0] != declaration_key:
                raise ManifestError(
                    "ambiguous check input %s matched by %s and %s" %
                    (normalized, declarations[previous[0]], pattern))
            expanded[key] = (declaration_key, normalized)
    files = []
    for key in sorted(expanded):
        relative = expanded[key][1]
        files.append((relative, _read_regular_check_input(relative, repo_root)))
    return files


def authorization_bundle_digest(data, rows, repo_root):
    """Hash a versioned, length-framed manifest/check-control bundle."""
    digest = hashlib.sha256()
    digest.update(BUNDLE_DOMAIN)

    def frame(label, value):
        digest.update(label)
        digest.update(len(value).to_bytes(8, "big"))
        digest.update(value)

    frame(b"manifest\0", data)
    for relative, contents in _authorization_files(rows, repo_root):
        frame(b"path\0", relative.encode("utf-8"))
        frame(b"bytes\0", contents)
    return digest.hexdigest()


def _validate_target_ownership(rows, repo_root):
    def components(value):
        return tuple(part for part in value.split("/") if part not in ("", "."))

    def static_prefix(value):
        result = []
        for part in components(value):
            if glob.has_magic(part):
                break
            result.append(part)
        return tuple(result)

    def prefix_of(left, right):
        return len(left) <= len(right) and right[:len(left)] == left

    def glob_overlap(left, right):
        left_prefix, right_prefix = static_prefix(left), static_prefix(right)
        return prefix_of(left_prefix, right_prefix) or prefix_of(
            right_prefix, left_prefix)

    def glob_concrete_overlap(pattern, concrete):
        pattern_key = pattern.replace(os.sep, "/")
        concrete_key = concrete.replace(os.sep, "/")
        # Treat the concrete path as a possible directory owner.  Determine
        # whether the segment-wise glob language can consume that directory
        # prefix and then match at least one descendant.  In particular,
        # out/**/*.txt overlaps concrete directory out/generated, while
        # out/left/*.txt remains disjoint from out/right.
        pattern_parts = components(pattern_key)
        concrete_parts = components(concrete_key)
        states = {0}
        for concrete_part in concrete_parts:
            closure = set(states)
            changed = True
            while changed:
                changed = False
                for index in tuple(closure):
                    if (index < len(pattern_parts)
                            and pattern_parts[index] == "**"
                            and index + 1 not in closure):
                        closure.add(index + 1)
                        changed = True
            following = set()
            for index in closure:
                if index >= len(pattern_parts):
                    continue
                part = pattern_parts[index]
                if part == "**":
                    following.add(index)
                elif fnmatch.fnmatchcase(concrete_part, part):
                    following.add(index + 1)
            states = following
            if not states:
                return False
        return bool(states)

    owners = []
    for row in rows:
        row_targets = targets(row)
        if not row_targets:
            raise ManifestError("unit %s has no target paths" % row["unit_id"])
        for raw in row_targets:
            normalized = _validate_target_path(raw, repo_root)
            key = _target_key(normalized)
            magical = glob.has_magic(normalized)
            for previous, previous_key, previous_magical, owner in owners:
                if key == previous_key:
                    raise ManifestError(
                        "duplicate normalized target %s owned by %s and %s" %
                        (normalized, owner, row["unit_id"]))
                if magical and previous_magical:
                    overlap = glob_overlap(key, previous_key)
                elif magical:
                    overlap = glob_concrete_overlap(key, previous_key)
                elif previous_magical:
                    overlap = glob_concrete_overlap(previous_key, key)
                else:
                    try:
                        overlap = os.path.commonpath((key, previous_key)) in (
                            key, previous_key)
                    except ValueError:
                        overlap = False
                if overlap:
                    raise ManifestError(
                        "overlapping target ownership %s (%s) and %s (%s)" %
                        (previous, owner, normalized, row["unit_id"]))
            owners.append((normalized, key, magical, row["unit_id"]))


def load(manifest, repo_root=None, data=None):
    repo_root = os.path.abspath(repo_root or os.getcwd())
    if data is None:
        data = manifest_bytes(manifest)
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ManifestError("manifest is not valid UTF-8: %s" % exc) from exc
    lines = text.splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        lines.pop(0)
    if not lines:
        raise ManifestError("manifest has no header")

    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter="\t")
    header = next(reader, [])
    if len(header) != len(set(header)):
        raise ManifestError("manifest header has duplicate columns")
    missing = [name for name in REQUIRED_COLUMNS if name not in header]
    surplus = [name for name in header if name not in REQUIRED_COLUMNS]
    if missing:
        raise ManifestError("manifest missing required columns: " + ", ".join(missing))
    if surplus:
        raise ManifestError("manifest has surplus columns: " + ", ".join(surplus))
    if len(header) != len(REQUIRED_COLUMNS):
        raise ManifestError("manifest header has the wrong number of columns")

    rows = []
    for line_number, values in enumerate(reader, 2):
        if not values or not any(value.strip() for value in values):
            continue
        if len(values) != len(header):
            kind = "surplus" if len(values) > len(header) else "missing"
            raise ManifestError("manifest row %d has %s TSV columns (expected %d, got %d)" %
                                (line_number, kind, len(header), len(values)))
        row = dict(zip(header, values))
        for name in REQUIRED_VALUES:
            row[name] = row[name].strip()
            if not row[name]:
                raise ManifestError("manifest row %d has an empty %s" %
                                    (line_number, name))
        if row["risk"] not in RISKS:
            raise ManifestError("manifest row %d has invalid risk %r; expected low, medium, or high" %
                                (line_number, row["risk"]))
        seen_check_inputs = set()
        for declaration in check_input_declarations(row):
            normalized = _validate_check_input_pattern(declaration, repo_root)
            key = _target_key(normalized)
            if key in seen_check_inputs:
                raise ManifestError(
                    "manifest row %d has duplicate check input declaration %s" %
                    (line_number, normalized))
            seen_check_inputs.add(key)
        rows.append(row)
    if not rows:
        raise ManifestError("manifest has a valid header but zero data rows")

    seen = set()
    duplicates = []
    for row in rows:
        unit_id = row["unit_id"]
        if unit_id in seen and unit_id not in duplicates:
            duplicates.append(unit_id)
        seen.add(unit_id)
    if duplicates:
        raise ManifestError("manifest has duplicate unit_id(s): " + ", ".join(duplicates))

    unknown = []
    for row in rows:
        for dependency in dependencies(row):
            if dependency == row["unit_id"]:
                raise ManifestError("unit %s depends on itself" % row["unit_id"])
            if dependency not in seen:
                unknown.append("%s -> %s" % (row["unit_id"], dependency))
    if unknown:
        raise ManifestError("depends_on references unknown unit_id(s): " +
                            ", ".join(unknown))

    adjacency = {row["unit_id"]: dependencies(row) for row in rows}
    state = {}  # 1 means active in the current DFS; 2 means fully visited.
    for start in adjacency:
        if state.get(start) == 2:
            continue
        active_path, positions = [start], {start: 0}
        state[start] = 1
        frames = [[start, iter(adjacency[start])]]
        cycle = None
        while frames:
            unit_id, children = frames[-1]
            try:
                dependency = next(children)
            except StopIteration:
                frames.pop()
                state[unit_id] = 2
                positions.pop(unit_id, None)
                active_path.pop()
                continue
            dependency_state = state.get(dependency, 0)
            if dependency_state == 1:
                cycle = active_path[positions[dependency]:] + [dependency]
                break
            if dependency_state == 2:
                continue
            state[dependency] = 1
            positions[dependency] = len(active_path)
            active_path.append(dependency)
            frames.append([dependency, iter(adjacency[dependency])])
        if cycle:
            raise ManifestError(
                "dependency cycle detected: %s; cycles must be resolved in the "
                "manifest: either merge the units or declare one-directional "
                "depends_on; see references/mapping.md" % " -> ".join(cycle))
    _validate_target_ownership(rows, repo_root)
    return rows


def _safe_matches(path, repo_root):
    normalized = _validate_target_path(path, repo_root)
    matches = glob.glob(normalized, root_dir=repo_root, recursive=True)
    safe = []
    for match in matches:
        _validate_target_path(match, repo_root)
        if _has_symlink_component(repo_root, match):
            raise ManifestError("target match has a symlink component: %s" % match)
        safe.append(os.path.join(repo_root, match))
    return safe


def _nonempty_file(path):
    return os.path.isfile(path) and not os.path.islink(path) and os.path.getsize(path) > 0


def _target_present(path, repo_root):
    normalized = _validate_target_path(path, repo_root)
    if glob.has_magic(normalized):
        matches = [match for match in _safe_matches(normalized, repo_root)
                   if os.path.isfile(match)]
        return bool(matches) and all(_nonempty_file(match) for match in matches)
    absolute = os.path.join(repo_root, normalized)
    if _has_symlink_component(repo_root, normalized):
        raise ManifestError("target has a symlink component: %s" % path)
    if os.path.isdir(absolute):
        for root, directories, files in os.walk(absolute, followlinks=False):
            directories[:] = [name for name in directories
                              if not os.path.islink(os.path.join(root, name))]
            if any(_nonempty_file(os.path.join(root, name)) for name in files):
                return True
        return False
    return _nonempty_file(absolute)


def files_present(row, repo_root=None):
    repo_root = os.path.abspath(repo_root or os.getcwd())
    paths = targets(row)
    return bool(paths) and all(_target_present(path, repo_root) for path in paths)


def _kill_and_wait(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait()
    except BaseException:
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()


def run_check(row, timeout=CHECK_TIMEOUT, repo_root=None):
    """Return ``(passed, reason, capped_output)`` for an authorized shell check."""
    command = (row.get("unit_check") or "").strip()
    if not command:
        return False, "empty", b""
    repo_root = os.path.abspath(repo_root or os.getcwd())
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            command, shell=True, cwd=repo_root, stdout=output,
            stderr=subprocess.STDOUT, start_new_session=True)
        try:
            returncode = process.wait(timeout=timeout)
            reason = "" if returncode == 0 else "exit %d" % returncode
        except subprocess.TimeoutExpired:
            _kill_and_wait(process)
            returncode, reason = process.returncode, "timeout"
        except BaseException:
            _kill_and_wait(process)
            raise
        output.seek(0)
        captured = output.read(CHECK_OUTPUT_LIMIT)
    return returncode == 0, reason, captured


def check_passes(row, timeout=CHECK_TIMEOUT, repo_root=None):
    return run_check(row, timeout, repo_root)[0]


def classify(rows, run_checks=False, check_timeout=CHECK_TIMEOUT, repo_root=None,
             check_results=None, authorization_guard=None):
    repo_root = os.path.abspath(repo_root or os.getcwd())
    completion = "done" if run_checks else "present"
    names = (completion, "pending", "blocked", "failed-check")
    states = {name: [] for name in names}
    state_by_id = {}
    by_id = {row["unit_id"]: row for row in rows}

    for row in rows:
        start = row["unit_id"]
        if start in state_by_id:
            continue
        frames = [(start, False)]
        while frames:
            unit_id, expanded = frames.pop()
            if unit_id in state_by_id:
                continue
            if not expanded:
                frames.append((unit_id, True))
                frames.extend((item, False) for item in reversed(
                    dependencies(by_id[unit_id])) if item not in state_by_id)
                continue
            current = by_id[unit_id]
            dependency_states = [state_by_id[item]
                                 for item in dependencies(current)]
            if any(item != completion for item in dependency_states):
                state = "blocked"
            elif not files_present(current, repo_root):
                state = "pending"
            elif run_checks:
                if authorization_guard is not None:
                    authorization_guard()
                result = run_check(current, check_timeout, repo_root)
                if check_results is not None:
                    check_results[unit_id] = result
                state = completion if result[0] else "failed-check"
            else:
                state = completion
            state_by_id[unit_id] = state
    for row in rows:
        states[state_by_id[row["unit_id"]]].append(row)
    return states


def _print_status(states, total, run_checks):
    completion = "done" if run_checks else "present"
    summary = "%d %s / %d pending / %d blocked / %d failed-check / %d total" % (
        len(states[completion]), completion, len(states["pending"]),
        len(states["blocked"]), len(states["failed-check"]), total)
    if not run_checks:
        summary += " (existence only; no unit checks were run)"
    print(summary)


def verify(rows, run_checks=False, check_timeout=CHECK_TIMEOUT, repo_root=None,
           authorization_guard=None):
    if not run_checks:
        states = classify(rows, False, check_timeout, repo_root)
        for row in states["pending"]:
            print("FAIL %s: missing or zero-byte target" % row["unit_id"], file=sys.stderr)
        for row in states["blocked"]:
            print("BLOCKED %s: dependency targets are not present" % row["unit_id"],
                  file=sys.stderr)
        valid = len(states["present"])
        print("existence audit only; unit checks NOT run — %d/%d units present" %
              (valid, len(rows)))
        return 0 if valid == len(rows) else 1

    results = {}
    states = classify(rows, True, check_timeout, repo_root, results,
                      authorization_guard)
    for row in states["pending"]:
        print("FAIL %s: missing or zero-byte target" % row["unit_id"], file=sys.stderr)
    for row in states["failed-check"]:
        reason = results.get(row["unit_id"], (False, "", b""))[1]
        print("FAIL %s: unit_check failed%s" %
              (row["unit_id"], ": %s" % reason if reason else ""),
              file=sys.stderr)
    for row in states["blocked"]:
        print("BLOCKED %s: dependency is not done" % row["unit_id"], file=sys.stderr)
    failed = len(states["failed-check"])
    print("verified %d/%d units; %d failed-check" %
          (len(states["done"]), len(rows), failed))
    return 0 if len(states["done"]) == len(rows) else 1


def positive_int(value):
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return parsed


def _mode_error(parser, message):
    parser.error(message + "; choose --existence-only, or --run-checks "
                 "--authorize-manifest SHA256, using only the SHA-256 explicitly "
                 "approved for the manifest/check-input bundle at the manifest gate")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog=("check_inputs is a comma-separated list of repository-relative "
                "regular control files or safe globs. Literal commas cannot be "
                "escaped. Globs must match and may not ambiguously overlap. The "
                "authorization bundle intentionally excludes mutable implementation "
                "outputs under test unless explicitly declared."))
    parser.add_argument("command", choices=["digest", "status", "next", "verify"])
    parser.add_argument("--manifest", default=MANIFEST)
    parser.add_argument("--batch", type=positive_int, default=10)
    parser.add_argument("--check-timeout", type=positive_int, default=CHECK_TIMEOUT,
                        help="seconds before an authorized unit_check is killed")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--run-checks", action="store_true",
                       help="run unit checks (requires exact bundle authorization)")
    modes.add_argument("--existence-only", action="store_true",
                       help="inspect target presence without claiming checks passed")
    modes.add_argument("--check", action="store_true", dest="legacy_check",
                       help=argparse.SUPPRESS)
    modes.add_argument("--skip-checks", action="store_true", dest="legacy_existence",
                       help=argparse.SUPPRESS)
    parser.add_argument("--authorize-manifest", metavar="SHA256",
                        help=("authorize checks from exactly this manifest plus its "
                              "declared check-input names and bytes (legacy flag name)"))
    args = parser.parse_args(argv)

    try:
        data = manifest_bytes(args.manifest)
    except OSError as error:
        print("error: %s" % error, file=sys.stderr)
        return 2
    if args.command == "digest":
        if (args.run_checks or args.existence_only or args.legacy_check or
                args.legacy_existence or args.authorize_manifest):
            parser.error("digest does not accept a queue execution mode")
        try:
            rows = load(args.manifest, os.getcwd(), data)
            digest = authorization_bundle_digest(data, rows, os.getcwd())
        except (OSError, ManifestError) as error:
            print("error: %s" % error, file=sys.stderr)
            return 2
        print(digest)
        return 0

    run_checks = args.run_checks or args.legacy_check
    existence_only = args.existence_only or args.legacy_existence
    if not run_checks and not existence_only:
        _mode_error(parser, "refusing ambiguous queue classification")
    authorization = (args.authorize_manifest or "").lower()
    if run_checks:
        if not authorization:
            _mode_error(parser, "--run-checks requires --authorize-manifest SHA256")
    elif args.authorize_manifest:
        parser.error("--authorize-manifest is meaningful only with --run-checks")

    try:
        rows = load(args.manifest, os.getcwd(), data)
        if run_checks:
            digest = authorization_bundle_digest(data, rows, os.getcwd())
    except (OSError, ManifestError) as error:
        print("error: %s" % error, file=sys.stderr)
        return 2
    if run_checks and not hmac.compare_digest(authorization, digest):
        parser.error("authorization bundle digest does not match the current manifest "
                     "and check inputs; no checks were run")

    authorization_guard = None
    if run_checks:
        def authorization_guard():
            current_data = manifest_bytes(args.manifest)
            current_rows = load(args.manifest, os.getcwd(), current_data)
            current_digest = authorization_bundle_digest(
                current_data, current_rows, os.getcwd())
            if not hmac.compare_digest(authorization, current_digest):
                raise ManifestError(
                    "authorization bundle changed immediately before check execution; "
                    "no further checks were run")

    try:
        if args.command == "verify":
            return verify(rows, run_checks, args.check_timeout, os.getcwd(),
                          authorization_guard)

        states = classify(rows, run_checks=run_checks,
                          check_timeout=args.check_timeout, repo_root=os.getcwd(),
                          authorization_guard=authorization_guard)
    except (OSError, ManifestError) as error:
        print("error: %s" % error, file=sys.stderr)
        return 2
    completion = "done" if run_checks else "present"
    if args.command == "status":
        _print_status(states, len(rows), run_checks)
        completed_ids = {row["unit_id"] for row in states[completion]}
        for row in states["blocked"]:
            waiting = [dependency for dependency in dependencies(row)
                       if dependency not in completed_ids]
            print("  blocked %s: waiting on %s" %
                  (row["unit_id"], ", ".join(waiting)))
        return 0

    actionable = {row["unit_id"] for state in ("pending", "failed-check")
                  for row in states[state]}
    selected = [row for row in rows if row["unit_id"] in actionable][:args.batch]
    batch = [{"unit_id": row["unit_id"],
              "source_scope": row.get("source_scope", ""),
              "target_paths": targets(row),
              "check_inputs": check_input_declarations(row),
              "unit_check": row.get("unit_check", "")}
             for row in selected]
    print(json.dumps(batch, indent=2))
    return 0


def _terminated(signum, _frame):
    raise Terminated(signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _terminated)
    try:
        sys.exit(main())
    except Terminated as exc:
        sys.exit(128 + exc.signum)
