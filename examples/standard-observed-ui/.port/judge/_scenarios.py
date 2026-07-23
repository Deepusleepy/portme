"""Single source of truth for judge scenarios (Pocket Tasks observed-only port).

Each scenario is an ordered list of steps. A step is either:
  {"post": <body dict-or-raw>}   -> POST /interact with this JSON body
  {"post_raw": <str>}            -> POST /interact with this raw (maybe non-JSON) body
  {"health": True}               -> GET /health

Every scenario begins with an implicit reset of its own isolated session so the
source and port are compared from identical initial state. Session IDs are
injected by the adapters; bodies here omit "session" unless a scenario
deliberately exercises the missing-session default (J-016b).

Only the approved interaction vocabulary is used: reset; add text; toggle index;
delete index; filter all/active/done; shortcut Alt+D/Escape; and malformed or
unknown actions. No endpoint other than GET /health and POST /interact.
"""

# scenario_id -> list of steps
SCENARIOS = {
    "J-001": [  # reset yields the empty initial view
        {"post": {"action": {"type": "reset"}}},
    ],
    "J-002": [  # add appends; surrounding whitespace trimmed; export + count update
        {"post": {"action": {"type": "add", "text": "Buy milk"}}},
        {"post": {"action": {"type": "add", "text": "  Walk dog  "}}},
    ],
    "J-003": [  # whitespace-only and missing text rejected, focus returns to input
        {"post": {"action": {"type": "add", "text": "   "}}},
        {"post": {"action": {"type": "add"}}},
    ],
    "J-004": [  # toggle completes then reactivates; aria label + live text + count
        {"post": {"action": {"type": "add", "text": "Alpha"}}},
        {"post": {"action": {"type": "add", "text": "Beta"}}},
        {"post": {"action": {"type": "toggle", "index": 0}}},
        {"post": {"action": {"type": "toggle", "index": 0}}},
    ],
    "J-005": [  # delete removes row, sets focus task-<index>, live "Deleted X"
        {"post": {"action": {"type": "add", "text": "One"}}},
        {"post": {"action": {"type": "add", "text": "Two"}}},
        {"post": {"action": {"type": "delete", "index": 0}}},
    ],
    "J-006": [  # filter all/active/done: view rows, focus filter-<v>, live text
        {"post": {"action": {"type": "add", "text": "Keep"}}},
        {"post": {"action": {"type": "add", "text": "Done"}}},
        {"post": {"action": {"type": "toggle", "index": 1}}},
        {"post": {"action": {"type": "filter", "value": "active"}}},
        {"post": {"action": {"type": "filter", "value": "done"}}},
        {"post": {"action": {"type": "filter", "value": "all"}}},
    ],
    "J-007": [  # filtered view empty -> "No tasks here", count reflects active total
        {"post": {"action": {"type": "add", "text": "X"}}},
        {"post": {"action": {"type": "toggle", "index": 0}}},
        {"post": {"action": {"type": "filter", "value": "active"}}},
    ],
    "J-008": [  # not-found: out-of-range, negative, and missing index leave state, focus
        {"post": {"action": {"type": "add", "text": "Solo"}}},
        {"post": {"action": {"type": "toggle", "index": 9}}},
        {"post": {"action": {"type": "delete", "index": 5}}},
        {"post": {"action": {"type": "toggle", "index": -1}}},
        {"post": {"action": {"type": "toggle"}}},
    ],
    "J-009": [  # Alt+D toggles theme both directions, focus unchanged
        {"post": {"action": {"type": "add", "text": "Themed"}}},
        {"post": {"action": {"type": "shortcut", "key": "Alt+D"}}},
        {"post": {"action": {"type": "shortcut", "key": "Alt+D"}}},
    ],
    "J-010": [  # Escape resets filter to all + focus new-item, keeps theme
        {"post": {"action": {"type": "add", "text": "E"}}},
        {"post": {"action": {"type": "shortcut", "key": "Alt+D"}}},
        {"post": {"action": {"type": "filter", "value": "active"}}},
        {"post": {"action": {"type": "shortcut", "key": "Escape"}}},
    ],
    "J-011": [  # unknown shortcut key -> empty live region, no change, focus kept
        {"post": {"action": {"type": "toggle", "index": 0}}},  # sets focus (no task -> not found)
        {"post": {"action": {"type": "add", "text": "K"}}},
        {"post": {"action": {"type": "toggle", "index": 0}}},  # focus task-0
        {"post": {"action": {"type": "shortcut", "key": "Ctrl+Z"}}},
    ],
    "J-012": [  # unknown and missing action type -> "Unknown action", focus kept
        {"post": {"action": {"type": "add", "text": "K"}}},
        {"post": {"action": {"type": "toggle", "index": 0}}},
        {"post": {"action": {"type": "frobnicate"}}},
        {"post": {"action": {}}},
        {"post": {}},
    ],
    "J-013": [  # export contains all tasks regardless of filter
        {"post": {"action": {"type": "add", "text": "a1"}}},
        {"post": {"action": {"type": "add", "text": "a2"}}},
        {"post": {"action": {"type": "toggle", "index": 0}}},
        {"post": {"action": {"type": "filter", "value": "active"}}},
    ],
    "J-014": [  # malformed: non-numeric index -> 400 ValueError
        {"post": {"action": {"type": "toggle", "index": "x"}}},
    ],
    "J-015": [  # malformed: action as list -> 400 AttributeError; bad JSON -> 400 JSONDecodeError
        {"post": {"action": [1, 2]}},
        {"post_raw": "not json"},
    ],
    "J-016": [  # health endpoint (version normalized)
        {"health": True},
    ],
    "J-017": [  # regression: whitespace-collapse + str() coercion of add text
        {"post": {"action": {"type": "add", "text": "a\t b   c"}}},   # -> "a b c"
        {"post": {"action": {"type": "add", "text": None}}},          # -> "None"
        {"post": {"action": {"type": "add", "text": 12345}}},         # -> "12345"
        {"post": {"action": {"type": "add", "text": "   \t  "}}},     # -> rejected
        {"post": {"action": {"type": "add", "text": "café ✓ 你好"}}},  # unicode preserved
    ],
    # PII-injection scenario: exercises the capture scanner/redaction pipeline.
    # The added text carries synthetic secrets so the local scanner has real
    # findings to catch and redact before admission. No real secret exists.
    "J-PII": [
        {"post": {"action": {"type": "add",
                             "text": "ping me at agent@example.com key=AKIAIOSFODNN7EXAMPLE"}}},
    ],
}

# Scenarios whose golden bodies are captured raw from the source and must pass
# through the scan/redact/admit pipeline. All of them do; listed for clarity.
ALL_IDS = list(SCENARIOS.keys())
