# Pocket Tasks: observed-only behavior port

A stdlib-only reimplementation of a "Pocket Tasks" to-do UI that existed only as an HTTP service (`GET /health`, `POST /interact`). Its internals were never read. Behavior was recovered by probing those two endpoints inside an approved action list. This is a disposable Portme practice run.

The UI surface that was exercised is interaction and DOM state: focus, accessibility labels, live-region messages, keyboard actions, export output, and error behavior. It did not exercise a real browser, CSS, screenshots, pixels, or a visual diff. The source implementation is intentionally not shipped. The admitted, scanned, redacted fixtures are the offline oracle.

## Run the port

```
python3 src/pocket_tasks.py          # serves http://127.0.0.1:18770
curl -s localhost:18770/health
curl -s -X POST localhost:18770/interact \
  -H 'Content-Type: application/json' \
  -d '{"session":"me","action":{"type":"add","text":"Buy milk"}}'
```

## Public surface

- `GET /health` returns `{"ok": true, "version": "pocket-tasks-port-1"}`
- `POST /interact` takes `{"session": <id?>, "action": {"type": ...}}`. Action types: `reset`, `add` (text), `toggle` (index), `delete` (index), `filter` (all, active, or done), `shortcut` (Alt+D or Escape). Response: `{dom:{title,theme,filter,count,empty,rows[ariaLabel,checked,text]}, export, focus, liveRegion}`. Errors are 400 `{"error": <ExceptionClassName>}`. Unknown routes are 404.

## Verify (offline, no source needed)

```
./verify.sh
```

That runs the stdlib-only check, the authorization-bundle digest pin, the authorized manifest queue (2/2), the differential judge (18/18), mutation sensitivity (6/6), the byte-fidelity guard, and a marker scan. `verify.sh` is relocatable. It does not need the observed source service or the original run paths.

## Audit trail

`.port/` holds the contract, behavior map, rulebook, gaps, manifest and authorization bundle, the capture and scanner pipeline, the differential judge and its redacted fixtures, the `pocketscan` secret scanner, capture and deletion receipts, and the adversarial review. Raw captures were quarantined outside this repo and deleted (see `.port/receipts/capture-001.md`). The retained records show 18/18 judge scenarios, 6/6 caught mutations, raw-byte fidelity, two review-found defects and their fixes, a 2/2 authorized queue, and verified quarantine deletion.

Parity is limited to the recorded scenarios and stated assumptions (see `.port/contract.md`). This is not a claim of full parity.
