#!/usr/bin/env python3
"""Closed-schema offline validator for the Phase 5D M0-D Plan R2 witness.

This validator intentionally has immutable R2 constants in code.  It is not a
Host harness and never reads VCPToolBox, loads a plugin, or performs an effect.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

import yaml


PLAN_PATH = Path(
    "control-plane/registry/drafts/"
    "2026-07-23-agents-os-phase-5d-m0d-quarantined-host-smoke-integration-plan-v0.1-r2-amendment.md"
)
PROFILE_PATH = Path(
    "control-plane/registry/drafts/"
    "2026-07-23-agents-os-phase-5d-m0d-quarantined-host-smoke-immutable-binding-profile-v0.1-r2.yaml"
)
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
PLAN_HEADER = re.compile(r"\A#[^\n]+\n\n```yaml\n(.*?)\n```\n", re.DOTALL)

EXPECTED_PLAN_SHA256 = "e3b70cc2638bca9624d2593e3105b69aeb1b033226941032f46c9bf61d1d3e0b"
EXPECTED_PROFILE_SHA256 = "3dfadf64e8e717d195ed64361bcf4f9af6d770eb835455e92d017510468b9349"
EXPECTED_PROFILE_SCHEMA = "agents-os.m0d-quarantined-host-smoke-immutable-binding-profile.v0.1-r2"
EXPECTED_PROFILE_ID = "PHASE_5D_M0D_QUARANTINED_HOST_SMOKE_IMMUTABLE_BINDING_PROFILE_V0_1_R2"
EXPECTED_PROFILE_STATUS = "fixed_for_fresh_full_atomic_independent_review"


class DuplicateKeyError(ValueError):
    """Raised when a JSON or YAML mapping repeats a key."""


class UniqueKeySafeLoader(yaml.SafeLoader):
    """SafeLoader variant that rejects duplicate YAML mapping keys."""


def construct_unique_mapping(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if type(key) is not str:
            raise DuplicateKeyError("YAML mapping key must be a string")
        if key in mapping:
            raise DuplicateKeyError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping
)


def no_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def strict_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicate_pairs)


def strict_yaml_text(text: str) -> Any:
    return yaml.load(text, Loader=UniqueKeySafeLoader)


def strict_yaml(path: Path) -> Any:
    return strict_yaml_text(path.read_text(encoding="utf-8"))


def valid_string(value: Any) -> bool:
    return type(value) is str and bool(value) and unicodedata.normalize("NFC", value) == value


def exact_keys(value: Any, keys: set[str], where: str, errors: list[str]) -> None:
    if type(value) is not dict:
        errors.append(f"{where}: expected object")
        return
    actual = set(value)
    if actual != keys:
        errors.append(
            f"{where}: fields mismatch missing={sorted(keys - actual)} extra={sorted(actual - keys)}"
        )


def exact_lower_hex(value: Any, width: int, where: str, errors: list[str]) -> None:
    pattern = HEX40 if width == 40 else HEX64
    if type(value) is not str or not pattern.fullmatch(value):
        errors.append(f"{where}: expected lowercase {width}-hex")


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


EXPECTED_PLAN_HEADER: dict[str, Any] = {
    "schema_version": "agents-os.phase5d.m0d.plan.v0.1-r2",
    "plan_id": "PHASE_5D_M0D_QUARANTINED_HOST_SMOKE_INTEGRATION_PLAN_V0_1_R2",
    "date": "2026-07-23",
    "status": "FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW",
    "acceptance_unit": "PHASE_5D_M0D_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE",
    "partial_acceptance": "forbidden",
    "precedence": ["R2_explicit_replacements", "R1_all_other_clauses"],
    "current_boundary": {
        "current_plan_authoring_only": True,
        "Host_worktree_read_or_write": "forbidden",
        "archive_delivery_or_installation": "forbidden",
        "plugin_enablement_or_Host_loading": "forbidden",
        "processToolCall_or_native_addon_load": "forbidden",
        "native_NAPI_invocation": "forbidden",
        "runtime_database_provider_private_Memory_sensing_or_effect": "forbidden",
        "implementation_authorized": False,
        "runtime_usable": False,
        "terminal_outcome": "NOT_EXECUTED",
    },
    "future_smoke_interface": {
        "future_lifecycle_methods_only": ["initialize", "shutdown"],
        "future_initialize_result": {"initialized": False},
        "future_shutdown_result": {"shutdown": True},
        "Host_lifecycle_argument_contract": "future_hash_bound_Host_contract_required",
        "future_Host_discovery_or_lifecycle": "separately_Jenn_authorized_only",
    },
}

EXPECTED_SOURCE_ANCHOR: dict[str, Any] = {
    "repository": "JENN2046/Agents-OS",
    "baseline_main_commit": "bc5df3903bd1f591d085538f3480be37c11c0ddc",
    "source_payload_commit": "0305e918f938d6b2092b38d6af57a258ae814096",
    "source_root": "extensions/agents-os-resident",
    "package_manifest_sha256": "b30b455cee6313b3c4c6fa0883865ec4ea45e3854d7453cbc651e77a2e83df23",
    "blocked_plugin_manifest_sha256": "25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0",
    "inert_commonjs_entrypoint_sha256": "51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec",
    "VCPToolBox_sealed_commit": "555b3b538f6eb736e530c2912de678c5941f9985",
    "VCPToolBox_sealed_tree": "fd82d403e79f36f749eb7f555b4736eae3eacdff",
    "sealed_host_commitments": [
        {"path": "AGENTS.md", "blob_oid": "28f22b4de495a63f14ede8fe72698278c877cb8d", "sha256": "24b2a4c3e45a98107a726c8dfd80b577846052d49068bb1c13479f872bf0374b"},
        {"path": "Plugin/AGENTS.md", "blob_oid": "c2d23c041033b1f7d46b9dc3bdb2ba738566c872", "sha256": "b060ad148827faa37877deb8b170399a0f00f46bc194797949005c9bb62572d4"},
        {"path": "docs/PLUGIN_ECOSYSTEM.md", "blob_oid": "81dc779453ccf2fb56c1f57d1ecde8ff3ffda506", "sha256": "f806b90c4f7d46bd2113f8b5af9f773adce49b454d615e7b6aa8445663490a65"},
        {"path": "rust-vexus-lite/AGENTS.md", "blob_oid": "0fad4dba9bcbaa2452a362910b01e6275e5c352e", "sha256": "e5e68ad817c4fc7da657ce0d9c131db666eff97888b772ac31b9661210c93494"},
        {"path": "rust-vexus-lite/Cargo.toml", "blob_oid": "3682f96f45c095f85e0f3c93bc2d6c1f21c98dde", "sha256": "01f6f29f824418c58dc1c0a5243df514bd6b2bd5cd6a68de850c13e465e6eea9"},
        {"path": "rust-vexus-lite/package.json", "blob_oid": "232a95ef206e6ffab0cdff959826faaa10f6fedb", "sha256": "c996185f59cc84208077f854077f2f5451368ea9cd05c775ba0b06028fed7f7c"},
        {"path": "Plugin.js", "blob_oid": "5fd77cea37c30ef432f23d9627d05aba862b9744", "sha256": "be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2"},
    ],
    "anchor_sha256": "b85ae99e47bc80bfbbcf634d403628a3ad972ec06a459e0e9cb710b679692352",
}

EXPECTED_R1_LINEAGE = {
    "r1_plan_sha256": "60cb27e9fafd2881dcbad4ccea5fd45ef2da8ceb8cb3717738d272d02cb77e27",
    "r1_profile_sha256": "de9feef1e71d4c7ef27b58d4759c7190fb7b4c9b7bbf9b636cdad08a8ff00e82",
    "r1_manifest_sha256": "6ea9be0cc7873dfed3b0038c853e18fcb58be97f08553411226dd7ef65b2f568",
    "r1_independent_review_sha256": "4172f1895e4b0bd829ec48775ce92d0785cbc6068e32439bd4aac6226112b265",
    "r1_finding_disposition_sha256": "0179e6dffac50e83312c645822645e4c19e9648645a13d1b325dc97714047f5a",
}

EXPECTED_PHASE5C_EVIDENCE = {
    "freeze_decision_sha256": "160f2e0d6e9a4a4fbb868bfb378b030b33455d78a943daea8aadb554a049e2ce",
    "implementation_closeout_sha256": "edf82f3d87ed1c7480c82ff60e355af88b8fb6ddd31953f20bca959aee28c0b9",
    "postmerge_durability_sha256": "55dbfd4000a5f709293bbdd0403c7623479253c180e0e8927462a1a17dad72fe",
}

EXPECTED_CURRENT_BOUNDARY = {
    "current_plan_authoring_only": True,
    "Host_worktree_read_or_write": "forbidden",
    "archive_delivery_or_installation": "forbidden",
    "plugin_enablement_or_Host_loading": "forbidden",
    "processToolCall_or_native_addon_load": "forbidden",
    "native_NAPI_invocation": "forbidden",
    "runtime_database_provider_private_Memory_sensing_or_effect": "forbidden",
    "implementation_authorized": False,
    "runtime_usable": False,
    "terminal_outcome": "NOT_EXECUTED",
    "future_lifecycle_methods_only": ["initialize", "shutdown"],
    "future_Host_lifecycle_argument_contract": "future_hash_bound_Host_contract_required",
    "future_Host_discovery_or_lifecycle": "separately_Jenn_authorized_only",
}

EXPECTED_OFFLINE_WITNESS_CONTRACT = {
    "favorable_result": "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY",
    "favorable_result_is_not_execution": True,
    "environment": "SYNTHETIC_PLAN_ONLY",
    "real_occurrence_count": 0,
    "source_profile_and_plan_mutation": "BLOCKED",
    "current_Host_plugin_native_or_runtime_claim": "BLOCKED",
    "duplicate_YAML_key_or_noncanonical_identity": "BLOCKED",
}

EXPECTED_AUTHORIZATION = {
    "R2_plan_authoring_authorized": True,
    "implementation_or_source_modification_authorized": False,
    "VCPToolBox_change_or_start_authorized": False,
    "archive_delivery_or_installation_authorized": False,
    "plugin_enablement_or_Host_loading_authorized": False,
    "processToolCall_or_native_addon_loading_authorized": False,
    "runtime_activation_authorized": False,
    "database_provider_private_Memory_sensing_or_effect_authorized": False,
    "Git_delivery_authorized": False,
    "separate_Jenn_plan_freeze_required": True,
}


def plan_header_sha256() -> str:
    return sha256_bytes(canonical_bytes(EXPECTED_PLAN_HEADER))


def load_plan(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except Exception as exc:
        return None, [f"plan read failed: {exc}"]
    if sha256_bytes(raw) != EXPECTED_PLAN_SHA256:
        errors.append("plan: immutable exact byte hash mismatch")
    match = PLAN_HEADER.match(text)
    if match is None:
        return None, errors + ["plan: missing canonical leading YAML header"]
    try:
        header = strict_yaml_text(match.group(1))
    except Exception as exc:
        return None, errors + [f"plan parse failed: {exc}"]
    exact_keys(header, set(EXPECTED_PLAN_HEADER), "plan.header", errors)
    if type(header) is not dict:
        return None, errors or ["plan.header: expected object"]
    if header != EXPECTED_PLAN_HEADER:
        errors.append("plan.header: exact current-boundary semantic projection changed")
    check_text_tree(header, "plan.header", errors)
    return header, errors


def load_profile(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    try:
        raw = path.read_bytes()
        profile = strict_yaml_text(raw.decode("utf-8"))
    except Exception as exc:
        return None, [f"profile parse failed: {exc}"]
    if sha256_bytes(raw) != EXPECTED_PROFILE_SHA256:
        errors.append("profile: immutable exact byte hash mismatch")
    expected_root = {
        "schema_version", "profile_id", "date", "status", "runtime_usable", "terminal_outcome",
        "plan_binding", "r1_immutable_lineage", "phase5c_immutable_evidence",
        "exact_source_Host_extension_anchor", "current_plan_boundary_projection",
        "offline_witness_contract", "authorization",
    }
    exact_keys(profile, expected_root, "profile", errors)
    if type(profile) is not dict:
        return None, errors or ["profile: expected object"]
    if profile.get("schema_version") != EXPECTED_PROFILE_SCHEMA:
        errors.append("profile.schema_version: exact R2 value required")
    if profile.get("profile_id") != EXPECTED_PROFILE_ID:
        errors.append("profile.profile_id: exact R2 value required")
    if profile.get("status") != EXPECTED_PROFILE_STATUS:
        errors.append("profile.status: exact R2 value required")
    if profile.get("date") != "2026-07-23":
        errors.append("profile.date: exact R2 value required")
    if type(profile.get("runtime_usable")) is not bool or profile.get("runtime_usable") is not False:
        errors.append("profile.runtime_usable: must be JSON false")
    if profile.get("terminal_outcome") != "NOT_EXECUTED":
        errors.append("profile.terminal_outcome: must be NOT_EXECUTED")
    plan_binding = profile.get("plan_binding")
    expected_plan_binding = {
        "plan_path": str(PLAN_PATH),
        "plan_sha256": EXPECTED_PLAN_SHA256,
        "required_plan_schema_version": EXPECTED_PLAN_HEADER["schema_version"],
        "required_plan_id": EXPECTED_PLAN_HEADER["plan_id"],
        "required_plan_status": EXPECTED_PLAN_HEADER["status"],
    }
    exact_keys(plan_binding, set(expected_plan_binding), "profile.plan_binding", errors)
    if plan_binding != expected_plan_binding:
        errors.append("profile.plan_binding: immutable Plan binding changed")
    exact_keys(profile.get("r1_immutable_lineage"), set(EXPECTED_R1_LINEAGE), "profile.r1_immutable_lineage", errors)
    if profile.get("r1_immutable_lineage") != EXPECTED_R1_LINEAGE:
        errors.append("profile.r1_immutable_lineage: immutable R1 binding changed")
    exact_keys(profile.get("phase5c_immutable_evidence"), set(EXPECTED_PHASE5C_EVIDENCE), "profile.phase5c_immutable_evidence", errors)
    if profile.get("phase5c_immutable_evidence") != EXPECTED_PHASE5C_EVIDENCE:
        errors.append("profile.phase5c_immutable_evidence: immutable Phase 5C binding changed")
    source_anchor = profile.get("exact_source_Host_extension_anchor")
    expected_anchor_keys = set(EXPECTED_SOURCE_ANCHOR)
    exact_keys(source_anchor, expected_anchor_keys, "profile.exact_source_Host_extension_anchor", errors)
    if source_anchor != EXPECTED_SOURCE_ANCHOR:
        errors.append("profile.exact_source_Host_extension_anchor: immutable sealed source/Host/extension binding changed")
    if type(source_anchor) is dict:
        preimage = dict(source_anchor)
        supplied_anchor = preimage.pop("anchor_sha256", None)
        recomputed = sha256_bytes(canonical_bytes(preimage))
        if supplied_anchor != recomputed:
            errors.append("profile.exact_source_Host_extension_anchor.anchor_sha256: mismatch")
        rows = source_anchor.get("sealed_host_commitments")
        if type(rows) is not list or len(rows) != 7:
            errors.append("profile.exact_source_Host_extension_anchor.sealed_host_commitments: exact seven rows required")
        else:
            for index, row in enumerate(rows):
                exact_keys(row, {"path", "blob_oid", "sha256"}, f"profile.sealed_host_commitments[{index}]", errors)
                if type(row) is dict:
                    if not valid_string(row.get("path")) or row["path"].startswith("/") or ".." in row["path"].split("/") or "\\" in row["path"]:
                        errors.append(f"profile.sealed_host_commitments[{index}].path: unsafe")
                    exact_lower_hex(row.get("blob_oid"), 40, f"profile.sealed_host_commitments[{index}].blob_oid", errors)
                    exact_lower_hex(row.get("sha256"), 64, f"profile.sealed_host_commitments[{index}].sha256", errors)
    exact_keys(profile.get("current_plan_boundary_projection"), set(EXPECTED_CURRENT_BOUNDARY), "profile.current_plan_boundary_projection", errors)
    if profile.get("current_plan_boundary_projection") != EXPECTED_CURRENT_BOUNDARY:
        errors.append("profile.current_plan_boundary_projection: exact no-execution Plan boundary changed")
    exact_keys(profile.get("offline_witness_contract"), set(EXPECTED_OFFLINE_WITNESS_CONTRACT), "profile.offline_witness_contract", errors)
    if profile.get("offline_witness_contract") != EXPECTED_OFFLINE_WITNESS_CONTRACT:
        errors.append("profile.offline_witness_contract: favorable outcome semantics changed")
    exact_keys(profile.get("authorization"), set(EXPECTED_AUTHORIZATION), "profile.authorization", errors)
    if profile.get("authorization") != EXPECTED_AUTHORIZATION:
        errors.append("profile.authorization: plan-only authorization changed")
    check_text_tree(profile, "profile", errors)
    return profile, errors


def expected_witness(profile: dict[str, Any]) -> dict[str, Any]:
    anchor = profile["exact_source_Host_extension_anchor"]
    return {
        "schema_version": "agents-os.m0d.synthetic-plan-r2-witness.v0.1",
        "environment": "SYNTHETIC_PLAN_ONLY",
        "plan_binding": {
            "plan_id": EXPECTED_PLAN_HEADER["plan_id"],
            "plan_sha256": EXPECTED_PLAN_SHA256,
            "plan_header_sha256": plan_header_sha256(),
        },
        "profile_binding": {
            "profile_id": EXPECTED_PROFILE_ID,
            "profile_sha256": EXPECTED_PROFILE_SHA256,
            "profile_schema_version": EXPECTED_PROFILE_SCHEMA,
        },
        "source_anchor": {
            "anchor_sha256": anchor["anchor_sha256"],
            "source_payload_commit": anchor["source_payload_commit"],
            "VCPToolBox_sealed_commit": anchor["VCPToolBox_sealed_commit"],
            "VCPToolBox_sealed_tree": anchor["VCPToolBox_sealed_tree"],
            "sealed_host_commitments_sha256": sha256_bytes(canonical_bytes(anchor["sealed_host_commitments"])),
        },
        "current_boundary": EXPECTED_CURRENT_BOUNDARY,
        "authorization": EXPECTED_AUTHORIZATION,
        "claimed_decision": EXPECTED_OFFLINE_WITNESS_CONTRACT["favorable_result"],
        "runtime_usable": False,
        "real_occurrence_count": 0,
    }


def validate_witness(value: Any, profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    expected = expected_witness(profile)
    exact_keys(value, set(expected), "witness", errors)
    if type(value) is not dict:
        return errors or ["witness: expected object"]
    check_text_tree(value, "witness", errors)
    if type(value.get("runtime_usable")) is not bool or value.get("runtime_usable") is not False:
        errors.append("witness.runtime_usable: must be JSON false")
    if type(value.get("real_occurrence_count")) is not int or value.get("real_occurrence_count") != 0:
        errors.append("witness.real_occurrence_count: must be exact integer zero")
    for key in expected:
        if value.get(key) != expected[key]:
            errors.append(f"witness.{key}: does not match immutable R2 Plan/profile derivation")
    return errors


def run_fixture(fixture_path: Path, plan_path: Path = PLAN_PATH, profile_path: Path = PROFILE_PATH) -> tuple[list[str], str]:
    plan, plan_errors = load_plan(plan_path)
    profile, profile_errors = load_profile(profile_path)
    errors = plan_errors + profile_errors
    if plan is None or profile is None:
        return errors or ["immutable input unavailable"], "BLOCKED"
    plan_current = plan["current_boundary"]
    if plan_current != {
        key: EXPECTED_CURRENT_BOUNDARY[key]
        for key in plan_current
    }:
        errors.append("plan/profile current-boundary cross-binding mismatch")
    try:
        value = strict_json(fixture_path)
    except Exception as exc:
        return errors + [f"fixture parse failed: {exc}"], "BLOCKED"
    errors += validate_witness(value, profile)
    return errors, "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY" if not errors else "BLOCKED"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_yaml(path: Path, value: Any) -> None:
    path.write_text(yaml.safe_dump(value, allow_unicode=False, sort_keys=False), encoding="utf-8")


def self_test(fixture: Path) -> list[str]:
    initial_errors, initial_result = run_fixture(fixture)
    failures: list[str] = []
    if initial_errors or initial_result != "QUARANTINED_HOST_SMOKE_PREFLIGHT_READY":
        failures.append("positive fixture did not pass")
        return failures + initial_errors
    with tempfile.TemporaryDirectory(prefix="phase5d-r2-self-test-") as temporary:
        root = Path(temporary)
        plan_copy = root / "plan.md"
        profile_copy = root / "profile.yaml"
        fixture_copy = root / "fixture.json"
        shutil.copyfile(PLAN_PATH, plan_copy)
        shutil.copyfile(PROFILE_PATH, profile_copy)
        shutil.copyfile(fixture, fixture_copy)

        def require_rejected(name: str, mutate: Any) -> None:
            shutil.copyfile(PLAN_PATH, plan_copy)
            shutil.copyfile(PROFILE_PATH, profile_copy)
            shutil.copyfile(fixture, fixture_copy)
            mutate(plan_copy, profile_copy, fixture_copy)
            errors, result = run_fixture(fixture_copy, plan_copy, profile_copy)
            if not errors or result != "BLOCKED":
                failures.append(f"mutation accepted: {name}")

        def mutate_profile(path: Path, edit: Any) -> None:
            value = strict_yaml(path)
            edit(value)
            write_yaml(path, value)

        def mutate_fixture(path: Path, edit: Any) -> None:
            value = strict_json(path)
            edit(value)
            write_json(path, value)

        require_rejected("source_payload_commit", lambda p, q, f: mutate_profile(q, lambda v: v["exact_source_Host_extension_anchor"].__setitem__("source_payload_commit", "0" * 40)))
        require_rejected("sealed_Host_commit", lambda p, q, f: mutate_profile(q, lambda v: v["exact_source_Host_extension_anchor"].__setitem__("VCPToolBox_sealed_commit", "0" * 40)))
        require_rejected("extension_hash", lambda p, q, f: mutate_profile(q, lambda v: v["exact_source_Host_extension_anchor"].__setitem__("package_manifest_sha256", "0" * 64)))
        require_rejected("host_row", lambda p, q, f: mutate_profile(q, lambda v: v["exact_source_Host_extension_anchor"]["sealed_host_commitments"][0].__setitem__("sha256", "0" * 64)))
        require_rejected("absolute_source_root", lambda p, q, f: mutate_profile(q, lambda v: v["exact_source_Host_extension_anchor"].__setitem__("source_root", "/tmp/escape")))
        require_rejected("plan_current_Host_claim", lambda p, q, f: p.write_text(p.read_text(encoding="utf-8").replace("Host_worktree_read_or_write: forbidden", "Host_worktree_read_or_write: authorized"), encoding="utf-8"))
        require_rejected("plan_processToolCall_claim", lambda p, q, f: p.write_text(p.read_text(encoding="utf-8").replace("processToolCall_or_native_addon_load: forbidden", "processToolCall_or_native_addon_load: authorized"), encoding="utf-8"))
        require_rejected("profile_identity", lambda p, q, f: mutate_profile(q, lambda v: v.__setitem__("profile_id", "PHASE_5D_MUTATED")))
        require_rejected("duplicate_profile_key", lambda p, q, f: q.write_text(q.read_text(encoding="utf-8") + "\nprofile_id: PHASE_5D_DUPLICATE\n", encoding="utf-8"))
        require_rejected("fixture_runtime", lambda p, q, f: mutate_fixture(f, lambda v: v.__setitem__("runtime_usable", True)))
        require_rejected("fixture_source_anchor", lambda p, q, f: mutate_fixture(f, lambda v: v["source_anchor"].__setitem__("source_payload_commit", "0" * 40)))
        require_rejected("fixture_current_decision", lambda p, q, f: mutate_fixture(f, lambda v: v.__setitem__("claimed_decision", "HOST_EXECUTED")))
    try:
        strict_yaml_text("profile_id: one\nprofile_id: two\n")
        failures.append("duplicate YAML key accepted")
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
    print(json.dumps({"errors": errors, "result": result}, separators=(",", ":"), sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
