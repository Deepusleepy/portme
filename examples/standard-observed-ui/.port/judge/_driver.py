"""Shared HTTP driver + normalizer for the Pocket Tasks judge (stdlib only).

Drives one scenario against a base URL through the two authorized public
surfaces only (GET /health, POST /interact) and returns a list of raw
observations. The normalizer masks exactly one declared source-identity field
(health.version); everything else is compared byte/structure-exact.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request


def _request(method, url, body_bytes=None):
    headers = {"Content-Type": "application/json"} if body_bytes is not None else {}
    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=10)
        return r.getcode(), r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")


def run_scenario(base_url, session_id, steps):
    """Return list of observations: {"kind","status","body"} per step.

    A fresh reset is issued for POST scenarios so state starts identical.
    """
    obs = []
    # Isolate: reset this session first (ignored for pure health scenarios).
    if any("post" in s or "post_raw" in s for s in steps):
        _request("POST", base_url + "/interact",
                 json.dumps({"session": session_id, "action": {"type": "reset"}}).encode())
    for step in steps:
        if step.get("health"):
            code, text = _request("GET", base_url + "/health")
            obs.append({"kind": "health", "status": code, "body": _loads(text)})
        elif "post_raw" in step:
            code, text = _request("POST", base_url + "/interact",
                                   step["post_raw"].encode("utf-8"))
            obs.append({"kind": "interact", "status": code, "body": _loads(text)})
        else:
            body = dict(step["post"])
            body["session"] = session_id
            code, text = _request("POST", base_url + "/interact",
                                   json.dumps(body).encode("utf-8"))
            obs.append({"kind": "interact", "status": code, "body": _loads(text)})
    return obs


def _loads(text):
    try:
        return json.loads(text)
    except ValueError:
        return {"__unparsable__": text}


import os
import re

_RULES_PATH = os.path.join(os.path.dirname(__file__), "..", "scanner",
                           "pocketscan-rules.json")


def _compiled_rules():
    with open(_RULES_PATH, "rb") as f:
        cfg = json.loads(f.read().decode("utf-8"))
    return [(re.compile(r["pattern"]), r.get("mask", "[REDACTED]")) for r in cfg["rules"]]


def _redact_str(s, rules):
    for rx, mask in rules:
        s = rx.sub(mask, s)
    return s


def _redact_tree(node, rules):
    if isinstance(node, str):
        return _redact_str(node, rules)
    if isinstance(node, list):
        return [_redact_tree(x, rules) for x in node]
    if isinstance(node, dict):
        return {k: _redact_tree(v, rules) for k, v in node.items()}
    return node


def normalize(obs):
    """Apply the two approved normalizations, in order:

      1. pocketscan redaction of every string leaf (privacy-preserving judge:
         secrets/PII never sit in .port results or fixtures, and the J-PII
         scenario compares equal on both sides after masking).
      2. mask health.version (contract S-000: version is a source-identity
         field; the port ships its own version string).

    No other field is normalized. Redaction is idempotent, so applying it to an
    already-admitted redacted golden fixture is a no-op.
    """
    rules = _compiled_rules()
    out = []
    for o in obs:
        o = json.loads(json.dumps(o))  # deep copy
        o = _redact_tree(o, rules)
        if o.get("kind") == "health" and isinstance(o.get("body"), dict):
            if "version" in o["body"]:
                o["body"]["version"] = "<version>"
        out.append(o)
    return out
