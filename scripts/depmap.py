#!/usr/bin/env python3
"""Deterministic heuristic dependency mapper for Python and TS/JS (stdlib only).

Feeds Phase 1 of a structure-preserving migration (references/mapping.md):
emits file-level edges, isolated files, strongly connected components, and a
package-level condensation — package cycles are the ones that hurt at compile
time even when the file graph looks clean.

TS resolution follows NodeNext/ESM: a `./foo.js` (or `.mjs`/`.cjs`) specifier
in a `.ts` file resolves to the matching `.ts`/`.tsx`/`.mts`/`.cts` source.
`import type`, `export ... from`, dynamic `import()`, and `require()` count.
Symlinks are never followed (files noted SYMLINK-SKIPPED); hidden and
build/vendor directories are excluded by default (`--exclude` adds more).

TS/JS scanning is lexical and necessarily heuristic; it is not a compiler
API.  Large-scale migrations require validation against the compiler API or
the build system's authoritative graph before the map may be frozen.

Guards the mis-rooted trap: a tree whose local imports resolve to zero edges
is almost always a wrong --root, so it exits 1 instead of writing a silently
empty map; a tree with genuinely no local imports succeeds with a note.

Usage, from the source repo:
  depmap.py --root src --lang python --out .port/depmap
  depmap.py --root src --lang ts     --out .port/depmap [--exclude generated]

Writes: edges.tsv (from<TAB>to), nodes.txt (ISOLATED / SYMLINK-SKIPPED
marked), order.txt (dependency-first SCC batches, CYCLE marked),
package-cycles.tsv.

Self-test: python3 scripts/tests/test_depmap.py
"""
import argparse
import ast
import json
import os
import re
import sys

TS_IMPORT = re.compile(r"""
    \b(?:import|export)\s+(?:type\s+)?
      (?:
        \{[^}]*\}
        | \*(?:\s+as\s+[A-Za-z_$][\w$]*)?
        | [A-Za-z_$][\w$]*(?:\s*,\s*(?:\{[^}]*\}|\*\s+as\s+[A-Za-z_$][\w$]*))?
      )\s+from\s*(?P<static_quote>['"])(?P<static>[^'"]+)(?P=static_quote)
  | \bimport\s*(?P<side_quote>['"])(?P<side>[^'"]+)(?P=side_quote)
  | \b(?:import|require)\s*\(\s*(?P<dynamic_quote>['"])
      (?P<dynamic>[^'"]+)(?P=dynamic_quote)\s*\)
""", re.X | re.S)
TS_EXTS = (".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs")
DEFAULT_EXCLUDES = {
    "node_modules", "dist", "build", "out", "coverage", "vendor", "venv",
    ".venv", "env", "__pycache__", "site-packages", "target",
}


def walk(root, exts, excludes=(), skipped=None):
    """Yield source paths while recording source-file symlinks in *skipped*."""
    excluded = DEFAULT_EXCLUDES | set(excludes)
    for dirpath, dirs, files in os.walk(root, followlinks=False):
        kept = []
        for name in sorted(dirs):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            if (name.startswith(".") or name in excluded or rel in excluded
                    or os.path.islink(path)):
                continue
            kept.append(name)
        dirs[:] = kept
        for name in sorted(files):
            if not name.endswith(exts):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, root)
            if os.path.islink(path):
                if skipped is not None:
                    skipped.append(rel)
                continue
            yield rel


def _python_index(files):
    index = {}
    for path in files:
        mod = path[:-3].replace(os.sep, ".")
        index[mod] = path
        if path.endswith("__init__.py"):
            index[mod.rsplit(".__init__", 1)[0]] = path
    return index


def _python_names(path, node):
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    pkg = os.path.dirname(path).replace(os.sep, ".")
    if node.level:
        parts = pkg.split(".") if pkg else []
        parts = parts[:max(0, len(parts) - node.level + 1)]
        base = ".".join(parts + ([node.module] if node.module else []))
    else:
        base = node.module or ""
    names = [f"{base}.{alias.name}".strip(".") for alias in node.names]
    return names + ([base] if base else [])


def _resolve_python_name(path, name, index, edges):
    probe = name
    while probe:
        if probe in index:
            if index[probe] != path:
                edges.add((path, index[probe]))
            return True
        probe = probe.rpartition(".")[0]
    return False


def _python_name_is_local(name, index):
    probe = name
    while probe:
        if probe in index:
            return True
        probe = probe.rpartition(".")[0]
    return False


def _wrong_root_imports(node, root_name, index):
    """Return root-qualified imports whose suffix exists inside selected root."""
    candidates = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            parts = alias.name.split(".")
            if len(parts) > 1 and parts[0] == root_name:
                candidates.append((alias.name, ".".join(parts[1:])))
    elif (isinstance(node, ast.ImportFrom) and not node.level and node.module):
        parts = node.module.split(".")
        if parts[0] == root_name:
            base = ".".join(parts[1:])
            for alias in node.names:
                suffix = ".".join(part for part in (base, alias.name) if part)
                candidates.append(("%s.%s" % (node.module, alias.name), suffix))
            if base:
                candidates.append((node.module, base))
    return [original for original, suffix in candidates
            if suffix and _python_name_is_local(suffix, index)]


class _PythonImportVisitor(ast.NodeVisitor):
    """Resolve imports while tracking simple importlib aliases and rebinding."""

    def __init__(self, path, index, root_name):
        self.path = path
        self.index = index
        self.root_name = root_name
        self.edges = set()
        self.local_refs = False
        self.dynamic_calls = []
        self.wrong_root_refs = []
        self.module_aliases = set()
        self.function_aliases = set()
        self.tainted_module_aliases = set()
        self.tainted_function_aliases = set()

    def _resolve_static(self, node):
        for name in _python_names(self.path, node):
            self.local_refs = (_resolve_python_name(
                self.path, name, self.index, self.edges) or self.local_refs)
        for name in _wrong_root_imports(node, self.root_name, self.index):
            self.wrong_root_refs.append(
                (self.path, getattr(node, "lineno", 0), name))

    def _rebind(self, name):
        if name in self.module_aliases:
            self.module_aliases.remove(name)
            self.tainted_module_aliases.add(name)
        if name in self.function_aliases:
            self.function_aliases.remove(name)
            self.tainted_function_aliases.add(name)

    def _bind_importlib_module(self, name):
        self._rebind(name)
        self.tainted_module_aliases.discard(name)
        self.module_aliases.add(name)

    def _bind_import_module_function(self, name):
        self._rebind(name)
        self.tainted_function_aliases.discard(name)
        self.function_aliases.add(name)

    def visit_Import(self, node):
        self._resolve_static(node)
        for alias in node.names:
            bound = alias.asname or alias.name.split(".")[0]
            if alias.name == "importlib":
                self._bind_importlib_module(bound)
            else:
                self._rebind(bound)

    def visit_ImportFrom(self, node):
        self._resolve_static(node)
        for alias in node.names:
            bound = alias.asname or alias.name
            if node.module == "importlib" and alias.name == "import_module":
                self._bind_import_module_function(bound)
            else:
                self._rebind(bound)

    def _dynamic_kind(self, node):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name == "__import__":
                return "__import__", False
            if name in self.function_aliases:
                return "importlib.import_module", False
            if name in self.tainted_function_aliases:
                return "rebound importlib.import_module alias %s" % name, True
        if (isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
                and isinstance(node.func.value, ast.Name)):
            name = node.func.value.id
            if name in self.module_aliases:
                return "importlib.import_module", False
            if name in self.tainted_module_aliases:
                return "rebound importlib alias %s.import_module" % name, True
        return None, False

    def visit_Call(self, node):
        call_kind, rebound = self._dynamic_kind(node)
        if call_kind is not None:
            literal = (node.args and isinstance(node.args[0], ast.Constant)
                       and isinstance(node.args[0].value, str))
            if literal and not rebound:
                self.local_refs = (_resolve_python_name(
                    self.path, node.args[0].value, self.index, self.edges)
                    or self.local_refs)
            else:
                self.dynamic_calls.append(
                    (self.path, getattr(node, "lineno", 0), call_kind))
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self._rebind(node.id)

    def visit_Assign(self, node):
        self.visit(node.value)
        for target in node.targets:
            self.visit(target)

    def visit_AnnAssign(self, node):
        if node.value is not None:
            self.visit(node.value)
        self.visit(node.target)
        self.visit(node.annotation)

    def visit_AugAssign(self, node):
        self.visit(node.value)
        self.visit(node.target)

    def visit_NamedExpr(self, node):
        self.visit(node.value)
        self.visit(node.target)

    def visit_FunctionDef(self, node):
        self._rebind(node.name)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self._rebind(node.name)
        self.generic_visit(node)


def python_analysis(root, files, include_failures=False, include_dynamic=False,
                    include_wrong_root=False):
    index, edges, local_refs = _python_index(files), set(), False
    failures, dynamic_calls, wrong_root_refs = [], [], []
    root_name = os.path.basename(os.path.abspath(root))
    for path in files:
        try:
            with open(os.path.join(root, path), encoding="utf-8",
                      errors="replace") as src:
                tree = ast.parse(src.read())
        except SyntaxError as exc:
            failures.append((path, str(exc)))
            continue
        visitor = _PythonImportVisitor(path, index, root_name)
        visitor.visit(tree)
        edges.update(visitor.edges)
        local_refs = visitor.local_refs or local_refs
        dynamic_calls.extend(visitor.dynamic_calls)
        wrong_root_refs.extend(visitor.wrong_root_refs)
    result = [edges, local_refs]
    if include_failures:
        result.append(failures)
    if include_dynamic:
        result.append(dynamic_calls)
    if include_wrong_root:
        result.append(wrong_root_refs)
    return tuple(result)


def python_edges(root, files):
    return python_analysis(root, files)[0]


def _strip_ts_comments(text):
    """Replace TS/JS comments with spaces while preserving strings/newlines."""
    chars = list(text)
    i, state, quote = 0, "code", ""
    while i < len(chars):
        char = chars[i]
        following = chars[i + 1] if i + 1 < len(chars) else ""
        if state == "code":
            if char in "'\"`":
                state, quote = "string", char
            elif char == "/" and following == "/":
                chars[i] = chars[i + 1] = " "
                state = "line"
                i += 1
            elif char == "/" and following == "*":
                chars[i] = chars[i + 1] = " "
                state = "block"
                i += 1
        elif state == "string":
            if char == "\\":
                i += 1
            elif char == "\n" and quote != "`":
                state = "code"
            elif char == quote:
                state = "code"
        elif state == "line":
            if char == "\n":
                state = "code"
            else:
                chars[i] = " "
        elif state == "block":
            if char == "*" and following == "/":
                chars[i] = chars[i + 1] = " "
                state = "code"
                i += 1
            elif char != "\n":
                chars[i] = " "
        i += 1
    return "".join(chars)


def _strip_json_trailing_commas(text):
    """Remove JSONC trailing commas without changing quoted string contents."""
    chars = list(text)
    i, quote = 0, None
    while i < len(chars):
        char = chars[i]
        if quote:
            if char == "\\":
                i += 1
            elif char == quote:
                quote = None
        elif char == '"':
            quote = char
        elif char == ",":
            probe = i + 1
            while probe < len(chars) and chars[probe].isspace():
                probe += 1
            if probe < len(chars) and chars[probe] in "}]":
                chars[i] = " "
        i += 1
    return "".join(chars)


def _ts_string_ranges(text):
    """Return non-code literal ranges, leaving template ${...} as code."""
    ranges = []

    def ordinary(i):
        quote, start = text[i], i
        i += 1
        while i < len(text):
            if text[i] == "\\":
                i += 2
            elif text[i] == "\n":
                break
            elif text[i] == quote:
                i += 1
                break
            else:
                i += 1
        ranges.append((start, min(i, len(text))))
        return i

    def template(i):
        raw_start = i
        i += 1
        while i < len(text):
            if text[i] == "\\":
                i += 2
            elif text[i] == "`":
                i += 1
                ranges.append((raw_start, i))
                return i
            elif text.startswith("${", i):
                ranges.append((raw_start, i + 2))
                i = expression(i + 2)
                raw_start = max(0, i - 1)
            else:
                i += 1
        ranges.append((raw_start, i))
        return i

    def expression(i):
        depth = 1
        while i < len(text) and depth:
            char = text[i]
            if char in "'\"":
                i = ordinary(i)
            elif char == "`":
                i = template(i)
            elif char == "{":
                depth += 1
                i += 1
            elif char == "}":
                depth -= 1
                i += 1
            else:
                i += 1
        return i

    i = 0
    while i < len(text):
        if text[i] in "'\"":
            i = ordinary(i)
        elif text[i] == "`":
            i = template(i)
        else:
            i += 1
    return ranges


REGEX_PREFIX_KEYWORDS = {
    "await", "case", "delete", "do", "else", "in", "instanceof", "new",
    "of", "return", "throw", "typeof", "void", "yield",
}


def _ts_lexical_text(text):
    """Mask comments and confidently recognized regex literals, preserving offsets."""
    chars = list(text)
    issues, i, can_start_regex = [], 0, True
    while i < len(chars):
        char = chars[i]
        following = chars[i + 1] if i + 1 < len(chars) else ""
        if char.isspace():
            i += 1
            continue
        if char in "'\"":
            quote = char
            i += 1
            while i < len(chars):
                if chars[i] == "\\":
                    i += 2
                elif chars[i] == quote:
                    i += 1
                    break
                elif chars[i] == "\n":
                    break
                else:
                    i += 1
            can_start_regex = False
            continue
        if char == "`":
            i += 1
            while i < len(chars):
                if chars[i] == "\\":
                    i += 2
                elif chars[i] == "`":
                    i += 1
                    break
                else:
                    i += 1
            can_start_regex = False
            continue
        if char == "/" and following in ("/", "*"):
            start = i
            if following == "/":
                i += 2
                while i < len(chars) and chars[i] != "\n":
                    i += 1
            else:
                i += 2
                while i + 1 < len(chars) and not (
                        chars[i] == "*" and chars[i + 1] == "/"):
                    i += 1
                i = min(len(chars), i + 2)
            for offset in range(start, i):
                if chars[offset] != "\n":
                    chars[offset] = " "
            continue
        if char == "/" and can_start_regex:
            start, probe, in_class, closed = i, i + 1, False, False
            while probe < len(chars) and chars[probe] != "\n":
                if chars[probe] == "\\":
                    probe += 2
                    continue
                if chars[probe] == "[":
                    in_class = True
                elif chars[probe] == "]":
                    in_class = False
                elif chars[probe] == "/" and not in_class:
                    probe += 1
                    while probe < len(chars) and (chars[probe].isalpha()
                                                   or chars[probe].isdigit()):
                        probe += 1
                    closed = True
                    break
                probe += 1
            if not closed:
                line = text.count("\n", 0, start) + 1
                issues.append("line %d: unterminated or ambiguous regex literal" % line)
                i += 1
                can_start_regex = True
                continue
            for offset in range(start, probe):
                if chars[offset] != "\n":
                    chars[offset] = " "
            i, can_start_regex = probe, False
            continue
        if char == "/":
            probe, in_class = i + 1, False
            while probe < len(chars) and chars[probe] != "\n":
                if chars[probe] == "\\":
                    probe += 2
                    continue
                if chars[probe] == "[":
                    in_class = True
                elif chars[probe] == "]":
                    in_class = False
                elif chars[probe] == "/" and not in_class:
                    segment = text[i + 1:probe]
                    if re.search(r"\b(?:import|require|export)\b", segment):
                        line = text.count("\n", 0, i) + 1
                        issues.append(
                            "line %d: ambiguous slash expression contains "
                            "dependency syntax" % line)
                    break
                probe += 1
            i += 2 if following == "=" else 1
            can_start_regex = True
            continue
        if char.isalpha() or char in "_$":
            start = i
            i += 1
            while i < len(chars) and (chars[i].isalnum() or chars[i] in "_$"):
                i += 1
            can_start_regex = text[start:i] in REGEX_PREFIX_KEYWORDS
            continue
        if char.isdigit():
            i += 1
            while i < len(chars) and (chars[i].isalnum() or chars[i] in "._"):
                i += 1
            can_start_regex = False
            continue
        if char in ")]}":
            can_start_regex = False
        elif char == ".":
            can_start_regex = False
        else:
            can_start_regex = True
        i += 1
    return "".join(chars), issues


def _ts_matches(text, lexical=None):
    """Yield import specifiers, excluding matches inside string literals."""
    stripped = lexical if lexical is not None else _ts_lexical_text(text)[0]
    ranges = _ts_string_ranges(stripped)
    for match in TS_IMPORT.finditer(stripped):
        if any(start <= match.start() < end for start, end in ranges):
            continue
        prefix = stripped[:match.start()].rstrip()
        if ((match.start() and stripped[match.start() - 1] in "_$") or
                prefix.endswith(".")):
            continue
        yield match, (match.group("static") or match.group("side") or
                      match.group("dynamic"))


def _ts_specifiers(text):
    for _match, specifier in _ts_matches(text):
        yield specifier


def _ts_candidates(base):
    stem, ext = os.path.splitext(base)
    remap = {
        ".js": (".ts", ".tsx", ".d.ts"),
        ".jsx": (".tsx", ".ts", ".d.ts"),
        ".mjs": (".mts", ".d.mts"),
        ".cjs": (".cts", ".d.cts"),
    }
    if ext in remap:
        return [stem + suffix for suffix in remap[ext]] + [base]
    if ext in TS_EXTS:
        return [base]
    return ([base + ext for ext in TS_EXTS]
            + [os.path.join(base, "index" + ext) for ext in TS_EXTS])


def _read_jsonc(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = _strip_json_trailing_commas(_strip_ts_comments(handle.read()))
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("configuration root must be an object")
    return value


def _extends_path(path, value):
    if not isinstance(value, str) or not value:
        raise ValueError("extends must be a non-empty string")
    if not value.startswith(("./", "../")):
        raise ValueError("non-local tsconfig/jsconfig extends is unsupported: %s" % value)
    resolved = os.path.normpath(os.path.join(os.path.dirname(path), value))
    if not os.path.splitext(resolved)[1]:
        resolved += ".json"
    return resolved


def _load_ts_config(path):
    path = os.path.abspath(path)
    chain, positions = [], {}
    current = path
    while True:
        if current in positions:
            cycle = [item[0] for item in chain[positions[current]:]] + [current]
            raise ValueError("tsconfig/jsconfig extends cycle: %s" %
                             " -> ".join(cycle))
        positions[current] = len(chain)
        config = _read_jsonc(current)
        chain.append((current, config))
        if "extends" not in config:
            break
        parent = _extends_path(current, config["extends"])
        if not os.path.isfile(parent):
            raise ValueError("extended config does not exist: %s" % parent)
        current = os.path.abspath(parent)

    base, paths = None, {}
    for config_path, config in reversed(chain):
        options = config.get("compilerOptions", {})
        if not isinstance(options, dict):
            raise ValueError("compilerOptions must be an object in %s" % config_path)
        if "baseUrl" in options:
            if not isinstance(options["baseUrl"], str):
                raise ValueError("compilerOptions.baseUrl must be a string in %s" %
                                 config_path)
            base = os.path.normpath(os.path.join(
                os.path.dirname(config_path), options["baseUrl"]))
        elif base is None:
            base = os.path.dirname(config_path)
        if "paths" not in options:
            continue
        candidate_paths = options["paths"]
        if not isinstance(candidate_paths, dict):
            raise ValueError("compilerOptions.paths must be an object in %s" %
                             config_path)
        for pattern, replacements in candidate_paths.items():
            if (not isinstance(pattern, str) or not isinstance(replacements, list)
                    or not all(isinstance(item, str) for item in replacements)):
                raise ValueError("invalid compilerOptions.paths entry in %s: %r" %
                                 (config_path, pattern))
        paths = candidate_paths
    return base, paths


def _read_ts_paths(root, include_issues=False):
    root = os.path.abspath(root)
    candidates = []
    for directory in (root, os.path.dirname(root)):
        for name in ("tsconfig.json", "jsconfig.json"):
            candidate = os.path.join(directory, name)
            if candidate not in candidates:
                candidates.append(candidate)
    issues = []
    for path in candidates:
        if not os.path.isfile(path):
            continue
        try:
            base, paths = _load_ts_config(path)
        except (OSError, ValueError, RecursionError) as exc:
            issues.append("cannot resolve %s: %s" % (path, exc))
            result = (None, {}, issues)
            return result if include_issues else result[:2]
        result = (base, paths, issues)
        return result if include_issues else result[:2]
    result = (None, {}, issues)
    return result if include_issues else result[:2]


def _alias_values(pattern, specifier):
    if "*" not in pattern:
        return [""] if pattern == specifier else []
    prefix, suffix = pattern.split("*", 1)
    if not specifier.startswith(prefix) or not specifier.endswith(suffix):
        return []
    end = len(specifier) - len(suffix) if suffix else len(specifier)
    return [specifier[len(prefix):end]]


def _inside(path, root):
    try:
        return os.path.commonpath((os.path.abspath(path), root)) == root
    except ValueError:
        return False


def _unmatched_ts_syntax(text, matches, lexical=None):
    stripped = lexical if lexical is not None else _ts_lexical_text(text)[0]
    ranges = _ts_string_ranges(stripped)
    spans = [match.span() for match, _specifier in matches]
    issues = []
    for token in re.finditer(r"\b(?:import|require|export)\b", stripped):
        start, word = token.start(), token.group(0)
        if any(left <= start < right for left, right in spans):
            continue
        if any(left <= start < right for left, right in ranges):
            continue
        if start and stripped[start - 1] == ".":
            continue
        tail = stripped[token.end():]
        if word == "import" and re.match(r"\s*\.\s*meta\b", tail):
            continue
        if word == "export":
            statement = tail.split(";", 1)[0]
            if not re.search(r"\bfrom\s*['\"]", statement):
                continue
        line = stripped.count("\n", 0, start) + 1
        issues.append("line %d: unrecognized %s syntax" % (line, word))
    return issues


def ts_analysis(root, files, include_issues=False):
    root_abs = os.path.abspath(root)
    fileset, edges = set(files), set()
    alias_base, aliases, config_issues = _read_ts_paths(root_abs, include_issues=True)
    relative_refs, unresolved, outside, syntax_issues = False, set(), set(), set()
    for path in files:
        with open(os.path.join(root, path), encoding="utf-8",
                  errors="replace") as src:
            text = src.read()
        lexical, lexical_issues = _ts_lexical_text(text)
        matches = list(_ts_matches(text, lexical))
        syntax_issues.update("%s:%s" % (path, issue) for issue in lexical_issues)
        syntax_issues.update("%s:%s" % (path, issue)
                             for issue in _unmatched_ts_syntax(text, matches, lexical))
        for _match, specifier in matches:
            bases = []
            if specifier.startswith(("./", "../")):
                relative_refs = True
                bases.append(os.path.normpath(
                    os.path.join(os.path.dirname(path), specifier)))
            else:
                matched = False
                for pattern, targets in aliases.items():
                    wildcard = _alias_values(pattern, specifier)
                    if not wildcard:
                        continue
                    matched = True
                    for target in targets if isinstance(targets, list) else []:
                        mapped = target.replace("*", wildcard[0])
                        absolute = os.path.normpath(os.path.join(alias_base, mapped))
                        if not _inside(absolute, root_abs):
                            outside.add("%s -> %s" % (specifier, absolute))
                            continue
                        bases.append(os.path.relpath(absolute, root_abs))
                if matched and not bases and not any(
                        item.startswith(specifier + " -> ") for item in outside):
                    unresolved.add(specifier)
                if not matched:
                    continue
            resolved = False
            for base in bases:
                for candidate in _ts_candidates(base):
                    candidate = os.path.normpath(candidate)
                    if candidate in fileset:
                        resolved = True
                        if candidate != path:
                            edges.add((path, candidate))
                        break
                if resolved:
                    break
            if not resolved and specifier.startswith(("./", "../")):
                extension = os.path.splitext(specifier)[1].lower()
                suffix = (" (non-code asset import unsupported by heuristic map)"
                          if extension and extension not in TS_EXTS else "")
                unresolved.add("%s -> %s%s" % (path, specifier, suffix))
            elif aliases and not specifier.startswith(("./", "../")) and bases and not resolved:
                unresolved.add("%s -> %s" % (path, specifier))
    result = (edges, relative_refs, unresolved, outside,
              set(config_issues), syntax_issues)
    return result if include_issues else result[:4]


def ts_edges(root, files):
    return ts_analysis(root, files)[0]


def tarjan(nodes, adj):
    """Iterative Tarjan traversal; safe for graphs deeper than Python's stack."""
    index, low, on, stack, sccs, counter = {}, {}, set(), [], [], 0
    for start in sorted(nodes):
        if start in index:
            continue
        index[start] = low[start] = counter
        counter += 1
        stack.append(start)
        on.add(start)
        frames = [[start, iter(sorted(adj.get(start, ()))), None]]
        while frames:
            vertex, children, parent = frames[-1]
            try:
                child = next(children)
            except StopIteration:
                frames.pop()
                if parent is not None:
                    low[parent] = min(low[parent], low[vertex])
                if low[vertex] == index[vertex]:
                    component = []
                    while True:
                        member = stack.pop()
                        on.discard(member)
                        component.append(member)
                        if member == vertex:
                            break
                    sccs.append(sorted(component))
                continue
            if child not in index:
                index[child] = low[child] = counter
                counter += 1
                stack.append(child)
                on.add(child)
                frames.append([child, iter(sorted(adj.get(child, ()))), vertex])
            elif child in on:
                low[vertex] = min(low[vertex], index[child])
    return sccs


def _write_parse_failures(out_dir, failures):
    os.makedirs(out_dir, exist_ok=True)
    for stale in ("edges.tsv", "nodes.txt", "order.txt", "package-cycles.tsv",
                  "dynamic-imports.txt"):
        try:
            os.unlink(os.path.join(out_dir, stale))
        except FileNotFoundError:
            pass
    with open(os.path.join(out_dir, "parse-failures.txt"), "w",
              encoding="utf-8", newline="\n") as out:
        for path, error in failures:
            out.write("%s\t%s\n" % (path, error.replace("\n", " ")))


def _write_dynamic_imports(out_dir, calls):
    os.makedirs(out_dir, exist_ok=True)
    _clear_map_outputs(out_dir)
    with open(os.path.join(out_dir, "dynamic-imports.txt"), "w",
              encoding="utf-8", newline="\n") as out:
        out.write("file\tline\tcall\n")
        for path, line, call_kind in sorted(calls):
            out.write("%s\t%d\t%s\n" % (path, line, call_kind))


def _clear_map_outputs(out_dir):
    for stale in ("edges.tsv", "nodes.txt", "order.txt", "package-cycles.tsv",
                  "dynamic-imports.txt"):
        try:
            os.unlink(os.path.join(out_dir, stale))
        except FileNotFoundError:
            pass


def main(argv=None):
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog=("TS/JS results are heuristic. Large-scale use requires compiler-API "
                "or authoritative build-graph validation."))
    ap.add_argument("--root", required=True)
    ap.add_argument("--lang", required=True, choices=["python", "ts"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--exclude", action="append", default=[],
                    help="additional directory name or root-relative path (repeatable)")
    ap.add_argument("--allow-unparseable", action="store_true",
                    help="write a partial Python map and mark parse failures")
    ap.add_argument("--allow-dynamic-imports", action="store_true",
                    help="allow nonliteral Python dynamic imports and retain a ledger")
    args = ap.parse_args(argv)

    exts = (".py",) if args.lang == "python" else TS_EXTS
    skipped = []
    files = sorted(walk(args.root, exts, args.exclude, skipped))
    if not files:
        print(f"no {args.lang} files under {args.root} — wrong --root?", file=sys.stderr)
        return 1
    failures, dynamic_calls, wrong_root_refs = [], [], []
    unresolved_aliases, outside_aliases = set(), set()
    config_issues, syntax_issues = set(), set()
    if args.lang == "python":
        (edges, has_local_import, failures, dynamic_calls,
         wrong_root_refs) = python_analysis(
            args.root, files, include_failures=True, include_dynamic=True,
            include_wrong_root=True)
        if failures:
            _write_parse_failures(args.out, failures)
            if not args.allow_unparseable:
                print("%d unparseable Python file(s); details written to %s" %
                      (len(failures), os.path.join(args.out, "parse-failures.txt")),
                      file=sys.stderr)
                return 1
            print("warn: allowing %d unparseable Python file(s); see %s" %
                  (len(failures), os.path.join(args.out, "parse-failures.txt")),
                  file=sys.stderr)
        if dynamic_calls:
            _write_dynamic_imports(args.out, dynamic_calls)
            if not args.allow_dynamic_imports:
                print("%d nonliteral Python dynamic import call(s); refusing a "
                      "partial map; details written to %s" %
                      (len(dynamic_calls),
                       os.path.join(args.out, "dynamic-imports.txt")),
                      file=sys.stderr)
                return 1
            print("warn: allowing %d nonliteral Python dynamic import call(s); see %s" %
                  (len(dynamic_calls), os.path.join(args.out, "dynamic-imports.txt")),
                  file=sys.stderr)
        if wrong_root_refs:
            _clear_map_outputs(args.out)
            examples = ", ".join("%s:%d (%s)" % item
                                 for item in sorted(wrong_root_refs)[:3])
            print("root-qualified import(s) resolve inside the selected directory: %s; "
                  "--root is probably one level too deep; run from parent/root "
                  "directory so package %r is included in module names." %
                  (examples, os.path.basename(os.path.abspath(args.root))),
                  file=sys.stderr)
            return 1
    else:
        (edges, has_local_import, unresolved_aliases, outside_aliases,
         config_issues, syntax_issues) = ts_analysis(
            args.root, files, include_issues=True)
        for issue in sorted(config_issues):
            print("error: %s" % issue, file=sys.stderr)
        if unresolved_aliases:
            print("error: unresolved local imports or tsconfig/jsconfig aliases: %s" %
                  ", ".join(sorted(unresolved_aliases)), file=sys.stderr)
        for note in sorted(outside_aliases):
            print("error: path alias resolves outside --root: %s" % note,
                  file=sys.stderr)
        for issue in sorted(syntax_issues):
            print("error: %s" % issue, file=sys.stderr)
        if config_issues or unresolved_aliases or outside_aliases or syntax_issues:
            _clear_map_outputs(args.out)
            print("refusing a partial heuristic TS/JS map; fix resolution or validate "
                  "with the compiler/build graph", file=sys.stderr)
            return 1
    if not edges and has_local_import and len(files) > 1:
        _clear_map_outputs(args.out)
        print("0 edges but local imports exist — almost certainly a wrong "
              "--root (see references/mapping.md zero-edge rule). Refusing "
              "to write an empty map.", file=sys.stderr)
        return 1

    os.makedirs(args.out, exist_ok=True)
    if not failures:
        try:
            os.unlink(os.path.join(args.out, "parse-failures.txt"))
        except FileNotFoundError:
            pass
    if not dynamic_calls:
        try:
            os.unlink(os.path.join(args.out, "dynamic-imports.txt"))
        except FileNotFoundError:
            pass
    adj = {}
    for source, target in sorted(edges):
        adj.setdefault(source, set()).add(target)
    with open(os.path.join(args.out, "edges.tsv"), "w", encoding="utf-8",
              newline="\n") as out:
        out.write("from\tto\n")
        for source, target in sorted(edges):
            out.write(f"{source}\t{target}\n")

    linked = {node for edge in edges for node in edge}
    failed_paths = {path for path, _error in failures}
    rows = [(path, "PARSE-FAILED" if path in failed_paths else
             ("" if path in linked else "ISOLATED")) for path in files]
    rows += [(path, "SYMLINK-SKIPPED") for path in skipped]
    with open(os.path.join(args.out, "nodes.txt"), "w", encoding="utf-8",
              newline="\n") as out:
        for path, marker in sorted(rows):
            out.write(f"{path}{chr(9) + marker if marker else ''}\n")

    sccs = tarjan(files, adj)
    with open(os.path.join(args.out, "order.txt"), "w", encoding="utf-8",
              newline="\n") as out:
        for number, comp in enumerate(sccs, 1):
            marker = " CYCLE" if len(comp) > 1 else ""
            out.write(f"# batch {number}{marker}\n" + "".join(p + "\n" for p in comp))

    package = lambda path: os.path.dirname(path) or "."
    package_adj = {}
    for source, target in sorted(edges):
        if package(source) != package(target):
            package_adj.setdefault(package(source), set()).add(package(target))
    package_sccs = tarjan(sorted({package(path) for path in files}), package_adj)
    with open(os.path.join(args.out, "package-cycles.tsv"), "w",
              encoding="utf-8", newline="\n") as out:
        out.write("cycle_id\tpackages\n")
        cycles = [comp for comp in package_sccs if len(comp) > 1]
        for number, comp in enumerate(cycles, 1):
            out.write(f"P-{number}\t{','.join(comp)}\n")

    if (not edges and not has_local_import and not failures and not unresolved_aliases
            and not outside_aliases and not config_issues and not syntax_issues):
        print("0 local imports — isolated files only")
    print(f"{len(files)} files, {len(edges)} edges, "
          f"{sum(1 for comp in sccs if len(comp) > 1)} file cycles, "
          f"{len(cycles)} package cycles → {args.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
