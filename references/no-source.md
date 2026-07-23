# Port from an observed-only source

## Legality and ethics gate

**Functional-replication fast path.** Proceed when the requested work is generic functional UX replication and excludes branding, assets, trade dress, paywalled content, access-control circumvention, and third-party private data.
Note that basis, the authorized account/environment, and the excluded material in `.port/status.md`; no separate mandatory stop is required for this path.
The fast path still requires a recorded authorization basis: whose account, what the user's relationship to the source is, and — when observation is automated (scripted driving, HAR capture, scraping) — whether the service's terms permit it as far as the user knows. Unknown terms are uncertainty, and uncertainty routes to the protected-case stop, not the fast path.

**Protected-case stop.** Stop before sizing when the plan may reproduce protected expression or material, bypass controls, use another person’s private data, or conflict with terms, license limits, contracts, account permissions, or applicable law.
Ask the user to resolve the exact concern. Their clearance is scope evidence, not jurisdiction-specific legal advice.
When uncertainty concerns only part of the request, propose a narrowed functional scope that excludes the uncertain material, method, account, or surface and ask the user to confirm it. Do not treat uncertainty about one surface as permission for it or as a mandatory end to clearly separable lawful work.

Never bypass authentication restrictions, rate limits, encryption, or technical protections.
Use only accounts, environments, traffic, and exports the user is authorized to inspect.
Do not collect credentials, tokens, sessions, or another person’s private data.
Do not reproduce unlicensed text, media, datasets, branding, or trade dress, and do not imply affiliation.
Set redaction, retention, and deletion rules before evidence is produced.

## Ask whether parity is necessary

Before any observation plan, ask whether the user needs behavior parity or merely comparable features.
If comparable features suffice, return **don’t port — write fresh / use a library**, record the escape verdict, and skip the entire probe-and-capture pipeline.
Continue only when source-specific behavior is part of the confirmed contract.

## Bound the parity claim

Recorded observation is the oracle; unreadable internals cannot provide complete coverage.
State in `.port/contract.md` that parity is bounded by observed scenarios.
Name source version and observation date, devices, platforms, locales, account tiers, flags, and permissions.
Use `unobserved, inferred` in the observed-source ledger column when evidence is absent.
Final claims say the port matches recorded scenarios and stated assumptions, never unqualified “full parity.”

```markdown
## Observed-only source limits
- Source/version/date: <identity>
- Authorized observation surfaces: <list>
- Environments and account classes: <list>
- Covered scenarios: <IDs>
- Unobserved areas: <list>
- Confirmed assumptions: <IDs>
- Fidelity claim: Matches recorded behavior within the coverage above.
```

## Inventory visible surfaces

Enumerate applicable screens, commands, gestures, keyboard paths, endpoints, exports, notifications, and external effects.
Include relevant roles, tiers, flags, locales, devices, and connectivity states.
Link every surface to a contract row, proposed scenario, and entry-to-result row in `.port/behavior-map.tsv`.
Mark unsafe, unlawful, or unavailable probes as exclusions rather than inferred passes.

## Discover an unknown interaction schema, then stop

When the public request envelope or action vocabulary is unknown, perform one
bounded schema-discovery step before proposing the final interaction script.
The user's authorization must explicitly include this discovery in a named
local/test account and environment; general permission to observe the product
is not enough. Use only harmless metadata, capability, validation-error, or
unknown-action probes on already authorized public surfaces. Never bypass
controls, authentication, rate limits, or technical protections.

Retain each probe, response class, timestamp, environment, and the resulting
candidate envelope/action vocabulary. Stop discovery once that bounded question
is answered, before adding endpoints, accounts, roles, methods, or other
surfaces. Present the findings and use them to draft the final interaction
script, which still requires the normal explicit authorization below. If the
bounded probes do not reveal the schema, record the unknown or ask the user to
expand scope; do not improvise broader probing.

The observed-UI example's
[`capture.py`](../examples/standard-observed-ui/.port/judge/capture.py) and
[`pocketscan.py`](../examples/standard-observed-ui/.port/scanner/pocketscan.py)
show one retained capture/scanner pipeline for a local fixture. They are worked
templates, not a universal scanner or a default authorization to probe another
source.

## Choose a proportionate probe matrix

Use repeatable interaction scripts with stable setup, actions, and checkpoints.
Probe normal behavior first, then risk-relevant empty, boundary, invalid, denied, timeout, retry, cancellation, and recovery paths.
Vary one dimension at a time, reset state, respect documented limits, and record unknowns.

**Quick local/offline app.** Cover the primary scenario plus the single highest-risk edge. Capture visible state, focus/keyboard behavior, and a local export or state snapshot only when applicable. Do not request HAR for an offline app.
**Standard local/offline app.** Cover confirmed surfaces and risk-focused edges across only the devices/locales that can change the contract. Prefer screenshots, recordings, accessibility trees, logs, and local state; omit network capture when no network behavior exists.
**Hosted or networked source.** Add authorized HAR or response capture only when protocol behavior is in scope.
**Large-scale.** Use a systematic environment matrix, but prune dimensions with documented evidence that they cannot affect contracted behavior.

Build flow as entry point → validation → rules → state → side effects → visible result, omitting layers that do not exist.
Infer hidden transitions from before-and-after evidence, label confidence, and test high-risk inferences with controlled negative probes.

## Produce evidence, then consume it

The porting agent may operate the source only after the user approves the exact interaction script and named account/environment. Outside that authorization, it consumes admitted fixtures and does not independently probe the source. Provide the producer with setup, actions, checkpoints, environment, source version, and redaction requirements. Do not request irrelevant capture types; an offline desktop workflow needs no HAR.

**Quarantine is the only raw landing point.** Before capture, create a unique temporary directory outside the repository, set mode `0700`, record its resolved path, and ensure it is not a symlink. Never aim a capture tool, browser download, export, or recorder at `.port/`. Use a disposable credential context where practical and keep quarantine out of sync/backup paths.

Before reading or transforming captures, reject symlinks, hard-link surprises, devices, sockets, FIFOs, and every entry other than ordinary directories and regular files. Do not follow links. Record the inventory and file hashes.

Run an explicitly named secret/PII/malware scanner with its version, exact command, rules/config path and digest, timestamp, findings, and exit status. Preserve the raw scanner output as a receipt outside the distributable fixture set. Redact in quarantine, rescan the redacted output, and review scenario provenance. Only then **copy, never link**, approved regular-file redactions into `.port/judge/fixtures/<scenario-id>/`; verify the admitted copies are regular non-symlink files and record their hashes, source hashes, redactions, scenario ID, environment, and timestamp. Raw evidence remains outside the repository even when retention policy permits keeping it elsewhere.

After admission, delete the quarantine according to the approved retention rule, verify the resolved path no longer exists, and record deletion command/method, timestamp, verifier, and result in `.port/receipts/capture-<id>.md`. If deletion fails, stop and report the residual path; do not claim cleanup. Scan admitted fixtures again immediately before commit or sharing.

Use this receipt shape:

```markdown
## Capture receipt — <ID>
- Authorization: <actual conversation message>; account/environment: <named>
- Quarantine: <resolved outside-repo path>; mode: 0700; non-symlink: yes
- Inventory: <regular files/dirs only receipt>; rejected entries: <none/list>
- Scanner: <name/version>; config: <path + SHA-256>; command/result: <raw receipt>
- Redaction/rescan: <method; findings; receipt>
- Admitted copies: <source hash → .port fixture hash>; link checks: passed
- Deletion: <method/time>; path-absent verification: <receipt>
```

## Turn evidence into the judge

A golden scenario contains setup, action sequence, checkpoints, raw observation, normalization, and expected verdict.
Assign stable IDs and map each scenario to contract surfaces.
When permitted, adapters replay the same logical actions against source evidence and port; otherwise use the recorded source golden.
Compare DOM, accessibility, network, export, state, behavior tables, and visual evidence according to each contract standard.
Normalize only approved noise.

Standard and Large-scale validate source-baseline ingestion and deliberately mutate port behavior to test judge sensitivity.
Quick may use the approved acceptance checklist without mandatory mutation validation.
Judge changes remain independent from port changes.

```tsv
scenario_id	surface_id	environment	setup	actions	checkpoints	fixture_refs	normalizer	coverage_limit
J-001	S-001	macOS;en-IN;paid	fresh document	click save	toast;export	fixtures/J-001/	mask_timestamp	other locales unobserved
```

## Manage assumptions and unknowns

Write one assumption per unknown behavior with evidence, confidence, target behavior, and user decision.
Confirm high-blast-radius assumptions before Phase 2.
Place site-specific unknowns in `.port/gaps.tsv` and mark affected code with `TODO(port): unobserved source behavior — <assumption ID>`.
Approved intentional differences enter `.port/accepted-divergences.tsv`.

```markdown
| ID | Unobserved behavior | Evidence | Inferred target behavior | Confidence | User decision |
|---|---|---|---|---|---|
| A-001 | <unknown> | <nearby observations> | <proposed behavior> | low | pending |
```

## Adapt the phases (0–6)

Phase 0 uses authorized fixtures as the oracle. Phase 1 uses behavior tracing and explicit assumptions.
Phase 2 targets risky inferences. Phase 3 keeps disk queues and read-only reviewers.
Phases 4–5 report scenario coverage bounds. Phase 6 retains marker, divergence, rollback, and retirement gates.

## Present observed-source evidence

At the initial decision, report the fast-path basis or protected-case concern, authorized surfaces, prohibited methods, exclusions, privacy handling, and the parity-versus-comparable-features answer.
At Phase 0, report scenarios, surface coverage, environments, mutation catches when required, and unobserved areas.
At later gates, repeat the bounded fidelity statement.
Quick records intermediate evidence without stopping; Standard and Large-scale stop at their phase gates.

## By mode

**Quick — two gates.** Approve the narrow observation/acceptance plan at the plan gate, then run without stops and present bounded results at the result gate.
**Standard — risk-focused observation.** Cover confirmed surfaces with proportionate edge probes and user-approved assumptions; use human acceptance only as a documented coverage limit where automation cannot work.
**Large-scale — systematic evidence.** Require redacted capture pipelines, stable scenario IDs, independent judge review, an environment matrix, and staged cutover.
