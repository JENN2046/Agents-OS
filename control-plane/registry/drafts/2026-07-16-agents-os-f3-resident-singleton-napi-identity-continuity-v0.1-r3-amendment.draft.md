# AGENTS OS F3 Resident Singleton, N-API, and Identity Continuity v0.1 R3 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R1 SHA-256: `e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e`  
Base R2 SHA-256: `4cd066dacf0f73d21566640a25c5cf5e90ca800ed4a793827c5088936703b236`  
Blocking R2 independent-review SHA-256: `3c4874507aac86f8b66cd540c4466b0dfc386a9e620f7c62b0043d292aca2afe`

## 1. Scope, precedence, and fixed inputs

This is the narrow R3 correction authorized by the immutable R3 start decision.
It closes only these accepted independent-review findings:

```text
F3-R2-FULL-ATOMIC-IR-M01
  contradictory no-intake versus persisted-terminal readiness semantics

F3-R2-FULL-ATOMIC-IR-M02
  non-total authority-epoch ordering after an explicit older-ledger restore

F3-R2-FULL-ATOMIC-IR-M03
  incomplete issuance CommandTypeDefinition and unclosed synthetic-manifest vocabulary
```

The effective reading order is:

```text
1. R3 explicit replacements
2. R2 explicit replacements not replaced by R3
3. R1 all other clauses
4. frozen F2 R1-R22 atomic bundle for every F2-owned shape and reducer
```

R1 and R2 are immutable inputs. R3 does not rewrite their bytes. An R3 clause
replaces an earlier clause only where this document says so explicitly. Every
other earlier invariant, failure rule, exclusion, and non-authorization remains
in force.

This document is a contract review subject only. It creates no implementation,
database, service, runtime, production-authentication, provider, effect,
TaskPermit, host, fence, F4, F5, or F6 authority.

## 2. Closed pre-intake readiness boundary

This section replaces the Command-intake meaning of R1 Sections 8 and 9 and the
readiness/lifecycle reason-code and transaction-order portions of R2 Sections
2.3 and 2.7. It does not change query or reserved-method behavior.

### 2.1 Two readiness observations and one persistence boundary

`execute_command` uses this total order:

```text
1. decode and validate the closed N-API request frame in memory
2. derive the canonical Command bytes and fingerprint in memory
3. observe the public Resident lifecycle projection before ledger-thread enqueue
4. if that observation is not READY, return a pre-intake response and do not enqueue
5. on the one ledger thread, begin the authoritative transaction
6. recheck lifecycle, lock, incarnation, epoch, generation, witness, continuity,
   one-connection ownership, schema support, and ledger integrity at one barrier
7. if that recheck is not proven READY and CONTINUOUS, roll back the transaction,
   return a pre-intake response, and persist nothing
8. only after the successful recheck may the transaction look up the replay ref,
   derive CommandGateResult, and open canonical intake
```

The transaction in step 5 may be opened only when step 3 observed `READY`. A
race from `READY` to another lifecycle value may therefore open a transaction,
but it never opens canonical intake and never writes. A call first observed in
`COLD`, `RECOVERING`, `DRAINING`, `STOPPED`, or `INDETERMINATE` does not open a
ledger transaction.

The persistence boundary is the successful step-6 barrier. Before it:

```text
no command_id is reserved
no replay_entry_ref is looked up or reserved
no CommandGateResult exists
no F3CommandIntakeRecord exists
no CommandReplayEntry exists
no envelope, action, activation, Event, domain fact, or Current State exists
```

Frame/schema failure remains an unpersisted protocol rejection under R1. An
integrity failure that prevents proving the step-6 facts returns fail-closed and
writes nothing. Neither case is a persisted rejected Command.

### 2.2 `F3PreIntakeUnavailableResultV0_1R3`

The only readiness/lifecycle response before canonical intake is:

```yaml
F3PreIntakeUnavailableResultV0_1R3:
  interface_version: agents-os.f3-pre-intake-unavailable-result.v0.1-r3
  method_id: execute_command
  request_id: stable_ref
  canonical_command_fingerprint: lowercase_sha256
  disposition: CONTRACT_NOT_ACTIVE | INDETERMINATE
  reason_code: closed_pre_intake_reason
  observed_lifecycle: COLD | RECOVERING | READY | DRAINING | STOPPED | INDETERMINATE
  retry_semantics: NEW_ELIGIBILITY_ATTEMPT_NO_COMMAND_ID_RESERVED
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under:

```text
agents-os.f3-pre-intake-unavailable-result.v0.1-r3
```

The closed `reason_code` order and exact response mapping are:

| reason code | disposition | required observed lifecycle |
|---|---|---|
| `RESIDENT_COLD` | `CONTRACT_NOT_ACTIVE` | `COLD` |
| `RESIDENT_RECOVERING` | `CONTRACT_NOT_ACTIVE` | `RECOVERING` |
| `RESIDENT_DRAINING` | `CONTRACT_NOT_ACTIVE` | `DRAINING` |
| `RESIDENT_STOPPED` | `CONTRACT_NOT_ACTIVE` | `STOPPED` |
| `RESIDENT_LIFECYCLE_INDETERMINATE` | `INDETERMINATE` | `INDETERMINATE` |
| `WRITER_RECHECK_NOT_READY` | `INDETERMINATE` | any value reached after an earlier `READY` observation |
| `IDENTITY_CONTINUITY_NOT_CONTINUOUS` | `INDETERMINATE` | `READY` or `INDETERMINATE` |
| `AUTHORITY_WITNESS_NOT_CURRENT` | `INDETERMINATE` | `READY` or `INDETERMINATE` |
| `LEDGER_INTEGRITY_NOT_PROVABLE` | `INDETERMINATE` | `READY` or `INDETERMINATE` |

Unknown, multiple, mismatched, or caller-supplied reason values reject. The
result is a low-disclosure response record, not ledger evidence, authority,
authorization, intake, replay, or a reservation. It contains no raw proof,
credential, SQL, path, provider response, or private state.

### 2.3 Corrected persistable gate-result enum

R3 removes these four R2 values from the persistable
`CommandGateResultV0_1R2.reason_codes` enum:

```text
RESIDENT_LIFECYCLE_NOT_READY
RESIDENT_READINESS_INDETERMINATE
IDENTITY_CONTINUITY_DISCONTINUOUS
IDENTITY_CONTINUITY_INDETERMINATE
```

They are not aliases and must not appear in a gate result, intake record, or
replay entry. The complete effective persistable enum is now:

```text
ACTOR_NOT_ACTIVE
ACTOR_CURRENTNESS_INDETERMINATE
PRINCIPAL_BINDING_NOT_ACTIVE
PRINCIPAL_BINDING_CURRENTNESS_INDETERMINATE
AUTHENTICATION_NOT_AUTHENTICATED
AUTHENTICATION_CURRENTNESS_INDETERMINATE
RESPONSIBILITY_NOT_ACTIVE
RESPONSIBILITY_CURRENTNESS_INDETERMINATE
TEMPORARY_WORKER_BINDING_NOT_ACTIVE
TEMPORARY_WORKER_BINDING_CURRENTNESS_INDETERMINATE
PROHIBITED_BOUNDARY_UNSATISFIED
PROHIBITED_BOUNDARY_INDETERMINATE
TRUSTED_TIME_OUTSIDE_VALIDITY
TRUSTED_TIME_INDETERMINATE
TARGET_REVISION_CONFLICT
DOMAIN_INVARIANT_REJECTED
REDUCER_INPUT_INDETERMINATE
COMMAND_DEFINITION_NOT_CURRENT
```

R2 result-shape rules remain unchanged for this smaller enum. A persistable
gate result exists only after the pre-intake barrier proves `READY`, exact
`CONTINUOUS`, and current authority witness/epoch/generation ownership.

### 2.4 Corrected first-submission and retry semantics

R2 Section 2.7 begins only after Section 2.1 step 8. Its existing-entry and
no-entry branches then remain exact. The four removed readiness/continuity codes
can never enter the `no entry + gate result` branches.

The retry rules are total:

```text
pre-intake unavailable response, then identical request after READY
  -> first eligibility attempt for canonical intake
  -> no prior command_id or replay disposition exists
  -> current gates may commit, persist REJECTED, or persist INDETERMINATE

persisted REJECTED or persisted gate-derived INDETERMINATE, then identical retry
  -> exact first persisted disposition; no gate reevaluation

existing command_id with changed canonical fingerprint
  -> PROTOCOL_CONFLICT; no mutation
```

This preserves the accepted Resident Architecture rule that a **persisted**
rejected Command is replayable while making it explicit that unavailable
Resident readiness never creates such a persisted Command.

## 3. Global authority epoch and explicit restore lineage

This section replaces R2 Sections 5.2-5.5 where they define authority-epoch
ordering, reservation/commit fields, and explicit older-ledger restore. R2's OS
lock, one-writer, witness durability, crash finalization, and fail-closed rules
remain in force.

### 3.1 One global high-watermark

For one `witness_id`, the durable witness journal owns one global committed
authority-epoch sequence across every ledger restore lineage:

```text
H = maximum authority_epoch among every valid COMMITTED witness entry
```

The reducer is total:

```text
no COMMITTED entries
  -> H = 0; no committed epoch fingerprint; genesis only

one or more valid COMMITTED entries with strictly increasing unique epochs
  -> H = the unique maximum; bind its witness and epoch fingerprints

duplicate epoch, decreasing epoch, forked generation, missing predecessor
commit, invalid fingerprint, truncated history, or unprovable maximum
  -> INDETERMINATE; no reservation, epoch, continuity, or READY
```

Every later COMMITTED witness entry uses exactly `H + 1`. An abandoned
reservation consumes a witness generation but consumes no authority epoch.
Therefore no retained witness history can contain two COMMITTED entries with
the same authority epoch.

### 3.2 R3 reservation and commit schemas

R3 replaces the R2 reservation and commit schemas with:

```yaml
ResidentAuthorityWitnessReservationV0_1R3:
  interface_version: agents-os.resident-authority-witness-reservation.v0.1-r3
  reservation_ref: stable_ref
  witness_id: stable_ref
  witness_generation: positive_safe_integer
  expected_previous_committed_generation: safe_integer
  previous_committed_witness_fingerprint: lowercase_sha256 | null
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  intended_authority_epoch: positive_safe_integer
  previous_global_authority_epoch_high_watermark: safe_integer
  previous_global_authority_epoch_fingerprint: lowercase_sha256 | null
  expected_previous_ledger_authority_epoch: positive_safe_integer | null
  expected_previous_ledger_epoch_fingerprint: lowercase_sha256 | null
  authority_lineage_id: stable_ref
  previous_authority_lineage_id: stable_ref | null
  restore_gap_start: positive_safe_integer | null
  restore_gap_end: positive_safe_integer | null
  incarnation_id: stable_ref
  restore_decision_ref: stable_ref | null
  restore_decision_fingerprint: lowercase_sha256 | null
  state: RESERVED
  canonical_fingerprint: lowercase_sha256

ResidentAuthorityWitnessCommitV0_1R3:
  interface_version: agents-os.resident-authority-witness-commit.v0.1-r3
  witness_id: stable_ref
  witness_generation: positive_safe_integer
  reservation_ref: stable_ref
  reservation_fingerprint: lowercase_sha256
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  authority_epoch: positive_safe_integer
  previous_global_authority_epoch_high_watermark: safe_integer
  authority_lineage_id: stable_ref
  authority_epoch_ref: stable_ref
  authority_epoch_fingerprint: lowercase_sha256
  incarnation_id: stable_ref
  ownership_started_event_sequence: positive_safe_integer
  restore_decision_ref: stable_ref | null
  restore_decision_fingerprint: lowercase_sha256 | null
  state: COMMITTED
  canonical_fingerprint: lowercase_sha256
```

Each fingerprint is SHA-256 JCS over its complete displayed field order,
excluding `canonical_fingerprint`, under its interface-version domain. The R3
reservation ref is:

```text
lowercase SHA-256(JCS([
  "agents-os.resident-authority-witness-reservation-ref.v0.1-r3",
  witness_id,
  witness_generation,
  intended_authority_epoch,
  authority_lineage_id
]))
```

The R2 abandonment schema remains effective and may name an R3 reservation. An
abandonment never changes the global committed high-watermark.

### 3.3 `ResidentAuthorityEpochV0_1R3`

R3 replaces the R2 epoch schema with:

```yaml
ResidentAuthorityEpochV0_1R3:
  interface_version: agents-os.resident-authority-epoch.v0.1-r3
  resident_identity_ref: stable_ref
  resident_identity_fingerprint: lowercase_sha256
  authority_epoch: positive_safe_integer
  expected_previous_authority_epoch: positive_safe_integer | null
  previous_authority_epoch_fingerprint: lowercase_sha256 | null
  previous_global_authority_epoch_high_watermark: safe_integer
  authority_lineage_id: stable_ref
  previous_authority_lineage_id: stable_ref | null
  restore_gap_start: positive_safe_integer | null
  restore_gap_end: positive_safe_integer | null
  authority_generation: positive_safe_integer
  witness_reservation_ref: stable_ref
  witness_reservation_fingerprint: lowercase_sha256
  incarnation_id: stable_ref
  previous_incarnation_id: stable_ref | null
  restore_decision_ref: stable_ref | null
  restore_decision_fingerprint: lowercase_sha256 | null
  ownership_started_event_sequence: positive_safe_integer
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under:

```text
agents-os.resident-authority-epoch.v0.1-r3
```

`authority_epoch` is globally ordered by the external witness. The
`expected_previous_authority_epoch` and predecessor fingerprint are the exact
head actually present in the current ledger transaction. The normal branch
requires both values to describe the same immediate predecessor. The restore
branch intentionally distinguishes global order from restored-ledger CAS.

### 3.4 Exact normal and older-restore branches

Genesis is:

```text
H = 0
authority_epoch = 1
expected_previous_authority_epoch = null
previous_global_authority_epoch_high_watermark = 0
one new authority_lineage_id
previous_authority_lineage_id = null
restore_gap_start = restore_gap_end = null
restore decision = null
```

Normal restart is legal only when the ledger head equals the unique global
committed high-watermark `H` and its fingerprint matches the witness:

```text
authority_epoch = H + 1
expected_previous_authority_epoch = H
previous_global_authority_epoch_high_watermark = H
authority_lineage_id = previous authority_lineage_id
previous_authority_lineage_id = same authority_lineage_id
restore_gap_start = restore_gap_end = null
restore decision = null
```

An explicit older-ledger restore is legal only when all R2 restore-decision
fields reproduce and the restored ledger head `R` is lower than retained global
high-watermark `H`. The exact one-time restore boundary is:

```text
authority_epoch = H + 1
expected_previous_authority_epoch = R
previous_authority_epoch_fingerprint = exact restored head R fingerprint
previous_global_authority_epoch_high_watermark = H
authority_lineage_id = exact new_restore_lineage_id from Jenn decision
previous_authority_lineage_id = lineage id of restored head R
restore_gap_start = R + 1
restore_gap_end = H
restore decision ref/fingerprint = exact current matching Jenn decision
witness generation = highest journal generation of any state + 1
```

The transaction CASes the exact restored ledger head `R`; the external witness
CASes the unique global committed high-watermark `H`. Both must succeed before
the R3 witness COMMIT is appended. This is the only exception to the R2
ledger-local `N + 1` rule. It never skips the global sequence: the new value is
exactly `H + 1`.

The restore decision's `new_restore_lineage_id` must never have appeared in any
ledger epoch, reservation, commit, or earlier decision. A decision is consumed
only by the one matching COMMITTED restore boundary. Reuse, a different backup,
a different `R`, a changed witness `H`, an empty gap, a stale generation, or a
missing predecessor fingerprint fails closed.

After the restore boundary, the ledger head is `H + 1`. Every later normal
restart follows the normal rule at `H + 2`, retains the new lineage id, and has
null restore fields. Retained earlier commits remain immutable historical
members of the single global ordering.

### 3.5 Crash-total restore behavior

The existing crash rules specialize as follows:

```text
restore reservation G exists; restored ledger has no epoch binding G
  -> ABANDON G; retain global H; require a new decision-current recheck and later G

restored ledger has exact H+1 epoch binding pending reservation G
  -> finalize only that exact witness COMMIT; never allocate another H+1

COMMITTED restore witness H+1 but ledger head is R or mismatched
  -> rollback detected; INDETERMINATE; decision does not authorize repair

retained witness high-watermark changes between decision check and reservation
  -> stale decision/witness binding; write nothing
```

No restore branch fabricates lost Events or F2 facts, turns a non-ACTIVE F2
assessment into ACTIVE, or reaches READY before full replay, continuity,
integrity, and prohibited-boundary checks pass.

## 4. Complete Delegation issuance registry instance

This section replaces R2's incomplete
`DelegationIssuanceCommandTypeV0_1R2` block. The R2 payload field semantics and
issuance graph remain unchanged.

### 4.1 Exact payload-schema descriptor

The payload schema digest is SHA-256 over the exact UTF-8 bytes of this one-line
JCS value, with no newline included in the digest input:

```json
{"additional_properties":false,"interface_version":"agents-os.delegation-issuance-command-payload-schema-descriptor.v0.1-r3","ordered_fields":[["payload_schema_version","literal:agents-os.delegation-issuance-command-payload.v0.1-r2"],["delegation_id","stable_ref"],["delegation_revision","positive_safe_integer"],["expected_previous_delegation_revision","positive_safe_integer|null"],["supersedes_delegation_revision","positive_safe_integer|null"],["delegator_actor_id","stable_ref"],["delegator_identity_revision","positive_safe_integer"],["delegate_actor_id","stable_ref"],["delegate_identity_revision","positive_safe_integer"],["parent_delegation_ref","stable_ref|null"],["source_responsibility_ref","stable_ref"],["responsibility_kind","stable_ref"],["responsibility_scope","F2_ResponsibilityScopeV0_1R7"],["may_redelegate","boolean"],["remaining_depth","safe_integer"],["not_before_utc_ms","safe_integer"],["expires_at_utc_ms","safe_integer"],["activation_mode","EXPLICIT_ACK|WORKER_ASSIGNMENT_HANDSHAKE"],["issued_by_actor_id","stable_ref"],["issued_by_actor_identity_revision","positive_safe_integer"],["issued_by_principal_binding_ref","stable_ref"],["issuer_currentness_event_sequence","positive_safe_integer"],["root_direction_ref","stable_ref|null"],["root_direction_fingerprint","lowercase_sha256|null"],["source_assignment_ref","stable_ref|null"],["source_assignment_fingerprint","lowercase_sha256|null"],["reason_code","TASK_HANDOFF|RUN_EXECUTION|DOMAIN_OPERATION|INCIDENT_RESPONSE|MAINTENANCE"],["reason_artifact_ref","F2_ResponsibilityResourceRefV0_1|null"],["status","literal:ACTIVE"]],"rules":["field_order_is_exact","unknown_fields_and_unknown_enum_values_reject","root_direction_ref_and_fingerprint_are_both_null_or_both_present","source_assignment_ref_and_fingerprint_are_both_null_or_both_present","command_supplies_no_action_envelope_event_final_delegation_or_activation_evidence"],"schema_ref":"agents-os.delegation-issuance-command-payload.v0.1-r2"}
```

The required digest is:

```text
045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1
```

Any character, field, constraint, or digest difference rejects the definition.

### 4.2 Exact reducer descriptor

The reducer digest is SHA-256 over the exact UTF-8 bytes of this one-line JCS
value, with no newline included in the digest input:

```json
{"atomic_outputs":["CommandGateResult_ADMITTED","AuthenticatedCommandContext","CommandEnvelope","AuthenticatedActorActionRefR4Effective","DelegationGrantRevisionV0_1R19Effective_pending","DelegationIssuanceEvent","F3CommandIntakeRecord_COMMITTED","CommandReplayEntry_COMMITTED"],"effect_class":"LEDGER_ONLY","failure_semantics":["pre_intake_unavailability_writes_nothing","post_preflight_proven_negative_persists_REJECTED","post_preflight_unreproducible_gate_persists_INDETERMINATE","integrity_or_uniqueness_unprovable_writes_nothing"],"frozen_F2_manifest_sha256":"95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1","interface_version":"agents-os.delegation-issuance-reducer-descriptor.v0.1-r3","ordered_preconditions":["current_F2_actor_identity_ACTIVE","current_F2_principal_binding_ACTIVE","current_F2_authentication_AUTHENTICATED","current_F3_Jenn_root_direction_ACTIVE","current_prohibited_boundary_satisfied","current_trusted_time_inside_validity","F3_READY_and_CONTINUOUS_at_pre_intake_and_writer_recheck","target_revision_and_F2_R19_delegation_invariants_satisfied"],"payload_schema_sha256":"045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1","prohibited_outputs":["DelegationActivationEvidence","TaskPermit","host_admission","effect_execution","provider_call","external_operation"],"reducer_ref":"agents-os.delegation-issuance-reducer.v0.1-r3"}
```

The required digest is:

```text
4c4bac289945131cd556dd855398761cc940b150d2930b4f4453d103c1296e70
```

The descriptor is the exact F3 orchestration of the frozen F2 R19 effective
issuance reducer. It does not alter any frozen F2 subject schema or fingerprint.

### 4.3 Full `CommandTypeDefinitionV0_1` instance

```yaml
DelegationIssuanceCommandTypeDefinitionV0_1R3:
  interface_version: agents-os.command-type-definition.v0.1
  registry_revision: 3
  command_type_id: DELEGATION_ISSUANCE
  command_type_version: 1
  owner_contract_ref: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE
  owner_contract_sha256: 95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1
  payload_schema_ref: agents-os.delegation-issuance-command-payload.v0.1-r2
  payload_schema_sha256: 045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1
  allowed_target_kinds:
    - F2_DELEGATION_REVISION
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
    - agents-os.gate.f3.resident-ready-continuous.v0.1-r3
    - agents-os.gate.f3.trusted-time-current.v0.1
  maximum_validity_duration_ms: 60000
  unknown_fields_policy: REJECT
  canonical_fingerprint: 549553a694a1d95f58932db1831b817f3cf4f744f4e33a73dbfc9ba233a5a07f
```

The required-gate list is bytewise sorted. The fingerprint is the R1 Section
10.1 formula over the complete displayed values. Its exact JCS input is:

```json
["agents-os.command-type-definition.v0.1",3,"DELEGATION_ISSUANCE",1,"F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R22_ATOMIC_BUNDLE","95bed046e98737efd86bd73f528594620a137d03ed179dd95bbb98a537cc11d1","agents-os.delegation-issuance-command-payload.v0.1-r2","045f1f13910b04589ca0c65e4536b3a8b253e70c37ff59d92caca6ccb51ef2c1",["F2_DELEGATION_REVISION"],"REQUIRED","REQUIRED","LEDGER_ONLY","agents-os.delegation-issuance-reducer.v0.1-r3","4c4bac289945131cd556dd855398761cc940b150d2930b4f4453d103c1296e70",["agents-os.gate.f2.actor-identity-active.v0.1","agents-os.gate.f2.authentication-authenticated.v0.1","agents-os.gate.f2.principal-binding-active.v0.1","agents-os.gate.f3.jenn-root-direction-active.v0.1-r2","agents-os.gate.f3.prohibited-boundary-current.v0.1","agents-os.gate.f3.resident-ready-continuous.v0.1-r3","agents-os.gate.f3.trusted-time-current.v0.1"],60000,"REJECT"]
```

No runtime self-registration or alternate registry revision is permitted.

## 5. Closed synthetic M0 subject vocabulary and mapping

This section replaces R2 Section 6.6. R2 Sections 6.2-6.5 continue to define
the fixed values and trace. The manifest is a summary of fully materialized
objects, never a shortcut that manufactures an object.

### 5.1 Manifest and entry schemas

```yaml
F3SyntheticM0GenesisSubjectEntryV0_1R3:
  kind: F3SyntheticM0ClosedSubjectKindV0_1R3
  subject_ref: stable_ref
  subject_fingerprint: lowercase_sha256

F3SyntheticM0GenesisManifestV0_1R3:
  interface_version: agents-os.f3-synthetic-m0-genesis-manifest.v0.1-r3
  fixture_namespace: agents-os.synthetic.f3-r2.m0
  frozen_F2_acceptance_decision_ref: stable_ref
  frozen_F2_acceptance_decision_sha256: lowercase_sha256
  frozen_F2_atomic_manifest_ref: stable_ref
  frozen_F2_atomic_manifest_sha256: lowercase_sha256
  Jenn_fixture_decision_ref: stable_ref
  Jenn_fixture_decision_sha256: lowercase_sha256
  fixed_time_constants: closed_object
  ordered_genesis_subjects: F3SyntheticM0GenesisSubjectEntryV0_1R3[57]
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

The manifest fingerprint is SHA-256 JCS over the complete displayed field
order, excluding `canonical_fingerprint`, under its interface-version domain.
The three top-level Command/Delegation refs must equal the matching entries in
the 57-entry array. A mismatch or duplicate rejects.

### 5.2 Exact closed enum order

`F3SyntheticM0ClosedSubjectKindV0_1R3` contains exactly these values in this
order:

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
39 F3_DELEGATION_ACTIVATION_COMMAND
40 F3_DELEGATION_ACTIVATION_GATE_RESULT
41 F3_DELEGATION_ACTIVATION_CONTEXT
42 F3_DELEGATION_ACTIVATION_ENVELOPE
43 F2_DELEGATION_ACTIVATION_ACKNOWLEDGEMENT
44 F2_DELEGATION_ACTIVATION_EVIDENCE
45 F2_DELEGATION_ACTIVATION_ASSESSMENT
46 F3_DELEGATION_ACTIVATION_EVENT
47 F3_DELEGATION_ACTIVATION_INTAKE
48 F3_DELEGATION_ACTIVATION_REPLAY_ENTRY
49 F3_IDENTICAL_ACTIVATION_REPLAY_PROOF
50 F3_ALTERED_ACTIVATION_REPLAY_CONFLICT_PROOF
51 F3_AUTHORITY_WITNESS_RESERVATION_EPOCH_2
52 F3_RESIDENT_AUTHORITY_EPOCH_2
53 F3_AUTHORITY_WITNESS_COMMIT_EPOCH_2
54 F3_RESIDENT_CONTINUITY_ASSESSMENT_EPOCH_2
55 F3_RESIDENT_READY_PROJECTION_EPOCH_2
56 F3_RESTART_RECOVERY_READY_PROOF
57 F3_CONCURRENT_SECOND_INCARNATION_DENIAL_PROOF
```

The array has cardinality 57. Entry `i` must use enum value `i`; every value
appears once; no other kind is legal.

### 5.3 Exact schema and predecessor mapping

The exact mapping is below. `-` means no predecessor inside this manifest;
authority inputs remain the fixed Jenn/F2 decision and manifest hashes.
Comma-separated predecessors mean every named earlier entry is required.

| # | kind | exact schema/interface | required predecessor kinds |
|---:|---|---|---|
| 1 | `F2_JENN_ACTOR_IDENTITY_REVISION` | `ActorIdentityRevisionV0_1R8` | - |
| 2 | `F2_JENN_AUTHENTICATOR_PROFILE_REVISION` | `AuthenticatorProfileRevisionR9Effective` | 1 |
| 3 | `F2_JENN_PRINCIPAL_REVISION` | `PrincipalRevisionR9Effective` | 2 |
| 4 | `F2_JENN_PRINCIPAL_BINDING_REVISION` | `ActorPrincipalBindingRevisionR10Effective` | 1,3 |
| 5 | `F2_JENN_BINDING_ACTIVATION_EVIDENCE` | `BindingActivationEvidenceR15Effective` | 4 |
| 6 | `F2_JENN_ROOT_RELATION` | frozen F2 `JennRootGovernanceAuthorityRefV0_1R8` projection | 1,4,5 |
| 7 | `F2_JENN_ROOT_DIRECTION` | frozen F2 current Jenn-root direction fact | 6 |
| 8 | `F2_SYNTHETIC_TRUSTED_TIME_DECISION` | frozen F2 trusted-time decision interface | - |
| 9 | `F2_SYNTHETIC_PROHIBITED_BOUNDARY_EVIDENCE` | frozen F2 prohibited-boundary evidence interface | - |
| 10 | `F2_COORDINATOR_ACTOR_IDENTITY_REVISION` | `ActorIdentityRevisionV0_1R8` | 1,7 |
| 11 | `F2_SYNTHETIC_M0_MANIFEST_CREATE` | `SyntheticM0PrincipalProvisioningManifestV0_1R8Effective` CREATE graph | 1,7,10 |
| 12 | `F2_SYNTHETIC_M0_MANIFEST_ACCEPT` | `SyntheticM0ManifestActivationRevisionV0_1R9` | 11 |
| 13 | `F2_COORDINATOR_AUTHENTICATOR_PROFILE_REVISION` | `AuthenticatorProfileRevisionR9Effective` | 11,12 |
| 14 | `F2_COORDINATOR_PRINCIPAL_REVISION` | `PrincipalRevisionR9Effective` | 11,12,13 |
| 15 | `F2_COORDINATOR_PRINCIPAL_BINDING_REVISION` | `ActorPrincipalBindingRevisionR10Effective` | 10,11,12,14 |
| 16 | `F2_COORDINATOR_BINDING_ACTIVATION_EVIDENCE` | `BindingActivationEvidenceR15Effective` | 12,15 |
| 17 | `F2_COORDINATOR_M0_ELIGIBILITY_ASSESSMENT` | `SyntheticM0ActorEligibilityAssessmentV0_1R13` | 10-16 |
| 18 | `F2_JENN_AUTHENTICATION_ASSESSMENT` | `AuthenticationAssessmentV0_1R15` | 1-5,8 |
| 19 | `F2_COORDINATOR_AUTHENTICATION_ASSESSMENT` | `AuthenticationAssessmentV0_1R15` | 10,13-17,8 |
| 20 | `F3_RESIDENT_IDENTITY_REVISION` | `ResidentIdentityRevisionV0_1` | 10,17 |
| 21 | `F3_AUTHORITY_WITNESS_RESERVATION_EPOCH_1` | `ResidentAuthorityWitnessReservationV0_1R3` | 20 |
| 22 | `F3_RESIDENT_AUTHORITY_EPOCH_1` | `ResidentAuthorityEpochV0_1R3` | 20,21 |
| 23 | `F3_AUTHORITY_WITNESS_COMMIT_EPOCH_1` | `ResidentAuthorityWitnessCommitV0_1R3` | 21,22 |
| 24 | `F3_RESIDENT_CONTINUITY_ASSESSMENT_EPOCH_1` | effective `ResidentIdentityContinuityAssessmentV0_1` | 10,17,20,22,23 |
| 25 | `F3_RESIDENT_READY_PROJECTION_EPOCH_1` | R1 closed Resident readiness projection | 8-9,17-24 |
| 26 | `F3_DELEGATION_ISSUANCE_PAYLOAD_SCHEMA_DESCRIPTOR` | `agents-os.delegation-issuance-command-payload-schema-descriptor.v0.1-r3` | - |
| 27 | `F3_DELEGATION_ISSUANCE_REDUCER_DESCRIPTOR` | `agents-os.delegation-issuance-reducer-descriptor.v0.1-r3` | 26 |
| 28 | `F3_DELEGATION_ISSUANCE_COMMAND_TYPE_DEFINITION` | `CommandTypeDefinitionV0_1` exact R3 instance | 26,27 |
| 29 | `F3_JENN_ROOT_DIRECTION_COMMAND_ASSESSMENT` | `F3JennRootDirectionCommandAssessmentV0_1R2` | 1-9,18,25 |
| 30 | `F3_DELEGATION_ISSUANCE_COMMAND` | `CanonicalCommandV0_1` effective R3 bundle | 7,18,26,28-29 |
| 31 | `F3_DELEGATION_ISSUANCE_GATE_RESULT` | effective `CommandGateResultV0_1R2` with R3 enum | 18,25,28-30 |
| 32 | `F3_DELEGATION_ISSUANCE_CONTEXT` | effective `AuthenticatedCommandContextV0_1` | 18,20,22-25,30-31 |
| 33 | `F3_DELEGATION_ISSUANCE_ENVELOPE` | effective `CommandEnvelopeV0_1R2` | 28,30-32 |
| 34 | `F2_DELEGATION_ISSUANCE_ACTION_REF` | `AuthenticatedActorActionRefR4Effective` | 18,32-33 |
| 35 | `F2_PENDING_DELEGATION_GRANT` | `DelegationGrantRevisionV0_1R19Effective` | 7,10,17,34 |
| 36 | `F3_DELEGATION_ISSUANCE_EVENT` | R1 closed F3 intake/Event projection | 33-35 |
| 37 | `F3_DELEGATION_ISSUANCE_INTAKE` | `F3CommandIntakeRecordV0_1R2` | 30-36 |
| 38 | `F3_DELEGATION_ISSUANCE_REPLAY_ENTRY` | `CommandReplayEntryV0_1R2` | 30,33,35,37 |
| 39 | `F3_DELEGATION_ACTIVATION_COMMAND` | `CanonicalCommandV0_1` plus `DelegationActivationAckPayloadV0_1` | 19,25,35 |
| 40 | `F3_DELEGATION_ACTIVATION_GATE_RESULT` | effective `CommandGateResultV0_1R2` with R3 enum | 19,25,35,39 |
| 41 | `F3_DELEGATION_ACTIVATION_CONTEXT` | effective `AuthenticatedCommandContextV0_1` | 19,20,22-25,39-40 |
| 42 | `F3_DELEGATION_ACTIVATION_ENVELOPE` | effective `CommandEnvelopeV0_1R2` | 39-41 |
| 43 | `F2_DELEGATION_ACTIVATION_ACKNOWLEDGEMENT` | `DelegationActivationAcknowledgementRefR4Effective` | 15-16,35,41-42 |
| 44 | `F2_DELEGATION_ACTIVATION_EVIDENCE` | `DelegationActivationEvidenceR15Effective` | 35,43 |
| 45 | `F2_DELEGATION_ACTIVATION_ASSESSMENT` | `DelegationActivationAssessmentV0_1R16` | 35,43-44 |
| 46 | `F3_DELEGATION_ACTIVATION_EVENT` | R1 closed F3 activation Event projection | 42-45 |
| 47 | `F3_DELEGATION_ACTIVATION_INTAKE` | `F3CommandIntakeRecordV0_1R2` | 39-46 |
| 48 | `F3_DELEGATION_ACTIVATION_REPLAY_ENTRY` | `CommandReplayEntryV0_1R2` | 39,42-47 |
| 49 | `F3_IDENTICAL_ACTIVATION_REPLAY_PROOF` | `F3SyntheticTraceProofV0_1R3` / `IDENTICAL_REPLAY` | 39,42,46-48 |
| 50 | `F3_ALTERED_ACTIVATION_REPLAY_CONFLICT_PROOF` | `F3SyntheticTraceProofV0_1R3` / `ALTERED_REPLAY_CONFLICT` | 39,46-49 |
| 51 | `F3_AUTHORITY_WITNESS_RESERVATION_EPOCH_2` | `ResidentAuthorityWitnessReservationV0_1R3` | 23,48 |
| 52 | `F3_RESIDENT_AUTHORITY_EPOCH_2` | `ResidentAuthorityEpochV0_1R3` | 22-23,51 |
| 53 | `F3_AUTHORITY_WITNESS_COMMIT_EPOCH_2` | `ResidentAuthorityWitnessCommitV0_1R3` | 51-52 |
| 54 | `F3_RESIDENT_CONTINUITY_ASSESSMENT_EPOCH_2` | effective `ResidentIdentityContinuityAssessmentV0_1` | 20,45,52-53 |
| 55 | `F3_RESIDENT_READY_PROJECTION_EPOCH_2` | R1 closed Resident readiness projection | 9,45,48,52-54 |
| 56 | `F3_RESTART_RECOVERY_READY_PROOF` | `F3SyntheticTraceProofV0_1R3` / `RESTART_READY` | 48,51-55 |
| 57 | `F3_CONCURRENT_SECOND_INCARNATION_DENIAL_PROOF` | `F3SyntheticTraceProofV0_1R3` / `CONCURRENT_START_DENIED` | 51-56 |

Numeric ranges in the predecessor column are inclusive entry numbers and are
only notation for the exact already-enumerated kinds. The table is normative;
an object under the wrong kind, wrong schema, wrong fingerprint domain, wrong
predecessor, later-before-earlier order, missing entry, duplicate entry, or
extra entry rejects the manifest.

### 5.4 Closed replay/restart/dual-start proof schema

```yaml
F3SyntheticTraceProofV0_1R3:
  interface_version: agents-os.f3-synthetic-trace-proof.v0.1-r3
  proof_kind: IDENTICAL_REPLAY | ALTERED_REPLAY_CONFLICT | RESTART_READY | CONCURRENT_START_DENIED
  subject_command_ref: stable_ref | null
  subject_command_fingerprint: lowercase_sha256 | null
  before_authority_epoch_ref: stable_ref
  before_authority_epoch_fingerprint: lowercase_sha256
  after_authority_epoch_ref: stable_ref
  after_authority_epoch_fingerprint: lowercase_sha256
  before_event_sequence: positive_safe_integer
  after_event_sequence: positive_safe_integer
  before_current_state_fingerprint: lowercase_sha256
  after_current_state_fingerprint: lowercase_sha256
  expected_result_code: closed_value
  denied_incarnation_id: stable_ref | null
  canonical_fingerprint: lowercase_sha256
```

Its fingerprint is SHA-256 JCS over the complete displayed field order,
excluding `canonical_fingerprint`, under its interface-version domain. The
shape rules are:

| proof kind | result | Command fields | epoch/event/state relation | denied incarnation |
|---|---|---|---|---|
| `IDENTICAL_REPLAY` | `REPLAYED_COMMITTED` | required | before = after for epoch, Event, and state | null |
| `ALTERED_REPLAY_CONFLICT` | `PROTOCOL_CONFLICT` | required; fingerprint is altered submission | before = after for epoch, Event, and state | null |
| `RESTART_READY` | `READY_CONTINUOUS` | null | after epoch = before global epoch + 1; Event/state reproduce exact recovery result | null |
| `CONCURRENT_START_DENIED` | `DUPLICATE_WRITER_DENIED` | null | before = after for epoch, Event, and state | required |

Unknown or inconsistent combinations reject. These records are synthetic
evidence only and cannot authorize runtime, a second writer, or an external
effect.

## 6. R3 invariants and mandatory negative cases

The effective bundle adds:

```text
F3-I33 readiness failure before the successful writer barrier creates no canonical intake
F3-I34 a pre-intake response reserves no command_id and is eligible for a later first intake
F3-I35 persistable gate reasons contain no Resident lifecycle or continuity code
F3-I36 every COMMITTED witness authority epoch is globally unique and strictly increasing
F3-I37 normal restart requires ledger head = global committed epoch high-watermark
F3-I38 older restore commits exactly global H+1 while CASing exact restored head R
F3-I39 one new restore lineage and one explicit gap bind the retained witness history
F3-I40 issuance CommandTypeDefinition has exact schema, reducer, gates, revision, and fingerprint
F3-I41 synthetic M0 manifest contains exactly 57 topologically mapped subjects
F3-I42 replay, restart, and concurrent-denial evidence use one closed proof schema
```

Mandatory proof or negative traces are:

```text
call observed COLD -> CONTRACT_NOT_ACTIVE; no transaction and no intake
READY before enqueue, DRAINING at writer recheck -> rollback; no intake
READY but continuity INDETERMINATE at writer recheck -> no gate result or replay entry
same request retried after READY -> first eligible intake, not replay of unavailable response
persisted REJECTED retried after gate changes -> exact first rejection
removed lifecycle reason supplied in CommandGateResult -> schema rejection
witness commits epochs 7, 8, 9; restore ledger epoch 6 -> reserve global 10, never 7
restore epoch 6 with H=9 -> predecessor CAS 6, gap 7..9, new lineage, global epoch 10
restore decision reused for a second boundary -> INDETERMINATE
normal restart with ledger head below witness H -> INDETERMINATE
duplicate COMMITTED authority_epoch in retained witness -> INDETERMINATE
issuance payload descriptor byte changed with old digest -> definition rejected
issuance reducer descriptor byte changed with old digest -> definition rejected
unsorted gate refs or wrong target kind -> definition rejected
synthetic manifest with 56, 58, duplicate, unknown, or out-of-order kinds -> rejected
synthetic kind mapped to wrong schema or predecessor fingerprint -> rejected
identical replay proof with changed Event sequence -> rejected
concurrent-start proof with a mutation or missing denied incarnation -> rejected
```

## 7. Atomic acceptance and stopping rule

```yaml
acceptance_unit_id: F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R3_ATOMIC_BUNDLE
subjects:
  - F3_R1_exact_sha256_e439b3178984ac28ae584a961e2e0dc2248002592f0fb571e5e0db05d117a70e
  - F3_R2_exact_sha256_4cd066dacf0f73d21566640a25c5cf5e90ca800ed4a793827c5088936703b236
  - this_exact_R3_document_sha256_after_author_closeout
precedence:
  - R3_explicit_replacements
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

The F3 core freeze gate is satisfied only when a fresh independent reviewer:

```text
recomputes the fixed R1, R2, and R3 hashes
reviews the complete effective three-subject bundle
recomputes both descriptor digests and the CommandTypeDefinition fingerprint
checks all 57 manifest kinds and predecessor mappings
constructs normal restart and older-ledger restore witnesses
finds zero blocker or major identity-spoofing, dual-writer, rollback/currentness,
replay, circular-proof, authority-expansion, downstream-boundary, synthetic-M0,
or internal-contradiction findings
```

A passing review creates only a Jenn atomic acceptance surface. It does not
accept or freeze F3 automatically.

## 8. Non-authorization

This R3 subject and any review package built from it do not authorize:

```text
Rust or JavaScript implementation
database creation, migration, connection, or write
Resident or service startup
runtime or plugin activation
production authentication, crypto, keys, credentials, or provider configuration
provider, executor, host, fence, TaskPermit, Outbox, or external effect
F4, F5, or F6 start
commit, push, PR, merge, deploy, release, publish, or tag
partial acceptance or automatic freeze
```
