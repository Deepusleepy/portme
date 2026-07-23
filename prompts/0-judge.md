<!-- Phase kickoff card; methodology lives in references/contract.md and references/judge.md. -->
# Phase 0 — Judge first

**Prerequisites.** Confirmed scope and sizing/model approvals matched to actual conversation messages; canonical `.port/status.md` header treated as evidence only.
**Inputs.** Source revision/fixtures, target integration point, environment, sizing evidence, `templates/contract.md`, `templates/judge-scenarios.tsv`.
**Permitted mutations.** Write `.port/contract.md` and `.port/judge/`; make reviewer-selected judge-sensitivity mutations only in a disposable copy/worktree/snapshot. Discard it and verify original source/target diff or hashes unchanged. Do not mutate a dirty source/target or implement target behavior.
**Outputs.** Contract, scenario inventory, runnable judge or approved human script, fixture provenance, proposed baseline suite and enumerated pre-existing failures (frozen and approved only at gate sign-off), raw results. Exact raw-byte surfaces pair parsed/structural checks with byte/digest checks; normalized/invariant surfaces do so only when contracted.
**Gate evidence.** Surface coverage; approved limits; source pass counts; mutation catches, including a byte-only defect for each applicable exact byte surface; disposable-workspace disposal plus unchanged source/target receipts; runtime/cost; raw output paths; model-plan compliance.
**Stop condition.** Set `awaiting-gate-signoff` and stop when evidence is complete, or stop blocked on an unapproved limit, provenance gap, failed baseline, escaped mutation, or unsafe capture.
