# AGENTS OS F7 R1 Atomic Independent Review Package Receipt v0.1

Date: 2026-07-18  
Owner: Jenn  
Agent steward: Nobao  
Result: `PASS_FOR_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`

## Scope

Created the F7 R1 normative contract, deterministic synthetic fixture builder,
synthetic fixture, offline semantic validator, nonindependent author self-review,
canonical hash-bound manifest and independent review instructions.

## Fixed review unit

```text
F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R1_ATOMIC_BUNDLE
```

```yaml
subjects: 4
authority_inputs: 31
author_evidence: 1
declared_inputs: 36
manifest_sha256: c86b8c17b93aa5e800bdf17e641666984c52cfc2e1006a90a38ad7dc61658c5c
```

## Validation

```yaml
fixed_validator: PASS
authority_profiles: 20_of_20
decision_cases: 20_of_20
candidate_revisions: 2_of_2
HD_M0_dispositions: 7_of_7
fully_resigned_adversarial_mutations: 31_of_31_REJECTED
builder_byte_reproduction: PASS
manifest_hashes: 36_of_36_MATCH
git_diff_check: PASS
exceptions: 0
```

## Boundaries

No accepted/frozen F1-F6 or foundational subject was modified. No private raw
Memory or `state-private/` content was read. No real Home data, sensing,
recording, Task/Command mutation, provider call, database write, runtime
activation or external effect occurred.

The author result does not accept or freeze F7. F8 remains unstarted. The next
gate is a fresh full atomic hash-bound independent review.

