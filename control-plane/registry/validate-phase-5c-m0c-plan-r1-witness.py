#!/usr/bin/env python3
"""Offline semantic validator for the Phase 5C M0-C R1 planning witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-offline-plugin-packaging-build-profile-v0.1-r1.yaml"
TOP_KEYS = {"schema_version", "profile_sha256", "sealed_host_input_count", "public_napi_methods", "cases", "terminal_outcome", "root_fingerprint"}
CASE_KEYS = {"case_id", "environment", "source_sealed", "package_inventory_exact", "manifest_state", "host_contract_exact", "temporary_staging_only", "public_napi_method_count", "vcptoolbox_write_count", "runtime_activation_count", "real_occurrence_count", "derived_result", "row_fingerprint"}
METHODS = ["execute_command", "execute_query", "claim_outbox", "acknowledge_outbox", "reconcile"]


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_strict(path: Path) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def is_int(value: object) -> bool:
    return type(value) is int and 0 <= value <= 9007199254740991


def derive(row: dict[str, object]) -> str:
    favorable = (
        row["environment"] == "SYNTHETIC_TEST"
        and row["source_sealed"] is True
        and row["package_inventory_exact"] is True
        and row["manifest_state"] == "BLOCKED"
        and row["host_contract_exact"] is True
        and row["temporary_staging_only"] is True
        and row["public_napi_method_count"] == 5
        and row["vcptoolbox_write_count"] == 0
        and row["runtime_activation_count"] == 0
        and row["real_occurrence_count"] == 0
    )
    return "PACKAGE_COMPATIBLE_PREVIEW" if favorable else "BLOCKED"


def validate(doc: object) -> list[str]:
    errors: list[str] = []
    if type(doc) is not dict:
        return ["root must be object"]
    if set(doc) != TOP_KEYS:
        errors.append("root field inventory mismatch")
        return errors
    if doc["schema_version"] != "agents-os.m0c-plan-witness.v0.1-r1": errors.append("schema_version mismatch")
    if doc["profile_sha256"] != hashlib.sha256(PROFILE.read_bytes()).hexdigest(): errors.append("profile digest mismatch")
    if doc["sealed_host_input_count"] != 7: errors.append("sealed host input count mismatch")
    if doc["public_napi_methods"] != METHODS: errors.append("public N-API inventory mismatch")
    if doc["terminal_outcome"] != "NOT_ACTIVATED": errors.append("terminal outcome mismatch")
    cases = doc["cases"]
    if type(cases) is not list or len(cases) != 11:
        errors.append("case inventory mismatch")
        return errors
    expected_ids = [f"C{i:02d}_{name}" for i, name in enumerate(["BASELINE", "ENABLED_MANIFEST", "UNSEALED_SOURCE", "EXTRA_FILE", "HOST_MISMATCH", "CALLER_STAGING", "NAPI_EXPANSION", "VCP_WRITE", "RUNTIME", "REAL_OCCURRENCE", "PRODUCTION_ENV"], 1)]
    if [row.get("case_id") if type(row) is dict else None for row in cases] != expected_ids: errors.append("case ids or order mismatch")
    for index, row in enumerate(cases):
        if type(row) is not dict or set(row) != CASE_KEYS:
            errors.append(f"case {index} field inventory mismatch")
            continue
        for key in ("source_sealed", "package_inventory_exact", "host_contract_exact", "temporary_staging_only"):
            if type(row[key]) is not bool: errors.append(f"case {index} {key} must be boolean")
        for key in ("public_napi_method_count", "vcptoolbox_write_count", "runtime_activation_count", "real_occurrence_count"):
            if not is_int(row[key]): errors.append(f"case {index} {key} invalid integer")
        if row["environment"] not in {"SYNTHETIC_TEST", "PRODUCTION"}: errors.append(f"case {index} environment invalid")
        if row["manifest_state"] not in {"BLOCKED", "ENABLED"}: errors.append(f"case {index} manifest state invalid")
        claimed_fp = row["row_fingerprint"]
        unsigned = dict(row); unsigned.pop("row_fingerprint")
        if claimed_fp != digest(unsigned): errors.append(f"case {index} row fingerprint mismatch")
        if row["derived_result"] != derive(row): errors.append(f"case {index} derived result mismatch")
    claimed_root = doc["root_fingerprint"]
    unsigned_doc = dict(doc); unsigned_doc.pop("root_fingerprint")
    if claimed_root != digest(unsigned_doc): errors.append("root fingerprint mismatch")
    return errors


def resign(doc: dict[str, object]) -> None:
    for row in doc["cases"]:
        unsigned = dict(row); unsigned.pop("row_fingerprint", None)
        row["row_fingerprint"] = digest(unsigned)
    unsigned_doc = dict(doc); unsigned_doc.pop("root_fingerprint", None)
    doc["root_fingerprint"] = digest(unsigned_doc)


def self_test(doc: dict[str, object]) -> list[str]:
    failures: list[str] = []
    mutations = [
        lambda d: d.update({"unknown": 1}),
        lambda d: d["cases"][0].update({"manifest_state": "ENABLED", "derived_result": "PACKAGE_COMPATIBLE_PREVIEW"}),
        lambda d: d["cases"][0].update({"vcptoolbox_write_count": 1, "derived_result": "PACKAGE_COMPATIBLE_PREVIEW"}),
        lambda d: d["cases"][0].update({"runtime_activation_count": 1, "derived_result": "PACKAGE_COMPATIBLE_PREVIEW"}),
        lambda d: d["cases"][0].update({"public_napi_method_count": 6, "derived_result": "PACKAGE_COMPATIBLE_PREVIEW"}),
        lambda d: d.update({"public_napi_methods": METHODS + ["start_runtime"]}),
        lambda d: d["cases"].reverse(),
        lambda d: d["cases"][0].update({"source_sealed": 1}),
    ]
    for index, mutate in enumerate(mutations, 1):
        candidate = copy.deepcopy(doc); mutate(candidate); resign(candidate)
        if not validate(candidate): failures.append(f"mutation {index} accepted")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        doc = load_strict(args.fixture)
        errors = validate(doc)
        if args.self_test and not errors: errors.extend(self_test(doc))
    except Exception as exc:
        errors = [f"stable BLOCK: {type(exc).__name__}: {exc}"]
    if errors:
        print(json.dumps({"result": "BLOCK", "errors": errors}, indent=2))
        return 1
    print(json.dumps({"result": "PASS", "cases": 11, "negative_mutations": 8 if args.self_test else 0, "terminal_outcome": "NOT_ACTIVATED"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
