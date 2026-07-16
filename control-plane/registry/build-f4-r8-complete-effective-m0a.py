#!/usr/bin/env python3
"""Build the fixed, offline, zero-effect F4 R8 complete-effective witness.

This is an independent fixture builder.  It consumes the immutable R7 witness
only as source material, emits no runtime authority, and never validates an
arbitrary caller-supplied fixture.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
R7_FIXTURE = HERE / "examples" / "2026-07-16-agents-os-f4-r7-complete-effective-m0a-witness-v0.1.json"
DEFAULT_OUTPUT = HERE / "examples" / "2026-07-16-agents-os-f4-r8-complete-effective-m0a-witness-v0.1.json"
CONTRACT = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R8_ATOMIC_BUNDLE"
F4_FP_PREFIX = "agents-os.f4-fingerprint.v0.1:"


def canonical_bytes(value: Any) -> bytes:
    def check(item: Any) -> None:
        if isinstance(item, float):
            raise ValueError("floating-point values are outside the canonical profile")
        if isinstance(item, str):
            if unicodedata.normalize("NFC", item) != item or item != item.strip() or "\0" in item:
                raise ValueError("non-canonical string")
        elif isinstance(item, list):
            for child in item:
                check(child)
        elif isinstance(item, dict):
            for key, child in item.items():
                check(key)
                check(child)

    check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def label(name: str) -> str:
    return hashlib.sha256(("agents-os.f4-r8-m0:" + name).encode("utf-8")).hexdigest()


R8_SCHEMAS: dict[str, dict[str, Any]] = {
    "EffectAuthorizationRequirementV0_1R8": {"interface_version": "agents-os.effect-authorization-requirement.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "mode", "requirement_basis_ref", "requirement_basis_fingerprint", "policy_bundle_revision", "policy_bundle_fingerprint", "prohibited_behavior_list_revision", "prohibited_behavior_list_fingerprint", "exact_effect_scope_fingerprint", "evaluated_at_trusted_time_utc_ms", "evaluation_watermark_event_sequence", "Jenn_decision_ref", "Jenn_decision_fingerprint", "Jenn_actor_identity_ref", "issued_at_utc_ms", "expires_at_utc_ms", "revocation_event_sequence", "exact_Jenn_scope_fingerprint", "currentness_result", "currentness_reason", "canonical_fingerprint"]},
    "F2ExecutionHostPrincipalBindingExtensionV0_1R8": {"interface_version": "agents-os.f2-execution-host-principal-binding-extension.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "host_actor_id", "host_actor_identity_revision", "host_actor_identity_ref", "host_actor_identity_fingerprint", "host_actor_identity_assessment_ref", "host_actor_identity_assessment_fingerprint", "host_actor_class", "host_process_principal_id", "host_process_principal_revision", "host_process_principal_ref", "host_process_principal_fingerprint", "host_process_principal_assessment_ref", "host_process_principal_assessment_fingerprint", "host_process_principal_class", "host_process_binding_ref", "host_process_binding_revision", "host_process_binding_fingerprint", "host_process_binding_assessment_ref", "host_process_binding_assessment_fingerprint", "provisioning_action_ref", "provisioning_action_fingerprint", "provisioning_basis_ref", "provisioning_basis_fingerprint", "canonical_fingerprint"]},
    "F4HostEffectTrustEligibilityAssessmentV0_1R8": {"interface_version": "agents-os.f4-host-effect-trust-eligibility.v0.1-r8", "fingerprint_field": "assessment_fingerprint", "fields": ["interface_version", "host_actor_identity_ref", "host_actor_identity_fingerprint", "integrity_assessment_ref", "integrity_assessment_fingerprint", "integrity_observation", "current_F2_actor_observation", "current_F2_actor_assessment_ref", "current_F2_actor_assessment_fingerprint", "F2_compromise_history_observation", "F2_compromise_history_evidence_ref", "F2_compromise_history_evidence_fingerprint", "F4_compromise_history_observation", "F4_compromise_history_evidence_ref", "F4_compromise_history_evidence_fingerprint", "assessment_watermark_event_sequence", "result", "reason", "assessment_fingerprint"]},
    "F4HostTrustRevisionV0_1R8": {"interface_version": "agents-os.f4-host-trust-revision.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "host_id", "host_trust_revision", "expected_previous_host_trust_revision", "previous_host_trust_ref", "previous_host_trust_fingerprint", "host_actor_id", "host_actor_identity_revision", "host_actor_identity_ref", "host_actor_identity_fingerprint", "host_actor_identity_assessment_ref", "host_actor_identity_assessment_fingerprint", "host_process_principal_id", "host_process_principal_revision", "host_process_principal_ref", "host_process_principal_fingerprint", "host_process_principal_assessment_ref", "host_process_principal_assessment_fingerprint", "host_process_binding_ref", "host_process_binding_revision", "host_process_binding_fingerprint", "host_process_binding_assessment_ref", "host_process_binding_assessment_fingerprint", "provisioning_action_ref", "provisioning_action_fingerprint", "provisioning_basis_ref", "provisioning_basis_fingerprint", "transition_kind", "transition_action_ref", "transition_action_fingerprint", "transition_authority_basis_ref", "transition_authority_basis_fingerprint", "authenticator_profile_ref", "authenticator_profile_revision", "authenticator_profile_fingerprint", "credential_binding_ref", "credential_binding_fingerprint", "lifecycle_state", "validity_start_utc_ms", "validity_end_utc_ms", "issued_event_sequence", "canonical_fingerprint"]},
    "HostAuthenticationAssessmentV0_1R8": {"interface_version": "agents-os.host-authentication-assessment.v0.1-r8", "fingerprint_field": "assessment_fingerprint", "fields": ["interface_version", "host_trust_ref", "host_trust_fingerprint", "host_actor_identity_ref", "host_actor_identity_fingerprint", "host_actor_identity_assessment_ref", "host_actor_identity_assessment_fingerprint", "host_process_principal_ref", "host_process_principal_fingerprint", "host_process_principal_assessment_ref", "host_process_principal_assessment_fingerprint", "host_process_binding_ref", "host_process_binding_fingerprint", "host_process_binding_assessment_ref", "host_process_binding_assessment_fingerprint", "effect_trust_eligibility_assessment_ref", "effect_trust_eligibility_assessment_fingerprint", "authenticator_profile_ref", "authenticator_profile_fingerprint", "challenge_ref", "challenge_fingerprint", "verifier_identity_ref", "verifier_profile_ref", "verification_evidence_ref", "verification_evidence_fingerprint", "host_authentication_epoch", "trusted_time_utc_ms", "valid_until_utc_ms", "host_revocation_event_sequence", "result", "reason", "assessment_fingerprint"]},
    "AuthoritySourceBindingV0_1R8": {"interface_version": "agents-os.authority-source-binding.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "role", "source_ref", "source_fingerprint", "canonical_fingerprint"]},
    "CapabilitySubsetProofV0_1R8": {"interface_version": "agents-os.capability-subset-proof.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "source_authority_set_fingerprint", "capability_definition_fingerprint", "operation_registry_fingerprint", "requested_operation_set", "source_projection_fingerprints", "exact_intersection_operation_set", "constraint_fingerprint", "result", "reason", "watermark_event_sequence", "canonical_fingerprint"]},
    "CapabilityGrantV0_1R8": {"interface_version": "agents-os.capability-grant.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "capability_definition_ref", "capability_definition_fingerprint", "capability_revision", "operation_registry_revision", "operation_registry_fingerprint", "operation_set", "constraint_fingerprint", "source_authority_bindings", "source_authority_set_fingerprint", "derived_subset_proof_ref", "derived_subset_proof_fingerprint", "canonical_fingerprint"]},
    "ResourceContainmentAssessmentV0_1R8": {"interface_version": "agents-os.resource-containment-assessment.v0.1-r8", "fingerprint_field": "assessment_fingerprint", "fields": ["interface_version", "source_scope_set_fingerprint", "resource_definition_fingerprint", "resource_kind", "resource_ref", "requested_operation_set", "selector_constraint_fingerprint", "source_projection_fingerprints", "result", "reason", "watermark_event_sequence", "assessment_fingerprint"]},
    "ResourceGrantV0_1R8": {"interface_version": "agents-os.resource-grant.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "resource_definition_ref", "resource_definition_fingerprint", "resource_kind", "resource_ref", "resource_subject_fingerprint", "operation_registry_revision", "operation_registry_fingerprint", "operation_set", "selector_constraint_fingerprint", "source_scope_bindings", "source_scope_set_fingerprint", "containment_assessment_ref", "containment_assessment_fingerprint", "canonical_fingerprint"]},
    "EffectIntentBindingV0_1R8": {"interface_version": "agents-os.effect-intent-binding.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "effect_intent_id", "operation_kind", "target_resource_refs", "payload_fingerprint", "capability_set_fingerprint", "resource_set_fingerprint", "expected_result_contract_ref", "expected_result_contract_fingerprint", "idempotency_key", "side_effect_audit_label", "external_effect_requested", "raw_payload_present", "canonical_fingerprint"]},
    "TaskPermitV0_1R8": {"interface_version": "agents-os.task-permit.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "F4_contract_version", "permit_id", "permit_revision", "issuance_event_sequence", "task_authority_binding", "actor_authority_binding", "resident_command_binding", "host_trust_ref", "host_trust_fingerprint", "host_authenticator_profile_ref", "host_authenticator_profile_fingerprint", "host_authentication_assessment_ref", "host_authentication_assessment_fingerprint", "host_authentication_epoch", "issuer_resident_identity_ref", "issuer_resident_epoch", "policy_bundle_revision", "policy_bundle_fingerprint", "prohibited_behavior_list_revision", "prohibited_boundary_evidence_ref", "prohibited_boundary_evidence_fingerprint", "capability_grants", "resource_grants", "effect_intent_binding", "execution_epoch", "host_fence_generation", "effect_fence_generation", "task_fence_generation", "issued_at_utc_ms", "not_before_utc_ms", "expires_at_utc_ms", "start_authority_commit_before_utc_ms", "max_invocations", "idempotency_key", "requires_human_presence", "human_presence_binding", "effect_authorization_requirement", "secret_handle_bindings", "permit_attestation_profile_ref", "permit_attestation_profile_fingerprint", "permit_attestation_evidence_ref", "permit_attestation_evidence_fingerprint", "canonical_fingerprint"]},
    "TaskPermitCurrentnessAssessmentV0_1R8": {"interface_version": "agents-os.task-permit-currentness-assessment.v0.1-r8", "fingerprint_field": "assessment_fingerprint", "fields": ["interface_version", "permit_ref", "permit_fingerprint", "lifecycle_state", "trusted_time_utc_ms", "task_binding_current", "actor_binding_current", "resident_command_binding_current", "host_trust_current", "host_authentication_current", "policy_current", "prohibited_boundary_current", "capability_grants_current", "resource_grants_current", "secret_handle_bindings_current", "permit_attestation_current", "human_presence_current", "effect_authorization_requirement_current", "time_window_current", "invocation_available", "execution_epoch_current", "host_fence_current", "effect_fence_current", "task_fence_current", "result", "reason", "assessment_event_sequence", "assessment_fingerprint"]},
    "HostLocalAdmissionRequestV0_1R8": {"interface_version": "agents-os.host-local-admission-request.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "invocation_identity", "task_permit_ref", "task_permit_fingerprint", "effect_intent_ref", "effect_intent_fingerprint", "resident_command_envelope_ref", "resident_command_envelope_fingerprint", "target_host_id", "target_host_trust_revision", "requested_at_utc_ms", "request_event_sequence", "canonical_fingerprint"]},
    "HostLocalAdmissionDecisionV0_1R8": {"interface_version": "agents-os.host-local-admission-decision.v0.1-r8", "fingerprint_field": "decision_fingerprint", "fields": ["interface_version", "invocation_identity_fingerprint", "request_ref", "request_fingerprint", "permit_currentness_assessment_ref", "permit_currentness_assessment_fingerprint", "host_authentication_assessment_ref", "host_authentication_assessment_fingerprint", "fence_state_ref", "fence_state_fingerprint", "current_watermark_event_sequence", "request_integrity", "permit_currentness", "host_authentication", "host_ownership", "task_fence_match", "host_fence_match", "effect_fence_match", "execution_epoch_match", "capability_subset", "resource_subset", "secret_handle_scope", "permit_attestation", "human_presence", "effect_intent_exact_match", "idempotency_identity_match", "invocation_slot_available", "prohibited_boundary", "effect_authorization_requirement_current", "decision", "reason", "decided_at_utc_ms", "decision_fingerprint"]},
    "FinalAuthorityObservationV0_1R8": {"interface_version": "agents-os.final-authority-observation.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "code", "observation", "evidence_availability", "evidence_ref", "evidence_fingerprint", "canonical_fingerprint"]},
    "FinalHandoffAuthorityAssessmentV0_1R8": {"interface_version": "agents-os.final-handoff-authority-assessment.v0.1-r8", "fingerprint_field": "assessment_fingerprint", "fields": ["interface_version", "permit_ref", "permit_fingerprint", "authority_observations", "authority_observation_set_fingerprint", "trusted_time_utc_ms", "watermark_event_sequence", "result", "reason", "assessment_fingerprint"]},
    "HostWorkAcceptanceFactV0_1R8": {"interface_version": "agents-os.host-work-acceptance-fact.v0.1-r8", "fingerprint_field": "fact_fingerprint", "fields": ["interface_version", "acceptance_id", "invocation_identity", "admission_request_ref", "admission_request_fingerprint", "admission_decision_ref", "admission_decision_fingerprint", "permit_currentness_assessment_ref", "permit_currentness_assessment_fingerprint", "host_authentication_assessment_ref", "host_authentication_assessment_fingerprint", "accepted_host_id", "accepted_host_trust_revision", "accepted_host_authentication_epoch", "accepted_task_fence_generation", "accepted_host_fence_generation", "accepted_effect_fence_generation", "accepted_execution_epoch", "accepted_watermark_event_sequence", "accepted_at_utc_ms", "start_authority_expires_at_utc_ms", "host_acceptance_attestation_ref", "host_acceptance_attestation_fingerprint", "fact_fingerprint"]},
    "HostWorkStartDispositionFactV0_1R8": {"interface_version": "agents-os.host-work-start-disposition-fact.v0.1-r8", "fingerprint_field": "fact_fingerprint", "fields": ["interface_version", "observation_id", "observation_attempt", "acceptance_ref", "acceptance_fingerprint", "invocation_identity_fingerprint", "observed_host_id", "observed_host_trust_revision", "observed_host_authentication_epoch", "rechecked_task_fence_generation", "rechecked_host_fence_generation", "rechecked_effect_fence_generation", "rechecked_execution_epoch", "rechecked_secret_handle_set_fingerprint", "rechecked_permit_attestation_fingerprint", "rechecked_human_presence_binding_fingerprint", "final_handoff_authority_assessment_ref", "final_handoff_authority_assessment_fingerprint", "secret_handles_current", "permit_attestation_current", "human_presence_current", "final_handoff_authority_current", "disposition", "reason", "observed_at_utc_ms", "observation_event_sequence", "host_observation_attestation_ref", "host_observation_attestation_fingerprint", "fact_fingerprint"]},
    "F4AcceptedEffectHandoffV0_1R8": {"interface_version": "agents-os.f4-accepted-effect-handoff.v0.1-r8", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "handoff_id", "acceptance_ref", "acceptance_fingerprint", "start_disposition_ref", "start_disposition_fingerprint", "invocation_identity", "task_permit_ref", "task_permit_fingerprint", "effect_intent_ref", "effect_intent_fingerprint", "owner_host_id", "owner_host_trust_revision", "owner_host_authentication_epoch", "execution_epoch", "task_fence_generation", "host_fence_generation", "effect_fence_generation", "start_authority_expires_at_utc_ms", "capability_set_fingerprint", "resource_set_fingerprint", "secret_handle_set_fingerprint", "permit_attestation_evidence_fingerprint", "human_presence_binding_fingerprint", "effect_authorization_requirement_fingerprint", "final_handoff_authority_assessment_fingerprint", "expected_result_contract_ref", "expected_result_contract_fingerprint", "handoff_event_sequence", "canonical_fingerprint"]},
}


INHERITED_SCHEMAS: dict[str, dict[str, Any]] = {
    "F4TaskAuthorityBindingV0_1": {"interface_version": "agents-os.f4-task-authority-binding.v0.1", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "task_id", "task_lifecycle_generation", "task_completion_epoch", "task_state_revision", "task_state_fingerprint", "goal_id", "goal_spec_revision", "goal_spec_fingerprint", "goal_plan_membership_revision", "goal_plan_membership_fingerprint", "task_commitment_snapshot_id", "task_commitment_snapshot_fingerprint", "dependency_closure_snapshot_id", "dependency_closure_fingerprint", "task_completion_refs", "completion_assurance_versions", "previous_execution_epoch", "execution_epoch_head_fingerprint", "currentness_event_sequence", "canonical_fingerprint"]},
    "F4ActorAuthorityBindingV0_1": {"interface_version": "agents-os.f4-actor-authority-binding.v0.1", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "actor_id", "actor_identity_revision", "actor_identity_assessment_ref", "actor_identity_assessment_fingerprint", "principal_id", "principal_binding_revision", "principal_binding_assessment_ref", "principal_binding_assessment_fingerprint", "authentication_assessment_ref", "authentication_assessment_fingerprint", "authentication_result", "responsibility_source_kind", "responsibility_source_ref", "responsibility_source_fingerprint", "delegation_chain_fingerprint", "bound_resource_ref", "action_ref", "action_fingerprint", "prohibited_behavior_list_revision", "prohibited_boundary_evidence_ref", "prohibited_boundary_evidence_fingerprint", "authority_event_sequence", "canonical_fingerprint"]},
    "F4ResidentCommandBindingV0_1": {"interface_version": "agents-os.f4-resident-command-binding.v0.1", "fingerprint_field": "canonical_fingerprint", "fields": ["interface_version", "resident_identity_ref", "resident_identity_revision", "resident_incarnation_id", "resident_epoch", "resident_continuity_assessment_ref", "resident_continuity_assessment_fingerprint", "resident_continuity_result", "command_id", "command_fingerprint", "command_type_id", "command_type_version", "command_definition_fingerprint", "command_envelope_ref", "command_envelope_fingerprint", "authenticated_context_ref", "authenticated_context_fingerprint", "authenticated_action_ref", "authenticated_action_fingerprint", "F3_contract_version", "writer_event_sequence", "canonical_fingerprint"]},
    "HumanPresenceBindingV0_1": {"interface_version": None, "fingerprint_field": "canonical_fingerprint", "fields": ["mode", "presence_event_ref", "presence_event_fingerprint", "present_actor_id", "present_actor_identity_revision", "authorized_scope_fingerprint", "observer_host_id", "observed_at_utc_ms", "valid_until_utc_ms", "revocation_event_sequence", "currentness_result", "canonical_fingerprint"]},
    "PermitInvocationIdentityV0_1": {"interface_version": None, "fingerprint_field": "canonical_fingerprint", "fields": ["permit_id", "permit_fingerprint", "invocation_ordinal", "idempotency_key", "execution_epoch", "host_id", "effect_intent_fingerprint", "canonical_fingerprint"]},
    "TaskPermitIssuanceFactV0_1": {"interface_version": None, "fingerprint_field": "fact_fingerprint", "fields": ["permit_ref", "permit_fingerprint", "issuance_command_envelope_ref", "issuance_command_envelope_fingerprint", "issuance_event_sequence", "fact_fingerprint"]},
    "TaskPermitTransitionFactV0_1": {"interface_version": None, "fingerprint_field": "fact_fingerprint", "fields": ["permit_ref", "permit_fingerprint", "transition_kind", "expected_previous_state", "resulting_state", "reason", "transition_action_ref", "transition_action_fingerprint", "event_sequence", "fact_fingerprint"]},
}
SCHEMAS = {**R8_SCHEMAS, **INHERITED_SCHEMAS}


def f4_stamp(schema_name: str, pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    ordered = list(pairs)
    profile = SCHEMAS[schema_name]
    fp_field = profile["fingerprint_field"]
    expected = profile["fields"][:-1]
    names = [name for name, _ in ordered]
    if names != expected or profile["fields"][-1] != fp_field:
        raise ValueError(f"{schema_name} field order mismatch: {names}")
    result = dict(ordered)
    result[fp_field] = digest([F4_FP_PREFIX + schema_name] + [value for _, value in ordered])
    return result


def restamp(schema_name: str, source: dict[str, Any]) -> dict[str, Any]:
    profile = SCHEMAS[schema_name]
    return f4_stamp(schema_name, [(name, copy.deepcopy(source[name])) for name in profile["fields"][:-1]])


def authorization_rows() -> list[dict[str, Any]]:
    policy_fp = label("policy-bundle:revision:1")
    pbl_fp = label("prohibited-behavior-list:revision:1")
    effect_scope_fp = label("effect-scope:synthetic-noop")
    common = [
        ("interface_version", R8_SCHEMAS["EffectAuthorizationRequirementV0_1R8"]["interface_version"]),
        ("requirement_basis_ref", "basis:policy-pbl:m0:r8"),
        ("requirement_basis_fingerprint", label("requirement-basis:policy-pbl")),
        ("policy_bundle_revision", 1),
        ("policy_bundle_fingerprint", policy_fp),
        ("prohibited_behavior_list_revision", 1),
        ("prohibited_behavior_list_fingerprint", pbl_fp),
        ("exact_effect_scope_fingerprint", effect_scope_fp),
    ]
    jenn_present = {
        "Jenn_decision_ref": "jenn-decision:f4:m0:r8",
        "Jenn_decision_fingerprint": label("jenn-decision"),
        "Jenn_actor_identity_ref": "actor:jenn:root",
        "issued_at_utc_ms": 1000,
        "expires_at_utc_ms": 9000,
        "revocation_event_sequence": 0,
        "exact_Jenn_scope_fingerprint": effect_scope_fp,
    }
    rows = [
        ("NO_SEPARATE", "NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED", {}, 2000, 70, "NOT_APPLICABLE", "NO_SEPARATE_REQUIRED"),
        ("EXACT_CURRENT", "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", jenn_present, 2400, 90, "CURRENT", "JENN_DECISION_CURRENT"),
        ("EXACT_MISSING", "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", {}, 2400, 90, "REJECTED", "JENN_DECISION_MISSING"),
        ("EXACT_REVOKED", "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", {**jenn_present, "revocation_event_sequence": 91}, 2400, 91, "REJECTED", "JENN_DECISION_REVOKED"),
        ("EXACT_SCOPE_MISMATCH", "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", {**jenn_present, "exact_Jenn_scope_fingerprint": label("different-jenn-scope")}, 2400, 90, "REJECTED", "JENN_SCOPE_MISMATCH"),
        ("EXACT_EXPIRED", "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", {**jenn_present, "expires_at_utc_ms": 2399}, 2400, 90, "REJECTED", "JENN_DECISION_EXPIRED"),
        ("PROHIBITED", "PROHIBITED_NON_ISSUABLE", {}, 2400, 90, "REJECTED", "PROHIBITED"),
    ]
    output = []
    jenn_fields = ["Jenn_decision_ref", "Jenn_decision_fingerprint", "Jenn_actor_identity_ref", "issued_at_utc_ms", "expires_at_utc_ms", "revocation_event_sequence", "exact_Jenn_scope_fingerprint"]
    for row_id, mode, present, evaluated_at, evaluation_watermark, result, reason in rows:
        pairs = [(common[0][0], common[0][1]), ("mode", mode)] + common[1:]
        pairs += [("evaluated_at_trusted_time_utc_ms", evaluated_at), ("evaluation_watermark_event_sequence", evaluation_watermark)]
        pairs += [(name, present.get(name)) for name in jenn_fields]
        pairs += [("currentness_result", result), ("currentness_reason", reason)]
        requirement = f4_stamp("EffectAuthorizationRequirementV0_1R8", pairs)
        resolution = {
            "interface_version": "agents-os.effect-authorization-requirement-resolution.v0.1-r8",
            "outcome": "REQUIREMENT_RESOLVED",
            "reason": "RESOLVED",
            "requirement_fingerprint": requirement["canonical_fingerprint"],
        }
        output.append({"id": row_id, "resolution": resolution, "requirement": requirement})
    return output


def eligibility_rows(extension: dict[str, Any]) -> list[dict[str, Any]]:
    cases = [
        ("INTEGRITY_FAILURE", "REJECTED", "ACTIVE", "ABSENT", "ABSENT", "INELIGIBLE", "INTEGRITY_FAILURE"),
        ("F2_HISTORY_PRESENT", "PASS", "ACTIVE", "PRESENT", "ABSENT", "INELIGIBLE", "F2_COMPROMISE_HISTORY_PRESENT"),
        ("F4_HISTORY_PRESENT", "PASS", "ACTIVE", "ABSENT", "PRESENT", "INELIGIBLE", "F4_COMPROMISE_HISTORY_PRESENT"),
        ("F2_NOT_ACTIVE", "PASS", "PROVEN_NOT_ACTIVE", "ABSENT", "ABSENT", "INELIGIBLE", "CURRENT_F2_ACTOR_NOT_ACTIVE"),
        ("HISTORY_UNAVAILABLE", "PASS", "ACTIVE", "UNAVAILABLE", "ABSENT", "INDETERMINATE", "HISTORY_UNAVAILABLE"),
        ("CURRENT_F2_UNAVAILABLE", "PASS", "UNAVAILABLE", "ABSENT", "ABSENT", "INDETERMINATE", "CURRENT_F2_INPUT_UNAVAILABLE"),
        ("ELIGIBLE", "PASS", "ACTIVE", "ABSENT", "ABSENT", "ELIGIBLE", "NEVER_COMPROMISED_AND_ALL_CURRENT"),
    ]
    rows = []
    for offset, (row_id, integrity, current, f2hist, f4hist, result, reason) in enumerate(cases):
        current_available = current != "UNAVAILABLE"
        f2_available = f2hist != "UNAVAILABLE"
        f4_available = f4hist != "UNAVAILABLE"
        pairs = [
            ("interface_version", R8_SCHEMAS["F4HostEffectTrustEligibilityAssessmentV0_1R8"]["interface_version"]),
            ("host_actor_identity_ref", extension["host_actor_identity_ref"]),
            ("host_actor_identity_fingerprint", extension["host_actor_identity_fingerprint"]),
            ("integrity_assessment_ref", f"assessment:eligibility-integrity:{row_id.lower()}"),
            ("integrity_assessment_fingerprint", label("eligibility-integrity:" + row_id)),
            ("integrity_observation", integrity),
            ("current_F2_actor_observation", current),
            ("current_F2_actor_assessment_ref", extension["host_actor_identity_assessment_ref"] if current_available else None),
            ("current_F2_actor_assessment_fingerprint", extension["host_actor_identity_assessment_fingerprint"] if current_available else None),
            ("F2_compromise_history_observation", f2hist),
            ("F2_compromise_history_evidence_ref", f"history:f2:{f2hist.lower()}:m0:r8" if f2_available else None),
            ("F2_compromise_history_evidence_fingerprint", label("f2-history:" + f2hist) if f2_available else None),
            ("F4_compromise_history_observation", f4hist),
            ("F4_compromise_history_evidence_ref", f"history:f4:{f4hist.lower()}:m0:r8" if f4_available else None),
            ("F4_compromise_history_evidence_fingerprint", label("f4-history:" + f4hist) if f4_available else None),
            ("assessment_watermark_event_sequence", 60 + offset),
            ("result", result),
            ("reason", reason),
        ]
        rows.append({"id": row_id, "assessment": f4_stamp("F4HostEffectTrustEligibilityAssessmentV0_1R8", pairs)})
    return rows


FINAL_CODES = [
    "CANONICAL_INTEGRITY", "F1_TASK", "F2_ACTOR_PRINCIPAL_BINDING",
    "F2_RESPONSIBILITY_DELEGATION", "F3_RESIDENT_COMMAND",
    "F4_HOST_EFFECT_TRUST", "POLICY", "PROHIBITED_BEHAVIOR_LIST",
    "EFFECT_AUTHORIZATION_REQUIREMENT", "TRUSTED_TIME", "TASK_FENCE",
    "HOST_FENCE", "EFFECT_FENCE",
]


def final_reduce(statuses: dict[str, tuple[str, str]]) -> tuple[str, str]:
    if statuses["CANONICAL_INTEGRITY"][0] == "REJECTED":
        return "REJECTED", "INTEGRITY_FAILURE"
    if any(statuses[code][0] == "REJECTED" for code in FINAL_CODES[1:]):
        return "REJECTED", "AUTHORITY_STALE"
    if any(observation == "INDETERMINATE" or availability == "UNAVAILABLE" for observation, availability in statuses.values()):
        return "INDETERMINATE", "AUTHORITY_UNAVAILABLE"
    return "CURRENT", "ALL_AUTHORITY_CURRENT"


def final_totality_vectors() -> list[dict[str, Any]]:
    vectors: list[dict[str, Any]] = []
    base = {code: ("PASS", "AVAILABLE") for code in FINAL_CODES}
    integrity = dict(base); integrity["CANONICAL_INTEGRITY"] = ("REJECTED", "AVAILABLE"); integrity["F1_TASK"] = ("INDETERMINATE", "UNAVAILABLE")
    vectors.append({"id": "INTEGRITY_OVER_UNAVAILABLE", "statuses": [{"code": code, "observation": integrity[code][0], "evidence_availability": integrity[code][1]} for code in FINAL_CODES], "expected": list(final_reduce(integrity))})
    for code in FINAL_CODES[1:]:
        row = dict(base); row[code] = ("REJECTED", "AVAILABLE")
        vectors.append({"id": "STALE_" + code, "statuses": [{"code": item, "observation": row[item][0], "evidence_availability": row[item][1]} for item in FINAL_CODES], "expected": list(final_reduce(row))})
    for code in FINAL_CODES:
        row = dict(base); row[code] = ("INDETERMINATE", "UNAVAILABLE")
        vectors.append({"id": "UNAVAILABLE_" + code, "statuses": [{"code": item, "observation": row[item][0], "evidence_availability": row[item][1]} for item in FINAL_CODES], "expected": list(final_reduce(row))})
    stale_over_unavailable = dict(base); stale_over_unavailable["F1_TASK"] = ("REJECTED", "AVAILABLE"); stale_over_unavailable["F3_RESIDENT_COMMAND"] = ("INDETERMINATE", "UNAVAILABLE")
    vectors.append({"id": "STALE_OVER_UNAVAILABLE", "statuses": [{"code": item, "observation": stale_over_unavailable[item][0], "evidence_availability": stale_over_unavailable[item][1]} for item in FINAL_CODES], "expected": list(final_reduce(stale_over_unavailable))})
    vectors.append({"id": "ALL_CURRENT", "statuses": [{"code": code, "observation": "PASS", "evidence_availability": "AVAILABLE"} for code in FINAL_CODES], "expected": ["CURRENT", "ALL_AUTHORITY_CURRENT"]})
    return vectors


def source_binding(role: str, source_ref: str, source_fingerprint: str) -> dict[str, Any]:
    return f4_stamp("AuthoritySourceBindingV0_1R8", [
        ("interface_version", R8_SCHEMAS["AuthoritySourceBindingV0_1R8"]["interface_version"]),
        ("role", role), ("source_ref", source_ref), ("source_fingerprint", source_fingerprint),
    ])


def build_fixture() -> dict[str, Any]:
    r7_bytes = R7_FIXTURE.read_bytes()
    r7 = json.loads(r7_bytes)
    by_kind = {node["kind"]: node["object"] for node in r7["nodes"]}
    r7_permit_wrapper = by_kind["TaskPermitV0_1R7AndIssuanceFact"]
    r7_admission = by_kind["HostLocalAdmissionV0_1R7"]
    r7_acceptance = by_kind["HostWorkAcceptanceFactV0_1R7"]
    r7_scope = by_kind["EffectScopeV0_1R7"]

    nodes: list[dict[str, Any]] = []
    base_value = {
        "R7_fixture_file_sha256": hashlib.sha256(r7_bytes).hexdigest(),
        "R7_fixture_canonical_sha256": digest(r7),
        "R7_contract_version": r7["contract_version"],
        "ordered_R7_node_fingerprints": [node["node_fingerprint"] for node in r7["nodes"]],
    }
    nodes.append({"ordinal": 1, "kind": "R7BaseIntegrityV0_1R8", "depends_on_ordinals": [], "object": base_value, "node_fingerprint": digest(["agents-os.f4-r8-complete-node.v0.1", 1, "R7BaseIntegrityV0_1R8", base_value, []])})

    def add(kind: str, obj: Any, dependencies: Iterable[int] = ()) -> int:
        deps = tuple(dict.fromkeys((1,) + tuple(dependencies)))
        ordinal = len(nodes) + 1
        dep_fps = [nodes[index - 1]["node_fingerprint"] for index in deps]
        node_fp = digest(["agents-os.f4-r8-complete-node.v0.1", ordinal, kind, obj, dep_fps])
        nodes.append({"ordinal": ordinal, "kind": kind, "depends_on_ordinals": list(deps), "object": obj, "node_fingerprint": node_fp})
        return ordinal

    auth_rows = authorization_rows()
    auth = copy.deepcopy(auth_rows[0]["requirement"])
    requirement_ref = "requirement:m0:r8"
    n_auth = add("EffectAuthorizationRequirementV0_1R8", {"requirement_ref": requirement_ref, "resolution": copy.deepcopy(auth_rows[0]["resolution"]), "requirement": auth})

    ext = f4_stamp("F2ExecutionHostPrincipalBindingExtensionV0_1R8", [
        ("interface_version", R8_SCHEMAS["F2ExecutionHostPrincipalBindingExtensionV0_1R8"]["interface_version"]),
        ("host_actor_id", "actor:execution-host:m0"), ("host_actor_identity_revision", 3),
        ("host_actor_identity_ref", "actor-revision:execution-host:m0:3"), ("host_actor_identity_fingerprint", label("host-actor:revision:3")),
        ("host_actor_identity_assessment_ref", "assessment:host-actor:m0:3"), ("host_actor_identity_assessment_fingerprint", label("host-actor-assessment:revision:3")),
        ("host_actor_class", "EXECUTION_HOST"), ("host_process_principal_id", "principal:host-process:m0"),
        ("host_process_principal_revision", 2), ("host_process_principal_ref", "principal-revision:host-process:m0:2"),
        ("host_process_principal_fingerprint", label("host-process-principal:revision:2")),
        ("host_process_principal_assessment_ref", "assessment:host-principal:m0:2"), ("host_process_principal_assessment_fingerprint", label("host-principal-assessment:revision:2")),
        ("host_process_principal_class", "HOST_PROCESS"), ("host_process_binding_ref", "binding:host:m0:4"),
        ("host_process_binding_revision", 4), ("host_process_binding_fingerprint", label("host-process-binding:revision:4")),
        ("host_process_binding_assessment_ref", "assessment:host-binding:m0:4"), ("host_process_binding_assessment_fingerprint", label("host-binding-assessment:revision:4")),
        ("provisioning_action_ref", "action:host-provision:m0:r8"), ("provisioning_action_fingerprint", label("host-provision-action:r8")),
        ("provisioning_basis_ref", "basis:accepted-host-provision:m0:r8"), ("provisioning_basis_fingerprint", label("host-provision-basis:r8")),
    ])
    n_ext = add("F2ExecutionHostPrincipalBindingExtensionV0_1R8", ext)

    eligibility = eligibility_rows(ext)
    eligible = copy.deepcopy(eligibility[-1]["assessment"])
    eligibility_ref = "assessment:effect-trust:m0:r8"
    n_elig = add("F4HostEffectTrustEligibilityAssessmentV0_1R8", {"assessment_ref": eligibility_ref, "assessment": eligible}, (n_ext,))

    host_trust_ref = "host-trust:actor:execution-host:m0:7"
    profile_ref = "auth-profile:m0:r8"
    profile_fp = label("authenticator-profile:m0:r8")
    trust = f4_stamp("F4HostTrustRevisionV0_1R8", [
        ("interface_version", R8_SCHEMAS["F4HostTrustRevisionV0_1R8"]["interface_version"]),
        ("host_id", ext["host_actor_id"]), ("host_trust_revision", 7), ("expected_previous_host_trust_revision", 6),
        ("previous_host_trust_ref", "host-trust:actor:execution-host:m0:6"), ("previous_host_trust_fingerprint", label("host-trust:revision:6")),
        ("host_actor_id", ext["host_actor_id"]), ("host_actor_identity_revision", 3), ("host_actor_identity_ref", ext["host_actor_identity_ref"]),
        ("host_actor_identity_fingerprint", ext["host_actor_identity_fingerprint"]), ("host_actor_identity_assessment_ref", ext["host_actor_identity_assessment_ref"]),
        ("host_actor_identity_assessment_fingerprint", ext["host_actor_identity_assessment_fingerprint"]), ("host_process_principal_id", ext["host_process_principal_id"]),
        ("host_process_principal_revision", ext["host_process_principal_revision"]), ("host_process_principal_ref", ext["host_process_principal_ref"]),
        ("host_process_principal_fingerprint", ext["host_process_principal_fingerprint"]), ("host_process_principal_assessment_ref", ext["host_process_principal_assessment_ref"]),
        ("host_process_principal_assessment_fingerprint", ext["host_process_principal_assessment_fingerprint"]), ("host_process_binding_ref", ext["host_process_binding_ref"]),
        ("host_process_binding_revision", ext["host_process_binding_revision"]), ("host_process_binding_fingerprint", ext["host_process_binding_fingerprint"]),
        ("host_process_binding_assessment_ref", ext["host_process_binding_assessment_ref"]), ("host_process_binding_assessment_fingerprint", ext["host_process_binding_assessment_fingerprint"]),
        ("provisioning_action_ref", ext["provisioning_action_ref"]), ("provisioning_action_fingerprint", ext["provisioning_action_fingerprint"]),
        ("provisioning_basis_ref", ext["provisioning_basis_ref"]), ("provisioning_basis_fingerprint", ext["provisioning_basis_fingerprint"]),
        ("transition_kind", "UPDATE"), ("transition_action_ref", "action:host-trust-update:m0:7"), ("transition_action_fingerprint", label("host-trust-update:7")),
        ("transition_authority_basis_ref", "basis:host-trust-update:m0:7"), ("transition_authority_basis_fingerprint", label("host-trust-update-authority:7")),
        ("authenticator_profile_ref", profile_ref), ("authenticator_profile_revision", 2), ("authenticator_profile_fingerprint", profile_fp),
        ("credential_binding_ref", "credential-handle:m0:r8"), ("credential_binding_fingerprint", label("credential-binding:m0:r8")),
        ("lifecycle_state", "ACTIVE"), ("validity_start_utc_ms", 1000), ("validity_end_utc_ms", None), ("issued_event_sequence", 67),
    ])
    n_trust = add("F4HostTrustRevisionV0_1R8", {"host_trust_ref": host_trust_ref, "host_trust": trust}, (n_ext, n_elig))

    r7_auth = by_kind["HostAuthenticationAssessmentV0_1R7"]
    host_auth = f4_stamp("HostAuthenticationAssessmentV0_1R8", [
        ("interface_version", R8_SCHEMAS["HostAuthenticationAssessmentV0_1R8"]["interface_version"]),
        ("host_trust_ref", host_trust_ref), ("host_trust_fingerprint", trust["canonical_fingerprint"]),
        ("host_actor_identity_ref", ext["host_actor_identity_ref"]), ("host_actor_identity_fingerprint", ext["host_actor_identity_fingerprint"]),
        ("host_actor_identity_assessment_ref", ext["host_actor_identity_assessment_ref"]), ("host_actor_identity_assessment_fingerprint", ext["host_actor_identity_assessment_fingerprint"]),
        ("host_process_principal_ref", ext["host_process_principal_ref"]), ("host_process_principal_fingerprint", ext["host_process_principal_fingerprint"]),
        ("host_process_principal_assessment_ref", ext["host_process_principal_assessment_ref"]), ("host_process_principal_assessment_fingerprint", ext["host_process_principal_assessment_fingerprint"]),
        ("host_process_binding_ref", ext["host_process_binding_ref"]), ("host_process_binding_fingerprint", ext["host_process_binding_fingerprint"]),
        ("host_process_binding_assessment_ref", ext["host_process_binding_assessment_ref"]), ("host_process_binding_assessment_fingerprint", ext["host_process_binding_assessment_fingerprint"]),
        ("effect_trust_eligibility_assessment_ref", eligibility_ref), ("effect_trust_eligibility_assessment_fingerprint", eligible["assessment_fingerprint"]),
        ("authenticator_profile_ref", profile_ref), ("authenticator_profile_fingerprint", profile_fp),
        ("challenge_ref", r7_auth["challenge_ref"]), ("challenge_fingerprint", r7_auth["challenge_fingerprint"]),
        ("verifier_identity_ref", r7_auth["verifier_identity_ref"]), ("verifier_profile_ref", r7_auth["verifier_profile_ref"]),
        ("verification_evidence_ref", r7_auth["verification_evidence_ref"]), ("verification_evidence_fingerprint", r7_auth["verification_evidence_fingerprint"]),
        ("host_authentication_epoch", 2), ("trusted_time_utc_ms", 1500), ("valid_until_utc_ms", 5000),
        ("host_revocation_event_sequence", 67), ("result", "AUTHENTICATED"), ("reason", "MATCH"),
    ])
    host_auth_ref = "host-authentication:" + trust["host_id"] + ":7:2"
    n_authn = add("HostAuthenticationAssessmentV0_1R8", {"assessment_ref": host_auth_ref, "assessment": host_auth}, (n_ext, n_elig, n_trust))

    r7_permit = r7_permit_wrapper["permit"]
    task_binding = restamp("F4TaskAuthorityBindingV0_1", r7_permit["task_authority_binding"])
    actor_binding_source = copy.deepcopy(r7_permit["actor_authority_binding"])
    actor_binding_source["prohibited_boundary_evidence_ref"] = "pbl:revision:1"
    actor_binding_source["prohibited_boundary_evidence_fingerprint"] = auth["prohibited_behavior_list_fingerprint"]
    actor_binding = restamp("F4ActorAuthorityBindingV0_1", actor_binding_source)
    resident_binding_source = copy.deepcopy(r7_permit["resident_command_binding"])
    resident_binding = restamp("F4ResidentCommandBindingV0_1", resident_binding_source)
    human_presence = restamp("HumanPresenceBindingV0_1", r7_permit["human_presence_binding"])

    source_specs = [
        ("F1_TASK", task_binding["task_id"], task_binding["canonical_fingerprint"]),
        ("F2_RESPONSIBILITY", actor_binding["responsibility_source_ref"], actor_binding["responsibility_source_fingerprint"]),
        ("F3_COMMAND", resident_binding["command_envelope_ref"], resident_binding["canonical_fingerprint"]),
        ("POLICY", "source:policy:revision:1", auth["policy_bundle_fingerprint"]),
        ("PROHIBITED_BEHAVIOR_LIST", "source:prohibited-behavior-list:revision:1", auth["prohibited_behavior_list_fingerprint"]),
    ]
    sources = [source_binding(*spec) for spec in source_specs]
    source_fps = [entry["canonical_fingerprint"] for entry in sources]
    cap_source_set = digest(["agents-os.f4-capability-source-authority-set.v0.1-r6", source_fps])
    res_source_set = digest(["agents-os.f4-resource-source-scope-set.v0.1-r6", source_fps])
    operation_registry_fp = label("operation-registry:revision:1")
    cap_definition_fp = label("capability-definition:synthetic-noop:revision:1")
    resource_definition_fp = label("resource-definition:synthetic:revision:1")
    constraint_fp = label("capability-constraint:synthetic-noop")
    selector_fp = label("resource-selector:synthetic-m0")
    operation_set = ["SYNTHETIC_NOOP"]
    projection_fps = [entry["source_fingerprint"] for entry in sources]
    cap_proof = f4_stamp("CapabilitySubsetProofV0_1R8", [
        ("interface_version", R8_SCHEMAS["CapabilitySubsetProofV0_1R8"]["interface_version"]),
        ("source_authority_set_fingerprint", cap_source_set), ("capability_definition_fingerprint", cap_definition_fp),
        ("operation_registry_fingerprint", operation_registry_fp), ("requested_operation_set", operation_set),
        ("source_projection_fingerprints", projection_fps), ("exact_intersection_operation_set", operation_set),
        ("constraint_fingerprint", constraint_fp), ("result", "PASS"), ("reason", "EXACT_SUBSET"), ("watermark_event_sequence", 70),
    ])
    capability_proof_ref = "proof:capability-subset:m0:r8"
    n_cap_proof = add("CapabilitySubsetProofV0_1R8", {"proof_ref": capability_proof_ref, "proof": cap_proof}, (n_auth,))
    capability = f4_stamp("CapabilityGrantV0_1R8", [
        ("interface_version", R8_SCHEMAS["CapabilityGrantV0_1R8"]["interface_version"]),
        ("capability_definition_ref", "capability-definition:synthetic-noop:m0"), ("capability_definition_fingerprint", cap_definition_fp),
        ("capability_revision", 1), ("operation_registry_revision", 1), ("operation_registry_fingerprint", operation_registry_fp),
        ("operation_set", operation_set), ("constraint_fingerprint", constraint_fp), ("source_authority_bindings", sources),
        ("source_authority_set_fingerprint", cap_source_set), ("derived_subset_proof_ref", capability_proof_ref),
        ("derived_subset_proof_fingerprint", cap_proof["canonical_fingerprint"]),
    ])
    n_cap = add("CapabilityGrantV0_1R8", capability, (n_cap_proof,))
    resource_assessment = f4_stamp("ResourceContainmentAssessmentV0_1R8", [
        ("interface_version", R8_SCHEMAS["ResourceContainmentAssessmentV0_1R8"]["interface_version"]),
        ("source_scope_set_fingerprint", res_source_set), ("resource_definition_fingerprint", resource_definition_fp),
        ("resource_kind", "SYNTHETIC_M0_RESOURCE"), ("resource_ref", "resource:m0-a:synthetic:001"),
        ("requested_operation_set", operation_set), ("selector_constraint_fingerprint", selector_fp),
        ("source_projection_fingerprints", projection_fps), ("result", "PASS"), ("reason", "EXACT_CONTAINMENT"),
        ("watermark_event_sequence", 70),
    ])
    resource_assessment_ref = "assessment:resource-containment:m0:r8"
    n_res_proof = add("ResourceContainmentAssessmentV0_1R8", {"assessment_ref": resource_assessment_ref, "assessment": resource_assessment}, (n_auth,))
    resource = f4_stamp("ResourceGrantV0_1R8", [
        ("interface_version", R8_SCHEMAS["ResourceGrantV0_1R8"]["interface_version"]),
        ("resource_definition_ref", "resource-definition:synthetic:m0"), ("resource_definition_fingerprint", resource_definition_fp),
        ("resource_kind", "SYNTHETIC_M0_RESOURCE"), ("resource_ref", "resource:m0-a:synthetic:001"),
        ("resource_subject_fingerprint", label("resource-subject:synthetic:001")), ("operation_registry_revision", 1),
        ("operation_registry_fingerprint", operation_registry_fp), ("operation_set", operation_set),
        ("selector_constraint_fingerprint", selector_fp), ("source_scope_bindings", copy.deepcopy(sources)),
        ("source_scope_set_fingerprint", res_source_set), ("containment_assessment_ref", resource_assessment_ref),
        ("containment_assessment_fingerprint", resource_assessment["assessment_fingerprint"]),
    ])
    n_res = add("ResourceGrantV0_1R8", resource, (n_res_proof,))

    cap_set_fp = digest(["agents-os.f4-capability-set.v0.1", [capability["canonical_fingerprint"]]])
    res_set_fp = digest(["agents-os.f4-resource-set.v0.1", [resource["canonical_fingerprint"]]])
    r7_effect = r7_scope["effect_intent_binding"]
    effect = f4_stamp("EffectIntentBindingV0_1R8", [
        ("interface_version", R8_SCHEMAS["EffectIntentBindingV0_1R8"]["interface_version"]),
        ("effect_intent_id", r7_effect["effect_intent_id"]), ("operation_kind", "SYNTHETIC_NOOP"),
        ("target_resource_refs", [resource["resource_ref"]]), ("payload_fingerprint", r7_effect["payload_fingerprint"]),
        ("capability_set_fingerprint", cap_set_fp), ("resource_set_fingerprint", res_set_fp),
        ("expected_result_contract_ref", r7_effect["expected_result_contract_ref"]),
        ("expected_result_contract_fingerprint", r7_effect["expected_result_contract_fingerprint"]),
        ("idempotency_key", r7_effect["idempotency_key"]), ("side_effect_audit_label", "GREEN"),
        ("external_effect_requested", True), ("raw_payload_present", False),
    ])
    n_scope = add("EffectScopeV0_1R8", {"capability_grants": [capability], "resource_grants": [resource], "secret_handle_bindings": [], "capability_set_fingerprint": cap_set_fp, "resource_set_fingerprint": res_set_fp, "secret_handle_set_fingerprint": r7_scope["secret_handle_set_fingerprint"], "effect_intent_binding": effect, "human_presence_binding": human_presence, "effect_authorization_requirement": auth}, (n_auth, n_cap, n_res))

    execution_epoch = 1
    issuance_sequence = r7_permit["issuance_event_sequence"]
    permit_id = digest(["agents-os.task-permit-id.v0.1", task_binding["task_id"], task_binding["task_lifecycle_generation"], execution_epoch, resident_binding["command_id"], host_trust_ref, effect["idempotency_key"], issuance_sequence])
    permit_ref = "permit:" + permit_id
    permit = f4_stamp("TaskPermitV0_1R8", [
        ("interface_version", R8_SCHEMAS["TaskPermitV0_1R8"]["interface_version"]), ("F4_contract_version", CONTRACT),
        ("permit_id", permit_id), ("permit_revision", 1), ("issuance_event_sequence", issuance_sequence),
        ("task_authority_binding", task_binding), ("actor_authority_binding", actor_binding), ("resident_command_binding", resident_binding),
        ("host_trust_ref", host_trust_ref), ("host_trust_fingerprint", trust["canonical_fingerprint"]),
        ("host_authenticator_profile_ref", profile_ref), ("host_authenticator_profile_fingerprint", profile_fp),
        ("host_authentication_assessment_ref", host_auth_ref), ("host_authentication_assessment_fingerprint", host_auth["assessment_fingerprint"]),
        ("host_authentication_epoch", host_auth["host_authentication_epoch"]), ("issuer_resident_identity_ref", r7_permit["issuer_resident_identity_ref"]),
        ("issuer_resident_epoch", r7_permit["issuer_resident_epoch"]), ("policy_bundle_revision", auth["policy_bundle_revision"]),
        ("policy_bundle_fingerprint", auth["policy_bundle_fingerprint"]), ("prohibited_behavior_list_revision", auth["prohibited_behavior_list_revision"]),
        ("prohibited_boundary_evidence_ref", "pbl:revision:1"), ("prohibited_boundary_evidence_fingerprint", auth["prohibited_behavior_list_fingerprint"]),
        ("capability_grants", [capability]), ("resource_grants", [resource]), ("effect_intent_binding", effect),
        ("execution_epoch", execution_epoch), ("host_fence_generation", 1), ("effect_fence_generation", 1), ("task_fence_generation", 1),
        ("issued_at_utc_ms", 2000), ("not_before_utc_ms", 2000), ("expires_at_utc_ms", 10000),
        ("start_authority_commit_before_utc_ms", 5000), ("max_invocations", 1), ("idempotency_key", effect["idempotency_key"]),
        ("requires_human_presence", False), ("human_presence_binding", human_presence), ("effect_authorization_requirement", auth),
        ("secret_handle_bindings", []), ("permit_attestation_profile_ref", r7_permit["permit_attestation_profile_ref"]),
        ("permit_attestation_profile_fingerprint", r7_permit["permit_attestation_profile_fingerprint"]),
        ("permit_attestation_evidence_ref", r7_permit["permit_attestation_evidence_ref"]),
        ("permit_attestation_evidence_fingerprint", r7_permit["permit_attestation_evidence_fingerprint"]),
    ])
    issuance = f4_stamp("TaskPermitIssuanceFactV0_1", [
        ("permit_ref", permit_ref), ("permit_fingerprint", permit["canonical_fingerprint"]),
        ("issuance_command_envelope_ref", resident_binding["command_envelope_ref"]),
        ("issuance_command_envelope_fingerprint", resident_binding["command_envelope_fingerprint"]),
        ("issuance_event_sequence", issuance_sequence),
    ])
    n_permit = add("TaskPermitV0_1R8AndIssuanceFact", {"permit": permit, "issuance_fact": issuance}, (n_authn, n_scope))

    r7_current = by_kind["TaskPermitCurrentnessAssessmentV0_1R7"]
    currentness = f4_stamp("TaskPermitCurrentnessAssessmentV0_1R8", [
        (name, R8_SCHEMAS["TaskPermitCurrentnessAssessmentV0_1R8"]["interface_version"] if name == "interface_version" else permit_ref if name == "permit_ref" else permit["canonical_fingerprint"] if name == "permit_fingerprint" else copy.deepcopy(r7_current[name]))
        for name in R8_SCHEMAS["TaskPermitCurrentnessAssessmentV0_1R8"]["fields"][:-1]
    ])
    currentness_ref = "permit-currentness:" + permit_id + ":80"
    n_current = add("TaskPermitCurrentnessAssessmentV0_1R8", {"assessment_ref": currentness_ref, "assessment": currentness}, (n_permit,))

    inv = f4_stamp("PermitInvocationIdentityV0_1", [
        ("permit_id", permit_id), ("permit_fingerprint", permit["canonical_fingerprint"]), ("invocation_ordinal", 1),
        ("idempotency_key", effect["idempotency_key"]), ("execution_epoch", execution_epoch), ("host_id", trust["host_id"]),
        ("effect_intent_fingerprint", effect["canonical_fingerprint"]),
    ])
    request_ref = "admission-request:" + inv["canonical_fingerprint"]
    request = f4_stamp("HostLocalAdmissionRequestV0_1R8", [
        ("interface_version", R8_SCHEMAS["HostLocalAdmissionRequestV0_1R8"]["interface_version"]), ("invocation_identity", inv),
        ("task_permit_ref", permit_ref), ("task_permit_fingerprint", permit["canonical_fingerprint"]),
        ("effect_intent_ref", "effect-intent:" + effect["effect_intent_id"]), ("effect_intent_fingerprint", effect["canonical_fingerprint"]),
        ("resident_command_envelope_ref", resident_binding["command_envelope_ref"]), ("resident_command_envelope_fingerprint", resident_binding["command_envelope_fingerprint"]),
        ("target_host_id", trust["host_id"]), ("target_host_trust_revision", trust["host_trust_revision"]),
        ("requested_at_utc_ms", 2200), ("request_event_sequence", 81),
    ])
    decision_ref = "admission-decision:" + inv["canonical_fingerprint"]
    r7_decision = r7_admission["decision"]
    decision = f4_stamp("HostLocalAdmissionDecisionV0_1R8", [
        (name, R8_SCHEMAS["HostLocalAdmissionDecisionV0_1R8"]["interface_version"] if name == "interface_version" else inv["canonical_fingerprint"] if name == "invocation_identity_fingerprint" else request_ref if name == "request_ref" else request["canonical_fingerprint"] if name == "request_fingerprint" else currentness_ref if name == "permit_currentness_assessment_ref" else currentness["assessment_fingerprint"] if name == "permit_currentness_assessment_fingerprint" else host_auth_ref if name == "host_authentication_assessment_ref" else host_auth["assessment_fingerprint"] if name == "host_authentication_assessment_fingerprint" else copy.deepcopy(r7_decision[name]))
        for name in R8_SCHEMAS["HostLocalAdmissionDecisionV0_1R8"]["fields"][:-1]
    ])
    n_admission = add("HostLocalAdmissionV0_1R8", {"invocation_identity": inv, "request_ref": request_ref, "request": request, "decision_ref": decision_ref, "decision": decision}, (n_authn, n_current))

    observation_evidence = {
        "CANONICAL_INTEGRITY": ("assessment:canonical-integrity:m0:r8", label("canonical-integrity")),
        "F1_TASK": ("assessment:f1-task:m0:r8", task_binding["canonical_fingerprint"]),
        "F2_ACTOR_PRINCIPAL_BINDING": ("assessment:f2-actor-principal-binding:m0:r8", ext["canonical_fingerprint"]),
        "F2_RESPONSIBILITY_DELEGATION": ("assessment:f2-responsibility:m0:r8", actor_binding["canonical_fingerprint"]),
        "F3_RESIDENT_COMMAND": ("assessment:f3-resident-command:m0:r8", resident_binding["canonical_fingerprint"]),
        "F4_HOST_EFFECT_TRUST": ("assessment:f4-host-effect-trust:m0:r8", trust["canonical_fingerprint"]),
        "POLICY": ("policy:revision:1", auth["policy_bundle_fingerprint"]),
        "PROHIBITED_BEHAVIOR_LIST": ("pbl:revision:1", auth["prohibited_behavior_list_fingerprint"]),
        "EFFECT_AUTHORIZATION_REQUIREMENT": (requirement_ref, auth["canonical_fingerprint"]),
        "TRUSTED_TIME": ("trusted-time:m0:2400", label("trusted-time:2400")),
        "TASK_FENCE": ("fence:task:m0:1", label("task-fence:1")),
        "HOST_FENCE": ("fence:host:m0:1", label("host-fence:1")),
        "EFFECT_FENCE": ("fence:effect:m0:1", label("effect-fence:1")),
    }
    final_observations = [f4_stamp("FinalAuthorityObservationV0_1R8", [
        ("interface_version", R8_SCHEMAS["FinalAuthorityObservationV0_1R8"]["interface_version"]),
        ("code", code), ("observation", "PASS"), ("evidence_availability", "AVAILABLE"),
        ("evidence_ref", observation_evidence[code][0]), ("evidence_fingerprint", observation_evidence[code][1]),
    ]) for code in FINAL_CODES]
    final_set_fp = digest(["agents-os.f4-final-authority-observation-set.v0.1-r8", [item["canonical_fingerprint"] for item in final_observations]])
    final_assessment = f4_stamp("FinalHandoffAuthorityAssessmentV0_1R8", [
        ("interface_version", R8_SCHEMAS["FinalHandoffAuthorityAssessmentV0_1R8"]["interface_version"]),
        ("permit_ref", permit_ref), ("permit_fingerprint", permit["canonical_fingerprint"]),
        ("authority_observations", final_observations), ("authority_observation_set_fingerprint", final_set_fp),
        ("trusted_time_utc_ms", 2400), ("watermark_event_sequence", 90),
        ("result", "CURRENT"), ("reason", "ALL_AUTHORITY_CURRENT"),
    ])
    final_ref = "final-authority-assessment:" + permit_id + ":90"
    n_final = add("FinalHandoffAuthorityAssessmentV0_1R8", {"assessment_ref": final_ref, "assessment": final_assessment}, (n_auth, n_authn, n_permit))

    acceptance_id = digest(["agents-os.host-work-acceptance-id.v0.1", inv["canonical_fingerprint"]])
    acceptance_ref = "acceptance:" + acceptance_id
    r7_acc = r7_acceptance["acceptance"]
    acceptance = f4_stamp("HostWorkAcceptanceFactV0_1R8", [
        ("interface_version", R8_SCHEMAS["HostWorkAcceptanceFactV0_1R8"]["interface_version"]), ("acceptance_id", acceptance_id),
        ("invocation_identity", inv), ("admission_request_ref", request_ref), ("admission_request_fingerprint", request["canonical_fingerprint"]),
        ("admission_decision_ref", decision_ref), ("admission_decision_fingerprint", decision["decision_fingerprint"]),
        ("permit_currentness_assessment_ref", currentness_ref), ("permit_currentness_assessment_fingerprint", currentness["assessment_fingerprint"]),
        ("host_authentication_assessment_ref", host_auth_ref), ("host_authentication_assessment_fingerprint", host_auth["assessment_fingerprint"]),
        ("accepted_host_id", trust["host_id"]), ("accepted_host_trust_revision", trust["host_trust_revision"]),
        ("accepted_host_authentication_epoch", host_auth["host_authentication_epoch"]), ("accepted_task_fence_generation", 1),
        ("accepted_host_fence_generation", 1), ("accepted_effect_fence_generation", 1), ("accepted_execution_epoch", execution_epoch),
        ("accepted_watermark_event_sequence", 84), ("accepted_at_utc_ms", 2300), ("start_authority_expires_at_utc_ms", 5000),
        ("host_acceptance_attestation_ref", r7_acc["host_acceptance_attestation_ref"]),
        ("host_acceptance_attestation_fingerprint", r7_acc["host_acceptance_attestation_fingerprint"]),
    ])
    transition = f4_stamp("TaskPermitTransitionFactV0_1", [
        ("permit_ref", permit_ref), ("permit_fingerprint", permit["canonical_fingerprint"]), ("transition_kind", "ACTIVATE"),
        ("expected_previous_state", "ISSUED"), ("resulting_state", "ACTIVE"), ("reason", "HOST_ACCEPTANCE"),
        ("transition_action_ref", acceptance_ref), ("transition_action_fingerprint", acceptance["fact_fingerprint"]), ("event_sequence", 84),
    ])
    n_accept = add("HostWorkAcceptanceFactV0_1R8", {"acceptance_ref": acceptance_ref, "acceptance": acceptance, "activation_transition": transition}, (n_admission,))

    observation_attempt = 1
    observation_id = digest(["agents-os.host-work-start-observation-id.v0.1", acceptance["fact_fingerprint"], observation_attempt])
    start_disposition_ref = "observation:" + observation_id
    disposition = f4_stamp("HostWorkStartDispositionFactV0_1R8", [
        ("interface_version", R8_SCHEMAS["HostWorkStartDispositionFactV0_1R8"]["interface_version"]),
        ("observation_id", observation_id), ("observation_attempt", observation_attempt), ("acceptance_ref", acceptance_ref),
        ("acceptance_fingerprint", acceptance["fact_fingerprint"]), ("invocation_identity_fingerprint", inv["canonical_fingerprint"]),
        ("observed_host_id", trust["host_id"]), ("observed_host_trust_revision", trust["host_trust_revision"]),
        ("observed_host_authentication_epoch", host_auth["host_authentication_epoch"]), ("rechecked_task_fence_generation", 1),
        ("rechecked_host_fence_generation", 1), ("rechecked_effect_fence_generation", 1), ("rechecked_execution_epoch", execution_epoch),
        ("rechecked_secret_handle_set_fingerprint", r7_scope["secret_handle_set_fingerprint"]),
        ("rechecked_permit_attestation_fingerprint", permit["permit_attestation_evidence_fingerprint"]),
        ("rechecked_human_presence_binding_fingerprint", human_presence["canonical_fingerprint"]),
        ("final_handoff_authority_assessment_ref", final_ref), ("final_handoff_authority_assessment_fingerprint", final_assessment["assessment_fingerprint"]),
        ("secret_handles_current", "NOT_APPLICABLE"), ("permit_attestation_current", "PASS"), ("human_presence_current", "NOT_APPLICABLE"),
        ("final_handoff_authority_current", "PASS"), ("disposition", "START_AUTHORITY_CURRENT"), ("reason", "ALL_RECHECKS_PASS"),
        ("observed_at_utc_ms", 2400), ("observation_event_sequence", 91),
        ("host_observation_attestation_ref", "attestation:host-observation:m0:r8"),
        ("host_observation_attestation_fingerprint", label("host-observation-attestation:r8")),
    ])
    n_disposition = add("HostWorkStartDispositionFactV0_1R8", {"start_disposition_ref": start_disposition_ref, "disposition": disposition}, (n_final, n_accept))

    handoff_id = digest(["agents-os.f4-accepted-effect-handoff-id.v0.1", inv["canonical_fingerprint"]])
    handoff_ref = "handoff:" + handoff_id
    handoff = f4_stamp("F4AcceptedEffectHandoffV0_1R8", [
        ("interface_version", R8_SCHEMAS["F4AcceptedEffectHandoffV0_1R8"]["interface_version"]), ("handoff_id", handoff_id),
        ("acceptance_ref", acceptance_ref), ("acceptance_fingerprint", acceptance["fact_fingerprint"]),
        ("start_disposition_ref", start_disposition_ref), ("start_disposition_fingerprint", disposition["fact_fingerprint"]),
        ("invocation_identity", inv), ("task_permit_ref", permit_ref), ("task_permit_fingerprint", permit["canonical_fingerprint"]),
        ("effect_intent_ref", "effect-intent:" + effect["effect_intent_id"]), ("effect_intent_fingerprint", effect["canonical_fingerprint"]),
        ("owner_host_id", trust["host_id"]), ("owner_host_trust_revision", trust["host_trust_revision"]),
        ("owner_host_authentication_epoch", host_auth["host_authentication_epoch"]), ("execution_epoch", execution_epoch),
        ("task_fence_generation", 1), ("host_fence_generation", 1), ("effect_fence_generation", 1),
        ("start_authority_expires_at_utc_ms", 5000), ("capability_set_fingerprint", cap_set_fp), ("resource_set_fingerprint", res_set_fp),
        ("secret_handle_set_fingerprint", r7_scope["secret_handle_set_fingerprint"]),
        ("permit_attestation_evidence_fingerprint", permit["permit_attestation_evidence_fingerprint"]),
        ("human_presence_binding_fingerprint", human_presence["canonical_fingerprint"]),
        ("effect_authorization_requirement_fingerprint", auth["canonical_fingerprint"]),
        ("final_handoff_authority_assessment_fingerprint", final_assessment["assessment_fingerprint"]),
        ("expected_result_contract_ref", effect["expected_result_contract_ref"]),
        ("expected_result_contract_fingerprint", effect["expected_result_contract_fingerprint"]), ("handoff_event_sequence", 91),
    ])
    n_handoff = add("F4AcceptedEffectHandoffV0_1R8", {"handoff_ref": handoff_ref, "handoff": handoff}, (n_auth, n_final, n_disposition))
    stub = {"interface_version": "agents-os.f5-boundary-zero-effect-stub.v0.1-r8", "handoff_ref": handoff_ref, "handoff_fingerprint": handoff["canonical_fingerprint"], "claim_state": "NOT_CLAIMED", "physical_effect_crossed": False, "terminal_outcome": "NOT_EXECUTED", "external_effect_count": 0, "provider_call_count": 0, "raw_secret_count": 0}
    add("F5BoundaryZeroEffectStubV0_1R8", stub, (n_handoff,))

    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f4-r8-complete-effective-m0a-witness.v0.1",
        "contract_version": CONTRACT,
        "canonical_profile": {
            "fingerprint_prefix": F4_FP_PREFIX,
            "schema_name_by_kind": {name: name for name in SCHEMAS},
            "schemas": {name: {"interface_version": spec["interface_version"], "fingerprint_field": spec["fingerprint_field"], "ordered_field_names": spec["fields"]} for name, spec in SCHEMAS.items()},
        },
        "authorization_totality_vectors": auth_rows,
        "authorization_invalid_input_summary": {"mixed_Jenn_presence_masks_rejected": 126, "unknown_mode_result": ["NO_REQUIREMENT_OBJECT", "INVALID_INPUT"], "contradictory_input_result": ["NO_REQUIREMENT_OBJECT", "INVALID_INPUT"]},
        "eligibility_totality_vectors": eligibility,
        "final_authority_code_order": FINAL_CODES,
        "final_authority_totality_vectors": final_totality_vectors(),
        "nodes": nodes,
        "assertions": {
            "host_actor_identity_revision": 3, "host_trust_revision": 7, "max_invocations": 1,
            "authorization_valid_requirement_count": 7, "authorization_resolution_count": 7,
            "eligibility_materialized_row_count": 7, "final_authority_code_count": 13,
            "final_authority_vector_count": len(final_totality_vectors()), "acceptance_count": 1,
            "accepted_handoff_count": 1, "external_effect_count": 0, "provider_call_count": 0,
            "raw_secret_count": 0, "terminal_outcome": "NOT_EXECUTED",
        },
    }

    def pointer_escape(value: str) -> str:
        return value.replace("~", "~0").replace("/", "~1")

    inventory: list[dict[str, Any]] = []
    profiles_by_fields = [(name, spec) for name, spec in SCHEMAS.items()]

    def discover(value: Any, pointer: str) -> None:
        if isinstance(value, dict):
            keys = list(value)
            for schema_name, spec in profiles_by_fields:
                if keys == spec["fields"]:
                    inventory.append({"json_pointer": pointer, "exact_schema_name": schema_name, "interface_version": spec["interface_version"], "fingerprint_field": spec["fingerprint_field"], "ordered_field_names": spec["fields"]})
                    break
            for key, child in value.items():
                discover(child, pointer + "/" + pointer_escape(key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                discover(child, pointer + "/" + str(index))

    discover(fixture, "")
    fixture["effective_schema_inventory"] = inventory
    fixture["assertions"]["effective_schema_inventory_count"] = len(inventory)
    fixture["assertions"]["node_count"] = len(nodes)
    return fixture


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None, help="write the generated fixture to this path")
    parser.add_argument("--compact", action="store_true", help="emit compact JSON")
    args = parser.parse_args()
    fixture = build_fixture()
    rendered = json.dumps(fixture, ensure_ascii=False, sort_keys=False, separators=(",", ":") if args.compact else None, indent=None if args.compact else 2) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
