# AGENTS OS F5 Outbox Delivery / Recovery v0.1 R1 Draft

Status: author-closed review subject; not accepted or frozen
Date: 2026-07-17
Owner: Jenn
Agent steward: Nobao
Acceptance unit: `F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R1_ATOMIC_BUNDLE`

## 1. Scope, authority, and precedence

This contract closes the F5 foundation boundary for transactional Outbox
delivery and recovery. It depends on the frozen F3 and F4 bundles and does not
modify their bytes or reproduce their reducers.

The complete R1 acceptance unit is:

```text
normative contract
+ deterministic synthetic fixture builder
+ fixed synthetic no-effect fixture
+ independent semantic validator
```

Partial acceptance is forbidden. R1 has no earlier F5 revision, so this file
is the complete normative subject. A future amendment may replace only clauses
it names explicitly.

F5 owns:

```text
durable Outbox intent materialization from one committed F4 handoff
claim, lease, fencing, dispatch-arm, attempt and receipt accounting
safe pre-arm claim and lease retry eligibility
dead-letter and UNKNOWN reconciliation
crash-window and startup recovery for those records
```

F5 does not own and MUST NOT recompute:

```text
F1 Task authority or scope
F2 Actor, Principal, Binding, responsibility or delegation
F3 Resident, Command intake, replay or writer authority
F4 permit issuance, Host authentication, effect scope or final authority
policy, Prohibited Behavior List or Jenn authorization decisions
F6 Validation requirement or Task completion eligibility
```

An F5 decision may preserve or narrow delivery eligibility. It can never add
an authority atom, widen an effect scope, issue a permit, authenticate a Host,
or turn a missing or negative upstream result into authority.

## 2. Fixed upstream bindings and current production posture

The accepted predecessor bindings are exact:

```yaml
F3:
  acceptance_unit: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
  manifest_sha256: 3075cda63fcb2c7937cb800a3bc09cc830d17e2f98b899828db15e09ab9f79ff
  freeze_decision_sha256: f692ef1a1af8ac15f40c8af696f486240b73a3ddf391633078e31f17eaf62529
F4:
  acceptance_unit: F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R9_ATOMIC_BUNDLE
  manifest_sha256: 8648cb687608b1151c81d01582a1fb7a19a5811a66224abe621a25188dc30dd5
  freeze_decision_sha256: 1f8cb1a9306175c5d1777e60804c90a0c91d3234d074aaa09d599e25440d79c2
```

The only positive effect-admission input F5 may consume is an exact committed
`F4AcceptedEffectHandoffV0_1R9` occurrence from the accepted F4 canonical
writer. Immediately before a physical boundary, F5 additionally requires a
new F4-owned `FinalHandoffAuthorityAssessmentV0_1R9` occurrence for the same
permit, invocation, handoff and complete authority set. F5 verifies refs,
fingerprints, result literals, freshness and equality only; F5 never executes
the F4 reducer.

The frozen F4 R9 decision states that a real positive handoff is currently
non-issuable pending independently accepted owner interfaces and current
production receipts. Therefore:

```yaml
real_F4_handoff_available_now: false
F5_positive_delivery_authority_now: NON_ISSUABLE
synthetic_fixture_may_substitute: false
F5_contract_constructibility_may_be_reviewed: true
```

Starting or later freezing F5 does not change these values. A production path
requires separate accepted owner interfaces, current production receipts,
implementation authority, runtime authority and a production profile.

## 3. Canonical encoding and fingerprint rules

All canonical objects use UTF-8, NFC strings, LF line endings, integers within
the JSON safe-integer range, no floats, and JCS-compatible JSON canonicalization.
Unknown fields, duplicate keys, unknown enum values, non-NFC strings, floats,
negative sequence values and non-lowercase SHA-256 values reject.

For every schema in Section 4:

```text
canonical_fingerprint =
  SHA256(JCS([schema_domain, ordered values excluding canonical_fingerprint]))
```

Schema domains are the exact `interface_version` followed by `-fingerprint`.
The fixture uses a separate root domain
`agents-os.f5-r1-synthetic-witness.v0.1`; synthetic IDs or fingerprints are
never interchangeable with production IDs or fingerprints.

References are stable opaque references. A ref plus fingerprint is one
indivisible commitment. Matching a ref without its fingerprint, or a
fingerprint without canonical-writer resolution, is insufficient.

## 4. Normative schemas

Field order below is exact and fingerprint-covered.

### 4.1 `F5OutboxIntentV0_1R1`

```yaml
interface_version: agents-os.f5-outbox-intent.v0.1-r1
outbox_intent_id: lowercase_sha256
outbox_intent_ref: stable_ref
source_handoff_ref: stable_ref
source_handoff_fingerprint: lowercase_sha256
source_handoff_event_sequence: non_negative_safe_integer
invocation_identity_fingerprint: lowercase_sha256
effect_id: stable_ref
effect_scope_ref: stable_ref
effect_scope_fingerprint: lowercase_sha256
expected_result_contract_ref: stable_ref
expected_result_contract_fingerprint: lowercase_sha256
owner_host_id: stable_ref
execution_epoch: positive_safe_integer
task_fence_generation: non_negative_safe_integer
host_fence_generation: non_negative_safe_integer
effect_fence_generation: non_negative_safe_integer
start_authority_expires_at_utc_ms: positive_safe_integer
completion_blocking: boolean
delivery_profile_ref: stable_ref
delivery_profile_fingerprint: lowercase_sha256
created_at_utc_ms: non_negative_safe_integer
created_event_sequence: non_negative_safe_integer
environment: SYNTHETIC_TEST | PRODUCTION
authority_eligible: boolean
canonical_fingerprint: lowercase_sha256
```

The intent copies, without reinterpretation, every handoff-bound identity,
scope, Host, epoch, fence, expiry and result-contract value. Production requires
`environment=PRODUCTION`, `authority_eligible=true`, and exact accepted F4
resolution. A synthetic intent is never claimable.

### 4.2 `F5EnqueueDispositionV0_1R1`

```yaml
interface_version: agents-os.f5-enqueue-disposition.v0.1-r1
source_handoff_ref: stable_ref
source_handoff_fingerprint: lowercase_sha256
outbox_intent_ref: stable_ref | null
outbox_intent_fingerprint: lowercase_sha256 | null
result: ENQUEUED | NOT_EXECUTABLE | INDETERMINATE
primary_reason: ENQUEUED_NEW | ENQUEUED_REPLAY | SYNTHETIC_INPUT | HANDOFF_UNAVAILABLE | HANDOFF_INVALID | HANDOFF_EXPIRED | HANDOFF_ALREADY_CONSUMED | INTEGRITY_FAILURE
reason_codes: sorted_unique_closed_set
observed_at_utc_ms: non_negative_safe_integer
observed_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

`reason_codes` contains every true reason. `primary_reason` is the first true
reason in this fixed precedence:

```text
INTEGRITY_FAILURE
SYNTHETIC_INPUT
HANDOFF_INVALID
HANDOFF_ALREADY_CONSUMED
HANDOFF_EXPIRED
HANDOFF_UNAVAILABLE
ENQUEUED_REPLAY
ENQUEUED_NEW
```

Only the last two yield `ENQUEUED`. A missing F5 intent after a committed F4
handoff is recoverable because the handoff remains durable and unconsumed;
deterministic materialization uses a uniqueness key on the exact handoff
fingerprint. Duplicate identical enqueue returns the first disposition and
intent. Changed bytes for the same handoff are an integrity failure.

### 4.3 `F5DispatcherClaimantAssessmentV0_1R1`

```yaml
interface_version: agents-os.f5-dispatcher-claimant-assessment.v0.1-r1
dispatcher_actor_id: stable_ref
dispatcher_actor_identity_ref: stable_ref
dispatcher_actor_identity_fingerprint: lowercase_sha256
dispatcher_principal_id: stable_ref
dispatcher_principal_ref: stable_ref
dispatcher_principal_fingerprint: lowercase_sha256
dispatcher_binding_assessment_ref: stable_ref
dispatcher_binding_assessment_fingerprint: lowercase_sha256
resident_authority_epoch: positive_safe_integer
resident_continuity_assessment_ref: stable_ref
resident_continuity_assessment_fingerprint: lowercase_sha256
owner_head_event_sequence: non_negative_safe_integer
assessed_at_event_sequence: non_negative_safe_integer
result: CURRENT | STALE | INDETERMINATE
environment: SYNTHETIC_TEST | PRODUCTION
authority_eligible: boolean
canonical_fingerprint: lowercase_sha256
```

`dispatcher` is an operational label only. Production identity must resolve to
an F2 `SYSTEM_SERVICE` Actor and `SERVICE_PROCESS` Principal with a current
Binding, plus current F3 Resident continuity. F5 does not create, activate or
classify those identities. This assessment permits claim ownership only after
F4 authority exists; it contributes no effect scope or authority atom.

### 4.4 `F5PhysicalBoundaryAuthorityObservationV0_1R1`

```yaml
interface_version: agents-os.f5-physical-boundary-authority-observation.v0.1-r1
observation_purpose: CLAIM | DISPATCH_ARM
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
source_handoff_ref: stable_ref
source_handoff_fingerprint: lowercase_sha256
fresh_F4_assessment_ref: stable_ref
fresh_F4_assessment_fingerprint: lowercase_sha256
fresh_F4_assessment_result: CURRENT | REJECTED | INDETERMINATE
observed_task_fence_generation: non_negative_safe_integer
observed_host_fence_generation: non_negative_safe_integer
observed_effect_fence_generation: non_negative_safe_integer
observed_execution_epoch: positive_safe_integer
observed_host_id: stable_ref
observed_at_utc_ms: non_negative_safe_integer
observed_event_sequence: non_negative_safe_integer
canonical_writer_head_event_sequence: non_negative_safe_integer
result: CURRENT | REJECTED | INDETERMINATE
primary_reason: ALL_CURRENT | AUTHORITY_STALE | FENCED | EPOCH_STALE | HOST_MISMATCH | EXPIRED | ASSESSMENT_UNAVAILABLE | INTEGRITY_FAILURE
reason_codes: sorted_unique_closed_set
canonical_fingerprint: lowercase_sha256
```

The F4 assessment is newly produced by the accepted F4 reducer for the same
complete authority set. `CURRENT` requires exact equality with every bound
handoff and intent value, `observed_at_utc_ms < start_authority_expires_at_utc_ms`,
and `observed_event_sequence = canonical_writer_head_event_sequence` in the
observation transaction. A claim requires purpose `CLAIM`; an arm requires a
later purpose `DISPATCH_ARM` observation. F5 does not inspect Actor class, Task labels, colors,
P0-P3, relationship, trust, urgency or historical success.

The fixed negative precedence is:

```text
INTEGRITY_FAILURE
AUTHORITY_STALE
FENCED
EPOCH_STALE
HOST_MISMATCH
EXPIRED
ASSESSMENT_UNAVAILABLE
ALL_CURRENT
```

### 4.5 `F5OutboxClaimFactV0_1R1`

```yaml
interface_version: agents-os.f5-outbox-claim-fact.v0.1-r1
claim_id: lowercase_sha256
claim_ref: stable_ref
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
claim_epoch: positive_safe_integer
expected_previous_claim_epoch: non_negative_safe_integer
claimant_assessment_ref: stable_ref
claimant_assessment_fingerprint: lowercase_sha256
claim_authority_observation_ref: stable_ref
claim_authority_observation_fingerprint: lowercase_sha256
lease_expires_at_utc_ms: positive_safe_integer
claim_fencing_token: lowercase_sha256
claimed_at_utc_ms: non_negative_safe_integer
claim_event_sequence: non_negative_safe_integer
result: CLAIMED | NOT_EXECUTABLE | INDETERMINATE
primary_reason: CLAIMED_NEW | CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY | SYNTHETIC_INPUT | INTENT_NOT_PENDING | CLAIM_ALREADY_ACTIVE | DISPATCH_ALREADY_ARMED | TERMINAL_ALREADY_RECORDED | CLAIMANT_STALE | CLAIMANT_UNAVAILABLE | AUTHORITY_STALE | AUTHORITY_UNAVAILABLE | EXPIRED | CAS_MISMATCH | INTEGRITY_FAILURE
reason_codes: sorted_unique_closed_set
canonical_fingerprint: lowercase_sha256
```

One current claim head exists per intent. The claim binds a purpose `CLAIM`
observation but does not consume the F4 invocation; the later arm binds a new
purpose `DISPATCH_ARM` observation. `claim_epoch` is previous plus one;
`claim_fencing_token` binds intent fingerprint, epoch and claimant assessment.
Only a claim with no dispatch-arm fact may be reclaimed after lease expiry,
and it still requires a new claimant assessment, a new purpose `CLAIM`
observation and a previous-plus-one claim epoch. Its prior projection may be
`CLAIMED`; the explicit expired-pre-arm condition makes it claimable without a
fictional PENDING transition. Lease expiry never erases an arm or terminal fact.

### 4.6 `F5OutboxLeaseFactV0_1R1`

```yaml
interface_version: agents-os.f5-outbox-lease-fact.v0.1-r1
lease_fact_id: lowercase_sha256
claim_ref: stable_ref
claim_fingerprint: lowercase_sha256
claim_epoch: positive_safe_integer
claim_fencing_token: lowercase_sha256
previous_lease_expiry_utc_ms: positive_safe_integer
new_lease_expiry_utc_ms: positive_safe_integer
renewed_at_utc_ms: non_negative_safe_integer
renewal_event_sequence: non_negative_safe_integer
result: RENEWED | REJECTED | INDETERMINATE
primary_reason: RENEWED | CLAIM_STALE | TOKEN_MISMATCH | DISPATCH_ALREADY_ARMED | EXPIRED | CAS_MISMATCH | INTEGRITY_FAILURE
reason_codes: sorted_unique_closed_set
canonical_fingerprint: lowercase_sha256
```

Renewal is allowed only before dispatch arm, before current expiry, for the
exact current claim token, and with CAS on the previous expiry. It cannot make
authority or handoff expiry later and does not substitute for the mandatory
fresh F4 assessment at dispatch arm.

### 4.7 `F5DispatchArmFactV0_1R1`

```yaml
interface_version: agents-os.f5-dispatch-arm-fact.v0.1-r1
dispatch_arm_id: lowercase_sha256
dispatch_arm_ref: stable_ref
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
claim_ref: stable_ref
claim_fingerprint: lowercase_sha256
claim_epoch: positive_safe_integer
claim_fencing_token: lowercase_sha256
attempt_ordinal: positive_safe_integer
attempt_id: lowercase_sha256
idempotency_key: stable_ref
physical_boundary_observation_ref: stable_ref
physical_boundary_observation_fingerprint: lowercase_sha256
armed_at_utc_ms: non_negative_safe_integer
armed_event_sequence: non_negative_safe_integer
arm_transaction_ref: stable_ref
arm_transaction_fingerprint: lowercase_sha256
result: ARMED | NOT_EXECUTABLE | INDETERMINATE
primary_reason: ARMED | SYNTHETIC_INPUT | CLAIM_STALE | TOKEN_MISMATCH | ALREADY_ARMED | TERMINAL_ALREADY_RECORDED | AUTHORITY_STALE | FENCED | EPOCH_STALE | HOST_MISMATCH | EXPIRED | OBSERVATION_UNAVAILABLE | CAS_MISMATCH | INTEGRITY_FAILURE
reason_codes: sorted_unique_closed_set
canonical_fingerprint: lowercase_sha256
```

The arm transaction is the one-time F4/F5 seam. It atomically rechecks the
claim CAS, consumes the exact invocation identity once, binds a fresh current
F4 assessment at the current writer head, and commits the arm fact before any
physical call. `idempotency_key` equals the F4-bound stable `effect_id`; callers
cannot supply or change it.

No queue or scheduler wait may occur between a successful arm transaction and
the adapter invocation. Immediately before invoking the adapter, the same
process checks trusted time is still strictly before the bound start-authority
expiry. If that local check fails, it does not call the adapter and records
`PRE_EFFECT_NOT_EXECUTED`; the consumed invocation still cannot be re-armed.
Any restart, ownership change, or uncertainty after arm goes to `UNKNOWN`
rather than crossing the boundary.

A second arm for the same intent or invocation is impossible. Exact replay
returns the first arm accounting; changed bytes are an integrity failure. A
committed arm is not proof the physical call happened. If the process loses
certainty after arm and before a definitive terminal receipt, recovery records
`UNKNOWN` and never automatically retries.

### 4.8 `F5DeliveryAttemptFactV0_1R1`

```yaml
interface_version: agents-os.f5-delivery-attempt-fact.v0.1-r1
attempt_id: lowercase_sha256
attempt_ref: stable_ref
dispatch_arm_ref: stable_ref
dispatch_arm_fingerprint: lowercase_sha256
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
attempt_ordinal: positive_safe_integer
idempotency_key: stable_ref
transport_profile_ref: stable_ref
transport_profile_fingerprint: lowercase_sha256
started_at_utc_ms: non_negative_safe_integer
returned_at_utc_ms: non_negative_safe_integer | null
outcome: PRE_EFFECT_NOT_EXECUTED | DISPATCHED | ACKED | SUCCEEDED | FAILED | UNKNOWN
outcome_evidence_ref: stable_ref
outcome_evidence_fingerprint: lowercase_sha256
effect_may_have_occurred: boolean
automatic_retry_eligible: boolean
attempt_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

Rules are exact:

| Outcome | effect_may_have_occurred | automatic_retry_eligible |
|---|---:|---:|
| `PRE_EFFECT_NOT_EXECUTED` | false | false |
| `DISPATCHED` | true | false |
| `ACKED` | true | false |
| `SUCCEEDED` | true | false |
| `FAILED` | true | false |
| `UNKNOWN` | true | false |

`ACKED` means only that the controlled Host or adapter accepted the request.
It is not effect completion. `FAILED` proves a terminal failure result, not
that no partial effect occurred. Only independently authenticated positive
terminal evidence may prove `SUCCEEDED`, `FAILED`, or a later reconciliation
resolution. Frozen F4 permits one invocation, so even authenticated
`PRE_EFFECT_NOT_EXECUTED` accounting cannot re-arm the consumed invocation.

### 4.9 `F5DeliveryReceiptV0_1R1`

```yaml
interface_version: agents-os.f5-delivery-receipt.v0.1-r1
receipt_id: stable_ref
source_id: stable_ref
source_receipt_revision: positive_safe_integer
attempt_ref: stable_ref
attempt_fingerprint: lowercase_sha256
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
effect_id: stable_ref
invocation_identity_fingerprint: lowercase_sha256
execution_epoch: positive_safe_integer
host_fence_generation: non_negative_safe_integer
effect_fence_generation: non_negative_safe_integer
receipt_kind: TRANSPORT_ACK | EFFECT_SUCCEEDED | EFFECT_FAILED | EFFECT_STATUS_UNKNOWN | EFFECT_QUERY_RESULT
effect_status: ACKED_ONLY | SUCCEEDED | FAILED | UNKNOWN | NOT_EXECUTED
observed_at_utc_ms: non_negative_safe_integer
received_at_utc_ms: non_negative_safe_integer
source_attestation_ref: stable_ref
source_attestation_fingerprint: lowercase_sha256
canonical_fingerprint: lowercase_sha256
```

Deduplication key is `(source_id, receipt_id)`. Exact duplicate bytes return
the first persisted result without another Event. Changed bytes, changed
attempt, effect, invocation, epoch or fence under the same key are a protocol
conflict and open reconciliation; they never overwrite the first receipt.
Late authentic facts are retained, but an old epoch cannot advance current
Task or create a new claim.

### 4.10 `F5DeadLetterFactV0_1R1`

```yaml
interface_version: agents-os.f5-dead-letter-fact.v0.1-r1
dead_letter_id: lowercase_sha256
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
last_claim_ref: stable_ref | null
last_claim_fingerprint: lowercase_sha256 | null
last_attempt_ref: stable_ref | null
last_attempt_fingerprint: lowercase_sha256 | null
reason: PRE_ARM_RETRY_EXHAUSTED | NON_RETRYABLE_PRE_ARM_REJECTION | AUTHORITY_REVOKED | EXPIRED | INTEGRITY_FAILURE | RECEIPT_CONFLICT | RECONCILIATION_REQUIRED
effect_outcome: NOT_PROVEN | SUCCEEDED | FAILED | UNKNOWN | NOT_EXECUTED
reconciliation_required: boolean
dead_lettered_at_utc_ms: non_negative_safe_integer
dead_letter_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

Dead-letter is queue accounting, not an effect outcome. Without separate
authenticated evidence `effect_outcome=NOT_PROVEN` or `UNKNOWN`. Dead-letter
does not authorize retry, compensation, permit renewal, Task completion or a
replacement effect.

### 4.11 `F5ReconciliationCaseV0_1R1`

```yaml
interface_version: agents-os.f5-reconciliation-case.v0.1-r1
reconciliation_id: lowercase_sha256
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
attempt_ref: stable_ref | null
attempt_fingerprint: lowercase_sha256 | null
reason: POST_ARM_CRASH | RECEIPT_CONFLICT | EFFECT_UNKNOWN | LATE_TERMINAL_FACT | DEAD_LETTER_REVIEW | INTEGRITY_RECOVERY
status: OPEN | QUERY_PENDING | RESOLVED | INDETERMINATE
resolution: NONE | SUCCEEDED | FAILED | NOT_EXECUTED | REMAINS_UNKNOWN
evidence_refs: sorted_unique_stable_refs
evidence_set_fingerprint: lowercase_sha256
owner_next_action: QUERY_BY_IDEMPOTENCY_KEY | AWAIT_AUTHENTICATED_RECEIPT | HUMAN_REVIEW | CLOSE_ACCOUNTING_ONLY
opened_event_sequence: non_negative_safe_integer
last_updated_event_sequence: non_negative_safe_integer
canonical_fingerprint: lowercase_sha256
```

Query and reconciliation use the existing `effect_id` and intent; they do not
open a second effect attempt. A later stronger authentic fact enriches the
same case. `REMAINS_UNKNOWN` is a valid fail-closed result. Compensation is a
new separately authorized effect and is outside this contract.

### 4.12 `F5OutboxProjectionV0_1R1`

```yaml
interface_version: agents-os.f5-outbox-projection.v0.1-r1
outbox_intent_ref: stable_ref
outbox_intent_fingerprint: lowercase_sha256
projection_version: positive_safe_integer
last_event_sequence: non_negative_safe_integer
state: PENDING | CLAIMED | DISPATCH_ARMED | DISPATCHED | ACKED | SUCCEEDED | FAILED | UNKNOWN | DEAD_LETTERED | RECONCILED
current_claim_ref: stable_ref | null
current_claim_fingerprint: lowercase_sha256 | null
current_attempt_ref: stable_ref | null
current_attempt_fingerprint: lowercase_sha256 | null
current_reconciliation_ref: stable_ref | null
current_reconciliation_fingerprint: lowercase_sha256 | null
effect_outcome: NOT_PROVEN | SUCCEEDED | FAILED | UNKNOWN | NOT_EXECUTED
automatic_retry_eligible: boolean
completion_blocking: boolean
projection_fingerprint: lowercase_sha256
```

This is a rebuildable projection, never authority. Deleting it and replaying
immutable facts must reproduce the same value without claiming, arming,
dispatching, retrying, issuing a permit or advancing a Task.
`automatic_retry_eligible` refers only to a physical-effect attempt and is
always `false` in R1. Pre-arm enqueue, claim and lease replay eligibility is
decided by its own reducer and does not imply effect-attempt eligibility.

### 4.13 `F5SyntheticDeliveryRecoveryWitnessV0_1R1`

```yaml
interface_version: agents-os.f5-synthetic-delivery-recovery-witness.v0.1-r1
witness_ref: synthetic-f5-r1:stable_ref
witness_namespace: synthetic-f5-r1
environment: SYNTHETIC_TEST
fingerprint_domain: agents-os.f5-r1-synthetic-witness.v0.1
prospective_F4_handoff_requirement_ref: stable_ref
prospective_F4_handoff_requirement_fingerprint: lowercase_sha256
vector_set_fingerprint: lowercase_sha256
authority_eligible: false
runtime_consumable: false
recovery_importable: false
physical_effect_boundary: NOT_EXECUTABLE
terminal_outcome: NOT_EXECUTED
accepted_real_handoff_count: 0
armed_dispatch_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
canonical_fingerprint: lowercase_sha256
```

## 5. Derived identities

The identities are exact:

```text
outbox_intent_id = SHA256(JCS([
  "agents-os.f5-outbox-intent-id.v0.1",
  source_handoff_fingerprint,
  invocation_identity_fingerprint,
  effect_id
]))

outbox_intent_ref = "outbox-intent:" + outbox_intent_id

claim_id = SHA256(JCS([
  "agents-os.f5-outbox-claim-id.v0.1",
  outbox_intent_fingerprint,
  claim_epoch
]))

claim_ref = "outbox-claim:" + claim_id

claim_fencing_token = SHA256(JCS([
  "agents-os.f5-outbox-claim-fence.v0.1",
  outbox_intent_fingerprint,
  claim_epoch,
  claimant_assessment_fingerprint
]))

attempt_id = SHA256(JCS([
  "agents-os.f5-delivery-attempt-id.v0.1",
  outbox_intent_fingerprint,
  attempt_ordinal
]))

dispatch_arm_id = SHA256(JCS([
  "agents-os.f5-dispatch-arm-id.v0.1",
  claim_fingerprint,
  attempt_id,
  physical_boundary_observation_fingerprint
]))
```

No caller-selected identity is accepted. `attempt_ordinal` is previous plus
one and never reused, including after crash or dead-letter.

## 6. Total state machine

The append-only facts reduce to this state machine:

```text
committed F4 handoff
  -> ENQUEUED -> PENDING

PENDING
  -> CLAIMED
  -> DEAD_LETTERED (expired, revoked, integrity failure or non-retryable rejection)

CLAIMED
  -> CLAIMED (safe pre-arm lease renewal)
  -> CLAIMED (lease expired and no arm exists; new claim epoch required)
  -> DISPATCH_ARMED
  -> DEAD_LETTERED

DISPATCH_ARMED
  -> DISPATCHED | ACKED | SUCCEEDED | FAILED | UNKNOWN
  -> UNKNOWN on any unclosed crash window

DISPATCHED
  -> ACKED | SUCCEEDED | FAILED | UNKNOWN

ACKED
  -> SUCCEEDED | FAILED | UNKNOWN

UNKNOWN | FAILED | DEAD_LETTERED
  -> RECONCILED

SUCCEEDED | RECONCILED
  -> no new delivery transition
```

`FAILED` is terminal for that attempt. A policy-authorized replacement or
compensation is a new upstream effect with a new F4 handoff; it is not an F5
retry of the old authority.

Every reducer returns exactly one of `APPLIED | REPLAYED | REJECTED |
INDETERMINATE`. Multiple failures use sorted unique `reason_codes` and the
fixed precedence declared by the relevant schema. Unknown or unavailable
inputs never default to APPLIED.

## 7. Claim, lease, and one-time consumption

Claim is an atomic canonical-writer transaction. It reads:

```text
exact immutable intent and F4 handoff
current intent projection rebuilt from immutable facts
current claim head and lease
absence of any arm or terminal fact
current dispatcher claimant assessment
fresh F4 physical-boundary assessment
trusted time and canonical writer head
```

It writes the claim fact and Event in one transaction. A claim is work
ownership, not effect authority. It cannot cross the physical boundary.

The arm transaction repeats the complete read at a later current watermark.
It uniquely consumes `(source_handoff_fingerprint,
invocation_identity_fingerprint)` and commits one arm fact before any external
call. A claim token is rejected after a newer epoch. Lease expiry after arm
does not permit a second claimant or second arm.

## 8. Retry and UNKNOWN rules

Within one F4 handoff, automatic retry is limited to pre-arm infrastructure
work:

```text
deterministic enqueue replay
claim after a prior claim lease expires with no arm fact
lease renewal before arm
recovery of a reply lost before any arm fact
```

Every such retry requires a new current claim epoch where applicable, a fresh
current F4 assessment, the exact same immutable intent, and trusted time before
all expiries. It never calls an external boundary.

After one arm fact exists, physical-effect automatic retry is always false,
including when later evidence says `PRE_EFFECT_NOT_EXECUTED`. Frozen F4 binds
one invocation and one physical claim. Any replacement attempt requires a new
upstream F4 permit/handoff and is not an F5 retry of the old authority.

`UNKNOWN`, `DISPATCHED`, `ACKED`, `FAILED`, timeout after arm, connection loss
after arm, missing response, process crash after arm, or unprovable call state
also can never automatically retry. Endpoint idempotency capability does not
relax this rule. It enables query/reconciliation using the same stable key,
not a new effect attempt.

## 9. Crash windows and recovery barrier

The minimum crash decisions are:

| Window | Recovery result |
|---|---|
| handoff committed, intent absent | deterministically enqueue or record a negative disposition; no effect |
| intent committed, claim absent | remain PENDING |
| claim committed, arm absent | reclaim only after lease expiry with new epoch and full recheck |
| arm committed, call state unknown | append UNKNOWN and open reconciliation; no automatic retry |
| call returned, receipt not committed | UNKNOWN until authenticated receipt/query resolves |
| receipt committed, projection absent | rebuild projection without any effect |
| dead-letter committed, projection absent | rebuild; do not infer effect outcome |
| reconciliation update committed, reply lost | exact replay returns first update |

Startup MUST complete this barrier before ordinary claim:

```text
1. verify F3 ledger continuity and canonical writer head
2. rebuild Outbox projections from immutable facts
3. scan committed F4 handoffs without enqueue dispositions
4. scan current claims and fence stale claim epochs
5. turn every unclosed post-arm window into UNKNOWN
6. ingest already committed receipts idempotently
7. open or resume one reconciliation case per uncertain intent
8. verify no duplicate arm, terminal conflict or receipt conflict is hidden
9. re-read current F4 authority for each candidate claim
10. publish a recovery barrier Event and only then allow ordinary claims
```

Recovery can write accounting and reconciliation facts while delivery is
blocked. It cannot resurrect an old handoff, permit, lease, claim, arm or
execution epoch.

## 10. Canonical writer and transaction ownership

The F3 frozen Resident remains the only canonical ledger writer and owns the
single authoritative connection. F5 owns reducer semantics, not a second
writer. Dispatcher, Host, adapter, provider and recovery scanner submit closed
inputs through the accepted writer boundary and cannot directly mutate Outbox,
Event, Task, permit or handoff state.

Each F5 mutation atomically writes:

```text
immutable F5 fact
+ append-only Event
+ canonical current pointer or version
+ Inbox/replay result when input is a Command
```

Projection updates may be rebuilt and need not be authority. An SQLite schema,
index, cache, transport API or N-API implementation profile is deferred.

F5 may declare required future F3 Command types only as downstream interface
requirements:

```yaml
owner: F3
status: UNACCEPTED_DOWNSTREAM_REQUIREMENT
usable_in_runtime: false
synthetic_fixture_only: true
authority_eligible: false
```

F5 does not freeze an F3 registry revision, CommandTypeDefinition, intake
state, replay ledger or envelope. Until accepted F3 command interfaces exist,
production F5 writer mutations remain non-issuable.

## 11. Synthetic isolation

The fixed fixture is structural evidence only:

```text
namespace = synthetic-f5-r1
environment = SYNTHETIC_TEST
authority_eligible = false
runtime_consumable = false
recovery_importable = false
physical_effect_boundary = NOT_EXECUTABLE
accepted_real_handoff_count = 0
armed_dispatch_count = 0
external_effect_count = 0
provider_call_count = 0
raw_secret_count = 0
terminal_outcome = NOT_EXECUTED
```

It contains no standard production `F4AcceptedEffectHandoff`, no real Actor,
Command, TaskPermit, Host, credential, secret handle, provider response,
Outbox claim, dispatch arm or effect receipt. Synthetic vector inputs test the
reducers but cannot be imported, renamed, re-signed or copied into a production
writer. Any production consumer MUST reject the namespace, environment,
fingerprint domain and witness schema.

## 12. Normative invariants

1. F5 consumes F4 authority and never creates or widens it.
2. No Actor or Task permission level, color, role, relationship, trust,
   urgency or historical success changes delivery eligibility.
3. PBL no-match is never authority.
4. A ref/fingerprint mismatch is an integrity failure.
5. A synthetic input is never production-eligible.
6. There is one canonical writer and one current claim head per intent.
7. Claim epoch and attempt ordinal are previous plus one.
8. Lease renewal cannot cross handoff, authority or policy expiry.
9. Lease expiry after arm never enables another arm.
10. The physical boundary requires one fresh current F4 assessment.
11. F5 does not locally recompute the F4 assessment.
12. The stable `effect_id` is the only dispatch idempotency key.
13. Arm is committed before any physical call.
14. An arm is not proof the physical call occurred.
15. Any unclosed post-arm crash becomes UNKNOWN.
16. No post-arm outcome permits an automatic physical-effect retry.
17. ACKED never means SUCCEEDED.
18. FAILED does not prove no partial effect.
19. Dead-letter does not prove an effect outcome.
20. Exact receipt replay creates no second Event.
21. Changed receipt bytes under the same key conflict.
22. Late authentic facts are retained but cannot advance an old epoch.
23. Reconciliation queries existing effect identity and creates no attempt.
24. Compensation requires a new separately authorized effect.
25. Rebuilding projections has no side effects.
26. Recovery completes before ordinary claims resume.
27. Missing, stale, conflicting, unknown or unavailable inputs fail closed.
28. No implementation, runtime, database, provider or real effect is authorized.

## 13. Mandatory adversarial decisions

The validator and independent reviewer MUST test at least:

```text
synthetic handoff presented to production -> reject
F4 handoff ref matches but fingerprint differs -> reject
F5 locally changes F4 assessment REJECTED to CURRENT -> reject
old F4 assessment reused at a later writer head -> reject
handoff expires exactly at observed time -> reject
claimant label alone without F2/F3 assessments -> reject
claim epoch skip or duplicate -> reject
stale claim token renewal -> reject
lease extension beyond authority expiry -> reject
second claim while current claim is active -> reject
lease expiry after arm followed by second arm -> reject
second arm with identical bytes -> replay first accounting, no call
second arm with changed bytes -> integrity failure
caller-selected idempotency key -> reject
crash after arm before call -> UNKNOWN, no automatic retry
crash after call before receipt -> UNKNOWN, no automatic retry
ACKED treated as success -> reject
FAILED treated as NOT_EXECUTED -> reject
UNKNOWN marked automatic-retry eligible -> reject
PRE_EFFECT_NOT_EXECUTED marked automatic-retry eligible after arm -> reject
dead-letter treated as effect failure or completion -> reject
same receipt key with changed effect or epoch -> conflict
late old-epoch SUCCEEDED advances current Task -> reject
reconciliation opens a new attempt -> reject
projection rebuild emits claim, arm or Event -> reject
missing recovery barrier still permits ordinary claim -> reject
PBL no-match creates delivery authority -> reject
Actor class, Task label, Green/Yellow/Red or P0-P3 changes claim -> reject
nonzero effect, provider, secret, arm or real-handoff fixture count -> reject
```

## 14. R1 witness and validator claim limit

The builder deterministically creates one fixed synthetic fixture containing:

```text
the exact schema-profile inventory
closed reducer decision vectors
crash-window decisions
retry and outcome truth tables
the synthetic non-authority witness
zero external-effect assertions
```

The validator independently computes schema/profile fingerprints, all object
fingerprints, vector reducer outputs, fixed reason precedence, identity
formulas, transition legality and negative mutations. It MUST reject a fixture
that is merely byte-equal but semantically invalid.

A validator PASS means only:

```text
R1 contract fixture and validator are mutually consistent
the closed synthetic reducers are constructible
the synthetic evidence is non-authority and zero-effect
```

It does not prove implementation correctness, runtime readiness, real F4
handoff availability, production authentication, provider safety or external
effect success.

## 15. Acceptance and downstream boundary

The author may fix R1 bytes and request fresh full atomic independent review.
The author cannot claim independence. An independent PASS cannot accept F5.
Only Jenn may accept and freeze the entire declared unit.

Nothing in R1:

```text
accepts or freezes F5
starts F6 or any later contract
authorizes Rust, JavaScript, N-API or SQLite implementation
creates a database, index, cache or migration
starts Resident, Worker, Host, dispatcher, service or provider
reads or changes credentials, secrets, keys or production authentication
crosses a file, process, network, device, provider or UI effect boundary
authorizes commit, push, PR, merge, release, deploy, publish or tag
```

The next gate after author closeout is a fresh hash-bound independent review of
the complete R1 atomic unit.
