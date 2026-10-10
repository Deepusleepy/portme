# Port status
- Mode: Standard (user override at sizing gate; honest score was 2 → Quick)
- Active phase: done
- Phase state: complete
- Gate log:
  - Sizing gate | 2026-07-22 | approver=user message: "APPROVED with one override: run this as Standard mode, not Quick … user requires full audit trail; Standard by user override." Scope (15 surfaces IN, OUT list, subparser-vs-top-level usage routing), value charter, model plan (current model all roles, single tier), build decision (typescript devDep only, npm run build → dist/, run node dist/cli.js, zero runtime deps, no CLI frameworks), and judge design approved as-is; judge to be two-way validated at the Phase 0 gate.
  - Phase 0 gate | 2026-07-22 | approver=user message: "Phase 0 gate APPROVED. I inspected phase0-validation.txt myself, self-consistency 14/14 and all four mutation classes caught … approving: the contract with all 15 surfaces at exact equivalence and the 16-row ledger; D-001 acknowledged and accepted; the frozen golden baseline (Python 3.14.6 oracle, pinned source), baseline is now frozen; any later change requires a new gate."
  - Phase 1 gate | 2026-07-22 | approver=user message: "Phase 1 gate APPROVED, the manifest is now FROZEN. Verified: all 5 units have judge-backed unit checks, all 9 gaps closed with owners, contract↔manifest join PASS (0 missing/0 orphan), 12 rules incl. R-002/R-003, dependency order U-005-first matches depmap." → Manifest frozen; later changes are amendments needing approval.
  - Phase 2 gate | 2026-07-22 | approver=user message: "Phase 2 gate APPROVED. Verified 70/70 probes incl. `--`; package.json no runtime deps; queue 5 done/0/0. RA-001 ACCEPTED as non-material (move to approved, keep G-010 closed); amortization keep-in-place accepted; F-1 handling approved; Phase 3 plan approved (5 units serial, single owner, no fan-out, referee in-loop); Phase 4 dissolve APPROVED NOW, fold survey into Phase 3, no separate gate, evidence lands in Phase 3 gate."
  - Phase 3 (+dissolved 4) gate | 2026-07-22 | approver=user message: "Phase 3 (+ dissolved 4) gate APPROVED. Verified the BigInt fix is real and the queue/judge/stress numbers. D-002 ACCEPTED (ASCII-only int parsing; fails safe, outside every exercised surface). Bookkeeping: set D-001 and D-002 to accepted with their gate/date. F-2 harvest approved; RA-001-to-approved and FREEZE drift policy confirmed." → Bookkeeping applied: D-001 accepted@Phase-0-gate, D-002 accepted@Phase-3-gate.
  - Result gate (pre-cutover) | 2026-07-22 | approver=user message: "Result ACCEPTED. I verified the Phase 5 judge log (14/14 source-vs-port) and the corrected divergence ledger myself. Done-gate arithmetic checks out: 0 introduced, 0 inherited, 0 unapproved baseline failures, 2 approved divergences, all three NF requirements met, 0 markers." → Cutover authorized.
  - Cutover gate (Phase 6, begin) | 2026-07-22 | approver=user message: "Proceed to Phase 6 cutover … D-001 and D-002 both SIGNED OFF; drift FREEZE confirmed; TODO burndown 0; declare node dist/cli.js canonical, record rollback line + retention of judge/.port audit trail; close status.md to terminal." → Note: this message authorized Phase 6 to BEGIN and to execute the listed steps; it did not itself accept the executed evidence.
  - Phase 6 evidence acceptance | 2026-07-22 | approver=user message: "Post-cutover audit … the ARTIFACTS need repair [8 defects listed] … this message is that acceptance, conditional on these repairs." → Independent audit found 8 artifact defects (port code sound); all repaired (see Errata below); acceptance of the completed Phase 6 evidence is hereby logged. Port run CLOSED.
- Approval provenance: historical gate quotes are preserved as audit evidence; the current provenance doctrine postdates the original run, and publication review established artifact/receipt consistency but did not recover the original conversation or create authority for future execution.
- Manifest/check-input authorization: historical Phase 1 approval covered the then-frozen 12-rule run, but its exact digest, commands, and check-input declarations are not recoverable from conversation provenance. Current authorization-bundle SHA-256 `b5f600b99716a82bf87a92076a678a4cea8013dee11861ff0b66b2f4fe79b95b` is publication bundle integrity for the explicitly invoked demo only; it is not original gate authority or authorization for an actual Portme run.
- Baseline command authorization: not established under current doctrine, which postdates the run; preserved gate prose names build/oracle decisions but does not prove a separately approved exact baseline command and isolated environment.
- Next concrete action: none, port complete (artifacts repaired and re-verified).
- Artifact index:
  - status/plan → `.port/status.md` (this file)
  - contract → `.port/contract.md` (Phase 0)
  - judge → `.port/judge/` (differential harness: Python oracle vs `node dist/cli.js`; Phase 0)
  - manifest/queue → `.port/manifest.tsv` (Phase 1) via `scripts/port_queue.py`
  - rulebook → `.port/rulebook.md` (Phase 1)
  - gap inventory → `.port/gaps.tsv` (Phase 1)
  - behavior map → `.port/behavior-map.tsv` (Phase 1)
  - accepted divergences → `.port/accepted-divergences.tsv` (Phase 1+)
  - source oracle → `REDACTED-SANDBOX/target-opus/notes_cli/{cli.py,commands.py}` (run `python3 -m notes_cli.cli`, Python 3.14.6)
  - target integration point → `REDACTED-SANDBOX/target-ts/src/` (built to `dist/cli.js`)
  - discovery evidence → `.port/evidence/source-baseline.txt`
- Blockers: none

> Mode note: user exercised the sizing-gate upward override to Standard for a full auditable artifact trail (frozen manifest + port_queue.py, contract+ledger, rulebook with language-migration checklist rows, gap inventory, two-way-validated differential judge, stress-test slice, per-phase gates 0–6). Per-phase gates now apply; I stop at each.

---

## Scope (restatement for confirmation)
- **Source:** `REDACTED-SANDBOX/target-opus`: a Python argparse CLI named `notes` (`notes_cli/cli.py`, `notes_cli/commands.py`), pinned as-is on disk 2026-07-22, run under **Python 3.14.6**. Subcommands `add`/`list`/`search`/`remove`, a plain-text notes file at `$NOTES_FILE` (default `~/.notes.txt`), exit codes 0/1/2, and a Click-style "did you mean" suggestion on a mistyped subcommand.
- **Target:** `REDACTED-SANDBOX/target-ts`: an empty Node package (`type: module`). Produce a faithful TypeScript port.
- **"Behaves the same" means:** for the enumerated surfaces below, identical **stdout text**, **stderr text**, **exit code**, and **notes-file format/content** given identical argv + `$NOTES_FILE` state, verified by differential comparison against the Python oracle.
- **Runnable as:** `node dist/cli.js <args>` (primary, per request). Build with the TypeScript compiler; **zero runtime dependencies**. See Build/Run plan.
- **Work boundary:** everything inside `target-ts/` (plus its `.port/`). `target-opus` is read-only oracle; nothing else is touched.

## Enumerated observable surfaces (IN scope): evidence: captured from oracle 2026-07-22
| # | Surface | Oracle behavior (must match) |
|---|---|---|
| S1 | `add <text>` | append note; stdout `Added note <N>.`; exit 0; file rewritten |
| S2 | `list` (non-empty / empty) | `<i>. <note>` per line, 1-based; empty file → no output; exit 0 |
| S3a | `search <term>` (ASCII) | case-insensitive substring (`.lower()`), print matches with their **original** 1-based index; exit 0 (S3 later split at errata: S3b = non-ASCII casing, intentionally-divergent D-001) |
| S4 | `remove <n>` valid | stdout `Removed: <text>`; exit 0; file rewritten |
| S5 | `remove <n>` out of range (0, negative, >len, empty file) | stderr `error: no note number <n>`; exit 1; file unchanged |
| S6a | `remove <non-int>` (ASCII) | stderr subparser usage + `notes remove: error: argument number: invalid int value: '<v>'`; exit 2 (S6 later split at errata: S6b = Unicode Nd digits, intentionally-divergent D-002) |
| S7 | no args | print top-level help to **stdout**; exit 0 |
| S8 | `-h` / `--help`; `add -h`, `list -h`, `search -h`, `remove -h` | print the corresponding help to stdout; exit 0 |
| S9 | mistyped subcommand, 1 close match (`lst`) | stderr top-level usage + invalid-choice + `. Did you mean 'list'?`; exit 2 |
| S10 | mistyped subcommand, ≥2 close matches (`addlis`) | `. (Did you mean one of: 'add', 'list'?)`; exit 2 |
| S11 | mistyped subcommand, no close match (`xyz`) | plain `invalid choice: 'xyz' (choose from 'add', 'list', 'search', 'remove')`; no suggestion; exit 2 |
| S12 | missing required arg (`add`, `search`, `remove`) | stderr **subparser** usage + `notes <sub>: error: the following arguments are required: <name>`; exit 2 |
| S13 | unrecognized extra args / unknown option (`add a b`, `remove 1 2`, `--bad`) | stderr **top-level** usage + `notes: error: unrecognized arguments: <rest>`; exit 2 |
| S14 | notes-file format | read skips blank/whitespace-only lines (`if line.strip()`), strips only trailing `\n`; write = each note + `\n`, whole-file rewrite, no trailing blank line |
| S15 | `$NOTES_FILE` resolution | env `NOTES_FILE` if set, else `~/.notes.txt` (home expansion); missing file reads as empty |

## OUT of scope
- Any behavior beyond the surfaces above; Python packaging/entry-point (`pyproject.toml`); `__pycache__`.
- Perfect Unicode-casing parity between Python `str.lower()` and JS `String.toLowerCase()` (ASCII parity guaranteed; exotic-locale case-folding differences are a noted potential divergence, not a target).
- Concurrency/locking on the notes file (source has none).

## Sizing: six-factor score
| Factor | Score | Evidence |
|---|---|---|
| Independent units | 1 | ~4 subcommands + parser/help/error layer + did-you-mean matcher + file store: several separable units, but one small cohesive CLI (~90 source LOC). |
| Semantic-gap severity | 1 | Direct algorithmic mapping, but several implicit behaviors to reproduce by hand: argparse **3.14.6** usage/help/error text, sub-vs-top-level prog on errors, exit-code routing, `difflib.get_close_matches` (SequenceMatcher ratio, n=3, cutoff=0.6), blank-line-skipping file read, `str.lower` semantics. No concurrency/security/data-model/architectural gap. |
| Referee cost | 0 | Deterministic CLI invocation; oracle and port both run in seconds; differential diff is free. |
| Blast radius | 0 | Sandbox CLI writing a plain-text file under `$NOTES_FILE`; trivially reversible; no money/security/prod impact. |
| Source availability | 0 | Fully readable, pinned on disk, runnable as oracle. |
| Judge availability | 0 | Public CLI surface; a differential judge (Python oracle vs `node dist/cli.js`) gives byte-exact stdout/stderr/exit + file-state comparison across the whole matrix. |
| **Total** | **2** | 0–3 range, **no** upward override (blast radius = 0, judge = 0). |

- **Whole-codebase-migration committed calls** (required by sizing.md for a language migration):
  1. **Structure-preserving**, not redesign: `cli.py`→`src/cli.ts`, `commands.py`→`src/commands.ts`, plus `src/difflib.ts` for the `get_close_matches` port.
  2. **Full build/typecheck cost:** one `tsc` run over ~3 tiny files = seconds (measured at Phase 4-equivalent; trivial).
  3. **Existing test suite:** the source has **no tests**: the judge must be **built** (differential harness), not inherited.
- **Mode verdict:** **Quick** (total 2, no override). Two gates only: this plan gate + one pre-cutover result gate; phases run uninterrupted between them.
- **Re-size trigger (quick.md):** if faithful argparse-text reproduction produces a **3rd same-symptom failure** on the same surface, or any new decision needs user approval, I pause and re-size to Standard rather than continue Quick.

## Escape verdicts considered
- **"No process needed: just implement it":** rejected. Multiple subtle observable surfaces and no existing test; real semantic reproduction work (argparse text, difflib ratio).
- **"Write fresh / use a library":** rejected. User explicitly wants a *faithful* port with matching text/exit codes/file format; the source is small, readable, and desired (not defective). Zero-dep constraint argues against pulling a CLI framework (commander/yargs) whose help/error text would diverge from argparse anyway.

## Value charter
- **Present pain:** the CLI exists only in Python; user wants it in TypeScript/Node without behavior drift.
- **Expected benefit:** a Node-runnable `notes` CLI byte-identical in observable behavior, enabling a TS toolchain with zero runtime deps.
- **Abort condition:** if matching argparse 3.14.6 help/error text verbatim proves to require an unbounded reverse-engineering effort disproportionate to value, prefer re-sizing to Standard (structured rulebook for the text layer) or renegotiating fidelity on the help-text surface (S8) with the user.

## Model plan
Model plan: current model (Opus) for implementers, reviewers, and rule-writers (default); constraints: single tier, no separate roles (Quick, single session).

## Size / calendar
- **Size band:** small. **Calendar:** ~single session (minutes–low hours). **Serialized cost driver:** getting argparse 3.14.6 usage/help/error text and the difflib ratio byte-exact, then one build + judge run.
- **Weakest evidence:** exact argparse help/usage/error text reproduction across S6a–S13 (version-specific spacing and prog selection), de-risked by the differential judge, which fails on any byte mismatch.

## Contract (what the port must do)
The port MUST produce, for every surface S1–S15, **byte-identical stdout, byte-identical stderr, the same exit code, and the same resulting notes-file bytes** as the Python oracle given the same argv and initial `$NOTES_FILE` contents. Specifically:
1. Exit codes: 0 success / help / no-command; 1 only for `remove` out-of-range; 2 for all argparse-style parse errors (invalid choice, invalid int, missing required, unrecognized args).
2. Error routing: missing-required and invalid-int errors print the **subparser** usage line and `notes <sub>: error: …`; invalid-choice and unrecognized-args print the **top-level** usage line and `notes: error: …`.
3. Did-you-mean: on invalid subcommand choice, append Click-style suggestion iff `get_close_matches(bad, [add,list,search,remove], n=3, cutoff=0.6)` is non-empty, singular `. Did you mean '<m>'?`, plural `. (Did you mean one of: <sorted, repr'd, comma-joined>?)`; else no suggestion (byte-identical to plain argparse).
4. File format: read = non-blank lines with trailing `\n` stripped; write = each note + `\n`, whole-file rewrite; `$NOTES_FILE` else `~/.notes.txt`; missing file = empty.
5. Zero runtime dependencies; `node dist/cli.js` is the entry point.

## Acceptance checklist (the judge): one item per surface, plus a negative probe
Judge = a **differential harness** (`.port/judge/`) that runs the Python oracle and `node dist/cli.js` on each scenario with a shared temp `$NOTES_FILE`, comparing stdout, stderr, exit code, and post-run file bytes. Every item retains raw evidence under `.port/evidence/`.

- **C1 (S1,S14):** `add "hello world"` then `add "Buy MILK"` → stdout `Added note 1.` / `Added note 2.`, exit 0, file = two lines. Evidence: `c1.txt`.
- **C2 (S2):** `list` on 2 notes → `1. hello world` / `2. Buy MILK`; and `list` on empty file → no output; exit 0. `c2.txt`.
- **C3 (S3a):** `search milk` → `2. Buy MILK`; `search HELLO` → `1. hello world` (case-insensitive, original index); exit 0. `c3.txt`.
- **C4 (S4):** `remove 1` on 2 notes → `Removed: hello world`, exit 0, file = remaining note. `c4.txt`.
- **C5 (S5):** `remove 5`, `remove 0`, `remove -1`, and `remove 1` on empty file → stderr `error: no note number <n>`, exit 1, file unchanged. `c5.txt`.
- **C6 (S6a):** `remove abc` → subparser usage + `invalid int value: 'abc'`, exit 2. `c6.txt`.
- **C7 (S7,S8):** no args, `-h`, `add -h`, `list -h`, `search -h`, `remove -h` → matching help to stdout, exit 0. `c7.txt`.
- **C8 (S9):** `lst` → `. Did you mean 'list'?`, exit 2. `c8.txt`.
- **C9 (S10):** `addlis` → `. (Did you mean one of: 'add', 'list'?)`, exit 2. `c9.txt`.
- **C10 (S11):** `xyz` → plain invalid-choice, no suggestion, exit 2. `c10.txt`.
- **C11 (S12):** `add`, `search`, `remove` with no positional → subparser usage + `the following arguments are required: <name>`, exit 2. `c11.txt`.
- **C12 (S13):** `add a b`, `remove 1 2`, `--bad` → top-level usage + `unrecognized arguments: <rest>`, exit 2. `c12.txt`.
- **C13 (S14,S15):** file with blank/whitespace lines reads as non-blank only; `NOTES_FILE` honored; default path logic. `c13.txt`.
- **C-neg (negative/mutation probe):** deliberately break the port (e.g. force exit 0 on invalid choice, or drop the did-you-mean suffix) and confirm the differential judge REJECTS it on the relevant item; restore → green; confirm build output byte-stable. `cneg.txt`.

## Build / run plan (decision to record)
- **Toolchain:** add **`typescript` as a devDependency only** (build-time). `tsconfig.json` targets modern Node ESM; `npm run build` runs `tsc` → `dist/cli.js` (+ `dist/*.js`). **No runtime dependencies.**
- **Run:** `node dist/cli.js <args>` (primary, as requested). `dist/cli.js` gets a `#!/usr/bin/env node` shebang; a `bin` field maps `notes`.
- **Rejected alternatives:** (a) `tsx`/`ts-node` runtime, adds a runtime dep and doesn't yield `node dist/cli.js`; (b) a CLI framework (commander/yargs), non-zero deps and its help/error text diverges from argparse, defeating the fidelity goal. Node 24 native type-stripping was considered but `tsc`→`dist` is the faithful match to the requested `node dist/cli.js`.

## Edit / implementation plan
Structure-preserving, three small files (+ config):
- `src/commands.ts`: `readNotes`/`writeNotes` (blank-skip, `rstrip("\n")`, whole-file rewrite, `$NOTES_FILE`/home default) and `add`/`listNotes`/`search`/`remove` returning exit codes; stderr for the remove range error.
- `src/difflib.ts`: faithful `getCloseMatches(word, possibilities, n=3, cutoff=0.6)` porting `SequenceMatcher.ratio` (longest-matching-block recursion; autojunk irrelevant for short inputs) + Click's `_format_possibilities`.
- `src/cli.ts`: a hand-written argparse-compatible parser layer reproducing usage/help/error text and prog selection for `notes` + 4 subparsers, wired to commands; `main(argv)` returns the process exit code; entry point calls `process.exit(main(argv))`.
- `tsconfig.json`, `package.json` scripts (`build`), `.gitignore` for `dist/`/`node_modules/` as needed.
No rollout/deploy/publish action is in scope.

## Proposed next action (on approval)
Write `.port/judge/run.sh` (oracle-vs-port differential harness) first (judge-first), validate it flags a broken port, then implement the three source files, build, and run C1–C13 + C-neg, capturing evidence, then stop at the pre-cutover result gate.

---

## Phase 0 (Judge first) gate evidence (2026-07-22)
- **Contract:** `.port/contract.md`: identification, boundary, 15 observable surfaces (all equivalence standard **exact**), 3 non-functional reqs (NF-001 zero runtime deps, NF-002 `node dist/cli.js`, NF-003 seconds), 16-row behavior ledger (B-001…B-016), done criteria. One proposed divergence D-001 (`.port/accepted-divergences.tsv`): search casing `str.lower()` vs `toLowerCase()` (ASCII-identical; non-security), flagged for sign-off.
- **Oracle rung:** #3 differential harness (source vs port), the strongest available; source has no tests so none inherited. Public CLI entry point only.
- **Judge:** `.port/judge/`: `judge.sh` (capture/compare/validate/port), `scenarios.sh` (14 scenarios J-001…J-013b → surfaces S1–S15), `scenarios.tsv` (frozen inventory), adapters (source/port/broken), frozen `golden/` baseline (provenance in README).
- **Contract coverage:** every surface S1–S15 mapped to ≥1 scenario. No coverage limits. (S15 default-path tested safely under a sandbox `$HOME`; D-001's non-ASCII casing is out-of-scope, not a judge gap.)
- **Baseline:** frozen source golden = 14/14 scenarios, deterministic. No pre-existing source failures (no source test suite; oracle is self-consistent).
- **Two-way validation** (`.port/judge/results/phase0-validation.txt`):
  - Pass direction: source vs source = **14/14 match**.
  - Fail direction: one deliberate mutation per comparator class, **all 4 CAUGHT**, stdout (add/remove output + file scenarios), stderr (did-you-mean scenarios), exit (remove-out-of-range), file (file-writing scenarios).
  - Summary: self-consistency PASS; mutations caught **4/4**.
- **Normalization:** none, all surfaces `exact`, byte-for-byte compare.
- **Runtime/cost:** full `validate` runs in seconds (14 scenarios × 6 captures). Model-plan compliance: single session, current model, no fan-out yet.
- **Raw evidence:** `.port/judge/results/phase0-validation.txt`, `.port/judge/golden/`, `.port/judge/README.md`.
- **Blockers:** none. **Awaiting:** Phase 0 gate sign-off (incl. D-001 acknowledgement) to start Phase 1.

---

## Phase 1 (Map and rules) gate evidence (2026-07-22)
- **Unit of work:** files (structure-preserving language migration, per mapping.md).
- **Behavior map** (`.port/behavior-map.tsv`): 5 target file-units + 3 source import edges (depmap) + 3 target module edges. depmap (`.port/evidence/depmap/`): **3 files, 2 edges, 0 file cycles, 0 package cycles**; source order `__init__ → commands → cli`. Zero-edge check N/A (edges present and grep-verified: `cli.py` imports `commands`, `difflib`, `os`).
- **Rulebook** (`.port/rulebook.md`): **12 rules** R-001…R-011 + R-014, plus the full language-migration decision checklist (ecosystem/banned alts, construct maps, errors, stdlib traps, memory/concurrency, numeric/text/encoding, module homes, path naming, source-bug posture). Flagged subtleties captured: **R-003** subparser-vs-top-level usage routing; **R-002** argparse-3.14.6-text fidelity (no CLI frameworks, zero runtime deps). Pending amendments: none.
- **Gap inventory** (`.port/gaps.tsv`): **9 gaps** G-001…G-009, all `closed` with a decided resolution + owning rule (universal newlines, blank-line whitespace set, `int()` parse, negative-number-as-positional, per-invocation path resolve, `repr()` quoting, exit routing, search original-index, error-routing ownership). No open gaps. High-risk gaps (G-009 routing, none open).
- **Divergences:** D-001 only (accepted Phase 0). No new divergences.
- **Candidate manifest** (`.port/manifest.tsv`): **5 units** U-001…U-005; exclusive target paths; dependency-first order U-005 → {U-001,U-002,U-003} → U-004. Each `unit_check` runs the public CLI via the judge (`checkport`) or the build+zero-dep probe, no existence-only checks; negative probe = the frozen byte-exact golden (wrong output fails). The required `check_inputs` column was added later by publication Errata pass 4 and is not represented as part of the historical Phase 1 approval.
- **Contract↔manifest join** (`.port/evidence/contract-manifest-join.txt`): **PASS**, all 15 surfaces S1–S15 mapped to ≥1 unit; 0 missing, 0 orphan. NF-001/NF-002 → U-005; NF-003 (seconds) covered by judge runtime log.
- **Queue state** (`scripts/port_queue.py status`): `0 done / 1 pending / 4 blocked / 5 total`. U-005 ready first; U-001/U-002/U-003 blocked on U-005; U-004 blocked on all. Correct topological gating.
- **Ownership conflicts:** none (disjoint target paths). **No fan-out** (single session) → no shard receipts needed.
- **Model-plan compliance:** current model, single session, rulebook authored under the approved tier.
- **Raw evidence:** `.port/behavior-map.tsv`, `.port/rulebook.md`, `.port/gaps.tsv`, `.port/manifest.tsv`, `.port/evidence/depmap/`, `.port/evidence/contract-manifest-join.txt`.
- **Blockers:** none. **Awaiting:** Phase 1 gate sign-off to freeze the manifest and start Phase 2 (stress-test slice). Per the skill, the manifest freezes only once this gate's approval is logged.

---

## Phase 2 (Stress-test rules) gate evidence (2026-07-22)
- **Amortization / keep-discard:** slice = the argparse-text + did-you-mean path (U-003+U-001), which required U-005/U-002/U-004 to run: i.e. the slice is ~100% of a 5-unit port with **no downstream fan-out**. Verdict: **KEEP IN PLACE** (stress-test.md: keep when the slice is a large fraction; disposal only pays to protect a fan-out). No disposable output; nothing bypasses review. ☑ keep/discard verdict followed, no disposable path can close a manifest row (there are none).
- **Implemented (kept):** `src/difflib.ts`, `src/commands.ts`, `src/argparse.ts`, `src/cli.ts`, `package.json`, `tsconfig.json`, `.gitignore`. Toolchain: `typescript`@7 + `@types/node` as **devDependencies only**; `dependencies: {}` (NF-001 holds). `npm run build` → `dist/`.
- **Slice judge (full suite):** `judge.sh port` → **14/14 scenarios byte-match** (differential: fresh source capture vs port; not vs `golden/`). Typecheck (`tsc --noEmit`) clean. `port_queue.py verify --check` → **5/5 units** pass their unit checks; `status` → 5 done / 0 pending / 0 blocked.
- **Adversarial stress** (`.port/judge/stress.sh`, `.port/judge/results/phase2-stress.txt`): **70/70** edge probes differentially match the source oracle (stdout+stderr+exit), attacking R-002 (argparse text), R-003 (prog routing + `--`), R-010 (int: `007`,`+2`,`1_0`,`1__0`,`5_`,`_5`,`0x10`,`1.0`,`" 3 "`), R-011 (usage/help under `-h add`, `add -h`, `list --help`, `remove -h 5`), R-014 (`-1`,`-5`,`-0`,`-1.5`, neg-as-text/term), and did-you-mean variants (`ad`,`lis`,`rmv`,`remov`,`ADD`,`serch`,…).
- **Findings by class (1 total):**
  - **F-1: implementer error / rulebook silence (fixed):** `notes --` and surplus-`--` cases diverged (source exit 2 `unrecognized arguments: --`; port had printed help exit 0). Root cause: R-003 was silent on the argparse `--` separator. Fixed in `src/argparse.ts`; all 14 `--` probes now match. Harvested as **G-010** (closed) + **RA-001** (pending rule amendment folding `--` handling into R-003). Classified **non-material** (no S1–S15 surface changes; `--` is out-of-contract observed behavior).
  - No rule defects, map errors, judge defects, or security findings. No open high-risk findings.
- **Amendments to approve:** **RA-001** (rulebook pending section), non-material clarification of R-003 for `--`. Already applied to the kept slice and differentially validated (70/70). No other amendments; contract, manifest, and equivalence standards unchanged.
- **Judge unchanged** since Phase 0 (no re-mutation needed); added a non-mutating `checkport` helper + the read-only `stress.sh` battery.
- **Measured cost / Phase 3 params** (`.port/cost-log.tsv`): 5 small units (<~60 LOC each), single owner, cheap in-loop referee (judge runs in seconds). **Phase 3 plan:** batch = all 5 serial, **no fan-out** (single session; no shared-resource contention); reviewer = adversarial read-only pass over the diff; forecast: minutes. Phase 4 (build/typecheck) is seconds, candidate to dissolve into Phase 3.
- **Raw evidence:** `.port/judge/results/phase2-stress.txt`, `.port/judge/results/port/`, `.port/gaps.tsv` (G-010), `.port/rulebook.md` (RA-001), `.port/cost-log.tsv`.
- **Blockers:** none. **Awaiting:** Phase 2 gate sign-off (incl. RA-001 disposition) to start Phase 3.

---

## Phase 3 (Port everything (+ dissolved Phase 4)) gate evidence (2026-07-22)
- Manifest: **5 total / 5 done / 0 pending / 0 blocked / 0 failed-check** (`port_queue.py verify --check` → verified 5/5; `status` → 5 done). Done = target files present + each unit's judge-backed unit check passes (negative probe = frozen byte-exact golden).
- Batch: single serial batch, all 5 units (U-005,U-001,U-002,U-003,U-004); single owner; **no fan-out**.
- **Enforcement receipt (expensive-referee deny):** N/A: no expensive referee class exists (build `tsc`, typecheck, and the differential judge are all seconds-scale and run in-loop) and there is **no worker fan-out** (single session). Per SKILL.md Standing Rule 3, the live-deny prerequisite applies only before fan-out of workers able to invoke a named expensive referee; none exist here, so it does not gate. Recorded explicitly rather than skipped silently.
- **Referees (in-loop):** `npm run build` (tsc emit) exit 0; `tsc --noEmit` typecheck **0 errors**; NF-001 `dependencies: {}` (0 runtime deps); differential judge **14/14**; stress battery **70/70**; difflib direct fuzz **448/448** identical to Python `difflib`.
- **Findings (adversarial read-only review, `.port/judge/results/phase3-review.md`):**
  - Confirmed defects: **2, both fixed**: F-1 (`--` separator, Phase 2) and **F-2 (BigInt precision** in `remove`: `Number` lost precision on >~16-digit ints, echoing `1e+22`/truncated; fixed to `bigint` end-to-end; re-probed MATCH).
  - Divergence proposed: **D-002** (F-3): Python `int()` accepts Unicode Nd digits (`remove ٣`→3); port is ASCII-only. Bounded, non-security, out of exercised surface; reproducing Unicode int() is disproportionate. Recorded in `.port/accepted-divergences.tsv` (pending) + G-011 (closed). **Awaiting user sign-off.**
  - Not-confirmed: **11** (difflib fuzz, CRLF read, embedded-newline write/read, empty-`NOTES_FILE` list, blank-line detection, negative numbers, int normalization, help paths, prog routing, search original-index/literal, exit routing), attacked, port proven correct by oracle.
  - Disputed: 0 (single reviewer; differential oracle is the tiebreaker). No open high-risk findings.
- **Review coverage:** all 5 units; deepest attacks on high-risk U-001 (448-word fuzz) and U-003 (70-probe + edge battery). Sampling minimum: 100% (5/5) given the small unit count.
- **Markers:** `TODO/FIXME/XXX/HACK/TODO(port)/BUG(port)` in `src/` → **none**.
- **Amendments this phase:** RA-001 moved to approved (folded into R-003); D-002 proposed. Manifest unchanged (fixes were within frozen units U-002/U-003, no add/split/rename/contract-ID change).
- **Keep/discard audit:** Phase 2 kept-in-place slice = the delivered units; no disposable output existed, so none closed a manifest row. ☑
- **Drift policy (recorded now per loops.md):** **FREEZE**: source `target-opus` is pinned as-is on disk 2026-07-22 and is not moving; no mirror/re-baseline needed. If the source later changes, re-baseline the golden behind a new gate.
- **Dissolved Phase 4:** mechanical survey (build+typecheck) folded into this loop per user approval; initial errors → fixed → **final 0**; no separate Phase 4 gate; evidence above.
- **Cost:** minutes; single session, current model. **Phase 5 forecast:** smoke + full judge in anger is seconds (differential harness already green); marker burndown = 0 remaining.
- **Raw evidence:** `.port/judge/results/phase3-review.md`, `phase3-difflib-fuzz.txt`, `phase3-adversarial.txt`, `phase2-stress.txt`, `.port/judge/results/port/`, `.port/cost-log.tsv`, `.port/rulebook.md` (R-003+RA-001), `.port/gaps.tsv` (G-010,G-011), `.port/accepted-divergences.tsv` (D-002).
- **Blockers:** none. **Awaiting:** Phase 3 gate sign-off (incl. D-002 disposition) to proceed to Phase 5.

---

## Phase 5 (Run and match) pre-cutover result gate evidence (2026-07-22)
- Smoke: **7/7 entry-point-class probes, 0 crashes** (no args, -h, add, list, search, remove valid/oob/non-int, invalid choice, unknown option), every exit is a clean 0/1/2. Raw: run inline (see gate message); no crash groups.
- Port judge (in anger): `judge.sh port` is a **differential** run: it captures the pinned source AND the port fresh, both now, and byte-compares them (NOT a comparison against `golden/`). Result: **14/14 scenarios match; introduced failures: 0.** Source-side classification: each scenario runs source AND port; zero mismatches → nothing to classify as port-bug/judge-bug/source-behavior. Raw: `.port/judge/results/phase5-judge.txt`.
- Source baseline / drift check, `judge.sh goldencheck` (added in errata): fresh pinned-source recapture vs the **frozen Phase 0 `golden/`** → **14/14 IDENTICAL, 0 drift** = source unchanged since Phase 0; 0 unapproved source failures; 0 approved pre-existing failures; baseline not narrowed. Raw: `.port/judge/results/phase5-golden-check.txt`.
- Inherited failures: **0** (none to classify/accept). Introduced failures: **0**.
- Approved divergences: **2**: D-001 (S3b search casing, accepted@Phase-0-gate), D-002 (S6b Unicode int, accepted@Phase-3-gate). Both ASCII-identical on the exercised surface; contract rows S3b/S6b marked `intentionally-divergent`; final sign-off at Phase 6.
- Non-functional referees: NF-001 zero runtime deps ✓ (`dependencies: {}`), NF-002 `node dist/cli.js` after `npm run build` ✓, NF-003 seconds ✓.
- Expansion evidence (beyond the 14): stress **70/70**, difflib direct fuzz **448/448** identical to Python `difflib` (real receipt `.port/judge/results/phase3-difflib-fuzz.txt`).
- **Bounded coverage (unexercised, distinct from the approved divergences):** the judge exercises only **ASCII** input, so two behavior bands are untested by construction: (BC-1) non-ASCII case-folding in `search` (S3b), the boundary that makes D-001 a divergence rather than a defect; (BC-2) Unicode Nd-digit input to `remove` (S6b), the boundary behind D-002. These are coverage boundaries (no test beyond ASCII), separate from the divergences themselves (which state how the port behaves there: D-001 uses `toLowerCase`; D-002 fails safe with the invalid-int error). Neither is a security/data-loss surface.
- Tool/environment exceptions: none. Markers in `src/`: none.
- Judge runtime/cost: seconds; single session, current model.

### Done gate (verification.md): all satisfied
- Port result: judge has no unresolved outcome. 14/14 pass; 2 approved divergences (D-001/D-002); bounded coverage BC-1/BC-2 (non-ASCII, unexercised) recorded separately, not coverage *limits* on any contracted ASCII surface. ✓
- Introduced failures: **0**. ✓
- Inherited failures: 0 (none). ✓
- Source baseline: 0 unapproved failures (identical to frozen golden). ✓
- Non-functional budgets: met. ✓
- Markers: 0 unresolved. ✓
- Divergence sign-off: D-001, D-002 accepted; final retirement sign-off at Phase 6. ✓

- **Blockers:** none. **Awaiting:** result-gate acceptance. Per ordering rule, **no cutover (Phase 6) step executes until the user accepts this result.**

---

## Phase 6 (Cut over) receipt (2026-07-22): TERMINAL
- **Marker burndown:** repo-wide scan of shipped sources (`src/`, config; excl. node_modules/dist/.git/.port) → **0** `TODO/FIXME/XXX/HACK/TODO(port)/BUG(port)`. `.port/*.md` string hits are prose describing the marker classes → classified **obsolete/documentation**, not live. Ledger: `.port/cutover-plan.md`.
- **Drift policy:** **FREEZE** confirmed, source pinned 2026-07-22 (Python 3.14.6), not moving; re-baseline behind a new gate if it ever changes.
- **Rollout:** direct swap: `node dist/cli.js` (built from `src/` via `npm run build`) is the **canonical `notes` implementation** in target-ts. Sandbox, no live traffic.
- **Release canary:** clean `rm -rf dist && npm run build` (exit 0) → judge **14/14** on the release artifact; **0 runtime deps**.
- **Rollback:** owner=user; action = revert to invoking the pinned Python source (`PYTHONPATH=<target-opus> python3 -m notes_cli.cli`), which remains runnable as the oracle. Immediate; **no reconciliation**, notes-file format is byte-identical (S14), stores interoperate, no data loss.
- **Divergence final sign-off:** D-001 and D-002 → **signed off by user at Phase 6** (`.port/accepted-divergences.tsv`).
- **Old-path retirement:** Python source **retained runnable** as oracle/rollback (not deleted). Port apparatus (`.port/` incl. judge + `golden/`) **retained as audit trail** (not deleted).
- **Recoverability window:** indefinite in sandbox, judge + source both re-runnable from disk in any session.
- **Cost:** whole run minutes, single session, current model (all roles).
- **Final done-gate:** 0 introduced / 0 inherited / 0 unapproved baseline failures; 2 approved divergences (signed off); judge 14/14; stress 70/70; difflib fuzz 448/448; typecheck 0 errors; zero runtime deps; 0 markers.

## Final artifact index (audit trail retained)
- `.port/status.md`: this log (terminal) · `.port/contract.md`, contract + 16-row ledger · `.port/manifest.tsv`. 5 frozen units
- `.port/rulebook.md`: 12 historical rules + RA-001 approved + language-migration checklist + publication check PC-001 · `.port/gaps.tsv`. G-001…G-013 (all closed)
- `.port/behavior-map.tsv` · `.port/accepted-divergences.tsv`: D-001,D-002 (signed off) · `.port/cost-log.tsv` · `.port/cutover-plan.md`
- `.port/judge/`: `judge.sh` (capture/compare/validate/port/checkport), `scenarios.{sh,tsv}`, adapters, `stress.sh`, frozen `golden/` (14), `results/` (phase0-validation, phase2-stress, phase3-review, phase3-difflib-fuzz, phase3-adversarial, phase5-judge)
- `.port/evidence/`: depmap, contract-manifest-join, source-baseline
- Shipped port: `src/{difflib,commands,argparse,cli}.ts` + `package.json`, `tsconfig.json`, `.gitignore` → `dist/cli.js`

---

## Errata (post-cutover audit): 2026-07-22
An independent reviewer audited the `.port/` trail; the shipped port code was sound but 8 artifacts needed repair. All fixed in place; no `src/` change. Re-verified after: build ok, `judge.sh port` 14/14, `goldencheck` 14/14, join PASS, queue 5 done/0/0.

1. **Empty fuzz receipt (worst).** `judge/results/phase3-difflib-fuzz.txt` was **0 bytes** (it had captured an empty *diff*, not a log) while status claimed 448/448. **Fix:** re-ran the fuzz for real: Python `difflib` vs compiled `dist/difflib.js` over 448 deterministic words, byte-comparing match sets + formatted suggestions. Result **448/448 identical** (69 words matched, 379 no-match). Wrote a self-contained 461-line receipt with the full listing. Claim substantiated, not fabricated.
2. **Contract vs divergences.** S3/S6 were `exact` while D-001/D-002 accept divergences there. **Fix:** split each, **S3a** (ASCII search) and **S6a** (ASCII int) stay `exact`; new **S3b**/**S6b** rows marked `intentionally-divergent` referencing D-001/D-002. Divergences section + ledger (B-003, B-012) updated; manifest re-pointed to S3a/S6a.
3. **Coverage honesty.** Phase 5 said "Skipped/bounded coverage: none." **Fix:** recorded two **bounded-coverage** bands distinct from the divergences. BC-1 (non-ASCII casing in search, boundary behind D-001) and BC-2 (Unicode Nd digits in remove, boundary behind D-002); done-gate line corrected (bounded coverage ≠ coverage limit).
4. **Phase 5 judge labeling.** `judge.sh port` is a **differential** (fresh source vs port), but status called it "vs frozen golden." **Fix:** added a dedicated **`goldencheck`** step (fresh source vs frozen `golden/` = the drift check), ran it → **14/14, 0 drift**, saved `judge/results/phase5-golden-check.txt`; corrected the wording in the Phase 2, 3, and 5 sections.
5. **Manifest joins.** U-005 wrongly cited **G-005** (owned by U-002) and named `pyproject.toml` (out of scope). **Fix:** removed G-005 from U-005; reworded U-005 source_scope to "target build/run wiring decision … NOT a port of pyproject.toml"; added **G-011** to U-003. Extended the join checker (`.port/evidence/contract_manifest_join.py`) to cover split surfaces **and NF-001..003**, and to accept `intentionally-divergent` rows backed by an approved divergence; re-ran → **PASS** (0 uncovered, 0 orphan).
6. **behavior-map.** Rows used `E-01…` in the `unit_id` column and one cited a non-existent **R-012**. **Fix:** all rows now key on manifest units (U-001…U-005); added a **`contract_ids`** column mapping each row/edge to its surfaces; replaced the R-012 reference with the actual rulebook Language-migration checklist item ("Module boundaries and canonical homes for shared helpers").
7. **Marker scan.** Phase 6's scan had excluded `.port/` and `dist/` yet claimed repo-wide. **Fix:** re-ran **truly repo-wide** (only `node_modules/`, `.git/` excluded) → 6 matches, **all in `.port/*.md` process/documentation text, 0 in `src/`/`dist/`/config**; each classified in `cutover-plan.md`; raw saved to `.port/evidence/phase6-marker-scan.txt`.
8. **Cost log.** Rows were all `NA`. **Fix:** filled measurable actuals: units=5, shipped src LOC=466 (argparse 208, difflib 128, commands 79, cli 51), judge/harness LOC=386, wall-clock proxies from artifact mtimes per phase; tokens/cost kept `NA` **with a stated reason** (not exposed to the agent) rather than estimated. Added a `phase-6-errata` row.

New/updated receipts: `judge/results/phase3-difflib-fuzz.txt` (real, 461 lines), `judge/results/phase5-golden-check.txt` (new), `judge/judge.sh` (`goldencheck` added; `port` relabeled differential), `evidence/contract_manifest_join.py` (new, NF+split+divergence-aware), `evidence/contract-manifest-join.txt` (re-run PASS), `evidence/phase6-marker-scan.txt` (new), `contract.md` (S3a/b, S6a/b), `manifest.tsv` (U-005 + S3a/S6a + G-011), `behavior-map.tsv` (unit_id + contract_ids + R-012 fix), `cutover-plan.md` (marker ledger), `cost-log.tsv` (actuals).

### Errata pass 2 (second post-cutover audit): 2026-07-23
A second audit found stale references left by pass 1. Fixed in place; no `src/` change. Re-verified after (battery below).

9. **Stale surface IDs.** `judge/scenarios.tsv` (J-003, J-006) and `judge/scenarios.sh` comments still cited deleted **S3/S6** → updated to **S3a/S6a**; `accepted-divergences.tsv` D-001/D-002 surface column S3/S6 → **S3b/S6b**. Grepped the whole `.port/` tree and updated every other bare reference to the split ID it means: `rulebook.md` (R-002 evidence `S6→S6a`; R-010 evidence `S6→S6a,S6b` + named-exception note), `results/phase3-review.md` (`R-010/S6→S6b`), and `status.md` prose (sizing table S3/S6→S3a/S6a with split note; weakest-evidence `S6–S13→S6a–S13`; checklist `C3 (S3)→S3a`, `C6 (S6)→S6a`), `cost-log.tsv` note. Added explicit **coverage records** to the contract divergence section: S3b = "bounded (BC-1); behavior covered by divergence approval, not scenarios"; S6b = "bounded (BC-2); …".
10. **Join checker depth.** Extended `evidence/contract_manifest_join.py` with four integrity checks: (a) every `scenarios.tsv` surface_id exists in the contract; (b) every accepted-divergence surface exists AND is marked `intentionally-divergent`; (c) every `behavior-map` contract_id exists; (d) no citation-bearing artifact cites a deleted bare **S3/S6**. **Verified it FAILS on the pre-fix state** (ran before applying fix 9 → **12 problems**: J-003/J-006 unknown surface, D-001/D-002 not-in-contract, 8 dead-ID hits) and **PASSES after** (0 problems). Receipt: `evidence/contract-manifest-join.txt`.
11. **Judge README.** Corrected the "every surface is exact" claim → **17 contract surface rows; 15 `exact` (scenario-covered); 2 `intentionally-divergent` sub-surfaces S3b/S6b (bounded coverage BC-1/BC-2, not scenario-covered)**. Relabeled `judge.sh port` as **differential (fresh source vs port)** and documented **`goldencheck`** = fresh source vs frozen `golden/` drift check (+ `checkport`). Provenance and normalization sections updated to match.
12. **Cost log per gate.** Added rows for **phase-0 (~8m), phase-1 (~13m), phase-3 (~9m, +dissolved-4 sub-note), phase-6 (~2m)** and **phase-6-errata-2 (~20m)**, using write-once artifact mtimes for active-execution wall-clock (22:03→22:45 span across phases 0–5). Noted that inter-gate **user-wait time is not file-measurable** (no writes during a gate wait), so recorded spans are active execution; tokens/cost remain **NA with the stated reason** (not exposed to the agent).

New/updated receipts (pass 2): `evidence/contract_manifest_join.py` (4 integrity checks; FAIL-then-PASS demonstrated), `evidence/contract-manifest-join.txt` (PASS, 0 problems), `judge/scenarios.tsv` + `judge/scenarios.sh` (S3a/S6a), `accepted-divergences.tsv` (S3b/S6b), `rulebook.md` (R-002/R-010 refs), `contract.md` (S3b/S6b coverage lines), `judge/README.md` (17 rows / differential vs drift), `judge/results/phase3-review.md` (S6b), `cost-log.tsv` (per-gate rows).

**Regression caught + fixed by the pass-2 battery:** the `verify --check` run exposed a latent defect from **pass-1 item 5**, editing U-005's row had dropped one tab, so `gap_ids` swallowed the `unit_check` command and `risk` ("low") was being executed as the check (`/bin/sh: low: command not found`, exit 127). Existence-only `status` had masked it (only `--check` runs the command). Restored U-005's column alignment (rule_ids='', gap_ids='', unit_check=the npm+zero-dep probe, risk=low) and rewrote the manifest as clean unquoted TSV. Re-verified: **`port_queue verify --check` = 5/5, 0 failed-check**; join+integrity PASS. This is a faithful repair of the frozen manifest's intended semantics (the unit_check content was unchanged), not a semantic amendment, no unit/path/contract-id/dependency changed.

### Errata pass 3 (self-contained publication audit): 2026-07-23
This pass audited the example as actually published under `port/`, copied it to
a fresh `/tmp` directory, and required it to verify without the dogfood
sandbox. Unlike the historical sections above, all commands in this section
use published paths. The original 14-scenario Phase 0/5 receipts remain
unchanged; the latest reproducible suite is separately recorded as 15 scenarios.

13. **Oracle was not shipped.** The adapters defaulted to redacted workstation paths, so the published judge could not run. **Fix:** copied only the four minimal, byte-identical source files/config into `source-python/` (no `.git`, `.port`, `__pycache__`, or `.pyc`), added `SHA256SUMS`, and made source/port/broken adapters default to `source-python/` and `dist/cli.js` relative to the example root. `PORTME_SOURCE_DIR` and `PORTME_DIST` remain supported.
14. **Exact S14 defect: Python `strip()` versus JavaScript `trim()`.** The port dropped U+FEFF-only lines that Python retains and retained U+001C-only lines that Python drops. Exact parity is practical, so this is **not** an approved divergence. **Fix:** R-008 now defines CPython's whitespace set; `src/commands.ts` uses it only for whitespace-only detection and leaves retained contents untouched. New J-014 drives both mismatch directions and its golden was captured from the shipped oracle. G-012 records the finding.
15. **ESM entry guard was path-spelling-sensitive.** `import.meta.url === pathToFileURL(process.argv[1]).href` could skip `main()` for `/tmp` versus `/private/tmp` on macOS. **Fix:** compare `realpathSync()` values around `fileURLToPath(import.meta.url)` and argv. PC-001/G-013 record this post-run publication verification invariant; it is outside the approved 12-rule migration count. `verify.sh` passes logical `/tmp`, physical `/private/tmp`, and explicit symlink-component probes.
16. **Judge result labels could traverse.** `capture` constructed and recursively removed `results/<label>` without validating the label. **Fix:** capture and compare require `[A-Za-z][A-Za-z0-9_-]*`, reject symlink result paths, and verify physical containment under `results/` before removal/use. Negative probes pass `../traversal-sentinel` to both capture and compare, receive exit 64, and prove the sentinel was not deleted.
17. **Published paths and pass-3 integrity.** Manifest checks still invoked nonexistent `.port/judge/...`, and the example depended on the surrounding repository's queue runner. **Fix at that time:** all live manifest checks used `port/judge/...`; the then-finalized core queue runner was vendored byte-for-byte at `scripts/port_queue.py`, with the published manifest always passed explicitly. `verify.sh` compared the then-current manifest-only digest to a reviewed publication constant and passed it to the runner. That was publication evidence under the pass-3 runner, not conversational gate approval; pass 4 below supersedes this mechanism with the finalized manifest/check-input authorization bundle. No historical Phase 1 approval is inferred.

18. **No clean one-command reproduction.** Added pinned `package-lock.json` and `./verify.sh`. Verification happens in a disposable `/tmp` copy, uses `npm ci`, and cleans only a freshly created path matching `/tmp/portme-standard-verify.*`; it never deletes build/results from the published source tree. The first dry run caught an incomplete TypeScript 7 native-platform lock, and the second caught a `set -u` local initializer in the new verifier; both were repaired before the retained passing receipt.

**Fresh receipt:** `port/evidence/errata-pass3-verification.txt`. Final clean-copy run: source hashes **4/4**; build PASS; judge pass direction **15/15**; four mutation classes caught **4/4**; source-vs-port **15/15**; golden drift **15/15**; stress **70/70**; capture/compare traversal labels rejected safely; all three ESM entry path forms PASS; publication-pinned queue **5/5**, 0 failed-check; join+integrity PASS; no `node_modules/` or `dist/` left in this example.

Historical-count note: every earlier `14/14` statement describes the evidence actually produced on 2026-07-22. J-014 and the 15-scenario results are post-publication pass-3 evidence and are not represented as part of the original run.

### Errata pass 4 (authorization-bundle schema migration): 2026-07-23
This publication-only pass adopted the finalized queue schema and stronger
authorization-bundle integrity model. It does **not** rewrite or fabricate the
historical Phase 1 gate: the old conversation provenance does not establish an
exact digest, command list, or `check_inputs` declarations for that run.

19. **Required `check_inputs` schema.** Added `check_inputs` between `gap_ids`
and `unit_check` in `port/manifest.tsv`. U-005 deliberately binds
`package.json`, `package-lock.json`, `tsconfig.json`, and
`source-python/SHA256SUMS`. U-001 through U-004 repeat the exact shared
declarations for `port/judge/judge.sh`, `port/judge/scenarios.sh`,
`port/judge/adapters/port.sh`, and `port/judge/golden/*.txt`; the finalized
runner globally deduplicates those exact repeats. Mutable `src/` and `dist/`
implementation outputs remain outside `check_inputs`.
20. **Versioned publication bundle.** Re-synced the vendored
`scripts/port_queue.py` byte-for-byte with the finalized top-level runner.
`port_queue.py digest` now covers exact manifest bytes plus sorted expanded
check-input names and bytes. The reviewed publication bundle pin is
`b5f600b99716a82bf87a92076a678a4cea8013dee11861ff0b66b2f4fe79b95b`;
the new manifest-only SHA-256 is
`35d9ee3ea7f8f8e9cf562d2ffa33392edc719ac955be47ef6bb8ac6ab079bd8a`
and is evidence only, never executable authorization. `verify.sh` compares the
current bundle digest to the reviewed pin before install/build and passes that
same constant to the queue. This is publication bundle integrity, not migration
approval, and hashing is not a sandbox.
21. **Schema-aware joins and verification.** The join checker now requires the
exact ten-column header and non-empty `check_inputs` for every unit before its
existing contract/scenario/divergence checks. It was re-run after migration.
The clean-copy verifier, official validation battery, runner identity, and pin
consistency are recorded in `port/evidence/errata-pass4-verification.txt`.
