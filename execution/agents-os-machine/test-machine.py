#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Machine Skeleton v0.1."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_machine() -> ModuleType:
    module_path = ROOT / "machine.py"
    spec = importlib.util.spec_from_file_location("agents_os_machine", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load machine module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def write_fixture(text: str) -> Path:
    temp_dir = tempfile.TemporaryDirectory(prefix="agents-os-machine-test-")
    path = Path(temp_dir.name) / "queue.md"
    path.write_text(text, encoding="utf-8")
    path._temp_dir = temp_dir  # type: ignore[attr-defined]
    return path


def main() -> int:
    machine = load_machine()
    failures: list[str] = []

    current = machine.load_queue()
    check(current["passed"], "current Active Work Queue should pass", failures)
    check(current["summary"]["now_count"] == 1, "current queue should have one NOW", failures)
    check(current["summary"]["item_count"] >= 1, "current queue should have at least one structured item", failures)
    check(current["summary"]["blocked_count"] >= 1, "current queue should keep blocked boundary entries", failures)
    check(current["summary"]["closed_count"] >= 1, "current queue should keep closed evidence entries", failures)

    preview = machine.build_preview(machine.now_item(current))
    check(preview["preview_only"] is True, "preview_only should be true", failures)
    check(preview["execution_authorized"] is False, "preview execution should not be authorized", failures)
    if preview["blocked"]:
        check(preview["actionable"] is False, "blocked current preview should be actionable=false", failures)
        check(
            preview["review_gate"]["requires_jenn_decision"] is True,
            "blocked current preview should require Jenn decision",
            failures,
        )
    else:
        check(preview["actionable"] is True, "unblocked preview should be actionable", failures)
    if "route_selection_required" in preview["denied_signals"]:
        check(
            preview["next_user_action"]["status"] == "route_choice_required",
            "route selection current preview should surface next user action",
            failures,
        )
        check(preview["next_user_action"]["decision_owner"] == "Jenn", "next user action owner should be Jenn", failures)
        check(
            preview["next_user_action"]["accepted_route_ids"] == ["A", "B", "C", "D", "E"],
            "next user action should surface accepted route ids",
            failures,
        )
        check(
            preview["next_user_action"]["active_queue_mutation_authorized"] is False,
            "next user action must not authorize active queue mutation",
            failures,
        )
        check(preview["next_user_action"]["execution_authorized"] is False, "next user action must not authorize execution", failures)
        readiness = preview["route_choice_adoption_bundle_readiness"]
        check(
            readiness["status"] == "waiting_for_jenn_route_choice",
            "route selection current preview should surface bundle readiness",
            failures,
        )
        check(readiness["decision_owner"] == "Jenn", "route bundle readiness owner should be Jenn", failures)
        check(readiness["bundle_preview_available"] is True, "route bundle preview evidence should be available", failures)
        check(readiness["can_apply_now"] is False, "route bundle readiness must not allow apply now", failures)
        check(
            readiness["route_adoption_authorized"] is False,
            "route bundle readiness must not authorize route adoption",
            failures,
        )
    check(preview["review_gate"]["requires_nobao_review"] is True, "preview should require Nobao review", failures)
    ok, failed_flags = machine.has_false_dangerous_flags(preview["authorization"])
    check(ok, f"preview dangerous flags should be false: {failed_flags}", failures)

    manifest = json.loads((ROOT / "machine-manifest.json").read_text(encoding="utf-8"))
    check(not machine.validate_manifest(manifest), "manifest should validate", failures)
    manifest["dangerous_authorization_defaults"]["provider_call_authorized"] = True
    check(machine.validate_manifest(manifest), "manifest with dangerous true should fail", failures)

    broken_preview = dict(preview)
    broken_preview["authorization"] = dict(preview["authorization"])
    broken_preview["authorization"]["provider_call_authorized"] = True
    check(machine.validate_preview(broken_preview), "preview with dangerous true should fail", failures)

    broken_next_action = dict(preview)
    broken_next_action["next_user_action"] = dict(preview["next_user_action"])
    broken_next_action["next_user_action"]["queue_promotion_authorized"] = True
    check(machine.validate_preview(broken_next_action), "preview with next user action queue promotion should fail", failures)

    broken_route_readiness = dict(preview)
    broken_route_readiness["route_choice_adoption_bundle_readiness"] = dict(preview["route_choice_adoption_bundle_readiness"])
    broken_route_readiness["route_choice_adoption_bundle_readiness"]["route_adoption_authorized"] = True
    check(machine.validate_preview(broken_route_readiness), "preview with route adoption readiness authorization should fail", failures)

    schema = json.loads((ROOT / "queue-item.schema.json").read_text(encoding="utf-8"))
    schema_item = dict(machine.now_item(current))
    schema_item["authorization"] = dict(schema_item["authorization"])
    schema_item["authorization"]["provider_call_authorized"] = True
    check(machine.validate_queue_item(schema_item, schema), "schema required_false should fail dangerous true", failures)

    no_now = machine.parse_queue_markdown(
        """# fixture

## NEXT

### NEXT-001: Later task

Goal: wait.
""",
        Path("fixture-no-now.md"),
    )
    check(not no_now["passed"], "queue without NOW should fail", failures)

    multiple_now = machine.parse_queue_markdown(
        """# fixture

## NOW

### NOW-001: First

Goal: one.

### NOW-002: Second

Goal: two.
""",
        Path("fixture-multiple-now.md"),
    )
    check(not multiple_now["passed"], "queue with multiple NOW should fail", failures)

    p3_queue = machine.parse_queue_markdown(
        """# fixture

## NOW

### NOW-001: Call provider

Goal: call provider and start service.
""",
        Path("fixture-p3.md"),
    )
    check(p3_queue["passed"], "P3 fixture structure should parse", failures)
    p3_preview = machine.build_preview(machine.now_item(p3_queue))
    check(p3_preview["blocked"] is True, "P3 signal preview should be blocked", failures)
    check(p3_preview["actionable"] is False, "P3 signal preview should be actionable=false", failures)
    check(p3_preview["review_gate"]["requires_jenn_decision"] is True, "P3 signal should require Jenn", failures)
    check(p3_preview["execution_authorized"] is False, "P3 signal should not authorize execution", failures)
    check(p3_preview["next_user_action"]["status"] == "none", "P3-only signal should not become route choice handoff", failures)

    negated_queue = machine.parse_queue_markdown(
        """# fixture

## NOW

### NOW-001: Local no-provider task

Goal: do local documentation only.
Do not call provider. Do not start service. Do not run executor.
""",
        Path("fixture-negated-signals.md"),
    )
    check(negated_queue["passed"], "negated signal fixture structure should parse", failures)
    negated_preview = machine.build_preview(machine.now_item(negated_queue))
    check(negated_preview["blocked"] is False, "negated boundary statements should not block preview", failures)
    check(negated_preview["actionable"] is True, "negated boundary preview should remain actionable", failures)
    check(
        negated_preview["route_choice_adoption_bundle_readiness"]["status"] == "not_active",
        "non-route preview bundle readiness should be not_active",
        failures,
    )

    route_selection_queue = machine.parse_queue_markdown(
        """# fixture

## NOW

### NOW-001: No Active Automatic Construction Item

Goal: hold the queue after closing the current autonomous governance sequence.

```text
requires_jenn_route_choice=true
```
""",
        Path("fixture-route-selection-stop.md"),
    )
    check(route_selection_queue["passed"], "route selection fixture structure should parse", failures)
    route_selection_preview = machine.build_preview(machine.now_item(route_selection_queue))
    check(route_selection_preview["blocked"] is True, "route selection stop-state should be blocked", failures)
    check(route_selection_preview["actionable"] is False, "route selection stop-state should be actionable=false", failures)
    check(
        route_selection_preview["review_gate"]["requires_jenn_decision"] is True,
        "route selection stop-state should require Jenn decision",
        failures,
    )
    check(
        "route_selection_required" in route_selection_preview["denied_signals"],
        "route selection signal should be recorded",
        failures,
    )
    check(
        route_selection_preview["next_user_action"]["status"] == "route_choice_required",
        "route selection stop-state should surface route choice handoff",
        failures,
    )
    check(
        route_selection_preview["next_user_action"]["decision_owner"] == "Jenn",
        "route selection handoff owner should be Jenn",
        failures,
    )
    check(
        route_selection_preview["next_user_action"]["accepted_route_ids"] == ["A", "B", "C", "D", "E"],
        "route selection handoff should include accepted route ids",
        failures,
    )
    check(
        route_selection_preview["next_user_action"]["queue_promotion_authorized"] is False,
        "route selection handoff must not authorize queue promotion",
        failures,
    )
    check(
        route_selection_preview["route_choice_adoption_bundle_readiness"]["status"] == "waiting_for_jenn_route_choice",
        "route selection stop-state should surface bundle readiness",
        failures,
    )
    check(
        route_selection_preview["route_choice_adoption_bundle_readiness"]["bundle_preview_available"] is True,
        "route selection bundle readiness should confirm bundle preview evidence",
        failures,
    )
    check(
        route_selection_preview["route_choice_adoption_bundle_readiness"]["can_apply_now"] is False,
        "route selection bundle readiness must keep can_apply_now=false",
        failures,
    )

    external_queue = machine.parse_queue_markdown(
        """# fixture

## NOW

### NOW-001: Write to Notion

Goal: write to Notion and create GitHub issue.
""",
        Path("fixture-external-write.md"),
    )
    check(external_queue["passed"], "external write fixture structure should parse", failures)
    external_preview = machine.build_preview(machine.now_item(external_queue))
    check(external_preview["blocked"] is True, "external write signal should be blocked", failures)
    check("external_write" in external_preview["denied_signals"], "external write signal should be detected", failures)
    check(external_preview["actionable"] is False, "external write preview should be actionable=false", failures)

    database_queue = machine.parse_queue_markdown(
        """# fixture

## NOW

### NOW-001: Database write

Goal: perform a database write.
""",
        Path("fixture-database-write.md"),
    )
    database_preview = machine.build_preview(machine.now_item(database_queue))
    check("database_write" in database_preview["denied_signals"], "database write signal should be detected", failures)

    protected_queue = machine.load_queue(Path("state-private/queue.md"))
    check(not protected_queue["passed"], "protected queue path should fail before read", failures)
    check(protected_queue.get("path_findings"), "protected queue path should include path findings", failures)

    envelope_validation = machine.validate_task_envelope_preview(preview["task_envelope_markdown"])
    check(envelope_validation["passed"], "temporary task envelope preview should validate", failures)
    check(envelope_validation["temporary_preview_cleaned"] is True, "temporary preview should be cleaned", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=16 failures={len(failures)}")
        return 1

    print("PASS current queue fixture")
    print("PASS preview authorization fixture")
    print("PASS manifest authorization fixture")
    print("PASS no NOW fixture")
    print("PASS multiple NOW fixture")
    print("PASS P3 signal fixture")
    print("PASS negated boundary signal fixture")
    print("PASS route selection stop-state fixture")
    print("PASS next user action fixture")
    print("PASS route choice adoption bundle readiness fixture")
    print("PASS task-envelope temporary validation fixture")
    print("cases=16 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
