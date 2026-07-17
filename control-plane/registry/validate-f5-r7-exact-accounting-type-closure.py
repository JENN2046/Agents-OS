#!/usr/bin/env python3
"""Validate the fixed nonauthority F5 R7 exact accounting type proof."""

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
    "2026-07-17-agents-os-f5-r7-exact-accounting-type-closure-v0.1.json"
)
SOURCE_R6 = Path(
    "control-plane/registry/examples/"
    "2026-07-17-agents-os-f5-r6-first-apply-eligibility-guard-v0.1.json"
)
SOURCE_R6_SHA256 = "853dda58e07fa88c460b4da7f177d70a4cf3efc62484a0a4c435e464f80889e8"
SOURCE_R6_CANONICAL_SHA256 = "5447834426db9fbd49d1261f48bba788e3a546f585f289fe3966e720bb9da2b2"
FIXTURE_INTERFACE = "agents-os.f5-r7-exact-accounting-type-closure-fixture.v0.1"
SAFE_INTEGER = 9007199254740991
SHA_RE = re.compile(r"[0-9a-f]{64}")
DERIVED_COUNT_FIELDS = (
    "modeled_event_delta",
    "modeled_call_authorization_delta",
    "total_event_count",
    "total_call_authorization_count",
)
STORED_COUNT_FIELDS = ("committed_event_count", "committed_call_authorization_count")
ASSERTION_COUNT_FIELDS = (
    "accepted_real_handoff_count",
    "claim_event_count",
    "armed_dispatch_count",
    "runtime_consumable_count",
    "external_effect_count",
    "provider_call_count",
    "raw_secret_count",
)
SOURCE_SUMMARY_COUNT_FIELDS = (
    "arm_guard_case_count",
    "first_apply_case_count",
    "adversarial_case_count",
    "real_effect_count",
)
R7_SUMMARY_COUNT_FIELDS = (
    "count_occurrence_total",
    "zero_or_one_occurrence_total",
    "individual_boolean_mutation_total",
    "real_effect_count",
)
SECTIONS = (
    "source_binding",
    "exact_integer_profile",
    "count_inventory",
    "adversarial_profile",
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
ROW_FIELDS = {
    "ordinal",
    "json_pointer",
    "section",
    "field_class",
    "integer_value",
    "expected_json_type",
}


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
            ensure(type(key) is str, f"non-string key at {path}")
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


def render(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_count(value: Any, path: str) -> None:
    ensure(type(value) is int, f"exact JSON integer required at {path}")
    ensure(0 <= value <= SAFE_INTEGER, f"non-negative safe integer required at {path}")


def sha(value: Any, path: str) -> None:
    ensure(type(value) is str and SHA_RE.fullmatch(value) is not None, f"sha required at {path}")


def stable_string(value: Any, path: str) -> None:
    ensure(type(value) is str and bool(value) and value == value.strip(), f"stable string required at {path}")


def pointer_get(root: Any, pointer: str) -> Any:
    node = root
    for token in pointer.lstrip("/").split("/"):
        node = node[int(token)] if isinstance(node, list) else node[token]
    return node


def pointer_set(root: Any, pointer: str, value: Any) -> None:
    tokens = pointer.lstrip("/").split("/")
    node = root
    for token in tokens[:-1]:
        node = node[int(token)] if isinstance(node, list) else node[token]
    final = tokens[-1]
    if isinstance(node, list):
        node[int(final)] = value
    else:
        node[final] = value


def derive_source_inventory(source: dict[str, Any]) -> list[dict[str, Any]]:
    ensure(isinstance(source.get("arm_guard_cases"), list) and len(source["arm_guard_cases"]) == 5, "source cases invalid")
    rows: list[dict[str, Any]] = []

    def add(pointer: str, section: str, field_class: str) -> None:
        value = pointer_get(source, pointer)
        exact_count(value, pointer)
        rows.append(
            {
                "ordinal": len(rows) + 1,
                "json_pointer": pointer,
                "section": section,
                "field_class": field_class,
                "integer_value": value,
                "expected_json_type": "INTEGER_NOT_BOOLEAN",
            }
        )

    for index, case in enumerate(source["arm_guard_cases"]):
        ensure(isinstance(case, dict), f"source case invalid at {index}")
        for field in DERIVED_COUNT_FIELDS:
            add(f"/arm_guard_cases/{index}/derived/{field}", "arm_guard_cases", "DERIVED_ACCOUNTING")
        stored = case["raw_input"]["stored_arm_state"]
        if stored is not None:
            for field in STORED_COUNT_FIELDS:
                add(
                    f"/arm_guard_cases/{index}/raw_input/stored_arm_state/{field}",
                    "arm_guard_cases",
                    "STORED_FIRST_ACCOUNTING",
                )
    for field in ASSERTION_COUNT_FIELDS:
        add(f"/assertions/{field}", "assertions", "NONAUTHORITY_ASSERTION_COUNT")
    for field in SOURCE_SUMMARY_COUNT_FIELDS:
        add(f"/summary/{field}", "summary", "PROOF_SUMMARY_COUNT")
    ensure(len(rows) == 37, "source count occurrence total invalid")
    ensure(sum(row["integer_value"] in (0, 1) for row in rows) == 34, "source zero-or-one total invalid")
    return rows


def validate_source_surface(source: Any) -> list[dict[str, Any]]:
    ensure(isinstance(source, dict), "source root invalid")
    validate_json(source)
    inventory = derive_source_inventory(source)
    ensure(source["environment"] == "SYNTHETIC_TEST", "source environment invalid")
    for field in ("authority_eligible", "runtime_consumable", "recovery_importable"):
        ensure(type(source[field]) is bool and source[field] is False, f"source boundary flag invalid {field}")
    for section in ("arm_guard_profile", "arm_guard_cases", "adversarial_cases", "assertions", "summary"):
        sha(source[section + "_fingerprint"], section + " fingerprint")
        ensure(source[section + "_fingerprint"] == digest(source[section]), f"source section fingerprint mismatch {section}")
    ensure(
        source["fixture_canonical_sha256"]
        == digest({key: value for key, value in source.items() if key != "fixture_canonical_sha256"}),
        "source root fingerprint mismatch",
    )
    return inventory


def load_source() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ensure(file_sha256(SOURCE_R6) == SOURCE_R6_SHA256, "R6 source file hash mismatch")
    source = parse_strict(SOURCE_R6.read_text(encoding="utf-8"))
    inventory = validate_source_surface(source)
    ensure(source["fixture_canonical_sha256"] == SOURCE_R6_CANONICAL_SHA256, "R6 source canonical mismatch")
    return source, inventory


def validate_fixture(fixture: Any, *, run_mutations: bool = True) -> dict[str, Any]:
    ensure(isinstance(fixture, dict) and set(fixture) == ROOT_FIELDS, "root inventory invalid")
    validate_json(fixture)
    ensure(fixture["fixture_interface"] == FIXTURE_INTERFACE, "fixture interface invalid")
    ensure(fixture["environment"] == "SYNTHETIC_TEST", "environment invalid")
    for field in ("authority_eligible", "runtime_consumable", "recovery_importable"):
        ensure(type(fixture[field]) is bool and fixture[field] is False, f"boundary flag invalid {field}")

    source, expected_inventory = load_source()
    ensure(
        fixture["source_binding"]
        == {
            "path": str(SOURCE_R6),
            "file_sha256": SOURCE_R6_SHA256,
            "fixture_canonical_sha256": SOURCE_R6_CANONICAL_SHA256,
            "fixture_interface": source["fixture_interface"],
        },
        "source binding mismatch",
    )

    profile = fixture["exact_integer_profile"]
    ensure(isinstance(profile, dict) and set(profile) == {
        "json_scalar_type",
        "boolean_is_integer",
        "float_is_integer",
        "minimum",
        "maximum",
        "validation_order",
        "closed_count_occurrence_total",
        "zero_or_one_occurrence_total",
    }, "integer profile inventory invalid")
    ensure(profile["json_scalar_type"] == "INTEGER", "integer scalar profile invalid")
    ensure(type(profile["boolean_is_integer"]) is bool and profile["boolean_is_integer"] is False, "boolean profile invalid")
    ensure(type(profile["float_is_integer"]) is bool and profile["float_is_integer"] is False, "float profile invalid")
    for field in ("minimum", "maximum", "closed_count_occurrence_total", "zero_or_one_occurrence_total"):
        exact_count(profile[field], "exact_integer_profile." + field)
    ensure(profile["minimum"] == 0 and profile["maximum"] == SAFE_INTEGER, "integer range invalid")
    ensure(profile["closed_count_occurrence_total"] == 37, "profile occurrence total invalid")
    ensure(profile["zero_or_one_occurrence_total"] == 34, "profile zero-or-one total invalid")
    ensure(profile["validation_order"] == "TYPE_BEFORE_EQUALITY_MAPPING_OR_DIGEST_TRUST", "validation order invalid")

    inventory = fixture["count_inventory"]
    ensure(isinstance(inventory, list) and len(inventory) == 37, "count inventory length invalid")
    for index, row in enumerate(inventory):
        ensure(isinstance(row, dict) and set(row) == ROW_FIELDS, f"count row inventory invalid {index}")
        exact_count(row["ordinal"], f"count_inventory[{index}].ordinal")
        ensure(row["ordinal"] == index + 1, f"count row ordinal invalid {index}")
        exact_count(row["integer_value"], f"count_inventory[{index}].integer_value")
        stable_string(row["json_pointer"], f"count_inventory[{index}].json_pointer")
        ensure(row["section"] in {"arm_guard_cases", "assertions", "summary"}, f"row section invalid {index}")
        ensure(row["field_class"] in {
            "DERIVED_ACCOUNTING",
            "STORED_FIRST_ACCOUNTING",
            "NONAUTHORITY_ASSERTION_COUNT",
            "PROOF_SUMMARY_COUNT",
        }, f"row class invalid {index}")
        ensure(row["expected_json_type"] == "INTEGER_NOT_BOOLEAN", f"row type marker invalid {index}")
    ensure(inventory == expected_inventory, "count inventory derivation mismatch")

    adversarial = fixture["adversarial_profile"]
    ensure(isinstance(adversarial, dict) and set(adversarial) == {
        "individual_fully_resigned_boolean_substitution_count",
        "prior_independent_accepted_zero_or_one_substitution_count",
        "required_individual_result",
        "multi_field_R6_counterexample",
    }, "adversarial profile inventory invalid")
    for field in (
        "individual_fully_resigned_boolean_substitution_count",
        "prior_independent_accepted_zero_or_one_substitution_count",
    ):
        exact_count(adversarial[field], "adversarial_profile." + field)
    ensure(adversarial["individual_fully_resigned_boolean_substitution_count"] == 37, "mutation count invalid")
    ensure(adversarial["prior_independent_accepted_zero_or_one_substitution_count"] == 34, "prior mutation count invalid")
    ensure(adversarial["required_individual_result"] == "REJECT_WRONG_SCALAR_TYPE", "required result invalid")
    validate_counterexample_profile(adversarial["multi_field_R6_counterexample"], source)

    assertions = fixture["assertions"]
    ensure(isinstance(assertions, dict) and set(assertions) == {
        "synthetic_nonauthority",
        "R6_first_apply_semantics_changed",
        "R5_receipt_or_arm_semantics_changed",
        *ASSERTION_COUNT_FIELDS,
        "terminal_outcome",
    }, "assertion inventory invalid")
    for field in ("synthetic_nonauthority", "R6_first_apply_semantics_changed", "R5_receipt_or_arm_semantics_changed"):
        ensure(type(assertions[field]) is bool, f"assertion boolean invalid {field}")
    ensure(assertions["synthetic_nonauthority"] is True, "synthetic assertion invalid")
    ensure(assertions["R6_first_apply_semantics_changed"] is False, "R6 semantic-change assertion invalid")
    ensure(assertions["R5_receipt_or_arm_semantics_changed"] is False, "R5 semantic-change assertion invalid")
    for field in ASSERTION_COUNT_FIELDS:
        exact_count(assertions[field], "assertions." + field)
        ensure(assertions[field] == 0, f"nonzero assertion count {field}")
    ensure(assertions["terminal_outcome"] == "NOT_EXECUTED", "terminal outcome invalid")

    summary = fixture["summary"]
    ensure(isinstance(summary, dict) and set(summary) == set(R7_SUMMARY_COUNT_FIELDS), "summary inventory invalid")
    for field in R7_SUMMARY_COUNT_FIELDS:
        exact_count(summary[field], "summary." + field)
    ensure(summary == {
        "count_occurrence_total": 37,
        "zero_or_one_occurrence_total": 34,
        "individual_boolean_mutation_total": 37,
        "real_effect_count": 0,
    }, "summary values invalid")

    for section in SECTIONS:
        sha(fixture[section + "_fingerprint"], section + " fingerprint")
        ensure(fixture[section + "_fingerprint"] == digest(fixture[section]), f"section fingerprint mismatch {section}")
    ensure(
        fixture["fixture_canonical_sha256"]
        == digest({key: value for key, value in fixture.items() if key != "fixture_canonical_sha256"}),
        "root fingerprint mismatch",
    )

    mutation_counts = mutation_suite(fixture, source, expected_inventory) if run_mutations else {}
    return {
        "result": "PASS_NO_BLOCKER",
        "source_count_occurrence_count": 37,
        "source_zero_or_one_occurrence_count": 34,
        **mutation_counts,
        "R5_first_apply_semantics_changed": False,
        "R6_first_apply_semantics_changed": False,
        "accepted_real_handoff_count": 0,
        "claim_event_count": 0,
        "armed_dispatch_count": 0,
        "runtime_consumable_count": 0,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }


def validate_counterexample_profile(profile: Any, source: dict[str, Any]) -> None:
    expected_fields = {
        "source_case_id",
        "mutated_json_pointers",
        "replacement_json_value",
        "changed_non_digest_fields",
        "recomputed_arm_guard_cases_fingerprint",
        "recomputed_fixture_canonical_sha256",
        "rendered_file_sha256",
        "R6_independent_review_rendered_sha256",
        "expected_R7_decision",
    }
    ensure(isinstance(profile, dict) and set(profile) == expected_fields, "counterexample profile inventory invalid")
    pointers = [f"/arm_guard_cases/0/derived/{field}" for field in DERIVED_COUNT_FIELDS]
    ensure(profile["source_case_id"] == "FIRST_APPLY_1_ELIGIBLE", "counterexample source invalid")
    ensure(profile["mutated_json_pointers"] == pointers, "counterexample pointers invalid")
    ensure(type(profile["replacement_json_value"]) is bool and profile["replacement_json_value"] is True, "replacement invalid")
    exact_count(profile["changed_non_digest_fields"], "counterexample.changed_non_digest_fields")
    ensure(profile["changed_non_digest_fields"] == 4, "counterexample changed count invalid")
    for field in (
        "recomputed_arm_guard_cases_fingerprint",
        "recomputed_fixture_canonical_sha256",
        "rendered_file_sha256",
        "R6_independent_review_rendered_sha256",
    ):
        sha(profile[field], "counterexample." + field)
    ensure(profile["R6_independent_review_rendered_sha256"] == "79e949da2501d7acaecc5898b19caa461b54776e81e0cc71ca30b51bfa21e7fa", "review binding invalid")
    ensure(profile["expected_R7_decision"] == "REJECT_WRONG_SCALAR_TYPE", "counterexample result invalid")
    item = copy.deepcopy(source)
    for pointer in pointers:
        pointer_set(item, pointer, True)
    resign_source(item, "arm_guard_cases")
    ensure(profile["recomputed_arm_guard_cases_fingerprint"] == item["arm_guard_cases_fingerprint"], "counterexample section digest invalid")
    ensure(profile["recomputed_fixture_canonical_sha256"] == item["fixture_canonical_sha256"], "counterexample root digest invalid")
    ensure(profile["rendered_file_sha256"] == hashlib.sha256(render(item)).hexdigest(), "counterexample rendered digest invalid")


def resign_source(source: dict[str, Any], section: str) -> None:
    source[section + "_fingerprint"] = digest(source[section])
    source["fixture_canonical_sha256"] = digest(
        {key: value for key, value in source.items() if key != "fixture_canonical_sha256"}
    )


def resign_fixture(fixture: dict[str, Any], section: str) -> None:
    fixture[section + "_fingerprint"] = digest(fixture[section])
    fixture["fixture_canonical_sha256"] = digest(
        {key: value for key, value in fixture.items() if key != "fixture_canonical_sha256"}
    )


def source_rejected(source: dict[str, Any]) -> bool:
    try:
        validate_source_surface(source)
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        return True
    return False


def fixture_rejected(fixture: dict[str, Any]) -> bool:
    try:
        validate_fixture(fixture, run_mutations=False)
    except (ValueError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
        return True
    return False


def mutation_suite(
    fixture: dict[str, Any],
    source: dict[str, Any],
    inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    source_rejections = 0
    for row in inventory:
        item = copy.deepcopy(source)
        replacement = bool(row["integer_value"])
        pointer_set(item, row["json_pointer"], replacement)
        resign_source(item, row["section"])
        ensure(source_rejected(item), f"source boolean mutation accepted at {row['json_pointer']}")
        source_rejections += 1

    item = copy.deepcopy(source)
    for field in DERIVED_COUNT_FIELDS:
        pointer_set(item, f"/arm_guard_cases/0/derived/{field}", True)
    resign_source(item, "arm_guard_cases")
    ensure(source_rejected(item), "four-field R6 boolean counterexample accepted")

    evidence_rejections = 0
    for index, row in enumerate(inventory):
        item = copy.deepcopy(fixture)
        item["count_inventory"][index]["integer_value"] = bool(row["integer_value"])
        resign_fixture(item, "count_inventory")
        ensure(fixture_rejected(item), f"R7 evidence-row boolean mutation accepted at {index}")
        evidence_rejections += 1

    closed_inventory_mutations = []
    item = copy.deepcopy(fixture); item["unknown_root"] = True
    item["fixture_canonical_sha256"] = digest({key: value for key, value in item.items() if key != "fixture_canonical_sha256"})
    closed_inventory_mutations.append(item)
    item = copy.deepcopy(fixture); item["exact_integer_profile"]["unknown"] = True; resign_fixture(item, "exact_integer_profile")
    closed_inventory_mutations.append(item)
    item = copy.deepcopy(fixture); item["count_inventory"][0]["unknown"] = True; resign_fixture(item, "count_inventory")
    closed_inventory_mutations.append(item)
    ensure(all(fixture_rejected(item) for item in closed_inventory_mutations), "closed inventory mutation accepted")

    item = copy.deepcopy(fixture)
    item["exact_integer_profile"]["maximum"] = True
    resign_fixture(item, "exact_integer_profile")
    ensure(fixture_rejected(item), "profile boolean-as-integer mutation accepted")

    return {
        "fully_resigned_source_boolean_mutations_rejected": source_rejections,
        "fully_resigned_zero_or_one_source_mutations_rejected": 34,
        "fully_resigned_evidence_row_boolean_mutations_rejected": evidence_rejections,
        "four_field_R6_counterexample_rejected": True,
        "closed_inventory_mutations_rejected": len(closed_inventory_mutations),
        "profile_boolean_as_integer_mutation_rejected": True,
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
