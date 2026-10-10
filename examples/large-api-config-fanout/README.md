# Legacy adapter: API and config fan-out practice run

This example ports the readable 52-line `source/legacy_adapter.py` CLI into a zero-dependency v2 API and config layout under `src/`. Large-scale mode was used only because the user asked for that override, to exercise fan-out, an API-version move, a config system, guardrails, the queue, and the serialized referee on a tiny fixture. It is evidence of those mechanics. It is not a recommendation to use Large-scale mode for work this small.

## Reproduce

```sh
./verify.sh
```

`verify.sh` first makes a disposable clean copy, so the published example is not mutated. Git stores only executable versus non-executable file modes. It does not preserve the historical results' original `0444` files and `0555` directories. The verifier accepts only those original modes or Git's normalized `0644`/`0755` checkout modes, rebuilds the read-only modes in the disposable copy, and then checks the result cryptographically. It checks the pinned authorization bundle, runs the authorized queue (4/4), all 35 unit tests, the 43/43 differential judge against the bundled source, a newly serialized full referee, and cryptographic `last` verification. It also checks the three deny receipts, worker receipts and overlapping timestamps, disjoint ownership, reviewer summaries, and the immutable referee failure `0003` followed by success `0004`.

## What the run actually did

The first orchestrator had no way to launch workers, so Phase 3 ran one unit at a time. That history is still in `.port/status.md`. A later parent addendum closed only the concurrency gap with two overlapping workers:

- U-EXEC: 2026-07-23 05:09:02–05:09:27Z, owned `src/execute.py`, narrow 9/9.
- U-CONFIG: 2026-07-23 05:09:04–05:09:31Z, owned `src/config.py`, narrow 11/11.
- Ownership was disjoint. Both worker guardrails fired with exit 126.
- Serialized integration referee `0003` failed because U-CONFIG's narrow leaf test missed the real positional caller and the default environment.
- The same owner fixed only `src/config.py`. Queue 4/4, referee `0004` 35/35, and the differential judge 43/43 then passed.

Independent reviewer summaries are in `.port/reviews/`. Both marked U-CONFIG and U-EXEC as pass. They scored the fan-out mechanics 6/10 and 8/10. Those summaries are evidence. They are not approval, and they are not verbatim user messages. The retained pre-fan-out baselines are last-known-good files, not the broken intermediate. Immutable `0003` plus the worker repair receipt keep the failure and the fix.

## Guardrail boundary

`worker-expensive-referee` is a stand-in used to prove that a deny fires and work routes to the serialized referee. It is not Claude settings, a security boundary, credential isolation, or container isolation. This example tests deny firing and referee routing. A worker could still invoke another path without a real process policy. Do not cite it as proof of containment.
