#!/usr/bin/env python3
"""Shared deterministic structural proof helpers for Phase 5C M0-C Plan R3.

This module is planning-only evidence.  Its lifecycle exercises use a newly
created, owned synthetic temporary directory and remove it before returning.
They neither assemble an installable plugin nor touch VCPToolBox, a database,
network, runtime, provider, private Memory, or host process.
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

import yaml


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r3.yaml"
SOURCE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-sealed-source-inventory-v0.1-r2.yaml"
ENTRYPOINT = ROOT / "extensions/agents-os-resident/index.js"
BLOCKED_MANIFEST = ROOT / "extensions/agents-os-resident/plugin-manifest.json.block"

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


def load_profiles() -> tuple[dict[str, Any], dict[str, Any]]:
    archive_profile = yaml.safe_load(ARCHIVE_PROFILE.read_text(encoding="utf-8"))
    source_profile = yaml.safe_load(SOURCE_PROFILE.read_text(encoding="utf-8"))
    if not isinstance(archive_profile, dict) or not isinstance(source_profile, dict):
        raise ValueError("profile root must be mapping")
    return archive_profile, source_profile


def member_manifest_projection(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row[key] for key in MEMBER_MANIFEST_FIELDS}


def derive_archive_members(source_records: list[dict[str, Any]], root_prefix: str) -> list[dict[str, Any]]:
    rows = [
        {
            "source_path": row["source_path"],
            "archive_path": root_prefix + str(row["source_path"]),
            "kind": row["kind"],
            "byte_length": row["byte_length"],
            "sha256": row["sha256"],
        }
        for row in source_records
    ]
    return sorted(rows, key=lambda row: str(row["source_path"]).encode("utf-8"))


def derive_synthetic_members(profile: dict[str, Any]) -> list[dict[str, Any]]:
    encoding = profile["archive_encoding"]
    header = encoding["header"]
    root_prefix = str(encoding["root_prefix"])
    rows: list[dict[str, Any]] = []
    for item in profile["synthetic_archive_exercise"]["members"]:
        content = str(item["content_utf8"]).encode("utf-8")
        rows.append(
            {
                "source_path": item["source_path"],
                "archive_path": root_prefix + str(item["source_path"]),
                "kind": "regular_file",
                "mode": int(str(header["mode_octal"]), 8),
                "uid": header["uid"],
                "gid": header["gid"],
                "uname": header["uname"],
                "gname": header["gname"],
                "mtime": header["mtime_unix_seconds"],
                "content_b64": b64(content),
                "byte_length": len(content),
                "sha256": sha256_bytes(content),
            }
        )
    return sorted(rows, key=lambda row: str(row["source_path"]).encode("utf-8"))


def octal_field(value: int, width: int) -> bytes:
    text = f"{value:0{width - 1}o}".encode("ascii")
    if len(text) != width - 1:
        raise ValueError("ustar numeric field overflow")
    return text + b"\0"


def ustar_header(name: str, size: int, *, mode: int, uid: int, gid: int, uname: str, gname: str, mtime: int) -> bytes:
    name_bytes = name.encode("utf-8")
    uname_bytes = uname.encode("utf-8")
    gname_bytes = gname.encode("utf-8")
    if not name_bytes or len(name_bytes) > 100 or len(uname_bytes) > 31 or len(gname_bytes) > 31:
        raise ValueError("unsupported ustar name")
    header = bytearray(512)
    header[0:len(name_bytes)] = name_bytes
    header[100:108] = octal_field(mode, 8)
    header[108:116] = octal_field(uid, 8)
    header[116:124] = octal_field(gid, 8)
    header[124:136] = octal_field(size, 12)
    header[136:148] = octal_field(mtime, 12)
    header[148:156] = b" " * 8
    header[156:157] = b"0"
    header[257:263] = b"ustar\0"
    header[263:265] = b"00"
    header[265:265 + len(uname_bytes)] = uname_bytes
    header[297:297 + len(gname_bytes)] = gname_bytes
    checksum = sum(header)
    header[148:156] = f"{checksum:06o}\0 ".encode("ascii")
    return bytes(header)


def encode_exact_ustar(members: list[dict[str, Any]]) -> bytes:
    stream = io.BytesIO()
    for row in members:
        content = base64.b64decode(str(row["content_b64"]), validate=True)
        stream.write(
            ustar_header(
                str(row["archive_path"]),
                len(content),
                mode=int(row["mode"]),
                uid=int(row["uid"]),
                gid=int(row["gid"]),
                uname=str(row["uname"]),
                gname=str(row["gname"]),
                mtime=int(row["mtime"]),
            )
        )
        stream.write(content)
        padding = (-len(content)) % 512
        if padding:
            stream.write(b"\0" * padding)
    stream.write(b"\0" * 1024)
    return stream.getvalue()


def parse_octal(field: bytes) -> int:
    text = field.rstrip(b"\0 ")
    if not text or any(char not in b"01234567" for char in text):
        raise ValueError("invalid octal field")
    return int(text, 8)


def parse_exact_ustar(raw: bytes) -> list[dict[str, Any]]:
    if len(raw) < 1024 or len(raw) % 512 != 0 or not raw.endswith(b"\0" * 1024):
        raise ValueError("ustar final zero-block contract mismatch")
    rows: list[dict[str, Any]] = []
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


def source_commitment(source_profile: dict[str, Any]) -> dict[str, Any]:
    return {
        key: source_profile[key]
        for key in (
            "source_root",
            "source_commit",
            "package_manifest_sha256",
            "content_tree_sha256",
            "blocked_plugin_manifest_sha256",
            "direct_entrypoint_sha256",
        )
    }


def normalized_inventory(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() or path.is_symlink()
    )


def _new_owned_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="agents-os-phase5c-m0c-r3-"))
    if normalized_inventory(root) != []:
        shutil.rmtree(root, ignore_errors=True)
        raise RuntimeError("new synthetic temp root was not empty")
    return root


def _remove_owned_root(root: Path) -> tuple[bool, list[str]]:
    shutil.rmtree(root)
    return root.exists(), normalized_inventory(root)


def run_success_lifecycle(profile: dict[str, Any], archive_bytes: bytes) -> dict[str, Any]:
    root = _new_owned_root()
    try:
        initial = normalized_inventory(root)
        archive_path = root / "archive.tar"
        archive_path.write_bytes(archive_bytes)
        before_cleanup = normalized_inventory(root)
        returned = archive_path.read_bytes()
        if returned != archive_bytes:
            raise RuntimeError("actual synthetic return bytes mismatch")
        root_exists, residue = _remove_owned_root(root)
        if root_exists or residue:
            raise RuntimeError("owned synthetic success root residue detected")
        return {
            "events": profile["output_lifecycle"]["success_events"],
            "initial_owned_root_inventory": initial,
            "before_cleanup_inventory": before_cleanup,
            "post_cleanup_owned_root_exists": root_exists,
            "post_cleanup_residue_relative_paths": residue,
            "return": {
                "archive_sha256": sha256_bytes(returned),
                "archive_byte_length": len(returned),
                "archive_bytes_in_memory_b64": b64(returned),
            },
        }
    finally:
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)


def run_failure_lifecycle(profile: dict[str, Any]) -> dict[str, Any]:
    root = _new_owned_root()
    try:
        initial = normalized_inventory(root)
        try:
            raise RuntimeError("SYNTHETIC_FAILURE")
        except RuntimeError as exc:
            if str(exc) != "SYNTHETIC_FAILURE":
                raise
        before_cleanup = normalized_inventory(root)
        root_exists, residue = _remove_owned_root(root)
        if root_exists or residue:
            raise RuntimeError("owned synthetic failure root residue detected")
        return {
            "events": profile["output_lifecycle"]["failure_events"],
            "initial_owned_root_inventory": initial,
            "before_cleanup_inventory": before_cleanup,
            "post_cleanup_owned_root_exists": root_exists,
            "post_cleanup_residue_relative_paths": residue,
            "return": {"stable_error_code": "SYNTHETIC_FAILURE"},
        }
    finally:
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)


def run_residue_probe(archive_bytes: bytes) -> dict[str, Any]:
    root = _new_owned_root()
    try:
        (root / "archive.tar").write_bytes(archive_bytes)
        observed = normalized_inventory(root)
        if observed != ["archive.tar"]:
            raise RuntimeError("synthetic residue probe did not observe archive residue")
        root_exists, post_cleanup = _remove_owned_root(root)
        if root_exists or post_cleanup:
            raise RuntimeError("synthetic residue probe cleanup failed")
        return {
            "probe_result": "CLEANUP_RESIDUE_DETECTED",
            "observed_before_cleanup_residue_relative_paths": observed,
            "post_cleanup_owned_root_exists": root_exists,
            "post_cleanup_residue_relative_paths": post_cleanup,
            "return": {"stable_error_code": "SYNTHETIC_CLEANUP_FAILURE"},
        }
    finally:
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)


def run_wrong_return_probe(archive_bytes: bytes) -> dict[str, Any]:
    root = _new_owned_root()
    try:
        archive_path = root / "archive.tar"
        archive_path.write_bytes(archive_bytes)
        actual = archive_path.read_bytes()
        wrong = actual[:-1]
        if wrong == archive_bytes:
            raise RuntimeError("synthetic wrong-return probe did not diverge")
        root_exists, residue = _remove_owned_root(root)
        if root_exists or residue:
            raise RuntimeError("synthetic wrong-return probe cleanup failed")
        return {
            "probe_result": "RETURN_BYTES_MISMATCH_DETECTED",
            "expected_archive_sha256": sha256_bytes(archive_bytes),
            "observed_returned_archive_sha256": sha256_bytes(wrong),
            "observed_returned_archive_byte_length": len(wrong),
            "observed_returned_archive_bytes_b64": b64(wrong),
            "post_cleanup_owned_root_exists": root_exists,
            "post_cleanup_residue_relative_paths": residue,
            "return": {"stable_error_code": "SYNTHETIC_RETURN_BYTES_MISMATCH"},
        }
    finally:
        if root.exists():
            shutil.rmtree(root, ignore_errors=True)


def run_lifecycle_proofs(profile: dict[str, Any], archive_bytes: bytes) -> dict[str, Any]:
    return {
        "success": run_success_lifecycle(profile, archive_bytes),
        "failure": run_failure_lifecycle(profile),
        "residue_probe": run_residue_probe(archive_bytes),
        "wrong_return_probe": run_wrong_return_probe(archive_bytes),
    }
