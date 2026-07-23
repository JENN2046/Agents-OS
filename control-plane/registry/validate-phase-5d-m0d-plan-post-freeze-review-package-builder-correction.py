#!/usr/bin/env python3
"""Offline proof for the narrow Phase 5D post-freeze builder correction.

The validator uses only a synthetic payload and temporary manifests/ZIPs.  It
does not modify frozen Plan bytes, VCPToolBox, a Host, runtime, database,
provider, authentication, private Memory, sensing, or any effect boundary.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from contextlib import contextmanager
from pathlib import Path
import tempfile
from types import ModuleType
from typing import Any, Iterator

import yaml


ROOT = Path(__file__).resolve().parents[2]
WRAPPER_RELATIVE_PATH = "control-plane/registry/build-phase-5d-m0d-plan-post-freeze-review-package.py"
FIXTURE_RELATIVE_PATH = (
    "control-plane/registry/examples/"
    "2026-07-23-agents-os-phase-5d-m0d-plan-post-freeze-review-package-builder-correction-fixture-v0.1.json"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_keys(value: object, expected: set[str], label: str, errors: list[str]) -> bool:
    if type(value) is not dict or set(value) != expected:
        errors.append(f"{label} field inventory mismatch")
        return False
    return True


def load_wrapper() -> ModuleType:
    path = ROOT / WRAPPER_RELATIVE_PATH
    spec = importlib.util.spec_from_file_location("_phase5d_post_freeze_builder", path)
    if spec is None or spec.loader is None:
        raise ValueError("post-freeze builder cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_fixture(value: object, errors: list[str]) -> dict[str, Any] | None:
    expected = {
        "schema_version",
        "environment",
        "historical_builders",
        "valid_control",
        "protected_paths",
        "allowed_template_paths",
        "rejection_expectation",
        "terminal_outcome",
    }
    if not exact_keys(value, expected, "fixture", errors):
        return None
    assert isinstance(value, dict)
    if value["schema_version"] != "agents-os.phase5d.post-freeze-review-package-builder-correction-fixture.v0.1":
        errors.append("fixture schema version mismatch")
    if value["environment"] != "SYNTHETIC_TEST" or value["terminal_outcome"] != "NOT_EXECUTED":
        errors.append("fixture boundary literal mismatch")
    builders = value["historical_builders"]
    if not exact_keys(builders, {"r1", "r2"}, "historical_builders", errors):
        return None
    assert isinstance(builders, dict)
    for revision in ("r1", "r2"):
        if not exact_keys(builders[revision], {"path", "sha256"}, f"historical_builders.{revision}", errors):
            return None
        assert isinstance(builders[revision], dict)
        if any(type(builders[revision][field]) is not str for field in ("path", "sha256")):
            errors.append(f"historical_builders.{revision} values must be strings")
    if not exact_keys(value["valid_control"], {"payload_path", "payload_sha256", "report_path"}, "valid_control", errors):
        return None
    assert isinstance(value["valid_control"], dict)
    if any(type(value["valid_control"][field]) is not str for field in ("payload_path", "payload_sha256", "report_path")):
        errors.append("valid_control values must be strings")
    if not exact_keys(
        value["rejection_expectation"],
        {"result", "output_file_exists_after_rejection"},
        "rejection_expectation",
        errors,
    ):
        return None
    assert isinstance(value["rejection_expectation"], dict)
    if value["rejection_expectation"] != {
        "result": "REJECTED_BEFORE_PAYLOAD_READ_OR_OUTPUT_WRITE",
        "output_file_exists_after_rejection": False,
    }:
        errors.append("rejection_expectation mismatch")
    for label in ("protected_paths", "allowed_template_paths"):
        items = value[label]
        if type(items) is not list or any(type(item) is not str for item in items):
            errors.append(f"{label} must be a string list")
        elif items != sorted(items) or len(items) != len(set(items)):
            errors.append(f"{label} must be sorted and unique")
    return value


@contextmanager
def workspace_cwd() -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(ROOT)
    try:
        yield
    finally:
        os.chdir(previous)


def synthetic_manifest(path: str, digest: str) -> dict[str, object]:
    return {
        "subjects": [{"role": "synthetic_payload", "path": path, "sha256": digest}],
        "authority_inputs": [],
        "author_evidence": [],
    }


def run(fixture_path: Path) -> dict[str, object]:
    errors: list[str] = []
    try:
        raw_fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"result": "BLOCK", "errors": [f"fixture parse failure: {exc}"]}
    fixture = validate_fixture(raw_fixture, errors)
    if fixture is None:
        return {"result": "BLOCK", "errors": errors}
    if errors:
        return {"result": "BLOCK", "errors": errors}

    wrapper = load_wrapper()
    builders = fixture["historical_builders"]
    assert isinstance(builders, dict)
    for revision in ("r1", "r2"):
        expected = builders[revision]
        assert isinstance(expected, dict)
        source = ROOT / expected["path"]
        actual = sha256_bytes(source.read_bytes()) if source.is_file() else None
        if actual != expected["sha256"]:
            errors.append(f"historical {revision} builder fixture SHA mismatch")
        if wrapper.HISTORICAL_BUILDERS.get(revision) != expected:
            errors.append(f"successor {revision} immutable builder inventory mismatch")

    valid = fixture["valid_control"]
    assert isinstance(valid, dict)
    payload = ROOT / valid["payload_path"]
    report = ROOT / valid["report_path"]
    if not payload.is_file() or sha256_bytes(payload.read_bytes()) != valid["payload_sha256"]:
        errors.append("valid control payload SHA mismatch")
    if report.is_symlink() or not report.is_file():
        errors.append("valid control report is unavailable")

    protected = fixture["protected_paths"]
    allowed = fixture["allowed_template_paths"]
    assert isinstance(protected, list) and isinstance(allowed, list)
    for path in allowed:
        if wrapper.is_protected_relative_path(path):
            errors.append(f"allowed template path classified as protected: {path}")
    for path in protected:
        if not wrapper.is_protected_relative_path(path):
            errors.append(f"protected path was not classified as protected: {path}")

    protected_output = ROOT / "state-private" / "post-freeze-builder-probe.zip"
    try:
        wrapper.safe_output_path(protected_output)
    except ValueError as exc:
        if str(exc) != f"output path resolves to protected path: {protected_output}":
            errors.append(f"protected output path wrong rejection: {exc}")
    else:
        errors.append("protected output path was accepted")

    protected_manifest = ROOT / "state-private" / "post-freeze-builder-probe.yaml"
    try:
        wrapper.safe_manifest_path(protected_manifest)
    except ValueError as exc:
        if str(exc) != f"protected manifest path: state-private/post-freeze-builder-probe.yaml":
            errors.append(f"protected manifest path wrong rejection: {exc}")
    else:
        errors.append("protected manifest path was accepted")

    equality_results: dict[str, str] = {}
    rejection_results: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="agents-os-phase5d-post-freeze-builder-") as temp_dir:
        temp = Path(temp_dir)
        valid_manifest = temp / "valid-manifest.yaml"
        valid_manifest.write_text(yaml.safe_dump(synthetic_manifest(valid["payload_path"], valid["payload_sha256"]), sort_keys=False), encoding="utf-8")
        with workspace_cwd():
            for revision in ("r1", "r2"):
                guarded_output = temp / f"{revision}-guarded.zip"
                historical_output = temp / f"{revision}-historical.zip"
                try:
                    wrapper.build(revision, guarded_output, valid_manifest, report)
                    wrapper.delegate_historical_build(revision, historical_output, valid_manifest, report)
                    if guarded_output.read_bytes() != historical_output.read_bytes():
                        errors.append(f"valid {revision} output differs from historical builder")
                        equality_results[revision] = "DIFFERENT"
                    else:
                        equality_results[revision] = "BYTE_EQUAL"
                except Exception as exc:
                    errors.append(f"valid {revision} control failed: {exc}")
                    equality_results[revision] = "ERROR"

                for protected_path in protected:
                    manifest = temp / f"{revision}-{protected_path.replace('/', '_').replace('.', '_')}.yaml"
                    manifest.write_text(
                        yaml.safe_dump(synthetic_manifest(protected_path, "0" * 64), sort_keys=False),
                        encoding="utf-8",
                    )
                    output = temp / f"{revision}-{protected_path.replace('/', '_').replace('.', '_')}.zip"
                    key = f"{revision}:{protected_path}"
                    try:
                        wrapper.build(revision, output, manifest, report)
                        errors.append(f"protected path accepted: {key}")
                        rejection_results[key] = "ACCEPTED"
                    except ValueError as exc:
                        expected_message = f"protected manifest subjects path: {protected_path}"
                        if str(exc) != expected_message:
                            errors.append(f"protected path wrong rejection for {key}: {exc}")
                            rejection_results[key] = "WRONG_REJECTION"
                        elif output.exists():
                            errors.append(f"protected path wrote output for {key}")
                            rejection_results[key] = "OUTPUT_WRITTEN"
                        else:
                            rejection_results[key] = "REJECTED_BEFORE_OUTPUT_WRITE"
                    except Exception as exc:
                        errors.append(f"protected path unstable error for {key}: {exc}")
                        rejection_results[key] = "UNSTABLE_ERROR"

    if errors:
        return {
            "result": "BLOCK",
            "errors": errors,
            "byte_equality": equality_results,
            "protected_rejections": rejection_results,
        }
    return {
        "result": "PASS",
        "historical_builders": builders,
        "byte_equality": equality_results,
        "protected_rejections": rejection_results,
        "protected_rejection_count": len(rejection_results),
        "terminal_outcome": "NOT_EXECUTED",
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path, nargs="?", default=ROOT / FIXTURE_RELATIVE_PATH)
    args = parser.parse_args()
    result = run(args.fixture)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
