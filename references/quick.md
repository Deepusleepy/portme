# Run a Quick port

## Worked micro-example

**Request.** “Port the old CLI’s `--json` error output into the new Go command.”
**Scope.** Include invalid-argument errors; exclude success output and network failures.
**Scores.** Units 0, gaps 1, referee 0, blast radius 0, source 0, judge 0 = **1**.
**Value.** Removes wrapper parsing; abort if the old schema varies across the pinned fixtures.
**Mode.** Quick: one localized surface, cheap deterministic comparison, no override.
**Model plan.** Current model for all roles (default); constraint: no separate tiers.
**Checklist.** Invalid flag → exact JSON keys, message, stderr placement, and exit code 2.
**Plan gate.** “Approve this scope, score decomposition, model plan, checklist, and direct edit?”
**Execution.** Record old output, edit the Go error adapter, run the command and focused test.
**Negative check.** Change exit code to 1; the focused test fails; restore and rerun green.
**Result gate.** Show raw old/new outputs, test result, diff, marker scan, and no rollout action.
**Outcome.** User accepts the verified result; integration or deployment remains separate scope.

## Qualify Quick

Use Quick only for a confirmed localized boundary scoring 0–3 with no sizing override.
Enumerate every included observable surface; do not hide a high-risk surface in an exclusion.
If a high-risk surface lacks a strong checklist item, re-size to Standard before work begins.
Record the approved score decomposition, value charter, and visible model-plan default.
For an observed-only source, proceed only on generic functional behavior with an approved interaction script and account/environment; exclude protected material, bypasses, and third-party private data.
Bound the result to approved recorded scenarios and propose a narrower scope when any legal or authorization uncertainty is separable.

## Plan gate

Write a short contract plus one checklist item per included surface in `.port/status.md`.
Each item names setup, action, expected outputs and side effects, and evidence to retain.
The user approves scope, exclusions, scores, mode, value charter, model plan, checklist, edit plan, and any rollout action.
Set the canonical status header’s phase state to `awaiting-gate-signoff`; only the approving user message clears it and enters the gate log.
A checklist omission on a high-risk surface upgrades the port to Standard.

## Execute without intermediate gates

Track units as a checklist in `.port/status.md`; Quick has no manifest or rulebook.
Keep the canonical status header current and link raw evidence; status is not evidence.
Record plan-gate and result-gate actual/forecast cost inline in `.port/status.md`; Quick does not need a separate `cost-log.tsv`.
Capture the source behavior, implement the bounded edit, and run the declared public entry point.
The unit check must reject representative broken output and may never check existence alone.
Run every approved checklist item and the applicable cheap mechanical checks.
Search the repository for unresolved `TODO`, `FIXME`, `XXX`, `HACK`, `TODO(port)`, `BUG(port)`, `PERF(port)`, and `SAFETY(port)` markers.
Record divergences, coverage limits, skips, and tool/environment exceptions separately from passes.

## Re-size trigger

Pause and re-size to Standard when discovery introduces a decision needing user approval, a shared rule, dependencies, a high-risk omission, a third failure with the same symptom on the same checklist item or edit site, or a referee that is not cheap and isolated.
This is a mode correction, not a third Quick gate; do not continue Quick work around it.

## Pre-cutover result gate

Present contract and checklist counts, source and port evidence, checks, negative probe, marker scan, divergences, exceptions, changed paths, rollback note, cost, and raw-result paths.
This gate always occurs before cutover: no rollout action executes until the user accepts the result here, even one the plan gate preapproved.
Deployment, wider integration, or a newly discovered rollout is new scope and cannot be inferred from acceptance.
Set `awaiting-gate-signoff` and stop. Only the user’s result-gate message clears it.
After acceptance, if no rollout was preapproved, set `Active phase: done` and `Phase state: complete`. If a rollout was preapproved, set `Active phase: rollout-active` and keep `Phase state: in-progress`; execute only that exact rollout without a third gate. Append its canary, rollback readiness/action, observed-result evidence, and completion condition to `.port/status.md`. Set `done` only when the receipt is complete. A failed rollout follows the preapproved rollback and records that terminal outcome; it never becomes an implied pass.
