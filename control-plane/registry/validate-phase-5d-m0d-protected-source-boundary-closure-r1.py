#!/usr/bin/env python3
"""Offline validator for the synthetic Phase 5D object-only boundary witness."""

from __future__ import annotations

import argparse
import copy
import json
import re
import runpy
import sys
from pathlib import Path
from typing import Any

BUILDER = runpy.run_path(
    str(Path(__file__).with_name("build-phase-5d-m0d-protected-source-boundary-closure-r1-witness.py"))
)
ALLOWED_BLOBS = BUILDER["ALLOWED_BLOBS"]
PROTECTED_PATHS = BUILDER["PROTECTED_PATHS"]
build_witness = BUILDER["build_witness"]


EXPECTED_SCHEMA = "agents-os.phase5d.protected-source-boundary.synthetic-witness.v0.1"
EXPECTED_COMMIT = "555b3b538f6eb736e530c2912de678c5941f9985"
EXPECTED_TREE = "fd82d403e79f36f749eb7f555b4736eae3eacdff"
EXPECTED_OPERATIONS = [
    "VERIFY_GIT_OBJECT_MEMBERSHIP",
    "READ_TREE_NAMES_ONLY",
    "ASSERT_PROTECTED_PATHS_UNREAD",
    "READ_ONLY_ALLOWLISTED_BLOBS_BY_EXACT_OID",
    "MATERIALIZE_TWO_INERT_PAYLOAD_FILES_ONLY",
    "OWNED_QUARANTINE_CLEANUP",
]
EXPECTED_FORBIDDEN = [
    "git_worktree_add",
    "git_checkout",
    "git_sparse_checkout",
    "git_archive",
    "generic_tree_blob_enumeration",
    "arbitrary_git_show_path",
    "protected_blob_object_lookup",
    "protected_path_content_read",
    "Host_lifecycle_or_plugin_operation",
]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OID_RE = re.compile(r"^[0-9a-f]{40}$")


def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def require_exact_keys(value: Any, expected: set[str], where: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{where}:TYPE")
        return False
    keys = set(value)
    if keys != expected:
        errors.append(f"{where}:KEYS")
        return False
    return True


def validate(doc: Any) -> list[str]:
    errors: list[str] = []
    if not require_exact_keys(
        doc,
        {
            "schema_version", "scope", "sealed_host", "protected_path_inventory",
            "allowed_blob_objects", "operation_sequence", "forbidden_operations",
            "no_full_worktree_or_checkout", "host_operation_count", "runtime_usable",
            "actual_execution_authorized", "result",
        },
        "root",
        errors,
    ):
        return errors
    if doc["schema_version"] != EXPECTED_SCHEMA:
        errors.append("root:SCHEMA_VERSION")
    if doc["scope"] != "SYNTHETIC_OBJECT_ONLY_NO_HOST":
        errors.append("root:SCOPE")
    if not require_exact_keys(doc["sealed_host"], {"commit", "tree"}, "sealed_host", errors):
        return errors
    if doc["sealed_host"]["commit"] != EXPECTED_COMMIT or doc["sealed_host"]["tree"] != EXPECTED_TREE:
        errors.append("sealed_host:IMMUTABLE_IDENTITY")
    inventory = doc["protected_path_inventory"]
    if type(inventory) is not list or len(inventory) != len(PROTECTED_PATHS):
        errors.append("protected_path_inventory:COUNT")
    else:
        for index, (actual, path) in enumerate(zip(inventory, PROTECTED_PATHS, strict=True)):
            if not require_exact_keys(actual, {"path", "content_read", "materialized"}, f"protected_path_inventory[{index}]", errors):
                continue
            if actual["path"] != path:
                errors.append(f"protected_path_inventory[{index}]:PATH")
            if type(actual["content_read"]) is not bool or actual["content_read"] is not False:
                errors.append(f"protected_path_inventory[{index}]:CONTENT_READ")
            if type(actual["materialized"]) is not bool or actual["materialized"] is not False:
                errors.append(f"protected_path_inventory[{index}]:MATERIALIZED")
    blobs = doc["allowed_blob_objects"]
    if type(blobs) is not list or len(blobs) != len(ALLOWED_BLOBS):
        errors.append("allowed_blob_objects:COUNT")
    else:
        for index, (actual, expected) in enumerate(zip(blobs, ALLOWED_BLOBS, strict=True)):
            if not require_exact_keys(actual, {"path", "blob_oid", "sha256"}, f"allowed_blob_objects[{index}]", errors):
                continue
            if actual != expected:
                errors.append(f"allowed_blob_objects[{index}]:IMMUTABLE_TUPLE")
            if type(actual["blob_oid"]) is not str or not OID_RE.fullmatch(actual["blob_oid"]):
                errors.append(f"allowed_blob_objects[{index}]:OID_TYPE")
            if type(actual["sha256"]) is not str or not SHA256_RE.fullmatch(actual["sha256"]):
                errors.append(f"allowed_blob_objects[{index}]:SHA_TYPE")
    if doc["operation_sequence"] != EXPECTED_OPERATIONS:
        errors.append("operation_sequence:EXACT_ALLOWLIST")
    if doc["forbidden_operations"] != EXPECTED_FORBIDDEN:
        errors.append("forbidden_operations:EXACT_INVENTORY")
    for field, expected in (
        ("no_full_worktree_or_checkout", True),
        ("runtime_usable", False),
        ("actual_execution_authorized", False),
    ):
        if type(doc[field]) is not bool or doc[field] is not expected:
            errors.append(f"{field}:BOOLEAN")
    if type(doc["host_operation_count"]) is not int or isinstance(doc["host_operation_count"], bool) or doc["host_operation_count"] != 0:
        errors.append("host_operation_count:ZERO_ONLY")
    if doc["result"] != "OBJECT_ONLY_PRECHECK_CANDIDATE":
        errors.append("result:CANDIDATE_ONLY")
    return errors


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="ascii"), object_pairs_hook=no_duplicates)


def self_test() -> int:
    cases: list[tuple[str, Any]] = []
    baseline = build_witness()
    cases.append(("baseline", baseline))
    mutation = copy.deepcopy(baseline); mutation["protected_path_inventory"][0]["content_read"] = True; cases.append(("protected_content_read", mutation))
    mutation = copy.deepcopy(baseline); mutation["protected_path_inventory"][0]["protected_blob_oid"] = "0" * 40; cases.append(("protected_identifier", mutation))
    mutation = copy.deepcopy(baseline); mutation["operation_sequence"][1] = "git_worktree_add"; cases.append(("worktree_operation", mutation))
    mutation = copy.deepcopy(baseline); mutation["allowed_blob_objects"][0]["sha256"] = "0" * 64; cases.append(("blob_tuple_substitution", mutation))
    mutation = copy.deepcopy(baseline); mutation["host_operation_count"] = 1; cases.append(("host_operation", mutation))
    mutation = copy.deepcopy(baseline); mutation["no_full_worktree_or_checkout"] = False; cases.append(("checkout_allowed", mutation))
    mutation = copy.deepcopy(baseline); mutation["runtime_usable"] = 0; cases.append(("integer_for_boolean", mutation))
    mutation = copy.deepcopy(baseline); mutation["protected_path_inventory"][0]["materialized"] = True; cases.append(("protected_materialized", mutation))
    mutation = copy.deepcopy(baseline); mutation["unknown"] = True; cases.append(("unknown_root", mutation))
    failures: list[str] = []
    for name, doc in cases:
        errors = validate(doc)
        if name == "baseline":
            if errors:
                failures.append(name)
        elif not errors:
            failures.append(name)
    try:
        json.loads('{"x":1,"x":2}', object_pairs_hook=no_duplicates)
        failures.append("duplicate_json_key")
    except ValueError:
        pass
    result = {"result": "PASS" if not failures else "BLOCKED", "cases": len(cases), "failures": failures}
    print(json.dumps(result, sort_keys=True))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.fixture is None:
        parser.error("fixture is required unless --self-test is used")
    try:
        errors = validate(load(args.fixture))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        errors = [f"input:BLOCKED:{type(exc).__name__}"]
    result = {"result": "PASS_NO_BLOCKER" if not errors else "BLOCKED", "errors": errors, "Host_operation_count": 0}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
