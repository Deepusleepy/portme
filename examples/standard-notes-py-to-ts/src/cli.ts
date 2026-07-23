#!/usr/bin/env node
// Port of notes_cli/cli.py — wires the argparse-compatible parser to the
// command implementations, augments the invalid-subcommand error with the
// Click-style "did you mean" suggestion (mirroring NotesArgumentParser), and
// routes exit codes (R-004). Entry point runs `node dist/cli.js`.
import { realpathSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { parse, ParserExit, TOP_HELP } from './argparse.js';
import { getCloseMatches, formatPossibilities } from './difflib.js';
import * as commands from './commands.js';

// NotesArgumentParser.error's suggestion hook: difflib.get_close_matches with
// CPython defaults (n=3, cutoff=0.6), formatted like Click (R-005, R-006).
function suggest(bad: string, choices: string[]): string | null {
  const matches = getCloseMatches(bad, choices);
  return matches.length ? formatPossibilities(matches) : null;
}

export function main(argv: string[]): number {
  let result;
  try {
    result = parse(argv, suggest);
  } catch (e) {
    if (e instanceof ParserExit) return e.code;
    throw e;
  }

  if (result.kind === 'none') {
    // No subcommand: argparse leaves args.func unset → print_help(), return 0.
    process.stdout.write(TOP_HELP);
    return 0;
  }

  switch (result.command) {
    case 'add':
      return commands.add(result.value as string);
    case 'list':
      return commands.listNotes();
    case 'search':
      return commands.search(result.value as string);
    case 'remove':
      return commands.remove(result.value as bigint);
    default:
      // Unreachable: parse() only returns known commands.
      return 0;
  }
}

// Run main only when executed directly (node dist/cli.js), not when imported.
// Resolve both sides through the filesystem so logically different paths to
// the same file (notably /tmp vs /private/tmp on macOS, or any symlinked path
// component) still identify the entry point correctly.
function isDirectEntry(): boolean {
  if (!process.argv[1]) return false;
  try {
    return realpathSync(process.argv[1]) === realpathSync(fileURLToPath(import.meta.url));
  } catch {
    return false;
  }
}

if (isDirectEntry()) {
  process.exit(main(process.argv.slice(2)));
}
