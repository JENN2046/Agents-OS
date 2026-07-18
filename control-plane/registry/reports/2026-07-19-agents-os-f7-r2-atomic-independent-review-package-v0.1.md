# AGENTS OS F7 R2 Atomic Independent Review Package v0.1

Date: 2026-07-19  
Owner: Jenn  
Review unit: `F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R2_ATOMIC_BUNDLE`  
Status: `FIXED_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## Canonical manifest

```text
control-plane/registry/reports/2026-07-19-agents-os-f7-r2-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256: d2fc34cd8df70d1a960e373606f6c53468e6020b8a8087b551561ebf6a032d35
```

```yaml
R1_subjects: 4
R2_subjects: 4
authority_inputs: 35
author_evidence: 1
declared_total: 44
partial_review: forbidden
```

The four R1 subjects remain immutable. R2 replaces only the R1 decision-case
coverage binding and preserves all other clauses.

## Review request

Perform a fresh full atomic hash-bound independent review. Do not adopt the R2
author self-review. Read and hash all 44 inputs and run every manifest command.

The central question is whether an internally valid, fully re-signed graph can
still remove, rename, replace or reorder a mandatory case while retaining a
favorable validator result.

Independently reproduce at least:

1. replace C06 identity-rewrite rejection with C01 allowed semantics;
2. replace C08 Session-to-Task rejection with allowed candidate semantics;
3. rename C06 to C99;
4. swap C06 and C07;
5. replace, rename or reorder R2 catalog anchors and fully re-sign them.

Confirm rejection comes from exact canonical inventory semantics, not only stale
hashes or an exception.

## Fixed author results

```yaml
R1_validator: PASS
R2_validator: PASS
canonical_decision_case_anchors: 20/20
R1_false_acceptance_regressions: 4/4_REJECTED
R2_catalog_mutations: 4/4_REJECTED
duplicate_JSON_key: REJECTED
R2_adversarial_total: 9/9_REJECTED
builder_byte_reproduction: 2/2_PASS
terminal_outcome: NOT_EXECUTED
```

These are author claims, not independent conclusions.

## Boundary

R2 adds no semantic class, writer, reducer result, permission model, identity
authority, Task/Command/Memory writer, runtime, provider, sensing path or F8
interface. The fixtures are synthetic and runtime unusable.

Allowed independent results are exactly `PASS_NO_BLOCKER` or `BLOCK`. Neither
result accepts or freezes F7. Only a later exact Jenn decision may do so.
