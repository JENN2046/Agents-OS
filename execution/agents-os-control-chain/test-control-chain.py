#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Control Chain v0.1."""

from __future__ import annotations

import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
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

        generic_p3_queue_path = Path(temp_dir) / "generic-p3-governance-gate-queue.md"
        generic_p3_queue_text = """# generic P3 governance gate fixture

## NOW

### NOW-001: Call provider

Call provider and start service.

## NEXT

_No active NEXT items._

## CLOSED

```text
prior_task: closed
```
"""
        generic_p3_queue_path.write_text(generic_p3_queue_text, encoding="utf-8")
        generic_p3_handoff = chain.route_choice_handoff_reconciliation(generic_p3_queue_path)
        generic_p3_bundle = chain.route_choice_adoption_bundle_preview(
            "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
            "先准备 formal Memory candidate gate v0.1；只做候选和确认模型，不写正式 Memory。",
            generic_p3_queue_path,
            chain.ROUTE_SELECTION_PACKAGE,
        )
        generic_p3_preview = chain.reviewed_route_adoption_preview(
            route_choice_proposal,
            route_review,
            generic_p3_queue_path,
        )
        generic_p3_apply = chain.reviewed_route_adoption_apply_gate(
            route_choice_proposal,
            route_review,
            generic_p3_queue_path,
            apply=True,
        )
        check(
            generic_p3_handoff["passed"] is True
            and generic_p3_handoff["active_jenn_governance_gate"] is True
            and generic_p3_handoff["machine_next_user_action"]["status"] == "governance_decision_required"
            and generic_p3_handoff["dashboard_next_user_action"]["status"] == "governance_decision_required",
            f"generic P3 blocked NOW must reconcile as an active Jenn gate: {generic_p3_handoff['errors']}",
            failures,
        )
        check(
            generic_p3_bundle["passed"] is False
            and generic_p3_bundle["active_jenn_governance_gate"] is True
            and generic_p3_bundle["can_apply_with_separate_apply_gate"] is False,
            "generic P3 blocked NOW must fail closed in the adoption bundle",
            failures,
        )
        check(
            generic_p3_preview["passed"] is False
            and generic_p3_preview["active_jenn_governance_gate"] is True
            and generic_p3_preview["queue_mutation_preview_authorized"] is False,
            "generic P3 blocked NOW must fail closed in the direct adoption preview",
            failures,
        )
        check(
            generic_p3_apply["passed"] is False
            and generic_p3_apply["active_jenn_governance_gate"] is True
            and generic_p3_apply["queue_adoption_authorized"] is False
            and generic_p3_apply["write_performed"] is False,
            "generic P3 blocked NOW must fail closed in the direct apply API",
            failures,
        )
        generic_p3_cli_apply = subprocess.run(
            [
                sys.executable,
                str(ROOT / "control_chain.py"),
                "reviewed-route-adoption-apply-gate",
                "--proposal-json",
                str(route_proposal_json),
                "--review-json",
                str(route_review_json),
                "--queue",
                str(generic_p3_queue_path),
                "--apply",
                "--json",
            ],
            cwd=chain.WORKSPACE_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        generic_p3_cli_result = json.loads(generic_p3_cli_apply.stdout)
        check(
            generic_p3_cli_apply.returncode == 1
            and generic_p3_cli_result["passed"] is False
            and generic_p3_cli_result["active_jenn_governance_gate"] is True
            and generic_p3_cli_result["write_performed"] is False,
            f"generic P3 blocked NOW must fail closed in the public CLI: {generic_p3_cli_apply.stderr}",
            failures,
        )
        check(
            generic_p3_queue_path.read_text(encoding="utf-8") == generic_p3_queue_text,
            "generic P3 bundle/API/CLI attacks must preserve exact queue bytes",
            failures,
        )

        byte_swap_queue_path = Path(temp_dir) / "byte-swap-queue.md"
        byte_swap_queue_path.write_text(route_queue_text, encoding="utf-8")
        original_snapshot_handoff = chain.route_choice_handoff_reconciliation_from_snapshot

        def byte_swap_after_handoff(queue_path: Path, snapshot: dict) -> dict:
            result = original_snapshot_handoff(queue_path, snapshot)
            byte_swap_queue_path.write_text(generic_p3_queue_text, encoding="utf-8")
            return result

        chain.route_choice_handoff_reconciliation_from_snapshot = byte_swap_after_handoff
        try:
            byte_swap_apply = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                byte_swap_queue_path,
                apply=True,
            )
        finally:
            chain.route_choice_handoff_reconciliation_from_snapshot = original_snapshot_handoff
        check(
            byte_swap_apply["passed"] is False
            and byte_swap_apply["queue_adoption_authorized"] is False
            and byte_swap_apply["write_performed"] is False,
            "same-inode queue byte swap after handoff must fail before route-adoption write",
            failures,
        )
        check(
            any("queue bytes changed after handoff attestation" in error for error in byte_swap_apply["errors"]),
            f"same-inode byte swap should report the failed byte binding: {byte_swap_apply['errors']}",
            failures,
        )
        check(
            byte_swap_queue_path.read_text(encoding="utf-8") == generic_p3_queue_text,
            "failed byte-swap attack must not overwrite the replacement queue bytes",
            failures,
        )

        symlink_swap_queue_path = Path(temp_dir) / "symlink-swap-queue.md"
        symlink_swap_queue_path.write_text(route_queue_text, encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="agents-os-external-queue-target-") as external_temp_dir:
            external_queue_path = Path(external_temp_dir) / "external-target.md"
            external_queue_text = "external target must remain unchanged\n"
            external_queue_path.write_text(external_queue_text, encoding="utf-8")

            def symlink_swap_after_handoff(queue_path: Path, snapshot: dict) -> dict:
                result = original_snapshot_handoff(queue_path, snapshot)
                symlink_swap_queue_path.unlink()
                symlink_swap_queue_path.symlink_to(external_queue_path)
                return result

            chain.route_choice_handoff_reconciliation_from_snapshot = symlink_swap_after_handoff
            try:
                symlink_swap_apply = chain.reviewed_route_adoption_apply_gate(
                    route_choice_proposal,
                    route_review,
                    symlink_swap_queue_path,
                    apply=True,
                )
            finally:
                chain.route_choice_handoff_reconciliation_from_snapshot = original_snapshot_handoff
            check(
                symlink_swap_apply["passed"] is False
                and symlink_swap_apply["queue_adoption_authorized"] is False
                and symlink_swap_apply["write_performed"] is False,
                "queue symlink swap after handoff must fail before route-adoption write",
                failures,
            )
            check(
                any("queue binding target is no longer a regular file" in error for error in symlink_swap_apply["errors"]),
                f"symlink swap should report the failed file-identity binding: {symlink_swap_apply['errors']}",
                failures,
            )
            check(
                external_queue_path.read_text(encoding="utf-8") == external_queue_text,
                "failed symlink-swap attack must not write the external target",
                failures,
            )

        read_skew_queue_path = Path(temp_dir) / "machine-dashboard-read-skew-queue.md"
        read_skew_queue_path.write_text(route_queue_text, encoding="utf-8")
        original_import_module = chain.import_module
        read_skew_state = {"triggered": False}

        def read_skew_import(path: Path, name: str) -> ModuleType:
            module = original_import_module(path, name)
            if Path(path) == chain.DASHBOARD and not read_skew_state["triggered"]:
                read_skew_queue_path.write_text(generic_p3_queue_text, encoding="utf-8")
                read_skew_state["triggered"] = True
            return module

        chain.import_module = read_skew_import
        try:
            read_skew_handoff = chain.route_choice_handoff_reconciliation(read_skew_queue_path)
        finally:
            chain.import_module = original_import_module
        check(read_skew_state["triggered"] is True, "Machine/Dashboard read-skew attack hook should run", failures)
        check(
            read_skew_handoff["passed"] is False
            and read_skew_handoff["aligned"] is False
            and read_skew_handoff["write_performed"] is False,
            "Machine/Dashboard pathname read-skew must fail the bound snapshot reconciliation",
            failures,
        )
        check(
            any("queue bytes changed after handoff attestation" in error for error in read_skew_handoff["errors"]),
            f"Machine/Dashboard read-skew should report queue byte drift: {read_skew_handoff['errors']}",
            failures,
        )

        post_cas_byte_queue_path = Path(temp_dir) / "post-cas-byte-swap-queue.md"
        post_cas_byte_queue_path.write_text(route_queue_text, encoding="utf-8")
        original_rename_exchange = chain.rename_exchange
        post_cas_byte_state = {"triggered": False}

        def post_cas_byte_swap(parent_fd: int, first_name: str, second_name: str) -> None:
            if not post_cas_byte_state["triggered"]:
                post_cas_byte_state["triggered"] = True
                post_cas_byte_queue_path.write_text(generic_p3_queue_text, encoding="utf-8")
            original_rename_exchange(parent_fd, first_name, second_name)

        chain.rename_exchange = post_cas_byte_swap
        try:
            post_cas_byte_apply = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                post_cas_byte_queue_path,
                apply=True,
            )
        finally:
            chain.rename_exchange = original_rename_exchange
        check(post_cas_byte_state["triggered"] is True, "post-CAS byte-swap attack hook should run", failures)
        check(
            post_cas_byte_apply["passed"] is False
            and post_cas_byte_apply["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and post_cas_byte_apply["queue_state"] == "UNKNOWN"
            and post_cas_byte_apply["queue_commit_attempted"] is True
            and post_cas_byte_apply["rollback_performed"] is True
            and post_cas_byte_apply["write_performed"] is True
            and post_cas_byte_apply["queue_adoption_authorized"] is False
            and post_cas_byte_apply["queue_write_authorized"] is False
            and post_cas_byte_apply["requires_jenn_decision"] is True,
            f"post-CAS same-inode byte swap must roll back and report PARTIAL_OR_UNKNOWN: {post_cas_byte_apply}",
            failures,
        )
        check(
            post_cas_byte_queue_path.read_text(encoding="utf-8") == generic_p3_queue_text,
            "post-CAS byte swap must preserve attacker-updated queue bytes instead of overwriting them",
            failures,
        )

        post_cas_link_queue_path = Path(temp_dir) / "post-cas-hardlink-queue.md"
        post_cas_link_alias_path = Path(temp_dir) / "post-cas-hardlink-alias.md"
        post_cas_link_queue_path.write_text(route_queue_text, encoding="utf-8")
        post_cas_link_state = {"triggered": False}

        def post_cas_hardlink(parent_fd: int, first_name: str, second_name: str) -> None:
            if not post_cas_link_state["triggered"]:
                post_cas_link_state["triggered"] = True
                os.link(post_cas_link_queue_path, post_cas_link_alias_path)
            original_rename_exchange(parent_fd, first_name, second_name)

        chain.rename_exchange = post_cas_hardlink
        try:
            post_cas_link_apply = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                post_cas_link_queue_path,
                apply=True,
            )
        finally:
            chain.rename_exchange = original_rename_exchange
        check(post_cas_link_state["triggered"] is True, "post-CAS hardlink attack hook should run", failures)
        check(
            post_cas_link_apply["passed"] is False
            and post_cas_link_apply["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and post_cas_link_apply["queue_state"] == "UNKNOWN"
            and post_cas_link_apply["rollback_performed"] is True
            and post_cas_link_apply["write_performed"] is True
            and post_cas_link_apply["queue_adoption_authorized"] is False,
            f"post-CAS hardlink injection must fail closed with truthful write evidence: {post_cas_link_apply}",
            failures,
        )
        check(
            post_cas_link_queue_path.read_text(encoding="utf-8") == route_queue_text
            and post_cas_link_alias_path.read_text(encoding="utf-8") == route_queue_text,
            "post-CAS hardlink injection must not expose candidate writes through the alias",
            failures,
        )
        post_cas_link_alias_path.unlink()

        original_temp_write = chain.write_transaction_temp_fd

        replacement_mode_queue_path = Path(temp_dir) / "replacement-mode-drift-queue.md"
        replacement_mode_queue_path.write_text(route_queue_text, encoding="utf-8")
        replacement_mode_queue_path.chmod(0o600)
        replacement_mode_state = {"triggered": False}

        def drift_replacement_mode_after_write(file_fd: int, data: bytes) -> None:
            original_temp_write(file_fd, data)
            os.fchmod(file_fd, 0o640)
            replacement_mode_state["triggered"] = True

        chain.write_transaction_temp_fd = drift_replacement_mode_after_write
        try:
            replacement_mode_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                replacement_mode_queue_path,
                apply=True,
            )
        finally:
            chain.write_transaction_temp_fd = original_temp_write
        check(
            replacement_mode_state["triggered"] is True,
            "replacement mode drift hook should run",
            failures,
        )
        check(
            replacement_mode_result["passed"] is False
            and replacement_mode_result["transaction_outcome"] == "NO_WRITE"
            and replacement_mode_result["queue_state"] == "UNCHANGED"
            and replacement_mode_result["queue_commit_attempted"] is False
            and replacement_mode_result["write_performed"] is False
            and replacement_mode_result["temp_cleanup_confirmed"] is True
            and replacement_mode_result["queue_adoption_authorized"] is False
            and replacement_mode_queue_path.read_text(encoding="utf-8") == route_queue_text
            and stat.S_IMODE(replacement_mode_queue_path.stat().st_mode) == 0o600,
            (
                "replacement mode drift before exchange must preserve exact old queue state "
                f"and report NO_WRITE: {replacement_mode_result}"
            ),
            failures,
        )
        check(
            any(
                "mode does not match the original queue" in error
                for error in replacement_mode_result["errors"]
            ),
            f"replacement mode drift should report original-metadata mismatch: {replacement_mode_result}",
            failures,
        )

        replacement_gid_queue_path = Path(temp_dir) / "replacement-gid-drift-queue.md"
        replacement_gid_queue_path.write_text(route_queue_text, encoding="utf-8")
        original_queue_gid = replacement_gid_queue_path.stat().st_gid
        replacement_gid_state: dict[str, object] = {"triggered": False, "file_fd": None}
        original_fstat = chain.os.fstat

        class GidDriftStat:
            def __init__(self, source: os.stat_result, gid: int) -> None:
                self._source = source
                self.st_gid = gid

            def __getattr__(self, name: str) -> object:
                return getattr(self._source, name)

        def mock_replacement_gid_after_write(file_fd: int, data: bytes) -> None:
            original_temp_write(file_fd, data)
            replacement_gid_state["file_fd"] = file_fd
            replacement_gid_state["triggered"] = True

        def replacement_gid_fstat(file_fd: int) -> os.stat_result:
            result = original_fstat(file_fd)
            if (
                replacement_gid_state["triggered"] is True
                and replacement_gid_state["file_fd"] == file_fd
            ):
                return GidDriftStat(result, result.st_gid + 1)  # type: ignore[return-value]
            return result

        chain.write_transaction_temp_fd = mock_replacement_gid_after_write
        chain.os.fstat = replacement_gid_fstat
        try:
            replacement_gid_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                replacement_gid_queue_path,
                apply=True,
            )
        finally:
            chain.os.fstat = original_fstat
            chain.write_transaction_temp_fd = original_temp_write
        check(
            replacement_gid_state["triggered"] is True,
            "replacement gid drift hook should run",
            failures,
        )
        check(
            replacement_gid_result["passed"] is False
            and replacement_gid_result["transaction_outcome"] == "NO_WRITE"
            and replacement_gid_result["queue_state"] == "UNCHANGED"
            and replacement_gid_result["queue_commit_attempted"] is False
            and replacement_gid_result["write_performed"] is False
            and replacement_gid_result["temp_cleanup_confirmed"] is True
            and replacement_gid_result["queue_adoption_authorized"] is False
            and replacement_gid_queue_path.read_text(encoding="utf-8") == route_queue_text
            and replacement_gid_queue_path.stat().st_gid == original_queue_gid,
            (
                "replacement gid drift before exchange must preserve exact old queue state "
                f"and report NO_WRITE: {replacement_gid_result}"
            ),
            failures,
        )
        check(
            any(
                "group does not match the original queue" in error
                for error in replacement_gid_result["errors"]
            ),
            f"replacement gid drift should report original-metadata mismatch: {replacement_gid_result}",
            failures,
        )

        original_extended_queue_path = Path(temp_dir) / "original-extended-metadata-queue.md"
        original_extended_queue_path.write_text(route_queue_text, encoding="utf-8")
        original_extended_identity = (
            original_extended_queue_path.stat().st_dev,
            original_extended_queue_path.stat().st_ino,
        )
        original_extended_metadata = chain.file_descriptor_extended_metadata
        extended_metadata_state = {"inspected": False}

        def mock_original_extended_metadata(file_fd: int) -> tuple[dict | None, str | None]:
            file_stat = os.fstat(file_fd)
            if (file_stat.st_dev, file_stat.st_ino) == original_extended_identity:
                extended_metadata_state["inspected"] = True
                return {
                    "count": 3,
                    "names_sha256": hashlib.sha256(
                        b"user.evidence\0system.posix_acl_access\0security.selinux"
                    ).hexdigest(),
                }, None
            return original_extended_metadata(file_fd)

        chain.file_descriptor_extended_metadata = mock_original_extended_metadata
        try:
            original_extended_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                original_extended_queue_path,
                apply=True,
            )
        finally:
            chain.file_descriptor_extended_metadata = original_extended_metadata
        check(
            extended_metadata_state["inspected"] is True,
            "original extended metadata fixture should be inspected",
            failures,
        )
        check(
            original_extended_result["passed"] is False
            and original_extended_result["transaction_outcome"] == "NO_WRITE"
            and original_extended_result["queue_state"] == "UNCHANGED"
            and original_extended_result["queue_commit_attempted"] is False
            and original_extended_result["write_performed"] is False
            and original_extended_result["temp_cleanup_confirmed"] is True
            and original_extended_result["queue_adoption_authorized"] is False
            and original_extended_queue_path.read_text(encoding="utf-8") == route_queue_text,
            (
                "original xattr, ACL, or security-label metadata must reject replacement "
                f"with exact old queue state: {original_extended_result}"
            ),
            failures,
        )
        check(
            any(
                "extended metadata" in error and "NO_WRITE" in error
                for error in original_extended_result["errors"]
            ),
            f"original extended metadata rejection should be explicit: {original_extended_result}",
            failures,
        )

        replacement_extended_queue_path = (
            Path(temp_dir) / "replacement-extended-metadata-drift-queue.md"
        )
        replacement_extended_queue_path.write_text(route_queue_text, encoding="utf-8")
        replacement_extended_state: dict[str, object] = {
            "triggered": False,
            "file_fd": None,
        }

        def mark_replacement_extended_metadata_after_write(
            file_fd: int,
            data: bytes,
        ) -> None:
            original_temp_write(file_fd, data)
            replacement_extended_state["file_fd"] = file_fd
            replacement_extended_state["triggered"] = True

        def mock_replacement_extended_metadata(
            file_fd: int,
        ) -> tuple[dict | None, str | None]:
            if (
                replacement_extended_state["triggered"] is True
                and replacement_extended_state["file_fd"] == file_fd
            ):
                return {
                    "count": 1,
                    "names_sha256": hashlib.sha256(b"user.evidence").hexdigest(),
                }, None
            return original_extended_metadata(file_fd)

        chain.write_transaction_temp_fd = mark_replacement_extended_metadata_after_write
        chain.file_descriptor_extended_metadata = mock_replacement_extended_metadata
        try:
            replacement_extended_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                replacement_extended_queue_path,
                apply=True,
            )
        finally:
            chain.file_descriptor_extended_metadata = original_extended_metadata
            chain.write_transaction_temp_fd = original_temp_write
        check(
            replacement_extended_state["triggered"] is True,
            "replacement extended metadata drift fixture should run",
            failures,
        )
        check(
            replacement_extended_result["passed"] is False
            and replacement_extended_result["transaction_outcome"] == "NO_WRITE"
            and replacement_extended_result["queue_state"] == "UNCHANGED"
            and replacement_extended_result["queue_commit_attempted"] is False
            and replacement_extended_result["write_performed"] is False
            and replacement_extended_result["temp_cleanup_confirmed"] is True
            and replacement_extended_result["queue_adoption_authorized"] is False
            and replacement_extended_queue_path.read_text(encoding="utf-8") == route_queue_text,
            (
                "replacement xattr, ACL, or security-label drift before exchange must "
                f"preserve exact old queue state: {replacement_extended_result}"
            ),
            failures,
        )
        check(
            any(
                "replacement extended metadata must be empty" in error
                for error in replacement_extended_result["errors"]
            ),
            f"replacement extended metadata drift should be explicit: {replacement_extended_result}",
            failures,
        )

        replacement_link_queue_path = Path(temp_dir) / "replacement-link-drift-queue.md"
        replacement_link_alias_path = Path(temp_dir) / "replacement-link-drift-alias.md"
        replacement_link_queue_path.write_text(route_queue_text, encoding="utf-8")
        replacement_link_state = {"triggered": False}

        def add_replacement_link_after_write(file_fd: int, data: bytes) -> None:
            original_temp_write(file_fd, data)
            temp_entries = list(
                replacement_link_queue_path.parent.glob(
                    f".{replacement_link_queue_path.name}.agents-os-txn-*.tmp"
                )
            )
            if len(temp_entries) != 1:
                raise OSError(errno.ENOENT, "replacement temp fixture entry is unavailable")
            os.link(temp_entries[0], replacement_link_alias_path)
            replacement_link_state["triggered"] = True

        chain.write_transaction_temp_fd = add_replacement_link_after_write
        try:
            replacement_link_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                replacement_link_queue_path,
                apply=True,
            )
        finally:
            chain.write_transaction_temp_fd = original_temp_write
        check(
            replacement_link_state["triggered"] is True,
            "replacement hard-link drift hook should run",
            failures,
        )
        check(
            replacement_link_result["passed"] is False
            and replacement_link_result["transaction_outcome"] == "NO_WRITE"
            and replacement_link_result["queue_state"] == "UNCHANGED"
            and replacement_link_result["queue_commit_attempted"] is False
            and replacement_link_result["write_performed"] is False
            and replacement_link_result["temp_cleanup_confirmed"] is False
            and replacement_link_result["queue_adoption_authorized"] is False
            and replacement_link_result["requires_jenn_decision"] is True
            and replacement_link_queue_path.read_text(encoding="utf-8") == route_queue_text,
            (
                "replacement hard-link drift before exchange must preserve exact old active "
                f"queue bytes and report NO_WRITE with unresolved cleanup: {replacement_link_result}"
            ),
            failures,
        )
        check(
            any(
                "hard-link count does not match nlink=1" in error
                for error in replacement_link_result["errors"]
            ),
            f"replacement hard-link drift should report original-metadata mismatch: {replacement_link_result}",
            failures,
        )
        if replacement_link_alias_path.exists():
            replacement_link_alias_path.unlink()

        replacement_uid_queue_path = Path(temp_dir) / "replacement-uid-drift-queue.md"
        replacement_uid_queue_path.write_text(route_queue_text, encoding="utf-8")
        replacement_uid_state: dict[str, object] = {"triggered": False, "file_fd": None}
        original_fstat = chain.os.fstat

        class UidDriftStat:
            def __init__(self, source: os.stat_result, uid: int) -> None:
                self._source = source
                self.st_uid = uid

            def __getattr__(self, name: str) -> object:
                return getattr(self._source, name)

        def mock_replacement_uid_after_write(file_fd: int, data: bytes) -> None:
            original_temp_write(file_fd, data)
            replacement_uid_state["file_fd"] = file_fd
            replacement_uid_state["triggered"] = True

        def replacement_uid_fstat(file_fd: int) -> os.stat_result:
            result = original_fstat(file_fd)
            if (
                replacement_uid_state["triggered"] is True
                and replacement_uid_state["file_fd"] == file_fd
            ):
                return UidDriftStat(result, result.st_uid + 1)  # type: ignore[return-value]
            return result

        chain.write_transaction_temp_fd = mock_replacement_uid_after_write
        chain.os.fstat = replacement_uid_fstat
        try:
            replacement_uid_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                replacement_uid_queue_path,
                apply=True,
            )
        finally:
            chain.os.fstat = original_fstat
            chain.write_transaction_temp_fd = original_temp_write
        check(
            replacement_uid_state["triggered"] is True,
            "replacement uid mock drift hook should run",
            failures,
        )
        check(
            replacement_uid_result["passed"] is False
            and replacement_uid_result["transaction_outcome"] == "NO_WRITE"
            and replacement_uid_result["queue_state"] == "UNCHANGED"
            and replacement_uid_result["queue_commit_attempted"] is False
            and replacement_uid_result["write_performed"] is False
            and replacement_uid_result["temp_cleanup_confirmed"] is True
            and replacement_uid_result["queue_adoption_authorized"] is False
            and replacement_uid_queue_path.read_text(encoding="utf-8") == route_queue_text,
            (
                "replacement uid drift before exchange must preserve exact old queue state "
                f"and report NO_WRITE: {replacement_uid_result}"
            ),
            failures,
        )
        check(
            any(
                "owner does not match the original queue" in error
                for error in replacement_uid_result["errors"]
            ),
            f"replacement uid drift should report original-metadata mismatch: {replacement_uid_result}",
            failures,
        )

        preexchange_metadata_queue_path = (
            Path(temp_dir) / "preexchange-replacement-mode-drift-queue.md"
        )
        preexchange_metadata_queue_path.write_text(route_queue_text, encoding="utf-8")
        preexchange_metadata_queue_path.chmod(0o600)
        original_named_validation = chain.validate_named_file_descriptor
        preexchange_metadata_state = {"triggered": False}

        def drift_replacement_mode_after_snapshot(
            parent_fd: int,
            name: str,
            file_fd: int,
            snapshot: dict,
            *,
            exchanged: bool = False,
        ) -> list[str]:
            result = original_named_validation(
                parent_fd,
                name,
                file_fd,
                snapshot,
                exchanged=exchanged,
            )
            if (
                not exchanged
                and not preexchange_metadata_state["triggered"]
                and name.startswith(f".{preexchange_metadata_queue_path.name}.agents-os-txn-")
            ):
                os.fchmod(file_fd, 0o640)
                preexchange_metadata_state["triggered"] = True
            return result

        chain.validate_named_file_descriptor = drift_replacement_mode_after_snapshot
        try:
            preexchange_metadata_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                preexchange_metadata_queue_path,
                apply=True,
            )
        finally:
            chain.validate_named_file_descriptor = original_named_validation
        check(
            preexchange_metadata_state["triggered"] is True,
            "pre-exchange replacement metadata drift hook should run",
            failures,
        )
        check(
            preexchange_metadata_result["passed"] is False
            and preexchange_metadata_result["transaction_outcome"] == "NO_WRITE"
            and preexchange_metadata_result["queue_state"] == "UNCHANGED"
            and preexchange_metadata_result["queue_commit_attempted"] is False
            and preexchange_metadata_result["write_performed"] is False
            and preexchange_metadata_result["temp_cleanup_confirmed"] is True
            and preexchange_metadata_result["queue_adoption_authorized"] is False
            and preexchange_metadata_queue_path.read_text(encoding="utf-8")
            == route_queue_text
            and stat.S_IMODE(preexchange_metadata_queue_path.stat().st_mode) == 0o600,
            (
                "replacement metadata drift after snapshot but before exchange must preserve "
                f"exact old queue state and report NO_WRITE: {preexchange_metadata_result}"
            ),
            failures,
        )
        check(
            any(
                "pre-exchange" in error
                and "mode does not match the original queue" in error
                for error in preexchange_metadata_result["errors"]
            ),
            f"pre-exchange metadata drift should report exact stage mismatch: {preexchange_metadata_result}",
            failures,
        )

        postexchange_metadata_queue_path = (
            Path(temp_dir) / "postexchange-replacement-mode-drift-queue.md"
        )
        postexchange_metadata_queue_path.write_text(route_queue_text, encoding="utf-8")
        postexchange_metadata_queue_path.chmod(0o600)
        postexchange_metadata_state = {"triggered": False}

        def drift_replacement_mode_after_exchange(
            parent_fd: int,
            first_name: str,
            second_name: str,
        ) -> None:
            original_rename_exchange(parent_fd, first_name, second_name)
            if not postexchange_metadata_state["triggered"]:
                os.chmod(postexchange_metadata_queue_path, 0o640)
                postexchange_metadata_state["triggered"] = True

        chain.rename_exchange = drift_replacement_mode_after_exchange
        try:
            postexchange_metadata_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                postexchange_metadata_queue_path,
                apply=True,
            )
        finally:
            chain.rename_exchange = original_rename_exchange
        check(
            postexchange_metadata_state["triggered"] is True,
            "post-exchange replacement metadata drift hook should run",
            failures,
        )
        check(
            postexchange_metadata_result["passed"] is False
            and postexchange_metadata_result["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and postexchange_metadata_result["queue_state"] == "UNCHANGED"
            and postexchange_metadata_result["queue_commit_attempted"] is True
            and postexchange_metadata_result["rollback_performed"] is True
            and postexchange_metadata_result["write_performed"] is True
            and postexchange_metadata_result["queue_adoption_authorized"] is False
            and postexchange_metadata_result["requires_jenn_decision"] is True
            and postexchange_metadata_queue_path.read_text(encoding="utf-8") == route_queue_text
            and stat.S_IMODE(postexchange_metadata_queue_path.stat().st_mode) == 0o600,
            (
                "replacement metadata drift after exchange must roll back exact old queue "
                f"state and report PARTIAL_OR_UNKNOWN: {postexchange_metadata_result}"
            ),
            failures,
        )

        final_metadata_queue_path = Path(temp_dir) / "final-replacement-mode-drift-queue.md"
        final_metadata_queue_path.write_text(route_queue_text, encoding="utf-8")
        final_metadata_queue_path.chmod(0o600)
        expected_final_metadata_text, _ = chain.append_route_adoption_to_queue_text(
            route_queue_text,
            route_choice_proposal,
        )
        original_unlink_descriptor = chain.unlink_named_entry_if_descriptor
        final_metadata_state = {"triggered": False}

        def drift_replacement_mode_before_final_classification(
            parent_fd: int,
            name: str,
            file_fd: int,
        ) -> tuple[bool, str | None]:
            if not final_metadata_state["triggered"]:
                os.chmod(final_metadata_queue_path, 0o640)
                final_metadata_state["triggered"] = True
            return original_unlink_descriptor(parent_fd, name, file_fd)

        chain.unlink_named_entry_if_descriptor = (
            drift_replacement_mode_before_final_classification
        )
        try:
            final_metadata_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                final_metadata_queue_path,
                apply=True,
            )
        finally:
            chain.unlink_named_entry_if_descriptor = original_unlink_descriptor
        check(
            final_metadata_state["triggered"] is True,
            "final replacement metadata drift hook should run",
            failures,
        )
        check(
            final_metadata_result["passed"] is False
            and final_metadata_result["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and final_metadata_result["queue_state"] == "UNKNOWN"
            and final_metadata_result["queue_commit_attempted"] is True
            and final_metadata_result["rollback_performed"] is False
            and final_metadata_result["write_performed"] is True
            and final_metadata_result["queue_adoption_authorized"] is False
            and final_metadata_result["queue_write_authorized"] is False
            and final_metadata_result["requires_jenn_decision"] is True
            and final_metadata_queue_path.read_text(encoding="utf-8")
            == expected_final_metadata_text,
            (
                "replacement metadata drift after displaced-old cleanup must report UNKNOWN "
                f"without adoption authorization: {final_metadata_result}"
            ),
            failures,
        )
        check(
            any(
                "final replacement" in error
                and "mode does not match the original queue" in error
                for error in final_metadata_result["errors"]
            ),
            f"final replacement metadata drift should report exact mismatch: {final_metadata_result}",
            failures,
        )

        def run_precommit_fault(
            name: str,
            helper_name: str,
            replacement: object,
        ) -> tuple[dict, Path]:
            fault_queue_path = Path(temp_dir) / name
            fault_queue_path.write_text(route_queue_text, encoding="utf-8")
            original_helper = getattr(chain, helper_name)
            setattr(chain, helper_name, replacement)
            try:
                result = chain.reviewed_route_adoption_apply_gate(
                    route_choice_proposal,
                    route_review,
                    fault_queue_path,
                    apply=True,
                )
            finally:
                setattr(chain, helper_name, original_helper)
            return result, fault_queue_path

        original_os_write = chain.os.write
        partial_write_state = {"triggered": False}

        def partial_write_then_eio(file_fd: int, data: bytes) -> int:
            if not partial_write_state["triggered"]:
                partial_write_state["triggered"] = True
                prefix_size = max(1, len(data) // 3)
                original_os_write(file_fd, data[:prefix_size])
                raise OSError(errno.EIO, "injected partial transaction write")
            return original_os_write(file_fd, data)

        partial_write_result, partial_write_queue_path = run_precommit_fault(
            "partial-write-fault-queue.md",
            "write_all_transaction_fd",
            lambda file_fd, data: partial_write_then_eio(file_fd, data),
        )
        check(partial_write_state["triggered"] is True, "partial-write fault hook should run", failures)
        check(
            partial_write_result["passed"] is False
            and partial_write_result["transaction_outcome"] == "NO_WRITE"
            and partial_write_result["queue_state"] == "UNCHANGED"
            and partial_write_result["queue_commit_attempted"] is False
            and partial_write_result["write_performed"] is False
            and partial_write_result["temp_cleanup_confirmed"] is True
            and partial_write_result["queue_adoption_authorized"] is False,
            f"partial temp write must prove NO_WRITE without a false active-queue mutation claim: {partial_write_result}",
            failures,
        )
        check(
            partial_write_queue_path.read_text(encoding="utf-8") == route_queue_text,
            "partial temp write failure must preserve exact old active queue bytes",
            failures,
        )

        def injected_truncate_failure(file_fd: int, size: int) -> None:
            raise OSError(errno.EIO, "injected transaction truncate failure")

        truncate_result, truncate_queue_path = run_precommit_fault(
            "truncate-fault-queue.md",
            "truncate_transaction_temp_fd",
            injected_truncate_failure,
        )
        check(
            truncate_result["passed"] is False
            and truncate_result["transaction_outcome"] == "NO_WRITE"
            and truncate_result["queue_state"] == "UNCHANGED"
            and truncate_result["write_performed"] is False
            and truncate_result["temp_cleanup_confirmed"] is True
            and truncate_queue_path.read_text(encoding="utf-8") == route_queue_text,
            f"temp ftruncate failure must preserve exact old active queue bytes: {truncate_result}",
            failures,
        )

        def injected_file_fsync_failure(file_fd: int) -> None:
            raise OSError(errno.EIO, "injected transaction file fsync failure")

        file_fsync_result, file_fsync_queue_path = run_precommit_fault(
            "file-fsync-fault-queue.md",
            "fsync_transaction_file_fd",
            injected_file_fsync_failure,
        )
        check(
            file_fsync_result["passed"] is False
            and file_fsync_result["transaction_outcome"] == "NO_WRITE"
            and file_fsync_result["queue_state"] == "UNCHANGED"
            and file_fsync_result["write_performed"] is False
            and file_fsync_result["temp_cleanup_confirmed"] is True
            and file_fsync_queue_path.read_text(encoding="utf-8") == route_queue_text,
            f"temp fsync failure must preserve exact old active queue bytes: {file_fsync_result}",
            failures,
        )

        parent_fsync_queue_path = Path(temp_dir) / "parent-fsync-fault-queue.md"
        parent_fsync_queue_path.write_text(route_queue_text, encoding="utf-8")
        original_parent_fsync = chain.fsync_transaction_parent_fd
        parent_fsync_state = {"calls": 0}

        def injected_first_parent_fsync_failure(parent_fd: int) -> None:
            parent_fsync_state["calls"] += 1
            if parent_fsync_state["calls"] == 1:
                raise OSError(errno.EIO, "injected post-exchange parent fsync failure")
            original_parent_fsync(parent_fd)

        chain.fsync_transaction_parent_fd = injected_first_parent_fsync_failure
        try:
            parent_fsync_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                parent_fsync_queue_path,
                apply=True,
            )
        finally:
            chain.fsync_transaction_parent_fd = original_parent_fsync
        check(
            parent_fsync_result["passed"] is False
            and parent_fsync_result["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and parent_fsync_result["queue_state"] == "UNCHANGED"
            and parent_fsync_result["queue_commit_attempted"] is True
            and parent_fsync_result["rollback_performed"] is True
            and parent_fsync_result["write_performed"] is True
            and parent_fsync_result["queue_adoption_authorized"] is False
            and parent_fsync_queue_path.read_text(encoding="utf-8") == route_queue_text,
            f"post-exchange parent fsync failure must roll back with truthful PARTIAL evidence: {parent_fsync_result}",
            failures,
        )

        commit_cleanup_fsync_queue_path = Path(temp_dir) / "commit-cleanup-fsync-fault-queue.md"
        commit_cleanup_fsync_queue_path.write_text(route_queue_text, encoding="utf-8")
        expected_commit_cleanup_text, _ = chain.append_route_adoption_to_queue_text(
            route_queue_text,
            route_choice_proposal,
        )
        commit_cleanup_fsync_state = {"calls": 0}

        def injected_commit_cleanup_fsync_failure(parent_fd: int) -> None:
            commit_cleanup_fsync_state["calls"] += 1
            if commit_cleanup_fsync_state["calls"] == 2:
                raise OSError(errno.EIO, "injected commit-cleanup parent fsync failure")
            original_parent_fsync(parent_fd)

        chain.fsync_transaction_parent_fd = injected_commit_cleanup_fsync_failure
        try:
            commit_cleanup_fsync_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                commit_cleanup_fsync_queue_path,
                apply=True,
            )
        finally:
            chain.fsync_transaction_parent_fd = original_parent_fsync
        check(
            commit_cleanup_fsync_result["passed"] is False
            and commit_cleanup_fsync_result["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and commit_cleanup_fsync_result["queue_state"] == "UPDATED"
            and commit_cleanup_fsync_result["queue_commit_attempted"] is True
            and commit_cleanup_fsync_result["rollback_performed"] is False
            and commit_cleanup_fsync_result["write_performed"] is True
            and commit_cleanup_fsync_result["temp_cleanup_confirmed"] is True
            and commit_cleanup_fsync_result["parent_directory_fsynced"] is False
            and commit_cleanup_fsync_result["queue_adoption_authorized"] is False
            and commit_cleanup_fsync_queue_path.read_text(encoding="utf-8")
            == expected_commit_cleanup_text,
            (
                "commit-cleanup fsync failure must preserve exact new bytes and "
                f"report truthful PARTIAL evidence: {commit_cleanup_fsync_result}"
            ),
            failures,
        )

        post_validation_queue_path = Path(temp_dir) / "post-validation-fault-queue.md"
        post_validation_queue_path.write_text(route_queue_text, encoding="utf-8")
        original_exchange_validation = chain.validate_transaction_exchange

        def injected_post_exchange_validation(*args: object, **kwargs: object) -> list[str]:
            raise OSError(errno.EIO, "injected post-exchange validation failure")

        chain.validate_transaction_exchange = injected_post_exchange_validation
        try:
            post_validation_result = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                post_validation_queue_path,
                apply=True,
            )
        finally:
            chain.validate_transaction_exchange = original_exchange_validation
        check(
            post_validation_result["passed"] is False
            and post_validation_result["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and post_validation_result["queue_state"] == "UNCHANGED"
            and post_validation_result["queue_commit_attempted"] is True
            and post_validation_result["rollback_performed"] is True
            and post_validation_result["write_performed"] is True
            and post_validation_result["queue_adoption_authorized"] is False
            and post_validation_queue_path.read_text(encoding="utf-8") == route_queue_text,
            f"post-exchange validation failure must roll back with truthful PARTIAL evidence: {post_validation_result}",
            failures,
        )

        if hasattr(os, "fork"):
            preexchange_kill_queue_path = Path(temp_dir) / "preexchange-kill-queue.md"
            preexchange_kill_queue_path.write_text(route_queue_text, encoding="utf-8")
            def kill_after_temp_fsync(file_fd: int, data: bytes) -> None:
                original_temp_write(file_fd, data)
                os.kill(os.getpid(), signal.SIGKILL)

            chain.write_transaction_temp_fd = kill_after_temp_fsync
            preexchange_child = os.fork()
            if preexchange_child == 0:
                chain.reviewed_route_adoption_apply_gate(
                    route_choice_proposal,
                    route_review,
                    preexchange_kill_queue_path,
                    apply=True,
                )
                os._exit(70)
            _, preexchange_status = os.waitpid(preexchange_child, 0)
            chain.write_transaction_temp_fd = original_temp_write
            check(
                os.WIFSIGNALED(preexchange_status)
                and os.WTERMSIG(preexchange_status) == signal.SIGKILL
                and preexchange_kill_queue_path.read_text(encoding="utf-8") == route_queue_text,
                "SIGKILL after temp fsync must leave exact old active queue bytes",
                failures,
            )
            preexchange_residue = list(
                preexchange_kill_queue_path.parent.glob(
                    f".{preexchange_kill_queue_path.name}.agents-os-txn-*.tmp"
                )
            )
            check(
                len(preexchange_residue) == 1,
                "SIGKILL after temp fsync must leave one discoverable transaction residue",
                failures,
            )
            preexchange_replay = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                preexchange_kill_queue_path,
                apply=True,
            )
            check(
                preexchange_replay["passed"] is False
                and preexchange_replay["transaction_outcome"] == "NO_WRITE"
                and preexchange_replay["queue_state"] == "UNCHANGED"
                and preexchange_replay["queue_commit_attempted"] is False
                and preexchange_replay["write_performed"] is False
                and preexchange_replay["temp_cleanup_confirmed"] is False
                and preexchange_replay["requires_jenn_decision"] is True
                and preexchange_replay["queue_adoption_authorized"] is False
                and preexchange_kill_queue_path.read_text(encoding="utf-8")
                == route_queue_text,
                (
                    "next invocation after pre-exchange SIGKILL must fail closed on "
                    f"bound residue without writing: {preexchange_replay}"
                ),
                failures,
            )
            check(
                any(
                    "residue requires reconciliation" in error
                    and "device=" in error
                    and "inode=" in error
                    for error in preexchange_replay["errors"]
                ),
                (
                    "pre-exchange SIGKILL residue must carry identity-bound "
                    f"reconciliation evidence: {preexchange_replay}"
                ),
                failures,
            )

            postexchange_kill_queue_path = Path(temp_dir) / "postexchange-kill-queue.md"
            postexchange_kill_queue_path.write_text(route_queue_text, encoding="utf-8")
            expected_postexchange_text, _ = chain.append_route_adoption_to_queue_text(
                route_queue_text,
                route_choice_proposal,
            )

            def kill_after_atomic_exchange(parent_fd: int, first_name: str, second_name: str) -> None:
                original_rename_exchange(parent_fd, first_name, second_name)
                os.kill(os.getpid(), signal.SIGKILL)

            chain.rename_exchange = kill_after_atomic_exchange
            postexchange_child = os.fork()
            if postexchange_child == 0:
                chain.reviewed_route_adoption_apply_gate(
                    route_choice_proposal,
                    route_review,
                    postexchange_kill_queue_path,
                    apply=True,
                )
                os._exit(71)
            _, postexchange_status = os.waitpid(postexchange_child, 0)
            chain.rename_exchange = original_rename_exchange
            check(
                os.WIFSIGNALED(postexchange_status)
                and os.WTERMSIG(postexchange_status) == signal.SIGKILL
                and postexchange_kill_queue_path.read_text(encoding="utf-8") == expected_postexchange_text,
                "SIGKILL after atomic exchange must leave exact new active queue bytes, never a torn queue",
                failures,
            )
            postexchange_residue = list(
                postexchange_kill_queue_path.parent.glob(
                    f".{postexchange_kill_queue_path.name}.agents-os-txn-*.tmp"
                )
            )
            check(
                len(postexchange_residue) == 1,
                "SIGKILL after atomic exchange must leave one discoverable transaction residue",
                failures,
            )
            postexchange_replay = chain.reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_review,
                postexchange_kill_queue_path,
                apply=True,
            )
            check(
                postexchange_replay["passed"] is False
                and postexchange_replay["transaction_outcome"] == "NO_WRITE"
                and postexchange_replay["queue_state"] == "UNCHANGED"
                and postexchange_replay["queue_commit_attempted"] is False
                and postexchange_replay["write_performed"] is False
                and postexchange_replay["temp_cleanup_confirmed"] is False
                and postexchange_replay["requires_jenn_decision"] is True
                and postexchange_replay["queue_adoption_authorized"] is False
                and postexchange_kill_queue_path.read_text(encoding="utf-8")
                == expected_postexchange_text,
                (
                    "next invocation after post-exchange SIGKILL must preserve exact "
                    f"new bytes while requiring residue reconciliation: {postexchange_replay}"
                ),
                failures,
            )
            check(
                any(
                    "residue requires reconciliation" in error
                    and "device=" in error
                    and "inode=" in error
                    for error in postexchange_replay["errors"]
                ),
                (
                    "post-exchange SIGKILL residue must carry identity-bound "
                    f"reconciliation evidence: {postexchange_replay}"
                ),
                failures,
            )

        symlink_residue_queue_path = Path(temp_dir) / "symlink-residue-queue.md"
        symlink_residue_queue_path.write_text(route_queue_text, encoding="utf-8")
        symlink_residue_target = Path(temp_dir) / "symlink-residue-target.md"
        symlink_residue_target.write_text("do not follow\n", encoding="utf-8")
        symlink_residue_name = (
            f".{symlink_residue_queue_path.name}.agents-os-txn-"
            f"{'0' * 32}.tmp"
        )
        symlink_residue_path = symlink_residue_queue_path.parent / symlink_residue_name
        symlink_residue_path.symlink_to(symlink_residue_target)
        symlink_residue_result = chain.reviewed_route_adoption_apply_gate(
            route_choice_proposal,
            route_review,
            symlink_residue_queue_path,
            apply=True,
        )
        check(
            symlink_residue_result["passed"] is False
            and symlink_residue_result["transaction_outcome"] == "NO_WRITE"
            and symlink_residue_result["queue_state"] == "UNCHANGED"
            and symlink_residue_result["queue_commit_attempted"] is False
            and symlink_residue_result["write_performed"] is False
            and symlink_residue_result["temp_cleanup_confirmed"] is False
            and symlink_residue_result["requires_jenn_decision"] is True
            and symlink_residue_result["queue_adoption_authorized"] is False
            and symlink_residue_queue_path.read_text(encoding="utf-8")
            == route_queue_text
            and symlink_residue_target.read_text(encoding="utf-8")
            == "do not follow\n",
            (
                "symlink transaction residue must fail closed without following or "
                f"writing either path: {symlink_residue_result}"
            ),
            failures,
        )
        check(
            any(
                "residue requires reconciliation" in error
                and "identity_unverified=" in error
                and symlink_residue_name in error
                for error in symlink_residue_result["errors"]
            ),
            (
                "symlink transaction residue must be reported as no-follow "
                f"identity-unverified evidence: {symlink_residue_result}"
            ),
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
        check(adoption_preview["queue_file_identity_bound"] is True, "reviewed route adoption preview must bind queue identity", failures)
        check(
            adoption_preview["queue_snapshot_sha256"] == hashlib.sha256(route_queue_text.encode("utf-8")).hexdigest(),
            "reviewed route adoption preview must bind the exact queue bytes",
            failures,
        )
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
        check(
            adoption_apply_preview["transaction_outcome"] == "NO_WRITE"
            and adoption_apply_preview["queue_state"] == "UNCHANGED",
            "route adoption apply preview must attest NO_WRITE/UNCHANGED",
            failures,
        )
        check(route_apply_queue_path.read_text(encoding="utf-8") == route_apply_queue_text, "route adoption apply preview should not change queue", failures)
        route_apply_before_stat = route_apply_queue_path.stat()
        adoption_apply = chain.reviewed_route_adoption_apply_gate(route_choice_proposal, route_review, route_apply_queue_path, apply=True)
        route_apply_text = route_apply_queue_path.read_text(encoding="utf-8")
        route_apply_after_stat = route_apply_queue_path.stat()
        check(adoption_apply["passed"], f"reviewed route adoption apply should pass: {adoption_apply['errors']}", failures)
        check(adoption_apply["active_queue_modified"] is True, "route adoption apply should mutate fixture queue", failures)
        check(adoption_apply["queue_write_authorized"] is True, "route adoption apply should authorize explicit queue write", failures)
        check(adoption_apply["queue_promotion_authorized"] is False, "route adoption apply must not authorize queue promotion", failures)
        check(adoption_apply["execution_authorized"] is False, "route adoption apply must not authorize execution", failures)
        check(adoption_apply["queue_file_identity_bound"] is True, "route adoption apply must preserve bound queue identity", failures)
        check(
            adoption_apply["queue_snapshot_sha256"] == hashlib.sha256(route_apply_queue_text.encode("utf-8")).hexdigest(),
            "route adoption apply must bind the exact pre-write queue bytes",
            failures,
        )
        check(
            adoption_apply["final_queue_sha256"] == hashlib.sha256(route_apply_text.encode("utf-8")).hexdigest(),
            "route adoption apply must attest the exact final queue bytes",
            failures,
        )
        check(
            adoption_apply["transaction_outcome"] == "COMMITTED"
            and adoption_apply["queue_state"] == "UPDATED"
            and adoption_apply["queue_commit_attempted"] is True
            and adoption_apply["write_performed"] is True
            and adoption_apply["temp_cleanup_confirmed"] is True
            and adoption_apply["parent_directory_fsynced"] is True,
            f"route adoption apply must prove a durable committed transaction: {adoption_apply}",
            failures,
        )
        check(
            route_apply_after_stat.st_ino != route_apply_before_stat.st_ino
            and stat.S_IMODE(route_apply_after_stat.st_mode) == stat.S_IMODE(route_apply_before_stat.st_mode)
            and route_apply_after_stat.st_uid == route_apply_before_stat.st_uid
            and route_apply_after_stat.st_gid == route_apply_before_stat.st_gid
            and route_apply_after_stat.st_nlink == 1,
            "committed route transaction must install a distinct inode with preserved security metadata",
            failures,
        )
        check(
            not list(route_apply_queue_path.parent.glob(f".{route_apply_queue_path.name}.agents-os-txn-*.tmp")),
            "committed route transaction must leave no reserved sibling temp entry",
            failures,
        )
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
        print(f"cases=58 failures={len(failures)}")
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
    print("PASS generic P3 Jenn governance gate block fixture")
    print("PASS queue byte-swap binding attack fixture")
    print("PASS queue symlink-swap binding attack fixture")
    print("PASS Machine/Dashboard read-skew binding attack fixture")
    print("PASS post-CAS byte-swap transaction attack fixture")
    print("PASS post-CAS hardlink transaction attack fixture")
    print("PASS replacement mode binding transaction fixture")
    print("PASS replacement gid binding transaction fixture")
    print("PASS replacement hard-link binding transaction fixture")
    print("PASS replacement uid mock binding transaction fixture")
    print("PASS original extended metadata NO_WRITE fixture")
    print("PASS replacement extended metadata NO_WRITE fixture")
    print("PASS pre-exchange replacement metadata binding fixture")
    print("PASS post-exchange replacement metadata rollback fixture")
    print("PASS final replacement metadata classification fixture")
    print("PASS partial-write transaction fault fixture")
    print("PASS ftruncate transaction fault fixture")
    print("PASS fsync transaction fault fixture")
    print("PASS post-exchange parent-fsync transaction fault fixture")
    print("PASS commit-cleanup parent-fsync transaction fault fixture")
    print("PASS post-exchange validation transaction fault fixture")
    print("PASS process-kill old-or-new transaction fixture")
    print("PASS process-kill transaction residue reconciliation fixture")
    print("PASS transaction residue no-follow fixture")
    print("PASS route choice queue proposal fixture")
    print("PASS reviewed queue mutation fixture")
    print("PASS reviewed route adoption preview fixture")
    print("PASS reviewed route adoption apply gate fixture")
    print("PASS route option stop gate fixture")
    print("cases=58 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
