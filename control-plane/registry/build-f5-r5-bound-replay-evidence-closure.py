#!/usr/bin/env python3
"""Build the deterministic nonauthority F5 R5 bound replay evidence fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path(
    "control-plane/registry/examples/"
    "2026-07-17-agents-os-f5-r5-bound-replay-evidence-closure-v0.1.json"
)
FIXTURE_INTERFACE = "agents-os.f5-r5-bound-replay-evidence-closure-fixture.v0.1"
PROOF_DOMAIN = "agents-os.f5-r5-bound-replay-evidence-closure-proof.v0.1"
RECEIPT_PAYLOAD_INTERFACE = "agents-os.f5-delivery-receipt-replay-payload.v0.1-r5"
ARM_PAYLOAD_INTERFACE = "agents-os.f5-dispatch-arm-replay-request-payload.v0.1-r4"

RECEIPT_KINDS = {
    "TRANSPORT_ACK",
    "EFFECT_SUCCEEDED",
    "EFFECT_FAILED",
    "EFFECT_STATUS_UNKNOWN",
    "EFFECT_QUERY_RESULT",
}
EFFECT_STATUSES = {"ACKED_ONLY", "SUCCEEDED", "FAILED", "UNKNOWN", "NOT_EXECUTED"}
RECEIPT_ALLOWED = {
    "TRANSPORT_ACK": {"ACKED_ONLY"},
    "EFFECT_SUCCEEDED": {"SUCCEEDED"},
    "EFFECT_FAILED": {"FAILED"},
    "EFFECT_STATUS_UNKNOWN": {"UNKNOWN"},
    "EFFECT_QUERY_RESULT": {"SUCCEEDED", "FAILED", "UNKNOWN", "NOT_EXECUTED"},
}
ALLOWED_TRANSITIONS = {
    ("PENDING", "CLAIMED"),
    ("PENDING", "DEAD_LETTERED"),
    ("CLAIMED", "CLAIMED"),
    ("CLAIMED", "DISPATCH_ARMED"),
    ("CLAIMED", "DEAD_LETTERED"),
    ("DISPATCH_ARMED", "DISPATCHED"),
    ("DISPATCH_ARMED", "ACKED"),
    ("DISPATCH_ARMED", "SUCCEEDED"),
    ("DISPATCH_ARMED", "FAILED"),
    ("DISPATCH_ARMED", "UNKNOWN"),
    ("DISPATCHED", "ACKED"),
    ("DISPATCHED", "SUCCEEDED"),
    ("DISPATCHED", "FAILED"),
    ("DISPATCHED", "UNKNOWN"),
    ("ACKED", "SUCCEEDED"),
    ("ACKED", "FAILED"),
    ("ACKED", "UNKNOWN"),
    ("FAILED", "RECONCILED"),
    ("UNKNOWN", "RECONCILED"),
    ("DEAD_LETTERED", "RECONCILED"),
}

SECTIONS = (
    "receipt_record_profile",
    "arm_request_profile",
    "receipt_replay_cases",
    "arm_identity_cases",
    "adversarial_cases",
    "assertions",
    "summary",
)


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


def h(domain: str, *values: Any) -> str:
    return digest([domain, *values])


def hx(label: str) -> str:
    return hashlib.sha256(("f5-r5:" + label).encode("utf-8")).hexdigest()


def compatibility(kind: str, status: str) -> str:
    return "COMPATIBLE" if status in RECEIPT_ALLOWED[kind] else "RECEIPT_KIND_STATUS_MISMATCH"


def receipt_payload(
    *,
    kind: str = "EFFECT_SUCCEEDED",
    status: str = "SUCCEEDED",
    observed_at_utc_ms: int = 1700,
) -> dict[str, Any]:
    return {
        "interface_version": RECEIPT_PAYLOAD_INTERFACE,
        "receipt_id": "synthetic-f5-r5:receipt-1",
        "source_id": "synthetic-f5-r5:receipt-source",
        "source_receipt_revision": 1,
        "attempt_ref": "synthetic-f5-r5:attempt-1",
        "attempt_fingerprint": hx("attempt-1"),
        "outbox_intent_ref": "synthetic-f5-r5:intent-1",
        "outbox_intent_fingerprint": hx("intent-1"),
        "effect_id": "synthetic-f5-r5:effect-1",
        "invocation_identity_fingerprint": hx("invocation-1"),
        "execution_epoch": 1,
        "host_fence_generation": 1,
        "effect_fence_generation": 1,
        "receipt_kind": kind,
        "effect_status": status,
        "observed_at_utc_ms": observed_at_utc_ms,
        "received_at_utc_ms": 1800,
        "source_attestation_ref": "synthetic-f5-r5:source-attestation-1",
        "source_attestation_fingerprint": hx("source-attestation-1"),
    }


def receipt_record(**changes: Any) -> dict[str, Any]:
    payload = receipt_payload(**changes)
    encoded = canonical_bytes(payload)
    return {
        "source_id": payload["source_id"],
        "receipt_id": payload["receipt_id"],
        "receipt_fingerprint": hashlib.sha256(encoded).hexdigest(),
        "receipt_canonical_utf8_hex": encoded.hex(),
    }


def decode_receipt_record(record: dict[str, Any]) -> dict[str, Any]:
    encoded = bytes.fromhex(record["receipt_canonical_utf8_hex"])
    payload = json.loads(encoded.decode("utf-8"))
    if encoded != canonical_bytes(payload):
        raise ValueError("noncanonical receipt bytes")
    if hashlib.sha256(encoded).hexdigest() != record["receipt_fingerprint"]:
        raise ValueError("receipt fingerprint mismatch")
    if payload["source_id"] != record["source_id"] or payload["receipt_id"] != record["receipt_id"]:
        raise ValueError("receipt outer key mismatch")
    return payload


def receipt_raw(
    *,
    stored: dict[str, Any] | None,
    submitted: dict[str, Any],
    lookup_reproducible: bool = True,
    **changes: Any,
) -> dict[str, Any]:
    raw = {
        "lookup_reproducible": lookup_reproducible,
        "stored_receipt": stored,
        "submitted_receipt": submitted,
        "integrity_valid": True,
        "source_attestation_status": "VALID",
        "attempt_effect_identity_match": True,
        "existing_effect_query_authenticated": True,
        "epoch_current": True,
        "fences_current": True,
        "attempt_current": True,
        "from_state": "DISPATCHED",
        "to_state": "SUCCEEDED",
    }
    raw.update(changes)
    return raw


def reduce_receipt(raw: dict[str, Any]) -> dict[str, Any]:
    submitted_payload = decode_receipt_record(raw["submitted_receipt"])
    stored = raw["stored_receipt"]
    if stored is not None:
        decode_receipt_record(stored)
        if (
            stored["source_id"],
            stored["receipt_id"],
        ) != (
            raw["submitted_receipt"]["source_id"],
            raw["submitted_receipt"]["receipt_id"],
        ):
            raise ValueError("stored/submitted receipt key mismatch")

    kind = submitted_payload["receipt_kind"]
    status = submitted_payload["effect_status"]
    comp = compatibility(kind, status)
    if not raw["lookup_reproducible"]:
        relation = "LOOKUP_INDETERMINATE"
    elif stored is None:
        relation = "NEW"
    elif all(
        stored[key] == raw["submitted_receipt"][key]
        for key in ("receipt_fingerprint", "receipt_canonical_utf8_hex")
    ):
        relation = "EXACT_DUPLICATE"
    else:
        relation = "CHANGED_BYTES_SAME_KEY"

    base = {"dedup_relation": relation, "compatibility": comp}
    if relation == "LOOKUP_INDETERMINATE":
        return {
            **base,
            "result": "INDETERMINATE",
            "primary_reason": "RECEIPT_LOOKUP_UNAVAILABLE",
            "reason_codes": ["RECEIPT_LOOKUP_UNAVAILABLE"],
            "event_created": False,
            "reconciliation_opened": False,
            "current_projection_advanced": False,
            "task_advancement_eligible": False,
        }
    if relation == "EXACT_DUPLICATE":
        return {
            **base,
            "result": "REPLAYED",
            "primary_reason": "EXACT_DUPLICATE_REPLAY",
            "reason_codes": [],
            "event_created": False,
            "reconciliation_opened": False,
            "current_projection_advanced": False,
            "task_advancement_eligible": False,
        }
    if relation == "CHANGED_BYTES_SAME_KEY":
        return {
            **base,
            "result": "REJECTED",
            "primary_reason": "RECEIPT_BYTES_CONFLICT",
            "reason_codes": ["RECEIPT_BYTES_CONFLICT"],
            "event_created": False,
            "reconciliation_opened": True,
            "current_projection_advanced": False,
            "task_advancement_eligible": False,
        }

    reasons: list[str] = []
    if not raw["integrity_valid"]:
        reasons.append("INTEGRITY_FAILURE")
    if raw["source_attestation_status"] == "INVALID":
        reasons.append("SOURCE_ATTESTATION_INVALID")
    if not raw["attempt_effect_identity_match"]:
        reasons.append("ATTEMPT_OR_EFFECT_MISMATCH")
    if kind == "EFFECT_QUERY_RESULT" and not raw["existing_effect_query_authenticated"]:
        reasons.append("EXISTING_EFFECT_QUERY_INVALID")
    if comp != "COMPATIBLE":
        reasons.append("RECEIPT_KIND_STATUS_MISMATCH")
    if (raw["from_state"], raw["to_state"]) not in ALLOWED_TRANSITIONS:
        reasons.append("TRANSITION_INVALID")
    if raw["source_attestation_status"] == "UNAVAILABLE":
        reasons.append("SOURCE_ATTESTATION_UNAVAILABLE")
    if not raw["epoch_current"]:
        reasons.append("EPOCH_STALE")
    if not raw["fences_current"]:
        reasons.append("FENCE_STALE")
    if not raw["attempt_current"]:
        reasons.append("ATTEMPT_STALE")
    precedence = (
        "INTEGRITY_FAILURE SOURCE_ATTESTATION_INVALID ATTEMPT_OR_EFFECT_MISMATCH "
        "EXISTING_EFFECT_QUERY_INVALID RECEIPT_KIND_STATUS_MISMATCH "
        "TRANSITION_INVALID SOURCE_ATTESTATION_UNAVAILABLE EPOCH_STALE "
        "FENCE_STALE ATTEMPT_STALE"
    ).split()
    primary = next((item for item in precedence if item in reasons), "APPLIED_CURRENT")
    if primary == "APPLIED_CURRENT":
        result = "APPLIED"
    elif primary == "SOURCE_ATTESTATION_UNAVAILABLE":
        result = "INDETERMINATE"
    elif primary in {"EPOCH_STALE", "FENCE_STALE", "ATTEMPT_STALE"}:
        result = "HISTORY_ONLY"
    else:
        result = "REJECTED"
    return {
        **base,
        "result": result,
        "primary_reason": "HISTORY_ONLY_" + primary if result == "HISTORY_ONLY" else primary,
        "reason_codes": sorted(reasons),
        "event_created": result in {"APPLIED", "HISTORY_ONLY"},
        "reconciliation_opened": False,
        "current_projection_advanced": result == "APPLIED",
        "task_advancement_eligible": False,
    }


def request_payload(*, attempt_ordinal: int = 1, requested_at_utc_ms: int = 1000) -> dict[str, Any]:
    intent_fingerprint = hx("arm-intent")
    invocation_fingerprint = hx("arm-invocation")
    return {
        "payload_interface": ARM_PAYLOAD_INTERFACE,
        "outbox_intent_ref": "synthetic-f5-r5:arm-intent",
        "outbox_intent_fingerprint": intent_fingerprint,
        "bound_invocation_identity_fingerprint": invocation_fingerprint,
        "claim_ref": "synthetic-f5-r5:arm-claim",
        "claim_fingerprint": hx("arm-claim"),
        "claim_epoch": 1,
        "claim_fencing_token": hx("arm-fence"),
        "attempt_ordinal": attempt_ordinal,
        "attempt_id": h(
            "agents-os.f5-delivery-attempt-id.v0.1",
            intent_fingerprint,
            attempt_ordinal,
        ),
        "idempotency_key": "synthetic-f5-r5:idempotency-key",
        "physical_boundary_observation_ref": "synthetic-f5-r5:boundary-observation",
        "physical_boundary_observation_fingerprint": hx("arm-boundary-observation"),
        "requested_at_utc_ms": requested_at_utc_ms,
        "requested_event_sequence": 21,
    }


def request_record(*, attempt_ordinal: int = 1, requested_at_utc_ms: int = 1000) -> dict[str, Any]:
    payload = request_payload(
        attempt_ordinal=attempt_ordinal,
        requested_at_utc_ms=requested_at_utc_ms,
    )
    encoded = canonical_bytes(payload)
    return {
        "request_id": h(
            "agents-os.f5-dispatch-arm-request-id.v0.1",
            payload["outbox_intent_fingerprint"],
            payload["bound_invocation_identity_fingerprint"],
            payload["attempt_ordinal"],
        ),
        "request_fingerprint": hashlib.sha256(encoded).hexdigest(),
        "request_canonical_utf8_hex": encoded.hex(),
    }


def decode_request_record(record: dict[str, Any]) -> dict[str, Any]:
    encoded = bytes.fromhex(record["request_canonical_utf8_hex"])
    payload = json.loads(encoded.decode("utf-8"))
    if encoded != canonical_bytes(payload):
        raise ValueError("noncanonical request bytes")
    if hashlib.sha256(encoded).hexdigest() != record["request_fingerprint"]:
        raise ValueError("request fingerprint mismatch")
    expected_id = h(
        "agents-os.f5-dispatch-arm-request-id.v0.1",
        payload["outbox_intent_fingerprint"],
        payload["bound_invocation_identity_fingerprint"],
        payload["attempt_ordinal"],
    )
    if record["request_id"] != expected_id:
        raise ValueError("request ID formula mismatch")
    return payload


def stored_arm_state(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "first_arm_ref": "synthetic-f5-r5:first-arm",
        "first_arm_fingerprint": hx("first-arm"),
        "first_event_ref": "synthetic-f5-r5:first-arm-event",
        "first_event_fingerprint": hx("first-arm-event"),
        "first_call_authorization_ref": "synthetic-f5-r5:first-call-authorization",
        "first_call_authorization_fingerprint": hx("first-call-authorization"),
        "committed_event_count": 1,
        "committed_call_authorization_count": 1,
    }


def derive_arm(raw: dict[str, Any]) -> dict[str, Any]:
    submitted_payload = decode_request_record(raw["submitted_request"])
    if (
        submitted_payload["bound_invocation_identity_fingerprint"]
        != raw["bound_invocation_identity_fingerprint"]
    ):
        raise ValueError("submitted invocation mismatch")
    stored = raw["stored_arm_state"]
    if stored is not None:
        stored_payload = decode_request_record(
            {
                key: stored[key]
                for key in (
                    "request_id",
                    "request_fingerprint",
                    "request_canonical_utf8_hex",
                )
            }
        )
        if (
            stored_payload["bound_invocation_identity_fingerprint"]
            != raw["bound_invocation_identity_fingerprint"]
        ):
            raise ValueError("stored invocation mismatch")
        if stored["request_id"] != raw["submitted_request"]["request_id"]:
            raise ValueError("stored/submitted request identity mismatch")

    if not raw["lookup_reproducible"]:
        relation = "LOOKUP_INDETERMINATE"
    elif stored is None:
        relation = "NO_EXISTING_ARM"
    elif all(
        stored[key] == raw["submitted_request"][key]
        for key in (
            "request_id",
            "request_fingerprint",
            "request_canonical_utf8_hex",
        )
    ):
        relation = "EXACT_DUPLICATE"
    else:
        relation = "CHANGED_BYTES_SAME_IDENTITY"

    outputs = {
        "NO_EXISTING_ARM": ("APPLIED", "ARMED_FIRST_APPLY", 1, 1),
        "EXACT_DUPLICATE": ("REPLAYED", "EXACT_DUPLICATE_REPLAY", 0, 0),
        "CHANGED_BYTES_SAME_IDENTITY": ("REJECTED", "REQUEST_BYTES_CONFLICT", 0, 0),
        "LOOKUP_INDETERMINATE": ("INDETERMINATE", "ARM_LOOKUP_UNAVAILABLE", 0, 0),
    }
    result, reason, event_delta, call_delta = outputs[relation]
    exact = relation == "EXACT_DUPLICATE"
    return {
        "replay_relation": relation,
        "result": result,
        "primary_reason": reason,
        "returned_first_arm_ref": stored["first_arm_ref"] if exact else None,
        "returned_first_arm_fingerprint": stored["first_arm_fingerprint"] if exact else None,
        "returned_first_event_ref": stored["first_event_ref"] if exact else None,
        "returned_first_event_fingerprint": stored["first_event_fingerprint"] if exact else None,
        "returned_first_call_authorization_ref": (
            stored["first_call_authorization_ref"] if exact else None
        ),
        "returned_first_call_authorization_fingerprint": (
            stored["first_call_authorization_fingerprint"] if exact else None
        ),
        "modeled_event_delta": event_delta,
        "modeled_call_authorization_delta": call_delta,
        "total_event_count": stored["committed_event_count"] if stored is not None else event_delta,
        "total_call_authorization_count": (
            stored["committed_call_authorization_count"] if stored is not None else call_delta
        ),
    }


def build_fixture() -> dict[str, Any]:
    receipt_base = receipt_record()
    receipt_changed = receipt_record(kind="TRANSPORT_ACK", status="ACKED_ONLY")
    receipt_incompatible = receipt_record(kind="TRANSPORT_ACK", status="SUCCEEDED")
    receipt_raws = [
        ("RECEIPT_BOUND_1_NEW", receipt_raw(stored=None, submitted=receipt_base)),
        (
            "RECEIPT_BOUND_2_EXACT",
            receipt_raw(stored=receipt_base, submitted=receipt_base),
        ),
        (
            "RECEIPT_BOUND_3_CHANGED_BYTES",
            receipt_raw(stored=receipt_base, submitted=receipt_changed),
        ),
        (
            "RECEIPT_BOUND_4_LOOKUP_INDETERMINATE",
            receipt_raw(
                stored=receipt_base,
                submitted=receipt_base,
                lookup_reproducible=False,
            ),
        ),
        (
            "RECEIPT_BOUND_5_INCOMPATIBLE_NEW",
            receipt_raw(stored=None, submitted=receipt_incompatible),
        ),
    ]
    receipt_cases = [
        {
            "case_id": case_id,
            "proof_mode": "ABSTRACT_NONOCCURRING_REDUCER_TRIAL",
            "raw_input": raw,
            "derived": reduce_receipt(raw),
        }
        for case_id, raw in receipt_raws
    ]

    request_base = request_record()
    request_changed = request_record(requested_at_utc_ms=1001)
    arm_stored = stored_arm_state(request_base)
    bound_invocation = hx("arm-invocation")
    arm_raws = [
        (
            "ARM_IDENTITY_1_FIRST",
            {
                "lookup_reproducible": True,
                "bound_invocation_identity_fingerprint": bound_invocation,
                "stored_arm_state": None,
                "submitted_request": request_base,
                "first_apply_eligibility": "ELIGIBLE_PROOF_PRECONDITION",
            },
        ),
        (
            "ARM_IDENTITY_2_EXACT",
            {
                "lookup_reproducible": True,
                "bound_invocation_identity_fingerprint": bound_invocation,
                "stored_arm_state": arm_stored,
                "submitted_request": request_base,
                "first_apply_eligibility": "NOT_ELIGIBLE",
            },
        ),
        (
            "ARM_IDENTITY_3_CHANGED_BYTES",
            {
                "lookup_reproducible": True,
                "bound_invocation_identity_fingerprint": bound_invocation,
                "stored_arm_state": arm_stored,
                "submitted_request": request_changed,
                "first_apply_eligibility": "NOT_ELIGIBLE",
            },
        ),
        (
            "ARM_IDENTITY_4_LOOKUP_INDETERMINATE_EQUAL_IDENTITY",
            {
                "lookup_reproducible": False,
                "bound_invocation_identity_fingerprint": bound_invocation,
                "stored_arm_state": arm_stored,
                "submitted_request": request_base,
                "first_apply_eligibility": "NOT_ELIGIBLE",
            },
        ),
    ]
    arm_cases = [
        {
            "case_id": case_id,
            "proof_mode": "ABSTRACT_NONOCCURRING_REDUCER_TRIAL",
            "raw_input": raw,
            "derived": derive_arm(raw),
        }
        for case_id, raw in arm_raws
    ]

    adversarial_cases = [
        {
            "check": "original_R3_detached_receipt_kind_status_exact_replay_override",
            "expected_decision": "REJECT_CLOSED_INVENTORY",
        },
        {
            "check": "bound_submitted_receipt_kind_status_change_presented_as_exact",
            "expected_decision": "REJECT_DERIVATION_MISMATCH",
        },
        {
            "check": "bound_stored_receipt_bytes_change_presented_as_exact",
            "expected_decision": "REJECT_DERIVATION_MISMATCH",
        },
        {
            "check": "noncanonical_receipt_bytes_with_recomputed_fingerprint",
            "expected_decision": "REJECT_NONCANONICAL_BYTES",
        },
        {
            "check": "receipt_fingerprint_not_equal_to_exact_bytes",
            "expected_decision": "REJECT_FINGERPRINT_FORMULA",
        },
        {
            "check": "receipt_outer_key_not_equal_to_bound_payload",
            "expected_decision": "REJECT_BOUND_KEY_MISMATCH",
        },
        {
            "check": "lookup_indeterminate_arm_with_different_valid_request_identity",
            "expected_decision": "REJECT_REQUEST_IDENTITY_MISMATCH",
        },
        {
            "check": "noncanonical_arm_request_bytes",
            "expected_decision": "REJECT_NONCANONICAL_BYTES",
        },
        {
            "check": "unknown_root_section_row_or_nested_raw_field",
            "expected_decision": "REJECT_CLOSED_INVENTORY",
        },
    ]
    assertions = {
        "synthetic_nonauthority": True,
        "receipt_kind_status_detached_authority_absent": True,
        "arm_identity_equality_precedes_lookup_branch": True,
        "accepted_real_handoff_count": 0,
        "claim_event_count": 0,
        "armed_dispatch_count": 0,
        "runtime_consumable_count": 0,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }
    fixture: dict[str, Any] = {
        "fixture_interface": FIXTURE_INTERFACE,
        "environment": "SYNTHETIC_TEST",
        "authority_eligible": False,
        "runtime_consumable": False,
        "recovery_importable": False,
        "fixture_canonical_sha256": "",
        "receipt_record_profile": {
            "record_fields": [
                "receipt_canonical_utf8_hex",
                "receipt_fingerprint",
                "receipt_id",
                "source_id",
            ],
            "payload_interface": RECEIPT_PAYLOAD_INTERFACE,
            "receipt_kind_and_effect_status_bound": True,
            "fingerprint_formula": "SHA256_EXACT_CANONICAL_UTF8_BYTES",
            "exact_replay_requires_byte_and_fingerprint_identity": True,
        },
        "arm_request_profile": {
            "record_fields": [
                "request_canonical_utf8_hex",
                "request_fingerprint",
                "request_id",
            ],
            "payload_interface": ARM_PAYLOAD_INTERFACE,
            "stored_submitted_identity_check_position": "BEFORE_LOOKUP_BRANCH",
            "different_identity_result": "REJECT_PROOF_INPUT",
        },
        "receipt_replay_cases": receipt_cases,
        "arm_identity_cases": arm_cases,
        "adversarial_cases": adversarial_cases,
        "assertions": assertions,
        "summary": {
            "receipt_replay_case_count": len(receipt_cases),
            "arm_identity_case_count": len(arm_cases),
            "adversarial_case_count": len(adversarial_cases),
            "receipt_exact_case_count": 1,
            "arm_lookup_equal_identity_case_count": 1,
            "real_effect_count": 0,
        },
    }
    for section in SECTIONS:
        fixture[section + "_fingerprint"] = digest(fixture[section])
    fixture["fixture_canonical_sha256"] = digest(
        {key: value for key, value in fixture.items() if key != "fixture_canonical_sha256"}
    )
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_fixture(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
