<!-- Template defined by references/contract.md; replace every <placeholder>. -->
# Port contract

## Identification
- Source: <repo/app/service; pinned revision/version; run method>
- Target: <repo/runtime/integration point/delivery form>
- Environment: <platform/locale/flags/credential class/services>

## Boundary
- In: <concrete surfaces and workflows>
- Out: <explicit exclusions>
- Retained/replaced dependencies: <list and versions>

## Observable surfaces
| ID | Surface | Input/action | Outputs and side effects | Standard | Comparator/invariant |
|---|---|---|---|---|---|
| S-001 | <surface> | <input> | <whole public result> | <exact/normalized/invariant/intentionally-divergent> | <method; for exact raw-byte surfaces include byte/digest coverage of encoding, whitespace, ordering, line endings, framing> |

## Non-functional requirements
| ID | Requirement | Workload/environment | Budget | Referee |
|---|---|---|---|---|
| NF-001 | <requirement> | <conditions> | <threshold> | <check> |

## Behavior ledger
| ID | Observed source behavior | Required port behavior | Approved divergence |
|---|---|---|---|
| B-001 | <observation> | <requirement> | <none or D-001> |

## Done criteria
- <judge suite and required counts>
- <mechanical and non-functional checks>
- <coverage, marker, divergence, and exception conditions>
