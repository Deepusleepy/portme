# Judge: Pocket Tasks observed-only differential harness

## Oracle rungs (per references/judge.md)
- **Rung 6 (source-backed golden scenarios)** for behavior: raw source observations captured
  through the two authorized public surfaces, scanned, redacted, and admitted as goldens.
- **Rung 4 (executable behavior table)** in spirit: `scenarios.tsv` is the static behavior
  table (action → observable envelope), compared mechanically.
- **Rung 3 (differential)** at replay time: `run_port.py` drives the port through its own
  public surface with the identical logical action sequences.

## Files
- `_scenarios.py`: single source of truth for scenario action sequences (17 scenarios).
- `_driver.py`: HTTP driver over GET /health + POST /interact; `normalize()` =
  pocketscan redaction of all string leaves + mask of `health.version`.
- `run_source.py`: ONLY authorized source driver; writes RAW observations to a caller dir
  (must be the outside-repo quarantine). Never writes to `.port/` directly.
- `capture.py`: full capture pipeline: quarantine(0700, outside repo, non-symlink) →
  raw capture → inventory (reject symlink/non-regular) → pocketscan scan (receipt) →
  redact + clean rescan → copy-not-link admission into `fixtures/<id>/observation.json` →
  admitted-copy verification → quarantine deletion + path-absent check → `receipts/capture-001.md`.
- `run_port.py`: drives the port (ephemeral loopback instance), normalizes, writes
  `results/port-obs/<id>.json`.
- `compare.py`: structural diff of normalized golden vs normalized port; per-scenario
  PASS/FAIL + summary failure queue. Exit 0 iff all pass.
- `mutation_test.py`,  two-way sensitivity: 6 mutation classes on disposable source copies;
  judge must FAIL each; records source-file hash unchanged.
- `fixtures/<id>/observation.json`: admitted REDACTED source goldens (the oracle).
- `results/`: port observations + phase evidence.

## Run
```
# behavior judge (starts an ephemeral port instance itself)
python3 .port/judge/run_port.py .port/judge/results/port-obs
python3 .port/judge/compare.py            # -> pass=17 fail=0

# two-way mutation sensitivity
python3 .port/judge/mutation_test.py      # -> all_caught=True (6/6)

# re-capture goldens from a running source (authorized matrix only)
python3 .port/judge/capture.py http://127.0.0.1:18765
```

## Environment
- Python 3 stdlib only. Source fixture observed at `http://127.0.0.1:18765` (health
  `ui-observed-1`) on 2026-07-23. Port default `PT_PORT=18770`; adapters use an ephemeral port.

## Normalization justification
Only two normalizations, each contract-cited:
1. `pocketscan` redaction of every string leaf, privacy-preserving judge; applied
   symmetrically so no secret/PII sits in `.port/` and the J-PII scenario compares equal.
   Idempotent on already-redacted goldens.
2. `health.version` masked (contract S-000 / divergence D-001): source-identity field.
Array order is preserved (task order is contractual). No other field is normalized.
