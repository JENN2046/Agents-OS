#!/usr/bin/env python3
"""Fixture tests for PR risk review helper."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_review() -> ModuleType:
    module_path = ROOT / "pr-risk-review.py"
    spec = importlib.util.spec_from_file_location("pr_risk_review", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def surface_ids(result: dict) -> set[str]:
    return {surface["surface_id"] for surface in result.get("risk_surfaces", [])}


def main() -> int:
    review = load_review()
    failures: list[str] = []

    runtime = review.classify_paths(
        [
            "execution/codex-appserver-active-loop/package.json",
            "execution/codex-appserver-active-loop/src/bridge/repo_snapshot.ts",
        ],
        include_content=False,
    )
    check(runtime["proof_matrix_required"] is True, "runtime paths should require proof matrix", failures)
    check(
        "runtime_provenance_package_file_set" in surface_ids(runtime),
        "runtime paths should trigger runtime provenance surface",
        failures,
    )
    runtime_surface = next(
        surface for surface in runtime["risk_surfaces"] if surface["surface_id"] == "runtime_provenance_package_file_set"
    )
    check(
        "extra installed-only runtime file" in runtime_surface["negative_cases"],
        "runtime surface should require extra installed-only negative case",
        failures,
    )

    gate = review.classify_paths(
        ["control-plane/registry/docctl.py", "control-plane/registry/validate-document-registry.py"],
        include_content=False,
    )
    check("readiness_gate" in surface_ids(gate), "validator/docctl paths should trigger readiness gate surface", failures)
    check(
        "status_enum_operator_contract" in surface_ids(gate),
        "docctl/status paths should trigger status contract surface",
        failures,
    )

    auth_redaction = review.classify_paths(
        ["execution/runner/auth_proxy.py", "execution/runner/redaction_policy.py"],
        include_content=False,
    )
    check(
        "public_endpoint_oauth_auth_routing" in surface_ids(auth_redaction),
        "auth path should trigger public endpoint/auth surface",
        failures,
    )
    check(
        "redaction_secret_handling" in surface_ids(auth_redaction),
        "redaction path should trigger secret handling surface",
        failures,
    )

    docs_only = review.classify_paths(
        ["ops/records/colameta-pr-retrospectives/2026-07-09-pr12-installed-only-runtime-file-detection.md"],
        include_content=False,
    )
    check(docs_only["proof_matrix_required"] is False, "docs-only retrospective path should not require proof matrix", failures)

    cli_json = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pr-risk-review.py"),
            "--paths",
            "execution/codex-appserver-active-loop/package.json",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_json.returncode == 0, "CLI JSON should pass without strict mode", failures)
    try:
        cli_payload = json.loads(cli_json.stdout)
    except json.JSONDecodeError:
        cli_payload = {}
        failures.append("CLI JSON should parse")
    check(cli_payload.get("proof_matrix_required") is True, "CLI JSON should report proof matrix requirement", failures)

    cli_strict = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pr-risk-review.py"),
            "--paths",
            "execution/codex-appserver-active-loop/package.json",
            "--strict",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_strict.returncode == 1, "CLI strict mode should fail when proof matrix is required", failures)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        handle.write('password = "should-not-be-read"\n')
        outside_path = handle.name
    try:
        cli_absolute = subprocess.run(
            [
                sys.executable,
                str(ROOT / "pr-risk-review.py"),
                "--paths",
                outside_path,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        Path(outside_path).unlink(missing_ok=True)
    check(cli_absolute.returncode == 2, "CLI should reject absolute paths", failures)
    try:
        absolute_payload = json.loads(cli_absolute.stdout)
    except json.JSONDecodeError:
        absolute_payload = {}
        failures.append("CLI absolute path JSON should parse")
    check(absolute_payload.get("path_input_valid") is False, "absolute path should be invalid", failures)
    check(absolute_payload.get("risk_surface_count") == 0, "absolute path should not be content-scanned", failures)

    cli_traversal = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pr-risk-review.py"),
            "--paths",
            "../outside.py",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_traversal.returncode == 2, "CLI should reject parent traversal paths", failures)
    try:
        traversal_payload = json.loads(cli_traversal.stdout)
    except json.JSONDecodeError:
        traversal_payload = {}
        failures.append("CLI traversal JSON should parse")
    check(traversal_payload.get("path_input_valid") is False, "parent traversal path should be invalid", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=8 failures={len(failures)}")
        return 1

    print("PASS runtime provenance risk fixture")
    print("PASS readiness/status risk fixture")
    print("PASS auth/redaction risk fixture")
    print("PASS docs-only no-risk fixture")
    print("PASS CLI JSON fixture")
    print("PASS CLI strict fixture")
    print("PASS CLI absolute path rejection fixture")
    print("PASS CLI parent traversal rejection fixture")
    print("cases=8 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
