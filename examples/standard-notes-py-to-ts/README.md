# Example: Standard mode, Python to TypeScript

A real Portme run in **Standard mode**: a small argparse `notes` CLI (Python 3.14.6) ported to TypeScript. It is byte-identical on 15 exact surfaces inside the approved contract, with two bounded approved differences and no runtime dependencies.

Publication edits: the run's `.port/` directory is published as `port/`, and absolute workstation paths are redacted to `REDACTED-*`. The original gate log and 14-scenario receipts stay as historical evidence. Errata pass 3 makes the example reproducible on its own: the Python oracle is in `source-python/`, adapters default to relative paths, and the latest suite has 15 scenarios. Errata pass 4 moves the publication onto the final authorization-bundle schema. It does not claim that Phase 1 was approved after the fact. `PORTME_SOURCE_DIR` and `PORTME_DIST` still override those defaults.

Run the clean-copy check with:

```sh
./verify.sh
```

It runs `npm ci`, builds in a disposable `/tmp` copy, validates the judge in both directions, checks source hashes and goldens, runs the differential and stress suites, tries logical, physical, and symlink ESM entry paths, rejects traversal result labels, and runs the publication-pinned manifest queue. It does not leave `node_modules/` or `dist/` in this directory.

This is a reproduction bundle you invoke by hand, not a migration gate. The authorization bundle SHA-256 pinned in `verify.sh` shows that the demo is running the exact manifest plus the declared check-input names and bytes reviewed for publication. It does not approve them, and it does not authorize a live Portme run. A real Standard or Large-scale run needs the user-approved Phase 1 bundle digest, exact checks, and check-input declarations from the conversation.

The six-factor score was **2**, which would have been Quick. The user overrode that and asked for the full Standard trail. That override, and every other gate decision, is quoted in the gate log in [`port/status.md`](port/status.md).

## What to look at

- **`port/status.md`**: historical final status plus three errata passes. Mode and override reason, a 7-entry gate log (sizing, phases 0, 1, 2, 3 with phase 4 folded in, result, cutover), and the artifact index.
- **`port/contract.md`**: 17 surface rows (15 `exact`, plus S3b and S6b marked `intentionally-divergent` with bounded-coverage records) and a 16-row behavior ledger.
- **`port/judge/`**: the differential judge, checked both ways at Phase 0. The historical source-vs-source receipt is 14/14, and four deliberate mutations were caught. The latest reproducible suite is 15/15 after J-014 added exact Unicode-whitespace coverage. Old receipts were not rewritten.
- **`port/manifest.tsv`**: 5 units, dependency-ordered, every `unit_check` real, with `check_inputs` binding the build controls or the shared judge scripts, adapter, and goldens. Driven by the vendored `scripts/port_queue.py`. `verify.sh` compares the current bundle digest to the reviewed publication constant before install and build, and passes that same pin to the queue. Manifest changes, declared control-byte changes, or glob-membership changes fail until a maintainer reviews the publication bundle and updates both the pin and the receipt.
- **`port/rulebook.md`**: the 12 rules frozen at Phase 1, plus the language-migration checklist. RA-001 is a real amendment (the argparse `--` separator) going from pending to approved with evidence. `PC-001` is a later publication check, not a 13th rule added after the fact.
- **`port/gaps.tsv`**: 13 gaps, all closed with resolutions and owners. G-010 and G-011 were found by the stress test and the adversarial review, not planned up front.
- **`port/judge/results/phase3-review.md`**: a review that assumed the port was wrong. Two confirmed defects (argparse `--` handling, and BigInt precision for huge integers), 11 attacks the port survived, and one proposed divergence sent to the user.
- **Errata at the end of `port/status.md`**: four post-cutover audits. They keep the original evidence and repair publication defects. The first two found 12 artifact defects (an empty fuzz receipt, a contract/divergence mismatch, stale surface IDs, a mislabeled judge step, and join errors). Pass 2's deeper join checker also caught a column-alignment regression that pass 1 had introduced. Each one was repaired with a new receipt, the checker now fails on the pre-fix state, and the acceptance was logged again. Pass 4 records the schema and bundle migration as publication integrity only. It does not invent a historical gate approval.
- **`port/accepted-divergences.tsv`**: two approved divergences (non-ASCII case-folding, and ASCII-only int parsing), with who approved them, at which gate, and the Phase 6 sign-off.
- **`port/cutover-plan.md`**: direct swap, the rollback line, a FREEZE drift policy, and the audit trail kept in place.
- **`src/`**: the shipped port. A hand-written argparse-compatible parser, a `difflib.SequenceMatcher` port, commands, and wiring.
- **`source-python/`**: the hash-pinned Python oracle and its minimal `pyproject.toml`. No `.git`, `.port`, or cache artifacts.

## Why this example matters

Two real defects were caught by the process. The stress test found a missing rule for `--` separator behavior. The adversarial review found a numeric-precision bug that all 14 saved scenarios had passed. Both were checked against the oracle, fixed, added to the gap inventory, and folded into the rulebook.
