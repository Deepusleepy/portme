"""Unit U-EXEC: execution / retry engine.

Drives the v2 plan against a status sequence and applies retry semantics. Only
HTTP 503 is retryable; retries are bounded by plan meta.maxAttempts. Produces
the legacy result envelope. Zero runtime dependencies.
"""


def execute(plan, sequence):
    """Execute `plan` against a comma-separated status `sequence`.

    Each attempt consumes the next status (clamped to the last once exhausted;
    defaults to 200 when the sequence is empty). Retries occur only on 503 and
    stop once attempts reach meta.maxAttempts.
    """
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
