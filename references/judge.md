# Build the judge first

Build the Phase 0 judge before implementation and derive its cases from `.port/contract.md`.
Keep judge code, admitted fixtures, and results under `.port/judge/`; readable/runnable-source observations may also live there. For observed-only sources, raw captures land only in the outside-repository quarantine from `references/no-source.md`, and `.port/` receives scanned redacted copies. A fresh session can reconstruct the oracle from disk but must re-establish source provenance, gate authority, and command authorization before executing it.
Keep the source runnable through Phase 5 so each behavior failure can be classified on both sides.

## Choose the strongest available oracle

Climb down only when a stronger rung cannot cover the public surface.

1. Reuse existing tests that exercise public behavior.
2. Add contract or schema tests for protocol guarantees.
3. Build a differential harness that runs source and port side by side.
4. Extract and compare an executable static behavior table.
5. Record and replay authorized traffic or sessions.
6. Build source-backed golden scenarios.
7. Add property or metamorphic checks for invariant families.
8. Use a human acceptance script when no automated comparator is proportionate or capable.

Mix rungs across surfaces. Prefer public entry points over source internals, and record the selected rung for every contract surface.
An uncovered surface is a proposed coverage limit, not an implied pass. Record its reason and affected contract IDs and obtain user approval; unapproved limits block done. Coverage limits cannot widen after implementation begins, and a failed scenario can never be reclassified as a limit.

## Use a behavior table for UI and feature ports

A static behavior table is a valid executable judge rung when behavior is registered or declarative.

**Extract the source table.** Read the source config or code registry and emit stable rows such as `context + keybinding → action`, `route → handler`, `command → effect`, `event → state transition`, or spreadsheet `cell/formula → computed value`.
**Extract the port table.** Use an independent adapter that emits the same columns and normalization.
**Compare mechanically.** Sort only fields declared unordered, then assert missing, extra, and changed rows are empty.
**Keep receipts.** Store both raw tables and the diff under `.port/judge/results/`, with the extraction command in `.port/judge/README.md`.
**Test sensitivity.** Remove one binding, remap one action, and add one unintended row; the table judge must reject each mutation in Standard and Large-scale.

This rung is lightweight and useful even when rendering or end-to-end UI automation is unavailable. It grades registered behavior, not appearance or runtime side effects, so pair it with focused interaction checks where those matter.

## Design the harness

Isolate source and port environments. Feed identical inputs, clocks, seeds, locales, and initial state where practical.
Capture outputs, errors, exit status, state changes, focus, accessibility state, and named side effects according to the contract.
Reset mutable state between scenarios and retain raw observations before normalization.
Emit per-scenario machine-readable verdicts plus summary counts that can become a failure queue.

Use this layout:

```text
.port/judge/
  README.md          # run command, tool versions, environment
  scenarios.tsv      # full schema in templates/judge-scenarios.tsv
  run-source.*       # source adapter
  run-port.*         # target adapter
  compare.*          # normalization and verdict logic
  fixtures/          # approved inputs and recordings
  results/           # raw and normalized observations
```

Generated results must not overwrite approved fixtures. For observed-only evidence, raw capture never lands here first; follow the outside-repository quarantine, scanning, redacted-copy, and deletion flow in `references/no-source.md`.
Every fixture, including one produced from readable source, records its producing command, pinned source revision, scenario ID, environment, and timestamp. Judge review verifies provenance before the Phase 0 gate; port-produced output cannot become a source golden.

## Price flaky and manual referees honestly

Treat visual diff as a flaky, cost-2 referee at sizing. It requires controlled fonts, viewport, animation, rendering engine, and thresholds, and it cannot establish interaction or state parity alone.
Use it only for contract surfaces where appearance is observable and a cheaper stable comparator cannot cover the requirement.
Record retry policy and false-positive handling before relying on its verdict.

Outside Quick, a human-acceptance rung is allowed for a surface when no automated comparator can meet the mutation bar.
At the Phase 0 gate, document the affected surface, why automation failed, the exact acceptance script, named evaluator, evidence to retain, and the resulting coverage limit.
Human acceptance cannot silently upgrade a bounded claim to full parity.

## Validate both directions

For **Standard** and **Large-scale**, name and run the judge plus applicable source baseline suite in Phase 0. Freeze their cases, commands, fixtures, and allowed bounded pre-existing failures at that gate; they cannot be narrowed after a failure. Enumerated pre-existing failures require user approval.
Deliberately break one behavior per comparator class and require the judge to fail. Apply every mutation in a disposable copy, worktree, or filesystem snapshot created from pinned inputs, never in a dirty source or target workspace. Record pre-mutation source and target diff/hash state, discard the disposable area afterward, then mechanically verify the original source and target diff/hash state is unchanged. Restoration by memory or an unverified reverse edit is not evidence.
Record mutation ID, disposable location/snapshot identity, broken behavior, expected caught cases, actual caught cases, disposal result, and before/after source and target diff/hash receipts.

Useful mutations include changed values, removed or reordered items, altered error semantics, suppressed side effects, exceeded budgets, broken focus or accessible names, and normalization inputs that preserve meaning. A reviewer chooses mutations; when no separate reviewer is proportionate, require at least one mutation for every high-risk contract surface rather than letting the judge author select the easiest cases.
Reject or repair a comparator when a planned mutation escapes. Do not weaken the contract to rescue the judge.

For **Quick**, enumerate one checklist item for every included surface, with setup, action, expected observable result, and evidence to retain. The user approves that checklist at the plan gate. A missing high-risk surface upgrades the port to Standard. Execute every item against the result and retain observed evidence; two-way mutation validation is optional, not a gate requirement.

## Debug the comparator

When many unrelated cases diverge together, inspect the referee before the port.
Compare raw observations, reduce to one minimal scenario, and test normalizers with equivalent and non-equivalent pairs.

Normalize line endings, whitespace, object-key order, locale, Unicode, paths, case, timestamps, IDs, or random values only when the contract explicitly permits it.
Preserve array order unless declared unordered. Represent non-JSON numeric values explicitly, and compare binary data by bytes or digest.
Over-normalization hides portability defects; every rule needs a contract citation.

For an **exact** surface whose contracted behavior includes raw bytes, parsed or
structural comparison is only one layer. Also retain and compare raw bytes or a
cryptographic digest across encoding, whitespace, ordering, line endings, and
protocol/file framing. Phase-0 sensitivity testing must include a byte-only
mutation when such a surface exists, for example, escaped UTF-8, changed newline,
or equivalent JSON with different key/space bytes, and the raw-byte referee must
catch it. Do not add byte checks to normalized or invariant surfaces unless the
contract makes bytes observable.

## Protect grader independence

Review judge changes separately from port changes. In Standard and Large-scale, use a reviewer who did not implement the affected port behavior.
Every judge change cites a contract row and, when automated, includes mutation evidence.
Never skip, delete, or relax a failing case to reduce the queue. Approved product changes begin in the contract.

## Present the Phase 0 gate

Report oracle rungs, contract coverage, baseline pass counts, mutation catches where required, normalizations, runtime, cost, human checks, and all coverage limits.
Store commands and results under `.port/judge/`.
In **Standard** and **Large-scale**, stop; Phase 1 starts only on explicit user continuation.
In **Quick**, record the evidence and continue through later phases without stopping.

## By mode

**Quick: acceptance-checklist judge.** The checklist is approved at the plan gate and executed at the result gate. No mandatory two-way mutation validation and no intermediate Phase 0 stop.
**Standard: automated high-risk coverage.** Require mutation-validated automation where feasible; a documented human-acceptance rung may cover a surface that cannot meet that bar.
**Large-scale: shardable independent judge.** Require machine-readable results, separate judge review, mutation validation, and a serialized runner when the referee is expensive.
