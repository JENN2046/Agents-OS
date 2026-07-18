#!/usr/bin/env python3
"""Offline semantic validator for the synthetic F6 R3 closure witness."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = WORKSPACE_ROOT / "control-plane/registry/examples/2026-07-18-agents-os-f6-r3-eight-finding-semantic-closure-v0.1.json"
R2_VALIDATOR_PATH = WORKSPACE_ROOT / "control-plane/registry/validate-f6-r2-ten-finding-proof-closure.py"
SAFE_MAX = 2**53 - 1
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._/-]*$")

R2_PATHS = {
    "amendment": "control-plane/registry/drafts/2026-07-17-agents-os-f6-validation-requirement-current-decision-v0.1-r2-amendment.draft.md",
    "builder": "control-plane/registry/build-f6-r2-ten-finding-proof-closure.py",
    "fixture": "control-plane/registry/examples/2026-07-17-agents-os-f6-r2-ten-finding-proof-closure-v0.1.json",
    "validator": "control-plane/registry/validate-f6-r2-ten-finding-proof-closure.py",
    "manifest": "control-plane/registry/reports/2026-07-17-agents-os-f6-r2-atomic-independent-review-package-v0.1.manifest.yaml",
    "independent_review": "control-plane/registry/reviews/2026-07-17-yellow-agents-os-f6-r2-full-atomic-independent-review.yaml",
    "disposition": "control-plane/registry/reviews/2026-07-18-agents-os-f6-r2-independent-review-disposition-v0.1.yaml",
    "r3_start_decision": "control-plane/registry/decisions/2026-07-18-agents-os-f6-r3-eight-finding-semantic-closure-start-decision-v0.1.yaml",
}

TOP_FIELDS = {
    "attempt_commitments", "authority_root_bindings", "context_assessment_bindings",
    "effective_fixture", "environment", "event_order_edges", "occurrence_assertions",
    "r2_bindings", "regression_catalog", "root_fingerprint", "runtime_usable",
    "schema_constraint_profiles", "schema_version", "summary",
}
WRAPPER_FIELDS = {"fingerprint", "key", "payload", "ref", "schema"}
PROFILE_FIELDS = {
    "canonical_instance_fingerprint", "canonical_instance_ref", "closed_fields",
    "cross_field_rules", "field_constraints", "nested_profiles", "schema_fingerprint",
    "schema_name", "schema_revision",
}
CONSTRAINT_FIELDS = {
    "allowed_values", "integer_max", "integer_min", "nested_profile", "nullable", "value_kind",
}
NESTED_PROFILE_FIELDS = {
    "closed_fields", "field_constraints", "profile_fingerprint", "profile_name", "variants",
}
VARIANT_FIELDS = {
    "assessment_kind", "closed_fields", "field_constraints", "variant_fingerprint",
}

SCHEMA_FIELDS: dict[str, list[str]] = {
    "F3CanonicalReadBarrierInputV0_1R2": ["barrier_id", "barrier_revision", "domain", "end_event_sequence", "environment", "start_event_sequence"],
    "TrustedTimeInputV0_1R2": ["barrier_fingerprint", "barrier_ref", "observed_event_sequence", "trusted_time_id", "trusted_time_revision"],
    "OpaqueUpstreamAssessmentInputV0_1R2": ["assessment_id", "assessment_revision", "barrier_fingerprint", "barrier_ref", "is_current_head", "kind", "observed_event_sequence", "owner_contract_fingerprint", "owner_contract_ref", "owner_phase", "result", "subject_fingerprint", "subject_payload", "subject_ref", "subject_revision"],
    "ValidationRequirementRevisionV0_1R2": ["creation_command_fingerprint", "creation_command_ref", "creation_event_fingerprint", "creation_event_ref", "creation_event_sequence", "delivery_subject_fingerprint", "delivery_subject_ref", "delivery_subject_revision", "effectful", "predecessor_fingerprint", "predecessor_ref", "predecessor_revision", "provenance_bindings", "provenance_set_fingerprint", "requirement_id", "requirement_revision", "task_id", "validator_contract_fingerprint", "validator_contract_ref", "validator_contract_revision", "waivability"],
    "RequirementWaiverEventV0_1R2": ["authority_assessment_fingerprint", "authority_assessment_ref", "authority_assessment_revision", "base_snapshot_fingerprint", "base_snapshot_ref", "base_snapshot_revision", "command_fingerprint", "command_ref", "event_fingerprint", "event_ref", "event_sequence", "expires_at_sequence", "is_current_head", "jenn_decision_fingerprint", "jenn_decision_ref", "jenn_decision_revision", "operation", "predecessor_fingerprint", "predecessor_ref", "predecessor_revision", "requirement_fingerprint", "requirement_id", "requirement_revision", "valid_from_sequence", "waiver_id", "waiver_revision"],
    "ValidationSetSnapshotV0_1R2": ["change_kind", "freeze_event_fingerprint", "freeze_event_ref", "frozen_event_sequence", "memberships", "predecessor_fingerprint", "predecessor_ref", "predecessor_revision", "set_id", "set_revision", "source_closure", "source_closure_fingerprint", "waiver_heads"],
    "ValidationAttemptRevisionV0_1R2": ["attempt_id", "attempt_revision", "authority_assessment_fingerprint", "authority_assessment_ref", "authority_assessment_revision", "carry_source", "context_binding", "created_event_fingerprint", "created_event_ref", "created_event_sequence", "current_head", "evidence_assessment_fingerprint", "evidence_assessment_ref", "evidence_assessment_revision", "evidence_bindings", "evidence_set_fingerprint", "f5_assessment_fingerprint", "f5_assessment_ref", "f5_assessment_revision", "method", "observed_event_sequence", "predecessor_fingerprint", "predecessor_ref", "predecessor_revision", "requirement_fingerprint", "requirement_id", "requirement_revision", "set_fingerprint", "set_ref", "set_revision", "state"],
    "ValidationRequirementCurrentDecisionV0_1R2": ["attempt_head_fingerprint", "attempt_head_ref", "barrier_fingerprint", "barrier_ref", "context_fingerprint", "decision_id", "observed_event_sequence", "primary_reason", "reason_codes", "requirement_fingerprint", "requirement_id", "requirement_revision", "result", "set_fingerprint", "set_ref", "set_revision", "waiver_head_fingerprint", "waiver_head_ref"],
    "ValidationSetCurrentDecisionV0_1R2": ["barrier_fingerprint", "barrier_ref", "decision_id", "observed_event_sequence", "primary_reason", "reason_codes", "requirement_decisions", "result", "set_fingerprint", "set_ref", "set_revision"],
    "TaskCompletionEligibilityDecisionV0_1R2": ["barrier_fingerprint", "barrier_ref", "candidate_context", "completion_guard_assessment_fingerprint", "completion_guard_assessment_ref", "completion_guard_assessment_revision", "decision_id", "dependency_context", "f5_blocker_assessment_fingerprint", "f5_blocker_assessment_ref", "f5_blocker_assessment_revision", "observed_event_sequence", "primary_reason", "quiescence_counts", "reason_codes", "result", "set_decision_fingerprint", "set_decision_ref", "task_id", "task_state_assessment_fingerprint", "task_state_assessment_ref", "task_state_assessment_revision"],
}

PROVENANCE_KINDS = ["GOAL_DOMAIN_CONTRACT", "JENN_EXPLICIT", "NOBAO_TASK_SPEC", "RUST_POLICY"]
ASSESSMENT_SUBJECT_FIELDS: dict[str, list[str]] = {
    "CANDIDATE_COMMITMENT_CURRENTNESS": ["candidate_id", "candidate_revision", "status"],
    "COMPLETION_GUARD_CURRENTNESS": ["counts", "guard_id", "guard_revision", "status"],
    "DEPENDENCY_CLOSURE_CURRENTNESS": ["dependency_id", "dependency_revision", "status"],
    "EVIDENCE_SET_CURRENTNESS": ["evidence_bindings", "evidence_set_fingerprint"],
    "F5_COMPLETION_BLOCKING_CURRENTNESS": ["result_id", "result_revision", "status"],
    "F5_DELIVERY_CURRENTNESS": ["delivery_subject_fingerprint", "delivery_subject_ref", "delivery_subject_revision", "status"],
    "JENN_WAIVER_AUTHORITY_CURRENTNESS": ["command_fingerprint", "command_ref", "decision_fingerprint", "decision_ref", "decision_revision", "event_fingerprint", "event_ref", "event_sequence", "requirement_id", "requirement_revision"],
    "REQUIREMENT_PROVENANCE_CURRENTNESS": ["command_fingerprint", "command_ref", "event_fingerprint", "event_ref", "event_sequence", "source_fingerprint", "source_kind", "source_ref", "source_revision"],
    "TASK_CURRENT_STATE": ["candidate_fingerprint", "candidate_ref", "candidate_revision", "dependency_fingerprint", "dependency_ref", "dependency_revision", "task_id", "task_lifecycle", "task_revision", "task_state_revision"],
    "VALIDATION_AUTHORITY_CURRENTNESS": ["requirement_id", "requirement_revision", "validator_contract_fingerprint", "validator_contract_ref", "validator_contract_revision"],
}
ASSESSMENT_RESULTS = {
    "CANDIDATE_COMMITMENT_CURRENTNESS": ("F1", "CURRENT"),
    "COMPLETION_GUARD_CURRENTNESS": ("F3", "CURRENT_ZERO"),
    "DEPENDENCY_CLOSURE_CURRENTNESS": ("F1", "CURRENT_CONFIRMED"),
    "EVIDENCE_SET_CURRENTNESS": ("F3", "EXACT_CURRENT"),
    "F5_COMPLETION_BLOCKING_CURRENTNESS": ("F5", "CLEAR"),
    "F5_DELIVERY_CURRENTNESS": ("F5", "APPLIED_CURRENT"),
    "JENN_WAIVER_AUTHORITY_CURRENTNESS": ("F3", "CURRENT_ACCEPTED"),
    "REQUIREMENT_PROVENANCE_CURRENTNESS": ("F3", "CURRENT_ACCEPTED"),
    "TASK_CURRENT_STATE": ("F1", "CURRENT_VERIFYING"),
    "VALIDATION_AUTHORITY_CURRENTNESS": ("F3", "CURRENT_ACCEPTED"),
}
QUIESCENCE_FIELDS = ["active_attempt_count", "active_effect_count", "open_command_count", "open_delivery_count", "pending_event_count"]
NESTED_FIELDS: dict[str, list[str]] = {
    "CARRY_SOURCE": ["root_source_attempt_fingerprint", "root_source_attempt_ref", "root_source_attempt_revision", "source_attempt_fingerprint", "source_attempt_ref", "source_attempt_revision"],
    "DECISION_BINDING": ["decision_fingerprint", "decision_ref", "requirement_id"],
    "EVIDENCE_BINDING_R3": ["evidence_assessment_fingerprint", "evidence_assessment_ref", "evidence_assessment_revision", "evidence_fingerprint", "evidence_ref", "evidence_revision"],
    "MEMBERSHIP": ["requirement_fingerprint", "requirement_id", "requirement_ref", "requirement_revision"],
    "PROVENANCE_BINDING": ["creation_command_fingerprint", "creation_command_ref", "creation_event_fingerprint", "creation_event_ref", "creation_event_sequence", "source_fingerprint", "source_kind", "source_owner_assessment_fingerprint", "source_owner_assessment_ref", "source_owner_assessment_revision", "source_ref", "source_revision"],
    "QUIESCENCE_COUNTS": QUIESCENCE_FIELDS,
    "SUBJECT_TUPLE": ["fingerprint", "ref", "revision"],
    "VALIDATION_CONTEXT": ["candidate", "context_fingerprint", "dependency", "evidence_set_fingerprint", "requirement_fingerprint", "requirement_id", "requirement_revision", "set_fingerprint", "set_ref", "set_revision", "validator_contract_fingerprint", "validator_contract_ref", "validator_contract_revision"],
    "WAIVER_HEAD": ["waiver_fingerprint", "waiver_ref", "waiver_revision"],
}
SCHEMA_NESTED = {
    ("OpaqueUpstreamAssessmentInputV0_1R2", "subject_payload"): "ASSESSMENT_SUBJECT_BY_KIND",
    ("ValidationRequirementRevisionV0_1R2", "provenance_bindings"): "PROVENANCE_BINDING",
    ("ValidationSetSnapshotV0_1R2", "memberships"): "MEMBERSHIP",
    ("ValidationSetSnapshotV0_1R2", "source_closure"): "PROVENANCE_BINDING",
    ("ValidationSetSnapshotV0_1R2", "waiver_heads"): "WAIVER_HEAD",
    ("ValidationAttemptRevisionV0_1R2", "carry_source"): "CARRY_SOURCE",
    ("ValidationAttemptRevisionV0_1R2", "context_binding"): "VALIDATION_CONTEXT",
    ("ValidationAttemptRevisionV0_1R2", "evidence_bindings"): "EVIDENCE_BINDING_R3",
    ("ValidationSetCurrentDecisionV0_1R2", "requirement_decisions"): "DECISION_BINDING",
    ("TaskCompletionEligibilityDecisionV0_1R2", "candidate_context"): "SUBJECT_TUPLE",
    ("TaskCompletionEligibilityDecisionV0_1R2", "dependency_context"): "SUBJECT_TUPLE",
    ("TaskCompletionEligibilityDecisionV0_1R2", "quiescence_counts"): "QUIESCENCE_COUNTS",
    ("COMPLETION_GUARD_CURRENTNESS", "counts"): "QUIESCENCE_COUNTS",
    ("EVIDENCE_SET_CURRENTNESS", "evidence_bindings"): "EVIDENCE_BINDING_R3",
}
NESTED_ARRAY_FIELDS = {
    ("ValidationRequirementRevisionV0_1R2", "provenance_bindings"),
    ("ValidationSetSnapshotV0_1R2", "memberships"),
    ("ValidationSetSnapshotV0_1R2", "source_closure"),
    ("ValidationSetSnapshotV0_1R2", "waiver_heads"),
    ("ValidationAttemptRevisionV0_1R2", "evidence_bindings"),
    ("ValidationSetCurrentDecisionV0_1R2", "requirement_decisions"),
    ("EVIDENCE_SET_CURRENTNESS", "evidence_bindings"),
}
NULLABLE_FIELDS = {
    ("ValidationRequirementRevisionV0_1R2", field) for field in ["delivery_subject_fingerprint", "delivery_subject_ref", "delivery_subject_revision", "predecessor_fingerprint", "predecessor_ref", "predecessor_revision"]
} | {
    ("RequirementWaiverEventV0_1R2", field) for field in ["predecessor_fingerprint", "predecessor_ref", "predecessor_revision"]
} | {
    ("ValidationSetSnapshotV0_1R2", field) for field in ["predecessor_fingerprint", "predecessor_ref", "predecessor_revision"]
} | {
    ("ValidationAttemptRevisionV0_1R2", field) for field in ["carry_source", "f5_assessment_fingerprint", "f5_assessment_ref", "f5_assessment_revision", "predecessor_fingerprint", "predecessor_ref", "predecessor_revision"]
} | {
    ("ValidationRequirementCurrentDecisionV0_1R2", field) for field in ["attempt_head_fingerprint", "attempt_head_ref", "context_fingerprint", "waiver_head_fingerprint", "waiver_head_ref"]
}
ENUMS: dict[tuple[str, str], list[str]] = {
    ("F3CanonicalReadBarrierInputV0_1R2", "domain"): ["SYNTHETIC_TEST"],
    ("F3CanonicalReadBarrierInputV0_1R2", "environment"): ["SYNTHETIC_TEST"],
    ("OpaqueUpstreamAssessmentInputV0_1R2", "kind"): sorted(ASSESSMENT_RESULTS),
    ("OpaqueUpstreamAssessmentInputV0_1R2", "owner_phase"): ["F1", "F3", "F5"],
    ("OpaqueUpstreamAssessmentInputV0_1R2", "result"): ["APPLIED_CURRENT", "CLEAR", "CURRENT", "CURRENT_ACCEPTED", "CURRENT_CONFIRMED", "CURRENT_VERIFYING", "CURRENT_ZERO", "EXACT_CURRENT"],
    ("ValidationRequirementRevisionV0_1R2", "waivability"): ["NON_WAIVABLE", "WAIVABLE"],
    ("RequirementWaiverEventV0_1R2", "operation"): ["EXPIRE", "GRANT", "INVALIDATE", "REVOKE"],
    ("ValidationSetSnapshotV0_1R2", "change_kind"): ["BASE", "WAIVER_CHANGE"],
    ("ValidationAttemptRevisionV0_1R2", "method"): ["EVIDENCE_CARRY_FORWARD_REVIEW", "FRESH_VALIDATION"],
    ("ValidationAttemptRevisionV0_1R2", "state"): ["FAILED", "PASSED", "PENDING"],
    ("ValidationRequirementCurrentDecisionV0_1R2", "result"): ["INDETERMINATE", "NOT_REQUIRED", "PENDING", "SATISFIED", "UNSATISFIED", "WAIVED"],
    ("ValidationSetCurrentDecisionV0_1R2", "result"): ["INDETERMINATE", "NOT_SATISFIED", "SATISFIED"],
    ("TaskCompletionEligibilityDecisionV0_1R2", "result"): ["ELIGIBLE", "INDETERMINATE", "NOT_ELIGIBLE"],
    ("CANDIDATE_COMMITMENT_CURRENTNESS", "status"): ["CURRENT"],
    ("COMPLETION_GUARD_CURRENTNESS", "status"): ["CURRENT_ZERO"],
    ("DEPENDENCY_CLOSURE_CURRENTNESS", "status"): ["CURRENT_CONFIRMED"],
    ("F5_COMPLETION_BLOCKING_CURRENTNESS", "status"): ["CLEAR"],
    ("F5_DELIVERY_CURRENTNESS", "status"): ["APPLIED_CURRENT"],
    ("REQUIREMENT_PROVENANCE_CURRENTNESS", "source_kind"): PROVENANCE_KINDS,
    ("TASK_CURRENT_STATE", "task_lifecycle"): ["VERIFYING"],
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R2V = load_module("f6_r2_validator_for_r3_validation", R2_VALIDATOR_PATH)


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_float(value: str) -> Any:
    raise ValueError(f"float forbidden: {value}")


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates, parse_float=reject_float)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def typed_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def is_int(value: Any, *, minimum: int = 0) -> bool:
    return type(value) is int and minimum <= value <= SAFE_MAX


def valid_hash(value: Any) -> bool:
    return isinstance(value, str) and HEX_RE.fullmatch(value) is not None


def valid_ref(value: Any) -> bool:
    return isinstance(value, str) and REF_RE.fullmatch(value) is not None and unicodedata.normalize("NFC", value) == value


def exact_fields(value: Any, expected: set[str] | list[str], path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"schema: {path} object required")
        return False
    if set(value) != set(expected):
        errors.append(f"schema: {path} closed fields mismatch")
        return False
    return True


def check_tree(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, float):
        errors.append(f"schema: {path} float forbidden")
    elif type(value) is int and not (-SAFE_MAX <= value <= SAFE_MAX):
        errors.append(f"schema: {path} unsafe integer")
    elif isinstance(value, str) and unicodedata.normalize("NFC", value) != value:
        errors.append(f"schema: {path} non-NFC string")
    elif isinstance(value, dict):
        for key, item in value.items():
            check_tree(item, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            check_tree(item, f"{path}[{index}]", errors)


def rows(data: dict[str, Any], schema: str) -> list[dict[str, Any]]:
    return data["normative_objects"][schema]


def wrapper_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return R2V.wrapper_index(data)


def find_kind(data: dict[str, Any], kind: str, occurrence: int = 0) -> dict[str, Any]:
    matches = [row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2") if row["payload"]["kind"] == kind]
    return matches[occurrence]


def value_kind(field: str, value: Any) -> str:
    if field.endswith("_fingerprint") or field == "fingerprint":
        return "lowercase_sha256"
    if field.endswith("_ref") or field == "ref":
        return "stable_ref"
    if field in {"revision", "sequence"} or field.endswith("_revision") or field.endswith("_sequence"):
        return "positive_safe_integer"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "stable_string"


def expected_constraint(schema: str, field: str, value: Any) -> dict[str, Any]:
    nested = SCHEMA_NESTED.get((schema, field))
    kind = ("array" if (schema, field) in NESTED_ARRAY_FIELDS else "object") if nested else value_kind(field, value)
    return {
        "allowed_values": ENUMS.get((schema, field)),
        "integer_max": SAFE_MAX if kind in {"positive_safe_integer", "non_negative_safe_integer"} else None,
        "integer_min": 1 if kind == "positive_safe_integer" else (0 if kind == "non_negative_safe_integer" else None),
        "nested_profile": nested,
        "nullable": (schema, field) in NULLABLE_FIELDS,
        "value_kind": kind,
    }


def expected_nested_profiles(schema: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    names = sorted({name for (owner, _), name in SCHEMA_NESTED.items() if owner == schema})
    if schema == "OpaqueUpstreamAssessmentInputV0_1R2":
        names = sorted(set(names) | {"EVIDENCE_BINDING_R3", "QUIESCENCE_COUNTS"})
    if "VALIDATION_CONTEXT" in names:
        names = sorted(set(names) | {"SUBJECT_TUPLE"})
    result = []
    for name in names:
        if name == "ASSESSMENT_SUBJECT_BY_KIND":
            fields: list[str] = []
            constraints: dict[str, Any] = {}
            variants = []
            for kind in sorted(ASSESSMENT_SUBJECT_FIELDS):
                instance = {
                    field: ([] if (kind, field) in NESTED_ARRAY_FIELDS else {})
                    if (kind, field) in SCHEMA_NESTED
                    else (1 if field in {"revision", "sequence"} or field.endswith("_revision") or field.endswith("_sequence") else "sample")
                    for field in ASSESSMENT_SUBJECT_FIELDS[kind]
                }
                variant = {
                    "assessment_kind": kind,
                    "closed_fields": ASSESSMENT_SUBJECT_FIELDS[kind],
                    "field_constraints": {field: expected_constraint(kind, field, instance[field]) for field in ASSESSMENT_SUBJECT_FIELDS[kind]},
                }
                variant["variant_fingerprint"] = typed_hash("agents-os.f6.r3.assessment-subject-profile", variant)
                variants.append(variant)
        else:
            fields = NESTED_FIELDS[name]
            constraints = {field: expected_constraint(name, field, None if field.startswith("predecessor_") else "sample") for field in fields}
            for field in fields:
                if field in {"candidate", "dependency"}:
                    constraints[field]["value_kind"] = "object"
                    constraints[field]["nested_profile"] = "SUBJECT_TUPLE"
                if field in QUIESCENCE_FIELDS:
                    constraints[field].update({"value_kind": "non_negative_safe_integer", "nullable": False, "integer_min": 0, "integer_max": SAFE_MAX})
            variants = []
        unsigned = {"closed_fields": fields, "field_constraints": constraints, "profile_name": name, "variants": variants}
        result.append({**unsigned, "profile_fingerprint": typed_hash("agents-os.f6.r3.nested-profile", unsigned)})
    return result


def expected_profiles(data: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for schema in sorted(SCHEMA_FIELDS):
        instance = rows(data, schema)[0]
        profile = {
            "canonical_instance_fingerprint": instance["fingerprint"],
            "canonical_instance_ref": instance["ref"],
            "closed_fields": SCHEMA_FIELDS[schema],
            "cross_field_rules": [f"R3-{schema}-TOTAL-MATRIX"],
            "field_constraints": {field: expected_constraint(schema, field, instance["payload"][field]) for field in SCHEMA_FIELDS[schema]},
            "nested_profiles": expected_nested_profiles(schema, data),
            "schema_name": schema,
            "schema_revision": 3,
        }
        profile["schema_fingerprint"] = typed_hash("agents-os.f6.r3.schema-profile", profile)
        result.append(profile)
    return result


def check_primitive(value: Any, constraint: dict[str, Any], path: str, errors: list[str]) -> bool:
    if value is None:
        if constraint["nullable"] is not True:
            errors.append(f"schema: {path} null forbidden")
            return False
        return True
    kind = constraint["value_kind"]
    valid = {
        "stable_string": lambda v: isinstance(v, str) and bool(v) and unicodedata.normalize("NFC", v) == v,
        "stable_ref": valid_ref,
        "lowercase_sha256": valid_hash,
        "boolean": lambda v: type(v) is bool,
        "positive_safe_integer": lambda v: is_int(v, minimum=1),
        "non_negative_safe_integer": lambda v: is_int(v, minimum=0),
        "object": lambda v: isinstance(v, dict),
        "array": lambda v: isinstance(v, list),
    }.get(kind, lambda _v: False)(value)
    if not valid:
        errors.append(f"schema: {path} invalid {kind}")
        return False
    allowed = constraint["allowed_values"]
    if allowed is not None and value not in allowed:
        errors.append(f"schema: {path} unknown enum")
        return False
    return True


def check_nested(value: Any, name: str, path: str, errors: list[str]) -> None:
    if name == "ASSESSMENT_SUBJECT_BY_KIND":
        return
    fields = NESTED_FIELDS[name]
    items = value if isinstance(value, list) else [value]
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]" if isinstance(value, list) else path
        if not exact_fields(item, fields, item_path, errors):
            continue
        for field in fields:
            constraint = expected_constraint(name, field, item[field])
            if field in QUIESCENCE_FIELDS:
                constraint.update({"value_kind": "non_negative_safe_integer", "nullable": False, "integer_min": 0, "integer_max": SAFE_MAX})
            if field in {"candidate", "dependency"}:
                constraint.update({"value_kind": "object", "nested_profile": "SUBJECT_TUPLE"})
            if check_primitive(item[field], constraint, f"{item_path}.{field}", errors) and constraint["nested_profile"] and item[field] is not None:
                check_nested(item[field], constraint["nested_profile"], f"{item_path}.{field}", errors)


def validate_profiles_and_values(data: dict[str, Any], profiles: Any, errors: list[str]) -> None:
    expected = expected_profiles(data)
    if profiles != expected:
        errors.append("schema: complete schema profile inventory mismatch")
    if not isinstance(profiles, list):
        return
    for schema, objects in data["normative_objects"].items():
        if schema not in SCHEMA_FIELDS:
            errors.append(f"schema: unknown normative schema {schema}")
            continue
        for index, wrapper in enumerate(objects):
            path = f"effective.{schema}[{index}]"
            if not exact_fields(wrapper, WRAPPER_FIELDS, path, errors):
                continue
            payload = wrapper["payload"]
            if not exact_fields(payload, SCHEMA_FIELDS[schema], path + ".payload", errors):
                continue
            for field in SCHEMA_FIELDS[schema]:
                constraint = expected_constraint(schema, field, rows(data, schema)[0]["payload"][field])
                value = payload[field]
                if check_primitive(value, constraint, f"{path}.payload.{field}", errors) and constraint["nested_profile"] and value is not None:
                    if constraint["nested_profile"] == "ASSESSMENT_SUBJECT_BY_KIND":
                        kind = payload["kind"]
                        fields = ASSESSMENT_SUBJECT_FIELDS.get(kind)
                        if fields is None or not exact_fields(value, fields or [], f"{path}.payload.subject_payload", errors):
                            continue
                        for nested_field in fields:
                            nested_constraint = expected_constraint(kind, nested_field, value[nested_field])
                            if check_primitive(value[nested_field], nested_constraint, f"{path}.payload.subject_payload.{nested_field}", errors) and nested_constraint["nested_profile"]:
                                check_nested(value[nested_field], nested_constraint["nested_profile"], f"{path}.payload.subject_payload.{nested_field}", errors)
                    else:
                        check_nested(value, constraint["nested_profile"], f"{path}.payload.{field}", errors)


def validate_supporting_objects(data: dict[str, Any], errors: list[str]) -> None:
    expected_groups = {
        "commands": ("SupportCommand", {"command_id", "purpose", "subject_fingerprint"}),
        "delivery_subjects": ("SupportDeliverySubject", {"subject_id", "subject_revision"}),
        "events": ("SupportEvent", {"command_fingerprint", "command_ref", "event_id", "event_kind", "event_sequence", "subject_fingerprint"}),
        "evidence_assessments": ("SupportEvidenceAssessment", {"assessment_id", "assessment_revision", "barrier_fingerprint", "barrier_ref", "is_current_head", "observed_event_sequence", "owner_contract_fingerprint", "owner_contract_ref", "owner_contract_revision", "owner_phase", "result", "subject_fingerprint", "subject_ref", "subject_revision"}),
        "evidence_objects": ("SupportEvidenceObject", {"environment", "evidence_id", "evidence_revision", "validation_subject"}),
        "jenn_decisions": ("SupportJennDecision", {"decision_event_sequence", "decision_id", "decision_revision", "requirement_id", "requirement_revision", "result"}),
        "owner_contracts": ("SupportOwnerContract", {"owner_phase", "revision"}),
        "provenance_sources": ("SupportProvenanceSource", {"source_kind", "source_revision", "task_id"}),
        "validator_contracts": ("SupportValidatorContract", {"contract_id", "contract_revision"}),
    }
    groups = data.get("supporting_objects")
    if not isinstance(groups, dict) or set(groups) != set(expected_groups):
        errors.append("schema: supporting object group inventory mismatch")
        return
    for group, (schema, payload_fields) in expected_groups.items():
        if not isinstance(groups[group], list):
            errors.append(f"schema: supporting group {group} must be an array")
            continue
        for index, wrapper in enumerate(groups[group]):
            path = f"support.{group}[{index}]"
            if not exact_fields(wrapper, WRAPPER_FIELDS, path, errors):
                continue
            if wrapper["schema"] != schema:
                errors.append(f"schema: {path} schema mismatch")
            if not exact_fields(wrapper["payload"], payload_fields, path + ".payload", errors):
                continue
            if wrapper["fingerprint"] != R2V.typed_hash(f"agents-os.f6.r2.{schema}", wrapper["payload"]):
                errors.append(f"integrity: {path} fingerprint mismatch")
            if not valid_ref(wrapper["ref"]):
                errors.append(f"schema: {path} invalid ref")
    for source in groups["provenance_sources"]:
        if source["payload"]["source_kind"] not in PROVENANCE_KINDS:
            errors.append("semantic: supporting provenance source kind outside closed set")
    for owner in groups["owner_contracts"]:
        if owner["payload"]["owner_phase"] not in {"F1", "F3", "F5"} or not is_int(owner["payload"]["revision"], minimum=1):
            errors.append("schema: supporting owner contract invalid")
    for evidence in groups["evidence_objects"]:
        if evidence["payload"]["environment"] != "SYNTHETIC_TEST" or not is_int(evidence["payload"]["evidence_revision"], minimum=1):
            errors.append("semantic: evidence object escaped synthetic boundary")


def binding_fingerprint(domain: str, row: dict[str, Any]) -> str:
    unsigned = dict(row)
    unsigned.pop("binding_fingerprint", None)
    unsigned.pop("commitment_fingerprint", None)
    unsigned.pop("edge_fingerprint", None)
    return typed_hash(domain, unsigned)


def attempt_event_subject(attempt: dict[str, Any]) -> dict[str, Any]:
    payload = attempt["payload"]
    return {
        "attempt_id": payload["attempt_id"], "attempt_revision": payload["attempt_revision"],
        "context_fingerprint": payload["context_binding"]["context_fingerprint"],
        "evidence_set_fingerprint": payload["evidence_set_fingerprint"],
        "method": payload["method"], "predecessor_fingerprint": payload["predecessor_fingerprint"],
        "predecessor_ref": payload["predecessor_ref"], "predecessor_revision": payload["predecessor_revision"],
        "requirement_fingerprint": payload["requirement_fingerprint"],
        "requirement_id": payload["requirement_id"],
        "requirement_revision": payload["requirement_revision"], "state": payload["state"],
    }


def exact_tuple(assessment: dict[str, Any]) -> dict[str, Any]:
    payload = assessment["payload"]
    return {"fingerprint": payload["subject_fingerprint"], "ref": payload["subject_ref"], "revision": payload["subject_revision"]}


def validate_authority_and_context(data: dict[str, Any], outer: dict[str, Any], errors: list[str]) -> None:
    index = wrapper_index(data)
    contracts = {row["payload"]["owner_phase"]: row for row in data["supporting_objects"]["owner_contracts"]}
    expected_roots = []
    for kind in sorted(ASSESSMENT_RESULTS):
        phase = ASSESSMENT_RESULTS[kind][0]
        contract = contracts[phase]
        item = {
            "assessment_kind": kind, "owner_phase": phase,
            "owner_contract_ref": contract["ref"], "owner_contract_revision": contract["payload"]["revision"],
            "owner_contract_fingerprint": contract["fingerprint"],
        }
        item["binding_fingerprint"] = binding_fingerprint("agents-os.f6.r3.authority-root", item)
        expected_roots.append(item)
    if outer["authority_root_bindings"] != expected_roots:
        errors.append("semantic: authority root binding inventory mismatch")
    barrier = rows(data, "F3CanonicalReadBarrierInputV0_1R2")[0]
    trusted = rows(data, "TrustedTimeInputV0_1R2")[0]
    for assessment in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2"):
        payload = assessment["payload"]
        kind = payload["kind"]
        expected = ASSESSMENT_RESULTS.get(kind)
        if expected is None or (payload["owner_phase"], payload["result"]) != expected:
            errors.append(f"semantic: {kind} owner/result matrix mismatch")
            continue
        contract = contracts[expected[0]]
        if (payload["owner_contract_ref"], payload["owner_contract_fingerprint"]) != (contract["ref"], contract["fingerprint"]):
            errors.append(f"semantic: {kind} owner root mismatch")
        if payload["barrier_ref"] != barrier["ref"] or payload["barrier_fingerprint"] != barrier["fingerprint"] or payload["is_current_head"] is not True:
            errors.append(f"semantic: {kind} current barrier mismatch")
        if payload["observed_event_sequence"] > trusted["payload"]["observed_event_sequence"]:
            errors.append(f"semantic: {kind} observed beyond trusted evaluation")
    kinds = [row["payload"]["kind"] for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2")]
    for required in ASSESSMENT_RESULTS:
        if required not in kinds:
            errors.append(f"semantic: required assessment kind missing: {required}")

    candidate_rows = [row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2") if row["payload"]["kind"] == "CANDIDATE_COMMITMENT_CURRENTNESS"]
    dependency_rows = [row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2") if row["payload"]["kind"] == "DEPENDENCY_CLOSURE_CURRENTNESS"]
    if len(candidate_rows) != 1 or len(dependency_rows) != 1:
        errors.append("semantic: exactly one candidate and dependency assessment required")
        return
    candidate, dependency = candidate_rows[0], dependency_rows[0]
    consumers = rows(data, "ValidationAttemptRevisionV0_1R2") + rows(data, "TaskCompletionEligibilityDecisionV0_1R2")
    expected_bindings = []
    for consumer in consumers:
        item = {
            "candidate_assessment_fingerprint": candidate["fingerprint"], "candidate_assessment_ref": candidate["ref"],
            "candidate_assessment_revision": candidate["payload"]["assessment_revision"],
            "consumer_fingerprint": consumer["fingerprint"], "consumer_ref": consumer["ref"],
            "consumer_revision": consumer["payload"].get("attempt_revision", 1),
            "dependency_assessment_fingerprint": dependency["fingerprint"], "dependency_assessment_ref": dependency["ref"],
            "dependency_assessment_revision": dependency["payload"]["assessment_revision"],
        }
        item["binding_fingerprint"] = binding_fingerprint("agents-os.f6.r3.context-assessment-binding", item)
        expected_bindings.append(item)
    expected_bindings.sort(key=lambda item: item["consumer_ref"])
    if outer["context_assessment_bindings"] != expected_bindings:
        errors.append("semantic: context assessment binding inventory mismatch")
    candidate_tuple, dependency_tuple = exact_tuple(candidate), exact_tuple(dependency)
    task = find_kind(data, "TASK_CURRENT_STATE")
    task_payload = task["payload"]["subject_payload"]
    if {"ref": task_payload["candidate_ref"], "revision": task_payload["candidate_revision"], "fingerprint": task_payload["candidate_fingerprint"]} != candidate_tuple:
        errors.append("semantic: Task candidate does not equal owner assessment")
    if {"ref": task_payload["dependency_ref"], "revision": task_payload["dependency_revision"], "fingerprint": task_payload["dependency_fingerprint"]} != dependency_tuple:
        errors.append("semantic: Task dependency does not equal owner assessment")
    for attempt in rows(data, "ValidationAttemptRevisionV0_1R2"):
        if attempt["payload"]["context_binding"]["candidate"] != candidate_tuple:
            errors.append(f"semantic: {attempt['key']} candidate context detached")
        if attempt["payload"]["context_binding"]["dependency"] != dependency_tuple:
            errors.append(f"semantic: {attempt['key']} dependency context detached")
    completion = rows(data, "TaskCompletionEligibilityDecisionV0_1R2")[0]
    if completion["payload"]["candidate_context"] != candidate_tuple or completion["payload"]["dependency_context"] != dependency_tuple:
        errors.append("semantic: completion context detached from owner assessments")


def validate_provenance_waiver_time(data: dict[str, Any], outer: dict[str, Any], errors: list[str]) -> None:
    index = wrapper_index(data)
    barrier = rows(data, "F3CanonicalReadBarrierInputV0_1R2")[0]
    trusted = rows(data, "TrustedTimeInputV0_1R2")[0]
    if trusted["payload"]["barrier_ref"] != barrier["ref"] or trusted["payload"]["barrier_fingerprint"] != barrier["fingerprint"]:
        errors.append("semantic: TrustedTime detached from exact F3 barrier")
    observed = trusted["payload"]["observed_event_sequence"]
    if not (barrier["payload"]["start_event_sequence"] <= observed <= barrier["payload"]["end_event_sequence"]):
        errors.append("semantic: TrustedTime outside F3 barrier")
    for requirement in rows(data, "ValidationRequirementRevisionV0_1R2"):
        payload = requirement["payload"]
        natural = None
        for binding in payload["provenance_bindings"]:
            source = index.get(binding["source_ref"])
            assessment = index.get(binding["source_owner_assessment_ref"])
            command = index.get(binding["creation_command_ref"])
            event = index.get(binding["creation_event_ref"])
            if None in {id(source) if source is not None else None, id(assessment) if assessment is not None else None, id(command) if command is not None else None, id(event) if event is not None else None}:
                errors.append("semantic: unresolved provenance graph object")
                continue
            if source["payload"].get("source_kind") not in PROVENANCE_KINDS or binding["source_kind"] != source["payload"].get("source_kind"):
                errors.append("semantic: provenance source kind outside closed authority set")
            natural = {"requirement_id": payload["requirement_id"], "requirement_revision": payload["requirement_revision"], "source_fingerprint": source["fingerprint"], "source_ref": source["ref"]}
            if command["payload"].get("purpose") != "CREATE_OR_REVISE_REQUIREMENT" or command["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.command-subject", natural):
                errors.append("semantic: Requirement creation Command mismatch")
            if event["payload"].get("event_kind") != "REQUIREMENT_COMMITTED" or event["payload"].get("command_ref") != command["ref"] or event["payload"].get("command_fingerprint") != command["fingerprint"] or event["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.event-subject", natural):
                errors.append("semantic: Requirement creation Event mismatch")
            expected_subject = {
                "command_fingerprint": command["fingerprint"], "command_ref": command["ref"],
                "event_fingerprint": event["fingerprint"], "event_ref": event["ref"],
                "event_sequence": event["payload"]["event_sequence"], "source_fingerprint": source["fingerprint"],
                "source_kind": source["payload"]["source_kind"], "source_ref": source["ref"],
                "source_revision": source["payload"]["source_revision"],
            }
            if assessment["payload"].get("subject_payload") != expected_subject:
                errors.append("semantic: provenance owner assessment does not bind typed graph")

    waiver = rows(data, "RequirementWaiverEventV0_1R2")[0]
    wp = waiver["payload"]
    decision = index.get(wp["jenn_decision_ref"])
    command = index.get(wp["command_ref"])
    event = index.get(wp["event_ref"])
    authority = index.get(wp["authority_assessment_ref"])
    requirement = next((row for row in rows(data, "ValidationRequirementRevisionV0_1R2") if row["payload"]["requirement_id"] == wp["requirement_id"] and row["payload"]["requirement_revision"] == wp["requirement_revision"]), None)
    if any(item is None for item in [decision, command, event, authority, requirement]):
        errors.append("semantic: unresolved waiver authority root")
        return
    if set(decision["payload"]) != {"decision_event_sequence", "decision_id", "decision_revision", "requirement_id", "requirement_revision", "result"}:
        errors.append("schema: Jenn decision closed fields mismatch")
    if (decision["payload"].get("requirement_id"), decision["payload"].get("requirement_revision"), decision["payload"].get("result")) != (wp["requirement_id"], wp["requirement_revision"], "CURRENT_ACCEPTED"):
        errors.append("semantic: Jenn decision does not authorize exact Requirement")
    natural = {"decision_fingerprint": decision["fingerprint"], "decision_ref": decision["ref"], "decision_revision": decision["payload"]["decision_revision"], "requirement_id": wp["requirement_id"], "requirement_revision": wp["requirement_revision"]}
    if command["payload"].get("purpose") != "GRANT_REQUIREMENT_WAIVER" or command["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.command-subject", natural):
        errors.append("semantic: waiver Command not rooted in exact Jenn decision")
    if event["payload"].get("event_kind") != "WAIVER_COMMITTED" or event["payload"].get("command_ref") != command["ref"] or event["payload"].get("command_fingerprint") != command["fingerprint"] or event["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.event-subject", natural):
        errors.append("semantic: waiver Event not rooted in exact Command")
    expected_authority = {
        "command_fingerprint": command["fingerprint"], "command_ref": command["ref"],
        "decision_fingerprint": decision["fingerprint"], "decision_ref": decision["ref"],
        "decision_revision": decision["payload"]["decision_revision"],
        "event_fingerprint": event["fingerprint"], "event_ref": event["ref"],
        "event_sequence": event["payload"]["event_sequence"],
        "requirement_id": wp["requirement_id"], "requirement_revision": wp["requirement_revision"],
    }
    if authority["payload"].get("subject_payload") != expected_authority:
        errors.append("semantic: waiver owner assessment root mismatch")
    snapshots = sorted(rows(data, "ValidationSetSnapshotV0_1R2"), key=lambda row: row["payload"]["set_revision"])
    if not (snapshots[0]["payload"]["frozen_event_sequence"] < decision["payload"].get("decision_event_sequence", SAFE_MAX) <= wp["event_sequence"] <= snapshots[-1]["payload"]["frozen_event_sequence"] <= observed <= barrier["payload"]["end_event_sequence"]):
        errors.append("semantic: waiver/TrustedTime typed Event order invalid")

    for snapshot in snapshots:
        command = index.get(snapshot["payload"]["freeze_event_ref"])
        event = command
        if event is None:
            errors.append("semantic: Validation Set freeze Event unresolved")
            continue
        linked_command = index.get(event["payload"].get("command_ref"))
        natural = {"set_id": snapshot["payload"]["set_id"], "revision": snapshot["payload"]["set_revision"]}
        if snapshot["payload"]["waiver_heads"]:
            natural["waiver"] = snapshot["payload"]["waiver_heads"][0]["waiver_fingerprint"]
        if linked_command is None or linked_command["payload"].get("purpose") != "FREEZE_VALIDATION_SET" or linked_command["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.command-subject", natural):
            errors.append("semantic: Validation Set freeze Command typed subject mismatch")
        if event["payload"].get("event_kind") != "VALIDATION_SET_FROZEN" or linked_command is None or event["payload"].get("command_fingerprint") != linked_command["fingerprint"] or event["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.event-subject", natural):
            errors.append("semantic: Validation Set freeze Event typed subject mismatch")
    for attempt in rows(data, "ValidationAttemptRevisionV0_1R2"):
        event = index.get(attempt["payload"]["created_event_ref"])
        linked_command = None if event is None else index.get(event["payload"].get("command_ref"))
        natural = attempt_event_subject(attempt)
        if linked_command is None or linked_command["payload"].get("purpose") != "COMMIT_VALIDATION_ATTEMPT" or linked_command["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.command-subject", natural):
            errors.append(f"semantic: {attempt['key']} commit Command typed subject mismatch")
        if event is None or event["payload"].get("event_kind") != "VALIDATION_ATTEMPT_COMMITTED" or linked_command is None or event["payload"].get("command_fingerprint") != linked_command["fingerprint"] or event["payload"].get("subject_fingerprint") != R2V.typed_hash("agents-os.f6.r2.event-subject", natural) or event["payload"].get("event_sequence") != attempt["payload"]["created_event_sequence"]:
            errors.append(f"semantic: {attempt['key']} commit Event typed subject mismatch")

    expected_edges = derive_event_edges(data)
    if outer["event_order_edges"] != expected_edges:
        errors.append("semantic: complete Event order edge set mismatch")
    for item in expected_edges:
        ok = item["from_sequence"] < item["to_sequence"] if item["relation"] == "LT" else item["from_sequence"] <= item["to_sequence"]
        if not ok:
            errors.append(f"semantic: invalid Event order {item['purpose']}")


def edge(from_ref: str, from_sequence: int, to_ref: str, to_sequence: int, relation: str, purpose: str) -> dict[str, Any]:
    item = {"from_ref": from_ref, "from_sequence": from_sequence, "purpose": purpose, "relation": relation, "to_ref": to_ref, "to_sequence": to_sequence}
    item["edge_fingerprint"] = binding_fingerprint("agents-os.f6.r3.event-order-edge", item)
    return item


def derive_event_edges(data: dict[str, Any]) -> list[dict[str, Any]]:
    index = wrapper_index(data)
    result = []
    requirements = rows(data, "ValidationRequirementRevisionV0_1R2")
    for req in requirements:
        payload = req["payload"]
        if payload["predecessor_ref"] is not None and payload["predecessor_ref"] in index:
            predecessor = index[payload["predecessor_ref"]]
            result.append(edge(predecessor["payload"]["creation_event_ref"], predecessor["payload"]["creation_event_sequence"], payload["creation_event_ref"], payload["creation_event_sequence"], "LT", "REQUIREMENT_PREDECESSOR"))
    for snapshot in rows(data, "ValidationSetSnapshotV0_1R2"):
        for member in snapshot["payload"]["memberships"]:
            if member["requirement_ref"] not in index:
                continue
            req = index[member["requirement_ref"]]
            result.append(edge(req["payload"]["creation_event_ref"], req["payload"]["creation_event_sequence"], snapshot["payload"]["freeze_event_ref"], snapshot["payload"]["frozen_event_sequence"], "LE", "REQUIREMENT_IN_SNAPSHOT"))
    snapshots = sorted(rows(data, "ValidationSetSnapshotV0_1R2"), key=lambda row: row["payload"]["set_revision"])
    decision = data["supporting_objects"]["jenn_decisions"][0]
    waiver = rows(data, "RequirementWaiverEventV0_1R2")[0]
    if len(snapshots) >= 2:
        base, current = snapshots[0], snapshots[-1]
        result.extend([
            edge(base["payload"]["freeze_event_ref"], base["payload"]["frozen_event_sequence"], decision["ref"], decision["payload"].get("decision_event_sequence", SAFE_MAX), "LT", "BASE_BEFORE_JENN_DECISION"),
            edge(decision["ref"], decision["payload"].get("decision_event_sequence", SAFE_MAX), waiver["payload"]["event_ref"], waiver["payload"]["event_sequence"], "LE", "JENN_DECISION_BEFORE_WAIVER"),
            edge(waiver["payload"]["event_ref"], waiver["payload"]["event_sequence"], current["payload"]["freeze_event_ref"], current["payload"]["frozen_event_sequence"], "LE", "WAIVER_BEFORE_CONSUMING_SNAPSHOT"),
        ])
        assessment_index = {row["ref"]: row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2")}
        for attempt in rows(data, "ValidationAttemptRevisionV0_1R2"):
            aggregate = assessment_index.get(attempt["payload"]["evidence_assessment_ref"])
            if aggregate is None:
                continue
            result.extend([
                edge(current["payload"]["freeze_event_ref"], current["payload"]["frozen_event_sequence"], attempt["payload"]["created_event_ref"], attempt["payload"]["created_event_sequence"], "LE", "SNAPSHOT_BEFORE_ATTEMPT"),
                edge(attempt["payload"]["created_event_ref"], attempt["payload"]["created_event_sequence"], aggregate["ref"], aggregate["payload"]["observed_event_sequence"], "LE", "ATTEMPT_BEFORE_EVIDENCE_ASSESSMENT"),
            ])
    trusted = rows(data, "TrustedTimeInputV0_1R2")[0]
    barrier = rows(data, "F3CanonicalReadBarrierInputV0_1R2")[0]
    result.extend([
        edge("synth:f6:r3:all-assessments", max((row["payload"]["observed_event_sequence"] for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2")), default=SAFE_MAX), trusted["ref"], trusted["payload"]["observed_event_sequence"], "LE", "ASSESSMENTS_BEFORE_TRUSTED_EVALUATION"),
        edge(trusted["ref"], trusted["payload"]["observed_event_sequence"], barrier["ref"], barrier["payload"]["end_event_sequence"], "LE", "TRUSTED_EVALUATION_WITHIN_BARRIER"),
    ])
    return sorted(result, key=lambda item: (item["purpose"], item["from_ref"], item["to_ref"]))


def validate_evidence_carry_f5(data: dict[str, Any], outer: dict[str, Any], errors: list[str]) -> None:
    index = wrapper_index(data)
    f3_contract = next(row for row in data["supporting_objects"]["owner_contracts"] if row["payload"]["owner_phase"] == "F3")
    barrier = rows(data, "F3CanonicalReadBarrierInputV0_1R2")[0]
    evidence_objects = {row["ref"]: row for row in data["supporting_objects"].get("evidence_objects", [])}
    evidence_assessments = {row["ref"]: row for row in data["supporting_objects"].get("evidence_assessments", [])}
    used_evidence: set[str] = set()
    expected_commitments = []
    attempts_by_ref = {row["ref"]: row for row in rows(data, "ValidationAttemptRevisionV0_1R2")}
    for attempt in rows(data, "ValidationAttemptRevisionV0_1R2"):
        payload = attempt["payload"]
        bindings = payload["evidence_bindings"]
        if bindings != sorted(bindings, key=lambda row: row["evidence_ref"]) or len({row["evidence_ref"] for row in bindings}) != len(bindings):
            errors.append(f"semantic: {attempt['key']} evidence set not sorted unique")
        for binding in bindings:
            evidence = evidence_objects.get(binding["evidence_ref"])
            assessment = evidence_assessments.get(binding["evidence_assessment_ref"])
            if evidence is None or assessment is None:
                errors.append(f"semantic: {attempt['key']} unresolved evidence/assessment")
                continue
            used_evidence.add(evidence["ref"])
            if (binding["evidence_fingerprint"], binding["evidence_revision"]) != (evidence["fingerprint"], evidence["payload"].get("evidence_revision")):
                errors.append(f"semantic: {attempt['key']} evidence tuple mismatch")
            ap = assessment["payload"]
            expected_assessment = {
                "assessment_id": ap.get("assessment_id"), "assessment_revision": 1,
                "barrier_fingerprint": barrier["fingerprint"], "barrier_ref": barrier["ref"],
                "is_current_head": True, "observed_event_sequence": payload["created_event_sequence"],
                "owner_contract_fingerprint": f3_contract["fingerprint"], "owner_contract_ref": f3_contract["ref"],
                "owner_contract_revision": f3_contract["payload"]["revision"], "owner_phase": "F3", "result": "EXACT_CURRENT",
                "subject_fingerprint": evidence["fingerprint"], "subject_ref": evidence["ref"],
                "subject_revision": evidence["payload"]["evidence_revision"],
            }
            if ap != expected_assessment or (binding["evidence_assessment_fingerprint"], binding["evidence_assessment_revision"]) != (assessment["fingerprint"], 1):
                errors.append(f"semantic: {attempt['key']} evidence owner assessment mismatch")
        expected_set_fp = R2V.typed_hash("agents-os.f6.r2.evidence-set", bindings)
        if payload["evidence_set_fingerprint"] != expected_set_fp:
            errors.append(f"semantic: {attempt['key']} evidence set fingerprint mismatch")
        aggregate = index.get(payload["evidence_assessment_ref"])
        if aggregate is None or aggregate["payload"].get("subject_payload") != {"evidence_bindings": bindings, "evidence_set_fingerprint": expected_set_fp}:
            errors.append(f"semantic: {attempt['key']} aggregate evidence assessment mismatch")
        item = {
            "attempt_fingerprint": attempt["fingerprint"], "attempt_ref": attempt["ref"],
            "attempt_revision": payload["attempt_revision"], "context_fingerprint": payload["context_binding"]["context_fingerprint"],
            "created_event_fingerprint": payload["created_event_fingerprint"], "created_event_ref": payload["created_event_ref"],
            "created_event_sequence": payload["created_event_sequence"], "evidence_set_fingerprint": payload["evidence_set_fingerprint"],
            "predecessor_fingerprint": payload["predecessor_fingerprint"], "predecessor_ref": payload["predecessor_ref"],
            "predecessor_revision": payload["predecessor_revision"],
        }
        item["commitment_fingerprint"] = binding_fingerprint("agents-os.f6.r3.attempt-commitment", item)
        expected_commitments.append(item)
        carry = payload["carry_source"]
        if carry is not None:
            source = attempts_by_ref.get(carry["source_attempt_ref"])
            root = attempts_by_ref.get(carry["root_source_attempt_ref"])
            if source is None or root is None or source is not root:
                errors.append("semantic: carry source/root do not resolve to one original attempt")
            else:
                source_tuple = (source["ref"], source["payload"]["attempt_revision"], source["fingerprint"])
                if (carry["source_attempt_ref"], carry["source_attempt_revision"], carry["source_attempt_fingerprint"]) != source_tuple or (carry["root_source_attempt_ref"], carry["root_source_attempt_revision"], carry["root_source_attempt_fingerprint"]) != source_tuple:
                    errors.append("semantic: carry ref/revision/fingerprint mismatch")
                if source["payload"]["method"] != "FRESH_VALIDATION" or source["payload"]["state"] != "PASSED" or source["payload"]["carry_source"] is not None or source["payload"]["requirement_id"] != payload["requirement_id"] or source["payload"]["requirement_revision"] != payload["requirement_revision"]:
                    errors.append("semantic: carry root is not the exact original PASSED source")
    expected_commitments.sort(key=lambda item: (item["attempt_ref"], item["attempt_revision"]))
    if outer["attempt_commitments"] != expected_commitments:
        errors.append("semantic: immutable attempt commitment inventory mismatch")
    if set(evidence_objects) != used_evidence:
        errors.append("semantic: evidence object inventory is not exact")

    for requirement in rows(data, "ValidationRequirementRevisionV0_1R2"):
        if not requirement["payload"]["effectful"]:
            continue
        matching = [row for row in rows(data, "ValidationAttemptRevisionV0_1R2") if row["payload"]["requirement_id"] == requirement["payload"]["requirement_id"]]
        for attempt in matching:
            assessment = index.get(attempt["payload"]["f5_assessment_ref"])
            delivery = index.get(requirement["payload"]["delivery_subject_ref"])
            if assessment is None or delivery is None:
                errors.append("semantic: effectful Requirement missing exact F5 support")
                continue
            ap = assessment["payload"]
            expected_subject = {"delivery_subject_fingerprint": delivery["fingerprint"], "delivery_subject_ref": delivery["ref"], "delivery_subject_revision": delivery["payload"]["subject_revision"], "status": "APPLIED_CURRENT"}
            if ap["subject_ref"] != delivery["ref"] or ap["subject_revision"] != delivery["payload"]["subject_revision"] or ap["subject_payload"] != expected_subject or ap["result"] != "APPLIED_CURRENT":
                errors.append("semantic: F5 assessment detached from exact delivery subject")


def validate_output_matrices(data: dict[str, Any], errors: list[str]) -> None:
    attempts = {row["ref"]: row for row in rows(data, "ValidationAttemptRevisionV0_1R2")}
    waivers = {row["ref"]: row for row in rows(data, "RequirementWaiverEventV0_1R2")}
    decision_rows = rows(data, "ValidationRequirementCurrentDecisionV0_1R2")
    for decision in decision_rows:
        payload = decision["payload"]
        if payload["result"] == "SATISFIED":
            valid = payload["attempt_head_ref"] in attempts and payload["attempt_head_fingerprint"] == attempts[payload["attempt_head_ref"]]["fingerprint"] and payload["context_fingerprint"] == attempts[payload["attempt_head_ref"]]["payload"]["context_binding"]["context_fingerprint"] and payload["waiver_head_ref"] is None and payload["waiver_head_fingerprint"] is None and payload["primary_reason"] == "VALIDATION_PASSED" and payload["reason_codes"] == ["VALIDATION_PASSED"]
        elif payload["result"] == "WAIVED":
            valid = payload["attempt_head_ref"] is None and payload["attempt_head_fingerprint"] is None and payload["context_fingerprint"] is None and payload["waiver_head_ref"] in waivers and payload["waiver_head_fingerprint"] == waivers[payload["waiver_head_ref"]]["fingerprint"] and payload["primary_reason"] == "CURRENT_WAIVER" and payload["reason_codes"] == ["CURRENT_WAIVER"]
        elif payload["result"] == "UNSATISFIED":
            valid = payload["attempt_head_ref"] is None and payload["attempt_head_fingerprint"] is None and payload["context_fingerprint"] is None and payload["waiver_head_ref"] is None and payload["waiver_head_fingerprint"] is None and payload["primary_reason"] == "NO_CURRENT_PASS" and payload["reason_codes"] == ["NO_CURRENT_PASS"]
        else:
            valid = False
        if not valid:
            errors.append(f"semantic: Requirement decision matrix contradiction: {payload['requirement_id']}")
    set_decision = rows(data, "ValidationSetCurrentDecisionV0_1R2")[0]
    expected_bindings = sorted([{"decision_fingerprint": row["fingerprint"], "decision_ref": row["ref"], "requirement_id": row["payload"]["requirement_id"]} for row in decision_rows], key=lambda row: row["requirement_id"])
    if set_decision["payload"]["requirement_decisions"] != expected_bindings or set_decision["payload"]["result"] != "SATISFIED" or any(row["payload"]["result"] not in {"SATISFIED", "WAIVED"} for row in decision_rows):
        errors.append("semantic: Validation Set decision matrix contradiction")
    completion = rows(data, "TaskCompletionEligibilityDecisionV0_1R2")[0]
    cp = completion["payload"]
    task = find_kind(data, "TASK_CURRENT_STATE")
    guard = find_kind(data, "COMPLETION_GUARD_CURRENTNESS")
    f5 = find_kind(data, "F5_COMPLETION_BLOCKING_CURRENTNESS")
    counts = cp["quiescence_counts"]
    valid_counts = isinstance(counts, dict) and set(counts) == set(QUIESCENCE_FIELDS) and all(type(counts[key]) is int and counts[key] == 0 for key in QUIESCENCE_FIELDS)
    valid = (
        cp["result"] == "ELIGIBLE" and cp["primary_reason"] == "ALL_COMPLETION_GATES_CURRENT"
        and cp["reason_codes"] == ["ALL_COMPLETION_GATES_CURRENT"]
        and task["payload"]["subject_payload"].get("task_lifecycle") == "VERIFYING"
        and task["payload"]["result"] == "CURRENT_VERIFYING"
        and guard["payload"]["subject_payload"].get("counts") == counts
        and guard["payload"]["result"] == "CURRENT_ZERO" and f5["payload"]["result"] == "CLEAR"
        and set_decision["payload"]["result"] == "SATISFIED" and valid_counts
    )
    if not valid:
        errors.append("semantic: completion cross-field matrix contradiction")


def validate_fixture(data: Any, *, execute_fixed: bool = False) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"R1_fixed": 0, "R1_independent": 0, "R2_additional": 0}
    if not exact_fields(data, TOP_FIELDS, "$", errors):
        return errors, counts
    check_tree(data, "$", errors)
    if data["schema_version"] != "agents-os.f6.validation-current-decision-r3-proof.v0.1" or data["environment"] != "SYNTHETIC_TEST" or data["runtime_usable"] is not False:
        errors.append("semantic: R3 synthetic boundary mismatch")
    unsigned = copy.deepcopy(data)
    root = unsigned.pop("root_fingerprint", None)
    if root != typed_hash("agents-os.f6.r3.root", unsigned):
        errors.append("integrity: R3 root fingerprint mismatch")
    if set(data["r2_bindings"]) != set(R2_PATHS):
        errors.append("integrity: R2 binding inventory mismatch")
    else:
        for key, path in R2_PATHS.items():
            binding = data["r2_bindings"][key]
            actual = hashlib.sha256((WORKSPACE_ROOT / path).read_bytes()).hexdigest()
            if binding != {"path": path, "sha256": actual}:
                errors.append(f"integrity: R2 binding mismatch: {key}")
    effective = data["effective_fixture"]
    r2_errors, _ = R2V.validate_fixture(effective, execute_r1=execute_fixed)
    errors.extend(f"R2 semantic: {error}" for error in r2_errors)
    if execute_fixed and not r2_errors:
        counts["R1_fixed"] = 32
        r1, r2, failures = R2V.run_mutations(effective)
        counts["R1_independent"] = r1
        counts["R2_additional"] = r2
        errors.extend(f"fixed regression: {failure}" for failure in failures)
        if (r1, r2) != (18, 12):
            errors.append(f"fixed regression counts {(r1, r2)} != (18, 12)")
    if isinstance(effective, dict) and "normative_objects" in effective:
        validate_profiles_and_values(effective, data["schema_constraint_profiles"], errors)
        validate_supporting_objects(effective, errors)
        validate_authority_and_context(effective, data, errors)
        validate_provenance_waiver_time(effective, data, errors)
        validate_evidence_carry_f5(effective, data, errors)
        validate_output_matrices(effective, errors)
    expected_occurrence = {
        "accepted_real_task_count": 0, "database_write_count": 0, "external_effect_count": 0,
        "provider_call_count": 0, "raw_secret_count": 0, "runtime_activation_count": 0,
        "task_done_mutation_count": 0, "terminal_outcome": "NOT_EXECUTED",
    }
    if data["occurrence_assertions"] != expected_occurrence:
        errors.append("semantic: zero-occurrence boundary mismatch")
    expected_catalog = {
        "R1_fixed_mutation_count": 32, "R1_independent_regression_count": 18,
        "R2_additional_negative_count": 12,
        "R2_independent_coordinated_probe_ids": [
            "IR-CONTEXT-01", "IR-WAIVER-01", "IR-REQ-GRAPH-01", "IR-REQ-GRAPH-02", "IR-REQ-GRAPH-03",
            "IR-PROVENANCE-01", "IR-EVIDENCE-01", "IR-EVIDENCE-02", "IR-EVIDENCE-03", "IR-EVIDENCE-04",
            "IR-CARRY-01", "IR-F5-01", "IR-MATRIX-01", "IR-SCHEMA-01", "IR-CONTEXT-02", "IR-TIME-01", "IR-OWNER-01",
        ],
    }
    if data["regression_catalog"] != expected_catalog:
        errors.append("integrity: regression catalog mismatch")
    summary = data["summary"]
    expected_summary = {
        "R1_fixed_mutation_count": 32, "R1_independent_regression_count": 18,
        "R2_additional_negative_count": 12, "R2_fixed_negative_total": 62,
        "R2_independent_coordinated_probe_count": 17,
        "attempt_commitment_count": len(rows(effective, "ValidationAttemptRevisionV0_1R2")),
        "context_binding_count": len(rows(effective, "ValidationAttemptRevisionV0_1R2")) + 1,
        "evidence_object_count": len(effective["supporting_objects"].get("evidence_objects", [])),
        "normative_schema_count": 10, "positive_graph_count": 3,
    }
    if summary != expected_summary:
        errors.append("integrity: summary mismatch")
    return errors, counts


def resign_outer(data: dict[str, Any]) -> None:
    unsigned = copy.deepcopy(data)
    unsigned.pop("root_fingerprint", None)
    data["root_fingerprint"] = typed_hash("agents-os.f6.r3.root", unsigned)


def refresh_assessment_subject(row: dict[str, Any]) -> None:
    payload = row["payload"]
    payload["subject_fingerprint"] = R2V.typed_hash(f"agents-os.f6.r2.assessment-subject.{payload['kind']}", payload["subject_payload"])


def sync_attempt_evidence(data: dict[str, Any], attempt: dict[str, Any]) -> None:
    payload = attempt["payload"]
    payload["evidence_set_fingerprint"] = R2V.typed_hash("agents-os.f6.r2.evidence-set", payload["evidence_bindings"])
    aggregate = next(row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2") if row["ref"] == payload["evidence_assessment_ref"])
    aggregate["payload"]["subject_payload"] = {"evidence_bindings": copy.deepcopy(payload["evidence_bindings"]), "evidence_set_fingerprint": payload["evidence_set_fingerprint"]}
    aggregate["payload"]["subject_revision"] = payload["attempt_revision"]
    refresh_assessment_subject(aggregate)


def coordinated_mutations() -> dict[str, Callable[[dict[str, Any]], None]]:
    def base(data: dict[str, Any]) -> dict[str, Any]:
        return data["effective_fixture"]

    def context_replace(data: dict[str, Any]) -> None:
        effective = base(data)
        candidate = {"ref": "synth:f6:r3:taskcandidate:alternate", "revision": 10, "fingerprint": "a" * 64}
        dependency = {"ref": "synth:f6:r3:dependencyclosure:alternate", "revision": 10, "fingerprint": "b" * 64}
        task = find_kind(effective, "TASK_CURRENT_STATE")
        task["payload"]["subject_payload"].update({"candidate_ref": candidate["ref"], "candidate_revision": 10, "candidate_fingerprint": candidate["fingerprint"], "dependency_ref": dependency["ref"], "dependency_revision": 10, "dependency_fingerprint": dependency["fingerprint"]})
        refresh_assessment_subject(task)
        for attempt in rows(effective, "ValidationAttemptRevisionV0_1R2"):
            attempt["payload"]["context_binding"]["candidate"] = copy.deepcopy(candidate)
            attempt["payload"]["context_binding"]["dependency"] = copy.deepcopy(dependency)
        completion = rows(effective, "TaskCompletionEligibilityDecisionV0_1R2")[0]["payload"]
        completion["candidate_context"] = copy.deepcopy(candidate); completion["dependency_context"] = copy.deepcopy(dependency)
        R2V.resign_all(effective); resign_outer(data)

    def waiver_substitution(data: dict[str, Any]) -> None:
        effective = base(data); index = wrapper_index(effective)
        decision = effective["supporting_objects"]["jenn_decisions"][0]
        waiver = rows(effective, "RequirementWaiverEventV0_1R2")[0]
        command = index[waiver["payload"]["command_ref"]]; event = index[waiver["payload"]["event_ref"]]
        authority = find_kind(effective, "JENN_WAIVER_AUTHORITY_CURRENTNESS")
        decision["payload"].update({"decision_id": "other", "requirement_id": "REQ-A", "requirement_revision": 2, "result": "CURRENT_ACCEPTED"}); R2V.reseal(decision)
        command["payload"].update({"command_id": "other", "purpose": "UNRELATED_OPERATION", "subject_fingerprint": "1" * 64}); R2V.reseal(command)
        event["payload"].update({"command_ref": command["ref"], "command_fingerprint": command["fingerprint"], "event_kind": "UNRELATED_EVENT", "subject_fingerprint": "2" * 64}); R2V.reseal(event)
        authority["payload"]["subject_ref"] = decision["ref"]
        authority["payload"]["subject_payload"].update({"decision_fingerprint": decision["fingerprint"], "decision_ref": decision["ref"], "command_fingerprint": command["fingerprint"], "command_ref": command["ref"], "event_fingerprint": event["fingerprint"], "event_ref": event["ref"]}); refresh_assessment_subject(authority)
        R2V.resign_all(effective); resign_outer(data)

    def branch(data: dict[str, Any]) -> None:
        effective = base(data); req = next(row for row in rows(effective, "ValidationRequirementRevisionV0_1R2") if row["payload"]["requirement_id"] == "REQ-A" and row["payload"]["requirement_revision"] == 2)
        duplicate = copy.deepcopy(req); duplicate["key"] = "REQ-A:r2:r3-branch"; R2V.reseal(duplicate); rows(effective, "ValidationRequirementRevisionV0_1R2").append(duplicate); R2V.resign_all(effective); resign_outer(data)
    def gap(data: dict[str, Any]) -> None:
        effective = base(data); rows(effective, "ValidationRequirementRevisionV0_1R2")[:] = [row for row in rows(effective, "ValidationRequirementRevisionV0_1R2") if not (row["payload"]["requirement_id"] == "REQ-A" and row["payload"]["requirement_revision"] == 1)]; R2V.resign_all(effective); resign_outer(data)
    def cycle(data: dict[str, Any]) -> None:
        effective = base(data); reqs = [row for row in rows(effective, "ValidationRequirementRevisionV0_1R2") if row["payload"]["requirement_id"] == "REQ-A"]
        r1 = next(row for row in reqs if row["payload"]["requirement_revision"] == 1); r2 = next(row for row in reqs if row["payload"]["requirement_revision"] == 2)
        r1["payload"].update({"predecessor_ref": r2["ref"], "predecessor_revision": 2, "predecessor_fingerprint": r2["fingerprint"]}); R2V.reseal(r1); R2V.resign_root(effective); resign_outer(data)
    def source_kind(data: dict[str, Any]) -> None:
        effective = base(data); source = effective["supporting_objects"]["provenance_sources"][0]; source["payload"]["source_kind"] = "ALIEN_SOURCE"; R2V.reseal(source)
        req = next(row for row in rows(effective, "ValidationRequirementRevisionV0_1R2") if any(item["source_ref"] == source["ref"] for item in row["payload"]["provenance_bindings"])); binding = next(item for item in req["payload"]["provenance_bindings"] if item["source_ref"] == source["ref"]); binding["source_kind"] = "ALIEN_SOURCE"; binding["source_fingerprint"] = source["fingerprint"]
        assessment = next(row for row in rows(effective, "OpaqueUpstreamAssessmentInputV0_1R2") if row["ref"] == binding["source_owner_assessment_ref"]); assessment["payload"]["subject_payload"].update({"source_kind": "ALIEN_SOURCE", "source_fingerprint": source["fingerprint"]}); refresh_assessment_subject(assessment); R2V.resign_all(effective); resign_outer(data)

    def evidence_change(mode: str) -> Callable[[dict[str, Any]], None]:
        def mutate(data: dict[str, Any]) -> None:
            effective = base(data); attempt = next(row for row in rows(effective, "ValidationAttemptRevisionV0_1R2") if row["key"] == "ATTEMPT-A:r1")
            if mode == "add":
                attempt["payload"]["evidence_bindings"].append({"evidence_assessment_fingerprint": "c" * 64, "evidence_assessment_ref": "synth:f6:r3:evidence-assessment:added", "evidence_assessment_revision": 1, "evidence_fingerprint": "b" * 64, "evidence_ref": "synth:f6:r3:evidence:added", "evidence_revision": 1}); attempt["payload"]["evidence_bindings"].sort(key=lambda row: row["evidence_ref"])
            elif mode == "delete": attempt["payload"]["evidence_bindings"] = attempt["payload"]["evidence_bindings"][1:]
            elif mode == "duplicate": attempt["payload"]["evidence_bindings"].append(copy.deepcopy(attempt["payload"]["evidence_bindings"][0])); attempt["payload"]["evidence_bindings"].sort(key=lambda row: row["evidence_ref"])
            else: attempt["payload"]["evidence_bindings"].reverse()
            sync_attempt_evidence(effective, attempt); R2V.resign_all(effective); resign_outer(data)
        return mutate
    def carry(data: dict[str, Any]) -> None:
        effective = base(data); attempt = next(row for row in rows(effective, "ValidationAttemptRevisionV0_1R2") if row["payload"]["method"] == "EVIDENCE_CARRY_FORWARD_REVIEW"); attempt["payload"]["carry_source"]["source_attempt_revision"] = 999; attempt["payload"]["carry_source"]["root_source_attempt_revision"] = 998; R2V.resign_all(effective); resign_outer(data)
    def f5(data: dict[str, Any]) -> None:
        effective = base(data); delivery = effective["supporting_objects"]["delivery_subjects"][0]; delivery["payload"]["subject_id"] = "alternate"; R2V.reseal(delivery); req = next(row for row in rows(effective, "ValidationRequirementRevisionV0_1R2") if row["payload"]["effectful"]); req["payload"]["delivery_subject_fingerprint"] = delivery["fingerprint"]; R2V.resign_all(effective); resign_outer(data)
    def matrix(data: dict[str, Any]) -> None:
        effective = base(data); waiver = rows(effective, "RequirementWaiverEventV0_1R2")[0]; decision = next(row for row in rows(effective, "ValidationRequirementCurrentDecisionV0_1R2") if row["payload"]["result"] == "SATISFIED"); decision["payload"]["waiver_head_ref"] = waiver["ref"]; decision["payload"]["waiver_head_fingerprint"] = waiver["fingerprint"]; R2V.resign_all(effective); resign_outer(data)
    def counts(data: dict[str, Any]) -> None:
        effective = base(data); guard = find_kind(effective, "COMPLETION_GUARD_CURRENTNESS"); guard["payload"]["subject_payload"]["counts"] = {}; refresh_assessment_subject(guard); rows(effective, "TaskCompletionEligibilityDecisionV0_1R2")[0]["payload"]["quiescence_counts"] = {}; R2V.resign_all(effective); resign_outer(data)
    def remove_dependency(data: dict[str, Any]) -> None:
        effective = base(data); rows(effective, "OpaqueUpstreamAssessmentInputV0_1R2")[:] = [row for row in rows(effective, "OpaqueUpstreamAssessmentInputV0_1R2") if row["payload"]["kind"] != "DEPENDENCY_CLOSURE_CURRENTNESS"]; R2V.resign_all(effective); resign_outer(data)
    def time_disconnect(data: dict[str, Any]) -> None:
        effective = base(data); trusted = rows(effective, "TrustedTimeInputV0_1R2")[0]; trusted["payload"].update({"barrier_ref": "synth:f6:r3:barrier:other", "barrier_fingerprint": "f" * 64, "observed_event_sequence": 999}); R2V.reseal(trusted); R2V.resign_root(effective); resign_outer(data)
    def owner(data: dict[str, Any]) -> None:
        effective = base(data); find_kind(effective, "VALIDATION_AUTHORITY_CURRENTNESS")["payload"]["owner_phase"] = "F1"; R2V.resign_all(effective); resign_outer(data)
    return {
        "IR-CONTEXT-01": context_replace, "IR-WAIVER-01": waiver_substitution,
        "IR-REQ-GRAPH-01": branch, "IR-REQ-GRAPH-02": gap, "IR-REQ-GRAPH-03": cycle,
        "IR-PROVENANCE-01": source_kind, "IR-EVIDENCE-01": evidence_change("add"),
        "IR-EVIDENCE-02": evidence_change("delete"), "IR-EVIDENCE-03": evidence_change("duplicate"),
        "IR-EVIDENCE-04": evidence_change("reorder"), "IR-CARRY-01": carry, "IR-F5-01": f5,
        "IR-MATRIX-01": matrix, "IR-SCHEMA-01": counts, "IR-CONTEXT-02": remove_dependency,
        "IR-TIME-01": time_disconnect, "IR-OWNER-01": owner,
    }


def run_coordinated_regressions(base: dict[str, Any]) -> tuple[int, int, list[str]]:
    rejected = 0
    exceptions = 0
    failures = []
    for case_id, mutate in coordinated_mutations().items():
        candidate = copy.deepcopy(base)
        try:
            mutate(candidate)
            errors, _ = validate_fixture(candidate, execute_fixed=False)
        except Exception as exc:
            exceptions += 1
            failures.append(f"{case_id}: exception {type(exc).__name__}: {exc}")
            continue
        if not errors:
            failures.append(f"{case_id}: incorrectly accepted")
        elif not any("semantic:" in error or "schema:" in error or "R2 semantic:" in error for error in errors):
            failures.append(f"{case_id}: rejected only outside semantic/schema layer")
        else:
            rejected += 1
    return rejected, exceptions, failures


def main() -> int:
    try:
        data = load_fixture(FIXTURE_PATH)
    except Exception as exc:
        print("result: BLOCK")
        print(f"load_error: {type(exc).__name__}: {exc}")
        return 1
    errors, counts = validate_fixture(data, execute_fixed=True)
    rejected, exceptions, failures = run_coordinated_regressions(data) if not errors else (0, 0, [])
    errors.extend(failures)
    if rejected != 17:
        errors.append(f"coordinated regression count {rejected} != 17")
    if exceptions != 0:
        errors.append(f"coordinated regression exception count {exceptions} != 0")
    if errors:
        print("result: BLOCK")
        for error in errors:
            print(f"error: {error}")
        return 1
    print("result: PASS_NO_BLOCKER")
    print("normative_schema_count: 10")
    print(f"normative_instance_count: {data['effective_fixture']['summary']['normative_instance_count']}")
    print("positive_graph_count: 3")
    print(f"R1_fixed_mutations_rejected: {counts['R1_fixed']}")
    print(f"R1_independent_regressions_rejected: {counts['R1_independent']}")
    print(f"R2_additional_negatives_rejected: {counts['R2_additional']}")
    print("fixed_negative_total_rejected: 62")
    print(f"R2_independent_coordinated_probes_rejected: {rejected}")
    print(f"mutation_exception_count: {exceptions}")
    print(f"fixture_canonical_sha256: {hashlib.sha256(canonical_bytes(data)).hexdigest()}")
    print("derived_satisfied_count: 3")
    print("derived_waived_count: 1")
    print("derived_completion_eligible_count: 1")
    for key, value in data["occurrence_assertions"].items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
