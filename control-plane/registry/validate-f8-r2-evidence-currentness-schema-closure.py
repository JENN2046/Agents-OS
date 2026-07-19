#!/usr/bin/env python3
"""Offline validator for the F8 R2 evidence-currentness closure witness."""

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


DEFAULT_FIXTURE = Path(
    "control-plane/registry/examples/"
    "2026-07-19-agents-os-f8-r2-evidence-currentness-schema-closure-v0.1.json"
)
DOMAIN = "F8_R2_SYNTHETIC_NONAUTHORITY"
F3_MANIFEST_SHA256 = "3075cda63fcb2c7937cb800a3bc09cc830d17e2f98b899828db15e09ab9f79ff"
MAX_SAFE_INTEGER = 9007199254740991
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

CONSUMER_ROLES = [
    "f7_intent_currentness", "actor_identity", "principal_binding", "responsibility",
    "f3_readiness", "pbl_currentness", "jenn_requirement", "jenn_exact_decision",
]
REASON_PRECEDENCE = [
    "UNKNOWN_OR_MALFORMED_INPUT", "SYNTHETIC_DOMAIN_VIOLATION",
    "EXPLICIT_ACTION_CHOICE_MISSING", "DIRECT_TASK_WRITE_FORBIDDEN",
    "DIRECT_COMMAND_COMMIT_FORBIDDEN", "EFFECT_EXECUTION_FORBIDDEN",
    "RELATIONSHIP_OR_TRUST_CANNOT_EXPAND_AUTHORITY", "PBL_NO_MATCH_IS_NOT_PERMISSION",
    "INTENT_SEMANTIC_CLASS_MISMATCH", "TARGET_KIND_OUTSIDE_F8",
    "CONTEXT_FINGERPRINT_MISMATCH", "ASSESSMENT_MISSING_OR_UNRESOLVABLE",
    "ASSESSMENT_REVISION_MISMATCH", "ASSESSMENT_FINGERPRINT_MISMATCH",
    "ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH",
    "ASSESSMENT_WATERMARK_BEHIND", "UPSTREAM_ASSESSMENT_NOT_CURRENT",
    "UPSTREAM_CURRENTNESS_UNAVAILABLE",
    "F7_INTENT_NOT_CURRENT", "ACTOR_IDENTITY_NOT_ACTIVE",
    "PRINCIPAL_BINDING_NOT_ACTIVE", "RESPONSIBILITY_NOT_ACTIVE", "F3_NOT_READY",
    "PBL_PROHIBITED", "EXACT_JENN_DECISION_MISSING_OR_INVALID",
    "F3_INTERFACE_REQUIREMENT_UNACCEPTED", "VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE",
]

SCHEMA_PROFILES = {
    "UpstreamOwnerAssessmentV0_1": [
        "assessment_id", "assessment_revision", "owner_contract", "assessment_kind",
        "subject_ref", "subject_revision", "subject_fingerprint", "context_fingerprint",
        "result", "based_on_event_sequence", "is_current_head", "row_fingerprint",
    ],
    "AssessmentConsumerV0_1R2": [
        "assessment_id", "expected_assessment_revision", "expected_assessment_fingerprint",
    ],
    "HomeIntentHandoffRawInputV0_1R2": [
        "environment", "intent_candidate_ref", "intent_candidate_revision",
        "intent_candidate_fingerprint", "intent_semantic_class", "creator_actor_ref",
        "creator_actor_revision", "creator_actor_fingerprint", "principal_ref",
        "principal_revision", "principal_fingerprint", "target_kind", "target_ref",
        "target_revision", "target_fingerprint", "payload_schema_ref",
        "payload_schema_fingerprint", "payload_commitment", "explicit_action_choice",
        "direct_task_write_requested", "direct_command_commit_requested",
        "effect_execution_requested", "relationship_or_trust_used_as_authority",
        "pbl_no_match_used_as_sufficient", "production_profile_requested",
        "runtime_usable_requested", "trusted_event_sequence", "context_fingerprint",
        "assessment_consumers",
    ],
    "HomeIntentHandoffDecisionV0_1R2": [
        "result", "reason_codes", "primary_reason", "command_authority",
        "task_write_authority", "effect_authority", "runtime_usable",
        "F3_recheck_required", "F3_command_ref", "F3_intake_ref",
    ],
    "HomeIntentHandoffDecisionCaseV0_1R2": [
        "case_id", "raw_input", "claimed_decision", "row_fingerprint",
    ],
    "HomeIntentHandoffCandidateRevisionV0_1R2": [
        "handoff_candidate_id", "handoff_candidate_revision", "predecessor_ref",
        "predecessor_fingerprint", "intent_candidate_ref", "intent_candidate_revision",
        "intent_candidate_fingerprint", "target_ref", "target_revision",
        "target_fingerprint", "payload_commitment", "context_fingerprint",
        "assessment_set_fingerprint", "created_event_ref", "created_event_fingerprint",
        "runtime_usable", "command_authority", "candidate_fingerprint",
    ],
    "ProspectiveF3HomeIntentInterfaceRequirementV0_1R2": [
        "requirement_id", "owner", "status", "usable_in_runtime",
        "synthetic_fixture_only", "required_F3_contract", "required_submission_interface",
        "required_intake_results", "F8_may_mint_command", "F8_may_mint_authentication",
        "F8_may_commit_intake", "row_fingerprint",
    ],
    "HomeIntentHandoffAcknowledgementRawInputV0_1R2": [
        "handoff_candidate_ref", "handoff_candidate_revision",
        "handoff_candidate_fingerprint", "trusted_event_sequence",
        "F3_outcome_assessment_id", "expected_assessment_revision",
        "expected_assessment_fingerprint",
    ],
    "HomeIntentHandoffAcknowledgementDecisionV0_1R2": [
        "result", "reason_codes", "primary_reason", "command_authority",
        "task_write_authority", "effect_authority", "runtime_usable",
    ],
    "BoundaryAssertionsV0_1R2": [
        "real_home_fact_count", "real_task_count", "real_command_count",
        "private_raw_memory_count", "runtime_activation_count", "database_write_count",
        "provider_call_count", "sensing_or_recording_count", "external_effect_count",
        "terminal_outcome",
    ],
}

ROOT_FIELDS = {
    "schema_version", "contract_id", "environment", "domain_tag", "runtime_usable",
    "schema_inventory", "prospective_f3_interface_requirement", "upstream_assessments",
    "handoff_cases", "handoff_candidate_history", "acknowledgement_cases",
    "boundary_assertions", "section_fingerprints", "root_fingerprint",
}
SCHEMA_ROW_FIELDS = {"schema_name", "exact_fields", "unknown_fields_policy", "row_fingerprint"}
ASSESSMENT_FIELDS = set(SCHEMA_PROFILES["UpstreamOwnerAssessmentV0_1"])
CONSUMER_FIELDS = set(SCHEMA_PROFILES["AssessmentConsumerV0_1R2"])
RAW_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffRawInputV0_1R2"])
DECISION_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffDecisionV0_1R2"])
CASE_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffDecisionCaseV0_1R2"])
CANDIDATE_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffCandidateRevisionV0_1R2"])
PROSPECTIVE_FIELDS = set(SCHEMA_PROFILES["ProspectiveF3HomeIntentInterfaceRequirementV0_1R2"])
ACK_RAW_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffAcknowledgementRawInputV0_1R2"])
ACK_DECISION_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffAcknowledgementDecisionV0_1R2"])
ACK_CASE_FIELDS = {"case_id", "raw_input", "claimed_decision", "row_fingerprint"}
BOUNDARY_FIELDS = set(SCHEMA_PROFILES["BoundaryAssertionsV0_1R2"])
SECTION_NAMES = [
    "schema_inventory", "prospective_f3_interface_requirement", "upstream_assessments",
    "handoff_cases", "handoff_candidate_history", "acknowledgement_cases",
    "boundary_assertions",
]

KIND_PROFILE = {
    "F7_INTENT_CURRENTNESS": ("F7", {"CURRENT_ACCEPTED", "STALE", "INDETERMINATE"}),
    "F2_ACTOR_IDENTITY": ("F2", {"ACTIVE", "INACTIVE", "INDETERMINATE"}),
    "F2_PRINCIPAL_BINDING": ("F2", {"ACTIVE", "INACTIVE", "INDETERMINATE"}),
    "F2_RESPONSIBILITY": ("F2", {"ACTIVE", "INACTIVE", "INDETERMINATE"}),
    "F3_RESIDENT_READINESS": ("F3", {"READY_CONTINUOUS", "NOT_READY", "INDETERMINATE"}),
    "PBL_CURRENTNESS": ("POLICY", {"CURRENT_NO_MATCH", "PROHIBITED", "INDETERMINATE"}),
    "JENN_REQUIREMENT": ("POLICY", {"NO_EXACT_DECISION_REQUIRED", "EXACT_DECISION_REQUIRED", "INDETERMINATE"}),
    "JENN_EXACT_DECISION": ("JENN_DECISION", {"CURRENT_ACCEPTED", "REJECTED", "INDETERMINATE"}),
    "F3_INTAKE_OUTCOME": ("F3", {"SYNTHETIC_TEST_COMMITTED", "REJECTED", "NOT_SUBMITTED", "INDETERMINATE"}),
}

SECTION_ANCHORS = {
    "upstream_assessments": "fa86c26780de3bbe29d120829ca345696b8e62960d3dc4683d733f8046fb8412",
    "handoff_cases": "ca071fc3ba9c6d86094b701518480a787e38b0b6e4a0dd14360052e93c478614",
    "handoff_candidate_history": "ebad15f90b3d977b5905450894af79985e279e7dc1e5f6ff54b5d7d267f80056",
    "acknowledgement_cases": "4652a75166d39221c12390415e699a715e5fef7a0250873b8f33632607172ad2",
}

class DuplicateKeyError(ValueError):
    pass


def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON number forbidden: {value}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def plain_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def without(row: dict[str, Any], field: str) -> dict[str, Any]:
    value = copy.deepcopy(row)
    value.pop(field, None)
    return value


def exact_fields(value: Any, fields: set[str], path: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{path}: expected object")
        return False
    actual = set(value)
    if actual != fields:
        errors.append(f"{path}: fields mismatch missing={sorted(fields-actual)} extra={sorted(actual-fields)}")
        return False
    return True


def valid_hash(value: Any) -> bool:
    return type(value) is str and SHA256_RE.fullmatch(value) is not None


def positive_int(value: Any) -> bool:
    return type(value) is int and 1 <= value <= MAX_SAFE_INTEGER


def non_negative_int(value: Any) -> bool:
    return type(value) is int and 0 <= value <= MAX_SAFE_INTEGER


def stable_ref(value: Any) -> bool:
    return (
        type(value) is str
        and bool(value)
        and unicodedata.normalize("NFC", value) == value
        and not value.isspace()
    )


def closed_string_list(value: Any, allowed: set[str], *, nonempty: bool = True) -> bool:
    return (
        type(value) is list
        and (bool(value) or not nonempty)
        and all(type(item) is str and item in allowed for item in value)
        and len(value) == len(set(value))
    )


def validate_json_value(value: Any, path: str, errors: list[str]) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value < 0 or value > MAX_SAFE_INTEGER:
            errors.append(f"{path}: integer outside safe range")
        return
    if type(value) is float:
        errors.append(f"{path}: floats are forbidden")
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
    errors.append(f"{path}: unsupported type {type(value).__name__}")


def context_fingerprint(raw: dict[str, Any]) -> str:
    keys = [
        "intent_candidate_ref", "intent_candidate_revision", "intent_candidate_fingerprint",
        "intent_semantic_class", "creator_actor_ref", "creator_actor_revision",
        "creator_actor_fingerprint", "principal_ref", "principal_revision",
        "principal_fingerprint", "target_kind", "target_ref", "target_revision",
        "target_fingerprint", "payload_schema_ref", "payload_schema_fingerprint",
        "payload_commitment", "explicit_action_choice", "trusted_event_sequence",
    ]
    return digest(DOMAIN + ":handoff-context", {key: raw[key] for key in keys})


def acknowledgement_context_fingerprint(
    candidate_ref: str, candidate_revision: int, candidate_fingerprint: str
) -> str:
    return digest(
        DOMAIN + ":f3-outcome-context",
        {
            "handoff_candidate_ref": candidate_ref,
            "handoff_candidate_revision": candidate_revision,
            "handoff_candidate_fingerprint": candidate_fingerprint,
        },
    )


def assessment_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["assessment_id"]: row for row in rows if type(row) is dict and type(row.get("assessment_id")) is str}


def derive_case(raw: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: set[str] = set()
    index = assessment_index(rows)
    if raw["environment"] != "SYNTHETIC_TEST" or raw["runtime_usable_requested"]:
        reasons.add("SYNTHETIC_DOMAIN_VIOLATION")
    if raw["explicit_action_choice"] is not True:
        reasons.add("EXPLICIT_ACTION_CHOICE_MISSING")
    flag_reasons = {
        "direct_task_write_requested": "DIRECT_TASK_WRITE_FORBIDDEN",
        "direct_command_commit_requested": "DIRECT_COMMAND_COMMIT_FORBIDDEN",
        "effect_execution_requested": "EFFECT_EXECUTION_FORBIDDEN",
        "relationship_or_trust_used_as_authority": "RELATIONSHIP_OR_TRUST_CANNOT_EXPAND_AUTHORITY",
        "pbl_no_match_used_as_sufficient": "PBL_NO_MATCH_IS_NOT_PERMISSION",
    }
    for key, reason in flag_reasons.items():
        if raw[key]:
            reasons.add(reason)
    if raw["intent_semantic_class"] != "INTENT_CANDIDATE":
        reasons.add("INTENT_SEMANTIC_CLASS_MISMATCH")
    if raw["target_kind"] != "ORCHESTRATOR_INTAKE_CANDIDATE":
        reasons.add("TARGET_KIND_OUTSIDE_F8")
    if raw["context_fingerprint"] != context_fingerprint(raw):
        reasons.add("CONTEXT_FINGERPRINT_MISMATCH")

    resolved: dict[str, dict[str, Any] | None] = {}
    for role in CONSUMER_ROLES:
        binding = raw["assessment_consumers"][role]
        aid = binding["assessment_id"]
        if aid is None:
            resolved[role] = None
            if role != "jenn_exact_decision":
                reasons.add("ASSESSMENT_MISSING_OR_UNRESOLVABLE")
            continue
        row = index.get(aid)
        resolved[role] = row
        if row is None:
            reasons.add("ASSESSMENT_MISSING_OR_UNRESOLVABLE")
            continue
        if binding["expected_assessment_revision"] != row["assessment_revision"]:
            reasons.add("ASSESSMENT_REVISION_MISMATCH")
        if binding["expected_assessment_fingerprint"] != row["row_fingerprint"]:
            reasons.add("ASSESSMENT_FINGERPRINT_MISMATCH")
        if row["based_on_event_sequence"] < raw["trusted_event_sequence"]:
            reasons.add("ASSESSMENT_WATERMARK_BEHIND")
        if not row["is_current_head"]:
            reasons.add("UPSTREAM_ASSESSMENT_NOT_CURRENT")
        if row["result"] == "INDETERMINATE":
            reasons.add("UPSTREAM_CURRENTNESS_UNAVAILABLE")

    exact_subjects = {
        "f7_intent_currentness": (raw["intent_candidate_ref"], raw["intent_candidate_revision"], raw["intent_candidate_fingerprint"], None),
        "actor_identity": (raw["creator_actor_ref"], raw["creator_actor_revision"], raw["creator_actor_fingerprint"], None),
        "principal_binding": (raw["principal_ref"], raw["principal_revision"], raw["principal_fingerprint"], None),
        "responsibility": (raw["target_ref"], raw["target_revision"], raw["target_fingerprint"], raw["context_fingerprint"]),
        "f3_readiness": ("F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE", 4, F3_MANIFEST_SHA256, None),
        "pbl_currentness": ("agents-os.prohibited-behavior-list.current", 1, digest(DOMAIN + ":pbl", {"revision": 1}), None),
        "jenn_requirement": (raw["target_ref"], raw["target_revision"], raw["target_fingerprint"], raw["context_fingerprint"]),
        "jenn_exact_decision": (raw["target_ref"], raw["target_revision"], raw["target_fingerprint"], raw["context_fingerprint"]),
    }
    kinds = {
        "f7_intent_currentness": ("F7", "F7_INTENT_CURRENTNESS"),
        "actor_identity": ("F2", "F2_ACTOR_IDENTITY"),
        "principal_binding": ("F2", "F2_PRINCIPAL_BINDING"),
        "responsibility": ("F2", "F2_RESPONSIBILITY"),
        "f3_readiness": ("F3", "F3_RESIDENT_READINESS"),
        "pbl_currentness": ("POLICY", "PBL_CURRENTNESS"),
        "jenn_requirement": ("POLICY", "JENN_REQUIREMENT"),
        "jenn_exact_decision": ("JENN_DECISION", "JENN_EXACT_DECISION"),
    }
    for role in CONSUMER_ROLES:
        row = resolved.get(role)
        if row is None:
            continue
        actual = (row["subject_ref"], row["subject_revision"], row["subject_fingerprint"], row["context_fingerprint"])
        if actual != exact_subjects[role] or (row["owner_contract"], row["assessment_kind"]) != kinds[role]:
            reasons.add("ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH")

    checks = {
        "f7_intent_currentness": ("CURRENT_ACCEPTED", "F7_INTENT_NOT_CURRENT"),
        "actor_identity": ("ACTIVE", "ACTOR_IDENTITY_NOT_ACTIVE"),
        "principal_binding": ("ACTIVE", "PRINCIPAL_BINDING_NOT_ACTIVE"),
        "responsibility": ("ACTIVE", "RESPONSIBILITY_NOT_ACTIVE"),
        "f3_readiness": ("READY_CONTINUOUS", "F3_NOT_READY"),
        "pbl_currentness": ("CURRENT_NO_MATCH", "PBL_PROHIBITED"),
    }
    for role, (favorable, reason) in checks.items():
        row = resolved.get(role)
        if row is not None and row["result"] not in {favorable, "INDETERMINATE"}:
            reasons.add(reason)
    requirement = resolved.get("jenn_requirement")
    if requirement is not None and requirement["result"] == "EXACT_DECISION_REQUIRED":
        decision = resolved.get("jenn_exact_decision")
        if decision is None or decision["result"] != "CURRENT_ACCEPTED":
            reasons.add("EXACT_JENN_DECISION_MISSING_OR_INVALID")
        elif (decision["subject_ref"], decision["subject_revision"], decision["subject_fingerprint"], decision["context_fingerprint"]) != exact_subjects["jenn_exact_decision"]:
            reasons.add("EXACT_JENN_DECISION_MISSING_OR_INVALID")

    hard = {
        "SYNTHETIC_DOMAIN_VIOLATION", "EXPLICIT_ACTION_CHOICE_MISSING",
        "DIRECT_TASK_WRITE_FORBIDDEN", "DIRECT_COMMAND_COMMIT_FORBIDDEN",
        "EFFECT_EXECUTION_FORBIDDEN", "RELATIONSHIP_OR_TRUST_CANNOT_EXPAND_AUTHORITY",
        "PBL_NO_MATCH_IS_NOT_PERMISSION", "INTENT_SEMANTIC_CLASS_MISMATCH",
        "TARGET_KIND_OUTSIDE_F8", "CONTEXT_FINGERPRINT_MISMATCH",
        "ASSESSMENT_REVISION_MISMATCH", "ASSESSMENT_FINGERPRINT_MISMATCH",
        "ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH",
        "ASSESSMENT_WATERMARK_BEHIND", "UPSTREAM_ASSESSMENT_NOT_CURRENT",
        "F7_INTENT_NOT_CURRENT",
        "ACTOR_IDENTITY_NOT_ACTIVE", "PRINCIPAL_BINDING_NOT_ACTIVE",
        "RESPONSIBILITY_NOT_ACTIVE", "F3_NOT_READY", "PBL_PROHIBITED",
        "EXACT_JENN_DECISION_MISSING_OR_INVALID",
    }
    if reasons & hard:
        result = "REJECTED"
    elif reasons & {"ASSESSMENT_MISSING_OR_UNRESOLVABLE", "UPSTREAM_CURRENTNESS_UNAVAILABLE"}:
        result = "INDETERMINATE"
    elif raw["production_profile_requested"]:
        reasons.add("F3_INTERFACE_REQUIREMENT_UNACCEPTED")
        result = "DEFERRED"
    else:
        reasons.add("VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE")
        result = "CANDIDATE_FORMED"
    ordered = [reason for reason in REASON_PRECEDENCE if reason in reasons]
    return {
        "result": result, "reason_codes": ordered, "primary_reason": ordered[0],
        "command_authority": False, "task_write_authority": False,
        "effect_authority": False, "runtime_usable": False,
        "F3_recheck_required": True, "F3_command_ref": None, "F3_intake_ref": None,
    }


def derive_ack(raw: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = assessment_index(rows).get(raw["F3_outcome_assessment_id"])
    expected_context = acknowledgement_context_fingerprint(
        raw["handoff_candidate_ref"],
        raw["handoff_candidate_revision"],
        raw["handoff_candidate_fingerprint"],
    )
    if row is None:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_MISSING"]
    elif raw["expected_assessment_revision"] != row["assessment_revision"]:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_REVISION_MISMATCH"]
    elif raw["expected_assessment_fingerprint"] != row["row_fingerprint"]:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_FINGERPRINT_MISMATCH"]
    elif (
        row["owner_contract"] != "F3"
        or row["assessment_kind"] != "F3_INTAKE_OUTCOME"
        or row["subject_ref"] != raw["handoff_candidate_ref"]
        or row["subject_revision"] != raw["handoff_candidate_revision"]
        or row["subject_fingerprint"] != raw["handoff_candidate_fingerprint"]
        or row["context_fingerprint"] != expected_context
    ):
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_SUBJECT_MISMATCH"]
    elif row["based_on_event_sequence"] < raw["trusted_event_sequence"]:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_WATERMARK_BEHIND"]
    elif not row["is_current_head"]:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_NOT_CURRENT"]
    elif row["result"] == "SYNTHETIC_TEST_COMMITTED":
        result, reasons = "ACKNOWLEDGED_COMMITTED", ["F3_OWNER_REPORTED_SYNTHETIC_COMMITTED"]
    elif row["result"] == "REJECTED":
        result, reasons = "ACKNOWLEDGED_REJECTED", ["F3_OWNER_REPORTED_REJECTED"]
    elif row["result"] == "NOT_SUBMITTED":
        result, reasons = "NOT_SUBMITTED", ["F3_OWNER_REPORTED_NOT_SUBMITTED"]
    else:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OWNER_REPORTED_INDETERMINATE"]
    return {
        "result": result, "reason_codes": reasons, "primary_reason": reasons[0],
        "command_authority": False, "task_write_authority": False,
        "effect_authority": False, "runtime_usable": False,
    }


def validate_fixture(fixture: Any, *, enforce_anchors: bool = True) -> list[str]:
    errors: list[str] = []
    validate_json_value(fixture, "$", errors)
    if not exact_fields(fixture, ROOT_FIELDS, "$", errors):
        return errors
    if fixture["schema_version"] != "agents-os.f8-r2.synthetic-nonauthority-witness.v0.1": errors.append("$: schema_version mismatch")
    if fixture["contract_id"] != "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R2": errors.append("$: contract_id mismatch")
    if fixture["environment"] != "SYNTHETIC_TEST" or fixture["domain_tag"] != DOMAIN or fixture["runtime_usable"] is not False: errors.append("$: synthetic domain boundary mismatch")

    inventory = fixture["schema_inventory"]
    if type(inventory) is not list or len(inventory) != len(SCHEMA_PROFILES):
        errors.append("schema_inventory: expected exact ten profiles")
    else:
        for index, ((name, fields), row) in enumerate(zip(SCHEMA_PROFILES.items(), inventory)):
            path = f"schema_inventory[{index}]"
            if not exact_fields(row, SCHEMA_ROW_FIELDS, path, errors): continue
            if row["schema_name"] != name or row["exact_fields"] != fields or row["unknown_fields_policy"] != "REJECT": errors.append(f"{path}: canonical profile mismatch")
            if row["row_fingerprint"] != digest(DOMAIN + ":schema-profile", without(row, "row_fingerprint")): errors.append(f"{path}: fingerprint mismatch")

    prospective = fixture["prospective_f3_interface_requirement"]
    if exact_fields(prospective, PROSPECTIVE_FIELDS, "prospective_f3_interface_requirement", errors):
        expected = {
            "requirement_id": "F3_HOME_INTENT_HANDOFF_COMMAND_TYPE", "owner": "F3",
            "status": "UNACCEPTED_DOWNSTREAM_REQUIREMENT", "usable_in_runtime": False,
            "synthetic_fixture_only": True,
            "required_F3_contract": "F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE",
            "required_submission_interface": "agents-os.command-submission.v0.1",
            "required_intake_results": ["COMMITTED", "REJECTED", "INDETERMINATE"],
            "F8_may_mint_command": False, "F8_may_mint_authentication": False,
            "F8_may_commit_intake": False,
        }
        if without(prospective, "row_fingerprint") != expected: errors.append("prospective_f3_interface_requirement: normative values mismatch")
        if prospective["row_fingerprint"] != digest(DOMAIN + ":prospective-f3-interface", expected): errors.append("prospective_f3_interface_requirement: fingerprint mismatch")

    rows = fixture["upstream_assessments"]
    if type(rows) is not list: errors.append("upstream_assessments: expected list"); rows = []
    seen: set[str] = set()
    actual_anchors: list[tuple[str, int, str]] = []
    for index, row in enumerate(rows):
        path = f"upstream_assessments[{index}]"
        if not exact_fields(row, ASSESSMENT_FIELDS, path, errors): continue
        aid = row["assessment_id"]
        if not stable_ref(aid): errors.append(f"{path}: invalid assessment_id")
        elif aid in seen: errors.append(f"{path}: duplicate assessment_id")
        else: seen.add(aid)
        if not stable_ref(row["subject_ref"]): errors.append(f"{path}: invalid subject_ref")
        if not positive_int(row["assessment_revision"]) or not positive_int(row["subject_revision"]) or not positive_int(row["based_on_event_sequence"]): errors.append(f"{path}: invalid positive integer")
        if not valid_hash(row["subject_fingerprint"]) or not valid_hash(row["row_fingerprint"]): errors.append(f"{path}: invalid subject/row fingerprint")
        contextual_kinds = {"F2_RESPONSIBILITY", "JENN_REQUIREMENT", "JENN_EXACT_DECISION", "F3_INTAKE_OUTCOME"}
        if row["assessment_kind"] in contextual_kinds:
            if not valid_hash(row["context_fingerprint"]): errors.append(f"{path}: contextual assessment requires context fingerprint")
        elif row["context_fingerprint"] is not None:
            errors.append(f"{path}: noncontextual assessment context must be null")
        if type(row["is_current_head"]) is not bool: errors.append(f"{path}: is_current_head must be strict boolean")
        profile = KIND_PROFILE.get(row["assessment_kind"])
        if profile is None or row["owner_contract"] != profile[0] or row["result"] not in profile[1]: errors.append(f"{path}: kind/owner/result mismatch")
        expected_fp = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
        if row["row_fingerprint"] != expected_fp: errors.append(f"{path}: row fingerprint mismatch")
        if type(aid) is str and type(row["assessment_revision"]) is int and type(row["row_fingerprint"]) is str:
            actual_anchors.append((aid, row["assessment_revision"], row["row_fingerprint"]))
    if enforce_anchors and digest(DOMAIN + ":section:upstream_assessments", rows) != SECTION_ANCHORS["upstream_assessments"]: errors.append("upstream_assessments: immutable section anchor mismatch")

    cases = fixture["handoff_cases"]
    if type(cases) is not list or len(cases) != 25: errors.append("handoff_cases: expected 25 rows"); cases = []
    actual_case_anchors: list[tuple[str, str]] = []
    bool_fields = ["explicit_action_choice", "direct_task_write_requested", "direct_command_commit_requested", "effect_execution_requested", "relationship_or_trust_used_as_authority", "pbl_no_match_used_as_sufficient", "production_profile_requested", "runtime_usable_requested"]
    for index, case in enumerate(cases):
        path = f"handoff_cases[{index}]"
        if not exact_fields(case, CASE_FIELDS, path, errors): continue
        raw, decision = case["raw_input"], case["claimed_decision"]
        if not stable_ref(case["case_id"]): errors.append(f"{path}.case_id: stable_ref required")
        if not valid_hash(case["row_fingerprint"]): errors.append(f"{path}.row_fingerprint: lowercase SHA-256 required")
        raw_ok = exact_fields(raw, RAW_FIELDS, path + ".raw_input", errors)
        decision_ok = exact_fields(decision, DECISION_FIELDS, path + ".claimed_decision", errors)
        if raw_ok:
            if type(raw["assessment_consumers"]) is not dict or set(raw["assessment_consumers"]) != set(CONSUMER_ROLES): errors.append(f"{path}.raw_input: consumer role inventory mismatch")
            else:
                for role in CONSUMER_ROLES:
                    binding = raw["assessment_consumers"][role]
                    if exact_fields(binding, CONSUMER_FIELDS, f"{path}.raw_input.assessment_consumers.{role}", errors):
                        aid = binding["assessment_id"]
                        revision = binding["expected_assessment_revision"]
                        fingerprint = binding["expected_assessment_fingerprint"]
                        if aid is None:
                            if revision is not None or fingerprint is not None: errors.append(f"{path}: null assessment requires all-null commitment")
                        elif not stable_ref(aid) or not positive_int(revision) or not valid_hash(fingerprint): errors.append(f"{path}: invalid assessment consumer")
            for key in ["environment", "intent_semantic_class", "target_kind"]:
                if not stable_ref(raw[key]): errors.append(f"{path}.raw_input.{key}: closed string required")
            if raw["environment"] != "SYNTHETIC_TEST": errors.append(f"{path}.raw_input.environment: unknown enum")
            if raw["intent_semantic_class"] not in {"INTENT_CANDIDATE", "SESSION_CONTENT"}: errors.append(f"{path}.raw_input.intent_semantic_class: unknown enum")
            if raw["target_kind"] not in {"ORCHESTRATOR_INTAKE_CANDIDATE", "TASK_CANONICAL_FACT"}: errors.append(f"{path}.raw_input.target_kind: unknown enum")
            for key in ["intent_candidate_ref", "creator_actor_ref", "principal_ref", "target_ref", "payload_schema_ref"]:
                if not stable_ref(raw[key]): errors.append(f"{path}.raw_input.{key}: stable_ref required")
            for key in bool_fields:
                if type(raw[key]) is not bool: errors.append(f"{path}.raw_input.{key}: strict boolean required")
            for key in ["intent_candidate_revision", "creator_actor_revision", "principal_revision", "target_revision", "trusted_event_sequence"]:
                if not positive_int(raw[key]): errors.append(f"{path}.raw_input.{key}: positive integer required")
            for key in ["intent_candidate_fingerprint", "creator_actor_fingerprint", "principal_fingerprint", "target_fingerprint", "payload_schema_fingerprint", "payload_commitment", "context_fingerprint"]:
                if not valid_hash(raw[key]): errors.append(f"{path}.raw_input.{key}: lowercase SHA-256 required")
        if decision_ok:
            if decision["result"] not in {"CANDIDATE_FORMED", "REJECTED", "DEFERRED", "INDETERMINATE"}: errors.append(f"{path}: unknown decision result")
            if not closed_string_list(decision["reason_codes"], set(REASON_PRECEDENCE)): errors.append(f"{path}: invalid reason_codes")
            elif decision["reason_codes"] != [reason for reason in REASON_PRECEDENCE if reason in decision["reason_codes"]]: errors.append(f"{path}: reason precedence mismatch")
            if type(decision["primary_reason"]) is not str or decision["primary_reason"] not in REASON_PRECEDENCE or (type(decision["reason_codes"]) is list and decision["reason_codes"] and decision["primary_reason"] != decision["reason_codes"][0]): errors.append(f"{path}: invalid primary_reason")
            for key in ["command_authority", "task_write_authority", "effect_authority", "runtime_usable"]:
                if decision[key] is not False: errors.append(f"{path}: {key} must be false")
            if decision["F3_recheck_required"] is not True or decision["F3_command_ref"] is not None or decision["F3_intake_ref"] is not None: errors.append(f"{path}: F3 boundary fields invalid")
        if raw_ok and decision_ok:
            try:
                if decision != derive_case(raw, rows): errors.append(f"{path}: claimed decision not independently derived")
            except Exception as exc:
                errors.append(f"{path}: stable semantic BLOCK ({type(exc).__name__})")
        if case["row_fingerprint"] != digest(DOMAIN + ":handoff-case", without(case, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")
        if type(case["case_id"]) is str and type(raw) is dict: actual_case_anchors.append((case["case_id"], plain_sha(raw)))
    if enforce_anchors and digest(DOMAIN + ":section:handoff_cases", cases) != SECTION_ANCHORS["handoff_cases"]: errors.append("handoff_cases: canonical section anchor mismatch")

    expected_assessment_set_fingerprint = None
    if cases and type(cases[0]) is dict and type(cases[0].get("raw_input")) is dict:
        consumers = cases[0]["raw_input"].get("assessment_consumers")
        if type(consumers) is dict and set(consumers) == set(CONSUMER_ROLES):
            assessment_set = [
                [
                    role,
                    consumers[role].get("assessment_id"),
                    consumers[role].get("expected_assessment_revision"),
                    consumers[role].get("expected_assessment_fingerprint"),
                ]
                for role in CONSUMER_ROLES
            ]
            expected_assessment_set_fingerprint = digest(DOMAIN + ":assessment-set", assessment_set)

    history = fixture["handoff_candidate_history"]
    if type(history) is not list or len(history) != 2: errors.append("handoff_candidate_history: expected two revisions"); history = []
    actual_candidate_anchors: list[tuple[str, int, str]] = []
    predecessor = None
    for index, row in enumerate(history):
        path = f"handoff_candidate_history[{index}]"
        if not exact_fields(row, CANDIDATE_FIELDS, path, errors): continue
        for key in ["handoff_candidate_id", "intent_candidate_ref", "target_ref", "created_event_ref"]:
            if not stable_ref(row[key]): errors.append(f"{path}.{key}: stable_ref required")
        if row["predecessor_ref"] is not None and not stable_ref(row["predecessor_ref"]): errors.append(f"{path}.predecessor_ref: stable_ref or null required")
        if row["predecessor_fingerprint"] is not None and not valid_hash(row["predecessor_fingerprint"]): errors.append(f"{path}.predecessor_fingerprint: SHA-256 or null required")
        integer_fields_valid = True
        for key in ["handoff_candidate_revision", "intent_candidate_revision", "target_revision"]:
            if not positive_int(row[key]):
                errors.append(f"{path}.{key}: positive integer required")
                integer_fields_valid = False
        if not integer_fields_valid:
            continue
        revision = row["handoff_candidate_revision"]
        if revision != index + 1: errors.append(f"{path}: revision sequence mismatch")
        if index == 0:
            if row["predecessor_ref"] is not None or row["predecessor_fingerprint"] is not None: errors.append(f"{path}: revision 1 predecessor must be null")
        elif predecessor is not None:
            if row["predecessor_ref"] != f"synthetic://f8/handoff-candidate/001@{revision-1}" or row["predecessor_fingerprint"] != predecessor["candidate_fingerprint"]: errors.append(f"{path}: predecessor mismatch")
        for key in ["intent_candidate_fingerprint", "target_fingerprint", "payload_commitment", "context_fingerprint", "assessment_set_fingerprint", "created_event_fingerprint", "candidate_fingerprint"]:
            if not valid_hash(row[key]): errors.append(f"{path}.{key}: invalid hash")
        if expected_assessment_set_fingerprint is not None and row["assessment_set_fingerprint"] != expected_assessment_set_fingerprint: errors.append(f"{path}: assessment set fingerprint mismatch")
        if index > 0 and predecessor is not None and row["handoff_candidate_id"] != predecessor["handoff_candidate_id"]: errors.append(f"{path}: candidate identity changed across revisions")
        if row["runtime_usable"] is not False or row["command_authority"] is not False: errors.append(f"{path}: candidate authority/runtime must be false")
        expected_fp = digest(DOMAIN + ":handoff-candidate", without(row, "candidate_fingerprint"))
        if row["candidate_fingerprint"] != expected_fp: errors.append(f"{path}: candidate fingerprint mismatch")
        actual_candidate_anchors.append((row["handoff_candidate_id"], revision, row["candidate_fingerprint"]))
        predecessor = row
    if enforce_anchors and digest(DOMAIN + ":section:handoff_candidate_history", history) != SECTION_ANCHORS["handoff_candidate_history"]: errors.append("handoff_candidate_history: immutable section anchor mismatch")

    ack_cases = fixture["acknowledgement_cases"]
    if type(ack_cases) is not list or len(ack_cases) != 9: errors.append("acknowledgement_cases: expected nine rows"); ack_cases = []
    actual_ack_anchors: list[tuple[str, str]] = []
    for index, case in enumerate(ack_cases):
        path = f"acknowledgement_cases[{index}]"
        if not exact_fields(case, ACK_CASE_FIELDS, path, errors): continue
        if not stable_ref(case["case_id"]): errors.append(f"{path}.case_id: stable_ref required")
        if not valid_hash(case["row_fingerprint"]): errors.append(f"{path}.row_fingerprint: lowercase SHA-256 required")
        raw, decision = case["raw_input"], case["claimed_decision"]
        raw_ok = exact_fields(raw, ACK_RAW_FIELDS, path + ".raw_input", errors)
        decision_ok = exact_fields(decision, ACK_DECISION_FIELDS, path + ".claimed_decision", errors)
        if raw_ok:
            for key in ["handoff_candidate_ref", "F3_outcome_assessment_id"]:
                if not stable_ref(raw[key]): errors.append(f"{path}.{key}: stable_ref required")
            for key in ["handoff_candidate_revision", "trusted_event_sequence", "expected_assessment_revision"]:
                if not positive_int(raw[key]): errors.append(f"{path}.{key}: positive integer required")
            for key in ["handoff_candidate_fingerprint", "expected_assessment_fingerprint"]:
                if not valid_hash(raw[key]): errors.append(f"{path}.{key}: lowercase SHA-256 required")
        if decision_ok:
            if decision["result"] not in {"NOT_SUBMITTED", "ACKNOWLEDGED_COMMITTED", "ACKNOWLEDGED_REJECTED", "ACKNOWLEDGED_INDETERMINATE"}: errors.append(f"{path}: unknown acknowledgement result")
            allowed_ack_reasons = {
                "F3_OUTCOME_MISSING", "F3_OUTCOME_REVISION_MISMATCH",
                "F3_OUTCOME_FINGERPRINT_MISMATCH", "F3_OUTCOME_SUBJECT_MISMATCH",
                "F3_OUTCOME_WATERMARK_BEHIND", "F3_OUTCOME_NOT_CURRENT",
                "F3_OWNER_REPORTED_SYNTHETIC_COMMITTED", "F3_OWNER_REPORTED_REJECTED",
                "F3_OWNER_REPORTED_NOT_SUBMITTED", "F3_OWNER_REPORTED_INDETERMINATE",
            }
            if not closed_string_list(decision["reason_codes"], allowed_ack_reasons): errors.append(f"{path}: invalid acknowledgement reason codes")
            if type(decision["primary_reason"]) is not str or (type(decision["reason_codes"]) is list and decision["reason_codes"] and decision["primary_reason"] != decision["reason_codes"][0]): errors.append(f"{path}: invalid acknowledgement primary reason")
            for key in ["command_authority", "task_write_authority", "effect_authority", "runtime_usable"]:
                if decision[key] is not False: errors.append(f"{path}: acknowledgement {key} must be false")
        if raw_ok and decision_ok:
            try:
                if decision != derive_ack(raw, rows): errors.append(f"{path}: acknowledgement not independently derived")
            except Exception as exc:
                errors.append(f"{path}: stable acknowledgement BLOCK ({type(exc).__name__})")
        if case["row_fingerprint"] != digest(DOMAIN + ":ack-case", without(case, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")
        if type(case["case_id"]) is str and type(raw) is dict: actual_ack_anchors.append((case["case_id"], plain_sha(raw)))
    if enforce_anchors and digest(DOMAIN + ":section:acknowledgement_cases", ack_cases) != SECTION_ANCHORS["acknowledgement_cases"]: errors.append("acknowledgement_cases: canonical section anchor mismatch")

    boundary = fixture["boundary_assertions"]
    if exact_fields(boundary, BOUNDARY_FIELDS, "boundary_assertions", errors):
        for key in BOUNDARY_FIELDS - {"terminal_outcome"}:
            if type(boundary[key]) is not int or boundary[key] != 0: errors.append(f"boundary_assertions.{key}: must be integer zero")
        if boundary["terminal_outcome"] != "NOT_EXECUTED": errors.append("boundary_assertions.terminal_outcome: must be NOT_EXECUTED")

    section_fingerprints = fixture["section_fingerprints"]
    if type(section_fingerprints) is not dict or set(section_fingerprints) != set(SECTION_NAMES): errors.append("section_fingerprints: exact section inventory mismatch")
    else:
        for name in SECTION_NAMES:
            if section_fingerprints[name] != digest(DOMAIN + ":section:" + name, fixture[name]): errors.append(f"section_fingerprints.{name}: mismatch")
    if valid_hash(fixture["root_fingerprint"]):
        body = copy.deepcopy(fixture); body.pop("root_fingerprint")
        if fixture["root_fingerprint"] != digest(DOMAIN + ":root", body): errors.append("root_fingerprint: mismatch")
    else: errors.append("root_fingerprint: invalid")
    return errors


def resign_fixture(fixture: dict[str, Any]) -> None:
    for row in fixture.get("schema_inventory", []):
        if type(row) is dict: row["row_fingerprint"] = digest(DOMAIN + ":schema-profile", without(row, "row_fingerprint"))
    prospective = fixture.get("prospective_f3_interface_requirement")
    if type(prospective) is dict: prospective["row_fingerprint"] = digest(DOMAIN + ":prospective-f3-interface", without(prospective, "row_fingerprint"))
    history = fixture.get("handoff_candidate_history", [])
    for index, row in enumerate(history):
        if type(row) is not dict: continue
        if index and type(history[index-1]) is dict:
            row["predecessor_fingerprint"] = history[index-1].get("candidate_fingerprint")
        row["candidate_fingerprint"] = digest(DOMAIN + ":handoff-candidate", without(row, "candidate_fingerprint"))
    if len(history) >= 2 and type(history[1]) is dict:
        candidate_fp = history[1].get("candidate_fingerprint")
        for row in fixture.get("upstream_assessments", []):
            if type(row) is dict and row.get("subject_ref") == "synthetic://f8/handoff-candidate/001@2": row["subject_fingerprint"] = candidate_fp
        for case in fixture.get("acknowledgement_cases", []):
            if type(case) is dict and type(case.get("raw_input")) is dict: case["raw_input"]["handoff_candidate_fingerprint"] = candidate_fp
    for row in fixture.get("upstream_assessments", []):
        if type(row) is dict: row["row_fingerprint"] = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
    for case in fixture.get("handoff_cases", []):
        if type(case) is dict: case["row_fingerprint"] = digest(DOMAIN + ":handoff-case", without(case, "row_fingerprint"))
    for case in fixture.get("acknowledgement_cases", []):
        if type(case) is dict: case["row_fingerprint"] = digest(DOMAIN + ":ack-case", without(case, "row_fingerprint"))
    sections = fixture.get("section_fingerprints")
    if type(sections) is dict:
        for name in SECTION_NAMES:
            if name in fixture: sections[name] = digest(DOMAIN + ":section:" + name, fixture[name])
    if type(fixture) is dict and "root_fingerprint" in fixture:
        body = copy.deepcopy(fixture); body.pop("root_fingerprint")
        fixture["root_fingerprint"] = digest(DOMAIN + ":root", body)


def run_mutations(fixture: dict[str, Any]) -> tuple[int, int, list[str]]:
    mutations: list[tuple[str, dict[str, Any]]] = []
    for index in range(25):
        value = copy.deepcopy(fixture)
        decision = value["handoff_cases"][index]["claimed_decision"]
        decision["result"] = "CANDIDATE_FORMED" if decision["result"] != "CANDIDATE_FORMED" else "REJECTED"
        resign_fixture(value)
        mutations.append((f"H{index+1:02d}_claim_tamper", value))
    value = copy.deepcopy(fixture); del value["handoff_cases"][5]; resign_fixture(value); mutations.append(("case_delete", value))
    value = copy.deepcopy(fixture); value["handoff_cases"][5]["case_id"] = "H99"; resign_fixture(value); mutations.append(("case_rename", value))
    value = copy.deepcopy(fixture); value["handoff_cases"][5], value["handoff_cases"][6] = value["handoff_cases"][6], value["handoff_cases"][5]; resign_fixture(value); mutations.append(("case_reorder", value))
    value = copy.deepcopy(fixture); value["handoff_cases"][5]["raw_input"] = copy.deepcopy(value["handoff_cases"][0]["raw_input"]); value["handoff_cases"][5]["claimed_decision"] = copy.deepcopy(value["handoff_cases"][0]["claimed_decision"]); resign_fixture(value); mutations.append(("case_positive_substitution", value))
    value = copy.deepcopy(fixture); value["unknown_root"] = False; resign_fixture(value); mutations.append(("unknown_root_field", value))
    value = copy.deepcopy(fixture); value["upstream_assessments"][0]["unknown"] = 0; resign_fixture(value); mutations.append(("unknown_assessment_field", value))
    value = copy.deepcopy(fixture); value["handoff_cases"][0]["raw_input"]["explicit_action_choice"] = 1; resign_fixture(value); mutations.append(("integer_as_boolean", value))
    value = copy.deepcopy(fixture); value["boundary_assertions"]["real_command_count"] = 1; resign_fixture(value); mutations.append(("nonzero_command_occurrence", value))
    value = copy.deepcopy(fixture); value["prospective_f3_interface_requirement"]["usable_in_runtime"] = True; resign_fixture(value); mutations.append(("prospective_runtime_usable", value))
    value = copy.deepcopy(fixture); value["prospective_f3_interface_requirement"]["status"] = "ACCEPTED"; resign_fixture(value); mutations.append(("prospective_status_forged", value))
    value = copy.deepcopy(fixture); value["handoff_cases"][0]["claimed_decision"]["command_authority"] = True; resign_fixture(value); mutations.append(("command_authority_forged", value))
    value = copy.deepcopy(fixture); value["upstream_assessments"][0]["subject_fingerprint"] = "0" * 64; resign_fixture(value); mutations.append(("same_revision_assessment_rewrite", value))
    value = copy.deepcopy(fixture); value["handoff_candidate_history"][1]["payload_commitment"] = "1" * 64; resign_fixture(value); mutations.append(("same_revision_candidate_rewrite", value))
    value = copy.deepcopy(fixture); value["acknowledgement_cases"][1]["claimed_decision"]["result"] = "NOT_SUBMITTED"; resign_fixture(value); mutations.append(("ack_outcome_tamper", value))
    value = copy.deepcopy(fixture); value["acknowledgement_cases"][1]["raw_input"]["F3_outcome_assessment_id"] = "A-F3-OUTCOME-MISMATCH"; value["acknowledgement_cases"][1]["claimed_decision"] = derive_ack(value["acknowledgement_cases"][1]["raw_input"], value["upstream_assessments"]); resign_fixture(value); mutations.append(("ack_subject_substitution", value))
    value = copy.deepcopy(fixture); value["handoff_cases"][0]["raw_input"]["payload_commitment"] = 1.25; resign_fixture(value); mutations.append(("float_payload", value))

    rejected = 0; failures: list[str] = []
    for name, value in mutations:
        try:
            errors = validate_fixture(value)
        except Exception as exc:
            failures.append(f"{name}: validator exception {type(exc).__name__}: {exc}")
            continue
        if errors: rejected += 1
        else: failures.append(f"{name}: incorrectly accepted")
    return len(mutations), rejected, failures


def run_r2_regressions(fixture: dict[str, Any]) -> tuple[int, int, list[str]]:
    results: list[tuple[str, bool, str]] = []

    def schema_case(name: str, value: dict[str, Any], fragment: str) -> None:
        try:
            resign_fixture(value)
            errors = validate_fixture(value, enforce_anchors=False)
            matched = any(fragment in error for error in errors)
            results.append((name, matched, " | ".join(errors[:6])))
        except Exception as exc:
            results.append((name, False, f"exception {type(exc).__name__}: {exc}"))

    # R1 A21: the owner row changes at the same revision while the consumer
    # retains the exact old fingerprint. The favorable claim must fail because
    # the reducer sees ASSESSMENT_FINGERPRINT_MISMATCH.
    value = copy.deepcopy(fixture)
    stale = assessment_index(value["upstream_assessments"])["A-F7-STALE"]
    stale["result"] = "CURRENT_ACCEPTED"
    stale["is_current_head"] = True
    value["handoff_cases"][9]["claimed_decision"] = copy.deepcopy(
        value["handoff_cases"][0]["claimed_decision"]
    )
    resign_fixture(value)
    derived = derive_case(
        value["handoff_cases"][9]["raw_input"], value["upstream_assessments"]
    )
    errors = validate_fixture(value, enforce_anchors=False)
    results.append((
        "A21_same_revision_assessment_rewrite",
        derived["result"] == "REJECTED"
        and "ASSESSMENT_FINGERPRINT_MISMATCH" in derived["reason_codes"]
        and any("claimed decision not independently derived" in error for error in errors),
        " | ".join(errors[:6]),
    ))

    # The candidate assessment-set commitment must remain tied to the exact
    # consumer fingerprints, not only IDs and revisions.
    value = copy.deepcopy(fixture)
    value["handoff_cases"][0]["raw_input"]["assessment_consumers"]["actor_identity"]["expected_assessment_fingerprint"] = "0" * 64
    schema_case(
        "assessment_set_exact_fingerprint_binding",
        value,
        "assessment set fingerprint mismatch",
    )

    # R1 A22 split into exact subject-revision, watermark and context probes.
    for name, field, replacement, reason in [
        ("ack_wrong_subject_revision", "subject_revision", 999, "F3_OUTCOME_SUBJECT_MISMATCH"),
        ("ack_watermark_behind", "based_on_event_sequence", 1, "F3_OUTCOME_WATERMARK_BEHIND"),
        ("ack_context_mismatch", "context_fingerprint", "0" * 64, "F3_OUTCOME_SUBJECT_MISMATCH"),
    ]:
        value = copy.deepcopy(fixture)
        row = assessment_index(value["upstream_assessments"])["A-F3-OUTCOME-COMMITTED"]
        row[field] = replacement
        row["row_fingerprint"] = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
        raw = value["acknowledgement_cases"][1]["raw_input"]
        raw["expected_assessment_fingerprint"] = row["row_fingerprint"]
        resign_fixture(value)
        decision = derive_ack(raw, value["upstream_assessments"])
        value["acknowledgement_cases"][1]["claimed_decision"] = copy.deepcopy(
            fixture["acknowledgement_cases"][1]["claimed_decision"]
        )
        resign_fixture(value)
        errors = validate_fixture(value, enforce_anchors=False)
        results.append((
            name,
            decision["result"] == "ACKNOWLEDGED_INDETERMINATE"
            and reason in decision["reason_codes"]
            and any("acknowledgement not independently derived" in error for error in errors),
            " | ".join(errors[:6]),
        ))

    value = copy.deepcopy(fixture)
    value["acknowledgement_cases"][1]["raw_input"]["expected_assessment_fingerprint"] = "0" * 64
    value["acknowledgement_cases"][1]["claimed_decision"] = copy.deepcopy(
        fixture["acknowledgement_cases"][1]["claimed_decision"]
    )
    schema_case("ack_assessment_fingerprint_mismatch", value, "acknowledgement not independently derived")

    # Target-schema probes deliberately disable canonical fixture anchors.
    value = copy.deepcopy(fixture)
    value["handoff_candidate_history"][1]["created_event_ref"] = 17
    schema_case("A23_created_event_ref_integer", value, "created_event_ref: stable_ref required")

    value = copy.deepcopy(fixture)
    value["handoff_candidate_history"][1]["unknown"] = False
    schema_case("unknown_candidate_field", value, "fields mismatch")

    value = copy.deepcopy(fixture)
    value["handoff_candidate_history"][1]["handoff_candidate_id"] = ""
    schema_case("empty_candidate_stable_ref", value, "handoff_candidate_id: stable_ref required")

    value = copy.deepcopy(fixture)
    value["handoff_candidate_history"][1]["handoff_candidate_revision"] = True
    schema_case("boolean_candidate_revision", value, "positive integer required")

    value = copy.deepcopy(fixture)
    value["handoff_candidate_history"][1]["predecessor_ref"] = None
    schema_case("candidate_predecessor_nullability", value, "predecessor mismatch")

    value = copy.deepcopy(fixture)
    binding = value["handoff_cases"][0]["raw_input"]["assessment_consumers"]["actor_identity"]
    binding["assessment_id"] = None
    schema_case("consumer_partial_null_tuple", value, "null assessment requires all-null commitment")

    value = copy.deepcopy(fixture)
    assessment_index(value["upstream_assessments"])["A-RESP-ACTIVE"]["context_fingerprint"] = None
    schema_case("contextual_assessment_null_context", value, "contextual assessment requires context fingerprint")

    value = copy.deepcopy(fixture)
    value["acknowledgement_cases"][1]["raw_input"]["handoff_candidate_ref"] = 17
    schema_case("ack_candidate_ref_integer", value, "handoff_candidate_ref: stable_ref required")

    value = copy.deepcopy(fixture)
    value["acknowledgement_cases"][1]["raw_input"]["trusted_event_sequence"] = 0
    schema_case("ack_trusted_sequence_zero", value, "trusted_event_sequence: positive integer required")

    value = copy.deepcopy(fixture)
    value["prospective_f3_interface_requirement"]["required_intake_results"] = [
        "COMMITTED", "INDETERMINATE", "REJECTED"
    ]
    schema_case("required_intake_results_wrong_order", value, "normative values mismatch")

    value = copy.deepcopy(fixture)
    value["boundary_assertions"]["provider_call_count"] = False
    schema_case("boolean_occurrence_count", value, "must be integer zero")

    passed = sum(1 for _, ok, _ in results if ok)
    failures = [f"{name}: {detail}" for name, ok, detail in results if not ok]
    return len(results), passed, failures


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=no_duplicate_pairs,
        parse_constant=reject_constant,
    )


def check_whitespace(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        try:
            data = path.read_bytes()
        except Exception as exc:
            errors.append(f"{path}: unreadable ({type(exc).__name__})")
            continue
        if b"\r" in data:
            errors.append(f"{path}: CR bytes forbidden")
        if b"\t" in data:
            errors.append(f"{path}: tab bytes forbidden")
        if not data.endswith(b"\n") or data.endswith(b"\n\n"):
            errors.append(f"{path}: exactly one terminal LF required")
        for number, line in enumerate(data.splitlines(), start=1):
            if line.endswith((b" ", b"\t")):
                errors.append(f"{path}:{number}: trailing whitespace")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--check-whitespace", nargs="+", type=Path)
    args = parser.parse_args()
    if args.check_whitespace:
        whitespace_errors = check_whitespace(args.check_whitespace)
        print(json.dumps({
            "result": "PASS" if not whitespace_errors else "BLOCK",
            "files_checked": len(args.check_whitespace),
            "errors": whitespace_errors,
        }, sort_keys=True))
        return 0 if not whitespace_errors else 1
    try:
        fixture = load_fixture(args.fixture)
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "phase": "parse", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 1
    errors = validate_fixture(fixture)
    mutation_total, mutation_rejected, mutation_failures = run_mutations(fixture) if not errors else (0, 0, [])
    regression_total, regression_passed, regression_failures = run_r2_regressions(fixture) if not errors else (0, 0, [])
    # Parser-level probes must fail closed without unhandled exceptions.
    parser_probes = {
        "duplicate_key": '{"a":1,"a":2}',
        "NaN": '{"a":NaN}',
        "Infinity": '{"a":Infinity}',
    }
    parser_rejected = 0
    for text in parser_probes.values():
        try:
            json.loads(text, object_pairs_hook=no_duplicate_pairs, parse_constant=reject_constant)
        except Exception:
            parser_rejected += 1
    ok = (
        not errors
        and not mutation_failures
        and mutation_rejected == mutation_total
        and not regression_failures
        and regression_passed == regression_total
        and parser_rejected == len(parser_probes)
    )
    result = {
        "result": "PASS" if ok else "BLOCK",
        "schema_profiles_verified": len(SCHEMA_PROFILES) if not errors else 0,
        "upstream_assessments_verified": len(fixture.get("upstream_assessments", [])) if not errors else 0,
        "handoff_cases_verified": len(fixture.get("handoff_cases", [])) if not errors else 0,
        "candidate_revisions_verified": len(fixture.get("handoff_candidate_history", [])) if not errors else 0,
        "acknowledgement_cases_verified": len(fixture.get("acknowledgement_cases", [])) if not errors else 0,
        "fully_resigned_mutations_rejected": f"{mutation_rejected}/{mutation_total}",
        "R2_target_regressions_passed": f"{regression_passed}/{regression_total}",
        "parser_probes_rejected": f"{parser_rejected}/{len(parser_probes)}",
        "real_command_count": fixture.get("boundary_assertions", {}).get("real_command_count"),
        "provider_call_count": fixture.get("boundary_assertions", {}).get("provider_call_count"),
        "external_effect_count": fixture.get("boundary_assertions", {}).get("external_effect_count"),
        "terminal_outcome": fixture.get("boundary_assertions", {}).get("terminal_outcome"),
        "root_fingerprint": fixture.get("root_fingerprint"),
        "errors": errors[:20],
        "mutation_failures": mutation_failures[:20],
        "R2_regression_failures": regression_failures[:20],
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
