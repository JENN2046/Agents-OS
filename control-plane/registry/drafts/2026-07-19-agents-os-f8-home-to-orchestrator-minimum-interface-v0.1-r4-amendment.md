# AGENTS OS F8 Home-to-Orchestrator Minimum Interface v0.1 R4 Amendment

Date: 2026-07-19
Status: fixed only when bound by an F8 R4 atomic manifest
Owner: Jenn
Agent steward: Nobao

## 1. Scope and precedence

R4 replaces only the nullability validation and all-null resolution clauses of
`AssessmentConsumerV0_1R3`. R3 governs all owner-issued immutable commitment,
candidate-history and minimum-watermark semantics not explicitly replaced
here. R2 and R1 continue in that order for all remaining clauses.

R4 does not change an assessment result, create an assessment or commitment,
recompute an upstream reducer, create permission, identity, Task or Command
authority, or authorize runtime use.

## 2. Closed consumer shapes

The field inventory remains exactly:

```yaml
AssessmentConsumerV0_1R4:
  assessment_id: stable_ref_or_null
  expected_assessment_revision: positive_safe_integer_or_null
  expected_assessment_fingerprint: lowercase_sha256_or_null
  owner_commitment_ref: stable_ref_or_null
  expected_owner_commitment_revision: positive_safe_integer_or_null
  expected_owner_commitment_fingerprint: lowercase_sha256_or_null
```

The schema is a closed two-branch sum type:

```text
ALL_NULL
  every one of the six fields is JSON null

ALL_NON_NULL
  both ref fields satisfy stable_ref
  both revision fields satisfy positive_safe_integer
  both fingerprint fields satisfy lowercase SHA-256
```

Every mixed-null combination is malformed and must be rejected before any
fingerprint or favorable result is trusted. With six nullable fields there are
exactly 62 mixed-null bit patterns; all 62 are invalid.

Unknown fields, missing fields, duplicate JSON keys, integer-as-boolean,
floats, NaN, wrong scalar types and out-of-range integers remain rejected.

## 3. All-null resolution

An `ALL_NULL` consumer represents missing or unavailable optional evidence. Its
canonical resolution is:

```yaml
assessment: null
resolution: ASSESSMENT_CONSUMER_UNAVAILABLE
owner_store_lookup_performed: false
assessment_result_interpreted: false
authority_created: false
```

The resolver must recognize this branch before assessment or owner-commitment
lookup. A caller cannot use the all-null form to select a default assessment,
reuse a prior assessment, infer authority, or obtain a favorable result.

For a required consumer, `ASSESSMENT_CONSUMER_UNAVAILABLE` produces the
enclosing reducer's existing fail-closed result. In the R4 constructive
witness:

```text
formation required consumer ALL_NULL
-> INDETERMINATE / ASSESSMENT_CONSUMER_UNAVAILABLE

acknowledgement F3 outcome consumer ALL_NULL
-> ACKNOWLEDGED_INDETERMINATE / ASSESSMENT_CONSUMER_UNAVAILABLE
```

An `ALL_NON_NULL` consumer continues to use the exact R3 owner-assessment and
owner-commitment resolution. R4 does not replace or weaken that path.

## 4. Inherited R2 H01 compatibility

R2 H01 is the canonical synthetic case in which:

```text
jenn_requirement == NO_EXACT_DECISION_REQUIRED
jenn_exact_decision consumer == all null
result == CANDIDATE_FORMED
```

When upgrading an R2 consumer to R4, each non-null R2 assessment tuple receives
its exact owner-commitment tuple. The optional `jenn_exact_decision` tuple
becomes all six fields null. Down-projecting the first three fields must recover
the exact immutable R2 H01 consumer inventory.

The all-null optional Jenn decision does not by itself make the case
indeterminate or rejected. It is legal because the separately resolved Jenn
requirement says an exact decision is not required. If the requirement says an
exact decision is required, the existing fail-closed R2/R3 rule still applies.

This compatibility rule does not let F8 decide whether Jenn authorization is
required. F8 consumes the exact upstream requirement assessment and only
preserves the already-frozen optional-consumer behavior.

## 5. Constructive witness requirements

The R4 synthetic witness must contain:

```yaml
schema_profiles: 3
consumer_shape_positive_cases: 2
mixed_null_negative_cases: 62
formation_all_null_cases: 1
acknowledgement_all_null_cases: 1
inherited_R2_H01_compatibility_cases: 1
real_runtime_occurrences: 0
terminal_outcome: NOT_EXECUTED
```

The validator must independently derive the two legal consumer branches,
reject all 62 mixed-null patterns, prove lookup count remains zero for all-null
resolution, and verify the exact R2 H01 source row and down-projection.

Fixture/root hashes are integrity anchors only. They do not replace schema,
sum-type, resolution or compatibility validation.

## 6. Authority and runtime boundary

```yaml
F8_role:
  consume_owner_assessment_and_commitment: true
  recompute_owner_reducer: false
  issue_owner_commitment: false
  create_permission_or_identity_authority: false
  create_Task_or_Command_authority: false
  narrow_low_disclosure_interface_only: true

synthetic_witness:
  runtime_usable: false
  production_usable: false
  real_Home: false
  real_Command: false
  private_Memory: false
  sensing: false
  effect: false
```

## 7. Governance boundary

```yaml
F8_R4_started: true
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
database_or_provider_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
real_effect_authorized: false
next_gate: F8_R4_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW
```
