#!/usr/bin/env bash
# Port adapter: run the locally built TypeScript CLI. Uses $NOTES_FILE / $HOME.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$HERE/../../.." && pwd -P)"
DIST="${PORTME_DIST:-$ROOT/dist/cli.js}"
exec node "$DIST" "$@"
