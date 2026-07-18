#!/usr/bin/env python3
"""Build the deterministic F7 R1 synthetic nonauthority witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = Path(
    "control-plane/registry/examples/"
    "2026-07-18-agents-os-f7-r1-home-domain-minimum-semantics-v0.1.json"
)
DOMAIN = "F7_R1_SYNTHETIC_NONAUTHORITY"
MAX_SAFE_INTEGER = 9007199254740991

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


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def sign_row(tag: str, row: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(row)
    result["row_fingerprint"] = digest(tag, result)
    return result


def derive_case(raw: dict[str, Any]) -> tuple[str, list[str], str]:
    source = raw["source_class"]
    target = raw["target_class"]
    reasons: set[str] = set()

    if raw["runtime_target_requested"]:
        reasons.add("SYNTHETIC_DOMAIN_ONLY")
    if raw["source_currentness"] == "UNKNOWN" or raw["creator_currentness"] == "UNKNOWN":
        reasons.add("UPSTREAM_CURRENTNESS_UNAVAILABLE")
    if raw["source_currentness"] == "STALE":
        reasons.add("SOURCE_NOT_CURRENT")
    if raw["creator_currentness"] == "STALE":
        reasons.add("CREATOR_NOT_CURRENT")
    if raw["explicit_choice"] is not True:
        reasons.add("EXPLICIT_CHOICE_MISSING")
    if raw["relationship_authority_requested"]:
        reasons.add("RELATIONSHIP_CANNOT_EXPAND_AUTHORITY")
    if raw["action_authority_requested"]:
        reasons.add("CANDIDATE_ONLY_NO_ACTION_AUTHORITY")

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
        reasons.add("PRESENCE_CONSENT_IS_NOT_SENSING_STATE")
        reasons.add("TARGET_WRITER_NOT_IMPLEMENTED")
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
        "TARGET_OUTSIDE_F7",
        "TARGET_WRITER_NOT_IMPLEMENTED",
        "MEMORY_CANDIDATE_IS_NOT_MEMORY",
        "PRESENCE_CONSENT_IS_NOT_SENSING_STATE",
        "GROWTH_EVENT_IS_NOT_POLICY_REVISION",
    } and not reasons & {
        "SYNTHETIC_DOMAIN_ONLY",
        "SOURCE_NOT_CURRENT",
        "CREATOR_NOT_CURRENT",
        "EXPLICIT_CHOICE_MISSING",
        "RELATIONSHIP_CANNOT_EXPAND_AUTHORITY",
        "IDENTITY_NARRATIVE_CANNOT_REWRITE_IDENTITY",
        "SESSION_CANNOT_CREATE_TASK",
        "CANDIDATE_ONLY_NO_ACTION_AUTHORITY",
    }:
        result = "DEFERRED"
    else:
        result = "REJECTED"

    ordered = [reason for reason in REASON_PRECEDENCE if reason in reasons]
    return result, ordered, ordered[0]


def raw_case(
    case_id: str,
    source_class: str,
    target_class: str,
    *,
    source_currentness: str = "CURRENT",
    creator_currentness: str = "CURRENT",
    explicit_choice: bool | None = True,
    relationship_authority_requested: bool = False,
    action_authority_requested: bool = False,
    runtime_target_requested: bool = False,
) -> dict[str, Any]:
    raw = {
        "source_class": source_class,
        "target_class": target_class,
        "source_currentness": source_currentness,
        "creator_currentness": creator_currentness,
        "explicit_choice": explicit_choice,
        "relationship_authority_requested": relationship_authority_requested,
        "action_authority_requested": action_authority_requested,
        "runtime_target_requested": runtime_target_requested,
    }
    result, reasons, primary = derive_case(raw)
    return sign_row(
        f"{DOMAIN}:decision-case",
        {
            "case_id": case_id,
            "raw_input": raw,
            "claimed_decision": {
                "result": result,
                "reason_codes": reasons,
                "primary_reason": primary,
                "action_authority": False,
            },
        },
    )


def candidate_revision(
    revision: int,
    predecessor: dict[str, Any] | None,
    source_revision: int,
    payload_label: str,
) -> dict[str, Any]:
    body = {
        "candidate_id": "home-candidate-synthetic-001",
        "candidate_revision": revision,
        "predecessor_ref": None if predecessor is None else f"home-candidate-synthetic-001@{revision - 1}",
        "predecessor_fingerprint": None if predecessor is None else predecessor["candidate_fingerprint"],
        "semantic_class": "MEMORY_CANDIDATE",
        "creator_actor_assessment_ref": "synthetic://f2/actor-assessment/nobao@1",
        "creator_actor_assessment_fingerprint": digest(DOMAIN + ":actor-assessment", {"revision": 1}),
        "source_subject_ref": "synthetic://session/content/001",
        "source_subject_revision": source_revision,
        "source_subject_fingerprint": digest(DOMAIN + ":source", {"revision": source_revision}),
        "created_event_ref": f"synthetic://event/candidate-{revision}",
        "created_event_fingerprint": digest(DOMAIN + ":event", {"sequence": revision}),
        "payload_commitment": digest(DOMAIN + ":payload", {"label": payload_label}),
    }
    body["candidate_fingerprint"] = digest(DOMAIN + ":candidate-revision", body)
    return body


def build_fixture() -> dict[str, Any]:
    authority_rows = [
        sign_row(
            f"{DOMAIN}:authority-profile",
            {
                "semantic_class": semantic_class,
                "semantic_owner": owner,
                "writer_status": status,
                "may_trigger_action_alone": False,
            },
        )
        for semantic_class, owner, status in AUTHORITY_PROFILE
    ]

    decision_cases = [
        raw_case("C01", "SESSION_CONTENT", "LIFE_STREAM_CANDIDATE"),
        raw_case("C02", "SESSION_CONTENT", "MEMORY_CANDIDATE"),
        raw_case("C03", "SESSION_CONTENT", "INTENT_CANDIDATE"),
        raw_case("C04", "SUBJECTIVE_RELATIONSHIP_MEMORY", "MEMORY_CANDIDATE"),
        raw_case("C05", "GROWTH_EVENT", "MEMORY_CANDIDATE"),
        raw_case("C06", "IDENTITY_NARRATIVE", "STABLE_IDENTITY_FACT"),
        raw_case("C07", "SUBJECTIVE_RELATIONSHIP_MEMORY", "FORMAL_RELATIONSHIP_FACT"),
        raw_case("C08", "SESSION_CONTENT", "TASK_CANONICAL_FACT"),
        raw_case("C09", "MEMORY_CANDIDATE", "MEMORY_CONTENT"),
        raw_case("C10", "INTENT_CANDIDATE", "ORCHESTRATOR_COMMAND"),
        raw_case("C11", "PRESENCE_CONSENT", "DEVICE_SENSING_STATE"),
        raw_case("C12", "GROWTH_EVENT", "BEHAVIOR_POLICY_REVISION"),
        raw_case("C13", "SUBJECTIVE_RELATIONSHIP_MEMORY", "MEMORY_CANDIDATE", relationship_authority_requested=True),
        raw_case("C14", "SESSION_CONTENT", "MEMORY_CANDIDATE", source_currentness="STALE"),
        raw_case("C15", "SESSION_CONTENT", "MEMORY_CANDIDATE", creator_currentness="STALE"),
        raw_case("C16", "SESSION_CONTENT", "MEMORY_CANDIDATE", explicit_choice=None),
        raw_case("C17", "SESSION_CONTENT", "MEMORY_CANDIDATE", source_currentness="UNKNOWN"),
        raw_case("C18", "SESSION_CONTENT", "MEMORY_CANDIDATE", action_authority_requested=True),
        raw_case("C19", "SESSION_CONTENT", "MEMORY_CANDIDATE", runtime_target_requested=True),
        raw_case(
            "C20",
            "SESSION_CONTENT",
            "TASK_CANONICAL_FACT",
            source_currentness="STALE",
            creator_currentness="STALE",
            explicit_choice=None,
            action_authority_requested=True,
        ),
    ]

    gaps = [
        sign_row(f"{DOMAIN}:gap-disposition", {"gap_id": gap_id, "disposition": disposition})
        for gap_id, disposition in GAP_DISPOSITIONS
    ]

    revision_1 = candidate_revision(1, None, 1, "candidate-v1")
    revision_2 = candidate_revision(2, revision_1, 2, "candidate-v2")

    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f7-home-domain-minimum-semantics-witness.v0.1",
        "contract_id": "F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R1",
        "environment": "SYNTHETIC_TEST",
        "domain_tag": DOMAIN,
        "runtime_usable": False,
        "authority_profile": authority_rows,
        "decision_cases": decision_cases,
        "candidate_history": [revision_1, revision_2],
        "gap_dispositions": gaps,
        "relationship_witness": {
            "formal_mutation_available": False,
            "subjective_memory_can_bind_other_party": False,
            "relationship_can_expand_authority": False,
            "target_status": "TARGET_NOT_IMPLEMENTED",
        },
        "presence_witness": {
            "policy_creates_consent": False,
            "consent_proves_sensing": False,
            "sensing_authorizes_recording": False,
            "sensing_creates_memory": False,
            "sensor_or_recording_implementation_present": False,
        },
        "boundary_assertions": {
            "accepted_real_identity_count": 0,
            "real_session_content_count": 0,
            "private_raw_memory_count": 0,
            "formal_memory_write_count": 0,
            "real_relationship_mutation_count": 0,
            "sensing_or_recording_count": 0,
            "Task_or_Command_mutation_count": 0,
            "database_write_count": 0,
            "provider_call_count": 0,
            "external_effect_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        },
    }

    sections = [
        "authority_profile",
        "decision_cases",
        "candidate_history",
        "gap_dispositions",
        "relationship_witness",
        "presence_witness",
        "boundary_assertions",
    ]
    fixture["section_fingerprints"] = {
        name: digest(f"{DOMAIN}:section:{name}", fixture[name]) for name in sections
    }
    fixture["root_fingerprint"] = digest(f"{DOMAIN}:root", fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    fixture = build_fixture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
