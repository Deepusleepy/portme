# Port contract

## Identification
- Source: `source/legacy_adapter.py` (readable, pinned by
  sha256 recorded in status.md; run method `python3 source/legacy_adapter.py <argv>`).
- Target: `.` — zero-dependency Python 3 package
  (`src/{config,translate,execute,cli}.py`); CLI entry `python3 src/cli.py`.
- Environment: macOS, CPython 3.14, POSIX locale; only env var consulted is
  `PORTME_TIMEOUT_MS`. Credential class: none. No network, no filesystem writes
  beyond stdout/stderr.

## Boundary
- In: `plan` and `run` subcommands; config resolution (defaults/file/env/CLI);
  v1→v2 request translation; validation and error surface; retry semantics;
  canonical JSON stdout; stderr error text; exit codes.
- Out: no new commands, no persistence, no logging, no config keys beyond the
  legacy four; `strict` remains accepted-but-inert (not newly wired).
- Retained/replaced dependencies: none (stdlib only, both sides).

## Observable surfaces
| ID | Surface | Input/action | Outputs and side effects | Standard | Comparator/invariant |
|---|---|---|---|---|---|
| S-001 | CLI `plan` | argv + --request JSON | canonical JSON v2 plan on stdout; exit 0 | exact | differential judge (bytes) |
| S-002 | CLI `run` | argv + --request + --sequence | canonical JSON result envelope; retry only on 503 up to maxAttempts; exit 0 | exact | differential judge (bytes) |
| S-003 | Config resolution | --config file, PORTME_TIMEOUT_MS, --timeout-ms/--retries/--region | effective config; precedence file<env<CLI; validation errors | exact | differential judge + unit tests |
| S-004 | Request translation | --request v1 JSON | v2 shape {subject,data,meta}; validation errors | exact | differential judge + unit tests |
| S-005 | Error/exit surface | any invalid input | `error: <msg>\n` on stderr, exit 2; argparse errors exit 2 | exact | differential judge (stderr+code) |

## Non-functional requirements
| ID | Requirement | Workload/environment | Budget | Referee |
|---|---|---|---|---|
| NF-001 | Zero runtime dependencies | import of any src module | no third-party import | py_compile + code review |
| NF-002 | Deterministic output | identical argv/env | byte-identical to source | differential judge |

## Behavior ledger
| ID | Observed source behavior | Required port behavior | Approved divergence |
|---|---|---|---|
| B-001 | defaults timeout_ms=1000,retries=2,region=us-east,strict=True | same | none |
| B-002 | precedence defaults<file<PORTME_TIMEOUT_MS<CLI | same | none |
| B-003 | unknown config keys -> `unknown config keys: <sorted>` exit2 | same | none |
| B-004 | timeout<=0/retries∉[0,5]/region∉{us-east,eu-west} -> ValueError exit2 | same | none |
| B-005 | request keys must be exactly {user_id,payload} | same | none |
| B-006 | user_id must be str or int; bool accepted (int subtype)->"True"/"False" | same | none |
| B-007 | v2 shape {subject.id:str, data:payload, meta:{region,timeoutMs,maxAttempts=retries+1}} | same | none |
| B-008 | run: only 503 retryable, bounded by maxAttempts | same | none |
| B-009 | error env: ok=200<=s<300; error=null if s<400 else temporary(503)/upstream | same | none |
| B-010 | stdout canonical JSON sort_keys+compact separators; error to stderr; exit 0/2 | same | none |
| B-011 | `strict` key accepted but never read (inert) | same | none |

## Done criteria
- Differential judge (43 scenarios) passes exact stdout+stderr+exit on all rows.
- Every manifest unit_check passes under the authorized bundle digest.
- `python3 -m py_compile src/*.py` clean; zero runtime imports.
- Zero introduced failures; zero unresolved TODO/BUG/PERF/SAFETY(port) markers.
- No approved divergences (accepted-divergences.tsv empty).
