#!/usr/bin/env python3
"""Offline validator for the Phase 5B M0-B Plan R1 synthetic witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


SAFE_MAX = 9_007_199_254_740_991
CASE_DOMAIN = "PHASE_5B_M0B_PLAN_R1_CASE_V1"
SECTION_DOMAIN = "PHASE_5B_M0B_PLAN_R1_SECTION_V1"
ROOT_DOMAIN = "PHASE_5B_M0B_PLAN_R1_ROOT_V1"

ROOT_FIELDS = {
    "schema_version", "profile", "case_catalog", "integrated_witness",
    "boundary_assertions", "section_fingerprints", "root_fingerprint",
}
PROFILE_FIELDS = {"environment", "domain_tag", "runtime_usable", "production_compatible"}
ROW_FIELDS = {"ordinal", "case_id", "raw_input", "derived_output", "row_fingerprint"}
RAW_FIELDS = {
    "source_kind", "branch_choice", "explicit_life_stream_choice",
    "life_stream_action", "explicit_memory_choice", "explicit_intent_choice",
    "request_f8_handoff", "f8_result", "f3_outcome",
    "direct_task_write_requested", "direct_command_commit_requested",
    "relationship_as_authority", "pbl_no_match_as_sufficient",
    "raw_content_persist_requested", "formal_memory_write_requested",
    "production_profile_requested", "upstream_current",
}
DERIVED_FIELDS = {
    "result", "reason_codes", "primary_reason", "life_stream_candidate_count",
    "memory_candidate_count", "intent_candidate_count", "handoff_candidate_count",
    "synthetic_f3_command_count", "command_owner", "goal_write_count",
    "task_write_count", "formal_memory_write_count", "home_command_write_count",
    "effect_count", "runtime_usable",
}
WITNESS_FIELDS = {
    "synthetic_session_observation_count", "branch_counts",
    "synthetic_life_stream_candidate_count", "synthetic_memory_candidate_count",
    "synthetic_intent_candidate_count", "synthetic_F8_handoff_candidate_count",
    "synthetic_F3_committed_command_count", "real_session_count", "real_Goal_count",
    "real_Task_count", "formal_memory_write_count", "real_Command_count",
    "provider_call_count", "network_call_count", "private_memory_read_count",
    "sensing_or_recording_count", "external_effect_count", "runtime_activation_count",
    "terminal_outcome",
}
BOUNDARY_FIELDS = {
    "Home_creates_permission", "Home_creates_identity_authority",
    "Home_writes_Goal_or_Task", "Home_commits_Command",
    "Memory_Candidate_is_formal_Memory", "relationship_expands_authority",
    "raw_Session_content_persisted", "private_Memory_read",
    "VCPToolBox_modified_or_started", "database_created", "runtime_activated",
    "provider_or_real_effect_executed", "implementation_authorized",
}
SECTION_FP_FIELDS = {"case_catalog", "integrated_witness", "boundary_assertions"}

SOURCE_KINDS = {"SESSION_CONTENT", "ORDINARY_THOUGHT", "RELATIONSHIP_MEMORY"}
BRANCH_CHOICES = {"NONE", "EPHEMERAL_ONLY", "DISCARD", "REMAIN_IN_SESSION", "PROPOSE_LIFE_STREAM_CANDIDATE"}
LIFE_ACTIONS = {"NONE", "OBSERVE", "DISCARD", "PROPOSE_MEMORY_CANDIDATE", "PROPOSE_INTENT_CANDIDATE"}
F8_RESULTS = {"NOT_EVALUATED", "CANDIDATE_FORMED", "REJECTED", "INDETERMINATE"}
F3_OUTCOMES = {"NOT_SUBMITTED", "SYNTHETIC_TEST_COMMITTED", "REJECTED", "INDETERMINATE"}
RESULTS = {
    "NO_PROMOTION", "INDETERMINATE", "REJECTED", "LIFE_STREAM_CANDIDATE_ONLY",
    "OBSERVED_NO_FURTHER_PROMOTION", "DISCARDED_NO_FURTHER_PROMOTION",
    "MEMORY_CANDIDATE_ONLY", "INTENT_CANDIDATE_ONLY", "HANDOFF_CANDIDATE_ONLY",
    "F3_COMMAND_ACKNOWLEDGED", "F3_REJECTION_ACKNOWLEDGED",
    "F3_INDETERMINATE_ACKNOWLEDGED",
}
REASON_PRECEDENCE = [
    "UNKNOWN_OR_MALFORMED_INPUT", "PRODUCTION_PROFILE_FORBIDDEN",
    "RAW_CONTENT_PERSISTENCE_FORBIDDEN", "FORMAL_MEMORY_WRITE_FORBIDDEN",
    "DIRECT_TASK_WRITE_FORBIDDEN", "DIRECT_COMMAND_COMMIT_FORBIDDEN",
    "RELATIONSHIP_CANNOT_EXPAND_AUTHORITY", "PBL_NO_MATCH_IS_NOT_PERMISSION",
    "UPSTREAM_CURRENTNESS_UNAVAILABLE", "ORDINARY_THOUGHT_CANNOT_PROMOTE",
    "EXPLICIT_SESSION_BRANCH_MISSING", "EXPLICIT_LIFE_STREAM_CHOICE_MISSING",
    "EXPLICIT_MEMORY_CHOICE_MISSING", "EXPLICIT_INTENT_CHOICE_MISSING",
    "F8_HANDOFF_REJECTED", "F8_HANDOFF_INDETERMINATE", "F3_NOT_SUBMITTED",
    "F3_REJECTED", "F3_INDETERMINATE", "VALID_NO_PROMOTION",
    "VALID_LIFE_STREAM_CANDIDATE", "VALID_OBSERVE", "VALID_DISCARD",
    "VALID_MEMORY_CANDIDATE", "VALID_INTENT_CANDIDATE", "VALID_HANDOFF_CANDIDATE",
    "VALID_F3_COMMIT_ACKNOWLEDGEMENT",
]


class ValidationError(ValueError):
    pass


def reject_float(value: str) -> None:
    raise ValidationError(f"float forbidden: {value}")


def reject_constant(value: str) -> None:
    raise ValidationError(f"non-finite number forbidden: {value}")


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=no_duplicates,
        parse_float=reject_float,
        parse_constant=reject_constant,
    )
    if type(value) is not dict:
        raise ValidationError("root must be object")
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def fingerprint(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + canonical_bytes(value)).hexdigest()


def closed(obj: Any, fields: set[str], label: str, errors: list[str]) -> None:
    if type(obj) is not dict:
        errors.append(f"{label}: expected object")
        return
    if set(obj) != fields:
        errors.append(f"{label}: fields mismatch missing={sorted(fields-set(obj))} extra={sorted(set(obj)-fields)}")


def scalar_walk(value: Any, path: str, errors: list[str]) -> None:
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value:
            errors.append(f"{path}: non-NFC string")
    elif type(value) is int:
        if value < 0 or value > SAFE_MAX:
            errors.append(f"{path}: unsafe integer")
    elif type(value) is float:
        errors.append(f"{path}: float forbidden")
    elif type(value) is list:
        for index, item in enumerate(value):
            scalar_walk(item, f"{path}[{index}]", errors)
    elif type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                errors.append(f"{path}: non-string key")
            scalar_walk(item, f"{path}.{key}", errors)
    elif value is not None and type(value) is not bool:
        errors.append(f"{path}: unsupported type {type(value).__name__}")


def is_hash(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(ch in "0123456789abcdef" for ch in value)


def base_input() -> dict[str, Any]:
    return {
        "source_kind": "SESSION_CONTENT", "branch_choice": "EPHEMERAL_ONLY",
        "explicit_life_stream_choice": False, "life_stream_action": "NONE",
        "explicit_memory_choice": False, "explicit_intent_choice": False,
        "request_f8_handoff": False, "f8_result": "NOT_EVALUATED",
        "f3_outcome": "NOT_SUBMITTED", "direct_task_write_requested": False,
        "direct_command_commit_requested": False, "relationship_as_authority": False,
        "pbl_no_match_as_sufficient": False, "raw_content_persist_requested": False,
        "formal_memory_write_requested": False, "production_profile_requested": False,
        "upstream_current": True,
    }


def raw(**overrides: Any) -> dict[str, Any]:
    value = base_input()
    value.update(overrides)
    return value


def expected_cases() -> list[tuple[str, dict[str, Any]]]:
    promote = {"branch_choice": "PROPOSE_LIFE_STREAM_CANDIDATE", "explicit_life_stream_choice": True}
    intent = {**promote, "life_stream_action": "PROPOSE_INTENT_CANDIDATE", "explicit_intent_choice": True}
    return [
        ("C01_EPHEMERAL_ONLY", raw(branch_choice="EPHEMERAL_ONLY")),
        ("C02_DISCARD", raw(branch_choice="DISCARD")),
        ("C03_REMAIN_IN_SESSION", raw(branch_choice="REMAIN_IN_SESSION")),
        ("C04_MISSING_BRANCH", raw(branch_choice="NONE")),
        ("C05_ORDINARY_THOUGHT_NO_PROMOTION", raw(source_kind="ORDINARY_THOUGHT", branch_choice="NONE")),
        ("C06_ORDINARY_THOUGHT_PROMOTION_REJECTED", raw(source_kind="ORDINARY_THOUGHT", **promote)),
        ("C07_IMPLICIT_LIFE_STREAM_REJECTED", raw(branch_choice="PROPOSE_LIFE_STREAM_CANDIDATE")),
        ("C08_LIFE_STREAM_CANDIDATE_ONLY", raw(**promote)),
        ("C09_OBSERVE_NO_FURTHER_PROMOTION", raw(**promote, life_stream_action="OBSERVE")),
        ("C10_DISCARD_NO_FURTHER_PROMOTION", raw(**promote, life_stream_action="DISCARD")),
        ("C11_MEMORY_CANDIDATE_ONLY", raw(**promote, life_stream_action="PROPOSE_MEMORY_CANDIDATE", explicit_memory_choice=True)),
        ("C12_IMPLICIT_MEMORY_PROMOTION_REJECTED", raw(**promote, life_stream_action="PROPOSE_MEMORY_CANDIDATE")),
        ("C13_INTENT_CANDIDATE_ONLY", raw(**intent)),
        ("C14_IMPLICIT_INTENT_PROMOTION_REJECTED", raw(**promote, life_stream_action="PROPOSE_INTENT_CANDIDATE")),
        ("C15_F8_HANDOFF_CANDIDATE_ONLY", raw(**intent, request_f8_handoff=True, f8_result="CANDIDATE_FORMED")),
        ("C16_F3_COMMITTED_ACKNOWLEDGED", raw(**intent, request_f8_handoff=True, f8_result="CANDIDATE_FORMED", f3_outcome="SYNTHETIC_TEST_COMMITTED")),
        ("C17_F3_REJECTED_ACKNOWLEDGED", raw(**intent, request_f8_handoff=True, f8_result="CANDIDATE_FORMED", f3_outcome="REJECTED")),
        ("C18_F3_INDETERMINATE_ACKNOWLEDGED", raw(**intent, request_f8_handoff=True, f8_result="CANDIDATE_FORMED", f3_outcome="INDETERMINATE")),
        ("C19_DIRECT_TASK_WRITE_REJECTED", raw(direct_task_write_requested=True)),
        ("C20_DIRECT_COMMAND_COMMIT_REJECTED", raw(direct_command_commit_requested=True)),
        ("C21_RELATIONSHIP_AUTHORITY_REJECTED", raw(source_kind="RELATIONSHIP_MEMORY", branch_choice="NONE", relationship_as_authority=True)),
        ("C22_PBL_NO_MATCH_PERMISSION_REJECTED", raw(pbl_no_match_as_sufficient=True)),
        ("C23_RAW_CONTENT_PERSIST_REJECTED", raw(raw_content_persist_requested=True)),
        ("C24_FORMAL_MEMORY_WRITE_REJECTED", raw(**promote, life_stream_action="PROPOSE_MEMORY_CANDIDATE", explicit_memory_choice=True, formal_memory_write_requested=True)),
        ("C25_PRODUCTION_PROFILE_REJECTED", raw(production_profile_requested=True)),
        ("C26_STALE_UPSTREAM_INDETERMINATE", raw(upstream_current=False)),
        ("C27_F8_REJECTED", raw(**intent, request_f8_handoff=True, f8_result="REJECTED")),
        ("C28_F8_INDETERMINATE", raw(**intent, request_f8_handoff=True, f8_result="INDETERMINATE")),
    ]


def make_output(result: str, reasons: list[str], life: int = 0, memory: int = 0, intent: int = 0, handoff: int = 0, f3: int = 0) -> dict[str, Any]:
    ordered = [reason for reason in REASON_PRECEDENCE if reason in set(reasons)]
    return {
        "result": result, "reason_codes": ordered, "primary_reason": ordered[0],
        "life_stream_candidate_count": life, "memory_candidate_count": memory,
        "intent_candidate_count": intent, "handoff_candidate_count": handoff,
        "synthetic_f3_command_count": f3, "command_owner": "F3" if f3 else None,
        "goal_write_count": 0, "task_write_count": 0, "formal_memory_write_count": 0,
        "home_command_write_count": 0, "effect_count": 0, "runtime_usable": False,
    }


def derive(value: dict[str, Any]) -> dict[str, Any]:
    structural = [
        ("production_profile_requested", "PRODUCTION_PROFILE_FORBIDDEN"),
        ("raw_content_persist_requested", "RAW_CONTENT_PERSISTENCE_FORBIDDEN"),
        ("formal_memory_write_requested", "FORMAL_MEMORY_WRITE_FORBIDDEN"),
        ("direct_task_write_requested", "DIRECT_TASK_WRITE_FORBIDDEN"),
        ("direct_command_commit_requested", "DIRECT_COMMAND_COMMIT_FORBIDDEN"),
        ("relationship_as_authority", "RELATIONSHIP_CANNOT_EXPAND_AUTHORITY"),
        ("pbl_no_match_as_sufficient", "PBL_NO_MATCH_IS_NOT_PERMISSION"),
    ]
    reasons = [reason for field, reason in structural if value[field]]
    if reasons:
        return make_output("REJECTED", reasons)
    if not value["upstream_current"]:
        return make_output("INDETERMINATE", ["UPSTREAM_CURRENTNESS_UNAVAILABLE"])
    if value["source_kind"] == "ORDINARY_THOUGHT":
        return make_output("NO_PROMOTION", ["VALID_NO_PROMOTION"]) if value["branch_choice"] == "NONE" else make_output("REJECTED", ["ORDINARY_THOUGHT_CANNOT_PROMOTE"])
    if value["source_kind"] == "RELATIONSHIP_MEMORY":
        return make_output("NO_PROMOTION", ["VALID_NO_PROMOTION"])
    if value["branch_choice"] == "NONE":
        return make_output("INDETERMINATE", ["EXPLICIT_SESSION_BRANCH_MISSING"])
    if value["branch_choice"] in {"EPHEMERAL_ONLY", "DISCARD", "REMAIN_IN_SESSION"}:
        return make_output("NO_PROMOTION", ["VALID_NO_PROMOTION"])
    if not value["explicit_life_stream_choice"]:
        return make_output("REJECTED", ["EXPLICIT_LIFE_STREAM_CHOICE_MISSING"])
    action = value["life_stream_action"]
    if action == "NONE": return make_output("LIFE_STREAM_CANDIDATE_ONLY", ["VALID_LIFE_STREAM_CANDIDATE"], life=1)
    if action == "OBSERVE": return make_output("OBSERVED_NO_FURTHER_PROMOTION", ["VALID_OBSERVE"], life=1)
    if action == "DISCARD": return make_output("DISCARDED_NO_FURTHER_PROMOTION", ["VALID_DISCARD"], life=1)
    if action == "PROPOSE_MEMORY_CANDIDATE":
        return make_output("MEMORY_CANDIDATE_ONLY", ["VALID_MEMORY_CANDIDATE"], life=1, memory=1) if value["explicit_memory_choice"] else make_output("REJECTED", ["EXPLICIT_MEMORY_CHOICE_MISSING"], life=1)
    if action != "PROPOSE_INTENT_CANDIDATE":
        return make_output("REJECTED", ["UNKNOWN_OR_MALFORMED_INPUT"])
    if not value["explicit_intent_choice"]:
        return make_output("REJECTED", ["EXPLICIT_INTENT_CHOICE_MISSING"], life=1)
    if not value["request_f8_handoff"]:
        return make_output("INTENT_CANDIDATE_ONLY", ["VALID_INTENT_CANDIDATE"], life=1, intent=1)
    if value["f8_result"] == "REJECTED":
        return make_output("REJECTED", ["F8_HANDOFF_REJECTED"], life=1, intent=1)
    if value["f8_result"] != "CANDIDATE_FORMED":
        return make_output("INDETERMINATE", ["F8_HANDOFF_INDETERMINATE"], life=1, intent=1)
    if value["f3_outcome"] == "NOT_SUBMITTED":
        return make_output("HANDOFF_CANDIDATE_ONLY", ["F3_NOT_SUBMITTED", "VALID_HANDOFF_CANDIDATE"], life=1, intent=1, handoff=1)
    if value["f3_outcome"] == "SYNTHETIC_TEST_COMMITTED":
        return make_output("F3_COMMAND_ACKNOWLEDGED", ["VALID_F3_COMMIT_ACKNOWLEDGEMENT"], life=1, intent=1, handoff=1, f3=1)
    if value["f3_outcome"] == "REJECTED":
        return make_output("F3_REJECTION_ACKNOWLEDGED", ["F3_REJECTED"], life=1, intent=1, handoff=1)
    return make_output("F3_INDETERMINATE_ACKNOWLEDGED", ["F3_INDETERMINATE"], life=1, intent=1, handoff=1)


def expected_witness() -> dict[str, Any]:
    return {
        "synthetic_session_observation_count": 4,
        "branch_counts": {"DISCARD": 1, "EPHEMERAL_ONLY": 1, "PROPOSE_LIFE_STREAM_CANDIDATE": 1, "REMAIN_IN_SESSION": 1},
        "synthetic_life_stream_candidate_count": 1, "synthetic_memory_candidate_count": 1,
        "synthetic_intent_candidate_count": 1, "synthetic_F8_handoff_candidate_count": 1,
        "synthetic_F3_committed_command_count": 1, "real_session_count": 0,
        "real_Goal_count": 0, "real_Task_count": 0, "formal_memory_write_count": 0,
        "real_Command_count": 0, "provider_call_count": 0, "network_call_count": 0,
        "private_memory_read_count": 0, "sensing_or_recording_count": 0,
        "external_effect_count": 0, "runtime_activation_count": 0,
        "terminal_outcome": "NOT_ACTIVATED",
    }


def expected_boundaries() -> dict[str, bool]:
    return {key: False for key in BOUNDARY_FIELDS}


def validate(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    scalar_walk(value, "$", errors)
    closed(value, ROOT_FIELDS, "root", errors)
    if set(value) != ROOT_FIELDS:
        return errors
    if value["schema_version"] != "agents-os.m0b-plan-r1-synthetic-witness.v0.1":
        errors.append("root: schema_version")
    closed(value["profile"], PROFILE_FIELDS, "profile", errors)
    if value["profile"] != {"environment": "SYNTHETIC_TEST", "domain_tag": "PHASE_5B_M0B_PLAN_R1_SYNTHETIC_NONAUTHORITY", "runtime_usable": False, "production_compatible": False}:
        errors.append("profile: exact synthetic profile mismatch")
    if type(value["case_catalog"]) is not list:
        errors.append("case_catalog: expected list")
        return errors
    specs = expected_cases()
    if len(value["case_catalog"]) != len(specs):
        errors.append("case_catalog: count mismatch")
    for index, row in enumerate(value["case_catalog"]):
        label = f"case_catalog[{index}]"
        closed(row, ROW_FIELDS, label, errors)
        if type(row) is not dict or set(row) != ROW_FIELDS:
            continue
        if type(row["ordinal"]) is not int or type(row["ordinal"]) is bool or row["ordinal"] != index + 1:
            errors.append(f"{label}: ordinal")
        closed(row["raw_input"], RAW_FIELDS, f"{label}.raw_input", errors)
        closed(row["derived_output"], DERIVED_FIELDS, f"{label}.derived_output", errors)
        if index < len(specs):
            expected_id, expected_raw = specs[index]
            if row["case_id"] != expected_id:
                errors.append(f"{label}: case_id inventory")
            if row["raw_input"] != expected_raw:
                errors.append(f"{label}: raw_input inventory")
        raw_value = row["raw_input"]
        if type(raw_value) is dict and set(raw_value) == RAW_FIELDS:
            for field in RAW_FIELDS - {"source_kind", "branch_choice", "life_stream_action", "f8_result", "f3_outcome"}:
                if type(raw_value[field]) is not bool:
                    errors.append(f"{label}.raw_input.{field}: strict boolean")
            for field, allowed in [("source_kind", SOURCE_KINDS), ("branch_choice", BRANCH_CHOICES), ("life_stream_action", LIFE_ACTIONS), ("f8_result", F8_RESULTS), ("f3_outcome", F3_OUTCOMES)]:
                if raw_value[field] not in allowed:
                    errors.append(f"{label}.raw_input.{field}: enum")
            try:
                independently_derived = derive(raw_value)
                if row["derived_output"] != independently_derived:
                    errors.append(f"{label}: derived_output mismatch")
            except Exception as exc:
                errors.append(f"{label}: derivation exception {type(exc).__name__}")
        derived = row["derived_output"]
        if type(derived) is dict and set(derived) == DERIVED_FIELDS:
            if derived["result"] not in RESULTS:
                errors.append(f"{label}.derived_output: result enum")
            if type(derived["runtime_usable"]) is not bool or derived["runtime_usable"]:
                errors.append(f"{label}.derived_output: runtime_usable")
            for count_field in DERIVED_FIELDS - {"result", "reason_codes", "primary_reason", "command_owner", "runtime_usable"}:
                if type(derived[count_field]) is not int or type(derived[count_field]) is bool or derived[count_field] < 0:
                    errors.append(f"{label}.derived_output.{count_field}: nonnegative integer")
        if not is_hash(row["row_fingerprint"]):
            errors.append(f"{label}: row_fingerprint format")
        else:
            body = {key: row[key] for key in ROW_FIELDS - {"row_fingerprint"}}
            if row["row_fingerprint"] != fingerprint(CASE_DOMAIN, body):
                errors.append(f"{label}: row_fingerprint mismatch")
    closed(value["integrated_witness"], WITNESS_FIELDS, "integrated_witness", errors)
    if value["integrated_witness"] != expected_witness():
        errors.append("integrated_witness: exact mismatch")
    closed(value["boundary_assertions"], BOUNDARY_FIELDS, "boundary_assertions", errors)
    if value["boundary_assertions"] != expected_boundaries():
        errors.append("boundary_assertions: exact all-false mismatch")
    closed(value["section_fingerprints"], SECTION_FP_FIELDS, "section_fingerprints", errors)
    if type(value["section_fingerprints"]) is dict and set(value["section_fingerprints"]) == SECTION_FP_FIELDS:
        expected_sections = {
            "case_catalog": fingerprint(SECTION_DOMAIN + ":case_catalog", value["case_catalog"]),
            "integrated_witness": fingerprint(SECTION_DOMAIN + ":integrated_witness", value["integrated_witness"]),
            "boundary_assertions": fingerprint(SECTION_DOMAIN + ":boundary_assertions", value["boundary_assertions"]),
        }
        if value["section_fingerprints"] != expected_sections:
            errors.append("section_fingerprints: mismatch")
    if not is_hash(value["root_fingerprint"]):
        errors.append("root_fingerprint: format")
    else:
        root_body = {key: value[key] for key in ROOT_FIELDS - {"root_fingerprint"}}
        if value["root_fingerprint"] != fingerprint(ROOT_DOMAIN, root_body):
            errors.append("root_fingerprint: mismatch")
    return errors


def resign(value: dict[str, Any]) -> None:
    for row in value.get("case_catalog", []):
        if type(row) is dict and "row_fingerprint" in row:
            body = {key: item for key, item in row.items() if key != "row_fingerprint"}
            row["row_fingerprint"] = fingerprint(CASE_DOMAIN, body)
    if all(key in value for key in ("case_catalog", "integrated_witness", "boundary_assertions")):
        value["section_fingerprints"] = {
            "case_catalog": fingerprint(SECTION_DOMAIN + ":case_catalog", value["case_catalog"]),
            "integrated_witness": fingerprint(SECTION_DOMAIN + ":integrated_witness", value["integrated_witness"]),
            "boundary_assertions": fingerprint(SECTION_DOMAIN + ":boundary_assertions", value["boundary_assertions"]),
        }
    if "root_fingerprint" in value:
        value["root_fingerprint"] = fingerprint(ROOT_DOMAIN, {key: item for key, item in value.items() if key != "root_fingerprint"})


def self_test_mutations(baseline: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    mutations: list[tuple[str, dict[str, Any]]] = []
    def add(name: str, mutate: Any) -> None:
        value = copy.deepcopy(baseline)
        mutate(value)
        resign(value)
        mutations.append((name, value))
    add("unknown_root", lambda v: v.update({"implementation_frozen": True}))
    add("unknown_raw_field", lambda v: v["case_catalog"][0]["raw_input"].update({"raw_text": "x"}))
    add("missing_raw_field", lambda v: v["case_catalog"][0]["raw_input"].pop("upstream_current"))
    add("bool_as_integer", lambda v: v["case_catalog"][0]["raw_input"].update({"upstream_current": 1}))
    add("unsafe_ordinal", lambda v: v["case_catalog"][0].update({"ordinal": SAFE_MAX + 1}))
    add("non_NFC_case_id", lambda v: v["case_catalog"][0].update({"case_id": "Cafe\u0301"}))
    add("unknown_branch", lambda v: v["case_catalog"][0]["raw_input"].update({"branch_choice": "AUTO"}))
    add("replace_required_case", lambda v: v["case_catalog"][18].update({"raw_input": copy.deepcopy(v["case_catalog"][0]["raw_input"]), "derived_output": copy.deepcopy(v["case_catalog"][0]["derived_output"])}))
    add("rename_case", lambda v: v["case_catalog"][0].update({"case_id": "C99"}))
    add("swap_cases", lambda v: v["case_catalog"].__setitem__(slice(0, 2), [v["case_catalog"][1], v["case_catalog"][0]]))
    add("duplicate_case", lambda v: v["case_catalog"].append(copy.deepcopy(v["case_catalog"][0])))
    add("remove_case", lambda v: v["case_catalog"].pop())
    add("forged_favorable_result", lambda v: v["case_catalog"][18]["derived_output"].update({"result": "NO_PROMOTION"}))
    add("task_write_count", lambda v: v["case_catalog"][0]["derived_output"].update({"task_write_count": 1}))
    add("Home_command_owner", lambda v: v["case_catalog"][15]["derived_output"].update({"command_owner": "HOME"}))
    add("runtime_usable", lambda v: v["case_catalog"][0]["derived_output"].update({"runtime_usable": True}))
    add("permission_boundary_true", lambda v: v["boundary_assertions"].update({"Home_creates_permission": True}))
    add("unknown_boundary", lambda v: v["boundary_assertions"].update({"second_writer": False}))
    add("real_session", lambda v: v["integrated_witness"].update({"real_session_count": 1}))
    add("formal_memory_write", lambda v: v["integrated_witness"].update({"formal_memory_write_count": 1}))
    add("provider_call", lambda v: v["integrated_witness"].update({"provider_call_count": 1}))
    add("raw_content_favorable", lambda v: v["case_catalog"][0]["raw_input"].update({"raw_content_persist_requested": True}))
    add("production_favorable", lambda v: v["case_catalog"][0]["raw_input"].update({"production_profile_requested": True}))
    add("relationship_favorable", lambda v: v["case_catalog"][0]["raw_input"].update({"relationship_as_authority": True}))
    add("direct_command_favorable", lambda v: v["case_catalog"][0]["raw_input"].update({"direct_command_commit_requested": True}))
    add("pbl_favorable", lambda v: v["case_catalog"][0]["raw_input"].update({"pbl_no_match_as_sufficient": True}))
    add("F3_commit_without_handoff", lambda v: v["case_catalog"][14]["raw_input"].update({"f3_outcome": "SYNTHETIC_TEST_COMMITTED", "f8_result": "NOT_EVALUATED"}))
    add("witness_branch_count", lambda v: v["integrated_witness"]["branch_counts"].update({"EPHEMERAL_ONLY": 2}))
    add("profile_production_compatible", lambda v: v["profile"].update({"production_compatible": True}))
    add("profile_runtime_usable", lambda v: v["profile"].update({"runtime_usable": True}))
    return mutations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        value = load_strict(args.fixture)
        errors = validate(value)
        if errors:
            print("BLOCK")
            for error in errors:
                print(f"- {error}")
            return 1
        rejected = 0
        if args.self_test:
            for name, mutation in self_test_mutations(value):
                mutation_errors = validate(mutation)
                if not mutation_errors:
                    print(f"BLOCK mutation accepted: {name}")
                    return 1
                rejected += 1
        print("PASS")
        print(f"case_count={len(value['case_catalog'])}")
        print(f"row_fingerprints_verified={len(value['case_catalog'])}")
        print("section_fingerprints_verified=3")
        print(f"fully_resigned_mutations_rejected={rejected}/{len(self_test_mutations(value)) if args.self_test else 0}")
        print(f"root_fingerprint={value['root_fingerprint']}")
        print("terminal_outcome=NOT_ACTIVATED")
        return 0
    except Exception as exc:
        print(f"BLOCK malformed input: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
