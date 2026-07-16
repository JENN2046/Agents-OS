# AGENTS OS F2 Actor Identity and Delegation v0.1 R15 Canonical Assessment, Assignment Issuance, Stewardship and Assurance Closure Amendment

```yaml
document_type: foundation_contract_amendment
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R15_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r15
date: 2026-07-15
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Scope and precedence

R15 closes only the remaining canonical-reference defects in R1-R14:

```text
assessment and evidence canonicalization
Responsibility Assignment issuance binding
Identity Stewardship deterministic derivation
CompromiseImpact total action mapping
complete effective materialization and review lineage
```

R15 has exact precedence over:

```text
R1 ActorIdentityAssessment, ResponsibilityAssignmentAssessment,
   DelegationAssessment, and AuthenticationAssessment schemas
R2 ResponsibilityAssignmentRevisionR2 and Assignment assessment additions
R2 IdentityRecoveryEvidence fingerprint semantics
R3/R4 fingerprint prose for legacy assessment/evidence objects
R7 ResponsibilityAssignmentAssessment reducer
R7 generic CompromiseImpact dependent-effect prose
R8 mutation-kind and target-kind enums for Assignment issuance
R8/R9 historical assurance mapping where R15 is more specific
```

All other R1-R14 rules remain effective. R1-R15 form one indivisible proposed
acceptance unit. Partial acceptance is forbidden.

## 2. F2 canonical assessment and evidence profile

### 2.1 Common canonical rule

Every effective F2 record classified below as an assessment, evidence, input
set, or derived relation uses:

```yaml
F2CanonicalDerivedRecordProfileV0_1R15:
  profile_version: agents-os.f2-canonical-derived-records.v0.1-r15
  hash_algorithm: SHA-256
  canonicalization: RFC_8785_JCS
  text_normalization: Unicode_15_1_NFC
  unknown_fields: REJECT
  undefined_values: REJECT
  normalized_key_collision: REJECT
  optional_absence: JSON_NULL_WHEN_FIELD_IS_IN_SCHEMA
  number_profile: F2CanonicalScalarProfileV0_1
  fingerprint_envelope: R4FingerprintEnvelope
```

For a registered schema with domain tag `D` and complete effective known object
`O`, excluding only `canonical_fingerprint`:

```text
canonical_fingerprint = SHA-256(JCS([D, O]))
```

Every field shown by the effective schema is present in `O`; optional values
use null. A `*_ref` is an exact normalized stable reference whose target
fingerprint is verified. A `*_fingerprint` contributes its verified lowercase
digest. `reason_codes` is sorted by NFC UTF-8 byte order and duplicate-free.
Other arrays use their owning schema's order; an array without an explicit
order is rejected.

### 2.2 Registered derived-record domains

| Effective record | Domain tag | Array order |
|---|---|---|
| `ActorIdentityAssessmentV0_1R15` | `agents-os.actor-identity-assessment.v0.1-r15` | `reason_codes` sorted |
| `AuthenticatorProfileAssessmentR7` | `agents-os.authenticator-profile-assessment.v0.1-r7` | `reason_codes` sorted |
| `CredentialHandleStatusAssessmentRefV0_1` | `agents-os.credential-handle-status-assessment-ref.v0.1` | none |
| `PrincipalAssessmentR7` | `agents-os.principal-assessment.v0.1-r7` | credential refs sorted by credential handle ref; reasons sorted |
| `PrincipalControlProofAssessmentRef` | `agents-os.principal-control-proof-assessment-ref.v0.1-r15` | none |
| `BindingActivationEvidenceR15Effective` | `agents-os.binding-activation-evidence.v0.1-r15` | none |
| `BindingActivationAssessmentR7` | `agents-os.binding-activation-assessment.v0.1-r7` | transition refs by Event then ID; reasons sorted |
| `ActorPrincipalBindingAssessmentR7` | `agents-os.actor-principal-binding-assessment.v0.1-r7` | credential refs sorted; transition refs by Event then ID; reasons sorted |
| `ResponsibilityAssignmentAssessmentV0_1R15` | `agents-os.responsibility-assignment-assessment.v0.1-r15` | transition refs by Event then ID; reasons sorted |
| `DelegationActivationEvidenceR15Effective` | `agents-os.delegation-activation-evidence.v0.1-r15` | none |
| `DelegationActivationAssessmentR7` | `agents-os.delegation-activation-assessment.v0.1-r7` | transition refs by Event then ID; reasons sorted |
| `DelegationAssessmentV0_1R15` | `agents-os.delegation-assessment.v0.1-r15` | lineage root-to-target; transition refs by Event then ID; reasons sorted |
| `AuthenticationAssessmentV0_1R15` | `agents-os.authentication-assessment.v0.1-r15` | reasons sorted |
| `HistoricalImpactInputSetV0_1` | `agents-os.historical-impact-input-set.v0.1` | impact streams by ID then revision |
| `HistoricalActionValidityAssessmentR15Effective` | `agents-os.historical-action-validity-assessment.v0.1-r15` | reasons sorted |
| `SyntheticM0ManifestAssessmentV0_1` | `agents-os.synthetic-m0-manifest-assessment.v0.1` | none |
| `SyntheticM0ActorEligibilityAssessmentV0_1R13` | `agents-os.synthetic-m0-actor-eligibility-assessment.v0.1-r13` | reasons sorted |
| `IdentityStewardshipAssessmentV0_1R15` | `agents-os.identity-stewardship-assessment.v0.1-r15` | responsibility evidence refs sorted by stable ref |
| `IdentityRecoveryEvidenceV0_1R15` | `agents-os.identity-recovery-evidence.v0.1-r15` | affected bindings and dispositions sorted by Binding stable ref |

This registry is closed for F2 v0.1. An unregistered assessment/evidence domain
cannot be used as a normative fingerprint input.

### 2.3 ActorIdentityAssessment replacement

```yaml
ActorIdentityAssessmentV0_1R15:
  actor_identity_ref:
  actor_identity_fingerprint:
  current_head_ref:
  current_head_fingerprint:
  assignment_assessment_ref: optional
  time_authority_ref:
  assessment: ACTIVE | SUSPENDED | COMPROMISED | RETIRED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

The assessment reads one complete current-head projection at
`based_on_event_sequence`. `current_head_ref` equals `actor_identity_ref` only
when the assessed revision is current. An older revision is `SUPERSEDED`.
Temporary Worker assignment evidence is mandatory; other classes use null.

### 2.4 Other legacy replacements

```yaml
AuthenticationAssessmentV0_1R15:
  authentication_assertion_ref:
  authentication_assertion_fingerprint:
  authenticator_profile_assessment_ref:
  principal_assessment_ref:
  binding_assessment_ref:
  credential_status_assessment_refs: []
  replay_assessment_ref:
  assessment: AUTHENTICATED | REJECTED | INDETERMINATE
  actor_identity_ref: optional
  principal_ref: optional
  binding_ref: optional
  verifier_revision:
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

IdentityRecoveryEvidenceV0_1R15:
  recovery_evidence_id:
  actor_identity_ref:
  compromised_actor_identity_ref:
  proposed_recovery_revision:
  incident_basis_ref:
  affected_binding_set_basis_event_sequence:
  complete_affected_binding_refs: []
  complete_affected_binding_set_fingerprint:
  binding_dispositions: []
  stewardship_assessment_ref:
  stewardship_assessment_fingerprint:
  steward_action_ref: LifecycleActionRefV0_1R8
  historical_steward_action_assessment_ref:
  recovery_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

The affected Binding set is derived from a complete ledger index at its basis
Event. Missing coverage is `INDETERMINATE`, never an empty set. Recovery action
and evidence are historical inputs; current steward session continuity is not
required after commit.

## 3. Responsibility Assignment issuance closure

### 3.1 Mutation and authority

R15 adds:

```text
mutation_kind = RESPONSIBILITY_ASSIGNMENT_REVISION
target_kind = RESPONSIBILITY_ASSIGNMENT
```

Only `JENN_ROOT_ACTION` may issue a Responsibility Assignment. R7's removal of
`PARENT_ASSIGNMENT` remains effective. Assignment cannot be self-issued and
cannot issue another Assignment. Downstream transfer uses Delegation only.

### 3.2 Complete Assignment subject

```yaml
ResponsibilityAssignmentRevisionV0_1R15:
  schema_version: agents-os.responsibility-assignment-revision.v0.1-r15
  assignment_id:
  assignment_revision:
  expected_previous_assignment_revision: positive_revision | null
  supersedes_assignment_revision: positive_revision | null
  actor_id:
  actor_identity_revision:
  responsibility_kind:
  responsibility_scope: ResponsibilityScopeV0_1R7
  responsibility_scope_fingerprint:
  may_redelegate: true | false
  max_redelegation_depth: 0..3
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  source_responsibility:
    kind: JENN_ROOT_DIRECTION
    source_ref:
    source_fingerprint:
  issued_by_actor_id:
  issued_by_actor_identity_revision:
  issued_by_principal_binding_ref:
  responsibility_basis_ref:
  responsibility_basis_fingerprint:
  issuer_currentness_event_sequence:
  authority_basis: TransitionAuthorityBasisV0_1R9
  authority_basis_fingerprint:
  status: ACTIVE
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  issuance_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Domain tag:
`agents-os.responsibility-assignment-revision.v0.1-r15`.

Create uses revision 1 and null predecessor fields. A successor is contiguous,
uses current-head CAS, preserves assignment ID, recipient Actor, root source,
responsibility kind, and issuer Jenn identity, and may only narrow scope,
shorten time, lower depth, or disable redelegation. Any other change requires a
new Assignment ID. Administrative state uses GovernedStateTransitionFact.

### 3.3 Body, intent, action, and subject order

The Assignment mutation body contains every Section 3.2 field except:

```text
mutation_body_fingerprint
mutation_intent_ref
mutation_intent_fingerprint
issuance_action_ref
mutation_replay_identity
created_at_event_sequence
canonical_fingerprint
```

Order:

```text
exact Assignment body
-> SHA-256(JCS(["agents-os.responsibility-assignment-body.v0.1-r15", body]))
-> MutationIntentV0_1R8 with mutation_kind RESPONSIBILITY_ASSIGNMENT_REVISION
-> exact authenticated Jenn F3 COMMITTED action binding that intent
-> LifecycleActionRefV0_1R8
-> replay identity
-> final Assignment subject at one Event
```

Final subject fingerprint:

```text
SHA-256(JCS([
  "agents-os.responsibility-assignment-revision.v0.1-r15",
  complete_Section_3_2_known_object_without_canonical_fingerprint
]))
```

The action Actor equals exact current Jenn; the action payload names the exact
intent fingerprint; the intent authority/body/target/CAS/head fields match;
the action is `COMMITTED`; and action, replay, Event, body, and subject are
verified in one Rust transaction. Reusing an action for different Assignment
bytes is a replay conflict.

### 3.4 Complete Assignment assessment

```yaml
ResponsibilityAssignmentAssessmentV0_1R15:
  assignment_ref:
  assignment_subject_fingerprint:
  current_assignment_head_ref:
  recipient_actor_identity_assessment_ref:
  source_direction_ref:
  source_direction_fingerprint:
  historical_issuance_validity_assessment_ref:
  current_transition_fact_refs: []
  responsibility_scope_contract_version: agents-os.responsibility-scope.v0.1-r7
  responsibility_scope_fingerprint:
  responsibility_lineage_fingerprint:
  time_authority_ref:
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Reducer:

```text
explicit REVOKE -> REVOKED
non-current head -> SUPERSEDED
SUSPEND without later valid RESUME -> SUSPENDED
issuance assurance INVALIDATED -> REVOKED
issuance assurance CHALLENGED or INDETERMINATE -> INDETERMINATE
missing/forked head, recipient, source, scope, transition, time, coverage,
  body/intent/action/replay/Event/fingerprint -> INDETERMINATE
recipient SUSPENDED -> SUSPENDED
recipient COMPROMISED, RETIRED, or EXPIRED -> REVOKED
before not_before -> NOT_YET_ACTIVE
at/after expires_at -> EXPIRED
all exact inputs valid and issuance assurance CONFIRMED -> ACTIVE
```

## 4. Derived Identity Stewardship assessment

No `IdentityStewardshipRelation` subject, revision stream, current pointer,
table, or second ledger is created. Stewardship is derived from existing facts.

```yaml
IdentityStewardshipAssessmentV0_1R15:
  target_actor_identity_ref:
  target_actor_identity_fingerprint:
  target_actor_identity_assessment_ref:
  target_actor_class:
  declared_identity_steward_ref:
  steward_actor_identity_ref: optional
  steward_actor_identity_assessment_ref: optional
  provisioning_authority_ref: optional
  provisioning_authority_fingerprint: optional
  responsibility_evidence_refs: []
  relation_kind: JENN_ROOT_STEWARD | JENN_STEWARD | NOBAO_STEWARD | RESPONSIBLE_DOMAIN_AGENT_STEWARD | PROVISIONING_STEWARD | NOT_APPLICABLE
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Total class predicate:

| Target class | Valid derived steward |
|---|---|
| `JENN_HUMAN_ROOT` | `NOT_APPLICABLE`; only Jenn governance/root paths mutate it |
| `RESIDENT_COORDINATOR` | exact current ACTIVE Jenn Actor named by immutable `identity_steward_ref` |
| `DOMAIN_AGENT` | exact current ACTIVE Jenn or Resident Coordinator named by `identity_steward_ref` |
| `TEMPORARY_WORKER` | exact current ACTIVE Jenn, Resident Coordinator, or responsible Domain Agent named by `identity_steward_ref`; Domain Agent requires current ACTIVE Assignment/Delegation whose exact scope contains the Worker's `assignment_binding_ref` |
| `SYSTEM_SERVICE` | exact accepted provisioning authority named by immutable steward ref |
| `EXECUTION_HOST` | exact accepted provisioning authority named by immutable steward ref |

All assessments and responsibility evidence use one watermark. Target Actor
revision, Actor class, and `identity_steward_ref` are exact and current.
Missing/forked/stale evidence yields `INDETERMINATE`; explicit mismatch yields
`INVALID`. `IDENTITY_STEWARD_ACTION` requires `VALID`, exact target, exact
requesting steward Actor, and exact watermark. The assessment grants no action
authority by itself and cannot override the single Prohibited Boundary.

R8 `stewardship_relation_ref/fingerprint` is replaced by
`identity_stewardship_assessment_ref/fingerprint` in Actor transition authority
bases. No independent relation currentness exists.

## 5. CompromiseImpact total mapping

### 5.1 Closed target action classes

Every `CompromiseImpactFact` target action must resolve to exactly one class:

```text
ACTOR_REVISION_CREATE_OR_UPDATE
PROFILE_REVISION_CREATE_OR_UPDATE
PRINCIPAL_REVISION_CREATE_OR_ROTATE
BINDING_ISSUANCE
BINDING_ACTIVATION
ASSIGNMENT_ISSUANCE
DELEGATION_ISSUANCE
DELEGATION_ACTIVATION
SAFETY_TRANSITION
ENABLING_TRANSITION
SYNTHETIC_MANIFEST_CREATE_OR_ACCEPT
```

`SAFETY_TRANSITION` is `SUSPEND`, `REVOKE`, `RENOUNCE`, `COMPROMISE`,
`RETIRE`, or manifest `REVOKE`. `ENABLING_TRANSITION` is `RESUME` or `RECOVER`.

Classification is ordered and exclusive:

```text
1. transition kind in SAFETY_TRANSITION -> SAFETY_TRANSITION
2. transition kind in ENABLING_TRANSITION -> ENABLING_TRANSITION
3. manifest CREATE/ACCEPT -> SYNTHETIC_MANIFEST_CREATE_OR_ACCEPT
4. Binding/Assignment/Delegation issuance or activation -> its exact class
5. Principal ROTATE_CREDENTIALS -> PRINCIPAL_REVISION_CREATE_OR_ROTATE
6. remaining Actor/Profile/Principal CREATE or UPDATE -> its revision class
7. otherwise -> reject target
```

Exactly one row must match. A CompromiseImpact action targeting another
CompromiseImpact action and any non-F2 action are rejected as targets.

### 5.2 Total mapping

| Target action class | `CHALLENGED` | `INVALIDATED` |
|---|---|---|
| Actor/Profile/Principal create or update | effective assessment `INDETERMINATE`; no new use | `INDETERMINATE`; no new use; explicit replacement/recovery required |
| Principal credential rotation | Principal `INDETERMINATE`; no new proof | Principal `INDETERMINATE`; affected credentials cannot support new proof; explicit rotation/revocation required |
| Binding issuance | Binding `INDETERMINATE` | Binding `REVOKED` prospectively |
| Binding activation | activation and effective Binding `INDETERMINATE` | Binding `REVOKED` prospectively |
| Assignment issuance | Assignment `INDETERMINATE` | Assignment `REVOKED` prospectively |
| Delegation issuance or activation | Delegation `INDETERMINATE` | Delegation `REVOKED` prospectively |
| Safety transition | keep the safer transition effective; expose assurance `INDETERMINATE` | keep the safer transition effective; never auto-restore; explicit compensation required |
| Enabling transition | target effective assessment `INDETERMINATE`; no new use | target remains non-active/`INDETERMINATE`; explicit new recovery/resume action required |
| Synthetic manifest create or accept | manifest and all derived subjects `INDETERMINATE` | manifest `REVOKED` prospectively; all derived subjects non-active |

`CLEAR_CHALLENGE` removes only the named challenge stream. It re-runs the total
reducer from all remaining streams and never reverses a safety transition.
`INVALIDATED` is terminal for its impact stream. Compensation is a new explicit
domain action; impact never deletes or rewrites historical Events.

### 5.3 Reducer integration

Every affected assessment binds:

```text
HistoricalActionValidityAssessment ref/fingerprint
HistoricalImpactInputSet ref/fingerprint
coverage watermark equal to the effective assessment watermark
```

Missing index coverage, unknown action class, conflicting stream, or mapping
failure produces `INDETERMINATE` and denies new use. Object-specific reducers
apply the table before ordinary ACTIVE success.

## 6. Complete materialization and review lineage requirements

The R15 materialization must be named:

```text
F2 Effective Contract Materialization v0.1-r15-v3
```

It must print the complete effective schema, domain tag/fingerprint rule,
authority predicate, currentness reducer, and source subject for:

```text
canonical scalars and fingerprints
Actor identity and recovery
Profile, Principal, credential and proof assessment
Binding issuance, activation and effective assessment
ResponsibilityScope and Responsibility Assignment
Delegation issuance, activation and effective assessment
Authentication assertion, assessment and command context
MutationIntent, LifecycleActionRef and replay
Identity Stewardship assessment
Governed state transitions
CompromiseImpact and historical assurance
Synthetic M0 manifest, controller, subjects and eligibility
single Prohibited Boundary interface
```

The review package must contain R1-R15, materialization v3, the prior R14 full
bundle review, the R14 materialization correction review, R15 author review,
and the new R15 full-bundle independent review when produced. Its manifest must
label acceptance subjects separately from supporting review evidence and print
the exact review lineage.

## 7. Required future fixtures

```text
same Actor assessment fields in two writers -> identical digest
unsorted or duplicate reason codes -> reject
unregistered assessment domain used as normative input -> reject
same Jenn action reused for two Assignment bodies -> replay conflict
Assignment action does not bind exact intent -> reject
Assignment issuance INVALIDATED -> REVOKED
steward relation absent but prose appears compatible -> INDETERMINATE
responsible Domain Agent scope does not contain Worker assignment -> INVALID
safety REVOKE action INVALIDATED -> remains safe; no automatic restore
unknown CompromiseImpact action class -> reject impact target
incomplete impact index coverage -> affected assessment INDETERMINATE
```

## 8. Finding disposition and non-authorization

| Finding | R15 disposition |
|---|---|
| `B01 ActorIdentityAssessment fingerprint` | Sections 2.1-2.3 |
| `B02 Assignment issuance binding` | Section 3 |
| `B03 stewardship relation authority` | Section 4 |
| `B04 CompromiseImpact total mapping` | Section 5 |
| `E01 incomplete review lineage` | Section 6 and rebuilt package |
| `M01 incomplete materialization` | required complete v3 |
| `M02 acceptance hashes external to R14` | R15 bundle manifest and future Jenn decision must bind R1-R15 hashes |

```yaml
acceptance_unit_id: F2_ACTOR_IDENTITY_AND_DELEGATION_V0_1_R15_ATOMIC_BUNDLE
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_full_bundle_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
production_authentication_authority_by_acceptance: false
F3_start_by_acceptance: false
```

R15 creates no runtime object, database, service, credential, Assignment,
stewardship ledger, provider call, permit, or effect. It does not accept F2,
start F3, authorize implementation, or activate runtime authentication.
