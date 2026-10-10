<!-- Phase kickoff card; methodology lives in references/cutover.md. -->
# Phase 6: Cut over

**Prerequisites.** Phase 5 approval and exact rollout authorization matched to actual conversation messages; drift policy; rollback owner and access.
**Inputs.** Release artifact, judge canaries, marker ledger, divergences, `templates/cutover-plan.md`, live signals and retirement checklist.
**Permitted mutations.** Execute only the approved rollout stages, rollback, reconciliation, marker resolutions, and old-path retirement actions.
**Outputs.** Removal receipts, canary/stage results, rollback test, divergence sign-offs, stabilization log, rollout and retirement state.
**Gate evidence.** Repository-wide marker scan, drift status, live comparisons, escape-fed judge/rule updates, recoverability, cost, raw paths.
**Stop condition.** Persist `rollout-active/retirement-pending` while the window remains; at completion set `awaiting-gate-signoff` and stop, or rollback immediately on a trigger.
