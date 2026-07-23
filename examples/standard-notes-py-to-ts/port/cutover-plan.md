# Cutover plan — notes CLI (Python → TypeScript)

- **Strategy:** direct swap (sandbox context) — declare `node dist/cli.js` (built from `src/` via `npm run build`) the **canonical implementation** of the `notes` CLI in this example. Low blast radius, immediate rollback, no live traffic/users.
- **Baseline and drift policy:** source pinned as-is on disk 2026-07-22 (Python 3.14.6) and now shipped byte-identically in `source-python/`. Policy: **FREEZE** — if it changes, update its SHA-256 baseline and re-baseline goldens behind a new gate.
- **Stages and dwell:** single stage (direct swap); historical pre-cutover canary was 14/14, and the latest post-publication suite is 15/15 on a clean copy.
- **Signals / judge canaries:** `./verify.sh` is the canonical one-command canary for the explicitly invoked publication demo. Its component commands use `port/judge/judge.sh` and the publication-pinned bundle-integrity path through `scripts/port_queue.py`; this is not conversation gate approval.
- **Rollback triggers:** any judge-canary mismatch, any runtime crash on a contracted surface, or discovery that the source moved outside FREEZE.
- **Rollback action and owner:** owner = user. Action = **revert to invoking the shipped Python source** (`PYTHONPATH=source-python python3 -m notes_cli.cli …`). Expected completion: immediate (no state migration — the notes file format is byte-identical).
- **Reconciliation:** none required — the notes-file format is identical (S14), so a store written by either implementation is readable by the other; rollback loses no data.
- **Stabilization window:** n/a for the sandbox (no live traffic). Judge + source both retained and re-runnable indefinitely as canaries.
- **Rollout state:** **retired** (old path retained as documented oracle/rollback, not in active use).
- **Old-path retirement:** the Python source is intentionally **kept runnable** as the oracle and rollback target (not deleted). The port apparatus (`.port/`, including the judge and `golden/`) is **retained as the audit trail**, not deleted.

## Port marker ledger — TRULY repo-wide scan (2026-07-22, corrected)
Historical scan: `grep -rnE "TODO\(port\)|BUG\(port\)|\bTODO\b|\bFIXME\b|\bXXX\b|\bHACK\b" .` over the original target tree (including its `.port/` and `dist/`), excluding only `node_modules/` and `.git/`. Published receipt: `port/evidence/phase6-marker-scan.txt`. Total matches: **6** — all in historical process/documentation text, **0 in shipped source/config**.

| # | Path:line | Kind | Classification | Disposition |
|---|---|---|---|---|
| 1 | `.port/contract.md:72` | prose: the marker-gate done criterion (lists the marker class names) | documentation | keep — process text, not a live marker |
| 2 | `.port/rulebook.md:127` | prose: source-bug posture rule (mentions `BUG(port):`) | documentation | keep — policy text |
| 3 | `.port/status.md:12` | prose: gate-log entry (word "TODO burndown") | documentation | keep — audit log |
| 4 | `.port/status.md:201` | prose: Phase 6 markers line (lists the class names) | documentation | keep — audit log |
| 5 | `.port/cutover-plan.md` (this ledger) | prose: this ledger names the classes | documentation | keep — this receipt |
| 6 | `.port/cutover-plan.md` (this ledger note) | prose: classification note | documentation | keep — this receipt |

**Shipped code (`src/`, `dist/`) and all config: 0 live markers.** The 6 hits are process/documentation text that necessarily names the marker classes; none is an unresolved `TODO(port)`/`BUG(port)` or a deferred item.

## Retirement checklist (sandbox scope)
- [x] Canonical implementation declared: `node dist/cli.js` (built from `src/`).
- [x] Old path (Python source) retained runnable as oracle + rollback target.
- [x] Notes-file format interop verified (S14) — no data migration/reconciliation needed.
- [x] Audit trail retained: `.port/` (contract, manifest, rulebook, gaps, divergences, judge, golden, results, cost-log).
- [x] Approved divergences D-001, D-002 final-signed-off.
- [x] No CI/pipelines/alerts to repoint (sandbox); documented for any future integration.
