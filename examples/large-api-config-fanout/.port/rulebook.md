# Port rulebook

## Approved rules

### R-001: Config defaults are frozen
- Source pattern/condition: DEFAULTS = timeout_ms=1000, retries=2, region=us-east, strict=True
- Required target action: reproduce exactly; ALLOWED = set(DEFAULTS)
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:4; S-003, B-001
- Positive example: load_config(None,env={}) -> those four values
- Negative example: emitting only three keys or a different timeout is wrong

### R-002: Config precedence is defaults < file < PORTME_TIMEOUT_MS < CLI
- Source pattern/condition: file update, then env override, then CLI-if-not-None
- Required target action: apply in that exact order; env applies whenever present; CLI value applied only when the arg is not None
- Named exceptions: only timeout_ms has an env layer; retries/region have file+CLI only
- Evidence and contract rows: legacy_adapter.py:15-19; S-003, B-002, G-002
- Positive example: config=100, env=250, --timeout-ms 999 -> 999
- Negative example: letting env override an explicit CLI value

### R-003: `strict` is accepted but inert
- Source pattern/condition: strict in DEFAULTS/ALLOWED, never read after load
- Required target action: validate as a known key, store it, never branch on it
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:4; B-011, G-001
- Positive example: {"strict":false} loads without error, changes nothing
- Negative example: rejecting strict as unknown, or wiring new behavior on it

### R-004: Request must contain exactly {user_id, payload}
- Source pattern/condition: sorted(req) != ["payload","user_id"]
- Required target action: raise ValueError("request must contain only user_id and payload")
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:26; S-004, B-005
- Positive example: {"user_id":"u","payload":1} ok
- Negative example: allowing an extra key or a missing key

### R-005: user_id str/int check reproduces bool acceptance
- Source pattern/condition: isinstance(req["user_id"], (str,int))
- Required target action: same check; do NOT special-case bool out (int subtype); str() it
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:27; S-004, B-006, G-003
- Positive example: user_id True -> subject.id "True"
- Negative example: rejecting bool, or excluding it via `type(x) is int`

### R-006: Status sequence parsing
- Source pattern/condition: [int(x) for x in sequence.split(",") if x]
- Required target action: reproduce; empty tokens skipped; empty seq -> default 200; non-numeric int() raises ValueError (caught at CLI -> exit 2)
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:32; S-002, B-008, G-004
- Positive example: "503,,200" -> [503,200]
- Negative example: defaulting junk to 0 or 200 instead of raising

### R-007: Only 503 is retryable, bounded by maxAttempts
- Source pattern/condition: retry loop breaks when status!=503 OR attempts>=maxAttempts
- Required target action: reproduce exactly (>=, not >); ok=200<=s<300; error=null if s<400 else temporary(503)/upstream
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:33-38; S-002, B-008, B-009
- Positive example: retries=2 -> maxAttempts=3 -> 503 seq gives attempts=3
- Negative example: retrying 500, or off-by-one on the attempt bound

### R-008: Error catch set and exit codes
- Source pattern/condition: except (ValueError, OSError, json.JSONDecodeError)
- Required target action: catch exactly those three; print "error: "+str(exc) to stderr; return 2. argparse failures keep their own SystemExit(2).
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:50-51; S-005, B-010, G-005
- Positive example: missing --request -> argparse usage on stderr, exit 2
- Negative example: catching KeyError/TypeError, or exiting 1

### R-009: Canonical JSON output
- Source pattern/condition: json.dumps(out, sort_keys=True, separators=(",",":"))
- Required target action: identical serialization; trailing newline from print()
- Named exceptions: none
- Evidence and contract rows: legacy_adapter.py:49; S-001, S-002, B-010
- Positive example: keys sorted, no spaces after separators
- Negative example: default json.dumps spacing or unsorted keys

## Pending amendments
(none)
