#!/usr/bin/env python3
"""Independently validate the F5 R1 synthetic delivery/recovery fixture."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = ROOT / "control-plane" / "registry" / "examples" / "2026-07-17-agents-os-f5-r1-synthetic-delivery-recovery-v0.1.json"
DOMAIN = "agents-os.f5-r1-synthetic-witness.v0.1"


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


def fields(value: str) -> list[str]:
    return value.split()


EXPECTED_SCHEMAS: dict[str, tuple[str, str, list[str]]] = {
    "F5OutboxIntentV0_1R1": (
        "agents-os.f5-outbox-intent.v0.1-r1", "canonical_fingerprint",
        fields("interface_version outbox_intent_id outbox_intent_ref source_handoff_ref source_handoff_fingerprint source_handoff_event_sequence invocation_identity_fingerprint effect_id effect_scope_ref effect_scope_fingerprint expected_result_contract_ref expected_result_contract_fingerprint owner_host_id execution_epoch task_fence_generation host_fence_generation effect_fence_generation start_authority_expires_at_utc_ms completion_blocking delivery_profile_ref delivery_profile_fingerprint created_at_utc_ms created_event_sequence environment authority_eligible canonical_fingerprint"),
    ),
    "F5EnqueueDispositionV0_1R1": (
        "agents-os.f5-enqueue-disposition.v0.1-r1", "canonical_fingerprint",
        fields("interface_version source_handoff_ref source_handoff_fingerprint outbox_intent_ref outbox_intent_fingerprint result primary_reason reason_codes observed_at_utc_ms observed_event_sequence canonical_fingerprint"),
    ),
    "F5DispatcherClaimantAssessmentV0_1R1": (
        "agents-os.f5-dispatcher-claimant-assessment.v0.1-r1", "canonical_fingerprint",
        fields("interface_version dispatcher_actor_id dispatcher_actor_identity_ref dispatcher_actor_identity_fingerprint dispatcher_principal_id dispatcher_principal_ref dispatcher_principal_fingerprint dispatcher_binding_assessment_ref dispatcher_binding_assessment_fingerprint resident_authority_epoch resident_continuity_assessment_ref resident_continuity_assessment_fingerprint owner_head_event_sequence assessed_at_event_sequence result environment authority_eligible canonical_fingerprint"),
    ),
    "F5PhysicalBoundaryAuthorityObservationV0_1R1": (
        "agents-os.f5-physical-boundary-authority-observation.v0.1-r1", "canonical_fingerprint",
        fields("interface_version observation_purpose outbox_intent_ref outbox_intent_fingerprint source_handoff_ref source_handoff_fingerprint fresh_F4_assessment_ref fresh_F4_assessment_fingerprint fresh_F4_assessment_result observed_task_fence_generation observed_host_fence_generation observed_effect_fence_generation observed_execution_epoch observed_host_id observed_at_utc_ms observed_event_sequence canonical_writer_head_event_sequence result primary_reason reason_codes canonical_fingerprint"),
    ),
    "F5OutboxClaimFactV0_1R1": (
        "agents-os.f5-outbox-claim-fact.v0.1-r1", "canonical_fingerprint",
        fields("interface_version claim_id claim_ref outbox_intent_ref outbox_intent_fingerprint claim_epoch expected_previous_claim_epoch claimant_assessment_ref claimant_assessment_fingerprint claim_authority_observation_ref claim_authority_observation_fingerprint lease_expires_at_utc_ms claim_fencing_token claimed_at_utc_ms claim_event_sequence result primary_reason reason_codes canonical_fingerprint"),
    ),
    "F5OutboxLeaseFactV0_1R1": (
        "agents-os.f5-outbox-lease-fact.v0.1-r1", "canonical_fingerprint",
        fields("interface_version lease_fact_id claim_ref claim_fingerprint claim_epoch claim_fencing_token previous_lease_expiry_utc_ms new_lease_expiry_utc_ms renewed_at_utc_ms renewal_event_sequence result primary_reason reason_codes canonical_fingerprint"),
    ),
    "F5DispatchArmFactV0_1R1": (
        "agents-os.f5-dispatch-arm-fact.v0.1-r1", "canonical_fingerprint",
        fields("interface_version dispatch_arm_id dispatch_arm_ref outbox_intent_ref outbox_intent_fingerprint claim_ref claim_fingerprint claim_epoch claim_fencing_token attempt_ordinal attempt_id idempotency_key physical_boundary_observation_ref physical_boundary_observation_fingerprint armed_at_utc_ms armed_event_sequence arm_transaction_ref arm_transaction_fingerprint result primary_reason reason_codes canonical_fingerprint"),
    ),
    "F5DeliveryAttemptFactV0_1R1": (
        "agents-os.f5-delivery-attempt-fact.v0.1-r1", "canonical_fingerprint",
        fields("interface_version attempt_id attempt_ref dispatch_arm_ref dispatch_arm_fingerprint outbox_intent_ref outbox_intent_fingerprint attempt_ordinal idempotency_key transport_profile_ref transport_profile_fingerprint started_at_utc_ms returned_at_utc_ms outcome outcome_evidence_ref outcome_evidence_fingerprint effect_may_have_occurred automatic_retry_eligible attempt_event_sequence canonical_fingerprint"),
    ),
    "F5DeliveryReceiptV0_1R1": (
        "agents-os.f5-delivery-receipt.v0.1-r1", "canonical_fingerprint",
        fields("interface_version receipt_id source_id source_receipt_revision attempt_ref attempt_fingerprint outbox_intent_ref outbox_intent_fingerprint effect_id invocation_identity_fingerprint execution_epoch host_fence_generation effect_fence_generation receipt_kind effect_status observed_at_utc_ms received_at_utc_ms source_attestation_ref source_attestation_fingerprint canonical_fingerprint"),
    ),
    "F5DeadLetterFactV0_1R1": (
        "agents-os.f5-dead-letter-fact.v0.1-r1", "canonical_fingerprint",
        fields("interface_version dead_letter_id outbox_intent_ref outbox_intent_fingerprint last_claim_ref last_claim_fingerprint last_attempt_ref last_attempt_fingerprint reason effect_outcome reconciliation_required dead_lettered_at_utc_ms dead_letter_event_sequence canonical_fingerprint"),
    ),
    "F5ReconciliationCaseV0_1R1": (
        "agents-os.f5-reconciliation-case.v0.1-r1", "canonical_fingerprint",
        fields("interface_version reconciliation_id outbox_intent_ref outbox_intent_fingerprint attempt_ref attempt_fingerprint reason status resolution evidence_refs evidence_set_fingerprint owner_next_action opened_event_sequence last_updated_event_sequence canonical_fingerprint"),
    ),
    "F5OutboxProjectionV0_1R1": (
        "agents-os.f5-outbox-projection.v0.1-r1", "projection_fingerprint",
        fields("interface_version outbox_intent_ref outbox_intent_fingerprint projection_version last_event_sequence state current_claim_ref current_claim_fingerprint current_attempt_ref current_attempt_fingerprint current_reconciliation_ref current_reconciliation_fingerprint effect_outcome automatic_retry_eligible completion_blocking projection_fingerprint"),
    ),
    "F5SyntheticDeliveryRecoveryWitnessV0_1R1": (
        "agents-os.f5-synthetic-delivery-recovery-witness.v0.1-r1", "canonical_fingerprint",
        fields("interface_version witness_ref witness_namespace environment fingerprint_domain prospective_F4_handoff_requirement_ref prospective_F4_handoff_requirement_fingerprint vector_set_fingerprint authority_eligible runtime_consumable recovery_importable physical_effect_boundary terminal_outcome accepted_real_handoff_count armed_dispatch_count external_effect_count provider_call_count raw_secret_count canonical_fingerprint"),
    ),
}


REQUIRED_VECTOR_IDS = set(fields(
    "ENQUEUE_NEW ENQUEUE_REPLAY ENQUEUE_SYNTHETIC ENQUEUE_INVALID ENQUEUE_ALREADY_CONSUMED ENQUEUE_EXPIRED ENQUEUE_UNAVAILABLE ENQUEUE_INTEGRITY ENQUEUE_MULTI_FAILURE_PRECEDENCE "
    "CLAIM_NEW CLAIM_SAFE_RECLAIM CLAIM_SYNTHETIC CLAIM_TERMINAL CLAIM_ALREADY_ACTIVE CLAIM_AFTER_ARM CLAIM_INTENT_NOT_PENDING CLAIM_CLAIMANT_STALE CLAIM_CLAIMANT_UNKNOWN CLAIM_AUTHORITY_STALE CLAIM_AUTHORITY_UNKNOWN CLAIM_EXPIRED CLAIM_CAS_MISMATCH CLAIM_INTEGRITY CLAIM_MULTI_FAILURE_PRECEDENCE "
    "LEASE_RENEW LEASE_CLAIM_STALE LEASE_STALE_TOKEN LEASE_AFTER_ARM LEASE_EXPIRED LEASE_CAS_MISMATCH LEASE_INTEGRITY LEASE_MULTI_FAILURE_PRECEDENCE "
    "ARM_CURRENT ARM_SYNTHETIC ARM_TERMINAL ARM_DUPLICATE ARM_CLAIM_STALE ARM_AUTHORITY_STALE ARM_AUTHORITY_UNKNOWN ARM_FENCED ARM_EPOCH_STALE ARM_HOST_MISMATCH ARM_EXPIRED ARM_TOKEN_MISMATCH ARM_CAS_MISMATCH ARM_INTEGRITY ARM_MULTI_FAILURE_PRECEDENCE "
    "ATTEMPT_PRE_EFFECT_NOT_EXECUTED ATTEMPT_DISPATCHED ATTEMPT_ACKED ATTEMPT_SUCCEEDED ATTEMPT_FAILED ATTEMPT_UNKNOWN "
    "RECEIPT_NEW RECEIPT_EXACT_DUPLICATE RECEIPT_CHANGED_SAME_KEY "
    "RECOVERY_HANDOFF_COMMITTED_INTENT_ABSENT RECOVERY_INTENT_COMMITTED_CLAIM_ABSENT RECOVERY_CLAIM_COMMITTED_ARM_ABSENT RECOVERY_ARM_COMMITTED_CALL_UNCERTAIN RECOVERY_CALL_RETURNED_RECEIPT_ABSENT RECOVERY_RECEIPT_COMMITTED_PROJECTION_ABSENT RECOVERY_DEAD_LETTER_PROJECTION_ABSENT RECOVERY_RECONCILIATION_REPLY_LOST"
))


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reason_codes(facts_map: dict[str, bool], primary: str, positive: set[str]) -> list[str]:
    return sorted(
        key for key, active in facts_map.items()
        if active and (key not in positive or key == primary)
    )


def choose(facts_map: dict[str, bool], order: list[str]) -> str:
    return next(reason for reason in order if facts_map.get(reason, False))


def independent_reduce(kind: str, data: dict[str, Any]) -> dict[str, Any]:
    if kind == "enqueue":
        facts_map = {
            "INTEGRITY_FAILURE": not data["integrity"],
            "SYNTHETIC_INPUT": data["synthetic"],
            "HANDOFF_INVALID": not data["handoff_valid"],
            "HANDOFF_ALREADY_CONSUMED": data["already_consumed"],
            "HANDOFF_EXPIRED": data["expired"],
            "HANDOFF_UNAVAILABLE": not data["available"],
            "ENQUEUED_REPLAY": data["identical_replay"],
            "ENQUEUED_NEW": True,
        }
        order = fields("INTEGRITY_FAILURE SYNTHETIC_INPUT HANDOFF_INVALID HANDOFF_ALREADY_CONSUMED HANDOFF_EXPIRED HANDOFF_UNAVAILABLE ENQUEUED_REPLAY ENQUEUED_NEW")
        primary = choose(facts_map, order)
        result = "ENQUEUED" if primary.startswith("ENQUEUED_") else ("INDETERMINATE" if primary == "HANDOFF_UNAVAILABLE" else "NOT_EXECUTABLE")
        return {"result": result, "primary_reason": primary, "reason_codes": reason_codes(facts_map, primary, {"ENQUEUED_REPLAY", "ENQUEUED_NEW"})}

    if kind == "claim":
        facts_map = {
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
        order = fields("INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED DISPATCH_ALREADY_ARMED CLAIM_ALREADY_ACTIVE INTENT_NOT_PENDING CLAIMANT_STALE CLAIMANT_UNAVAILABLE AUTHORITY_STALE AUTHORITY_UNAVAILABLE EXPIRED CAS_MISMATCH CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY CLAIMED_NEW")
        primary = choose(facts_map, order)
        if primary in {"CLAIMANT_UNAVAILABLE", "AUTHORITY_UNAVAILABLE"}:
            return {
                "result": "INDETERMINATE",
                "primary_reason": primary,
                "reason_codes": reason_codes(
                    facts_map, primary,
                    {"CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY", "CLAIMED_NEW"},
                ),
            }
        return {
            "result": "CLAIMED" if primary.startswith("CLAIMED_") else "NOT_EXECUTABLE",
            "primary_reason": primary,
            "reason_codes": reason_codes(facts_map, primary, {"CLAIMED_AFTER_SAFE_PRE_ARM_LEASE_EXPIRY", "CLAIMED_NEW"}),
        }

    if kind == "lease":
        facts_map = {
            "INTEGRITY_FAILURE": not data["integrity"],
            "CLAIM_STALE": not data["claim_current"],
            "TOKEN_MISMATCH": not data["token_match"],
            "DISPATCH_ALREADY_ARMED": data["arm_exists"],
            "EXPIRED": data["expired"],
            "CAS_MISMATCH": not data["cas_match"],
            "RENEWED": True,
        }
        primary = choose(facts_map, fields("INTEGRITY_FAILURE CLAIM_STALE TOKEN_MISMATCH DISPATCH_ALREADY_ARMED EXPIRED CAS_MISMATCH RENEWED"))
        return {"result": "RENEWED" if primary == "RENEWED" else "REJECTED", "primary_reason": primary, "reason_codes": reason_codes(facts_map, primary, {"RENEWED"})}

    if kind == "arm":
        facts_map = {
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
        order = fields("INTEGRITY_FAILURE SYNTHETIC_INPUT TERMINAL_ALREADY_RECORDED ALREADY_ARMED CLAIM_STALE TOKEN_MISMATCH AUTHORITY_STALE FENCED EPOCH_STALE HOST_MISMATCH EXPIRED OBSERVATION_UNAVAILABLE CAS_MISMATCH ARMED")
        primary = choose(facts_map, order)
        result = "ARMED" if primary == "ARMED" else ("INDETERMINATE" if primary == "OBSERVATION_UNAVAILABLE" else "NOT_EXECUTABLE")
        return {"result": result, "primary_reason": primary, "reason_codes": reason_codes(facts_map, primary, {"ARMED"})}

    if kind == "attempt":
        outcome = data["outcome"]
        ensure(outcome in {"PRE_EFFECT_NOT_EXECUTED", "DISPATCHED", "ACKED", "SUCCEEDED", "FAILED", "UNKNOWN"}, "unknown attempt outcome")
        if outcome == "PRE_EFFECT_NOT_EXECUTED":
            return {"effect_may_have_occurred": False, "automatic_retry_eligible": False}
        return {"effect_may_have_occurred": True, "automatic_retry_eligible": False}

    if kind == "receipt":
        table = {
            "NEW": {"result": "APPLIED", "event_created": True, "reconciliation_opened": False},
            "EXACT_DUPLICATE": {"result": "REPLAYED", "event_created": False, "reconciliation_opened": False},
            "CHANGED_SAME_KEY": {"result": "CONFLICT", "event_created": True, "reconciliation_opened": True},
        }
        ensure(data["mode"] in table, "unknown receipt mode")
        return table[data["mode"]]

    if kind == "recovery":
        table = {
            "HANDOFF_COMMITTED_INTENT_ABSENT": "DETERMINISTIC_ENQUEUE_NO_EFFECT",
            "INTENT_COMMITTED_CLAIM_ABSENT": "REMAIN_PENDING",
            "CLAIM_COMMITTED_ARM_ABSENT": "RECLAIM_ONLY_AFTER_EXPIRY_AND_RECHECK",
            "ARM_COMMITTED_CALL_UNCERTAIN": "UNKNOWN_NO_AUTOMATIC_RETRY",
            "CALL_RETURNED_RECEIPT_ABSENT": "UNKNOWN_AWAIT_RECEIPT_OR_QUERY",
            "RECEIPT_COMMITTED_PROJECTION_ABSENT": "REBUILD_PROJECTION_NO_EFFECT",
            "DEAD_LETTER_PROJECTION_ABSENT": "REBUILD_WITH_OUTCOME_NOT_PROVEN",
            "RECONCILIATION_REPLY_LOST": "REPLAY_FIRST_UPDATE",
        }
        ensure(data["window"] in table, "unknown recovery window")
        return {"decision": table[data["window"]]}

    raise ValueError("unknown vector kind")


def validate_scalar_tree(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        raise ValueError(f"float forbidden at {path}")
    if isinstance(value, str):
        ensure(unicodedata.normalize("NFC", value) == value, f"non-NFC string at {path}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            validate_scalar_tree(child, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, child in value.items():
            validate_scalar_tree(key, f"{path}.<key>")
            validate_scalar_tree(child, f"{path}.{key}")


def recompute_fixture_hash(fixture: dict[str, Any]) -> str:
    clone = copy.deepcopy(fixture)
    clone.pop("fixture_canonical_sha256", None)
    return digest([DOMAIN, "fixture", clone])


def validate_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    validate_scalar_tree(fixture)
    expected_root_keys = {
        "interface_version", "contract_version", "environment", "fingerprint_domain",
        "schema_profiles", "schema_profile_set_fingerprint",
        "prospective_F4_handoff_requirement", "decision_vectors",
        "synthetic_witness", "assertions", "summary", "fixture_canonical_sha256",
    }
    ensure(set(fixture) == expected_root_keys, "fixture root fields mismatch")
    ensure(fixture["interface_version"] == "agents-os.f5-r1-synthetic-fixture.v0.1", "fixture interface mismatch")
    ensure(fixture["contract_version"] == "F5_OUTBOX_DELIVERY_RECOVERY_V0_1_R1_ATOMIC_BUNDLE", "contract mismatch")
    ensure(fixture["environment"] == "SYNTHETIC_TEST", "fixture environment must be synthetic")
    ensure(fixture["fingerprint_domain"] == DOMAIN, "fixture domain mismatch")
    ensure(fixture["fixture_canonical_sha256"] == recompute_fixture_hash(fixture), "fixture canonical hash mismatch")

    profiles = fixture["schema_profiles"]
    ensure(len(profiles) == len(EXPECTED_SCHEMAS) == 13, "schema profile count mismatch")
    ensure(len({p["schema_name"] for p in profiles}) == len(profiles), "duplicate schema profile")
    actual_names = {p["schema_name"] for p in profiles}
    ensure(actual_names == set(EXPECTED_SCHEMAS), "schema profile names mismatch")
    for profile in profiles:
        ensure(set(profile) == {"schema_name", "interface_version", "fingerprint_field", "fields", "schema_profile_fingerprint"}, "schema profile fields mismatch")
        name = profile["schema_name"]
        interface, fingerprint_field, ordered_fields = EXPECTED_SCHEMAS[name]
        ensure(profile["interface_version"] == interface, f"{name} interface mismatch")
        ensure(profile["fingerprint_field"] == fingerprint_field, f"{name} fingerprint field mismatch")
        ensure(profile["fields"] == ordered_fields, f"{name} ordered fields mismatch")
        expected_fp = digest([DOMAIN, "schema-profile", name, interface, fingerprint_field, ordered_fields])
        ensure(profile["schema_profile_fingerprint"] == expected_fp, f"{name} profile fingerprint mismatch")
    expected_profile_set = digest([DOMAIN, "schema-profile-set", [p["schema_profile_fingerprint"] for p in profiles]])
    ensure(fixture["schema_profile_set_fingerprint"] == expected_profile_set, "schema profile set mismatch")

    requirement = fixture["prospective_F4_handoff_requirement"]
    ensure(requirement["interface_version"] == "agents-os.f5-prospective-f4-handoff-requirement.v0.1-r1", "requirement interface mismatch")
    ensure(requirement["owner"] == "F4", "requirement owner mismatch")
    ensure(requirement["required_schema_name"] == "F4AcceptedEffectHandoffV0_1R9", "required F4 schema mismatch")
    ensure(requirement["required_interface_version"] == "agents-os.f4-accepted-effect-handoff.v0.1-r9", "required F4 interface mismatch")
    ensure(requirement["required_F4_manifest_sha256"] == "8648cb687608b1151c81d01582a1fb7a19a5811a66224abe621a25188dc30dd5", "required F4 manifest mismatch")
    ensure(requirement["status"] == "UNAVAILABLE_FOR_REAL_POSITIVE_HANDOFF", "requirement status mismatch")
    ensure(requirement["usable_in_runtime"] is False and requirement["synthetic_fixture_only"] is True and requirement["authority_eligible"] is False, "requirement must be non-runtime non-authority")
    req_without_fp = {k: v for k, v in requirement.items() if k != "canonical_fingerprint"}
    ensure(requirement["canonical_fingerprint"] == digest([DOMAIN, "prospective-requirement", req_without_fp]), "requirement fingerprint mismatch")

    vectors = fixture["decision_vectors"]
    vector_ids = [v["vector_id"] for v in vectors]
    ensure(len(vector_ids) == len(set(vector_ids)), "duplicate vector id")
    ensure(set(vector_ids) == REQUIRED_VECTOR_IDS, "required vector set mismatch")
    for vector in vectors:
        ensure(set(vector) == {"vector_id", "kind", "input", "expected", "canonical_fingerprint"}, "vector fields mismatch")
        expected = independent_reduce(vector["kind"], vector["input"])
        ensure(vector["expected"] == expected, f"vector reducer mismatch: {vector['vector_id']}")
        expected_fp = digest([DOMAIN, "decision-vector", vector["vector_id"], vector["kind"], vector["input"], expected])
        ensure(vector["canonical_fingerprint"] == expected_fp, f"vector fingerprint mismatch: {vector['vector_id']}")
    expected_vector_set = digest([DOMAIN, "decision-vector-set", [v["canonical_fingerprint"] for v in vectors]])

    witness = fixture["synthetic_witness"]
    witness_profile = EXPECTED_SCHEMAS["F5SyntheticDeliveryRecoveryWitnessV0_1R1"][2]
    ensure(list(witness) == witness_profile, "witness field order mismatch")
    ensure(witness["witness_namespace"] == "synthetic-f5-r1", "witness namespace mismatch")
    ensure(witness["environment"] == "SYNTHETIC_TEST", "witness environment mismatch")
    ensure(witness["fingerprint_domain"] == DOMAIN, "witness domain mismatch")
    ensure(witness["prospective_F4_handoff_requirement_ref"] == requirement["requirement_ref"], "witness requirement ref mismatch")
    ensure(witness["prospective_F4_handoff_requirement_fingerprint"] == requirement["canonical_fingerprint"], "witness requirement fingerprint mismatch")
    ensure(witness["vector_set_fingerprint"] == expected_vector_set, "witness vector set mismatch")
    ensure(witness["authority_eligible"] is False, "witness authority must be false")
    ensure(witness["runtime_consumable"] is False, "witness runtime consumable must be false")
    ensure(witness["recovery_importable"] is False, "witness recovery importable must be false")
    ensure(witness["physical_effect_boundary"] == "NOT_EXECUTABLE", "witness physical boundary mismatch")
    ensure(witness["terminal_outcome"] == "NOT_EXECUTED", "witness terminal outcome mismatch")
    for key in ["accepted_real_handoff_count", "armed_dispatch_count", "external_effect_count", "provider_call_count", "raw_secret_count"]:
        ensure(witness[key] == 0, f"witness {key} must be zero")
    witness_without_fp = {k: v for k, v in witness.items() if k != "canonical_fingerprint"}
    ensure(witness["canonical_fingerprint"] == digest([DOMAIN, "witness", witness_without_fp]), "witness fingerprint mismatch")

    expected_assertions = {
        "accepted_real_handoff_count": 0,
        "armed_dispatch_count": 0,
        "runtime_consumable_count": 0,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }
    ensure(fixture["assertions"] == expected_assertions, "assertions mismatch")
    ensure(fixture["summary"]["schema_profile_count"] == 13, "summary schema count mismatch")
    ensure(fixture["summary"]["decision_vector_count"] == len(vectors), "summary vector count mismatch")
    ensure(fixture["summary"]["recovery_vector_count"] == 8, "summary recovery count mismatch")

    # No normative runtime object occurrence may hide outside profile metadata.
    production_interfaces = {value[0] for value in EXPECTED_SCHEMAS.values()} - {
        "agents-os.f5-synthetic-delivery-recovery-witness.v0.1-r1"
    }
    def walk(value: Any, path: str = "$") -> None:
        if isinstance(value, dict):
            if path != "$" and not path.startswith("$.schema_profiles["):
                interface = value.get("interface_version")
                ensure(interface not in production_interfaces, f"runtime object occurrence at {path}")
                if "environment" in value:
                    ensure(value["environment"] == "SYNTHETIC_TEST", f"non-synthetic environment at {path}")
                if "authority_eligible" in value:
                    ensure(value["authority_eligible"] is False, f"authority eligible at {path}")
            for key, child in value.items():
                walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
    walk(fixture)

    return {
        "result": "PASS_NO_BLOCKER",
        "schema_profile_count": len(profiles),
        "decision_vector_count": len(vectors),
        "recovery_vector_count": 8,
        "accepted_real_handoff_count": 0,
        "armed_dispatch_count": 0,
        "runtime_consumable_count": 0,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
        "fixture_canonical_sha256": fixture["fixture_canonical_sha256"],
    }


def resign_vector_fixture(fixture: dict[str, Any]) -> None:
    for vector in fixture["decision_vectors"]:
        vector["canonical_fingerprint"] = digest([
            DOMAIN, "decision-vector", vector["vector_id"], vector["kind"],
            vector["input"], vector["expected"],
        ])
    vector_set = digest([DOMAIN, "decision-vector-set", [v["canonical_fingerprint"] for v in fixture["decision_vectors"]]])
    fixture["synthetic_witness"]["vector_set_fingerprint"] = vector_set
    resign_witness(fixture)


def resign_witness(fixture: dict[str, Any]) -> None:
    witness = fixture["synthetic_witness"]
    witness["canonical_fingerprint"] = digest([DOMAIN, "witness", {k: v for k, v in witness.items() if k != "canonical_fingerprint"}])
    resign_root(fixture)


def resign_requirement(fixture: dict[str, Any]) -> None:
    requirement = fixture["prospective_F4_handoff_requirement"]
    requirement["canonical_fingerprint"] = digest([DOMAIN, "prospective-requirement", {k: v for k, v in requirement.items() if k != "canonical_fingerprint"}])
    fixture["synthetic_witness"]["prospective_F4_handoff_requirement_fingerprint"] = requirement["canonical_fingerprint"]
    resign_witness(fixture)


def resign_profiles(fixture: dict[str, Any]) -> None:
    for profile in fixture["schema_profiles"]:
        profile["schema_profile_fingerprint"] = digest([
            DOMAIN, "schema-profile", profile["schema_name"], profile["interface_version"],
            profile["fingerprint_field"], profile["fields"],
        ])
    fixture["schema_profile_set_fingerprint"] = digest([DOMAIN, "schema-profile-set", [p["schema_profile_fingerprint"] for p in fixture["schema_profiles"]]])
    resign_root(fixture)


def resign_root(fixture: dict[str, Any]) -> None:
    fixture["fixture_canonical_sha256"] = recompute_fixture_hash(fixture)


def mutation_checks(base: dict[str, Any]) -> int:
    mutations: list[dict[str, Any]] = []

    item = copy.deepcopy(base)
    item["synthetic_witness"]["external_effect_count"] = 1
    item["assertions"]["external_effect_count"] = 1
    resign_witness(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["synthetic_witness"]["authority_eligible"] = True
    resign_witness(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["synthetic_witness"]["runtime_consumable"] = True
    resign_witness(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["synthetic_witness"]["armed_dispatch_count"] = 1
    item["assertions"]["armed_dispatch_count"] = 1
    resign_witness(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["prospective_F4_handoff_requirement"]["usable_in_runtime"] = True
    resign_requirement(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["prospective_F4_handoff_requirement"]["required_F4_manifest_sha256"] = "0" * 64
    resign_requirement(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["schema_profiles"][0]["fields"].pop()
    resign_profiles(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["decision_vectors"].pop()
    item["summary"]["decision_vector_count"] -= 1
    resign_vector_fixture(item); mutations.append(item)

    item = copy.deepcopy(base)
    target = next(v for v in item["decision_vectors"] if v["vector_id"] == "ATTEMPT_UNKNOWN")
    target["expected"]["automatic_retry_eligible"] = True
    resign_vector_fixture(item); mutations.append(item)

    item = copy.deepcopy(base)
    target = next(v for v in item["decision_vectors"] if v["vector_id"] == "ATTEMPT_PRE_EFFECT_NOT_EXECUTED")
    target["expected"]["automatic_retry_eligible"] = True
    resign_vector_fixture(item); mutations.append(item)

    item = copy.deepcopy(base)
    target = next(v for v in item["decision_vectors"] if v["vector_id"] == "RECEIPT_EXACT_DUPLICATE")
    target["expected"]["event_created"] = True
    resign_vector_fixture(item); mutations.append(item)

    item = copy.deepcopy(base)
    target = next(v for v in item["decision_vectors"] if v["vector_id"] == "RECOVERY_ARM_COMMITTED_CALL_UNCERTAIN")
    target["expected"]["decision"] = "RETRY_AUTOMATICALLY"
    resign_vector_fixture(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["environment"] = "PRODUCTION"
    resign_root(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["decision_vectors"].append(copy.deepcopy(item["decision_vectors"][0]))
    item["summary"]["decision_vector_count"] += 1
    resign_vector_fixture(item); mutations.append(item)

    item = copy.deepcopy(base)
    item["fixture_canonical_sha256"] = "0" * 64
    mutations.append(item)

    rejected = 0
    for mutation in mutations:
        try:
            validate_fixture(mutation)
        except (ValueError, KeyError, TypeError):
            rejected += 1
    ensure(rejected == len(mutations), "one or more semantic mutations were accepted")
    return rejected


def main() -> int:
    fixture_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    try:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        result = validate_fixture(fixture)
        result["negative_mutations_rejected"] = mutation_checks(fixture)
    except (OSError, json.JSONDecodeError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"result": "BLOCK", "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
