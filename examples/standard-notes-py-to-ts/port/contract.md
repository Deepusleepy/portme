# Port contract

## Identification
- Source: shipped under `source-python/` (Python argparse CLI `notes`; `notes_cli/cli.py`, `notes_cli/commands.py`; byte-identical to the source pinned on 2026-07-22). Run method (oracle): `PYTHONPATH=source-python NOTES_FILE=<file> python3 -m notes_cli.cli <args>` under **Python 3.14.6**.
- Target: this example root (Node ESM package). Delivery: TypeScript in `src/`, compiled by `tsc` to `dist/`; entry point `node dist/cli.js <args>`. Zero runtime dependencies; `typescript` is a build-time devDependency only.
- Environment: macOS (darwin), Node v24.18.0, npm 11.18.0. Locale C/UTF-8. Behavior-affecting inputs: `$NOTES_FILE` (path to notes store) and `$HOME` (for default-path `~` expansion). No feature flags, no credentials, no network.

## Boundary
- In: the `notes` CLI public surface — subcommands `add`, `list`, `search`, `remove`; help/usage/error text; exit codes; did-you-mean suggestion on mistyped subcommand; the plain-text notes-file read/write format; `$NOTES_FILE`/`~/.notes.txt` resolution. Enumerated as surfaces S1–S15 below.
- Out: Python packaging/entry-point metadata (`pyproject.toml`), `__pycache__`, the `notes_cli` import structure itself; concurrency/file-locking (source has none); perfect Unicode case-folding parity between Python `str.lower()` and JS `String.toLowerCase()` beyond ASCII (see D-001).
- Retained/replaced dependencies: source uses only the Python stdlib (`argparse`, `difflib`, `re`, `ast`, `os`). Port replaces these with hand-written TypeScript (argparse-compatible parser + `difflib.getCloseMatches` port + Node `fs`/`os`/`process`). No third-party runtime dependency retained or added.

## Observable surfaces
Equivalence standard is **exact** (byte-identical stdout, stderr, exit code, and resulting notes-file bytes) for every surface unless noted. Comparator: differential harness (`port/judge/`) diffing the shipped Python oracle against `node dist/cli.js` on identical argv + initial `$NOTES_FILE`.

| ID | Surface | Input/action | Outputs and side effects | Standard | Comparator/invariant |
|---|---|---|---|---|---|
| S1 | `add <text>` | one positional | stdout `Added note <N>.\n` where N = new count; append text as a line; exit 0 | exact | diff stdout+file+exit |
| S2 | `list` | none | `<i>. <note>\n` per note, 1-based, in file order; empty store → no output; exit 0 | exact | diff stdout+exit |
| S3a | `search <term>` — ASCII term/notes | one positional | for each note whose lowercased text contains lowercased term: `<i>. <note>\n` with note's **original** 1-based index; exit 0 | exact | diff stdout+exit |
| S3b | `search <term>` — non-ASCII case-folding sub-behavior | one positional with code points where `str.lower()` ≠ `toLowerCase()` | match set may differ from source | intentionally-divergent (D-001) | out of exercised surface; see accepted-divergences.tsv |
| S4 | `remove <n>` (in range) | int positional | stdout `Removed: <text>\n`; note n removed; whole file rewritten; exit 0 | exact | diff stdout+file+exit |
| S5 | `remove <n>` (out of range: n<1, n>len, empty store) | int positional | stderr `error: no note number <n>\n`; file unchanged; exit 1 | exact | diff stderr+file+exit |
| S6a | `remove <v>` — ASCII int / non-int | int positional | valid ASCII int (incl. sign, underscores, arbitrary precision) parses; otherwise stderr `usage: notes remove [-h] number\nnotes remove: error: argument number: invalid int value: '<v>'\n`; exit 2 | exact | diff stderr+exit |
| S6b | `remove <v>` — Unicode Nd digit sub-behavior | positional with Unicode decimal digits (e.g. `٣`) | source parses via CPython int() (accepts); port rejects with the invalid-int error (fails safe) | intentionally-divergent (D-002) | out of exercised surface; see accepted-divergences.tsv |
| S7 | no args | (empty argv) | top-level help to **stdout**; exit 0 | exact | diff stdout+exit |
| S8 | help flags | `-h`, `--help`, `add -h`, `list -h`, `search -h`, `remove -h` | corresponding help to stdout; exit 0 | exact | diff stdout+exit |
| S9 | mistyped sub, 1 close match | `lst` | stderr top-level usage + `notes: error: argument command: invalid choice: 'lst' (choose from 'add', 'list', 'search', 'remove'). Did you mean 'list'?\n`; exit 2 | exact | diff stderr+exit |
| S10 | mistyped sub, ≥2 close matches | `addlis` | as S9 but suffix `. (Did you mean one of: 'add', 'list'?)`; exit 2 | exact | diff stderr+exit |
| S11 | mistyped sub, no close match | `xyz` | plain invalid-choice line, **no** suggestion suffix; exit 2 | exact | diff stderr+exit |
| S12 | missing required arg | `add`, `search`, `remove` (no positional) | stderr **subparser** usage + `notes <sub>: error: the following arguments are required: <name>\n`; exit 2 | exact | diff stderr+exit |
| S13 | unrecognized args / unknown option | `add a b`, `remove 1 2`, `--bad` | stderr **top-level** usage + `notes: error: unrecognized arguments: <rest>\n`; exit 2 | exact | diff stderr+exit |
| S14 | notes-file format | read/write round-trip, including Unicode whitespace | read: keep only lines whose Python `str.strip()` is truthy, remove exactly one trailing `\n` (retained contents unchanged); this retains U+FEFF-only lines and skips U+001C-only lines; write: each note + `\n`, whole-file overwrite | exact | diff stdout + resulting file bytes, including J-014 |
| S15 | store path resolution | `$NOTES_FILE` set / unset | use `$NOTES_FILE` if set, else `~/.notes.txt` (`$HOME` expansion); missing file → empty store | exact | diff file location+bytes (HOME sandboxed) |

## Non-functional requirements
| ID | Requirement | Workload/environment | Budget | Referee |
|---|---|---|---|---|
| NF-001 | Zero runtime dependencies | `npm ls --omit=dev` / package.json `dependencies` | dependencies = {} | inspect package.json + install tree |
| NF-002 | Runnable as `node dist/cli.js` after `npm run build` | clean checkout | build exits 0; `node dist/cli.js` works | Phase 4 build + Phase 5 smoke |
| NF-003 | Deterministic, seconds-scale per invocation | single CLI call | < 1s | judge runtime log |
| NF-004 | Self-contained reproducibility | copy this example alone; run `./verify.sh` | shipped oracle digest, `npm ci`, build, 15-scenario differential/golden checks, stress, safe-label probe, symlink entry probes, and publication-pinned bundle queue all pass; source tree gains no `node_modules`/`dist` | `verify.sh` + publication receipt |

## Behavior ledger
| ID | Observed source behavior | Required port behavior | Approved divergence |
|---|---|---|---|
| B-001 | `add`: `_read()`; append `args.text`; `_write()`; `print(f"Added note {len(notes)}.")`; return 0 | identical stdout, file effect, exit | none |
| B-002 | `list_notes`: `enumerate(_read(),1)` → `print(f"{i}. {n}")`; return 0 | identical | none |
| B-003 | `search`: `enumerate(_read(),1)`; if `term.lower() in n.lower()` → `print(f"{i}. {n}")`; return 0 | identical; JS `toLowerCase` for ASCII | D-001 (non-ASCII casing) |
| B-004 | `remove` in range: `notes.pop(n-1)`; `_write`; `print(f"Removed: {removed}")`; return 0 | identical | none |
| B-005 | `remove` out of range (`not 1<=n<=len`): `print("error: no note number {n}", file=stderr)`; return 1 | identical stderr + exit 1; file untouched | none |
| B-006 | `_read`: file missing → `[]`; else lines with `line.strip()` truthy, each `rstrip("\n")`; Python's whitespace set includes U+001C..U+001F and excludes U+FEFF | identical Python-whitespace filtering + trailing-\n strip, with retained contents unchanged | none |
| B-007 | `_write`: open 'w'; for each note write `n + "\n"` | identical bytes | none |
| B-008 | `NOTES_FILE = env NOTES_FILE or expanduser("~/.notes.txt")` resolved at import time | resolve `$NOTES_FILE` else `$HOME/.notes.txt` (`~` expansion) | none (resolve per-invocation; observationally identical for a single process) |
| B-009 | argparse: unknown subcommand → `error("argument command: invalid choice: '<bad>' (choose from 'add', 'list', 'search', 'remove')")` → usage to stderr + exit 2 | reproduce exact text, top-level usage `usage: notes [-h] command ...`, prog `notes`, exit 2 | none |
| B-010 | `NotesArgumentParser.error` appends Click suffix when `get_close_matches(bad, choices)` (difflib defaults n=3, cutoff=0.6) non-empty; `_format_possibilities`: sorted, each `repr()`, `", "`-joined; 1→`Did you mean '<m>'?`, ≥2→`(Did you mean one of: ...?)`; separator `. ` | reproduce matcher (SequenceMatcher ratio) + formatting byte-for-byte | none |
| B-011 | argparse missing required positional → subparser usage + `notes <sub>: error: the following arguments are required: <name>`; exit 2 | reproduce, with subparser prog/usage | none |
| B-012 | argparse invalid int for `remove` → subparser usage + `notes remove: error: argument number: invalid int value: '<v>'`; exit 2 | reproduce for ASCII ints (incl. sign/underscore/arbitrary-precision via BigInt) | D-002 (Unicode Nd digits) |
| B-013 | argparse unrecognized extra args / unknown option → **top-level** usage + `notes: error: unrecognized arguments: <rest>`; exit 2 | reproduce, with top-level prog even though a subparser ran | none |
| B-014 | `-h`/`--help` and each subcommand `-h` → formatted help to stdout; exit 0 (SystemExit 0) | reproduce Python 3.14.6 help text byte-for-byte (usage, `positional arguments:`, `options:`, 2-space gutter, command list indentation) | none |
| B-015 | no subcommand (`args.func` unset) → `parser.print_help()` to stdout; return 0 | identical help text to stdout; exit 0 | none |
| B-016 | `add`/`search`/`remove` help text include their positional; `list` has none | reproduce each subparser's help | none |

## Divergences (accepted)
See `port/accepted-divergences.tsv` (both signed off at Phase 6).
- **D-001** (S3b/B-003): Python `str.lower()` vs JS `String.toLowerCase()` differ for some non-ASCII code points (e.g. locale-specific/Turkish, some Unicode). Port uses `toLowerCase()`. ASCII parity is guaranteed and is all the checklist exercises. Accepted bounded divergence (accepted@Phase-0-gate; not a security/privacy/data-loss issue). The contract surface is split: S3a = ASCII search behavior (`exact`); S3b = non-ASCII casing (`intentionally-divergent`, D-001).
  - **S3b coverage:** bounded (BC-1); behavior covered by divergence approval, not scenarios (the judge exercises ASCII input only; no scenario drives non-ASCII casing).
- **D-002** (S6b/B-012): Python `int()` accepts Unicode Nd decimal digits (e.g. `٣`→3), so `remove ٣` removes note 3; the port's `pyInt` accepts ASCII `[0-9]` only and rejects non-ASCII digits with the argparse invalid-int error (exit 2, fails safe). Reproducing CPython's Unicode-aware `int()` is disproportionate; ASCII numeric input is identical. Accepted bounded divergence (accepted@Phase-3-gate; not a security/privacy/data-loss issue). Surface split: S6a = ASCII int parsing (`exact`); S6b = Unicode-digit input (`intentionally-divergent`, D-002).
  - **S6b coverage:** bounded (BC-2); behavior covered by divergence approval, not scenarios (the judge exercises ASCII input only; no scenario drives Unicode-digit input).

## Done criteria
- Latest reproducible judge suite: differential harness passes all 15 scenarios J-001…J-014 (source vs `node dist/cli.js`), byte-exact on stdout, stderr, exit, and resulting file bytes. The historical Phase 0/5 receipts remain 14-scenario receipts and are not relabeled.
- Two-way validation (Phase 0): judge passes source-vs-source and fails on every mutation-class broken adapter (stdout, stderr, exit, file).
- Mechanical checks: `npm ci` + `tsc` build exit 0 with no type errors; NF-001 zero runtime deps and NF-004 clean-copy verification pass.
- Introduced failures: zero. The source has no pre-existing test failures to inherit (no test suite); baseline = the frozen oracle transcripts.
- Marker gate: no unresolved `TODO`/`FIXME`/`XXX`/`HACK`/`TODO(port)`/`BUG(port)` in `src/`.
- Divergence gate: D-001 and D-002 carry final sign-off before cutover (both signed off at Phase 6).
