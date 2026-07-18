#!/usr/bin/env python3
"""Validate the synthetic F6 R4 five-finding consistency closure witness."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = WORKSPACE_ROOT / "control-plane/registry/examples/2026-07-18-agents-os-f6-r4-five-finding-consistency-closure-v0.1.json"
R3_VALIDATOR_PATH = WORKSPACE_ROOT / "control-plane/registry/validate-f6-r3-eight-finding-semantic-closure.py"
R3_BUILDER_PATH = WORKSPACE_ROOT / "control-plane/registry/build-f6-r3-eight-finding-semantic-closure.py"
R4_BUILDER_PATH = WORKSPACE_ROOT / "control-plane/registry/build-f6-r4-five-finding-consistency-closure.py"

TOP_FIELDS = {
    "schema_version", "environment", "runtime_usable", "r3_bindings", "r3_fixture",
    "task_identity_bindings", "consumer_assessment_bindings", "waiver_time_bindings",
    "evidence_subject_bindings", "strict_event_edges", "regression_catalog",
    "occurrence_assertions", "root_fingerprint",
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R3V = load_module("f6_r3_validator_for_r4_validation", R3_VALIDATOR_PATH)
R3B = load_module("f6_r3_builder_for_r4_validation", R3_BUILDER_PATH)
R4B = load_module("f6_r4_builder_for_regression_signing", R4_BUILDER_PATH)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def typed_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode() + b"\x00" + canonical_bytes(value)).hexdigest()


def rows(effective: dict[str, Any], schema: str) -> list[dict[str, Any]]:
    return effective["normative_objects"][schema]


def bind(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result["binding_fingerprint"] = typed_hash(domain, result)
    return result


def derive_task_bindings(effective: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    index = R3V.wrapper_index(effective)
    task = R3V.find_kind(effective, "TASK_CURRENT_STATE")
    task_id = task["payload"]["subject_payload"].get("task_id")
    result = [bind("agents-os.f6.r4.task-identity", {
        "consumer_kind": "F1_TASK_ASSESSMENT", "consumer_ref": task["ref"],
        "consumer_revision": task["payload"]["assessment_revision"], "task_id": task_id,
    })]
    requirements = rows(effective, "ValidationRequirementRevisionV0_1R2")
    requirement_index = {(r["payload"]["requirement_id"], r["payload"]["requirement_revision"]): r for r in requirements}
    for requirement in requirements:
        rp = requirement["payload"]
        if rp.get("task_id") != task_id:
            errors.append(f"semantic: {requirement['key']} Task identity mismatch")
        result.append(bind("agents-os.f6.r4.task-identity", {"consumer_kind":"REQUIREMENT","consumer_ref":requirement["ref"],"consumer_revision":rp["requirement_revision"],"task_id":rp.get("task_id")}))
    set_tasks: dict[str, str] = {}
    for snapshot in rows(effective, "ValidationSetSnapshotV0_1R2"):
        member_tasks = {index[m["requirement_ref"]]["payload"].get("task_id") for m in snapshot["payload"]["memberships"] if m["requirement_ref"] in index}
        derived = next(iter(member_tasks)) if len(member_tasks) == 1 else "INDETERMINATE"
        if derived != task_id or len(snapshot["payload"]["memberships"]) == 0:
            errors.append(f"semantic: {snapshot['key']} mixed or detached Task identity")
        set_tasks[snapshot["ref"]] = derived
        result.append(bind("agents-os.f6.r4.task-identity", {"consumer_kind":"VALIDATION_SET","consumer_ref":snapshot["ref"],"consumer_revision":snapshot["payload"]["set_revision"],"task_id":derived}))
    for attempt in rows(effective, "ValidationAttemptRevisionV0_1R2"):
        ap = attempt["payload"]
        requirement = requirement_index.get((ap["requirement_id"], ap["requirement_revision"]))
        derived = None if requirement is None else requirement["payload"].get("task_id")
        if derived != task_id or set_tasks.get(ap["set_ref"]) != task_id:
            errors.append(f"semantic: {attempt['key']} Task identity mismatch")
        result.append(bind("agents-os.f6.r4.task-identity", {"consumer_kind":"ATTEMPT","consumer_ref":attempt["ref"],"consumer_revision":ap["attempt_revision"],"task_id":derived}))
    completion = rows(effective, "TaskCompletionEligibilityDecisionV0_1R2")[0]
    if completion["payload"].get("task_id") != task_id:
        errors.append("semantic: completion Task identity mismatch")
    result.append(bind("agents-os.f6.r4.task-identity", {"consumer_kind":"COMPLETION","consumer_ref":completion["ref"],"consumer_revision":1,"task_id":completion["payload"].get("task_id")}))
    return sorted(result, key=lambda x: (x["consumer_kind"], x["consumer_ref"]))


def derive_consumer_assessments(effective: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    index = R3V.wrapper_index(effective)
    result: list[dict[str, Any]] = []
    def walk(value: Any, path: str) -> None:
        if isinstance(value, list):
            for i, item in enumerate(value): walk(item, f"{path}[{i}]")
        elif isinstance(value, dict):
            for key in sorted(value):
                if key.endswith("_assessment_ref"):
                    prefix = key[:-4]; ref = value[key]; resolved = index.get(ref)
                    actual_fp = None if resolved is None else resolved["fingerprint"]
                    actual_rev = None if resolved is None else resolved["payload"].get("assessment_revision")
                    declared_fp = value.get(prefix + "_fingerprint")
                    declared_rev = value.get(prefix + "_revision")
                    null_tuple = ref is None and declared_fp is None and declared_rev is None
                    if not null_tuple and (resolved is None or declared_fp != actual_fp or declared_rev != actual_rev):
                        errors.append(f"semantic: consumer assessment tuple mismatch at {path}.{prefix}")
                    result.append(bind("agents-os.f6.r4.consumer-assessment", {
                        "consumer_path":f"{path}.{prefix}","assessment_ref":ref,
                        "declared_fingerprint":declared_fp,"declared_revision":declared_rev,
                        "resolved_fingerprint":actual_fp,"resolved_revision":actual_rev,
                    }))
                walk(value[key], f"{path}.{key}")
    walk(effective["normative_objects"], "$.normative_objects")
    return sorted(result, key=lambda x: x["consumer_path"])


def derive_waiver_time(effective: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    trusted = rows(effective, "TrustedTimeInputV0_1R2")[0]
    observed = trusted["payload"]["observed_event_sequence"]
    result = []
    for waiver in rows(effective, "RequirementWaiverEventV0_1R2"):
        wp = waiver["payload"]
        current = wp["valid_from_sequence"] <= observed < wp["expires_at_sequence"] and wp["is_current_head"] is True
        if not current:
            errors.append("semantic: waiver is not current at TrustedTime")
        result.append(bind("agents-os.f6.r4.waiver-time", {
            "trusted_time_ref":trusted["ref"],"trusted_time_fingerprint":trusted["fingerprint"],"trusted_time_revision":trusted["payload"]["trusted_time_revision"],
            "observed_event_sequence":observed,"waiver_ref":waiver["ref"],"waiver_revision":wp["waiver_revision"],
            "valid_from_sequence":wp["valid_from_sequence"],"expires_at_sequence":wp["expires_at_sequence"],"derived_current":current,
        }))
    return result


def derive_evidence_subjects(effective: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    index = R3V.wrapper_index(effective); result = []
    for attempt in rows(effective, "ValidationAttemptRevisionV0_1R2"):
        ap = attempt["payload"]
        for item in ap["evidence_bindings"]:
            evidence = index.get(item["evidence_ref"])
            if evidence is None:
                errors.append(f"semantic: {attempt['key']} evidence unresolved"); continue
            if evidence["payload"].get("validation_subject") != ap["requirement_id"]:
                errors.append(f"semantic: {attempt['key']} evidence validates another Requirement")
            result.append(bind("agents-os.f6.r4.evidence-subject", {
                "attempt_ref":attempt["ref"],"attempt_revision":ap["attempt_revision"],"context_fingerprint":ap["context_binding"]["context_fingerprint"],
                "evidence_assessment_ref":item["evidence_assessment_ref"],"evidence_assessment_fingerprint":item["evidence_assessment_fingerprint"],"evidence_assessment_revision":item["evidence_assessment_revision"],
                "evidence_ref":evidence["ref"],"evidence_revision":evidence["payload"]["evidence_revision"],
                "requirement_id":ap["requirement_id"],"requirement_revision":ap["requirement_revision"],"requirement_fingerprint":ap["requirement_fingerprint"],
                "validation_subject":evidence["payload"].get("validation_subject"),
            }))
    return sorted(result, key=lambda x: (x["attempt_ref"], x["evidence_ref"]))


def derive_strict_edges(effective: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    index = R3V.wrapper_index(effective); result = []
    for attempt in rows(effective, "ValidationAttemptRevisionV0_1R2"):
        ap = attempt["payload"]
        pairs = []
        if ap["predecessor_ref"] is not None:
            pairs.append(("ATTEMPT_PREDECESSOR", index.get(ap["predecessor_ref"])))
        if ap["carry_source"] is not None:
            pairs.append(("CARRY_SOURCE", index.get(ap["carry_source"]["source_attempt_ref"])))
        for purpose, source in pairs:
            if source is None:
                errors.append(f"semantic: {purpose} source unresolved"); continue
            edge = bind("agents-os.f6.r4.strict-event-edge", {"purpose":purpose,"from_ref":source["payload"]["created_event_ref"],"from_sequence":source["payload"]["created_event_sequence"],"to_ref":ap["created_event_ref"],"to_sequence":ap["created_event_sequence"],"relation":"LT"})
            if edge["from_sequence"] >= edge["to_sequence"]:
                errors.append(f"semantic: {purpose} Event order is not strict")
            result.append(edge)
    return sorted(result, key=lambda x: (x["purpose"], x["from_ref"], x["to_ref"]))


def validate_fixture(data: Any, *, execute_fixed: bool = False) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []; counts = {"R1_fixed":0,"R1_independent":0,"R2_additional":0,"R2_coordinated":0}
    if not isinstance(data, dict) or set(data) != TOP_FIELDS:
        return ["schema: R4 root fields mismatch"], counts
    if data["schema_version"] != "agents-os.f6.validation-current-decision-r4-proof.v0.1" or data["environment"] != "SYNTHETIC_TEST" or data["runtime_usable"] is not False:
        errors.append("semantic: R4 synthetic boundary mismatch")
    unsigned = copy.deepcopy(data); root = unsigned.pop("root_fingerprint", None)
    if root != typed_hash("agents-os.f6.r4.root", unsigned): errors.append("integrity: R4 root fingerprint mismatch")
    if set(data["r3_bindings"]) != set(R4B.R3_PATHS): errors.append("integrity: R3 binding inventory mismatch")
    else:
        for key, path in R4B.R3_PATHS.items():
            actual = hashlib.sha256((WORKSPACE_ROOT / path).read_bytes()).hexdigest()
            if data["r3_bindings"][key] != {"path":path,"sha256":actual}: errors.append(f"integrity: R3 binding mismatch: {key}")
    r3 = data["r3_fixture"]
    r3_errors, old_counts = R3V.validate_fixture(r3, execute_fixed=execute_fixed)
    errors.extend(f"R3: {e}" for e in r3_errors)
    counts.update(old_counts)
    if execute_fixed and not r3_errors:
        rejected, exceptions, failures = R3V.run_coordinated_regressions(r3)
        counts["R2_coordinated"] = rejected
        errors.extend(f"R3 regression: {f}" for f in failures)
        if rejected != 17 or exceptions != 0: errors.append("R3 coordinated regression count mismatch")
    effective = r3["effective_fixture"]
    expected = derive_task_bindings(effective, errors)
    if data["task_identity_bindings"] != expected: errors.append("semantic: Task identity binding inventory mismatch")
    expected = derive_consumer_assessments(effective, errors)
    if data["consumer_assessment_bindings"] != expected: errors.append("semantic: consumer assessment inventory mismatch")
    expected = derive_waiver_time(effective, errors)
    if data["waiver_time_bindings"] != expected: errors.append("semantic: waiver time inventory mismatch")
    expected = derive_evidence_subjects(effective, errors)
    if data["evidence_subject_bindings"] != expected: errors.append("semantic: evidence subject inventory mismatch")
    expected = derive_strict_edges(effective, errors)
    if data["strict_event_edges"] != expected: errors.append("semantic: strict Event edge inventory mismatch")
    if data["regression_catalog"] != {"fixed_negative_total":62,"R2_coordinated_count":17,"R3_independent_case_count":7}: errors.append("integrity: regression catalog mismatch")
    if data["occurrence_assertions"] != r3["occurrence_assertions"]: errors.append("semantic: occurrence assertions mismatch")
    return errors, counts


def refresh_r3(r3: dict[str, Any]) -> None:
    effective = r3["effective_fixture"]
    R3V.R2V.resign_all(effective)
    R3B.close_attempt_events(effective)
    r3["schema_constraint_profiles"] = R3B.build_profiles(effective)
    r3["authority_root_bindings"] = R3B.build_authority_roots(effective)
    r3["context_assessment_bindings"] = R3B.build_context_bindings(effective)
    r3["attempt_commitments"] = R3B.build_attempt_commitments(effective)
    r3["event_order_edges"] = R3B.build_event_edges(effective)
    unsigned = copy.deepcopy(r3); unsigned.pop("root_fingerprint", None)
    r3["root_fingerprint"] = R3B.typed_hash("agents-os.f6.r3.root", unsigned)


def refresh_r4(data: dict[str, Any]) -> None:
    effective = data["r3_fixture"]["effective_fixture"]
    data["task_identity_bindings"] = R4B.task_identity_bindings(effective)
    data["consumer_assessment_bindings"] = R4B.consumer_assessment_bindings(effective)
    data["waiver_time_bindings"] = R4B.waiver_time_bindings(effective)
    data["evidence_subject_bindings"] = R4B.evidence_subject_bindings(effective)
    data["strict_event_edges"] = R4B.strict_event_edges(effective)
    unsigned = copy.deepcopy(data); unsigned.pop("root_fingerprint", None)
    data["root_fingerprint"] = typed_hash("agents-os.f6.r4.root", unsigned)


def cases() -> dict[str, Callable[[dict[str, Any]], None]]:
    def effective(d: dict[str, Any]) -> dict[str, Any]: return d["r3_fixture"]["effective_fixture"]
    def finish(d: dict[str, Any]) -> None: refresh_r3(d["r3_fixture"]); refresh_r4(d)
    def c01(d: dict[str, Any]) -> None:
        rows(effective(d), "TaskCompletionEligibilityDecisionV0_1R2")[0]["payload"]["task_id"] = "task:other"; finish(d)
    def c02(d: dict[str, Any]) -> None:
        for row in rows(effective(d), "ValidationRequirementRevisionV0_1R2"):
            if row["payload"]["requirement_id"] == "REQ-A": row["payload"]["task_id"] = "task:other"
        finish(d)
    def c03(d: dict[str, Any]) -> None:
        e = effective(d); evidence = e["supporting_objects"]["evidence_objects"][0]
        evidence["payload"]["validation_subject"] = "REQ-D"; R3V.R2V.reseal(evidence)
        for assessment in e["supporting_objects"]["evidence_assessments"]:
            if assessment["payload"]["subject_ref"] == evidence["ref"]:
                assessment["payload"]["subject_fingerprint"] = evidence["fingerprint"]; R3V.R2V.reseal(assessment)
                for attempt in rows(e, "ValidationAttemptRevisionV0_1R2"):
                    for binding in attempt["payload"]["evidence_bindings"]:
                        if binding["evidence_ref"] == evidence["ref"]:
                            binding["evidence_fingerprint"] = evidence["fingerprint"]
                            binding["evidence_assessment_fingerprint"] = assessment["fingerprint"]
                            R3V.sync_attempt_evidence(e, attempt)
        finish(d)
    def c04(d: dict[str, Any]) -> None:
        attempt = next(a for a in rows(effective(d), "ValidationAttemptRevisionV0_1R2") if a["payload"]["f5_assessment_ref"] is not None)
        attempt["payload"]["f5_assessment_revision"] = 999; finish(d)
    def c05(d: dict[str, Any]) -> None:
        for assessment in rows(effective(d), "OpaqueUpstreamAssessmentInputV0_1R2"):
            assessment["payload"]["assessment_revision"] += 1
        finish(d)
    def c06(d: dict[str, Any]) -> None:
        e = effective(d); waiver = rows(e, "RequirementWaiverEventV0_1R2")[0]
        rows(e, "TrustedTimeInputV0_1R2")[0]["payload"]["observed_event_sequence"] = waiver["payload"]["expires_at_sequence"] + 1; finish(d)
    def c07(d: dict[str, Any]) -> None:
        e = effective(d); carry = next(a for a in rows(e, "ValidationAttemptRevisionV0_1R2") if a["payload"]["carry_source"] is not None)
        source = R3V.wrapper_index(e)[carry["payload"]["carry_source"]["source_attempt_ref"]]
        event = R3V.wrapper_index(e)[carry["payload"]["created_event_ref"]]
        changed_sequence = source["payload"]["created_event_sequence"] - 1
        event["payload"]["event_sequence"] = changed_sequence
        carry["payload"]["created_event_sequence"] = changed_sequence
        finish(d)
    return {"F6-R3-IR-C01":c01,"F6-R3-IR-C02":c02,"F6-R3-IR-C03":c03,"F6-R3-IR-C04":c04,"F6-R3-IR-C05":c05,"F6-R3-IR-C06":c06,"F6-R3-IR-C07":c07}


def run_cases(base: dict[str, Any]) -> tuple[int, int, list[str]]:
    rejected = 0; exceptions = 0; failures = []
    for case_id, mutate in cases().items():
        candidate = copy.deepcopy(base)
        try:
            mutate(candidate); errors, _ = validate_fixture(candidate, execute_fixed=False)
        except Exception as exc:
            exceptions += 1; failures.append(f"{case_id}: exception {type(exc).__name__}: {exc}"); continue
        if not errors: failures.append(f"{case_id}: incorrectly accepted")
        elif not any(e.startswith("semantic:") for e in errors): failures.append(f"{case_id}: rejected outside R4 semantic layer")
        else: rejected += 1
    return rejected, exceptions, failures


def main() -> int:
    try: data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print("result: BLOCK"); print(f"load_error: {type(exc).__name__}: {exc}"); return 1
    errors, counts = validate_fixture(data, execute_fixed=True)
    rejected, exceptions, failures = run_cases(data) if not errors else (0, 0, [])
    errors.extend(failures)
    if rejected != 7: errors.append(f"R3 independent case rejection count {rejected} != 7")
    if exceptions != 0: errors.append(f"R4 case exception count {exceptions} != 0")
    if errors:
        print("result: BLOCK")
        for error in errors: print(f"error: {error}")
        return 1
    print("result: PASS_NO_BLOCKER")
    print("fixed_negative_total_rejected: 62")
    print(f"R2_coordinated_cases_rejected: {counts['R2_coordinated']}")
    print(f"R3_independent_cases_rejected: {rejected}")
    print(f"case_exception_count: {exceptions}")
    print(f"fixture_canonical_sha256: {hashlib.sha256(canonical_bytes(data)).hexdigest()}")
    print("task_identity_binding: PASS")
    print("assessment_revision_equality: PASS")
    print("TrustedTime_waiver_currentness: PASS")
    print("evidence_subject_binding: PASS")
    print("strict_Event_order: PASS")
    for key, value in data["occurrence_assertions"].items(): print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
