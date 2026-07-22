#!/usr/bin/env python3
"""Validate the Phase 5C M0-C Plan R3 structural-only synthetic witness.

The validator derives source, archive, return-byte, and temporary-root cleanup
facts from the sealed inputs and real synthetic filesystem observations.  It
does not install or enable a plugin, modify VCPToolBox, or access any runtime,
database, provider, private Memory, sensor, or effect boundary.
"""

from __future__ import annotations

import argparse
import base64
import copy
import json
from pathlib import Path
import re
import unicodedata
from typing import Any

import yaml

import phase5c_m0c_r3_structural_core as core


R2_ARCHIVE_PROFILE = core.ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r2.yaml"

TOP_KEYS = {
    "schema_version",
    "environment",
    "archive_profile_sha256",
    "source_inventory_profile_sha256",
    "source_commitment",
    "sealed_host_contract",
    "source_inventory",
    "archive_member_inventory",
    "manifest_evidence",
    "entrypoint",
    "native_napi_methods",
    "synthetic_archive",
    "output_request",
    "lifecycle_execution_proofs",
    "terminal_outcome",
    "root_fingerprint",
}
SOURCE_RECORD_KEYS = {"source_path", "kind", "byte_length", "sha256"}
ARCHIVE_MEMBER_KEYS = {"source_path", "archive_path", "kind", "byte_length", "sha256"}
SYNTHETIC_MEMBER_KEYS = set(core.MEMBER_MANIFEST_FIELDS) | {"content_b64"}
SYNTHETIC_ARCHIVE_KEYS = {"members", "member_manifest_sha256", "archive_bytes_b64", "archive_sha256", "archive_byte_length"}
SUCCESS_KEYS = {
    "events",
    "initial_owned_root_inventory",
    "before_cleanup_inventory",
    "post_cleanup_owned_root_exists",
    "post_cleanup_residue_relative_paths",
    "return",
}
FAILURE_KEYS = SUCCESS_KEYS
RESIDUE_PROBE_KEYS = {
    "probe_result",
    "observed_before_cleanup_residue_relative_paths",
    "post_cleanup_owned_root_exists",
    "post_cleanup_residue_relative_paths",
    "return",
}
WRONG_RETURN_PROBE_KEYS = {
    "probe_result",
    "expected_archive_sha256",
    "observed_returned_archive_sha256",
    "observed_returned_archive_byte_length",
    "observed_returned_archive_bytes_b64",
    "post_cleanup_owned_root_exists",
    "post_cleanup_residue_relative_paths",
    "return",
}


def strict_pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_strict(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_pairs)


def is_safe_int(value: object) -> bool:
    return type(value) is int and 0 <= value <= 9007199254740991


def is_sha256(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def is_oid(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def decode_b64(value: object, label: str, errors: list[str]) -> bytes | None:
    if type(value) is not str:
        errors.append(f"{label} must be base64 string")
        return None
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        errors.append(f"{label} invalid base64")
        return None


def exact_keys(value: object, expected: set[str], label: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{label} must be object")
        return False
    actual = set(value)
    if actual != expected:
        errors.append(f"{label} field inventory mismatch")
        return False
    return True


def safe_relative_path(value: object, label: str, errors: list[str]) -> bool:
    if type(value) is not str:
        errors.append(f"{label} must be string")
        return False
    if not value or unicodedata.normalize("NFC", value) != value:
        errors.append(f"{label} must be nonempty NFC path")
        return False
    if "\\" in value or value.startswith("/") or "\x00" in value:
        errors.append(f"{label} unsafe path form")
        return False
    if any(part in {"", ".", ".."} for part in value.split("/")):
        errors.append(f"{label} traversal or empty segment")
        return False
    return True


def source_record_schema(row: object, label: str, errors: list[str]) -> bool:
    if not exact_keys(row, SOURCE_RECORD_KEYS, label, errors):
        return False
    assert isinstance(row, dict)
    ok = safe_relative_path(row["source_path"], f"{label}.source_path", errors)
    if row["kind"] != "regular_file":
        errors.append(f"{label}.kind must be regular_file")
        ok = False
    if not is_safe_int(row["byte_length"]):
        errors.append(f"{label}.byte_length invalid")
        ok = False
    if not is_sha256(row["sha256"]):
        errors.append(f"{label}.sha256 invalid")
        ok = False
    return ok


def archive_member_schema(row: object, root_prefix: str, label: str, errors: list[str]) -> bool:
    if not exact_keys(row, ARCHIVE_MEMBER_KEYS, label, errors):
        return False
    assert isinstance(row, dict)
    ok = safe_relative_path(row["source_path"], f"{label}.source_path", errors)
    ok = safe_relative_path(row["archive_path"], f"{label}.archive_path", errors) and ok
    if type(row["archive_path"]) is str and not row["archive_path"].startswith(root_prefix):
        errors.append(f"{label}.archive_path outside archive root")
        ok = False
    if type(row["archive_path"]) is str and len(row["archive_path"].encode("utf-8")) > 100:
        errors.append(f"{label}.archive_path exceeds ustar limit")
        ok = False
    if row["kind"] != "regular_file":
        errors.append(f"{label}.kind must be regular_file")
        ok = False
    if not is_safe_int(row["byte_length"]):
        errors.append(f"{label}.byte_length invalid")
        ok = False
    if not is_sha256(row["sha256"]):
        errors.append(f"{label}.sha256 invalid")
        ok = False
    return ok


def synthetic_member_schema(row: object, root_prefix: str, label: str, errors: list[str]) -> bool:
    if not exact_keys(row, SYNTHETIC_MEMBER_KEYS, label, errors):
        return False
    assert isinstance(row, dict)
    ok = safe_relative_path(row["source_path"], f"{label}.source_path", errors)
    ok = safe_relative_path(row["archive_path"], f"{label}.archive_path", errors) and ok
    if type(row["archive_path"]) is str and row["archive_path"] != root_prefix + str(row["source_path"]):
        errors.append(f"{label}.archive_path does not derive from source path")
        ok = False
    if row["kind"] != "regular_file":
        errors.append(f"{label}.kind must be regular_file")
        ok = False
    for key in ("mode", "uid", "gid", "mtime", "byte_length"):
        if not is_safe_int(row[key]):
            errors.append(f"{label}.{key} invalid")
            ok = False
    if type(row["mode"]) is int and row["mode"] > 0o777:
        errors.append(f"{label}.mode outside POSIX permission range")
        ok = False
    for key in ("uname", "gname"):
        if type(row[key]) is not str or unicodedata.normalize("NFC", row[key]) != row[key]:
            errors.append(f"{label}.{key} invalid")
            ok = False
    content = decode_b64(row["content_b64"], f"{label}.content_b64", errors)
    if content is not None:
        if row["byte_length"] != len(content):
            errors.append(f"{label}.byte_length does not match content")
            ok = False
        if row["sha256"] != core.sha256_bytes(content):
            errors.append(f"{label}.sha256 does not match content")
            ok = False
    if not is_sha256(row["sha256"]):
        errors.append(f"{label}.sha256 invalid")
        ok = False
    return ok


def validate_profile(archive_profile: object, r2_profile: object, errors: list[str]) -> bool:
    if type(archive_profile) is not dict or type(r2_profile) is not dict:
        errors.append("archive profile malformed")
        return False
    expected_top = {
        "schema_version", "profile_id", "date", "owner", "agent_steward", "status", "runtime_usable", "inherits",
        "archive_encoding", "output_lifecycle", "sealed_host_contract", "entrypoint_contract", "manifest_contract",
        "synthetic_archive_exercise", "boundary",
    }
    if set(archive_profile) != expected_top:
        errors.append("archive profile field inventory mismatch")
        return False
    encoding = archive_profile["archive_encoding"]
    expected_encoding = {
        "format", "compression", "byte_stream", "checksum_algorithm", "checksum_preimage", "root_prefix",
        "explicit_directory_entries", "regular_files_only", "member_order", "path_separator",
        "reject_absolute_traversal_backslash_duplicate_or_non_NFC_paths", "member_manifest", "header",
        "end_of_archive_zero_blocks",
    }
    if type(encoding) is not dict or set(encoding) != expected_encoding:
        errors.append("archive encoding malformed")
        return False
    manifest = encoding.get("member_manifest")
    expected_member_manifest = {"algorithm", "preimage", "encoding", "object_key_order", "separators", "row_field_inventory"}
    if type(manifest) is not dict or set(manifest) != expected_member_manifest:
        errors.append("member manifest profile malformed")
        return False
    if manifest.get("row_field_inventory") != list(core.MEMBER_MANIFEST_FIELDS):
        errors.append("member manifest field inventory mismatch")
    if manifest.get("algorithm") != "SHA-256" or manifest.get("preimage") != "canonical_JSON_array_of_exact_member_projection_rows":
        errors.append("member manifest algorithm mismatch")
    if manifest.get("encoding") != "UTF-8" or manifest.get("object_key_order") != "LEXICOGRAPHIC_SORTED" or manifest.get("separators") != "NO_INSIGNIFICANT_WHITESPACE":
        errors.append("member manifest canonical JSON contract mismatch")
    header = encoding.get("header")
    expected_header = {
        "mode_octal", "uid", "gid", "uname", "gname", "mtime_unix_seconds", "pax_headers", "hardlinks_symlinks_devices_named_pipes",
    }
    if type(header) is not dict or set(header) != expected_header:
        errors.append("archive header field inventory mismatch")
    else:
        if (
            type(header["mode_octal"]) is not str
            or type(header["uid"]) is not int
            or type(header["gid"]) is not int
            or type(header["uname"]) is not str
            or type(header["gname"]) is not str
            or type(header["mtime_unix_seconds"]) is not int
            or header["mode_octal"] != "0644"
            or header["uid"] != 0
            or header["gid"] != 0
            or header["uname"] != ""
            or header["gname"] != ""
            or header["mtime_unix_seconds"] != 0
        ):
            errors.append("archive header normalization mismatch")
    if encoding.get("format") != "POSIX_USTAR" or encoding.get("compression") != "NONE" or encoding.get("root_prefix") != "agents-os-resident/":
        errors.append("archive encoding contract mismatch")
    lifecycle = archive_profile["output_lifecycle"]
    required_lifecycle_keys = {
        "caller_supplied_output_path", "staging_root", "archive_location_before_delivery", "delivery_mode",
        "serialized_success_return_fields", "serialized_failure_return_fields", "success_events", "failure_events",
        "actual_observation_contract", "required_negative_actual_probes",
    }
    if type(lifecycle) is not dict or set(lifecycle) != required_lifecycle_keys:
        errors.append("output lifecycle field inventory mismatch")
    else:
        if lifecycle["caller_supplied_output_path"] != "forbidden" or lifecycle["staging_root"] != "newly_created_owned_synthetic_temporary_directory" or lifecycle["delivery_mode"] != "RETURN_IN_MEMORY_BYTES_ONLY":
            errors.append("output lifecycle contract mismatch")
        if lifecycle["serialized_success_return_fields"] != ["archive_sha256", "archive_byte_length", "archive_bytes_in_memory_b64"]:
            errors.append("success return field inventory mismatch")
        if lifecycle["serialized_failure_return_fields"] != ["stable_error_code"]:
            errors.append("failure return field inventory mismatch")
        if lifecycle["actual_observation_contract"] != {
            "initial_owned_root_inventory": [],
            "success_before_cleanup_inventory": ["archive.tar"],
            "failure_before_cleanup_inventory": [],
            "post_cleanup_owned_root_exists": False,
            "post_cleanup_residue_relative_paths": [],
        }:
            errors.append("actual filesystem observation contract mismatch")
        if lifecycle["required_negative_actual_probes"] != ["CLEANUP_RESIDUE_DETECTED", "RETURN_BYTES_MISMATCH_DETECTED"]:
            errors.append("actual negative probe inventory mismatch")
    for key in ("sealed_host_contract", "entrypoint_contract", "manifest_contract"):
        if archive_profile[key] != r2_profile.get(key):
            errors.append(f"{key} differs from immutable R2 contract")
    boundary = archive_profile["boundary"]
    if type(boundary) is not dict or any(boundary.get(key) is not False for key in (
        "synthetic_witness_runtime_usable", "implementation_authorized", "VCPToolBox_change_or_start_authorized",
        "plugin_enablement_or_native_host_loading_authorized", "database_private_Memory_provider_sensing_or_effect_authorized",
        "release_deploy_publish_authorized",
    )) or boundary.get("owned_temp_root_synthetic_test_only") is not True:
        errors.append("R3 boundary contract mismatch")
    return not errors


def validate_source_profile_and_files(profile: object, errors: list[str]) -> bool:
    if type(profile) is not dict or type(profile.get("records")) is not list:
        errors.append("source inventory profile malformed")
        return False
    records = profile["records"]
    ok = True
    if profile.get("record_count") != len(records):
        errors.append("source inventory profile record count mismatch")
        ok = False
    paths: list[str] = []
    for index, row in enumerate(records):
        ok = source_record_schema(row, f"source inventory profile record {index}", errors) and ok
        if type(row) is dict and type(row.get("source_path")) is str:
            paths.append(row["source_path"])
            source_root = core.ROOT / str(profile.get("source_root", ""))
            path = source_root / row["source_path"]
            if not path.is_file():
                errors.append(f"sealed source missing: {row['source_path']}")
                ok = False
            elif path.stat().st_size != row["byte_length"] or core.sha256_file(path) != row["sha256"]:
                errors.append(f"sealed source bytes mismatch: {row['source_path']}")
                ok = False
    if len(paths) != len(set(paths)):
        errors.append("source inventory profile duplicate source paths")
        ok = False
    if profile.get("records_canonical_sha256") != core.sha256_bytes(core.canonical(records)):
        errors.append("source inventory profile canonical digest mismatch")
        ok = False
    return ok


def validate_source_commitment(doc: dict[str, Any], source_profile: dict[str, Any], errors: list[str]) -> None:
    expected = core.source_commitment(source_profile)
    if exact_keys(doc["source_commitment"], set(expected), "source commitment", errors) and doc["source_commitment"] != expected:
        errors.append("source commitment differs from sealed source profile")


def validate_host_contract(doc: dict[str, Any], archive_profile: dict[str, Any], errors: list[str]) -> None:
    value = doc["sealed_host_contract"]
    expected = archive_profile["sealed_host_contract"]
    if not exact_keys(value, {"VCPToolBox_sealed_commit", "VCPToolBox_sealed_tree", "inputs"}, "sealed host contract", errors):
        return
    assert isinstance(value, dict)
    if not is_oid(value["VCPToolBox_sealed_commit"]) or not is_oid(value["VCPToolBox_sealed_tree"]):
        errors.append("sealed host contract OID invalid")
    if type(value["inputs"]) is not list:
        errors.append("sealed host contract inputs must be list")
    else:
        for index, row in enumerate(value["inputs"]):
            if not exact_keys(row, {"path", "blob_oid", "sha256"}, f"sealed host input {index}", errors):
                continue
            assert isinstance(row, dict)
            safe_relative_path(row["path"], f"sealed host input {index}.path", errors)
            if not is_oid(row["blob_oid"]) or not is_sha256(row["sha256"]):
                errors.append(f"sealed host input {index} identifier invalid")
    if value != expected:
        errors.append("sealed host contract differs from immutable host source")


def validate_source_inventory_and_mapping(doc: dict[str, Any], source_profile: dict[str, Any], archive_profile: dict[str, Any], errors: list[str]) -> None:
    records = doc["source_inventory"]
    if type(records) is not list:
        errors.append("source inventory must be list")
        return
    for index, row in enumerate(records):
        source_record_schema(row, f"source inventory record {index}", errors)
    if records != source_profile["records"]:
        errors.append("source inventory differs from sealed source profile")
    root_prefix = archive_profile["archive_encoding"]["root_prefix"]
    members = doc["archive_member_inventory"]
    if type(members) is not list:
        errors.append("archive member inventory must be list")
        return
    for index, row in enumerate(members):
        archive_member_schema(row, root_prefix, f"archive member record {index}", errors)
    expected = core.derive_archive_members(source_profile["records"], root_prefix)
    if members != expected:
        errors.append("archive member inventory does not derive from sealed source inventory")


def validate_manifest_evidence(doc: dict[str, Any], source_profile: dict[str, Any], archive_profile: dict[str, Any], errors: list[str]) -> None:
    value = doc["manifest_evidence"]
    if not exact_keys(value, {"blocked_manifest_b64", "enabled_manifest_paths"}, "manifest evidence", errors):
        return
    assert isinstance(value, dict)
    blocked = decode_b64(value["blocked_manifest_b64"], "blocked manifest", errors)
    if blocked is not None and core.sha256_bytes(blocked) != source_profile["blocked_plugin_manifest_sha256"]:
        errors.append("blocked manifest bytes do not match sealed source profile")
    if value["enabled_manifest_paths"] != []:
        errors.append("enabled manifest member is forbidden")
    source_paths = [row["source_path"] for row in source_profile["records"]]
    contract = archive_profile["manifest_contract"]
    if contract["enabled_manifest_path"] in source_paths or contract["blocked_manifest_path"] not in source_paths:
        errors.append("blocked versus enabled manifest inventory mismatch")


def validate_entrypoint(doc: dict[str, Any], source_profile: dict[str, Any], archive_profile: dict[str, Any], errors: list[str]) -> None:
    value = doc["entrypoint"]
    if not exact_keys(value, {"source_b64"}, "entrypoint", errors):
        return
    assert isinstance(value, dict)
    raw = decode_b64(value["source_b64"], "entrypoint source", errors)
    if raw is None:
        return
    if core.sha256_bytes(raw) != source_profile["direct_entrypoint_sha256"]:
        errors.append("entrypoint bytes do not match sealed source profile")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        errors.append("entrypoint source must be UTF-8")
        return
    if unicodedata.normalize("NFC", text) != text:
        errors.append("entrypoint source must be NFC")
    exports_match = re.search(r"module\.exports\s*=\s*\{([^}]*)\}\s*;", text)
    if exports_match is None:
        errors.append("CommonJS export declaration missing")
    else:
        exports = [item.strip() for item in exports_match.group(1).split(",") if item.strip()]
        if exports != archive_profile["entrypoint_contract"]["commonjs_exports"]:
            errors.append("CommonJS export inventory mismatch")
    function_name = archive_profile["entrypoint_contract"]["native_load_allowed_only_inside_function"]
    function_index = text.find(f"function {function_name}")
    if function_index < 0:
        errors.append("native-load function missing")
        return
    modules = [match.group(1) for match in re.finditer(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)", text)]
    if modules != [archive_profile["entrypoint_contract"]["native_require_module"]]:
        errors.append("native require module inventory mismatch")
    if any(match.start() < function_index for match in re.finditer(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)", text)):
        errors.append("eager native load detected")


def validate_napi_methods(doc: dict[str, Any], archive_profile: dict[str, Any], errors: list[str]) -> None:
    methods = doc["native_napi_methods"]
    if type(methods) is not list or any(type(item) is not str for item in methods):
        errors.append("native N-API methods must be string list")
    elif methods != archive_profile["entrypoint_contract"]["native_NAPI_methods"]:
        errors.append("native N-API method inventory mismatch")


def validate_synthetic_archive(doc: dict[str, Any], archive_profile: dict[str, Any], errors: list[str]) -> tuple[bytes | None, str | None, int | None]:
    value = doc["synthetic_archive"]
    if not exact_keys(value, SYNTHETIC_ARCHIVE_KEYS, "synthetic archive", errors):
        return None, None, None
    assert isinstance(value, dict)
    members = value["members"]
    if type(members) is not list:
        errors.append("synthetic archive members must be list")
        return None, None, None
    root_prefix = archive_profile["archive_encoding"]["root_prefix"]
    for index, row in enumerate(members):
        synthetic_member_schema(row, root_prefix, f"synthetic member {index}", errors)
    expected_members = core.derive_synthetic_members(archive_profile)
    if members != expected_members:
        errors.append("synthetic archive members differ from fixed structural inputs")
    projected = [core.member_manifest_projection(row) for row in members if type(row) is dict and set(row) == SYNTHETIC_MEMBER_KEYS]
    expected_manifest_sha = core.sha256_bytes(core.canonical(projected))
    if not is_sha256(value["member_manifest_sha256"]) or value["member_manifest_sha256"] != expected_manifest_sha:
        errors.append("synthetic archive member manifest SHA mismatch")
    raw = decode_b64(value["archive_bytes_b64"], "synthetic archive bytes", errors)
    if raw is None:
        return None, None, None
    actual_sha = core.sha256_bytes(raw)
    if not is_sha256(value["archive_sha256"]) or value["archive_sha256"] != actual_sha:
        errors.append("synthetic archive SHA mismatch")
    if not is_safe_int(value["archive_byte_length"]) or value["archive_byte_length"] != len(raw):
        errors.append("synthetic archive byte length mismatch")
    try:
        derived = core.encode_exact_ustar(members)
        if raw != derived:
            errors.append("archive bytes are not deterministic encoding")
        parsed = core.parse_exact_ustar(raw)
        expected_parsed = [
            {key: row[key] for key in ("archive_path", "mode", "uid", "gid", "uname", "gname", "mtime", "byte_length", "sha256")}
            for row in members
            if type(row) is dict
        ]
        if parsed != expected_parsed:
            errors.append("parsed ustar members differ from structural records")
    except Exception as exc:
        errors.append(f"synthetic archive parse or encoding failed: {type(exc).__name__}")
    return raw, actual_sha, len(raw)


def validate_lifecycle_proofs(doc: dict[str, Any], archive_profile: dict[str, Any], archive_bytes: bytes | None, errors: list[str]) -> None:
    if doc["output_request"] != {"caller_output_path": None}:
        errors.append("caller supplied output path forbidden")
    proofs = doc["lifecycle_execution_proofs"]
    expected_keys = {"success", "failure", "residue_probe", "wrong_return_probe"}
    if not exact_keys(proofs, expected_keys, "lifecycle execution proofs", errors) or archive_bytes is None:
        return
    assert isinstance(proofs, dict)
    if exact_keys(proofs["success"], SUCCESS_KEYS, "success lifecycle proof", errors):
        success = proofs["success"]
        assert isinstance(success, dict)
        returned = success["return"]
        if exact_keys(returned, {"archive_sha256", "archive_byte_length", "archive_bytes_in_memory_b64"}, "success return", errors):
            assert isinstance(returned, dict)
            returned_bytes = decode_b64(returned["archive_bytes_in_memory_b64"], "success returned bytes", errors)
            if returned_bytes is not None:
                if returned_bytes != archive_bytes:
                    errors.append("success returned bytes do not equal archive bytes")
                if returned["archive_sha256"] != core.sha256_bytes(returned_bytes) or returned["archive_byte_length"] != len(returned_bytes):
                    errors.append("success returned byte metadata mismatch")
    if exact_keys(proofs["failure"], FAILURE_KEYS, "failure lifecycle proof", errors):
        failure = proofs["failure"]
        assert isinstance(failure, dict)
        if failure["return"] != {"stable_error_code": "SYNTHETIC_FAILURE"}:
            errors.append("failure output return exposes archive bytes or wrong code")
    if exact_keys(proofs["residue_probe"], RESIDUE_PROBE_KEYS, "residue probe", errors):
        residue = proofs["residue_probe"]
        assert isinstance(residue, dict)
        if residue["probe_result"] != "CLEANUP_RESIDUE_DETECTED" or residue["observed_before_cleanup_residue_relative_paths"] != ["archive.tar"]:
            errors.append("actual cleanup residue probe mismatch")
        if residue["return"] != {"stable_error_code": "SYNTHETIC_CLEANUP_FAILURE"}:
            errors.append("cleanup residue probe fail-closed return mismatch")
    if exact_keys(proofs["wrong_return_probe"], WRONG_RETURN_PROBE_KEYS, "wrong return probe", errors):
        wrong = proofs["wrong_return_probe"]
        assert isinstance(wrong, dict)
        observed = decode_b64(wrong["observed_returned_archive_bytes_b64"], "wrong return probe bytes", errors)
        if observed is not None:
            if wrong["probe_result"] != "RETURN_BYTES_MISMATCH_DETECTED" or observed == archive_bytes:
                errors.append("actual wrong-return probe mismatch")
            if wrong["expected_archive_sha256"] != core.sha256_bytes(archive_bytes) or wrong["observed_returned_archive_sha256"] != core.sha256_bytes(observed) or wrong["observed_returned_archive_byte_length"] != len(observed):
                errors.append("wrong-return probe byte binding mismatch")
        if wrong["return"] != {"stable_error_code": "SYNTHETIC_RETURN_BYTES_MISMATCH"}:
            errors.append("wrong-return probe fail-closed return mismatch")
    try:
        expected = core.run_lifecycle_proofs(archive_profile, archive_bytes)
    except Exception as exc:
        errors.append(f"stable BLOCK: actual lifecycle execution failed: {type(exc).__name__}")
        return
    if proofs != expected:
        errors.append("lifecycle execution proofs do not derive from actual owned temp root")


def validate(doc: object) -> list[str]:
    errors: list[str] = []
    if not exact_keys(doc, TOP_KEYS, "root", errors):
        return errors
    assert isinstance(doc, dict)
    if doc["schema_version"] != "agents-os.m0c-plan-structural-witness.v0.1-r3":
        errors.append("schema version mismatch")
    if doc["environment"] != "SYNTHETIC_TEST":
        errors.append("environment must be SYNTHETIC_TEST")
    try:
        archive_profile, source_profile = core.load_profiles()
        r2_profile = yaml.safe_load(R2_ARCHIVE_PROFILE.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"stable BLOCK: profile parse {type(exc).__name__}"]
    validate_profile(archive_profile, r2_profile, errors)
    validate_source_profile_and_files(source_profile, errors)
    if doc["archive_profile_sha256"] != core.sha256_file(core.ARCHIVE_PROFILE):
        errors.append("archive profile SHA mismatch")
    if doc["source_inventory_profile_sha256"] != core.sha256_file(core.SOURCE_PROFILE):
        errors.append("source inventory profile SHA mismatch")
    validate_source_commitment(doc, source_profile, errors)
    validate_host_contract(doc, archive_profile, errors)
    validate_manifest_evidence(doc, source_profile, archive_profile, errors)
    validate_entrypoint(doc, source_profile, archive_profile, errors)
    validate_napi_methods(doc, archive_profile, errors)
    validate_source_inventory_and_mapping(doc, source_profile, archive_profile, errors)
    archive_bytes, _, _ = validate_synthetic_archive(doc, archive_profile, errors)
    validate_lifecycle_proofs(doc, archive_profile, archive_bytes, errors)
    if doc["terminal_outcome"] != "NOT_ACTIVATED":
        errors.append("terminal outcome must be NOT_ACTIVATED")
    if not is_sha256(doc["root_fingerprint"]):
        errors.append("root fingerprint invalid")
    else:
        unsigned = dict(doc)
        unsigned.pop("root_fingerprint")
        if doc["root_fingerprint"] != core.sha256_bytes(core.canonical(unsigned)):
            errors.append("root fingerprint mismatch")
    return errors


def resign(doc: dict[str, Any]) -> None:
    unsigned = dict(doc)
    unsigned.pop("root_fingerprint", None)
    doc["root_fingerprint"] = core.sha256_bytes(core.canonical(unsigned))


def refresh_synthetic_archive(doc: dict[str, Any]) -> None:
    archive = doc["synthetic_archive"]
    assert isinstance(archive, dict)
    members = archive["members"]
    assert isinstance(members, list)
    raw = core.encode_exact_ustar(members)
    archive["member_manifest_sha256"] = core.sha256_bytes(core.canonical([core.member_manifest_projection(row) for row in members]))
    archive["archive_bytes_b64"] = core.b64(raw)
    archive["archive_sha256"] = core.sha256_bytes(raw)
    archive["archive_byte_length"] = len(raw)


def refresh_lifecycle_proofs(doc: dict[str, Any]) -> None:
    archive_profile, _ = core.load_profiles()
    archive = doc["synthetic_archive"]
    assert isinstance(archive, dict)
    raw = base64.b64decode(str(archive["archive_bytes_b64"]), validate=True)
    doc["lifecycle_execution_proofs"] = core.run_lifecycle_proofs(archive_profile, raw)


def self_test(doc: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    def expect(case_id: str, expected: str, mutate) -> None:
        candidate = copy.deepcopy(doc)
        mutate(candidate)
        resign(candidate)
        errors = validate(candidate)
        if not any(expected in error for error in errors):
            failures.append(f"{case_id} missing target semantic rejection: {errors}")

    expect("R3S01_MEMBER_MANIFEST_OLD_FIVE_FIELD", "member manifest SHA mismatch", lambda d: d["synthetic_archive"].update({"member_manifest_sha256": core.sha256_bytes(core.canonical([{key: row[key] for key in ("source_path", "archive_path", "kind", "byte_length", "sha256")} for row in d["synthetic_archive"]["members"]]))}))
    expect("R3S03_CALLER_OUTPUT_PATH", "caller supplied output path forbidden", lambda d: d["output_request"].update({"caller_output_path": "/tmp/forbidden.tar"}))
    expect("R3S04_CLAIMED_CLEANUP_RESIDUE", "lifecycle execution proofs do not derive", lambda d: d["lifecycle_execution_proofs"]["success"]["post_cleanup_residue_relative_paths"].append("archive.tar"))
    expect("R3S05_WRONG_SUCCESS_RETURN_BYTES", "success returned bytes do not equal archive bytes", lambda d: d["lifecycle_execution_proofs"]["success"]["return"].update({"archive_bytes_in_memory_b64": core.b64(b"wrong"), "archive_sha256": core.sha256_bytes(b"wrong"), "archive_byte_length": 5}))
    expect("R3S06_FAILURE_DELIVERY_FIELD", "failure output return exposes archive bytes or wrong code", lambda d: d["lifecycle_execution_proofs"]["failure"]["return"].update({"archive_bytes_in_memory_b64": ""}))
    expect("R3S07_RESIDUE_PROBE_SUPPRESSION", "actual cleanup residue probe mismatch", lambda d: d["lifecycle_execution_proofs"]["residue_probe"].update({"observed_before_cleanup_residue_relative_paths": []}))
    expect("R3S08_WRONG_RETURN_PROBE_SUPPRESSION", "actual wrong-return probe mismatch", lambda d: d["lifecycle_execution_proofs"]["wrong_return_probe"].update({"probe_result": "PASS"}))
    expect("R3S09_ENABLED_MANIFEST", "enabled manifest member is forbidden", lambda d: d["manifest_evidence"]["enabled_manifest_paths"].append("plugin-manifest.json"))
    expect("R3S10_NAPI_EXPANSION", "native N-API method inventory mismatch", lambda d: d["native_napi_methods"].append("start_runtime"))

    def eager_native_load(d: dict[str, Any]) -> None:
        raw = base64.b64decode(d["entrypoint"]["source_b64"])
        marker = b"async function processToolCall"
        changed = raw.replace(marker, b"const eager = require('./agents-os-resident.linux-x64-gnu.node');\n" + marker, 1)
        d["entrypoint"]["source_b64"] = core.b64(changed)
        for row in d["source_inventory"]:
            if row["source_path"] == "index.js":
                row["byte_length"] = len(changed)
                row["sha256"] = core.sha256_bytes(changed)
    expect("R3S11_EAGER_NATIVE_LOAD", "eager native load detected", eager_native_load)

    def archive_metadata_drift(d: dict[str, Any]) -> None:
        archive = d["synthetic_archive"]
        raw = bytearray(base64.b64decode(archive["archive_bytes_b64"]))
        raw[136:148] = core.octal_field(1, 12)
        raw[148:156] = b" " * 8
        checksum = sum(raw[:148] + b" " * 8 + raw[156:512])
        raw[148:156] = f"{checksum:06o}\0 ".encode("ascii")
        changed = bytes(raw)
        archive["archive_bytes_b64"] = core.b64(changed)
        archive["archive_sha256"] = core.sha256_bytes(changed)
        archive["archive_byte_length"] = len(changed)
        refresh_lifecycle_proofs(d)
    expect("R3S12_ARCHIVE_METADATA_DRIFT", "archive bytes are not deterministic encoding", archive_metadata_drift)
    expect("R3S13_UNKNOWN_ROOT_FIELD", "root field inventory mismatch", lambda d: d.update({"unknown": 1}))
    expect("R3S14_BOOLEAN_TYPE", "environment must be SYNTHETIC_TEST", lambda d: d.update({"environment": True}))
    expect("R3S15_NON_NFC_PATH", "must be nonempty NFC path", lambda d: d["synthetic_archive"]["members"][0].update({"source_path": "e\u0301.txt", "archive_path": "agents-os-resident/e\u0301.txt"}))
    archive_profile, _ = core.load_profiles()
    r2_profile = yaml.safe_load(R2_ARCHIVE_PROFILE.read_text(encoding="utf-8"))
    profile_drift = copy.deepcopy(archive_profile)
    profile_drift["archive_encoding"]["member_manifest"]["row_field_inventory"] = ["source_path"]
    profile_errors: list[str] = []
    validate_profile(profile_drift, r2_profile, profile_errors)
    if not any("member manifest field inventory mismatch" in error for error in profile_errors):
        failures.append(f"R3S16_MEMBER_MANIFEST_PROFILE_DRIFT missing target semantic rejection: {profile_errors}")
    try:
        json.loads('{"a":1,"a":2}', object_pairs_hook=strict_pairs)
        failures.append("R3S17_DUPLICATE_JSON_KEY accepted")
    except ValueError:
        pass
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        doc = load_strict(args.fixture)
        errors = validate(doc)
        if not errors and args.self_test:
            errors.extend(self_test(doc))
    except Exception as exc:
        errors = [f"stable BLOCK: {type(exc).__name__}: {exc}"]
    if errors:
        print(json.dumps({"result": "BLOCK", "errors": errors}, indent=2))
        return 1
    print(json.dumps({"result": "PASS", "structural_negative_mutations": 15 if args.self_test else 0, "parser_probes": 1 if args.self_test else 0, "actual_lifecycle_probes": 2 if args.self_test else 0, "terminal_outcome": "NOT_ACTIVATED"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
