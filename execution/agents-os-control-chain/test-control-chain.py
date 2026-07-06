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

    invalid_decision = chain.build_commander_decision(invalid)
    check(invalid_decision["decision"] == "reject_as_out_of_scope", "invalid candidate should be rejected", failures)

    local_preview = chain.build_track_preview(local_decision, "run_validation_command")
    check(local_preview["selected_track"] == "local_executor", "local preview should select local executor", failures)
    check(local_preview["track_authorized"] is True, "local preview should be track-authorized", failures)

    blocked_preview = chain.build_track_preview(provider_decision)
    check(blocked_preview["selected_track"] == "stop", "provider preview should select stop", failures)
    check(blocked_preview["track_authorized"] is False, "selector must not elevate blocked decision", failures)

    cola_preview = chain.build_track_preview(colameta_decision)
    check(cola_preview["selected_track"] == "colameta", "ColaMeta preview should select ColaMeta", failures)
    check(cola_preview["execution_authorization_scope"] == "none", "ColaMeta preview should keep scope none", failures)

    local_result = chain.local_executor_run(local_preview, "run_validation_command", command="python3 --version")
    check(local_result["passed"], f"local validation command should pass: {local_result['errors']}", failures)
    check(local_result["execution_performed"] is True, "local validation command should execute", failures)
    check(local_result["write_performed"] is False, "validation command should not write", failures)

    forbidden_result = chain.local_executor_run(local_preview, "provider_call")
    check(forbidden_result["validation_passed"] is False, "provider_call should be blocked", failures)

    cola_result = chain.colameta_readiness(cola_preview)
    check(cola_result["passed"], f"ColaMeta readiness should pass: {cola_result['errors']}", failures)
    check(cola_result["preview_only"] is True, "ColaMeta readiness should be preview-only", failures)
    check(cola_result["execution_performed"] is False, "ColaMeta readiness should not execute", failures)
    check(cola_result["effects"]["provider_call_performed"] is False, "ColaMeta readiness should not call provider", failures)
    check(cola_result["colameta_readiness"]["preflight"]["memory"]["content_read"] is False, "memory content should not be read", failures)

    proposal = chain.queue_update_proposal(local_result)
    check(proposal["proposal_only"] is True, "queue proposal should be proposal-only", failures)
    check(proposal["active_queue_modified"] is False, "queue proposal should not mutate queue", failures)

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

    validation = chain.validate_control_chain(run_colameta=False)
    check(validation["passed"], f"control chain validation without ColaMeta should pass: {validation['errors']}", failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=14 failures={len(failures)}")
        return 1

    print("PASS commander routing fixtures")
    print("PASS selector no-elevation fixtures")
    print("PASS local executor allowed/forbidden fixtures")
    print("PASS ColaMeta readiness fixture")
    print("PASS queue proposal-only fixture")
    print("PASS reviewed queue mutation fixture")
    print("cases=14 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
