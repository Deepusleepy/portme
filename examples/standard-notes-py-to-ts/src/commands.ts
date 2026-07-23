// Port of notes_cli/commands.py — plain-text notes store + subcommand impls.
// Rulebook: R-001 (print/stderr mapping, per-invocation path), R-007 (read:
// universal newlines + blank-line skip + trailing-\n strip), R-008
// (Python-compatible str.strip whitespace for the blank test), R-009 (write),
// and the search original-index rule (G-008).
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

function out(s: string): void {
  process.stdout.write(s);
}
function err(s: string): void {
  process.stderr.write(s);
}

// CPython's default str.strip()/str.isspace() set. It intentionally differs
// from ECMAScript String.prototype.trim(): Python strips U+001C..U+001F but
// does not strip U+FEFF (BOM). This predicate only decides whether to retain a
// line; retained line contents are never modified.
const PYTHON_WHITESPACE_ONLY =
  /^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]*$/u;

function isPythonWhitespaceOnly(value: string): boolean {
  return PYTHON_WHITESPACE_ONLY.test(value);
}

// os.environ.get("NOTES_FILE", os.path.expanduser("~/.notes.txt")).
// Faithful to CPython: the default applies only when the key is ABSENT (an
// explicitly-empty NOTES_FILE is honored as ""), and expanduser("~") uses $HOME.
export function notesFile(): string {
  if (Object.prototype.hasOwnProperty.call(process.env, 'NOTES_FILE')) {
    return process.env.NOTES_FILE as string;
  }
  return join(homedir(), '.notes.txt');
}

function read(): string[] {
  const path = notesFile();
  if (!existsSync(path)) return [];
  // Python text mode applies universal newlines before line iteration.
  const text = readFileSync(path, 'utf8').replace(/\r\n/g, '\n').replace(/\r/g, '\n');
  // Split into lines; the trailing empty artifact (and any Python-whitespace-
  // only line) is dropped, matching `if line.strip()` exactly. Kept contents
  // remain unchanged, including leading/trailing whitespace and U+FEFF.
  return text.split('\n').filter((line) => !isPythonWhitespaceOnly(line));
}

function write(notes: string[]): void {
  writeFileSync(notesFile(), notes.map((n) => n + '\n').join(''), 'utf8');
}

export function add(text: string): number {
  const notes = read();
  notes.push(text);
  write(notes);
  out(`Added note ${notes.length}.\n`);
  return 0;
}

export function listNotes(): number {
  const notes = read();
  for (let i = 0; i < notes.length; i++) {
    out(`${i + 1}. ${notes[i]}\n`);
  }
  return 0;
}

export function search(term: string): number {
  const notes = read();
  const needle = term.toLowerCase();
  for (let i = 0; i < notes.length; i++) {
    if (notes[i].toLowerCase().includes(needle)) {
      out(`${i + 1}. ${notes[i]}\n`);
    }
  }
  return 0;
}

// n is a bigint to mirror CPython's arbitrary-precision int exactly (R-010):
// the range check and the echoed number must match Python for any magnitude.
export function remove(n: bigint): number {
  const notes = read();
  if (!(1n <= n && n <= BigInt(notes.length))) {
    err(`error: no note number ${n}\n`);
    return 1;
  }
  const removed = notes.splice(Number(n) - 1, 1)[0];
  write(notes);
  out(`Removed: ${removed}\n`);
  return 0;
}
