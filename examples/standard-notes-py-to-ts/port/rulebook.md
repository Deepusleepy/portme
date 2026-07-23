# Port rulebook — notes CLI (Python argparse → TypeScript)

Read-only during Phase 2/3. Cite rule IDs from implementer/fixer work; propose
amendments in the Pending section for the next gate. Governing oracle: the
Python 3.14.6 source now shipped at `source-python/`, verified byte-for-byte by
the Phase 0 differential judge and the recorded SHA-256 source baseline.

## Approved rules

### R-001 — Canonical Python→TS construct mappings
- Source pattern/condition: idiomatic Python constructs in the source.
- Required target action: map deterministically —
  - `print(x)` → write `x + "\n"` to **stdout** (`process.stdout.write`); `print(..., file=sys.stderr)` → **stderr** (`process.stderr.write`). Never use `console.log` (it can differ in newline/flush and object formatting).
  - f-strings → template literals with identical text; `{len(notes)}` → `notes.length`.
  - `enumerate(xs, 1)` → manual 1-based index.
  - Path/store resolution happens **per invocation** (G-005): `process.env.NOTES_FILE ?? join(os.homedir(), ".notes.txt")`.
- Named exceptions: none.
- Evidence/contract rows: B-001…B-008, B-015; commands.py.
- Positive: `print(f"Added note {len(notes)}.")` → `out("Added note " + notes.length + ".\n")`.
- Negative: do **not** emit via `console.log(...)` (adds its own newline handling and is not byte-guaranteed).

### R-002 — argparse-text fidelity (hand-written parser, pinned to Python 3.14.6)
- Source pattern/condition: any user-visible usage line, help body, or error message produced by argparse.
- Required target action: reproduce **byte-for-byte** the Python 3.14.6 argparse output. Hardcode/generate the exact strings observed from the oracle (see R-011 for the frozen usage/help text). Match spacing precisely: two-space gutter before help columns, `positional arguments:` and `options:` section headers (3.14 wording), the `-h, --help  show this help message and exit` line, and the subcommand list indentation under `command`.
- Named exceptions: none. The banned alternative is any third-party arg parser (commander/yargs/minimist/argparse-js) — they produce different help/error text and add runtime deps (NF-001). Zero runtime dependencies.
- Evidence/contract rows: B-009…B-016, S6a–S13; source captures in `port/judge/golden/`.
- Positive: unknown option `--bad` → `usage: notes [-h] command ...\nnotes: error: unrecognized arguments: --bad\n`, exit 2.
- Negative: emitting a commander-style `error: unknown option '--bad'` is a fidelity failure.

### R-003 — Subparser-vs-top-level usage/prog routing (the flagged subtlety)
- Source pattern/condition: an argparse error is raised while parsing.
- Required target action: route the usage banner + `prog` by error kind —
  - **Subparser owns** (prog `notes <sub>`, usage `usage: notes <sub> ...`): `type=int` conversion failure (`invalid int value`) and missing-required-positional (`the following arguments are required: <name>`).
  - **Top-level owns** (prog `notes`, usage `usage: notes [-h] command ...`): invalid subcommand choice (`invalid choice`) and the final unrecognized-arguments sweep (`unrecognized arguments: <rest>`) — even when a subparser already consumed its known args.
  - **`--` separator** (folded in from RA-001, approved 2026-07-22): the first `--` toggles positional-only mode. A `--` that a positional can consume is **removed** (`notes -- add hello`, `notes add -- hello`, `notes add -- --` → text `"--"`); a **surplus** `--` (no subcommand follows, or the parser has no positional to consume it) is reported **literally** inside `unrecognized arguments`, in token order (`notes --` → `unrecognized arguments: --`, exit 2; `notes list --`; `notes list -- extra` → `-- extra`). See G-010.
- Named exceptions: none.
- Evidence/contract rows: B-011,B-012 (sub) vs B-009,B-013 (top); G-009,G-010; captures c6/c11 (sub) vs c9/c10/c11-choice/c12 (top); `--` cases in `port/judge/results/phase2-stress.txt`.
- Positive: `notes add` (missing text) → `usage: notes add [-h] text` + `notes add: error: the following arguments are required: text`.
- Negative: `notes add a b` (extra) → **top-level** `usage: notes [-h] command ...` + `notes: error: unrecognized arguments: b` — NOT the `notes add` usage.

### R-004 — Exit-code routing
- Source pattern/condition: any program exit.
- Required target action: `0` for success, help, and no-subcommand; `1` **only** for `remove` out-of-range; `2` for every argparse-style parse error (invalid choice, invalid int, missing required, unrecognized args). Implement `main(argv: string[]): number` returning the code; parse errors throw a `ParserExit(2)` caught in `main`; help throws a `ParserExit(0)`; entry file does `process.exit(main(process.argv.slice(2)))`.
- Named exceptions: none.
- Evidence/contract rows: B-005, B-014, B-015, G-007; NF-002.
- Positive: `remove 99` on 2 notes → stderr `error: no note number 99`, exit **1**.
- Negative: exiting `0` on a parse error, or `2` on remove-out-of-range, is wrong.

### R-005 — difflib `get_close_matches` semantics
- Source pattern/condition: the did-you-mean matcher.
- Required target action: port `difflib.SequenceMatcher.ratio()` faithfully (longest-matching-block recursion; junk-free; autojunk is irrelevant since command names are far below the 200-element threshold). `getCloseMatches(word, possibilities, n=3, cutoff=0.6)`: compute `ratio` for each possibility, keep those `>= cutoff`, return the top `n` by ratio (ties broken as CPython's `heapq.nlargest` does — but final display order is fixed by R-006's sort, so selection is what matters). Use CPython defaults exactly.
- Named exceptions: none.
- Evidence/contract rows: B-010, S9–S11; cli.py:34-56.
- Positive: `get_close_matches('lst', [add,list,search,remove])` → `['list']`; `('addlis', ...)` → `['add','list']`; `('xyz', ...)` → `[]`.
- Negative: using Levenshtein distance or a naive substring test (wrong match set) fails c8/c9/c10.

### R-006 — Suggestion formatting (`_format_possibilities`, Click mirror) + Python repr
- Source pattern/condition: rendering the matched suggestions into the error message.
- Required target action: mirror Click's `_format_possibilities`: `sorted(matches)` (alphabetical), each rendered with **Python `repr()`**, joined by `", "`. 1 match → `Did you mean <p>?`; ≥2 → `(Did you mean one of: <ps>?)`. The parser appends `. ` + this phrase to the argparse invalid-choice message. Command names are fixed ASCII lowercase, so `repr(x) === "'" + x + "'"`; implement a small `pyRepr` returning the single-quoted form (with CPython's quote/escape rules as a safety net).
- Named exceptions: none.
- Evidence/contract rows: B-010; cli.py:16-33.
- Positive: matches `['list']` → `. Did you mean 'list'?`; `['add','list']` → `. (Did you mean one of: 'add', 'list'?)`.
- Negative: double quotes, unsorted order, or missing the leading `. ` separator fails c8/c9.

### R-007 — Notes-file read (universal newlines + trailing-\n strip)
- Source pattern/condition: `_read()` over the store file.
- Required target action: if the file is missing → `[]`. Else read UTF-8, apply universal-newline normalization (`\r\n` and `\r` → `\n`), split on `\n`, then keep only elements that are not whitespace-only under R-008; each kept element is the note text with its `\n` already removed and all other contents unchanged.
- Named exceptions: none.
- Evidence/contract rows: B-006, S14, G-001; commands.py:8-12.
- Positive: bytes `a\n\n   \nb\n` → notes `["a","b"]`.
- Negative: `"a\n\n".split("\n")` without dropping the trailing artifact would add a spurious empty element (harmless after trim-filter, but keep the rule to stay faithful for spaced lines).

### R-008 — Python-compatible "blank line" whitespace set
- Source pattern/condition: the `if line.strip()` skip filter.
- Required target action: decide whitespace-only using CPython's default `str.strip()`/`str.isspace()` set: U+0009–U+000D, U+001C–U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028, U+2029, U+202F, U+205F, and U+3000. Use this predicate only to filter; never trim retained contents.
- Named exceptions: none. ECMAScript `String.prototype.trim()` is prohibited here because it drops U+FEFF (which Python retains) and retains U+001C (which Python drops).
- Evidence/contract rows: B-006, S14, G-002, G-012; `source-python/notes_cli/commands.py:10`; J-013/J-014.
- Positive: `"   "` and `"\u001c"` → blank (skipped); `"\ufeff"` and `"  x  "` → retained unchanged.
- Negative: `line.trim() !== ""` fails both sides of J-014.

### R-009 — Notes-file write
- Source pattern/condition: `_write(notes)`.
- Required target action: overwrite the whole file (UTF-8); write each note followed by `"\n"`; no trailing blank line beyond each note's own `\n`.
- Named exceptions: none.
- Evidence/contract rows: B-007, S14; commands.py:14-17.
- Positive: notes `["a","b"]` → bytes `a\nb\n`.
- Negative: joining with `\n` **without** a trailing newline (`a\nb`) diverges from the source.

### R-010 — `remove` number parsing mirrors CPython `int()`
- Source pattern/condition: the `number` positional (`type=int`).
- Required target action: `pyInt(token)` mirrors CPython `int(str)` base-10: strip surrounding whitespace, optional single leading `+`/`-`, digits with optional single underscores **between** digits (`1_000` → 1000), reject empty, floats, hex, and stray characters; on any rejection produce the argparse `invalid int value: '<original token>'` error (exit 2, subparser usage per R-003).
- Named exceptions: ASCII digits only — Unicode Nd digits (which CPython `int()` accepts) are the accepted divergence D-002 (surface S6b); the port rejects them with the invalid-int error (fails safe).
- Evidence/contract rows: B-005, B-012, S6a (ASCII, exact), S6b/D-002 (Unicode-digit divergence), G-003, G-011; cli.py:71.
- Positive: `remove 1_0` → number 10; `remove +2` → 2; `remove abc` → invalid-int error.
- Negative: `Number("1.5")`/`parseInt` accept inputs Python rejects (`1.5`, `0x10`, trailing junk) — do not use them directly.

### R-011 — Frozen usage/help strings (Python 3.14.6)
- Source pattern/condition: usage and help output.
- Required target action: emit these exact strings (trailing newline as argparse does). Usage lines:
  - top: `usage: notes [-h] command ...`
  - add: `usage: notes add [-h] text`
  - list: `usage: notes list [-h]`
  - search: `usage: notes search [-h] term`
  - remove: `usage: notes remove [-h] number`
  Full help bodies (top and each subcommand) are frozen in `port/judge/golden/c7_help.txt`; reproduce them byte-for-byte, including the blank line after usage, the `Keep plain-text notes.` description on top help, `positional arguments:` / `options:` sections, and the two-space help gutter.
- Named exceptions: none.
- Evidence/contract rows: B-014, B-016, S7, S8; golden/c7_help.txt.
- Positive: `notes list -h` → `usage: notes list [-h]\n\noptions:\n  -h, --help  show this help message and exit\n`.
- Negative: `optional arguments:` (pre-3.10 wording) instead of `options:` is a version-fidelity failure.

## Language-migration decision checklist
- **Target ecosystem adoption and banned alternatives:** Node stdlib only (`node:fs`, `node:os`, `node:process`). Banned: any third-party runtime dependency, especially CLI/arg-parsing frameworks (commander, yargs, minimist, argparse-js) — they break argparse text fidelity (R-002) and violate zero-dep NF-001. `typescript` allowed **as a devDependency** for build only.
- **Canonical construct mappings:** R-001 (print/stderr, f-strings, enumerate, path resolution).
- **Errors:** R-004 — success/help = 0, remove-out-of-range = 1, parse errors = 2. Parse errors modeled as a thrown `ParserExit(code)` (precondition/usage guard, not an allocation guard) caught in `main`; command precondition failure (`remove` range) is an ordinary return value (1), not a throw. No panics/process.exit inside library functions except the single entry point.
- **Standard-library semantic traps:**
  - `str.lower()` vs `String.toLowerCase()` → search casing (D-001, accepted; ASCII-identical) — R-001/contract.
  - `str.strip()` vs `trim()` → blank-line filter; use the explicit Python set, not `trim()` (R-008).
  - `int()` vs `Number()/parseInt()` → remove parsing (R-010).
  - universal-newline text read → file read (R-007).
  - `difflib.SequenceMatcher.ratio` → did-you-mean matcher (R-005); do not substitute a different string-distance metric.
  - `repr()` → suggestion quoting (R-006).
  - argparse negative-number-as-positional (R-014).
- **Memory, ownership, and concurrency:** none — single-threaded, synchronous CLI; use synchronous `fs` calls (`readFileSync`/`writeFileSync`); no locking (source has none, out of scope).
- **Numeric, text/encoding, time, and serialization semantics:** all I/O UTF-8; no time or serialization surface; numeric only via `pyInt` (R-010). Note counts are plain integers.
- **Module boundaries and canonical homes for shared helpers:** `src/difflib.ts` hosts `getCloseMatches`, `formatPossibilities`, `pyRepr`. `src/argparse.ts` hosts the parser, `pyInt`, and usage/help/error text. `src/commands.ts` hosts the store + command implementations. `src/cli.ts` wires them and owns `main`/entry + the did-you-mean augmentation hook (mirrors `NotesArgumentParser` living in `cli.py`).
- **Target-path naming rules:** lowercase module names mirroring source (`commands.ts`, `cli.ts`); new modules named for their role (`argparse.ts`, `difflib.ts`). Compiled output under `dist/`; entry `dist/cli.js`.
- **Source-bug posture:** no known source bugs. Reproduce observed behavior exactly (it is the oracle). If a surprising behavior is discovered mid-port, mark it `BUG(port):` and raise it at a gate rather than silently "fixing" it. Security/privacy/data-loss defects would default to *do-not-reproduce* + flag — none present (a local plain-text notes file).

### R-014 — argparse negative-number-as-positional
- Source pattern/condition: a token that looks like a negative number (`-` followed by digits) in positional position.
- Required target action: because no defined option string looks like a negative number, treat such tokens as positional **values**, not options. So `remove -1` → `number = -1` (→ out-of-range → exit 1). Only `-h`/`--help` and non-numeric `-`/`--` tokens are treated as options/unrecognized.
- Named exceptions: none.
- Evidence/contract rows: G-004; source capture `remove -1` → `error: no note number -1`, exit 1.
- Positive: `remove -1` → range error exit 1.
- Negative: treating `-1` as an unknown option (`unrecognized arguments: -1`) is wrong.

## Publication verification checks (post-run; outside the approved migration rule count)

### PC-001 — ESM direct-entry identity uses physical paths
- Provenance: introduced in publication errata pass 3 after the 12-rule Phase 1 set was frozen. Publication review verified this invariant through the reproduction bundle; no retroactive rule amendment or user gate approval is claimed.
- Source pattern/condition: `src/cli.ts` must run `main()` when Node invokes the compiled file through any path spelling of that same file.
- Required target action: compare `realpathSync(process.argv[1])` with `realpathSync(fileURLToPath(import.meta.url))`; on lookup failure, treat the module as imported rather than direct. This covers `/tmp` versus `/private/tmp` on macOS and arbitrary symlinked path components.
- Named exceptions: none.
- Evidence/contract rows: NF-002, NF-004, G-013; `verify.sh` logical/physical/symlink entry probes.
- Positive: `node /tmp/<copy>/dist/cli.js add x` executes even when `import.meta.url` resolves beneath `/private/tmp`.
- Negative: comparing `import.meta.url === pathToFileURL(process.argv[1]).href` is path-spelling-sensitive and can silently skip `main()`.

## Approved amendments (applied)

### RA-001 — argparse `--` separator handling folded into R-003 — APPROVED 2026-07-22
- Disposition: user accepted as **non-material** at the Phase 2 gate ("folding `--` separator behavior into R-003 is a clarification of out-of-contract observed behavior; no contract surface or equivalence standard changes; manifest stays frozen"). Applied to R-003 above; gap **G-010** remains closed with its evidence.
- Evidence: `port/judge/results/phase2-stress.txt` — 14 `--` probes all differentially match source; full battery 70/70.

## Pending amendments
(none)
