# AGENTS OS F4 TaskPermit, Host Authentication, and Effect Admission v0.1 R8 Amendment Draft

Status: author-closed review subject; not accepted or frozen  
Date: 2026-07-16  
Base R7 SHA-256: `bf0ec245382e1b9315faf946927464efc97223c4b2581761895cd4e09f6d533c`  
Blocking R7 review SHA-256: `2269974576054ef7ed6def87e649876c3e874fef17b61525cbb10735829f3025`

## 1. Scope and precedence

R8 closes only `F4-R7-FULL-ATOMIC-IR-B01` through `B07`. Effective order is
R8, R7, R6, R5, R4, R3, R2, R1. All twenty-one R1-R7 subjects remain
immutable. The effective literal is
`F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R8_ATOMIC_BUNDLE`.

R8 changes no F1, F2, or F3 lifecycle result, grants no F5 authority, and does
not authorize implementation or any real Host or effect.

## 2. One canonical effective schema and fingerprint profile

R8 replaces every earlier generic or object-specific F4 canonical, assessment,
decision, and fact fingerprint formula, including the R6 disposition and
authority-source exceptions, with exactly:

```text
F4_FP(exact_schema_name, ordered_values) =
  SHA256(JCS(["agents-os.f4-fingerprint.v0.1:" + exact_schema_name,
              ...ordered_values]))
```

`ordered_values` is every field before the declared fingerprint field in the
exact order below. The fingerprint field itself is excluded. Interface-version
strings are ordinary first field values where printed. No interface version,
wrapper kind, filename, Rust type, or caller-selected label may substitute for
`exact_schema_name`. Set and derived-ID formulas printed in this amendment are
separate formulas and MUST NOT be used as object fingerprint domains. The R6
capability-source and resource-source set formulas retain their exact printed
`v0.1-r6` domains; R8 changes their entry objects, not those set domains.

The following registry is complete for every changed or new R8 fingerprinted
object. A name not listed here cannot be emitted as an R8 object. The unchanged
embedded R1 schemas `F4TaskAuthorityBindingV0_1`,
`F4ActorAuthorityBindingV0_1`, `F4ResidentCommandBindingV0_1`,
`HumanPresenceBindingV0_1`, `SecretHandleBindingV0_1`, and
`F4FenceStateV0_1` retain their exact R1 fields but use this same `F4_FP`
profile. `PermitInvocationIdentityV0_1`, `TaskPermitIssuanceFactV0_1`, and
`TaskPermitTransitionFactV0_1` retain their exact R1 fields and names; their
changed values and fingerprints MUST be recomputed.

```yaml
R8_effective_schema_registry:
  EffectAuthorizationRequirementV0_1R8:
    interface_version: agents-os.effect-authorization-requirement.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, mode, requirement_basis_ref, requirement_basis_fingerprint, policy_bundle_revision, policy_bundle_fingerprint, prohibited_behavior_list_revision, prohibited_behavior_list_fingerprint, exact_effect_scope_fingerprint, evaluated_at_trusted_time_utc_ms, evaluation_watermark_event_sequence, Jenn_decision_ref, Jenn_decision_fingerprint, Jenn_actor_identity_ref, issued_at_utc_ms, expires_at_utc_ms, revocation_event_sequence, exact_Jenn_scope_fingerprint, currentness_result, currentness_reason, canonical_fingerprint]
  F2ExecutionHostPrincipalBindingExtensionV0_1R8:
    interface_version: agents-os.f2-execution-host-principal-binding-extension.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, host_actor_id, host_actor_identity_revision, host_actor_identity_ref, host_actor_identity_fingerprint, host_actor_identity_assessment_ref, host_actor_identity_assessment_fingerprint, host_actor_class, host_process_principal_id, host_process_principal_revision, host_process_principal_ref, host_process_principal_fingerprint, host_process_principal_assessment_ref, host_process_principal_assessment_fingerprint, host_process_principal_class, host_process_binding_ref, host_process_binding_revision, host_process_binding_fingerprint, host_process_binding_assessment_ref, host_process_binding_assessment_fingerprint, provisioning_action_ref, provisioning_action_fingerprint, provisioning_basis_ref, provisioning_basis_fingerprint, canonical_fingerprint]
  F4HostEffectTrustEligibilityAssessmentV0_1R8:
    interface_version: agents-os.f4-host-effect-trust-eligibility.v0.1-r8
    fingerprint_field: assessment_fingerprint
    fields: [interface_version, host_actor_identity_ref, host_actor_identity_fingerprint, integrity_assessment_ref, integrity_assessment_fingerprint, integrity_observation, current_F2_actor_observation, current_F2_actor_assessment_ref, current_F2_actor_assessment_fingerprint, F2_compromise_history_observation, F2_compromise_history_evidence_ref, F2_compromise_history_evidence_fingerprint, F4_compromise_history_observation, F4_compromise_history_evidence_ref, F4_compromise_history_evidence_fingerprint, assessment_watermark_event_sequence, result, reason, assessment_fingerprint]
  F4HostTrustRevisionV0_1R8:
    interface_version: agents-os.f4-host-trust-revision.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, host_id, host_trust_revision, expected_previous_host_trust_revision, previous_host_trust_ref, previous_host_trust_fingerprint, host_actor_id, host_actor_identity_revision, host_actor_identity_ref, host_actor_identity_fingerprint, host_actor_identity_assessment_ref, host_actor_identity_assessment_fingerprint, host_process_principal_id, host_process_principal_revision, host_process_principal_ref, host_process_principal_fingerprint, host_process_principal_assessment_ref, host_process_principal_assessment_fingerprint, host_process_binding_ref, host_process_binding_revision, host_process_binding_fingerprint, host_process_binding_assessment_ref, host_process_binding_assessment_fingerprint, provisioning_action_ref, provisioning_action_fingerprint, provisioning_basis_ref, provisioning_basis_fingerprint, transition_kind, transition_action_ref, transition_action_fingerprint, transition_authority_basis_ref, transition_authority_basis_fingerprint, authenticator_profile_ref, authenticator_profile_revision, authenticator_profile_fingerprint, credential_binding_ref, credential_binding_fingerprint, lifecycle_state, validity_start_utc_ms, validity_end_utc_ms, issued_event_sequence, canonical_fingerprint]
  HostAuthenticationAssessmentV0_1R8:
    interface_version: agents-os.host-authentication-assessment.v0.1-r8
    fingerprint_field: assessment_fingerprint
    fields: [interface_version, host_trust_ref, host_trust_fingerprint, host_actor_identity_ref, host_actor_identity_fingerprint, host_actor_identity_assessment_ref, host_actor_identity_assessment_fingerprint, host_process_principal_ref, host_process_principal_fingerprint, host_process_principal_assessment_ref, host_process_principal_assessment_fingerprint, host_process_binding_ref, host_process_binding_fingerprint, host_process_binding_assessment_ref, host_process_binding_assessment_fingerprint, effect_trust_eligibility_assessment_ref, effect_trust_eligibility_assessment_fingerprint, authenticator_profile_ref, authenticator_profile_fingerprint, challenge_ref, challenge_fingerprint, verifier_identity_ref, verifier_profile_ref, verification_evidence_ref, verification_evidence_fingerprint, host_authentication_epoch, trusted_time_utc_ms, valid_until_utc_ms, host_revocation_event_sequence, result, reason, assessment_fingerprint]
  AuthoritySourceBindingV0_1R8:
    interface_version: agents-os.authority-source-binding.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, role, source_ref, source_fingerprint, canonical_fingerprint]
  CapabilitySubsetProofV0_1R8:
    interface_version: agents-os.capability-subset-proof.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, source_authority_set_fingerprint, capability_definition_fingerprint, operation_registry_fingerprint, requested_operation_set, source_projection_fingerprints, exact_intersection_operation_set, constraint_fingerprint, result, reason, watermark_event_sequence, canonical_fingerprint]
  CapabilityGrantV0_1R8:
    interface_version: agents-os.capability-grant.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, capability_definition_ref, capability_definition_fingerprint, capability_revision, operation_registry_revision, operation_registry_fingerprint, operation_set, constraint_fingerprint, source_authority_bindings, source_authority_set_fingerprint, derived_subset_proof_ref, derived_subset_proof_fingerprint, canonical_fingerprint]
  ResourceContainmentAssessmentV0_1R8:
    interface_version: agents-os.resource-containment-assessment.v0.1-r8
    fingerprint_field: assessment_fingerprint
    fields: [interface_version, source_scope_set_fingerprint, resource_definition_fingerprint, resource_kind, resource_ref, requested_operation_set, selector_constraint_fingerprint, source_projection_fingerprints, result, reason, watermark_event_sequence, assessment_fingerprint]
  ResourceGrantV0_1R8:
    interface_version: agents-os.resource-grant.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, resource_definition_ref, resource_definition_fingerprint, resource_kind, resource_ref, resource_subject_fingerprint, operation_registry_revision, operation_registry_fingerprint, operation_set, selector_constraint_fingerprint, source_scope_bindings, source_scope_set_fingerprint, containment_assessment_ref, containment_assessment_fingerprint, canonical_fingerprint]
  EffectIntentBindingV0_1R8:
    interface_version: agents-os.effect-intent-binding.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, effect_intent_id, operation_kind, target_resource_refs, payload_fingerprint, capability_set_fingerprint, resource_set_fingerprint, expected_result_contract_ref, expected_result_contract_fingerprint, idempotency_key, side_effect_audit_label, external_effect_requested, raw_payload_present, canonical_fingerprint]
  TaskPermitV0_1R8:
    interface_version: agents-os.task-permit.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, F4_contract_version, permit_id, permit_revision, issuance_event_sequence, task_authority_binding, actor_authority_binding, resident_command_binding, host_trust_ref, host_trust_fingerprint, host_authenticator_profile_ref, host_authenticator_profile_fingerprint, host_authentication_assessment_ref, host_authentication_assessment_fingerprint, host_authentication_epoch, issuer_resident_identity_ref, issuer_resident_epoch, policy_bundle_revision, policy_bundle_fingerprint, prohibited_behavior_list_revision, prohibited_boundary_evidence_ref, prohibited_boundary_evidence_fingerprint, capability_grants, resource_grants, effect_intent_binding, execution_epoch, host_fence_generation, effect_fence_generation, task_fence_generation, issued_at_utc_ms, not_before_utc_ms, expires_at_utc_ms, start_authority_commit_before_utc_ms, max_invocations, idempotency_key, requires_human_presence, human_presence_binding, effect_authorization_requirement, secret_handle_bindings, permit_attestation_profile_ref, permit_attestation_profile_fingerprint, permit_attestation_evidence_ref, permit_attestation_evidence_fingerprint, canonical_fingerprint]
  TaskPermitCurrentnessAssessmentV0_1R8:
    interface_version: agents-os.task-permit-currentness-assessment.v0.1-r8
    fingerprint_field: assessment_fingerprint
    fields: [interface_version, permit_ref, permit_fingerprint, lifecycle_state, trusted_time_utc_ms, task_binding_current, actor_binding_current, resident_command_binding_current, host_trust_current, host_authentication_current, policy_current, prohibited_boundary_current, capability_grants_current, resource_grants_current, secret_handle_bindings_current, permit_attestation_current, human_presence_current, effect_authorization_requirement_current, time_window_current, invocation_available, execution_epoch_current, host_fence_current, effect_fence_current, task_fence_current, result, reason, assessment_event_sequence, assessment_fingerprint]
  HostLocalAdmissionRequestV0_1R8:
    interface_version: agents-os.host-local-admission-request.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, invocation_identity, task_permit_ref, task_permit_fingerprint, effect_intent_ref, effect_intent_fingerprint, resident_command_envelope_ref, resident_command_envelope_fingerprint, target_host_id, target_host_trust_revision, requested_at_utc_ms, request_event_sequence, canonical_fingerprint]
  HostLocalAdmissionDecisionV0_1R8:
    interface_version: agents-os.host-local-admission-decision.v0.1-r8
    fingerprint_field: decision_fingerprint
    fields: [interface_version, invocation_identity_fingerprint, request_ref, request_fingerprint, permit_currentness_assessment_ref, permit_currentness_assessment_fingerprint, host_authentication_assessment_ref, host_authentication_assessment_fingerprint, fence_state_ref, fence_state_fingerprint, current_watermark_event_sequence, request_integrity, permit_currentness, host_authentication, host_ownership, task_fence_match, host_fence_match, effect_fence_match, execution_epoch_match, capability_subset, resource_subset, secret_handle_scope, permit_attestation, human_presence, effect_intent_exact_match, idempotency_identity_match, invocation_slot_available, prohibited_boundary, effect_authorization_requirement_current, decision, reason, decided_at_utc_ms, decision_fingerprint]
  FinalAuthorityObservationV0_1R8:
    interface_version: agents-os.final-authority-observation.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, code, observation, evidence_availability, evidence_ref, evidence_fingerprint, canonical_fingerprint]
  FinalHandoffAuthorityAssessmentV0_1R8:
    interface_version: agents-os.final-handoff-authority-assessment.v0.1-r8
    fingerprint_field: assessment_fingerprint
    fields: [interface_version, permit_ref, permit_fingerprint, authority_observations, authority_observation_set_fingerprint, trusted_time_utc_ms, watermark_event_sequence, result, reason, assessment_fingerprint]
  HostWorkAcceptanceFactV0_1R8:
    interface_version: agents-os.host-work-acceptance-fact.v0.1-r8
    fingerprint_field: fact_fingerprint
    fields: [interface_version, acceptance_id, invocation_identity, admission_request_ref, admission_request_fingerprint, admission_decision_ref, admission_decision_fingerprint, permit_currentness_assessment_ref, permit_currentness_assessment_fingerprint, host_authentication_assessment_ref, host_authentication_assessment_fingerprint, accepted_host_id, accepted_host_trust_revision, accepted_host_authentication_epoch, accepted_task_fence_generation, accepted_host_fence_generation, accepted_effect_fence_generation, accepted_execution_epoch, accepted_watermark_event_sequence, accepted_at_utc_ms, start_authority_expires_at_utc_ms, host_acceptance_attestation_ref, host_acceptance_attestation_fingerprint, fact_fingerprint]
  HostWorkStartDispositionFactV0_1R8:
    interface_version: agents-os.host-work-start-disposition-fact.v0.1-r8
    fingerprint_field: fact_fingerprint
    fields: [interface_version, observation_id, observation_attempt, acceptance_ref, acceptance_fingerprint, invocation_identity_fingerprint, observed_host_id, observed_host_trust_revision, observed_host_authentication_epoch, rechecked_task_fence_generation, rechecked_host_fence_generation, rechecked_effect_fence_generation, rechecked_execution_epoch, rechecked_secret_handle_set_fingerprint, rechecked_permit_attestation_fingerprint, rechecked_human_presence_binding_fingerprint, final_handoff_authority_assessment_ref, final_handoff_authority_assessment_fingerprint, secret_handles_current, permit_attestation_current, human_presence_current, final_handoff_authority_current, disposition, reason, observed_at_utc_ms, observation_event_sequence, host_observation_attestation_ref, host_observation_attestation_fingerprint, fact_fingerprint]
  F4AcceptedEffectHandoffV0_1R8:
    interface_version: agents-os.f4-accepted-effect-handoff.v0.1-r8
    fingerprint_field: canonical_fingerprint
    fields: [interface_version, handoff_id, acceptance_ref, acceptance_fingerprint, start_disposition_ref, start_disposition_fingerprint, invocation_identity, task_permit_ref, task_permit_fingerprint, effect_intent_ref, effect_intent_fingerprint, owner_host_id, owner_host_trust_revision, owner_host_authentication_epoch, execution_epoch, task_fence_generation, host_fence_generation, effect_fence_generation, start_authority_expires_at_utc_ms, capability_set_fingerprint, resource_set_fingerprint, secret_handle_set_fingerprint, permit_attestation_evidence_fingerprint, human_presence_binding_fingerprint, effect_authorization_requirement_fingerprint, final_handoff_authority_assessment_fingerprint, expected_result_contract_ref, expected_result_contract_fingerprint, handoff_event_sequence, canonical_fingerprint]
```

`EffectAuthorizationRequirementResolutionV0_1R8` is a non-persisted transport
result with exact fields `[interface_version, outcome, reason,
requirement_fingerprint]`; it has no canonical fingerprint or authority.
`EffectScopeV0_1R8`, graph nodes, vector collections, and the zero-effect stub
are evidence wrappers, not normative authority objects and are not counted as
effective schemas.

The witness MUST expose a machine-readable inventory with JSON pointer, exact
schema name, interface version, fingerprint field, and ordered field names for
every effective object. The validator discovers and counts objects from that
inventory; wrapper or node counts cannot stand in for object counts.

## 3. Derived identities and exact reference chain

R8 retains the R1 `permit_id` and invocation formulas and requires every
changed value to cascade. These formulas are closed:

```text
acceptance_id =
  SHA256(JCS(["agents-os.host-work-acceptance-id.v0.1",
              invocation_identity.canonical_fingerprint]))

acceptance_ref = "acceptance:" + acceptance_id

observation_id =
  SHA256(JCS(["agents-os.host-work-start-observation-id.v0.1",
              acceptance.fact_fingerprint,
              observation_attempt]))

start_disposition_ref = "observation:" + observation_id

handoff_id =
  SHA256(JCS(["agents-os.f4-accepted-effect-handoff-id.v0.1",
              invocation_identity.canonical_fingerprint]))

handoff_ref = "handoff:" + handoff_id
```

The following equalities are mandatory and fingerprint-covered:

```text
permit_ref == "permit:" + permit_id everywhere
activation_transition.transition_action_ref == acceptance_ref
disposition.acceptance_ref == acceptance_ref
handoff.acceptance_ref == acceptance_ref
handoff.start_disposition_ref == start_disposition_ref
zero_effect_stub.handoff_ref == handoff_ref
```

Request, acceptance, and handoff contain byte-identical invocation identity;
disposition contains its exact fingerprint. Every request, decision,
assessment, acceptance, disposition, and handoff fingerprint ref MUST resolve
to the exact emitted object. Outer graph dependencies do not substitute for
these semantic edges.

## 4. Exact Host trust, profile, and revision binding

The constructive R8 Host uses deliberately different revision spaces:

```text
host_actor_identity_revision = 3
host_trust_revision = 7
```

R8 replaces the four ambiguous fields in their prior positions:

```text
target_host_identity_revision   -> target_host_trust_revision
accepted_host_identity_revision -> accepted_host_trust_revision
observed_host_identity_revision -> observed_host_trust_revision
owner_host_identity_revision    -> owner_host_trust_revision
```

All four equal the exact current `F4HostTrustRevision.host_trust_revision`.
The Host-trust object separately binds F2 Actor revision 3. A downstream field
named `*_host_identity_revision` is forbidden.

`AUTHENTICATED / MATCH` requires the Host-authentication profile ref and
fingerprint to equal the exact Host-trust profile ref and fingerprint. Ref-only,
fingerprint-only, or dual mismatch maps to `REJECTED / PROFILE_MISMATCH` even
when all other evidence passes. Permit profile ref/fingerprint MUST equal both.

The complete removed set outside the immutable R1 base-integrity evidence is:

```text
host_identity_ref
host_identity_fingerprint
target_host_identity_revision
accepted_host_identity_revision
observed_host_identity_revision
owner_host_identity_revision
Jenn_authorization_binding
Jenn_authorization_binding_fingerprint
Jenn_authorization_current
side_effect_class
source_authority_refs
source_scope_refs
```

Removed values are `ACCEPTANCE_MISSING` and
`agents-os.host-identity-revision.v0.1`. Recursive presence rejects.

## 5. Total authorization resolution and seven-field presence

The only legal persisted modes are the three full literals:

```text
NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED
EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED
PROHIBITED_NON_ISSUABLE
```

The canonical evaluator, not a caller, supplies result and reason. Mode input
integrity conflict produces
`NO_REQUIREMENT_OBJECT / MODE_INPUT_INTEGRITY_CONFLICT`; unavailable mode input
produces `NO_REQUIREMENT_OBJECT / MODE_INPUT_UNAVAILABLE`; any unknown mode or
internally contradictory normalized input produces
`NO_REQUIREMENT_OBJECT / INVALID_INPUT`. No-object rows have null requirement
fingerprint and cannot enter a permit.

For exact-Jenn mode, decision-index observation is one of `PRESENT`,
`ABSENT_PROVEN`, `UNAVAILABLE`, or `INTEGRITY_CONFLICT`. `ABSENT_PROVEN` is
mutually exclusive with every present predicate. The exact seven Jenn fields
are the seven fields from `Jenn_decision_ref` through
`exact_Jenn_scope_fingerprint` in the registry. The sole legal persisted rows
are:

| Mode/result/reason | Seven Jenn fields |
|---|---|
| NO_SEPARATE / NOT_APPLICABLE / NO_SEPARATE_REQUIRED | all null |
| PROHIBITED / REJECTED / PROHIBITED | all null |
| EXACT / REJECTED / JENN_DECISION_MISSING | all null |
| EXACT / CURRENT / JENN_DECISION_CURRENT | all non-null |
| EXACT / REJECTED / JENN_DECISION_REVOKED | all non-null |
| EXACT / REJECTED / JENN_SCOPE_MISMATCH | all non-null |
| EXACT / REJECTED / JENN_DECISION_EXPIRED | all non-null |

Every one of the other 126 mixed presence masks rejects. Decision evidence on
NO_SEPARATE or PROHIBITED rejects. A present exact decision with any null Jenn
field produces no object. Present-decision negative precedence is exactly
revoked, scope mismatch, expired; a proven negative dominates unrelated
unavailability only when all seven fields required to construct that negative
row are present. Otherwise evidence unavailability produces no object.
Current requires exact scope equality, time before expiry, and the current
revocation head at the same evaluation watermark.

## 6. Constructible F4 effect-trust eligibility

The exact eligibility schema is in Section 2. Presence rules are:

```text
current F2 observation ACTIVE, PROVEN_NOT_ACTIVE, or INDETERMINATE
  -> current assessment ref/fingerprint both non-null
current F2 observation UNAVAILABLE
  -> both null

F2/F4 history PRESENT, ABSENT, or INDETERMINATE
  -> corresponding evidence ref/fingerprint both non-null
F2/F4 history UNAVAILABLE
  -> both null
```

All observations bind one `assessment_watermark_event_sequence`. Synthetic or
last-known “no compromise” heads cannot replace an absence proof. The total
order is integrity rejected, F2 history present, F4 history present, current F2
proven not active, either history indeterminate/unavailable, current F2
indeterminate/unavailable, then ACTIVE plus both histories ABSENT. Results and
reasons are respectively:

```text
INELIGIBLE / INTEGRITY_FAILURE
INELIGIBLE / F2_COMPROMISE_HISTORY_PRESENT
INELIGIBLE / F4_COMPROMISE_HISTORY_PRESENT
INELIGIBLE / CURRENT_F2_ACTOR_NOT_ACTIVE
INDETERMINATE / HISTORY_UNAVAILABLE
INDETERMINATE / CURRENT_F2_INPUT_UNAVAILABLE
ELIGIBLE / NEVER_COMPROMISED_AND_ALL_CURRENT
```

Every other tuple rejects. A recovered ACTIVE F2 Actor with same-lineage
compromise evidence remains F4-ineligible; this does not amend the F2 RECOVER
result.

## 7. Total final-handoff authority reducer

`authority_observations` contains exactly one each, in this order:

```text
CANONICAL_INTEGRITY
F1_TASK
F2_ACTOR_PRINCIPAL_BINDING
F2_RESPONSIBILITY_DELEGATION
F3_RESIDENT_COMMAND
F4_HOST_EFFECT_TRUST
POLICY
PROHIBITED_BEHAVIOR_LIST
EFFECT_AUTHORIZATION_REQUIREMENT
TRUSTED_TIME
TASK_FENCE
HOST_FENCE
EFFECT_FENCE
```

For each observation, `AVAILABLE` requires non-null evidence ref/fingerprint
and permits only `PASS` or `REJECTED`; `UNAVAILABLE` requires both null and only
`INDETERMINATE`. Missing, duplicate, extra, reordered, or invalid tuples reject.
The set fingerprint is:

```text
SHA256(JCS(["agents-os.f4-final-authority-observation-set.v0.1-r8",
            ordered FinalAuthorityObservation fingerprints]))
```

The total reducer is:

```text
CANONICAL_INTEGRITY = REJECTED
  -> REJECTED / INTEGRITY_FAILURE
else any other observation = REJECTED
  -> REJECTED / AUTHORITY_STALE
else any observation = INDETERMINATE or UNAVAILABLE
  -> INDETERMINATE / AUTHORITY_UNAVAILABLE
else exact thirteen all PASS and AVAILABLE
  -> CURRENT / ALL_AUTHORITY_CURRENT
```

Result and reason are reducer outputs, never caller inputs. All observations,
trusted time, and the exact F1/F2/F3/F4/policy/PBL/authorization/fence evidence
belong to the printed watermark.

## 8. Capability/resource proof and snapshot consistency

R8 materializes `CapabilitySubsetProofV0_1R8` and
`ResourceContainmentAssessmentV0_1R8`. Source roles obey the R6 exact role
matrix. Their POLICY and PROHIBITED_BEHAVIOR_LIST source fingerprints MUST equal
the exact fingerprints used by the authorization requirement and permit at the
same watermark. F1/F2/F3 sources resolve to the exact bound authority objects.

The synthetic M0 operation is `SYNTHETIC_NOOP`. Capability PASS requires the
requested set to equal a subset of the computed exact intersection; resource
PASS requires the exact resource ref and operation to be contained by the
computed source scope. Grant proof refs/fingerprints MUST resolve to the
materialized PASS proof/assessment. Opaque labels, wildcard/ambient scope,
missing roles, duplicate roles, or mismatched snapshots reject.

## 9. Independent evidence profile

R8 uses four new subjects: this amendment, an independent fixture builder, its
fixed complete-effective fixture, and a semantic validator that does not import
the builder. The validator MUST NOT compare the fixture to an internally built
expected fixture. It validates arbitrary input using the schema registry,
field order, types, nullability, closed enums, fingerprint formulas, reducer
rules, identity formulas, semantic refs, graph edges, and zero-effect claims.

Negative mutations re-sign every non-target parent and node so rejection proves
the attacked semantic rule rather than a shallow hash mismatch. At minimum they
cover wrong domain, field order, all derived IDs/refs, Host profile, all 126
mixed Jenn masks, unknown/mutually impossible authorization input, final reducer
precedence, eligibility presence, proof/source roles, single invocation,
base-integrity dependency, old fields/values, and nonzero effect/provider/raw
secret counts.

The fresh review unit is all twenty-five R1-R8 subjects. Only Jenn may accept or
freeze it. Nothing starts F5/F6 or authorizes implementation, runtime, database,
service, Host, provider, production authentication, credentials, keys, physical
effects, commit, push, merge, release, or deploy.
