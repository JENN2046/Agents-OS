# AGENTS OS F6 R6 Fresh Full Atomic Independent Review Package v0.1

Review unit: `F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R6_ATOMIC_BUNDLE`

Manifest SHA-256: `519939e743457773476ed1915781c314046f790ec1322361d4df42c47fd5dd9f`

This indivisible unit contains 24 subjects, 40 authority inputs and one
non-independent author review: 65 hash-bound inputs total. Partial review is
forbidden. Execute all twelve Manifest commands and independently review both
R6 proof surfaces.

## R6 proof surfaces

### Same-revision immutable history

The fixed R5 fixture bytes are the immutable history anchor. A candidate may
not replace that anchor with a self-signed mirror. Replacing candidate,
Requirement, evidence or attempt context and then updating the assessment
subject, every dependent fingerprint and every root while keeping the same
attempt and assessment revisions must reject at the R6 semantic layer.

The reviewer should independently construct that fully coordinated mutation,
not merely leave the old assessment unchanged.

### Contextual assessment schema totality

The reviewer should fully re-sign and test:

```text
unknown wrapper, payload, assessed-subject and binding fields
missing required fields
integer 1/0 substituted for JSON boolean
float, non-finite and unsafe integer values
invalid nullable predecessor combinations
duplicate JSON keys before object construction
missing, duplicated or reordered immutable-history rows
malformed values that previously raised KeyError or TypeError
```

Every invalid input must return deterministic `BLOCK` without an uncaught
exception. Failure must arise from the target schema/history rule, not stale
hashes or unpropagated references.

## Author evidence boundary

Author validation claims:

```yaml
fixed_negative_total: 62/62_REJECTED
R2_coordinated_cases: 17/17_REJECTED
R3_cases: 7/7_REJECTED
R4_context_replacement_case: 1/1_REJECTED
R6_adversarial_cases: 11/11_REJECTED
same_revision_full_resign: 1/1_REJECTED
schema_totality_cases: 10/10_REJECTED_OR_STABLE_BLOCK
exceptions: 0
builder_byte_reproduction: PASS
real_occurrences: 0
```

These are author claims and cannot substitute for independent judgment.
Allowed independent results are only `PASS_NO_BLOCKER` or `BLOCK`.

## Governance boundary

F6 is not accepted or frozen. F7 is not started. This package authorizes no
implementation, runtime, database, service, provider, production
authentication, real Task/Validation/Event/effect or Git delivery.
