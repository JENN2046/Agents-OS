#!/usr/bin/env python3
"""Fixture tests for read-only docctl apply-fix preview mode."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_docctl() -> ModuleType:
    module_path = ROOT / "docctl.py"
    spec = importlib.util.spec_from_file_location("docctl", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load docctl from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def no_write_flags(result: dict[str, object]) -> bool:
    return (
        result.get("would_write") is False
        and result.get("write_performed") is False
        and result.get("patch_created") is False
        and result.get("snapshot_write_performed") is False
        and result.get("execution_authorized") is False
        and result.get("registry_write_performed") is False
        and result.get("external_write_performed") is False
        and result.get("provider_call_performed") is False
    )


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []

    current = docctl.apply_fix_preview("PF-0001")
    proposal = current.get("proposal") if isinstance(current.get("proposal"), dict) else {}
    check(current["passed"], "current apply-fix preview should pass", failures)
    check(current["preview_only"] is True, "preview should report preview_only=true", failures)
    check(no_write_flags(current), "preview should report all write flags false", failures)
    check(
        proposal.get("proposal_category") in {"no_action_needed", "register_missing_document"},
        "current preview should expose a plan-fix proposal",
        failures,
    )

    missing = docctl.apply_fix_preview("PF-9999")
    check(not missing["passed"], "missing proposal id should fail", failures)
    check(missing["preview_status"] == "proposal_not_found", "missing proposal should report proposal_not_found", failures)
    check(no_write_flags(missing), "missing proposal should not write", failures)
    check(missing.get("findings", [{}])[0].get("rule_id") == "DOCCTL-APPLY-FIX-PREVIEW", "missing proposal should emit preview finding", failures)

    protected = docctl.apply_fix_preview("PF-0001", Path("state-private/federated.yaml"))
    protected_proposal = protected.get("proposal") if isinstance(protected.get("proposal"), dict) else {}
    check(not protected["passed"], "protected target preview should fail", failures)
    check(protected["preview_status"] == "blocked", "protected target should report blocked", failures)
    check(protected_proposal.get("proposal_category") == "blocked_protected_path", "protected target should keep blocked proposal category", failures)
    check(no_write_flags(protected), "protected target should not write", failures)

    cli_json = subprocess.run(
        [
            sys.executable,
            str(ROOT / "docctl.py"),
            "apply-fix",
            "--preview",
            "PF-0001",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_json.returncode == 0, "apply-fix preview JSON CLI should pass on current registry", failures)
    try:
        cli_data = json.loads(cli_json.stdout)
    except json.JSONDecodeError:
        cli_data = {}
        failures.append("apply-fix preview JSON CLI should emit JSON")
    check(cli_data.get("preview_only") is True, "JSON CLI should report preview_only=true", failures)
    check(no_write_flags(cli_data), "JSON CLI should report all write flags false", failures)

    cli_text = subprocess.run(
        [
            sys.executable,
            str(ROOT / "docctl.py"),
            "apply-fix",
            "--preview",
            "PF-0001",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_text.returncode == 0, "apply-fix preview text CLI should pass on current registry", failures)
    check("Preview only: True" in cli_text.stdout, "text CLI should show preview_only", failures)
    check("Patch created: False" in cli_text.stdout, "text CLI should show patch_created=false", failures)
    check("Execution authorized: False" in cli_text.stdout, "text CLI should show execution_authorized=false", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=5 failures={len(failures)}")
        return 1

    print("PASS current no-action preview fixture")
    print("PASS missing proposal fixture")
    print("PASS protected target fixture")
    print("PASS apply-fix preview JSON CLI fixture")
    print("PASS apply-fix preview text CLI fixture")
    print("cases=5 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
