#!/usr/bin/env python3
"""Fixture tests for the local document registry validator."""

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
    module_path = ROOT / "validate-document-registry.py"
    spec = importlib.util.spec_from_file_location("document_registry_validator", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def finding_ids(result: dict) -> set[str]:
    return {
        finding["rule_id"]
        for item in result["documents"]
        for finding in item["findings"]
    } | {finding["rule_id"] for finding in result["registry_findings"]}


def one_doc(**overrides: object) -> dict:
    doc = {
        "id": "fixture-doc",
        "title": "Fixture Doc",
        "doc_type": "reference",
        "status": "active",
        "scope": "fixture only",
        "canonical_path": "control-plane/registry/README.md",
        "owner": {"human": "Jenn", "agent_steward": "Nobao"},
        "source_of_truth": "control-plane/registry/README.md",
        "supersedes": [],
        "superseded_by": None,
        "related": [],
        "last_reviewed": "2026-07-01",
        "review_by": "fixture",
        "freshness": {"level": "ordinary", "review_trigger": ["fixture changes"]},
        "security_boundary": ["no secrets"],
        "validation": {"notes": ["fixture"]},
    }
    doc.update(overrides)
    return doc


def validate_single(validator: ModuleType, **overrides: object) -> dict:
    return validator.validate_registry({"documents": [one_doc(**overrides)]})


def main() -> int:
    validator = load_validator()
    failures: list[str] = []

    example_path = ROOT / "drafts" / "document-registry.v0.1.example.yaml"
    data = validator.load_yaml(example_path)
    result = validator.validate_registry(data)
    document_ids = {
        item.get("id")
        for item in data.get("documents", [])
        if isinstance(item, dict)
    }
    required_document_ids = {
        "registry-readme",
        "golden-paths",
        "decision-records-guidance",
        "scorecard-guidance",
        "governance-control-plane-decision",
        "documentation-governance-draft",
        "documentation-governance-object-example",
        "governance-registry-validator",
        "document-registry-validator",
        "golden-path-scorecard-example",
    }
    check(result["passed"], "document registry example should pass scorecard", failures)
    check(
        required_document_ids.issubset(document_ids),
        "document registry is missing required document records",
        failures,
    )
    check(result["summary"]["fail"] == 0, "document registry should have no failures", failures)

    missing_owner = validate_single(validator, owner={})
    check(not missing_owner["passed"], "active document without owner should fail", failures)
    check("DOC-005" in finding_ids(missing_owner), "missing owner should trigger DOC-005", failures)

    missing_canonical = validate_single(validator, canonical_path="")
    check(not missing_canonical["passed"], "active document without canonical path should fail", failures)
    check(
        "DOC-006" in finding_ids(missing_canonical),
        "missing canonical path should trigger DOC-006",
        failures,
    )

    missing_source = validate_single(validator, source_of_truth="")
    check(not missing_source["passed"], "active document without source_of_truth should fail", failures)
    check("DOC-008" in finding_ids(missing_source), "missing source_of_truth should trigger DOC-008", failures)

    missing_title = validate_single(validator, title="")
    check(not missing_title["passed"], "document without required title should fail", failures)
    check("DOC-019" in finding_ids(missing_title), "missing title should trigger DOC-019", failures)

    missing_review_by = validate_single(validator, review_by="")
    check(not missing_review_by["passed"], "active document without review_by should fail", failures)
    check("DOC-013" in finding_ids(missing_review_by), "missing review_by should trigger DOC-013", failures)

    related_missing = validate_single(
        validator,
        related=["control-plane/registry/no-such-related-file.md"],
    )
    check(related_missing["passed"], "missing related path should warn but not fail", failures)
    check("DOC-011" in finding_ids(related_missing), "missing related path should trigger DOC-011", failures)

    secret_like = validate_single(
        validator,
        notes="sk-" + ("a" * 20),
    )
    check(not secret_like["passed"], "secret-like pattern should fail", failures)
    check("DOC-014" in finding_ids(secret_like), "secret-like pattern should trigger DOC-014", failures)

    draft_claims_active = validate_single(
        validator,
        status="draft",
        authority="active authority",
    )
    check(not draft_claims_active["passed"], "draft claiming active authority should fail", failures)
    check("DOC-009" in finding_ids(draft_claims_active), "draft active claim should trigger DOC-009", failures)

    superseded_missing_target = validate_single(
        validator,
        status="superseded",
        superseded_by=None,
    )
    check(
        superseded_missing_target["passed"],
        "superseded document missing superseded_by should warn but not fail",
        failures,
    )
    check(
        "DOC-010" in finding_ids(superseded_missing_target),
        "superseded missing target should trigger DOC-010",
        failures,
    )

    valid_lifecycle_transition = validate_single(
        validator,
        status="active",
        lifecycle_transition={"from": "draft", "to": "active"},
    )
    check(valid_lifecycle_transition["passed"], "valid lifecycle transition should pass", failures)

    invalid_lifecycle_transition = validate_single(
        validator,
        status="active",
        lifecycle_transition={"from": "archived", "to": "active"},
    )
    check(not invalid_lifecycle_transition["passed"], "invalid lifecycle transition should fail", failures)
    check(
        "DOC-020" in finding_ids(invalid_lifecycle_transition),
        "invalid lifecycle transition should trigger DOC-020",
        failures,
    )

    mismatched_lifecycle_transition = validate_single(
        validator,
        status="active",
        lifecycle_transition={"from": "draft", "to": "accepted"},
    )
    check(not mismatched_lifecycle_transition["passed"], "mismatched lifecycle target should fail", failures)
    check(
        "DOC-020" in finding_ids(mismatched_lifecycle_transition),
        "mismatched lifecycle target should trigger DOC-020",
        failures,
    )

    protected_path = validate_single(
        validator,
        canonical_path="state-private/private-note.md",
    )
    check(not protected_path["passed"], "protected canonical path should fail", failures)
    check("DOC-017" in finding_ids(protected_path), "protected canonical path should trigger DOC-017", failures)

    original_read_safe_text = validator.read_safe_text

    def fake_source_secret(path_value, findings, protected_rule_id, missing_rule_id, missing_level, label):
        if label == "source_of_truth":
            return "source contains " + "sk-" + ("a" * 20)
        return ""

    validator.read_safe_text = fake_source_secret
    source_secret = validate_single(validator)
    validator.read_safe_text = original_read_safe_text
    check(not source_secret["passed"], "source_of_truth content secret-like pattern should fail", failures)
    check(
        "DOC-014" in finding_ids(source_secret),
        "source_of_truth content secret-like pattern should trigger DOC-014",
        failures,
    )

    protected_related = validate_single(
        validator,
        related=["state-private/private-note.md"],
    )
    check(not protected_related["passed"], "protected related path should fail", failures)
    check("DOC-011" in finding_ids(protected_related), "protected related path should trigger DOC-011", failures)

    outside_related = validate_single(
        validator,
        related=["/etc/hosts"],
    )
    check(not outside_related["passed"], "outside related path should fail", failures)
    check("DOC-011" in finding_ids(outside_related), "outside related path should trigger DOC-011", failures)

    protected_target_findings = validator.preflight_target(
        validator.WORKSPACE_ROOT / "state-private" / "document-registry.yaml"
    )
    check(
        any(finding["rule_id"] == "DOC-TARGET" for finding in protected_target_findings),
        "protected validator target should trigger DOC-TARGET",
        failures,
    )

    outside_target_findings = validator.preflight_target(Path("/etc/hosts"))
    check(
        any(finding["rule_id"] == "DOC-TARGET" for finding in outside_target_findings),
        "outside validator target should trigger DOC-TARGET",
        failures,
    )

    outside_symlink_path = ROOT / ".tmp-doc-outside-link.md"
    remove_fixture_path(outside_symlink_path)
    try:
        outside_symlink_path.symlink_to(Path("/etc/hosts"))
        outside_symlink_doc = validate_single(validator, canonical_path=str(outside_symlink_path))
        check(not outside_symlink_doc["passed"], "workspace symlink to outside canonical path should fail", failures)
        check(
            "DOC-017" in finding_ids(outside_symlink_doc),
            "outside symlink canonical path should trigger DOC-017",
            failures,
        )

        outside_symlink_target_findings = validator.preflight_target(outside_symlink_path)
        check(
            any(finding["rule_id"] == "DOC-TARGET" for finding in outside_symlink_target_findings),
            "outside symlink validator target should trigger DOC-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(outside_symlink_path)

    protected_symlink_path = ROOT / ".tmp-doc-protected-link.md"
    remove_fixture_path(protected_symlink_path)
    try:
        protected_symlink_path.symlink_to(validator.WORKSPACE_ROOT / "state-private" / "document-registry.md")
        protected_symlink_doc = validate_single(validator, canonical_path=str(protected_symlink_path))
        check(not protected_symlink_doc["passed"], "workspace symlink to protected canonical path should fail", failures)
        check(
            "DOC-017" in finding_ids(protected_symlink_doc),
            "protected symlink canonical path should trigger DOC-017",
            failures,
        )

        protected_symlink_target_findings = validator.preflight_target(protected_symlink_path)
        check(
            any(finding["rule_id"] == "DOC-TARGET" for finding in protected_symlink_target_findings),
            "protected symlink validator target should trigger DOC-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(protected_symlink_path)

    loop_symlink_path = ROOT / ".tmp-doc-loop-link.md"
    remove_fixture_path(loop_symlink_path)
    try:
        loop_symlink_path.symlink_to(loop_symlink_path.name)
        loop_symlink_doc = validate_single(validator, canonical_path=str(loop_symlink_path))
        check(not loop_symlink_doc["passed"], "symlink loop canonical path should fail", failures)
        check("DOC-017" in finding_ids(loop_symlink_doc), "symlink loop canonical path should trigger DOC-017", failures)

        loop_symlink_target_findings = validator.preflight_target(loop_symlink_path)
        check(
            any(finding["rule_id"] == "DOC-TARGET" for finding in loop_symlink_target_findings),
            "symlink loop validator target should trigger DOC-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(loop_symlink_path)

    malformed_registry = validator.validate_registry({"documents": "not-a-list"})
    check(not malformed_registry["passed"], "malformed documents root should fail", failures)
    check("DOC-ROOT" in finding_ids(malformed_registry), "malformed documents root should trigger DOC-ROOT", failures)

    cli_env = dict(os.environ)
    cli_env["PYTHONDONTWRITEBYTECODE"] = "1"
    protected_cli_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "validate-document-registry.py"),
            str(validator.WORKSPACE_ROOT / "state-private" / "document-registry.yaml"),
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
        any(finding.get("rule_id") == "DOC-TARGET" for finding in protected_cli_data.get("registry_findings", [])),
        "protected CLI target should trigger DOC-TARGET",
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
            str(ROOT / "validate-document-registry.py"),
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
        any(finding.get("rule_id") == "DOC-TARGET" for finding in cli_data.get("registry_findings", [])),
        "outside CLI target should trigger DOC-TARGET",
        failures,
    )
    check(
        cli_data.get("warnings", {}).get("target_read_performed") is False,
        "outside CLI target should not read target",
        failures,
    )

    loop_cli_path = ROOT / ".tmp-doc-cli-loop-link.md"
    remove_fixture_path(loop_cli_path)
    try:
        loop_cli_path.symlink_to(loop_cli_path.name)
        loop_cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "validate-document-registry.py"),
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
            any(finding.get("rule_id") == "DOC-TARGET" for finding in loop_cli_data.get("registry_findings", [])),
            "symlink loop CLI target should trigger DOC-TARGET",
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
        print(f"cases=29 failures={len(failures)}")
        return 1

    print("PASS document registry example")
    print("PASS missing owner fixture")
    print("PASS missing canonical path fixture")
    print("PASS missing source_of_truth fixture")
    print("PASS missing title field-matrix fixture")
    print("PASS missing review_by strict fixture")
    print("PASS missing related path fixture")
    print("PASS secret-like fixture")
    print("PASS draft active-authority fixture")
    print("PASS superseded fixture")
    print("PASS valid lifecycle transition fixture")
    print("PASS invalid lifecycle transition fixture")
    print("PASS mismatched lifecycle transition fixture")
    print("PASS protected path fixture")
    print("PASS source_of_truth content secret fixture")
    print("PASS protected related path fixture")
    print("PASS outside related path fixture")
    print("PASS protected target fixture")
    print("PASS outside target fixture")
    print("PASS outside symlink canonical path fixture")
    print("PASS outside symlink target fixture")
    print("PASS protected symlink canonical path fixture")
    print("PASS protected symlink target fixture")
    print("PASS symlink loop canonical path fixture")
    print("PASS symlink loop target fixture")
    print("PASS malformed registry root fixture")
    print("PASS protected CLI target fixture")
    print("PASS outside CLI target fixture")
    print("PASS symlink loop CLI target fixture")
    print("cases=29 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
