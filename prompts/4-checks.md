<!-- Phase kickoff card; methodology lives in references/verification.md. -->
# Phase 4: Mechanical checks

**Prerequisites.** Phase 3 approval matched to the actual conversation; stable target batch; manifest/check-input authorization bundle digest, command/declaration authorization, and referee guardrail receipts current.
**Inputs.** Target output, referee stack, tool versions, manifest ownership, rules/gaps, serialized-runner path.
**Permitted mutations.** Fix owned target paths from the survey queue; do not weaken checks, alter the contract, or bypass referee guardrails/serialized placement.
**Outputs.** Raw survey output, machine-readable error queue, root-cause groups, reviewed fixes, rerun results, exception dispositions.
**Gate evidence.** Current manifest/check-input authorization bundle digest and declaration authorization, commands/runtimes, initial/final counts, cascades, regenerated units, per-class guardrail receipts, raw paths, cost.
**Stop condition.** Use the mid-phase exception gate for third recurrences; set `awaiting-gate-signoff` and stop only at zero unapproved mechanical errors.
