# Validation ledger

This ledger distinguishes executed evidence from designed coverage. It is not a claim that every Portme path has been proven end to end.

## Executed dogfood

- **Quick Python framework-feature port:** `examples/quick-did-you-mean/` ports Click behavior into an argparse CLI and records the two-gate flow, source evidence, focused checks, and a real target diff.
- **Standard Python → TypeScript port:** `examples/standard-notes-py-to-ts/` records phases 0–6, a differential judge, mutation sensitivity, manifest-driven units, review findings, and final checks.
- **Standard observed-only UI behavior port:** `examples/standard-observed-ui/` packages the admitted redacted oracle plus capture/scanner/deletion receipts, 18/18 interaction/DOM-state scenarios, 6/6 caught mutations, a raw-byte fidelity guard, two review-found defects/fixes, and a 2/2 authorized queue. It exercised focus, accessibility labels, live-region text, keyboard actions, export, and error semantics through the HTTP interaction envelope. It did not run a real browser renderer, CSS, screenshots, pixel comparison, or visual diff, and it does not ship the observed source implementation.
- **Large API/config/fan-out port:** `examples/large-api-config-fanout/` packages the readable source, target, tests, current queue/referee runners, and immutable run evidence. Large-scale mode was a user-requested override on a tiny 52-line fixture. The original orchestrator's serial degradation remains recorded; a later parent addendum ran two real overlapping workers on disjoint U-CONFIG/U-EXEC paths. Both narrow suites and exit-126 guardrails fired; serialized integration result `0003` caught the config positional/environment regression, the same owner repaired only `src/config.py`, and `0004` passed 35/35 before the 43/43 differential judge. The earlier 0001/0002 receipts also prove real serialized-referee lock contention. The guardrail is a harness stand-in that tests deny firing and referee routing, not Claude settings or a security boundary.
- **Bundled script regression suites:** `scripts/tests/test_*.py` cover the queue, heuristic dependency mapper, candidate-manifest generator, and serialized referee runner. The queue cases cover versioned manifest/check-input authorization bundles, control-byte and glob-membership changes, exact cross-unit declaration deduplication, overlap rejection, and mutable-output exclusion. Passing unit tests validate those utilities in fixtures; they are not end-to-end proof of the full doctrine.

## Designed, not yet end-to-end dogfooded

- Real `.claude/settings` deny firing and bypass coverage in Claude Code.
- Genuine credential separation or container/process isolation.
- Production-scale fan-out with many workers and expensive shared referees.
- A hosted third-party observed source with real account/tier/terms boundaries.
- Actual browser rendering, CSS, screenshots, and visual/pixel diff.
- Other UI platforms, devices, locales, and accessibility implementations.
- API-version and configuration-system scale beyond the tiny bundled fixture.

The bundled examples must not be generalized into proof for these remaining
areas. In particular, the fan-out stand-in demonstrates routing and recovery,
not containment, and the observed UI example demonstrates behavior-state parity,
not visual parity.

## Deliberate gaps

- No C/C++ dependency mapper is bundled.
- No persistent build/event daemon is bundled; expensive checks use an explicit serialized runner.

Update this file only when a reproducible run and its raw receipts are added. Keep planned validation separate from executed results.

## Latest local check

- 2026-07-23: all **95** bundled utility regression tests passed with bytecode writes disabled. This validates the finalized authorization-bundle queue, depmap, manifest generator, and referee-runner fixtures; it remains utility evidence, not end-to-end proof of every designed Portme path.
- The official skill-creator `quick_validate.py` passed against this skill in a throwaway `/tmp` virtual environment using an existing external PyYAML installation; nothing was installed into the project. The frontmatter description is within the official 1024-character limit.
- The Standard example's `./verify.sh` passed from its disposable clean copy: its manifest/check-input authorization bundle matched the reviewed publication pin before install/build; source hashes 4/4, schema-aware join/integrity PASS, judge 15/15 in both pass and differential directions, mutation classes 4/4 caught, golden drift 15/15, stress 70/70, traversal and three ESM-entry probes PASS, and publication-pinned queue 5/5. This proves publication bundle integrity for the explicitly invoked demo, not conversation approval for a migration gate.
- The observed-only UI example's `./verify.sh` passed from a disposable clean copy without the source service or original dogfood paths: publication bundle pin matched, queue 2/2, judge 18/18, mutations 6/6, and byte fidelity passed. This validator sandbox forbids TCP bind, so the current validation replaced only listen/connect with a temporary `socketpair` transport while still executing the real `BaseHTTPRequestHandler` and raw response bytes; the retained raw dogfood receipts cover the original loopback HTTP run. This is not browser evidence.
- The API/config/fan-out example's `./verify.sh` passed from its own disposable clean copy: publication bundle pin matched, queue 4/4, unittest 35/35, bundled-source judge 43/43, a new serialized result was published and cryptographic `last` verification passed, and the deny/worker/reviewer plus immutable 0003/0004 receipts were checked.
- Local Markdown links, JSON parsing, TSV column structure, shell syntax, and vendored-runner byte identity all passed. No generated `node_modules/`, `dist/`, Python bytecode, or `__pycache__` remains in either shipped example.
