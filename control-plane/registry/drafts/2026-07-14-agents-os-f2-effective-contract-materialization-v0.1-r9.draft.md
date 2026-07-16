# AGENTS OS F2 Effective Contract Materialization v0.1-r9

```yaml
document_type: derived_effective_contract_materialization
project: AGENTS OS
contract: F2 Actor Identity and Delegation v0.1
effective_version: v0.1-r9
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: derived_review_surface
source_of_authority: fixed_R1_through_R9_subjects_only
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

R1-R9 are the acceptance subject set. This materialization is excluded.

## 2. Exact action and mutation order

The effective mutation kinds are:

```text
ACTOR_IDENTITY_REVISION
AUTHENTICATOR_PROFILE_REVISION
PRINCIPAL_REVISION
BINDING_REVISION
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

### 3.3 Binding

Source: R9 Section 3; it replaces assembled R1/R3/R4/R7 subject schemas and
fingerprints.

```yaml
ActorPrincipalBindingRevisionR9:
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

Binding body excludes only mutation/body/intent/source/replay/Event/final
digest provenance fields. Its final fingerprint is the exact R9 known object
under `agents-os.actor-principal-binding-revision.v0.1-r9`. Synthetic Binding
spec fingerprint equals the `BINDING_REVISION` mutation-body fingerprint.

### 3.4 Actor

R8 Section 7 complete Actor schema and formula remain unchanged. Its complete
transition table is:

| Transition | Source | Target | Exact authority kind |
|---|---|---|---|
| `CREATE` | none | `ACTIVE` | `JENN_GOVERNANCE_DECISION_BASIS`, exact steward, or accepted provisioning for service/host |
| `UPDATE` | `ACTIVE` | `ACTIVE` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION` |
| `UPDATE` | `SUSPENDED` | `SUSPENDED` | `JENN_ROOT_ACTION` or `IDENTITY_STEWARD_ACTION` |
| `SUSPEND` | `ACTIVE` | `SUSPENDED` | Jenn, steward, self-suspend, incident, or accepted provisioning where allowed |
| `RESUME` | `SUSPENDED` | `ACTIVE` | Jenn or exact steward |
| `COMPROMISE` | `ACTIVE` or `SUSPENDED` | `COMPROMISED` | Jenn, steward, incident, or accepted provisioning where allowed |
| `RECOVER` | `COMPROMISED` | `ACTIVE` | Jenn or exact steward plus recovery evidence |
| `RETIRE` | `ACTIVE`, `SUSPENDED`, or `COMPROMISED` | `RETIRED` | Jenn, steward, or accepted provisioning where allowed |

`RETIRED` is terminal. Self action cannot resume, recover, update, or retire.

## 4. Complete authority schema and tables

### 4.1 Authority basis

Source: R8 Section 3.1 as replaced by R9 Section 5.

```yaml
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

### 4.4 Binding issuance table

| Mode | Exact allowed basis |
|---|---|
| `JENN_INTERACTIVE_AUTHENTICATION` | `JENN_ROOT_ACTION`; `JENN_GOVERNANCE_DECISION_BASIS` only for bootstrap |
| `RESIDENT_ATTESTED_AGENT_SESSION` | `IDENTITY_STEWARD_ACTION` |
| `SERVICE_PROVISIONING_ATTESTATION` | `ACCEPTED_PROVISIONING_ACTION` |
| `WORKER_ASSIGNMENT_HANDSHAKE` | `DIRECT_DELEGATOR_ACTION` |
| `SYNTHETIC_M0_FIXTURE` | manifest-derived group intent only |

### 4.5 Governed transition table

| Target | Transition | Exact allowed basis |
|---|---|---|
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

## 5. Compromise impact and historical assurance

### 5.1 Complete impact schema

```yaml
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
```

### 5.2 Impact authority and membership tables

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

## 6. Unchanged total reducers

R8 Delegation descendant precedence remains:

```text
REVOKED > SUPERSEDED > SUSPENDED > INDETERMINATE > EXPIRED > NOT_YET_ACTIVE > ACTIVE
```

Binding effective-current reducer remains R7 Section 7.3. Activation evidence
proves activation only; it is not the effective Binding projection. Assignment
and Delegation use historical issuance assurance, not current session Binding,
and require complete impact coverage at their assessment watermark.

## 7. Synthetic M0 atomic graph

Manifest creation is bound by a prior Jenn governance authority and a later
exact Jenn decision. Manifest activation uses the acyclic Section 2 body. At
the one ACCEPT Event, the closed ordered Profile/Principal/Binding spec set is
materialized atomically. Each subject uses its spec body fingerprint, the group
activation intent, exact derived lifecycle/issuance ref, derivation replay
identity, and activation Event. Any omitted, extra, conflicting, or partially
materialized subject rejects the transaction. Revocation makes all derived
subjects and the controller non-active prospectively.

## 8. Non-authorization

This materialization creates no authority. F2 remains unaccepted pending fresh
independent review and Jenn's later decision. F3, implementation, runtime,
production authentication, database, service, provider, credential, commit,
and push actions remain unauthorized.
