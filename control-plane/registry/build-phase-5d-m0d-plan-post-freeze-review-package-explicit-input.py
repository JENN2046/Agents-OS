#!/usr/bin/env python3
"""Fail closed for explicit inputs without rewriting the frozen R2 builder.

The Phase 5D M0-D R2 review-package builder is immutable evidence.  This
successor keeps its normal workspace behavior behind the already-guarded
post-freeze builder, and adds one exact compatibility path for an extracted
archive: the paired ``MANIFEST.yaml`` / ``REPORT.md`` aliases from its
``payload/`` directory.  Every other absent explicit path is rejected before
the historical builder can read a payload or create an output ZIP.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import sys
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Iterator

import yaml


ROOT = Path(__file__).resolve().parents[2]
PRIOR_SUCCESSOR = {
    "path": "control-plane/registry/build-phase-5d-m0d-plan-post-freeze-review-package.py",
    "sha256": "7ce6091dca0002483180317d9b607f73aad018d8558b1b9f1c30280c493d0392",
}
ARCHIVE_MANIFEST_ALIAS = "MANIFEST.yaml"
ARCHIVE_REPORT_ALIAS = "REPORT.md"
ARCHIVE_PAYLOAD_DIRECTORY = "payload"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def prior_successor_path() -> Path:
    return ROOT / PRIOR_SUCCESSOR["path"]


def load_prior_successor() -> ModuleType:
    path = prior_successor_path()
    if path.is_symlink() or not path.is_file():
        raise ValueError("guarded post-freeze builder is unavailable")
    actual = sha256_bytes(path.read_bytes())
    if actual != PRIOR_SUCCESSOR["sha256"]:
        raise ValueError("guarded post-freeze builder SHA-256 mismatch")
    spec = importlib.util.spec_from_file_location("_phase5d_post_freeze_builder_guard", path)
    if spec is None or spec.loader is None:
        raise ValueError("guarded post-freeze builder cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def working_directory(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} is not a regular file: {path}")
    return path


def archive_alias_pair(manifest: Path, report: Path) -> bool:
    return manifest.as_posix() == ARCHIVE_MANIFEST_ALIAS and report.as_posix() == ARCHIVE_REPORT_ALIAS


def mentions_archive_alias(path: Path) -> bool:
    return path.as_posix() in {ARCHIVE_MANIFEST_ALIAS, ARCHIVE_REPORT_ALIAS}


def require_archive_alias_context(manifest: Path, report: Path) -> tuple[Path, Path, Path]:
    if not archive_alias_pair(manifest, report):
        raise ValueError("archive-root aliases must be supplied together as MANIFEST.yaml REPORT.md")
    payload_root = Path.cwd().resolve()
    if payload_root.name != ARCHIVE_PAYLOAD_DIRECTORY:
        raise ValueError("archive-root aliases require the current directory to be payload")
    archive_root = payload_root.parent
    manifest_path = regular_file(archive_root / ARCHIVE_MANIFEST_ALIAS, "archive manifest")
    report_path = regular_file(archive_root / ARCHIVE_REPORT_ALIAS, "archive report")
    return archive_root, manifest_path, report_path


def archive_member_path(prior: ModuleType, payload_root: Path, declared_path: object) -> Path:
    relative = prior.parse_relative_path(declared_path, "archive manifest path")
    raw = relative.as_posix()
    if prior.is_protected_relative_path(raw):
        raise ValueError(f"protected archive manifest path: {raw}")

    candidate = payload_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError(f"archive manifest path traverses symlink: {raw}")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(payload_root)
    except ValueError as exc:
        raise ValueError(f"archive manifest path escapes payload: {raw}") from exc
    return regular_file(candidate, f"archive manifest path {raw}")


def preflight_archive_alias_inputs(prior: ModuleType, manifest_path: Path, payload_root: Path) -> None:
    manifest = prior.load_manifest(manifest_path)
    for row in prior.declared_rows(manifest):
        source = archive_member_path(prior, payload_root, row["path"])
        actual = prior.sha256_bytes(source.read_bytes())
        if actual != row["sha256"]:
            raise ValueError(f"archive manifest hash mismatch for {row['path']}: {actual} != {row['sha256']}")


def archive_output_path(prior: ModuleType, output: Path, archive_root: Path) -> Path:
    target = prior.safe_output_path(output)
    try:
        target.relative_to(archive_root)
    except ValueError:
        return target
    raise ValueError("archive alias output must be outside the extracted archive root")


def build_from_archive_aliases(prior: ModuleType, output: Path, manifest: Path, report: Path) -> None:
    archive_root, manifest_path, report_path = require_archive_alias_context(manifest, report)
    payload_root = archive_root / ARCHIVE_PAYLOAD_DIRECTORY
    if payload_root != Path.cwd().resolve():
        raise ValueError("archive-root aliases require the direct payload directory")
    target = archive_output_path(prior, output, archive_root)
    prior.verify_historical_builder("r2")
    preflight_archive_alias_inputs(prior, manifest_path, payload_root)

    historical = prior.load_historical_builder("r2")
    result = historical.main(
        [
            str(prior.historical_builder_path("r2")),
            str(target),
            ARCHIVE_MANIFEST_ALIAS,
            ARCHIVE_REPORT_ALIAS,
        ]
    )
    if result != 0:
        raise ValueError("immutable R2 review-package builder failed")


def build(output: Path, manifest: Path | None, report: Path | None) -> None:
    """Build R2 with no fallback from an absent explicit input to a default."""

    prior = load_prior_successor()
    if (manifest is None) != (report is None):
        raise ValueError("explicit manifest and report inputs must be supplied together")
    if manifest is None and report is None:
        prior.build("r2", output, prior.default_manifest_path("r2"), prior.default_report_path("r2"))
        return

    assert manifest is not None and report is not None
    if archive_alias_pair(manifest, report):
        build_from_archive_aliases(prior, output, manifest, report)
        return
    if mentions_archive_alias(manifest) or mentions_archive_alias(report):
        raise ValueError("archive-root aliases must be supplied together as MANIFEST.yaml REPORT.md")

    # The prior successor treats explicit direct paths as explicit paths: its
    # safe manifest/report guards reject a missing or unsafe path before output.
    prior.build("r2", output, manifest, report)


def main(argv: list[str]) -> int:
    if len(argv) not in (2, 4):
        print(f"usage: {argv[0]} OUTPUT_ZIP [MANIFEST_PATH REPORT_PATH]", file=sys.stderr)
        return 2
    output = Path(argv[1])
    manifest = Path(argv[2]) if len(argv) == 4 else None
    report = Path(argv[3]) if len(argv) == 4 else None
    try:
        build(output, manifest, report)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"BLOCK explicit-input resolution: {exc}", file=sys.stderr)
        return 1
    print("PASS guarded Phase 5D R2 explicit-input review-package build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
