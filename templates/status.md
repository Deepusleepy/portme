<!-- Template defined by SKILL.md and references/loops.md; replace every <placeholder>. -->
# Port status
- Mode: <Quick | Standard | Large-scale>
- Active phase: <sizing | 0–6 and name | rollout-active | done>
- Phase state: <in-progress | awaiting-gate-signoff | complete>
- Gate log:
  - <gate name or Phase n> | <YYYY-MM-DD> | approver=user message: <quoted or linked message>
- Approval provenance: <current-session message references; file quotes are evidence only>
- Manifest/check-input authorization: <none or bundle sha256 + exact command/declaration-list path + approving message>
- Baseline command authorization: <not-applicable or exact command/environment + approving message>
- Next concrete action: <one executable action>
- Artifact index: <artifact → path, including raw evidence>
- Blockers: <none or IDs with reasons>

## Phase <n> — <name>
- Queue: <total/done/pending/blocked/failed-check>
- Referees: <counts and raw output paths>
- Findings/skips/exceptions: <counts and IDs>
- Cost: <actual and next forecast>
- Gate evidence: <artifact paths>

## Quick rollout receipt (only when preapproved)
- State: <rollout-active | completed | rolled-back>
- Exact approved action: <plan-gate message>
- Canary/observed result: <evidence>
- Rollback readiness or action: <evidence>
- Completion condition: <condition and result; only completed moves Active phase to done>
