#!/usr/bin/env python3
"""Generate a candidate port manifest from a depmap output directory.

Every row contains explicit unit_check and check_inputs placeholders.  Replace
both, listing only repository-local check-control assets, before the Phase 1
freeze; the candidate manifest-only hash printed here is not authorization.
"""
import argparse
import csv
import glob
import hashlib
import io
import ntpath
import os
import re
import sys
import tempfile


HEADERS = (
    "unit_id", "source_scope", "target_paths", "depends_on", "contract_ids",
    "rule_ids", "gap_ids", "check_inputs", "unit_check", "risk",
)
CHECK_PLACEHOLDER = "<fill: public-entry check with negative probe>"
CHECK_INPUTS_PLACEHOLDER = "<fill: repository-local check-control assets before freeze>"
BATCH = re.compile(r"^# batch\s+(\d+)(?:\s+(CYCLE))?\s*$")


def safe_relative(path, label="source", allow_dot=False):
    if not path or "\0" in path or "\t" in path or "\r" in path or "\n" in path:
        raise ValueError("malformed %s path: %r" % (label, path))
    drive, _tail = ntpath.splitdrive(path)
    if os.path.isabs(path) or ntpath.isabs(path) or drive:
        raise ValueError("absolute %s path is forbidden: %s" % (label, path))
    parts = path.replace("\\", "/").split("/")
    if ".." in parts:
        raise ValueError("%s traversal is forbidden: %s" % (label, path))
    normalized = os.path.normpath(path).replace(os.sep, "/")
    if normalized in ("", ".") and not (allow_dot and normalized == "."):
        raise ValueError("%s path must name a file: %s" % (label, path))
    if "," in normalized or glob.has_magic(normalized):
        raise ValueError(
            "unsupported filename in %s path %r: commas and glob metacharacters "
            "cannot be encoded safely by the current manifest schema; rename the "
            "path before generating a manifest" % (label, path))
    return normalized


def read_batches(path):
    batches, current, cycle = [], None, False
    seen = set()
    with open(path, encoding="utf-8") as handle:
        for number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            match = BATCH.match(line)
            if match:
                if current is not None:
                    if not current:
                        raise ValueError("empty batch before line %d" % number)
                    batches.append((current, cycle))
                expected = len(batches) + 1
                if int(match.group(1)) != expected:
                    raise ValueError("non-sequential batch number at line %d: expected %d" %
                                     (number, expected))
                current, cycle = [], bool(match.group(2))
            elif line.startswith("#"):
                raise ValueError("malformed depmap batch header at line %d: %s" %
                                 (number, line))
            elif current is None:
                raise ValueError("file entry before first batch at line %d" % number)
            else:
                source = safe_relative(line)
                if source in seen:
                    raise ValueError("duplicate source entry at line %d: %s" %
                                     (number, source))
                seen.add(source)
                current.append(source)
    if current is not None:
        if not current:
            raise ValueError("empty final batch")
        batches.append((current, cycle))
    if not batches:
        raise ValueError("order.txt contains no batches")
    return batches


def parse_ext(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("extension mapping must be FROM=TO")
    source, target = value.split("=", 1)
    if not source:
        raise argparse.ArgumentTypeError("extension mapping source cannot be empty")
    if "/" in source or "\\" in source or "/" in target or "\\" in target:
        raise argparse.ArgumentTypeError("extension mappings cannot contain paths")
    return source, target


def target_for(source, target_root, ext_map):
    source = safe_relative(source)
    target_root = safe_relative(target_root, "target root", allow_dot=True)
    mapped = source
    for old in sorted(ext_map, key=len, reverse=True):
        if mapped.endswith(old):
            mapped = mapped[:-len(old)] + ext_map[old]
            break
    return safe_relative(os.path.join(target_root, mapped), "derived target")


def read_edges(path):
    if not os.path.isfile(path):
        raise ValueError(
            "edges.tsv is required; depmap emits it with a from/to header even "
            "for a true zero-edge map")
    edges = []
    seen = set()
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        header = next(reader, None)
        if header != ["from", "to"]:
            raise ValueError("edges.tsv must have exactly from and to columns")
        for number, values in enumerate(reader, 2):
            if len(values) != 2 or not all(value.strip() for value in values):
                raise ValueError("malformed edges.tsv row %d: expected two non-empty columns" %
                                 number)
            edge = (safe_relative(values[0].strip()),
                    safe_relative(values[1].strip()))
            if edge in seen:
                raise ValueError("duplicate edge at edges.tsv row %d: %s -> %s" %
                                 (number, edge[0], edge[1]))
            seen.add(edge)
            edges.append(edge)
    return edges


def graph_components(nodes, edges):
    """Return iterative Tarjan SCCs for depmap consistency validation."""
    adjacency = {node: set() for node in nodes}
    for source, target in edges:
        adjacency[source].add(target)
    index, low, active, stack, components, counter = {}, {}, set(), [], [], 0
    for start in sorted(nodes):
        if start in index:
            continue
        index[start] = low[start] = counter
        counter += 1
        stack.append(start)
        active.add(start)
        frames = [[start, iter(sorted(adjacency[start])), None]]
        while frames:
            node, children, parent = frames[-1]
            try:
                child = next(children)
            except StopIteration:
                frames.pop()
                if parent is not None:
                    low[parent] = min(low[parent], low[node])
                if low[node] == index[node]:
                    component = set()
                    while True:
                        member = stack.pop()
                        active.remove(member)
                        component.add(member)
                        if member == node:
                            break
                    components.append(component)
                continue
            if child not in index:
                index[child] = low[child] = counter
                counter += 1
                stack.append(child)
                active.add(child)
                frames.append([child, iter(sorted(adjacency[child])), node])
            elif child in active:
                low[node] = min(low[node], index[child])
    return components


def validate_order(batches, edges, file_units):
    self_edges = sorted(source for source, target in edges if source == target)
    if self_edges:
        raise ValueError("edges.tsv contains unsupported self-cycle(s): " +
                         ", ".join(self_edges))
    components = graph_components(file_units, edges)
    component_by_file = {path: component for component in components
                         for path in component}
    for index, (files, marked_cycle) in enumerate(batches, 1):
        component = component_by_file[files[0]]
        if set(files) != component:
            if len(component) > 1:
                raise ValueError(
                    "multi-file SCC is not represented as one CYCLE batch: %s" %
                    ", ".join(sorted(component)))
            raise ValueError("batch %d groups files that are not one SCC" % index)
        expected_cycle = len(component) > 1
        if marked_cycle != expected_cycle:
            raise ValueError("batch %d cycle marker is inconsistent with edges.tsv" %
                             index)
    for source, target in edges:
        source_unit, target_unit = file_units[source], file_units[target]
        if source_unit != target_unit and target_unit >= source_unit:
            raise ValueError(
                "edge violates dependency-first order: %s -> %s (batch %d must "
                "come after batch %d)" %
                (source, target, source_unit, target_unit))


def render(rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=HEADERS, delimiter="\t",
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def atomic_write(path, data):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".manifest.", suffix=".tmp",
                                              dir=parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", required=True, dest="map_dir")
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--map-ext", action="append", default=[], type=parse_ext,
                        metavar="FROM=TO")
    parser.add_argument("--output", "--out", dest="output",
                        help="write atomically to PATH (default: manifest TSV on stdout)")
    args = parser.parse_args(argv)

    try:
        safe_relative(args.target_root, "target root", allow_dot=True)
        batches = read_batches(os.path.join(args.map_dir, "order.txt"))
        edges = read_edges(os.path.join(args.map_dir, "edges.tsv"))
        ext_map = dict(args.map_ext)
        file_units = {}
        for index, (files, _cycle) in enumerate(batches, 1):
            for path in files:
                file_units[path] = index

        unknown = sorted({endpoint for edge in edges for endpoint in edge
                          if endpoint not in file_units})
        if unknown:
            raise ValueError("edges.tsv references unknown source entries: " +
                             ", ".join(unknown))
        validate_order(batches, edges, file_units)

        dependencies = {index: set() for index in range(1, len(batches) + 1)}
        for source, target in edges:
            source_unit, target_unit = file_units[source], file_units[target]
            if source_unit != target_unit:
                dependencies[source_unit].add(target_unit)

        rows = []
        target_owners = {}
        for index, (files, cycle) in enumerate(batches, 1):
            derived = [target_for(path, args.target_root, ext_map) for path in files]
            identities = [source for source, target in zip(files, derived)
                          if os.path.normcase(os.path.normpath(source)) ==
                          os.path.normcase(os.path.normpath(target))]
            if identities:
                raise ValueError("identity substitution is not a port for unit U-%d: %s" %
                                 (index, ", ".join(identities)))
            for source, target in zip(files, derived):
                key = os.path.normcase(os.path.normpath(target))
                if key in target_owners:
                    raise ValueError("derived target collision %s from %s and %s" %
                                     (target, target_owners[key], source))
                target_owners[key] = source
            rows.append({
                "unit_id": "U-%d" % index,
                "source_scope": ", ".join(files),
                "target_paths": ", ".join(derived),
                "depends_on": ", ".join("U-%d" % item
                                          for item in sorted(dependencies[index])),
                "contract_ids": "",
                "rule_ids": "",
                "gap_ids": "",
                "check_inputs": CHECK_INPUTS_PLACEHOLDER,
                "unit_check": CHECK_PLACEHOLDER,
                "risk": "high" if cycle else "low",
            })
        data = render(rows)
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1

    digest = hashlib.sha256(data).hexdigest()
    if args.output:
        try:
            atomic_write(args.output, data)
        except OSError as exc:
            print("error: %s" % exc, file=sys.stderr)
            return 1
        print("wrote CANDIDATE manifest to %s; fill unit_check and check_inputs "
              "before freeze at the Phase 1 gate" % args.output)
    else:
        sys.stdout.buffer.write(data)
    print("candidate manifest-only sha256 %s (not an authorization bundle)" % digest,
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
