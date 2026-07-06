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
    check(current["summary"]["next_count"] == 2, "current queue should have two NEXT items", failures)
    check(current["summary"]["later_count"] == 4, "current queue should have four LATER items", failures)
    check(current["summary"]["blocked_count"] == 6, "current queue should have six BLOCKED entries", failures)
    check(current["summary"]["closed_count"] == 5, "current queue should have five CLOSED entries", failures)

    preview = machine.build_preview(machine.now_item(current))
    check(preview["preview_only"] is True, "preview_only should be true", failures)
    check(preview["execution_authorized"] is False, "preview execution should not be authorized", failures)
    check(preview["actionable"] is True, "unblocked preview should be actionable", failures)
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
        print(f"cases=8 failures={len(failures)}")
        return 1

    print("PASS current queue fixture")
    print("PASS preview authorization fixture")
    print("PASS manifest authorization fixture")
    print("PASS no NOW fixture")
    print("PASS multiple NOW fixture")
    print("PASS P3 signal fixture")
    print("PASS task-envelope temporary validation fixture")
    print("cases=12 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
