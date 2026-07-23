"""Execution / retry engine (packet U-EXEC; contract S-002).

Ports ``execute`` from legacy_adapter.py:30-38 exactly.

Rules applied:
- R-006 status sequence parsing: ``[int(x) for x in sequence.split(",") if x]``;
  empty tokens skipped; empty sequence -> default status 200; non-numeric
  tokens let ``int()`` raise ValueError (caught at the CLI -> exit 2). (G-004)
- R-007 only 503 is retryable, bounded by maxAttempts: loop breaks when
  status != 503 OR attempts >= maxAttempts (``>=``, not ``>``);
  ok = 200 <= s < 300; error = None if s < 400 else temporary(503)/upstream.
"""


def execute(plan, sequence):
    attempts = 0
    statuses = [int(x) for x in sequence.split(",") if x]
    while True:
        status = statuses[min(attempts, len(statuses) - 1)] if statuses else 200
        attempts += 1
        if status != 503 or attempts >= plan["meta"]["maxAttempts"]:
            break
    return {
        "attempts": attempts,
        "status": status,
        "ok": 200 <= status < 300,
        "request": plan,
        "error": None if status < 400 else ("temporary" if status == 503 else "upstream"),
    }
