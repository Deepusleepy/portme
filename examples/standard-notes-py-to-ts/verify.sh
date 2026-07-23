#!/usr/bin/env bash
# Reproduce the published example without mutating this directory. The build,
# captures, and queue checks all run in a disposable copy below /tmp.
set -eu

VERIFY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
VERIFY_WORK="$(mktemp -d /tmp/portme-standard-verify.XXXXXX)"
VERIFY_COPY="$VERIFY_WORK/example"
# Publication-bundle integrity pin. This constant records the exact manifest
# plus declared check-input names and bytes consciously reviewed for this
# explicitly invoked demo; it is not migration approval and cannot replace a
# live Portme run's conversation-authorized bundle digest.
EXPECTED_AUTHORIZATION_BUNDLE_SHA256="b5f600b99716a82bf87a92076a678a4cea8013dee11861ff0b66b2f4fe79b95b"

cleanup() {
  case "$VERIFY_WORK" in
    /tmp/portme-standard-verify.*) rm -rf -- "$VERIFY_WORK" ;;
    *) echo "refusing to clean unexpected verification path: $VERIFY_WORK" >&2; return 1 ;;
  esac
}
trap cleanup EXIT HUP INT TERM

mkdir -p "$VERIFY_COPY"
( cd "$VERIFY_ROOT" && tar -cf - --exclude='./node_modules' --exclude='./dist' . ) |
  ( cd "$VERIFY_COPY" && tar -xf - )
VERIFY_COPY_REAL="$(cd "$VERIFY_COPY" && pwd -P)"
cd "$VERIFY_COPY"

echo "== publication authorization-bundle integrity pin =="
current_authorization_bundle_sha256="$(python3 scripts/port_queue.py digest --manifest port/manifest.tsv)"
if [ "$current_authorization_bundle_sha256" != "$EXPECTED_AUTHORIZATION_BUNDLE_SHA256" ]; then
  echo "publication manifest/check-input authorization bundle SHA-256 mismatch" >&2
  echo "expected: $EXPECTED_AUTHORIZATION_BUNDLE_SHA256" >&2
  echo "current:  $current_authorization_bundle_sha256" >&2
  echo "review the byte change, then consciously update the pin and publication receipt" >&2
  exit 1
fi

echo "== shipped Python source digest =="
( cd source-python && shasum -a 256 -c SHA256SUMS )

echo "== contract/manifest/scenario joins =="
python3 port/evidence/contract_manifest_join.py

echo "== deterministic install and build =="
npm ci --ignore-scripts
npm run build

echo "== judge two-way validation =="
bash port/judge/judge.sh validate

echo "== fresh source-to-port differential =="
bash port/judge/judge.sh port

echo "== shipped-source golden drift check =="
bash port/judge/judge.sh goldencheck

echo "== differential stress =="
bash port/judge/stress.sh

echo "== hardened result-label negative probe =="
mkdir -p port/judge/traversal-sentinel
printf 'must survive\n' >port/judge/traversal-sentinel/keep.txt
set +e
bash port/judge/judge.sh capture port/judge/adapters/source.sh '../traversal-sentinel' \
  >"$VERIFY_WORK/capture-label-negative.txt" 2>&1
capture_label_rc=$?
bash port/judge/judge.sh compare '../traversal-sentinel' source \
  >"$VERIFY_WORK/compare-label-negative.txt" 2>&1
compare_label_rc=$?
set -e
if [ "$capture_label_rc" -ne 64 ] ||
   [ "$compare_label_rc" -ne 64 ] ||
   [ ! -f port/judge/traversal-sentinel/keep.txt ] ||
   ! grep -q 'result label must match' "$VERIFY_WORK/capture-label-negative.txt" ||
   ! grep -q 'result label must match' "$VERIFY_WORK/compare-label-negative.txt"; then
  echo "unsafe label was not rejected cleanly" >&2
  exit 1
fi
echo "PASS capture/compare traversal labels rejected with exit 64; sentinel retained"

echo "== ESM entry through logical, physical, and symlink paths =="
probe_entry() {
  local cli_path="$1" probe_name="$2" notes output
  notes="$VERIFY_WORK/$probe_name.notes"
  output="$(NOTES_FILE="$notes" node "$cli_path" add "$probe_name")"
  [ "$output" = 'Added note 1.' ] || {
    echo "entry probe failed for $probe_name: $output" >&2
    return 1
  }
  echo "PASS $probe_name"
}
probe_entry "$VERIFY_COPY/dist/cli.js" logical-tmp
probe_entry "$VERIFY_COPY_REAL/dist/cli.js" physical-tmp
ln -s "$VERIFY_COPY_REAL" "$VERIFY_WORK/example-link"
probe_entry "$VERIFY_WORK/example-link/dist/cli.js" symlink-component

echo "== publication-pinned queue over port/manifest.tsv =="
python3 scripts/port_queue.py verify \
  --manifest port/manifest.tsv \
  --run-checks \
  --authorize-manifest "$EXPECTED_AUTHORIZATION_BUNDLE_SHA256"

echo "== VERIFY PASS: self-contained 15-scenario suite =="
