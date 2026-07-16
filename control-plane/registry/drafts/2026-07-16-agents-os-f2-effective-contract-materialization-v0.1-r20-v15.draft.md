# AGENTS OS F2 Effective Contract Materialization v0.1-r20-v15

```yaml
document_type: derived_effective_contract_materialization
project: AGENTS OS
contract: F2 Actor Identity and Delegation v0.1
effective_version: v0.1-r20-v15
date: 2026-07-16
owner: Jenn
agent_steward: Nobao
status: derived_review_surface
source_of_authority: fixed_R1_through_R20_subjects_only
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
| R18 | `1baf807dcff8fee1d3e0f64a121bbc88c338c53488b1bcf58b2f7af959a0e222` | Temporary Worker responsibility separation and exact activation-assurance projection |
| R19 | `d26c2a42264789fcd6ae7587ebbe65e15f8c1773188922428f61a723368965b3` | Actor pre-start state, canonical activation RESUME revalidation, non-circular Worker stewardship, and closed Delegation reason |
| R20 | `cad4f293dee172d793db19c9cec0e6148116d44e6b659b3f2ed528a409f5772b` | final freeze closure: deterministic M0 specs/digests, typed stewardship targets, and total nullable expiry |

R1-R20 are the acceptance subject set. This materialization is excluded. It is
a complete resolved reading surface, not a source of new authority.
V15 replaces v14 only as the current derived review surface. V5 through v14 remain
immutable historical review evidence and are not repaired in place.

V15 preserves every v14 correction, applies the fixed R20 subject overlay, and
faithfully repairs the materialization-only omissions found in the R19/v14
review. It prints only authoritative identity, currentness, CAS, canonical
digest, and attenuation semantics required for the F2 freeze surface. Source
provenance and presentation corrections remain non-authoritative. V15 adds no
authority or implementation permission beyond fixed R1-R20.

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

Each authoritative F2 revision/fact class has one accepting ledger writer and
one current-head CAS path. Derived assessments and projections are rebuildable
read models, never second authoritative writers. The concrete Rust module,
database, index, and transaction implementation remain implementation-profile
choices; they may not change the single-writer property or accepted bytes.

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

Across Profile revisions, `profile_id`, `proof_kind`,
`lifecycle_controller_ref`, and profile-steward lineage are immutable.
Changing any of them requires a new `profile_id`. Every Profile reference is
exact to revision and fingerprint.

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

Across Principal revisions, `principal_id`, `principal_class`, `environment`,
and lifecycle-controller lineage are immutable. A class or environment change
requires a new Principal. Only `ROTATE_CREDENTIALS` may change credential
handles or advance the exact same Profile ID.

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

A Binding successor is contiguous, uses exact current-head CAS, preserves
`binding_id`, `actor_id`, and `principal_id`, and may only advance exact
Actor/Principal/Profile revisions, narrow scope, or shorten its validity
window. A different Actor or Principal requires a new `binding_id`.

One active `principal_id` binds at most one `actor_id`. One Actor may have
multiple active Principals only for distinct active representation surfaces.
A Binding is exact to `actor_identity_revision`; an Actor identity revision
advance makes the old Binding non-current until explicitly superseded or
replaced. A Binding proves representation only and grants neither permission
nor responsibility.

The closed compatibility negatives are:

```text
AGENT_SESSION cannot bind JENN_HUMAN_ROOT
HUMAN_SESSION cannot silently bind RESIDENT_COORDINATOR
HOST_PROCESS cannot bind JENN_HUMAN_ROOT or RESIDENT_COORDINATOR
```

### 3.4 Actor

Source: R8 Sections 7.1-7.3, with the R16 Section 2.3 authority-basis
replacement and R18 Section 2.1 field removal; R19 Section 2 supplies the
downstream Actor assessment and time overlay.

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

Across Actor revisions, `actor_id`, `actor_class`, and identity-stewardship
lineage are immutable. Actor-class or stewardship-lineage change requires a
new `actor_id`.

`assignment_binding_ref` is not an effective Actor field and is rejected for
every class. A Temporary Worker requires `validity_window`; its identity state
does not depend on responsibility currentness. Operational use is decided only
by the R18 derived assessment in Section 10.

CREATE authority is class-exclusive. The complete CREATE table is:

| Actor class | Source | Target | Exact authority path |
|---|---|---|---|
| `JENN_HUMAN_ROOT` | none | `ACTIVE` | existing Jenn governance bootstrap using `JENN_GOVERNANCE_DECISION_BASIS` |
| `RESIDENT_COORDINATOR` | none | `ACTIVE` | R16 CREATE stewardship; exact Jenn steward |
| `DOMAIN_AGENT` | none | `ACTIVE` | R16 CREATE stewardship; exact Jenn or current Resident Coordinator steward |
| `TEMPORARY_WORKER` | none | `ACTIVE` | R16 CREATE stewardship; exact Jenn, current Resident Coordinator, or responsible Domain Agent steward |
| `SYSTEM_SERVICE` | none | `ACTIVE` | accepted provisioning path only |
| `EXECUTION_HOST` | none | `ACTIVE` | accepted provisioning path only |

Ordinary Actors cannot use the Jenn governance-bootstrap CREATE path. Jenn,
System Service, and Execution Host cannot use the R16 stewardship CREATE path.
Only System Service and Execution Host can use provisioning CREATE.

The remaining lifecycle transition table is:

| Transition | Source | Target | Exact authority kind |
|---|---|---|---|
| `UPDATE` | `ACTIVE` | `ACTIVE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |
| `UPDATE` | `SUSPENDED` | `SUSPENDED` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `BOUND_ACTOR_SELF_SUSPEND_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |
| `RESUME` | `SUSPENDED` | `ACTIVE` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION` |
| `COMPROMISE` | `ACTIVE` or `SUSPENDED` | `COMPROMISED` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |
| `RECOVER` | `COMPROMISED` | `ACTIVE` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION`, plus recovery evidence |
| `RETIRE` | `ACTIVE`, `SUSPENDED`, or `COMPROMISED` | `RETIRED` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, or allowed `ACCEPTED_PROVISIONING_ACTION` |

`RETIRED` is terminal. Self action cannot resume, recover, update, or retire.
`ACCEPTED_PROVISIONING_ACTION` for UPDATE is allowed only for
`SYSTEM_SERVICE` or `EXECUTION_HOST`.

## 4. Complete authority schema and tables

### 4.1 Authority basis

Source: R8 Section 3.1 as replaced by R9 Section 5 and narrowed by R20 Section 5.

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

`JennRootGovernanceAuthorityRefV0_1R8.permitted_basis_uses` is a sorted,
non-empty, duplicate-free subset of this closed set:

```text
IDENTITY_BOOTSTRAP
SYNTHETIC_M0_MANIFEST_GOVERNANCE
```

Its source decision predates the mutation intent, its validity window contains
intent issuance, and the selected basis use matches the mutation. Empty,
unknown, duplicate, reordered, expired, or mismatched values reject.

Current-state basis watermark always equals intent expected ledger head. The
Jenn governance basis revalidates its prior source authority at that same head.
Every optional field not required by its exact basis kind is forbidden.

Exact required/forbidden matrix:

| Basis kind | Required exact inputs | Forbidden inputs |
|---|---|---|
| `JENN_ROOT_ACTION` | requested Jenn Actor ref, ACTIVE identity assessment, ACTIVE effective Jenn Binding, exact root relation | Profile/controller, responsibility, incident, provisioning |
| `JENN_GOVERNANCE_DECISION_BASIS` | exact revalidated Jenn root governance authority ref/fingerprint | requested Actor/Binding, relation/responsibility, Profile/controller, incident, provisioning |
| `IDENTITY_STEWARD_ACTION` | steward Actor ref, ACTIVE identity/Binding, exact `VALID IdentityStewardshipAssessmentV0_1R19` target relation | Profile/controller, responsibility, incident, provisioning |
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

For `IDENTITY_STEWARD_ACTION`, `target_relation_ref/fingerprint` name only the
exact R19 stewardship assessment; an independent relation, responsibility
assessment, target object, Principal, or caller assertion rejects. The
assessment target Actor is derived by this closed matrix:

| Consumer | Exact target Actor |
|---|---|
| `RESIDENT_ATTESTED_AGENT_SESSION` Binding issuance | Actor revision named by the proposed Binding and issuance snapshot |
| Binding `SUSPEND`, `RESUME`, or `REVOKE` | Actor revision named by the current target Binding |
| Binding activation-evidence transition | Actor revision named by the evidence target Binding |
| Actor-target CompromiseImpact | exact compromised Actor revision |

The assessment is `VALID`, uses the authority/intent watermark, names the
requested steward, and has relation kind `JENN_ROOT_STEWARD`, `JENN_STEWARD`,
`NOBAO_STEWARD`, or `RESPONSIBLE_DOMAIN_AGENT_STEWARD`. Any unlisted generic
consumer forbids `IDENTITY_STEWARD_ACTION`. Actor lifecycle transitions use
the separately typed R16/R19 Actor authority bases.

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
| Binding activation evidence | `RESUME` | current SUSPENDED evidence plus exact `VALID ActivationEvidenceResumeRevalidationAssessmentV0_1R19` binding a new current proof and the expected SUSPEND head | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| Delegation activation evidence | `SUSPEND` or `REVOKE` | current evidence and delegator current | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` |
| Delegation activation evidence | `RESUME` | current SUSPENDED evidence plus exact `VALID ActivationEvidenceResumeRevalidationAssessmentV0_1R19` binding the acknowledgement, current principal Binding, source, ancestors, and expected SUSPEND head | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` |
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

| Compromised target | Impact | Exact allowed basis |
|---|---|---|
| Actor | `CHALLENGE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Actor | `INVALIDATE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION` |
| Actor | `CLEAR_CHALLENGE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION` |
| Principal | `CHALLENGE` | `JENN_ROOT_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Principal | `INVALIDATE` | `JENN_ROOT_ACTION` |
| Principal | `CLEAR_CHALLENGE` | `JENN_ROOT_ACTION` |

| Current stream state | Allowed successor | Target membership |
|---|---|---|
| none | `CHALLENGE`, `INVALIDATE` | fixes exact sorted set and fingerprint |
| `CHALLENGED` | `CLEAR_CHALLENGE`, `INVALIDATE` | must be byte-identical to revision 1 |
| `INVALIDATED` | none | terminal and indexed by all members |
| `CLEARED` | none | terminal and indexed by all members |

An incident policy cannot invalidate or clear. Principal-target impact
forbids `IDENTITY_STEWARD_ACTION`; no Binding, represented Actor, Profile
controller, credential, or caller assertion is converted into Principal
stewardship.

Historical aggregate remains:

```text
any verified INVALIDATED -> INVALIDATED
else incomplete/conflicting coverage -> INDETERMINATE
else any CHALLENGED -> CHALLENGED
else -> CONFIRMED
```

## 6. Complete total reducers

### 6.1 `BindingEffectiveCurrentReducer`

Source: R7 Section 7.3, R15 Sections 5.2-5.3, and R16 Section 3.4. This sole
indexed reducer applies the closed assurance graph before ordinary Binding
currentness. Binding activation assurance is consumed transitively through the
exact fingerprinted `BindingActivationAssessmentV0_1R16`; it is not duplicated
in the effective Binding assessment.

```text
missing, extra, duplicated, stale, forked, watermark-mismatched, or
  fingerprint-mismatched direct Binding action-role coverage or transitive
  activation assurance -> INDETERMINATE, except that an already proven
  effective safer transition state remains effective
Binding issuance or activation assurance INVALIDATED -> REVOKED prospectively
Binding issuance or activation assurance CHALLENGED or INDETERMINATE
  -> INDETERMINATE, except that an already proven effective SUSPEND or REVOKE
  remains SUSPENDED or REVOKED
all required enabling issuance and activation assurance CONFIRMED -> continue
effective Binding REVOKE -> REVOKED
Binding head no longer current -> SUPERSEDED
effective SUSPEND without later valid RESUME -> SUSPENDED
missing/forked head, transition, Actor, Principal, Profile, credential,
  activation, time, snapshot, intent, action, replay, Event, or fingerprint
  -> INDETERMINATE
trusted now before not_before -> NOT_YET_ACTIVE
expires_at is non-null and trusted now at/after expires_at -> EXPIRED
expires_at is null -> continue without an expiry branch
Actor NOT_YET_ACTIVE -> NOT_YET_ACTIVE
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
all exact dependencies current and valid and every required direct and
  transitive assurance CONFIRMED -> ACTIVE
```

Activation proves only the later proof/evidence graph. This reducer alone owns
`binding_effective_current_projection`. Challenged or invalidated enabling
assurance never restores a less safe state; only a new explicit valid
compensation action may change an already effective safety transition.

### 6.2 `ResponsibilityAssignmentEffectiveReducer`

This reducer inlines the complete R15 Section 3.4 and R16 Section 3.4 order.
Its closed reduction sequence is:

```text
missing, extra, duplicated, stale, forked, or fingerprint-mismatched required
  action-role coverage -> INDETERMINATE, except that an already proven effective
  safer transition state remains effective
issuance assurance INVALIDATED -> REVOKED
issuance assurance CHALLENGED or INDETERMINATE -> INDETERMINATE, except that an
  already proven effective SUSPEND or REVOKE remains SUSPENDED or REVOKED
issuance assurance CONFIRMED -> continue
effective REVOKE -> REVOKED
non-current head -> SUPERSEDED
effective SUSPEND without later valid RESUME -> SUSPENDED
missing/conflicting head, recipient identity, scope, transition, time, source,
  body, intent, action, replay, Event, or fingerprint -> INDETERMINATE
recipient Actor NOT_YET_ACTIVE -> NOT_YET_ACTIVE
recipient Actor SUSPENDED -> SUSPENDED
recipient Actor COMPROMISED, RETIRED, or EXPIRED -> REVOKED
before start -> NOT_YET_ACTIVE
expiry is non-null and trusted now is at/after expiry -> EXPIRED
expiry is null -> continue without an expiry branch
all exact current inputs valid and every required assurance CONFIRMED -> ACTIVE
```

No challenged or invalidated enabling action restores a less safe state. Only a
new explicit valid compensation action may change an already effective safety
transition as specified by R16.

### 6.3 `DelegationEffectiveCurrentReducer`

Exact precedence:

```text
REVOKED > SUPERSEDED > SUSPENDED > INDETERMINATE > EXPIRED > NOT_YET_ACTIVE > ACTIVE
```

```text
own REVOKE or RENOUNCE -> REVOKED
target-own `DELEGATION_ISSUANCE` assurance or transitive Delegation activation
  assurance INVALIDATED
  -> REVOKED prospectively
any root/ancestor REVOKED, RENOUNCED, or assurance INVALIDATED -> REVOKED
delegator or delegate Actor COMPROMISED, RETIRED, or EXPIRED -> REVOKED
own head or any required exact ancestor SUPERSEDED -> SUPERSEDED
delegator or delegate Actor SUPERSEDED, named identity revision advanced
  normally, or required Binding/source/parent revision replaced -> SUPERSEDED
own or any root/ancestor SUSPENDED -> SUSPENDED
delegator or delegate Actor SUSPENDED -> SUSPENDED
target-own `DELEGATION_ISSUANCE` assurance or transitive Delegation activation
  assurance CHALLENGED or INDETERMINATE -> INDETERMINATE while preserving any
  already effective safer state
delegator or delegate Actor INDETERMINATE -> INDETERMINATE
any other missing/conflicting/challenged/indeterminate dependency -> INDETERMINATE
own or any root/ancestor EXPIRED -> EXPIRED
target delegate Actor NOT_YET_ACTIVE -> NOT_YET_ACTIVE
own or any root/ancestor NOT_YET_ACTIVE -> NOT_YET_ACTIVE
all exact root-to-target inputs ACTIVE and every required direct and transitive
  assurance CONFIRMED -> ACTIVE
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

Profile and Principal specs use their exact R20 own-domain digests. Only
Binding specs use the `BINDING_REVISION` body digest. The precommit input has no
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

Cross-field numeric, revision, and Event invariants are:

```text
dual-predecessor lifecycle subject revision 1:
  expected_previous_revision = null
  supersedes_revision = null

dual-predecessor lifecycle subject revision N greater than 1:
  expected_previous_revision = N - 1
  supersedes_revision = N - 1

finite expires_at_utc_ms:
  not_before_utc_ms < expires_at_utc_ms

MutationIntent:
  issued_at_utc_ms < expires_at_utc_ms

assessment Event sequence <= current recovered Event sequence
remaining_depth <= maximum_edges_per_chain - 1
```

Every Actor, Profile, Principal, Binding, Assignment, Delegation, and Binding
or Delegation activation-evidence subject revision stream has one current
head. A successor names N - 1 in its two schema-specific predecessor fields,
and N - 1 is the exact current head in the accepting transaction.

Each CompromiseImpact stream has one current head under its distinct R8 CAS.
Revision 1 has null `expected_previous_impact_revision` and null
`expected_previous_impact_event_sequence`. Revision N greater than 1 names
N - 1 and that exact current head's effective Event sequence. It has no
`supersedes_revision` field.

Each synthetic manifest activation stream also has one unique contiguous
current head under its distinct R8-R9 CAS. Revision 1 is `ACCEPT` with null
`expected_previous_activation_revision`; a later revision names N - 1 and may
only be the terminal Jenn `REVOKE`. It has no second predecessor field.

Governed transition facts, including facts targeting activation evidence, use
the exact target head in `expected_target_head`; the facts are not themselves
dual-predecessor revision streams. In every branch, the immutable accepted
object or fact, its current-pointer advance, and its Event append are one
transaction. Skips, forks, stale CAS, duplicate heads, wrong target/body
values, and fingerprint mismatch reject before any enabling assessment.

R20 nullable expiry is total for Binding and Responsibility Assignment:

```text
expires_at_utc_ms = null means a known unbounded future expiry
null is encoded as JSON null and is never omitted or coerced

trusted now < not_before -> NOT_YET_ACTIVE
finite expiry and trusted now >= expiry -> EXPIRED
null expiry -> no expiry branch; every other reducer input still applies
missing or uncertain trusted time -> INDETERMINATE
```

The admission and narrowing truth table is:

| Source expiry | Candidate expiry | Result |
|---|---|---|
| null | null | equal, allowed |
| null | finite valid value | shorter, allowed |
| finite S | finite C with C less than or equal to S | equal or shorter, allowed |
| finite S | finite C greater than S | wider, reject |
| finite | null | wider, reject |

The candidate start is greater than or equal to the source start and its own
finite end is strictly after its start. Binding snapshots, synthetic
precommit inputs, and Binding creation specs repeat the exact Binding value and
cannot reinterpret null.

The complete canonical array-order registry needed by authoritative F2
fingerprints, exact sets, and reducers is:

| Array family or exact field | Canonical order |
|---|---|
| reason codes, principal classes, environments | NFC UTF-8 bytes |
| permitted basis uses and supported mutation kinds | displayed closed-enum order |
| identity-charter, credential-handle, trust-anchor, basis, proof, artifact-metadata, and assessment refs | ref kind/type, stable ID, then revision under the owning schema |
| SyntheticM0AuthenticatorProfileCreationSpecV0_1R20.trust_anchor_refs | exact normalized stable-ref UTF-8 bytes |
| SyntheticM0PrincipalCreationSpecV0_1R20.credential_handle_refs | normalized opaque-ref UTF-8 bytes |
| Actor, Principal, Binding, Assignment, and Delegation revision refs | stable ID, then revision |
| BindingScope contexts | context kind, NFC context ID, numeric context revision |
| current transition facts | effective Event sequence, then fact ID |
| compromise-impact facts | effective Event sequence, then impact fact ID |
| complete target action refs | action ref ID, then action fingerprint bytes |
| synthetic_profile_creation_specs | profile_id normalized UTF-8 bytes |
| synthetic_principal_creation_specs | principal_id normalized UTF-8 bytes |
| permitted_binding_creation_specs | binding_id normalized UTF-8 bytes |
| responsibility resource refs | resource kind, NFC resource ID, revision with null first |
| Delegation lineage and ancestry | semantic root-to-leaf; sorting is forbidden |
| complete affected Binding refs | Binding ID, then revision |
| binding dispositions | contained Binding ID, then revision |
| HistoricalImpactInputSet current impact heads | impact stream ID, then revision |
| action assurance bindings | R17 enum ordinal, action-ref NFC bytes, fingerprint bytes |
| PrincipalAssessmentV0_1R16 credential-status assessment ref/fingerprint arrays | same length, paired by credential-handle stable ref, sorted by that credential-handle stable ref, duplicate-free |
| other paired ref/fingerprint arrays in R16-R20 assessments | same length, owning stable-ref order, duplicate-free |

Every listed collection is duplicate-free under its owning stable key.
Paired arrays preserve pair identity and cannot be sorted independently. An
array not covered here or by a more specific effective source rule rejects;
order is never guessed. This registry controls canonical bytes only and adds
no permission or business capability.

Source: R1 Section 18; R2 Section 9; R4 Sections 2-3; R5-R7 scalar
amendments; R7 Sections 2.3, 3.2, and 3.3; R8 Sections 2.1 and 6.2; R15
Section 2; R16 Section 3; R17 Section 2; R19 Section 3; and R20 Sections 3-6.

All numeric admission operates only on the already-parsed ECMAScript
`Number`/IEEE-754 binary64 value. The source JSON token spelling, decimal
precision, exponent notation, and information loss during standards-compliant
parsing are not retained and are not independent rejection conditions. A value
rejects only when the parsed value fails its owning predicate. Negative zero,
parsed non-integers, non-finite parsed values, and unsafe parsed integers reject;
parser rounding by itself does not reject. Text is Unicode 15.1 NFC. Unknown
keys, undefined values, normalized-key collisions, and unordered arrays without
a declared order reject.

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

R6 parsed-number conformance examples are normative:

| JSON source token | Parsed binary64 value | Result |
|---|---:|---|
| `0` | `+0` | accept |
| `-0` | `-0` | reject |
| `1e3` | `1000` | accept |
| `1.5` | `1.5` | reject |
| `9007199254740990.5` | `9007199254740990` | accept |
| `9007199254740991` | `9007199254740991` | accept |
| `9007199254740991.5` | `9007199254740992` | reject |
| `9007199254740992` | `9007199254740992` | reject |

`BindingScopeV0_1.contexts` is non-empty and sorts by `context_kind` NFC UTF-8
bytes, then `context_id` normalized UTF-8 bytes, then numeric
`context_revision`. Duplicate normalized tuples reject. Wildcard, glob, regex,
subtree, future context, free-form map, and unknown context kind reject.

`BindingScopeContextV0_1.context_id` is a Unicode scalar-value string normalized
with Unicode 15.1 NFC before validation. Its normalized value contains 1 through
256 Unicode scalar values and contains no U+0000-U+001F, U+007F, or
U+0080-U+009F. Normalized UTF-8 bytes determine ordering and equality.

`R4FingerprintEnvelope` is an envelope value, not a separately fingerprinted
record. `CanonicalDigestScalarV0_1` is a scalar value. The scalar profile,
Binding scope context, lifecycle window, controller ref, Delegation policy,
and assurance role retain exactly the domains or `NOT_STANDALONE`
classification stated in Section 21; v15 does not invent domains for them.

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
| Identity stewardship assessment | `agents-os.identity-stewardship-assessment.v0.1-r19` |
| Identity recovery evidence | `agents-os.identity-recovery-evidence.v0.1-r15` |
| Actor CREATE target spec | `agents-os.actor-create-stewardship-target-spec.v0.1-r16` |
| Actor CREATE stewardship assessment | `agents-os.actor-create-stewardship-assessment.v0.1-r16` |
| Actor CREATE authority basis | `agents-os.actor-create-steward-authority-basis.v0.1-r16` |
| Actor general transition authority basis | `agents-os.actor-general-transition-authority-basis.v0.1-r16` |
| Action assurance binding | `agents-os.action-assurance-binding.v0.1-r17` |
| Temporary Worker responsibility binding ref | `agents-os.temporary-worker-responsibility-binding-ref.v0.1-r18` |
| Temporary Worker responsibility binding assessment | `agents-os.temporary-worker-responsibility-binding-assessment.v0.1-r18` |
| Activation-evidence RESUME revalidation assessment | `agents-os.activation-evidence-resume-revalidation-assessment.v0.1-r19` |
| Temporary Worker stewardship scope assessment | `agents-os.temporary-worker-stewardship-scope-assessment.v0.1-r19` |

Unregistered derived-record fingerprints cannot be normative F2 inputs.

### 8.1 Exact special formula catalogue

The general registered-record rule above does not replace the following
source-defined special projections. These formulas are complete and normative.

Delegation activation acknowledgement replay identity:

```text
SHA-256(JCS([
  "agents-os.delegation-activation-ack.v0.1",
  command_envelope_fingerprint,
  delegation_ref,
  delegation_subject_fingerprint,
  acknowledging_principal_binding_ref
]))
```

Stable activation-evidence IDs:

```text
binding evidence_id = SHA-256(JCS([
  "agents-os.binding-activation-evidence-id.v0.1",
  binding_id,
  binding_revision
]))

delegation evidence_id = SHA-256(JCS([
  "agents-os.delegation-activation-evidence-id.v0.1",
  delegation_id,
  delegation_revision
]))
```

Binding scope fingerprint:

```text
binding_scope_fingerprint = SHA-256(JCS([
  "agents-os.binding-scope.v0.1",
  "EXACT_REPRESENTATION_CONTEXT_SET",
  [[context_kind, context_id, context_revision], ... canonical order]
]))
```

Authenticated Actor action ref fingerprint:

```text
canonical_action_ref_fingerprint = SHA-256(JCS([
  "agents-os.authenticated-actor-action-ref.v0.1",
  interface_version,
  action_ref_id,
  F3_contract_version,
  command_id,
  command_envelope_ref,
  command_envelope_fingerprint,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  principal_binding_ref,
  authentication_assertion_ref,
  authentication_assessment_ref,
  responsibility_source_ref,
  delegation_chain_fingerprint_or_null,
  prohibited_behavior_list_revision,
  prohibited_boundary_evidence_ref,
  F3_intake_event_sequence,
  F3_intake_state_ref
]))
```

Delegation activation acknowledgement fingerprint:

```text
delegation_activation_ack_ref_fingerprint = SHA-256(JCS([
  "agents-os.delegation-activation-acknowledgement-ref.v0.1",
  interface_version,
  acknowledgement_ref_id,
  F3_contract_version,
  "COMMITTED",
  "DELEGATION_ACTIVATION_ACK",
  intake_event_sequence,
  command_envelope_ref,
  command_envelope_fingerprint,
  "DELEGATION_ACTIVATION_ACK",
  delegation_ref,
  delegation_subject_fingerprint,
  delegate_actor_id,
  delegate_actor_identity_revision,
  acknowledging_principal_id,
  acknowledging_principal_revision,
  acknowledging_principal_binding_ref,
  authentication_assertion_ref,
  authentication_assessment_ref,
  "NONE_ACTIVATION_PURPOSE_ONLY",
  prohibited_behavior_list_revision,
  prohibited_boundary_evidence_ref,
  replay_identity
]))
```

Activation evidence replay identities:

```text
binding_activation_evidence_replay_identity = SHA-256(JCS([
  "agents-os.binding-activation-evidence-replay.v0.1",
  evidence_id,
  target_binding_ref,
  binding_subject_fingerprint,
  actor_id,
  actor_identity_revision,
  principal_id,
  principal_revision,
  principal_class,
  environment,
  authenticator_profile_ref,
  verifier_revision,
  principal_control_proof_assessment_ref_fingerprint,
  activation_mode,
  stewardship_source.kind,
  stewardship_source.source_ref,
  steward_actor_id_or_null,
  steward_actor_identity_revision_or_null,
  steward_principal_binding_ref_or_null,
  canonical_steward_action_ref_fingerprint_or_null,
  not_before_utc_ms,
  expires_at_utc_ms
]))

delegation_activation_evidence_replay_identity = SHA-256(JCS([
  "agents-os.delegation-activation-evidence-replay.v0.1",
  evidence_id,
  delegation_ref,
  delegation_subject_fingerprint,
  activation_mode,
  delegate_actor_id,
  delegate_actor_identity_revision,
  acknowledging_principal_binding_ref,
  delegation_activation_ack_ref_fingerprint,
  not_before_utc_ms,
  expires_at_utc_ms
]))
```

R19 Delegation issuance intent and final subject:

```text
delegation_issuance_intent_fingerprint = SHA-256(JCS([
  "agents-os.delegation-issuance-intent.v0.1-r19",
  delegation_id,
  delegation_revision,
  expected_previous_delegation_revision_or_null,
  supersedes_delegation_revision_or_null,
  delegator_actor_id,
  delegator_identity_revision,
  delegate_actor_id,
  delegate_identity_revision,
  parent_delegation_ref_or_null,
  source_responsibility_ref,
  responsibility_kind,
  responsibility_scope,
  may_redelegate,
  remaining_depth,
  not_before_utc_ms,
  expires_at_utc_ms,
  activation_mode,
  issued_by_actor_id,
  issued_by_actor_identity_revision,
  issued_by_principal_binding_ref,
  issuer_currentness_event_sequence,
  root_direction_ref_or_null,
  root_direction_fingerprint_or_null,
  source_assignment_ref_or_null,
  source_assignment_fingerprint_or_null,
  reason_code,
  reason_artifact_ref_or_null,
  status
]))

delegation_subject_fingerprint = SHA-256(JCS([
  "agents-os.delegation-grant-subject.v0.1-r4",
  delegation_issuance_intent_fingerprint,
  issuance_action_ref.F3_contract_version,
  issuance_action_ref.canonical_action_ref_fingerprint,
  created_at_event_sequence
]))
```

Responsibility lineage, generic mutation body, and lifecycle replay:

```text
responsibility_lineage_fingerprint = SHA-256(JCS([
  "agents-os.responsibility-lineage.v0.1-r7",
  root_source_ref,
  root_source_fingerprint,
  [[delegation_ref, delegation_subject_fingerprint], ... root-to-leaf]
]))

mutation_body_fingerprint = SHA-256(JCS([
  "agents-os.mutation-body.v0.1",
  mutation_kind,
  mutation_kind_specific_schema_known_object
]))

mutation_replay_identity = SHA-256(JCS([
  "agents-os.lifecycle-mutation-replay.v0.1-r8",
  mutation_intent_fingerprint,
  action_ref,
  action_fingerprint
]))
```

R20 synthetic creation specs and local digest formulas:

```text
synthetic_profile_creation_spec_fingerprint = SHA-256(JCS([
  "agents-os.synthetic-m0-authenticator-profile-creation-spec.v0.1-r20",
  {
    "profile_id": profile_id,
    "profile_revision": 1,
    "expected_previous_profile_revision": null,
    "supersedes_profile_revision": null,
    "transition_kind": "CREATE",
    "source_status": null,
    "status": "ACTIVE",
    "proof_kind": "SYNTHETIC_FIXTURE",
    "supported_principal_classes": ["SYNTHETIC_TEST_PRINCIPAL"],
    "supported_environments": ["SYNTHETIC_TEST"],
    "verifier_id": verifier_id,
    "verifier_revision": 1,
    "trust_anchor_refs": canonical_trust_anchor_refs,
    "assertion_max_age_ms": assertion_max_age_ms,
    "clock_policy_ref": clock_policy_ref,
    "replay_policy_ref": replay_policy_ref
  }
]))

synthetic_principal_creation_spec_fingerprint = SHA-256(JCS([
  "agents-os.synthetic-m0-principal-creation-spec.v0.1-r20",
  {
    "principal_id": principal_id,
    "principal_revision": 1,
    "expected_previous_principal_revision": null,
    "supersedes_principal_revision": null,
    "transition_kind": "CREATE",
    "source_status": null,
    "principal_class": "SYNTHETIC_TEST_PRINCIPAL",
    "environment": "SYNTHETIC_TEST",
    "authenticator_profile_creation_spec_ref": authenticator_profile_creation_spec_ref,
    "authenticator_profile_creation_spec_fingerprint": authenticator_profile_creation_spec_fingerprint,
    "credential_handle_refs": canonical_credential_handle_refs,
    "status": "ACTIVE"
  }
]))

derivation_replay_identity = SHA-256(JCS([
  "agents-os.synthetic-manifest-derived-lifecycle-replay.v0.1-r20",
  manifest_ref,
  manifest_fingerprint.digest_lowercase_hex,
  manifest_assessment_ref,
  manifest_assessment_fingerprint.digest_lowercase_hex,
  controller_id,
  controller_spec_fingerprint.digest_lowercase_hex,
  spec_kind,
  spec_id,
  spec_fingerprint.digest_lowercase_hex
]))

complete_target_set_fingerprint = SHA-256(JCS([
  "agents-os.compromise-complete-target-action-set.v0.1-r20",
  compromised_actor_or_principal_ref,
  selection_basis_event_sequence,
  [[action_ref, action_fingerprint.digest_lowercase_hex],
   ... canonical action-ref order]
]))

complete_affected_binding_set_fingerprint = SHA-256(JCS([
  "agents-os.identity-recovery-complete-affected-binding-set.v0.1-r20",
  actor_id,
  compromised_actor_identity_revision,
  affected_binding_set_basis_event_sequence,
  [binding_ref, ... canonical Binding-ref order]
]))
```

All five digest results use the existing owning result type. The three local
digest results are CanonicalDigestScalarV0_1 lowercase hex strings. Creation
spec fingerprints use R4FingerprintEnvelope. Complete target actions sort by
action ref and fingerprint and reject duplicate action refs. Complete affected
Bindings sort by Binding ID and revision and have exact set equality with
binding_dispositions. Missing coverage, unresolved refs, omissions,
duplicates, or alternate order reject before the containing body is accepted.

Historical impact input set:

```text
impact_input_set_fingerprint = SHA-256(JCS([
  "agents-os.historical-impact-input-set.v0.1",
  action_ref,
  action_fingerprint,
  coverage_through_event_sequence,
  [[impact_stream_id, impact_revision, impact_fact_fingerprint,
    effective_at_event_sequence, stream_state], ... canonical order]
]))
```

Effective Actor subject fingerprint, with the R18-removed
`assignment_binding_ref` absent:

```text
actor_identity_fingerprint = SHA-256(JCS([
  "agents-os.actor-identity-revision.v0.1-r8",
  {
    "schema_version": schema_version,
    "actor_id": actor_id,
    "actor_identity_revision": actor_identity_revision,
    "expected_previous_actor_identity_revision": expected_previous_actor_identity_revision_or_null,
    "supersedes_actor_identity_revision": supersedes_actor_identity_revision_or_null,
    "actor_class": actor_class,
    "canonical_name": canonical_name,
    "identity_charter_refs": canonical_identity_charter_refs,
    "identity_steward_ref": identity_steward_ref,
    "parent_actor_ref": parent_actor_ref_or_null,
    "transition_kind": transition_kind,
    "source_status": source_status_or_null,
    "status": status,
    "validity_window": canonical_validity_window_or_null,
    "transition_authority_basis_fingerprint": transition_authority_basis_fingerprint,
    "mutation_body_fingerprint": mutation_body_fingerprint,
    "mutation_intent_fingerprint": mutation_intent_fingerprint,
    "lifecycle_action_ref_fingerprint": lifecycle_action_ref.canonical_fingerprint.digest_lowercase_hex,
    "mutation_replay_identity": mutation_replay_identity,
    "recovery_evidence_ref": recovery_evidence_ref_or_null,
    "change_reason_code": change_reason_code,
    "created_at_event_sequence": created_at_event_sequence
  }
]))
```

Binding and Assignment body/final fingerprints:

```text
binding_subject_fingerprint = SHA-256(JCS([
  "agents-os.actor-principal-binding-revision.v0.1-r9",
  complete_effective_Binding_known_object_without_canonical_fingerprint
]))

assignment_mutation_body_fingerprint = SHA-256(JCS([
  "agents-os.responsibility-assignment-body.v0.1-r15",
  complete_Assignment_body_known_object
]))

assignment_subject_fingerprint = SHA-256(JCS([
  "agents-os.responsibility-assignment-revision.v0.1-r15",
  complete_effective_Assignment_known_object_without_canonical_fingerprint
]))
```

Temporary Worker responsibility binding ref:

```text
temporary_worker_responsibility_binding_fingerprint = SHA-256(JCS([
  "agents-os.temporary-worker-responsibility-binding-ref.v0.1-r18",
  worker_actor_id,
  source_kind,
  source_subject_ref,
  source_subject_fingerprint,
  bound_resource_ref
]))
```

R19 registered derived assessments use their complete printed known objects:

```text
resume_revalidation_assessment_fingerprint = SHA-256(JCS([
  "agents-os.activation-evidence-resume-revalidation-assessment.v0.1-r19",
  complete_ActivationEvidenceResumeRevalidationAssessmentV0_1R19_without_canonical_fingerprint
]))

worker_stewardship_scope_assessment_fingerprint = SHA-256(JCS([
  "agents-os.temporary-worker-stewardship-scope-assessment.v0.1-r19",
  complete_TemporaryWorkerStewardshipScopeAssessmentV0_1R19_without_canonical_fingerprint
]))

identity_stewardship_assessment_fingerprint = SHA-256(JCS([
  "agents-os.identity-stewardship-assessment.v0.1-r19",
  complete_IdentityStewardshipAssessmentV0_1R19_without_canonical_fingerprint
]))
```

R3 Binding and Delegation subject formulas, the pre-R4 principal-control-proof
formula, pre-R4 activation evidence/assessment formulas, the R3 Delegation
intent domain, and any Actor projection containing `assignment_binding_ref` are
superseded and forbidden in new effective records.

## 9. Actor identity, stewardship, and recovery

Source: R2 Sections 7.2 and 9; R8 Section 7; R13-R16; R18 Section 2; R19
Sections 2 and 4; and R20 Sections 4.3, 5, and 6.

The complete Actor revision schema remains Section 3.4 of this materialization.
Its sole current assessment is:

```yaml
ActorIdentityAssessmentV0_1R16:
  actor_identity_ref:
  actor_identity_fingerprint:
  current_head_ref:
  current_head_fingerprint:
  time_authority_ref:
  action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | COMPROMISED | RETIRED | EXPIRED | SUPERSEDED | INDETERMINATE
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
  malformed validity window, or fingerprint conflict -> INDETERMINATE
validity window exists and trusted now < not_before_utc_ms -> NOT_YET_ACTIVE
validity window exists and trusted now >= expires_at_utc_ms -> EXPIRED
all class/lifecycle/time dependencies current -> ACTIVE
```

The active interval is exactly
`not_before_utc_ms <= trusted now < expires_at_utc_ms`. A Temporary Worker with
a missing validity window is `INDETERMINATE`; other classes omit the window
unless their accepted profile requires one. `NOT_YET_ACTIVE` is derived only;
it is not a stored Actor status or transition target.

A Temporary Worker identity may be `ACTIVE` without current responsibility.
That state does not permit operational use. Section 10 owns the separate
responsibility-binding projection and F3 must require it to be `ACTIVE`.

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
  intended_initial_resource_ref: ResponsibilityResourceRefV0_1 | null
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

The complete Actor general-basis matrix is:

| Basis kind | Required exact inputs and admitted use | Required null or forbidden inputs |
|---|---|---|
| JENN_ROOT_ACTION | requested Jenn Actor, ACTIVE identity/Binding, exact root relation | incident and provisioning inputs |
| JENN_GOVERNANCE_DECISION_BASIS | exact revalidated Jenn-root authority; Jenn CREATE or recovery bootstrap only | requested Actor/Binding, stewardship, incident, provisioning |
| IDENTITY_STEWARD_ACTION | requested steward Actor ACTIVE identity/Binding and exact VALID R19 stewardship assessment; post-create only | Jenn-root, incident, provisioning |
| BOUND_ACTOR_SELF_SUSPEND_ACTION | exact current ACTIVE target Actor and Binding; SUSPEND only | Jenn-root, stewardship, incident, provisioning |
| ACCEPTED_INCIDENT_POLICY_ACTION | policy ref/fingerprint/controller; SUSPEND or COMPROMISE only | requested Actor/Binding, Jenn-root, stewardship, provisioning |
| ACCEPTED_PROVISIONING_ACTION | component ref/fingerprint and basis ref/fingerprint; System Service or Execution Host CREATE, UPDATE, SUSPEND, COMPROMISE, or RETIRE only | requested Actor/Binding, Jenn-root, stewardship, incident |

Every schema-known optional field not selected by its row is JSON null and is
semantically forbidden. The basis, every assessment, and the MutationIntent
use one exact expected-head watermark. Unlisted class, transition, or basis
tuples reject.

The target spec is content-addressed input, not a ledger stream. Its absence
watermark, assessment watermark, and basis watermark are equal. Stable Actor
identity fields in the later CREATE body are byte-equal to the spec. The exact
acyclic order is target spec, assessment, basis, mutation body, intent, action,
LifecycleActionRef, and final Actor Event.

R19 adds this target-state-independent scope projection for the responsible
Domain Agent branch only:

```yaml
TemporaryWorkerStewardshipScopeAssessmentV0_1R19:
  target_worker_identity_ref:
  target_worker_identity_fingerprint:
  worker_actor_id:
  declared_domain_agent_steward_ref:
  domain_agent_identity_assessment_ref:
  domain_agent_identity_assessment_fingerprint:
  domain_agent_responsibility_assessment_ref:
  domain_agent_responsibility_assessment_fingerprint:
  worker_responsibility_binding_ref: TemporaryWorkerResponsibilityBindingRefV0_1R18
  worker_responsibility_binding_fingerprint:
  source_subject_ref:
  source_subject_fingerprint:
  source_current_head_ref:
  source_current_head_fingerprint:
  source_transition_fact_refs: []
  source_transition_fact_fingerprints: []
  source_action_assurance_bindings: ActionAssuranceBindingV0_1R17[]
  source_responsibility_scope_fingerprint:
  bound_resource_ref: ResponsibilityResourceRefV0_1
  domain_agent_responsibility_scope_fingerprint:
  time_authority_ref:
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

Its domain is
`agents-os.temporary-worker-stewardship-scope-assessment.v0.1-r19` and it uses
the R15 derived-record profile. Arrays are sorted, paired arrays are parallel,
and all values use one exact watermark.

### 9.2 `TemporaryWorkerStewardshipScopeReducerV0_1R19`

```text
target stable Actor is exactly TEMPORARY_WORKER and its current-head identity
  bytes match worker_actor_id; target assessment state is not an input
declared steward is the exact current ACTIVE Domain Agent
Domain Agent responsibility is ACTIVE and contains bound_resource_ref
worker_actor_id is absent from every Actor position in the Domain Agent
  responsibility root and Delegation lineage
Domain Agent responsibility is not issued, delegated, controlled, or made
  current by the target Worker or a lineage deriving from it
Worker binding ref/fingerprint names the same Worker, source subject, source
  fingerprint, and exact TASK or RUN resource
source Assignment recipient or Delegation delegate equals worker_actor_id
source subject is the unique current head with valid CAS, issuance, lineage,
  activation when Delegation, transitions, assurance, time, scope, and
  fingerprints, excluding only the target Worker's derived identity state from
  the source operational-use projection
source is not suspended, revoked, renounced, expired, superseded, challenged,
  invalidated, or indeterminate
source scope and Domain Agent scope both contain the exact bound resource
all inputs use one exact watermark -> VALID
```

A proven mismatch is `INVALID`; missing, forked, stale, uncertain, or
fingerprint-conflicting evidence is `INDETERMINATE`. The target Worker identity
assessment, the R18 operational Worker binding assessment, and any Domain Agent
responsibility lineage containing or deriving from the target Worker are
forbidden inputs. A `VALID` result is allowlisted only as responsibility
evidence for the following stewardship assessment; it cannot assign work,
activate the Worker, authorize a Command, or create another ledger.

Post-create stewardship is:

```yaml
IdentityStewardshipAssessmentV0_1R19:
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
  responsibility_evidence_fingerprints: []
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
| Temporary Worker | ACTIVE Jenn or Coordinator; responsible Domain Agent requires exactly one `VALID TemporaryWorkerStewardshipScopeAssessmentV0_1R19` ref/fingerprint for the exact post-create R18 bound resource |
| System Service / Execution Host | exact accepted provisioning authority |

Post-create Actor transition authority uses this assessment ref/fingerprint
instead of an independent stewardship relation ref. CREATE uses only the R16
CREATE assessment and basis above.

For Domain Agent stewardship during CREATE,
`intended_initial_resource_ref.resource_kind` is exactly `TASK` or `RUN` and
the steward's current ACTIVE responsibility scope contains the exact tuple.
The field is precommit evidence only and never assigns work. After CREATE, the
responsible Domain Agent branch consumes only the Section 9.2 scope assessment;
the target Worker's non-ACTIVE identity or operational-binding state remains
separate and does not create the former recovery lock.

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
  binding_dispositions:
    - binding_ref:
      disposition: REVOKED | SUPERSEDED_BY_REPLACEMENT
      disposition_event_ref:
      replacement_binding_ref: optional
  stewardship_assessment_ref:
  stewardship_assessment_fingerprint:
  steward_action_ref: LifecycleActionRefV0_1R8
  historical_steward_action_assessment_ref:
  recovery_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Affected Binding refs and dispositions sort by Binding ID and revision.
`binding_dispositions` contains exactly one element for every
`complete_affected_binding_refs` element and no other element. For
`REVOKED`, `replacement_binding_ref` is JSON null; for
`SUPERSEDED_BY_REPLACEMENT`, it is the exact verified replacement Binding.
Missing or extra dispositions, duplicate refs, an invalid disposition Event,
or incomplete ledger-index coverage yields `INDETERMINATE` and cannot activate
recovery.

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

Assignment issuance is non-recursive and non-self-authorizing:

```text
actor_id != issued_by_actor_id
issued_by_actor_id is exactly Jenn under JENN_ROOT_ACTION
no Assignment may issue, justify, widen, renew, or make current another
  Assignment
source_responsibility.kind is exactly JENN_ROOT_DIRECTION
```

Any self-issuance, Assignment-derived issuer authority, or Assignment recursion
rejects before subject construction.

An Assignment successor is contiguous, uses exact current-head CAS, preserves
`assignment_id`, recipient Actor, root source, responsibility kind, and issuer
Jenn identity, and may only narrow scope, shorten its time window, lower
depth, or disable redelegation. Any other change requires a new
`assignment_id`.

The complete effective Assignment assessment is
`ResponsibilityAssignmentAssessmentV0_1R16` in Section 18. Its assurance array
replaces the superseded standalone historical-issuance ref.

The sole complete Assignment reducer is Section 6.2. Assignment recursion is
forbidden.

### 10.1 Temporary Worker responsibility binding

Source: R18 Section 3. These are derived values over existing Assignment or
Delegation facts. They have no independent revision, current head, transition,
mutation command, or writer.

```yaml
TemporaryWorkerResponsibilityBindingRefV0_1R18:
  worker_actor_id:
  source_kind: RESPONSIBILITY_ASSIGNMENT | DELEGATION
  source_subject_ref:
  source_subject_fingerprint:
  bound_resource_ref: ResponsibilityResourceRefV0_1
  canonical_fingerprint: R4FingerprintEnvelope

TemporaryWorkerResponsibilityBindingAssessmentV0_1R18:
  binding_ref: TemporaryWorkerResponsibilityBindingRefV0_1R18
  binding_fingerprint:
  worker_actor_identity_assessment_ref:
  worker_actor_identity_assessment_fingerprint:
  source_subject_ref:
  source_subject_fingerprint:
  source_current_head_ref:
  source_effective_assessment_ref:
  source_effective_assessment_fingerprint:
  responsibility_scope_fingerprint:
  bound_resource_ref: ResponsibilityResourceRefV0_1
  time_authority_ref:
  assessment: NOT_YET_ACTIVE | ACTIVE | SUSPENDED | REVOKED | RENOUNCED | EXPIRED | SUPERSEDED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

The reference fingerprint domain is
`agents-os.temporary-worker-responsibility-binding-ref.v0.1-r18`. Its exact
known-object projection is ordered as:

```text
worker_actor_id
source_kind
source_subject_ref
source_subject_fingerprint
bound_resource_ref
```

The assessment domain is
`agents-os.temporary-worker-responsibility-binding-assessment.v0.1-r18` and
uses the R15 derived-record profile. `bound_resource_ref.resource_kind` is
exactly `TASK` or `RUN` and its complete tuple occurs byte-identically in the
source subject's R7 exact scope. Reason codes are sorted unique NFC strings;
all current inputs share one watermark.

#### 10.1.1 `TemporaryWorkerResponsibilityBindingReducerV0_1R18`

```text
worker class is not TEMPORARY_WORKER -> reject
worker stable ID differs from binding.worker_actor_id -> reject
worker identity RETIRED or COMPROMISED -> INDETERMINATE; deny new use
worker identity NOT_YET_ACTIVE -> NOT_YET_ACTIVE
worker identity SUSPENDED -> SUSPENDED
worker identity EXPIRED -> EXPIRED
worker identity INDETERMINATE -> INDETERMINATE

RESPONSIBILITY_ASSIGNMENT source:
  subject actor_id must equal worker_actor_id
  use exact ResponsibilityAssignmentAssessmentV0_1R16

DELEGATION source:
  subject delegate_actor_id must equal worker_actor_id
  use exact DelegationAssessmentV0_1R16

subject/ref/fingerprint/head/scope mismatch -> INDETERMINATE
bound resource absent from exact source scope -> INDETERMINATE
source NOT_YET_ACTIVE -> NOT_YET_ACTIVE
source SUSPENDED -> SUSPENDED
source REVOKED -> REVOKED
source RENOUNCED -> RENOUNCED
source EXPIRED -> EXPIRED
source SUPERSEDED -> SUPERSEDED
source INDETERMINATE -> INDETERMINATE
worker identity ACTIVE and source assessment ACTIVE -> ACTIVE
```

Only `ACTIVE` supports a Temporary Worker Command. Identity ACTIVE, a matching
resource, or a historical source alone is insufficient. The Assignment or
Delegation remains the sole canonical responsibility fact; this reducer owns
only a rebuildable derived projection.

## 11. Delegation issuance and currentness

Source: R1 Sections 10.3 and 11-12; R2 Section 4; R3-R4; R7 Sections 11-12;
R8 Section 4; and R19 Section 5.

```yaml
DelegationReasonV0_1R19:
  reason_code: TASK_HANDOFF | RUN_EXECUTION | DOMAIN_OPERATION | INCIDENT_RESPONSE | MAINTENANCE
  reason_artifact_ref: ResponsibilityResourceRefV0_1 | null

DelegationGrantRevisionV0_1R19Effective:
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
  reason_code: TASK_HANDOFF | RUN_EXECUTION | DOMAIN_OPERATION | INCIDENT_RESPONSE | MAINTENANCE
  reason_artifact_ref: ResponsibilityResourceRefV0_1 | null
  status: ACTIVE
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

`reason_artifact_ref`, when non-null, has `resource_kind: ARTIFACT_METADATA`
and names an immutable low-disclosure artifact reference. The embedded reason
value is `NOT_STANDALONE`; it conveys no authority and has no independent
writer or fingerprint domain. Inline narrative, secrets, provider output,
private memory, wildcard/future scope, aliases, unknown codes, and the old
`reason` field all reject.

The R19 issuance-intent and R4 final-subject formulas are printed in Section
8.1. The complete
`ResponsibilityScopeV0_1R7` value already carries its own
`canonical_fingerprint`; the Delegation subject has no separate
`responsibility_scope_fingerprint` field. The subject contains no activation
evidence backward ref. Chain maximum is three edges, Actor IDs are unique,
scope/time narrow, depth decrements exactly, and parallel-chain union is
forbidden.

Every edge preserves the exact root responsibility source, names the exact
immediate parent, deterministically narrows scope and time, decrements depth
exactly once, and retains a complete acyclic root-to-target lineage. No edge
may widen scope/time/depth, change lineage root, union parallel chains, or
derive authority from the delegate.

The exact Delegation issuance branches are:

```text
common issuance:
  delegator_actor_id = issued_by_actor_id
  delegator_identity_revision = issued_by_actor_identity_revision
  issuance action names that Actor revision and Principal Binding
  issuance action is F3 COMMITTED and binds the exact issuance intent
  issuer identity and Binding are current at issuer_currentness_event_sequence
  delegator and delegate are distinct ACTIVE Actors
  no self edge, repeated Actor, or lineage cycle

revision CAS:
  revision 1 -> both predecessor fields are null
  revision N greater than 1 -> both predecessor fields are N - 1
  N - 1 is the unique current Delegation head in the transaction

first Jenn-root edge:
  issuer is current Jenn root
  root_direction ref/fingerprint are present and current
  source Assignment ref/fingerprint are null
  action responsibility source is that exact JENN_ROOT_DIRECTION
  remaining_depth = policy.maximum_edges_per_chain - 1

first Assignment-rooted edge:
  source Assignment ref/fingerprint are present
  exact Assignment is current ACTIVE, belongs to issuer, permits redelegation,
    and has max_redelegation_depth greater than zero
  responsibility kind is equal and scope/time are contained
  remaining_depth =
    min(assignment.max_redelegation_depth,
        policy.maximum_edges_per_chain) - 1
  root-direction fields are null unless fixed by that Assignment
  action responsibility source is the exact Assignment

child edge:
  exact parent is current ACTIVE
  parent delegate = child delegator = child issuer
  parent may_redelegate = true and parent remaining_depth greater than zero
  child responsibility kind equals parent kind
  child scope/time are contained by parent
  child remaining_depth = parent remaining_depth - 1
  child preserves the exact root source and names the immediate parent revision
  action responsibility source is the exact parent Delegation

every branch:
  remaining_depth = 0 -> may_redelegate = false
  may_redelegate = false -> no child edge
  scope, time, and depth may only attenuate
```

Missing, extra, stale, non-current, mismatched, cyclic, or branch-incompatible
inputs reject. No implementation may infer a root or parent branch from
ambient relationships.

The following closed non-transferable set always rejects:

```text
Jenn root identity creation, replacement, or recovery
Jenn-only top-level Goal final change, closure, outcome, or reopen
Jenn's authority to revise the Prohibited Behavior List
responsibility outside the delegator's own current responsibility scope
responsibility to redefine this non-transferable list
```

The complete effective Delegation assessment is
`DelegationAssessmentV0_1R16` in Section 18. Its exact fingerprinted ancestry,
activation, transition, and assurance inputs replace the R15 aliases.

Root-to-target ancestry is complete and ordered. The sole complete Delegation
reducer is Section 6.3.

## 12. Binding and Delegation activation evidence

Source: R2 Sections 5-6, R3 Sections 2-4, R4 Sections 4-6, R7 Section 7,
R8 Section 6.4, R15 Section 2.2, R18 Section 4, and R19 Section 3.

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
  stewardship_source: >
    exact R2 inline {kind, source_ref} object
    | exact SyntheticManifestDerivedLifecycleRefV0_1 object
  steward_actor_id: optional
  steward_actor_identity_revision: optional
  steward_principal_binding_ref: optional
  steward_action_ref: AuthenticatedActorActionRefR4Effective | null
  not_before_utc_ms:
  expires_at_utc_ms:
  replay_identity: CanonicalDigestScalarV0_1
  status: ACTIVE
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope
```

Evidence exists after the immutable Binding subject. The exact conditional
field projection is:

| Activation mode/source | Exact `stewardship_source` value | Separate steward fields |
|---|---|---|
| `JENN_ROOT_BOOTSTRAP_DECISION` | R2 inline object with `kind: JENN_ROOT_BOOTSTRAP_DECISION` and `source_ref` naming the exact accepted governance decision | all four schema-known steward fields are present with JSON `null` values |
| `AUTHENTICATED_STEWARD_ACTION` | R2 inline object with `kind: AUTHENTICATED_STEWARD_ACTION` and its exact `source_ref` | all four separate steward fields are required and `steward_action_ref` is the exact authenticated action |
| `SYNTHETIC_M0_FIXTURE` | the exact `SyntheticManifestDerivedLifecycleRefV0_1` for this Binding creation spec, replacing the R2 stewardship-source object | all four schema-known steward fields are present with JSON `null` values; no distinct synthetic action ref exists |

No other shape is accepted. The synthetic derived lifecycle ref must bind the
accepted manifest, manifest assessment, controller spec, exact Binding creation
spec, and derivation replay identity as required by R8. The evidence fingerprint
covers the complete selected source object. Every schema-known conditional
field occupies its fixed position; a branch without a value encodes JSON
`null`. Omitting such a field or encoding a non-null value outside its branch
rejects. Raw proof is forbidden.

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
  status: ACTIVE
  created_at_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

```

Evidence IDs, subject fingerprints, acknowledgements, action refs, replay
identities, CAS, time windows, and Event sequences are all fingerprinted.
The complete effective Binding and Delegation activation assessments are the
R16 schemas in Section 18.

Evidence-stream creation is constrained by R18:

```text
creation_status = ACTIVE_ONLY
Binding derived states = ACTIVE | SUSPENDED | REVOKED | SUPERSEDED
Delegation derived states = ACTIVE | SUSPENDED | REVOKED | RENOUNCED | SUPERSEDED
```

`creation_status` is a contract rule, not a schema field. A new evidence stream
created directly in any non-`ACTIVE` state rejects. Later effective states come
only from accepted current-head and transition reduction.

### 12.1 Canonical activation-evidence RESUME revalidation

```yaml
ActivationEvidenceResumeRevalidationAssessmentV0_1R19:
  revalidation_assessment_id:
  target_kind: BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE
  target_activation_evidence_ref:
  target_activation_evidence_fingerprint:
  current_transition_head_ref:
  current_transition_head_fingerprint:
  target_subject_ref:
  target_subject_fingerprint:
  actor_identity_assessment_ref:
  actor_identity_assessment_fingerprint:
  principal_assessment_ref: optional
  principal_assessment_fingerprint: optional
  authenticator_profile_assessment_ref: optional
  authenticator_profile_assessment_fingerprint: optional
  credential_status_assessment_refs: []
  credential_status_assessment_fingerprints: []
  principal_control_proof_assessment_ref: optional
  principal_control_proof_assessment_fingerprint: optional
  delegation_activation_acknowledgement_ref: optional
  delegation_activation_acknowledgement_fingerprint: optional
  acknowledging_principal_binding_assessment_ref: optional
  acknowledging_principal_binding_assessment_fingerprint: optional
  acknowledgement_action_validity_assessment_ref: optional
  acknowledgement_action_validity_assessment_fingerprint: optional
  source_responsibility_assessment_ref: optional
  source_responsibility_assessment_fingerprint: optional
  ancestor_delegation_assessment_refs: []
  ancestor_delegation_assessment_fingerprints: []
  time_authority_ref:
  assessment: VALID | INVALID | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
  assessed_at_utc_ms:
  canonical_fingerprint: R4FingerprintEnvelope
```

The domain is
`agents-os.activation-evidence-resume-revalidation-assessment.v0.1-r19`.
It uses the R15 derived-record profile; arrays are sorted, paired arrays are
parallel, dependencies share one watermark, and mixed conditional branches,
stale watermarks, unknown fields, missing fingerprints, and normalized-key
collisions reject.

`ActivationEvidenceResumeRevalidationReducerV0_1R19` is total:

```text
target evidence/ref/fingerprint does not name the unique current suspended
  activation-evidence stream -> INVALID
current transition head is not the accepted SUSPEND head named by the RESUME
  expected_target_head -> INVALID
fork, CAS gap, missing coverage, stale watermark, time uncertainty, action
  assurance failure, or ref/fingerprint mismatch -> INDETERMINATE
actor identity not ACTIVE, or trusted time outside a required current validity
  window -> INVALID when proven, otherwise INDETERMINATE

BINDING_ACTIVATION_EVIDENCE:
  principal, Profile, every credential, and a fresh principal-control proof
    ref/fingerprint are required
  Delegation-only fields and arrays are null/empty
  proof is VERIFIED, assessed after the effective SUSPEND Event, current at the
    common watermark, and binds the exact Binding, Actor, Principal, Profile,
    verifier revision, and challenge fingerprint
  every exact dependency is current and ACTIVE -> VALID

DELEGATION_ACTIVATION_EVIDENCE:
  exact immutable acknowledgement and fingerprint are required
  acknowledging Principal Binding is required and ACTIVE
  exact historical action-validity assessment for the acknowledgement command
    envelope is required and current_assurance is CONFIRMED
  source responsibility and complete ancestor arrays are required as applicable
  Binding-only Profile/credential/proof fields are null/empty
  acknowledgement binds the exact current Delegation subject, delegate Actor,
    committed command envelope, activation mode, and replay identity
  delegate identity, acknowledging Binding, source responsibility, and every
    ancestor are current at the common watermark -> VALID
```

A routine session end, Binding expiry/replacement, or credential rotation does
not retroactively invalidate the acknowledgement. Only its exact historical
action assurance and CompromiseImpact projection can make it `CHALLENGED`,
`INVALIDATED`, or `INDETERMINATE`. Neither branch consumes the effective
Binding or Delegation assessment whose activation result it helps resume;
`INVALID` and `INDETERMINATE` both reject RESUME.

The exact activation assurance projection is:

| Effective object | Exact mode/source | Action ref source | Action fingerprint source | Role |
|---|---|---|---|---|
| Binding activation | `JENN_ROOT_BOOTSTRAP_DECISION` | `stewardship_source.source_ref` | canonical fingerprint of that exact accepted governance decision | `BINDING_ACTIVATION` |
| Binding activation | `AUTHENTICATED_STEWARD_ACTION` | `steward_action_ref.action_ref_id` | `steward_action_ref.canonical_action_ref_fingerprint` | `BINDING_ACTIVATION` |
| Binding activation | `SYNTHETIC_M0_FIXTURE` | none | none | required manifest `SYNTHETIC_MANIFEST_ACCEPT` assurance is transitive |
| Delegation activation | `EXPLICIT_ACK` | `acknowledgement_ref.command_envelope_ref` | `acknowledgement_ref.command_envelope_fingerprint` | `DELEGATION_ACTIVATION` |
| Delegation activation | `WORKER_ASSIGNMENT_HANDSHAKE` | `acknowledgement_ref.command_envelope_ref` | `acknowledgement_ref.command_envelope_fingerprint` | `DELEGATION_ACTIVATION` |

The synthetic row is selected before the Binding stewardship-source rows; it
never inherits a second activation action from a bootstrap or steward field.
Bootstrap without a resolvable accepted decision fingerprint, authenticated
activation without the exact steward action, and Delegation activation without
the exact committed command envelope are `INDETERMINATE`. The acknowledgement
ID, Principal Binding, replay ID, evidence fingerprint, or caller label cannot
substitute for the listed action source.

`WORKER_ASSIGNMENT_HANDSHAKE` additionally requires the future F3 closed
payload to bind that exact activation mode. Until F3 supplies it, assessment is
`INDETERMINATE`; this materialization does not invent the F3 payload.

## 13. F3-owned authentication and Command boundary

Source: R1 Sections 14-15 as narrowed by R2 Section 8, R15 Section 2, R18
Section 5, and R20 Section 2.

The following are ownership placeholders only:

| F3-owned surface | F2 requirement |
|---|---|
| `CommandTypeDefinition` | F3 must close its registry, version, payload, target, and domain-gate contract |
| `CanonicalCommand` | F3 must close canonical bytes, identity, replay, expiry, target, and payload binding |
| `AuthenticatedCommandContext` | F3 must close the committed intake context and exact responsibility attribution |

Their earlier R1 shapes are historical incomplete interfaces. They are not
effective F2 schemas, are not printed as implementable field lists, receive no
F2 fingerprint domain, and cannot be implemented before F3 acceptance.

F2 retains only the authentication assertion value and its canonical derived
assessment:

```yaml
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

`AuthenticationAssertionValue` is an external authentication value with no
standalone F2 record fingerprint. R15 owns the canonical Authentication
assessment shown above. Only
`AUTHENTICATED` enters responsibility attribution and the single prohibited
line. Proof bytes, credentials, secrets, cookies, private memory, and provider
raw output are never stored.

An Actor assessment of `NOT_YET_ACTIVE` cannot produce `AUTHENTICATED`. With
complete proven pre-start evidence the result is `REJECTED`; missing, stale,
forked, or time-uncertain evidence is `INDETERMINATE`. Neither result supports
operational use.

F4 must admit an effect only against exact identity, responsibility, permit,
host, and fence evidence supplied by the owning accepted contracts. F2
supplies only the identity/currentness/responsibility properties defined here;
it does not define the F4 permit schema, host transport, fence mechanism,
cryptographic profile, or effect transaction. Missing, stale, conflicting, or
indeterminate F2 evidence cannot be converted by F4 into effect admission.

## 14. Mutation intent, action, replay, and transitions

Source: R7 Sections 2.3 and 3.3; R8 Sections 2-3; R9; R15 Section 3; and R20
Sections 4-6.

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

MutationIntent validity and Event binding are total:

```text
intent_revision = 1
effective_at_event_sequence = expected_ledger_head_event_sequence + 1
issued_at_utc_ms < expires_at_utc_ms
target_kind exactly matches mutation_kind
target_current_ref and target_current_fingerprint are both null only for CREATE
expected_target_head is all-null for CREATE
otherwise expected_target_head is the exact unique current target head
mutation_body_fingerprint equals the exact mutation-kind projection
authority basis, current assessments, target head, and intent share one
  expected-ledger-head watermark
```

The Event at effective_at_event_sequence is both the committed F3 intake Event
referenced by the action interface and the F2 lifecycle or transition Event.
No intervening Event is admitted. Missing, extra, stale, forked, mismatched, or
non-contiguous values reject before action attribution.

The one complete effective governed transition schema is printed in Section 19
with the R9 authority basis. Assignment transitions allow Jenn only. Safety
transitions never auto-reverse.

For `GOVERNED_STATE_TRANSITION`, the mutation-kind-specific known object uses
the transition-fact semantic fields through `expected_target_head`, followed
in exact order by:

```text
resume_revalidation_assessment_ref
resume_revalidation_assessment_fingerprint
reason_codes
```

The two revalidation positions are required and name an exact `VALID` R19
assessment only for `RESUME` targeting Binding or Delegation activation
evidence; for every other target/transition tuple both are JSON null. They are
hashed into the mutation body before MutationIntent construction. The exact
order is revalidation -> body -> body fingerprint -> intent -> committed
action -> LifecycleActionRef -> replay identity -> final fact -> Event/CAS.
Missing, extra, substituted, or non-null-outside-branch values reject.

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

Source: R8 Sections 6.1, 6.2, 6.3, and 6.4; R9 Sections 2 and 3.4; R10
Sections 3.3, 4, and 5; R11 Sections 2, 3, and 4; R12 Sections 2, 3, and 4;
R13 Sections 2, 3, and 4; R14 Sections 1, 2, and 3; and R20 Sections 3-4.

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

Source: R1 Sections 2 and 16.

F2 defines identity, responsibility, provenance, and derived currentness. It
does not define permissions. Every authenticated action still passes the one
canonical Prohibited Behavior List interface. Relationship, responsibility,
delegation, stewardship, authentication, and capability cannot waive or expand
that boundary. Unknown boundary revision or evaluation result stops the action.

## 18. Complete assurance-bound assessment catalogue

Source: R7 Sections 5-7, R15 Section 3, R16 Section 3, R18, and R19 Sections
2-4. These are the complete effective schemas; no earlier assessment alias
remains effective.

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
| Binding activation | the exact conditional Section 12 activation source plus activation-evidence transition actions; synthetic mode uses manifest assurance transitively and has no invented activation action |
| Effective Binding | issuance and Binding transition actions |
| Assignment | issuance and Assignment transition actions |
| Delegation activation | exact acknowledgement command envelope plus activation-evidence transition actions |
| Delegation | issuance and Delegation transition actions |
| Synthetic manifest | create, accept, and effective revoke action when present |
| Temporary Worker responsibility binding | no direct action role; exact Actor and Assignment/Delegation assessments are transitive inputs |

Every role set is derived from a complete ledger index through the assessment
watermark. Missing coverage, missing role, extra role, fingerprint mismatch, or
non-confirmed enabling assurance fails closed. Safety transition effects remain
safe and never auto-restore.

### 18.1 Common R16 reducer prelude

The R16 Section 3.4 prelude applies to exactly these four reducers printed in
Sections 18.2 through 18.5:

```text
AuthenticatorProfileEffectiveReducer
PrincipalEffectiveReducer
BindingActivationEffectiveReducer
DelegationActivationEffectiveReducer
```

`BindingEffectiveCurrentReducer` in Section 6.1,
`ResponsibilityAssignmentEffectiveReducer` in Section 6.2, and
`SyntheticM0ManifestAssessmentReducer` in Section 20.1 each print the same
required composition inline so every sole indexed definition is complete
without an implicit cross-reference.

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

Source: R2 Section 5, R3 Sections 3-5, R4 Section 5, R7 Section 7.2, R16
Sections 3.2-3.4, R18 Section 4, and R19 Section 3.

```text
complete evidence stream proves no active evidence, or an effective REVOKE or
  SUSPEND is present without a later valid RESUME -> NOT_ACTIVATED
missing/forked evidence head or CAS, stale or replayed evidence, invalid
  transition fact, incomplete action-role coverage, non-confirmed enabling
  assurance, target Binding mismatch, proof/stewardship mismatch, time-window
  mismatch, or any ref/fingerprint mismatch -> INDETERMINATE
ordinary mode missing or substituting the exact R18 bootstrap/steward action
  projection -> INDETERMINATE
synthetic mode containing an invented BINDING_ACTIVATION action, or missing
  exact transitive manifest create/accept assurance -> INDETERMINATE
accepted RESUME fact missing or mismatching the exact R19 revalidation
  ref/fingerprint, or named assessment not VALID at the same watermark
  -> INDETERMINATE
exact current evidence is REVOKED or validly SUSPENDED -> NOT_ACTIVATED
exact current ACTIVE evidence matches the immutable Binding subject, exact
  proof and stewardship inputs, and any RESUME binds the exact fresh current
  proof through its VALID R19 revalidation; replay identity, time, transition
  facts, fingerprints, watermark, and all enabling assurance are CONFIRMED
  -> ACTIVATED
```

This reducer owns only `binding_activation_projection`. It never decides
whether the Actor, Principal, Profile, credentials, administrative Binding
state, or Binding time window permits a new Command.

### 18.5 `DelegationActivationEffectiveReducer`

Source: R2 Section 6, R3 Sections 2 and 5, R4 Section 6, R7 Section 7.4, R16
Sections 3.2-3.4, R18 Section 4, and R19 Section 3.

```text
complete evidence stream proves no active evidence, or an effective REVOKE,
  RENOUNCE, or SUSPEND is present without a later valid RESUME -> NOT_ACTIVATED
missing/forked evidence head or CAS, stale or replayed evidence, invalid
  transition fact, incomplete action-role coverage, non-confirmed enabling
  assurance, delegation-subject mismatch, acknowledgement mismatch, time-window
  mismatch, or any ref/fingerprint mismatch -> INDETERMINATE
acknowledgement ID or other substitute used instead of the exact R18 committed
  command-envelope ref/fingerprint -> INDETERMINATE
WORKER_ASSIGNMENT_HANDSHAKE without the future F3 exact mode binding
  -> INDETERMINATE
accepted RESUME fact missing or mismatching the exact R19 revalidation
  ref/fingerprint, or named assessment not VALID at the same watermark
  -> INDETERMINATE
exact current evidence is REVOKED, validly RENOUNCED, or validly SUSPENDED
  -> NOT_ACTIVATED
exact current ACTIVE evidence matches the immutable Delegation subject, exact
  R3 acknowledgement, and any RESUME binds its historical action assurance,
  current delegate/Binding/source/ancestor inputs through the exact VALID R19
  revalidation; replay identity, time, transition facts, fingerprints,
  watermark, and every enabling assurance are CONFIRMED -> ACTIVATED
```

This reducer owns only `delegation_activation_projection`. It does not decide
whether the responsibility source, lineage, scope, actors, or time window make
the Delegation effective.

## 19. Complete governed transition and assurance schemas

Source: R8 Sections 3 and 5; R9 Sections 4-5; R15 Section 5; R16 Section 3;
R17 Section 2; R18 Section 4; R19 Section 3; and R20 Sections 4.2 and 5.

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
  resume_revalidation_assessment_ref: optional
  resume_revalidation_assessment_fingerprint: optional
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
  incident_basis_ref:
  selection_basis_event_sequence:
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

In the governed-transition known-object order, the two R19 revalidation fields
occur immediately after `expected_target_head`. Both are required and bind the
exact `VALID ActivationEvidenceResumeRevalidationAssessmentV0_1R19` for a
`RESUME` targeting either activation-evidence kind. For every other
target/transition tuple both are JSON null. The fact recomputes the identical
mutation-body values, intent, action, replay identity, Event, and current-head
CAS; omission, substitution, or a non-null value outside the closed branch
rejects.

Impact streams sort by stream ID then revision. Binding arrays sort by action
role enum ordinal, action ref, then action fingerprint. Historical assessment
and input-set coverage equal the containing assessment watermark. Action
classification uses the exclusive R15 order; unknown, recursive, or non-F2
targets reject.

### 19.1 Closed assurance-role enum

`ActionAssuranceRoleV0_1R17` is printed exactly once in Section 8. Its 43
entries and their printed order are the closed canonical enum. Aliases, case
folding, localization, numeric codes, reordering, omissions, duplicates, and
extensions reject.

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
| Binding activation source | R18 bootstrap decision or authenticated steward action | BINDING_ACTIVATION |
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
| Delegation activation acknowledgement command envelope | R18 `EXPLICIT_ACK` or `WORKER_ASSIGNMENT_HANDSHAKE` | DELEGATION_ACTIVATION |
| Delegation-activation transition fact | SUSPEND | DELEGATION_ACTIVATION_TRANSITION_SUSPEND |
| Delegation-activation transition fact | RESUME | DELEGATION_ACTIVATION_TRANSITION_RESUME |
| Delegation-activation transition fact | REVOKE | DELEGATION_ACTIVATION_TRANSITION_REVOKE |
| Delegation-activation transition fact | RENOUNCE | DELEGATION_ACTIVATION_TRANSITION_RENOUNCE |
| Synthetic manifest | creation | SYNTHETIC_MANIFEST_CREATE |
| Manifest activation revision | ACCEPT | SYNTHETIC_MANIFEST_ACCEPT |
| Manifest activation revision | REVOKE | SYNTHETIC_MANIFEST_REVOKE |

Exactly one tuple matches each admitted direct assurance action. Zero or
multiple matches reject. `ActionAssuranceCompleteSetReducer` derives each
complete set from the following closed branches:

```text
Actor/Profile/Principal:
  contiguous root-to-current revision chain and every accepted lifecycle action
Binding/Assignment/Delegation:
  exact issuance plus every accepted target transition fact through watermark
ordinary Binding activation:
  exact R18 Section 4.1 BINDING_ACTIVATION source plus every accepted
  Binding-activation-evidence transition through the assessment watermark
synthetic M0 Binding activation:
  no separate BINDING_ACTIVATION action; exact SYNTHETIC_MANIFEST_CREATE and
  SYNTHETIC_MANIFEST_ACCEPT assurance consumed transitively plus every accepted
  Binding-activation-evidence transition through the assessment watermark
Delegation activation:
  exact R18 Section 4.1 acknowledgement command envelope as DELEGATION_ACTIVATION
  plus every accepted Delegation-activation-evidence transition through the
  assessment watermark
synthetic M0 manifest:
  exact SYNTHETIC_MANIFEST_CREATE plus contiguous activation revisions through
  watermark using SYNTHETIC_MANIFEST_ACCEPT or SYNTHETIC_MANIFEST_REVOKE
```

Repeated roles are allowed only for different exact action refs. Caller labels
and ordering are ignored and recomputed from the closed indexes.

For the two activation roles, the row identifies the admitted action class but
Section 12 exclusively defines the action ref and fingerprint fields. A
bootstrap source, steward action, acknowledgement, command envelope, replay
identity, or evidence object cannot be substituted for another.

## 20. Complete synthetic M0 schemas

Source: R8 Sections 6.1, 6.2, 6.3, and 6.4; R9 Sections 2 and 3.4; R10
Sections 3.3, 4, and 5; R11 Sections 2, 3, and 4; R12 Sections 2, 3, and 4;
R13 Sections 2, 3, and 4; R14 Sections 1, 2, and 3; R16 Section 3.2; R17
Section 2; and R20 Sections 3-4.

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

SyntheticM0AuthenticatorProfileCreationSpecV0_1R20:
  profile_id:
  profile_revision: 1
  expected_previous_profile_revision: null
  supersedes_profile_revision: null
  transition_kind: CREATE
  source_status: null
  status: ACTIVE
  proof_kind: SYNTHETIC_FIXTURE
  supported_principal_classes:
    - SYNTHETIC_TEST_PRINCIPAL
  supported_environments:
    - SYNTHETIC_TEST
  verifier_id:
  verifier_revision: 1
  trust_anchor_refs: []
  assertion_max_age_ms: duration_milliseconds
  clock_policy_ref:
  replay_policy_ref:
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticM0PrincipalCreationSpecV0_1R20:
  principal_id:
  principal_revision: 1
  expected_previous_principal_revision: null
  supersedes_principal_revision: null
  transition_kind: CREATE
  source_status: null
  principal_class: SYNTHETIC_TEST_PRINCIPAL
  environment: SYNTHETIC_TEST
  authenticator_profile_creation_spec_ref:
  authenticator_profile_creation_spec_fingerprint:
  credential_handle_refs: []
  status: ACTIVE
  canonical_fingerprint: R4FingerprintEnvelope

SyntheticM0PrincipalProvisioningManifestV0_1R8Effective:
  manifest_id:
  manifest_revision: 1
  workspace_fixture_id:
  controller_spec: SyntheticM0ControllerSpecV0_1
  controller_spec_fingerprint:
  synthetic_profile_creation_specs: SyntheticM0AuthenticatorProfileCreationSpecV0_1R20[]
  synthetic_principal_creation_specs: SyntheticM0PrincipalCreationSpecV0_1R20[]
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

Both `synthetic_profile_creation_specs` and
`synthetic_principal_creation_specs` are non-empty. Profile specs sort by
profile_id normalized UTF-8 bytes and reject duplicate profile_id values or
fingerprints. Principal specs sort by principal_id normalized UTF-8 bytes and
reject duplicate principal_id values or fingerprints. Each Profile spec uses
the displayed singleton-array order; trust_anchor_refs sort by exact normalized
stable ref and reject duplicates; verifier_id and verifier_revision are
byte-identical to the enclosing controller. Each Principal spec names one exact
same-manifest Profile spec; credential_handle_refs are exact opaque non-secret
refs sorted by normalized UTF-8 bytes, duplicate-free, and equal the handles
used by that Principal from deterministic_credential_handle_refs. Every
permitted Binding names one exact same-manifest Principal and Profile and the
exact pre-existing ELIGIBLE Actor required by R12-R14.

At ACCEPT, every creation-spec field is byte-identical in the final subject.
The excluded fields have these only valid projections:

```text
Profile:
  lifecycle_controller_ref = exact same-manifest SyntheticM0ControllerRefV0_1
  credential_status_provider_ref = exact stable ref of that same controller
  profile_steward_ref = exact same-manifest SYNTHETIC_M0_STEWARD ref
  mutation_body_fingerprint = exact Profile creation-spec fingerprint
  mutation_intent_ref/fingerprint = exact manifest activation intent
  lifecycle_action_ref = exact same-spec SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity = that derived ref's derivation_replay_identity
  created_at_event_sequence = manifest ACCEPT Event
  canonical_fingerprint = effective final Profile subject fingerprint

Principal:
  authenticator_profile_ref = exact revision-1 Profile materialized from the
    named same-manifest Profile creation spec
  provisioning_source_ref = exact same-spec SyntheticManifestDerivedLifecycleRefV0_1
  lifecycle_controller_ref = exact controller ref of that materialized Profile
  mutation_body_fingerprint = exact Principal creation-spec fingerprint
  mutation_intent_ref/fingerprint = exact manifest activation intent
  lifecycle_action_ref = exact same-spec SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity = that derived ref's derivation_replay_identity
  created_at_event_sequence = manifest ACCEPT Event
  canonical_fingerprint = effective final Principal subject fingerprint
```

Extra fields, caller-supplied or external controller/steward/Profile/
provisioning/action/intent/replay/Event/final-subject refs, mismatch, partial
materialization, or different order rejects the whole atomic materialization.

The exact acyclic order is:

```text
typed Profile and Principal specs
-> Binding precommit and Binding spec
-> manifest body and fingerprint
-> creation and activation decisions
-> ACTIVE manifest assessment
-> derived lifecycle refs
-> final Profile, Principal, and Binding in one Event
```

The spec fingerprint formulas and derivation replay formula are printed in
Section 8.1. No creation spec contains its manifest, assessment, derived ref,
Event, or final subject fingerprint.

### 20.1 `SyntheticM0ManifestAssessmentReducer`

Source: R8 Section 6.3, R15 Sections 5.2-5.3, R16 Sections 3.2-3.4, and R17
Section 2.3.

```text
missing activation coverage, missing current head, fork, non-contiguous
  revision, CAS gap, manifest ref/fingerprint mismatch, Jenn decision mismatch,
  lifecycle-action mismatch, mutation-intent mismatch, replay mismatch,
  incomplete/extra/duplicated action-role coverage, stale or unequal watermark,
  or any canonical fingerprint conflict -> INDETERMINATE, except that an already
  proven effective manifest REVOKE remains REVOKED
assurance role SYNTHETIC_MANIFEST_CREATE or SYNTHETIC_MANIFEST_ACCEPT
  INVALIDATED -> REVOKED prospectively;
  every derived subject is non-active
assurance role SYNTHETIC_MANIFEST_CREATE or SYNTHETIC_MANIFEST_ACCEPT
  CHALLENGED or INDETERMINATE
  -> INDETERMINATE; every derived subject is non-active, except that an already
  proven effective manifest REVOKE remains REVOKED
all required SYNTHETIC_MANIFEST_CREATE and SYNTHETIC_MANIFEST_ACCEPT assurance
  CONFIRMED -> continue
proven effective later contiguous current activation head REVOKE -> REVOKED;
  its SYNTHETIC_MANIFEST_REVOKE safety effect remains effective even when its
  assurance is CHALLENGED or INVALIDATED and only explicit valid compensation
  may change it
unique contiguous current activation head is ACCEPT, all derived Jenn-decision
  equalities and fingerprints match, and all required
  SYNTHETIC_MANIFEST_CREATE and SYNTHETIC_MANIFEST_ACCEPT assurance is
  CONFIRMED -> ACTIVE
```

Revision 1 must be `ACCEPT`; only a later contiguous Jenn revision may
`REVOKE`; revocation is terminal. The manifest owns the controller, so no
second controller current-state stream exists. Only `ACTIVE` supports derived
synthetic subjects or controller currentness.

All subject specs and ref/fingerprint arrays use the exact R11 Sections 2 and
3, R12 Sections 2, 3, and 4, R13 Sections 2, 3, and 4, and R14 Section 2 closed positive
reference sets. Synthetic acceptance is atomic, M0-only, and cannot contain a
real secret, active Jenn credential, production Principal, or active host
identity.

## 21. Exact domain and source index

This index is generated from the source-first v15 inventory. It covers every
effective top-level schema, external interface, embedded value, canonical
profile, and reducer printed by v15. `NOT_STANDALONE` means R1-R20 defines no
independent F2 record fingerprint for that surface; v15 does not invent one.

| Exact surface | Kind | Exact domain or classification | Authoritative source | Printed section |
|---|---|---|---|---|
| `SyntheticM0ManifestActivationBodyV0_1R9` | mutation body | `NOT_STANDALONE` | R9 2.1 | 2 |
| `AuthenticatorProfileRevisionR9Effective` | subject/policy revision | `agents-os.authenticator-profile-revision.v0.1-r8` | R7 5.2 + R7 5.3 + R8 2.1 + R8 2.2 + R8 2.3 + R8 2.4 + R9 5.1 + R9 5.2 | 3 |
| `PrincipalRevisionR9Effective` | subject/policy revision | `agents-os.principal-revision.v0.1-r8` | R7 6.1 + R7 6.2 + R8 2.1 + R8 2.2 + R8 2.3 + R8 2.4 + R9 5.1 | 3 |
| `BindingIssuanceInputSnapshotV0_1R10` | schema | `agents-os.binding-issuance-input-snapshot.v0.1-r10` | R10 3 + R20 6 | 3 |
| `SyntheticBindingPrecommitInputV0_1R11` | schema | `agents-os.synthetic-binding-precommit-input.v0.1-r11` | R11 2 + R12 2 + R20 6 | 3 |
| `SyntheticM0ActorEligibilityAssessmentV0_1R13` | assessment | `agents-os.synthetic-m0-actor-eligibility-assessment.v0.1-r13` | R13 2 + R14 2 | 3 |
| `ActorPrincipalBindingRevisionR10Effective` | subject/policy revision | `agents-os.actor-principal-binding-revision.v0.1-r9` | R1 7.4 + R7 7.1 + R9 3.2 + R9 3.3 + R10 4 + R11 2 + R11 3 + R12 2 + R12 3 + R12 4 + R13 2 + R13 3 + R13 4 + R14 1 + R14 2 + R14 3 + R20 6 | 3 |
| `ActorIdentityRevisionV0_1R8` | subject/policy revision | `agents-os.actor-identity-revision.v0.1-r8` | R1 5.2 + R8 7.1 + R8 7.2 + R8 7.3 + R16 2.3 + R18 2.1 + R19 2 | 3 |
| `JennRootGovernanceAuthorityRefV0_1R8` | reference/interface | `agents-os.jenn-root-governance-authority-ref.v0.1-r8` | R8 3.1 | 4 |
| `TransitionAuthorityBasisV0_1R9` | schema | `agents-os.transition-authority-basis.v0.1-r9` | R8 3.1 + R9 5 + R20 5 | 4 |
| `R4FingerprintEnvelope` | value type | `NOT_STANDALONE` | R4 2 | 8 |
| `CanonicalDigestScalarV0_1` | value type | `NOT_STANDALONE` | R5 2 | 8 |
| `F2CanonicalScalarProfileV0_1` | canonical profile | `NOT_STANDALONE` | R7 2.2 + R7 2.3 + R20 6 | 8 |
| `F2CanonicalDerivedRecordProfileV0_1R15` | canonical profile | `NOT_STANDALONE` | R15 2.1 | 8 |
| `BindingScopeContextV0_1` | scope/value | `NOT_STANDALONE` | R5 4.1 + R5 4.2 + R5 4.3 | 8 |
| `BindingScopeV0_1` | scope/value | `agents-os.binding-scope.v0.1` | R4 3 + R5 4.3 | 8 |
| `IdentityValidityWindowV0_1` | schema | `agents-os.identity-validity-window.v0.1` | R7 4.1 | 8 |
| `LifecycleControllerRefV0_1` | reference/interface | `agents-os.lifecycle-controller-ref.v0.1` | R7 5.1 | 8 |
| `DelegationPolicyRevision` | subject/policy revision | `NOT_STANDALONE` | R1 11.3 | 8 |
| `ActionAssuranceRoleV0_1R17` | value type | `NOT_STANDALONE` | R17 2 | 8 |
| `ActorIdentityAssessmentV0_1R16` | assessment | `agents-os.actor-identity-assessment.v0.1-r16` | R16 3.2 + R17 2 + R18 2 + R19 2 | 9 |
| `ActorCreateStewardshipTargetSpecV0_1R16` | embedded spec | `agents-os.actor-create-stewardship-target-spec.v0.1-r16` | R16 2 + R18 2 | 9 |
| `ActorCreateStewardshipAssessmentV0_1R16` | assessment | `agents-os.actor-create-stewardship-assessment.v0.1-r16` | R16 2 | 9 |
| `ActorCreateStewardAuthorityBasisV0_1R16` | schema | `agents-os.actor-create-steward-authority-basis.v0.1-r16` | R16 2 | 9 |
| `ActorGeneralTransitionAuthorityBasisV0_1R16` | schema | `agents-os.actor-general-transition-authority-basis.v0.1-r16` | R8 7.1 + R16 2.3 + R19 4 | 9 |
| `TemporaryWorkerStewardshipScopeAssessmentV0_1R19` | assessment | `agents-os.temporary-worker-stewardship-scope-assessment.v0.1-r19` | R19 4 | 9 |
| `IdentityStewardshipAssessmentV0_1R19` | assessment | `agents-os.identity-stewardship-assessment.v0.1-r19` | R15 4 + R18 2 + R19 4 | 9 |
| `IdentityRecoveryEvidenceV0_1R15` | evidence | `agents-os.identity-recovery-evidence.v0.1-r15` | R2 7.2 + R2 9 + R15 2.2 + R15 2.4 + R20 4.3 | 9 |
| `ResponsibilityResourceRefV0_1` | reference/interface | `NOT_STANDALONE` | R7 10.1 | 10 |
| `ResponsibilityScopeV0_1R7` | scope/value | `agents-os.responsibility-scope.v0.1-r7` | R7 10.2 | 10 |
| `ResponsibilityAssignmentRevisionV0_1R15` | subject/policy revision | `agents-os.responsibility-assignment-revision.v0.1-r15` | R15 3 + R20 6 | 10 |
| `TemporaryWorkerResponsibilityBindingRefV0_1R18` | embedded derived ref | `agents-os.temporary-worker-responsibility-binding-ref.v0.1-r18` | R18 3 | 10 |
| `TemporaryWorkerResponsibilityBindingAssessmentV0_1R18` | assessment | `agents-os.temporary-worker-responsibility-binding-assessment.v0.1-r18` | R18 3.2 + R18 3.3 + R19 2.3 | 10 |
| `DelegationReasonV0_1R19` | embedded value | `NOT_STANDALONE` | R19 5 | 11 |
| `DelegationGrantRevisionV0_1R19Effective` | subject/policy revision | `agents-os.delegation-grant-subject.v0.1-r4` | R1 11.1 + R1 11.2 + R1 11.4 + R2 4 + R3 5.2 + R3 5.3 + R4 7 + R7 10.2 + R7 11.2 + R7 12.2 + R19 5.1 + R19 5.2 | 11 |
| `AuthenticatedActorActionRefR4Effective` | reference/interface | `agents-os.authenticated-actor-action-ref.v0.1` | R2 2 + R4 4.2 | 12 |
| `DelegationActivationAcknowledgementRefR4Effective` | reference/interface | `agents-os.delegation-activation-acknowledgement-ref.v0.1` | R3 2 + R4 4.3 | 12 |
| `PrincipalControlProofAssessmentRefV0_1R15` | assessment | `agents-os.principal-control-proof-assessment-ref.v0.1-r15` | R2 5 + R4 4.1 + R15 2.2 | 12 |
| `BindingActivationEvidenceR15Effective` | evidence | `agents-os.binding-activation-evidence.v0.1-r15` | R2 5 + R3 3 + R4 2 + R4 5.1 + R4 5.2 + R8 6.4 + R15 2.2 + R18 4.1 + R18 4.2 + R18 4.3 | 12 |
| `DelegationActivationEvidenceR15Effective` | evidence | `agents-os.delegation-activation-evidence.v0.1-r15` | R2 6 + R3 2 + R3 4 + R4 6.1 + R4 6.2 + R15 2.2 + R18 4.1 + R18 4.2 + R18 4.3 | 12 |
| `ActivationEvidenceResumeRevalidationAssessmentV0_1R19` | assessment | `agents-os.activation-evidence-resume-revalidation-assessment.v0.1-r19` | R19 3 | 12 |
| `AuthenticationAssertionValue` | external command/auth interface | `NOT_STANDALONE` | R1 14.2 | 13 |
| `AuthenticationAssessmentV0_1R15` | assessment | `agents-os.authentication-assessment.v0.1-r15` | R1 14.3 + R15 2.2 + R15 2.4 + R19 2.3 | 13 |
| `MutationIntentV0_1R17Effective` | intent | `agents-os.mutation-intent.v0.1` | R7 2.3 + R7 3.3 + R8 2.1 + R9 2.1 + R9 3.1 + R15 3.1 | 14 |
| `LifecycleActionRefV0_1R8` | reference/interface | `agents-os.lifecycle-action-ref.v0.1-r8` | R8 2.3 | 14 |
| `AuthenticatorProfileAssessmentV0_1R16` | assessment | `agents-os.authenticator-profile-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `CredentialHandleStatusAssessmentRefV0_1` | assessment ref | `agents-os.credential-handle-status-assessment-ref.v0.1` | R7 6.3 | 18 |
| `PrincipalAssessmentV0_1R16` | assessment | `agents-os.principal-assessment.v0.1-r16` | R16 3.2 + R17 2 | 18 |
| `BindingActivationAssessmentV0_1R16` | assessment | `agents-os.binding-activation-assessment.v0.1-r16` | R16 3.2 + R17 2.1 + R17 2.3 + R18 4.1 + R18 4.2 + R19 3 | 18 |
| `ActorPrincipalBindingAssessmentV0_1R16` | assessment | `agents-os.actor-principal-binding-assessment.v0.1-r16` | R16 3.2 + R17 2.1 + R17 2.3 + R19 2.3 | 18 |
| `ResponsibilityAssignmentAssessmentV0_1R16` | assessment | `agents-os.responsibility-assignment-assessment.v0.1-r16` | R16 3.2 + R17 2.1 + R17 2.3 + R19 2.3 | 18 |
| `DelegationActivationAssessmentV0_1R16` | assessment | `agents-os.delegation-activation-assessment.v0.1-r16` | R16 3.2 + R17 2.1 + R17 2.3 + R18 4.1 + R18 4.2 + R19 3 | 18 |
| `DelegationAssessmentV0_1R16` | assessment | `agents-os.delegation-assessment.v0.1-r16` | R16 3.2 + R17 2.1 + R17 2.3 + R19 2.3 | 18 |
| `GovernedStateTransitionFactV0_1R9Effective` | fact | `agents-os.governed-state-transition-fact.v0.1-r8` | R8 3.3 + R9 5 + R19 3 | 19 |
| `CompromiseImpactFactV0_1R9Effective` | fact | `agents-os.compromise-impact-fact.v0.1-r8` | R8 5.1 + R9 4 + R20 4.2 + R20 5.2 | 19 |
| `HistoricalImpactInputSetV0_1` | input set | `agents-os.historical-impact-input-set.v0.1` | R8 5.2 | 19 |
| `HistoricalActionValidityAssessmentV0_1R16` | assessment | `agents-os.historical-action-validity-assessment.v0.1-r16` | R16 3.1 | 19 |
| `ActionAssuranceBindingV0_1R17` | embedded assurance | `agents-os.action-assurance-binding.v0.1-r17` | R17 2 | 19 |
| `SyntheticM0ControllerSpecV0_1` | embedded spec | `agents-os.synthetic-m0-controller-spec.v0.1` | R8 6.1 | 20 |
| `SyntheticM0AuthenticatorProfileCreationSpecV0_1R20` | embedded spec | `agents-os.synthetic-m0-authenticator-profile-creation-spec.v0.1-r20` | R20 3.1 | 20 |
| `SyntheticM0PrincipalCreationSpecV0_1R20` | embedded spec | `agents-os.synthetic-m0-principal-creation-spec.v0.1-r20` | R20 3.2 | 20 |
| `SyntheticM0PrincipalProvisioningManifestV0_1R8Effective` | schema | `agents-os.synthetic-m0-principal-provisioning-manifest.v0.1-r8` | R8 6.2 + R10 5 + R11 2 + R11 3 + R12 2 + R12 3 + R12 4 + R13 2 + R13 3 + R13 4 + R14 1 + R14 2 + R14 3 + R20 3.3 | 20 |
| `SyntheticM0ControllerRefV0_1` | reference/interface | `agents-os.synthetic-m0-controller-ref.v0.1` | R8 6.4 + R12 4 | 20 |
| `SyntheticManifestDerivedLifecycleRefV0_1` | reference/interface | `agents-os.synthetic-manifest-derived-lifecycle-ref.v0.1` | R8 6.4 + R11 3 + R12 3 + R13 3 + R14 2 + R20 4.1 | 20 |
| `SyntheticM0ManifestActivationRevisionV0_1R9` | subject/policy revision | `agents-os.synthetic-m0-manifest-activation-revision.v0.1` | R8 6.3 + R9 2 | 20 |
| `SyntheticM0ManifestAssessmentV0_1R16` | assessment | `agents-os.synthetic-m0-manifest-assessment.v0.1-r16` | R8 6.3 + R16 3.2 + R17 2 | 20 |

The F3-owned placeholders `CommandTypeDefinition`, `CanonicalCommand`, and
`AuthenticatedCommandContext` are intentionally excluded from this schema
inventory because Section 13 prints no effective field schema for them.

The reducer index is exhaustive for every explicitly named reducer printed in v15:

| Exact reducer | Kind | Fingerprint domain | Authoritative source | Printed section |
|---|---|---|---|---|
| `BindingEffectiveCurrentReducer` | reducer | `NOT_STANDALONE` | R7 7.3 + R15 5.2 + R15 5.3 + R16 3.4 + R17 2.3 + R18 4.1 + R18 4.2 + R19 2.3 + R20 6 | 6.1 |
| `ResponsibilityAssignmentEffectiveReducer` | reducer | `NOT_STANDALONE` | R15 3.4 + R16 3.4 + R17 2.3 + R19 2.3 + R20 6 | 6.2 |
| `DelegationEffectiveCurrentReducer` | reducer | `NOT_STANDALONE` | R1 12 + R7 11.2 + R7 12.2 + R8 4.1 + R8 4.2 + R8 4.3 + R15 5.2 + R15 5.3 + R16 3.4 + R17 2.3 + R19 2.3 | 6.3 |
| `HistoricalActionAssuranceReducer` | reducer | `NOT_STANDALONE` | R8 5.2 + R8 5.3 + R8 5.4 + R15 5.2 + R15 5.3 + R16 3.4 | 6.4 |
| `ActorIdentityEffectiveReducer` | reducer | `NOT_STANDALONE` | R7 4.3 + R15 2.3 + R16 3.2 + R16 3.4 + R17 2.3 + R18 2.1 + R19 2.1 + R19 2.2 | 9 |
| `TemporaryWorkerStewardshipScopeReducerV0_1R19` | reducer | `NOT_STANDALONE` | R19 4.1 + R19 4.2 | 9.2 |
| `TemporaryWorkerResponsibilityBindingReducerV0_1R18` | reducer | `NOT_STANDALONE` | R18 3.1 + R18 3.2 + R18 3.3 + R19 2.3 | 10.1 |
| `ActivationEvidenceResumeRevalidationReducerV0_1R19` | reducer | `NOT_STANDALONE` | R19 3.1 + R19 3.2 | 12.1 |
| `CompromiseImpactStreamReducer` | reducer | `NOT_STANDALONE` | R8 5.1 + R8 5.3 + R8 5.4 + R9 4 + R15 5.1 + R15 5.2 + R15 5.3 + R20 4.2 + R20 5 | 5.2 and 15 |
| `AuthenticatorProfileEffectiveReducer` | reducer | `NOT_STANDALONE` | R7 5.2 + R7 5.3 + R16 3.2 + R16 3.4 + R17 2.3 | 18.2 |
| `PrincipalEffectiveReducer` | reducer | `NOT_STANDALONE` | R7 6.1 + R7 6.2 + R7 6.3 + R7 6.4 + R16 3.2 + R16 3.4 + R17 2.3 | 18.3 |
| `BindingActivationEffectiveReducer` | reducer | `NOT_STANDALONE` | R2 5 + R3 3 + R4 5.1 + R4 5.2 + R4 5.3 + R7 7.2 + R16 3.2 + R16 3.4 + R17 2.3 + R18 4.1 + R18 4.2 + R18 4.3 + R19 3.1 + R19 3.2 + R19 3.3 | 18.4 |
| `DelegationActivationEffectiveReducer` | reducer | `NOT_STANDALONE` | R2 6 + R3 2 + R3 4 + R4 6.1 + R4 6.2 + R4 6.3 + R7 7.4 + R16 3.2 + R16 3.4 + R17 2.3 + R18 4.1 + R18 4.2 + R18 4.3 + R19 3.1 + R19 3.2 + R19 3.3 | 18.5 |
| `SyntheticM0ManifestAssessmentReducer` | reducer | `NOT_STANDALONE` | R8 6.3 + R15 5.2 + R15 5.3 + R16 3.2 + R16 3.4 + R17 2.3 | 20.1 |
| `ActionAssuranceCompleteSetReducer` | reducer | `NOT_STANDALONE` | R16 3.1 + R16 3.2 + R16 3.4 + R17 2.1 + R17 2.2 + R17 2.3 + R18 4.1 + R18 4.2 | 19.1 and 19.2 |

The surface row set equals every top-level schema block name in this file. The
reducer row set equals every explicitly named reducer definition. Completeness
also requires source-field equality: a row-set match alone is insufficient.
Canonical F2 fingerprints use the exact printed domain, R15 profile, R4
envelope, R7 scalar profile, RFC 8785 JCS, Unicode 15.1 NFC, unknown-field
rejection, and the complete source-defined object excluding only its own
canonical fingerprint. External interfaces remain owned by their named source
contract and receive no inferred F2 fingerprint.

```text
effective_top_level_schema_rows: 66
explicit_named_reducer_rows: 15
duplicate_schema_rows: 0
duplicate_reducer_rows: 0
```

## 22. Non-authorization

The final independent review applies F2_FREEZE_RULE_V0_1. Only an exact
reachable identity-spoofing, authority-expansion, revocation/compromise-bypass,
fail-open, dual-writer, circular-proof, M0-impossibility, or unresolved
internal-contradiction finding is BLOCKING_F2. F3/F4 protocol choices,
production authentication, storage, Rust layout, performance, fixtures,
source-index presentation, and other implementation-profile findings are
documented without triggering a new F2 amendment.

PASS_NO_BLOCKER means the F2 core freeze gate is satisfied. It does not claim
semantic perfection, implementation readiness, F3/F4 completion, production
readiness, or absence of non-blocking findings. A PASS only places the fixed
R1-R20 unit on Jenn's atomic freeze-decision surface.

This complete materialization creates no authority. F2 remains unaccepted
pending the user-scoped targeted consistency review and fresh full atomic-bundle
independent review. Those reviews, not this materialization or its authoring
run, determine the next eligible gate.
F3, implementation, runtime, production authentication, database, service,
provider, credential, commit, and push actions remain unauthorized.
