"""Unit U-CONFIG: configuration system.

Resolves the effective adapter configuration from three layered sources with
strict precedence: built-in defaults < config file < PORTME_TIMEOUT_MS env <
CLI overrides. Validates the resolved values and raises ValueError with the
exact legacy messages on any violation. Zero runtime dependencies.
"""
import json
import os

# Built-in defaults. `strict` is an accepted-but-inert key preserved from the
# legacy contract: it is validated as a known key and stored, never read.
DEFAULTS = {"timeout_ms": 1000, "retries": 2, "region": "us-east", "strict": True}
ALLOWED = frozenset(DEFAULTS)
REGIONS = ("us-east", "eu-west")


def load_config(path, cli_timeout_ms=None, cli_retries=None, cli_region=None, env=None):
    """Return the resolved config dict.

    Precedence (lowest to highest): DEFAULTS, config file, PORTME_TIMEOUT_MS,
    CLI overrides. `env` defaults to os.environ; injectable for testing.
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
    if cfg["region"] not in REGIONS:
        raise ValueError("unsupported region")
    return cfg
