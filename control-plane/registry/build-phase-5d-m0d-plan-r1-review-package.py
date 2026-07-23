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
WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_PATH_PARTS = frozenset(
    {
        "state-private",
        "secret",
        "secrets",
        "credentials",
        "tokens",
        "cookies",
        "browser profiles",
        "private memory raw text",
        "provider raw response",
    }
)
PROTECTED_BASENAMES = frozenset({"credentials.json", "token.json", "id_rsa", "id_ed25519"})
PROTECTED_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx"})


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_protected_relative_path(path: str) -> bool:
    """Return whether a manifest path selects protected or secret-like data.

    This lexical check happens before resolution or any file-content read.
    ``.env.example`` remains allowed because the workspace expressly permits
    example/template files; actual dotenv files do not.
    """

    candidate = PurePosixPath(path)
    parts = tuple(part.lower() for part in candidate.parts)
    if any(part in PROTECTED_PATH_PARTS for part in parts):
        return True
    if any(part in PROTECTED_BASENAMES or any(part.endswith(suffix) for suffix in PROTECTED_SUFFIXES) for part in parts):
        return True
    return any(
        part == ".env"
        or (part.startswith(".env.") and part != ".env.example")
        or part == "config.env"
        or (part.startswith("config.env.") and part != "config.env.example")
        for part in parts
    )


def safe_archive_name(path: str) -> str:
    if type(path) is not str:
        raise ValueError("manifest path must be a string")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in path:
        raise ValueError(f"unsafe archive path: {path}")
    return str(PurePosixPath("payload") / candidate)


def manifest_source_path(path: str) -> Path:
    """Resolve a declared source without reading protected workspace content."""

    safe_archive_name(path)
    if is_protected_relative_path(path):
        raise ValueError(f"protected manifest source path: {path}")
    candidate = WORKSPACE_ROOT.joinpath(*PurePosixPath(path).parts)
    resolved = candidate.resolve(strict=False)
    try:
        relative = resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError(f"manifest source points outside workspace: {path}") from exc
    if is_protected_relative_path(relative.as_posix()):
        raise ValueError(f"manifest source resolves to protected path: {path}")
    return candidate


def read_manifest_source(path: str) -> tuple[Path, bytes]:
    """Perform all path checks before the only content read for an entry."""

    source = manifest_source_path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError(f"not a regular source file: {source}")
    return source, source.read_bytes()


def add_file(entries: dict[str, bytes], arcname: str, source: Path, data: bytes) -> None:
    if arcname in entries:
        raise ValueError(f"duplicate archive path: {arcname}")
    entries[arcname] = data


def run_path_guard_self_test() -> int:
    protected = ("state-private/foo", ".env", "config.env", "secrets/payload", "credentials.json", "key.pem")
    rejected = []
    for path in protected:
        try:
            read_manifest_source(path)
        except ValueError as exc:
            if str(exc) == f"protected manifest source path: {path}":
                rejected.append(path)
                continue
            raise
        raise AssertionError(f"protected path was accepted: {path}")
    if is_protected_relative_path(".env.example") or is_protected_relative_path("config.env.example"):
        raise AssertionError("allowed dotenv example was classified as protected")
    if rejected != list(protected):
        raise AssertionError("path guard self-test did not cover every protected path")
    print("PASS protected manifest source path guard")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--self-test":
        return run_path_guard_self_test()
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
            arcname = safe_archive_name(item["path"])
            if arcname in entries:
                raise ValueError(f"duplicate archive path: {arcname}")
            source, data = read_manifest_source(item["path"])
            actual = sha256(data)
            if actual != item["sha256"]:
                raise ValueError(f"hash mismatch for {source}: {actual} != {item['sha256']}")
            add_file(entries, arcname, source, data)
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
