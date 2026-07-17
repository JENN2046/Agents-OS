#!/usr/bin/env python3
"""Independently validate the F5 R2 full-effective synthetic proof fixture."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from itertools import combinations, product
from pathlib import Path
from typing import Any


DEFAULT_FIXTURE = Path("control-plane/registry/examples/2026-07-17-agents-os-f5-r2-full-effective-delivery-recovery-v0.1.json")
FIXTURE_INTERFACE = "agents-os.f5-r2-full-effective-fixture.v0.1"
PROOF_DOMAIN = "agents-os.f5-r2-full-effective-proof.v0.1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def h(domain: str, *values: Any) -> str:
    return digest([domain, *values])


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


SCHEMAS: list[tuple[str, str, str, list[str]]] = [
    ("F5OutboxIntentV0_1R1", "agents-os.f5-outbox-intent.v0.1-r1", "canonical_fingerprint", "interface_version outbox_intent_id outbox_intent_ref source_handoff_ref source_handoff_fingerprint source_handoff_event_sequence invocation_identity_fingerprint effect_id effect_scope_ref effect_scope_fingerprint expected_result_contract_ref expected_result_contract_fingerprint owner_host_id execution_epoch task_fence_generation host_fence_generation effect_fence_generation start_authority_expires_at_utc_ms completion_blocking delivery_profile_ref delivery_profile_fingerprint created_at_utc_ms created_event_sequence environment authority_eligible canonical_fingerprint".split()),
    ("F5EnqueueDispositionV0_1R1", "agents-os.f5-enqueue-disposition.v0.1-r1", "canonical_fingerprint", "interface_version source_handoff_ref source_handoff_fingerprint outbox_intent_ref outbox_intent_fingerprint result primary_reason reason_codes observed_at_utc_ms observed_event_sequence canonical_fingerprint".split()),
    ("F5DispatcherClaimantAssessmentV0_1R1", "agents-os.f5-dispatcher-claimant-assessment.v0.1-r1", "canonical_fingerprint", "interface_version dispatcher_actor_id dispatcher_actor_identity_ref dispatcher_actor_identity_fingerprint dispatcher_principal_id dispatcher_principal_ref dispatcher_principal_fingerprint dispatcher_binding_assessment_ref dispatcher_binding_assessment_fingerprint resident_authority_epoch resident_continuity_assessment_ref resident_continuity_assessment_fingerprint owner_head_event_sequence assessed_at_event_sequence result environment authority_eligible canonical_fingerprint".split()),
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "agents-os.f5-physical-boundary-authority-observation.v0.1-r1", "canonical_fingerprint", "interface_version observation_purpose outbox_intent_ref outbox_intent_fingerprint source_handoff_ref source_handoff_fingerprint fresh_F4_assessment_ref fresh_F4_assessment_fingerprint fresh_F4_assessment_result observed_task_fence_generation observed_host_fence_generation observed_effect_fence_generation observed_execution_epoch observed_host_id observed_at_utc_ms observed_event_sequence canonical_writer_head_event_sequence result primary_reason reason_codes canonical_fingerprint".split()),
    ("F5OutboxClaimFactV0_1R1", "agents-os.f5-outbox-claim-fact.v0.1-r1", "canonical_fingerprint", "interface_version claim_id claim_ref outbox_intent_ref outbox_intent_fingerprint claim_epoch expected_previous_claim_epoch claimant_assessment_ref claimant_assessment_fingerprint claim_authority_observation_ref claim_authority_observation_fingerprint lease_expires_at_utc_ms claim_fencing_token claimed_at_utc_ms claim_event_sequence result primary_reason reason_codes canonical_fingerprint".split()),
    ("F5OutboxLeaseFactV0_1R1", "agents-os.f5-outbox-lease-fact.v0.1-r1", "canonical_fingerprint", "interface_version lease_fact_id claim_ref claim_fingerprint claim_epoch claim_fencing_token previous_lease_expiry_utc_ms new_lease_expiry_utc_ms renewed_at_utc_ms renewal_event_sequence result primary_reason reason_codes canonical_fingerprint".split()),
    ("F5DispatchArmRequestV0_1R2", "agents-os.f5-dispatch-arm-request.v0.1-r2", "canonical_fingerprint", "interface_version dispatch_arm_request_id outbox_intent_ref outbox_intent_fingerprint invocation_identity_fingerprint claim_ref claim_fingerprint claim_epoch claim_fencing_token attempt_ordinal attempt_id idempotency_key physical_boundary_observation_ref physical_boundary_observation_fingerprint requested_at_utc_ms requested_event_sequence canonical_fingerprint".split()),
    ("F5DispatchArmDispositionV0_1R2", "agents-os.f5-dispatch-arm-disposition.v0.1-r2", "canonical_fingerprint", "interface_version dispatch_arm_request_id dispatch_arm_request_fingerprint replay_relation first_arm_ref first_arm_fingerprint result primary_reason reason_codes event_created physical_call_authorized observed_event_sequence canonical_fingerprint".split()),
    ("F5DispatchArmFactV0_1R2", "agents-os.f5-dispatch-arm-fact.v0.1-r2", "canonical_fingerprint", "interface_version dispatch_arm_id dispatch_arm_ref dispatch_arm_request_id dispatch_arm_request_fingerprint outbox_intent_ref outbox_intent_fingerprint claim_ref claim_fingerprint claim_epoch claim_fencing_token attempt_ordinal attempt_id idempotency_key physical_boundary_observation_ref physical_boundary_observation_fingerprint armed_at_utc_ms armed_event_sequence arm_transaction_ref arm_transaction_fingerprint canonical_fingerprint".split()),
    ("F5DeliveryAttemptFactV0_1R1", "agents-os.f5-delivery-attempt-fact.v0.1-r1", "canonical_fingerprint", "interface_version attempt_id attempt_ref dispatch_arm_ref dispatch_arm_fingerprint outbox_intent_ref outbox_intent_fingerprint attempt_ordinal idempotency_key transport_profile_ref transport_profile_fingerprint started_at_utc_ms returned_at_utc_ms outcome outcome_evidence_ref outcome_evidence_fingerprint effect_may_have_occurred automatic_retry_eligible attempt_event_sequence canonical_fingerprint".split()),
    ("F5DeliveryReceiptV0_1R1", "agents-os.f5-delivery-receipt.v0.1-r1", "canonical_fingerprint", "interface_version receipt_id source_id source_receipt_revision attempt_ref attempt_fingerprint outbox_intent_ref outbox_intent_fingerprint effect_id invocation_identity_fingerprint execution_epoch host_fence_generation effect_fence_generation receipt_kind effect_status observed_at_utc_ms received_at_utc_ms source_attestation_ref source_attestation_fingerprint canonical_fingerprint".split()),
    ("F5DeliveryReceiptDispositionV0_1R2", "agents-os.f5-delivery-receipt-disposition.v0.1-r2", "canonical_fingerprint", "interface_version source_id receipt_id receipt_fingerprint dedup_relation result primary_reason reason_codes event_created reconciliation_opened current_projection_advanced task_advancement_eligible observed_event_sequence canonical_fingerprint".split()),
    ("F5DeadLetterFactV0_1R1", "agents-os.f5-dead-letter-fact.v0.1-r1", "canonical_fingerprint", "interface_version dead_letter_id outbox_intent_ref outbox_intent_fingerprint last_claim_ref last_claim_fingerprint last_attempt_ref last_attempt_fingerprint reason effect_outcome reconciliation_required dead_lettered_at_utc_ms dead_letter_event_sequence canonical_fingerprint".split()),
    ("F5ReconciliationCaseV0_1R1", "agents-os.f5-reconciliation-case.v0.1-r1", "canonical_fingerprint", "interface_version reconciliation_id outbox_intent_ref outbox_intent_fingerprint attempt_ref attempt_fingerprint reason status resolution evidence_refs evidence_set_fingerprint owner_next_action opened_event_sequence last_updated_event_sequence canonical_fingerprint".split()),
    ("F5OutboxProjectionV0_1R1", "agents-os.f5-outbox-projection.v0.1-r1", "projection_fingerprint", "interface_version outbox_intent_ref outbox_intent_fingerprint projection_version last_event_sequence state current_claim_ref current_claim_fingerprint current_attempt_ref current_attempt_fingerprint current_reconciliation_ref current_reconciliation_fingerprint effect_outcome automatic_retry_eligible completion_blocking projection_fingerprint".split()),
    ("F5SyntheticDeliveryRecoveryWitnessV0_1R1", "agents-os.f5-synthetic-delivery-recovery-witness.v0.1-r1", "canonical_fingerprint", "interface_version witness_ref witness_namespace environment fingerprint_domain prospective_F4_handoff_requirement_ref prospective_F4_handoff_requirement_fingerprint vector_set_fingerprint authority_eligible runtime_consumable recovery_importable physical_effect_boundary terminal_outcome accepted_real_handoff_count armed_dispatch_count external_effect_count provider_call_count raw_secret_count canonical_fingerprint".split()),
]

CLAIM_PRECEDENCE = "INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED DISPATCH_ALREADY_ARMED CLAIM_ALREADY_ACTIVE INTENT_NOT_PENDING CLAIMANT_STALE CLAIMANT_UNAVAILABLE AUTHORITY_STALE AUTHORITY_UNAVAILABLE EXPIRED CAS_MISMATCH CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY CLAIMED_NEW".split()
LEASE_PRECEDENCE = "INTEGRITY_FAILURE CLAIM_STALE TOKEN_MISMATCH DISPATCH_ALREADY_ARMED EXPIRED CAS_MISMATCH RENEWED".split()
ARM_PRECEDENCE = "INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED CLAIM_STALE TOKEN_MISMATCH AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED OBSERVATION_UNAVAILABLE CAS_MISMATCH ARMED_FIRST_APPLY".split()

RECEIPT_KINDS = "TRANSPORT_ACK EFFECT_SUCCEEDED EFFECT_FAILED EFFECT_STATUS_UNKNOWN EFFECT_QUERY_RESULT".split()
EFFECT_STATUSES = "ACKED_ONLY SUCCEEDED FAILED UNKNOWN NOT_EXECUTED".split()
RECEIPT_ALLOWED = {"TRANSPORT_ACK": {"ACKED_ONLY"}, "EFFECT_SUCCEEDED": {"SUCCEEDED"}, "EFFECT_FAILED": {"FAILED"}, "EFFECT_STATUS_UNKNOWN": {"UNKNOWN"}, "EFFECT_QUERY_RESULT": {"SUCCEEDED", "FAILED", "UNKNOWN", "NOT_EXECUTED"}}

STATES = "PENDING CLAIMED DISPATCH_ARMED DISPATCHED ACKED SUCCEEDED FAILED UNKNOWN DEAD_LETTERED RECONCILED".split()
ALLOWED_TRANSITIONS = {
    ("PENDING", "CLAIMED"), ("PENDING", "DEAD_LETTERED"),
    ("CLAIMED", "CLAIMED"), ("CLAIMED", "DISPATCH_ARMED"), ("CLAIMED", "DEAD_LETTERED"),
    ("DISPATCH_ARMED", "DISPATCHED"), ("DISPATCH_ARMED", "ACKED"), ("DISPATCH_ARMED", "SUCCEEDED"), ("DISPATCH_ARMED", "FAILED"), ("DISPATCH_ARMED", "UNKNOWN"),
    ("DISPATCHED", "ACKED"), ("DISPATCHED", "SUCCEEDED"), ("DISPATCHED", "FAILED"), ("DISPATCHED", "UNKNOWN"),
    ("ACKED", "SUCCEEDED"), ("ACKED", "FAILED"), ("ACKED", "UNKNOWN"),
    ("FAILED", "RECONCILED"), ("UNKNOWN", "RECONCILED"), ("DEAD_LETTERED", "RECONCILED"),
}

ADVERSARIAL = {
    "synthetic_handoff_or_witness_presented_to_production": "REJECT_SYNTHETIC_NONAUTHORITY",
    "F4_handoff_ref_match_with_fingerprint_mismatch": "REJECT_INTEGRITY_FAILURE",
    "F5_local_override_of_F4_REJECTED_or_INDETERMINATE": "REJECT_NO_LOCAL_OVERRIDE",
    "old_F4_assessment_reused_at_later_writer_head": "REJECT_AUTHORITY_STALE",
    "observed_time_equal_to_expiry": "REJECT_EXPIRED_EXCLUSIVE_BOUND",
    "dispatcher_label_without_current_F2_F3_assessments": "REJECT_CLAIMANT_UNAVAILABLE",
    "skipped_duplicate_or_stale_claim_epoch": "REJECT_CAS_OR_STALE_EPOCH",
    "stale_claim_token_or_lease_CAS": "REJECT_TOKEN_OR_CAS_MISMATCH",
    "lease_extension_beyond_authority_expiry": "REJECT_EXPIRY_BOUND",
    "second_claim_while_current_claim_active": "REJECT_CLAIM_ALREADY_ACTIVE",
    "second_claim_or_arm_after_a_dispatch_arm_exists": "REJECT_DISPATCH_ALREADY_ARMED",
    "exact_arm_replay_without_second_call": "REPLAY_FIRST_ACCOUNTING_ZERO_CALL",
    "changed_arm_bytes_under_same_identity": "REJECT_REQUEST_BYTES_CONFLICT",
    "caller_selected_or_changed_idempotency_key": "REJECT_EFFECT_ID_MISMATCH",
    "crash_after_arm_before_call": "UNKNOWN_NO_AUTOMATIC_RETRY",
    "crash_after_call_before_receipt": "UNKNOWN_NO_AUTOMATIC_RETRY",
    "ACK_treated_as_SUCCEEDED": "REJECT_RECEIPT_KIND_STATUS_MISMATCH",
    "FAILED_treated_as_NOT_EXECUTED": "REJECT_FAILED_MAY_HAVE_EFFECT",
    "UNKNOWN_or_PRE_EFFECT_NOT_EXECUTED_marked_auto_retry_after_arm": "REJECT_AUTOMATIC_RETRY_FALSE",
    "dead_letter_treated_as_effect_failure_or_completion": "REJECT_ACCOUNTING_ONLY",
    "changed_receipt_under_same_source_and_receipt_id": "REJECT_RECEIPT_BYTES_CONFLICT",
    "old_epoch_late_SUCCEEDED_advances_current_Task": "RETAIN_HISTORY_NO_CURRENT_ADVANCEMENT",
    "reconciliation_opens_new_attempt_or_compensation": "REJECT_EXISTING_EFFECT_QUERY_ONLY",
    "projection_rebuild_emits_claim_arm_Event_or_effect": "REJECT_ZERO_EFFECT_REBUILD_ONLY",
    "missing_recovery_barrier_allows_ordinary_claim": "REJECT_BARRIER_REQUIRED",
    "PBL_no_match_creates_delivery_authority": "REJECT_PBL_NOT_POSITIVE_AUTHORITY",
    "permission_lane_or_role_label_changes_delivery_result": "REJECT_LABELS_NONAUTHORITATIVE",
    "any_nonzero_real_handoff_arm_runtime_effect_provider_or_secret_count": "REJECT_NONZERO_COUNT",
}

ADVERSARIAL_INPUTS: dict[str, dict[str, Any]] = {
    "synthetic_handoff_or_witness_presented_to_production": {"target_environment": "PRODUCTION", "evidence_environment": "SYNTHETIC_TEST", "authority_eligible": False},
    "F4_handoff_ref_match_with_fingerprint_mismatch": {"ref_match": True, "fingerprint_match": False},
    "F5_local_override_of_F4_REJECTED_or_INDETERMINATE": {"F4_result": "REJECTED", "F5_requested_result": "CURRENT"},
    "old_F4_assessment_reused_at_later_writer_head": {"assessment_head": 10, "writer_head": 11},
    "observed_time_equal_to_expiry": {"observed_at_utc_ms": 1000, "expiry_utc_ms": 1000},
    "dispatcher_label_without_current_F2_F3_assessments": {"dispatcher_label": True, "F2_current": False, "F3_current": False},
    "skipped_duplicate_or_stale_claim_epoch": {"previous_epoch": 3, "submitted_epoch": 5},
    "stale_claim_token_or_lease_CAS": {"token_match": False, "cas_match": False},
    "lease_extension_beyond_authority_expiry": {"new_lease_expiry": 2000, "authority_expiry": 1500},
    "second_claim_while_current_claim_active": {"current_claim_active": True},
    "second_claim_or_arm_after_a_dispatch_arm_exists": {"dispatch_arm_exists": True},
    "exact_arm_replay_without_second_call": {"replay_relation": "EXACT_DUPLICATE", "requested_second_call": True},
    "changed_arm_bytes_under_same_identity": {"replay_relation": "CHANGED_BYTES_SAME_IDENTITY"},
    "caller_selected_or_changed_idempotency_key": {"supplied_key": "caller-key", "effect_id": "bound-effect"},
    "crash_after_arm_before_call": {"arm_committed": True, "call_started": False, "certainty": False},
    "crash_after_call_before_receipt": {"call_started": True, "receipt_present": False, "certainty": False},
    "ACK_treated_as_SUCCEEDED": {"receipt_kind": "TRANSPORT_ACK", "effect_status": "SUCCEEDED"},
    "FAILED_treated_as_NOT_EXECUTED": {"attempt_outcome": "FAILED", "claimed_effect_may_have_occurred": False},
    "UNKNOWN_or_PRE_EFFECT_NOT_EXECUTED_marked_auto_retry_after_arm": {"arm_exists": True, "attempt_outcome": "UNKNOWN", "automatic_retry_eligible": True},
    "dead_letter_treated_as_effect_failure_or_completion": {"dead_letter_present": True, "claimed_completion": True},
    "changed_receipt_under_same_source_and_receipt_id": {"dedup_relation": "CHANGED_BYTES_SAME_KEY"},
    "old_epoch_late_SUCCEEDED_advances_current_Task": {"receipt_epoch": 1, "current_epoch": 2, "requested_current_advancement": True},
    "reconciliation_opens_new_attempt_or_compensation": {"reconciliation_creates_attempt": True},
    "projection_rebuild_emits_claim_arm_Event_or_effect": {"rebuild_emits_event": True},
    "missing_recovery_barrier_allows_ordinary_claim": {"recovery_barrier_complete": False, "ordinary_claim_requested": True},
    "PBL_no_match_creates_delivery_authority": {"PBL_match": False, "upstream_authority_current": False, "requested_allow": True},
    "permission_lane_or_role_label_changes_delivery_result": {"authority_inputs_equal": True, "label_changed": True, "delivery_result_changed": True},
    "any_nonzero_real_handoff_arm_runtime_effect_provider_or_secret_count": {"accepted_real_handoff_count": 0, "armed_dispatch_count": 0, "runtime_consumable_count": 0, "external_effect_count": 1, "provider_call_count": 0, "raw_secret_count": 0},
}


def independent_adversarial_decision(name: str, data: dict[str, Any]) -> str:
    if name == "synthetic_handoff_or_witness_presented_to_production":
        return "REJECT_SYNTHETIC_NONAUTHORITY" if data["target_environment"] == "PRODUCTION" and (data["evidence_environment"] != "PRODUCTION" or not data["authority_eligible"]) else "UNEXPECTED_ACCEPT"
    if name == "F4_handoff_ref_match_with_fingerprint_mismatch":
        return "REJECT_INTEGRITY_FAILURE" if data["ref_match"] and not data["fingerprint_match"] else "UNEXPECTED_ACCEPT"
    if name == "F5_local_override_of_F4_REJECTED_or_INDETERMINATE":
        return "REJECT_NO_LOCAL_OVERRIDE" if data["F4_result"] != "CURRENT" and data["F5_requested_result"] == "CURRENT" else "UNEXPECTED_ACCEPT"
    if name == "old_F4_assessment_reused_at_later_writer_head":
        return "REJECT_AUTHORITY_STALE" if data["assessment_head"] != data["writer_head"] else "UNEXPECTED_ACCEPT"
    if name == "observed_time_equal_to_expiry":
        return "REJECT_EXPIRED_EXCLUSIVE_BOUND" if data["observed_at_utc_ms"] >= data["expiry_utc_ms"] else "UNEXPECTED_ACCEPT"
    if name == "dispatcher_label_without_current_F2_F3_assessments":
        return "REJECT_CLAIMANT_UNAVAILABLE" if data["dispatcher_label"] and not (data["F2_current"] and data["F3_current"]) else "UNEXPECTED_ACCEPT"
    if name == "skipped_duplicate_or_stale_claim_epoch":
        return "REJECT_CAS_OR_STALE_EPOCH" if data["submitted_epoch"] != data["previous_epoch"] + 1 else "UNEXPECTED_ACCEPT"
    if name == "stale_claim_token_or_lease_CAS":
        return "REJECT_TOKEN_OR_CAS_MISMATCH" if not data["token_match"] or not data["cas_match"] else "UNEXPECTED_ACCEPT"
    if name == "lease_extension_beyond_authority_expiry":
        return "REJECT_EXPIRY_BOUND" if data["new_lease_expiry"] > data["authority_expiry"] else "UNEXPECTED_ACCEPT"
    if name == "second_claim_while_current_claim_active":
        return "REJECT_CLAIM_ALREADY_ACTIVE" if data["current_claim_active"] else "UNEXPECTED_ACCEPT"
    if name == "second_claim_or_arm_after_a_dispatch_arm_exists":
        return "REJECT_DISPATCH_ALREADY_ARMED" if data["dispatch_arm_exists"] else "UNEXPECTED_ACCEPT"
    if name == "exact_arm_replay_without_second_call":
        return "REPLAY_FIRST_ACCOUNTING_ZERO_CALL" if data["replay_relation"] == "EXACT_DUPLICATE" else "UNEXPECTED_ACCEPT"
    if name == "changed_arm_bytes_under_same_identity":
        return "REJECT_REQUEST_BYTES_CONFLICT" if data["replay_relation"] == "CHANGED_BYTES_SAME_IDENTITY" else "UNEXPECTED_ACCEPT"
    if name == "caller_selected_or_changed_idempotency_key":
        return "REJECT_EFFECT_ID_MISMATCH" if data["supplied_key"] != data["effect_id"] else "UNEXPECTED_ACCEPT"
    if name == "crash_after_arm_before_call":
        return "UNKNOWN_NO_AUTOMATIC_RETRY" if data["arm_committed"] and not data["certainty"] else "UNEXPECTED_ACCEPT"
    if name == "crash_after_call_before_receipt":
        return "UNKNOWN_NO_AUTOMATIC_RETRY" if data["call_started"] and not data["receipt_present"] and not data["certainty"] else "UNEXPECTED_ACCEPT"
    if name == "ACK_treated_as_SUCCEEDED":
        return "REJECT_RECEIPT_KIND_STATUS_MISMATCH" if data["effect_status"] not in RECEIPT_ALLOWED[data["receipt_kind"]] else "UNEXPECTED_ACCEPT"
    if name == "FAILED_treated_as_NOT_EXECUTED":
        return "REJECT_FAILED_MAY_HAVE_EFFECT" if data["attempt_outcome"] == "FAILED" and not data["claimed_effect_may_have_occurred"] else "UNEXPECTED_ACCEPT"
    if name == "UNKNOWN_or_PRE_EFFECT_NOT_EXECUTED_marked_auto_retry_after_arm":
        return "REJECT_AUTOMATIC_RETRY_FALSE" if data["arm_exists"] and data["attempt_outcome"] in {"UNKNOWN", "PRE_EFFECT_NOT_EXECUTED"} and data["automatic_retry_eligible"] else "UNEXPECTED_ACCEPT"
    if name == "dead_letter_treated_as_effect_failure_or_completion":
        return "REJECT_ACCOUNTING_ONLY" if data["dead_letter_present"] and data["claimed_completion"] else "UNEXPECTED_ACCEPT"
    if name == "changed_receipt_under_same_source_and_receipt_id":
        return "REJECT_RECEIPT_BYTES_CONFLICT" if data["dedup_relation"] == "CHANGED_BYTES_SAME_KEY" else "UNEXPECTED_ACCEPT"
    if name == "old_epoch_late_SUCCEEDED_advances_current_Task":
        return "RETAIN_HISTORY_NO_CURRENT_ADVANCEMENT" if data["receipt_epoch"] < data["current_epoch"] and data["requested_current_advancement"] else "UNEXPECTED_ACCEPT"
    if name == "reconciliation_opens_new_attempt_or_compensation":
        return "REJECT_EXISTING_EFFECT_QUERY_ONLY" if data["reconciliation_creates_attempt"] else "UNEXPECTED_ACCEPT"
    if name == "projection_rebuild_emits_claim_arm_Event_or_effect":
        return "REJECT_ZERO_EFFECT_REBUILD_ONLY" if data["rebuild_emits_event"] else "UNEXPECTED_ACCEPT"
    if name == "missing_recovery_barrier_allows_ordinary_claim":
        return "REJECT_BARRIER_REQUIRED" if not data["recovery_barrier_complete"] and data["ordinary_claim_requested"] else "UNEXPECTED_ACCEPT"
    if name == "PBL_no_match_creates_delivery_authority":
        return "REJECT_PBL_NOT_POSITIVE_AUTHORITY" if not data["PBL_match"] and not data["upstream_authority_current"] and data["requested_allow"] else "UNEXPECTED_ACCEPT"
    if name == "permission_lane_or_role_label_changes_delivery_result":
        return "REJECT_LABELS_NONAUTHORITATIVE" if data["authority_inputs_equal"] and data["label_changed"] and data["delivery_result_changed"] else "UNEXPECTED_ACCEPT"
    if name == "any_nonzero_real_handoff_arm_runtime_effect_provider_or_secret_count":
        keys = ("accepted_real_handoff_count", "armed_dispatch_count", "runtime_consumable_count", "external_effect_count", "provider_call_count", "raw_secret_count")
        return "REJECT_NONZERO_COUNT" if any(data[key] != 0 for key in keys) else "UNEXPECTED_ACCEPT"
    raise ValueError(f"unknown adversarial check: {name}")


def section_fingerprint(name: str, value: Any) -> str:
    return h(PROOF_DOMAIN, name, value)


def expected_profile(name: str, interface: str, fp_field: str, fields: list[str]) -> dict[str, Any]:
    row = {"schema_name": name, "interface_version": interface, "fingerprint_field": fp_field, "fields": fields}
    row["schema_profile_fingerprint"] = h(PROOF_DOMAIN, "schema-profile", name, interface, fp_field, fields)
    return row


def object_fingerprint(obj: dict[str, Any], fields: list[str], fp_field: str) -> str:
    return h(obj["interface_version"] + "-fingerprint", *[obj[field] for field in fields if field != fp_field])


def validate_profiles(fixture: dict[str, Any]) -> None:
    expected = [expected_profile(*schema) for schema in SCHEMAS]
    ensure(fixture["schema_profiles"] == expected, "schema profile inventory mismatch")


def validate_instances(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = fixture["canonical_instances"]
    ensure(len(rows) == len(SCHEMAS), "canonical instance count mismatch")
    by_name = {row["schema_name"]: row["object"] for row in rows}
    ensure(set(by_name) == {name for name, *_ in SCHEMAS}, "canonical instance schema set mismatch")
    for name, interface, fp_field, fields in SCHEMAS:
        obj = by_name[name]
        ensure(set(obj) == set(fields) and len(obj) == len(fields), f"{name} field inventory mismatch")
        ensure(obj["interface_version"] == interface, f"{name} interface mismatch")
        ensure(obj[fp_field] == object_fingerprint(obj, fields, fp_field), f"{name} fingerprint mismatch")
    ensure(by_name["F5OutboxIntentV0_1R1"]["environment"] == "SYNTHETIC_TEST", "intent environment must be synthetic")
    ensure(by_name["F5OutboxIntentV0_1R1"]["authority_eligible"] is False, "synthetic intent cannot be authority eligible")
    witness = by_name["F5SyntheticDeliveryRecoveryWitnessV0_1R1"]
    ensure(witness["authority_eligible"] is False and witness["runtime_consumable"] is False and witness["recovery_importable"] is False, "witness authority boundary failed")
    ensure(witness["accepted_real_handoff_count"] == witness["armed_dispatch_count"] == witness["external_effect_count"] == witness["provider_call_count"] == witness["raw_secret_count"] == 0, "witness zero count failed")
    receipt_disposition = by_name["F5DeliveryReceiptDispositionV0_1R2"]
    ensure(receipt_disposition["task_advancement_eligible"] is False, "F5 receipt cannot make Task advancement eligible")
    ensure(receipt_disposition["dedup_relation"] == "NEW" and receipt_disposition["result"] == "APPLIED" and receipt_disposition["primary_reason"] == "APPLIED_CURRENT", "receipt disposition sample mismatch")
    return by_name


def validate_identities(fixture: dict[str, Any], by_name: dict[str, dict[str, Any]]) -> None:
    intent = by_name["F5OutboxIntentV0_1R1"]
    claim = by_name["F5OutboxClaimFactV0_1R1"]
    request = by_name["F5DispatchArmRequestV0_1R2"]
    arm = by_name["F5DispatchArmFactV0_1R2"]
    expected = {
        "outbox_intent_id": h("agents-os.f5-outbox-intent-id.v0.1", intent["source_handoff_fingerprint"], intent["invocation_identity_fingerprint"], intent["effect_id"]),
        "claim_id": h("agents-os.f5-outbox-claim-id.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"]),
        "claim_fencing_token": h("agents-os.f5-outbox-claim-fence.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"], claim["claimant_assessment_fingerprint"]),
        "attempt_id": h("agents-os.f5-delivery-attempt-id.v0.1", request["outbox_intent_fingerprint"], request["attempt_ordinal"]),
        "dispatch_arm_request_id": h("agents-os.f5-dispatch-arm-request-id.v0.1", request["outbox_intent_fingerprint"], request["invocation_identity_fingerprint"], request["attempt_ordinal"]),
        "dispatch_arm_id": h("agents-os.f5-dispatch-arm-id.v0.2", request["dispatch_arm_request_id"]),
    }
    ensure(fixture["derived_identities"] == expected, "derived identity proof mismatch")
    ensure(intent["outbox_intent_id"] == expected["outbox_intent_id"], "intent ID mismatch")
    ensure(claim["claim_id"] == expected["claim_id"] and claim["claim_fencing_token"] == expected["claim_fencing_token"], "claim identity mismatch")
    ensure(request["attempt_id"] == expected["attempt_id"], "attempt identity mismatch")
    ensure(request["dispatch_arm_request_id"] == h("agents-os.f5-dispatch-arm-request-id.v0.1", request["outbox_intent_fingerprint"], request["invocation_identity_fingerprint"], request["attempt_ordinal"]), "arm request ID mismatch")
    ensure(arm["dispatch_arm_id"] == expected["dispatch_arm_id"], "arm ID mismatch")
    ensure(request["idempotency_key"] == intent["effect_id"] == arm["idempotency_key"], "idempotency key mismatch")
    disposition = by_name["F5DispatchArmDispositionV0_1R2"]
    ensure(disposition["dispatch_arm_request_id"] == request["dispatch_arm_request_id"] and disposition["dispatch_arm_request_fingerprint"] == request["canonical_fingerprint"], "arm disposition request binding mismatch")
    ensure(disposition["first_arm_ref"] == arm["dispatch_arm_ref"] and disposition["first_arm_fingerprint"] == arm["canonical_fingerprint"], "first-apply disposition arm binding mismatch")


def expected_pairwise() -> list[dict[str, Any]]:
    result = []
    for kind, precedence in (("claim", CLAIM_PRECEDENCE), ("lease", LEASE_PRECEDENCE), ("arm", ARM_PRECEDENCE)):
        failures = precedence[:-2] if kind == "claim" else precedence[:-1]
        for left, right in combinations(failures, 2):
            result.append({"case_id": f"{kind.upper()}_{left}__{right}", "kind": kind, "active_reasons": [right, left], "expected_primary_reason": left, "expected_reason_codes": sorted([left, right])})
    return result


def validate_precedence(fixture: dict[str, Any]) -> None:
    ensure(fixture["pairwise_precedence_cases"] == expected_pairwise(), "pairwise precedence proof mismatch")


def expected_replay() -> list[dict[str, Any]]:
    outputs = {"NO_EXISTING_ARM": ("APPLIED", "ARMED_FIRST_APPLY", True, True), "EXACT_DUPLICATE": ("REPLAYED", "EXACT_DUPLICATE_REPLAY", False, False), "CHANGED_BYTES_SAME_IDENTITY": ("REJECTED", "REQUEST_BYTES_CONFLICT", False, False), "LOOKUP_INDETERMINATE": ("INDETERMINATE", "ARM_LOOKUP_UNAVAILABLE", False, False)}
    return [{"relation": relation, "expected": {"result": values[0], "primary_reason": values[1], "event_created": values[2], "physical_call_authorized": values[3]}} for relation, values in outputs.items()]


def validate_replay(fixture: dict[str, Any]) -> None:
    ensure(fixture["arm_replay_cases"] == expected_replay(), "arm replay proof mismatch")


def expected_receipts() -> list[dict[str, Any]]:
    return [{"receipt_kind": kind, "effect_status": status, "expected": "APPLIED" if status in RECEIPT_ALLOWED[kind] else "REJECTED_RECEIPT_KIND_STATUS_MISMATCH"} for kind, status in product(RECEIPT_KINDS, EFFECT_STATUSES)]


def validate_receipts(fixture: dict[str, Any]) -> None:
    ensure(fixture["receipt_compatibility_cases"] == expected_receipts(), "receipt compatibility matrix mismatch")


def expected_transitions() -> list[dict[str, Any]]:
    return [{"from_state": old, "to_state": new, "expected": "ALLOWED" if (old, new) in ALLOWED_TRANSITIONS else "REJECTED_TRANSITION_INVALID"} for old, new in product(STATES, STATES)]


def validate_transitions(fixture: dict[str, Any]) -> None:
    ensure(fixture["transition_cases"] == expected_transitions(), "transition matrix mismatch")


def validate_adversarial(fixture: dict[str, Any]) -> None:
    expected = [
        {
            "check": name,
            "input": ADVERSARIAL_INPUTS[name],
            "expected_decision": independent_adversarial_decision(name, ADVERSARIAL_INPUTS[name]),
        }
        for name in ADVERSARIAL
    ]
    ensure(fixture["adversarial_cases"] == expected, "adversarial decision set mismatch")


SECTIONS = ("schema_profiles", "canonical_instances", "derived_identities", "pairwise_precedence_cases", "arm_replay_cases", "receipt_compatibility_cases", "transition_cases", "adversarial_cases", "assertions", "summary")


def validate_section_hashes(fixture: dict[str, Any]) -> None:
    for key in SECTIONS:
        ensure(fixture[f"{key}_fingerprint"] == section_fingerprint(key, fixture[key]), f"{key} section fingerprint mismatch")


def validate_root(fixture: dict[str, Any]) -> None:
    copy_root = copy.deepcopy(fixture)
    claimed = copy_root.pop("fixture_canonical_sha256")
    ensure(claimed == digest(copy_root), "fixture canonical hash mismatch")


def validate_fixture(fixture: dict[str, Any], run_mutations: bool = True) -> dict[str, Any]:
    ensure(fixture["fixture_interface"] == FIXTURE_INTERFACE, "fixture interface mismatch")
    ensure(fixture["environment"] == "SYNTHETIC_TEST", "fixture must be synthetic")
    ensure(fixture["authority_eligible"] is False and fixture["runtime_consumable"] is False, "fixture must be nonauthority")
    validate_section_hashes(fixture)
    validate_root(fixture)
    validate_profiles(fixture)
    by_name = validate_instances(fixture)
    validate_identities(fixture, by_name)
    validate_precedence(fixture)
    validate_replay(fixture)
    validate_receipts(fixture)
    validate_transitions(fixture)
    validate_adversarial(fixture)
    assertions = fixture["assertions"]
    for field in ("accepted_real_handoff_count", "armed_dispatch_count", "runtime_consumable_count", "external_effect_count", "provider_call_count", "raw_secret_count"):
        ensure(assertions[field] == 0, f"{field} must be zero")
    ensure(assertions["terminal_outcome"] == "NOT_EXECUTED", "terminal outcome mismatch")
    expected_summary = {"schema_profile_count": 16, "canonical_instance_count": 16, "derived_identity_count": 6, "pairwise_precedence_case_count": len(expected_pairwise()), "arm_replay_case_count": 4, "receipt_compatibility_case_count": 25, "transition_case_count": 100, "adversarial_case_count": 28}
    ensure(fixture["summary"] == expected_summary, "summary mismatch")
    return {"result": "PASS_NO_BLOCKER", **expected_summary, "negative_mutations_rejected": mutation_checks(fixture) if run_mutations else None, "fixture_canonical_sha256": fixture["fixture_canonical_sha256"], **assertions}


def resign_section(fixture: dict[str, Any], key: str) -> None:
    fixture[f"{key}_fingerprint"] = section_fingerprint(key, fixture[key])


def resign_root(fixture: dict[str, Any]) -> None:
    fixture.pop("fixture_canonical_sha256", None)
    fixture["fixture_canonical_sha256"] = digest(fixture)


def mutation_checks(base: dict[str, Any]) -> int:
    mutations: list[dict[str, Any]] = []
    for identity in sorted(base["derived_identities"]):
        item = copy.deepcopy(base); item["derived_identities"][identity] = "0" * 64; resign_section(item, "derived_identities"); resign_root(item); mutations.append(item)
    for index in range(len(base["canonical_instances"])):
        item = copy.deepcopy(base); row = item["canonical_instances"][index]; name = row["schema_name"]; fp_field = next(schema[2] for schema in SCHEMAS if schema[0] == name); row["object"][fp_field] = "0" * 64; resign_section(item, "canonical_instances"); resign_root(item); mutations.append(item)
    item = copy.deepcopy(base); item["pairwise_precedence_cases"][0]["expected_primary_reason"] = item["pairwise_precedence_cases"][0]["active_reasons"][0]; resign_section(item, "pairwise_precedence_cases"); resign_root(item); mutations.append(item)
    item = copy.deepcopy(base); exact = next(row for row in item["arm_replay_cases"] if row["relation"] == "EXACT_DUPLICATE"); exact["expected"]["physical_call_authorized"] = True; resign_section(item, "arm_replay_cases"); resign_root(item); mutations.append(item)
    item = copy.deepcopy(base); bad = next(row for row in item["receipt_compatibility_cases"] if row["receipt_kind"] == "TRANSPORT_ACK" and row["effect_status"] == "SUCCEEDED"); bad["expected"] = "APPLIED"; resign_section(item, "receipt_compatibility_cases"); resign_root(item); mutations.append(item)
    item = copy.deepcopy(base); bad = next(row for row in item["transition_cases"] if row["from_state"] == "SUCCEEDED" and row["to_state"] == "DISPATCHED"); bad["expected"] = "ALLOWED"; resign_section(item, "transition_cases"); resign_root(item); mutations.append(item)
    item = copy.deepcopy(base); item["adversarial_cases"][0]["expected_decision"] = "ACCEPT"; resign_section(item, "adversarial_cases"); resign_root(item); mutations.append(item)
    item = copy.deepcopy(base); item["authority_eligible"] = True; resign_root(item); mutations.append(item)
    item = copy.deepcopy(base); profile = item["schema_profiles"][0]; profile["fields"] = profile["fields"][:-1]; profile["schema_profile_fingerprint"] = h(PROOF_DOMAIN, "schema-profile", profile["schema_name"], profile["interface_version"], profile["fingerprint_field"], profile["fields"]); resign_section(item, "schema_profiles"); resign_root(item); mutations.append(item)
    rejected = 0
    for mutation in mutations:
        try:
            validate_fixture(mutation, run_mutations=False)
        except (ValueError, KeyError, TypeError):
            rejected += 1
    ensure(rejected == len(mutations), "one or more fully re-signed mutations were accepted")
    return rejected


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    try:
        result = validate_fixture(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"result": "BLOCK", "error": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
