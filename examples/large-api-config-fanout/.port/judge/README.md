# Differential judge — legacy_adapter port

## Run
    python3 .port/judge/compare.py --mode source   # capture source baseline only
    python3 .port/judge/compare.py --mode diff      # run source+port, assert exact equality
    python3 .port/judge/compare.py --mode diff --target <DIR>  # mutation sensitivity

## Oracle
Rung 3 (differential harness): the readable source at
source/legacy_adapter.py and the port at src/cli.py are
run under identical argv+env; stdout (canonical JSON), stderr, and exit code are
compared byte-for-byte across 43 scenarios (J-01..J-43).

## Environment
CPython 3.14 (macOS). Only PORTME_TIMEOUT_MS is injected; the harness clears it
from the baseline env unless a scenario sets it. Fixtures under fixtures/ are
approved config inputs; their sha256 are recorded in .port/status.md.

## Sensitivity (two-way validation)
Five mutations (results/mutation/) each on a distinct comparator class were
injected into disposable copies and every one was caught:
M1 API-drop-region (18/43), M2 exec off-by-one (40/43), M3 exec retry-500
(42/43), M4 config precedence (42/43), M5 CLI error text (28/43).
Source workspace hash unchanged before/after (see status.md).

## Provenance
Every fixture is a hand-authored approved input (not port-produced). Source
baseline captured by `--mode source` into results/source-baseline.json.
