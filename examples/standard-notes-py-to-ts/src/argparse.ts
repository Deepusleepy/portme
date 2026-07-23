// Minimal argparse-compatible parser for the fixed `notes` grammar, reproducing
// Python 3.14.6 argparse's usage/help/error text byte-for-byte (rulebook R-002,
// R-011), the subparser-vs-top-level prog/usage routing (R-003), CPython int()
// parsing for the `remove` number (R-010), and negative-number-as-positional
// (R-014). No third-party dependency (NF-001).
import { pyRepr } from './difflib.js';

// Thrown to unwind to main() with a process exit code (R-004).
export class ParserExit extends Error {
  code: number;
  constructor(code: number) {
    super(`ParserExit(${code})`);
    this.code = code;
  }
}

// --- Frozen text, verbatim from the Python 3.14.6 oracle (R-011) ---
const TOP_USAGE = 'usage: notes [-h] command ...\n';
const TOP_HELP =
  'usage: notes [-h] command ...\n' +
  '\n' +
  'Keep plain-text notes.\n' +
  '\n' +
  'positional arguments:\n' +
  '  command\n' +
  '    add       Add a note\n' +
  '    list      List notes\n' +
  '    search    Search notes\n' +
  '    remove    Remove a note by number\n' +
  '\n' +
  'options:\n' +
  '  -h, --help  show this help message and exit\n';

interface SubDef {
  usage: string;
  help: string;
  positional: { name: string; type: 'str' | 'int' } | null;
}

const SUBS: Record<string, SubDef> = {
  add: {
    usage: 'usage: notes add [-h] text\n',
    help:
      'usage: notes add [-h] text\n\npositional arguments:\n  text\n\n' +
      'options:\n  -h, --help  show this help message and exit\n',
    positional: { name: 'text', type: 'str' },
  },
  list: {
    usage: 'usage: notes list [-h]\n',
    help:
      'usage: notes list [-h]\n\noptions:\n  -h, --help  show this help message and exit\n',
    positional: null,
  },
  search: {
    usage: 'usage: notes search [-h] term\n',
    help:
      'usage: notes search [-h] term\n\npositional arguments:\n  term\n\n' +
      'options:\n  -h, --help  show this help message and exit\n',
    positional: { name: 'term', type: 'str' },
  },
  remove: {
    usage: 'usage: notes remove [-h] number\n',
    help:
      'usage: notes remove [-h] number\n\npositional arguments:\n  number\n\n' +
      'options:\n  -h, --help  show this help message and exit\n',
    positional: { name: 'number', type: 'int' },
  },
};

// Insertion order — argparse lists choices in definition order, not sorted.
const CHOICES = ['add', 'list', 'search', 'remove'];

// argparse._negative_number_matcher.
const NEG_NUMBER = /^-\d+$|^-\d*\.\d+$/;

function looksLikeOption(t: string): boolean {
  if (t.length === 0 || t[0] !== '-') return false;
  if (t === '-') return false; // a lone dash is a positional value
  if (NEG_NUMBER.test(t)) return false; // negative number → positional (R-014)
  return true;
}

// CPython int(str) for base 10: optional surrounding whitespace, optional single
// sign, digits with single underscores strictly between digits. Returns null on
// anything CPython would reject (float, hex, empty, stray chars). Returns a
// bigint to preserve CPython's arbitrary-precision integers exactly (R-010).
// ASCII digits only; Python int() also accepts Unicode Nd digits — accepted
// divergence D-002.
export function pyInt(token: string): bigint | null {
  const s = token.trim();
  if (!/^[+-]?\d(?:_?\d)*$/.test(s)) return null;
  const neg = s[0] === '-';
  const digits = s.replace(/^[+-]/, '').replace(/_/g, '');
  const v = BigInt(digits);
  return neg ? -v : v;
}

function errorTop(message: string): never {
  process.stderr.write(TOP_USAGE);
  process.stderr.write(`notes: error: ${message}\n`);
  throw new ParserExit(2);
}
function errorSub(sub: string, message: string): never {
  process.stderr.write(SUBS[sub].usage);
  process.stderr.write(`notes ${sub}: error: ${message}\n`);
  throw new ParserExit(2);
}

export type ParseResult =
  | { kind: 'none' } // no subcommand → caller prints top help, exit 0
  | { kind: 'command'; command: string; value?: string | bigint };

// suggest(bad, choices) → the "did you mean" phrase to append, or null (R-006).
export function parse(
  argv: string[],
  suggest: (bad: string, choices: string[]) => string | null,
): ParseResult {
  const extrasTop: string[] = [];
  let i = 0;
  let sawSep = false;

  // Phase A: top-level tokens up to the first positional (the subcommand).
  // The first `--` toggles positional-only mode; consumed if a subcommand
  // follows, otherwise reported literally as unrecognized (argparse quirk).
  for (; i < argv.length; i++) {
    const t = argv[i];
    if (sawSep) break; // the token after the separator is the subcommand
    if (t === '--') { sawSep = true; continue; }
    if (t === '-h' || t === '--help') {
      process.stdout.write(TOP_HELP);
      throw new ParserExit(0);
    }
    if (looksLikeOption(t)) { extrasTop.push(t); continue; }
    break; // first positional = subcommand
  }

  if (i >= argv.length) {
    // No subcommand token. A dangling separator becomes an unrecognized arg.
    if (sawSep) extrasTop.push('--');
    if (extrasTop.length) errorTop(`unrecognized arguments: ${extrasTop.join(' ')}`);
    return { kind: 'none' };
  }

  const sub = argv[i];
  const rest = argv.slice(i + 1);

  if (!Object.prototype.hasOwnProperty.call(SUBS, sub)) {
    const choiceList = CHOICES.map(pyRepr).join(', ');
    let message = `argument command: invalid choice: ${pyRepr(sub)} (choose from ${choiceList})`;
    const phrase = suggest(sub, CHOICES);
    if (phrase) message += `. ${phrase}`;
    errorTop(message);
  }

  const def = SUBS[sub];
  const positionals: string[] = [];
  const extras: string[] = [];
  let subSep = false;
  for (let k = 0; k < rest.length; k++) {
    const t = rest[k];
    if (subSep) {
      // Positional-only region after the separator.
      if (def.positional && positionals.length < 1) positionals.push(t);
      else extras.push(t);
      continue;
    }
    if (t === '--') {
      subSep = true;
      // A separator a positional can consume is removed; otherwise it is a
      // literal unrecognized token (argparse quirk, e.g. `notes list --`).
      if (!def.positional) extras.push('--');
      continue;
    }
    if (t === '-h' || t === '--help') {
      process.stdout.write(def.help);
      throw new ParserExit(0);
    }
    if (looksLikeOption(t)) { extras.push(t); continue; }
    if (def.positional && positionals.length < 1) positionals.push(t);
    else extras.push(t); // extra positional beyond the arity
  }

  // Missing required positional (subparser owns this error — R-003).
  if (def.positional && positionals.length < 1) {
    errorSub(sub, `the following arguments are required: ${def.positional.name}`);
  }

  let value: string | bigint | undefined;
  if (def.positional) {
    if (def.positional.type === 'int') {
      const parsed = pyInt(positionals[0]);
      if (parsed === null) {
        errorSub(sub, `argument ${def.positional.name}: invalid int value: ${pyRepr(positionals[0])}`);
      }
      value = parsed as bigint;
    } else {
      value = positionals[0];
    }
  }

  // Leftover tokens → top-level unrecognized-arguments sweep (R-003).
  const allExtras = extrasTop.concat(extras);
  if (allExtras.length) errorTop(`unrecognized arguments: ${allExtras.join(' ')}`);

  return { kind: 'command', command: sub, value };
}

export { TOP_HELP };
