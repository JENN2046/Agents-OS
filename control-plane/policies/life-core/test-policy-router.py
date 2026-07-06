#!/usr/bin/env python3
"""Fixture tests for the local life-core policy router."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent


def load_router() -> Any:
    module_path = ROOT / "policy-router.py"
    spec = importlib.util.spec_from_file_location("policy_router", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load router from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_fixtures() -> dict[str, Any]:
    with (ROOT / "policy-router.fixtures.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def matched_rule_ids(result: dict[str, Any]) -> set[str]:
    return {str(rule.get("id")) for rule in result.get("matched_rules", [])}


def result_values(result: dict[str, Any], key: str) -> set[str]:
    return {str(value) for value in result.get(key, [])}


def validate_case(router: Any, case: dict[str, Any]) -> list[str]:
    result = router.route_action(case["action"], ROOT)
    failures: list[str] = []

    if result["decision"] != case["expected_decision"]:
        failures.append(
            f"decision expected {case['expected_decision']} got {result['decision']}"
        )

    if result["permission_level"] != case["expected_permission_level"]:
        failures.append(
            "permission expected "
            f"{case['expected_permission_level']} got {result['permission_level']}"
        )

    matched = matched_rule_ids(result)
    for rule_id in case.get("must_match_rules", []):
        if rule_id not in matched:
            failures.append(f"missing matched rule {rule_id}")

    for rule_id in case.get("must_not_match_rules", []):
        if rule_id in matched:
            failures.append(f"unexpected matched rule {rule_id}")

    evidence = result_values(result, "required_evidence")
    for item in case.get("must_include_evidence", []):
        if item not in evidence:
            failures.append(f"missing evidence {item}")

    for item in case.get("must_not_include_evidence", []):
        if item in evidence:
            failures.append(f"unexpected evidence {item}")

    denied_boundaries = result_values(result, "denied_boundaries")
    for item in case.get("must_include_denied_boundaries", []):
        if item not in denied_boundaries:
            failures.append(f"missing denied boundary {item}")

    for item in case.get("must_not_include_denied_boundaries", []):
        if item in denied_boundaries:
            failures.append(f"unexpected denied boundary {item}")

    for module in result.get("required_modules", []):
        if not (ROOT / module).exists():
            failures.append(f"missing required module file {module}")

    return failures


def main() -> int:
    router = load_router()
    fixtures = load_fixtures()
    failures: list[str] = []

    for case in fixtures["cases"]:
        case_failures = validate_case(router, case)
        if case_failures:
            failures.append(f"{case['id']}: {'; '.join(case_failures)}")
            print(f"FAIL {case['id']}")
            for failure in case_failures:
                print(f"  - {failure}")
        else:
            print(f"PASS {case['id']}")

    print(f"cases={len(fixtures['cases'])} failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
