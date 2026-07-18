#!/usr/bin/env python3
"""Offline semantic validator for the F7 R1 synthetic witness."""

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
    "2026-07-18-agents-os-f7-r1-home-domain-minimum-semantics-v0.1.json"
)
DOMAIN = "F7_R1_SYNTHETIC_NONAUTHORITY"
MAX_SAFE_INTEGER = 9007199254740991
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

AUTHORITY_PROFILE = [
    ("STABLE_IDENTITY_FACT", "F2_IDENTITY_AUTHORITY", "UPSTREAM_CANONICAL"),
    ("IDENTITY_NARRATIVE", "IDENTIFIED_AGENT_SELF_RECORD_CANDIDATE", "HOME_CANDIDATE_WRITER"),
    ("FORMAL_RELATIONSHIP_FACT", "FUTURE_RESIDENT_HOME_RELATIONSHIP_REDUCER", "TARGET_NOT_IMPLEMENTED"),
    ("SUBJECTIVE_RELATIONSHIP_MEMORY", "IDENTIFIED_AGENT_SELF_RECORD_CANDIDATE", "HOME_CANDIDATE_WRITER"),
    ("PRESENCE_POLICY", "JENN_GOVERNED_POLICY", "POLICY_AUTHORITY"),
    ("PRESENCE_CONSENT", "FUTURE_AUTHENTICATED_CONSENT_AUTHORITY", "TARGET_NOT_IMPLEMENTED"),
    ("DEVICE_SENSING_STATE", "AUTHENTICATED_PHYSICAL_HOST_ACCEPTED_UPSTREAM", "TARGET_NOT_IMPLEMENTED"),
    ("SESSION_CONTENT", "SESSION_HOST_TRANSIENT_AUTHORITY", "DEFERRED_EXTERNAL_AUTHORITY"),
    ("LIFE_STREAM_CANDIDATE", "EXACT_CANDIDATE_CREATOR", "HOME_CANDIDATE_WRITER"),
    ("MEMORY_CONTENT", "GOVERNED_VCP_NATIVE_MEMORY_AUTHORITY", "DEFERRED_EXTERNAL_AUTHORITY"),
    ("MEMORY_ACCESS_AUTHORITY", "FUTURE_GOVERNED_MEMORY_BRIDGE", "DEFERRED_EXTERNAL_AUTHORITY"),
    ("MEMORY_CANDIDATE", "EXACT_CANDIDATE_CREATOR", "HOME_CANDIDATE_WRITER"),
    ("INTENT_CANDIDATE", "EXACT_CANDIDATE_CREATOR", "HOME_CANDIDATE_WRITER"),
    ("ORCHESTRATOR_COMMAND", "F3_COMMAND_AUTHORITY", "UPSTREAM_CANONICAL"),
    ("GROWTH_EVENT", "EXACT_EVENT_OBSERVER_CANDIDATE", "HOME_CANDIDATE_WRITER"),
    ("BEHAVIOR_POLICY_REVISION", "JENN_OR_ACCEPTED_DELEGATED_POLICY_AUTHORITY", "POLICY_AUTHORITY"),
    ("AGENT_MEMBER_STATE", "FUTURE_RESIDENT_HOME_MEMBER_REDUCER", "TARGET_NOT_IMPLEMENTED"),
    ("ARTIFACT", "CORRESPONDING_ARTIFACT_STORAGE_AUTHORITY", "DEFERRED_EXTERNAL_AUTHORITY"),
    ("HOME_PROJECTION", "DETERMINISTIC_PROJECTION_ONLY", "PROJECTION_ONLY"),
    ("TASK_CANONICAL_FACT", "F1_F3_TASK_AUTHORITY", "UPSTREAM_CANONICAL"),
]
SEMANTIC_CLASSES = {row[0] for row in AUTHORITY_PROFILE}
WRITER_STATUSES = {
    "UPSTREAM_CANONICAL",
    "HOME_CANDIDATE_WRITER",
    "POLICY_AUTHORITY",
    "TARGET_NOT_IMPLEMENTED",
    "DEFERRED_EXTERNAL_AUTHORITY",
    "PROJECTION_ONLY",
}
GAP_DISPOSITIONS = [
    ("HD-M0-01", "RESOLVED_BY_F2_FROZEN_CONTRACT"),
    ("HD-M0-02", "RESOLVED_BY_F3_FROZEN_CONTRACT"),
    ("HD-M0-03", "F7_SEMANTIC_BOUNDARY_CANDIDATE_PENDING_ACCEPTANCE"),
    ("HD-M0-04", "DEFERRED_TO_GOVERNED_MEMORY_ACCESS_CONTRACT"),
    ("HD-M0-05", "DEFERRED_TO_F8_HOME_TO_ORCHESTRATOR_INTERFACE"),
    ("HD-M0-06", "F7_SEMANTIC_BOUNDARY_CANDIDATE_NO_SENSING_IMPLEMENTATION"),
    ("HD-M0-07", "F7_SEMANTIC_BOUNDARY_CANDIDATE_WRITER_TARGET_NOT_IMPLEMENTED"),
]
REASON_PRECEDENCE = [
    "UNKNOWN_OR_MALFORMED_INPUT",
    "SYNTHETIC_DOMAIN_ONLY",
    "UPSTREAM_CURRENTNESS_UNAVAILABLE",
    "SOURCE_NOT_CURRENT",
    "CREATOR_NOT_CURRENT",
    "EXPLICIT_CHOICE_MISSING",
    "TARGET_OUTSIDE_F7",
    "TARGET_WRITER_NOT_IMPLEMENTED",
    "RELATIONSHIP_CANNOT_EXPAND_AUTHORITY",
    "IDENTITY_NARRATIVE_CANNOT_REWRITE_IDENTITY",
    "SESSION_CANNOT_CREATE_TASK",
    "MEMORY_CANDIDATE_IS_NOT_MEMORY",
    "PRESENCE_CONSENT_IS_NOT_SENSING_STATE",
    "GROWTH_EVENT_IS_NOT_POLICY_REVISION",
    "CANDIDATE_ONLY_NO_ACTION_AUTHORITY",
    "VALID_HOME_CANDIDATE",
]
ALLOWED_PAIRS = {
    ("SESSION_CONTENT", "LIFE_STREAM_CANDIDATE"),
    ("SESSION_CONTENT", "MEMORY_CANDIDATE"),
    ("SESSION_CONTENT", "INTENT_CANDIDATE"),
    ("SUBJECTIVE_RELATIONSHIP_MEMORY", "MEMORY_CANDIDATE"),
    ("GROWTH_EVENT", "MEMORY_CANDIDATE"),
}
FIXED_SYNTHETIC_HISTORY_ANCHORS = [
    ("home-candidate-synthetic-001", 1, "a1cf0683d435eb61225d5b516661fa5795e476dcf8564f9dced89308de868fff"),
    ("home-candidate-synthetic-001", 2, "c3901b5312fcb027448859165af6f2084447bd4573e4fea9718463e7ebaa9795"),
]

ROOT_FIELDS = {
    "schema_version", "contract_id", "environment", "domain_tag", "runtime_usable",
    "authority_profile", "decision_cases", "candidate_history", "gap_dispositions",
    "relationship_witness", "presence_witness", "boundary_assertions",
    "section_fingerprints", "root_fingerprint",
}
AUTHORITY_FIELDS = {
    "semantic_class", "semantic_owner", "writer_status", "may_trigger_action_alone", "row_fingerprint"
}
CASE_FIELDS = {"case_id", "raw_input", "claimed_decision", "row_fingerprint"}
RAW_FIELDS = {
    "source_class", "target_class", "source_currentness", "creator_currentness",
    "explicit_choice", "relationship_authority_requested", "action_authority_requested",
    "runtime_target_requested",
}
DECISION_FIELDS = {"result", "reason_codes", "primary_reason", "action_authority"}
CANDIDATE_FIELDS = {
    "candidate_id", "candidate_revision", "predecessor_ref", "predecessor_fingerprint",
    "semantic_class", "creator_actor_assessment_ref", "creator_actor_assessment_fingerprint",
    "source_subject_ref", "source_subject_revision", "source_subject_fingerprint",
    "created_event_ref", "created_event_fingerprint", "payload_commitment", "candidate_fingerprint",
}
GAP_FIELDS = {"gap_id", "disposition", "row_fingerprint"}
RELATIONSHIP_FIELDS = {
    "formal_mutation_available", "subjective_memory_can_bind_other_party",
    "relationship_can_expand_authority", "target_status",
}
PRESENCE_FIELDS = {
    "policy_creates_consent", "consent_proves_sensing", "sensing_authorizes_recording",
    "sensing_creates_memory", "sensor_or_recording_implementation_present",
}
BOUNDARY_FIELDS = {
    "accepted_real_identity_count", "real_session_content_count", "private_raw_memory_count",
    "formal_memory_write_count", "real_relationship_mutation_count", "sensing_or_recording_count",
    "Task_or_Command_mutation_count", "database_write_count", "provider_call_count",
    "external_effect_count", "terminal_outcome",
}
SECTION_NAMES = [
    "authority_profile", "decision_cases", "candidate_history", "gap_dispositions",
    "relationship_witness", "presence_witness", "boundary_assertions",
]


class DuplicateKeyError(ValueError):
    pass


def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def without_field(row: dict[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(row)
    result.pop(field, None)
    return result


def validate_json_value(value: Any, path: str, errors: list[str]) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value < 0 or value > MAX_SAFE_INTEGER:
            errors.append(f"{path}: integer outside safe non-negative range")
        return
    if type(value) is float:
        errors.append(f"{path}: floats are forbidden")
        return
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value:
            errors.append(f"{path}: string is not NFC")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]", errors)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                errors.append(f"{path}: non-string object key")
            else:
                validate_json_value(key, f"{path}.<key>", errors)
            validate_json_value(item, f"{path}.{key}", errors)
        return
    errors.append(f"{path}: unsupported JSON type {type(value).__name__}")


def exact_fields(value: Any, fields: set[str], path: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{path}: expected object")
        return False
    actual = set(value)
    if actual != fields:
        errors.append(f"{path}: fields mismatch missing={sorted(fields-actual)} extra={sorted(actual-fields)}")
        return False
    return True


def strict_bool(value: Any) -> bool:
    return type(value) is bool


def strict_positive_int(value: Any) -> bool:
    return type(value) is int and 1 <= value <= MAX_SAFE_INTEGER


def valid_hash(value: Any) -> bool:
    return type(value) is str and SHA256_RE.fullmatch(value) is not None


def derive_case(raw: dict[str, Any]) -> tuple[str, list[str], str]:
    source, target = raw["source_class"], raw["target_class"]
    reasons: set[str] = set()
    if raw["runtime_target_requested"]:
        reasons.add("SYNTHETIC_DOMAIN_ONLY")
    if raw["source_currentness"] == "UNKNOWN" or raw["creator_currentness"] == "UNKNOWN":
        reasons.add("UPSTREAM_CURRENTNESS_UNAVAILABLE")
    if raw["source_currentness"] == "STALE": reasons.add("SOURCE_NOT_CURRENT")
    if raw["creator_currentness"] == "STALE": reasons.add("CREATOR_NOT_CURRENT")
    if raw["explicit_choice"] is not True: reasons.add("EXPLICIT_CHOICE_MISSING")
    if raw["relationship_authority_requested"]: reasons.add("RELATIONSHIP_CANNOT_EXPAND_AUTHORITY")
    if raw["action_authority_requested"]: reasons.add("CANDIDATE_ONLY_NO_ACTION_AUTHORITY")
    if (source, target) == ("IDENTITY_NARRATIVE", "STABLE_IDENTITY_FACT"):
        reasons.add("IDENTITY_NARRATIVE_CANNOT_REWRITE_IDENTITY")
    elif (source, target) == ("SUBJECTIVE_RELATIONSHIP_MEMORY", "FORMAL_RELATIONSHIP_FACT"):
        reasons.add("TARGET_WRITER_NOT_IMPLEMENTED")
    elif (source, target) == ("SESSION_CONTENT", "TASK_CANONICAL_FACT"):
        reasons.add("SESSION_CANNOT_CREATE_TASK")
    elif (source, target) == ("MEMORY_CANDIDATE", "MEMORY_CONTENT"):
        reasons.add("MEMORY_CANDIDATE_IS_NOT_MEMORY")
    elif (source, target) == ("INTENT_CANDIDATE", "ORCHESTRATOR_COMMAND"):
        reasons.add("TARGET_OUTSIDE_F7")
    elif (source, target) == ("PRESENCE_CONSENT", "DEVICE_SENSING_STATE"):
        reasons.update({"PRESENCE_CONSENT_IS_NOT_SENSING_STATE", "TARGET_WRITER_NOT_IMPLEMENTED"})
    elif (source, target) == ("GROWTH_EVENT", "BEHAVIOR_POLICY_REVISION"):
        reasons.add("GROWTH_EVENT_IS_NOT_POLICY_REVISION")
    elif (source, target) not in ALLOWED_PAIRS:
        reasons.add("TARGET_OUTSIDE_F7")
    blocking = reasons - {"VALID_HOME_CANDIDATE"}
    if not blocking and (source, target) in ALLOWED_PAIRS:
        reasons.add("VALID_HOME_CANDIDATE")
        result = "CANDIDATE_ACCEPTED"
    elif "UPSTREAM_CURRENTNESS_UNAVAILABLE" in reasons:
        result = "INDETERMINATE"
    elif reasons & {
        "TARGET_OUTSIDE_F7", "TARGET_WRITER_NOT_IMPLEMENTED", "MEMORY_CANDIDATE_IS_NOT_MEMORY",
        "PRESENCE_CONSENT_IS_NOT_SENSING_STATE", "GROWTH_EVENT_IS_NOT_POLICY_REVISION",
    } and not reasons & {
        "SYNTHETIC_DOMAIN_ONLY", "SOURCE_NOT_CURRENT", "CREATOR_NOT_CURRENT",
        "EXPLICIT_CHOICE_MISSING", "RELATIONSHIP_CANNOT_EXPAND_AUTHORITY",
        "IDENTITY_NARRATIVE_CANNOT_REWRITE_IDENTITY", "SESSION_CANNOT_CREATE_TASK",
        "CANDIDATE_ONLY_NO_ACTION_AUTHORITY",
    }:
        result = "DEFERRED"
    else:
        result = "REJECTED"
    ordered = [reason for reason in REASON_PRECEDENCE if reason in reasons]
    return result, ordered, ordered[0]


def validate_fixture(document: Any) -> list[str]:
    errors: list[str] = []
    validate_json_value(document, "$", errors)
    if not exact_fields(document, ROOT_FIELDS, "$", errors):
        return errors
    if document["schema_version"] != "agents-os.f7-home-domain-minimum-semantics-witness.v0.1":
        errors.append("$.schema_version: unexpected value")
    if document["contract_id"] != "F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R1":
        errors.append("$.contract_id: unexpected value")
    if document["environment"] != "SYNTHETIC_TEST" or document["domain_tag"] != DOMAIN:
        errors.append("$: synthetic domain binding mismatch")
    if document["runtime_usable"] is not False:
        errors.append("$.runtime_usable: must be strict false")

    authority = document["authority_profile"]
    if type(authority) is not list or len(authority) != len(AUTHORITY_PROFILE):
        errors.append("$.authority_profile: must contain exactly 20 rows")
    else:
        resolved: list[tuple[str, str, str]] = []
        for index, row in enumerate(authority):
            path = f"$.authority_profile[{index}]"
            if not exact_fields(row, AUTHORITY_FIELDS, path, errors): continue
            if row["semantic_class"] not in SEMANTIC_CLASSES: errors.append(path + ": unknown semantic class")
            if row["writer_status"] not in WRITER_STATUSES: errors.append(path + ": unknown writer status")
            if row["may_trigger_action_alone"] is not False: errors.append(path + ": action authority must be false")
            expected_hash = digest(DOMAIN + ":authority-profile", without_field(row, "row_fingerprint"))
            if row["row_fingerprint"] != expected_hash: errors.append(path + ": row fingerprint mismatch")
            resolved.append((row["semantic_class"], row["semantic_owner"], row["writer_status"]))
        if resolved != AUTHORITY_PROFILE:
            errors.append("$.authority_profile: mapping or order differs from normative profile")

    cases = document["decision_cases"]
    if type(cases) is not list or len(cases) != 20:
        errors.append("$.decision_cases: must contain exactly 20 cases")
    else:
        ids: set[str] = set()
        for index, case in enumerate(cases):
            path = f"$.decision_cases[{index}]"
            if not exact_fields(case, CASE_FIELDS, path, errors): continue
            if type(case["case_id"]) is not str or case["case_id"] in ids:
                errors.append(path + ": invalid or duplicate case_id")
            ids.add(case["case_id"])
            raw, claim = case["raw_input"], case["claimed_decision"]
            if not exact_fields(raw, RAW_FIELDS, path + ".raw_input", errors): continue
            if not exact_fields(claim, DECISION_FIELDS, path + ".claimed_decision", errors): continue
            if raw["source_class"] not in SEMANTIC_CLASSES or raw["target_class"] not in SEMANTIC_CLASSES:
                errors.append(path + ": unknown source or target class"); continue
            if raw["source_currentness"] not in {"CURRENT", "STALE", "UNKNOWN"}:
                errors.append(path + ": invalid source currentness"); continue
            if raw["creator_currentness"] not in {"CURRENT", "STALE", "UNKNOWN"}:
                errors.append(path + ": invalid creator currentness"); continue
            if raw["explicit_choice"] is not None and not strict_bool(raw["explicit_choice"]):
                errors.append(path + ": explicit_choice must be boolean or null"); continue
            for name in ("relationship_authority_requested", "action_authority_requested", "runtime_target_requested"):
                if not strict_bool(raw[name]): errors.append(path + f": {name} must be strict boolean")
            if claim["result"] not in {"CANDIDATE_ACCEPTED", "REJECTED", "DEFERRED", "INDETERMINATE"}:
                errors.append(path + ": unknown claimed result"); continue
            if type(claim["reason_codes"]) is not list or any(type(x) is not str for x in claim["reason_codes"]):
                errors.append(path + ": reason_codes must be a string list"); continue
            if claim["action_authority"] is not False:
                errors.append(path + ": action authority must remain false")
            expected_result, expected_reasons, expected_primary = derive_case(raw)
            if (claim["result"], claim["reason_codes"], claim["primary_reason"]) != (
                expected_result, expected_reasons, expected_primary
            ):
                errors.append(path + ": claimed decision differs from independently derived decision")
            expected_hash = digest(DOMAIN + ":decision-case", without_field(case, "row_fingerprint"))
            if case["row_fingerprint"] != expected_hash: errors.append(path + ": row fingerprint mismatch")

    history = document["candidate_history"]
    if type(history) is not list or len(history) != 2:
        errors.append("$.candidate_history: requires two revision witnesses")
    else:
        identities: set[tuple[str, int]] = set()
        resolved_history: list[tuple[str, int, str]] = []
        previous: dict[str, Any] | None = None
        for index, revision in enumerate(history):
            path = f"$.candidate_history[{index}]"
            if not exact_fields(revision, CANDIDATE_FIELDS, path, errors): continue
            if not strict_positive_int(revision["candidate_revision"]): errors.append(path + ": invalid candidate revision")
            if not strict_positive_int(revision["source_subject_revision"]): errors.append(path + ": invalid source revision")
            identity = (revision["candidate_id"], revision["candidate_revision"])
            if identity in identities: errors.append(path + ": duplicate immutable identity/revision")
            identities.add(identity)
            resolved_history.append((revision["candidate_id"], revision["candidate_revision"], revision["candidate_fingerprint"]))
            for name in (
                "creator_actor_assessment_fingerprint", "source_subject_fingerprint",
                "created_event_fingerprint", "payload_commitment", "candidate_fingerprint",
            ):
                if not valid_hash(revision[name]): errors.append(path + f": malformed {name}")
            expected_hash = digest(DOMAIN + ":candidate-revision", without_field(revision, "candidate_fingerprint"))
            if revision["candidate_fingerprint"] != expected_hash: errors.append(path + ": candidate fingerprint mismatch")
            if previous is None:
                if revision["candidate_revision"] != 1 or revision["predecessor_ref"] is not None or revision["predecessor_fingerprint"] is not None:
                    errors.append(path + ": revision 1 predecessor rule violated")
            else:
                if revision["candidate_id"] != previous["candidate_id"]:
                    errors.append(path + ": candidate identity changed across lineage")
                if revision["candidate_revision"] != previous["candidate_revision"] + 1:
                    errors.append(path + ": candidate revisions are not contiguous")
                expected_ref = f"{revision['candidate_id']}@{revision['candidate_revision'] - 1}"
                if revision["predecessor_ref"] != expected_ref or revision["predecessor_fingerprint"] != previous["candidate_fingerprint"]:
                    errors.append(path + ": exact predecessor binding mismatch")
            previous = revision
        if resolved_history != FIXED_SYNTHETIC_HISTORY_ANCHORS:
            errors.append("$.candidate_history: differs from the fixed immutable synthetic history anchor")

    gaps = document["gap_dispositions"]
    if type(gaps) is not list or len(gaps) != 7:
        errors.append("$.gap_dispositions: must contain exactly seven rows")
    else:
        resolved_gaps = []
        for index, row in enumerate(gaps):
            path = f"$.gap_dispositions[{index}]"
            if not exact_fields(row, GAP_FIELDS, path, errors): continue
            expected_hash = digest(DOMAIN + ":gap-disposition", without_field(row, "row_fingerprint"))
            if row["row_fingerprint"] != expected_hash: errors.append(path + ": row fingerprint mismatch")
            resolved_gaps.append((row["gap_id"], row["disposition"]))
        if resolved_gaps != GAP_DISPOSITIONS: errors.append("$.gap_dispositions: normative mapping mismatch")

    relationship = document["relationship_witness"]
    if exact_fields(relationship, RELATIONSHIP_FIELDS, "$.relationship_witness", errors):
        expected_relationship = {
            "formal_mutation_available": False,
            "subjective_memory_can_bind_other_party": False,
            "relationship_can_expand_authority": False,
            "target_status": "TARGET_NOT_IMPLEMENTED",
        }
        if relationship != expected_relationship: errors.append("$.relationship_witness: unsafe relationship semantics")
    presence = document["presence_witness"]
    if exact_fields(presence, PRESENCE_FIELDS, "$.presence_witness", errors):
        if any(value is not False for value in presence.values()):
            errors.append("$.presence_witness: presence must not create consent, sensing, recording or Memory")
    boundary = document["boundary_assertions"]
    if exact_fields(boundary, BOUNDARY_FIELDS, "$.boundary_assertions", errors):
        for name in BOUNDARY_FIELDS - {"terminal_outcome"}:
            if type(boundary[name]) is not int or boundary[name] != 0:
                errors.append(f"$.boundary_assertions.{name}: must be strict integer zero")
        if boundary["terminal_outcome"] != "NOT_EXECUTED":
            errors.append("$.boundary_assertions.terminal_outcome: must be NOT_EXECUTED")

    section_fingerprints = document["section_fingerprints"]
    if exact_fields(section_fingerprints, set(SECTION_NAMES), "$.section_fingerprints", errors):
        for name in SECTION_NAMES:
            expected_hash = digest(f"{DOMAIN}:section:{name}", document[name])
            if section_fingerprints[name] != expected_hash:
                errors.append(f"$.section_fingerprints.{name}: mismatch")
    if not valid_hash(document["root_fingerprint"]):
        errors.append("$.root_fingerprint: malformed")
    else:
        expected_root = digest(DOMAIN + ":root", without_field(document, "root_fingerprint"))
        if document["root_fingerprint"] != expected_root:
            errors.append("$.root_fingerprint: mismatch")
    return errors


def resign(document: dict[str, Any]) -> None:
    for row in document.get("authority_profile", []):
        if type(row) is dict:
            row["row_fingerprint"] = digest(DOMAIN + ":authority-profile", without_field(row, "row_fingerprint"))
    for row in document.get("decision_cases", []):
        if type(row) is dict:
            row["row_fingerprint"] = digest(DOMAIN + ":decision-case", without_field(row, "row_fingerprint"))
    for row in document.get("candidate_history", []):
        if type(row) is dict:
            row["candidate_fingerprint"] = digest(DOMAIN + ":candidate-revision", without_field(row, "candidate_fingerprint"))
    for row in document.get("gap_dispositions", []):
        if type(row) is dict:
            row["row_fingerprint"] = digest(DOMAIN + ":gap-disposition", without_field(row, "row_fingerprint"))
    if type(document.get("section_fingerprints")) is dict:
        document["section_fingerprints"] = {
            name: digest(f"{DOMAIN}:section:{name}", document[name])
            for name in SECTION_NAMES if name in document
        }
    document["root_fingerprint"] = digest(DOMAIN + ":root", without_field(document, "root_fingerprint"))


def set_claim_accepted(case: dict[str, Any]) -> None:
    case["claimed_decision"] = {
        "result": "CANDIDATE_ACCEPTED",
        "reason_codes": ["VALID_HOME_CANDIDATE"],
        "primary_reason": "VALID_HOME_CANDIDATE",
        "action_authority": False,
    }


def run_adversarial_suite(base: dict[str, Any]) -> tuple[int, list[str]]:
    mutations: list[tuple[str, Any]] = []

    for case_index, name in [(5,"identity_rewrite"),(6,"subjective_to_formal"),(7,"session_to_task"),
                             (8,"candidate_to_memory"),(9,"intent_to_command"),(10,"consent_to_sensing"),
                             (11,"growth_to_policy"),(12,"relationship_authority")]:
        def mutate_claim(doc: dict[str, Any], index: int = case_index) -> None:
            set_claim_accepted(doc["decision_cases"][index])
        mutations.append((name, mutate_claim))

    mutations.extend([
        ("sensing_creates_memory", lambda d: d["presence_witness"].__setitem__("sensing_creates_memory", True)),
        ("projection_becomes_writer", lambda d: d["authority_profile"][18].__setitem__("writer_status", "HOME_CANDIDATE_WRITER")),
        ("unknown_class", lambda d: d["decision_cases"][0]["raw_input"].__setitem__("target_class", "UNKNOWN_CLASS")),
        ("unknown_writer", lambda d: d["authority_profile"][0].__setitem__("writer_status", "UNKNOWN_WRITER")),
        ("unknown_result", lambda d: d["decision_cases"][0]["claimed_decision"].__setitem__("result", "ALLOW")),
        ("runtime_usable", lambda d: d.__setitem__("runtime_usable", True)),
        ("unknown_root_field", lambda d: d.__setitem__("unexpected", "value")),
        ("unknown_row_field", lambda d: d["decision_cases"][0].__setitem__("unexpected", "value")),
        ("bool_as_integer", lambda d: d["decision_cases"][0]["raw_input"].__setitem__("explicit_choice", 1)),
        ("float_value", lambda d: d["boundary_assertions"].__setitem__("external_effect_count", 0.0)),
        ("non_nfc", lambda d: d["decision_cases"][0].__setitem__("case_id", "e\u0301")),
    ])

    for boundary_name in sorted(BOUNDARY_FIELDS - {"terminal_outcome"}):
        mutations.append((f"nonzero_{boundary_name}", lambda d, key=boundary_name: d["boundary_assertions"].__setitem__(key, 1)))

    def same_revision_changed_payload(doc: dict[str, Any]) -> None:
        doc["candidate_history"][1]["payload_commitment"] = "f" * 64
    mutations.append(("same_revision_changed_payload", same_revision_changed_payload))

    failed: list[str] = []
    rejected = 0
    for name, mutation in mutations:
        mutated = copy.deepcopy(base)
        mutation(mutated)
        resign(mutated)
        try:
            errors = validate_fixture(mutated)
        except Exception as exc:  # stable rejection, never counted as success
            failed.append(f"{name}: validator exception {type(exc).__name__}: {exc}")
            continue
        if errors:
            rejected += 1
        else:
            failed.append(f"{name}: fully re-signed semantic mutation was accepted")

    duplicate_json = '{"schema_version":"x","schema_version":"y"}'
    try:
        json.loads(duplicate_json, object_pairs_hook=no_duplicate_pairs)
        failed.append("duplicate_json_key: accepted")
    except DuplicateKeyError:
        rejected += 1
    return rejected, failed


def load_document(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_pairs)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--skip-adversarial", action="store_true")
    args = parser.parse_args()
    try:
        document = load_document(args.fixture)
        errors = validate_fixture(document)
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "errors": [f"stable parse/validation failure: {type(exc).__name__}: {exc}"]}, indent=2))
        return 1
    if errors:
        print(json.dumps({"result": "BLOCK", "errors": errors}, indent=2))
        return 1
    adversarial_rejected = 0
    if not args.skip_adversarial:
        adversarial_rejected, adversarial_failures = run_adversarial_suite(document)
        if adversarial_failures:
            print(json.dumps({"result": "BLOCK", "adversarial_failures": adversarial_failures}, indent=2))
            return 1
    print(json.dumps({
        "result": "PASS",
        "authority_profile_count": len(document["authority_profile"]),
        "decision_case_count": len(document["decision_cases"]),
        "candidate_revision_count": len(document["candidate_history"]),
        "gap_disposition_count": len(document["gap_dispositions"]),
        "adversarial_mutations_rejected": adversarial_rejected,
        "real_occurrence_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
        "root_fingerprint": document["root_fingerprint"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
