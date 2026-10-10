# Validation ledger

This ledger separates what has been run from what is only designed. It is not a claim that every Portme path has been proven end to end.

## Runs that were actually executed

- **Quick Python framework-feature port.** `examples/quick-did-you-mean/` ports Click behavior into an argparse CLI. It records the two-gate flow, source evidence, focused checks, and a real target diff.
- **Standard Python to TypeScript port.** `examples/standard-notes-py-to-ts/` records phases 0–6, a differential judge, mutation sensitivity, manifest-driven units, review findings, and final checks.
- **Standard observed-only UI behavior port.** `examples/standard-observed-ui/` keeps the admitted redacted oracle plus capture, scanner, and deletion receipts. It records 18/18 interaction and DOM-state scenarios, 6/6 caught mutations, a raw-byte fidelity guard, two defects found in review and then fixed, and a 2/2 authorized queue. The exercised surface is focus, accessibility labels, live-region text, keyboard actions, export, and error behavior, through the HTTP interaction envelope. It did not run a real browser, CSS, screenshots, pixel comparison, or a visual diff, and it does not ship the observed source.
- **Large API, config, and fan-out port.** `examples/large-api-config-fanout/` keeps the readable source, target, tests, current queue and referee runners, and historically immutable run evidence. Git cannot retain `0444`/`0555` read-only modes, so the packaged verifier accepts only the original modes or Git-normalized `0644`/`0755`, rebuilds read-only modes in its disposable copy, and then checks the result contents and metadata cryptographically. Large-scale mode was a user-requested override on a tiny 52-line fixture. The first orchestrator had no worker launcher, so it ran the units one at a time, and that history is still recorded. A later parent addendum ran two real overlapping workers on disjoint U-CONFIG and U-EXEC paths. Both narrow suites and the exit-126 guardrails fired. Serialized integration result `0003` caught the config positional and environment regression. The same owner repaired only `src/config.py`, and `0004` passed 35/35 before the 43/43 differential judge. The earlier 0001 and 0002 receipts also show real lock contention on the serialized referee. The guardrail is a harness stand-in that tests deny firing and referee routing. It is not Claude settings, and it is not a security boundary.
- **Bundled script tests.** `scripts/tests/test_*.py` cover the queue, the heuristic dependency mapper, the candidate-manifest generator, and the serialized referee runner. The queue cases cover versioned manifest and check-input authorization bundles, control-byte and glob-membership changes, exact cross-unit declaration deduplication, overlap rejection, and mutable-output exclusion. Passing these tests validates those utilities on fixtures. It is not end-to-end proof of the whole method.

## Designed, not yet run end to end

- Real `.claude/settings` deny firing and bypass coverage in Claude Code.
- Real credential separation, or container and process isolation.
- Production-scale fan-out with many workers and expensive shared referees.
- A hosted third-party observed source with real account, tier, and terms boundaries.
- Actual browser rendering, CSS, screenshots, and visual or pixel diff.
- Other UI platforms, devices, locales, and accessibility implementations.
- API-version and configuration-system scale beyond the tiny bundled fixture.

Do not generalize the bundled examples into proof for these remaining areas. The fan-out stand-in shows routing and recovery, not containment. The observed UI example shows behavior-state parity, not visual parity.

## Deliberate gaps

- No C/C++ dependency mapper is bundled.
- No long-running build or event daemon is bundled. Expensive checks use an explicit serialized runner.

Update this file only when a reproducible run and its raw receipts are added. Keep planned validation separate from executed results.

## Latest local check

- 2026-07-23: all **95** bundled utility regression tests passed with bytecode writes disabled. This validates the finalized authorization-bundle queue, depmap, manifest generator, and referee-runner fixtures. It remains utility evidence, not end-to-end proof of every designed Portme path.
- The official skill-creator `quick_validate.py` passed against this skill in a throwaway `/tmp` virtual environment, using an existing external PyYAML installation. Nothing was installed into the project. The frontmatter description is within the official 1024-character limit.
- The Standard example's `./verify.sh` passed from its disposable clean copy. The manifest and check-input authorization bundle matched the reviewed publication pin before install and build. Source hashes 4/4, schema-aware join and integrity PASS, judge 15/15 in both pass and differential directions, mutation classes 4/4 caught, golden drift 15/15, stress 70/70, traversal and three ESM-entry probes PASS, and publication-pinned queue 5/5. This proves publication bundle integrity for the explicitly invoked demo, not conversation approval for a migration gate.
- The observed-only UI example's `./verify.sh` passed from a disposable clean copy without the source service or original run paths. The publication bundle pin matched, queue 2/2, judge 18/18, mutations 6/6, and byte fidelity passed. This validator sandbox forbids TCP bind, so that validation replaced only listen and connect with a temporary `socketpair` transport, while still running the real `BaseHTTPRequestHandler` and raw response bytes. The retained raw receipts cover the original loopback HTTP run. This is not browser evidence.
- The API and config example's `./verify.sh` passed from its own disposable clean copy. The publication bundle pin matched, queue 4/4, unittest 35/35, bundled-source judge 43/43, a new serialized result was published and cryptographic `last` verification passed, and the deny, worker, reviewer, and historically immutable 0003/0004 receipts were checked. A later clean clone of the first remote `v0.1.0` tag showed that Git normalizes non-executable modes to `0644` files and `0755` directories. The verifier was corrected to validate the source checkout before copying, accept only original `0444`/`0555` or Git-normalized modes, rebuild read-only modes in its disposable copy, and reject unexpected modes. Both the normalized-mode probe and the rejection probe pass. No GitHub release was created from the failed tag.
- Local Markdown links, JSON parsing, TSV column structure, shell syntax, and vendored-runner byte identity all passed. No generated `node_modules/`, `dist/`, Python bytecode, or `__pycache__` remains in either shipped example.
