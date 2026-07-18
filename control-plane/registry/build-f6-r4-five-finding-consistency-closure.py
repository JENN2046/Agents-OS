#!/usr/bin/env python3
"""Build the deterministic synthetic F6 R4 five-finding closure witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = WORKSPACE_ROOT / "control-plane/registry/examples/2026-07-18-agents-os-f6-r4-five-finding-consistency-closure-v0.1.json"
R3_BUILDER_PATH = WORKSPACE_ROOT / "control-plane/registry/build-f6-r3-eight-finding-semantic-closure.py"
R3_VALIDATOR_PATH = WORKSPACE_ROOT / "control-plane/registry/validate-f6-r3-eight-finding-semantic-closure.py"

R3_PATHS = {
    "amendment": "control-plane/registry/drafts/2026-07-18-agents-os-f6-validation-requirement-current-decision-v0.1-r3-amendment.draft.md",
    "builder": "control-plane/registry/build-f6-r3-eight-finding-semantic-closure.py",
    "fixture": "control-plane/registry/examples/2026-07-18-agents-os-f6-r3-eight-finding-semantic-closure-v0.1.json",
    "validator": "control-plane/registry/validate-f6-r3-eight-finding-semantic-closure.py",
    "manifest": "control-plane/registry/reports/2026-07-18-agents-os-f6-r3-atomic-independent-review-package-v0.1.manifest.yaml",
    "independent_review": "control-plane/registry/reviews/2026-07-18-yellow-agents-os-f6-r3-full-atomic-independent-review.yaml",
    "case_evidence": "control-plane/registry/reviews/2026-07-18-f6-r3-independent-consistency-cases.json",
    "disposition": "control-plane/registry/reviews/2026-07-18-agents-os-f6-r3-independent-review-disposition-v0.1.yaml",
    "r4_start_decision": "control-plane/registry/decisions/2026-07-18-agents-os-f6-r4-five-finding-consistency-closure-start-decision-v0.1.yaml",
}


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R3B = load_module("f6_r3_builder_for_r4", R3_BUILDER_PATH)
R3V = load_module("f6_r3_validator_for_r4", R3_VALIDATOR_PATH)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def typed_hash(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode() + b"\x00" + canonical_bytes(value)).hexdigest()


def file_hash(path: str) -> str:
    return hashlib.sha256((WORKSPACE_ROOT / path).read_bytes()).hexdigest()


def rows(effective: dict[str, Any], schema: str) -> list[dict[str, Any]]:
    return effective["normative_objects"][schema]


def wrapper_index(effective: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return R3V.wrapper_index(effective)


def seal_binding(domain: str, value: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(value)
    value["binding_fingerprint"] = typed_hash(domain, value)
    return value


def task_identity_bindings(effective: dict[str, Any]) -> list[dict[str, Any]]:
    index = wrapper_index(effective)
    task_assessment = R3V.find_kind(effective, "TASK_CURRENT_STATE")
    task_id = task_assessment["payload"]["subject_payload"]["task_id"]
    result = [seal_binding("agents-os.f6.r4.task-identity", {
        "consumer_kind": "F1_TASK_ASSESSMENT", "consumer_ref": task_assessment["ref"],
        "consumer_revision": task_assessment["payload"]["assessment_revision"], "task_id": task_id,
    })]
    requirements = rows(effective, "ValidationRequirementRevisionV0_1R2")
    for requirement in requirements:
        p = requirement["payload"]
        result.append(seal_binding("agents-os.f6.r4.task-identity", {
            "consumer_kind": "REQUIREMENT", "consumer_ref": requirement["ref"],
            "consumer_revision": p["requirement_revision"], "task_id": p["task_id"],
        }))
    for snapshot in rows(effective, "ValidationSetSnapshotV0_1R2"):
        member_tasks = sorted({index[m["requirement_ref"]]["payload"]["task_id"] for m in snapshot["payload"]["memberships"] if m["requirement_ref"] in index})
        result.append(seal_binding("agents-os.f6.r4.task-identity", {
            "consumer_kind": "VALIDATION_SET", "consumer_ref": snapshot["ref"],
            "consumer_revision": snapshot["payload"]["set_revision"],
            "task_id": member_tasks[0] if len(member_tasks) == 1 else "INDETERMINATE",
        }))
    for attempt in rows(effective, "ValidationAttemptRevisionV0_1R2"):
        p = attempt["payload"]
        requirement = next(row for row in requirements if row["payload"]["requirement_id"] == p["requirement_id"] and row["payload"]["requirement_revision"] == p["requirement_revision"])
        result.append(seal_binding("agents-os.f6.r4.task-identity", {
            "consumer_kind": "ATTEMPT", "consumer_ref": attempt["ref"],
            "consumer_revision": p["attempt_revision"], "task_id": requirement["payload"]["task_id"],
        }))
    for completion in rows(effective, "TaskCompletionEligibilityDecisionV0_1R2"):
        result.append(seal_binding("agents-os.f6.r4.task-identity", {
            "consumer_kind": "COMPLETION", "consumer_ref": completion["ref"],
            "consumer_revision": 1, "task_id": completion["payload"]["task_id"],
        }))
    return sorted(result, key=lambda x: (x["consumer_kind"], x["consumer_ref"]))


def consumer_assessment_bindings(effective: dict[str, Any]) -> list[dict[str, Any]]:
    index = wrapper_index(effective)
    result: list[dict[str, Any]] = []

    def walk(value: Any, path: str) -> None:
        if isinstance(value, list):
            for number, item in enumerate(value):
                walk(item, f"{path}[{number}]")
        elif isinstance(value, dict):
            for key in sorted(value):
                if key.endswith("_assessment_ref"):
                    prefix = key[:-4]
                    ref = value[key]
                    resolved = index.get(ref)
                    result.append(seal_binding("agents-os.f6.r4.consumer-assessment", {
                        "consumer_path": f"{path}.{prefix}", "assessment_ref": ref,
                        "declared_fingerprint": value.get(prefix + "_fingerprint"),
                        "declared_revision": value.get(prefix + "_revision"),
                        "resolved_fingerprint": None if resolved is None else resolved["fingerprint"],
                        "resolved_revision": None if resolved is None else resolved["payload"].get("assessment_revision"),
                    }))
                walk(value[key], f"{path}.{key}")
    walk(effective["normative_objects"], "$.normative_objects")
    return sorted(result, key=lambda x: x["consumer_path"])


def waiver_time_bindings(effective: dict[str, Any]) -> list[dict[str, Any]]:
    trusted = rows(effective, "TrustedTimeInputV0_1R2")[0]
    result = []
    for waiver in rows(effective, "RequirementWaiverEventV0_1R2"):
        wp = waiver["payload"]
        observed = trusted["payload"]["observed_event_sequence"]
        result.append(seal_binding("agents-os.f6.r4.waiver-time", {
            "trusted_time_ref": trusted["ref"], "trusted_time_fingerprint": trusted["fingerprint"],
            "trusted_time_revision": trusted["payload"]["trusted_time_revision"],
            "observed_event_sequence": observed, "waiver_ref": waiver["ref"],
            "waiver_revision": wp["waiver_revision"], "valid_from_sequence": wp["valid_from_sequence"],
            "expires_at_sequence": wp["expires_at_sequence"],
            "derived_current": wp["valid_from_sequence"] <= observed < wp["expires_at_sequence"],
        }))
    return result


def evidence_subject_bindings(effective: dict[str, Any]) -> list[dict[str, Any]]:
    index = wrapper_index(effective)
    result = []
    for attempt in rows(effective, "ValidationAttemptRevisionV0_1R2"):
        ap = attempt["payload"]
        for binding in ap["evidence_bindings"]:
            evidence = index[binding["evidence_ref"]]
            result.append(seal_binding("agents-os.f6.r4.evidence-subject", {
                "attempt_ref": attempt["ref"], "attempt_revision": ap["attempt_revision"],
                "context_fingerprint": ap["context_binding"]["context_fingerprint"],
                "evidence_assessment_ref": binding["evidence_assessment_ref"],
                "evidence_assessment_fingerprint": binding["evidence_assessment_fingerprint"],
                "evidence_assessment_revision": binding["evidence_assessment_revision"],
                "evidence_ref": evidence["ref"], "evidence_revision": evidence["payload"]["evidence_revision"],
                "requirement_id": ap["requirement_id"], "requirement_revision": ap["requirement_revision"],
                "requirement_fingerprint": ap["requirement_fingerprint"],
                "validation_subject": evidence["payload"]["validation_subject"],
            }))
    return sorted(result, key=lambda x: (x["attempt_ref"], x["evidence_ref"]))


def strict_event_edges(effective: dict[str, Any]) -> list[dict[str, Any]]:
    index = wrapper_index(effective)
    result = []
    for attempt in rows(effective, "ValidationAttemptRevisionV0_1R2"):
        ap = attempt["payload"]
        if ap["predecessor_ref"] is not None:
            predecessor = index[ap["predecessor_ref"]]
            result.append(seal_binding("agents-os.f6.r4.strict-event-edge", {
                "purpose": "ATTEMPT_PREDECESSOR", "from_ref": predecessor["payload"]["created_event_ref"],
                "from_sequence": predecessor["payload"]["created_event_sequence"],
                "to_ref": ap["created_event_ref"], "to_sequence": ap["created_event_sequence"], "relation": "LT",
            }))
        if ap["carry_source"] is not None:
            source = index[ap["carry_source"]["source_attempt_ref"]]
            result.append(seal_binding("agents-os.f6.r4.strict-event-edge", {
                "purpose": "CARRY_SOURCE", "from_ref": source["payload"]["created_event_ref"],
                "from_sequence": source["payload"]["created_event_sequence"],
                "to_ref": ap["created_event_ref"], "to_sequence": ap["created_event_sequence"], "relation": "LT",
            }))
    return sorted(result, key=lambda x: (x["purpose"], x["from_ref"], x["to_ref"]))


def build_fixture() -> dict[str, Any]:
    r3_fixture = R3B.build_fixture()
    fixture = {
        "schema_version": "agents-os.f6.validation-current-decision-r4-proof.v0.1",
        "environment": "SYNTHETIC_TEST", "runtime_usable": False,
        "r3_bindings": {key: {"path": path, "sha256": file_hash(path)} for key, path in R3_PATHS.items()},
        "r3_fixture": r3_fixture,
        "task_identity_bindings": task_identity_bindings(r3_fixture["effective_fixture"]),
        "consumer_assessment_bindings": consumer_assessment_bindings(r3_fixture["effective_fixture"]),
        "waiver_time_bindings": waiver_time_bindings(r3_fixture["effective_fixture"]),
        "evidence_subject_bindings": evidence_subject_bindings(r3_fixture["effective_fixture"]),
        "strict_event_edges": strict_event_edges(r3_fixture["effective_fixture"]),
        "regression_catalog": {"fixed_negative_total": 62, "R2_coordinated_count": 17, "R3_independent_case_count": 7},
        "occurrence_assertions": copy.deepcopy(r3_fixture["occurrence_assertions"]),
    }
    fixture["root_fingerprint"] = typed_hash("agents-os.f6.r4.root", fixture)
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
