import unittest

import _bootstrap  # noqa: F401
import execute


def plan(max_attempts):
    return {"meta": {"maxAttempts": max_attempts}, "subject": {"id": "u"}, "data": 1}


class ExecuteTest(unittest.TestCase):
    def test_200_single_attempt(self):
        r = execute.execute(plan(3), "200")
        self.assertEqual((r["attempts"], r["status"], r["ok"], r["error"]), (1, 200, True, None))

    def test_503_exhausts_attempts(self):
        r = execute.execute(plan(3), "503")
        self.assertEqual((r["attempts"], r["status"], r["error"]), (3, 503, "temporary"))
        self.assertFalse(r["ok"])

    def test_503_then_recover(self):
        r = execute.execute(plan(3), "503,503,200")
        self.assertEqual((r["attempts"], r["status"]), (3, 200))

    def test_503_recover_early(self):
        r = execute.execute(plan(3), "503,200")
        self.assertEqual((r["attempts"], r["status"]), (2, 200))

    def test_500_upstream_no_retry(self):
        r = execute.execute(plan(3), "500")
        self.assertEqual((r["attempts"], r["status"], r["error"]), (1, 500, "upstream"))

    def test_503_no_retry_when_max1(self):
        r = execute.execute(plan(1), "503")
        self.assertEqual(r["attempts"], 1)

    def test_302_boundary_no_error(self):
        r = execute.execute(plan(3), "302")
        self.assertEqual((r["ok"], r["error"]), (False, None))

    def test_empty_sequence_defaults_200(self):
        r = execute.execute(plan(3), "")
        self.assertEqual((r["attempts"], r["status"]), (1, 200))

    def test_negative_probe(self):
        # Negative probe: a plain 200 must not be reported as an error.
        self.assertIsNone(execute.execute(plan(3), "200")["error"])


if __name__ == "__main__":
    unittest.main()
