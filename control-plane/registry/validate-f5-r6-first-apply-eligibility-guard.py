#!/usr/bin/env python3
"""Validate the fixed nonauthority F5 R6 first-apply eligibility guard."""

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
    "2026-07-17-agents-os-f5-r6-first-apply-eligibility-guard-v0.1.json"
)
FIXTURE_INTERFACE = "agents-os.f5-r6-first-apply-eligibility-guard-fixture.v0.1"
ARM_PAYLOAD_INTERFACE = "agents-os.f5-dispatch-arm-replay-request-payload.v0.1-r4"
SAFE_INTEGER = 9007199254740991
SHA_RE = re.compile(r"[0-9a-f]{64}")
HEX_RE = re.compile(r"(?:[0-9a-f]{2})+")

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
ARM_RECORD_FIELDS = {"request_id", "request_fingerprint", "request_canonical_utf8_hex"}
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
RAW_FIELDS = {
    "lookup_reproducible",
    "bound_invocation_identity_fingerprint",
    "stored_arm_state",
    "submitted_request",
    "first_apply_eligibility",
}
DERIVED_FIELDS = {
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
CASE_IDS = [
    "FIRST_APPLY_1_ELIGIBLE",
    "FIRST_APPLY_2_NOT_ELIGIBLE",
    "FIRST_APPLY_3_EXACT_REPLAY",
    "FIRST_APPLY_4_CHANGED_BYTES",
    "FIRST_APPLY_5_LOOKUP_INDETERMINATE",
]
SECTIONS = ("arm_guard_profile", "arm_guard_cases", "adversarial_cases", "assertions", "summary")
ROOT_FIELDS = {
    "fixture_interface",
    "environment",
    "authority_eligible",
    "runtime_consumable",
    "recovery_importable",
    "fixture_canonical_sha256",
} | set(SECTIONS) | {section + "_fingerprint" for section in SECTIONS}
EXPECTED_ADVERSARIAL = [
    {"check": "exact_R5_not_eligible_presented_as_APPLIED_one_Event_one_call", "expected_decision": "REJECT_DERIVATION_MISMATCH"},
    {"check": "eligible_first_apply_presented_as_NOT_ELIGIBLE_rejection", "expected_decision": "REJECT_DERIVATION_MISMATCH"},
    {"check": "not_eligible_first_apply_nonzero_Event_delta", "expected_decision": "REJECT_DERIVATION_MISMATCH"},
    {"check": "not_eligible_first_apply_nonzero_call_delta", "expected_decision": "REJECT_DERIVATION_MISMATCH"},
    {"check": "unknown_first_apply_eligibility_enum", "expected_decision": "REJECT_CLOSED_ENUM"},
    {"check": "unknown_root_section_row_or_raw_field", "expected_decision": "REJECT_CLOSED_INVENTORY"},
]


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        ensure(key not in result, f"duplicate JSON key {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> Any:
    raise ValueError(f"non-JSON constant {value}")


def parse_strict(text: str) -> Any:
    return json.loads(text, object_pairs_hook=unique_pairs, parse_constant=reject_constant)


def validate_json(value: Any, path: str = "$") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        ensure(abs(value) <= SAFE_INTEGER, f"unsafe integer at {path}")
        return
    ensure(type(value) is not float, f"float forbidden at {path}")
    if isinstance(value, str):
        ensure(unicodedata.normalize("NFC", value) == value, f"non-NFC at {path}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_json(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            ensure(isinstance(key, str), f"non-string key at {path}")
            validate_json(key, f"{path}.<key>")
            validate_json(item, f"{path}.{key}")
        return
    raise ValueError(f"invalid JSON at {path}")


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


def parse_request(record: Any, path: str) -> dict[str, Any]:
    ensure(isinstance(record, dict) and set(record) == ARM_RECORD_FIELDS, f"request inventory invalid at {path}")
    sha(record["request_id"], path + ".request_id")
    sha(record["request_fingerprint"], path + ".request_fingerprint")
    hex_text = record["request_canonical_utf8_hex"]
    ensure(isinstance(hex_text, str) and HEX_RE.fullmatch(hex_text) is not None, f"request hex invalid at {path}")
    encoded = bytes.fromhex(hex_text)
    payload = parse_strict(encoded.decode("utf-8"))
    ensure(isinstance(payload, dict) and set(payload) == ARM_PAYLOAD_FIELDS, f"payload inventory invalid at {path}")
    validate_json(payload, path + ".payload")
    ensure(encoded == canonical_bytes(payload), f"noncanonical request at {path}")
    ensure(payload["payload_interface"] == ARM_PAYLOAD_INTERFACE, f"payload interface invalid at {path}")
    for field in ("outbox_intent_ref", "claim_ref", "idempotency_key", "physical_boundary_observation_ref"):
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
        == h("agents-os.f5-delivery-attempt-id.v0.1", payload["outbox_intent_fingerprint"], payload["attempt_ordinal"]),
        f"attempt ID formula mismatch at {path}",
    )
    ensure(hashlib.sha256(encoded).hexdigest() == record["request_fingerprint"], f"request fingerprint mismatch at {path}")
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
    ensure(isinstance(raw, dict) and set(raw) == RAW_FIELDS, "raw inventory invalid")
    ensure(type(raw["lookup_reproducible"]) is bool, "lookup flag invalid")
    sha(raw["bound_invocation_identity_fingerprint"], "bound invocation")
    ensure(
        raw["first_apply_eligibility"] in {"ELIGIBLE_PROOF_PRECONDITION", "NOT_ELIGIBLE"},
        "first apply eligibility invalid",
    )
    submitted_payload = parse_request(raw["submitted_request"], "submitted")
    ensure(
        submitted_payload["bound_invocation_identity_fingerprint"]
        == raw["bound_invocation_identity_fingerprint"],
        "submitted invocation mismatch",
    )
    stored = raw["stored_arm_state"]
    if stored is not None:
        ensure(isinstance(stored, dict) and set(stored) == STORED_ARM_FIELDS, "stored inventory invalid")
        stored_payload = parse_request({key: stored[key] for key in ARM_RECORD_FIELDS}, "stored")
        ensure(
            stored_payload["bound_invocation_identity_fingerprint"]
            == raw["bound_invocation_identity_fingerprint"],
            "stored invocation mismatch",
        )
        ensure(stored["request_id"] == raw["submitted_request"]["request_id"], "request identity mismatch")
        for field in ("first_arm_ref", "first_event_ref", "first_call_authorization_ref"):
            stable_ref(stored[field], "stored." + field)
        for field in ("first_arm_fingerprint", "first_event_fingerprint", "first_call_authorization_fingerprint"):
            sha(stored[field], "stored." + field)
        ensure(
            stored["committed_event_count"] == 1
            and stored["committed_call_authorization_count"] == 1,
            "stored-first accounting invalid",
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
    if relation == "NO_EXISTING_ARM" and raw["first_apply_eligibility"] != "ELIGIBLE_PROOF_PRECONDITION":
        result, reason, event_delta, call_delta = "REJECTED", "FIRST_APPLY_NOT_ELIGIBLE", 0, 0
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


def validate_fixture(fixture: Any, *, run_mutations: bool = True) -> dict[str, Any]:
    ensure(isinstance(fixture, dict) and set(fixture) == ROOT_FIELDS, "root inventory invalid")
    validate_json(fixture)
    ensure(fixture["fixture_interface"] == FIXTURE_INTERFACE, "fixture interface invalid")
    ensure(fixture["environment"] == "SYNTHETIC_TEST", "environment invalid")
    ensure(fixture["authority_eligible"] is False, "authority must be false")
    ensure(fixture["runtime_consumable"] is False, "runtime must be false")
    ensure(fixture["recovery_importable"] is False, "recovery import must be false")
    ensure(
        fixture["arm_guard_profile"]
        == {
            "first_apply_relation": "NO_EXISTING_ARM",
            "eligible_value": "ELIGIBLE_PROOF_PRECONDITION",
            "eligible_result": "APPLIED_ONE_EVENT_ONE_CALL",
            "not_eligible_value": "NOT_ELIGIBLE",
            "not_eligible_result": "REJECTED_ZERO_EVENT_ZERO_CALL",
            "guard_position": "AFTER_RELATION_DERIVATION_BEFORE_ACCOUNTING_OUTPUT",
        },
        "guard profile mismatch",
    )
    cases = fixture["arm_guard_cases"]
    ensure(isinstance(cases, list) and len(cases) == 5, "case count invalid")
    ensure([row["case_id"] for row in cases] == CASE_IDS, "case IDs invalid")
    for index, row in enumerate(cases):
        ensure(
            isinstance(row, dict)
            and set(row) == {"case_id", "proof_mode", "raw_input", "derived"},
            f"case inventory invalid at {index}",
        )
        ensure(row["proof_mode"] == "ABSTRACT_NONOCCURRING_REDUCER_TRIAL", "proof mode invalid")
        ensure(isinstance(row["derived"], dict) and set(row["derived"]) == DERIVED_FIELDS, "derived inventory invalid")
        ensure(row["derived"] == reduce_arm(row["raw_input"]), f"derivation mismatch at {index}")
    ensure(fixture["adversarial_cases"] == EXPECTED_ADVERSARIAL, "adversarial inventory mismatch")
    ensure(
        fixture["assertions"]
        == {
            "synthetic_nonauthority": True,
            "receipt_replay_semantics_changed": False,
            "accepted_real_handoff_count": 0,
            "claim_event_count": 0,
            "armed_dispatch_count": 0,
            "runtime_consumable_count": 0,
            "external_effect_count": 0,
            "provider_call_count": 0,
            "raw_secret_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        },
        "assertions mismatch",
    )
    ensure(
        fixture["summary"]
        == {
            "arm_guard_case_count": 5,
            "first_apply_case_count": 2,
            "adversarial_case_count": 6,
            "real_effect_count": 0,
        },
        "summary mismatch",
    )
    for section in SECTIONS:
        ensure(fixture[section + "_fingerprint"] == digest(fixture[section]), f"section fingerprint mismatch {section}")
    ensure(
        fixture["fixture_canonical_sha256"]
        == digest({key: value for key, value in fixture.items() if key != "fixture_canonical_sha256"}),
        "root fingerprint mismatch",
    )
    counts = mutation_suite(fixture) if run_mutations else {}
    return {
        "result": "PASS_NO_BLOCKER",
        "arm_guard_case_count": 5,
        "eligible_first_apply_count": 1,
        "not_eligible_first_apply_count": 1,
        **counts,
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


def mutation_suite(base: dict[str, Any]) -> dict[str, Any]:
    mutations: list[tuple[str, dict[str, Any]]] = []

    item = copy.deepcopy(base)
    item["arm_guard_cases"][0]["raw_input"]["first_apply_eligibility"] = "NOT_ELIGIBLE"
    resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("exact_R5_counterexample", item))

    item = copy.deepcopy(base)
    item["arm_guard_cases"][1]["raw_input"]["first_apply_eligibility"] = "ELIGIBLE_PROOF_PRECONDITION"
    resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("inverse_eligibility_mutation", item))

    item = copy.deepcopy(base)
    item["arm_guard_cases"][1]["derived"]["modeled_event_delta"] = 1
    resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("not_eligible_event_delta", item))

    item = copy.deepcopy(base)
    item["arm_guard_cases"][1]["derived"]["modeled_call_authorization_delta"] = 1
    resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("not_eligible_call_delta", item))

    item = copy.deepcopy(base)
    item["arm_guard_cases"][0]["raw_input"]["first_apply_eligibility"] = "UNKNOWN"
    resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("unknown_eligibility", item))

    item = copy.deepcopy(base); item["unknown_root"] = True; resign_root(item)
    mutations.append(("unknown_root", item))
    item = copy.deepcopy(base); item["arm_guard_profile"]["unknown"] = True; resign_section(item, "arm_guard_profile"); resign_root(item)
    mutations.append(("unknown_section", item))
    item = copy.deepcopy(base); item["arm_guard_cases"][0]["unknown"] = True; resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("unknown_row", item))
    item = copy.deepcopy(base); item["arm_guard_cases"][0]["raw_input"]["unknown"] = True; resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("unknown_raw", item))

    item = copy.deepcopy(base)
    record = item["arm_guard_cases"][0]["raw_input"]["submitted_request"]
    payload = parse_request(record, "mutation")
    noncanonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
    record["request_canonical_utf8_hex"] = noncanonical.hex()
    record["request_fingerprint"] = hashlib.sha256(noncanonical).hexdigest()
    resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("noncanonical_request", item))

    item = copy.deepcopy(base)
    item["arm_guard_cases"][0]["raw_input"]["submitted_request"]["request_fingerprint"] = "f" * 64
    resign_section(item, "arm_guard_cases"); resign_root(item)
    mutations.append(("wrong_request_fingerprint", item))

    rejected_names = [name for name, item in mutations if rejected(item)]
    ensure(len(rejected_names) == len(mutations), "a fully re-signed R6 mutation was accepted")
    ensure("exact_R5_counterexample" in rejected_names, "exact R5 counterexample accepted")
    return {
        "fully_resigned_mutations_rejected": len(mutations),
        "exact_R5_counterexample_rejected": True,
        "inverse_eligibility_mutation_rejected": True,
        "closed_inventory_mutations_rejected": 4,
    }


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    try:
        fixture = parse_strict(path.read_text(encoding="utf-8"))
        result = validate_fixture(fixture)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"result": "BLOCK", "error": str(exc)}, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
