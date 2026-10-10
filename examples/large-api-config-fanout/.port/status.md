# Port status
- Mode: Large-scale (user-requested override on a small fixture; recorded honestly, see Sizing)
- Active phase: 6. Cut over / rollout-active (retirement-pending; disposable dogfood)
- Phase state: complete (all objective phase gates green under harness preauthorization)
- Gate log:
  - sizing | 2026-07-23 | approver=harness preauthorization (disposable): Large-scale override + model plan
  - Phase 0 | 2026-07-23 | approver=harness preauthorization: judge 43 scenarios + 5 mutations caught
  - Phase 1 | 2026-07-23 | approver=harness preauthorization: bundle digest 7fa1c825… + clean join
  - Phase 2 | 2026-07-23 | approver=harness preauthorization: stress slice, 0 amendments
  - Phase 3 | 2026-07-23 | approver=harness preauthorization: 4/4 units done, 2 reviews/high-risk unit
  - Phase 4 | 2026-07-23 | approver=harness preauthorization: serialized referee + deny receipts
  - Phase 5 | 2026-07-23 | approver=harness preauthorization: judge 43/43, 0 introduced/inherited
  - Phase 6 | 2026-07-23 | approver=harness preauthorization: canary + rollback receipt
- Approval provenance: parent-orchestrator task message granting disposable harness preauthorization
  to continue through objective phase gates when required evidence is green. Not a quoted end-user
  approval; this is a disposable dogfood run. Stop conditions (contract change, divergence, failed
  gate, destructive/out-of-scope, unresolved high-risk) did not trigger.
- Manifest/check-input publication bundle: SHA-256
  37280d4e00533ecedff4c5a89c76c3622176f53bc0e22652e30bfd62d7ae9589;
  exact checks = the four `unit_check` commands in .port/manifest.tsv;
  declarations = tests/test_{config,translate,execute,cli}.py, tests/_bootstrap.py;
  verified: mismatched digest (all-zero) refused execution; correct digest ran 4/4 done.
  This publication pin changed from the historical run's `7fa1c825…` only because
  manifest source scopes were rebased to bundled `source/legacy_adapter.py`. It
  proves the shipped bundle's integrity; it is not user approval for another run.
- Baseline command authorization: not-applicable (no build/typecheck baseline needed; stdlib only)
- Next concrete action: none, run complete; old path retained for rollback (disposable)
- Artifact index:
  - source: source/legacy_adapter.py @ sha256 bb35f057aeefb98ef12a0d2e8fcb03fc03c009eaf59f71e7b3a9a59701af7457
  - port src: src/{config,translate,execute,cli}.py
  - tests: tests/test_{config,translate,execute,cli}.py, tests/_bootstrap.py
  - judge: .port/judge/compare.py, .port/judge/README.md, .port/judge/fixtures/*, .port/judge/results/*
  - manifest: .port/manifest.tsv; packets: .port/packets/U-*.md
  - contract/map/gaps/rules: .port/contract.md, behavior-map.tsv, gaps.tsv, rulebook.md
  - deny receipts: .port/receipts/deny-{direct,wrapper-bash,alt-env}.txt
  - referee results: .port/referee/0001–0004 (immutable 0444/0555; 0003 fail, 0004 fix)
  - parent review summaries: .port/reviews/fanout-review-{A,B}.md (evidence, not approval)
  - cutover: .port/cutover-plan.md; divergences: .port/accepted-divergences.tsv (empty)
- Blockers: none

## Post-run fan-out transport addendum: parent harness
- Purpose: close the original orchestrator's disclosed no-Agent concurrency gap without rewriting the historical run.
- Reopened units: U-CONFIG owner=Opus-worker-config (`src/config.py` only); U-EXEC owner=Opus-worker-exec (`src/execute.py` only).
- Baselines: `.port/evidence/fanout-baseline-config.py`, `.port/evidence/fanout-baseline-execute.py`.
- Launch rule: both workers start concurrently; each writes only its owned implementation path plus `.port/receipts/fanout-<unit>.md`; judge/rulebook/manifest/shared controls remain read-only.
- Liveness: observable progress is owned file creation or receipt creation; stall threshold 5 minutes. Parent must record ownership reclaim before relaunch and preserve U-CONFIG/U-EXEC IDs.
- Completion condition: both narrow unit checks pass, target ownership remains disjoint, authorized queue returns 4/4, serialized full referee passes, and independent parent review finds no behavior regression.
- State: COMPLETE. Real overlapping worker windows: U-EXEC 05:09:02–05:09:27Z; U-CONFIG 05:09:04–05:09:31Z. No stall or reclaim.
- Worker results: U-EXEC narrow 9/9; U-CONFIG narrow 11/11; both guardrails fired exit 126 and neither worker ran the full referee.
- Integration defect caught: serialized referee `0003` exit 1 exposed U-CONFIG's positional/env signature regression despite its 11/11 narrow pass. Same owner fixed only `src/config.py`; receipt append records root cause and fix.
- Final evidence: authorized queue 4/4; serialized referee `0004` exit 0 (35/35); corrected full differential judge 43/43. An earlier parent judge invocation passed `src/cli.py` where `--target` expected the repo root and produced a transport-only 0/43; rerun with `--target .` passed and the operator error was not treated as a product failure.
- Independent Opus review votes: U-CONFIG PASS / U-EXEC PASS from both reviewers. Fan-out mechanics scores 6/10 and 8/10; parent-retained summaries are in `.port/reviews/`. Shared confirmed process finding: the config leaf check exercised keyword calls only and could not catch its real positional consumer; integration serialization/recovery saved correctness. Process improvement required: every leaf unit check must include at least one actual consumer/public-entry call shape or an explicit integration dependency check. These reviews are evidence, not approval.
- Evidence caveat: pre-fan-out baselines preserve the last known-good files, not the broken intermediate; immutable referee `0003` plus the worker receipt/fix append preserve the failure trail.
- Publication relocation changed packet source paths and the current publication
  bundle pin. Packet hashes and `7fa1c825…` values quoted inside worker receipts
  remain historical read-time facts; they are not claims about the relocated
  packet bytes.

## Sizing decomposition (six factors)
Genuine measured size of this fixture is tiny (52-line source, one CLI). The user explicitly
requested a Large-scale dogfood to exercise fan-out/API/config paths, so the mode was overridden
UP to Large-scale and that override is recorded rather than hidden.
- Independent units: 1 (score 0 by size; 4 units carved for the exercise)
- Semantic-gap severity: 1 (implicit defaults, precedence, bool-as-int, retry bound)
- Referee cost: 0 (judge runs in seconds)
- Blast radius: 0 (isolated CLI, instant rollback)
- Source availability: 0 (readable, pinned, runnable)
- Judge availability: 0 (differential harness on public CLI surface)
- Arithmetic: 2/12 → intrinsic Quick. Override: user-requested Large-scale (dogfooding fan-out,
  API-version, and config-system control paths). Honest note: process is deliberately heavier than
  the fixture warrants; this is the requested exercise, not a sizing recommendation.
- Model plan: current model (Opus 4.8) for implementers, reviewers, and rule-writers (default).
  The original orchestrator could not switch tiers or spawn agents and kept roles
  separate serially; the later parent addendum used two real concurrent workers.

## Recorded constraints (honest original-run degradation)
- No Agent/Task subagent-spawn transport was exposed to the original orchestrator. Per SKILL.md rule 8 and
  references/loops.md ("when none exists, run the same loop serially, the process degrades
  gracefully, the roles don't change"), fan-out and independent review were executed as a
  serialized loop with preserved role separation, disjoint owned paths, read-only review passes,
  and full disk evidence. Real concurrency was NOT achieved in that original phase and this
  history remains disclosed rather than rewritten. The later parent addendum at lines above
  closed this gap with overlapping U-CONFIG/U-EXEC workers. The referee lock contention
  (real OS-level serialization) and the manifest queue are genuine, not simulated.
- The accidental-invocation guardrail is the harness-equivalent `worker-expensive-referee` stand-in
  (exit 126 on all routes), NOT an edit to the user's Claude settings. It is a guardrail against
  accidental invocation, not a security boundary: a worker could still call full_referee.sh
  directly. Genuine isolation would require separate credentials + container/process policy.

## Phase 0: Judge first
- Oracle: rung 3 differential harness (.port/judge/compare.py), 43 scenarios, exact stdout+stderr+exit.
- Baseline: 43 source observations captured (.port/judge/results/source-baseline.json).
- Two-way validation: 5 mutations on distinct comparator classes, all caught (M1 18/43, M2 40/43,
  M3 42/43, M4 42/43, M5 28/43). Mutations applied only in disposable mktemp copies.
- Source integrity: src set digest f23196f9… identical before and after mutation testing.

## Phase 1: Map and rules
- Artifacts: behavior-map.tsv (7 edges), gaps.tsv (5 closed), rulebook.md (9 rules), manifest (4 units).
- Contract↔manifest join: S-001..S-005 all covered, 0 uncovered, 0 orphaned.
- Authorization bundle SHA-256: 7fa1c825ff13f6b8598e6f4d3122c6e599c516658cf6f55085f5f7b1543d443a.
- Publication relocation rebased manifest source scopes and produced current integrity pin
  37280d4e00533ecedff4c5a89c76c3622176f53bc0e22652e30bfd62d7ae9589;
  the historical Phase-1 authorization above is retained honestly.
- Fixture provenance (sha256): base 2e291d9f, region aca22356, strict 017708ed, full 3331ce6d,
  unknown b7072030, badregion ca4e4fd8, badtimeout 49e5f3ec, badretries 4e85a3cd, badjson a216e309.

## Phase 2: Stress-test the rules
- Slice: U-CONFIG (highest-risk gap: precedence + inert strict). Slice share of this port is large
  (one of four tiny units) → KEEP-IN-PLACE verdict per stress-test.md (disposal only pays with a
  fan-out to protect). Reviewed output retained; 0 rule amendments surfaced. No disposable output
  can close a manifest row (nothing was discarded).

## Phase 3: Port everything
- Manifest: 4 total / 4 done / 0 pending / 0 blocked / 0 failed-check (under authorized digest).
- Ownership: disjoint target paths (config.py, translate.py, execute.py, cli.py); U-CLI serialized last.
- Original serial review: 2 independent adversarial read-only passes per high-risk unit
  (U-CONFIG/U-API/U-EXEC) plus U-CLI; findings 0 confirmed behavioral / 2 style-only
  not-confirmed (bare open vs context manager, both behavior-neutral incl. identical
  OSError paths). The parent concurrent addendum later confirmed one process finding:
  U-CONFIG's leaf check missed the positional consumer call shape exposed by referee 0003.
- Guardrail preflight: worker-expensive-referee denied on direct + bash-wrapper + env/absolute routes,
  all exit 126, receipts under .port/receipts/. Authorized runner (referee_runner.py) confirmed working.
- Liveness/reclaim policy: stall threshold = one unit's expected duration (seconds here); a stalled
  owner's unit is reclaimed by recording the reclaim here, recovering on-disk partial output, and
  requeuing under a new owner with the SAME unit ID; never two owners on one unit. No stall occurred
  (serial execution), so no reclaim was needed; procedure verified against manifest queue disk truth.
- Markers: 0 TODO/FIXME/XXX/HACK/BUG(port)/PERF(port)/SAFETY(port).
- Drift policy: FREEZE (source pinned and idle).

## Phase 4: Mechanical checks / serialized referee
- Referee: full_referee.sh (35 unittest + py_compile src/*.py) via referee_runner.py, serialized.
- Lock contention: A held lock (result 0001, exit 0); B (no --wait) denied "referee lock is held
  (live pid)" exit 2; C (--wait) blocked then ran (result 0002, exit 0). Real OS serialization.
- last: .port/referee/0002 exit 0, cryptographically verified (file set, sha256, 0444/0555 modes,
  COMPLETE marker, exit consistency). Tamper drill: mutated copy rejected ("mode is not 0555").

## Phase 5: Run and match
- Smoke: 3/3 (plan ok exit 0, run retry exit 0, bad region error exit 2).
- Port judge: 43/43; introduced failures: 0.
- Source baseline suite: 43/43 (differential); approved pre-existing failures: 0; unapproved: 0.
- Inherited failures: 0. Approved divergences: 0. Non-functional referees: 2/2 (zero-dep, deterministic).
- Skipped/bounded coverage: none. Tool/environment exceptions: none.

## Phase 6: Cut over
- Marker ledger: empty (0 unresolved). Drift: FREEZE. Strategy: direct swap, instant rollback.
- Pre-cutover canary: judge 43/43 + referee 0002 verified. Rollback receipt: source retained @
  bb35f057…, rollback drill re-ran source standalone (exit 0). Rollout state: retirement-pending
  (disposable; old path intentionally retained). Divergence sign-offs: none pending (0 divergences).
