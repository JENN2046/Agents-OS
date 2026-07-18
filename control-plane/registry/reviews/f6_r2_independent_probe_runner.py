#!/usr/bin/env python3
"""Independent coordinated semantic probes for the fixed F6 R2 review package.

The validator's resign_all helper is used only as a mechanical propagation tool
to avoid stale outer hashes. Expected semantic outcomes are independently
derived from the R2 contract and external review request.
"""
from __future__ import annotations
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable

PACKAGE_ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    "/mnt/data/f6_r2_review_pkg/F6-R2-external-independent-review-package"
)
VALIDATOR_PATH = PACKAGE_ROOT / "control-plane/registry/validate-f6-r2-ten-finding-proof-closure.py"
FIXTURE_PATH = PACKAGE_ROOT / "control-plane/registry/examples/2026-07-17-agents-os-f6-r2-ten-finding-proof-closure-v0.1.json"

spec = importlib.util.spec_from_file_location("f6r2_validator_under_review", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(validator)
base = validator.load_fixture(FIXTURE_PATH)

def normrows(data: dict[str, Any], schema: str) -> list[dict[str, Any]]:
    return data["normative_objects"][schema]

def assessments(data: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [
        row for row in normrows(data, "OpaqueUpstreamAssessmentInputV0_1R2")
        if row["payload"]["kind"] == kind
    ]

def refresh_assessment_subject(row: dict[str, Any]) -> None:
    payload = row["payload"]
    payload["subject_fingerprint"] = validator.typed_hash(
        f"agents-os.f6.r2.assessment-subject.{payload['kind']}",
        payload["subject_payload"],
    )

def sync_attempt_evidence(data: dict[str, Any], attempt: dict[str, Any]) -> None:
    payload = attempt["payload"]
    payload["evidence_set_fingerprint"] = validator.typed_hash(
        "agents-os.f6.r2.evidence-set", payload["evidence_bindings"]
    )
    assessment = next(
        row for row in assessments(data, "EVIDENCE_SET_CURRENTNESS")
        if row["ref"] == payload["evidence_assessment_ref"]
    )
    assessment["payload"]["subject_payload"] = {
        "evidence_bindings": copy.deepcopy(payload["evidence_bindings"]),
        "evidence_set_fingerprint": payload["evidence_set_fingerprint"],
    }
    assessment["payload"]["subject_revision"] = payload["attempt_revision"]
    refresh_assessment_subject(assessment)

def run_probe(
    probe_id: str,
    target: str,
    changed_objects: list[str],
    mutator: Callable[[dict[str, Any]], None],
) -> dict[str, Any]:
    data = copy.deepcopy(base)
    try:
        mutator(data)
        errors, _ = validator.validate_fixture(data, execute_r1=False)
        actual = "REJECT" if errors else "ACCEPT"
        exception = None
    except Exception as exc:  # no probe exception may count as a semantic rejection
        errors = []
        actual = "EXCEPTION"
        exception = f"{type(exc).__name__}: {exc}"
    stale_terms = (
        "root fingerprint mismatch",
        "fingerprint mismatch",
        "unresolved exact binding",
    )
    stale_only = bool(errors) and all(
        any(term in error for term in stale_terms) for error in errors
    )
    return {
        "id": probe_id,
        "objects_changed": changed_objects,
        "dependent_refs_and_fingerprints_propagated": True,
        "execution_completed_without_exception": exception is None,
        "expected_result": "REJECT",
        "actual_result": actual,
        "rejection_layer": target,
        "rejected_only_because_of_stale_outer_hash": stale_only,
        "validator_errors": errors,
        "exception": exception,
    }

def context_replace(data: dict[str, Any]) -> None:
    candidate = {
        "ref": "synth:f6:r2:taskcandidate:coordinated-alternate",
        "revision": 10,
        "fingerprint": "a" * 64,
    }
    dependency = {
        "ref": "synth:f6:r2:dependencyclosure:coordinated-alternate",
        "revision": 10,
        "fingerprint": "b" * 64,
    }
    task = assessments(data, "TASK_CURRENT_STATE")[0]
    task["payload"]["subject_payload"].update({
        "candidate_ref": candidate["ref"],
        "candidate_revision": candidate["revision"],
        "candidate_fingerprint": candidate["fingerprint"],
        "dependency_ref": dependency["ref"],
        "dependency_revision": dependency["revision"],
        "dependency_fingerprint": dependency["fingerprint"],
    })
    refresh_assessment_subject(task)
    for attempt in normrows(data, "ValidationAttemptRevisionV0_1R2"):
        attempt["payload"]["context_binding"]["candidate"] = copy.deepcopy(candidate)
        attempt["payload"]["context_binding"]["dependency"] = copy.deepcopy(dependency)
    completion = normrows(data, "TaskCompletionEligibilityDecisionV0_1R2")[0]["payload"]
    completion["candidate_context"] = copy.deepcopy(candidate)
    completion["dependency_context"] = copy.deepcopy(dependency)
    # Separate candidate/dependency currentness assessments intentionally remain
    # on the original subjects. Exact owner binding should reject the new context.
    validator.resign_all(data)

def waiver_substitution(data: dict[str, Any]) -> None:
    decision = data["supporting_objects"]["jenn_decisions"][0]
    command = next(row for row in data["supporting_objects"]["commands"] if row["key"] == "waiver:req-d")
    event = next(row for row in data["supporting_objects"]["events"] if row["key"] == "waiver:req-d")
    waiver = normrows(data, "RequirementWaiverEventV0_1R2")[0]
    authority = assessments(data, "JENN_WAIVER_AUTHORITY_CURRENTNESS")[0]

    decision["payload"].update({
        "decision_id": "jenn-waive-req-a-substituted",
        "requirement_id": "REQ-A",
        "requirement_revision": 2,
        "result": "CURRENT_ACCEPTED",
    })
    validator.reseal(decision)
    command["payload"].update({
        "command_id": "command:unrelated-operation",
        "purpose": "UNRELATED_OPERATION",
        "subject_fingerprint": "1" * 64,
    })
    validator.reseal(command)
    event["payload"].update({
        "command_ref": command["ref"],
        "command_fingerprint": command["fingerprint"],
        "event_id": "event:unrelated-operation",
        "event_kind": "UNRELATED_EVENT",
        "event_sequence": 114,
        "subject_fingerprint": "2" * 64,
    })
    validator.reseal(event)

    waiver["payload"].update({
        "jenn_decision_ref": decision["ref"],
        "jenn_decision_revision": decision["payload"]["decision_revision"],
        "jenn_decision_fingerprint": decision["fingerprint"],
        "command_ref": command["ref"],
        "command_fingerprint": command["fingerprint"],
        "event_ref": event["ref"],
        "event_fingerprint": event["fingerprint"],
        "event_sequence": 114,
    })
    wp = waiver["payload"]
    authority["payload"]["subject_ref"] = decision["ref"]
    authority["payload"]["subject_revision"] = decision["payload"]["decision_revision"]
    authority["payload"]["subject_payload"] = {
        "command_fingerprint": command["fingerprint"],
        "command_ref": command["ref"],
        "decision_fingerprint": decision["fingerprint"],
        "decision_ref": decision["ref"],
        "decision_revision": decision["payload"]["decision_revision"],
        "event_fingerprint": event["fingerprint"],
        "event_ref": event["ref"],
        "event_sequence": 114,
        "requirement_id": wp["requirement_id"],
        "requirement_revision": wp["requirement_revision"],
    }
    refresh_assessment_subject(authority)
    validator.resign_all(data)

def req_branch(data: dict[str, Any]) -> None:
    reqs = normrows(data, "ValidationRequirementRevisionV0_1R2")
    source = next(
        row for row in reqs
        if row["payload"]["requirement_id"] == "REQ-A"
        and row["payload"]["requirement_revision"] == 2
    )
    duplicate = copy.deepcopy(source)
    duplicate["key"] = "REQ-A:r2:independent-branch"
    validator.reseal(duplicate)
    reqs.append(duplicate)
    validator.resign_all(data)

def req_gap(data: dict[str, Any]) -> None:
    reqs = normrows(data, "ValidationRequirementRevisionV0_1R2")
    reqs[:] = [
        row for row in reqs
        if not (
            row["payload"]["requirement_id"] == "REQ-A"
            and row["payload"]["requirement_revision"] == 1
        )
    ]
    validator.resign_all(data)

def req_cycle(data: dict[str, Any]) -> None:
    reqs = [
        row for row in normrows(data, "ValidationRequirementRevisionV0_1R2")
        if row["payload"]["requirement_id"] == "REQ-A"
    ]
    r1 = next(row for row in reqs if row["payload"]["requirement_revision"] == 1)
    r2 = next(row for row in reqs if row["payload"]["requirement_revision"] == 2)
    r1["payload"].update({
        "predecessor_ref": r2["ref"],
        "predecessor_revision": 2,
        "predecessor_fingerprint": r2["fingerprint"],
    })
    validator.reseal(r1)
    r2["payload"]["predecessor_fingerprint"] = r1["fingerprint"]
    validator.reseal(r2)
    # A content-hash cycle has no practical closed fixed point. The semantic
    # base-predecessor/cycle error is nevertheless reached and is not solely an
    # outer-root mismatch.
    validator.resign_root(data)

def wrong_source_kind(data: dict[str, Any]) -> None:
    source = data["supporting_objects"]["provenance_sources"][0]
    source_ref = source["ref"]
    source["payload"]["source_kind"] = "ALIEN_SOURCE"
    validator.reseal(source)
    requirement = next(
        row for row in normrows(data, "ValidationRequirementRevisionV0_1R2")
        if any(binding["source_ref"] == source_ref for binding in row["payload"]["provenance_bindings"])
    )
    binding = next(
        item for item in requirement["payload"]["provenance_bindings"]
        if item["source_ref"] == source_ref
    )
    binding["source_fingerprint"] = source["fingerprint"]
    binding["source_kind"] = "ALIEN_SOURCE"
    authority = next(
        row for row in assessments(data, "REQUIREMENT_PROVENANCE_CURRENTNESS")
        if row["payload"]["subject_payload"]["source_ref"] == source_ref
    )
    authority["payload"]["subject_payload"].update({
        "source_fingerprint": source["fingerprint"],
        "source_kind": "ALIEN_SOURCE",
    })
    refresh_assessment_subject(authority)
    validator.resign_all(data)

def evidence_add(data: dict[str, Any]) -> None:
    attempt = next(row for row in normrows(data, "ValidationAttemptRevisionV0_1R2") if row["key"] == "ATTEMPT-A:r1")
    attempt["payload"]["evidence_bindings"].append({
        "evidence_ref": "a" * 64,
        "evidence_revision": 1,
        "evidence_fingerprint": "b" * 64,
    })
    attempt["payload"]["evidence_bindings"].sort(key=lambda row: row["evidence_ref"])
    sync_attempt_evidence(data, attempt)
    validator.resign_all(data)

def evidence_delete(data: dict[str, Any]) -> None:
    attempt = next(row for row in normrows(data, "ValidationAttemptRevisionV0_1R2") if row["key"] == "ATTEMPT-A:r1")
    attempt["payload"]["evidence_bindings"] = attempt["payload"]["evidence_bindings"][1:]
    sync_attempt_evidence(data, attempt)
    validator.resign_all(data)

def evidence_duplicate(data: dict[str, Any]) -> None:
    attempt = next(row for row in normrows(data, "ValidationAttemptRevisionV0_1R2") if row["key"] == "ATTEMPT-A:r1")
    attempt["payload"]["evidence_bindings"].append(copy.deepcopy(attempt["payload"]["evidence_bindings"][0]))
    attempt["payload"]["evidence_bindings"].sort(key=lambda row: row["evidence_ref"])
    sync_attempt_evidence(data, attempt)
    validator.resign_all(data)

def evidence_reorder(data: dict[str, Any]) -> None:
    attempt = next(row for row in normrows(data, "ValidationAttemptRevisionV0_1R2") if row["key"] == "ATTEMPT-A:r1")
    attempt["payload"]["evidence_bindings"].reverse()
    sync_attempt_evidence(data, attempt)
    validator.resign_all(data)

def carry_revision_mismatch(data: dict[str, Any]) -> None:
    attempt = next(
        row for row in normrows(data, "ValidationAttemptRevisionV0_1R2")
        if row["payload"]["method"] == "EVIDENCE_CARRY_FORWARD_REVIEW"
    )
    attempt["payload"]["carry_source"]["source_attempt_revision"] = 999
    attempt["payload"]["carry_source"]["root_source_attempt_revision"] = 998
    validator.resign_all(data)

def f5_subject_fingerprint_mismatch(data: dict[str, Any]) -> None:
    delivery = data["supporting_objects"]["delivery_subjects"][0]
    delivery["payload"]["subject_id"] = "effectful-delivery-substituted"
    validator.reseal(delivery)
    requirement = next(
        row for row in normrows(data, "ValidationRequirementRevisionV0_1R2")
        if row["payload"]["effectful"]
    )
    requirement["payload"]["delivery_subject_fingerprint"] = delivery["fingerprint"]
    # F5 assessment stays on the old subject fingerprint/payload.
    validator.resign_all(data)

def decision_matrix_contradiction(data: dict[str, Any]) -> None:
    waiver = normrows(data, "RequirementWaiverEventV0_1R2")[0]
    decision = next(
        row for row in normrows(data, "ValidationRequirementCurrentDecisionV0_1R2")
        if row["payload"]["requirement_id"] == "REQ-A"
    )
    decision["payload"]["waiver_head_ref"] = waiver["ref"]
    decision["payload"]["waiver_head_fingerprint"] = waiver["fingerprint"]
    validator.resign_all(data)

def empty_quiescence_counts(data: dict[str, Any]) -> None:
    guard = assessments(data, "COMPLETION_GUARD_CURRENTNESS")[0]
    guard["payload"]["subject_payload"]["counts"] = {}
    refresh_assessment_subject(guard)
    completion = normrows(data, "TaskCompletionEligibilityDecisionV0_1R2")[0]
    completion["payload"]["quiescence_counts"] = {}
    validator.resign_all(data)

def remove_dependency_assessment(data: dict[str, Any]) -> None:
    rows = normrows(data, "OpaqueUpstreamAssessmentInputV0_1R2")
    rows[:] = [
        row for row in rows
        if row["payload"]["kind"] != "DEPENDENCY_CLOSURE_CURRENTNESS"
    ]
    validator.resign_all(data)

def trusted_time_disconnect(data: dict[str, Any]) -> None:
    trusted_time = normrows(data, "TrustedTimeInputV0_1R2")[0]
    trusted_time["payload"].update({
        "barrier_ref": "synth:f6:r2:f3canonicalreadbarrierinputv0_1r2:wrong",
        "barrier_fingerprint": "f" * 64,
        "observed_event_sequence": 999,
    })
    validator.reseal(trusted_time)
    for profile in data["schema_profiles"]:
        if profile["schema_name"] == "TrustedTimeInputV0_1R2":
            profile["canonical_instance_fingerprint"] = trusted_time["fingerprint"]
            unsigned = {
                key: profile[key]
                for key in validator.PROFILE_FIELDS
                if key != "schema_fingerprint"
            }
            profile["schema_fingerprint"] = validator.typed_hash(
                "agents-os.f6.r2.schema-profile", unsigned
            )
    validator.resign_root(data)

def owner_phase_mismatch(data: dict[str, Any]) -> None:
    authority = assessments(data, "VALIDATION_AUTHORITY_CURRENTNESS")[0]
    authority["payload"]["owner_phase"] = "F1"  # owner contract remains the F3 contract
    validator.resign_all(data)

PROBES = [
    ("IR-CONTEXT-01", "candidate/dependency owner assessment binding",
     ["TASK_CURRENT_STATE assessment", "all attempt contexts", "completion context"], context_replace),
    ("IR-WAIVER-01", "exact immutable Jenn decision and authenticated Command/Event root",
     ["Jenn decision", "waiver Command", "waiver Event", "waiver", "Jenn authority assessment"], waiver_substitution),
    ("IR-GRAPH-BRANCH", "Requirement branch detection",
     ["Requirement revision graph", "dependent summaries/fingerprints"], req_branch),
    ("IR-GRAPH-GAP", "Requirement gap/missing predecessor detection",
     ["Requirement revision graph", "dependent summaries/fingerprints"], req_gap),
    ("IR-GRAPH-CYCLE", "Requirement cycle/base-predecessor detection",
     ["Requirement revision graph", "direct fingerprints/root"], req_cycle),
    ("IR-GRAPH-WRONG-SOURCE", "closed provenance source-kind and authority binding",
     ["provenance source", "Requirement binding", "owner assessment", "source closure"], wrong_source_kind),
    ("IR-EVIDENCE-ADD", "extra unbound evidence rejection",
     ["evidence array", "set fingerprint", "assessment", "attempt and decisions"], evidence_add),
    ("IR-EVIDENCE-DELETE", "missing evidence / immutable attempt revision",
     ["evidence array", "set fingerprint", "assessment", "attempt and decisions"], evidence_delete),
    ("IR-EVIDENCE-DUPLICATE", "duplicate evidence rejection",
     ["evidence array", "set fingerprint", "assessment", "attempt and decisions"], evidence_duplicate),
    ("IR-EVIDENCE-REORDER", "unsorted evidence rejection",
     ["evidence array", "set fingerprint", "assessment", "attempt and decisions"], evidence_reorder),
    ("IR-CARRY-REVISION", "carry source exact revision binding",
     ["carry source revision tuple", "attempt and decisions"], carry_revision_mismatch),
    ("IR-F5-SUBJECT-FP", "F5 assessment exact delivery subject fingerprint",
     ["delivery subject", "effectful Requirement", "downstream decisions"], f5_subject_fingerprint_mismatch),
    ("IR-DECISION-MATRIX", "closed decision nullability/cross-field matrix",
     ["Requirement decision", "set decision", "completion"], decision_matrix_contradiction),
    ("IR-COMPLETION-COUNTS", "exact five-key quiescence count closure",
     ["completion guard", "completion decision"], empty_quiescence_counts),
    ("IR-MISSING-DEPENDENCY-ASSESSMENT", "mandatory dependency owner assessment consumption",
     ["assessment inventory", "summary/root"], remove_dependency_assessment),
    ("IR-TRUSTED-TIME", "trusted time exact barrier and event-order binding",
     ["TrustedTime canonical instance", "schema profile", "root"], trusted_time_disconnect),
    ("IR-OWNER-PHASE", "owner phase and owner-contract exactness",
     ["Validation authority assessment", "dependent attempts/decisions"], owner_phase_mismatch),
]

results = [run_probe(pid, target, changed, mutator) for pid, target, changed, mutator in PROBES]
summary = {
    "executed": len(results),
    "rejected": sum(row["actual_result"] == "REJECT" for row in results),
    "unexpectedly_accepted": sum(row["actual_result"] == "ACCEPT" for row in results),
    "execution_exceptions": sum(row["actual_result"] == "EXCEPTION" for row in results),
}
output = {
    "schema_version": "agents-os.independent-coordinated-probes.v0.1",
    "package_id": "agents-os-f6-r2-atomic-independent-review-package-v0.1",
    "base_fixture_validated_without_errors": validator.validate_fixture(copy.deepcopy(base), execute_r1=False)[0] == [],
    "mechanical_propagation_note": "Author resign_all/reseal helpers used only to propagate hashes; semantic expectations and disposition are independent.",
    "summary": summary,
    "probes": results,
}
print(json.dumps(output, indent=2, ensure_ascii=False))
