import unittest

import _bootstrap  # noqa: F401
import translate

CFG = {"region": "us-east", "timeout_ms": 1000, "retries": 2}


class TranslateTest(unittest.TestCase):
    def test_shape(self):
        out = translate.translate({"user_id": "u1", "payload": {"a": 1}}, CFG)
        self.assertEqual(out, {
            "subject": {"id": "u1"},
            "data": {"a": 1},
            "meta": {"region": "us-east", "timeoutMs": 1000, "maxAttempts": 3},
        })

    def test_int_user_id_stringified(self):
        out = translate.translate({"user_id": 42, "payload": 1}, CFG)
        self.assertEqual(out["subject"]["id"], "42")

    def test_bool_user_id_accepted(self):
        # bool is an int subtype in Python; legacy accepts it -> "True".
        out = translate.translate({"user_id": True, "payload": 1}, CFG)
        self.assertEqual(out["subject"]["id"], "True")

    def test_max_attempts_is_retries_plus_one(self):
        out = translate.translate({"user_id": "u", "payload": 1}, {"region": "us-east", "timeout_ms": 1000, "retries": 4})
        self.assertEqual(out["meta"]["maxAttempts"], 5)

    def test_extra_key_rejected(self):
        with self.assertRaises(ValueError) as e:
            translate.translate({"user_id": "u", "payload": 1, "extra": 2}, CFG)
        self.assertEqual(str(e.exception), "request must contain only user_id and payload")

    def test_missing_key_rejected(self):
        with self.assertRaises(ValueError) as e:
            translate.translate({"user_id": "u"}, CFG)
        self.assertEqual(str(e.exception), "request must contain only user_id and payload")

    def test_bad_user_id_type(self):
        with self.assertRaises(ValueError) as e:
            translate.translate({"user_id": [1], "payload": 1}, CFG)
        self.assertEqual(str(e.exception), "user_id must be string or integer")

    def test_negative_probe(self):
        # Negative probe: region must not be dropped from meta.
        out = translate.translate({"user_id": "u", "payload": 1}, CFG)
        self.assertIn("region", out["meta"])


if __name__ == "__main__":
    unittest.main()
