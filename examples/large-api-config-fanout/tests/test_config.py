import json
import os
import tempfile
import unittest

import _bootstrap  # noqa: F401
import config


def write_cfg(data):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(data, fh)
    return path


class ConfigTest(unittest.TestCase):
    def test_defaults(self):
        self.assertEqual(
            config.load_config(None, env={}),
            {"timeout_ms": 1000, "retries": 2, "region": "us-east", "strict": True},
        )

    def test_file_overrides_defaults(self):
        p = write_cfg({"timeout_ms": 500, "retries": 4})
        cfg = config.load_config(p, env={})
        self.assertEqual(cfg["timeout_ms"], 500)
        self.assertEqual(cfg["retries"], 4)

    def test_env_overrides_file(self):
        p = write_cfg({"timeout_ms": 500})
        cfg = config.load_config(p, env={"PORTME_TIMEOUT_MS": "250"})
        self.assertEqual(cfg["timeout_ms"], 250)

    def test_cli_overrides_env_and_file(self):
        p = write_cfg({"timeout_ms": 100})
        cfg = config.load_config(p, cli_timeout_ms=999, env={"PORTME_TIMEOUT_MS": "250"})
        self.assertEqual(cfg["timeout_ms"], 999)

    def test_strict_inert_accepted(self):
        p = write_cfg({"strict": False})
        self.assertEqual(config.load_config(p, env={})["strict"], False)

    def test_unknown_keys_sorted(self):
        p = write_cfg({"foo": 1, "bar": 2})
        with self.assertRaises(ValueError) as e:
            config.load_config(p, env={})
        self.assertEqual(str(e.exception), "unknown config keys: bar, foo")

    def test_timeout_must_be_positive(self):
        with self.assertRaises(ValueError) as e:
            config.load_config(None, cli_timeout_ms=0, env={})
        self.assertEqual(str(e.exception), "timeout_ms must be positive")

    def test_retries_range(self):
        with self.assertRaises(ValueError) as e:
            config.load_config(None, cli_retries=6, env={})
        self.assertEqual(str(e.exception), "retries must be between 0 and 5")

    def test_region_validation(self):
        with self.assertRaises(ValueError) as e:
            config.load_config(None, cli_region="apac", env={})
        self.assertEqual(str(e.exception), "unsupported region")

    def test_eu_west_allowed(self):
        self.assertEqual(config.load_config(None, cli_region="eu-west", env={})["region"], "eu-west")

    def test_negative_probe(self):
        # Negative probe: defaults must NOT silently be wrong.
        self.assertNotEqual(config.load_config(None, env={})["timeout_ms"], 999)


if __name__ == "__main__":
    unittest.main()
