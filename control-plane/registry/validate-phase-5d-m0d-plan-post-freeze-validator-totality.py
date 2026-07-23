#!/usr/bin/env python3
"""Guard the immutable Phase 5D R2 validator against malformed boundaries.

This successor preserves the frozen validator and Plan bytes.  It performs a
closed-shape Plan-header preflight before delegation, so malformed
``current_boundary`` input becomes a deterministic offline BLOCK rather than
an uncaught exception.  It does not load a Host, plugin, addon, runtime,
database, provider, Memory, sensing, or effect boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
FROZEN_VALIDATOR = {
    "path": "control-plane/registry/validate-phase-5d-m0d-plan-r2-witness.py",
    "sha256": "d2767d569eabc795433530f2490672ce71089d85a49da10454294ff47834ac3f",
}
DEFAULT_PLAN = ROOT / "control-plane/registry/drafts/2026-07-23-agents-os-phase-5d-m0d-quarantined-host-smoke-integration-plan-v0.1-r2-amendment.md"
DEFAULT_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-23-agents-os-phase-5d-m0d-quarantined-host-smoke-immutable-binding-profile-v0.1-r2.yaml"
DEFAULT_FIXTURE = ROOT / "control-plane/registry/examples/2026-07-23-agents-os-phase-5d-m0d-plan-r2-synthetic-witness-v0.1.json"
DEFAULT_CORRECTION_FIXTURE = ROOT / "control-plane/registry/examples/2026-07-24-agents-os-phase-5d-m0d-plan-post-freeze-validator-totality-correction-fixture-v0.1.json"


class DuplicateKeyError(ValueError):
    """Raised when the correction fixture repeats a JSON object key."""


def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_keys(value: object, expected: set[str], label: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{label}: expected object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(f"{label}: fields mismatch missing={sorted(expected - actual)} extra={sorted(actual - expected)}")
        return False
    return True


def load_historical_validator() -> ModuleType:
    path = ROOT / FROZEN_VALIDATOR["path"]
    if path.is_symlink() or not path.is_file():
        raise ValueError("historical validator unavailable")
    if sha256_bytes(path.read_bytes()) != FROZEN_VALIDATOR["sha256"]:
        raise ValueError("historical validator SHA-256 mismatch")
    spec = importlib.util.spec_from_file_location("_phase5d_m0d_frozen_r2_validator", path)
    if spec is None or spec.loader is None:
        raise ValueError("historical validator cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def block(errors: list[str], delegated: bool = False) -> dict[str, object]:
    return {
        "delegated_historical_validator": delegated,
        "errors": errors,
        "result": "BLOCK",
        "terminal_outcome": "NOT_EXECUTED",
    }


def preflight_current_boundary(plan_path: Path, historical: ModuleType) -> list[str]:
    """Return deterministic shape errors without invoking the frozen reducer."""

    try:
        text = plan_path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return ["plan.header: unreadable or non-UTF-8"]
    match = historical.PLAN_HEADER.match(text)
    if match is None:
        return ["plan.header: missing or malformed"]
    try:
        header = historical.strict_yaml_text(match.group(1))
    except historical.DuplicateKeyError:
        return ["plan.header: duplicate YAML key"]
    except yaml.YAMLError:
        return ["plan.header: YAML parse failure"]
    except Exception:
        return ["plan.header: parse failure"]
    if type(header) is not dict:
        return ["plan.header: expected object"]
    boundary = header.get("current_boundary")
    expected = set(historical.EXPECTED_PLAN_HEADER["current_boundary"])
    if type(boundary) is not dict:
        return ["plan.current_boundary: expected object"]
    actual = set(boundary)
    if actual != expected:
        return [
            "plan.current_boundary: fields mismatch "
            f"missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        ]
    return []


def run(
    fixture_path: Path = DEFAULT_FIXTURE,
    plan_path: Path = DEFAULT_PLAN,
    profile_path: Path = DEFAULT_PROFILE,
) -> dict[str, object]:
    try:
        historical = load_historical_validator()
    except Exception as exc:
        return block([f"historical validator unavailable: {type(exc).__name__}"])
    preflight_errors = preflight_current_boundary(plan_path, historical)
    if preflight_errors:
        return block(preflight_errors)
    try:
        errors, historical_result = historical.run_fixture(fixture_path, plan_path, profile_path)
    except Exception as exc:
        return block([f"historical validator execution failure: {type(exc).__name__}"], delegated=True)
    if type(errors) is not list:
        return block(["historical validator returned malformed errors"], delegated=True)
    if errors or historical_result != "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY":
        return block([str(error) for error in errors] or ["historical validator returned non-favorable result"], delegated=True)
    return {
        "delegated_historical_validator": True,
        "errors": [],
        "historical_result": historical_result,
        "result": "PASS",
        "terminal_outcome": "NOT_EXECUTED",
    }


def read_fixture(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_pairs)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError):
        return None, ["correction fixture: parse failure"]
    errors: list[str] = []
    if not exact_keys(
        value,
        {"environment", "frozen_artifacts", "negative_cases", "positive_control", "schema_version", "terminal_outcome"},
        "correction fixture",
        errors,
    ):
        return None, errors
    assert isinstance(value, dict)
    if value["schema_version"] != "agents-os.phase5d.m0d.post-freeze-validator-totality-correction-fixture.v0.1":
        errors.append("correction fixture: schema version mismatch")
    if value["environment"] != "SYNTHETIC_TEST" or value["terminal_outcome"] != "NOT_EXECUTED":
        errors.append("correction fixture: boundary literal mismatch")
    artifacts = value["frozen_artifacts"]
    if not exact_keys(artifacts, {"fixture", "plan", "profile", "validator"}, "correction fixture.frozen_artifacts", errors):
        return None, errors
    assert isinstance(artifacts, dict)
    expected_artifacts = {
        "validator": FROZEN_VALIDATOR,
        "plan": {"path": DEFAULT_PLAN.relative_to(ROOT).as_posix(), "sha256": "e3b70cc2638bca9624d2593e3105b69aeb1b033226941032f46c9bf61d1d3e0b"},
        "profile": {"path": DEFAULT_PROFILE.relative_to(ROOT).as_posix(), "sha256": "3dfadf64e8e717d195ed64361bcf4f9af6d770eb835455e92d017510468b9349"},
        "fixture": {"path": DEFAULT_FIXTURE.relative_to(ROOT).as_posix(), "sha256": "37160f3b298aea5438f57c7f332d7cea1653ffbe245e183d1b292af7b2220ed0"},
    }
    if artifacts != expected_artifacts:
        errors.append("correction fixture: frozen artifact inventory mismatch")
    expected_cases = [
        {"id": "UNKNOWN_BOUNDARY_KEY", "mutation": "add_unknown_key", "expected_error_prefix": "plan.current_boundary: fields mismatch"},
        {"id": "MISSING_BOUNDARY_KEY", "mutation": "remove_required_key", "expected_error_prefix": "plan.current_boundary: fields mismatch"},
        {"id": "MISSING_BOUNDARY_MAPPING", "mutation": "remove_boundary_mapping", "expected_error_prefix": "plan.current_boundary: expected object"},
        {"id": "NON_MAPPING_BOUNDARY", "mutation": "replace_boundary_with_empty_list", "expected_error_prefix": "plan.current_boundary: expected object"},
        {"id": "DUPLICATE_BOUNDARY_KEY", "mutation": "duplicate_existing_key", "expected_error_prefix": "plan.header: duplicate YAML key"},
    ]
    if value["negative_cases"] != expected_cases:
        errors.append("correction fixture: negative case inventory mismatch")
    if value["positive_control"] != {
        "expected_historical_result": "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY",
        "expected_result": "PASS",
    }:
        errors.append("correction fixture: positive control mismatch")
    return value, errors


def rewrite_header(plan_text: str, historical: ModuleType, mutate: Any) -> str:
    match = historical.PLAN_HEADER.match(plan_text)
    if match is None:
        raise ValueError("frozen plan header unavailable")
    header = historical.strict_yaml_text(match.group(1))
    if type(header) is not dict:
        raise ValueError("frozen plan header malformed")
    mutate(header)
    rendered = yaml.safe_dump(header, allow_unicode=False, sort_keys=False).rstrip("\n")
    return f"{plan_text[:match.start(1)]}{rendered}{plan_text[match.end(1):]}"


def mutate_plan(plan_text: str, mutation: str, historical: ModuleType) -> str:
    if mutation == "add_unknown_key":
        return rewrite_header(
            plan_text,
            historical,
            lambda value: value["current_boundary"].__setitem__("unexpected_current_boundary_key", "forbidden"),
        )
    if mutation == "remove_required_key":
        return rewrite_header(
            plan_text,
            historical,
            lambda value: value["current_boundary"].pop("runtime_usable"),
        )
    if mutation == "remove_boundary_mapping":
        return rewrite_header(plan_text, historical, lambda value: value.pop("current_boundary"))
    if mutation == "replace_boundary_with_empty_list":
        return rewrite_header(plan_text, historical, lambda value: value.__setitem__("current_boundary", []))
    if mutation == "duplicate_existing_key":
        marker = "  current_plan_authoring_only: true\n"
        if marker not in plan_text:
            raise ValueError("frozen current-boundary marker unavailable")
        return plan_text.replace(marker, marker + marker, 1)
    raise ValueError(f"unknown fixture mutation: {mutation}")


def self_test(correction_fixture: Path = DEFAULT_CORRECTION_FIXTURE) -> dict[str, object]:
    fixture, errors = read_fixture(correction_fixture)
    if fixture is None or errors:
        return block(errors or ["correction fixture unavailable"])
    try:
        historical = load_historical_validator()
    except Exception as exc:
        return block([f"historical validator unavailable: {type(exc).__name__}"])

    for artifact in fixture["frozen_artifacts"].values():
        assert isinstance(artifact, dict)
        path = ROOT / artifact["path"]
        if path.is_symlink() or not path.is_file() or sha256_bytes(path.read_bytes()) != artifact["sha256"]:
            errors.append(f"frozen artifact digest mismatch: {artifact['path']}")

    positive = run()
    if positive.get("result") != "PASS" or positive.get("delegated_historical_validator") is not True:
        errors.append("positive control did not delegate to the historical validator")
    if positive.get("historical_result") != fixture["positive_control"]["expected_historical_result"]:
        errors.append("positive control historical result mismatch")

    negative_results: dict[str, str] = {}
    plan_text = DEFAULT_PLAN.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="agents-os-phase5d-validator-totality-") as directory:
        temporary_plan = Path(directory) / "mutated-plan.md"
        for case in fixture["negative_cases"]:
            assert isinstance(case, dict)
            try:
                temporary_plan.write_text(mutate_plan(plan_text, case["mutation"], historical), encoding="utf-8")
                result = run(DEFAULT_FIXTURE, temporary_plan, DEFAULT_PROFILE)
            except Exception as exc:
                errors.append(f"negative case uncaught exception: {case['id']}:{type(exc).__name__}")
                negative_results[case["id"]] = "UNCAUGHT_EXCEPTION"
                continue
            case_errors = result.get("errors")
            if (
                result.get("result") != "BLOCK"
                or result.get("delegated_historical_validator") is not False
                or result.get("terminal_outcome") != "NOT_EXECUTED"
                or type(case_errors) is not list
                or not case_errors
                or not str(case_errors[0]).startswith(case["expected_error_prefix"])
            ):
                errors.append(f"negative case did not fail closed: {case['id']}")
                negative_results[case["id"]] = "UNEXPECTED_RESULT"
            else:
                negative_results[case["id"]] = "BLOCK_BEFORE_DELEGATION"

    if errors:
        return block(errors)
    return {
        "frozen_validator_sha256": FROZEN_VALIDATOR["sha256"],
        "negative_cases": negative_results,
        "result": "PASS",
        "terminal_outcome": "NOT_EXECUTED",
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "fixture_path",
        nargs="?",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="R2 synthetic witness to validate (default: frozen R2 fixture)",
    )
    parser.add_argument(
        "--plan",
        type=Path,
        default=DEFAULT_PLAN,
        help="Plan header to preflight before historical validation",
    )
    parser.add_argument(
        "--profile",
        type=Path,
        default=DEFAULT_PROFILE,
        help="Immutable R2 profile supplied to the historical validator",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--correction-fixture",
        type=Path,
        default=DEFAULT_CORRECTION_FIXTURE,
        help="Synthetic fixture used only by --self-test",
    )
    args = parser.parse_args(argv)
    result = (
        self_test(args.correction_fixture)
        if args.self_test
        else run(args.fixture_path, args.plan, args.profile)
    )
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0 if result.get("result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
