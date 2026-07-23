"""Config resolution (S-003).

Reproduces legacy_adapter.py:4-23 (DEFAULTS, load_config) exactly.

Rules applied:
- R-001: config defaults are frozen (timeout_ms=1000, retries=2, region=us-east,
  strict=True); ALLOWED = set(DEFAULTS). (G-001, B-001)
- R-002/G-002: precedence is defaults < file < PORTME_TIMEOUT_MS < CLI. The env
  layer exists only for timeout_ms and applies whenever present; each CLI value
  is applied only when its arg is not None. (B-002)
- R-003/G-001: `strict` is a known key that is accepted, validated, and stored,
  but never read/branched on after load (inert). (B-011)
"""

import json
import os

DEFAULTS = {"timeout_ms": 1000, "retries": 2, "region": "us-east", "strict": True}
ALLOWED = set(DEFAULTS)


def load_config(path, cli_timeout_ms=None, cli_retries=None, cli_region=None, env=None):
    """Resolve effective config with precedence defaults < file < env < CLI.

    Positional order (path, cli_timeout_ms, cli_retries, cli_region) matches the
    CLI's positional call `load_config(a.config, a.timeout_ms, a.retries,
    a.region)`. `cli_*` are CLI overrides applied only when not None.

    `env` is the environment mapping to consult (only PORTME_TIMEOUT_MS matters).
    When no mapping is injected it defaults to the real process environment
    (`os.environ`), matching the source/baseline; tests inject `env={}` to
    isolate.
    """
    if env is None:
        env = os.environ
    cfg = dict(DEFAULTS)
    if path:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        unknown = sorted(set(data) - ALLOWED)
        if unknown:
            raise ValueError("unknown config keys: " + ", ".join(unknown))
        cfg.update(data)
    if "PORTME_TIMEOUT_MS" in env:
        cfg["timeout_ms"] = int(env["PORTME_TIMEOUT_MS"])
    if cli_timeout_ms is not None:
        cfg["timeout_ms"] = cli_timeout_ms
    if cli_retries is not None:
        cfg["retries"] = cli_retries
    if cli_region is not None:
        cfg["region"] = cli_region
    if cfg["timeout_ms"] <= 0:
        raise ValueError("timeout_ms must be positive")
    if not 0 <= cfg["retries"] <= 5:
        raise ValueError("retries must be between 0 and 5")
    if cfg["region"] not in ("us-east", "eu-west"):
        raise ValueError("unsupported region")
    return cfg
