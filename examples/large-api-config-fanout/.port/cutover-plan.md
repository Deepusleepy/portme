# Cutover plan
- Strategy: direct swap (low blast radius: single-user CLI, no persistence, instant rollback)
- Baseline and drift policy: source sha256 bb35f057aeefb98ef12a0d2e8fcb03fc03c009eaf59f71e7b3a9a59701af7457; policy = FREEZE (source is pinned and idle)
- Stages and dwell: single stage; pre-cutover judge canary must be 43/43 before swap
- Signals: differential judge (43 scenarios), full_referee serialized suite (35 tests), exit-code parity
- Rollback triggers: any judge scenario mismatch, any introduced failure, any non-stdlib import
- Rollback action and owner: orchestrator repoints callers to
  source/legacy_adapter.py (retained, unchanged); ETA seconds
- Reconciliation: none (stateless transform; no target-only data)
- Stabilization window: judge canary retained; old path kept runnable through the window
- Rollout state: retirement-pending (disposable dogfood; old path intentionally retained)
- Old-path retirement date: not-scheduled (disposable harness run)
- Quick terminal rule: not-applicable (Large-scale)

## Pre-cutover judge canary
- Command: python3 .port/judge/compare.py --mode diff
- Result: 43/43 matched (exact stdout+stderr+exit)
- Serialized referee canary: .port/referee/0002 exit 0 (35 tests + py_compile), last-verified

## Rollback receipt
- Old path retained and runnable: source/legacy_adapter.py @ bb35f057aeefb98ef12a0d2e8fcb03fc03c009eaf59f71e7b3a9a59701af7457
- Verified rollback drill: re-ran source oracle via judge --mode source (43 observations captured)
- No target-only state exists; swapping back is loss-free.
