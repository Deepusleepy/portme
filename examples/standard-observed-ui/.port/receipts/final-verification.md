# Final verification receipt — Pocket Tasks observed-only port

Date: 2026-07-23. Mode: Standard. Runner: single-session Opus 4.8 (build + review).
Entry point: `./verify.sh` (offline; no source needed). All green.

## Mechanical results
- Zero third-party runtime deps: PASS (stdlib-only import allowlist).
- Authorization bundle digest pin: `b8a5666a993576c12567f9818a89b046e39ce1ae53e2cfb9b9fcd745ed536a59`
  matches computed digest over `.port/manifest.tsv` + declared check-input bytes.
- Authorized manifest queue: **2/2 units verified, 0 failed-check** (U-001 run_port+compare+byte_fidelity; U-002 mutation_test).
- Differential judge: **18/18 scenarios PASS** (J-001..J-017, J-PII) vs admitted redacted source goldens.
- Two-way mutation sensitivity: **6/6 classes caught** (changed-value, removed-item,
  error-semantics, broken-focus, broken-aria, suppressed-effect); source file hash unchanged.
- Byte fidelity: PASS (raw UTF-8, `ensure_ascii=False`).
- Marker ledger: 0 open TODO/BUG/PERF/SAFETY(port)/FIXME/XXX/HACK.

## Privacy / evidence pipeline (proven, not skipped)
- Quarantine: created OUTSIDE the repo via `tempfile.mkdtemp`, `chmod 0700`, verified
  non-symlink and outside-repo; resolved path recorded (`receipts/capture-001.md`).
- Inventory: 18 regular files, 0 rejected (symlink/non-regular guard active).
- Scanner: `pocketscan 1.0.0`, rules SHA-256 `9772277db2440aa756dfe689ade6c3e1253a9295214f6147cb304f88f96f22a9`.
  Raw findings = 8 (all from the J-PII scenario's synthetic secrets). Raw receipt:
  `receipts/capture-001-scan-raw.json` (kept outside the fixture set).
- Redaction + rescan: redacted copies rescanned → **findings = 0**
  (`receipts/capture-001-rescan-redacted.json`).
- Admission: 18 redacted regular files COPIED (not linked) into `judge/fixtures/<id>/`;
  symlink + hard-link (nlink==1) checks passed; source→admitted hashes recorded
  (`evidence/capture-001-admitted.txt`).
- Deletion: `shutil.rmtree` of the quarantine; path-absent verification confirmed.
- Pre-share rescan of admitted fixtures: **0 findings**.

## No-real-secret note
The whole-repo scan reports the synthetic string in `.port/judge/_scenarios.py`
(J-PII definition): the canonical AWS **documentation example** key
`AKIAIOSFODNN7EXAMPLE` and an `@example.com` address. These are deliberate,
non-sensitive fixtures whose only purpose is to exercise the scan/redact pipeline.
No real credential, token, session, or private data exists anywhere in the target.

## Defects found and fixed in adversarial review
- add text normalization (whitespace-collapse + `str()` coercion) — was `.strip()`.
- JSON output encoding — was ASCII-escaped, now raw UTF-8.
Both fixed and regression-guarded (J-017 + `byte_fidelity.py`). Post-fix: 0 divergences
over a 19-input adversarial probe set. Details: `judge/results/phase3-adversarial-review.md`.

## Bounded-fidelity claim
The port matches the recorded scenarios and stated assumptions (contract §Observed-only
source limits). This is NOT an unqualified full-parity claim; unobserved areas
(concurrency, session TTL, persistence, non-UTF-8 bodies, empty POST body) are listed
as coverage limits.
