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
    check(intent["authorization"]["route_auto_selection_authorized"] is False, "intent candidate must not authorize route auto-selection", failures)
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

    negated = producer.candidate_from_intent("Do not call provider. Do not start service. Build local docs only.")
    check(not producer.validate_candidate(negated, schema), "negated boundary candidate should validate", failures)
    check(negated["blocked"] is False, "negated boundary statements should not block candidate", failures)
    check(not negated["risk_signals"], "negated boundary statements should not produce risk signals", failures)

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

    for option_id in producer.ROUTE_OPTIONS:
        route_candidate = producer.candidate_from_route_option(option_id)
        check(route_candidate.get("schema_version") == "agents-os.task-producer.candidate-task.v0.1", f"route option {option_id} should produce candidate", failures)
        check(not producer.validate_candidate(route_candidate, schema), f"route option {option_id} candidate should validate", failures)
        check(route_candidate["source"]["raw_content_included"] is False, f"route option {option_id} raw body should not be included", failures)
        check(route_candidate["source_facts"]["route_option_id"] == option_id, f"route option {option_id} id should surface", failures)
        check(route_candidate["source_facts"]["route_selected"] is False, f"route option {option_id} must not select route", failures)
        check(route_candidate["source_facts"]["route_auto_selection_authorized"] is False, f"route option {option_id} must not authorize auto-selection", failures)
        check("route_selection_required" in route_candidate["risk_signals"], f"route option {option_id} should require route selection", failures)
        check(route_candidate["blocked"] is True, f"route option {option_id} should remain blocked pending Jenn route selection", failures)
        check(route_candidate["actionable_after_review"] is False, f"route option {option_id} should not be actionable after Nobao review alone", failures)
        check(route_candidate["review_gate"]["requires_jenn_decision"] is True, f"route option {option_id} should require Jenn decision", failures)
        check(route_candidate["authorization"]["route_auto_selection_authorized"] is False, f"route option {option_id} authorization must keep auto-selection false", failures)
        check(route_candidate["queue_effect"]["active_queue_modified"] is False, f"route option {option_id} must not modify queue", failures)
        check(route_candidate["execution_effect"]["execution_authorized"] is False, f"route option {option_id} must not authorize execution", failures)

    bad_route = producer.candidate_from_route_option("Z")
    check(bad_route.get("passed") is False, "invalid route option should fail preflight", failures)
    check(bool(bad_route.get("findings")), "invalid route option should include findings", failures)

    route_choice = producer.route_choice_preview(
        "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
        "先准备 formal Memory candidate gate v0.1；只做候选和确认模型，不写正式 Memory。"
    )
    check(route_choice["passed"] is True, "route choice preview should pass for exact route text", failures)
    check(not producer.validate_route_choice_preview(route_choice), "route choice preview should validate", failures)
    check(route_choice["selected_option"]["option_id"] == "B", "route choice preview should resolve option B", failures)
    check(route_choice["confirmation_text_included"] is False, "route choice preview must not include raw text", failures)
    check(route_choice["workspace_route_state_modified"] is False, "route choice preview must not modify route state", failures)
    check(route_choice["active_queue_modified"] is False, "route choice preview must not modify queue", failures)
    check(route_choice["queue_promotion_authorized"] is False, "route choice preview must not authorize queue promotion", failures)
    check(route_choice["execution_authorized"] is False, "route choice preview must not authorize execution", failures)
    check(route_choice["review_gate"]["requires_nobao_review"] is True, "route choice preview should require Nobao review", failures)

    bad_route_choice = producer.route_choice_preview("继续做。")
    check(bad_route_choice.get("passed") is False, "route choice without marker should fail", failures)
    check(bool(bad_route_choice.get("findings")), "route choice without marker should include findings", failures)
    placeholder_route_choice = producer.route_choice_preview(
        "确认选择 AGENTS OS 下一路线：New AGENTS OS Construction Route。\n"
        "路线目标是：<Jenn 填写目标>。"
    )
    check(placeholder_route_choice.get("passed") is False, "new route placeholder goal should fail", failures)
    check(bool(placeholder_route_choice.get("findings")), "new route placeholder goal should include findings", failures)

    template_coverage = producer.route_choice_template_coverage()
    check(template_coverage["passed"] is True, f"route choice template coverage should pass: {template_coverage['errors']}", failures)
    check(not producer.validate_route_choice_template_coverage(template_coverage), "route choice template coverage should validate", failures)
    check(template_coverage["template_count"] == 5, "route choice template coverage should find five templates", failures)
    check(template_coverage["templates_checked"] == 5, "route choice template coverage should check five templates", failures)
    check(template_coverage["parsed_route_ids"] == ["A", "B", "C", "D", "E"], "route choice template coverage should prove A-E", failures)
    check(template_coverage["placeholder_goal_blocked"] is True, "Template E placeholder goal should be blocked", failures)
    check(template_coverage["concrete_new_route_fixture_passed"] is True, "concrete new route fixture should pass", failures)
    check(template_coverage["raw_template_output"] is False, "route choice template coverage must not output raw templates", failures)
    check(template_coverage["active_queue_modified"] is False, "route choice template coverage must not modify queue", failures)
    check(template_coverage["execution_authorized"] is False, "route choice template coverage must not authorize execution", failures)
    broken_template_coverage = dict(template_coverage)
    broken_template_coverage["raw_template_output"] = True
    check(
        producer.validate_route_choice_template_coverage(broken_template_coverage),
        "route choice template coverage with raw output should fail",
        failures,
    )

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
        print(f"cases=19 failures={len(failures)}")
        return 1

    print("PASS manifest boundary fixture")
    print("PASS intent candidate fixture")
    print("PASS risky candidate fixture")
    print("PASS negated boundary signal fixture")
    print("PASS queue mutation signal fixture")
    print("PASS allowlisted review source fixture")
    print("PASS route option candidate fixture")
    print("PASS invalid route option fixture")
    print("PASS route choice preview fixture")
    print("PASS invalid route choice preview fixture")
    print("PASS route choice template coverage fixture")
    print("PASS protected/disallowed source preflight fixture")
    print("cases=19 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
