#!/usr/bin/env python3
"""Fixture tests for read-only ColaMeta executor preflight gate."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_preflight() -> ModuleType:
    module_path = ROOT / "colameta-executor-preflight.py"
    spec = importlib.util.spec_from_file_location("colameta_executor_preflight", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load preflight module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def authorization_flags_false(result: dict[str, object]) -> bool:
    return (
        result.get("executor_authorized") is False
        and result.get("service_start_authorized") is False
        and result.get("provider_call_authorized") is False
        and result.get("memory_write_authorized") is False
        and result.get("external_write_authorized") is False
    )


def main() -> int:
    preflight_module = load_preflight()
    failures: list[str] = []

    current = preflight_module.preflight()
    check(current["passed"], "current preflight should pass", failures)
    check(current["read_only"] is True, "preflight should be read-only", failures)
    check(current["summary_only"] is True, "preflight should be summary-only", failures)
    check(authorization_flags_false(current), "authorization flags should be false", failures)
    check(current.get("plan", {}).get("plan_loader_valid") is True, "plan loader should be valid", failures)
    check(current.get("plan", {}).get("lint_status") == "passed", "plan lint should pass", failures)
    check(current.get("prompts", {}).get("present_count") == 7, "seven prompt files should be present", failures)
    check(current.get("memory", {}).get("byte_count") == 0, "ColaMeta memory should remain empty", failures)

    protected = preflight_module.preflight(Path("state-private/plan.json"))
    check(not protected["passed"], "protected plan path should fail", failures)
    check(authorization_flags_false(protected), "protected failure should keep authorization flags false", failures)
    check(
        any(item.get("rule_id") == "COLAMETA-PREFLIGHT-PLAN" for item in protected.get("findings", [])),
        "protected plan should emit plan finding",
        failures,
    )

    missing = preflight_module.preflight(Path("control-plane/registry/missing-colameta-plan.json"))
    check(not missing["passed"], "missing plan path should fail", failures)
    check(authorization_flags_false(missing), "missing plan should keep authorization flags false", failures)

    cli_json = subprocess.run(
        [sys.executable, str(ROOT / "colameta-executor-preflight.py"), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_json.returncode == 0, "preflight JSON CLI should pass", failures)
    try:
        cli_data = json.loads(cli_json.stdout)
    except json.JSONDecodeError:
        cli_data = {}
        failures.append("preflight JSON CLI should emit JSON")
    check(authorization_flags_false(cli_data), "JSON CLI authorization flags should be false", failures)
    check(cli_data.get("warnings", {}).get("executor_ran") is False, "JSON CLI should report executor_ran=false", failures)

    cli_text = subprocess.run(
        [sys.executable, str(ROOT / "colameta-executor-preflight.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_text.returncode == 0, "preflight text CLI should pass", failures)
    check("Executor authorized: False" in cli_text.stdout, "text CLI should show executor_authorized=false", failures)
    check("Provider call authorized: False" in cli_text.stdout, "text CLI should show provider_call_authorized=false", failures)
    check("Memory write authorized: False" in cli_text.stdout, "text CLI should show memory_write_authorized=false", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=5 failures={len(failures)}")
        return 1

    print("PASS current preflight fixture")
    print("PASS protected plan fixture")
    print("PASS missing plan fixture")
    print("PASS preflight JSON CLI fixture")
    print("PASS preflight text CLI fixture")
    print("cases=5 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
