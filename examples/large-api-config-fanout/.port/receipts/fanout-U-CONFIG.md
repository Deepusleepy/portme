# Receipt: fanout U-CONFIG

## Run metadata
- Start (UTC): 2026-07-23T05:09:04Z
- End (UTC): 2026-07-23T05:09:31Z
- Model / role: Opus 4.8, implementer (worker `Opus-worker-config`)
- Fan-out transport test: real concurrent Portme fan-out

## Owned paths (exclusive)
- src/config.py
- .port/receipts/fanout-U-CONFIG.md

## Packet
- Packet: .port/packets/U-CONFIG.md
- Packet digest (sha256 of packet file): c2b029c364671b89bddd07e1833419741dd37bc3c4f44637f8af1c7d51de87c3
- Authorization bundle SHA-256 (declared in packet): 7fa1c825ff13f6b8598e6f4d3122c6e599c516658cf6f55085f5f7b1543d443a

## Evidence consumed (read-only)
- Source: source/legacy_adapter.py:4-23 (DEFAULTS, load_config)
- Contract: .port/contract.md (S-003 config resolution, B-001/B-002/B-003/B-004/B-011)
- Rulebook: .port/rulebook.md (R-001, R-002, R-003)
- Gaps: .port/gaps.tsv (G-001, G-002, both closed)
- Check inputs: tests/test_config.py, tests/_bootstrap.py

## Applied rules / gaps
- R-001 (B-001): DEFAULTS reproduced exactly {timeout_ms:1000, retries:2, region:us-east, strict:True}; ALLOWED = set(DEFAULTS).
- R-002 / G-002 (B-002): precedence defaults < file < PORTME_TIMEOUT_MS < CLI. Env layer only for timeout_ms, applied whenever present; each CLI override applied only when arg is not None. Env does NOT override an explicit CLI value.
- R-003 / G-001 (B-011): `strict` accepted as a known key, validated (via ALLOWED), stored, never branched on, inert.
- Validation preserved: unknown keys -> "unknown config keys: <sorted>" (B-003); timeout_ms<=0 -> "timeout_ms must be positive"; retries not in [0,5] -> "retries must be between 0 and 5"; region not in {us-east,eu-west} -> "unsupported region" (B-004).

## Guardrail (worker guardrail must fire)
- Command: ./worker-expensive-referee
- Result: printed "DENIED: workers must route full_referee.sh through serialized referee_runner.py" to stderr; exit code 126 (expected). Guardrail confirmed firing.
- full_referee.sh NOT invoked (parent owns the expensive referee).

## Unit check (declared narrow check only)
- Command: python3 -m unittest discover -s tests -p test_config.py
- Result: OK, all passed; exit 0
- Test count: 11 tests (includes test_negative_probe, defaults not silently wrong)
- Additional: python3 -m py_compile src/config.py, clean (NF-001: only stdlib `json` imported, zero third-party).

## Files written
- src/config.py (created; DEFAULTS, ALLOWED, load_config with env/cli precedence)
- .port/receipts/fanout-U-CONFIG.md (this receipt)

## Uncertainty / notes
- Target signature adapted to the check's contract: load_config(path, env=None, cli_timeout_ms=None, cli_retries=None, cli_region=None). This differs from the source's argparse `args` object but preserves identical semantics/precedence per R-002; tests call it with these exact kwargs. No behavioral divergence introduced.
- No other paths touched (manifest, judge, rules, status, other source/tests, shared controls untouched). Leaf unit, no dependencies.

## FIX: coordinator-directed integration defect (U-CONFIG)
- Timestamp (UTC): 2026-07-23T05:13:04Z
- Requested by: coordinator/parent integration. Confirmed defect: serialized referee `.port/referee/0003` exited 1; authorized queue failed U-CLI.
- Root cause: `load_config` defaulted `env` to `{}` (ignoring the real process environment) AND placed `env` as the 2nd positional parameter. `src/cli.py` (owned by U-CLI, not editable here) calls `load_config(a.config, a.timeout_ms, a.retries, a.region)` positionally, so `a.timeout_ms` landed in `env` and `a.region` landed in `cli_retries`. Result: `--region apac` produced a `TypeError` (uncaught, not in the ValueError/OSError/JSONDecodeError catch set) → exit 1 instead of the expected `error: unsupported region` → exit 2.
- Fix applied (src/config.py ONLY):
  - Added `import os`.
  - Reordered signature to `load_config(path, cli_timeout_ms=None, cli_retries=None, cli_region=None, env=None)` so the CLI's positional call maps correctly (path, cli_timeout_ms, cli_retries, cli_region) and `env` is the trailing/injectable param.
  - `if env is None: env = os.environ`: defaults to the real process environment (PORTME_TIMEOUT_MS honored from os.environ when no mapping injected), while `env={}` injection still isolates for tests. Precedence defaults<file<PORTME_TIMEOUT_MS<CLI (R-002/G-002) unchanged.
- Scope honored: only src/config.py edited; no tests, cli.py, manifest, judge, rules, status, or shared controls touched. full_referee.sh NOT invoked.
- Verification (post-fix):
  - `python3 -m py_compile src/config.py`: clean.
  - Narrow check `python3 -m unittest discover -s tests -p test_config.py`. OK, 11 tests, exit 0.
  - Identified CLI/env check `python3 -m unittest discover -s tests -p test_cli.py` (read-only run). OK, 7 tests, exit 0 (previously FAILED: test_error_to_stderr_exit2 returned 1 != 2; now passes).
  - Direct env sanity: `PORTME_TIMEOUT_MS=250 load_config(None)['timeout_ms']` -> 250 (real env honored); `load_config(None, env={})['timeout_ms']` -> 1000 (injectable isolation preserved).
- Note: the underlying trigger surfaced through U-CLI's positional call; the confirmed fix lives entirely in the owned U-CONFIG file per coordinator direction.
