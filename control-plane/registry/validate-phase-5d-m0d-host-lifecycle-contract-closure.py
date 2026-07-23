#!/usr/bin/env python3
"""Offline validator for the Phase 5D Host lifecycle contract-closure fixture.

This program accepts no Host path, worktree, archive, plugin, or runtime input.
It validates only fixed control-plane bytes and synthetic fixture data.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "control-plane/registry/drafts/2026-07-24-agents-os-phase-5d-m0d-host-lifecycle-contract-closure-v0.1-r1.md"
PROFILE_PATH = ROOT / "control-plane/registry/drafts/2026-07-24-agents-os-phase-5d-m0d-host-lifecycle-evidence-profile-v0.1-r1.yaml"
FIXTURE_PATH = ROOT / "control-plane/registry/examples/2026-07-24-agents-os-phase-5d-m0d-host-lifecycle-contract-closure-fixture-v0.1.json"

EXPECTED_CONTRACT_SHA256 = "fb31de51e4a65d9d582416eee5bce36715c11f0710c3222614c148498e951f29"
EXPECTED_PROFILE_SHA256 = "dd2fc55c16795e4344adcdf1f0267959604b62591475615fcac694b3cf8661bc"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

ROOT_FIELDS = {
    "schema_version",
    "contract_path",
    "contract_sha256",
    "profile_path",
    "profile_sha256",
    "cases",
}
CASE_FIELDS = {
    "case_id",
    "evidence_class",
    "owner_contract",
    "expected_result",
    "runtime_usable",
    "actual_host_smoke_execution_authorized",
    "expected_host_operation_count",
}
OWNER_FIELDS = {
    "owner_contract_ref",
    "owner_contract_revision",
    "owner_contract_sha256",
    "sections",
}
SECTION_NAMES = {"host_discovery", "initialize", "shutdown", "quarantine_cleanup"}
SECTION_FIELDS = {"section_ref", "section_revision", "section_sha256", "expected_outcome"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json_strict(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    if type(data) is not dict:
        raise ValueError("fixture root must be an object")
    return data


def is_ref(value: Any, *, synthetic: bool) -> bool:
    return (
        type(value) is str
        and bool(value)
        and unicodedata.normalize("NFC", value) == value
        and (value.startswith("synthetic:") if synthetic else True)
    )


def is_positive_safe_integer(value: Any) -> bool:
    return type(value) is int and 0 < value <= 9007199254740991


def error(errors: list[str], message: str) -> None:
    errors.append(message)


def exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        error(errors, f"{label}: expected object")
        return False
    if set(value) != expected:
        error(errors, f"{label}: closed field set mismatch")
        return False
    return True


def validate_owner(owner: Any, errors: list[str]) -> None:
    if not exact_keys(owner, OWNER_FIELDS, "owner_contract", errors):
        return
    if not is_ref(owner["owner_contract_ref"], synthetic=True):
        error(errors, "owner_contract.owner_contract_ref must be a synthetic NFC ref")
    if not is_positive_safe_integer(owner["owner_contract_revision"]):
        error(errors, "owner_contract.owner_contract_revision must be a positive safe integer")
    if type(owner["owner_contract_sha256"]) is not str or not SHA256_RE.fullmatch(owner["owner_contract_sha256"]):
        error(errors, "owner_contract.owner_contract_sha256 must be lowercase SHA-256")
    sections = owner["sections"]
    if type(sections) is not dict or set(sections) != SECTION_NAMES:
        error(errors, "owner_contract.sections must contain exactly the four closed section names")
        return
    expected_outcomes = {
        "host_discovery": "SYNTHETIC_HOST_DISCOVERY_ONLY",
        "initialize": "INITIALIZED_FALSE",
        "shutdown": "SHUTDOWN_TRUE",
        "quarantine_cleanup": "OWNED_ROOT_REMOVED",
    }
    for name in sorted(SECTION_NAMES):
        section = sections[name]
        if not exact_keys(section, SECTION_FIELDS, f"owner_contract.sections.{name}", errors):
            continue
        if not is_ref(section["section_ref"], synthetic=True):
            error(errors, f"owner_contract.sections.{name}.section_ref must be a synthetic NFC ref")
        if not is_positive_safe_integer(section["section_revision"]):
            error(errors, f"owner_contract.sections.{name}.section_revision must be a positive safe integer")
        if type(section["section_sha256"]) is not str or not SHA256_RE.fullmatch(section["section_sha256"]):
            error(errors, f"owner_contract.sections.{name}.section_sha256 must be lowercase SHA-256")
        if section["expected_outcome"] != expected_outcomes[name]:
            error(errors, f"owner_contract.sections.{name}.expected_outcome mismatch")


def validate_case(case: Any, errors: list[str]) -> None:
    if not exact_keys(case, CASE_FIELDS, "case", errors):
        return
    if type(case["case_id"]) is not str or not case["case_id"]:
        error(errors, "case_id must be a nonempty string")
    if type(case["runtime_usable"]) is not bool or case["runtime_usable"]:
        error(errors, "runtime_usable must be strict false")
    if type(case["actual_host_smoke_execution_authorized"]) is not bool or case["actual_host_smoke_execution_authorized"]:
        error(errors, "actual_host_smoke_execution_authorized must be strict false")
    if type(case["expected_host_operation_count"]) is not int or case["expected_host_operation_count"] != 0:
        error(errors, "expected_host_operation_count must be integer zero")
    evidence_class = case["evidence_class"]
    if evidence_class == "NONE":
        if case["owner_contract"] is not None:
            error(errors, "NONE requires owner_contract null")
        if case["expected_result"] != "BLOCKED_MISSING_HASH_BOUND_HOST_LIFECYCLE_CONTRACT":
            error(errors, "NONE requires the missing-owner-contract result")
    elif evidence_class == "SYNTHETIC_TEST_ONLY":
        if case["expected_result"] != "SYNTHETIC_CONTRACT_SHAPE_VALIDATED":
            error(errors, "synthetic evidence requires the synthetic-shape result")
        validate_owner(case["owner_contract"], errors)
    else:
        error(errors, "evidence_class is not allowed in the current closure")


def validate_fixture(data: Any) -> list[str]:
    errors: list[str] = []
    if not exact_keys(data, ROOT_FIELDS, "fixture", errors):
        return errors
    if data["schema_version"] != "agents-os.phase5d.m0d.host-lifecycle-contract-closure-fixture.v0.1-r1":
        error(errors, "fixture schema_version mismatch")
    if data["contract_path"] != str(CONTRACT_PATH.relative_to(ROOT)):
        error(errors, "fixture contract_path mismatch")
    if data["profile_path"] != str(PROFILE_PATH.relative_to(ROOT)):
        error(errors, "fixture profile_path mismatch")
    if data["contract_sha256"] != EXPECTED_CONTRACT_SHA256:
        error(errors, "fixture contract_sha256 mismatch")
    if data["profile_sha256"] != EXPECTED_PROFILE_SHA256:
        error(errors, "fixture profile_sha256 mismatch")
    if type(data["cases"]) is not list or len(data["cases"]) != 2:
        error(errors, "fixture cases must be an exact two-case list")
        return errors
    expected_ids = ["MISSING_OWNER_CONTRACT", "SYNTHETIC_SCHEMA_SHAPE_ONLY"]
    if [case.get("case_id") if type(case) is dict else None for case in data["cases"]] != expected_ids:
        error(errors, "fixture case inventory or order mismatch")
    for case in data["cases"]:
        validate_case(case, errors)
    return errors


def run_self_test(fixture: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    mutations: list[tuple[str, Any]] = []
    unknown = copy.deepcopy(fixture)
    unknown["unknown"] = True
    mutations.append(("unknown_root", unknown))
    runtime = copy.deepcopy(fixture)
    runtime["cases"][1]["runtime_usable"] = True
    mutations.append(("runtime_true", runtime))
    authorization = copy.deepcopy(fixture)
    authorization["cases"][1]["actual_host_smoke_execution_authorized"] = True
    mutations.append(("host_authorized", authorization))
    namespace = copy.deepcopy(fixture)
    namespace["cases"][1]["owner_contract"]["sections"]["initialize"]["section_ref"] = "host:initialize"
    mutations.append(("non_synthetic_ref", namespace))
    missing_section = copy.deepcopy(fixture)
    del missing_section["cases"][1]["owner_contract"]["sections"]["shutdown"]
    mutations.append(("missing_section", missing_section))
    for name, mutated in mutations:
        if not validate_fixture(mutated):
            failures.append(f"self-test mutation accepted: {name}")
    try:
        json.loads('{"a":1,"a":2}', object_pairs_hook=reject_duplicate_keys)
        failures.append("self-test duplicate key accepted")
    except ValueError:
        pass
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", default=str(FIXTURE_PATH))
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        fixture_path = Path(args.fixture).resolve(strict=True)
        if fixture_path != FIXTURE_PATH.resolve():
            raise ValueError("only the fixed Phase 5D synthetic fixture is accepted")
        contract_hash = sha256_file(CONTRACT_PATH)
        profile_hash = sha256_file(PROFILE_PATH)
        if contract_hash != EXPECTED_CONTRACT_SHA256:
            raise ValueError("fixed contract bytes do not match the immutable contract hash")
        if profile_hash != EXPECTED_PROFILE_SHA256:
            raise ValueError("fixed profile bytes do not match the immutable profile hash")
        fixture = read_json_strict(fixture_path)
        errors = validate_fixture(fixture)
        if args.self_test:
            errors.extend(run_self_test(fixture))
    except Exception as exc:
        errors = [f"BLOCKED: {exc}"]
    payload = {
        "result": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "profile_sha256": EXPECTED_PROFILE_SHA256,
        "runtime_usable": False,
        "actual_host_smoke_execution_authorized": False,
        "host_operation_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
