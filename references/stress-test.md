# Stress-test the rules

Phase 2 makes the Phase 1 artifacts govern real target work before broad implementation. When the rulebook trigger fired, `.port/rulebook.md` is the primary object under stress; when no rulebook exists, stress the applicable map, gaps, contract, and judge instead, and create a rulebook only if the slice surfaces a recurring decision.
Use the production unit packets (`.port/packets/<unit_id>.md`, defined in `references/loops.md`), checks, review roles, and model tiers planned for Phase 3 so the exercise exposes actual pipeline defects. Write the slice's packets now; Phase 2 is where a packet template's gaps surface cheaply.

## Decide whether disposal pays

Disposal depends on how many later units will reuse the slice, not on the mode name.

**Discard the slice** when many untouched units will reuse its rules and conventions. Re-running one pilot after amendments is cheap compared with propagating an unreviewed choice through fan-out.
**Keep the reviewed output** when the slice is a large fraction of the whole port. In that case, deleting and rebuilding it would cost more than the downstream risk it protects.

Record total planned units, estimated slice share, downstream units affected by its rules, and the keep/discard verdict before implementation.
For a kept slice, stress-test in place and close its manifest row only after review, judge evidence, and approved amendments are applied.
For a disposable slice, isolate its outputs and prevent them from closing `.port/manifest.tsv` rows.

## Select the risky vertical slice

Choose a thin slice that crosses the highest-risk semantic gaps and reaches one visible result.
Include only layers the behavior actually uses: entry point, validation, rules, state, side effects, visible output, and judge case as applicable.
Prefer shared conventions over one-off pathology unless the rare path is catastrophic.
Record the unit, risk hypothesis, rules, gap rows, and expected judge cases.

## Isolate a disposable experiment

When the verdict is discard, use scratch paths or an isolated work area.
Snapshot pre-pilot target paths if isolation is impossible.
Keep judge fixtures immutable and `.port/rulebook.md` read-only during the run.
Make manifest completion checks reject pilot paths.

For a kept in-place slice, assign normal exclusive ownership and retain a pre-change receipt. It still cannot bypass the full review or judge merely because it will survive.

If isolation and exact restoration cannot be proved, reclassify the slice as kept-in-place or ask the user for an isolated workspace. Do not call output disposable while it can leak into manifest completion.

## Run the slice

Give the implementer only applicable contract rows, behavior-map rows, rules, gaps, owned paths, and cheap unit check.
Use the implementer tier approved at sizing.
Run the cheap check and applicable judge scenarios.
Capture tokens, elapsed time, reviewer time, rework, tool contention, and referee runtime; these measurements replace qualitative sizing estimates.
Mark unresolved sites with `TODO(port): <reason>`.

Reviewers use separate read-only contexts and the approved reviewer tier.
They attack rules versus output and rules versus contract, citing a rule, source site, trace, gap row, or contract row.
Classify findings as rule defect, missing rule, gap omission, map error, implementer error, judge defect, or acceptable choice.
Use a separate tiebreaker and default unsupported disputes to not-confirmed.

## Use the dual-translation bakeoff selectively

Only structure-preserving migrations with line-comparable outputs benefit from a dual-translation bakeoff.
One translator follows the rulebook; another uses source behavior and target idioms without it.
The native-idiom translator's workspace contains only the pinned source inputs and target toolchain metadata: no `.port/`, rulebook, inventory, or any mention that a rule-following translation exists. Exposure invalidates the baseline. Keep output paths isolated.
A diff inspector classifies material differences as rule-following correct, native-idiom correct, both acceptable, or both wrong.
Convert repeated or high-risk differences into proposed rules.

Do not use line-by-line comparison for feature ports or redesigns. Their oracle is observable behavior and declared invariants.

For a high-risk redesign, optionally rehearse the whole run in a disposable workspace: execute the production packets, ownership, review, referee, merge, and recovery path across all units, retain only evidence and rule or map amendments, then restore or discard the workspace before the real run. Use this when cross-unit interactions are the primary unknown and the rehearsal cost is lower than rollback risk.

## Stress redesigns and feature ports

Assign attack lenses that match the surface: state, errors, lifecycle, security, concurrency, data, UI interaction, accessibility, and integration boundaries.
Trace a scenario backward from visible result to entry point.
Exercise empty, error, retry, cancellation, and permission-denied paths where relevant.
Compare behavior and invariants, not internal structure.

## Harvest amendments

After the run, place proposed rule changes in the pending section of `.port/rulebook.md`.
Add discovered sites to `.port/gaps.tsv` and correct map or manifest ownership errors.
Review judge defects separately from port findings.
If a judge change needs a new sensitivity mutation, follow `references/judge.md`: mutate only a disposable copy/worktree/snapshot, discard it, and verify the original source and target diff/hash state is unchanged.
List affected future units for each amendment.
The user approves material rule or contract changes at the Phase 2 gate. A material amendment changes contracted behavior, an equivalence standard, safety or data handling, unit ownership or dependency order, judge coverage or normalization, a shared translation rule, or expected cost or blast radius enough to change the approved plan.

For a kept slice, apply approved amendments to it through the normal fix and review loop before marking it done.
For a disposable slice, amendments, not implementation, are the reusable output.

## Dispose or retain according to the verdict

For disposal, remove pilot target output after evidence capture, restore overwritten paths from the recorded state, and retain only reports, raw judge results, cost observations, and approved artifact amendments under `.port/`.
Verify that no stale pilot file can satisfy manifest completion.

For retention, list the reviewed target paths, final judge result, approved amendments applied, and manifest receipt.
Do not describe kept output as disposable or force a rebuild solely to satisfy mode convention.

## Choose Phase 3 parameters

Set batch size from observed implementer time, reviewer time, conflict rate, and referee capacity.
Reduce fan-out when shared-resource edits or rule defects were frequent.
Increase reviewer strength before implementer strength when interpretation errors replicated.
Forecast Phase 3 with the measured per-unit range, review multiplier, fixed overhead, rate limits, and serialized-referee time.
Append numeric forecasts and actuals to `.port/cost-log.tsv` now that measured evidence exists.

## Present the Phase 2 gate

Report slice share, the keep-or-discard decision, judge results, mutation status if the judge changed, findings by class, amendments, kept or discarded paths, measured cost, and proposed batch size. Include a checkbox proving the recorded keep/discard verdict was followed and no disposable output can close a manifest row.
Standard and Large-scale stop for explicit approval before Phase 3.
Quick records the evidence and continues without an intermediate gate.

## By mode

**Quick: stress in place when needed.** If one risky ambiguity warrants Phase 2 work, test the actual unit and keep reviewed output; no Phase 2 stop occurs.
**Standard: keep or discard by reuse.** Keep a slice that is a large share of the port; discard it only when enough downstream units benefit from regeneration.
**Large-scale: protect fan-out.** A disposable production-topology slice is usually worthwhile, but retention remains valid when the slice dominates the port. Add adversarial review, measurement, and a bakeoff when structure-preserving.
