#!/usr/bin/env python3
"""Independent semantic validator for the F4 R8 complete-effective witness.

This validator deliberately does not import, execute, or compare against the R8
fixture builder.  It accepts an arbitrary JSON fixture and checks the frozen R8
profile from independent constants and reducers below.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
DEFAULT = (
    HERE
    / "examples"
    / "2026-07-16-agents-os-f4-r8-complete-effective-m0a-witness-v0.1.json"
)
CONTRACT = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R8_ATOMIC_BUNDLE"
FP_PREFIX = "agents-os.f4-fingerprint.v0.1:"
NODE_DOMAIN = "agents-os.f4-r8-complete-node.v0.1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class ValidationError(AssertionError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _reject_float(_: str) -> Any:
    raise ValidationError("floating-point JSON numbers are forbidden")


def _reject_constant(value: str) -> Any:
    raise ValidationError(f"non-JSON numeric constant is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in out, f"duplicate JSON object key: {key!r}")
        out[key] = value
    return out


def load_strict(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValidationError("fixture is not strict UTF-8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValidationError) as exc:
        raise ValidationError(f"invalid strict JSON: {exc}") from exc
    require(isinstance(value, dict), "fixture root must be an object")
    _validate_lexical_tree(value)
    return value, raw


def _validate_lexical_tree(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        require(0 <= value <= MAX_SAFE_INTEGER, f"unsafe or negative integer at {path}")
        return
    if isinstance(value, float):
        raise ValidationError(f"floating-point value at {path}")
    if isinstance(value, str):
        require(unicodedata.normalize("NFC", value) == value, f"non-NFC string at {path}")
        require("\0" not in value, f"NUL in string at {path}")
        require(value == value.strip(), f"edge whitespace in string at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_lexical_tree(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _validate_lexical_tree(key, f"{path}.<key>")
            _validate_lexical_tree(item, f"{path}.{key}")
        return
    raise ValidationError(f"unsupported JSON value at {path}: {type(value).__name__}")


def jcs(value: Any) -> bytes:
    """JCS for the R8 integer-only JSON profile."""
    _validate_lexical_tree(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256(value: Any) -> str:
    return hashlib.sha256(jcs(value)).hexdigest()


def f4_fp(exact_schema_name: str, preceding_values: list[Any]) -> str:
    return sha256([FP_PREFIX + exact_schema_name, *preceding_values])


def identity_fp(domain: str, *values: Any) -> str:
    return sha256([domain, *values])


def ordered_keys(obj: dict[str, Any], expected: tuple[str, ...], where: str) -> None:
    actual = tuple(obj.keys())
    require(actual == expected, f"{where} field order/inventory mismatch: {actual!r}")


def require_hash(value: Any, where: str) -> None:
    require(isinstance(value, str) and HASH_RE.fullmatch(value) is not None, f"bad SHA-256 at {where}")


def require_ref(value: Any, where: str) -> None:
    require(isinstance(value, str) and 1 <= len(value.encode("utf-8")) <= 512, f"bad stable ref at {where}")


def fingerprint_object(
    obj: dict[str, Any],
    schema_name: str,
    fields: tuple[str, ...],
    fingerprint_field: str,
    where: str,
) -> None:
    ordered_keys(obj, (*fields, fingerprint_field), where)
    require_hash(obj[fingerprint_field], f"{where}.{fingerprint_field}")
    expected = f4_fp(schema_name, [obj[name] for name in fields])
    require(obj[fingerprint_field] == expected, f"{where} fingerprint/domain mismatch")


def sorted_unique_utf8(values: list[str], where: str) -> None:
    require(all(isinstance(value, str) for value in values), f"{where} contains non-string")
    require(values == sorted(values, key=lambda value: value.encode("utf-8")), f"{where} not UTF-8 sorted")
    require(len(values) == len(set(values)), f"{where} contains duplicates")


def _walk(value: Any):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


REMOVED_FIELDS = {
    "Jenn_authorization_binding",
    "Jenn_authorization_binding_fingerprint",
    "Jenn_authorization_current",
    "side_effect_class",
    "source_authority_refs",
    "source_scope_refs",
    "target_host_identity_revision",
    "accepted_host_identity_revision",
    "observed_host_identity_revision",
    "owner_host_identity_revision",
}
REMOVED_VALUES = {"ACCEPTANCE_MISSING"}


def reject_removed_surface(value: Any) -> None:
    for item in _walk(value):
        if isinstance(item, dict):
            overlap = REMOVED_FIELDS.intersection(item)
            require(not overlap, f"removed field(s) present: {sorted(overlap)!r}")
        elif isinstance(item, str):
            require(item not in REMOVED_VALUES, f"removed value present: {item}")


AUTH_MODES = {
    "NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED",
    "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED",
    "PROHIBITED_NON_ISSUABLE",
}
JENN_FIELDS = (
    "Jenn_decision_ref",
    "Jenn_decision_fingerprint",
    "Jenn_actor_identity_ref",
    "issued_at_utc_ms",
    "expires_at_utc_ms",
    "revocation_event_sequence",
    "exact_Jenn_scope_fingerprint",
)


def authorization_reduce(
    mode: str,
    presence_mask: int,
    condition: str,
) -> tuple[str, str, str]:
    """Total R8 authorization reducer; invalid tuples raise ValidationError."""
    require(mode in AUTH_MODES, "unknown authorization mode")
    require(0 <= presence_mask < 128, "invalid Jenn field presence mask")
    if mode == "NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED":
        require(presence_mask == 0 and condition == "NO_SEPARATE_REQUIRED", "invalid no-separate tuple")
        return "REQUIREMENT", "NOT_APPLICABLE", "NO_SEPARATE_REQUIRED"
    if mode == "PROHIBITED_NON_ISSUABLE":
        require(presence_mask == 0 and condition == "PROHIBITED", "invalid prohibited tuple")
        return "REQUIREMENT", "REJECTED", "PROHIBITED"
    if condition == "JENN_DECISION_MISSING":
        require(presence_mask == 0, "missing plus present Jenn fields is invalid")
        return "REQUIREMENT", "REJECTED", condition
    require(presence_mask == 127, "exact Jenn decision requires all seven fields")
    table = {
        "JENN_DECISION_CURRENT": ("REQUIREMENT", "CURRENT", "JENN_DECISION_CURRENT"),
        "JENN_DECISION_REVOKED": ("REQUIREMENT", "REJECTED", "JENN_DECISION_REVOKED"),
        "JENN_SCOPE_MISMATCH": ("REQUIREMENT", "REJECTED", "JENN_SCOPE_MISMATCH"),
        "JENN_DECISION_EXPIRED": ("REQUIREMENT", "REJECTED", "JENN_DECISION_EXPIRED"),
    }
    require(condition in table, "unknown exact-Jenn condition")
    return table[condition]


ELIGIBILITY_PRECEDENCE = (
    "INTEGRITY_FAILURE",
    "F2_COMPROMISE_HISTORY_PRESENT",
    "F4_COMPROMISE_HISTORY_PRESENT",
    "CURRENT_F2_ACTOR_NOT_ACTIVE",
    "HISTORY_UNAVAILABLE",
    "CURRENT_F2_INPUT_UNAVAILABLE",
)


def eligibility_reduce(conditions: set[str]) -> tuple[str, str]:
    require(conditions <= set(ELIGIBILITY_PRECEDENCE), "unknown eligibility condition")
    for reason in ELIGIBILITY_PRECEDENCE:
        if reason in conditions:
            if reason in {"HISTORY_UNAVAILABLE", "CURRENT_F2_INPUT_UNAVAILABLE"}:
                return "INDETERMINATE", reason
            return "INELIGIBLE", reason
    return "ELIGIBLE", "NEVER_COMPROMISED_AND_ALL_CURRENT"


FINAL_OBSERVATION_CODES: tuple[str, ...] = (
    "CANONICAL_INTEGRITY",
    "F1_TASK",
    "F2_ACTOR_PRINCIPAL_BINDING",
    "F2_RESPONSIBILITY_DELEGATION",
    "F3_RESIDENT_COMMAND",
    "F4_HOST_EFFECT_TRUST",
    "POLICY",
    "PROHIBITED_BEHAVIOR_LIST",
    "EFFECT_AUTHORIZATION_REQUIREMENT",
    "TRUSTED_TIME",
    "TASK_FENCE",
    "HOST_FENCE",
    "EFFECT_FENCE",
)


def final_authority_reduce(observations: dict[str, str]) -> tuple[str, str]:
    require(tuple(observations) == FINAL_OBSERVATION_CODES, "final-authority observation inventory/order mismatch")
    statuses = set(observations.values())
    require(statuses <= {"CURRENT", "STALE", "UNAVAILABLE", "INTEGRITY_FAILURE"}, "unknown final-authority status")
    if "INTEGRITY_FAILURE" in statuses:
        return "REJECTED", "INTEGRITY_FAILURE"
    if "STALE" in statuses:
        return "REJECTED", "AUTHORITY_STALE"
    if "UNAVAILABLE" in statuses:
        return "INDETERMINATE", "AUTHORITY_UNAVAILABLE"
    return "CURRENT", "ALL_AUTHORITY_CURRENT"


def node_fingerprint(node: dict[str, Any], dependency_fingerprints: list[str]) -> str:
    return sha256(
        [
            NODE_DOMAIN,
            node["ordinal"],
            node["kind"],
            node["object"],
            dependency_fingerprints,
        ]
    )


def resign_nodes(fixture: dict[str, Any]) -> None:
    """Re-sign outer DAG nodes only; used by adversarial semantic mutations."""
    nodes = fixture["nodes"]
    for node in nodes:
        dependency_fingerprints = [nodes[index - 1]["node_fingerprint"] for index in node["depends_on_ordinals"]]
        node["node_fingerprint"] = node_fingerprint(node, dependency_fingerprints)


def _fields(csv: str) -> tuple[str, ...]:
    return tuple(csv.split())


# Exact interface version, fingerprint field, and preceding field order.  This
# is an independent transcription of the R8 amendment registry plus the nine
# explicitly inherited R1 schemas.  It is not read from fixture metadata.
SCHEMAS: dict[str, tuple[str | None, str, tuple[str, ...]]] = {
    "EffectAuthorizationRequirementV0_1R8": (
        "agents-os.effect-authorization-requirement.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version mode requirement_basis_ref requirement_basis_fingerprint policy_bundle_revision policy_bundle_fingerprint prohibited_behavior_list_revision prohibited_behavior_list_fingerprint exact_effect_scope_fingerprint evaluated_at_trusted_time_utc_ms evaluation_watermark_event_sequence Jenn_decision_ref Jenn_decision_fingerprint Jenn_actor_identity_ref issued_at_utc_ms expires_at_utc_ms revocation_event_sequence exact_Jenn_scope_fingerprint currentness_result currentness_reason"),
    ),
    "F2ExecutionHostPrincipalBindingExtensionV0_1R8": (
        "agents-os.f2-execution-host-principal-binding-extension.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version host_actor_id host_actor_identity_revision host_actor_identity_ref host_actor_identity_fingerprint host_actor_identity_assessment_ref host_actor_identity_assessment_fingerprint host_actor_class host_process_principal_id host_process_principal_revision host_process_principal_ref host_process_principal_fingerprint host_process_principal_assessment_ref host_process_principal_assessment_fingerprint host_process_principal_class host_process_binding_ref host_process_binding_revision host_process_binding_fingerprint host_process_binding_assessment_ref host_process_binding_assessment_fingerprint provisioning_action_ref provisioning_action_fingerprint provisioning_basis_ref provisioning_basis_fingerprint"),
    ),
    "F4HostEffectTrustEligibilityAssessmentV0_1R8": (
        "agents-os.f4-host-effect-trust-eligibility.v0.1-r8", "assessment_fingerprint",
        _fields("interface_version host_actor_identity_ref host_actor_identity_fingerprint integrity_assessment_ref integrity_assessment_fingerprint integrity_observation current_F2_actor_observation current_F2_actor_assessment_ref current_F2_actor_assessment_fingerprint F2_compromise_history_observation F2_compromise_history_evidence_ref F2_compromise_history_evidence_fingerprint F4_compromise_history_observation F4_compromise_history_evidence_ref F4_compromise_history_evidence_fingerprint assessment_watermark_event_sequence result reason"),
    ),
    "F4HostTrustRevisionV0_1R8": (
        "agents-os.f4-host-trust-revision.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version host_id host_trust_revision expected_previous_host_trust_revision previous_host_trust_ref previous_host_trust_fingerprint host_actor_id host_actor_identity_revision host_actor_identity_ref host_actor_identity_fingerprint host_actor_identity_assessment_ref host_actor_identity_assessment_fingerprint host_process_principal_id host_process_principal_revision host_process_principal_ref host_process_principal_fingerprint host_process_principal_assessment_ref host_process_principal_assessment_fingerprint host_process_binding_ref host_process_binding_revision host_process_binding_fingerprint host_process_binding_assessment_ref host_process_binding_assessment_fingerprint provisioning_action_ref provisioning_action_fingerprint provisioning_basis_ref provisioning_basis_fingerprint transition_kind transition_action_ref transition_action_fingerprint transition_authority_basis_ref transition_authority_basis_fingerprint authenticator_profile_ref authenticator_profile_revision authenticator_profile_fingerprint credential_binding_ref credential_binding_fingerprint lifecycle_state validity_start_utc_ms validity_end_utc_ms issued_event_sequence"),
    ),
    "HostAuthenticationAssessmentV0_1R8": (
        "agents-os.host-authentication-assessment.v0.1-r8", "assessment_fingerprint",
        _fields("interface_version host_trust_ref host_trust_fingerprint host_actor_identity_ref host_actor_identity_fingerprint host_actor_identity_assessment_ref host_actor_identity_assessment_fingerprint host_process_principal_ref host_process_principal_fingerprint host_process_principal_assessment_ref host_process_principal_assessment_fingerprint host_process_binding_ref host_process_binding_fingerprint host_process_binding_assessment_ref host_process_binding_assessment_fingerprint effect_trust_eligibility_assessment_ref effect_trust_eligibility_assessment_fingerprint authenticator_profile_ref authenticator_profile_fingerprint challenge_ref challenge_fingerprint verifier_identity_ref verifier_profile_ref verification_evidence_ref verification_evidence_fingerprint host_authentication_epoch trusted_time_utc_ms valid_until_utc_ms host_revocation_event_sequence result reason"),
    ),
    "AuthoritySourceBindingV0_1R8": (
        "agents-os.authority-source-binding.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version role source_ref source_fingerprint"),
    ),
    "CapabilitySubsetProofV0_1R8": (
        "agents-os.capability-subset-proof.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version source_authority_set_fingerprint capability_definition_fingerprint operation_registry_fingerprint requested_operation_set source_projection_fingerprints exact_intersection_operation_set constraint_fingerprint result reason watermark_event_sequence"),
    ),
    "CapabilityGrantV0_1R8": (
        "agents-os.capability-grant.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version capability_definition_ref capability_definition_fingerprint capability_revision operation_registry_revision operation_registry_fingerprint operation_set constraint_fingerprint source_authority_bindings source_authority_set_fingerprint derived_subset_proof_ref derived_subset_proof_fingerprint"),
    ),
    "ResourceContainmentAssessmentV0_1R8": (
        "agents-os.resource-containment-assessment.v0.1-r8", "assessment_fingerprint",
        _fields("interface_version source_scope_set_fingerprint resource_definition_fingerprint resource_kind resource_ref requested_operation_set selector_constraint_fingerprint source_projection_fingerprints result reason watermark_event_sequence"),
    ),
    "ResourceGrantV0_1R8": (
        "agents-os.resource-grant.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version resource_definition_ref resource_definition_fingerprint resource_kind resource_ref resource_subject_fingerprint operation_registry_revision operation_registry_fingerprint operation_set selector_constraint_fingerprint source_scope_bindings source_scope_set_fingerprint containment_assessment_ref containment_assessment_fingerprint"),
    ),
    "EffectIntentBindingV0_1R8": (
        "agents-os.effect-intent-binding.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version effect_intent_id operation_kind target_resource_refs payload_fingerprint capability_set_fingerprint resource_set_fingerprint expected_result_contract_ref expected_result_contract_fingerprint idempotency_key side_effect_audit_label external_effect_requested raw_payload_present"),
    ),
    "TaskPermitV0_1R8": (
        "agents-os.task-permit.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version F4_contract_version permit_id permit_revision issuance_event_sequence task_authority_binding actor_authority_binding resident_command_binding host_trust_ref host_trust_fingerprint host_authenticator_profile_ref host_authenticator_profile_fingerprint host_authentication_assessment_ref host_authentication_assessment_fingerprint host_authentication_epoch issuer_resident_identity_ref issuer_resident_epoch policy_bundle_revision policy_bundle_fingerprint prohibited_behavior_list_revision prohibited_boundary_evidence_ref prohibited_boundary_evidence_fingerprint capability_grants resource_grants effect_intent_binding execution_epoch host_fence_generation effect_fence_generation task_fence_generation issued_at_utc_ms not_before_utc_ms expires_at_utc_ms start_authority_commit_before_utc_ms max_invocations idempotency_key requires_human_presence human_presence_binding effect_authorization_requirement secret_handle_bindings permit_attestation_profile_ref permit_attestation_profile_fingerprint permit_attestation_evidence_ref permit_attestation_evidence_fingerprint"),
    ),
    "TaskPermitCurrentnessAssessmentV0_1R8": (
        "agents-os.task-permit-currentness-assessment.v0.1-r8", "assessment_fingerprint",
        _fields("interface_version permit_ref permit_fingerprint lifecycle_state trusted_time_utc_ms task_binding_current actor_binding_current resident_command_binding_current host_trust_current host_authentication_current policy_current prohibited_boundary_current capability_grants_current resource_grants_current secret_handle_bindings_current permit_attestation_current human_presence_current effect_authorization_requirement_current time_window_current invocation_available execution_epoch_current host_fence_current effect_fence_current task_fence_current result reason assessment_event_sequence"),
    ),
    "HostLocalAdmissionRequestV0_1R8": (
        "agents-os.host-local-admission-request.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version invocation_identity task_permit_ref task_permit_fingerprint effect_intent_ref effect_intent_fingerprint resident_command_envelope_ref resident_command_envelope_fingerprint target_host_id target_host_trust_revision requested_at_utc_ms request_event_sequence"),
    ),
    "HostLocalAdmissionDecisionV0_1R8": (
        "agents-os.host-local-admission-decision.v0.1-r8", "decision_fingerprint",
        _fields("interface_version invocation_identity_fingerprint request_ref request_fingerprint permit_currentness_assessment_ref permit_currentness_assessment_fingerprint host_authentication_assessment_ref host_authentication_assessment_fingerprint fence_state_ref fence_state_fingerprint current_watermark_event_sequence request_integrity permit_currentness host_authentication host_ownership task_fence_match host_fence_match effect_fence_match execution_epoch_match capability_subset resource_subset secret_handle_scope permit_attestation human_presence effect_intent_exact_match idempotency_identity_match invocation_slot_available prohibited_boundary effect_authorization_requirement_current decision reason decided_at_utc_ms"),
    ),
    "FinalAuthorityObservationV0_1R8": (
        "agents-os.final-authority-observation.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version code observation evidence_availability evidence_ref evidence_fingerprint"),
    ),
    "FinalHandoffAuthorityAssessmentV0_1R8": (
        "agents-os.final-handoff-authority-assessment.v0.1-r8", "assessment_fingerprint",
        _fields("interface_version permit_ref permit_fingerprint authority_observations authority_observation_set_fingerprint trusted_time_utc_ms watermark_event_sequence result reason"),
    ),
    "HostWorkAcceptanceFactV0_1R8": (
        "agents-os.host-work-acceptance-fact.v0.1-r8", "fact_fingerprint",
        _fields("interface_version acceptance_id invocation_identity admission_request_ref admission_request_fingerprint admission_decision_ref admission_decision_fingerprint permit_currentness_assessment_ref permit_currentness_assessment_fingerprint host_authentication_assessment_ref host_authentication_assessment_fingerprint accepted_host_id accepted_host_trust_revision accepted_host_authentication_epoch accepted_task_fence_generation accepted_host_fence_generation accepted_effect_fence_generation accepted_execution_epoch accepted_watermark_event_sequence accepted_at_utc_ms start_authority_expires_at_utc_ms host_acceptance_attestation_ref host_acceptance_attestation_fingerprint"),
    ),
    "HostWorkStartDispositionFactV0_1R8": (
        "agents-os.host-work-start-disposition-fact.v0.1-r8", "fact_fingerprint",
        _fields("interface_version observation_id observation_attempt acceptance_ref acceptance_fingerprint invocation_identity_fingerprint observed_host_id observed_host_trust_revision observed_host_authentication_epoch rechecked_task_fence_generation rechecked_host_fence_generation rechecked_effect_fence_generation rechecked_execution_epoch rechecked_secret_handle_set_fingerprint rechecked_permit_attestation_fingerprint rechecked_human_presence_binding_fingerprint final_handoff_authority_assessment_ref final_handoff_authority_assessment_fingerprint secret_handles_current permit_attestation_current human_presence_current final_handoff_authority_current disposition reason observed_at_utc_ms observation_event_sequence host_observation_attestation_ref host_observation_attestation_fingerprint"),
    ),
    "F4AcceptedEffectHandoffV0_1R8": (
        "agents-os.f4-accepted-effect-handoff.v0.1-r8", "canonical_fingerprint",
        _fields("interface_version handoff_id acceptance_ref acceptance_fingerprint start_disposition_ref start_disposition_fingerprint invocation_identity task_permit_ref task_permit_fingerprint effect_intent_ref effect_intent_fingerprint owner_host_id owner_host_trust_revision owner_host_authentication_epoch execution_epoch task_fence_generation host_fence_generation effect_fence_generation start_authority_expires_at_utc_ms capability_set_fingerprint resource_set_fingerprint secret_handle_set_fingerprint permit_attestation_evidence_fingerprint human_presence_binding_fingerprint effect_authorization_requirement_fingerprint final_handoff_authority_assessment_fingerprint expected_result_contract_ref expected_result_contract_fingerprint handoff_event_sequence"),
    ),
    # Unchanged embedded R1 schemas, now fingerprinted by the R8 F4_FP profile.
    "F4TaskAuthorityBindingV0_1": (
        "agents-os.f4-task-authority-binding.v0.1", "canonical_fingerprint",
        _fields("interface_version task_id task_lifecycle_generation task_completion_epoch task_state_revision task_state_fingerprint goal_id goal_spec_revision goal_spec_fingerprint goal_plan_membership_revision goal_plan_membership_fingerprint task_commitment_snapshot_id task_commitment_snapshot_fingerprint dependency_closure_snapshot_id dependency_closure_fingerprint task_completion_refs completion_assurance_versions previous_execution_epoch execution_epoch_head_fingerprint currentness_event_sequence"),
    ),
    "F4ActorAuthorityBindingV0_1": (
        "agents-os.f4-actor-authority-binding.v0.1", "canonical_fingerprint",
        _fields("interface_version actor_id actor_identity_revision actor_identity_assessment_ref actor_identity_assessment_fingerprint principal_id principal_binding_revision principal_binding_assessment_ref principal_binding_assessment_fingerprint authentication_assessment_ref authentication_assessment_fingerprint authentication_result responsibility_source_kind responsibility_source_ref responsibility_source_fingerprint delegation_chain_fingerprint bound_resource_ref action_ref action_fingerprint prohibited_behavior_list_revision prohibited_boundary_evidence_ref prohibited_boundary_evidence_fingerprint authority_event_sequence"),
    ),
    "F4ResidentCommandBindingV0_1": (
        "agents-os.f4-resident-command-binding.v0.1", "canonical_fingerprint",
        _fields("interface_version resident_identity_ref resident_identity_revision resident_incarnation_id resident_epoch resident_continuity_assessment_ref resident_continuity_assessment_fingerprint resident_continuity_result command_id command_fingerprint command_type_id command_type_version command_definition_fingerprint command_envelope_ref command_envelope_fingerprint authenticated_context_ref authenticated_context_fingerprint authenticated_action_ref authenticated_action_fingerprint F3_contract_version writer_event_sequence"),
    ),
    "HumanPresenceBindingV0_1": (
        None, "canonical_fingerprint",
        _fields("mode presence_event_ref presence_event_fingerprint present_actor_id present_actor_identity_revision authorized_scope_fingerprint observer_host_id observed_at_utc_ms valid_until_utc_ms revocation_event_sequence currentness_result"),
    ),
    "SecretHandleBindingV0_1": (
        None, "canonical_fingerprint",
        _fields("handle_ref handle_revision handle_binding_fingerprint owner_host_id permitted_use_fingerprint revocation_head_fingerprint raw_value_present"),
    ),
    "F4FenceStateV0_1": (
        "agents-os.f4-fence-state.v0.1", "canonical_fingerprint",
        _fields("interface_version task_id task_lifecycle_generation host_id execution_epoch task_fence_generation host_fence_generation effect_fence_generation fence_reason source_event_ref source_event_fingerprint event_sequence"),
    ),
    "PermitInvocationIdentityV0_1": (
        None, "canonical_fingerprint",
        _fields("permit_id permit_fingerprint invocation_ordinal idempotency_key execution_epoch host_id effect_intent_fingerprint"),
    ),
    "TaskPermitIssuanceFactV0_1": (
        None, "fact_fingerprint",
        _fields("permit_ref permit_fingerprint issuance_command_envelope_ref issuance_command_envelope_fingerprint issuance_event_sequence"),
    ),
    "TaskPermitTransitionFactV0_1": (
        None, "fact_fingerprint",
        _fields("permit_ref permit_fingerprint transition_kind expected_previous_state resulting_state reason transition_action_ref transition_action_fingerprint event_sequence"),
    ),
}

R7_BASE_FILE_SHA256 = "57141c7c470f4424c3bff43cf2d410550200309c27d3b400dba69257e019666b"
R7_BASE_CANONICAL_SHA256 = "2ad2151a6077c66a39303e47a2db0d547b4aa501fffd3f8d80b19634e5e11fe5"
R7_BASE_CONTRACT = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R7_ATOMIC_BUNDLE"
R7_BASE_NODE_FINGERPRINTS = (
    "64b9ac0298cf0cfbcf1f09e5ee0c82ad17351972a6bd6a994b8c35721b4de3e2",
    "460d45a2d0f3cb930003ce09a18c3dd3529a7cf6117f9732c73f354f52fad4ee",
    "d78fc795286860ee5ff3f06cd30470c8ada8e96e32a875ea9d228bacf0afbcb1",
    "31a2cfee3ed04d5cedd3bac44f55bbe34303fa6b3e1d2e025d4d9066dd5787ef",
    "3c076daad00b21b8ed1db5d896d6606b8574d2ea5d13d6bf6964aef2328189de",
    "0b43d94beb938bd7b6cb010b81ba4db7a57c677fc6f70ca3586f27809d38e59b",
    "c310e3d0efd554c3af96562d72c6eb63f6afba723dc7fd4ae05a4c31de9607a4",
    "636e9ffda27dcc7e9f52ed02c6be0304196edaecb2f2a02ef70bdc8c40570255",
    "0d0307a999bbc9ce93fbac186dba1f0bab9e308c917e32f63469633d8540d4c0",
    "c3440182e4655768d145cb48152d9ea88286dedb7603d197a65e101b102e1cd7",
    "2e34952952509cbde939f36104be92011ecab510c00a8436c8fc49e830c90f5e",
    "25b8505c34286c6cd56fa923b6f43d5ea0669f2552fc4d51c96837231f73474a",
    "25bcaeef0f9dffd7b7c73303d6b4e4782a01cf17b2b21b50f12b97acf924b98c",
    "cb725a4da30790b8a80d42d8e76062c4d0672a6c951c4f0dbb4aa0aa6eb14e33",
    "d11b03ae7f161ecbcb5fcf7b4e657bde8581b650c7aebb276021e9784e66d9ac",
    "c0aeee31d161694144f34be080b02b0a3e25d5864e606ece4078038556817355",
    "9b509fc6e74d5349dba14216987e448d6a0bf9be8e352358d3df787731280f12",
    "db996f36210bf1b48179d7221f034ef9cc70349e5fb83b1240121dd0bab5d17e",
)


def json_pointer(root: Any, pointer: str) -> Any:
    require(pointer.startswith("/"), f"invalid JSON pointer: {pointer!r}")
    current = root
    for encoded in pointer[1:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            require(token.isdigit(), f"non-index list pointer component: {token!r}")
            current = current[int(token)]
        elif isinstance(current, dict):
            require(token in current, f"missing JSON pointer component: {token!r}")
            current = current[token]
        else:
            raise ValidationError(f"JSON pointer traverses scalar at {token!r}")
    return current


def _candidate_schema_objects(value: Any, pointer: str = "") -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if isinstance(value, dict):
        fingerprint_names = {profile[1] for profile in SCHEMAS.values()}
        if any(name in value for name in fingerprint_names):
            matching = [
                schema_name
                for schema_name, (_, fingerprint_field, fields) in SCHEMAS.items()
                if tuple(value) == (*fields, fingerprint_field)
            ]
            if matching:
                out[pointer or "/"] = value
        for key, child in value.items():
            child_pointer = pointer + "/" + key.replace("~", "~0").replace("/", "~1")
            out.update(_candidate_schema_objects(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            out.update(_candidate_schema_objects(child, pointer + f"/{index}"))
    return out


def validate_inventory(fixture: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    inventory = fixture["effective_schema_inventory"]
    require(isinstance(inventory, list) and inventory, "effective_schema_inventory must be nonempty")
    exact_entry_fields = (
        "json_pointer",
        "exact_schema_name",
        "interface_version",
        "fingerprint_field",
        "ordered_field_names",
    )
    by_schema: dict[str, list[dict[str, Any]]] = {}
    seen_pointers: set[str] = set()
    for index, entry in enumerate(inventory):
        require(isinstance(entry, dict), f"inventory[{index}] is not an object")
        ordered_keys(entry, exact_entry_fields, f"inventory[{index}]")
        pointer = entry["json_pointer"]
        schema_name = entry["exact_schema_name"]
        require(pointer not in seen_pointers, f"duplicate inventory pointer: {pointer}")
        seen_pointers.add(pointer)
        require(schema_name in SCHEMAS, f"unknown inventory schema: {schema_name}")
        interface_version, fingerprint_field, fields = SCHEMAS[schema_name]
        require(entry["interface_version"] == interface_version, f"inventory interface mismatch: {pointer}")
        require(entry["fingerprint_field"] == fingerprint_field, f"inventory fingerprint-field mismatch: {pointer}")
        require(entry["ordered_field_names"] == [*fields, fingerprint_field], f"inventory field order mismatch: {pointer}")
        obj = json_pointer(fixture, pointer)
        require(isinstance(obj, dict), f"inventory pointer is not an object: {pointer}")
        validate_schema_object(obj, schema_name, pointer)
        by_schema.setdefault(schema_name, []).append(obj)
    candidates = _candidate_schema_objects(fixture)
    # Node fingerprints and the inventory's metadata are not normative schema
    # objects; every actual F4 schema-shaped object must otherwise be listed.
    unlisted = set(candidates).difference(seen_pointers)
    require(not unlisted, f"schema-shaped object(s) missing from inventory: {sorted(unlisted)!r}")
    require(set(candidates) == seen_pointers, "inventory contains non-schema or incomplete object pointers")
    return by_schema


def unique_objects(by_schema: dict[str, list[dict[str, Any]]], schema_name: str) -> list[dict[str, Any]]:
    unique: dict[bytes, dict[str, Any]] = {}
    for obj in by_schema.get(schema_name, []):
        unique[jcs(obj)] = obj
    require(unique, f"missing required schema: {schema_name}")
    return list(unique.values())


def one_unique(by_schema: dict[str, list[dict[str, Any]]], schema_name: str) -> dict[str, Any]:
    objects = unique_objects(by_schema, schema_name)
    require(len(objects) == 1, f"expected one unique {schema_name}, got {len(objects)}")
    return objects[0]


def validate_authorization(by_schema: dict[str, list[dict[str, Any]]], fixture: dict[str, Any]) -> dict[str, Any]:
    rows = unique_objects(by_schema, "EffectAuthorizationRequirementV0_1R8")
    require(len(rows) == 7, f"expected seven persisted authorization rows, got {len(rows)}")
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        mask = sum((row[field] is not None) << index for index, field in enumerate(JENN_FIELDS))
        expected = authorization_reduce(row["mode"], mask, row["currentness_reason"])
        actual = ("REQUIREMENT", row["currentness_result"], row["currentness_reason"])
        require(actual == expected, f"authorization reducer mismatch: {actual!r} != {expected!r}")
        require(isinstance(row["evaluated_at_trusted_time_utc_ms"], int), "authorization trusted time missing")
        require(isinstance(row["evaluation_watermark_event_sequence"], int), "authorization watermark missing")
        reason = row["currentness_reason"]
        if reason == "JENN_DECISION_CURRENT":
            require(row["issued_at_utc_ms"] <= row["evaluated_at_trusted_time_utc_ms"] < row["expires_at_utc_ms"], "current Jenn decision time relation invalid")
            require(row["revocation_event_sequence"] <= row["evaluation_watermark_event_sequence"], "current Jenn revocation head is from the future")
            require(row["exact_Jenn_scope_fingerprint"] == row["exact_effect_scope_fingerprint"], "current Jenn scope mismatch")
        elif reason == "JENN_DECISION_REVOKED":
            require(0 < row["revocation_event_sequence"] <= row["evaluation_watermark_event_sequence"], "revoked Jenn decision is not visible at watermark")
        elif reason == "JENN_SCOPE_MISMATCH":
            require(row["exact_Jenn_scope_fingerprint"] != row["exact_effect_scope_fingerprint"], "scope-mismatch row has equal scopes")
        elif reason == "JENN_DECISION_EXPIRED":
            require(row["evaluated_at_trusted_time_utc_ms"] >= row["expires_at_utc_ms"], "expired Jenn decision has not expired")
        seen.add((row["mode"], row["currentness_result"], row["currentness_reason"]))
    expected_rows = {
        ("NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED", "NOT_APPLICABLE", "NO_SEPARATE_REQUIRED"),
        ("PROHIBITED_NON_ISSUABLE", "REJECTED", "PROHIBITED"),
        ("EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", "REJECTED", "JENN_DECISION_MISSING"),
        ("EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", "CURRENT", "JENN_DECISION_CURRENT"),
        ("EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", "REJECTED", "JENN_DECISION_REVOKED"),
        ("EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", "REJECTED", "JENN_SCOPE_MISMATCH"),
        ("EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", "REJECTED", "JENN_DECISION_EXPIRED"),
    }
    require(seen == expected_rows, "authorization legal-row set mismatch")
    mixed_rejected = 0
    for mask in range(1, 127):
        try:
            authorization_reduce("EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED", mask, "JENN_DECISION_CURRENT")
        except ValidationError:
            mixed_rejected += 1
    require(mixed_rejected == 126, "not all 126 mixed Jenn masks reject")
    for mode in ("UNKNOWN", "", "EXACT"):
        try:
            authorization_reduce(mode, 0, "JENN_DECISION_MISSING")
        except ValidationError:
            continue
        raise ValidationError(f"unknown authorization mode did not reject: {mode!r}")
    # Transport no-object rows are evidence, never persisted authority.  Their
    # exact materialization is validated when present.
    resolutions = fixture.get("authorization_totality_vectors")
    if resolutions is not None:
        require(isinstance(resolutions, list), "authorization resolutions must be a list")
        allowed_no_object = {
            ("NO_REQUIREMENT_OBJECT", "MODE_INPUT_INTEGRITY_CONFLICT", None),
            ("NO_REQUIREMENT_OBJECT", "MODE_INPUT_UNAVAILABLE", None),
            ("NO_REQUIREMENT_OBJECT", "INVALID_INPUT", None),
        }
        observed_no_object: set[tuple[Any, Any, Any]] = set()
        for index, wrapper in enumerate(resolutions):
            resolution = wrapper.get("resolution", wrapper) if isinstance(wrapper, dict) else wrapper
            require(isinstance(resolution, dict), f"authorization resolution {index} not an object")
            ordered_keys(
                resolution,
                ("interface_version", "outcome", "reason", "requirement_fingerprint"),
                f"authorization resolution {index}",
            )
            require(
                resolution["interface_version"] == "agents-os.effect-authorization-requirement-resolution.v0.1-r8",
                "wrong authorization resolution interface",
            )
            key = (resolution["outcome"], resolution["reason"], resolution["requirement_fingerprint"])
            if resolution["outcome"] == "NO_REQUIREMENT_OBJECT":
                observed_no_object.add(key)
            else:
                require(resolution["outcome"] == "REQUIREMENT_RESOLVED", "unknown authorization resolution outcome")
                require_hash(resolution["requirement_fingerprint"], "authorization resolution fingerprint")
        if observed_no_object:
            require(allowed_no_object <= observed_no_object, "missing required no-object authorization resolution rows")
    invalid = fixture["authorization_invalid_input_summary"]
    ordered_keys(
        invalid,
        ("mixed_Jenn_presence_masks_rejected", "unknown_mode_result", "contradictory_input_result"),
        "authorization_invalid_input_summary",
    )
    require(invalid["mixed_Jenn_presence_masks_rejected"] == 126, "fixture does not assert 126 mixed-mask rejections")
    require(invalid["unknown_mode_result"] == ["NO_REQUIREMENT_OBJECT", "INVALID_INPUT"], "unknown-mode summary is fail-open")
    require(invalid["contradictory_input_result"] == ["NO_REQUIREMENT_OBJECT", "INVALID_INPUT"], "contradictory-input summary is fail-open")
    return {"authorization_legal_row_count": 7, "mixed_authorization_masks_rejected": mixed_rejected}


def _eligibility_expected(row: dict[str, Any]) -> tuple[str, str]:
    conditions: set[str] = set()
    integrity = row["integrity_observation"]
    current = row["current_F2_actor_observation"]
    f2_history = row["F2_compromise_history_observation"]
    f4_history = row["F4_compromise_history_observation"]
    require(integrity in {"PASS", "REJECTED"}, "invalid eligibility integrity observation")
    require(current in {"ACTIVE", "PROVEN_NOT_ACTIVE", "INDETERMINATE", "UNAVAILABLE"}, "invalid current F2 observation")
    require(f2_history in {"PRESENT", "ABSENT", "INDETERMINATE", "UNAVAILABLE"}, "invalid F2 history observation")
    require(f4_history in {"PRESENT", "ABSENT", "INDETERMINATE", "UNAVAILABLE"}, "invalid F4 history observation")
    if integrity == "REJECTED": conditions.add("INTEGRITY_FAILURE")
    if f2_history == "PRESENT": conditions.add("F2_COMPROMISE_HISTORY_PRESENT")
    if f4_history == "PRESENT": conditions.add("F4_COMPROMISE_HISTORY_PRESENT")
    if current == "PROVEN_NOT_ACTIVE": conditions.add("CURRENT_F2_ACTOR_NOT_ACTIVE")
    if f2_history in {"INDETERMINATE", "UNAVAILABLE"} or f4_history in {"INDETERMINATE", "UNAVAILABLE"}:
        conditions.add("HISTORY_UNAVAILABLE")
    if current in {"INDETERMINATE", "UNAVAILABLE"}: conditions.add("CURRENT_F2_INPUT_UNAVAILABLE")
    return eligibility_reduce(conditions)


def validate_eligibility(by_schema: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = unique_objects(by_schema, "F4HostEffectTrustEligibilityAssessmentV0_1R8")
    require(len(rows) == 7, f"expected seven eligibility rows, got {len(rows)}")
    seen: set[tuple[str, str]] = set()
    for row in rows:
        current_refs = (row["current_F2_actor_assessment_ref"], row["current_F2_actor_assessment_fingerprint"])
        f2_refs = (row["F2_compromise_history_evidence_ref"], row["F2_compromise_history_evidence_fingerprint"])
        f4_refs = (row["F4_compromise_history_evidence_ref"], row["F4_compromise_history_evidence_fingerprint"])
        require((current_refs == (None, None)) == (row["current_F2_actor_observation"] == "UNAVAILABLE"), "current F2 presence rule mismatch")
        require((f2_refs == (None, None)) == (row["F2_compromise_history_observation"] == "UNAVAILABLE"), "F2 history presence rule mismatch")
        require((f4_refs == (None, None)) == (row["F4_compromise_history_observation"] == "UNAVAILABLE"), "F4 history presence rule mismatch")
        for pair, where in ((current_refs, "current F2"), (f2_refs, "F2 history"), (f4_refs, "F4 history")):
            require((pair[0] is None) == (pair[1] is None), f"partial ref/fingerprint pair: {where}")
            if pair[0] is not None:
                require_ref(pair[0], where); require_hash(pair[1], where)
        require(isinstance(row["assessment_watermark_event_sequence"], int), "eligibility watermark missing")
        expected = _eligibility_expected(row)
        actual = (row["result"], row["reason"])
        require(actual == expected, f"eligibility reducer mismatch: {actual!r} != {expected!r}")
        seen.add(actual)
    expected_results = {
        ("INELIGIBLE", "INTEGRITY_FAILURE"),
        ("INELIGIBLE", "F2_COMPROMISE_HISTORY_PRESENT"),
        ("INELIGIBLE", "F4_COMPROMISE_HISTORY_PRESENT"),
        ("INELIGIBLE", "CURRENT_F2_ACTOR_NOT_ACTIVE"),
        ("INDETERMINATE", "HISTORY_UNAVAILABLE"),
        ("INDETERMINATE", "CURRENT_F2_INPUT_UNAVAILABLE"),
        ("ELIGIBLE", "NEVER_COMPROMISED_AND_ALL_CURRENT"),
    }
    require(seen == expected_results, "eligibility seven-row result set mismatch")
    precedence_checked = 0
    for mask in range(64):
        conditions = {reason for index, reason in enumerate(ELIGIBILITY_PRECEDENCE) if mask & (1 << index)}
        result = eligibility_reduce(conditions)
        expected_reason = next((reason for reason in ELIGIBILITY_PRECEDENCE if reason in conditions), None)
        if expected_reason is None:
            expected = ("ELIGIBLE", "NEVER_COMPROMISED_AND_ALL_CURRENT")
        elif expected_reason in {"HISTORY_UNAVAILABLE", "CURRENT_F2_INPUT_UNAVAILABLE"}:
            expected = ("INDETERMINATE", expected_reason)
        else:
            expected = ("INELIGIBLE", expected_reason)
        require(result == expected, "eligibility precedence is not total")
        precedence_checked += 1
    eligible = [row for row in rows if row["result"] == "ELIGIBLE"]
    require(len(eligible) == 1, "expected one eligible Host row")
    return eligible[0], {"eligibility_row_count": 7, "eligibility_precedence_combinations_checked": precedence_checked}


def validate_final_authority(
    fixture: dict[str, Any], by_schema: dict[str, list[dict[str, Any]]], permit_ref: str, permit_fingerprint: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    assessments = unique_objects(by_schema, "FinalHandoffAuthorityAssessmentV0_1R8")
    require(len(assessments) == 1, "constructive graph must emit exactly one final-authority assessment")
    seen_results: set[tuple[str, str]] = set()
    for assessment in assessments:
        observations = assessment["authority_observations"]
        require(isinstance(observations, list) and len(observations) == 13, "final authority requires exactly 13 observations")
        require(tuple(item["code"] for item in observations) == FINAL_OBSERVATION_CODES, "final-authority code order mismatch")
        reduced_input: dict[str, str] = {}
        fingerprints: list[str] = []
        for index, observation in enumerate(observations):
            validate_schema_object(observation, "FinalAuthorityObservationV0_1R8", f"final observation {index}")
            availability = observation["evidence_availability"]
            state = observation["observation"]
            if availability == "AVAILABLE":
                require(state in {"PASS", "REJECTED"}, "available final observation has invalid state")
                require_ref(observation["evidence_ref"], "final observation evidence ref")
                require_hash(observation["evidence_fingerprint"], "final observation evidence fingerprint")
                reduced_input[observation["code"]] = "CURRENT" if state == "PASS" else "STALE"
            elif availability == "UNAVAILABLE":
                require(state == "INDETERMINATE", "unavailable final observation must be INDETERMINATE")
                require(observation["evidence_ref"] is None and observation["evidence_fingerprint"] is None, "unavailable final observation carries evidence")
                reduced_input[observation["code"]] = "UNAVAILABLE"
            else:
                raise ValidationError("unknown final observation availability")
            if observation["code"] == "CANONICAL_INTEGRITY" and state == "REJECTED":
                reduced_input[observation["code"]] = "INTEGRITY_FAILURE"
            fingerprints.append(observation["canonical_fingerprint"])
        set_fp = identity_fp("agents-os.f4-final-authority-observation-set.v0.1-r8", fingerprints)
        require(assessment["authority_observation_set_fingerprint"] == set_fp, "final observation-set fingerprint mismatch")
        require(assessment["permit_ref"] == permit_ref and assessment["permit_fingerprint"] == permit_fingerprint, "final authority permit binding mismatch")
        expected = final_authority_reduce(reduced_input)
        actual = (assessment["result"], assessment["reason"])
        require(actual == expected, f"final-authority reducer mismatch: {actual!r} != {expected!r}")
        seen_results.add(actual)
    vectors = fixture["final_authority_totality_vectors"]
    require(isinstance(vectors, list) and len(vectors) == 28, "final-authority totality vector count must be 28")
    vector_results: set[tuple[str, str]] = set()
    vector_ids: set[str] = set()
    for index, vector in enumerate(vectors):
        ordered_keys(vector, ("id", "statuses", "expected"), f"final vector {index}")
        require(vector["id"] not in vector_ids, f"duplicate final vector id: {vector['id']}")
        vector_ids.add(vector["id"])
        statuses = vector["statuses"]
        require(isinstance(statuses, list) and len(statuses) == 13, f"final vector {index} does not have 13 statuses")
        reduced_input: dict[str, str] = {}
        for status in statuses:
            ordered_keys(status, ("code", "observation", "evidence_availability"), f"final vector {index} status")
            code = status["code"]
            observation = status["observation"]
            availability = status["evidence_availability"]
            if availability == "AVAILABLE":
                require(observation in {"PASS", "REJECTED"}, "invalid available final-vector status")
                reduced_input[code] = "CURRENT" if observation == "PASS" else "STALE"
            elif availability == "UNAVAILABLE":
                require(observation == "INDETERMINATE", "invalid unavailable final-vector status")
                reduced_input[code] = "UNAVAILABLE"
            else:
                raise ValidationError("unknown final-vector availability")
            if code == "CANONICAL_INTEGRITY" and observation == "REJECTED":
                reduced_input[code] = "INTEGRITY_FAILURE"
        require(tuple(reduced_input) == FINAL_OBSERVATION_CODES, f"final vector {index} code inventory/order mismatch")
        expected = final_authority_reduce(reduced_input)
        require(vector["expected"] == list(expected), f"final vector {index} reducer mismatch")
        vector_results.add(expected)
    require(
        vector_results == {
            ("REJECTED", "INTEGRITY_FAILURE"),
            ("REJECTED", "AUTHORITY_STALE"),
            ("INDETERMINATE", "AUTHORITY_UNAVAILABLE"),
            ("CURRENT", "ALL_AUTHORITY_CURRENT"),
        },
        "final-authority vector outcome set incomplete",
    )
    current = [row for row in assessments if row["result"] == "CURRENT"]
    require(len(current) == 1, "expected one current final-authority assessment")
    return current[0], {"final_authority_vector_count": len(vectors), "final_authority_observation_count": 13}


def validate_dag(fixture: dict[str, Any]) -> dict[str, Any]:
    nodes = fixture["nodes"]
    require(isinstance(nodes, list) and len(nodes) >= 18, "incomplete effective DAG")
    kinds: set[str] = set()
    for index, node in enumerate(nodes, 1):
        ordered_keys(node, ("ordinal", "kind", "depends_on_ordinals", "object", "node_fingerprint"), f"node {index}")
        require(node["ordinal"] == index, f"non-contiguous node ordinal {index}")
        require(isinstance(node["kind"], str) and node["kind"] not in kinds, f"duplicate/invalid node kind at {index}")
        kinds.add(node["kind"])
        dependencies = node["depends_on_ordinals"]
        require(isinstance(dependencies, list), f"node {index} dependencies not list")
        require(dependencies == sorted(set(dependencies)), f"node {index} dependencies not sorted unique")
        require(all(isinstance(dep, int) and 1 <= dep < index for dep in dependencies), f"node {index} has non-acyclic dependency")
        if index == 1:
            require(dependencies == [], "base-integrity node must have no dependency")
        else:
            require(1 in dependencies, f"node {index} lacks direct base-integrity dependency")
        dependency_fingerprints = [nodes[dep - 1]["node_fingerprint"] for dep in dependencies]
        require_hash(node["node_fingerprint"], f"node {index} fingerprint")
        require(node["node_fingerprint"] == node_fingerprint(node, dependency_fingerprints), f"node {index} fingerprint mismatch")
    base = nodes[0]["object"]
    require(isinstance(base, dict), "base-integrity object is not a map")
    ordered_keys(
        base,
        ("R7_fixture_file_sha256", "R7_fixture_canonical_sha256", "R7_contract_version", "ordered_R7_node_fingerprints"),
        "R7 base integrity",
    )
    require(base["R7_fixture_file_sha256"] == R7_BASE_FILE_SHA256, "wrong immutable R7 fixture hash")
    require(base["R7_fixture_canonical_sha256"] == R7_BASE_CANONICAL_SHA256, "wrong immutable R7 canonical hash")
    require(base["R7_contract_version"] == R7_BASE_CONTRACT, "wrong immutable R7 contract literal")
    require(tuple(base["ordered_R7_node_fingerprints"]) == R7_BASE_NODE_FINGERPRINTS, "R7 base node fingerprint inventory mismatch")
    return {"node_count": len(nodes), "node_hashes_verified": len(nodes), "base_dependency_count": len(nodes) - 1}


def validate_host_chain(
    by_schema: dict[str, list[dict[str, Any]]], eligible: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    extension = one_unique(by_schema, "F2ExecutionHostPrincipalBindingExtensionV0_1R8")
    trust = one_unique(by_schema, "F4HostTrustRevisionV0_1R8")
    authentication = one_unique(by_schema, "HostAuthenticationAssessmentV0_1R8")
    permit = one_unique(by_schema, "TaskPermitV0_1R8")
    require(extension["host_actor_class"] == "EXECUTION_HOST", "Host Actor class is not EXECUTION_HOST")
    require(extension["host_process_principal_class"] == "HOST_PROCESS", "Host Principal class is not HOST_PROCESS")
    require(extension["host_actor_identity_revision"] == 3, "Host Actor revision must be 3")
    require(trust["host_trust_revision"] == 7, "Host-trust revision must be 7")
    require(trust["expected_previous_host_trust_revision"] == 6, "Host-trust CAS predecessor must be revision 6")
    require(trust["previous_host_trust_ref"] is not None and trust["previous_host_trust_fingerprint"] is not None, "Host-trust update lacks predecessor binding")
    require(trust["transition_kind"] == "UPDATE", "Host-trust revision 7 is not an UPDATE")
    require(trust["host_actor_identity_revision"] == 3, "Host trust does not bind Actor revision 3")
    equality_fields = (
        "host_actor_id", "host_actor_identity_revision", "host_actor_identity_ref",
        "host_actor_identity_fingerprint", "host_actor_identity_assessment_ref",
        "host_actor_identity_assessment_fingerprint", "host_process_principal_id",
        "host_process_principal_revision", "host_process_principal_ref",
        "host_process_principal_fingerprint", "host_process_principal_assessment_ref",
        "host_process_principal_assessment_fingerprint", "host_process_binding_ref",
        "host_process_binding_revision", "host_process_binding_fingerprint",
        "host_process_binding_assessment_ref", "host_process_binding_assessment_fingerprint",
        "provisioning_action_ref", "provisioning_action_fingerprint", "provisioning_basis_ref",
        "provisioning_basis_fingerprint",
    )
    for field in equality_fields:
        require(trust[field] == extension[field], f"Host trust/F2 extension mismatch: {field}")
    require(trust["host_id"] == extension["host_actor_id"], "Host id must equal F2 Host Actor id")
    require(trust["lifecycle_state"] == "ACTIVE", "constructive Host trust is not ACTIVE")
    require(eligible["host_actor_identity_ref"] == extension["host_actor_identity_ref"], "eligibility Host Actor ref mismatch")
    require(eligible["host_actor_identity_fingerprint"] == extension["host_actor_identity_fingerprint"], "eligibility Host Actor fingerprint mismatch")
    auth_extension_fields = (
        "host_actor_identity_ref", "host_actor_identity_fingerprint",
        "host_actor_identity_assessment_ref", "host_actor_identity_assessment_fingerprint",
        "host_process_principal_ref", "host_process_principal_fingerprint",
        "host_process_principal_assessment_ref", "host_process_principal_assessment_fingerprint",
        "host_process_binding_ref", "host_process_binding_fingerprint",
        "host_process_binding_assessment_ref", "host_process_binding_assessment_fingerprint",
    )
    for field in auth_extension_fields:
        require(authentication[field] == extension[field], f"Host authentication/F2 extension mismatch: {field}")
    require(authentication["host_trust_fingerprint"] == trust["canonical_fingerprint"], "authentication Host-trust fingerprint mismatch")
    require(authentication["authenticator_profile_ref"] == trust["authenticator_profile_ref"], "authentication profile ref mismatch")
    require(authentication["authenticator_profile_fingerprint"] == trust["authenticator_profile_fingerprint"], "authentication profile fingerprint mismatch")
    require(authentication["effect_trust_eligibility_assessment_fingerprint"] == eligible["assessment_fingerprint"], "authentication eligibility binding mismatch")
    require(authentication["result"] == "AUTHENTICATED" and authentication["reason"] == "MATCH", "constructive Host is not AUTHENTICATED/MATCH")
    require(trust["validity_start_utc_ms"] <= authentication["trusted_time_utc_ms"] < authentication["valid_until_utc_ms"], "Host authentication time window invalid")
    require(authentication["host_revocation_event_sequence"] >= trust["issued_event_sequence"], "Host authentication uses stale revocation head")
    require(permit["host_trust_fingerprint"] == trust["canonical_fingerprint"], "permit Host-trust fingerprint mismatch")
    require(permit["host_authenticator_profile_ref"] == trust["authenticator_profile_ref"], "permit profile ref mismatch")
    require(permit["host_authenticator_profile_fingerprint"] == trust["authenticator_profile_fingerprint"], "permit profile fingerprint mismatch")
    require(permit["host_authentication_assessment_fingerprint"] == authentication["assessment_fingerprint"], "permit Host-authentication binding mismatch")
    require(permit["host_authentication_epoch"] == authentication["host_authentication_epoch"], "permit authentication epoch mismatch")
    return extension, trust, authentication, permit


SOURCE_ROLES_WITHOUT_DELEGATION = (
    "F1_TASK", "F2_RESPONSIBILITY", "F3_COMMAND", "POLICY", "PROHIBITED_BEHAVIOR_LIST"
)


def _validate_sources(
    bindings: list[dict[str, Any]], set_domain: str, expected_fingerprints: dict[str, str], where: str
) -> str:
    require(isinstance(bindings, list), f"{where} source bindings not a list")
    require(tuple(item["role"] for item in bindings) == SOURCE_ROLES_WITHOUT_DELEGATION, f"{where} role matrix/order mismatch")
    sort_key = lambda item: (item["role"].encode(), item["source_ref"].encode(), item["canonical_fingerprint"].encode())
    require(bindings == sorted(bindings, key=sort_key), f"{where} source bindings not canonical sorted")
    require(len({(item["role"], item["source_ref"]) for item in bindings}) == len(bindings), f"{where} duplicate role/ref")
    require(len({item["canonical_fingerprint"] for item in bindings}) == len(bindings), f"{where} duplicate source fingerprint")
    for index, item in enumerate(bindings):
        validate_schema_object(item, "AuthoritySourceBindingV0_1R8", f"{where} source {index}")
        require(item["source_fingerprint"] == expected_fingerprints[item["role"]], f"{where} source does not resolve: {item['role']}")
    return identity_fp(set_domain, [item["canonical_fingerprint"] for item in bindings])


def validate_grants_and_scope(
    by_schema: dict[str, list[dict[str, Any]]], permit: dict[str, Any], main_authorization: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    task = one_unique(by_schema, "F4TaskAuthorityBindingV0_1")
    actor = one_unique(by_schema, "F4ActorAuthorityBindingV0_1")
    resident = one_unique(by_schema, "F4ResidentCommandBindingV0_1")
    extension = one_unique(by_schema, "F2ExecutionHostPrincipalBindingExtensionV0_1R8")
    require(actor["responsibility_source_kind"] != "DELEGATION", "M0 source matrix unexpectedly requires delegation")
    expected_sources = {
        "F1_TASK": task["canonical_fingerprint"],
        "F2_RESPONSIBILITY": actor["responsibility_source_fingerprint"],
        "F3_COMMAND": resident["canonical_fingerprint"],
        "POLICY": main_authorization["policy_bundle_fingerprint"],
        "PROHIBITED_BEHAVIOR_LIST": main_authorization["prohibited_behavior_list_fingerprint"],
    }
    expected_source_refs = {
        "F1_TASK": task["task_id"],
        "F2_RESPONSIBILITY": actor["responsibility_source_ref"],
        "F3_COMMAND": resident["command_envelope_ref"],
    }
    require(permit["policy_bundle_fingerprint"] == expected_sources["POLICY"], "permit/authorization policy snapshot mismatch")
    require(permit["prohibited_boundary_evidence_fingerprint"] == expected_sources["PROHIBITED_BEHAVIOR_LIST"], "permit/authorization PBL snapshot mismatch")
    require(permit["policy_bundle_revision"] == main_authorization["policy_bundle_revision"], "policy revision mismatch")
    require(permit["prohibited_behavior_list_revision"] == main_authorization["prohibited_behavior_list_revision"], "PBL revision mismatch")
    require(actor["prohibited_behavior_list_revision"] == main_authorization["prohibited_behavior_list_revision"], "F2/PBL revision mismatch")
    capability = one_unique(by_schema, "CapabilityGrantV0_1R8")
    resource = one_unique(by_schema, "ResourceGrantV0_1R8")
    cap_proof = one_unique(by_schema, "CapabilitySubsetProofV0_1R8")
    res_proof = one_unique(by_schema, "ResourceContainmentAssessmentV0_1R8")
    cap_set = _validate_sources(
        capability["source_authority_bindings"],
        "agents-os.f4-capability-source-authority-set.v0.1-r6",
        expected_sources,
        "capability",
    )
    res_set = _validate_sources(
        resource["source_scope_bindings"],
        "agents-os.f4-resource-source-scope-set.v0.1-r6",
        expected_sources,
        "resource",
    )
    require(capability["source_authority_set_fingerprint"] == cap_set, "capability source-set fingerprint mismatch")
    require(resource["source_scope_set_fingerprint"] == res_set, "resource source-set fingerprint mismatch")
    require(capability["operation_set"] == ["SYNTHETIC_NOOP"], "capability operation is not the exact synthetic operation")
    require(resource["operation_set"] == ["SYNTHETIC_NOOP"], "resource operation is not the exact synthetic operation")
    require(resource["resource_kind"] == "SYNTHETIC_M0_RESOURCE", "resource kind is not synthetic M0")
    require(cap_proof["source_authority_set_fingerprint"] == cap_set, "capability proof source set mismatch")
    require(cap_proof["capability_definition_fingerprint"] == capability["capability_definition_fingerprint"], "capability proof definition mismatch")
    require(cap_proof["operation_registry_fingerprint"] == capability["operation_registry_fingerprint"], "capability proof registry mismatch")
    require(cap_proof["requested_operation_set"] == capability["operation_set"], "capability proof requested operations mismatch")
    require(cap_proof["exact_intersection_operation_set"] == capability["operation_set"], "capability exact intersection mismatch")
    require(cap_proof["constraint_fingerprint"] == capability["constraint_fingerprint"], "capability proof constraint mismatch")
    for bindings in (capability["source_authority_bindings"], resource["source_scope_bindings"]):
        by_role = {item["role"]: item for item in bindings}
        for role, expected_ref in expected_source_refs.items():
            require(by_role[role]["source_ref"] == expected_ref, f"source ref does not resolve exact bound authority: {role}")
    expected_projections = [expected_sources[role] for role in SOURCE_ROLES_WITHOUT_DELEGATION]
    require(cap_proof["source_projection_fingerprints"] == expected_projections, "capability source projections mismatch")
    require(cap_proof["result"] == "PASS", "capability subset proof is not PASS")
    require(capability["derived_subset_proof_fingerprint"] == cap_proof["canonical_fingerprint"], "capability grant proof fingerprint does not resolve")
    require(res_proof["source_scope_set_fingerprint"] == res_set, "resource proof source set mismatch")
    require(res_proof["resource_definition_fingerprint"] == resource["resource_definition_fingerprint"], "resource proof definition mismatch")
    require(res_proof["resource_kind"] == resource["resource_kind"] and res_proof["resource_ref"] == resource["resource_ref"], "resource proof target mismatch")
    require(res_proof["requested_operation_set"] == resource["operation_set"], "resource proof operations mismatch")
    require(res_proof["selector_constraint_fingerprint"] == resource["selector_constraint_fingerprint"], "resource selector mismatch")
    require(res_proof["source_projection_fingerprints"] == expected_projections, "resource source projections mismatch")
    require(res_proof["result"] == "PASS", "resource containment assessment is not PASS")
    require(resource["containment_assessment_fingerprint"] == res_proof["assessment_fingerprint"], "resource grant containment fingerprint does not resolve")
    require(cap_proof["watermark_event_sequence"] == main_authorization["evaluation_watermark_event_sequence"], "capability proof/auth watermark mismatch")
    require(res_proof["watermark_event_sequence"] == main_authorization["evaluation_watermark_event_sequence"], "resource proof/auth watermark mismatch")
    require(actor["prohibited_boundary_evidence_fingerprint"] == main_authorization["prohibited_behavior_list_fingerprint"], "F2 actor/PBL snapshot mismatch")
    require(permit["capability_grants"] == [capability], "permit capability grant mismatch")
    require(permit["resource_grants"] == [resource], "permit resource grant mismatch")
    return capability, resource, cap_proof, res_proof


def _find_wrapper(fixture: dict[str, Any], kind_fragment: str) -> dict[str, Any]:
    matches = [node["object"] for node in fixture["nodes"] if kind_fragment in node["kind"]]
    require(len(matches) == 1 and isinstance(matches[0], dict), f"expected one node wrapper containing {kind_fragment!r}")
    return matches[0]


def validate_identity_and_reference_chain(
    fixture: dict[str, Any],
    by_schema: dict[str, list[dict[str, Any]]],
    trust: dict[str, Any],
    authentication: dict[str, Any],
    permit: dict[str, Any],
    main_authorization: dict[str, Any],
    final_current: dict[str, Any],
    capability: dict[str, Any],
    resource: dict[str, Any],
) -> dict[str, Any]:
    task = one_unique(by_schema, "F4TaskAuthorityBindingV0_1")
    actor = one_unique(by_schema, "F4ActorAuthorityBindingV0_1")
    resident = one_unique(by_schema, "F4ResidentCommandBindingV0_1")
    extension = one_unique(by_schema, "F2ExecutionHostPrincipalBindingExtensionV0_1R8")
    human = one_unique(by_schema, "HumanPresenceBindingV0_1")
    effect = one_unique(by_schema, "EffectIntentBindingV0_1R8")
    currentness = one_unique(by_schema, "TaskPermitCurrentnessAssessmentV0_1R8")
    invocation = one_unique(by_schema, "PermitInvocationIdentityV0_1")
    issuance = one_unique(by_schema, "TaskPermitIssuanceFactV0_1")
    request = one_unique(by_schema, "HostLocalAdmissionRequestV0_1R8")
    decision = one_unique(by_schema, "HostLocalAdmissionDecisionV0_1R8")
    acceptance = one_unique(by_schema, "HostWorkAcceptanceFactV0_1R8")
    transition = one_unique(by_schema, "TaskPermitTransitionFactV0_1")
    disposition = one_unique(by_schema, "HostWorkStartDispositionFactV0_1R8")
    handoff = one_unique(by_schema, "F4AcceptedEffectHandoffV0_1R8")
    cap_proof = one_unique(by_schema, "CapabilitySubsetProofV0_1R8")
    res_proof = one_unique(by_schema, "ResourceContainmentAssessmentV0_1R8")

    authorization_wrapper = _find_wrapper(fixture, "EffectAuthorizationRequirementV0_1R8")
    eligibility_wrapper = _find_wrapper(fixture, "F4HostEffectTrustEligibilityAssessmentV0_1R8")
    trust_wrapper = _find_wrapper(fixture, "F4HostTrustRevisionV0_1R8")
    authentication_wrapper = _find_wrapper(fixture, "HostAuthenticationAssessmentV0_1R8")
    cap_proof_wrapper = _find_wrapper(fixture, "CapabilitySubsetProofV0_1R8")
    res_proof_wrapper = _find_wrapper(fixture, "ResourceContainmentAssessmentV0_1R8")
    currentness_wrapper = _find_wrapper(fixture, "TaskPermitCurrentnessAssessmentV0_1R8")
    admission_wrapper = _find_wrapper(fixture, "HostLocalAdmissionV0_1R8")
    final_wrapper = _find_wrapper(fixture, "FinalHandoffAuthorityAssessmentV0_1R8")
    acceptance_wrapper = _find_wrapper(fixture, "HostWorkAcceptanceFactV0_1R8")
    disposition_wrapper = _find_wrapper(fixture, "HostWorkStartDispositionFactV0_1R8")
    handoff_wrapper = _find_wrapper(fixture, "F4AcceptedEffectHandoffV0_1R8")
    require(authorization_wrapper["requirement"] == main_authorization, "authorization wrapper requirement mismatch")
    require(authorization_wrapper["resolution"]["requirement_fingerprint"] == main_authorization["canonical_fingerprint"], "authorization resolution fingerprint mismatch")
    require(eligibility_wrapper["assessment"]["assessment_fingerprint"] == authentication["effect_trust_eligibility_assessment_fingerprint"], "eligibility wrapper object mismatch")
    require(eligibility_wrapper["assessment_ref"] == authentication["effect_trust_eligibility_assessment_ref"], "eligibility wrapper ref mismatch")
    require(trust_wrapper["host_trust"] == trust, "Host-trust wrapper mismatch")
    require(authentication_wrapper["assessment"] == authentication, "Host-authentication wrapper mismatch")
    require(cap_proof_wrapper["proof"] == cap_proof and cap_proof_wrapper["proof_ref"] == capability["derived_subset_proof_ref"], "capability proof ref/object mismatch")
    require(res_proof_wrapper["assessment"] == res_proof and res_proof_wrapper["assessment_ref"] == resource["containment_assessment_ref"], "resource assessment ref/object mismatch")
    require(currentness_wrapper["assessment"] == currentness, "currentness wrapper mismatch")
    require(admission_wrapper["invocation_identity"] == invocation and admission_wrapper["request"] == request and admission_wrapper["decision"] == decision, "admission wrapper mismatch")
    require(final_wrapper["assessment"] == final_current, "final-authority wrapper mismatch")
    require(acceptance_wrapper["acceptance"] == acceptance and acceptance_wrapper["activation_transition"] == transition, "acceptance wrapper mismatch")
    require(disposition_wrapper["disposition"] == disposition, "disposition wrapper mismatch")
    require(handoff_wrapper["handoff"] == handoff, "handoff wrapper mismatch")

    cap_set_fp = identity_fp("agents-os.f4-capability-set.v0.1", [capability["canonical_fingerprint"]])
    res_set_fp = identity_fp("agents-os.f4-resource-set.v0.1", [resource["canonical_fingerprint"]])
    secret_fps = [item["canonical_fingerprint"] for item in permit["secret_handle_bindings"]]
    require(secret_fps == sorted(secret_fps), "secret handles not sorted")
    secret_set_fp = identity_fp("agents-os.f4-secret-handle-set.v0.1", secret_fps)
    require(effect["capability_set_fingerprint"] == cap_set_fp, "effect capability set mismatch")
    require(effect["resource_set_fingerprint"] == res_set_fp, "effect resource set mismatch")
    require(effect["operation_kind"] == "SYNTHETIC_NOOP", "effect operation is not SYNTHETIC_NOOP")
    require(effect["target_resource_refs"] == [resource["resource_ref"]], "effect resource target mismatch")
    require(effect["external_effect_requested"] is True and effect["raw_payload_present"] is False, "effect intent flags invalid")
    require(permit["effect_intent_binding"] == effect, "permit effect intent is not exact")
    require(permit["effect_authorization_requirement"] == main_authorization, "permit authorization requirement mismatch")
    require(permit["human_presence_binding"] == human, "permit human-presence binding mismatch")
    require(permit["F4_contract_version"] == CONTRACT, "permit contract literal mismatch")
    require(permit["max_invocations"] == 1, "R8 permit must have max_invocations=1")
    require(permit["idempotency_key"] == effect["idempotency_key"], "permit/effect idempotency mismatch")
    require(main_authorization["evaluated_at_trusted_time_utc_ms"] <= permit["issued_at_utc_ms"], "permit embeds a future authorization evaluation")
    require(main_authorization["evaluation_watermark_event_sequence"] <= permit["issuance_event_sequence"], "permit embeds a future authorization watermark")
    expected_permit_id = identity_fp(
        "agents-os.task-permit-id.v0.1",
        task["task_id"],
        task["task_lifecycle_generation"],
        permit["execution_epoch"],
        resident["command_id"],
        permit["host_trust_ref"],
        effect["idempotency_key"],
        permit["issuance_event_sequence"],
    )
    require(permit["permit_id"] == expected_permit_id, "permit_id derivation mismatch")
    permit_ref = "permit:" + expected_permit_id
    require(trust_wrapper["host_trust_ref"] == permit["host_trust_ref"], "Host-trust wrapper ref mismatch")
    require(authentication_wrapper["assessment_ref"] == permit["host_authentication_assessment_ref"], "Host-authentication wrapper ref mismatch")
    require(permit["execution_epoch"] == task["previous_execution_epoch"] + 1, "execution epoch derivation mismatch")
    require(permit["not_before_utc_ms"] <= permit["issued_at_utc_ms"] < permit["expires_at_utc_ms"], "permit validity window invalid")
    require(permit["issued_at_utc_ms"] <= permit["start_authority_commit_before_utc_ms"] <= permit["expires_at_utc_ms"], "start-authority deadline invalid")

    require(invocation["permit_id"] == expected_permit_id, "invocation permit_id mismatch")
    require(invocation["permit_fingerprint"] == permit["canonical_fingerprint"], "invocation permit fingerprint mismatch")
    require(invocation["invocation_ordinal"] == 1, "R8 invocation ordinal must be 1")
    require(invocation["idempotency_key"] == effect["idempotency_key"], "invocation idempotency mismatch")
    require(invocation["execution_epoch"] == permit["execution_epoch"], "invocation execution epoch mismatch")
    require(invocation["host_id"] == trust["host_id"], "invocation Host id mismatch")
    require(invocation["effect_intent_fingerprint"] == effect["canonical_fingerprint"], "invocation effect fingerprint mismatch")

    require(issuance["permit_ref"] == permit_ref and issuance["permit_fingerprint"] == permit["canonical_fingerprint"], "issuance permit binding mismatch")
    require(issuance["issuance_command_envelope_ref"] == resident["command_envelope_ref"], "issuance command ref mismatch")
    require(issuance["issuance_command_envelope_fingerprint"] == resident["command_envelope_fingerprint"], "issuance command fingerprint mismatch")
    require(issuance["issuance_event_sequence"] == permit["issuance_event_sequence"], "issuance sequence mismatch")
    require(currentness["permit_ref"] == permit_ref and currentness["permit_fingerprint"] == permit["canonical_fingerprint"], "currentness permit binding mismatch")
    require(currentness["result"] == "VALID" and currentness["reason"] == "ALL_CURRENT", "permit currentness not VALID/ALL_CURRENT")
    require(currentness_wrapper["assessment_ref"] == decision["permit_currentness_assessment_ref"], "currentness wrapper ref mismatch")

    require(request["invocation_identity"] == invocation, "request invocation bytes differ")
    require(request["task_permit_ref"] == permit_ref and request["task_permit_fingerprint"] == permit["canonical_fingerprint"], "request permit binding mismatch")
    require(request["effect_intent_fingerprint"] == effect["canonical_fingerprint"], "request effect fingerprint mismatch")
    require(request["resident_command_envelope_ref"] == resident["command_envelope_ref"], "request command ref mismatch")
    require(request["resident_command_envelope_fingerprint"] == resident["command_envelope_fingerprint"], "request command fingerprint mismatch")
    require(request["target_host_id"] == trust["host_id"], "request Host id mismatch")
    require(request["target_host_trust_revision"] == 7, "request Host-trust revision mismatch")
    require(decision["invocation_identity_fingerprint"] == invocation["canonical_fingerprint"], "decision invocation fingerprint mismatch")
    require(decision["request_fingerprint"] == request["canonical_fingerprint"], "decision request fingerprint mismatch")
    require(decision["permit_currentness_assessment_fingerprint"] == currentness["assessment_fingerprint"], "decision currentness fingerprint mismatch")
    require(decision["host_authentication_assessment_fingerprint"] == authentication["assessment_fingerprint"], "decision authentication fingerprint mismatch")
    require(decision["decision"] == "ADMITTED" and decision["reason"] == "ALL_CHECKS_PASS", "constructive admission did not ADMIT")
    require(admission_wrapper["request_ref"] == decision["request_ref"] == acceptance["admission_request_ref"], "admission request ref does not resolve")
    require(admission_wrapper["decision_ref"] == acceptance["admission_decision_ref"], "admission decision ref does not resolve")

    acceptance_id = identity_fp("agents-os.host-work-acceptance-id.v0.1", invocation["canonical_fingerprint"])
    acceptance_ref = "acceptance:" + acceptance_id
    require(acceptance["acceptance_id"] == acceptance_id, "acceptance_id derivation mismatch")
    require(acceptance_wrapper["acceptance_ref"] == acceptance_ref, "acceptance wrapper ref mismatch")
    require(acceptance["invocation_identity"] == invocation, "acceptance invocation bytes differ")
    require(acceptance["admission_request_ref"] == decision["request_ref"], "acceptance/request ref chain mismatch")
    require(acceptance["admission_request_fingerprint"] == request["canonical_fingerprint"], "acceptance request fingerprint mismatch")
    require(acceptance["admission_decision_fingerprint"] == decision["decision_fingerprint"], "acceptance decision fingerprint mismatch")
    require(acceptance["permit_currentness_assessment_ref"] == decision["permit_currentness_assessment_ref"], "acceptance currentness ref mismatch")
    require(acceptance["permit_currentness_assessment_fingerprint"] == currentness["assessment_fingerprint"], "acceptance currentness fingerprint mismatch")
    require(acceptance["host_authentication_assessment_ref"] == decision["host_authentication_assessment_ref"], "acceptance authentication ref mismatch")
    require(acceptance["host_authentication_assessment_fingerprint"] == authentication["assessment_fingerprint"], "acceptance authentication fingerprint mismatch")
    require(acceptance["accepted_host_id"] == trust["host_id"], "acceptance Host id mismatch")
    require(acceptance["accepted_host_trust_revision"] == 7, "acceptance Host-trust revision mismatch")
    require(acceptance["accepted_host_authentication_epoch"] == authentication["host_authentication_epoch"], "acceptance auth epoch mismatch")
    require(transition["permit_ref"] == permit_ref and transition["permit_fingerprint"] == permit["canonical_fingerprint"], "activation transition permit binding mismatch")
    require(transition["transition_kind"] == "ACTIVATE" and transition["reason"] == "HOST_ACCEPTANCE", "invalid activation transition")
    require(transition["transition_action_ref"] == acceptance_ref, "activation transition acceptance ref mismatch")
    require(transition["transition_action_fingerprint"] == acceptance["fact_fingerprint"], "activation transition acceptance fingerprint mismatch")

    observation_id = identity_fp(
        "agents-os.host-work-start-observation-id.v0.1",
        acceptance["fact_fingerprint"],
        disposition["observation_attempt"],
    )
    observation_ref = "observation:" + observation_id
    require(disposition["observation_id"] == observation_id, "observation_id derivation mismatch")
    require(disposition_wrapper["start_disposition_ref"] == observation_ref, "disposition wrapper ref mismatch")
    require(disposition["acceptance_ref"] == acceptance_ref, "disposition acceptance ref mismatch")
    require(disposition["acceptance_fingerprint"] == acceptance["fact_fingerprint"], "disposition acceptance fingerprint mismatch")
    require(disposition["invocation_identity_fingerprint"] == invocation["canonical_fingerprint"], "disposition invocation fingerprint mismatch")
    require(disposition["observed_host_id"] == trust["host_id"], "disposition Host id mismatch")
    require(disposition["observed_host_trust_revision"] == 7, "disposition Host-trust revision mismatch")
    require(disposition["observed_host_authentication_epoch"] == authentication["host_authentication_epoch"], "disposition auth epoch mismatch")
    require(disposition["final_handoff_authority_assessment_fingerprint"] == final_current["assessment_fingerprint"], "disposition final-authority fingerprint mismatch")
    require(disposition["final_handoff_authority_assessment_ref"] == final_wrapper["assessment_ref"], "final-authority assessment ref does not resolve")
    require(disposition["disposition"] == "START_AUTHORITY_CURRENT" and disposition["reason"] == "ALL_RECHECKS_PASS", "start disposition is not current")

    handoff_id = identity_fp("agents-os.f4-accepted-effect-handoff-id.v0.1", invocation["canonical_fingerprint"])
    handoff_ref = "handoff:" + handoff_id
    require(handoff["handoff_id"] == handoff_id, "handoff_id derivation mismatch")
    require(handoff_wrapper["handoff_ref"] == handoff_ref, "handoff wrapper ref mismatch")
    require(handoff["acceptance_ref"] == acceptance_ref and handoff["acceptance_fingerprint"] == acceptance["fact_fingerprint"], "handoff acceptance chain mismatch")
    require(handoff["start_disposition_ref"] == observation_ref and handoff["start_disposition_fingerprint"] == disposition["fact_fingerprint"], "handoff disposition chain mismatch")
    require(handoff["invocation_identity"] == invocation, "handoff invocation bytes differ")
    require(handoff["task_permit_ref"] == permit_ref and handoff["task_permit_fingerprint"] == permit["canonical_fingerprint"], "handoff permit chain mismatch")
    require(handoff["effect_intent_fingerprint"] == effect["canonical_fingerprint"], "handoff effect fingerprint mismatch")
    require(handoff["owner_host_id"] == trust["host_id"] and handoff["owner_host_trust_revision"] == 7, "handoff Host trust mismatch")
    require(handoff["owner_host_authentication_epoch"] == authentication["host_authentication_epoch"], "handoff auth epoch mismatch")
    require(handoff["capability_set_fingerprint"] == cap_set_fp and handoff["resource_set_fingerprint"] == res_set_fp, "handoff grant-set mismatch")
    require(handoff["secret_handle_set_fingerprint"] == secret_set_fp, "handoff secret-handle set mismatch")
    require(handoff["permit_attestation_evidence_fingerprint"] == permit["permit_attestation_evidence_fingerprint"], "handoff attestation mismatch")
    require(handoff["human_presence_binding_fingerprint"] == human["canonical_fingerprint"], "handoff human-presence mismatch")
    require(handoff["effect_authorization_requirement_fingerprint"] == main_authorization["canonical_fingerprint"], "handoff authorization mismatch")
    require(handoff["final_handoff_authority_assessment_fingerprint"] == final_current["assessment_fingerprint"], "handoff final-authority mismatch")
    require(handoff["expected_result_contract_ref"] == effect["expected_result_contract_ref"], "handoff result-contract ref mismatch")
    require(handoff["expected_result_contract_fingerprint"] == effect["expected_result_contract_fingerprint"], "handoff result-contract fingerprint mismatch")

    stub = _find_wrapper(fixture, "ZeroEffect")
    require(stub.get("handoff_ref") == handoff_ref, "zero-effect stub handoff_ref mismatch")
    require(stub.get("handoff_fingerprint") == handoff["canonical_fingerprint"], "zero-effect stub handoff fingerprint mismatch")
    require(stub.get("claim_state") == "NOT_CLAIMED", "zero-effect stub unexpectedly claimed")
    require(stub.get("physical_effect_crossed") is False, "zero-effect stub crossed physical boundary")
    require(stub.get("terminal_outcome") == "NOT_EXECUTED", "zero-effect terminal outcome mismatch")
    for field in ("external_effect_count", "provider_call_count", "raw_secret_count"):
        require(stub.get(field) == 0, f"nonzero zero-effect counter: {field}")

    # Current final-authority evidence must resolve to the exact constructive
    # snapshots rather than opaque authority labels.
    evidence = {row["code"]: row for row in final_current["authority_observations"]}
    expected_evidence = {
        "F1_TASK": task["canonical_fingerprint"],
        "F2_ACTOR_PRINCIPAL_BINDING": extension["canonical_fingerprint"],
        "F2_RESPONSIBILITY_DELEGATION": actor["canonical_fingerprint"],
        "F3_RESIDENT_COMMAND": resident["canonical_fingerprint"],
        "F4_HOST_EFFECT_TRUST": trust["canonical_fingerprint"],
        "POLICY": main_authorization["policy_bundle_fingerprint"],
        "PROHIBITED_BEHAVIOR_LIST": main_authorization["prohibited_behavior_list_fingerprint"],
        "EFFECT_AUTHORIZATION_REQUIREMENT": main_authorization["canonical_fingerprint"],
    }
    for code, fingerprint in expected_evidence.items():
        require(evidence[code]["evidence_fingerprint"] == fingerprint, f"final authority evidence does not resolve: {code}")
    require(evidence["EFFECT_AUTHORIZATION_REQUIREMENT"]["evidence_ref"] == authorization_wrapper["requirement_ref"], "final authorization ref does not resolve")
    require(final_current["watermark_event_sequence"] >= permit["issuance_event_sequence"], "final authority watermark predates permit issuance")
    require(final_current["trusted_time_utc_ms"] == disposition["observed_at_utc_ms"], "final authority/disposition trusted-time mismatch")

    return {
        "permit_id_verified": expected_permit_id,
        "invocation_fingerprint_verified": invocation["canonical_fingerprint"],
        "acceptance_id_verified": acceptance_id,
        "observation_id_verified": observation_id,
        "handoff_id_verified": handoff_id,
        "acceptance_count": 1,
        "accepted_handoff_count": 1,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }


def validate_schema_object(obj: dict[str, Any], schema_name: str, where: str) -> None:
    require(schema_name in SCHEMAS, f"unknown R8 schema name at {where}: {schema_name}")
    interface_version, fingerprint_field, fields = SCHEMAS[schema_name]
    fingerprint_object(obj, schema_name, fields, fingerprint_field, where)
    if interface_version is not None:
        require(obj["interface_version"] == interface_version, f"wrong interface version at {where}")


def validate_canonical_profile(fixture: dict[str, Any]) -> dict[str, Any]:
    profile = fixture["canonical_profile"]
    ordered_keys(profile, ("fingerprint_prefix", "schema_name_by_kind", "schemas"), "canonical_profile")
    require(profile["fingerprint_prefix"] == FP_PREFIX, "canonical fingerprint prefix mismatch")
    emitted = {entry["exact_schema_name"] for entry in fixture["effective_schema_inventory"]}
    require(set(profile["schema_name_by_kind"]) == emitted, "canonical schema-name map is not exact emitted inventory")
    require(all(key == value for key, value in profile["schema_name_by_kind"].items()), "schema-name map substitutes a label")
    require(set(profile["schemas"]) == emitted, "canonical profile schemas are not exact emitted inventory")
    for schema_name, declaration in profile["schemas"].items():
        ordered_keys(declaration, ("interface_version", "fingerprint_field", "ordered_field_names"), f"profile schema {schema_name}")
        interface_version, fingerprint_field, fields = SCHEMAS[schema_name]
        require(declaration["interface_version"] == interface_version, f"profile interface mismatch: {schema_name}")
        require(declaration["fingerprint_field"] == fingerprint_field, f"profile fingerprint field mismatch: {schema_name}")
        require(declaration["ordered_field_names"] == [*fields, fingerprint_field], f"profile field order mismatch: {schema_name}")
    return {"effective_schema_count": len(emitted)}


def validate_fixture(fixture: dict[str, Any], *, fixture_bytes: bytes | None = None) -> dict[str, Any]:
    ordered_keys(
        fixture,
        (
            "schema_version", "contract_version", "canonical_profile",
            "authorization_totality_vectors", "authorization_invalid_input_summary",
            "eligibility_totality_vectors", "final_authority_code_order",
            "final_authority_totality_vectors", "nodes", "assertions",
            "effective_schema_inventory",
        ),
        "fixture root",
    )
    require(fixture["schema_version"] == "agents-os.f4-r8-complete-effective-m0a-witness.v0.1", "wrong fixture schema version")
    require(fixture["contract_version"] == CONTRACT, "wrong fixture contract version")
    require(fixture["final_authority_code_order"] == list(FINAL_OBSERVATION_CODES), "top-level final-authority code order mismatch")
    reject_removed_surface(fixture)
    summary: dict[str, Any] = {"result": "PASS", "contract_version": CONTRACT}
    summary.update(validate_dag(fixture))
    by_schema = validate_inventory(fixture)
    summary.update(validate_canonical_profile(fixture))
    summary.update(validate_authorization(by_schema, fixture))
    eligible, eligibility_summary = validate_eligibility(by_schema)
    summary.update(eligibility_summary)
    extension, trust, authentication, permit = validate_host_chain(by_schema, eligible)
    main_authorizations = [
        row for row in unique_objects(by_schema, "EffectAuthorizationRequirementV0_1R8")
        if row["mode"] == "NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED"
    ]
    require(len(main_authorizations) == 1, "expected one no-separate constructive requirement")
    main_authorization = main_authorizations[0]
    capability, resource, _, _ = validate_grants_and_scope(by_schema, permit, main_authorization)
    permit_ref = "permit:" + permit["permit_id"]
    final_current, final_summary = validate_final_authority(
        fixture, by_schema, permit_ref, permit["canonical_fingerprint"]
    )
    summary.update(final_summary)
    summary.update(
        validate_identity_and_reference_chain(
            fixture, by_schema, trust, authentication, permit, main_authorization,
            final_current, capability, resource,
        )
    )
    assertions = fixture["assertions"]
    expected_assertions = {
        "host_actor_identity_revision": extension["host_actor_identity_revision"],
        "host_trust_revision": trust["host_trust_revision"],
        "max_invocations": permit["max_invocations"],
        "authorization_valid_requirement_count": 7,
        "authorization_resolution_count": len(fixture["authorization_totality_vectors"]),
        "eligibility_materialized_row_count": len(fixture["eligibility_totality_vectors"]),
        "final_authority_code_count": len(FINAL_OBSERVATION_CODES),
        "final_authority_vector_count": len(fixture["final_authority_totality_vectors"]),
        "acceptance_count": 1,
        "accepted_handoff_count": 1,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
        "effective_schema_inventory_count": len(fixture["effective_schema_inventory"]),
        "node_count": len(fixture["nodes"]),
    }
    require(assertions == expected_assertions, "fixture assertions do not equal dynamically verified counts")
    summary["effective_schema_object_count"] = len(fixture["effective_schema_inventory"])
    summary["fixture_canonical_sha256"] = sha256(fixture)
    if fixture_bytes is not None:
        summary["fixture_file_sha256"] = hashlib.sha256(fixture_bytes).hexdigest()
    return summary


def run_mutations(fixture: dict[str, Any]) -> int:
    def schema_objects(value: dict[str, Any], schema_name: str) -> list[dict[str, Any]]:
        return [
            json_pointer(value, entry["json_pointer"])
            for entry in value["effective_schema_inventory"]
            if entry["exact_schema_name"] == schema_name
        ]

    def resign_effective(value: dict[str, Any], skip_schemas: set[str] | None = None) -> None:
        skipped = skip_schemas or set()
        entries = sorted(
            value["effective_schema_inventory"],
            key=lambda entry: entry["json_pointer"].count("/"),
            reverse=True,
        )
        for entry in entries:
            schema_name = entry["exact_schema_name"]
            if schema_name in skipped:
                continue
            obj = json_pointer(value, entry["json_pointer"])
            _, fingerprint_field, fields = SCHEMAS[schema_name]
            obj[fingerprint_field] = f4_fp(schema_name, [obj[field] for field in fields])
        resign_nodes(value)

    def mutate_wrong_domain(value: dict[str, Any]) -> None:
        for invocation in schema_objects(value, "PermitInvocationIdentityV0_1"):
            fields = SCHEMAS["PermitInvocationIdentityV0_1"][2]
            invocation["canonical_fingerprint"] = identity_fp(
                "agents-os.permit-invocation-identity.v0.1-r8-wrong-domain",
                *[invocation[field] for field in fields],
            )
        resign_effective(value, {"PermitInvocationIdentityV0_1"})

    def mutate_field_order(value: dict[str, Any]) -> None:
        obj = schema_objects(value, "HostAuthenticationAssessmentV0_1R8")[0]
        moved = obj.pop("authenticator_profile_ref")
        obj["authenticator_profile_ref"] = moved
        resign_effective(value)

    def mutate_permit_id(value: dict[str, Any]) -> None:
        schema_objects(value, "TaskPermitV0_1R8")[0]["permit_id"] = "0" * 64
        resign_effective(value)

    def mutate_acceptance_ref(value: dict[str, Any]) -> None:
        wrapper = next(node["object"] for node in value["nodes"] if node["kind"] == "HostWorkAcceptanceFactV0_1R8")
        wrapper["acceptance_ref"] = "acceptance:" + "1" * 64
        resign_effective(value)

    def mutate_profile_ref(value: dict[str, Any]) -> None:
        schema_objects(value, "HostAuthenticationAssessmentV0_1R8")[0]["authenticator_profile_ref"] += ":mismatch"
        resign_effective(value)

    def mutate_auth_mixed_presence(value: dict[str, Any]) -> None:
        rows = schema_objects(value, "EffectAuthorizationRequirementV0_1R8")
        row = next(item for item in rows if item["currentness_reason"] == "JENN_DECISION_CURRENT")
        row["Jenn_actor_identity_ref"] = None
        resign_effective(value)

    def mutate_auth_unknown_mode(value: dict[str, Any]) -> None:
        rows = schema_objects(value, "EffectAuthorizationRequirementV0_1R8")
        row = next(item for item in rows if item["currentness_reason"] == "JENN_DECISION_MISSING")
        row["mode"] = "UNKNOWN_MODE"
        resign_effective(value)

    def mutate_final_precedence(value: dict[str, Any]) -> None:
        vector = next(item for item in value["final_authority_totality_vectors"] if item["id"] == "INTEGRITY_OVER_UNAVAILABLE")
        vector["expected"] = ["INDETERMINATE", "AUTHORITY_UNAVAILABLE"]
        resign_effective(value)

    def mutate_final_availability(value: dict[str, Any]) -> None:
        assessment = schema_objects(value, "FinalHandoffAuthorityAssessmentV0_1R8")[0]
        observation = assessment["authority_observations"][1]
        observation["evidence_availability"] = "UNAVAILABLE"
        resign_effective(value)

    def mutate_eligibility_presence(value: dict[str, Any]) -> None:
        rows = schema_objects(value, "F4HostEffectTrustEligibilityAssessmentV0_1R8")
        row = next(item for item in rows if item["current_F2_actor_observation"] == "UNAVAILABLE")
        row["current_F2_actor_assessment_ref"] = "forbidden:last-known-assessment"
        resign_effective(value)

    def mutate_source_role(value: dict[str, Any]) -> None:
        for grant in schema_objects(value, "CapabilityGrantV0_1R8"):
            grant["source_authority_bindings"][1]["role"] = "AMBIENT_AUTHORITY"
        resign_effective(value)

    def mutate_subset_proof(value: dict[str, Any]) -> None:
        schema_objects(value, "CapabilitySubsetProofV0_1R8")[0]["exact_intersection_operation_set"] = []
        resign_effective(value)

    def mutate_single_invocation(value: dict[str, Any]) -> None:
        schema_objects(value, "TaskPermitV0_1R8")[0]["max_invocations"] = 2
        resign_effective(value)

    def mutate_host_trust_revision(value: dict[str, Any]) -> None:
        schema_objects(value, "HostLocalAdmissionRequestV0_1R8")[0]["target_host_trust_revision"] = 8
        resign_effective(value)

    def mutate_observation_id(value: dict[str, Any]) -> None:
        schema_objects(value, "HostWorkStartDispositionFactV0_1R8")[0]["observation_id"] = "2" * 64
        resign_effective(value)

    def mutate_pbl_snapshot(value: dict[str, Any]) -> None:
        schema_objects(value, "TaskPermitV0_1R8")[0]["prohibited_boundary_evidence_fingerprint"] = "3" * 64
        resign_effective(value)

    def mutate_base_edge(value: dict[str, Any]) -> None:
        node = value["nodes"][-1]
        node["depends_on_ordinals"].remove(1)
        resign_nodes(value)

    def mutate_old_field(value: dict[str, Any]) -> None:
        schema_objects(value, "F4AcceptedEffectHandoffV0_1R8")[0]["owner_host_identity_revision"] = 3
        resign_effective(value)

    def mutate_effect_count(value: dict[str, Any]) -> None:
        _find_wrapper(value, "ZeroEffect")["external_effect_count"] = 1
        resign_nodes(value)

    cases: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("wrong_fingerprint_domain", mutate_wrong_domain),
        ("schema_field_order", mutate_field_order),
        ("permit_id_derivation", mutate_permit_id),
        ("acceptance_ref_chain", mutate_acceptance_ref),
        ("host_profile_ref", mutate_profile_ref),
        ("authorization_mixed_presence", mutate_auth_mixed_presence),
        ("authorization_unknown_mode", mutate_auth_unknown_mode),
        ("final_integrity_precedence", mutate_final_precedence),
        ("final_availability_nullability", mutate_final_availability),
        ("eligibility_presence", mutate_eligibility_presence),
        ("capability_source_role", mutate_source_role),
        ("capability_subset_proof", mutate_subset_proof),
        ("single_invocation", mutate_single_invocation),
        ("host_trust_revision", mutate_host_trust_revision),
        ("observation_id_derivation", mutate_observation_id),
        ("PBL_snapshot", mutate_pbl_snapshot),
        ("base_integrity_edge", mutate_base_edge),
        ("removed_host_identity_field", mutate_old_field),
        ("external_effect_count", mutate_effect_count),
    ]
    rejected = 0
    for name, mutation in cases:
        candidate = copy.deepcopy(fixture)
        mutation(candidate)
        try:
            validate_fixture(candidate)
        except ValidationError:
            rejected += 1
        else:
            raise ValidationError(f"semantic mutation was accepted: {name}")
    require(rejected == len(cases), "not every semantic mutation rejected")
    return rejected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT)
    parser.add_argument("--skip-mutations", action="store_true")
    args = parser.parse_args()
    try:
        fixture, raw = load_strict(args.fixture)
        summary = validate_fixture(fixture, fixture_bytes=raw)
        summary["negative_mutations_rejected"] = 0 if args.skip_mutations else run_mutations(fixture)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    except (OSError, ValidationError, KeyError, IndexError, TypeError) as exc:
        print(json.dumps({"result": "BLOCK", "reason": str(exc)}, sort_keys=True, separators=(",", ":")))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
