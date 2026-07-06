#!/usr/bin/env python3
"""Fixture tests for the Federated Document Registry validator."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def remove_fixture_path(path: Path) -> None:
    if path.exists() or path.is_symlink():
        path.unlink()


def load_validator() -> ModuleType:
    module_path = ROOT / "validate-federated-document-registry.py"
    spec = importlib.util.spec_from_file_location("federated_document_registry_validator", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def finding_ids(result: dict) -> set[str]:
    ids = {finding["rule_id"] for finding in result["registry_findings"]}
    for item in result["registries"]:
        ids.update(finding["rule_id"] for finding in item["findings"])
    return ids


def one_registry(**overrides: object) -> dict:
    entry = {
        "id": "fixture-registry",
        "title": "Fixture Registry",
        "status": "pilot",
        "directory_root": "control-plane/registry",
        "registry_path": "control-plane/registry/drafts/document-registry.v0.1.example.yaml",
        "owner": {"human": "Jenn", "agent_steward": "Nobao"},
        "validator": "control-plane/registry/validate-document-registry.py",
        "expected_document_count": 88,
        "authority": "example only, not active authority data",
        "security_boundary": ["no secrets", "no full workspace scan"],
    }
    entry.update(overrides)
    return entry


def validate_single(validator: ModuleType, **overrides: object) -> dict:
    return validator.validate_federation({"registries": [one_registry(**overrides)]})


class FailingDocumentValidator:
    def load_yaml(self, path: Path) -> dict:
        return {}

    def validate_registry(self, data: dict) -> dict:
        return {
            "passed": False,
            "summary": {"checked_documents": 0},
            "documents": [],
            "registry_findings": [{"rule_id": "fixture", "level": "fail", "message": "fixture"}],
        }


def main() -> int:
    validator = load_validator()
    failures: list[str] = []

    example_path = ROOT / "drafts" / "federated-document-registry.v0.1.example.yaml"
    data = validator.load_yaml(example_path)
    result = validator.validate_federation(data)
    registry_ids = {
        item.get("id")
        for item in data.get("registries", [])
        if isinstance(item, dict)
    }
    required_ids = {
        "registry-document-registry",
        "task-envelope-document-registry",
        "life-core-document-registry",
    }
    check(result["passed"], "federated registry example should pass", failures)
    check(required_ids.issubset(registry_ids), "federated registry is missing required ids", failures)
    check(result["summary"]["checked_registries"] == 3, "federated registry should check three registries", failures)

    missing_path = validate_single(validator, registry_path="")
    check(not missing_path["passed"], "missing registry_path should fail", failures)
    check("FDR-002" in finding_ids(missing_path), "missing registry_path should trigger FDR-002", failures)

    protected_path = validate_single(validator, registry_path="state-private/document-registry.yaml")
    check(not protected_path["passed"], "protected registry_path should fail", failures)
    check("FDR-003" in finding_ids(protected_path), "protected registry_path should trigger FDR-003", failures)

    outside_path = validate_single(validator, registry_path="/etc/hosts")
    check(not outside_path["passed"], "outside registry_path should fail", failures)
    check("FDR-003" in finding_ids(outside_path), "outside registry_path should trigger FDR-003", failures)

    mismatched_count = validate_single(validator, expected_document_count=999)
    check(not mismatched_count["passed"], "expected_document_count mismatch should fail", failures)
    check("FDR-009" in finding_ids(mismatched_count), "count mismatch should trigger FDR-009", failures)

    duplicate_id = validator.validate_federation(
        {"registries": [one_registry(id="dupe"), one_registry(id="dupe")]}
    )
    check(not duplicate_id["passed"], "duplicate id should fail", failures)
    check("FDR-010" in finding_ids(duplicate_id), "duplicate id should trigger FDR-010", failures)

    duplicate_path = validator.validate_federation(
        {
            "registries": [
                one_registry(id="one"),
                one_registry(id="two"),
            ]
        }
    )
    check(not duplicate_path["passed"], "duplicate registry_path should fail", failures)
    check("FDR-011" in finding_ids(duplicate_path), "duplicate registry_path should trigger FDR-011", failures)

    failed_child = validator.validate_federation(
        {"registries": [one_registry(expected_document_count="")]},
        document_validator=FailingDocumentValidator(),
    )
    check(not failed_child["passed"], "failed child document registry should fail federation", failures)
    check("FDR-008" in finding_ids(failed_child), "failed child should trigger FDR-008", failures)

    invalid_count = validate_single(validator, expected_document_count="many")
    check(not invalid_count["passed"], "non-integer expected_document_count should fail", failures)
    check("FDR-009" in finding_ids(invalid_count), "non-integer count should trigger FDR-009", failures)

    metadata_secret = validator.validate_federation(
        {
            "notes": ["sk-" + ("a" * 20)],
            "registries": [one_registry()],
        }
    )
    check(not metadata_secret["passed"], "root metadata secret-like pattern should fail", failures)
    check("FDR-015" in finding_ids(metadata_secret), "root metadata secret-like pattern should trigger FDR-015", failures)

    missing_known_review = validate_single(
        validator,
        known_external_scope=[
            {
                "path": "control-plane/registry/WORKSPACE_REGISTRY.yaml",
                "classification": "known_external_scope",
                "reason": "fixture",
            }
        ],
    )
    check(not missing_known_review["passed"], "known_external_scope missing review_trigger should fail", failures)
    check("FDR-017" in finding_ids(missing_known_review), "known external metadata should trigger FDR-017", failures)

    protected_known = validate_single(
        validator,
        known_external_scope=[
            {
                "path": "state-private/known.md",
                "classification": "known_external_scope",
                "reason": "fixture",
                "review_trigger": ["fixture"],
            }
        ],
    )
    check(not protected_known["passed"], "protected known_external_scope path should fail", failures)
    check("FDR-017" in finding_ids(protected_known), "protected known path should trigger FDR-017", failures)

    registered_known = validate_single(
        validator,
        known_external_scope=[
            {
                "path": "control-plane/registry/README.md",
                "classification": "known_external_scope",
                "reason": "fixture",
                "review_trigger": ["fixture"],
            }
        ],
    )
    check(not registered_known["passed"], "registered document cannot be known_external_scope", failures)
    check("FDR-019" in finding_ids(registered_known), "registered known path should trigger FDR-019", failures)

    missing_archive_safe_use = validate_single(
        validator,
        archive_notes=[
            {
                "path": "control-plane/registry/archive-notes/2026-07-01-grouped-historical-document-governance-backlog.md",
                "classification": "historical_archive",
                "replacement": ["control-plane/registry/README.md"],
                "review_trigger": ["fixture"],
            }
        ],
    )
    check(not missing_archive_safe_use["passed"], "archive_note missing safe_use should fail", failures)
    check("FDR-018" in finding_ids(missing_archive_safe_use), "archive safe_use should trigger FDR-018", failures)

    missing_archive_replacement = validate_single(
        validator,
        archive_notes=[
            {
                "path": "control-plane/registry/archive-notes/2026-07-01-grouped-historical-document-governance-backlog.md",
                "classification": "historical_archive",
                "safe_use": "historical context only",
                "review_trigger": ["fixture"],
            }
        ],
    )
    check(not missing_archive_replacement["passed"], "archive_note missing replacement should fail", failures)
    check("FDR-018" in finding_ids(missing_archive_replacement), "archive replacement should trigger FDR-018", failures)

    protected_archive = validate_single(
        validator,
        archive_notes=[
            {
                "path": "state-private/archive-note.md",
                "classification": "historical_archive",
                "safe_use": "historical context only",
                "replacement": ["control-plane/registry/README.md"],
                "review_trigger": ["fixture"],
            }
        ],
    )
    check(not protected_archive["passed"], "protected archive_note path should fail", failures)
    check("FDR-018" in finding_ids(protected_archive), "protected archive path should trigger FDR-018", failures)

    protected_target_findings = validator.preflight_target(
        validator.WORKSPACE_ROOT / "state-private" / "federated-document-registry.yaml"
    )
    check(
        any(finding["rule_id"] == "FDR-TARGET" for finding in protected_target_findings),
        "protected validator target should trigger FDR-TARGET",
        failures,
    )

    outside_target_findings = validator.preflight_target(Path("/etc/hosts"))
    check(
        any(finding["rule_id"] == "FDR-TARGET" for finding in outside_target_findings),
        "outside validator target should trigger FDR-TARGET",
        failures,
    )

    symlink_path = ROOT / ".tmp-fdr-outside-link.yaml"
    remove_fixture_path(symlink_path)
    try:
        symlink_path.symlink_to(Path("/etc/hosts"))
        symlink_registry = validate_single(validator, registry_path=str(symlink_path))
        check(not symlink_registry["passed"], "workspace symlink to outside registry should fail", failures)
        check("FDR-003" in finding_ids(symlink_registry), "outside symlink registry should trigger FDR-003", failures)

        symlink_target_findings = validator.preflight_target(symlink_path)
        check(
            any(finding["rule_id"] == "FDR-TARGET" for finding in symlink_target_findings),
            "outside symlink validator target should trigger FDR-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(symlink_path)

    protected_symlink_path = ROOT / ".tmp-fdr-protected-link.yaml"
    remove_fixture_path(protected_symlink_path)
    try:
        protected_symlink_path.symlink_to(
            validator.WORKSPACE_ROOT / "state-private" / "federated-document-registry.yaml"
        )
        protected_symlink_registry = validate_single(validator, registry_path=str(protected_symlink_path))
        check(
            not protected_symlink_registry["passed"],
            "workspace symlink to protected registry should fail",
            failures,
        )
        check(
            "FDR-003" in finding_ids(protected_symlink_registry),
            "protected symlink registry should trigger FDR-003",
            failures,
        )

        protected_symlink_target_findings = validator.preflight_target(protected_symlink_path)
        check(
            any(finding["rule_id"] == "FDR-TARGET" for finding in protected_symlink_target_findings),
            "protected symlink validator target should trigger FDR-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(protected_symlink_path)

    loop_symlink_path = ROOT / ".tmp-fdr-loop-link.yaml"
    remove_fixture_path(loop_symlink_path)
    try:
        loop_symlink_path.symlink_to(loop_symlink_path.name)
        loop_symlink_registry = validate_single(validator, registry_path=str(loop_symlink_path))
        check(not loop_symlink_registry["passed"], "symlink loop registry should fail", failures)
        check("FDR-003" in finding_ids(loop_symlink_registry), "symlink loop registry should trigger FDR-003", failures)

        loop_symlink_target_findings = validator.preflight_target(loop_symlink_path)
        check(
            any(finding["rule_id"] == "FDR-TARGET" for finding in loop_symlink_target_findings),
            "symlink loop validator target should trigger FDR-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(loop_symlink_path)

    cli_env = dict(os.environ)
    cli_env["PYTHONDONTWRITEBYTECODE"] = "1"
    protected_cli_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "validate-federated-document-registry.py"),
            str(validator.WORKSPACE_ROOT / "state-private" / "federated-document-registry.yaml"),
            "--json",
        ],
        capture_output=True,
        text=True,
        env=cli_env,
        check=False,
    )
    check(protected_cli_result.returncode == 1, "protected CLI target should return failure", failures)
    try:
        protected_cli_data = json.loads(protected_cli_result.stdout)
    except json.JSONDecodeError:
        protected_cli_data = {}
        failures.append("protected CLI target should emit JSON")
    check(
        any(finding.get("rule_id") == "FDR-TARGET" for finding in protected_cli_data.get("registry_findings", [])),
        "protected CLI target should trigger FDR-TARGET",
        failures,
    )
    check(
        protected_cli_data.get("warnings", {}).get("target_read_performed") is False,
        "protected CLI target should not read target",
        failures,
    )

    cli_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "validate-federated-document-registry.py"),
            "/etc/hosts",
            "--json",
        ],
        capture_output=True,
        text=True,
        env=cli_env,
        check=False,
    )
    check(cli_result.returncode == 1, "outside CLI target should return failure", failures)
    try:
        cli_data = json.loads(cli_result.stdout)
    except json.JSONDecodeError:
        cli_data = {}
        failures.append("outside CLI target should emit JSON")
    check(
        any(finding.get("rule_id") == "FDR-TARGET" for finding in cli_data.get("registry_findings", [])),
        "outside CLI target should trigger FDR-TARGET",
        failures,
    )
    check(
        cli_data.get("warnings", {}).get("target_read_performed") is False,
        "outside CLI target should not read target",
        failures,
    )

    loop_cli_path = ROOT / ".tmp-fdr-cli-loop-link.yaml"
    remove_fixture_path(loop_cli_path)
    try:
        loop_cli_path.symlink_to(loop_cli_path.name)
        loop_cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "validate-federated-document-registry.py"),
                str(loop_cli_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            env=cli_env,
            check=False,
        )
        check(loop_cli_result.returncode == 1, "symlink loop CLI target should return failure", failures)
        try:
            loop_cli_data = json.loads(loop_cli_result.stdout)
        except json.JSONDecodeError:
            loop_cli_data = {}
            failures.append("symlink loop CLI target should emit JSON")
        check(
            any(finding.get("rule_id") == "FDR-TARGET" for finding in loop_cli_data.get("registry_findings", [])),
            "symlink loop CLI target should trigger FDR-TARGET",
            failures,
        )
        check(
            loop_cli_data.get("warnings", {}).get("target_read_performed") is False,
            "symlink loop CLI target should not read target",
            failures,
        )
    finally:
        remove_fixture_path(loop_cli_path)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=27 failures={len(failures)}")
        return 1

    print("PASS federated registry example")
    print("PASS missing registry_path fixture")
    print("PASS protected registry_path fixture")
    print("PASS outside registry_path fixture")
    print("PASS document count mismatch fixture")
    print("PASS duplicate id fixture")
    print("PASS duplicate path fixture")
    print("PASS failed child registry fixture")
    print("PASS non-integer expected_document_count fixture")
    print("PASS root metadata secret-like fixture")
    print("PASS known_external_scope review trigger fixture")
    print("PASS protected known_external_scope fixture")
    print("PASS registered known_external_scope fixture")
    print("PASS archive_note safe_use fixture")
    print("PASS archive_note replacement fixture")
    print("PASS protected archive_note fixture")
    print("PASS protected target fixture")
    print("PASS outside target fixture")
    print("PASS outside symlink registry fixture")
    print("PASS outside symlink target fixture")
    print("PASS protected CLI target fixture")
    print("PASS outside CLI target fixture")
    print("PASS protected symlink registry fixture")
    print("PASS protected symlink target fixture")
    print("PASS symlink loop registry fixture")
    print("PASS symlink loop target fixture")
    print("PASS symlink loop CLI target fixture")
    print("cases=27 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
