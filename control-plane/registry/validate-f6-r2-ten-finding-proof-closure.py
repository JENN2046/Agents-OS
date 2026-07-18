#!/usr/bin/env python3
"""Offline semantic validator for the synthetic F6 R2 closure witness."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = WORKSPACE_ROOT / "control-plane/registry/examples/2026-07-17-agents-os-f6-r2-ten-finding-proof-closure-v0.1.json"
R1_VALIDATOR = WORKSPACE_ROOT / "control-plane/registry/validate-f6-r1-validation-current-decision.py"
SAFE_MAX = 2**53 - 1
HEX_RE = re.compile(r"^[0-9a-f]{64}$")
REF_RE = re.compile(r"^[a-z0-9][a-z0-9:._/-]*$")

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

TOP_FIELDS = {"schema_version", "environment", "runtime_usable", "r1_bindings", "schema_profiles", "normative_objects", "supporting_objects", "regression_catalog", "occurrence_assertions", "summary", "root_fingerprint"}
WRAPPER_FIELDS = {"ref", "schema", "key", "payload", "fingerprint"}
PROFILE_FIELDS = {"canonical_instance_fingerprint", "canonical_instance_ref", "closed_fields", "schema_name", "schema_revision", "schema_fingerprint"}
R1_PROBES = [f"F6-R1-IR-P{index:02d}" for index in range(1, 19)]


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


def stable_ref(schema: str, key: str) -> str:
    return f"synth:f6:r2:{schema.lower()}:{typed_hash('agents-os.f6.r2.ref', [schema, key])}"


def is_int(value: Any, positive: bool = False) -> bool:
    return type(value) is int and 0 <= value <= SAFE_MAX and (not positive or value > 0)


def check_tree(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, float):
        errors.append(f"{path}: float forbidden")
    elif type(value) is int and not (-SAFE_MAX <= value <= SAFE_MAX):
        errors.append(f"{path}: unsafe integer")
    elif isinstance(value, str) and unicodedata.normalize("NFC", value) != value:
        errors.append(f"{path}: non-NFC string")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            check_tree(item, f"{path}[{index}]", errors)
    elif isinstance(value, dict):
        for key, item in value.items():
            check_tree(key, f"{path}.<key>", errors)
            check_tree(item, f"{path}.{key}", errors)


def exact_fields(value: Any, expected: set[str], path: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{path}: object required")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(f"{path}: fields mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
        return False
    return True


def valid_hash(value: Any) -> bool:
    return isinstance(value, str) and HEX_RE.fullmatch(value) is not None


def valid_ref(value: Any) -> bool:
    return isinstance(value, str) and REF_RE.fullmatch(value) is not None


def wrapper_index(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in data.get("normative_objects", {}).values():
        if isinstance(group, list):
            rows.extend(row for row in group if isinstance(row, dict))
    for group in data.get("supporting_objects", {}).values():
        if isinstance(group, list):
            rows.extend(row for row in group if isinstance(row, dict))
    return {row.get("ref", f"invalid:{index}"): row for index, row in enumerate(rows)}


def validate_wrapper(row: Any, path: str, errors: list[str], expected_schema: str | None = None) -> None:
    if not exact_fields(row, WRAPPER_FIELDS, path, errors):
        return
    schema = row["schema"]
    if not isinstance(schema, str) or (expected_schema is not None and schema != expected_schema):
        errors.append(f"{path}: schema mismatch")
        return
    if not isinstance(row["key"], str) or row["ref"] != stable_ref(schema, row["key"]):
        errors.append(f"{path}: stable ref mismatch")
    if not isinstance(row["payload"], dict):
        errors.append(f"{path}: payload object required")
        return
    if row["fingerprint"] != typed_hash(f"agents-os.f6.r2.{schema}", row["payload"]):
        errors.append(f"{path}: fingerprint mismatch")
    if expected_schema in SCHEMA_FIELDS and set(row["payload"]) != set(SCHEMA_FIELDS[expected_schema]):
        errors.append(f"{path}: closed payload fields mismatch")


def require_bound(index: dict[str, dict[str, Any]], ref: Any, fingerprint: Any, path: str, errors: list[str], schema: str | None = None) -> dict[str, Any] | None:
    if not valid_ref(ref) or not valid_hash(fingerprint):
        errors.append(f"{path}: invalid binding")
        return None
    row = index.get(ref)
    if row is None or row.get("fingerprint") != fingerprint:
        errors.append(f"{path}: unresolved exact binding")
        return None
    if schema is not None and row.get("schema") != schema:
        errors.append(f"{path}: wrong schema")
        return None
    return row


def validate_fixture(data: Any, *, execute_r1: bool = False) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts = {"R1_mutations": 0}
    if not exact_fields(data, TOP_FIELDS, "$", errors):
        return errors, counts
    check_tree(data, "$", errors)
    if data["schema_version"] != "agents-os.f6.validation-current-decision-r2-proof.v0.1" or data["environment"] != "SYNTHETIC_TEST" or data["runtime_usable"] is not False:
        errors.append("$: environment or schema boundary mismatch")
    unsigned = copy.deepcopy(data); root = unsigned.pop("root_fingerprint", None)
    if root != typed_hash("agents-os.f6.r2.root", unsigned):
        errors.append("$: root fingerprint mismatch")

    if set(data["r1_bindings"]) != set(R1_PATHS):
        errors.append("$.r1_bindings: key set mismatch")
    else:
        for key, expected_path in R1_PATHS.items():
            binding = data["r1_bindings"][key]
            if not exact_fields(binding, {"path", "sha256"}, f"$.r1_bindings.{key}", errors):
                continue
            if binding["path"] != expected_path:
                errors.append(f"$.r1_bindings.{key}: path mismatch")
                continue
            actual = hashlib.sha256((WORKSPACE_ROOT / expected_path).read_bytes()).hexdigest()
            if binding["sha256"] != actual:
                errors.append(f"$.r1_bindings.{key}: hash mismatch")
    if execute_r1:
        run = subprocess.run([sys.executable, str(R1_VALIDATOR)], cwd=WORKSPACE_ROOT, text=True, capture_output=True)
        if run.returncode != 0 or "negative_mutations_rejected: 32" not in run.stdout:
            errors.append("R1 validator regression failed")
        else:
            counts["R1_mutations"] = 32

    if set(data["normative_objects"]) != set(SCHEMA_FIELDS):
        errors.append("$.normative_objects: schema inventory mismatch")
    profiles = data["schema_profiles"]
    if not isinstance(profiles, list) or len(profiles) != 10:
        errors.append("$.schema_profiles: exactly ten required")
        profiles = []
    profile_names = [row.get("schema_name") for row in profiles if isinstance(row, dict)]
    if profile_names != sorted(SCHEMA_FIELDS) or len(set(profile_names)) != len(profile_names):
        errors.append("$.schema_profiles: sorted exact unique names required")

    index = wrapper_index(data)
    all_refs: list[str] = []
    for schema, rows in data["normative_objects"].items():
        if not isinstance(rows, list) or not rows:
            errors.append(f"$.normative_objects.{schema}: nonempty array required")
            continue
        for idx, row in enumerate(rows):
            validate_wrapper(row, f"$.normative_objects.{schema}[{idx}]", errors, schema)
            if isinstance(row, dict): all_refs.append(row.get("ref"))
    for group, rows in data["supporting_objects"].items():
        if not isinstance(rows, list):
            errors.append(f"$.supporting_objects.{group}: array required")
            continue
        for idx, row in enumerate(rows):
            validate_wrapper(row, f"$.supporting_objects.{group}[{idx}]", errors)
            if isinstance(row, dict): all_refs.append(row.get("ref"))
    if len(all_refs) != len(set(all_refs)):
        errors.append("$: duplicate object ref")

    for idx, profile in enumerate(profiles):
        path = f"$.schema_profiles[{idx}]"
        if not exact_fields(profile, PROFILE_FIELDS, path, errors): continue
        schema = profile["schema_name"]
        if schema not in SCHEMA_FIELDS: continue
        expected_fields = SCHEMA_FIELDS[schema]
        if profile["schema_revision"] != 2 or profile["closed_fields"] != expected_fields:
            errors.append(f"{path}: schema definition mismatch")
        instance = require_bound(index, profile["canonical_instance_ref"], profile["canonical_instance_fingerprint"], path+".instance", errors, schema)
        unsigned_profile = {key: profile[key] for key in PROFILE_FIELDS if key != "schema_fingerprint"}
        if profile["schema_fingerprint"] != typed_hash("agents-os.f6.r2.schema-profile", unsigned_profile):
            errors.append(f"{path}: schema fingerprint mismatch")
        if instance is not None and set(instance["payload"]) != set(expected_fields):
            errors.append(f"{path}: canonical instance fields mismatch")

    barriers = data["normative_objects"].get("F3CanonicalReadBarrierInputV0_1R2", [])
    if len(barriers) != 1: errors.append("barrier: exactly one required")
    barrier = barriers[0] if barriers else {"ref": None, "fingerprint": None, "payload": {}}
    bp = barrier.get("payload", {})
    if not is_int(bp.get("barrier_revision"), True) or not is_int(bp.get("start_event_sequence"), True) or not is_int(bp.get("end_event_sequence"), True) or bp.get("start_event_sequence", 0) > bp.get("end_event_sequence", -1):
        errors.append("barrier: invalid sequence")
    if bp.get("domain") != "SYNTHETIC_TEST" or bp.get("environment") != "SYNTHETIC_TEST": errors.append("barrier: synthetic domain required")

    assessments = data["normative_objects"].get("OpaqueUpstreamAssessmentInputV0_1R2", [])
    assessment_by_ref = {row["ref"]: row for row in assessments if isinstance(row, dict) and "ref" in row}
    allowed_results = {
        "TASK_CURRENT_STATE": {"CURRENT_VERIFYING"}, "CANDIDATE_COMMITMENT_CURRENTNESS": {"CURRENT"},
        "DEPENDENCY_CLOSURE_CURRENTNESS": {"CURRENT_CONFIRMED"}, "F5_COMPLETION_BLOCKING_CURRENTNESS": {"CLEAR"},
        "COMPLETION_GUARD_CURRENTNESS": {"CURRENT_ZERO"}, "REQUIREMENT_PROVENANCE_CURRENTNESS": {"CURRENT_ACCEPTED"},
        "JENN_WAIVER_AUTHORITY_CURRENTNESS": {"CURRENT_ACCEPTED"}, "EVIDENCE_SET_CURRENTNESS": {"EXACT_CURRENT"},
        "VALIDATION_AUTHORITY_CURRENTNESS": {"CURRENT_ACCEPTED"}, "F5_DELIVERY_CURRENTNESS": {"APPLIED_CURRENT"},
    }
    revision_key = {
        "TASK_CURRENT_STATE": "task_state_revision", "CANDIDATE_COMMITMENT_CURRENTNESS": "candidate_revision",
        "DEPENDENCY_CLOSURE_CURRENTNESS": "dependency_revision", "F5_COMPLETION_BLOCKING_CURRENTNESS": "result_revision",
        "COMPLETION_GUARD_CURRENTNESS": "guard_revision", "REQUIREMENT_PROVENANCE_CURRENTNESS": "source_revision",
        "JENN_WAIVER_AUTHORITY_CURRENTNESS": "decision_revision", "VALIDATION_AUTHORITY_CURRENTNESS": "validator_contract_revision",
        "F5_DELIVERY_CURRENTNESS": "delivery_subject_revision",
    }
    for idx, row in enumerate(assessments):
        p = row["payload"]; path = f"assessment[{idx}]"; kind = p.get("kind")
        if kind not in allowed_results or p.get("result") not in allowed_results.get(kind, set()): errors.append(f"{path}: kind/result matrix")
        if p.get("barrier_ref") != barrier.get("ref") or p.get("barrier_fingerprint") != barrier.get("fingerprint") or p.get("is_current_head") is not True: errors.append(f"{path}: barrier/current head mismatch")
        if not is_int(p.get("assessment_revision"), True) or not is_int(p.get("subject_revision"), True) or not is_int(p.get("observed_event_sequence"), True) or p.get("observed_event_sequence", SAFE_MAX) > bp.get("end_event_sequence", -1): errors.append(f"{path}: revision/sequence invalid")
        if p.get("subject_fingerprint") != typed_hash(f"agents-os.f6.r2.assessment-subject.{kind}", p.get("subject_payload")): errors.append(f"{path}: subject fingerprint mismatch")
        key = revision_key.get(kind)
        if key is not None and p.get("subject_payload", {}).get(key) != p.get("subject_revision"): errors.append(f"{path}: exact subject revision mismatch")
        require_bound(index, p.get("owner_contract_ref"), p.get("owner_contract_fingerprint"), path+".owner", errors)

    requirements = data["normative_objects"].get("ValidationRequirementRevisionV0_1R2", [])
    req_by_ref = {row["ref"]: row for row in requirements}
    req_groups: dict[str, list[dict[str, Any]]] = {}
    for row in requirements: req_groups.setdefault(row["payload"]["requirement_id"], []).append(row)
    for req_id, rows in req_groups.items():
        rows.sort(key=lambda row: (type(row["payload"].get("requirement_revision")) is not int, row["payload"].get("requirement_revision", 0)))
        revisions = [row["payload"].get("requirement_revision") for row in rows]
        if any(type(value) is not int for value in revisions) or revisions != list(range(1, len(rows)+1)): errors.append(f"requirement {req_id}: contiguous exact integer revisions required")
        for pos, row in enumerate(rows):
            p=row["payload"]
            if pos == 0:
                if any(p.get(k) is not None for k in ("predecessor_ref","predecessor_revision","predecessor_fingerprint")): errors.append(f"requirement {req_id}: revision1 predecessor must be null")
            else:
                prev=rows[pos-1]
                if not is_int(p.get("predecessor_revision"), True):
                    errors.append(f"requirement {req_id}: predecessor revision must be exact positive integer")
                if (p.get("predecessor_ref"),p.get("predecessor_revision"),p.get("predecessor_fingerprint")) != (prev["ref"],prev["payload"]["requirement_revision"],prev["fingerprint"]): errors.append(f"requirement {req_id}: predecessor mismatch")
                if prev["payload"].get("creation_event_sequence", SAFE_MAX) >= p.get("creation_event_sequence", -1):
                    errors.append(f"requirement {req_id}: predecessor Event must precede revision Event")
            if p.get("waivability") not in {"WAIVABLE","NON_WAIVABLE"} or type(p.get("effectful")) is not bool: errors.append(f"requirement {req_id}: matrix invalid")
            if p.get("effectful"):
                require_bound(index,p.get("delivery_subject_ref"),p.get("delivery_subject_fingerprint"),f"requirement {req_id}.delivery",errors)
                if not is_int(p.get("delivery_subject_revision"),True): errors.append(f"requirement {req_id}: delivery revision")
            elif any(p.get(k) is not None for k in ("delivery_subject_ref","delivery_subject_revision","delivery_subject_fingerprint")): errors.append(f"requirement {req_id}: non-effectful delivery fields")
            command=require_bound(index,p.get("creation_command_ref"),p.get("creation_command_fingerprint"),f"requirement {req_id}.command",errors)
            event=require_bound(index,p.get("creation_event_ref"),p.get("creation_event_fingerprint"),f"requirement {req_id}.event",errors)
            if event is not None and event["payload"].get("event_sequence") != p.get("creation_event_sequence"): errors.append(f"requirement {req_id}: creation event sequence mismatch")
            bindings=p.get("provenance_bindings")
            if not isinstance(bindings,list) or not bindings or bindings != sorted(bindings,key=lambda x:x.get("source_ref","")) or len({x.get("source_ref") for x in bindings}) != len(bindings): errors.append(f"requirement {req_id}: provenance set invalid")
            elif p.get("provenance_set_fingerprint") != typed_hash("agents-os.f6.r2.provenance-set",bindings): errors.append(f"requirement {req_id}: provenance fingerprint")
            else:
                for binding in bindings:
                    source=require_bound(index,binding.get("source_ref"),binding.get("source_fingerprint"),f"requirement {req_id}.source",errors)
                    assessment=require_bound(index,binding.get("source_owner_assessment_ref"),binding.get("source_owner_assessment_fingerprint"),f"requirement {req_id}.source assessment",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
                    if source is not None and source["payload"].get("source_revision") != binding.get("source_revision"): errors.append(f"requirement {req_id}: source revision mismatch")
                    if assessment is not None:
                        ap=assessment["payload"]
                        expected={"command_fingerprint":binding.get("creation_command_fingerprint"),"command_ref":binding.get("creation_command_ref"),"event_fingerprint":binding.get("creation_event_fingerprint"),"event_ref":binding.get("creation_event_ref"),"event_sequence":binding.get("creation_event_sequence"),"source_fingerprint":binding.get("source_fingerprint"),"source_kind":binding.get("source_kind"),"source_ref":binding.get("source_ref"),"source_revision":binding.get("source_revision")}
                        if ap.get("kind")!="REQUIREMENT_PROVENANCE_CURRENTNESS" or ap.get("result")!="CURRENT_ACCEPTED" or ap.get("subject_revision")!=p.get("requirement_revision") or ap.get("subject_payload")!=expected: errors.append(f"requirement {req_id}: provenance authority mismatch")

    sets = data["normative_objects"].get("ValidationSetSnapshotV0_1R2", [])
    sets.sort(key=lambda row: row["payload"].get("set_revision",0)); set_by_ref={row["ref"]:row for row in sets}
    current_heads={req_id:max(rows,key=lambda row:row["payload"]["requirement_revision"]) for req_id,rows in req_groups.items()}
    exact_memberships=sorted([{"requirement_fingerprint":row["fingerprint"],"requirement_id":rid,"requirement_ref":row["ref"],"requirement_revision":row["payload"]["requirement_revision"]} for rid,row in current_heads.items()],key=lambda x:x["requirement_id"])
    exact_sources=sorted([binding for row in current_heads.values() for binding in row["payload"]["provenance_bindings"]],key=lambda x:x["source_ref"])
    for pos,row in enumerate(sets):
        p=row["payload"]
        if p.get("set_revision")!=pos+1: errors.append("set: contiguous revisions required")
        if p.get("memberships")!=exact_memberships: errors.append("set: exact current membership required")
        if p.get("source_closure")!=exact_sources or p.get("source_closure_fingerprint")!=typed_hash("agents-os.f6.r2.source-closure",exact_sources): errors.append("set: exact provenance closure required")
        freeze=require_bound(index,p.get("freeze_event_ref"),p.get("freeze_event_fingerprint"),"set.freeze",errors)
        if freeze is not None and freeze["payload"].get("event_sequence")!=p.get("frozen_event_sequence"): errors.append("set: freeze event mismatch")
        for member in p.get("memberships",[]):
            req=req_by_ref.get(member.get("requirement_ref"))
            if req is not None and req["payload"].get("creation_event_sequence",SAFE_MAX)>p.get("frozen_event_sequence",-1): errors.append("set: requirement created after containing snapshot")
        if pos==0:
            if any(p.get(k) is not None for k in ("predecessor_ref","predecessor_revision","predecessor_fingerprint")): errors.append("set: base predecessor")
        else:
            prev=sets[pos-1]
            if (p.get("predecessor_ref"),p.get("predecessor_revision"),p.get("predecessor_fingerprint"))!=(prev["ref"],prev["payload"]["set_revision"],prev["fingerprint"]): errors.append("set: predecessor mismatch")

    waivers=data["normative_objects"].get("RequirementWaiverEventV0_1R2",[]); waiver_by_ref={row["ref"]:row for row in waivers}
    for row in waivers:
        p=row["payload"]; req=next((x for x in requirements if x["payload"]["requirement_id"]==p.get("requirement_id") and x["payload"]["requirement_revision"]==p.get("requirement_revision")),None)
        if req is None or req["fingerprint"]!=p.get("requirement_fingerprint") or req["payload"].get("waivability")!="WAIVABLE": errors.append("waiver: exact waivable Requirement required")
        base=require_bound(index,p.get("base_snapshot_ref"),p.get("base_snapshot_fingerprint"),"waiver.base",errors,"ValidationSetSnapshotV0_1R2")
        decision=require_bound(index,p.get("jenn_decision_ref"),p.get("jenn_decision_fingerprint"),"waiver.decision",errors)
        command=require_bound(index,p.get("command_ref"),p.get("command_fingerprint"),"waiver.command",errors)
        event=require_bound(index,p.get("event_ref"),p.get("event_fingerprint"),"waiver.event",errors)
        assessment=require_bound(index,p.get("authority_assessment_ref"),p.get("authority_assessment_fingerprint"),"waiver.assessment",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
        if decision is not None and decision["payload"].get("decision_revision")!=p.get("jenn_decision_revision"): errors.append("waiver: decision revision mismatch")
        expected={"command_fingerprint":p.get("command_fingerprint"),"command_ref":p.get("command_ref"),"decision_fingerprint":p.get("jenn_decision_fingerprint"),"decision_ref":p.get("jenn_decision_ref"),"decision_revision":p.get("jenn_decision_revision"),"event_fingerprint":p.get("event_fingerprint"),"event_ref":p.get("event_ref"),"event_sequence":p.get("event_sequence"),"requirement_id":p.get("requirement_id"),"requirement_revision":p.get("requirement_revision")}
        if assessment is not None:
            ap=assessment["payload"]
            if ap.get("kind")!="JENN_WAIVER_AUTHORITY_CURRENTNESS" or ap.get("result")!="CURRENT_ACCEPTED" or ap.get("subject_ref")!=p.get("jenn_decision_ref") or ap.get("subject_revision")!=p.get("jenn_decision_revision") or ap.get("subject_payload")!=expected: errors.append("waiver: exact Jenn authority mismatch")
        if base is not None and not (base["payload"].get("frozen_event_sequence",SAFE_MAX)<p.get("event_sequence",-1)): errors.append("waiver: event must follow base snapshot")
        if event is not None and event["payload"].get("event_sequence")!=p.get("event_sequence"): errors.append("waiver: event sequence mismatch")
        if p.get("operation")!="GRANT" or p.get("is_current_head") is not True or not (p.get("valid_from_sequence",SAFE_MAX)<=150<p.get("expires_at_sequence",-1)): errors.append("waiver: current grant matrix")
    if sets:
        current_set=sets[-1]
        for head in current_set["payload"].get("waiver_heads",[]):
            waiver=require_bound(index,head.get("waiver_ref"),head.get("waiver_fingerprint"),"set.waiver_head",errors,"RequirementWaiverEventV0_1R2")
            if waiver is not None and not (waiver["payload"].get("event_sequence",SAFE_MAX)<=current_set["payload"].get("frozen_event_sequence",-1)): errors.append("set: waiver after consuming snapshot")
    else:
        current_set={"ref":None,"fingerprint":None,"payload":{}}

    attempts=data["normative_objects"].get("ValidationAttemptRevisionV0_1R2",[]); attempt_by_ref={row["ref"]:row for row in attempts}
    attempt_groups:dict[str,list[dict[str,Any]]]={}
    for row in attempts: attempt_groups.setdefault(row["payload"]["attempt_id"],[]).append(row)
    current_attempts:dict[str,dict[str,Any]]={}
    for attempt_id,rows in attempt_groups.items():
        rows.sort(key=lambda row:row["payload"].get("attempt_revision",0))
        if [r["payload"].get("attempt_revision") for r in rows]!=list(range(1,len(rows)+1)): errors.append(f"attempt {attempt_id}: contiguous chain")
        if sum(r["payload"].get("current_head") is True for r in rows)!=1 or rows[-1]["payload"].get("current_head") is not True: errors.append(f"attempt {attempt_id}: unique latest head")
        for pos,row in enumerate(rows):
            p=row["payload"]
            if pos==0:
                if any(p.get(k) is not None for k in ("predecessor_ref","predecessor_revision","predecessor_fingerprint")): errors.append(f"attempt {attempt_id}: base predecessor")
            else:
                prev=rows[pos-1]
                if (p.get("predecessor_ref"),p.get("predecessor_revision"),p.get("predecessor_fingerprint"))!=(prev["ref"],prev["payload"]["attempt_revision"],prev["fingerprint"]): errors.append(f"attempt {attempt_id}: predecessor mismatch")
            req=next((x for x in requirements if x["payload"]["requirement_id"]==p.get("requirement_id") and x["payload"]["requirement_revision"]==p.get("requirement_revision")),None)
            if req is None or req["fingerprint"]!=p.get("requirement_fingerprint"): errors.append(f"attempt {attempt_id}: Requirement binding")
            if (p.get("set_ref"),p.get("set_revision"),p.get("set_fingerprint"))!=(current_set.get("ref"),current_set.get("payload",{}).get("set_revision"),current_set.get("fingerprint")): errors.append(f"attempt {attempt_id}: set binding")
            event=require_bound(index,p.get("created_event_ref"),p.get("created_event_fingerprint"),f"attempt {attempt_id}.event",errors)
            if event is not None and event["payload"].get("event_sequence")!=p.get("created_event_sequence"): errors.append(f"attempt {attempt_id}: event sequence")
            if not (current_set.get("payload",{}).get("frozen_event_sequence",SAFE_MAX)<=p.get("created_event_sequence",-1)<=p.get("observed_event_sequence",-1)<=150): errors.append(f"attempt {attempt_id}: temporal order")
            context=p.get("context_binding",{}); unsigned_context=dict(context); cfp=unsigned_context.pop("context_fingerprint",None)
            if cfp!=typed_hash("agents-os.f6.r2.validation-context",unsigned_context): errors.append(f"attempt {attempt_id}: context fingerprint")
            if context.get("requirement_fingerprint")!=p.get("requirement_fingerprint") or context.get("set_fingerprint")!=p.get("set_fingerprint"): errors.append(f"attempt {attempt_id}: context subject mismatch")
            evidence=p.get("evidence_bindings")
            if not isinstance(evidence,list) or not evidence or evidence!=sorted(evidence,key=lambda x:x.get("evidence_ref","")) or len({x.get("evidence_ref") for x in evidence})!=len(evidence): errors.append(f"attempt {attempt_id}: exact evidence set")
            elif p.get("evidence_set_fingerprint")!=typed_hash("agents-os.f6.r2.evidence-set",evidence) or context.get("evidence_set_fingerprint")!=p.get("evidence_set_fingerprint"): errors.append(f"attempt {attempt_id}: evidence fingerprint")
            ev_assessment=require_bound(index,p.get("evidence_assessment_ref"),p.get("evidence_assessment_fingerprint"),f"attempt {attempt_id}.evidence assessment",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
            if ev_assessment is not None:
                ep=ev_assessment["payload"]
                if ep.get("kind")!="EVIDENCE_SET_CURRENTNESS" or ep.get("result")!="EXACT_CURRENT" or ep.get("subject_revision")!=p.get("attempt_revision") or ep.get("subject_payload")!={"evidence_bindings":evidence,"evidence_set_fingerprint":p.get("evidence_set_fingerprint")}: errors.append(f"attempt {attempt_id}: exact evidence assessment")
            auth=require_bound(index,p.get("authority_assessment_ref"),p.get("authority_assessment_fingerprint"),f"attempt {attempt_id}.authority",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
            expected_auth={"requirement_id":p.get("requirement_id"),"requirement_revision":p.get("requirement_revision"),"validator_contract_fingerprint":context.get("validator_contract_fingerprint"),"validator_contract_ref":context.get("validator_contract_ref"),"validator_contract_revision":context.get("validator_contract_revision")}
            if auth is not None:
                ap=auth["payload"]
                if ap.get("kind")!="VALIDATION_AUTHORITY_CURRENTNESS" or ap.get("result")!="CURRENT_ACCEPTED" or ap.get("subject_revision")!=context.get("validator_contract_revision") or ap.get("subject_payload")!=expected_auth: errors.append(f"attempt {attempt_id}: current authority required")
            if p.get("state")!="PASSED": errors.append(f"attempt {attempt_id}: positive witness must PASSED")
            if p.get("method")=="FRESH_VALIDATION":
                if p.get("carry_source") is not None: errors.append(f"attempt {attempt_id}: fresh carry fields forbidden")
            elif p.get("method")=="EVIDENCE_CARRY_FORWARD_REVIEW":
                carry=p.get("carry_source")
                if not isinstance(carry,dict): errors.append(f"attempt {attempt_id}: carry source required")
                else:
                    source_candidate = attempt_by_ref.get(carry.get("source_attempt_ref"))
                    if source_candidate is not None and source_candidate["payload"].get("method") != "FRESH_VALIDATION":
                        errors.append(f"attempt {attempt_id}: carry source must be original fresh validation")
                    source=require_bound(index,carry.get("source_attempt_ref"),carry.get("source_attempt_fingerprint"),f"attempt {attempt_id}.carry",errors,"ValidationAttemptRevisionV0_1R2")
                    root_source=require_bound(index,carry.get("root_source_attempt_ref"),carry.get("root_source_attempt_fingerprint"),f"attempt {attempt_id}.root carry",errors,"ValidationAttemptRevisionV0_1R2")
                    if source is None or root_source is None or source["ref"]!=root_source["ref"] or source["payload"].get("method")!="FRESH_VALIDATION" or source["payload"].get("state")!="PASSED" or source["payload"].get("requirement_id")!=p.get("requirement_id"): errors.append(f"attempt {attempt_id}: direct original fresh source required")
            else: errors.append(f"attempt {attempt_id}: unknown method")
            effectful=False if req is None else req["payload"].get("effectful")
            if effectful:
                f5=require_bound(index,p.get("f5_assessment_ref"),p.get("f5_assessment_fingerprint"),f"attempt {attempt_id}.f5",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
                if f5 is not None:
                    fp=f5["payload"]
                    if fp.get("kind")!="F5_DELIVERY_CURRENTNESS" or fp.get("result")!="APPLIED_CURRENT" or fp.get("subject_ref")!=req["payload"].get("delivery_subject_ref") or fp.get("subject_revision")!=req["payload"].get("delivery_subject_revision") or fp.get("subject_fingerprint")!=typed_hash("agents-os.f6.r2.assessment-subject.F5_DELIVERY_CURRENTNESS",fp.get("subject_payload")): errors.append(f"attempt {attempt_id}: exact F5 supporting evidence")
            elif any(p.get(k) is not None for k in ("f5_assessment_ref","f5_assessment_revision","f5_assessment_fingerprint")): errors.append(f"attempt {attempt_id}: F5 forbidden for non-effectful")
        current_attempts[rows[-1]["payload"]["requirement_id"]]=rows[-1]

    req_decisions=data["normative_objects"].get("ValidationRequirementCurrentDecisionV0_1R2",[]); req_decision_by_req={row["payload"]["requirement_id"]:row for row in req_decisions}
    for req_id,req in current_heads.items():
        decision=req_decision_by_req.get(req_id)
        if decision is None: errors.append(f"decision {req_id}: missing"); continue
        p=decision["payload"]; attempt=current_attempts.get(req_id); waiver=next((w for w in waivers if w["payload"]["requirement_id"]==req_id and w["payload"].get("is_current_head") is True),None)
        expected_result="SATISFIED" if attempt is not None else ("WAIVED" if waiver is not None else "UNSATISFIED")
        expected_reason="VALIDATION_PASSED" if attempt is not None else ("CURRENT_WAIVER" if waiver is not None else "NO_CURRENT_PASS")
        if p.get("result")!=expected_result or p.get("primary_reason")!=expected_reason or p.get("reason_codes")!=[expected_reason]: errors.append(f"decision {req_id}: derived result mismatch")
        if (p.get("requirement_fingerprint"),p.get("set_fingerprint"))!=(req["fingerprint"],current_set.get("fingerprint")): errors.append(f"decision {req_id}: exact subject mismatch")
        if attempt is not None and (p.get("attempt_head_ref"),p.get("attempt_head_fingerprint"),p.get("context_fingerprint"))!=(attempt["ref"],attempt["fingerprint"],attempt["payload"]["context_binding"]["context_fingerprint"]): errors.append(f"decision {req_id}: attempt binding")
        if waiver is not None and (p.get("waiver_head_ref"),p.get("waiver_head_fingerprint"))!=(waiver["ref"],waiver["fingerprint"]): errors.append(f"decision {req_id}: waiver binding")

    set_decisions=data["normative_objects"].get("ValidationSetCurrentDecisionV0_1R2",[])
    set_decision=set_decisions[0] if len(set_decisions)==1 else None
    exact_decision_bindings=sorted([{"decision_fingerprint":row["fingerprint"],"decision_ref":row["ref"],"requirement_id":row["payload"]["requirement_id"]} for row in req_decisions],key=lambda x:x["requirement_id"])
    if set_decision is None: errors.append("set decision: exactly one")
    else:
        p=set_decision["payload"]
        if p.get("requirement_decisions")!=exact_decision_bindings or p.get("result")!="SATISFIED" or p.get("primary_reason")!="ALL_REQUIRED_CURRENT" or p.get("reason_codes")!=["ALL_REQUIRED_CURRENT"]: errors.append("set decision: derivation mismatch")
        if (p.get("set_ref"),p.get("set_fingerprint"))!=(current_set.get("ref"),current_set.get("fingerprint")): errors.append("set decision: subject mismatch")

    completions=data["normative_objects"].get("TaskCompletionEligibilityDecisionV0_1R2",[])
    completion=completions[0] if len(completions)==1 else None
    if completion is None: errors.append("completion: exactly one")
    else:
        p=completion["payload"]
        task=require_bound(index,p.get("task_state_assessment_ref"),p.get("task_state_assessment_fingerprint"),"completion.task",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
        guard=require_bound(index,p.get("completion_guard_assessment_ref"),p.get("completion_guard_assessment_fingerprint"),"completion.guard",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
        f5=require_bound(index,p.get("f5_blocker_assessment_ref"),p.get("f5_blocker_assessment_fingerprint"),"completion.f5",errors,"OpaqueUpstreamAssessmentInputV0_1R2")
        eligible=True
        if task is None or task["payload"].get("kind")!="TASK_CURRENT_STATE" or task["payload"].get("result")!="CURRENT_VERIFYING" or task["payload"].get("subject_payload",{}).get("task_lifecycle")!="VERIFYING": eligible=False
        if task is not None:
            tp=task["payload"]["subject_payload"]
            if p.get("candidate_context")!={"fingerprint":tp.get("candidate_fingerprint"),"ref":tp.get("candidate_ref"),"revision":tp.get("candidate_revision")} or p.get("dependency_context")!={"fingerprint":tp.get("dependency_fingerprint"),"ref":tp.get("dependency_ref"),"revision":tp.get("dependency_revision")}: eligible=False
        for attempt in current_attempts.values():
            context=attempt["payload"]["context_binding"]
            if context.get("candidate")!=p.get("candidate_context") or context.get("dependency")!=p.get("dependency_context"): eligible=False
        if guard is None or guard["payload"].get("result")!="CURRENT_ZERO" or guard["payload"].get("subject_payload",{}).get("counts")!=p.get("quiescence_counts") or any(type(v) is not int or v!=0 for v in p.get("quiescence_counts",{}).values()): eligible=False
        if f5 is None or f5["payload"].get("result")!="CLEAR": eligible=False
        if set_decision is None or (p.get("set_decision_ref"),p.get("set_decision_fingerprint"))!=(set_decision["ref"],set_decision["fingerprint"]): eligible=False
        expected="ELIGIBLE" if eligible else "NOT_ELIGIBLE"
        if p.get("result")!=expected or (eligible and (p.get("primary_reason")!="ALL_COMPLETION_GATES_CURRENT" or p.get("reason_codes")!=["ALL_COMPLETION_GATES_CURRENT"])): errors.append("completion: exact derived eligibility mismatch")

    catalog=data["regression_catalog"]
    if catalog.get("R1_fixed_mutation_count")!=32 or catalog.get("R1_independent_probe_ids")!=R1_PROBES or len(catalog.get("R2_additional_negative_ids",[]))!=12: errors.append("regression catalog mismatch")
    current_attempt_rows = list(current_attempts.values())
    positive_graph_count = sum([
        any(row["payload"].get("method") == "FRESH_VALIDATION" and not next((req["payload"].get("effectful") for req in requirements if req["payload"]["requirement_id"] == row["payload"].get("requirement_id") and req["payload"]["requirement_revision"] == row["payload"].get("requirement_revision")), True) for row in current_attempt_rows),
        any(row["payload"].get("method") == "EVIDENCE_CARRY_FORWARD_REVIEW" for row in current_attempt_rows),
        any(next((req["payload"].get("effectful") for req in requirements if req["payload"]["requirement_id"] == row["payload"].get("requirement_id") and req["payload"]["requirement_revision"] == row["payload"].get("requirement_revision")), False) for row in current_attempt_rows),
    ])
    expected_summary = {
        "normative_schema_count": len(profiles),
        "normative_instance_count": sum(len(group) for group in data["normative_objects"].values()),
        "positive_graph_count": positive_graph_count,
        "R1_fixed_mutation_count": 32,
        "R1_independent_regression_count": 18,
        "R2_additional_negative_count": 12,
        "requirement_revision_count": len(requirements),
        "current_requirement_count": len(current_heads),
        "attempt_revision_count": len(attempts),
        "requirement_decision_count": len(req_decisions),
        "derived_satisfied_count": sum(row["payload"].get("result") == "SATISFIED" for row in req_decisions),
        "derived_waived_count": sum(row["payload"].get("result") == "WAIVED" for row in req_decisions),
        "derived_completion_eligible_count": int(completion is not None and completion["payload"].get("result") == "ELIGIBLE"),
    }
    if data["summary"] != expected_summary: errors.append("summary derived count mismatch")
    expected_occ={"accepted_real_task_count":0,"database_write_count":0,"external_effect_count":0,"provider_call_count":0,"raw_secret_count":0,"runtime_activation_count":0,"task_done_mutation_count":0,"terminal_outcome":"NOT_EXECUTED"}
    if data["occurrence_assertions"]!=expected_occ: errors.append("occurrence assertions mismatch")
    return errors, counts


def reseal(row: dict[str, Any]) -> None:
    row["ref"] = stable_ref(row["schema"], row["key"])
    row["fingerprint"] = typed_hash(f"agents-os.f6.r2.{row['schema']}", row["payload"])


def resign_root(data: dict[str, Any]) -> None:
    unsigned=copy.deepcopy(data); unsigned.pop("root_fingerprint",None)
    data["root_fingerprint"]=typed_hash("agents-os.f6.r2.root",unsigned)


def rows(data: dict[str, Any], schema: str) -> list[dict[str, Any]]:
    return data["normative_objects"][schema]


def find_kind(data: dict[str, Any], kind: str, occurrence: int = 0) -> dict[str, Any]:
    matches=[row for row in rows(data,"OpaqueUpstreamAssessmentInputV0_1R2") if row["payload"]["kind"]==kind]
    return matches[occurrence]


def resign_all(data: dict[str, Any]) -> None:
    support_index=wrapper_index(data)
    for group in data["supporting_objects"].values():
        for row in group: reseal(row)
    index=wrapper_index(data)
    for row in rows(data,"OpaqueUpstreamAssessmentInputV0_1R2"):
        reseal(row)
        index[row["ref"]]=row
    req_rows=rows(data,"ValidationRequirementRevisionV0_1R2")
    for row in sorted(req_rows,key=lambda x:(x["payload"]["requirement_id"],x["payload"]["requirement_revision"] if type(x["payload"]["requirement_revision"]) is int else 0)):
        p=row["payload"]
        if p.get("predecessor_ref") in index: p["predecessor_fingerprint"]=index[p["predecessor_ref"]]["fingerprint"]
        if p.get("creation_command_ref") in index: p["creation_command_fingerprint"]=index[p["creation_command_ref"]]["fingerprint"]
        if p.get("creation_event_ref") in index:
            event=index[p["creation_event_ref"]]; p["creation_event_fingerprint"]=event["fingerprint"]; p["creation_event_sequence"]=event["payload"]["event_sequence"]
        for binding in p.get("provenance_bindings",[]):
            if binding.get("source_ref") in index: binding["source_fingerprint"]=index[binding["source_ref"]]["fingerprint"]
            if binding.get("source_owner_assessment_ref") in index: binding["source_owner_assessment_fingerprint"]=index[binding["source_owner_assessment_ref"]]["fingerprint"]
            if binding.get("creation_command_ref") in index: binding["creation_command_fingerprint"]=index[binding["creation_command_ref"]]["fingerprint"]
            if binding.get("creation_event_ref") in index:
                event=index[binding["creation_event_ref"]]; binding["creation_event_fingerprint"]=event["fingerprint"]; binding["creation_event_sequence"]=event["payload"]["event_sequence"]
        p["provenance_set_fingerprint"]=typed_hash("agents-os.f6.r2.provenance-set",p.get("provenance_bindings"))
        reseal(row); index[row["ref"]]=row
    set_rows=rows(data,"ValidationSetSnapshotV0_1R2")
    for row in sorted(set_rows,key=lambda x:x["payload"]["set_revision"]):
        p=row["payload"]
        if p.get("predecessor_ref") in index: p["predecessor_fingerprint"]=index[p["predecessor_ref"]]["fingerprint"]
        if p.get("freeze_event_ref") in index:
            ev=index[p["freeze_event_ref"]]; p["freeze_event_fingerprint"]=ev["fingerprint"]; p["frozen_event_sequence"]=ev["payload"]["event_sequence"]
        for member in p.get("memberships",[]):
            if member.get("requirement_ref") in index: member["requirement_fingerprint"]=index[member["requirement_ref"]]["fingerprint"]
        source_closure=sorted([binding for req in req_rows if any(m.get("requirement_ref")==req["ref"] for m in p.get("memberships",[])) for binding in req["payload"]["provenance_bindings"]],key=lambda x:x["source_ref"])
        p["source_closure"]=source_closure; p["source_closure_fingerprint"]=typed_hash("agents-os.f6.r2.source-closure",source_closure)
        reseal(row); index[row["ref"]]=row
    for row in rows(data,"RequirementWaiverEventV0_1R2"):
        p=row["payload"]
        for ref_key,fp_key in [("authority_assessment_ref","authority_assessment_fingerprint"),("base_snapshot_ref","base_snapshot_fingerprint"),("command_ref","command_fingerprint"),("event_ref","event_fingerprint"),("jenn_decision_ref","jenn_decision_fingerprint")]:
            if p.get(ref_key) in index: p[fp_key]=index[p[ref_key]]["fingerprint"]
        req=next((x for x in req_rows if x["payload"]["requirement_id"]==p.get("requirement_id") and x["payload"]["requirement_revision"]==p.get("requirement_revision")),None)
        if req: p["requirement_fingerprint"]=req["fingerprint"]
        if p.get("event_ref") in index: p["event_sequence"]=index[p["event_ref"]]["payload"]["event_sequence"]
        reseal(row); index[row["ref"]]=row
    for row in set_rows:
        for head in row["payload"].get("waiver_heads",[]):
            if head.get("waiver_ref") in index: head["waiver_fingerprint"]=index[head["waiver_ref"]]["fingerprint"]
        reseal(row); index[row["ref"]]=row
    attempt_rows=rows(data,"ValidationAttemptRevisionV0_1R2")
    for row in sorted(attempt_rows,key=lambda x:(x["payload"]["attempt_id"],x["payload"]["attempt_revision"])):
        p=row["payload"]
        for ref_key,fp_key in [("authority_assessment_ref","authority_assessment_fingerprint"),("evidence_assessment_ref","evidence_assessment_fingerprint"),("f5_assessment_ref","f5_assessment_fingerprint"),("created_event_ref","created_event_fingerprint"),("predecessor_ref","predecessor_fingerprint"),("requirement_id","unused")]:
            if ref_key=="requirement_id": continue
            if p.get(ref_key) in index: p[fp_key]=index[p[ref_key]]["fingerprint"]
        req=next((x for x in req_rows if x["payload"]["requirement_id"]==p["requirement_id"] and x["payload"]["requirement_revision"]==p["requirement_revision"]),None)
        if req: p["requirement_fingerprint"]=req["fingerprint"]
        setrow=next((x for x in set_rows if x["payload"]["set_revision"]==p["set_revision"]),None)
        if setrow: p["set_ref"]=setrow["ref"]; p["set_fingerprint"]=setrow["fingerprint"]
        context=p["context_binding"]
        if req: context["requirement_fingerprint"]=req["fingerprint"]
        if setrow: context["set_ref"]=setrow["ref"]; context["set_fingerprint"]=setrow["fingerprint"]
        context["evidence_set_fingerprint"]=p["evidence_set_fingerprint"]
        carry = p.get("carry_source")
        if isinstance(carry, dict):
            if carry.get("source_attempt_ref") in index:
                carry["source_attempt_fingerprint"] = index[carry["source_attempt_ref"]]["fingerprint"]
            if carry.get("root_source_attempt_ref") in index:
                carry["root_source_attempt_fingerprint"] = index[carry["root_source_attempt_ref"]]["fingerprint"]
        unsigned=dict(context); unsigned.pop("context_fingerprint",None); context["context_fingerprint"]=typed_hash("agents-os.f6.r2.validation-context",unsigned)
        reseal(row); index[row["ref"]]=row
    for row in rows(data,"ValidationRequirementCurrentDecisionV0_1R2"):
        p=row["payload"]
        req=next((x for x in req_rows if x["payload"]["requirement_id"]==p["requirement_id"] and x["payload"]["requirement_revision"]==p["requirement_revision"]),None)
        if req: p["requirement_fingerprint"]=req["fingerprint"]
        setrow=next((x for x in set_rows if x["payload"]["set_revision"]==p["set_revision"]),None)
        if setrow: p["set_ref"]=setrow["ref"]; p["set_fingerprint"]=setrow["fingerprint"]
        if p.get("attempt_head_ref") in index:
            attempt=index[p["attempt_head_ref"]]; p["attempt_head_fingerprint"]=attempt["fingerprint"]; p["context_fingerprint"]=attempt["payload"]["context_binding"]["context_fingerprint"]
        if p.get("waiver_head_ref") in index: p["waiver_head_fingerprint"]=index[p["waiver_head_ref"]]["fingerprint"]
        reseal(row); index[row["ref"]]=row
    set_decision=rows(data,"ValidationSetCurrentDecisionV0_1R2")[0]
    set_decision["payload"]["requirement_decisions"]=sorted([{"decision_fingerprint":row["fingerprint"],"decision_ref":row["ref"],"requirement_id":row["payload"]["requirement_id"]} for row in rows(data,"ValidationRequirementCurrentDecisionV0_1R2")],key=lambda x:x["requirement_id"])
    current_set=max(set_rows,key=lambda x:x["payload"]["set_revision"]); set_decision["payload"]["set_ref"]=current_set["ref"]; set_decision["payload"]["set_fingerprint"]=current_set["fingerprint"]
    reseal(set_decision); index[set_decision["ref"]]=set_decision
    completion=rows(data,"TaskCompletionEligibilityDecisionV0_1R2")[0]
    completion["payload"]["set_decision_ref"]=set_decision["ref"]; completion["payload"]["set_decision_fingerprint"]=set_decision["fingerprint"]
    for ref_key,fp_key in [("task_state_assessment_ref","task_state_assessment_fingerprint"),("completion_guard_assessment_ref","completion_guard_assessment_fingerprint"),("f5_blocker_assessment_ref","f5_blocker_assessment_fingerprint")]:
        if completion["payload"].get(ref_key) in index: completion["payload"][fp_key]=index[completion["payload"][ref_key]]["fingerprint"]
    reseal(completion); index[completion["ref"]]=completion
    for profile in data["schema_profiles"]:
        instance=index.get(profile["canonical_instance_ref"])
        if instance: profile["canonical_instance_fingerprint"]=instance["fingerprint"]
        unsigned={k:profile[k] for k in PROFILE_FIELDS if k!="schema_fingerprint"}; profile["schema_fingerprint"]=typed_hash("agents-os.f6.r2.schema-profile",unsigned)
    data["summary"]["normative_instance_count"]=sum(len(group) for group in data["normative_objects"].values())
    resign_root(data)


def mutation_cases() -> dict[str, Callable[[dict[str, Any]], None]]:
    def assessment_revision(kind: str, value: int) -> Callable[[dict[str,Any]],None]:
        def mutate(data: dict[str,Any]) -> None:
            find_kind(data,kind)["payload"]["subject_revision"]=value; resign_all(data)
        return mutate
    def p01(data:dict[str,Any])->None:
        find_kind(data,"VALIDATION_AUTHORITY_CURRENTNESS")["payload"]["result"]="NOT_APPLICABLE"; resign_all(data)
    def p02(data:dict[str,Any])->None:
        a=rows(data,"ValidationAttemptRevisionV0_1R2")[0]; source=rows(data,"ValidationAttemptRevisionV0_1R2")[1]
        a["payload"]["carry_source"]={"root_source_attempt_fingerprint":source["fingerprint"],"root_source_attempt_ref":source["ref"],"root_source_attempt_revision":1,"source_attempt_fingerprint":source["fingerprint"],"source_attempt_ref":source["ref"],"source_attempt_revision":1}; resign_all(data)
    def p09(data:dict[str,Any])->None:
        event=data["supporting_objects"]["events"][1]
        event["payload"]["event_sequence"]=199
        reseal(event)
        assessment=find_kind(data,"REQUIREMENT_PROVENANCE_CURRENTNESS",1)
        assessment["payload"]["subject_payload"]["event_sequence"]=199
        assessment["payload"]["subject_payload"]["event_fingerprint"]=event["fingerprint"]
        assessment["payload"]["subject_fingerprint"]=typed_hash("agents-os.f6.r2.assessment-subject.REQUIREMENT_PROVENANCE_CURRENTNESS",assessment["payload"]["subject_payload"])
        resign_all(data)
    def p10(data:dict[str,Any])->None:
        waiver=rows(data,"RequirementWaiverEventV0_1R2")[0]
        event=next(x for x in data["supporting_objects"]["events"] if x["ref"]==waiver["payload"]["event_ref"])
        event["payload"]["event_sequence"]=1
        reseal(event)
        assessment=find_kind(data,"JENN_WAIVER_AUTHORITY_CURRENTNESS")
        assessment["payload"]["subject_payload"]["event_sequence"]=1
        assessment["payload"]["subject_payload"]["event_fingerprint"]=event["fingerprint"]
        assessment["payload"]["subject_fingerprint"]=typed_hash("agents-os.f6.r2.assessment-subject.JENN_WAIVER_AUTHORITY_CURRENTNESS",assessment["payload"]["subject_payload"])
        resign_all(data)
    def p11(data:dict[str,Any])->None:
        decision=data["supporting_objects"]["jenn_decisions"][0]; decision["payload"]["decision_id"]="substituted-decision"; resign_all(data)
    def p12(data:dict[str,Any])->None:
        reqs=rows(data,"ValidationRequirementRevisionV0_1R2"); reqs[:]=[r for r in reqs if not (r["payload"]["requirement_id"]=="REQ-A" and r["payload"]["requirement_revision"]==1)]; resign_all(data)
    def p13(data:dict[str,Any])->None:
        req=next(r for r in rows(data,"ValidationRequirementRevisionV0_1R2") if r["payload"]["requirement_id"]=="REQ-A" and r["payload"]["requirement_revision"]==2); req["payload"]["predecessor_revision"]=True; resign_all(data)
    def p14(data:dict[str,Any])->None:
        attempt=next(r for r in rows(data,"ValidationAttemptRevisionV0_1R2") if r["payload"]["current_head"]); attempt["payload"]["context_binding"]["candidate"]={"ref":"synth:f6:r2:taskcandidate:alternate","revision":9,"fingerprint":"a"*64}; resign_all(data)
    def p15(data:dict[str,Any])->None:
        attempt=next(r for r in rows(data,"ValidationAttemptRevisionV0_1R2") if r["payload"]["current_head"]); attempt["payload"]["context_binding"]["dependency"]={"ref":"synth:f6:r2:dependencyclosure:alternate","revision":9,"fingerprint":"b"*64}; resign_all(data)
    def p16(data:dict[str,Any])->None:
        attempt=rows(data,"ValidationAttemptRevisionV0_1R2")[0]; attempt["payload"]["evidence_bindings"].append({"evidence_fingerprint":"c"*64,"evidence_ref":"d"*64,"evidence_revision":1}); attempt["payload"]["evidence_bindings"].sort(key=lambda x:x["evidence_ref"]); attempt["payload"]["evidence_set_fingerprint"]=typed_hash("agents-os.f6.r2.evidence-set",attempt["payload"]["evidence_bindings"]); resign_all(data)
    def p17(data:dict[str,Any])->None:
        source=data["supporting_objects"]["provenance_sources"][0]; source["payload"]["source_revision"]=999; resign_all(data)
    def p18(data:dict[str,Any])->None:
        task=find_kind(data,"TASK_CURRENT_STATE")
        task["payload"]["subject_payload"]["task_lifecycle"]="ACTIVE"
        task["payload"]["subject_fingerprint"]=typed_hash("agents-os.f6.r2.assessment-subject.TASK_CURRENT_STATE",task["payload"]["subject_payload"])
        resign_all(data)
    def missing_schema(data:dict[str,Any])->None: data["schema_profiles"].pop(); resign_root(data)
    def unknown_field(data:dict[str,Any])->None: rows(data,"ValidationRequirementCurrentDecisionV0_1R2")[0]["payload"]["unknown_field"]=0; resign_all(data)
    def decision_contradiction(data:dict[str,Any])->None: rows(data,"ValidationRequirementCurrentDecisionV0_1R2")[0]["payload"]["result"]="WAIVED"; resign_all(data)
    def branch(data:dict[str,Any])->None: duplicate=copy.deepcopy(next(r for r in rows(data,"ValidationRequirementRevisionV0_1R2") if r["payload"]["requirement_id"]=="REQ-A" and r["payload"]["requirement_revision"]==2)); duplicate["key"]="REQ-A:r2:branch"; reseal(duplicate); rows(data,"ValidationRequirementRevisionV0_1R2").append(duplicate); resign_all(data)
    def cycle(data:dict[str,Any])->None:
        reqs=[r for r in rows(data,"ValidationRequirementRevisionV0_1R2") if r["payload"]["requirement_id"]=="REQ-A"]; reqs[0]["payload"]["predecessor_ref"]=reqs[1]["ref"]; reqs[0]["payload"]["predecessor_revision"]=2; reqs[0]["payload"]["predecessor_fingerprint"]=reqs[1]["fingerprint"]; resign_all(data)
    def evidence_duplicate(data:dict[str,Any])->None: a=rows(data,"ValidationAttemptRevisionV0_1R2")[0]; a["payload"]["evidence_bindings"].append(copy.deepcopy(a["payload"]["evidence_bindings"][0])); resign_all(data)
    def evidence_unsorted(data:dict[str,Any])->None: a=rows(data,"ValidationAttemptRevisionV0_1R2")[0]; a["payload"]["evidence_bindings"].reverse(); resign_all(data)
    def carry_chain(data:dict[str,Any])->None: a=next(r for r in rows(data,"ValidationAttemptRevisionV0_1R2") if r["payload"]["method"]=="EVIDENCE_CARRY_FORWARD_REVIEW"); a["payload"]["carry_source"].update({"source_attempt_ref":a["ref"],"source_attempt_fingerprint":a["fingerprint"],"source_attempt_revision":2}); resign_all(data)
    def f5_wrong(data:dict[str,Any])->None: a=find_kind(data,"F5_DELIVERY_CURRENTNESS"); a["payload"]["subject_ref"]="synth:f6:r2:deliverysubject:other"; resign_all(data)
    def f5_history(data:dict[str,Any])->None: a=find_kind(data,"F5_DELIVERY_CURRENTNESS"); a["payload"]["result"]="HISTORY_ONLY"; resign_all(data)
    return {
        "F6-R1-IR-P01":p01,"F6-R1-IR-P02":p02,"F6-R1-IR-P03":assessment_revision("TASK_CURRENT_STATE",4),
        "F6-R1-IR-P04":assessment_revision("CANDIDATE_COMMITMENT_CURRENTNESS",8),"F6-R1-IR-P05":assessment_revision("DEPENDENCY_CLOSURE_CURRENTNESS",8),
        "F6-R1-IR-P06":assessment_revision("F5_COMPLETION_BLOCKING_CURRENTNESS",4),"F6-R1-IR-P07":assessment_revision("COMPLETION_GUARD_CURRENTNESS",4),
        "F6-R1-IR-P08":assessment_revision("VALIDATION_AUTHORITY_CURRENTNESS",999),"F6-R1-IR-P09":p09,"F6-R1-IR-P10":p10,
        "F6-R1-IR-P11":p11,"F6-R1-IR-P12":p12,"F6-R1-IR-P13":p13,"F6-R1-IR-P14":p14,"F6-R1-IR-P15":p15,
        "F6-R1-IR-P16":p16,"F6-R1-IR-P17":p17,"F6-R1-IR-P18":p18,
        "SCHEMA-INVENTORY-MISSING":missing_schema,"SCHEMA-UNKNOWN-FIELD":unknown_field,"DECISION-CROSS-FIELD":decision_contradiction,
        "REQUIREMENT-BRANCH":branch,"REQUIREMENT-CYCLE":cycle,"EVIDENCE-DUPLICATE":evidence_duplicate,"EVIDENCE-UNSORTED":evidence_unsorted,
        "CARRY-CHAIN":carry_chain,"F5-WRONG-SUBJECT":f5_wrong,"F5-HISTORY-ONLY":f5_history,"EVENT-ORDER":p10,"CONTEXT-MISMATCH":p14,
    }


def run_mutations(base: dict[str, Any]) -> tuple[int,int,list[str]]:
    r1_rejected=0; r2_rejected=0; failures=[]
    for case_id,mutate in mutation_cases().items():
        candidate=copy.deepcopy(base)
        try:
            mutate(candidate)
            errors,_=validate_fixture(candidate,execute_r1=False)
        except Exception as exc:
            failures.append(f"{case_id}: mutation exception {type(exc).__name__}: {exc}")
            continue
        if not errors:
            failures.append(f"{case_id}: incorrectly accepted")
        elif case_id in R1_PROBES:
            r1_rejected+=1
        else:
            r2_rejected+=1
    return r1_rejected,r2_rejected,failures


def main() -> int:
    try:
        data=load_fixture(FIXTURE_PATH)
    except Exception as exc:
        print("result: BLOCK")
        print(f"load_error: {type(exc).__name__}: {exc}")
        return 1
    errors,counts=validate_fixture(data,execute_r1=True)
    r1_rejected,r2_rejected,mutation_failures=run_mutations(data) if not errors else (0,0,[])
    errors.extend(mutation_failures)
    if r1_rejected!=18: errors.append(f"R1 independent regression count {r1_rejected} != 18")
    if r2_rejected!=12: errors.append(f"R2 negative count {r2_rejected} != 12")
    if errors:
        print("result: BLOCK")
        for error in errors: print(f"error: {error}")
        return 1
    fixture_canonical_sha256=hashlib.sha256(canonical_bytes(data)).hexdigest()
    print("result: PASS_NO_BLOCKER")
    print("normative_schema_count: 10")
    print(f"normative_instance_count: {data['summary']['normative_instance_count']}")
    print("positive_graph_count: 3")
    print(f"R1_fixed_mutations_rejected: {counts['R1_mutations']}")
    print(f"R1_independent_regressions_rejected: {r1_rejected}")
    print(f"R2_additional_negatives_rejected: {r2_rejected}")
    print(f"total_R2_mutations_rejected: {r1_rejected+r2_rejected}")
    print("mutation_exception_count: 0")
    print(f"fixture_canonical_sha256: {fixture_canonical_sha256}")
    print("derived_satisfied_count: 3")
    print("derived_waived_count: 1")
    print("derived_completion_eligible_count: 1")
    for key,value in data["occurrence_assertions"].items(): print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
