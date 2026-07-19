#!/usr/bin/env python3
"""Validate the deterministic synthetic F8 R5 H01 owner-binding witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


DOMAIN = "agents-os:f8-r5-h01-owner-commitment-stable-ref-closure:v0.1"
R2_FIXTURE_SHA256 = "36d60ffc0ff0b184c7d306b6293601a3661a22affe1cab8b00da609cb280f501"
R2_VALIDATOR_SHA256 = "9ac243f7aecc0519da5b5bb7266cd604260894861f2c4a3edf98039adbaba65d"
R2_H01_ROW_FINGERPRINT = "867b7f110b5ee7c34c314850f20ff488a8574c77164ded7d06736b6b3b085787"
TRUSTED_H01_OWNER_SOURCE_ANCHOR = "79fbc671c0852b990f2c605dc7c77733ff9e150087e2e30cc910eada638cdbaa"
MAX_SAFE_INTEGER = 9007199254740991
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
CONSUMER_FIELDS = [
    "assessment_id",
    "expected_assessment_revision",
    "expected_assessment_fingerprint",
    "owner_commitment_ref",
    "expected_owner_commitment_revision",
    "expected_owner_commitment_fingerprint",
]
EXPECTED_NON_NULL_ROLES = [
    "actor_identity",
    "f3_readiness",
    "f7_intent_currentness",
    "jenn_requirement",
    "pbl_currentness",
    "principal_binding",
    "responsibility",
]
EXPECTED_ALL_ROLES = [
    "actor_identity",
    "f3_readiness",
    "f7_intent_currentness",
    "jenn_exact_decision",
    "jenn_requirement",
    "pbl_currentness",
    "principal_binding",
    "responsibility",
]
ROOT_FIELDS = {
    "schema_version", "contract_id", "environment", "runtime_usable", "domain_tag",
    "schema_inventory", "trusted_H01_owner_commitment_source",
    "merged_H01_derivation_cases", "stable_ref_vectors", "boundary_assertions",
    "section_fingerprints", "root_fingerprint",
}
SOURCE_FIELDS = {
    "role", "owner_contract", "commitment_ref", "commitment_revision",
    "assessment_id", "assessment_revision", "assessment_fingerprint",
    "issued_event_ref", "issued_event_sequence", "issued_event_fingerprint",
    "commitment_fingerprint",
}
RESOLUTION_FIELDS = {
    "role", "consumer", "resolved_commitment_ref", "resolved_commitment_revision",
    "resolved_commitment_fingerprint", "resolution", "owner_lookup_performed",
    "row_fingerprint",
}
MERGED_FIELDS = {
    "source_case_id", "source_row_fingerprint", "source_raw_input_fingerprint",
    "source_consumer_inventory_fingerprint", "trusted_owner_source_anchor",
    "upgraded_consumers", "owner_commitment_resolutions",
    "downprojected_consumer_inventory_fingerprint", "derived_decision",
    "row_fingerprint",
}
VECTOR_FIELDS = {
    "case_id", "input_kind", "literal_value", "codepoints", "expected_valid",
    "row_fingerprint",
}
BOUNDARY_FIELDS = {
    "runtime_usable_count", "real_Home_count", "real_Command_count", "task_write_count",
    "database_write_count", "provider_call_count", "production_authentication_count",
    "private_Memory_read_count", "sensing_or_recording_count", "external_effect_count",
    "terminal_outcome",
}
DECISION_FIELDS = {
    "F3_command_ref", "F3_intake_ref", "F3_recheck_required", "command_authority",
    "effect_authority", "primary_reason", "reason_codes", "result", "runtime_usable",
    "task_write_authority",
}
EXPECTED_SCHEMA_FIELDS = {
    "TrustedH01OwnerCommitmentV0_1R5": [
        "role", "owner_contract", "commitment_ref", "commitment_revision",
        "assessment_id", "assessment_revision", "assessment_fingerprint",
        "issued_event_ref", "issued_event_sequence", "issued_event_fingerprint",
        "commitment_fingerprint",
    ],
    "H01OwnerCommitmentResolutionV0_1R5": [
        "role", "consumer", "resolved_commitment_ref",
        "resolved_commitment_revision", "resolved_commitment_fingerprint",
        "resolution", "owner_lookup_performed", "row_fingerprint",
    ],
    "MergedR2R3R4H01DerivationV0_1R5": [
        "source_case_id", "source_row_fingerprint",
        "source_raw_input_fingerprint", "source_consumer_inventory_fingerprint",
        "trusted_owner_source_anchor", "upgraded_consumers",
        "owner_commitment_resolutions",
        "downprojected_consumer_inventory_fingerprint", "derived_decision",
        "row_fingerprint",
    ],
}


class DuplicateKeyError(ValueError):
    pass


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=strict_object,
        parse_constant=reject_constant,
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def plain_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def without(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {name: item for name, item in value.items() if name != key}


def exact_fields(value: Any, expected: set[str] | list[str], path: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{path}: object required")
        return False
    expected_set = set(expected)
    actual = set(value)
    if actual != expected_set:
        errors.append(
            f"{path}: exact fields required missing={sorted(expected_set-actual)} extra={sorted(actual-expected_set)}"
        )
        return False
    return True


def stable_ref(value: Any) -> bool:
    return (
        type(value) is str
        and bool(value)
        and unicodedata.normalize("NFC", value) == value
    )


def positive_int(value: Any) -> bool:
    return type(value) is int and 0 < value <= MAX_SAFE_INTEGER


def valid_hash(value: Any) -> bool:
    return type(value) is str and HASH_RE.fullmatch(value) is not None


def validate_json_value(value: Any, path: str, errors: list[str]) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            errors.append(f"{path}: integer outside JSON safe range")
        return
    if type(value) is float:
        errors.append(f"{path}: float forbidden")
        return
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value:
            errors.append(f"{path}: non-NFC string")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]", errors)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                errors.append(f"{path}: non-string key")
            validate_json_value(item, f"{path}.{key}", errors)
        return
    errors.append(f"{path}: unsupported JSON value")


def validate_consumer(value: Any, path: str, errors: list[str]) -> str | None:
    if not exact_fields(value, CONSUMER_FIELDS, path, errors):
        return None
    null_count = sum(value[field] is None for field in CONSUMER_FIELDS)
    if null_count == len(CONSUMER_FIELDS):
        return "ALL_NULL"
    if null_count:
        errors.append(f"{path}: MIXED_NULL_INVALID")
        return None
    for key in ("assessment_id", "owner_commitment_ref"):
        if not stable_ref(value[key]):
            errors.append(f"{path}.{key}: stable_ref required")
    for key in ("expected_assessment_revision", "expected_owner_commitment_revision"):
        if not positive_int(value[key]):
            errors.append(f"{path}.{key}: positive safe integer required")
    for key in ("expected_assessment_fingerprint", "expected_owner_commitment_fingerprint"):
        if not valid_hash(value[key]):
            errors.append(f"{path}.{key}: lowercase SHA-256 required")
    return "ALL_NON_NULL" if not any(error.startswith(path) for error in errors) else None


def locate_h01(r2_fixture: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in r2_fixture.get("handoff_cases", []) if row.get("case_id") == "H01"]
    if len(rows) != 1:
        raise ValueError("R2 fixture must contain exactly one H01")
    row = rows[0]
    if row.get("row_fingerprint") != R2_H01_ROW_FINGERPRINT:
        raise ValueError("R2 H01 fingerprint mismatch")
    return row


def load_r2_validator(path: Path) -> Any:
    if hashlib.sha256(path.read_bytes()).hexdigest() != R2_VALIDATOR_SHA256:
        raise ValueError("R2 validator hash mismatch")
    spec = importlib.util.spec_from_file_location("f8_r2_fixed_validator_for_r5", path)
    if spec is None or spec.loader is None:
        raise ValueError("unable to load fixed R2 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_source_records(
    records: Any,
    r2_fixture: dict[str, Any],
    h01: dict[str, Any],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    if type(records) is not list or len(records) != len(EXPECTED_NON_NULL_ROLES):
        errors.append("trusted_H01_owner_commitment_source: expected seven rows")
        return {}
    roles = [row.get("role") if type(row) is dict else None for row in records]
    if roles != EXPECTED_NON_NULL_ROLES:
        errors.append("trusted_H01_owner_commitment_source: canonical role order mismatch")
    source_anchor = digest(DOMAIN + ":trusted-owner-source-anchor", records)
    if source_anchor != TRUSTED_H01_OWNER_SOURCE_ANCHOR:
        errors.append("trusted_H01_owner_commitment_source: immutable trusted anchor mismatch")
    assessments = {row["assessment_id"]: row for row in r2_fixture["upstream_assessments"]}
    consumers = h01["raw_input"]["assessment_consumers"]
    index: dict[str, dict[str, Any]] = {}
    for position, row in enumerate(records):
        path = f"trusted_H01_owner_commitment_source[{position}]"
        if not exact_fields(row, SOURCE_FIELDS, path, errors):
            continue
        role = row["role"]
        if role not in EXPECTED_NON_NULL_ROLES or role in index:
            errors.append(f"{path}.role: unknown or duplicate role")
            continue
        consumer = consumers[role]
        assessment = assessments.get(consumer["assessment_id"])
        for key in ("role", "owner_contract", "commitment_ref", "assessment_id", "issued_event_ref"):
            if not stable_ref(row[key]):
                errors.append(f"{path}.{key}: stable_ref required")
        for key in ("commitment_revision", "assessment_revision", "issued_event_sequence"):
            if not positive_int(row[key]):
                errors.append(f"{path}.{key}: positive safe integer required")
        for key in ("assessment_fingerprint", "issued_event_fingerprint", "commitment_fingerprint"):
            if not valid_hash(row[key]):
                errors.append(f"{path}.{key}: lowercase SHA-256 required")
        if assessment is None or row["owner_contract"] != assessment["owner_contract"]:
            errors.append(f"{path}: owner contract mismatch")
        if (
            row["assessment_id"], row["assessment_revision"], row["assessment_fingerprint"]
        ) != (
            consumer["assessment_id"], consumer["expected_assessment_revision"],
            consumer["expected_assessment_fingerprint"],
        ):
            errors.append(f"{path}: committed assessment tuple mismatch")
        event = {
            "owner_contract": row["owner_contract"],
            "role": role,
            "assessment_id": row["assessment_id"],
            "assessment_revision": row["assessment_revision"],
            "issued_event_ref": row["issued_event_ref"],
            "issued_event_sequence": row["issued_event_sequence"],
        }
        if row["issued_event_fingerprint"] != digest(DOMAIN + ":owner-issued-event", event):
            errors.append(f"{path}: issued Event fingerprint mismatch")
        if row["commitment_fingerprint"] != digest(
            DOMAIN + ":trusted-owner-commitment", without(row, "commitment_fingerprint")
        ):
            errors.append(f"{path}: commitment fingerprint mismatch")
        index[role] = row
    return index


def derive_h01(
    merged: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
    h01: dict[str, Any],
    r2_fixture: dict[str, Any],
    r2_validator: Any,
    errors: list[str],
) -> dict[str, Any] | None:
    upgraded = merged["upgraded_consumers"]
    source_consumers = h01["raw_input"]["assessment_consumers"]
    if type(upgraded) is not dict or list(upgraded) != EXPECTED_ALL_ROLES:
        errors.append("merged_H01_derivation_cases[0].upgraded_consumers: exact role inventory and order required")
        return None
    downprojected: dict[str, dict[str, Any]] = {}
    expected_resolutions: list[dict[str, Any]] = []
    for role in EXPECTED_ALL_ROLES:
        consumer = upgraded[role]
        local: list[str] = []
        shape = validate_consumer(consumer, f"merged_H01.upgraded_consumers.{role}", local)
        errors.extend(local)
        expected_shape = "ALL_NULL" if role == "jenn_exact_decision" else "ALL_NON_NULL"
        if shape != expected_shape:
            errors.append(f"merged_H01.upgraded_consumers.{role}: expected {expected_shape}")
            continue
        downprojected[role] = {key: consumer[key] for key in CONSUMER_FIELDS[:3]}
        if shape == "ALL_NULL":
            resolution = {
                "role": role,
                "consumer": consumer,
                "resolved_commitment_ref": None,
                "resolved_commitment_revision": None,
                "resolved_commitment_fingerprint": None,
                "resolution": "OPTIONAL_ALL_NULL_NO_LOOKUP",
                "owner_lookup_performed": False,
            }
        else:
            source = source_index.get(role)
            if source is None:
                errors.append(f"merged_H01.upgraded_consumers.{role}: trusted source missing")
                continue
            if (
                consumer["owner_commitment_ref"],
                consumer["expected_owner_commitment_revision"],
                consumer["expected_owner_commitment_fingerprint"],
            ) != (
                source["commitment_ref"], source["commitment_revision"],
                source["commitment_fingerprint"],
            ):
                errors.append(f"merged_H01.upgraded_consumers.{role}: exact owner commitment mismatch")
            if (
                consumer["assessment_id"], consumer["expected_assessment_revision"],
                consumer["expected_assessment_fingerprint"],
            ) != (
                source["assessment_id"], source["assessment_revision"],
                source["assessment_fingerprint"],
            ):
                errors.append(f"merged_H01.upgraded_consumers.{role}: committed assessment mismatch")
            resolution = {
                "role": role,
                "consumer": consumer,
                "resolved_commitment_ref": source["commitment_ref"],
                "resolved_commitment_revision": source["commitment_revision"],
                "resolved_commitment_fingerprint": source["commitment_fingerprint"],
                "resolution": "EXACT_TRUSTED_OWNER_COMMITMENT",
                "owner_lookup_performed": True,
            }
        expected_resolutions.append({
            **resolution,
            "row_fingerprint": digest(DOMAIN + ":owner-resolution", resolution),
        })
    if downprojected != source_consumers:
        errors.append("merged_H01_derivation_cases[0]: exact R2 consumer down-projection mismatch")
    if merged["downprojected_consumer_inventory_fingerprint"] != plain_sha(downprojected):
        errors.append("merged_H01_derivation_cases[0]: down-projection fingerprint mismatch")
    actual_resolutions = merged["owner_commitment_resolutions"]
    if actual_resolutions != expected_resolutions:
        errors.append("merged_H01_derivation_cases[0]: owner resolution inventory not independently derived")
    try:
        derived = r2_validator.derive_case(h01["raw_input"], r2_fixture["upstream_assessments"])
    except Exception as exc:
        errors.append(f"merged_H01_derivation_cases[0]: fixed R2 reducer stable BLOCK ({type(exc).__name__})")
        return None
    if derived.get("result") != "CANDIDATE_FORMED":
        errors.append("merged_H01_derivation_cases[0]: fixed R2 reducer did not derive CANDIDATE_FORMED")
    if any(error.startswith("merged_H01") for error in errors):
        return None
    return derived


def validate_fixture(
    fixture: Any,
    r2_fixture: dict[str, Any],
    r2_validator: Any,
) -> list[str]:
    errors: list[str] = []
    validate_json_value(fixture, "$", errors)
    if not exact_fields(fixture, ROOT_FIELDS, "$", errors):
        return errors
    if fixture["schema_version"] != "agents-os.f8-r5-h01-owner-commitment-stable-ref-closure-witness.v0.1":
        errors.append("$: schema_version mismatch")
    if fixture["contract_id"] != "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R5":
        errors.append("$: contract_id mismatch")
    if fixture["environment"] != "SYNTHETIC_TEST" or fixture["runtime_usable"] is not False or fixture["domain_tag"] != DOMAIN:
        errors.append("$: synthetic boundary mismatch")

    inventory = fixture["schema_inventory"]
    expected_schema_ids = [
        "TrustedH01OwnerCommitmentV0_1R5",
        "H01OwnerCommitmentResolutionV0_1R5",
        "MergedR2R3R4H01DerivationV0_1R5",
    ]
    if type(inventory) is not list or len(inventory) != 3:
        errors.append("schema_inventory: expected three rows")
    else:
        if [row.get("schema_id") for row in inventory] != expected_schema_ids:
            errors.append("schema_inventory: canonical schema order mismatch")
        for index, row in enumerate(inventory):
            path = f"schema_inventory[{index}]"
            if type(row) is not dict or set(row) != {"schema_id", "fields", "closed", "schema_fingerprint"}:
                errors.append(f"{path}: exact fields required")
                continue
            if (
                row["closed"] is not True
                or row["fields"] != EXPECTED_SCHEMA_FIELDS.get(row["schema_id"])
            ):
                errors.append(f"{path}: invalid closed schema row")
            if row["schema_fingerprint"] != digest(DOMAIN + ":schema", without(row, "schema_fingerprint")):
                errors.append(f"{path}: fingerprint mismatch")

    h01 = locate_h01(r2_fixture)
    source_index = validate_source_records(
        fixture["trusted_H01_owner_commitment_source"], r2_fixture, h01, errors
    )

    merged_rows = fixture["merged_H01_derivation_cases"]
    if type(merged_rows) is not list or len(merged_rows) != 1:
        errors.append("merged_H01_derivation_cases: expected one row")
    else:
        merged = merged_rows[0]
        if exact_fields(merged, MERGED_FIELDS, "merged_H01_derivation_cases[0]", errors):
            source_consumers = h01["raw_input"]["assessment_consumers"]
            if merged["source_case_id"] != "H01" or merged["source_row_fingerprint"] != h01["row_fingerprint"]:
                errors.append("merged_H01_derivation_cases[0]: source H01 binding mismatch")
            if merged["source_raw_input_fingerprint"] != plain_sha(h01["raw_input"]):
                errors.append("merged_H01_derivation_cases[0]: source raw-input fingerprint mismatch")
            if merged["source_consumer_inventory_fingerprint"] != plain_sha(source_consumers):
                errors.append("merged_H01_derivation_cases[0]: source consumer fingerprint mismatch")
            if merged["trusted_owner_source_anchor"] != TRUSTED_H01_OWNER_SOURCE_ANCHOR:
                errors.append("merged_H01_derivation_cases[0]: trusted owner-source anchor mismatch")
            derived = derive_h01(merged, source_index, h01, r2_fixture, r2_validator, errors)
            if derived is None:
                if merged["derived_decision"].get("result") == "CANDIDATE_FORMED":
                    errors.append("merged_H01_derivation_cases[0]: favorable result without complete derivation")
            elif merged["derived_decision"] != derived:
                errors.append("merged_H01_derivation_cases[0]: claimed decision not independently derived")
            decision = merged["derived_decision"]
            if exact_fields(decision, DECISION_FIELDS, "merged_H01_derivation_cases[0].derived_decision", errors):
                for key in ("runtime_usable", "command_authority", "task_write_authority", "effect_authority"):
                    if decision[key] is not False:
                        errors.append(f"merged_H01_derivation_cases[0].derived_decision.{key}: false required")
            if merged["row_fingerprint"] != digest(
                DOMAIN + ":merged-H01-derivation", without(merged, "row_fingerprint")
            ):
                errors.append("merged_H01_derivation_cases[0]: row fingerprint mismatch")

    vectors = fixture["stable_ref_vectors"]
    if type(vectors) is not list or len(vectors) != 2:
        errors.append("stable_ref_vectors: expected two rows")
    else:
        expected_ids = ["SR-NFC-INTERNAL-SPACE", "SR-NON-NFC-CODEPOINTS"]
        if [row.get("case_id") for row in vectors] != expected_ids:
            errors.append("stable_ref_vectors: canonical order mismatch")
        for index, row in enumerate(vectors):
            path = f"stable_ref_vectors[{index}]"
            if not exact_fields(row, VECTOR_FIELDS, path, errors):
                continue
            if row["input_kind"] == "LITERAL":
                if not stable_ref(row["literal_value"]) or row["codepoints"] is not None:
                    actual = False
                else:
                    actual = stable_ref(row["literal_value"])
            elif row["input_kind"] == "CODEPOINTS":
                if type(row["codepoints"]) is not list or not all(type(x) is int and 0 <= x <= 0x10FFFF for x in row["codepoints"]):
                    errors.append(f"{path}.codepoints: valid codepoint list required")
                    actual = False
                else:
                    actual = stable_ref("".join(chr(x) for x in row["codepoints"]))
                if row["literal_value"] is not None:
                    errors.append(f"{path}.literal_value: null required")
            else:
                errors.append(f"{path}.input_kind: closed enum required")
                actual = False
            if type(row["expected_valid"]) is not bool or actual is not row["expected_valid"]:
                errors.append(f"{path}: stable_ref result mismatch")
            if index == 0 and without(row, "row_fingerprint") != {
                "case_id": "SR-NFC-INTERNAL-SPACE",
                "input_kind": "LITERAL",
                "literal_value": "synthetic://owner commitment/h01",
                "codepoints": None,
                "expected_valid": True,
            }:
                errors.append(f"{path}: canonical internal-space positive vector mismatch")
            if index == 1 and without(row, "row_fingerprint") != {
                "case_id": "SR-NON-NFC-CODEPOINTS",
                "input_kind": "CODEPOINTS",
                "literal_value": None,
                "codepoints": [115, 121, 110, 116, 104, 101, 116, 105, 99, 58, 47, 47, 99, 97, 102, 101, 769],
                "expected_valid": False,
            }:
                errors.append(f"{path}: canonical non-NFC negative vector mismatch")
            if row["row_fingerprint"] != digest(DOMAIN + ":stable-ref-vector", without(row, "row_fingerprint")):
                errors.append(f"{path}: row fingerprint mismatch")

    boundary = fixture["boundary_assertions"]
    if exact_fields(boundary, BOUNDARY_FIELDS, "boundary_assertions", errors):
        for key in BOUNDARY_FIELDS - {"terminal_outcome"}:
            if type(boundary[key]) is not int or boundary[key] != 0:
                errors.append(f"boundary_assertions.{key}: integer zero required")
        if boundary["terminal_outcome"] != "NOT_EXECUTED":
            errors.append("boundary_assertions.terminal_outcome: NOT_EXECUTED required")

    section_names = [
        "schema_inventory", "trusted_H01_owner_commitment_source",
        "merged_H01_derivation_cases", "stable_ref_vectors", "boundary_assertions",
    ]
    expected_sections = {
        name: digest(DOMAIN + ":section:" + name, fixture[name]) for name in section_names
    }
    if fixture["section_fingerprints"] != expected_sections:
        errors.append("section_fingerprints: exact derived inventory mismatch")
    if fixture["root_fingerprint"] != digest(DOMAIN + ":root", without(fixture, "root_fingerprint")):
        errors.append("root_fingerprint: mismatch")
    return errors


def resign_fixture(value: dict[str, Any]) -> None:
    for row in value.get("trusted_H01_owner_commitment_source", []):
        if type(row) is dict:
            row["commitment_fingerprint"] = digest(
                DOMAIN + ":trusted-owner-commitment", without(row, "commitment_fingerprint")
            )
    merged_rows = value.get("merged_H01_derivation_cases", [])
    if type(merged_rows) is list and merged_rows and type(merged_rows[0]) is dict:
        merged = merged_rows[0]
        for row in merged.get("owner_commitment_resolutions", []):
            if type(row) is dict:
                row["row_fingerprint"] = digest(
                    DOMAIN + ":owner-resolution", without(row, "row_fingerprint")
                )
        merged["row_fingerprint"] = digest(
            DOMAIN + ":merged-H01-derivation", without(merged, "row_fingerprint")
        )
    for row in value.get("stable_ref_vectors", []):
        if type(row) is dict:
            row["row_fingerprint"] = digest(
                DOMAIN + ":stable-ref-vector", without(row, "row_fingerprint")
            )
    section_names = [
        "schema_inventory", "trusted_H01_owner_commitment_source",
        "merged_H01_derivation_cases", "stable_ref_vectors", "boundary_assertions",
    ]
    value["section_fingerprints"] = {
        name: digest(DOMAIN + ":section:" + name, value[name]) for name in section_names
    }
    value["root_fingerprint"] = digest(DOMAIN + ":root", without(value, "root_fingerprint"))


def run_regressions(
    fixture: dict[str, Any],
    r2_fixture: dict[str, Any],
    r2_validator: Any,
) -> tuple[int, list[str]]:
    failures: list[str] = []
    probes: list[tuple[str, dict[str, Any], str]] = []

    def add(name: str, value: dict[str, Any], target: str) -> None:
        resign_fixture(value)
        probes.append((name, value, target))

    for field, replacement in (
        ("owner_commitment_ref", "synthetic://attacker/commitment@1"),
        ("expected_owner_commitment_revision", 2),
        ("expected_owner_commitment_fingerprint", "f" * 64),
    ):
        value = copy.deepcopy(fixture)
        consumer = value["merged_H01_derivation_cases"][0]["upgraded_consumers"]["f7_intent_currentness"]
        consumer[field] = replacement
        resolution = value["merged_H01_derivation_cases"][0]["owner_commitment_resolutions"][2]
        mapping = {
            "owner_commitment_ref": "resolved_commitment_ref",
            "expected_owner_commitment_revision": "resolved_commitment_revision",
            "expected_owner_commitment_fingerprint": "resolved_commitment_fingerprint",
        }
        resolution["consumer"][field] = replacement
        resolution[mapping[field]] = replacement
        add(f"commitment-{field}-substitution", value, "exact owner commitment mismatch")

    value = copy.deepcopy(fixture)
    merged = value["merged_H01_derivation_cases"][0]
    merged["upgraded_consumers"]["f7_intent_currentness"].update({
        key: merged["upgraded_consumers"]["actor_identity"][key]
        for key in CONSUMER_FIELDS[3:]
    })
    merged["owner_commitment_resolutions"][2]["consumer"] = copy.deepcopy(
        merged["upgraded_consumers"]["f7_intent_currentness"]
    )
    add("commitment-tuple-cross-role", value, "exact owner commitment mismatch")

    value = copy.deepcopy(fixture)
    source = value["trusted_H01_owner_commitment_source"][2]
    source["commitment_ref"] = "synthetic://attacker/source/rewrite@1"
    merged = value["merged_H01_derivation_cases"][0]
    consumer = merged["upgraded_consumers"]["f7_intent_currentness"]
    consumer["owner_commitment_ref"] = source["commitment_ref"]
    source["commitment_fingerprint"] = digest(
        DOMAIN + ":trusted-owner-commitment", without(source, "commitment_fingerprint")
    )
    consumer["expected_owner_commitment_fingerprint"] = source["commitment_fingerprint"]
    resolution = merged["owner_commitment_resolutions"][2]
    resolution["consumer"] = copy.deepcopy(consumer)
    resolution["resolved_commitment_ref"] = source["commitment_ref"]
    resolution["resolved_commitment_fingerprint"] = source["commitment_fingerprint"]
    merged["trusted_owner_source_anchor"] = digest(
        DOMAIN + ":trusted-owner-source-anchor", value["trusted_H01_owner_commitment_source"]
    )
    add("coordinated-source-and-consumer-rewrite", value, "immutable trusted anchor mismatch")

    for name, mutate in (
        ("source-row-delete", lambda rows: rows.pop()),
        ("source-row-duplicate", lambda rows: rows.append(copy.deepcopy(rows[-1]))),
        ("source-row-reorder", lambda rows: rows.reverse()),
    ):
        value = copy.deepcopy(fixture)
        mutate(value["trusted_H01_owner_commitment_source"])
        value["merged_H01_derivation_cases"][0]["trusted_owner_source_anchor"] = digest(
            DOMAIN + ":trusted-owner-source-anchor", value["trusted_H01_owner_commitment_source"]
        )
        add(name, value, "trusted_H01_owner_commitment_source")

    value = copy.deepcopy(fixture)
    value["merged_H01_derivation_cases"][0]["derived_decision"]["result"] = "REJECTED"
    add("claimed-result-change", value, "claimed decision not independently derived")

    value = copy.deepcopy(fixture)
    merged = value["merged_H01_derivation_cases"][0]
    merged["upgraded_consumers"]["actor_identity"]["expected_assessment_fingerprint"] = "e" * 64
    merged["owner_commitment_resolutions"][0]["consumer"] = copy.deepcopy(
        merged["upgraded_consumers"]["actor_identity"]
    )
    add("assessment-tuple-change-fixed-commitment", value, "committed assessment mismatch")

    value = copy.deepcopy(fixture)
    value["stable_ref_vectors"][0]["literal_value"] = "synthetic://cafe\u0301"
    add("non-NFC-stable-ref", value, "non-NFC string")

    for name, value, target in probes:
        errors = validate_fixture(value, r2_fixture, r2_validator)
        if not errors or not any(target in error for error in errors):
            failures.append(f"{name}: target={target!r} errors={errors[:5]!r}")

    if not stable_ref("synthetic://owner commitment/h01"):
        failures.append("NFC-internal-space-positive")
    if stable_ref("synthetic://cafe\u0301"):
        failures.append("non-NFC-direct-negative")
    if stable_ref(1) or stable_ref(None) or stable_ref(""):
        failures.append("stable-ref-primitive-profile")
    return len(probes) + 4, failures


def parser_probes() -> tuple[int, list[str]]:
    failures: list[str] = []
    samples = {
        "duplicate-key": '{"a":1,"a":2}',
        "float": '{"a":1.5}',
        "NaN": '{"a":NaN}',
    }
    for name, text in samples.items():
        rejected = False
        try:
            value = json.loads(text, object_pairs_hook=strict_object, parse_constant=reject_constant)
            local: list[str] = []
            validate_json_value(value, "probe", local)
            rejected = bool(local)
        except Exception:
            rejected = True
        if not rejected:
            failures.append(name)
    return len(samples), failures


def check_whitespace(paths: list[str]) -> int:
    errors: list[str] = []
    for name in paths:
        data = Path(name).read_bytes()
        if b"\r" in data:
            errors.append(f"{name}: CR byte")
        if not data.endswith(b"\n"):
            errors.append(f"{name}: missing final LF")
        for index, line in enumerate(data.splitlines(), 1):
            if line.endswith((b" ", b"\t")):
                errors.append(f"{name}:{index}: trailing whitespace")
    print(json.dumps({
        "errors": errors,
        "files_checked": len(paths),
        "result": "PASS" if not errors else "BLOCK",
    }, sort_keys=True))
    return 0 if not errors else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture",
        nargs="?",
        default="control-plane/registry/examples/2026-07-19-agents-os-f8-r5-h01-owner-commitment-stable-ref-closure-v0.1.json",
    )
    parser.add_argument(
        "--r2-fixture",
        default="control-plane/registry/examples/2026-07-19-agents-os-f8-r2-evidence-currentness-schema-closure-v0.1.json",
    )
    parser.add_argument(
        "--r2-validator",
        default="control-plane/registry/validate-f8-r2-evidence-currentness-schema-closure.py",
    )
    parser.add_argument("--check-whitespace", nargs="+")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check_whitespace:
        return check_whitespace(args.check_whitespace)
    try:
        fixture = load_json(Path(args.fixture))
        r2_path = Path(args.r2_fixture)
        if hashlib.sha256(r2_path.read_bytes()).hexdigest() != R2_FIXTURE_SHA256:
            raise ValueError("R2 fixture hash mismatch")
        r2_fixture = load_json(r2_path)
        r2_validator = load_r2_validator(Path(args.r2_validator))
        errors = validate_fixture(fixture, r2_fixture, r2_validator)
        regression_count, regression_failures = run_regressions(
            fixture, r2_fixture, r2_validator
        )
        parser_count, parser_failures = parser_probes()
    except Exception as exc:
        print(json.dumps({
            "result": "BLOCK",
            "errors": [f"stable BLOCK ({type(exc).__name__}): {exc}"],
        }, sort_keys=True))
        return 1
    errors.extend(f"regression: {item}" for item in regression_failures)
    errors.extend(f"parser: {item}" for item in parser_failures)
    result = {
        "result": "PASS" if not errors else "BLOCK",
        "errors": errors,
        "schema_profiles_verified": 3 if not errors else 0,
        "H01_cases_verified": 1 if not errors else 0,
        "non_null_owner_commitments_verified": 7 if not errors else 0,
        "all_null_optional_consumers_verified": 1 if not errors else 0,
        "trusted_owner_source_anchor_verified": not errors,
        "merged_R2_R3_R4_derivation_verified": not errors,
        "stable_ref_internal_space_positive_verified": not errors,
        "regression_probes": regression_count,
        "regression_failures": len(regression_failures),
        "parser_probes": parser_count,
        "parser_failures": len(parser_failures),
        "runtime_usable": False,
        "terminal_outcome": "NOT_EXECUTED",
        "fixture_canonical_sha256": hashlib.sha256(canonical_bytes(fixture)).hexdigest(),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
