# Write the port contract

Write `.port/contract.md` beside the Phase 0 judge. It defines equivalence before implementation can redefine success.
Draft product intent with the user. Keep observed source behavior, required port behavior, and approved divergence in separate fields.

## Identify source and target

**Source.** Record the repository, application, service, or artifact with a pinned revision or version and the exact run or observation method.
**Target.** Record the repository, runtime, integration point, and delivery form.
**Environment.** Name relevant platform, locale, feature flags, credential class, services, and other conditions that can alter behavior.
**Unknowns.** Mark unavailable facts as assumptions awaiting confirmation; do not turn missing evidence into precision.

## Fix the boundary

List included commands, routes, screens, workflows, modules, and data paths.
List excluded neighbors and follow-on work explicitly.
Name retained and replaced dependencies plus source versions or dates excluded from parity.
Map every included item to at least one observable surface. Internal structure alone is not a contract surface.
For infrastructure-as-code, distinguish configuration or plan parity from deployed-state and reconciliation semantics; state effects are separate contract surfaces when observable.

Use the one scope confirmation already required by `SKILL.md`. The contract refines that approved boundary and does not create a duplicate scope question.

## Enumerate observable behavior

For each applicable surface, capture the whole public result:

- **CLI:** inputs, stdout, stderr, exit status, files, and environment effects.
- **API:** requests, responses, status codes, headers, authentication, persistence, and retry semantics.
- **UI:** actions, visible state, focus, keyboard flow, loading, errors, accessibility, and navigation.
- **Integrations:** emitted events, network calls, promised logs, notifications, and external writes.
- **Failures:** error type, timing, recovery, partial side effects, and retryability.

Do not add empty categories. A frontend-only port may have no API surface.

## Assign an equivalence standard

Choose exactly one standard per surface:

- **exact** — bytes, codes, ordering, or messages that consumers observe directly.
- **normalized** — named instability such as approved timestamps or generated IDs may differ.
- **invariant** — several outputs are valid, but stated properties must hold.
- **intentionally-divergent** — the user approved a different target behavior and its rationale.

Put the normalization algorithm or invariant beside the surface.
When an **exact** surface contracts raw bytes, structural or parsed equality is
not sufficient by itself. Pair it with a byte-for-byte comparison or digest
that covers the applicable encoding, whitespace, ordering, line endings, and
framing. Do not impose byte equality on normalized or invariant surfaces unless
their contract separately names raw bytes as observable.
For numeric behavior, name an absolute or relative epsilon; for stochastic behavior, name the distributional bound, sample size, and confidence rule.
Reject terms such as “similar” or “works”; they cannot drive a verdict.
Security, privacy, and data-loss defects begin as proposed divergences rather than copied behavior.

## Count non-functional behavior

Set performance budgets with workload, percentile, environment, and tolerance.
State accessibility requirements as concrete checks and interaction paths.
Capture error type, timing, retryability, message stability, concurrency, and ordering guarantees when consumers rely on them.
Add compatibility, resource, and startup budgets only where they are observable requirements.

## Maintain the behavior ledger

Create one row per observed behavior.
For observed-only sources, use `unobserved, inferred` in the source column when evidence is absent.
Give each divergence a stable ID and mirror approved rows into `.port/accepted-divergences.tsv` for Phase 6.
Each divergence row covers one bounded behavior on one surface. Blanket rows such as “platform differences” are invalid; split them until each can be judged and signed off independently.

Use this template:

```markdown
# Port contract

## Identification
- Source: <repo/app/service, revision/version, run method>
- Target: <repo/runtime/integration point>
- Environment: <platform, locale, flags, credentials class>

## Boundary
- In: <concrete surfaces and workflows>
- Out: <explicit exclusions>
- Retained/replaced dependencies: <list>

## Observable surfaces
| ID | Surface | Input/action | Outputs and side effects | Standard | Comparator/invariant |
|---|---|---|---|---|---|
| S-001 | <command/API/UI> | <input> | <result> | exact | <method> |

## Non-functional requirements
| ID | Requirement | Workload/environment | Budget | Referee |
|---|---|---|---|---|
| NF-001 | <performance/a11y/error> | <conditions> | <threshold> | <check> |

## Behavior ledger
| ID | Observed source behavior | Required port behavior | Approved divergence |
|---|---|---|---|
| B-001 | <observation> | <requirement> | <none or D-001> |

## Done criteria
- <judge suite and required counts>
- <mechanical checks>
- <non-functional budgets>
- <marker and divergence gates>
```

Use this schema for `.port/accepted-divergences.tsv`:

```tsv
id	surface	source_behavior	port_behavior	reason	approved_by	approved_at	final_signoff
D-001	S-004	<observed>	<required>	<security/product reason>	<user>	<date>	pending
```

## Define done

Every contract surface has a judge rung or a user-approved coverage limit with a reason and affected contract IDs. An unapproved limit blocks done.
Mechanical checks and non-functional budgets meet their approved thresholds.
Introduced failures are zero.
Every inherited failure is tied to a source rerun, classified, counted, and explicitly accepted; its count need not be zero.
The frozen source baseline suite has no unapproved source failures; bounded, enumerated pre-existing failures may remain only with user approval.
Every unresolved `TODO`, `FIXME`, `XXX`, `HACK`, `TODO(port)`, `BUG(port)`, `PERF(port)`, and `SAFETY(port)` match is resolved, classified unrelated, or explicitly accepted with evidence.
Every approved divergence receives final sign-off before retirement of the old path.

## Present the contract evidence

Show the contract, uncovered surfaces, assumptions, proposed divergences, judge plan, and projected referee cost together.
In Standard and Large-scale, this evidence forms the Phase 0 gate and the workflow stops for explicit continuation.
In Quick, the contract and acceptance checklist belong to the sizing plan gate; Phase 0 records them and continues without another stop.

## By mode

**Quick — short contract at the plan gate.** Keep applicable surfaces and a concise ledger; use an acceptance checklist and do not introduce a Phase 0 gate.
**Standard — complete included behavior.** Cover all included surfaces, non-functional risks, assumptions, and explicit coverage limits.
**Large-scale — stable machine joins.** Assign stable IDs everywhere and require machine-readable divergence tracking across workers and gates.
