# Pocket Tasks — observed-only behavior port (Portme dogfood)

A self-contained, stdlib-only reimplementation of a "Pocket Tasks" to-do UI that
was available **only as an observed HTTP service** (`GET /health`, `POST /interact`).
Its internals were never read; behavior was recovered purely by probing the two
authorized endpoints within an approved action vocabulary. This is a disposable
Portme dogfood run.

The exercised UI surface is interaction and DOM-state behavior: focus,
accessibility labels, live-region messages, keyboard actions, export output, and
error semantics. It did **not** exercise a real browser renderer, CSS, screenshots,
pixel output, or visual diff. The source implementation is intentionally not
shipped; the admitted, scanned, redacted observation fixtures are the offline
oracle.

## Run the port
```
python3 src/pocket_tasks.py          # serves http://127.0.0.1:18770
curl -s localhost:18770/health
curl -s -X POST localhost:18770/interact \
  -H 'Content-Type: application/json' \
  -d '{"session":"me","action":{"type":"add","text":"Buy milk"}}'
```

## Public surface
- `GET /health` → `{"ok": true, "version": "pocket-tasks-port-1"}`
- `POST /interact` with `{"session": <id?>, "action": {"type": ...}}`; action types:
  `reset`, `add`(text), `toggle`(index), `delete`(index), `filter`(value all/active/done),
  `shortcut`(key Alt+D/Escape). Response envelope: `{dom:{title,theme,filter,count,empty,
  rows[ariaLabel,checked,text]}, export, focus, liveRegion}`. Errors: 400
  `{"error": <ExceptionClassName>}`; unknown routes 404.

## Verify (offline, no source needed)
```
./verify.sh
```
Runs: stdlib-only check, authorization-bundle digest pin, authorized manifest queue
(2/2 units), differential judge (18/18), two-way mutation sensitivity (6/6), byte-fidelity
guard, and marker scan. `verify.sh` is relocatable and needs neither the observed
source service nor any original dogfood path.

## Audit trail
Everything lives under `.port/` — contract, behavior map, rulebook, gaps/assumptions,
manifest + authorization bundle, the capture/scanner pipeline, differential judge and
its admitted redacted goldens, the named `pocketscan` secret/PII scanner, capture and
deletion receipts, and adversarial review. Raw captures were quarantined **outside**
this repo and deleted (see `.port/receipts/capture-001.md`). The retained run records
18/18 judge scenarios, 6/6 caught mutations, raw-byte fidelity, two review-found
defects and their fixes, a 2/2 authorized queue, and verified quarantine deletion.

Parity is bounded by the recorded scenarios and stated assumptions (see
`.port/contract.md`); this is not an unqualified full-parity claim.
