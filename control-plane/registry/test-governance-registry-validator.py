#!/usr/bin/env python3
"""Fixture tests for the local governance registry scorecard validator."""

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
    module_path = ROOT / "validate-governance-registry.py"
    spec = importlib.util.spec_from_file_location("governance_registry_validator", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load validator from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    validator = load_validator()
    failures: list[str] = []

    example_path = ROOT / "drafts" / "agents-os-governance-registry.v0.1.example.yaml"
    data = validator.load_yaml(example_path)
    result = validator.validate_registry(data)
    object_ids = {
        item.get("id")
        for item in data.get("objects", [])
        if isinstance(item, dict)
    }
    required_object_ids = {
        "life-core",
        "policy-router",
        "task-envelope-system",
        "workspace-registry",
        "governance-golden-paths",
        "governance-decision-record-template",
        "governance-scorecard",
        "governance-registry-scorecard-validator",
        "decision-governance-control-plane-layer",
    }
    check(result["passed"], "draft registry example should pass scorecard", failures)
    check(
        required_object_ids.issubset(object_ids),
        "draft registry is missing required governance objects",
        failures,
    )
    check(
        result["summary"]["checked_objects"] >= len(required_object_ids),
        "draft registry should include required governance objects",
        failures,
    )
    check(result["summary"]["fail"] == 0, "draft registry should have no failures", failures)

    broken = {
        "objects": [
            {
                "id": "broken-object",
                "type": "validator",
                "status": "active",
                "path": "control-plane/registry/broken.py",
                "authority": "active authority",
            }
        ]
    }
    broken_result = validator.validate_registry(broken)
    broken_findings = {
        finding["rule_id"]
        for item in broken_result["objects"]
        for finding in item["findings"]
    }
    check(not broken_result["passed"], "broken registry should fail scorecard", failures)
    check("SC-005" in broken_findings, "broken active object should miss owner", failures)
    check("SC-007" in broken_findings, "broken object should miss red_zone", failures)
    check("SC-008" in broken_findings, "broken script-like object should miss validation", failures)

    secret_like = {
        "objects": [
            {
                "id": "secret-like",
                "type": "registry",
                "status": "draft",
                "path": "control-plane/registry/drafts/secret-like.yaml",
                "owner": {"human": "Jenn", "agent_steward": "Nobao"},
                "scope": "fixture only",
                "authority": "draft only, not active authority",
                "red_zone": ["do not store secrets"],
                "validation": {"notes": ["fixture"]},
                "evidence": ["fixture"],
                "last_receipt": "fixture",
                "last_review": "fixture",
                "notes": "sk-" + ("a" * 20),
            }
        ]
    }
    secret_result = validator.validate_registry(secret_like)
    secret_findings = {
        finding["rule_id"]
        for item in secret_result["objects"]
        for finding in item["findings"]
    }
    check(not secret_result["passed"], "secret-like registry should fail scorecard", failures)
    check("SC-012" in secret_findings, "secret-like registry should trigger SC-012", failures)

    malformed_registry = validator.validate_registry({"objects": "not-a-list"})
    malformed_findings = {finding["rule_id"] for finding in malformed_registry["registry_findings"]}
    check(not malformed_registry["passed"], "malformed objects root should fail", failures)
    check("SC-ROOT" in malformed_findings, "malformed objects root should trigger SC-ROOT", failures)

    protected_target_findings = validator.preflight_target(
        validator.WORKSPACE_ROOT / "state-private" / "governance-registry.yaml"
    )
    check(
        any(finding["rule_id"] == "SC-TARGET" for finding in protected_target_findings),
        "protected validator target should trigger SC-TARGET",
        failures,
    )

    outside_target_findings = validator.preflight_target(Path("/etc/hosts"))
    check(
        any(finding["rule_id"] == "SC-TARGET" for finding in outside_target_findings),
        "outside validator target should trigger SC-TARGET",
        failures,
    )

    outside_symlink_path = ROOT / ".tmp-governance-outside-link.yaml"
    remove_fixture_path(outside_symlink_path)
    try:
        outside_symlink_path.symlink_to(Path("/etc/hosts"))
        outside_symlink_findings = validator.preflight_target(outside_symlink_path)
        check(
            any(finding["rule_id"] == "SC-TARGET" for finding in outside_symlink_findings),
            "outside symlink validator target should trigger SC-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(outside_symlink_path)

    protected_symlink_path = ROOT / ".tmp-governance-protected-link.yaml"
    remove_fixture_path(protected_symlink_path)
    try:
        protected_symlink_path.symlink_to(
            validator.WORKSPACE_ROOT / "state-private" / "governance-registry.yaml"
        )
        protected_symlink_findings = validator.preflight_target(protected_symlink_path)
        check(
            any(finding["rule_id"] == "SC-TARGET" for finding in protected_symlink_findings),
            "protected symlink validator target should trigger SC-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(protected_symlink_path)

    loop_symlink_path = ROOT / ".tmp-governance-loop-link.yaml"
    remove_fixture_path(loop_symlink_path)
    try:
        loop_symlink_path.symlink_to(loop_symlink_path.name)
        loop_symlink_findings = validator.preflight_target(loop_symlink_path)
        check(
            any(finding["rule_id"] == "SC-TARGET" for finding in loop_symlink_findings),
            "symlink loop validator target should trigger SC-TARGET",
            failures,
        )
    finally:
        remove_fixture_path(loop_symlink_path)

    cli_env = dict(os.environ)
    cli_env["PYTHONDONTWRITEBYTECODE"] = "1"
    protected_cli_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "validate-governance-registry.py"),
            str(validator.WORKSPACE_ROOT / "state-private" / "governance-registry.yaml"),
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
        any(finding.get("rule_id") == "SC-TARGET" for finding in protected_cli_data.get("registry_findings", [])),
        "protected CLI target should trigger SC-TARGET",
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
            str(ROOT / "validate-governance-registry.py"),
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
        any(finding.get("rule_id") == "SC-TARGET" for finding in cli_data.get("registry_findings", [])),
        "outside CLI target should trigger SC-TARGET",
        failures,
    )
    check(
        cli_data.get("warnings", {}).get("target_read_performed") is False,
        "outside CLI target should not read target",
        failures,
    )

    loop_cli_path = ROOT / ".tmp-governance-cli-loop-link.yaml"
    remove_fixture_path(loop_cli_path)
    try:
        loop_cli_path.symlink_to(loop_cli_path.name)
        loop_cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "validate-governance-registry.py"),
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
            any(finding.get("rule_id") == "SC-TARGET" for finding in loop_cli_data.get("registry_findings", [])),
            "symlink loop CLI target should trigger SC-TARGET",
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
        print(f"cases=12 failures={len(failures)}")
        return 1

    print("PASS draft registry scorecard")
    print("PASS broken registry scorecard")
    print("PASS secret-like registry scorecard")
    print("PASS malformed registry root fixture")
    print("PASS protected target fixture")
    print("PASS outside target fixture")
    print("PASS outside symlink target fixture")
    print("PASS protected symlink target fixture")
    print("PASS symlink loop target fixture")
    print("PASS protected CLI target fixture")
    print("PASS outside CLI target fixture")
    print("PASS symlink loop CLI target fixture")
    print("cases=12 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
