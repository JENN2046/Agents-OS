#!/usr/bin/env python3
"""Build the deterministic synthetic F6 R2 ten-finding closure witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    WORKSPACE_ROOT
    / "control-plane/registry/examples/2026-07-17-agents-os-f6-r2-ten-finding-proof-closure-v0.1.json"
)

R1_PATHS = {
    "contract": "control-plane/registry/drafts/2026-07-17-agents-os-f6-validation-requirement-current-decision-v0.1-r1.draft.md",
    "builder": "control-plane/registry/build-f6-r1-validation-current-decision.py",
    "fixture": "control-plane/registry/examples/2026-07-17-agents-os-f6-r1-validation-current-decision-v0.1.json",
    "validator": "control-plane/registry/validate-f6-r1-validation-current-decision.py",
    "manifest": "control-plane/registry/reports/2026-07-17-agents-os-f6-r1-atomic-independent-review-package-v0.1.manifest.yaml",
    "review": "control-plane/registry/reviews/2026-07-17-yellow-agents-os-f6-r1-full-atomic-independent-review.yaml",
    "disposition": "control-plane/registry/reviews/2026-07-17-agents-os-f6-r1-independent-review-disposition-v0.1.yaml",
    "start_decision": "control-plane/registry/decisions/2026-07-17-agents-os-f6-r2-ten-finding-proof-closure-start-decision-v0.1.yaml",
}

SCHEMA_FIELDS: dict[str, list[str]] = {
    "F3CanonicalReadBarrierInputV0_1R2": [
        "barrier_id", "barrier_revision", "domain", "end_event_sequence",
        "environment", "start_event_sequence",
    ],
    "TrustedTimeInputV0_1R2": [
        "barrier_fingerprint", "barrier_ref", "observed_event_sequence",
        "trusted_time_id", "trusted_time_revision",
    ],
    "OpaqueUpstreamAssessmentInputV0_1R2": [
        "assessment_id", "assessment_revision", "barrier_fingerprint",
        "barrier_ref", "is_current_head", "kind", "observed_event_sequence",
        "owner_contract_fingerprint", "owner_contract_ref", "owner_phase",
        "result", "subject_fingerprint", "subject_payload", "subject_ref",
        "subject_revision",
    ],
    "ValidationRequirementRevisionV0_1R2": [
        "creation_command_fingerprint", "creation_command_ref",
        "creation_event_fingerprint", "creation_event_ref",
        "creation_event_sequence", "delivery_subject_fingerprint",
        "delivery_subject_ref", "delivery_subject_revision", "effectful",
        "predecessor_fingerprint", "predecessor_ref", "predecessor_revision",
        "provenance_bindings", "provenance_set_fingerprint", "requirement_id",
        "requirement_revision", "task_id", "validator_contract_fingerprint",
        "validator_contract_ref", "validator_contract_revision", "waivability",
    ],
    "RequirementWaiverEventV0_1R2": [
        "authority_assessment_fingerprint", "authority_assessment_ref",
        "authority_assessment_revision", "base_snapshot_fingerprint",
        "base_snapshot_ref", "base_snapshot_revision", "command_fingerprint",
        "command_ref", "event_fingerprint", "event_ref", "event_sequence",
        "expires_at_sequence", "is_current_head", "jenn_decision_fingerprint",
        "jenn_decision_ref", "jenn_decision_revision", "operation",
        "predecessor_fingerprint", "predecessor_ref", "predecessor_revision",
        "requirement_fingerprint", "requirement_id", "requirement_revision",
        "valid_from_sequence", "waiver_id", "waiver_revision",
    ],
    "ValidationSetSnapshotV0_1R2": [
        "change_kind", "freeze_event_fingerprint", "freeze_event_ref",
        "frozen_event_sequence", "memberships", "predecessor_fingerprint",
        "predecessor_ref", "predecessor_revision", "set_id", "set_revision",
        "source_closure", "source_closure_fingerprint", "waiver_heads",
    ],
    "ValidationAttemptRevisionV0_1R2": [
        "attempt_id", "attempt_revision", "authority_assessment_fingerprint",
        "authority_assessment_ref", "authority_assessment_revision",
        "carry_source", "context_binding", "created_event_fingerprint",
        "created_event_ref", "created_event_sequence", "current_head",
        "evidence_assessment_fingerprint", "evidence_assessment_ref",
        "evidence_assessment_revision", "evidence_bindings",
        "evidence_set_fingerprint", "f5_assessment_fingerprint",
        "f5_assessment_ref", "f5_assessment_revision", "method",
        "observed_event_sequence", "predecessor_fingerprint", "predecessor_ref",
        "predecessor_revision", "requirement_fingerprint", "requirement_id",
        "requirement_revision", "set_fingerprint", "set_ref", "set_revision",
        "state",
    ],
    "ValidationRequirementCurrentDecisionV0_1R2": [
        "attempt_head_fingerprint", "attempt_head_ref", "barrier_fingerprint",
        "barrier_ref", "context_fingerprint", "decision_id",
        "observed_event_sequence", "primary_reason", "reason_codes",
        "requirement_fingerprint", "requirement_id", "requirement_revision",
        "result", "set_fingerprint", "set_ref", "set_revision",
        "waiver_head_fingerprint", "waiver_head_ref",
    ],
    "ValidationSetCurrentDecisionV0_1R2": [
        "barrier_fingerprint", "barrier_ref", "decision_id",
        "observed_event_sequence", "primary_reason", "reason_codes",
        "requirement_decisions", "result", "set_fingerprint", "set_ref",
        "set_revision",
    ],
    "TaskCompletionEligibilityDecisionV0_1R2": [
        "barrier_fingerprint", "barrier_ref", "candidate_context",
        "completion_guard_assessment_fingerprint", "completion_guard_assessment_ref",
        "completion_guard_assessment_revision", "decision_id", "dependency_context",
        "f5_blocker_assessment_fingerprint", "f5_blocker_assessment_ref",
        "f5_blocker_assessment_revision", "observed_event_sequence",
        "primary_reason", "quiescence_counts", "reason_codes", "result",
        "set_decision_fingerprint", "set_decision_ref", "task_id",
        "task_state_assessment_fingerprint", "task_state_assessment_ref",
        "task_state_assessment_revision",
    ],
}

R1_INDEPENDENT_PROBES = [f"F6-R1-IR-P{index:02d}" for index in range(1, 19)]


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def typed_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def file_hash(path: str) -> str:
    return hashlib.sha256((WORKSPACE_ROOT / path).read_bytes()).hexdigest()


def stable_ref(schema: str, key: str) -> str:
    return f"synth:f6:r2:{schema.lower()}:{typed_hash('agents-os.f6.r2.ref', [schema, key])}"


def seal(schema: str, key: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "ref": stable_ref(schema, key),
        "schema": schema,
        "key": key,
        "payload": payload,
        "fingerprint": typed_hash(f"agents-os.f6.r2.{schema}", payload),
    }


def support(kind: str, key: str, payload: dict[str, Any]) -> dict[str, Any]:
    return seal(f"Support{kind}", key, payload)


def make_assessment(
    *, kind: str, owner_phase: str, owner_contract_ref: str,
    owner_contract_fingerprint: str, subject_ref: str, subject_revision: int,
    subject_payload: dict[str, Any], result: str, observed: int,
    barrier: dict[str, Any], key: str,
) -> dict[str, Any]:
    subject_fingerprint = typed_hash(f"agents-os.f6.r2.assessment-subject.{kind}", subject_payload)
    payload = {
        "assessment_id": f"assessment:{key}",
        "assessment_revision": 1,
        "barrier_fingerprint": barrier["fingerprint"],
        "barrier_ref": barrier["ref"],
        "is_current_head": True,
        "kind": kind,
        "observed_event_sequence": observed,
        "owner_contract_fingerprint": owner_contract_fingerprint,
        "owner_contract_ref": owner_contract_ref,
        "owner_phase": owner_phase,
        "result": result,
        "subject_fingerprint": subject_fingerprint,
        "subject_payload": subject_payload,
        "subject_ref": subject_ref,
        "subject_revision": subject_revision,
    }
    return seal("OpaqueUpstreamAssessmentInputV0_1R2", key, payload)


def make_command(key: str, purpose: str, subject_payload: dict[str, Any]) -> dict[str, Any]:
    return support("Command", key, {
        "command_id": f"command:{key}",
        "purpose": purpose,
        "subject_fingerprint": typed_hash("agents-os.f6.r2.command-subject", subject_payload),
    })


def make_event(key: str, kind: str, sequence: int, command: dict[str, Any], subject_payload: dict[str, Any]) -> dict[str, Any]:
    return support("Event", key, {
        "command_fingerprint": command["fingerprint"],
        "command_ref": command["ref"],
        "event_id": f"event:{key}",
        "event_kind": kind,
        "event_sequence": sequence,
        "subject_fingerprint": typed_hash("agents-os.f6.r2.event-subject", subject_payload),
    })


def make_requirement(
    *, requirement_id: str, revision: int, predecessor: dict[str, Any] | None,
    task_id: str, waivability: str, effectful: bool, validator_contract: dict[str, Any],
    provenance_source: dict[str, Any], provenance_assessment: dict[str, Any],
    creation_command: dict[str, Any], creation_event: dict[str, Any],
    delivery_subject: dict[str, Any] | None,
) -> dict[str, Any]:
    binding = {
        "creation_command_fingerprint": creation_command["fingerprint"],
        "creation_command_ref": creation_command["ref"],
        "creation_event_fingerprint": creation_event["fingerprint"],
        "creation_event_ref": creation_event["ref"],
        "creation_event_sequence": creation_event["payload"]["event_sequence"],
        "source_fingerprint": provenance_source["fingerprint"],
        "source_kind": provenance_source["payload"]["source_kind"],
        "source_owner_assessment_fingerprint": provenance_assessment["fingerprint"],
        "source_owner_assessment_ref": provenance_assessment["ref"],
        "source_owner_assessment_revision": provenance_assessment["payload"]["assessment_revision"],
        "source_ref": provenance_source["ref"],
        "source_revision": provenance_source["payload"]["source_revision"],
    }
    payload = {
        "creation_command_fingerprint": creation_command["fingerprint"],
        "creation_command_ref": creation_command["ref"],
        "creation_event_fingerprint": creation_event["fingerprint"],
        "creation_event_ref": creation_event["ref"],
        "creation_event_sequence": creation_event["payload"]["event_sequence"],
        "delivery_subject_fingerprint": None if delivery_subject is None else delivery_subject["fingerprint"],
        "delivery_subject_ref": None if delivery_subject is None else delivery_subject["ref"],
        "delivery_subject_revision": None if delivery_subject is None else delivery_subject["payload"]["subject_revision"],
        "effectful": effectful,
        "predecessor_fingerprint": None if predecessor is None else predecessor["fingerprint"],
        "predecessor_ref": None if predecessor is None else predecessor["ref"],
        "predecessor_revision": None if predecessor is None else predecessor["payload"]["requirement_revision"],
        "provenance_bindings": [binding],
        "provenance_set_fingerprint": typed_hash("agents-os.f6.r2.provenance-set", [binding]),
        "requirement_id": requirement_id,
        "requirement_revision": revision,
        "task_id": task_id,
        "validator_contract_fingerprint": validator_contract["fingerprint"],
        "validator_contract_ref": validator_contract["ref"],
        "validator_contract_revision": validator_contract["payload"]["contract_revision"],
        "waivability": waivability,
    }
    return seal("ValidationRequirementRevisionV0_1R2", f"{requirement_id}:r{revision}", payload)


def evidence_set(label: str) -> tuple[list[dict[str, Any]], str]:
    rows = sorted([
        {"evidence_fingerprint": hashlib.sha256(f"{label}:evidence:1".encode()).hexdigest(), "evidence_ref": hashlib.sha256(f"{label}:ref:1".encode()).hexdigest(), "evidence_revision": 1},
        {"evidence_fingerprint": hashlib.sha256(f"{label}:evidence:2".encode()).hexdigest(), "evidence_ref": hashlib.sha256(f"{label}:ref:2".encode()).hexdigest(), "evidence_revision": 1},
    ], key=lambda row: row["evidence_ref"])
    return rows, typed_hash("agents-os.f6.r2.evidence-set", rows)


def build_fixture() -> dict[str, Any]:
    barrier = seal("F3CanonicalReadBarrierInputV0_1R2", "barrier", {
        "barrier_id": "f6-r2-barrier", "barrier_revision": 1,
        "domain": "SYNTHETIC_TEST", "end_event_sequence": 200,
        "environment": "SYNTHETIC_TEST", "start_event_sequence": 1,
    })
    trusted_time = seal("TrustedTimeInputV0_1R2", "trusted-time", {
        "barrier_fingerprint": barrier["fingerprint"], "barrier_ref": barrier["ref"],
        "observed_event_sequence": 150, "trusted_time_id": "f6-r2-time",
        "trusted_time_revision": 1,
    })

    f1_contract = support("OwnerContract", "f1", {"owner_phase": "F1", "revision": 3})
    f3_contract = support("OwnerContract", "f3", {"owner_phase": "F3", "revision": 4})
    f5_contract = support("OwnerContract", "f5", {"owner_phase": "F5", "revision": 7})
    validator_contract = support("ValidatorContract", "validator", {"contract_id": "f6-validator-synthetic", "contract_revision": 2})
    delivery_subject = support("DeliverySubject", "effectful", {"subject_id": "effectful-delivery", "subject_revision": 5})

    candidate_payload = {"candidate_id": "candidate-current", "candidate_revision": 9, "status": "CURRENT"}
    dependency_payload = {"dependency_id": "dependency-current", "dependency_revision": 9, "status": "CURRENT_CONFIRMED"}
    candidate_ref = stable_ref("TaskCandidate", "candidate-current")
    dependency_ref = stable_ref("DependencyClosure", "dependency-current")
    candidate_assessment = make_assessment(
        kind="CANDIDATE_COMMITMENT_CURRENTNESS", owner_phase="F1",
        owner_contract_ref=f1_contract["ref"], owner_contract_fingerprint=f1_contract["fingerprint"],
        subject_ref=candidate_ref, subject_revision=9, subject_payload=candidate_payload,
        result="CURRENT", observed=140, barrier=barrier, key="candidate",
    )
    dependency_assessment = make_assessment(
        kind="DEPENDENCY_CLOSURE_CURRENTNESS", owner_phase="F1",
        owner_contract_ref=f1_contract["ref"], owner_contract_fingerprint=f1_contract["fingerprint"],
        subject_ref=dependency_ref, subject_revision=9, subject_payload=dependency_payload,
        result="CURRENT_CONFIRMED", observed=140, barrier=barrier, key="dependency",
    )
    task_state_payload = {
        "candidate_fingerprint": candidate_assessment["payload"]["subject_fingerprint"],
        "candidate_ref": candidate_ref, "candidate_revision": 9,
        "dependency_fingerprint": dependency_assessment["payload"]["subject_fingerprint"],
        "dependency_ref": dependency_ref, "dependency_revision": 9,
        "task_id": "task:f6-r2", "task_lifecycle": "VERIFYING",
        "task_revision": 5, "task_state_revision": 5,
    }
    task_state_assessment = make_assessment(
        kind="TASK_CURRENT_STATE", owner_phase="F1",
        owner_contract_ref=f1_contract["ref"], owner_contract_fingerprint=f1_contract["fingerprint"],
        subject_ref="synth:f6:r2:task:f6-r2", subject_revision=5,
        subject_payload=task_state_payload, result="CURRENT_VERIFYING", observed=141,
        barrier=barrier, key="task-state",
    )
    f5_blocker_payload = {"result_id": "f5-blocker", "result_revision": 5, "status": "CLEAR"}
    f5_blocker_assessment = make_assessment(
        kind="F5_COMPLETION_BLOCKING_CURRENTNESS", owner_phase="F5",
        owner_contract_ref=f5_contract["ref"], owner_contract_fingerprint=f5_contract["fingerprint"],
        subject_ref=stable_ref("F5CompletionBlocker", "current"), subject_revision=5,
        subject_payload=f5_blocker_payload, result="CLEAR", observed=142,
        barrier=barrier, key="f5-blocker",
    )
    counts = {"active_attempt_count": 0, "active_effect_count": 0, "open_command_count": 0, "open_delivery_count": 0, "pending_event_count": 0}
    guard_payload = {"guard_id": "completion-guard", "guard_revision": 5, "counts": counts, "status": "CURRENT_ZERO"}
    guard_assessment = make_assessment(
        kind="COMPLETION_GUARD_CURRENTNESS", owner_phase="F3",
        owner_contract_ref=f3_contract["ref"], owner_contract_fingerprint=f3_contract["fingerprint"],
        subject_ref=stable_ref("CompletionGuard", "current"), subject_revision=5,
        subject_payload=guard_payload, result="CURRENT_ZERO", observed=143,
        barrier=barrier, key="completion-guard",
    )

    commands: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    provenance_sources: list[dict[str, Any]] = []
    assessments = [candidate_assessment, dependency_assessment, task_state_assessment, f5_blocker_assessment, guard_assessment]
    requirements: list[dict[str, Any]] = []

    def requirement_revision(req_id: str, revision: int, sequence: int, predecessor: dict[str, Any] | None, waivability: str, effectful: bool) -> dict[str, Any]:
        source = support("ProvenanceSource", f"{req_id}:r{revision}", {"source_kind": "TASK_SPEC", "source_revision": revision, "task_id": "task:f6-r2"})
        natural = {"requirement_id": req_id, "requirement_revision": revision, "source_ref": source["ref"], "source_fingerprint": source["fingerprint"]}
        command = make_command(f"create:{req_id}:r{revision}", "CREATE_OR_REVISE_REQUIREMENT", natural)
        event = make_event(f"create:{req_id}:r{revision}", "REQUIREMENT_COMMITTED", sequence, command, natural)
        provenance_payload = {
            "command_fingerprint": command["fingerprint"], "command_ref": command["ref"],
            "event_fingerprint": event["fingerprint"], "event_ref": event["ref"],
            "event_sequence": sequence, "source_fingerprint": source["fingerprint"],
            "source_kind": "TASK_SPEC", "source_ref": source["ref"], "source_revision": revision,
        }
        assessment = make_assessment(
            kind="REQUIREMENT_PROVENANCE_CURRENTNESS", owner_phase="F3",
            owner_contract_ref=f3_contract["ref"], owner_contract_fingerprint=f3_contract["fingerprint"],
            subject_ref=stable_ref("RequirementProvenance", f"{req_id}:r{revision}"),
            subject_revision=revision, subject_payload=provenance_payload,
            result="CURRENT_ACCEPTED", observed=sequence, barrier=barrier,
            key=f"provenance:{req_id}:r{revision}",
        )
        commands.append(command); events.append(event); provenance_sources.append(source); assessments.append(assessment)
        req = make_requirement(
            requirement_id=req_id, revision=revision, predecessor=predecessor,
            task_id="task:f6-r2", waivability=waivability, effectful=effectful,
            validator_contract=validator_contract, provenance_source=source,
            provenance_assessment=assessment, creation_command=command,
            creation_event=event, delivery_subject=delivery_subject if effectful else None,
        )
        requirements.append(req)
        return req

    req_a1 = requirement_revision("REQ-A", 1, 10, None, "NON_WAIVABLE", False)
    req_a2 = requirement_revision("REQ-A", 2, 20, req_a1, "NON_WAIVABLE", False)
    req_b = requirement_revision("REQ-B", 1, 30, None, "NON_WAIVABLE", False)
    req_c = requirement_revision("REQ-C", 1, 40, None, "NON_WAIVABLE", True)
    req_d = requirement_revision("REQ-D", 1, 50, None, "WAIVABLE", False)
    current_requirements = [req_a2, req_b, req_c, req_d]

    def membership(req: dict[str, Any]) -> dict[str, Any]:
        return {"requirement_fingerprint": req["fingerprint"], "requirement_id": req["payload"]["requirement_id"], "requirement_ref": req["ref"], "requirement_revision": req["payload"]["requirement_revision"]}

    source_closure = sorted([row for req in current_requirements for row in req["payload"]["provenance_bindings"]], key=lambda row: row["source_ref"])
    base_freeze_command = make_command("set:base", "FREEZE_VALIDATION_SET", {"set_id": "SET-F6-R2", "revision": 1})
    base_freeze_event = make_event("set:base", "VALIDATION_SET_FROZEN", 110, base_freeze_command, {"set_id": "SET-F6-R2", "revision": 1})
    commands.append(base_freeze_command); events.append(base_freeze_event)
    base_set = seal("ValidationSetSnapshotV0_1R2", "set:r1", {
        "change_kind": "BASE", "freeze_event_fingerprint": base_freeze_event["fingerprint"],
        "freeze_event_ref": base_freeze_event["ref"], "frozen_event_sequence": 110,
        "memberships": sorted([membership(req) for req in current_requirements], key=lambda row: row["requirement_id"]),
        "predecessor_fingerprint": None, "predecessor_ref": None, "predecessor_revision": None,
        "set_id": "SET-F6-R2", "set_revision": 1, "source_closure": source_closure,
        "source_closure_fingerprint": typed_hash("agents-os.f6.r2.source-closure", source_closure),
        "waiver_heads": [],
    })

    jenn_decision = support("JennDecision", "waive:req-d", {"decision_id": "jenn-waive-req-d", "decision_revision": 1, "requirement_id": "REQ-D", "requirement_revision": 1, "result": "CURRENT_ACCEPTED"})
    waiver_natural = {"decision_fingerprint": jenn_decision["fingerprint"], "decision_ref": jenn_decision["ref"], "decision_revision": 1, "requirement_id": "REQ-D", "requirement_revision": 1}
    waiver_command = make_command("waiver:req-d", "GRANT_REQUIREMENT_WAIVER", waiver_natural)
    waiver_event = make_event("waiver:req-d", "WAIVER_COMMITTED", 114, waiver_command, waiver_natural)
    commands.append(waiver_command); events.append(waiver_event)
    waiver_authority_payload = {
        "command_fingerprint": waiver_command["fingerprint"], "command_ref": waiver_command["ref"],
        "decision_fingerprint": jenn_decision["fingerprint"], "decision_ref": jenn_decision["ref"],
        "decision_revision": 1, "event_fingerprint": waiver_event["fingerprint"],
        "event_ref": waiver_event["ref"], "event_sequence": 114,
        "requirement_id": "REQ-D", "requirement_revision": 1,
    }
    waiver_authority = make_assessment(
        kind="JENN_WAIVER_AUTHORITY_CURRENTNESS", owner_phase="F3",
        owner_contract_ref=f3_contract["ref"], owner_contract_fingerprint=f3_contract["fingerprint"],
        subject_ref=jenn_decision["ref"], subject_revision=1,
        subject_payload=waiver_authority_payload, result="CURRENT_ACCEPTED",
        observed=114, barrier=barrier, key="waiver-authority:req-d",
    )
    assessments.append(waiver_authority)
    waiver = seal("RequirementWaiverEventV0_1R2", "waiver:req-d:r1", {
        "authority_assessment_fingerprint": waiver_authority["fingerprint"],
        "authority_assessment_ref": waiver_authority["ref"], "authority_assessment_revision": 1,
        "base_snapshot_fingerprint": base_set["fingerprint"], "base_snapshot_ref": base_set["ref"],
        "base_snapshot_revision": 1, "command_fingerprint": waiver_command["fingerprint"],
        "command_ref": waiver_command["ref"], "event_fingerprint": waiver_event["fingerprint"],
        "event_ref": waiver_event["ref"], "event_sequence": 114, "expires_at_sequence": 180,
        "is_current_head": True, "jenn_decision_fingerprint": jenn_decision["fingerprint"],
        "jenn_decision_ref": jenn_decision["ref"], "jenn_decision_revision": 1,
        "operation": "GRANT", "predecessor_fingerprint": None, "predecessor_ref": None,
        "predecessor_revision": None, "requirement_fingerprint": req_d["fingerprint"],
        "requirement_id": "REQ-D", "requirement_revision": 1,
        "valid_from_sequence": 114, "waiver_id": "WAIVER-REQ-D", "waiver_revision": 1,
    })

    current_freeze_command = make_command("set:current", "FREEZE_VALIDATION_SET", {"set_id": "SET-F6-R2", "revision": 2, "waiver": waiver["fingerprint"]})
    current_freeze_event = make_event("set:current", "VALIDATION_SET_FROZEN", 120, current_freeze_command, {"set_id": "SET-F6-R2", "revision": 2, "waiver": waiver["fingerprint"]})
    commands.append(current_freeze_command); events.append(current_freeze_event)
    current_set = seal("ValidationSetSnapshotV0_1R2", "set:r2", {
        "change_kind": "WAIVER_CHANGE", "freeze_event_fingerprint": current_freeze_event["fingerprint"],
        "freeze_event_ref": current_freeze_event["ref"], "frozen_event_sequence": 120,
        "memberships": sorted([membership(req) for req in current_requirements], key=lambda row: row["requirement_id"]),
        "predecessor_fingerprint": base_set["fingerprint"], "predecessor_ref": base_set["ref"],
        "predecessor_revision": 1, "set_id": "SET-F6-R2", "set_revision": 2,
        "source_closure": source_closure,
        "source_closure_fingerprint": typed_hash("agents-os.f6.r2.source-closure", source_closure),
        "waiver_heads": [{"waiver_fingerprint": waiver["fingerprint"], "waiver_ref": waiver["ref"], "waiver_revision": 1}],
    })

    attempts: list[dict[str, Any]] = []
    evidence_assessments: list[dict[str, Any]] = []
    authority_assessments: list[dict[str, Any]] = []
    f5_delivery_assessment: dict[str, Any] | None = None

    candidate_context = {"fingerprint": candidate_assessment["payload"]["subject_fingerprint"], "ref": candidate_ref, "revision": 9}
    dependency_context = {"fingerprint": dependency_assessment["payload"]["subject_fingerprint"], "ref": dependency_ref, "revision": 9}

    def attempt(req: dict[str, Any], attempt_id: str, revision: int, sequence: int, method: str, predecessor: dict[str, Any] | None, current_head: bool, carry_source: dict[str, Any] | None, effectful: bool) -> dict[str, Any]:
        rows, set_fp = evidence_set(attempt_id)
        ev_assessment = make_assessment(
            kind="EVIDENCE_SET_CURRENTNESS", owner_phase="F3",
            owner_contract_ref=f3_contract["ref"], owner_contract_fingerprint=f3_contract["fingerprint"],
            subject_ref=stable_ref("EvidenceSet", attempt_id), subject_revision=revision,
            subject_payload={"evidence_bindings": rows, "evidence_set_fingerprint": set_fp},
            result="EXACT_CURRENT", observed=sequence, barrier=barrier, key=f"evidence:{attempt_id}:r{revision}",
        )
        authority_payload = {
            "requirement_id": req["payload"]["requirement_id"],
            "requirement_revision": req["payload"]["requirement_revision"],
            "validator_contract_fingerprint": validator_contract["fingerprint"],
            "validator_contract_ref": validator_contract["ref"],
            "validator_contract_revision": 2,
        }
        auth_assessment = make_assessment(
            kind="VALIDATION_AUTHORITY_CURRENTNESS", owner_phase="F3",
            owner_contract_ref=f3_contract["ref"], owner_contract_fingerprint=f3_contract["fingerprint"],
            subject_ref=validator_contract["ref"], subject_revision=2,
            subject_payload=authority_payload, result="CURRENT_ACCEPTED",
            observed=sequence, barrier=barrier, key=f"authority:{attempt_id}:r{revision}",
        )
        evidence_assessments.append(ev_assessment); authority_assessments.append(auth_assessment)
        event_command = make_command(f"attempt:{attempt_id}:r{revision}", "COMMIT_VALIDATION_ATTEMPT", {"attempt_id": attempt_id, "revision": revision})
        event = make_event(f"attempt:{attempt_id}:r{revision}", "VALIDATION_ATTEMPT_COMMITTED", sequence, event_command, {"attempt_id": attempt_id, "revision": revision})
        commands.append(event_command); events.append(event)
        f5_binding = None
        nonlocal f5_delivery_assessment
        if effectful:
            delivery_payload = {"delivery_subject_fingerprint": delivery_subject["fingerprint"], "delivery_subject_ref": delivery_subject["ref"], "delivery_subject_revision": 5, "status": "APPLIED_CURRENT"}
            f5_binding = make_assessment(
                kind="F5_DELIVERY_CURRENTNESS", owner_phase="F5",
                owner_contract_ref=f5_contract["ref"], owner_contract_fingerprint=f5_contract["fingerprint"],
                subject_ref=delivery_subject["ref"], subject_revision=5,
                subject_payload=delivery_payload, result="APPLIED_CURRENT",
                observed=sequence, barrier=barrier, key=f"f5-delivery:{attempt_id}",
            )
            f5_delivery_assessment = f5_binding
        context_payload = {
            "candidate": candidate_context, "dependency": dependency_context,
            "evidence_set_fingerprint": set_fp,
            "requirement_fingerprint": req["fingerprint"],
            "requirement_id": req["payload"]["requirement_id"],
            "requirement_revision": req["payload"]["requirement_revision"],
            "set_fingerprint": current_set["fingerprint"], "set_ref": current_set["ref"],
            "set_revision": 2, "validator_contract_fingerprint": validator_contract["fingerprint"],
            "validator_contract_ref": validator_contract["ref"], "validator_contract_revision": 2,
        }
        context_payload["context_fingerprint"] = typed_hash("agents-os.f6.r2.validation-context", context_payload)
        payload = {
            "attempt_id": attempt_id, "attempt_revision": revision,
            "authority_assessment_fingerprint": auth_assessment["fingerprint"],
            "authority_assessment_ref": auth_assessment["ref"], "authority_assessment_revision": 1,
            "carry_source": carry_source, "context_binding": context_payload,
            "created_event_fingerprint": event["fingerprint"], "created_event_ref": event["ref"],
            "created_event_sequence": sequence, "current_head": current_head,
            "evidence_assessment_fingerprint": ev_assessment["fingerprint"],
            "evidence_assessment_ref": ev_assessment["ref"], "evidence_assessment_revision": 1,
            "evidence_bindings": rows, "evidence_set_fingerprint": set_fp,
            "f5_assessment_fingerprint": None if f5_binding is None else f5_binding["fingerprint"],
            "f5_assessment_ref": None if f5_binding is None else f5_binding["ref"],
            "f5_assessment_revision": None if f5_binding is None else 1,
            "method": method, "observed_event_sequence": sequence,
            "predecessor_fingerprint": None if predecessor is None else predecessor["fingerprint"],
            "predecessor_ref": None if predecessor is None else predecessor["ref"],
            "predecessor_revision": None if predecessor is None else predecessor["payload"]["attempt_revision"],
            "requirement_fingerprint": req["fingerprint"], "requirement_id": req["payload"]["requirement_id"],
            "requirement_revision": req["payload"]["requirement_revision"],
            "set_fingerprint": current_set["fingerprint"], "set_ref": current_set["ref"], "set_revision": 2,
            "state": "PASSED",
        }
        row = seal("ValidationAttemptRevisionV0_1R2", f"{attempt_id}:r{revision}", payload)
        attempts.append(row)
        return row

    attempt_a = attempt(req_a2, "ATTEMPT-A", 1, 130, "FRESH_VALIDATION", None, True, None, False)
    attempt_b1 = attempt(req_b, "ATTEMPT-B", 1, 131, "FRESH_VALIDATION", None, False, None, False)
    carry_source = {"root_source_attempt_fingerprint": attempt_b1["fingerprint"], "root_source_attempt_ref": attempt_b1["ref"], "root_source_attempt_revision": 1, "source_attempt_fingerprint": attempt_b1["fingerprint"], "source_attempt_ref": attempt_b1["ref"], "source_attempt_revision": 1}
    attempt_b2 = attempt(req_b, "ATTEMPT-B", 2, 132, "EVIDENCE_CARRY_FORWARD_REVIEW", attempt_b1, True, carry_source, False)
    attempt_c = attempt(req_c, "ATTEMPT-C", 1, 133, "FRESH_VALIDATION", None, True, None, True)
    assessments.extend(evidence_assessments + authority_assessments)
    if f5_delivery_assessment is not None:
        assessments.append(f5_delivery_assessment)

    def requirement_decision(req: dict[str, Any], attempt_head: dict[str, Any] | None, waiver_head: dict[str, Any] | None, result: str, reason: str) -> dict[str, Any]:
        return seal("ValidationRequirementCurrentDecisionV0_1R2", f"decision:{req['payload']['requirement_id']}", {
            "attempt_head_fingerprint": None if attempt_head is None else attempt_head["fingerprint"],
            "attempt_head_ref": None if attempt_head is None else attempt_head["ref"],
            "barrier_fingerprint": barrier["fingerprint"], "barrier_ref": barrier["ref"],
            "context_fingerprint": None if attempt_head is None else attempt_head["payload"]["context_binding"]["context_fingerprint"],
            "decision_id": f"decision:{req['payload']['requirement_id']}",
            "observed_event_sequence": 150, "primary_reason": reason, "reason_codes": [reason],
            "requirement_fingerprint": req["fingerprint"], "requirement_id": req["payload"]["requirement_id"],
            "requirement_revision": req["payload"]["requirement_revision"], "result": result,
            "set_fingerprint": current_set["fingerprint"], "set_ref": current_set["ref"], "set_revision": 2,
            "waiver_head_fingerprint": None if waiver_head is None else waiver_head["fingerprint"],
            "waiver_head_ref": None if waiver_head is None else waiver_head["ref"],
        })

    requirement_decisions = [
        requirement_decision(req_a2, attempt_a, None, "SATISFIED", "VALIDATION_PASSED"),
        requirement_decision(req_b, attempt_b2, None, "SATISFIED", "VALIDATION_PASSED"),
        requirement_decision(req_c, attempt_c, None, "SATISFIED", "VALIDATION_PASSED"),
        requirement_decision(req_d, None, waiver, "WAIVED", "CURRENT_WAIVER"),
    ]
    decision_bindings = sorted([{"decision_fingerprint": row["fingerprint"], "decision_ref": row["ref"], "requirement_id": row["payload"]["requirement_id"]} for row in requirement_decisions], key=lambda row: row["requirement_id"])
    set_decision = seal("ValidationSetCurrentDecisionV0_1R2", "set-decision", {
        "barrier_fingerprint": barrier["fingerprint"], "barrier_ref": barrier["ref"],
        "decision_id": "set-decision", "observed_event_sequence": 150,
        "primary_reason": "ALL_REQUIRED_CURRENT", "reason_codes": ["ALL_REQUIRED_CURRENT"],
        "requirement_decisions": decision_bindings, "result": "SATISFIED",
        "set_fingerprint": current_set["fingerprint"], "set_ref": current_set["ref"], "set_revision": 2,
    })
    completion_decision = seal("TaskCompletionEligibilityDecisionV0_1R2", "completion-decision", {
        "barrier_fingerprint": barrier["fingerprint"], "barrier_ref": barrier["ref"],
        "candidate_context": candidate_context,
        "completion_guard_assessment_fingerprint": guard_assessment["fingerprint"],
        "completion_guard_assessment_ref": guard_assessment["ref"], "completion_guard_assessment_revision": 1,
        "decision_id": "completion-decision", "dependency_context": dependency_context,
        "f5_blocker_assessment_fingerprint": f5_blocker_assessment["fingerprint"],
        "f5_blocker_assessment_ref": f5_blocker_assessment["ref"], "f5_blocker_assessment_revision": 1,
        "observed_event_sequence": 150, "primary_reason": "ALL_COMPLETION_GATES_CURRENT",
        "quiescence_counts": counts, "reason_codes": ["ALL_COMPLETION_GATES_CURRENT"],
        "result": "ELIGIBLE", "set_decision_fingerprint": set_decision["fingerprint"],
        "set_decision_ref": set_decision["ref"], "task_id": "task:f6-r2",
        "task_state_assessment_fingerprint": task_state_assessment["fingerprint"],
        "task_state_assessment_ref": task_state_assessment["ref"], "task_state_assessment_revision": 1,
    })

    normative_objects: dict[str, list[dict[str, Any]]] = {
        "F3CanonicalReadBarrierInputV0_1R2": [barrier],
        "TrustedTimeInputV0_1R2": [trusted_time],
        "OpaqueUpstreamAssessmentInputV0_1R2": assessments,
        "ValidationRequirementRevisionV0_1R2": requirements,
        "RequirementWaiverEventV0_1R2": [waiver],
        "ValidationSetSnapshotV0_1R2": [base_set, current_set],
        "ValidationAttemptRevisionV0_1R2": attempts,
        "ValidationRequirementCurrentDecisionV0_1R2": requirement_decisions,
        "ValidationSetCurrentDecisionV0_1R2": [set_decision],
        "TaskCompletionEligibilityDecisionV0_1R2": [completion_decision],
    }
    schema_profiles = []
    for schema in sorted(SCHEMA_FIELDS):
        instance = normative_objects[schema][0]
        if schema == "ValidationRequirementRevisionV0_1R2":
            instance = req_a2
        profile_payload = {
            "canonical_instance_fingerprint": instance["fingerprint"],
            "canonical_instance_ref": instance["ref"],
            "closed_fields": SCHEMA_FIELDS[schema],
            "schema_name": schema,
            "schema_revision": 2,
        }
        profile_payload["schema_fingerprint"] = typed_hash("agents-os.f6.r2.schema-profile", profile_payload)
        schema_profiles.append(profile_payload)

    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f6.validation-current-decision-r2-proof.v0.1",
        "environment": "SYNTHETIC_TEST",
        "runtime_usable": False,
        "r1_bindings": {key: {"path": path, "sha256": file_hash(path)} for key, path in R1_PATHS.items()},
        "schema_profiles": schema_profiles,
        "normative_objects": normative_objects,
        "supporting_objects": {
            "commands": commands,
            "events": events,
            "owner_contracts": [f1_contract, f3_contract, f5_contract],
            "provenance_sources": provenance_sources,
            "validator_contracts": [validator_contract],
            "delivery_subjects": [delivery_subject],
            "jenn_decisions": [jenn_decision],
        },
        "regression_catalog": {
            "R1_fixed_mutation_count": 32,
            "R1_independent_probe_ids": R1_INDEPENDENT_PROBES,
            "R2_additional_negative_ids": [
                "SCHEMA-INVENTORY-MISSING", "SCHEMA-UNKNOWN-FIELD",
                "DECISION-CROSS-FIELD", "REQUIREMENT-BRANCH", "REQUIREMENT-CYCLE",
                "EVIDENCE-DUPLICATE", "EVIDENCE-UNSORTED", "CARRY-CHAIN",
                "F5-WRONG-SUBJECT", "F5-HISTORY-ONLY", "EVENT-ORDER",
                "CONTEXT-MISMATCH",
            ],
        },
        "occurrence_assertions": {
            "accepted_real_task_count": 0, "database_write_count": 0,
            "external_effect_count": 0, "provider_call_count": 0,
            "raw_secret_count": 0, "runtime_activation_count": 0,
            "task_done_mutation_count": 0, "terminal_outcome": "NOT_EXECUTED",
        },
        "summary": {
            "normative_schema_count": len(schema_profiles),
            "normative_instance_count": sum(len(rows) for rows in normative_objects.values()),
            "positive_graph_count": 3,
            "R1_fixed_mutation_count": 32,
            "R1_independent_regression_count": 18,
            "R2_additional_negative_count": 12,
            "requirement_revision_count": len(requirements),
            "current_requirement_count": len(current_requirements),
            "attempt_revision_count": len(attempts),
            "requirement_decision_count": len(requirement_decisions),
            "derived_satisfied_count": 3,
            "derived_waived_count": 1,
            "derived_completion_eligible_count": 1,
        },
    }
    fixture["root_fingerprint"] = typed_hash("agents-os.f6.r2.root", fixture)
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
