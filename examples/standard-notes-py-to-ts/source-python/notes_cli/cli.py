"""notes — a tiny CLI for keeping plain-text notes."""
import argparse
import ast
import re
from difflib import get_close_matches
import sys

from . import commands

# Matches argparse's invalid-choice message, capturing the repr'd bad token.
# argparse formats the value with %r, so the captured group is a Python repr.
_INVALID_CHOICE_RE = re.compile(r"invalid choice: (?P<value>'(?:[^'\\]|\\.)*'|\".*?\")")


def _format_possibilities(possibilities) -> str:
    """Mirror of Click's click.exceptions._format_possibilities.

    Possibilities are sorted, each repr()'d and comma-joined; singular and
    plural use the same phrasing Click emits.
    """
    possibility_str = ", ".join(repr(p) for p in sorted(possibilities))
    if len(possibilities) == 1:
        return f"Did you mean {possibility_str}?"
    return f"(Did you mean one of: {possibility_str}?)"


class NotesArgumentParser(argparse.ArgumentParser):
    """argparse parser that appends Click-style "did you mean" suggestions
    to the unknown-subcommand error, while preserving argparse's message,
    usage banner, and exit code (2)."""

    def error(self, message):
        match = _INVALID_CHOICE_RE.search(message)
        if match:
            try:
                bad = ast.literal_eval(match.group("value"))
            except (ValueError, SyntaxError):
                bad = None
            choices = self._subcommand_choices()
            if bad is not None and choices:
                # Same matching approach as Click: difflib.get_close_matches
                # with its defaults (n=3, cutoff=0.6).
                matches = get_close_matches(bad, choices)
                if matches:
                    message = f"{message}. {_format_possibilities(matches)}"
        super().error(message)

    def _subcommand_choices(self):
        """Valid subcommand names, i.e. Click's equivalent of Group.commands."""
        for action in self._actions:
            if isinstance(action, argparse._SubParsersAction):
                return list(action.choices)
        return None


def build_parser() -> argparse.ArgumentParser:
    parser = NotesArgumentParser(prog="notes", description="Keep plain-text notes.")
    sub = parser.add_subparsers(dest="command", metavar="command")

    p_add = sub.add_parser("add", help="Add a note")
    p_add.add_argument("text")
    p_add.set_defaults(func=commands.add)

    p_list = sub.add_parser("list", help="List notes")
    p_list.set_defaults(func=commands.list_notes)

    p_search = sub.add_parser("search", help="Search notes")
    p_search.add_argument("term")
    p_search.set_defaults(func=commands.search)

    p_remove = sub.add_parser("remove", help="Remove a note by number")
    p_remove.add_argument("number", type=int)
    p_remove.set_defaults(func=commands.remove)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
