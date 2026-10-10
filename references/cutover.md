# Cut over the verified port

Begin Phase 6 only after the applicable Phase 5 evidence is green.
Treat cutover as a reversible behavior change; integration and live traffic can expose risks outside an isolated judge.
Keep decisions and counts under `.port/` so rollback and retirement survive session changes.

## Burn down deferred markers

Search the entire target repository mechanically for `TODO(port)`, `BUG(port)`, `PERF(port)`, `SAFETY(port)`, and unresolved `TODO`, `FIXME`, `XXX`, and `HACK` variants; classify unrelated matches rather than narrowing the scan.
Record marker type, path, unit, reason, owner, disposition, and contract impact in `.port/status.md`.
Classify each marker as fix-before-cutover, approved divergence, post-cutover follow-up, or obsolete.
Anything deferred past cutover requires user approval.

Fix one marker or tightly related root cause at a time, then rerun affected judge scenarios.
Run the full judge after the ledger reaches its approved state.
Delete or rename a marker only with a removal receipt linking its prior path and text, resolution or approved deferral, affected contract IDs, and passing judge evidence. Renaming or making a marker obsolete does not resolve it.

```markdown
## Port marker ledger
| ID | Type | Path | Unit | Reason | Disposition | Evidence | Owner |
|---|---|---|---|---|---|---|---|
| M-001 | TODO(port) | <path:line> | U-004 | <unknown> | fix-before-cutover | J-019 | <owner> |
```

## Apply the drift policy

Choose the drift policy no later than the end of Phase 3 fan-out and confirm it in Phase 6:

- **Freeze the source baseline** when source changes can pause.
- **Mirror source changes** when both paths must remain active.
- **Re-baseline before final verification** when source movement is unavoidable.

Record source revision, policy, change window, owner, and last synchronization in `.port/status.md`.
A re-baseline reopens affected mapping, gap, judge, and verification work.
Stop cutover when the source moved outside the approved policy; the Phase 5 oracle is no longer current.

## Choose rollout by blast radius

**Direct swap.** Reserve it for low-blast-radius behavior with immediate rollback.
**Feature flag.** Use controlled enablement for user-visible or moderately risky behavior.
**Shadow or dual run.** Compare deterministic services and transformations on production-shaped inputs without controlling user output.
**Staged rollout.** Progress by internal users, cohort, region, tenant, or traffic percentage for broad impact.

Prevent or deduplicate shadow writes; duplicate side effects can corrupt state or notify users twice.
Choose stages and dwell conditions from traffic volume and failure-detection latency.
Keep the old path runnable through the rollback window.

## Define rollback before rollout

Name the exact rollback action, owner, access path, and expected completion time.
Set triggers for judge canaries, error rate, latency, data mismatch, accessibility regression, and support signals.
Use conservative thresholds for irreversible side effects.
Test rollback in a safe environment or limited cohort.
Define state reconciliation and identify any target-only data lost by rollback.

```markdown
## Cutover plan
- Strategy: <direct / flag / shadow / staged>
- Baseline and drift policy: <revision; policy>
- Stages and dwell: <sequence>
- Signals: <metrics and judge canaries>
- Rollback triggers: <thresholds>
- Rollback action and owner: <procedure>
- Reconciliation: <state repair>
- Stabilization window: <owner / signals / dwell>
- Rollout state: <not-started / rollout-active / retirement-pending / retired>
- Old-path retirement date: <date or condition>
```

## Execute and observe

Run a pre-cutover judge canary against the release artifact.
Start at the smallest meaningful exposure and wait for the defined dwell condition before advancing.
During shadow or dual-run operation, compare source and port outputs on live inputs.
Track errors, latency, reconciliation, accessibility, contract-specific signals, and support feedback.
Rollback immediately when a defined trigger fires; do not renegotiate an incident threshold during the incident.
Record stage counts, mismatches, costs, and decisions in `.port/status.md`.
While exposure remains active or the rollback window is open, persist Phase 6 as `rollout-active/retirement-pending` in the phase receipt beneath the canonical status header. Do not report the port terminal while old-path retirement is pending.

Before broader exposure, optionally run the post-implementation gap audit and independent exploratory judge-expansion soak from `verification.md`. Use it for high-risk surfaces, long-tail input distributions, or lifecycle behavior that a bounded suite may miss; any escape reopens the owning contract, gap, rule, and judge evidence.

## Stabilize after cutover

Define a stabilization window with owner, signals, dwell time, and rollback availability. Keep judge canaries and the old path available through that window. Every escaped regression becomes a judge scenario and, when it reflects a recurring decision, a gap or rulebook amendment before the fix is called stable. Report escape counts and reopened artifacts at retirement.

## Review approved divergences

Read every `.port/accepted-divergences.tsv` row.
Show source behavior, port behavior, rationale, judge treatment, and rollout evidence.
The user gives final sign-off per divergence; update `final_signoff` only after that decision.
Do not retire the old path while a required sign-off remains pending.

## Retire the old path

Wait until the rollback window closes, then:

- Remove old routing and obsolete flags.
- Remove unused code, configuration, secrets, jobs, and data flows.
- Update user and operator documentation.
- Point CI, release checks, deployment pipelines, and environment configuration at the new path.
- Transfer alerts, dashboards, on-call notes, and code ownership.
- Archive source observations and judge fixtures according to policy.
- Confirm no production traffic or scheduled work reaches the old path.

Retirement is an operational state, not merely code deletion.

## Present the Phase 6 gate

Report marker counts, drift status, rollout stages, live comparisons, rollback readiness, divergence sign-offs, retirement checklist, recoverability window, and total cost.
In Standard and Large-scale, stop after the Phase 6 evidence; further work needs a new explicit scope.
Authorization to *begin* Phase 6 is not acceptance of its evidence: the run is terminal only when an actual conversation message accepts the executed cutover evidence (or actually preauthorizes objective, mechanically evidenced pass conditions before execution). The gate log records that authority but cannot create it.
In Quick, the result gate is always pre-cutover. A rollout the plan gate preapproved executes only after result acceptance: status remains `rollout-active` until its canary/rollback/observed-result receipt meets the approved completion condition, then becomes `done`. This is not another gate; any other cutover is new scope.

## By mode

**Quick: low-risk reversible cutover.** The result gate always precedes cutover. Use a direct swap only when that exact action was approved at the plan gate and immediate rollback exists; execute it after result acceptance, hold status at `rollout-active`, and move to `done` only after the complete receipt, with no extra Phase 6 stop.
**Standard: controlled exposure.** Prefer a feature flag or limited stage with a concise marker, drift, and rollback ledger.
**Large-scale: formal transition.** Require shadow or staged rollout where feasible, tested rollback, drift ownership, complete divergence sign-off, and verified retirement.
