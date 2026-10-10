# notes-CLI differential judge

Rung 3 of `references/judge.md`: a **differential harness** that runs the Python
source oracle and the compiled TypeScript port side by side on identical argv +
initial `$NOTES_FILE` state, and asserts byte-identical **stdout, stderr, exit
code, and resulting notes-file bytes**. The contract has **17 surface rows**
(S1, S2, S3a, S3b, S4, S5, S6a, S6b, S7–S15); **15 are `exact`** and byte-compared
by these scenarios, and **2 are `intentionally-divergent` sub-surfaces**: S3b
(non-ASCII search casing, D-001) and S6b (Unicode-digit `remove`, D-002), which
are **not** exercised by scenarios (bounded coverage BC-1/BC-2; behavior covered
by divergence approval). See `port/contract.md`.

## Layout
- `scenarios.sh`: scenario definitions (`scn_<id>`); drives the CLI, emits a deterministic transcript.
- `scenarios.tsv`: frozen scenario inventory (schema: `templates/judge-scenarios.tsv`), mapped to surface IDs.
- `adapters/source.sh`: source adapter: defaults to `source-python/`; override with `PORTME_SOURCE_DIR`.
- `adapters/port.sh`: port adapter: defaults to `dist/cli.js`; override with `PORTME_DIST`.
- `adapters/broken.sh`: Phase-0 mutation adapter (wraps source, corrupts one channel via `$MUTATION`).
- `judge.sh`: `capture` / `compare` / `validate` (Phase 0) / `port` (Phase 5 differential) / `goldencheck` (drift) / `checkport <ids>` (per-unit).
- `golden/`: **frozen** source baseline transcripts (do not overwrite; provenance below).
- `results/`: generated transcripts + validation logs (regenerable; never overwrites `golden/`).

## Run
```
bash port/judge/judge.sh validate     # two-way validation (source vs source; source vs broken)
bash port/judge/judge.sh port         # DIFFERENTIAL, fresh shipped source vs node dist/cli.js
bash port/judge/judge.sh goldencheck  # DRIFT, fresh shipped source vs frozen golden/
```
Each scenario runs against a fresh temp `$NOTES_FILE`; the default-path scenario
runs under a fresh sandbox `$HOME` with `NOTES_FILE` unset. No real dotfile is touched.

## Provenance (golden baseline)
- Historical J-001…J-013b goldens were produced by `bash judge.sh capture adapters/source.sh source` from `REDACTED-SANDBOX/target-opus`, pinned as-is on disk 2026-07-22.
- J-014 was added by post-publication errata pass 3 on 2026-07-23 and captured from the byte-identical oracle shipped in `source-python/`; it was not retroactively inserted into old receipts.
- Tools: Python 3.14.6, Node v24.18.0, GNU bash 3.2.57 (arm64-apple-darwin25), macOS.
- Latest suite: J-001…J-014 (**15 scenarios**) covering the **15 `exact` surfaces** (S1, S2, S3a, S4, S5, S6a, S7–S15). J-014 adds both directions of Python-vs-JavaScript whitespace-set coverage. The 2 `intentionally-divergent` sub-surfaces (S3b, S6b) remain outside scenario coverage (BC-1/BC-2).
- Port-produced output can never become a golden (judge.md grader-independence rule).

## Phase 0 two-way validation result (2026-07-22): see `results/phase0-validation.txt`
- Self-consistency (pass direction): source vs source = **14/14 match**.
- Mutation catches (fail direction), one per comparator class, all **CAUGHT**:
  - `stdout` → c1_add, c4_remove_ok, c13_fileformat, c13b_defaultpath
  - `stderr` → c8_dym_singular, c9_dym_plural
  - `exit`   → c5_remove_oob
  - `file`   → c1_add, c4_remove_ok, c5_remove_oob, c13_fileformat
- Summary: self-consistency PASS; mutations caught 4/4. The judge passes on
  correct behavior and rejects every deliberately broken class.

## Normalization
None. The 15 exact surfaces are covered by the latest 15-scenario suite; transcripts are compared
byte-for-byte. No timestamps/IDs/paths appear in output, so no normalizer is
warranted (over-normalization would hide portability defects; see judge.md). The 2
intentionally-divergent sub-surfaces (S3b/S6b) are out of scenario scope, not
normalized away.
