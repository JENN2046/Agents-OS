# AGENTS OS F2 Effective Contract Materialization v0.1-r17-v8

```yaml
document_type: derived_effective_contract_materialization
project: AGENTS OS
contract: F2 Actor Identity and Delegation v0.1
effective_version: v0.1-r17-v8
date: 2026-07-15
owner: Jenn
agent_steward: Nobao
status: derived_review_surface
source_of_authority: fixed_R1_through_R17_subjects_only
is_acceptance_subject: false
creates_new_semantics: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Authority and source map

This is a non-authoritative resolved reading surface. The fixed subjects and
their precedence control any conflict.

| Subject | SHA-256 | Effective contribution |
|---|---|---|
| R1 | `639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b` | Actor classes, base identity/responsibility/delegation boundaries |
| R2 | `8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd` | authenticated provenance and activation contracts |
| R3 | `d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db` | acyclic activation split and Binding semantic fields |
| R4 | `a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59` | canonical fingerprint envelope and activation evidence formulas |
| R5 | `cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be` | scalar encoding |
| R6 | `bed38cf83a2d15da3c11383b9b1ec264a3bf390f6d9fc0931f45d2d8c0e94932` | parsed number admission |
| R7 | `343881f2292fbb3c09b0cc572b0d9a9c8f77eef1e4b5957134de31796228187c` | lifecycle/currentness, exact scope, one lineage, scalar profile |
| R8 | `861b5ac20d170466d0ecdcc7f1bdf5aeaf50f01a7431dbea3b027b66bce1fde3` | intent/action/replay, total descendant and impact reducers, M0 graph, Actor schema |
| R9 | `438eae729291ddefebbc7f0f25c17575e54c34e6c3e6699b633b28759d295a94` | activation acyclicity, complete Binding, impact membership, authority watermark |
| R10 | `b8ec2014cd2117b4eca92bb8962f0cbd92cf5550023320d268d2a31a28d0adf8` | Binding issuance snapshot, activation boundary, creation-spec precedence, complete materialization |
| R11 | `baa7cd2962c45a5c4f31da759ddc25d2a7d8b2ad3b67b6f43c1776c8ce0d3ea6` | acyclic synthetic precommit inputs and final materialization corrections |
| R12 | `4f6baae88d419ad321a8de875703c08df4608ec8d6dc95305174fe58a617e82a` | pre-existing synthetic Actor boundary and Profile target/controller correction |
| R13 | `e1bbebbb45b01709951a2cb03fd95d2b9f93ddb687285ce432994ed5c1ad52ce` | deterministic M0 Actor eligibility assessment and exact synthetic row |
| R14 | `19f624306eaa349404ef0669fbf69b97a6f45cff5b47cdc25160035b0cd77190` | closed positive eligibility and Binding reference universe |
| R15 | `b6e705312dcbb986999326aefd3b75e6299ba31e66733103cd94fd8711a71ad2` | canonical derived records, Assignment issuance, stewardship, assurance totality |
| R16 | `b3381201ba2839387844957c8df5ffe8851ff45506b67999b1ff60d56441134a` | acyclic CREATE stewardship, assurance-bound schemas, complete v4 surface |
| R17 | `3ee7bfc99fb2888d8f9994c2e2d36a039f8da1112db39b876544636bafedf1c8` | closed assurance-role vocabulary and complete-set derivation |

R1-R17 are the acceptance subject set. This materialization is excluded. It is
a complete resolved reading surface, not a source of new authority.
V8 replaces v7 only as the current derived review surface. V5 through v7 remain
immutable historical review evidence and are not repaired in place.

V8 retains all source-exact v7 schemas and adds only the five complete reducer
definitions required by the v7 full atomic-bundle review. R1-R17 are unchanged.

## 2. Exact action and mutation order

The effective mutation kinds are:

```text
ACTOR_IDENTITY_REVISION
AUTHENTICATOR_PROFILE_REVISION
PRINCIPAL_REVISION
BINDING_REVISION
RESPONSIBILITY_ASSIGNMENT_REVISION
GOVERNED_STATE_TRANSITION
COMPROMISE_IMPACT
SYNTHETIC_M0_MANIFEST_CREATE
SYNTHETIC_M0_MANIFEST_ACTIVATION
```

The pre-action order is always:

```text
semantic body
-> mutation body fingerprint
-> MutationIntent
-> intent fingerprint
-> exact authenticated action / Jenn decision / provisioning action
-> LifecycleActionRef
-> replay identity
-> final subject or fact
-> final subject or fact fingerprint
```

For manifest activation, the pre-action body is exactly:

```yaml
SyntheticM0ManifestActivationBodyV0_1R9:
  activation_stream_id:
  activation_revision:
  expected_previous_activation_revision: positive_revision | null
  manifest_ref:
  manifest_fingerprint:
  transition: ACCEPT | REVOKE
  authority_basis_ref:
  authority_basis_fingerprint:
  expected_ledger_head_event_sequence:
  effective_at_event_sequence:
```

It excludes the later Jenn decision. After the decision binds the intent, the
final activation revision derives the decision fields from the lifecycle action
ref. This removes the R8 fixed point.

## 3. Complete lifecycle schemas

### 3.1 Profile

Source: R7 Section 5, R8 Sections 2-3, R9 Section 5.

```yaml
AuthenticatorProfileRevisionR9Effective:
  profile_id:
  profile_revision:
  expected_previous_profile_revision: positive_revision | null
  supersedes_profile_revision: positive_revision | null
  transition_kind: CREATE | UPDATE | SUSPEND | RESUME | RETIRE
  source_status: ACTIVE | SUSPENDED | null
  status: ACTIVE | SUSPENDED | RETIRED
  proof_kind: SYNTHETIC_FIXTURE | LOCAL_OS_SESSION | ASYMMETRIC_SIGNATURE | PROCESS_ATTESTATION | HOST_ATTESTATION
  supported_principal_classes: []
  supported_environments: []
  verifier_id:
  verifier_revision:
  lifecycle_controller_ref: LifecycleControllerRefV0_1 | SyntheticM0ControllerRefV0_1
  credential_status_provider_ref:
  trust_anchor_refs: []
  assertion_max_age_ms:
  clock_policy_ref:
  replay_policy_ref:
  profile_steward_ref:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8 | SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

### 3.2 Principal

Source: R7 Section 6, R8 Sections 2-3, R9 Section 5.

```yaml
PrincipalRevisionR9Effective:
  principal_id:
  principal_revision:
  expected_previous_principal_revision: positive_revision | null
  supersedes_principal_revision: positive_revision | null
  transition_kind: CREATE | ROTATE_CREDENTIALS | SUSPEND | RESUME | REVOKE | RETIRE
  source_status: ACTIVE | SUSPENDED | REVOKED | null
  principal_class: HUMAN_SESSION | AGENT_SESSION | SERVICE_PROCESS | WORKER_PROCESS | HOST_PROCESS | SYNTHETIC_TEST_PRINCIPAL
  environment: SYNTHETIC_TEST | LOCAL_DEVELOPMENT | PRODUCTION
  authenticator_profile_ref:
  credential_handle_refs: []
  status: ACTIVE | SUSPENDED | REVOKED | RETIRED
  provisioning_source_ref: LifecycleActionRefV0_1R8 | SyntheticManifestDerivedLifecycleRefV0_1
  lifecycle_controller_ref:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8 | SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

### 3.3 Binding and issuance snapshots

Source: R9 Section 3 as amended by R10 Sections 2-5.

```yaml
BindingIssuanceInputSnapshotV0_1R10:
  snapshot_id:
  actor_identity_ref:
  actor_identity_fingerprint:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  principal_ref:
  principal_fingerprint:
  principal_assessment_ref:
  principal_assessment_fingerprint:
  authenticator_profile_ref:
  authenticator_profile_fingerprint:
  authenticator_profile_assessment_ref:
  authenticator_profile_assessment_fingerprint:
  binding_scope_fingerprint:
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  assessed_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticBindingPrecommitInputV0_1R11:
  precommit_input_id:
  workspace_fixture_id:
  controller_spec_ref:
  controller_spec_fingerprint:
  existing_actor_identity_ref:
  existing_actor_identity_fingerprint:
  principal_creation_spec_ref:
  principal_creation_spec_fingerprint:
  authenticator_profile_creation_spec_ref:
  authenticator_profile_creation_spec_fingerprint:
  binding_scope_fingerprint:
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  canonical_fingerprint: R4FingerprintEnvelope
```

The non-synthetic snapshot binds exact ACTIVE Actor, Principal, and Profile
assessments at the intent ledger head. The synthetic input binds a pre-existing
Actor revision and only Profile/Principal/controller specs fixed before the
manifest body. At ACCEPT, Rust requires the complete R13/R14
`SyntheticM0ActorEligibilityAssessment = ELIGIBLE`; an ACTIVE-only check is
insufficient. No Actor spec exists or is materialized.
Manifest, activation, own Binding-spec, Event, action, intent, replay,
assessment, and proof fields remain forbidden in the precommit input.

At ACCEPT, Rust derives:

```yaml
SyntheticM0ActorEligibilityAssessmentV0_1R13:
  actor_identity_ref:
  actor_identity_fingerprint:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  root_create_revision_ref:
  root_create_revision_fingerprint:
  root_create_authority_basis_ref:
  root_create_authority_basis_fingerprint:
  root_Jenn_governance_authority_ref:
  root_Jenn_governance_authority_fingerprint:
  assessment: ELIGIBLE | INELIGIBLE | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

`ELIGIBLE` reads only the exact current Actor head/assessment, complete revision
chain, revision-1 CREATE basis, root Jenn governance authority, class, and
ACCEPT watermark. It requires ACTIVE at ACCEPT, `SYNTHETIC_TEST`
`IDENTITY_BOOTSTRAP`, and class in `RESIDENT_COORDINATOR | DOMAIN_AGENT |
TEMPORARY_WORKER | SYSTEM_SERVICE`. It performs no global Binding or credential
absence scan.

```yaml
ActorPrincipalBindingRevisionR10Effective:
  schema_version: agents-os.actor-principal-binding-revision.v0.1-r9
  binding_id:
  binding_revision:
  expected_previous_binding_revision: positive_revision | null
  supersedes_binding_revision: positive_revision | null
  actor_id:
  actor_identity_revision:
  principal_id:
  principal_revision:
  principal_class:
  authenticator_profile_ref:
  environment:
  not_before_utc_ms:
  expires_at_utc_ms: utc_milliseconds | null
  binding_scope:
  issued_by_actor_ref: optional
  issuance_basis_ref:
  activation_mode: JENN_INTERACTIVE_AUTHENTICATION | RESIDENT_ATTESTED_AGENT_SESSION | SERVICE_PROVISIONING_ATTESTATION | WORKER_ASSIGNMENT_HANDSHAKE | SYNTHETIC_M0_FIXTURE
  status: ACTIVE
  issuance_input_snapshot: BindingIssuanceInputSnapshotV0_1R10 | SyntheticBindingPrecommitInputV0_1R11
  issuance_input_snapshot_fingerprint:
  authority_basis: TransitionAuthorityBasisV0_1R9
  authority_basis_fingerprint:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  binding_issuance_source_ref: LifecycleActionRefV0_1R8 | SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

The Binding body includes the snapshot and excludes only its own body digest,
intent, source, replay, Event, and final digest provenance fields. The final
fingerprint remains the R9 known-object domain with the R10 fields inserted.
The subject is not operational until the later proof, activation, and effective
Binding assessments all pass.

### 3.4 Actor

Source: R8 Section 7 and R9 Section 5 watermark correction.

```yaml
ActorIdentityRevisionV0_1R8:
  schema_version: agents-os.actor-identity-revision.v0.1-r8
  actor_id:
  actor_identity_revision:
  expected_previous_actor_identity_revision: positive_revision | null
  supersedes_actor_identity_revision: positive_revision | null
  actor_class: JENN_HUMAN_ROOT | RESIDENT_COORDINATOR | DOMAIN_AGENT | TEMPORARY_WORKER | SYSTEM_SERVICE | EXECUTION_HOST
  canonical_name:
  identity_charter_refs: []
  identity_steward_ref:
  parent_actor_ref: optional
  transition_kind: CREATE | UPDATE | SUSPEND | RESUME | COMPROMISE | RECOVER | RETIRE
  source_status: ACTIVE | SUSPENDED | COMPROMISED | null
  status: ACTIVE | SUSPENDED | COMPROMISED | RETIRED
  validity_window: IdentityValidityWindowV0_1 | null
  assignment_binding_ref: optional
  transition_authority_basis: ActorCreateStewardAuthorityBasisV0_1R16 | ActorGeneralTransitionAuthorityBasisV0_1R16
  transition_authority_basis_fingerprint:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  recovery_evidence_ref: optional
  change_reason_code:
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Its complete transition table is:

| Transition | Source | Target | Exact authority kind |
|---|---|---|---|
| `CREATE` | none | `ACTIVE` | `JENN_GOVERNANCE_DECISION_BASIS`, `IDENTITY_STEWARD_ACTION`, or `ACCEPTED_PROVISIONING_ACTION` for service/host |
| `UPDATE` | `ACTIVE` | `ACTIVE` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION` |
| `UPDATE` | `SUSPENDED` | `SUSPENDED` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION` |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `BOUND_ACTOR_SELF_SUSPEND_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |
| `RESUME` | `SUSPENDED` | `ACTIVE` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION` |
| `COMPROMISE` | `ACTIVE` or `SUSPENDED` | `COMPROMISED` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |
| `RECOVER` | `COMPROMISED` | `ACTIVE` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION`, plus recovery evidence |
| `RETIRE` | `ACTIVE`, `SUSPENDED`, or `COMPROMISED` | `RETIRED` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |

`RETIRED` is terminal. Self action cannot resume, recover, update, or retire.

## 4. Complete authority schema and tables

### 4.1 Authority basis

Source: R8 Section 3.1 as replaced by R9 Section 5.

```yaml
JennRootGovernanceAuthorityRefV0_1R8:
  authority_ref_id:
  authority_contract_version: agents-os.jenn-root-governance-authority-ref.v0.1-r8
  authority_kind: JENN_EXPLICIT_PROJECT_DECISION_AUTHORITY
  source_decision_ref:
  source_decision_fingerprint:
  permitted_basis_uses: []
  environment: SYNTHETIC_TEST
  not_before_utc_ms:
  expires_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

TransitionAuthorityBasisV0_1R9:
  authority_basis_id:
  basis_kind: JENN_ROOT_ACTION | JENN_GOVERNANCE_DECISION_BASIS | IDENTITY_STEWARD_ACTION | PROFILE_CONTROLLER_ACTION | BOUND_ACTOR_SELF_ACTION | DIRECT_DELEGATOR_ACTION | ANCESTOR_DELEGATOR_ACTION | DELEGATE_RENUNCIATION_ACTION | ACCEPTED_INCIDENT_POLICY_ACTION | ACCEPTED_PROVISIONING_ACTION
  requested_by_actor_ref: optional
  requested_by_actor_identity_assessment_ref: optional
  requested_by_effective_binding_assessment_ref: optional
  Jenn_root_authority_ref: optional
  Jenn_root_authority_fingerprint: optional
  target_relation_ref: optional
  target_relation_fingerprint: optional
  responsibility_assessment_ref: optional
  target_profile_assessment_ref: optional
  controller_currentness_assessment_ref: optional
  lifecycle_controller_ref: optional
  incident_policy_ref: optional
  incident_policy_fingerprint: optional
  incident_controller_ref: optional
  provisioning_component_ref: optional
  provisioning_component_fingerprint: optional
  provisioning_basis_ref: optional
  provisioning_basis_fingerprint: optional
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Current-state basis watermark always equals intent expected ledger head. The
Jenn governance basis revalidates its prior source authority at that same head.
Every optional field not required by its exact basis kind is forbidden.

Exact required/forbidden matrix:

| Basis kind | Required exact inputs | Forbidden inputs |
|---|---|---|
| `JENN_ROOT_ACTION` | requested Jenn Actor ref, ACTIVE identity assessment, ACTIVE effective Jenn Binding, exact root relation | Profile/controller, responsibility, incident, provisioning |
| `JENN_GOVERNANCE_DECISION_BASIS` | exact revalidated Jenn root governance authority ref/fingerprint | requested Actor/Binding, relation/responsibility, Profile/controller, incident, provisioning |
| `IDENTITY_STEWARD_ACTION` | steward Actor ref, ACTIVE identity/Binding, exact stewardship target relation | Profile/controller, responsibility, incident, provisioning |
| `PROFILE_CONTROLLER_ACTION` | target Profile assessment: absent for CREATE, ACTIVE for UPDATE/SUSPEND, SUSPENDED for RESUME, ACTIVE or SUSPENDED for RETIRE; separate operational controller currentness; exact lifecycle controller | incident; Actor fields unless Actor controller; component fields unless component controller |
| `BOUND_ACTOR_SELF_ACTION` | exact target Actor ref, ACTIVE identity, ACTIVE effective target Binding | relation/responsibility, Profile/controller, incident, provisioning |
| `DIRECT_DELEGATOR_ACTION` | target relation, delegator Actor ACTIVE identity/Binding, current source responsibility | Profile/controller, incident, provisioning |
| `ANCESTOR_DELEGATOR_ACTION` | exact lineage relation, ancestor Actor ACTIVE identity/Binding, current source responsibility | Profile/controller, incident, provisioning |
| `DELEGATE_RENUNCIATION_ACTION` | target relation, delegate Actor ACTIVE identity/Binding | responsibility, Profile/controller, incident, provisioning |
| `ACCEPTED_INCIDENT_POLICY_ACTION` | accepted policy ref/fingerprint and matching incident controller | requested Actor/Binding, relation/responsibility, Profile/controller, provisioning |
| `ACCEPTED_PROVISIONING_ACTION` | accepted component ref/fingerprint and provisioning basis ref/fingerprint | requested Actor/Binding, relation/responsibility, Profile/controller, incident |

Fields required by one row are forbidden in all other rows unless that row
explicitly names them. Actor rows require the committed action Actor to equal
the requested Actor. All current assessments use the intent ledger watermark.

### 4.2 Profile lifecycle table

| Transition | Source | Target | Exact allowed basis |
|---|---|---|---|
| `CREATE` | none | `ACTIVE` | `JENN_ROOT_ACTION`, `JENN_GOVERNANCE_DECISION_BASIS`, `ACCEPTED_PROVISIONING_ACTION`; synthetic group exception |
| `UPDATE` | `ACTIVE` | `ACTIVE` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| `RESUME` | `SUSPENDED` | `ACTIVE` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| `RETIRE` | `ACTIVE` or `SUSPENDED` | `RETIRED` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` |

Target Profile assessment uses the displayed source status. Controller
currentness is a separate operational assessment.

### 4.3 Principal lifecycle table

| Transition | Source | Target | Exact allowed basis |
|---|---|---|---|
| `CREATE` | none | `ACTIVE` | `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_PROVISIONING_ACTION`; synthetic group exception |
| `ROTATE_CREDENTIALS` | `ACTIVE` | `ACTIVE` | `PROFILE_CONTROLLER_ACTION` |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| `RESUME` | `SUSPENDED` | `ACTIVE` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| `REVOKE` | `ACTIVE` or `SUSPENDED` | `REVOKED` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| `RETIRE` | `ACTIVE`, `SUSPENDED`, or `REVOKED` | `RETIRED` | `JENN_ROOT_ACTION`, `PROFILE_CONTROLLER_ACTION` |

### 4.4 Binding issuance table and exact predicates

| Mode | Exact allowed basis | Required current facts at intent head | Forbidden |
|---|---|---|---|
| `JENN_INTERACTIVE_AUTHENTICATION` | `JENN_ROOT_ACTION`; bootstrap only `JENN_GOVERNANCE_DECISION_BASIS` | exact ACTIVE snapshot Actor, Principal, Profile; scope/window; Jenn basis | control proof; unrelated steward/component fields |
| `RESIDENT_ATTESTED_AGENT_SESSION` | `IDENTITY_STEWARD_ACTION` | exact ACTIVE snapshot; current steward identity and effective Binding; target relation | control proof; component/incident fields |
| `SERVICE_PROVISIONING_ATTESTATION` | `ACCEPTED_PROVISIONING_ACTION` | exact ACTIVE snapshot; accepted component and provisioning basis | control proof; Actor requester fields |
| `WORKER_ASSIGNMENT_HANDSHAKE` | `DIRECT_DELEGATOR_ACTION` | exact ACTIVE snapshot; responsible Actor identity/effective Binding; current responsibility assessment | control proof; component/incident fields |
| `SYNTHETIC_M0_FIXTURE` | manifest-derived group intent only | exact ACTIVE manifest/controller; exact Profile/Principal/Binding spec membership; scope/window; Event-time `SyntheticM0ActorEligibilityAssessment = ELIGIBLE` | every assessment/proof in precommit body; control proof at issuance |

Every snapshot ref equals the corresponding Binding field. Non-synthetic
snapshot, authority, and intent watermarks are identical. Synthetic Actor
eligibility is required transaction evidence at ACCEPT and remains outside the
precommit body. Every optional authority field not listed is forbidden.

### 4.5 Governed transition table

| Target | Transition | Required source/additional predicate | Exact allowed basis |
|---|---|---|---|
| Binding | `SUSPEND` | current ACTIVE target; self route only exact represented Actor | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Binding | `RESUME` | current SUSPENDED target; all Actor/Principal/Profile/credential/activation facts validate | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| Binding | `REVOKE` | current ACTIVE or SUSPENDED target | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Assignment | `SUSPEND` | current ACTIVE target | `JENN_ROOT_ACTION` |
| Assignment | `RESUME` | current SUSPENDED target; source responsibility current | `JENN_ROOT_ACTION` |
| Assignment | `REVOKE` | current ACTIVE or SUSPENDED target | `JENN_ROOT_ACTION` |
| Delegation | `SUSPEND` | current ACTIVE target; delegator/ancestor route requires current responsibility chain | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION`, `ANCESTOR_DELEGATOR_ACTION` |
| Delegation | `RESUME` | current SUSPENDED target; full parent chain validates | same as SUSPEND |
| Delegation | `REVOKE` | current ACTIVE or SUSPENDED target | same as SUSPEND |
| Delegation | `RENOUNCE` | current delegate closes only its exact grant and descendants | `DELEGATE_RENUNCIATION_ACTION` |
| Binding activation evidence | `SUSPEND` or `REVOKE` | current evidence; target Binding lifecycle authority current; incident can only move safer | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Binding activation evidence | `RESUME` | current SUSPENDED evidence plus new current proof and target lifecycle authority | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| Delegation activation evidence | `SUSPEND` or `REVOKE` | current evidence and delegator current | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` |
| Delegation activation evidence | `RESUME` | current SUSPENDED evidence; exact acknowledgement remains valid | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` |
| Delegation activation evidence | `RENOUNCE` | delegate closes own exact activation | `DELEGATE_RENUNCIATION_ACTION` |

`REVOKE` and `RENOUNCE` are terminal. `RESUME` is allowed only after
`SUSPEND`. Every transition uses exact current-head CAS. Incident action cannot
resume. Every unlisted target/transition/basis tuple is forbidden.

## 5. Compromise impact and historical assurance

### 5.1 Complete impact schema

The one complete effective `CompromiseImpactFactV0_1R9Effective` schema is
printed exactly once in Section 19. Section 5.2 supplies its authority and
membership reducer tables.

### 5.2 `CompromiseImpactStreamReducer`

| Impact | Exact allowed basis |
|---|---|
| `CHALLENGE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| `INVALIDATE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION` |
| `CLEAR_CHALLENGE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION` |

| Current stream state | Allowed successor | Target membership |
|---|---|---|
| none | `CHALLENGE`, `INVALIDATE` | fixes exact sorted set and fingerprint |
| `CHALLENGED` | `CLEAR_CHALLENGE`, `INVALIDATE` | must be byte-identical to revision 1 |
| `INVALIDATED` | none | terminal and indexed by all members |
| `CLEARED` | none | terminal and indexed by all members |

Historical aggregate remains:

```text
any verified INVALIDATED -> INVALIDATED
else incomplete/conflicting coverage -> INDETERMINATE
else any CHALLENGED -> CHALLENGED
else -> CONFIRMED
```

## 6. Complete total reducers

### 6.1 `BindingEffectiveCurrentReducer`

```text
explicit Binding REVOKE -> REVOKED
Binding head no longer current -> SUPERSEDED
SUSPEND without later valid RESUME -> SUSPENDED
missing/forked head, transition, Actor, Principal, Profile, credential,
  activation, time, snapshot, or fingerprint -> INDETERMINATE
trusted now before not_before -> NOT_YET_ACTIVE
trusted now at/after expires_at -> EXPIRED
Actor SUSPENDED -> SUSPENDED
Actor COMPROMISED, RETIRED, or EXPIRED -> REVOKED
Actor INDETERMINATE -> INDETERMINATE
Principal SUSPENDED -> SUSPENDED
Principal REVOKED or RETIRED -> REVOKED
Principal SUPERSEDED -> SUPERSEDED
Principal INDETERMINATE -> INDETERMINATE
Profile SUSPENDED -> SUSPENDED
Profile RETIRED -> REVOKED
Profile SUPERSEDED -> SUPERSEDED
Profile INDETERMINATE -> INDETERMINATE
any credential REVOKED -> REVOKED
any credential INDETERMINATE -> INDETERMINATE
activation NOT_ACTIVATED -> NOT_YET_ACTIVE
activation INDETERMINATE -> INDETERMINATE
all exact dependencies current and valid -> ACTIVE
```

Activation proves only the later proof/evidence graph. This reducer alone owns
`binding_effective_current_projection`.

### 6.2 `ResponsibilityAssignmentEffectiveReducer`

```text
REVOKE -> REVOKED
non-current head -> SUPERSEDED
SUSPEND without later valid RESUME -> SUSPENDED
missing/conflicting head, historical action assurance, recipient identity,
  scope, transition, time, source, or fingerprint -> INDETERMINATE
recipient Actor SUSPENDED -> SUSPENDED
recipient Actor COMPROMISED, RETIRED, or EXPIRED -> REVOKED
before start -> NOT_YET_ACTIVE
at/after expiry -> EXPIRED
all exact current inputs valid -> ACTIVE
```

### 6.3 `DelegationEffectiveCurrentReducer`

Exact precedence:

```text
REVOKED > SUPERSEDED > SUSPENDED > INDETERMINATE > EXPIRED > NOT_YET_ACTIVE > ACTIVE
```

```text
own REVOKE or RENOUNCE -> REVOKED
any root/ancestor REVOKED, RENOUNCED, or assurance INVALIDATED -> REVOKED
own head or any required exact ancestor SUPERSEDED -> SUPERSEDED
own or any root/ancestor SUSPENDED -> SUSPENDED
any missing/conflicting/challenged/indeterminate dependency -> INDETERMINATE
own or any root/ancestor EXPIRED -> EXPIRED
own or any root/ancestor NOT_YET_ACTIVE -> NOT_YET_ACTIVE
all exact root-to-target inputs ACTIVE -> ACTIVE
```

### 6.4 `HistoricalActionAssuranceReducer`

```text
any verified current impact stream INVALIDATED -> INVALIDATED
else incomplete, forked, mismatched, or conflicting coverage -> INDETERMINATE
else any current impact stream CHALLENGED -> CHALLENGED
else -> CONFIRMED
```

Routine session end, Binding expiry/replacement, credential rotation, or issuer
identity update does not retroactively alter a committed action. `CLEARED`
remains indexed audit evidence but contributes no challenge.

## 7. Synthetic M0 atomic graph

Exact acyclic order:

```text
pre-existing Actor revision + controller + Profile + Principal creation specs fixed
-> synthetic Binding precommit input fixed
-> Binding creation spec/body fingerprint fixed
-> manifest body and fingerprint fixed
-> manifest creation intent and Jenn decision fixed
-> activation body/intent and Jenn decision fixed
-> one atomic materialization Event
-> final derived issuance refs and final subject fingerprints
```

Profile and Principal specs retain their R8 own-domain digests. Only Binding
specs use the `BINDING_REVISION` body digest. The precommit input has no
manifest, activation, own-spec, or Event fields. The final derived issuance ref
proves same-manifest membership only for Profile, Principal, and Binding. The
Binding spec names the exact pre-existing Actor and its R13 eligibility is
derived at ACCEPT. The transaction's closed reference set additionally requires
same-manifest synthetic Profile and `SYNTHETIC_TEST` Principal specs, every
credential handle in `deterministic_credential_handle_refs`, and no external
Binding, credential, Jenn identity, or host identity ref in the Binding spec.
Any omission, mismatch, ineligible/indeterminate Actor, or partial
materialization rejects.

## 8. Canonical scalars, fingerprints, and derived records

Source: R4 Sections 2-3, R5-R7 scalar amendments, R15 Section 2.

All JSON numbers use the F2 binary64/JCS safe domains. Revisions, Event
sequences, timestamps, durations, depths, and counters reject negative zero,
fractions, non-finite values, unsafe integers, or parser-rounding admission.
Text is Unicode 15.1 NFC. Unknown keys, undefined, normalized-key collisions,
and unordered arrays without a declared order reject.

```yaml
R4FingerprintEnvelope:
  algorithm: SHA-256
  canonicalization_contract_version: agents-os.f2-r4-jcs.v0.1
  digest_lowercase_hex: exactly_64_lowercase_hex_characters

CanonicalDigestScalarV0_1:
  JSON_type: string
  derivation_algorithm: SHA-256
  canonicalization_contract_version: agents-os.f2-digest-scalar.v0.1
  owning_input_serialization: RFC_8785_JCS_under_the_exact_domain_tagged_formula
  digest_source: raw_32_octet_SHA256_result
  persisted_encoding: lowercase_hex
  encoded_length: 64_ASCII_characters
  accepted_pattern: "^[0-9a-f]{64}$"
  JCS_inserted_value: the_exact_persisted_JSON_string

F2CanonicalScalarProfileV0_1:
  contract_version: agents-os.f2-canonical-scalars.v0.1
  safe_uint:
    predicate: Number.isSafeInteger(value) && value >= 0 && !Object.is(value, -0)
    range: 0..9007199254740991
  positive_revision:
    predicate: safe_uint && value >= 1
    range: 1..9007199254740991
  nullable_previous_revision:
    create_value: null
    successor_value: positive_revision
  event_sequence:
    predicate: safe_uint
    range: 0..9007199254740991
  utc_milliseconds:
    predicate: safe_uint
    range: 0..9007199254740991
  duration_milliseconds:
    predicate: safe_uint && value >= 1
    range: 1..9007199254740991
  delegation_policy_maximum_edges:
    exact_value_in_v0_1: 3
  delegation_remaining_depth:
    range: 0..2
  assignment_max_redelegation_depth:
    range: 0..3

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

BindingScopeContextV0_1:
  context_kind: SESSION | SURFACE | HOST_PROCESS | SERVICE_INSTANCE | SYNTHETIC_FIXTURE
  context_id: NFC_nonempty_UTF8_JSON_string
  context_revision: JCS_SAFE_UINT

BindingScopeV0_1:
  schema_version: agents-os.binding-scope.v0.1
  scope_kind: EXACT_REPRESENTATION_CONTEXT_SET
  contexts: BindingScopeContextV0_1[]

IdentityValidityWindowV0_1:
  schema_version: agents-os.identity-validity-window.v0.1
  not_before_utc_ms:
  expires_at_utc_ms:

LifecycleControllerRefV0_1:
  controller_kind: SYSTEM_SERVICE_ACTOR | ACCEPTED_PROVISIONING_COMPONENT | SYNTHETIC_FIXTURE_CONTROLLER
  controller_ref:
  controller_revision:
  controller_fingerprint:
  provisioning_basis_ref:

DelegationPolicyRevision:
  policy_id: agents-os-delegation-policy
  policy_revision: 1
  maximum_edges_per_chain: 3
  parallel_chain_union: forbidden
  implicit_delegation: forbidden
  relationship_based_expansion: forbidden
  model_self_delegation: forbidden
  default_redelegation: false
  unknown_scope_behavior: STOP_AND_CLARIFY

ActionAssuranceRoleV0_1R17:
  - ACTOR_REVISION_CREATE
  - ACTOR_REVISION_UPDATE
  - ACTOR_TRANSITION_SUSPEND
  - ACTOR_TRANSITION_RESUME
  - ACTOR_TRANSITION_COMPROMISE
  - ACTOR_TRANSITION_RECOVER
  - ACTOR_TRANSITION_RETIRE
  - PROFILE_REVISION_CREATE
  - PROFILE_REVISION_UPDATE
  - PROFILE_TRANSITION_SUSPEND
  - PROFILE_TRANSITION_RESUME
  - PROFILE_TRANSITION_RETIRE
  - PRINCIPAL_REVISION_CREATE
  - PRINCIPAL_REVISION_ROTATE_CREDENTIALS
  - PRINCIPAL_TRANSITION_SUSPEND
  - PRINCIPAL_TRANSITION_RESUME
  - PRINCIPAL_TRANSITION_REVOKE
  - PRINCIPAL_TRANSITION_RETIRE
  - BINDING_ISSUANCE
  - BINDING_TRANSITION_SUSPEND
  - BINDING_TRANSITION_RESUME
  - BINDING_TRANSITION_REVOKE
  - BINDING_ACTIVATION
  - BINDING_ACTIVATION_TRANSITION_SUSPEND
  - BINDING_ACTIVATION_TRANSITION_RESUME
  - BINDING_ACTIVATION_TRANSITION_REVOKE
  - ASSIGNMENT_ISSUANCE
  - ASSIGNMENT_TRANSITION_SUSPEND
  - ASSIGNMENT_TRANSITION_RESUME
  - ASSIGNMENT_TRANSITION_REVOKE
  - DELEGATION_ISSUANCE
  - DELEGATION_TRANSITION_SUSPEND
  - DELEGATION_TRANSITION_RESUME
  - DELEGATION_TRANSITION_REVOKE
  - DELEGATION_TRANSITION_RENOUNCE
  - DELEGATION_ACTIVATION
  - DELEGATION_ACTIVATION_TRANSITION_SUSPEND
  - DELEGATION_ACTIVATION_TRANSITION_RESUME
  - DELEGATION_ACTIVATION_TRANSITION_REVOKE
  - DELEGATION_ACTIVATION_TRANSITION_RENOUNCE
  - SYNTHETIC_MANIFEST_CREATE
  - SYNTHETIC_MANIFEST_ACCEPT
  - SYNTHETIC_MANIFEST_REVOKE
```

`R4FingerprintEnvelope` is an envelope value, not a separately fingerprinted
record. `CanonicalDigestScalarV0_1` is a scalar value. The scalar profile,
Binding scope context, lifecycle window, controller ref, Delegation policy,
and assurance role retain exactly the domains or `NOT_STANDALONE`
classification stated in Section 21; v8 does not invent domains for them.

Every registered assessment/evidence record uses:

```text
SHA-256(JCS([registered_domain_tag,
             complete_effective_known_object_without_canonical_fingerprint]))
```

and stores `R4FingerprintEnvelope`. `reason_codes` is sorted unique NFC UTF-8.
Refs are exact stable refs with verified target fingerprints. The closed domain
registry is:

| Record | Domain |
|---|---|
| Actor identity assessment | `agents-os.actor-identity-assessment.v0.1-r16` |
| Profile assessment | `agents-os.authenticator-profile-assessment.v0.1-r16` |
| Credential status assessment ref | `agents-os.credential-handle-status-assessment-ref.v0.1` |
| Principal assessment | `agents-os.principal-assessment.v0.1-r16` |
| Principal control proof assessment ref | `agents-os.principal-control-proof-assessment-ref.v0.1-r15` |
| Binding activation evidence | `agents-os.binding-activation-evidence.v0.1-r15` |
| Binding activation assessment | `agents-os.binding-activation-assessment.v0.1-r16` |
| Effective Binding assessment | `agents-os.actor-principal-binding-assessment.v0.1-r16` |
| Assignment assessment | `agents-os.responsibility-assignment-assessment.v0.1-r16` |
| Delegation activation evidence | `agents-os.delegation-activation-evidence.v0.1-r15` |
| Delegation activation assessment | `agents-os.delegation-activation-assessment.v0.1-r16` |
| Delegation assessment | `agents-os.delegation-assessment.v0.1-r16` |
| Authentication assessment | `agents-os.authentication-assessment.v0.1-r15` |
| Historical impact input set | `agents-os.historical-impact-input-set.v0.1` |
| Historical action validity | `agents-os.historical-action-validity-assessment.v0.1-r16` |
| Synthetic manifest assessment | `agents-os.synthetic-m0-manifest-assessment.v0.1-r16` |
| Synthetic Actor eligibility | `agents-os.synthetic-m0-actor-eligibility-assessment.v0.1-r13` |
| Identity stewardship assessment | `agents-os.identity-stewardship-assessment.v0.1-r15` |
| Identity recovery evidence | `agents-os.identity-recovery-evidence.v0.1-r15` |
| Actor CREATE target spec | `agents-os.actor-create-stewardship-target-spec.v0.1-r16` |
| Actor CREATE stewardship assessment | `agents-os.actor-create-stewardship-assessment.v0.1-r16` |
| Actor CREATE authority basis | `agents-os.actor-create-steward-authority-basis.v0.1-r16` |
| Action assurance binding | `agents-os.action-assurance-binding.v0.1-r17` |

Unregistered derived-record fingerprints cannot be normative F2 inputs.

## 9. Actor identity, stewardship, and recovery

Source: R8 Section 7, R13-R16.

The complete Actor revision schema remains Section 3.4 of this materialization.
Its sole current assessment is:

```yaml
ActorIdentityAssessmentV0_1R16:
  actor_identity_ref:
  actor_identity_fingerprint:
  current_head_ref:
  current_head_fingerprint:
  assignment_assessment_ref: optional
  time_authority_ref:
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: ACTIVE | SUSPENDED | COMPROMISED | RETIRED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

### 9.1 `ActorIdentityEffectiveReducer`

Reducer precedence:

```text
non-current assessed revision -> SUPERSEDED
current RETIRED -> RETIRED
current COMPROMISED -> COMPROMISED
current SUSPENDED -> SUSPENDED
missing/forked head, invalid transition/action/assurance, time uncertainty,
  missing Worker assignment, or fingerprint conflict -> INDETERMINATE
Temporary Worker assignment non-active -> EXPIRED or INDETERMINATE by cause
trusted now outside validity window -> EXPIRED
all class/lifecycle/time dependencies current -> ACTIVE
```

CREATE-time stewardship is derived from an acyclic precommit target spec:

```yaml
ActorCreateStewardshipTargetSpecV0_1R16:
  spec_id:
  intended_actor_id:
  intended_actor_class: RESIDENT_COORDINATOR | DOMAIN_AGENT | TEMPORARY_WORKER
  intended_canonical_name:
  intended_identity_charter_refs: []
  intended_identity_steward_ref:
  intended_parent_actor_ref: optional
  intended_validity_window: IdentityValidityWindowV0_1 | null
  intended_assignment_binding_ref: optional
  expected_actor_head: null
  actor_head_absence_basis_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

ActorCreateStewardshipAssessmentV0_1R16:
  target_spec_ref:
  target_spec_fingerprint:
  intended_actor_id:
  intended_actor_class:
  declared_identity_steward_ref:
  steward_actor_identity_ref:
  steward_actor_identity_fingerprint:
  steward_actor_identity_assessment_ref:
  steward_actor_identity_assessment_fingerprint:
  steward_effective_binding_assessment_ref:
  steward_effective_binding_assessment_fingerprint:
  responsibility_evidence_refs: []
  responsibility_evidence_fingerprints: []
  actor_head_absence_basis_event_sequence:
  relation_kind: JENN_STEWARD | NOBAO_STEWARD | RESPONSIBLE_DOMAIN_AGENT_STEWARD
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

ActorCreateStewardAuthorityBasisV0_1R16:
  authority_basis_id:
  basis_kind: IDENTITY_STEWARD_ACTION
  requested_by_actor_ref:
  requested_by_actor_identity_assessment_ref:
  requested_by_effective_binding_assessment_ref:
  create_target_spec_ref:
  create_target_spec_fingerprint:
  create_stewardship_assessment_ref:
  create_stewardship_assessment_fingerprint:
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

ActorGeneralTransitionAuthorityBasisV0_1R16:
  authority_basis_id:
  basis_kind: JENN_ROOT_ACTION | JENN_GOVERNANCE_DECISION_BASIS | IDENTITY_STEWARD_ACTION | BOUND_ACTOR_SELF_SUSPEND_ACTION | ACCEPTED_INCIDENT_POLICY_ACTION | ACCEPTED_PROVISIONING_ACTION
  requested_by_actor_ref: optional
  requested_by_actor_identity_assessment_ref: optional
  requested_by_effective_binding_assessment_ref: optional
  Jenn_root_authority_ref: optional
  Jenn_root_authority_fingerprint: optional
  identity_stewardship_assessment_ref: optional
  identity_stewardship_assessment_fingerprint: optional
  incident_policy_ref: optional
  incident_policy_fingerprint: optional
  incident_controller_ref: optional
  provisioning_component_ref: optional
  provisioning_component_fingerprint: optional
  provisioning_basis_ref: optional
  provisioning_basis_fingerprint: optional
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

The target spec is content-addressed input, not a ledger stream. Its absence
watermark, assessment watermark, and basis watermark are equal. Stable Actor
identity fields in the later CREATE body are byte-equal to the spec. The exact
acyclic order is target spec, assessment, basis, mutation body, intent, action,
LifecycleActionRef, and final Actor Event.

Post-create stewardship remains:

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

| Target | Exact valid steward derivation |
|---|---|
| Jenn | NOT_APPLICABLE; Jenn root/governance action only |
| Resident Coordinator | ACTIVE Jenn named by immutable steward ref |
| Domain Agent | ACTIVE Jenn or Resident Coordinator named by steward ref |
| Temporary Worker | ACTIVE Jenn, Coordinator, or responsible Domain Agent; Domain Agent needs current containing responsibility evidence |
| System Service / Execution Host | exact accepted provisioning authority |

Post-create Actor transition authority uses this assessment ref/fingerprint
instead of an independent stewardship relation ref. CREATE uses only the R16
CREATE assessment and basis above.

```yaml
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

Affected Binding refs and dispositions sort by Binding stable ref. Complete
ledger-index coverage is mandatory; missing coverage is indeterminate.

## 10. Responsibility scope and Assignment

Source: R7 Sections 10-12 and R15 Section 3.

```yaml
ResponsibilityResourceRefV0_1:
  resource_kind: GOAL | TASK | RUN | DOMAIN | ARTIFACT_METADATA
  resource_id:
  resource_revision: positive_revision | null
  resource_fingerprint: optional

ResponsibilityScopeV0_1R7:
  scope_contract_version: agents-os.responsibility-scope.v0.1-r7
  workspace_id:
  scope_mode: EXACT_SET
  resource_refs: ResponsibilityResourceRefV0_1[]
  canonical_fingerprint: R4FingerprintEnvelope
```

Refs sort by kind, NFC ID, and null-before-positive revision. Scope is nonempty;
wildcard, subtree, regex, ambient access, and natural-language sets reject.

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

Only `JENN_ROOT_ACTION` issues it. Body excludes body digest, intent, action,
replay, Event, and final fingerprint. The deterministic order is body -> body
fingerprint -> MutationIntent -> F3 COMMITTED Jenn action -> lifecycle ref ->
replay -> final subject/Event. Final fingerprint uses the full known object
under `agents-os.responsibility-assignment-revision.v0.1-r15`.

The complete effective Assignment assessment is
`ResponsibilityAssignmentAssessmentV0_1R16` in Section 18. Its assurance array
replaces the superseded standalone historical-issuance ref.

The sole complete Assignment reducer is Section 6.2. Assignment recursion is
forbidden.

## 11. Delegation issuance and currentness

Source: R1 Sections 11-12, R3-R4, R7 Sections 11-12, R8 Section 4.

```yaml
DelegationGrantRevisionV0_1R15Effective:
  delegation_id:
  delegation_revision:
  expected_previous_delegation_revision: positive_revision | null
  supersedes_delegation_revision: positive_revision | null
  delegator_actor_id:
  delegator_identity_revision:
  delegate_actor_id:
  delegate_identity_revision:
  parent_delegation_ref: optional
  source_responsibility_ref:
  responsibility_kind:
  responsibility_scope: ResponsibilityScopeV0_1R7
  responsibility_scope_fingerprint:
  may_redelegate: true | false
  remaining_depth: 0..2
  not_before_utc_ms:
  expires_at_utc_ms:
  activation_mode: EXPLICIT_ACK | WORKER_ASSIGNMENT_HANDSHAKE
  issued_by_actor_id:
  issued_by_actor_identity_revision:
  issued_by_principal_binding_ref:
  issuer_currentness_event_sequence:
  root_direction_ref: optional
  root_direction_fingerprint: optional
  source_assignment_ref: optional
  source_assignment_fingerprint: optional
  delegation_issuance_intent_fingerprint:
  issuance_action_ref: AuthenticatedActorActionRefR4Effective
  reason:
  status: ACTIVE
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

The R3/R4 intent and final subject formulas remain exact. The subject contains
no activation evidence backward ref. Chain maximum is three edges, Actor IDs
are unique, scope/time narrow, depth decrements exactly, and parallel-chain
union is forbidden.

The complete effective Delegation assessment is
`DelegationAssessmentV0_1R16` in Section 18. Its exact fingerprinted ancestry,
activation, transition, and assurance inputs replace the R15 aliases.

Root-to-target ancestry is complete and ordered. The sole complete Delegation
reducer is Section 6.3.

## 12. Binding and Delegation activation evidence

Source: R2 Sections 5-6, R3 Sections 3-4, R4, R7 Section 7, R15 Section 2.

```yaml
AuthenticatedActorActionRefR4Effective:
  interface_version: agents-os.authenticated-actor-action-ref.v0.1
  action_ref_id:
  F3_contract_version:
  command_id:
  command_envelope_ref:
  command_envelope_fingerprint:
  actor_id:
  actor_identity_revision:
  principal_id:
  principal_revision:
  principal_binding_ref:
  authentication_assertion_ref:
  authentication_assessment_ref:
  responsibility_source_ref:
  delegation_chain_fingerprint: optional
  prohibited_behavior_list_revision:
  prohibited_boundary_evidence_ref:
  F3_intake_event_sequence:
  F3_intake_state_ref:
  canonical_action_ref_fingerprint: R4FingerprintEnvelope

DelegationActivationAcknowledgementRefR4Effective:
  interface_version: agents-os.delegation-activation-acknowledgement-ref.v0.1
  acknowledgement_ref_id:
  F3_contract_version:
  intake_state: COMMITTED
  intake_purpose: DELEGATION_ACTIVATION_ACK
  intake_event_sequence:
  command_envelope_ref:
  command_envelope_fingerprint:
  command_type_id: DELEGATION_ACTIVATION_ACK
  delegation_ref:
  delegation_subject_fingerprint:
  delegate_actor_id:
  delegate_actor_identity_revision:
  acknowledging_principal_id:
  acknowledging_principal_revision:
  acknowledging_principal_binding_ref:
  authentication_assertion_ref:
  authentication_assessment_ref:
  responsibility_source_mode: NONE_ACTIVATION_PURPOSE_ONLY
  prohibited_behavior_list_revision:
  prohibited_boundary_evidence_ref:
  replay_identity: CanonicalDigestScalarV0_1
```

The action ref fingerprint domain is
`agents-os.authenticated-actor-action-ref.v0.1`. The acknowledgement fingerprint
domain is `agents-os.delegation-activation-acknowledgement-ref.v0.1`; its
fingerprint is a verified companion value used by activation evidence and is
not an extra field invented in the external interface.

```yaml
PrincipalControlProofAssessmentRefV0_1R15:
  interface_version: agents-os.principal-control-proof-assessment-ref.v0.1
  assessment_ref_id:
  principal_id:
  principal_revision:
  authenticator_profile_ref:
  verifier_id:
  verifier_revision:
  challenge_fingerprint:
  assessment: VERIFIED
  assessed_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

BindingActivationEvidenceR15Effective:
  evidence_id:
  evidence_revision:
  expected_previous_evidence_revision: positive_revision | null
  supersedes_evidence_revision: positive_revision | null
  target_binding_ref:
  target_binding_fingerprint:
  actor_id:
  actor_identity_revision:
  principal_id:
  principal_revision:
  principal_class:
  environment:
  authenticator_profile_ref:
  verifier_revision:
  target_proof_assessment_ref: PrincipalControlProofAssessmentRefV0_1R15
  activation_mode:
  stewardship_source:
    kind: JENN_ROOT_BOOTSTRAP_DECISION | AUTHENTICATED_STEWARD_ACTION
    source_ref:
  steward_actor_id: optional
  steward_actor_identity_revision: optional
  steward_principal_binding_ref: optional
  steward_action_ref: AuthenticatedActorActionRefR4Effective | null
  not_before_utc_ms:
  expires_at_utc_ms:
  replay_identity: CanonicalDigestScalarV0_1
  status: ACTIVE | REVOKED | SUPERSEDED
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Evidence exists after the immutable Binding subject. Bootstrap omits steward
Actor, Binding, and action fields; all other modes require all four exact
steward fields. Raw proof is forbidden.

```yaml
DelegationActivationEvidenceR15Effective:
  evidence_id:
  evidence_revision:
  expected_previous_evidence_revision: positive_revision | null
  supersedes_evidence_revision: positive_revision | null
  delegation_ref:
  delegation_subject_fingerprint:
  activation_mode: EXPLICIT_ACK | WORKER_ASSIGNMENT_HANDSHAKE
  delegate_actor_id:
  delegate_actor_identity_revision:
  acknowledging_principal_binding_ref:
  acknowledgement_ref: DelegationActivationAcknowledgementRefR4Effective
  not_before_utc_ms:
  expires_at_utc_ms:
  replay_identity: CanonicalDigestScalarV0_1
  status: ACTIVE | REVOKED | SUPERSEDED
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

```

Evidence IDs, subject fingerprints, acknowledgements, action refs, replay
identities, CAS, time windows, and Event sequences are all fingerprinted.
The complete effective Binding and Delegation activation assessments are the
R16 schemas in Section 18.

## 13. Exact authentication and command interfaces

Source: R1 Sections 14-15, R2 Section 8, R15 Section 2.

```yaml
CommandTypeDefinition:
  command_type_id:
  registry_revision:
  owning_domain:
  required_resource_kinds: []
  domain_gate_ref:

CanonicalCommand:
  command_contract_version:
  command_id:
  workspace_id:
  command_type_id:
  target_resource_refs: []
  payload:
  issued_at_utc_ms:
  expires_at_utc_ms:
  nonce:
  expected_domain_aggregate_versions: []

AuthenticationAssertionValue:
  assertion_id:
  authenticator_profile_ref:
  principal_id:
  principal_binding_ref:
  actor_id:
  actor_identity_revision:
  command_id:
  command_fingerprint:
  nonce:
  issued_at_utc_ms:
  expires_at_utc_ms:
  verifier_id:
  verifier_revision:
  proof_ref:

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
```

```yaml
AuthenticatedCommandContext:
  context_contract_version: authenticated-command-context.v0.1
  command_id:
  command_fingerprint:
  workspace_id:
  command_type_id:
  target_resource_refs: []
  actor_id:
  actor_identity_revision:
  principal_id:
  principal_binding_ref:
  authentication_assertion_ref:
  authentication_assessment_ref:
  responsibility_source:
    kind: JENN_ROOT_DIRECTION | DIRECT_ASSIGNMENT | DELEGATION_CHAIN
    source_ref:
  delegation_chain_refs: []
  responsibility_assignment_revision: optional
  command_registry_revision:
  delegation_policy_revision:
  responsibility_scope_fingerprint:
  prohibited_behavior_list_revision:
  issued_at_utc_ms:
  expires_at_utc_ms:
  nonce:
  inbox_received_event_sequence:
```

`CommandTypeDefinition`, `CanonicalCommand`, `AuthenticationAssertionValue`,
and `AuthenticatedCommandContext` are exact R1 interfaces. F2 does not assign
them a standalone F2 fingerprint domain or add a canonical fingerprint field.
R15 alone owns the canonical Authentication assessment shown above. Only
`AUTHENTICATED` enters responsibility attribution and the single prohibited
line. Proof bytes, credentials, secrets, cookies, private memory, and provider
raw output are never stored.

## 14. Mutation intent, action, replay, and transitions

Source: R8 Sections 2-3, R9, R15 Section 3.

```yaml
MutationIntentV0_1R17Effective:
  intent_id:
  intent_revision: 1
  mutation_kind: ACTOR_IDENTITY_REVISION | AUTHENTICATOR_PROFILE_REVISION | PRINCIPAL_REVISION | BINDING_REVISION | RESPONSIBILITY_ASSIGNMENT_REVISION | GOVERNED_STATE_TRANSITION | COMPROMISE_IMPACT | SYNTHETIC_M0_MANIFEST_CREATE | SYNTHETIC_M0_MANIFEST_ACTIVATION
  target_kind: ACTOR_IDENTITY | AUTHENTICATOR_PROFILE | PRINCIPAL | BINDING | RESPONSIBILITY_ASSIGNMENT | ASSIGNMENT | DELEGATION | BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE | COMPROMISE_IMPACT_STREAM | SYNTHETIC_M0_MANIFEST | SYNTHETIC_M0_MANIFEST_ACTIVATION
  target_stable_id:
  target_current_ref: optional
  target_current_fingerprint: optional
  expected_target_head:
    target_revision: positive_revision | null
    target_fingerprint: CanonicalDigestScalarV0_1 | null
    last_transition_event_sequence: event_sequence | null
  authority_basis_ref:
  authority_basis_fingerprint:
  mutation_body_fingerprint:
  expected_ledger_head_event_sequence:
  effective_at_event_sequence:
  issued_at_utc_ms:
  expires_at_utc_ms:
  nonce:
  canonical_fingerprint: R4FingerprintEnvelope

LifecycleActionRefV0_1R8:
  interface_version: agents-os.lifecycle-action-ref.v0.1-r8
  action_kind: AUTHENTICATED_ACTOR_ACTION | JENN_GOVERNANCE_DECISION | ACCEPTED_PROVISIONING_ACTION
  action_ref:
  action_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  mutation_replay_identity: CanonicalDigestScalarV0_1
  committed_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

The MutationIntent fingerprint domain is exactly
`agents-os.mutation-intent.v0.1`; R9 and R15 extend only the closed mutation and
target enums. The LifecycleActionRef fingerprint domain is exactly
`agents-os.lifecycle-action-ref.v0.1-r8`. One action binds one
intent/body/head/target. Duplicate exact replay is idempotent; differing bytes
are conflict.

The one complete effective governed transition schema is printed in Section 19
with the R9 authority basis. Assignment transitions allow Jenn only. Safety
transitions never auto-reverse.

## 15. Historical action assurance and CompromiseImpact

Source: R7 Section 9, R8 Section 5, R9 Section 4, R15 Section 5,
and R16 Section 3.

The complete CompromiseImpact, input-set, historical assessment, and assurance
Allowed target action classes and total effects are:

| Class | CHALLENGED | INVALIDATED |
|---|---|---|
| Actor/Profile/Principal create/update | INDETERMINATE; deny new use | INDETERMINATE; deny new use; explicit repair |
| Credential rotation | Principal INDETERMINATE | Principal INDETERMINATE; explicit rotate/revoke |
| Binding issuance/activation | Binding INDETERMINATE | Binding REVOKED prospectively |
| Assignment issuance | Assignment INDETERMINATE | Assignment REVOKED prospectively |
| Delegation issuance/activation | Delegation INDETERMINATE | Delegation REVOKED prospectively |
| Safety transition | keep safe effect; assurance INDETERMINATE | keep safe effect; explicit compensation only |
| Enabling transition | target INDETERMINATE/non-active | remain non-active; new explicit action required |
| Synthetic manifest create/accept | manifest and derived subjects INDETERMINATE | manifest REVOKED; derived subjects non-active |

Unknown/non-F2/recursive impact targets reject. Every directly affected reducer
binds `ActionAssuranceBindingV0_1R17`; its historical assessment binds the exact
impact input set and equal coverage watermark.
Classification first matches safety transitions (`SUSPEND`, `REVOKE`,
`RENOUNCE`, `COMPROMISE`, `RETIRE`, manifest `REVOKE`), then enabling
transitions (`RESUME`, `RECOVER`), then manifest, issuance/activation,
credential rotation, and remaining lifecycle create/update classes. Exactly one
class must match.

## 16. Synthetic M0 graph

Source: R8 Section 6 and R9-R14.

The complete controller, manifest, activation, and Actor eligibility schemas
are printed in Section 20. Derived lifecycle ref and Binding precommit schemas
are printed in Sections 3 and 7. The exact order is:

```text
pre-existing eligible Actor + controller/Profile/Principal specs
-> Binding precommit input
-> Binding spec/body digest
-> manifest body/digest
-> manifest creation intent/Jenn decision
-> activation body/intent/Jenn decision
-> one ACCEPT Event verifies Actor ELIGIBLE
-> atomic Profile/Principal/Binding materialization
-> derived lifecycle refs and final fingerprints
```

Only synthetic test principals, deterministic credential handles, and exact
same-manifest specs are permitted. No production credential, Jenn credential,
active host identity, raw secret, or partial materialization is allowed.

## 17. Single Prohibited Boundary interface

Source: root AGENTS.md, accepted single-boundary direction, R1 Sections 3-4.

F2 defines identity, responsibility, provenance, and derived currentness. It
does not define permissions. Every authenticated action still passes the one
canonical Prohibited Behavior List interface. Relationship, responsibility,
delegation, stewardship, authentication, and capability cannot waive or expand
that boundary. Unknown boundary revision or evaluation result stops the action.

## 18. Complete assurance-bound assessment catalogue

Source: R7 Sections 5-7, R15 Section 3, and R16 Section 3. These are the
complete effective schemas; no earlier assessment alias remains effective.

```yaml
AuthenticatorProfileAssessmentV0_1R16:
  profile_ref:
  profile_subject_fingerprint:
  current_profile_head_ref:
  lifecycle_controller_ref:
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: ACTIVE | SUSPENDED | RETIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

CredentialHandleStatusAssessmentRefV0_1:
  assessment_ref:
  principal_ref:
  authenticator_profile_ref:
  credential_handle_ref:
  assessment: ACTIVE | REVOKED | INDETERMINATE
  controller_ref:
  based_on_event_sequence:
  assessed_at_utc_ms:
  assessment_fingerprint:

PrincipalAssessmentV0_1R16:
  principal_ref:
  principal_subject_fingerprint:
  current_principal_head_ref:
  authenticator_profile_assessment_ref:
  authenticator_profile_assessment_fingerprint:
  credential_status_assessment_refs: []
  credential_status_assessment_fingerprints: []
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: ACTIVE | SUSPENDED | REVOKED | RETIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

BindingActivationAssessmentV0_1R16:
  binding_ref:
  binding_subject_fingerprint:
  activation_evidence_ref:
  activation_evidence_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: ACTIVATED | NOT_ACTIVATED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

ActorPrincipalBindingAssessmentV0_1R16:
  binding_ref:
  binding_subject_fingerprint:
  current_binding_head_ref:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  principal_assessment_ref:
  principal_assessment_fingerprint:
  authenticator_profile_assessment_ref:
  authenticator_profile_assessment_fingerprint:
  credential_status_assessment_refs: []
  credential_status_assessment_fingerprints: []
  binding_activation_assessment_ref:
  binding_activation_assessment_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  time_authority_ref:
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

ResponsibilityAssignmentAssessmentV0_1R16:
  assignment_ref:
  assignment_subject_fingerprint:
  current_assignment_head_ref:
  recipient_actor_identity_assessment_ref:
  recipient_actor_identity_assessment_fingerprint:
  source_direction_ref:
  source_direction_fingerprint:
  responsibility_scope_contract_version: agents-os.responsibility-scope.v0.1-r7
  responsibility_scope_fingerprint:
  responsibility_lineage_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  time_authority_ref:
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

DelegationActivationAssessmentV0_1R16:
  delegation_ref:
  delegation_subject_fingerprint:
  activation_acknowledgement_ref:
  activation_evidence_ref:
  activation_evidence_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: ACTIVATED | NOT_ACTIVATED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

DelegationAssessmentV0_1R16:
  delegation_ref:
  delegation_subject_fingerprint:
  current_delegation_head_ref:
  source_assignment_assessment_ref: optional
  source_assignment_assessment_fingerprint: optional
  ancestor_delegation_assessment_refs: []
  ancestor_delegation_assessment_fingerprints: []
  delegator_actor_identity_assessment_ref:
  delegator_actor_identity_assessment_fingerprint:
  delegate_actor_identity_assessment_ref:
  delegate_actor_identity_assessment_fingerprint:
  activation_assessment_ref:
  activation_assessment_fingerprint:
  current_transition_fact_refs: []
  current_transition_fact_fingerprints: []
  responsibility_scope_fingerprint:
  responsibility_lineage_fingerprint:
  time_authority_ref:
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | RENOUNCED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

```

Parallel ref/fingerprint arrays are same-length, index-aligned, sorted by the
owning stable-ref order, and duplicate-free. Direct assurance role sets are:

| Assessment | Complete direct action roles |
|---|---|
| Actor | current Actor revision and all effective Actor lifecycle actions through watermark |
| Profile | current Profile revision and all effective Profile lifecycle actions |
| Principal | current Principal revision and all effective Principal lifecycle actions |
| Binding activation | activation and activation-evidence transition actions |
| Effective Binding | issuance and Binding transition actions |
| Assignment | issuance and Assignment transition actions |
| Delegation activation | activation and activation-evidence transition actions |
| Delegation | issuance and Delegation transition actions |
| Synthetic manifest | create, accept, and effective revoke action when present |

Every role set is derived from a complete ledger index through the assessment
watermark. Missing coverage, missing role, extra role, fingerprint mismatch, or
non-confirmed enabling assurance fails closed. Safety transition effects remain
safe and never auto-restore.

### 18.1 Common R16 reducer prelude

The five reducers below apply the R16 Section 3.4 order before their
object-specific rules:

```text
1. Require one complete closed action-role set through based_on_event_sequence.
2. Require every direct and transitive assurance input to have the same
   watermark and an exact matching fingerprint.
3. Preserve an already effective safer transition; challenged or invalidated
   assurance never restores a less safe state.
4. Apply the object-specific current-head, CAS, dependency, and terminal rules.
5. Return ACTIVE or ACTIVATED only when every enabling assurance is CONFIRMED.
```

An unknown role, missing or extra role, missing coverage, stale watermark,
fork, CAS gap, invalid transition provenance, ref/fingerprint mismatch, or
conflicting dependency returns `INDETERMINATE`, except that a proven effective
safer state remains effective as required by R16. Reason codes describe the
selected branch but do not change precedence.

### 18.2 `AuthenticatorProfileEffectiveReducer`

Source: R7 Sections 5.2-5.3 and R16 Sections 3.2-3.4.

```text
effective RETIRE transition -> RETIRED
effective SUSPEND without a later valid RESUME -> SUSPENDED
assessed Profile revision is not the unique current head -> SUPERSEDED
missing/forked current head or CAS, invalid transition matrix or authority,
  incomplete action-role coverage, non-confirmed enabling assurance,
  unavailable or mismatched verifier, clock policy, credential-status provider,
  lifecycle controller, provisioning basis, or fingerprint -> INDETERMINATE
current head status RETIRED -> RETIRED
current head status SUSPENDED -> SUSPENDED
unique current ACTIVE head, valid current controller/provider/verifier/clock,
  exact fingerprints, and all enabling assurance CONFIRMED -> ACTIVE
```

Only `ACTIVE` may provision a Principal, verify a new assertion, or support an
effective Binding. `RETIRED` is terminal; an incident action cannot resume.

### 18.3 `PrincipalEffectiveReducer`

Source: R7 Sections 6.1-6.4 and R16 Sections 3.2-3.4.

```text
effective RETIRE transition -> RETIRED
effective REVOKE transition -> REVOKED
effective SUSPEND without a later valid RESUME -> SUSPENDED
assessed Principal revision is not the unique current head -> SUPERSEDED
missing/forked current head or CAS, invalid transition matrix or provenance,
  incomplete action-role coverage, non-confirmed enabling assurance,
  Profile ref/fingerprint mismatch, credential array mismatch, or Principal
  fingerprint mismatch -> INDETERMINATE
current head status RETIRED -> RETIRED
current head status REVOKED -> REVOKED
current head status SUSPENDED -> SUSPENDED
exact referenced Profile assessment is not ACTIVE, or any exact credential
  handle assessment is missing, conflicting, REVOKED, or INDETERMINATE
  -> INDETERMINATE
unique current ACTIVE head, exact ACTIVE Profile, every exact credential handle
  ACTIVE, valid transition provenance and fingerprints, and all enabling
  assurance CONFIRMED -> ACTIVE
```

`REVOKED` permits only `RETIRE`; `RETIRED` is terminal. A Principal never
creates or attests itself.

### 18.4 `BindingActivationEffectiveReducer`

Source: R2 Section 5, R3 Sections 3-5, R4 Section 5, R7 Section 7.2, and R16
Sections 3.2-3.4.

```text
complete evidence stream proves no active evidence, or an effective REVOKE or
  SUSPEND is present without a later valid RESUME -> NOT_ACTIVATED
missing/forked evidence head or CAS, stale or replayed evidence, invalid
  transition fact, incomplete action-role coverage, non-confirmed enabling
  assurance, target Binding mismatch, proof/stewardship mismatch, time-window
  mismatch, or any ref/fingerprint mismatch -> INDETERMINATE
exact current evidence is REVOKED or validly SUSPENDED -> NOT_ACTIVATED
exact current ACTIVE evidence matches the immutable Binding subject, exact
  proof and stewardship inputs, replay identity, time, transition facts,
  fingerprints, watermark, and all enabling assurance is CONFIRMED -> ACTIVATED
```

This reducer owns only `binding_activation_projection`. It never decides
whether the Actor, Principal, Profile, credentials, administrative Binding
state, or Binding time window permits a new Command.

### 18.5 `DelegationActivationEffectiveReducer`

Source: R2 Section 6, R3 Sections 2 and 5, R4 Section 6, R7 Section 7.4, and R16
Sections 3.2-3.4.

```text
complete evidence stream proves no active evidence, or an effective REVOKE,
  RENOUNCE, or SUSPEND is present without a later valid RESUME -> NOT_ACTIVATED
missing/forked evidence head or CAS, stale or replayed evidence, invalid
  transition fact, incomplete action-role coverage, non-confirmed enabling
  assurance, delegation-subject mismatch, acknowledgement mismatch, time-window
  mismatch, or any ref/fingerprint mismatch -> INDETERMINATE
exact current evidence is REVOKED, validly RENOUNCED, or validly SUSPENDED
  -> NOT_ACTIVATED
exact current ACTIVE evidence matches the immutable Delegation subject, exact
  R3 acknowledgement, delegate and Binding inputs, replay identity, time,
  transition facts, fingerprints, watermark, and every enabling assurance is
  CONFIRMED -> ACTIVATED
```

This reducer owns only `delegation_activation_projection`. It does not decide
whether the responsibility source, lineage, scope, actors, or time window make
the Delegation effective.

## 19. Complete governed transition and assurance schemas

Source: R8 Sections 3 and 5, R9 Section 4, R15 Section 5, R16 Section 3.

```yaml
GovernedStateTransitionFactV0_1R9Effective:
  transition_fact_id:
  target_kind: BINDING | ASSIGNMENT | DELEGATION | BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE
  target_ref:
  target_fingerprint:
  transition: SUSPEND | RESUME | REVOKE | RENOUNCE
  authority_basis: TransitionAuthorityBasisV0_1R9
  authority_basis_fingerprint:
  expected_target_head:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  effective_at_event_sequence:
  reason_codes: []
  canonical_fingerprint: R4FingerprintEnvelope

CompromiseImpactFactV0_1R9Effective:
  impact_fact_id:
  impact_stream_id:
  impact_revision:
  expected_previous_impact_revision: positive_revision | null
  compromised_actor_or_principal_ref:
  compromised_subject_action_set_ref:
  compromised_subject_action_set_fingerprint:
  selection_basis_event_sequence:
  incident_basis_ref:
  complete_target_action_refs: []
  complete_target_set_fingerprint:
  impact: CHALLENGE | INVALIDATE | CLEAR_CHALLENGE
  authority_basis: TransitionAuthorityBasisV0_1R9
  authority_basis_fingerprint:
  expected_previous_impact_event_sequence: event_sequence | null
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  effective_at_event_sequence:
  reason_codes: []
  canonical_fingerprint: R4FingerprintEnvelope

HistoricalImpactInputSetV0_1:
  action_ref:
  action_fingerprint:
  coverage_through_event_sequence:
  current_impact_heads:
    - impact_stream_id:
      impact_revision:
      impact_fact_ref:
      impact_fact_fingerprint:
      effective_at_event_sequence:
      stream_state: CHALLENGED | INVALIDATED | CLEARED
  impact_input_set_fingerprint: CanonicalDigestScalarV0_1

HistoricalActionValidityAssessmentV0_1R16:
  action_ref:
  action_fingerprint:
  actor_ref_at_commit: optional
  principal_ref_at_commit: optional
  binding_ref_at_commit: optional
  authentication_assessment_ref_at_commit: optional
  authentication_assessment_fingerprint_at_commit: optional
  committed_event_sequence:
  validity_at_commit: VALID | INVALID | INDETERMINATE
  impact_input_set_ref:
  impact_input_set_fingerprint:
  impact_coverage_through_event_sequence:
  current_assurance: CONFIRMED | CHALLENGED | INVALIDATED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

ActionAssuranceBindingV0_1R17:
  action_role: ActionAssuranceRoleV0_1R17
  action_ref:
  action_fingerprint:
  historical_action_validity_assessment_ref:
  historical_action_validity_assessment_fingerprint:
```

Impact streams sort by stream ID then revision. Binding arrays sort by action
role enum ordinal, action ref, then action fingerprint. Historical assessment
and input-set coverage equal the containing assessment watermark. Action
classification uses the exclusive R15 order; unknown, recursive, or non-F2
targets reject.

### 19.1 Closed assurance-role enum

```text
ACTOR_REVISION_CREATE
ACTOR_REVISION_UPDATE
ACTOR_TRANSITION_SUSPEND
ACTOR_TRANSITION_RESUME
ACTOR_TRANSITION_COMPROMISE
ACTOR_TRANSITION_RECOVER
ACTOR_TRANSITION_RETIRE
PROFILE_REVISION_CREATE
PROFILE_REVISION_UPDATE
PROFILE_TRANSITION_SUSPEND
PROFILE_TRANSITION_RESUME
PROFILE_TRANSITION_RETIRE
PRINCIPAL_REVISION_CREATE
PRINCIPAL_REVISION_ROTATE_CREDENTIALS
PRINCIPAL_TRANSITION_SUSPEND
PRINCIPAL_TRANSITION_RESUME
PRINCIPAL_TRANSITION_REVOKE
PRINCIPAL_TRANSITION_RETIRE
BINDING_ISSUANCE
BINDING_TRANSITION_SUSPEND
BINDING_TRANSITION_RESUME
BINDING_TRANSITION_REVOKE
BINDING_ACTIVATION
BINDING_ACTIVATION_TRANSITION_SUSPEND
BINDING_ACTIVATION_TRANSITION_RESUME
BINDING_ACTIVATION_TRANSITION_REVOKE
ASSIGNMENT_ISSUANCE
ASSIGNMENT_TRANSITION_SUSPEND
ASSIGNMENT_TRANSITION_RESUME
ASSIGNMENT_TRANSITION_REVOKE
DELEGATION_ISSUANCE
DELEGATION_TRANSITION_SUSPEND
DELEGATION_TRANSITION_RESUME
DELEGATION_TRANSITION_REVOKE
DELEGATION_TRANSITION_RENOUNCE
DELEGATION_ACTIVATION
DELEGATION_ACTIVATION_TRANSITION_SUSPEND
DELEGATION_ACTIVATION_TRANSITION_RESUME
DELEGATION_ACTIVATION_TRANSITION_REVOKE
DELEGATION_ACTIVATION_TRANSITION_RENOUNCE
SYNTHETIC_MANIFEST_CREATE
SYNTHETIC_MANIFEST_ACCEPT
SYNTHETIC_MANIFEST_REVOKE
```

Only these exact ASCII strings are admitted. Printed order is canonical enum
order; aliases, case folding, localization, numeric codes, and extensions
reject.

### 19.2 Total action-to-role mapping and `ActionAssuranceCompleteSetReducer`

| Object/target | Exact kind | Role |
|---|---|---|
| Actor revision | CREATE | ACTOR_REVISION_CREATE |
| Actor revision | UPDATE | ACTOR_REVISION_UPDATE |
| Actor revision | SUSPEND | ACTOR_TRANSITION_SUSPEND |
| Actor revision | RESUME | ACTOR_TRANSITION_RESUME |
| Actor revision | COMPROMISE | ACTOR_TRANSITION_COMPROMISE |
| Actor revision | RECOVER | ACTOR_TRANSITION_RECOVER |
| Actor revision | RETIRE | ACTOR_TRANSITION_RETIRE |
| Profile revision | CREATE | PROFILE_REVISION_CREATE |
| Profile revision | UPDATE | PROFILE_REVISION_UPDATE |
| Profile revision | SUSPEND | PROFILE_TRANSITION_SUSPEND |
| Profile revision | RESUME | PROFILE_TRANSITION_RESUME |
| Profile revision | RETIRE | PROFILE_TRANSITION_RETIRE |
| Principal revision | CREATE | PRINCIPAL_REVISION_CREATE |
| Principal revision | ROTATE_CREDENTIALS | PRINCIPAL_REVISION_ROTATE_CREDENTIALS |
| Principal revision | SUSPEND | PRINCIPAL_TRANSITION_SUSPEND |
| Principal revision | RESUME | PRINCIPAL_TRANSITION_RESUME |
| Principal revision | REVOKE | PRINCIPAL_TRANSITION_REVOKE |
| Principal revision | RETIRE | PRINCIPAL_TRANSITION_RETIRE |
| Binding subject | issuance | BINDING_ISSUANCE |
| Binding transition fact | SUSPEND | BINDING_TRANSITION_SUSPEND |
| Binding transition fact | RESUME | BINDING_TRANSITION_RESUME |
| Binding transition fact | REVOKE | BINDING_TRANSITION_REVOKE |
| Binding activation evidence | creation | BINDING_ACTIVATION |
| Binding-activation transition fact | SUSPEND | BINDING_ACTIVATION_TRANSITION_SUSPEND |
| Binding-activation transition fact | RESUME | BINDING_ACTIVATION_TRANSITION_RESUME |
| Binding-activation transition fact | REVOKE | BINDING_ACTIVATION_TRANSITION_REVOKE |
| Assignment subject | issuance | ASSIGNMENT_ISSUANCE |
| Assignment transition fact | SUSPEND | ASSIGNMENT_TRANSITION_SUSPEND |
| Assignment transition fact | RESUME | ASSIGNMENT_TRANSITION_RESUME |
| Assignment transition fact | REVOKE | ASSIGNMENT_TRANSITION_REVOKE |
| Delegation subject | issuance | DELEGATION_ISSUANCE |
| Delegation transition fact | SUSPEND | DELEGATION_TRANSITION_SUSPEND |
| Delegation transition fact | RESUME | DELEGATION_TRANSITION_RESUME |
| Delegation transition fact | REVOKE | DELEGATION_TRANSITION_REVOKE |
| Delegation transition fact | RENOUNCE | DELEGATION_TRANSITION_RENOUNCE |
| Delegation activation evidence | creation | DELEGATION_ACTIVATION |
| Delegation-activation transition fact | SUSPEND | DELEGATION_ACTIVATION_TRANSITION_SUSPEND |
| Delegation-activation transition fact | RESUME | DELEGATION_ACTIVATION_TRANSITION_RESUME |
| Delegation-activation transition fact | REVOKE | DELEGATION_ACTIVATION_TRANSITION_REVOKE |
| Delegation-activation transition fact | RENOUNCE | DELEGATION_ACTIVATION_TRANSITION_RENOUNCE |
| Synthetic manifest | creation | SYNTHETIC_MANIFEST_CREATE |
| Manifest activation revision | ACCEPT | SYNTHETIC_MANIFEST_ACCEPT |
| Manifest activation revision | REVOKE | SYNTHETIC_MANIFEST_REVOKE |

Exactly one tuple matches each admitted direct assurance action. Zero or
multiple matches reject. Complete bindings come from the contiguous
root-to-current Actor/Profile/Principal revision chain; issuance plus all
accepted target transition facts for Binding/Assignment/Delegation; evidence
creation plus evidence transition facts for activation; and manifest creation
plus contiguous activation revisions for synthetic M0. Repeated roles are
allowed only for different exact action refs. Caller labels and ordering are
ignored and recomputed from the closed indexes.

## 20. Complete synthetic M0 schemas

Source: R8 Section 6 and R9-R14.

```yaml
SyntheticM0ControllerSpecV0_1:
  controller_contract_version: agents-os.synthetic-m0-controller.v0.1
  controller_id:
  controller_revision: 1
  controller_kind: MANIFEST_OWNED_DETERMINISTIC_VERIFIER
  verifier_id:
  verifier_revision: 1
  supported_mutation_kinds:
    - AUTHENTICATOR_PROFILE_REVISION
    - PRINCIPAL_REVISION
    - GOVERNED_STATE_TRANSITION
  state_model: IMMUTABLE_ACCEPTED_MANIFEST
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticM0PrincipalProvisioningManifestV0_1R8Effective:
  manifest_id:
  manifest_revision: 1
  workspace_fixture_id:
  controller_spec: SyntheticM0ControllerSpecV0_1
  controller_spec_fingerprint:
  synthetic_profile_creation_specs: []
  synthetic_principal_creation_specs: []
  permitted_binding_creation_specs: []
  deterministic_credential_handle_refs: []
  manifest_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  manifest_creation_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticM0ControllerRefV0_1:
  manifest_ref:
  manifest_fingerprint:
  manifest_assessment_ref:
  manifest_assessment_fingerprint:
  controller_id:
  controller_spec_fingerprint:
  profile_spec_id:
  profile_spec_fingerprint:
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticManifestDerivedLifecycleRefV0_1:
  manifest_ref:
  manifest_fingerprint:
  manifest_assessment_ref:
  manifest_assessment_fingerprint:
  controller_id:
  controller_spec_fingerprint:
  spec_kind: PROFILE | PRINCIPAL | BINDING
  spec_id:
  spec_fingerprint:
  derivation_replay_identity: CanonicalDigestScalarV0_1
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticM0ManifestActivationRevisionV0_1R9:
  activation_stream_id:
  activation_revision:
  expected_previous_activation_revision: positive_revision | null
  transition: ACCEPT | REVOKE
  manifest_ref:
  manifest_fingerprint:
  Jenn_decision_ref:
  Jenn_decision_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8
  mutation_replay_identity: CanonicalDigestScalarV0_1
  effective_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticM0ManifestAssessmentV0_1R16:
  manifest_ref:
  manifest_fingerprint:
  current_activation_revision_ref:
  current_activation_revision_fingerprint:
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: ACTIVE | REVOKED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope

```

### 20.1 `SyntheticM0ManifestAssessmentReducer`

Source: R8 Section 6.3 and R16 Sections 3.2-3.4.

```text
missing activation coverage, missing current head, fork, non-contiguous
  revision, CAS gap, manifest ref/fingerprint mismatch, Jenn decision mismatch,
  lifecycle-action mismatch, mutation-intent mismatch, replay mismatch,
  incomplete action-role coverage, stale watermark, non-confirmed enabling
  assurance, or any canonical fingerprint conflict -> INDETERMINATE
unique contiguous current activation head is ACCEPT, all derived Jenn-decision
  equalities and fingerprints match, and all required MANIFEST_CREATE and
  MANIFEST_ACCEPT assurance is CONFIRMED -> ACTIVE
unique later contiguous current activation head is REVOKE, its safety effect
  remains effective, and all required transition inputs match -> REVOKED
```

Revision 1 must be `ACCEPT`; only a later contiguous Jenn revision may
`REVOKE`; revocation is terminal. The manifest owns the controller, so no
second controller current-state stream exists. Only `ACTIVE` supports derived
synthetic subjects or controller currentness.

All subject specs and ref/fingerprint arrays use their R11-R14 closed positive
reference sets. Synthetic acceptance is atomic, M0-only, and cannot contain a
real secret, active Jenn credential, production Principal, or active host
identity.

## 21. Exact domain and source index

This index is generated from the source-first v8 inventory. It covers every
effective top-level schema, external interface, embedded value, canonical
profile, and reducer printed by v8. `NOT_STANDALONE` means R1-R17 defines no
independent F2 record fingerprint for that surface; v8 does not invent one.

| Exact surface | Kind | Exact domain or classification | Authoritative source | Printed section |
|---|---|---|---|---|
| `SyntheticM0ManifestActivationBodyV0_1R9` | mutation body | `NOT_STANDALONE` | R9 2.1 | 2 |
| `AuthenticatorProfileRevisionR9Effective` | subject/policy revision | `agents-os.authenticator-profile-revision.v0.1-r8` | R7 5-6 + R8 2 + R9 5 | 3 |
| `PrincipalRevisionR9Effective` | subject/policy revision | `agents-os.principal-revision.v0.1-r8` | R7 5-6 + R8 2 + R9 5 | 3 |
| `BindingIssuanceInputSnapshotV0_1R10` | schema | `agents-os.binding-issuance-input-snapshot.v0.1-r10` | R10 3 | 3 |
| `SyntheticBindingPrecommitInputV0_1R11` | schema | `agents-os.synthetic-binding-precommit-input.v0.1-r11` | R11 2 + R12 2 | 3 |
| `SyntheticM0ActorEligibilityAssessmentV0_1R13` | assessment | `agents-os.synthetic-m0-actor-eligibility-assessment.v0.1-r13` | R13 2 + R14 2 | 3 |
| `ActorPrincipalBindingRevisionR10Effective` | subject/policy revision | `agents-os.actor-principal-binding-revision.v0.1-r9` | R9 3 + R10 4 + R11-R14 | 3 |
| `ActorIdentityRevisionV0_1R8` | subject/policy revision | `agents-os.actor-identity-revision.v0.1-r8` | R8 7 + R16 2.3 | 3 |
| `JennRootGovernanceAuthorityRefV0_1R8` | reference/interface | `agents-os.jenn-root-governance-authority-ref.v0.1-r8` | R8 3.1 | 4 |
| `TransitionAuthorityBasisV0_1R9` | schema | `agents-os.transition-authority-basis.v0.1-r9` | R8 3.1 + R9 5 | 4 |
| `R4FingerprintEnvelope` | value type | `NOT_STANDALONE` | R4 2-3 | 8 |
| `CanonicalDigestScalarV0_1` | value type | `NOT_STANDALONE` | R5 2-4 | 8 |
| `F2CanonicalScalarProfileV0_1` | canonical profile | `NOT_STANDALONE` | R7 | 8 |
| `F2CanonicalDerivedRecordProfileV0_1R15` | canonical profile | `NOT_STANDALONE` | R15 2.1 | 8 |
| `BindingScopeContextV0_1` | scope/value | `NOT_STANDALONE` | R5 2-4 | 8 |
| `BindingScopeV0_1` | scope/value | `agents-os.binding-scope.v0.1` | R4 2-3 | 8 |
| `IdentityValidityWindowV0_1` | schema | `agents-os.identity-validity-window.v0.1` | R7 | 8 |
| `LifecycleControllerRefV0_1` | reference/interface | `agents-os.lifecycle-controller-ref.v0.1` | R7 | 8 |
| `DelegationPolicyRevision` | subject/policy revision | `NOT_STANDALONE` | R1 10-15 | 8 |
| `ActionAssuranceRoleV0_1R17` | value type | `NOT_STANDALONE` | R17 2 | 8 |
| `ActorIdentityAssessmentV0_1R16` | assessment | `agents-os.actor-identity-assessment.v0.1-r16` | R16 3.2 + R17 2 | 9 |
| `ActorCreateStewardshipTargetSpecV0_1R16` | embedded spec | `agents-os.actor-create-stewardship-target-spec.v0.1-r16` | R16 2 | 9 |
| `ActorCreateStewardshipAssessmentV0_1R16` | assessment | `agents-os.actor-create-stewardship-assessment.v0.1-r16` | R16 2 | 9 |
| `ActorCreateStewardAuthorityBasisV0_1R16` | schema | `agents-os.actor-create-steward-authority-basis.v0.1-r16` | R16 2 | 9 |
| `ActorGeneralTransitionAuthorityBasisV0_1R16` | schema | `agents-os.actor-general-transition-authority-basis.v0.1-r16` | R16 2 | 9 |
| `IdentityStewardshipAssessmentV0_1R15` | assessment | `agents-os.identity-stewardship-assessment.v0.1-r15` | R15 4 | 9 |
| `IdentityRecoveryEvidenceV0_1R15` | evidence | `agents-os.identity-recovery-evidence.v0.1-r15` | R15 2.4 | 9 |
| `ResponsibilityResourceRefV0_1` | reference/interface | `NOT_STANDALONE` | R7 | 10 |
| `ResponsibilityScopeV0_1R7` | scope/value | `agents-os.responsibility-scope.v0.1-r7` | R7 | 10 |
| `ResponsibilityAssignmentRevisionV0_1R15` | subject/policy revision | `agents-os.responsibility-assignment-revision.v0.1-r15` | R15 3 | 10 |
| `DelegationGrantRevisionV0_1R15Effective` | subject/policy revision | `agents-os.delegation-grant-subject.v0.1-r4` | R1 11 + R3/R4/R7 overlays | 11 |
| `AuthenticatedActorActionRefR4Effective` | reference/interface | `agents-os.authenticated-actor-action-ref.v0.1` | R2 2 + R4 4.2 | 12 |
| `DelegationActivationAcknowledgementRefR4Effective` | reference/interface | `agents-os.delegation-activation-acknowledgement-ref.v0.1` | R3 2 + R4 4.3 | 12 |
| `PrincipalControlProofAssessmentRefV0_1R15` | assessment | `agents-os.principal-control-proof-assessment-ref.v0.1-r15` | R2 5 + R4 4.1 + R15 2.2 | 12 |
| `BindingActivationEvidenceR15Effective` | evidence | `agents-os.binding-activation-evidence.v0.1-r15` | R2 5 + R3/R4 + R15 2.2 | 12 |
| `DelegationActivationEvidenceR15Effective` | evidence | `agents-os.delegation-activation-evidence.v0.1-r15` | R2 6 + R3/R4 + R15 2.2 | 12 |
| `CommandTypeDefinition` | external registry interface | `NOT_STANDALONE` | R1 10-15 | 13 |
| `CanonicalCommand` | external command/auth interface | `NOT_STANDALONE` | R1 10-15 | 13 |
| `AuthenticationAssertionValue` | external command/auth interface | `NOT_STANDALONE` | R1 10-15 | 13 |
| `AuthenticationAssessmentV0_1R15` | assessment | `agents-os.authentication-assessment.v0.1-r15` | R1 14.3 + R15 2.4 | 13 |
| `AuthenticatedCommandContext` | external command/auth interface | `NOT_STANDALONE` | R1 10-15 | 13 |
| `MutationIntentV0_1R17Effective` | intent | `agents-os.mutation-intent.v0.1` | R8 2 + R9/R15 enum overlays | 14 |
| `LifecycleActionRefV0_1R8` | reference/interface | `agents-os.lifecycle-action-ref.v0.1-r8` | R8 2 + R9/R15 enum overlays | 14 |
| `AuthenticatorProfileAssessmentV0_1R16` | assessment | `agents-os.authenticator-profile-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `CredentialHandleStatusAssessmentRefV0_1` | assessment ref | `agents-os.credential-handle-status-assessment-ref.v0.1` | R7 | 18 |
| `PrincipalAssessmentV0_1R16` | assessment | `agents-os.principal-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `BindingActivationAssessmentV0_1R16` | assessment | `agents-os.binding-activation-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `ActorPrincipalBindingAssessmentV0_1R16` | assessment | `agents-os.actor-principal-binding-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `ResponsibilityAssignmentAssessmentV0_1R16` | assessment | `agents-os.responsibility-assignment-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `DelegationActivationAssessmentV0_1R16` | assessment | `agents-os.delegation-activation-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `DelegationAssessmentV0_1R16` | assessment | `agents-os.delegation-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `GovernedStateTransitionFactV0_1R9Effective` | fact | `agents-os.governed-state-transition-fact.v0.1-r8` | R8 3.3 + R9 5 | 19 |
| `CompromiseImpactFactV0_1R9Effective` | fact | `agents-os.compromise-impact-fact.v0.1-r8` | R8 5.1 + R9 4 | 19 |
| `HistoricalImpactInputSetV0_1` | input set | `agents-os.historical-impact-input-set.v0.1` | R8 5.2 | 19 |
| `HistoricalActionValidityAssessmentV0_1R16` | assessment | `agents-os.historical-action-validity-assessment.v0.1-r16` | R16 3.1 | 19 |
| `ActionAssuranceBindingV0_1R17` | embedded assurance | `agents-os.action-assurance-binding.v0.1-r17` | R17 2 | 19 |
| `SyntheticM0ControllerSpecV0_1` | embedded spec | `agents-os.synthetic-m0-controller-spec.v0.1` | R8 6 + R9-R14 overlays | 20 |
| `SyntheticM0PrincipalProvisioningManifestV0_1R8Effective` | schema | `agents-os.synthetic-m0-principal-provisioning-manifest.v0.1-r8` | R8 6 + R9-R14 overlays | 20 |
| `SyntheticM0ControllerRefV0_1` | reference/interface | `agents-os.synthetic-m0-controller-ref.v0.1` | R8 6 + R9-R14 overlays | 20 |
| `SyntheticManifestDerivedLifecycleRefV0_1` | reference/interface | `agents-os.synthetic-manifest-derived-lifecycle-ref.v0.1` | R8 6 + R9-R14 overlays | 20 |
| `SyntheticM0ManifestActivationRevisionV0_1R9` | subject/policy revision | `agents-os.synthetic-m0-manifest-activation-revision.v0.1` | R8 6.3 + R9 2 | 20 |
| `SyntheticM0ManifestAssessmentV0_1R16` | assessment | `agents-os.synthetic-m0-manifest-assessment.v0.1-r16` | R8 6.3 + R16 3.2 | 20 |

The reducer index is exhaustive for every explicitly named reducer printed in v8:

| Exact reducer | Kind | Fingerprint domain | Authoritative source | Printed section |
|---|---|---|---|---|
| `BindingEffectiveCurrentReducer` | reducer | `NOT_STANDALONE` | R7 7.3 + R16 3 | 6.1 |
| `ResponsibilityAssignmentEffectiveReducer` | reducer | `NOT_STANDALONE` | R15 3.4 + R16 3 | 6.2 |
| `DelegationEffectiveCurrentReducer` | reducer | `NOT_STANDALONE` | R7 11-12 + R8 4 + R16 3 | 6.3 |
| `HistoricalActionAssuranceReducer` | reducer | `NOT_STANDALONE` | R8 5 + R15 5 + R16 3 | 6.4 |
| `ActorIdentityEffectiveReducer` | reducer | `NOT_STANDALONE` | R7 4 + R15 2.3 + R16 3 | 9 |
| `CompromiseImpactStreamReducer` | reducer | `NOT_STANDALONE` | R8 5 + R9 4 + R15 5 | 5/15 |
| `AuthenticatorProfileEffectiveReducer` | reducer | `NOT_STANDALONE` | R7 5.2-5.3 + R16 3 | 18.2 |
| `PrincipalEffectiveReducer` | reducer | `NOT_STANDALONE` | R7 6.1-6.4 + R16 3 | 18.3 |
| `BindingActivationEffectiveReducer` | reducer | `NOT_STANDALONE` | R2-R4 activation + R7 7.2 + R16 3 | 18.4 |
| `DelegationActivationEffectiveReducer` | reducer | `NOT_STANDALONE` | R2-R4 activation + R7 7.4 + R16 3 | 18.5 |
| `SyntheticM0ManifestAssessmentReducer` | reducer | `NOT_STANDALONE` | R8 6.3 + R16 3 | 20 |
| `ActionAssuranceCompleteSetReducer` | reducer | `NOT_STANDALONE` | R16 3 + R17 2 | 19.1-19.2 |

The surface row set equals every top-level schema block name in this file. The
reducer row set equals every explicitly named reducer definition. Completeness
also requires source-field equality: a row-set match alone is insufficient.
Canonical F2 fingerprints use the exact printed domain, R15 profile, R4
envelope, R7 scalar profile, RFC 8785 JCS, Unicode 15.1 NFC, unknown-field
rejection, and the complete source-defined object excluding only its own
canonical fingerprint. External interfaces remain owned by their named source
contract and receive no inferred F2 fingerprint.

## 22. Non-authorization

This complete materialization creates no authority. F2 remains unaccepted
pending a fresh full atomic-bundle independent review and Jenn's later decision.
F3, implementation, runtime, production authentication, database, service,
provider, credential, commit, and push actions remain unauthorized.
