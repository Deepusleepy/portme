#!/usr/bin/env bash
# Source adapter: run the shipped Python oracle. Uses $NOTES_FILE / $HOME.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
ROOT="$(cd "$HERE/../../.." && pwd -P)"
SRC="${PORTME_SOURCE_DIR:-$ROOT/source-python}"
exec env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$SRC" python3 -m notes_cli.cli "$@"
