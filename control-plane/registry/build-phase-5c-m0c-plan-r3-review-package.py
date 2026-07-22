#!/usr/bin/env python3
"""Build a deterministic, self-contained Phase 5C M0-C Plan R3 review ZIP.

The archive builder only reads manifest-declared workspace files and writes the
requested local review archive. It does not access VCPToolBox, runtime,
database, provider, private Memory, sensing, or external effects.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

import yaml


ROOT = Path(__file__).resolve().parents[2]
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_relative(value: object) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("archive path must be nonempty forward-slash relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in value.split("/")):
        raise ValueError("archive path traversal or absolute form")
    return value


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def read_manifest(path: Path) -> dict[str, object]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(data) is not dict:
        raise ValueError("manifest root must be mapping")
    return data


def declared_rows(manifest: dict[str, object]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    sections = (
        ("subjects", manifest["review_unit"]["subjects"]),
        ("authority_inputs", manifest["authority_inputs"]),
        ("author_evidence", manifest["author_evidence"]),
    )
    for section, values in sections:
        if type(values) is not list:
            raise ValueError(f"{section} must be list")
        for index, row in enumerate(values):
            if type(row) is not dict:
                raise ValueError(f"{section}[{index}] must be mapping")
            path = safe_relative(row.get("path"))
            digest = row.get("sha256")
            role = row.get("role")
            if type(role) is not str or not role or type(digest) is not str or len(digest) != 64:
                raise ValueError(f"{section}[{index}] role/path/hash malformed")
            rows.append({"section": section, "role": role, "source_path": path, "archive_path": path, "sha256": digest})
    paths = [row["source_path"] for row in rows]
    if len(paths) != len(set(paths)):
        raise ValueError("manifest declared duplicate input path")
    return rows


def make_zip_entry(name: str, content: bytes) -> tuple[zipfile.ZipInfo, bytes]:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    info.compress_type = zipfile.ZIP_STORED
    return info, content


def build(manifest_path: Path, report_path: Path, output: Path, snapshot_id: str) -> dict[str, object]:
    manifest = read_manifest(manifest_path)
    rows = declared_rows(manifest)
    entries: dict[str, bytes] = {}
    for row in rows:
        content = (ROOT / row["source_path"]).read_bytes()
        actual = sha256_bytes(content)
        if actual != row["sha256"]:
            raise ValueError(f"manifest input hash mismatch: {row['source_path']}")
        entries[row["archive_path"]] = content
    entries["MANIFEST.yaml"] = manifest_path.read_bytes()
    entries["REPORT.md"] = report_path.read_bytes()
    entries["SOURCE_SNAPSHOT_ID.txt"] = (snapshot_id + "\n").encode("ascii")
    archive_map = {
        "schema_version": "agents-os.review-archive-map.v0.1",
        "source_snapshot_id": snapshot_id,
        "declared_inputs": rows,
    }
    entries["ARCHIVE_MAP.json"] = canonical(archive_map) + b"\n"
    if len(entries) != len(set(entries)):
        raise ValueError("archive duplicate entry path")
    checksums = "".join(f"{sha256_bytes(entries[name])}  {name}\n" for name in sorted(entries))
    entries["CHECKSUMS.sha256"] = checksums.encode("ascii")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, strict_timestamps=True) as archive:
        for name in sorted(entries):
            info, content = make_zip_entry(name, entries[name])
            archive.writestr(info, content)
    verify(output)
    return {
        "archive_path": str(output),
        "archive_sha256": sha256_bytes(output.read_bytes()),
        "entry_count": len(entries),
        "declared_input_count": len(rows),
    }


def verify(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC mismatch")
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError("ZIP duplicate path")
        for info in infos:
            safe_relative(info.filename)
            mode = info.external_attr >> 16
            if not stat.S_ISREG(mode):
                raise ValueError("ZIP member must be a regular file")
            archive.read(info.filename)
        checksums = archive.read("CHECKSUMS.sha256").decode("ascii").splitlines()
        expected: dict[str, str] = {}
        for line in checksums:
            if line.count("  ") != 1:
                raise ValueError("CHECKSUMS syntax mismatch")
            digest, name = line.split("  ", 1)
            if re.fullmatch(r"[0-9a-f]{64}", digest) is None or name in expected:
                raise ValueError("CHECKSUMS digest or duplicate-name mismatch")
            safe_relative(name)
            expected[name] = digest
        actual_names = set(names) - {"CHECKSUMS.sha256"}
        if set(expected) != actual_names:
            raise ValueError("CHECKSUMS inventory mismatch")
        for name, digest in expected.items():
            if sha256_bytes(archive.read(name)) != digest:
                raise ValueError(f"CHECKSUMS mismatch: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--snapshot-id", required=True)
    args = parser.parse_args()
    result = build(args.manifest, args.report, args.output, args.snapshot_id)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
