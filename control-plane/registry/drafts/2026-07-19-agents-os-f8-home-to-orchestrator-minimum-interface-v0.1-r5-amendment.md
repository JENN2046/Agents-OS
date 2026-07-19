# AGENTS OS F8 Home-to-Orchestrator Minimum Interface v0.1 R5 Amendment

Date: 2026-07-19
Status: fixed only when bound by an F8 R5 atomic manifest
Owner: Jenn
Agent steward: Nobao

## 1. Scope and precedence

R5 replaces only the inherited R2 H01 compatibility derivation and the R4
`stable_ref` implementation profile. R4 continues to govern consumer
nullability and all-null fail-closed resolution. R3 continues to govern exact
owner-issued immutable assessment-revision commitment consumption. R2 and R1
continue in that order for all remaining clauses.

```text
R5 explicit replacements
-> R4 clauses not replaced by R5
-> R3 clauses not replaced by R4 or R5
-> R2 clauses not replaced by R3 through R5
-> R1 all other clauses
```

R5 does not issue an assessment or commitment, recompute an upstream reducer,
create permission, identity, Task or Command authority, or authorize runtime
use.

## 2. Exact H01 owner-commitment source binding

Every non-null consumer in the upgraded R2 H01 inventory must resolve against
an immutable owner-source record outside the caller-controlled R5 graph.

```yaml
TrustedH01OwnerCommitmentV0_1R5:
  role: closed_H01_consumer_role
  owner_contract: closed_owner_contract
  commitment_ref: stable_ref
  commitment_revision: positive_safe_integer
  assessment_id: stable_ref
  assessment_revision: positive_safe_integer
  assessment_fingerprint: lowercase_sha256
  issued_event_ref: stable_ref
  issued_event_sequence: positive_safe_integer
  issued_event_fingerprint: lowercase_sha256
  commitment_fingerprint: lowercase_sha256
```

The immutable source key is:

```text
(role, commitment_ref, commitment_revision)
```

The source record must bind the exact R2 assessment tuple:

```text
(assessment_id, assessment_revision, assessment_fingerprint)
```

and its `commitment_fingerprint` must cover every preceding field. The R5
offline validator carries a fixed trusted-source commitment anchor that is not
derived from caller-provided fixture rows during validation. Editing and fully
re-signing a fixture, consumer or claimed source row cannot change this trusted
anchor.

For every non-null H01 consumer, validation requires exact equality of:

```text
consumer owner_commitment_ref
consumer expected_owner_commitment_revision
consumer expected_owner_commitment_fingerprint

==

resolved trusted source commitment ref / revision / fingerprint
```

and exact equality of the assessment tuple committed by that source. Missing,
duplicate, substituted, conflicting or untrusted source records fail closed.
F8 does not derive whether the upstream owner should have issued the
assessment; it only consumes the fixed owner record.

The optional `jenn_exact_decision` consumer remains the R4 `ALL_NULL` form and
performs no owner-source lookup.

## 3. Merged H01 derivation

The R5 H01 result must be derived and must not be copied from
`claimed_result`.

The normative sequence is:

```text
1. Resolve the exact immutable R2 H01 row and its exact R2 assessment inventory.
2. Apply R4 two-branch nullability validation to every upgraded consumer.
3. For every ALL_NON_NULL consumer, resolve the exact trusted R3-style owner commitment.
4. Require exact assessment tuple equality between R2 consumer, R5 consumer and trusted commitment.
5. For the ALL_NULL Jenn consumer, perform zero owner lookup and preserve optionality only because the R2 Jenn-requirement assessment says NO_EXACT_DECISION_REQUIRED.
6. Invoke the fixed R2 handoff reducer over the fixed R2 raw input and upstream assessments.
7. Accept CANDIDATE_FORMED only when steps 1 through 6 all succeed and the derived R2 result is CANDIDATE_FORMED.
```

The validator must verify the fixed R2 fixture and R2 validator hashes before
using that reducer. It must not treat an R5 fixture field as an alternative R2
implementation.

The R5 decision projection is:

```yaml
result: CANDIDATE_FORMED
primary_reason: VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE
reason_codes:
  - VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE
runtime_usable: false
command_authority: false
task_write_authority: false
effect_authority: false
F3_recheck_required: true
F3_command_ref: null
F3_intake_ref: null
```

Any owner-commitment substitution produces `INDETERMINATE` and never a
favorable result.

## 4. Restored stable_ref profile

R5 restores the inherited definition without adding a new restriction:

```text
type(value) is JSON string
and value is nonempty
and NFC(value) == value
```

Internal spaces and an all-whitespace nonempty string are not rejected by the
`stable_ref` profile itself. Domain-specific schemas may impose additional
constraints only through a separately frozen clause; R5 adds none.

The validator must include:

```text
non-NFC stable_ref -> REJECT
nonempty NFC stable_ref containing internal space -> ACCEPT
integer / null / empty string -> REJECT when stable_ref is required
```

## 5. Required R5 regressions

The offline validator must independently re-sign and reject at least:

```text
owner commitment ref substitution
owner commitment revision substitution
owner commitment fingerprint substitution
owner commitment tuple copied from another H01 role
trusted owner-source row deletion, duplication or reordering
claimed_result changed without changing derivation
R2 H01 assessment tuple changed while commitment remains fixed
non-NFC stable_ref
```

It must accept a nonempty NFC stable ref containing an internal space. Rejection
must come from the target semantic or schema rule, not a stale row, section or
root fingerprint.

## 6. Constructive witness and boundary

```yaml
R5_witness:
  H01_case_count: 1
  non_null_consumer_count: 7
  all_null_consumer_count: 1
  exact_owner_commitment_resolutions: 7
  stable_ref_internal_space_positive_count: 1
  runtime_usable_count: 0
  real_Home_count: 0
  real_Command_count: 0
  database_write_count: 0
  provider_call_count: 0
  production_authentication_count: 0
  private_Memory_read_count: 0
  sensing_or_recording_count: 0
  external_effect_count: 0
  terminal_outcome: NOT_EXECUTED
```

Synthetic trusted anchors are test-only and must never be compiled or loaded as
production authority.

## 7. Governance boundary

```yaml
F8_R5_started: true
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
next_gate: F8_R5_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW
```
