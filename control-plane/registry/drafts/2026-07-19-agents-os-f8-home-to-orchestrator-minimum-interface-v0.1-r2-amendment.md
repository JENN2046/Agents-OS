# AGENTS OS F8 Home-to-Orchestrator Minimum Interface v0.1 R2 Amendment

Status: fixed only when bound by an F8 R2 atomic manifest
Date: 2026-07-19
Owner: Jenn
Agent steward: Nobao

## 1. Amendment boundary and precedence

This amendment closes exactly `F8-R1-B01` through `F8-R1-B04` and
`F8-R1-M01` through `F8-R1-M02`. It does not replace the F8 R1 contract as a
historical subject. For the R1+R2 atomic unit:

```text
R2 explicit replacement clauses
-> R1 clauses not explicitly replaced
```

The four R1 subjects and their R1 manifest remain byte-immutable. R2 does not
accept or freeze F8, start Phase 5A, implement an adapter, activate runtime,
create a database, authenticate production traffic, access private Memory,
sense, record, call a provider or execute a real effect.

## 2. Canonical prospective F3 result order

R2 replaces every R1 ordering of `required_intake_results` with exactly:

```json
["COMMITTED", "REJECTED", "INDETERMINATE"]
```

This is an ordered JSON array and is fingerprinted as such. Any deletion,
addition, duplicate, substitution or reorder rejects. The array remains an
unaccepted F3-owned interface requirement; it does not define or activate an
F3 Command type.

## 3. Exact assessment consumption

R2 replaces `AssessmentConsumerV0_1` with:

```yaml
AssessmentConsumerV0_1R2:
  assessment_id: stable_ref_or_null
  expected_assessment_revision: positive_safe_integer_or_null
  expected_assessment_fingerprint: lowercase_sha256_or_null
```

Nullability is all-or-none. A missing optional Jenn decision has all three
fields null. Every non-null consumer is resolved through the upstream owner's
assessment store by exact ID and revision. Before interpreting the assessment
result, F8 must require:

```text
resolved assessment revision == expected_assessment_revision
resolved immutable row fingerprint == expected_assessment_fingerprint
resolved row recomputed fingerprint == expected_assessment_fingerprint
resolved current-head marker == true
resolved based_on_event_sequence >= trusted_event_sequence
resolved owner, kind, subject, revision, fingerprint and context == expected
```

F8 never accepts a caller-supplied result label as authority. The synthetic
fixture represents owner resolution only as constructive nonauthority evidence.
Changing an assessment result, subject, current-head marker, Event watermark or
any other fingerprinted field without advancing the owner assessment revision
changes the row fingerprint and invalidates the existing consumer.

## 4. Exact assessment-set commitment

R2 replaces the candidate assessment-set formula with:

```text
assessment_set_fingerprint = SHA256(
  domain_tag
  || canonical ordered rows of:
     role,
     assessment_id,
     expected_assessment_revision,
     expected_assessment_fingerprint
)
```

The role order is the closed F8 consumer-role order. Missing optional Jenn
decision values are represented by three nulls. The candidate fingerprint
commits to this assessment-set fingerprint. ID and revision alone are
insufficient.

## 5. Exact-current F3 acknowledgement

R2 replaces the acknowledgement raw input with:

```yaml
HomeIntentHandoffAcknowledgementRawInputV0_1R2:
  handoff_candidate_ref: stable_ref
  handoff_candidate_revision: positive_safe_integer
  handoff_candidate_fingerprint: lowercase_sha256
  trusted_event_sequence: positive_safe_integer
  F3_outcome_assessment_id: stable_ref
  expected_assessment_revision: positive_safe_integer
  expected_assessment_fingerprint: lowercase_sha256
```

The exact F3 outcome context is:

```text
SHA256(domain || candidate_ref || candidate_revision || candidate_fingerprint)
```

An acknowledgement may report `ACKNOWLEDGED_COMMITTED` only when the resolved
assessment satisfies all of:

```text
owner_contract == F3
assessment_kind == F3_INTAKE_OUTCOME
assessment revision and fingerprint equal the consumer commitment
subject_ref == handoff_candidate_ref
subject_revision == handoff_candidate_revision
subject_fingerprint == handoff_candidate_fingerprint
context_fingerprint == exact F3 outcome context
is_current_head == true
based_on_event_sequence >= trusted_event_sequence
result == SYNTHETIC_TEST_COMMITTED
```

Any missing, malformed, wrong-revision, wrong-fingerprint, wrong-subject,
wrong-context, stale-head, behind-watermark or indeterminate input returns
`ACKNOWLEDGED_INDETERMINATE`. It cannot create Command authority, Task-write
authority, effect authority or runtime usability.

## 6. Closed schema totality

R2 requires validation of every field before any object or section fingerprint
is trusted. Fixture anchors prove immutable test inventory only; they never
substitute for target-schema validation.

Closed primitive profiles are:

```yaml
stable_ref: strict JSON string, nonempty, NFC
lowercase_sha256: strict JSON string matching ^[0-9a-f]{64}$
positive_safe_integer: strict JSON integer in 1..9007199254740991, excluding booleans
non_negative_safe_integer: strict JSON integer in 0..9007199254740991, excluding booleans
strict_json_boolean: exactly true or false
closed_enum: exact listed string value
nullable_T: either null or a value satisfying T
```

Every object validates:

```text
exact field inventory
every primitive type and range
every closed enum
all-or-none nullable tuples
cross-field result/reason/authority rules
predecessor revision and fingerprint rules
assessment kind/owner/result/context rules
candidate and acknowledgement exact subject rules
section inventory and root inventory
duplicate JSON key rejection
float, NaN and Infinity rejection
NFC string enforcement
```

In particular, all candidate refs including `created_event_ref` are validated
as `stable_ref`. The validator must reject invalid objects with
`enforce_anchors=false`, proving that the target schema—not fixture equality—
caused rejection. Malformed inputs return stable `BLOCK` errors and never an
uncaught exception.

## 7. Accepted direction inputs

The R2 atomic manifest must add the exact accepted direction inputs named by
the immutable F8 start decision:

```yaml
resident_architecture:
  path: control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
  sha256: 12e8984ad24f67d58d26ef9debf605317b0761a6e4f0181ade328567af52373e
high_privilege_architecture:
  path: control-plane/registry/decisions/2026-07-12-agents-os-vcp-high-privilege-architecture-v0.1.md
  sha256: 9b3a8ecf80ab1a8c7cba120f46d0ec70bab437040dda3c7a468cbe5623875a71
```

They are direction inputs only. R2 does not activate a Resident, provider,
high-privilege tool, service or runtime.

## 8. Offline whitespace validation

R2 replaces the Git-worktree-dependent author command with a package-local
deterministic validator invocation:

```text
python3 validator/validate-f8-r2-witness.py --check-whitespace \
  subjects/F8-R2-amendment.md \
  validator/build-f8-r2-witness.py \
  validator/validate-f8-r2-witness.py \
  fixture/F8-R2-synthetic-witness.json
```

The check rejects CRLF, tabs, trailing spaces, missing terminal LF and more
than one terminal LF. It does not require `.git` and is reproducible from the
offline ZIP. The unchanged R1 subjects remain covered by their exact manifest
hashes; R2 does not normalize or silently rewrite their historical whitespace.

## 9. Required R2 regressions

The fixed R2 witness and validator must fully re-sign and reject at least:

```text
required_intake_results reorder
same-revision assessment result/current-head rewrite with old consumer fingerprint
same-revision assessment rewrite plus candidate assessment-set left on old fingerprint
consumer expected assessment fingerprint substitution
acknowledgement wrong candidate subject revision
acknowledgement watermark behind trusted sequence
acknowledgement context mismatch
acknowledgement assessment fingerprint mismatch
candidate created_event_ref integer with fixture anchors disabled
unknown root, row and nested fields with anchors disabled
wrong stable_ref, enum, boolean, integer, hash and nullable tuple types
candidate predecessor cross-field contradiction
acknowledgement favorable-result cross-field contradiction
synthetic object marked runtime usable
nonzero real Command, provider or effect occurrence
```

The three R1 favorable invalid attacks `A21`, `A22` and `A23` are mandatory R2
regressions. Rejection must arise from the intended R2 fingerprint,
acknowledgement-currentness or target-schema rule—not a stale dependent hash,
fixture anchor mismatch or exception.

## 10. Stop and governance rule

The R2 author result may be only
`PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW`. It is not an independent result and
does not accept or freeze F8.

```yaml
F8_started: true
F8_accepted: false
F8_frozen: false
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
provider_or_effect_execution_authorized: false
```

The next gate is one fresh full atomic hash-bound independent review of the
unchanged four R1 subjects plus the four new R2 subjects and every declared
authority/evidence input. Partial review is forbidden.
