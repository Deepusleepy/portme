import json
import os
import subprocess
import sys
import unittest

CLI = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "cli.py"))


def run(args, env=None):
    e = dict(os.environ)
    e.pop("PORTME_TIMEOUT_MS", None)
    if env:
        e.update(env)
    return subprocess.run([sys.executable, CLI] + args, capture_output=True, text=True, env=e)


class CliTest(unittest.TestCase):
    def test_plan_defaults(self):
        r = run(["plan", "--request", '{"user_id":"u1","payload":{"a":1}}'])
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), {
            "subject": {"id": "u1"}, "data": {"a": 1},
            "meta": {"region": "us-east", "timeoutMs": 1000, "maxAttempts": 3},
        })

    def test_canonical_json_bytes(self):
        r = run(["plan", "--request", '{"user_id":"u","payload":1}'])
        self.assertEqual(
            r.stdout,
            '{"data":1,"meta":{"maxAttempts":3,"region":"us-east","timeoutMs":1000},"subject":{"id":"u"}}\n',
        )

    def test_run_retry_503(self):
        r = run(["run", "--request", '{"user_id":"u","payload":1}', "--sequence", "503"])
        self.assertEqual(json.loads(r.stdout)["attempts"], 3)
        self.assertEqual(json.loads(r.stdout)["error"], "temporary")

    def test_error_to_stderr_exit2(self):
        r = run(["plan", "--region", "apac", "--request", '{"user_id":"u","payload":1}'])
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stderr, "error: unsupported region\n")
        self.assertEqual(r.stdout, "")

    def test_bad_json_request_exit2(self):
        r = run(["plan", "--request", "{bad}"])
        self.assertEqual(r.returncode, 2)
        self.assertTrue(r.stderr.startswith("error: "))

    def test_argparse_missing_request_exit2(self):
        r = run(["run"])
        self.assertEqual(r.returncode, 2)

    def test_negative_probe(self):
        # Negative probe: a valid plan must not exit non-zero.
        r = run(["plan", "--request", '{"user_id":"u","payload":1}'])
        self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
