# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R9 Amendment Draft

Status: author-closed candidate fixed for fresh independent review; not accepted or frozen  
Date: 2026-07-16  
Base R8 SHA-256: `f483f8db5df3fc7e435c2a5acd8a3d29fff438f08b69ea3049543d0fded3bb0c`  
Blocking R8 review SHA-256: `219254fee8bfe9772f5728ad3764b9948f7f05d982e1b4eb333111dc0ecbd484`

## 1. Scope and precedence

R9 closes only `F4-R8-FULL-ATOMIC-IR-B01` through `B06` and the strict
validation gaps independently confirmed against those findings. Effective
order is R9, R8, R7, R6, R5, R4, R3, R2, R1. All twenty-five R1-R8 subjects
remain immutable. The effective literal is
`F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R9_ATOMIC_BUNDLE`.

R9 is still a zero-effect contract/witness revision. It changes no frozen F2 or
F3 lifecycle result, starts no F5 work, and grants no implementation, runtime,
Host, provider, database, authentication, or physical-effect authority.

Section 10 is the final R9 boundary correction. Where any earlier R9 paragraph,
schema, fixture rule, or validation rule conflicts with Section 10, Section 10
replaces it. Earlier text remains visible only as review lineage inside this
working subject and is not effective R9 semantics.

## 2. Normative effect scope and authorization basis

R9 replaces every opaque `exact_effect_scope_fingerprint` with this normative
object. It uses the unchanged R8 `F4_FP` formula and exact printed field order.

```yaml
EffectScopeV0_1R9:
  interface_version: agents-os.effect-scope.v0.1-r9
  scope_ref: stable_ref
  task_authority_binding_fingerprint: lowercase_sha256
  actor_authority_binding_fingerprint: lowercase_sha256
  resident_command_binding_fingerprint: lowercase_sha256
  host_trust_ref: stable_ref
  host_trust_fingerprint: lowercase_sha256
  effect_intent_ref: stable_ref
  effect_intent_fingerprint: lowercase_sha256
  operation_kind: stable_ref
  target_resource_refs: sorted_unique_low_disclosure_refs
  payload_fingerprint: lowercase_sha256
  capability_set_fingerprint: lowercase_sha256
  resource_set_fingerprint: lowercase_sha256
  secret_handle_set_fingerprint: lowercase_sha256
  idempotency_key: stable_ref
  requires_human_presence: boolean
  human_presence_binding_fingerprint: lowercase_sha256
  expected_result_contract_ref: stable_ref
  expected_result_contract_fingerprint: lowercase_sha256
  target_host_id: stable_ref
  target_host_trust_revision: positive_safe_integer
  external_effect_requested: boolean
  canonical_fingerprint: lowercase_sha256

PolicySnapshotV0_1R9:
  interface_version: agents-os.policy-snapshot.v0.1-r9
  policy_ref: stable_ref
  policy_revision: positive_safe_integer
  exact_scope_ref: stable_ref
  exact_scope_fingerprint: lowercase_sha256
  derived_mode: NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED | EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED | PROHIBITED_NON_ISSUABLE
  rule_set_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

ProhibitedBehaviorListSnapshotV0_1R9:
  interface_version: agents-os.prohibited-behavior-list-snapshot.v0.1-r9
  prohibited_behavior_list_ref: stable_ref
  prohibited_behavior_list_revision: positive_safe_integer
  exact_scope_ref: stable_ref
  exact_scope_fingerprint: lowercase_sha256
  boundary_result: ALLOWED_WITHOUT_SEPARATE_JENN_AUTHORIZATION | EXACT_JENN_AUTHORIZATION_REQUIRED | PROHIBITED
  rule_set_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

ProhibitedBoundaryAssessmentV0_1R9:
  interface_version: agents-os.prohibited-boundary-assessment.v0.1-r9
  assessment_ref: stable_ref
  exact_scope_ref: stable_ref
  exact_scope_fingerprint: lowercase_sha256
  policy_snapshot_ref: stable_ref
  policy_snapshot_fingerprint: lowercase_sha256
  prohibited_behavior_list_snapshot_ref: stable_ref
  prohibited_behavior_list_snapshot_fingerprint: lowercase_sha256
  matched_rule_ids: sorted_unique_closed_strings
  watermark_event_sequence: non_negative_safe_integer
  result: ALLOWED | PROHIBITED | INDETERMINATE
  reason: AUTONOMOUS_ALLOWED | EXACT_JENN_REQUIRED | PROHIBITED | INPUT_UNAVAILABLE | INTEGRITY_FAILURE
  assessment_fingerprint: lowercase_sha256

EffectAuthorizationBasisV0_1R9:
  interface_version: agents-os.effect-authorization-basis.v0.1-r9
  exact_scope_ref: stable_ref
  exact_scope_fingerprint: lowercase_sha256
  policy_snapshot_ref: stable_ref
  policy_snapshot_fingerprint: lowercase_sha256
  prohibited_behavior_list_snapshot_ref: stable_ref
  prohibited_behavior_list_snapshot_fingerprint: lowercase_sha256
  prohibited_boundary_assessment_ref: stable_ref
  prohibited_boundary_assessment_fingerprint: lowercase_sha256
  derived_mode: NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED | EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED | PROHIBITED_NON_ISSUABLE
  evaluation_watermark_event_sequence: non_negative_safe_integer
  result: RESOLVED
  canonical_fingerprint: lowercase_sha256
```

`EffectScope` MUST resolve the exact emitted effect intent and its exact
F1/F2/F3 authority bindings, operation, targets, payload, idempotency,
capability/resource/secret/presence/result/Host values. Policy and PBL snapshots
MUST resolve that same scope, share one watermark, and deterministically agree
on the derived mode. The prohibited-boundary assessment resolves the exact
scope and both snapshots; `TaskPermit.prohibited_boundary_evidence_*` resolves
that assessment, never the PBL document alone. The authorization basis resolves
all four. A label hash,
zero digest, different scope, inconsistent mode, stale snapshot, or unresolved
ref emits no authorization requirement.

`EffectScope.scope_ref = "effect-scope:" + scope_id`, where
`scope_id = SHA256(JCS(["agents-os.effect-scope-id.v0.1-r9", every
EffectScope field value after scope_ref and before canonical_fingerprint in
printed order]))`. The ordinary `F4_FP` then covers `scope_ref` and every
preceding scope field without a hash fixed point. Its direct
operation/targets/payload/result/idempotency values MUST equal the resolved
EffectIntent; its authority/Host/set/presence values MUST equal the permit's
resolved bindings. Any mismatch rejects before authorization mode derivation.

R9 replaces the R8 requirement field list by inserting
`exact_effect_scope_ref` immediately before `exact_effect_scope_fingerprint`,
and by inserting `revocation_observation_ref` and
`revocation_observation_fingerprint` immediately after
`revocation_event_sequence`. Its schema name and interface are
`EffectAuthorizationRequirementV0_1R9` and
`agents-os.effect-authorization-requirement.v0.1-r9`. The
`requirement_basis_ref/fingerprint` MUST resolve the exact R9 basis.

R9 inserts the complete `effect_scope` object into `TaskPermitV0_1R9`
immediately after `effect_intent_binding`. It inserts
`effect_scope_ref/fingerprint` into `F4AcceptedEffectHandoffV0_1R9`
immediately after `effect_intent_ref/fingerprint`. The permit, authorization
requirement, handoff, policy/PBL snapshots, and final authorization evidence all
bind one byte-identical scope ref/fingerprint.

## 3. Recomputable capability/resource authority

R9 adds the following exact schemas, all fingerprinted with R8 `F4_FP`.

```yaml
EffectAuthorityPolicySourceSnapshotV0_1R9:
  interface_version: agents-os.effect-authority-policy-source-snapshot.v0.1-r9
  source_ref: stable_ref
  policy_revision: positive_safe_integer
  allowed_operation_set: sorted_unique_closed_strings
  allowed_resource_kind: closed_resource_kind
  allowed_resource_refs: sorted_unique_stable_refs
  constraint_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

EffectAuthorityProhibitedBoundarySourceSnapshotV0_1R9:
  interface_version: agents-os.effect-authority-prohibited-boundary-source-snapshot.v0.1-r9
  source_ref: stable_ref
  prohibited_behavior_list_revision: positive_safe_integer
  allowed_operation_set: sorted_unique_closed_strings
  allowed_resource_kind: closed_resource_kind
  allowed_resource_refs: sorted_unique_stable_refs
  constraint_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

OperationRegistryV0_1R9:
  interface_version: agents-os.operation-registry.v0.1-r9
  registry_ref: stable_ref
  registry_revision: positive_safe_integer
  operation_vocabulary: sorted_unique_closed_strings
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

CapabilityDefinitionV0_1R9:
  interface_version: agents-os.capability-definition.v0.1-r9
  definition_ref: stable_ref
  definition_revision: positive_safe_integer
  operation_registry_ref: stable_ref
  operation_registry_fingerprint: lowercase_sha256
  allowed_operation_set: sorted_unique_closed_strings
  constraint_schema_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

ResourceDefinitionV0_1R9:
  interface_version: agents-os.resource-definition.v0.1-r9
  definition_ref: stable_ref
  definition_revision: positive_safe_integer
  resource_kind: closed_resource_kind
  operation_registry_ref: stable_ref
  operation_registry_fingerprint: lowercase_sha256
  allowed_operation_set: sorted_unique_closed_strings
  selector_kind: EXACT_REF
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

AuthorityScopeProjectionV0_1R9:
  interface_version: agents-os.authority-scope-projection.v0.1-r9
  projection_ref: stable_ref
  role: F1_TASK | F2_RESPONSIBILITY | F2_DELEGATION | F3_COMMAND | POLICY | PROHIBITED_BEHAVIOR_LIST
  source_ref: stable_ref
  source_fingerprint: lowercase_sha256
  source_currentness_assessment_ref: stable_ref
  source_currentness_assessment_fingerprint: lowercase_sha256
  operation_registry_fingerprint: lowercase_sha256
  allowed_operation_set: sorted_unique_closed_strings
  allowed_resource_kind: closed_resource_kind
  allowed_resource_refs: sorted_unique_stable_refs
  constraint_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  result: CURRENT
  canonical_fingerprint: lowercase_sha256
```

The synthetic M0 registry contains exactly `F4_M0_SYNTHETIC_NOOP`. Definitions
allow only that operation. It is bound to one exact prospective F3
`CommandTypeDefinitionV0_1` with `registry_revision = 5`,
`command_type_id = F4_M0_SYNTHETIC_NOOP`, `command_type_version = 1`,
`owner_contract_ref = F4_R9_AMENDMENT_SUBJECT`,
`owner_contract_sha256 = SHA-256(the exact R9 amendment subject bytes)`,
`effect_class = EFFECT_INTENT`, `allowed_target_kinds = [F4_M0_NO_EFFECT]`,
`expected_target_revision_policy = FORBIDDEN`,
`responsibility_mode = REQUIRED`, `unknown_fields_policy = REJECT`, and an
exact M0-only payload/reducer/gate profile that forbids external effect,
provider call, runtime activation, implementation, production authentication,
and any output other than this constructive witness. The definition and its
payload/reducer descriptors use the following R9 materialization wrapper because
the frozen F3 descriptors are exact one-line JCS values without their own
fingerprint field:

```yaml
F3DescriptorMaterializationV0_1R9:
  interface_version: agents-os.f3-descriptor-materialization.v0.1-r9
  descriptor_ref: stable_ref
  descriptor_kind: PAYLOAD_SCHEMA | REDUCER
  exact_descriptor: exact_closed_descriptor_object
  exact_jcs_sha256: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

`exact_jcs_sha256 = SHA-256(JCS(exact_descriptor))`. The inner payload
descriptor has exactly `additional_properties`, `interface_version`,
`ordered_fields`, `rules`, and `schema_ref`, with additional properties false,
one empty no-effect payload, and rules forbidding unknown/effect/provider/auth
fields. The inner reducer descriptor has exactly `atomic_outputs`,
`effect_class`, `failure_semantics`, `interface_version`,
`ordered_preconditions`, `payload_schema_sha256`, `prohibited_outputs`, and
`reducer_ref`; it binds the payload digest, has `EFFECT_INTENT`, emits only the
constructive witness chain, and prohibits physical/external/provider/runtime
outputs. Both exact inner descriptor profiles are closed WRAPPER_SCHEMAS and
recursively inventoried; the outer materialization is F4-fingerprinted and
symbol-resolvable. CommandTypeDefinition references the exact descriptor refs
and digests, not the outer fingerprints.

It is not a member of frozen F3 registry revision 4,
does not reinterpret either frozen `LEDGER_ONLY` command, and is inadmissible
before this complete F4 atomic bundle is accepted. The witness proves only
prospective contract constructibility; it does not register or activate the
definition at runtime.

The M0 EffectIntent, EffectScope, permit, and handoff resolve one exact result
contract rather than an opaque digest:

```yaml
F4M0ExpectedResultContractV0_1R9:
  interface_version: agents-os.f4-m0-expected-result-contract.v0.1-r9
  result_contract_ref: stable_ref
  allowed_terminal_outcomes: [NOT_EXECUTED]
  physical_effect_allowed: false
  external_effect_allowed: false
  provider_call_allowed: false
  raw_secret_allowed: false
  evidence_requirement: POSITIVE_ZERO_EFFECT_WITNESS
  canonical_fingerprint: lowercase_sha256
```

The result-contract ref/fingerprint at every occurrence resolves this same
object. It cannot name the downstream zero-effect stub because that would be a
cycle; the stub independently demonstrates satisfaction of this prior
contract. Any other outcome, true effect/provider/secret flag, unresolved
contract, or changed contract fingerprint rejects.

R9 replaces the R6 source-role rule to remove its circular
exact-Jenn dependency: every set has exactly one each of `F1_TASK`,
`F2_RESPONSIBILITY`, `F3_COMMAND`, `POLICY`, and
`PROHIBITED_BEHAVIOR_LIST`; `F2_DELEGATION` is present exactly when the Actor
binding uses delegation. `JENN_DECISION` is forbidden as a capability/resource
projection. Jenn authorization is evaluated only after the scope exists and can
restrict or reject it, never create an operation absent from the upstream
intersection.

The POLICY and PROHIBITED_BEHAVIOR_LIST projections resolve the two pre-scope
source snapshots above. Those snapshots bind the accepted authority vocabulary,
resource scope, constraints, revision, and watermark but do not contain an
EffectScope fingerprint. They are distinct from the main scope-specific
`PolicySnapshotV0_1R9` and `ProhibitedBehaviorListSnapshotV0_1R9`, which are
created only after grants and EffectScope exist and are used only for prohibited
boundary/mode derivation. This exact topology is acyclic:

```text
pre-scope F1/F2/F3/policy/PBL sources + definitions/registry
  -> projections -> proofs -> grants -> EffectIntent -> EffectScope
  -> scope-specific policy/PBL snapshots -> authorization basis/requirement
```
Every projection source ref/fingerprint resolves to the exact permit-bound F1,
F2, F3, policy/PBL, or Jenn object at a watermark not later than permit
issuance. Its currentness-assessment ref/fingerprint resolves the same source at
that watermark. Duplicate, missing, extra, stale, unresolved, wildcard, or ambient
source scope rejects.

R9 replaces the capability proof with `CapabilitySubsetProofV0_1R9` by adding
`source_projection_refs` immediately before
`source_projection_fingerprints`. The validator resolves each projection and
computes the sorted set intersection itself. `PASS / EXACT_SUBSET` is legal only
when the requested operation set is an exact subset of that computed
intersection and the definition/registry/constraint objects resolve.

R9 replaces the resource assessment with
`ResourceContainmentAssessmentV0_1R9` by adding
`source_projection_refs` immediately before
`source_projection_fingerprints`. `PASS / EXACT_CONTAINMENT` is legal only when
every required projection contains the exact resource ref/kind and requested
operation and the definition/registry/selector objects resolve.

`CapabilityGrantV0_1R9` and `ResourceGrantV0_1R9` retain R8 relative order but
use R9 definitions, projections, proofs, interfaces, and schema names. Every
proof/assessment ref/fingerprint resolves to the emitted PASS object. No
caller-supplied PASS, repeated label, or opaque proof is authority.

## 4. Resolved F2 identity, compromise history, and Host transitions

R9 adds:

```yaml
F2CurrentIdentityBindingEvidenceV0_1R9:
  interface_version: agents-os.f2-current-identity-binding-evidence.v0.1-r9
  host_actor_id: stable_ref
  host_actor_identity_revision: positive_safe_integer
  actor_ref: stable_ref
  actor_fingerprint: lowercase_sha256
  actor_class: EXECUTION_HOST
  actor_lifecycle_state: ACTIVE
  principal_id: stable_ref
  principal_revision: positive_safe_integer
  principal_ref: stable_ref
  principal_fingerprint: lowercase_sha256
  principal_class: HOST_PROCESS
  binding_ref: stable_ref
  binding_revision: positive_safe_integer
  binding_fingerprint: lowercase_sha256
  binding_actor_ref: stable_ref
  binding_principal_ref: stable_ref
  watermark_event_sequence: non_negative_safe_integer
  result: CURRENT
  canonical_fingerprint: lowercase_sha256

CompromiseHistoryEvidenceV0_1R9:
  interface_version: agents-os.compromise-history-evidence.v0.1-r9
  history_ref: stable_ref
  history_domain: F2_ACTOR | F4_HOST_TRUST
  subject_ref: stable_ref
  subject_fingerprint: lowercase_sha256
  lineage_id: stable_ref
  history_start_event_sequence: non_negative_safe_integer
  history_end_event_sequence: non_negative_safe_integer
  complete_event_set_fingerprint: lowercase_sha256
  compromise_event_refs: sorted_unique_stable_refs
  compromise_event_fingerprints: sorted_unique_lowercase_sha256
  observation: ABSENT | PRESENT
  canonical_writer_ref: stable_ref
  canonical_writer_fingerprint: lowercase_sha256
  result: COMPLETE
  canonical_fingerprint: lowercase_sha256

HostTrustActionEvidenceV0_1R9:
  interface_version: agents-os.host-trust-action-evidence.v0.1-r9
  action_ref: stable_ref
  action_kind: CREATE | UPDATE | SUSPEND | RESUME | REVOKE | COMPROMISE | RETIRE
  target_host_id: stable_ref
  expected_previous_host_trust_revision: positive_safe_integer | null
  observed_previous_head_ref: stable_ref | null
  observed_previous_head_fingerprint: lowercase_sha256 | null
  resulting_host_trust_revision: positive_safe_integer
  issuer_actor_ref: stable_ref
  issuer_actor_fingerprint: lowercase_sha256
  issuer_principal_ref: stable_ref
  issuer_principal_fingerprint: lowercase_sha256
  self_issued: false
  action_event_sequence: non_negative_safe_integer
  result: AUTHENTICATED
  canonical_fingerprint: lowercase_sha256

HostLifecyclePolicySnapshotV0_1R9:
  interface_version: agents-os.host-lifecycle-policy-snapshot.v0.1-r9
  policy_ref: stable_ref
  policy_revision: positive_safe_integer
  target_host_actor_id: stable_ref
  allowed_transition_kinds: sorted_unique_closed_transition_kinds
  required_issuer_actor_classes: sorted_unique_closed_actor_classes
  rule_set_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

HostLifecycleProhibitedBoundarySnapshotV0_1R9:
  interface_version: agents-os.host-lifecycle-prohibited-boundary-snapshot.v0.1-r9
  prohibited_behavior_list_ref: stable_ref
  prohibited_behavior_list_revision: positive_safe_integer
  target_host_actor_id: stable_ref
  prohibited_transition_kinds: sorted_unique_closed_transition_kinds
  rule_set_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  lifecycle_state: ACTIVE
  canonical_fingerprint: lowercase_sha256

HostTrustAuthorityBasisV0_1R9:
  interface_version: agents-os.host-trust-authority-basis.v0.1-r9
  basis_ref: stable_ref
  action_ref: stable_ref
  action_fingerprint: lowercase_sha256
  F2_identity_binding_evidence_ref: stable_ref
  F2_identity_binding_evidence_fingerprint: lowercase_sha256
  host_lifecycle_policy_snapshot_ref: stable_ref
  host_lifecycle_policy_snapshot_fingerprint: lowercase_sha256
  host_lifecycle_prohibited_boundary_snapshot_ref: stable_ref
  host_lifecycle_prohibited_boundary_snapshot_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  result: AUTHORIZED
  canonical_fingerprint: lowercase_sha256
```

The main R9 Host uses a revision-1 F2 `EXECUTION_HOST` Actor created through
the frozen accepted-provisioning route, a revision-1 `HOST_PROCESS` Principal,
a revision-1 ActorPrincipalBinding, a materialized Host-trust
revision 1 `CREATE`, and current revision 2 `UPDATE`. CREATE has null previous
fields, null observed-head fields, and a complete absence-of-head result in its
authenticated action/basis. UPDATE resolves revision 1 in both the Host-trust
object and action observed-head fields,
requires expected previous 1 and resulting revision 2, and resolves its
authenticated non-self action and authority basis. Both provisioning and
transition action/basis refs resolve. Later transitions are previous-plus-one;
self-issued, missing-head, wrong-CAS, wrong-action, or wrong-basis bytes reject.

Host lifecycle action/basis resolves the two preexisting lifecycle snapshots
above, not the main effect-scope Policy/PBL snapshots. Lifecycle snapshots bind
the target Host Actor and transition kinds but exclude the current Host-trust
fingerprint, so CREATE and UPDATE are acyclic:
`F2 identity + lifecycle snapshots -> action/basis -> HostTrust -> EffectScope`.

The current F2 evidence resolves the exact F2 Actor, Principal, and Binding
bytes/classes/lifecycle at one watermark. The R9 witness MUST materialize the
fixed non-production frozen-F2 Actor revision and assessment, Authenticator
Profile revision and assessment, HOST_PROCESS Principal revision and
assessment, ActorPrincipalBinding revision and assessment, Binding activation
assessment, responsibility source, and any applicable delegation chain using
their native frozen-F2 schema names, nested field types, and fingerprint
formulas. A FingerprintEnvelope cannot substitute for an embedded frozen-F2
authority-basis, lifecycle-action, assessment, or subject object. It MUST likewise materialize
the permit-bound frozen-F1 Task authority as the exact accepted
`GoalPlanMembershipRevision` plus its current full-snapshot `GoalPlanRevision`,
using the frozen F1 canonical profile; F1 defines no separate TaskRevision
object. It MUST materialize the frozen-F3 ResidentIdentity,
ResidentIdentityContinuityAssessment, ResidentAuthorityEpoch, prospective R9
CommandTypeDefinition and its R9 exact-descriptor materialization wrappers,
AuthenticatedCommandContext, and CommandEnvelope using their native schemas.
The CommandEnvelope binds `F4_M0_SYNTHETIC_NOOP`; borrowing either frozen F3
`LEDGER_ONLY` definition or aliasing any command-type/context/epoch ref to a
different schema rejects. An F4 extension,
F2-looking label, or F4_FP over an upstream object cannot substitute for those
bytes.

This is a direct-upstream-input closure, not a recursive replay of the complete
F1/F2/F3 mutation ledgers. A frozen upstream subject may contain a ref to an
authority action, mutation intent, time authority, accepted provisioning
source, or external governance decision that its owning frozen contract treats
as an input outside the subject/assessment bytes. Such a ref may remain a
hash-bound upstream leaf only at an explicitly enumerated `(native schema,
field)` position in the validator. It MUST retain its exact paired fingerprint
or native embedded object, MUST remain inside the verified native subject
fingerprint, and MUST NOT be consumed directly by any F4 reducer, projection,
Host authentication decision, final currentness decision, or handoff. Global
field-name exceptions and caller-selected leaves are forbidden. Every direct
F4 authority/evidence input and every ref named in the preceding materialized
set resolves through the symbol table.

The complete non-resolved leaf position set is closed and contains no other
entry:

```text
F4HostTrustRevisionV0_1R9.credential_binding_ref
HostAuthenticationAssessmentV0_1R9.challenge_ref
HostAuthenticationAssessmentV0_1R9.verification_evidence_ref
TaskPermitV0_1R9.permit_attestation_profile_ref
TaskPermitV0_1R9.permit_attestation_evidence_ref
HostWorkAcceptanceFactV0_1R9.host_acceptance_attestation_ref
HostWorkStartDispositionFactV0_1R9.host_observation_attestation_ref

ActorIdentityRevisionV0_1R8.mutation_intent_ref
PrincipalRevisionR9Effective.mutation_intent_ref
ActorPrincipalBindingRevisionR10Effective.mutation_intent_ref
AuthenticatorProfileRevisionR9Effective.mutation_intent_ref
LifecycleActionRefV0_1R8.mutation_intent_ref
LifecycleActionRefV0_1R8.action_ref
LifecycleControllerRefV0_1.controller_ref
ActorGeneralTransitionAuthorityBasisV0_1R16.identity_stewardship_assessment_ref
ActorGeneralTransitionAuthorityBasisV0_1R16.incident_policy_ref
ActorGeneralTransitionAuthorityBasisV0_1R16.provisioning_component_ref
ActorGeneralTransitionAuthorityBasisV0_1R16.provisioning_basis_ref
TransitionAuthorityBasisV0_1R9.target_relation_ref
TransitionAuthorityBasisV0_1R9.incident_policy_ref
TransitionAuthorityBasisV0_1R9.provisioning_component_ref
TransitionAuthorityBasisV0_1R9.provisioning_basis_ref
JennRootGovernanceAuthorityRefV0_1R8.source_decision_ref
AuthenticationAssessmentV0_1R15.authentication_assertion_ref
BindingActivationAssessmentV0_1R16.activation_evidence_ref
ResidentAuthorityEpochV0_1R3.witness_reservation_ref
```

The first seven are the credential/cryptographic-attestation handles already
allowed by the F4 profiles. The remainder are frozen-upstream-internal leaves
only. A non-null leaf still obeys its owning native schema's nullability,
pairing, basis-kind, and fingerprint rules. Moving a leaf to another schema or
field, using it as a direct F4 decision input, or adding any position rejects.

Every compromise-history ABSENT row
has an empty event list and
`complete_event_set_fingerprint = SHA256(JCS([domain, lineage_id,
start_sequence, end_sequence, []]))`; PRESENT has at least one resolvable
compromise event. The canonical writer resolves to the exact F3 Resident
identity. Arbitrary, last-known, truncated, different-lineage, future-watermark,
or synthetic absence evidence rejects.

`F4HostEffectTrustEligibilityAssessmentV0_1R9` retains R8 field order with R9
interface/schema name, but every current-F2 and history ref/fingerprint resolves
to the exact R9 objects. `HostAuthenticationAssessmentV0_1R9` binds the current
F2 evidence, the current Host-trust revision 2, both complete-history objects,
and the exact current Host profile. Its positive result is impossible unless all
resolved evidence passes.

The exact `HostAuthenticationAssessmentV0_1R9` field order is the R8 list with
its interface changed to `agents-os.host-authentication-assessment.v0.1-r9` and
these six fields inserted immediately after
`host_process_binding_assessment_fingerprint`, before
`effect_trust_eligibility_assessment_ref`:

```text
F2_identity_binding_evidence_ref
F2_identity_binding_evidence_fingerprint
F2_compromise_history_evidence_ref
F2_compromise_history_evidence_fingerprint
F4_compromise_history_evidence_ref
F4_compromise_history_evidence_fingerprint
```

All remaining R8 fields retain their exact relative order; the assessment
fingerprint remains last and uses `F4_FP(HostAuthenticationAssessmentV0_1R9,
preceding values)`.

`F4HostTrustRevisionV0_1R9` likewise retains the exact R8 field order, changes
only its interface to `agents-os.f4-host-trust-revision.v0.1-r9`, and uses the
R9 schema name in F4_FP. The revision-1 CREATE and revision-2 UPDATE are two
separate persisted occurrences of that schema.

## 5. Exact Jenn revocation observation and authorization totality

```yaml
JennEffectAuthorizationDecisionV0_1R9:
  interface_version: agents-os.jenn-effect-authorization-decision.v0.1-r9
  decision_ref: stable_ref
  Jenn_actor_identity_ref: stable_ref
  exact_effect_scope_ref: stable_ref
  exact_effect_scope_fingerprint: lowercase_sha256
  issued_at_utc_ms: non_negative_safe_integer
  expires_at_utc_ms: positive_safe_integer
  decision_event_sequence: non_negative_safe_integer
  result: AUTHORIZED
  canonical_fingerprint: lowercase_sha256

JennDecisionLookupAssessmentV0_1R9:
  interface_version: agents-os.jenn-decision-lookup-assessment.v0.1-r9
  assessment_ref: stable_ref
  exact_effect_scope_ref: stable_ref
  exact_effect_scope_fingerprint: lowercase_sha256
  decision_index_head_ref: stable_ref | null
  decision_index_head_fingerprint: lowercase_sha256 | null
  matched_decision_ref: stable_ref | null
  matched_decision_fingerprint: lowercase_sha256 | null
  watermark_event_sequence: non_negative_safe_integer
  outcome: PRESENT | ABSENT_PROVEN | UNAVAILABLE | INTEGRITY_CONFLICT
  assessment_fingerprint: lowercase_sha256

JennDecisionRevocationObservationV0_1R9:
  interface_version: agents-os.jenn-decision-revocation-observation.v0.1-r9
  observation_ref: stable_ref
  Jenn_decision_ref: stable_ref
  Jenn_decision_fingerprint: lowercase_sha256
  observation: NO_REVOCATION_THROUGH_WATERMARK | REVOKED
  revocation_event_ref: stable_ref | null
  revocation_event_fingerprint: lowercase_sha256 | null
  revocation_event_sequence: non_negative_safe_integer
  history_complete_through_event_sequence: non_negative_safe_integer
  canonical_writer_ref: stable_ref
  canonical_writer_fingerprint: lowercase_sha256
  result: COMPLETE
  canonical_fingerprint: lowercase_sha256
```

`NO_REVOCATION_THROUGH_WATERMARK` requires null event ref/fingerprint,
`revocation_event_sequence = 0`, and a complete history through the evaluation
watermark. `REVOKED` requires a resolvable revocation event with positive
sequence not later than both history-complete and evaluation watermarks. A
current exact-Jenn row requires the first observation. A visible revoked
observation is always `JENN_DECISION_REVOKED` and dominates simultaneous scope
mismatch, expiry, or unavailable secondary evidence. Scope mismatch then
precedes expiry. Missing is possible only from a complete decision-index
absence proof and cannot coexist with present evidence.

R9 requires exactly ten authorization-resolution rows:

```text
7 REQUIREMENT_RESOLVED rows from the R8 legal persisted matrix
1 NO_REQUIREMENT_OBJECT / MODE_INPUT_INTEGRITY_CONFLICT
1 NO_REQUIREMENT_OBJECT / MODE_INPUT_UNAVAILABLE
1 NO_REQUIREMENT_OBJECT / INVALID_INPUT
```

The three no-object rows are mandatory, have null requirement fingerprint, and
produce no requirement object. The validator evaluates every concurrent
revoked/scope/expired boolean cross-product with unavailable evidence and every
Jenn presence mask. A permit may reference only NO_SEPARATE/NOT_APPLICABLE or
EXACT/CURRENT. PROHIBITED, REJECTED, INDETERMINATE, no-object, unknown, or
caller-selected result/reason can never enter a permit.

R9 also inserts
`Jenn_decision_lookup_assessment_ref/fingerprint` immediately before
`Jenn_decision_ref/fingerprint` in the R9 authorization requirement. For
NO_SEPARATE and PROHIBITED both are null. For exact-MISSING they resolve an
`ABSENT_PROVEN` lookup while decision and revocation fields are null. For every
exact-present row they resolve `PRESENT` and the exact emitted decision. Lookup
INTEGRITY_CONFLICT or UNAVAILABLE produces the matching no-object row and no
persisted requirement.

## 6. Materialized final authority evidence

R9 adds:

```yaml
F4TrustedTimeProfileV0_1R9:
  interface_version: agents-os.f4-trusted-time-profile.v0.1-r9
  profile_ref: stable_ref
  source_kind: SYNTHETIC_MONOTONIC_FIXTURE
  time_scale: UTC_MS
  uncertainty_policy: EXACT_ZERO_UNCERTAINTY
  external_time_source: false
  production_authentication: false
  canonical_fingerprint: lowercase_sha256

EventWatermarkSnapshotV0_1R9:
  interface_version: agents-os.event-watermark-snapshot.v0.1-r9
  watermark_ref: stable_ref
  event_sequence: non_negative_safe_integer
  committed_head_set_fingerprint: lowercase_sha256
  trusted_time_utc_ms: non_negative_safe_integer
  result: COMPLETE
  canonical_fingerprint: lowercase_sha256

CanonicalIntegrityEvidenceV0_1R9:
  interface_version: agents-os.canonical-integrity-evidence.v0.1-r9
  evidence_ref: stable_ref
  reviewed_object_set_fingerprint: lowercase_sha256
  schema_registry_fingerprint: lowercase_sha256
  semantic_edge_set_fingerprint: lowercase_sha256
  watermark_ref: stable_ref
  watermark_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  result: PASS
  canonical_fingerprint: lowercase_sha256

TrustedTimeEvidenceV0_1R9:
  interface_version: agents-os.trusted-time-evidence.v0.1-r9
  evidence_ref: stable_ref
  trusted_time_profile_ref: stable_ref
  trusted_time_profile_fingerprint: lowercase_sha256
  trusted_time_utc_ms: non_negative_safe_integer
  monotonic_reading_sequence: positive_safe_integer
  watermark_ref: stable_ref
  watermark_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  result: CURRENT
  canonical_fingerprint: lowercase_sha256

F4FenceStateV0_1R9:
  interface_version: agents-os.f4-fence-state.v0.1-r9
  fence_ref: stable_ref
  scope_kind: TASK | HOST | EFFECT
  scope_ref: stable_ref
  scope_fingerprint: lowercase_sha256
  generation: positive_safe_integer
  quarantine_state: CLEAR | QUARANTINED
  head_event_sequence: non_negative_safe_integer
  watermark_ref: stable_ref
  watermark_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  result: CURRENT | REJECTED
  canonical_fingerprint: lowercase_sha256

F4FenceSnapshotV0_1R9:
  interface_version: agents-os.f4-fence-snapshot.v0.1-r9
  snapshot_ref: stable_ref
  task_fence_ref: stable_ref
  task_fence_fingerprint: lowercase_sha256
  host_fence_ref: stable_ref
  host_fence_fingerprint: lowercase_sha256
  effect_fence_ref: stable_ref
  effect_fence_fingerprint: lowercase_sha256
  watermark_ref: stable_ref
  watermark_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  result: CURRENT
  canonical_fingerprint: lowercase_sha256

AuthorityCurrentnessEvidenceV0_1R9:
  interface_version: agents-os.authority-currentness-evidence.v0.1-r9
  evidence_ref: stable_ref
  code: F1_TASK | F2_ACTOR_PRINCIPAL_BINDING | F2_RESPONSIBILITY_DELEGATION | F3_RESIDENT_COMMAND | F4_HOST_EFFECT_TRUST | POLICY | PROHIBITED_BEHAVIOR_LIST | EFFECT_AUTHORIZATION_REQUIREMENT
  subject_ref: stable_ref
  subject_fingerprint: lowercase_sha256
  subject_watermark_event_sequence: non_negative_safe_integer
  watermark_ref: stable_ref
  watermark_fingerprint: lowercase_sha256
  assessment_watermark_event_sequence: non_negative_safe_integer
  result: CURRENT | REJECTED | INDETERMINATE
  reason: CURRENT | STALE | UNAVAILABLE | INTEGRITY_FAILURE
  canonical_fingerprint: lowercase_sha256
```

The TrustedTimeEvidence profile pair resolves the one exact profile above.
This profile is constructive-witness-only and neither reads a real clock nor
authorizes a production time, authentication, provider, or runtime source.

The complete R9 witness materializes one current object for every final code:
eight authority-currentness objects, one integrity object, one trusted-time
object, and three fence states. Every `FinalAuthorityObservation` ref and
fingerprint resolves to its exact object; no label or zero digest is permitted.
The admission fence snapshot resolves all three exact fence objects. Fence
scope refs/fingerprints resolve the Task, current Host trust, and exact effect
scope respectively. Generation, quarantine, head event, time, epoch, and
watermark values equal the permit, acceptance, disposition, and handoff.

Every final evidence object resolves the same exact
`EventWatermarkSnapshotV0_1R9`; its printed watermark sequence and trusted time
equal that snapshot. No evidence event/head may be later than the snapshot.

The final assessment DAG directly depends on acceptance and all thirteen
evidence objects. Any unresolved, stale, quarantined, future, mismatched, or
unavailable evidence derives the R8 total reducer result; caller-supplied PASS is
ignored.

## 7. Effective reducers, expiry, and causal transaction

R9 changes no effective R2/R3/R5 reason order. It requires the independent
semantic validator to implement, from the normalized fields rather than fixed
positive result strings:

1. the complete R2 TaskPermit-currentness mapping and precedence, with R5/R8
   Host-trust and effect-authorization field names;
2. the complete R2 admission mapping and precedence, including prohibited
   boundary, exact effect scope, final fence snapshot, and authorization;
3. the R4/R5 effective start-disposition mapping and precedence, including
   complete final authority, Host authentication, three fences, epoch, expiry,
   secrets, attestation, and human presence.

Any proven negative dominates unavailable evidence. The exact first reason from
the inherited precedence is the only legal fingerprinted reason. A supplied
VALID, ADMITTED, or START_AUTHORITY_CURRENT whose normalized fields do not
reduce to it rejects.

R9 materializes the start reduction instead of leaving it implicit:

```yaml
HostWorkStartRecheckAssessmentV0_1R9:
  interface_version: agents-os.host-work-start-recheck-assessment.v0.1-r9
  assessment_ref: stable_ref
  acceptance_ref: stable_ref
  acceptance_fingerprint: lowercase_sha256
  final_handoff_authority_assessment_ref: stable_ref
  final_handoff_authority_assessment_fingerprint: lowercase_sha256
  trusted_time_evidence_ref: stable_ref
  trusted_time_evidence_fingerprint: lowercase_sha256
  canonical_integrity_current: PASS | REJECTED | INDETERMINATE
  final_authority_current: PASS | REJECTED | INDETERMINATE
  host_trust_current: PASS | REJECTED | INDETERMINATE
  host_authentication_current: PASS | REJECTED | INDETERMINATE
  task_fence_current: PASS | REJECTED | INDETERMINATE
  host_fence_current: PASS | REJECTED | INDETERMINATE
  effect_fence_current: PASS | REJECTED | INDETERMINATE
  execution_epoch_current: PASS | REJECTED | INDETERMINATE
  start_authority_time_current: PASS | REJECTED | INDETERMINATE
  secret_handles_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  permit_attestation_current: PASS | REJECTED | INDETERMINATE
  human_presence_current: PASS | NOT_APPLICABLE | REJECTED | INDETERMINATE
  watermark_ref: stable_ref
  watermark_fingerprint: lowercase_sha256
  watermark_event_sequence: non_negative_safe_integer
  result: CURRENT | REJECTED | INDETERMINATE
  reason: ALL_RECHECKS_PASS | INTEGRITY_FAILURE | AUTHORITY_STALE | HOST_UNAUTHENTICATED | FENCED | EPOCH_STALE | EXPIRED | SECRET_HANDLE_STALE | ATTESTATION_STALE | HUMAN_PRESENCE_STALE | OBSERVATION_UNAVAILABLE
  assessment_fingerprint: lowercase_sha256
```

Its exact rejected precedence is `INTEGRITY_FAILURE`, `AUTHORITY_STALE`,
`HOST_UNAUTHENTICATED`, `FENCED`, `EPOCH_STALE`, `EXPIRED`,
`SECRET_HANDLE_STALE`, `ATTESTATION_STALE`, then
`HUMAN_PRESENCE_STALE`. Otherwise any INDETERMINATE produces
`INDETERMINATE / OBSERVATION_UNAVAILABLE`; only all applicable PASS or valid
NOT_APPLICABLE produces `CURRENT / ALL_RECHECKS_PASS`.

`HostWorkStartDispositionFactV0_1R9` inserts the recheck assessment
ref/fingerprint immediately after its final-handoff assessment ref/fingerprint.
Disposition MUST be the exact mapping of that resolved assessment; only CURRENT
can share a transaction with a handoff.

For strict-registry completeness, these R9 effective schemas retain their exact
R8 field order except for the explicit R9 insertions already printed:

```text
TaskPermitCurrentnessAssessmentV0_1R9
HostLocalAdmissionRequestV0_1R9
HostLocalAdmissionDecisionV0_1R9
FinalAuthorityObservationV0_1R9
FinalHandoffAuthorityAssessmentV0_1R9
HostWorkAcceptanceFactV0_1R9
HostWorkStartDispositionFactV0_1R9
F4AcceptedEffectHandoffV0_1R9
```

Each changes its first interface value from `...r8` to the corresponding
`...r9` literal and changes its F4_FP exact schema name from R8 to R9. Currentness
and admission have no unprinted field insertion. Final observation and final
assessment have no unprinted insertion. Acceptance has no unprinted insertion.
Disposition inserts the start-recheck pair and transaction ID exactly where
stated. Handoff inserts the effect-scope pair and transaction ID exactly where
stated. No implementation may infer any other R9 field.

The fixed positive witness obeys:

```text
permit issuance event
  <= currentness assessment event
  <= request event
  <= decision event
  < acceptance event
  <= final-authority watermark
  < disposition event
  == handoff event
  == activation/handoff transaction event

requested_at
  <= decided_at
  <= accepted_at
  <= final trusted time
  == observed_at
  < acceptance start-authority expiry
  == handoff start-authority expiry
  <= permit expiry
```

The start-authority expiry is the minimum of permit expiry, Host-authentication
validity, exact-Jenn expiry when applicable, human-presence expiry when
applicable, and any shorter accepted Host-policy grace bound; it can never
outlive any bound deadline. Equality of
observed/final time with start-authority expiry is expired and emits no handoff.

`HostWorkStartDispositionFactV0_1R9` inserts `handoff_transaction_id`
immediately after `observation_event_sequence`.
`F4AcceptedEffectHandoffV0_1R9` inserts the same
`handoff_transaction_id` immediately before `handoff_event_sequence`. The
activation transition uses the earlier acceptance event sequence; disposition
and handoff use one later event sequence and one handoff transaction ID. A
successful disposition without its exact handoff or a
handoff outside that transaction is impossible.

## 8. Strict schema discovery, types, symbols, and removed surfaces

The R9 validator has two closed registries:
`NORMATIVE_SCHEMAS` and `WRAPPER_SCHEMAS`. It recursively visits every object
under the root before trusting fixture inventory. Any object with an
`interface_version`, any known fingerprint field, or any schema-like wrapper
MUST match exactly one registry entry including field order, field types,
nullability, closed enums, and interface. Unknown interface, unknown wrapper,
extra/missing/reordered field, invalid null, float, non-NFC string, or shadow
object rejects.

Discovered `(JSON pointer, schema name)` occurrences MUST equal the fixture
inventory exactly. Duplicate semantic objects remain separate occurrences; JCS
deduplication cannot hide them. Required counts are computed by the validator,
never accepted from fixture summary.

Recursive classification still validates the root `schema_inventory` container
and every `SchemaInventoryEntry` against closed `WRAPPER_SCHEMAS`, but those
inventory-metadata objects are the sole occurrences excluded from the set that
the inventory enumerates; otherwise enumeration would be self-referential.
Every other normative, native-upstream, and wrapper occurrence, including the
root witness object, MUST appear exactly once at its exact pointer.

R9 adds a closed symbol table. For every authority/evidence `*_ref` the witness
contains one exact binding from ref to target JSON pointer, target schema, and
target fingerprint. Duplicate refs, aliases, orphan refs, wrong schemas,
wrong paired fingerprints, wrapper targets, or unresolved authority/evidence
refs reject. Low-disclosure credential handles and cryptographic attestation
handles remain non-authority handles and are checked only under their existing
profiles; they cannot satisfy an authority ref.

```yaml
CanonicalSymbolBindingV0_1R9:
  interface_version: agents-os.canonical-symbol-binding.v0.1-r9
  symbol_ref: stable_ref
  target_exact_schema_name: closed_schema_name
  target_fingerprint: lowercase_sha256
  target_inventory_pointer: canonical_JSON_pointer
  canonical_fingerprint: lowercase_sha256

CrossObjectSymbolTableV0_1R9:
  interface_version: agents-os.cross-object-symbol-table.v0.1-r9
  bindings: sorted_unique_CanonicalSymbolBindingV0_1R9
  binding_set_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256
```

The symbol table is itself strictly discovered and fingerprinted. Every binding
target pointer is in the independently discovered inventory and the pointed
object's verified native fingerprint equals the target fingerprint. Upstream
F1/F2/F3 targets retain their native fingerprint domains; R9 MUST NOT rewrite
them with F4_FP. When a native upstream schema represents its fingerprint as a
`FingerprintEnvelope`, `CanonicalSymbolBinding.target_fingerprint` equals that
envelope's `digest_lowercase_hex`; the validator first verifies the complete
native envelope, algorithm, canonicalization-contract version, and digest over
the target bytes. Extracting the digest never discards or replaces envelope
verification.

The recursive removed set is exactly the R8 field set plus:

```text
host_identity_ref
host_identity_fingerprint
Jenn_authorization
```

The removed values are exactly:

```text
ACCEPTANCE_MISSING
agents-os.host-identity-revision.v0.1
```

They reject anywhere outside the immutable R1 base-integrity bytes, including
wrappers and shadow objects. Any R8 interface for an object explicitly replaced
by R9 is also a removed value in the R9 effective tree; it remains only in
immutable lineage files, never as an R9 object.

## 9. Independent evidence and mutation minimum

R9 uses four new subjects: this amendment, independent fixture builder, fixed
fixture, and independent validator. The validator neither imports the builder
nor builds an expected fixture. Every semantic mutation re-signs all non-target
parents, IDs, refs, inventory entries, symbol bindings, and DAG nodes.

The fixed suite covers at least:

```text
all permit/invocation/acceptance/observation/handoff derived IDs and refs
Host profile ref-only, fingerprint-only, and dual mismatch
Actor/Host-trust revision swap and implicit equalization
missing, duplicate, extra, stale, unresolved, and wildcard source roles
scope mismatch after full re-sign
arbitrary operation and resource containment
all 126 Jenn mixed masks and 3 mandatory no-object rows
all concurrent revoked/scope/expiry/unavailable combinations
synthetic/truncated/different-lineage compromise absence
unresolved final evidence and each stale/quarantined fence
every inherited currentness, admission, and start negative class
combined rejected plus unavailable precedence
every event/time/expiry inequality and transaction split
CREATE null-head and UPDATE CAS/action/basis failures
unknown/shadow/extra/missing/type/nullability schema objects
every removed field and value
missing base edge and nonzero effect/provider/raw-secret count
```

The fresh review unit is all twenty-nine R1-R9 subjects. Only Jenn may accept or
freeze it. Nothing starts F5/F6 or authorizes implementation, runtime, database,
service, Host, provider, production authentication, credentials, keys, physical
effects, commit, push, merge, release, or deploy.

## 10. Final external-boundary correction

This section closes the independently reproduced boundary failures in the
earlier R9 working bytes. It replaces every conflicting claim in Sections 2-9.

### 10.1 F4 is an upstream-assessment consumer

F4 does not create, reconstruct, or reduce F1, F2, or F3 authority. In
particular, F4 MUST NOT:

```text
construct an F1 Task or decide F1 Task currentness
construct an F2 Actor, Principal, Binding, responsibility, or delegation
replay an F2 lifecycle, mutation intent, CAS, provisioning, or assessment reducer
construct an F3 Resident, authority epoch, Command definition, context, intake,
  replay entry, or CommandEnvelope
decide an F3 Command is COMMITTED
infer effect authority from Actor class, role name, relationship, trust,
  urgency, historical success, Green/Yellow/Red, or P0-P3
```

The only accepted upstream interface is an owner-issued receipt:

```yaml
UpstreamAuthorityAssessmentReceiptV0_1R9:
  interface_version: agents-os.upstream-authority-assessment-receipt.v0.1-r9
  receipt_ref: stable_ref
  receipt_revision: positive_safe_integer
  role: F1_TASK_SCOPE | F2_ACTOR_BINDING | F2_RESPONSIBILITY | F2_DELEGATION | F3_COMMAND
  owner_phase: F1 | F2 | F3
  owner_contract_ref: stable_ref
  owner_contract_fingerprint: lowercase_sha256
  owner_result_profile_ref: stable_ref
  owner_result_profile_fingerprint: lowercase_sha256
  responsibility_route: NOT_APPLICABLE | DIRECT_RESPONSIBILITY | DELEGATED_RESPONSIBILITY
  assessment_schema_name: closed_owner_schema_name
  assessment_ref: stable_ref
  assessment_fingerprint: lowercase_sha256
  subject_schema_name: closed_owner_schema_name
  subject_ref: stable_ref
  subject_revision: positive_safe_integer
  subject_fingerprint: lowercase_sha256
  owner_result: TASK_SCOPE_CURRENT | BINDING_CURRENT | RESPONSIBILITY_CURRENT | DELEGATION_CURRENT | COMMAND_COMMITTED_CURRENT
  owner_head_event_sequence: non_negative_safe_integer
  assessed_at_event_sequence: non_negative_safe_integer
  resolved_at_watermark_event_sequence: non_negative_safe_integer
  owner_currentness: CURRENT | STALE | INDETERMINATE
  authority_atom_set_mode: GATE_ONLY | OWNER_ISSUED_ATOM_SET
  authority_atoms: sorted_unique_EffectAuthorityAtomV0_1R9
  authority_atom_set_fingerprint: lowercase_sha256
  environment: NON_PRODUCTION_REVIEW | SYNTHETIC_TEST | PRODUCTION
  authority_eligible: boolean
  canonical_fingerprint: lowercase_sha256
```

The owning phase creates the receipt and hash-binds its complete authority-atom
set. F4 verifies only exact schema/role,
subject and assessment ref/fingerprint equality, accepted frozen owner lineage,
the role-specific result literal, `owner_currentness = CURRENT`, and
`owner_head_event_sequence <= assessed_at_event_sequence <=
resolved_at_watermark_event_sequence`. F4 does not reproduce the owner reducer.
`STALE`, `INDETERMINATE`, unavailable, conflicting, unknown, future-watermark,
wrong-lineage, or synthetic authority inputs are non-issuable.

`F2_ACTOR_BINDING` is gate-only: it has
`authority_atom_set_mode = GATE_ONLY`, an empty `authority_atoms` list, and the
canonical empty-set fingerprint. Scope-bearing roles use
`OWNER_ISSUED_ATOM_SET` and a non-empty sorted-unique atom list. The atom-set
fingerprint is:

```text
SHA256(JCS([
  "agents-os.owner-issued-authority-atom-set.v0.1-r9",
  sorted_unique(authority_atoms[*].authority_tuple_fingerprint)
]))
```

Each role has exactly one accepted normalized result:

```text
F1_TASK_SCOPE       -> TASK_SCOPE_CURRENT
F2_ACTOR_BINDING    -> BINDING_CURRENT
F2_RESPONSIBILITY   -> RESPONSIBILITY_CURRENT
F2_DELEGATION       -> DELEGATION_CURRENT
F3_COMMAND          -> COMMAND_COMMITTED_CURRENT
```

The role/owner/result/route matrix is exact:

```text
F1_TASK_SCOPE       -> F1 -> TASK_SCOPE_CURRENT       -> NOT_APPLICABLE
F2_ACTOR_BINDING    -> F2 -> BINDING_CURRENT          -> NOT_APPLICABLE
F2_RESPONSIBILITY   -> F2 -> RESPONSIBILITY_CURRENT   -> DIRECT_RESPONSIBILITY | DELEGATED_RESPONSIBILITY
F2_DELEGATION       -> F2 -> DELEGATION_CURRENT       -> NOT_APPLICABLE
F3_COMMAND          -> F3 -> COMMAND_COMMITTED_CURRENT -> NOT_APPLICABLE
```

`F2_DELEGATION` is required if and only if the owner-issued
`F2_RESPONSIBILITY` receipt says `DELEGATED_RESPONSIBILITY`. F4 cannot infer or
select this route. The synthetic receipt deliberately says
`DELEGATED_RESPONSIBILITY`, so its missing delegation receipt is a reproducible
fail-closed input rather than a fixture-authored policy choice.

The accepted owner result-profile ref/fingerprint hash-binds this entire matrix
and is part of the receipt. It
must resolve through the owning phase's accepted manifest. Unknown, added,
cross-role, or locally interpreted result literals are rejected.

The receipt canonical fingerprint covers the mode, every embedded complete
atom, and the atom-set fingerprint. F4 MUST NOT construct, augment, union,
translate, or replace that list. An atom set supplied outside the owner-issued
receipt is not authority. Until each required owning phase independently
accepts and emits this receipt interface, a real positive handoff is
non-issuable.

The formula above is the prospective production interface requirement. The R9
synthetic fixture substitutes the non-authority domain-separated form
`["agents-os.f4-r9-synthetic-witness.v0.1",
"owner-issued-atom-set", tuple_fingerprints]`. Its result is deliberately not
interchangeable with a production owner-issued atom-set fingerprint.

For a production admission, every required receipt has
`environment = PRODUCTION` and `authority_eligible = true`. A synthetic receipt
always has `environment = SYNTHETIC_TEST` and `authority_eligible = false`.
Changing either value, re-signing the receipt, or copying it outside the
fixture cannot turn it into owner-issued authority because production resolves
the subject and assessment against the owning phase's canonical writer and
accepted manifest.

The effective R9 fixture and validator therefore contain no native F1/F2/F3
subject or assessment object and no F4 implementation of an F1/F2/F3 reducer.
All earlier R9 native-materialization and direct-upstream-reduction requirements
are removed from the effective fixture profile.

Section 10 also narrows the earlier local-symbol rule. Top-level fixture objects
and every locally dereferenced ref/fingerprint pair require one exact symbol
binding. External owner commitments (`owner_contract_ref`, `assessment_ref`,
`subject_ref`, owner result-profile refs, canonical-writer refs/pointers, and
`resource_ref`, operation/resource registry refs, narrowing source-contract,
source-input, source-result-profile refs, and the final transaction ref) are intentionally not
materialized as native objects. In the
synthetic fixture they must use the `synthetic-f4-r9:` namespace and be
hash-bound by their enclosing receipt/observation/atom. In production they must
resolve through the named accepted canonical writer and accepted manifest;
unavailable or mismatching external commitments fail closed. This exception
does not permit an unbound local authority object or caller-supplied PASS.

The synthetic final transaction ref is an external non-authority transaction
commitment hash-bound by the snapshot. A production transaction ref must
resolve through the canonical transaction writer in the same transaction as
the final snapshot and future handoff; an unresolved or mismatching transaction
commitment is non-executable.

A receipt or governance assessment cannot prove its own currentness. Every
admission attempt consumes a canonical-writer observation:

```yaml
AuthorityInputCurrentnessObservationV0_1R9:
  interface_version: agents-os.authority-input-currentness-observation.v0.1-r9
  observation_ref: stable_ref
  input_kind: OWNER_RECEIPT | SCOPE_NARROWING_RECEIPT | PBL_ASSESSMENT | AUTHORIZATION_POLICY_ASSESSMENT | JENN_EXACT_DECISION | OPERATION_REGISTRY | RESOURCE_KIND_REGISTRY | EFFECT_CONSTRAINT
  input_ref: stable_ref
  input_fingerprint: lowercase_sha256
  canonical_writer_ref: stable_ref
  canonical_writer_fingerprint: lowercase_sha256
  canonical_latest_pointer_ref: stable_ref
  observed_latest_input_ref: stable_ref
  observed_latest_input_fingerprint: lowercase_sha256
  observed_owner_head_event_sequence: non_negative_safe_integer
  observed_latest_pointer_revision: positive_safe_integer
  observed_at_event_sequence: non_negative_safe_integer
  observation_result: CURRENT | STALE | INDETERMINATE
  environment: NON_PRODUCTION_REVIEW | SYNTHETIC_TEST | PRODUCTION
  authority_eligible: boolean
  canonical_fingerprint: lowercase_sha256
```

This observation is emitted by the input's accepted canonical writer from its
live canonical-latest lookup; it is not authored or inferred by F4. `CURRENT`
requires the observed latest ref/fingerprint to equal the bound input and the
observed writer head to be the head used by the final admission snapshot. The
final disposition/handoff transaction re-resolves every required observation
and rejects any head advance, pointer revision change, mismatch, unavailable
writer, stale result, or indeterminate result. An older internally consistent
receipt, PBL assessment, policy assessment, or Jenn decision therefore cannot
remain current by self-assertion.

The operation registry, resource-kind registry, and exact constraint each have
their own observation with `input_kind = OPERATION_REGISTRY`,
`RESOURCE_KIND_REGISTRY`, or `EFFECT_CONSTRAINT`. All three are mandatory in
the final snapshot. A registry or constraint writer-head/pointer advance,
unknown entry, removal, revocation, mismatch, or unavailable lookup fails
closed even when every owner and narrowing receipt remains internally current.

The complete final lookup is bound as one snapshot:

```yaml
FinalAdmissionCurrentnessSnapshotV0_1R9:
  interface_version: agents-os.final-admission-currentness-snapshot.v0.1-r9
  snapshot_ref: stable_ref
  required_input_roles: sorted_unique_closed_roles
  required_input_set_basis_refs: sorted_unique_stable_refs
  required_input_set_basis_fingerprints: basis_ref_ordered_lowercase_sha256
  required_input_set_basis_fingerprint: lowercase_sha256
  present_input_refs: sorted_unique_stable_refs
  missing_required_input_roles: sorted_unique_closed_roles
  observation_refs: input_ordered_stable_refs
  observation_fingerprints: input_ordered_lowercase_sha256
  observed_writer_head_event_sequences: input_ordered_non_negative_safe_integers
  observation_set_fingerprint: lowercase_sha256
  final_transaction_ref: stable_ref
  final_transaction_fingerprint: lowercase_sha256
  transaction_binding_rule: EXACT_SAME_TRANSACTION
  final_snapshot_event_sequence: non_negative_safe_integer
  snapshot_result: CURRENT | STALE | INDETERMINATE | NOT_AUTHORITY_ELIGIBLE
  environment: NON_PRODUCTION_REVIEW | SYNTHETIC_TEST | PRODUCTION
  authority_eligible: boolean
  canonical_fingerprint: lowercase_sha256
```

`required_input_roles` is derived from and hash-bound to the responsibility
route receipt, authorization policy assessment, exact intersection assessment,
PBL assessment, exact scope, and registry-bound atom. The two basis arrays are
ordered by basis ref; their set fingerprint is
`SHA256(JCS([synthetic_base_domain, "required-input-basis",
required_input_roles, basis_refs, basis_fingerprints]))` in the synthetic
profile. A caller cannot omit a conditional Delegation/Jenn role or a mandatory
gate by editing only the snapshot.

The three parallel observation lists are ordered by `present_input_refs`.
`observation_set_fingerprint` covers every input ref, observation ref,
observation fingerprint, and observed writer head as
`SHA256(JCS([synthetic_base_domain, "observation-set", present_input_refs,
missing_required_input_roles,
observation_refs, observation_fingerprints,
observed_writer_head_event_sequences]))` in the synthetic profile. Production `CURRENT`
requires an empty `missing_required_input_roles`, one canonical-writer
observation for every required input, no extras,
all results `CURRENT`, all observations at or before the final snapshot event,
and a same-transaction re-read proving each writer head/pointer unchanged. The
handoff binds this exact snapshot ref/fingerprint. The synthetic fixture emits
only `NOT_AUTHORITY_ELIGIBLE / SYNTHETIC_TEST / authority_eligible = false`;
because its builder creates both sides, it is schema constructibility evidence,
not independent canonical-writer currentness evidence.

When exact Jenn authorization is required, the required input set contains two
distinct roles: `JENN_EXACT_DECISION` for the decision canonical-latest lookup
and `JENN_EXACT_DECISION_SCOPE` for its monotonic tuple narrowing receipt. Both
receive independent observations in the same final transaction; either one
missing, stale, revoked, mismatched, or indeterminate blocks admission. The
snapshot's `final_transaction_ref/fingerprint` is unique to that attempt, and a
future handoff must bind the same values with
`transaction_binding_rule = EXACT_SAME_TRANSACTION`. Replaying an older
snapshot in a new transaction is non-executable.

In the synthetic profile the transaction fingerprint is
`SHA256(JCS([synthetic_base_domain, "final-transaction",
final_transaction_ref, required_input_set_basis_fingerprint,
observation_set_fingerprint, final_snapshot_event_sequence]))`. The production
profile additionally requires the canonical transaction writer and one-time
consumption ledger; R9 does not implement either runtime surface.

### 10.2 Prospective F3 interface is an unaccepted dependency

R9 declares only this requirement:

```yaml
ProspectiveF3InterfaceRequirementV0_1R9:
  interface_version: agents-os.prospective-f3-interface-requirement.v0.1-r9
  requirement_ref: stable_ref
  owner: F3
  required_interface_kind: CLOSED_EFFECT_INTENT_COMMAND_TYPE
  required_effect_authority_atom_schema_fingerprint: lowercase_sha256
  required_intake_result: COMMITTED
  status: UNACCEPTED_DOWNSTREAM_REQUIREMENT
  usable_in_runtime: false
  synthetic_fixture_only: true
  authority_eligible: false
  canonical_fingerprint: lowercase_sha256
```

F4 does not define an F3 registry revision, CommandTypeDefinition, payload or
reducer descriptor, AuthenticatedCommandContext, replay state, intake state, or
CommandEnvelope. The effective R9 fixture contains no `COMMITTED` F3 object and
no `F3_COMMAND` authority receipt or projection. The requirement cannot satisfy
permit issuance. A real positive handoff remains impossible until F3
independently accepts and freezes the interface and its canonical writer emits
a hash-bound, current, authority-eligible `F3_COMMAND` receipt.

`required_effect_authority_atom_schema_fingerprint` covers a closed canonical
schema-profile descriptor, not merely a schema name or field list. The
descriptor includes the interface version, ordered fields, field types,
closed-enum constraints, nullability, canonical fingerprint rule, tuple
fingerprint rule, and synthetic/production domain rule. Any omitted or changed
profile component changes the fingerprint. This requirement fingerprint is
still only an unaccepted dependency and never proves F3 acceptance.

### 10.3 Authority is an intersection of coupled atoms

R9 replaces every separate operation/resource set used for authority decisions
with one atomic tuple:

```yaml
EffectConstraintV0_1R9:
  interface_version: agents-os.effect-constraint.v0.1-r9
  constraint_ref: stable_ref
  payload_schema_fingerprint: lowercase_sha256
  external_effect_allowed: boolean
  provider_call_allowed: boolean
  raw_secret_allowed: boolean
  requires_human_presence: boolean
  not_before_utc_ms: non_negative_safe_integer
  expires_at_utc_ms: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256

EffectAuthorityAtomV0_1R9:
  interface_version: agents-os.effect-authority-atom.v0.1-r9
  atom_ref: stable_ref
  operation_registry_ref: stable_ref
  operation_registry_fingerprint: lowercase_sha256
  operation_kind: closed_operation
  resource_kind_registry_ref: stable_ref
  resource_kind_registry_fingerprint: lowercase_sha256
  resource_kind: closed_resource_kind
  resource_ref: stable_ref
  constraint_ref: stable_ref
  constraint_fingerprint: lowercase_sha256
  authority_tuple_fingerprint: lowercase_sha256
  canonical_fingerprint: lowercase_sha256

F4SyntheticExactEffectScopeV0_1R9:
  interface_version: agents-os.f4-synthetic-exact-effect-scope.v0.1-r9
  scope_ref: synthetic-f4-r9:stable_ref
  effect_authority_atom_ref: stable_ref
  effect_authority_atom_fingerprint: lowercase_sha256
  effect_authority_tuple_fingerprint: lowercase_sha256
  environment: SYNTHETIC_TEST
  authority_eligible: false
  canonical_fingerprint: lowercase_sha256

```

An atom is equal only when the complete
`(operation_registry_fingerprint, operation_kind,
resource_kind_registry_fingerprint, resource_kind, resource_ref,
constraint_fingerprint)` tuple is equal. `authority_tuple_fingerprint` is

```text
SHA256(JCS([
  "agents-os.effect-authority-tuple.v0.1-r9",
  operation_registry_fingerprint,
  operation_kind,
  resource_kind_registry_fingerprint,
  resource_kind,
  resource_ref,
  constraint_fingerprint
]))
```

It excludes local `atom_ref`, registry refs, and `constraint_ref`, while binding
the canonical registry fingerprints that close both vocabularies. Unknown,
unavailable, mismatching, or non-current registry entries reject. The atom
`canonical_fingerprint` still covers all provenance and fields. Effective
authority is the set intersection of complete `authority_tuple_fingerprint`
values across the owner-issued atom sets embedded in every required
scope-bearing receipt. Gate-only receipts participate only as mandatory
currentness gates and never add an atom. Operation and resource
sets are never intersected separately. Adding an owner-issued receipt or proof
can only preserve or shrink the tuple set. Union, wildcard, cross-product,
component-wise
mixing, caller-supplied PASS, unknown input, missing role, duplicate alias, or
an empty required intersection cannot issue a permit.

As with the atom-set fingerprint, the synthetic fixture uses
`["agents-os.f4-r9-synthetic-witness.v0.1", "authority-tuple", ...]` in place
of the prospective production domain. A synthetic tuple fingerprint cannot be
reused as production authority.

Example: authority for `(read, A, constraint-1)` plus authority for
`(write, B, constraint-2)` does not create `(read, B)` or `(write, A)`.
Constraint objects resolve and are reduced monotonically; an opaque constraint
digest is not authority.

An exact Jenn decision, when independently required by policy, can only
intersect the already-effective atom set. It cannot add an atom absent from the
upstream intersection.

Policy, Host, and conditional Jenn inputs use a second canonical-writer receipt
whose only semantic operation is monotonic narrowing:

```yaml
EffectScopeNarrowingReceiptV0_1R9:
  interface_version: agents-os.effect-scope-narrowing-receipt.v0.1-r9
  receipt_ref: stable_ref
  receipt_revision: positive_safe_integer
  role: POLICY_SCOPE | HOST_CAPABILITY_RESOURCE_SCOPE | JENN_EXACT_DECISION_SCOPE
  owner_kind: POLICY_CANONICAL_WRITER | HOST_TRUST_CANONICAL_WRITER | JENN_DECISION_CANONICAL_WRITER
  source_contract_ref: stable_ref
  source_contract_fingerprint: lowercase_sha256
  source_input_ref: stable_ref
  source_input_fingerprint: lowercase_sha256
  source_result_profile_ref: stable_ref
  source_result_profile_fingerprint: lowercase_sha256
  source_result: CURRENT_SCOPE_CONSTRAINT
  authority_atoms: sorted_unique_EffectAuthorityAtomV0_1R9
  authority_atom_set_fingerprint: lowercase_sha256
  owner_head_event_sequence: non_negative_safe_integer
  evaluated_at_event_sequence: non_negative_safe_integer
  resolved_at_watermark_event_sequence: non_negative_safe_integer
  environment: NON_PRODUCTION_REVIEW | SYNTHETIC_TEST | PRODUCTION
  authority_eligible: boolean
  canonical_fingerprint: lowercase_sha256
```

Each receipt is emitted by the named accepted canonical writer and receives a
live `AuthorityInputCurrentnessObservationV0_1R9` with
`input_kind = SCOPE_NARROWING_RECEIPT`. F4 cannot author or augment these sets.
The role/owner matrix is exact:

```text
POLICY_SCOPE                   -> POLICY_CANONICAL_WRITER
HOST_CAPABILITY_RESOURCE_SCOPE -> HOST_TRUST_CANONICAL_WRITER
JENN_EXACT_DECISION_SCOPE       -> JENN_DECISION_CANONICAL_WRITER
```

The source result-profile fingerprint covers this matrix and the only accepted
normalized result, `CURRENT_SCOPE_CONSTRAINT`; cross-role owner values or any
other result reject.
`POLICY_SCOPE` and `HOST_CAPABILITY_RESOURCE_SCOPE` are always required. When
the separate policy assessment says
`EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED`,
`JENN_EXACT_DECISION_SCOPE` is also required and must be issued by the Jenn
decision canonical writer for the same exact scope. When policy says no
separate Jenn authorization is required, the Jenn narrowing role is absent;
its absence does not add scope. Every narrowing set is intersected with the
already-effective upstream tuple set. A narrowing receipt can preserve or
remove tuples but can never introduce an effective tuple absent upstream.

The synthetic fixture includes non-authority Policy and Host narrowing
receipts for the hypothetical tuple. Because its policy requires exact Jenn
authorization and no Jenn narrowing receipt exists, the intersection remains
`NOT_AUTHORITY_ELIGIBLE`.

The synthetic fixture makes its incomplete intersection explicit:

```yaml
SyntheticAuthorityIntersectionAssessmentV0_1R9:
  interface_version: agents-os.synthetic-authority-intersection-assessment.v0.1-r9
  assessment_ref: synthetic-f4-r9:stable_ref
  required_scope_roles: sorted_unique_closed_roles
  present_scope_roles: sorted_unique_closed_roles
  missing_scope_roles: sorted_unique_closed_roles
  source_receipt_refs: role_ordered_stable_refs
  source_receipt_fingerprints: role_ordered_lowercase_sha256
  source_atom_set_fingerprints: role_ordered_lowercase_sha256
  intersection_tuple_fingerprints: sorted_unique_lowercase_sha256
  intersection_set_fingerprint: lowercase_sha256
  result: NOT_AUTHORITY_ELIGIBLE
  environment: SYNTHETIC_TEST
  authority_eligible: false
  canonical_fingerprint: lowercase_sha256
```

The parallel source lists are ordered by `present_scope_roles`. For the fixed
synthetic policy and delegated-responsibility route, `required_scope_roles` is
exactly `F1_TASK_SCOPE`, `F2_DELEGATION`, `F2_RESPONSIBILITY`, `F3_COMMAND`,
`HOST_CAPABILITY_RESOURCE_SCOPE`, `JENN_EXACT_DECISION_SCOPE`, and
`POLICY_SCOPE`. The assessment must show missing `F2_DELEGATION`, `F3_COMMAND`,
and `JENN_EXACT_DECISION_SCOPE`; a non-empty intersection of
the present synthetic sets does not override either missing role or any
`authority_eligible = false` input.

For this synthetic profile, `intersection_set_fingerprint` is the hash of
`[synthetic_base_domain, "intersection-set",
sorted_unique(intersection_tuple_fingerprints)]`. The witness
`reducer_trace_fingerprint` is the hash of
`[synthetic_base_domain, "reducer-trace",
operation_resource_constraint_currentness_fingerprints,
receipt_fingerprints_in_fixture_role_order,
currentness_observation_fingerprints_in_the_same_role_order,
narrowing_receipt_fingerprints_in_role_order,
narrowing_currentness_fingerprints_in_role_order,
intersection_assessment_fingerprint, currentness_snapshot_fingerprint, PBL_fingerprint,
PBL_currentness_fingerprint, policy_fingerprint,
policy_currentness_fingerprint, prospective_requirement_fingerprint,
"NOT_AUTHORITY_ELIGIBLE"]`. Every component resolves to a local object; the
trace is not a caller-supplied PASS label.

### 10.4 PBL is veto-only

R9 replaces any earlier PBL-derived authorization mode with:

```yaml
ProhibitedBoundaryAssessmentV0_1R9Final:
  interface_version: agents-os.prohibited-boundary-assessment.v0.1-r9-final
  assessment_ref: stable_ref
  exact_effect_scope_ref: stable_ref
  exact_effect_scope_fingerprint: lowercase_sha256
  prohibited_behavior_list_revision: stable_ref
  evaluated_rule_set_fingerprint: lowercase_sha256
  matched_rule_ids: sorted_unique_stable_refs
  evaluation_result: PROHIBITED_MATCH | NO_PROHIBITED_MATCH | INDETERMINATE
  evaluated_at_event_sequence: non_negative_safe_integer
  canonical_fingerprint: lowercase_sha256

EffectAuthorizationPolicyAssessmentV0_1R9:
  interface_version: agents-os.effect-authorization-policy-assessment.v0.1-r9
  assessment_ref: stable_ref
  exact_effect_scope_ref: stable_ref
  exact_effect_scope_fingerprint: lowercase_sha256
  policy_bundle_revision: stable_ref
  authorization_requirement: NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED | EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED
  assessed_at_event_sequence: non_negative_safe_integer
  result: CURRENT | STALE | INDETERMINATE
  canonical_fingerprint: lowercase_sha256
```

`PROHIBITED_MATCH` vetoes admission. `INDETERMINATE`, missing rules, unavailable
PBL, conflicting evaluation, or incomplete rule-set coverage fail closed.
`NO_PROHIBITED_MATCH` proves only that no current prohibition matched; it does
not create an atom, responsibility, capability, permission, authorization mode,
permit, or handoff. Jenn-authorization requirement comes only from the separate
current policy assessment. PBL result never selects that mode.

Admission requires all of the following independently:

```text
all required owner-issued upstream receipts current and authority-eligible
one non-empty exact coupled-atom intersection containing the requested atom
current Host trust/authentication receipt and current fences
PBL evaluation_result = NO_PROHIBITED_MATCH
authorization policy assessment CURRENT
exact current Jenn decision when the policy requires it
current time, expiry, integrity, replay, and one-time-consumption conditions
```

No item substitutes for another. Relationship, trust, urgency, historical
success, Actor class, Task label, Green/Yellow/Red, or P0-P3 cannot alter effect
authority.

### 10.5 Synthetic constructibility is not authority

The R9 M0-A artifact is replaced by:

```yaml
F4SyntheticHandoffConstructibilityWitnessV0_1R9:
  interface_version: agents-os.f4-synthetic-handoff-constructibility-witness.v0.1-r9
  witness_ref: synthetic-f4-r9:stable_ref
  witness_namespace: synthetic-f4-r9
  environment: SYNTHETIC_TEST
  fingerprint_domain: agents-os.f4-r9-synthetic-witness.v0.1
  prospective_f3_requirement_ref: stable_ref
  prospective_f3_requirement_fingerprint: lowercase_sha256
  hypothetical_effect_atom_ref: stable_ref
  hypothetical_effect_atom_fingerprint: lowercase_sha256
  intersection_assessment_ref: stable_ref
  intersection_assessment_fingerprint: lowercase_sha256
  currentness_snapshot_ref: stable_ref
  currentness_snapshot_fingerprint: lowercase_sha256
  reducer_trace_fingerprint: lowercase_sha256
  claim_state: FIXTURE_ONLY
  authority_eligible: false
  runtime_consumable: false
  recovery_importable: false
  physical_effect_boundary: NOT_EXECUTABLE
  terminal_outcome: NOT_EXECUTED
  external_effect_count: 0
  provider_call_count: 0
  raw_secret_count: 0
  canonical_fingerprint: lowercase_sha256
```

The fixture uses only the `synthetic-f4-r9:` namespace and `SYNTHETIC_TEST`
environment. Every fixture-generated fingerprint is separated under the single
base domain `agents-os.f4-r9-synthetic-witness.v0.1`; schema, tuple, atom-set,
symbol-set, reducer-trace, and evidence-node hashes use distinct second-element
tags under that base rather than an additional authority domain. It contains no
production `TaskPermit`, `TaskPermitIssuanceFact`, `HostWorkAcceptanceFact`,
`HostWorkStartDispositionFact`, or `F4AcceptedEffectHandoff` occurrence. It
contains no native F1/F2/F3 subject, assessment, Command, intake, or replay
occurrence. Synthetic inputs are always `authority_eligible = false`.
The synthetic PBL and policy assessments bind the exact synthetic scope object
above; they never alias an atom, receipt, or prospective requirement as an
EffectScope.

The fixture assertions are exactly:

```yaml
accepted_handoff_count: 0
synthetic_constructibility_witness_count: 1
runtime_consumable_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

A production validator, recovery path, importer, F5 consumer, Host, or runtime
MUST reject the synthetic namespace, environment, fingerprint domain, witness
schema, prospective requirement, and any receipt with
`authority_eligible = false`. Copying, re-signing, renaming, or replaying a
synthetic object cannot convert it to production authority; production still
requires independently resolved owner-issued receipts from accepted canonical
writers. The fixture contains no F4-created `AuthorityAtomProjection`; atom
occurrences exist only as the canonical hypothetical atom and byte-identical
copies embedded in synthetic owner receipts. The fixture does not prove runtime readiness or a positive operational
handoff. It proves only that the closed tuple/intersection, veto, policy, and
fail-closed reducers are structurally constructible without effects.

### 10.6 Required independent attacks

The effective R9 validator and fresh reviewer MUST cover at least:

```text
old Actor assessment with caller-side ACTIVE inference -> reject
INDETERMINATE Binding receipt -> reject
F4 reconstruction of any owner reducer or native owner object -> reject
prospective F3 requirement changed to accepted, wrapped as a COMMITTED F3 object,
  or used as F3 authority -> reject
synthetic F3 or F4 object presented to production profile -> reject
synthetic witness copied, re-signed, recovered, or imported -> reject
separate operation/resource intersection or Cartesian cross-pair -> reject
atom supplied by an F4-created projection or outside an owner receipt -> reject
owner receipt atom-set or tuple fingerprint mismatch/augmentation -> reject
unknown, missing, conflicting, stale, or duplicate authority atom -> reject
PBL NO_PROHIBITED_MATCH with missing upstream authority -> reject
PBL NO_PROHIBITED_MATCH with required Jenn decision absent -> reject
Jenn decision for resource A applied to resource B -> reject
stale owner or Jenn watermark -> reject
old receipt/PBL/policy whose canonical-latest pointer or writer head advanced -> reject
Actor class, relationship, trust, urgency, historical success, Task label,
  Green/Yellow/Red, or P0-P3 changing admission -> reject
any UNKNOWN or unavailable input defaulting to pass -> reject
```

The effective R9 validator MUST fail if any native F1/F2/F3 object, prospective
F3 accepted/committed object, standard accepted handoff, separate authority
operation/resource set, PBL-derived positive authorization mode, production
namespace, or nonzero effect/provider/secret count appears anywhere in the
fixture, including wrappers and shadow objects.

### 10.7 Gate result

R9 may be reviewed only as a semantic, synthetic-non-authority constructibility
package. It is not positive operational handoff evidence. A real accepted
handoff remains blocked on an independently accepted F3 interface and
owner-issued current receipts. Nothing in R9 authorizes reopening F3,
implementation, F5, runtime, Host activation, provider/service/database work,
production authentication, commit, push, merge, release, or deploy.
