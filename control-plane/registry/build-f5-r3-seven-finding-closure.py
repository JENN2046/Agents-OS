#!/usr/bin/env python3
"""Build the deterministic, non-authority F5 R3 seven-finding closure fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations, product
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path("control-plane/registry/examples/2026-07-17-agents-os-f5-r3-seven-finding-closure-v0.1.json")
FIXTURE_INTERFACE = "agents-os.f5-r3-seven-finding-closure-fixture.v0.1"
PROOF_DOMAIN = "agents-os.f5-r3-seven-finding-closure-proof.v0.1"
SAFE_INTEGER = 9007199254740991


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def h(domain: str, *values: Any) -> str:
    return digest([domain, *values])


def hx(label: str) -> str:
    return hashlib.sha256(("f5-r3:" + label).encode()).hexdigest()


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
    ("F5DeliveryReceiptDispositionV0_1R3", "agents-os.f5-delivery-receipt-disposition.v0.1-r3", "canonical_fingerprint", "interface_version source_id receipt_id receipt_fingerprint dedup_relation result primary_reason reason_codes event_created reconciliation_opened current_projection_advanced task_advancement_eligible observed_event_sequence canonical_fingerprint".split()),
    ("F5DeadLetterFactV0_1R1", "agents-os.f5-dead-letter-fact.v0.1-r1", "canonical_fingerprint", "interface_version dead_letter_id outbox_intent_ref outbox_intent_fingerprint last_claim_ref last_claim_fingerprint last_attempt_ref last_attempt_fingerprint reason effect_outcome reconciliation_required dead_lettered_at_utc_ms dead_letter_event_sequence canonical_fingerprint".split()),
    ("F5ReconciliationCaseV0_1R1", "agents-os.f5-reconciliation-case.v0.1-r1", "canonical_fingerprint", "interface_version reconciliation_id outbox_intent_ref outbox_intent_fingerprint attempt_ref attempt_fingerprint reason status resolution evidence_refs evidence_set_fingerprint owner_next_action opened_event_sequence last_updated_event_sequence canonical_fingerprint".split()),
    ("F5OutboxProjectionV0_1R1", "agents-os.f5-outbox-projection.v0.1-r1", "projection_fingerprint", "interface_version outbox_intent_ref outbox_intent_fingerprint projection_version last_event_sequence state current_claim_ref current_claim_fingerprint current_attempt_ref current_attempt_fingerprint current_reconciliation_ref current_reconciliation_fingerprint effect_outcome automatic_retry_eligible completion_blocking projection_fingerprint".split()),
    ("F5SyntheticDeliveryRecoveryWitnessV0_1R1", "agents-os.f5-synthetic-delivery-recovery-witness.v0.1-r1", "canonical_fingerprint", "interface_version witness_ref witness_namespace environment fingerprint_domain prospective_F4_handoff_requirement_ref prospective_F4_handoff_requirement_fingerprint vector_set_fingerprint authority_eligible runtime_consumable recovery_importable physical_effect_boundary terminal_outcome accepted_real_handoff_count armed_dispatch_count external_effect_count provider_call_count raw_secret_count canonical_fingerprint".split()),
]


ENUMS: dict[tuple[str, str], list[str]] = {
    ("F5OutboxIntentV0_1R1", "environment"): ["SYNTHETIC_TEST", "PRODUCTION"],
    ("F5EnqueueDispositionV0_1R1", "result"): ["ENQUEUED", "NOT_EXECUTABLE", "INDETERMINATE"],
    ("F5EnqueueDispositionV0_1R1", "primary_reason"): "ENQUEUED_NEW ENQUEUED_REPLAY SYNTHETIC_INPUT HANDOFF_UNAVAILABLE HANDOFF_INVALID HANDOFF_EXPIRED HANDOFF_ALREADY_CONSUMED INTEGRITY_FAILURE".split(),
    ("F5DispatcherClaimantAssessmentV0_1R1", "result"): ["CURRENT", "STALE", "INDETERMINATE"],
    ("F5DispatcherClaimantAssessmentV0_1R1", "environment"): ["SYNTHETIC_TEST", "PRODUCTION"],
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "observation_purpose"): ["CLAIM", "DISPATCH_ARM"],
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "fresh_F4_assessment_result"): ["CURRENT", "REJECTED", "INDETERMINATE"],
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "result"): ["CURRENT", "REJECTED", "INDETERMINATE"],
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "primary_reason"): "ALL_CURRENT AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED ASSESSMENT_UNAVAILABLE INTEGRITY_FAILURE".split(),
    ("F5OutboxClaimFactV0_1R1", "result"): ["CLAIMED", "NOT_EXECUTABLE", "INDETERMINATE"],
    ("F5OutboxClaimFactV0_1R1", "primary_reason"): "CLAIMED_NEW CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY SYNTHETIC_INPUT INTENT_NOT_PENDING CLAIM_ALREADY_ACTIVE DISPATCH_ALREADY_ARMED TERMINAL_ALREADY_RECORDED CLAIMANT_STALE CLAIMANT_UNAVAILABLE AUTHORITY_STALE AUTHORITY_UNAVAILABLE EXPIRED CAS_MISMATCH INTEGRITY_FAILURE".split(),
    ("F5OutboxLeaseFactV0_1R1", "result"): ["RENEWED", "REJECTED", "INDETERMINATE"],
    ("F5OutboxLeaseFactV0_1R1", "primary_reason"): "RENEWED CLAIM_STALE TOKEN_MISMATCH DISPATCH_ALREADY_ARMED EXPIRED CAS_MISMATCH INTEGRITY_FAILURE".split(),
    ("F5DispatchArmDispositionV0_1R2", "replay_relation"): ["NO_EXISTING_ARM", "EXACT_DUPLICATE", "CHANGED_BYTES_SAME_IDENTITY", "LOOKUP_INDETERMINATE"],
    ("F5DispatchArmDispositionV0_1R2", "result"): ["APPLIED", "REPLAYED", "REJECTED", "INDETERMINATE"],
    ("F5DispatchArmDispositionV0_1R2", "primary_reason"): "ARMED_FIRST_APPLY EXACT_DUPLICATE_REPLAY REQUEST_BYTES_CONFLICT ARM_LOOKUP_UNAVAILABLE SYNTHETIC_INPUT CLAIM_STALE TOKEN_MISMATCH TERMINAL_ALREADY_RECORDED AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED OBSERVATION_UNAVAILABLE CAS_MISMATCH INTEGRITY_FAILURE".split(),
    ("F5DeliveryAttemptFactV0_1R1", "outcome"): "PRE_EFFECT_NOT_EXECUTED DISPATCHED ACKED SUCCEEDED FAILED UNKNOWN".split(),
    ("F5DeliveryReceiptV0_1R1", "receipt_kind"): "TRANSPORT_ACK EFFECT_SUCCEEDED EFFECT_FAILED EFFECT_STATUS_UNKNOWN EFFECT_QUERY_RESULT".split(),
    ("F5DeliveryReceiptV0_1R1", "effect_status"): "ACKED_ONLY SUCCEEDED FAILED UNKNOWN NOT_EXECUTED".split(),
    ("F5DeliveryReceiptDispositionV0_1R3", "dedup_relation"): ["NEW", "EXACT_DUPLICATE", "CHANGED_BYTES_SAME_KEY", "LOOKUP_INDETERMINATE"],
    ("F5DeliveryReceiptDispositionV0_1R3", "result"): ["APPLIED", "HISTORY_ONLY", "REPLAYED", "REJECTED", "INDETERMINATE"],
    ("F5DeliveryReceiptDispositionV0_1R3", "primary_reason"): "APPLIED_CURRENT HISTORY_ONLY_EPOCH_STALE HISTORY_ONLY_FENCE_STALE HISTORY_ONLY_ATTEMPT_STALE EXACT_DUPLICATE_REPLAY RECEIPT_BYTES_CONFLICT RECEIPT_LOOKUP_UNAVAILABLE INTEGRITY_FAILURE SOURCE_ATTESTATION_INVALID ATTEMPT_OR_EFFECT_MISMATCH EXISTING_EFFECT_QUERY_INVALID RECEIPT_KIND_STATUS_MISMATCH TRANSITION_INVALID SOURCE_ATTESTATION_UNAVAILABLE".split(),
    ("F5DeadLetterFactV0_1R1", "reason"): "PRE_ARM_RETRY_EXHAUSTED NON_RETRYABLE_PRE_ARM_REJECTION AUTHORITY_REVOKED EXPIRED INTEGRITY_FAILURE RECEIPT_CONFLICT RECONCILIATION_REQUIRED".split(),
    ("F5DeadLetterFactV0_1R1", "effect_outcome"): "NOT_PROVEN SUCCEEDED FAILED UNKNOWN NOT_EXECUTED".split(),
    ("F5ReconciliationCaseV0_1R1", "reason"): "POST_ARM_CRASH RECEIPT_CONFLICT EFFECT_UNKNOWN LATE_TERMINAL_FACT DEAD_LETTER_REVIEW INTEGRITY_RECOVERY".split(),
    ("F5ReconciliationCaseV0_1R1", "status"): "OPEN QUERY_PENDING RESOLVED INDETERMINATE".split(),
    ("F5ReconciliationCaseV0_1R1", "resolution"): "NONE SUCCEEDED FAILED NOT_EXECUTED REMAINS_UNKNOWN".split(),
    ("F5ReconciliationCaseV0_1R1", "owner_next_action"): "QUERY_BY_IDEMPOTENCY_KEY AWAIT_AUTHENTICATED_RECEIPT HUMAN_REVIEW CLOSE_ACCOUNTING_ONLY".split(),
    ("F5OutboxProjectionV0_1R1", "state"): "PENDING CLAIMED DISPATCH_ARMED DISPATCHED ACKED SUCCEEDED FAILED UNKNOWN DEAD_LETTERED RECONCILED".split(),
    ("F5OutboxProjectionV0_1R1", "effect_outcome"): "NOT_PROVEN SUCCEEDED FAILED UNKNOWN NOT_EXECUTED".split(),
    ("F5SyntheticDeliveryRecoveryWitnessV0_1R1", "witness_namespace"): ["synthetic-f5-r3"],
    ("F5SyntheticDeliveryRecoveryWitnessV0_1R1", "environment"): ["SYNTHETIC_TEST"],
    ("F5SyntheticDeliveryRecoveryWitnessV0_1R1", "fingerprint_domain"): [PROOF_DOMAIN],
    ("F5SyntheticDeliveryRecoveryWitnessV0_1R1", "physical_effect_boundary"): ["NOT_EXECUTABLE"],
    ("F5SyntheticDeliveryRecoveryWitnessV0_1R1", "terminal_outcome"): ["NOT_EXECUTED"],
}

BOOL_FIELDS = {"completion_blocking", "authority_eligible", "event_created", "physical_call_authorized", "effect_may_have_occurred", "automatic_retry_eligible", "reconciliation_opened", "current_projection_advanced", "task_advancement_eligible", "reconciliation_required", "runtime_consumable", "recovery_importable"}
NULLABLE_KEYS = {
    ("F5EnqueueDispositionV0_1R1", "outbox_intent_ref"), ("F5EnqueueDispositionV0_1R1", "outbox_intent_fingerprint"),
    ("F5DispatchArmDispositionV0_1R2", "first_arm_ref"), ("F5DispatchArmDispositionV0_1R2", "first_arm_fingerprint"),
    ("F5DeliveryAttemptFactV0_1R1", "returned_at_utc_ms"),
    ("F5DeadLetterFactV0_1R1", "last_claim_ref"), ("F5DeadLetterFactV0_1R1", "last_claim_fingerprint"),
    ("F5DeadLetterFactV0_1R1", "last_attempt_ref"), ("F5DeadLetterFactV0_1R1", "last_attempt_fingerprint"),
    ("F5ReconciliationCaseV0_1R1", "attempt_ref"), ("F5ReconciliationCaseV0_1R1", "attempt_fingerprint"),
    ("F5OutboxProjectionV0_1R1", "current_claim_ref"), ("F5OutboxProjectionV0_1R1", "current_claim_fingerprint"),
    ("F5OutboxProjectionV0_1R1", "current_attempt_ref"), ("F5OutboxProjectionV0_1R1", "current_attempt_fingerprint"),
    ("F5OutboxProjectionV0_1R1", "current_reconciliation_ref"), ("F5OutboxProjectionV0_1R1", "current_reconciliation_fingerprint"),
}
SHA_ID_FIELDS = {"outbox_intent_id", "claim_id", "lease_fact_id", "dispatch_arm_request_id", "dispatch_arm_id", "attempt_id", "dead_letter_id", "reconciliation_id", "claim_fencing_token"}


def field_type(name: str, field: str, interface: str) -> str:
    if field == "interface_version":
        return "literal:" + interface
    if (name, field) in ENUMS:
        return "enum:" + "|".join(ENUMS[(name, field)])
    if field in BOOL_FIELDS:
        return "boolean"
    if field == "reason_codes":
        return "sorted_unique_closed_set"
    if field == "evidence_refs":
        return "sorted_unique_stable_refs"
    if (name, field) in NULLABLE_KEYS:
        if field == "returned_at_utc_ms":
            return "non_negative_safe_integer|null"
        return ("lowercase_sha256|null" if field.endswith("_fingerprint") else "stable_ref|null")
    if field.endswith("_fingerprint") or field in SHA_ID_FIELDS:
        return "lowercase_sha256"
    if field == "expected_previous_claim_epoch" or field.endswith(("_utc_ms", "_sequence", "_generation", "_count")):
        return "non_negative_safe_integer"
    if field.endswith(("_epoch", "_ordinal", "_revision", "_version")):
        return "positive_safe_integer"
    return "stable_ref"


def sample_value(name: str, field: str, type_name: str) -> Any:
    if type_name.startswith("literal:"):
        return type_name.split(":", 1)[1]
    if type_name.startswith("enum:"):
        return type_name.split(":", 1)[1].split("|")[0]
    if type_name == "boolean":
        return False
    if type_name in {"sorted_unique_closed_set", "sorted_unique_stable_refs"}:
        return []
    if type_name.endswith("|null"):
        return None
    if type_name == "lowercase_sha256":
        return hx(name + ":" + field)
    if type_name == "positive_safe_integer":
        return 1
    if type_name == "non_negative_safe_integer":
        return 0
    return "synthetic-f5-r3:" + field


OVERRIDES: dict[str, dict[str, Any]] = {
    "F5OutboxIntentV0_1R1": {"environment": "SYNTHETIC_TEST", "authority_eligible": False, "created_at_utc_ms": 1000, "start_authority_expires_at_utc_ms": 5000},
    "F5EnqueueDispositionV0_1R1": {"outbox_intent_ref": None, "outbox_intent_fingerprint": None, "result": "NOT_EXECUTABLE", "primary_reason": "SYNTHETIC_INPUT", "reason_codes": ["SYNTHETIC_INPUT"], "observed_at_utc_ms": 1000},
    "F5DispatcherClaimantAssessmentV0_1R1": {"result": "STALE", "environment": "SYNTHETIC_TEST", "authority_eligible": False, "owner_head_event_sequence": 10, "assessed_at_event_sequence": 10},
    "F5PhysicalBoundaryAuthorityObservationV0_1R1": {"observation_purpose": "CLAIM", "fresh_F4_assessment_result": "REJECTED", "result": "REJECTED", "primary_reason": "AUTHORITY_STALE", "reason_codes": ["AUTHORITY_STALE"], "observed_at_utc_ms": 1100, "observed_event_sequence": 11, "canonical_writer_head_event_sequence": 11},
    "F5OutboxClaimFactV0_1R1": {"claim_epoch": 1, "expected_previous_claim_epoch": 0, "lease_expires_at_utc_ms": 2000, "claimed_at_utc_ms": 1200, "result": "NOT_EXECUTABLE", "primary_reason": "SYNTHETIC_INPUT", "reason_codes": ["SYNTHETIC_INPUT"]},
    "F5OutboxLeaseFactV0_1R1": {"claim_epoch": 1, "previous_lease_expiry_utc_ms": 2000, "new_lease_expiry_utc_ms": 2500, "renewed_at_utc_ms": 1500, "result": "REJECTED", "primary_reason": "CLAIM_STALE", "reason_codes": ["CLAIM_STALE"]},
    "F5DispatchArmRequestV0_1R2": {"claim_epoch": 1, "attempt_ordinal": 1, "requested_at_utc_ms": 1600, "requested_event_sequence": 12},
    "F5DispatchArmDispositionV0_1R2": {"replay_relation": "NO_EXISTING_ARM", "first_arm_ref": None, "first_arm_fingerprint": None, "result": "REJECTED", "primary_reason": "SYNTHETIC_INPUT", "reason_codes": ["SYNTHETIC_INPUT"], "event_created": False, "physical_call_authorized": False},
    "F5DeliveryAttemptFactV0_1R1": {"attempt_ordinal": 1, "started_at_utc_ms": 1700, "returned_at_utc_ms": 1700, "outcome": "PRE_EFFECT_NOT_EXECUTED", "effect_may_have_occurred": False, "automatic_retry_eligible": False},
    "F5DeliveryReceiptV0_1R1": {"source_receipt_revision": 1, "execution_epoch": 1, "receipt_kind": "TRANSPORT_ACK", "effect_status": "ACKED_ONLY", "observed_at_utc_ms": 1700, "received_at_utc_ms": 1800},
    "F5DeliveryReceiptDispositionV0_1R3": {"dedup_relation": "NEW", "result": "REJECTED", "primary_reason": "SOURCE_ATTESTATION_INVALID", "reason_codes": ["SOURCE_ATTESTATION_INVALID"], "event_created": False, "reconciliation_opened": False, "current_projection_advanced": False, "task_advancement_eligible": False},
    "F5DeadLetterFactV0_1R1": {"last_claim_ref": None, "last_claim_fingerprint": None, "last_attempt_ref": None, "last_attempt_fingerprint": None, "reason": "INTEGRITY_FAILURE", "effect_outcome": "NOT_PROVEN", "reconciliation_required": True},
    "F5ReconciliationCaseV0_1R1": {"attempt_ref": None, "attempt_fingerprint": None, "reason": "INTEGRITY_RECOVERY", "status": "OPEN", "resolution": "NONE", "evidence_refs": [], "owner_next_action": "HUMAN_REVIEW", "opened_event_sequence": 1, "last_updated_event_sequence": 1},
    "F5OutboxProjectionV0_1R1": {"projection_version": 1, "state": "PENDING", "current_claim_ref": None, "current_claim_fingerprint": None, "current_attempt_ref": None, "current_attempt_fingerprint": None, "current_reconciliation_ref": None, "current_reconciliation_fingerprint": None, "effect_outcome": "NOT_PROVEN", "automatic_retry_eligible": False, "completion_blocking": True},
    "F5SyntheticDeliveryRecoveryWitnessV0_1R1": {"witness_ref": "synthetic-f5-r3:witness", "witness_namespace": "synthetic-f5-r3", "environment": "SYNTHETIC_TEST", "fingerprint_domain": PROOF_DOMAIN, "authority_eligible": False, "runtime_consumable": False, "recovery_importable": False, "physical_effect_boundary": "NOT_EXECUTABLE", "terminal_outcome": "NOT_EXECUTED", "accepted_real_handoff_count": 0, "armed_dispatch_count": 0, "external_effect_count": 0, "provider_call_count": 0, "raw_secret_count": 0},
}


def object_fingerprint(obj: dict[str, Any], fields: list[str], fp_field: str) -> str:
    return h(obj["interface_version"] + "-fingerprint", *[obj[field] for field in fields if field != fp_field])


def build_shapes_and_graph() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    objects: dict[str, dict[str, Any]] = {}
    meta = {name: (interface, fp_field, fields) for name, interface, fp_field, fields in SCHEMAS}
    for name, interface, fp_field, fields in SCHEMAS:
        types = [field_type(name, field, interface) for field in fields]
        profile = {"schema_name": name, "interface_version": interface, "fingerprint_field": fp_field, "fields": fields, "field_types": types}
        profile["schema_profile_fingerprint"] = h(PROOF_DOMAIN, "schema-profile", name, interface, fp_field, fields, types)
        profiles.append(profile)
        obj = {field: sample_value(name, field, typ) for field, typ in zip(fields, types) if field != fp_field}
        obj.update(OVERRIDES.get(name, {}))
        objects[name] = obj

    intent = objects["F5OutboxIntentV0_1R1"]
    intent["outbox_intent_id"] = h("agents-os.f5-outbox-intent-id.v0.1", intent["source_handoff_fingerprint"], intent["invocation_identity_fingerprint"], intent["effect_id"])
    intent["outbox_intent_ref"] = "outbox-intent:" + intent["outbox_intent_id"]
    intent["canonical_fingerprint"] = object_fingerprint(intent, meta["F5OutboxIntentV0_1R1"][2], meta["F5OutboxIntentV0_1R1"][1])

    claim = objects["F5OutboxClaimFactV0_1R1"]
    claim["outbox_intent_ref"] = intent["outbox_intent_ref"]
    claim["outbox_intent_fingerprint"] = intent["canonical_fingerprint"]
    claim["claim_id"] = h("agents-os.f5-outbox-claim-id.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"])
    claim["claim_ref"] = "outbox-claim:" + claim["claim_id"]
    claim["claim_fencing_token"] = h("agents-os.f5-outbox-claim-fence.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"], claim["claimant_assessment_fingerprint"])
    claim["canonical_fingerprint"] = object_fingerprint(claim, meta["F5OutboxClaimFactV0_1R1"][2], meta["F5OutboxClaimFactV0_1R1"][1])

    lease = objects["F5OutboxLeaseFactV0_1R1"]
    lease.update({"claim_ref": claim["claim_ref"], "claim_fingerprint": claim["canonical_fingerprint"], "claim_epoch": claim["claim_epoch"], "claim_fencing_token": claim["claim_fencing_token"]})

    request = objects["F5DispatchArmRequestV0_1R2"]
    request.update({"outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "invocation_identity_fingerprint": intent["invocation_identity_fingerprint"], "claim_ref": claim["claim_ref"], "claim_fingerprint": claim["canonical_fingerprint"], "claim_epoch": claim["claim_epoch"], "claim_fencing_token": claim["claim_fencing_token"], "idempotency_key": intent["effect_id"]})
    request["attempt_id"] = h("agents-os.f5-delivery-attempt-id.v0.1", request["outbox_intent_fingerprint"], request["attempt_ordinal"])
    request["dispatch_arm_request_id"] = h("agents-os.f5-dispatch-arm-request-id.v0.1", request["outbox_intent_fingerprint"], request["invocation_identity_fingerprint"], request["attempt_ordinal"])
    request["canonical_fingerprint"] = object_fingerprint(request, meta["F5DispatchArmRequestV0_1R2"][2], meta["F5DispatchArmRequestV0_1R2"][1])

    disposition = objects["F5DispatchArmDispositionV0_1R2"]
    disposition.update({"dispatch_arm_request_id": request["dispatch_arm_request_id"], "dispatch_arm_request_fingerprint": request["canonical_fingerprint"]})

    arm = objects["F5DispatchArmFactV0_1R2"]
    arm.update({"dispatch_arm_request_id": request["dispatch_arm_request_id"], "dispatch_arm_request_fingerprint": request["canonical_fingerprint"], "outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "claim_ref": claim["claim_ref"], "claim_fingerprint": claim["canonical_fingerprint"], "claim_epoch": claim["claim_epoch"], "claim_fencing_token": claim["claim_fencing_token"], "attempt_ordinal": request["attempt_ordinal"], "attempt_id": request["attempt_id"], "idempotency_key": intent["effect_id"], "physical_boundary_observation_ref": request["physical_boundary_observation_ref"], "physical_boundary_observation_fingerprint": request["physical_boundary_observation_fingerprint"], "armed_at_utc_ms": 1650})
    arm["dispatch_arm_id"] = h("agents-os.f5-dispatch-arm-id.v0.2", request["dispatch_arm_request_id"])
    arm["dispatch_arm_ref"] = "dispatch-arm:" + arm["dispatch_arm_id"]
    arm["canonical_fingerprint"] = object_fingerprint(arm, meta["F5DispatchArmFactV0_1R2"][2], meta["F5DispatchArmFactV0_1R2"][1])

    attempt = objects["F5DeliveryAttemptFactV0_1R1"]
    attempt.update({"attempt_id": request["attempt_id"], "attempt_ref": "delivery-attempt:" + request["attempt_id"], "dispatch_arm_ref": arm["dispatch_arm_ref"], "dispatch_arm_fingerprint": arm["canonical_fingerprint"], "outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "idempotency_key": intent["effect_id"]})
    attempt["canonical_fingerprint"] = object_fingerprint(attempt, meta["F5DeliveryAttemptFactV0_1R1"][2], meta["F5DeliveryAttemptFactV0_1R1"][1])

    receipt = objects["F5DeliveryReceiptV0_1R1"]
    receipt.update({"attempt_ref": attempt["attempt_ref"], "attempt_fingerprint": attempt["canonical_fingerprint"], "outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "effect_id": intent["effect_id"], "invocation_identity_fingerprint": intent["invocation_identity_fingerprint"], "execution_epoch": intent["execution_epoch"], "host_fence_generation": intent["host_fence_generation"], "effect_fence_generation": intent["effect_fence_generation"]})

    projection = objects["F5OutboxProjectionV0_1R1"]
    projection.update({"outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"]})
    dead = objects["F5DeadLetterFactV0_1R1"]
    dead.update({"outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"]})
    recon = objects["F5ReconciliationCaseV0_1R1"]
    recon.update({"outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"]})

    # Complete all remaining fingerprints after bindings are final.
    for name, obj in objects.items():
        interface, fp_field, fields = meta[name]
        obj[fp_field] = object_fingerprint(obj, fields, fp_field)

    graph_names = ["F5OutboxIntentV0_1R1", "F5OutboxClaimFactV0_1R1", "F5DispatchArmRequestV0_1R2", "F5DispatchArmFactV0_1R2"]
    graph_objects = {name: json.loads(json.dumps(objects[name])) for name in graph_names}
    graph = {
        "proof_mode": "ABSTRACT_NONOCCURRING_FORMULA_PROOF",
        "authority_eligible": False,
        "runtime_consumable": False,
        "occurrence_count": 0,
        "objects": graph_objects,
        "derived_identities": {
            "outbox_intent_id": intent["outbox_intent_id"],
            "claim_id": claim["claim_id"],
            "claim_fencing_token": claim["claim_fencing_token"],
            "attempt_id": request["attempt_id"],
            "dispatch_arm_request_id": request["dispatch_arm_request_id"],
            "dispatch_arm_id": arm["dispatch_arm_id"],
        },
    }
    shapes = [{"schema_name": name, "semantic_role": "NON_OCCURRING_SHAPE_EXAMPLE", "occurrence_count": 0, "object": objects[name]} for name, *_ in SCHEMAS]
    return profiles, shapes, graph


CLAIM_PRECEDENCE = "INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED DISPATCH_ALREADY_ARMED CLAIM_ALREADY_ACTIVE INTENT_NOT_PENDING CLAIMANT_STALE CLAIMANT_UNAVAILABLE AUTHORITY_STALE AUTHORITY_UNAVAILABLE EXPIRED CAS_MISMATCH CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY CLAIMED_NEW".split()
LEASE_PRECEDENCE = "INTEGRITY_FAILURE CLAIM_STALE TOKEN_MISMATCH DISPATCH_ALREADY_ARMED EXPIRED CAS_MISMATCH RENEWED".split()
ARM_PRECEDENCE = "INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED CLAIM_STALE TOKEN_MISMATCH AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED OBSERVATION_UNAVAILABLE CAS_MISMATCH ARMED_FIRST_APPLY".split()


def reduce_reasons(kind: str, raw_entries: list[dict[str, Any]]) -> dict[str, Any]:
    precedence = {"CLAIM": CLAIM_PRECEDENCE, "LEASE": LEASE_PRECEDENCE, "ARM": ARM_PRECEDENCE}[kind]
    active = {row["reason"] for row in raw_entries if row["is_true"]}
    primary = next(reason for reason in precedence if reason in active)
    if kind == "CLAIM":
        result = "INDETERMINATE" if primary in {"CLAIMANT_UNAVAILABLE", "AUTHORITY_UNAVAILABLE"} else "NOT_EXECUTABLE"
    elif kind == "LEASE":
        result = "REJECTED"
    else:
        result = "INDETERMINATE" if primary == "OBSERVATION_UNAVAILABLE" else "REJECTED"
    return {"result": result, "primary_reason": primary, "reason_codes": sorted(active)}


def precedence_trials() -> tuple[list[dict[str, Any]], int]:
    trials: list[dict[str, Any]] = []
    unordered = 0
    for kind, precedence, failures in (
        ("CLAIM", CLAIM_PRECEDENCE, CLAIM_PRECEDENCE[:-2]),
        ("LEASE", LEASE_PRECEDENCE, LEASE_PRECEDENCE[:-1]),
        ("ARM", ARM_PRECEDENCE, ARM_PRECEDENCE[:-1]),
    ):
        for left, right in combinations(failures, 2):
            unordered += 1
            case_id = f"{kind}_{left}__{right}"
            for order_index, ordered in enumerate(((left, right), (right, left)), 1):
                raw = [{"reason": reason, "is_true": True} for reason in ordered]
                trials.append({"unordered_case_id": case_id, "kind": kind, "ordering": order_index, "raw_conditions": raw, "derived": reduce_reasons(kind, raw)})
    return trials, unordered


def request_record(label: str, changed: bool = False) -> dict[str, Any]:
    payload = {"bound_invocation_identity_fingerprint": hx("arm-invocation"), "attempt_ordinal": 1, "requested_at_utc_ms": 1001 if changed else 1000}
    request_id = h("agents-os.f5-dispatch-arm-request-id.v0.1", hx("arm-intent"), payload["bound_invocation_identity_fingerprint"], payload["attempt_ordinal"])
    return {"request_id": request_id, "request_fingerprint": digest(payload), "request_canonical_utf8_hex": canonical_bytes(payload).hex(), "bound_invocation_identity_fingerprint": payload["bound_invocation_identity_fingerprint"]}


def derive_arm_case(raw: dict[str, Any]) -> dict[str, Any]:
    if not raw["lookup_reproducible"]:
        relation = "LOOKUP_INDETERMINATE"
    elif raw["stored_arm_state"] is None:
        relation = "NO_EXISTING_ARM"
    else:
        stored = raw["stored_arm_state"]
        submitted = raw["submitted_request"]
        exact = all(stored[k] == submitted[k] for k in ("request_id", "request_fingerprint", "request_canonical_utf8_hex", "bound_invocation_identity_fingerprint"))
        relation = "EXACT_DUPLICATE" if exact else "CHANGED_BYTES_SAME_IDENTITY"
    outputs = {
        "NO_EXISTING_ARM": ("APPLIED", "ARMED_FIRST_APPLY", 1, 1),
        "EXACT_DUPLICATE": ("REPLAYED", "EXACT_DUPLICATE_REPLAY", 0, 0),
        "CHANGED_BYTES_SAME_IDENTITY": ("REJECTED", "REQUEST_BYTES_CONFLICT", 0, 0),
        "LOOKUP_INDETERMINATE": ("INDETERMINATE", "ARM_LOOKUP_UNAVAILABLE", 0, 0),
    }
    result, reason, event_delta, call_delta = outputs[relation]
    if relation == "NO_EXISTING_ARM" and raw["first_apply_eligibility"] != "ELIGIBLE_PROOF_PRECONDITION":
        result, reason, event_delta, call_delta = "REJECTED", "FIRST_APPLY_NOT_ELIGIBLE", 0, 0
    returned_ref = raw["stored_arm_state"]["first_arm_ref"] if relation == "EXACT_DUPLICATE" else None
    returned_fp = raw["stored_arm_state"]["first_arm_fingerprint"] if relation == "EXACT_DUPLICATE" else None
    return {"replay_relation": relation, "result": result, "primary_reason": reason, "returned_first_arm_ref": returned_ref, "returned_first_arm_fingerprint": returned_fp, "modeled_event_delta": event_delta, "modeled_call_authorization_delta": call_delta, "total_event_count": raw["previous_event_count"] + event_delta, "total_call_authorization_count": raw["previous_call_authorization_count"] + call_delta}


def arm_cases() -> list[dict[str, Any]]:
    base = request_record("base")
    stored = {**base, "first_arm_ref": "synthetic-f5-r3:first-arm", "first_arm_fingerprint": hx("first-arm"), "committed_event_count": 1, "committed_call_authorization_count": 1}
    changed = request_record("changed", changed=True)
    raws = [
        {"lookup_reproducible": True, "bound_invocation_identity_fingerprint": base["bound_invocation_identity_fingerprint"], "stored_arm_state": None, "submitted_request": base, "first_apply_eligibility": "ELIGIBLE_PROOF_PRECONDITION", "previous_event_count": 0, "previous_call_authorization_count": 0},
        {"lookup_reproducible": True, "bound_invocation_identity_fingerprint": base["bound_invocation_identity_fingerprint"], "stored_arm_state": stored, "submitted_request": base, "first_apply_eligibility": "NOT_ELIGIBLE", "previous_event_count": 1, "previous_call_authorization_count": 1},
        {"lookup_reproducible": True, "bound_invocation_identity_fingerprint": base["bound_invocation_identity_fingerprint"], "stored_arm_state": stored, "submitted_request": changed, "first_apply_eligibility": "NOT_ELIGIBLE", "previous_event_count": 1, "previous_call_authorization_count": 1},
        {"lookup_reproducible": False, "bound_invocation_identity_fingerprint": base["bound_invocation_identity_fingerprint"], "stored_arm_state": stored, "submitted_request": base, "first_apply_eligibility": "NOT_ELIGIBLE", "previous_event_count": 1, "previous_call_authorization_count": 1},
    ]
    return [{"case_id": f"ARM_STATE_DERIVATION_{i + 1}", "proof_mode": "ABSTRACT_NONOCCURRING_REDUCER_TRIAL", "raw_input": raw, "derived": derive_arm_case(raw)} for i, raw in enumerate(raws)]


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


def compatibility(kind: str, status: str) -> str:
    return "COMPATIBLE" if status in RECEIPT_ALLOWED[kind] else "RECEIPT_KIND_STATUS_MISMATCH"


def receipt_relation(raw: dict[str, Any]) -> str:
    if not raw["lookup_reproducible"]:
        return "LOOKUP_INDETERMINATE"
    if raw["stored_receipt"] is None:
        return "NEW"
    return "EXACT_DUPLICATE" if raw["stored_receipt"]["receipt_fingerprint"] == raw["submitted_receipt"]["receipt_fingerprint"] else "CHANGED_BYTES_SAME_KEY"


def reduce_receipt(raw: dict[str, Any]) -> dict[str, Any]:
    relation = receipt_relation(raw)
    if relation == "LOOKUP_INDETERMINATE":
        return {"dedup_relation": relation, "compatibility": compatibility(raw["receipt_kind"], raw["effect_status"]), "result": "INDETERMINATE", "primary_reason": "RECEIPT_LOOKUP_UNAVAILABLE", "reason_codes": ["RECEIPT_LOOKUP_UNAVAILABLE"], "event_created": False, "reconciliation_opened": False, "current_projection_advanced": False, "task_advancement_eligible": False}
    if relation == "EXACT_DUPLICATE":
        return {"dedup_relation": relation, "compatibility": compatibility(raw["receipt_kind"], raw["effect_status"]), "result": "REPLAYED", "primary_reason": "EXACT_DUPLICATE_REPLAY", "reason_codes": [], "event_created": False, "reconciliation_opened": False, "current_projection_advanced": False, "task_advancement_eligible": False}
    if relation == "CHANGED_BYTES_SAME_KEY":
        return {"dedup_relation": relation, "compatibility": compatibility(raw["receipt_kind"], raw["effect_status"]), "result": "REJECTED", "primary_reason": "RECEIPT_BYTES_CONFLICT", "reason_codes": ["RECEIPT_BYTES_CONFLICT"], "event_created": False, "reconciliation_opened": True, "current_projection_advanced": False, "task_advancement_eligible": False}
    comp = compatibility(raw["receipt_kind"], raw["effect_status"])
    reasons: list[str] = []
    if not raw["integrity_valid"]: reasons.append("INTEGRITY_FAILURE")
    if raw["source_attestation_status"] == "INVALID": reasons.append("SOURCE_ATTESTATION_INVALID")
    if not raw["attempt_effect_identity_match"]: reasons.append("ATTEMPT_OR_EFFECT_MISMATCH")
    if raw["receipt_kind"] == "EFFECT_QUERY_RESULT" and not raw["existing_effect_query_authenticated"]: reasons.append("EXISTING_EFFECT_QUERY_INVALID")
    if comp != "COMPATIBLE": reasons.append("RECEIPT_KIND_STATUS_MISMATCH")
    if (raw["from_state"], raw["to_state"]) not in ALLOWED_TRANSITIONS: reasons.append("TRANSITION_INVALID")
    if raw["source_attestation_status"] == "UNAVAILABLE": reasons.append("SOURCE_ATTESTATION_UNAVAILABLE")
    if not raw["epoch_current"]: reasons.append("EPOCH_STALE")
    if not raw["fences_current"]: reasons.append("FENCE_STALE")
    if not raw["attempt_current"]: reasons.append("ATTEMPT_STALE")
    precedence = "INTEGRITY_FAILURE SOURCE_ATTESTATION_INVALID ATTEMPT_OR_EFFECT_MISMATCH EXISTING_EFFECT_QUERY_INVALID RECEIPT_KIND_STATUS_MISMATCH TRANSITION_INVALID SOURCE_ATTESTATION_UNAVAILABLE EPOCH_STALE FENCE_STALE ATTEMPT_STALE".split()
    primary = next((reason for reason in precedence if reason in reasons), "APPLIED_CURRENT")
    if primary == "APPLIED_CURRENT": result = "APPLIED"
    elif primary == "SOURCE_ATTESTATION_UNAVAILABLE": result = "INDETERMINATE"
    elif primary in {"EPOCH_STALE", "FENCE_STALE", "ATTEMPT_STALE"}: result = "HISTORY_ONLY"
    else: result = "REJECTED"
    primary_out = "HISTORY_ONLY_" + primary if result == "HISTORY_ONLY" else primary
    return {"dedup_relation": relation, "compatibility": comp, "result": result, "primary_reason": primary_out, "reason_codes": sorted(reasons), "event_created": result in {"APPLIED", "HISTORY_ONLY"}, "reconciliation_opened": False, "current_projection_advanced": result == "APPLIED", "task_advancement_eligible": False}


def base_receipt_raw() -> dict[str, Any]:
    return {"lookup_reproducible": True, "stored_receipt": None, "submitted_receipt": {"source_id": "synthetic-f5-r3:receipt-source", "receipt_id": "synthetic-f5-r3:receipt-1", "receipt_fingerprint": hx("submitted-receipt")}, "receipt_kind": "EFFECT_SUCCEEDED", "effect_status": "SUCCEEDED", "integrity_valid": True, "source_attestation_status": "VALID", "attempt_effect_identity_match": True, "existing_effect_query_authenticated": True, "epoch_current": True, "fences_current": True, "attempt_current": True, "from_state": "DISPATCHED", "to_state": "SUCCEEDED"}


def receipt_currentness_cases() -> list[dict[str, Any]]:
    cases: list[tuple[str, dict[str, Any]]] = []
    cases.append(("NEW_APPLIED_CURRENT", base_receipt_raw()))
    for name, changes in [
        ("NEW_HISTORY_EPOCH_STALE", {"epoch_current": False}),
        ("NEW_REJECT_SOURCE_INVALID", {"source_attestation_status": "INVALID"}),
        ("NEW_INDETERMINATE_SOURCE_UNAVAILABLE", {"source_attestation_status": "UNAVAILABLE"}),
        ("NEW_REJECT_COMPATIBILITY", {"receipt_kind": "TRANSPORT_ACK", "effect_status": "SUCCEEDED"}),
        ("NEW_REJECT_TRANSITION", {"from_state": "SUCCEEDED", "to_state": "DISPATCHED"}),
        ("NEW_REJECT_UNAUTHENTICATED_QUERY", {"receipt_kind": "EFFECT_QUERY_RESULT", "effect_status": "NOT_EXECUTED", "existing_effect_query_authenticated": False}),
        ("EXACT_DUPLICATE", {"stored_receipt": {"source_id": "synthetic-f5-r3:receipt-source", "receipt_id": "synthetic-f5-r3:receipt-1", "receipt_fingerprint": hx("submitted-receipt")}}),
        ("CHANGED_BYTES_SAME_KEY", {"stored_receipt": {"source_id": "synthetic-f5-r3:receipt-source", "receipt_id": "synthetic-f5-r3:receipt-1", "receipt_fingerprint": hx("different-receipt")}}),
        ("LOOKUP_INDETERMINATE", {"lookup_reproducible": False}),
    ]:
        raw = base_receipt_raw(); raw.update(changes); cases.append((name, raw))
    return [{"case_id": name, "raw_input": raw, "derived": reduce_receipt(raw)} for name, raw in cases]


ADVERSARIAL_CASES = [
    {"check": "fully_resigned_float_time", "expected_decision": "REJECT_SCHEMA_VALUE"},
    {"check": "fully_resigned_unknown_enum", "expected_decision": "REJECT_SCHEMA_VALUE"},
    {"check": "fully_resigned_non_NFC_ref", "expected_decision": "REJECT_SCHEMA_VALUE"},
    {"check": "fully_resigned_unknown_root_or_object_field", "expected_decision": "REJECT_CLOSED_INVENTORY"},
    {"check": "compatibility_without_currentness", "expected_decision": "COMPATIBLE_ONLY_NOT_APPLIED"},
    {"check": "caller_supplied_arm_relation", "expected_decision": "REJECT_RELATION_AS_INPUT"},
    {"check": "order_dependent_precedence", "expected_decision": "REJECT_ORDER_DEPENDENCE"},
    {"check": "synthetic_nonauthority_claim_or_arm", "expected_decision": "REJECT_ZERO_OCCURRENCE"},
    {"check": "coherent_graph_with_formula_wrong_ID", "expected_decision": "REJECT_ID_FORMULA"},
]


SECTIONS = ("schema_profiles", "schema_shape_examples", "synthetic_nonauthority_scenario", "identity_formula_graph", "precedence_ordering_trials", "arm_state_derivation_cases", "receipt_compatibility_cases", "receipt_currentness_cases", "transition_cases", "adversarial_cases", "assertions", "summary")


def section_fingerprint(name: str, value: Any) -> str:
    return h(PROOF_DOMAIN, name, value)


def build_fixture() -> dict[str, Any]:
    profiles, shapes, graph = build_shapes_and_graph()
    trials, unordered = precedence_trials()
    arms = arm_cases()
    compatibility_cases = [{"receipt_kind": kind, "effect_status": status, "derived_compatibility": compatibility(kind, status)} for kind, status in product(RECEIPT_KINDS, EFFECT_STATUSES)]
    receipts = receipt_currentness_cases()
    transitions = [{"from_state": old, "to_state": new, "derived": "ALLOWED" if (old, new) in ALLOWED_TRANSITIONS else "REJECTED_TRANSITION_INVALID"} for old, new in product(STATES, STATES)]
    fixture: dict[str, Any] = {
        "fixture_interface": FIXTURE_INTERFACE,
        "environment": "SYNTHETIC_TEST",
        "authority_eligible": False,
        "runtime_consumable": False,
        "schema_profiles": profiles,
        "schema_shape_examples": shapes,
        "synthetic_nonauthority_scenario": {"raw_input": {"environment": "SYNTHETIC_TEST", "authority_eligible": False}, "derived": {"enqueue_result": "NOT_EXECUTABLE", "enqueue_primary_reason": "SYNTHETIC_INPUT", "claim_result": "NOT_EXECUTABLE", "claim_primary_reason": "SYNTHETIC_INPUT", "arm_result": "REJECTED", "arm_primary_reason": "SYNTHETIC_INPUT", "claim_event_created": False, "arm_event_created": False, "physical_call_authorized": False}},
        "identity_formula_graph": graph,
        "precedence_ordering_trials": trials,
        "arm_state_derivation_cases": arms,
        "receipt_compatibility_cases": compatibility_cases,
        "receipt_currentness_cases": receipts,
        "transition_cases": transitions,
        "adversarial_cases": ADVERSARIAL_CASES,
        "assertions": {"accepted_real_handoff_count": 0, "claim_event_count": 0, "armed_dispatch_count": 0, "runtime_consumable_count": 0, "external_effect_count": 0, "provider_call_count": 0, "raw_secret_count": 0, "terminal_outcome": "NOT_EXECUTED"},
        "summary": {"schema_profile_count": len(profiles), "schema_shape_example_count": len(shapes), "identity_formula_count": 6, "precedence_unordered_pair_count": unordered, "precedence_ordering_trial_count": len(trials), "arm_state_derivation_case_count": len(arms), "receipt_compatibility_case_count": len(compatibility_cases), "receipt_currentness_case_count": len(receipts), "transition_state_count": len(STATES), "transition_case_count": len(transitions), "adversarial_case_count": len(ADVERSARIAL_CASES)},
    }
    for key in SECTIONS:
        fixture[key + "_fingerprint"] = section_fingerprint(key, fixture[key])
    fixture["fixture_canonical_sha256"] = digest(fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_fixture(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
