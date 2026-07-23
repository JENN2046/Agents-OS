#!/usr/bin/env python3
"""Offline regression proof for Phase 5D post-freeze explicit-input handling."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import stat
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, Iterator


ROOT = Path(__file__).resolve().parents[2]
SUCCESSOR_RELATIVE_PATH = "control-plane/registry/build-phase-5d-m0d-plan-post-freeze-review-package-explicit-input.py"
FIXTURE_RELATIVE_PATH = (
    "control-plane/registry/examples/"
    "2026-07-24-agents-os-phase-5d-m0d-plan-post-freeze-review-package-explicit-input-correction-fixture-v0.1.json"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exact_keys(value: object, expected: set[str], label: str, errors: list[str]) -> bool:
    if type(value) is not dict or set(value) != expected:
        errors.append(f"{label} field inventory mismatch")
        return False
    return True


def load_successor() -> ModuleType:
    path = ROOT / SUCCESSOR_RELATIVE_PATH
    if path.is_symlink() or not path.is_file():
        raise ValueError("explicit-input successor is unavailable")
    spec = importlib.util.spec_from_file_location("_phase5d_explicit_input_successor", path)
    if spec is None or spec.loader is None:
        raise ValueError("explicit-input successor cannot be loaded")
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


def validate_fixture(value: object, errors: list[str]) -> dict[str, Any] | None:
    if not exact_keys(
        value,
        {"schema_version", "environment", "frozen_bindings", "archive_aliases", "negative_case_ids", "expectations", "terminal_outcome"},
        "fixture",
        errors,
    ):
        return None
    assert isinstance(value, dict)
    if value["schema_version"] != "agents-os.phase5d.post-freeze-review-package-explicit-input-correction-fixture.v0.1":
        errors.append("fixture schema version mismatch")
    if value["environment"] != "SYNTHETIC_TEST" or value["terminal_outcome"] != "NOT_EXECUTED":
        errors.append("fixture boundary literal mismatch")
    if not exact_keys(value["frozen_bindings"], {"r2_builder", "r2_manifest", "prior_guarded_successor"}, "frozen_bindings", errors):
        return None
    assert isinstance(value["frozen_bindings"], dict)
    for name, binding in value["frozen_bindings"].items():
        if not exact_keys(binding, {"path", "sha256"}, f"frozen_bindings.{name}", errors):
            return None
        assert isinstance(binding, dict)
        if type(binding["path"]) is not str or type(binding["sha256"]) is not str:
            errors.append(f"frozen_bindings.{name} values must be strings")
    if not exact_keys(value["archive_aliases"], {"manifest", "report", "payload_directory"}, "archive_aliases", errors):
        return None
    assert isinstance(value["archive_aliases"], dict)
    if value["archive_aliases"] != {
        "manifest": "MANIFEST.yaml",
        "report": "REPORT.md",
        "payload_directory": "payload",
    }:
        errors.append("archive alias inventory mismatch")
    expected_negative_cases = ["ALIAS_OUTSIDE_PAYLOAD", "MISSING_BOTH", "MISSING_MANIFEST", "MISSING_REPORT", "PARTIAL_ALIAS"]
    if value["negative_case_ids"] != expected_negative_cases:
        errors.append("negative case inventory mismatch")
    if value["expectations"] != {
        "direct_explicit_inputs": "BYTE_EQUAL",
        "archive_alias_pair": "BYTE_EQUAL",
        "all_negative_cases": "REJECTED_BEFORE_OUTPUT_WRITE",
    }:
        errors.append("expectation inventory mismatch")
    return value


def safe_extract(archive: Path, destination: Path) -> None:
    with zipfile.ZipFile(archive, "r") as source:
        for info in source.infolist():
            candidate = PurePosixPath(info.filename)
            if candidate.is_absolute() or ".." in candidate.parts or "\\" in info.filename:
                raise ValueError(f"unsafe generated archive member: {info.filename}")
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError(f"generated archive contains symlink: {info.filename}")
        source.extractall(destination)


def expect_rejection(
    successor: ModuleType,
    output: Path,
    manifest: Path | None,
    report: Path | None,
    errors: list[str],
    results: dict[str, str],
    case_id: str,
) -> None:
    try:
        successor.build(output, manifest, report)
    except ValueError:
        if output.exists():
            errors.append(f"{case_id} wrote output before rejection")
            results[case_id] = "OUTPUT_WRITTEN"
        else:
            results[case_id] = "REJECTED_BEFORE_OUTPUT_WRITE"
    except Exception as exc:
        errors.append(f"{case_id} raised an unstable exception: {exc}")
        results[case_id] = "UNSTABLE_EXCEPTION"
    else:
        errors.append(f"{case_id} accepted a malformed explicit input")
        results[case_id] = "ACCEPTED"


def run(fixture_path: Path) -> dict[str, object]:
    errors: list[str] = []
    try:
        raw_fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"result": "BLOCK", "errors": [f"fixture parse failure: {exc}"], "terminal_outcome": "NOT_EXECUTED"}
    fixture = validate_fixture(raw_fixture, errors)
    if fixture is None or errors:
        return {"result": "BLOCK", "errors": errors, "terminal_outcome": "NOT_EXECUTED"}

    try:
        successor = load_successor()
        prior = successor.load_prior_successor()
    except Exception as exc:
        return {"result": "BLOCK", "errors": [f"successor load failure: {exc}"], "terminal_outcome": "NOT_EXECUTED"}

    bindings = fixture["frozen_bindings"]
    assert isinstance(bindings, dict)
    for binding_name, binding in bindings.items():
        assert isinstance(binding, dict)
        path = ROOT / binding["path"]
        actual = sha256_bytes(path.read_bytes()) if path.is_file() and not path.is_symlink() else None
        if actual != binding["sha256"]:
            errors.append(f"{binding_name} SHA-256 mismatch")
    if successor.PRIOR_SUCCESSOR != bindings["prior_guarded_successor"]:
        errors.append("successor prior-guard binding mismatch")

    manifest_path = ROOT / bindings["r2_manifest"]["path"]
    report_path = prior.default_report_path("r2")
    if manifest_path.is_symlink() or not manifest_path.is_file() or report_path.is_symlink() or not report_path.is_file():
        errors.append("frozen direct controls are unavailable")
    if errors:
        return {"result": "BLOCK", "errors": errors, "terminal_outcome": "NOT_EXECUTED"}

    byte_equality: dict[str, str] = {}
    negative_results: dict[str, str] = {}
    historical_fallback_observed = False
    with tempfile.TemporaryDirectory(prefix="agents-os-phase5d-explicit-input-") as temp_dir:
        temp = Path(temp_dir)
        historical_output = temp / "historical.zip"
        with working_directory(ROOT):
            prior.delegate_historical_build("r2", historical_output, manifest_path, report_path)

        direct_output = temp / "direct.zip"
        try:
            successor.build(direct_output, manifest_path, report_path)
            byte_equality["direct_explicit"] = "BYTE_EQUAL" if direct_output.read_bytes() == historical_output.read_bytes() else "DIFFERENT"
            if byte_equality["direct_explicit"] != "BYTE_EQUAL":
                errors.append("direct explicit output differs from historical R2 output")
        except Exception as exc:
            errors.append(f"direct explicit control failed: {exc}")
            byte_equality["direct_explicit"] = "ERROR"

        extracted = temp / "extracted"
        safe_extract(historical_output, extracted)
        payload = extracted / fixture["archive_aliases"]["payload_directory"]
        alias_output = temp / "alias.zip"
        try:
            with working_directory(payload):
                successor.build(
                    alias_output,
                    Path(fixture["archive_aliases"]["manifest"]),
                    Path(fixture["archive_aliases"]["report"]),
                )
            byte_equality["archive_alias_pair"] = "BYTE_EQUAL" if alias_output.read_bytes() == historical_output.read_bytes() else "DIFFERENT"
            if byte_equality["archive_alias_pair"] != "BYTE_EQUAL":
                errors.append("archive alias output differs from historical R2 output")
        except Exception as exc:
            errors.append(f"archive alias control failed: {exc}")
            byte_equality["archive_alias_pair"] = "ERROR"

        historical_missing = temp / "historical-missing.zip"
        historical = prior.load_historical_builder("r2")
        with working_directory(ROOT):
            historical_result = historical.main(
                [
                    str(prior.historical_builder_path("r2")),
                    str(historical_missing),
                    str(temp / "missing-manifest.yaml"),
                    str(temp / "missing-report.md"),
                ]
            )
        historical_fallback_observed = historical_result == 0 and historical_missing.is_file()
        if not historical_fallback_observed:
            errors.append("frozen historical missing-input fallback was not reproducible")

        expect_rejection(
            successor,
            temp / "missing-manifest.zip",
            temp / "missing-manifest.yaml",
            report_path,
            errors,
            negative_results,
            "MISSING_MANIFEST",
        )
        expect_rejection(
            successor,
            temp / "missing-report.zip",
            manifest_path,
            temp / "missing-report.md",
            errors,
            negative_results,
            "MISSING_REPORT",
        )
        expect_rejection(
            successor,
            temp / "missing-both.zip",
            temp / "missing-both-manifest.yaml",
            temp / "missing-both-report.md",
            errors,
            negative_results,
            "MISSING_BOTH",
        )
        with working_directory(payload):
            expect_rejection(
                successor,
                temp / "partial-alias.zip",
                Path(fixture["archive_aliases"]["manifest"]),
                report_path,
                errors,
                negative_results,
                "PARTIAL_ALIAS",
            )
        with working_directory(ROOT):
            expect_rejection(
                successor,
                temp / "alias-outside-payload.zip",
                Path(fixture["archive_aliases"]["manifest"]),
                Path(fixture["archive_aliases"]["report"]),
                errors,
                negative_results,
                "ALIAS_OUTSIDE_PAYLOAD",
            )

    if errors:
        return {
            "result": "BLOCK",
            "errors": errors,
            "byte_equality": byte_equality,
            "negative_results": negative_results,
            "historical_fallback_observed": historical_fallback_observed,
            "terminal_outcome": "NOT_EXECUTED",
        }
    return {
        "result": "PASS",
        "byte_equality": byte_equality,
        "negative_results": negative_results,
        "negative_case_count": len(negative_results),
        "historical_fallback_observed": historical_fallback_observed,
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
