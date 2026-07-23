# Phase 3 — Adversarial read-only review (assume the port is WRONG)

Reviewer stance: separate read-only pass; every objection cites a rulebook/contract/source line and is adjudicated by the differential oracle (not opinion). Verdicts: **confirmed** (real defect, fixed), **not-confirmed** (attacked, port proven correct), **divergence** (real, proposed for sign-off), **acceptable**.

## Confirmed defects (found + fixed this phase)
| ID | Unit | Objection (rule) | Evidence | Disposition |
|---|---|---|---|---|
| F-1 | U-003 | R-003 silent on `--` separator; `notes --` prints help exit 0 vs source exit 2 `unrecognized arguments: --` | phase2-stress.txt | FIXED in argparse.ts; G-010 closed; RA-001 folded into R-003 (approved). 14 `--` probes now match. |
| F-2 | U-003/U-002 | R-010 int used JS `Number` → precision loss: `remove 9999999999999999999999` echoed `1e+22`; 20-digit → `…67000` | phase3-adversarial.txt | FIXED: `pyInt` returns `bigint`, `remove(n: bigint)`; range check + echo now exact. Re-probed: MATCH. |

## Divergence (real, proposed for sign-off)
| ID | Unit | Objection (rule) | Evidence | Disposition |
|---|---|---|---|---|
| F-3 → D-002 | U-003 | R-010/S6b: Python `int()` accepts Unicode Nd digits (`remove ٣` → removes note 3, exit 1); port rejects → invalid-int exit 2 | phase3-adversarial.txt | Proposed **accepted divergence D-002** (ASCII-only int, surface S6b). Reproducing CPython Unicode int() is disproportionate; ASCII surface (S6a) identical; non-security. Awaiting user sign-off. G-011 closed → D-002. |

## Not-confirmed (attacked hard, port proven correct)
| # | Unit | Attack (rule) | Oracle result | Verdict |
|---|---|---|---|---|
| A-1 | U-001 | R-005/R-006: is `getCloseMatches` truly bit-identical to `difflib`? Fuzzed **448 words** (typos, deletions, insertions, transpositions, 400 random) comparing match sets AND formatted suggestion strings | `diff` IDENTICAL (phase3-difflib-fuzz.txt) | not-confirmed — port correct |
| A-2 | U-002 | R-007: does universal-newline read hold for CRLF? `a\r\nb\r\n` | both `1. a / 2. b` | not-confirmed |
| A-3 | U-002 | R-007/R-009: note text containing an embedded newline (`add $'l1\nl2'`) — write embeds `\n`, next read splits into 2 notes? | source & port both split identically; file bytes match | not-confirmed |
| A-4 | U-002 | R-001/S15: `NOTES_FILE=""` (set-but-empty) → does `list` diverge? | both exit 0, empty (existsSync("")/os.path.exists("") both false) | not-confirmed |
| A-5 | U-002 | R-008: blank/whitespace-only line detection (`trim` vs `str.strip`) on tabs/spaces | c13 golden + stress match | not-confirmed |
| A-6 | U-003 | R-014: negative-number-as-positional across `-1,-5,-0,-1.5`, neg-as-text/term | 70/70 stress match | not-confirmed |
| A-7 | U-003 | R-010: int normalization `007,+2,1_0,1__0,5_,_5,0x10,1.0," 3 "` | 70/70 stress match | not-confirmed |
| A-8 | U-003 | R-011: help/usage under alt paths `-h add`, `add -h`, `list --help`, `remove -h 5` | 70/70 stress match | not-confirmed |
| A-9 | U-003 | R-003: prog routing sub-vs-top for missing/invalid-int/unrecognized/invalid-choice | c6/c11/c12 golden + stress match | not-confirmed |
| A-10 | U-002 | R-001/G-008: search prints ORIGINAL 1-based index and is a literal (non-regex) substring, case-insensitive | c3 golden + `search "beta g"` match | not-confirmed |
| A-11 | U-004 | R-004: exit-code routing 0/1/2 across all surfaces incl. no-command help | 14/14 judge match | not-confirmed |

## Style/observations (non-behavioral, no action)
- `NOTES_FILE=""` + `add` crashes on both sides (source: Python traceback; port: Node stack) with differing text — pathological environment, out of the 15 contracted surfaces; not reproduced verbatim (a crash-message divergence on an invalid store path). Recorded as a known non-covered pathological input, not a defect.

## Coverage of review
All 5 units reviewed. High-risk units U-001 (difflib) and U-003 (argparse) received the deepest attacks (448-word fuzz; 70-probe + edge battery). 2 confirmed defects (both fixed), 1 divergence (D-002, proposed), 11 not-confirmed. No open high-risk findings. No disputed findings (single reviewer; oracle is the tiebreaker).
