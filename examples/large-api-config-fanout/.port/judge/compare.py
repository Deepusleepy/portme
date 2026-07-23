#!/usr/bin/env python3
"""Differential judge for the legacy_adapter port.

Runs the readable source and the port under identical argv/env and compares the
whole public CLI surface: stdout (canonical JSON), stderr, and exit code.

Usage:
  compare.py --mode source            # dump source observations only (baseline)
  compare.py --mode diff              # run source+port, assert exact equality
  compare.py --mode diff --target DIR # compare against an alternate port dir
                                      # (used for mutation sensitivity checks)

Exit 0 = all scenarios matched (diff) / baseline captured (source).
Exit 1 = at least one mismatch.
Stdlib only; no runtime dependencies.
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SOURCE = os.path.join(TARGET_ROOT, "source", "legacy_adapter.py")
FIX = os.path.join(HERE, "fixtures")


def f(name):
    return os.path.join(FIX, name)


# Each scenario: id, args (list after the program), env overrides (dict or None).
# Config paths are derived from this example so source and port resolve identically
# after the example is copied anywhere.
SCENARIOS = [
    # --- plan: config precedence and defaults ---
    ("J-01-plan-defaults", ["plan", "--request", '{"user_id":"u1","payload":{"a":1}}'], None),
    ("J-02-plan-int-uid", ["plan", "--request", '{"user_id":42,"payload":[1,2]}'], None),
    ("J-03-plan-config-file", ["plan", "--config", f("base.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-04-plan-env-over-file", ["plan", "--config", f("base.json"), "--request", '{"user_id":"u","payload":1}'], {"PORTME_TIMEOUT_MS": "250"}),
    ("J-05-plan-cli-over-env-over-file", ["plan", "--config", f("full.json"), "--timeout-ms", "999", "--request", '{"user_id":"u","payload":1}'], {"PORTME_TIMEOUT_MS": "250"}),
    ("J-06-plan-env-only", ["plan", "--request", '{"user_id":"u","payload":1}'], {"PORTME_TIMEOUT_MS": "777"}),
    ("J-07-plan-cli-region", ["plan", "--region", "eu-west", "--request", '{"user_id":"u","payload":1}'], None),
    ("J-08-plan-cli-retries0", ["plan", "--retries", "0", "--request", '{"user_id":"u","payload":1}'], None),
    ("J-09-plan-config-region", ["plan", "--config", f("region.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-10-plan-strict-inert", ["plan", "--config", f("strict.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-11-plan-full-config", ["plan", "--config", f("full.json"), "--request", '{"user_id":"u","payload":1}'], None),
    # --- config validation errors ---
    ("J-12-unknown-keys", ["plan", "--config", f("unknown.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-13-timeout-zero-config", ["plan", "--config", f("badtimeout.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-14-timeout-neg-cli", ["plan", "--timeout-ms", "-5", "--request", '{"user_id":"u","payload":1}'], None),
    ("J-15-retries-hi-config", ["plan", "--config", f("badretries.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-16-retries-hi-cli", ["plan", "--retries", "6", "--request", '{"user_id":"u","payload":1}'], None),
    ("J-17-region-bad-config", ["plan", "--config", f("badregion.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-18-region-bad-cli", ["plan", "--region", "apac", "--request", '{"user_id":"u","payload":1}'], None),
    ("J-19-env-not-int", ["plan", "--request", '{"user_id":"u","payload":1}'], {"PORTME_TIMEOUT_MS": "abc"}),
    ("J-20-config-missing-file", ["plan", "--config", f("does-not-exist.json"), "--request", '{"user_id":"u","payload":1}'], None),
    ("J-21-config-bad-json", ["plan", "--config", f("badjson.json"), "--request", '{"user_id":"u","payload":1}'], None),
    # --- request validation ---
    ("J-22-request-extra-key", ["plan", "--request", '{"user_id":"u","payload":1,"extra":2}'], None),
    ("J-23-request-missing-key", ["plan", "--request", '{"user_id":"u"}'], None),
    ("J-24-uid-list", ["plan", "--request", '{"user_id":[1],"payload":1}'], None),
    ("J-25-uid-bool", ["plan", "--request", '{"user_id":true,"payload":1}'], None),
    ("J-26-request-bad-json", ["plan", "--request", "{bad}"], None),
    # --- run: retry semantics ---
    ("J-27-run-200", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "200"], None),
    ("J-28-run-503-default", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "503"], None),
    ("J-29-run-503x2-then-200", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "503,503,200"], None),
    ("J-30-run-503-then-200", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "503,200"], None),
    ("J-31-run-500-upstream", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "500"], None),
    ("J-32-run-404-upstream", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "404"], None),
    ("J-33-run-503-retries0", ["run", "--retries", "0", "--request", '{"user_id":"u","payload":1}', "--sequence", "503"], None),
    ("J-34-run-empty-seq", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", ""], None),
    ("J-35-run-bad-seq", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "abc"], None),
    ("J-36-run-503-retries4", ["run", "--config", f("base.json"), "--request", '{"user_id":"u","payload":1}', "--sequence", "503"], None),
    ("J-37-run-302-noerror", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "302"], None),
    ("J-38-run-201-ok", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "201"], None),
    ("J-39-run-300-boundary", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "300"], None),
    ("J-40-run-299-boundary", ["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "299"], None),
    # --- argparse-level failures ---
    ("J-41-missing-request", ["run"], None),
    ("J-42-bad-command", ["frobnicate", "--request", '{"user_id":"u","payload":1}'], None),
    ("J-43-missing-command", ["--request", '{"user_id":"u","payload":1}'], None),
]


def run(program, args, env_overrides):
    env = dict(os.environ)
    env.pop("PORTME_TIMEOUT_MS", None)  # ensure a clean baseline unless set
    if env_overrides:
        env.update(env_overrides)
    proc = subprocess.run(
        [sys.executable] + program + args,
        capture_output=True, text=True, env=env,
    )
    return {"stdout": proc.stdout, "stderr": proc.stderr, "exit": proc.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["source", "diff"], default="diff")
    ap.add_argument("--target", default=TARGET_ROOT,
                    help="port root containing src/cli.py")
    ap.add_argument("--results", default=os.path.join(HERE, "results"))
    args = ap.parse_args()

    port_cli = os.path.join(args.target, "src", "cli.py")
    observations = {}
    mismatches = []

    for sid, sargs, env in SCENARIOS:
        src_obs = run([SOURCE], sargs, env)
        observations[sid] = {"source": src_obs}
        if args.mode == "diff":
            port_obs = run([port_cli], sargs, env)
            observations[sid]["port"] = port_obs
            if src_obs != port_obs:
                mismatches.append((sid, src_obs, port_obs))

    os.makedirs(args.results, exist_ok=True)
    out_name = "source-baseline.json" if args.mode == "source" else "diff.json"
    with open(os.path.join(args.results, out_name), "w") as fh:
        json.dump(observations, fh, indent=2, sort_keys=True)

    total = len(SCENARIOS)
    if args.mode == "source":
        print("baseline: captured %d source observations -> %s" % (total, out_name))
        return 0

    passed = total - len(mismatches)
    print("diff: %d/%d scenarios matched" % (passed, total))
    for sid, s, p in mismatches:
        print("  MISMATCH %s" % sid)
        print("    source: %r" % s)
        print("    port:   %r" % p)
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
