#!/usr/bin/env python3
"""byte_fidelity.py — guards the ensure_ascii=False fix (a byte-level property
the structural JSON judge cannot see).

Starts an ephemeral port instance, adds a task with non-ASCII text, and asserts
the raw HTTP response body carries raw UTF-8 bytes (e.g. b"caf\\xc3\\xa9"), not
ASCII-escaped "\\u00e9". This matches the observed source, which emits raw UTF-8.

Exit 0 iff the raw bytes are non-escaped UTF-8.
"""
import os
import sys
import threading
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import pocket_tasks  # noqa: E402


def main():
    httpd = pocket_tasks.make_server("127.0.0.1", 0)
    base = "http://127.0.0.1:%d" % httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        body = '{"session":"bf","action":{"type":"add","text":"café ✓"}}'
        req = urllib.request.Request(base + "/interact", data=body.encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        raw = urllib.request.urlopen(req, timeout=10).read()
    finally:
        httpd.shutdown()
    has_raw_utf8 = b"caf\xc3\xa9" in raw
    has_escaped = b"\\u00e9" in raw
    ok = has_raw_utf8 and not has_escaped
    print("raw_utf8_present=%s ascii_escaped=%s -> %s"
          % (has_raw_utf8, has_escaped, "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
