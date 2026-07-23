#!/usr/bin/env bash
# Phase 2 adversarial stress: run a wide battery of edge-case argv vectors NOT in
# the frozen golden against BOTH the source oracle and the port, and diff
# stdout/stderr/exit. Attacks R-002 (argparse text), R-003 (prog routing),
# R-010 (int parsing), R-011 (usage/help strings), R-014 (negative numbers).
# Any MISMATCH is a rule/implementation defect to harvest.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/adapters/source.sh"
PORT="$HERE/adapters/port.sh"
SEED=( "alpha" "beta gamma" )

run() { # <adapter> ; args passed via global ARGS array; uses global NF
  : >"$NF"; local l; for l in "${SEED[@]}"; do printf '%s\n' "$l" >>"$NF"; done
  NOTES_FILE="$NF" "$1" ${ARGS[@]+"${ARGS[@]}"} >"$2" 2>"$3"; echo $?
}

mismatch=0; total=0
probe() { # description, then argv...
  local desc="$1"; shift
  ARGS=("$@"); total=$((total+1))
  local NF so se po pe sr pr; NF="$(mktemp)"; so="$(mktemp)"; se="$(mktemp)"; po="$(mktemp)"; pe="$(mktemp)"
  sr="$(run "$SRC" "$so" "$se")"
  pr="$(run "$PORT" "$po" "$pe")"
  if [ "$sr" = "$pr" ] && diff -q "$so" "$po" >/dev/null && diff -q "$se" "$pe" >/dev/null; then
    printf 'OK    %s\n' "$desc"
  else
    mismatch=$((mismatch+1))
    printf 'DIFF  %s\n' "$desc"
    printf '  argv:'; printf ' %q' "${ARGS[@]}"; printf '\n'
    printf '  exit  src=%s port=%s\n' "$sr" "$pr"
    diff <(printf 'STDOUT|'; cat "$so"; printf 'STDERR|'; cat "$se") \
         <(printf 'STDOUT|'; cat "$po"; printf 'STDERR|'; cat "$pe") | sed 's/^/  /'
  fi
  rm -f "$NF" "$so" "$se" "$po" "$pe"
}

echo "### R-014 negative numbers & sign/underscore int parsing (R-010) ###"
probe "remove -1"        remove -1
probe "remove -5"        remove -5
probe "remove -0"        remove -0
probe "remove -1.5"      remove -1.5
probe "remove +2"        remove +2
probe "remove 007"       remove 007
probe "remove 1_0"       remove 1_0
probe "remove 1__0"      remove 1__0
probe "remove 5_"        remove 5_
probe "remove _5"        remove _5
probe "remove 0x10"      remove 0x10
probe "remove 1.0"       remove 1.0
probe "remove empty"     remove ""
probe "remove 3abc"      remove 3abc
probe "remove sp 3 sp"   remove " 3 "
probe "search -1 (neg as term)" search -1
probe "add -5 (neg as text)"    add -5

echo "### R-003 prog routing / help paths / unrecognized ###"
probe "top -h before sub"    -h add
probe "sub add -h"           add -h
probe "sub list --help"      list --help
probe "sub search -h"        search -h
probe "remove -h with extra" remove -h 5
probe "add missing"          add
probe "search missing"       search
probe "remove missing"       remove
probe "add extra a b c"      add a b c
probe "list extra"           list extra
probe "remove 1 2 3"         remove 1 2 3
probe "unknown --bad"        --bad
probe "unknown -x"           -x
probe "add --bad"            add --bad
probe "list --bad"           list --bad
probe "double dash then sub" -- add hello
probe "double dash then bad" -- lst
probe "sub add dashdash neg" add -- -5

echo "### R-005/R-006 did-you-mean variants ###"
probe "ad"        ad
probe "lis"       lis
probe "sea"       sea
probe "rmv"       rmv
probe "remov"     remov
probe "remove"    remove
probe "l"         l
probe "searchx"   searchx
probe "adds"      adds
probe "ADD upper" ADD
probe "listt"     listt
probe "aad"       aad
probe "serch"     serch

echo "### R-003/argparse '--' separator quirk ###"
probe "bare --"            --
probe "-- --"              -- --
probe "-- add hello"       -- add hello
probe "-- lst"             -- lst
probe "list --"            list --
probe "list -- extra"      list -- extra
probe "add --"             add --
probe "add -- hello"       add -- hello
probe "add -- --"          add -- --
probe "remove --"          remove --
probe "remove -- 1"        remove -- 1
probe "search -- foo"      search -- foo
probe "add a -- b"         add a -- b
probe "remove 1 -- 2"      remove 1 -- 2

echo "### misc surfaces ###"
probe "no args"          # (none)
probe "just --"          --
probe "add empty"        add ""
probe "search empty"     search ""
probe "search no-match"  search zzzznote
probe "add then dup num" add "alpha"
probe "remove huge"      remove 999999
probe "remove top count" remove 2

echo
printf '===== STRESS SUMMARY: %d/%d probes match, %d mismatches =====\n' "$((total-mismatch))" "$total" "$mismatch"
exit $((mismatch>0))
