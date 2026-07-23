#!/usr/bin/env python3
"""pocketscan — a small, explicitly named local secret/PII scanner (stdlib only).

This is the scanner referenced by the observed-only capture pipeline. It is
deliberately simple and fully local: no network, no external services. It scans
regular files against a versioned regex ruleset and can emit findings or write
redacted copies.

Usage:
  pocketscan.py --version
  pocketscan.py scan   --rules <rules.json> [--json] <path> [<path> ...]
  pocketscan.py redact --rules <rules.json> --out <dir> <path> [<path> ...]

Exit status: 0 = clean (no findings), 1 = findings present, 2 = usage/error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

TOOL = "pocketscan"
TOOL_VERSION = "1.0.0"


def load_rules(path):
    with open(path, "rb") as f:
        raw = f.read()
    cfg = json.loads(raw.decode("utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    compiled = [(r["id"], re.compile(r["pattern"]), r.get("mask", "[REDACTED]"))
                for r in cfg["rules"]]
    return cfg, compiled, digest


def _iter_files(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for name in sorted(files):
                    yield os.path.join(root, name)
        else:
            yield p


def scan(paths, compiled):
    findings = []
    for fp in _iter_files(paths):
        try:
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            findings.append({"file": fp, "rule": "read-error", "detail": str(e)})
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for rid, rx, _mask in compiled:
                for m in rx.finditer(line):
                    findings.append({"file": fp, "line": line_no, "rule": rid,
                                     "match_sha256": hashlib.sha256(
                                         m.group(0).encode()).hexdigest()[:16]})
    return findings


def redact(paths, compiled, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for fp in _iter_files(paths):
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        for _rid, rx, mask in compiled:
            text = rx.sub(mask, text)
        dest = os.path.join(out_dir, os.path.basename(fp))
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)
        written.append(dest)
    return written


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--version":
        print("%s %s" % (TOOL, TOOL_VERSION))
        return 0
    ap = argparse.ArgumentParser(prog=TOOL)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "redact"):
        sp = sub.add_parser(name)
        sp.add_argument("--rules", required=True)
        sp.add_argument("paths", nargs="+")
        if name == "scan":
            sp.add_argument("--json", action="store_true")
        else:
            sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    _cfg, compiled, digest = load_rules(args.rules)

    if args.cmd == "scan":
        findings = scan(args.paths, compiled)
        report = {
            "tool": TOOL, "tool_version": TOOL_VERSION,
            "ruleset_sha256": digest,
            "scanned": args.paths,
            "finding_count": len(findings),
            "findings": findings,
        }
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("%s %s ruleset=%s findings=%d" %
                  (TOOL, TOOL_VERSION, digest[:12], len(findings)))
            for fnd in findings:
                print("  %s:%s %s" % (fnd.get("file"), fnd.get("line", "-"),
                                      fnd.get("rule")))
        return 1 if findings else 0

    if args.cmd == "redact":
        written = redact(args.paths, compiled, args.out)
        print("%s redact ruleset=%s wrote=%d -> %s" %
              (TOOL, digest[:12], len(written), args.out))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
