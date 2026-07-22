#!/usr/bin/env python3
"""Validate Phase 5C M0-C Plan R4 exact-byte and cleanup-fault evidence.

The validator consumes an R4 profile and a synthetic witness only. It does not
package, install, enable, or load a plugin, modify extension source or
VCPToolBox, or touch runtime, database, provider, private Memory, sensing, or
real-effect boundaries.
"""

from __future__ import annotations

import argparse
import base64
import copy
import json
from pathlib import Path
import re
from typing import Any

import yaml

import phase5c_m0c_r4_structural_core as core


TOP_KEYS = {
    "schema_version",
    "environment",
    "archive_profile_sha256",
    "synthetic_archive",
    "output_request",
    "lifecycle_execution_proofs",
    "terminal_outcome",
    "root_fingerprint",
}
SYNTHETIC_MEMBER_KEYS = set(core.MEMBER_MANIFEST_FIELDS) | {"content_b64"}
SYNTHETIC_ARCHIVE_KEYS = {
    "members",
    "member_manifest_sha256",
    "archive_bytes_b64",
    "archive_sha256",
    "archive_byte_length",
}
SUCCESS_KEYS = {
    "initial_owned_root_inventory",
    "before_cleanup_inventory",
    "post_cleanup_owned_root_exists",
    "post_cleanup_residue_relative_paths",
    "return",
}
FAULT_KEYS = {
    "fault_injection",
    "before_cleanup_attempt_inventory",
    "cleanup_attempt_result",
    "post_cleanup_owned_root_exists",
    "post_cleanup_residue_relative_paths",
    "probe_result",
    "return",
    "finalizer_runs_only_after_post_cleanup_observation",
}
WRONG_RETURN_KEYS = {
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


def exact_keys(value: object, expected: set[str], label: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{label} must be object")
        return False
    if set(value) != expected:
        errors.append(f"{label} field inventory mismatch")
        return False
    return True


def safe_int(value: object) -> bool:
    return type(value) is int and 0 <= value <= 9007199254740991


def sha256(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def decode_b64(value: object, label: str, errors: list[str]) -> bytes | None:
    if type(value) is not str:
        errors.append(f"{label} must be base64 string")
        return None
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        errors.append(f"{label} invalid base64")
        return None


def validate_profile(profile: object, errors: list[str]) -> bool:
    expected_top = {
        "schema_version",
        "profile_id",
        "date",
        "owner",
        "agent_steward",
        "status",
        "runtime_usable",
        "inherits",
        "archive_encoding",
        "output_lifecycle",
        "synthetic_archive_exercise",
        "boundary",
    }
    if not exact_keys(profile, expected_top, "R4 profile", errors):
        return False
    assert isinstance(profile, dict)
    if profile["schema_version"] != "agents-os.m0c.exact-archive-output-lifecycle-profile.v0.1-r4":
        errors.append("R4 profile schema version mismatch")
    if profile["profile_id"] != "PHASE_5C_M0C_EXACT_ARCHIVE_OUTPUT_LIFECYCLE_PROFILE_V0_1_R4":
        errors.append("R4 profile identifier mismatch")
    if profile["runtime_usable"] is not False:
        errors.append("R4 profile must be runtime unusable")
    inherits = profile["inherits"]
    if not exact_keys(inherits, {
        "R3_archive_output_lifecycle_profile",
        "R3_archive_output_lifecycle_profile_sha256",
        "R3_independent_review_sha256",
    }, "R4 inherits", errors):
        return False
    assert isinstance(inherits, dict)
    if inherits["R3_archive_output_lifecycle_profile"] != "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r3.yaml":
        errors.append("R4 immutable R3 profile path mismatch")
    if inherits["R3_archive_output_lifecycle_profile_sha256"] != "71d534e8b98b8241216049433280261fcbba18590819ea8b6a692e47e46c0062":
        errors.append("R4 immutable R3 profile binding mismatch")
    if inherits["R3_independent_review_sha256"] != "14e07fb392419a45e71b205493907bc9306e3dc6a3ab82a034d51de13b2df4e0":
        errors.append("R4 immutable R3 review binding mismatch")
    encoding = profile["archive_encoding"]
    expected_encoding = {
        "format", "compression", "byte_stream", "checksum_algorithm", "checksum_preimage",
        "root_prefix", "explicit_directory_entries", "regular_files_only", "member_order",
        "path_separator", "reject_absolute_traversal_backslash_duplicate_or_non_NFC_paths",
        "member_manifest", "block_size_bytes", "header_byte_contract",
        "header_value_normalization", "body_padding", "end_of_archive",
    }
    if not exact_keys(encoding, expected_encoding, "R4 archive encoding", errors):
        return False
    assert isinstance(encoding, dict)
    expected_literals = {
        "format": "POSIX_USTAR",
        "compression": "NONE",
        "byte_stream": "complete_raw_tar_bytes",
        "checksum_algorithm": "SHA-256",
        "checksum_preimage": "complete_raw_tar_bytes_including_two_512_byte_zero_blocks",
        "root_prefix": "agents-os-resident/",
        "explicit_directory_entries": "forbidden",
        "regular_files_only": True,
        "member_order": "UTF8_BYTEWISE_ASCENDING_SOURCE_PATH",
        "path_separator": "FORWARD_SLASH_ONLY",
        "reject_absolute_traversal_backslash_duplicate_or_non_NFC_paths": True,
        "block_size_bytes": 512,
    }
    for key, expected in expected_literals.items():
        if encoding[key] != expected:
            errors.append(f"R4 archive encoding {key} mismatch")
    manifest = encoding["member_manifest"]
    if not exact_keys(manifest, {
        "algorithm", "preimage", "encoding", "object_key_order", "separators", "row_field_inventory",
    }, "R4 member manifest", errors):
        return False
    assert isinstance(manifest, dict)
    if manifest != {
        "algorithm": "SHA-256",
        "preimage": "canonical_JSON_array_of_exact_member_projection_rows",
        "encoding": "UTF-8",
        "object_key_order": "LEXICOGRAPHIC_SORTED",
        "separators": "NO_INSIGNIFICANT_WHITESPACE",
        "row_field_inventory": list(core.MEMBER_MANIFEST_FIELDS),
    }:
        errors.append("R4 member manifest contract mismatch")
    expected_header = {
        "filename": {"offset": 0, "width": 100, "encoding": "UTF8_NUL_THEN_ZERO_FILL", "value_source": "archive_path"},
        "mode": {"offset": 100, "width": 8, "encoding": "ZERO_PADDED_OCTAL_THEN_NUL", "value_source": "mode"},
        "uid": {"offset": 108, "width": 8, "encoding": "ZERO_PADDED_OCTAL_THEN_NUL", "value_source": "uid"},
        "gid": {"offset": 116, "width": 8, "encoding": "ZERO_PADDED_OCTAL_THEN_NUL", "value_source": "gid"},
        "size": {"offset": 124, "width": 12, "encoding": "ZERO_PADDED_OCTAL_THEN_NUL", "value_source": "byte_length"},
        "mtime": {"offset": 136, "width": 12, "encoding": "ZERO_PADDED_OCTAL_THEN_NUL", "value_source": "mtime"},
        "checksum": {"offset": 148, "width": 8, "preimage_fill_hex": "20", "encoding": "SIX_OCTAL_DIGITS_NUL_ASCII_SPACE", "unsigned_byte_sum": True},
        "typeflag": {"offset": 156, "width": 1, "encoding": "EXACT_HEX", "hex": "30"},
        "linkname": {"offset": 157, "width": 100, "encoding": "ALL_ZERO_BYTES"},
        "magic": {"offset": 257, "width": 6, "encoding": "EXACT_HEX", "hex": "757374617200"},
        "version": {"offset": 263, "width": 2, "encoding": "EXACT_HEX", "hex": "3030"},
        "uname": {"offset": 265, "width": 32, "encoding": "UTF8_NUL_THEN_ZERO_FILL", "value_source": "uname"},
        "gname": {"offset": 297, "width": 32, "encoding": "UTF8_NUL_THEN_ZERO_FILL", "value_source": "gname"},
        "devmajor": {"offset": 329, "width": 8, "encoding": "ALL_ZERO_BYTES"},
        "devminor": {"offset": 337, "width": 8, "encoding": "ALL_ZERO_BYTES"},
        "prefix": {"offset": 345, "width": 155, "encoding": "ALL_ZERO_BYTES"},
        "trailing_unused": {"offset": 500, "width": 12, "encoding": "ALL_ZERO_BYTES"},
    }
    if encoding["header_byte_contract"] != expected_header:
        errors.append("R4 complete ustar header byte contract mismatch")
    if encoding["header_value_normalization"] != {
        "mode_octal": "0644", "uid": 0, "gid": 0, "uname": "", "gname": "",
        "mtime_unix_seconds": 0, "numeric_overflow": "REJECT",
    }:
        errors.append("R4 header value normalization mismatch")
    if encoding["body_padding"] != {"alignment_bytes": 512, "fill_hex": "00"}:
        errors.append("R4 body padding contract mismatch")
    if encoding["end_of_archive"] != {"zero_block_count": 2, "block_size_bytes": 512}:
        errors.append("R4 terminal block contract mismatch")
    lifecycle = profile["output_lifecycle"]
    if not exact_keys(lifecycle, {
        "caller_supplied_output_path", "staging_root", "archive_location_before_delivery",
        "delivery_mode", "serialized_success_return_fields", "serialized_failure_return_fields",
        "actual_observation_contract", "cleanup_fault_contract", "required_negative_actual_probes",
    }, "R4 output lifecycle", errors):
        return False
    assert isinstance(lifecycle, dict)
    if (
        lifecycle["caller_supplied_output_path"] != "forbidden"
        or lifecycle["staging_root"] != "newly_created_owned_synthetic_temporary_directory"
        or lifecycle["archive_location_before_delivery"] != "owned_temp_root/archive.tar"
        or lifecycle["delivery_mode"] != "RETURN_IN_MEMORY_BYTES_ONLY"
        or lifecycle["serialized_success_return_fields"] != [
            "archive_sha256",
            "archive_byte_length",
            "archive_bytes_in_memory_b64",
        ]
        or lifecycle["serialized_failure_return_fields"] != ["stable_error_code"]
    ):
        errors.append("R4 inherited output lifecycle contract mismatch")
    if lifecycle["actual_observation_contract"] != {
        "initial_owned_root_inventory": [],
        "success_before_cleanup_inventory": ["archive.tar"],
        "failure_before_cleanup_inventory": [],
        "post_cleanup_owned_root_exists": False,
        "post_cleanup_residue_relative_paths": [],
    }:
        errors.append("R4 normal cleanup observation contract mismatch")
    expected_fault = {
        "environment": "SYNTHETIC_TEST",
        "root_ownership": "NEWLY_CREATED_DISPOSABLE_OWNED_TEMP_ROOT",
        "fault_injection": "ATTEMPT_ROOT_RMDIR_WHILE_ARCHIVE_TAR_REMAINS",
        "expected_post_attempt_owned_root_exists": True,
        "expected_post_attempt_residue_relative_paths": ["archive.tar"],
        "required_result": "CLEANUP_RESIDUE_DETECTED",
        "required_fail_closed_return": {"stable_error_code": "SYNTHETIC_CLEANUP_RESIDUE"},
        "finalizer_may_remove_root_only_after_post_attempt_observation": True,
    }
    if lifecycle["cleanup_fault_contract"] != expected_fault:
        errors.append("R4 post-cleanup fault contract mismatch")
    if lifecycle["required_negative_actual_probes"] != ["CLEANUP_RESIDUE_DETECTED", "RETURN_BYTES_MISMATCH_DETECTED"]:
        errors.append("R4 negative probe inventory mismatch")
    exercise = profile["synthetic_archive_exercise"]
    if exercise != {
        "environment": "SYNTHETIC_TEST",
        "members": [
            {"source_path": "README.md", "content_utf8": "synthetic-only README"},
            {"source_path": "index.js", "content_utf8": "module.exports = {};"},
            {"source_path": "package.json", "content_utf8": '{"name":"synthetic-only"}'},
            {"source_path": "plugin-manifest.json.block", "content_utf8": '{"disabled":true}'},
        ],
    }:
        errors.append("R4 synthetic archive exercise contract mismatch")
    boundary = profile["boundary"]
    expected_boundary = {
        "synthetic_witness_runtime_usable": False,
        "owned_temp_root_synthetic_test_only": True,
        "implementation_authorized": False,
        "VCPToolBox_change_or_start_authorized": False,
        "plugin_enablement_or_native_host_loading_authorized": False,
        "database_private_Memory_provider_sensing_or_effect_authorized": False,
        "release_deploy_publish_authorized": False,
    }
    if boundary != expected_boundary:
        errors.append("R4 boundary contract mismatch")
    return not errors


def validate_member(row: object, profile: dict[str, Any], label: str, errors: list[str]) -> bool:
    if not exact_keys(row, SYNTHETIC_MEMBER_KEYS, label, errors):
        return False
    assert isinstance(row, dict)
    ok = True
    if not core.safe_path(row["source_path"]) or not core.safe_path(row["archive_path"]):
        errors.append(f"{label} path invalid")
        ok = False
    root_prefix = profile["archive_encoding"]["root_prefix"]
    if row["archive_path"] != root_prefix + str(row["source_path"]):
        errors.append(f"{label} archive path mapping mismatch")
        ok = False
    if row["kind"] != "regular_file":
        errors.append(f"{label} kind mismatch")
        ok = False
    for key in ("mode", "uid", "gid", "mtime", "byte_length"):
        if not safe_int(row[key]):
            errors.append(f"{label} {key} invalid")
            ok = False
    for key in ("uname", "gname"):
        if type(row[key]) is not str:
            errors.append(f"{label} {key} invalid")
            ok = False
    content = decode_b64(row["content_b64"], f"{label} content", errors)
    if content is not None:
        if row["byte_length"] != len(content) or row["sha256"] != core.sha256_bytes(content):
            errors.append(f"{label} content commitment mismatch")
            ok = False
    if not sha256(row["sha256"]):
        errors.append(f"{label} sha256 invalid")
        ok = False
    return ok


def validate_synthetic_archive(doc: dict[str, Any], profile: dict[str, Any], errors: list[str]) -> bytes | None:
    archive = doc["synthetic_archive"]
    if not exact_keys(archive, SYNTHETIC_ARCHIVE_KEYS, "synthetic archive", errors):
        return None
    assert isinstance(archive, dict)
    members = archive["members"]
    if type(members) is not list:
        errors.append("synthetic archive members must be list")
        return None
    for index, row in enumerate(members):
        validate_member(row, profile, f"synthetic member {index}", errors)
    expected_members = core.derive_synthetic_members(profile)
    if members != expected_members:
        errors.append("synthetic members differ from R4 profile derivation")
    expected_manifest = core.sha256_bytes(core.canonical([
        core.member_projection(row) for row in members if type(row) is dict and set(row) == SYNTHETIC_MEMBER_KEYS
    ]))
    if archive["member_manifest_sha256"] != expected_manifest:
        errors.append("synthetic member manifest SHA mismatch")
    raw = decode_b64(archive["archive_bytes_b64"], "synthetic archive bytes", errors)
    if raw is None:
        return None
    if archive["archive_sha256"] != core.sha256_bytes(raw) or archive["archive_byte_length"] != len(raw):
        errors.append("synthetic archive byte commitment mismatch")
    try:
        core.verify_exact_ustar(profile, members, raw)
    except Exception:
        errors.append("archive bytes violate exact R4 ustar byte contract")
    return raw


def validate_lifecycle(doc: dict[str, Any], profile: dict[str, Any], raw: bytes | None, errors: list[str]) -> None:
    if doc["output_request"] != {"caller_output_path": None}:
        errors.append("caller supplied output path forbidden")
    proofs = doc["lifecycle_execution_proofs"]
    if not exact_keys(proofs, {"success", "failure", "cleanup_fault_probe", "wrong_return_probe"}, "lifecycle proofs", errors) or raw is None:
        return
    assert isinstance(proofs, dict)
    if exact_keys(proofs["success"], SUCCESS_KEYS, "success proof", errors):
        success = proofs["success"]
        assert isinstance(success, dict)
        returned = success["return"]
        if not exact_keys(returned, {"archive_sha256", "archive_byte_length", "archive_bytes_in_memory_b64"}, "success return", errors):
            return
        assert isinstance(returned, dict)
        returned_bytes = decode_b64(returned["archive_bytes_in_memory_b64"], "success returned bytes", errors)
        if returned_bytes is not None and (
            returned_bytes != raw
            or returned["archive_sha256"] != core.sha256_bytes(returned_bytes)
            or returned["archive_byte_length"] != len(returned_bytes)
        ):
            errors.append("success returned bytes do not equal archive bytes")
    if exact_keys(proofs["failure"], SUCCESS_KEYS, "failure proof", errors):
        failure = proofs["failure"]
        assert isinstance(failure, dict)
        if failure["return"] != {"stable_error_code": "SYNTHETIC_FAILURE"}:
            errors.append("failure output return mismatch")
    if exact_keys(proofs["cleanup_fault_probe"], FAULT_KEYS, "cleanup fault probe", errors):
        fault = proofs["cleanup_fault_probe"]
        assert isinstance(fault, dict)
        contract = profile["output_lifecycle"]["cleanup_fault_contract"]
        if fault["fault_injection"] != contract["fault_injection"] or fault["before_cleanup_attempt_inventory"] != ["archive.tar"]:
            errors.append("cleanup fault injection record mismatch")
        if fault["cleanup_attempt_result"] != "DIRECTORY_NOT_EMPTY":
            errors.append("cleanup fault attempt did not fail as injected")
        if fault["post_cleanup_owned_root_exists"] is not True or fault["post_cleanup_residue_relative_paths"] != ["archive.tar"]:
            errors.append("cleanup fault post-attempt observation mismatch")
        if fault["probe_result"] != contract["required_result"] or fault["return"] != contract["required_fail_closed_return"]:
            errors.append("cleanup fault fail-closed result mismatch")
        if fault["finalizer_runs_only_after_post_cleanup_observation"] is not True:
            errors.append("cleanup fault finalizer ordering mismatch")
    if exact_keys(proofs["wrong_return_probe"], WRONG_RETURN_KEYS, "wrong return probe", errors):
        wrong = proofs["wrong_return_probe"]
        assert isinstance(wrong, dict)
        observed = decode_b64(wrong["observed_returned_archive_bytes_b64"], "wrong return bytes", errors)
        if observed is not None and (
            wrong["probe_result"] != "RETURN_BYTES_MISMATCH_DETECTED"
            or observed == raw
            or wrong["expected_archive_sha256"] != core.sha256_bytes(raw)
            or wrong["observed_returned_archive_sha256"] != core.sha256_bytes(observed)
            or wrong["observed_returned_archive_byte_length"] != len(observed)
        ):
            errors.append("wrong return probe mismatch")
    try:
        actual = core.run_lifecycle_proofs(profile, raw)
    except Exception as exc:
        errors.append(f"stable BLOCK: actual R4 lifecycle execution failed: {type(exc).__name__}")
        return
    if proofs != actual:
        errors.append("lifecycle proofs do not derive from actual R4 owned-root observations")


def validate(doc: object) -> list[str]:
    errors: list[str] = []
    if not exact_keys(doc, TOP_KEYS, "root", errors):
        return errors
    assert isinstance(doc, dict)
    if doc["schema_version"] != "agents-os.m0c-plan-structural-witness.v0.1-r4":
        errors.append("R4 witness schema version mismatch")
    if doc["environment"] != "SYNTHETIC_TEST":
        errors.append("R4 witness environment mismatch")
    try:
        profile = core.load_profile()
    except Exception as exc:
        return [f"stable BLOCK: R4 profile parse {type(exc).__name__}"]
    validate_profile(profile, errors)
    if doc["archive_profile_sha256"] != core.sha256_file(core.ARCHIVE_PROFILE):
        errors.append("R4 archive profile SHA mismatch")
    raw = validate_synthetic_archive(doc, profile, errors)
    validate_lifecycle(doc, profile, raw, errors)
    if doc["terminal_outcome"] != "NOT_ACTIVATED":
        errors.append("terminal outcome must be NOT_ACTIVATED")
    if not sha256(doc["root_fingerprint"]):
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


def refresh_archive_commitments(doc: dict[str, Any]) -> None:
    archive = doc["synthetic_archive"]
    assert isinstance(archive, dict)
    raw = base64.b64decode(str(archive["archive_bytes_b64"]), validate=True)
    archive["archive_sha256"] = core.sha256_bytes(raw)
    archive["archive_byte_length"] = len(raw)


def self_test(doc: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    def expect(case_id: str, expected: str, mutate) -> None:
        candidate = copy.deepcopy(doc)
        mutate(candidate)
        resign(candidate)
        errors = validate(candidate)
        if not any(expected in error for error in errors):
            failures.append(f"{case_id} missing target semantic rejection: {errors}")

    def mutate_header(doc: dict[str, Any], offset: int, replacement: bytes) -> None:
        archive = doc["synthetic_archive"]
        assert isinstance(archive, dict)
        raw = bytearray(base64.b64decode(str(archive["archive_bytes_b64"]), validate=True))
        raw[offset:offset + len(replacement)] = replacement
        checksum = sum(raw[:148] + b" " * 8 + raw[156:512])
        raw[148:156] = f"{checksum:06o}".encode("ascii") + bytes([0]) + b" "
        archive["archive_bytes_b64"] = core.b64(bytes(raw))
        refresh_archive_commitments(doc)

    expect("R4S01_NUL_REGULAR_TYPEFLAG", "archive bytes violate exact R4 ustar byte contract", lambda d: mutate_header(d, 156, bytes([0])))
    expect("R4S02_NUMERIC_SPACE_TERMINATOR", "archive bytes violate exact R4 ustar byte contract", lambda d: mutate_header(d, 100, b"0000644 "))
    expect("R4S03_MAGIC_DRIFT", "archive bytes violate exact R4 ustar byte contract", lambda d: mutate_header(d, 257, b"x"))
    expect("R4S04_UNUSED_BYTE_DRIFT", "archive bytes violate exact R4 ustar byte contract", lambda d: mutate_header(d, 500, b"x"))

    def body_padding_drift(d: dict[str, Any]) -> None:
        archive = d["synthetic_archive"]
        assert isinstance(archive, dict)
        first = archive["members"][0]
        offset = 512 + first["byte_length"]
        mutate_header(d, offset, b"x")

    expect("R4S05_BODY_PADDING_DRIFT", "archive bytes violate exact R4 ustar byte contract", body_padding_drift)

    def terminal_drift(d: dict[str, Any]) -> None:
        archive = d["synthetic_archive"]
        assert isinstance(archive, dict)
        raw = bytearray(base64.b64decode(str(archive["archive_bytes_b64"]), validate=True))
        raw[-1] = 1
        archive["archive_bytes_b64"] = core.b64(bytes(raw))
        refresh_archive_commitments(d)

    expect("R4S06_TERMINAL_BLOCK_DRIFT", "archive bytes violate exact R4 ustar byte contract", terminal_drift)
    expect("R4S07_FAULT_RESIDUE_SUPPRESSION", "cleanup fault post-attempt observation mismatch", lambda d: d["lifecycle_execution_proofs"]["cleanup_fault_probe"].update({"post_cleanup_owned_root_exists": False, "post_cleanup_residue_relative_paths": []}))
    expect("R4S08_FAULT_RESULT_SUPPRESSION", "cleanup fault fail-closed result mismatch", lambda d: d["lifecycle_execution_proofs"]["cleanup_fault_probe"].update({"probe_result": "PASS"}))
    expect("R4S09_FAULT_FINALIZER_ORDER", "cleanup fault finalizer ordering mismatch", lambda d: d["lifecycle_execution_proofs"]["cleanup_fault_probe"].update({"finalizer_runs_only_after_post_cleanup_observation": False}))
    expect("R4S10_CALLER_OUTPUT_PATH", "caller supplied output path forbidden", lambda d: d["output_request"].update({"caller_output_path": "/tmp/forbidden"}))
    expect("R4S11_UNKNOWN_ROOT", "root field inventory mismatch", lambda d: d.update({"unknown": 1}))
    profile = core.load_profile()
    profile["archive_encoding"]["header_byte_contract"]["typeflag"]["hex"] = "00"
    profile_errors: list[str] = []
    validate_profile(profile, profile_errors)
    if not any("complete ustar header byte contract mismatch" in error for error in profile_errors):
        failures.append(f"R4S12_PROFILE_TYPEFLAG_DRIFT missing target semantic rejection: {profile_errors}")
    try:
        json.loads('{"a":1,"a":2}', object_pairs_hook=strict_pairs)
        failures.append("R4S13_DUPLICATE_JSON_KEY accepted")
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
    print(json.dumps({
        "result": "PASS",
        "structural_negative_mutations": 12 if args.self_test else 0,
        "parser_probes": 1 if args.self_test else 0,
        "actual_post_cleanup_fault_injections": 1 if args.self_test else 0,
        "terminal_outcome": "NOT_ACTIVATED",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
