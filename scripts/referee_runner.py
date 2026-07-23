#!/usr/bin/env python3
"""Run a serialized referee command and atomically retain immutable results."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time


class LockBusy(RuntimeError):
    pass


class ResultIntegrityError(RuntimeError):
    pass


class Terminated(BaseException):
    def __init__(self, signum):
        super().__init__(signum)
        self.signum = signum


def positive(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return parsed


def _read_regular(path, limit=None):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except FileNotFoundError:
        raise
    except OSError as exc:
        raise ValueError("cannot safely open regular file: %s" % exc) from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("is not a regular file")
        if limit is not None and info.st_size > limit:
            raise ValueError("file exceeds %d-byte integrity limit" % limit)
        chunks, total = [], 0
        while True:
            chunk = os.read(descriptor, 128 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if limit is not None and total > limit:
                raise ValueError("file exceeds %d-byte integrity limit" % limit)
            chunks.append(chunk)
        return b"".join(chunks), info
    finally:
        os.close(descriptor)


def _read_lock(path):
    try:
        raw, info = _read_regular(path, 16 * 1024)
        data = json.loads(raw.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("payload is not an object")
        if data.get("schema", 1) != 1:
            raise ValueError("unsupported lock schema")
        pid = data.get("pid")
        timestamp = data.get("timestamp")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise ValueError("pid is invalid")
        if (isinstance(timestamp, bool) or
                not isinstance(timestamp, (int, float)) or
                not math.isfinite(timestamp)):
            raise ValueError("timestamp is invalid")
        return raw, pid, max(0.0, time.time() - timestamp), (
            info.st_dev, info.st_ino)
    except FileNotFoundError:
        raise
    except (OSError, UnicodeDecodeError, ValueError, TypeError,
            json.JSONDecodeError) as exc:
        raise LockBusy(
            "referee lock is malformed or unsafe; inspect it and remove it "
            "manually only after proving its owner is dead: %s (%s)" %
            (path, exc)) from exc


def _pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _acquire_lock(port, lock, payload, stale_seconds, wait):
    deadline = None
    if isinstance(wait, float):
        deadline = time.monotonic() + wait
    while True:
        descriptor, candidate_name = tempfile.mkstemp(
            prefix=".referee.lock.%d." % os.getpid(), dir=port)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
                os.fchmod(handle.fileno(), 0o444)
            try:
                os.link(candidate_name, lock)
            except FileExistsError:
                pass
            else:
                return lock, payload
        except FileExistsError:
            pass
        finally:
            try:
                os.unlink(candidate_name)
            except FileNotFoundError:
                pass

        try:
            raw, pid, age, identity = _read_lock(lock)
        except FileNotFoundError:
            continue
        if age > stale_seconds and not _pid_alive(pid):
            try:
                current = os.lstat(lock)
                if (current.st_dev, current.st_ino) != identity:
                    continue
                current_raw, _info = _read_regular(lock, 16 * 1024)
                if current_raw != raw:
                    continue
                lock.unlink()
                print("warning: took over stale referee lock", file=sys.stderr)
            except FileNotFoundError:
                pass
            except ValueError as exc:
                raise LockBusy(
                    "referee lock changed into an unsafe form; inspect it and "
                    "remove it manually only after proving its owner is dead: "
                    "%s (%s)" % (lock, exc)) from exc
            continue
        if not wait:
            owner = " (live pid %d)" % pid if _pid_alive(pid) else ""
            raise LockBusy("referee lock is held%s: %s" % (owner, lock))
        if deadline is not None and time.monotonic() >= deadline:
            raise LockBusy("timed out waiting for referee lock: %s" % lock)
        time.sleep(0.1)


def acquire_lock(port, stale_seconds, wait=False):
    port.mkdir(parents=True, exist_ok=True)
    lock = port / "referee.lock"
    payload = (json.dumps({"pid": os.getpid(), "schema": 1,
                           "timestamp": time.time()}, sort_keys=True) +
               "\n").encode("utf-8")
    try:
        return _acquire_lock(port, lock, payload, stale_seconds, wait)
    except BaseException:
        # A signal can arrive after the atomic link succeeds but before the
        # caller receives ownership. Remove only our exact payload.
        release_lock(lock, payload)
        raise


def release_lock(lock, payload):
    try:
        raw, _info = _read_regular(lock, 16 * 1024)
        if raw == payload:
            lock.unlink()
    except (FileNotFoundError, ValueError):
        pass


def next_result_number(root):
    root.mkdir(parents=True, exist_ok=True)
    info = os.lstat(root)
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise ResultIntegrityError("referee result root is not a real directory: %s" % root)
    root.chmod(stat.S_IMODE(info.st_mode) | stat.S_IWUSR | stat.S_IXUSR)
    numbers = [int(path.name) for path in root.iterdir() if path.name.isdigit()]
    return max(numbers, default=0) + 1


def _kill_and_wait(process):
    if process is None:
        return
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    while process.poll() is None:
        try:
            process.wait()
        except BaseException:
            continue


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _secure_digest(path):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ValueError("cannot safely open regular file: %s" % exc) from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("is not a regular file")
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 128 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        return digest.hexdigest(), info
    finally:
        os.close(descriptor)


def _write_text(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def _finish_result(temporary, final, command, returncode, started, timeout):
    _write_text(temporary / "exit.txt", "%d\n" % returncode)
    evidence = {
        name: _sha256(temporary / name)
        for name in ("cmd.txt", "output.txt", "exit.txt")
    }
    ended = time.time()
    metadata = {
        "command": command,
        "duration_seconds": max(0.0, ended - started),
        "ended_at": ended,
        "exit_code": returncode,
        "pid": os.getpid(),
        "sha256": evidence,
        "started_at": started,
        "timeout_seconds": timeout,
    }
    _write_text(temporary / "metadata.json",
                json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    marker = {
        "metadata_sha256": _sha256(temporary / "metadata.json"),
        "schema": 1,
    }
    _write_text(temporary / "COMPLETE",
                json.dumps(marker, sort_keys=True) + "\n")
    for path in temporary.iterdir():
        if path.is_file():
            path.chmod(0o444)
    temporary.chmod(0o555)
    os.rename(temporary, final)


def _remove_temporary(path):
    if path is None or not path.exists():
        return
    try:
        path.chmod(0o700)
        for child in path.iterdir():
            if not child.is_symlink():
                child.chmod(0o600)
        shutil.rmtree(path)
    except OSError:
        pass


def run_command(args):
    if not args.command:
        print("error: command required after --", file=sys.stderr)
        return 2
    command = args.command[1:] if args.command[0] == "--" else args.command
    if not command:
        print("error: command required after --", file=sys.stderr)
        return 2
    port = Path(args.port)
    try:
        lock, payload = acquire_lock(port, args.stale_seconds, args.wait)
    except LockBusy as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2

    process, temporary = None, None
    try:
        root = port / "referee"
        number = next_result_number(root)
        final = root / ("%04d" % number)
        temporary = Path(tempfile.mkdtemp(
            prefix=".%04d.%d." % (number, os.getpid()), suffix=".tmp", dir=root))
        _write_text(temporary / "cmd.txt", shlex.join(command) + "\n")
        output_path = temporary / "output.txt"
        returncode = 127
        started = time.time()
        try:
            with output_path.open("wb") as output:
                try:
                    process = subprocess.Popen(command, stdout=output,
                                               stderr=subprocess.STDOUT,
                                               start_new_session=True)
                    try:
                        returncode = process.wait(timeout=args.timeout)
                    except subprocess.TimeoutExpired:
                        _kill_and_wait(process)
                        returncode = 124
                        output.write(("\n[referee_runner] timeout after %g seconds\n" %
                                      args.timeout).encode("utf-8"))
                except OSError as exc:
                    output.write(("referee_runner: %s\n" % exc).encode("utf-8"))
        except BaseException:
            _kill_and_wait(process)
            raise
        _finish_result(temporary, final, command, returncode, started, args.timeout)
        temporary = None
        print(final)
        return returncode
    except (OSError, ResultIntegrityError) as exc:
        print("error: cannot publish referee result: %s" % exc, file=sys.stderr)
        return 2
    finally:
        _kill_and_wait(process)
        _remove_temporary(temporary)
        release_lock(lock, payload)


RESULT_FILES = {"cmd.txt", "output.txt", "exit.txt", "metadata.json", "COMPLETE"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXIT_RE = re.compile(br"^-?(?:0|[1-9][0-9]*)\n$")


def _verified_result(path):
    directory = os.lstat(path)
    if stat.S_ISLNK(directory.st_mode) or not stat.S_ISDIR(directory.st_mode):
        raise ResultIntegrityError("numeric result is not a real directory")
    if stat.S_IMODE(directory.st_mode) != 0o555:
        raise ResultIntegrityError("result directory mode is not 0555")
    names = set(os.listdir(path))
    if names != RESULT_FILES:
        missing = sorted(RESULT_FILES - names)
        extra = sorted(names - RESULT_FILES)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("extra " + ", ".join(extra))
        raise ResultIntegrityError("critical file set mismatch: " + "; ".join(details))

    data, digests = {}, {}
    for name in sorted(RESULT_FILES):
        try:
            if name in ("COMPLETE", "metadata.json", "exit.txt"):
                content, info = _read_regular(path / name, 1024 * 1024)
                data[name] = content
                digests[name] = hashlib.sha256(content).hexdigest()
            else:
                digests[name], info = _secure_digest(path / name)
        except ValueError as exc:
            raise ResultIntegrityError("unsafe %s: %s" % (name, exc)) from exc
        if stat.S_IMODE(info.st_mode) != 0o444:
            raise ResultIntegrityError("%s mode is not 0444" % name)

    try:
        marker = json.loads(data["COMPLETE"].decode("utf-8"))
        metadata = json.loads(data["metadata.json"].decode("utf-8"))
    except (UnicodeDecodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ResultIntegrityError("invalid JSON integrity metadata: %s" % exc) from exc
    if (not isinstance(marker, dict) or set(marker) != {"metadata_sha256", "schema"}
            or marker.get("schema") != 1
            or not isinstance(marker.get("metadata_sha256"), str)
            or not SHA256_RE.fullmatch(marker["metadata_sha256"])):
        raise ResultIntegrityError("COMPLETE marker has invalid schema or digest")
    if marker["metadata_sha256"] != digests["metadata.json"]:
        raise ResultIntegrityError("COMPLETE metadata digest mismatch")
    if not isinstance(metadata, dict):
        raise ResultIntegrityError("metadata.json root is not an object")
    evidence = metadata.get("sha256")
    evidence_names = {"cmd.txt", "output.txt", "exit.txt"}
    if not isinstance(evidence, dict) or set(evidence) != evidence_names:
        raise ResultIntegrityError("metadata.json has an invalid sha256 file set")
    for name in sorted(evidence_names):
        if (not isinstance(evidence[name], str) or
                not SHA256_RE.fullmatch(evidence[name]) or
                evidence[name] != digests[name]):
            raise ResultIntegrityError("metadata hash mismatch for %s" % name)
    if not EXIT_RE.fullmatch(data["exit.txt"]):
        raise ResultIntegrityError("exit.txt is not a canonical integer")
    exit_code = int(data["exit.txt"].strip())
    recorded = metadata.get("exit_code")
    if isinstance(recorded, bool) or not isinstance(recorded, int) or recorded != exit_code:
        raise ResultIntegrityError("metadata and exit.txt exit codes are inconsistent")
    return exit_code


def last_result(args):
    root = Path(args.port) / "referee"
    try:
        root_info = os.lstat(root)
        if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
            raise ResultIntegrityError("referee result root is not a real directory")
        candidates = sorted((root / entry.name for entry in os.scandir(root)
                             if entry.name.isdigit()),
                            key=lambda path: int(path.name), reverse=True)
    except FileNotFoundError:
        candidates = []
    except (OSError, ResultIntegrityError) as exc:
        print("error: cannot inspect referee results: %s" % exc, file=sys.stderr)
        return 1
    for latest in candidates:
        try:
            info = os.lstat(latest)
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise ResultIntegrityError("numeric result is not a real directory")
            exit_code = _verified_result(latest)
        except (OSError, ResultIntegrityError) as exc:
            print("error: invalid referee result %s: %s" % (latest, exc),
                  file=sys.stderr)
            return 1
        print("%s exit %d" % (latest, exit_code))
        return 0
    print("error: no completed referee results", file=sys.stderr)
    return 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--port", default=".port")
    run.add_argument("--timeout", type=positive, default=1800.0)
    run.add_argument("--stale-seconds", type=positive, default=3600.0)
    run.add_argument("--wait", nargs="?", const=True, default=False, type=positive,
                     metavar="SECONDS",
                     help="wait for the lock, indefinitely when no value is supplied")
    run.add_argument("command", nargs=argparse.REMAINDER)
    run.set_defaults(func=run_command)
    last = subparsers.add_parser("last")
    last.add_argument("--port", default=".port")
    last.set_defaults(func=last_result)
    args = parser.parse_args(argv)
    return args.func(args)


def _terminated(signum, _frame):
    raise Terminated(signum)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _terminated)
    try:
        sys.exit(main())
    except Terminated as exc:
        sys.exit(128 + exc.signum)
