#!/usr/bin/env python3
"""Regression tests for scripts/port_queue.py."""
import csv
import importlib.util
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "port_queue.py"
SPEC = importlib.util.spec_from_file_location("port_queue", str(SCRIPT))
port_queue = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(port_queue)
HEADERS = list(port_queue.REQUIRED_COLUMNS)


def row(unit_id="U-1", targets="out/result.txt", depends="",
        check="test -s out/result.txt", risk="low", check_inputs=None):
    if check_inputs is None:
        check_inputs = "checks/%s.conf" % unit_id
    return {
        "unit_id": unit_id, "source_scope": "src/example",
        "target_paths": targets, "depends_on": depends,
        "contract_ids": "S-1", "rule_ids": "R-1", "gap_ids": "",
        "check_inputs": check_inputs, "unit_check": check, "risk": risk,
    }


class QueueFixture:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.manifest = self.root / "manifest.tsv"

    def close(self):
        self.temporary.cleanup()

    def write(self, rows, headers=None, comment=False, line_ending="\n"):
        with self.manifest.open("w", encoding="utf-8", newline="") as handle:
            if comment:
                handle.write("# trusted candidate" + line_ending)
            writer = csv.DictWriter(handle, fieldnames=headers or HEADERS,
                                    delimiter="\t", lineterminator=line_ending,
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return self.manifest

    def file(self, relative, content="content\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def digest(self):
        result = self.run("digest")
        if result.returncode:
            raise AssertionError(result.stderr)
        return result.stdout.strip()

    def run(self, command, *options):
        return subprocess.run(
            [sys.executable, str(SCRIPT), command, "--manifest", str(self.manifest),
             *options], cwd=str(self.root), text=True, capture_output=True)

    def checked(self, command, *options):
        return self.run(command, "--run-checks", "--authorize-manifest",
                        self.digest(), *options)


class PortQueueTests(unittest.TestCase):
    def setUp(self):
        self.fixture = QueueFixture()
        self.fixture.file("checks/U-1.conf", "stable=true\n")
        self.fixture.file("checks/U-2.conf", "stable=true\n")

    def tearDown(self):
        self.fixture.close()

    def assert_load_error(self, text):
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 2)
        self.assertIn(text, result.stderr)

    def test_ambiguous_default_refuses_without_executing_manifest(self):
        marker = self.fixture.root / "executed"
        self.fixture.write([row(check="touch %s" % shlex.quote(str(marker)))])
        self.fixture.file("out/result.txt")
        result = self.fixture.run("verify")
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing ambiguous", result.stderr)
        self.assertFalse(marker.exists())

    def test_missing_or_wrong_authorization_never_executes(self):
        marker = self.fixture.root / "executed"
        self.fixture.write([row(check="touch %s" % shlex.quote(str(marker)))])
        self.fixture.file("out/result.txt")
        missing = self.fixture.run("status", "--run-checks")
        wrong = self.fixture.run("status", "--run-checks",
                                 "--authorize-manifest", "0" * 64)
        self.assertEqual(missing.returncode, 2)
        self.assertEqual(wrong.returncode, 2)
        self.assertIn("does not match", wrong.stderr)
        self.assertFalse(marker.exists())

    def test_authorization_error_never_suggests_self_computing_digest(self):
        self.fixture.write([row()])
        result = self.fixture.run("status", "--run-checks")
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("$(", result.stderr)
        self.assertIn("explicitly approved", result.stderr)
        self.assertIn("manifest/check-input bundle", result.stderr)

    def test_digest_authorizes_only_exact_current_bytes(self):
        self.fixture.write([row()])
        first = self.fixture.digest()
        self.fixture.manifest.write_bytes(self.fixture.manifest.read_bytes() + b"\n")
        self.assertNotEqual(first, self.fixture.digest())
        result = self.fixture.run("status", "--run-checks",
                                  "--authorize-manifest", first)
        self.assertEqual(result.returncode, 2)

    def test_driver_edit_refuses_unchanged_manifest_before_execution(self):
        marker = self.fixture.root / "executed"
        driver = self.fixture.file(
            "checks/driver.py", "raise SystemExit('old driver')\n")
        command = "%s checks/driver.py" % shlex.quote(sys.executable)
        self.fixture.write([row(check=command, check_inputs="checks/driver.py")])
        self.fixture.file("out/result.txt")
        approved = self.fixture.digest()
        driver.write_text(
            "from pathlib import Path\nPath(%r).touch()\n" % str(marker),
            encoding="utf-8")
        result = self.fixture.run(
            "verify", "--run-checks", "--authorize-manifest", approved)
        self.assertEqual(result.returncode, 2)
        self.assertIn("authorization bundle digest does not match", result.stderr)
        self.assertFalse(marker.exists())

    def test_check_input_glob_membership_change_refuses(self):
        self.fixture.file("checks/control/one.conf")
        self.fixture.write([row(check="true", check_inputs="checks/control/*.conf")])
        self.fixture.file("out/result.txt")
        approved = self.fixture.digest()
        self.fixture.file("checks/control/two.conf")
        result = self.fixture.run(
            "status", "--run-checks", "--authorize-manifest", approved)
        self.assertEqual(result.returncode, 2)
        self.assertIn("authorization bundle digest does not match", result.stderr)

    def test_implementation_output_is_not_hashed_by_default(self):
        self.fixture.write([row(check="true")])
        output = self.fixture.file("out/result.txt", "first\n")
        first = self.fixture.digest()
        output.write_text("changed implementation\n", encoding="utf-8")
        self.assertEqual(first, self.fixture.digest())

    def test_check_inputs_reject_escape_empty_glob_symlink_and_nonregular(self):
        outside = self.fixture.file("outside.conf")
        os.symlink(outside, self.fixture.root / "checks" / "linked.conf")
        (self.fixture.root / "checks" / "directory").mkdir()
        cases = (
            ("../outside.conf", "traversal"),
            ("checks/missing-*.conf", "zero files"),
            ("checks/linked.conf", "symlink"),
            ("checks/directory", "not a regular file"),
        )
        for declaration, message in cases:
            with self.subTest(declaration=declaration):
                self.fixture.write([row(check_inputs=declaration)])
                result = self.fixture.run("digest")
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)

    def test_duplicate_and_ambiguous_check_input_declarations_fail(self):
        self.fixture.write([row(
            check_inputs="checks/U-1.conf, checks/./U-1.conf")])
        self.assert_load_error("duplicate check input declaration")

        self.fixture.write([row(
            check_inputs="checks/*.conf, checks/U-1.conf")])
        result = self.fixture.run("digest")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ambiguous check input", result.stderr)

        self.fixture.write([
            row("U-1", check_inputs="checks/U-1.conf"),
            row("U-2", targets="out/two.txt", check_inputs="checks/U-1.conf"),
        ])
        result = self.fixture.run("digest")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_direct_check_with_stable_declared_config_passes(self):
        self.fixture.write([row(check="test -s checks/U-1.conf")])
        self.fixture.file("out/result.txt")
        result = self.fixture.checked("verify")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verified 1/1", result.stdout)

    def test_existence_mode_is_honestly_worded_and_never_says_done(self):
        self.fixture.write([row(check="false")], comment=True)
        self.fixture.file("out/result.txt")
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 present", result.stdout)
        self.assertIn("no unit checks were run", result.stdout)
        self.assertNotIn("done", result.stdout)

    def test_check_failure_blocks_passing_dependent_at_same_level(self):
        self.fixture.write([
            row(check="false"),
            row("U-2", "out/second.txt", depends="U-1",
                check="test -s out/second.txt"),
        ])
        self.fixture.file("out/result.txt")
        self.fixture.file("out/second.txt")
        result = self.fixture.checked("status")
        self.assertIn("0 done / 0 pending / 1 blocked / 1 failed-check / 2 total",
                      result.stdout)
        self.assertIn("blocked U-2: waiting on U-1", result.stdout)

    def test_happy_checked_status_next_and_verify(self):
        self.fixture.write([
            row(), row("U-2", "out/second.txt", depends="U-1",
                       check="test -s out/second.txt")])
        self.fixture.file("out/result.txt")
        self.fixture.file("out/second.txt")
        self.assertIn("2 done", self.fixture.checked("status").stdout)
        self.assertEqual(json.loads(self.fixture.checked("next").stdout), [])
        verified = self.fixture.checked("verify")
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertIn("verified 2/2", verified.stdout)

    def test_failing_check_is_failed_and_next(self):
        self.fixture.write([row(check="false")])
        self.fixture.file("out/result.txt")
        status = self.fixture.checked("status")
        self.assertIn("1 failed-check", status.stdout)
        next_result = self.fixture.checked("next", "--batch", "1")
        self.assertEqual(json.loads(next_result.stdout)[0]["unit_id"], "U-1")
        verified = self.fixture.checked("verify")
        self.assertEqual(verified.returncode, 1)
        self.assertIn("unit_check failed: exit", verified.stderr)

    def test_timeout_and_output_cap_are_preserved(self):
        self.fixture.write([row(check="sleep 2")])
        self.fixture.file("out/result.txt")
        started = time.monotonic()
        result = self.fixture.checked("verify", "--check-timeout", "1")
        self.assertEqual(result.returncode, 1)
        self.assertLess(time.monotonic() - started, 1.8)
        self.assertIn("unit_check failed: timeout", result.stderr)
        command = "%s -c %s" % (
            shlex.quote(sys.executable), shlex.quote("print('x' * 70000)"))
        passed, reason, output = port_queue.run_check(
            row(check=command), timeout=5, repo_root=str(self.fixture.root))
        self.assertTrue(passed, reason)
        self.assertEqual(len(output), 64 * 1024)

    def test_globs_directories_and_spaces_remain_supported(self):
        self.fixture.write([row(targets="out dir/*.txt, generated")])
        self.fixture.file("out dir/first file.txt")
        self.fixture.file("generated/nested/result.txt")
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 present", result.stdout)

    def test_glob_requires_matches_and_every_file_nonempty(self):
        self.fixture.write([row(targets="generated/*.txt")])
        self.fixture.file("generated/one.txt")
        self.fixture.file("generated/two.txt", "")
        result = self.fixture.run("status", "--existence-only")
        self.assertIn("0 present / 1 pending", result.stdout)

    def test_absolute_traversal_and_windows_absolute_targets_are_rejected(self):
        for target in ("/etc/hosts", "../escape", "safe/../../escape", "C:\\etc\\hosts"):
            with self.subTest(target=target):
                self.fixture.write([row(targets=target)])
                result = self.fixture.run("status", "--existence-only")
                self.assertEqual(result.returncode, 2)
                self.assertRegex(result.stderr, "absolute|traversal")

    def test_symlink_target_or_component_is_rejected(self):
        outside = self.fixture.file("outside.txt")
        os.symlink(outside, self.fixture.root / "linked.txt")
        self.fixture.write([row(targets="linked.txt")])
        self.assert_load_error("symlink component")
        (self.fixture.root / "real").mkdir()
        os.symlink(self.fixture.root / "real", self.fixture.root / "alias")
        self.fixture.write([row(targets="alias/result.txt")])
        self.assert_load_error("symlink component")

    def test_duplicate_normalized_and_parent_child_ownership_rejected(self):
        cases = [
            [row("U-1", "out/a.txt"), row("U-2", "out/./a.txt")],
            [row("U-1", "out"), row("U-2", "out/a.txt")],
        ]
        for rows in cases:
            with self.subTest(rows=rows):
                self.fixture.write(rows)
                result = self.fixture.run("status", "--existence-only")
                self.assertEqual(result.returncode, 2)
                self.assertRegex(result.stderr, "duplicate|overlapping")

    def test_glob_and_matching_concrete_ownership_are_rejected(self):
        cases = [
            [row("U-1", "out/*.txt"), row("U-2", "out/result.txt")],
            [row("U-1", "out"), row("U-2", "out/**/*.txt")],
            [row("U-1", "out/**/*.txt"), row("U-2", "out/generated")],
        ]
        for rows in cases:
            with self.subTest(rows=rows):
                self.fixture.write(rows)
                self.assert_load_error("overlapping target ownership")

    def test_overlapping_globs_are_rejected_but_disjoint_globs_are_preserved(self):
        self.fixture.write([
            row("U-1", "out/**/*.txt"),
            row("U-2", "out/generated/*.txt"),
        ])
        self.assert_load_error("overlapping target ownership")

        self.fixture.write([
            row("U-1", "out/left/*.txt"),
            row("U-2", "out/right/*.txt"),
        ])
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 0, result.stderr)

        self.fixture.write([
            row("U-1", "out/*.txt"),
            row("U-2", "out/generated/result.txt"),
        ])
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_row_column_counts_are_manifest_errors(self):
        header = "\t".join(HEADERS)
        valid = "\t".join(row()[name] for name in HEADERS)
        for body, word in ((valid + "\textra", "surplus"),
                           ("\t".join(valid.split("\t")[:-1]), "missing")):
            with self.subTest(word=word):
                self.fixture.manifest.write_text(header + "\n" + body + "\n")
                result = self.fixture.run("status", "--existence-only")
                self.assertEqual(result.returncode, 2)
                self.assertIn(word, result.stderr)

    def test_required_values_and_risk_are_validated(self):
        for changed, text in (({"source_scope": ""}, "empty source_scope"),
                              ({"target_paths": ""}, "empty target_paths"),
                              ({"check_inputs": ""}, "empty check_inputs"),
                              ({"unit_check": ""}, "empty unit_check"),
                              ({"risk": "critical"}, "invalid risk")):
            candidate = row()
            candidate.update(changed)
            self.fixture.write([candidate])
            self.assert_load_error(text)

    def test_manifest_structure_errors(self):
        self.fixture.write([])
        self.assert_load_error("zero data rows")
        self.fixture.write([row(), row(targets="out/other.txt")])
        self.assert_load_error("duplicate unit_id")
        self.fixture.write([row(depends="U-404")])
        self.assert_load_error("U-1 -> U-404")
        self.fixture.write([row(depends="U-1")])
        self.assert_load_error("depends on itself")

    def test_dependency_cycle_is_rejected(self):
        self.fixture.write([row("A", depends="B"),
                            row("B", targets="out/b.txt", depends="A")])
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 2)
        self.assertIn("A -> B -> A", result.stderr)

    def test_deep_reverse_order_acyclic_manifest_is_stack_safe(self):
        count = 1600
        rows = [row("U-%d" % index, "out/%d.txt" % index,
                    depends="U-%d" % (index - 1) if index else "")
                for index in range(count)]
        self.fixture.write(list(reversed(rows)))
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_deep_dependency_cycle_is_reported_without_recursion(self):
        count = 1600
        rows = [row("U-%d" % index, "out/%d.txt" % index,
                    depends=("U-%d" % (index + 1) if index + 1 < count else "U-0"))
                for index in range(count)]
        self.fixture.write(rows)
        result = self.fixture.run("status", "--existence-only")
        self.assertEqual(result.returncode, 2)
        self.assertIn("dependency cycle detected", result.stderr)
        self.assertNotIn("RecursionError", result.stderr)

    def test_batch_must_be_positive(self):
        self.fixture.write([row()])
        result = self.fixture.run("next", "--existence-only", "--batch", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be at least 1", result.stderr)

    def test_help_documents_bundle_and_check_input_limits(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--help"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("check_inputs", result.stdout)
        self.assertIn("Literal commas cannot be escaped", result.stdout)
        self.assertIn("implementation outputs", result.stdout)
        self.assertIn("legacy flag", result.stdout)
        self.assertIn("name)", result.stdout)

    @unittest.skipUnless(hasattr(os, "killpg"), "requires POSIX process groups")
    def test_sigterm_kills_and_waits_for_running_check_group(self):
        pidfile = self.fixture.root / "child.pid"
        code = ("import os,time,pathlib; "
                "pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(30)" %
                str(pidfile))
        command = "%s -c %s" % (shlex.quote(sys.executable), shlex.quote(code))
        self.fixture.write([row(check=command)])
        self.fixture.file("out/result.txt")
        cmd = [sys.executable, str(SCRIPT), "verify", "--manifest",
               str(self.fixture.manifest), "--run-checks", "--authorize-manifest",
               self.fixture.digest()]
        parent = subprocess.Popen(cmd, cwd=self.fixture.root, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True)
        deadline = time.time() + 3
        while not pidfile.exists() and time.time() < deadline:
            time.sleep(0.02)
        self.assertTrue(pidfile.exists())
        child_pid = int(pidfile.read_text())
        parent.send_signal(signal.SIGTERM)
        parent.communicate(timeout=3)
        self.assertEqual(parent.returncode, 128 + signal.SIGTERM)
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
