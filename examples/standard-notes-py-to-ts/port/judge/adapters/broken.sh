#!/usr/bin/env bash
# Deliberately-broken adapter for Phase 0 two-way judge validation.
# Wraps the source oracle and corrupts exactly ONE comparator class, selected
# by $MUTATION, so the judge must reject it. Real file side effects still run
# (source executes); only the observed channel named by $MUTATION is tampered.
#   MUTATION=stdout  lowercase the "Added"/"Removed" stdout words
#   MUTATION=stderr  strip the did-you-mean suffix from stderr
#   MUTATION=exit    coerce the remove-out-of-range exit 1 into 0
#   MUTATION=file    append a stray line to the notes file after the command
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$HERE/../../.." && pwd -P)"
SRC="${PORTME_SOURCE_DIR:-$ROOT/source-python}"
o="$(mktemp)"; e="$(mktemp)"
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SRC" python3 -m notes_cli.cli "$@" >"$o" 2>"$e"; rc=$?
case "${MUTATION:-}" in
  stdout) sed -e 's/Added/added/' -e 's/Removed/removed/' "$o" ; cat "$e" >&2 ;;
  stderr) cat "$o" ; sed -E -e 's/\. Did you mean [^\n]*//' -e 's/\. \(Did you mean one of[^\n]*//' "$e" >&2 ;;
  exit)   cat "$o" ; cat "$e" >&2 ; [ "$rc" = "1" ] && rc=0 ;;
  file)   cat "$o" ; cat "$e" >&2 ; printf 'STRAY\n' >>"${NOTES_FILE:-/dev/null}" ;;
  *)      cat "$o" ; cat "$e" >&2 ;;
esac
rm -f "$o" "$e"
exit "$rc"
