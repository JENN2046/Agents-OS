#!/usr/bin/env python3
"""Fixture tests for AGENTS OS Workbench v0.1."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
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


def fixture_queue_with_now_lines(workbench: ModuleType, title: str, *lines: str) -> str:
    return workbench.fixture_queue_text(title).replace(
        "Run local validation and prepare proposal-only queue output.",
        "\n".join(["Run local validation and prepare proposal-only queue output.", *lines]),
    )


def fixture_governance_gate_queue_text() -> str:
    return """# workbench governance gate fixture

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


def fixture_generic_p3_governance_gate_queue_text() -> str:
    return """# workbench generic P3 governance gate fixture

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


def main() -> int:
    parser = argparse.ArgumentParser(description="Fixture tests for AGENTS OS Workbench v0.1.")
    parser.add_argument("--full", action="store_true", help="Run full validation and completion audit checks.")
    args = parser.parse_args()

    workbench = load_workbench()
    failures: list[str] = []

    if not args.full:
        with tempfile.TemporaryDirectory(prefix="agents-os-workbench-fast-test-", dir=workbench.WORKSPACE_ROOT) as temp_dir:
            record_root = Path(temp_dir) / "records"
            record_root.mkdir()
            route_queue_path = Path(temp_dir) / "route-stop-queue.md"
            route_queue_path.write_text(workbench.fixture_route_stop_queue_text(), encoding="utf-8")
            current_cycle = workbench.build_cycle(
                "Build AGENTS OS into a local automatic workbench.",
                route_queue_path,
                run_local_validation=True,
                validation_command="python3 --version",
            )
            check(current_cycle["passed"] is True, f"current cycle should pass: {current_cycle['errors']}", failures)
            check(
                current_cycle["stages"]["next_step"]["status"] == "route_choice_required",
                "current stopped queue should require route choice",
                failures,
            )
            check(
                current_cycle["stages"]["local_validation"]["performed"] is False,
                "route-stopped cycle should not run local validation",
                failures,
            )
            check(current_cycle["execution_authorized"] is False, "route-stopped cycle must not authorize execution", failures)

            queue_path = Path(temp_dir) / "queue.md"
            queue_path.write_text(workbench.fixture_queue_text(), encoding="utf-8")
            safe_cycle = workbench.build_cycle(
                "Write local governance report and run fast validation.",
                queue_path,
                run_local_validation=True,
                validation_command="python3 --version",
            )
            check(safe_cycle["passed"] is True, f"safe cycle should pass: {safe_cycle['errors']}", failures)
            check(
                safe_cycle["stages"]["judgment"]["decision"] == "route_to_local_executor",
                "safe cycle should route to local executor",
                failures,
            )
            check(
                safe_cycle["stages"]["local_validation"]["performed"] is True,
                "safe cycle should run lightweight local validation",
                failures,
            )
            check(
                safe_cycle["stages"]["intake_proposal"]["can_apply_after_review"] is True,
                "safe cycle should produce reviewable intake",
                failures,
            )
            check(
                safe_cycle["stages"]["queue_proposal"]["active_queue_modified"] is False,
                "safe cycle must not mutate queue during preview",
                failures,
            )

            provider_cycle = workbench.build_cycle(
                "Call provider and start service.",
                queue_path,
                run_local_validation=True,
                validation_command="python3 --version",
            )
            check(provider_cycle["passed"] is True, f"provider cycle should pass as stopped output: {provider_cycle['errors']}", failures)
            check(
                provider_cycle["stages"]["judgment"]["decision"] == "stop_needs_jenn_decision",
                "provider cycle should stop for Jenn decision",
                failures,
            )
            check(
                provider_cycle["stages"]["local_validation"]["performed"] is False,
                "provider cycle should not run local validation",
                failures,
            )
            check(
                provider_cycle["stages"]["record"]["effect_summary"]["provider_call_authorized"] is False,
                "provider cycle must not authorize provider call",
                failures,
            )

            record_path = record_root / "cycle-record.json"
            recorded_cycle = workbench.build_cycle(
                "Write local governance report and run fast validation.",
                queue_path,
                run_local_validation=True,
                validation_command="python3 --version",
                write_record=True,
                record_path=record_path,
                allowed_record_root=record_root,
            )
            check(recorded_cycle["passed"] is True, f"recorded cycle should pass: {recorded_cycle['errors']}", failures)
            check(recorded_cycle["record_write_performed"] is True, "recorded cycle should write inside allowed root", failures)
            check(record_path.exists(), "record file should exist under allowed root", failures)
            blocked_record_cycle = workbench.build_cycle(
                "Write local governance report and run fast validation.",
                queue_path,
                run_local_validation=True,
                validation_command="python3 --version",
                write_record=True,
                record_path=Path(temp_dir) / "outside-record.json",
                allowed_record_root=record_root,
            )
            check(blocked_record_cycle["passed"] is False, "blocked record cycle should fail outside record root", failures)
            check(
                blocked_record_cycle["stages"]["record_write"]["write_performed"] is False,
                "blocked record cycle must not write outside allowed root",
                failures,
            )

            selector_queue_path = Path(temp_dir) / "selector-queue.md"
            selector_queue_path.write_text(
                workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1"),
                encoding="utf-8",
            )
            selector = workbench.build_next_step_selector(selector_queue_path, record_root)
            check(selector["passed"] is True, f"next-step selector should pass: {selector['errors']}", failures)
            check(selector["candidate_present"] is True, "next-step selector should emit a candidate", failures)
            check(
                selector.get("candidate", {}).get("title") == "AGENTS OS external Git exact pre-push command gate v0.1",
                "next-step selector should keep publication target at exact pre-push gate without push evidence",
                failures,
            )
            check(
                selector.get("candidate", {}).get("substantive_progress") is True,
                "selector candidate must prove substantive progress",
                failures,
            )
            check(selector["validation_plan"]["level"] == "fast", "selector should default to fast validation", failures)
            post_push_queue_path = Path(temp_dir) / "post-push-selector-queue.md"
            post_push_queue_path.write_text(
                fixture_queue_with_now_lines(
                    workbench,
                    "AGENTS OS external Git publication target gate v0.1",
                    "closed evidence: remote branch created pr/workbench-next-step-fast-validation and draft PR #5 opened.",
                ),
                encoding="utf-8",
            )
            post_push_selector = workbench.build_next_step_selector(post_push_queue_path, record_root)
            check(
                post_push_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git post-push verification receipt v0.1",
                "next-step selector should choose post-push receipt only after push evidence",
                failures,
            )
            check(
                "git ls-remote origin refs/heads/pr/workbench-next-step-fast-validation"
                in post_push_selector.get("candidate", {}).get("validation", []),
                "post-push selector should verify the published branch ref",
                failures,
            )
            post_push_with_safety_note_queue_path = Path(temp_dir) / "post-push-safety-note-selector-queue.md"
            post_push_with_safety_note_queue_path.write_text(
                fixture_queue_with_now_lines(
                    workbench,
                    "AGENTS OS external Git publication target gate v0.1",
                    "closed evidence: pushed branch pr/workbench-next-step-fast-validation; no tags, no release.",
                ),
                encoding="utf-8",
            )
            post_push_with_safety_note_selector = workbench.build_next_step_selector(
                post_push_with_safety_note_queue_path,
                record_root,
            )
            check(
                post_push_with_safety_note_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git post-push verification receipt v0.1",
                "next-step selector should accept pushed-branch evidence with unrelated safety negation",
                failures,
            )
            post_push_after_comma_safety_note_queue_path = Path(temp_dir) / "post-push-comma-safety-note-selector-queue.md"
            post_push_after_comma_safety_note_queue_path.write_text(
                fixture_queue_with_now_lines(
                    workbench,
                    "AGENTS OS external Git publication target gate v0.1",
                    "closed evidence: no tags, no release, pushed branch pr/workbench-next-step-fast-validation.",
                ),
                encoding="utf-8",
            )
            post_push_after_comma_safety_note_selector = workbench.build_next_step_selector(
                post_push_after_comma_safety_note_queue_path,
                record_root,
            )
            check(
                post_push_after_comma_safety_note_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git post-push verification receipt v0.1",
                "next-step selector should accept pushed-branch evidence after comma-separated safety negation",
                failures,
            )
            post_push_after_stale_negation_queue_path = Path(temp_dir) / "post-push-stale-negation-selector-queue.md"
            post_push_after_stale_negation_queue_path.write_text(
                fixture_queue_with_now_lines(
                    workbench,
                    "AGENTS OS external Git publication target gate v0.1",
                    "closed evidence: branch not pushed yet; pushed branch pr/workbench-next-step-fast-validation.",
                ),
                encoding="utf-8",
            )
            post_push_after_stale_negation_selector = workbench.build_next_step_selector(
                post_push_after_stale_negation_queue_path,
                record_root,
            )
            check(
                "git ls-remote origin refs/heads/pr/workbench-next-step-fast-validation"
                in post_push_after_stale_negation_selector.get("candidate", {}).get("validation", []),
                "post-push selector should extract branch ref after stale negated push note",
                failures,
            )
            remote_branch_plan_queue_path = Path(temp_dir) / "remote-branch-plan-selector-queue.md"
            remote_branch_plan_queue_path.write_text(
                fixture_queue_with_now_lines(
                    workbench,
                    "AGENTS OS external Git publication target gate v0.1",
                    "pre-push plan field: remote branch: pr/workbench-next-step-fast-validation",
                ),
                encoding="utf-8",
            )
            remote_branch_plan_selector = workbench.build_next_step_selector(remote_branch_plan_queue_path, record_root)
            check(
                remote_branch_plan_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git exact pre-push command gate v0.1",
                "next-step selector must not treat remote branch target fields as post-push evidence",
                failures,
            )
            not_pushed_queue_path = Path(temp_dir) / "not-pushed-selector-queue.md"
            not_pushed_queue_path.write_text(
                fixture_queue_with_now_lines(
                    workbench,
                    "AGENTS OS external Git publication target gate v0.1",
                    "pre-push state: branch not pushed yet; remote branch: pr/workbench-next-step-fast-validation",
                ),
                encoding="utf-8",
            )
            not_pushed_selector = workbench.build_next_step_selector(not_pushed_queue_path, record_root)
            check(
                not_pushed_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git exact pre-push command gate v0.1",
                "next-step selector must keep negated push notes in the pre-push path",
                failures,
            )
            unrelated_post_push_queue_path = Path(temp_dir) / "unrelated-post-push-selector-queue.md"
            unrelated_post_push_queue_path.write_text(
                workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1").replace(
                    "old_task: closed",
                    "old_task: closed\nunrelated: remote branch created pr/old-work and PR #12 opened",
                ),
                encoding="utf-8",
            )
            unrelated_post_push_selector = workbench.build_next_step_selector(unrelated_post_push_queue_path, record_root)
            check(
                unrelated_post_push_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git exact pre-push command gate v0.1",
                "next-step selector must ignore unrelated CLOSED post-push evidence",
                failures,
            )
            closed_next_boundary_queue_path = Path(temp_dir) / "closed-next-boundary-selector-queue.md"
            closed_next_boundary_queue_path.write_text(
                workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1").replace(
                    "old_task: closed",
                    (
                        "old_task: closed\n"
                        "external_git_publication_target_gate_v0.1: accepted target; "
                        "next boundary is exact pre-push command gate"
                    ),
                ),
                encoding="utf-8",
            )
            closed_next_boundary_selector = workbench.build_next_step_selector(closed_next_boundary_queue_path, record_root)
            check(
                closed_next_boundary_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git exact pre-push command gate v0.1",
                "next-step selector must not treat CLOSED receipt prose as a completed pre-push gate",
                failures,
            )
            closed_pre_push_queue_path = Path(temp_dir) / "closed-pre-push-selector-queue.md"
            closed_pre_push_queue_path.write_text(
                workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1").replace(
                    "old_task: closed",
                    "old_task: closed\nexternal_git_exact_pre_push_command_gate_v0.1: accepted no-write command plan; no push",
                ),
                encoding="utf-8",
            )
            closed_pre_push_selector = workbench.build_next_step_selector(closed_pre_push_queue_path, record_root)
            check(
                closed_pre_push_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git command execution authorization gate v0.1",
                "next-step selector must not repeat a CLOSED exact pre-push command gate",
                failures,
            )
            post_push_receipt_now_queue_path = Path(temp_dir) / "post-push-receipt-now-selector-queue.md"
            post_push_receipt_now_queue_path.write_text(
                fixture_queue_with_now_lines(
                    workbench,
                    "AGENTS OS external Git post-push verification receipt v0.1",
                    "published remote ref verified by git ls-remote; local leftovers classified.",
                ).replace(
                    "old_task: closed",
                    "old_task: closed\nexternal_git_exact_pre_push_command_gate_v0.1: accepted no-write command plan; no push",
                ),
                encoding="utf-8",
            )
            post_push_receipt_now_selector = workbench.build_next_step_selector(post_push_receipt_now_queue_path, record_root)
            check(
                post_push_receipt_now_selector.get("candidate", {}).get("title")
                == "AGENTS OS external Git PR review tracking gate v0.1",
                "next-step selector must not rewind a post-push receipt NOW to execution authorization",
                failures,
            )

            duplicate_queue_path = Path(temp_dir) / "duplicate-selector-queue.md"
            duplicate_queue_path.write_text(
                workbench.fixture_queue_text("AGENTS OS external Git exact pre-push command gate v0.1"),
                encoding="utf-8",
            )
            duplicate_selector = workbench.build_next_step_selector(duplicate_queue_path, record_root)
            check(
                duplicate_selector["selector_state"] == "blocked_repeat_detected",
                "next-step selector should block same-semantic repeat",
                failures,
            )
            cli_selector = subprocess.run(
                [
                    "python3",
                    str(ROOT / "workbench.py"),
                    "select-next-step",
                    "--queue",
                    str(selector_queue_path),
                    "--record-root",
                    str(record_root),
                    "--json",
                ],
                cwd=workbench.WORKSPACE_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            check(cli_selector.returncode == 0, f"CLI select-next-step should pass: {cli_selector.stderr}", failures)
            if cli_selector.stdout:
                cli_selector_payload = json.loads(cli_selector.stdout)
                check(
                    cli_selector_payload.get("candidate", {}).get("substantive_progress") is True,
                    "CLI select-next-step should prove substantive progress",
                    failures,
                )
            else:
                failures.append("CLI select-next-step should emit JSON")

            fast_validation = workbench.validate_workbench_by_level("fast")
            check(
                fast_validation["passed"] is True,
                f"workbench fast validation should pass: {fast_validation['errors']}",
                failures,
            )
            check(fast_validation["actual_level"] == "fast", "fast validation should report actual level", failures)
            check(
                fast_validation["ordinary_progress_eligible"] is True,
                "fast validation should be eligible for ordinary progress",
                failures,
            )
            check(
                fast_validation["external_write_eligible"] is False,
                "fast validation must not be eligible for external write",
                failures,
            )
            check(
                "docctl status" in fast_validation["skipped_full_checks"],
                "fast validation should skip full docctl status",
                failures,
            )
            failed_full_metadata = workbench.attach_validation_metadata(
                {"passed": False, "errors": ["fixture failure"]},
                "full",
                workbench.time.monotonic(),
                required_level="full",
            )
            check(
                failed_full_metadata["external_write_eligible"] is False,
                "failed full validation must not be external-write eligible",
                failures,
            )
            check(
                failed_full_metadata["release_eligible"] is False,
                "failed full validation must not be release eligible",
                failures,
            )

        if failures:
            for failure in failures:
                print(f"FAIL {failure}")
            print(f"cases=10 failures={len(failures)} mode=fast")
            return 1

        print("PASS current stopped queue cycle")
        print("PASS local-safe workbench cycle")
        print("PASS provider stop cycle")
        print("PASS workbench record write gate fixtures")
        print("PASS workbench next-step selector fast fixtures")
        print("PASS workbench duplicate selector guard")
        print("PASS workbench CLI selector")
        print("PASS workbench fast validation")
        print("cases=10 failures=0 mode=fast")
        return 0

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
        empty_status = workbench.build_status(advance_record_root, queue_path)
        check(empty_status["passed"] is True, f"empty status should pass: {empty_status['errors']}", failures)
        check(
            empty_status["status_reconciliation"]["next_action_source"] == "live_queue",
            "empty status should treat the live queue as the current authority",
            failures,
        )
        check(
            empty_status["next_step"]["status"] == empty_status["live_queue"]["next_step"]["status"],
            "empty status should project the live queue next step",
            failures,
        )
        check(
            empty_status["next_step"].get("execution_authorized") is False,
            "empty status must keep execution authorization false",
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
        safe_status = workbench.build_status(advance_record_root, advance_queue_path)
        check(safe_status["passed"] is True, f"safe status should pass: {safe_status['errors']}", failures)
        check(
            safe_status["latest_advance_id"] == safe_advance["advance_id"],
            "safe status should identify safe advance as latest",
            failures,
        )
        check(
            safe_status["next_step"]["status"] == "review_queue_proposal",
            "safe status should preserve the pending review boundary",
            failures,
        )
        check(
            safe_status["status_reconciliation"]["record_next_step_status"]
            == "review_queue_proposal"
            and safe_status["status_reconciliation"]["next_action_source"]
            == "latest_record"
            and safe_status["status_reconciliation"]["queue_bytes_match_record"]
            is True
            and safe_status["status_reconciliation"]["record_boundary_pending"]
            is True
            and safe_status["status_reconciliation"][
                "record_boundary_may_be_stale"
            ]
            is False,
            "unchanged queue bytes must keep the record boundary authoritative",
            failures,
        )
        invalid_shadow_payload = json.loads(json.dumps(safe_advance))
        invalid_shadow_payload["advance_id"] = "ADVANCE-INVALID-SHADOW"
        invalid_shadow_payload["passed"] = False
        invalid_shadow_payload["errors"] = [
            "synthetic incomplete advance record"
        ]
        invalid_shadow_path = (
            advance_record_root / "invalid-shadow-advance.json"
        )
        invalid_shadow_path.write_text(
            json.dumps(
                invalid_shadow_payload,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        invalid_shadow_mtime_ns = (
            max(
                path.stat().st_mtime_ns
                for path in advance_record_root.glob("*.json")
                if path != invalid_shadow_path
            )
            + 1_000_000
        )
        os.utime(
            invalid_shadow_path,
            ns=(invalid_shadow_mtime_ns, invalid_shadow_mtime_ns),
        )
        invalid_shadow_status = workbench.build_status(
            advance_record_root,
            advance_queue_path,
        )
        check(
            invalid_shadow_status["passed"] is False
            and invalid_shadow_status["latest_advance_id"]
            == safe_advance["advance_id"]
            and invalid_shadow_status[
                "invalid_matching_advance_record_count"
            ]
            == 1
            and invalid_shadow_status[
                "invalid_live_binding_advance_record_count"
            ]
            == 1
            and invalid_shadow_status["status_reconciliation"][
                "record_boundary_pending"
            ]
            is True
            and any(
                "record reconciliation is required" in error
                for error in invalid_shadow_status["errors"]
            ),
            "invalid newer records must fail closed without shadowing a valid boundary",
            failures,
        )
        invalid_shadow_path.unlink()
        unbound_shadow_payload = json.loads(json.dumps(safe_advance))
        unbound_shadow_payload["advance_id"] = "ADVANCE-UNBOUND-SHADOW"
        unbound_shadow_payload.pop("source_queue_binding", None)
        unbound_shadow_path = (
            advance_record_root / "unbound-shadow-advance.json"
        )
        unbound_shadow_path.write_text(
            json.dumps(
                unbound_shadow_payload,
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        unbound_shadow_status = workbench.build_status(
            advance_record_root,
            advance_queue_path,
        )
        check(
            unbound_shadow_status["passed"] is False
            and unbound_shadow_status["latest_advance_id"]
            == safe_advance["advance_id"]
            and unbound_shadow_status["unbound_advance_record_count"]
            == 1
            and unbound_shadow_status["status_reconciliation"][
                "record_boundary_pending"
            ]
            is True
            and any(
                "unbound advance records cannot be reconciled" in error
                for error in unbound_shadow_status["errors"]
            ),
            "unbound records must fail closed without shadowing a valid boundary",
            failures,
        )
        unbound_shadow_path.unlink()
        advance_record_files_before = sorted(advance_record_root.glob("*.json"))
        repeated_run = workbench.build_run(
            "Write local governance report and run docctl validation.",
            advance_queue_path,
            record_root=advance_record_root,
            max_steps=2,
            allowed_queue_root=Path(temp_dir),
        )
        pending_selector = workbench.build_next_step_selector(
            advance_queue_path,
            advance_record_root,
        )
        pending_continue = workbench.build_continue_current(
            advance_queue_path,
            record_root=advance_record_root,
            max_steps=2,
            allowed_queue_root=Path(temp_dir),
        )
        pending_continue_loop = workbench.build_continue_loop(
            advance_queue_path,
            record_root=advance_record_root,
            max_cycles=2,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            repeated_run["passed"] is True
            and repeated_run["steps_performed"] == 0
            and repeated_run["record_write_count"] == 0
            and repeated_run["local_safe_execution_count"] == 0
            and repeated_run["stopped_reason"] == "review_queue_proposal",
            "repeated run must stop without re-executing an unchanged queue",
            failures,
        )
        check(
            pending_selector["passed"] is True
            and pending_selector["candidate_present"] is False
            and pending_selector["selector_state"]
            == "blocked_by_pending_record_boundary",
            "selector must not propose duplicate work across a pending boundary",
            failures,
        )
        check(
            pending_continue["passed"] is True
            and pending_continue["run"] is None
            and pending_continue["run_summary"]["record_write_count"] == 0
            and pending_continue["run_summary"]["local_safe_execution_count"]
            == 0
            and pending_continue["next_step"]["status"]
            == "review_queue_proposal"
            and sorted(advance_record_root.glob("*.json"))
            == advance_record_files_before,
            "continue must preserve a pending boundary without new records",
            failures,
        )
        check(
            pending_continue_loop["passed"] is True
            and pending_continue_loop["cycles_performed"] == 0
            and pending_continue_loop["record_write_count"] == 0
            and pending_continue_loop["local_safe_execution_count"] == 0
            and pending_continue_loop["stopped_reason"]
            == "review_queue_proposal"
            and sorted(advance_record_root.glob("*.json"))
            == advance_record_files_before,
            "continue loop must preserve a pending boundary without work",
            failures,
        )
        original_advance_queue_text = advance_queue_path.read_text(
            encoding="utf-8"
        )
        advance_queue_path.write_text(
            original_advance_queue_text + "\n<!-- reviewed queue change -->\n",
            encoding="utf-8",
        )
        changed_queue_status = workbench.build_status(
            advance_record_root,
            advance_queue_path,
        )
        check(
            changed_queue_status["passed"] is True
            and changed_queue_status["next_step"]["status"]
            == "queue_ready_for_run"
            and changed_queue_status["status_reconciliation"][
                "next_action_source"
            ]
            == "live_queue"
            and changed_queue_status["status_reconciliation"][
                "queue_bytes_match_record"
            ]
            is False
            and changed_queue_status["status_reconciliation"][
                "record_boundary_may_be_stale"
            ]
            is True,
            "changed queue bytes must supersede the bound record boundary",
            failures,
        )
        snapshot_record_queue_path = (
            Path(temp_dir) / "snapshot-record-queue.md"
        )
        snapshot_record_queue_path.write_text(
            workbench.fixture_queue_text(),
            encoding="utf-8",
        )
        snapshot_record_root = (
            Path(temp_dir) / "snapshot-bound-records"
        )
        snapshot_record_root.mkdir()
        snapshot_record_intent = (
            "Write snapshot-bound governance evidence and run validation."
        )
        snapshot_h1_advance = workbench.build_advance(
            snapshot_record_intent,
            snapshot_record_queue_path,
            record_root=snapshot_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        snapshot_h1_binding = snapshot_h1_advance.get(
            "source_queue_binding",
            {},
        )
        snapshot_h1_cycle_path = snapshot_record_root / Path(
            snapshot_h1_advance["stages"]["record"]["cycle_record_path"]
        ).name
        snapshot_h1_advance_path = snapshot_record_root / Path(
            snapshot_h1_advance["stages"]["record"]["advance_record_path"]
        ).name
        snapshot_record_queue_path.write_text(
            workbench.fixture_queue_text()
            + "\n<!-- distinct queue snapshot H2 -->\n",
            encoding="utf-8",
        )
        snapshot_h2_advance = workbench.build_advance(
            snapshot_record_intent,
            snapshot_record_queue_path,
            record_root=snapshot_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        snapshot_h2_binding = snapshot_h2_advance.get(
            "source_queue_binding",
            {},
        )
        snapshot_h2_cycle_path = snapshot_record_root / Path(
            snapshot_h2_advance["stages"]["record"]["cycle_record_path"]
        ).name
        snapshot_h2_advance_path = snapshot_record_root / Path(
            snapshot_h2_advance["stages"]["record"]["advance_record_path"]
        ).name
        snapshot_record_files = sorted(
            snapshot_record_root.glob("*.json")
        )
        snapshot_h1_cycle_payload = (
            workbench.load_json(snapshot_h1_cycle_path)
            if snapshot_h1_cycle_path.exists()
            else {}
        )
        snapshot_h1_advance_payload = (
            workbench.load_json(snapshot_h1_advance_path)
            if snapshot_h1_advance_path.exists()
            else {}
        )
        snapshot_h2_cycle_payload = (
            workbench.load_json(snapshot_h2_cycle_path)
            if snapshot_h2_cycle_path.exists()
            else {}
        )
        snapshot_h2_advance_payload = (
            workbench.load_json(snapshot_h2_advance_path)
            if snapshot_h2_advance_path.exists()
            else {}
        )
        check(
            snapshot_h1_advance["passed"] is True
            and snapshot_h2_advance["passed"] is True
            and snapshot_h1_advance["advance_id"]
            != snapshot_h2_advance["advance_id"]
            and snapshot_h1_binding != snapshot_h2_binding
            and snapshot_h1_cycle_path != snapshot_h2_cycle_path
            and snapshot_h1_advance_path != snapshot_h2_advance_path
            and len(snapshot_record_files) == 4
            and snapshot_h1_cycle_payload.get("replay_inputs", {}).get(
                "queue_binding"
            )
            == snapshot_h1_binding
            and snapshot_h1_advance_payload.get("source_queue_binding")
            == snapshot_h1_binding
            and snapshot_h2_cycle_payload.get("replay_inputs", {}).get(
                "queue_binding"
            )
            == snapshot_h2_binding
            and snapshot_h2_advance_payload.get("source_queue_binding")
            == snapshot_h2_binding,
            "same-intent advances over distinct queue snapshots must preserve both cycle and advance records",
            failures,
        )
        record_binding_skew_queue_path = (
            Path(temp_dir) / "record-binding-skew-queue.md"
        )
        record_binding_skew_queue_path.write_text(
            workbench.fixture_queue_text(),
            encoding="utf-8",
        )
        record_binding_skew_root = (
            Path(temp_dir) / "record-binding-skew-records"
        )
        record_binding_skew_root.mkdir()
        original_load_bound_queue_snapshot = (
            workbench.load_bound_queue_snapshot
        )
        record_binding_skew_calls = {"count": 0}

        def record_binding_skew_snapshot(
            chain: object,
            queue_path: Path,
        ) -> tuple[dict | None, str | None]:
            snapshot_result = original_load_bound_queue_snapshot(
                chain,
                queue_path,
            )
            record_binding_skew_calls["count"] += 1
            if record_binding_skew_calls["count"] == 1:
                record_binding_skew_queue_path.write_text(
                    workbench.fixture_queue_text()
                    + "\n<!-- changed after record-path binding -->\n",
                    encoding="utf-8",
                )
            return snapshot_result

        workbench.load_bound_queue_snapshot = (
            record_binding_skew_snapshot
        )
        try:
            record_binding_skew_advance = workbench.build_advance(
                "Do not record after queue binding skew.",
                record_binding_skew_queue_path,
                record_root=record_binding_skew_root,
                allowed_queue_root=Path(temp_dir),
            )
        finally:
            workbench.load_bound_queue_snapshot = (
                original_load_bound_queue_snapshot
            )
        check(
            record_binding_skew_calls["count"] >= 2
            and record_binding_skew_advance["passed"] is False
            and record_binding_skew_advance["stages"]["execution"][
                "local_safe_execution_performed"
            ]
            is False
            and record_binding_skew_advance[
                "cycle_record_write_performed"
            ]
            is False
            and record_binding_skew_advance[
                "advance_record_write_performed"
            ]
            is False
            and not list(record_binding_skew_root.glob("*.json"))
            and any(
                "queue bytes changed after the caller snapshot"
                in error
                for error in record_binding_skew_advance["errors"]
            ),
            "advance must fail closed when queue bytes change after record-path binding",
            failures,
        )
        expected_binding_queue_path = (
            Path(temp_dir) / "expected-binding-queue.md"
        )
        expected_binding_queue_path.write_text(
            workbench.fixture_queue_text(),
            encoding="utf-8",
        )
        expected_binding_record_root = (
            Path(temp_dir) / "expected-binding-records"
        )
        expected_binding_record_root.mkdir()
        expected_binding_status = workbench.build_status(
            expected_binding_record_root,
            expected_binding_queue_path,
        )
        expected_binding = expected_binding_status["live_queue"][
            "queue_binding"
        ]
        expected_binding_queue_path.write_text(
            workbench.fixture_queue_text()
            + "\n<!-- changed after caller snapshot -->\n",
            encoding="utf-8",
        )
        expected_binding_run = workbench.build_run(
            "Write local governance report and run docctl validation.",
            expected_binding_queue_path,
            record_root=expected_binding_record_root,
            max_steps=2,
            allowed_queue_root=Path(temp_dir),
            expected_queue_binding=expected_binding,
        )
        check(
            expected_binding_run["passed"] is False
            and expected_binding_run["steps_performed"] == 0
            and expected_binding_run["record_write_count"] == 0
            and expected_binding_run["local_safe_execution_count"] == 0
            and not list(expected_binding_record_root.glob("*.json"))
            and any(
                "queue bytes changed after the caller status snapshot"
                in error
                for error in expected_binding_run["errors"]
            ),
            "run must fail closed when queue bytes change after caller status",
            failures,
        )
        expected_binding_changed_bytes = (
            expected_binding_queue_path.read_bytes()
        )
        expected_binding_advance = workbench.build_advance(
            "Write local governance report and run docctl validation.",
            expected_binding_queue_path,
            record_root=expected_binding_record_root,
            apply_intake=True,
            allowed_queue_root=Path(temp_dir),
            expected_queue_binding=expected_binding,
        )
        check(
            expected_binding_advance["passed"] is False
            and expected_binding_advance["stages"]["execution"][
                "local_safe_execution_performed"
            ]
            is False
            and expected_binding_advance["stages"]["intake_apply"][
                "write_performed"
            ]
            is False
            and expected_binding_advance["active_queue_modified"] is False
            and expected_binding_advance["queue_write_authorized"] is False
            and expected_binding_queue_path.read_bytes()
            == expected_binding_changed_bytes
            and not list(expected_binding_record_root.glob("*.json")),
            "advance must not execute, record, or apply intake after binding drift",
            failures,
        )
        reversion_queue_path = Path(temp_dir) / "hash-reversion-queue.md"
        reversion_h1_bytes = workbench.fixture_queue_text().encode("utf-8")
        reversion_queue_path.write_bytes(reversion_h1_bytes)
        reversion_record_root = Path(temp_dir) / "hash-reversion-records"
        reversion_record_root.mkdir()
        reversion_h1_advance = workbench.build_advance(
            "Write H1 local governance report and run docctl validation.",
            reversion_queue_path,
            record_root=reversion_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        reversion_queue_path.write_bytes(
            reversion_h1_bytes
            + b"\n<!-- distinct H2 queue bytes -->\n"
        )
        reversion_h2_advance = workbench.build_advance(
            "Write H2 local governance report and run docctl validation.",
            reversion_queue_path,
            record_root=reversion_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        reversion_h2_record_path = (
            reversion_record_root
            / Path(
                reversion_h2_advance["stages"]["record"][
                    "record_path"
                ]
            ).name
        )
        reversion_h1_record_path = (
            reversion_record_root
            / Path(
                reversion_h1_advance["stages"]["record"][
                    "record_path"
                ]
            ).name
        )
        reversion_h2_mtime_ns = (
            reversion_h1_record_path.stat().st_mtime_ns + 1_000_000
        )
        os.utime(
            reversion_h2_record_path,
            ns=(reversion_h2_mtime_ns, reversion_h2_mtime_ns),
        )
        reversion_queue_path.write_bytes(reversion_h1_bytes)
        reversion_status = workbench.build_status(
            reversion_record_root,
            reversion_queue_path,
        )
        reversion_record_files_before = sorted(
            reversion_record_root.glob("*.json")
        )
        reversion_run = workbench.build_run(
            "Do not repeat reverted H1 queue work.",
            reversion_queue_path,
            record_root=reversion_record_root,
            max_steps=2,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            reversion_h1_advance["passed"] is True
            and reversion_h2_advance["passed"] is True
            and reversion_status["passed"] is True
            and reversion_status["latest_advance_id"]
            == reversion_h2_advance["advance_id"]
            and reversion_status["authoritative_record"]["advance_id"]
            == reversion_h1_advance["advance_id"]
            and reversion_status["exact_matching_advance_record_count"]
            == 1
            and reversion_status["next_step"]["status"]
            == "review_queue_proposal"
            and reversion_status["status_reconciliation"][
                "record_boundary_pending"
            ]
            is True
            and reversion_status["status_reconciliation"][
                "record_boundary_may_be_stale"
            ]
            is True
            and reversion_run["passed"] is True
            and reversion_run["steps_performed"] == 0
            and reversion_run["record_write_count"] == 0
            and reversion_run["local_safe_execution_count"] == 0
            and sorted(reversion_record_root.glob("*.json"))
            == reversion_record_files_before,
            "H1-H2-H1 reversion must preserve the exact H1 pending boundary",
            failures,
        )
        selector_skew_queue_path = (
            Path(temp_dir) / "selector-read-skew-queue.md"
        )
        selector_skew_queue_path.write_text(
            workbench.fixture_queue_text(),
            encoding="utf-8",
        )
        selector_skew_record_root = (
            Path(temp_dir) / "selector-read-skew-records"
        )
        selector_skew_record_root.mkdir()
        original_load_bound_queue_snapshot = (
            workbench.load_bound_queue_snapshot
        )
        selector_skew_calls = {"count": 0}

        def selector_skew_snapshot(
            chain: object,
            queue_path: Path,
        ) -> tuple[dict | None, str | None]:
            snapshot_result = original_load_bound_queue_snapshot(
                chain,
                queue_path,
            )
            selector_skew_calls["count"] += 1
            if selector_skew_calls["count"] == 1:
                selector_skew_queue_path.write_text(
                    workbench.fixture_queue_text()
                    + "\n<!-- selector status/read skew -->\n",
                    encoding="utf-8",
                )
            return snapshot_result

        workbench.load_bound_queue_snapshot = selector_skew_snapshot
        try:
            selector_skew = workbench.build_next_step_selector(
                selector_skew_queue_path,
                selector_skew_record_root,
            )
        finally:
            workbench.load_bound_queue_snapshot = (
                original_load_bound_queue_snapshot
            )
        check(
            selector_skew_calls["count"] >= 2
            and selector_skew["passed"] is False
            and selector_skew["candidate_present"] is False
            and any(
                "selector queue bytes changed after status reconciliation"
                in error
                for error in selector_skew["errors"]
            ),
            "selector must fail closed on status/read queue-byte skew",
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
                workbench.valid_queue_snapshot_binding(
                    safe_advance_payload.get("source_queue_binding")
                ),
                "safe advance record must bind exact source queue bytes",
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
        status_after_intake = workbench.build_status(advance_record_root, advance_apply_queue_path)
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
        check(
            status_after_intake["next_step"]["status"] == "queue_ready_for_run"
            and status_after_intake["status_reconciliation"][
                "next_action_source"
            ]
            == "live_queue"
            and status_after_intake["status_reconciliation"][
                "queue_bytes_match_record"
            ]
            is False
            and status_after_intake["status_reconciliation"][
                "record_boundary_may_be_stale"
            ]
            is True,
            "applied intake bytes must supersede the source record boundary",
            failures,
        )
        cli_status = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "status",
                "--queue",
                str(advance_apply_queue_path),
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

        selector_queue_path = Path(temp_dir) / "selector-queue.md"
        selector_queue_path.write_text(
            workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1"),
            encoding="utf-8",
        )
        selector = workbench.build_next_step_selector(selector_queue_path, advance_record_root)
        check(selector["passed"] is True, f"next-step selector should pass: {selector['errors']}", failures)
        check(selector["candidate_present"] is True, "next-step selector should emit a candidate", failures)
        selector_candidate = selector.get("candidate", {})
        check(
            selector_candidate.get("title") == "AGENTS OS external Git exact pre-push command gate v0.1",
            "next-step selector should keep publication target at exact pre-push gate without push evidence",
            failures,
        )
        check(selector_candidate.get("not_repeat_of_now") is True, "selector candidate must not repeat NOW", failures)
        check(selector_candidate.get("not_repeat_of_queue") is True, "selector candidate must not repeat queue", failures)
        check(
            selector_candidate.get("substantive_progress") is True,
            "selector candidate must prove substantive progress",
            failures,
        )
        check(bool(selector_candidate.get("goal_delta")), "selector candidate must describe goal delta", failures)
        check(bool(selector_candidate.get("state_delta")), "selector candidate must describe state delta", failures)
        check(
            len(selector_candidate.get("completion_criteria", [])) >= 2,
            "selector candidate must include completion criteria",
            failures,
        )
        check(selector["validation_plan"]["level"] == "fast", "selector should default to fast validation", failures)
        check(
            selector["validation_plan"]["full_validation_required_before_external_write"] is True,
            "selector must require full validation before external write",
            failures,
        )
        check(selector["write_performed"] is False, "selector must be read-only", failures)
        post_push_selector_queue_path = Path(temp_dir) / "post-push-selector-queue.md"
        post_push_selector_queue_path.write_text(
            fixture_queue_with_now_lines(
                workbench,
                "AGENTS OS external Git publication target gate v0.1",
                "closed evidence: remote branch created pr/workbench-next-step-fast-validation and draft PR #5 opened.",
            ),
            encoding="utf-8",
        )
        post_push_selector = workbench.build_next_step_selector(post_push_selector_queue_path, advance_record_root)
        check(
            post_push_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git post-push verification receipt v0.1",
            "next-step selector should choose post-push receipt only after push evidence",
            failures,
        )
        check(
            "git ls-remote origin refs/heads/pr/workbench-next-step-fast-validation"
            in post_push_selector.get("candidate", {}).get("validation", []),
            "post-push selector should verify the published branch ref",
            failures,
        )
        post_push_with_safety_note_selector_queue_path = Path(temp_dir) / "post-push-safety-note-selector-queue.md"
        post_push_with_safety_note_selector_queue_path.write_text(
            fixture_queue_with_now_lines(
                workbench,
                "AGENTS OS external Git publication target gate v0.1",
                "closed evidence: pushed branch pr/workbench-next-step-fast-validation; no tags, no release.",
            ),
            encoding="utf-8",
        )
        post_push_with_safety_note_selector = workbench.build_next_step_selector(
            post_push_with_safety_note_selector_queue_path,
            advance_record_root,
        )
        check(
            post_push_with_safety_note_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git post-push verification receipt v0.1",
            "next-step selector should accept pushed-branch evidence with unrelated safety negation",
            failures,
        )
        post_push_after_comma_safety_note_selector_queue_path = Path(temp_dir) / "post-push-comma-safety-note-selector-queue.md"
        post_push_after_comma_safety_note_selector_queue_path.write_text(
            fixture_queue_with_now_lines(
                workbench,
                "AGENTS OS external Git publication target gate v0.1",
                "closed evidence: no tags, no release, pushed branch pr/workbench-next-step-fast-validation.",
            ),
            encoding="utf-8",
        )
        post_push_after_comma_safety_note_selector = workbench.build_next_step_selector(
            post_push_after_comma_safety_note_selector_queue_path,
            advance_record_root,
        )
        check(
            post_push_after_comma_safety_note_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git post-push verification receipt v0.1",
            "next-step selector should accept pushed-branch evidence after comma-separated safety negation",
            failures,
        )
        post_push_after_stale_negation_selector_queue_path = Path(temp_dir) / "post-push-stale-negation-selector-queue.md"
        post_push_after_stale_negation_selector_queue_path.write_text(
            fixture_queue_with_now_lines(
                workbench,
                "AGENTS OS external Git publication target gate v0.1",
                "closed evidence: branch not pushed yet; pushed branch pr/workbench-next-step-fast-validation.",
            ),
            encoding="utf-8",
        )
        post_push_after_stale_negation_selector = workbench.build_next_step_selector(
            post_push_after_stale_negation_selector_queue_path,
            advance_record_root,
        )
        check(
            "git ls-remote origin refs/heads/pr/workbench-next-step-fast-validation"
            in post_push_after_stale_negation_selector.get("candidate", {}).get("validation", []),
            "post-push selector should extract branch ref after stale negated push note",
            failures,
        )
        remote_branch_plan_selector_queue_path = Path(temp_dir) / "remote-branch-plan-selector-queue.md"
        remote_branch_plan_selector_queue_path.write_text(
            fixture_queue_with_now_lines(
                workbench,
                "AGENTS OS external Git publication target gate v0.1",
                "pre-push plan field: remote branch: pr/workbench-next-step-fast-validation",
            ),
            encoding="utf-8",
        )
        remote_branch_plan_selector = workbench.build_next_step_selector(
            remote_branch_plan_selector_queue_path,
            advance_record_root,
        )
        check(
            remote_branch_plan_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git exact pre-push command gate v0.1",
            "next-step selector must not treat remote branch target fields as post-push evidence",
            failures,
        )
        not_pushed_selector_queue_path = Path(temp_dir) / "not-pushed-selector-queue.md"
        not_pushed_selector_queue_path.write_text(
            fixture_queue_with_now_lines(
                workbench,
                "AGENTS OS external Git publication target gate v0.1",
                "pre-push state: branch not pushed yet; remote branch: pr/workbench-next-step-fast-validation",
            ),
            encoding="utf-8",
        )
        not_pushed_selector = workbench.build_next_step_selector(
            not_pushed_selector_queue_path,
            advance_record_root,
        )
        check(
            not_pushed_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git exact pre-push command gate v0.1",
            "next-step selector must keep negated push notes in the pre-push path",
            failures,
        )
        unrelated_post_push_selector_queue_path = Path(temp_dir) / "unrelated-post-push-selector-queue.md"
        unrelated_post_push_selector_queue_path.write_text(
            workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1").replace(
                "old_task: closed",
                "old_task: closed\nunrelated: remote branch created pr/old-work and PR #12 opened",
            ),
            encoding="utf-8",
        )
        unrelated_post_push_selector = workbench.build_next_step_selector(
            unrelated_post_push_selector_queue_path,
            advance_record_root,
        )
        check(
            unrelated_post_push_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git exact pre-push command gate v0.1",
            "next-step selector must ignore unrelated CLOSED post-push evidence",
            failures,
        )
        closed_next_boundary_selector_queue_path = Path(temp_dir) / "closed-next-boundary-selector-queue.md"
        closed_next_boundary_selector_queue_path.write_text(
            workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1").replace(
                "old_task: closed",
                (
                    "old_task: closed\n"
                    "external_git_publication_target_gate_v0.1: accepted target; "
                    "next boundary is exact pre-push command gate"
                ),
            ),
            encoding="utf-8",
        )
        closed_next_boundary_selector = workbench.build_next_step_selector(
            closed_next_boundary_selector_queue_path,
            advance_record_root,
        )
        check(
            closed_next_boundary_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git exact pre-push command gate v0.1",
            "next-step selector must not treat CLOSED receipt prose as a completed pre-push gate",
            failures,
        )
        closed_pre_push_selector_queue_path = Path(temp_dir) / "closed-pre-push-selector-queue.md"
        closed_pre_push_selector_queue_path.write_text(
            workbench.fixture_queue_text("AGENTS OS external Git publication target gate v0.1").replace(
                "old_task: closed",
                "old_task: closed\nexternal_git_exact_pre_push_command_gate_v0.1: accepted no-write command plan; no push",
            ),
            encoding="utf-8",
        )
        closed_pre_push_selector = workbench.build_next_step_selector(
            closed_pre_push_selector_queue_path,
            advance_record_root,
        )
        check(
            closed_pre_push_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git command execution authorization gate v0.1",
            "next-step selector must not repeat a CLOSED exact pre-push command gate",
            failures,
        )
        post_push_receipt_now_selector_queue_path = Path(temp_dir) / "post-push-receipt-now-selector-queue.md"
        post_push_receipt_now_selector_queue_path.write_text(
            fixture_queue_with_now_lines(
                workbench,
                "AGENTS OS external Git post-push verification receipt v0.1",
                "published remote ref verified by git ls-remote; local leftovers classified.",
            ).replace(
                "old_task: closed",
                "old_task: closed\nexternal_git_exact_pre_push_command_gate_v0.1: accepted no-write command plan; no push",
            ),
            encoding="utf-8",
        )
        post_push_receipt_now_selector = workbench.build_next_step_selector(
            post_push_receipt_now_selector_queue_path,
            advance_record_root,
        )
        check(
            post_push_receipt_now_selector.get("candidate", {}).get("title")
            == "AGENTS OS external Git PR review tracking gate v0.1",
            "next-step selector must not rewind a post-push receipt NOW to execution authorization",
            failures,
        )
        active_loop_selector_queue_path = Path(temp_dir) / "active-loop-selector-queue.md"
        active_loop_selector_queue_path.write_text(
            workbench.fixture_queue_text("AGENTS OS codex-appserver active-loop import gate v0.1"),
            encoding="utf-8",
        )
        active_loop_selector = workbench.build_next_step_selector(active_loop_selector_queue_path, advance_record_root)
        check(
            active_loop_selector["passed"] is True,
            f"active-loop selector should pass: {active_loop_selector['errors']}",
            failures,
        )
        active_loop_candidate = active_loop_selector.get("candidate", {})
        check(
            active_loop_candidate.get("title") == "AGENTS OS active-loop receipt contract review v0.1",
            "active-loop selector should choose receipt contract review",
            failures,
        )
        check(
            active_loop_candidate.get("substantive_progress") is True,
            "active-loop selector candidate must prove substantive progress",
            failures,
        )
        check(
            active_loop_candidate.get("not_repeat_of_queue") is True,
            "active-loop selector candidate must not repeat queue",
            failures,
        )
        duplicate_selector_queue_path = Path(temp_dir) / "duplicate-selector-queue.md"
        duplicate_selector_queue_path.write_text(
            workbench.fixture_queue_text("AGENTS OS external Git exact pre-push command gate v0.1"),
            encoding="utf-8",
        )
        duplicate_selector = workbench.build_next_step_selector(duplicate_selector_queue_path, advance_record_root)
        check(
            duplicate_selector["selector_state"] == "blocked_repeat_detected",
            "next-step selector should block same-semantic repeat",
            failures,
        )
        check(duplicate_selector["passed"] is False, "duplicate selector should fail closed", failures)
        cli_selector = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "select-next-step",
                "--queue",
                str(selector_queue_path),
                "--record-root",
                str(advance_record_root),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(cli_selector.returncode == 0, f"CLI select-next-step should pass: {cli_selector.stderr}", failures)
        if cli_selector.stdout:
            cli_selector_payload = json.loads(cli_selector.stdout)
            check(
                cli_selector_payload.get("schema_version") == "agents-os.workbench.next-step-selector.v0.1",
                "CLI select-next-step should emit selector schema",
                failures,
            )
            check(
                cli_selector_payload.get("candidate", {}).get("substantive_progress") is True,
                "CLI select-next-step should prove substantive progress",
                failures,
            )
        else:
            failures.append("CLI select-next-step should emit JSON")

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
        stopped_goal_status = workbench.build_status(advance_record_root, stopped_queue_path)
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
        goal_status = workbench.build_status(advance_record_root, goal_queue_path)
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
        route_transaction_fault_path = Path(temp_dir) / "route-transaction-fault-queue.md"
        route_transaction_fault_text = workbench.fixture_route_stop_queue_text()
        route_transaction_fault_path.write_text(route_transaction_fault_text, encoding="utf-8")
        original_workbench_import = workbench.import_module
        workbench_fault_state = {"triggered": False}

        def import_with_post_exchange_fault(path: Path, module_name: str) -> ModuleType:
            module = original_workbench_import(path, module_name)
            if Path(path) == workbench.CONTROL_CHAIN_PATH:
                original_exchange = module.rename_exchange

                def injected_post_cas_byte_swap(
                    parent_fd: int,
                    first_name: str,
                    second_name: str,
                ) -> None:
                    if not workbench_fault_state["triggered"]:
                        workbench_fault_state["triggered"] = True
                        route_transaction_fault_path.write_text(
                            fixture_generic_p3_governance_gate_queue_text(),
                            encoding="utf-8",
                        )
                    original_exchange(parent_fd, first_name, second_name)

                module.rename_exchange = injected_post_cas_byte_swap
            return module

        workbench.import_module = import_with_post_exchange_fault
        try:
            route_transaction_fault = workbench.build_route_choice_apply_gate(
                route_choice_text,
                route_transaction_fault_path,
                apply=True,
                allowed_queue_root=Path(temp_dir),
            )
        finally:
            workbench.import_module = original_workbench_import
        check(
            workbench_fault_state["triggered"] is True
            and route_transaction_fault["passed"] is False
            and route_transaction_fault["transaction_outcome"] == "PARTIAL_OR_UNKNOWN"
            and route_transaction_fault["queue_state"] == "UNKNOWN"
            and route_transaction_fault["queue_state_known"] is False
            and route_transaction_fault["queue_commit_attempted"] is True
            and route_transaction_fault["rollback_performed"] is True
            and route_transaction_fault["write_performed"] is True
            and route_transaction_fault["workspace_route_state_modified"] is None
            and route_transaction_fault["active_queue_modified"] is None
            and route_transaction_fault["queue_write_authorized"] is False
            and route_transaction_fault["requires_jenn_decision"] is True,
            f"Workbench must preserve truthful PARTIAL transaction evidence: {route_transaction_fault}",
            failures,
        )
        check(
            route_transaction_fault["review"]["review_status"] == "blocked"
            and route_transaction_fault["next_step"]["status"] == "queue_state_reconciliation_required"
            and route_transaction_fault["next_step"]["owner"] == "Jenn"
            and route_transaction_fault["next_step"]["active_queue_mutation_authorized"] is False,
            "Workbench PARTIAL transaction must stop at Jenn-owned exact-byte reconciliation",
            failures,
        )
        check(
            route_transaction_fault_path.read_text(encoding="utf-8")
            == fixture_generic_p3_governance_gate_queue_text(),
            "Workbench post-CAS rollback must preserve externally changed queue bytes",
            failures,
        )

        unresolved_temp_queue_path = Path(temp_dir) / "unresolved-temp-cleanup-queue.md"
        unresolved_temp_alias_path = Path(temp_dir) / "unresolved-temp-cleanup-alias.md"
        unresolved_temp_queue_text = workbench.fixture_route_stop_queue_text()
        unresolved_temp_queue_path.write_text(unresolved_temp_queue_text, encoding="utf-8")
        unresolved_temp_state = {"triggered": False}

        def import_with_unresolved_temp_cleanup(path: Path, module_name: str) -> ModuleType:
            module = original_workbench_import(path, module_name)
            if Path(path) == workbench.CONTROL_CHAIN_PATH:
                original_temp_write = module.write_transaction_temp_fd

                def add_replacement_link_after_write(file_fd: int, data: bytes) -> None:
                    original_temp_write(file_fd, data)
                    if not unresolved_temp_state["triggered"]:
                        temp_entries = list(
                            unresolved_temp_queue_path.parent.glob(
                                f".{unresolved_temp_queue_path.name}.agents-os-txn-*.tmp"
                            )
                        )
                        if len(temp_entries) != 1:
                            raise OSError("unresolved temp cleanup fixture entry is unavailable")
                        os.link(temp_entries[0], unresolved_temp_alias_path)
                        unresolved_temp_state["triggered"] = True

                module.write_transaction_temp_fd = add_replacement_link_after_write
            return module

        workbench.import_module = import_with_unresolved_temp_cleanup
        try:
            unresolved_temp_result = workbench.build_route_choice_apply_gate(
                route_choice_text,
                unresolved_temp_queue_path,
                apply=True,
                allowed_queue_root=Path(temp_dir),
            )
        finally:
            workbench.import_module = original_workbench_import
        check(
            unresolved_temp_state["triggered"] is True
            and unresolved_temp_result["passed"] is False
            and unresolved_temp_result["transaction_outcome"] == "NO_WRITE"
            and unresolved_temp_result["queue_state"] == "UNCHANGED"
            and unresolved_temp_result["queue_state_known"] is True
            and unresolved_temp_result["queue_commit_attempted"] is False
            and unresolved_temp_result["write_performed"] is False
            and unresolved_temp_result["temp_cleanup_confirmed"] is False
            and unresolved_temp_result["workspace_route_state_modified"] is False
            and unresolved_temp_result["active_queue_modified"] is False
            and unresolved_temp_result["queue_write_authorized"] is False
            and unresolved_temp_result["requires_jenn_decision"] is True,
            (
                "Workbench must preserve NO_WRITE evidence while surfacing unresolved "
                f"transaction cleanup: {unresolved_temp_result}"
            ),
            failures,
        )
        check(
            unresolved_temp_result["review"]["review_status"] == "blocked"
            and unresolved_temp_result["next_step"]["status"]
            == "queue_state_reconciliation_required"
            and unresolved_temp_result["next_step"]["owner"] == "Jenn"
            and unresolved_temp_result["next_step"]["active_queue_mutation_authorized"]
            is False
            and unresolved_temp_queue_path.read_text(encoding="utf-8")
            == unresolved_temp_queue_text,
            "Workbench unresolved temp cleanup must stop at Jenn-owned reconciliation",
            failures,
        )
        if unresolved_temp_alias_path.exists():
            unresolved_temp_alias_path.unlink()

        governance_gate_queue_path = Path(temp_dir) / "governance-gate-queue.md"
        governance_gate_queue_text = fixture_governance_gate_queue_text()
        governance_gate_queue_path.write_text(governance_gate_queue_text, encoding="utf-8")
        governance_route_preview = workbench.build_route_choice_preview(
            route_choice_text,
            governance_gate_queue_path,
        )
        check(
            governance_route_preview["passed"] is False,
            "active Jenn governance gate should block Workbench route preview",
            failures,
        )
        check(
            governance_route_preview["active_jenn_governance_gate"] is True
            and governance_route_preview["bundle"]["can_apply_with_separate_apply_gate"] is False,
            "active Jenn governance gate should block Workbench apply readiness",
            failures,
        )
        check(
            governance_route_preview["next_step"]["status"] == "governance_decision_required"
            and governance_route_preview["next_step"]["owner"] == "Jenn",
            "active Jenn governance gate should preserve Jenn as preview decision owner",
            failures,
        )
        governance_apply_preview = workbench.build_route_choice_apply_gate(
            route_choice_text,
            governance_gate_queue_path,
            apply=False,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            governance_apply_preview["passed"] is False
            and governance_apply_preview["apply_gate"]["queue_adoption_authorized"] is False,
            "active Jenn governance gate should block Workbench apply preview",
            failures,
        )
        governance_apply = workbench.build_route_choice_apply_gate(
            route_choice_text,
            governance_gate_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            governance_apply["passed"] is False
            and governance_apply["apply_gate"]["queue_adoption_authorized"] is False
            and governance_apply["requires_jenn_decision"] is True,
            "active Jenn governance gate should block Workbench apply production path",
            failures,
        )
        check(
            governance_apply["write_performed"] is False
            and governance_apply["active_queue_modified"] is False
            and governance_apply["queue_write_authorized"] is False,
            "blocked Workbench governance apply must keep all write flags false",
            failures,
        )
        check(
            governance_gate_queue_path.read_text(encoding="utf-8") == governance_gate_queue_text,
            "blocked Workbench governance apply must preserve exact queue bytes",
            failures,
        )
        generic_p3_gate_queue_path = Path(temp_dir) / "generic-p3-governance-gate-queue.md"
        generic_p3_gate_queue_text = fixture_generic_p3_governance_gate_queue_text()
        generic_p3_gate_queue_path.write_text(generic_p3_gate_queue_text, encoding="utf-8")
        generic_p3_route_preview = workbench.build_route_choice_preview(
            route_choice_text,
            generic_p3_gate_queue_path,
        )
        generic_p3_route_apply = workbench.build_route_choice_apply_gate(
            route_choice_text,
            generic_p3_gate_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            generic_p3_route_preview["passed"] is False
            and generic_p3_route_preview["active_jenn_governance_gate"] is True
            and generic_p3_route_preview["bundle"]["can_apply_with_separate_apply_gate"] is False,
            "generic P3 blocked NOW must block Workbench route preview and apply readiness",
            failures,
        )
        check(
            generic_p3_route_preview["next_step"]["status"] == "governance_decision_required"
            and generic_p3_route_preview["next_step"]["owner"] == "Jenn",
            "generic P3 Workbench preview must surface Jenn governance decision",
            failures,
        )
        check(
            generic_p3_route_apply["passed"] is False
            and generic_p3_route_apply["active_jenn_governance_gate"] is True
            and generic_p3_route_apply["apply_gate"]["queue_adoption_authorized"] is False
            and generic_p3_route_apply["requires_jenn_decision"] is True
            and generic_p3_route_apply["write_performed"] is False,
            "generic P3 blocked NOW must fail closed in Workbench apply",
            failures,
        )
        check(
            generic_p3_gate_queue_path.read_text(encoding="utf-8") == generic_p3_gate_queue_text,
            "generic P3 Workbench attacks must preserve exact queue bytes",
            failures,
        )
        generic_p3_run_record_root = Path(temp_dir) / "generic-p3-run-records"
        generic_p3_run_record_root.mkdir()
        generic_p3_run = workbench.build_run(
            "Continue current work.",
            generic_p3_gate_queue_path,
            record_root=generic_p3_run_record_root,
            max_steps=3,
            allowed_queue_root=Path(temp_dir),
        )
        check(
            generic_p3_run["passed"] is True
            and generic_p3_run["steps_performed"] == 1
            and generic_p3_run["record_write_count"] == 1
            and generic_p3_run["local_safe_execution_count"] == 0,
            "generic P3 run must stop after one boundary record without execution",
            failures,
        )
        check(
            generic_p3_run["stopped_reason"]
            == "governance_decision_required"
            and generic_p3_run["next_step"]["status"]
            == "governance_decision_required"
            and workbench.goal_state_for_next_step(
                generic_p3_run["next_step"]
            )
            == "waiting_at_boundary",
            "generic P3 run must preserve the Jenn governance boundary",
            failures,
        )
        check(
            generic_p3_run["active_queue_modified"] is False
            and generic_p3_run["queue_write_authorized"] is False
            and generic_p3_run["execution_authorized"] is False
            and generic_p3_run["provider_call_authorized"] is False
            and generic_p3_run["service_start_authorized"] is False
            and generic_p3_gate_queue_path.read_text(encoding="utf-8")
            == generic_p3_gate_queue_text,
            "generic P3 run must preserve queue bytes and all effect denials",
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
            route_promotion_status["status_reconciliation"][
                "next_action_source"
            ]
            == "live_queue"
            and route_promotion_status["status_reconciliation"][
                "record_boundary_may_be_stale"
            ]
            is False
            and route_promotion_status["matching_advance_record_count"] == 0,
            "route promotion status must ignore unrelated queue records",
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
        cli_governance_queue_path = Path(temp_dir) / "cli-governance-gate-queue.md"
        cli_governance_queue_text = fixture_governance_gate_queue_text()
        cli_governance_queue_path.write_text(cli_governance_queue_text, encoding="utf-8")
        cli_governance_preview = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "route-choice-preview",
                "--confirmation-text",
                route_choice_text,
                "--queue",
                str(cli_governance_queue_path),
                "--json",
            ],
            cwd=workbench.WORKSPACE_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        check(
            cli_governance_preview.returncode == 1,
            f"CLI active governance preview should fail closed: {cli_governance_preview.stderr}",
            failures,
        )
        if cli_governance_preview.stdout:
            cli_governance_preview_payload = json.loads(cli_governance_preview.stdout)
            check(
                cli_governance_preview_payload.get("active_jenn_governance_gate") is True,
                "CLI active governance preview should preserve the Jenn gate",
                failures,
            )
            check(
                cli_governance_preview_payload.get("bundle", {}).get("can_apply_with_separate_apply_gate") is False,
                "CLI active governance preview must not become apply-ready",
                failures,
            )
        else:
            failures.append("CLI active governance preview should emit JSON")
        cli_governance_apply = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "route-choice-apply-gate",
                "--confirmation-text",
                route_choice_text,
                "--queue",
                str(cli_governance_queue_path),
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
        check(
            cli_governance_apply.returncode == 1,
            f"CLI active governance apply should fail closed: {cli_governance_apply.stderr}",
            failures,
        )
        if cli_governance_apply.stdout:
            cli_governance_apply_payload = json.loads(cli_governance_apply.stdout)
            check(
                cli_governance_apply_payload.get("apply_gate", {}).get("queue_adoption_authorized") is False,
                "CLI active governance apply must not authorize queue adoption",
                failures,
            )
            check(
                cli_governance_apply_payload.get("write_performed") is False,
                "CLI active governance apply must not write",
                failures,
            )
        else:
            failures.append("CLI active governance apply should emit JSON")
        check(
            cli_governance_queue_path.read_text(encoding="utf-8") == cli_governance_queue_text,
            "CLI active governance apply must preserve exact queue bytes",
            failures,
        )
        cli_generic_p3_queue_path = Path(temp_dir) / "cli-generic-p3-governance-gate-queue.md"
        cli_generic_p3_queue_text = fixture_generic_p3_governance_gate_queue_text()
        cli_generic_p3_queue_path.write_text(cli_generic_p3_queue_text, encoding="utf-8")
        cli_generic_p3_apply = subprocess.run(
            [
                "python3",
                str(ROOT / "workbench.py"),
                "route-choice-apply-gate",
                "--confirmation-text",
                route_choice_text,
                "--queue",
                str(cli_generic_p3_queue_path),
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
        check(
            cli_generic_p3_apply.returncode == 1,
            f"CLI generic P3 governance apply should fail closed: {cli_generic_p3_apply.stderr}",
            failures,
        )
        if cli_generic_p3_apply.stdout:
            cli_generic_p3_payload = json.loads(cli_generic_p3_apply.stdout)
            check(
                cli_generic_p3_payload.get("active_jenn_governance_gate") is True
                and cli_generic_p3_payload.get("apply_gate", {}).get("queue_adoption_authorized") is False
                and cli_generic_p3_payload.get("write_performed") is False,
                "CLI generic P3 governance apply must preserve the gate and deny writes",
                failures,
            )
        else:
            failures.append("CLI generic P3 governance apply should emit JSON")
        check(
            cli_generic_p3_queue_path.read_text(encoding="utf-8") == cli_generic_p3_queue_text,
            "CLI generic P3 governance apply must preserve exact queue bytes",
            failures,
        )
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
                cli_live_status_payload.get(
                    "status_reconciliation",
                    {},
                ).get("next_action_source")
                == "live_queue"
                and cli_live_status_payload.get(
                    "status_reconciliation",
                    {},
                ).get("record_boundary_may_be_stale")
                is False
                and cli_live_status_payload.get(
                    "matching_advance_record_count"
                )
                == 0,
                "CLI live status must ignore unrelated queue records",
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
        check(
            "git_release_boundary" in workbench.queue_p3_signals("Publish report to GitHub release, not as force push"),
            "P3 scanner must not let unrelated not hide release boundary signals",
            failures,
        )
        p3_not_proposal = dict(p3_cycle["stages"]["intake_proposal"])
        p3_not_proposal["proposed_queue_item"] = dict(p3_not_proposal["proposed_queue_item"])
        p3_not_proposal["proposed_queue_item"]["title"] = "Publish report to GitHub release, not as force push"
        p3_not_review = workbench.accepted_nobao_review_for_intake(p3_not_proposal)
        blocked_p3_not_intake = workbench.reviewed_intake_apply_gate(
            p3_not_proposal,
            p3_not_review,
            p3_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        check(blocked_p3_not_intake["passed"] is False, "P3 intake with unrelated not should fail", failures)
        check(blocked_p3_not_intake["write_performed"] is False, "P3 intake with unrelated not must not write", failures)

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

    fast_validation = workbench.validate_workbench_by_level("fast")
    check(
        fast_validation["passed"] is True,
        f"workbench fast validation should pass: {fast_validation['errors']}",
        failures,
    )
    check(fast_validation["level"] == "fast", "workbench fast validation should report fast level", failures)
    check(
        fast_validation["next_step_selector"]["substantive_progress"] is True,
        "fast validation should cover substantive selector progress",
        failures,
    )
    check(
        fast_validation["codex_active_loop_import"]["passed"] is True,
        f"fast validation should cover codex active-loop import boundary: {fast_validation['codex_active_loop_import']['errors']}",
        failures,
    )
    check(
        "docctl status" in fast_validation["skipped_full_checks"],
        "fast validation should skip full docctl status",
        failures,
    )
    check(
        fast_validation["full_validation_required_before_external_write"] is True,
        "fast validation must require full validation before external write",
        failures,
    )
    failed_full_metadata = workbench.attach_validation_metadata(
        {"passed": False, "errors": ["fixture failure"]},
        "full",
        workbench.time.monotonic(),
        required_level="full",
    )
    check(
        failed_full_metadata["external_write_eligible"] is False,
        "failed full validation must not be external-write eligible",
        failures,
    )
    check(
        failed_full_metadata["release_eligible"] is False,
        "failed full validation must not be release eligible",
        failures,
    )

    validation: dict[str, object] = {}
    audit: dict[str, object] = {}
    if args.full:
        validation = workbench.validate_workbench()
        check(validation["passed"] is True, f"workbench validation should pass: {validation['errors']}", failures)
        check(validation["temporary_fixture_cleaned"] is True, "workbench validation should clean temporary fixture", failures)
        check(
            validation["docctl_release_gate"]["required_before_external_write"] is True,
            "workbench validation should keep docctl as external-write release gate",
            failures,
        )
        if validation["docctl_release_gate"]["passed"] is not True:
            check(
                validation["external_write_eligible"] is False,
                "docctl release gate failure must block external-write eligibility",
                failures,
            )
            check(
                validation["release_eligible"] is False,
                "docctl release gate failure must block release eligibility",
                failures,
            )
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
        audit = workbench.build_completion_audit(validation_result=validation)
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
        print(f"cases={25 if args.full else 18} failures={len(failures)} mode={'full' if args.full else 'fast'}")
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
    print("PASS workbench route transaction truthfulness fixture")
    print("PASS workbench unresolved transaction cleanup reconciliation fixture")
    print("PASS active Jenn governance preview fixtures")
    print("PASS active Jenn governance apply fixtures")
    print("PASS generic P3 Jenn governance Workbench fixtures")
    print("PASS workbench queue promotion apply gate fixtures")
    print("PASS workbench continue current fixtures")
    print("PASS workbench continue loop fixtures")
    print("PASS workbench next-step selector fixtures")
    print("PASS workbench fast validation")
    if args.full:
        print("PASS workbench validation")
        print("PASS workbench completion audit")
    print(f"cases={25 if args.full else 18} failures=0 mode={'full' if args.full else 'fast'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
