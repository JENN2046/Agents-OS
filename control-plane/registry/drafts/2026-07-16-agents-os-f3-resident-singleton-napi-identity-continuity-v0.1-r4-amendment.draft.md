# AGENTS OS F3 Resident Singleton, N-API, and Identity Continuity v0.1 R4 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R1 SHA-256: `e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e`  
Base R2 SHA-256: `4cd066dacf0f73d21566640a25c5cf5e90ca800ed4a793827c5088936703b236`  
Base R3 SHA-256: `8a25b247a0618ab06ef6186464405b9d137bf68967a9952647986562cb93244c`  
Blocking R3 independent-review SHA-256: `33d31ddfaa90e7b9171461d4cd89f013fb13568ef7a645fec356fd44063b784e`

## 1. Scope, precedence, and fixed inputs

This is the narrow R4 correction authorized by the immutable R4 start
decision. It closes only:

```text
F3-R3-FULL-ATOMIC-IR-M01 restore lineage retry after an abandoned reservation
F3-R3-FULL-ATOMIC-IR-M02 effective F3 contract-bundle version binding
F3-R3-FULL-ATOMIC-IR-M03 complete activation Command registry definition
F3-R3-FULL-ATOMIC-IR-M04 seven exact synthetic leaf schemas and mapping
```

The effective reading order is:

```text
1. R4 explicit replacements
2. R3 other explicit replacements
3. R2 other explicit replacements
4. R1 all other clauses
5. frozen F2 R1-R22 atomic bundle for every F2-owned shape and reducer
```

R1, R2, R3, and the R3 independent review are immutable inputs. Every earlier
invariant, failure rule, exclusion, and non-authorization not explicitly
replaced here remains in force.

This document creates no implementation, database, runtime, service,
production-authentication, provider, effect, TaskPermit, host, fence, F4, F5,
or F6 authority.

## 2. Crash-total restore lineage retry chain

This section replaces R3 Sections 3.2, 3.4, and 3.5 only where they govern a
restore reservation, abandonment, lineage uniqueness, or retry. Global epoch
high-watermark `H`, restored ledger predecessor `R`, the `H + 1` rule, and all
other R3 authority semantics remain unchanged.

### 2.1 Immutable restore-lineage claim

The first reservation for one exact unconsumed restore decision creates one
immutable claim:

```yaml
ResidentRestoreLineageClaimV0_1R4:
  interface_version: agents-os.resident-restore-lineage-claim.v0.1-r4
  restore_lineage_claim_ref: stable_ref
  witness_id: stable_ref
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  restore_decision_ref: stable_ref
  restore_decision_fingerprint: lowercase_sha256
  authority_lineage_id: stable_ref
  previous_authority_lineage_id: stable_ref
  restored_authority_epoch: positive_safe_integer
  restored_authority_epoch_fingerprint: lowercase_sha256
  claimed_previous_global_high_watermark: positive_safe_integer
  claimed_previous_global_epoch_fingerprint: lowercase_sha256
  intended_authority_epoch: positive_safe_integer
  restore_gap_start: positive_safe_integer
  restore_gap_end: positive_safe_integer
  first_witness_generation: positive_safe_integer
  state: OPEN_UNTIL_ONE_COMMIT
  canonical_fingerprint: lowercase_sha256
```

The ref is independently derived:

```text
SHA-256(JCS([
  "agents-os.resident-restore-lineage-claim-ref.v0.1-r4",
  witness_id,
  restore_decision_ref,
  authority_lineage_id
]))
```

The fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under its interface-version domain. The
claim is valid only when:

```text
restored_authority_epoch = R
claimed_previous_global_high_watermark = H
intended_authority_epoch = H + 1
restore_gap_start = R + 1
restore_gap_end = H
authority_lineage_id = decision.new_restore_lineage_id
every decision, backup, restored-head, witness, and fingerprint input matches
```

`OPEN_UNTIL_ONE_COMMIT` is a fixed semantic literal, not mutable state. The
terminal state is reduced from the witness attempt chain below. The claim
grants no authority and cannot make a stale decision current.

### 2.2 R4 restore attempt fields

R4 replaces the effective reservation schema name and interface with
`ResidentAuthorityWitnessReservationV0_1R4` and
`agents-os.resident-authority-witness-reservation.v0.1-r4`. It preserves every
R3 field and adds these fields immediately before `incarnation_id`:

```yaml
restore_lineage_claim_ref: stable_ref | null
restore_lineage_claim_fingerprint: lowercase_sha256 | null
restore_attempt_ordinal: positive_safe_integer | null
previous_restore_attempt_ref: stable_ref | null
previous_restore_attempt_fingerprint: lowercase_sha256 | null
```

For a normal genesis/restart reservation all five fields are null. For a
restore reservation they are all required except the two previous-attempt
fields, which are null exactly for ordinal 1. The reservation ref intentionally
remains the independent R3 derivation so an R3-shaped and R4-shaped reservation
at the same generation cannot coexist; the R4 schema fingerprint and exact
decoder distinguish the field set. It binds generation, intended epoch, and
lineage, while the fingerprint includes the five inserted fields in the
displayed insertion order.

R4 replaces the abandonment schema with:

```yaml
ResidentAuthorityWitnessAbandonV0_1R4:
  interface_version: agents-os.resident-authority-witness-abandon.v0.1-r4
  abandon_ref: stable_ref
  witness_id: stable_ref
  witness_generation: positive_safe_integer
  reservation_ref: stable_ref
  reservation_fingerprint: lowercase_sha256
  restore_lineage_claim_ref: stable_ref | null
  restore_lineage_claim_fingerprint: lowercase_sha256 | null
  restore_attempt_ordinal: positive_safe_integer | null
  observed_ledger_epoch_ref: stable_ref | null
  observed_ledger_epoch_fingerprint: lowercase_sha256 | null
  reason: NO_MATCHING_LEDGER_EPOCH
  state: ABANDONED
  canonical_fingerprint: lowercase_sha256
```

R4 replaces the effective COMMIT schema name and interface with
`ResidentAuthorityWitnessCommitV0_1R4` and
`agents-os.resident-authority-witness-commit.v0.1-r4`, preserves every R3 field,
and adds the same claim ref/fingerprint and attempt ordinal immediately after
`reservation_fingerprint`. Each R4 abandonment or commit fingerprint is
SHA-256 JCS over its complete effective field order, excluding
`canonical_fingerprint`, under its own interface-version domain.

The attempt identity is:

```text
restore attempt ref = reservation_ref for RESERVED
restore attempt ref = abandon_ref for ABANDONED
restore attempt ref = authority_epoch_ref for COMMITTED
```

### 2.3 Total retry reducer

One restore claim has exactly this state machine:

```text
no attempt
  -> ordinal 1 RESERVED at first_witness_generation

RESERVED K + no exact ledger epoch binding that reservation
  -> exactly one ABANDONED K

ABANDONED K + decision still unconsumed + ledger still exact R + witness still H
  -> ordinal K+1 RESERVED at a strictly later unused witness generation
  -> same claim ref/fingerprint, decision, lineage L, R, H, H+1, and gap
  -> previous_restore_attempt_ref/fingerprint = exact ABANDONED K

RESERVED K + exact ledger H+1 epoch binding that reservation
  -> exactly one COMMITTED K
  -> decision and claim terminally consumed

COMMITTED K
  -> no later attempt for this claim, decision, or lineage
```

Every reservation has exactly one terminal `ABANDONED` or `COMMITTED` record,
never both. Attempt ordinals begin at 1, are contiguous, and never repeat. A
retry may reuse lineage `L` only when it uses the exact same claim and decision
after the exact previous attempt is `ABANDONED`.

The corrected uniqueness rule is:

```text
L must never appear in a COMMITTED epoch, COMMITTED witness entry, different
restore decision, different claim, different backup, different restored head,
different H, different gap, or competing live reservation.

L may appear in multiple reservations only inside one contiguous attempt chain
for the same still-unconsumed claim, and every earlier reservation must be
ABANDONED before the next one exists.
```

If ledger `R`, witness `H`, the decision bytes, backup, gap, identity, or any
bound fingerprint changes after abandonment, the claim is stale and no retry is
legal. A new transition then requires a new exact Jenn decision and new lineage;
this contract does not create that decision.

Thus the crash before epoch commit is retryable without lineage competition,
while crash after epoch commit still finalizes the exact pending reservation
and never allocates a second `H + 1`.

## 3. Effective R4 bundle-version binding

This section replaces the R2 Section 1 effective bundle literal and every
inherited effective use of it.

The sole effective literal is:

```text
F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
```

Every effective field named `F3_contract_version` uses exactly that literal,
including:

```text
CanonicalCommandV0_1
AuthenticatedCommandContextV0_1
CommandEnvelopeV0_1R2
F3CommandIntakeRecordV0_1R2
AuthenticatedActorActionRefR4Effective
DelegationActivationAcknowledgementRefR4Effective
every issuance and activation synthetic fixture object carrying that field
```

The field name, frozen F2 field order, and fingerprint domains do not change;
the canonical **value** changes from the blocked R2 literal to the R4 literal.
Every fingerprint formula that includes `F3_contract_version` therefore uses
the R4 literal. An R1, R2, R3, unknown, absent, mixed, or caller-selected value
is a version mismatch and rejects before replay mutation.

The global replay namespace remains `F3_GLOBAL_COMMAND_NAMESPACE`; it never
makes records from different canonical fingerprints equal. A Command carrying
an older bundle literal has different canonical bytes and conflicts with an
existing R4 command ID.

## 4. Registry revision 4

R4 replaces the R3 issuance definition and completes the activation definition.
Both types are members of one exact registry revision 4.

### 4.1 Revised issuance definition

The R3 payload and reducer descriptors remain byte-identical, with digests:

```text
payload 045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1
reducer 4c4bac289945131cd556dd855398761cc940b150d2930b4f4453d103c1296e70
```

The effective definition is:

```yaml
DelegationIssuanceCommandTypeDefinitionV0_1R4:
  interface_version: agents-os.command-type-definition.v0.1
  registry_revision: 4
  command_type_id: DELEGATION_ISSUANCE
  command_type_version: 1
  owner_contract_ref: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE
  owner_contract_sha256: 95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1
  payload_schema_ref: agents-os.delegation-issuance-command-payload.v0.1-r2
  payload_schema_sha256: 045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1
  allowed_target_kinds: [F2_DELEGATION_REVISION]
  expected_target_revision_policy: REQUIRED
  responsibility_mode: REQUIRED
  effect_class: LEDGER_ONLY
  reducer_ref: agents-os.delegation-issuance-reducer.v0.1-r3
  reducer_sha256: 4c4bac289945131cd556dd855398761cc940b150d2930b4f4453d103c1296e70
  required_gate_refs:
    - agents-os.gate.f2.actor-identity-active.v0.1
    - agents-os.gate.f2.authentication-authenticated.v0.1
    - agents-os.gate.f2.principal-binding-active.v0.1
    - agents-os.gate.f3.jenn-root-direction-active.v0.1-r2
    - agents-os.gate.f3.prohibited-boundary-current.v0.1
    - agents-os.gate.f3.resident-ready-continuous.v0.1-r4
    - agents-os.gate.f3.trusted-time-current.v0.1
  maximum_validity_duration_ms: 60000
  unknown_fields_policy: REJECT
  canonical_fingerprint: f3f728ee416cc9477f25279ffcf436554cd8dde257c62ec86021af4e41755c16
```

Its exact R1 fingerprint input is:

```json
["agents-os.command-type-definition.v0.1",4,"DELEGATION_ISSUANCE",1,"F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE","95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1","agents-os.delegation-issuance-command-payload.v0.1-r2","045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1",["F2_DELEGATION_REVISION"],"REQUIRED","REQUIRED","LEDGER_ONLY","agents-os.delegation-issuance-reducer.v0.1-r3","4c4bac289945131cd556dd855398761cc940b150d2930b4f4453d103c1296e70",["agents-os.gate.f2.actor-identity-active.v0.1","agents-os.gate.f2.authentication-authenticated.v0.1","agents-os.gate.f2.principal-binding-active.v0.1","agents-os.gate.f3.jenn-root-direction-active.v0.1-r2","agents-os.gate.f3.prohibited-boundary-current.v0.1","agents-os.gate.f3.resident-ready-continuous.v0.1-r4","agents-os.gate.f3.trusted-time-current.v0.1"],60000,"REJECT"]
```

### 4.2 Exact activation payload descriptor

The activation payload schema digest is SHA-256 over the exact UTF-8 bytes of
this one-line JCS value, with no newline in the digest input:

```json
{"additional_properties":false,"interface_version":"agents-os.delegation-activation-ack-payload-schema-descriptor.v0.1-r4","ordered_fields":[["interface_version","literal:agents-os.delegation-activation-ack-payload.v0.1"],["activation_mode","EXPLICIT_ACK|WORKER_ASSIGNMENT_HANDSHAKE"],["delegation_ref","stable_ref"],["delegation_subject_fingerprint","lowercase_sha256"],["delegate_actor_id","stable_ref"],["delegate_actor_identity_revision","positive_safe_integer"],["responsibility_source_mode","literal:NONE_ACTIVATION_PURPOSE_ONLY"]],"rules":["field_order_is_exact","unknown_fields_and_unknown_enum_values_reject","WORKER_ASSIGNMENT_HANDSHAKE_requires_TEMPORARY_WORKER_delegate","no_responsibility_domain_effect_provider_host_permit_secret_or_credential_field"],"schema_ref":"agents-os.delegation-activation-ack-payload.v0.1"}
```

Required digest:

```text
7bfc6a067e0cce72a39c4b8fd0cf7d0021ecd28a9f88d2afccae151d3157fd15
```

### 4.3 Exact activation reducer descriptor

The activation reducer digest is SHA-256 over the exact UTF-8 bytes of this
one-line JCS value, with no newline in the digest input:

```json
{"atomic_outputs":["CommandGateResult_ADMITTED","AuthenticatedCommandContext","CommandEnvelope","DelegationActivationAcknowledgementRefR4Effective","DelegationActivationEvidenceR15Effective","DelegationActivationAssessmentV0_1R16","Delegation_current_projection_ACTIVE","DelegationActivationEvent","F3CommandIntakeRecord_COMMITTED","CommandReplayEntry_COMMITTED"],"effect_class":"LEDGER_ONLY","failure_semantics":["pre_intake_unavailability_writes_nothing","post_preflight_proven_negative_persists_REJECTED","post_preflight_unreproducible_gate_persists_INDETERMINATE","integrity_or_uniqueness_unprovable_writes_nothing"],"frozen_F2_manifest_sha256":"95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1","interface_version":"agents-os.delegation-activation-ack-reducer-descriptor.v0.1-r4","ordered_preconditions":["current_F2_delegate_actor_identity_ACTIVE","current_F2_delegate_principal_binding_ACTIVE","current_F2_authentication_AUTHENTICATED","exact_F2_delegation_current_pending_unexpired_unrecalled_unsuspended_unrevoked_unrenounced_not_superseded","payload_delegate_revision_fingerprint_and_activation_mode_match","responsibility_source_mode_NONE_ACTIVATION_PURPOSE_ONLY","current_prohibited_boundary_satisfied","current_trusted_time_inside_validity","F3_READY_and_CONTINUOUS_at_pre_intake_and_writer_recheck","WORKER_ASSIGNMENT_HANDSHAKE_requires_current_exact_TEMPORARY_WORKER_binding"],"payload_schema_sha256":"7bfc6a067e0cce72a39c4b8fd0cf7d0021ecd28a9f88d2afccae151d3157fd15","prohibited_outputs":["new_responsibility_source","Delegation_issuance","TaskPermit","host_admission","effect_execution","provider_call","external_operation"],"reducer_ref":"agents-os.delegation-activation-ack-reducer.v0.1-r4"}
```

Required digest:

```text
8d5ccccc6a80647954472925de5e2addbbacdb54cf17ebdcad0140ba8e2469e1
```

### 4.4 Full activation definition

```yaml
DelegationActivationAckCommandTypeDefinitionV0_1R4:
  interface_version: agents-os.command-type-definition.v0.1
  registry_revision: 4
  command_type_id: DELEGATION_ACTIVATION_ACK
  command_type_version: 1
  owner_contract_ref: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE
  owner_contract_sha256: 95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1
  payload_schema_ref: agents-os.delegation-activation-ack-payload.v0.1
  payload_schema_sha256: 7bfc6a067e0cce72a39c4b8fd0cf7d0021ecd28a9f88d2afccae151d3157fd15
  allowed_target_kinds: [F2_DELEGATION_REVISION]
  expected_target_revision_policy: REQUIRED
  responsibility_mode: NONE_ACTIVATION_PURPOSE_ONLY
  effect_class: LEDGER_ONLY
  reducer_ref: agents-os.delegation-activation-ack-reducer.v0.1-r4
  reducer_sha256: 8d5ccccc6a80647954472925de5e2addbbacdb54cf17ebdcad0140ba8e2469e1
  required_gate_refs:
    - agents-os.gate.f2.actor-identity-active.v0.1
    - agents-os.gate.f2.authentication-authenticated.v0.1
    - agents-os.gate.f2.delegation-pending-current.v0.1
    - agents-os.gate.f2.principal-binding-active.v0.1
    - agents-os.gate.f3.prohibited-boundary-current.v0.1
    - agents-os.gate.f3.resident-ready-continuous.v0.1-r4
    - agents-os.gate.f3.trusted-time-current.v0.1
  maximum_validity_duration_ms: 60000
  unknown_fields_policy: REJECT
  canonical_fingerprint: a40dda2278ba856ab9248f8d0da22b6fd8857ff70f9d1d68aee7a83c20ef610b
```

Its exact R1 fingerprint input is:

```json
["agents-os.command-type-definition.v0.1",4,"DELEGATION_ACTIVATION_ACK",1,"F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE","95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1","agents-os.delegation-activation-ack-payload.v0.1","7bfc6a067e0cce72a39c4b8fd0cf7d0021ecd28a9f88d2afccae151d3157fd15",["F2_DELEGATION_REVISION"],"REQUIRED","NONE_ACTIVATION_PURPOSE_ONLY","LEDGER_ONLY","agents-os.delegation-activation-ack-reducer.v0.1-r4","8d5ccccc6a80647954472925de5e2addbbacdb54cf17ebdcad0140ba8e2469e1",["agents-os.gate.f2.actor-identity-active.v0.1","agents-os.gate.f2.authentication-authenticated.v0.1","agents-os.gate.f2.delegation-pending-current.v0.1","agents-os.gate.f2.principal-binding-active.v0.1","agents-os.gate.f3.prohibited-boundary-current.v0.1","agents-os.gate.f3.resident-ready-continuous.v0.1-r4","agents-os.gate.f3.trusted-time-current.v0.1"],60000,"REJECT"]
```

Both definitions are exact accepted-contract candidates only. They do not
self-register at runtime or authorize implementation.

## 5. Exact schemas for the seven descriptive synthetic leaves

This section replaces the descriptive schema mappings for R3 rows 7, 8, 9,
25, 36, 46, and 55. These are fixture evidence interfaces; they bind synthetic
inputs and derived projections without changing a frozen F2 schema.

### 5.1 Synthetic Jenn root-direction input

```yaml
F3SyntheticJennRootDirectionInputV0_1R4:
  interface_version: agents-os.f3-synthetic-jenn-root-direction-input.v0.1-r4
  fixture_namespace: agents-os.synthetic.f3-r2.m0
  evidence_class: SYNTHETIC_CONTRACT_FIXTURE_ONLY
  subject_ref: stable_ref
  frozen_F2_manifest_sha256: 95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1
  Jenn_actor_id: stable_ref
  Jenn_actor_identity_revision: positive_safe_integer
  Jenn_actor_identity_fingerprint: lowercase_sha256
  Jenn_principal_binding_ref: stable_ref
  Jenn_principal_binding_fingerprint: lowercase_sha256
  Jenn_root_relation_ref: stable_ref
  Jenn_root_relation_fingerprint: lowercase_sha256
  responsibility_kind: JENN_ROOT_DIRECTION
  responsibility_scope_ref: stable_ref
  responsibility_scope_fingerprint: lowercase_sha256
  not_before_utc_ms: safe_integer
  expires_at_utc_ms: safe_integer
  current_at_event_sequence: positive_safe_integer
  assessment: ACTIVE
  canonical_fingerprint: lowercase_sha256
```

### 5.2 Synthetic trusted-time input

```yaml
F3SyntheticTrustedTimeInputV0_1R4:
  interface_version: agents-os.f3-synthetic-trusted-time-input.v0.1-r4
  fixture_namespace: agents-os.synthetic.f3-r2.m0
  evidence_class: SYNTHETIC_CONTRACT_FIXTURE_ONLY
  subject_ref: stable_ref
  time_authority_ref: stable_ref
  time_authority_fingerprint: lowercase_sha256
  observed_utc_ms: safe_integer
  valid_from_utc_ms: safe_integer
  valid_through_utc_ms: safe_integer
  maximum_staleness_ms: positive_safe_integer
  based_on_event_sequence: positive_safe_integer
  assessment: CURRENT
  canonical_fingerprint: lowercase_sha256
```

For M0, `observed_utc_ms = T0_utc_ms`, the validity interval contains every
fixture Command time, and the maximum-staleness predicate reproduces at the
writer barrier.

### 5.3 Synthetic prohibited-boundary input

```yaml
F3SyntheticProhibitedBoundaryInputV0_1R4:
  interface_version: agents-os.f3-synthetic-prohibited-boundary-input.v0.1-r4
  fixture_namespace: agents-os.synthetic.f3-r2.m0
  evidence_class: SYNTHETIC_CONTRACT_FIXTURE_ONLY
  subject_ref: stable_ref
  prohibited_behavior_list_ref: stable_ref
  prohibited_behavior_list_revision: positive_safe_integer
  prohibited_behavior_list_fingerprint: lowercase_sha256
  boundary_decision_ref: stable_ref
  boundary_decision_fingerprint: lowercase_sha256
  assessed_at_event_sequence: positive_safe_integer
  assessed_at_utc_ms: safe_integer
  assessment: SATISFIED
  canonical_fingerprint: lowercase_sha256
```

For each of Sections 5.1-5.3, `subject_ref` is independently derived:

```text
SHA-256(JCS([
  "agents-os.f3-synthetic-authority-input-ref.v0.1-r4",
  interface_version,
  "agents-os.synthetic.f3-r2.m0"
]))
```

The three interface-version values are distinct, so the three refs are
distinct. No caller-selected ref or alternate fixture namespace is accepted.

### 5.4 Resident readiness projection

```yaml
ResidentReadyProjectionV0_1R4:
  interface_version: agents-os.resident-ready-projection.v0.1-r4
  readiness_ref: stable_ref
  F3_contract_version: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  incarnation_id: stable_ref
  authority_epoch_ref: stable_ref
  authority_epoch_fingerprint: lowercase_sha256
  authority_epoch: positive_safe_integer
  authority_generation: positive_safe_integer
  witness_commit_ref: stable_ref
  witness_commit_fingerprint: lowercase_sha256
  continuity_assessment_ref: stable_ref
  continuity_assessment_fingerprint: lowercase_sha256
  F2_recovery_watermark_event_sequence: positive_safe_integer
  prohibited_boundary_evidence_ref: stable_ref
  prohibited_boundary_evidence_fingerprint: lowercase_sha256
  ledger_head_event_ref: stable_ref
  ledger_head_event_fingerprint: lowercase_sha256
  ledger_head_event_sequence: positive_safe_integer
  supported_contract_set_fingerprint: lowercase_sha256
  lifecycle: READY
  assessment: READY_CONTINUOUS
  canonical_fingerprint: lowercase_sha256
```

`readiness_ref` is SHA-256 JCS over its domain, resident identity ref,
incarnation ID, authority epoch, and authority generation. The projection
fingerprint is SHA-256 JCS over the complete displayed field order excluding
`canonical_fingerprint`, under its interface-version domain. Every R1 READY
predicate must reproduce; an omitted or mismatched input is INDETERMINATE and
no READY projection exists.

### 5.5 Canonical F3 ledger Event

```yaml
F3LedgerEventV0_1R4:
  interface_version: agents-os.f3-ledger-event.v0.1-r4
  event_ref: stable_ref
  event_sequence: positive_safe_integer
  previous_event_ref: stable_ref | null
  previous_event_fingerprint: lowercase_sha256 | null
  event_kind: DELEGATION_ISSUED | DELEGATION_ACTIVATED
  F3_contract_version: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  resident_authority_epoch: positive_safe_integer
  resident_authority_generation: positive_safe_integer
  command_id: stable_ref
  canonical_command_fingerprint: lowercase_sha256
  gate_result_ref: stable_ref
  gate_result_fingerprint: lowercase_sha256
  authenticated_context_ref: stable_ref
  authenticated_context_fingerprint: lowercase_sha256
  command_envelope_ref: stable_ref
  command_envelope_fingerprint: lowercase_sha256
  action_or_activation_ref: stable_ref
  action_or_activation_fingerprint: lowercase_sha256
  subject_ref: stable_ref
  subject_fingerprint: lowercase_sha256
  F3_intake_state_ref: stable_ref
  occurred_at_utc_ms: safe_integer
  canonical_fingerprint: lowercase_sha256
```

The event ref is independently derived before any Event fingerprint:

```text
SHA-256(JCS([
  "agents-os.f3-ledger-event-ref.v0.1-r4",
  event_sequence,
  event_kind,
  command_id
]))
```

The Event fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under its interface-version domain. Issuance
uses `DELEGATION_ISSUED` and the pending Delegation subject; activation uses
`DELEGATION_ACTIVATED` and the exact activation evidence subject. The Event
contains only the independent intake ref, never an intake fingerprint, so the
existing graph remains acyclic.

All three input schemas in Sections 5.1-5.3 and both projection schemas use
SHA-256 JCS over the complete displayed field order excluding
`canonical_fingerprint`, under their exact interface-version domain. Unknown
fields, missing conditional values, non-literal assessments, or digest
mismatches reject.

## 6. Revised exact synthetic manifest: 60 subjects

This section replaces R3 Sections 5.1-5.3 where they define manifest version,
cardinality, enum order, activation registry membership, and the seven
descriptive mappings. R3 Section 5.4 trace-proof schema remains effective.

```yaml
F3SyntheticM0GenesisSubjectEntryV0_1R4:
  kind: F3SyntheticM0ClosedSubjectKindV0_1R4
  subject_ref: stable_ref
  subject_fingerprint: lowercase_sha256

F3SyntheticM0GenesisManifestV0_1R4:
  interface_version: agents-os.f3-synthetic-m0-genesis-manifest.v0.1-r4
  fixture_namespace: agents-os.synthetic.f3-r2.m0
  frozen_F2_acceptance_decision_ref: stable_ref
  frozen_F2_acceptance_decision_sha256: lowercase_sha256
  frozen_F2_atomic_manifest_ref: stable_ref
  frozen_F2_atomic_manifest_sha256: lowercase_sha256
  Jenn_fixture_decision_ref: stable_ref
  Jenn_fixture_decision_sha256: lowercase_sha256
  fixed_time_constants: closed_object
  ordered_genesis_subjects: F3SyntheticM0GenesisSubjectEntryV0_1R4[60]
  issuance_command_ref: stable_ref
  issuance_command_fingerprint: lowercase_sha256
  pending_delegation_ref: stable_ref
  pending_delegation_fingerprint: lowercase_sha256
  activation_command_ref: stable_ref
  activation_command_fingerprint: lowercase_sha256
  final_event_sequence: positive_safe_integer
  expected_final_state_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

The manifest fingerprint uses its R4 interface-version domain. Every subject
carrying `F3_contract_version` uses the R4 literal.

The exact enum order is:

```text
01 F2_JENN_ACTOR_IDENTITY_REVISION
02 F2_JENN_AUTHENTICATOR_PROFILE_REVISION
03 F2_JENN_PRINCIPAL_REVISION
04 F2_JENN_PRINCIPAL_BINDING_REVISION
05 F2_JENN_BINDING_ACTIVATION_EVIDENCE
06 F2_JENN_ROOT_RELATION
07 F2_JENN_ROOT_DIRECTION
08 F2_SYNTHETIC_TRUSTED_TIME_DECISION
09 F2_SYNTHETIC_PROHIBITED_BOUNDARY_EVIDENCE
10 F2_COORDINATOR_ACTOR_IDENTITY_REVISION
11 F2_SYNTHETIC_M0_MANIFEST_CREATE
12 F2_SYNTHETIC_M0_MANIFEST_ACCEPT
13 F2_COORDINATOR_AUTHENTICATOR_PROFILE_REVISION
14 F2_COORDINATOR_PRINCIPAL_REVISION
15 F2_COORDINATOR_PRINCIPAL_BINDING_REVISION
16 F2_COORDINATOR_BINDING_ACTIVATION_EVIDENCE
17 F2_COORDINATOR_M0_ELIGIBILITY_ASSESSMENT
18 F2_JENN_AUTHENTICATION_ASSESSMENT
19 F2_COORDINATOR_AUTHENTICATION_ASSESSMENT
20 F3_RESIDENT_IDENTITY_REVISION
21 F3_AUTHORITY_WITNESS_RESERVATION_EPOCH_1
22 F3_RESIDENT_AUTHORITY_EPOCH_1
23 F3_AUTHORITY_WITNESS_COMMIT_EPOCH_1
24 F3_RESIDENT_CONTINUITY_ASSESSMENT_EPOCH_1
25 F3_RESIDENT_READY_PROJECTION_EPOCH_1
26 F3_DELEGATION_ISSUANCE_PAYLOAD_SCHEMA_DESCRIPTOR
27 F3_DELEGATION_ISSUANCE_REDUCER_DESCRIPTOR
28 F3_DELEGATION_ISSUANCE_COMMAND_TYPE_DEFINITION
29 F3_JENN_ROOT_DIRECTION_COMMAND_ASSESSMENT
30 F3_DELEGATION_ISSUANCE_COMMAND
31 F3_DELEGATION_ISSUANCE_GATE_RESULT
32 F3_DELEGATION_ISSUANCE_CONTEXT
33 F3_DELEGATION_ISSUANCE_ENVELOPE
34 F2_DELEGATION_ISSUANCE_ACTION_REF
35 F2_PENDING_DELEGATION_GRANT
36 F3_DELEGATION_ISSUANCE_EVENT
37 F3_DELEGATION_ISSUANCE_INTAKE
38 F3_DELEGATION_ISSUANCE_REPLAY_ENTRY
39 F3_DELEGATION_ACTIVATION_PAYLOAD_SCHEMA_DESCRIPTOR
40 F3_DELEGATION_ACTIVATION_REDUCER_DESCRIPTOR
41 F3_DELEGATION_ACTIVATION_COMMAND_TYPE_DEFINITION
42 F3_DELEGATION_ACTIVATION_COMMAND
43 F3_DELEGATION_ACTIVATION_GATE_RESULT
44 F3_DELEGATION_ACTIVATION_CONTEXT
45 F3_DELEGATION_ACTIVATION_ENVELOPE
46 F2_DELEGATION_ACTIVATION_ACKNOWLEDGEMENT
47 F2_DELEGATION_ACTIVATION_EVIDENCE
48 F2_DELEGATION_ACTIVATION_ASSESSMENT
49 F3_DELEGATION_ACTIVATION_EVENT
50 F3_DELEGATION_ACTIVATION_INTAKE
51 F3_DELEGATION_ACTIVATION_REPLAY_ENTRY
52 F3_IDENTICAL_ACTIVATION_REPLAY_PROOF
53 F3_ALTERED_ACTIVATION_REPLAY_CONFLICT_PROOF
54 F3_AUTHORITY_WITNESS_RESERVATION_EPOCH_2
55 F3_RESIDENT_AUTHORITY_EPOCH_2
56 F3_AUTHORITY_WITNESS_COMMIT_EPOCH_2
57 F3_RESIDENT_CONTINUITY_ASSESSMENT_EPOCH_2
58 F3_RESIDENT_READY_PROJECTION_EPOCH_2
59 F3_RESTART_RECOVERY_READY_PROOF
60 F3_CONCURRENT_SECOND_INCARNATION_DENIAL_PROOF
```

The R3 exact mapping for rows 1-38 remains effective except these replacements:

| row | exact R4 schema/interface | predecessors |
|---:|---|---|
| 7 | `F3SyntheticJennRootDirectionInputV0_1R4` | 1,4-6 |
| 8 | `F3SyntheticTrustedTimeInputV0_1R4` | - |
| 9 | `F3SyntheticProhibitedBoundaryInputV0_1R4` | - |
| 25 | `ResidentReadyProjectionV0_1R4` | 8-9,17-24 |
| 28 | `CommandTypeDefinitionV0_1` exact R4 issuance instance | 26-27 |
| 30 | `CanonicalCommandV0_1` effective R4 bundle literal | 7,18,26,28-29 |
| 32 | `AuthenticatedCommandContextV0_1` effective R4 bundle literal | 18,20,22-25,30-31 |
| 33 | `CommandEnvelopeV0_1R2` effective R4 bundle literal | 28,30-32 |
| 34 | `AuthenticatedActorActionRefR4Effective` with R4 bundle literal | 18,32-33 |
| 36 | `F3LedgerEventV0_1R4` / `DELEGATION_ISSUED` | 30-35 |
| 37 | `F3CommandIntakeRecordV0_1R2` with R4 bundle literal | 30-36 |

Rows 39-60 map exactly as follows:

| # | kind | exact schema/interface | predecessors |
|---:|---|---|---|
| 39 | `F3_DELEGATION_ACTIVATION_PAYLOAD_SCHEMA_DESCRIPTOR` | `agents-os.delegation-activation-ack-payload-schema-descriptor.v0.1-r4` | - |
| 40 | `F3_DELEGATION_ACTIVATION_REDUCER_DESCRIPTOR` | `agents-os.delegation-activation-ack-reducer-descriptor.v0.1-r4` | 39 |
| 41 | `F3_DELEGATION_ACTIVATION_COMMAND_TYPE_DEFINITION` | `CommandTypeDefinitionV0_1` exact R4 activation instance | 39-40 |
| 42 | `F3_DELEGATION_ACTIVATION_COMMAND` | `CanonicalCommandV0_1` plus `DelegationActivationAckPayloadV0_1`, R4 literal | 19,25,35,39-41 |
| 43 | `F3_DELEGATION_ACTIVATION_GATE_RESULT` | effective `CommandGateResultV0_1R2` with R3 enum | 19,25,35,41-42 |
| 44 | `F3_DELEGATION_ACTIVATION_CONTEXT` | `AuthenticatedCommandContextV0_1`, R4 literal | 19,20,22-25,42-43 |
| 45 | `F3_DELEGATION_ACTIVATION_ENVELOPE` | `CommandEnvelopeV0_1R2`, R4 literal | 42-44 |
| 46 | `F2_DELEGATION_ACTIVATION_ACKNOWLEDGEMENT` | `DelegationActivationAcknowledgementRefR4Effective`, R4 literal | 15-16,35,44-45 |
| 47 | `F2_DELEGATION_ACTIVATION_EVIDENCE` | `DelegationActivationEvidenceR15Effective` | 35,46 |
| 48 | `F2_DELEGATION_ACTIVATION_ASSESSMENT` | `DelegationActivationAssessmentV0_1R16` | 35,46-47 |
| 49 | `F3_DELEGATION_ACTIVATION_EVENT` | `F3LedgerEventV0_1R4` / `DELEGATION_ACTIVATED` | 42-48 |
| 50 | `F3_DELEGATION_ACTIVATION_INTAKE` | `F3CommandIntakeRecordV0_1R2`, R4 literal | 42-49 |
| 51 | `F3_DELEGATION_ACTIVATION_REPLAY_ENTRY` | `CommandReplayEntryV0_1R2` | 42,45-50 |
| 52 | `F3_IDENTICAL_ACTIVATION_REPLAY_PROOF` | `F3SyntheticTraceProofV0_1R3` / `IDENTICAL_REPLAY` | 42,45,49-51 |
| 53 | `F3_ALTERED_ACTIVATION_REPLAY_CONFLICT_PROOF` | `F3SyntheticTraceProofV0_1R3` / `ALTERED_REPLAY_CONFLICT` | 42,49-52 |
| 54 | `F3_AUTHORITY_WITNESS_RESERVATION_EPOCH_2` | effective R4 witness reservation | 23,51 |
| 55 | `F3_RESIDENT_AUTHORITY_EPOCH_2` | `ResidentAuthorityEpochV0_1R3` | 22-23,54 |
| 56 | `F3_AUTHORITY_WITNESS_COMMIT_EPOCH_2` | effective R4 witness commit | 54-55 |
| 57 | `F3_RESIDENT_CONTINUITY_ASSESSMENT_EPOCH_2` | effective `ResidentIdentityContinuityAssessmentV0_1` | 20,48,55-56 |
| 58 | `F3_RESIDENT_READY_PROJECTION_EPOCH_2` | `ResidentReadyProjectionV0_1R4` | 9,48,51,55-57 |
| 59 | `F3_RESTART_RECOVERY_READY_PROOF` | `F3SyntheticTraceProofV0_1R3` / `RESTART_READY` | 51,54-58 |
| 60 | `F3_CONCURRENT_SECOND_INCARNATION_DENIAL_PROOF` | `F3SyntheticTraceProofV0_1R3` / `CONCURRENT_START_DENIED` | 54-59 |

Every inherited R3 row 1-38 not printed in the replacement table keeps its
exact R3 schema and predecessors. There is no implicit row between 1 and 60.
The array has exactly 60 entries, entry `i` uses enum value `i`, and every
predecessor number is lower than its subject. Missing, duplicate, extra,
unknown, misordered, wrong-schema, or wrong-version entries reject.

## 7. R4 invariants and mandatory negative cases

```text
F3-I43 one restore decision owns one immutable lineage claim
F3-I44 abandoned attempts may retry only inside the same contiguous claim chain
F3-I45 one claim has at most one COMMITTED attempt and no competing lineage use
F3-I46 every F3_contract_version field uses the R4 atomic-bundle literal
F3-I47 issuance and activation definitions share registry revision 4
F3-I48 activation payload, reducer, gates, and definition fingerprints are exact
F3-I49 the synthetic manifest contains exactly 60 schema-bound topological leaves
F3-I50 root direction, time, boundary, readiness, and Event leaves have exact schemas
```

Mandatory traces include:

```text
restore ordinal 1 abandoned, exact state unchanged -> ordinal 2 same claim allowed
abandoned claim reused by different decision/lineage/backup/R/H -> INDETERMINATE
two live reservations for one claim -> INDETERMINATE
one claim with ABANDONED and COMMITTED for the same ordinal -> INDETERMINATE
one claim with two COMMITTED attempts -> INDETERMINATE
older R1/R2/R3 F3_contract_version in any graph node -> version mismatch
mixed R4 Command and R2 envelope/action/ack -> fingerprint/schema rejection
issuance definition revision 3 under registry revision 4 -> rejected
activation payload/reducer descriptor byte changed under old digest -> rejected
activation definition missing, altered, or wrong target/gate/ref -> rejected
synthetic manifest cardinality 57 or 59 or 61 -> rejected
activation Command without rows 39-41 -> rejected
rows 7/8/9/25/36/49/58 under a descriptive or alternate schema -> rejected
READY projection omitting witness/continuity/ledger head -> rejected
Event containing intake fingerprint or mismatched event kind -> rejected
```

## 8. Atomic acceptance and non-authorization

```yaml
acceptance_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE
subjects:
  - F3_R1_exact_sha256_e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
  - F3_R2_exact_sha256_4cd066dacf0f73d21566640a25c5cf5e90ca800ed4a793827c5088936703b236
  - F3_R3_exact_sha256_8a25b247a0618ab06ef6186464405b9d137bf68967a9952647986562cb93244c
  - this_exact_R4_document_sha256_after_author_closeout
precedence:
  - R4_explicit_replacements
  - R3_other_explicit_replacements
  - R2_other_explicit_replacements
  - R1_all_other_clauses
partial_acceptance: forbidden
acceptance_authority: Jenn
fresh_full_atomic_independent_review_required: true
review_must_be_hash_bound: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F4_automatic_start: forbidden
```

A passing fresh review creates only a Jenn atomic decision surface. R4 does not
accept or freeze F3 and does not authorize Rust/JavaScript implementation,
database work, Resident/service startup, runtime/plugin activation, production
authentication, crypto, keys, credentials, provider/executor calls, host/fence/
TaskPermit/Outbox/effect behavior, F4/F5/F6, public API/MCP expansion, commit,
push, PR, merge, release, deploy, publish, or tag.
