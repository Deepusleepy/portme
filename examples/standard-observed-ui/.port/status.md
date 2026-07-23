# Port status
- Mode: Standard
- Active phase: 6 — Cut over / done
- Phase state: complete
- Gate log:
  - sizing | 2026-07-23 | approver=harness preauthorization (local disposable dogfood; objective-condition gate, NOT quoted user approval)
  - Phase 0 judge | 2026-07-23 | approver=harness preauthorization; objective condition: judge 18/18 + mutation 6/6 green
  - Phase 1 map+manifest | 2026-07-23 | approver=harness preauthorization; bundle pin recorded below
  - Phase 2 stress slice | 2026-07-23 | approver=harness preauthorization; risky slice = index/error contract, kept in place (small port)
  - Phase 3–5 port+checks | 2026-07-23 | approver=harness preauthorization; objective condition: manifest queue 2/2, 0 failed-check
  - Phase 6 cutover | 2026-07-23 | approver=harness preauthorization; markers 0, no rollout target
- Approval provenance: This run is authorized by HARNESS-LEVEL PREAUTHORIZATION for a
  local disposable test, defined as objective phase gates that pass only when the required
  mechanical evidence is green. This is explicitly NOT a quoted end-user approval and NOT
  authority for any other run. Every gate above cites that preauthorization plus its
  objective green condition, which is evidenced on disk.
- Manifest/check-input authorization: bundle SHA-256
  `b8a5666a993576c12567f9818a89b046e39ce1ae53e2cfb9b9fcd745ed536a59`
  over `.port/manifest.tsv` + declared check-input bytes; compute with
  `python3 scripts/port_queue.py --manifest .port/manifest.tsv digest`; exact checks =
  U-001 `run_port && compare && byte_fidelity`, U-002 `mutation_test`. Authorized under the
  preauthorized objective condition; a manifest/check-control byte or glob change reopens Phase 1.
- Baseline command authorization: not-applicable (no build/typecheck baseline; observed-only UI port, stdlib run)
- Next concrete action: none — port complete and verified; disposable target, no rollout.
- Artifact index:
  - port engine → src/pocket_tasks.py
  - contract → .port/contract.md ; behavior map → .port/behavior-map.tsv
  - rulebook → .port/rulebook.md ; gaps/assumptions → .port/gaps.tsv
  - divergences → .port/accepted-divergences.tsv ; cost → .port/cost-log.tsv
  - manifest → .port/manifest.tsv ; queue → scripts/port_queue.py
  - judge → .port/judge/ (README, scenarios.tsv, _scenarios.py, _driver.py, run_source.py,
    run_port.py, capture.py, compare.py, mutation_test.py, byte_fidelity.py, fixtures/, results/)
  - scanner → .port/scanner/pocketscan.py + pocketscan-rules.json
  - capture receipts → .port/receipts/ ; evidence → .port/evidence/
  - verify entry → verify.sh ; cutover → .port/cutover-plan.md
  - raw evidence: quarantine was created OUTSIDE the repo and DELETED (see receipts/capture-001.md)
- Blockers: none

## Phase 0–6 — summary
- Queue: 2/2 units present, 2/2 verified, 0 pending/blocked/failed-check
- Judge: 18/18 scenarios PASS (differential vs admitted redacted source goldens)
- Mutation sensitivity: 6/6 classes caught; source file hash unchanged
- Byte fidelity: PASS (raw UTF-8, ensure_ascii=False)
- Capture pipeline: quarantine 0700 outside repo + non-symlink; inventory 18 regular files,
  0 rejected; pocketscan 1.0.0 (rules SHA-256 9772277db2440aa7...) raw findings=8 →
  redacted rescan findings=0; 18 copy-not-link admissions verified; quarantine deleted +
  path-absent confirmed
- Adversarial review: 2 confirmed defects (add normalization; ensure_ascii) found and fixed;
  0 divergences post-fix over 19 extra probes
- Markers: 0 open
- Cost: single-session Opus 4.8 build/review; tokens NA (not metered by harness)
