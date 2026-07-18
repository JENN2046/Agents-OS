#!/usr/bin/env python3
"""Offline validator for the F7 R2 canonical decision-case inventory."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable


R1_VALIDATOR = Path("control-plane/registry/validate-f7-r1-home-domain-minimum-semantics.py")
R1_FIXTURE = Path("control-plane/registry/examples/2026-07-18-agents-os-f7-r1-home-domain-minimum-semantics-v0.1.json")
R2_FIXTURE = Path("control-plane/registry/examples/2026-07-19-agents-os-f7-r2-decision-case-inventory-closure-v0.1.json")
R1_FIXTURE_SHA256 = "8bda718fd580fa95124120b148699fae099a9eb9710ead53eeefc943f1864f01"
R1_ROOT_FINGERPRINT = "2a5dc56a38de8636a31887a4bc3a954844ed42413a505068d5d2fdd4cf435b54"
DOMAIN = "F7_R2_DECISION_CASE_INVENTORY_SYNTHETIC_NONAUTHORITY"
MAX_SAFE_INTEGER = 9007199254740991
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

ROOT_FIELDS = {
    "schema_version", "amendment_id", "environment", "domain_tag", "runtime_usable",
    "r1_fixture_sha256", "r1_root_fingerprint", "decision_case_anchors",
    "catalog_fingerprint", "boundary_assertions", "root_fingerprint",
}
ANCHOR_FIELDS = {
    "ordinal", "case_id", "raw_input", "derived_decision", "r1_row_fingerprint", "anchor_fingerprint",
}
RAW_FIELDS = {
    "source_class", "target_class", "source_currentness", "creator_currentness", "explicit_choice",
    "relationship_authority_requested", "action_authority_requested", "runtime_target_requested",
}
DECISION_FIELDS = {"result", "reason_codes", "primary_reason", "action_authority"}
BOUNDARY_FIELDS = {
    "real_home_fact_count", "private_raw_memory_count", "sensing_or_recording_count",
    "Task_or_Command_mutation_count", "database_write_count", "provider_call_count",
    "external_effect_count", "terminal_outcome",
}


class DuplicateKeyError(ValueError):
    pass


def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_r1_module() -> Any:
    spec = importlib.util.spec_from_file_location("f7_r1_validator_fixed", R1_VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load fixed R1 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def without_field(value: dict[str, Any], field: str) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop(field, None)
    return result


def raw(
    source: str,
    target: str,
    *,
    source_currentness: str = "CURRENT",
    creator_currentness: str = "CURRENT",
    explicit_choice: bool | None = True,
    relationship_authority_requested: bool = False,
    action_authority_requested: bool = False,
    runtime_target_requested: bool = False,
) -> dict[str, Any]:
    return {
        "source_class": source,
        "target_class": target,
        "source_currentness": source_currentness,
        "creator_currentness": creator_currentness,
        "explicit_choice": explicit_choice,
        "relationship_authority_requested": relationship_authority_requested,
        "action_authority_requested": action_authority_requested,
        "runtime_target_requested": runtime_target_requested,
    }


EXPECTED_CASES = [
    ("C01", raw("SESSION_CONTENT", "LIFE_STREAM_CANDIDATE")),
    ("C02", raw("SESSION_CONTENT", "MEMORY_CANDIDATE")),
    ("C03", raw("SESSION_CONTENT", "INTENT_CANDIDATE")),
    ("C04", raw("SUBJECTIVE_RELATIONSHIP_MEMORY", "MEMORY_CANDIDATE")),
    ("C05", raw("GROWTH_EVENT", "MEMORY_CANDIDATE")),
    ("C06", raw("IDENTITY_NARRATIVE", "STABLE_IDENTITY_FACT")),
    ("C07", raw("SUBJECTIVE_RELATIONSHIP_MEMORY", "FORMAL_RELATIONSHIP_FACT")),
    ("C08", raw("SESSION_CONTENT", "TASK_CANONICAL_FACT")),
    ("C09", raw("MEMORY_CANDIDATE", "MEMORY_CONTENT")),
    ("C10", raw("INTENT_CANDIDATE", "ORCHESTRATOR_COMMAND")),
    ("C11", raw("PRESENCE_CONSENT", "DEVICE_SENSING_STATE")),
    ("C12", raw("GROWTH_EVENT", "BEHAVIOR_POLICY_REVISION")),
    ("C13", raw("SUBJECTIVE_RELATIONSHIP_MEMORY", "MEMORY_CANDIDATE", relationship_authority_requested=True)),
    ("C14", raw("SESSION_CONTENT", "MEMORY_CANDIDATE", source_currentness="STALE")),
    ("C15", raw("SESSION_CONTENT", "MEMORY_CANDIDATE", creator_currentness="STALE")),
    ("C16", raw("SESSION_CONTENT", "MEMORY_CANDIDATE", explicit_choice=None)),
    ("C17", raw("SESSION_CONTENT", "MEMORY_CANDIDATE", source_currentness="UNKNOWN")),
    ("C18", raw("SESSION_CONTENT", "MEMORY_CANDIDATE", action_authority_requested=True)),
    ("C19", raw("SESSION_CONTENT", "MEMORY_CANDIDATE", runtime_target_requested=True)),
    ("C20", raw(
        "SESSION_CONTENT", "TASK_CANONICAL_FACT", source_currentness="STALE",
        creator_currentness="STALE", explicit_choice=None, action_authority_requested=True,
    )),
]


def validate_json_value(value: Any, path: str, errors: list[str]) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if value < 0 or value > MAX_SAFE_INTEGER: errors.append(path + ": unsafe integer")
        return
    if type(value) is float:
        errors.append(path + ": float forbidden"); return
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value: errors.append(path + ": non-NFC string")
        return
    if type(value) is list:
        for index, item in enumerate(value): validate_json_value(item, f"{path}[{index}]", errors)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str: errors.append(path + ": non-string key")
            validate_json_value(item, f"{path}.{key}", errors)
        return
    errors.append(path + ": unsupported JSON type")


def exact_fields(value: Any, expected: set[str], path: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(path + ": expected object"); return False
    actual = set(value)
    if actual != expected:
        errors.append(f"{path}: fields mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}")
        return False
    return True


def expected_catalog(r1_module: Any) -> list[dict[str, Any]]:
    catalog = []
    for ordinal, (case_id, raw_input) in enumerate(EXPECTED_CASES, start=1):
        result, reasons, primary = r1_module.derive_case(copy.deepcopy(raw_input))
        catalog.append({
            "ordinal": ordinal,
            "case_id": case_id,
            "raw_input": copy.deepcopy(raw_input),
            "derived_decision": {
                "result": result,
                "reason_codes": reasons,
                "primary_reason": primary,
                "action_authority": False,
            },
        })
    return catalog


def validate_pair(r1: Any, r2: Any, r1_bytes_sha256: str, r1_module: Any) -> list[str]:
    errors: list[str] = []
    validate_json_value(r2, "$", errors)
    r1_errors = r1_module.validate_fixture(r1)
    if r1_errors:
        errors.extend("R1:" + error for error in r1_errors)
    if not exact_fields(r2, ROOT_FIELDS, "$", errors): return errors
    if r2["schema_version"] != "agents-os.f7-r2-decision-case-inventory-witness.v0.1": errors.append("$: schema mismatch")
    if r2["amendment_id"] != "F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R2": errors.append("$: amendment mismatch")
    if r2["environment"] != "SYNTHETIC_TEST" or r2["domain_tag"] != DOMAIN: errors.append("$: synthetic domain mismatch")
    if r2["runtime_usable"] is not False: errors.append("$: runtime_usable must be false")
    if r1_bytes_sha256 != R1_FIXTURE_SHA256 or r2["r1_fixture_sha256"] != R1_FIXTURE_SHA256:
        errors.append("$: immutable R1 fixture byte anchor mismatch")
    if r1.get("root_fingerprint") != R1_ROOT_FINGERPRINT or r2["r1_root_fingerprint"] != R1_ROOT_FINGERPRINT:
        errors.append("$: immutable R1 root anchor mismatch")

    normative = expected_catalog(r1_module)
    resolved_r1 = []
    if type(r1.get("decision_cases")) is list:
        for case in r1["decision_cases"]:
            if type(case) is dict and all(key in case for key in ("case_id", "raw_input", "claimed_decision", "row_fingerprint")):
                resolved_r1.append({
                    "case_id": case["case_id"], "raw_input": case["raw_input"],
                    "derived_decision": case["claimed_decision"], "r1_row_fingerprint": case["row_fingerprint"],
                })
    expected_r1 = []
    for item, actual_case in zip(normative, r1.get("decision_cases", [])):
        expected_r1.append({
            "case_id": item["case_id"], "raw_input": item["raw_input"],
            "derived_decision": item["derived_decision"],
            "r1_row_fingerprint": actual_case.get("row_fingerprint") if type(actual_case) is dict else None,
        })
    if len(resolved_r1) != 20 or any(
        resolved_r1[index]["case_id"] != normative[index]["case_id"]
        or resolved_r1[index]["raw_input"] != normative[index]["raw_input"]
        or resolved_r1[index]["derived_decision"] != normative[index]["derived_decision"]
        for index in range(min(len(resolved_r1), 20))
    ):
        errors.append("$.R1.decision_cases: canonical ID order raw-input or derived-decision inventory mismatch")

    anchors = r2["decision_case_anchors"]
    if type(anchors) is not list or len(anchors) != 20:
        errors.append("$.decision_case_anchors: requires exactly 20 ordered anchors")
    else:
        expected_anchors = []
        for index, item in enumerate(normative):
            anchor = anchors[index]
            path = f"$.decision_case_anchors[{index}]"
            if not exact_fields(anchor, ANCHOR_FIELDS, path, errors): continue
            if type(anchor["ordinal"]) is not int or anchor["ordinal"] != index + 1: errors.append(path + ": ordinal mismatch")
            if not exact_fields(anchor["raw_input"], RAW_FIELDS, path + ".raw_input", errors): continue
            if not exact_fields(anchor["derived_decision"], DECISION_FIELDS, path + ".derived_decision", errors): continue
            expected_r1_row = r1["decision_cases"][index]["row_fingerprint"] if len(r1.get("decision_cases", [])) > index else None
            unsigned = {
                "ordinal": index + 1,
                "case_id": item["case_id"],
                "raw_input": item["raw_input"],
                "derived_decision": item["derived_decision"],
                "r1_row_fingerprint": expected_r1_row,
            }
            expected_signed = copy.deepcopy(unsigned)
            expected_signed["anchor_fingerprint"] = digest(DOMAIN + ":case-anchor", unsigned)
            expected_anchors.append(expected_signed)
            if anchor != expected_signed: errors.append(path + ": canonical anchor mismatch")
        if anchors != expected_anchors: errors.append("$.decision_case_anchors: exact ordered catalog mismatch")
        if r2["catalog_fingerprint"] != digest(DOMAIN + ":catalog", anchors): errors.append("$.catalog_fingerprint: mismatch")

    boundary = r2["boundary_assertions"]
    if exact_fields(boundary, BOUNDARY_FIELDS, "$.boundary_assertions", errors):
        for key in BOUNDARY_FIELDS - {"terminal_outcome"}:
            if type(boundary[key]) is not int or boundary[key] != 0: errors.append(f"$.boundary_assertions.{key}: must be strict zero")
        if boundary["terminal_outcome"] != "NOT_EXECUTED": errors.append("$.boundary_assertions.terminal_outcome: mismatch")
    for key in ("r1_fixture_sha256", "r1_root_fingerprint", "catalog_fingerprint", "root_fingerprint"):
        if type(r2[key]) is not str or SHA256_RE.fullmatch(r2[key]) is None: errors.append(f"$.{key}: malformed hash")
    expected_root = digest(DOMAIN + ":root", without_field(r2, "root_fingerprint"))
    if r2["root_fingerprint"] != expected_root: errors.append("$.root_fingerprint: mismatch")
    return errors


def resign_r2(r2: dict[str, Any]) -> None:
    for anchor in r2.get("decision_case_anchors", []):
        if type(anchor) is dict:
            anchor["anchor_fingerprint"] = digest(DOMAIN + ":case-anchor", without_field(anchor, "anchor_fingerprint"))
    r2["catalog_fingerprint"] = digest(DOMAIN + ":catalog", r2.get("decision_case_anchors"))
    r2["root_fingerprint"] = digest(DOMAIN + ":root", without_field(r2, "root_fingerprint"))


def run_regressions(r1: dict[str, Any], r2: dict[str, Any], r1_module: Any) -> tuple[int, list[str]]:
    cases: list[tuple[str, Callable[[dict[str, Any]], None]]] = []

    def replace_semantics(target_index: int, source_index: int) -> Callable[[dict[str, Any]], None]:
        def mutate(doc: dict[str, Any]) -> None:
            case_id = doc["decision_cases"][target_index]["case_id"]
            replacement = copy.deepcopy(doc["decision_cases"][source_index])
            replacement["case_id"] = case_id
            doc["decision_cases"][target_index] = replacement
        return mutate

    cases.extend([
        ("replace_C06_with_C01_semantics", replace_semantics(5, 0)),
        ("replace_C08_with_C01_semantics", replace_semantics(7, 0)),
        ("rename_C06_to_C99", lambda d: d["decision_cases"][5].__setitem__("case_id", "C99")),
        ("swap_C06_C07", lambda d: d["decision_cases"].__setitem__(slice(5, 7), [d["decision_cases"][6], d["decision_cases"][5]])),
    ])
    failures: list[str] = []
    rejected = 0
    for name, mutate in cases:
        changed = copy.deepcopy(r1)
        mutate(changed)
        r1_module.resign(changed)
        if r1_module.validate_fixture(changed):
            failures.append(name + ": fixed R1 validator unexpectedly rejected; target R2 regression not demonstrated")
            continue
        changed_sha = hashlib.sha256(canonical_bytes(changed)).hexdigest()
        errors = validate_pair(changed, r2, changed_sha, r1_module)
        if any("canonical ID order raw-input or derived-decision inventory mismatch" in error for error in errors):
            rejected += 1
        else:
            failures.append(name + ": not rejected by target R2 inventory semantic")

    r2_mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("R2_anchor_substitution", lambda d: d["decision_case_anchors"][5].update(copy.deepcopy(d["decision_case_anchors"][0]))),
        ("R2_anchor_rename", lambda d: d["decision_case_anchors"][5].__setitem__("case_id", "C99")),
        ("R2_anchor_reorder", lambda d: d["decision_case_anchors"].__setitem__(slice(5, 7), [d["decision_case_anchors"][6], d["decision_case_anchors"][5]])),
        ("R2_anchor_unknown_field", lambda d: d["decision_case_anchors"][5].__setitem__("unexpected", True)),
    ]
    for name, mutate in r2_mutations:
        changed = copy.deepcopy(r2)
        mutate(changed)
        resign_r2(changed)
        errors = validate_pair(r1, changed, R1_FIXTURE_SHA256, r1_module)
        if errors: rejected += 1
        else: failures.append(name + ": fully re-signed R2 catalog mutation accepted")

    try:
        json.loads('{"schema_version":"x","schema_version":"y"}', object_pairs_hook=no_duplicate_pairs)
        failures.append("duplicate_JSON_key: accepted")
    except DuplicateKeyError:
        rejected += 1
    return rejected, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r1-fixture", type=Path, default=R1_FIXTURE)
    parser.add_argument("--r2-fixture", type=Path, default=R2_FIXTURE)
    parser.add_argument("--skip-adversarial", action="store_true")
    args = parser.parse_args()
    try:
        r1_bytes = args.r1_fixture.read_bytes()
        r1 = json.loads(r1_bytes, object_pairs_hook=no_duplicate_pairs)
        r2 = json.loads(args.r2_fixture.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_pairs)
        r1_module = load_r1_module()
        errors = validate_pair(r1, r2, hashlib.sha256(r1_bytes).hexdigest(), r1_module)
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "errors": [f"stable failure: {type(exc).__name__}: {exc}"]}, indent=2)); return 1
    if errors:
        print(json.dumps({"result": "BLOCK", "errors": errors}, indent=2)); return 1
    rejected = 0
    if not args.skip_adversarial:
        rejected, failures = run_regressions(r1, r2, r1_module)
        if failures:
            print(json.dumps({"result": "BLOCK", "adversarial_failures": failures}, indent=2)); return 1
    print(json.dumps({
        "result": "PASS",
        "canonical_decision_case_anchors": len(r2["decision_case_anchors"]),
        "R1_fully_resigned_false_acceptances_closed": 4,
        "R2_catalog_mutations_rejected": 4,
        "total_R2_adversarial_cases_rejected": rejected,
        "runtime_usable": False,
        "terminal_outcome": "NOT_EXECUTED",
        "root_fingerprint": r2["root_fingerprint"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
