#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Workbench v0.1."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_workbench() -> ModuleType:
    module_path = ROOT / "workbench.py"
    spec = importlib.util.spec_from_file_location("agents_os_workbench", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load workbench module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    workbench = load_workbench()
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="agents-os-workbench-route-stop-", dir=workbench.WORKSPACE_ROOT) as route_stop_dir:
        current_queue_path = Path(route_stop_dir) / "route-stop-queue.md"
        current_queue_path.write_text(workbench.fixture_route_stop_queue_text(), encoding="utf-8")
        current_cycle = workbench.build_cycle(
            "Build AGENTS OS into a local automatic workbench.",
            current_queue_path,
            run_local_validation=True,
        )
    check(current_cycle["passed"] is True, f"current cycle should pass: {current_cycle['errors']}", failures)
    check(
        current_cycle["stages"]["next_step"]["status"] == "route_choice_required",
        "current stopped queue should require route choice",
        failures,
    )
    check(
        current_cycle["stages"]["next_step"]["accepted_route_ids"] == ["A", "B", "C", "D", "E"],
        "current stopped queue should expose route choices A-E",
        failures,
    )
    check(
        current_cycle["stages"]["next_step"]["exact_confirmation_templates_available"] is True,
        "current stopped queue should expose confirmation template availability",
        failures,
    )
    check(
        current_cycle["stages"]["next_step"]["route_auto_selection_authorized"] is False,
        "current stopped queue must not authorize route auto-selection",
        failures,
    )
    check(
        current_cycle["stages"]["local_validation"]["performed"] is False,
        "current stopped queue must not run local validation",
        failures,
    )
    check(current_cycle["active_queue_modified"] is False, "current cycle must not mutate active queue", failures)
    check(current_cycle["execution_authorized"] is False, "current cycle must not authorize execution", failures)
    check(
        current_cycle["stages"]["intake_proposal"]["can_apply_after_review"] is False,
        "current stopped queue intake must not be applicable",
        failures,
    )
    check(
        current_cycle["stages"]["intake_proposal"]["active_queue_modified"] is False,
        "current stopped queue intake must not mutate active queue",
        failures,
    )
    check(
        current_cycle["stages"]["record"]["next_step"]["status"] == "route_choice_required",
        "current cycle record should capture route_choice_required next step",
        failures,
    )
    check(
        current_cycle["stages"]["record"]["next_step"]["accepted_route_ids"] == ["A", "B", "C", "D", "E"],
        "current cycle record should capture route choices A-E",
        failures,
    )
    check(
        current_cycle["stages"]["record"]["write_performed"] is False,
        "current cycle record must not write",
        failures,
    )

    with tempfile.TemporaryDirectory(prefix="agents-os-workbench-test-", dir=workbench.WORKSPACE_ROOT) as temp_dir:
        queue_path = Path(temp_dir) / "queue.md"
        queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        stopped_queue_path = Path(temp_dir) / "stopped-queue.md"
        stopped_queue_path.write_text(workbench.fixture_route_stop_queue_text(), encoding="utf-8")
        advance_record_root = Path(temp_dir) / "advance-records"
        advance_record_root.mkdir()
        empty_status = workbench.build_status(advance_record_root)
        check(empty_status["passed"] is True, f"empty status should pass: {empty_status['errors']}", failures)
        check(
            empty_status["next_step"]["status"] == "no_advance_records",
            "empty status should report no_advance_records",
            failures,
        )
        check(empty_status["goal_session_count"] == 0, "empty status should report no goal sessions", failures)

        safe_cycle = workbench.build_cycle(
            "Write local governance report and run docctl validation.",
            queue_path,
            run_local_validation=True,
        )
        check(safe_cycle["passed"] is True, f"safe cycle should pass: {safe_cycle['errors']}", failures)
        check(
            safe_cycle["stages"]["judgment"]["decision"] == "route_to_local_executor",
            "safe cycle should route to local executor",
            failures,
        )
        check(
            safe_cycle["stages"]["track_preview"]["track_authorized"] is True,
            "safe cycle should authorize local-safe track preview",
            failures,
        )
        check(
            safe_cycle["stages"]["local_validation"]["performed"] is True,
            "safe cycle should run local validation",
            failures,
        )
        check(
            safe_cycle["stages"]["queue_proposal"]["proposal_only"] is True,
            "safe cycle should produce proposal-only queue output",
            failures,
        )
        check(
            safe_cycle["stages"]["queue_proposal"]["active_queue_modified"] is False,
            "safe cycle queue proposal must not mutate queue",
            failures,
        )
        check(
            safe_cycle["stages"]["intake_proposal"]["can_apply_after_review"] is True,
            "safe cycle intake should be applicable after review",
            failures,
        )
        check(
            safe_cycle["stages"]["intake_proposal"]["queue_write_authorized"] is False,
            "safe cycle intake must not authorize queue write",
            failures,
        )
        check(
            safe_cycle["stages"]["next_step"]["status"] == "review_queue_proposal",
            "safe cycle should end at review_queue_proposal",
            failures,
        )
        check(
            safe_cycle["stages"]["record"]["stage_receipts"]["local_validation_performed"] is True,
            "safe cycle record should capture local validation",
            failures,
        )
        check(
            safe_cycle["stages"]["record"]["stage_receipts"]["queue_proposal_present"] is True,
            "safe cycle record should capture queue proposal",
            failures,
        )
        check(
            safe_cycle["stages"]["record"]["effect_summary"]["active_queue_modified"] is False,
            "safe cycle record must keep active queue mutation false",
            failures,
        )
        check(
            safe_cycle["stages"]["record"]["replay_inputs"]["raw_intent_included"] is False,
            "safe cycle record must not include raw intent",
            failures,
        )
        safe_review = workbench.accepted_nobao_review_for_intake(safe_cycle["stages"]["intake_proposal"])
        intake_preview = workbench.reviewed_intake_apply_gate(
            safe_cycle["stages"]["intake_proposal"],
            safe_review,
            queue_path,
            apply=False,
            allowed_queue_root=Path(temp_dir),
        )
        check(intake_preview["passed"] is True, f"safe intake preview should pass: {intake_preview['errors']}", failures)
        check(intake_preview["preview_only"] is True, "safe intake preview should remain preview_only", failures)
        check(
            intake_preview["write_performed"] is False,
            "safe intake preview must not write",
            failures,
        )
        check(
            intake_preview["queue_intake_authorized"] is True,
            "safe intake preview should authorize separate reviewed intake",
            failures,
        )
        check(
            intake_preview["queue_write_authorized"] is False,
            "safe intake preview must not authorize queue write",
            failures,
        )
        before_intake_text = queue_path.read_text(encoding="utf-8")
        intake_apply = workbench.reviewed_intake_apply_gate(
            safe_cycle["stages"]["intake_proposal"],
            safe_review,
            queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(intake_apply["passed"] is True, f"safe intake apply should pass: {intake_apply['errors']}", failures)
        check(intake_apply["write_performed"] is True, "safe intake apply should write fixture queue", failures)
        check(intake_apply["active_queue_modified"] is True, "safe intake apply should mark queue modified", failures)
        check(
            intake_apply["queue_promotion_authorized"] is False,
            "safe intake apply must not authorize queue promotion",
            failures,
        )
        check(intake_apply["execution_authorized"] is False, "safe intake apply must not authorize execution", failures)
        after_intake_text = queue_path.read_text(encoding="utf-8")
        check(before_intake_text != after_intake_text, "safe intake apply should change fixture queue text", failures)
        check(
            f"### {intake_apply['mutation'].get('appended_next_id')}: {safe_cycle['stages']['task']['title']}" in after_intake_text,
            "safe intake apply should append candidate title to NEXT",
            failures,
        )
        advance_queue_path = Path(temp_dir) / "advance-queue.md"
        advance_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        safe_advance = workbench.build_advance(
            "Write local governance report and run docctl validation.",
            advance_queue_path,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        check(safe_advance["passed"] is True, f"safe advance should pass: {safe_advance['errors']}", failures)
        check(
            safe_advance["stages"]["execution"]["local_safe_execution_performed"] is True,
            "safe advance should perform local-safe execution",
            failures,
        )
        check(
            safe_advance["stages"]["verification"]["passed"] is True,
            "safe advance verification should pass",
            failures,
        )
        check(
            safe_advance["record_write_performed"] is True,
            "safe advance should write a record",
            failures,
        )
        check(
            safe_advance["active_queue_modified"] is False,
            "safe advance without apply_intake must not modify queue",
            failures,
        )
        safe_status = workbench.build_status(advance_record_root)
        check(safe_status["passed"] is True, f"safe status should pass: {safe_status['errors']}", failures)
        check(
            safe_status["latest_advance_id"] == safe_advance["advance_id"],
            "safe status should identify safe advance as latest",
            failures,
        )
        check(
            safe_status["next_step"]["status"] == "review_queue_proposal",
            "safe status should surface review_queue_proposal",
            failures,
        )
        check(safe_status["write_performed"] is False, "safe status must be read-only", failures)
        check(safe_status["goal_session_count"] == 0, "safe status before goal should report no goal sessions", failures)
        check(
            Path(temp_dir, "advance-records", Path(safe_advance["stages"]["record"]["record_path"]).name).exists(),
            "safe advance record file should exist",
            failures,
        )
        safe_advance_record_path = Path(temp_dir, "advance-records", Path(safe_advance["stages"]["record"]["record_path"]).name)
        if safe_advance_record_path.exists():
            safe_advance_payload = workbench.load_json(safe_advance_record_path)
            check(
                safe_advance_payload.get("schema_version") == "agents-os.workbench.advance.v0.1",
                "safe advance record file should contain advance record",
                failures,
            )
            check(
                safe_advance_payload.get("advance_id") == safe_advance["advance_id"],
                "safe advance record file should match advance_id",
                failures,
            )
            check(
                safe_advance_payload.get("passed") is True,
                "safe advance record file should include final passed=true",
                failures,
            )
            check(
                safe_advance_payload.get("stages", {}).get("execution", {}).get("local_safe_execution_performed") is True,
                "safe advance record file should capture local-safe execution",
                failures,
            )
        safe_cycle_record_path = Path(temp_dir, "advance-records", Path(safe_advance["stages"]["record"]["cycle_record_path"]).name)
        check(safe_cycle_record_path.exists(), "safe advance cycle record file should exist", failures)
        if safe_cycle_record_path.exists():
            safe_cycle_payload = workbench.load_json(safe_cycle_record_path)
            check(
                safe_cycle_payload.get("schema_version") == "agents-os.workbench.record-preview.v0.1",
                "safe advance cycle record file should contain cycle record preview",
                failures,
            )

        advance_apply_queue_path = Path(temp_dir) / "advance-apply-queue.md"
        advance_apply_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        advance_with_intake = workbench.build_advance(
            "Write local governance report and run docctl validation.",
            advance_apply_queue_path,
            record_root=advance_record_root,
            apply_intake=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            advance_with_intake["passed"] is True,
            f"advance with intake should pass: {advance_with_intake['errors']}",
            failures,
        )
        check(
            advance_with_intake["stages"]["intake_apply"]["write_performed"] is True,
            "advance with intake should write fixture NEXT",
            failures,
        )
        check(
            advance_with_intake["queue_promotion_authorized"] is False,
            "advance with intake must not authorize queue promotion",
            failures,
        )
        check(
            advance_with_intake["execution_authorized"] is False,
            "advance with intake must not authorize dangerous execution",
            failures,
        )
        advance_with_intake_record_path = Path(
            temp_dir,
            "advance-records",
            Path(advance_with_intake["stages"]["record"]["record_path"]).name,
        )
        if advance_with_intake_record_path.exists():
            advance_with_intake_payload = workbench.load_json(advance_with_intake_record_path)
            check(
                advance_with_intake_payload.get("stages", {}).get("intake_apply", {}).get("write_performed") is True,
                "advance with intake record should capture intake write",
                failures,
            )
        else:
            failures.append("advance with intake record file should exist")
        status_after_intake = workbench.build_status(advance_record_root)
        check(
            status_after_intake["latest_advance_id"] == advance_with_intake["advance_id"],
            "status after intake should identify latest advance with intake",
            failures,
        )
        check(
            status_after_intake["latest_effects"]["active_queue_modified"] is True,
            "status after intake should surface fixture queue write",
            failures,
        )
        check(
            status_after_intake["latest_effects"]["queue_promotion_authorized"] is False,
            "status after intake must keep queue promotion false",
            failures,
        )
        cli_status = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "status",
                "--record-root",
                str(advance_record_root),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_status.returncode == 0, f"CLI status should pass: {cli_status.stderr}", failures)
        if cli_status.stdout:
            cli_status_payload = json.loads(cli_status.stdout)
            check(
                cli_status_payload.get("schema_version") == "agents-os.workbench.status.v0.1",
                "CLI status should emit status schema",
                failures,
            )
            check(
                cli_status_payload.get("latest_advance_id") == advance_with_intake["advance_id"],
                "CLI status should report latest advance with intake",
                failures,
            )
            check(
                cli_status_payload.get("goal_session_count") == 0,
                "CLI status before goal should report no goal sessions",
                failures,
            )
        else:
            failures.append("CLI status should emit JSON")

        provider_cycle = workbench.build_cycle(
            "Call provider and start service.",
            queue_path,
            run_local_validation=True,
        )
        check(provider_cycle["passed"] is True, f"provider cycle should pass as stopped output: {provider_cycle['errors']}", failures)
        check(
            provider_cycle["stages"]["judgment"]["decision"] == "stop_needs_jenn_decision",
            "provider cycle should stop for Jenn decision",
            failures,
        )
        check(
            provider_cycle["stages"]["local_validation"]["performed"] is False,
            "provider cycle must not run local validation",
            failures,
        )
        check(
            provider_cycle["stages"]["next_step"]["status"] == "jenn_decision_required",
            "provider cycle next step should require Jenn",
            failures,
        )
        check(
            provider_cycle["stages"]["intake_proposal"]["candidate_requires_jenn_decision"] is True,
            "provider cycle intake should require Jenn decision",
            failures,
        )
        check(
            provider_cycle["stages"]["intake_proposal"]["can_apply_after_review"] is False,
            "provider cycle intake must not be applicable",
            failures,
        )
        check(
            provider_cycle["stages"]["record"]["stage_receipts"]["local_validation_performed"] is False,
            "provider cycle record should show local validation was not run",
            failures,
        )
        check(
            provider_cycle["stages"]["record"]["effect_summary"]["provider_call_authorized"] is False,
            "provider cycle record must not authorize provider call",
            failures,
        )
        provider_review = workbench.accepted_nobao_review_for_intake(provider_cycle["stages"]["intake_proposal"])
        blocked_provider_intake = workbench.reviewed_intake_apply_gate(
            provider_cycle["stages"]["intake_proposal"],
            provider_review,
            queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(blocked_provider_intake["passed"] is False, "provider intake apply should fail", failures)
        check(
            blocked_provider_intake["write_performed"] is False,
            "provider intake apply must not write",
            failures,
        )
        provider_advance = workbench.build_advance(
            "Call provider and start service.",
            queue_path,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        check(provider_advance["passed"] is True, f"provider advance should pass as stopped output: {provider_advance['errors']}", failures)
        check(
            provider_advance["stages"]["execution"]["local_safe_execution_performed"] is False,
            "provider advance must not perform local-safe execution",
            failures,
        )
        check(
            provider_advance["stages"]["next_step"]["status"] == "jenn_decision_required",
            "provider advance should require Jenn decision",
            failures,
        )
        stopped_run = workbench.build_run(
            "Build AGENTS OS into a local automatic workbench.",
            stopped_queue_path,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        check(stopped_run["passed"] is True, f"stopped run should pass: {stopped_run['errors']}", failures)
        check(stopped_run["next_step"]["status"] == "route_choice_required", "stopped run should stop at route_choice_required", failures)
        check(stopped_run["local_safe_execution_count"] == 0, "stopped run must not execute local-safe command", failures)
        check(stopped_run["record_write_count"] == 1, "stopped run should write one record", failures)
        stopped_goal = workbench.build_goal_session(
            "Build AGENTS OS into a local automatic workbench.",
            stopped_queue_path,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        check(stopped_goal["passed"] is True, f"stopped goal should pass: {stopped_goal['errors']}", failures)
        check(
            stopped_goal["schema_version"] == "agents-os.workbench.goal-session.v0.1",
            "stopped goal should emit goal session schema",
            failures,
        )
        check(stopped_goal["goal_state"] == "waiting_at_boundary", "stopped goal should wait at boundary", failures)
        check(stopped_goal["next_step"]["status"] == "route_choice_required", "stopped goal should stop at route choice", failures)
        check(stopped_goal["record"]["write_performed"] is True, "stopped goal should write session record", failures)
        check(stopped_goal["source"]["objective_raw_output"] is False, "stopped goal must not output raw objective", failures)
        check(
            stopped_goal["route_choice_readiness"]["accepted_route_ids"] == ["A", "B", "C", "D", "E"],
            "stopped goal should surface route choices A-E",
            failures,
        )
        check(
            stopped_goal["route_choice_readiness"]["option_count"] == 5,
            "stopped goal should surface five route options",
            failures,
        )
        check(
            stopped_goal["route_choice_readiness"]["raw_template_output"] is False,
            "stopped goal must not output raw route templates",
            failures,
        )
        stopped_goal_status = workbench.build_status(advance_record_root)
        check(stopped_goal_status["passed"] is True, f"stopped goal status should pass: {stopped_goal_status['errors']}", failures)
        check(
            stopped_goal_status["route_choice_readiness"]["option_count"] == 5,
            "stopped goal status should surface five route options",
            failures,
        )
        check(
            stopped_goal_status["latest_goal_session"]["route_choice_readiness"]["option_count"] == 5,
            "stopped goal status should recover goal route choice readiness",
            failures,
        )

        run_queue_path = Path(temp_dir) / "run-queue.md"
        run_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        safe_run = workbench.build_run(
            "Write local governance report and run docctl validation.",
            run_queue_path,
            validation_command="python3 --version",
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        check(safe_run["passed"] is True, f"safe run should pass: {safe_run['errors']}", failures)
        check(safe_run["local_safe_execution_count"] == 1, "safe run should execute once", failures)
        check(safe_run["next_step"]["status"] == "review_queue_proposal", "safe run should stop at review_queue_proposal", failures)
        check(safe_run["active_queue_modified"] is False, "safe run must not modify queue without apply_intake", failures)
        goal_queue_path = Path(temp_dir) / "goal-queue.md"
        goal_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        safe_goal = workbench.build_goal_session(
            "Write local governance report and run docctl validation.",
            goal_queue_path,
            validation_command="python3 --version",
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        check(safe_goal["passed"] is True, f"safe goal should pass: {safe_goal['errors']}", failures)
        check(safe_goal["run_summary"]["local_safe_execution_count"] == 1, "safe goal should execute once", failures)
        check(safe_goal["next_step"]["status"] == "review_queue_proposal", "safe goal should stop at review queue proposal", failures)
        check(safe_goal["record"]["write_performed"] is True, "safe goal should write session record", failures)
        check(
            safe_goal["route_choice_readiness"]["present"] is False,
            "safe goal should not surface route choice readiness",
            failures,
        )
        goal_status = workbench.build_status(advance_record_root)
        check(goal_status["passed"] is True, f"goal status should pass: {goal_status['errors']}", failures)
        check(goal_status["goal_session_count"] == 2, "goal status should count stopped and safe goal sessions", failures)
        check(
            goal_status["latest_goal_session"]["goal_session_id"] == safe_goal["goal_session_id"],
            "goal status should surface latest goal session id",
            failures,
        )
        check(
            goal_status["latest_goal_session"]["goal_state"] == "waiting_at_boundary",
            "goal status should surface latest goal state",
            failures,
        )
        check(
            goal_status["latest_goal_session"]["next_step"]["status"] == "review_queue_proposal",
            "goal status should surface latest goal next step",
            failures,
        )
        check(
            goal_status["latest_goal_session"]["objective_raw_output"] is False,
            "goal status must not expose raw objective",
            failures,
        )
        check(
            goal_status["route_choice_readiness"]["present"] is False,
            "goal status for safe latest advance should not surface route choice readiness",
            failures,
        )
        route_choice_text = (
            "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
            "先准备 formal Memory candidate gate v0.1；只做候选和确认模型，不写正式 Memory，\n"
            "不读 private raw Memory，不读 state-private/，并保留 receipt/review/validation。"
        )
        route_choice_queue_path = Path(temp_dir) / "route-choice-queue.md"
        route_choice_queue_path.write_text(workbench.fixture_route_stop_queue_text(), encoding="utf-8")
        route_choice_preview = workbench.build_route_choice_preview(route_choice_text, route_choice_queue_path)
        check(
            route_choice_preview["passed"] is True,
            f"route choice preview should pass: {route_choice_preview['errors']}",
            failures,
        )
        check(
            route_choice_preview["bundle"]["selected_route_id"] == "B",
            "route choice preview should select route B",
            failures,
        )
        check(
            route_choice_preview["bundle"]["can_apply_with_separate_apply_gate"] is True,
            "route choice preview should reach separate apply gate readiness",
            failures,
        )
        check(
            route_choice_preview["confirmation_text_included"] is False,
            "route choice preview must not include confirmation text",
            failures,
        )
        check(route_choice_preview["active_queue_modified"] is False, "route choice preview must not modify queue", failures)
        check(route_choice_preview["execution_authorized"] is False, "route choice preview must not authorize execution", failures)
        route_apply_queue_path = Path(temp_dir) / "route-apply-queue.md"
        route_apply_queue_path.write_text(workbench.fixture_route_stop_queue_text(), encoding="utf-8")
        route_apply_preview = workbench.build_route_choice_apply_gate(
            route_choice_text,
            route_apply_queue_path,
            apply=False,
            allowed_queue_root=Path(temp_dir),
        )
        check(route_apply_preview["passed"] is True, f"route apply preview should pass: {route_apply_preview['errors']}", failures)
        check(route_apply_preview["write_performed"] is False, "route apply preview must not write", failures)
        check(route_apply_preview["queue_write_authorized"] is False, "route apply preview must not authorize queue write", failures)
        before_route_apply = route_apply_queue_path.read_text(encoding="utf-8")
        route_apply = workbench.build_route_choice_apply_gate(
            route_choice_text,
            route_apply_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(route_apply["passed"] is True, f"route apply should pass: {route_apply['errors']}", failures)
        check(route_apply["write_performed"] is True, "route apply should write fixture queue", failures)
        check(route_apply["active_queue_modified"] is True, "route apply should mark fixture queue modified", failures)
        check(route_apply["queue_promotion_authorized"] is False, "route apply must not authorize queue promotion", failures)
        check(route_apply["execution_authorized"] is False, "route apply must not authorize execution", failures)
        after_route_apply = route_apply_queue_path.read_text(encoding="utf-8")
        check(before_route_apply != after_route_apply, "route apply should change fixture queue text", failures)
        check(
            "AGENTS OS formal Memory candidate gate v0.1" in after_route_apply,
            "route apply should append formal Memory first safe package",
            failures,
        )
        route_promotion_preview = workbench.build_queue_promotion_apply_gate(
            route_apply_queue_path,
            apply=False,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            route_promotion_preview["passed"] is True,
            f"route promotion preview should pass: {route_promotion_preview['errors']}",
            failures,
        )
        check(route_promotion_preview["write_performed"] is False, "route promotion preview must not write", failures)
        route_promotion_apply = workbench.build_queue_promotion_apply_gate(
            route_apply_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            route_promotion_apply["passed"] is True,
            f"route promotion apply should pass: {route_promotion_apply['errors']}",
            failures,
        )
        check(route_promotion_apply["write_performed"] is True, "route promotion apply should write fixture queue", failures)
        check(
            route_promotion_apply["queue_promotion_authorized"] is True,
            "route promotion apply should authorize reviewed queue promotion",
            failures,
        )
        check(route_promotion_apply["execution_authorized"] is False, "route promotion apply must not authorize execution", failures)
        check(
            "### NOW-001: AGENTS OS formal Memory candidate gate v0.1" in route_apply_queue_path.read_text(encoding="utf-8"),
            "route promotion apply should move route package into NOW",
            failures,
        )
        route_promotion_status = workbench.build_status(advance_record_root, route_apply_queue_path)
        route_continue_record_root = Path(temp_dir) / "route-continue-records"
        route_continue_record_root.mkdir()
        check(
            route_promotion_status["passed"] is True,
            f"route promotion status should pass: {route_promotion_status['errors']}",
            failures,
        )
        check(
            route_promotion_status["live_queue"]["next_step"]["status"] == "queue_ready_for_run",
            "route promotion status should report live queue ready for run",
            failures,
        )
        check(
            route_promotion_status["status_reconciliation"]["record_boundary_may_be_stale"] is True,
            "route promotion status should detect stale record boundary",
            failures,
        )
        route_promotion_continue = workbench.build_continue_current(
            route_apply_queue_path,
            validation_command="python3 --version",
            record_root=route_continue_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            route_promotion_continue["passed"] is True,
            f"route promotion continue should pass: {route_promotion_continue['errors']}",
            failures,
        )
        check(
            route_promotion_continue["run_summary"]["local_safe_execution_count"] == 1,
            "route promotion continue should execute current NOW once",
            failures,
        )
        check(
            route_promotion_continue["run_summary"]["record_write_count"] == 1,
            "route promotion continue should write one record",
            failures,
        )
        check(
            route_promotion_continue["source"]["derived_intent_raw_output"] is False,
            "route promotion continue must not output derived raw intent",
            failures,
        )
        check(
            route_promotion_continue["next_step"]["status"] == "review_queue_proposal",
            "route promotion continue should stop at review_queue_proposal",
            failures,
        )
        continue_completion_queue_path = Path(temp_dir) / "continue-completion-queue.md"
        continue_completion_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        continue_completion_record_root = Path(temp_dir) / "continue-completion-records"
        continue_completion_record_root.mkdir()
        continue_with_completion = workbench.build_continue_current(
            continue_completion_queue_path,
            validation_command="python3 --version",
            record_root=continue_completion_record_root,
            apply_completion_promotion=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            continue_with_completion["passed"] is True,
            f"continue with completion promotion should pass: {continue_with_completion['errors']}",
            failures,
        )
        check(
            continue_with_completion["run_summary"]["local_safe_execution_count"] == 1,
            "continue with completion promotion should execute current NOW once",
            failures,
        )
        check(
            continue_with_completion["completion_promotion"]["write_performed"] is True,
            "continue with completion promotion should write reviewed queue promotion",
            failures,
        )
        check(
            continue_with_completion["queue_promotion_authorized"] is True,
            "continue with completion promotion should authorize reviewed queue promotion",
            failures,
        )
        check(
            continue_with_completion["execution_authorized"] is False,
            "continue with completion promotion must not authorize execution",
            failures,
        )
        check(
            "### NOW-001: Safe follow-up task" in continue_completion_queue_path.read_text(encoding="utf-8"),
            "continue with completion promotion should promote safe follow-up to NOW",
            failures,
        )
        check(
            continue_with_completion["next_step"]["status"] == "completion_promotion_applied_continue_ready",
            "continue with completion promotion should report continue-ready next step",
            failures,
        )
        continue_loop_queue_path = Path(temp_dir) / "continue-loop-queue.md"
        continue_loop_queue_path.write_text(workbench.fixture_loop_queue_text(), encoding="utf-8")
        continue_loop_record_root = Path(temp_dir) / "continue-loop-records"
        continue_loop_record_root.mkdir()
        continue_loop = workbench.build_continue_loop(
            continue_loop_queue_path,
            validation_command="python3 --version",
            record_root=continue_loop_record_root,
            max_cycles=2,
            apply_completion_promotion=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(continue_loop["passed"] is True, f"continue loop should pass: {continue_loop['errors']}", failures)
        check(continue_loop["cycles_performed"] == 2, "continue loop should perform two cycles", failures)
        check(continue_loop["local_safe_execution_count"] == 2, "continue loop should execute two validations", failures)
        check(continue_loop["record_write_count"] == 2, "continue loop should write two records", failures)
        check(continue_loop["completion_promotion_count"] == 2, "continue loop should apply two promotions", failures)
        check(continue_loop["stopped_reason"] == "max_cycles_reached", "continue loop should stop at max cycles", failures)
        check(continue_loop["execution_authorized"] is False, "continue loop must not authorize execution", failures)
        check(
            "### NOW-001: Second safe follow-up task" in continue_loop_queue_path.read_text(encoding="utf-8"),
            "continue loop should promote second safe follow-up to NOW",
            failures,
        )

        run_apply_queue_path = Path(temp_dir) / "run-apply-queue.md"
        run_apply_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        run_with_intake = workbench.build_run(
            "Write local governance report and run docctl validation.",
            run_apply_queue_path,
            record_root=advance_record_root,
            apply_intake=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(run_with_intake["passed"] is True, f"run with intake should pass: {run_with_intake['errors']}", failures)
        check(run_with_intake["active_queue_modified"] is True, "run with intake should modify fixture queue", failures)
        check(run_with_intake["queue_promotion_authorized"] is False, "run with intake must not authorize queue promotion", failures)
        check(run_with_intake["local_safe_execution_count"] == 1, "run with intake should execute once", failures)

        cli_run_record_root = Path(temp_dir) / "cli-run-records"
        cli_run_record_root.mkdir()
        cli_run_queue_path = Path(temp_dir) / "cli-run-queue.md"
        cli_run_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        cli_run = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "run",
                "--intent",
                "Write local governance report and run docctl validation.",
                "--queue",
                str(cli_run_queue_path),
                "--record-root",
                str(cli_run_record_root),
                "--allowed-queue-root",
                str(Path(temp_dir)),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_run.returncode == 0, f"CLI run should pass: {cli_run.stderr}", failures)
        if cli_run.stdout:
            cli_run_payload = json.loads(cli_run.stdout)
            check(
                cli_run_payload.get("schema_version") == "agents-os.workbench.run.v0.1",
                "CLI run should emit run schema",
                failures,
            )
            check(cli_run_payload.get("local_safe_execution_count") == 1, "CLI run should execute once", failures)
        else:
            failures.append("CLI run should emit JSON")
        cli_goal_record_root = Path(temp_dir) / "cli-goal-records"
        cli_goal_record_root.mkdir()
        cli_goal_queue_path = Path(temp_dir) / "cli-goal-queue.md"
        cli_goal_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        cli_goal = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "goal",
                "--objective",
                "Write local governance report and run docctl validation.",
                "--queue",
                str(cli_goal_queue_path),
                "--validation-command",
                "python3 --version",
                "--record-root",
                str(cli_goal_record_root),
                "--allowed-queue-root",
                str(Path(temp_dir)),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_goal.returncode == 0, f"CLI goal should pass: {cli_goal.stderr}", failures)
        if cli_goal.stdout:
            cli_goal_payload = json.loads(cli_goal.stdout)
            check(
                cli_goal_payload.get("schema_version") == "agents-os.workbench.goal-session.v0.1",
                "CLI goal should emit goal session schema",
                failures,
            )
            check(
                cli_goal_payload.get("run_summary", {}).get("local_safe_execution_count") == 1,
                "CLI goal should execute once",
                failures,
            )
            check(
                cli_goal_payload.get("record", {}).get("write_performed") is True,
                "CLI goal should write session record",
                failures,
            )
        else:
            failures.append("CLI goal should emit JSON")
        cli_route_choice_queue_path = Path(temp_dir) / "cli-route-choice-queue.md"
        cli_route_choice_queue_path.write_text(workbench.fixture_route_stop_queue_text(), encoding="utf-8")
        cli_route_choice = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "route-choice-preview",
                "--confirmation-text",
                route_choice_text,
                "--queue",
                str(cli_route_choice_queue_path),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_route_choice.returncode == 0, f"CLI route choice preview should pass: {cli_route_choice.stderr}", failures)
        if cli_route_choice.stdout:
            cli_route_payload = json.loads(cli_route_choice.stdout)
            check(
                cli_route_payload.get("schema_version") == "agents-os.workbench.route-choice-preview.v0.1",
                "CLI route choice preview should emit workbench route schema",
                failures,
            )
            check(
                cli_route_payload.get("bundle", {}).get("selected_route_id") == "B",
                "CLI route choice preview should select B",
                failures,
            )
            check(
                cli_route_payload.get("active_queue_modified") is False,
                "CLI route choice preview must not modify queue",
                failures,
            )
        else:
            failures.append("CLI route choice preview should emit JSON")
        cli_route_apply_queue_path = Path(temp_dir) / "cli-route-apply-queue.md"
        cli_route_apply_queue_path.write_text(workbench.fixture_route_stop_queue_text(), encoding="utf-8")
        cli_route_apply = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "route-choice-apply-gate",
                "--confirmation-text",
                route_choice_text,
                "--queue",
                str(cli_route_apply_queue_path),
                "--allowed-queue-root",
                str(Path(temp_dir)),
                "--apply",
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_route_apply.returncode == 0, f"CLI route apply should pass: {cli_route_apply.stderr}", failures)
        if cli_route_apply.stdout:
            cli_route_apply_payload = json.loads(cli_route_apply.stdout)
            check(
                cli_route_apply_payload.get("schema_version") == "agents-os.workbench.route-choice-apply-gate.v0.1",
                "CLI route apply should emit workbench apply schema",
                failures,
            )
            check(
                cli_route_apply_payload.get("write_performed") is True,
                "CLI route apply should write fixture queue",
                failures,
            )
            check(
                cli_route_apply_payload.get("queue_promotion_authorized") is False,
                "CLI route apply must not authorize queue promotion",
                failures,
            )
        else:
            failures.append("CLI route apply should emit JSON")
        cli_queue_promotion = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "queue-promotion-apply-gate",
                "--queue",
                str(cli_route_apply_queue_path),
                "--allowed-queue-root",
                str(Path(temp_dir)),
                "--apply",
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_queue_promotion.returncode == 0, f"CLI queue promotion should pass: {cli_queue_promotion.stderr}", failures)
        if cli_queue_promotion.stdout:
            cli_queue_promotion_payload = json.loads(cli_queue_promotion.stdout)
            check(
                cli_queue_promotion_payload.get("schema_version") == "agents-os.workbench.queue-promotion-apply-gate.v0.1",
                "CLI queue promotion should emit workbench promotion schema",
                failures,
            )
            check(
                cli_queue_promotion_payload.get("write_performed") is True,
                "CLI queue promotion should write fixture queue",
                failures,
            )
            check(
                cli_queue_promotion_payload.get("execution_authorized") is False,
                "CLI queue promotion must not authorize execution",
                failures,
            )
        else:
            failures.append("CLI queue promotion should emit JSON")
        cli_live_status = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "status",
                "--record-root",
                str(cli_goal_record_root),
                "--queue",
                str(cli_route_apply_queue_path),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_live_status.returncode == 0, f"CLI live status should pass: {cli_live_status.stderr}", failures)
        if cli_live_status.stdout:
            cli_live_status_payload = json.loads(cli_live_status.stdout)
            check(
                cli_live_status_payload.get("live_queue", {}).get("next_step", {}).get("status") == "queue_ready_for_run",
                "CLI live status should report promoted queue ready for run",
                failures,
            )
            check(
                cli_live_status_payload.get("status_reconciliation", {}).get("record_boundary_may_be_stale") is True,
                "CLI live status should detect stale record boundary",
                failures,
            )
        else:
            failures.append("CLI live status should emit JSON")
        cli_continue_record_root = Path(temp_dir) / "cli-continue-records"
        cli_continue_record_root.mkdir()
        cli_continue = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "continue",
                "--queue",
                str(cli_route_apply_queue_path),
                "--validation-command",
                "python3 --version",
                "--record-root",
                str(cli_continue_record_root),
                "--allowed-queue-root",
                str(Path(temp_dir)),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_continue.returncode == 0, f"CLI continue should pass: {cli_continue.stderr}", failures)
        if cli_continue.stdout:
            cli_continue_payload = json.loads(cli_continue.stdout)
            check(
                cli_continue_payload.get("schema_version") == "agents-os.workbench.continue-current.v0.1",
                "CLI continue should emit continue schema",
                failures,
            )
            check(
                cli_continue_payload.get("run_summary", {}).get("local_safe_execution_count") == 1,
                "CLI continue should execute current NOW once",
                failures,
            )
            check(
                cli_continue_payload.get("source", {}).get("derived_intent_raw_output") is False,
                "CLI continue must not output derived raw intent",
                failures,
            )
        else:
            failures.append("CLI continue should emit JSON")
        cli_completion_queue_path = Path(temp_dir) / "cli-completion-queue.md"
        cli_completion_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        cli_completion_record_root = Path(temp_dir) / "cli-completion-records"
        cli_completion_record_root.mkdir()
        cli_continue_completion = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "continue",
                "--queue",
                str(cli_completion_queue_path),
                "--validation-command",
                "python3 --version",
                "--record-root",
                str(cli_completion_record_root),
                "--allowed-queue-root",
                str(Path(temp_dir)),
                "--apply-completion-promotion",
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(
            cli_continue_completion.returncode == 0,
            f"CLI continue completion promotion should pass: {cli_continue_completion.stderr}",
            failures,
        )
        if cli_continue_completion.stdout:
            cli_continue_completion_payload = json.loads(cli_continue_completion.stdout)
            check(
                cli_continue_completion_payload.get("completion_promotion", {}).get("write_performed") is True,
                "CLI continue completion promotion should write reviewed queue promotion",
                failures,
            )
            check(
                cli_continue_completion_payload.get("next_step", {}).get("status") == "completion_promotion_applied_continue_ready",
                "CLI continue completion promotion should report continue-ready next step",
                failures,
            )
            check(
                cli_continue_completion_payload.get("execution_authorized") is False,
                "CLI continue completion promotion must not authorize execution",
                failures,
            )
        else:
            failures.append("CLI continue completion promotion should emit JSON")
        cli_loop_queue_path = Path(temp_dir) / "cli-loop-queue.md"
        cli_loop_queue_path.write_text(workbench.fixture_loop_queue_text(), encoding="utf-8")
        cli_loop_record_root = Path(temp_dir) / "cli-loop-records"
        cli_loop_record_root.mkdir()
        cli_loop = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "loop",
                "--queue",
                str(cli_loop_queue_path),
                "--validation-command",
                "python3 --version",
                "--record-root",
                str(cli_loop_record_root),
                "--allowed-queue-root",
                str(Path(temp_dir)),
                "--max-cycles",
                "2",
                "--apply-completion-promotion",
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_loop.returncode == 0, f"CLI loop should pass: {cli_loop.stderr}", failures)
        if cli_loop.stdout:
            cli_loop_payload = json.loads(cli_loop.stdout)
            check(
                cli_loop_payload.get("schema_version") == "agents-os.workbench.continue-loop.v0.1",
                "CLI loop should emit continue loop schema",
                failures,
            )
            check(cli_loop_payload.get("cycles_performed") == 2, "CLI loop should perform two cycles", failures)
            check(
                cli_loop_payload.get("completion_promotion_count") == 2,
                "CLI loop should apply two completion promotions",
                failures,
            )
            check(
                cli_loop_payload.get("execution_authorized") is False,
                "CLI loop must not authorize execution",
                failures,
            )
        else:
            failures.append("CLI loop should emit JSON")

        p3_queue_path = Path(temp_dir) / "p3-queue.md"
        p3_queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
        p3_cycle = workbench.build_cycle(
            "Write local governance report and run docctl validation.",
            p3_queue_path,
            run_local_validation=True,
        )
        p3_proposal = dict(p3_cycle["stages"]["intake_proposal"])
        p3_proposal["proposed_queue_item"] = dict(p3_proposal["proposed_queue_item"])
        p3_proposal["proposed_queue_item"]["title"] = "Publish report to GitHub release"
        p3_review = workbench.accepted_nobao_review_for_intake(p3_proposal)
        blocked_p3_intake = workbench.reviewed_intake_apply_gate(
            p3_proposal,
            p3_review,
            p3_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(blocked_p3_intake["passed"] is False, "P3 intake apply should fail", failures)
        check(blocked_p3_intake["write_performed"] is False, "P3 intake apply must not write", failures)

        record_path = Path(temp_dir) / "records" / "safe-cycle-record.json"
        record_path.parent.mkdir()
        recorded_cycle = workbench.build_cycle(
            "Write local governance report and run docctl validation.",
            queue_path,
            run_local_validation=True,
            write_record=True,
            record_path=record_path,
            allowed_record_root=record_path.parent,
        )
        check(recorded_cycle["passed"] is True, f"recorded cycle should pass: {recorded_cycle['errors']}", failures)
        check(recorded_cycle["record_write_performed"] is True, "recorded cycle should mark record_write_performed", failures)
        check(
            recorded_cycle["stages"]["record_write"]["write_performed"] is True,
            "recorded cycle should write record file",
            failures,
        )
        check(record_path.exists(), "record file should exist under allowed root", failures)
        if record_path.exists():
            recorded_payload = workbench.load_json(record_path)
            check(
                recorded_payload.get("record_id") == recorded_cycle["stages"]["record"]["record_id"],
                "record file should contain the record preview",
                failures,
            )

        blocked_record_cycle = workbench.build_cycle(
            "Write local governance report and run docctl validation.",
            queue_path,
            run_local_validation=True,
            write_record=True,
            record_path=Path(temp_dir) / "outside-record.json",
            allowed_record_root=record_path.parent,
        )
        check(blocked_record_cycle["passed"] is False, "blocked record cycle should fail", failures)
        check(
            blocked_record_cycle["stages"]["record_write"]["write_performed"] is False,
            "blocked record cycle must not write outside allowed root",
            failures,
        )

    validation = workbench.validate_workbench()
    check(validation["passed"] is True, f"workbench validation should pass: {validation['errors']}", failures)
    check(validation["temporary_fixture_cleaned"] is True, "workbench validation should clean temporary fixture", failures)
    check(
        validation["safe_advance"]["record_write_performed"] is True,
        "workbench validation should cover safe advance record write",
        failures,
    )
    check(
        validation["safe_advance"]["local_safe_execution_performed"] is True,
        "workbench validation should cover safe advance execution",
        failures,
    )
    audit = workbench.build_completion_audit()
    check(audit["passed"] is True, f"workbench audit should pass: {audit['errors']}", failures)
    check(audit["failed_requirement_ids"] == [], "workbench audit should have no failed requirements", failures)
    check(
        audit["real_queue_boundary"]["handled"] is True,
        "workbench audit should treat the real queue boundary as handled",
        failures,
    )
    check(
        audit["real_queue_boundary"]["execution_authorized"] is False,
        "workbench audit must not authorize execution at the real queue boundary",
        failures,
    )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=18 failures={len(failures)}")
        return 1

    print("PASS current stopped queue cycle")
    print("PASS local-safe workbench cycle")
    print("PASS provider stop cycle")
    print("PASS workbench record preview fixtures")
    print("PASS workbench record write gate fixtures")
    print("PASS workbench intake proposal fixtures")
    print("PASS workbench reviewed intake apply gate fixtures")
    print("PASS workbench advance fixtures")
    print("PASS workbench status fixtures")
    print("PASS workbench run fixtures")
    print("PASS workbench goal fixtures")
    print("PASS workbench route choice preview fixtures")
    print("PASS workbench route choice apply gate fixtures")
    print("PASS workbench queue promotion apply gate fixtures")
    print("PASS workbench continue current fixtures")
    print("PASS workbench continue loop fixtures")
    print("PASS workbench validation")
    print("PASS workbench completion audit")
    print("cases=18 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
