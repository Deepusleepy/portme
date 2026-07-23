"""Unit U-API: v1 -> v2 request translation (API versioning boundary).

Validates the inbound v1 request ({user_id, payload}) and re-shapes it into the
internal v2 envelope ({subject, data, meta}). Errors raise ValueError with the
exact legacy messages. Zero runtime dependencies.
"""


def translate(req, cfg):
    """Translate a validated v1 request dict into the v2 internal shape.

    The v1 request must contain exactly the keys `user_id` and `payload`.
    `user_id` must be a string or integer (bool is an int subtype and is
    accepted, matching legacy behavior; it stringifies to "True"/"False").
    """
    if sorted(req) != ["payload", "user_id"]:
        raise ValueError("request must contain only user_id and payload")
    if not isinstance(req["user_id"], (str, int)):
        raise ValueError("user_id must be string or integer")
    return {
        "subject": {"id": str(req["user_id"])},
        "data": req["payload"],
        "meta": {
            "region": cfg["region"],
            "timeoutMs": cfg["timeout_ms"],
            "maxAttempts": cfg["retries"] + 1,
        },
    }
