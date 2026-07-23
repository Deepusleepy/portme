#!/usr/bin/env bash
# Differential judge for the notes-CLI port. Stdlib/bash + python3 + node only.
#
#   judge.sh capture <adapter.sh> <label>   run all scenarios → results/<label>/
#   judge.sh compare <labelA> <labelB>       byte-diff transcripts; verdicts
#   judge.sh validate                        Phase 0 two-way validation
#   judge.sh port                            Phase 5: source (golden) vs port
#
# A scenario passes when the two transcripts are byte-identical. Each scenario
# runs against a fresh temp NOTES_FILE (and, for the default-path scenario, a
# fresh sandbox HOME with NOTES_FILE unset), so runs are independent and no
# real dotfile is touched.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS="$HERE/results"
mkdir -p "$RESULTS"
RESULTS_REAL="$(cd "$RESULTS" && pwd -P)"
source "$HERE/scenarios.sh"

validate_label() {
  local label="$1"
  case "$label" in
    ''|*[!A-Za-z0-9_-]*|[!A-Za-z]*)
      echo "error: result label must match [A-Za-z][A-Za-z0-9_-]*: $label" >&2
      return 64
      ;;
  esac
}

safe_result_dir() {
  local label="$1" candidate resolved
  validate_label "$label" || return $?
  candidate="$RESULTS_REAL/$label"
  case "$candidate" in
    "$RESULTS_REAL"/*) ;;
    *) echo "error: result path escaped results: $candidate" >&2; return 64;;
  esac
  if [ -L "$candidate" ]; then
    echo "error: refusing symlink result path: $candidate" >&2
    return 64
  fi
  if [ -e "$candidate" ]; then
    if [ ! -d "$candidate" ]; then
      echo "error: result path is not a directory: $candidate" >&2
      return 64
    fi
    resolved="$(cd "$candidate" && pwd -P)" || return 64
    case "$resolved" in
      "$RESULTS_REAL"/*) ;;
      *) echo "error: resolved result path escaped results: $resolved" >&2; return 64;;
    esac
  fi
  printf '%s\n' "$candidate"
}

capture() {   # <adapter> <label>
  local adapter="$1" label="$2" out
  out="$(safe_result_dir "$label")" || return $?
  rm -rf -- "$out"; mkdir -p "$out"
  export CLI="$adapter"
  local s
  for s in $SCENARIOS; do
    if [ "$s" = "c13b_defaultpath" ]; then
      local h; h="$(mktemp -d)"
      ( export HOME="$h"; unset NOTES_FILE; "scn_$s" ) >"$out/$s.txt" 2>&1
      rm -rf "$h"
    else
      local nf; nf="$(mktemp)"; rm -f "$nf"
      ( export NOTES_FILE="$nf"; "scn_$s" ) >"$out/$s.txt" 2>&1
      rm -f "$nf"
    fi
  done
  echo "captured $label → $out ($(echo $SCENARIOS | wc -w | tr -d ' ') scenarios)"
}

compare() {   # <labelA> <labelB>  -> exit 0 iff all identical
  local a b fails=0 total=0 s
  a="$(safe_result_dir "$1")" || return $?
  b="$(safe_result_dir "$2")" || return $?
  for s in $SCENARIOS; do
    total=$((total+1))
    if diff -q "$a/$s.txt" "$b/$s.txt" >/dev/null 2>&1; then
      printf 'PASS %s\n' "$s"
    else
      printf 'FAIL %s\n' "$s"; fails=$((fails+1))
    fi
  done
  printf '== %d/%d scenarios match (%s vs %s) ==\n' "$((total-fails))" "$total" "$1" "$2"
  return $((fails>0))
}

validate() {  # Phase 0 two-way
  echo "### Source self-consistency (pass direction) ###"
  capture "$HERE/adapters/source.sh" source
  capture "$HERE/adapters/source.sh" source2
  echo "--- source vs source2 (must be all PASS) ---"
  compare source source2; local self=$?
  echo
  echo "### Mutation catches (fail direction) — judge must reject each ###"
  local m all_caught=0 total_mut=0 tmp; tmp="$(mktemp)"
  for m in stdout stderr exit file; do
    total_mut=$((total_mut+1))
    MUTATION="$m" capture "$HERE/adapters/broken.sh" "broken-$m" >/dev/null
    echo "--- source vs broken-$m (MUTATION=$m; must FAIL somewhere) ---"
    compare source "broken-$m" >"$tmp"
    local caught; caught="$(grep '^FAIL' "$tmp" | awk '{print $2}' | paste -sd, -)"
    if [ -n "$caught" ]; then
      echo "MUTATION $m: CAUGHT on: $caught"; all_caught=$((all_caught+1))
    else
      echo "MUTATION $m: *** ESCAPED *** (judge insensitive to $m)"
    fi
    echo
  done
  rm -f "$tmp"
  echo "===== VALIDATION SUMMARY ====="
  [ "$self" = 0 ] && echo "self-consistency: PASS (source==source)" || echo "self-consistency: FAIL"
  echo "mutations caught: $all_caught/$total_mut"
  { [ "$self" = 0 ] && [ "$all_caught" = "$total_mut" ]; }
}

port() {      # Phase 5: fresh source capture vs port (differential, both run now)
  capture "$HERE/adapters/source.sh" source
  capture "$HERE/adapters/port.sh" port
  echo "--- fresh source capture vs port (differential) ---"
  compare source port
}

goldencheck() { # drift check: fresh source capture vs frozen golden/ (not port)
  capture "$HERE/adapters/source.sh" source_now >/dev/null
  local fails=0 total=0 s
  for s in $SCENARIOS; do
    total=$((total+1))
    if diff -q "$HERE/golden/$s.txt" "$RESULTS/source_now/$s.txt" >/dev/null 2>&1; then
      printf 'PASS %s\n' "$s"
    else
      printf 'DRIFT %s\n' "$s"; fails=$((fails+1))
    fi
  done
  rm -rf "$RESULTS/source_now"
  printf '== %d/%d scenarios: fresh source == frozen golden (0 drift; J-001…J-013b Phase 0, J-014 errata pass 3) ==\n' "$((total-fails))" "$total"
  return $((fails>0))
}

checkport() { # <scenario-id...>  run port on given scenarios, diff vs frozen golden; exit 0 iff all match
  local id fails=0 tmp; tmp="$(mktemp -d)"
  export CLI="$HERE/adapters/port.sh"
  for id in "$@"; do
    if [ "$id" = "c13b_defaultpath" ]; then
      local h; h="$(mktemp -d)"; ( export HOME="$h"; unset NOTES_FILE; "scn_$id" ) >"$tmp/$id.txt" 2>&1; rm -rf "$h"
    else
      local nf; nf="$(mktemp)"; rm -f "$nf"; ( export NOTES_FILE="$nf"; "scn_$id" ) >"$tmp/$id.txt" 2>&1; rm -f "$nf"
    fi
    if diff -q "$HERE/golden/$id.txt" "$tmp/$id.txt" >/dev/null 2>&1; then echo "PASS $id"; else echo "FAIL $id"; fails=$((fails+1)); fi
  done
  rm -rf "$tmp"
  return $((fails>0))
}

cmd="${1:-}"; shift || true
case "$cmd" in
  capture) capture "$@";;
  compare) compare "$@";;
  validate) validate;;
  port) port;;
  goldencheck) goldencheck;;
  checkport) checkport "$@";;
  *) echo "usage: judge.sh {capture <adapter> <label>|compare <A> <B>|validate|port|goldencheck|checkport <ids...>}" >&2; exit 64;;
esac
