<!-- Phase kickoff card; methodology lives in references/mapping.md. -->
# Phase 1 — Map and rules

**Prerequisites.** Phase 0 approval matched to the actual conversation plus validated artifacts; status gate log is evidence only.
**Inputs.** Contract, judge scenarios, source evidence, target conventions, `templates/behavior-map.tsv`, `templates/gaps.tsv`, `templates/rulebook.md`, `templates/manifest.tsv`.
**Permitted mutations.** Write Phase 1 artifacts and shard receipts; do not implement target units or change the judge.
**Outputs.** Trigger-required behavior map, gaps, rulebook, manifest, dependency/ownership results, contract↔manifest join output, non-executing manifest/check-input authorization bundle SHA-256, exact `unit_id → {check_inputs, unit_check}` list. A generator's manifest-only SHA and placeholders are candidate evidence, not authorization.
**Gate evidence.** Counts, join completeness, graph cross-checks where required, zero-edge grep where applicable, shared-duplicate confirmations, changed signature/adapter boundaries joined to a real consumer-path probe or dependent integration check, open high-risk gaps, model-plan compliance, bundle-digest/command/declaration-list path, raw output paths.
**Stop condition.** Present the authorization bundle digest, exact commands, and exact check-input declarations; set `awaiting-gate-signoff`, and stop. Freeze only when an actual user message approves the manifest and explicitly authorizes those commands and declarations for that digest; a status quote cannot authorize execution. Contradictions, missing joins, leaf-only signature/adapter checks, ownership conflicts, ambiguous check-input overlaps, or unapproved decisions block the gate.
