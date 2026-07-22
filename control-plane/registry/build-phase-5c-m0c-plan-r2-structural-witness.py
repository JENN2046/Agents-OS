#!/usr/bin/env python3
"""Build the deterministic, structural-only Phase 5C M0-C R2 witness.

This program produces planning evidence only.  It neither assembles an
extension package nor opens a VCPToolBox worktree, database, network, runtime,
provider, or host process.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-exact-archive-output-lifecycle-profile-v0.1-r2.yaml"
SOURCE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-sealed-source-inventory-v0.1-r2.yaml"
ENTRYPOINT = ROOT / "extensions/agents-os-resident/index.js"
BLOCKED_MANIFEST = ROOT / "extensions/agents-os-resident/plugin-manifest.json.block"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def archive_member_projection(row: dict[str, object]) -> dict[str, object]:
    return {key: row[key] for key in ("source_path", "archive_path", "kind", "byte_length", "sha256")}


def synthetic_member_projection(row: dict[str, object]) -> dict[str, object]:
    return {key: row[key] for key in ("source_path", "archive_path", "kind", "mode", "uid", "gid", "uname", "gname", "mtime", "byte_length", "sha256")}


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


def encode_exact_ustar(members: list[dict[str, object]]) -> bytes:
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


def derive_archive_members(source_records: list[dict[str, object]], root_prefix: str) -> list[dict[str, object]]:
    rows = []
    for row in source_records:
        rows.append(
            {
                "source_path": row["source_path"],
                "archive_path": root_prefix + str(row["source_path"]),
                "kind": row["kind"],
                "byte_length": row["byte_length"],
                "sha256": row["sha256"],
            }
        )
    return sorted(rows, key=lambda row: str(row["source_path"]).encode("utf-8"))


def derive_synthetic_members(profile: dict[str, object]) -> list[dict[str, object]]:
    encoding = profile["archive_encoding"]
    header = encoding["header"]
    root_prefix = str(encoding["root_prefix"])
    rows = []
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


def load_profiles() -> tuple[dict[str, object], dict[str, object]]:
    return yaml.safe_load(ARCHIVE_PROFILE.read_text()), yaml.safe_load(SOURCE_PROFILE.read_text())


def build() -> dict[str, object]:
    archive_profile, source_profile = load_profiles()
    members = derive_synthetic_members(archive_profile)
    archive_bytes = encode_exact_ustar(members)
    archive_sha256 = sha256_bytes(archive_bytes)
    source_commitment = {
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
    success_events = archive_profile["output_lifecycle"]["success_events"]
    failure_events = archive_profile["output_lifecycle"]["failure_events"]
    body: dict[str, object] = {
        "schema_version": "agents-os.m0c-plan-structural-witness.v0.1-r2",
        "environment": "SYNTHETIC_TEST",
        "archive_profile_sha256": sha256_file(ARCHIVE_PROFILE),
        "source_inventory_profile_sha256": sha256_file(SOURCE_PROFILE),
        "source_commitment": source_commitment,
        "sealed_host_contract": archive_profile["sealed_host_contract"],
        "source_inventory": source_profile["records"],
        "archive_member_inventory": derive_archive_members(source_profile["records"], archive_profile["archive_encoding"]["root_prefix"]),
        "manifest_evidence": {"blocked_manifest_b64": b64(BLOCKED_MANIFEST.read_bytes()), "enabled_manifest_paths": []},
        "entrypoint": {"source_b64": b64(ENTRYPOINT.read_bytes())},
        "native_napi_methods": archive_profile["entrypoint_contract"]["native_NAPI_methods"],
        "synthetic_archive": {
            "members": members,
            "member_manifest_sha256": sha256_bytes(canonical([synthetic_member_projection(row) for row in members])),
            "archive_bytes_b64": b64(archive_bytes),
            "archive_sha256": archive_sha256,
            "archive_byte_length": len(archive_bytes),
        },
        "output_request": {"caller_output_path": None},
        "success_output_lifecycle": {
            "events": success_events,
            "residue_relative_paths": [],
            "return": {
                "archive_sha256": archive_sha256,
                "archive_byte_length": len(archive_bytes),
                "archive_bytes_delivery": "IN_MEMORY_ONLY",
            },
        },
        "failure_output_lifecycle": {
            "events": failure_events,
            "residue_relative_paths": [],
            "return": {"stable_error_code": "SYNTHETIC_FAILURE", "archive_bytes_delivery": "NONE"},
        },
        "terminal_outcome": "NOT_ACTIVATED",
    }
    body["root_fingerprint"] = sha256_bytes(canonical(body))
    return body


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    payload = canonical(build()) + b"\n"
    if output:
        output.write_bytes(payload)
    else:
        sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
