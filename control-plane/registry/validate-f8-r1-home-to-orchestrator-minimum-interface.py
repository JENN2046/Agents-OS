#!/usr/bin/env python3
"""Offline semantic validator for the F8 R1 synthetic nonauthority witness."""

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
    "2026-07-19-agents-os-f8-r1-home-to-orchestrator-minimum-interface-v0.1.json"
)
DOMAIN = "F8_R1_SYNTHETIC_NONAUTHORITY"
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
    "ASSESSMENT_REVISION_MISMATCH", "ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH",
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
    "AssessmentConsumerV0_1": ["assessment_id", "expected_assessment_revision"],
    "HomeIntentHandoffRawInputV0_1": [
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
    "HomeIntentHandoffDecisionV0_1": [
        "result", "reason_codes", "primary_reason", "command_authority",
        "task_write_authority", "effect_authority", "runtime_usable",
        "F3_recheck_required", "F3_command_ref", "F3_intake_ref",
    ],
    "HomeIntentHandoffDecisionCaseV0_1": [
        "case_id", "raw_input", "claimed_decision", "row_fingerprint",
    ],
    "HomeIntentHandoffCandidateRevisionV0_1": [
        "handoff_candidate_id", "handoff_candidate_revision", "predecessor_ref",
        "predecessor_fingerprint", "intent_candidate_ref", "intent_candidate_revision",
        "intent_candidate_fingerprint", "target_ref", "target_revision",
        "target_fingerprint", "payload_commitment", "context_fingerprint",
        "assessment_set_fingerprint", "created_event_ref", "created_event_fingerprint",
        "runtime_usable", "command_authority", "candidate_fingerprint",
    ],
    "ProspectiveF3HomeIntentInterfaceRequirementV0_1": [
        "requirement_id", "owner", "status", "usable_in_runtime",
        "synthetic_fixture_only", "required_F3_contract", "required_submission_interface",
        "required_intake_results", "F8_may_mint_command", "F8_may_mint_authentication",
        "F8_may_commit_intake", "row_fingerprint",
    ],
    "HomeIntentHandoffAcknowledgementRawInputV0_1": [
        "handoff_candidate_ref", "handoff_candidate_fingerprint",
        "F3_outcome_assessment_id", "expected_assessment_revision",
    ],
    "HomeIntentHandoffAcknowledgementDecisionV0_1": [
        "result", "reason_codes", "primary_reason", "command_authority",
        "task_write_authority", "effect_authority", "runtime_usable",
    ],
    "BoundaryAssertionsV0_1": [
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
CONSUMER_FIELDS = set(SCHEMA_PROFILES["AssessmentConsumerV0_1"])
RAW_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffRawInputV0_1"])
DECISION_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffDecisionV0_1"])
CASE_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffDecisionCaseV0_1"])
CANDIDATE_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffCandidateRevisionV0_1"])
PROSPECTIVE_FIELDS = set(SCHEMA_PROFILES["ProspectiveF3HomeIntentInterfaceRequirementV0_1"])
ACK_RAW_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffAcknowledgementRawInputV0_1"])
ACK_DECISION_FIELDS = set(SCHEMA_PROFILES["HomeIntentHandoffAcknowledgementDecisionV0_1"])
ACK_CASE_FIELDS = {"case_id", "raw_input", "claimed_decision", "row_fingerprint"}
BOUNDARY_FIELDS = set(SCHEMA_PROFILES["BoundaryAssertionsV0_1"])
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

CASE_DIGESTS = [
    ("H01", "b81f59d748780d5ebd4f38f48ba2856c4f5478f536590a38a85b87598f370b45"),
    ("H02", "a5d7d0127fe0994c867cf4f54094704a94f81d1e91283a0a4db05530ca836d02"),
    ("H03", "89f1080d2a8725f08a000cef7a72eb3fd514089015d8e12ee791f747fdc03d0d"),
    ("H04", "1a3e35eb3b6d156541ba7b69f6893ed5a4b94efa897c11c049c3f37ca19f8b2f"),
    ("H05", "1223295f8851fca78143200d37dd87a4660f3a897f798ed1a27d3fe81e42391d"),
    ("H06", "92b593c50b5caabdc04abad7945abd407d2df2b25d996c45f8fcaa58d04736c1"),
    ("H07", "a5fe4d42342b649e94ef4df527b60dddf307231a017e046cb2946d5bc78648da"),
    ("H08", "e7f9e53016d4b3b49294716f32aed4a0248ea2d01fe5bc468c453c50c06a6257"),
    ("H09", "c038e464924a332c10b75009de1ced54c2bb82941fb7c6906804241e216c6b95"),
    ("H10", "143ca57d0cd1a19311797aae729937ea15ffb9889f6aebf2f1889beb15fb1ed9"),
    ("H11", "539b2ee23ba1be86df867db131ddd35c09c97683036781929c887e39b2ce140b"),
    ("H12", "ac8d478dc490b8679246702692e8c2517f886c5815d388c1b8dd572797d59f8b"),
    ("H13", "72b43f8142113758657c29e9fa53ef16c1f03da18263ec110adbb0bf9cb88e6e"),
    ("H14", "26f06a6b0be4c008cb5568f3af0ed21095d31f738f6579d52b4892c1d92c5887"),
    ("H15", "82ce50de2bc9d5a3207d63c807d3088c384b40f152cd9d6354eec60a362ac39b"),
    ("H16", "7de2e32863973a82dca125d5593b9624dd233535d7d2b2dffd48a0a0ae026e93"),
    ("H17", "106598b5b2bbe58d31751d3adeb230838dc8f966ad864fa7ef0115691c2f60ae"),
    ("H18", "504e64e4e90a5758acdf30db9f6a916c4836c88a10944bfb1e36e383bc7795a5"),
    ("H19", "5ed4e72579667791055fb7c45a3a6d0f757b7f896c2d129bec368887f93d59f1"),
    ("H20", "ab5e0d0ed9cf3a2f9a162f5cd669a2e994d6d926c80b2eeb5052ac64255b92e8"),
    ("H21", "f632f971a78ddab0fd0ca90e664fee9a63336f3eddfeb8251be7821d8d0abedb"),
    ("H22", "36c6354ab629591f533bf0211b3610355c14eb4b0fe455e761418065231d9337"),
    ("H23", "cb6e687acea0de8eeded0d84bb124b6f257f9903a604cb3bd342474069c6980f"),
    ("H24", "86a000f80f28190d4c54dfc62ef10f0d888f71c5dc5eb6015e7ef63bac465f8d"),
    ("H25", "adb8b66753c1d866b189eceaa98fd4a06a417a8fe3af7a767be471ccec5ee2a4"),
]
ASSESSMENT_ANCHORS = [
    ("A-F7-CURRENT", 1, "5eec405b2eb3a0f20fba4288bf1fe05bed80c54c174c3e13d0c728ad70da4397"),
    ("A-F7-STALE", 1, "1abdc6e2a75789926849b97e8d2f77145097baca4a9ec353e15103d730ec7e19"),
    ("A-F7-UNKNOWN", 1, "a9e750aaf84063fd2eb29618e364557cd29b6575dfaf2a189a56a4c6a62332fd"),
    ("A-ACTOR-ACTIVE", 1, "449bad01367f8ddbad76d859b29e3e669808f47c63fef54be95515d6df18de4b"),
    ("A-ACTOR-INACTIVE", 1, "a14cac7c3b1acd6bd9c47a77f4411a68c6e0ee007b3d43adca837a8be9abc254"),
    ("A-ACTOR-BEHIND", 1, "e207e44f1b58965bfc472e234ade8cd334b3ddd6aaa875d88a9ec1c39c7ee51e"),
    ("A-PRINCIPAL-ACTIVE", 1, "1380ac8c50815d455ae990d9abe3ec8e26040dfe03a7dee358043752d30062ac"),
    ("A-PRINCIPAL-INACTIVE", 1, "431b2168aeafcfaf1f3a046a65c8083ae3cc65ebe96a6112645d90c63dac62ae"),
    ("A-RESP-ACTIVE", 1, "60b7fe175b702f6df4b368b9edbe4dc8512f3c1e715aec4d997cc6a23cc8ba54"),
    ("A-RESP-INACTIVE", 1, "e25eefa7b0ca0758bc0373e211e71b5943a249b1c56cc0f959bbe1f01f559c92"),
    ("A-RESP-MISMATCH", 1, "83dcd8c191ddf6645ff2284d487af29542ef46222644cf6f972798d473c50cc8"),
    ("A-F3-READY", 1, "e352073ee52fedd95f8bd1d85b3b150bbbb728d48313c18457f721bb89408c6d"),
    ("A-F3-UNKNOWN", 1, "cad3bc00a04a8804c8ce0ce5759e8df4e428a989f8d8c0c524e6efd83810294c"),
    ("A-PBL-CLEAR", 1, "dce5192e48c282f2a9ec5ba5615cd8f40a9c859218de5177e6f461deac245817"),
    ("A-PBL-PROHIBITED", 1, "70f27ba3069666e7f4d2d9c08e471f39864416081377c5d06f070125fabc5e50"),
    ("A-JREQ-NONE", 1, "7cb69d6956b829141bfa94ed810d7d0adb3866b57338d298baa7cb470af6627f"),
    ("A-JREQ-REQUIRED", 1, "97fcac87d4377f90773eae9adf6aa12783a6402ec45e58238efee3f2357c8d8b"),
    ("A-JDECISION-CURRENT", 1, "5fd17df47dae2b7bf0f4b227b5ba3123380256138de665281c5d8cd55fe4dd0b"),
    ("A-JDECISION-MISMATCH", 1, "cdb7184a2aed1daea8421a144a7707a3efb52633d42d78a5d30774616885d20d"),
    ("A-F3-OUTCOME-NOT-SUBMITTED", 1, "b45d2cfb0cf383deca08b5dce9125a4ba4d276d4d355b5b0a40de2fe875c47aa"),
    ("A-F3-OUTCOME-COMMITTED", 1, "972afc55fb882ca854b59b6280eab5cf973ead17ca7bf3c7b6e22894b74991b6"),
    ("A-F3-OUTCOME-REJECTED", 1, "417858decc7f808f51e63abd51b6def6241b3752181cbc55333ce2f827d8a345"),
    ("A-F3-OUTCOME-INDETERMINATE", 1, "46c135bd87c6cfee1d62291a46c8353dc694b7ec7bc3fe822630823b74dfbdaa"),
    ("A-F3-OUTCOME-STALE", 1, "7ce5fdbd225cb81d39813e23382059f0bd9b8aa083d50621faa4d0b2a412bf72"),
    ("A-F3-OUTCOME-MISMATCH", 1, "982c718d7f0cec7593d2f6b3a6233560e513ab29c6ee2c5cb56615494296d7b9"),
]
CANDIDATE_ANCHORS = [
    ("synthetic://f8/handoff-candidate/001", 1, "a258b96db9166b58e717fa4a73d2681e05dcfa4dfcebbbe2b4f2e32c29c18262"),
    ("synthetic://f8/handoff-candidate/001", 2, "dae3fc758e15c295528587b35b48b0780e443120bd1136db18bcd17e24caf3f3"),
]
ACK_DIGESTS = [
    ("A01", "a0163f732d4db5e256e457e55d66db9456f8e9735af8c3c499399a8b26cc3f8c"),
    ("A02", "4679060e2fddfbee4832fa1707a0e3778fd15822712e3936fe319fc6dab3f742"),
    ("A03", "b7e31f61b4d964599631875aac47070c67ebab94fde68f14e1a234fd2c5c30ee"),
    ("A04", "e04d64d45f4c0c9f229f675d3687254515738984c7c99dda8fb1cd187b51119e"),
    ("A05", "b038ea7eb1c7f8b20c0462d3ec8676fe8e133896a8155eeef8ad7e84057ac399"),
    ("A06", "7b9c63379375f1e05b67d6a2cc12cbd50e941f1a898434fa20b94338bec4fece"),
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
        "ASSESSMENT_REVISION_MISMATCH", "ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH",
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
    if row is None:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_MISSING"]
    elif raw["expected_assessment_revision"] != row["assessment_revision"]:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_REVISION_MISMATCH"]
    elif row["owner_contract"] != "F3" or row["assessment_kind"] != "F3_INTAKE_OUTCOME" or row["subject_ref"] != raw["handoff_candidate_ref"] or row["subject_fingerprint"] != raw["handoff_candidate_fingerprint"]:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_SUBJECT_MISMATCH"]
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
    if fixture["schema_version"] != "agents-os.f8-r1.synthetic-nonauthority-witness.v0.1": errors.append("$: schema_version mismatch")
    if fixture["contract_id"] != "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R1": errors.append("$: contract_id mismatch")
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
            "required_intake_results": ["COMMITTED", "INDETERMINATE", "REJECTED"],
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
        if type(aid) is not str or not aid: errors.append(f"{path}: invalid assessment_id")
        elif aid in seen: errors.append(f"{path}: duplicate assessment_id")
        else: seen.add(aid)
        if not positive_int(row["assessment_revision"]) or not positive_int(row["subject_revision"]) or not positive_int(row["based_on_event_sequence"]): errors.append(f"{path}: invalid positive integer")
        if not valid_hash(row["subject_fingerprint"]) or (row["context_fingerprint"] is not None and not valid_hash(row["context_fingerprint"])): errors.append(f"{path}: invalid subject/context fingerprint")
        if type(row["is_current_head"]) is not bool: errors.append(f"{path}: is_current_head must be strict boolean")
        profile = KIND_PROFILE.get(row["assessment_kind"])
        if profile is None or row["owner_contract"] != profile[0] or row["result"] not in profile[1]: errors.append(f"{path}: kind/owner/result mismatch")
        expected_fp = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
        if row["row_fingerprint"] != expected_fp: errors.append(f"{path}: row fingerprint mismatch")
        if type(aid) is str and type(row["assessment_revision"]) is int and type(row["row_fingerprint"]) is str:
            actual_anchors.append((aid, row["assessment_revision"], row["row_fingerprint"]))
    if enforce_anchors and actual_anchors != ASSESSMENT_ANCHORS: errors.append("upstream_assessments: immutable assessment anchors mismatch")

    cases = fixture["handoff_cases"]
    if type(cases) is not list or len(cases) != 25: errors.append("handoff_cases: expected 25 rows"); cases = []
    actual_case_anchors: list[tuple[str, str]] = []
    bool_fields = ["explicit_action_choice", "direct_task_write_requested", "direct_command_commit_requested", "effect_execution_requested", "relationship_or_trust_used_as_authority", "pbl_no_match_used_as_sufficient", "production_profile_requested", "runtime_usable_requested"]
    for index, case in enumerate(cases):
        path = f"handoff_cases[{index}]"
        if not exact_fields(case, CASE_FIELDS, path, errors): continue
        raw, decision = case["raw_input"], case["claimed_decision"]
        raw_ok = exact_fields(raw, RAW_FIELDS, path + ".raw_input", errors)
        decision_ok = exact_fields(decision, DECISION_FIELDS, path + ".claimed_decision", errors)
        if raw_ok:
            if type(raw["assessment_consumers"]) is not dict or set(raw["assessment_consumers"]) != set(CONSUMER_ROLES): errors.append(f"{path}.raw_input: consumer role inventory mismatch")
            else:
                for role in CONSUMER_ROLES:
                    binding = raw["assessment_consumers"][role]
                    if exact_fields(binding, CONSUMER_FIELDS, f"{path}.raw_input.assessment_consumers.{role}", errors):
                        aid, revision = binding["assessment_id"], binding["expected_assessment_revision"]
                        if aid is None:
                            if revision is not None: errors.append(f"{path}: null assessment requires null revision")
                        elif type(aid) is not str or not positive_int(revision): errors.append(f"{path}: invalid assessment consumer")
            for key in bool_fields:
                if type(raw[key]) is not bool: errors.append(f"{path}.raw_input.{key}: strict boolean required")
            for key in ["intent_candidate_revision", "creator_actor_revision", "principal_revision", "target_revision", "trusted_event_sequence"]:
                if not positive_int(raw[key]): errors.append(f"{path}.raw_input.{key}: positive integer required")
            for key in ["intent_candidate_fingerprint", "creator_actor_fingerprint", "principal_fingerprint", "target_fingerprint", "payload_schema_fingerprint", "payload_commitment", "context_fingerprint"]:
                if not valid_hash(raw[key]): errors.append(f"{path}.raw_input.{key}: lowercase SHA-256 required")
        if decision_ok:
            if decision["result"] not in {"CANDIDATE_FORMED", "REJECTED", "DEFERRED", "INDETERMINATE"}: errors.append(f"{path}: unknown decision result")
            if type(decision["reason_codes"]) is not list or not decision["reason_codes"] or len(set(decision["reason_codes"])) != len(decision["reason_codes"]): errors.append(f"{path}: invalid reason_codes")
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
    if enforce_anchors and actual_case_anchors != CASE_DIGESTS: errors.append("handoff_cases: canonical ID/order/raw inventory mismatch")

    history = fixture["handoff_candidate_history"]
    if type(history) is not list or len(history) != 2: errors.append("handoff_candidate_history: expected two revisions"); history = []
    actual_candidate_anchors: list[tuple[str, int, str]] = []
    predecessor = None
    for index, row in enumerate(history):
        path = f"handoff_candidate_history[{index}]"
        if not exact_fields(row, CANDIDATE_FIELDS, path, errors): continue
        revision = row["handoff_candidate_revision"]
        if revision != index + 1: errors.append(f"{path}: revision sequence mismatch")
        if index == 0:
            if row["predecessor_ref"] is not None or row["predecessor_fingerprint"] is not None: errors.append(f"{path}: revision 1 predecessor must be null")
        elif predecessor is not None:
            if row["predecessor_ref"] != f"synthetic://f8/handoff-candidate/001@{revision-1}" or row["predecessor_fingerprint"] != predecessor["candidate_fingerprint"]: errors.append(f"{path}: predecessor mismatch")
        for key in ["intent_candidate_fingerprint", "target_fingerprint", "payload_commitment", "context_fingerprint", "assessment_set_fingerprint", "created_event_fingerprint", "candidate_fingerprint"]:
            if not valid_hash(row[key]): errors.append(f"{path}.{key}: invalid hash")
        if row["runtime_usable"] is not False or row["command_authority"] is not False: errors.append(f"{path}: candidate authority/runtime must be false")
        expected_fp = digest(DOMAIN + ":handoff-candidate", without(row, "candidate_fingerprint"))
        if row["candidate_fingerprint"] != expected_fp: errors.append(f"{path}: candidate fingerprint mismatch")
        actual_candidate_anchors.append((row["handoff_candidate_id"], revision, row["candidate_fingerprint"]))
        predecessor = row
    if enforce_anchors and actual_candidate_anchors != CANDIDATE_ANCHORS: errors.append("handoff_candidate_history: immutable history anchors mismatch")

    ack_cases = fixture["acknowledgement_cases"]
    if type(ack_cases) is not list or len(ack_cases) != 6: errors.append("acknowledgement_cases: expected six rows"); ack_cases = []
    actual_ack_anchors: list[tuple[str, str]] = []
    for index, case in enumerate(ack_cases):
        path = f"acknowledgement_cases[{index}]"
        if not exact_fields(case, ACK_CASE_FIELDS, path, errors): continue
        raw, decision = case["raw_input"], case["claimed_decision"]
        raw_ok = exact_fields(raw, ACK_RAW_FIELDS, path + ".raw_input", errors)
        decision_ok = exact_fields(decision, ACK_DECISION_FIELDS, path + ".claimed_decision", errors)
        if raw_ok:
            if not valid_hash(raw["handoff_candidate_fingerprint"]) or not positive_int(raw["expected_assessment_revision"]): errors.append(f"{path}: invalid raw acknowledgement fields")
        if decision_ok:
            if decision["result"] not in {"NOT_SUBMITTED", "ACKNOWLEDGED_COMMITTED", "ACKNOWLEDGED_REJECTED", "ACKNOWLEDGED_INDETERMINATE"}: errors.append(f"{path}: unknown acknowledgement result")
            for key in ["command_authority", "task_write_authority", "effect_authority", "runtime_usable"]:
                if decision[key] is not False: errors.append(f"{path}: acknowledgement {key} must be false")
        if raw_ok and decision_ok:
            try:
                if decision != derive_ack(raw, rows): errors.append(f"{path}: acknowledgement not independently derived")
            except Exception as exc:
                errors.append(f"{path}: stable acknowledgement BLOCK ({type(exc).__name__})")
        if case["row_fingerprint"] != digest(DOMAIN + ":ack-case", without(case, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")
        if type(case["case_id"]) is str and type(raw) is dict: actual_ack_anchors.append((case["case_id"], plain_sha(raw)))
    if enforce_anchors and actual_ack_anchors != ACK_DIGESTS: errors.append("acknowledgement_cases: canonical ID/order/raw inventory mismatch")

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


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=no_duplicate_pairs,
        parse_constant=reject_constant,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    try:
        fixture = load_fixture(args.fixture)
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "phase": "parse", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 1
    errors = validate_fixture(fixture)
    mutation_total, mutation_rejected, mutation_failures = run_mutations(fixture) if not errors else (0, 0, [])
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
    ok = not errors and not mutation_failures and mutation_rejected == mutation_total and parser_rejected == len(parser_probes)
    result = {
        "result": "PASS" if ok else "BLOCK",
        "schema_profiles_verified": len(SCHEMA_PROFILES) if not errors else 0,
        "upstream_assessments_verified": len(fixture.get("upstream_assessments", [])) if not errors else 0,
        "handoff_cases_verified": len(fixture.get("handoff_cases", [])) if not errors else 0,
        "candidate_revisions_verified": len(fixture.get("handoff_candidate_history", [])) if not errors else 0,
        "acknowledgement_cases_verified": len(fixture.get("acknowledgement_cases", [])) if not errors else 0,
        "fully_resigned_mutations_rejected": f"{mutation_rejected}/{mutation_total}",
        "parser_probes_rejected": f"{parser_rejected}/{len(parser_probes)}",
        "real_command_count": fixture.get("boundary_assertions", {}).get("real_command_count"),
        "provider_call_count": fixture.get("boundary_assertions", {}).get("provider_call_count"),
        "external_effect_count": fixture.get("boundary_assertions", {}).get("external_effect_count"),
        "terminal_outcome": fixture.get("boundary_assertions", {}).get("terminal_outcome"),
        "root_fingerprint": fixture.get("root_fingerprint"),
        "errors": errors[:20],
        "mutation_failures": mutation_failures[:20],
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
