#!/usr/bin/env python3
"""Independently validate the fixed F5 R3 seven-finding closure fixture."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unicodedata
from itertools import combinations, product
from pathlib import Path
from typing import Any


DEFAULT_FIXTURE = Path("control-plane/registry/examples/2026-07-17-agents-os-f5-r3-seven-finding-closure-v0.1.json")
FIXTURE_INTERFACE = "agents-os.f5-r3-seven-finding-closure-fixture.v0.1"
PROOF_DOMAIN = "agents-os.f5-r3-seven-finding-closure-proof.v0.1"
SAFE_INTEGER = 9007199254740991
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
HEX_RE = re.compile(r"^(?:[0-9a-f]{2})+$")


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def parse_json_strict(text: str) -> Any:
    return json.loads(text, object_pairs_hook=reject_duplicate_pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("non-finite JSON number")))


def validate_json_value(value: Any, path: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        ensure(-SAFE_INTEGER <= value <= SAFE_INTEGER, f"unsafe integer at {path}")
        return
    ensure(not isinstance(value, float), f"float forbidden at {path}")
    if isinstance(value, str):
        ensure(unicodedata.normalize("NFC", value) == value, f"non-NFC string at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            ensure(isinstance(key, str) and unicodedata.normalize("NFC", key) == key, f"invalid key at {path}")
            validate_json_value(item, f"{path}.{key}")
        return
    raise ValueError(f"unsupported JSON type at {path}")


def canonical_bytes(value: Any) -> bytes:
    validate_json_value(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def raw_canonical_bytes(value: Any) -> bytes:
    """Attacker re-sign helper; deliberately does not enforce R3 value rules."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_digest(value: Any) -> str:
    return hashlib.sha256(raw_canonical_bytes(value)).hexdigest()


def h(domain: str, *values: Any) -> str:
    return digest([domain, *values])


def raw_h(domain: str, *values: Any) -> str:
    return raw_digest([domain, *values])


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
    ("F5EnqueueDispositionV0_1R1", "result"): "ENQUEUED NOT_EXECUTABLE INDETERMINATE".split(),
    ("F5EnqueueDispositionV0_1R1", "primary_reason"): "ENQUEUED_NEW ENQUEUED_REPLAY SYNTHETIC_INPUT HANDOFF_UNAVAILABLE HANDOFF_INVALID HANDOFF_EXPIRED HANDOFF_ALREADY_CONSUMED INTEGRITY_FAILURE".split(),
    ("F5DispatcherClaimantAssessmentV0_1R1", "result"): "CURRENT STALE INDETERMINATE".split(),
    ("F5DispatcherClaimantAssessmentV0_1R1", "environment"): "SYNTHETIC_TEST PRODUCTION".split(),
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "observation_purpose"): "CLAIM DISPATCH_ARM".split(),
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "fresh_F4_assessment_result"): "CURRENT REJECTED INDETERMINATE".split(),
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "result"): "CURRENT REJECTED INDETERMINATE".split(),
    ("F5PhysicalBoundaryAuthorityObservationV0_1R1", "primary_reason"): "ALL_CURRENT AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED ASSESSMENT_UNAVAILABLE INTEGRITY_FAILURE".split(),
    ("F5OutboxClaimFactV0_1R1", "result"): "CLAIMED NOT_EXECUTABLE INDETERMINATE".split(),
    ("F5OutboxClaimFactV0_1R1", "primary_reason"): "CLAIMED_NEW CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY SYNTHETIC_INPUT INTENT_NOT_PENDING CLAIM_ALREADY_ACTIVE DISPATCH_ALREADY_ARMED TERMINAL_ALREADY_RECORDED CLAIMANT_STALE CLAIMANT_UNAVAILABLE AUTHORITY_STALE AUTHORITY_UNAVAILABLE EXPIRED CAS_MISMATCH INTEGRITY_FAILURE".split(),
    ("F5OutboxLeaseFactV0_1R1", "result"): "RENEWED REJECTED INDETERMINATE".split(),
    ("F5OutboxLeaseFactV0_1R1", "primary_reason"): "RENEWED CLAIM_STALE TOKEN_MISMATCH DISPATCH_ALREADY_ARMED EXPIRED CAS_MISMATCH INTEGRITY_FAILURE".split(),
    ("F5DispatchArmDispositionV0_1R2", "replay_relation"): "NO_EXISTING_ARM EXACT_DUPLICATE CHANGED_BYTES_SAME_IDENTITY LOOKUP_INDETERMINATE".split(),
    ("F5DispatchArmDispositionV0_1R2", "result"): "APPLIED REPLAYED REJECTED INDETERMINATE".split(),
    ("F5DispatchArmDispositionV0_1R2", "primary_reason"): "ARMED_FIRST_APPLY EXACT_DUPLICATE_REPLAY REQUEST_BYTES_CONFLICT ARM_LOOKUP_UNAVAILABLE SYNTHETIC_INPUT CLAIM_STALE TOKEN_MISMATCH TERMINAL_ALREADY_RECORDED AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED OBSERVATION_UNAVAILABLE CAS_MISMATCH INTEGRITY_FAILURE".split(),
    ("F5DeliveryAttemptFactV0_1R1", "outcome"): "PRE_EFFECT_NOT_EXECUTED DISPATCHED ACKED SUCCEEDED FAILED UNKNOWN".split(),
    ("F5DeliveryReceiptV0_1R1", "receipt_kind"): "TRANSPORT_ACK EFFECT_SUCCEEDED EFFECT_FAILED EFFECT_STATUS_UNKNOWN EFFECT_QUERY_RESULT".split(),
    ("F5DeliveryReceiptV0_1R1", "effect_status"): "ACKED_ONLY SUCCEEDED FAILED UNKNOWN NOT_EXECUTED".split(),
    ("F5DeliveryReceiptDispositionV0_1R3", "dedup_relation"): "NEW EXACT_DUPLICATE CHANGED_BYTES_SAME_KEY LOOKUP_INDETERMINATE".split(),
    ("F5DeliveryReceiptDispositionV0_1R3", "result"): "APPLIED HISTORY_ONLY REPLAYED REJECTED INDETERMINATE".split(),
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
    if field == "interface_version": return "literal:" + interface
    if (name, field) in ENUMS: return "enum:" + "|".join(ENUMS[(name, field)])
    if field in BOOL_FIELDS: return "boolean"
    if field == "reason_codes": return "sorted_unique_closed_set"
    if field == "evidence_refs": return "sorted_unique_stable_refs"
    if (name, field) in NULLABLE_KEYS:
        if field == "returned_at_utc_ms": return "non_negative_safe_integer|null"
        return ("lowercase_sha256|null" if field.endswith("_fingerprint") else "stable_ref|null")
    if field.endswith("_fingerprint") or field in SHA_ID_FIELDS: return "lowercase_sha256"
    if field == "expected_previous_claim_epoch" or field.endswith(("_utc_ms", "_sequence", "_generation", "_count")): return "non_negative_safe_integer"
    if field.endswith(("_epoch", "_ordinal", "_revision", "_version")): return "positive_safe_integer"
    return "stable_ref"


def validate_type(value: Any, type_name: str, path: str, closed_reasons: set[str] | None = None) -> None:
    if type_name.startswith("literal:"):
        ensure(value == type_name.split(":", 1)[1], f"literal mismatch at {path}")
    elif type_name.startswith("enum:"):
        ensure(isinstance(value, str) and value in type_name.split(":", 1)[1].split("|"), f"enum mismatch at {path}")
    elif type_name == "boolean":
        ensure(type(value) is bool, f"boolean required at {path}")
    elif type_name == "lowercase_sha256":
        ensure(isinstance(value, str) and SHA_RE.fullmatch(value) is not None, f"sha256 required at {path}")
    elif type_name == "stable_ref":
        ensure(isinstance(value, str) and bool(value) and value.strip() == value, f"stable_ref required at {path}")
    elif type_name == "positive_safe_integer":
        ensure(type(value) is int and 0 < value <= SAFE_INTEGER, f"positive safe integer required at {path}")
    elif type_name == "non_negative_safe_integer":
        ensure(type(value) is int and 0 <= value <= SAFE_INTEGER, f"non-negative safe integer required at {path}")
    elif type_name.endswith("|null"):
        if value is not None: validate_type(value, type_name[:-5], path)
    elif type_name == "sorted_unique_stable_refs":
        ensure(isinstance(value, list) and value == sorted(set(value)), f"sorted unique refs required at {path}")
        for index, item in enumerate(value): validate_type(item, "stable_ref", f"{path}[{index}]")
    elif type_name == "sorted_unique_closed_set":
        ensure(isinstance(value, list) and value == sorted(set(value)), f"sorted unique reasons required at {path}")
        ensure(closed_reasons is not None and all(isinstance(x, str) and x in closed_reasons for x in value), f"unknown reason at {path}")
    else:
        raise ValueError(f"unknown type rule {type_name} at {path}")


def object_fingerprint(obj: dict[str, Any], fields: list[str], fp_field: str) -> str:
    return h(obj["interface_version"] + "-fingerprint", *[obj[field] for field in fields if field != fp_field])


def raw_object_fingerprint(obj: dict[str, Any], fields: list[str], fp_field: str) -> str:
    return raw_h(obj["interface_version"] + "-fingerprint", *[obj[field] for field in fields if field != fp_field])


META = {name: (interface, fp_field, fields) for name, interface, fp_field, fields in SCHEMAS}


def validate_cross(name: str, obj: dict[str, Any]) -> None:
    def paired(ref: str, fp: str) -> None:
        ensure((obj[ref] is None) == (obj[fp] is None), f"nullable ref/fingerprint mismatch in {name}")
    if name == "F5OutboxIntentV0_1R1":
        ensure(obj["created_at_utc_ms"] < obj["start_authority_expires_at_utc_ms"], "intent expiry ordering invalid")
        ensure(obj["environment"] != "SYNTHETIC_TEST" or obj["authority_eligible"] is False, "synthetic intent cannot be authority eligible")
    elif name == "F5EnqueueDispositionV0_1R1":
        paired("outbox_intent_ref", "outbox_intent_fingerprint")
        ensure(obj["result"] == "NOT_EXECUTABLE" and obj["primary_reason"] == "SYNTHETIC_INPUT" and obj["outbox_intent_ref"] is None, "synthetic enqueue shape invalid")
    elif name == "F5DispatcherClaimantAssessmentV0_1R1":
        ensure(obj["assessed_at_event_sequence"] <= obj["owner_head_event_sequence"], "claimant watermark invalid")
        ensure(obj["environment"] != "SYNTHETIC_TEST" or obj["authority_eligible"] is False, "synthetic claimant cannot be authority eligible")
    elif name == "F5PhysicalBoundaryAuthorityObservationV0_1R1":
        ensure(obj["observed_event_sequence"] == obj["canonical_writer_head_event_sequence"], "observation watermark invalid")
        ensure(obj["result"] != "CURRENT" or obj["fresh_F4_assessment_result"] == "CURRENT", "current observation lacks current F4 result")
    elif name == "F5OutboxClaimFactV0_1R1":
        ensure(obj["claim_epoch"] == obj["expected_previous_claim_epoch"] + 1, "claim epoch is not previous plus one")
        ensure(obj["claimed_at_utc_ms"] < obj["lease_expires_at_utc_ms"], "claim lease ordering invalid")
        ensure(obj["result"] == "NOT_EXECUTABLE" and obj["primary_reason"] == "SYNTHETIC_INPUT", "synthetic claim must be non-executable")
    elif name == "F5OutboxLeaseFactV0_1R1":
        ensure(obj["renewed_at_utc_ms"] < obj["previous_lease_expiry_utc_ms"] < obj["new_lease_expiry_utc_ms"], "lease time bounds invalid")
    elif name == "F5DispatchArmDispositionV0_1R2":
        paired("first_arm_ref", "first_arm_fingerprint")
        ensure(obj["result"] == "REJECTED" and obj["primary_reason"] == "SYNTHETIC_INPUT", "synthetic arm disposition must reject")
        ensure(obj["event_created"] is False and obj["physical_call_authorized"] is False and obj["first_arm_ref"] is None, "synthetic arm occurrence leaked")
    elif name == "F5DeliveryAttemptFactV0_1R1":
        ensure(obj["returned_at_utc_ms"] is None or obj["started_at_utc_ms"] <= obj["returned_at_utc_ms"], "attempt time ordering invalid")
        if obj["outcome"] == "PRE_EFFECT_NOT_EXECUTED": ensure(obj["effect_may_have_occurred"] is False and obj["automatic_retry_eligible"] is False, "pre-effect attempt flags invalid")
    elif name == "F5DeliveryReceiptV0_1R1":
        ensure(obj["observed_at_utc_ms"] <= obj["received_at_utc_ms"], "receipt time ordering invalid")
        ensure(compatibility(obj["receipt_kind"], obj["effect_status"]) == "COMPATIBLE", "receipt shape incompatible")
    elif name == "F5DeliveryReceiptDispositionV0_1R3":
        expected_flags = {
            "APPLIED": (True, True), "HISTORY_ONLY": (True, False), "REPLAYED": (False, False), "REJECTED": (False, False), "INDETERMINATE": (False, False)
        }[obj["result"]]
        ensure((obj["event_created"], obj["current_projection_advanced"]) == expected_flags, "receipt disposition flags invalid")
        ensure(obj["task_advancement_eligible"] is False, "F5 cannot advance Task")
    elif name == "F5DeadLetterFactV0_1R1":
        paired("last_claim_ref", "last_claim_fingerprint"); paired("last_attempt_ref", "last_attempt_fingerprint")
    elif name == "F5ReconciliationCaseV0_1R1":
        paired("attempt_ref", "attempt_fingerprint")
        ensure(obj["opened_event_sequence"] <= obj["last_updated_event_sequence"], "reconciliation watermark ordering invalid")
    elif name == "F5OutboxProjectionV0_1R1":
        paired("current_claim_ref", "current_claim_fingerprint"); paired("current_attempt_ref", "current_attempt_fingerprint"); paired("current_reconciliation_ref", "current_reconciliation_fingerprint")
        if obj["state"] == "PENDING": ensure(obj["current_claim_ref"] is None and obj["current_attempt_ref"] is None and obj["effect_outcome"] == "NOT_PROVEN", "pending projection invalid")
    elif name == "F5SyntheticDeliveryRecoveryWitnessV0_1R1":
        ensure(obj["authority_eligible"] is obj["runtime_consumable"] is obj["recovery_importable"] is False, "witness authority boundary invalid")
        for field in ("accepted_real_handoff_count", "armed_dispatch_count", "external_effect_count", "provider_call_count", "raw_secret_count"): ensure(obj[field] == 0, f"witness {field} nonzero")


def validate_object(name: str, obj: dict[str, Any]) -> None:
    interface, fp_field, fields = META[name]
    ensure(type(obj) is dict and set(obj) == set(fields) and len(obj) == len(fields), f"{name} closed field inventory mismatch")
    reason_values = set(ENUMS.get((name, "primary_reason"), []))
    if name == "F5DeliveryReceiptDispositionV0_1R3":
        reason_values.update({"EPOCH_STALE", "FENCE_STALE", "ATTEMPT_STALE"})
    for field in fields:
        validate_type(obj[field], field_type(name, field, interface), f"{name}.{field}", reason_values if field == "reason_codes" else None)
    ensure(obj[fp_field] == object_fingerprint(obj, fields, fp_field), f"{name} fingerprint mismatch")
    validate_cross(name, obj)


CLAIM_PRECEDENCE = "INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED DISPATCH_ALREADY_ARMED CLAIM_ALREADY_ACTIVE INTENT_NOT_PENDING CLAIMANT_STALE CLAIMANT_UNAVAILABLE AUTHORITY_STALE AUTHORITY_UNAVAILABLE EXPIRED CAS_MISMATCH CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY CLAIMED_NEW".split()
LEASE_PRECEDENCE = "INTEGRITY_FAILURE CLAIM_STALE TOKEN_MISMATCH DISPATCH_ALREADY_ARMED EXPIRED CAS_MISMATCH RENEWED".split()
ARM_PRECEDENCE = "INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED CLAIM_STALE TOKEN_MISMATCH AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED OBSERVATION_UNAVAILABLE CAS_MISMATCH ARMED_FIRST_APPLY".split()


def reduce_reasons(kind: str, raw: list[dict[str, Any]]) -> dict[str, Any]:
    ensure(all(set(row) == {"reason", "is_true"} and type(row["is_true"]) is bool for row in raw), "precedence raw row invalid")
    precedence = {"CLAIM": CLAIM_PRECEDENCE, "LEASE": LEASE_PRECEDENCE, "ARM": ARM_PRECEDENCE}[kind]
    active = {row["reason"] for row in raw if row["is_true"]}
    ensure(active and active <= set(precedence), "precedence raw reason invalid")
    primary = next(x for x in precedence if x in active)
    if kind == "CLAIM": result = "INDETERMINATE" if primary in {"CLAIMANT_UNAVAILABLE", "AUTHORITY_UNAVAILABLE"} else "NOT_EXECUTABLE"
    elif kind == "LEASE": result = "REJECTED"
    else: result = "INDETERMINATE" if primary == "OBSERVATION_UNAVAILABLE" else "REJECTED"
    return {"result": result, "primary_reason": primary, "reason_codes": sorted(active)}


RECEIPT_KINDS = "TRANSPORT_ACK EFFECT_SUCCEEDED EFFECT_FAILED EFFECT_STATUS_UNKNOWN EFFECT_QUERY_RESULT".split()
EFFECT_STATUSES = "ACKED_ONLY SUCCEEDED FAILED UNKNOWN NOT_EXECUTED".split()
RECEIPT_ALLOWED = {"TRANSPORT_ACK": {"ACKED_ONLY"}, "EFFECT_SUCCEEDED": {"SUCCEEDED"}, "EFFECT_FAILED": {"FAILED"}, "EFFECT_STATUS_UNKNOWN": {"UNKNOWN"}, "EFFECT_QUERY_RESULT": {"SUCCEEDED", "FAILED", "UNKNOWN", "NOT_EXECUTED"}}
STATES = "PENDING CLAIMED DISPATCH_ARMED DISPATCHED ACKED SUCCEEDED FAILED UNKNOWN DEAD_LETTERED RECONCILED".split()
ALLOWED_TRANSITIONS = {
    ("PENDING", "CLAIMED"), ("PENDING", "DEAD_LETTERED"), ("CLAIMED", "CLAIMED"), ("CLAIMED", "DISPATCH_ARMED"), ("CLAIMED", "DEAD_LETTERED"),
    ("DISPATCH_ARMED", "DISPATCHED"), ("DISPATCH_ARMED", "ACKED"), ("DISPATCH_ARMED", "SUCCEEDED"), ("DISPATCH_ARMED", "FAILED"), ("DISPATCH_ARMED", "UNKNOWN"),
    ("DISPATCHED", "ACKED"), ("DISPATCHED", "SUCCEEDED"), ("DISPATCHED", "FAILED"), ("DISPATCHED", "UNKNOWN"), ("ACKED", "SUCCEEDED"), ("ACKED", "FAILED"), ("ACKED", "UNKNOWN"),
    ("FAILED", "RECONCILED"), ("UNKNOWN", "RECONCILED"), ("DEAD_LETTERED", "RECONCILED"),
}


def compatibility(kind: str, status: str) -> str:
    ensure(kind in RECEIPT_KINDS and status in EFFECT_STATUSES, "receipt compatibility enum invalid")
    return "COMPATIBLE" if status in RECEIPT_ALLOWED[kind] else "RECEIPT_KIND_STATUS_MISMATCH"


def parse_request_record(record: dict[str, Any]) -> dict[str, Any]:
    ensure(set(record) == {"request_id", "request_fingerprint", "request_canonical_utf8_hex", "bound_invocation_identity_fingerprint"}, "submitted request inventory invalid")
    ensure(SHA_RE.fullmatch(record["request_id"]) and SHA_RE.fullmatch(record["request_fingerprint"]) and SHA_RE.fullmatch(record["bound_invocation_identity_fingerprint"]), "request hash invalid")
    ensure(isinstance(record["request_canonical_utf8_hex"], str) and HEX_RE.fullmatch(record["request_canonical_utf8_hex"]), "request bytes hex invalid")
    payload = parse_json_strict(bytes.fromhex(record["request_canonical_utf8_hex"]).decode("utf-8"))
    validate_json_value(payload)
    ensure(record["request_fingerprint"] == digest(payload), "request bytes/fingerprint mismatch")
    ensure(payload["bound_invocation_identity_fingerprint"] == record["bound_invocation_identity_fingerprint"], "request invocation binding mismatch")
    return payload


def derive_arm(raw: dict[str, Any]) -> dict[str, Any]:
    expected_fields = {"lookup_reproducible", "bound_invocation_identity_fingerprint", "stored_arm_state", "submitted_request", "first_apply_eligibility", "previous_event_count", "previous_call_authorization_count"}
    ensure(set(raw) == expected_fields, "arm raw input inventory mismatch")
    ensure(type(raw["lookup_reproducible"]) is bool, "arm lookup flag type invalid")
    ensure(type(raw["previous_event_count"]) is int and 0 <= raw["previous_event_count"] <= SAFE_INTEGER, "arm previous Event count invalid")
    ensure(type(raw["previous_call_authorization_count"]) is int and 0 <= raw["previous_call_authorization_count"] <= SAFE_INTEGER, "arm previous call count invalid")
    ensure(raw["first_apply_eligibility"] in {"ELIGIBLE_PROOF_PRECONDITION", "NOT_ELIGIBLE"}, "arm eligibility enum invalid")
    ensure(isinstance(raw["bound_invocation_identity_fingerprint"], str) and SHA_RE.fullmatch(raw["bound_invocation_identity_fingerprint"]), "arm bound invocation invalid")
    parse_request_record(raw["submitted_request"])
    ensure(raw["submitted_request"]["bound_invocation_identity_fingerprint"] == raw["bound_invocation_identity_fingerprint"], "submitted request bound invocation mismatch")
    stored = raw["stored_arm_state"]
    if stored is not None:
        expected_stored = {"request_id", "request_fingerprint", "request_canonical_utf8_hex", "bound_invocation_identity_fingerprint", "first_arm_ref", "first_arm_fingerprint", "committed_event_count", "committed_call_authorization_count"}
        ensure(set(stored) == expected_stored, "stored arm inventory invalid")
        parse_request_record({k: stored[k] for k in ("request_id", "request_fingerprint", "request_canonical_utf8_hex", "bound_invocation_identity_fingerprint")})
        ensure(stored["bound_invocation_identity_fingerprint"] == raw["bound_invocation_identity_fingerprint"], "stored arm bound invocation mismatch")
        validate_type(stored["first_arm_ref"], "stable_ref", "stored_arm.first_arm_ref")
        validate_type(stored["first_arm_fingerprint"], "lowercase_sha256", "stored_arm.first_arm_fingerprint")
        ensure(stored["committed_event_count"] == stored["committed_call_authorization_count"] == 1, "stored first accounting invalid")
    if not raw["lookup_reproducible"]: relation = "LOOKUP_INDETERMINATE"
    elif stored is None: relation = "NO_EXISTING_ARM"
    else:
        submitted = raw["submitted_request"]
        exact = all(stored[k] == submitted[k] for k in ("request_id", "request_fingerprint", "request_canonical_utf8_hex", "bound_invocation_identity_fingerprint"))
        relation = "EXACT_DUPLICATE" if exact else "CHANGED_BYTES_SAME_IDENTITY"
    outputs = {"NO_EXISTING_ARM": ("APPLIED", "ARMED_FIRST_APPLY", 1, 1), "EXACT_DUPLICATE": ("REPLAYED", "EXACT_DUPLICATE_REPLAY", 0, 0), "CHANGED_BYTES_SAME_IDENTITY": ("REJECTED", "REQUEST_BYTES_CONFLICT", 0, 0), "LOOKUP_INDETERMINATE": ("INDETERMINATE", "ARM_LOOKUP_UNAVAILABLE", 0, 0)}
    result, reason, event_delta, call_delta = outputs[relation]
    if relation == "NO_EXISTING_ARM" and raw["first_apply_eligibility"] != "ELIGIBLE_PROOF_PRECONDITION": result, reason, event_delta, call_delta = "REJECTED", "FIRST_APPLY_NOT_ELIGIBLE", 0, 0
    returned_ref = stored["first_arm_ref"] if relation == "EXACT_DUPLICATE" else None
    returned_fp = stored["first_arm_fingerprint"] if relation == "EXACT_DUPLICATE" else None
    return {"replay_relation": relation, "result": result, "primary_reason": reason, "returned_first_arm_ref": returned_ref, "returned_first_arm_fingerprint": returned_fp, "modeled_event_delta": event_delta, "modeled_call_authorization_delta": call_delta, "total_event_count": raw["previous_event_count"] + event_delta, "total_call_authorization_count": raw["previous_call_authorization_count"] + call_delta}


def receipt_relation(raw: dict[str, Any]) -> str:
    if not raw["lookup_reproducible"]: return "LOOKUP_INDETERMINATE"
    if raw["stored_receipt"] is None: return "NEW"
    ensure(raw["stored_receipt"]["source_id"] == raw["submitted_receipt"]["source_id"] and raw["stored_receipt"]["receipt_id"] == raw["submitted_receipt"]["receipt_id"], "receipt lookup key mismatch")
    return "EXACT_DUPLICATE" if raw["stored_receipt"]["receipt_fingerprint"] == raw["submitted_receipt"]["receipt_fingerprint"] else "CHANGED_BYTES_SAME_KEY"


def reduce_receipt(raw: dict[str, Any]) -> dict[str, Any]:
    expected_fields = {"lookup_reproducible", "stored_receipt", "submitted_receipt", "receipt_kind", "effect_status", "integrity_valid", "source_attestation_status", "attempt_effect_identity_match", "existing_effect_query_authenticated", "epoch_current", "fences_current", "attempt_current", "from_state", "to_state"}
    ensure(set(raw) == expected_fields, "receipt raw input inventory mismatch")
    ensure(type(raw["lookup_reproducible"]) is bool, "receipt lookup flag invalid")
    for field in ("integrity_valid", "attempt_effect_identity_match", "existing_effect_query_authenticated", "epoch_current", "fences_current", "attempt_current"):
        ensure(type(raw[field]) is bool, f"receipt boolean {field} invalid")
    ensure(raw["source_attestation_status"] in {"VALID", "INVALID", "UNAVAILABLE"}, "receipt attestation enum invalid")
    ensure(raw["from_state"] in STATES and raw["to_state"] in STATES, "receipt state enum invalid")
    ensure(set(raw["submitted_receipt"]) == {"source_id", "receipt_id", "receipt_fingerprint"}, "submitted receipt inventory invalid")
    validate_type(raw["submitted_receipt"]["source_id"], "stable_ref", "submitted_receipt.source_id")
    validate_type(raw["submitted_receipt"]["receipt_id"], "stable_ref", "submitted_receipt.receipt_id")
    validate_type(raw["submitted_receipt"]["receipt_fingerprint"], "lowercase_sha256", "submitted_receipt.receipt_fingerprint")
    if raw["stored_receipt"] is not None:
        ensure(set(raw["stored_receipt"]) == {"source_id", "receipt_id", "receipt_fingerprint"}, "stored receipt inventory invalid")
        validate_type(raw["stored_receipt"]["source_id"], "stable_ref", "stored_receipt.source_id")
        validate_type(raw["stored_receipt"]["receipt_id"], "stable_ref", "stored_receipt.receipt_id")
        validate_type(raw["stored_receipt"]["receipt_fingerprint"], "lowercase_sha256", "stored_receipt.receipt_fingerprint")
    relation = receipt_relation(raw); comp = compatibility(raw["receipt_kind"], raw["effect_status"])
    base = {"dedup_relation": relation, "compatibility": comp, "task_advancement_eligible": False}
    if relation == "LOOKUP_INDETERMINATE": return {**base, "result": "INDETERMINATE", "primary_reason": "RECEIPT_LOOKUP_UNAVAILABLE", "reason_codes": ["RECEIPT_LOOKUP_UNAVAILABLE"], "event_created": False, "reconciliation_opened": False, "current_projection_advanced": False}
    if relation == "EXACT_DUPLICATE": return {**base, "result": "REPLAYED", "primary_reason": "EXACT_DUPLICATE_REPLAY", "reason_codes": [], "event_created": False, "reconciliation_opened": False, "current_projection_advanced": False}
    if relation == "CHANGED_BYTES_SAME_KEY": return {**base, "result": "REJECTED", "primary_reason": "RECEIPT_BYTES_CONFLICT", "reason_codes": ["RECEIPT_BYTES_CONFLICT"], "event_created": False, "reconciliation_opened": True, "current_projection_advanced": False}
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
    primary = next((x for x in precedence if x in reasons), "APPLIED_CURRENT")
    if primary == "APPLIED_CURRENT": result = "APPLIED"
    elif primary == "SOURCE_ATTESTATION_UNAVAILABLE": result = "INDETERMINATE"
    elif primary in {"EPOCH_STALE", "FENCE_STALE", "ATTEMPT_STALE"}: result = "HISTORY_ONLY"
    else: result = "REJECTED"
    return {**base, "result": result, "primary_reason": ("HISTORY_ONLY_" + primary if result == "HISTORY_ONLY" else primary), "reason_codes": sorted(reasons), "event_created": result in {"APPLIED", "HISTORY_ONLY"}, "reconciliation_opened": False, "current_projection_advanced": result == "APPLIED"}


SECTIONS = ("schema_profiles", "schema_shape_examples", "synthetic_nonauthority_scenario", "identity_formula_graph", "precedence_ordering_trials", "arm_state_derivation_cases", "receipt_compatibility_cases", "receipt_currentness_cases", "transition_cases", "adversarial_cases", "assertions", "summary")
ROOT_FIELDS = {"fixture_interface", "environment", "authority_eligible", "runtime_consumable", "fixture_canonical_sha256"} | set(SECTIONS) | {key + "_fingerprint" for key in SECTIONS}


def section_fingerprint(name: str, value: Any) -> str:
    return h(PROOF_DOMAIN, name, value)


def validate_profiles(fixture: dict[str, Any]) -> None:
    profiles = fixture["schema_profiles"]
    ensure(len(profiles) == len(SCHEMAS), "schema profile count mismatch")
    for actual, (name, interface, fp_field, fields) in zip(profiles, SCHEMAS):
        ensure(set(actual) == {"schema_name", "interface_version", "fingerprint_field", "fields", "field_types", "schema_profile_fingerprint"}, "profile inventory invalid")
        types = [field_type(name, field, interface) for field in fields]
        expected = {"schema_name": name, "interface_version": interface, "fingerprint_field": fp_field, "fields": fields, "field_types": types, "schema_profile_fingerprint": h(PROOF_DOMAIN, "schema-profile", name, interface, fp_field, fields, types)}
        ensure(actual == expected, f"schema profile mismatch for {name}")


def validate_shapes(fixture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = fixture["schema_shape_examples"]
    ensure(len(rows) == len(SCHEMAS), "shape count mismatch")
    by_name: dict[str, dict[str, Any]] = {}
    for row in rows:
        ensure(set(row) == {"schema_name", "semantic_role", "occurrence_count", "object"}, "shape row inventory invalid")
        ensure(row["semantic_role"] == "NON_OCCURRING_SHAPE_EXAMPLE" and row["occurrence_count"] == 0, "shape represented as occurrence")
        ensure(row["schema_name"] not in by_name and row["schema_name"] in META, "shape schema invalid")
        validate_object(row["schema_name"], row["object"])
        by_name[row["schema_name"]] = row["object"]
    ensure(set(by_name) == set(META), "shape schema set mismatch")
    intent, claim, request, arm = (by_name[n] for n in ("F5OutboxIntentV0_1R1", "F5OutboxClaimFactV0_1R1", "F5DispatchArmRequestV0_1R2", "F5DispatchArmFactV0_1R2"))
    ensure(claim["outbox_intent_ref"] == intent["outbox_intent_ref"] and claim["outbox_intent_fingerprint"] == intent["canonical_fingerprint"], "claim/intent binding invalid")
    ensure(request["claim_ref"] == claim["claim_ref"] and request["claim_fingerprint"] == claim["canonical_fingerprint"], "request/claim binding invalid")
    ensure(arm["dispatch_arm_request_id"] == request["dispatch_arm_request_id"] and arm["dispatch_arm_request_fingerprint"] == request["canonical_fingerprint"], "arm/request binding invalid")
    return by_name


def expected_identities(objects: dict[str, dict[str, Any]]) -> dict[str, str]:
    intent = objects["F5OutboxIntentV0_1R1"]; claim = objects["F5OutboxClaimFactV0_1R1"]; request = objects["F5DispatchArmRequestV0_1R2"]
    return {
        "outbox_intent_id": h("agents-os.f5-outbox-intent-id.v0.1", intent["source_handoff_fingerprint"], intent["invocation_identity_fingerprint"], intent["effect_id"]),
        "claim_id": h("agents-os.f5-outbox-claim-id.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"]),
        "claim_fencing_token": h("agents-os.f5-outbox-claim-fence.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"], claim["claimant_assessment_fingerprint"]),
        "attempt_id": h("agents-os.f5-delivery-attempt-id.v0.1", request["outbox_intent_fingerprint"], request["attempt_ordinal"]),
        "dispatch_arm_request_id": h("agents-os.f5-dispatch-arm-request-id.v0.1", request["outbox_intent_fingerprint"], request["invocation_identity_fingerprint"], request["attempt_ordinal"]),
        "dispatch_arm_id": h("agents-os.f5-dispatch-arm-id.v0.2", request["dispatch_arm_request_id"]),
    }


def validate_graph(fixture: dict[str, Any]) -> None:
    graph = fixture["identity_formula_graph"]
    ensure(set(graph) == {"proof_mode", "authority_eligible", "runtime_consumable", "occurrence_count", "objects", "derived_identities"}, "identity graph inventory invalid")
    ensure(graph["proof_mode"] == "ABSTRACT_NONOCCURRING_FORMULA_PROOF" and graph["authority_eligible"] is graph["runtime_consumable"] is False and graph["occurrence_count"] == 0, "identity graph authority leak")
    required = {"F5OutboxIntentV0_1R1", "F5OutboxClaimFactV0_1R1", "F5DispatchArmRequestV0_1R2", "F5DispatchArmFactV0_1R2"}
    ensure(set(graph["objects"]) == required, "identity graph object set invalid")
    for name, obj in graph["objects"].items(): validate_object(name, obj)
    ids = expected_identities(graph["objects"])
    ensure(graph["derived_identities"] == ids, "derived identity map mismatch")
    intent = graph["objects"]["F5OutboxIntentV0_1R1"]; claim = graph["objects"]["F5OutboxClaimFactV0_1R1"]; request = graph["objects"]["F5DispatchArmRequestV0_1R2"]; arm = graph["objects"]["F5DispatchArmFactV0_1R2"]
    ensure(intent["outbox_intent_id"] == ids["outbox_intent_id"] and intent["outbox_intent_ref"] == "outbox-intent:" + ids["outbox_intent_id"], "intent formula invalid")
    ensure(claim["claim_id"] == ids["claim_id"] and claim["claim_ref"] == "outbox-claim:" + ids["claim_id"] and claim["claim_fencing_token"] == ids["claim_fencing_token"], "claim formula invalid")
    ensure(request["attempt_id"] == ids["attempt_id"] and request["dispatch_arm_request_id"] == ids["dispatch_arm_request_id"], "request formula invalid")
    ensure(arm["dispatch_arm_id"] == ids["dispatch_arm_id"] and arm["dispatch_arm_ref"] == "dispatch-arm:" + ids["dispatch_arm_id"], "arm formula invalid")
    ensure(request["idempotency_key"] == intent["effect_id"] == arm["idempotency_key"], "idempotency binding invalid")


def validate_proofs(fixture: dict[str, Any]) -> None:
    trials = fixture["precedence_ordering_trials"]
    ensure(len(trials) == 294, "precedence trial count must be 294")
    case_orders: dict[str, set[int]] = {}
    case_outputs: dict[str, set[str]] = {}
    for row in trials:
        ensure(set(row) == {"unordered_case_id", "kind", "ordering", "raw_conditions", "derived"}, "precedence row inventory invalid")
        actual = reduce_reasons(row["kind"], row["raw_conditions"])
        ensure(row["derived"] == actual, "precedence result not raw-derived")
        case_orders.setdefault(row["unordered_case_id"], set()).add(row["ordering"])
        case_outputs.setdefault(row["unordered_case_id"], set()).add(json.dumps(actual, sort_keys=True))
    ensure(len(case_orders) == 147 and all(v == {1, 2} for v in case_orders.values()) and all(len(v) == 1 for v in case_outputs.values()), "precedence two-order invariance failed")
    arms = fixture["arm_state_derivation_cases"]
    ensure(len(arms) == 4, "arm case count invalid")
    relations = set()
    for row in arms:
        ensure(set(row) == {"case_id", "proof_mode", "raw_input", "derived"} and row["proof_mode"] == "ABSTRACT_NONOCCURRING_REDUCER_TRIAL", "arm row inventory invalid")
        actual = derive_arm(row["raw_input"]); ensure(row["derived"] == actual, "arm relation not state-derived"); relations.add(actual["replay_relation"])
    ensure(relations == {"NO_EXISTING_ARM", "EXACT_DUPLICATE", "CHANGED_BYTES_SAME_IDENTITY", "LOOKUP_INDETERMINATE"}, "arm relation coverage invalid")
    compat = fixture["receipt_compatibility_cases"]
    ensure(len(compat) == 25, "receipt compatibility count invalid")
    for row in compat:
        ensure(set(row) == {"receipt_kind", "effect_status", "derived_compatibility"}, "compatibility row inventory invalid")
        ensure(row["derived_compatibility"] == compatibility(row["receipt_kind"], row["effect_status"]), "compatibility derivation invalid")
        ensure(row["derived_compatibility"] in {"COMPATIBLE", "RECEIPT_KIND_STATUS_MISMATCH"}, "compatibility escalated to application")
    receipts = fixture["receipt_currentness_cases"]
    ensure(len(receipts) >= 10, "receipt currentness coverage incomplete")
    results = set()
    for row in receipts:
        ensure(set(row) == {"case_id", "raw_input", "derived"}, "receipt currentness row inventory invalid")
        actual = reduce_receipt(row["raw_input"]); ensure(row["derived"] == actual, "receipt result not raw-derived"); results.add(actual["result"])
    ensure({"APPLIED", "HISTORY_ONLY", "REJECTED", "INDETERMINATE", "REPLAYED"} <= results, "receipt result coverage incomplete")
    transitions = fixture["transition_cases"]
    ensure(len(STATES) == 10 and len(transitions) == 100, "transition proof must be 10x10=100")
    expected = [{"from_state": old, "to_state": new, "derived": "ALLOWED" if (old, new) in ALLOWED_TRANSITIONS else "REJECTED_TRANSITION_INVALID"} for old, new in product(STATES, STATES)]
    ensure(transitions == expected, "transition table mismatch")


def validate_scenario_and_assertions(fixture: dict[str, Any]) -> None:
    scenario = fixture["synthetic_nonauthority_scenario"]
    ensure(set(scenario) == {"raw_input", "derived"} and scenario["raw_input"] == {"environment": "SYNTHETIC_TEST", "authority_eligible": False}, "synthetic scenario raw input invalid")
    expected = {"enqueue_result": "NOT_EXECUTABLE", "enqueue_primary_reason": "SYNTHETIC_INPUT", "claim_result": "NOT_EXECUTABLE", "claim_primary_reason": "SYNTHETIC_INPUT", "arm_result": "REJECTED", "arm_primary_reason": "SYNTHETIC_INPUT", "claim_event_created": False, "arm_event_created": False, "physical_call_authorized": False}
    ensure(scenario["derived"] == expected, "synthetic scenario authority leak")
    assertions = fixture["assertions"]
    ensure(set(assertions) == {"accepted_real_handoff_count", "claim_event_count", "armed_dispatch_count", "runtime_consumable_count", "external_effect_count", "provider_call_count", "raw_secret_count", "terminal_outcome"}, "assertion inventory invalid")
    for field in assertions:
        if field != "terminal_outcome": ensure(assertions[field] == 0, f"{field} must be zero")
    ensure(assertions["terminal_outcome"] == "NOT_EXECUTED", "terminal outcome invalid")


def validate_fixture(fixture: dict[str, Any], run_mutations: bool = True) -> dict[str, Any]:
    validate_json_value(fixture)
    ensure(type(fixture) is dict and set(fixture) == ROOT_FIELDS, "closed root inventory mismatch")
    ensure(fixture["fixture_interface"] == FIXTURE_INTERFACE and fixture["environment"] == "SYNTHETIC_TEST", "fixture identity invalid")
    ensure(fixture["authority_eligible"] is fixture["runtime_consumable"] is False, "fixture authority boundary invalid")
    validate_profiles(fixture); validate_shapes(fixture); validate_graph(fixture); validate_proofs(fixture); validate_scenario_and_assertions(fixture)
    expected_summary = {"schema_profile_count": 16, "schema_shape_example_count": 16, "identity_formula_count": 6, "precedence_unordered_pair_count": 147, "precedence_ordering_trial_count": 294, "arm_state_derivation_case_count": 4, "receipt_compatibility_case_count": 25, "receipt_currentness_case_count": len(fixture["receipt_currentness_cases"]), "transition_state_count": 10, "transition_case_count": 100, "adversarial_case_count": 9}
    ensure(fixture["summary"] == expected_summary, "summary mismatch")
    # Fingerprints are checked only after closed schema and semantic validation.
    for key in SECTIONS: ensure(fixture[key + "_fingerprint"] == section_fingerprint(key, fixture[key]), f"{key} section fingerprint mismatch")
    root = copy.deepcopy(fixture); claimed = root.pop("fixture_canonical_sha256"); ensure(claimed == digest(root), "fixture root fingerprint mismatch")
    mutation_result = mutation_checks(fixture) if run_mutations else {"schema_invalid_resigned_mutations_rejected": None, "graph_level_identity_mutations_rejected": None, "proof_mutations_rejected": None, "duplicate_key_probe_rejected": None}
    return {"result": "PASS_NO_BLOCKER", **expected_summary, **mutation_result, "fixture_canonical_sha256": fixture["fixture_canonical_sha256"], **fixture["assertions"]}


def raw_resign_section(fixture: dict[str, Any], section: str) -> None:
    fixture[section + "_fingerprint"] = raw_h(PROOF_DOMAIN, section, fixture[section])


def raw_resign_root(fixture: dict[str, Any]) -> None:
    fixture.pop("fixture_canonical_sha256", None); fixture["fixture_canonical_sha256"] = raw_digest(fixture)


def raw_resign_shape(fixture: dict[str, Any], index: int) -> None:
    row = fixture["schema_shape_examples"][index]; name = row["schema_name"]; _, fp_field, fields = META[name]
    row["object"][fp_field] = raw_object_fingerprint(row["object"], fields, fp_field)
    raw_resign_section(fixture, "schema_shape_examples"); raw_resign_root(fixture)


def propagate_graph_with_override(fixture: dict[str, Any], target: str) -> None:
    graph = fixture["identity_formula_graph"]; objects = graph["objects"]
    intent = objects["F5OutboxIntentV0_1R1"]; claim = objects["F5OutboxClaimFactV0_1R1"]; request = objects["F5DispatchArmRequestV0_1R2"]; arm = objects["F5DispatchArmFactV0_1R2"]
    wrong = "f" * 64
    intent_id = wrong if target == "outbox_intent_id" else h("agents-os.f5-outbox-intent-id.v0.1", intent["source_handoff_fingerprint"], intent["invocation_identity_fingerprint"], intent["effect_id"])
    intent["outbox_intent_id"] = intent_id; intent["outbox_intent_ref"] = "outbox-intent:" + intent_id; intent["canonical_fingerprint"] = object_fingerprint(intent, META["F5OutboxIntentV0_1R1"][2], META["F5OutboxIntentV0_1R1"][1])
    claim["outbox_intent_ref"] = intent["outbox_intent_ref"]; claim["outbox_intent_fingerprint"] = intent["canonical_fingerprint"]
    claim_id = wrong if target == "claim_id" else h("agents-os.f5-outbox-claim-id.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"])
    token = wrong if target == "claim_fencing_token" else h("agents-os.f5-outbox-claim-fence.v0.1", claim["outbox_intent_fingerprint"], claim["claim_epoch"], claim["claimant_assessment_fingerprint"])
    claim["claim_id"] = claim_id; claim["claim_ref"] = "outbox-claim:" + claim_id; claim["claim_fencing_token"] = token; claim["canonical_fingerprint"] = object_fingerprint(claim, META["F5OutboxClaimFactV0_1R1"][2], META["F5OutboxClaimFactV0_1R1"][1])
    request.update({"outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "claim_ref": claim["claim_ref"], "claim_fingerprint": claim["canonical_fingerprint"], "claim_fencing_token": token})
    attempt_id = wrong if target == "attempt_id" else h("agents-os.f5-delivery-attempt-id.v0.1", request["outbox_intent_fingerprint"], request["attempt_ordinal"])
    request_id = wrong if target == "dispatch_arm_request_id" else h("agents-os.f5-dispatch-arm-request-id.v0.1", request["outbox_intent_fingerprint"], request["invocation_identity_fingerprint"], request["attempt_ordinal"])
    request["attempt_id"] = attempt_id; request["dispatch_arm_request_id"] = request_id; request["canonical_fingerprint"] = object_fingerprint(request, META["F5DispatchArmRequestV0_1R2"][2], META["F5DispatchArmRequestV0_1R2"][1])
    arm.update({"dispatch_arm_request_id": request_id, "dispatch_arm_request_fingerprint": request["canonical_fingerprint"], "outbox_intent_ref": intent["outbox_intent_ref"], "outbox_intent_fingerprint": intent["canonical_fingerprint"], "claim_ref": claim["claim_ref"], "claim_fingerprint": claim["canonical_fingerprint"], "claim_fencing_token": token, "attempt_id": attempt_id})
    arm_id = wrong if target == "dispatch_arm_id" else h("agents-os.f5-dispatch-arm-id.v0.2", request_id)
    arm["dispatch_arm_id"] = arm_id; arm["dispatch_arm_ref"] = "dispatch-arm:" + arm_id; arm["canonical_fingerprint"] = object_fingerprint(arm, META["F5DispatchArmFactV0_1R2"][2], META["F5DispatchArmFactV0_1R2"][1])
    graph["derived_identities"] = {"outbox_intent_id": intent_id, "claim_id": claim_id, "claim_fencing_token": token, "attempt_id": attempt_id, "dispatch_arm_request_id": request_id, "dispatch_arm_id": arm_id}
    raw_resign_section(fixture, "identity_formula_graph"); raw_resign_root(fixture)


def rejected(fixture: dict[str, Any]) -> bool:
    try:
        validate_fixture(fixture, run_mutations=False)
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        return True
    return False


def mutation_checks(base: dict[str, Any]) -> dict[str, Any]:
    schema_mutations: list[dict[str, Any]] = []
    by_name = {row["schema_name"]: index for index, row in enumerate(base["schema_shape_examples"])}
    def shape_mut(name: str, field: str, value: Any) -> None:
        item = copy.deepcopy(base); index = by_name[name]; item["schema_shape_examples"][index]["object"][field] = value; raw_resign_shape(item, index); schema_mutations.append(item)
    shape_mut("F5OutboxIntentV0_1R1", "created_at_utc_ms", 1000.5)
    shape_mut("F5OutboxIntentV0_1R1", "created_event_sequence", SAFE_INTEGER + 1)
    shape_mut("F5OutboxIntentV0_1R1", "owner_host_id", "e\u0301")
    shape_mut("F5DeliveryReceiptV0_1R1", "receipt_kind", "UNRECOGNIZED_KIND")
    shape_mut("F5OutboxIntentV0_1R1", "created_event_sequence", "1000")
    shape_mut("F5OutboxClaimFactV0_1R1", "expected_previous_claim_epoch", 1)
    item = copy.deepcopy(base); index = by_name["F5OutboxIntentV0_1R1"]; item["schema_shape_examples"][index]["object"]["unknown_field"] = "x"; raw_resign_shape(item, index); schema_mutations.append(item)
    item = copy.deepcopy(base); item["unknown_root_field"] = "x"; raw_resign_root(item); schema_mutations.append(item)
    ensure(all(rejected(x) for x in schema_mutations), "a fully re-signed schema-invalid mutation was accepted")
    duplicate_probe = False
    try: parse_json_strict('{"a":1,"a":2}')
    except ValueError: duplicate_probe = True
    ensure(duplicate_probe, "duplicate JSON key probe accepted")

    graph_mutations: list[dict[str, Any]] = []
    for target in ("outbox_intent_id", "claim_id", "claim_fencing_token", "attempt_id", "dispatch_arm_request_id", "dispatch_arm_id"):
        item = copy.deepcopy(base); propagate_graph_with_override(item, target); graph_mutations.append(item)
    ensure(all(rejected(x) for x in graph_mutations), "a coherent graph-level formula mutation was accepted")

    proof_mutations: list[dict[str, Any]] = []
    item = copy.deepcopy(base); item["precedence_ordering_trials"][0]["derived"]["primary_reason"] = item["precedence_ordering_trials"][0]["raw_conditions"][1]["reason"]; raw_resign_section(item, "precedence_ordering_trials"); raw_resign_root(item); proof_mutations.append(item)
    item = copy.deepcopy(base); item["arm_state_derivation_cases"][1]["derived"]["modeled_call_authorization_delta"] = 1; raw_resign_section(item, "arm_state_derivation_cases"); raw_resign_root(item); proof_mutations.append(item)
    item = copy.deepcopy(base); item["receipt_compatibility_cases"][0]["derived_compatibility"] = "APPLIED"; raw_resign_section(item, "receipt_compatibility_cases"); raw_resign_root(item); proof_mutations.append(item)
    item = copy.deepcopy(base); item["receipt_currentness_cases"][0]["raw_input"]["epoch_current"] = False; raw_resign_section(item, "receipt_currentness_cases"); raw_resign_root(item); proof_mutations.append(item)
    item = copy.deepcopy(base); item["transition_cases"][0]["derived"] = "ALLOWED" if item["transition_cases"][0]["derived"] != "ALLOWED" else "REJECTED_TRANSITION_INVALID"; raw_resign_section(item, "transition_cases"); raw_resign_root(item); proof_mutations.append(item)
    item = copy.deepcopy(base); item["synthetic_nonauthority_scenario"]["derived"]["physical_call_authorized"] = True; raw_resign_section(item, "synthetic_nonauthority_scenario"); raw_resign_root(item); proof_mutations.append(item)
    ensure(all(rejected(x) for x in proof_mutations), "a fully re-signed proof mutation was accepted")
    return {"schema_invalid_resigned_mutations_rejected": len(schema_mutations), "graph_level_identity_mutations_rejected": len(graph_mutations), "proof_mutations_rejected": len(proof_mutations), "duplicate_key_probe_rejected": True}


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    try:
        fixture = parse_json_strict(path.read_text(encoding="utf-8"))
        result = validate_fixture(fixture)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "BLOCK", "error": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
