#!/usr/bin/env python3
"""Build the F5 R2 full-effective synthetic, zero-effect proof fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations, product
from pathlib import Path
from typing import Any


FIXTURE_INTERFACE = "agents-os.f5-r2-full-effective-fixture.v0.1"
PROOF_DOMAIN = "agents-os.f5-r2-full-effective-proof.v0.1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def h(domain: str, *values: Any) -> str:
    return digest([domain, *values])


def hx(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


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
RECEIPT_ALLOWED = {
    "TRANSPORT_ACK": {"ACKED_ONLY"},
    "EFFECT_SUCCEEDED": {"SUCCEEDED"},
    "EFFECT_FAILED": {"FAILED"},
    "EFFECT_STATUS_UNKNOWN": {"UNKNOWN"},
    "EFFECT_QUERY_RESULT": {"SUCCEEDED", "FAILED", "UNKNOWN", "NOT_EXECUTED"},
}

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


def schema_profiles() -> list[dict[str, Any]]:
    profiles = []
    for name, interface, fp_field, fields in SCHEMAS:
        row = {"schema_name": name, "interface_version": interface, "fingerprint_field": fp_field, "fields": fields}
        row["schema_profile_fingerprint"] = h(PROOF_DOMAIN, "schema-profile", name, interface, fp_field, fields)
        profiles.append(row)
    return profiles


def sample_value(field: str) -> Any:
    if field in {"reason_codes", "evidence_refs"}:
        return []
    if field.endswith("_fingerprint") or field.endswith("_sha256") or field.endswith("_id") and field not in {"effect_id", "source_id", "receipt_id", "owner_host_id", "dispatcher_actor_id", "dispatcher_principal_id"}:
        return hx(field)
    if field.endswith("_ref") or field.endswith("_id") or field in {"idempotency_key", "claim_fencing_token"}:
        return f"synthetic-f5-r2:{field}"
    if field.endswith("_count") or field.endswith("_generation") or field.endswith("_sequence"):
        return 0
    if field.endswith("_epoch") or field.endswith("_ordinal") or field.endswith("_revision") or field.endswith("_version"):
        return 1
    if field.endswith("_utc_ms"):
        return 1000
    if field in {"authority_eligible", "runtime_consumable", "recovery_importable", "automatic_retry_eligible", "event_created", "physical_call_authorized", "current_projection_advanced", "task_advancement_eligible"}:
        return False
    if field in {"completion_blocking", "effect_may_have_occurred", "reconciliation_required"}:
        return True
    return f"SYNTHETIC_{field.upper()}"


OVERRIDES: dict[str, dict[str, Any]] = {
    "F5OutboxIntentV0_1R1": {"environment": "SYNTHETIC_TEST", "authority_eligible": False, "start_authority_expires_at_utc_ms": 2000},
    "F5EnqueueDispositionV0_1R1": {"result": "NOT_EXECUTABLE", "primary_reason": "SYNTHETIC_INPUT", "reason_codes": ["SYNTHETIC_INPUT"]},
    "F5DispatcherClaimantAssessmentV0_1R1": {"result": "CURRENT", "environment": "SYNTHETIC_TEST", "authority_eligible": False},
    "F5PhysicalBoundaryAuthorityObservationV0_1R1": {"observation_purpose": "CLAIM", "fresh_F4_assessment_result": "CURRENT", "result": "CURRENT", "primary_reason": "ALL_CURRENT", "reason_codes": []},
    "F5OutboxClaimFactV0_1R1": {"result": "CLAIMED", "primary_reason": "CLAIMED_NEW", "reason_codes": []},
    "F5OutboxLeaseFactV0_1R1": {"result": "RENEWED", "primary_reason": "RENEWED", "reason_codes": []},
    "F5DispatchArmDispositionV0_1R2": {"replay_relation": "NO_EXISTING_ARM", "result": "APPLIED", "primary_reason": "ARMED_FIRST_APPLY", "reason_codes": [], "event_created": True, "physical_call_authorized": True},
    "F5DeliveryAttemptFactV0_1R1": {"outcome": "PRE_EFFECT_NOT_EXECUTED", "effect_may_have_occurred": False, "automatic_retry_eligible": False},
    "F5DeliveryReceiptV0_1R1": {"receipt_kind": "TRANSPORT_ACK", "effect_status": "ACKED_ONLY"},
    "F5DeliveryReceiptDispositionV0_1R2": {"dedup_relation": "NEW", "result": "APPLIED", "primary_reason": "APPLIED_CURRENT", "reason_codes": [], "event_created": True, "reconciliation_opened": False, "current_projection_advanced": True, "task_advancement_eligible": False},
    "F5DeadLetterFactV0_1R1": {"reason": "INTEGRITY_FAILURE", "effect_outcome": "NOT_PROVEN", "reconciliation_required": True},
    "F5ReconciliationCaseV0_1R1": {"reason": "INTEGRITY_RECOVERY", "status": "OPEN", "resolution": "NONE", "owner_next_action": "HUMAN_REVIEW", "evidence_refs": []},
    "F5OutboxProjectionV0_1R1": {"state": "PENDING", "effect_outcome": "NOT_PROVEN", "automatic_retry_eligible": False, "completion_blocking": True},
    "F5SyntheticDeliveryRecoveryWitnessV0_1R1": {"witness_ref": "synthetic-f5-r2:witness", "witness_namespace": "synthetic-f5-r2", "environment": "SYNTHETIC_TEST", "fingerprint_domain": PROOF_DOMAIN, "authority_eligible": False, "runtime_consumable": False, "recovery_importable": False, "physical_effect_boundary": "NOT_EXECUTABLE", "terminal_outcome": "NOT_EXECUTED", "accepted_real_handoff_count": 0, "armed_dispatch_count": 0, "external_effect_count": 0, "provider_call_count": 0, "raw_secret_count": 0},
}


def object_fingerprint(obj: dict[str, Any], fields: list[str], fp_field: str) -> str:
    values = [obj[field] for field in fields if field != fp_field]
    return h(obj["interface_version"] + "-fingerprint", *values)


def build_instances() -> tuple[list[dict[str, Any]], dict[str, str]]:
    by_name: dict[str, dict[str, Any]] = {}
    fields_by_name = {name: (interface, fp_field, fields) for name, interface, fp_field, fields in SCHEMAS}
    for name, interface, fp_field, fields in SCHEMAS:
        obj = {field: sample_value(field) for field in fields if field != fp_field}
        obj["interface_version"] = interface
        obj.update(OVERRIDES.get(name, {}))
        by_name[name] = obj

    intent = by_name["F5OutboxIntentV0_1R1"]
    intent["outbox_intent_id"] = h("agents-os.f5-outbox-intent-id.v0.1", intent["source_handoff_fingerprint"], intent["invocation_identity_fingerprint"], intent["effect_id"])
    intent["outbox_intent_ref"] = "outbox-intent:" + intent["outbox_intent_id"]
    intent["canonical_fingerprint"] = object_fingerprint(intent, fields_by_name["F5OutboxIntentV0_1R1"][2], "canonical_fingerprint")

    claim = by_name["F5OutboxClaimFactV0_1R1"]
    claim["outbox_intent_ref"] = intent["outbox_intent_ref"]
    claim["outbox_intent_fingerprint"] = intent["canonical_fingerprint"]
    claim["claim_id"] = h("agents-os.f5-outbox-claim-id.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"])
    claim["claim_ref"] = "outbox-claim:" + claim["claim_id"]
    claim["claim_fencing_token"] = h("agents-os.f5-outbox-claim-fence.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"], claim["claimant_assessment_fingerprint"])
    claim["canonical_fingerprint"] = object_fingerprint(claim, fields_by_name["F5OutboxClaimFactV0_1R1"][2], "canonical_fingerprint")

    request = by_name["F5DispatchArmRequestV0_1R2"]
    request.update({"outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "invocation_identity_fingerprint": intent["invocation_identity_fingerprint"], "claim_ref": claim["claim_ref"], "claim_fingerprint": claim["canonical_fingerprint"], "claim_epoch": claim["claim_epoch"], "claim_fencing_token": claim["claim_fencing_token"], "idempotency_key": intent["effect_id"]})
    request["attempt_id"] = h("agents-os.f5-delivery-attempt-id.v0.1", request["outbox_intent_fingerprint"], request["attempt_ordinal"])
    request["dispatch_arm_request_id"] = h("agents-os.f5-dispatch-arm-request-id.v0.1", request["outbox_intent_fingerprint"], request["invocation_identity_fingerprint"], request["attempt_ordinal"])
    request["canonical_fingerprint"] = object_fingerprint(request, fields_by_name["F5DispatchArmRequestV0_1R2"][2], "canonical_fingerprint")

    disposition = by_name["F5DispatchArmDispositionV0_1R2"]
    disposition.update({"dispatch_arm_request_id": request["dispatch_arm_request_id"], "dispatch_arm_request_fingerprint": request["canonical_fingerprint"]})

    arm = by_name["F5DispatchArmFactV0_1R2"]
    arm.update({"dispatch_arm_request_id": request["dispatch_arm_request_id"], "dispatch_arm_request_fingerprint": request["canonical_fingerprint"], "outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "claim_ref": claim["claim_ref"], "claim_fingerprint": claim["canonical_fingerprint"], "claim_epoch": claim["claim_epoch"], "claim_fencing_token": claim["claim_fencing_token"], "attempt_ordinal": request["attempt_ordinal"], "attempt_id": request["attempt_id"], "idempotency_key": intent["effect_id"], "physical_boundary_observation_ref": request["physical_boundary_observation_ref"], "physical_boundary_observation_fingerprint": request["physical_boundary_observation_fingerprint"]})
    arm["dispatch_arm_id"] = h("agents-os.f5-dispatch-arm-id.v0.2", request["dispatch_arm_request_id"])
    arm["dispatch_arm_ref"] = "dispatch-arm:" + arm["dispatch_arm_id"]
    arm["canonical_fingerprint"] = object_fingerprint(arm, fields_by_name["F5DispatchArmFactV0_1R2"][2], "canonical_fingerprint")
    disposition["first_arm_ref"] = arm["dispatch_arm_ref"]
    disposition["first_arm_fingerprint"] = arm["canonical_fingerprint"]

    for name, obj in by_name.items():
        interface, fp_field, fields = fields_by_name[name]
        if fp_field not in obj:
            obj[fp_field] = object_fingerprint(obj, fields, fp_field)

    identities = {
        "outbox_intent_id": intent["outbox_intent_id"],
        "claim_id": claim["claim_id"],
        "claim_fencing_token": claim["claim_fencing_token"],
        "attempt_id": request["attempt_id"],
        "dispatch_arm_request_id": request["dispatch_arm_request_id"],
        "dispatch_arm_id": arm["dispatch_arm_id"],
    }
    return [{"schema_name": name, "object": by_name[name]} for name, *_ in SCHEMAS], identities


def pairwise_cases(kind: str, precedence: list[str]) -> list[dict[str, Any]]:
    failures = precedence[:-2] if kind == "claim" else precedence[:-1]
    cases = []
    for left, right in combinations(failures, 2):
        cases.append({"case_id": f"{kind.upper()}_{left}__{right}", "kind": kind, "active_reasons": [right, left], "expected_primary_reason": left, "expected_reason_codes": sorted([left, right])})
    return cases


def arm_replay_cases() -> list[dict[str, Any]]:
    outputs = {
        "NO_EXISTING_ARM": ("APPLIED", "ARMED_FIRST_APPLY", True, True),
        "EXACT_DUPLICATE": ("REPLAYED", "EXACT_DUPLICATE_REPLAY", False, False),
        "CHANGED_BYTES_SAME_IDENTITY": ("REJECTED", "REQUEST_BYTES_CONFLICT", False, False),
        "LOOKUP_INDETERMINATE": ("INDETERMINATE", "ARM_LOOKUP_UNAVAILABLE", False, False),
    }
    return [{"relation": relation, "expected": {"result": values[0], "primary_reason": values[1], "event_created": values[2], "physical_call_authorized": values[3]}} for relation, values in outputs.items()]


def receipt_matrix() -> list[dict[str, Any]]:
    return [{"receipt_kind": kind, "effect_status": status, "expected": "APPLIED" if status in RECEIPT_ALLOWED[kind] else "REJECTED_RECEIPT_KIND_STATUS_MISMATCH"} for kind, status in product(RECEIPT_KINDS, EFFECT_STATUSES)]


def transition_matrix() -> list[dict[str, Any]]:
    return [{"from_state": old, "to_state": new, "expected": "ALLOWED" if (old, new) in ALLOWED_TRANSITIONS else "REJECTED_TRANSITION_INVALID"} for old, new in product(STATES, STATES)]


def section_fingerprint(name: str, value: Any) -> str:
    return h(PROOF_DOMAIN, name, value)


def build_fixture() -> dict[str, Any]:
    profiles = schema_profiles()
    instances, identities = build_instances()
    precedence = pairwise_cases("claim", CLAIM_PRECEDENCE) + pairwise_cases("lease", LEASE_PRECEDENCE) + pairwise_cases("arm", ARM_PRECEDENCE)
    replay = arm_replay_cases()
    receipts = receipt_matrix()
    transitions = transition_matrix()
    adversarial = [{"check": name, "input": ADVERSARIAL_INPUTS[name], "expected_decision": decision} for name, decision in ADVERSARIAL.items()]
    fixture: dict[str, Any] = {
        "fixture_interface": FIXTURE_INTERFACE,
        "environment": "SYNTHETIC_TEST",
        "authority_eligible": False,
        "runtime_consumable": False,
        "schema_profiles": profiles,
        "canonical_instances": instances,
        "derived_identities": identities,
        "pairwise_precedence_cases": precedence,
        "arm_replay_cases": replay,
        "receipt_compatibility_cases": receipts,
        "transition_cases": transitions,
        "adversarial_cases": adversarial,
        "assertions": {"accepted_real_handoff_count": 0, "armed_dispatch_count": 0, "runtime_consumable_count": 0, "external_effect_count": 0, "provider_call_count": 0, "raw_secret_count": 0, "terminal_outcome": "NOT_EXECUTED"},
        "summary": {"schema_profile_count": len(profiles), "canonical_instance_count": len(instances), "derived_identity_count": len(identities), "pairwise_precedence_case_count": len(precedence), "arm_replay_case_count": len(replay), "receipt_compatibility_case_count": len(receipts), "transition_case_count": len(transitions), "adversarial_case_count": len(adversarial)},
    }
    for key in ("schema_profiles", "canonical_instances", "derived_identities", "pairwise_precedence_cases", "arm_replay_cases", "receipt_compatibility_cases", "transition_cases", "adversarial_cases", "assertions", "summary"):
        fixture[f"{key}_fingerprint"] = section_fingerprint(key, fixture[key])
    fixture["fixture_canonical_sha256"] = digest(fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("control-plane/registry/examples/2026-07-17-agents-os-f5-r2-full-effective-delivery-recovery-v0.1.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_fixture(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
