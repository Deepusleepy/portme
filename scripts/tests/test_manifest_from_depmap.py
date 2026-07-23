#!/usr/bin/env python3
import csv
import hashlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "manifest_from_depmap.py"


class ManifestFromDepmapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.map = self.root / "map"
        self.map.mkdir()
        self.out = self.root / "manifest.tsv"

    def write_map(self, order, edges="from\tto\n"):
        (self.map / "order.txt").write_text(order)
        (self.map / "edges.tsv").write_text(edges)

    def run_script(self, *extra):
        return subprocess.run([
            sys.executable, str(SCRIPT), "--map", str(self.map),
            "--target-root", "target", "--out", str(self.out), *extra,
        ], text=True, capture_output=True)

    def rows(self):
        with self.out.open(newline="") as handle:
            return list(csv.DictReader(handle, delimiter="\t"))

    def test_basic_generation_uses_depmap_edges(self):
        self.write_map("# batch 1\nbase.py\n# batch 2\nmain.py\n",
                       "from\tto\nmain.py\tbase.py\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = self.rows()
        self.assertEqual([row["unit_id"] for row in rows], ["U-1", "U-2"])
        self.assertEqual(rows[1]["depends_on"], "U-1")
        self.assertEqual(rows[0]["risk"], "low")
        self.assertIn("CANDIDATE", result.stdout)
        self.assertIn("Phase 1 gate", result.stdout)
        expected = hashlib.sha256(self.out.read_bytes()).hexdigest()
        self.assertIn("candidate manifest-only sha256 %s" % expected,
                      result.stderr)
        self.assertIn("not an authorization bundle", result.stderr)
        self.assertIn("check-control assets before freeze",
                      rows[0]["check_inputs"])
        self.assertFalse(any(path.name.startswith(".manifest.")
                             for path in self.root.iterdir()))

    def test_cycle_batch_collapses_into_one_high_risk_unit(self):
        self.write_map("# batch 1 CYCLE\na.py\nb.py\n",
                       "from\tto\na.py\tb.py\nb.py\ta.py\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["source_scope"], "a.py, b.py")
        self.assertEqual(rows[0]["risk"], "high")

    def test_identity_substitution_is_refused(self):
        self.write_map("# batch 1\na.py\n")
        result = subprocess.run([
            sys.executable, str(SCRIPT), "--map", str(self.map),
            "--target-root", ".", "--out", str(self.out),
        ], text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("identity substitution is not a port", result.stderr)
        self.assertFalse(self.out.exists())

    def test_map_ext_changes_derived_extension(self):
        self.write_map("# batch 1\npkg/a.py\n")
        result = self.run_script("--map-ext", ".py=.ts")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.rows()[0]["target_paths"], "target/pkg/a.ts")

    def test_stdout_mode_is_clean_tsv_and_digest_is_on_stderr(self):
        self.write_map("# batch 1\na.py\n")
        result = subprocess.run([
            sys.executable, str(SCRIPT), "--map", str(self.map),
            "--target-root", "target",
        ], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = list(csv.DictReader(io.StringIO(result.stdout), delimiter="\t"))
        self.assertEqual(rows[0]["unit_id"], "U-1")
        self.assertNotIn("sha256", result.stdout)
        self.assertIn("candidate manifest-only sha256", result.stderr)

    def test_absolute_and_traversal_sources_are_rejected(self):
        for source in ("/etc/passwd", "../escape.py", "safe/../../escape.py",
                       "C:\\escape.py"):
            with self.subTest(source=source):
                self.write_map("# batch 1\n%s\n" % source)
                result = self.run_script()
                self.assertEqual(result.returncode, 1)
                self.assertRegex(result.stderr, "absolute|traversal")
                self.assertFalse(self.out.exists())

    def test_duplicate_source_entry_is_rejected(self):
        self.write_map("# batch 1\na.py\n# batch 2\na.py\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate source entry", result.stderr)

    def test_unknown_edge_endpoint_is_rejected(self):
        self.write_map("# batch 1\na.py\n", "from\tto\na.py\tmissing.py\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown source entries: missing.py", result.stderr)

    def test_missing_edges_file_is_a_hard_error(self):
        (self.map / "order.txt").write_text("# batch 1\na.py\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("edges.tsv is required", result.stderr)
        self.assertFalse(self.out.exists())

    def test_dependency_order_violation_is_rejected(self):
        self.write_map("# batch 1\nmain.py\n# batch 2\nbase.py\n",
                       "from\tto\nmain.py\tbase.py\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("edge violates dependency-first order", result.stderr)

    def test_scc_must_be_exactly_one_cycle_batch(self):
        edges = "from\tto\na.py\tb.py\nb.py\ta.py\n"
        cases = (
            "# batch 1\na.py\n# batch 2\nb.py\n",
            "# batch 1\na.py\nb.py\n",
        )
        for order in cases:
            with self.subTest(order=order):
                self.write_map(order, edges)
                result = self.run_script()
                self.assertEqual(result.returncode, 1)
                self.assertRegex(result.stderr, "multi-file SCC|cycle marker")

    def test_unrelated_files_cannot_be_grouped_as_a_cycle(self):
        self.write_map("# batch 1 CYCLE\na.py\nb.py\n")
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertIn("not one SCC", result.stderr)

    def test_commas_and_glob_magic_in_paths_are_actionably_rejected(self):
        for source in ("has,comma.py", "star*.py", "question?.py", "group[1].py"):
            with self.subTest(source=source):
                self.write_map("# batch 1\n%s\n" % source)
                result = self.run_script()
                self.assertEqual(result.returncode, 1)
                self.assertIn("unsupported filename", result.stderr)
                self.assertIn("current manifest schema", result.stderr)

        self.write_map("# batch 1\na.py\n")
        result = self.run_script("--map-ext", ".py=*.ts")
        self.assertEqual(result.returncode, 1)
        self.assertIn("unsupported filename", result.stderr)

    def test_duplicate_derived_target_collision_is_rejected(self):
        self.write_map("# batch 1\na.py\n# batch 2\na.ts\n")
        result = self.run_script("--map-ext", ".py=.ts")
        self.assertEqual(result.returncode, 1)
        self.assertIn("derived target collision", result.stderr)

    def test_malformed_and_duplicate_edge_rows_are_rejected(self):
        cases = (
            "from\tto\na.py\n",
            "from\tto\na.py\ta.py\textra\n",
            "from\tto\na.py\ta.py\na.py\ta.py\n",
        )
        for edges in cases:
            with self.subTest(edges=edges):
                self.write_map("# batch 1\na.py\n", edges)
                result = self.run_script()
                self.assertEqual(result.returncode, 1)
                self.assertRegex(result.stderr, "malformed|duplicate edge")


if __name__ == "__main__":
    unittest.main(verbosity=2)
