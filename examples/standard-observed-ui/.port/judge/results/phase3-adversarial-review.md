# Adversarial review — Pocket Tasks port

Reviewer stance: assume the port is wrong; every finding cites a source
observation. Method: `run_port` vs live source differential over 19 tricky
inputs beyond the scenario set (`REDACTED-LOCAL-FIXTURE/adversarial.py` transcript), plus targeted
normalization probes against the source.

## Confirmed defects (fixed)

- **F-1 add text normalization (severity: high, contract B-001/B-013).**
  Port modeled add as `(text or "").strip()`. Source actually applies
  `" ".join(str(action.get("text","")).split())`:
  - internal whitespace runs (spaces, tabs, newlines) collapse to a single
    space — `"a\t b   c"` → `"a b c"`; port previously kept `"a\t b   c"`.
  - non-string values are stringified — `None`→`"None"`, `12345`→`"12345"`,
    `[1,2]`→`"[1, 2]"`, `{"k":1}`→`"{'k': 1}"`; port previously either dropped
    them ("Task cannot be empty") or crashed (`int.strip`/`.strip` AttributeError
    → 400).
  Evidence: source probes `norm-*` (double-space, tabs, list, dict, bool, float,
  null, numeric). Fix: rewrote the add branch. Guarded by scenario J-017.

- **F-2 JSON encoding (severity: medium, contract B-013).**
  Port emitted `ensure_ascii=True` (default), escaping non-ASCII to `\uXXXX`.
  Source emits raw UTF-8 bytes (`café` → `caf\xc3\xa9`). Structurally identical
  after JSON parse, so the structural judge did not catch it — a real
  byte-fidelity gap. Fix: `json.dumps(..., ensure_ascii=False)`. Guarded by
  `byte_fidelity.py` (a byte-level check the structural judge cannot see).

## Reviewed and confirmed already-correct

- Numeric/bool/float/numeric-string index coercion (`int(1.0)`, `int(True)`,
  `int("0")`), huge index → "Task not found": port matches source.
- Case-sensitivity of filter value (`"All"`) and shortcut key (`"alt+d"`):
  both treated as unknown → live "" / no change; port matches.
- Extra action keys ignored; `reset` ignores stray `text`: port matches.
- Raw-body classes (empty, whitespace, top-level array/number/string):
  400 error-class contract matches source.

## Post-fix result
0 divergences over the 19-input adversarial set; full judge 18/18; mutation 6/6;
byte_fidelity PASS. No open defects remain.
