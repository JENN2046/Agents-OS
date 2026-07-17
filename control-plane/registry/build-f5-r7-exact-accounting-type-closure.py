#!/usr/bin/env python3
"""Build the fixed nonauthority F5 R7 exact accounting type proof fixture."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any


SOURCE_R6 = Path(
    "control-plane/registry/examples/"
    "2026-07-17-agents-os-f5-r6-first-apply-eligibility-guard-v0.1.json"
)
DEFAULT_OUTPUT = Path(
    "control-plane/registry/examples/"
    "2026-07-17-agents-os-f5-r7-exact-accounting-type-closure-v0.1.json"
)
SOURCE_R6_SHA256 = "853dda58e07fa88c460b4da7f177d70a4cf3efc62484a0a4c435e464f80889e8"
SOURCE_R6_CANONICAL_SHA256 = "5447834426db9fbd49d1261f48bba788e3a546f585f289fe3966e720bb9da2b2"
FIXTURE_INTERFACE = "agents-os.f5-r7-exact-accounting-type-closure-fixture.v0.1"
SAFE_INTEGER = 9007199254740991
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
SUMMARY_COUNT_FIELDS = (
    "arm_guard_case_count",
    "first_apply_case_count",
    "adversarial_case_count",
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


def load_source() -> dict[str, Any]:
    ensure(file_sha256(SOURCE_R6) == SOURCE_R6_SHA256, "R6 source file hash mismatch")
    source = parse_strict(SOURCE_R6.read_text(encoding="utf-8"))
    validate_json(source)
    ensure(isinstance(source, dict), "R6 source root invalid")
    ensure(
        source.get("fixture_canonical_sha256") == SOURCE_R6_CANONICAL_SHA256,
        "R6 source canonical field mismatch",
    )
    ensure(
        digest({key: value for key, value in source.items() if key != "fixture_canonical_sha256"})
        == SOURCE_R6_CANONICAL_SHA256,
        "R6 source canonical digest mismatch",
    )
    return source


def count_inventory(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(pointer: str, section: str, field_class: str) -> None:
        value = pointer_get(source, pointer)
        ensure(type(value) is int and 0 <= value <= SAFE_INTEGER, f"source count invalid at {pointer}")
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
    for field in SUMMARY_COUNT_FIELDS:
        add(f"/summary/{field}", "summary", "PROOF_SUMMARY_COUNT")

    ensure(len(rows) == 37, "closed count inventory must contain 37 occurrences")
    ensure(sum(row["integer_value"] in (0, 1) for row in rows) == 34, "zero-or-one count must be 34")
    return rows


def resign_source(source: dict[str, Any], section: str) -> None:
    source[section + "_fingerprint"] = digest(source[section])
    source["fixture_canonical_sha256"] = digest(
        {key: value for key, value in source.items() if key != "fixture_canonical_sha256"}
    )


def multi_field_counterexample(source: dict[str, Any]) -> dict[str, Any]:
    item = copy.deepcopy(source)
    pointers = [f"/arm_guard_cases/0/derived/{field}" for field in DERIVED_COUNT_FIELDS]
    for pointer in pointers:
        pointer_set(item, pointer, True)
    resign_source(item, "arm_guard_cases")
    return {
        "source_case_id": "FIRST_APPLY_1_ELIGIBLE",
        "mutated_json_pointers": pointers,
        "replacement_json_value": True,
        "changed_non_digest_fields": 4,
        "recomputed_arm_guard_cases_fingerprint": item["arm_guard_cases_fingerprint"],
        "recomputed_fixture_canonical_sha256": item["fixture_canonical_sha256"],
        "rendered_file_sha256": hashlib.sha256(render(item)).hexdigest(),
        "R6_independent_review_rendered_sha256": "79e949da2501d7acaecc5898b19caa461b54776e81e0cc71ca30b51bfa21e7fa",
        "expected_R7_decision": "REJECT_WRONG_SCALAR_TYPE",
    }


def build_fixture() -> dict[str, Any]:
    source = load_source()
    inventory = count_inventory(source)
    fixture: dict[str, Any] = {
        "fixture_interface": FIXTURE_INTERFACE,
        "environment": "SYNTHETIC_TEST",
        "authority_eligible": False,
        "runtime_consumable": False,
        "recovery_importable": False,
        "source_binding": {
            "path": str(SOURCE_R6),
            "file_sha256": SOURCE_R6_SHA256,
            "fixture_canonical_sha256": SOURCE_R6_CANONICAL_SHA256,
            "fixture_interface": source["fixture_interface"],
        },
        "exact_integer_profile": {
            "json_scalar_type": "INTEGER",
            "boolean_is_integer": False,
            "float_is_integer": False,
            "minimum": 0,
            "maximum": SAFE_INTEGER,
            "validation_order": "TYPE_BEFORE_EQUALITY_MAPPING_OR_DIGEST_TRUST",
            "closed_count_occurrence_total": 37,
            "zero_or_one_occurrence_total": 34,
        },
        "count_inventory": inventory,
        "adversarial_profile": {
            "individual_fully_resigned_boolean_substitution_count": 37,
            "prior_independent_accepted_zero_or_one_substitution_count": 34,
            "required_individual_result": "REJECT_WRONG_SCALAR_TYPE",
            "multi_field_R6_counterexample": multi_field_counterexample(source),
        },
        "assertions": {
            "synthetic_nonauthority": True,
            "R6_first_apply_semantics_changed": False,
            "R5_receipt_or_arm_semantics_changed": False,
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
            "count_occurrence_total": 37,
            "zero_or_one_occurrence_total": 34,
            "individual_boolean_mutation_total": 37,
            "real_effect_count": 0,
        },
    }
    for section in SECTIONS:
        fixture[section + "_fingerprint"] = digest(fixture[section])
    fixture["fixture_canonical_sha256"] = digest(fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.write_bytes(render(build_fixture()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
