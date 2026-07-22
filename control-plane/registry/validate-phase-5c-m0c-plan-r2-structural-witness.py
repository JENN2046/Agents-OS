#!/usr/bin/env python3
"""Fail-closed offline validator for the Phase 5C M0-C R2 structural witness.

The validator consumes fixed planning profiles and a synthetic JSON witness. It
does not package files, load a native addon, access VCPToolBox, or execute any
runtime, database, provider, private-Memory, sensing, or effect operation.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unicodedata

import yaml


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r2.yaml"
SOURCE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-sealed-source-inventory-v0.1-r2.yaml"
BUILDER_PATH = ROOT / "control-plane/registry/build-phase-5c-m0c-plan-r2-structural-witness.py"


def load_builder() -> object:
    spec = importlib.util.spec_from_file_location("phase5c_r2_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load structural witness builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()

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
    "success_output_lifecycle",
    "failure_output_lifecycle",
    "terminal_outcome",
    "root_fingerprint",
}
SOURCE_RECORD_KEYS = {"source_path", "kind", "byte_length", "sha256"}
ARCHIVE_MEMBER_KEYS = {"source_path", "archive_path", "kind", "byte_length", "sha256"}
SYNTHETIC_MEMBER_KEYS = {
    "source_path",
    "archive_path",
    "kind",
    "mode",
    "uid",
    "gid",
    "uname",
    "gname",
    "mtime",
    "content_b64",
    "byte_length",
    "sha256",
}
SYNTHETIC_ARCHIVE_KEYS = {"members", "member_manifest_sha256", "archive_bytes_b64", "archive_sha256", "archive_byte_length"}
SUCCESS_LIFECYCLE_KEYS = {"events", "residue_relative_paths", "return"}
FAILURE_LIFECYCLE_KEYS = {"events", "residue_relative_paths", "return"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def strict_pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def load_strict(path: Path) -> object:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=strict_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite number: {value}")),
    )


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
    if set(value) != expected:
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
    segments = value.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        errors.append(f"{label} traversal or empty segment")
        return False
    return True


def source_record_schema(row: object, label: str, errors: list[str]) -> bool:
    if not exact_keys(row, SOURCE_RECORD_KEYS, label, errors):
        return False
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
    ok = safe_relative_path(row["source_path"], f"{label}.source_path", errors)
    ok = safe_relative_path(row["archive_path"], f"{label}.archive_path", errors) and ok
    if type(row["archive_path"]) is str and not row["archive_path"].startswith(root_prefix):
        errors.append(f"{label}.archive_path outside archive root")
        ok = False
    if type(row["archive_path"]) is str and len(row["archive_path"].encode("utf-8")) > 100:
        errors.append(f"{label}.archive_path exceeds ustar name limit")
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
    ok = safe_relative_path(row["source_path"], f"{label}.source_path", errors)
    ok = safe_relative_path(row["archive_path"], f"{label}.archive_path", errors) and ok
    if type(row["archive_path"]) is str and row["archive_path"] != root_prefix + str(row["source_path"]):
        errors.append(f"{label}.archive_path does not derive from source path")
        ok = False
    if type(row["archive_path"]) is str and len(row["archive_path"].encode("utf-8")) > 100:
        errors.append(f"{label}.archive_path exceeds ustar name limit")
        ok = False
    if row["kind"] != "regular_file":
        errors.append(f"{label}.kind must be regular_file")
        ok = False
    for key in ("mode", "uid", "gid", "mtime", "byte_length"):
        if not is_safe_int(row[key]):
            errors.append(f"{label}.{key} invalid")
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
        if row["sha256"] != sha256_bytes(content):
            errors.append(f"{label}.sha256 does not match content")
            ok = False
    if not is_sha256(row["sha256"]):
        errors.append(f"{label}.sha256 invalid")
        ok = False
    return ok


def parse_octal(field: bytes) -> int:
    text = field.rstrip(b"\0 ")
    if not text or any(char not in b"01234567" for char in text):
        raise ValueError("invalid octal field")
    return int(text, 8)


def parse_exact_ustar(raw: bytes) -> list[dict[str, object]]:
    if len(raw) < 1024 or len(raw) % 512 != 0 or not raw.endswith(b"\0" * 1024):
        raise ValueError("ustar final zero-block contract mismatch")
    rows: list[dict[str, object]] = []
    offset = 0
    terminal = len(raw) - 1024
    while offset < terminal:
        header = raw[offset:offset + 512]
        if len(header) != 512 or header == b"\0" * 512:
            raise ValueError("unexpected zero or truncated ustar header")
        if header[257:263] != b"ustar\0" or header[263:265] != b"00" or header[156:157] != b"0":
            raise ValueError("ustar format fields mismatch")
        stored_checksum = parse_octal(header[148:156])
        computed_checksum = sum(header[:148] + b" " * 8 + header[156:])
        if stored_checksum != computed_checksum:
            raise ValueError("ustar header checksum mismatch")
        name = header[:100].split(b"\0", 1)[0].decode("utf-8", "strict")
        uname = header[265:297].split(b"\0", 1)[0].decode("utf-8", "strict")
        gname = header[297:329].split(b"\0", 1)[0].decode("utf-8", "strict")
        size = parse_octal(header[124:136])
        data_start = offset + 512
        data_end = data_start + size
        padded_end = data_start + ((size + 511) // 512) * 512
        if padded_end > terminal:
            raise ValueError("ustar member exceeds archive boundary")
        content = raw[data_start:data_end]
        rows.append(
            {
                "archive_path": name,
                "mode": parse_octal(header[100:108]),
                "uid": parse_octal(header[108:116]),
                "gid": parse_octal(header[116:124]),
                "uname": uname,
                "gname": gname,
                "mtime": parse_octal(header[136:148]),
                "byte_length": size,
                "sha256": sha256_bytes(content),
            }
        )
        offset = padded_end
    if offset != terminal:
        raise ValueError("ustar terminal boundary mismatch")
    return rows


def source_profile_valid(profile: object, errors: list[str]) -> bool:
    if type(profile) is not dict or type(profile.get("records")) is not list:
        errors.append("source inventory profile malformed")
        return False
    records = profile["records"]
    ok = True
    if profile.get("record_count") != len(records):
        errors.append("source inventory profile record count mismatch")
        ok = False
    for index, row in enumerate(records):
        ok = source_record_schema(row, f"source inventory profile record {index}", errors) and ok
    paths = [row.get("source_path") for row in records if type(row) is dict]
    if len(paths) != len(set(paths)):
        errors.append("source inventory profile duplicate source paths")
        ok = False
    if profile.get("records_canonical_sha256") != sha256_bytes(canonical(records)):
        errors.append("source inventory profile canonical digest mismatch")
        ok = False
    return ok


def validate_source_commitment(doc: dict[str, object], source_profile: dict[str, object], errors: list[str]) -> None:
    expected_keys = {
        "source_root",
        "source_commit",
        "package_manifest_sha256",
        "content_tree_sha256",
        "blocked_plugin_manifest_sha256",
        "direct_entrypoint_sha256",
    }
    value = doc["source_commitment"]
    if not exact_keys(value, expected_keys, "source commitment", errors):
        return
    if value != {key: source_profile[key] for key in expected_keys}:
        errors.append("source commitment differs from sealed source profile")


def validate_host_contract(doc: dict[str, object], archive_profile: dict[str, object], errors: list[str]) -> None:
    value = doc["sealed_host_contract"]
    expected = archive_profile["sealed_host_contract"]
    expected_keys = {"VCPToolBox_sealed_commit", "VCPToolBox_sealed_tree", "inputs"}
    if not exact_keys(value, expected_keys, "sealed host contract", errors):
        return
    if not is_oid(value["VCPToolBox_sealed_commit"]) or not is_oid(value["VCPToolBox_sealed_tree"]):
        errors.append("sealed host contract OID invalid")
    inputs = value["inputs"]
    if type(inputs) is not list:
        errors.append("sealed host contract inputs must be list")
    else:
        for index, row in enumerate(inputs):
            if not exact_keys(row, {"path", "blob_oid", "sha256"}, f"sealed host input {index}", errors):
                continue
            safe_relative_path(row["path"], f"sealed host input {index}.path", errors)
            if not is_oid(row["blob_oid"]):
                errors.append(f"sealed host input {index}.blob_oid invalid")
            if not is_sha256(row["sha256"]):
                errors.append(f"sealed host input {index}.sha256 invalid")
    if value != expected:
        errors.append("sealed host contract differs from immutable host source")


def validate_source_inventory_and_mapping(doc: dict[str, object], source_profile: dict[str, object], archive_profile: dict[str, object], errors: list[str]) -> None:
    records = doc["source_inventory"]
    if type(records) is not list:
        errors.append("source inventory must be list")
        return
    for index, row in enumerate(records):
        source_record_schema(row, f"source inventory record {index}", errors)
    paths = [row.get("source_path") for row in records if type(row) is dict]
    if len(paths) != len(set(paths)):
        errors.append("source inventory duplicate source paths")
    if records != source_profile["records"]:
        errors.append("source inventory differs from sealed source profile")
    root_prefix = archive_profile["archive_encoding"]["root_prefix"]
    members = doc["archive_member_inventory"]
    if type(members) is not list:
        errors.append("archive member inventory must be list")
        return
    for index, row in enumerate(members):
        archive_member_schema(row, root_prefix, f"archive member record {index}", errors)
    member_paths = [row.get("archive_path") for row in members if type(row) is dict]
    if len(member_paths) != len(set(member_paths)):
        errors.append("archive member inventory duplicate archive paths")
    expected = BUILDER.derive_archive_members(source_profile["records"], root_prefix)
    if members != expected:
        errors.append("archive member inventory does not derive from sealed source inventory")


def validate_manifest_evidence(doc: dict[str, object], source_profile: dict[str, object], archive_profile: dict[str, object], errors: list[str]) -> None:
    value = doc["manifest_evidence"]
    if not exact_keys(value, {"blocked_manifest_b64", "enabled_manifest_paths"}, "manifest evidence", errors):
        return
    blocked = decode_b64(value["blocked_manifest_b64"], "blocked manifest", errors)
    if blocked is not None and sha256_bytes(blocked) != source_profile["blocked_plugin_manifest_sha256"]:
        errors.append("blocked manifest bytes do not match sealed source profile")
    if type(value["enabled_manifest_paths"]) is not list:
        errors.append("enabled manifest paths must be list")
    elif value["enabled_manifest_paths"] != []:
        errors.append("enabled manifest member is forbidden")
    contract = archive_profile["manifest_contract"]
    source_paths = [row["source_path"] for row in source_profile["records"]]
    if contract["enabled_manifest_path"] in source_paths:
        errors.append("sealed source inventory contains enabled manifest")
    if contract["blocked_manifest_path"] not in source_paths:
        errors.append("sealed source inventory lacks blocked manifest")


def validate_entrypoint(doc: dict[str, object], source_profile: dict[str, object], archive_profile: dict[str, object], errors: list[str]) -> None:
    value = doc["entrypoint"]
    if not exact_keys(value, {"source_b64"}, "entrypoint", errors):
        return
    raw = decode_b64(value["source_b64"], "entrypoint source", errors)
    if raw is None:
        return
    if sha256_bytes(raw) != source_profile["direct_entrypoint_sha256"]:
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
    require_matches = list(re.finditer(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)", text))
    modules = [match.group(1) for match in require_matches]
    if modules != [archive_profile["entrypoint_contract"]["native_require_module"]]:
        errors.append("native require module inventory mismatch")
    if any(match.start() < function_index for match in require_matches):
        errors.append("eager native load detected")


def validate_napi_methods(doc: dict[str, object], archive_profile: dict[str, object], errors: list[str]) -> None:
    methods = doc["native_napi_methods"]
    if type(methods) is not list or any(type(item) is not str for item in methods):
        errors.append("native N-API methods must be string list")
        return
    if methods != archive_profile["entrypoint_contract"]["native_NAPI_methods"]:
        errors.append("native N-API method inventory mismatch")


def validate_synthetic_archive(doc: dict[str, object], archive_profile: dict[str, object], errors: list[str]) -> tuple[str | None, int | None]:
    value = doc["synthetic_archive"]
    if not exact_keys(value, SYNTHETIC_ARCHIVE_KEYS, "synthetic archive", errors):
        return None, None
    root_prefix = archive_profile["archive_encoding"]["root_prefix"]
    members = value["members"]
    if type(members) is not list:
        errors.append("synthetic archive members must be list")
        return None, None
    for index, row in enumerate(members):
        synthetic_member_schema(row, root_prefix, f"synthetic member {index}", errors)
    paths = [row.get("source_path") for row in members if type(row) is dict]
    if paths != sorted(paths, key=lambda item: str(item).encode("utf-8")):
        errors.append("synthetic archive member order is not UTF-8 bytewise")
    if len(paths) != len(set(paths)):
        errors.append("synthetic archive duplicate source paths")
    expected_members = BUILDER.derive_synthetic_members(archive_profile)
    if members != expected_members:
        errors.append("synthetic archive members differ from fixed structural inputs")
    projected = [BUILDER.synthetic_member_projection(row) for row in members if type(row) is dict and set(row) == SYNTHETIC_MEMBER_KEYS]
    if not is_sha256(value["member_manifest_sha256"]):
        errors.append("synthetic archive member manifest SHA invalid")
    elif value["member_manifest_sha256"] != sha256_bytes(canonical(projected)):
        errors.append("synthetic archive member manifest SHA mismatch")
    raw = decode_b64(value["archive_bytes_b64"], "synthetic archive bytes", errors)
    if raw is None:
        return None, None
    if not is_sha256(value["archive_sha256"]) or value["archive_sha256"] != sha256_bytes(raw):
        errors.append("synthetic archive SHA mismatch")
    if not is_safe_int(value["archive_byte_length"]) or value["archive_byte_length"] != len(raw):
        errors.append("synthetic archive byte length mismatch")
    try:
        derived_raw = BUILDER.encode_exact_ustar(members)
    except Exception as exc:
        errors.append(f"synthetic archive member encoding invalid: {type(exc).__name__}")
        derived_raw = None
    if derived_raw is not None and raw != derived_raw:
        errors.append("archive bytes are not deterministic encoding")
    try:
        parsed = parse_exact_ustar(raw)
        expected = [
            {key: row[key] for key in ("archive_path", "mode", "uid", "gid", "uname", "gname", "mtime", "byte_length", "sha256")}
            for row in members
        ]
        if parsed != expected:
            errors.append("parsed ustar members differ from structural records")
    except Exception as exc:
        errors.append(f"synthetic archive parse failed: {type(exc).__name__}: {exc}")
    return sha256_bytes(raw), len(raw)


def validate_lifecycles(doc: dict[str, object], archive_profile: dict[str, object], archive_sha256: str | None, archive_size: int | None, errors: list[str]) -> None:
    request = doc["output_request"]
    if exact_keys(request, {"caller_output_path"}, "output request", errors):
        if request["caller_output_path"] is not None:
            errors.append("caller supplied output path forbidden")
    success = doc["success_output_lifecycle"]
    if exact_keys(success, SUCCESS_LIFECYCLE_KEYS, "success output lifecycle", errors):
        if success["events"] != archive_profile["output_lifecycle"]["success_events"]:
            errors.append("success output lifecycle transitions mismatch")
        if success["residue_relative_paths"] != []:
            errors.append("success cleanup residue must be empty")
        returned = success["return"]
        if exact_keys(returned, {"archive_sha256", "archive_byte_length", "archive_bytes_delivery"}, "success output return", errors):
            if returned["archive_sha256"] != archive_sha256 or returned["archive_byte_length"] != archive_size:
                errors.append("success output return not bound to archive bytes")
            if returned["archive_bytes_delivery"] != "IN_MEMORY_ONLY":
                errors.append("success archive delivery must be memory only")
    failure = doc["failure_output_lifecycle"]
    if exact_keys(failure, FAILURE_LIFECYCLE_KEYS, "failure output lifecycle", errors):
        if failure["events"] != archive_profile["output_lifecycle"]["failure_events"]:
            errors.append("failure output lifecycle transitions mismatch")
        if failure["residue_relative_paths"] != []:
            errors.append("failure cleanup residue must be empty")
        returned = failure["return"]
        if exact_keys(returned, {"stable_error_code", "archive_bytes_delivery"}, "failure output return", errors):
            if returned["stable_error_code"] != "SYNTHETIC_FAILURE" or returned["archive_bytes_delivery"] != "NONE":
                errors.append("failure output return exposes archive bytes")


def validate(doc: object) -> list[str]:
    errors: list[str] = []
    if not exact_keys(doc, TOP_KEYS, "root", errors):
        return errors
    if doc["schema_version"] != "agents-os.m0c-plan-structural-witness.v0.1-r2":
        errors.append("schema version mismatch")
    if doc["environment"] != "SYNTHETIC_TEST":
        errors.append("environment must be SYNTHETIC_TEST")
    try:
        archive_profile = yaml.safe_load(ARCHIVE_PROFILE.read_text())
        source_profile = yaml.safe_load(SOURCE_PROFILE.read_text())
    except Exception as exc:
        return [f"stable BLOCK: profile parse {type(exc).__name__}: {exc}"]
    source_profile_valid(source_profile, errors)
    if doc["archive_profile_sha256"] != sha256_file(ARCHIVE_PROFILE):
        errors.append("archive profile SHA mismatch")
    if doc["source_inventory_profile_sha256"] != sha256_file(SOURCE_PROFILE):
        errors.append("source inventory profile SHA mismatch")
    validate_source_commitment(doc, source_profile, errors)
    validate_host_contract(doc, archive_profile, errors)
    validate_manifest_evidence(doc, source_profile, archive_profile, errors)
    # Do this before source/profile equality so an eager-load mutation has an
    # independently observable target-semantic rejection.
    validate_entrypoint(doc, source_profile, archive_profile, errors)
    validate_napi_methods(doc, archive_profile, errors)
    validate_source_inventory_and_mapping(doc, source_profile, archive_profile, errors)
    archive_sha256, archive_size = validate_synthetic_archive(doc, archive_profile, errors)
    validate_lifecycles(doc, archive_profile, archive_sha256, archive_size, errors)
    if doc["terminal_outcome"] != "NOT_ACTIVATED":
        errors.append("terminal outcome must be NOT_ACTIVATED")
    if not is_sha256(doc["root_fingerprint"]):
        errors.append("root fingerprint invalid")
    else:
        unsigned = dict(doc)
        unsigned.pop("root_fingerprint")
        if doc["root_fingerprint"] != sha256_bytes(canonical(unsigned)):
            errors.append("root fingerprint mismatch")
    return errors


def resign(doc: dict[str, object]) -> None:
    unsigned = dict(doc)
    unsigned.pop("root_fingerprint", None)
    doc["root_fingerprint"] = sha256_bytes(canonical(unsigned))


def refresh_synthetic_archive(doc: dict[str, object]) -> None:
    archive = doc["synthetic_archive"]
    raw = BUILDER.encode_exact_ustar(archive["members"])
    archive["member_manifest_sha256"] = sha256_bytes(canonical([BUILDER.synthetic_member_projection(row) for row in archive["members"]]))
    archive["archive_bytes_b64"] = base64.b64encode(raw).decode("ascii")
    archive["archive_sha256"] = sha256_bytes(raw)
    archive["archive_byte_length"] = len(raw)
    returned = doc["success_output_lifecycle"]["return"]
    returned["archive_sha256"] = archive["archive_sha256"]
    returned["archive_byte_length"] = archive["archive_byte_length"]


def refresh_mapping(doc: dict[str, object], archive_profile: dict[str, object]) -> None:
    doc["archive_member_inventory"] = BUILDER.derive_archive_members(doc["source_inventory"], archive_profile["archive_encoding"]["root_prefix"])


def rewrite_first_header_mtime(raw: bytes, value: int) -> bytes:
    changed = bytearray(raw)
    changed[136:148] = BUILDER.octal_field(value, 12)
    changed[148:156] = b" " * 8
    checksum = sum(changed[:148] + b" " * 8 + changed[156:512])
    changed[148:156] = f"{checksum:06o}\0 ".encode("ascii")
    return bytes(changed)


def self_test(doc: dict[str, object]) -> list[str]:
    archive_profile = yaml.safe_load(ARCHIVE_PROFILE.read_text())
    failures: list[str] = []

    def expect(case_id: str, expected: str, mutate) -> None:
        candidate = copy.deepcopy(doc)
        mutate(candidate)
        resign(candidate)
        errors = validate(candidate)
        if not any(expected in error for error in errors):
            failures.append(f"{case_id} missing target semantic rejection: {errors}")

    expect("S01_SOURCE_COMMIT_SUBSTITUTION", "source commitment differs", lambda d: d["source_commitment"].update({"source_commit": "0" * 40}))
    expect("S02_HOST_BLOB_SUBSTITUTION", "sealed host contract differs", lambda d: d["sealed_host_contract"]["inputs"][0].update({"blob_oid": "0" * 40}))

    def add_member(d):
        d["source_inventory"].append({"source_path": "z-extra.txt", "kind": "regular_file", "byte_length": 1, "sha256": "a" * 64})
        refresh_mapping(d, archive_profile)
    expect("S03_MEMBER_ADDITION", "source inventory differs", add_member)

    def remove_member(d):
        d["source_inventory"].pop()
        refresh_mapping(d, archive_profile)
    expect("S04_MEMBER_REMOVAL", "source inventory differs", remove_member)

    def duplicate_member(d):
        d["source_inventory"].append(copy.deepcopy(d["source_inventory"][0]))
        refresh_mapping(d, archive_profile)
    expect("S05_MEMBER_DUPLICATION", "source inventory duplicate", duplicate_member)

    def reorder_mapping(d):
        d["archive_member_inventory"].reverse()
    expect("S06_MEMBER_REORDER", "archive member inventory does not derive", reorder_mapping)

    def replace_member(d):
        d["source_inventory"][0]["sha256"] = "b" * 64
        refresh_mapping(d, archive_profile)
    expect("S07_MEMBER_REPLACEMENT", "source inventory differs", replace_member)

    def traversal_member(d):
        row = d["synthetic_archive"]["members"][0]
        row["source_path"] = "../escape.txt"
        row["archive_path"] = "agents-os-resident/../escape.txt"
        refresh_synthetic_archive(d)
    expect("S08_TRAVERSAL_MEMBER", "traversal", traversal_member)

    def symlink_member(d):
        d["synthetic_archive"]["members"][0]["kind"] = "symlink"
        refresh_synthetic_archive(d)
    expect("S09_SYMLINK_MEMBER", ".kind must be regular_file", symlink_member)

    def absolute_member(d):
        row = d["synthetic_archive"]["members"][0]
        row["source_path"] = "/absolute.txt"
        row["archive_path"] = "/absolute.txt"
        refresh_synthetic_archive(d)
    expect("S10_ABSOLUTE_MEMBER", "unsafe path form", absolute_member)

    def backslash_member(d):
        row = d["synthetic_archive"]["members"][0]
        row["source_path"] = "bad\\\\path.txt"
        row["archive_path"] = "agents-os-resident/bad\\\\path.txt"
        refresh_synthetic_archive(d)
    expect("S11_BACKSLASH_MEMBER", "unsafe path form", backslash_member)

    def eager_load(d):
        raw = base64.b64decode(d["entrypoint"]["source_b64"])
        marker = b"async function processToolCall"
        changed = raw.replace(marker, b"const eager = require('./agents-os-resident.linux-x64-gnu.node');\\n" + marker, 1)
        d["entrypoint"]["source_b64"] = base64.b64encode(changed).decode("ascii")
        for row in d["source_inventory"]:
            if row["source_path"] == "index.js":
                row["byte_length"] = len(changed)
                row["sha256"] = sha256_bytes(changed)
        refresh_mapping(d, archive_profile)
    expect("S12_EAGER_NATIVE_LOAD", "eager native load detected", eager_load)

    expect("S13_NAPI_EXPANSION", "native N-API method inventory mismatch", lambda d: d["native_napi_methods"].append("start_runtime"))
    expect("S14_ENABLED_MANIFEST", "enabled manifest member is forbidden", lambda d: d["manifest_evidence"]["enabled_manifest_paths"].append("plugin-manifest.json"))

    def archive_metadata_drift(d):
        raw = base64.b64decode(d["synthetic_archive"]["archive_bytes_b64"])
        changed = rewrite_first_header_mtime(raw, 1)
        archive = d["synthetic_archive"]
        archive["archive_bytes_b64"] = base64.b64encode(changed).decode("ascii")
        archive["archive_sha256"] = sha256_bytes(changed)
        archive["archive_byte_length"] = len(changed)
        d["success_output_lifecycle"]["return"]["archive_sha256"] = archive["archive_sha256"]
        d["success_output_lifecycle"]["return"]["archive_byte_length"] = archive["archive_byte_length"]
    expect("S15_ARCHIVE_METADATA_DRIFT", "archive bytes are not deterministic encoding", archive_metadata_drift)

    expect("S16_CALLER_OUTPUT_PATH", "caller supplied output path forbidden", lambda d: d["output_request"].update({"caller_output_path": "/tmp/output.tar"}))
    expect("S17_SUCCESS_RESIDUE", "success cleanup residue must be empty", lambda d: d["success_output_lifecycle"]["residue_relative_paths"].append("archive.tar"))
    expect("S18_FAILURE_DELIVERY", "failure output return exposes archive bytes", lambda d: d["failure_output_lifecycle"]["return"].update({"archive_bytes_delivery": "IN_MEMORY_ONLY"}))
    expect("S19_UNKNOWN_FIELD", "root field inventory mismatch", lambda d: d.update({"unknown": 1}))
    expect("S20_BOOLEAN_TYPE", "environment must be SYNTHETIC_TEST", lambda d: d.update({"environment": True}))
    try:
        json.loads('{"a":1,"a":2}', object_pairs_hook=strict_pairs)
        failures.append("S21_DUPLICATE_JSON_KEY accepted")
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
    print(json.dumps({"result": "PASS", "structural_negative_mutations": 20 if args.self_test else 0, "parser_probes": 1 if args.self_test else 0, "terminal_outcome": "NOT_ACTIVATED"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
