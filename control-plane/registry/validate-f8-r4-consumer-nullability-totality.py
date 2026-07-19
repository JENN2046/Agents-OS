#!/usr/bin/env python3
"""Validate the deterministic synthetic F8 R4 consumer-totality witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


DOMAIN = "agents-os:f8-r4-consumer-nullability-totality:v0.1"
R2_H01_ROW_FINGERPRINT = "867b7f110b5ee7c34c314850f20ff488a8574c77164ded7d06736b6b3b085787"
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
ROOT_FIELDS = {
    "schema_version", "contract_id", "environment", "runtime_usable", "domain_tag",
    "schema_inventory", "consumer_shape_positive_cases", "mixed_null_negative_cases",
    "formation_all_null_cases", "canonical_candidate_history",
    "acknowledgement_all_null_cases", "inherited_R2_H01_compatibility_cases",
    "boundary_assertions", "section_fingerprints", "root_fingerprint",
}
BOUNDARY_FIELDS = {
    "runtime_usable_count", "real_Home_count", "real_Command_count", "task_write_count",
    "database_write_count", "provider_call_count", "production_authentication_count",
    "private_Memory_read_count", "sensing_or_recording_count", "external_effect_count",
    "terminal_outcome",
}
DECISION_FIELDS = {
    "result", "primary_reason", "reason_codes", "runtime_usable",
    "command_authority", "task_write_authority", "effect_authority",
}
FORMATION_FIELDS = {
    "case_id", "assessment_consumer", "minimum_trusted_event_sequence",
    "claimed_decision", "row_fingerprint",
}
CANDIDATE_FIELDS = {
    "candidate_ref", "candidate_revision", "runtime_usable",
    "command_authority", "candidate_fingerprint",
}
ACK_FIELDS = {"case_id", "raw_input", "claimed_decision", "row_fingerprint"}
ACK_RAW_FIELDS = {
    "handoff_candidate_ref", "handoff_candidate_revision",
    "handoff_candidate_fingerprint", "F3_outcome_consumer",
    "minimum_trusted_event_sequence",
}
COMPAT_FIELDS = {
    "source_case_id", "source_row_fingerprint", "source_result",
    "source_consumer_inventory_fingerprint", "upgraded_consumers",
    "downprojected_consumer_inventory_fingerprint", "claimed_result",
    "row_fingerprint",
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


def without(value: dict[str, Any], key: str) -> dict[str, Any]:
    return {name: item for name, item in value.items() if name != key}


def exact_fields(value: Any, expected: set[str] | list[str], path: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{path}: object required")
        return False
    expected_set = set(expected)
    actual = set(value)
    if actual != expected_set:
        errors.append(f"{path}: exact fields required missing={sorted(expected_set-actual)} extra={sorted(actual-expected_set)}")
        return False
    return True


def stable_ref(value: Any) -> bool:
    return type(value) is str and bool(value) and not any(ch.isspace() for ch in value)


def positive_int(value: Any) -> bool:
    return type(value) is int and 0 < value <= MAX_SAFE_INTEGER


def valid_hash(value: Any) -> bool:
    return type(value) is str and HASH_RE.fullmatch(value) is not None


def validate_json_value(value: Any, path: str, errors: list[str]) -> None:
    if value is None or type(value) in {bool, str}:
        return
    if type(value) is int:
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            errors.append(f"{path}: integer outside JSON safe range")
        return
    if type(value) is float:
        errors.append(f"{path}: float forbidden")
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
    if null_count == 6:
        return "ALL_NULL"
    if null_count != 0:
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
    return "ALL_NON_NULL" if not errors_for_path(errors, path) else None


def errors_for_path(errors: list[str], path: str) -> bool:
    return any(error.startswith(path + ".") or error.startswith(path + ":") for error in errors)


def resolve_consumer(value: dict[str, Any], lookup_counter: list[int]) -> dict[str, Any]:
    if all(value[field] is None for field in CONSUMER_FIELDS):
        return {
            "assessment": None,
            "resolution": "ASSESSMENT_CONSUMER_UNAVAILABLE",
            "owner_store_lookup_performed": False,
            "assessment_result_interpreted": False,
            "authority_created": False,
        }
    lookup_counter[0] += 1
    return {
        "assessment": "R3_OWNER_LOOKUP_REQUIRED",
        "resolution": "DEFER_TO_R3_EXACT_OWNER_RESOLUTION",
        "owner_store_lookup_performed": True,
        "assessment_result_interpreted": False,
        "authority_created": False,
    }


def unavailable_decision(*, acknowledgement: bool) -> dict[str, Any]:
    return {
        "result": "ACKNOWLEDGED_INDETERMINATE" if acknowledgement else "INDETERMINATE",
        "primary_reason": "ASSESSMENT_CONSUMER_UNAVAILABLE",
        "reason_codes": ["ASSESSMENT_CONSUMER_UNAVAILABLE"],
        "runtime_usable": False,
        "command_authority": False,
        "task_write_authority": False,
        "effect_authority": False,
    }


def validate_decision(value: Any, path: str, errors: list[str], *, acknowledgement: bool) -> bool:
    if not exact_fields(value, DECISION_FIELDS, path, errors):
        return False
    expected_result = "ACKNOWLEDGED_INDETERMINATE" if acknowledgement else "INDETERMINATE"
    if value["result"] != expected_result:
        errors.append(f"{path}.result: {expected_result} required")
    if value["primary_reason"] != "ASSESSMENT_CONSUMER_UNAVAILABLE":
        errors.append(f"{path}.primary_reason: unavailable reason required")
    if value["reason_codes"] != ["ASSESSMENT_CONSUMER_UNAVAILABLE"]:
        errors.append(f"{path}.reason_codes: exact unavailable list required")
    for key in ("runtime_usable", "command_authority", "task_write_authority", "effect_authority"):
        if value[key] is not False:
            errors.append(f"{path}.{key}: false required")
    return not errors_for_path(errors, path)


def derive_formation(case: dict[str, Any], lookup_counter: list[int]) -> dict[str, Any]:
    resolution = resolve_consumer(case["assessment_consumer"], lookup_counter)
    if resolution["resolution"] == "ASSESSMENT_CONSUMER_UNAVAILABLE":
        return unavailable_decision(acknowledgement=False)
    raise ValueError("R4 witness delegates non-null formation to unchanged R3 semantics")


def derive_ack(case: dict[str, Any], history: list[dict[str, Any]], lookup_counter: list[int]) -> dict[str, Any]:
    raw = case["raw_input"]
    found = [
        row for row in history
        if row["candidate_ref"] == raw["handoff_candidate_ref"]
        and row["candidate_revision"] == raw["handoff_candidate_revision"]
        and row["candidate_fingerprint"] == raw["handoff_candidate_fingerprint"]
    ]
    if len(found) != 1:
        return {
            **unavailable_decision(acknowledgement=True),
            "primary_reason": "HANDOFF_CANDIDATE_NOT_CURRENT",
            "reason_codes": ["HANDOFF_CANDIDATE_NOT_CURRENT"],
        }
    resolution = resolve_consumer(raw["F3_outcome_consumer"], lookup_counter)
    if resolution["resolution"] == "ASSESSMENT_CONSUMER_UNAVAILABLE":
        return unavailable_decision(acknowledgement=True)
    raise ValueError("R4 witness delegates non-null acknowledgement to unchanged R3 semantics")


def locate_R2_H01(r2_fixture: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in r2_fixture.get("handoff_cases", []) if row.get("case_id") == "H01"]
    if len(rows) != 1:
        raise ValueError("R2 fixture must contain exactly one H01")
    row = rows[0]
    if row.get("row_fingerprint") != R2_H01_ROW_FINGERPRINT:
        raise ValueError("R2 H01 fingerprint mismatch")
    return row


def validate_fixture(fixture: Any, r2_fixture: Any) -> list[str]:
    errors: list[str] = []
    validate_json_value(fixture, "fixture", errors)
    if not exact_fields(fixture, ROOT_FIELDS, "fixture", errors):
        return errors
    if fixture["schema_version"] != "agents-os.f8-r4-consumer-nullability-totality-witness.v0.1": errors.append("schema_version mismatch")
    if fixture["contract_id"] != "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R4": errors.append("contract_id mismatch")
    if fixture["environment"] != "SYNTHETIC_TEST" or fixture["runtime_usable"] is not False: errors.append("synthetic runtime boundary mismatch")
    if fixture["domain_tag"] != DOMAIN: errors.append("domain_tag mismatch")

    schemas = fixture["schema_inventory"]
    if type(schemas) is not list or len(schemas) != 3:
        errors.append("schema_inventory: expected three rows")
        schemas = []
    expected_schema_rows = [
        {
            "schema_id": "AssessmentConsumerV0_1R4",
            "fields": CONSUMER_FIELDS,
            "closed": True,
            "legal_shapes": ["ALL_NULL", "ALL_NON_NULL"],
        },
        {
            "schema_id": "ConsumerResolutionV0_1R4",
            "fields": ["assessment", "resolution", "owner_store_lookup_performed", "assessment_result_interpreted", "authority_created"],
            "closed": True,
        },
        {
            "schema_id": "InheritedR2H01CompatibilityV0_1R4",
            "fields": ["source_case_id", "source_row_fingerprint", "source_result", "source_consumer_inventory_fingerprint", "upgraded_consumers", "downprojected_consumer_inventory_fingerprint", "claimed_result"],
            "closed": True,
        },
    ]
    schema_ids = []
    for index, row in enumerate(schemas):
        path = f"schema_inventory[{index}]"
        if type(row) is not dict or not valid_hash(row.get("schema_fingerprint")):
            errors.append(f"{path}: invalid schema row")
            continue
        if index < len(expected_schema_rows) and without(row, "schema_fingerprint") != expected_schema_rows[index]:
            errors.append(f"{path}: canonical closed schema row mismatch")
        if row["schema_fingerprint"] != digest(DOMAIN + ":schema", without(row, "schema_fingerprint")):
            errors.append(f"{path}: schema fingerprint mismatch")
        schema_ids.append(row.get("schema_id"))
    if schema_ids != ["AssessmentConsumerV0_1R4", "ConsumerResolutionV0_1R4", "InheritedR2H01CompatibilityV0_1R4"]:
        errors.append("schema_inventory: canonical schema order mismatch")

    positives = fixture["consumer_shape_positive_cases"]
    if type(positives) is not list or len(positives) != 2:
        errors.append("consumer_shape_positive_cases: expected two rows")
        positives = []
    positive_shapes = []
    for index, row in enumerate(positives):
        path = f"consumer_shape_positive_cases[{index}]"
        if not exact_fields(row, {"case_id", "consumer", "expected_shape", "expected_valid", "row_fingerprint"}, path, errors): continue
        local: list[str] = []
        shape = validate_consumer(row["consumer"], path + ".consumer", local)
        if local: errors.extend(local)
        if shape != row["expected_shape"] or row["expected_valid"] is not True: errors.append(f"{path}: positive shape not independently derived")
        if row["row_fingerprint"] != digest(DOMAIN + ":consumer-shape", without(row, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")
        positive_shapes.append(shape)
    if positive_shapes != ["ALL_NULL", "ALL_NON_NULL"]: errors.append("positive consumer shapes: canonical order mismatch")

    mixed = fixture["mixed_null_negative_cases"]
    if type(mixed) is not list or len(mixed) != 62:
        errors.append("mixed_null_negative_cases: expected 62 rows")
        mixed = []
    seen_masks = []
    for index, row in enumerate(mixed):
        path = f"mixed_null_negative_cases[{index}]"
        if not exact_fields(row, {"case_id", "null_mask", "consumer", "expected_shape", "expected_valid", "row_fingerprint"}, path, errors): continue
        local: list[str] = []
        shape = validate_consumer(row["consumer"], path + ".consumer", local)
        if shape is not None or not any("MIXED_NULL_INVALID" in error for error in local): errors.append(f"{path}: mixed-null shape accepted")
        if row["expected_shape"] != "MIXED_NULL_INVALID" or row["expected_valid"] is not False: errors.append(f"{path}: mixed-null claim mismatch")
        if row["row_fingerprint"] != digest(DOMAIN + ":mixed-null", without(row, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")
        seen_masks.append(row["null_mask"])
    if seen_masks != list(range(1, 63)): errors.append("mixed-null inventory: canonical 1..62 masks required")

    formation = fixture["formation_all_null_cases"]
    lookup = [0]
    if type(formation) is not list or len(formation) != 1:
        errors.append("formation_all_null_cases: expected one row")
    else:
        row = formation[0]
        if exact_fields(row, FORMATION_FIELDS, "formation_all_null_cases[0]", errors):
            if not stable_ref(row["case_id"]) or not positive_int(row["minimum_trusted_event_sequence"]): errors.append("formation all-null id/watermark invalid")
            local: list[str] = []
            if validate_consumer(row["assessment_consumer"], "formation_all_null_cases[0].assessment_consumer", local) != "ALL_NULL": errors.append("formation all-null consumer invalid")
            errors.extend(local)
            validate_decision(row["claimed_decision"], "formation_all_null_cases[0].claimed_decision", errors, acknowledgement=False)
            if derive_formation(row, lookup) != row["claimed_decision"]: errors.append("formation all-null decision not independently derived")
            if row["row_fingerprint"] != digest(DOMAIN + ":formation", without(row, "row_fingerprint")): errors.append("formation row fingerprint mismatch")

    history = fixture["canonical_candidate_history"]
    if type(history) is not list or len(history) != 1:
        errors.append("canonical_candidate_history: expected one row")
        history = []
    else:
        row = history[0]
        if exact_fields(row, CANDIDATE_FIELDS, "canonical_candidate_history[0]", errors):
            if not stable_ref(row["candidate_ref"]) or not positive_int(row["candidate_revision"]): errors.append("candidate identity invalid")
            if row["candidate_fingerprint"] != digest(DOMAIN + ":candidate", without(row, "candidate_fingerprint")): errors.append("candidate fingerprint mismatch")
            if row["runtime_usable"] is not False or row["command_authority"] is not False: errors.append("candidate authority boundary mismatch")

    acknowledgements = fixture["acknowledgement_all_null_cases"]
    if type(acknowledgements) is not list or len(acknowledgements) != 1:
        errors.append("acknowledgement_all_null_cases: expected one row")
    elif history:
        row = acknowledgements[0]
        if exact_fields(row, ACK_FIELDS, "acknowledgement_all_null_cases[0]", errors):
            if not stable_ref(row["case_id"]): errors.append("acknowledgement case id invalid")
            raw = row["raw_input"]
            if exact_fields(raw, ACK_RAW_FIELDS, "acknowledgement_all_null_cases[0].raw_input", errors):
                if not stable_ref(raw["handoff_candidate_ref"]) or not positive_int(raw["handoff_candidate_revision"]) or not valid_hash(raw["handoff_candidate_fingerprint"]): errors.append("acknowledgement candidate tuple invalid")
                if not positive_int(raw["minimum_trusted_event_sequence"]): errors.append("acknowledgement minimum watermark invalid")
                local = []
                if validate_consumer(raw["F3_outcome_consumer"], "acknowledgement_all_null_cases[0].raw_input.F3_outcome_consumer", local) != "ALL_NULL": errors.append("acknowledgement all-null consumer invalid")
                errors.extend(local)
            validate_decision(row["claimed_decision"], "acknowledgement_all_null_cases[0].claimed_decision", errors, acknowledgement=True)
            if derive_ack(row, history, lookup) != row["claimed_decision"]: errors.append("acknowledgement all-null decision not independently derived")
            if row["row_fingerprint"] != digest(DOMAIN + ":acknowledgement", without(row, "row_fingerprint")): errors.append("acknowledgement row fingerprint mismatch")
    if lookup[0] != 0: errors.append("all-null resolution performed owner lookup")

    compat = fixture["inherited_R2_H01_compatibility_cases"]
    if type(compat) is not list or len(compat) != 1:
        errors.append("inherited_R2_H01_compatibility_cases: expected one row")
    else:
        row = compat[0]
        try:
            if not exact_fields(row, COMPAT_FIELDS, "inherited_R2_H01_compatibility_cases[0]", errors):
                raise ValueError("R2 H01 compatibility fields invalid")
            h01 = locate_R2_H01(r2_fixture)
            source = h01["raw_input"]["assessment_consumers"]
            if row["source_case_id"] != "H01" or row["source_row_fingerprint"] != h01["row_fingerprint"]: errors.append("R2 H01 source binding mismatch")
            if row["source_result"] != "CANDIDATE_FORMED" or row["claimed_result"] != "CANDIDATE_FORMED": errors.append("R2 H01 candidate result not preserved")
            source_fp = digest(DOMAIN + ":R2-H01-source-consumers", source)
            if row["source_consumer_inventory_fingerprint"] != source_fp: errors.append("R2 H01 source consumer fingerprint mismatch")
            upgraded = row["upgraded_consumers"]
            if type(upgraded) is not dict or set(upgraded) != set(source):
                errors.append("R2 H01 upgraded consumer inventory mismatch")
            else:
                down = {}
                for role in sorted(upgraded):
                    local = []
                    shape = validate_consumer(upgraded[role], f"R2_H01.upgraded_consumers.{role}", local)
                    errors.extend(local)
                    expected_shape = "ALL_NULL" if role == "jenn_exact_decision" else "ALL_NON_NULL"
                    if shape != expected_shape: errors.append(f"R2 H01 {role}: expected {expected_shape}")
                    down[role] = {key: upgraded[role][key] for key in CONSUMER_FIELDS[:3]}
                if down != source: errors.append("R2 H01 exact R2 consumer down-projection mismatch")
                down_fp = digest(DOMAIN + ":R2-H01-source-consumers", down)
                if row["downprojected_consumer_inventory_fingerprint"] != down_fp: errors.append("R2 H01 down-projection fingerprint mismatch")
            if row["row_fingerprint"] != digest(DOMAIN + ":R2-H01-compatibility", without(row, "row_fingerprint")): errors.append("R2 H01 compatibility row fingerprint mismatch")
        except Exception as exc:
            errors.append(f"R2 H01 compatibility stable BLOCK ({type(exc).__name__})")

    boundary = fixture["boundary_assertions"]
    if exact_fields(boundary, BOUNDARY_FIELDS, "boundary_assertions", errors):
        for key in BOUNDARY_FIELDS - {"terminal_outcome"}:
            if type(boundary[key]) is not int or boundary[key] != 0: errors.append(f"boundary_assertions.{key}: integer zero required")
        if boundary["terminal_outcome"] != "NOT_EXECUTED": errors.append("terminal_outcome must be NOT_EXECUTED")

    section_names = [
        "schema_inventory", "consumer_shape_positive_cases", "mixed_null_negative_cases",
        "formation_all_null_cases", "canonical_candidate_history",
        "acknowledgement_all_null_cases", "inherited_R2_H01_compatibility_cases",
        "boundary_assertions",
    ]
    expected_sections = {name: digest(DOMAIN + ":section:" + name, fixture[name]) for name in section_names}
    if type(fixture["section_fingerprints"]) is not dict or set(fixture["section_fingerprints"]) != set(section_names): errors.append("section fingerprint inventory fields mismatch")
    if fixture["section_fingerprints"] != expected_sections: errors.append("section fingerprint inventory mismatch")
    if fixture["root_fingerprint"] != digest(DOMAIN + ":root", without(fixture, "root_fingerprint")): errors.append("root fingerprint mismatch")
    return errors


def run_regressions(fixture: dict[str, Any], r2_fixture: dict[str, Any]) -> tuple[int, list[str]]:
    failures: list[str] = []
    base = fixture["consumer_shape_positive_cases"][1]["consumer"]
    null = fixture["consumer_shape_positive_cases"][0]["consumer"]
    probes: list[tuple[str, dict[str, Any], bool]] = []
    probes.append(("all-null", copy.deepcopy(null), True))
    probes.append(("all-non-null", copy.deepcopy(base), True))
    for index, field in enumerate(CONSUMER_FIELDS):
        one_null = copy.deepcopy(base); one_null[field] = None
        probes.append((f"single-null-{index}", one_null, False))
        one_non_null = copy.deepcopy(null); one_non_null[field] = base[field]
        probes.append((f"single-non-null-{index}", one_non_null, False))
    unknown = copy.deepcopy(null); unknown["unknown"] = None
    probes.append(("unknown-field", unknown, False))
    missing = copy.deepcopy(null); missing.pop(CONSUMER_FIELDS[-1])
    probes.append(("missing-field", missing, False))
    bool_revision = copy.deepcopy(base); bool_revision["expected_assessment_revision"] = True
    probes.append(("integer-as-boolean", bool_revision, False))
    bad_hash = copy.deepcopy(base); bad_hash["expected_assessment_fingerprint"] = "0" * 63
    probes.append(("bad-hash", bad_hash, False))
    for name, value, expected in probes:
        local: list[str] = []
        accepted = validate_consumer(value, name, local) in {"ALL_NULL", "ALL_NON_NULL"} and not local
        if accepted != expected:
            failures.append(name)
    lookup = [0]
    result = resolve_consumer(null, lookup)
    if lookup[0] != 0 or result["resolution"] != "ASSESSMENT_CONSUMER_UNAVAILABLE": failures.append("all-null-lookup")
    try:
        h01 = locate_R2_H01(r2_fixture)
        if h01["claimed_decision"]["result"] != "CANDIDATE_FORMED": failures.append("R2-H01-result")
    except Exception:
        failures.append("R2-H01-binding")
    return len(probes) + 2, failures


def parser_probes() -> tuple[int, list[str]]:
    failures: list[str] = []
    samples = {
        "duplicate-key": '{"a":1,"a":2}',
        "float": '{"a":1.5}',
        "NaN": '{"a":NaN}',
        "integer-as-boolean": json.dumps({"runtime_usable": 1}),
    }
    for name, text in samples.items():
        rejected = False
        try:
            value = json.loads(text, object_pairs_hook=strict_object, parse_constant=reject_constant)
            local: list[str] = []
            validate_json_value(value, "probe", local)
            if name == "integer-as-boolean":
                rejected = type(value.get("runtime_usable")) is not bool
            else:
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
        if b"\r" in data: errors.append(f"{name}: CR byte")
        if not data.endswith(b"\n"): errors.append(f"{name}: missing final LF")
        for index, line in enumerate(data.splitlines(), 1):
            if line.endswith((b" ", b"\t")): errors.append(f"{name}:{index}: trailing whitespace")
    print(json.dumps({"errors": errors, "files_checked": len(paths), "result": "PASS" if not errors else "BLOCK"}, sort_keys=True))
    return 0 if not errors else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", default="control-plane/registry/examples/2026-07-19-agents-os-f8-r4-consumer-nullability-totality-v0.1.json")
    parser.add_argument("--r2-fixture", default="control-plane/registry/examples/2026-07-19-agents-os-f8-r2-evidence-currentness-schema-closure-v0.1.json")
    parser.add_argument("--check-whitespace", nargs="+")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check_whitespace:
        return check_whitespace(args.check_whitespace)
    try:
        fixture = load_json(Path(args.fixture))
        r2_fixture = load_json(Path(args.r2_fixture))
        errors = validate_fixture(fixture, r2_fixture)
        regression_count, regression_failures = run_regressions(fixture, r2_fixture)
        parser_count, parser_failures = parser_probes()
    except Exception as exc:
        output = {"errors": [f"stable semantic BLOCK ({type(exc).__name__}): {exc}"], "result": "BLOCK"}
        print(json.dumps(output, sort_keys=True))
        return 1
    errors.extend(f"regression failed: {name}" for name in regression_failures)
    errors.extend(f"parser probe failed: {name}" for name in parser_failures)
    output = {
        "result": "PASS" if not errors else "BLOCK",
        "errors": errors,
        "schema_profiles_verified": 3,
        "consumer_shape_positive_cases": 2,
        "mixed_null_negative_cases": 62,
        "formation_all_null_cases": 1,
        "acknowledgement_all_null_cases": 1,
        "inherited_R2_H01_compatibility_cases": 1,
        "R4_regressions": f"{regression_count-len(regression_failures)}/{regression_count}_PASS",
        "parser_probes": f"{parser_count-len(parser_failures)}/{parser_count}_REJECTED",
        "owner_store_lookup_count_for_all_null": 0,
        "provider_call_count": 0,
        "external_effect_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
        "root_fingerprint": fixture.get("root_fingerprint"),
    }
    print(json.dumps(output, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
