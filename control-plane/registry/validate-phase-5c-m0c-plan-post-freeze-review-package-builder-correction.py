#!/usr/bin/env python3
"""Offline validation for the Phase 5C post-freeze builder correction.

It uses temporary files only.  It does not modify the historical builder,
accepted Plan subjects, VCPToolBox, a plugin, a runtime, a database, private
Memory, a provider, sensing, or an effect boundary.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import ModuleType
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
WRAPPER_RELATIVE_PATH = "control-plane/registry/build-phase-5c-m0c-plan-post-freeze-review-package.py"
FIXTURE_RELATIVE_PATH = "control-plane/registry/examples/2026-07-22-agents-os-phase-5c-m0c-plan-post-freeze-review-package-builder-correction-fixture-v0.1.json"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_wrapper() -> ModuleType:
    path = ROOT / WRAPPER_RELATIVE_PATH
    spec = importlib.util.spec_from_file_location("_phase5c_m0c_post_freeze_builder", path)
    if spec is None or spec.loader is None:
        raise ValueError("correction builder cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_keys(value: object, keys: set[str], label: str, errors: list[str]) -> bool:
    if type(value) is not dict or set(value) != keys:
        errors.append(f"{label} field inventory mismatch")
        return False
    return True


def validate_fixture(value: object, errors: list[str]) -> dict[str, Any] | None:
    expected = {
        "schema_version", "environment", "historical_builder", "valid_control",
        "reserved_generated_archive_members", "collision_expectation", "terminal_outcome",
    }
    if not exact_keys(value, expected, "fixture", errors):
        return None
    assert isinstance(value, dict)
    if value["schema_version"] != "agents-os.phase5c.post-freeze-review-package-builder-correction-fixture.v0.1":
        errors.append("fixture schema version mismatch")
    if value["environment"] != "SYNTHETIC_TEST" or value["terminal_outcome"] != "NOT_EXECUTED":
        errors.append("fixture boundary literal mismatch")
    if not exact_keys(value["historical_builder"], {"path", "sha256"}, "historical_builder", errors):
        return None
    if not exact_keys(value["valid_control"], {"payload_path", "payload_sha256", "report_path", "snapshot_id"}, "valid_control", errors):
        return None
    if not exact_keys(value["collision_expectation"], {"result", "output_file_exists_after_rejection"}, "collision_expectation", errors):
        return None
    members = value["reserved_generated_archive_members"]
    if type(members) is not list or any(type(item) is not str for item in members):
        errors.append("reserved generated archive members malformed")
    elif members != sorted(members) or len(members) != len(set(members)):
        errors.append("reserved generated archive members must be sorted and unique")
    return value


def run(fixture_path: Path) -> dict[str, object]:
    errors: list[str] = []
    try:
        raw_fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"result": "BLOCK", "errors": [f"fixture parse failure: {exc}"]}
    fixture = validate_fixture(raw_fixture, errors)
    if fixture is None:
        return {"result": "BLOCK", "errors": errors}

    wrapper = load_wrapper()
    historical_path = ROOT / fixture["historical_builder"]["path"]
    actual_historical_sha = sha256_bytes(historical_path.read_bytes()) if historical_path.is_file() else None
    if actual_historical_sha != fixture["historical_builder"]["sha256"]:
        errors.append("historical builder fixture SHA mismatch")
    if wrapper.HISTORICAL_BUILDER_SHA256 != fixture["historical_builder"]["sha256"]:
        errors.append("wrapper historical builder SHA mismatch")
    expected_members = frozenset(fixture["reserved_generated_archive_members"])
    if wrapper.GENERATED_ARCHIVE_MEMBERS != expected_members:
        errors.append("wrapper reserved member inventory mismatch")

    control = fixture["valid_control"]
    payload_path = ROOT / control["payload_path"]
    report_path = ROOT / control["report_path"]
    if not payload_path.is_file() or sha256_bytes(payload_path.read_bytes()) != control["payload_sha256"]:
        errors.append("valid control payload SHA mismatch")
    if not report_path.is_file():
        errors.append("valid control report is unavailable")
    base_manifest = {
        "schema_version": "agents-os.synthetic-review-package-control.v0.1",
        "review_unit": {"subjects": []},
        "authority_inputs": [],
        "author_evidence": [{
            "role": "synthetic_payload",
            "path": control["payload_path"],
            "sha256": control["payload_sha256"],
        }],
    }

    valid_archive_sha: str | None = None
    collision_results: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="agents-os-phase5c-post-freeze-builder-") as temp_dir:
        temp_root = Path(temp_dir)
        valid_manifest_path = temp_root / "valid-control-manifest.yaml"
        valid_manifest_path.write_text(
            yaml.safe_dump(base_manifest, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        valid_output = temp_root / "valid-successor.zip"
        historical_output = temp_root / "valid-historical.zip"
        try:
            result = wrapper.build(valid_manifest_path, report_path, valid_output, control["snapshot_id"])
            historical = wrapper.load_historical_builder()
            historical.build(valid_manifest_path, report_path, historical_output, control["snapshot_id"])
            valid_archive_sha = sha256_bytes(valid_output.read_bytes())
            if result.get("archive_sha256") != valid_archive_sha:
                errors.append("valid builder result digest mismatch")
            if valid_output.read_bytes() != historical_output.read_bytes():
                errors.append("valid non-colliding successor output differs from immutable historical builder")
        except Exception as exc:
            errors.append(f"valid non-colliding control failed: {exc}")

        for member in fixture["reserved_generated_archive_members"]:
            collision_manifest = copy.deepcopy(base_manifest)
            collision_manifest["author_evidence"].append({
                "role": "synthetic_reserved_member_collision",
                "path": member,
                "sha256": "0" * 64,
            })
            collision_manifest_path = temp_root / f"collision-{member.replace('.', '_')}.yaml"
            collision_output = temp_root / f"collision-{member.replace('.', '_')}.zip"
            collision_manifest_path.write_text(
                yaml.safe_dump(collision_manifest, sort_keys=False, allow_unicode=True),
                encoding="utf-8",
            )
            try:
                wrapper.build(collision_manifest_path, report_path, collision_output, control["snapshot_id"])
                errors.append(f"reserved member collision accepted: {member}")
                collision_results[member] = "ACCEPTED"
            except ValueError as exc:
                expected_message = f"manifest declared reserved generated archive member(s): {member}"
                if str(exc) != expected_message:
                    errors.append(f"reserved member collision wrong rejection for {member}: {exc}")
                    collision_results[member] = "WRONG_REJECTION"
                elif collision_output.exists():
                    errors.append(f"reserved member collision wrote output: {member}")
                    collision_results[member] = "OUTPUT_WRITTEN"
                else:
                    collision_results[member] = "REJECTED_BEFORE_OUTPUT_WRITE"
            except Exception as exc:
                errors.append(f"reserved member collision unstable error for {member}: {exc}")
                collision_results[member] = "UNSTABLE_ERROR"

    post_historical_sha = sha256_bytes(historical_path.read_bytes()) if historical_path.is_file() else None
    if post_historical_sha != actual_historical_sha:
        errors.append("historical builder bytes changed during validation")
    if errors:
        return {
            "result": "BLOCK",
            "errors": errors,
            "valid_archive_sha256": valid_archive_sha,
            "collision_results": collision_results,
        }
    return {
        "result": "PASS",
        "historical_builder_sha256": actual_historical_sha,
        "valid_archive_sha256": valid_archive_sha,
        "collision_results": collision_results,
        "collision_count": len(collision_results),
        "terminal_outcome": "NOT_EXECUTED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path, nargs="?", default=ROOT / FIXTURE_RELATIVE_PATH)
    args = parser.parse_args()
    result = run(args.fixture)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
