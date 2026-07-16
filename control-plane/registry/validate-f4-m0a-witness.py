#!/usr/bin/env python3
"""Validate the exact F4 R1 synthetic, zero-effect M0-A witness."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


CONTRACT = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R1_ATOMIC_BUNDLE"
INTERFACE = "agents-os.f4-m0a-witness.v0.1"
FINGERPRINT_DOMAIN = "agents-os.f4-fingerprint.v0.1:"
NODE_DOMAIN = "agents-os.f4-m0a-node.v0.1"
DEFAULT_FIXTURE = Path(__file__).with_name("examples") / (
    "2026-07-16-agents-os-f4-taskpermit-host-authentication-"
    "effect-admission-m0a-witness-v0.1.json"
)
MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _assert_scalar_profile(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < -MAX_SAFE_INTEGER or value > MAX_SAFE_INTEGER:
            raise ValueError(f"unsafe integer at {path}")
        return
    if isinstance(value, float):
        raise ValueError(f"floating-point value forbidden at {path}")
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise ValueError(f"non-NFC string at {path}")
        if "\x00" in value or value != value.strip():
            raise ValueError(f"invalid string boundary at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_scalar_profile(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"non-string key at {path}")
            _assert_scalar_profile(key, f"{path}.<key>")
            _assert_scalar_profile(item, f"{path}.{key}")
        return
    raise ValueError(f"unsupported value at {path}: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    """JCS-equivalent bytes for this fixture's restricted no-float profile."""
    _assert_scalar_profile(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def reject_duplicate_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def label_digest(label: str) -> str:
    return digest(["agents-os.f4-m0a-upstream-fixture.v0.1", label])


def set_digest(domain: str, fingerprints: list[str]) -> str:
    return digest([domain, sorted(fingerprints)])


def permit_id(
    task_id: str,
    task_generation: int,
    execution_epoch: int,
    command_id: str,
    host_id: str,
    idempotency_key: str,
    issuance_event_sequence: int,
) -> str:
    return digest(
        [
            "agents-os.task-permit-id.v0.1",
            task_id,
            task_generation,
            execution_epoch,
            command_id,
            host_id,
            idempotency_key,
            issuance_event_sequence,
        ]
    )


def build_expected_fixture() -> dict[str, Any]:
    fingerprinted_objects: list[tuple[str, str]] = []

    def stamped(
        schema_name: str,
        fields: dict[str, Any],
        fingerprint_field: str = "canonical_fingerprint",
    ) -> dict[str, Any]:
        value = dict(fields)
        value[fingerprint_field] = digest(
            [FINGERPRINT_DOMAIN + schema_name, *fields.values()]
        )
        fingerprinted_objects.append((schema_name, value[fingerprint_field]))
        return value

    task = stamped(
        "F4TaskAuthorityBindingV0_1",
        {
            "interface_version": "agents-os.f4-task-authority-binding.v0.1",
            "task_id": "task:m0-a:f4:001",
            "task_lifecycle_generation": 1,
            "task_completion_epoch": 0,
            "task_state_revision": 1,
            "task_state_fingerprint": label_digest("f1-task-state"),
            "goal_id": "goal:m0-a:f4:001",
            "goal_spec_revision": 1,
            "goal_spec_fingerprint": label_digest("f1-goal-spec"),
            "goal_plan_membership_revision": 1,
            "goal_plan_membership_fingerprint": label_digest("f1-membership"),
            "task_commitment_snapshot_id": "commitment:m0-a:f4:001",
            "task_commitment_snapshot_fingerprint": label_digest("f1-commitment"),
            "dependency_closure_snapshot_id": "dependencies:m0-a:f4:001",
            "dependency_closure_fingerprint": label_digest("f1-dependencies"),
            "task_completion_refs": [],
            "completion_assurance_versions": [],
            "previous_execution_epoch": 0,
            "execution_epoch_head_fingerprint": label_digest("f4-epoch-genesis"),
            "currentness_event_sequence": 10,
        },
    )
    actor = stamped(
        "F4ActorAuthorityBindingV0_1",
        {
            "interface_version": "agents-os.f4-actor-authority-binding.v0.1",
            "actor_id": "actor:m0-a:synthetic",
            "actor_identity_revision": 1,
            "actor_identity_assessment_ref": "fixture:f2-actor-assessment",
            "actor_identity_assessment_fingerprint": label_digest("f2-actor-assessment"),
            "principal_id": "principal:m0-a:synthetic",
            "principal_binding_revision": 1,
            "principal_binding_assessment_ref": "fixture:f2-principal-assessment",
            "principal_binding_assessment_fingerprint": label_digest("f2-principal-assessment"),
            "authentication_assessment_ref": "fixture:f2-authentication-assessment",
            "authentication_assessment_fingerprint": label_digest("f2-authentication-assessment"),
            "authentication_result": "AUTHENTICATED",
            "responsibility_source_kind": "ASSIGNMENT",
            "responsibility_source_ref": "assignment:m0-a:f4:001",
            "responsibility_source_fingerprint": label_digest("f2-assignment"),
            "delegation_chain_fingerprint": None,
            "bound_resource_ref": "resource:m0-a:synthetic:001",
            "action_ref": "action:m0-a:f4:001",
            "action_fingerprint": label_digest("f2-action"),
            "prohibited_behavior_list_revision": 1,
            "prohibited_boundary_evidence_ref": "fixture:f2-prohibited-boundary",
            "prohibited_boundary_evidence_fingerprint": label_digest("f2-prohibited-boundary"),
            "authority_event_sequence": 20,
        },
    )
    resident = stamped(
        "F4ResidentCommandBindingV0_1",
        {
            "interface_version": "agents-os.f4-resident-command-binding.v0.1",
            "resident_identity_ref": "resident:m0-a:synthetic",
            "resident_identity_revision": 1,
            "resident_incarnation_id": "resident-incarnation:m0-a:001",
            "resident_epoch": 1,
            "resident_continuity_assessment_ref": "fixture:f3-continuity",
            "resident_continuity_assessment_fingerprint": label_digest("f3-continuity"),
            "resident_continuity_result": "CONTINUOUS",
            "command_id": "command:m0-a:effect-intent:001",
            "command_fingerprint": label_digest("f3-command"),
            "command_type_id": "command-type:m0-a:synthetic-effect-intent",
            "command_type_version": 1,
            "command_definition_fingerprint": label_digest("f3-synthetic-command-definition"),
            "command_envelope_ref": "fixture:f3-command-envelope",
            "command_envelope_fingerprint": label_digest("f3-command-envelope"),
            "authenticated_context_ref": "fixture:f3-authenticated-context",
            "authenticated_context_fingerprint": label_digest("f3-authenticated-context"),
            "authenticated_action_ref": "fixture:f3-authenticated-action",
            "authenticated_action_fingerprint": label_digest("f3-authenticated-action"),
            "F3_contract_version": "F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE",
            "writer_event_sequence": 30,
        },
    )
    host_identity = stamped(
        "HostIdentityRevisionV0_1",
        {
            "interface_version": "agents-os.host-identity-revision.v0.1",
            "host_id": "host:m0-a:synthetic",
            "revision": 1,
            "previous_revision_ref": None,
            "previous_revision_fingerprint": None,
            "host_kind": "SYNTHETIC_M0_HOST",
            "controller_actor_id": "actor:m0-a:synthetic",
            "controller_actor_identity_revision": 1,
            "authenticator_profile_ref": "auth-profile:m0-a:synthetic",
            "authenticator_profile_revision": 1,
            "authenticator_profile_fingerprint": label_digest("host-authenticator-profile"),
            "credential_binding_ref": "credential-handle:m0-a:synthetic",
            "credential_binding_fingerprint": label_digest("host-credential-binding"),
            "lifecycle_state": "ACTIVE",
            "validity_start_utc_ms": 1_000,
            "validity_end_utc_ms": None,
            "issued_event_sequence": 40,
        },
    )
    host_auth = stamped(
        "HostAuthenticationAssessmentV0_1",
        {
            "interface_version": "agents-os.host-authentication-assessment.v0.1",
            "host_identity_ref": "fixture:host-identity",
            "host_identity_fingerprint": host_identity["canonical_fingerprint"],
            "authenticator_profile_ref": "auth-profile:m0-a:synthetic",
            "authenticator_profile_fingerprint": label_digest("host-authenticator-profile"),
            "challenge_ref": "challenge:m0-a:f4:001",
            "challenge_fingerprint": label_digest("host-challenge"),
            "verifier_identity_ref": "verifier:m0-a:synthetic",
            "verifier_profile_ref": "verifier-profile:m0-a:synthetic",
            "verification_evidence_ref": "verification-evidence:m0-a:f4:001",
            "verification_evidence_fingerprint": label_digest("host-verification-evidence"),
            "host_authentication_epoch": 1,
            "trusted_time_utc_ms": 1_500,
            "valid_until_utc_ms": 5_000,
            "host_revocation_event_sequence": 40,
            "result": "AUTHENTICATED",
            "reason": "MATCH",
        },
        "assessment_fingerprint",
    )
    fence = stamped(
        "F4FenceStateV0_1",
        {
            "interface_version": "agents-os.f4-fence-state.v0.1",
            "task_id": "task:m0-a:f4:001",
            "task_lifecycle_generation": 1,
            "host_id": "host:m0-a:synthetic",
            "execution_epoch": 1,
            "task_fence_generation": 1,
            "host_fence_generation": 1,
            "effect_fence_generation": 1,
            "fence_reason": "GENESIS",
            "source_event_ref": "fixture:f4-fence-genesis",
            "source_event_fingerprint": label_digest("f4-fence-genesis"),
            "event_sequence": 50,
        },
    )
    capability = stamped(
        "CapabilityGrantV0_1",
        {
            "capability_id": "capability:m0-a:synthetic-noop",
            "capability_revision": 1,
            "operation_set": ["SYNTHETIC_NOOP"],
            "constraint_fingerprint": label_digest("synthetic-capability-constraint"),
        },
    )
    resource = stamped(
        "ResourceGrantV0_1",
        {
            "resource_kind": "SYNTHETIC_M0_RESOURCE",
            "resource_ref": "resource:m0-a:synthetic:001",
            "resource_subject_fingerprint": label_digest("synthetic-resource"),
            "operation_set": ["SYNTHETIC_NOOP"],
            "selector_constraint_fingerprint": label_digest("synthetic-resource-selector"),
        },
    )
    capability_set_fingerprint = set_digest(
        "agents-os.f4-capability-set.v0.1", [capability["canonical_fingerprint"]]
    )
    resource_set_fingerprint = set_digest(
        "agents-os.f4-resource-set.v0.1", [resource["canonical_fingerprint"]]
    )
    secret_handle_set_fingerprint = set_digest(
        "agents-os.f4-secret-handle-set.v0.1", []
    )
    effect = stamped(
        "EffectIntentBindingV0_1",
        {
            "interface_version": "agents-os.effect-intent-binding.v0.1",
            "effect_intent_id": "effect-intent:m0-a:f4:001",
            "operation_kind": "SYNTHETIC_NOOP",
            "target_resource_refs": ["resource:m0-a:synthetic:001"],
            "payload_fingerprint": label_digest("synthetic-noop-payload"),
            "capability_set_fingerprint": capability_set_fingerprint,
            "resource_set_fingerprint": resource_set_fingerprint,
            "expected_result_contract_ref": "result-contract:m0-a:not-executed",
            "expected_result_contract_fingerprint": label_digest("synthetic-result-contract"),
            "idempotency_key": "idempotency:m0-a:f4:001",
            "side_effect_class": "GREEN",
            "external_effect_requested": True,
            "raw_payload_present": False,
        },
    )
    Jenn_authorization = stamped(
        "JennAuthorizationBindingV0_1",
        {
            "mode": "NOT_REQUIRED",
            "authorization_event_ref": None,
            "authorization_event_fingerprint": None,
            "Jenn_actor_identity_ref": None,
            "authorized_scope_fingerprint": None,
            "authorized_side_effect_class": None,
            "policy_bundle_revision": None,
            "prohibited_behavior_list_revision": None,
            "issued_at_utc_ms": None,
            "expires_at_utc_ms": None,
            "revocation_event_sequence": None,
            "currentness_result": "NOT_APPLICABLE",
        },
    )
    human_presence = stamped(
        "HumanPresenceBindingV0_1",
        {
            "mode": "NOT_REQUIRED",
            "presence_event_ref": None,
            "presence_event_fingerprint": None,
            "present_actor_id": None,
            "present_actor_identity_revision": None,
            "authorized_scope_fingerprint": None,
            "observer_host_id": None,
            "observed_at_utc_ms": None,
            "valid_until_utc_ms": None,
            "revocation_event_sequence": None,
            "currentness_result": "NOT_APPLICABLE",
        },
    )

    issuance_event_sequence = 70
    execution_epoch = 1
    permit_identity = permit_id(
        task["task_id"],
        task["task_lifecycle_generation"],
        execution_epoch,
        resident["command_id"],
        host_identity["host_id"],
        effect["idempotency_key"],
        issuance_event_sequence,
    )
    permit = stamped(
        "TaskPermitV0_1",
        {
            "interface_version": "agents-os.task-permit.v0.1",
            "F4_contract_version": CONTRACT,
            "permit_id": permit_identity,
            "permit_revision": 1,
            "issuance_event_sequence": issuance_event_sequence,
            "task_authority_binding": task,
            "actor_authority_binding": actor,
            "resident_command_binding": resident,
            "host_identity_ref": "fixture:host-identity",
            "host_identity_fingerprint": host_identity["canonical_fingerprint"],
            "host_authenticator_profile_ref": "auth-profile:m0-a:synthetic",
            "host_authenticator_profile_fingerprint": label_digest("host-authenticator-profile"),
            "host_authentication_assessment_ref": "fixture:host-authentication",
            "host_authentication_assessment_fingerprint": host_auth["assessment_fingerprint"],
            "host_authentication_epoch": 1,
            "issuer_resident_identity_ref": "resident:m0-a:synthetic",
            "issuer_resident_epoch": 1,
            "policy_bundle_revision": 1,
            "policy_bundle_fingerprint": label_digest("policy-bundle"),
            "prohibited_behavior_list_revision": 1,
            "prohibited_boundary_evidence_ref": "fixture:f4-prohibited-boundary",
            "prohibited_boundary_evidence_fingerprint": label_digest("f4-prohibited-boundary"),
            "capability_grants": [capability],
            "resource_grants": [resource],
            "effect_intent_binding": effect,
            "execution_epoch": execution_epoch,
            "host_fence_generation": 1,
            "effect_fence_generation": 1,
            "task_fence_generation": 1,
            "issued_at_utc_ms": 2_000,
            "not_before_utc_ms": 2_000,
            "expires_at_utc_ms": 10_000,
            "start_authority_commit_before_utc_ms": 5_000,
            "max_invocations": 1,
            "idempotency_key": "idempotency:m0-a:f4:001",
            "requires_human_presence": False,
            "human_presence_binding": human_presence,
            "Jenn_authorization_binding": Jenn_authorization,
            "secret_handle_bindings": [],
            "permit_attestation_profile_ref": "attestation-profile:m0-a:synthetic",
            "permit_attestation_profile_fingerprint": label_digest("permit-attestation-profile"),
            "permit_attestation_evidence_ref": "attestation-evidence:m0-a:f4:001",
            "permit_attestation_evidence_fingerprint": label_digest("permit-attestation-evidence"),
        },
    )
    permit_ref = "permit:" + permit_identity
    issuance_fact = stamped(
        "TaskPermitIssuanceFactV0_1",
        {
            "permit_ref": permit_ref,
            "permit_fingerprint": permit["canonical_fingerprint"],
            "issuance_command_envelope_ref": resident["command_envelope_ref"],
            "issuance_command_envelope_fingerprint": resident["command_envelope_fingerprint"],
            "issuance_event_sequence": issuance_event_sequence,
        },
        "fact_fingerprint",
    )
    currentness = stamped(
        "TaskPermitCurrentnessAssessmentV0_1",
        {
            "interface_version": "agents-os.task-permit-currentness-assessment.v0.1",
            "permit_ref": permit_ref,
            "permit_fingerprint": permit["canonical_fingerprint"],
            "lifecycle_state": "ISSUED",
            "trusted_time_utc_ms": 2_100,
            "task_binding_current": "PASS",
            "actor_binding_current": "PASS",
            "resident_command_binding_current": "PASS",
            "host_identity_current": "PASS",
            "host_authentication_current": "PASS",
            "policy_current": "PASS",
            "prohibited_boundary_current": "PASS",
            "capability_grants_current": "PASS",
            "resource_grants_current": "PASS",
            "secret_handle_bindings_current": "NOT_APPLICABLE",
            "permit_attestation_current": "PASS",
            "human_presence_current": "NOT_APPLICABLE",
            "Jenn_authorization_current": "NOT_APPLICABLE",
            "time_window_current": "PASS",
            "invocation_available": "PASS",
            "execution_epoch_current": "PASS",
            "host_fence_current": "PASS",
            "effect_fence_current": "PASS",
            "task_fence_current": "PASS",
            "result": "VALID",
            "reason": "ALL_CURRENT",
            "assessment_event_sequence": 80,
        },
        "assessment_fingerprint",
    )
    invocation = stamped(
        "PermitInvocationIdentityV0_1",
        {
            "permit_id": permit_identity,
            "permit_fingerprint": permit["canonical_fingerprint"],
            "invocation_ordinal": 1,
            "idempotency_key": "idempotency:m0-a:f4:001",
            "execution_epoch": 1,
            "host_id": "host:m0-a:synthetic",
            "effect_intent_fingerprint": effect["canonical_fingerprint"],
        },
    )
    request = stamped(
        "HostLocalAdmissionRequestV0_1",
        {
            "interface_version": "agents-os.host-local-admission-request.v0.1",
            "invocation_identity": invocation,
            "task_permit_ref": permit_ref,
            "task_permit_fingerprint": permit["canonical_fingerprint"],
            "effect_intent_ref": "fixture:effect-intent",
            "effect_intent_fingerprint": effect["canonical_fingerprint"],
            "resident_command_envelope_ref": resident["command_envelope_ref"],
            "resident_command_envelope_fingerprint": resident["command_envelope_fingerprint"],
            "target_host_id": "host:m0-a:synthetic",
            "target_host_identity_revision": 1,
            "requested_at_utc_ms": 2_200,
            "request_event_sequence": 81,
        },
    )
    decision = stamped(
        "HostLocalAdmissionDecisionV0_1",
        {
            "interface_version": "agents-os.host-local-admission-decision.v0.1",
            "invocation_identity_fingerprint": invocation["canonical_fingerprint"],
            "request_ref": "fixture:admission-request",
            "request_fingerprint": request["canonical_fingerprint"],
            "permit_currentness_assessment_ref": "fixture:permit-currentness",
            "permit_currentness_assessment_fingerprint": currentness["assessment_fingerprint"],
            "host_authentication_assessment_ref": "fixture:host-authentication",
            "host_authentication_assessment_fingerprint": host_auth["assessment_fingerprint"],
            "fence_state_ref": "fixture:fence-heads",
            "fence_state_fingerprint": fence["canonical_fingerprint"],
            "current_watermark_event_sequence": 80,
            "request_integrity": "PASS",
            "permit_currentness": "PASS",
            "host_authentication": "PASS",
            "host_ownership": "PASS",
            "task_fence_match": "PASS",
            "host_fence_match": "PASS",
            "effect_fence_match": "PASS",
            "execution_epoch_match": "PASS",
            "capability_subset": "PASS",
            "resource_subset": "PASS",
            "secret_handle_scope": "NOT_APPLICABLE",
            "permit_attestation": "PASS",
            "human_presence": "NOT_APPLICABLE",
            "effect_intent_exact_match": "PASS",
            "idempotency_identity_match": "PASS",
            "invocation_slot_available": "PASS",
            "prohibited_boundary": "PASS",
            "Jenn_authorization": "NOT_APPLICABLE",
            "decision": "ADMITTED",
            "reason": "ALL_CHECKS_PASS",
            "decided_at_utc_ms": 2_200,
        },
        "decision_fingerprint",
    )
    acceptance_identity = digest(
        [
            "agents-os.host-work-acceptance-id.v0.1",
            invocation["canonical_fingerprint"],
        ]
    )
    acceptance = stamped(
        "HostWorkAcceptanceFactV0_1",
        {
            "interface_version": "agents-os.host-work-acceptance-fact.v0.1",
            "acceptance_id": acceptance_identity,
            "invocation_identity": invocation,
            "admission_request_ref": "fixture:admission-request",
            "admission_request_fingerprint": request["canonical_fingerprint"],
            "admission_decision_ref": "fixture:admission-decision",
            "admission_decision_fingerprint": decision["decision_fingerprint"],
            "permit_currentness_assessment_ref": "fixture:permit-currentness",
            "permit_currentness_assessment_fingerprint": currentness["assessment_fingerprint"],
            "host_authentication_assessment_ref": "fixture:host-authentication",
            "host_authentication_assessment_fingerprint": host_auth["assessment_fingerprint"],
            "accepted_host_id": "host:m0-a:synthetic",
            "accepted_host_identity_revision": 1,
            "accepted_host_authentication_epoch": 1,
            "accepted_task_fence_generation": 1,
            "accepted_host_fence_generation": 1,
            "accepted_effect_fence_generation": 1,
            "accepted_execution_epoch": 1,
            "accepted_watermark_event_sequence": 84,
            "accepted_at_utc_ms": 2_300,
            "start_authority_expires_at_utc_ms": 5_000,
            "host_acceptance_attestation_ref": "attestation:host-acceptance:m0-a:001",
            "host_acceptance_attestation_fingerprint": label_digest("host-acceptance-attestation"),
        },
        "fact_fingerprint",
    )
    activation = stamped(
        "TaskPermitTransitionFactV0_1",
        {
            "permit_ref": permit_ref,
            "permit_fingerprint": permit["canonical_fingerprint"],
            "transition_kind": "ACTIVATE",
            "expected_previous_state": "ISSUED",
            "resulting_state": "ACTIVE",
            "reason": "HOST_ACCEPTANCE",
            "transition_action_ref": "acceptance:" + acceptance_identity,
            "transition_action_fingerprint": acceptance["fact_fingerprint"],
            "event_sequence": 84,
        },
        "fact_fingerprint",
    )
    observation_attempt = 1
    observation_identity = digest(
        [
            "agents-os.host-work-start-observation-id.v0.1",
            acceptance["fact_fingerprint"],
            observation_attempt,
        ]
    )
    start_disposition = stamped(
        "HostWorkStartDispositionFactV0_1",
        {
            "interface_version": "agents-os.host-work-start-disposition-fact.v0.1",
            "observation_id": observation_identity,
            "observation_attempt": observation_attempt,
            "acceptance_ref": "acceptance:" + acceptance_identity,
            "acceptance_fingerprint": acceptance["fact_fingerprint"],
            "invocation_identity_fingerprint": invocation["canonical_fingerprint"],
            "observed_host_id": "host:m0-a:synthetic",
            "observed_host_identity_revision": 1,
            "observed_host_authentication_epoch": 1,
            "rechecked_task_fence_generation": 1,
            "rechecked_host_fence_generation": 1,
            "rechecked_effect_fence_generation": 1,
            "rechecked_execution_epoch": 1,
            "rechecked_secret_handle_set_fingerprint": secret_handle_set_fingerprint,
            "rechecked_permit_attestation_fingerprint": label_digest("permit-attestation-evidence"),
            "rechecked_human_presence_binding_fingerprint": human_presence["canonical_fingerprint"],
            "secret_handles_current": "NOT_APPLICABLE",
            "permit_attestation_current": "PASS",
            "human_presence_current": "NOT_APPLICABLE",
            "disposition": "START_AUTHORITY_CURRENT",
            "reason": "ALL_RECHECKS_PASS",
            "observed_at_utc_ms": 2_400,
            "observation_event_sequence": 90,
            "host_observation_attestation_ref": "attestation:host-observation:m0-a:001",
            "host_observation_attestation_fingerprint": label_digest("host-observation-attestation"),
        },
        "fact_fingerprint",
    )
    handoff_identity = digest(
        [
            "agents-os.f4-accepted-effect-handoff-id.v0.1",
            invocation["canonical_fingerprint"],
        ]
    )
    handoff = stamped(
        "F4AcceptedEffectHandoffV0_1",
        {
            "interface_version": "agents-os.f4-accepted-effect-handoff.v0.1",
            "handoff_id": handoff_identity,
            "acceptance_ref": "acceptance:" + acceptance_identity,
            "acceptance_fingerprint": acceptance["fact_fingerprint"],
            "start_disposition_ref": "observation:" + observation_identity,
            "start_disposition_fingerprint": start_disposition["fact_fingerprint"],
            "invocation_identity": invocation,
            "task_permit_ref": permit_ref,
            "task_permit_fingerprint": permit["canonical_fingerprint"],
            "effect_intent_ref": "fixture:effect-intent",
            "effect_intent_fingerprint": effect["canonical_fingerprint"],
            "owner_host_id": "host:m0-a:synthetic",
            "owner_host_identity_revision": 1,
            "owner_host_authentication_epoch": 1,
            "execution_epoch": 1,
            "task_fence_generation": 1,
            "host_fence_generation": 1,
            "effect_fence_generation": 1,
            "start_authority_expires_at_utc_ms": 5_000,
            "capability_set_fingerprint": capability_set_fingerprint,
            "resource_set_fingerprint": resource_set_fingerprint,
            "secret_handle_set_fingerprint": secret_handle_set_fingerprint,
            "permit_attestation_evidence_fingerprint": label_digest("permit-attestation-evidence"),
            "human_presence_binding_fingerprint": human_presence["canonical_fingerprint"],
            "Jenn_authorization_binding_fingerprint": Jenn_authorization["canonical_fingerprint"],
            "expected_result_contract_ref": effect["expected_result_contract_ref"],
            "expected_result_contract_fingerprint": effect["expected_result_contract_fingerprint"],
            "handoff_event_sequence": 91,
        },
    )
    terminal_stub = stamped(
        "SyntheticF5BoundaryStubV0_1",
        {
            "interface_version": "agents-os.synthetic-f5-boundary-stub.v0.1",
            "fixture_only": True,
            "handoff_ref": "handoff:" + handoff_identity,
            "handoff_fingerprint": handoff["canonical_fingerprint"],
            "provider_call_count": 0,
            "network_call_count": 0,
            "process_start_count": 0,
            "file_mutation_count": 0,
            "device_actuation_count": 0,
            "external_effect_count": 0,
            "positive_non_execution_evidence": True,
            "terminal_outcome": "NOT_EXECUTED",
            "production_F5_fact": False,
        },
    )

    node_specs: list[tuple[str, str, tuple[str, ...], Any]] = [
        ("task_authority", "F1_TASK_AUTHORITY_BINDING", (), task),
        ("actor_authority", "F2_ACTOR_AUTHORITY_BINDING", (), actor),
        ("resident_command", "F3_RESIDENT_COMMAND_BINDING", ("actor_authority",), resident),
        ("host_identity", "F4_HOST_IDENTITY", ("actor_authority",), host_identity),
        ("host_authentication", "F4_HOST_AUTHENTICATION", ("host_identity",), host_auth),
        ("fence_heads", "F4_FENCE_HEADS", ("task_authority", "host_identity"), fence),
        (
            "effect_scope",
            "F4_EFFECT_SCOPE",
            ("task_authority", "actor_authority", "resident_command"),
            {
                "capability_grants": [capability],
                "resource_grants": [resource],
                "secret_handle_bindings": [],
                "capability_set_fingerprint": capability_set_fingerprint,
                "resource_set_fingerprint": resource_set_fingerprint,
                "secret_handle_set_fingerprint": secret_handle_set_fingerprint,
                "effect_intent_binding": effect,
                "human_presence_binding": human_presence,
                "Jenn_authorization_binding": Jenn_authorization,
            },
        ),
        (
            "task_permit",
            "F4_TASK_PERMIT_ISSUANCE",
            (
                "task_authority",
                "actor_authority",
                "resident_command",
                "host_identity",
                "host_authentication",
                "fence_heads",
                "effect_scope",
            ),
            {"permit": permit, "issuance_fact": issuance_fact},
        ),
        (
            "permit_currentness",
            "F4_PERMIT_CURRENTNESS",
            (
                "task_authority",
                "actor_authority",
                "resident_command",
                "host_identity",
                "host_authentication",
                "fence_heads",
                "task_permit",
            ),
            currentness,
        ),
        (
            "admission",
            "F4_LOCAL_ADMISSION",
            ("effect_scope", "task_permit", "permit_currentness"),
            {
                "invocation_identity": invocation,
                "request": request,
                "decision": decision,
            },
        ),
        (
            "work_acceptance",
            "F4_HOST_WORK_ACCEPTANCE",
            ("host_authentication", "fence_heads", "admission"),
            {"acceptance": acceptance, "activation_transition": activation},
        ),
        (
            "start_disposition",
            "F4_START_AUTHORITY_DISPOSITION",
            ("host_authentication", "fence_heads", "work_acceptance"),
            start_disposition,
        ),
        (
            "accepted_handoff",
            "F4_ACCEPTED_EFFECT_HANDOFF",
            ("effect_scope", "task_permit", "work_acceptance", "start_disposition"),
            handoff,
        ),
        (
            "zero_effect_terminal_stub",
            "SYNTHETIC_F5_BOUNDARY_STUB",
            ("accepted_handoff",),
            terminal_stub,
        ),
    ]

    fingerprints: dict[str, str] = {}
    nodes: list[dict[str, Any]] = []
    for ordinal, (node_id, kind, dependencies, value) in enumerate(node_specs, 1):
        upstream = [[dependency, fingerprints[dependency]] for dependency in dependencies]
        canonical_value = [NODE_DOMAIN, kind, node_id, value, upstream]
        node_fingerprint = digest(canonical_value)
        fingerprints[node_id] = node_fingerprint
        nodes.append(
            {
                "ordinal": ordinal,
                "node_id": node_id,
                "kind": kind,
                "depends_on": list(dependencies),
                "canonical_value": canonical_value,
                "sha256": node_fingerprint,
            }
        )

    assertions = {
        "node_count": len(nodes),
        "schema_fingerprint_count": len(fingerprinted_objects),
        "acceptance_count": 1,
        "accepted_handoff_count": 1,
        "start_authority_current_count": 1,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "real_resource_count": 0,
        "production_registry_entry_count": 0,
        "production_F5_fact_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }
    return {
        "interface_version": INTERFACE,
        "contract_version": CONTRACT,
        "mode": "SYNTHETIC_ZERO_EFFECT",
        "nodes": nodes,
        "assertions": assertions,
    }


def validate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    expected = build_expected_fixture()
    if fixture != expected:
        raise ValueError("fixture does not materialize the exact expected F4 M0-A witness")

    seen: dict[str, str] = {}
    edge_count = 0
    for expected_ordinal, node in enumerate(fixture["nodes"], 1):
        if node["ordinal"] != expected_ordinal:
            raise ValueError("node ordinals are not contiguous")
        if node["node_id"] in seen:
            raise ValueError(f"duplicate node_id: {node['node_id']}")
        for dependency in node["depends_on"]:
            if dependency not in seen:
                raise ValueError(f"non-topological dependency: {dependency}")
        edge_count += len(node["depends_on"])
        if digest(node["canonical_value"]) != node["sha256"]:
            raise ValueError(f"node hash mismatch: {node['node_id']}")
        upstream = node["canonical_value"][4]
        if upstream != [[dependency, seen[dependency]] for dependency in node["depends_on"]]:
            raise ValueError(f"upstream fingerprint mismatch: {node['node_id']}")
        seen[node["node_id"]] = node["sha256"]

    assertions = fixture["assertions"]
    zero_fields = (
        "external_effect_count",
        "provider_call_count",
        "raw_secret_count",
        "real_resource_count",
        "production_registry_entry_count",
        "production_F5_fact_count",
    )
    if any(assertions[field] != 0 for field in zero_fields):
        raise ValueError("zero-effect or non-production assertion failed")
    if assertions["acceptance_count"] != 1 or assertions["accepted_handoff_count"] != 1:
        raise ValueError("constructive acceptance/handoff count failed")
    if assertions["terminal_outcome"] != "NOT_EXECUTED":
        raise ValueError("synthetic terminal outcome is not NOT_EXECUTED")

    return {
        "result": "PASS",
        "interface_version": INTERFACE,
        "contract_version": CONTRACT,
        "node_count": len(fixture["nodes"]),
        "edge_count": edge_count,
        "node_hashes_verified": len(seen),
        "schema_fingerprints_verified": assertions["schema_fingerprint_count"],
        "acceptance_count": assertions["acceptance_count"],
        "accepted_handoff_count": assertions["accepted_handoff_count"],
        "external_effect_count": assertions["external_effect_count"],
        "provider_call_count": assertions["provider_call_count"],
        "raw_secret_count": assertions["raw_secret_count"],
        "terminal_outcome": assertions["terminal_outcome"],
        "fixture_canonical_sha256": digest(fixture),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--emit-fixture", action="store_true")
    args = parser.parse_args()

    if args.emit_fixture:
        print(json.dumps(build_expected_fixture(), ensure_ascii=False, indent=2))
        return 0

    try:
        fixture = json.loads(
            args.fixture.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_object_pairs,
        )
        result = validate_fixture(fixture)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(json.dumps({"result": "BLOCK", "error": str(error)}, sort_keys=True))
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
