#!/usr/bin/env python3
"""Build the deterministic F8 R1 synthetic nonauthority witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path(
    "control-plane/registry/examples/"
    "2026-07-19-agents-os-f8-r1-home-to-orchestrator-minimum-interface-v0.1.json"
)
DOMAIN = "F8_R1_SYNTHETIC_NONAUTHORITY"
F3_MANIFEST_SHA256 = "3075cda63fcb2c7937cb800a3bc09cc830d17e2f98b899828db15e09ab9f79ff"

CONSUMER_ROLES = [
    "f7_intent_currentness",
    "actor_identity",
    "principal_binding",
    "responsibility",
    "f3_readiness",
    "pbl_currentness",
    "jenn_requirement",
    "jenn_exact_decision",
]

REASON_PRECEDENCE = [
    "UNKNOWN_OR_MALFORMED_INPUT",
    "SYNTHETIC_DOMAIN_VIOLATION",
    "EXPLICIT_ACTION_CHOICE_MISSING",
    "DIRECT_TASK_WRITE_FORBIDDEN",
    "DIRECT_COMMAND_COMMIT_FORBIDDEN",
    "EFFECT_EXECUTION_FORBIDDEN",
    "RELATIONSHIP_OR_TRUST_CANNOT_EXPAND_AUTHORITY",
    "PBL_NO_MATCH_IS_NOT_PERMISSION",
    "INTENT_SEMANTIC_CLASS_MISMATCH",
    "TARGET_KIND_OUTSIDE_F8",
    "CONTEXT_FINGERPRINT_MISMATCH",
    "ASSESSMENT_MISSING_OR_UNRESOLVABLE",
    "ASSESSMENT_REVISION_MISMATCH",
    "ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH",
    "ASSESSMENT_WATERMARK_BEHIND",
    "UPSTREAM_ASSESSMENT_NOT_CURRENT",
    "UPSTREAM_CURRENTNESS_UNAVAILABLE",
    "F7_INTENT_NOT_CURRENT",
    "ACTOR_IDENTITY_NOT_ACTIVE",
    "PRINCIPAL_BINDING_NOT_ACTIVE",
    "RESPONSIBILITY_NOT_ACTIVE",
    "F3_NOT_READY",
    "PBL_PROHIBITED",
    "EXACT_JENN_DECISION_MISSING_OR_INVALID",
    "F3_INTERFACE_REQUIREMENT_UNACCEPTED",
    "VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE",
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


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def signed(tag: str, row: dict[str, Any], field: str = "row_fingerprint") -> dict[str, Any]:
    result = copy.deepcopy(row)
    result[field] = digest(tag, result)
    return result


def context_fingerprint(raw: dict[str, Any]) -> str:
    value = {
        key: raw[key]
        for key in [
            "intent_candidate_ref", "intent_candidate_revision", "intent_candidate_fingerprint",
            "intent_semantic_class", "creator_actor_ref", "creator_actor_revision",
            "creator_actor_fingerprint", "principal_ref", "principal_revision",
            "principal_fingerprint", "target_kind", "target_ref", "target_revision",
            "target_fingerprint", "payload_schema_ref", "payload_schema_fingerprint",
            "payload_commitment", "explicit_action_choice", "trusted_event_sequence",
        ]
    }
    return digest(DOMAIN + ":handoff-context", value)


def assessment(
    assessment_id: str,
    owner: str,
    kind: str,
    subject_ref: str,
    subject_revision: int,
    subject_fingerprint: str,
    result: str,
    *,
    context: str | None = None,
    current: bool = True,
    event_sequence: int = 100,
) -> dict[str, Any]:
    return signed(
        DOMAIN + ":assessment",
        {
            "assessment_id": assessment_id,
            "assessment_revision": 1,
            "owner_contract": owner,
            "assessment_kind": kind,
            "subject_ref": subject_ref,
            "subject_revision": subject_revision,
            "subject_fingerprint": subject_fingerprint,
            "context_fingerprint": context,
            "result": result,
            "based_on_event_sequence": event_sequence,
            "is_current_head": current,
        },
    )


def consumer(assessment_id: str | None, revision: int | None = 1) -> dict[str, Any]:
    return {
        "assessment_id": assessment_id,
        "expected_assessment_revision": None if assessment_id is None else revision,
    }


def assessment_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["assessment_id"]: row for row in rows}


def resolve_case(raw: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[str, list[str], str]:
    reasons: set[str] = set()
    index = assessment_index(rows)

    if raw["environment"] != "SYNTHETIC_TEST" or raw["runtime_usable_requested"]:
        reasons.add("SYNTHETIC_DOMAIN_VIOLATION")
    if raw["explicit_action_choice"] is not True:
        reasons.add("EXPLICIT_ACTION_CHOICE_MISSING")
    if raw["direct_task_write_requested"]:
        reasons.add("DIRECT_TASK_WRITE_FORBIDDEN")
    if raw["direct_command_commit_requested"]:
        reasons.add("DIRECT_COMMAND_COMMIT_FORBIDDEN")
    if raw["effect_execution_requested"]:
        reasons.add("EFFECT_EXECUTION_FORBIDDEN")
    if raw["relationship_or_trust_used_as_authority"]:
        reasons.add("RELATIONSHIP_OR_TRUST_CANNOT_EXPAND_AUTHORITY")
    if raw["pbl_no_match_used_as_sufficient"]:
        reasons.add("PBL_NO_MATCH_IS_NOT_PERMISSION")
    if raw["intent_semantic_class"] != "INTENT_CANDIDATE":
        reasons.add("INTENT_SEMANTIC_CLASS_MISMATCH")
    if raw["target_kind"] != "ORCHESTRATOR_INTAKE_CANDIDATE":
        reasons.add("TARGET_KIND_OUTSIDE_F8")
    expected_context = context_fingerprint(raw)
    if raw["context_fingerprint"] != expected_context:
        reasons.add("CONTEXT_FINGERPRINT_MISMATCH")

    resolved: dict[str, dict[str, Any] | None] = {}
    for role in CONSUMER_ROLES:
        binding = raw["assessment_consumers"][role]
        assessment_id = binding["assessment_id"]
        if assessment_id is None:
            resolved[role] = None
            if role != "jenn_exact_decision":
                reasons.add("ASSESSMENT_MISSING_OR_UNRESOLVABLE")
            continue
        row = index.get(assessment_id)
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
        "f7_intent_currentness": (
            raw["intent_candidate_ref"], raw["intent_candidate_revision"],
            raw["intent_candidate_fingerprint"], None,
        ),
        "actor_identity": (
            raw["creator_actor_ref"], raw["creator_actor_revision"],
            raw["creator_actor_fingerprint"], None,
        ),
        "principal_binding": (
            raw["principal_ref"], raw["principal_revision"], raw["principal_fingerprint"], None,
        ),
        "responsibility": (
            raw["target_ref"], raw["target_revision"], raw["target_fingerprint"],
            raw["context_fingerprint"],
        ),
        "f3_readiness": (
            "F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE",
            4, F3_MANIFEST_SHA256, None,
        ),
        "pbl_currentness": (
            "agents-os.prohibited-behavior-list.current", 1,
            digest(DOMAIN + ":pbl", {"revision": 1}), None,
        ),
        "jenn_requirement": (
            raw["target_ref"], raw["target_revision"], raw["target_fingerprint"],
            raw["context_fingerprint"],
        ),
        "jenn_exact_decision": (
            raw["target_ref"], raw["target_revision"], raw["target_fingerprint"],
            raw["context_fingerprint"],
        ),
    }
    for role, expected in exact_subjects.items():
        row = resolved.get(role)
        if row is None:
            continue
        actual = (
            row["subject_ref"], row["subject_revision"], row["subject_fingerprint"],
            row["context_fingerprint"],
        )
        if actual != expected:
            reasons.add("ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH")

    expected_kinds = {
        "f7_intent_currentness": ("F7", "F7_INTENT_CURRENTNESS"),
        "actor_identity": ("F2", "F2_ACTOR_IDENTITY"),
        "principal_binding": ("F2", "F2_PRINCIPAL_BINDING"),
        "responsibility": ("F2", "F2_RESPONSIBILITY"),
        "f3_readiness": ("F3", "F3_RESIDENT_READINESS"),
        "pbl_currentness": ("POLICY", "PBL_CURRENTNESS"),
        "jenn_requirement": ("POLICY", "JENN_REQUIREMENT"),
        "jenn_exact_decision": ("JENN_DECISION", "JENN_EXACT_DECISION"),
    }
    for role, (owner, kind) in expected_kinds.items():
        row = resolved.get(role)
        if row is not None and (row["owner_contract"], row["assessment_kind"]) != (owner, kind):
            reasons.add("ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH")

    result_checks = {
        "f7_intent_currentness": ("CURRENT_ACCEPTED", "F7_INTENT_NOT_CURRENT"),
        "actor_identity": ("ACTIVE", "ACTOR_IDENTITY_NOT_ACTIVE"),
        "principal_binding": ("ACTIVE", "PRINCIPAL_BINDING_NOT_ACTIVE"),
        "responsibility": ("ACTIVE", "RESPONSIBILITY_NOT_ACTIVE"),
        "f3_readiness": ("READY_CONTINUOUS", "F3_NOT_READY"),
        "pbl_currentness": ("CURRENT_NO_MATCH", "PBL_PROHIBITED"),
    }
    for role, (favorable, reason) in result_checks.items():
        row = resolved.get(role)
        if row is not None and row["result"] not in {favorable, "INDETERMINATE"}:
            reasons.add(reason)

    requirement = resolved.get("jenn_requirement")
    if requirement is not None and requirement["result"] == "EXACT_DECISION_REQUIRED":
        decision = resolved.get("jenn_exact_decision")
        if decision is None or decision["result"] != "CURRENT_ACCEPTED":
            reasons.add("EXACT_JENN_DECISION_MISSING_OR_INVALID")
        elif (
            decision["subject_ref"], decision["subject_revision"],
            decision["subject_fingerprint"], decision["context_fingerprint"]
        ) != exact_subjects["jenn_exact_decision"]:
            reasons.add("EXACT_JENN_DECISION_MISSING_OR_INVALID")

    structural_rejects = {
        "SYNTHETIC_DOMAIN_VIOLATION", "EXPLICIT_ACTION_CHOICE_MISSING",
        "DIRECT_TASK_WRITE_FORBIDDEN", "DIRECT_COMMAND_COMMIT_FORBIDDEN",
        "EFFECT_EXECUTION_FORBIDDEN", "RELATIONSHIP_OR_TRUST_CANNOT_EXPAND_AUTHORITY",
        "PBL_NO_MATCH_IS_NOT_PERMISSION", "INTENT_SEMANTIC_CLASS_MISMATCH",
        "TARGET_KIND_OUTSIDE_F8", "CONTEXT_FINGERPRINT_MISMATCH",
        "ASSESSMENT_REVISION_MISMATCH", "ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH",
        "ASSESSMENT_WATERMARK_BEHIND",
        "UPSTREAM_ASSESSMENT_NOT_CURRENT", "F7_INTENT_NOT_CURRENT",
        "ACTOR_IDENTITY_NOT_ACTIVE", "PRINCIPAL_BINDING_NOT_ACTIVE",
        "RESPONSIBILITY_NOT_ACTIVE", "F3_NOT_READY", "PBL_PROHIBITED",
        "EXACT_JENN_DECISION_MISSING_OR_INVALID",
    }
    if reasons & structural_rejects:
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
    return result, ordered, ordered[0]


def claimed_decision(raw: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    result, reasons, primary = resolve_case(raw, rows)
    return {
        "result": result,
        "reason_codes": reasons,
        "primary_reason": primary,
        "command_authority": False,
        "task_write_authority": False,
        "effect_authority": False,
        "runtime_usable": False,
        "F3_recheck_required": True,
        "F3_command_ref": None,
        "F3_intake_ref": None,
    }


def make_case(case_id: str, raw: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    raw = copy.deepcopy(raw)
    return signed(
        DOMAIN + ":handoff-case",
        {"case_id": case_id, "raw_input": raw, "claimed_decision": claimed_decision(raw, rows)},
    )


def make_candidate(
    revision: int,
    predecessor: dict[str, Any] | None,
    raw: dict[str, Any],
    payload_commitment: str,
) -> dict[str, Any]:
    consumers = raw["assessment_consumers"]
    assessment_set = [
        [role, consumers[role]["assessment_id"], consumers[role]["expected_assessment_revision"]]
        for role in CONSUMER_ROLES
    ]
    body = {
        "handoff_candidate_id": "synthetic://f8/handoff-candidate/001",
        "handoff_candidate_revision": revision,
        "predecessor_ref": None if predecessor is None else f"synthetic://f8/handoff-candidate/001@{revision-1}",
        "predecessor_fingerprint": None if predecessor is None else predecessor["candidate_fingerprint"],
        "intent_candidate_ref": raw["intent_candidate_ref"],
        "intent_candidate_revision": raw["intent_candidate_revision"],
        "intent_candidate_fingerprint": raw["intent_candidate_fingerprint"],
        "target_ref": raw["target_ref"],
        "target_revision": raw["target_revision"],
        "target_fingerprint": raw["target_fingerprint"],
        "payload_commitment": payload_commitment,
        "context_fingerprint": raw["context_fingerprint"],
        "assessment_set_fingerprint": digest(DOMAIN + ":assessment-set", assessment_set),
        "created_event_ref": f"synthetic://f8/event/handoff-candidate-{revision}",
        "created_event_fingerprint": digest(DOMAIN + ":event", {"sequence": 200 + revision}),
        "runtime_usable": False,
        "command_authority": False,
    }
    body["candidate_fingerprint"] = digest(DOMAIN + ":handoff-candidate", body)
    return body


def derive_ack(raw: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    index = assessment_index(rows)
    row = index.get(raw["F3_outcome_assessment_id"])
    reasons: list[str]
    if row is None:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_MISSING"]
    elif raw["expected_assessment_revision"] != row["assessment_revision"]:
        result, reasons = "ACKNOWLEDGED_INDETERMINATE", ["F3_OUTCOME_REVISION_MISMATCH"]
    elif (
        row["owner_contract"] != "F3"
        or row["assessment_kind"] != "F3_INTAKE_OUTCOME"
        or row["subject_ref"] != raw["handoff_candidate_ref"]
        or row["subject_fingerprint"] != raw["handoff_candidate_fingerprint"]
    ):
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
        "result": result,
        "reason_codes": reasons,
        "primary_reason": reasons[0],
        "command_authority": False,
        "task_write_authority": False,
        "effect_authority": False,
        "runtime_usable": False,
    }


def make_ack_case(case_id: str, raw: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    return signed(
        DOMAIN + ":ack-case",
        {"case_id": case_id, "raw_input": raw, "claimed_decision": derive_ack(raw, rows)},
    )


def build_fixture() -> dict[str, Any]:
    intent_ref = "synthetic://f7/intent-candidate/001"
    intent_fp = digest(DOMAIN + ":intent", {"ref": intent_ref, "revision": 2, "class": "INTENT_CANDIDATE"})
    actor_ref = "synthetic://f2/actor/nobao"
    actor_fp = digest(DOMAIN + ":actor", {"ref": actor_ref, "revision": 1})
    principal_ref = "synthetic://f2/principal/nobao-session"
    principal_fp = digest(DOMAIN + ":principal", {"ref": principal_ref, "revision": 1})
    target_ref = "synthetic://orchestrator/intake-scope/home-intent"
    target_fp = digest(DOMAIN + ":target", {"ref": target_ref, "revision": 1})
    payload_schema_ref = "synthetic://f8/schema/home-intent-payload/v0.1"
    payload_schema_fp = digest(DOMAIN + ":payload-schema", {"ref": payload_schema_ref})
    payload_commitment = digest(DOMAIN + ":payload", {"intent": "synthetic-action-request", "scope": "fixture-only"})

    base_raw: dict[str, Any] = {
        "environment": "SYNTHETIC_TEST",
        "intent_candidate_ref": intent_ref,
        "intent_candidate_revision": 2,
        "intent_candidate_fingerprint": intent_fp,
        "intent_semantic_class": "INTENT_CANDIDATE",
        "creator_actor_ref": actor_ref,
        "creator_actor_revision": 1,
        "creator_actor_fingerprint": actor_fp,
        "principal_ref": principal_ref,
        "principal_revision": 1,
        "principal_fingerprint": principal_fp,
        "target_kind": "ORCHESTRATOR_INTAKE_CANDIDATE",
        "target_ref": target_ref,
        "target_revision": 1,
        "target_fingerprint": target_fp,
        "payload_schema_ref": payload_schema_ref,
        "payload_schema_fingerprint": payload_schema_fp,
        "payload_commitment": payload_commitment,
        "explicit_action_choice": True,
        "direct_task_write_requested": False,
        "direct_command_commit_requested": False,
        "effect_execution_requested": False,
        "relationship_or_trust_used_as_authority": False,
        "pbl_no_match_used_as_sufficient": False,
        "production_profile_requested": False,
        "runtime_usable_requested": False,
        "trusted_event_sequence": 100,
        "context_fingerprint": "",
        "assessment_consumers": {},
    }
    base_raw["context_fingerprint"] = context_fingerprint(base_raw)

    pbl_ref = "agents-os.prohibited-behavior-list.current"
    pbl_fp = digest(DOMAIN + ":pbl", {"revision": 1})
    other_target_ref = "synthetic://orchestrator/intake-scope/other"
    other_target_fp = digest(DOMAIN + ":target", {"ref": other_target_ref, "revision": 1})
    other_context = digest(DOMAIN + ":handoff-context", {"other": True})

    rows = [
        assessment("A-F7-CURRENT", "F7", "F7_INTENT_CURRENTNESS", intent_ref, 2, intent_fp, "CURRENT_ACCEPTED"),
        assessment("A-F7-STALE", "F7", "F7_INTENT_CURRENTNESS", intent_ref, 2, intent_fp, "STALE", current=False),
        assessment("A-F7-UNKNOWN", "F7", "F7_INTENT_CURRENTNESS", intent_ref, 2, intent_fp, "INDETERMINATE"),
        assessment("A-ACTOR-ACTIVE", "F2", "F2_ACTOR_IDENTITY", actor_ref, 1, actor_fp, "ACTIVE"),
        assessment("A-ACTOR-INACTIVE", "F2", "F2_ACTOR_IDENTITY", actor_ref, 1, actor_fp, "INACTIVE"),
        assessment("A-ACTOR-BEHIND", "F2", "F2_ACTOR_IDENTITY", actor_ref, 1, actor_fp, "ACTIVE", event_sequence=99),
        assessment("A-PRINCIPAL-ACTIVE", "F2", "F2_PRINCIPAL_BINDING", principal_ref, 1, principal_fp, "ACTIVE"),
        assessment("A-PRINCIPAL-INACTIVE", "F2", "F2_PRINCIPAL_BINDING", principal_ref, 1, principal_fp, "INACTIVE"),
        assessment("A-RESP-ACTIVE", "F2", "F2_RESPONSIBILITY", target_ref, 1, target_fp, "ACTIVE", context=base_raw["context_fingerprint"]),
        assessment("A-RESP-INACTIVE", "F2", "F2_RESPONSIBILITY", target_ref, 1, target_fp, "INACTIVE", context=base_raw["context_fingerprint"]),
        assessment("A-RESP-MISMATCH", "F2", "F2_RESPONSIBILITY", other_target_ref, 1, other_target_fp, "ACTIVE", context=other_context),
        assessment("A-F3-READY", "F3", "F3_RESIDENT_READINESS", "F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE", 4, F3_MANIFEST_SHA256, "READY_CONTINUOUS"),
        assessment("A-F3-UNKNOWN", "F3", "F3_RESIDENT_READINESS", "F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE", 4, F3_MANIFEST_SHA256, "INDETERMINATE"),
        assessment("A-PBL-CLEAR", "POLICY", "PBL_CURRENTNESS", pbl_ref, 1, pbl_fp, "CURRENT_NO_MATCH"),
        assessment("A-PBL-PROHIBITED", "POLICY", "PBL_CURRENTNESS", pbl_ref, 1, pbl_fp, "PROHIBITED"),
        assessment("A-JREQ-NONE", "POLICY", "JENN_REQUIREMENT", target_ref, 1, target_fp, "NO_EXACT_DECISION_REQUIRED", context=base_raw["context_fingerprint"]),
        assessment("A-JREQ-REQUIRED", "POLICY", "JENN_REQUIREMENT", target_ref, 1, target_fp, "EXACT_DECISION_REQUIRED", context=base_raw["context_fingerprint"]),
        assessment("A-JDECISION-CURRENT", "JENN_DECISION", "JENN_EXACT_DECISION", target_ref, 1, target_fp, "CURRENT_ACCEPTED", context=base_raw["context_fingerprint"]),
        assessment("A-JDECISION-MISMATCH", "JENN_DECISION", "JENN_EXACT_DECISION", other_target_ref, 1, other_target_fp, "CURRENT_ACCEPTED", context=other_context),
    ]

    base_raw["assessment_consumers"] = {
        "f7_intent_currentness": consumer("A-F7-CURRENT"),
        "actor_identity": consumer("A-ACTOR-ACTIVE"),
        "principal_binding": consumer("A-PRINCIPAL-ACTIVE"),
        "responsibility": consumer("A-RESP-ACTIVE"),
        "f3_readiness": consumer("A-F3-READY"),
        "pbl_currentness": consumer("A-PBL-CLEAR"),
        "jenn_requirement": consumer("A-JREQ-NONE"),
        "jenn_exact_decision": consumer(None),
    }

    def variant(**changes: Any) -> dict[str, Any]:
        raw = copy.deepcopy(base_raw)
        consumer_changes = changes.pop("consumer_changes", {})
        for key, value in changes.items():
            raw[key] = value
        for role, value in consumer_changes.items():
            raw["assessment_consumers"][role] = value
        return raw

    wrong_intent_fp = digest(DOMAIN + ":intent", {"ref": intent_ref, "revision": 2, "changed": True})
    wrong_payload = digest(DOMAIN + ":payload", {"changed": True})
    cases_raw = [
        variant(),
        variant(intent_semantic_class="SESSION_CONTENT"),
        variant(explicit_action_choice=False),
        variant(direct_task_write_requested=True),
        variant(direct_command_commit_requested=True),
        variant(effect_execution_requested=True),
        variant(relationship_or_trust_used_as_authority=True),
        variant(pbl_no_match_used_as_sufficient=True),
        variant(consumer_changes={"f7_intent_currentness": consumer("A-F7-UNKNOWN")}),
        variant(consumer_changes={"f7_intent_currentness": consumer("A-F7-STALE")}),
        variant(consumer_changes={"actor_identity": consumer("A-ACTOR-INACTIVE")}),
        variant(consumer_changes={"principal_binding": consumer("A-PRINCIPAL-INACTIVE")}),
        variant(consumer_changes={"responsibility": consumer("A-RESP-INACTIVE")}),
        variant(consumer_changes={"responsibility": consumer("A-RESP-MISMATCH")}),
        variant(consumer_changes={"f3_readiness": consumer("A-F3-UNKNOWN")}),
        variant(consumer_changes={"pbl_currentness": consumer("A-PBL-PROHIBITED")}),
        variant(consumer_changes={"jenn_requirement": consumer("A-JREQ-REQUIRED"), "jenn_exact_decision": consumer(None)}),
        variant(consumer_changes={"jenn_requirement": consumer("A-JREQ-REQUIRED"), "jenn_exact_decision": consumer("A-JDECISION-MISMATCH")}),
        variant(target_kind="TASK_CANONICAL_FACT"),
        variant(payload_commitment=wrong_payload),
        variant(production_profile_requested=True),
        variant(consumer_changes={"actor_identity": consumer("A-ACTOR-ACTIVE", 2)}),
        variant(intent_candidate_fingerprint=wrong_intent_fp),
        variant(runtime_usable_requested=True),
        variant(consumer_changes={"actor_identity": consumer("A-ACTOR-BEHIND")}),
    ]
    cases = [make_case(f"H{index:02d}", raw, rows) for index, raw in enumerate(cases_raw, start=1)]

    candidate_1 = make_candidate(1, None, base_raw, payload_commitment)
    candidate_2 = make_candidate(2, candidate_1, base_raw, payload_commitment)
    candidates = [candidate_1, candidate_2]

    candidate_ref = "synthetic://f8/handoff-candidate/001@2"
    rows.extend([
        assessment("A-F3-OUTCOME-NOT-SUBMITTED", "F3", "F3_INTAKE_OUTCOME", candidate_ref, 2, candidate_2["candidate_fingerprint"], "NOT_SUBMITTED"),
        assessment("A-F3-OUTCOME-COMMITTED", "F3", "F3_INTAKE_OUTCOME", candidate_ref, 2, candidate_2["candidate_fingerprint"], "SYNTHETIC_TEST_COMMITTED"),
        assessment("A-F3-OUTCOME-REJECTED", "F3", "F3_INTAKE_OUTCOME", candidate_ref, 2, candidate_2["candidate_fingerprint"], "REJECTED"),
        assessment("A-F3-OUTCOME-INDETERMINATE", "F3", "F3_INTAKE_OUTCOME", candidate_ref, 2, candidate_2["candidate_fingerprint"], "INDETERMINATE"),
        assessment("A-F3-OUTCOME-STALE", "F3", "F3_INTAKE_OUTCOME", candidate_ref, 2, candidate_2["candidate_fingerprint"], "SYNTHETIC_TEST_COMMITTED", current=False),
        assessment("A-F3-OUTCOME-MISMATCH", "F3", "F3_INTAKE_OUTCOME", "synthetic://f8/handoff-candidate/other@1", 1, digest(DOMAIN + ":other-candidate", {"revision": 1}), "SYNTHETIC_TEST_COMMITTED"),
    ])

    def ack_raw(assessment_id: str, revision: int = 1) -> dict[str, Any]:
        return {
            "handoff_candidate_ref": candidate_ref,
            "handoff_candidate_fingerprint": candidate_2["candidate_fingerprint"],
            "F3_outcome_assessment_id": assessment_id,
            "expected_assessment_revision": revision,
        }

    ack_cases = [
        make_ack_case("A01", ack_raw("A-F3-OUTCOME-NOT-SUBMITTED"), rows),
        make_ack_case("A02", ack_raw("A-F3-OUTCOME-COMMITTED"), rows),
        make_ack_case("A03", ack_raw("A-F3-OUTCOME-REJECTED"), rows),
        make_ack_case("A04", ack_raw("A-F3-OUTCOME-INDETERMINATE"), rows),
        make_ack_case("A05", ack_raw("A-F3-OUTCOME-STALE"), rows),
        make_ack_case("A06", ack_raw("A-F3-OUTCOME-MISMATCH"), rows),
    ]

    prospective = signed(
        DOMAIN + ":prospective-f3-interface",
        {
            "requirement_id": "F3_HOME_INTENT_HANDOFF_COMMAND_TYPE",
            "owner": "F3",
            "status": "UNACCEPTED_DOWNSTREAM_REQUIREMENT",
            "usable_in_runtime": False,
            "synthetic_fixture_only": True,
            "required_F3_contract": "F3_RESIDENT_SINGLETON_NAPI_IDENTITY_CONTINUITY_V0_1_R4_ATOMIC_BUNDLE",
            "required_submission_interface": "agents-os.command-submission.v0.1",
            "required_intake_results": ["COMMITTED", "INDETERMINATE", "REJECTED"],
            "F8_may_mint_command": False,
            "F8_may_mint_authentication": False,
            "F8_may_commit_intake": False,
        },
    )

    schema_inventory = [
        signed(
            DOMAIN + ":schema-profile",
            {"schema_name": name, "exact_fields": fields, "unknown_fields_policy": "REJECT"},
        )
        for name, fields in SCHEMA_PROFILES.items()
    ]
    boundary = {
        "real_home_fact_count": 0,
        "real_task_count": 0,
        "real_command_count": 0,
        "private_raw_memory_count": 0,
        "runtime_activation_count": 0,
        "database_write_count": 0,
        "provider_call_count": 0,
        "sensing_or_recording_count": 0,
        "external_effect_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }

    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f8-r1.synthetic-nonauthority-witness.v0.1",
        "contract_id": "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R1",
        "environment": "SYNTHETIC_TEST",
        "domain_tag": DOMAIN,
        "runtime_usable": False,
        "schema_inventory": schema_inventory,
        "prospective_f3_interface_requirement": prospective,
        "upstream_assessments": rows,
        "handoff_cases": cases,
        "handoff_candidate_history": candidates,
        "acknowledgement_cases": ack_cases,
        "boundary_assertions": boundary,
        "section_fingerprints": {},
        "root_fingerprint": "",
    }
    section_names = [
        "schema_inventory", "prospective_f3_interface_requirement", "upstream_assessments",
        "handoff_cases", "handoff_candidate_history", "acknowledgement_cases",
        "boundary_assertions",
    ]
    fixture["section_fingerprints"] = {
        name: digest(DOMAIN + ":section:" + name, fixture[name]) for name in section_names
    }
    root_body = copy.deepcopy(fixture)
    root_body.pop("root_fingerprint")
    fixture["root_fingerprint"] = digest(DOMAIN + ":root", root_body)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    fixture = build_fixture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "result": "PASS",
        "output": str(args.output),
        "handoff_case_count": len(fixture["handoff_cases"]),
        "assessment_count": len(fixture["upstream_assessments"]),
        "acknowledgement_case_count": len(fixture["acknowledgement_cases"]),
        "root_fingerprint": fixture["root_fingerprint"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
