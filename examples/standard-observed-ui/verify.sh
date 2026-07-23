#!/usr/bin/env bash
# Self-contained verification for the Pocket Tasks observed-only port.
# Runs from the target root. Requires only Python 3 stdlib. No network to any
# source is needed: goldens are the admitted redacted fixtures already on disk.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd "$(dirname "$0")"

PIN=b8a5666a993576c12567f9818a89b046e39ce1ae53e2cfb9b9fcd745ed536a59

echo "== NF-001: zero third-party runtime deps =="
if grep -REn '^\s*(import|from)\s+' src/pocket_tasks.py \
   | grep -Ev 'from __future__|http\.server|json|os|urllib|re|hashlib|threading|argparse|sys|datetime|tempfile|shutil|subprocess|importlib|stat' ; then
  echo "FAIL: unexpected import"; exit 1
fi
echo "ok: stdlib only"

echo "== authorization bundle digest pin =="
GOT=$(python3 scripts/port_queue.py --manifest .port/manifest.tsv digest)
echo "computed=$GOT"
[ "$GOT" = "$PIN" ] || { echo "FAIL: digest drift (check_inputs changed) — reopen Phase 1"; exit 1; }
echo "ok: matches pinned bundle"

echo "== manifest queue (authorized checks) =="
python3 scripts/port_queue.py --manifest .port/manifest.tsv \
  --run-checks --authorize-manifest "$PIN" --check-timeout 180 verify

echo "== differential judge =="
python3 .port/judge/run_port.py .port/judge/results/port-obs >/dev/null
python3 .port/judge/compare.py

echo "== two-way mutation sensitivity =="
python3 .port/judge/mutation_test.py | tail -3

echo "== marker ledger =="
if grep -REn 'TODO\(port\)|BUG\(port\)|PERF\(port\)|SAFETY\(port\)|FIXME|XXX|HACK' src .port/judge/*.py .port/scanner/*.py 2>/dev/null; then
  echo "note: markers present — must be accepted in accepted-divergences/gaps"
else
  echo "ok: no open markers"
fi

echo "ALL VERIFICATION PASSED"
