#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Dashboard v0.1."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_dashboard() -> ModuleType:
    module_path = ROOT / "dashboard.py"
    spec = importlib.util.spec_from_file_location("agents_os_dashboard", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load dashboard module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    dashboard = load_dashboard()
    failures: list[str] = []

    summary = dashboard.build_dashboard_summary(run_validations=True)
    machine = dashboard.load_machine()
    expected_now = machine.now_item(machine.load_queue())["title"]
    check(summary["passed"], f"current dashboard summary should pass: {summary['errors']}", failures)
    check(summary["preview_only"] is True, "dashboard summary should be preview_only", failures)
    check(summary["read_only"] is True, "dashboard summary should be read_only", failures)
    check(summary["write_performed"] is False, "dashboard summary should not write", failures)
    check(summary["execution_authorized"] is False, "dashboard should not authorize execution", failures)
    check(summary["queue"]["now"]["title"] == expected_now, "dashboard should surface current NOW", failures)
    check(
        summary["route_selection"]["status"] == "awaiting_jenn_selection",
        "dashboard route selection should await Jenn after MEHS terminal closeout",
        failures,
    )
    check(
        summary["route_selection"]["requires_jenn_decision"] is True,
        "route selection should require Jenn after MEHS terminal closeout",
        failures,
    )
    check(summary["route_selection"]["route_auto_selection_authorized"] is False, "route selection must not authorize auto-selection", failures)
    check(summary["route_selection"]["queue_promotion_authorized"] is False, "route selection must not authorize queue promotion", failures)
    check(summary["route_selection"]["execution_authorized"] is False, "route selection must not authorize execution", failures)
    check(summary["route_selection"]["option_count"] == 5, "dashboard should surface five route options", failures)
    check(
        summary["next_user_action"]["status"] == "route_choice_required",
        "MEHS terminal closeout should return the next action to route choice",
        failures,
    )
    check(summary["next_user_action"]["decision_owner"] == "Jenn", "MEHS route choice owner should be Jenn", failures)
    check(summary["next_user_action"]["requires_jenn_decision"] is True, "MEHS route choice should require Jenn", failures)
    check(summary["next_user_action"]["accepted_route_ids"] == ["A", "B", "C", "D", "E"], "MEHS route choice should surface route ids", failures)
    check(summary["next_user_action"]["exact_confirmation_templates_available"] is True, "MEHS route choice should surface confirmation templates", failures)
    check(
        summary["next_user_action"]["active_queue_mutation_authorized"] is False,
        "next user action must not authorize active queue mutation",
        failures,
    )
    check(
        summary["next_user_action"]["queue_promotion_authorized"] is False,
        "next user action must not authorize queue promotion",
        failures,
    )
    check(summary["next_user_action"]["execution_authorized"] is False, "next user action must not authorize execution", failures)
    check(summary["route_adoption_gate"]["status"] == "waiting_for_jenn_route_choice", "dashboard route adoption gate should await Jenn", failures)
    check(summary["route_adoption_gate"]["all_required_gates_present"] is True, "dashboard should surface required route adoption gates", failures)
    check(summary["route_adoption_gate"]["future_apply_gate_available"] is True, "dashboard should surface future apply gate availability", failures)
    check(summary["route_adoption_gate"]["can_apply_now"] is False, "route adoption gate must not apply before Jenn route choice", failures)
    check(summary["route_adoption_gate"]["requires_jenn_decision"] is True, "route adoption gate should require Jenn", failures)
    check(summary["route_adoption_gate"]["active_queue_mutation_authorized"] is False, "route adoption gate must not authorize active queue mutation", failures)
    check(summary["route_adoption_gate"]["queue_promotion_authorized"] is False, "route adoption gate must not authorize queue promotion", failures)
    check(summary["route_adoption_gate"]["execution_authorized"] is False, "route adoption gate must not authorize execution", failures)
    check(
        summary["route_choice_adoption_bundle"]["status"] == "waiting_for_jenn_route_choice",
        "dashboard route choice adoption bundle should await Jenn",
        failures,
    )
    check(summary["route_choice_adoption_bundle"]["bundle_preview_available"] is True, "route adoption bundle preview should be available", failures)
    check(summary["route_choice_adoption_bundle"]["can_apply_now"] is False, "route adoption bundle must not apply before Jenn route choice", failures)
    check(summary["route_choice_adoption_bundle"]["requires_jenn_decision"] is True, "route adoption bundle should require Jenn", failures)
    check(summary["route_choice_adoption_bundle"]["preview_only"] is True, "route adoption bundle should be preview_only", failures)
    check(summary["route_choice_adoption_bundle"]["read_only"] is True, "route adoption bundle should be read_only", failures)
    check(summary["route_choice_adoption_bundle"]["active_queue_mutation_authorized"] is False, "route adoption bundle must not authorize active queue mutation", failures)
    check(summary["route_choice_adoption_bundle"]["route_adoption_authorized"] is False, "route adoption bundle must not authorize route adoption", failures)
    check(summary["route_choice_adoption_bundle"]["execution_authorized"] is False, "route adoption bundle must not authorize execution", failures)
    check(summary["route_choice_adoption_bundle"]["raw_confirmation_text_output"] is False, "route adoption bundle must not output raw confirmation text", failures)
    check(summary["route_choice_adoption_bundle"]["raw_template_output"] is False, "route adoption bundle must not output raw template", failures)
    check(summary["last_completed"]["status"] == "present", "dashboard should surface last CLOSED item", failures)
    check(summary["open_blockers"], "dashboard should surface open blockers", failures)
    check(summary["validation_status"]["passed"] is True, "dashboard should surface passing validation status", failures)
    check(summary["formal_memory_write_authorized"] is False, "dashboard must not authorize formal Memory write", failures)
    check(summary["private_memory_raw_read_authorized"] is False, "dashboard must not authorize private raw Memory read", failures)

    memory_candidates = summary["memory_candidates"]
    check(memory_candidates, "dashboard should produce Memory candidates", failures)
    for candidate in memory_candidates:
        check(candidate["candidate_only"] is True, "Memory candidate should be candidate_only", failures)
        check(candidate["formal_memory_write_authorized"] is False, "Memory candidate must not authorize Memory write", failures)
        check(candidate["memory_write_performed"] is False, "Memory candidate must not perform Memory write", failures)
        check(candidate["private_memory_raw_read"] is False, "Memory candidate must not read private raw Memory", failures)
        check(candidate["requires_jenn_confirmation"] is True, "Memory candidate should require Jenn confirmation", failures)

    no_validation = dashboard.build_dashboard_summary(run_validations=False)
    check(no_validation["passed"], f"summary without validation should still pass: {no_validation['errors']}", failures)
    check(no_validation["validation_status"]["checked"] is False, "no-validation summary should mark validation unchecked", failures)

    manifest = json.loads((ROOT / "dashboard-manifest.json").read_text(encoding="utf-8"))
    check(not dashboard.validate_manifest(manifest), "dashboard manifest should validate", failures)
    manifest["authorization_defaults"]["provider_call_authorized"] = True
    check(dashboard.validate_manifest(manifest), "manifest with dangerous true should fail", failures)

    broken = dict(summary)
    broken["authorization"] = dict(summary["authorization"])
    broken["authorization"]["provider_call_authorized"] = True
    check(dashboard.validate_dashboard_summary(broken), "summary with dangerous authorization should fail", failures)

    broken_candidate = dict(memory_candidates[0])
    broken_candidate["formal_memory_write_authorized"] = True
    check(dashboard.validate_memory_candidate(broken_candidate), "Memory candidate authorizing Memory write should fail", failures)

    broken_route = dict(summary)
    broken_route["route_selection"] = dict(summary["route_selection"])
    broken_route["route_selection"]["route_auto_selection_authorized"] = True
    check(dashboard.validate_dashboard_summary(broken_route), "route auto-selection authorization should fail", failures)

    broken_next_user_action = dict(summary)
    broken_next_user_action["next_user_action"] = dict(summary["next_user_action"])
    broken_next_user_action["next_user_action"]["queue_promotion_authorized"] = True
    check(dashboard.validate_dashboard_summary(broken_next_user_action), "next user action queue promotion authorization should fail", failures)

    broken_adoption_gate = dict(summary)
    broken_adoption_gate["route_adoption_gate"] = dict(summary["route_adoption_gate"])
    broken_adoption_gate["route_adoption_gate"]["active_queue_mutation_authorized"] = True
    check(dashboard.validate_dashboard_summary(broken_adoption_gate), "route adoption active queue mutation authorization should fail", failures)

    broken_adoption_bundle = dict(summary)
    broken_adoption_bundle["route_choice_adoption_bundle"] = dict(summary["route_choice_adoption_bundle"])
    broken_adoption_bundle["route_choice_adoption_bundle"]["route_adoption_authorized"] = True
    check(dashboard.validate_dashboard_summary(broken_adoption_bundle), "route adoption bundle route adoption authorization should fail", failures)

    with tempfile.TemporaryDirectory(prefix="agents-os-dashboard-route-stop-test-", dir=dashboard.WORKSPACE_ROOT) as route_temp_dir:
        route_fixture = Path(route_temp_dir) / "route-stop-queue.md"
        route_fixture.write_text(
            """# route stop fixture

## NOW

### NOW-001: No Active Automatic Construction Item

Waiting for Jenn route selection.

## NEXT

_No active NEXT items._

## CLOSED

```text
old_task: closed
```
""",
            encoding="utf-8",
        )
        route_fixture_summary = dashboard.build_dashboard_summary(route_fixture, run_validations=False)
        check(route_fixture_summary["passed"], f"route stop fixture should pass: {route_fixture_summary['errors']}", failures)
        check(route_fixture_summary["route_selection"]["status"] == "awaiting_jenn_selection", "route stop fixture should require route selection", failures)
        check(route_fixture_summary["route_selection"]["requires_jenn_decision"] is True, "route stop fixture route selection should require Jenn", failures)
        check(route_fixture_summary["next_user_action"]["status"] == "route_choice_required", "route stop fixture should surface route choice next action", failures)
        check(route_fixture_summary["next_user_action"]["decision_owner"] == "Jenn", "route stop fixture next action owner should be Jenn", failures)
        check(
            route_fixture_summary["next_user_action"]["accepted_route_ids"] == ["A", "B", "C", "D", "E"],
            "route stop fixture should surface route choices A-E",
            failures,
        )
        check(
            route_fixture_summary["next_user_action"]["exact_confirmation_templates_available"] is True,
            "route stop fixture should surface available confirmation templates",
            failures,
        )
        check(route_fixture_summary["route_adoption_gate"]["status"] == "waiting_for_jenn_route_choice", "route stop fixture adoption gate should wait", failures)
        check(route_fixture_summary["route_choice_adoption_bundle"]["status"] == "waiting_for_jenn_route_choice", "route stop fixture adoption bundle should wait", failures)

    with tempfile.TemporaryDirectory(prefix="agents-os-dashboard-test-", dir=dashboard.WORKSPACE_ROOT) as temp_dir:
        fixture = Path(temp_dir) / "queue.md"
        fixture.write_text(
            """# fixture queue

## NOW

### NOW-001: Fixture dashboard task

Goal: show state.

## NEXT

### NEXT-001: Fixture next

Wait.

## BLOCKED

```text
provider_calls: blocked
formal_memory_write: blocked
```

## CLOSED

```text
first_closed: old
latest_closed: new
```
""",
            encoding="utf-8",
        )
        fixture_summary = dashboard.build_dashboard_summary(fixture, run_validations=False)
        check(fixture_summary["passed"], f"fixture dashboard summary should pass: {fixture_summary['errors']}", failures)
        check(fixture_summary["queue"]["now"]["title"] == "Fixture dashboard task", "fixture NOW should surface", failures)
        check(fixture_summary["route_selection"]["status"] == "not_active", "fixture route selection should be inactive", failures)
        check(fixture_summary["next_user_action"]["status"] == "none", "fixture next user action should be inactive", failures)
        check(fixture_summary["route_adoption_gate"]["status"] == "not_active", "fixture route adoption gate should be inactive", failures)
        check(fixture_summary["route_choice_adoption_bundle"]["status"] == "not_active", "fixture route adoption bundle should be inactive", failures)
        check(fixture_summary["last_completed"]["text"] == "latest_closed: new", "latest CLOSED should surface", failures)
        check(len(fixture_summary["open_blockers"]) == 2, "fixture blockers should surface", failures)

        p3_fixture = Path(temp_dir) / "p3-queue.md"
        p3_fixture.write_text(
            """# P3 fixture queue

## NOW

### NOW-001: Call provider

Call provider and start service.

## NEXT

_No active NEXT items._

## CLOSED

```text
old_task: closed
```
""",
            encoding="utf-8",
        )
        p3_summary = dashboard.build_dashboard_summary(p3_fixture, run_validations=False)
        check(p3_summary["passed"], f"P3 dashboard summary should pass as blocked state: {p3_summary['errors']}", failures)
        check(p3_summary["queue"]["now"]["blocked"] is True, "P3 dashboard NOW should preserve blocked=true", failures)
        check(
            p3_summary["queue"]["now"]["review_requires_jenn_decision"] is True,
            "P3 dashboard NOW should preserve Jenn review requirement",
            failures,
        )
        check(
            p3_summary["next_user_action"]["status"] == "governance_decision_required",
            "P3 dashboard next action should require governance decision",
            failures,
        )
        check(p3_summary["next_user_action"]["decision_owner"] == "Jenn", "P3 dashboard next action owner should be Jenn", failures)

    protected_summary = dashboard.build_dashboard_summary(Path("state-private/queue.md"), run_validations=False)
    check(not protected_summary["passed"], "protected queue path should fail before read", failures)

    validation = dashboard.validate_dashboard(run_validations=False)
    check(validation["passed"], f"dashboard validation without docctl should pass: {validation['errors']}", failures)
    check(validation["formal_memory_write_authorized"] is False, "validation should keep Memory write unauthorized", failures)
    check(validation["private_memory_raw_read_authorized"] is False, "validation should keep private Memory read unauthorized", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=17 failures={len(failures)}")
        return 1

    print("PASS current dashboard summary fixture")
    print("PASS validation status fixture")
    print("PASS memory candidate no-write fixture")
    print("PASS route selection visibility fixture")
    print("PASS next user action fixture")
    print("PASS route adoption gate visibility fixture")
    print("PASS route adoption bundle visibility fixture")
    print("PASS manifest authorization fixture")
    print("PASS route selection wait-state fixture")
    print("PASS fixture queue summary fixture")
    print("PASS protected path fixture")
    print("cases=17 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
