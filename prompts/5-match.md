<!-- Phase kickoff card; methodology lives in references/verification.md. -->
# Phase 5 — Run and match

**Prerequisites.** Phase 4 approval matched to the actual conversation (or documented cheap-check dissolution); trusted frozen Phase 0 baseline available.
**Inputs.** Source and port environments, exact judge fixtures/normalizers, contract, divergences, approved limits, raw check outputs.
**Permitted mutations.** Fix introduced target root causes; judge changes require separate review and mutation evidence; never narrow baseline or reclassify failures as limits.
**Outputs.** Smoke and full-judge results, matched inherited failures, exceptions, optional gap audit and exploratory soak, updated raw receipts.
**Gate evidence.** Zero introduced failures, no unapproved baseline failures, bounded classifications, non-functional budgets, skip reasons, raw paths, cost.
**Stop condition.** Set `awaiting-gate-signoff` and stop before cutover; unresolved outcomes, provenance gaps, or high-risk soak findings block the gate.
