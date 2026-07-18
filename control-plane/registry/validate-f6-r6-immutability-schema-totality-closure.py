#!/usr/bin/env python3
"""Validate the synthetic F6 R6 immutability/schema-totality closure."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import unicodedata
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "control-plane/registry/examples/2026-07-18-agents-os-f6-r6-immutability-schema-totality-closure-v0.1.json"
SAFE_MAX = 9_007_199_254_740_991


class DuplicateKeyError(ValueError):
    pass


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R5V = load("f6_r5_validator_for_r6", ROOT / "control-plane/registry/validate-f6-r5-contextual-evidence-assessment-closure.py")
R6B = load("f6_r6_builder_for_validation", ROOT / "control-plane/registry/build-f6-r6-immutability-schema-totality-closure.py")


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def h(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode() + b"\0" + canonical(value)).hexdigest()


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise DuplicateKeyError("duplicate JSON key: " + key)
        output[key] = value
    return output


def reject_float(_: str) -> Any:
    raise ValueError("floating-point JSON values are forbidden")


def reject_constant(_: str) -> Any:
    raise ValueError("non-finite JSON values are forbidden")


def strict_loads(text: str) -> Any:
    return json.loads(
        text,
        object_pairs_hook=strict_object,
        parse_float=reject_float,
        parse_constant=reject_constant,
    )


def is_string(value: Any) -> bool:
    return type(value) is str and unicodedata.normalize("NFC", value) == value


def is_safe_int(value: Any, *, positive: bool = False) -> bool:
    return type(value) is int and (value > 0 if positive else value >= 0) and value <= SAFE_MAX


def is_hex64(value: Any) -> bool:
    return is_string(value) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_scalar_tree(value: Any, errors: list[str], path: str = "$") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value < 0 or value > SAFE_MAX:
            errors.append("schema: unsafe integer at " + path)
        return
    if type(value) is float:
        errors.append("schema: floating-point value at " + path)
        return
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value:
            errors.append("schema: non-NFC string at " + path)
        return
    if type(value) is list:
        for index, child in enumerate(value):
            validate_scalar_tree(child, errors, f"{path}[{index}]")
        return
    if type(value) is dict:
        for key, child in value.items():
            if not is_string(key):
                errors.append("schema: invalid object key at " + path)
            validate_scalar_tree(child, errors, path + "." + str(key))
        return
    errors.append("schema: unsupported JSON value at " + path)


def validate_contextual_schema(r5: Any, errors: list[str]) -> bool:
    if type(r5) is not dict:
        errors.append("schema: R5 candidate must be object")
        return False
    assessments = r5.get("contextual_evidence_assessments")
    bindings = r5.get("attempt_contextual_evidence_bindings")
    if type(assessments) is not list or type(bindings) is not list:
        errors.append("schema: contextual inventories must be arrays")
        return False
    valid = True
    for index, item in enumerate(assessments):
        prefix = f"schema: contextual assessment[{index}]"
        if type(item) is not dict or set(item) != R6B.WRAPPER_FIELDS:
            errors.append(prefix + " wrapper fields mismatch")
            valid = False
            continue
        payload = item.get("payload")
        if type(payload) is not dict or set(payload) != R6B.PAYLOAD_FIELDS:
            errors.append(prefix + " payload fields mismatch")
            valid = False
            continue
        subject = payload.get("assessed_subject")
        if type(subject) is not dict or set(subject) != R6B.SUBJECT_FIELDS:
            errors.append(prefix + " assessed-subject fields mismatch")
            valid = False
            continue
        if item["schema"] != "ContextualEvidenceAssessmentInputV0_1R5" or not all(is_string(item[k]) for k in ("key", "ref")) or not is_hex64(item["fingerprint"]):
            errors.append(prefix + " wrapper type/value mismatch")
            valid = False
        string_fields = {
            "assessment_id", "owner_phase", "owner_contract_ref",
            "owner_contract_fingerprint", "barrier_ref", "barrier_fingerprint",
            "result",
        }
        if not all(is_string(payload[k]) for k in string_fields):
            errors.append(prefix + " payload string type mismatch")
            valid = False
        if payload["owner_phase"] != "F3" or payload["result"] != "EXACT_CURRENT":
            errors.append(prefix + " closed enum mismatch")
            valid = False
        if type(payload["is_current_head"]) is not bool:
            errors.append(prefix + " is_current_head must be JSON boolean")
            valid = False
        if not is_safe_int(payload["assessment_revision"], positive=True) or not is_safe_int(payload["owner_contract_revision"], positive=True) or not is_safe_int(payload["observed_event_sequence"]):
            errors.append(prefix + " revision or sequence type/range mismatch")
            valid = False
        predecessor = (payload["predecessor_ref"], payload["predecessor_revision"], payload["predecessor_fingerprint"])
        if payload["assessment_revision"] == 1:
            if predecessor != (None, None, None):
                errors.append(prefix + " revision-one predecessor must be all null")
                valid = False
        elif not (is_string(predecessor[0]) and is_safe_int(predecessor[1], positive=True) and is_hex64(predecessor[2])):
            errors.append(prefix + " predecessor tuple type mismatch")
            valid = False
        for key in ("owner_contract_fingerprint", "barrier_fingerprint"):
            if not is_hex64(payload[key]):
                errors.append(prefix + " fingerprint type mismatch: " + key)
                valid = False
        for key in ("evidence_ref", "requirement_id", "attempt_ref"):
            if not is_string(subject[key]):
                errors.append(prefix + " subject string type mismatch: " + key)
                valid = False
        for key in ("evidence_revision", "requirement_revision", "attempt_revision"):
            if not is_safe_int(subject[key], positive=True):
                errors.append(prefix + " subject revision type/range mismatch: " + key)
                valid = False
        for key in ("evidence_fingerprint", "requirement_fingerprint", "attempt_context_fingerprint"):
            if not is_hex64(subject[key]):
                errors.append(prefix + " subject fingerprint type mismatch: " + key)
                valid = False
    for index, binding in enumerate(bindings):
        prefix = f"schema: contextual binding[{index}]"
        if type(binding) is not dict or set(binding) != R6B.BINDING_FIELDS:
            errors.append(prefix + " fields mismatch")
            valid = False
            continue
        for key in ("attempt_ref", "evidence_ref", "assessment_ref"):
            if not is_string(binding[key]):
                errors.append(prefix + " ref type mismatch: " + key)
                valid = False
        for key in ("attempt_revision", "evidence_revision", "assessment_revision"):
            if not is_safe_int(binding[key], positive=True):
                errors.append(prefix + " revision type/range mismatch: " + key)
                valid = False
        for key in ("attempt_context_fingerprint", "evidence_fingerprint", "assessment_fingerprint", "binding_fingerprint"):
            if not is_hex64(binding[key]):
                errors.append(prefix + " fingerprint type mismatch: " + key)
                valid = False
    return valid


def validate_history_shape(history: Any, errors: list[str]) -> bool:
    if type(history) is not dict or set(history) != R6B.HISTORY_FIELDS:
        errors.append("schema: immutable history fields mismatch")
        return False
    valid = True
    if not is_string(history["anchor_fixture_path"]) or not is_hex64(history["anchor_fixture_sha256"]) or not is_hex64(history["history_fingerprint"]):
        errors.append("schema: immutable history anchor/fingerprint type mismatch")
        valid = False
    if type(history["attempt_revisions"]) is not list or type(history["assessment_revisions"]) is not list:
        errors.append("schema: immutable history inventories must be arrays")
        return False
    for index, row in enumerate(history["attempt_revisions"]):
        if type(row) is not dict or set(row) != R6B.ATTEMPT_HISTORY_FIELDS:
            errors.append(f"schema: attempt history[{index}] fields mismatch")
            valid = False
    for index, row in enumerate(history["assessment_revisions"]):
        if type(row) is not dict or set(row) != R6B.ASSESSMENT_HISTORY_FIELDS:
            errors.append(f"schema: assessment history[{index}] fields mismatch")
            valid = False
    return valid


def safe_validate_r5(r5: Any, execute_fixed: bool) -> tuple[list[str], dict[str, int]]:
    try:
        errors, counts = R5V.validate_fixture(r5, execute_fixed)
        return list(errors), counts
    except Exception as exc:
        return ["schema: malformed R5 input returned BLOCK: " + type(exc).__name__ + ": " + str(exc)], {}


def validate_immutable_revisions(candidate: dict[str, Any], baseline: dict[str, Any], errors: list[str]) -> None:
    expected = R6B.derive_history(baseline)
    current = R6B.derive_history(candidate)
    base_attempts = {(r["attempt_id"], r["attempt_revision"]): r for r in expected["attempt_revisions"]}
    current_attempts = {(r["attempt_id"], r["attempt_revision"]): r for r in current["attempt_revisions"]}
    base_assessments = {(r["assessment_id"], r["assessment_revision"]): r for r in expected["assessment_revisions"]}
    current_assessments = {(r["assessment_id"], r["assessment_revision"]): r for r in current["assessment_revisions"]}
    for key, row in base_attempts.items():
        if key not in current_attempts:
            errors.append("semantic: immutable attempt revision missing: " + repr(key))
        elif current_attempts[key] != row:
            errors.append("semantic: same-revision attempt mutation: " + repr(key))
    for key, row in base_assessments.items():
        if key not in current_assessments:
            errors.append("semantic: immutable contextual assessment revision missing: " + repr(key))
        elif current_assessments[key] != row:
            errors.append("semantic: same-revision contextual assessment mutation: " + repr(key))


def validate_fixture(data: Any, execute_fixed: bool = False) -> tuple[list[str], dict[str, int]]:
    errors: list[str] = []
    counts: dict[str, int] = {}
    validate_scalar_tree(data, errors)
    if type(data) is not dict or set(data) != R6B.ROOT_FIELDS:
        return errors + ["schema: R6 root fields mismatch"], counts
    if data["schema_version"] != "agents-os.f6.validation-current-decision-r6-proof.v0.1" or data["environment"] != "SYNTHETIC_TEST" or type(data["runtime_usable"]) is not bool or data["runtime_usable"] is not False:
        errors.append("semantic: R6 synthetic boundary mismatch")
    unsigned = copy.deepcopy(data)
    root = unsigned.pop("root_fingerprint", None)
    if not is_hex64(root) or root != h("agents-os.f6.r6.root", unsigned):
        errors.append("integrity: R6 root fingerprint mismatch")
    if type(data["r5_bindings"]) is not dict or set(data["r5_bindings"]) != set(R6B.R5_PATHS):
        errors.append("integrity: R5 binding inventory mismatch")
    else:
        for key, path in R6B.R5_PATHS.items():
            expected = {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
            if data["r5_bindings"][key] != expected:
                errors.append("integrity: R5 binding mismatch: " + key)
    if data["schema_profiles"] != R6B.SCHEMA_PROFILES:
        errors.append("schema: R6 schema profile inventory mismatch")
    history_shape_ok = validate_history_shape(data["immutable_revision_history"], errors)
    fixed_baseline = strict_loads((ROOT / R6B.R5_FIXTURE_PATH).read_text())
    expected_history = R6B.derive_history(fixed_baseline)
    if history_shape_ok and data["immutable_revision_history"] != expected_history:
        errors.append("semantic: immutable revision history does not match fixed R5 anchor")
    schema_ok = validate_contextual_schema(data["r5_fixture"], errors)
    r5_errors, old_counts = safe_validate_r5(data["r5_fixture"], execute_fixed)
    errors.extend("R5: " + item for item in r5_errors)
    counts.update(old_counts)
    if schema_ok:
        try:
            validate_immutable_revisions(data["r5_fixture"], fixed_baseline, errors)
        except Exception as exc:
            errors.append("schema: immutable comparison returned BLOCK: " + type(exc).__name__ + ": " + str(exc))
    expected_catalog = {"fixed_negative_total": 62, "R2_coordinated_count": 17, "R3_case_count": 7, "R4_context_case_count": 1, "R6_adversarial_case_count": 11}
    if data["regression_catalog"] != expected_catalog:
        errors.append("integrity: R6 regression catalog mismatch")
    if data["occurrence_assertions"] != data["r5_fixture"].get("occurrence_assertions"):
        errors.append("semantic: occurrence boundary mismatch")
    return errors, counts


def reroot_r5(r5: dict[str, Any]) -> None:
    unsigned = copy.deepcopy(r5)
    unsigned.pop("root_fingerprint", None)
    r5["root_fingerprint"] = R5V.h("agents-os.f6.r5.root", unsigned)


def reroot_r6(data: dict[str, Any]) -> None:
    unsigned = copy.deepcopy(data)
    unsigned.pop("root_fingerprint", None)
    data["root_fingerprint"] = h("agents-os.f6.r6.root", unsigned)


def refresh_assessment_and_binding(r5: dict[str, Any], assessment: dict[str, Any]) -> None:
    assessment["fingerprint"] = R5V.h("agents-os.f6.r5.ContextualEvidenceAssessmentInputV0_1R5", assessment["payload"])
    for binding in r5["attempt_contextual_evidence_bindings"]:
        if binding.get("assessment_ref") == assessment.get("ref") and binding.get("assessment_revision") == assessment["payload"].get("assessment_revision"):
            binding["assessment_fingerprint"] = assessment["fingerprint"]
            unsigned = {key: value for key, value in binding.items() if key != "binding_fingerprint"}
            binding["binding_fingerprint"] = R5V.h("agents-os.f6.r5.attempt-contextual-evidence-binding", unsigned)
    reroot_r5(r5)


def coordinated_same_revision_resign(data: dict[str, Any]) -> None:
    r5 = data["r5_fixture"]
    r4 = r5["r4_fixture"]
    effective = r4["r3_fixture"]["effective_fixture"]
    candidate = R5V.R4V.R3V.find_kind(effective, "CANDIDATE_COMMITMENT_CURRENTNESS")
    candidate["payload"]["subject_payload"] = {"candidate_id": "candidate-r6-same-revision-attack", "candidate_revision": 10, "status": "CURRENT"}
    candidate["payload"]["subject_ref"] = "synth:f6:r6:taskcandidate:same-revision-attack"
    candidate["payload"]["subject_revision"] = 10
    candidate["payload"]["subject_fingerprint"] = R5V.R4V.R3V.R2V.typed_hash("agents-os.f6.r2.assessment-subject.CANDIDATE_COMMITMENT_CURRENTNESS", candidate["payload"]["subject_payload"])
    R5V.R4V.R3V.R2V.reseal(candidate)
    candidate_tuple = R5V.R4V.R3V.exact_tuple(candidate)
    task = R5V.R4V.R3V.find_kind(effective, "TASK_CURRENT_STATE")
    task["payload"]["subject_payload"].update({"candidate_ref": candidate_tuple["ref"], "candidate_revision": candidate_tuple["revision"], "candidate_fingerprint": candidate_tuple["fingerprint"]})
    R5V.R4V.R3V.refresh_assessment_subject(task)
    for attempt in R5V.rows(effective, "ValidationAttemptRevisionV0_1R2"):
        attempt["payload"]["context_binding"]["candidate"] = copy.deepcopy(candidate_tuple)
    R5V.rows(effective, "TaskCompletionEligibilityDecisionV0_1R2")[0]["payload"]["candidate_context"] = copy.deepcopy(candidate_tuple)
    R5V.R4V.refresh_r3(r4["r3_fixture"])
    R5V.R4V.refresh_r4(r4)
    assessments, bindings = R5V.R5B.build_contextual(r4)
    r5["contextual_evidence_assessments"] = assessments
    r5["attempt_contextual_evidence_bindings"] = bindings
    reroot_r5(r5)
    reroot_r6(data)


def mutate_assessment(data: dict[str, Any], mutation: Callable[[dict[str, Any]], None]) -> None:
    assessment = data["r5_fixture"]["contextual_evidence_assessments"][0]
    mutation(assessment)
    if type(assessment.get("payload")) is dict and "assessment_revision" in assessment["payload"]:
        try:
            refresh_assessment_and_binding(data["r5_fixture"], assessment)
        except Exception:
            reroot_r5(data["r5_fixture"])
    else:
        reroot_r5(data["r5_fixture"])
    reroot_r6(data)


def run_adversarial_cases(base: dict[str, Any]) -> tuple[int, int, list[str]]:
    cases: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
        ("same_revision_full_resign", coordinated_same_revision_resign, "same-revision"),
        ("unknown_payload_field", lambda d: mutate_assessment(d, lambda a: a["payload"].__setitem__("unknown_payload_field", "x")), "payload fields mismatch"),
        ("integer_as_boolean", lambda d: mutate_assessment(d, lambda a: a["payload"].__setitem__("is_current_head", 1)), "JSON boolean"),
        ("missing_required_payload", lambda d: mutate_assessment(d, lambda a: a["payload"].pop("owner_phase")), "payload fields mismatch"),
        ("float_revision", lambda d: mutate_assessment(d, lambda a: a["payload"].__setitem__("assessment_revision", 1.0)), "floating-point"),
        ("unsafe_integer", lambda d: mutate_assessment(d, lambda a: a["payload"].__setitem__("observed_event_sequence", SAFE_MAX + 1)), "unsafe integer"),
        ("unknown_wrapper_field", lambda d: mutate_assessment(d, lambda a: a.__setitem__("unknown_wrapper_field", "x")), "wrapper fields mismatch"),
        ("invalid_nullable_predecessor", lambda d: mutate_assessment(d, lambda a: a["payload"].__setitem__("predecessor_ref", "synth:invalid")), "predecessor must be all null"),
        ("missing_history_row", lambda d: (d["immutable_revision_history"]["attempt_revisions"].pop(), d["immutable_revision_history"].__setitem__("history_fingerprint", h("agents-os.f6.r6.immutable-revision-history", {k: v for k, v in d["immutable_revision_history"].items() if k != "history_fingerprint"})), reroot_r6(d)), "does not match fixed R5 anchor"),
        ("reordered_history", lambda d: (d["immutable_revision_history"]["assessment_revisions"].reverse(), d["immutable_revision_history"].__setitem__("history_fingerprint", h("agents-os.f6.r6.immutable-revision-history", {k: v for k, v in d["immutable_revision_history"].items() if k != "history_fingerprint"})), reroot_r6(d)), "does not match fixed R5 anchor"),
    ]
    rejected = 0
    exceptions = 0
    failures: list[str] = []
    for case_id, mutation, target in cases:
        candidate = copy.deepcopy(base)
        try:
            mutation(candidate)
            errors, _ = validate_fixture(candidate, False)
            if errors and any(target in error for error in errors):
                rejected += 1
            else:
                failures.append(case_id + ": target rejection absent; errors=" + repr(errors))
        except Exception as exc:
            exceptions += 1
            failures.append(case_id + ": probe exception " + type(exc).__name__ + ": " + str(exc))
    try:
        strict_loads('{"duplicate":1,"duplicate":2}')
        failures.append("duplicate_JSON_key: incorrectly accepted")
    except DuplicateKeyError:
        rejected += 1
    except Exception as exc:
        exceptions += 1
        failures.append("duplicate_JSON_key: wrong exception " + type(exc).__name__)
    return rejected, exceptions, failures


def main() -> int:
    try:
        data = strict_loads(FIXTURE.read_text())
        errors, counts = validate_fixture(data, True)
        rejected, exceptions, failures = run_adversarial_cases(data)
        if rejected != 11 or exceptions or failures:
            errors.extend(failures)
            if rejected != 11:
                errors.append("R6 adversarial rejection count mismatch")
            if exceptions:
                errors.append("R6 adversarial exception count nonzero")
    except Exception as exc:
        print("result: BLOCK")
        print("error: deterministic validation exception:", type(exc).__name__, str(exc))
        return 1
    if errors:
        print("result: BLOCK")
        for error in errors:
            print("error:", error)
        return 1
    print("result: PASS_NO_BLOCKER")
    print("fixed_negative_total_rejected: 62")
    print("R2_coordinated_cases_rejected: 17")
    print("R3_cases_rejected: 7")
    print("R4_context_replacement_case_rejected: 1")
    print("R6_adversarial_cases_rejected: 11")
    print("same_revision_full_resign_rejected: 1")
    print("schema_totality_cases_rejected: 10")
    print("case_exception_count: 0")
    print("fixture_canonical_sha256:", hashlib.sha256(canonical(data)).hexdigest())
    print("immutable_revision_history: PASS")
    print("contextual_assessment_schema_totality: PASS")
    for key, value in data["occurrence_assertions"].items():
        print(key + ":", value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
