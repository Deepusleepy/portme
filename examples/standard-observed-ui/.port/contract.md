# Port contract — Pocket Tasks (observed-only UI behavior)

## Identification
- Source: "Pocket Tasks" to-do UI, observed only over HTTP at `http://127.0.0.1:18765`.
  Health identity `{"ok": true, "version": "ui-observed-1"}`. Observation date 2026-07-23.
  Run/observation method: `GET /health`, `POST /interact` with JSON bodies, isolated
  session IDs. Internals (processes, files, source, modules) were never inspected —
  genuinely observed-only.
- Target: this self-contained Python-stdlib example (`.`), engine
  `src/pocket_tasks.py`, own public surface `GET /health` + `POST /interact`
  (default `PT_PORT=18770`). Delivery form: runnable stdlib HTTP server, zero deps.
- Environment: local loopback only; no locale/flag/tier/auth dimensions exist on the
  fixture (single anonymous shared surface). No account, credentials, or private data.

## Observed-only source limits
- Source/version/date: Pocket Tasks / `ui-observed-1` / 2026-07-23
- Authorized observation surfaces: `GET /health`, `POST /interact`
- Environments and account classes: single anonymous local session space; no tiers
- Covered scenarios: J-001..J-017, J-PII (18)
- Unobserved areas: concurrency/race behavior, session eviction/TTL, persistence across
  restart, very large inputs, non-UTF-8 bodies, HTTP methods other than the two used,
  truly empty POST body semantics, grapheme/NFC unicode normalization of task text
  (only Python str.split() whitespace-collapse is observed, not codepoint normalization).
- Confirmed assumptions: A-001, A-002, A-003 (see gaps.tsv)
- Fidelity claim: Matches recorded behavior within the coverage above. Not unqualified parity.

## Boundary
- In: reset; add (text, whitespace-trim, empty-reject); toggle index (complete/reactivate);
  delete index; filter all/active/done; shortcut Alt+D (theme) and Escape (reset view);
  the full response envelope (dom: title/theme/filter/count/empty/rows[ariaLabel,checked,text],
  export, focus, liveRegion); malformed/unknown actions and their HTTP status/error contract;
  the `/health` surface.
- Out: any real browser rendering, CSS/layout, screenshots, pixel/visual diff, browser
  automation, persistence guarantees, authentication, multi-user semantics, network
  protocol details beyond request/response JSON, and the source's internal code or storage.
- Retained/replaced dependencies: none retained; port is stdlib-only and shares no code
  with the source.

## Observable surfaces
| ID | Surface | Input/action | Outputs and side effects | Standard | Comparator/invariant |
|---|---|---|---|---|---|
| S-000 | GET /health | — | 200 `{ok, version}` | normalized | version masked to `<version>` (source-identity) |
| S-001 | POST /interact add | `{type:add,text}` | trim; empty→"Task cannot be empty"; append; live "Added X"; focus new-item; export/count update | exact | full-envelope structural diff |
| S-002 | POST /interact toggle | `{type:toggle,index}` | flip done; aria "Mark X done/active"; count=active; live "X completed/active"; focus task-N; not-found→"Task not found" keep focus | exact | structural diff |
| S-003 | POST /interact delete | `{type:delete,index}` | remove row; live "Deleted X"; focus task-N; not-found→"Task not found" keep focus | exact | structural diff |
| S-004 | POST /interact filter | `{type:filter,value}` | valid→view rows + focus filter-V + live "Showing V tasks"; invalid→live "" no change; empty view→"No tasks here" | exact | structural diff |
| S-005 | POST /interact shortcut | `{type:shortcut,key}` | Alt+D toggles theme + live "Dark/Light theme" keep focus; Escape→filter all + focus new-item + live "Reset view" (theme kept); unknown→live "" | exact | structural diff |
| S-006 | POST /interact export | any mutating action | `export` lists ALL tasks `[ ]/[x] text\n` regardless of filter | exact | structural diff |
| S-007 | POST /interact unknown/missing type | `{type:?}` / `{}` / no action | live "Unknown action"; keep focus; no change; 200 | exact | structural diff |
| S-008 | POST /interact error contract | non-int index / non-dict action / bad JSON | 400 `{"error": <ExceptionClassName>}`: ValueError / AttributeError / JSONDecodeError | exact | status + body diff |
| S-009 | routing | unknown path, GET /interact | 404 | exact | status diff |

## Non-functional requirements
| ID | Requirement | Workload/environment | Budget | Referee |
|---|---|---|---|---|
| NF-001 | Zero runtime dependencies | import/run | stdlib only | grep for third-party imports |
| NF-002 | Accessible name present on every task row | any list state | `ariaLabel` non-empty and reflects state | judge (aria in rows) |
| NF-003 | Live-region text present for every action | any action | `liveRegion` field always set | judge (present in every step) |

## Behavior ledger
| ID | Observed source behavior | Required port behavior | Approved divergence |
|---|---|---|---|
| B-001 | add trims surrounding whitespace, rejects empty/whitespace-only with "Task cannot be empty" | same | none |
| B-002 | `dom.count` = number of active (not-done) tasks regardless of filter | same | none |
| B-003 | `dom.empty` = "No tasks here" when the filtered view has no rows, else null | same | none |
| B-004 | rows are the filtered view; export is always all tasks | same | none |
| B-005 | ariaLabel = "Mark <text> done" (active) / "Mark <text> active" (done) | same | none |
| B-006 | toggle/delete out-of-range/negative/missing index → "Task not found", state+focus unchanged | same | none |
| B-007 | focus set only by add(new-item), toggle/delete(task-N), filter(filter-V), Escape/reset(new-item); other actions keep prior focus | same | none |
| B-008 | Alt+D toggles theme; Escape resets filter+focus but not theme; unknown shortcut/filter → live "" no change | same | none |
| B-009 | unknown/missing action type → live "Unknown action", no change | same | none |
| B-010 | error surface: 400 with `{"error": "<ExceptionClassName>"}` (ValueError/AttributeError/JSONDecodeError) | reproduced for parity | none — flagged as hardening candidate D-CAND-1 (see gaps.tsv), not diverged |
| B-011 | missing `session` key accepted → shared default bucket | same | none |
| B-012 | /health version string differs by build | port ships own version `pocket-tasks-port-1` | D-001 (normalized) |
| B-013 | add normalizes text as `" ".join(str(text or "").split())`: any value stringified, all whitespace runs collapsed to single spaces, ends trimmed; response is raw UTF-8 (ensure_ascii=False) | same | none — was a defect (initially modeled as `.strip()` + default ascii escaping), found in adversarial review, fixed; guarded by J-017 + byte_fidelity.py |

## Done criteria
- Differential judge J-001..J-017 + J-PII PASS against admitted redacted source goldens (18/18).
- Two-way mutation sensitivity: all 6 mutation classes caught; source file hash unchanged.
- Manifest/check-input authorization bundle verified (2/2 units, 0 failed-check).
- Capture pipeline receipt complete: quarantine 0700 outside repo, inventory, scanner run
  with version/config-digest/receipt, redaction+clean rescan, copy-not-link admission,
  quarantine deletion verified.
- No unresolved TODO(port)/BUG(port) markers except accepted, documented ones.
- Coverage limits (above) explicitly recorded; no unapproved limit.
