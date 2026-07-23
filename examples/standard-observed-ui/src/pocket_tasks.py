"""Pocket Tasks — behavior-preserving port of an observed-only task UI.

This module is the port's own public engine. It reproduces the observed
request/response contract of the source fixture (a "Pocket Tasks" to-do UI)
that was probed only through GET /health and POST /interact.

The behavior encoded here is derived exclusively from recorded observations
(see .port/behavior-map.tsv and .port/contract.md). It is not a copy of the
source's implementation, which was never read.

Stdlib only.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TITLE = "Pocket Tasks"
VERSION = "pocket-tasks-port-1"
VALID_FILTERS = ("all", "active", "done")


def fresh_state():
    """A reset session: empty task list, all filter, light theme, input focus."""
    return {
        "tasks": [],        # list of {"text": str, "done": bool}
        "filter": "all",
        "theme": "light",
        "focus": "new-item",
        "live": "",
    }


def _rows_for_view(state):
    """Rows in the current filter view, preserving insertion order."""
    f = state["filter"]
    out = []
    for t in state["tasks"]:
        if f == "active" and t["done"]:
            continue
        if f == "done" and not t["done"]:
            continue
        aria = "Mark %s active" % t["text"] if t["done"] else "Mark %s done" % t["text"]
        out.append({"ariaLabel": aria, "checked": t["done"], "text": t["text"]})
    return out


def render(state):
    """Build the full observable response envelope from session state."""
    rows = _rows_for_view(state)
    active_count = sum(1 for t in state["tasks"] if not t["done"])
    export = "".join(
        ("[x] %s\n" if t["done"] else "[ ] %s\n") % t["text"] for t in state["tasks"]
    )
    return {
        "dom": {
            "count": active_count,
            "empty": None if rows else "No tasks here",
            "filter": state["filter"],
            "rows": rows,
            "theme": state["theme"],
            "title": TITLE,
        },
        "export": export,
        "focus": state["focus"],
        "liveRegion": state["live"],
    }


def apply_action(state, action):
    """Mutate session state per one action dict, then set the live-region text.

    `action` must be a mapping. A non-mapping raises AttributeError (observed
    contract: 400 {"error": "AttributeError"}). A non-numeric index raises
    ValueError (observed contract: 400 {"error": "ValueError"}). Both are left
    to propagate to the transport layer, matching the source's error surface.
    """
    atype = action.get("type")

    if atype == "reset":
        state.clear()
        state.update(fresh_state())
        return

    if atype == "add":
        # Observed source normalization: coerce any value with str(), then
        # collapse every run of whitespace to a single space and trim ends
        # (equivalent to " ".join(str(text).split())). Whitespace-only or
        # empty -> rejected. Non-string values are stringified, never errored.
        text = " ".join(str(action.get("text", "")).split())
        state["focus"] = "new-item"
        if not text:
            state["live"] = "Task cannot be empty"
            return
        state["tasks"].append({"text": text, "done": False})
        state["live"] = "Added %s" % text
        return

    if atype == "toggle":
        index = int(action.get("index", -1))
        if 0 <= index < len(state["tasks"]):
            t = state["tasks"][index]
            t["done"] = not t["done"]
            state["focus"] = "task-%d" % index
            state["live"] = ("%s completed" if t["done"] else "%s active") % t["text"]
        else:
            state["live"] = "Task not found"
        return

    if atype == "delete":
        index = int(action.get("index", -1))
        if 0 <= index < len(state["tasks"]):
            t = state["tasks"].pop(index)
            state["focus"] = "task-%d" % index
            state["live"] = "Deleted %s" % t["text"]
        else:
            state["live"] = "Task not found"
        return

    if atype == "filter":
        value = action.get("value")
        if value in VALID_FILTERS:
            state["filter"] = value
            state["focus"] = "filter-%s" % value
            state["live"] = "Showing %s tasks" % value
        else:
            state["live"] = ""
        return

    if atype == "shortcut":
        key = action.get("key")
        if key == "Alt+D":
            state["theme"] = "dark" if state["theme"] == "light" else "light"
            state["live"] = "Dark theme" if state["theme"] == "dark" else "Light theme"
        elif key == "Escape":
            state["filter"] = "all"
            state["focus"] = "new-item"
            state["live"] = "Reset view"
        else:
            state["live"] = ""
        return

    # Missing or unrecognized action type.
    state["live"] = "Unknown action"


def interact(sessions, body):
    """Process one POST /interact body against the session store, return envelope.

    `body` must be a mapping (a non-mapping raises AttributeError). The session
    key is `body.get("session")` (may be None -> a shared default bucket),
    matching the observed source, which accepts a missing session field.
    """
    session_key = body.get("session")
    action = body.get("action") or {}
    state = sessions.setdefault(session_key, fresh_state())
    apply_action(state, action)
    return render(state)


# ---------------------------------------------------------------------------
# Public HTTP entry point (the port's own surface).
# ---------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    server_version = "PocketTasksPort/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # silence default logging
        pass

    def _send_json(self, code, payload):
        # ensure_ascii=False to match the source's raw-UTF-8 JSON output byte-for-byte.
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"ok": True, "version": VERSION})
            return
        self._send_json(404, {"error": "NotFound"})

    def do_POST(self):
        if self.path != "/interact":
            self._send_json(404, {"error": "NotFound"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw.decode("utf-8"))
            payload = interact(self.server.sessions, body)
        except (ValueError, AttributeError, TypeError) as exc:
            # ValueError covers json.JSONDecodeError and int() failures; the
            # source exposes the concrete exception class name with HTTP 400.
            self._send_json(400, {"error": type(exc).__name__})
            return
        self._send_json(200, payload)


def make_server(host="127.0.0.1", port=0):
    httpd = ThreadingHTTPServer((host, port), _Handler)
    httpd.sessions = {}
    return httpd


def main():
    import os

    host = os.environ.get("PT_HOST", "127.0.0.1")
    port = int(os.environ.get("PT_PORT", "18770"))
    httpd = make_server(host, port)
    print("Pocket Tasks port listening on http://%s:%d" % (host, httpd.server_address[1]))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
