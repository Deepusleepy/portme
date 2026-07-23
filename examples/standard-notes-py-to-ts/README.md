# Example: Standard-mode run — Python → TypeScript language port

This is a real artifact trail from an agent using Portme in **Standard mode**
to port a small argparse-based `notes` CLI (Python 3.14.6) to TypeScript with
byte-identical results on 15 exact scenario-covered surfaces within the approved
contract scope, two bounded approved divergences, and zero runtime dependencies.
Publication edits: the run's `.port/` directory is published as `port/`, and
absolute historical workstation paths are redacted to `REDACTED-*`. The
original gate log and 14-scenario receipts remain historical evidence. Errata
pass 3 makes the published example independently reproducible: the exact
Python oracle is in `source-python/`, adapters default to relative paths, and
the latest suite has 15 scenarios. Errata pass 4 migrates the publication to
the finalized authorization-bundle schema without claiming retroactive Phase 1
approval. `PORTME_SOURCE_DIR` and `PORTME_DIST` still override those defaults.

Run the complete clean-copy verification with one command:

```sh
./verify.sh
```

It performs `npm ci`, builds in a disposable `/tmp` copy, validates the judge
in both directions, checks source hashes and goldens, runs differential and
stress suites, exercises logical/physical/symlink ESM entry paths, proves
traversal result labels are rejected, and runs the publication-pinned manifest queue.
It does not leave `node_modules/` or `dist/` in this directory.

This is a human-invoked reproduction bundle, not a migration gate. The
manifest/check-input authorization bundle SHA-256 pinned in `verify.sh` proves
that the demo is running the exact manifest plus sorted expanded declared
check-input names and bytes reviewed for publication; it does not approve them
or authorize a real Portme run. Actual Standard/Large-scale execution requires
the user-approved Phase 1 bundle digest, exact checks, and check-input
declarations from the live conversation or trusted provenance.

The run was honestly sized **2 → Quick** by the six-factor score; the user
exercised the sizing gate's override to demand the full Standard audit trail.
That override — and every other gate decision — is quoted verbatim in the
gate log inside [`port/status.md`](port/status.md).

## What to look at

- **`port/status.md`** — the historical terminal status plus three honest errata passes: mode with override
  reason, full 7-entry gate log (sizing, P0, P1, P2, P3+dissolved-4, result,
  cutover), artifact index. This is what "resumable and auditable" means.
- **`port/contract.md`** — 17 surface rows (15 `exact`, plus S3b/S6b marked
  `intentionally-divergent` with bounded-coverage records); 16-row behavior
  ledger.
- **`port/judge/`** — the differential judge, **two-way validated at Phase 0**:
  the historical source-vs-source receipt is 14/14 and four deliberate
  mutations were caught. The latest reproducible suite is 15/15 after J-014
  added exact Unicode-whitespace coverage; old receipts were not rewritten.
- **`port/manifest.tsv`** — 5 units, dependency-ordered, every `unit_check`
  substantive, with required `check_inputs` binding the build controls or the
  shared judge scripts, adapter, and goldens; driven by the vendored
  `scripts/port_queue.py`. `verify.sh` compares the current manifest/check-input
  authorization bundle digest to the reviewed publication constant before
  install/build and passes that same pin to the queue. Manifest changes,
  declared control-byte changes, or glob-membership changes fail until a
  maintainer reviews the publication bundle and updates both pin and receipt.
- **`port/rulebook.md`** — the honest 12-rule frozen Phase 1 set + the filled
  language-migration decision checklist; RA-001 shows a real amendment
  (argparse `--` separator) going pending → approved with evidence. `PC-001`
  is a post-run publication verification check, not a retroactive 13th rule.
- **`port/gaps.tsv`** — 13 gaps, all closed with recorded resolutions and
  owners; G-010/G-011 were *found by the process* (stress test and
  adversarial review), not planned up front.
- **`port/judge/results/phase3-review.md`** — the adversarial review that
  assumed the port was wrong: 2 confirmed defects (argparse `--` handling;
  BigInt precision for huge integers), 11 attacks the port survived, and one
  proposed divergence sent to the user for disposition.
- **The Errata sections at the end of `port/status.md`** — four post-cutover
  audits preserve the original evidence while repairing publication defects.
  The first two found 12 artifact defects (an empty
  fuzz receipt, a contract/divergence mismatch, stale surface IDs, a
  mislabeled judge step, join errors — pass 2's deeper join checker even
  caught a column-alignment regression introduced by pass 1). Every one was
  repaired with new receipts, the checker now fails on the pre-fix state,
  and the acceptance was re-logged. Pass 4 records the schema/bundle migration
  as publication integrity only, without fabricating historical gate approval.
  Audits finding real problems — and the trail absorbing them honestly — is
  the method working, not failing.
- **`port/accepted-divergences.tsv`** — two approved divergences (non-ASCII
  case-folding; ASCII-only int parsing) with who approved them, at which
  gate, and final Phase 6 sign-off.
- **`port/cutover-plan.md`** — direct-swap rollout, rollback line, FREEZE
  drift policy, retention of the audit trail.
- **`src/`** — the shipped port: hand-written argparse-compatible parser,
  faithful `difflib.SequenceMatcher` port, commands, wiring.
- **`source-python/`** — the byte-identical, hash-pinned Python oracle and its
  minimal `pyproject.toml`; no `.git`, `.port`, or cache artifacts.

## Why this example matters

Two genuine defects were caught **by the method, not by luck**: the stress
test exposed a rulebook silence (`--` separator semantics), and the
adversarial review exposed a numeric-precision bug that all 14 golden
scenarios passed over. Both were characterized against the oracle, fixed,
harvested into the gap inventory, and folded into the rulebook — the
repair-the-loop doctrine in action at small scale.
