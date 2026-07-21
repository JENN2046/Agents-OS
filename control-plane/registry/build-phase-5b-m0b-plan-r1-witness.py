#!/usr/bin/env python3
"""Build the deterministic synthetic Phase 5B M0-B Plan R1 witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


SAFE_MAX = 9_007_199_254_740_991
CASE_DOMAIN = "PHASE_5B_M0B_PLAN_R1_CASE_V1"
SECTION_DOMAIN = "PHASE_5B_M0B_PLAN_R1_SECTION_V1"
ROOT_DOMAIN = "PHASE_5B_M0B_PLAN_R1_ROOT_V1"

REASON_PRECEDENCE = [
    "UNKNOWN_OR_MALFORMED_INPUT",
    "PRODUCTION_PROFILE_FORBIDDEN",
    "RAW_CONTENT_PERSISTENCE_FORBIDDEN",
    "FORMAL_MEMORY_WRITE_FORBIDDEN",
    "DIRECT_TASK_WRITE_FORBIDDEN",
    "DIRECT_COMMAND_COMMIT_FORBIDDEN",
    "RELATIONSHIP_CANNOT_EXPAND_AUTHORITY",
    "PBL_NO_MATCH_IS_NOT_PERMISSION",
    "UPSTREAM_CURRENTNESS_UNAVAILABLE",
    "ORDINARY_THOUGHT_CANNOT_PROMOTE",
    "EXPLICIT_SESSION_BRANCH_MISSING",
    "EXPLICIT_LIFE_STREAM_CHOICE_MISSING",
    "EXPLICIT_MEMORY_CHOICE_MISSING",
    "EXPLICIT_INTENT_CHOICE_MISSING",
    "F8_HANDOFF_REJECTED",
    "F8_HANDOFF_INDETERMINATE",
    "F3_NOT_SUBMITTED",
    "F3_REJECTED",
    "F3_INDETERMINATE",
    "VALID_NO_PROMOTION",
    "VALID_LIFE_STREAM_CANDIDATE",
    "VALID_OBSERVE",
    "VALID_DISCARD",
    "VALID_MEMORY_CANDIDATE",
    "VALID_INTENT_CANDIDATE",
    "VALID_HANDOFF_CANDIDATE",
    "VALID_F3_COMMIT_ACKNOWLEDGEMENT",
]

RAW_FIELDS = {
    "source_kind",
    "branch_choice",
    "explicit_life_stream_choice",
    "life_stream_action",
    "explicit_memory_choice",
    "explicit_intent_choice",
    "request_f8_handoff",
    "f8_result",
    "f3_outcome",
    "direct_task_write_requested",
    "direct_command_commit_requested",
    "relationship_as_authority",
    "pbl_no_match_as_sufficient",
    "raw_content_persist_requested",
    "formal_memory_write_requested",
    "production_profile_requested",
    "upstream_current",
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def fingerprint(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("ascii") + b"\0" + canonical_bytes(value)).hexdigest()


def base_input() -> dict[str, Any]:
    return {
        "source_kind": "SESSION_CONTENT",
        "branch_choice": "EPHEMERAL_ONLY",
        "explicit_life_stream_choice": False,
        "life_stream_action": "NONE",
        "explicit_memory_choice": False,
        "explicit_intent_choice": False,
        "request_f8_handoff": False,
        "f8_result": "NOT_EVALUATED",
        "f3_outcome": "NOT_SUBMITTED",
        "direct_task_write_requested": False,
        "direct_command_commit_requested": False,
        "relationship_as_authority": False,
        "pbl_no_match_as_sufficient": False,
        "raw_content_persist_requested": False,
        "formal_memory_write_requested": False,
        "production_profile_requested": False,
        "upstream_current": True,
    }


def raw(**overrides: Any) -> dict[str, Any]:
    value = base_input()
    value.update(overrides)
    if set(value) != RAW_FIELDS:
        raise AssertionError("builder raw input inventory drift")
    return value


def case_specs() -> list[tuple[str, dict[str, Any]]]:
    promote = {
        "branch_choice": "PROPOSE_LIFE_STREAM_CANDIDATE",
        "explicit_life_stream_choice": True,
    }
    intent = {
        **promote,
        "life_stream_action": "PROPOSE_INTENT_CANDIDATE",
        "explicit_intent_choice": True,
    }
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


def output(result: str, reasons: list[str], *, life: int = 0, memory: int = 0, intent: int = 0, handoff: int = 0, f3: int = 0) -> dict[str, Any]:
    ordered = [reason for reason in REASON_PRECEDENCE if reason in set(reasons)]
    return {
        "result": result,
        "reason_codes": ordered,
        "primary_reason": ordered[0],
        "life_stream_candidate_count": life,
        "memory_candidate_count": memory,
        "intent_candidate_count": intent,
        "handoff_candidate_count": handoff,
        "synthetic_f3_command_count": f3,
        "command_owner": "F3" if f3 else None,
        "goal_write_count": 0,
        "task_write_count": 0,
        "formal_memory_write_count": 0,
        "home_command_write_count": 0,
        "effect_count": 0,
        "runtime_usable": False,
    }


def derive_case(value: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    structural = [
        ("production_profile_requested", "PRODUCTION_PROFILE_FORBIDDEN"),
        ("raw_content_persist_requested", "RAW_CONTENT_PERSISTENCE_FORBIDDEN"),
        ("formal_memory_write_requested", "FORMAL_MEMORY_WRITE_FORBIDDEN"),
        ("direct_task_write_requested", "DIRECT_TASK_WRITE_FORBIDDEN"),
        ("direct_command_commit_requested", "DIRECT_COMMAND_COMMIT_FORBIDDEN"),
        ("relationship_as_authority", "RELATIONSHIP_CANNOT_EXPAND_AUTHORITY"),
        ("pbl_no_match_as_sufficient", "PBL_NO_MATCH_IS_NOT_PERMISSION"),
    ]
    reasons.extend(reason for field, reason in structural if value[field])
    if reasons:
        return output("REJECTED", reasons)
    if not value["upstream_current"]:
        return output("INDETERMINATE", ["UPSTREAM_CURRENTNESS_UNAVAILABLE"])
    if value["source_kind"] == "ORDINARY_THOUGHT":
        if value["branch_choice"] == "NONE":
            return output("NO_PROMOTION", ["VALID_NO_PROMOTION"])
        return output("REJECTED", ["ORDINARY_THOUGHT_CANNOT_PROMOTE"])
    if value["source_kind"] == "RELATIONSHIP_MEMORY":
        return output("NO_PROMOTION", ["VALID_NO_PROMOTION"])
    if value["branch_choice"] == "NONE":
        return output("INDETERMINATE", ["EXPLICIT_SESSION_BRANCH_MISSING"])
    if value["branch_choice"] in {"EPHEMERAL_ONLY", "DISCARD", "REMAIN_IN_SESSION"}:
        return output("NO_PROMOTION", ["VALID_NO_PROMOTION"])
    if not value["explicit_life_stream_choice"]:
        return output("REJECTED", ["EXPLICIT_LIFE_STREAM_CHOICE_MISSING"])

    action = value["life_stream_action"]
    if action == "NONE":
        return output("LIFE_STREAM_CANDIDATE_ONLY", ["VALID_LIFE_STREAM_CANDIDATE"], life=1)
    if action == "OBSERVE":
        return output("OBSERVED_NO_FURTHER_PROMOTION", ["VALID_OBSERVE"], life=1)
    if action == "DISCARD":
        return output("DISCARDED_NO_FURTHER_PROMOTION", ["VALID_DISCARD"], life=1)
    if action == "PROPOSE_MEMORY_CANDIDATE":
        if not value["explicit_memory_choice"]:
            return output("REJECTED", ["EXPLICIT_MEMORY_CHOICE_MISSING"], life=1)
        return output("MEMORY_CANDIDATE_ONLY", ["VALID_MEMORY_CANDIDATE"], life=1, memory=1)
    if action != "PROPOSE_INTENT_CANDIDATE":
        return output("REJECTED", ["UNKNOWN_OR_MALFORMED_INPUT"])
    if not value["explicit_intent_choice"]:
        return output("REJECTED", ["EXPLICIT_INTENT_CHOICE_MISSING"], life=1)
    if not value["request_f8_handoff"]:
        return output("INTENT_CANDIDATE_ONLY", ["VALID_INTENT_CANDIDATE"], life=1, intent=1)
    if value["f8_result"] == "REJECTED":
        return output("REJECTED", ["F8_HANDOFF_REJECTED"], life=1, intent=1)
    if value["f8_result"] != "CANDIDATE_FORMED":
        return output("INDETERMINATE", ["F8_HANDOFF_INDETERMINATE"], life=1, intent=1)
    if value["f3_outcome"] == "NOT_SUBMITTED":
        return output("HANDOFF_CANDIDATE_ONLY", ["F3_NOT_SUBMITTED", "VALID_HANDOFF_CANDIDATE"], life=1, intent=1, handoff=1)
    if value["f3_outcome"] == "SYNTHETIC_TEST_COMMITTED":
        return output("F3_COMMAND_ACKNOWLEDGED", ["VALID_F3_COMMIT_ACKNOWLEDGEMENT"], life=1, intent=1, handoff=1, f3=1)
    if value["f3_outcome"] == "REJECTED":
        return output("F3_REJECTION_ACKNOWLEDGED", ["F3_REJECTED"], life=1, intent=1, handoff=1)
    return output("F3_INDETERMINATE_ACKNOWLEDGED", ["F3_INDETERMINATE"], life=1, intent=1, handoff=1)


def integrated_witness() -> dict[str, Any]:
    return {
        "synthetic_session_observation_count": 4,
        "branch_counts": {
            "DISCARD": 1,
            "EPHEMERAL_ONLY": 1,
            "PROPOSE_LIFE_STREAM_CANDIDATE": 1,
            "REMAIN_IN_SESSION": 1,
        },
        "synthetic_life_stream_candidate_count": 1,
        "synthetic_memory_candidate_count": 1,
        "synthetic_intent_candidate_count": 1,
        "synthetic_F8_handoff_candidate_count": 1,
        "synthetic_F3_committed_command_count": 1,
        "real_session_count": 0,
        "real_Goal_count": 0,
        "real_Task_count": 0,
        "formal_memory_write_count": 0,
        "real_Command_count": 0,
        "provider_call_count": 0,
        "network_call_count": 0,
        "private_memory_read_count": 0,
        "sensing_or_recording_count": 0,
        "external_effect_count": 0,
        "runtime_activation_count": 0,
        "terminal_outcome": "NOT_ACTIVATED",
    }


def build_fixture() -> dict[str, Any]:
    rows = []
    for ordinal, (case_id, value) in enumerate(case_specs(), start=1):
        row = {
            "ordinal": ordinal,
            "case_id": case_id,
            "raw_input": copy.deepcopy(value),
            "derived_output": derive_case(value),
        }
        row["row_fingerprint"] = fingerprint(CASE_DOMAIN, row)
        rows.append(row)
    fixture: dict[str, Any] = {
        "schema_version": "agents-os.m0b-plan-r1-synthetic-witness.v0.1",
        "profile": {
            "environment": "SYNTHETIC_TEST",
            "domain_tag": "PHASE_5B_M0B_PLAN_R1_SYNTHETIC_NONAUTHORITY",
            "runtime_usable": False,
            "production_compatible": False,
        },
        "case_catalog": rows,
        "integrated_witness": integrated_witness(),
        "boundary_assertions": {
            "Home_creates_permission": False,
            "Home_creates_identity_authority": False,
            "Home_writes_Goal_or_Task": False,
            "Home_commits_Command": False,
            "Memory_Candidate_is_formal_Memory": False,
            "relationship_expands_authority": False,
            "raw_Session_content_persisted": False,
            "private_Memory_read": False,
            "VCPToolBox_modified_or_started": False,
            "database_created": False,
            "runtime_activated": False,
            "provider_or_real_effect_executed": False,
            "implementation_authorized": False,
        },
    }
    fixture["section_fingerprints"] = {
        "case_catalog": fingerprint(SECTION_DOMAIN + ":case_catalog", fixture["case_catalog"]),
        "integrated_witness": fingerprint(SECTION_DOMAIN + ":integrated_witness", fixture["integrated_witness"]),
        "boundary_assertions": fingerprint(SECTION_DOMAIN + ":boundary_assertions", fixture["boundary_assertions"]),
    }
    fixture["root_fingerprint"] = fingerprint(ROOT_DOMAIN, fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_bytes(canonical_bytes(build_fixture()) + b"\n")
    print(f"PASS wrote={args.output} cases={len(case_specs())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
