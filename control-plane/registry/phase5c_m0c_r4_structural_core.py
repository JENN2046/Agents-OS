#!/usr/bin/env python3
"""Exact synthetic ustar and owned-temp-root helpers for Phase 5C M0-C R4.

This module is a planning-only proof harness. It writes only inside newly
created disposable temporary directories, performs no plugin packaging or
activation, and never accesses VCPToolBox, a runtime, database, provider,
private Memory, sensor, or effect boundary.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
from typing import Any
import unicodedata

import yaml


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r4.yaml"
ZERO = bytes([0])
BLOCK_SIZE = 512
MEMBER_MANIFEST_FIELDS = (
    "source_path",
    "archive_path",
    "kind",
    "mode",
    "uid",
    "gid",
    "uname",
    "gname",
    "mtime",
    "byte_length",
    "sha256",
)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def load_profile() -> dict[str, Any]:
    profile = yaml.safe_load(ARCHIVE_PROFILE.read_text(encoding="utf-8"))
    if type(profile) is not dict:
        raise ValueError("R4 archive profile root must be mapping")
    return profile


def member_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row[key] for key in MEMBER_MANIFEST_FIELDS}


def safe_path(value: object) -> bool:
    return (
        type(value) is str
        and bool(value)
        and unicodedata.normalize("NFC", value) == value
        and "\\" not in value
        and not value.startswith("/")
        and all(part not in {"", ".", ".."} for part in value.split("/"))
    )


def derive_synthetic_members(profile: dict[str, Any]) -> list[dict[str, Any]]:
    encoding = profile["archive_encoding"]
    normal = encoding["header_value_normalization"]
    root_prefix = encoding["root_prefix"]
    rows: list[dict[str, Any]] = []
    for item in profile["synthetic_archive_exercise"]["members"]:
        source_path = item["source_path"]
        content = item["content_utf8"].encode("utf-8")
        rows.append(
            {
                "source_path": source_path,
                "archive_path": root_prefix + source_path,
                "kind": "regular_file",
                "mode": int(normal["mode_octal"], 8),
                "uid": normal["uid"],
                "gid": normal["gid"],
                "uname": normal["uname"],
                "gname": normal["gname"],
                "mtime": normal["mtime_unix_seconds"],
                "content_b64": b64(content),
                "byte_length": len(content),
                "sha256": sha256_bytes(content),
            }
        )
    return sorted(rows, key=lambda row: row["source_path"].encode("utf-8"))


def _field(contract: dict[str, Any], name: str) -> dict[str, Any]:
    value = contract[name]
    if type(value) is not dict:
        raise ValueError(f"ustar profile field {name} malformed")
    return value


def _slice(field: dict[str, Any]) -> slice:
    offset = field["offset"]
    width = field["width"]
    if type(offset) is not int or type(width) is not int or offset < 0 or width <= 0:
        raise ValueError("ustar field offset or width invalid")
    return slice(offset, offset + width)


def _string_field(value: str, width: int) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) >= width:
        raise ValueError("ustar string field does not leave required NUL terminator")
    return raw + ZERO + ZERO * (width - len(raw) - 1)


def _octal_field(value: int, width: int) -> bytes:
    if type(value) is not int or value < 0:
        raise ValueError("ustar numeric value invalid")
    digits = f"{value:o}".encode("ascii")
    if len(digits) > width - 1:
        raise ValueError("ustar numeric field overflow")
    return b"0" * (width - 1 - len(digits)) + digits + ZERO


def _hex_field(field: dict[str, Any], width: int) -> bytes:
    value = field.get("hex")
    if type(value) is not str or len(value) != width * 2:
        raise ValueError("ustar exact hex field malformed")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError("ustar exact hex field invalid") from exc
    if len(raw) != width:
        raise ValueError("ustar exact hex field width mismatch")
    return raw


def encode_header(profile: dict[str, Any], row: dict[str, Any]) -> bytes:
    encoding = profile["archive_encoding"]
    contract = encoding["header_byte_contract"]
    if encoding["block_size_bytes"] != BLOCK_SIZE:
        raise ValueError("unsupported R4 ustar block size")
    header = bytearray(BLOCK_SIZE)
    for name, value_key in (
        ("filename", "archive_path"),
        ("uname", "uname"),
        ("gname", "gname"),
    ):
        field = _field(contract, name)
        selected = row[value_key]
        if field.get("encoding") != "UTF8_NUL_THEN_ZERO_FILL" or field.get("value_source") != value_key:
            raise ValueError(f"ustar {name} profile contract mismatch")
        header[_slice(field)] = _string_field(selected, field["width"])
    for name, value_key in (
        ("mode", "mode"),
        ("uid", "uid"),
        ("gid", "gid"),
        ("size", "byte_length"),
        ("mtime", "mtime"),
    ):
        field = _field(contract, name)
        if field.get("encoding") != "ZERO_PADDED_OCTAL_THEN_NUL" or field.get("value_source") != value_key:
            raise ValueError(f"ustar {name} profile contract mismatch")
        header[_slice(field)] = _octal_field(row[value_key], field["width"])
    for name in ("typeflag", "magic", "version"):
        field = _field(contract, name)
        if field.get("encoding") != "EXACT_HEX":
            raise ValueError(f"ustar {name} profile contract mismatch")
        header[_slice(field)] = _hex_field(field, field["width"])
    for name in ("linkname", "devmajor", "devminor", "prefix", "trailing_unused"):
        field = _field(contract, name)
        if field.get("encoding") != "ALL_ZERO_BYTES":
            raise ValueError(f"ustar {name} profile contract mismatch")
        header[_slice(field)] = ZERO * field["width"]
    checksum = _field(contract, "checksum")
    if (
        checksum.get("preimage_fill_hex") != "20"
        or checksum.get("encoding") != "SIX_OCTAL_DIGITS_NUL_ASCII_SPACE"
        or checksum.get("unsigned_byte_sum") is not True
        or checksum["width"] != 8
    ):
        raise ValueError("ustar checksum profile contract mismatch")
    header[_slice(checksum)] = b" " * checksum["width"]
    total = sum(header)
    text = f"{total:06o}".encode("ascii")
    if len(text) != 6:
        raise ValueError("ustar checksum overflow")
    header[_slice(checksum)] = text + ZERO + b" "
    return bytes(header)


def encode_exact_ustar(profile: dict[str, Any], members: list[dict[str, Any]]) -> bytes:
    encoding = profile["archive_encoding"]
    padding = encoding["body_padding"]
    ending = encoding["end_of_archive"]
    if padding != {"alignment_bytes": 512, "fill_hex": "00"}:
        raise ValueError("ustar body padding profile mismatch")
    if ending != {"zero_block_count": 2, "block_size_bytes": 512}:
        raise ValueError("ustar terminal profile mismatch")
    stream = io.BytesIO()
    for row in members:
        content = base64.b64decode(row["content_b64"], validate=True)
        if len(content) != row["byte_length"] or sha256_bytes(content) != row["sha256"]:
            raise ValueError("synthetic member content commitment mismatch")
        stream.write(encode_header(profile, row))
        stream.write(content)
        member_padding = (-len(content)) % BLOCK_SIZE
        stream.write(ZERO * member_padding)
    stream.write(ZERO * (ending["zero_block_count"] * ending["block_size_bytes"]))
    return stream.getvalue()


def verify_exact_ustar(profile: dict[str, Any], members: list[dict[str, Any]], raw: bytes) -> None:
    expected = encode_exact_ustar(profile, members)
    if raw != expected:
        raise ValueError("archive bytes violate exact R4 ustar byte contract")
    if len(raw) % BLOCK_SIZE != 0 or not raw.endswith(ZERO * 1024):
        raise ValueError("archive terminal blocks violate exact R4 ustar byte contract")


def normalized_inventory(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    )


def _new_owned_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="agents-os-phase5c-m0c-r4-"))
    if normalized_inventory(root):
        shutil.rmtree(root, ignore_errors=True)
        raise RuntimeError("new owned synthetic temp root was not empty")
    return root


def _finalize_owned_root(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    if root.exists():
        raise RuntimeError("owned synthetic temp root finalizer failed")


def run_success_lifecycle(profile: dict[str, Any], archive_bytes: bytes) -> dict[str, Any]:
    root = _new_owned_root()
    proof: dict[str, Any] | None = None
    try:
        archive_path = root / "archive.tar"
        archive_path.write_bytes(archive_bytes)
        returned = archive_path.read_bytes()
        if returned != archive_bytes:
            raise RuntimeError("synthetic success returned bytes mismatch")
        _finalize_owned_root(root)
        proof = {
            "initial_owned_root_inventory": [],
            "before_cleanup_inventory": ["archive.tar"],
            "post_cleanup_owned_root_exists": False,
            "post_cleanup_residue_relative_paths": [],
            "return": {
                "archive_sha256": sha256_bytes(returned),
                "archive_byte_length": len(returned),
                "archive_bytes_in_memory_b64": b64(returned),
            },
        }
    finally:
        if root.exists():
            _finalize_owned_root(root)
    assert proof is not None
    return proof


def run_failure_lifecycle() -> dict[str, Any]:
    root = _new_owned_root()
    proof: dict[str, Any] | None = None
    try:
        _finalize_owned_root(root)
        proof = {
            "initial_owned_root_inventory": [],
            "before_cleanup_inventory": [],
            "post_cleanup_owned_root_exists": False,
            "post_cleanup_residue_relative_paths": [],
            "return": {"stable_error_code": "SYNTHETIC_FAILURE"},
        }
    finally:
        if root.exists():
            _finalize_owned_root(root)
    assert proof is not None
    return proof


def run_cleanup_fault_probe(profile: dict[str, Any], archive_bytes: bytes) -> dict[str, Any]:
    contract = profile["output_lifecycle"]["cleanup_fault_contract"]
    root = _new_owned_root()
    proof: dict[str, Any] | None = None
    try:
        archive_path = root / "archive.tar"
        archive_path.write_bytes(archive_bytes)
        before_attempt = normalized_inventory(root)
        attempt_error = None
        try:
            root.rmdir()
        except OSError:
            attempt_error = "DIRECTORY_NOT_EMPTY"
        if attempt_error != "DIRECTORY_NOT_EMPTY":
            raise RuntimeError("fault injection did not produce incomplete cleanup")
        post_exists = root.exists()
        post_residue = normalized_inventory(root)
        if post_exists is not True or post_residue != ["archive.tar"]:
            raise RuntimeError("post-cleanup residue observation mismatch")
        proof = {
            "fault_injection": contract["fault_injection"],
            "before_cleanup_attempt_inventory": before_attempt,
            "cleanup_attempt_result": attempt_error,
            "post_cleanup_owned_root_exists": post_exists,
            "post_cleanup_residue_relative_paths": post_residue,
            "probe_result": contract["required_result"],
            "return": contract["required_fail_closed_return"],
            "finalizer_runs_only_after_post_cleanup_observation": True,
        }
    finally:
        if root.exists():
            _finalize_owned_root(root)
    assert proof is not None
    return proof


def run_wrong_return_probe(archive_bytes: bytes) -> dict[str, Any]:
    root = _new_owned_root()
    proof: dict[str, Any] | None = None
    try:
        archive_path = root / "archive.tar"
        archive_path.write_bytes(archive_bytes)
        wrong = archive_path.read_bytes()[:-1]
        if wrong == archive_bytes:
            raise RuntimeError("wrong-return probe did not diverge")
        _finalize_owned_root(root)
        proof = {
            "probe_result": "RETURN_BYTES_MISMATCH_DETECTED",
            "expected_archive_sha256": sha256_bytes(archive_bytes),
            "observed_returned_archive_sha256": sha256_bytes(wrong),
            "observed_returned_archive_byte_length": len(wrong),
            "observed_returned_archive_bytes_b64": b64(wrong),
            "post_cleanup_owned_root_exists": False,
            "post_cleanup_residue_relative_paths": [],
            "return": {"stable_error_code": "SYNTHETIC_RETURN_BYTES_MISMATCH"},
        }
    finally:
        if root.exists():
            _finalize_owned_root(root)
    assert proof is not None
    return proof


def run_lifecycle_proofs(profile: dict[str, Any], archive_bytes: bytes) -> dict[str, Any]:
    return {
        "success": run_success_lifecycle(profile, archive_bytes),
        "failure": run_failure_lifecycle(),
        "cleanup_fault_probe": run_cleanup_fault_probe(profile, archive_bytes),
        "wrong_return_probe": run_wrong_return_probe(archive_bytes),
    }
