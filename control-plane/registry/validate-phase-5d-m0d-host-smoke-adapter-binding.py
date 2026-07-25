#!/usr/bin/env python3
"""Offline validator for the Phase 5D M0-D Host-smoke adapter-binding closure.

This validator consumes only control-plane documents and synthetic fixture bytes.
It never opens VCPToolBox, materializes a payload, or invokes a Host API.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "control-plane/registry/drafts/2026-07-24-agents-os-phase-5d-m0d-host-smoke-adapter-binding-contract-closure-v0.1-r1.md"
PROFILE_PATH = ROOT / "control-plane/registry/drafts/2026-07-24-agents-os-phase-5d-m0d-host-smoke-adapter-binding-evidence-profile-v0.1-r1.yaml"
FIXTURE_PATH = ROOT / "control-plane/registry/examples/2026-07-24-agents-os-phase-5d-m0d-host-smoke-adapter-binding-fixture-v0.1.json"

SHA256 = re.compile(r"^[0-9a-f]{64}$")

ANCHOR = {
    "VCPToolBox_commit": "555b3b538f6eb736e530c2912de678c5941f9985",
    "VCPToolBox_tree": "fd82d403e79f36f749eb7f555b4736eae3eacdff",
    "source_preflight_sha256": "3a420c5ff995fc28839ba2340d69a23501bf9bd517d77ef552a9217cdfa14a3d",
    "inert_entrypoint_sha256": "51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec",
    "blocked_manifest_sha256": "25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0",
}

ROOT_FIELDS = ["schema_version", "contract_path", "profile_path", "immutable_anchor", "cases"]
CASE_FIELDS = [
    "case_id", "environment", "owner_contract", "hermetic_dependency_inventory",
    "inert_payload", "transient_enabled_manifest", "lifecycle_binding", "expected_result",
    "runtime_usable", "actual_Host_smoke_execution_authorized", "Host_operation_count",
]
CASE_IDS = ["C01_MISSING_OWNER_BINDING", "C02_SYNTHETIC_COMPLETE_SHAPE"]
SECTION_NAMES = [
    "hermetic_quarantine_root", "Host_module_and_dependency_inventory", "inert_payload",
    "transient_enabled_manifest", "host_discovery", "initialize", "shutdown", "quarantine_cleanup",
]
PROFILE_CROSS_FIELD_RULES = [
    "all_cases_require_SYNTHETIC_TEST_environment",
    "all_cases_require_runtime_usable_false",
    "all_cases_require_actual_Host_smoke_execution_authorized_false",
    "all_cases_require_Host_operation_count_zero",
    "all_boolean_and_integer_fields_require_strict_JSON_types",
    "all_mapping_keys_require_strict_JSON_strings",
    "C01_requires_null_owner_contract_and_inventory",
    "C02_requires_complete_synthetic_owner_contract_shape",
    "C02_requires_synthetic_unmaterialized_inventory",
    "C02_requires_unmaterialized_transient_manifest",
    "all_sections_require_strict_ref_positive_revision_lowercase_sha256",
    "synthetic_fingerprints_must_derive_from_their_synthetic_reference_bytes",
    "processToolCall_authorized_must_be_false",
    "unknown_or_missing_field_result_BLOCKED",
]
PROFILE_FORBIDDEN_CLAIMS = [
    "owner_issued_actual_Host_contract_present",
    "actual_Host_smoke_execution_authorized",
    "Host_operation_count_greater_than_zero",
    "real_quarantine_root_created",
    "enabled_manifest_materialized",
    "processToolCall_or_native_addon_authorized",
    "runtime_database_dependency_install_provider_private_Memory_sensing_or_effect",
]


def exact_keys(value: Any, fields: list[str]) -> bool:
    return isinstance(value, dict) and list(value) == fields


def valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def stable_ref(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and unicodedata.normalize("NFC", value) == value


def positive_int(value: Any) -> bool:
    return type(value) is int and 0 < value <= 9007199254740991


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def error(errors: list[str], code: str) -> None:
    errors.append(code)


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                "mapping keys must be strings", key_node.start_mark,
            )
        if key in mapping:
            raise ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key {key!r}", key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return yaml.load(stream, Loader=UniqueKeyLoader)


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=reject_duplicate_json_keys)


def validate_contract_text(path: Path, errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        error(errors, "CONTRACT_UNAVAILABLE")
        return
    required = [
        "PHASE_5D_M0D_HOST_SMOKE_ADAPTER_BINDING_CLOSURE_V0_1_R1",
        "Complete Host module and dependency inventory",
        "SYNTHETIC_ADAPTER_BINDING_SHAPE_VALIDATED",
        "Host_operation_count: 0",
        "actual_Host_smoke_execution_authorized: false",
        "All boolean fields in the profile and fixture use strict JSON booleans.",
        "VCPToolBox_worktree_read_write_clone_checkout_or_start: forbidden",
    ]
    if any(item not in text for item in required):
        error(errors, "CONTRACT_REQUIRED_CLAUSE_MISSING")
    if "actual_Host_smoke_execution_authorized: true" in text:
        error(errors, "CONTRACT_EXECUTION_AUTHORITY_ESCALATION")


def validate_profile(profile: Any, errors: list[str]) -> None:
    required_root = [
        "schema_version", "profile_id", "status", "contract_id", "runtime_usable",
        "actual_Host_smoke_execution_authorized", "Host_operation_count", "terminal_outcome",
        "closed_fixture_root_fields", "closed_case_fields", "case_ids_in_order",
        "immutable_anchor_fields", "owner_contract_fields", "required_sections_in_order",
        "section_fields", "inventory_fields", "inventory_entry_fields", "inert_payload_fields",
        "transient_enabled_manifest_fields", "lifecycle_binding_fields", "current_allowed_results",
        "cross_field_rules", "forbidden_claims",
    ]
    if not exact_keys(profile, required_root):
        error(errors, "PROFILE_ROOT_SCHEMA_INVALID")
        return
    if profile["schema_version"] != "agents-os.phase5d.m0d.host-smoke-adapter-binding-evidence-profile.v0.1-r1":
        error(errors, "PROFILE_SCHEMA_VERSION_INVALID")
    if profile["profile_id"] != "PHASE_5D_M0D_HOST_SMOKE_ADAPTER_BINDING_EVIDENCE_PROFILE_V0_1_R1":
        error(errors, "PROFILE_ID_INVALID")
    if profile["contract_id"] != "PHASE_5D_M0D_HOST_SMOKE_ADAPTER_BINDING_CLOSURE_V0_1_R1":
        error(errors, "PROFILE_CONTRACT_BINDING_INVALID")
    if profile["status"] != "FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW":
        error(errors, "PROFILE_STATUS_INVALID")
    if profile["runtime_usable"] is not False or profile["actual_Host_smoke_execution_authorized"] is not False:
        error(errors, "PROFILE_RUNTIME_BOUNDARY_INVALID")
    if (
        type(profile["Host_operation_count"]) is not int
        or profile["Host_operation_count"] != 0
        or profile["terminal_outcome"] != "NOT_EXECUTED"
    ):
        error(errors, "PROFILE_OPERATION_BOUNDARY_INVALID")
    if profile["closed_fixture_root_fields"] != ROOT_FIELDS or profile["closed_case_fields"] != CASE_FIELDS:
        error(errors, "PROFILE_CLOSED_FIELDS_INVALID")
    if profile["case_ids_in_order"] != CASE_IDS or profile["required_sections_in_order"] != SECTION_NAMES:
        error(errors, "PROFILE_ORDERING_INVALID")
    if profile["immutable_anchor_fields"] != list(ANCHOR):
        error(errors, "PROFILE_ANCHOR_SCHEMA_INVALID")
    if profile["owner_contract_fields"] != ["kind", "contract_ref", "contract_revision", "contract_sha256", "sections"]:
        error(errors, "PROFILE_OWNER_SCHEMA_INVALID")
    if profile["section_fields"] != ["ref", "revision", "sha256"]:
        error(errors, "PROFILE_SECTION_SCHEMA_INVALID")
    if profile["inventory_fields"] != ["kind", "complete_for_actual_Host", "entries"]:
        error(errors, "PROFILE_INVENTORY_SCHEMA_INVALID")
    if profile["inventory_entry_fields"] != ["logical_name", "source_kind", "immutable_identity", "sha256", "resolution_ordinal"]:
        error(errors, "PROFILE_INVENTORY_ENTRY_SCHEMA_INVALID")
    if profile["inert_payload_fields"] != ["entrypoint_sha256", "blocked_manifest_sha256", "processToolCall_authorized"]:
        error(errors, "PROFILE_PAYLOAD_SCHEMA_INVALID")
    if profile["transient_enabled_manifest_fields"] != ["target_relative_path", "byte_count", "sha256", "materialized"]:
        error(errors, "PROFILE_MANIFEST_SCHEMA_INVALID")
    if profile["lifecycle_binding_fields"] != [
        "host_discovery_selector", "initialize_selector", "initialize_argument_bytes_sha256",
        "initialize_expected_return", "shutdown_selector", "shutdown_argument_bytes_sha256",
        "shutdown_expected_return", "cleanup_selector",
    ]:
        error(errors, "PROFILE_LIFECYCLE_SCHEMA_INVALID")
    if profile["current_allowed_results"] != [
        "BLOCKED_MISSING_OWNER_ISSUED_ADAPTER_BINDING",
        "BLOCKED_HERMETIC_DEPENDENCY_INVENTORY_UNAVAILABLE",
        "SYNTHETIC_ADAPTER_BINDING_SHAPE_VALIDATED",
    ]:
        error(errors, "PROFILE_RESULT_SET_INVALID")
    if profile["cross_field_rules"] != PROFILE_CROSS_FIELD_RULES:
        error(errors, "PROFILE_CROSS_FIELD_RULES_INVALID")
    if profile["forbidden_claims"] != PROFILE_FORBIDDEN_CLAIMS:
        error(errors, "PROFILE_FORBIDDEN_CLAIMS_INVALID")


def validate_payload(payload: Any, errors: list[str]) -> None:
    if not exact_keys(payload, ["entrypoint_sha256", "blocked_manifest_sha256", "processToolCall_authorized"]):
        error(errors, "INERT_PAYLOAD_SCHEMA_INVALID")
        return
    if not valid_sha256(payload["entrypoint_sha256"]) or payload["entrypoint_sha256"] != ANCHOR["inert_entrypoint_sha256"]:
        error(errors, "INERT_ENTRYPOINT_BINDING_INVALID")
    if not valid_sha256(payload["blocked_manifest_sha256"]) or payload["blocked_manifest_sha256"] != ANCHOR["blocked_manifest_sha256"]:
        error(errors, "BLOCKED_MANIFEST_BINDING_INVALID")
    if payload["processToolCall_authorized"] is not False:
        error(errors, "PROCESS_TOOL_CALL_AUTHORITY_ESCALATION")


def validate_transient_manifest(manifest: Any, errors: list[str]) -> None:
    fields = ["target_relative_path", "byte_count", "sha256", "materialized"]
    if not exact_keys(manifest, fields):
        error(errors, "TRANSIENT_MANIFEST_BINDING_INVALID")
        return
    if (
        type(manifest["target_relative_path"]) is not str
        or manifest["target_relative_path"] != "Plugin/AGENTSOSResident/plugin-manifest.json"
        or type(manifest["byte_count"]) is not int
        or manifest["byte_count"] != 413
        or not valid_sha256(manifest["sha256"])
        or manifest["sha256"] != ANCHOR["blocked_manifest_sha256"]
        or manifest["materialized"] is not False
    ):
        error(errors, "TRANSIENT_MANIFEST_BINDING_INVALID")


def validate_owner_contract(owner: Any, errors: list[str]) -> None:
    fields = ["kind", "contract_ref", "contract_revision", "contract_sha256", "sections"]
    if not exact_keys(owner, fields):
        error(errors, "OWNER_CONTRACT_SCHEMA_INVALID")
        return
    if owner["kind"] != "SYNTHETIC_SHAPE_ONLY" or not stable_ref(owner["contract_ref"]) or not owner["contract_ref"].startswith("synthetic:"):
        error(errors, "OWNER_CONTRACT_KIND_INVALID")
    if not positive_int(owner["contract_revision"]) or owner["contract_revision"] != 1:
        error(errors, "OWNER_CONTRACT_REVISION_INVALID")
    if not valid_sha256(owner["contract_sha256"]) or owner["contract_sha256"] != sha256_text(owner["contract_ref"]):
        error(errors, "OWNER_CONTRACT_FINGERPRINT_INVALID")
    sections = owner["sections"]
    if not isinstance(sections, dict) or list(sections) != SECTION_NAMES:
        error(errors, "OWNER_CONTRACT_SECTION_INVENTORY_INVALID")
        return
    for name in SECTION_NAMES:
        section = sections[name]
        if not exact_keys(section, ["ref", "revision", "sha256"]):
            error(errors, f"OWNER_SECTION_SCHEMA_INVALID:{name}")
            continue
        if not stable_ref(section["ref"]) or not section["ref"].startswith("synthetic:"):
            error(errors, f"OWNER_SECTION_REF_INVALID:{name}")
        if not positive_int(section["revision"]) or section["revision"] != 1:
            error(errors, f"OWNER_SECTION_REVISION_INVALID:{name}")
        if not valid_sha256(section["sha256"]) or section["sha256"] != sha256_text(section["ref"]):
            error(errors, f"OWNER_SECTION_FINGERPRINT_INVALID:{name}")


def validate_inventory(inventory: Any, errors: list[str]) -> None:
    if not exact_keys(inventory, ["kind", "complete_for_actual_Host", "entries"]):
        error(errors, "INVENTORY_SCHEMA_INVALID")
        return
    if inventory["kind"] != "SYNTHETIC_UNMATERIALIZED" or inventory["complete_for_actual_Host"] is not False:
        error(errors, "INVENTORY_RUNTIME_CLAIM_INVALID")
    entries = inventory["entries"]
    if not isinstance(entries, list) or not entries:
        error(errors, "INVENTORY_ENTRY_SET_INVALID")
        return
    for ordinal, entry in enumerate(entries, start=1):
        if not exact_keys(entry, ["logical_name", "source_kind", "immutable_identity", "sha256", "resolution_ordinal"]):
            error(errors, f"INVENTORY_ENTRY_SCHEMA_INVALID:{ordinal}")
            continue
        if not stable_ref(entry["logical_name"]) or not entry["logical_name"].startswith("synthetic:"):
            error(errors, f"INVENTORY_ENTRY_NAME_INVALID:{ordinal}")
        if entry["source_kind"] != "SYNTHETIC":
            error(errors, f"INVENTORY_ENTRY_KIND_INVALID:{ordinal}")
        if not stable_ref(entry["immutable_identity"]) or not entry["immutable_identity"].startswith("synthetic:"):
            error(errors, f"INVENTORY_ENTRY_IDENTITY_INVALID:{ordinal}")
        if not valid_sha256(entry["sha256"]) or entry["sha256"] != sha256_text(entry["immutable_identity"]):
            error(errors, f"INVENTORY_ENTRY_FINGERPRINT_INVALID:{ordinal}")
        if not positive_int(entry["resolution_ordinal"]) or entry["resolution_ordinal"] != ordinal:
            error(errors, f"INVENTORY_ENTRY_ORDER_INVALID:{ordinal}")


def validate_lifecycle(lifecycle: Any, sections: Any, errors: list[str]) -> None:
    fields = [
        "host_discovery_selector", "initialize_selector", "initialize_argument_bytes_sha256",
        "initialize_expected_return", "shutdown_selector", "shutdown_argument_bytes_sha256",
        "shutdown_expected_return", "cleanup_selector",
    ]
    if not exact_keys(lifecycle, fields):
        error(errors, "LIFECYCLE_BINDING_SCHEMA_INVALID")
        return
    if not isinstance(sections, dict) or "initialize" not in sections or "shutdown" not in sections:
        error(errors, "LIFECYCLE_OWNER_SECTION_UNAVAILABLE")
        return
    if not isinstance(sections["initialize"], dict) or not isinstance(sections["shutdown"], dict):
        error(errors, "LIFECYCLE_OWNER_SECTION_UNAVAILABLE")
        return
    if not isinstance(sections["initialize"].get("ref"), str) or not isinstance(sections["shutdown"].get("ref"), str):
        error(errors, "LIFECYCLE_OWNER_SECTION_UNAVAILABLE")
        return
    for field in ["host_discovery_selector", "initialize_selector", "shutdown_selector", "cleanup_selector"]:
        if not stable_ref(lifecycle[field]) or not lifecycle[field].startswith("synthetic:"):
            error(errors, f"LIFECYCLE_SELECTOR_INVALID:{field}")
    if (
        not exact_keys(lifecycle["initialize_expected_return"], ["initialized"])
        or lifecycle["initialize_expected_return"]["initialized"] is not False
        or not exact_keys(lifecycle["shutdown_expected_return"], ["shutdown"])
        or lifecycle["shutdown_expected_return"]["shutdown"] is not True
    ):
        error(errors, "LIFECYCLE_RETURN_INVALID")
    if (
        not valid_sha256(lifecycle["initialize_argument_bytes_sha256"])
        or lifecycle["initialize_argument_bytes_sha256"] != sha256_text(sections["initialize"]["ref"])
    ):
        error(errors, "INITIALIZE_ARGUMENT_FINGERPRINT_INVALID")
    if (
        not valid_sha256(lifecycle["shutdown_argument_bytes_sha256"])
        or lifecycle["shutdown_argument_bytes_sha256"] != sha256_text(sections["shutdown"]["ref"])
    ):
        error(errors, "SHUTDOWN_ARGUMENT_FINGERPRINT_INVALID")


def validate_case(case: Any, index: int, errors: list[str]) -> str:
    if not exact_keys(case, CASE_FIELDS):
        error(errors, f"CASE_SCHEMA_INVALID:{index}")
        return "BLOCKED"
    if case["case_id"] != CASE_IDS[index]:
        error(errors, f"CASE_ID_INVALID:{index}")
    if case["environment"] != "SYNTHETIC_TEST":
        error(errors, f"CASE_ENVIRONMENT_INVALID:{index}")
    if case["runtime_usable"] is not False or case["actual_Host_smoke_execution_authorized"] is not False:
        error(errors, f"CASE_RUNTIME_AUTHORITY_INVALID:{index}")
    if type(case["Host_operation_count"]) is not int or case["Host_operation_count"] != 0:
        error(errors, f"CASE_HOST_OPERATION_COUNT_INVALID:{index}")
    validate_payload(case["inert_payload"], errors)
    validate_transient_manifest(case["transient_enabled_manifest"], errors)

    if index == 0:
        if case["owner_contract"] is not None or case["hermetic_dependency_inventory"] is not None or case["lifecycle_binding"] is not None:
            error(errors, "MISSING_OWNER_CASE_NOT_NULL")
        derived = "BLOCKED_MISSING_OWNER_ISSUED_ADAPTER_BINDING"
    else:
        owner_contract = case["owner_contract"]
        validate_owner_contract(owner_contract, errors)
        validate_inventory(case["hermetic_dependency_inventory"], errors)
        # A malformed owner contract is evidence unavailable, never a reason for
        # the offline reducer to raise before it can return a fail-closed result.
        # Resolve its sections only after the outer type has been established.
        sections = owner_contract.get("sections") if isinstance(owner_contract, dict) else None
        validate_lifecycle(case["lifecycle_binding"], sections, errors)
        derived = "SYNTHETIC_ADAPTER_BINDING_SHAPE_VALIDATED"
    if case["expected_result"] != derived:
        error(errors, f"CASE_EXPECTED_RESULT_INVALID:{index}")
    return derived


def validate_fixture(contract_path: Path, profile_path: Path, fixture_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    validate_contract_text(contract_path, errors)
    try:
        profile = load_yaml(profile_path)
    except (OSError, UnicodeError, yaml.YAMLError):
        profile = None
        error(errors, "PROFILE_UNAVAILABLE")
    if profile is not None:
        validate_profile(profile, errors)
    try:
        fixture = load_json(fixture_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        fixture = None
        error(errors, "FIXTURE_UNAVAILABLE")
    results: list[dict[str, str]] = []
    if fixture is not None:
        if not exact_keys(fixture, ROOT_FIELDS):
            error(errors, "FIXTURE_ROOT_SCHEMA_INVALID")
        elif fixture["schema_version"] != "agents-os.phase5d.m0d.host-smoke-adapter-binding-fixture.v0.1-r1":
            error(errors, "FIXTURE_SCHEMA_VERSION_INVALID")
        elif fixture["contract_path"] != str(CONTRACT_PATH.relative_to(ROOT)) or fixture["profile_path"] != str(PROFILE_PATH.relative_to(ROOT)):
            error(errors, "FIXTURE_PATH_BINDING_INVALID")
        elif fixture["immutable_anchor"] != ANCHOR:
            error(errors, "FIXTURE_IMMUTABLE_ANCHOR_INVALID")
        elif not isinstance(fixture["cases"], list) or len(fixture["cases"]) != 2:
            error(errors, "FIXTURE_CASE_COUNT_INVALID")
        else:
            for index, case in enumerate(fixture["cases"]):
                before = len(errors)
                derived = validate_case(case, index, errors)
                results.append({
                    "case_id": str(case.get("case_id", "UNKNOWN")) if isinstance(case, dict) else "UNKNOWN",
                    "derived_result": derived if len(errors) == before else "BLOCKED",
                })
    return {
        "result": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "case_results": results,
        "runtime_usable": False,
        "actual_Host_smoke_execution_authorized": False,
        "Host_operation_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }


def run_self_test() -> dict[str, Any]:
    baseline = load_json(FIXTURE_PATH)
    mutations: list[tuple[str, Any]] = []
    item = copy.deepcopy(baseline); item["extra"] = True; mutations.append(("unknown_root_field", item))
    item = copy.deepcopy(baseline); item["cases"][0]["owner_contract"] = {}; mutations.append(("missing_case_owner_injected", item))
    item = copy.deepcopy(baseline); item["cases"][1]["runtime_usable"] = True; mutations.append(("runtime_true", item))
    item = copy.deepcopy(baseline); item["cases"][1]["actual_Host_smoke_execution_authorized"] = True; mutations.append(("actual_authority_true", item))
    item = copy.deepcopy(baseline); item["cases"][1]["Host_operation_count"] = 1; mutations.append(("nonzero_host_operation", item))
    item = copy.deepcopy(baseline); del item["cases"][1]["owner_contract"]["sections"]["shutdown"]; mutations.append(("missing_shutdown_section", item))
    item = copy.deepcopy(baseline); item["cases"][1]["owner_contract"]["sections"]["initialize"]["sha256"] = "0" * 64; mutations.append(("forged_initialize_hash", item))
    item = copy.deepcopy(baseline); item["cases"][1]["hermetic_dependency_inventory"]["complete_for_actual_Host"] = True; mutations.append(("inventory_claimed_complete", item))
    item = copy.deepcopy(baseline); item["cases"][1]["transient_enabled_manifest"]["materialized"] = True; mutations.append(("manifest_materialized", item))
    item = copy.deepcopy(baseline); item["cases"][1]["transient_enabled_manifest"]["materialized"] = 0; mutations.append(("manifest_materialized_integer_zero", item))
    item = copy.deepcopy(baseline); item["cases"][1]["transient_enabled_manifest"]["materialized"] = 0.0; mutations.append(("manifest_materialized_float_zero", item))
    item = copy.deepcopy(baseline); item["cases"][1]["transient_enabled_manifest"]["byte_count"] = 413.0; mutations.append(("manifest_byte_count_float", item))
    item = copy.deepcopy(baseline); item["cases"][1]["inert_payload"]["processToolCall_authorized"] = True; mutations.append(("process_tool_call_authorized", item))
    item = copy.deepcopy(baseline); item["cases"][1]["owner_contract"] = []; mutations.append(("malformed_owner_contract", item))
    item = copy.deepcopy(baseline); item["cases"][1]["lifecycle_binding"]["initialize_expected_return"] = {"initialized": 0}; mutations.append(("initialize_return_integer_zero", item))
    item = copy.deepcopy(baseline); item["cases"][1]["lifecycle_binding"]["shutdown_expected_return"] = {"shutdown": 1}; mutations.append(("shutdown_return_integer_one", item))
    item = copy.deepcopy(baseline); item["cases"][1] = None; mutations.append(("null_case", item))
    item = copy.deepcopy(baseline); item["cases"][1] = []; mutations.append(("list_case", item))
    item = copy.deepcopy(baseline); item["cases"][1] = "forged"; mutations.append(("string_case", item))
    item = copy.deepcopy(baseline); item["cases"][1] = 1; mutations.append(("integer_case", item))

    rejected: list[str] = []
    for name, mutation in mutations:
        temp = FIXTURE_PATH.with_name(f".{FIXTURE_PATH.name}.{name}.tmp")
        try:
            temp.write_text(json.dumps(mutation, ensure_ascii=False), encoding="utf-8")
            outcome = validate_fixture(CONTRACT_PATH, PROFILE_PATH, temp)
            if outcome["result"] == "BLOCKED":
                rejected.append(name)
        finally:
            temp.unlink(missing_ok=True)
    duplicate_json = FIXTURE_PATH.with_name(f".{FIXTURE_PATH.name}.duplicate-json.tmp")
    duplicate_yaml = PROFILE_PATH.with_name(f".{PROFILE_PATH.name}.duplicate-yaml.tmp")
    nonstring_yaml = PROFILE_PATH.with_name(f".{PROFILE_PATH.name}.nonstring-key.tmp")
    profile_bool = PROFILE_PATH.with_name(f".{PROFILE_PATH.name}.host-operation-bool.tmp")
    profile_float = PROFILE_PATH.with_name(f".{PROFILE_PATH.name}.host-operation-float.tmp")
    try:
        duplicate_json.write_text(
            FIXTURE_PATH.read_text(encoding="utf-8").replace(
                '"schema_version": ', '"schema_version": "forged", "schema_version": ', 1
            ),
            encoding="utf-8",
        )
        if validate_fixture(CONTRACT_PATH, PROFILE_PATH, duplicate_json)["result"] == "BLOCKED":
            rejected.append("duplicate_json_key")
        duplicate_yaml.write_text(PROFILE_PATH.read_text(encoding="utf-8") + "\nprofile_id: forged\n", encoding="utf-8")
        try:
            load_yaml(duplicate_yaml)
        except yaml.YAMLError:
            rejected.append("duplicate_yaml_key")
        nonstring_yaml.write_text("1: invalid\n" + PROFILE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            load_yaml(nonstring_yaml)
        except yaml.YAMLError:
            rejected.append("nonstring_yaml_key")
        profile_mutation = load_yaml(PROFILE_PATH)
        profile_mutation["Host_operation_count"] = False
        profile_bool.write_text(yaml.safe_dump(profile_mutation, sort_keys=False), encoding="utf-8")
        if validate_fixture(CONTRACT_PATH, profile_bool, FIXTURE_PATH)["result"] == "BLOCKED":
            rejected.append("profile_host_operation_boolean")
        profile_mutation = load_yaml(PROFILE_PATH)
        profile_mutation["Host_operation_count"] = 0.0
        profile_float.write_text(yaml.safe_dump(profile_mutation, sort_keys=False), encoding="utf-8")
        if validate_fixture(CONTRACT_PATH, profile_float, FIXTURE_PATH)["result"] == "BLOCKED":
            rejected.append("profile_host_operation_float")
    finally:
        duplicate_json.unlink(missing_ok=True)
        duplicate_yaml.unlink(missing_ok=True)
        nonstring_yaml.unlink(missing_ok=True)
        profile_bool.unlink(missing_ok=True)
        profile_float.unlink(missing_ok=True)
    negative_case_count = len(mutations) + 5
    return {
        "result": "PASS" if len(rejected) == negative_case_count else "BLOCKED",
        "negative_cases": negative_case_count,
        "rejected_cases": len(rejected),
        "rejected_case_ids": rejected,
        "runtime_usable": False,
        "actual_Host_smoke_execution_authorized": False,
        "Host_operation_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--profile", type=Path, default=PROFILE_PATH)
    parser.add_argument("--fixture", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    output = run_self_test() if args.self_test else validate_fixture(args.contract, args.profile, args.fixture)
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if output["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
