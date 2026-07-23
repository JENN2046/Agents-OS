#!/usr/bin/env python3
"""Guard future Phase 5D review-package builds without rewriting frozen bytes.

The accepted R1/R2 package builders are immutable historical evidence.  This
successor checks a future or re-signed manifest before delegating to one of
those exact sources.  It does not own Plan, Host, plugin, runtime, database,
provider, authentication, Memory, or effect semantics.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Iterator

import yaml


ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_BUILDERS = {
    "r1": {
        "path": "control-plane/registry/build-phase-5d-m0d-plan-r1-review-package.py",
        "sha256": "de811d192f348af5aff68c631738b51e09cc33aa743d4fafa7dcf74ae6475074",
    },
    "r2": {
        "path": "control-plane/registry/build-phase-5d-m0d-plan-r2-review-package.py",
        "sha256": "105a4ee485750c7c4f64f7b872f97e4b5e3d9f03bcc9d191a2d0e2c3c56a361b",
    },
}
MANIFEST_GROUPS = ("subjects", "authority_inputs", "author_evidence")
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
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


class DuplicateKeyError(ValueError):
    pass


class UniqueKeySafeLoader(yaml.SafeLoader):
    pass


def construct_unique_mapping(loader: yaml.SafeLoader, node: yaml.nodes.MappingNode, deep: bool = False) -> dict[str, object]:
    mapping: dict[str, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if type(key) is not str:
            raise DuplicateKeyError("manifest mapping key must be a string")
        if key in mapping:
            raise DuplicateKeyError(f"duplicate manifest key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeySafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_unique_mapping)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def historical_builder_path(revision: str) -> Path:
    if revision not in HISTORICAL_BUILDERS:
        raise ValueError(f"unknown historical builder revision: {revision}")
    return ROOT / HISTORICAL_BUILDERS[revision]["path"]


def verify_historical_builder(revision: str) -> Path:
    path = historical_builder_path(revision)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"immutable historical builder is unavailable: {revision}")
    actual = sha256_bytes(path.read_bytes())
    expected = HISTORICAL_BUILDERS[revision]["sha256"]
    if actual != expected:
        raise ValueError(f"immutable historical builder SHA-256 mismatch: {revision}")
    return path


def load_historical_builder(revision: str) -> ModuleType:
    path = verify_historical_builder(revision)
    module_name = f"_phase5d_m0d_immutable_{revision}_review_package_builder"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"immutable historical builder cannot be loaded: {revision}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def parse_relative_path(path: object, label: str) -> PurePosixPath:
    if type(path) is not str or not path:
        raise ValueError(f"{label} must be a nonempty string")
    if "\\" in path:
        raise ValueError(f"{label} must not contain a backslash: {path}")
    candidate = PurePosixPath(path)
    if str(candidate) == "." or candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"unsafe {label}: {path}")
    return candidate


def is_protected_relative_path(path: str) -> bool:
    parts = tuple(part.lower() for part in PurePosixPath(path).parts)
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


def protected_workspace_file(path: object, label: str) -> Path:
    relative = parse_relative_path(path, label)
    raw = relative.as_posix()
    if is_protected_relative_path(raw):
        raise ValueError(f"protected {label}: {raw}")
    candidate = ROOT.joinpath(*relative.parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved_relative = resolved.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"{label} points outside workspace: {raw}") from exc
    if is_protected_relative_path(resolved_relative.as_posix()):
        raise ValueError(f"{label} resolves to protected path: {raw}")
    if candidate.is_symlink() or not candidate.is_file():
        raise ValueError(f"{label} is not a regular workspace file: {raw}")
    return candidate


def safe_report_path(path: Path) -> Path:
    candidate = path if path.is_absolute() else ROOT / path
    try:
        relative = candidate.resolve(strict=False).relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"report path points outside workspace: {path}") from exc
    return protected_workspace_file(relative.as_posix(), "report path")


def safe_manifest_path(path: Path) -> Path:
    candidate = path.resolve(strict=False)
    try:
        relative = candidate.relative_to(ROOT)
    except ValueError:
        if is_protected_relative_path(candidate.as_posix()):
            raise ValueError(f"protected manifest path: {path}")
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError(f"manifest is not a regular file: {path}")
        return candidate
    return protected_workspace_file(relative.as_posix(), "manifest path")


def safe_output_path(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    try:
        relative = resolved.relative_to(ROOT)
    except ValueError:
        return resolved
    if is_protected_relative_path(relative.as_posix()):
        raise ValueError(f"output path resolves to protected path: {path}")
    return resolved


@contextmanager
def workspace_cwd() -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(ROOT)
    try:
        yield
    finally:
        os.chdir(previous)


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError(f"manifest is not a regular file: {manifest_path}")
    try:
        value = yaml.load(manifest_path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"manifest parse failure: {exc}") from exc
    if type(value) is not dict:
        raise ValueError("manifest must be a mapping")
    return value


def declared_rows(manifest: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for group in MANIFEST_GROUPS:
        value = manifest.get(group)
        if type(value) is not list:
            raise ValueError(f"manifest group {group} must be a list")
        for index, item in enumerate(value):
            if type(item) is not dict:
                raise ValueError(f"manifest group {group}[{index}] must be a mapping")
            path = item.get("path")
            digest = item.get("sha256")
            if type(path) is not str or type(digest) is not str or not SHA256_RE.fullmatch(digest):
                raise ValueError(f"manifest group {group}[{index}] has malformed path or sha256")
            rows.append({"group": group, "path": path, "sha256": digest})
    return rows


def preflight_manifest_entries(manifest_path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    manifest = load_manifest(manifest_path)
    rows = declared_rows(manifest)
    for row in rows:
        protected_workspace_file(row["path"], f"manifest {row['group']} path")
    return manifest, rows


def delegate_historical_build(revision: str, output: Path, manifest_path: Path, report_path: Path) -> None:
    historical = load_historical_builder(revision)
    if revision == "r1":
        original_manifest, original_report = historical.MANIFEST_PATH, historical.REPORT_PATH
        historical.MANIFEST_PATH, historical.REPORT_PATH = manifest_path, report_path
        try:
            result = historical.main([str(historical_builder_path(revision)), str(output)])
        finally:
            historical.MANIFEST_PATH, historical.REPORT_PATH = original_manifest, original_report
    else:
        result = historical.main([str(historical_builder_path(revision)), str(output), str(manifest_path), str(report_path)])
    if result != 0:
        raise ValueError(f"immutable historical builder failed: {revision}")


def build(revision: str, output: Path, manifest_path: Path, report_path: Path) -> None:
    """Preflight all manifest entries before any delegated payload read/write."""

    manifest = safe_manifest_path(manifest_path)
    verify_historical_builder(revision)
    preflight_manifest_entries(manifest)
    report = safe_report_path(report_path)
    target = safe_output_path(output)
    with workspace_cwd():
        delegate_historical_build(revision, target, manifest, report)


def default_manifest_path(revision: str) -> Path:
    historical = load_historical_builder(revision)
    return ROOT / historical.MANIFEST_PATH


def default_report_path(revision: str) -> Path:
    historical = load_historical_builder(revision)
    return ROOT / historical.REPORT_PATH


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("revision", choices=tuple(sorted(HISTORICAL_BUILDERS)))
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv[1:])
    manifest = args.manifest if args.manifest is not None else default_manifest_path(args.revision)
    report = args.report if args.report is not None else default_report_path(args.revision)
    build(args.revision, args.output, manifest, report)
    print(f"PASS guarded Phase 5D {args.revision} review-package build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
