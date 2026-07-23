#!/usr/bin/env python3
"""Integration unit U-CLI: command-line interface.

Wires the config system (U-CONFIG), the v1->v2 translator (U-API), and the
execution engine (U-EXEC) behind the legacy `plan`/`run` commands. Emits
canonical JSON on stdout, `error: <message>` on stderr, and preserves the
legacy exit codes (0 success, 2 handled error / argparse failure).
Zero runtime dependencies.
"""
import argparse
import json
import sys

from config import load_config
from translate import translate
from execute import execute


def main(argv=None):
    p = argparse.ArgumentParser(prog="legacy-adapter")
    p.add_argument("command", choices=["plan", "run"])
    p.add_argument("--config")
    p.add_argument("--request", required=True)
    p.add_argument("--timeout-ms", type=int)
    p.add_argument("--retries", type=int)
    p.add_argument("--region")
    p.add_argument("--sequence", default="200")
    a = p.parse_args(argv)
    try:
        cfg = load_config(a.config, a.timeout_ms, a.retries, a.region)
        req = json.loads(a.request)
        plan = translate(req, cfg)
        out = plan if a.command == "plan" else execute(plan, a.sequence)
        print(json.dumps(out, sort_keys=True, separators=(",", ":")))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
