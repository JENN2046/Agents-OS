#!/usr/bin/env python3
"""Offline validator for F4 R3 PRESTART and start-disposition totality."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "control-plane/registry/examples/2026-07-16-agents-os-f4-r3-prestart-start-disposition-totality-vectors-v0.1.json"
CONTRACT = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R3_ATOMIC_BUNDLE"

CHECKS = [
    "integrity_current", "acceptance_current", "expiry_current",
    "host_identity_current", "host_authentication_current", "task_fence_match",
    "host_fence_match", "effect_fence_match", "execution_epoch_match",
    "secret_handles_current", "permit_attestation_current", "human_presence_current",
]
NA_FIELDS = {"secret_handles_current", "human_presence_current"}
TRI = {"PASS", "REJECTED", "INDETERMINATE"}
REASON_BY_CHECK = {
    "integrity_current": "INTEGRITY_FAILURE",
    "acceptance_current": "ACCEPTANCE_MISSING",
    "expiry_current": "EXPIRED",
    "host_identity_current": "HOST_UNAUTHENTICATED",
    "host_authentication_current": "HOST_UNAUTHENTICATED",
    "task_fence_match": "FENCED",
    "host_fence_match": "FENCED",
    "effect_fence_match": "FENCED",
    "execution_epoch_match": "EPOCH_STALE",
    "secret_handles_current": "SECRET_HANDLE_STALE",
    "permit_attestation_current": "ATTESTATION_STALE",
    "human_presence_current": "HUMAN_PRESENCE_STALE",
}
REJECTED_PRECEDENCE = [
    "INTEGRITY_FAILURE", "ACCEPTANCE_MISSING", "HOST_UNAUTHENTICATED",
    "FENCED", "EPOCH_STALE", "EXPIRED", "SECRET_HANDLE_STALE",
    "ATTESTATION_STALE", "HUMAN_PRESENCE_STALE",
]


def fail(message: str) -> None:
    raise ValueError(message)


def first_present(candidates: set[str]) -> str:
    for reason in REJECTED_PRECEDENCE:
        if reason in candidates:
            return reason
    fail("no ordered rejected reason")


def validate_checks(checks: dict[str, str]) -> None:
    if list(checks) != CHECKS:
        fail("check order or coverage mismatch")
    for field, value in checks.items():
        allowed = TRI | ({"NOT_APPLICABLE"} if field in NA_FIELDS else set())
        if value not in allowed:
            fail(f"invalid {field}={value}")


def derive_host(case: dict[str, Any]) -> list[str]:
    lifecycle = case.get("lifecycle")
    unavailable = case.get("unavailable")
    if lifecycle not in {"PRESTART", "ACTIVE"} or not isinstance(unavailable, list):
        fail("invalid Host case")
    if any(item not in {"VERIFIER_UNAVAILABLE", "REVOCATION_UNAVAILABLE", "UNKNOWN"} for item in unavailable):
        fail("unknown Host unavailable reason")
    if lifecycle == "PRESTART":
        return ["REJECTED", "PRESTART"]
    if unavailable:
        order = ["REVOCATION_UNAVAILABLE", "VERIFIER_UNAVAILABLE", "UNKNOWN"]
        return ["INDETERMINATE", next(item for item in order if item in unavailable)]
    return ["AUTHENTICATED", "MATCH"]


def derive_start(base: dict[str, str], case: dict[str, Any]) -> list[str]:
    overrides = case.get("overrides", {})
    if not isinstance(overrides, dict) or any(key not in CHECKS for key in overrides):
        fail("unknown start-disposition override")
    checks = {field: overrides.get(field, base[field]) for field in CHECKS}
    validate_checks(checks)
    candidates = {REASON_BY_CHECK[field] for field, value in checks.items() if value == "REJECTED"}
    if candidates:
        return ["NOT_STARTED", first_present(candidates)]
    if any(value == "INDETERMINATE" for value in checks.values()):
        return ["INDETERMINATE", "OBSERVATION_UNAVAILABLE"]
    return ["START_AUTHORITY_CURRENT", "ALL_RECHECKS_PASS"]


def validate_case(actual: list[str], case: dict[str, Any]) -> None:
    if actual != case.get("expected"):
        fail(f"{case.get('id')} expected {case.get('expected')} derived {actual}")


def validate_fixture(data: dict[str, Any]) -> dict[str, int]:
    if list(data) != ["interface_version", "contract_version", "host_prestart", "start_disposition"]:
        fail("top-level order mismatch")
    if data["interface_version"] != "agents-os.f4-r3-prestart-start-disposition-totality-vectors.v0.1":
        fail("interface mismatch")
    if data["contract_version"] != CONTRACT:
        fail("contract mismatch")
    host_cases = data["host_prestart"]["cases"]
    for case in host_cases:
        validate_case(derive_host(case), case)
    start = data["start_disposition"]
    validate_checks(start["base_checks"])
    start_cases = start["cases"]
    for case in start_cases:
        validate_case(derive_start(start["base_checks"], case), case)
    return {"host_case_count": len(host_cases), "start_disposition_case_count": len(start_cases)}


def negative_self_tests(data: dict[str, Any]) -> int:
    mutations = []
    host = copy.deepcopy(data)
    host["host_prestart"]["cases"][0]["expected"] = ["REJECTED", "NOT_YET_VALID"]
    mutations.append(host)
    start_result = copy.deepcopy(data)
    start_result["start_disposition"]["cases"][3]["expected"] = ["INDETERMINATE", "OBSERVATION_UNAVAILABLE"]
    mutations.append(start_result)
    start_reason = copy.deepcopy(data)
    start_reason["start_disposition"]["cases"][4]["expected"] = ["NOT_STARTED", "FENCED"]
    mutations.append(start_reason)
    rejected = 0
    for mutation in mutations:
        try:
            validate_fixture(mutation)
        except ValueError:
            rejected += 1
    if rejected != len(mutations):
        fail("negative mutation accepted")
    return rejected


def main() -> None:
    raw = FIXTURE.read_bytes()
    data = json.loads(raw)
    counts = validate_fixture(data)
    negative = negative_self_tests(data)
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    output = {
        "contract_version": CONTRACT,
        "external_effect_count": 0,
        "fixture_canonical_sha256": hashlib.sha256(canonical).hexdigest(),
        "fixture_file_sha256": hashlib.sha256(raw).hexdigest(),
        "host_case_count": counts["host_case_count"],
        "negative_mutations_rejected": negative,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "result": "PASS",
        "start_disposition_case_count": counts["start_disposition_case_count"],
        "total_case_count": sum(counts.values()),
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
