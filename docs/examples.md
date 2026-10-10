# Recorded examples

These are real runs that were kept. Each one says what it actually exercised. Read [VALIDATION.md](../VALIDATION.md) before treating any of them as proof of a path it did not run.

Together they cover Quick mode, a Standard language port, observed UI behavior (interaction and page state, not pixels), and a small API/config exercise that used the Large-scale machinery because someone asked for it. Production-scale fan-out, and real isolation or security boundaries, are still unproven on purpose.

## Quick: "did you mean"

[`examples/quick-did-you-mean/`](../examples/quick-did-you-mean/) ports Click's "did you mean" suggestion into an argparse CLI. It records the scope confirmation, the size score, the checklist, a negative probe, the gate log, and the one-file diff. The source and target repos are not shipped, so you cannot replay it from a clean checkout.

## Standard: Python notes CLI to TypeScript

[`examples/standard-notes-py-to-ts/`](../examples/standard-notes-py-to-ts/) is a full Standard-mode port. It is byte-identical on 15 exact surfaces inside the approved contract, with two bounded approved differences. It includes a differential judge that was checked both ways (it passes on the real source and fails on deliberately broken behavior), a frozen 5-unit manifest, 12 rules, 13 closed gaps, and a review that found two real bugs the saved scenarios missed.

## Standard: observed to-do UI

[`examples/standard-observed-ui/`](../examples/standard-observed-ui/) is a Standard run whose source is intentionally missing. The redacted fixtures are the offline oracle. It keeps the capture, scanner, and deletion trail, an 18/18 differential judge, 6/6 caught mutations, a raw-byte check, and two bugs found in review and then fixed. The UI surface that was exercised is interaction and DOM state: focus, accessibility text, live regions, keyboard, export, and error behavior. It is not browser rendering, CSS, screenshots, or a visual diff.

## Large-scale machinery on a tiny API/config port

[`examples/large-api-config-fanout/`](../examples/large-api-config-fanout/) ports a readable API and config surface. Large-scale mode was a requested override on a 52-line fixture, not a judgment that the fixture needed it. The first run had no way to launch workers, so it did the units one at a time and wrote that down. A later addendum ran two real overlapping workers on disjoint paths (`U-CONFIG` and `U-EXEC`), with exit-126 guardrail receipts, a serialized check that failed (`0003`) and then passed after a fix (`0004`), queue 4/4, tests 35/35, and judge 43/43. The guardrail is a stand-in that shows a deny firing and a check being routed. It is not Claude settings, and it is not a security boundary.
