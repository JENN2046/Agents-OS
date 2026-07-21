#!/usr/bin/env python3
"""Validate the narrow Plan R5 strict JSON integer closure."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[2]
R4_VALIDATOR = ROOT / "control-plane/registry/validate-phase-5b-m0b-plan-r4-closure-witness.py"
R5_BUILDER = ROOT / "control-plane/registry/build-phase-5b-m0b-plan-r5-strict-integer-witness.py"
PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r5-strict-json-integer-profile-v0.1.yaml"
DOMAIN = "PHASE_5B_M0B_PLAN_R5_SYNTHETIC_NONAUTHORITY"
TARGET = "R5_PRINCIPAL_REVISION_JSON_INTEGER_INVALID"


def jcs(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else jcs(value)).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R4 = load_module(R4_VALIDATOR, "phase5b_r4_validator_for_r5")
R5 = load_module(R5_BUILDER, "phase5b_r5_builder")


def strict_json(path: Path) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in rows:
            if key in out:
                raise ValueError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
    )
    if not isinstance(value, dict):
        raise ValueError("fixture root must be object")
    return value


def load_profile() -> dict[str, Any]:
    value = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("R5 profile must be an object")
    return value


def exact_fields(value: Any, fields: list[str]) -> bool:
    return isinstance(value, dict) and set(value) == set(fields)


def add(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def strict_integer_one(value: Any) -> bool:
    return type(value) is int and value == 1


def observed_values(fixture: dict[str, Any]) -> tuple[Any, Any]:
    r4 = fixture["R4_fixture"]
    return (
        r4["derived_sealed_binding"]["claimed_principal_revision"],
        r4["R3_fixture"]["F3"]["command"]["claimed_principal_revision"],
    )


def expected_observations(fixture: dict[str, Any]) -> list[dict[str, Any]]:
    derived, consumed = observed_values(fixture)
    return [
        R5.observation("R4_fixture.derived_sealed_binding.claimed_principal_revision", derived),
        R5.observation("R4_fixture.R3_fixture.F3.command.claimed_principal_revision", consumed),
    ]


def validate_semantics(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    fields = [
        "schema_version",
        "domain",
        "profile_fingerprint",
        "R4_fixture",
        "strict_integer_observations",
        "fixed_regressions",
        "boundary",
        "root_fingerprint",
    ]
    add(errors, exact_fields(fixture, fields), "R5_ROOT_SCHEMA_INVALID")
    if not exact_fields(fixture, fields):
        return sorted(set(errors))
    add(
        errors,
        fixture["schema_version"] == "agents-os.m0b-r5-strict-integer-witness.v0.1"
        and fixture["domain"] == DOMAIN,
        "R5_ROOT_DOMAIN_INVALID",
    )
    add(errors, fixture["profile_fingerprint"] == digest(PROFILE.read_bytes()), "R5_PROFILE_FINGERPRINT_INVALID")
    r4 = fixture["R4_fixture"]
    errors.extend(f"R4::{code}" for code in R4.validate_semantics(r4))
    try:
        derived, consumed = observed_values(fixture)
    except (KeyError, TypeError, IndexError):
        errors.append(TARGET)
    else:
        add(errors, strict_integer_one(derived) and strict_integer_one(consumed), TARGET)
        add(errors, fixture["strict_integer_observations"] == expected_observations(fixture), "R5_OBSERVATION_BINDING_INVALID")
    profile = load_profile()
    expected_cases = profile["fixed_regressions"]
    add(errors, fixture["fixed_regressions"] == expected_cases and len(expected_cases) == len(set(expected_cases)) == 4, "R5_REGRESSION_INVENTORY_INVALID")
    expected_boundary = {
        "plan_only": True,
        "runtime_usable": False,
        "implementation_authorized": False,
        "database_created": False,
        "real_occurrence_count": 0,
        "terminal_outcome": "NOT_ACTIVATED",
    }
    add(errors, fixture["boundary"] == expected_boundary, "R5_BOUNDARY_EXPANSION")
    unsigned = {key: value for key, value in fixture.items() if key != "root_fingerprint"}
    add(errors, fixture["root_fingerprint"] == digest(["agents-os.m0b.r5.strict-integer-root.v0.1", unsigned]), "R5_ROOT_FINGERPRINT_INVALID")
    return sorted(set(errors))


def validate_fixed_fixture(fixture: dict[str, Any]) -> list[str]:
    return [] if fixture == R5.build_fixture() else ["R5_FIXED_FIXTURE_SEAL_MISMATCH"]


def resign(fixture: dict[str, Any]) -> None:
    R4.resign(fixture["R4_fixture"])
    fixture["strict_integer_observations"] = expected_observations(fixture)
    unsigned = {key: value for key, value in fixture.items() if key != "root_fingerprint"}
    fixture["root_fingerprint"] = digest(["agents-os.m0b.r5.strict-integer-root.v0.1", unsigned])


def fixed_cases() -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    def inner(value: Any) -> Callable[[dict[str, Any]], None]:
        return lambda f: f["R4_fixture"]["R3_fixture"]["F3"]["command"].update(claimed_principal_revision=value)

    def coordinated(value: Any) -> Callable[[dict[str, Any]], None]:
        def mutate(fixture: dict[str, Any]) -> None:
            fixture["R4_fixture"]["derived_sealed_binding"]["claimed_principal_revision"] = value
            fixture["R4_fixture"]["R3_fixture"]["F3"]["command"]["claimed_principal_revision"] = value
        return mutate

    return [
        ("inner_revision_integer_1_to_boolean_true", inner(True)),
        ("inner_revision_integer_1_to_float_1_0", inner(1.0)),
        ("derived_and_inner_revision_to_boolean_true", coordinated(True)),
        ("derived_and_inner_revision_to_float_1_0", coordinated(1.0)),
    ]


def totality_values() -> list[tuple[str, Any]]:
    return [
        ("boolean_true", True),
        ("boolean_false", False),
        ("float_one", 1.0),
        ("float_zero", 0.0),
        ("null", None),
        ("string", "1"),
        ("array", [1]),
        ("object", {"value": 1}),
        ("zero", 0),
        ("negative", -1),
        ("other_integer", 2),
    ]


def run_cases(base: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for case_id, mutate in fixed_cases():
        fixture = copy.deepcopy(base)
        mutate(fixture)
        resign(fixture)
        semantic = validate_semantics(fixture)
        seal = validate_fixed_fixture(fixture)
        passed = TARGET in semantic and seal == ["R5_FIXED_FIXTURE_SEAL_MISMATCH"]
        rows.append({
            "case_id": case_id,
            "semantic_errors": semantic,
            "fixed_seal_errors": seal,
            "target_semantic_rejection": passed,
            "seal_only": not semantic,
        })
        if not passed:
            failures.append(case_id)
    return rows, failures


def run_totality(base: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for case_id, value in totality_values():
        fixture = copy.deepcopy(base)
        fixture["R4_fixture"]["R3_fixture"]["F3"]["command"]["claimed_principal_revision"] = value
        resign(fixture)
        semantic = validate_semantics(fixture)
        passed = TARGET in semantic
        rows.append({"case_id": case_id, "target_semantic_rejection": passed, "semantic_errors": semantic})
        if not passed:
            failures.append(case_id)
    return rows, failures


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} FIXTURE.json", file=sys.stderr)
        return 2
    try:
        fixture = strict_json(Path(sys.argv[1]))
        semantic = validate_semantics(fixture)
        seal = validate_fixed_fixture(fixture)
        fixed_rows, fixed_failures = run_cases(fixture)
        totality_rows, totality_failures = run_totality(fixture)
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 1
    result = {
        "result": "PASS" if not semantic and not seal and not fixed_failures and not totality_failures else "BLOCK",
        "semantic_errors": semantic,
        "fixed_fixture_errors": seal,
        "fixed_regressions": {
            "executed": len(fixed_rows),
            "target_semantic_rejected": sum(row["target_semantic_rejection"] for row in fixed_rows),
            "seal_only_rejections": sum(row["seal_only"] for row in fixed_rows),
            "failures": fixed_failures,
        },
        "totality_matrix": {
            "executed": len(totality_rows),
            "target_semantic_rejected": sum(row["target_semantic_rejection"] for row in totality_rows),
            "failures": totality_failures,
        },
        "positive_control": "STRICT_INTEGER_1_ACCEPTED" if not semantic else "FAILED",
        "terminal_outcome": fixture.get("boundary", {}).get("terminal_outcome"),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
