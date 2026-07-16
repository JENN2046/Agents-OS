# AGENTS OS F2 Effective Contract Materialization v0.1-r8

```yaml
document_type: derived_effective_contract_materialization
project: AGENTS OS
contract: F2 Actor Identity and Delegation v0.1
effective_version: v0.1-r8
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: derived_review_surface
source_of_authority: fixed_R1_through_R8_subjects_only
is_acceptance_subject: false
creates_new_semantics: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
F3_started: false
```

## 1. Authority and source hashes

This document is a resolved reading surface. It neither replaces nor amends a
fixed subject. If it conflicts with a subject, the subject set and the explicit
R1-to-R8 precedence rules control.

| Subject | SHA-256 |
|---|---|
| R1 base | `639e255417be99613cbe768c3b22edec7d5e1303d5a006e2c5dd70ceb1e83f2b` |
| R2 amendment | `8df5e63b9170491c8ea0e764ee6a297035164160bee976674c073f5bf921edcd` |
| R3 amendment | `d4c7e2e59a71911e47b62dd1ecddc7f56e1292841ceb7181c4d08346f7a0a9db` |
| R4 amendment | `a60a6a75c24b0fca68cb87e6e2f576f542f0f4a20caf12adbebb136ad9f51f59` |
| R5 amendment | `cf568eac5aa06b785ad047d41e2f22e7223e625840a3d96eccfcd9a1434b57be` |
| R6 amendment | `bed38cf83a2d15da3c11383b9b1ec264a3bf390f6d9fc0931f45d2d8c0e94932` |
| R7 amendment | `343881f2292fbb3c09b0cc572b0d9a9c8f77eef1e4b5957134de31796228187c` |
| R8 amendment | `861b5ac20d170466d0ecdcc7f1bdf5aeaf50f01a7431dbea3b027b66bce1fde3` |

R8 has exact precedence only for the topics named in R8 Section 1. All other
R1-R7 semantics remain effective. The acceptance subject set is R1-R8; this
materialization is excluded.

## 2. Effective source map

| Effective topic | Controlling source |
|---|---|
| Actor classes and stable meanings | R1 Sections 4-6 |
| Actor revision schema, authority, and fingerprint | R8 Section 7; replaces overlapping R1/R2/R7 fields |
| Principal and Profile lifecycle/currentness | R7 Sections 3, 5, and 6, with exact action binding from R8 Section 2 |
| Binding subject, activation, and effective currentness | R3-R7, with transition authority/action binding from R8 Sections 2-3 |
| Assignment provenance and scope | R2/R7; `EXACT_SET` only in v0.1 |
| Delegation lineage and effective currentness | R1-R7 with total descendant cascade from R8 Section 4 |
| Suspension, revocation, resume, and renunciation | R7 Section 8 replaced where R8 Sections 2-3 specify action and authority |
| Historical action assurance | R7 Section 9 with complete aggregation from R8 Section 5 |
| Synthetic M0 provisioning | R7 Sections 5-6 replaced where R8 Section 6 specifies the graph |
| Scalar and fingerprint profile | R4-R7, including `F2 Canonical Scalar Profile v0.1` |
| Single Prohibited Boundary | R1/R6; unchanged by R7-R8 |

## 3. Exact mutation and action schemas

Source: R8 Sections 2.1-2.4, hash
`861b5ac20d170466d0ecdcc7f1bdf5aeaf50f01a7431dbea3b027b66bce1fde3`.

```yaml
MutationIntentV0_1:
  intent_id:
  intent_revision: 1
  mutation_kind: ACTOR_IDENTITY_REVISION | AUTHENTICATOR_PROFILE_REVISION | PRINCIPAL_REVISION | GOVERNED_STATE_TRANSITION | COMPROMISE_IMPACT | SYNTHETIC_M0_MANIFEST_CREATE | SYNTHETIC_M0_MANIFEST_ACTIVATION
  target_kind: ACTOR_IDENTITY | AUTHENTICATOR_PROFILE | PRINCIPAL | BINDING | ASSIGNMENT | DELEGATION | BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE | COMPROMISE_IMPACT_STREAM | SYNTHETIC_M0_MANIFEST | SYNTHETIC_M0_MANIFEST_ACTIVATION
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

R8LifecycleMutationProvenance:
  mutation_body_fingerprint:
  mutation_intent_ref:
  mutation_intent_fingerprint:
  lifecycle_action_ref: LifecycleActionRefV0_1R8 | SyntheticManifestDerivedLifecycleRefV0_1
  mutation_replay_identity: CanonicalDigestScalarV0_1
  created_at_event_sequence:

AuthenticatorProfileRevisionR8:
  profile_id:
  profile_revision:
  expected_previous_profile_revision: null | positive_revision
  supersedes_profile_revision: null | positive_revision
  transition_kind: CREATE | UPDATE | SUSPEND | RESUME | RETIRE
  source_status: null | ACTIVE | SUSPENDED
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

PrincipalRevisionR8:
  principal_id:
  principal_revision:
  expected_previous_principal_revision: null | positive_revision
  supersedes_principal_revision: null | positive_revision
  transition_kind: CREATE | ROTATE_CREDENTIALS | SUSPEND | RESUME | REVOKE | RETIRE
  source_status: null | ACTIVE | SUSPENDED | REVOKED
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

Domain tags:

```text
agents-os.mutation-intent.v0.1
agents-os.lifecycle-action-ref.v0.1-r8
```

The complete mutation-body projections are:

| Mutation kind | Exact projection |
|---|---|
| `ACTOR_IDENTITY_REVISION` | every R8 Section 7 Actor field except action ref, intent ref, replay identity, derived Event, and final fingerprint |
| `AUTHENTICATOR_PROFILE_REVISION` | every effective R7 Profile field except the same provenance/result fields |
| `PRINCIPAL_REVISION` | every effective R7 Principal field except the same provenance/result fields |
| `GOVERNED_STATE_TRANSITION` | target, transition, authority fingerprint, CAS, Event, and ordered reason codes |
| `COMPROMISE_IMPACT` | stream/revision/CAS, compromised subject, incident basis, watermark, complete target set/fingerprint, impact, authority fingerprint, and Event |
| `SYNTHETIC_M0_MANIFEST_CREATE` | every manifest body/spec field except action, activation, Event, and final fingerprint |
| `SYNTHETIC_M0_MANIFEST_ACTIVATION` | activation stream/revision/CAS, manifest, transition, Jenn decision, and Event |

The body fingerprint uses domain tag `agents-os.mutation-body.v0.1`. Optional
positions are explicit nulls. The effective Event is exactly ledger head plus
one and is both the F3 intake Event and F2 mutation Event. A derived synthetic
create uses the manifest activation intent as its closed group intent. Replay identity uses
domain tag `agents-os.lifecycle-mutation-replay.v0.1-r8`. Commit order is body,
body digest, intent, intent digest, committed action, action ref, replay
identity, final subject/fact, then final digest. Fixed points reject.

## 4. Exact governed transition authority

Source: R8 Sections 3.1-3.3.

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

TransitionAuthorityBasisV0_1R8:
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
  profile_assessment_ref: optional
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

GovernedStateTransitionFactV0_1R8:
  transition_fact_id:
  target_kind: BINDING | ASSIGNMENT | DELEGATION | BINDING_ACTIVATION_EVIDENCE | DELEGATION_ACTIVATION_EVIDENCE
  target_ref:
  target_fingerprint:
  transition: SUSPEND | RESUME | REVOKE | RENOUNCE
  authority_basis: TransitionAuthorityBasisV0_1R8
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
```

The exact target/transition/basis table is:

| Target | Transition | Allowed exact basis kinds |
|---|---|---|
| Authenticator Profile | `CREATE` | `JENN_ROOT_ACTION`, `JENN_GOVERNANCE_DECISION_BASIS`, `ACCEPTED_PROVISIONING_ACTION` |
| Authenticator Profile | other lifecycle transitions | exact R8 Section 3.2 subset |
| Principal | lifecycle transitions | exact R8 Section 3.2 subset |
| Binding | `SUSPEND` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Binding | `RESUME` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| Binding | `REVOKE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `BOUND_ACTOR_SELF_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Assignment | `SUSPEND`, `RESUME`, `REVOKE` | `JENN_ROOT_ACTION` |
| Delegation | `SUSPEND`, `RESUME`, `REVOKE` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION`, `ANCESTOR_DELEGATOR_ACTION` |
| Delegation | `RENOUNCE` | `DELEGATE_RENUNCIATION_ACTION` |
| Binding activation evidence | `SUSPEND`, `REVOKE` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION`, `ACCEPTED_INCIDENT_POLICY_ACTION` |
| Binding activation evidence | `RESUME` | `JENN_ROOT_ACTION`, `IDENTITY_STEWARD_ACTION`, `PROFILE_CONTROLLER_ACTION` |
| Delegation activation evidence | `SUSPEND`, `RESUME`, `REVOKE` | `JENN_ROOT_ACTION`, `DIRECT_DELEGATOR_ACTION` |
| Delegation activation evidence | `RENOUNCE` | `DELEGATE_RENUNCIATION_ACTION` |

Every unlisted combination rejects. Binding/Assignment/activation-evidence
`RENOUNCE` rejects. The detailed current-state predicate and required/forbidden
basis fields are exactly R8 Sections 3.1-3.2 and are not widened here.

## 5. Exact Delegation effective reducer

Source: R8 Sections 4.1-4.3.

At one watermark the reducer reads the target head, own transition head, root
Assignment, exact root-to-parent chain, issuance/activation assurance, Actor
identity, scope, lineage, time, and policy. The chain cannot omit or reorder an
ancestor.

| Upstream effective state | Descendant mapping |
|---|---|
| `REVOKED`, `RENOUNCED`, or historical assurance `INVALIDATED` | `REVOKED` |
| `SUPERSEDED` | `SUPERSEDED` |
| `SUSPENDED` | `SUSPENDED` |
| `INDETERMINATE`, challenged assurance, or incomplete coverage | `INDETERMINATE` |
| `EXPIRED` | `EXPIRED` |
| `NOT_YET_ACTIVE` | `NOT_YET_ACTIVE` |
| `ACTIVE` | continue |

Total precedence:

```text
REVOKED
> SUPERSEDED
> SUSPENDED
> INDETERMINATE
> EXPIRED
> NOT_YET_ACTIVE
> ACTIVE
```

The child changes prospectively at the upstream Event. No child Event is
synthesized. Resume clears only its own suspension stream.

## 6. Exact historical action assurance

Source: R8 Sections 5.1-5.4.

```yaml
CompromiseImpactFactV0_1R8:
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
  authority_basis: TransitionAuthorityBasisV0_1R8
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

HistoricalActionValidityAssessmentR8Additions:
  impact_input_set_ref:
  impact_input_set_fingerprint:
  impact_coverage_through_event_sequence:
```

Rust derives the complete set from the ledger through the same assessment
watermark. It sorts current heads by stream ID then revision. Missing coverage,
forks, duplicates, Event gaps, target mismatch, or digest conflict makes the
set incomplete. `INVALIDATED` is terminal per stream; clear affects only an
exact current challenge stream.

Aggregate precedence:

```text
any verified current INVALIDATED -> INVALIDATED
else incomplete/conflicting coverage -> INDETERMINATE
else any CHALLENGED -> CHALLENGED
else -> CONFIRMED
```

Impact authority is total: Jenn root or the exact same-or-higher identity
steward may challenge, invalidate, or clear; accepted incident policy may only
challenge. The effective impact domain tag is
`agents-os.compromise-impact-fact.v0.1-r8`.

## 7. Exact synthetic M0 graph

Source: R8 Sections 6.1-6.4.

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

SyntheticM0PrincipalProvisioningManifestV0_1R8:
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

SyntheticM0ManifestActivationRevisionV0_1:
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

SyntheticM0ManifestAssessmentV0_1:
  manifest_ref:
  activation_revision_ref:
  assessment: ACTIVE | REVOKED | INDETERMINATE
  based_on_event_sequence:
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
```

The manifest creation action is Jenn governance only. Activation revision 1 is
Jenn `ACCEPT`; later contiguous Jenn `REVOKE` is terminal. Activation decision
fields equal the decision inside the lifecycle action ref. Synthetic creation
uses the one manifest-derived ref per exact creation spec, and the synthetic
Profile uses the matching manifest-derived controller ref. Manifest revocation
makes all derived subjects and controller dependencies non-active at the same
Event.

All declared synthetic subjects materialize atomically at the manifest ACCEPT
Event. Each subject uses its creation-spec fingerprint as body fingerprint,
the manifest activation intent as group intent, its derived lifecycle ref as
action ref, derivation replay identity as mutation replay identity, and the
activation Event as created Event. Partial materialization or different
existing bytes rejects.

## 8. Exact Actor revision

Source: R8 Sections 7.1-7.3.

```yaml
ActorIdentityTransitionAuthorityBasisV0_1R8:
  authority_basis_id:
  basis_kind: JENN_ROOT_ACTION | JENN_GOVERNANCE_DECISION_BASIS | IDENTITY_STEWARD_ACTION | BOUND_ACTOR_SELF_SUSPEND_ACTION | ACCEPTED_INCIDENT_POLICY_ACTION | ACCEPTED_PROVISIONING_ACTION
  requested_by_actor_ref: optional
  requested_by_actor_identity_assessment_ref: optional
  requested_by_effective_binding_assessment_ref: optional
  Jenn_root_authority_ref: optional
  Jenn_root_authority_fingerprint: optional
  stewardship_relation_ref: optional
  stewardship_relation_fingerprint: optional
  incident_policy_ref: optional
  incident_policy_fingerprint: optional
  incident_controller_ref: optional
  provisioning_component_ref: optional
  provisioning_component_fingerprint: optional
  provisioning_basis_ref: optional
  provisioning_basis_fingerprint: optional
  based_on_event_sequence:
  canonical_fingerprint: R4FingerprintEnvelope

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
  transition_authority_basis: ActorIdentityTransitionAuthorityBasisV0_1R8
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

Removed fields are `identity_provisioning_basis_ref`, `created_by_actor_ref`,
free-form `change_reason`, R2 separate stewardship source/actor/binding/action
fields, R7 `target_status`, and the duplicate R7 steward field. Reintroducing
one rejects.

The exact Actor fingerprint domain tag is
`agents-os.actor-identity-revision.v0.1-r8`; its known object contains every
displayed scalar/semantic field, inserting verified authority/action digest
strings instead of their full envelopes, and excludes only removed fields and
the final digest itself. All numeric values use the R7 scalar profile.

For every other R8 schema, the effective default is
`SHA-256(JCS([exact_R8_domain_tag,
exact_schema_known_object_without_canonical_fingerprint]))`. All displayed
fields and explicit nulls are included; unknown or omitted fields reject. The
effective Profile and Principal tags are respectively
`agents-os.authenticator-profile-revision.v0.1-r8` and
`agents-os.principal-revision.v0.1-r8`.

## 9. Unchanged effective boundaries

F2 still does not create ordinary permission levels. It defines stable identity,
responsibility, representation, delegation, authentication attribution, and
the check against one external canonical Prohibited Behavior List revision.
Identity, responsibility, relationship, authentication, and execution
admission remain different systems.

`RUNNING` services, credentials, production keys, provider calls, TaskPermit,
effect fencing, F3 intake, implementation, and runtime activation remain
outside this document and unauthorized.

## 10. Review use

The fresh independent reviewer must verify the R1-R8 source hashes directly,
recompute this materialization hash, compare every displayed effective schema
and reducer to its named source section, and treat any mismatch as a finding
against this derived surface. A materialization defect does not silently amend
the subjects.
