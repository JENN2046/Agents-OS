#!/usr/bin/env python3
"""Fixture tests for the local task-envelope loop runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_loop() -> ModuleType:
    module_path = ROOT / "run-task-envelope-loop.py"
    spec = importlib.util.spec_from_file_location("task_envelope_loop", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load loop from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    loop = load_loop()
    failures: list[str] = []

    example = ROOT / "examples" / "2026-06-30-example-local-task-envelope-loop.md"
    example_result = loop.run_loop(
        example,
        write_local_receipt=False,
        run_date="2026-06-30",
    )
    check(example_result["gate"]["status"] == "ALLOW", "example should be allowed", failures)
    check(example_result["gate"]["color_zone"] == "绿色区", "example should route green", failures)
    check(example_result["router"]["decision"] == "allowed", "example router decision", failures)
    check(example_result["router"]["permission_level"] == "A2", "example permission", failures)
    check(example_result["validation"]["passed"], "example validator should pass", failures)
    check(example_result["receipt"] is None, "no receipt should be written in fixture test", failures)

    template = ROOT / "agents-os-task-envelope-v0.1.md"
    template_result = loop.run_loop(
        template,
        write_local_receipt=False,
        run_date="2026-06-30",
    )
    check(
        template_result["gate"]["status"] == "NEEDS_ENVELOPE_FIX",
        "blank template should need envelope fix",
        failures,
    )
    check(not template_result["validation"]["passed"], "blank template validator should fail", failures)
    check(template_result["receipt"] is None, "no template receipt should be written", failures)

    red_gate = loop.gate_from_results(
        {
            "passed": False,
            "forbidden_hits": [],
            "forbidden_pattern_hits": [],
        },
        {
            "decision": "proposal_only",
            "permission_level": "A4",
        },
    )
    check(red_gate["status"] == "FORBIDDEN", "red router decision should beat form gaps", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=3 failures={len(failures)}")
        return 1

    print("PASS filled example task envelope loop")
    print("PASS blank template task envelope loop")
    print("PASS red router decision precedence")
    print("cases=3 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
