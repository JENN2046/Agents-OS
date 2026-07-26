#!/usr/bin/env python3
"""Build a deterministic, protected-path-safe R2 review ZIP from JSON-YAML."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile


WORKSPACE = Path("/home/jenn/AGENTS_OS_Workspace").resolve()
FIXED_ZIP_TIME = (2026, 7, 25, 0, 0, 0)
PROTECTED_PARTS = {"state-private", "secrets", "credentials", "tokens", "cookies"}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def safe_relative(value: str) -> PurePosixPath:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("unsafe path")
    item = PurePosixPath(value)
    if item.is_absolute() or ".." in item.parts or any(part in PROTECTED_PARTS for part in item.parts):
        raise ValueError("unsafe path")
    if any(part == ".env" or part.startswith(".env.") or part == "config.env" for part in item.parts):
        raise ValueError("unsafe path")
    return item


def workspace_file(value: str) -> Path:
    relative = safe_relative(value)
    candidate = WORKSPACE.joinpath(*relative.parts)
    resolved = candidate.resolve(strict=True)
    if WORKSPACE not in (resolved, *resolved.parents):
        raise ValueError("workspace escape")
    info = resolved.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ValueError("not regular")
    return resolved


def load_manifest(path: Path) -> dict:
    document = json.loads(path.read_text(encoding="utf-8"))
    if set(document) != {
        "schema_version", "review_unit", "atomic", "partial_review",
        "subjects", "authority_inputs", "author_evidence", "fixed_commands",
    }:
        raise ValueError("manifest keys")
    if document["atomic"] is not True or document["partial_review"] != "forbidden":
        raise ValueError("atomicity")
    for field in ("subjects", "authority_inputs", "author_evidence"):
        if type(document[field]) is not list:
            raise ValueError("manifest list")
    return document


def records(document: dict) -> list[dict]:
    result: list[dict] = []
    for group in ("subjects", "authority_inputs", "author_evidence"):
        for item in document[group]:
            if set(item) != {"id", "path", "sha256"}:
                raise ValueError("record keys")
            if type(item["id"]) is not str or type(item["path"]) is not str or type(item["sha256"]) is not str:
                raise ValueError("record type")
            source = workspace_file(item["path"])
            if digest(source) != item["sha256"]:
                raise ValueError("record hash")
            result.append(item)
    if len({item["path"] for item in result}) != len(result):
        raise ValueError("duplicate path")
    return result


def write_entry(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = (0o100644 & 0xFFFF) << 16
    archive.writestr(info, content)


def build(manifest_path: Path, output_path: Path) -> None:
    manifest_path = manifest_path.resolve(strict=True)
    if manifest_path.parent != (WORKSPACE / "control-plane/registry/reports"):
        raise ValueError("manifest location")
    document = load_manifest(manifest_path)
    checked = records(document)
    if output_path.exists() or output_path.is_symlink():
        raise ValueError("output exists")
    archive_map: list[dict] = []
    with zipfile.ZipFile(output_path, "x", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
        manifest_bytes = manifest_path.read_bytes()
        write_entry(archive, "MANIFEST.yaml", manifest_bytes)
        for item in checked:
            payload_name = f"payload/{safe_relative(item['path']).as_posix()}"
            source = workspace_file(item["path"])
            content = source.read_bytes()
            write_entry(archive, payload_name, content)
            archive_map.append({"archive_path": payload_name, "path": item["path"], "sha256": digest(source)})
        archive_map_bytes = (json.dumps(archive_map, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
        write_entry(archive, "ARCHIVE_MAP.json", archive_map_bytes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        build(args.manifest, args.output)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise SystemExit(f"BLOCKED:{type(exc).__name__}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
