#!/usr/bin/env python3
"""Create a deterministic, no-Git Phase 5D M0-D Plan R1 review archive."""

from __future__ import annotations

import hashlib
import json
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

import yaml


MANIFEST_PATH = Path(
    "control-plane/registry/reports/"
    "2026-07-23-agents-os-phase-5d-m0d-plan-r1-atomic-independent-review-package-v0.1.manifest.yaml"
)
REPORT_PATH = Path(
    "control-plane/registry/reports/"
    "2026-07-23-agents-os-phase-5d-m0d-plan-r1-atomic-independent-review-package-v0.1.md"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_archive_name(path: str) -> str:
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in path:
        raise ValueError(f"unsafe archive path: {path}")
    return str(PurePosixPath("payload") / candidate)


def add_file(entries: dict[str, bytes], arcname: str, source: Path) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"not a regular source file: {source}")
    if arcname in entries:
        raise ValueError(f"duplicate archive path: {arcname}")
    entries[arcname] = source.read_bytes()


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} OUTPUT_ZIP", file=sys.stderr)
        return 2
    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = yaml.safe_load(manifest_bytes)
    entries: dict[str, bytes] = {"MANIFEST.yaml": manifest_bytes, "REPORT.md": REPORT_PATH.read_bytes()}
    groups = ("subjects", "authority_inputs", "author_evidence")
    archive_map: list[dict[str, str]] = []
    for group in groups:
        for item in manifest.get(group, []):
            source = Path(item["path"])
            data = source.read_bytes()
            actual = sha256(data)
            if actual != item["sha256"]:
                raise ValueError(f"hash mismatch for {source}: {actual} != {item['sha256']}")
            arcname = safe_archive_name(item["path"])
            add_file(entries, arcname, source)
            archive_map.append({"archive_path": arcname, "sha256": actual, "source_path": item["path"]})
    archive_map_bytes = (json.dumps(archive_map, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("ascii")
    entries["ARCHIVE_MAP.json"] = archive_map_bytes
    checksums = "".join(f"{sha256(entries[name])}  {name}\n" for name in sorted(entries))
    entries["CHECKSUMS.sha256"] = checksums.encode("ascii")
    output = Path(argv[1])
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, entries[name])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
