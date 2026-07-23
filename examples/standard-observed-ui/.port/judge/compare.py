#!/usr/bin/env python3
"""Compare — the mechanical verdict engine for the Pocket Tasks judge.

For each scenario it loads:
  - the admitted golden fixture:  fixtures/<id>/observation.json   (redacted at
    admission from the source capture)
  - the port observation:         results/port-obs/<id>.json       (produced by
    run_port.py, already normalized)

Both sides pass through _driver.normalize() so the comparison is symmetric and
idempotent, then are diffed structurally. Any missing/extra/changed field fails
the scenario. Emits per-scenario verdicts and summary counts (a failure queue).

Usage: compare.py [scenario_id ...]
Exit status: 0 all pass, 1 any fail/missing.
"""
import json
import os
import sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import _driver  # noqa: E402
import _scenarios  # noqa: E402

FIX = os.path.join(HERE, "fixtures")
PORT_OBS = os.path.join(HERE, "results", "port-obs")


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _diff(a, b, path=""):
    """Return list of human-readable difference strings."""
    diffs = []
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        return ["%s: type %s != %s" % (path or "/", type(a).__name__, type(b).__name__)]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                diffs.append("%s/%s: extra in port" % (path, k))
            elif k not in b:
                diffs.append("%s/%s: missing in port" % (path, k))
            else:
                diffs += _diff(a[k], b[k], "%s/%s" % (path, k))
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append("%s: length %d != %d" % (path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            diffs += _diff(x, y, "%s[%d]" % (path, i))
    else:
        if a != b:
            diffs.append("%s: %r != %r" % (path or "/", a, b))
    return diffs


def main():
    ids = sys.argv[1:] or _scenarios.ALL_IDS
    passed = failed = missing = 0
    lines = []
    for sid in ids:
        gpath = os.path.join(FIX, sid, "observation.json")
        ppath = os.path.join(PORT_OBS, "%s.json" % sid)
        if not os.path.exists(gpath):
            lines.append("MISSING-GOLDEN %s" % sid)
            missing += 1
            continue
        if not os.path.exists(ppath):
            lines.append("MISSING-PORT %s" % sid)
            missing += 1
            continue
        golden = _driver.normalize(_load(gpath)["observations"])
        port = _driver.normalize(_load(ppath)["observations"])
        d = _diff(golden, port)
        if d:
            failed += 1
            lines.append("FAIL %s" % sid)
            for line in d[:12]:
                lines.append("    %s" % line)
        else:
            passed += 1
            lines.append("PASS %s" % sid)
    print("\n".join(lines))
    print("\nsummary: pass=%d fail=%d missing=%d total=%d" %
          (passed, failed, missing, len(ids)))
    return 0 if (failed == 0 and missing == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
