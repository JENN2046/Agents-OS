#!/usr/bin/env python3
"""Independently validate the fixed F6 R1 synthetic contract witness."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Callable


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    WORKSPACE_ROOT
    / "control-plane/registry/examples/2026-07-17-agents-os-f6-r1-validation-current-decision-v0.1.json"
)
SAFE_MAX = 2**53 - 1
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
REF_RE = re.compile(r"^[a-z0-9][a-z0-9:._/-]*$")


ROOT_FIELDS = {
    "schema_version",
    "environment",
    "authority_eligible",
    "runtime_consumable",
    "recovery_importable",
    "contains_real_task_run_validation_or_effect",
    "canonicalization_profile",
    "authority_bindings",
    "prospective_owner_interfaces",
    "graph_witness",
    "decision_vectors",
    "reason_precedence_trials",
    "mutation_expectations",
    "summary",
    "root_fingerprint",
}
GRAPH_FIELDS = {
    "read_barrier",
    "trusted_time",
    "upstream_assessments",
    "requirements",
    "waiver_events",
    "validation_sets",
    "current_validation_set_id",
    "attempt_revisions",
    "completion_input",
    "expected_decisions",
    "graph_fingerprint",
}
READ_BARRIER_FIELDS = {
    "interface_version",
    "barrier_id",
    "resident_identity_ref",
    "resident_authority_epoch",
    "schema_contract_set_fingerprint",
    "start_event_sequence",
    "end_event_sequence",
    "f3_result",
    "canonical_fingerprint",
}
TRUSTED_TIME_FIELDS = {
    "interface_version",
    "trusted_time_ref",
    "as_of_utc_ms",
    "time_policy_ref",
    "time_policy_fingerprint",
    "result",
    "read_barrier_ref",
    "read_barrier_fingerprint",
    "assessed_at_event_sequence",
    "canonical_fingerprint",
}
ASSESSMENT_FIELDS = {
    "interface_version",
    "assessment_ref",
    "owner_contract",
    "assessment_kind",
    "subject_ref",
    "subject_revision",
    "subject_fingerprint",
    "result",
    "read_barrier_ref",
    "read_barrier_fingerprint",
    "assessed_at_event_sequence",
    "canonical_fingerprint",
}
REQUIREMENT_FIELDS = {
    "interface_version",
    "task_id",
    "requirement_id",
    "requirement_revision",
    "task_spec_revision",
    "canonical_requirement_key",
    "semantic_digest",
    "provenance_bindings",
    "provenance_set_fingerprint",
    "validation_type",
    "acceptance_predicate_ref",
    "acceptance_predicate_fingerprint",
    "result_scope_ref",
    "result_scope_fingerprint",
    "validator_contract_ref",
    "validator_contract_version",
    "validator_contract_fingerprint",
    "enforcement_phase",
    "requiredness",
    "waivability",
    "waiver_duration_policy",
    "evidence_reuse_mode",
    "carry_forward_equivalence_contract_ref",
    "carry_forward_equivalence_contract_version",
    "carry_forward_equivalence_contract_fingerprint",
    "evidence_freshness_mode",
    "evidence_max_age_ms",
    "effectful_delivery_binding_required",
    "effectful_delivery_subject_ref",
    "effectful_delivery_subject_fingerprint",
    "supersedes_requirement_revision",
    "created_event_sequence",
    "canonical_fingerprint",
}
PROVENANCE_FIELDS = {
    "source_kind",
    "source_ref",
    "source_revision",
    "source_fingerprint",
    "effective_scope",
    "nonwaivable",
}
WAIVER_FIELDS = {
    "interface_version",
    "waiver_id",
    "waiver_event_id",
    "waiver_event_index",
    "prior_waiver_event_fingerprint",
    "operation",
    "task_id",
    "requirement_id",
    "requirement_revision",
    "lifecycle_generation",
    "completion_epoch",
    "task_spec_revision",
    "result_revision",
    "base_snapshot_id",
    "jenn_decision_ref",
    "jenn_decision_fingerprint",
    "jenn_decision_result",
    "reason_ref",
    "risk_acknowledgement_ref",
    "review_at_utc_ms",
    "expires_at_utc_ms",
    "follow_up_task_ref",
    "event_sequence",
    "canonical_fingerprint",
}
VALIDATION_SET_FIELDS = {
    "interface_version",
    "snapshot_id",
    "task_id",
    "lifecycle_generation",
    "completion_epoch",
    "task_spec_revision",
    "result_revision",
    "validation_set_revision",
    "base_snapshot_id",
    "freeze_trigger",
    "memberships",
    "membership_set_fingerprint",
    "source_bindings",
    "source_set_fingerprint",
    "frozen_event_ref",
    "frozen_event_sequence",
    "canonical_fingerprint",
}
MEMBERSHIP_FIELDS = {
    "requirement_id",
    "requirement_revision",
    "requirement_fingerprint",
    "active_waiver_id",
    "active_waiver_event_fingerprint",
}
SOURCE_BINDING_FIELDS = {"source_ref", "source_revision", "source_fingerprint"}
ATTEMPT_FIELDS = {
    "interface_version",
    "attempt_id",
    "attempt_number",
    "attempt_revision",
    "prior_attempt_revision_fingerprint",
    "task_id",
    "requirement_id",
    "requirement_revision",
    "requirement_fingerprint",
    "validation_set_snapshot_id",
    "validation_set_snapshot_fingerprint",
    "lifecycle_generation",
    "completion_epoch",
    "task_spec_revision",
    "result_revision",
    "candidate_commitment_ref",
    "candidate_commitment_fingerprint",
    "dependency_closure_ref",
    "dependency_closure_fingerprint",
    "validation_type",
    "validation_method",
    "state",
    "committed_event_ref",
    "committed_event_sequence",
    "command_envelope_ref",
    "command_envelope_fingerprint",
    "authority_assessment_ref",
    "authority_assessment_fingerprint",
    "authority_assessment_result",
    "evidence_refs",
    "evidence_digest",
    "evidence_currentness_ref",
    "evidence_currentness_fingerprint",
    "evidence_currentness_result",
    "evidence_observed_at_utc_ms",
    "evidence_expires_at_utc_ms",
    "source_validation_id",
    "root_source_validation_id",
    "equivalence_fingerprint",
    "f5_delivery_assessment_ref",
    "f5_delivery_assessment_fingerprint",
    "f5_delivery_assessment_result",
    "canonical_fingerprint",
}
COMPLETION_INPUT_FIELDS = {
    "interface_version",
    "task_id",
    "lifecycle_generation",
    "completion_epoch",
    "task_spec_revision",
    "result_revision",
    "task_lifecycle",
    "task_currentness_assessment_ref",
    "task_currentness_assessment_fingerprint",
    "candidate_commitment_ref",
    "candidate_commitment_fingerprint",
    "candidate_currentness_assessment_ref",
    "candidate_currentness_assessment_fingerprint",
    "validation_set_snapshot_id",
    "validation_set_snapshot_fingerprint",
    "dependency_closure_ref",
    "dependency_closure_fingerprint",
    "dependency_currentness_assessment_ref",
    "dependency_currentness_assessment_fingerprint",
    "f5_completion_blocking_assessment_ref",
    "f5_completion_blocking_assessment_fingerprint",
    "current_nonterminal_execution_run_count",
    "current_nonterminal_validation_count",
    "active_control_intent_count",
    "unknown_effect_count",
    "completion_blocking_effect_count",
    "completion_guard_currentness_assessment_ref",
    "completion_guard_currentness_assessment_fingerprint",
    "read_barrier_ref",
    "read_barrier_fingerprint",
    "trusted_time_ref",
    "trusted_time_fingerprint",
    "canonical_fingerprint",
}
EXPECTED_REQUIREMENT_FIELDS = {
    "requirement_id",
    "result",
    "current_attempt_id",
    "current_attempt_revision_fingerprint",
    "current_waiver_id",
    "current_waiver_event_fingerprint",
    "primary_reason",
    "reason_codes",
}
EXPECTED_SET_FIELDS = {
    "result",
    "current_required_count",
    "current_unwaived_required_pass_count",
    "nonterminal_attempt_count",
    "primary_reason",
    "reason_codes",
}
EXPECTED_COMPLETION_FIELDS = {
    "result",
    "completion_assessment_snapshot_may_be_created",
    "task_done_may_be_committed",
    "primary_reason",
    "reason_codes",
}
REQUIREMENT_CASE_FIELDS = {
    "case_id",
    "integrity_status",
    "requiredness",
    "waivability",
    "waiver_status",
    "validation_type",
    "effectful_delivery_binding_required",
    "latest_attempt_state",
    "attempt_binding_status",
    "authority_result",
    "evidence_currentness",
    "validation_method",
    "carry_forward_status",
    "f5_delivery_status",
    "expected_result",
    "expected_primary_reason",
    "expected_reason_codes",
    "case_fingerprint",
}
SET_CASE_FIELDS = {
    "case_id",
    "integrity_status",
    "snapshot_currentness",
    "required_decisions",
    "optional_decisions",
    "nonterminal_attempt_count",
    "expected_result",
    "expected_primary_reason",
    "expected_reason_codes",
    "case_fingerprint",
}
COMPLETION_CASE_FIELDS = {
    "case_id",
    "integrity_status",
    "read_barrier_status",
    "task_currentness",
    "task_lifecycle",
    "candidate_currentness",
    "validation_set_decision",
    "dependency_currentness",
    "f5_completion_currentness",
    "trusted_time_status",
    "nonterminal_execution_run_count",
    "nonterminal_validation_count",
    "active_control_intent_count",
    "unknown_effect_count",
    "completion_blocking_effect_count",
    "expected_result",
    "expected_primary_reason",
    "expected_reason_codes",
    "case_fingerprint",
}
TRIAL_FIELDS = {
    "unordered_case_id",
    "reducer",
    "ordering",
    "raw_conditions",
    "expected_result",
    "expected_primary_reason",
    "expected_reason_codes",
    "trial_fingerprint",
}


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


REQUIREMENT_CASE_IDS = [
    "REQ-01-FRESH-PASS-CURRENT",
    "REQ-02-FRESH-PASS-TIMELESS",
    "REQ-03-NO-ATTEMPT",
    "REQ-04-PENDING",
    "REQ-05-RUNNING",
    "REQ-06-CANCELLED",
    "REQ-07-FAILED",
    "REQ-08-INCONCLUSIVE",
    "REQ-09-ERROR",
    "REQ-10-EVIDENCE-STALE",
    "REQ-11-EVIDENCE-INDETERMINATE",
    "REQ-12-AUTHORITY-REJECTED",
    "REQ-13-AUTHORITY-INDETERMINATE",
    "REQ-14-BINDING-STALE",
    "REQ-15-CARRY-FORWARD-VALID",
    "REQ-16-CARRY-FORWARD-INVALID",
    "REQ-17-WAIVER-ACTIVE",
    "REQ-18-OPTIONAL",
    "REQ-19-WAIVER-INVALID",
    "REQ-20-EFFECTFUL-F5-CURRENT",
    "REQ-21-EFFECTFUL-F5-HISTORY",
    "REQ-22-HUMAN-CARRY-FORWARD-INVALID",
]
SET_CASE_IDS = [f"SET-{index:02d}-{suffix}" for index, suffix in enumerate(
    [
        "ALL-PASSED",
        "PASS-AND-WAIVER",
        "ALL-WAIVED",
        "PENDING",
        "FAILED",
        "INDETERMINATE",
        "OPTIONAL-IGNORED",
        "EMPTY",
        "NONTERMINAL",
        "SNAPSHOT-STALE",
    ],
    start=1,
)]
COMPLETION_CASE_IDS = [
    "COMP-01-ELIGIBLE",
    "COMP-02-BARRIER-INDETERMINATE",
    "COMP-03-BARRIER-CHANGED",
    "COMP-04-TASK-STALE",
    "COMP-05-TASK-INDETERMINATE",
    "COMP-06-TASK-ACTIVE",
    "COMP-07-CANDIDATE-STALE",
    "COMP-08-CANDIDATE-INDETERMINATE",
    "COMP-09-SET-NOT-SATISFIED",
    "COMP-10-SET-INDETERMINATE",
    "COMP-11-DEPENDENCY-CHALLENGED",
    "COMP-12-DEPENDENCY-INVALIDATED",
    "COMP-13-DEPENDENCY-INDETERMINATE",
    "COMP-14-NONTERMINAL-RUN",
    "COMP-15-NONTERMINAL-VALIDATION",
    "COMP-16-ACTIVE-CONTROL",
    "COMP-17-UNKNOWN-EFFECT",
    "COMP-18-COMPLETION-BLOCKING-EFFECT",
    "COMP-19-F5-BLOCKED",
    "COMP-20-F5-INDETERMINATE",
    "COMP-21-TIME-INDETERMINATE",
    "COMP-22-MULTIPLE-FAILURES",
]
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


class DuplicateKeyError(ValueError):
    pass


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key: {key}")
        result[key] = value
    return result


def reject_float(value: str) -> Any:
    raise ValueError(f"float forbidden: {value}")


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=no_duplicates,
        parse_float=reject_float,
    )


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


def check_scalar_tree(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                errors.append(f"{path}: non-string object key")
            elif unicodedata.normalize("NFC", key) != key:
                errors.append(f"{path}: non-NFC object key")
            check_scalar_tree(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_scalar_tree(child, f"{path}[{index}]", errors)
    elif isinstance(value, bool) or value is None:
        return
    elif type(value) is int:
        if value < -SAFE_MAX or value > SAFE_MAX:
            errors.append(f"{path}: integer outside JSON safe range")
    elif isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            errors.append(f"{path}: non-NFC string")
    else:
        errors.append(f"{path}: unsupported scalar type {type(value).__name__}")


def exact_fields(value: Any, fields: set[str], path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected object")
        return False
    actual = set(value)
    if actual != fields:
        errors.append(
            f"{path}: field inventory mismatch missing={sorted(fields-actual)} unknown={sorted(actual-fields)}"
        )
        return False
    return True


def is_hash(value: Any) -> bool:
    return isinstance(value, str) and HEX_RE.fullmatch(value) is not None


def is_ref(value: Any) -> bool:
    return isinstance(value, str) and REF_RE.fullmatch(value) is not None


def is_int(value: Any, *, positive: bool = False) -> bool:
    return type(value) is int and (-SAFE_MAX <= value <= SAFE_MAX) and (
        value > 0 if positive else value >= 0
    )


def check_hash(value: Any, path: str, errors: list[str], *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not is_hash(value):
        errors.append(f"{path}: expected lowercase SHA-256")


def check_ref(value: Any, path: str, errors: list[str], *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not is_ref(value):
        errors.append(f"{path}: invalid stable_ref")


def check_int(value: Any, path: str, errors: list[str], *, positive: bool = False, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not is_int(value, positive=positive):
        errors.append(f"{path}: expected {'positive' if positive else 'non-negative'} safe integer")


def check_fingerprint(value: dict[str, Any], domain: str, path: str, errors: list[str]) -> None:
    supplied = value.get("canonical_fingerprint")
    payload = {key: child for key, child in value.items() if key != "canonical_fingerprint"}
    expected = typed_hash(domain, payload)
    if supplied != expected:
        errors.append(f"{path}: canonical fingerprint mismatch")


def choose_primary(reasons: list[str], precedence: list[str]) -> str:
    true_reasons = set(reasons)
    return next(reason for reason in precedence if reason in true_reasons)


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
    codes = sorted(set(reasons))
    if any(reason in set(REQUIREMENT_REASON_PRECEDENCE[:8]) for reason in codes):
        return "INDETERMINATE", choose_primary(codes, REQUIREMENT_REASON_PRECEDENCE), codes
    if raw["requiredness"] == "OPTIONAL":
        return "NOT_REQUIRED", "REQUIREMENT_OPTIONAL", ["REQUIREMENT_OPTIONAL"]
    if raw["waiver_status"] == "ACTIVE_VALID":
        return "WAIVED", "REQUIREMENT_WAIVED", ["REQUIREMENT_WAIVED"]
    if raw["latest_attempt_state"] == "FAILED":
        return "UNSATISFIED", "LATEST_ATTEMPT_FAILED", ["LATEST_ATTEMPT_FAILED"]
    if raw["latest_attempt_state"] in {"INCONCLUSIVE", "ERROR", "CORRUPT"}:
        return "INDETERMINATE", "EVIDENCE_UNAVAILABLE", ["EVIDENCE_UNAVAILABLE"]
    if raw["latest_attempt_state"] == "PASSED":
        return "SATISFIED", "VALIDATION_PASSED", ["VALIDATION_PASSED"]
    return "PENDING", "CURRENT_PASS_MISSING", ["CURRENT_PASS_MISSING"]


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
    codes = sorted(set(reasons))
    if any(reason in set(SET_REASON_PRECEDENCE[:3]) for reason in codes):
        return "INDETERMINATE", choose_primary(codes, SET_REASON_PRECEDENCE), codes
    if codes:
        return "NOT_SATISFIED", choose_primary(codes, SET_REASON_PRECEDENCE), codes
    return "SATISFIED", "ALL_REQUIRED_CURRENTLY_SATISFIED", ["ALL_REQUIRED_CURRENTLY_SATISFIED"]


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
    if raw["nonterminal_execution_run_count"] > 0 or raw["nonterminal_validation_count"] > 0:
        reasons.append("NONTERMINAL_WORK_PRESENT")
    if raw["active_control_intent_count"] > 0:
        reasons.append("ACTIVE_CONTROL_INTENT")
    if (
        raw["unknown_effect_count"] > 0
        or raw["completion_blocking_effect_count"] > 0
        or raw["f5_completion_currentness"] == "BLOCKED"
    ):
        reasons.append("UNRESOLVED_EFFECT_PRESENT")
    codes = sorted(set(reasons))
    if any(reason in set(COMPLETION_REASON_PRECEDENCE[:8]) for reason in codes):
        return "INDETERMINATE", choose_primary(codes, COMPLETION_REASON_PRECEDENCE), codes
    if codes:
        return "NOT_ELIGIBLE", choose_primary(codes, COMPLETION_REASON_PRECEDENCE), codes
    return "ELIGIBLE", "ALL_COMPLETION_GATES_SATISFIED", ["ALL_COMPLETION_GATES_SATISFIED"]


def validate_read_barrier(value: Any, path: str, errors: list[str]) -> None:
    if not exact_fields(value, READ_BARRIER_FIELDS, path, errors):
        return
    if value["interface_version"] != "agents-os.f6-f3-read-barrier-input.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    check_hash(value["barrier_id"], f"{path}.barrier_id", errors)
    check_ref(value["resident_identity_ref"], f"{path}.resident_identity_ref", errors)
    check_int(value["resident_authority_epoch"], f"{path}.resident_authority_epoch", errors, positive=True)
    check_hash(value["schema_contract_set_fingerprint"], f"{path}.schema_contract_set_fingerprint", errors)
    check_int(value["start_event_sequence"], f"{path}.start_event_sequence", errors)
    check_int(value["end_event_sequence"], f"{path}.end_event_sequence", errors)
    if value["f3_result"] not in {"CURRENT", "INDETERMINATE"}:
        errors.append(f"{path}: invalid f3_result")
    identity = {
        "resident_identity_ref": value["resident_identity_ref"],
        "resident_authority_epoch": value["resident_authority_epoch"],
        "schema_contract_set_fingerprint": value["schema_contract_set_fingerprint"],
        "start_event_sequence": value["start_event_sequence"],
        "end_event_sequence": value["end_event_sequence"],
    }
    if value["barrier_id"] != typed_hash("agents-os.f6.read-barrier-id.v0.1-r1", identity):
        errors.append(f"{path}: barrier_id formula mismatch")
    if value["f3_result"] != "CURRENT" or value["start_event_sequence"] != value["end_event_sequence"]:
        errors.append(f"{path}: positive witness requires one unchanged CURRENT barrier")
    check_fingerprint(value, "agents-os.f6.read-barrier.v0.1-r1", path, errors)


def validate_trusted_time(value: Any, barrier: dict[str, Any], path: str, errors: list[str]) -> None:
    if not exact_fields(value, TRUSTED_TIME_FIELDS, path, errors):
        return
    if value["interface_version"] != "agents-os.f6-trusted-time-input.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    check_ref(value["trusted_time_ref"], f"{path}.trusted_time_ref", errors)
    check_int(value["as_of_utc_ms"], f"{path}.as_of_utc_ms", errors)
    check_ref(value["time_policy_ref"], f"{path}.time_policy_ref", errors)
    check_hash(value["time_policy_fingerprint"], f"{path}.time_policy_fingerprint", errors)
    if value["result"] not in {"CURRENT", "INDETERMINATE"}:
        errors.append(f"{path}: invalid result")
    if value["result"] != "CURRENT":
        errors.append(f"{path}: positive witness trusted time must be CURRENT")
    if value["read_barrier_ref"] != barrier.get("barrier_id") or value[
        "read_barrier_fingerprint"
    ] != barrier.get("canonical_fingerprint"):
        errors.append(f"{path}: read barrier mismatch")
    if value["assessed_at_event_sequence"] != barrier.get("end_event_sequence"):
        errors.append(f"{path}: watermark mismatch")
    check_fingerprint(value, "agents-os.f6.trusted-time.v0.1-r1", path, errors)


ASSESSMENT_MATRIX = {
    ("F1", "TASK_CURRENTNESS"): {"CURRENT", "STALE", "INDETERMINATE"},
    ("F1", "CANDIDATE_COMMITMENT_CURRENTNESS"): {"CURRENT", "STALE", "INDETERMINATE"},
    ("F1", "DEPENDENCY_CLOSURE_CURRENTNESS"): {
        "CURRENT_CONFIRMED",
        "CHALLENGED",
        "INVALIDATED",
        "INDETERMINATE",
    },
    ("F3", "VALIDATION_AUTHORITY_CURRENTNESS"): {
        "CURRENT_ACCEPTED",
        "REJECTED",
        "INDETERMINATE",
    },
    ("ACCEPTED_EVIDENCE_OWNER", "EVIDENCE_CURRENTNESS"): {
        "CURRENT",
        "TIMELESS",
        "STALE",
        "INDETERMINATE",
    },
    ("F5", "F5_DELIVERY_CURRENTNESS"): {
        "CLEAR",
        "BLOCKED",
        "APPLIED_CURRENT",
        "HISTORY_ONLY",
        "INDETERMINATE",
    },
    ("ACCEPTED_COMPLETION_GUARD_OWNER", "COMPLETION_GUARD_CURRENTNESS"): {
        "CURRENT",
        "STALE",
        "INDETERMINATE",
    },
}


def validate_assessment(value: Any, barrier: dict[str, Any], path: str, errors: list[str]) -> None:
    if not exact_fields(value, ASSESSMENT_FIELDS, path, errors):
        return
    if value["interface_version"] != "agents-os.f6-upstream-assessment-input.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    check_ref(value["assessment_ref"], f"{path}.assessment_ref", errors)
    check_ref(value["subject_ref"], f"{path}.subject_ref", errors)
    check_int(value["subject_revision"], f"{path}.subject_revision", errors)
    check_hash(value["subject_fingerprint"], f"{path}.subject_fingerprint", errors)
    allowed = ASSESSMENT_MATRIX.get((value["owner_contract"], value["assessment_kind"]))
    if allowed is None or value["result"] not in allowed:
        errors.append(f"{path}: closed owner/kind/result matrix violation")
    if value["read_barrier_ref"] != barrier.get("barrier_id") or value[
        "read_barrier_fingerprint"
    ] != barrier.get("canonical_fingerprint"):
        errors.append(f"{path}: read barrier mismatch")
    if value["assessed_at_event_sequence"] != barrier.get("end_event_sequence"):
        errors.append(f"{path}: watermark mismatch")
    check_fingerprint(value, "agents-os.f6.upstream-assessment.v0.1-r1", path, errors)


def validate_requirement(value: Any, path: str, errors: list[str]) -> None:
    if not exact_fields(value, REQUIREMENT_FIELDS, path, errors):
        return
    if value["interface_version"] != "agents-os.validation-requirement.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    for field in (
        "task_id",
        "requirement_id",
        "semantic_digest",
        "provenance_set_fingerprint",
        "acceptance_predicate_fingerprint",
        "result_scope_fingerprint",
        "validator_contract_fingerprint",
        "canonical_fingerprint",
    ):
        check_hash(value[field], f"{path}.{field}", errors)
    for field in (
        "canonical_requirement_key",
        "acceptance_predicate_ref",
        "result_scope_ref",
        "validator_contract_ref",
        "validator_contract_version",
    ):
        check_ref(value[field], f"{path}.{field}", errors)
    check_int(value["requirement_revision"], f"{path}.requirement_revision", errors, positive=True)
    check_int(value["task_spec_revision"], f"{path}.task_spec_revision", errors, positive=True)
    check_int(value["created_event_sequence"], f"{path}.created_event_sequence", errors)
    expected_id = typed_hash(
        "agents-os.f6.requirement-id.v0.1-r1",
        {
            "task_id": value["task_id"],
            "canonical_requirement_key": value["canonical_requirement_key"],
        },
    )
    if value["requirement_id"] != expected_id:
        errors.append(f"{path}: requirement_id formula mismatch")
    if value["requirement_revision"] == 1 and value["supersedes_requirement_revision"] is not None:
        errors.append(f"{path}: revision 1 must not supersede")
    if value["requirement_revision"] > 1 and value["supersedes_requirement_revision"] != value[
        "requirement_revision"
    ] - 1:
        errors.append(f"{path}: revision predecessor mismatch")
    if value["enforcement_phase"] != "POST_RESULT_VALIDATION":
        errors.append(f"{path}: pre-execution safety may not be modeled as Validation")
    if value["validation_type"] not in {
        "DETERMINISTIC",
        "RUNTIME_OBSERVATION",
        "INDEPENDENT_REVIEW",
        "HUMAN_ACCEPTANCE",
    }:
        errors.append(f"{path}: invalid validation_type")
    if value["requiredness"] not in {"REQUIRED", "OPTIONAL"}:
        errors.append(f"{path}: invalid requiredness")
    if value["waivability"] not in {"NON_WAIVABLE", "JENN_WAIVABLE"}:
        errors.append(f"{path}: invalid waivability")
    if value["waiver_duration_policy"] not in {
        "NOT_APPLICABLE",
        "COMPLETION_SCOPED_ONLY",
        "EXPIRY_REQUIRED",
    }:
        errors.append(f"{path}: invalid waiver_duration_policy")
    if value["evidence_reuse_mode"] not in {
        "NEVER_REUSE",
        "REVALIDATE_WITH_OLD_EVIDENCE",
        "CONDITIONAL_CARRY_FORWARD",
    }:
        errors.append(f"{path}: invalid evidence_reuse_mode")
    if value["evidence_freshness_mode"] not in {
        "FRESH_AT_DECISION",
        "IMMUTABLE_WHEN_FINGERPRINT_MATCHES",
        "EXPIRES_AT",
    }:
        errors.append(f"{path}: invalid evidence_freshness_mode")
    if not isinstance(value["effectful_delivery_binding_required"], bool):
        errors.append(f"{path}: effectful_delivery_binding_required must be boolean")

    provenance = value["provenance_bindings"]
    if not isinstance(provenance, list) or not provenance:
        errors.append(f"{path}: nonempty provenance required")
        provenance = []
    keys: list[tuple[str, str, int]] = []
    for index, row in enumerate(provenance):
        row_path = f"{path}.provenance_bindings[{index}]"
        if not exact_fields(row, PROVENANCE_FIELDS, row_path, errors):
            continue
        if row["source_kind"] not in {
            "NOBAO_TASK_SPEC",
            "RUST_POLICY",
            "GOAL_DOMAIN_CONTRACT",
            "JENN_EXPLICIT",
        }:
            errors.append(f"{row_path}: invalid source_kind")
        check_ref(row["source_ref"], f"{row_path}.source_ref", errors)
        check_int(row["source_revision"], f"{row_path}.source_revision", errors, positive=True)
        check_hash(row["source_fingerprint"], f"{row_path}.source_fingerprint", errors)
        if row["effective_scope"] not in {"THIS_TASK", "OPEN_TASKS", "FUTURE_ONLY"}:
            errors.append(f"{row_path}: invalid effective_scope")
        if not isinstance(row["nonwaivable"], bool):
            errors.append(f"{row_path}: nonwaivable must be boolean")
        keys.append((row["source_kind"], row["source_ref"], row["source_revision"]))
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        errors.append(f"{path}: provenance ordering/uniqueness failure")
    if value["provenance_set_fingerprint"] != typed_hash(
        "agents-os.f6.requirement-provenance-set.v0.1-r1", provenance
    ):
        errors.append(f"{path}: provenance_set_fingerprint mismatch")
    if any(row.get("nonwaivable") is True for row in provenance) and (
        value["waivability"] != "NON_WAIVABLE"
        or value["waiver_duration_policy"] != "NOT_APPLICABLE"
    ):
        errors.append(f"{path}: nonwaivable provenance was weakened")
    if value["waivability"] == "NON_WAIVABLE" and value["waiver_duration_policy"] != "NOT_APPLICABLE":
        errors.append(f"{path}: NON_WAIVABLE duration matrix violation")
    if value["waivability"] == "JENN_WAIVABLE" and value["waiver_duration_policy"] not in {
        "COMPLETION_SCOPED_ONLY",
        "EXPIRY_REQUIRED",
    }:
        errors.append(f"{path}: JENN_WAIVABLE duration matrix violation")
    if value["validation_type"] == "HUMAN_ACCEPTANCE" and (
        value["evidence_reuse_mode"] != "NEVER_REUSE"
        or value["evidence_freshness_mode"] != "FRESH_AT_DECISION"
    ):
        errors.append(f"{path}: HUMAN_ACCEPTANCE reuse matrix violation")
    if value["effectful_delivery_binding_required"] and (
        value["evidence_reuse_mode"] != "NEVER_REUSE"
        or value["evidence_freshness_mode"] != "FRESH_AT_DECISION"
    ):
        errors.append(f"{path}: effectful reuse matrix violation")
    if value["effectful_delivery_binding_required"]:
        check_ref(
            value["effectful_delivery_subject_ref"],
            f"{path}.effectful_delivery_subject_ref",
            errors,
        )
        check_hash(
            value["effectful_delivery_subject_fingerprint"],
            f"{path}.effectful_delivery_subject_fingerprint",
            errors,
        )
    elif value["effectful_delivery_subject_ref"] is not None or value[
        "effectful_delivery_subject_fingerprint"
    ] is not None:
        errors.append(f"{path}: non-effectful Requirement contains delivery subject")
    carry_fields = (
        value["carry_forward_equivalence_contract_ref"],
        value["carry_forward_equivalence_contract_version"],
        value["carry_forward_equivalence_contract_fingerprint"],
    )
    if value["evidence_reuse_mode"] == "CONDITIONAL_CARRY_FORWARD":
        if value["validation_type"] != "DETERMINISTIC" or value[
            "effectful_delivery_binding_required"
        ]:
            errors.append(f"{path}: carry-forward eligibility matrix violation")
        if any(item is None for item in carry_fields):
            errors.append(f"{path}: carry-forward contract incomplete")
        if value["evidence_freshness_mode"] not in {
            "IMMUTABLE_WHEN_FINGERPRINT_MATCHES",
            "EXPIRES_AT",
        }:
            errors.append(f"{path}: carry-forward freshness matrix violation")
    elif any(item is not None for item in carry_fields):
        errors.append(f"{path}: non-carry Requirement contains carry contract")
    if value["evidence_freshness_mode"] == "EXPIRES_AT":
        check_int(value["evidence_max_age_ms"], f"{path}.evidence_max_age_ms", errors, positive=True)
    elif value["evidence_max_age_ms"] is not None:
        errors.append(f"{path}: evidence_max_age_ms must be null")
    check_fingerprint(value, "agents-os.f6.requirement.v0.1-r1", path, errors)


def validate_waiver(
    value: Any,
    requirement_by_id: dict[str, dict[str, Any]],
    snapshot_by_id: dict[str, dict[str, Any]],
    path: str,
    errors: list[str],
) -> None:
    if not exact_fields(value, WAIVER_FIELDS, path, errors):
        return
    if value["interface_version"] != "agents-os.requirement-waiver-event.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    for field in ("waiver_id", "waiver_event_id", "base_snapshot_id", "canonical_fingerprint"):
        check_hash(value[field], f"{path}.{field}", errors)
    for field in ("task_id", "requirement_id"):
        check_hash(value[field], f"{path}.{field}", errors)
    for field in (
        "waiver_event_index",
        "requirement_revision",
        "lifecycle_generation",
        "completion_epoch",
        "task_spec_revision",
        "result_revision",
    ):
        check_int(value[field], f"{path}.{field}", errors, positive=True)
    check_int(value["event_sequence"], f"{path}.event_sequence", errors)
    check_hash(value["prior_waiver_event_fingerprint"], f"{path}.prior_waiver_event_fingerprint", errors, nullable=True)
    if value["operation"] not in {"GRANT", "REVOKE", "EXPIRE", "INVALIDATE"}:
        errors.append(f"{path}: invalid operation")
    identity = {
        "task_id": value["task_id"],
        "requirement_id": value["requirement_id"],
        "requirement_revision": value["requirement_revision"],
        "lifecycle_generation": value["lifecycle_generation"],
        "completion_epoch": value["completion_epoch"],
        "task_spec_revision": value["task_spec_revision"],
        "result_revision": value["result_revision"],
    }
    if value["waiver_id"] != typed_hash("agents-os.f6.waiver-id.v0.1-r1", identity):
        errors.append(f"{path}: waiver_id formula mismatch")
    event_identity = {
        "waiver_id": value["waiver_id"],
        "waiver_event_index": value["waiver_event_index"],
        "operation": value["operation"],
    }
    if value["waiver_event_id"] != typed_hash(
        "agents-os.f6.waiver-event-id.v0.1-r1", event_identity
    ):
        errors.append(f"{path}: waiver_event_id formula mismatch")
    requirement = requirement_by_id.get(value["requirement_id"])
    base_snapshot = snapshot_by_id.get(value["base_snapshot_id"])
    if requirement is None or base_snapshot is None:
        errors.append(f"{path}: unresolved Requirement or base snapshot")
    else:
        if requirement["task_id"] != value["task_id"] or requirement[
            "requirement_revision"
        ] != value["requirement_revision"]:
            errors.append(f"{path}: Requirement binding mismatch")
        for field in (
            "task_id",
            "lifecycle_generation",
            "completion_epoch",
            "task_spec_revision",
            "result_revision",
        ):
            if base_snapshot[field] != value[field]:
                errors.append(f"{path}: base snapshot {field} mismatch")
        if requirement["waivability"] != "JENN_WAIVABLE":
            errors.append(f"{path}: NON_WAIVABLE Requirement cannot be granted")
    if value["operation"] == "GRANT":
        if value["waiver_event_index"] != 1 or value["prior_waiver_event_fingerprint"] is not None:
            errors.append(f"{path}: GRANT must be first waiver event")
        check_ref(value["jenn_decision_ref"], f"{path}.jenn_decision_ref", errors)
        check_hash(value["jenn_decision_fingerprint"], f"{path}.jenn_decision_fingerprint", errors)
        if value["jenn_decision_result"] != "CURRENT_ACCEPTED":
            errors.append(f"{path}: GRANT requires current Jenn decision")
        check_ref(value["risk_acknowledgement_ref"], f"{path}.risk_acknowledgement_ref", errors)
        if requirement is not None and requirement["waiver_duration_policy"] == "COMPLETION_SCOPED_ONLY":
            check_int(value["review_at_utc_ms"], f"{path}.review_at_utc_ms", errors, positive=True)
            if value["expires_at_utc_ms"] is not None or value["follow_up_task_ref"] is not None:
                errors.append(f"{path}: completion-scoped waiver field matrix violation")
        if requirement is not None and requirement["waiver_duration_policy"] == "EXPIRY_REQUIRED":
            check_int(value["expires_at_utc_ms"], f"{path}.expires_at_utc_ms", errors, positive=True)
            check_ref(value["follow_up_task_ref"], f"{path}.follow_up_task_ref", errors)
    else:
        if any(
            value[field] is not None
            for field in (
                "jenn_decision_ref",
                "jenn_decision_fingerprint",
                "risk_acknowledgement_ref",
                "review_at_utc_ms",
                "expires_at_utc_ms",
                "follow_up_task_ref",
            )
        ) or value["jenn_decision_result"] != "NOT_APPLICABLE":
            errors.append(f"{path}: terminal waiver event field matrix violation")
    check_ref(value["reason_ref"], f"{path}.reason_ref", errors)
    check_fingerprint(value, "agents-os.f6.waiver-event.v0.1-r1", path, errors)


def validate_waiver_chains(
    events: list[dict[str, Any]], errors: list[str]
) -> dict[str, dict[str, Any]]:
    ordering = [
        (event.get("waiver_id"), event.get("waiver_event_index")) for event in events
    ]
    if ordering != sorted(ordering) or len(ordering) != len(set(ordering)):
        errors.append("graph.waiver_events: ordering or duplicate event failure")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_ids: set[str] = set()
    for event in events:
        groups[event.get("waiver_id")].append(event)
        event_id = event.get("waiver_event_id")
        if event_id in event_ids:
            errors.append("graph.waiver_events: duplicate waiver_event_id")
        event_ids.add(event_id)
    heads: dict[str, dict[str, Any]] = {}
    for waiver_id, rows in groups.items():
        rows.sort(key=lambda item: item.get("waiver_event_index", -1))
        indices = [row.get("waiver_event_index") for row in rows]
        if indices != list(range(1, len(rows) + 1)):
            errors.append(f"waiver {waiver_id}: event index gap or branch")
            continue
        if rows[0].get("operation") != "GRANT":
            errors.append(f"waiver {waiver_id}: first operation is not GRANT")
        for index, row in enumerate(rows[1:], start=1):
            if row.get("prior_waiver_event_fingerprint") != rows[index - 1].get(
                "canonical_fingerprint"
            ):
                errors.append(f"waiver {waiver_id}: prior fingerprint mismatch")
            if rows[index - 1].get("operation") in {"REVOKE", "EXPIRE", "INVALIDATE"}:
                errors.append(f"waiver {waiver_id}: successor after terminal operation")
            immutable = (
                "task_id",
                "requirement_id",
                "requirement_revision",
                "lifecycle_generation",
                "completion_epoch",
                "task_spec_revision",
                "result_revision",
                "base_snapshot_id",
            )
            if any(row.get(field) != rows[0].get(field) for field in immutable):
                errors.append(f"waiver {waiver_id}: immutable binding changed")
            if row.get("event_sequence", -1) <= rows[index - 1].get(
                "event_sequence", SAFE_MAX
            ):
                errors.append(f"waiver {waiver_id}: Event sequence did not advance")
        heads[waiver_id] = rows[-1]
    return heads


def validate_validation_set(
    value: Any,
    requirement_by_id: dict[str, dict[str, Any]],
    waiver_by_id: dict[str, dict[str, Any]],
    path: str,
    errors: list[str],
) -> None:
    if not exact_fields(value, VALIDATION_SET_FIELDS, path, errors):
        return
    if value["interface_version"] != "agents-os.validation-set-snapshot.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    for field in (
        "snapshot_id",
        "task_id",
        "membership_set_fingerprint",
        "source_set_fingerprint",
        "canonical_fingerprint",
    ):
        check_hash(value[field], f"{path}.{field}", errors)
    check_hash(value["base_snapshot_id"], f"{path}.base_snapshot_id", errors, nullable=True)
    for field in (
        "lifecycle_generation",
        "completion_epoch",
        "task_spec_revision",
        "result_revision",
        "validation_set_revision",
    ):
        check_int(value[field], f"{path}.{field}", errors, positive=True)
    check_int(value["frozen_event_sequence"], f"{path}.frozen_event_sequence", errors)
    check_ref(value["frozen_event_ref"], f"{path}.frozen_event_ref", errors)
    if value["freeze_trigger"] not in {
        "FIRST_RUN",
        "FIRST_FORMAL_VALIDATION",
        "FIRST_VERIFYING",
        "EXTENSION",
        "WAIVER_CHANGE",
    }:
        errors.append(f"{path}: invalid freeze_trigger")
    if value["validation_set_revision"] == 1 and value["base_snapshot_id"] is not None:
        errors.append(f"{path}: revision 1 must have null base")
    if value["validation_set_revision"] > 1 and value["base_snapshot_id"] is None:
        errors.append(f"{path}: later revision requires base")
    memberships = value["memberships"]
    if not isinstance(memberships, list):
        errors.append(f"{path}: memberships must be list")
        memberships = []
    membership_keys: list[str] = []
    for index, member in enumerate(memberships):
        member_path = f"{path}.memberships[{index}]"
        if not exact_fields(member, MEMBERSHIP_FIELDS, member_path, errors):
            continue
        check_hash(member["requirement_id"], f"{member_path}.requirement_id", errors)
        check_int(member["requirement_revision"], f"{member_path}.requirement_revision", errors, positive=True)
        check_hash(member["requirement_fingerprint"], f"{member_path}.requirement_fingerprint", errors)
        check_hash(member["active_waiver_id"], f"{member_path}.active_waiver_id", errors, nullable=True)
        check_hash(
            member["active_waiver_event_fingerprint"],
            f"{member_path}.active_waiver_event_fingerprint",
            errors,
            nullable=True,
        )
        if (member["active_waiver_id"] is None) != (
            member["active_waiver_event_fingerprint"] is None
        ):
            errors.append(f"{member_path}: waiver ref/fingerprint nullability mismatch")
        requirement = requirement_by_id.get(member["requirement_id"])
        if requirement is None:
            errors.append(f"{member_path}: unknown Requirement")
        elif requirement["requirement_revision"] != member["requirement_revision"] or requirement[
            "canonical_fingerprint"
        ] != member["requirement_fingerprint"]:
            errors.append(f"{member_path}: Requirement revision/fingerprint mismatch")
        elif any(
            source.get("effective_scope") == "FUTURE_ONLY"
            for source in requirement.get("provenance_bindings", [])
        ):
            errors.append(f"{member_path}: FUTURE_ONLY provenance is not current")
        if member["active_waiver_id"] is not None:
            waiver = waiver_by_id.get(member["active_waiver_id"])
            if waiver is None or waiver["canonical_fingerprint"] != member[
                "active_waiver_event_fingerprint"
            ]:
                errors.append(f"{member_path}: active waiver target mismatch")
            elif waiver.get("base_snapshot_id") != value.get(
                "base_snapshot_id"
            ) or waiver.get("event_sequence", SAFE_MAX + 1) > value.get(
                "frozen_event_sequence", -1
            ):
                errors.append(
                    f"{member_path}: waiver is not ordered between base and snapshot"
                )
        membership_keys.append(member["requirement_id"])
    if membership_keys != sorted(membership_keys) or len(membership_keys) != len(set(membership_keys)):
        errors.append(f"{path}: membership ordering/uniqueness failure")
    if value["membership_set_fingerprint"] != typed_hash(
        "agents-os.f6.validation-membership-set.v0.1-r1", memberships
    ):
        errors.append(f"{path}: membership_set_fingerprint mismatch")
    sources = value["source_bindings"]
    if not isinstance(sources, list) or not sources:
        errors.append(f"{path}: nonempty source_bindings required")
        sources = []
    source_keys: list[tuple[str, int]] = []
    for index, source in enumerate(sources):
        source_path = f"{path}.source_bindings[{index}]"
        if not exact_fields(source, SOURCE_BINDING_FIELDS, source_path, errors):
            continue
        check_ref(source["source_ref"], f"{source_path}.source_ref", errors)
        check_int(source["source_revision"], f"{source_path}.source_revision", errors, positive=True)
        check_hash(source["source_fingerprint"], f"{source_path}.source_fingerprint", errors)
        source_keys.append((source["source_ref"], source["source_revision"]))
    if source_keys != sorted(source_keys) or len(source_keys) != len(set(source_keys)):
        errors.append(f"{path}: source ordering/uniqueness failure")
    expected_source_map: dict[tuple[str, int], dict[str, Any]] = {}
    source_conflict = False
    for member in memberships:
        requirement = requirement_by_id.get(member.get("requirement_id"))
        if requirement is None:
            continue
        for provenance in requirement.get("provenance_bindings", []):
            key = (provenance.get("source_ref"), provenance.get("source_revision"))
            projected = {
                "source_ref": provenance.get("source_ref"),
                "source_revision": provenance.get("source_revision"),
                "source_fingerprint": provenance.get("source_fingerprint"),
            }
            existing = expected_source_map.get(key)
            if existing is not None and existing != projected:
                source_conflict = True
            expected_source_map[key] = projected
    expected_sources = [expected_source_map[key] for key in sorted(expected_source_map)]
    if source_conflict or sources != expected_sources:
        errors.append(f"{path}: source_bindings are not the exact Requirement provenance union")
    if value["source_set_fingerprint"] != typed_hash(
        "agents-os.f6.validation-source-set.v0.1-r1", sources
    ):
        errors.append(f"{path}: source_set_fingerprint mismatch")
    identity = {
        "task_id": value["task_id"],
        "lifecycle_generation": value["lifecycle_generation"],
        "completion_epoch": value["completion_epoch"],
        "task_spec_revision": value["task_spec_revision"],
        "result_revision": value["result_revision"],
        "validation_set_revision": value["validation_set_revision"],
        "base_snapshot_id": value["base_snapshot_id"],
        "freeze_trigger": value["freeze_trigger"],
        "membership_set_fingerprint": value["membership_set_fingerprint"],
        "source_set_fingerprint": value["source_set_fingerprint"],
    }
    if value["snapshot_id"] != typed_hash("agents-os.f6.validation-set-id.v0.1-r1", identity):
        errors.append(f"{path}: snapshot_id formula mismatch")
    check_fingerprint(value, "agents-os.f6.validation-set.v0.1-r1", path, errors)


def validate_attempt(
    value: Any,
    requirement_by_id: dict[str, dict[str, Any]],
    snapshot_by_id: dict[str, dict[str, Any]],
    assessment_by_ref: dict[str, dict[str, Any]],
    trusted_time: dict[str, Any],
    path: str,
    errors: list[str],
) -> None:
    if not exact_fields(value, ATTEMPT_FIELDS, path, errors):
        return
    if value["interface_version"] != "agents-os.validation-attempt-revision.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    for field in (
        "attempt_id",
        "task_id",
        "requirement_id",
        "requirement_fingerprint",
        "validation_set_snapshot_id",
        "validation_set_snapshot_fingerprint",
        "candidate_commitment_fingerprint",
        "dependency_closure_fingerprint",
        "command_envelope_fingerprint",
        "authority_assessment_fingerprint",
        "canonical_fingerprint",
    ):
        check_hash(value[field], f"{path}.{field}", errors)
    for field in (
        "attempt_number",
        "attempt_revision",
        "requirement_revision",
        "lifecycle_generation",
        "completion_epoch",
        "task_spec_revision",
        "result_revision",
    ):
        check_int(value[field], f"{path}.{field}", errors, positive=True)
    check_int(value["committed_event_sequence"], f"{path}.committed_event_sequence", errors)
    check_hash(value["prior_attempt_revision_fingerprint"], f"{path}.prior_attempt_revision_fingerprint", errors, nullable=True)
    for field in (
        "candidate_commitment_ref",
        "dependency_closure_ref",
        "committed_event_ref",
        "command_envelope_ref",
        "authority_assessment_ref",
    ):
        check_ref(value[field], f"{path}.{field}", errors)
    if value["validation_type"] not in {
        "DETERMINISTIC",
        "RUNTIME_OBSERVATION",
        "INDEPENDENT_REVIEW",
        "HUMAN_ACCEPTANCE",
    }:
        errors.append(f"{path}: invalid validation_type")
    if value["validation_method"] not in {
        "FRESH_VALIDATION",
        "EVIDENCE_CARRY_FORWARD_REVIEW",
    }:
        errors.append(f"{path}: invalid validation_method")
    if value["state"] not in {
        "PENDING",
        "RUNNING",
        "PASSED",
        "FAILED",
        "INCONCLUSIVE",
        "ERROR",
        "CANCELLED",
    }:
        errors.append(f"{path}: invalid state")
    if value["authority_assessment_result"] not in {
        "CURRENT_ACCEPTED",
        "REJECTED",
        "INDETERMINATE",
    }:
        errors.append(f"{path}: invalid authority assessment result")
    identity = {
        "task_id": value["task_id"],
        "requirement_id": value["requirement_id"],
        "requirement_revision": value["requirement_revision"],
        "lifecycle_generation": value["lifecycle_generation"],
        "completion_epoch": value["completion_epoch"],
        "task_spec_revision": value["task_spec_revision"],
        "result_revision": value["result_revision"],
        "attempt_number": value["attempt_number"],
    }
    if value["attempt_id"] != typed_hash("agents-os.f6.validation-attempt-id.v0.1-r1", identity):
        errors.append(f"{path}: attempt_id formula mismatch")
    requirement = requirement_by_id.get(value["requirement_id"])
    snapshot = snapshot_by_id.get(value["validation_set_snapshot_id"])
    if requirement is None or snapshot is None:
        errors.append(f"{path}: unresolved Requirement or Validation Set")
    else:
        if requirement["canonical_fingerprint"] != value["requirement_fingerprint"] or requirement[
            "requirement_revision"
        ] != value["requirement_revision"]:
            errors.append(f"{path}: Requirement binding mismatch")
        if snapshot["canonical_fingerprint"] != value["validation_set_snapshot_fingerprint"]:
            errors.append(f"{path}: snapshot fingerprint mismatch")
        for field in (
            "task_id",
            "lifecycle_generation",
            "completion_epoch",
            "task_spec_revision",
            "result_revision",
        ):
            if snapshot[field] != value[field]:
                errors.append(f"{path}: snapshot {field} mismatch")
        if requirement["validation_type"] != value["validation_type"]:
            errors.append(f"{path}: validation_type mismatch")
    authority = assessment_by_ref.get(value["authority_assessment_ref"])
    if authority is None or authority.get("canonical_fingerprint") != value[
        "authority_assessment_fingerprint"
    ] or authority.get("assessment_kind") != "VALIDATION_AUTHORITY_CURRENTNESS" or authority.get(
        "result"
    ) != value["authority_assessment_result"]:
        errors.append(f"{path}: authority assessment binding mismatch")
    elif requirement is not None and (
        authority.get("subject_ref") != requirement["validator_contract_ref"]
        or authority.get("subject_fingerprint")
        != requirement["validator_contract_fingerprint"]
    ):
        errors.append(
            f"{path}: authority assessment subject is not the exact validator contract"
        )

    evidence_terminal = value["state"] in {"PASSED", "FAILED", "INCONCLUSIVE"}
    if evidence_terminal:
        if not isinstance(value["evidence_refs"], list) or not value["evidence_refs"]:
            errors.append(f"{path}: terminal result requires evidence refs")
        else:
            for index, ref in enumerate(value["evidence_refs"]):
                check_ref(ref, f"{path}.evidence_refs[{index}]", errors)
        check_hash(value["evidence_digest"], f"{path}.evidence_digest", errors)
        check_ref(value["evidence_currentness_ref"], f"{path}.evidence_currentness_ref", errors)
        check_hash(value["evidence_currentness_fingerprint"], f"{path}.evidence_currentness_fingerprint", errors)
        check_int(value["evidence_observed_at_utc_ms"], f"{path}.evidence_observed_at_utc_ms", errors)
        check_int(
            value["evidence_expires_at_utc_ms"],
            f"{path}.evidence_expires_at_utc_ms",
            errors,
            positive=True,
            nullable=True,
        )
        evidence = assessment_by_ref.get(value["evidence_currentness_ref"])
        if evidence is None or evidence.get("canonical_fingerprint") != value[
            "evidence_currentness_fingerprint"
        ] or evidence.get("assessment_kind") != "EVIDENCE_CURRENTNESS" or evidence.get(
            "result"
        ) != value["evidence_currentness_result"]:
            errors.append(f"{path}: evidence assessment binding mismatch")
        elif evidence.get("subject_ref") not in value["evidence_refs"] or evidence.get(
            "subject_fingerprint"
        ) != value["evidence_digest"]:
            errors.append(f"{path}: evidence assessment does not bind exact evidence bytes")
        as_of = trusted_time.get("as_of_utc_ms")
        observed = value["evidence_observed_at_utc_ms"]
        if is_int(as_of) and is_int(observed) and observed > as_of:
            errors.append(f"{path}: evidence observation is in the future")
        if requirement is not None:
            freshness_mode = requirement["evidence_freshness_mode"]
            if freshness_mode == "EXPIRES_AT":
                expires = value["evidence_expires_at_utc_ms"]
                max_age = requirement["evidence_max_age_ms"]
                if not is_int(expires, positive=True) or not is_int(max_age, positive=True):
                    errors.append(f"{path}: EXPIRES_AT evidence requires exact expiry inputs")
                else:
                    if expires != observed + max_age:
                        errors.append(f"{path}: evidence expiry formula mismatch")
                    if is_int(as_of) and as_of >= expires:
                        errors.append(f"{path}: evidence has expired")
            elif value["evidence_expires_at_utc_ms"] is not None:
                errors.append(f"{path}: non-expiring Requirement contains evidence expiry")
            if value["evidence_currentness_result"] == "TIMELESS" and freshness_mode != (
                "IMMUTABLE_WHEN_FINGERPRINT_MATCHES"
            ):
                errors.append(f"{path}: TIMELESS evidence violates Requirement freshness")
            if freshness_mode == "FRESH_AT_DECISION" and value[
                "evidence_currentness_result"
            ] != "CURRENT":
                errors.append(f"{path}: fresh-at-decision evidence is not CURRENT")
        if value["state"] == "PASSED" and value["evidence_currentness_result"] not in {
            "CURRENT",
            "TIMELESS",
        }:
            errors.append(f"{path}: PASSED evidence is not current")
    else:
        if value["evidence_refs"] != [] or any(
            value[field] is not None
            for field in (
                "evidence_digest",
                "evidence_currentness_ref",
                "evidence_currentness_fingerprint",
                "evidence_observed_at_utc_ms",
                "evidence_expires_at_utc_ms",
            )
        ) or value["evidence_currentness_result"] != "NOT_APPLICABLE":
            errors.append(f"{path}: non-evidence state contains evidence fields")
    if value["validation_method"] == "FRESH_VALIDATION":
        if any(
            value[field] is not None
            for field in (
                "source_validation_id",
                "root_source_validation_id",
                "equivalence_fingerprint",
            )
        ):
            errors.append(f"{path}: fresh Validation contains carry-forward fields")
    else:
        for field in ("source_validation_id", "root_source_validation_id", "equivalence_fingerprint"):
            check_hash(value[field], f"{path}.{field}", errors)
        if requirement is not None and (
            requirement["evidence_reuse_mode"] != "CONDITIONAL_CARRY_FORWARD"
            or requirement["validation_type"] == "HUMAN_ACCEPTANCE"
            or requirement["effectful_delivery_binding_required"]
        ):
            errors.append(f"{path}: carry-forward forbidden by Requirement")
    if requirement is not None and requirement["effectful_delivery_binding_required"]:
        check_ref(value["f5_delivery_assessment_ref"], f"{path}.f5_delivery_assessment_ref", errors)
        check_hash(value["f5_delivery_assessment_fingerprint"], f"{path}.f5_delivery_assessment_fingerprint", errors)
        if value["f5_delivery_assessment_result"] != "APPLIED_CURRENT":
            errors.append(f"{path}: effectful F5 evidence not current")
        f5 = assessment_by_ref.get(value["f5_delivery_assessment_ref"])
        if f5 is None or f5.get("canonical_fingerprint") != value[
            "f5_delivery_assessment_fingerprint"
        ] or f5.get("assessment_kind") != "F5_DELIVERY_CURRENTNESS" or f5.get(
            "result"
        ) != "APPLIED_CURRENT":
            errors.append(f"{path}: effectful F5 assessment binding mismatch")
        elif f5.get("subject_ref") != requirement[
            "effectful_delivery_subject_ref"
        ] or f5.get("subject_fingerprint") != requirement[
            "effectful_delivery_subject_fingerprint"
        ]:
            errors.append(f"{path}: effectful F5 assessment subject mismatch")
    elif any(
        value[field] is not None
        for field in ("f5_delivery_assessment_ref", "f5_delivery_assessment_fingerprint")
    ) or value["f5_delivery_assessment_result"] != "NOT_REQUIRED":
        errors.append(f"{path}: non-effectful attempt contains F5 binding")
    check_fingerprint(value, "agents-os.f6.validation-attempt.v0.1-r1", path, errors)


def validate_attempt_chains(
    attempts: list[dict[str, Any]],
    requirement_by_id: dict[str, dict[str, Any]],
    current_snapshot: dict[str, Any],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    keys = [
        (row.get("requirement_id"), row.get("attempt_number"), row.get("attempt_revision"))
        for row in attempts
    ]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        errors.append("graph.attempt_revisions: ordering or duplicate revision failure")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attempts:
        groups[row.get("attempt_id")].append(row)
    heads_by_binding: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    immutable_fields = {
        "attempt_id",
        "attempt_number",
        "task_id",
        "requirement_id",
        "requirement_revision",
        "requirement_fingerprint",
        "validation_set_snapshot_id",
        "validation_set_snapshot_fingerprint",
        "lifecycle_generation",
        "completion_epoch",
        "task_spec_revision",
        "result_revision",
        "candidate_commitment_ref",
        "candidate_commitment_fingerprint",
        "dependency_closure_ref",
        "dependency_closure_fingerprint",
        "validation_type",
        "validation_method",
        "authority_assessment_ref",
        "authority_assessment_fingerprint",
        "authority_assessment_result",
        "source_validation_id",
        "root_source_validation_id",
        "equivalence_fingerprint",
        "f5_delivery_assessment_ref",
        "f5_delivery_assessment_fingerprint",
        "f5_delivery_assessment_result",
    }
    transitions = {
        "PENDING": {"RUNNING", "CANCELLED"},
        "RUNNING": {"PASSED", "FAILED", "INCONCLUSIVE", "ERROR", "CANCELLED"},
    }
    for attempt_id, rows in groups.items():
        rows.sort(key=lambda item: item.get("attempt_revision", -1))
        revisions = [row.get("attempt_revision") for row in rows]
        if revisions != list(range(1, len(rows) + 1)):
            errors.append(f"attempt {attempt_id}: revision chain gap/branch")
            continue
        first = rows[0]
        if first.get("state") != "PENDING" or first.get("prior_attempt_revision_fingerprint") is not None:
            errors.append(f"attempt {attempt_id}: first revision must be PENDING with null prior")
        for index, row in enumerate(rows):
            if any(row.get(field) != first.get(field) for field in immutable_fields):
                errors.append(f"attempt {attempt_id}: immutable binding changed")
            if index > 0:
                prior = rows[index - 1]
                if row.get("prior_attempt_revision_fingerprint") != prior.get("canonical_fingerprint"):
                    errors.append(f"attempt {attempt_id}: prior fingerprint mismatch")
                if row.get("state") not in transitions.get(prior.get("state"), set()):
                    errors.append(f"attempt {attempt_id}: invalid state transition")
                if row.get("committed_event_sequence", -1) <= prior.get(
                    "committed_event_sequence", SAFE_MAX
                ):
                    errors.append(f"attempt {attempt_id}: Event sequence did not advance")
        binding = (
            first.get("task_id"),
            first.get("requirement_id"),
            first.get("requirement_revision"),
            first.get("validation_set_snapshot_id"),
            first.get("lifecycle_generation"),
            first.get("completion_epoch"),
            first.get("task_spec_revision"),
            first.get("result_revision"),
        )
        heads_by_binding[binding].append(rows[-1])
    current_heads: dict[str, dict[str, Any]] = {}
    for binding, heads in heads_by_binding.items():
        heads.sort(key=lambda item: item.get("attempt_number", -1))
        numbers = [head.get("attempt_number") for head in heads]
        if numbers != list(range(1, len(heads) + 1)):
            errors.append(f"attempt binding {binding}: attempt number gap/duplicate")
        for index, head in enumerate(heads[1:], start=1):
            if head.get("committed_event_sequence", -1) <= heads[index - 1].get(
                "committed_event_sequence", SAFE_MAX
            ):
                errors.append(
                    f"attempt binding {binding}: later attempt is not later in Event order"
                )
        expected_current_binding = (
            current_snapshot.get("task_id"),
            binding[1],
            binding[2],
            current_snapshot.get("snapshot_id"),
            current_snapshot.get("lifecycle_generation"),
            current_snapshot.get("completion_epoch"),
            current_snapshot.get("task_spec_revision"),
            current_snapshot.get("result_revision"),
        )
        if binding == expected_current_binding:
            if binding[1] in current_heads:
                errors.append(f"Requirement {binding[1]}: multiple current attempt bindings")
            current_heads[binding[1]] = heads[-1]
    for requirement_id in current_heads:
        if requirement_id not in requirement_by_id:
            errors.append(f"attempt head references unknown Requirement {requirement_id}")
    return current_heads


def validate_carry_forward_links(
    attempts: list[dict[str, Any]],
    requirement_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attempts:
        groups[row.get("attempt_id")].append(row)
    heads: dict[str, dict[str, Any]] = {}
    for attempt_id, rows in groups.items():
        rows.sort(key=lambda item: item.get("attempt_revision", -1))
        if rows:
            heads[attempt_id] = rows[-1]
    for current in heads.values():
        if current.get("validation_method") != "EVIDENCE_CARRY_FORWARD_REVIEW":
            continue
        source_id = current.get("source_validation_id")
        if source_id != current.get("root_source_validation_id"):
            errors.append(f"attempt {current.get('attempt_id')}: carry-forward root must equal source")
        source = heads.get(source_id)
        if source is None:
            errors.append(f"attempt {current.get('attempt_id')}: unresolved carry-forward source")
            continue
        if source.get("validation_method") != "FRESH_VALIDATION" or source.get("state") != "PASSED":
            errors.append(f"attempt {current.get('attempt_id')}: source is not original FRESH PASSED")
        for field in ("task_id", "requirement_id", "requirement_revision"):
            if source.get(field) != current.get(field):
                errors.append(f"attempt {current.get('attempt_id')}: carry-forward source {field} mismatch")
        if not is_int(source.get("committed_event_sequence")) or not is_int(
            current.get("committed_event_sequence")
        ) or source["committed_event_sequence"] >= current["committed_event_sequence"]:
            errors.append(f"attempt {current.get('attempt_id')}: source is not earlier")
        requirement = requirement_by_id.get(current.get("requirement_id"))
        if requirement is None:
            continue
        expected = typed_hash(
            "agents-os.f6.carry-forward-equivalence.v0.1-r1",
            {
                "source_validation_id": source_id,
                "source_evidence_digest": source.get("evidence_digest"),
                "task_id": current.get("task_id"),
                "requirement_id": current.get("requirement_id"),
                "requirement_revision": current.get("requirement_revision"),
                "lifecycle_generation": current.get("lifecycle_generation"),
                "completion_epoch": current.get("completion_epoch"),
                "task_spec_revision": current.get("task_spec_revision"),
                "result_revision": current.get("result_revision"),
                "validator_contract_fingerprint": requirement.get(
                    "validator_contract_fingerprint"
                ),
                "carry_forward_equivalence_contract_fingerprint": requirement.get(
                    "carry_forward_equivalence_contract_fingerprint"
                ),
                "result_scope_fingerprint": requirement.get("result_scope_fingerprint"),
                "evidence_currentness_fingerprint": current.get(
                    "evidence_currentness_fingerprint"
                ),
            },
        )
        if current.get("equivalence_fingerprint") != expected:
            errors.append(f"attempt {current.get('attempt_id')}: equivalence formula mismatch")


def validate_completion_input(
    value: Any,
    current_snapshot: dict[str, Any],
    barrier: dict[str, Any],
    trusted_time: dict[str, Any],
    assessment_by_ref: dict[str, dict[str, Any]],
    path: str,
    errors: list[str],
) -> dict[str, str]:
    statuses = {
        "task": "INDETERMINATE",
        "candidate": "INDETERMINATE",
        "dependency": "INDETERMINATE",
        "f5": "INDETERMINATE",
    }
    if not exact_fields(value, COMPLETION_INPUT_FIELDS, path, errors):
        return statuses
    if value["interface_version"] != "agents-os.task-completion-eligibility-input.v0.1-r1":
        errors.append(f"{path}: interface_version mismatch")
    for field in (
        "task_id",
        "task_currentness_assessment_fingerprint",
        "candidate_commitment_fingerprint",
        "candidate_currentness_assessment_fingerprint",
        "validation_set_snapshot_id",
        "validation_set_snapshot_fingerprint",
        "dependency_closure_fingerprint",
        "dependency_currentness_assessment_fingerprint",
        "f5_completion_blocking_assessment_fingerprint",
        "completion_guard_currentness_assessment_fingerprint",
        "read_barrier_ref",
        "read_barrier_fingerprint",
        "trusted_time_fingerprint",
        "canonical_fingerprint",
    ):
        check_hash(value[field], f"{path}.{field}", errors)
    for field in (
        "lifecycle_generation",
        "completion_epoch",
        "task_spec_revision",
        "result_revision",
    ):
        check_int(value[field], f"{path}.{field}", errors, positive=True)
    for field in (
        "current_nonterminal_execution_run_count",
        "current_nonterminal_validation_count",
        "active_control_intent_count",
        "unknown_effect_count",
        "completion_blocking_effect_count",
    ):
        check_int(value[field], f"{path}.{field}", errors)
    for field in (
        "task_currentness_assessment_ref",
        "candidate_commitment_ref",
        "candidate_currentness_assessment_ref",
        "dependency_closure_ref",
        "dependency_currentness_assessment_ref",
        "f5_completion_blocking_assessment_ref",
        "completion_guard_currentness_assessment_ref",
        "trusted_time_ref",
    ):
        check_ref(value[field], f"{path}.{field}", errors)
    if value["task_lifecycle"] not in {
        "READY",
        "ACTIVE",
        "WAITING",
        "PAUSED",
        "BLOCKED",
        "VERIFYING",
        "DONE",
        "FAILED",
        "CANCELLED",
    }:
        errors.append(f"{path}: invalid task_lifecycle")
    for field in (
        "task_id",
        "lifecycle_generation",
        "completion_epoch",
        "task_spec_revision",
        "result_revision",
    ):
        if value[field] != current_snapshot.get(field):
            errors.append(f"{path}: current snapshot {field} mismatch")
    if value["validation_set_snapshot_id"] != current_snapshot.get("snapshot_id") or value[
        "validation_set_snapshot_fingerprint"
    ] != current_snapshot.get("canonical_fingerprint"):
        errors.append(f"{path}: current Validation Set mismatch")
    if value["read_barrier_ref"] != barrier.get("barrier_id") or value[
        "read_barrier_fingerprint"
    ] != barrier.get("canonical_fingerprint"):
        errors.append(f"{path}: barrier mismatch")
    if value["trusted_time_ref"] != trusted_time.get("trusted_time_ref") or value[
        "trusted_time_fingerprint"
    ] != trusted_time.get("canonical_fingerprint"):
        errors.append(f"{path}: trusted-time binding mismatch")
    bindings = [
        ("task", "task_currentness_assessment_ref", "task_currentness_assessment_fingerprint", "TASK_CURRENTNESS"),
        ("candidate", "candidate_currentness_assessment_ref", "candidate_currentness_assessment_fingerprint", "CANDIDATE_COMMITMENT_CURRENTNESS"),
        ("dependency", "dependency_currentness_assessment_ref", "dependency_currentness_assessment_fingerprint", "DEPENDENCY_CLOSURE_CURRENTNESS"),
        ("f5", "f5_completion_blocking_assessment_ref", "f5_completion_blocking_assessment_fingerprint", "F5_DELIVERY_CURRENTNESS"),
    ]
    for name, ref_field, fp_field, kind in bindings:
        assessment = assessment_by_ref.get(value[ref_field])
        if assessment is None or assessment.get("canonical_fingerprint") != value[fp_field] or assessment.get(
            "assessment_kind"
        ) != kind:
            errors.append(f"{path}: {name} assessment binding mismatch")
        else:
            statuses[name] = assessment["result"]
    task_assessment = assessment_by_ref.get(value["task_currentness_assessment_ref"])
    task_context_fingerprint = typed_hash(
        "agents-os.f6.task-completion-context.v0.1-r1",
        {
            "task_id": value["task_id"],
            "lifecycle_generation": value["lifecycle_generation"],
            "completion_epoch": value["completion_epoch"],
            "task_spec_revision": value["task_spec_revision"],
            "result_revision": value["result_revision"],
        },
    )
    if task_assessment is not None and task_assessment.get("subject_ref") != value["task_id"]:
        errors.append(f"{path}: task assessment subject mismatch")
    if task_assessment is not None and task_assessment.get(
        "subject_fingerprint"
    ) != task_context_fingerprint:
        errors.append(f"{path}: task assessment context fingerprint mismatch")
    candidate_assessment = assessment_by_ref.get(value["candidate_currentness_assessment_ref"])
    if candidate_assessment is not None and candidate_assessment.get("subject_ref") != value[
        "candidate_commitment_ref"
    ]:
        errors.append(f"{path}: candidate assessment subject mismatch")
    if candidate_assessment is not None and candidate_assessment.get(
        "subject_fingerprint"
    ) != value["candidate_commitment_fingerprint"]:
        errors.append(f"{path}: candidate assessment fingerprint mismatch")
    dependency_assessment = assessment_by_ref.get(value["dependency_currentness_assessment_ref"])
    if dependency_assessment is not None and dependency_assessment.get("subject_ref") != value[
        "dependency_closure_ref"
    ]:
        errors.append(f"{path}: dependency assessment subject mismatch")
    if dependency_assessment is not None and dependency_assessment.get(
        "subject_fingerprint"
    ) != value["dependency_closure_fingerprint"]:
        errors.append(f"{path}: dependency assessment fingerprint mismatch")
    f5_assessment = assessment_by_ref.get(value["f5_completion_blocking_assessment_ref"])
    if f5_assessment is not None and f5_assessment.get("subject_ref") != value["task_id"]:
        errors.append(f"{path}: F5 assessment subject mismatch")
    if f5_assessment is not None and f5_assessment.get(
        "subject_fingerprint"
    ) != task_context_fingerprint:
        errors.append(f"{path}: F5 assessment context fingerprint mismatch")
    completion_guard = assessment_by_ref.get(
        value["completion_guard_currentness_assessment_ref"]
    )
    completion_guard_subject_fingerprint = typed_hash(
        "agents-os.f6.completion-guard-subject.v0.1-r1",
        {
            "task_id": value["task_id"],
            "lifecycle_generation": value["lifecycle_generation"],
            "completion_epoch": value["completion_epoch"],
            "task_spec_revision": value["task_spec_revision"],
            "result_revision": value["result_revision"],
            "current_nonterminal_execution_run_count": value[
                "current_nonterminal_execution_run_count"
            ],
            "current_nonterminal_validation_count": value[
                "current_nonterminal_validation_count"
            ],
            "active_control_intent_count": value["active_control_intent_count"],
            "unknown_effect_count": value["unknown_effect_count"],
            "completion_blocking_effect_count": value[
                "completion_blocking_effect_count"
            ],
        },
    )
    if completion_guard is None or completion_guard.get(
        "canonical_fingerprint"
    ) != value["completion_guard_currentness_assessment_fingerprint"] or completion_guard.get(
        "assessment_kind"
    ) != "COMPLETION_GUARD_CURRENTNESS" or completion_guard.get("result") != "CURRENT":
        errors.append(f"{path}: completion guard assessment binding mismatch")
    elif completion_guard.get("subject_ref") != value["task_id"] or completion_guard.get(
        "subject_fingerprint"
    ) != completion_guard_subject_fingerprint:
        errors.append(f"{path}: completion guard count subject mismatch")
    check_fingerprint(value, "agents-os.f6.task-completion-input.v0.1-r1", path, errors)
    return statuses


def graph_requirement_decisions(
    requirements: list[dict[str, Any]],
    current_snapshot: dict[str, Any],
    current_heads: dict[str, dict[str, Any]],
    waiver_by_id: dict[str, dict[str, Any]],
    trusted_time: dict[str, Any],
) -> list[dict[str, Any]]:
    membership_by_id = {
        member["requirement_id"]: member for member in current_snapshot["memberships"]
    }
    decisions: list[dict[str, Any]] = []
    for requirement in requirements:
        member = membership_by_id[requirement["requirement_id"]]
        head = current_heads.get(requirement["requirement_id"])
        waiver = waiver_by_id.get(member["active_waiver_id"])
        active_waiver = (
            waiver is not None
            and waiver["operation"] == "GRANT"
            and waiver["jenn_decision_result"] == "CURRENT_ACCEPTED"
            and (head is None or head["state"] != "FAILED")
            and (
                waiver["expires_at_utc_ms"] is None
                or trusted_time["as_of_utc_ms"] < waiver["expires_at_utc_ms"]
            )
        )
        if requirement["requiredness"] == "OPTIONAL":
            result, primary = "NOT_REQUIRED", "REQUIREMENT_OPTIONAL"
        elif waiver is not None and waiver["operation"] == "GRANT" and head is not None and head[
            "state"
        ] == "FAILED":
            result, primary = "INDETERMINATE", "WAIVER_INVALID"
        elif active_waiver:
            result, primary = "WAIVED", "REQUIREMENT_WAIVED"
        elif head is None or head["state"] in {"PENDING", "RUNNING", "CANCELLED"}:
            result, primary = "PENDING", "CURRENT_PASS_MISSING"
        elif head["state"] == "FAILED":
            result, primary = "UNSATISFIED", "LATEST_ATTEMPT_FAILED"
        elif head["state"] in {"INCONCLUSIVE", "ERROR"}:
            result, primary = "INDETERMINATE", "EVIDENCE_UNAVAILABLE"
        elif head["state"] == "PASSED" and head["authority_assessment_result"] == "CURRENT_ACCEPTED" and head[
            "evidence_currentness_result"
        ] in {"CURRENT", "TIMELESS"}:
            result, primary = "SATISFIED", "VALIDATION_PASSED"
        else:
            result, primary = "INDETERMINATE", "EVIDENCE_UNAVAILABLE"
        decisions.append(
            {
                "requirement_id": requirement["requirement_id"],
                "result": result,
                "current_attempt_id": head["attempt_id"] if head else None,
                "current_attempt_revision_fingerprint": head["canonical_fingerprint"] if head else None,
                "current_waiver_id": waiver["waiver_id"] if active_waiver else None,
                "current_waiver_event_fingerprint": waiver["canonical_fingerprint"] if active_waiver else None,
                "primary_reason": primary,
                "reason_codes": [primary],
            }
        )
    return sorted(decisions, key=lambda item: item["requirement_id"])


def validate_expected_graph(
    graph: dict[str, Any],
    requirements: list[dict[str, Any]],
    current_snapshot: dict[str, Any],
    current_heads: dict[str, dict[str, Any]],
    waiver_by_id: dict[str, dict[str, Any]],
    trusted_time: dict[str, Any],
    completion_statuses: dict[str, str],
    errors: list[str],
) -> None:
    expected = graph.get("expected_decisions")
    if not exact_fields(
        expected,
        {"requirement_decisions", "validation_set_decision", "completion_decision"},
        "graph.expected_decisions",
        errors,
    ):
        return
    supplied_requirements = expected["requirement_decisions"]
    if not isinstance(supplied_requirements, list):
        errors.append("graph.expected_decisions.requirement_decisions: expected list")
        return
    for index, row in enumerate(supplied_requirements):
        exact_fields(row, EXPECTED_REQUIREMENT_FIELDS, f"graph.expected.requirement[{index}]", errors)
    derived_requirements = graph_requirement_decisions(
        requirements, current_snapshot, current_heads, waiver_by_id, trusted_time
    )
    if supplied_requirements != derived_requirements:
        errors.append("graph.expected_decisions: Requirement decisions are not independently derived")
    required_results = [
        decision["result"]
        for decision, requirement in zip(derived_requirements, sorted(requirements, key=lambda item: item["requirement_id"]))
        if requirement["requiredness"] == "REQUIRED"
    ]
    optional_results = [
        decision["result"]
        for decision, requirement in zip(derived_requirements, sorted(requirements, key=lambda item: item["requirement_id"]))
        if requirement["requiredness"] == "OPTIONAL"
    ]
    nonterminal = sum(
        1 for head in current_heads.values() if head["state"] in {"PENDING", "RUNNING"}
    )
    set_raw = {
        "integrity_status": "VALID",
        "snapshot_currentness": "CURRENT",
        "required_decisions": required_results,
        "optional_decisions": optional_results,
        "nonterminal_attempt_count": nonterminal,
    }
    set_result, set_primary, set_reasons = derive_set_case(set_raw)
    derived_set = {
        "result": set_result,
        "current_required_count": len(required_results),
        "current_unwaived_required_pass_count": sum(
            1 for result in required_results if result == "SATISFIED"
        ),
        "nonterminal_attempt_count": nonterminal,
        "primary_reason": set_primary,
        "reason_codes": set_reasons,
    }
    exact_fields(expected["validation_set_decision"], EXPECTED_SET_FIELDS, "graph.expected.validation_set", errors)
    if expected["validation_set_decision"] != derived_set:
        errors.append("graph.expected_decisions: Validation Set decision is not independently derived")
    completion_input = graph["completion_input"]
    completion_raw = {
        "integrity_status": "VALID",
        "read_barrier_status": "CURRENT",
        "task_currentness": completion_statuses["task"],
        "task_lifecycle": completion_input["task_lifecycle"],
        "candidate_currentness": completion_statuses["candidate"],
        "validation_set_decision": set_result,
        "dependency_currentness": completion_statuses["dependency"],
        "f5_completion_currentness": completion_statuses["f5"],
        "trusted_time_status": trusted_time["result"],
        "nonterminal_execution_run_count": completion_input[
            "current_nonterminal_execution_run_count"
        ],
        "nonterminal_validation_count": completion_input["current_nonterminal_validation_count"],
        "active_control_intent_count": completion_input["active_control_intent_count"],
        "unknown_effect_count": completion_input["unknown_effect_count"],
        "completion_blocking_effect_count": completion_input["completion_blocking_effect_count"],
    }
    comp_result, comp_primary, comp_reasons = derive_completion_case(completion_raw)
    derived_completion = {
        "result": comp_result,
        "completion_assessment_snapshot_may_be_created": comp_result == "ELIGIBLE",
        "task_done_may_be_committed": comp_result == "ELIGIBLE",
        "primary_reason": comp_primary,
        "reason_codes": comp_reasons,
    }
    exact_fields(expected["completion_decision"], EXPECTED_COMPLETION_FIELDS, "graph.expected.completion", errors)
    if expected["completion_decision"] != derived_completion:
        errors.append("graph.expected_decisions: completion decision is not independently derived")


def validate_vectors(value: Any, errors: list[str]) -> None:
    if not exact_fields(
        value,
        {"requirement_cases", "validation_set_cases", "completion_cases"},
        "decision_vectors",
        errors,
    ):
        return
    requirements = value["requirement_cases"]
    sets = value["validation_set_cases"]
    completions = value["completion_cases"]
    if [row.get("case_id") for row in requirements] != REQUIREMENT_CASE_IDS:
        errors.append("decision_vectors.requirement_cases: exact inventory/order mismatch")
    if [row.get("case_id") for row in sets] != SET_CASE_IDS:
        errors.append("decision_vectors.validation_set_cases: exact inventory/order mismatch")
    if [row.get("case_id") for row in completions] != COMPLETION_CASE_IDS:
        errors.append("decision_vectors.completion_cases: exact inventory/order mismatch")
    for index, row in enumerate(requirements):
        path = f"decision_vectors.requirement_cases[{index}]"
        if not exact_fields(row, REQUIREMENT_CASE_FIELDS, path, errors):
            continue
        for field, allowed in {
            "integrity_status": {"VALID", "INVALID"},
            "requiredness": {"REQUIRED", "OPTIONAL"},
            "waivability": {"NON_WAIVABLE", "JENN_WAIVABLE"},
            "waiver_status": {"NONE", "ACTIVE_VALID", "ACTIVE_INVALID"},
            "validation_type": {"DETERMINISTIC", "RUNTIME_OBSERVATION", "INDEPENDENT_REVIEW", "HUMAN_ACCEPTANCE"},
            "latest_attempt_state": {"NONE", "PENDING", "RUNNING", "PASSED", "FAILED", "INCONCLUSIVE", "ERROR", "CANCELLED", "CORRUPT"},
            "attempt_binding_status": {"CURRENT", "STALE", "INDETERMINATE"},
            "authority_result": {"CURRENT_ACCEPTED", "REJECTED", "INDETERMINATE", "NOT_APPLICABLE"},
            "evidence_currentness": {"CURRENT", "TIMELESS", "STALE", "INDETERMINATE", "NOT_APPLICABLE"},
            "validation_method": {"NONE", "FRESH_VALIDATION", "EVIDENCE_CARRY_FORWARD_REVIEW"},
            "carry_forward_status": {"NOT_APPLICABLE", "VALID", "INVALID"},
            "f5_delivery_status": {"NOT_REQUIRED", "APPLIED_CURRENT", "HISTORY_ONLY", "INDETERMINATE"},
        }.items():
            if row[field] not in allowed:
                errors.append(f"{path}.{field}: invalid enum")
        if not isinstance(row["effectful_delivery_binding_required"], bool):
            errors.append(f"{path}.effectful_delivery_binding_required: expected boolean")
        payload = {key: child for key, child in row.items() if key != "case_fingerprint"}
        if row["case_fingerprint"] != typed_hash("agents-os.f6.requirement-case.v0.1-r1", payload):
            errors.append(f"{path}: case fingerprint mismatch")
        derived = derive_requirement_case(row)
        supplied = (
            row["expected_result"],
            row["expected_primary_reason"],
            row["expected_reason_codes"],
        )
        if supplied != derived:
            errors.append(f"{path}: rendered answer differs from independent reducer")
    for index, row in enumerate(sets):
        path = f"decision_vectors.validation_set_cases[{index}]"
        if not exact_fields(row, SET_CASE_FIELDS, path, errors):
            continue
        check_int(row["nonterminal_attempt_count"], f"{path}.nonterminal_attempt_count", errors)
        if row["integrity_status"] not in {"VALID", "INVALID"} or row[
            "snapshot_currentness"
        ] not in {"CURRENT", "STALE", "INDETERMINATE"}:
            errors.append(f"{path}: invalid status enum")
        allowed_decisions = {"SATISFIED", "UNSATISFIED", "WAIVED", "PENDING", "NOT_REQUIRED", "INDETERMINATE"}
        if not isinstance(row["required_decisions"], list) or not all(
            item in allowed_decisions for item in row["required_decisions"]
        ):
            errors.append(f"{path}: invalid required_decisions")
        if not isinstance(row["optional_decisions"], list) or not all(
            item in allowed_decisions for item in row["optional_decisions"]
        ):
            errors.append(f"{path}: invalid optional_decisions")
        payload = {key: child for key, child in row.items() if key != "case_fingerprint"}
        if row["case_fingerprint"] != typed_hash("agents-os.f6.set-case.v0.1-r1", payload):
            errors.append(f"{path}: case fingerprint mismatch")
        derived = derive_set_case(row)
        supplied = (
            row["expected_result"],
            row["expected_primary_reason"],
            row["expected_reason_codes"],
        )
        if supplied != derived:
            errors.append(f"{path}: rendered answer differs from independent reducer")
    for index, row in enumerate(completions):
        path = f"decision_vectors.completion_cases[{index}]"
        if not exact_fields(row, COMPLETION_CASE_FIELDS, path, errors):
            continue
        for field in (
            "nonterminal_execution_run_count",
            "nonterminal_validation_count",
            "active_control_intent_count",
            "unknown_effect_count",
            "completion_blocking_effect_count",
        ):
            check_int(row[field], f"{path}.{field}", errors)
        enum_matrix = {
            "integrity_status": {"VALID", "INVALID"},
            "read_barrier_status": {"CURRENT", "INDETERMINATE", "CHANGED_DURING_REDUCTION"},
            "task_currentness": {"CURRENT", "STALE", "INDETERMINATE"},
            "task_lifecycle": {"READY", "ACTIVE", "WAITING", "PAUSED", "BLOCKED", "VERIFYING", "DONE", "FAILED", "CANCELLED"},
            "candidate_currentness": {"CURRENT", "STALE", "INDETERMINATE"},
            "validation_set_decision": {"SATISFIED", "NOT_SATISFIED", "INDETERMINATE"},
            "dependency_currentness": {"CURRENT_CONFIRMED", "CHALLENGED", "INVALIDATED", "INDETERMINATE"},
            "f5_completion_currentness": {"CLEAR", "BLOCKED", "INDETERMINATE"},
            "trusted_time_status": {"CURRENT", "INDETERMINATE"},
        }
        for field, allowed in enum_matrix.items():
            if row[field] not in allowed:
                errors.append(f"{path}.{field}: invalid enum")
        payload = {key: child for key, child in row.items() if key != "case_fingerprint"}
        if row["case_fingerprint"] != typed_hash("agents-os.f6.completion-case.v0.1-r1", payload):
            errors.append(f"{path}: case fingerprint mismatch")
        derived = derive_completion_case(row)
        supplied = (
            row["expected_result"],
            row["expected_primary_reason"],
            row["expected_reason_codes"],
        )
        if supplied != derived:
            errors.append(f"{path}: rendered answer differs from independent reducer")


def precedence_definitions() -> dict[str, dict[str, Any]]:
    return {
        "REQUIREMENT": {
            "reasons": REQUIREMENT_REASON_PRECEDENCE[:10],
            "indeterminate": set(REQUIREMENT_REASON_PRECEDENCE[:8]),
            "precedence": REQUIREMENT_REASON_PRECEDENCE,
        },
        "VALIDATION_SET": {
            "reasons": SET_REASON_PRECEDENCE[:7],
            "indeterminate": set(SET_REASON_PRECEDENCE[:3]),
            "precedence": SET_REASON_PRECEDENCE,
        },
        "COMPLETION": {
            "reasons": COMPLETION_REASON_PRECEDENCE[:15],
            "indeterminate": set(COMPLETION_REASON_PRECEDENCE[:8]),
            "precedence": COMPLETION_REASON_PRECEDENCE,
        },
    }


def expected_trial_map() -> dict[tuple[str, str, int], tuple[list[str], str, str, list[str]]]:
    expected: dict[tuple[str, str, int], tuple[list[str], str, str, list[str]]] = {}
    for reducer, definition in precedence_definitions().items():
        for index, (first, second) in enumerate(combinations(definition["reasons"], 2), start=1):
            unordered_id = f"{reducer}-PAIR-{index:03d}"
            reasons = [first, second]
            primary = choose_primary(reasons, definition["precedence"])
            if any(reason in definition["indeterminate"] for reason in reasons):
                result = "INDETERMINATE"
            elif reducer == "REQUIREMENT":
                result = "UNSATISFIED" if primary == "LATEST_ATTEMPT_FAILED" else "PENDING"
            elif reducer == "VALIDATION_SET":
                result = "NOT_SATISFIED"
            else:
                result = "NOT_ELIGIBLE"
            expected[(reducer, unordered_id, 1)] = (reasons, result, primary, sorted(reasons))
            expected[(reducer, unordered_id, 2)] = (list(reversed(reasons)), result, primary, sorted(reasons))
    return expected


def validate_precedence_trials(value: Any, errors: list[str]) -> None:
    if not isinstance(value, list):
        errors.append("reason_precedence_trials: expected list")
        return
    expected = expected_trial_map()
    if len(value) != len(expected):
        errors.append("reason_precedence_trials: exact trial count mismatch")
    seen: set[tuple[str, str, int]] = set()
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for index, row in enumerate(value):
        path = f"reason_precedence_trials[{index}]"
        if not exact_fields(row, TRIAL_FIELDS, path, errors):
            continue
        key = (row["reducer"], row["unordered_case_id"], row["ordering"])
        if key in seen:
            errors.append(f"{path}: duplicate trial identity")
        seen.add(key)
        grouped[(row["reducer"], row["unordered_case_id"])].append(row)
        expected_value = expected.get(key)
        supplied = (
            row["raw_conditions"],
            row["expected_result"],
            row["expected_primary_reason"],
            row["expected_reason_codes"],
        )
        if expected_value is None or supplied != expected_value:
            errors.append(f"{path}: trial does not match closed pairwise derivation")
        payload = {key_name: child for key_name, child in row.items() if key_name != "trial_fingerprint"}
        if row["trial_fingerprint"] != typed_hash(
            "agents-os.f6.reason-precedence-trial.v0.1-r1", payload
        ):
            errors.append(f"{path}: trial fingerprint mismatch")
    if seen != set(expected):
        errors.append("reason_precedence_trials: trial inventory mismatch")
    for key, rows in grouped.items():
        if len(rows) != 2:
            errors.append(f"reason_precedence_trials {key}: expected exactly two orderings")
            continue
        rows.sort(key=lambda item: item["ordering"])
        if rows[0]["ordering"] != 1 or rows[1]["ordering"] != 2:
            errors.append(f"reason_precedence_trials {key}: ordering labels mismatch")
        if rows[1]["raw_conditions"] != list(reversed(rows[0]["raw_conditions"])):
            errors.append(f"reason_precedence_trials {key}: second order is not exact reverse")
        for field in ("expected_result", "expected_primary_reason", "expected_reason_codes"):
            if rows[0][field] != rows[1][field]:
                errors.append(f"reason_precedence_trials {key}: order-dependent {field}")


EXPECTED_CANONICALIZATION_PROFILE = {
    "encoding": "UTF-8",
    "unicode": "NFC",
    "object_key_order": "LEXICAL",
    "array_order": "CONTRACT_BUSINESS_KEY",
    "number_profile": "JSON_SAFE_INTEGER_NO_FLOAT_NO_BOOLEAN_ALIAS",
    "digest": "SHA-256_LOWERCASE_HEX",
    "unknown_fields": "REJECT",
}
EXPECTED_AUTHORITY_BINDINGS = {
    "F1_acceptance_decision_sha256": "e49e572055b8e367d38cc70297f5ee144482f4023c62aa46e74de35d999977b2",
    "F3_freeze_decision_sha256": "f692ef1a1af8ac15f40c8af696f486240b73a3ddf391633078e31f17eaf62529",
    "F3_manifest_sha256": "3075cda63fcb2c7937cb800a3bc09cc830d17e2f98b899828db15e09ab9f79ff",
    "F3_independent_review_sha256": "19c14d0a926d76f89a460b8d596c573a49a8fa580739227847ac765b0e52d38b",
    "F5_freeze_decision_sha256": "73270ad50c639be792f252e55befcf93c3dcc3edfffc74cb11c7c0fd212d7dbb",
    "F5_manifest_sha256": "2c867bcab4810f5625caa3cb7a649209e19fc53eab34d6ba16737dcce8d14031",
    "F5_independent_review_sha256": "edcfb8cb4e2d8ff1cabe8a5e1ffaaacf44ed1844eb32444497851f2b5c03f334",
    "F6_start_decision_sha256": "335c838830fce9d6f48dedfcdd5bd07c2be5eacba1a3ec61962305fccae6f30f",
}


def validate_fixture(data: Any) -> list[str]:
    errors: list[str] = []
    check_scalar_tree(data, "root", errors)
    if not exact_fields(data, ROOT_FIELDS, "root", errors):
        return errors
    if data["schema_version"] != "agents-os.f6-r1-synthetic-validation-current-decision.v0.1":
        errors.append("root: schema_version mismatch")
    if data["environment"] != "SYNTHETIC_TEST":
        errors.append("root: production or unknown environment forbidden")
    for field in (
        "authority_eligible",
        "runtime_consumable",
        "recovery_importable",
        "contains_real_task_run_validation_or_effect",
    ):
        if data[field] is not False:
            errors.append(f"root.{field}: must be false")
    if data["canonicalization_profile"] != EXPECTED_CANONICALIZATION_PROFILE:
        errors.append("root: canonicalization profile mismatch")
    if data["authority_bindings"] != EXPECTED_AUTHORITY_BINDINGS:
        errors.append("root: authority bindings mismatch")
    if data["prospective_owner_interfaces"] != {
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
    }:
        errors.append("root: prospective owner interface boundary mismatch")
    graph = data["graph_witness"]
    if not exact_fields(graph, GRAPH_FIELDS, "graph", errors):
        return errors
    barrier = graph["read_barrier"]
    validate_read_barrier(barrier, "graph.read_barrier", errors)
    trusted_time = graph["trusted_time"]
    validate_trusted_time(trusted_time, barrier, "graph.trusted_time", errors)
    assessments = graph["upstream_assessments"]
    if not isinstance(assessments, list):
        errors.append("graph.upstream_assessments: expected list")
        assessments = []
    if [row.get("assessment_ref") for row in assessments] != sorted(
        row.get("assessment_ref") for row in assessments
    ) or len({row.get("assessment_ref") for row in assessments}) != len(assessments):
        errors.append("graph.upstream_assessments: ordering/uniqueness failure")
    for index, row in enumerate(assessments):
        validate_assessment(row, barrier, f"graph.upstream_assessments[{index}]", errors)
    assessment_by_ref = {
        row.get("assessment_ref"): row for row in assessments if isinstance(row, dict)
    }
    requirements = graph["requirements"]
    if not isinstance(requirements, list):
        errors.append("graph.requirements: expected list")
        requirements = []
    for index, row in enumerate(requirements):
        validate_requirement(row, f"graph.requirements[{index}]", errors)
        if row.get("created_event_sequence", SAFE_MAX + 1) > barrier.get(
            "end_event_sequence", -1
        ):
            errors.append(f"graph.requirements[{index}]: created after read barrier")
    requirement_ids = [row.get("requirement_id") for row in requirements]
    if requirement_ids != sorted(requirement_ids) or len(requirement_ids) != len(set(requirement_ids)):
        errors.append("graph.requirements: ordering/uniqueness failure")
    requirement_by_id = {
        row.get("requirement_id"): row for row in requirements if isinstance(row, dict)
    }
    validation_sets = graph["validation_sets"]
    if not isinstance(validation_sets, list):
        errors.append("graph.validation_sets: expected list")
        validation_sets = []
    snapshot_by_id = {
        row.get("snapshot_id"): row for row in validation_sets if isinstance(row, dict)
    }
    waiver_events = graph["waiver_events"]
    if not isinstance(waiver_events, list):
        errors.append("graph.waiver_events: expected list")
        waiver_events = []
    for index, row in enumerate(waiver_events):
        validate_waiver(
            row,
            requirement_by_id,
            snapshot_by_id,
            f"graph.waiver_events[{index}]",
            errors,
        )
        if row.get("event_sequence", SAFE_MAX + 1) > barrier.get(
            "end_event_sequence", -1
        ):
            errors.append(f"graph.waiver_events[{index}]: committed after read barrier")
    waiver_by_id = validate_waiver_chains(waiver_events, errors)
    for index, row in enumerate(validation_sets):
        validate_validation_set(
            row,
            requirement_by_id,
            waiver_by_id,
            f"graph.validation_sets[{index}]",
            errors,
        )
        if row.get("frozen_event_sequence", SAFE_MAX + 1) > barrier.get(
            "end_event_sequence", -1
        ):
            errors.append(f"graph.validation_sets[{index}]: frozen after read barrier")
    revisions = [row.get("validation_set_revision") for row in validation_sets]
    if revisions != list(range(1, len(validation_sets) + 1)):
        errors.append("graph.validation_sets: revision inventory/order mismatch")
    for index, row in enumerate(validation_sets):
        if index > 0 and row.get("base_snapshot_id") != validation_sets[index - 1].get("snapshot_id"):
            errors.append(f"graph.validation_sets[{index}]: base snapshot mismatch")
        if index > 0 and row.get("frozen_event_sequence", -1) <= validation_sets[
            index - 1
        ].get("frozen_event_sequence", SAFE_MAX):
            errors.append(f"graph.validation_sets[{index}]: freeze Event did not advance")
    current_snapshot = snapshot_by_id.get(graph["current_validation_set_id"])
    if current_snapshot is None or (validation_sets and current_snapshot is not validation_sets[-1]):
        errors.append("graph: current_validation_set_id is not exact latest snapshot")
        current_snapshot = validation_sets[-1] if validation_sets else {}
    attempts = graph["attempt_revisions"]
    if not isinstance(attempts, list):
        errors.append("graph.attempt_revisions: expected list")
        attempts = []
    for index, row in enumerate(attempts):
        validate_attempt(
            row,
            requirement_by_id,
            snapshot_by_id,
            assessment_by_ref,
            trusted_time,
            f"graph.attempt_revisions[{index}]",
            errors,
        )
        if row.get("committed_event_sequence", SAFE_MAX + 1) > barrier.get(
            "end_event_sequence", -1
        ):
            errors.append(f"graph.attempt_revisions[{index}]: committed after read barrier")
    current_heads = validate_attempt_chains(
        attempts, requirement_by_id, current_snapshot, errors
    )
    validate_carry_forward_links(attempts, requirement_by_id, errors)
    completion_statuses = validate_completion_input(
        graph["completion_input"],
        current_snapshot,
        barrier,
        trusted_time,
        assessment_by_ref,
        "graph.completion_input",
        errors,
    )
    validate_expected_graph(
        graph,
        requirements,
        current_snapshot,
        current_heads,
        waiver_by_id,
        trusted_time,
        completion_statuses,
        errors,
    )
    supplied_graph_fp = graph["graph_fingerprint"]
    graph_payload = {key: child for key, child in graph.items() if key != "graph_fingerprint"}
    if supplied_graph_fp != typed_hash("agents-os.f6.graph-witness.v0.1-r1", graph_payload):
        errors.append("graph: graph_fingerprint mismatch")
    validate_vectors(data["decision_vectors"], errors)
    validate_precedence_trials(data["reason_precedence_trials"], errors)
    if data["mutation_expectations"] != MUTATION_EXPECTATIONS:
        errors.append("root: mutation expectation inventory mismatch")
    summary = data["summary"]
    expected_summary = {
        "normative_schema_count": 10,
        "requirement_case_count": 22,
        "validation_set_case_count": 10,
        "completion_case_count": 22,
        "decision_vector_count": 54,
        "precedence_raw_trial_count": len(expected_trial_map()),
        "negative_mutation_count": 32,
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
    }
    if summary != expected_summary:
        errors.append("root: summary mismatch")
    supplied_root = data["root_fingerprint"]
    root_payload = {key: child for key, child in data.items() if key != "root_fingerprint"}
    if supplied_root != typed_hash("agents-os.f6.fixture-root.v0.1-r1", root_payload):
        errors.append("root: root_fingerprint mismatch")
    return errors


def resign_case(row: dict[str, Any], domain: str) -> None:
    row["case_fingerprint"] = typed_hash(
        domain, {key: child for key, child in row.items() if key != "case_fingerprint"}
    )


def resign_root(data: dict[str, Any]) -> None:
    data["root_fingerprint"] = typed_hash(
        "agents-os.f6.fixture-root.v0.1-r1",
        {key: child for key, child in data.items() if key != "root_fingerprint"},
    )


def resign_graph(
    data: dict[str, Any],
    *,
    recompute_snapshot_ids: bool = True,
    recompute_attempt_ids: bool = True,
) -> None:
    graph = data["graph_witness"]
    barrier = graph["read_barrier"]
    barrier["canonical_fingerprint"] = typed_hash(
        "agents-os.f6.read-barrier.v0.1-r1",
        {key: child for key, child in barrier.items() if key != "canonical_fingerprint"},
    )
    trusted = graph["trusted_time"]
    trusted["read_barrier_fingerprint"] = barrier["canonical_fingerprint"]
    trusted["canonical_fingerprint"] = typed_hash(
        "agents-os.f6.trusted-time.v0.1-r1",
        {key: child for key, child in trusted.items() if key != "canonical_fingerprint"},
    )
    for assessment in graph["upstream_assessments"]:
        assessment["read_barrier_fingerprint"] = barrier["canonical_fingerprint"]
        assessment["canonical_fingerprint"] = typed_hash(
            "agents-os.f6.upstream-assessment.v0.1-r1",
            {key: child for key, child in assessment.items() if key != "canonical_fingerprint"},
        )
    requirement_by_id: dict[str, dict[str, Any]] = {}
    for requirement in graph["requirements"]:
        requirement["provenance_set_fingerprint"] = typed_hash(
            "agents-os.f6.requirement-provenance-set.v0.1-r1",
            requirement["provenance_bindings"],
        )
        requirement["canonical_fingerprint"] = typed_hash(
            "agents-os.f6.requirement.v0.1-r1",
            {key: child for key, child in requirement.items() if key != "canonical_fingerprint"},
        )
        requirement_by_id[requirement["requirement_id"]] = requirement
    snapshot_old_to_new: dict[str, str] = {}
    snapshot_by_id: dict[str, dict[str, Any]] = {}
    waiver_old_to_new: dict[str, str] = {}
    waiver_by_id: dict[str, dict[str, Any]] = {}

    def resign_waivers() -> None:
        for waiver in graph["waiver_events"]:
            old_waiver_id = waiver["waiver_id"]
            if waiver["base_snapshot_id"] in snapshot_old_to_new:
                waiver["base_snapshot_id"] = snapshot_old_to_new[waiver["base_snapshot_id"]]
            identity = {
                "task_id": waiver["task_id"],
                "requirement_id": waiver["requirement_id"],
                "requirement_revision": waiver["requirement_revision"],
                "lifecycle_generation": waiver["lifecycle_generation"],
                "completion_epoch": waiver["completion_epoch"],
                "task_spec_revision": waiver["task_spec_revision"],
                "result_revision": waiver["result_revision"],
            }
            waiver["waiver_id"] = typed_hash("agents-os.f6.waiver-id.v0.1-r1", identity)
            waiver["waiver_event_id"] = typed_hash(
                "agents-os.f6.waiver-event-id.v0.1-r1",
                {
                    "waiver_id": waiver["waiver_id"],
                    "waiver_event_index": waiver["waiver_event_index"],
                    "operation": waiver["operation"],
                },
            )
            waiver["canonical_fingerprint"] = typed_hash(
                "agents-os.f6.waiver-event.v0.1-r1",
                {key: child for key, child in waiver.items() if key != "canonical_fingerprint"},
            )
            waiver_old_to_new[old_waiver_id] = waiver["waiver_id"]
            waiver_by_id[waiver["waiver_id"]] = waiver

    for snapshot_index, snapshot in enumerate(graph["validation_sets"]):
        if snapshot_index == 1:
            resign_waivers()
        old_id = snapshot["snapshot_id"]
        if snapshot["base_snapshot_id"] in snapshot_old_to_new:
            snapshot["base_snapshot_id"] = snapshot_old_to_new[snapshot["base_snapshot_id"]]
        for member in snapshot["memberships"]:
            requirement = requirement_by_id.get(member["requirement_id"])
            if requirement is not None:
                member["requirement_fingerprint"] = requirement["canonical_fingerprint"]
            if member["active_waiver_id"] in waiver_old_to_new:
                member["active_waiver_id"] = waiver_old_to_new[member["active_waiver_id"]]
            waiver = waiver_by_id.get(member["active_waiver_id"])
            if waiver is not None:
                member["active_waiver_event_fingerprint"] = waiver["canonical_fingerprint"]
        snapshot["membership_set_fingerprint"] = typed_hash(
            "agents-os.f6.validation-membership-set.v0.1-r1", snapshot["memberships"]
        )
        snapshot["source_set_fingerprint"] = typed_hash(
            "agents-os.f6.validation-source-set.v0.1-r1", snapshot["source_bindings"]
        )
        if recompute_snapshot_ids:
            identity = {
                "task_id": snapshot["task_id"],
                "lifecycle_generation": snapshot["lifecycle_generation"],
                "completion_epoch": snapshot["completion_epoch"],
                "task_spec_revision": snapshot["task_spec_revision"],
                "result_revision": snapshot["result_revision"],
                "validation_set_revision": snapshot["validation_set_revision"],
                "base_snapshot_id": snapshot["base_snapshot_id"],
                "freeze_trigger": snapshot["freeze_trigger"],
                "membership_set_fingerprint": snapshot["membership_set_fingerprint"],
                "source_set_fingerprint": snapshot["source_set_fingerprint"],
            }
            snapshot["snapshot_id"] = typed_hash(
                "agents-os.f6.validation-set-id.v0.1-r1", identity
            )
        snapshot["canonical_fingerprint"] = typed_hash(
            "agents-os.f6.validation-set.v0.1-r1",
            {key: child for key, child in snapshot.items() if key != "canonical_fingerprint"},
        )
        snapshot_old_to_new[old_id] = snapshot["snapshot_id"]
        snapshot_by_id[snapshot["snapshot_id"]] = snapshot
    if graph["waiver_events"] and not waiver_by_id:
        resign_waivers()
    if graph["current_validation_set_id"] in snapshot_old_to_new:
        graph["current_validation_set_id"] = snapshot_old_to_new[graph["current_validation_set_id"]]
    assessment_by_ref = {row["assessment_ref"]: row for row in graph["upstream_assessments"]}
    attempt_groups: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for attempt in graph["attempt_revisions"]:
        if attempt["validation_set_snapshot_id"] in snapshot_old_to_new:
            attempt["validation_set_snapshot_id"] = snapshot_old_to_new[
                attempt["validation_set_snapshot_id"]
            ]
        snapshot = snapshot_by_id.get(attempt["validation_set_snapshot_id"])
        if snapshot is not None:
            attempt["validation_set_snapshot_fingerprint"] = snapshot["canonical_fingerprint"]
        requirement = requirement_by_id.get(attempt["requirement_id"])
        if requirement is not None:
            attempt["requirement_fingerprint"] = requirement["canonical_fingerprint"]
        authority = assessment_by_ref.get(attempt["authority_assessment_ref"])
        if authority is not None:
            attempt["authority_assessment_fingerprint"] = authority["canonical_fingerprint"]
        evidence = assessment_by_ref.get(attempt["evidence_currentness_ref"])
        if evidence is not None:
            attempt["evidence_currentness_fingerprint"] = evidence["canonical_fingerprint"]
        if recompute_attempt_ids:
            identity = {
                "task_id": attempt["task_id"],
                "requirement_id": attempt["requirement_id"],
                "requirement_revision": attempt["requirement_revision"],
                "lifecycle_generation": attempt["lifecycle_generation"],
                "completion_epoch": attempt["completion_epoch"],
                "task_spec_revision": attempt["task_spec_revision"],
                "result_revision": attempt["result_revision"],
                "attempt_number": attempt["attempt_number"],
            }
            attempt["attempt_id"] = typed_hash(
                "agents-os.f6.validation-attempt-id.v0.1-r1", identity
            )
        attempt_groups[(attempt["attempt_id"], attempt["attempt_number"])].append(attempt)
    for rows in attempt_groups.values():
        rows.sort(key=lambda item: item["attempt_revision"])
        prior: str | None = None
        for row in rows:
            row["prior_attempt_revision_fingerprint"] = prior
            row["canonical_fingerprint"] = typed_hash(
                "agents-os.f6.validation-attempt.v0.1-r1",
                {key: child for key, child in row.items() if key != "canonical_fingerprint"},
            )
            prior = row["canonical_fingerprint"]
    graph["attempt_revisions"].sort(
        key=lambda item: (item["requirement_id"], item["attempt_number"], item["attempt_revision"])
    )
    current_snapshot = snapshot_by_id[graph["current_validation_set_id"]]
    completion = graph["completion_input"]
    completion["validation_set_snapshot_id"] = current_snapshot["snapshot_id"]
    completion["validation_set_snapshot_fingerprint"] = current_snapshot["canonical_fingerprint"]
    completion["read_barrier_fingerprint"] = barrier["canonical_fingerprint"]
    completion["trusted_time_fingerprint"] = trusted["canonical_fingerprint"]
    for ref_field, fp_field in (
        ("task_currentness_assessment_ref", "task_currentness_assessment_fingerprint"),
        ("candidate_currentness_assessment_ref", "candidate_currentness_assessment_fingerprint"),
        ("dependency_currentness_assessment_ref", "dependency_currentness_assessment_fingerprint"),
        ("f5_completion_blocking_assessment_ref", "f5_completion_blocking_assessment_fingerprint"),
        ("completion_guard_currentness_assessment_ref", "completion_guard_currentness_assessment_fingerprint"),
    ):
        assessment = assessment_by_ref.get(completion[ref_field])
        if assessment is not None:
            completion[fp_field] = assessment["canonical_fingerprint"]
    completion["canonical_fingerprint"] = typed_hash(
        "agents-os.f6.task-completion-input.v0.1-r1",
        {key: child for key, child in completion.items() if key != "canonical_fingerprint"},
    )
    heads: dict[str, dict[str, Any]] = {}
    for attempt in graph["attempt_revisions"]:
        current = heads.get(attempt["requirement_id"])
        if current is None or (attempt["attempt_number"], attempt["attempt_revision"]) > (
            current["attempt_number"],
            current["attempt_revision"],
        ):
            heads[attempt["requirement_id"]] = attempt
    for expected in graph["expected_decisions"]["requirement_decisions"]:
        head = heads.get(expected["requirement_id"])
        if head is not None:
            expected["current_attempt_id"] = head["attempt_id"]
            expected["current_attempt_revision_fingerprint"] = head["canonical_fingerprint"]
        member = next(
            (
                row
                for row in current_snapshot["memberships"]
                if row["requirement_id"] == expected["requirement_id"]
            ),
            None,
        )
        if member and member["active_waiver_id"]:
            expected["current_waiver_id"] = member["active_waiver_id"]
            expected["current_waiver_event_fingerprint"] = member[
                "active_waiver_event_fingerprint"
            ]
    graph["graph_fingerprint"] = typed_hash(
        "agents-os.f6.graph-witness.v0.1-r1",
        {key: child for key, child in graph.items() if key != "graph_fingerprint"},
    )
    resign_root(data)


def mutation_cases(base: dict[str, Any]) -> dict[str, Callable[[dict[str, Any]], None]]:
    def vector_case(data: dict[str, Any], section: str, case_id: str) -> dict[str, Any]:
        return next(
            row for row in data["decision_vectors"][section] if row["case_id"] == case_id
        )

    def update_requirement_id_graphwide(data: dict[str, Any]) -> None:
        graph = data["graph_witness"]
        requirement = graph["requirements"][0]
        old_id = requirement["requirement_id"]
        new_id = "f" * 64 if old_id != "f" * 64 else "e" * 64
        requirement["requirement_id"] = new_id
        for snapshot in graph["validation_sets"]:
            for member in snapshot["memberships"]:
                if member["requirement_id"] == old_id:
                    member["requirement_id"] = new_id
        for attempt in graph["attempt_revisions"]:
            if attempt["requirement_id"] == old_id:
                attempt["requirement_id"] = new_id
        for waiver in graph["waiver_events"]:
            if waiver["requirement_id"] == old_id:
                waiver["requirement_id"] = new_id
        for expected in graph["expected_decisions"]["requirement_decisions"]:
            if expected["requirement_id"] == old_id:
                expected["requirement_id"] = new_id
        graph["requirements"].sort(key=lambda item: item["requirement_id"])
        graph["expected_decisions"]["requirement_decisions"].sort(
            key=lambda item: item["requirement_id"]
        )
        resign_graph(data)

    def update_snapshot_id_graphwide(data: dict[str, Any]) -> None:
        graph = data["graph_witness"]
        snapshot = graph["validation_sets"][-1]
        old_id = snapshot["snapshot_id"]
        snapshot["snapshot_id"] = "f" * 64 if old_id != "f" * 64 else "e" * 64
        graph["current_validation_set_id"] = snapshot["snapshot_id"]
        for attempt in graph["attempt_revisions"]:
            if attempt["validation_set_snapshot_id"] == old_id:
                attempt["validation_set_snapshot_id"] = snapshot["snapshot_id"]
        graph["completion_input"]["validation_set_snapshot_id"] = snapshot["snapshot_id"]
        resign_graph(data, recompute_snapshot_ids=False)

    def update_attempt_id_graphwide(data: dict[str, Any]) -> None:
        graph = data["graph_witness"]
        old_id = graph["attempt_revisions"][0]["attempt_id"]
        new_id = "f" * 64 if old_id != "f" * 64 else "e" * 64
        for attempt in graph["attempt_revisions"]:
            if attempt["attempt_id"] == old_id:
                attempt["attempt_id"] = new_id
        for expected in graph["expected_decisions"]["requirement_decisions"]:
            if expected["current_attempt_id"] == old_id:
                expected["current_attempt_id"] = new_id
        resign_graph(data, recompute_attempt_ids=False)

    def branch_attempt(data: dict[str, Any]) -> None:
        graph = data["graph_witness"]
        source = copy.deepcopy(graph["attempt_revisions"][2])
        source["state"] = "FAILED"
        source["committed_event_ref"] = "synth:f6:event:branch"
        source["committed_event_sequence"] += 1
        source["canonical_fingerprint"] = typed_hash(
            "agents-os.f6.validation-attempt.v0.1-r1",
            {key: child for key, child in source.items() if key != "canonical_fingerprint"},
        )
        graph["attempt_revisions"].append(source)
        graph["attempt_revisions"].sort(
            key=lambda item: (item["requirement_id"], item["attempt_number"], item["attempt_revision"])
        )
        graph["graph_fingerprint"] = typed_hash(
            "agents-os.f6.graph-witness.v0.1-r1",
            {key: child for key, child in graph.items() if key != "graph_fingerprint"},
        )
        resign_root(data)

    cases: dict[str, Callable[[dict[str, Any]], None]] = {}
    cases["unknown_root_field"] = lambda data: (
        data.__setitem__("unknown", "x"), resign_root(data)
    )
    cases["unknown_graph_field"] = lambda data: (
        data["graph_witness"].__setitem__("unknown", "x"),
        data["graph_witness"].__setitem__(
            "graph_fingerprint",
            typed_hash(
                "agents-os.f6.graph-witness.v0.1-r1",
                {
                    key: child
                    for key, child in data["graph_witness"].items()
                    if key != "graph_fingerprint"
                },
            ),
        ),
        resign_root(data),
    )

    def unknown_requirement(data: dict[str, Any]) -> None:
        data["graph_witness"]["requirements"][0]["unknown"] = "x"
        resign_graph(data)

    cases["unknown_requirement_field"] = unknown_requirement

    def mutate_completion_count(data: dict[str, Any], value: Any) -> None:
        row = vector_case(data, "completion_cases", "COMP-01-ELIGIBLE")
        row["nonterminal_execution_run_count"] = value
        resign_case(row, "agents-os.f6.completion-case.v0.1-r1")
        resign_root(data)

    cases["float_where_count_required"] = lambda data: mutate_completion_count(data, 0.5)
    cases["boolean_where_count_required"] = lambda data: mutate_completion_count(data, True)
    cases["unsafe_integer"] = lambda data: mutate_completion_count(data, SAFE_MAX + 1)

    def non_nfc(data: dict[str, Any]) -> None:
        row = vector_case(data, "requirement_cases", "REQ-01-FRESH-PASS-CURRENT")
        row["case_id"] = "REQ-e\u0301"
        resign_case(row, "agents-os.f6.requirement-case.v0.1-r1")
        resign_root(data)

    cases["non_nfc_string"] = non_nfc

    def uppercase_hash(data: dict[str, Any]) -> None:
        data["graph_witness"]["requirements"][0]["semantic_digest"] = data[
            "graph_witness"
        ]["requirements"][0]["semantic_digest"].upper()
        resign_graph(data)

    cases["uppercase_hash"] = uppercase_hash

    def missing_vector(data: dict[str, Any]) -> None:
        data["decision_vectors"]["requirement_cases"].pop()
        resign_root(data)

    cases["missing_requirement_vector"] = missing_vector

    def extra_vector(data: dict[str, Any]) -> None:
        row = copy.deepcopy(data["decision_vectors"]["requirement_cases"][-1])
        row["case_id"] = "REQ-23-EXTRA"
        resign_case(row, "agents-os.f6.requirement-case.v0.1-r1")
        data["decision_vectors"]["requirement_cases"].append(row)
        resign_root(data)

    cases["extra_requirement_vector"] = extra_vector

    def duplicate_membership(data: dict[str, Any]) -> None:
        snapshot = data["graph_witness"]["validation_sets"][-1]
        snapshot["memberships"].append(copy.deepcopy(snapshot["memberships"][0]))
        resign_graph(data)

    cases["duplicate_requirement_membership"] = duplicate_membership

    def unsorted_membership(data: dict[str, Any]) -> None:
        snapshot = data["graph_witness"]["validation_sets"][-1]
        snapshot["memberships"][0], snapshot["memberships"][1] = (
            snapshot["memberships"][1],
            snapshot["memberships"][0],
        )
        resign_graph(data)

    cases["unsorted_requirement_membership"] = unsorted_membership
    cases["requirement_id_formula_graphwide_resigned"] = update_requirement_id_graphwide
    cases["snapshot_id_formula_graphwide_resigned"] = update_snapshot_id_graphwide
    cases["attempt_id_formula_graphwide_resigned"] = update_attempt_id_graphwide
    cases["attempt_chain_branch_resigned"] = branch_attempt

    def invalid_transition(data: dict[str, Any]) -> None:
        data["graph_witness"]["attempt_revisions"][1]["state"] = "PENDING"
        resign_graph(data)

    cases["attempt_invalid_transition_resigned"] = invalid_transition

    def attempt_gap(data: dict[str, Any]) -> None:
        first_id = data["graph_witness"]["attempt_revisions"][0]["attempt_id"]
        for row in data["graph_witness"]["attempt_revisions"]:
            if row["attempt_id"] == first_id:
                row["attempt_number"] = 2
        resign_graph(data)

    cases["attempt_number_gap_resigned"] = attempt_gap

    semantic_vectors = {
        "stale_evidence_labeled_satisfied_resigned": (
            "requirement_cases",
            "REQ-01-FRESH-PASS-CURRENT",
            "evidence_currentness",
            "STALE",
            "agents-os.f6.requirement-case.v0.1-r1",
        ),
        "carry_forward_invalid_labeled_satisfied_resigned": (
            "requirement_cases",
            "REQ-15-CARRY-FORWARD-VALID",
            "carry_forward_status",
            "INVALID",
            "agents-os.f6.requirement-case.v0.1-r1",
        ),
        "f5_history_labeled_satisfied_resigned": (
            "requirement_cases",
            "REQ-20-EFFECTFUL-F5-CURRENT",
            "f5_delivery_status",
            "HISTORY_ONLY",
            "agents-os.f6.requirement-case.v0.1-r1",
        ),
        "nonwaivable_waiver_resigned": (
            "requirement_cases",
            "REQ-17-WAIVER-ACTIVE",
            "waivability",
            "NON_WAIVABLE",
            "agents-os.f6.requirement-case.v0.1-r1",
        ),
        "all_waived_set_labeled_satisfied_resigned": (
            "validation_set_cases",
            "SET-01-ALL-PASSED",
            "required_decisions",
            ["WAIVED", "WAIVED"],
            "agents-os.f6.set-case.v0.1-r1",
        ),
        "empty_set_labeled_satisfied_resigned": (
            "validation_set_cases",
            "SET-01-ALL-PASSED",
            "required_decisions",
            [],
            "agents-os.f6.set-case.v0.1-r1",
        ),
        "active_task_labeled_eligible_resigned": (
            "completion_cases",
            "COMP-01-ELIGIBLE",
            "task_lifecycle",
            "ACTIVE",
            "agents-os.f6.completion-case.v0.1-r1",
        ),
        "nonterminal_run_labeled_eligible_resigned": (
            "completion_cases",
            "COMP-01-ELIGIBLE",
            "nonterminal_execution_run_count",
            1,
            "agents-os.f6.completion-case.v0.1-r1",
        ),
        "unknown_effect_labeled_eligible_resigned": (
            "completion_cases",
            "COMP-01-ELIGIBLE",
            "unknown_effect_count",
            1,
            "agents-os.f6.completion-case.v0.1-r1",
        ),
    }
    for name, (section, case_id, field, value, domain) in semantic_vectors.items():
        def mutate(data: dict[str, Any], s: str = section, c: str = case_id, f: str = field, v: Any = value, d: str = domain) -> None:
            row = vector_case(data, s, c)
            row[f] = copy.deepcopy(v)
            resign_case(row, d)
            resign_root(data)
        cases[name] = mutate

    def human_carry_forward(data: dict[str, Any]) -> None:
        row = vector_case(data, "requirement_cases", "REQ-01-FRESH-PASS-CURRENT")
        row["validation_type"] = "HUMAN_ACCEPTANCE"
        row["validation_method"] = "EVIDENCE_CARRY_FORWARD_REVIEW"
        row["carry_forward_status"] = "VALID"
        resign_case(row, "agents-os.f6.requirement-case.v0.1-r1")
        resign_root(data)

    cases["human_carry_forward_labeled_satisfied_resigned"] = human_carry_forward

    def completion_guard_count_changed(data: dict[str, Any]) -> None:
        data["graph_witness"]["completion_input"][
            "current_nonterminal_execution_run_count"
        ] = 1
        resign_graph(data)

    cases["completion_guard_count_changed_resigned"] = completion_guard_count_changed

    def prospective_owner_interface_promoted(data: dict[str, Any]) -> None:
        data["prospective_owner_interfaces"]["F5_completion_blocking_assessment"][
            "status"
        ] = "ACCEPTED"
        resign_root(data)

    cases["prospective_owner_interface_promoted_resigned"] = (
        prospective_owner_interface_promoted
    )

    cases["synthetic_environment_changed_to_production_resigned"] = lambda data: (
        data.__setitem__("environment", "PRODUCTION"), resign_root(data)
    )
    cases["synthetic_runtime_consumable_enabled_resigned"] = lambda data: (
        data.__setitem__("runtime_consumable", True), resign_root(data)
    )
    if set(cases) != set(MUTATION_EXPECTATIONS):
        return cases
    return {name: cases[name] for name in MUTATION_EXPECTATIONS}


def run_mutations(base: dict[str, Any]) -> tuple[int, list[str]]:
    failures: list[str] = []
    cases = mutation_cases(base)
    if list(cases) != MUTATION_EXPECTATIONS:
        return 0, ["validator mutation implementation inventory mismatch"]
    rejected = 0
    for name, mutate in cases.items():
        candidate = copy.deepcopy(base)
        try:
            mutate(candidate)
            errors = validate_fixture(candidate)
        except Exception as exc:
            failures.append(
                f"mutation execution error: {name}: {type(exc).__name__}: {exc}"
            )
            continue
        if errors:
            rejected += 1
        else:
            failures.append(f"mutation incorrectly accepted: {name}")
    return rejected, failures


def main() -> int:
    try:
        data = load_fixture(FIXTURE_PATH)
    except Exception as exc:
        print(f"result: BLOCK\nerror: fixture load failed: {exc}")
        return 1
    errors = validate_fixture(data)
    rejected, mutation_failures = run_mutations(data)
    errors.extend(mutation_failures)
    if errors:
        print("result: BLOCK")
        print(f"error_count: {len(errors)}")
        for error in errors[:80]:
            print(f"- {error}")
        return 1
    summary = data["summary"]
    print("result: PASS_NO_BLOCKER")
    print(f"normative_schema_count: {summary['normative_schema_count']}")
    print(f"decision_vector_count: {summary['decision_vector_count']}")
    print(f"requirement_case_count: {summary['requirement_case_count']}")
    print(f"validation_set_case_count: {summary['validation_set_case_count']}")
    print(f"completion_case_count: {summary['completion_case_count']}")
    print(f"precedence_raw_trial_count: {summary['precedence_raw_trial_count']}")
    print(f"negative_mutations_rejected: {rejected}")
    print(f"graph_requirement_count: {summary['graph_requirement_count']}")
    print(f"graph_validation_set_count: {summary['graph_validation_set_count']}")
    print(f"graph_attempt_revision_count: {summary['graph_attempt_revision_count']}")
    print(f"graph_waiver_event_count: {summary['graph_waiver_event_count']}")
    print(f"fixture_canonical_sha256: {data['root_fingerprint']}")
    print(f"derived_eligible_case_count: {summary['derived_eligible_case_count']}")
    print(f"task_done_mutation_count: {summary['task_done_mutation_count']}")
    print(f"accepted_real_task_count: {summary['accepted_real_task_count']}")
    print(f"runtime_consumable_count: {summary['runtime_consumable_count']}")
    print(f"external_effect_count: {summary['external_effect_count']}")
    print(f"provider_call_count: {summary['provider_call_count']}")
    print(f"raw_secret_count: {summary['raw_secret_count']}")
    print(f"terminal_outcome: {summary['terminal_outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
