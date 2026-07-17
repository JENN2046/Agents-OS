#!/usr/bin/env python3
"""Validate the fixed nonauthority F5 R5 bound replay evidence fixture."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


DEFAULT_FIXTURE = Path(
    "control-plane/registry/examples/"
    "2026-07-17-agents-os-f5-r5-bound-replay-evidence-closure-v0.1.json"
)
FIXTURE_INTERFACE = "agents-os.f5-r5-bound-replay-evidence-closure-fixture.v0.1"
RECEIPT_PAYLOAD_INTERFACE = "agents-os.f5-delivery-receipt-replay-payload.v0.1-r5"
ARM_PAYLOAD_INTERFACE = "agents-os.f5-dispatch-arm-replay-request-payload.v0.1-r4"
SAFE_INTEGER = 9007199254740991
SHA_RE = re.compile(r"[0-9a-f]{64}")
HEX_RE = re.compile(r"(?:[0-9a-f]{2})+")

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
SOURCE_ATTESTATION_STATUSES = {"VALID", "INVALID", "UNAVAILABLE"}
STATES = {
    "PENDING",
    "CLAIMED",
    "DISPATCH_ARMED",
    "DISPATCHED",
    "ACKED",
    "SUCCEEDED",
    "FAILED",
    "UNKNOWN",
    "DEAD_LETTERED",
    "RECONCILED",
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

RECEIPT_PAYLOAD_FIELDS = {
    "interface_version",
    "receipt_id",
    "source_id",
    "source_receipt_revision",
    "attempt_ref",
    "attempt_fingerprint",
    "outbox_intent_ref",
    "outbox_intent_fingerprint",
    "effect_id",
    "invocation_identity_fingerprint",
    "execution_epoch",
    "host_fence_generation",
    "effect_fence_generation",
    "receipt_kind",
    "effect_status",
    "observed_at_utc_ms",
    "received_at_utc_ms",
    "source_attestation_ref",
    "source_attestation_fingerprint",
}
RECEIPT_RECORD_FIELDS = {
    "source_id",
    "receipt_id",
    "receipt_fingerprint",
    "receipt_canonical_utf8_hex",
}
RECEIPT_RAW_FIELDS = {
    "lookup_reproducible",
    "stored_receipt",
    "submitted_receipt",
    "integrity_valid",
    "source_attestation_status",
    "attempt_effect_identity_match",
    "existing_effect_query_authenticated",
    "epoch_current",
    "fences_current",
    "attempt_current",
    "from_state",
    "to_state",
}
RECEIPT_DERIVED_FIELDS = {
    "dedup_relation",
    "compatibility",
    "result",
    "primary_reason",
    "reason_codes",
    "event_created",
    "reconciliation_opened",
    "current_projection_advanced",
    "task_advancement_eligible",
}

ARM_PAYLOAD_FIELDS = {
    "payload_interface",
    "outbox_intent_ref",
    "outbox_intent_fingerprint",
    "bound_invocation_identity_fingerprint",
    "claim_ref",
    "claim_fingerprint",
    "claim_epoch",
    "claim_fencing_token",
    "attempt_ordinal",
    "attempt_id",
    "idempotency_key",
    "physical_boundary_observation_ref",
    "physical_boundary_observation_fingerprint",
    "requested_at_utc_ms",
    "requested_event_sequence",
}
ARM_RECORD_FIELDS = {
    "request_id",
    "request_fingerprint",
    "request_canonical_utf8_hex",
}
STORED_ARM_FIELDS = ARM_RECORD_FIELDS | {
    "first_arm_ref",
    "first_arm_fingerprint",
    "first_event_ref",
    "first_event_fingerprint",
    "first_call_authorization_ref",
    "first_call_authorization_fingerprint",
    "committed_event_count",
    "committed_call_authorization_count",
}
ARM_RAW_FIELDS = {
    "lookup_reproducible",
    "bound_invocation_identity_fingerprint",
    "stored_arm_state",
    "submitted_request",
    "first_apply_eligibility",
}
ARM_DERIVED_FIELDS = {
    "replay_relation",
    "result",
    "primary_reason",
    "returned_first_arm_ref",
    "returned_first_arm_fingerprint",
    "returned_first_event_ref",
    "returned_first_event_fingerprint",
    "returned_first_call_authorization_ref",
    "returned_first_call_authorization_fingerprint",
    "modeled_event_delta",
    "modeled_call_authorization_delta",
    "total_event_count",
    "total_call_authorization_count",
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
ROOT_FIELDS = {
    "fixture_interface",
    "environment",
    "authority_eligible",
    "runtime_consumable",
    "recovery_importable",
    "fixture_canonical_sha256",
} | set(SECTIONS) | {section + "_fingerprint" for section in SECTIONS}

EXPECTED_ADVERSARIAL_CASES = [
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


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def reject_constant(value: str) -> Any:
    raise ValueError(f"non-JSON constant {value}")


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        ensure(key not in result, f"duplicate JSON key {key}")
        result[key] = value
    return result


def parse_json_strict(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=unique_pairs,
        parse_constant=reject_constant,
    )


def validate_json_value(value: Any, path: str = "$") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        ensure(abs(value) <= SAFE_INTEGER, f"unsafe integer at {path}")
        return
    ensure(type(value) is not float, f"float forbidden at {path}")
    if isinstance(value, str):
        ensure(unicodedata.normalize("NFC", value) == value, f"non-NFC string at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            ensure(isinstance(key, str), f"non-string key at {path}")
            validate_json_value(key, f"{path}.<key>")
            validate_json_value(item, f"{path}.{key}")
        return
    raise ValueError(f"invalid JSON value at {path}")


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


def sha(value: Any, path: str) -> None:
    ensure(isinstance(value, str) and SHA_RE.fullmatch(value) is not None, f"sha required at {path}")


def stable_ref(value: Any, path: str) -> None:
    ensure(isinstance(value, str) and bool(value) and value == value.strip(), f"stable ref required at {path}")


def safe_int(value: Any, path: str, *, positive: bool = False) -> None:
    ensure(type(value) is int and 0 <= value <= SAFE_INTEGER, f"safe integer required at {path}")
    if positive:
        ensure(value > 0, f"positive safe integer required at {path}")


def boolean(value: Any, path: str) -> None:
    ensure(type(value) is bool, f"boolean required at {path}")


def decode_bound_json(hex_text: Any, path: str) -> tuple[bytes, dict[str, Any]]:
    ensure(isinstance(hex_text, str) and HEX_RE.fullmatch(hex_text) is not None, f"canonical hex required at {path}")
    encoded = bytes.fromhex(hex_text)
    payload = parse_json_strict(encoded.decode("utf-8"))
    ensure(isinstance(payload, dict), f"object payload required at {path}")
    validate_json_value(payload, path)
    ensure(encoded == canonical_bytes(payload), f"noncanonical bytes at {path}")
    return encoded, payload


def validate_receipt_payload(payload: dict[str, Any], path: str) -> None:
    ensure(set(payload) == RECEIPT_PAYLOAD_FIELDS, f"receipt payload inventory invalid at {path}")
    ensure(payload["interface_version"] == RECEIPT_PAYLOAD_INTERFACE, f"receipt payload interface invalid at {path}")
    for field in (
        "receipt_id",
        "source_id",
        "attempt_ref",
        "outbox_intent_ref",
        "effect_id",
        "source_attestation_ref",
    ):
        stable_ref(payload[field], f"{path}.{field}")
    for field in (
        "attempt_fingerprint",
        "outbox_intent_fingerprint",
        "invocation_identity_fingerprint",
        "source_attestation_fingerprint",
    ):
        sha(payload[field], f"{path}.{field}")
    for field in ("source_receipt_revision", "execution_epoch"):
        safe_int(payload[field], f"{path}.{field}", positive=True)
    for field in (
        "host_fence_generation",
        "effect_fence_generation",
        "observed_at_utc_ms",
        "received_at_utc_ms",
    ):
        safe_int(payload[field], f"{path}.{field}")
    ensure(payload["receipt_kind"] in RECEIPT_KINDS, f"unknown receipt kind at {path}")
    ensure(payload["effect_status"] in EFFECT_STATUSES, f"unknown effect status at {path}")


def parse_receipt_record(record: Any, path: str) -> dict[str, Any]:
    ensure(isinstance(record, dict) and set(record) == RECEIPT_RECORD_FIELDS, f"receipt record inventory invalid at {path}")
    stable_ref(record["source_id"], f"{path}.source_id")
    stable_ref(record["receipt_id"], f"{path}.receipt_id")
    sha(record["receipt_fingerprint"], f"{path}.receipt_fingerprint")
    encoded, payload = decode_bound_json(record["receipt_canonical_utf8_hex"], f"{path}.receipt_canonical_utf8_hex")
    validate_receipt_payload(payload, path + ".payload")
    ensure(payload["source_id"] == record["source_id"], f"bound source ID mismatch at {path}")
    ensure(payload["receipt_id"] == record["receipt_id"], f"bound receipt ID mismatch at {path}")
    ensure(hashlib.sha256(encoded).hexdigest() == record["receipt_fingerprint"], f"receipt fingerprint formula mismatch at {path}")
    return payload


def compatibility(kind: str, status: str) -> str:
    return "COMPATIBLE" if status in RECEIPT_ALLOWED[kind] else "RECEIPT_KIND_STATUS_MISMATCH"


def reduce_receipt(raw: Any) -> dict[str, Any]:
    ensure(isinstance(raw, dict) and set(raw) == RECEIPT_RAW_FIELDS, "receipt raw inventory invalid")
    for field in (
        "lookup_reproducible",
        "integrity_valid",
        "attempt_effect_identity_match",
        "existing_effect_query_authenticated",
        "epoch_current",
        "fences_current",
        "attempt_current",
    ):
        boolean(raw[field], f"receipt_raw.{field}")
    ensure(raw["source_attestation_status"] in SOURCE_ATTESTATION_STATUSES, "source attestation status invalid")
    ensure(raw["from_state"] in STATES and raw["to_state"] in STATES, "receipt state invalid")
    submitted_payload = parse_receipt_record(raw["submitted_receipt"], "submitted_receipt")
    stored = raw["stored_receipt"]
    if stored is not None:
        parse_receipt_record(stored, "stored_receipt")
        ensure(
            (stored["source_id"], stored["receipt_id"])
            == (
                raw["submitted_receipt"]["source_id"],
                raw["submitted_receipt"]["receipt_id"],
            ),
            "stored/submitted receipt key mismatch",
        )

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
        return {**base, "result": "INDETERMINATE", "primary_reason": "RECEIPT_LOOKUP_UNAVAILABLE", "reason_codes": ["RECEIPT_LOOKUP_UNAVAILABLE"], "event_created": False, "reconciliation_opened": False, "current_projection_advanced": False, "task_advancement_eligible": False}
    if relation == "EXACT_DUPLICATE":
        return {**base, "result": "REPLAYED", "primary_reason": "EXACT_DUPLICATE_REPLAY", "reason_codes": [], "event_created": False, "reconciliation_opened": False, "current_projection_advanced": False, "task_advancement_eligible": False}
    if relation == "CHANGED_BYTES_SAME_KEY":
        return {**base, "result": "REJECTED", "primary_reason": "RECEIPT_BYTES_CONFLICT", "reason_codes": ["RECEIPT_BYTES_CONFLICT"], "event_created": False, "reconciliation_opened": True, "current_projection_advanced": False, "task_advancement_eligible": False}

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
    precedence = "INTEGRITY_FAILURE SOURCE_ATTESTATION_INVALID ATTEMPT_OR_EFFECT_MISMATCH EXISTING_EFFECT_QUERY_INVALID RECEIPT_KIND_STATUS_MISMATCH TRANSITION_INVALID SOURCE_ATTESTATION_UNAVAILABLE EPOCH_STALE FENCE_STALE ATTEMPT_STALE".split()
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


def validate_arm_payload(payload: dict[str, Any], path: str) -> None:
    ensure(set(payload) == ARM_PAYLOAD_FIELDS, f"arm payload inventory invalid at {path}")
    ensure(payload["payload_interface"] == ARM_PAYLOAD_INTERFACE, f"arm payload interface invalid at {path}")
    for field in (
        "outbox_intent_ref",
        "claim_ref",
        "idempotency_key",
        "physical_boundary_observation_ref",
    ):
        stable_ref(payload[field], f"{path}.{field}")
    for field in (
        "outbox_intent_fingerprint",
        "bound_invocation_identity_fingerprint",
        "claim_fingerprint",
        "claim_fencing_token",
        "attempt_id",
        "physical_boundary_observation_fingerprint",
    ):
        sha(payload[field], f"{path}.{field}")
    for field in ("claim_epoch", "attempt_ordinal"):
        safe_int(payload[field], f"{path}.{field}", positive=True)
    for field in ("requested_at_utc_ms", "requested_event_sequence"):
        safe_int(payload[field], f"{path}.{field}")
    ensure(
        payload["attempt_id"]
        == h(
            "agents-os.f5-delivery-attempt-id.v0.1",
            payload["outbox_intent_fingerprint"],
            payload["attempt_ordinal"],
        ),
        f"attempt ID formula mismatch at {path}",
    )


def parse_request_record(record: Any, path: str) -> dict[str, Any]:
    ensure(isinstance(record, dict) and set(record) == ARM_RECORD_FIELDS, f"request record inventory invalid at {path}")
    sha(record["request_id"], f"{path}.request_id")
    sha(record["request_fingerprint"], f"{path}.request_fingerprint")
    encoded, payload = decode_bound_json(record["request_canonical_utf8_hex"], f"{path}.request_canonical_utf8_hex")
    validate_arm_payload(payload, path + ".payload")
    ensure(hashlib.sha256(encoded).hexdigest() == record["request_fingerprint"], f"request fingerprint formula mismatch at {path}")
    ensure(
        record["request_id"]
        == h(
            "agents-os.f5-dispatch-arm-request-id.v0.1",
            payload["outbox_intent_fingerprint"],
            payload["bound_invocation_identity_fingerprint"],
            payload["attempt_ordinal"],
        ),
        f"request ID formula mismatch at {path}",
    )
    return payload


def reduce_arm(raw: Any) -> dict[str, Any]:
    ensure(isinstance(raw, dict) and set(raw) == ARM_RAW_FIELDS, "arm raw inventory invalid")
    boolean(raw["lookup_reproducible"], "arm_raw.lookup_reproducible")
    sha(raw["bound_invocation_identity_fingerprint"], "arm_raw.bound_invocation_identity_fingerprint")
    ensure(raw["first_apply_eligibility"] in {"ELIGIBLE_PROOF_PRECONDITION", "NOT_ELIGIBLE"}, "first apply eligibility invalid")
    submitted_payload = parse_request_record(raw["submitted_request"], "submitted_request")
    ensure(
        submitted_payload["bound_invocation_identity_fingerprint"]
        == raw["bound_invocation_identity_fingerprint"],
        "submitted invocation mismatch",
    )
    stored = raw["stored_arm_state"]
    if stored is not None:
        ensure(isinstance(stored, dict) and set(stored) == STORED_ARM_FIELDS, "stored arm inventory invalid")
        stored_payload = parse_request_record(
            {key: stored[key] for key in ARM_RECORD_FIELDS},
            "stored_arm_state",
        )
        ensure(
            stored_payload["bound_invocation_identity_fingerprint"]
            == raw["bound_invocation_identity_fingerprint"],
            "stored invocation mismatch",
        )
        for field in (
            "first_arm_ref",
            "first_event_ref",
            "first_call_authorization_ref",
        ):
            stable_ref(stored[field], "stored_arm_state." + field)
        for field in (
            "first_arm_fingerprint",
            "first_event_fingerprint",
            "first_call_authorization_fingerprint",
        ):
            sha(stored[field], "stored_arm_state." + field)
        for field in ("committed_event_count", "committed_call_authorization_count"):
            safe_int(stored[field], "stored_arm_state." + field)
            ensure(stored[field] == 1, "stored-first accounting must equal one")
        ensure(
            stored["request_id"] == raw["submitted_request"]["request_id"],
            "stored/submitted request identity mismatch",
        )

    if not raw["lookup_reproducible"]:
        relation = "LOOKUP_INDETERMINATE"
    elif stored is None:
        relation = "NO_EXISTING_ARM"
    elif all(
        stored[key] == raw["submitted_request"][key]
        for key in ("request_id", "request_fingerprint", "request_canonical_utf8_hex")
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
        "returned_first_call_authorization_ref": stored["first_call_authorization_ref"] if exact else None,
        "returned_first_call_authorization_fingerprint": stored["first_call_authorization_fingerprint"] if exact else None,
        "modeled_event_delta": event_delta,
        "modeled_call_authorization_delta": call_delta,
        "total_event_count": stored["committed_event_count"] if stored is not None else event_delta,
        "total_call_authorization_count": stored["committed_call_authorization_count"] if stored is not None else call_delta,
    }


def validate_profiles(fixture: dict[str, Any]) -> None:
    ensure(
        fixture["receipt_record_profile"]
        == {
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
        "receipt profile mismatch",
    )
    ensure(
        fixture["arm_request_profile"]
        == {
            "record_fields": [
                "request_canonical_utf8_hex",
                "request_fingerprint",
                "request_id",
            ],
            "payload_interface": ARM_PAYLOAD_INTERFACE,
            "stored_submitted_identity_check_position": "BEFORE_LOOKUP_BRANCH",
            "different_identity_result": "REJECT_PROOF_INPUT",
        },
        "arm profile mismatch",
    )


def validate_cases(fixture: dict[str, Any]) -> None:
    receipt_cases = fixture["receipt_replay_cases"]
    ensure(isinstance(receipt_cases, list) and len(receipt_cases) == 5, "receipt case count invalid")
    ensure(
        [row["case_id"] for row in receipt_cases]
        == [
            "RECEIPT_BOUND_1_NEW",
            "RECEIPT_BOUND_2_EXACT",
            "RECEIPT_BOUND_3_CHANGED_BYTES",
            "RECEIPT_BOUND_4_LOOKUP_INDETERMINATE",
            "RECEIPT_BOUND_5_INCOMPATIBLE_NEW",
        ],
        "receipt case IDs invalid",
    )
    for index, row in enumerate(receipt_cases):
        ensure(
            isinstance(row, dict)
            and set(row) == {"case_id", "proof_mode", "raw_input", "derived"},
            f"receipt row inventory invalid at {index}",
        )
        ensure(row["proof_mode"] == "ABSTRACT_NONOCCURRING_REDUCER_TRIAL", "receipt proof mode invalid")
        ensure(
            isinstance(row["derived"], dict)
            and set(row["derived"]) == RECEIPT_DERIVED_FIELDS,
            "receipt derived inventory invalid",
        )
        ensure(row["derived"] == reduce_receipt(row["raw_input"]), f"receipt derivation mismatch at {index}")

    arm_cases = fixture["arm_identity_cases"]
    ensure(isinstance(arm_cases, list) and len(arm_cases) == 4, "arm case count invalid")
    ensure(
        [row["case_id"] for row in arm_cases]
        == [
            "ARM_IDENTITY_1_FIRST",
            "ARM_IDENTITY_2_EXACT",
            "ARM_IDENTITY_3_CHANGED_BYTES",
            "ARM_IDENTITY_4_LOOKUP_INDETERMINATE_EQUAL_IDENTITY",
        ],
        "arm case IDs invalid",
    )
    for index, row in enumerate(arm_cases):
        ensure(
            isinstance(row, dict)
            and set(row) == {"case_id", "proof_mode", "raw_input", "derived"},
            f"arm row inventory invalid at {index}",
        )
        ensure(row["proof_mode"] == "ABSTRACT_NONOCCURRING_REDUCER_TRIAL", "arm proof mode invalid")
        ensure(
            isinstance(row["derived"], dict)
            and set(row["derived"]) == ARM_DERIVED_FIELDS,
            "arm derived inventory invalid",
        )
        ensure(row["derived"] == reduce_arm(row["raw_input"]), f"arm derivation mismatch at {index}")


def validate_assertions(fixture: dict[str, Any]) -> None:
    expected = {
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
    ensure(fixture["assertions"] == expected, "assertions mismatch")
    ensure(fixture["adversarial_cases"] == EXPECTED_ADVERSARIAL_CASES, "adversarial inventory mismatch")
    ensure(
        fixture["summary"]
        == {
            "receipt_replay_case_count": 5,
            "arm_identity_case_count": 4,
            "adversarial_case_count": 9,
            "receipt_exact_case_count": 1,
            "arm_lookup_equal_identity_case_count": 1,
            "real_effect_count": 0,
        },
        "summary mismatch",
    )


def validate_fixture(fixture: Any, *, run_mutations: bool = True) -> dict[str, Any]:
    ensure(isinstance(fixture, dict) and set(fixture) == ROOT_FIELDS, "root inventory invalid")
    validate_json_value(fixture)
    ensure(fixture["fixture_interface"] == FIXTURE_INTERFACE, "fixture interface invalid")
    ensure(fixture["environment"] == "SYNTHETIC_TEST", "fixture environment invalid")
    ensure(fixture["authority_eligible"] is False, "fixture authority must be false")
    ensure(fixture["runtime_consumable"] is False, "fixture runtime consumability must be false")
    ensure(fixture["recovery_importable"] is False, "fixture recovery importability must be false")
    validate_profiles(fixture)
    validate_cases(fixture)
    validate_assertions(fixture)
    for section in SECTIONS:
        ensure(
            fixture[section + "_fingerprint"] == digest(fixture[section]),
            f"section fingerprint mismatch: {section}",
        )
    ensure(
        fixture["fixture_canonical_sha256"]
        == digest({key: value for key, value in fixture.items() if key != "fixture_canonical_sha256"}),
        "fixture canonical fingerprint mismatch",
    )
    mutation_counts = run_mutation_suite(fixture) if run_mutations else {}
    return {
        "result": "PASS_NO_BLOCKER",
        "receipt_replay_case_count": 5,
        "arm_identity_case_count": 4,
        "adversarial_case_count": 9,
        **mutation_counts,
        "accepted_real_handoff_count": 0,
        "claim_event_count": 0,
        "armed_dispatch_count": 0,
        "runtime_consumable_count": 0,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }


def resign_section(fixture: dict[str, Any], section: str) -> None:
    fixture[section + "_fingerprint"] = digest(fixture[section])


def resign_root(fixture: dict[str, Any]) -> None:
    fixture["fixture_canonical_sha256"] = digest(
        {key: value for key, value in fixture.items() if key != "fixture_canonical_sha256"}
    )


def rejected(fixture: dict[str, Any]) -> bool:
    try:
        validate_fixture(fixture, run_mutations=False)
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        return True
    return False


def make_receipt_record(*, kind: str, status: str, observed_at_utc_ms: int = 1700) -> dict[str, Any]:
    exact_case = _BASE_FOR_MUTATION["receipt_replay_cases"][1]
    original = parse_receipt_record(exact_case["raw_input"]["submitted_receipt"], "mutation_source")
    payload = copy.deepcopy(original)
    payload["receipt_kind"] = kind
    payload["effect_status"] = status
    payload["observed_at_utc_ms"] = observed_at_utc_ms
    encoded = canonical_bytes(payload)
    return {
        "source_id": payload["source_id"],
        "receipt_id": payload["receipt_id"],
        "receipt_fingerprint": hashlib.sha256(encoded).hexdigest(),
        "receipt_canonical_utf8_hex": encoded.hex(),
    }


def make_request_record(*, attempt_ordinal: int, requested_at_utc_ms: int = 1000) -> dict[str, Any]:
    source = _BASE_FOR_MUTATION["arm_identity_cases"][0]["raw_input"]["submitted_request"]
    payload = parse_request_record(source, "mutation_source")
    payload = copy.deepcopy(payload)
    payload["attempt_ordinal"] = attempt_ordinal
    payload["attempt_id"] = h(
        "agents-os.f5-delivery-attempt-id.v0.1",
        payload["outbox_intent_fingerprint"],
        attempt_ordinal,
    )
    payload["requested_at_utc_ms"] = requested_at_utc_ms
    encoded = canonical_bytes(payload)
    return {
        "request_id": h(
            "agents-os.f5-dispatch-arm-request-id.v0.1",
            payload["outbox_intent_fingerprint"],
            payload["bound_invocation_identity_fingerprint"],
            attempt_ordinal,
        ),
        "request_fingerprint": hashlib.sha256(encoded).hexdigest(),
        "request_canonical_utf8_hex": encoded.hex(),
    }


_BASE_FOR_MUTATION: dict[str, Any] = {}


def run_mutation_suite(base: dict[str, Any]) -> dict[str, Any]:
    global _BASE_FOR_MUTATION
    _BASE_FOR_MUTATION = base
    mutations: list[tuple[str, dict[str, Any]]] = []

    item = copy.deepcopy(base)
    exact_raw = item["receipt_replay_cases"][1]["raw_input"]
    exact_raw["receipt_kind"] = "TRANSPORT_ACK"
    exact_raw["effect_status"] = "ACKED_ONLY"
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("original_R3_receipt_probe", item))

    item = copy.deepcopy(base)
    item["receipt_replay_cases"][1]["raw_input"]["submitted_receipt"] = make_receipt_record(
        kind="TRANSPORT_ACK",
        status="ACKED_ONLY",
    )
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("bound_submitted_receipt_change", item))

    item = copy.deepcopy(base)
    item["receipt_replay_cases"][1]["raw_input"]["stored_receipt"] = make_receipt_record(
        kind="EFFECT_SUCCEEDED",
        status="SUCCEEDED",
        observed_at_utc_ms=1699,
    )
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("bound_stored_receipt_change", item))

    item = copy.deepcopy(base)
    record = item["receipt_replay_cases"][0]["raw_input"]["submitted_receipt"]
    payload = parse_receipt_record(record, "mutation_receipt")
    noncanonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    record["receipt_canonical_utf8_hex"] = noncanonical.hex()
    record["receipt_fingerprint"] = hashlib.sha256(noncanonical).hexdigest()
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("noncanonical_receipt_bytes", item))

    item = copy.deepcopy(base)
    item["receipt_replay_cases"][0]["raw_input"]["submitted_receipt"]["receipt_fingerprint"] = "f" * 64
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("wrong_receipt_fingerprint", item))

    item = copy.deepcopy(base)
    item["receipt_replay_cases"][0]["raw_input"]["submitted_receipt"]["source_id"] = "synthetic-f5-r5:wrong-source"
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("receipt_outer_key_mismatch", item))

    item = copy.deepcopy(base)
    item["arm_identity_cases"][3]["raw_input"]["submitted_request"] = make_request_record(
        attempt_ordinal=2
    )
    resign_section(item, "arm_identity_cases")
    resign_root(item)
    mutations.append(("lookup_indeterminate_different_request_identity", item))

    item = copy.deepcopy(base)
    record = item["arm_identity_cases"][0]["raw_input"]["submitted_request"]
    payload = parse_request_record(record, "mutation_request")
    noncanonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    record["request_canonical_utf8_hex"] = noncanonical.hex()
    record["request_fingerprint"] = hashlib.sha256(noncanonical).hexdigest()
    resign_section(item, "arm_identity_cases")
    resign_root(item)
    mutations.append(("noncanonical_arm_request", item))

    item = copy.deepcopy(base)
    item["unknown_root"] = True
    resign_root(item)
    mutations.append(("unknown_root", item))

    item = copy.deepcopy(base)
    item["receipt_record_profile"]["unknown_section_field"] = True
    resign_section(item, "receipt_record_profile")
    resign_root(item)
    mutations.append(("unknown_section", item))

    item = copy.deepcopy(base)
    item["receipt_replay_cases"][0]["unknown_row_field"] = True
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("unknown_row", item))

    item = copy.deepcopy(base)
    item["receipt_replay_cases"][0]["raw_input"]["unknown_nested_raw_field"] = True
    resign_section(item, "receipt_replay_cases")
    resign_root(item)
    mutations.append(("unknown_nested_raw", item))

    rejected_names = [name for name, mutation in mutations if rejected(mutation)]
    ensure(len(rejected_names) == len(mutations), "a fully re-signed R5 mutation was accepted")
    ensure("original_R3_receipt_probe" in rejected_names, "original R3 receipt probe accepted")
    ensure(
        "lookup_indeterminate_different_request_identity" in rejected_names,
        "R4 lookup-indeterminate identity probe accepted",
    )
    return {
        "fully_resigned_mutations_rejected": len(mutations),
        "receipt_binding_mutations_rejected": 6,
        "arm_identity_mutations_rejected": 2,
        "closed_inventory_mutations_rejected": 4,
        "original_R3_receipt_probe_rejected": True,
        "R4_lookup_indeterminate_different_identity_probe_rejected": True,
    }


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
