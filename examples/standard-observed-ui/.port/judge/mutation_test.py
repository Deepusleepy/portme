#!/usr/bin/env python3
"""mutation_test.py — two-way judge sensitivity for the Pocket Tasks judge.

The judge must PASS the faithful port (proven by compare.py) and FAIL every
deliberately mutated port. Each mutation is applied to a DISPOSABLE copy of
src/pocket_tasks.py in a temp directory, loaded fresh, driven through its own
public surface, and compared against the admitted golden fixtures. The original
source file and the source fixture are never touched; their hashes are recorded
before and after to prove that.

Mutation classes (one representative each, chosen to hit distinct comparators):
  M1 changed-value      — active count uses total instead of active
  M2 removed-item       — filter view ignores the 'done' filter
  M3 error-semantics    — non-numeric index no longer raises (returns 200)
  M4 broken-focus       — toggle stops setting focus
  M5 broken-aria        — accessible label drops the completed/active suffix
  M6 suppressed-effect  — export omits done tasks

Usage: mutation_test.py
Exit 0 iff every mutation is caught (judge fails on each).
"""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "src", "pocket_tasks.py"))
sys.path.insert(0, HERE)
import _driver  # noqa: E402
import _scenarios  # noqa: E402
import compare as _compare  # noqa: E402

MUTATIONS = [
    ("M1", "changed-value",
     'active_count = sum(1 for t in state["tasks"] if not t["done"])',
     'active_count = len(state["tasks"])'),
    ("M2", "removed-item",
     'if f == "done" and not t["done"]:\n            continue',
     'if f == "done" and not t["done"]:\n            pass'),
    ("M3", "error-semantics",
     'index = int(action.get("index", -1))',
     'index = int(action.get("index", -1)) if str(action.get("index", -1)).lstrip("-").isdigit() else -1'),
    ("M4", "broken-focus",
     'state["focus"] = "task-%d" % index\n            state["live"] = ("%s completed" if t["done"] else "%s active") % t["text"]',
     'state["live"] = ("%s completed" if t["done"] else "%s active") % t["text"]'),
    ("M5", "broken-aria",
     '"Mark %s active" % t["text"] if t["done"] else "Mark %s done" % t["text"]',
     '"Mark %s" % t["text"]'),
    ("M6", "suppressed-effect",
     '("[x] %s\\n" if t["done"] else "[ ] %s\\n") % t["text"] for t in state["tasks"]',
     '("[ ] %s\\n") % t["text"] for t in state["tasks"] if not t["done"]'),
]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def drive(mod):
    httpd = mod.make_server("127.0.0.1", 0)
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    obs_by_sid = {}
    try:
        for sid in _scenarios.ALL_IDS:
            obs = _driver.run_scenario(base, "mut-%s" % sid, _scenarios.SCENARIOS[sid])
            obs_by_sid[sid] = _driver.normalize(obs)
    finally:
        httpd.shutdown()
    return obs_by_sid


def judge_fails(obs_by_sid):
    """True if at least one scenario diverges from golden (judge catches it)."""
    for sid in _scenarios.ALL_IDS:
        gpath = os.path.join(_compare.FIX, sid, "observation.json")
        with open(gpath) as f:
            golden = _driver.normalize(json.load(f)["observations"])
        if _compare._diff(golden, obs_by_sid[sid]):
            return True
    return False


def main():
    src_before = sha(SRC)
    results = []
    all_caught = True
    with open(SRC, encoding="utf-8") as f:
        original = f.read()

    for mid, mclass, old, new in MUTATIONS:
        assert old in original, "mutation %s anchor not found" % mid
        tmp = tempfile.mkdtemp(prefix="mut-%s-" % mid)
        mpath = os.path.join(tmp, "pocket_tasks.py")
        with open(mpath, "w", encoding="utf-8") as f:
            f.write(original.replace(old, new, 1))
        try:
            mod = load_module(mpath, "pt_%s" % mid)
            obs = drive(mod)
            caught = judge_fails(obs)
        finally:
            shutil.rmtree(tmp)
        results.append((mid, mclass, tmp, caught))
        all_caught = all_caught and caught

    src_after = sha(SRC)
    print("# Mutation sensitivity — %d classes" % len(MUTATIONS))
    print("source file sha256 before=%s after=%s unchanged=%s"
          % (src_before, src_after, src_before == src_after))
    for mid, mclass, tmp, caught in results:
        print("%s %-18s disposable=%s caught=%s"
              % (mid, mclass, tmp, "YES" if caught else "NO -- ESCAPED"))
    print("\nall_caught=%s (%d/%d)"
          % (all_caught, sum(1 for r in results if r[3]), len(results)))
    return 0 if (all_caught and src_before == src_after) else 1


if __name__ == "__main__":
    raise SystemExit(main())
