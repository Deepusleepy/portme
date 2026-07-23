#!/usr/bin/env python3
import os
import json
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
DEPMAP = REPO / "scripts" / "depmap.py"
SPEC = importlib.util.spec_from_file_location("depmap", str(DEPMAP))
depmap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(depmap)
FIXTURES = HERE / "fixtures" / "depmap"
OUTPUTS = ("edges.tsv", "nodes.txt", "order.txt", "package-cycles.tsv")


class DepmapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)

    def fixture(self, name):
        target = self.work / name
        shutil.copytree(FIXTURES / name, target)
        return target

    def run_depmap(self, root, lang, out_name="map", *extra):
        out = self.work / out_name
        proc = subprocess.run(
            [sys.executable, str(DEPMAP), "--root", str(root), "--lang", lang,
             "--out", str(out), *extra],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc, out

    def raw_depmap(self, root, lang, out_name="map", *extra):
        out = self.work / out_name
        proc = subprocess.run(
            [sys.executable, str(DEPMAP), "--root", str(root), "--lang", lang,
             "--out", str(out), *extra], text=True, capture_output=True)
        return proc, out

    def test_python_file_and_package_cycle_with_isolated_file(self):
        _, out = self.run_depmap(self.fixture("python_graph"), "python")
        edges = (out / "edges.tsv").read_text()
        self.assertIn("alpha/a.py\tbeta/b.py\n", edges)
        self.assertIn("beta/b.py\talpha/a.py\n", edges)
        self.assertIn(" CYCLE\nalpha/a.py\nbeta/b.py\n",
                      (out / "order.txt").read_text())
        self.assertIn("P-1\talpha,beta\n",
                      (out / "package-cycles.tsv").read_text())
        self.assertIn("isolated.py\tISOLATED\n", (out / "nodes.txt").read_text())

    def test_python_stdlib_only_is_valid_zero_edge_tree(self):
        proc, out = self.run_depmap(self.fixture("python_stdlib"), "python")
        self.assertIn("0 local imports — isolated files only", proc.stdout)
        self.assertEqual((out / "edges.tsv").read_text(), "from\tto\n")
        self.assertIn("one.py\tISOLATED", (out / "nodes.txt").read_text())
        self.assertIn("two.py\tISOLATED", (out / "nodes.txt").read_text())

    def test_python_root_qualified_import_flags_parent_root_misselection(self):
        for statement in ("import pkg.b\n", "from pkg import b\n"):
            with self.subTest(statement=statement):
                parent = self.work / ("wrong_root_%d" % len(list(self.work.iterdir())))
                root = parent / "pkg"
                root.mkdir(parents=True)
                (root / "a.py").write_text(statement)
                (root / "b.py").write_text("VALUE = 1\n")
                failed, out = self.raw_depmap(root, "python", parent.name + "_map")
                self.assertEqual(failed.returncode, 1)
                self.assertIn("--root is probably one level too deep", failed.stderr)
                self.assertIn("run from parent/root", failed.stderr)
                self.assertFalse((out / "edges.tsv").exists())

    def test_external_imports_do_not_trigger_wrong_root_detection(self):
        root = self.work / "pkg"
        root.mkdir()
        (root / "a.py").write_text("import os\nfrom collections import deque\n")
        (root / "b.py").write_text("VALUE = 1\n")
        proc, out = self.run_depmap(root, "python", "external_map")
        self.assertIn("0 local imports", proc.stdout)
        self.assertEqual((out / "edges.tsv").read_text(), "from\tto\n")

    def test_ts_nodenext_export_from_and_dynamic_imports(self):
        _, out = self.run_depmap(self.fixture("ts_nodenext"), "ts")
        edges = set((out / "edges.tsv").read_text().splitlines()[1:])
        self.assertEqual(edges, {
            "cli.ts\targparse.ts",
            "cli.ts\tcommands.mts",
            "cli.ts\tcomponent.tsx",
            "cli.ts\tdifflib.ts",
            "cli.ts\tlegacy.cts",
        })

    def test_ts_multiline_import(self):
        root = self.work / "multiline"
        root.mkdir()
        (root / "main.ts").write_text(
            "import {\n  a,\n  b\n} from './values.js';\n")
        (root / "values.ts").write_text("export const a = 1; export const b = 2;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertIn("main.ts\tvalues.ts\n", (out / "edges.tsv").read_text())

    def test_ts_commented_out_import_produces_no_edge(self):
        root = self.work / "comments"
        root.mkdir()
        (root / "main.ts").write_text(
            "// import './one.js';\n/* import { two } from './two.js'; */\n")
        (root / "one.ts").write_text("export const one = 1;\n")
        (root / "two.ts").write_text("export const two = 2;\n")
        proc, out = self.run_depmap(root, "ts")
        self.assertEqual((out / "edges.tsv").read_text(), "from\tto\n")
        self.assertIn("isolated files only", proc.stdout)

    def test_ts_string_literal_fake_import_produces_no_edge(self):
        root = self.work / "strings"
        root.mkdir()
        (root / "main.ts").write_text(
            "const fake = \"import { value } from './value.js'\";\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertEqual((out / "edges.tsv").read_text(), "from\tto\n")

    def test_regex_quotes_do_not_corrupt_lexer_across_newline(self):
        root = self.work / "regex_quotes"
        root.mkdir()
        (root / "main.ts").write_text(
            "/[\\\"']/;\nimport { value } from './value.js';\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertIn("main.ts\tvalue.ts\n", (out / "edges.tsv").read_text())

    def test_same_line_regex_quote_does_not_hide_real_import(self):
        root = self.work / "same_line_regex"
        root.mkdir()
        (root / "main.ts").write_text(
            "/it's/; import { value } from './value.js';\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertIn("main.ts\tvalue.ts\n", (out / "edges.tsv").read_text())

    def test_import_text_inside_regex_literal_does_not_create_edge(self):
        root = self.work / "regex_fake_import"
        root.mkdir()
        (root / "main.ts").write_text(
            "const matcher = /import(\".\\/value.js\")/;\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertEqual((out / "edges.tsv").read_text(), "from\tto\n")

    def test_ambiguous_slash_dependency_syntax_fails_closed(self):
        root = self.work / "ambiguous_regex"
        root.mkdir()
        (root / "main.ts").write_text(
            "if (enabled) /import(\".\\/value.js\")/.test(text);\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        failed, out = self.raw_depmap(root, "ts")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("ambiguous slash expression", failed.stderr)
        self.assertFalse((out / "edges.tsv").exists())

    def test_dynamic_import_inside_template_expression_is_detected(self):
        root = self.work / "template_expression"
        root.mkdir()
        (root / "main.ts").write_text(
            "const loaded = `prefix ${import('./value.js')}`;\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertIn("main.ts\tvalue.ts\n", (out / "edges.tsv").read_text())

    def test_fake_import_in_template_raw_text_is_ignored(self):
        root = self.work / "template_raw"
        root.mkdir()
        (root / "main.ts").write_text(
            "const text = `import('./value.js')`;\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertEqual((out / "edges.tsv").read_text(), "from\tto\n")

    def test_tsconfig_paths_alias_resolves_to_edge(self):
        project = self.work / "alias"
        root = project / "src"
        root.mkdir(parents=True)
        (project / "tsconfig.json").write_text(json.dumps({
            "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
        }))
        (root / "main.ts").write_text("import { value } from '@/value.js';\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertIn("main.ts\tvalue.ts\n", (out / "edges.tsv").read_text())

    def test_local_tsconfig_extends_inherits_baseurl_and_paths(self):
        project = self.work / "extends_alias"
        root = project / "src"
        root.mkdir(parents=True)
        (project / "base.json").write_text(json.dumps({
            "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
        }))
        (project / "tsconfig.json").write_text(json.dumps({
            "extends": "./base.json", "compilerOptions": {"strict": True}
        }))
        (root / "main.ts").write_text("import { value } from '@/value.js';\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertIn("main.ts\tvalue.ts\n", (out / "edges.tsv").read_text())

    def test_baseurl_and_paths_can_be_inherited_from_separate_local_levels(self):
        project = self.work / "layered_extends"
        root = project / "src"
        root.mkdir(parents=True)
        (project / "base.json").write_text(json.dumps({
            "compilerOptions": {"baseUrl": "."}
        }))
        (project / "aliases.json").write_text(json.dumps({
            "extends": "./base.json",
            "compilerOptions": {"paths": {"@/*": ["src/*"]}},
        }))
        (project / "tsconfig.json").write_text(json.dumps({
            "extends": "./aliases.json"
        }))
        (root / "main.ts").write_text("import { value } from '@/value.js';\n")
        (root / "value.ts").write_text("export const value = 1;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertIn("main.ts\tvalue.ts\n", (out / "edges.tsv").read_text())

    def test_tsconfig_extends_cycle_fails_closed(self):
        project = self.work / "extends_cycle"
        root = project / "src"
        root.mkdir(parents=True)
        (project / "tsconfig.json").write_text(json.dumps({"extends": "./base.json"}))
        (project / "base.json").write_text(json.dumps({"extends": "./tsconfig.json"}))
        (root / "main.ts").write_text("export const value = 1;\n")
        failed, out = self.raw_depmap(root, "ts")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("extends cycle", failed.stderr)
        self.assertFalse((out / "nodes.txt").exists())

    def test_deep_tsconfig_extends_chain_is_stack_safe(self):
        project = self.work / "deep_extends"
        root = project / "src"
        root.mkdir(parents=True)
        count = 1600
        (project / "tsconfig.json").write_text(json.dumps({"extends": "./c0000.json"}))
        for index in range(count):
            value = ({"extends": "./c%04d.json" % (index + 1)}
                     if index + 1 < count else {"compilerOptions": {"strict": True}})
            (project / ("c%04d.json" % index)).write_text(json.dumps(value))
        (root / "one.ts").write_text("export const one = 1;\n")
        (root / "two.ts").write_text("export const two = 2;\n")
        _, out = self.run_depmap(root, "ts")
        self.assertTrue((out / "order.txt").exists())

    def test_deep_tsconfig_cycle_fails_cleanly_and_clears_stale_outputs(self):
        project = self.work / "deep_extends_cycle"
        root = project / "src"
        root.mkdir(parents=True)
        count = 1200
        (project / "tsconfig.json").write_text(json.dumps({"extends": "./c0000.json"}))
        for index in range(count):
            target = index + 1 if index + 1 < count else 600
            (project / ("c%04d.json" % index)).write_text(json.dumps({
                "extends": "./c%04d.json" % target,
            }))
        (root / "main.ts").write_text("export const value = 1;\n")
        out = self.work / "stale_map"
        out.mkdir()
        for name in OUTPUTS:
            (out / name).write_text("stale\n")
        failed, _ = self.raw_depmap(root, "ts", "stale_map")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("extends cycle", failed.stderr)
        self.assertNotIn("RecursionError", failed.stderr)
        for name in OUTPUTS:
            self.assertFalse((out / name).exists())

    def test_unresolved_alias_fails_instead_of_claiming_isolation(self):
        project = self.work / "unresolved_alias"
        root = project / "src"
        root.mkdir(parents=True)
        (project / "tsconfig.json").write_text(json.dumps({
            "compilerOptions": {"baseUrl": ".", "paths": {"@/*": ["src/*"]}}
        }))
        (root / "main.ts").write_text("import { missing } from '@/missing.js';\n")
        (root / "other.ts").write_text("export const other = 1;\n")
        failed, out = self.raw_depmap(root, "ts")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("unresolved local imports", failed.stderr)
        self.assertFalse((out / "nodes.txt").exists())

    def test_unrecognized_import_syntax_fails_closed(self):
        root = self.work / "bad_import"
        root.mkdir()
        (root / "main.ts").write_text("const value = import(unknown);\n")
        (root / "other.ts").write_text("export const other = 1;\n")
        failed, out = self.raw_depmap(root, "ts")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("unrecognized import syntax", failed.stderr)
        self.assertFalse((out / "nodes.txt").exists())

    def test_relative_non_code_asset_import_fails_closed_honestly(self):
        root = self.work / "asset_import"
        root.mkdir()
        (root / "main.ts").write_text("import './style.css';\n")
        (root / "other.ts").write_text("export const other = 1;\n")
        (root / "style.css").write_text("body {}\n")
        failed, out = self.raw_depmap(root, "ts")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("non-code asset import unsupported", failed.stderr)
        self.assertFalse((out / "edges.tsv").exists())

    def test_literal_python_dynamic_imports_resolve_local_edges(self):
        root = self.work / "python_dynamic_literal"
        package = root / "local"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        (package / "mod.py").write_text("VALUE = 1\n")
        (root / "main.py").write_text(
            "import importlib\n"
            "one = importlib.import_module('local.mod')\n"
            "two = __import__('local.mod')\n")
        _, out = self.run_depmap(root, "python")
        self.assertIn("main.py\tlocal/mod.py\n", (out / "edges.tsv").read_text())

    def test_nonliteral_python_dynamic_import_fails_with_ledger_and_override(self):
        root = self.work / "python_dynamic_nonliteral"
        root.mkdir()
        (root / "main.py").write_text(
            "import importlib\nname = 'anything'\nimportlib.import_module(name)\n")
        (root / "other.py").write_text("VALUE = 1\n")
        failed, out = self.raw_depmap(root, "python", "dynamic_failed")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("nonliteral Python dynamic import", failed.stderr)
        ledger = out / "dynamic-imports.txt"
        self.assertIn("main.py\t3\timportlib.import_module", ledger.read_text())
        self.assertFalse((out / "edges.tsv").exists())

        allowed, allowed_out = self.run_depmap(
            root, "python", "dynamic_allowed", "--allow-dynamic-imports")
        self.assertIn("warn: allowing", allowed.stderr)
        self.assertTrue((allowed_out / "dynamic-imports.txt").exists())

    def test_importlib_alias_literal_forms_resolve_local_edges(self):
        root = self.work / "python_dynamic_alias_literal"
        package = root / "local"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        (package / "mod.py").write_text("VALUE = 1\n")
        (root / "main.py").write_text(
            "import importlib as il\n"
            "from importlib import import_module as im\n"
            "one = il.import_module('local.mod')\n"
            "two = im('local.mod')\n")
        _, out = self.run_depmap(root, "python")
        self.assertIn("main.py\tlocal/mod.py\n", (out / "edges.tsv").read_text())

    def test_importlib_alias_nonliteral_forms_fail_with_ledger(self):
        root = self.work / "python_dynamic_alias_nonliteral"
        root.mkdir()
        (root / "main.py").write_text(
            "import importlib as il\n"
            "from importlib import import_module as im\n"
            "name = 'anything'\n"
            "il.import_module(name)\n"
            "im(name)\n")
        (root / "other.py").write_text("VALUE = 1\n")
        failed, out = self.raw_depmap(root, "python", "alias_nonliteral")
        self.assertEqual(failed.returncode, 1)
        ledger = (out / "dynamic-imports.txt").read_text()
        self.assertIn("main.py\t4\timportlib.import_module", ledger)
        self.assertIn("main.py\t5\timportlib.import_module", ledger)
        self.assertFalse((out / "edges.tsv").exists())

    def test_rebound_importlib_alias_fails_closed(self):
        root = self.work / "python_dynamic_alias_rebound"
        root.mkdir()
        (root / "main.py").write_text(
            "import importlib as il\n"
            "from importlib import import_module as im\n"
            "il = object()\n"
            "im = lambda value: value\n"
            "il.import_module('other')\n"
            "im('other')\n")
        (root / "other.py").write_text("VALUE = 1\n")
        failed, out = self.raw_depmap(root, "python", "alias_rebound")
        self.assertEqual(failed.returncode, 1)
        ledger = (out / "dynamic-imports.txt").read_text()
        self.assertIn("rebound importlib alias il.import_module", ledger)
        self.assertIn("rebound importlib.import_module alias im", ledger)
        self.assertFalse((out / "edges.tsv").exists())

    def test_iterative_scc_handles_deep_graph(self):
        count = 25000
        nodes = ["n%05d" % index for index in range(count)]
        adjacency = {nodes[index]: {nodes[index + 1]}
                     for index in range(count - 1)}
        components = depmap.tarjan(nodes, adjacency)
        self.assertEqual(len(components), count)
        self.assertEqual(components[0], [nodes[-1]])
        self.assertEqual(components[-1], [nodes[0]])

    def test_help_discloses_heuristic_and_large_scale_validation(self):
        result = subprocess.run([sys.executable, str(DEPMAP), "--help"],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("heuristic", result.stdout)
        self.assertIn("Large-scale", result.stdout)
        self.assertIn("compiler-API", result.stdout)

    def test_unparseable_python_fails_closed_and_can_be_allowed(self):
        root = self.work / "broken_python"
        root.mkdir()
        (root / "good.py").write_text("VALUE = 1\n")
        (root / "bad.py").write_text("def broken(:\n")
        failed, failed_out = self.raw_depmap(root, "python", "failed")
        self.assertEqual(failed.returncode, 1)
        self.assertIn("unparseable Python file", failed.stderr)
        self.assertIn("bad.py", (failed_out / "parse-failures.txt").read_text())
        self.assertFalse((failed_out / "edges.tsv").exists())

        allowed, allowed_out = self.run_depmap(
            root, "python", "allowed", "--allow-unparseable")
        self.assertIn("warn: allowing", allowed.stderr)
        self.assertIn("bad.py\tPARSE-FAILED\n",
                      (allowed_out / "nodes.txt").read_text())

    def test_outputs_are_byte_identical(self):
        root = self.fixture("python_graph")
        _, first = self.run_depmap(root, "python", "first")
        _, second = self.run_depmap(root, "python", "second")
        for name in OUTPUTS:
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)

    def test_file_symlinks_are_not_parsed_and_directory_symlinks_not_followed(self):
        root = self.fixture("symlinks")
        os.symlink(root / "helper.py", root / "linked.py")
        os.symlink(root / "nested", root / "linked_dir", target_is_directory=True)
        _, out = self.run_depmap(root, "python")
        nodes = (out / "nodes.txt").read_text()
        self.assertIn("linked.py\tSYMLINK-SKIPPED\n", nodes)
        self.assertNotIn("linked_dir", nodes)
        self.assertNotIn("linked.py\tISOLATED", nodes)

    def test_default_hidden_and_user_exclusions(self):
        root = self.fixture("exclusions")
        cache_fixture = root / "__pycache__"
        cache_fixture.mkdir()
        (cache_fixture / "bad.py").write_text("raise RuntimeError('excluded')\n")
        _, out = self.run_depmap(root, "python", "map", "--exclude", "ignored")
        nodes = (out / "nodes.txt").read_text()
        self.assertIn("main.py", nodes)
        self.assertIn("helper.py", nodes)
        for excluded in (".hidden", "node_modules", "dist", "build", "out",
                         "coverage", "vendor", "venv", ".venv", "env",
                         "__pycache__", "site-packages", "target", "ignored"):
            self.assertNotIn(excluded + os.sep, nodes)


if __name__ == "__main__":
    unittest.main()
