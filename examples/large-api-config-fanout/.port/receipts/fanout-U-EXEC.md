# Receipt — fanout U-EXEC

- Start (UTC): 2026-07-23T05:09:02Z
- End (UTC): 2026-07-23T05:09:27Z
- Model / role: Opus 4.8 — implementer (worker `Opus-worker-exec`); real concurrent parent fan-out
- Owned paths (exclusive): `src/execute.py`, `.port/receipts/fanout-U-EXEC.md`
- Packet: `.port/packets/U-EXEC.md`
  - Packet SHA-256 (digest of packet file at read time): `a2dd91f767b98eb7a72cc7bdd917c1cbfbc90fba8e104b87112c2441a5b2d2a5`
  - Authorization bundle SHA-256 (declared in packet): `7fa1c825ff13f6b8598e6f4d3122c6e599c516658cf6f55085f5f7b1543d443a`

## Applied rules / gaps / contract
- Contract: S-002 (CLI `run` — canonical JSON result envelope; retry only on 503 up to maxAttempts).
- R-006 — Status sequence parsing: `[int(x) for x in sequence.split(",") if x]`;
  empty tokens skipped; empty sequence -> default status 200; non-numeric token
  lets `int()` raise ValueError (caught at CLI -> exit 2). Reproduced verbatim.
- R-007 — Only 503 retryable, bounded by maxAttempts: break when
  `status != 503 or attempts >= plan["meta"]["maxAttempts"]` (`>=`, not `>`);
  `ok = 200 <= status < 300`; `error = None if status<400 else temporary(503)/upstream`.
  Reproduced verbatim.
- G-004 (closed) — empty/junk sequence handling: empty seq -> [] -> default 200;
  junk causes `int()` ValueError caught downstream. Honored per R-006.
- Source evidence: `source/legacy_adapter.py:30-38` (function `execute`).

## Guardrail (worker expensive-referee)
- Command: `./worker-expensive-referee`
- Result: stderr `DENIED: workers must route full_referee.sh through serialized referee_runner.py`; exit code 126 (expected). Guardrail fires; worker did NOT invoke `full_referee.sh` (parent owns the expensive referee).

## Unit check (declared narrow)
- Command: `python3 -m unittest discover -s tests -p test_execute.py`
- Result: OK (exit 0)
- Tests run: 9 (all passed), including negative probe `test_negative_probe` (200 not reported as error).
- Auxiliary: `python3 -m py_compile src/execute.py` -> clean (NF-001 zero-import; execute.py imports nothing).

## Files written
- `src/execute.py` (created; did not exist prior)
- `.port/receipts/fanout-U-EXEC.md` (this receipt)

## Scope adherence
- Edited only the two owned paths. No edits to manifest, judge, rules, status,
  other source/tests, or shared controls. Did not run `full_referee.sh`.

## Uncertainty / notes
- None blocking. `execute` consumes only `plan["meta"]["maxAttempts"]` from the
  v2 plan (leaf unit, no cross-unit dependency). Full byte-differential judge is
  parent-owned and out of worker scope; narrow unit check is green.
