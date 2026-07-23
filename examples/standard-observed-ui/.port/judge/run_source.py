#!/usr/bin/env python3
"""Source adapter — drives the observed-only source fixture and writes RAW
(unredacted) per-scenario observations into a caller-provided directory.

This adapter is the ONLY thing authorized to operate the source, and only
within the approved interaction matrix (GET /health, POST /interact, isolated
session IDs). Its output is raw evidence and must be written to the outside-
repository quarantine, never directly into .port/. The capture pipeline
(capture.py) is responsible for scanning, redacting, admitting, and deleting.

Usage: run_source.py <base_url> <out_dir> [scenario_id ...]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import _driver  # noqa: E402
import _scenarios  # noqa: E402


def main():
    base_url = sys.argv[1]
    out_dir = sys.argv[2]
    ids = sys.argv[3:] or _scenarios.ALL_IDS
    os.makedirs(out_dir, exist_ok=True)
    for sid in ids:
        steps = _scenarios.SCENARIOS[sid]
        obs = _driver.run_scenario(base_url, "cap-%s" % sid, steps)
        with open(os.path.join(out_dir, "%s.json" % sid), "w", encoding="utf-8") as f:
            json.dump({"scenario_id": sid, "observations": obs}, f, indent=2)
    print("captured %d scenario(s) -> %s" % (len(ids), out_dir))


if __name__ == "__main__":
    main()
