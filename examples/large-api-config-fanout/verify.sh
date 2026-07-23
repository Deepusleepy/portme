#!/usr/bin/env bash
# Reproduce the packaged API/config/fan-out evidence without mutating this tree.
set -euo pipefail

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
WORK=$(mktemp -d "${TMPDIR:-/tmp}/portme-api-fanout-verify.XXXXXX")
CASE="$WORK/example"
cleanup() {
  chmod -R u+w "$WORK" 2>/dev/null || true
  rm -R -- "$WORK"
}
trap cleanup EXIT HUP INT TERM

mkdir "$CASE"
cp -R "$ROOT/." "$CASE/"
cd "$CASE"
export PYTHONDONTWRITEBYTECODE=1

BUNDLE_PIN=37280d4e00533ecedff4c5a89c76c3622176f53bc0e22652e30bfd62d7ae9589
SOURCE_PIN=bb35f057aeefb98ef12a0d2e8fcb03fc03c009eaf59f71e7b3a9a59701af7457
QUEUE_PIN=a22b62ab18d47002d0f7baec8bb5f241b4fe45c1ff2037fbe9d6fdd3bf07b557
REFEREE_PIN=3d7adb3378fea9de3524f5dea798347e1dcdf10da0824ed3715de842a4d362ed

echo "== bundled source and runner pins =="
python3 - "$SOURCE_PIN" "$QUEUE_PIN" "$REFEREE_PIN" <<'PY'
import hashlib
import pathlib
import sys

expected = dict(zip(
    ("source/legacy_adapter.py", "scripts/port_queue.py", "scripts/referee_runner.py"),
    sys.argv[1:],
))
for name, wanted in expected.items():
    got = hashlib.sha256(pathlib.Path(name).read_bytes()).hexdigest()
    if got != wanted:
        raise SystemExit("digest drift: %s: %s != %s" % (name, got, wanted))
    print("ok: %s %s" % (name, got))
PY

echo "== current authorization-bundle pin =="
GOT=$(python3 scripts/port_queue.py --manifest .port/manifest.tsv digest)
echo "computed=$GOT"
[ "$GOT" = "$BUNDLE_PIN" ] || {
  echo "FAIL: authorization bundle drift; expected $BUNDLE_PIN" >&2
  exit 1
}

echo "== authorized manifest queue =="
QUEUE_OUTPUT=$(python3 scripts/port_queue.py --manifest .port/manifest.tsv \
  --run-checks --authorize-manifest "$BUNDLE_PIN" --check-timeout 120 verify)
printf '%s\n' "$QUEUE_OUTPUT"
printf '%s\n' "$QUEUE_OUTPUT" | grep -F "verified 4/4 units; 0 failed-check" >/dev/null

echo "== full unittest suite =="
TEST_OUTPUT=$(python3 -m unittest discover -s tests -v 2>&1)
printf '%s\n' "$TEST_OUTPUT"
printf '%s\n' "$TEST_OUTPUT" | grep -E 'Ran 35 tests in ' >/dev/null
printf '%s\n' "$TEST_OUTPUT" | grep -Fx 'OK' >/dev/null

echo "== differential judge against bundled source =="
JUDGE_OUTPUT=$(python3 .port/judge/compare.py --mode diff)
printf '%s\n' "$JUDGE_OUTPUT"
printf '%s\n' "$JUDGE_OUTPUT" | grep -Fx 'diff: 43/43 scenarios matched' >/dev/null

echo "== new serialized full referee and cryptographic last =="
RUN_OUTPUT=$(python3 scripts/referee_runner.py run --port .port --timeout 120 -- ./full_referee.sh)
printf '%s\n' "$RUN_OUTPUT"
printf '%s\n' "$RUN_OUTPUT" | grep -E '\.port/referee/0005$' >/dev/null
LAST_OUTPUT=$(python3 scripts/referee_runner.py last --port .port)
printf '%s\n' "$LAST_OUTPUT"
printf '%s\n' "$LAST_OUTPUT" | grep -E '\.port/referee/0005 exit 0$' >/dev/null

echo "== immutable history, fan-out, guardrail, and review receipts =="
python3 <<'PY'
import datetime as dt
import importlib.util
from pathlib import Path
import re

root = Path(".")
spec = importlib.util.spec_from_file_location("referee_runner", root / "scripts/referee_runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

assert runner._verified_result(root / ".port/referee/0003") == 1
assert runner._verified_result(root / ".port/referee/0004") == 0
assert runner._verified_result(root / ".port/referee/0005") == 0

failed = (root / ".port/referee/0003/output.txt").read_text()
fixed = (root / ".port/referee/0004/output.txt").read_text()
new = (root / ".port/referee/0005/output.txt").read_text()
assert "FAILED (failures=1)" in failed and "AssertionError: 1 != 2" in failed
assert "Ran 35 tests" in fixed and fixed.rstrip().endswith("OK")
assert "Ran 35 tests" in new and new.rstrip().endswith("OK")

for name in ("deny-direct.txt", "deny-wrapper-bash.txt", "deny-alt-env.txt"):
    text = (root / ".port/receipts" / name).read_text()
    assert "DENIED: workers must route full_referee.sh" in text
    assert "exit=126" in text

config = (root / ".port/receipts/fanout-U-CONFIG.md").read_text()
execute = (root / ".port/receipts/fanout-U-EXEC.md").read_text()
assert "2026-07-23T05:09:04Z" in config and "2026-07-23T05:09:31Z" in config
assert "2026-07-23T05:09:02Z" in execute and "2026-07-23T05:09:27Z" in execute
assert "11 tests" in config and "9 (all passed)" in execute
assert "exit code 126" in config and "exit code 126" in execute
assert "only src/config.py edited" in config
assert "- src/config.py\n- .port/receipts/fanout-U-CONFIG.md" in config
assert "`src/execute.py`, `.port/receipts/fanout-U-EXEC.md`" in execute

def window(text):
    values = re.findall(r"2026-07-23T05:09:\d\dZ", text)
    assert len(values) >= 2
    return tuple(dt.datetime.fromisoformat(value.replace("Z", "+00:00")) for value in values[:2])

config_start, config_end = window(config)
exec_start, exec_end = window(execute)
assert max(config_start, exec_start) < min(config_end, exec_end)
config_owned = {"src/config.py", ".port/receipts/fanout-U-CONFIG.md"}
exec_owned = {"src/execute.py", ".port/receipts/fanout-U-EXEC.md"}
assert config_owned.isdisjoint(exec_owned)

review_a = (root / ".port/reviews/fanout-review-A.md").read_text()
review_b = (root / ".port/reviews/fanout-review-B.md").read_text()
for review in (review_a, review_b):
    assert "U-CONFIG **PASS**; U-EXEC **PASS**" in review
    assert "not a verbatim user message" in review
    assert "no approval" in review
assert "**6/10**" in review_a and "positional consumer call shape" in review_a
assert "**8/10**" in review_b and "last-known-good" in review_b
assert "behavior-neutral" in review_b

status = (root / ".port/status.md").read_text()
assert "Real overlapping worker windows" in status
assert "U-EXEC 05:09:02–05:09:27Z" in status
assert "U-CONFIG 05:09:04–05:09:31Z" in status
assert "one process finding" in status
print("ok: immutable 0003/0004/0005, deny x3, overlapping disjoint workers, reviews A/B")
PY

echo "ALL VERIFICATION PASSED"
