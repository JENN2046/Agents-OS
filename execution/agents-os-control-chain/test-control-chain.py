#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Control Chain v0.1."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_chain() -> ModuleType:
    module_path = ROOT / "control_chain.py"
    spec = importlib.util.spec_from_file_location("agents_os_control_chain", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load control chain module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_producer() -> ModuleType:
    module_path = ROOT.parents[0] / "agents-os-task-producer" / "producer.py"
    spec = importlib.util.spec_from_file_location("agents_os_task_producer", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load task producer module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def candidate(candidate_id: str, title: str, summary: str, risk_signals: list[str] | None = None, jenn: bool = False) -> dict:
    return {
        "schema_version": "agents-os.task-producer.candidate-task.v0.1",
        "candidate_id": candidate_id,
        "producer_generated": True,
        "title": title,
        "summary": summary,
        "risk_signals": risk_signals or [],
        "authorization": {
            "queue_write_authorized": False,
            "execution_authorized": False,
            "provider_call_authorized": False,
            "service_start_authorized": False,
            "executor_run_authorized": False,
            "external_write_authorized": False,
            "memory_write_authorized": False,
            "runtime_plugin_activation_authorized": False,
            "plugin_execution_authorized": False,
            "route_auto_selection_authorized": False,
        },
        "execution_effect": {
            "write_performed": False,
            "execution_authorized": False,
            "service_started": False,
            "executor_run_performed": False,
            "provider_call_performed": False,
            "external_write_performed": False,
            "memory_write_performed": False,
            "runtime_plugin_activation_performed": False,
            "plugin_execution_performed": False,
        },
        "review_gate": {
            "requires_nobao_review": True,
            "requires_jenn_decision": jenn,
            "execution_authorized": False,
        },
    }


def main() -> int:
    chain = load_chain()
    producer = load_producer()
    failures: list[str] = []

    local = candidate("CANDIDATE-LOCAL", "Write governance report", "Write local governance report and run docctl validation.")
    colameta = candidate("CANDIDATE-COLAMETA", "ColaMeta Executor Readiness Reconciliation", "Run ColaMeta executor readiness reconciliation.")
    provider = candidate("CANDIDATE-PROVIDER", "Call provider", "Call provider and start service.", ["provider_call", "service_start"], True)
    invalid = candidate("CANDIDATE-INVALID", "Bad candidate", "Missing review gate")
    invalid["review_gate"]["requires_nobao_review"] = False

    local_decision = chain.build_commander_decision(local)
    check(local_decision["decision"] == "route_to_local_executor", "local governance task should route to local executor", failures)
    check(local_decision["execution_authorization_scope"] == "local_safe_only", "local task should get local_safe_only scope", failures)
    check(local_decision["execution_authorized"] is False, "Commander should not directly authorize execution", failures)

    colameta_decision = chain.build_commander_decision(colameta)
    check(colameta_decision["decision"] == "route_to_colameta", "ColaMeta readiness should route to ColaMeta", failures)
    check(colameta_decision["execution_authorization_scope"] == "none", "ColaMeta route should stay scope none", failures)

    provider_decision = chain.build_commander_decision(provider)
    check(provider_decision["decision"] == "stop_needs_jenn_decision", "provider task should stop for Jenn", failures)
    check(provider_decision["execution_authorization_scope"] == "blocked_requires_jenn", "provider task should be blocked_requires_jenn", failures)

    route_candidate = producer.candidate_from_route_option("A")
    route_decision = chain.build_commander_decision(route_candidate)
    check(route_decision["decision"] == "stop_needs_jenn_decision", "route option candidate should stop for Jenn", failures)
    check(route_decision["execution_authorization_scope"] == "blocked_requires_jenn", "route option candidate should be blocked_requires_jenn", failures)
    check(route_decision["requires_jenn_decision"] is True, "route option candidate should require Jenn decision", failures)
    check(route_decision["execution_authorized"] is False, "route option candidate should not authorize execution", failures)
    check("route_selection_required" in route_decision["blocked_capabilities"], "route option should block route selection", failures)
    check("route_auto_selection" in route_decision["blocked_capabilities"], "route option should block route auto-selection", failures)

    invalid_decision = chain.build_commander_decision(invalid)
    check(invalid_decision["decision"] == "reject_as_out_of_scope", "invalid candidate should be rejected", failures)

    local_preview = chain.build_track_preview(local_decision, "run_validation_command")
    check(local_preview["selected_track"] == "local_executor", "local preview should select local executor", failures)
    check(local_preview["track_authorized"] is True, "local preview should be track-authorized", failures)

    blocked_preview = chain.build_track_preview(provider_decision)
    check(blocked_preview["selected_track"] == "stop", "provider preview should select stop", failures)
    check(blocked_preview["track_authorized"] is False, "selector must not elevate blocked decision", failures)

    route_preview = chain.build_track_preview(route_decision)
    check(route_preview["selected_track"] == "stop", "route option preview should select stop", failures)
    check(route_preview["track_authorized"] is False, "selector must not elevate route option decision", failures)

    cola_preview = chain.build_track_preview(colameta_decision)
    check(cola_preview["selected_track"] == "colameta", "ColaMeta preview should select ColaMeta", failures)
    check(cola_preview["execution_authorization_scope"] == "none", "ColaMeta preview should keep scope none", failures)

    local_result = chain.local_executor_run(local_preview, "run_validation_command", command="python3 --version")
    check(local_result["passed"], f"local validation command should pass: {local_result['errors']}", failures)
    check(local_result["execution_performed"] is True, "local validation command should execute", failures)
    check(local_result["write_performed"] is False, "validation command should not write", failures)

    forbidden_result = chain.local_executor_run(local_preview, "provider_call")
    check(forbidden_result["validation_passed"] is False, "provider_call should be blocked", failures)

    failing_result = chain.local_executor_run(
        local_preview,
        "run_validation_command",
        command="python3 execution/agents-os-control-chain/does-not-exist.py",
    )
    failure_report = chain.build_failure_report(failing_result)
    check(failure_report["category"] == "validation_failed", "failed validation should classify as validation_failed", failures)
    check(failure_report["repair_attempt_allowed"] is True, "validation_failed should allow one future repair attempt", failures)
    check(failure_report["max_repair_attempts"] == 1, "validation_failed max repair attempts should be 1", failures)
    check(failure_report["silent_retry_authorized"] is False, "failure report must not authorize silent retry", failures)
    check(failure_report["queue_promotion_allowed"] is False, "failure report must not allow queue promotion", failures)

    stop_loop = chain.build_stop_loop_result(failure_report)
    check(stop_loop["status"] == "stopped_for_review", "stop loop should stop for review", failures)
    check(stop_loop["queue_promoted"] is False, "stop loop must not promote queue", failures)
    check(stop_loop["silent_retry_performed"] is False, "stop loop must not silently retry", failures)

    failed_proposal = chain.queue_update_proposal(failing_result)
    check(failed_proposal["close_current_now"] is False, "failed track result should not close NOW", failures)
    check(failed_proposal["promote_next_title"] is None, "failed track result should not promote NEXT", failures)

    def failed_fixture(track_id: str, error: str) -> dict:
        return dict(
            local_result,
            track_result_id=track_id,
            validation_passed=False,
            passed=False,
            errors=[error],
        )

    category_fixtures = [
        (failed_fixture("TRACKRESULT-PROTECTED", "target path is protected: state-private/foo"), "protected_path_detected"),
        (failed_fixture("TRACKRESULT-DIRTY", "dirty tracked worktree before local executor action"), "dirty_worktree_conflict"),
        (failed_fixture("TRACKRESULT-SCOPE", "target path is outside workspace: /tmp/foo"), "scope_violation"),
        (failed_fixture("TRACKRESULT-UNKNOWN", "action_type is not allowed: make_coffee"), "unknown_action_type"),
        (failed_fixture("TRACKRESULT-P3", "provider_call requested by action"), "p3_signal_detected"),
        ({"schema_version": "agents-os.control-chain.track-result.v0.1", "track_result_id": "TRACKRESULT-BROKEN"}, "executor_output_invalid"),
    ]
    for fixture, expected_category in category_fixtures:
        report = chain.build_failure_report(fixture)
        check(report["category"] == expected_category, f"expected {expected_category}, got {report['category']}", failures)
        check(report["silent_retry_authorized"] is False, f"{expected_category} should not authorize silent retry", failures)
        check(report["queue_promotion_allowed"] is False, f"{expected_category} should not allow queue promotion", failures)
    p3_report = chain.build_failure_report(category_fixtures[4][0])
    p3_stop = chain.build_stop_loop_result(p3_report)
    check(p3_report["requires_jenn_decision"] is True, "P3 failure should require Jenn decision", failures)
    check(p3_stop["provider_call_performed"] is False, "P3 stop loop must not perform provider call", failures)

    cola_result = chain.colameta_readiness(cola_preview)
    check(cola_result["passed"], f"ColaMeta readiness should pass: {cola_result['errors']}", failures)
    check(cola_result["preview_only"] is True, "ColaMeta readiness should be preview-only", failures)
    check(cola_result["execution_performed"] is False, "ColaMeta readiness should not execute", failures)
    check(cola_result["effects"]["provider_call_performed"] is False, "ColaMeta readiness should not call provider", failures)
    check(cola_result["colameta_readiness"]["preflight"]["memory"]["content_read"] is False, "memory content should not be read", failures)

    proposal = chain.queue_update_proposal(local_result)
    check(proposal["proposal_only"] is True, "queue proposal should be proposal-only", failures)
    check(proposal["active_queue_modified"] is False, "queue proposal should not mutate queue", failures)

    route_choice_preview = producer.route_choice_preview(
        "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
        "先准备 formal Memory candidate gate v0.1；只做候选和确认模型，不写正式 Memory。"
    )
    route_choice_proposal = chain.route_choice_queue_proposal(route_choice_preview)
    check(route_choice_proposal["passed"] is True, f"route choice proposal should pass: {route_choice_proposal['errors']}", failures)
    check(route_choice_proposal["proposal_only"] is True, "route choice proposal should be proposal-only", failures)
    check(route_choice_proposal["preview_only"] is True, "route choice proposal should be preview-only", failures)
    check(route_choice_proposal["source_route_choice_option_id"] == "B", "route choice proposal should carry selected option B", failures)
    check(route_choice_proposal["proposed_queue_item"]["lane"] == "NEXT", "route choice proposal should propose NEXT lane", failures)
    check(route_choice_proposal["active_queue_modified"] is False, "route choice proposal must not mutate active queue", failures)
    check(route_choice_proposal["queue_write_authorized"] is False, "route choice proposal must not authorize queue write", failures)
    check(route_choice_proposal["queue_promotion_authorized"] is False, "route choice proposal must not authorize queue promotion", failures)
    check(route_choice_proposal["execution_authorized"] is False, "route choice proposal must not authorize execution", failures)
    invalid_route_choice_proposal = chain.route_choice_queue_proposal({"schema_version": "bad"})
    check(invalid_route_choice_proposal["passed"] is False, "invalid route choice preview should not produce passing proposal", failures)
    check(bool(invalid_route_choice_proposal["errors"]), "invalid route choice proposal should include errors", failures)

    with tempfile.TemporaryDirectory(prefix="agents-os-control-chain-test-", dir=chain.WORKSPACE_ROOT) as temp_dir:
        queue_path = Path(temp_dir) / "queue.md"
        queue_path.write_text(
            """# fixture queue

## NOW

### NOW-001: Completed task

Done.

## NEXT

### NEXT-001: Safe next task

Write local governance report.

### NEXT-002: Later task

Wait.

## CLOSED

```text
old_task: closed
```
""",
            encoding="utf-8",
        )
        fixture_proposal = chain.queue_update_proposal(local_result, queue_path)
        review = {
            "schema_version": "agents-os.queue-manager.review.v0.1",
            "source_proposal_id": fixture_proposal["proposal_id"],
            "review_status": "accepted",
            "reviewer": "Nobao",
            "requires_jenn_decision": False,
        }
        mutation_preview = chain.reviewed_queue_mutation(fixture_proposal, review, queue_path)
        check(mutation_preview["passed"], f"reviewed queue mutation preview should pass: {mutation_preview['errors']}", failures)
        check(mutation_preview["preview_only"] is True, "reviewed mutation preview should be preview-only", failures)
        check(mutation_preview["active_queue_modified"] is False, "reviewed mutation preview should not mutate queue", failures)
        mutation_apply = chain.reviewed_queue_mutation(fixture_proposal, review, queue_path, apply=True)
        check(mutation_apply["passed"], f"reviewed queue mutation apply should pass: {mutation_apply['errors']}", failures)
        check(mutation_apply["active_queue_modified"] is True, "reviewed mutation apply should mutate fixture queue", failures)
        check("### NOW-001: Safe next task" in queue_path.read_text(encoding="utf-8"), "reviewed mutation should promote safe NEXT", failures)

        pending_review = dict(review, review_status="pending")
        pending_mutation = chain.reviewed_queue_mutation(fixture_proposal, pending_review, queue_path)
        check(pending_mutation["queue_mutation_authorized"] is False, "pending review should block mutation", failures)

        p3_path = Path(temp_dir) / "p3-queue.md"
        p3_path.write_text(
            """# fixture queue

## NOW

### NOW-001: Completed task

Done.

## NEXT

### NEXT-001: Call provider

Call provider and start service.

## CLOSED

```text
old_task: closed
```
""",
            encoding="utf-8",
        )
        p3_proposal = chain.queue_update_proposal(local_result, p3_path)
        p3_review = dict(review, source_proposal_id=p3_proposal["proposal_id"])
        p3_mutation = chain.reviewed_queue_mutation(p3_proposal, p3_review, p3_path)
        check(p3_mutation["queue_mutation_authorized"] is False, "P3 NEXT target should block mutation", failures)

        route_queue_path = Path(temp_dir) / "route-queue.md"
        route_queue_text = """# fixture queue

## NOW

### NOW-001: No Active Automatic Construction Item

Waiting for Jenn route selection.

## NEXT

_No active NEXT items._

## CLOSED

```text
old_task: closed
```
"""
        route_queue_path.write_text(route_queue_text, encoding="utf-8")
        route_review = {
            "schema_version": "agents-os.queue-manager.review.v0.1",
            "source_proposal_id": route_choice_proposal["proposal_id"],
            "review_status": "accepted",
            "reviewer": "Nobao",
            "requires_jenn_decision": False,
        }
        adoption_preview = chain.reviewed_route_adoption_preview(route_choice_proposal, route_review, route_queue_path)
        check(adoption_preview["passed"], f"reviewed route adoption preview should pass: {adoption_preview['errors']}", failures)
        check(adoption_preview["preview_only"] is True, "reviewed route adoption should be preview-only", failures)
        check(adoption_preview["queue_mutation_preview_authorized"] is True, "reviewed route adoption preview should be authorized as preview", failures)
        check(adoption_preview["active_queue_modified"] is False, "reviewed route adoption preview must not mutate queue", failures)
        check(adoption_preview["write_performed"] is False, "reviewed route adoption preview must not write", failures)
        check(adoption_preview["queue_write_authorized"] is False, "reviewed route adoption preview must not authorize queue write", failures)
        check(adoption_preview["execution_authorized"] is False, "reviewed route adoption preview must not authorize execution", failures)
        check(adoption_preview["mutation_preview"]["target_lane"] == "NEXT", "reviewed route adoption preview should target NEXT", failures)
        check(adoption_preview["mutation_preview"]["would_promote_now"] is False, "reviewed route adoption preview must not promote NOW", failures)
        check(route_queue_path.read_text(encoding="utf-8") == route_queue_text, "reviewed route adoption preview should not change fixture queue", failures)

        pending_route_review = dict(route_review, review_status="pending")
        pending_adoption_preview = chain.reviewed_route_adoption_preview(route_choice_proposal, pending_route_review, route_queue_path)
        check(pending_adoption_preview["passed"] is False, "pending route adoption review should fail preview", failures)
        check(pending_adoption_preview["active_queue_modified"] is False, "pending route adoption preview must not mutate queue", failures)

    validation = chain.validate_control_chain(run_colameta=False)
    check(validation["passed"], f"control chain validation without ColaMeta should pass: {validation['errors']}", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=24 failures={len(failures)}")
        return 1

    print("PASS commander routing fixtures")
    print("PASS selector no-elevation fixtures")
    print("PASS local executor allowed/forbidden fixtures")
    print("PASS failure handling stop-loop fixtures")
    print("PASS ColaMeta readiness fixture")
    print("PASS queue proposal-only fixture")
    print("PASS route choice queue proposal fixture")
    print("PASS reviewed queue mutation fixture")
    print("PASS reviewed route adoption preview fixture")
    print("PASS route option stop gate fixture")
    print("cases=24 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
