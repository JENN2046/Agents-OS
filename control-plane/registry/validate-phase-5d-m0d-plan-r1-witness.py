#!/usr/bin/env python3
"""Offline, closed-schema validator for the Phase 5D M0-D Plan R1 witness."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import yaml


PROFILE_PATH = Path(
    "control-plane/registry/drafts/"
    "2026-07-23-agents-os-phase-5d-m0d-quarantined-host-smoke-build-profile-v0.1-r1.yaml"
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKeyError(ValueError):
    pass


def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_pairs
    )


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def exact_keys(value: Any, keys: set[str], where: str, errors: list[str]) -> None:
    if type(value) is not dict:
        errors.append(f"{where}: expected object")
        return
    actual = set(value)
    if actual != keys:
        errors.append(
            f"{where}: fields mismatch missing={sorted(keys - actual)} extra={sorted(actual - keys)}"
        )


def valid_string(value: Any) -> bool:
    return type(value) is str and bool(value) and unicodedata.normalize("NFC", value) == value


def check_text_tree(value: Any, where: str, errors: list[str]) -> None:
    if type(value) is str:
        if not valid_string(value):
            errors.append(f"{where}: invalid string")
    elif type(value) is dict:
        for key, child in value.items():
            if type(key) is not str or not valid_string(key):
                errors.append(f"{where}: invalid object key")
            check_text_tree(child, f"{where}.{key}", errors)
    elif type(value) is list:
        for index, child in enumerate(value):
            check_text_tree(child, f"{where}[{index}]", errors)
    elif type(value) in (bool, int) or value is None:
        return
    else:
        errors.append(f"{where}: disallowed JSON value type")


def load_profile() -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        profile = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - reports a fail-closed parse error
        return None, [f"profile parse failed: {exc}"]
    exact_keys(
        profile,
        {
            "schema_version",
            "profile_id",
            "date",
            "owner",
            "agent_steward",
            "status",
            "runtime_usable",
            "terminal_outcome",
            "baseline",
            "ownership",
            "sealed_host_commitments",
            "future_source_inventory",
            "quarantine_contract",
            "future_smoke_contract",
            "state_machine",
            "validation",
            "authorization",
        },
        "profile",
        errors,
    )
    if type(profile) is not dict:
        return None, errors or ["profile: expected object"]
    baseline = profile.get("baseline")
    exact_keys(
        baseline,
        {
            "repository",
            "baseline_main_commit",
            "source_payload_commit",
            "source_root",
            "package_manifest_sha256",
            "blocked_plugin_manifest_sha256",
            "inert_commonjs_entrypoint_sha256",
            "VCPToolBox_sealed_commit",
            "VCPToolBox_sealed_tree",
        },
        "profile.baseline",
        errors,
    )
    if type(baseline) is dict:
        for key in (
            "baseline_main_commit",
            "source_payload_commit",
            "VCPToolBox_sealed_commit",
            "VCPToolBox_sealed_tree",
        ):
            if not HEX40.fullmatch(str(baseline.get(key, ""))):
                errors.append(f"profile.baseline.{key}: expected lowercase 40-hex")
        for key in (
            "package_manifest_sha256",
            "blocked_plugin_manifest_sha256",
            "inert_commonjs_entrypoint_sha256",
        ):
            if not HEX64.fullmatch(str(baseline.get(key, ""))):
                errors.append(f"profile.baseline.{key}: expected lowercase 64-hex")
    commitments = profile.get("sealed_host_commitments")
    if type(commitments) is not list or len(commitments) != 7:
        errors.append("profile.sealed_host_commitments: expected exactly seven rows")
    else:
        seen_paths: set[str] = set()
        for index, row in enumerate(commitments):
            exact_keys(row, {"path", "blob_oid", "sha256"}, f"profile.commitments[{index}]", errors)
            if type(row) is not dict:
                continue
            path = row.get("path")
            if not valid_string(path) or path.startswith("/") or ".." in path.split("/") or "\\" in path:
                errors.append(f"profile.commitments[{index}].path: unsafe path")
            if path in seen_paths:
                errors.append(f"profile.commitments[{index}].path: duplicate")
            seen_paths.add(path)
            if not HEX40.fullmatch(str(row.get("blob_oid", ""))):
                errors.append(f"profile.commitments[{index}].blob_oid: expected lowercase 40-hex")
            if not HEX64.fullmatch(str(row.get("sha256", ""))):
                errors.append(f"profile.commitments[{index}].sha256: expected lowercase 64-hex")
    exact_keys(
        profile.get("ownership"),
        {
            "extension_owner",
            "VCPToolBox_core_owner",
            "VCPToolBox_core_diff_expected",
            "VCPToolBox_worktree_read_or_write_during_plan",
            "parallel_Host_loader_or_runtime",
            "parallel_permission_identity_Task_Command_or_effect_authority",
        },
        "profile.ownership",
        errors,
    )
    if profile.get("ownership") != {
        "extension_owner": "JENN_OWNED_EXTERNAL_EXTENSION",
        "VCPToolBox_core_owner": "VCPToolBox",
        "VCPToolBox_core_diff_expected": "zero",
        "VCPToolBox_worktree_read_or_write_during_plan": "forbidden",
        "parallel_Host_loader_or_runtime": "forbidden",
        "parallel_permission_identity_Task_Command_or_effect_authority": "forbidden",
    }:
        errors.append("profile.ownership: frozen ownership boundary changed")
    exact_keys(
        profile.get("future_source_inventory"),
        {"create", "modify", "dependencies_or_locks_changed", "Rust_NAPI_or_SQLite_changed", "public_API_or_MCP_changed", "VCPToolBox_tracked_files_changed"},
        "profile.future_source_inventory",
        errors,
    )
    if profile.get("future_source_inventory") != {
        "create": [
            "extensions/agents-os-resident/tools/prepare-quarantined-host-smoke.mjs",
            "extensions/agents-os-resident/tools/validate-quarantined-host-smoke.mjs",
            "extensions/agents-os-resident/fixtures/quarantined-host-smoke-contract.v0.1.json",
            "extensions/agents-os-resident/tests/quarantined-host-smoke.mjs",
        ],
        "modify": [
            "extensions/agents-os-resident/README.md",
            "extensions/agents-os-resident/package-manifest.json",
        ],
        "dependencies_or_locks_changed": False,
        "Rust_NAPI_or_SQLite_changed": False,
        "public_API_or_MCP_changed": False,
        "VCPToolBox_tracked_files_changed": False,
    }:
        errors.append("profile.future_source_inventory: frozen file scope changed")
    exact_keys(
        profile.get("quarantine_contract"),
        {
            "environment",
            "caller_selected_source_host_output_manifest_or_config_path",
            "existing_root_or_residue",
            "network_provider_credentials_private_memory_user_content_existing_database",
            "archive_delivery",
            "canonical_workspace_manifest",
            "workspace_enabled_manifest",
            "transient_enabled_manifest",
        },
        "profile.quarantine_contract",
        errors,
    )
    expected_transient_manifest = {
        "possible_only_after_separate_Jenn_enablement_gate": True,
        "location": "newly_created_owned_quarantine_root_only",
        "must_be_deleted_before_terminal_success": True,
        "source_or_Host_worktree_persistence": "forbidden",
    }
    expected_quarantine = {
        "environment": "NEWLY_CREATED_OWNED_DISPOSABLE_NONPRODUCTION_ROOT",
        "caller_selected_source_host_output_manifest_or_config_path": "forbidden",
        "existing_root_or_residue": "BLOCKED",
        "network_provider_credentials_private_memory_user_content_existing_database": "forbidden",
        "archive_delivery": "separately_Jenn_authorized_only",
        "canonical_workspace_manifest": "plugin-manifest.json.block",
        "workspace_enabled_manifest": "forbidden",
        "transient_enabled_manifest": expected_transient_manifest,
    }
    if profile.get("quarantine_contract") != expected_quarantine:
        errors.append("profile.quarantine_contract: frozen isolation boundary changed")
    exact_keys(
        profile.get("future_smoke_contract"),
        {
            "current_plan_result",
            "lifecycle_methods_allowed_only",
            "processToolCall_or_native_addon_load",
            "native_NAPI_methods_allowed",
            "expected_initialize_result",
            "expected_shutdown_result",
            "host_lifecycle_argument_contract",
            "Host_discovery_or_lifecycle_invocation",
            "unexpected_call_result",
            "cleanup_required_before_terminal_success",
        },
        "profile.future_smoke_contract",
        errors,
    )
    expected_smoke = {
        "current_plan_result": "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY",
        "lifecycle_methods_allowed_only": ["initialize", "shutdown"],
        "processToolCall_or_native_addon_load": "forbidden",
        "native_NAPI_methods_allowed": [],
        "expected_initialize_result": {"initialized": False},
        "expected_shutdown_result": {"shutdown": True},
        "host_lifecycle_argument_contract": "future_hash_bound_Host_contract_required",
        "Host_discovery_or_lifecycle_invocation": "separately_Jenn_authorized_only",
        "unexpected_call_result": "BLOCKED",
        "cleanup_required_before_terminal_success": True,
    }
    if profile.get("future_smoke_contract") != expected_smoke:
        errors.append("profile.future_smoke_contract: frozen no-load boundary changed")
    exact_keys(
        profile.get("state_machine"),
        {"allowed_sequence", "current_terminal_state", "skipped_reordered_or_unknown_state", "any_failure_requires_cleanup"},
        "profile.state_machine",
        errors,
    )
    expected_state_machine = {
        "allowed_sequence": [
            "NOT_STARTED",
            "QUARANTINE_CREATED",
            "SEALED_INPUTS_VERIFIED",
            "BLOCKED_PACKAGE_STAGED",
            "FUTURE_JENN_ENABLEMENT_GATE",
            "FUTURE_JENN_HOST_LOAD_GATE",
            "INITIALIZED_INERT",
            "SHUTDOWN_INERT",
            "QUARANTINE_REMOVED",
        ],
        "current_terminal_state": "NOT_EXECUTED",
        "skipped_reordered_or_unknown_state": "BLOCKED",
        "any_failure_requires_cleanup": True,
    }
    if profile.get("state_machine") != expected_state_machine:
        errors.append("profile.state_machine: frozen sequence changed")
    expected_authorization = {
        "plan_authoring_authorized": True,
        "implementation_or_source_modification_authorized": False,
        "VCPToolBox_change_or_start_authorized": False,
        "clean_Host_worktree_creation_or_inspection_authorized": False,
        "archive_delivery_or_installation_authorized": False,
        "plugin_enablement_authorized": False,
        "Host_loading_authorized": False,
        "native_addon_loading_authorized": False,
        "runtime_activation_authorized": False,
        "database_creation_or_connection_authorized": False,
        "production_authentication_authorized": False,
        "private_Memory_access_authorized": False,
        "provider_sensing_or_real_effect_authorized": False,
        "Git_delivery_authorized": False,
        "separate_Jenn_plan_freeze_required": True,
        "separate_Jenn_implementation_start_required_after_plan_durability": True,
    }
    exact_keys(profile.get("authorization"), set(expected_authorization), "profile.authorization", errors)
    if profile.get("authorization") != expected_authorization:
        errors.append("profile.authorization: plan-only boundary changed")
    if profile.get("runtime_usable") is not False or profile.get("terminal_outcome") != "NOT_EXECUTED":
        errors.append("profile: current boundary must remain runtime-unusable and NOT_EXECUTED")
    check_text_tree(profile, "profile", errors)
    return profile, errors


def expected_witness(profile: dict[str, Any]) -> dict[str, Any]:
    baseline = profile["baseline"]
    quarantine = profile["quarantine_contract"]
    smoke = profile["future_smoke_contract"]
    state_machine = profile["state_machine"]
    commitments = profile["sealed_host_commitments"]
    return {
        "authorization": profile["authorization"],
        "baseline": {
            "VCPToolBox_sealed_commit": baseline["VCPToolBox_sealed_commit"],
            "VCPToolBox_sealed_tree": baseline["VCPToolBox_sealed_tree"],
            "baseline_main_commit": baseline["baseline_main_commit"],
            "blocked_plugin_manifest_sha256": baseline["blocked_plugin_manifest_sha256"],
            "inert_commonjs_entrypoint_sha256": baseline["inert_commonjs_entrypoint_sha256"],
            "package_manifest_sha256": baseline["package_manifest_sha256"],
            "repository": baseline["repository"],
            "source_payload_commit": baseline["source_payload_commit"],
            "source_root": baseline["source_root"],
        },
        "claimed_decision": smoke["current_plan_result"],
        "environment": "SYNTHETIC_PLAN_ONLY",
        "quarantine_contract": {
            "caller_selected_source_host_output_manifest_or_config_path": quarantine[
                "caller_selected_source_host_output_manifest_or_config_path"
            ],
            "environment": quarantine["environment"],
            "existing_root_or_residue": quarantine["existing_root_or_residue"],
            "transient_enabled_manifest": quarantine["transient_enabled_manifest"],
            "workspace_enabled_manifest": quarantine["workspace_enabled_manifest"],
        },
        "real_occurrence_count": 0,
        "runtime_usable": False,
        "schema_version": "agents-os.m0d-synthetic-plan-witness.v0.1",
        "sealed_host_commitments": commitments,
        "sealed_host_commitments_sha256": hashlib.sha256(canonical_bytes(commitments)).hexdigest(),
        "smoke_contract": {
            "expected_initialize_result": smoke["expected_initialize_result"],
            "expected_shutdown_result": smoke["expected_shutdown_result"],
            "host_lifecycle_argument_contract": smoke["host_lifecycle_argument_contract"],
            "lifecycle_methods_allowed_only": smoke["lifecycle_methods_allowed_only"],
            "native_NAPI_methods_allowed": smoke["native_NAPI_methods_allowed"],
            "processToolCall_or_native_addon_load": smoke["processToolCall_or_native_addon_load"],
        },
        "state_machine": {
            "allowed_sequence": state_machine["allowed_sequence"],
            "current_terminal_state": state_machine["current_terminal_state"],
            "observed_sequence": ["NOT_STARTED"],
        },
    }


def validate(value: Any, profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    exact_keys(
        value,
        {
            "authorization",
            "baseline",
            "claimed_decision",
            "environment",
            "quarantine_contract",
            "real_occurrence_count",
            "runtime_usable",
            "schema_version",
            "sealed_host_commitments",
            "sealed_host_commitments_sha256",
            "smoke_contract",
            "state_machine",
        },
        "witness",
        errors,
    )
    if type(value) is not dict:
        return errors or ["witness: expected object"]
    check_text_tree(value, "witness", errors)
    if value.get("schema_version") != "agents-os.m0d-synthetic-plan-witness.v0.1":
        errors.append("witness.schema_version: mismatch")
    if value.get("environment") != "SYNTHETIC_PLAN_ONLY":
        errors.append("witness.environment: must be synthetic plan only")
    if type(value.get("runtime_usable")) is not bool or value.get("runtime_usable") is not False:
        errors.append("witness.runtime_usable: must be JSON false")
    if type(value.get("real_occurrence_count")) is not int or value.get("real_occurrence_count") != 0:
        errors.append("witness.real_occurrence_count: must be exact integer zero")
    expected = expected_witness(profile)
    for key in (
        "baseline",
        "quarantine_contract",
        "smoke_contract",
        "state_machine",
        "authorization",
        "sealed_host_commitments",
    ):
        if value.get(key) != expected[key]:
            errors.append(f"witness.{key}: does not match independently loaded profile")
    digest = hashlib.sha256(canonical_bytes(value.get("sealed_host_commitments"))).hexdigest()
    if value.get("sealed_host_commitments_sha256") != digest:
        errors.append("witness.sealed_host_commitments_sha256: mismatch")
    if not HEX64.fullmatch(str(value.get("sealed_host_commitments_sha256", ""))):
        errors.append("witness.sealed_host_commitments_sha256: expected lowercase 64-hex")
    if value.get("claimed_decision") != expected["claimed_decision"]:
        errors.append("witness.claimed_decision: not derived from the profile boundary")
    return errors


def run_fixture(path: Path) -> tuple[list[str], str]:
    profile, profile_errors = load_profile()
    if profile is None:
        return profile_errors, "BLOCKED"
    try:
        value = strict_json(path)
    except Exception as exc:
        return profile_errors + [f"fixture parse failed: {exc}"], "BLOCKED"
    errors = profile_errors + validate(value, profile)
    return errors, "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY" if not errors else "BLOCKED"


def self_test(fixture: Path) -> list[str]:
    errors, result = run_fixture(fixture)
    if errors or result != "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY":
        return ["positive fixture did not pass"] + errors
    profile, profile_errors = load_profile()
    if profile is None or profile_errors:
        return ["profile invalid during self-test"] + profile_errors
    value = strict_json(fixture)
    mutations: list[tuple[str, Any]] = []
    for name, mutate in (
        ("sealed_commit", lambda v: v["baseline"].__setitem__("VCPToolBox_sealed_commit", "0" * 40)),
        ("host_sha", lambda v: v["sealed_host_commitments"][0].__setitem__("sha256", "0" * 64)),
        ("caller_path", lambda v: v["quarantine_contract"].__setitem__("caller_selected_source_host_output_manifest_or_config_path", "allowed")),
        ("enabled_manifest", lambda v: v["quarantine_contract"].__setitem__("workspace_enabled_manifest", "allowed")),
        ("process_tool_call", lambda v: v["smoke_contract"].__setitem__("processToolCall_or_native_addon_load", "allowed")),
        ("native_methods", lambda v: v["smoke_contract"].__setitem__("native_NAPI_methods_allowed", ["execute_query"])),
        ("runtime", lambda v: v.__setitem__("runtime_usable", True)),
        ("occurrence", lambda v: v.__setitem__("real_occurrence_count", 1)),
        ("state_order", lambda v: v["state_machine"].__setitem__("observed_sequence", ["SHUTDOWN_INERT"])),
        ("unknown_field", lambda v: v.__setitem__("implementation_frozen", True)),
    ):
        mutated = copy.deepcopy(value)
        mutate(mutated)
        mutations.append((name, mutated))
    failures: list[str] = []
    for name, mutated in mutations:
        if not validate(mutated, profile):
            failures.append(f"mutation accepted: {name}")
    try:
        json.loads('{"x":1,"x":2}', object_pairs_hook=no_duplicate_pairs)
        failures.append("duplicate JSON key accepted")
    except DuplicateKeyError:
        pass
    return failures


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 3) or (len(argv) == 3 and argv[2] != "--self-test"):
        print(f"usage: {argv[0]} FIXTURE_PATH [--self-test]", file=sys.stderr)
        return 2
    fixture = Path(argv[1])
    errors, result = run_fixture(fixture)
    if len(argv) == 3:
        errors += self_test(fixture)
    payload = {"errors": errors, "result": result}
    print(json.dumps(payload, separators=(",", ":"), sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
