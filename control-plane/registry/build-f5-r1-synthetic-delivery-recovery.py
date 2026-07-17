#!/usr/bin/env python3
"""Build the fixed F5 R1 synthetic non-authority delivery/recovery fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FIXTURE_INTERFACE = "agents-os.f5-r1-synthetic-fixture.v0.1"
SYNTHETIC_DOMAIN = "agents-os.f5-r1-synthetic-witness.v0.1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


SCHEMAS: list[tuple[str, str, str, list[str]]] = [
    (
        "F5OutboxIntentV0_1R1",
        "agents-os.f5-outbox-intent.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "outbox_intent_id", "outbox_intent_ref",
            "source_handoff_ref", "source_handoff_fingerprint",
            "source_handoff_event_sequence", "invocation_identity_fingerprint",
            "effect_id", "effect_scope_ref", "effect_scope_fingerprint",
            "expected_result_contract_ref", "expected_result_contract_fingerprint",
            "owner_host_id", "execution_epoch", "task_fence_generation",
            "host_fence_generation", "effect_fence_generation",
            "start_authority_expires_at_utc_ms", "completion_blocking",
            "delivery_profile_ref", "delivery_profile_fingerprint",
            "created_at_utc_ms", "created_event_sequence", "environment",
            "authority_eligible", "canonical_fingerprint",
        ],
    ),
    (
        "F5EnqueueDispositionV0_1R1",
        "agents-os.f5-enqueue-disposition.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "source_handoff_ref", "source_handoff_fingerprint",
            "outbox_intent_ref", "outbox_intent_fingerprint", "result",
            "primary_reason", "reason_codes", "observed_at_utc_ms",
            "observed_event_sequence", "canonical_fingerprint",
        ],
    ),
    (
        "F5DispatcherClaimantAssessmentV0_1R1",
        "agents-os.f5-dispatcher-claimant-assessment.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "dispatcher_actor_id", "dispatcher_actor_identity_ref",
            "dispatcher_actor_identity_fingerprint", "dispatcher_principal_id",
            "dispatcher_principal_ref", "dispatcher_principal_fingerprint",
            "dispatcher_binding_assessment_ref", "dispatcher_binding_assessment_fingerprint",
            "resident_authority_epoch", "resident_continuity_assessment_ref",
            "resident_continuity_assessment_fingerprint", "owner_head_event_sequence",
            "assessed_at_event_sequence", "result", "environment",
            "authority_eligible", "canonical_fingerprint",
        ],
    ),
    (
        "F5PhysicalBoundaryAuthorityObservationV0_1R1",
        "agents-os.f5-physical-boundary-authority-observation.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "observation_purpose", "outbox_intent_ref", "outbox_intent_fingerprint",
            "source_handoff_ref", "source_handoff_fingerprint",
            "fresh_F4_assessment_ref", "fresh_F4_assessment_fingerprint",
            "fresh_F4_assessment_result", "observed_task_fence_generation",
            "observed_host_fence_generation", "observed_effect_fence_generation",
            "observed_execution_epoch", "observed_host_id", "observed_at_utc_ms",
            "observed_event_sequence", "canonical_writer_head_event_sequence",
            "result", "primary_reason", "reason_codes", "canonical_fingerprint",
        ],
    ),
    (
        "F5OutboxClaimFactV0_1R1",
        "agents-os.f5-outbox-claim-fact.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "claim_id", "claim_ref", "outbox_intent_ref",
            "outbox_intent_fingerprint", "claim_epoch", "expected_previous_claim_epoch",
            "claimant_assessment_ref", "claimant_assessment_fingerprint",
            "claim_authority_observation_ref", "claim_authority_observation_fingerprint",
            "lease_expires_at_utc_ms", "claim_fencing_token", "claimed_at_utc_ms",
            "claim_event_sequence", "result", "primary_reason", "reason_codes",
            "canonical_fingerprint",
        ],
    ),
    (
        "F5OutboxLeaseFactV0_1R1",
        "agents-os.f5-outbox-lease-fact.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "lease_fact_id", "claim_ref", "claim_fingerprint",
            "claim_epoch", "claim_fencing_token", "previous_lease_expiry_utc_ms",
            "new_lease_expiry_utc_ms", "renewed_at_utc_ms", "renewal_event_sequence",
            "result", "primary_reason", "reason_codes", "canonical_fingerprint",
        ],
    ),
    (
        "F5DispatchArmFactV0_1R1",
        "agents-os.f5-dispatch-arm-fact.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "dispatch_arm_id", "dispatch_arm_ref",
            "outbox_intent_ref", "outbox_intent_fingerprint", "claim_ref",
            "claim_fingerprint", "claim_epoch", "claim_fencing_token",
            "attempt_ordinal", "attempt_id", "idempotency_key",
            "physical_boundary_observation_ref",
            "physical_boundary_observation_fingerprint", "armed_at_utc_ms",
            "armed_event_sequence", "arm_transaction_ref",
            "arm_transaction_fingerprint", "result", "primary_reason",
            "reason_codes", "canonical_fingerprint",
        ],
    ),
    (
        "F5DeliveryAttemptFactV0_1R1",
        "agents-os.f5-delivery-attempt-fact.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "attempt_id", "attempt_ref", "dispatch_arm_ref",
            "dispatch_arm_fingerprint", "outbox_intent_ref",
            "outbox_intent_fingerprint", "attempt_ordinal", "idempotency_key",
            "transport_profile_ref", "transport_profile_fingerprint",
            "started_at_utc_ms", "returned_at_utc_ms", "outcome",
            "outcome_evidence_ref", "outcome_evidence_fingerprint",
            "effect_may_have_occurred", "automatic_retry_eligible",
            "attempt_event_sequence", "canonical_fingerprint",
        ],
    ),
    (
        "F5DeliveryReceiptV0_1R1",
        "agents-os.f5-delivery-receipt.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "receipt_id", "source_id",
            "source_receipt_revision", "attempt_ref", "attempt_fingerprint",
            "outbox_intent_ref", "outbox_intent_fingerprint", "effect_id",
            "invocation_identity_fingerprint", "execution_epoch",
            "host_fence_generation", "effect_fence_generation", "receipt_kind",
            "effect_status", "observed_at_utc_ms", "received_at_utc_ms",
            "source_attestation_ref", "source_attestation_fingerprint",
            "canonical_fingerprint",
        ],
    ),
    (
        "F5DeadLetterFactV0_1R1",
        "agents-os.f5-dead-letter-fact.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "dead_letter_id", "outbox_intent_ref",
            "outbox_intent_fingerprint", "last_claim_ref", "last_claim_fingerprint",
            "last_attempt_ref", "last_attempt_fingerprint", "reason",
            "effect_outcome", "reconciliation_required", "dead_lettered_at_utc_ms",
            "dead_letter_event_sequence", "canonical_fingerprint",
        ],
    ),
    (
        "F5ReconciliationCaseV0_1R1",
        "agents-os.f5-reconciliation-case.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "reconciliation_id", "outbox_intent_ref",
            "outbox_intent_fingerprint", "attempt_ref", "attempt_fingerprint",
            "reason", "status", "resolution", "evidence_refs",
            "evidence_set_fingerprint", "owner_next_action", "opened_event_sequence",
            "last_updated_event_sequence", "canonical_fingerprint",
        ],
    ),
    (
        "F5OutboxProjectionV0_1R1",
        "agents-os.f5-outbox-projection.v0.1-r1",
        "projection_fingerprint",
        [
            "interface_version", "outbox_intent_ref", "outbox_intent_fingerprint",
            "projection_version", "last_event_sequence", "state",
            "current_claim_ref", "current_claim_fingerprint", "current_attempt_ref",
            "current_attempt_fingerprint", "current_reconciliation_ref",
            "current_reconciliation_fingerprint", "effect_outcome",
            "automatic_retry_eligible", "completion_blocking",
            "projection_fingerprint",
        ],
    ),
    (
        "F5SyntheticDeliveryRecoveryWitnessV0_1R1",
        "agents-os.f5-synthetic-delivery-recovery-witness.v0.1-r1",
        "canonical_fingerprint",
        [
            "interface_version", "witness_ref", "witness_namespace", "environment",
            "fingerprint_domain", "prospective_F4_handoff_requirement_ref",
            "prospective_F4_handoff_requirement_fingerprint",
            "vector_set_fingerprint", "authority_eligible", "runtime_consumable",
            "recovery_importable", "physical_effect_boundary", "terminal_outcome",
            "accepted_real_handoff_count", "armed_dispatch_count",
            "external_effect_count", "provider_call_count", "raw_secret_count",
            "canonical_fingerprint",
        ],
    ),
]


def schema_profiles() -> list[dict[str, Any]]:
    result = []
    for name, interface, fingerprint_field, fields in SCHEMAS:
        profile = {
            "schema_name": name,
            "interface_version": interface,
            "fingerprint_field": fingerprint_field,
            "fields": fields,
        }
        profile["schema_profile_fingerprint"] = digest(
            [SYNTHETIC_DOMAIN, "schema-profile", name, interface, fingerprint_field, fields]
        )
        result.append(profile)
    return result


def first_reason(facts: dict[str, bool], precedence: list[str]) -> str:
    for reason in precedence:
        if facts.get(reason, False):
            return reason
    raise ValueError("vector has no true reason")


def reason_codes(
    facts: dict[str, bool], primary: str, positive_reasons: set[str]
) -> list[str]:
    return sorted(
        reason
        for reason, active in facts.items()
        if active and (reason not in positive_reasons or reason == primary)
    )


def evaluate(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    if kind == "enqueue":
        facts = {
            "INTEGRITY_FAILURE": not data["integrity"],
            "SYNTHETIC_INPUT": data["synthetic"],
            "HANDOFF_INVALID": not data["handoff_valid"],
            "HANDOFF_ALREADY_CONSUMED": data["already_consumed"],
            "HANDOFF_EXPIRED": data["expired"],
            "HANDOFF_UNAVAILABLE": not data["available"],
            "ENQUEUED_REPLAY": data["identical_replay"],
            "ENQUEUED_NEW": True,
        }
        order = [
            "INTEGRITY_FAILURE", "SYNTHETIC_INPUT", "HANDOFF_INVALID",
            "HANDOFF_ALREADY_CONSUMED", "HANDOFF_EXPIRED", "HANDOFF_UNAVAILABLE",
            "ENQUEUED_REPLAY", "ENQUEUED_NEW",
        ]
        primary = first_reason(facts, order)
        result = "ENQUEUED" if primary.startswith("ENQUEUED_") else (
            "INDETERMINATE" if primary == "HANDOFF_UNAVAILABLE" else "NOT_EXECUTABLE"
        )
        return {
            "result": result,
            "primary_reason": primary,
            "reason_codes": reason_codes(
                facts, primary, {"ENQUEUED_REPLAY", "ENQUEUED_NEW"}
            ),
        }

    if kind == "claim":
        facts = {
            "INTEGRITY_FAILURE": not data["integrity"],
            "SYNTHETIC_INPUT": data["synthetic"],
            "TERMINAL_ALREADY_RECORDED": data["terminal"],
            "DISPATCH_ALREADY_ARMED": data["arm_exists"],
            "CLAIM_ALREADY_ACTIVE": data["active_claim"],
            "INTENT_NOT_PENDING": data["state"] != "PENDING" and not (
                data["state"] == "CLAIMED" and data["safe_expired_reclaim"]
            ),
            "CLAIMANT_STALE": data["claimant_result"] == "STALE",
            "CLAIMANT_UNAVAILABLE": data["claimant_result"] == "INDETERMINATE",
            "AUTHORITY_STALE": data["authority_result"] == "REJECTED",
            "AUTHORITY_UNAVAILABLE": data["authority_result"] == "INDETERMINATE",
            "EXPIRED": data["expired"],
            "CAS_MISMATCH": not data["cas_match"],
            "CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY": data["safe_expired_reclaim"],
            "CLAIMED_NEW": True,
        }
        order = [
            "INTEGRITY_FAILURE", "SYNTHETIC_INPUT", "TERMINAL_ALREADY_RECORDED",
            "DISPATCH_ALREADY_ARMED", "CLAIM_ALREADY_ACTIVE", "INTENT_NOT_PENDING",
            "CLAIMANT_STALE", "CLAIMANT_UNAVAILABLE", "AUTHORITY_STALE",
            "AUTHORITY_UNAVAILABLE", "EXPIRED", "CAS_MISMATCH",
            "CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY", "CLAIMED_NEW",
        ]
        primary = first_reason(facts, order)
        if primary in {"CLAIMANT_UNAVAILABLE", "AUTHORITY_UNAVAILABLE"}:
            return {
                "result": "INDETERMINATE",
                "primary_reason": primary,
                "reason_codes": reason_codes(
                    facts, primary,
                    {"CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY", "CLAIMED_NEW"},
                ),
            }
        return {
            "result": "CLAIMED" if primary.startswith("CLAIMED_") else "NOT_EXECUTABLE",
            "primary_reason": primary,
            "reason_codes": reason_codes(
                facts, primary, {"CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY", "CLAIMED_NEW"}
            ),
        }

    if kind == "lease":
        facts = {
            "INTEGRITY_FAILURE": not data["integrity"],
            "CLAIM_STALE": not data["claim_current"],
            "TOKEN_MISMATCH": not data["token_match"],
            "DISPATCH_ALREADY_ARMED": data["arm_exists"],
            "EXPIRED": data["expired"],
            "CAS_MISMATCH": not data["cas_match"],
            "RENEWED": True,
        }
        order = [
            "INTEGRITY_FAILURE", "CLAIM_STALE", "TOKEN_MISMATCH",
            "DISPATCH_ALREADY_ARMED", "EXPIRED", "CAS_MISMATCH", "RENEWED",
        ]
        primary = first_reason(facts, order)
        return {
            "result": "RENEWED" if primary == "RENEWED" else "REJECTED",
            "primary_reason": primary,
            "reason_codes": reason_codes(facts, primary, {"RENEWED"}),
        }

    if kind == "arm":
        facts = {
            "INTEGRITY_FAILURE": not data["integrity"],
            "SYNTHETIC_INPUT": data["synthetic"],
            "TERMINAL_ALREADY_RECORDED": data["terminal"],
            "ALREADY_ARMED": data["already_armed"],
            "CLAIM_STALE": not data["claim_current"],
            "TOKEN_MISMATCH": not data["token_match"],
            "AUTHORITY_STALE": data["authority_result"] == "REJECTED",
            "FENCED": data["fenced"],
            "EPOCH_STALE": not data["epoch_match"],
            "HOST_MISMATCH": not data["host_match"],
            "EXPIRED": data["expired"],
            "OBSERVATION_UNAVAILABLE": data["authority_result"] == "INDETERMINATE",
            "CAS_MISMATCH": not data["cas_match"],
            "ARMED": True,
        }
        order = [
            "INTEGRITY_FAILURE", "SYNTHETIC_INPUT", "TERMINAL_ALREADY_RECORDED",
            "ALREADY_ARMED", "CLAIM_STALE", "TOKEN_MISMATCH", "AUTHORITY_STALE",
            "FENCED", "EPOCH_STALE", "HOST_MISMATCH", "EXPIRED",
            "OBSERVATION_UNAVAILABLE", "CAS_MISMATCH", "ARMED",
        ]
        primary = first_reason(facts, order)
        result = "ARMED" if primary == "ARMED" else (
            "INDETERMINATE" if primary == "OBSERVATION_UNAVAILABLE" else "NOT_EXECUTABLE"
        )
        return {
            "result": result,
            "primary_reason": primary,
            "reason_codes": reason_codes(facts, primary, {"ARMED"}),
        }

    if kind == "attempt":
        outcome = data["outcome"]
        if outcome == "PRE_EFFECT_NOT_EXECUTED":
            return {
                "effect_may_have_occurred": False,
                "automatic_retry_eligible": False,
            }
        if outcome in {"DISPATCHED", "ACKED", "SUCCEEDED", "FAILED", "UNKNOWN"}:
            return {"effect_may_have_occurred": True, "automatic_retry_eligible": False}
        raise ValueError(f"unknown attempt outcome: {outcome}")

    if kind == "receipt":
        mode = data["mode"]
        if mode == "NEW":
            return {"result": "APPLIED", "event_created": True, "reconciliation_opened": False}
        if mode == "EXACT_DUPLICATE":
            return {"result": "REPLAYED", "event_created": False, "reconciliation_opened": False}
        if mode == "CHANGED_SAME_KEY":
            return {"result": "CONFLICT", "event_created": True, "reconciliation_opened": True}
        raise ValueError(f"unknown receipt mode: {mode}")

    if kind == "recovery":
        decisions = {
            "HANDOFF_COMMITTED_INTENT_ABSENT": "DETERMINISTIC_ENQUEUE_NO_EFFECT",
            "INTENT_COMMITTED_CLAIM_ABSENT": "REMAIN_PENDING",
            "CLAIM_COMMITTED_ARM_ABSENT": "RECLAIM_ONLY_AFTER_EXPIRY_AND_RECHECK",
            "ARM_COMMITTED_CALL_UNCERTAIN": "UNKNOWN_NO_AUTOMATIC_RETRY",
            "CALL_RETURNED_RECEIPT_ABSENT": "UNKNOWN_AWAIT_RECEIPT_OR_QUERY",
            "RECEIPT_COMMITTED_PROJECTION_ABSENT": "REBUILD_PROJECTION_NO_EFFECT",
            "DEAD_LETTER_PROJECTION_ABSENT": "REBUILD_WITH_OUTCOME_NOT_PROVEN",
            "RECONCILIATION_REPLY_LOST": "REPLAY_FIRST_UPDATE",
        }
        return {"decision": decisions[data["window"]]}

    raise ValueError(f"unknown vector kind: {kind}")


def vector(vector_id: str, kind: str, data: dict[str, Any]) -> dict[str, Any]:
    result = {
        "vector_id": vector_id,
        "kind": kind,
        "input": data,
        "expected": evaluate(kind, data),
    }
    result["canonical_fingerprint"] = digest(
        [SYNTHETIC_DOMAIN, "decision-vector", vector_id, kind, data, result["expected"]]
    )
    return result


def vectors() -> list[dict[str, Any]]:
    base_enqueue = {
        "integrity": True, "synthetic": False, "handoff_valid": True,
        "already_consumed": False, "expired": False, "available": True,
        "identical_replay": False,
    }
    base_claim = {
        "integrity": True, "synthetic": False, "state": "PENDING",
        "active_claim": False, "arm_exists": False, "terminal": False,
        "claimant_result": "CURRENT", "authority_result": "CURRENT",
        "expired": False, "cas_match": True, "safe_expired_reclaim": False,
    }
    base_lease = {
        "integrity": True, "claim_current": True, "token_match": True,
        "arm_exists": False, "expired": False, "cas_match": True,
    }
    base_arm = {
        "integrity": True, "synthetic": False, "claim_current": True,
        "token_match": True, "already_armed": False, "terminal": False,
        "authority_result": "CURRENT", "fenced": False, "epoch_match": True,
        "host_match": True, "expired": False, "cas_match": True,
    }

    result: list[dict[str, Any]] = []

    for vector_id, changes in [
        ("ENQUEUE_NEW", {}),
        ("ENQUEUE_REPLAY", {"identical_replay": True}),
        ("ENQUEUE_SYNTHETIC", {"synthetic": True}),
        ("ENQUEUE_INVALID", {"handoff_valid": False}),
        ("ENQUEUE_ALREADY_CONSUMED", {"already_consumed": True}),
        ("ENQUEUE_EXPIRED", {"expired": True}),
        ("ENQUEUE_UNAVAILABLE", {"available": False}),
        ("ENQUEUE_INTEGRITY", {"integrity": False}),
        ("ENQUEUE_MULTI_FAILURE_PRECEDENCE", {"integrity": False, "synthetic": True, "expired": True}),
    ]:
        data = dict(base_enqueue); data.update(changes)
        result.append(vector(vector_id, "enqueue", data))

    for vector_id, changes in [
        ("CLAIM_NEW", {}),
        ("CLAIM_SAFE_RECLAIM", {"safe_expired_reclaim": True, "state": "CLAIMED"}),
        ("CLAIM_SYNTHETIC", {"synthetic": True}),
        ("CLAIM_TERMINAL", {"terminal": True}),
        ("CLAIM_ALREADY_ACTIVE", {"active_claim": True}),
        ("CLAIM_AFTER_ARM", {"arm_exists": True}),
        ("CLAIM_INTENT_NOT_PENDING", {"state": "CLAIMED"}),
        ("CLAIM_CLAIMANT_STALE", {"claimant_result": "STALE"}),
        ("CLAIM_CLAIMANT_UNKNOWN", {"claimant_result": "INDETERMINATE"}),
        ("CLAIM_AUTHORITY_STALE", {"authority_result": "REJECTED"}),
        ("CLAIM_AUTHORITY_UNKNOWN", {"authority_result": "INDETERMINATE"}),
        ("CLAIM_EXPIRED", {"expired": True}),
        ("CLAIM_CAS_MISMATCH", {"cas_match": False}),
        ("CLAIM_INTEGRITY", {"integrity": False}),
        ("CLAIM_MULTI_FAILURE_PRECEDENCE", {"terminal": True, "arm_exists": True, "active_claim": True, "authority_result": "REJECTED"}),
    ]:
        data = dict(base_claim); data.update(changes)
        result.append(vector(vector_id, "claim", data))

    for vector_id, changes in [
        ("LEASE_RENEW", {}),
        ("LEASE_CLAIM_STALE", {"claim_current": False}),
        ("LEASE_STALE_TOKEN", {"token_match": False}),
        ("LEASE_AFTER_ARM", {"arm_exists": True}),
        ("LEASE_EXPIRED", {"expired": True}),
        ("LEASE_CAS_MISMATCH", {"cas_match": False}),
        ("LEASE_INTEGRITY", {"integrity": False}),
        ("LEASE_MULTI_FAILURE_PRECEDENCE", {"token_match": False, "arm_exists": True, "expired": True}),
    ]:
        data = dict(base_lease); data.update(changes)
        result.append(vector(vector_id, "lease", data))

    for vector_id, changes in [
        ("ARM_CURRENT", {}),
        ("ARM_SYNTHETIC", {"synthetic": True}),
        ("ARM_TERMINAL", {"terminal": True}),
        ("ARM_DUPLICATE", {"already_armed": True}),
        ("ARM_CLAIM_STALE", {"claim_current": False}),
        ("ARM_AUTHORITY_STALE", {"authority_result": "REJECTED"}),
        ("ARM_AUTHORITY_UNKNOWN", {"authority_result": "INDETERMINATE"}),
        ("ARM_FENCED", {"fenced": True}),
        ("ARM_EPOCH_STALE", {"epoch_match": False}),
        ("ARM_HOST_MISMATCH", {"host_match": False}),
        ("ARM_EXPIRED", {"expired": True}),
        ("ARM_TOKEN_MISMATCH", {"token_match": False}),
        ("ARM_CAS_MISMATCH", {"cas_match": False}),
        ("ARM_INTEGRITY", {"integrity": False}),
        ("ARM_MULTI_FAILURE_PRECEDENCE", {"authority_result": "REJECTED", "fenced": True, "expired": True}),
    ]:
        data = dict(base_arm); data.update(changes)
        result.append(vector(vector_id, "arm", data))

    for outcome in [
        "PRE_EFFECT_NOT_EXECUTED", "DISPATCHED", "ACKED", "SUCCEEDED", "FAILED", "UNKNOWN"
    ]:
        result.append(vector(
            f"ATTEMPT_{outcome}",
            "attempt",
            {"outcome": outcome, "profile_retryable": outcome == "PRE_EFFECT_NOT_EXECUTED"},
        ))

    for mode in ["NEW", "EXACT_DUPLICATE", "CHANGED_SAME_KEY"]:
        result.append(vector(f"RECEIPT_{mode}", "receipt", {"mode": mode}))

    for window in [
        "HANDOFF_COMMITTED_INTENT_ABSENT", "INTENT_COMMITTED_CLAIM_ABSENT",
        "CLAIM_COMMITTED_ARM_ABSENT", "ARM_COMMITTED_CALL_UNCERTAIN",
        "CALL_RETURNED_RECEIPT_ABSENT", "RECEIPT_COMMITTED_PROJECTION_ABSENT",
        "DEAD_LETTER_PROJECTION_ABSENT", "RECONCILIATION_REPLY_LOST",
    ]:
        result.append(vector(f"RECOVERY_{window}", "recovery", {"window": window}))

    return result


def build_fixture() -> dict[str, Any]:
    profiles = schema_profiles()
    decision_vectors = vectors()
    profile_set_fingerprint = digest(
        [SYNTHETIC_DOMAIN, "schema-profile-set", [p["schema_profile_fingerprint"] for p in profiles]]
    )
    vector_set_fingerprint = digest(
        [SYNTHETIC_DOMAIN, "decision-vector-set", [v["canonical_fingerprint"] for v in decision_vectors]]
    )
    prospective_requirement = {
        "interface_version": "agents-os.f5-prospective-f4-handoff-requirement.v0.1-r1",
        "requirement_ref": "synthetic-f5-r1:requirement:f4-handoff",
        "owner": "F4",
        "required_schema_name": "F4AcceptedEffectHandoffV0_1R9",
        "required_interface_version": "agents-os.f4-accepted-effect-handoff.v0.1-r9",
        "required_F4_manifest_sha256": "8648cb687608b1151c81d01582a1fb7a19a5811a66224abe621a25188dc30dd5",
        "status": "UNAVAILABLE_FOR_REAL_POSITIVE_HANDOFF",
        "usable_in_runtime": False,
        "synthetic_fixture_only": True,
        "authority_eligible": False,
    }
    prospective_requirement["canonical_fingerprint"] = digest(
        [SYNTHETIC_DOMAIN, "prospective-requirement", prospective_requirement]
    )
    witness = {
        "interface_version": "agents-os.f5-synthetic-delivery-recovery-witness.v0.1-r1",
        "witness_ref": "synthetic-f5-r1:witness:delivery-recovery",
        "witness_namespace": "synthetic-f5-r1",
        "environment": "SYNTHETIC_TEST",
        "fingerprint_domain": SYNTHETIC_DOMAIN,
        "prospective_F4_handoff_requirement_ref": prospective_requirement["requirement_ref"],
        "prospective_F4_handoff_requirement_fingerprint": prospective_requirement["canonical_fingerprint"],
        "vector_set_fingerprint": vector_set_fingerprint,
        "authority_eligible": False,
        "runtime_consumable": False,
        "recovery_importable": False,
        "physical_effect_boundary": "NOT_EXECUTABLE",
        "terminal_outcome": "NOT_EXECUTED",
        "accepted_real_handoff_count": 0,
        "armed_dispatch_count": 0,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
    }
    witness["canonical_fingerprint"] = digest(
        [SYNTHETIC_DOMAIN, "witness", witness]
    )
    fixture: dict[str, Any] = {
        "interface_version": FIXTURE_INTERFACE,
        "contract_version": "F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R1_ATOMIC_BUNDLE",
        "environment": "SYNTHETIC_TEST",
        "fingerprint_domain": SYNTHETIC_DOMAIN,
        "schema_profiles": profiles,
        "schema_profile_set_fingerprint": profile_set_fingerprint,
        "prospective_F4_handoff_requirement": prospective_requirement,
        "decision_vectors": decision_vectors,
        "synthetic_witness": witness,
        "assertions": {
            "accepted_real_handoff_count": 0,
            "armed_dispatch_count": 0,
            "runtime_consumable_count": 0,
            "external_effect_count": 0,
            "provider_call_count": 0,
            "raw_secret_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        },
        "summary": {
            "schema_profile_count": len(profiles),
            "decision_vector_count": len(decision_vectors),
            "recovery_vector_count": sum(v["kind"] == "recovery" for v in decision_vectors),
            "negative_or_fail_closed_vector_count": sum(
                v["expected"].get("result") in {"NOT_EXECUTABLE", "REJECTED", "INDETERMINATE", "CONFLICT"}
                or v["expected"].get("decision", "").startswith("UNKNOWN")
                for v in decision_vectors
            ),
        },
    }
    fixture["fixture_canonical_sha256"] = digest(
        [SYNTHETIC_DOMAIN, "fixture", fixture]
    )
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rendered = json.dumps(build_fixture(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
