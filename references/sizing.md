# Size the port

Use this gate with the scope confirmation already required by `SKILL.md`. Do not ask the user to confirm the same boundary twice.
For a closed or observed-only source, Standard and Large-scale read `no-source.md` before scoring; Quick applies the authorization and bounded-fidelity rule in `quick.md`. Legality or observation limits may end the port before cost matters.

## Identify the thing being sized

**Carry forward the scope restatement.** Include the source, target, boundary, meaning of equivalent behavior, and explicit exclusions from the `SKILL.md` confirmation.
**Pin the oracle.** Name the source revision, build, version, or observation date and the target repository plus integration point.
**Enumerate broad requests.** For “everything X-related,” bucket discoveries by risk and propose an explicit in/out cut before expanding them into concrete sub-features. This keeps wide themes reviewable without hiding omissions.

Passive discovery may include source entry points, routes, commands, symbols, UI labels, tests, and configuration. A running-source probe is execution and needs the applicable explicit authorization; it is never passive discovery.
Attach evidence to each sub-feature so the user can add or remove items deliberately.
Where possible, present that enumerated list, the sizing verdict, the model plan, and the existing scope confirmation in one message and accept one response.
If enumeration materially changes the boundary, stop for confirmation at that combined gate. Otherwise, do not create a second scope stop.

## Score six factors

Assign each factor 0, 1, or 2 and record its evidence.

| Factor | 0 | 1 | 2 |
|---|---|---|---|
| Independent units | 1–2 tightly local units | 3–15 separable units | More than 15 units or multiple subsystems |
| Semantic-gap severity | Direct mapping with explicit types and errors | Several implicit defaults or lifecycle differences | Concurrency, security, data model, or architectural gaps |
| Referee cost | Deterministic check completes in seconds | Full check takes minutes or needs shared setup | Check is costly, flaky, manual, or rate-limited |
| Blast radius | Isolated and easy to undo | User-visible, shared, or one bounded sensitive/auth feature | Broad security-system, money, data-loss, or production impact |
| Source availability | Readable, pinned, and runnable | Partly readable or difficult to run | Observed-only, unstable, or inaccessible during work |
| Judge availability | Portable public-surface judge already works | Judge can be built from tests or recordings | Oracle is weak, manual, or has sparse coverage |

**Override upward.** A blast-radius score of 2 or judge-availability score of 2 raises the mode to at least **Standard**, even when the total suggests Quick. A bounded login/auth or other sensitive feature may therefore be Standard when its units and referee remain focused. Choose **Large-scale** for broad security-system impact (identity/authorization architecture, credential or policy propagation, or many trust boundaries) or broad production impact; durable queues, stronger review, and controlled referees are part of that risk response.
Treat unknown evidence as the higher plausible score. Do not lower source-availability risk merely because the visible interface looks simple.
Show all six scores, their evidence, arithmetic, and overrides. The user approves this decomposition before the mode binds; a total alone is not a sizing decision.

## Map the score to a mode

Choose **Quick** for totals 0–3 with no override: one localized behavior can stay in a single controlled loop.
Choose **Standard** for totals 4–8 or a bounded factor scored 2: semantic gaps need all phases 0–6 without industrial fan-out.
Choose **Large-scale** for totals 9–12, more than 15 repeatable units, parallel-agent necessity, an expensive shared referee, or a broad production/security-system override.
Raise the mode when uncertainty is material. Lower it only with concrete evidence and user agreement.
Quick also requires every included surface to fit an acceptance checklist with setup, action, observable result, and retained evidence. A missing or weakly judged high-risk surface upgrades the port to Standard.

For a whole-codebase language migration, additionally force three committed calls before the mode binds, each backed by paths or counts: structure-preserving or redesign; the measured cost of one full build/typecheck run; and whether the existing test suite hits the public surface (survives as the judge) or imports internals (dies with the language—a judge must be built).

Passive inspection cannot supply the measured build. At the initial combined scope proposal, name one exact baseline command, source revision, expected outputs, timeout, and a disposable credential-free container/worktree/snapshot with network and external writes disabled where practical. Ask the user to authorize that command specifically. Do not run an installer, lifecycle hook, build, or test until they do. Capture the command and result, verify the source/target remained unchanged, then finalize the sizing verdict; if measurement changes the score or mode, present the revised decomposition for approval rather than silently binding the provisional mode.

## Decide whether the migration is worth it

Before binding the mode, state the present pain, the expected measurable benefit of the port, and an abort condition that would make fresh implementation, a library, or staying put better. Ask the user to approve this value charter with the sizing decomposition.

## Consider the two escape verdicts

Return **no process needed — just implement it** only when all are true:

- One obvious edit has no semantic uncertainty.
- An existing test exercises the exact public behavior.
- The change is low-blast-radius and cheap to reverse.
- The target needs no new architecture or compatibility decision.

Return **don’t port — write fresh / use a library** when any applies:

- The desired behavior is small, but preserving a tangled or inaccessible source adds needless uncertainty.
- A maintained library already satisfies the confirmed contract.
- License, terms, or asset rights block the proposed port.
- The source behavior is mostly defects the user does not want.
- No credible judge can be built at acceptable cost.

State the applicable criterion and cite the exact existing test, observed behavior, and proposed edit or library evidence that supports it. Ask the user to choose; an escape verdict changes the task, not merely its mode.

## Choose the model plan

At the sizing gate, ask the user to choose model tiers for implementers, reviewers, and rule-writers. Include this named line: `Model plan — current model for implementers, reviewers, and rule-writers (default); constraints: <none or cannot switch>.`
Explain the blast-radius tradeoff: rule-writers and reviewers shape many downstream units, while implementers are bounded by review and referees.
Record the decision in `.port/status.md` and the sizing row of `.port/cost-log.tsv`.
The approved model plan binds Phase 1 rule authorship, Phase 2 review, and Phase 3 fan-out until the user changes it at a later gate.
The visible current-model plan is a proposal, not silent approval. Starting work under an unapproved plan is a process violation; log it and stop the affected fan-out until the user decides. Inability to switch tiers is a recorded constraint and does not stall the port; use the approved available model with unchanged role separation.
For Quick work without separate roles, record the single chosen tier or note that the user chose the current model for all roles.

## Estimate size at the gate

Count units from the confirmed manifest sketch; line count is not a proxy for independent review work.
For **Quick** and **Standard**, report a qualitative size band—**small**, **medium**, or **large**—plus a rough calendar range and the main serialized cost driver.
Do not forecast numeric tokens at sizing for Quick or Standard. For Large-scale, use a numeric range only when measured units from the same pipeline already exist; otherwise defer it. Keep the sizing flow to the band, calendar range, serialized cost driver, and evidence quality.

## Present the sizing gate

Present the bucketed unit list and in/out cut, six-score decomposition, total, override and destination mode, migration-value charter, mode verdict, escape verdict, qualitative size/calendar estimate, weakest evidence, and proposed next discovery action. For whole-codebase sizing that lacks a measurement, label the mode provisional and include the exact isolated baseline-command authorization described above.
Include the model-tier choices for implementers, reviewers, and rule-writers as a user decision in the same gate.
In **Quick**, this is the single plan gate. Approval starts uninterrupted work through the pre-cutover result gate; a rollout preapproved here still executes only after the user accepts the result.
In **Standard** and **Large-scale**, approval starts Phase 0, whose evidence ends at its own gate.

## By mode

**Quick — one plan gate and one result gate.** Use one unit list, a small/medium/large band, rough calendar, a chosen model tier, and no stops between phases. The judge may be the acceptance checklist.
**Standard — per-phase gates.** Score every factor, choose all three role tiers, estimate sampled review qualitatively at sizing, then replace that estimate with measured numeric cost after Phase 2.
**Large-scale — per-phase gates with orchestration detail.** Add rate limits, batch-size assumptions, serialized-referee time, and evidence-backed numeric ranges when available.

## After Phase 2 only — forecast cost

Once Phase 2 supplies measured per-unit implementation, review, rework, and referee costs, forecast with their range, review topology, fixed overhead, rate limits, and serialized-referee time. Convert tokens to money only from prices for the approved model plan. Append estimates and actuals to `.port/cost-log.tsv`:

```tsv
gate	mode	units	size_band	calendar_range	low_tokens	high_tokens	actual_tokens	actual_cost	elapsed_minutes	model_plan	notes
phase-2	Standard	8	medium	2–5 days	<low>	<high>	<actual>	<cost>	<minutes>	impl:<tier>;review:<tier>;rules:<tier>	<evidence>
```
