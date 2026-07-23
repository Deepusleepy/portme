#!/usr/bin/env python3
import json
import hashlib
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "referee_runner.py"


class RefereeRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.port = Path(self.tmp.name) / ".port"
        self.addCleanup(self.make_writable)

    def make_writable(self):
        if not self.port.exists():
            return
        for root, directories, files in os.walk(self.port, topdown=False,
                                                followlinks=False):
            for name in files:
                path = Path(root) / name
                if not path.is_symlink():
                    path.chmod(0o600)
            for name in directories:
                path = Path(root) / name
                if not path.is_symlink():
                    path.chmod(0o700)
        self.port.chmod(0o700)

    def reset_port(self):
        self.make_writable()
        shutil.rmtree(self.port)

    def command(self, code, *options):
        return [sys.executable, str(SCRIPT), "run", "--port", str(self.port),
                *options, "--", sys.executable, "-c", code]

    def run_command(self, code, *options):
        return subprocess.run(self.command(code, *options), text=True,
                              capture_output=True)

    def last(self):
        return subprocess.run([sys.executable, str(SCRIPT), "last", "--port",
                               str(self.port)], text=True, capture_output=True)

    def completed(self):
        result = self.run_command("print('done')")
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(result.stdout.strip())

    def rewrite_immutable(self, result, name, data):
        result.chmod(0o755)
        path = result / name
        path.chmod(0o644)
        path.write_bytes(data)
        path.chmod(0o444)
        result.chmod(0o555)

    def test_concurrent_second_run_fails_fast_on_lock(self):
        first = subprocess.Popen(self.command("import time; time.sleep(1)"),
                                 text=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        deadline = time.time() + 2
        while not (self.port / "referee.lock").exists() and time.time() < deadline:
            time.sleep(0.02)
        second = self.run_command("print('second')")
        self.assertEqual(second.returncode, 2)
        self.assertIn("referee lock is held", second.stderr)
        stdout, stderr = first.communicate(timeout=3)
        self.assertEqual(first.returncode, 0, stderr)
        self.assertIn("0001", stdout)

    def test_waiting_contenders_serialize_without_partial_lock_payloads(self):
        processes = [subprocess.Popen(
            self.command("import time; time.sleep(0.03)", "--wait", "5"),
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                     for _ in range(6)]
        observed = 0
        deadline = time.time() + 6
        while any(process.poll() is None for process in processes) and time.time() < deadline:
            lock = self.port / "referee.lock"
            try:
                payload = json.loads(lock.read_text())
            except FileNotFoundError:
                pass
            else:
                self.assertIsInstance(payload["pid"], int)
                self.assertEqual(payload["schema"], 1)
                self.assertIn("timestamp", payload)
                observed += 1
            time.sleep(0.005)
        outputs = [process.communicate(timeout=2) for process in processes]
        for process, (_stdout, stderr) in zip(processes, outputs):
            self.assertEqual(process.returncode, 0, stderr)
        self.assertGreater(observed, 0)
        results = sorted(path.name for path in (self.port / "referee").iterdir()
                         if path.name.isdigit())
        self.assertEqual(results, ["%04d" % index for index in range(1, 7)])

    def test_numbered_outputs_never_overwrite_and_last_reports_latest(self):
        first = self.run_command("print('first')")
        second = self.run_command("print('second')")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        one = self.port / "referee" / "0001"
        two = self.port / "referee" / "0002"
        self.assertEqual((one / "output.txt").read_text(), "first\n")
        self.assertEqual((two / "output.txt").read_text(), "second\n")
        last = self.last()
        self.assertEqual(last.returncode, 0, last.stderr)
        self.assertIn(str(two), last.stdout)
        self.assertIn("exit 0", last.stdout)
        for result in (one, two):
            self.assertTrue((result / "COMPLETE").is_file())
            metadata = json.loads((result / "metadata.json").read_text())
            for name in ("cmd.txt", "output.txt", "exit.txt"):
                digest = hashlib.sha256((result / name).read_bytes()).hexdigest()
                self.assertEqual(metadata["sha256"][name], digest)
            for path in result.iterdir():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o444)
            self.assertEqual(stat.S_IMODE(result.stat().st_mode), 0o555)
        self.assertTrue(stat.S_IMODE((self.port / "referee").stat().st_mode) &
                        stat.S_IWUSR)

    def test_timeout_kills_command_and_records_124(self):
        started = time.monotonic()
        result = self.run_command("import time; time.sleep(2)", "--timeout", "0.2")
        self.assertEqual(result.returncode, 124)
        self.assertLess(time.monotonic() - started, 1.5)
        saved = self.port / "referee" / "0001"
        self.assertEqual((saved / "exit.txt").read_text(), "124\n")
        self.assertIn("timeout", (saved / "output.txt").read_text())

    def test_stale_lock_is_taken_over(self):
        self.port.mkdir()
        (self.port / "referee.lock").write_text(json.dumps({
            "pid": 999999, "timestamp": 0,
        }) + "\n")
        result = self.run_command("print('ok')", "--stale-seconds", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("took over stale referee lock", result.stderr)
        self.assertFalse((self.port / "referee.lock").exists())

    def test_live_aged_lock_owner_is_never_stolen(self):
        self.port.mkdir()
        lock = self.port / "referee.lock"
        lock.write_text(json.dumps({"pid": os.getpid(), "timestamp": 0}) + "\n")
        result = self.run_command("print('no')", "--stale-seconds", "0.1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("live pid", result.stderr)
        self.assertTrue(lock.exists())
        self.assertEqual(json.loads(lock.read_text())["pid"], os.getpid())

    def test_empty_and_corrupt_locks_fail_closed_even_when_old(self):
        self.port.mkdir()
        for payload in (b"", b"not json\n", b'{"pid": 999999}\n'):
            with self.subTest(payload=payload):
                lock = self.port / "referee.lock"
                lock.write_bytes(payload)
                os.utime(lock, (0, 0))
                result = self.run_command("print('no')", "--stale-seconds", "0.1")
                self.assertEqual(result.returncode, 2)
                self.assertIn("remove it manually only after proving", result.stderr)
                self.assertEqual(lock.read_bytes(), payload)
                lock.unlink()

    def test_nonfinite_and_nonpositive_numeric_values_are_rejected(self):
        for option in ("--timeout", "--stale-seconds", "--wait"):
            for value in ("nan", "inf", "-inf", "0", "-1"):
                with self.subTest(option=option, value=value):
                    options = ((option + "=" + value,) if value.startswith("-")
                               else (option, value))
                    result = self.run_command("print('no')", *options)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("finite number greater than zero", result.stderr)

    def test_numbered_result_is_invisible_until_atomically_complete(self):
        process = subprocess.Popen(self.command("import time; time.sleep(0.5)"),
                                   text=True, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        deadline = time.time() + 2
        root = self.port / "referee"
        while not root.exists() and time.time() < deadline:
            time.sleep(0.01)
        self.assertTrue(root.exists())
        visible = [path for path in root.iterdir() if path.name.isdigit()]
        self.assertEqual(visible, [])
        self.assertTrue(any(path.name.startswith(".") for path in root.iterdir()))
        stdout, stderr = process.communicate(timeout=3)
        self.assertEqual(process.returncode, 0, stderr)
        result = Path(stdout.strip())
        self.assertTrue((result / "COMPLETE").is_file())
        self.assertTrue((result / "metadata.json").is_file())

    def test_last_rejects_incomplete_numbered_result(self):
        completed = self.run_command("print('done')")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        incomplete = self.port / "referee" / "9999"
        incomplete.mkdir()
        (incomplete / "exit.txt").write_text("0\n")
        (incomplete / "exit.txt").chmod(0o444)
        incomplete.chmod(0o555)
        last = self.last()
        self.assertEqual(last.returncode, 1)
        self.assertIn("invalid referee result", last.stderr)
        self.assertIn("missing COMPLETE", last.stderr)

    def test_last_rejects_tampered_evidence_metadata_and_complete_marker(self):
        cases = {
            "output.txt": b"tampered\n",
            "metadata.json": b"{}\n",
            "COMPLETE": b"{}\n",
        }
        for name, replacement in cases.items():
            with self.subTest(name=name):
                result = self.completed()
                self.rewrite_immutable(result, name, replacement)
                last = self.last()
                self.assertEqual(last.returncode, 1)
                self.assertIn("invalid referee result", last.stderr)
                self.reset_port()

    def test_last_rejects_cryptographically_consistent_but_conflicting_exit_codes(self):
        result = self.completed()
        result.chmod(0o755)
        exit_path = result / "exit.txt"
        exit_path.chmod(0o644)
        exit_path.write_text("7\n")
        exit_path.chmod(0o444)

        metadata_path = result / "metadata.json"
        metadata_path.chmod(0o644)
        metadata = json.loads(metadata_path.read_text())
        metadata["sha256"]["exit.txt"] = hashlib.sha256(b"7\n").hexdigest()
        metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
        metadata_path.chmod(0o444)

        complete_path = result / "COMPLETE"
        complete_path.chmod(0o644)
        marker = {
            "metadata_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
            "schema": 1,
        }
        complete_path.write_text(json.dumps(marker, sort_keys=True) + "\n")
        complete_path.chmod(0o444)
        result.chmod(0o555)

        last = self.last()
        self.assertEqual(last.returncode, 1)
        self.assertIn("exit codes are inconsistent", last.stderr)

    def test_last_rejects_mode_missing_extra_and_symlink_file_tampering(self):
        result = self.completed()
        (result / "output.txt").chmod(0o644)
        last = self.last()
        self.assertEqual(last.returncode, 1)
        self.assertIn("mode is not 0444", last.stderr)

        self.reset_port()
        result = self.completed()
        result.chmod(0o755)
        (result / "cmd.txt").unlink()
        result.chmod(0o555)
        self.assertIn("missing cmd.txt", self.last().stderr)

        self.reset_port()
        result = self.completed()
        result.chmod(0o755)
        extra = result / "extra.txt"
        extra.write_text("unexpected\n")
        result.chmod(0o555)
        self.assertIn("extra extra.txt", self.last().stderr)

        self.reset_port()
        result = self.completed()
        result.chmod(0o755)
        target = result / "output.txt"
        target.unlink()
        os.symlink("cmd.txt", target)
        result.chmod(0o555)
        self.assertIn("unsafe output.txt", self.last().stderr)

    def test_last_rejects_symlink_numeric_result_directory(self):
        completed = self.completed()
        root = self.port / "referee"
        os.symlink(completed.name, root / "9999", target_is_directory=True)
        last = self.last()
        self.assertEqual(last.returncode, 1)
        self.assertIn("numeric result is not a real directory", last.stderr)

    @unittest.skipUnless(hasattr(os, "killpg"), "requires POSIX process groups")
    def test_sigterm_kills_child_and_releases_lock_before_exit(self):
        pidfile = Path(self.tmp.name) / "child.pid"
        code = ("import os,time,pathlib; "
                "pathlib.Path(%r).write_text(str(os.getpid())); time.sleep(30)" %
                str(pidfile))
        process = subprocess.Popen(self.command(code), text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        deadline = time.time() + 3
        while not pidfile.exists() and time.time() < deadline:
            time.sleep(0.02)
        self.assertTrue(pidfile.exists())
        child_pid = int(pidfile.read_text())
        process.send_signal(signal.SIGTERM)
        process.communicate(timeout=3)
        self.assertEqual(process.returncode, 128 + signal.SIGTERM)
        self.assertFalse((self.port / "referee.lock").exists())
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
