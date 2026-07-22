#!/usr/bin/env python3
"""Build Phase 5C review ZIPs with a post-freeze generated-member guard.

This successor preserves the historical R3 builder as an immutable byte-bound
dependency.  It adds no Plan semantics: it rejects a manifest-declared archive
path that would otherwise be overwritten by package-local generated metadata,
then delegates a valid build to the exact historical source.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_BUILDER_RELATIVE_PATH = "control-plane/registry/build-phase-5c-m0c-plan-r3-review-package.py"
HISTORICAL_BUILDER_SHA256 = "8ddffa24d935189f733929b1aa0df16b997f0b65db946411fdfd0c5b889bcfd4"
GENERATED_ARCHIVE_MEMBERS = frozenset({
    "MANIFEST.yaml",
    "REPORT.md",
    "SOURCE_SNAPSHOT_ID.txt",
    "ARCHIVE_MAP.json",
    "CHECKSUMS.sha256",
})


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def historical_builder_path() -> Path:
    return ROOT / HISTORICAL_BUILDER_RELATIVE_PATH


def verify_historical_builder() -> Path:
    path = historical_builder_path()
    if not path.is_file():
        raise ValueError("immutable historical builder is unavailable")
    actual = sha256_bytes(path.read_bytes())
    if actual != HISTORICAL_BUILDER_SHA256:
        raise ValueError("immutable historical builder SHA-256 mismatch")
    return path


def load_historical_builder() -> ModuleType:
    path = verify_historical_builder()
    module_name = "_phase5c_m0c_immutable_r3_review_package_builder"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError("immutable historical builder cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def collision_names(manifest_path: Path) -> tuple[str, ...]:
    """Return sorted manifest archive paths that collide with generated members.

    The historical parser is deliberately reused so valid manifest parsing
    behavior remains byte-compatible.  This occurs before the delegated
    builder reads any declared payload or creates the output archive.
    """

    historical = load_historical_builder()
    manifest = historical.read_manifest(manifest_path)
    rows = historical.declared_rows(manifest)
    return tuple(sorted({row["archive_path"] for row in rows} & GENERATED_ARCHIVE_MEMBERS))


def reject_generated_member_collisions(manifest_path: Path) -> None:
    collisions = collision_names(manifest_path)
    if collisions:
        raise ValueError(
            "manifest declared reserved generated archive member(s): "
            + ", ".join(collisions)
        )


def build(manifest_path: Path, report_path: Path, output: Path, snapshot_id: str) -> dict[str, object]:
    reject_generated_member_collisions(manifest_path)
    historical = load_historical_builder()
    return historical.build(manifest_path, report_path, output, snapshot_id)


def verify(path: Path) -> None:
    historical = load_historical_builder()
    historical.verify(path)


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
