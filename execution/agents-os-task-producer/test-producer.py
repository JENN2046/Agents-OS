#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Task Producer Skeleton v0.1."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_producer() -> ModuleType:
    module_path = ROOT / "producer.py"
    spec = importlib.util.spec_from_file_location("agents_os_task_producer", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load producer module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    producer = load_producer()
    failures: list[str] = []
    schema = json.loads((ROOT / "candidate-task.schema.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "producer-manifest.json").read_text(encoding="utf-8"))

    check(not producer.validate_manifest(manifest), "manifest should validate", failures)
    manifest["dangerous_authorization_defaults"]["provider_call_authorized"] = True
    check(producer.validate_manifest(manifest), "manifest with dangerous true should fail", failures)

    intent = producer.candidate_from_intent("Build a local review task from Jenn intent.")
    check(not producer.validate_candidate(intent, schema), "intent candidate should validate", failures)
    check(intent["blocked"] is False, "benign intent should not be blocked", failures)
    check(intent["review_gate"]["requires_nobao_review"] is True, "intent candidate should require Nobao review", failures)
    check(intent["authorization"]["queue_write_authorized"] is False, "intent candidate must not authorize queue write", failures)
    check(intent["execution_effect"]["execution_authorized"] is False, "intent candidate must not authorize execution", failures)
    check(intent["source"]["raw_content_included"] is False, "intent raw content flag should be false", failures)

    risky = producer.candidate_from_intent("Call provider, start service, and write to Notion.")
    check(not producer.validate_candidate(risky, schema), "risky candidate should still validate as blocked preview", failures)
    check(risky["blocked"] is True, "risky candidate should be blocked", failures)
    check("provider_call" in risky["risk_signals"], "provider signal should be detected", failures)
    check("service_start" in risky["risk_signals"], "service signal should be detected", failures)
    check("external_write" in risky["risk_signals"], "external write signal should be detected", failures)
    check(risky["review_gate"]["requires_jenn_decision"] is True, "P3-like risk should require Jenn", failures)
    check(risky["execution_effect"]["provider_call_performed"] is False, "risky candidate must not perform provider call", failures)

    queue_signal = producer.candidate_from_intent("Promote NEXT-001 to NOW and update the Active Work Queue.")
    check(not producer.validate_candidate(queue_signal, schema), "queue-signal candidate should validate", failures)
    check(queue_signal["blocked"] is True, "queue-signal candidate should be blocked", failures)
    check("queue_write" in queue_signal["risk_signals"], "queue write signal should be detected", failures)
    check("queue_promotion" in queue_signal["risk_signals"], "queue promotion signal should be detected", failures)
    check(queue_signal["queue_effect"]["active_queue_modified"] is False, "producer must not modify queue", failures)

    broken = dict(intent)
    broken["authorization"] = dict(intent["authorization"])
    broken["authorization"]["provider_call_authorized"] = True
    check(producer.validate_candidate(broken, schema), "candidate with dangerous true should fail", failures)

    review_candidate = producer.candidate_from_review_source(producer.DEFAULT_REVIEW_SOURCE)
    check(review_candidate.get("schema_version") == "agents-os.task-producer.candidate-task.v0.1", "review source should produce candidate", failures)
    check(not producer.validate_candidate(review_candidate, schema), "review candidate should validate", failures)
    check(review_candidate["source"]["raw_content_included"] is False, "review source raw body should not be included", failures)
    check(review_candidate["source_facts"]["heading_count"] >= 1, "review candidate should include heading facts", failures)

    protected = producer.candidate_from_review_source(Path("state-private/task.md"))
    check(protected.get("passed") is False, "protected source path should fail before read", failures)
    check(bool(protected.get("findings")), "protected source path should include findings", failures)

    disallowed = producer.candidate_from_review_source(Path("AGENTS.md"))
    check(disallowed.get("passed") is False, "non-allowlisted source path should fail", failures)
    check(bool(disallowed.get("findings")), "non-allowlisted source path should include findings", failures)

    validation = producer.validate_producer(run_docctl=False)
    check(validation["passed"], f"producer validation without docctl should pass: {validation['errors']}", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=13 failures={len(failures)}")
        return 1

    print("PASS manifest boundary fixture")
    print("PASS intent candidate fixture")
    print("PASS risky candidate fixture")
    print("PASS queue mutation signal fixture")
    print("PASS allowlisted review source fixture")
    print("PASS protected/disallowed source preflight fixture")
    print("cases=13 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
