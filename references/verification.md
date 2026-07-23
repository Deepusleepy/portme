# Verify mechanically, then match behavior

Phase 4 — Mechanical checks and Phase 5 — Run and match are separate gates in Standard and Large-scale unless every Phase 4 referee is seconds-cheap.
Keep source and port environments available through Phase 5 for two-sided classification.
Quick runs applicable checks and its acceptance checklist without intermediate stops, then presents one result gate.

## Build the referee stack

Name each referee’s command, runtime, owner, inputs, outputs, pass condition, and contract coverage.
Measure a representative run before placement.

| Port type | Mechanical referees | Behavior referees |
|---|---|---|
| Language | compiler, typechecker, linter, package graph, build | portable public tests, differential harness |
| Framework | build, typecheck, route/schema validation | render tests, lifecycle and navigation scenarios |
| API version | schema validator, generated-client check | contract tests, recorded request replay |
| UI | build, view-hierarchy/DOM and accessibility-tree snapshots | behavior-table diff, interaction traces, visual diff, keyboard flows, navigation/back-stack, permission prompts; platform idiom may be an approved divergence |
| Config | parser, schema validator, dry-run | normalized plan diff, error and default scenarios |
| Data behavior | schema checks, migration dry-run | invariants, checksums, reconciliation, side-effect diff |
| Graphics | shader/compiler validation, asset and scene schema checks | pixel or perceptual diff, geometry bounds, frame invariants, interaction traces |

Combine complementary referees and tie each one to contract rows or gap classes.
Security and data-loss checks stay strict even when the source is defective; harmful parity needs an approved divergence.

## Guard expensive-referee placement

Use active-harness denies—for example, Claude Code permission denies in `.claude/settings.json`—to reduce accidental calls to minutes-expensive, rate-limited, stateful, or workspace-wide referees. Cover direct commands plus known wrappers, aliases, task runners, absolute executable paths, and alternate working directories. Prompt rules alone are weak, but denies are still guardrails rather than a security boundary; they do not make hostile execution safe or invocation impossible. Use separate credentials and container/process isolation when containment matters.

Before any Phase 3 fan-out, run a live preflight from a worker-equivalent context for every named expensive-referee class and retain each denial receipt.
Also prove the authorized serialized runner can invoke the referee.
Try direct commands and obvious indirect or alternate paths through scripts and task runners; a new wrapper is a coverage gap, not proof of containment. Record configuration path and digest, denied command classes, test invocations, observed results, runner path, timestamp, remaining bypasses, and raw receipt paths in `.port/status.md`. Use the receipt example in `references/execution-trust.md`.
Missing, stale, obviously bypassable, or untested guardrails block the fan-out gate unless genuine isolation independently contains the operation.

If a deny fires during implementation or fixing, flag the event and send the pending check to the serialized runner.
The deny firing is the design working. Never weaken it, remove it, disguise the command, or route around it.

## Price and place referees

Seconds-cheap deterministic checks belong inside each Phase 3 unit loop.
When every mechanical referee is cheap and isolated, dissolve Phase 4 into Phase 3.
One serialized runner owns each expensive shared referee and runs only on stable batches — `scripts/referee_runner.py` (in this skill) provides the transport: an exclusive lock with stale takeover, a timeout, and numbered immutable result directories under `.port/referee/`. Published result files are mode `0444` and result directories are `0555`; `referee_runner.py last` cryptographically verifies the complete file set, hashes, modes, completion marker, and consistent exit metadata before reporting the latest result. Workers read those verified results instead of invoking the referee themselves.
Fixers may run narrow cheap checks that cannot mutate shared state.
Record measured runtime, placement, and live-deny status in `.port/status.md`. Before the runner or any queue action executes a manifest check, verify the current manifest/check-input authorization bundle SHA-256 against the conversation-authorized digest and pass both `--run-checks` and the explicit approved digest as described in `references/execution-trust.md`. The bundle binds check-control bytes but does not isolate hostile target execution; use a sandbox when containment matters.

## Phase 4 — Mechanical checks

Run one full survey over stable Phase 3 output and capture raw output plus tool versions.
Parse errors into a machine-readable queue grouped by unit and root cause.
Separate root failures from downstream cascades and repair shared roots before dependents.
Give fixers exclusive paths, error IDs, and applicable rule or gap rows.
Behavioral or architectural fixes receive adversarial review.

Rerun the serialized survey after a stable fixer batch, not on partial trees.
Repeat until the mechanical error queue is empty.
On a third recurrence, use the mid-phase exception gate in `references/loops.md`: amend shared policy only with evidence of a shared defect, otherwise apply a localized reviewed fix or user-approved tool/environment exception.
Never delete, disable, or weaken a check to reach zero.

## Present the Phase 4 gate

Report commands, runtimes, survey rounds, initial and final error counts, root-cause groups, regenerated units, guardrail preflight receipt, and cost.
Name checks dissolved into Phase 3 and update `.port/status.md` with the Phase 5 forecast.
Standard and Large-scale stop for explicit continuation.
Quick records applicable evidence and proceeds directly to Phase 5.

## Phase 5 — Run and match

Start with the smallest smoke path for each entry-point class.
Capture crash signature, environment, input, and first failing boundary; group crashes by root cause.
Fix bounded root causes, rerun affected smoke sets, and send a third recurrence through the mid-phase exception gate so only an evidenced shared defect amends shared policy.

After smoke passes, run the approved Phase 0 judge with its exact fixtures, normalizers, seeds, and environment.
Capture raw source and port observations.
For every port failure, run the same case against the source and classify it as introduced failure, inherited failure, approved divergence, environment failure, or judge defect.
Broad unrelated failures trigger referee debugging first.
Review judge changes separately, and never weaken or delete a case to shrink the queue.

The applicable source baseline suite was named and frozen at Phase 0, including commands, cases, and any bounded enumerated pre-existing failures approved by the user. It cannot be narrowed after failures appear. For observed-only sources, approved recorded fixtures replace the runnable-source baseline; validate their provenance and ingest them without inventing a source rerun.

Assign one fixer per independent introduced root cause. Cite contract rows and rerun affected cases.
Use the serialized full-judge runner when replay or environments are expensive.
After local cases pass, run the complete judge to expose cross-surface regressions.

## Document the explicit done gate

**Port result.** The judge has no unresolved outcome: contracted scenarios pass or are recorded as approved divergences, explicitly accepted inherited failures, or user-approved coverage limits with reason and affected contract IDs. Limits cannot widen after implementation begins, and failed scenarios never become limits.
**Introduced failures.** The count is zero.
**Inherited failures.** Every inherited failure is classified, linked to the same source case, counted, and explicitly accepted by the user. “Inherited” requires the failure mode to match in type, outputs, and side effects; the accepted count may be greater than zero.
**Source baseline.** Separately, rerun the frozen approved source baseline suite and require no unapproved source failures. Bounded, enumerated pre-existing failures remain visible and require their recorded approval.
**Non-functional behavior.** Every applicable referee meets its contract budget.
**Coverage.** Approved divergences and bounded or skipped coverage are listed separately from passes.
**Tool/environment exceptions.** User-approved irreducible exceptions are listed and counted separately with affected scenarios; they are never passes.

Do not convert inherited failures into passes or require their count to be zero. Acceptance records ownership of known source behavior; it does not erase the count.

Use this status block:

```markdown
## Phase 5 — Run and match
- Smoke: <passed>/<total>; crashes by root cause: <count>
- Port judge: <passed>/<total>; introduced failures: 0
- Source baseline suite: <passed>/<total>; approved pre-existing failures: <count and IDs>; unapproved: 0
- Inherited failures: <count>; classified: <count>; explicitly accepted: <count>; IDs: <list>
- Approved divergences: <count and IDs>
- Non-functional referees: <passed>/<total>
- Skipped or bounded coverage: <none or exact list>
- Tool/environment exceptions: <count and IDs>
- Judge runtime and cost: <values>
```

## Audit gaps and expand the judge

After the full implementation passes, optionally run a post-implementation gap audit: compare target decisions, `TODO`/`FIXME` families, changed public surfaces, and review findings against `.port/gaps.tsv`, then add any omitted decision before cutover. For risk that deterministic cases may miss, let an independent reviewer propose exploratory judge scenarios and run a time-bounded soak—overnight when proportionate—against production-shaped inputs. New failures reopen the owning contract, gap, or rule; retain scenario and raw-result paths. This recipe expands evidence and never relaxes the frozen baseline.

## Present the Phase 5 gate

Report smoke, port judge, separate source-baseline result, inherited-failure classifications and acceptances, divergences, coverage, optional gap-audit or expansion-soak findings, runtime, and cost. Cite raw command-output paths; `.port/status.md` is only the summary.
Forecast marker burndown and cutover cost.
Standard and Large-scale stop for explicit continuation to Phase 6.
Quick presents this as the pre-cutover result gate; no rollout has executed yet. After acceptance, no-rollout work becomes `done`; a plan-preapproved rollout becomes `rollout-active` until its receipt completes, then `done` (see `quick.md`). Any other deployment is new scope.

## By mode

**Quick — result gate only.** Run cheap checks and the focused acceptance checklist in one uninterrupted flow; no Phase 4 stop, no Phase 5 mutation requirement, and never any gates beyond the plan gate and pre-cutover result gate — a preapproved rollout follows result acceptance as a receipt, not a gate.
**Standard — priced serialization.** Serialize expensive referees, use risk-grouped queues, require live deny-guardrail preflights before fan-out, and apply the explicit inherited-failure acceptance rule.
**Large-scale — complete receipts.** Use survey queues, accidental-invocation guardrails, genuinely isolated execution where required, serialized runners, full count receipts, adversarial fix review, and the same zero-introduced/classified-and-accepted-inherited done gate.
