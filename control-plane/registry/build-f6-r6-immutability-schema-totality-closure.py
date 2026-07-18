#!/usr/bin/env python3
"""Build the deterministic synthetic F6 R6 immutability/schema witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = WORKSPACE_ROOT / "control-plane/registry/examples/2026-07-18-agents-os-f6-r6-immutability-schema-totality-closure-v0.1.json"
R5_BUILDER_PATH = WORKSPACE_ROOT / "control-plane/registry/build-f6-r5-contextual-evidence-assessment-closure.py"
R5_FIXTURE_PATH = "control-plane/registry/examples/2026-07-18-agents-os-f6-r5-contextual-evidence-assessment-closure-v0.1.json"
R5_PATHS = {
    "amendment": "control-plane/registry/drafts/2026-07-18-agents-os-f6-validation-requirement-current-decision-v0.1-r5-amendment.draft.md",
    "builder": "control-plane/registry/build-f6-r5-contextual-evidence-assessment-closure.py",
    "fixture": R5_FIXTURE_PATH,
    "validator": "control-plane/registry/validate-f6-r5-contextual-evidence-assessment-closure.py",
    "manifest": "control-plane/registry/reports/2026-07-18-agents-os-f6-r5-atomic-independent-review-package-v0.1.manifest.yaml",
    "independent_review": "control-plane/registry/reviews/2026-07-18-yellow-agents-os-f6-r5-full-atomic-independent-review.yaml",
    "disposition": "control-plane/registry/reviews/2026-07-18-agents-os-f6-r5-independent-review-disposition-v0.1.yaml",
    "r6_start_decision": "control-plane/registry/decisions/2026-07-18-agents-os-f6-r6-immutability-schema-totality-closure-start-decision-v0.1.yaml",
}

ROOT_FIELDS = {
    "schema_version", "environment", "runtime_usable", "r5_bindings",
    "r5_fixture", "immutable_revision_history", "schema_profiles",
    "regression_catalog", "occurrence_assertions", "root_fingerprint",
}
WRAPPER_FIELDS = {"schema", "key", "ref", "payload", "fingerprint"}
PAYLOAD_FIELDS = {
    "assessment_id", "assessment_revision", "predecessor_ref",
    "predecessor_revision", "predecessor_fingerprint", "is_current_head",
    "owner_phase", "owner_contract_ref", "owner_contract_revision",
    "owner_contract_fingerprint", "barrier_ref", "barrier_fingerprint",
    "observed_event_sequence", "result", "assessed_subject",
}
SUBJECT_FIELDS = {
    "evidence_ref", "evidence_revision", "evidence_fingerprint",
    "requirement_id", "requirement_revision", "requirement_fingerprint",
    "attempt_ref", "attempt_revision", "attempt_context_fingerprint",
}
BINDING_FIELDS = {
    "attempt_ref", "attempt_revision", "attempt_context_fingerprint",
    "evidence_ref", "evidence_revision", "evidence_fingerprint",
    "assessment_ref", "assessment_revision", "assessment_fingerprint",
    "binding_fingerprint",
}
ATTEMPT_HISTORY_FIELDS = {
    "attempt_id", "attempt_revision", "attempt_ref", "attempt_fingerprint",
    "predecessor_ref", "predecessor_revision", "predecessor_fingerprint",
    "requirement_id", "requirement_revision", "requirement_fingerprint",
    "attempt_context_fingerprint", "evidence_set_fingerprint",
}
ASSESSMENT_HISTORY_FIELDS = {
    "assessment_id", "assessment_revision", "assessment_ref",
    "assessment_fingerprint", "predecessor_ref", "predecessor_revision",
    "predecessor_fingerprint", "assessed_subject_fingerprint",
    "attempt_context_fingerprint",
}
HISTORY_FIELDS = {
    "anchor_fixture_path", "anchor_fixture_sha256", "attempt_revisions",
    "assessment_revisions", "history_fingerprint",
}

SCHEMA_PROFILES = {
    "root_fields": sorted(ROOT_FIELDS),
    "contextual_wrapper_fields": sorted(WRAPPER_FIELDS),
    "contextual_payload_fields": sorted(PAYLOAD_FIELDS),
    "assessed_subject_fields": sorted(SUBJECT_FIELDS),
    "attempt_binding_fields": sorted(BINDING_FIELDS),
    "history_fields": sorted(HISTORY_FIELDS),
    "attempt_history_fields": sorted(ATTEMPT_HISTORY_FIELDS),
    "assessment_history_fields": sorted(ASSESSMENT_HISTORY_FIELDS),
    "strict_rules": [
        "duplicate_JSON_keys_reject_before_validation",
        "JSON_boolean_is_not_integer",
        "floats_and_nonfinite_numbers_forbidden",
        "integers_must_be_safe_range",
        "unknown_missing_or_malformed_fields_return_BLOCK",
        "schema_validation_precedes_fingerprint_trust",
    ],
}


def load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R5B = load("f6_r5_builder_for_r6", R5_BUILDER_PATH)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def h(domain: str, value: Any) -> str:
    return hashlib.sha256(domain.encode() + b"\0" + canonical(value)).hexdigest()


def file_hash(path: str) -> str:
    return hashlib.sha256((WORKSPACE_ROOT / path).read_bytes()).hexdigest()


def attempt_rows(r5: dict[str, Any]) -> list[dict[str, Any]]:
    return r5["r4_fixture"]["r3_fixture"]["effective_fixture"]["normative_objects"]["ValidationAttemptRevisionV0_1R2"]


def derive_history(r5: dict[str, Any]) -> dict[str, Any]:
    attempts = []
    for item in attempt_rows(r5):
        p = item["payload"]
        attempts.append({
            "attempt_id": p["attempt_id"],
            "attempt_revision": p["attempt_revision"],
            "attempt_ref": item["ref"],
            "attempt_fingerprint": item["fingerprint"],
            "predecessor_ref": p["predecessor_ref"],
            "predecessor_revision": p["predecessor_revision"],
            "predecessor_fingerprint": p["predecessor_fingerprint"],
            "requirement_id": p["requirement_id"],
            "requirement_revision": p["requirement_revision"],
            "requirement_fingerprint": p["requirement_fingerprint"],
            "attempt_context_fingerprint": p["context_binding"]["context_fingerprint"],
            "evidence_set_fingerprint": p["evidence_set_fingerprint"],
        })
    assessments = []
    for item in r5["contextual_evidence_assessments"]:
        p = item["payload"]
        assessments.append({
            "assessment_id": p["assessment_id"],
            "assessment_revision": p["assessment_revision"],
            "assessment_ref": item["ref"],
            "assessment_fingerprint": item["fingerprint"],
            "predecessor_ref": p["predecessor_ref"],
            "predecessor_revision": p["predecessor_revision"],
            "predecessor_fingerprint": p["predecessor_fingerprint"],
            "assessed_subject_fingerprint": h("agents-os.f6.r6.assessed-subject", p["assessed_subject"]),
            "attempt_context_fingerprint": p["assessed_subject"]["attempt_context_fingerprint"],
        })
    history = {
        "anchor_fixture_path": R5_FIXTURE_PATH,
        "anchor_fixture_sha256": file_hash(R5_FIXTURE_PATH),
        "attempt_revisions": sorted(attempts, key=lambda x: (x["attempt_id"], x["attempt_revision"])),
        "assessment_revisions": sorted(assessments, key=lambda x: (x["assessment_id"], x["assessment_revision"])),
    }
    history["history_fingerprint"] = h("agents-os.f6.r6.immutable-revision-history", history)
    return history


def build_fixture() -> dict[str, Any]:
    r5 = R5B.build_fixture()
    output = {
        "schema_version": "agents-os.f6.validation-current-decision-r6-proof.v0.1",
        "environment": "SYNTHETIC_TEST",
        "runtime_usable": False,
        "r5_bindings": {key: {"path": path, "sha256": file_hash(path)} for key, path in R5_PATHS.items()},
        "r5_fixture": r5,
        "immutable_revision_history": derive_history(r5),
        "schema_profiles": copy.deepcopy(SCHEMA_PROFILES),
        "regression_catalog": {
            "fixed_negative_total": 62,
            "R2_coordinated_count": 17,
            "R3_case_count": 7,
            "R4_context_case_count": 1,
            "R6_adversarial_case_count": 11,
        },
        "occurrence_assertions": copy.deepcopy(r5["occurrence_assertions"]),
    }
    output["root_fingerprint"] = h("agents-os.f6.r6.root", output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = canonical(build_fixture())
    args.output.write_bytes(payload)
    print("output:", args.output)
    print("bytes:", len(payload))
    print("sha256:", hashlib.sha256(payload).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
