# Port status
- Mode: Quick
- Active phase: done
- Phase state: complete
- Gate log:
  - Quick plan gate | 2026-07-22 | approver=user message: "Approved: scope as stated, the append divergence (keep argparse's message and append the Click-style suggestion), the sizing scores and Quick mode, the model plan, the acceptance checklist C1–C5, and the single-file edit plan. No rollout in scope. Proceed to the result gate."
  - Pre-cutover result gate | 2026-07-22 | approver=user message: "Result accepted. The port is complete; no rollout, no further scope. Please finalize .port/status.md per the skill (gate log updated with this acceptance, terminal state) and end."
- Approval provenance: archival gate quotes preserved from the 2026-07-22 status; the current provenance doctrine postdates the run, and publication review established only artifact consistency, not access to the original conversation or authority for future work.
- Manifest authorization: not-applicable — Quick mode used no manifest.
- Baseline command authorization: not established and not required by the historical Quick plan; the current field postdates the run, and this redacted archive is not authorization to rerun source commands.
- Next concrete action: none — port complete, no rollout in scope.
- Artifact index:
  - status/plan → `.port/status.md` (this file)
  - source oracle → `REDACTED-SANDBOX/source-click/src/click/exceptions.py` (NoSuchCommand, `_format_possibilities`), `src/click/core.py` (Group.resolve_command)
  - target integration point → `REDACTED-SANDBOX/target-opus/notes_cli/cli.py` (`build_parser` / `main`)
  - raw evidence → `.port/evidence/` (created during execution)
- Blockers: none

## Result gate evidence (2026-07-22)
- **Edit:** `notes_cli/cli.py` only — added `NotesArgumentParser(error override)`, `_format_possibilities` (mirror of Click), and `_INVALID_CHOICE_RE`; `build_parser` now instantiates `NotesArgumentParser`. Stdlib `difflib`/`re`/`ast` only; no new dependency.
- **Checklist: 5/5 pass** (C1 singular, C2 plural, C3 no-match unchanged, C4 valid commands, C5 negative probe). Evidence: `.port/evidence/c{1..5}.txt`.
  - C1 `notes lst` → `...invalid choice: 'lst' (choose from ...). Did you mean 'list'?`, exit 2.
  - C2 `notes addlis` → `...(Did you mean one of: 'add', 'list'?)`, exit 2.
  - C3 `notes xyz` → no suggestion; `diff` vs `.port/evidence/baseline-xyz.txt` = IDENTICAL; exit 2.
  - C4 add/list/search → exit 0, normal output.
  - C5 mutation A (suppress matches) and B (wrong suggestion) both make C1 fail; restore → green; file byte-identical to pre-mutation.
- **Faithfulness cross-check vs real Click** (`click-ref.txt`, shipped alongside this file): suggestion phrase is identical for all three tokens — Click `Did you mean 'list'?` / `(Did you mean one of: 'add', 'list'?)` / (none); exit 2 in both. Only difference is the surrounding message (approved divergence: argparse `invalid choice...` wrapper vs Click's `No such command...` + usage banner).
- **Marker scan:** no TODO/FIXME/XXX/HACK/TODO(port)/BUG(port) in `notes_cli/`.
- **Divergences:** append-not-replace (pre-approved); none new.
- **Changed paths:** `notes_cli/cli.py`. **Rollback:** revert that one file (no deps, no state).
- **Cost:** exploration + one edit + checklist run; minutes. **No rollout in scope.**

## Scope (carried from confirmation)
- **Source:** Click, `source-click` working tree (pinned as-is on disk 2026-07-22). Feature: the "did you mean" subcommand suggestion produced when an unknown subcommand is given to a `Group`.
  - Oracle detail: `click/core.py:2081` raises `NoSuchCommand(cmd_name, possibilities=self.commands, ...)`. `click/exceptions.py:288-301` computes `difflib.get_close_matches(command_name, possibilities)` (difflib defaults: `n=3`, `cutoff=0.6`) and formats via `_format_possibilities` (`exceptions.py:26-33`): possibilities `sorted`, each `repr()`'d, joined by `", "`; singular → `Did you mean {p}?`, plural → `(Did you mean one of: {ps}?)`.
- **Target:** `target-opus`, argparse CLI `notes` (`notes_cli/cli.py`). Integration point: unknown-subcommand error path.
- **"Behaves the same" means:** for a mistyped subcommand, the error suggests the closest valid command name(s) using the **same matching approach** (difflib `get_close_matches`, same defaults) and the **same suggestion phrasing** as Click (singular/plural forms above), while keeping argparse as the parser and preserving the existing exit code (2).
- **In scope:** unknown/mistyped subcommand of the top-level `notes` group.
- **Out of scope:** unknown options/flags (Click's `NoSuchOption` path); success output; argument-value errors; replacing argparse's usage banner or its `invalid choice: ... (choose from ...)` wording.

## Approved-divergence note (source is oracle, not spec)
Click **replaces** the whole message (`No such command 'lst'. Did you mean 'list'?`) with its own usage banner. The task requires keeping argparse. So we **append** Click's suggestion phrase to argparse's existing message:
`argument command: invalid choice: 'lst' (choose from 'add', 'list', 'search', 'remove'). Did you mean 'list'?`
Same matcher, same suggestion phrasing; argparse message + exit code 2 preserved. This divergence is inherent to the task and is flagged for approval at this gate.

## Sizing — six-factor score
| Factor | Score | Evidence |
|---|---|---|
| Independent units | 0 | One localized behavior: a single error hook on the unknown-subcommand path. |
| Semantic-gap severity | 1 | Algorithm maps directly (both use `difflib.get_close_matches`), but integration requires a small explicit decision: append to argparse's message vs. replace it (the divergence above). No lifecycle/concurrency gaps. |
| Referee cost | 0 | Deterministic CLI invocation, completes in seconds. |
| Blast radius | 0 | Error-message text only; trivially reversible; no data/money/security impact. |
| Source availability | 0 | Source readable and pinned on disk; exact lines cited above. |
| Judge availability | 0 | Public CLI surface; acceptance checklist with deterministic stdout/stderr/exit comparison. |
| **Total** | **1** | No upward override (blast radius and judge both 0). |

- **Mode verdict:** Quick (total 1, 0–3, no override). One plan gate (this) + one pre-cutover result gate; no stops between.
- **Escape verdicts considered:** "No process needed" rejected — there is a real semantic decision (append vs. replace) and no existing test. "Write fresh / library" rejected — source is small, readable, and the desired behavior is exactly Click's, not a defect.
- **Size band:** small. **Calendar:** minutes. **Serialized cost driver:** the single edit + checklist run.
- **Weakest evidence:** the plural-message CLI path — with only 4 dissimilar commands, few tokens yield ≥2 close matches. Verified reachable via `notes addlis` → `['add', 'list']` (checklist item 2 covers it).

## Value charter
- **Present pain:** argparse's `invalid choice` error lists all commands but offers no "closest match" hint, unlike Click.
- **Expected benefit:** mistyped subcommands get a targeted suggestion, matching Click's UX.
- **Abort condition:** if preserving argparse's exit code or usage banner turned out to conflict with producing a Click-faithful suggestion (it does not — append works cleanly), prefer staying put.

## Model plan
Model plan — current model (Opus) for implementers, reviewers, and rule-writers (default); constraints: single tier, no separate roles (Quick).

## Contract (what the port must do)
1. On an unknown top-level subcommand, argparse still prints its usage line + `notes: error: argument command: invalid choice: '<bad>' (choose from ...)` to stderr and exits **2**.
2. When `difflib.get_close_matches('<bad>', <valid subcommand names>)` (defaults `n=3`, `cutoff=0.6`) is non-empty, the error message is augmented with Click's suggestion phrase:
   - 1 match → `Did you mean '<m>'?`
   - ≥2 matches → `(Did you mean one of: '<m1>', '<m2>'?)` with matches `sorted` and each `repr()`'d, joined by `", "`.
3. When there are no close matches, the output is byte-for-byte the current argparse behavior.
4. argparse remains the parser; no new dependency beyond stdlib `difflib`.

## Acceptance checklist (the judge)
- **C1 — singular suggestion.** Setup: `NOTES_FILE=/tmp/n.txt`. Action: `notes lst`. Expect: stderr contains argparse usage + error, ending with ` Did you mean 'list'?`; exit code 2. Evidence: `.port/evidence/c1.txt`.
- **C2 — plural suggestion.** Action: `notes addlis`. Expect: error contains `(Did you mean one of: 'add', 'list'?)`; exit 2. Evidence: `.port/evidence/c2.txt`.
- **C3 — no close match unchanged.** Action: `notes xyz`. Expect: NO "Did you mean" text; message identical to pre-port argparse output; exit 2. Evidence: `.port/evidence/c3.txt`.
- **C4 — valid command unaffected.** Action: `notes list` (and one more valid command). Expect: normal behavior, exit 0. Evidence: `.port/evidence/c4.txt`.
- **C5 — negative/mutation probe.** Temporarily break the matcher (e.g. force zero suggestions or wrong exit code); confirm C1 fails; restore; rerun C1 green. Evidence: `.port/evidence/c5.txt`.

## Edit plan
Single file: `notes_cli/cli.py`. Add a small `ArgumentParser` subclass overriding `error()` that (a) detects the invalid-subcommand-choice message, (b) reads valid subcommand names from the `_SubParsersAction`, (c) extracts the bad token, (d) computes `get_close_matches`, and (e) appends the Click-style suffix before delegating to the normal argparse `error()` (which prints usage + exits 2). Add a `_format_possibilities` helper mirroring Click's. No rollout/deploy action in scope.
