#!/usr/bin/env python3
"""Build the deterministic synthetic F6 R3 eight-finding closure witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    WORKSPACE_ROOT
    / "control-plane/registry/examples/2026-07-18-agents-os-f6-r3-eight-finding-semantic-closure-v0.1.json"
)
R2_BUILDER_PATH = WORKSPACE_ROOT / "control-plane/registry/build-f6-r2-ten-finding-proof-closure.py"
R2_VALIDATOR_PATH = WORKSPACE_ROOT / "control-plane/registry/validate-f6-r2-ten-finding-proof-closure.py"

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

PROVENANCE_KINDS = ["GOAL_DOMAIN_CONTRACT", "JENN_EXPLICIT", "NOBAO_TASK_SPEC", "RUST_POLICY"]
ASSESSMENT_KINDS = [
    "CANDIDATE_COMMITMENT_CURRENTNESS",
    "COMPLETION_GUARD_CURRENTNESS",
    "DEPENDENCY_CLOSURE_CURRENTNESS",
    "EVIDENCE_SET_CURRENTNESS",
    "F5_COMPLETION_BLOCKING_CURRENTNESS",
    "F5_DELIVERY_CURRENTNESS",
    "JENN_WAIVER_AUTHORITY_CURRENTNESS",
    "REQUIREMENT_PROVENANCE_CURRENTNESS",
    "TASK_CURRENT_STATE",
    "VALIDATION_AUTHORITY_CURRENTNESS",
]
QUIESCENCE_FIELDS = [
    "active_attempt_count", "active_effect_count", "open_command_count",
    "open_delivery_count", "pending_event_count",
]
ASSESSMENT_SUBJECT_FIELDS: dict[str, list[str]] = {
    "CANDIDATE_COMMITMENT_CURRENTNESS": ["candidate_id", "candidate_revision", "status"],
    "COMPLETION_GUARD_CURRENTNESS": ["counts", "guard_id", "guard_revision", "status"],
    "DEPENDENCY_CLOSURE_CURRENTNESS": ["dependency_id", "dependency_revision", "status"],
    "EVIDENCE_SET_CURRENTNESS": ["evidence_bindings", "evidence_set_fingerprint"],
    "F5_COMPLETION_BLOCKING_CURRENTNESS": ["result_id", "result_revision", "status"],
    "F5_DELIVERY_CURRENTNESS": ["delivery_subject_fingerprint", "delivery_subject_ref", "delivery_subject_revision", "status"],
    "JENN_WAIVER_AUTHORITY_CURRENTNESS": [
        "command_fingerprint", "command_ref", "decision_fingerprint", "decision_ref",
        "decision_revision", "event_fingerprint", "event_ref", "event_sequence",
        "requirement_id", "requirement_revision",
    ],
    "REQUIREMENT_PROVENANCE_CURRENTNESS": [
        "command_fingerprint", "command_ref", "event_fingerprint", "event_ref",
        "event_sequence", "source_fingerprint", "source_kind", "source_ref", "source_revision",
    ],
    "TASK_CURRENT_STATE": [
        "candidate_fingerprint", "candidate_ref", "candidate_revision",
        "dependency_fingerprint", "dependency_ref", "dependency_revision",
        "task_id", "task_lifecycle", "task_revision", "task_state_revision",
    ],
    "VALIDATION_AUTHORITY_CURRENTNESS": [
        "requirement_id", "requirement_revision", "validator_contract_fingerprint",
        "validator_contract_ref", "validator_contract_revision",
    ],
}

NESTED_FIELDS: dict[str, list[str]] = {
    "CARRY_SOURCE": [
        "root_source_attempt_fingerprint", "root_source_attempt_ref",
        "root_source_attempt_revision", "source_attempt_fingerprint",
        "source_attempt_ref", "source_attempt_revision",
    ],
    "DECISION_BINDING": ["decision_fingerprint", "decision_ref", "requirement_id"],
    "EVIDENCE_BINDING_R3": [
        "evidence_assessment_fingerprint", "evidence_assessment_ref",
        "evidence_assessment_revision", "evidence_fingerprint", "evidence_ref",
        "evidence_revision",
    ],
    "MEMBERSHIP": [
        "requirement_fingerprint", "requirement_id", "requirement_ref",
        "requirement_revision",
    ],
    "PROVENANCE_BINDING": [
        "creation_command_fingerprint", "creation_command_ref",
        "creation_event_fingerprint", "creation_event_ref",
        "creation_event_sequence", "source_fingerprint", "source_kind",
        "source_owner_assessment_fingerprint", "source_owner_assessment_ref",
        "source_owner_assessment_revision", "source_ref", "source_revision",
    ],
    "QUIESCENCE_COUNTS": QUIESCENCE_FIELDS,
    "SUBJECT_TUPLE": ["fingerprint", "ref", "revision"],
    "VALIDATION_CONTEXT": [
        "candidate", "context_fingerprint", "dependency", "evidence_set_fingerprint",
        "requirement_fingerprint", "requirement_id", "requirement_revision",
        "set_fingerprint", "set_ref", "set_revision",
        "validator_contract_fingerprint", "validator_contract_ref",
        "validator_contract_revision",
    ],
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
    ("ValidationRequirementRevisionV0_1R2", field)
    for field in [
        "delivery_subject_fingerprint", "delivery_subject_ref", "delivery_subject_revision",
        "predecessor_fingerprint", "predecessor_ref", "predecessor_revision",
    ]
} | {
    ("RequirementWaiverEventV0_1R2", field)
    for field in ["predecessor_fingerprint", "predecessor_ref", "predecessor_revision"]
} | {
    ("ValidationSetSnapshotV0_1R2", field)
    for field in ["predecessor_fingerprint", "predecessor_ref", "predecessor_revision"]
} | {
    ("ValidationAttemptRevisionV0_1R2", field)
    for field in [
        "carry_source", "f5_assessment_fingerprint", "f5_assessment_ref",
        "f5_assessment_revision", "predecessor_fingerprint", "predecessor_ref",
        "predecessor_revision",
    ]
} | {
    ("ValidationRequirementCurrentDecisionV0_1R2", field)
    for field in [
        "attempt_head_fingerprint", "attempt_head_ref", "context_fingerprint",
        "waiver_head_fingerprint", "waiver_head_ref",
    ]
}

ENUMS: dict[tuple[str, str], list[str]] = {
    ("F3CanonicalReadBarrierInputV0_1R2", "domain"): ["SYNTHETIC_TEST"],
    ("F3CanonicalReadBarrierInputV0_1R2", "environment"): ["SYNTHETIC_TEST"],
    ("OpaqueUpstreamAssessmentInputV0_1R2", "kind"): ASSESSMENT_KINDS,
    ("OpaqueUpstreamAssessmentInputV0_1R2", "owner_phase"): ["F1", "F3", "F5"],
    ("OpaqueUpstreamAssessmentInputV0_1R2", "result"): [
        "APPLIED_CURRENT", "CLEAR", "CURRENT", "CURRENT_ACCEPTED",
        "CURRENT_CONFIRMED", "CURRENT_VERIFYING", "CURRENT_ZERO",
        "EXACT_CURRENT",
    ],
    ("ValidationRequirementRevisionV0_1R2", "waivability"): ["NON_WAIVABLE", "WAIVABLE"],
    ("RequirementWaiverEventV0_1R2", "operation"): ["EXPIRE", "GRANT", "INVALIDATE", "REVOKE"],
    ("ValidationSetSnapshotV0_1R2", "change_kind"): ["BASE", "WAIVER_CHANGE"],
    ("ValidationAttemptRevisionV0_1R2", "method"): ["EVIDENCE_CARRY_FORWARD_REVIEW", "FRESH_VALIDATION"],
    ("ValidationAttemptRevisionV0_1R2", "state"): ["FAILED", "PASSED", "PENDING"],
    ("ValidationRequirementCurrentDecisionV0_1R2", "result"): [
        "INDETERMINATE", "NOT_REQUIRED", "PENDING", "SATISFIED", "UNSATISFIED", "WAIVED",
    ],
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


R2B = load_module("f6_r2_builder_for_r3", R2_BUILDER_PATH)
R2V = load_module("f6_r2_validator_for_r3", R2_VALIDATOR_PATH)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def typed_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def file_hash(path: str) -> str:
    return hashlib.sha256((WORKSPACE_ROOT / path).read_bytes()).hexdigest()


def rows(data: dict[str, Any], schema: str) -> list[dict[str, Any]]:
    return data["normative_objects"][schema]


def find_assessment(data: dict[str, Any], kind: str, *, subject_ref: str | None = None) -> dict[str, Any]:
    matches = [row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2") if row["payload"]["kind"] == kind]
    if subject_ref is not None:
        matches = [row for row in matches if row["payload"]["subject_ref"] == subject_ref]
    if len(matches) != 1:
        raise RuntimeError(f"expected one assessment for {kind}/{subject_ref}, got {len(matches)}")
    return matches[0]


def refresh_assessment(row: dict[str, Any]) -> None:
    payload = row["payload"]
    payload["subject_fingerprint"] = R2V.typed_hash(
        f"agents-os.f6.r2.assessment-subject.{payload['kind']}", payload["subject_payload"]
    )
    R2V.reseal(row)


def close_provenance(data: dict[str, Any]) -> None:
    index = R2V.wrapper_index(data)
    for source in data["supporting_objects"]["provenance_sources"]:
        source["payload"]["source_kind"] = "NOBAO_TASK_SPEC"
        R2V.reseal(source)
        requirement = next(
            row for row in rows(data, "ValidationRequirementRevisionV0_1R2")
            if any(binding["source_ref"] == source["ref"] for binding in row["payload"]["provenance_bindings"])
        )
        binding = next(item for item in requirement["payload"]["provenance_bindings"] if item["source_ref"] == source["ref"])
        command = index[binding["creation_command_ref"]]
        event = index[binding["creation_event_ref"]]
        natural = {
            "requirement_id": requirement["payload"]["requirement_id"],
            "requirement_revision": requirement["payload"]["requirement_revision"],
            "source_fingerprint": source["fingerprint"],
            "source_ref": source["ref"],
        }
        command["payload"]["purpose"] = "CREATE_OR_REVISE_REQUIREMENT"
        command["payload"]["subject_fingerprint"] = R2V.typed_hash("agents-os.f6.r2.command-subject", natural)
        R2V.reseal(command)
        event["payload"]["command_ref"] = command["ref"]
        event["payload"]["command_fingerprint"] = command["fingerprint"]
        event["payload"]["event_kind"] = "REQUIREMENT_COMMITTED"
        event["payload"]["subject_fingerprint"] = R2V.typed_hash("agents-os.f6.r2.event-subject", natural)
        R2V.reseal(event)
        binding.update({
            "creation_command_fingerprint": command["fingerprint"],
            "creation_event_fingerprint": event["fingerprint"],
            "creation_event_sequence": event["payload"]["event_sequence"],
            "source_fingerprint": source["fingerprint"],
            "source_kind": "NOBAO_TASK_SPEC",
        })
        assessment = index[binding["source_owner_assessment_ref"]]
        assessment["payload"]["subject_payload"].update({
            "command_fingerprint": command["fingerprint"], "command_ref": command["ref"],
            "event_fingerprint": event["fingerprint"], "event_ref": event["ref"],
            "event_sequence": event["payload"]["event_sequence"],
            "source_fingerprint": source["fingerprint"], "source_kind": "NOBAO_TASK_SPEC",
            "source_ref": source["ref"], "source_revision": source["payload"]["source_revision"],
        })
        refresh_assessment(assessment)


def close_waiver_root(data: dict[str, Any]) -> None:
    decision = data["supporting_objects"]["jenn_decisions"][0]
    decision["payload"]["decision_event_sequence"] = 112
    R2V.reseal(decision)
    command = next(row for row in data["supporting_objects"]["commands"] if row["key"] == "waiver:req-d")
    event = next(row for row in data["supporting_objects"]["events"] if row["key"] == "waiver:req-d")
    natural = {
        "decision_fingerprint": decision["fingerprint"], "decision_ref": decision["ref"],
        "decision_revision": decision["payload"]["decision_revision"],
        "requirement_id": decision["payload"]["requirement_id"],
        "requirement_revision": decision["payload"]["requirement_revision"],
    }
    command["payload"]["purpose"] = "GRANT_REQUIREMENT_WAIVER"
    command["payload"]["subject_fingerprint"] = R2V.typed_hash("agents-os.f6.r2.command-subject", natural)
    R2V.reseal(command)
    event["payload"].update({
        "command_ref": command["ref"], "command_fingerprint": command["fingerprint"],
        "event_kind": "WAIVER_COMMITTED",
        "subject_fingerprint": R2V.typed_hash("agents-os.f6.r2.event-subject", natural),
    })
    R2V.reseal(event)
    authority = find_assessment(data, "JENN_WAIVER_AUTHORITY_CURRENTNESS")
    authority["payload"]["subject_ref"] = decision["ref"]
    authority["payload"]["subject_revision"] = decision["payload"]["decision_revision"]
    authority["payload"]["subject_payload"] = {
        "command_fingerprint": command["fingerprint"], "command_ref": command["ref"],
        "decision_fingerprint": decision["fingerprint"], "decision_ref": decision["ref"],
        "decision_revision": decision["payload"]["decision_revision"],
        "event_fingerprint": event["fingerprint"], "event_ref": event["ref"],
        "event_sequence": event["payload"]["event_sequence"],
        "requirement_id": "REQ-D", "requirement_revision": 1,
    }
    refresh_assessment(authority)


def close_evidence(data: dict[str, Any]) -> None:
    barrier = rows(data, "F3CanonicalReadBarrierInputV0_1R2")[0]
    f3_contract = next(row for row in data["supporting_objects"]["owner_contracts"] if row["payload"]["owner_phase"] == "F3")
    evidence_objects: dict[tuple[str, str], dict[str, Any]] = {}
    evidence_assessments: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for attempt in rows(data, "ValidationAttemptRevisionV0_1R2"):
        converted: list[dict[str, Any]] = []
        for number, old in enumerate(attempt["payload"]["evidence_bindings"], start=1):
            identity = (old["evidence_ref"], old["evidence_fingerprint"])
            if identity not in evidence_objects:
                key = f"{attempt['payload']['attempt_id'].lower()}:{number}"
                evidence = R2B.support("EvidenceObject", key, {
                    "environment": "SYNTHETIC_TEST", "evidence_id": f"evidence:{key}",
                    "evidence_revision": old["evidence_revision"],
                    "validation_subject": attempt["payload"]["requirement_id"],
                })
                evidence_objects[identity] = evidence
            evidence = evidence_objects[identity]
            assessment_identity = (
                identity[0], identity[1], attempt["payload"]["attempt_id"],
                attempt["payload"]["attempt_revision"],
            )
            if assessment_identity not in evidence_assessments:
                assessment_key = (
                    f"{attempt['payload']['attempt_id'].lower()}:r"
                    f"{attempt['payload']['attempt_revision']}:{number}"
                )
                assessment = R2B.support("EvidenceAssessment", assessment_key, {
                    "assessment_id": f"evidence-assessment:{assessment_key}", "assessment_revision": 1,
                    "barrier_fingerprint": barrier["fingerprint"], "barrier_ref": barrier["ref"],
                    "is_current_head": True,
                    "observed_event_sequence": attempt["payload"]["created_event_sequence"],
                    "owner_contract_fingerprint": f3_contract["fingerprint"],
                    "owner_contract_ref": f3_contract["ref"],
                    "owner_contract_revision": f3_contract["payload"]["revision"],
                    "owner_phase": "F3", "result": "EXACT_CURRENT",
                    "subject_fingerprint": evidence["fingerprint"], "subject_ref": evidence["ref"],
                    "subject_revision": evidence["payload"]["evidence_revision"],
                })
                evidence_assessments[assessment_identity] = assessment
            assessment = evidence_assessments[assessment_identity]
            converted.append({
                "evidence_assessment_fingerprint": assessment["fingerprint"],
                "evidence_assessment_ref": assessment["ref"],
                "evidence_assessment_revision": assessment["payload"]["assessment_revision"],
                "evidence_fingerprint": evidence["fingerprint"], "evidence_ref": evidence["ref"],
                "evidence_revision": evidence["payload"]["evidence_revision"],
            })
        converted.sort(key=lambda row: row["evidence_ref"])
        attempt["payload"]["evidence_bindings"] = converted
        attempt["payload"]["evidence_set_fingerprint"] = R2V.typed_hash("agents-os.f6.r2.evidence-set", converted)
        aggregate = next(
            row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2")
            if row["ref"] == attempt["payload"]["evidence_assessment_ref"]
        )
        aggregate["payload"]["subject_payload"] = {
            "evidence_bindings": copy.deepcopy(converted),
            "evidence_set_fingerprint": attempt["payload"]["evidence_set_fingerprint"],
        }
        aggregate["payload"]["subject_revision"] = attempt["payload"]["attempt_revision"]
        refresh_assessment(aggregate)
    data["supporting_objects"]["evidence_objects"] = sorted(evidence_objects.values(), key=lambda row: row["ref"])
    data["supporting_objects"]["evidence_assessments"] = sorted(evidence_assessments.values(), key=lambda row: row["ref"])


def close_set_events(data: dict[str, Any]) -> None:
    index = R2V.wrapper_index(data)
    for snapshot in rows(data, "ValidationSetSnapshotV0_1R2"):
        event = index[snapshot["payload"]["freeze_event_ref"]]
        command = index[event["payload"]["command_ref"]]
        natural = {
            "set_id": snapshot["payload"]["set_id"],
            "revision": snapshot["payload"]["set_revision"],
        }
        if snapshot["payload"]["waiver_heads"]:
            natural["waiver"] = snapshot["payload"]["waiver_heads"][0]["waiver_fingerprint"]
        command["payload"]["purpose"] = "FREEZE_VALIDATION_SET"
        command["payload"]["subject_fingerprint"] = R2V.typed_hash("agents-os.f6.r2.command-subject", natural)
        R2V.reseal(command)
        event["payload"].update({
            "command_fingerprint": command["fingerprint"], "command_ref": command["ref"],
            "event_kind": "VALIDATION_SET_FROZEN",
            "subject_fingerprint": R2V.typed_hash("agents-os.f6.r2.event-subject", natural),
        })
        R2V.reseal(event)


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


def close_attempt_events(data: dict[str, Any]) -> None:
    ordered = sorted(
        rows(data, "ValidationAttemptRevisionV0_1R2"),
        key=lambda row: (row["payload"]["attempt_id"], row["payload"]["attempt_revision"]),
    )
    for attempt in ordered:
        index = R2V.wrapper_index(data)
        event = index[attempt["payload"]["created_event_ref"]]
        command = index[event["payload"]["command_ref"]]
        natural = attempt_event_subject(attempt)
        command["payload"]["purpose"] = "COMMIT_VALIDATION_ATTEMPT"
        command["payload"]["subject_fingerprint"] = R2V.typed_hash("agents-os.f6.r2.command-subject", natural)
        R2V.reseal(command)
        event["payload"].update({
            "command_fingerprint": command["fingerprint"], "command_ref": command["ref"],
            "event_kind": "VALIDATION_ATTEMPT_COMMITTED",
            "subject_fingerprint": R2V.typed_hash("agents-os.f6.r2.event-subject", natural),
        })
        R2V.reseal(event)
        R2V.resign_all(data)


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


def field_constraint(schema: str, field: str, value: Any) -> dict[str, Any]:
    nested = SCHEMA_NESTED.get((schema, field))
    kind = ("array" if (schema, field) in NESTED_ARRAY_FIELDS else "object") if nested else value_kind(field, value)
    return {
        "allowed_values": ENUMS.get((schema, field)),
        "integer_max": (2**53 - 1) if kind in {"positive_safe_integer", "non_negative_safe_integer"} else None,
        "integer_min": 1 if kind == "positive_safe_integer" else (0 if kind == "non_negative_safe_integer" else None),
        "nested_profile": nested,
        "nullable": (schema, field) in NULLABLE_FIELDS,
        "value_kind": kind,
    }


def nested_profiles_for(schema: str, data: dict[str, Any]) -> list[dict[str, Any]]:
    names = sorted({name for (owner, _field), name in SCHEMA_NESTED.items() if owner == schema})
    if schema == "OpaqueUpstreamAssessmentInputV0_1R2":
        names = sorted(set(names) | {"EVIDENCE_BINDING_R3", "QUIESCENCE_COUNTS"})
    if "VALIDATION_CONTEXT" in names:
        names = sorted(set(names) | {"SUBJECT_TUPLE"})
    profiles: list[dict[str, Any]] = []
    for name in names:
        if name == "ASSESSMENT_SUBJECT_BY_KIND":
            fields: list[str] = []
            constraints: dict[str, Any] = {}
            variants = []
            assessments = rows(data, "OpaqueUpstreamAssessmentInputV0_1R2")
            for kind in sorted(ASSESSMENT_SUBJECT_FIELDS):
                instance = next(row["payload"]["subject_payload"] for row in assessments if row["payload"]["kind"] == kind)
                variant = {
                    "assessment_kind": kind,
                    "closed_fields": ASSESSMENT_SUBJECT_FIELDS[kind],
                    "field_constraints": {
                        field: field_constraint(kind, field, instance[field])
                        for field in ASSESSMENT_SUBJECT_FIELDS[kind]
                    },
                }
                variant["variant_fingerprint"] = typed_hash("agents-os.f6.r3.assessment-subject-profile", variant)
                variants.append(variant)
        else:
            fields = NESTED_FIELDS[name]
            constraints = {
                field: field_constraint(name, field, None if field.startswith("predecessor_") else "sample")
                for field in fields
            }
            for field in fields:
                if field in {"candidate", "dependency"}:
                    constraints[field]["value_kind"] = "object"
                    constraints[field]["nested_profile"] = "SUBJECT_TUPLE"
                if field in QUIESCENCE_FIELDS:
                    constraints[field].update({"value_kind": "non_negative_safe_integer", "nullable": False, "integer_min": 0, "integer_max": 2**53 - 1})
            variants = []
        unsigned = {"closed_fields": fields, "field_constraints": constraints, "profile_name": name, "variants": variants}
        profiles.append({**unsigned, "profile_fingerprint": typed_hash("agents-os.f6.r3.nested-profile", unsigned)})
    return profiles


def build_profiles(data: dict[str, Any]) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    for schema in sorted(R2V.SCHEMA_FIELDS):
        instance = rows(data, schema)[0]
        constraints = {
            field: field_constraint(schema, field, instance["payload"][field])
            for field in R2V.SCHEMA_FIELDS[schema]
        }
        profile = {
            "canonical_instance_fingerprint": instance["fingerprint"],
            "canonical_instance_ref": instance["ref"],
            "closed_fields": R2V.SCHEMA_FIELDS[schema],
            "cross_field_rules": [f"R3-{schema}-TOTAL-MATRIX"],
            "field_constraints": constraints,
            "nested_profiles": nested_profiles_for(schema, data),
            "schema_name": schema,
            "schema_revision": 3,
        }
        profile["schema_fingerprint"] = typed_hash("agents-os.f6.r3.schema-profile", profile)
        profiles.append(profile)
    return profiles


def binding_fingerprint(domain: str, row: dict[str, Any]) -> str:
    unsigned = dict(row)
    unsigned.pop("binding_fingerprint", None)
    unsigned.pop("commitment_fingerprint", None)
    unsigned.pop("edge_fingerprint", None)
    return typed_hash(domain, unsigned)


def build_authority_roots(data: dict[str, Any]) -> list[dict[str, Any]]:
    contracts = {row["payload"]["owner_phase"]: row for row in data["supporting_objects"]["owner_contracts"]}
    owners = {
        "CANDIDATE_COMMITMENT_CURRENTNESS": "F1", "DEPENDENCY_CLOSURE_CURRENTNESS": "F1",
        "TASK_CURRENT_STATE": "F1", "COMPLETION_GUARD_CURRENTNESS": "F3",
        "EVIDENCE_SET_CURRENTNESS": "F3", "JENN_WAIVER_AUTHORITY_CURRENTNESS": "F3",
        "REQUIREMENT_PROVENANCE_CURRENTNESS": "F3", "VALIDATION_AUTHORITY_CURRENTNESS": "F3",
        "F5_COMPLETION_BLOCKING_CURRENTNESS": "F5", "F5_DELIVERY_CURRENTNESS": "F5",
    }
    result = []
    for kind in sorted(owners):
        contract = contracts[owners[kind]]
        row = {
            "assessment_kind": kind, "owner_phase": owners[kind],
            "owner_contract_ref": contract["ref"],
            "owner_contract_revision": contract["payload"]["revision"],
            "owner_contract_fingerprint": contract["fingerprint"],
        }
        row["binding_fingerprint"] = binding_fingerprint("agents-os.f6.r3.authority-root", row)
        result.append(row)
    return result


def build_context_bindings(data: dict[str, Any]) -> list[dict[str, Any]]:
    candidate = find_assessment(data, "CANDIDATE_COMMITMENT_CURRENTNESS")
    dependency = find_assessment(data, "DEPENDENCY_CLOSURE_CURRENTNESS")
    consumers = rows(data, "ValidationAttemptRevisionV0_1R2") + rows(data, "TaskCompletionEligibilityDecisionV0_1R2")
    result = []
    for consumer in consumers:
        revision = consumer["payload"].get("attempt_revision", 1)
        row = {
            "candidate_assessment_fingerprint": candidate["fingerprint"],
            "candidate_assessment_ref": candidate["ref"],
            "candidate_assessment_revision": candidate["payload"]["assessment_revision"],
            "consumer_fingerprint": consumer["fingerprint"], "consumer_ref": consumer["ref"],
            "consumer_revision": revision,
            "dependency_assessment_fingerprint": dependency["fingerprint"],
            "dependency_assessment_ref": dependency["ref"],
            "dependency_assessment_revision": dependency["payload"]["assessment_revision"],
        }
        row["binding_fingerprint"] = binding_fingerprint("agents-os.f6.r3.context-assessment-binding", row)
        result.append(row)
    return sorted(result, key=lambda row: row["consumer_ref"])


def build_attempt_commitments(data: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for attempt in rows(data, "ValidationAttemptRevisionV0_1R2"):
        payload = attempt["payload"]
        row = {
            "attempt_fingerprint": attempt["fingerprint"], "attempt_ref": attempt["ref"],
            "attempt_revision": payload["attempt_revision"],
            "context_fingerprint": payload["context_binding"]["context_fingerprint"],
            "created_event_fingerprint": payload["created_event_fingerprint"],
            "created_event_ref": payload["created_event_ref"],
            "created_event_sequence": payload["created_event_sequence"],
            "evidence_set_fingerprint": payload["evidence_set_fingerprint"],
            "predecessor_fingerprint": payload["predecessor_fingerprint"],
            "predecessor_ref": payload["predecessor_ref"],
            "predecessor_revision": payload["predecessor_revision"],
        }
        row["commitment_fingerprint"] = binding_fingerprint("agents-os.f6.r3.attempt-commitment", row)
        result.append(row)
    return sorted(result, key=lambda row: (row["attempt_ref"], row["attempt_revision"]))


def edge(from_ref: str, from_sequence: int, to_ref: str, to_sequence: int, relation: str, purpose: str) -> dict[str, Any]:
    row = {
        "from_ref": from_ref, "from_sequence": from_sequence, "purpose": purpose,
        "relation": relation, "to_ref": to_ref, "to_sequence": to_sequence,
    }
    row["edge_fingerprint"] = binding_fingerprint("agents-os.f6.r3.event-order-edge", row)
    return row


def build_event_edges(data: dict[str, Any]) -> list[dict[str, Any]]:
    index = R2V.wrapper_index(data)
    result: list[dict[str, Any]] = []
    requirements = rows(data, "ValidationRequirementRevisionV0_1R2")
    for req in requirements:
        payload = req["payload"]
        if payload["predecessor_ref"] is not None:
            predecessor = index[payload["predecessor_ref"]]
            result.append(edge(
                predecessor["payload"]["creation_event_ref"], predecessor["payload"]["creation_event_sequence"],
                payload["creation_event_ref"], payload["creation_event_sequence"], "LT", "REQUIREMENT_PREDECESSOR",
            ))
    for snapshot in rows(data, "ValidationSetSnapshotV0_1R2"):
        for member in snapshot["payload"]["memberships"]:
            req = index[member["requirement_ref"]]
            result.append(edge(
                req["payload"]["creation_event_ref"], req["payload"]["creation_event_sequence"],
                snapshot["payload"]["freeze_event_ref"], snapshot["payload"]["frozen_event_sequence"],
                "LE", "REQUIREMENT_IN_SNAPSHOT",
            ))
    snapshots = sorted(rows(data, "ValidationSetSnapshotV0_1R2"), key=lambda row: row["payload"]["set_revision"])
    base, current = snapshots
    decision = data["supporting_objects"]["jenn_decisions"][0]
    waiver = rows(data, "RequirementWaiverEventV0_1R2")[0]
    result.extend([
        edge(base["payload"]["freeze_event_ref"], base["payload"]["frozen_event_sequence"], decision["ref"], decision["payload"]["decision_event_sequence"], "LT", "BASE_BEFORE_JENN_DECISION"),
        edge(decision["ref"], decision["payload"]["decision_event_sequence"], waiver["payload"]["event_ref"], waiver["payload"]["event_sequence"], "LE", "JENN_DECISION_BEFORE_WAIVER"),
        edge(waiver["payload"]["event_ref"], waiver["payload"]["event_sequence"], current["payload"]["freeze_event_ref"], current["payload"]["frozen_event_sequence"], "LE", "WAIVER_BEFORE_CONSUMING_SNAPSHOT"),
    ])
    assessment_index = {row["ref"]: row for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2")}
    trusted = rows(data, "TrustedTimeInputV0_1R2")[0]
    barrier = rows(data, "F3CanonicalReadBarrierInputV0_1R2")[0]
    for attempt in rows(data, "ValidationAttemptRevisionV0_1R2"):
        aggregate = assessment_index[attempt["payload"]["evidence_assessment_ref"]]
        result.extend([
            edge(current["payload"]["freeze_event_ref"], current["payload"]["frozen_event_sequence"], attempt["payload"]["created_event_ref"], attempt["payload"]["created_event_sequence"], "LE", "SNAPSHOT_BEFORE_ATTEMPT"),
            edge(attempt["payload"]["created_event_ref"], attempt["payload"]["created_event_sequence"], aggregate["ref"], aggregate["payload"]["observed_event_sequence"], "LE", "ATTEMPT_BEFORE_EVIDENCE_ASSESSMENT"),
        ])
    result.extend([
        edge("synth:f6:r3:all-assessments", max(row["payload"]["observed_event_sequence"] for row in rows(data, "OpaqueUpstreamAssessmentInputV0_1R2")), trusted["ref"], trusted["payload"]["observed_event_sequence"], "LE", "ASSESSMENTS_BEFORE_TRUSTED_EVALUATION"),
        edge(trusted["ref"], trusted["payload"]["observed_event_sequence"], barrier["ref"], barrier["payload"]["end_event_sequence"], "LE", "TRUSTED_EVALUATION_WITHIN_BARRIER"),
    ])
    return sorted(result, key=lambda row: (row["purpose"], row["from_ref"], row["to_ref"]))


def build_fixture() -> dict[str, Any]:
    effective = R2B.build_fixture()
    close_provenance(effective)
    close_waiver_root(effective)
    close_evidence(effective)
    R2V.resign_all(effective)
    close_set_events(effective)
    R2V.resign_all(effective)
    close_attempt_events(effective)
    errors, _ = R2V.validate_fixture(effective, execute_r1=False)
    if errors:
        raise RuntimeError("R3 effective R2 graph invalid: " + "; ".join(errors[:10]))
    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f6.validation-current-decision-r3-proof.v0.1",
        "environment": "SYNTHETIC_TEST", "runtime_usable": False,
        "r2_bindings": {key: {"path": path, "sha256": file_hash(path)} for key, path in R2_PATHS.items()},
        "effective_fixture": effective,
        "schema_constraint_profiles": build_profiles(effective),
        "authority_root_bindings": build_authority_roots(effective),
        "context_assessment_bindings": build_context_bindings(effective),
        "attempt_commitments": build_attempt_commitments(effective),
        "event_order_edges": build_event_edges(effective),
        "regression_catalog": {
            "R1_fixed_mutation_count": 32, "R1_independent_regression_count": 18,
            "R2_additional_negative_count": 12,
            "R2_independent_coordinated_probe_ids": [
                "IR-CONTEXT-01", "IR-WAIVER-01", "IR-REQ-GRAPH-01", "IR-REQ-GRAPH-02",
                "IR-REQ-GRAPH-03", "IR-PROVENANCE-01", "IR-EVIDENCE-01", "IR-EVIDENCE-02",
                "IR-EVIDENCE-03", "IR-EVIDENCE-04", "IR-CARRY-01", "IR-F5-01",
                "IR-MATRIX-01", "IR-SCHEMA-01", "IR-CONTEXT-02", "IR-TIME-01", "IR-OWNER-01",
            ],
        },
        "occurrence_assertions": copy.deepcopy(effective["occurrence_assertions"]),
        "summary": {
            "R1_fixed_mutation_count": 32, "R1_independent_regression_count": 18,
            "R2_additional_negative_count": 12, "R2_fixed_negative_total": 62,
            "R2_independent_coordinated_probe_count": 17,
            "attempt_commitment_count": len(rows(effective, "ValidationAttemptRevisionV0_1R2")),
            "context_binding_count": len(rows(effective, "ValidationAttemptRevisionV0_1R2")) + 1,
            "evidence_object_count": len(effective["supporting_objects"]["evidence_objects"]),
            "normative_schema_count": len(R2V.SCHEMA_FIELDS), "positive_graph_count": 3,
        },
    }
    fixture["root_fingerprint"] = typed_hash("agents-os.f6.r3.root", fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = canonical_bytes(build_fixture())
    args.output.write_bytes(data)
    print(f"output: {args.output}")
    print(f"bytes: {len(data)}")
    print(f"sha256: {hashlib.sha256(data).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
