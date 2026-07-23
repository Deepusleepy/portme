#!/usr/bin/env python3
"""Port adapter — drives the port through its own public HTTP surface, applies
the approved normalization (pocketscan redaction + version mask), and writes
per-scenario normalized observations under results/port-obs/.

Starts an ephemeral instance of the port on a loopback port unless PT_BASE is
set to an already-running instance.

Usage: run_port.py <out_dir> [scenario_id ...]
"""
import json
import os
import sys
import threading

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import _driver  # noqa: E402
import _scenarios  # noqa: E402


def main():
    out_dir = sys.argv[1]
    ids = sys.argv[2:] or _scenarios.ALL_IDS
    os.makedirs(out_dir, exist_ok=True)

    base = os.environ.get("PT_BASE")
    httpd = None
    if not base:
        import pocket_tasks
        httpd = pocket_tasks.make_server("127.0.0.1", 0)
        port = httpd.server_address[1]
        base = "http://127.0.0.1:%d" % port
        threading.Thread(target=httpd.serve_forever, daemon=True).start()

    try:
        for sid in ids:
            steps = _scenarios.SCENARIOS[sid]
            obs = _driver.run_scenario(base, "port-%s" % sid, steps)
            obs = _driver.normalize(obs)
            with open(os.path.join(out_dir, "%s.json" % sid), "w", encoding="utf-8") as f:
                json.dump({"scenario_id": sid, "observations": obs}, f, indent=2)
    finally:
        if httpd is not None:
            httpd.shutdown()
    print("port observations for %d scenario(s) -> %s" % (len(ids), out_dir))


if __name__ == "__main__":
    main()
