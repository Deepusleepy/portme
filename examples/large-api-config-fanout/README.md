# Legacy adapter — API/config/fan-out dogfood

This self-contained example ports the readable 52-line
`source/legacy_adapter.py` CLI into a zero-dependency v2 API/config architecture
under `src/`. It intentionally used Portme's Large-scale mode only because the
user requested that override to exercise fan-out, API-version, config-system,
guardrail, queue, and serialized-referee paths on a tiny fixture. It is evidence
of those mechanics, not a recommendation to use Large-scale mode for work this
small.

## Reproduce

```sh
./verify.sh
```

`verify.sh` first makes a disposable clean copy, so the published example is not
mutated. In that copy it verifies the pinned current authorization bundle, runs
the authorized queue (4/4), all 35 unittests, the 43/43 differential judge
against the bundled source, a newly serialized full referee, and cryptographic
`last` verification. It also checks the three deny receipts, worker receipts and
overlapping timestamps, disjoint ownership, reviewer summaries, and immutable
historical referee failure `0003` followed by success `0004`.

## Honest run history

The original orchestrator lacked a worker-spawn transport and recorded its
Phase-3 implementation/review as a serial degradation. That history remains in
`.port/status.md`. A later parent addendum closed only the concurrency gap with
two genuinely overlapping workers:

- U-EXEC: 2026-07-23 05:09:02–05:09:27Z, owned `src/execute.py`, narrow 9/9.
- U-CONFIG: 2026-07-23 05:09:04–05:09:31Z, owned `src/config.py`, narrow 11/11.
- Ownership was disjoint. Both worker guardrails fired with exit 126.
- Serialized integration referee `0003` failed because U-CONFIG's narrow leaf
  test missed its real positional consumer and default environment behavior.
- The same owner fixed only `src/config.py`; queue 4/4, referee `0004` 35/35,
  and the differential judge 43/43 then passed.

The parent-retained independent reviewer summaries are in `.port/reviews/`.
Both reviewers marked U-CONFIG and U-EXEC PASS; they scored fan-out mechanics
6/10 and 8/10. Those summaries are evidence, not approval and not verbatim user
messages. The retained pre-fan-out baselines are last-known-good files, not the
broken intermediate; immutable `0003` plus the worker repair receipt preserve
the failure/recovery trail.

## Guardrail boundary

`worker-expensive-referee` is a harness stand-in used to prove that a deny fires
and work routes to the serialized referee. It is not Claude settings, a security
boundary, credential isolation, or container isolation. This example tests deny
firing and referee routing; a worker could still invoke another path without
genuine process policy. Do not cite it as proof of containment.
