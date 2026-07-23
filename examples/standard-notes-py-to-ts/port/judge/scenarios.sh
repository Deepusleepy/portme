#!/usr/bin/env bash
# Scenario definitions for the notes-CLI differential judge.
#
# Each scenario is a shell function `scn_<id>` that drives the CLI through one
# or more invocations and emits a deterministic transcript to stdout. The
# harness (capture.sh) runs each scenario twice — once per adapter (source vs
# port) — into results/<label>/<id>.txt, then compare.sh diffs them.
#
# A scenario uses only:
#   step <argv...>   run `$CLI <argv>` against $NOTES_FILE; append argv/exit/stdout/stderr
#   seed <line...>   write given lines to $NOTES_FILE
#   dumpfile         append the byte content of $NOTES_FILE (od -An -c)
# $CLI is an absolute path to an adapter script; $NOTES_FILE is a fresh temp
# file reset before every scenario by the harness.

SCENARIOS="c1_add c2_list c3_search c4_remove_ok c5_remove_oob c6_remove_nonint c7_help c8_dym_singular c9_dym_plural c10_dym_none c11_missing_req c12_unrecognized c13_fileformat c13b_defaultpath c14_unicode_whitespace"

_TMPO="$(mktemp)"; _TMPE="$(mktemp)"
trap 'rm -f "$_TMPO" "$_TMPE"' EXIT

step() {
  printf '$ notes'; printf ' %q' "$@"; printf '\n'
  "$CLI" "$@" >"$_TMPO" 2>"$_TMPE"; local rc=$?
  printf 'exit=%d\n' "$rc"
  printf -- '--stdout--\n'; cat "$_TMPO"
  printf -- '--stderr--\n'; cat "$_TMPE"
  printf -- '--end--\n'
}

seed() { : >"$NOTES_FILE"; local l; for l in "$@"; do printf '%s\n' "$l" >>"$NOTES_FILE"; done; }
seed_raw() { printf '%b' "$1" >"$NOTES_FILE"; }  # raw bytes incl. blank lines
dumpfile() { printf -- '--file--\n'; if [ -f "$NOTES_FILE" ]; then od -An -c "$NOTES_FILE"; else printf '(no file)\n'; fi; }

scn_c1_add() {           # S1,S14 : two adds build the file
  step add "hello world"
  step add "Buy MILK"
  dumpfile
}
scn_c2_list() {          # S2 : populated then empty
  seed "hello world" "Buy MILK"; step list
  seed;                  step list
}
scn_c3_search() {        # S3a : case-insensitive (ASCII), original index
  seed "hello world" "Buy MILK"
  step search milk
  step search HELLO
  step search zzz
}
scn_c4_remove_ok() {     # S4 : remove in range rewrites file
  seed "hello world" "Buy MILK"
  step remove 1
  dumpfile
}
scn_c5_remove_oob() {    # S5 : out of range → stderr, exit 1, file intact
  seed "hello world" "Buy MILK"
  step remove 5
  step remove 0
  step remove -1
  dumpfile
  seed; step remove 1    # empty store
}
scn_c6_remove_nonint() { # S6a : invalid int value (ASCII), exit 2
  step remove abc
}
scn_c7_help() {          # S7,S8 : help surfaces
  step
  step -h
  step --help
  step add -h
  step list -h
  step search -h
  step remove -h
}
scn_c8_dym_singular() {  # S9
  step lst
}
scn_c9_dym_plural() {    # S10
  step addlis
}
scn_c10_dym_none() {     # S11
  step xyz
}
scn_c11_missing_req() {  # S12
  step add
  step search
  step remove
}
scn_c12_unrecognized() { # S13
  step add a b
  step remove 1 2
  step --bad
}
scn_c13_fileformat() {   # S14 : blank/whitespace lines skipped, rstrip only \n
  seed_raw 'a\n\n   \nb\n'
  step list
  step add c
  dumpfile
  # preserve leading/trailing spaces within a note
  seed_raw '  spaced  \n'
  step list
  step add tail
  dumpfile
}
scn_c13b_defaultpath() { # S15 : NOTES_FILE unset → $HOME/.notes.txt
  # harness sets HOME to a sandbox and unsets NOTES_FILE for this scenario only
  step add fromdefault
  step list
  printf -- '--homefile--\n'
  if [ -f "$HOME/.notes.txt" ]; then od -An -c "$HOME/.notes.txt"; else printf '(no ~/.notes.txt)\n'; fi
}
scn_c14_unicode_whitespace() { # S14: Python strip set differs from JS trim
  # U+FEFF is retained by Python (but JS trim removes it); U+001C is skipped by
  # Python (but JS trim retains it). Also prove retained content is unchanged.
  seed_raw '\357\273\277\n\034\nkeep\357\273\277\n'
  step list
  step add tail
  dumpfile
}
