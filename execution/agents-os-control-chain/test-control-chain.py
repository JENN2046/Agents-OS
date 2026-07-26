#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Control Chain v0.1."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
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

    with tempfile.TemporaryDirectory(prefix="agents-os-route-handoff-test-", dir=chain.WORKSPACE_ROOT) as handoff_temp_dir:
        handoff_queue_path = Path(handoff_temp_dir) / "route-handoff-queue.md"
        handoff_queue_path.write_text(
            """# route handoff fixture

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
        route_handoff = chain.route_choice_handoff_reconciliation(handoff_queue_path)
    check(route_handoff["passed"] is True, f"route choice handoff reconciliation should pass: {route_handoff['errors']}", failures)
    check(route_handoff["aligned"] is True, "route choice handoff should align Machine and Dashboard", failures)
    check(route_handoff["route_choice_required"] is True, "route choice handoff should require route choice", failures)
    check(route_handoff["decision_owner"] == "Jenn", "route choice handoff decision owner should be Jenn", failures)
    check(route_handoff["accepted_route_ids"] == ["A", "B", "C", "D", "E"], "route choice handoff should carry route ids A-E", failures)
    check(route_handoff["active_queue_mutation_authorized"] is False, "route choice handoff must not authorize active queue mutation", failures)
    check(route_handoff["queue_promotion_authorized"] is False, "route choice handoff must not authorize queue promotion", failures)
    check(route_handoff["execution_authorized"] is False, "route choice handoff must not authorize execution", failures)

    closed_append_text = """# append closed fixture

## NOW

### NOW-001: Current

Done.

## CLOSED

```text
old_task: closed
```

## Immediate Construction Instruction

```text
route A
```
"""
    closed_appended = chain.append_closed_entry(closed_append_text, "new_task: closed")
    closed_section = closed_appended.split("## Immediate Construction Instruction", 1)[0]
    immediate_section = closed_appended.split("## Immediate Construction Instruction", 1)[1]
    check("new_task: closed" in closed_section, "append_closed_entry should insert under CLOSED section", failures)
    check("new_task: closed" not in immediate_section, "append_closed_entry must not insert into later fenced sections", failures)

    route_template_readiness = chain.route_choice_template_readiness()
    check(
        route_template_readiness["passed"] is True,
        f"route choice template readiness should pass: {route_template_readiness['errors']}",
        failures,
    )
    check(
        route_template_readiness["task_producer_coverage_passed"] is True,
        "route choice template readiness should use passing Task Producer coverage",
        failures,
    )
    check(
        route_template_readiness["accepted_route_ids"] == ["A", "B", "C", "D", "E"],
        "route choice template readiness should accept route ids A-E",
        failures,
    )
    check(
        route_template_readiness["parsed_route_ids"] == ["A", "B", "C", "D", "E"],
        "route choice template readiness should prove parsed route ids A-E",
        failures,
    )
    check(route_template_readiness["placeholder_goal_blocked"] is True, "Template E placeholder should remain blocked", failures)
    check(route_template_readiness["concrete_new_route_fixture_passed"] is True, "Concrete option E fixture should pass", failures)
    check(route_template_readiness["active_queue_modified"] is False, "route choice template readiness must not modify queue", failures)
    check(route_template_readiness["raw_template_output"] is False, "route choice template readiness must not output raw templates", failures)
    check(route_template_readiness["execution_authorized"] is False, "route choice template readiness must not authorize execution", failures)

    route_e2e_readiness = chain.route_choice_end_to_end_readiness()
    check(
        route_e2e_readiness["passed"] is True,
        f"route choice end-to-end readiness should pass: {route_e2e_readiness['errors']}",
        failures,
    )
    check(
        route_e2e_readiness["checked_route_ids"] == ["A", "B", "C", "D", "E"],
        "route choice end-to-end readiness should check route ids A-E",
        failures,
    )
    check(
        route_e2e_readiness["passed_route_ids"] == ["A", "B", "C", "D", "E"],
        "route choice end-to-end readiness should pass route ids A-E",
        failures,
    )
    check(route_e2e_readiness["route_count"] == 5, "route choice end-to-end readiness should cover five routes", failures)
    for stage, count in route_e2e_readiness["stage_counts"].items():
        check(count == 5, f"route choice end-to-end readiness stage {stage} should pass all five routes", failures)
    check(route_e2e_readiness["temporary_fixture_cleaned"] is True, "route choice end-to-end readiness should clean fixture", failures)
    check(route_e2e_readiness["fixture_queue_unchanged"] is True, "route choice end-to-end readiness fixture should stay unchanged", failures)
    check(route_e2e_readiness["active_queue_modified"] is False, "route choice end-to-end readiness must not modify active queue", failures)
    check(route_e2e_readiness["real_queue_write_performed"] is False, "route choice end-to-end readiness must not write real queue", failures)
    check(route_e2e_readiness["route_selected"] is False, "route choice end-to-end readiness must not select a route", failures)
    check(route_e2e_readiness["route_adoption_authorized"] is False, "route choice end-to-end readiness must not authorize route adoption", failures)
    check(route_e2e_readiness["execution_authorized"] is False, "route choice end-to-end readiness must not authorize execution", failures)
    check(route_e2e_readiness["raw_confirmation_text_output"] is False, "route choice end-to-end readiness must not output raw confirmation text", failures)
    check(route_e2e_readiness["raw_template_output"] is False, "route choice end-to-end readiness must not output raw template", failures)

    route_adoption_bundle = chain.route_choice_adoption_bundle_preview(
        "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
        "这是 adoption bundle fixture；不写真实队列、不执行。",
        fixture_only=True,
    )
    check(
        route_adoption_bundle["passed"] is True,
        f"route choice adoption bundle preview should pass: {route_adoption_bundle['errors']}",
        failures,
    )
    check(route_adoption_bundle["selected_route_id"] == "B", "route adoption bundle should select route B fixture", failures)
    check(route_adoption_bundle["queue_proposal_passed"] is True, "route adoption bundle should pass queue proposal", failures)
    check(route_adoption_bundle["review_object_generated"] is True, "route adoption bundle should generate review object", failures)
    check(route_adoption_bundle["reviewed_route_adoption_preview_passed"] is True, "route adoption bundle should pass adoption preview", failures)
    check(route_adoption_bundle["reviewed_route_adoption_apply_preview_passed"] is True, "route adoption bundle should pass apply-gate preview", failures)
    check(route_adoption_bundle["can_apply_with_separate_apply_gate"] is True, "route adoption bundle should identify separate apply gate", failures)
    check(route_adoption_bundle["real_queue_write_performed"] is False, "route adoption bundle must not write real queue", failures)
    check(route_adoption_bundle["active_queue_modified"] is False, "route adoption bundle must not mutate active queue", failures)
    check(route_adoption_bundle["route_adoption_authorized"] is False, "route adoption bundle must not authorize route adoption", failures)
    check(route_adoption_bundle["execution_authorized"] is False, "route adoption bundle must not authorize execution", failures)
    check(route_adoption_bundle["raw_confirmation_text_output"] is False, "route adoption bundle must not output raw confirmation text", failures)
    check(route_adoption_bundle["raw_template_output"] is False, "route adoption bundle must not output raw template", failures)
    invalid_route_adoption_bundle = chain.route_choice_adoption_bundle_preview("继续做。", fixture_only=True)
    check(invalid_route_adoption_bundle["passed"] is False, "invalid route adoption bundle should fail", failures)
    check(invalid_route_adoption_bundle["real_queue_write_performed"] is False, "invalid route adoption bundle must not write real queue", failures)
    check(invalid_route_adoption_bundle["execution_authorized"] is False, "invalid route adoption bundle must not authorize execution", failures)

    with tempfile.TemporaryDirectory(prefix="agents-os-governance-gate-test-", dir=chain.WORKSPACE_ROOT) as gate_temp_dir:
        governance_queue_path = Path(gate_temp_dir) / "governance-gate-queue.md"
        governance_queue_text = """# governance gate fixture

## NOW

### NOW-001: Awaiting Jenn Explicit Start Decision

```text
requires_jenn_decision=true
decision_owner=Jenn
```

## NEXT

_No active NEXT items._

## CLOSED

```text
prior_task: closed
```
"""
        governance_queue_path.write_text(governance_queue_text, encoding="utf-8")
        governance_handoff = chain.route_choice_handoff_reconciliation(governance_queue_path)
        governance_bundle = chain.route_choice_adoption_bundle_preview(
            "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
            "这是 governance gate fixture；不写真实队列、不执行。",
            governance_queue_path,
            chain.ROUTE_SELECTION_PACKAGE,
        )
        check(
            governance_queue_path.read_text(encoding="utf-8") == governance_queue_text,
            "active governance gate fixtures must not modify their queue",
            failures,
        )
    check(
        governance_handoff["passed"] is True and governance_handoff["aligned"] is True,
        f"active governance gate handoff should pass and align: {governance_handoff['errors']}",
        failures,
    )
    check(
        governance_handoff["machine_next_user_action"]["status"] == "governance_decision_required"
        and governance_handoff["dashboard_next_user_action"]["status"] == "governance_decision_required",
        "active governance gate fixture should make Machine and Dashboard require a governance decision",
        failures,
    )
    check(
        chain.active_jenn_governance_gate(governance_handoff) is True,
        "active Jenn governance gate should be detected",
        failures,
    )
    check(
        governance_bundle["passed"] is False
        and governance_bundle["can_apply_with_separate_apply_gate"] is False,
        "production governance bundle should fail closed before apply readiness",
        failures,
    )
    check(
        governance_bundle["fixture_only"] is False,
        "active governance gate fixture should exercise the public production bundle path",
        failures,
    )
    check(
        governance_bundle["active_jenn_governance_gate"] is True,
        "production governance bundle should preserve the active Jenn gate",
        failures,
    )
    check(
        governance_bundle["review_object_generated"] is False
        and governance_bundle["reviewed_route_adoption_preview_passed"] is False
        and governance_bundle["reviewed_route_adoption_apply_preview_passed"] is False,
        "production governance bundle must not generate or pass route adoption review",
        failures,
    )
    check(
        governance_bundle["review_requires_jenn_decision"] is True,
        "production governance bundle should preserve the Jenn decision requirement",
        failures,
    )
    governance_gate_errors = chain.route_adoption_handoff_gate_errors(governance_handoff)
    check(
        governance_gate_errors == ["active Jenn governance gate blocks route adoption"],
        f"active Jenn governance gate should emit the exact production block: {governance_gate_errors}",
        failures,
    )
    governance_handoff_errors = chain.validate_route_adoption_bundle_handoff(
        governance_handoff,
        governance_bundle,
    )
    check(
        governance_handoff_errors == [],
        f"production fail-closed governance bundle should satisfy handoff validation: {governance_handoff_errors}",
        failures,
    )

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
        direct_governance_queue_path = Path(temp_dir) / "direct-governance-gate-queue.md"
        direct_governance_queue_text = """# governance gate fixture

## NOW

### NOW-001: Awaiting Jenn Explicit Start Decision

```text
requires_jenn_decision=true
decision_owner=Jenn
```

## NEXT

_No active NEXT items._

## CLOSED

```text
prior_task: closed
```
"""
        direct_governance_queue_path.write_text(direct_governance_queue_text, encoding="utf-8")
        direct_governance_preview = chain.reviewed_route_adoption_preview(
            route_choice_proposal,
            route_review,
            direct_governance_queue_path,
        )
        direct_governance_apply_preview = chain.reviewed_route_adoption_apply_gate(
            route_choice_proposal,
            route_review,
            direct_governance_queue_path,
        )
        direct_governance_apply = chain.reviewed_route_adoption_apply_gate(
            route_choice_proposal,
            route_review,
            direct_governance_queue_path,
            apply=True,
        )
        check(
            direct_governance_preview["passed"] is False
            and direct_governance_preview["active_jenn_governance_gate"] is True
            and direct_governance_preview["requires_jenn_decision"] is True
            and direct_governance_preview["queue_mutation_preview_authorized"] is False,
            "direct reviewed route adoption preview must fail closed under the active Jenn gate",
            failures,
        )
        check(
            direct_governance_apply_preview["passed"] is False
            and direct_governance_apply_preview["active_jenn_governance_gate"] is True
            and direct_governance_apply_preview["queue_adoption_authorized"] is False,
            "direct reviewed route adoption apply preview must fail closed under the active Jenn gate",
            failures,
        )
        check(
            direct_governance_apply["passed"] is False
            and direct_governance_apply["active_jenn_governance_gate"] is True
            and direct_governance_apply["queue_adoption_authorized"] is False
            and direct_governance_apply["active_queue_modified"] is False
            and direct_governance_apply["write_performed"] is False
            and direct_governance_apply["queue_write_authorized"] is False,
            "direct reviewed route adoption apply must not authorize or perform a write under the active Jenn gate",
            failures,
        )
        check(
            direct_governance_queue_path.read_text(encoding="utf-8") == direct_governance_queue_text,
            "direct active Jenn gate attacks must leave queue bytes unchanged",
            failures,
        )

        route_proposal_json = Path(temp_dir) / "route-proposal.json"
        route_review_json = Path(temp_dir) / "route-review.json"
        route_proposal_json.write_text(json.dumps(route_choice_proposal), encoding="utf-8")
        route_review_json.write_text(json.dumps(route_review), encoding="utf-8")
        direct_cli_apply = subprocess.run(
            [
                sys.executable,
                str(ROOT / "control_chain.py"),
                "reviewed-route-adoption-apply-gate",
                "--proposal-json",
                str(route_proposal_json),
                "--review-json",
                str(route_review_json),
                "--queue",
                str(direct_governance_queue_path),
                "--apply",
                "--json",
            ],
            cwd=chain.WORKSPACE_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        direct_cli_apply_result = json.loads(direct_cli_apply.stdout)
        check(
            direct_cli_apply.returncode == 1
            and direct_cli_apply_result["passed"] is False
            and direct_cli_apply_result["active_jenn_governance_gate"] is True
            and direct_cli_apply_result["queue_adoption_authorized"] is False
            and direct_cli_apply_result["write_performed"] is False,
            f"public reviewed route adoption CLI must fail closed under the active Jenn gate: {direct_cli_apply.stderr}",
            failures,
        )
        check(
            direct_governance_queue_path.read_text(encoding="utf-8") == direct_governance_queue_text,
            "public reviewed route adoption CLI attack must leave queue bytes unchanged",
            failures,
        )

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

        route_apply_queue_path = Path(temp_dir) / "route-apply-queue.md"
        route_apply_queue_text = """# fixture queue

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
        route_apply_queue_path.write_text(route_apply_queue_text, encoding="utf-8")
        adoption_apply_preview = chain.reviewed_route_adoption_apply_gate(route_choice_proposal, route_review, route_apply_queue_path)
        check(adoption_apply_preview["passed"], f"reviewed route adoption apply preview should pass: {adoption_apply_preview['errors']}", failures)
        check(adoption_apply_preview["preview_only"] is True, "route adoption apply preview should be preview-only", failures)
        check(adoption_apply_preview["active_queue_modified"] is False, "route adoption apply preview must not mutate queue", failures)
        check(adoption_apply_preview["queue_write_authorized"] is False, "route adoption apply preview must not authorize queue write", failures)
        check(route_apply_queue_path.read_text(encoding="utf-8") == route_apply_queue_text, "route adoption apply preview should not change queue", failures)
        adoption_apply = chain.reviewed_route_adoption_apply_gate(route_choice_proposal, route_review, route_apply_queue_path, apply=True)
        route_apply_text = route_apply_queue_path.read_text(encoding="utf-8")
        check(adoption_apply["passed"], f"reviewed route adoption apply should pass: {adoption_apply['errors']}", failures)
        check(adoption_apply["active_queue_modified"] is True, "route adoption apply should mutate fixture queue", failures)
        check(adoption_apply["queue_write_authorized"] is True, "route adoption apply should authorize explicit queue write", failures)
        check(adoption_apply["queue_promotion_authorized"] is False, "route adoption apply must not authorize queue promotion", failures)
        check(adoption_apply["execution_authorized"] is False, "route adoption apply must not authorize execution", failures)
        check("### NOW-001: No Active Automatic Construction Item" in route_apply_text, "route adoption apply must leave NOW unchanged", failures)
        check("### NEXT-001: AGENTS OS formal Memory candidate gate v0.1" in route_apply_text, "route adoption apply should append selected route to NEXT", failures)
        duplicate_route_apply = chain.reviewed_route_adoption_apply_gate(route_choice_proposal, route_review, route_apply_queue_path)
        check(duplicate_route_apply["passed"] is False, "duplicate route adoption should fail", failures)
        check(duplicate_route_apply["queue_adoption_authorized"] is False, "duplicate route adoption should be blocked", failures)
        pending_route_apply = chain.reviewed_route_adoption_apply_gate(route_choice_proposal, pending_route_review, route_apply_queue_path)
        check(pending_route_apply["passed"] is False, "pending route adoption apply should fail", failures)
        check(pending_route_apply["queue_adoption_authorized"] is False, "pending route adoption apply should be blocked", failures)
        p3_route_proposal = json.loads(json.dumps(route_choice_proposal))
        p3_route_proposal["proposal_id"] = chain.stable_id("ROUTEQUEUEPROPOSALP3", ["provider", "service"])
        p3_route_proposal["proposed_queue_item"] = {
            "lane": "NEXT",
            "title": "Call provider",
            "body_lines": ["Call provider and start service."],
        }
        p3_route_review = dict(route_review, source_proposal_id=p3_route_proposal["proposal_id"])
        p3_route_apply = chain.reviewed_route_adoption_apply_gate(p3_route_proposal, p3_route_review, route_apply_queue_path)
        check(p3_route_apply["passed"] is False, "P3 route adoption should fail", failures)
        check(p3_route_apply["queue_adoption_authorized"] is False, "P3 route adoption should be blocked", failures)

    validation = chain.validate_control_chain(run_colameta=False)
    check(validation["passed"], f"control chain validation without ColaMeta should pass: {validation['errors']}", failures)
    check(validation["route_choice_handoff"]["aligned"] is True, "validation should report aligned route handoff", failures)
    check(validation["route_choice_handoff"]["execution_authorized"] is False, "validation should keep route handoff execution unauthorized", failures)
    check(
        validation["route_choice_template_readiness"]["parsed_route_ids"] == ["A", "B", "C", "D", "E"],
        "validation should report A-E template readiness",
        failures,
    )
    check(
        validation["route_choice_template_readiness"]["execution_authorized"] is False,
        "validation should keep template readiness execution unauthorized",
        failures,
    )
    check(
        validation["route_choice_end_to_end_readiness"]["passed_route_ids"] == ["A", "B", "C", "D", "E"],
        "validation should report A-E end-to-end readiness",
        failures,
    )
    check(
        validation["route_choice_end_to_end_readiness"]["real_queue_write_performed"] is False,
        "validation should keep end-to-end readiness real queue writes false",
        failures,
    )
    check(
        validation["route_choice_end_to_end_readiness"]["execution_authorized"] is False,
        "validation should keep end-to-end readiness execution unauthorized",
        failures,
    )
    check(
        validation["route_choice_adoption_bundle_preview"]["selected_route_id"] == "B",
        "validation should report route adoption bundle fixture B",
        failures,
    )
    check(
        validation["route_choice_adoption_bundle_preview"]["can_apply_with_separate_apply_gate"] is True,
        "validation should report route adoption bundle separate apply gate readiness",
        failures,
    )
    check(
        validation["route_choice_adoption_bundle_preview"]["real_queue_write_performed"] is False,
        "validation should keep route adoption bundle real queue writes false",
        failures,
    )
    check(
        validation["route_choice_adoption_bundle_preview"]["route_adoption_authorized"] is False,
        "validation should keep route adoption bundle route adoption unauthorized",
        failures,
    )
    check(
        validation["route_choice_adoption_bundle_preview"]["execution_authorized"] is False,
        "validation should keep route adoption bundle execution unauthorized",
        failures,
    )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=34 failures={len(failures)}")
        return 1

    print("PASS commander routing fixtures")
    print("PASS selector no-elevation fixtures")
    print("PASS local executor allowed/forbidden fixtures")
    print("PASS failure handling stop-loop fixtures")
    print("PASS ColaMeta readiness fixture")
    print("PASS queue proposal-only fixture")
    print("PASS route choice handoff reconciliation fixture")
    print("PASS CLOSED append boundary fixture")
    print("PASS route choice template readiness fixture")
    print("PASS route choice end-to-end readiness fixture")
    print("PASS route choice adoption bundle preview fixture")
    print("PASS active Jenn governance gate production block fixture")
    print("PASS active Jenn governance gate handoff validation fixture")
    print("PASS direct active Jenn governance gate adoption block fixture")
    print("PASS public active Jenn governance gate adoption CLI block fixture")
    print("PASS route choice queue proposal fixture")
    print("PASS reviewed queue mutation fixture")
    print("PASS reviewed route adoption preview fixture")
    print("PASS reviewed route adoption apply gate fixture")
    print("PASS route option stop gate fixture")
    print("cases=34 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
