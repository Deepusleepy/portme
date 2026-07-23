# Cutover plan — Pocket Tasks port (Phase 6)

## Marker ledger
- `grep -REn 'TODO\(port\)|BUG\(port\)|PERF\(port\)|SAFETY\(port\)|FIXME|XXX|HACK'`
  over `src/`, `.port/judge/*.py`, `.port/scanner/*.py`: **0 matches** (see
  verify.sh "marker ledger" step). No open markers to burn down.

## Drift policy
- The source is a static local fixture (`ui-observed-1`); no upstream drift is
  expected during this disposable run. If the source version string changes,
  reopen Phase 0: re-capture goldens via `.port/judge/capture.py` and re-run the
  differential judge before trusting parity.

## Divergences requiring final sign-off
- **D-001** (health version normalized) — accepted; comparator masks the field.
- **D-CAND-1** (error body exposes exception class name) — NOT diverged;
  reproduced for parity and recorded as a productionization hardening note.
  Final sign-off deferred to whoever productionizes the port.

## Rollout / rollback
- Blast radius: none. This is a disposable local dogfood target with no
  consumers, no production path, and no data. No rollout is performed and none
  was requested. Rollback in the original disposable run = delete
  `REDACTED-LOCAL-FIXTURE`.
- Old-path retirement: not applicable (no pre-existing implementation replaced).

## Re-verification entry point
- `./verify.sh` from the target root reproduces every gate offline (digest pin,
  authorized manifest queue 2/2, judge 18/18, mutation 6/6, marker scan).
