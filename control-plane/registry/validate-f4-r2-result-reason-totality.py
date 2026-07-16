#!/usr/bin/env python3
"""Offline validator for the F4 R2 result/reason totality vectors."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "control-plane/registry/examples/2026-07-16-agents-os-f4-r2-result-reason-totality-vectors-v0.1.json"
CONTRACT = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R2_ATOMIC_BUNDLE"

HOST_REJECTED = [
    "INTEGRITY_FAILURE", "COMPROMISED", "REVOKED", "RETIRED", "SUSPENDED",
    "PROFILE_MISMATCH", "CHALLENGE_MISMATCH", "EXPIRED", "NOT_YET_VALID",
]
HOST_INDETERMINATE = ["REVOCATION_UNAVAILABLE", "VERIFIER_UNAVAILABLE", "UNKNOWN"]
HOST_ALLOWED = set(HOST_REJECTED + HOST_INDETERMINATE + ["MATCH"])

PERMIT_CHECKS = [
    "task_binding_current", "actor_binding_current", "resident_command_binding_current",
    "host_identity_current", "host_authentication_current", "policy_current",
    "prohibited_boundary_current", "capability_grants_current", "resource_grants_current",
    "secret_handle_bindings_current", "permit_attestation_current", "human_presence_current",
    "Jenn_authorization_current", "time_window_current", "invocation_available",
    "execution_epoch_current", "host_fence_current", "effect_fence_current", "task_fence_current",
]
PERMIT_REASON_BY_CHECK = {
    "task_binding_current": "TASK_STALE",
    "actor_binding_current": "ACTOR_STALE",
    "resident_command_binding_current": "COMMAND_STALE",
    "host_identity_current": "HOST_STALE",
    "host_authentication_current": "AUTH_STALE",
    "policy_current": "POLICY_STALE",
    "prohibited_boundary_current": "PROHIBITED",
    "capability_grants_current": "CAPABILITY_STALE",
    "resource_grants_current": "RESOURCE_STALE",
    "secret_handle_bindings_current": "SECRET_HANDLE_STALE",
    "permit_attestation_current": "ATTESTATION_STALE",
    "human_presence_current": "HUMAN_PRESENCE_STALE",
    "Jenn_authorization_current": "AUTHORIZATION_STALE",
    "invocation_available": "INVOCATIONS_EXHAUSTED",
    "execution_epoch_current": "EPOCH_STALE",
    "host_fence_current": "FENCE_STALE",
    "effect_fence_current": "FENCE_STALE",
    "task_fence_current": "FENCE_STALE",
}
PERMIT_REJECTED = [
    "INTEGRITY_FAILURE", "PROHIBITED", "TERMINAL", "EXPIRED", "NOT_YET_VALID",
    "INVOCATIONS_EXHAUSTED", "TASK_STALE", "ACTOR_STALE", "COMMAND_STALE",
    "HOST_STALE", "AUTH_STALE", "POLICY_STALE", "CAPABILITY_STALE",
    "RESOURCE_STALE", "SECRET_HANDLE_STALE", "ATTESTATION_STALE",
    "HUMAN_PRESENCE_STALE", "AUTHORIZATION_STALE", "EPOCH_STALE", "FENCE_STALE",
]

ADMISSION_CHECKS = [
    "request_integrity", "permit_currentness", "host_authentication", "host_ownership",
    "task_fence_match", "host_fence_match", "effect_fence_match", "execution_epoch_match",
    "capability_subset", "resource_subset", "secret_handle_scope", "permit_attestation",
    "human_presence", "effect_intent_exact_match", "idempotency_identity_match",
    "invocation_slot_available", "prohibited_boundary", "Jenn_authorization",
]
ADMISSION_REASON_BY_CHECK = {
    "request_integrity": "INVALID_REQUEST",
    "permit_currentness": "PERMIT_INVALID",
    "host_authentication": "HOST_UNAUTHENTICATED",
    "host_ownership": "HOST_NOT_OWNER",
    "task_fence_match": "STALE_FENCE",
    "host_fence_match": "STALE_FENCE",
    "effect_fence_match": "STALE_FENCE",
    "execution_epoch_match": "STALE_EPOCH",
    "capability_subset": "CAPABILITY_DENIED",
    "resource_subset": "RESOURCE_DENIED",
    "secret_handle_scope": "SECRET_HANDLE_DENIED",
    "permit_attestation": "ATTESTATION_INVALID",
    "human_presence": "HUMAN_PRESENCE_MISSING",
    "effect_intent_exact_match": "EFFECT_MISMATCH",
    "idempotency_identity_match": "IDEMPOTENCY_CONFLICT",
    "invocation_slot_available": "INVOCATION_UNAVAILABLE",
    "prohibited_boundary": "PROHIBITED",
    "Jenn_authorization": "AUTHORIZATION_MISSING",
}
ADMISSION_REJECTED = [
    "INTEGRITY_FAILURE", "PROHIBITED", "INVALID_REQUEST", "PERMIT_INVALID",
    "HOST_UNAUTHENTICATED", "HOST_NOT_OWNER", "STALE_FENCE", "STALE_EPOCH",
    "CAPABILITY_DENIED", "RESOURCE_DENIED", "SECRET_HANDLE_DENIED",
    "ATTESTATION_INVALID", "HUMAN_PRESENCE_MISSING", "EFFECT_MISMATCH",
    "IDEMPOTENCY_CONFLICT", "INVOCATION_UNAVAILABLE", "AUTHORIZATION_MISSING",
]

TRI = {"PASS", "REJECTED", "INDETERMINATE"}
TRI_NA = TRI | {"NOT_APPLICABLE"}
PERMIT_NA = {"secret_handle_bindings_current", "human_presence_current", "Jenn_authorization_current"}
ADMISSION_NA = {"secret_handle_scope", "human_presence", "Jenn_authorization"}


def fail(message: str) -> None:
    raise ValueError(message)


def first_present(order: list[str], candidates: set[str]) -> str:
    for item in order:
        if item in candidates:
            return item
    fail("candidate set has no ordered member")


def validate_checks(checks: dict[str, str], order: list[str], na_fields: set[str]) -> None:
    if list(checks) != order:
        fail("check field order or coverage mismatch")
    for field, value in checks.items():
        if value not in (TRI_NA if field in na_fields else TRI):
            fail(f"invalid check value: {field}={value}")


def derive_host(case: dict[str, Any]) -> list[str]:
    observations = case.get("observations")
    if not isinstance(observations, list) or not observations:
        fail("host observations must be a non-empty list")
    if any(item not in HOST_ALLOWED for item in observations):
        fail("unknown host observation")
    candidates = set(observations)
    if "MATCH" in candidates and len(candidates) != 1:
        candidates.discard("MATCH")
        candidates.add("INTEGRITY_FAILURE")
    rejected = candidates & set(HOST_REJECTED)
    if rejected:
        return ["REJECTED", first_present(HOST_REJECTED, rejected)]
    indeterminate = candidates & set(HOST_INDETERMINATE)
    if indeterminate:
        return ["INDETERMINATE", first_present(HOST_INDETERMINATE, indeterminate)]
    if candidates == {"MATCH"}:
        return ["AUTHENTICATED", "MATCH"]
    fail("host candidate set is not total")


def derive_permit(base: dict[str, str], base_lifecycle: str, case: dict[str, Any]) -> list[str]:
    overrides = case.get("overrides", {})
    if not isinstance(overrides, dict) or any(key not in PERMIT_CHECKS for key in overrides):
        fail("unknown permit override")
    checks = {field: overrides.get(field, base[field]) for field in PERMIT_CHECKS}
    validate_checks(checks, PERMIT_CHECKS, PERMIT_NA)
    lifecycle = case.get("lifecycle", base_lifecycle)
    if lifecycle not in {"ISSUED", "ACTIVE", "CONSUMED", "REVOKED", "EXPIRED", "SUPERSEDED", "INDETERMINATE"}:
        fail("invalid lifecycle")

    candidates: set[str] = set()
    if case.get("integrity_failure", False):
        candidates.add("INTEGRITY_FAILURE")
    lifecycle_reason = {
        "CONSUMED": "INVOCATIONS_EXHAUSTED",
        "REVOKED": "TERMINAL",
        "SUPERSEDED": "TERMINAL",
        "EXPIRED": "EXPIRED",
    }.get(lifecycle)
    if lifecycle_reason:
        candidates.add(lifecycle_reason)
    for field, value in checks.items():
        if value != "REJECTED":
            continue
        if field == "time_window_current":
            time_reason = case.get("time_reason")
            if time_reason in {"NOT_YET_VALID", "EXPIRED"}:
                candidates.add(time_reason)
            elif time_reason is None:
                candidates.add("INTEGRITY_FAILURE")
            else:
                fail("unknown time_reason")
        else:
            candidates.add(PERMIT_REASON_BY_CHECK[field])
    if candidates:
        return ["REJECTED", first_present(PERMIT_REJECTED, candidates)]
    if lifecycle == "INDETERMINATE" or any(value == "INDETERMINATE" for value in checks.values()):
        return ["INDETERMINATE", "UNAVAILABLE"]
    if lifecycle in {"ISSUED", "ACTIVE"}:
        return ["VALID", "ALL_CURRENT"]
    fail("permit candidate set is not total")


def derive_admission(base: dict[str, str], case: dict[str, Any]) -> list[str]:
    overrides = case.get("overrides", {})
    if not isinstance(overrides, dict) or any(key not in ADMISSION_CHECKS for key in overrides):
        fail("unknown admission override")
    checks = {field: overrides.get(field, base[field]) for field in ADMISSION_CHECKS}
    validate_checks(checks, ADMISSION_CHECKS, ADMISSION_NA)
    candidates: set[str] = set()
    if case.get("integrity_failure", False):
        candidates.add("INTEGRITY_FAILURE")
    for field, value in checks.items():
        if value == "REJECTED":
            candidates.add(ADMISSION_REASON_BY_CHECK[field])
    if candidates:
        return ["REJECTED", first_present(ADMISSION_REJECTED, candidates)]
    if any(value == "INDETERMINATE" for value in checks.values()):
        return ["INDETERMINATE", "CURRENTNESS_UNAVAILABLE"]
    return ["ADMITTED", "ALL_CHECKS_PASS"]


def validate_case(actual: list[str], case: dict[str, Any]) -> None:
    if actual != case.get("expected"):
        fail(f"case {case.get('id')} expected {case.get('expected')} but derived {actual}")


def validate_fixture(data: dict[str, Any]) -> dict[str, int]:
    if list(data) != ["interface_version", "contract_version", "host_authentication", "permit_currentness", "host_local_admission"]:
        fail("top-level field order mismatch")
    if data["interface_version"] != "agents-os.f4-r2-result-reason-totality-vectors.v0.1":
        fail("interface version mismatch")
    if data["contract_version"] != CONTRACT:
        fail("contract version mismatch")

    host_cases = data["host_authentication"]["cases"]
    for case in host_cases:
        validate_case(derive_host(case), case)

    permit = data["permit_currentness"]
    validate_checks(permit["base_checks"], PERMIT_CHECKS, PERMIT_NA)
    permit_cases = permit["cases"]
    for case in permit_cases:
        validate_case(derive_permit(permit["base_checks"], permit["base_lifecycle"], case), case)

    admission = data["host_local_admission"]
    validate_checks(admission["base_checks"], ADMISSION_CHECKS, ADMISSION_NA)
    admission_cases = admission["cases"]
    for case in admission_cases:
        validate_case(derive_admission(admission["base_checks"], case), case)

    return {
        "host_case_count": len(host_cases),
        "permit_case_count": len(permit_cases),
        "admission_case_count": len(admission_cases),
    }


def negative_self_tests(data: dict[str, Any]) -> int:
    mutations = []
    changed_host = copy.deepcopy(data)
    changed_host["host_authentication"]["cases"][0]["expected"] = ["INDETERMINATE", "VERIFIER_UNAVAILABLE"]
    mutations.append(changed_host)
    changed_permit = copy.deepcopy(data)
    changed_permit["permit_currentness"]["cases"][0]["expected"] = ["REJECTED", "POLICY_STALE"]
    mutations.append(changed_permit)
    changed_admission = copy.deepcopy(data)
    changed_admission["host_local_admission"]["cases"][0]["expected"] = ["INDETERMINATE", "CURRENTNESS_UNAVAILABLE"]
    mutations.append(changed_admission)
    rejected = 0
    for mutation in mutations:
        try:
            validate_fixture(mutation)
        except ValueError:
            rejected += 1
    if rejected != len(mutations):
        fail("negative mutation was not rejected")
    return rejected


def main() -> None:
    raw = FIXTURE.read_bytes()
    data = json.loads(raw)
    counts = validate_fixture(data)
    negative_count = negative_self_tests(data)
    canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    output = {
        "admission_case_count": counts["admission_case_count"],
        "contract_version": CONTRACT,
        "fixture_canonical_sha256": hashlib.sha256(canonical).hexdigest(),
        "fixture_file_sha256": hashlib.sha256(raw).hexdigest(),
        "host_case_count": counts["host_case_count"],
        "negative_mutations_rejected": negative_count,
        "permit_case_count": counts["permit_case_count"],
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "result": "PASS",
        "total_case_count": sum(counts.values()),
        "external_effect_count": 0,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
