#!/usr/bin/env python3
"""Build the fixed synthetic F6 R1 Validation current-decision witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    WORKSPACE_ROOT
    / "control-plane/registry/examples/2026-07-17-agents-os-f6-r1-validation-current-decision-v0.1.json"
)
SAFE_MAX = 2**53 - 1


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def typed_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\0" + canonical_bytes(value)).hexdigest()


def labeled_hash(label: str) -> str:
    return typed_hash("agents-os.f6.synthetic-label.v0.1-r1", {"label": label})


def with_fingerprint(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    rendered = dict(value)
    rendered["canonical_fingerprint"] = typed_hash(domain, rendered)
    return rendered


def with_case_fingerprint(section: str, value: dict[str, Any]) -> dict[str, Any]:
    rendered = dict(value)
    rendered["case_fingerprint"] = typed_hash(
        f"agents-os.f6.{section}-case.v0.1-r1", rendered
    )
    return rendered


REQUIREMENT_REASON_PRECEDENCE = [
    "REQUIREMENT_INPUT_INTEGRITY_FAILURE",
    "REQUIREMENT_BINDING_UNAVAILABLE",
    "ATTEMPT_CHAIN_CORRUPT",
    "ATTEMPT_AUTHORITY_UNAVAILABLE",
    "EVIDENCE_UNAVAILABLE",
    "CARRY_FORWARD_INVALID",
    "F5_DELIVERY_UNAVAILABLE",
    "WAIVER_INVALID",
    "LATEST_ATTEMPT_FAILED",
    "CURRENT_PASS_MISSING",
    "REQUIREMENT_OPTIONAL",
    "REQUIREMENT_WAIVED",
    "VALIDATION_PASSED",
]

SET_REASON_PRECEDENCE = [
    "VALIDATION_SET_INPUT_INTEGRITY_FAILURE",
    "SNAPSHOT_CURRENTNESS_UNAVAILABLE",
    "REQUIREMENT_DECISION_INDETERMINATE",
    "EMPTY_REQUIRED_SET",
    "REQUIRED_REQUIREMENT_NOT_SATISFIED",
    "NO_REAL_REQUIRED_PASS",
    "NONTERMINAL_VALIDATION_PRESENT",
    "ALL_REQUIRED_CURRENTLY_SATISFIED",
]

COMPLETION_REASON_PRECEDENCE = [
    "COMPLETION_INPUT_INTEGRITY_FAILURE",
    "READ_BARRIER_UNAVAILABLE",
    "TASK_CURRENTNESS_UNAVAILABLE",
    "CANDIDATE_CURRENTNESS_UNAVAILABLE",
    "VALIDATION_SET_DECISION_INDETERMINATE",
    "DEPENDENCY_CURRENTNESS_UNAVAILABLE",
    "F5_CURRENTNESS_UNAVAILABLE",
    "TRUSTED_TIME_UNAVAILABLE",
    "TASK_NOT_VERIFYING",
    "CANDIDATE_NOT_CURRENT",
    "VALIDATION_SET_NOT_SATISFIED",
    "DEPENDENCY_NOT_CONFIRMED",
    "NONTERMINAL_WORK_PRESENT",
    "ACTIVE_CONTROL_INTENT",
    "UNRESOLVED_EFFECT_PRESENT",
    "ALL_COMPLETION_GATES_SATISFIED",
]


def choose_primary(reasons: list[str], precedence: list[str]) -> str:
    true_reasons = set(reasons)
    return next(reason for reason in precedence if reason in true_reasons)


def sorted_unique(values: list[str]) -> list[str]:
    return sorted(set(values))


def derive_requirement_case(raw: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    if raw["integrity_status"] != "VALID":
        reasons.append("REQUIREMENT_INPUT_INTEGRITY_FAILURE")
    if raw["attempt_binding_status"] != "CURRENT":
        reasons.append("REQUIREMENT_BINDING_UNAVAILABLE")
    if raw["latest_attempt_state"] == "CORRUPT":
        reasons.append("ATTEMPT_CHAIN_CORRUPT")
    if raw["authority_result"] in {"REJECTED", "INDETERMINATE"}:
        reasons.append("ATTEMPT_AUTHORITY_UNAVAILABLE")
    if raw["latest_attempt_state"] in {"INCONCLUSIVE", "ERROR"}:
        reasons.append("EVIDENCE_UNAVAILABLE")
    if raw["latest_attempt_state"] == "PASSED" and raw["evidence_currentness"] in {
        "STALE",
        "INDETERMINATE",
        "NOT_APPLICABLE",
    }:
        reasons.append("EVIDENCE_UNAVAILABLE")
    if raw["validation_method"] == "EVIDENCE_CARRY_FORWARD_REVIEW" and (
        raw["carry_forward_status"] != "VALID"
        or raw["validation_type"] == "HUMAN_ACCEPTANCE"
        or raw["effectful_delivery_binding_required"]
    ):
        reasons.append("CARRY_FORWARD_INVALID")
    if raw["effectful_delivery_binding_required"] and raw["f5_delivery_status"] in {
        "HISTORY_ONLY",
        "INDETERMINATE",
        "NOT_REQUIRED",
    }:
        reasons.append("F5_DELIVERY_UNAVAILABLE")
    if not raw["effectful_delivery_binding_required"] and raw["f5_delivery_status"] != "NOT_REQUIRED":
        reasons.append("REQUIREMENT_INPUT_INTEGRITY_FAILURE")
    if raw["waiver_status"] == "ACTIVE_INVALID" or (
        raw["waiver_status"] == "ACTIVE_VALID" and raw["latest_attempt_state"] == "FAILED"
    ) or (
        raw["waiver_status"] == "ACTIVE_VALID" and raw["waivability"] != "JENN_WAIVABLE"
    ):
        reasons.append("WAIVER_INVALID")

    indeterminate_reasons = set(REQUIREMENT_REASON_PRECEDENCE[:8])
    if any(reason in indeterminate_reasons for reason in reasons):
        codes = sorted_unique(reasons)
        return "INDETERMINATE", choose_primary(codes, REQUIREMENT_REASON_PRECEDENCE), codes

    if raw["requiredness"] == "OPTIONAL":
        return "NOT_REQUIRED", "REQUIREMENT_OPTIONAL", ["REQUIREMENT_OPTIONAL"]
    if raw["waiver_status"] == "ACTIVE_VALID":
        return "WAIVED", "REQUIREMENT_WAIVED", ["REQUIREMENT_WAIVED"]

    state = raw["latest_attempt_state"]
    if state == "FAILED":
        return "UNSATISFIED", "LATEST_ATTEMPT_FAILED", ["LATEST_ATTEMPT_FAILED"]
    if state in {"INCONCLUSIVE", "ERROR", "CORRUPT"}:
        return "INDETERMINATE", "EVIDENCE_UNAVAILABLE", ["EVIDENCE_UNAVAILABLE"]
    if state == "PASSED":
        return "SATISFIED", "VALIDATION_PASSED", ["VALIDATION_PASSED"]
    return "PENDING", "CURRENT_PASS_MISSING", ["CURRENT_PASS_MISSING"]


def requirement_case(case_id: str, **overrides: Any) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "case_id": case_id,
        "integrity_status": "VALID",
        "requiredness": "REQUIRED",
        "waivability": "NON_WAIVABLE",
        "waiver_status": "NONE",
        "validation_type": "DETERMINISTIC",
        "effectful_delivery_binding_required": False,
        "latest_attempt_state": "PASSED",
        "attempt_binding_status": "CURRENT",
        "authority_result": "CURRENT_ACCEPTED",
        "evidence_currentness": "CURRENT",
        "validation_method": "FRESH_VALIDATION",
        "carry_forward_status": "NOT_APPLICABLE",
        "f5_delivery_status": "NOT_REQUIRED",
    }
    raw.update(overrides)
    result, primary, reasons = derive_requirement_case(raw)
    raw.update(
        {
            "expected_result": result,
            "expected_primary_reason": primary,
            "expected_reason_codes": reasons,
        }
    )
    return with_case_fingerprint("requirement", raw)


def derive_set_case(raw: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    if raw["integrity_status"] != "VALID":
        reasons.append("VALIDATION_SET_INPUT_INTEGRITY_FAILURE")
    if raw["snapshot_currentness"] != "CURRENT":
        reasons.append("SNAPSHOT_CURRENTNESS_UNAVAILABLE")
    if "INDETERMINATE" in raw["required_decisions"] + raw["optional_decisions"]:
        reasons.append("REQUIREMENT_DECISION_INDETERMINATE")
    if not raw["required_decisions"]:
        reasons.append("EMPTY_REQUIRED_SET")
    if any(value not in {"SATISFIED", "WAIVED"} for value in raw["required_decisions"]):
        reasons.append("REQUIRED_REQUIREMENT_NOT_SATISFIED")
    if not any(value == "SATISFIED" for value in raw["required_decisions"]):
        reasons.append("NO_REAL_REQUIRED_PASS")
    if raw["nonterminal_attempt_count"] > 0:
        reasons.append("NONTERMINAL_VALIDATION_PRESENT")

    codes = sorted_unique(reasons)
    if any(reason in set(SET_REASON_PRECEDENCE[:3]) for reason in codes):
        return "INDETERMINATE", choose_primary(codes, SET_REASON_PRECEDENCE), codes
    if codes:
        return "NOT_SATISFIED", choose_primary(codes, SET_REASON_PRECEDENCE), codes
    return (
        "SATISFIED",
        "ALL_REQUIRED_CURRENTLY_SATISFIED",
        ["ALL_REQUIRED_CURRENTLY_SATISFIED"],
    )


def set_case(case_id: str, **overrides: Any) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "case_id": case_id,
        "integrity_status": "VALID",
        "snapshot_currentness": "CURRENT",
        "required_decisions": ["SATISFIED"],
        "optional_decisions": [],
        "nonterminal_attempt_count": 0,
    }
    raw.update(overrides)
    result, primary, reasons = derive_set_case(raw)
    raw.update(
        {
            "expected_result": result,
            "expected_primary_reason": primary,
            "expected_reason_codes": reasons,
        }
    )
    return with_case_fingerprint("set", raw)


def derive_completion_case(raw: dict[str, Any]) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    if raw["integrity_status"] != "VALID":
        reasons.append("COMPLETION_INPUT_INTEGRITY_FAILURE")
    if raw["read_barrier_status"] != "CURRENT":
        reasons.append("READ_BARRIER_UNAVAILABLE")
    if raw["task_currentness"] != "CURRENT":
        reasons.append("TASK_CURRENTNESS_UNAVAILABLE")
    if raw["candidate_currentness"] == "INDETERMINATE":
        reasons.append("CANDIDATE_CURRENTNESS_UNAVAILABLE")
    if raw["validation_set_decision"] == "INDETERMINATE":
        reasons.append("VALIDATION_SET_DECISION_INDETERMINATE")
    if raw["dependency_currentness"] == "INDETERMINATE":
        reasons.append("DEPENDENCY_CURRENTNESS_UNAVAILABLE")
    if raw["f5_completion_currentness"] == "INDETERMINATE":
        reasons.append("F5_CURRENTNESS_UNAVAILABLE")
    if raw["trusted_time_status"] != "CURRENT":
        reasons.append("TRUSTED_TIME_UNAVAILABLE")
    if raw["task_lifecycle"] != "VERIFYING":
        reasons.append("TASK_NOT_VERIFYING")
    if raw["candidate_currentness"] == "STALE":
        reasons.append("CANDIDATE_NOT_CURRENT")
    if raw["validation_set_decision"] == "NOT_SATISFIED":
        reasons.append("VALIDATION_SET_NOT_SATISFIED")
    if raw["dependency_currentness"] in {"CHALLENGED", "INVALIDATED"}:
        reasons.append("DEPENDENCY_NOT_CONFIRMED")
    if raw["nonterminal_execution_run_count"] > 0 or raw[
        "nonterminal_validation_count"
    ] > 0:
        reasons.append("NONTERMINAL_WORK_PRESENT")
    if raw["active_control_intent_count"] > 0:
        reasons.append("ACTIVE_CONTROL_INTENT")
    if (
        raw["unknown_effect_count"] > 0
        or raw["completion_blocking_effect_count"] > 0
        or raw["f5_completion_currentness"] == "BLOCKED"
    ):
        reasons.append("UNRESOLVED_EFFECT_PRESENT")

    codes = sorted_unique(reasons)
    if any(reason in set(COMPLETION_REASON_PRECEDENCE[:8]) for reason in codes):
        return "INDETERMINATE", choose_primary(codes, COMPLETION_REASON_PRECEDENCE), codes
    if codes:
        return "NOT_ELIGIBLE", choose_primary(codes, COMPLETION_REASON_PRECEDENCE), codes
    return (
        "ELIGIBLE",
        "ALL_COMPLETION_GATES_SATISFIED",
        ["ALL_COMPLETION_GATES_SATISFIED"],
    )


def completion_case(case_id: str, **overrides: Any) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "case_id": case_id,
        "integrity_status": "VALID",
        "read_barrier_status": "CURRENT",
        "task_currentness": "CURRENT",
        "task_lifecycle": "VERIFYING",
        "candidate_currentness": "CURRENT",
        "validation_set_decision": "SATISFIED",
        "dependency_currentness": "CURRENT_CONFIRMED",
        "f5_completion_currentness": "CLEAR",
        "trusted_time_status": "CURRENT",
        "nonterminal_execution_run_count": 0,
        "nonterminal_validation_count": 0,
        "active_control_intent_count": 0,
        "unknown_effect_count": 0,
        "completion_blocking_effect_count": 0,
    }
    raw.update(overrides)
    result, primary, reasons = derive_completion_case(raw)
    raw.update(
        {
            "expected_result": result,
            "expected_primary_reason": primary,
            "expected_reason_codes": reasons,
        }
    )
    return with_case_fingerprint("completion", raw)


def build_requirement_vectors() -> list[dict[str, Any]]:
    return [
        requirement_case("REQ-01-FRESH-PASS-CURRENT"),
        requirement_case("REQ-02-FRESH-PASS-TIMELESS", evidence_currentness="TIMELESS"),
        requirement_case(
            "REQ-03-NO-ATTEMPT",
            latest_attempt_state="NONE",
            authority_result="NOT_APPLICABLE",
            evidence_currentness="NOT_APPLICABLE",
            validation_method="NONE",
        ),
        requirement_case(
            "REQ-04-PENDING",
            latest_attempt_state="PENDING",
            evidence_currentness="NOT_APPLICABLE",
        ),
        requirement_case(
            "REQ-05-RUNNING",
            latest_attempt_state="RUNNING",
            evidence_currentness="NOT_APPLICABLE",
        ),
        requirement_case(
            "REQ-06-CANCELLED",
            latest_attempt_state="CANCELLED",
            evidence_currentness="NOT_APPLICABLE",
        ),
        requirement_case("REQ-07-FAILED", latest_attempt_state="FAILED"),
        requirement_case("REQ-08-INCONCLUSIVE", latest_attempt_state="INCONCLUSIVE"),
        requirement_case("REQ-09-ERROR", latest_attempt_state="ERROR", evidence_currentness="NOT_APPLICABLE"),
        requirement_case("REQ-10-EVIDENCE-STALE", evidence_currentness="STALE"),
        requirement_case("REQ-11-EVIDENCE-INDETERMINATE", evidence_currentness="INDETERMINATE"),
        requirement_case("REQ-12-AUTHORITY-REJECTED", authority_result="REJECTED"),
        requirement_case("REQ-13-AUTHORITY-INDETERMINATE", authority_result="INDETERMINATE"),
        requirement_case("REQ-14-BINDING-STALE", attempt_binding_status="STALE"),
        requirement_case(
            "REQ-15-CARRY-FORWARD-VALID",
            validation_method="EVIDENCE_CARRY_FORWARD_REVIEW",
            carry_forward_status="VALID",
        ),
        requirement_case(
            "REQ-16-CARRY-FORWARD-INVALID",
            validation_method="EVIDENCE_CARRY_FORWARD_REVIEW",
            carry_forward_status="INVALID",
        ),
        requirement_case(
            "REQ-17-WAIVER-ACTIVE",
            waivability="JENN_WAIVABLE",
            waiver_status="ACTIVE_VALID",
            latest_attempt_state="NONE",
            authority_result="NOT_APPLICABLE",
            evidence_currentness="NOT_APPLICABLE",
            validation_method="NONE",
        ),
        requirement_case(
            "REQ-18-OPTIONAL",
            requiredness="OPTIONAL",
            latest_attempt_state="NONE",
            authority_result="NOT_APPLICABLE",
            evidence_currentness="NOT_APPLICABLE",
            validation_method="NONE",
        ),
        requirement_case(
            "REQ-19-WAIVER-INVALID",
            waivability="JENN_WAIVABLE",
            waiver_status="ACTIVE_INVALID",
        ),
        requirement_case(
            "REQ-20-EFFECTFUL-F5-CURRENT",
            validation_type="RUNTIME_OBSERVATION",
            effectful_delivery_binding_required=True,
            f5_delivery_status="APPLIED_CURRENT",
        ),
        requirement_case(
            "REQ-21-EFFECTFUL-F5-HISTORY",
            validation_type="RUNTIME_OBSERVATION",
            effectful_delivery_binding_required=True,
            f5_delivery_status="HISTORY_ONLY",
        ),
        requirement_case(
            "REQ-22-HUMAN-CARRY-FORWARD-INVALID",
            validation_type="HUMAN_ACCEPTANCE",
            validation_method="EVIDENCE_CARRY_FORWARD_REVIEW",
            carry_forward_status="VALID",
        ),
    ]


def build_set_vectors() -> list[dict[str, Any]]:
    return [
        set_case("SET-01-ALL-PASSED", required_decisions=["SATISFIED", "SATISFIED"]),
        set_case("SET-02-PASS-AND-WAIVER", required_decisions=["SATISFIED", "WAIVED"]),
        set_case("SET-03-ALL-WAIVED", required_decisions=["WAIVED", "WAIVED"]),
        set_case("SET-04-PENDING", required_decisions=["SATISFIED", "PENDING"]),
        set_case("SET-05-FAILED", required_decisions=["SATISFIED", "UNSATISFIED"]),
        set_case("SET-06-INDETERMINATE", required_decisions=["SATISFIED", "INDETERMINATE"]),
        set_case(
            "SET-07-OPTIONAL-IGNORED",
            required_decisions=["SATISFIED"],
            optional_decisions=["NOT_REQUIRED"],
        ),
        set_case("SET-08-EMPTY", required_decisions=[]),
        set_case("SET-09-NONTERMINAL", nonterminal_attempt_count=1),
        set_case("SET-10-SNAPSHOT-STALE", snapshot_currentness="STALE"),
    ]


def build_completion_vectors() -> list[dict[str, Any]]:
    return [
        completion_case("COMP-01-ELIGIBLE"),
        completion_case("COMP-02-BARRIER-INDETERMINATE", read_barrier_status="INDETERMINATE"),
        completion_case("COMP-03-BARRIER-CHANGED", read_barrier_status="CHANGED_DURING_REDUCTION"),
        completion_case("COMP-04-TASK-STALE", task_currentness="STALE"),
        completion_case("COMP-05-TASK-INDETERMINATE", task_currentness="INDETERMINATE"),
        completion_case("COMP-06-TASK-ACTIVE", task_lifecycle="ACTIVE"),
        completion_case("COMP-07-CANDIDATE-STALE", candidate_currentness="STALE"),
        completion_case("COMP-08-CANDIDATE-INDETERMINATE", candidate_currentness="INDETERMINATE"),
        completion_case("COMP-09-SET-NOT-SATISFIED", validation_set_decision="NOT_SATISFIED"),
        completion_case("COMP-10-SET-INDETERMINATE", validation_set_decision="INDETERMINATE"),
        completion_case("COMP-11-DEPENDENCY-CHALLENGED", dependency_currentness="CHALLENGED"),
        completion_case("COMP-12-DEPENDENCY-INVALIDATED", dependency_currentness="INVALIDATED"),
        completion_case("COMP-13-DEPENDENCY-INDETERMINATE", dependency_currentness="INDETERMINATE"),
        completion_case("COMP-14-NONTERMINAL-RUN", nonterminal_execution_run_count=1),
        completion_case("COMP-15-NONTERMINAL-VALIDATION", nonterminal_validation_count=1),
        completion_case("COMP-16-ACTIVE-CONTROL", active_control_intent_count=1),
        completion_case("COMP-17-UNKNOWN-EFFECT", unknown_effect_count=1),
        completion_case("COMP-18-COMPLETION-BLOCKING-EFFECT", completion_blocking_effect_count=1),
        completion_case("COMP-19-F5-BLOCKED", f5_completion_currentness="BLOCKED"),
        completion_case("COMP-20-F5-INDETERMINATE", f5_completion_currentness="INDETERMINATE"),
        completion_case("COMP-21-TIME-INDETERMINATE", trusted_time_status="INDETERMINATE"),
        completion_case(
            "COMP-22-MULTIPLE-FAILURES",
            task_lifecycle="ACTIVE",
            nonterminal_execution_run_count=1,
            unknown_effect_count=1,
        ),
    ]


def build_precedence_trials() -> list[dict[str, Any]]:
    definitions = {
        "REQUIREMENT": {
            "reasons": REQUIREMENT_REASON_PRECEDENCE[:10],
            "indeterminate": set(REQUIREMENT_REASON_PRECEDENCE[:8]),
            "known_results": {
                "LATEST_ATTEMPT_FAILED": "UNSATISFIED",
                "CURRENT_PASS_MISSING": "PENDING",
            },
            "precedence": REQUIREMENT_REASON_PRECEDENCE,
        },
        "VALIDATION_SET": {
            "reasons": SET_REASON_PRECEDENCE[:7],
            "indeterminate": set(SET_REASON_PRECEDENCE[:3]),
            "known_results": {},
            "precedence": SET_REASON_PRECEDENCE,
        },
        "COMPLETION": {
            "reasons": COMPLETION_REASON_PRECEDENCE[:15],
            "indeterminate": set(COMPLETION_REASON_PRECEDENCE[:8]),
            "known_results": {},
            "precedence": COMPLETION_REASON_PRECEDENCE,
        },
    }
    trials: list[dict[str, Any]] = []
    for reducer, definition in definitions.items():
        pair_index = 0
        for first, second in combinations(definition["reasons"], 2):
            pair_index += 1
            reasons = [first, second]
            primary = choose_primary(reasons, definition["precedence"])
            if any(reason in definition["indeterminate"] for reason in reasons):
                result = "INDETERMINATE"
            elif reducer == "REQUIREMENT":
                result = definition["known_results"][primary]
            elif reducer == "VALIDATION_SET":
                result = "NOT_SATISFIED"
            else:
                result = "NOT_ELIGIBLE"
            unordered_id = f"{reducer}-PAIR-{pair_index:03d}"
            for ordering, ordered_reasons in ((1, reasons), (2, list(reversed(reasons)))):
                row = {
                    "unordered_case_id": unordered_id,
                    "reducer": reducer,
                    "ordering": ordering,
                    "raw_conditions": ordered_reasons,
                    "expected_result": result,
                    "expected_primary_reason": primary,
                    "expected_reason_codes": sorted(reasons),
                }
                row["trial_fingerprint"] = typed_hash(
                    "agents-os.f6.reason-precedence-trial.v0.1-r1", row
                )
                trials.append(row)
    return trials


def make_read_barrier() -> dict[str, Any]:
    identity = {
        "resident_identity_ref": "synth:f6:resident:one",
        "resident_authority_epoch": 7,
        "schema_contract_set_fingerprint": labeled_hash("schema-contract-set"),
        "start_event_sequence": 200,
        "end_event_sequence": 200,
    }
    value = {
        "interface_version": "agents-os.f6-f3-read-barrier-input.v0.1-r1",
        "barrier_id": typed_hash("agents-os.f6.read-barrier-id.v0.1-r1", identity),
        **identity,
        "f3_result": "CURRENT",
    }
    return with_fingerprint("agents-os.f6.read-barrier.v0.1-r1", value)


def make_trusted_time(barrier: dict[str, Any]) -> dict[str, Any]:
    return with_fingerprint(
        "agents-os.f6.trusted-time.v0.1-r1",
        {
            "interface_version": "agents-os.f6-trusted-time-input.v0.1-r1",
            "trusted_time_ref": "synth:f6:time:one",
            "as_of_utc_ms": 1_800_000_000_000,
            "time_policy_ref": "synth:f6:time-policy:v1",
            "time_policy_fingerprint": labeled_hash("time-policy-v1"),
            "result": "CURRENT",
            "read_barrier_ref": barrier["barrier_id"],
            "read_barrier_fingerprint": barrier["canonical_fingerprint"],
            "assessed_at_event_sequence": barrier["end_event_sequence"],
        },
    )


def make_assessment(
    barrier: dict[str, Any],
    name: str,
    owner: str,
    kind: str,
    result: str,
    subject_ref: str,
    subject_revision: int,
    subject_fingerprint: str | None = None,
) -> dict[str, Any]:
    return with_fingerprint(
        "agents-os.f6.upstream-assessment.v0.1-r1",
        {
            "interface_version": "agents-os.f6-upstream-assessment-input.v0.1-r1",
            "assessment_ref": f"synth:f6:assessment:{name}",
            "owner_contract": owner,
            "assessment_kind": kind,
            "subject_ref": subject_ref,
            "subject_revision": subject_revision,
            "subject_fingerprint": subject_fingerprint
            or labeled_hash(f"subject:{subject_ref}:{subject_revision}"),
            "result": result,
            "read_barrier_ref": barrier["barrier_id"],
            "read_barrier_fingerprint": barrier["canonical_fingerprint"],
            "assessed_at_event_sequence": barrier["end_event_sequence"],
        },
    )


def make_requirement(
    task_id: str,
    key: str,
    validation_type: str,
    requiredness: str,
    reuse_mode: str,
    freshness_mode: str,
    provenance_kind: str,
    waivability: str = "NON_WAIVABLE",
    waiver_duration_policy: str = "NOT_APPLICABLE",
) -> dict[str, Any]:
    requirement_id = typed_hash(
        "agents-os.f6.requirement-id.v0.1-r1",
        {"task_id": task_id, "canonical_requirement_key": key},
    )
    is_human = validation_type == "HUMAN_ACCEPTANCE"
    provenance = [
        {
            "source_kind": provenance_kind,
            "source_ref": f"synth:f6:source:{key}",
            "source_revision": 1,
            "source_fingerprint": labeled_hash(f"source:{key}:1"),
            "effective_scope": "THIS_TASK",
            "nonwaivable": waivability == "NON_WAIVABLE",
        }
    ]
    carry_ref = None
    carry_version = None
    carry_fp = None
    if reuse_mode == "CONDITIONAL_CARRY_FORWARD":
        carry_ref = f"synth:f6:carry-contract:{key}"
        carry_version = "v1"
        carry_fp = labeled_hash(f"carry-contract:{key}:v1")
    value = {
        "interface_version": "agents-os.validation-requirement.v0.1-r1",
        "task_id": task_id,
        "requirement_id": requirement_id,
        "requirement_revision": 1,
        "task_spec_revision": 3,
        "canonical_requirement_key": key,
        "semantic_digest": labeled_hash(f"semantic:{key}"),
        "provenance_bindings": provenance,
        "provenance_set_fingerprint": typed_hash(
            "agents-os.f6.requirement-provenance-set.v0.1-r1", provenance
        ),
        "validation_type": validation_type,
        "acceptance_predicate_ref": f"synth:f6:predicate:{key}",
        "acceptance_predicate_fingerprint": labeled_hash(f"predicate:{key}"),
        "result_scope_ref": "synth:f6:result:revision-5",
        "result_scope_fingerprint": labeled_hash("result-revision-5"),
        "validator_contract_ref": f"synth:f6:validator:{key}",
        "validator_contract_version": "v1",
        "validator_contract_fingerprint": labeled_hash(f"validator:{key}:v1"),
        "enforcement_phase": "POST_RESULT_VALIDATION",
        "requiredness": requiredness,
        "waivability": waivability,
        "waiver_duration_policy": waiver_duration_policy,
        "evidence_reuse_mode": reuse_mode,
        "carry_forward_equivalence_contract_ref": carry_ref,
        "carry_forward_equivalence_contract_version": carry_version,
        "carry_forward_equivalence_contract_fingerprint": carry_fp,
        "evidence_freshness_mode": freshness_mode,
        "evidence_max_age_ms": None,
        "effectful_delivery_binding_required": False,
        "effectful_delivery_subject_ref": None,
        "effectful_delivery_subject_fingerprint": None,
        "supersedes_requirement_revision": None,
        "created_event_sequence": 101 if not is_human else 102,
    }
    return with_fingerprint("agents-os.f6.requirement.v0.1-r1", value)


def make_validation_set(
    task_id: str,
    requirements: list[dict[str, Any]],
    *,
    validation_set_revision: int = 1,
    base_snapshot_id: str | None = None,
    freeze_trigger: str = "FIRST_VERIFYING",
    active_waivers: dict[str, tuple[str, str]] | None = None,
) -> dict[str, Any]:
    active_waivers = active_waivers or {}
    memberships = sorted(
        [
            {
                "requirement_id": requirement["requirement_id"],
                "requirement_revision": requirement["requirement_revision"],
                "requirement_fingerprint": requirement["canonical_fingerprint"],
                "active_waiver_id": active_waivers.get(requirement["requirement_id"], (None, None))[0],
                "active_waiver_event_fingerprint": active_waivers.get(requirement["requirement_id"], (None, None))[1],
            }
            for requirement in requirements
        ],
        key=lambda item: item["requirement_id"],
    )
    source_bindings = sorted(
        [
            {
                "source_ref": provenance["source_ref"],
                "source_revision": provenance["source_revision"],
                "source_fingerprint": provenance["source_fingerprint"],
            }
            for requirement in requirements
            for provenance in requirement["provenance_bindings"]
        ],
        key=lambda item: (item["source_ref"], item["source_revision"]),
    )
    membership_fp = typed_hash(
        "agents-os.f6.validation-membership-set.v0.1-r1", memberships
    )
    source_fp = typed_hash("agents-os.f6.validation-source-set.v0.1-r1", source_bindings)
    identity = {
        "task_id": task_id,
        "lifecycle_generation": 2,
        "completion_epoch": 2,
        "task_spec_revision": 3,
        "result_revision": 5,
        "validation_set_revision": validation_set_revision,
        "base_snapshot_id": base_snapshot_id,
        "freeze_trigger": freeze_trigger,
        "membership_set_fingerprint": membership_fp,
        "source_set_fingerprint": source_fp,
    }
    value = {
        "interface_version": "agents-os.validation-set-snapshot.v0.1-r1",
        "snapshot_id": typed_hash("agents-os.f6.validation-set-id.v0.1-r1", identity),
        **{key: identity[key] for key in (
            "task_id",
            "lifecycle_generation",
            "completion_epoch",
            "task_spec_revision",
            "result_revision",
            "validation_set_revision",
            "base_snapshot_id",
            "freeze_trigger",
        )},
        "memberships": memberships,
        "membership_set_fingerprint": membership_fp,
        "source_bindings": source_bindings,
        "source_set_fingerprint": source_fp,
        "frozen_event_ref": f"synth:f6:event:validation-set-frozen:{validation_set_revision}",
        "frozen_event_sequence": 108 + validation_set_revision * 2,
    }
    return with_fingerprint("agents-os.f6.validation-set.v0.1-r1", value)


def make_waiver_grant(
    task_id: str,
    requirement: dict[str, Any],
    base_snapshot: dict[str, Any],
) -> dict[str, Any]:
    identity = {
        "task_id": task_id,
        "requirement_id": requirement["requirement_id"],
        "requirement_revision": requirement["requirement_revision"],
        "lifecycle_generation": base_snapshot["lifecycle_generation"],
        "completion_epoch": base_snapshot["completion_epoch"],
        "task_spec_revision": base_snapshot["task_spec_revision"],
        "result_revision": base_snapshot["result_revision"],
    }
    waiver_id = typed_hash("agents-os.f6.waiver-id.v0.1-r1", identity)
    event_identity = {
        "waiver_id": waiver_id,
        "waiver_event_index": 1,
        "operation": "GRANT",
    }
    value = {
        "interface_version": "agents-os.requirement-waiver-event.v0.1-r1",
        "waiver_id": waiver_id,
        "waiver_event_id": typed_hash(
            "agents-os.f6.waiver-event-id.v0.1-r1", event_identity
        ),
        "waiver_event_index": 1,
        "prior_waiver_event_fingerprint": None,
        "operation": "GRANT",
        **identity,
        "base_snapshot_id": base_snapshot["snapshot_id"],
        "jenn_decision_ref": "synth:f6:jenn-waiver-decision:one",
        "jenn_decision_fingerprint": labeled_hash("jenn-waiver-decision-one"),
        "jenn_decision_result": "CURRENT_ACCEPTED",
        "reason_ref": "synth:f6:waiver-reason:one",
        "risk_acknowledgement_ref": "synth:f6:waiver-risk:one",
        "review_at_utc_ms": 1_800_000_100_000,
        "expires_at_utc_ms": None,
        "follow_up_task_ref": None,
        "event_sequence": 111,
    }
    return with_fingerprint("agents-os.f6.waiver-event.v0.1-r1", value)


def make_attempt_chain(
    task_id: str,
    requirement: dict[str, Any],
    snapshot: dict[str, Any],
    authority_assessment: dict[str, Any],
    evidence_assessment: dict[str, Any],
    attempt_number: int,
    start_sequence: int,
) -> list[dict[str, Any]]:
    identity = {
        "task_id": task_id,
        "requirement_id": requirement["requirement_id"],
        "requirement_revision": requirement["requirement_revision"],
        "lifecycle_generation": snapshot["lifecycle_generation"],
        "completion_epoch": snapshot["completion_epoch"],
        "task_spec_revision": snapshot["task_spec_revision"],
        "result_revision": snapshot["result_revision"],
        "attempt_number": attempt_number,
    }
    attempt_id = typed_hash("agents-os.f6.validation-attempt-id.v0.1-r1", identity)
    states = ["PENDING", "RUNNING", "PASSED"]
    revisions: list[dict[str, Any]] = []
    prior_fp: str | None = None
    for index, state in enumerate(states, start=1):
        terminal_evidence = state == "PASSED"
        value = {
            "interface_version": "agents-os.validation-attempt-revision.v0.1-r1",
            "attempt_id": attempt_id,
            "attempt_number": attempt_number,
            "attempt_revision": index,
            "prior_attempt_revision_fingerprint": prior_fp,
            "task_id": task_id,
            "requirement_id": requirement["requirement_id"],
            "requirement_revision": requirement["requirement_revision"],
            "requirement_fingerprint": requirement["canonical_fingerprint"],
            "validation_set_snapshot_id": snapshot["snapshot_id"],
            "validation_set_snapshot_fingerprint": snapshot["canonical_fingerprint"],
            "lifecycle_generation": snapshot["lifecycle_generation"],
            "completion_epoch": snapshot["completion_epoch"],
            "task_spec_revision": snapshot["task_spec_revision"],
            "result_revision": snapshot["result_revision"],
            "candidate_commitment_ref": "synth:f6:candidate-commitment:9",
            "candidate_commitment_fingerprint": labeled_hash("candidate-commitment-9"),
            "dependency_closure_ref": "synth:f6:dependency-closure:9",
            "dependency_closure_fingerprint": labeled_hash("dependency-closure-9"),
            "validation_type": requirement["validation_type"],
            "validation_method": "FRESH_VALIDATION",
            "state": state,
            "committed_event_ref": f"synth:f6:event:{attempt_id}:{index}",
            "committed_event_sequence": start_sequence + index - 1,
            "command_envelope_ref": f"synth:f6:command-envelope:{attempt_id}:{index}",
            "command_envelope_fingerprint": labeled_hash(f"command:{attempt_id}:{index}"),
            "authority_assessment_ref": authority_assessment["assessment_ref"],
            "authority_assessment_fingerprint": authority_assessment["canonical_fingerprint"],
            "authority_assessment_result": authority_assessment["result"],
            "evidence_refs": [evidence_assessment["subject_ref"]]
            if terminal_evidence
            else [],
            "evidence_digest": evidence_assessment["subject_fingerprint"]
            if terminal_evidence
            else None,
            "evidence_currentness_ref": evidence_assessment["assessment_ref"] if terminal_evidence else None,
            "evidence_currentness_fingerprint": evidence_assessment["canonical_fingerprint"] if terminal_evidence else None,
            "evidence_currentness_result": evidence_assessment["result"] if terminal_evidence else "NOT_APPLICABLE",
            "evidence_observed_at_utc_ms": 1_799_999_999_000 if terminal_evidence else None,
            "evidence_expires_at_utc_ms": None,
            "source_validation_id": None,
            "root_source_validation_id": None,
            "equivalence_fingerprint": None,
            "f5_delivery_assessment_ref": None,
            "f5_delivery_assessment_fingerprint": None,
            "f5_delivery_assessment_result": "NOT_REQUIRED",
        }
        rendered = with_fingerprint("agents-os.f6.validation-attempt.v0.1-r1", value)
        revisions.append(rendered)
        prior_fp = rendered["canonical_fingerprint"]
    return revisions


def build_graph_witness() -> dict[str, Any]:
    barrier = make_read_barrier()
    trusted_time = make_trusted_time(barrier)
    task_id = typed_hash("agents-os.f6.synthetic-task-id.v0.1-r1", {"label": "task-one"})
    requirement_a = make_requirement(
        task_id,
        "result-digest-matches",
        "DETERMINISTIC",
        "REQUIRED",
        "CONDITIONAL_CARRY_FORWARD",
        "IMMUTABLE_WHEN_FINGERPRINT_MATCHES",
        "RUST_POLICY",
    )
    requirement_b = make_requirement(
        task_id,
        "jenn-accepts-result",
        "HUMAN_ACCEPTANCE",
        "REQUIRED",
        "NEVER_REUSE",
        "FRESH_AT_DECISION",
        "JENN_EXPLICIT",
    )
    requirement_c = make_requirement(
        task_id,
        "optional-format-advisory",
        "DETERMINISTIC",
        "OPTIONAL",
        "REVALIDATE_WITH_OLD_EVIDENCE",
        "FRESH_AT_DECISION",
        "NOBAO_TASK_SPEC",
    )
    requirement_d = make_requirement(
        task_id,
        "manual-advisory-evidence-unavailable",
        "INDEPENDENT_REVIEW",
        "REQUIRED",
        "REVALIDATE_WITH_OLD_EVIDENCE",
        "FRESH_AT_DECISION",
        "JENN_EXPLICIT",
        "JENN_WAIVABLE",
        "COMPLETION_SCOPED_ONLY",
    )
    requirements = sorted(
        [requirement_a, requirement_b, requirement_c, requirement_d],
        key=lambda item: item["requirement_id"],
    )
    base_snapshot = make_validation_set(task_id, requirements)
    waiver_grant = make_waiver_grant(task_id, requirement_d, base_snapshot)
    snapshot = make_validation_set(
        task_id,
        requirements,
        validation_set_revision=2,
        base_snapshot_id=base_snapshot["snapshot_id"],
        freeze_trigger="WAIVER_CHANGE",
        active_waivers={
            requirement_d["requirement_id"]: (
                waiver_grant["waiver_id"],
                waiver_grant["canonical_fingerprint"],
            )
        },
    )

    task_completion_context_fingerprint = typed_hash(
        "agents-os.f6.task-completion-context.v0.1-r1",
        {
            "task_id": task_id,
            "lifecycle_generation": snapshot["lifecycle_generation"],
            "completion_epoch": snapshot["completion_epoch"],
            "task_spec_revision": snapshot["task_spec_revision"],
            "result_revision": snapshot["result_revision"],
        },
    )
    completion_guard_subject_fingerprint = typed_hash(
        "agents-os.f6.completion-guard-subject.v0.1-r1",
        {
            "task_id": task_id,
            "lifecycle_generation": snapshot["lifecycle_generation"],
            "completion_epoch": snapshot["completion_epoch"],
            "task_spec_revision": snapshot["task_spec_revision"],
            "result_revision": snapshot["result_revision"],
            "current_nonterminal_execution_run_count": 0,
            "current_nonterminal_validation_count": 0,
            "active_control_intent_count": 0,
            "unknown_effect_count": 0,
            "completion_blocking_effect_count": 0,
        },
    )

    assessments = [
        make_assessment(
            barrier,
            "task-current",
            "F1",
            "TASK_CURRENTNESS",
            "CURRENT",
            task_id,
            5,
            task_completion_context_fingerprint,
        ),
        make_assessment(
            barrier,
            "candidate-current",
            "F1",
            "CANDIDATE_COMMITMENT_CURRENTNESS",
            "CURRENT",
            "synth:f6:candidate-commitment:9",
            9,
            labeled_hash("candidate-commitment-9"),
        ),
        make_assessment(
            barrier,
            "dependency-current",
            "F1",
            "DEPENDENCY_CLOSURE_CURRENTNESS",
            "CURRENT_CONFIRMED",
            "synth:f6:dependency-closure:9",
            9,
            labeled_hash("dependency-closure-9"),
        ),
        make_assessment(
            barrier,
            "f5-clear",
            "F5",
            "F5_DELIVERY_CURRENTNESS",
            "CLEAR",
            task_id,
            5,
            task_completion_context_fingerprint,
        ),
        make_assessment(
            barrier,
            "completion-guard-current",
            "ACCEPTED_COMPLETION_GUARD_OWNER",
            "COMPLETION_GUARD_CURRENTNESS",
            "CURRENT",
            task_id,
            5,
            completion_guard_subject_fingerprint,
        ),
        make_assessment(
            barrier,
            "authority-a",
            "F3",
            "VALIDATION_AUTHORITY_CURRENTNESS",
            "CURRENT_ACCEPTED",
            requirement_a["validator_contract_ref"],
            1,
            requirement_a["validator_contract_fingerprint"],
        ),
        make_assessment(barrier, "evidence-a", "ACCEPTED_EVIDENCE_OWNER", "EVIDENCE_CURRENTNESS", "CURRENT", "synth:f6:evidence:a", 1),
        make_assessment(
            barrier,
            "authority-b",
            "F3",
            "VALIDATION_AUTHORITY_CURRENTNESS",
            "CURRENT_ACCEPTED",
            requirement_b["validator_contract_ref"],
            1,
            requirement_b["validator_contract_fingerprint"],
        ),
        make_assessment(barrier, "evidence-b", "ACCEPTED_EVIDENCE_OWNER", "EVIDENCE_CURRENTNESS", "CURRENT", "synth:f6:evidence:b", 1),
    ]
    assessments.sort(key=lambda item: item["assessment_ref"])
    assessment_by_ref = {item["assessment_ref"]: item for item in assessments}

    attempts = make_attempt_chain(
        task_id,
        requirement_a,
        snapshot,
        assessment_by_ref["synth:f6:assessment:authority-a"],
        assessment_by_ref["synth:f6:assessment:evidence-a"],
        1,
        120,
    ) + make_attempt_chain(
        task_id,
        requirement_b,
        snapshot,
        assessment_by_ref["synth:f6:assessment:authority-b"],
        assessment_by_ref["synth:f6:assessment:evidence-b"],
        1,
        123,
    )
    attempts.sort(
        key=lambda item: (
            item["requirement_id"],
            item["attempt_number"],
            item["attempt_revision"],
        )
    )

    task_assessment = assessment_by_ref["synth:f6:assessment:task-current"]
    candidate_assessment = assessment_by_ref["synth:f6:assessment:candidate-current"]
    dependency_assessment = assessment_by_ref["synth:f6:assessment:dependency-current"]
    f5_assessment = assessment_by_ref["synth:f6:assessment:f5-clear"]
    completion_guard_assessment = assessment_by_ref[
        "synth:f6:assessment:completion-guard-current"
    ]
    completion_input = with_fingerprint(
        "agents-os.f6.task-completion-input.v0.1-r1",
        {
            "interface_version": "agents-os.task-completion-eligibility-input.v0.1-r1",
            "task_id": task_id,
            "lifecycle_generation": snapshot["lifecycle_generation"],
            "completion_epoch": snapshot["completion_epoch"],
            "task_spec_revision": snapshot["task_spec_revision"],
            "result_revision": snapshot["result_revision"],
            "task_lifecycle": "VERIFYING",
            "task_currentness_assessment_ref": task_assessment["assessment_ref"],
            "task_currentness_assessment_fingerprint": task_assessment["canonical_fingerprint"],
            "candidate_commitment_ref": "synth:f6:candidate-commitment:9",
            "candidate_commitment_fingerprint": labeled_hash("candidate-commitment-9"),
            "candidate_currentness_assessment_ref": candidate_assessment["assessment_ref"],
            "candidate_currentness_assessment_fingerprint": candidate_assessment["canonical_fingerprint"],
            "validation_set_snapshot_id": snapshot["snapshot_id"],
            "validation_set_snapshot_fingerprint": snapshot["canonical_fingerprint"],
            "dependency_closure_ref": "synth:f6:dependency-closure:9",
            "dependency_closure_fingerprint": labeled_hash("dependency-closure-9"),
            "dependency_currentness_assessment_ref": dependency_assessment["assessment_ref"],
            "dependency_currentness_assessment_fingerprint": dependency_assessment["canonical_fingerprint"],
            "f5_completion_blocking_assessment_ref": f5_assessment["assessment_ref"],
            "f5_completion_blocking_assessment_fingerprint": f5_assessment["canonical_fingerprint"],
            "current_nonterminal_execution_run_count": 0,
            "current_nonterminal_validation_count": 0,
            "active_control_intent_count": 0,
            "unknown_effect_count": 0,
            "completion_blocking_effect_count": 0,
            "completion_guard_currentness_assessment_ref": completion_guard_assessment[
                "assessment_ref"
            ],
            "completion_guard_currentness_assessment_fingerprint": completion_guard_assessment[
                "canonical_fingerprint"
            ],
            "read_barrier_ref": barrier["barrier_id"],
            "read_barrier_fingerprint": barrier["canonical_fingerprint"],
            "trusted_time_ref": trusted_time["trusted_time_ref"],
            "trusted_time_fingerprint": trusted_time["canonical_fingerprint"],
        },
    )

    heads = {
        requirement["requirement_id"]: max(
            (
                attempt
                for attempt in attempts
                if attempt["requirement_id"] == requirement["requirement_id"]
            ),
            key=lambda item: (item["attempt_number"], item["attempt_revision"]),
            default=None,
        )
        for requirement in requirements
    }
    expected_requirement_decisions = []
    for requirement in requirements:
        head = heads[requirement["requirement_id"]]
        if requirement["requiredness"] == "OPTIONAL":
            result = "NOT_REQUIRED"
            reason = "REQUIREMENT_OPTIONAL"
        elif requirement["requirement_id"] == requirement_d["requirement_id"]:
            result = "WAIVED"
            reason = "REQUIREMENT_WAIVED"
        else:
            result = "SATISFIED"
            reason = "VALIDATION_PASSED"
        expected_requirement_decisions.append(
            {
                "requirement_id": requirement["requirement_id"],
                "result": result,
                "current_attempt_id": head["attempt_id"] if head else None,
                "current_attempt_revision_fingerprint": head["canonical_fingerprint"] if head else None,
                "current_waiver_id": waiver_grant["waiver_id"] if result == "WAIVED" else None,
                "current_waiver_event_fingerprint": waiver_grant["canonical_fingerprint"] if result == "WAIVED" else None,
                "primary_reason": reason,
                "reason_codes": [reason],
            }
        )
    expected_requirement_decisions.sort(key=lambda item: item["requirement_id"])
    expected = {
        "requirement_decisions": expected_requirement_decisions,
        "validation_set_decision": {
            "result": "SATISFIED",
            "current_required_count": 3,
            "current_unwaived_required_pass_count": 2,
            "nonterminal_attempt_count": 0,
            "primary_reason": "ALL_REQUIRED_CURRENTLY_SATISFIED",
            "reason_codes": ["ALL_REQUIRED_CURRENTLY_SATISFIED"],
        },
        "completion_decision": {
            "result": "ELIGIBLE",
            "completion_assessment_snapshot_may_be_created": True,
            "task_done_may_be_committed": True,
            "primary_reason": "ALL_COMPLETION_GATES_SATISFIED",
            "reason_codes": ["ALL_COMPLETION_GATES_SATISFIED"],
        },
    }
    graph = {
        "read_barrier": barrier,
        "trusted_time": trusted_time,
        "upstream_assessments": assessments,
        "requirements": requirements,
        "waiver_events": [waiver_grant],
        "validation_sets": [base_snapshot, snapshot],
        "current_validation_set_id": snapshot["snapshot_id"],
        "attempt_revisions": attempts,
        "completion_input": completion_input,
        "expected_decisions": expected,
    }
    graph["graph_fingerprint"] = typed_hash(
        "agents-os.f6.graph-witness.v0.1-r1", graph
    )
    return graph


MUTATION_EXPECTATIONS = [
    "unknown_root_field",
    "unknown_graph_field",
    "unknown_requirement_field",
    "float_where_count_required",
    "boolean_where_count_required",
    "unsafe_integer",
    "non_nfc_string",
    "uppercase_hash",
    "missing_requirement_vector",
    "extra_requirement_vector",
    "duplicate_requirement_membership",
    "unsorted_requirement_membership",
    "requirement_id_formula_graphwide_resigned",
    "snapshot_id_formula_graphwide_resigned",
    "attempt_id_formula_graphwide_resigned",
    "attempt_chain_branch_resigned",
    "attempt_invalid_transition_resigned",
    "attempt_number_gap_resigned",
    "stale_evidence_labeled_satisfied_resigned",
    "carry_forward_invalid_labeled_satisfied_resigned",
    "human_carry_forward_labeled_satisfied_resigned",
    "f5_history_labeled_satisfied_resigned",
    "nonwaivable_waiver_resigned",
    "all_waived_set_labeled_satisfied_resigned",
    "empty_set_labeled_satisfied_resigned",
    "active_task_labeled_eligible_resigned",
    "nonterminal_run_labeled_eligible_resigned",
    "unknown_effect_labeled_eligible_resigned",
    "completion_guard_count_changed_resigned",
    "prospective_owner_interface_promoted_resigned",
    "synthetic_environment_changed_to_production_resigned",
    "synthetic_runtime_consumable_enabled_resigned",
]


def build_fixture() -> dict[str, Any]:
    requirement_vectors = build_requirement_vectors()
    set_vectors = build_set_vectors()
    completion_vectors = build_completion_vectors()
    precedence_trials = build_precedence_trials()
    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f6-r1-synthetic-validation-current-decision.v0.1",
        "environment": "SYNTHETIC_TEST",
        "authority_eligible": False,
        "runtime_consumable": False,
        "recovery_importable": False,
        "contains_real_task_run_validation_or_effect": False,
        "canonicalization_profile": {
            "encoding": "UTF-8",
            "unicode": "NFC",
            "object_key_order": "LEXICAL",
            "array_order": "CONTRACT_BUSINESS_KEY",
            "number_profile": "JSON_SAFE_INTEGER_NO_FLOAT_NO_BOOLEAN_ALIAS",
            "digest": "SHA-256_LOWERCASE_HEX",
            "unknown_fields": "REJECT",
        },
        "authority_bindings": {
            "F1_acceptance_decision_sha256": "e49e572055b8e367d38cc70297f5ee144482f4023c62aa46e74de35d999977b2",
            "F3_freeze_decision_sha256": "f692ef1a1af8ac15f40c8af696f486240b73a3ddf391633078e31f17eaf62529",
            "F3_manifest_sha256": "3075cda63fcb2c7937cb800a3bc09cc830d17e2f98b899828db15e09ab9f79ff",
            "F3_independent_review_sha256": "19c14d0a926d76f89a460b8d596c573a49a8fa580739227847ac765b0e52d38b",
            "F5_freeze_decision_sha256": "73270ad50c639be792f252e55befcf93c3dcc3edfffc74cb11c7c0fd212d7dbb",
            "F5_manifest_sha256": "2c867bcab4810f5625caa3cb7a649209e19fc53eab34d6ba16737dcce8d14031",
            "F5_independent_review_sha256": "edcfb8cb4e2d8ff1cabe8a5e1ffaaacf44ed1844eb32444497851f2b5c03f334",
            "F6_start_decision_sha256": "335c838830fce9d6f48dedfcdd5bd07c2be5eacba1a3ec61962305fccae6f30f",
        },
        "prospective_owner_interfaces": {
            "F5_completion_blocking_assessment": {
                "owner": "F5",
                "status": "UNACCEPTED_OWNER_INTERFACE_REQUIREMENT",
                "runtime_usable": False,
                "synthetic_fixture_only": True,
            },
            "completion_guard_currentness_assessment": {
                "owner": "ACCEPTED_COMPLETION_GUARD_OWNER",
                "status": "UNACCEPTED_OWNER_INTERFACE_REQUIREMENT",
                "runtime_usable": False,
                "synthetic_fixture_only": True,
            },
        },
        "graph_witness": build_graph_witness(),
        "decision_vectors": {
            "requirement_cases": requirement_vectors,
            "validation_set_cases": set_vectors,
            "completion_cases": completion_vectors,
        },
        "reason_precedence_trials": precedence_trials,
        "mutation_expectations": MUTATION_EXPECTATIONS,
        "summary": {
            "normative_schema_count": 10,
            "requirement_case_count": len(requirement_vectors),
            "validation_set_case_count": len(set_vectors),
            "completion_case_count": len(completion_vectors),
            "decision_vector_count": len(requirement_vectors)
            + len(set_vectors)
            + len(completion_vectors),
            "precedence_raw_trial_count": len(precedence_trials),
            "negative_mutation_count": len(MUTATION_EXPECTATIONS),
            "graph_requirement_count": 4,
            "graph_validation_set_count": 2,
            "graph_attempt_revision_count": 6,
            "graph_waiver_event_count": 1,
            "derived_eligible_case_count": 1,
            "task_done_mutation_count": 0,
            "accepted_real_task_count": 0,
            "runtime_consumable_count": 0,
            "external_effect_count": 0,
            "provider_call_count": 0,
            "raw_secret_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        },
    }
    fixture["root_fingerprint"] = typed_hash(
        "agents-os.f6.fixture-root.v0.1-r1", fixture
    )
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    fixture = build_fixture()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
