# AGENTS OS F6 Validation Requirement Current Decision v0.1 R1 Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-17  
Owner: Jenn  
Agent steward: Nobao  
Acceptance unit: `F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R1_ATOMIC_BUNDLE`

## 1. Scope, authority, and atomic unit

F6 closes the deterministic current decision for one exact
`ValidationRequirement` revision and the fail-closed eligibility gate for one
Task to enter `DONE`. It consumes accepted F1 facts, the frozen F3 canonical
writer/read-barrier interface, and an F5 currentness assessment only when an
exact Requirement explicitly binds delivery evidence.

The complete R1 acceptance unit is:

```text
normative contract
+ deterministic synthetic fixture builder
+ fixed synthetic nonauthority fixture
+ independent offline semantic validator
```

Partial acceptance is forbidden. R1 has no earlier F6 revision. A later
amendment may replace only clauses it names explicitly.

F6 owns:

```text
ValidationRequirement identity, revision, provenance and closed semantics
immutable Validation Set snapshot membership binding
append-only Validation attempt state-chain validation
Requirement waiver currentness for the exact Task/result/epoch binding
deterministic current Requirement decision
deterministic current Validation Set decision
Task completion eligibility at one F3 current-read barrier
the required atomic seam for COMPLETION_ASSESSMENT + DONE
```

F6 does not own and MUST NOT recompute:

```text
F1 Goal, Task scope, Task lifecycle authority, result authority, success
  criteria, plan membership, dependency closure or completion assurance
F2 Actor, Principal, Binding, responsibility, delegation or authentication
F3 Resident identity, Command authentication, canonical writer, Event ordering,
  replay, intake or read-barrier authority
F4 permit, Host authentication, effect admission or fences
F5 delivery, receipt, retry, dead-letter, effect outcome or reconciliation
policy/PBL/Jenn authority decisions owned by their accepted source contracts
```

F6 verifies refs, fingerprints, revisions, watermarks, closed result literals
and equality. It never rebuilds an upstream reducer from role names, colors,
relationships, trust, urgency, historical success or natural-language labels.

## 2. Fixed predecessor bindings

```yaml
F1:
  acceptance_unit: F1_GOAL_SPECIFICATION_SUCCESS_CRITERIA_PLAN_MEMBERSHIP_V0_1_R3_ATOMIC_BUNDLE
  acceptance_decision_sha256: e49e572055b8e367d38cc70297f5ee144482f4023c62aa46e74de35d999977b2
F3:
  acceptance_unit: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
  manifest_sha256: 3075cda63fcb2c7937cb800a3bc09cc830d17e2f98b899828db15e09ab9f79ff
  freeze_decision_sha256: f692ef1a1af8ac15f40c8af696f486240b73a3ddf391633078e31f17eaf62529
F5:
  acceptance_unit: F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R7_ATOMIC_BUNDLE
  manifest_sha256: 2c867bcab4810f5625caa3cb7a649209e19fc53eab34d6ba16737dcce8d14031
  freeze_decision_sha256: 73270ad50c639be792f252e55befcf93c3dcc3edfffc74cb11c7c0fd212d7dbb
F6_start:
  decision_sha256: 335c838830fce9d6f48dedfcdd5bd07c2be5eacba1a3ec61962305fccae6f30f
```

F1 remains authoritative for `SuccessCriterionDecision`. F6 does not use a
Task Validation result to synthesize a Goal criterion decision. Goal closure
continues to use F1's exact Jenn/Nobao/policy authority and closure basis.

F5 remains authoritative for delivery/effect accounting. `ACKED`,
`APPLIED_CURRENT`, `SUCCEEDED`, `FAILED`, dead-letter or reconciliation is
never a Validation `PASSED` result by itself. An effectful Requirement still
needs a separately committed, current Validation attempt whose evidence may
include the exact F5 assessment.

## 3. Canonical encoding, identifiers, and validation order

Every F6 canonical value uses:

```text
encoding: UTF-8
strings: Unicode NFC
JSON objects: lexical key order for canonicalization
numbers: integers only, -(2^53-1) through 2^53-1
booleans: never accepted as integers
arrays: exact contract-defined business-key order
duplicate keys or array business keys: reject
unknown fields or enum values: reject
digest: SHA-256 lowercase hexadecimal
```

Canonical fingerprints are:

```text
SHA-256(
  UTF8(domain_tag)
  + 0x00
  + JCS(object_without_canonical_fingerprint)
)
```

Derived stable IDs use the same function over the exact identity tuple and a
distinct domain tag. A caller-supplied ID that does not match the formula is
rejected even when every dependent reference and fingerprint is re-signed.

Validation order is mandatory:

```text
1. strict-decode bytes and reject duplicate keys
2. recursively enforce scalar types, safe integers and NFC
3. enforce closed root/section/row field inventories and enum matrices
4. recompute every stable ID from its complete identity tuple
5. recompute every object and section fingerprint
6. verify reference targets, exact revisions and graph acyclicity
7. verify F3 read-barrier and all upstream-assessment bindings
8. derive attempt heads, waiver currentness and all F6 decisions
9. compare derived values with any rendered witness expectations
```

Fingerprints are integrity evidence, not semantic authority. Passing a hash
check never skips Steps 3 through 9.

## 4. Closed normative schemas

R1 freezes ten logical schemas. They are contract shapes, not a database or
implementation layout.

### 4.1 `F3CanonicalReadBarrierInputV0_1R1`

```yaml
interface_version: agents-os.f6-f3-read-barrier-input.v0.1-r1
barrier_id: lowercase_sha256
resident_identity_ref: stable_ref
resident_authority_epoch: positive_safe_integer
schema_contract_set_fingerprint: lowercase_sha256
start_event_sequence: non_negative_safe_integer
end_event_sequence: non_negative_safe_integer
f3_result: CURRENT | INDETERMINATE
canonical_fingerprint: lowercase_sha256
```

`barrier_id` is derived from the Resident identity, epoch, schema fingerprint
and both sequences. F6 accepts a usable barrier only when:

```text
f3_result == CURRENT
start_event_sequence == end_event_sequence
the F3 interface version and fingerprint are recognized
```

F6 does not decide Resident continuity or writer ownership. A changed head or
`INDETERMINATE` barrier requires a complete retry from a new F3 barrier.

### 4.2 `TrustedTimeInputV0_1R1`

```yaml
interface_version: agents-os.f6-trusted-time-input.v0.1-r1
trusted_time_ref: stable_ref
as_of_utc_ms: non_negative_safe_integer
time_policy_ref: stable_ref
time_policy_fingerprint: lowercase_sha256
result: CURRENT | INDETERMINATE
read_barrier_ref: lowercase_sha256
read_barrier_fingerprint: lowercase_sha256
assessed_at_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

Time is only usable when `result == CURRENT`, its barrier is the exact current
F3 barrier, and `assessed_at_event_sequence` equals the barrier head. F6 does
not infer current time from file timestamps, UI clocks or caller input.

### 4.3 `OpaqueUpstreamAssessmentInputV0_1R1`

```yaml
interface_version: agents-os.f6-upstream-assessment-input.v0.1-r1
assessment_ref: stable_ref
owner_contract: F1 | F3 | F5 | ACCEPTED_EVIDENCE_OWNER | ACCEPTED_COMPLETION_GUARD_OWNER
assessment_kind:
  TASK_CURRENTNESS
  | CANDIDATE_COMMITMENT_CURRENTNESS
  | DEPENDENCY_CLOSURE_CURRENTNESS
  | VALIDATION_AUTHORITY_CURRENTNESS
  | EVIDENCE_CURRENTNESS
  | F5_DELIVERY_CURRENTNESS
  | COMPLETION_GUARD_CURRENTNESS
subject_ref: stable_ref
subject_revision: non_negative_safe_integer
subject_fingerprint: lowercase_sha256
result:
  CURRENT
  | CURRENT_ACCEPTED
  | CURRENT_CONFIRMED
  | CLEAR
  | BLOCKED
  | APPLIED_CURRENT
  | TIMELESS
  | STALE
  | CHALLENGED
  | INVALIDATED
  | REJECTED
  | INDETERMINATE
  | HISTORY_ONLY
read_barrier_ref: lowercase_sha256
read_barrier_fingerprint: lowercase_sha256
assessed_at_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

The allowed owner/kind/result matrix is closed:

| owner / kind | usable positive result |
|---|---|
| F1 / TASK_CURRENTNESS | CURRENT |
| F1 / CANDIDATE_COMMITMENT_CURRENTNESS | CURRENT |
| F1 / DEPENDENCY_CLOSURE_CURRENTNESS | CURRENT_CONFIRMED |
| F3 / VALIDATION_AUTHORITY_CURRENTNESS | CURRENT_ACCEPTED |
| ACCEPTED_EVIDENCE_OWNER / EVIDENCE_CURRENTNESS | CURRENT or TIMELESS |
| F5 / F5_DELIVERY_CURRENTNESS | APPLIED_CURRENT or CLEAR, as required by the exact consumer |
| ACCEPTED_COMPLETION_GUARD_OWNER / COMPLETION_GUARD_CURRENTNESS | CURRENT |

F6 consumes the value. It does not reconstruct why the owner produced it.
Unknown kind, owner mismatch, unavailable owner version, barrier mismatch or
non-current watermark is `INDETERMINATE` for the affected F6 decision.

For Task completion, F6 derives the exact assessment subject fingerprint:

```text
task_completion_context_fingerprint = typed_hash(
  "agents-os.f6.task-completion-context.v0.1-r1",
  {task_id, lifecycle_generation, completion_epoch, task_spec_revision,
   result_revision}
)
```

Both `TASK_CURRENTNESS` and completion-blocking `F5_DELIVERY_CURRENTNESS`
must name the exact `task_id` and this fingerprint. Their result literals are
still owned by F1 and F5; F6 verifies only exact subject binding.

`BLOCKED` is a recognized known-negative completion result and never appears
in a positive row. `CLEAR | BLOCKED` is a prospective F5 owner-interface requirement for the
completion consumer, not an amendment to frozen F5 bytes. Its status in R1 is
`UNACCEPTED_OWNER_INTERFACE_REQUIREMENT`, `runtime_usable=false` and
`synthetic_fixture_only=true`. No real F6 eligibility decision is issuable
until a separately accepted implementation/owner profile materializes that
assessment from frozen F5 projection semantics. This limitation does not let
F6 recompute or invent F5 outcomes.

The execution/Validation/control/effect counts in the completion input are
not caller assertions. They are bound by a prospective completion-guard owner
assessment whose exact subject fingerprint is:

```text
typed_hash(
  "agents-os.f6.completion-guard-subject.v0.1-r1",
  {task_id, lifecycle_generation, completion_epoch, task_spec_revision,
   result_revision, current_nonterminal_execution_run_count,
   current_nonterminal_validation_count, active_control_intent_count,
   unknown_effect_count, completion_blocking_effect_count}
)
```

This second prospective interface has the same
`UNACCEPTED_OWNER_INTERFACE_REQUIREMENT`, `runtime_usable=false` and
`synthetic_fixture_only=true` boundary. Until separately accepted, the counts
cannot support a real positive eligibility decision.

### 4.4 `ValidationRequirementRevisionV0_1R1`

```yaml
interface_version: agents-os.validation-requirement.v0.1-r1
task_id: lowercase_sha256
requirement_id: lowercase_sha256
requirement_revision: positive_safe_integer
task_spec_revision: positive_safe_integer
canonical_requirement_key: stable_ref
semantic_digest: lowercase_sha256
provenance_bindings:
  - source_kind: NOBAO_TASK_SPEC | RUST_POLICY | GOAL_DOMAIN_CONTRACT | JENN_EXPLICIT
    source_ref: stable_ref
    source_revision: positive_safe_integer
    source_fingerprint: lowercase_sha256
    effective_scope: THIS_TASK | OPEN_TASKS | FUTURE_ONLY
    nonwaivable: boolean
provenance_set_fingerprint: lowercase_sha256
validation_type: DETERMINISTIC | RUNTIME_OBSERVATION | INDEPENDENT_REVIEW | HUMAN_ACCEPTANCE
acceptance_predicate_ref: stable_ref
acceptance_predicate_fingerprint: lowercase_sha256
result_scope_ref: stable_ref
result_scope_fingerprint: lowercase_sha256
validator_contract_ref: stable_ref
validator_contract_version: stable_ref
validator_contract_fingerprint: lowercase_sha256
enforcement_phase: POST_RESULT_VALIDATION
requiredness: REQUIRED | OPTIONAL
waivability: NON_WAIVABLE | JENN_WAIVABLE
waiver_duration_policy: NOT_APPLICABLE | COMPLETION_SCOPED_ONLY | EXPIRY_REQUIRED
evidence_reuse_mode: NEVER_REUSE | REVALIDATE_WITH_OLD_EVIDENCE | CONDITIONAL_CARRY_FORWARD
carry_forward_equivalence_contract_ref: null | stable_ref
carry_forward_equivalence_contract_version: null | stable_ref
carry_forward_equivalence_contract_fingerprint: null | lowercase_sha256
evidence_freshness_mode: FRESH_AT_DECISION | IMMUTABLE_WHEN_FINGERPRINT_MATCHES | EXPIRES_AT
evidence_max_age_ms: null | positive_safe_integer
effectful_delivery_binding_required: boolean
effectful_delivery_subject_ref: null | stable_ref
effectful_delivery_subject_fingerprint: null | lowercase_sha256
supersedes_requirement_revision: null | positive_safe_integer
created_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

Identity is:

```text
requirement_id = typed_id(
  "agents-os.f6.requirement-id.v0.1-r1",
  {task_id, canonical_requirement_key}
)
```

Revision 1 has no predecessor. Every later revision is exact predecessor plus
one and names it. Revision rollback, gaps and reuse for another key reject.

`provenance_bindings` are sorted by `(source_kind, source_ref,
source_revision)`, duplicate-free and exact. Any `nonwaivable=true` source
makes the effective Requirement `NON_WAIVABLE + NOT_APPLICABLE`.

Cross-field rules:

```text
NON_WAIVABLE -> NOT_APPLICABLE
JENN_WAIVABLE -> COMPLETION_SCOPED_ONLY or EXPIRY_REQUIRED
HUMAN_ACCEPTANCE -> NEVER_REUSE + FRESH_AT_DECISION
effectful delivery -> NEVER_REUSE + FRESH_AT_DECISION
effectful delivery -> both exact F5 delivery subject fields present
non-effectful delivery -> both exact F5 delivery subject fields null
CONDITIONAL_CARRY_FORWARD -> DETERMINISTIC, no effectful delivery, all three
  equivalence-contract fields present, and freshness is IMMUTABLE... or EXPIRES_AT
EXPIRES_AT -> evidence_max_age_ms present
other freshness modes -> evidence_max_age_ms null
other reuse modes -> carry-forward contract fields null
```

For `EXPIRES_AT`, the canonical attempt derives
`evidence_expires_at_utc_ms = evidence_observed_at_utc_ms +
evidence_max_age_ms`; supplied expiry values are not trusted. The evidence is
unusable when trusted time is at or after that exact derived expiry.

F6 does not allow `PRE_EXECUTION_SAFETY` to be disguised as result Validation.
Such safety remains F4/F5/host policy.

### 4.5 `RequirementWaiverEventV0_1R1`

```yaml
interface_version: agents-os.requirement-waiver-event.v0.1-r1
waiver_id: lowercase_sha256
waiver_event_id: lowercase_sha256
waiver_event_index: positive_safe_integer
prior_waiver_event_fingerprint: null | lowercase_sha256
operation: GRANT | REVOKE | EXPIRE | INVALIDATE
task_id: lowercase_sha256
requirement_id: lowercase_sha256
requirement_revision: positive_safe_integer
lifecycle_generation: positive_safe_integer
completion_epoch: positive_safe_integer
task_spec_revision: positive_safe_integer
result_revision: positive_safe_integer
base_snapshot_id: lowercase_sha256
jenn_decision_ref: null | stable_ref
jenn_decision_fingerprint: null | lowercase_sha256
jenn_decision_result: NOT_APPLICABLE | CURRENT_ACCEPTED | INDETERMINATE | REJECTED
reason_ref: stable_ref
risk_acknowledgement_ref: null | stable_ref
review_at_utc_ms: null | positive_safe_integer
expires_at_utc_ms: null | positive_safe_integer
follow_up_task_ref: null | stable_ref
event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

`waiver_id` binds Task, Requirement revision, lifecycle generation, completion
epoch, Task spec and result. `waiver_event_id` additionally binds the event
index and operation. Only `GRANT` has an exact Jenn decision and risk
acknowledgement. The first event is `GRANT`; later events are contiguous,
single-head, prior-fingerprint-bound terminal invalidations. Branches, gaps,
multiple heads or an unavailable Jenn decision are invalid.

`EXPIRY_REQUIRED` grant requires a future expiry and durable nonterminal
follow-up Task ref. `COMPLETION_SCOPED_ONLY` requires `review_at_utc_ms` and no
expiry. A grant for `NON_WAIVABLE`, a grant while a current `FAILED` attempt
exists, or a grant that attempts partial waiver is invalid. `REVOKE`, `EXPIRE`
and `INVALIDATE` never fall back to an older grant.

### 4.6 `ValidationSetSnapshotV0_1R1`

```yaml
interface_version: agents-os.validation-set-snapshot.v0.1-r1
snapshot_id: lowercase_sha256
task_id: lowercase_sha256
lifecycle_generation: positive_safe_integer
completion_epoch: positive_safe_integer
task_spec_revision: positive_safe_integer
result_revision: positive_safe_integer
validation_set_revision: positive_safe_integer
base_snapshot_id: null | lowercase_sha256
freeze_trigger: FIRST_RUN | FIRST_FORMAL_VALIDATION | FIRST_VERIFYING | EXTENSION | WAIVER_CHANGE
memberships:
  - requirement_id: lowercase_sha256
    requirement_revision: positive_safe_integer
    requirement_fingerprint: lowercase_sha256
    active_waiver_id: null | lowercase_sha256
    active_waiver_event_fingerprint: null | lowercase_sha256
membership_set_fingerprint: lowercase_sha256
source_bindings:
  - source_ref: stable_ref
    source_revision: positive_safe_integer
    source_fingerprint: lowercase_sha256
source_set_fingerprint: lowercase_sha256
frozen_event_ref: stable_ref
frozen_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

Memberships are sorted by `requirement_id`, unique and exact. Source bindings
are the duplicate-free exact union of every current member Requirement's
provenance projected to `(source_ref, source_revision, source_fingerprint)`,
sorted by `(source_ref, source_revision)`. Omission, substitution or an
inconsistent fingerprint rejects the snapshot. Snapshot ID binds the complete
Task/result/epoch tuple, revision, base, both set fingerprints and freeze
trigger. An old snapshot is immutable and never becomes current again.

Revision 1 has no base. Later revisions name the current predecessor and are
exact predecessor plus one. A current snapshot with zero current REQUIRED
members may be historically valid but can never satisfy Task completion.
Snapshot freeze Event sequences strictly advance and cannot exceed the F3
barrier head used by the decision.

`active_waiver_id` and its event fingerprint are both null or both present.
Presence does not itself prove validity; F6 independently reduces the exact
waiver Event chain at the current barrier and trusted time.

A current snapshot cannot materialize a Requirement whose only or any
governing provenance binding is `FUTURE_ONLY`; that source has not become
current authority for this Task. F6 does not reinterpret the scope label.

### 4.7 `ValidationAttemptRevisionV0_1R1`

```yaml
interface_version: agents-os.validation-attempt-revision.v0.1-r1
attempt_id: lowercase_sha256
attempt_number: positive_safe_integer
attempt_revision: positive_safe_integer
prior_attempt_revision_fingerprint: null | lowercase_sha256
task_id: lowercase_sha256
requirement_id: lowercase_sha256
requirement_revision: positive_safe_integer
requirement_fingerprint: lowercase_sha256
validation_set_snapshot_id: lowercase_sha256
validation_set_snapshot_fingerprint: lowercase_sha256
lifecycle_generation: positive_safe_integer
completion_epoch: positive_safe_integer
task_spec_revision: positive_safe_integer
result_revision: positive_safe_integer
candidate_commitment_ref: stable_ref
candidate_commitment_fingerprint: lowercase_sha256
dependency_closure_ref: stable_ref
dependency_closure_fingerprint: lowercase_sha256
validation_type: DETERMINISTIC | RUNTIME_OBSERVATION | INDEPENDENT_REVIEW | HUMAN_ACCEPTANCE
validation_method: FRESH_VALIDATION | EVIDENCE_CARRY_FORWARD_REVIEW
state: PENDING | RUNNING | PASSED | FAILED | INCONCLUSIVE | ERROR | CANCELLED
committed_event_ref: stable_ref
committed_event_sequence: non_negative_safe_integer
command_envelope_ref: stable_ref
command_envelope_fingerprint: lowercase_sha256
authority_assessment_ref: stable_ref
authority_assessment_fingerprint: lowercase_sha256
authority_assessment_result: CURRENT_ACCEPTED | REJECTED | INDETERMINATE
evidence_refs: [stable_ref]
evidence_digest: null | lowercase_sha256
evidence_currentness_ref: null | stable_ref
evidence_currentness_fingerprint: null | lowercase_sha256
evidence_currentness_result: NOT_APPLICABLE | CURRENT | TIMELESS | STALE | INDETERMINATE
evidence_observed_at_utc_ms: null | non_negative_safe_integer
evidence_expires_at_utc_ms: null | positive_safe_integer
source_validation_id: null | lowercase_sha256
root_source_validation_id: null | lowercase_sha256
equivalence_fingerprint: null | lowercase_sha256
f5_delivery_assessment_ref: null | stable_ref
f5_delivery_assessment_fingerprint: null | lowercase_sha256
f5_delivery_assessment_result: NOT_REQUIRED | APPLIED_CURRENT | HISTORY_ONLY | INDETERMINATE
canonical_fingerprint: lowercase_sha256
```

Attempt identity is derived from:

```text
task_id + requirement_id + requirement_revision + lifecycle_generation
+ completion_epoch + task_spec_revision + result_revision + attempt_number
```

For one exact binding, attempt numbers begin at 1 and are contiguous. Each
attempt has one contiguous revision chain beginning with `PENDING`. Allowed
transitions are:

```text
PENDING -> RUNNING | CANCELLED
RUNNING -> PASSED | FAILED | INCONCLUSIVE | ERROR | CANCELLED
terminal -> no successor
```

Every revision repeats the exact immutable binding and authority assessment.
A mismatch, branch, gap, duplicate number, duplicate revision or invalid
transition makes the affected Requirement decision `INDETERMINATE`.
Revision Event sequences strictly advance; all Requirement creation, waiver,
snapshot and attempt Events consumed by a decision must be at or before its
single F3 barrier head.

The `VALIDATION_AUTHORITY_CURRENTNESS` assessment subject must be the exact
Requirement validator contract ref/fingerprint. F6 does not infer validator
authority from the Command label, Actor class, role or caller.

Terminal `PASSED`, `FAILED` and `INCONCLUSIVE` require nonempty evidence refs,
an evidence digest and an exact evidence-currentness assessment. `PASSED`
requires `CURRENT` or `TIMELESS` plus the Requirement freshness contract.
`ERROR` describes validator failure; it is not a failed result. `CANCELLED`
and nonterminal states have no completion authority.

`EVIDENCE_CARRY_FORWARD_REVIEW` requires a
`CONDITIONAL_CARRY_FORWARD` Requirement, exact current equivalence
fingerprint, and a source/root source that is the same original
`FRESH_VALIDATION + PASSED` attempt. A carry-forward attempt can never become
the next source. `HUMAN_ACCEPTANCE`, effectful, UNKNOWN-linked or
`NEVER_REUSE` Requirements reject carry-forward.

The equivalence fingerprint is derived, never asserted:

```text
equivalence_fingerprint = typed_hash(
  "agents-os.f6.carry-forward-equivalence.v0.1-r1",
  {
    source_validation_id,
    source_evidence_digest,
    task_id,
    requirement_id,
    requirement_revision,
    lifecycle_generation,
    completion_epoch,
    task_spec_revision,
    result_revision,
    validator_contract_fingerprint,
    carry_forward_equivalence_contract_fingerprint,
    result_scope_fingerprint,
    evidence_currentness_fingerprint
  }
)
```

The named source must resolve to the unique head of an earlier original
`FRESH_VALIDATION + PASSED` chain for the same Task and Requirement revision.
`source_validation_id == root_source_validation_id`; the source cannot itself
be a carry-forward, and its committed Event sequence must precede the current
attempt.

For `effectful_delivery_binding_required=true`, all three F5 fields are
present, the assessment subject ref/fingerprint exactly equals the Requirement
delivery subject binding, and the current usable value is `APPLIED_CURRENT`.
For every other
Requirement they are exactly `null, null, NOT_REQUIRED`. Even
`APPLIED_CURRENT` cannot produce `PASSED`; it only supports currentness of an
independently committed Validation outcome.

### 4.8 `ValidationRequirementCurrentDecisionV0_1R1`

```yaml
interface_version: agents-os.validation-requirement-current-decision.v0.1-r1
task_id: lowercase_sha256
requirement_id: lowercase_sha256
requirement_revision: positive_safe_integer
validation_set_snapshot_id: lowercase_sha256
read_barrier_ref: lowercase_sha256
read_barrier_fingerprint: lowercase_sha256
result: SATISFIED | UNSATISFIED | WAIVED | PENDING | NOT_REQUIRED | INDETERMINATE
current_attempt_id: null | lowercase_sha256
current_attempt_revision_fingerprint: null | lowercase_sha256
current_waiver_id: null | lowercase_sha256
current_waiver_event_fingerprint: null | lowercase_sha256
primary_reason: closed_reason_code
reason_codes: sorted_unique_closed_set
assessed_at_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

This is a deterministic F6 projection. It is not a caller assertion, mutable
boolean or permission grant.

### 4.9 `ValidationSetCurrentDecisionV0_1R1`

```yaml
interface_version: agents-os.validation-set-current-decision.v0.1-r1
task_id: lowercase_sha256
validation_set_snapshot_id: lowercase_sha256
read_barrier_ref: lowercase_sha256
read_barrier_fingerprint: lowercase_sha256
requirement_decision_refs: [lowercase_sha256]
result: SATISFIED | NOT_SATISFIED | INDETERMINATE
current_required_count: non_negative_safe_integer
current_unwaived_required_pass_count: non_negative_safe_integer
nonterminal_attempt_count: non_negative_safe_integer
primary_reason: closed_reason_code
reason_codes: sorted_unique_closed_set
assessed_at_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

### 4.10 `TaskCompletionEligibilityDecisionV0_1R1`

Input binds:

```yaml
interface_version: agents-os.task-completion-eligibility-input.v0.1-r1
task_id: lowercase_sha256
lifecycle_generation: positive_safe_integer
completion_epoch: positive_safe_integer
task_spec_revision: positive_safe_integer
result_revision: positive_safe_integer
task_lifecycle: READY | ACTIVE | WAITING | PAUSED | BLOCKED | VERIFYING | DONE | FAILED | CANCELLED
task_currentness_assessment_ref: stable_ref
task_currentness_assessment_fingerprint: lowercase_sha256
candidate_commitment_ref: stable_ref
candidate_commitment_fingerprint: lowercase_sha256
candidate_currentness_assessment_ref: stable_ref
candidate_currentness_assessment_fingerprint: lowercase_sha256
validation_set_snapshot_id: lowercase_sha256
validation_set_snapshot_fingerprint: lowercase_sha256
dependency_closure_ref: stable_ref
dependency_closure_fingerprint: lowercase_sha256
dependency_currentness_assessment_ref: stable_ref
dependency_currentness_assessment_fingerprint: lowercase_sha256
f5_completion_blocking_assessment_ref: stable_ref
f5_completion_blocking_assessment_fingerprint: lowercase_sha256
current_nonterminal_execution_run_count: non_negative_safe_integer
current_nonterminal_validation_count: non_negative_safe_integer
active_control_intent_count: non_negative_safe_integer
unknown_effect_count: non_negative_safe_integer
completion_blocking_effect_count: non_negative_safe_integer
completion_guard_currentness_assessment_ref: stable_ref
completion_guard_currentness_assessment_fingerprint: lowercase_sha256
read_barrier_ref: lowercase_sha256
read_barrier_fingerprint: lowercase_sha256
trusted_time_ref: stable_ref
trusted_time_fingerprint: lowercase_sha256
canonical_fingerprint: lowercase_sha256
```

Output is:

```yaml
interface_version: agents-os.task-completion-eligibility-decision.v0.1-r1
task_id: lowercase_sha256
lifecycle_generation: positive_safe_integer
completion_epoch: positive_safe_integer
task_spec_revision: positive_safe_integer
result_revision: positive_safe_integer
result: ELIGIBLE | NOT_ELIGIBLE | INDETERMINATE
validation_set_decision_ref: lowercase_sha256
completion_assessment_snapshot_may_be_created: boolean
task_done_may_be_committed: boolean
primary_reason: closed_reason_code
reason_codes: sorted_unique_closed_set
read_barrier_ref: lowercase_sha256
read_barrier_fingerprint: lowercase_sha256
assessed_at_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

The fixture models the input and derived result only. It never creates this
canonical output or a Task mutation.

## 5. Attempt-head and waiver reduction

### 5.1 Current attempt head

For one exact Requirement binding, F6 reads the complete attempt/revision set
through one F3 barrier.

```text
validate every attempt identity and revision chain
-> reject any branch, gap, duplicate, cross-binding or invalid transition
-> order attempts by contiguous attempt_number
-> current attempt is the highest attempt_number
-> current attempt state is its unique chain head
```

F6 does not choose the most favorable historical attempt. Starting a newer
attempt makes its nonterminal or terminal head the current attempt. Earlier
`PASSED` facts remain history and cannot mask a later `FAILED`, `ERROR`,
`INCONCLUSIVE`, `CANCELLED`, `PENDING` or `RUNNING` attempt.

### 5.2 Current waiver

F6 validates the exact waiver chain referenced by the snapshot membership.

```text
no waiver ref -> no current waiver
valid GRANT head and all Task/result/epoch/spec/snapshot fields exact
  + current Jenn decision + duration/follow-up guards -> active waiver
REVOKE / EXPIRE / INVALIDATE head -> no active waiver
time at or after expires_at -> no active waiver and expiry reconciliation required
branch/gap/mismatch/unavailable Jenn decision -> INDETERMINATE
```

A waiver never changes an attempt state and never creates `SATISFIED`.

## 6. Total Requirement decision reducer

All true reasons are collected, de-duplicated and lexically sorted.
`primary_reason` is the first true reason in the frozen precedence list below.

```text
REQUIREMENT_INPUT_INTEGRITY_FAILURE
REQUIREMENT_BINDING_UNAVAILABLE
ATTEMPT_CHAIN_CORRUPT
ATTEMPT_AUTHORITY_UNAVAILABLE
EVIDENCE_UNAVAILABLE
CARRY_FORWARD_INVALID
F5_DELIVERY_UNAVAILABLE
WAIVER_INVALID
LATEST_ATTEMPT_FAILED
CURRENT_PASS_MISSING
REQUIREMENT_OPTIONAL
REQUIREMENT_WAIVED
VALIDATION_PASSED
```

Total result matrix:

```text
any of the first eight reasons
  -> INDETERMINATE

requiredness == OPTIONAL, with no integrity/currentness failure
  -> NOT_REQUIRED

valid active waiver, no current FAILED attempt, no integrity failure
  -> WAIVED

no current attempt, or head PENDING/RUNNING/CANCELLED
  -> PENDING

head FAILED
  -> UNSATISFIED

head INCONCLUSIVE or ERROR
  -> INDETERMINATE

head PASSED + current authority + current/timeless evidence + valid freshness
  + valid carry-forward when applicable + required F5 currentness when applicable
  -> SATISFIED
```

Known failure and unknown evidence remain distinct. A `FAILED` attempt is
`UNSATISFIED`; evidence or reducer uncertainty is `INDETERMINATE`. Neither is
automatic Task `FAILED`.

## 7. Total Validation Set decision reducer

Reason precedence:

```text
VALIDATION_SET_INPUT_INTEGRITY_FAILURE
SNAPSHOT_CURRENTNESS_UNAVAILABLE
REQUIREMENT_DECISION_INDETERMINATE
EMPTY_REQUIRED_SET
REQUIRED_REQUIREMENT_NOT_SATISFIED
NO_REAL_REQUIRED_PASS
NONTERMINAL_VALIDATION_PRESENT
ALL_REQUIRED_CURRENTLY_SATISFIED
```

Reduction:

```text
integrity, snapshot currentness or any Requirement INDETERMINATE
  -> INDETERMINATE

zero current REQUIRED members
  -> NOT_SATISFIED

any unwaived REQUIRED decision not SATISFIED
  -> NOT_SATISFIED

any current nonterminal attempt
  -> NOT_SATISFIED

zero current, nonwaived, REQUIRED SATISFIED attempt-backed decisions
  -> NOT_SATISFIED

otherwise
  -> SATISFIED
```

All-required-waived is never completion-satisfying. At least one current,
nonwaived, REQUIRED, real `PASSED` Validation attempt is mandatory. Optional
members do not add or remove completion authority.

## 8. Total Task completion eligibility reducer

Reason precedence:

```text
COMPLETION_INPUT_INTEGRITY_FAILURE
READ_BARRIER_UNAVAILABLE
TASK_CURRENTNESS_UNAVAILABLE
CANDIDATE_CURRENTNESS_UNAVAILABLE
VALIDATION_SET_DECISION_INDETERMINATE
DEPENDENCY_CURRENTNESS_UNAVAILABLE
F5_CURRENTNESS_UNAVAILABLE
TRUSTED_TIME_UNAVAILABLE
TASK_NOT_VERIFYING
CANDIDATE_NOT_CURRENT
VALIDATION_SET_NOT_SATISFIED
DEPENDENCY_NOT_CONFIRMED
NONTERMINAL_WORK_PRESENT
ACTIVE_CONTROL_INTENT
UNRESOLVED_EFFECT_PRESENT
ALL_COMPLETION_GATES_SATISFIED
```

Any of the first eight reasons produces `INDETERMINATE`. Otherwise any known
negative reason produces `NOT_ELIGIBLE`. `ELIGIBLE` requires all of:

```text
one unchanged F3 CURRENT read barrier
trusted time CURRENT at the same barrier
F1 Task currentness == CURRENT for exact task/generation/epoch/spec/result
Task lifecycle == VERIFYING
exact current CANDIDATE_ADOPTION commitment == CURRENT
F6 Validation Set decision == SATISFIED at the same barrier
F1 dependency closure currentness == CURRENT_CONFIRMED
zero current nonterminal execution Runs
zero current nonterminal Validations
zero active or unreconciled Control Intent
zero UNKNOWN effect
zero completion-blocking effect
F5 completion-blocking currentness == CLEAR
```

`Run SUCCEEDED`, F5 `ACKED`, F5 `APPLIED_CURRENT`, plan progress, Goal health,
Worker success, model opinion or UI state is absent from this positive formula.

## 9. Atomic completion seam

An `ELIGIBLE` projection alone does not complete a Task. A future accepted
implementation may commit `DONE` only inside one F3 canonical-writer
transaction that:

```text
re-reads every bound canonical input at one unchanged barrier
re-runs the F6 Requirement, Set and Task eligibility reducers
allocates the next Task commitment revision
creates COMPLETION_ASSESSMENT TaskCommitmentSnapshot with exact current
  Validation decisions, waiver refs, result and dependency closure
appends the Task DONE Event
updates Task Current State and completion ref
commits all or none
```

The transaction must use the same Task CAS as Validation start, Validation
outcome, waiver change, set extension, Task spec/result change, reopen,
Control Intent and dependency/fence change. A concurrent change causes retry
from a new barrier; it never permits a stale decision to commit.

Identical `command_id` replay returns the original committed completion.
Changed bytes under the same ID conflict. Crash before commit leaves no
completion snapshot or DONE Event; crash after commit recovers both. Projection
rebuild creates neither.

## 10. Invalidation and late facts

The historical attempt, decision and completion basis remain append-only.
Changes affect currentness as follows:

| Change | Current effect |
|---|---|
| Requirement/set/task/result/epoch revision change | old decision loses current authority |
| evidence becomes stale/unavailable | affected Requirement becomes INDETERMINATE |
| valid current FAILED attempt | Requirement becomes UNSATISFIED |
| waiver expires/revokes/invalidates | Requirement returns to ordinary attempt reduction |
| F5 fact becomes HISTORY_ONLY/INDETERMINATE | effect-bound Requirement cannot remain SATISFIED |
| dependency assurance CHALLENGED/INVALIDATED/INDETERMINATE | Task completion not eligible |
| post-completion challenge | historical DONE unchanged; F1 reopening/assurance rules decide downstream impact |

F6 never automatically reopens, fails, cancels or completes a Task. It never
turns a late delivery fact into Validation `PASSED` or a Task mutation.

## 11. Synthetic witness and isolation

The R1 fixture is a deterministic contract witness only:

```yaml
environment: SYNTHETIC_TEST
authority_eligible: false
runtime_consumable: false
recovery_importable: false
contains_real_Task_Run_Validation_or_effect: false
task_done_mutation_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

Synthetic IDs use a synthetic-only namespace or deterministic hashes of fixed
synthetic labels. Production readers must reject the fixture schema, root
environment or any `authority_eligible=false` record. Changing the environment
or runtime flags and re-signing the fixture remains invalid.

The positive graph may derive `ELIGIBLE` to prove constructibility. That value
is not a canonical decision, Command, Event, completion snapshot or Task
mutation and cannot be imported into recovery.

## 12. Required adversarial coverage

The fixed validator must independently enforce:

```text
closed root/section/row schemas and all cross-field matrices
safe-integer-without-boolean, no floats, NFC and lowercase hashes
stable ID derivation even after graph-wide ref propagation and re-signing
complete attempt chains, exact transitions, unique numbers and no branches
latest attempt wins; historical favorable PASS cannot mask a later result
waiver source, binding, expiry, revocation and nonwaivable rules
carry-forward roots at one original FRESH PASSED attempt, never a chain
HUMAN_ACCEPTANCE/effect/UNKNOWN evidence never reused
F5 currentness is necessary only when explicitly bound and never sufficient
all-required-waived and empty required set are not completion-satisfying
Requirement/Set/Completion reason precedence is order-independent
one F3 barrier and watermark across every consumed assessment
Task ACTIVE, stale candidate, nonterminal work, Control Intent, UNKNOWN,
  completion-blocking effect or non-confirmed dependency cannot be eligible
Run success, ACK, dead-letter, PBL no-match or role/color labels cannot pass
synthetic fixture cannot become production/runtime/recovery authority
```

Every negative mutation is fully root-re-signed. ID mutations also propagate
dependent refs and recompute object fingerprints so rejection must come from
the identifier formula or semantic rule, not a detached hash mismatch.

## 13. Normative invariants

```text
F6-I01 one Requirement stable ID binds one Task and canonical key forever
F6-I02 revisions, snapshots, attempts and waiver chains are append-only and contiguous
F6-I03 all decisions use one unchanged F3 read barrier and exact current watermarks
F6-I04 F6 consumes upstream assessments and never reimplements their reducers
F6-I05 one attempt satisfies at most one exact Requirement revision and context
F6-I06 the unique head of the highest attempt number is the current attempt
F6-I07 PASSED requires current authority, evidence and freshness; historical existence is insufficient
F6-I08 waiver is never PASSED and all-waived never completes a Task
F6-I09 effect/delivery evidence cannot substitute for Validation PASSED
F6-I10 UNKNOWN, stale, missing, conflict or unsupported version never passes
F6-I11 Task completion requires VERIFYING, current candidate, satisfied set,
        confirmed dependencies and zero unresolved work/effect at one barrier
F6-I12 Run success, Worker declaration, plan progress and UI state cannot complete a Task
F6-I13 COMPLETION_ASSESSMENT + DONE + Current State commit atomically or not at all
F6-I14 projection rebuild, validator execution and synthetic witness create zero authority or effect
F6-I15 no Actor/Task permission level, role, color, relationship, trust or urgency changes a decision
```

## 14. R1 acceptance and stop rule

R1 becomes an acceptance candidate only after:

```text
all four subject hashes fixed
builder reproduces the fixture byte-for-byte
all ten normative schema profiles pass
full positive graph independently derives the rendered decisions
all fixed reducer vectors pass
all reverse-order precedence trials pass
all fully re-signed negative mutations are rejected
all synthetic zero-authority/runtime/effect/secret assertions pass
fresh full atomic hash-bound independent review returns PASS_NO_BLOCKER
```

The author self-review is evidence only and is never independent. A
`PASS_NO_BLOCKER` review may prepare only a Jenn-owned atomic freeze decision
surface. It cannot automatically accept/freeze F6 or start F7.

A later R2 is not preplanned. It requires a new independently reproducible F6
semantic or proof defect. Rust, SQLite, index, cache, performance, production
authentication, provider, service, runtime or F7 implementation-profile
questions do not by themselves trigger R2.

## 15. Non-authorization

This contract and its review package do not authorize:

```text
F6 acceptance or freeze
F7 start
Rust/JavaScript/database/index/cache implementation
Task, Run, Validation, Event, waiver, snapshot or completion mutation
Resident, Worker, Host, validator, dispatcher, service or provider startup
runtime activation or production authentication
real delivery, effect, device, file, process, network or UI execution
secret, credential, raw provider response, state-private or raw Memory access
public API or MCP expansion
commit, push, PR, merge, tag, release, deploy or publish
```
