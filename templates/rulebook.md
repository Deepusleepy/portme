<!-- Template defined by references/mapping.md; replace every <placeholder>. -->
# Port rulebook

## Approved rules

### R-001 — <short decision>
- Source pattern/condition: <pattern>
- Required target action: <action>
- Named exceptions: <none or list>
- Evidence and contract rows: <paths/IDs>
- Positive example: <example>
- Negative example: <counterexample>

## Language-migration decision checklist
<!-- For language ports, a rulebook silent on any applicable row below is incomplete. Delete for other port types. -->
- Target ecosystem adoption and banned alternatives: <libs/idioms in; alternatives out>
- Canonical construct mappings: <source construct → target construct>
- Errors: <exceptions/panics/sentinels/partial results; distinguish allocation-failure guards from precondition guards — they translate differently>
- Standard-library semantic traps: <source stdlib calls whose target namesake differs (locale-dependent character classes, integer division, sort stability, regex dialects); decide each once>
- Memory, ownership, and concurrency: <policy>
- Numeric, text/encoding, time, and serialization semantics: <policy>
- Module boundaries and canonical homes for shared helpers: <policy>
- Target-path naming rules: <rule>
- Source-bug posture: <reproduce with BUG(port) / diverge with approval>

## Pending amendments

### RA-001 — <proposed change>
- Trigger/fingerprint: <rule ID + symptom class>
- Evidence: <exact tests/behaviors/edits>
- Affected units: <IDs>
- Material impact: <behavior/coverage/ownership/cost/blast radius>
- User disposition: <pending>
