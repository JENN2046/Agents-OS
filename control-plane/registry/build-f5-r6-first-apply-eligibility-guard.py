#!/usr/bin/env python3
"""Build the deterministic nonauthority F5 R6 first-apply guard fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path(
    "control-plane/registry/examples/"
    "2026-07-17-agents-os-f5-r6-first-apply-eligibility-guard-v0.1.json"
)
FIXTURE_INTERFACE = "agents-os.f5-r6-first-apply-eligibility-guard-fixture.v0.1"
ARM_PAYLOAD_INTERFACE = "agents-os.f5-dispatch-arm-replay-request-payload.v0.1-r4"
SECTIONS = ("arm_guard_profile", "arm_guard_cases", "adversarial_cases", "assertions", "summary")


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
    return hashlib.sha256(("f5-r6:" + label).encode("utf-8")).hexdigest()


def request_payload(*, requested_at_utc_ms: int = 1000) -> dict[str, Any]:
    intent_fingerprint = hx("arm-intent")
    invocation_fingerprint = hx("arm-invocation")
    return {
        "payload_interface": ARM_PAYLOAD_INTERFACE,
        "outbox_intent_ref": "synthetic-f5-r6:arm-intent",
        "outbox_intent_fingerprint": intent_fingerprint,
        "bound_invocation_identity_fingerprint": invocation_fingerprint,
        "claim_ref": "synthetic-f5-r6:arm-claim",
        "claim_fingerprint": hx("arm-claim"),
        "claim_epoch": 1,
        "claim_fencing_token": hx("arm-fence"),
        "attempt_ordinal": 1,
        "attempt_id": h(
            "agents-os.f5-delivery-attempt-id.v0.1",
            intent_fingerprint,
            1,
        ),
        "idempotency_key": "synthetic-f5-r6:idempotency-key",
        "physical_boundary_observation_ref": "synthetic-f5-r6:boundary-observation",
        "physical_boundary_observation_fingerprint": hx("arm-boundary-observation"),
        "requested_at_utc_ms": requested_at_utc_ms,
        "requested_event_sequence": 21,
    }


def request_record(*, requested_at_utc_ms: int = 1000) -> dict[str, Any]:
    payload = request_payload(requested_at_utc_ms=requested_at_utc_ms)
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


def decode_request(record: dict[str, Any]) -> dict[str, Any]:
    encoded = bytes.fromhex(record["request_canonical_utf8_hex"])
    payload = json.loads(encoded.decode("utf-8"))
    if encoded != canonical_bytes(payload):
        raise ValueError("noncanonical request")
    if hashlib.sha256(encoded).hexdigest() != record["request_fingerprint"]:
        raise ValueError("request fingerprint mismatch")
    expected_id = h(
        "agents-os.f5-dispatch-arm-request-id.v0.1",
        payload["outbox_intent_fingerprint"],
        payload["bound_invocation_identity_fingerprint"],
        payload["attempt_ordinal"],
    )
    if record["request_id"] != expected_id:
        raise ValueError("request ID mismatch")
    return payload


def stored_arm(record: dict[str, Any]) -> dict[str, Any]:
    return {
        **record,
        "first_arm_ref": "synthetic-f5-r6:first-arm",
        "first_arm_fingerprint": hx("first-arm"),
        "first_event_ref": "synthetic-f5-r6:first-event",
        "first_event_fingerprint": hx("first-event"),
        "first_call_authorization_ref": "synthetic-f5-r6:first-call",
        "first_call_authorization_fingerprint": hx("first-call"),
        "committed_event_count": 1,
        "committed_call_authorization_count": 1,
    }


def derive(raw: dict[str, Any]) -> dict[str, Any]:
    submitted_payload = decode_request(raw["submitted_request"])
    if (
        submitted_payload["bound_invocation_identity_fingerprint"]
        != raw["bound_invocation_identity_fingerprint"]
    ):
        raise ValueError("submitted invocation mismatch")
    stored = raw["stored_arm_state"]
    if stored is not None:
        stored_payload = decode_request(
            {
                key: stored[key]
                for key in ("request_id", "request_fingerprint", "request_canonical_utf8_hex")
            }
        )
        if (
            stored_payload["bound_invocation_identity_fingerprint"]
            != raw["bound_invocation_identity_fingerprint"]
        ):
            raise ValueError("stored invocation mismatch")
        if stored["request_id"] != raw["submitted_request"]["request_id"]:
            raise ValueError("stored/submitted identity mismatch")

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
    if (
        relation == "NO_EXISTING_ARM"
        and raw["first_apply_eligibility"] != "ELIGIBLE_PROOF_PRECONDITION"
    ):
        result = "REJECTED"
        reason = "FIRST_APPLY_NOT_ELIGIBLE"
        event_delta = 0
        call_delta = 0

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
    base = request_record()
    changed = request_record(requested_at_utc_ms=1001)
    stored = stored_arm(base)
    invocation = hx("arm-invocation")
    raws = [
        (
            "FIRST_APPLY_1_ELIGIBLE",
            {
                "lookup_reproducible": True,
                "bound_invocation_identity_fingerprint": invocation,
                "stored_arm_state": None,
                "submitted_request": base,
                "first_apply_eligibility": "ELIGIBLE_PROOF_PRECONDITION",
            },
        ),
        (
            "FIRST_APPLY_2_NOT_ELIGIBLE",
            {
                "lookup_reproducible": True,
                "bound_invocation_identity_fingerprint": invocation,
                "stored_arm_state": None,
                "submitted_request": base,
                "first_apply_eligibility": "NOT_ELIGIBLE",
            },
        ),
        (
            "FIRST_APPLY_3_EXACT_REPLAY",
            {
                "lookup_reproducible": True,
                "bound_invocation_identity_fingerprint": invocation,
                "stored_arm_state": stored,
                "submitted_request": base,
                "first_apply_eligibility": "NOT_ELIGIBLE",
            },
        ),
        (
            "FIRST_APPLY_4_CHANGED_BYTES",
            {
                "lookup_reproducible": True,
                "bound_invocation_identity_fingerprint": invocation,
                "stored_arm_state": stored,
                "submitted_request": changed,
                "first_apply_eligibility": "NOT_ELIGIBLE",
            },
        ),
        (
            "FIRST_APPLY_5_LOOKUP_INDETERMINATE",
            {
                "lookup_reproducible": False,
                "bound_invocation_identity_fingerprint": invocation,
                "stored_arm_state": stored,
                "submitted_request": base,
                "first_apply_eligibility": "NOT_ELIGIBLE",
            },
        ),
    ]
    cases = [
        {
            "case_id": case_id,
            "proof_mode": "ABSTRACT_NONOCCURRING_REDUCER_TRIAL",
            "raw_input": raw,
            "derived": derive(raw),
        }
        for case_id, raw in raws
    ]
    adversarial = [
        {
            "check": "exact_R5_not_eligible_presented_as_APPLIED_one_Event_one_call",
            "expected_decision": "REJECT_DERIVATION_MISMATCH",
        },
        {
            "check": "eligible_first_apply_presented_as_NOT_ELIGIBLE_rejection",
            "expected_decision": "REJECT_DERIVATION_MISMATCH",
        },
        {
            "check": "not_eligible_first_apply_nonzero_Event_delta",
            "expected_decision": "REJECT_DERIVATION_MISMATCH",
        },
        {
            "check": "not_eligible_first_apply_nonzero_call_delta",
            "expected_decision": "REJECT_DERIVATION_MISMATCH",
        },
        {
            "check": "unknown_first_apply_eligibility_enum",
            "expected_decision": "REJECT_CLOSED_ENUM",
        },
        {
            "check": "unknown_root_section_row_or_raw_field",
            "expected_decision": "REJECT_CLOSED_INVENTORY",
        },
    ]
    fixture: dict[str, Any] = {
        "fixture_interface": FIXTURE_INTERFACE,
        "environment": "SYNTHETIC_TEST",
        "authority_eligible": False,
        "runtime_consumable": False,
        "recovery_importable": False,
        "fixture_canonical_sha256": "",
        "arm_guard_profile": {
            "first_apply_relation": "NO_EXISTING_ARM",
            "eligible_value": "ELIGIBLE_PROOF_PRECONDITION",
            "eligible_result": "APPLIED_ONE_EVENT_ONE_CALL",
            "not_eligible_value": "NOT_ELIGIBLE",
            "not_eligible_result": "REJECTED_ZERO_EVENT_ZERO_CALL",
            "guard_position": "AFTER_RELATION_DERIVATION_BEFORE_ACCOUNTING_OUTPUT",
        },
        "arm_guard_cases": cases,
        "adversarial_cases": adversarial,
        "assertions": {
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
        "summary": {
            "arm_guard_case_count": len(cases),
            "first_apply_case_count": 2,
            "adversarial_case_count": len(adversarial),
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
