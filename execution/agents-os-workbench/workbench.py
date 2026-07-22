#!/usr/bin/env python3
"""AGENTS OS preview-first workbench loop.

The workbench connects the existing Task Producer, Machine, Control Chain, and
Dashboard into one local cycle:

idea -> task -> queue -> intake proposal -> judgment -> track preview
-> validation -> queue proposal -> dashboard -> record -> next step

It keeps queue mutation, promotion, provider calls, service starts, runtime or
plugin activation, external writes, and formal Memory writes disabled.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any


WORKBENCH_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = WORKBENCH_DIR.parents[1]
PRODUCER_PATH = WORKSPACE_ROOT / "execution" / "agents-os-task-producer" / "producer.py"
MACHINE_PATH = WORKSPACE_ROOT / "execution" / "agents-os-machine" / "machine.py"
CONTROL_CHAIN_PATH = WORKSPACE_ROOT / "execution" / "agents-os-control-chain" / "control_chain.py"
DASHBOARD_PATH = WORKSPACE_ROOT / "execution" / "agents-os-dashboard" / "dashboard.py"
MANIFEST_PATH = WORKBENCH_DIR / "workbench-manifest.json"
DEFAULT_QUEUE = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-22-agents-os-active-work-queue-v14.2.md"
DEFAULT_ROUTE_SELECTION_PACKAGE = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-07-agents-os-next-route-selection-package-v0.1.md"
DEFAULT_VALIDATION_COMMAND = "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status"
DEFAULT_RECORD_ROOT = WORKBENCH_DIR / "records"
CODEX_ACTIVE_LOOP_ROOT = WORKSPACE_ROOT / "execution" / "codex-appserver-active-loop"
VALIDATION_LEVELS = ("fast", "targeted", "full")


def workspace_relative(path: Path) -> str:
    try:
        return str(path.relative_to(WORKSPACE_ROOT))
    except ValueError:
        return str(path)


VALIDATION_INPUT_PATHS = (
    MANIFEST_PATH,
    WORKBENCH_DIR / "workbench.py",
    WORKBENCH_DIR / "test-workbench.py",
    CODEX_ACTIVE_LOOP_ROOT / "BOUNDARY.md",
    CODEX_ACTIVE_LOOP_ROOT / "WORKBENCH_INTEGRATION.md",
    CODEX_ACTIVE_LOOP_ROOT / "schemas" / "agents-os" / "active-loop-receipt.v0.1.schema.json",
)


def validation_input_hash(paths: tuple[Path, ...] = VALIDATION_INPUT_PATHS) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: workspace_relative(item)):
        digest.update(workspace_relative(path).encode("utf-8"))
        digest.update(b"\0")
        if path.is_file():
            digest.update(path.read_bytes())
        else:
            digest.update(b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


def validation_commands_for_level(level: str) -> list[str]:
    try:
        commands = load_json(MANIFEST_PATH).get("validation_commands", [])
    except Exception:
        commands = []
    if level == "fast":
        return [command for command in commands if "--level fast" in command or "test-workbench.py" in command and "--full" not in command]
    if level == "targeted":
        return [command for command in commands if "--level targeted" in command]
    if level == "full":
        return [command for command in commands if "workbench.py validate" in command and "--level" not in command or "--full" in command or "workbench.py audit" in command]
    return []


def validation_eligibility(level: str) -> dict[str, bool]:
    return {
        "ordinary_progress_eligible": level in {"fast", "targeted", "full"},
        "boundary_eligible": level in {"targeted", "full"},
        "external_write_eligible": level == "full",
        "release_eligible": level == "full",
        "full_validation_required_before_external_write": level != "full",
    }


def attach_validation_metadata(
    result: dict[str, Any],
    level: str,
    started_at: float,
    *,
    required_level: str | None = None,
) -> dict[str, Any]:
    required = required_level or level
    result["level"] = level
    result["validation_level"] = level
    result["required_level"] = required
    result["actual_level"] = level
    result["duration_seconds"] = round(time.monotonic() - started_at, 3)
    result["input_hash"] = validation_input_hash()
    result["validation_commands"] = validation_commands_for_level(level)
    result["eligibility"] = validation_eligibility(level)
    result.update(validation_eligibility(level))
    if result.get("passed") is not True:
        result["external_write_eligible"] = False
        result["release_eligible"] = False
        eligibility = dict(result.get("eligibility", {}))
        eligibility["external_write_eligible"] = False
        eligibility["release_eligible"] = False
        result["eligibility"] = eligibility
    return result


def apply_docctl_release_gate(result: dict[str, Any], docctl_probe: dict[str, Any]) -> dict[str, Any]:
    blocked = docctl_probe.get("passed") is not True
    result["docctl_release_gate"] = {
        "required_before_external_write": True,
        "passed": not blocked,
        "blocked": blocked,
        "probe_returncode": docctl_probe.get("returncode"),
        "probe_command": docctl_probe.get("command"),
        "raw_output_included": False,
    }
    result["release_blocked_by_docctl"] = blocked
    if blocked:
        result["external_write_eligible"] = False
        result["release_eligible"] = False
        eligibility = dict(result.get("eligibility", {}))
        eligibility["external_write_eligible"] = False
        eligibility["release_eligible"] = False
        result["eligibility"] = eligibility
    return result

NEGATED_SIGNAL_CONTEXT = re.compile(
    r"\b(no|do not|does not|cannot|can't|must not|blocked actions?|blocked until|forbidden|denied)\b",
    re.I,
)
EXTERNAL_GIT_NEGATED_SIGNAL_CONTEXT = re.compile(
    r"\b(no|not|do not|does not|cannot|can't|must not|blocked actions?|blocked until|forbidden|denied)\b",
    re.I,
)
QUEUE_P3_PATTERNS = {
    "provider_call": re.compile(r"\b(call|invoke|use|run)\s+(a\s+)?provider\b", re.I),
    "service_start": re.compile(r"\b(start|launch|run)\s+(a\s+)?service\b", re.I),
    "executor_run": re.compile(r"\b(run|start|launch)\s+(the\s+)?executor\b", re.I),
    "external_write": re.compile(r"\b(write|post|send|upload|publish)\s+(to\s+)?(notion|github|email|mail|slack|discord|external)\b", re.I),
    "memory_write": re.compile(r"\b(write|update|register)\s+(formal\s+)?memory\b", re.I),
    "runtime_plugin_activation": re.compile(r"\bactivate\s+(plugin|runtime|vcptoolbox|colameta)\b", re.I),
    "state_private": re.compile(r"\bstate-private/", re.I),
    "auth_or_secret_config": re.compile(r"\b(auth|token|cookie|session|credential|secret|provider config|runtime config)\b", re.I),
    "git_release_boundary": re.compile(r"\b(git push|git tag|force push|release|deploy|publish|history rewrite|npm publish|package publish)\b", re.I),
}

DANGEROUS_AUTHORIZATION_FLAGS = (
    "provider_call_authorized",
    "service_start_authorized",
    "executor_run_authorized",
    "external_write_authorized",
    "memory_write_authorized",
    "runtime_plugin_activation_authorized",
    "active_queue_mutation_authorized",
    "queue_promotion_authorized",
    "route_auto_selection_authorized",
)


def import_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return str(path)


def stable_id(prefix: str, payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(encoded).hexdigest()[:10].upper()}"


def authorization_defaults() -> dict[str, bool]:
    return {flag: False for flag in DANGEROUS_AUTHORIZATION_FLAGS}


def false_flag_failures(value: dict[str, Any]) -> list[str]:
    return [flag for flag in DANGEROUS_AUTHORIZATION_FLAGS if value.get(flag) is not False]


def compact_errors(*values: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for value in values:
        if value.get("passed") is False:
            errors.extend(str(item) for item in value.get("errors", []) if item)
            errors.extend(str(item) for item in value.get("parse_errors", []) if item)
    return errors


def summarize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "proposed_lane": candidate.get("proposed_lane"),
        "blocked": candidate.get("blocked"),
        "risk_signals": candidate.get("risk_signals", []),
        "requires_nobao_review": candidate.get("review_gate", {}).get("requires_nobao_review"),
        "requires_jenn_decision": candidate.get("review_gate", {}).get("requires_jenn_decision"),
        "execution_authorized": candidate.get("execution_effect", {}).get("execution_authorized"),
    }


def summarize_machine_preview(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_item": preview.get("source_item", {}),
        "blocked": preview.get("blocked"),
        "actionable": preview.get("actionable"),
        "denied_signals": preview.get("denied_signals", []),
        "next_user_action_status": preview.get("next_user_action", {}).get("status"),
        "next_user_action": summarize_next_user_action(preview.get("next_user_action", {})),
        "requires_jenn_decision": preview.get("review_gate", {}).get("requires_jenn_decision"),
        "execution_authorized": preview.get("execution_authorized"),
    }


def summarize_next_user_action(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": action.get("status"),
        "decision_owner": action.get("decision_owner"),
        "requires_jenn_decision": action.get("requires_jenn_decision"),
        "instruction": action.get("instruction"),
        "accepted_route_ids": action.get("accepted_route_ids", []),
        "template_source_path": action.get("template_source_path"),
        "exact_confirmation_templates_available": action.get("exact_confirmation_templates_available"),
        "route_auto_selection_authorized": action.get("route_auto_selection_authorized"),
        "active_queue_mutation_authorized": action.get("active_queue_mutation_authorized"),
        "queue_promotion_authorized": action.get("queue_promotion_authorized"),
        "execution_authorized": action.get("execution_authorized"),
        "write_performed": action.get("write_performed"),
        "raw_content_output": action.get("raw_content_output"),
    }


def normalized_task_title(value: str) -> str:
    lowered = re.sub(r"\bv\d+(?:\.\d+)*\b", " ", value.lower())
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    stop_words = {"a", "agents", "an", "and", "closed", "for", "gate", "now", "os", "the", "to", "v"}
    return " ".join(token for token in lowered.split() if token and token not in stop_words)


def title_is_repeat(candidate_title: str, existing_titles: list[str]) -> bool:
    candidate = normalized_task_title(candidate_title)
    if not candidate:
        return True
    candidate_tokens = set(candidate.split())
    for title in existing_titles:
        existing = normalized_task_title(title)
        if not existing:
            continue
        if candidate == existing:
            return True
        existing_tokens = set(existing.split())
        if candidate_tokens and candidate_tokens.issubset(existing_tokens):
            return True
        if existing_tokens and existing_tokens.issubset(candidate_tokens) and len(existing_tokens) >= 4:
            return True
    return False


def queue_closed_titles(queue_text: str) -> list[str]:
    in_closed = False
    titles: list[str] = []
    for line in queue_text.splitlines():
        stripped = line.strip()
        if stripped == "## CLOSED":
            in_closed = True
            continue
        if in_closed and line.startswith("## "):
            break
        if not in_closed or not stripped or stripped.startswith("```"):
            continue
        if ":" in stripped:
            titles.append(stripped.split(":", 1)[0])
        titles.extend(re.findall(r'"([^"]+)"', stripped))
    return titles


def line_has_non_negated_signal(line: str, pattern: re.Pattern[str]) -> bool:
    return bool(pattern.search(line)) and not NEGATED_SIGNAL_CONTEXT.search(line)


def external_git_match_is_negated(line: str, match: re.Match[str]) -> bool:
    prefix = line[: match.start()]
    clause_prefix = re.split(r"[,.;:]", prefix)[-1]
    return bool(EXTERNAL_GIT_NEGATED_SIGNAL_CONTEXT.search(clause_prefix))


def external_git_line_has_non_negated_signal(line: str, pattern: re.Pattern[str]) -> bool:
    return any(not external_git_match_is_negated(line, match) for match in pattern.finditer(line))


def external_git_has_post_push_evidence(queue_text: str) -> bool:
    patterns = (
        re.compile(r"\b(pushed|push completed|branch pushed|published remote branch)\b", re.I),
        re.compile(r"\bremote branch\s+(exists|created|published|available|verified)\b", re.I),
        re.compile(r"\b(PR|pull request)\s*#?\d+\b", re.I),
        re.compile(r"\bopened\s+(a\s+)?(draft\s+)?(PR|pull request)\b", re.I),
    )
    return any(
        external_git_line_has_non_negated_signal(line, pattern)
        for line in queue_text.splitlines()
        for pattern in patterns
    )


def external_git_published_branch_ref(queue_text: str) -> str | None:
    branch_name = r"(?P<branch>[A-Za-z0-9][A-Za-z0-9._/-]*)"
    patterns = (
        re.compile(rf"\bremote branch\s+(?:exists|created|published|available|verified)\s*:?\s*(?:origin/|refs/heads/)?{branch_name}\b", re.I),
        re.compile(rf"\bpublished remote branch\s*:?\s*(?:origin/|refs/heads/)?{branch_name}\b", re.I),
        re.compile(rf"\bbranch pushed\s+(?:to\s+origin\s+)?(?:as\s+)?(?:origin/|refs/heads/)?{branch_name}\b", re.I),
        re.compile(rf"\bpushed\s+(?:branch\s+)?(?:to\s+origin\s+)?(?:as\s+)?(?:origin/|refs/heads/)?{branch_name}\b", re.I),
    )
    non_branch_words = {"and", "as", "branch", "created", "draft", "opened", "origin", "pr", "published", "remote", "to", "verified"}
    for line in queue_text.splitlines():
        for pattern in patterns:
            for match in pattern.finditer(line):
                if external_git_match_is_negated(line, match):
                    continue
                branch = match.group("branch").strip(".,;:)")
                if branch.lower() in non_branch_words:
                    continue
                return f"refs/heads/{branch.removeprefix('refs/heads/').removeprefix('origin/')}"
    return None


def validate_next_user_action_summary(prefix: str, action: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if action.get("status") == "route_choice_required":
        for flag in (
            "route_auto_selection_authorized",
            "active_queue_mutation_authorized",
            "queue_promotion_authorized",
            "execution_authorized",
            "write_performed",
            "raw_content_output",
        ):
            if action.get(flag) is not False:
                errors.append(f"{prefix} next user action must keep {flag}=false")
        if action.get("decision_owner") != "Jenn":
            errors.append(f"{prefix} route choice owner must be Jenn")
        if action.get("requires_jenn_decision") is not True:
            errors.append(f"{prefix} route choice must require Jenn decision")
        if not action.get("accepted_route_ids"):
            errors.append(f"{prefix} route choice must include accepted_route_ids")
        if action.get("exact_confirmation_templates_available") is not True:
            errors.append(f"{prefix} route choice must expose confirmation template availability")
    return errors


def build_route_choice_readiness(next_step: dict[str, Any]) -> dict[str, Any]:
    """Summarize Jenn route-choice options without selecting or printing templates."""
    if next_step.get("status") != "route_choice_required":
        return {
            "schema_version": "agents-os.workbench.route-choice-readiness.v0.1",
            "present": False,
            "status": next_step.get("status"),
            "raw_template_output": False,
            "confirmation_text_included": False,
            "route_auto_selection_authorized": False,
            "active_queue_mutation_authorized": False,
            "queue_promotion_authorized": False,
            "execution_authorized": False,
            "write_performed": False,
            "errors": [],
            "passed": True,
        }

    producer = import_module(PRODUCER_PATH, "agents_os_task_producer_route_readiness_for_workbench")
    template_path_value = next_step.get("template_source_path") or rel(DEFAULT_ROUTE_SELECTION_PACKAGE)
    template_path = Path(template_path_value)
    source = template_path if template_path.is_absolute() else WORKSPACE_ROOT / template_path
    accepted_route_ids = [str(item) for item in next_step.get("accepted_route_ids", [])]
    errors: list[str] = []
    options: list[dict[str, Any]] = []
    template_coverage: dict[str, Any] = {}
    try:
        text = source.read_text(encoding="utf-8")
        parsed_options = producer.parse_route_options(text)
        for option_id in accepted_route_ids:
            parsed = parsed_options.get(option_id, {})
            options.append(
                {
                    "option_id": option_id,
                    "title": parsed.get("title"),
                    "first_safe_package": parsed.get("first_safe_package"),
                    "must_keep_count": len(parsed.get("must_keep", [])),
                }
            )
        template_coverage = producer.route_choice_template_coverage(source)
        coverage_errors = producer.validate_route_choice_template_coverage(template_coverage)
        errors.extend(f"template coverage: {error}" for error in coverage_errors)
    except OSError as exc:
        errors.append(f"route choice package read failed: {exc}")
    except Exception as exc:  # pragma: no cover - surfaced as validation error
        errors.append(f"route choice readiness failed: {exc}")

    result = {
        "schema_version": "agents-os.workbench.route-choice-readiness.v0.1",
        "present": True,
        "status": "route_choice_required",
        "decision_owner": next_step.get("decision_owner") or next_step.get("owner"),
        "requires_jenn_decision": next_step.get("requires_jenn_decision"),
        "instruction": next_step.get("instruction"),
        "accepted_route_ids": accepted_route_ids,
        "option_count": len(options),
        "options": options,
        "template_source_path": rel(source),
        "exact_confirmation_templates_available": next_step.get("exact_confirmation_templates_available"),
        "template_coverage_passed": template_coverage.get("passed") if template_coverage else None,
        "template_coverage_parsed_route_ids": template_coverage.get("parsed_route_ids", []),
        "template_e_placeholder_blocked": template_coverage.get("placeholder_goal_blocked") if template_coverage else None,
        "template_e_concrete_fixture_passed": template_coverage.get("concrete_new_route_fixture_passed") if template_coverage else None,
        "confirmation_text_included": False,
        "raw_confirmation_text_output": False,
        "raw_template_output": False,
        "route_selected": False,
        "route_auto_selection_authorized": False,
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
        "next_required_input": "Jenn sends one exact route confirmation text from the template source",
        "next_preview_command_shape": "python3 execution/agents-os-task-producer/producer.py route-choice-preview --confirmation-text '<Jenn exact route confirmation text>' --json",
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_route_choice_readiness(result)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_route_choice_readiness(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.route-choice-readiness.v0.1":
        errors.append("route choice readiness schema_version is invalid")
    for flag in (
        "confirmation_text_included",
        "raw_template_output",
        "route_auto_selection_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "write_performed",
    ):
        if result.get(flag) is not False:
            errors.append(f"route choice readiness must keep {flag}=false")
    if result.get("present") is True:
        if result.get("status") != "route_choice_required":
            errors.append("route choice readiness present requires route_choice_required status")
        if result.get("decision_owner") != "Jenn":
            errors.append("route choice readiness owner must be Jenn")
        if result.get("requires_jenn_decision") is not True:
            errors.append("route choice readiness must require Jenn decision")
        if result.get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
            errors.append("route choice readiness accepted_route_ids must be A-E")
        if result.get("option_count") != 5:
            errors.append("route choice readiness option_count must be 5")
        if result.get("template_coverage_passed") is not True:
            errors.append("route choice readiness template coverage must pass")
        if result.get("template_coverage_parsed_route_ids") != ["A", "B", "C", "D", "E"]:
            errors.append("route choice readiness parsed route ids must be A-E")
        if result.get("exact_confirmation_templates_available") is not True:
            errors.append("route choice readiness must expose confirmation template availability")
        for option in result.get("options", []):
            if option.get("option_id") not in ["A", "B", "C", "D", "E"]:
                errors.append(f"route choice readiness invalid option id: {option.get('option_id')}")
            if not option.get("title"):
                errors.append(f"route choice readiness option {option.get('option_id')} missing title")
            if not option.get("first_safe_package"):
                errors.append(f"route choice readiness option {option.get('option_id')} missing first safe package")
    return errors


def build_route_choice_preview(
    confirmation_text: str,
    queue_path: Path = DEFAULT_QUEUE,
    *,
    source: Path = DEFAULT_ROUTE_SELECTION_PACKAGE,
) -> dict[str, Any]:
    """Preview a Jenn route confirmation through the Workbench boundary."""
    chain = import_module(CONTROL_CHAIN_PATH, "agents_os_control_chain_route_preview_for_workbench")
    bundle = chain.route_choice_adoption_bundle_preview(
        confirmation_text,
        queue_path,
        source,
    )
    errors = []
    if bundle.get("passed") is not True:
        errors.extend(f"bundle: {error}" for error in bundle.get("errors", []))
    result = {
        "schema_version": "agents-os.workbench.route-choice-preview.v0.1",
        "mode": "route_choice_confirmation_preview",
        "preview_only": True,
        "source": {
            "confirmation_text_character_count": len(confirmation_text),
            "confirmation_text_included": False,
            "route_selection_package": rel(source if source.is_absolute() else WORKSPACE_ROOT / source),
            "queue_path": rel(queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path),
        },
        "bundle": {
            "schema_version": bundle.get("schema_version"),
            "passed": bundle.get("passed"),
            "selected_route_id": bundle.get("selected_route_id"),
            "selected_route_title": bundle.get("selected_route_title"),
            "selected_first_safe_package": bundle.get("selected_first_safe_package"),
            "route_goal_present": bundle.get("route_goal_present"),
            "queue_proposal_passed": bundle.get("queue_proposal_passed"),
            "proposal_id": bundle.get("proposal_id"),
            "proposed_next_title": bundle.get("proposed_next_title"),
            "review_status": bundle.get("review_status"),
            "reviewer": bundle.get("reviewer"),
            "reviewed_route_adoption_preview_passed": bundle.get("reviewed_route_adoption_preview_passed"),
            "reviewed_route_adoption_apply_preview_passed": bundle.get("reviewed_route_adoption_apply_preview_passed"),
            "can_apply_with_separate_apply_gate": bundle.get("can_apply_with_separate_apply_gate"),
            "next_required_gate": bundle.get("next_required_gate"),
        },
        "confirmation_text_included": False,
        "raw_confirmation_text_output": False,
        "raw_template_output": False,
        "route_selected": False,
        "workspace_route_state_modified": False,
        "active_queue_modified": False,
        "write_performed": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "route_adoption_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "executor_run_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "next_step": {
            "status": "review_route_choice_adoption_bundle",
            "owner": "Nobao",
            "selected_route_id": bundle.get("selected_route_id"),
            "instruction": bundle.get("next_required_gate"),
            "active_queue_mutation_authorized": False,
            "queue_promotion_authorized": False,
            "execution_authorized": False,
            "write_performed": False,
        },
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_workbench_route_choice_preview(result)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_workbench_route_choice_preview(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.route-choice-preview.v0.1":
        errors.append("workbench route choice preview schema_version is invalid")
    if result.get("mode") != "route_choice_confirmation_preview":
        errors.append("workbench route choice preview mode is invalid")
    if result.get("preview_only") is not True:
        errors.append("workbench route choice preview must be preview_only")
    if result.get("source", {}).get("confirmation_text_included") is not False:
        errors.append("workbench route choice preview must not include confirmation text in source")
    for flag in (
        "confirmation_text_included",
        "raw_confirmation_text_output",
        "raw_template_output",
        "route_selected",
        "workspace_route_state_modified",
        "active_queue_modified",
        "write_performed",
        "queue_write_authorized",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "route_adoption_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "executor_run_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
    ):
        if result.get(flag) is not False:
            errors.append(f"workbench route choice preview must keep {flag}=false")
    bundle = result.get("bundle", {})
    if not result.get("errors"):
        if bundle.get("passed") is not True:
            errors.append("workbench route choice preview requires passing bundle")
        if bundle.get("selected_route_id") not in ["A", "B", "C", "D", "E"]:
            errors.append("workbench route choice preview selected_route_id must be A-E")
        if not bundle.get("selected_first_safe_package"):
            errors.append("workbench route choice preview must include first safe package")
        if bundle.get("queue_proposal_passed") is not True:
            errors.append("workbench route choice preview requires queue proposal")
        if bundle.get("reviewed_route_adoption_preview_passed") is not True:
            errors.append("workbench route choice preview requires adoption preview")
        if bundle.get("reviewed_route_adoption_apply_preview_passed") is not True:
            errors.append("workbench route choice preview requires apply preview")
        if bundle.get("can_apply_with_separate_apply_gate") is not True:
            errors.append("workbench route choice preview must surface separate apply gate readiness")
    if not result.get("next_step", {}).get("status"):
        errors.append("workbench route choice preview must emit next_step.status")
    return errors


def build_route_choice_apply_gate(
    confirmation_text: str,
    queue_path: Path = DEFAULT_QUEUE,
    *,
    source: Path = DEFAULT_ROUTE_SELECTION_PACKAGE,
    apply: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    """Apply, or preview applying, a reviewed route choice into a queue."""
    producer = import_module(PRODUCER_PATH, "agents_os_task_producer_route_apply_for_workbench")
    chain = import_module(CONTROL_CHAIN_PATH, "agents_os_control_chain_route_apply_for_workbench")
    errors: list[str] = []
    resolved_queue, path_error = resolve_queue_apply_path(queue_path, allowed_queue_root)
    if path_error or resolved_queue is None:
        errors.append(path_error or "queue path is not allowed")

    route_preview = producer.route_choice_preview(confirmation_text, source)
    route_preview_errors = chain.validate_route_choice_preview(route_preview)
    errors.extend(f"route choice preview: {error}" for error in route_preview_errors)
    proposal = chain.route_choice_queue_proposal(route_preview)
    errors.extend(f"route choice proposal: {error}" for error in proposal.get("errors", []))
    review = chain.accepted_nobao_review_for(proposal)

    apply_gate: dict[str, Any] = {
        "schema_version": "agents-os.queue-manager.reviewed-route-adoption-apply-gate.v0.1",
        "passed": False,
        "preview_only": not apply,
        "queue_adoption_authorized": False,
        "route_adoption_authorized": False,
        "active_queue_modified": False,
        "write_performed": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "mutation": {},
        "errors": [],
    }
    if not errors and resolved_queue is not None:
        apply_gate = chain.reviewed_route_adoption_apply_gate(
            proposal,
            review,
            resolved_queue,
            apply=apply,
        )
        errors.extend(f"apply gate: {error}" for error in apply_gate.get("errors", []))

    selected = route_preview.get("selected_option", {}) if isinstance(route_preview, dict) else {}
    mutation = apply_gate.get("mutation", {})
    result = {
        "schema_version": "agents-os.workbench.route-choice-apply-gate.v0.1",
        "mode": "route_choice_reviewed_apply_gate",
        "preview_only": not apply,
        "source": {
            "confirmation_text_character_count": len(confirmation_text),
            "confirmation_text_included": False,
            "route_selection_package": rel(source if source.is_absolute() else WORKSPACE_ROOT / source),
            "queue_path": rel(resolved_queue) if resolved_queue is not None else str(queue_path),
            "allowed_queue_root": rel(allowed_queue_root if allowed_queue_root.is_absolute() else WORKSPACE_ROOT / allowed_queue_root),
        },
        "route": {
            "selected_route_id": selected.get("option_id"),
            "selected_route_title": selected.get("title"),
            "selected_first_safe_package": selected.get("first_safe_package"),
            "route_goal_present": bool(selected.get("route_goal")),
        },
        "proposal": {
            "proposal_id": proposal.get("proposal_id"),
            "passed": proposal.get("passed"),
            "proposed_next_title": proposal.get("proposed_queue_item", {}).get("title"),
            "requires_nobao_review": proposal.get("requires_nobao_review"),
            "requires_jenn_decision": proposal.get("requires_jenn_decision"),
        },
        "review": {
            "review_status": review.get("review_status"),
            "reviewer": review.get("reviewer"),
            "requires_jenn_decision": review.get("requires_jenn_decision"),
        },
        "apply_gate": {
            "schema_version": apply_gate.get("schema_version"),
            "passed": apply_gate.get("passed"),
            "preview_only": apply_gate.get("preview_only"),
            "queue_adoption_authorized": apply_gate.get("queue_adoption_authorized"),
            "route_adoption_authorized": apply_gate.get("route_adoption_authorized"),
            "no_p3_route_adoption_guard": apply_gate.get("no_p3_route_adoption_guard"),
            "appended_next_id": mutation.get("appended_next_id"),
            "appended_next_title": mutation.get("appended_next_title"),
            "next_count_before": mutation.get("next_count_before"),
            "next_count_after": mutation.get("next_count_after"),
            "left_now_unchanged": mutation.get("left_now_unchanged"),
            "promoted_now": mutation.get("promoted_now"),
        },
        "confirmation_text_included": False,
        "raw_confirmation_text_output": False,
        "raw_template_output": False,
        "route_auto_selection_authorized": False,
        "workspace_route_state_modified": apply_gate.get("workspace_route_state_modified") is True,
        "active_queue_modified": apply_gate.get("active_queue_modified") is True,
        "write_performed": apply_gate.get("write_performed") is True,
        "queue_write_authorized": apply_gate.get("queue_write_authorized") is True,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "executor_run_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "next_step": {
            "status": "route_adoption_applied_review_queue_promotion" if apply_gate.get("write_performed") is True else "review_route_choice_apply_gate",
            "owner": "Nobao",
            "selected_route_id": selected.get("option_id"),
            "instruction": "review NEXT-to-NOW promotion gate for the updated queue"
            if apply_gate.get("write_performed") is True
            else "review route choice apply gate before --apply",
            "active_queue_mutation_authorized": apply_gate.get("write_performed") is True,
            "queue_promotion_authorized": False,
            "execution_authorized": False,
            "write_performed": apply_gate.get("write_performed") is True,
        },
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_workbench_route_choice_apply_gate(result, apply=apply)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_workbench_route_choice_apply_gate(result: dict[str, Any], *, apply: bool) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.route-choice-apply-gate.v0.1":
        errors.append("workbench route choice apply gate schema_version is invalid")
    if result.get("mode") != "route_choice_reviewed_apply_gate":
        errors.append("workbench route choice apply gate mode is invalid")
    if result.get("preview_only") is not (not apply):
        errors.append("workbench route choice apply gate preview_only does not match apply mode")
    if result.get("confirmation_text_included") is not False:
        errors.append("workbench route choice apply gate must not include confirmation text")
    if result.get("raw_confirmation_text_output") is not False:
        errors.append("workbench route choice apply gate must not output raw confirmation text")
    if result.get("raw_template_output") is not False:
        errors.append("workbench route choice apply gate must not output raw template")
    for flag in (
        "route_auto_selection_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "executor_run_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
    ):
        if result.get(flag) is not False:
            errors.append(f"workbench route choice apply gate must keep {flag}=false")
    if not apply:
        for flag in ("workspace_route_state_modified", "active_queue_modified", "write_performed", "queue_write_authorized"):
            if result.get(flag) is not False:
                errors.append(f"preview route choice apply gate must keep {flag}=false")
    if apply:
        for flag in ("workspace_route_state_modified", "active_queue_modified", "write_performed", "queue_write_authorized"):
            if result.get(flag) is not True:
                errors.append(f"applied route choice apply gate must set {flag}=true")
    route = result.get("route", {})
    if not result.get("errors"):
        if route.get("selected_route_id") not in ["A", "B", "C", "D", "E"]:
            errors.append("workbench route choice apply gate selected_route_id must be A-E")
        if not route.get("selected_first_safe_package"):
            errors.append("workbench route choice apply gate must include first safe package")
        if result.get("proposal", {}).get("passed") is not True:
            errors.append("workbench route choice apply gate requires passed proposal")
        if result.get("review", {}).get("review_status") != "accepted":
            errors.append("workbench route choice apply gate requires accepted review")
        apply_gate = result.get("apply_gate", {})
        if apply_gate.get("passed") is not True:
            errors.append("workbench route choice apply gate requires passed apply gate")
        if apply_gate.get("queue_adoption_authorized") is not True:
            errors.append("workbench route choice apply gate requires queue adoption authorization")
        if apply_gate.get("promoted_now") is not False:
            errors.append("workbench route choice apply gate must not promote NOW")
        if apply_gate.get("left_now_unchanged") is not True:
            errors.append("workbench route choice apply gate must leave NOW unchanged")
    if not result.get("next_step", {}).get("status"):
        errors.append("workbench route choice apply gate must emit next_step.status")
    return errors


def build_queue_promotion_apply_gate(
    queue_path: Path = DEFAULT_QUEUE,
    *,
    apply: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    """Preview or apply the reviewed NEXT-to-NOW promotion gate."""
    chain = import_module(CONTROL_CHAIN_PATH, "agents_os_control_chain_queue_promotion_for_workbench")
    errors: list[str] = []
    resolved_queue, path_error = resolve_queue_apply_path(queue_path, allowed_queue_root)
    if path_error or resolved_queue is None:
        errors.append(path_error or "queue path is not allowed")

    now_count: int | None = None
    next_count: int | None = None
    current_now_title: str | None = None
    promote_next_title: str | None = None
    if resolved_queue is not None:
        queue_text = resolved_queue.read_text(encoding="utf-8")
        now_blocks = chain.queue_lane_blocks(queue_text, "NOW")
        next_blocks = chain.queue_lane_blocks(queue_text, "NEXT")
        now_count = len(now_blocks)
        next_count = len(next_blocks)
        current_now_title = now_blocks[0].get("title") if now_blocks else None
        promote_next_title = next_blocks[0].get("title") if next_blocks else None

    proposal = {
        "schema_version": "agents-os.queue-manager.proposal.v0.1",
        "proposal_id": stable_id(
            "QUEUEPROMOTIONPROPOSAL",
            [
                rel(resolved_queue) if resolved_queue is not None else str(queue_path),
                current_now_title,
                promote_next_title,
                apply,
            ],
        ),
        "source_track_result_id": "workbench-reviewed-next-promotion",
        "proposal_only": True,
        "active_queue_modified": False,
        "write_performed": False,
        "close_current_now": True,
        "promote_next_title": promote_next_title,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "blocked_reason": None if promote_next_title else "no NEXT item available to promote",
        "errors": [],
    }
    proposal_errors = chain.validate_queue_proposal(proposal)
    proposal["passed"] = not proposal_errors
    proposal["errors"] = proposal_errors
    errors.extend(f"proposal: {error}" for error in proposal_errors)
    review = chain.accepted_nobao_review_for(proposal)

    mutation_gate: dict[str, Any] = {
        "schema_version": "agents-os.queue-manager.reviewed-mutation.v0.1",
        "passed": False,
        "preview_only": not apply,
        "queue_mutation_authorized": False,
        "active_queue_modified": False,
        "write_performed": False,
        "auto_promote_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "no_p3_auto_promote_guard": False,
        "mutation": {},
        "errors": [],
    }
    if not errors and resolved_queue is not None:
        mutation_gate = chain.reviewed_queue_mutation(
            proposal,
            review,
            resolved_queue,
            apply=apply,
        )
        errors.extend(f"mutation gate: {error}" for error in mutation_gate.get("errors", []))

    mutation = mutation_gate.get("mutation", {})
    result = {
        "schema_version": "agents-os.workbench.queue-promotion-apply-gate.v0.1",
        "mode": "reviewed_next_to_now_promotion_gate",
        "preview_only": not apply,
        "source": {
            "queue_path": rel(resolved_queue) if resolved_queue is not None else str(queue_path),
            "allowed_queue_root": rel(allowed_queue_root if allowed_queue_root.is_absolute() else WORKSPACE_ROOT / allowed_queue_root),
        },
        "queue_before": {
            "now_count": now_count,
            "next_count": next_count,
            "current_now_title": current_now_title,
            "promote_next_title": promote_next_title,
        },
        "proposal": {
            "proposal_id": proposal.get("proposal_id"),
            "passed": proposal.get("passed"),
            "close_current_now": proposal.get("close_current_now"),
            "promote_next_title": proposal.get("promote_next_title"),
            "requires_nobao_review": proposal.get("requires_nobao_review"),
            "requires_jenn_decision": proposal.get("requires_jenn_decision"),
        },
        "review": {
            "review_status": review.get("review_status"),
            "reviewer": review.get("reviewer"),
            "requires_jenn_decision": review.get("requires_jenn_decision"),
        },
        "mutation_gate": {
            "schema_version": mutation_gate.get("schema_version"),
            "passed": mutation_gate.get("passed"),
            "preview_only": mutation_gate.get("preview_only"),
            "queue_mutation_authorized": mutation_gate.get("queue_mutation_authorized"),
            "no_p3_auto_promote_guard": mutation_gate.get("no_p3_auto_promote_guard"),
            "closed_now_title": mutation.get("closed_now_title"),
            "promoted_now_title": mutation.get("promoted_now_title"),
            "exactly_one_now_before": mutation.get("exactly_one_now_before"),
            "exactly_one_now_after": mutation.get("exactly_one_now_after"),
        },
        "active_queue_modified": mutation_gate.get("active_queue_modified") is True,
        "write_performed": mutation_gate.get("write_performed") is True,
        "queue_write_authorized": mutation_gate.get("write_performed") is True,
        "queue_promotion_authorized": mutation_gate.get("queue_mutation_authorized") is True,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "executor_run_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "raw_content_output": False,
        "next_step": {
            "status": "review_promoted_now_before_run" if mutation_gate.get("write_performed") is True else "review_queue_promotion_apply_gate",
            "owner": "Nobao",
            "instruction": "run workbench goal/run against the promoted queue"
            if mutation_gate.get("write_performed") is True
            else "review NEXT-to-NOW promotion gate before --apply",
            "active_queue_mutation_authorized": mutation_gate.get("write_performed") is True,
            "queue_promotion_authorized": mutation_gate.get("queue_mutation_authorized") is True,
            "execution_authorized": False,
            "write_performed": mutation_gate.get("write_performed") is True,
        },
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_workbench_queue_promotion_apply_gate(result, apply=apply)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_workbench_queue_promotion_apply_gate(result: dict[str, Any], *, apply: bool) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.queue-promotion-apply-gate.v0.1":
        errors.append("workbench queue promotion apply gate schema_version is invalid")
    if result.get("mode") != "reviewed_next_to_now_promotion_gate":
        errors.append("workbench queue promotion apply gate mode is invalid")
    if result.get("preview_only") is not (not apply):
        errors.append("workbench queue promotion apply gate preview_only does not match apply mode")
    for flag in (
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "executor_run_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"workbench queue promotion apply gate must keep {flag}=false")
    if not apply:
        for flag in ("active_queue_modified", "write_performed", "queue_write_authorized"):
            if result.get(flag) is not False:
                errors.append(f"preview queue promotion apply gate must keep {flag}=false")
    if apply:
        for flag in ("active_queue_modified", "write_performed", "queue_write_authorized", "queue_promotion_authorized"):
            if result.get(flag) is not True:
                errors.append(f"applied queue promotion apply gate must set {flag}=true")
    proposal = result.get("proposal", {})
    if not result.get("errors"):
        if proposal.get("passed") is not True:
            errors.append("workbench queue promotion apply gate requires passed proposal")
        if proposal.get("close_current_now") is not True:
            errors.append("workbench queue promotion apply gate proposal must close current NOW")
        if not proposal.get("promote_next_title"):
            errors.append("workbench queue promotion apply gate proposal must identify NEXT target")
        if result.get("review", {}).get("review_status") != "accepted":
            errors.append("workbench queue promotion apply gate requires accepted review")
        gate = result.get("mutation_gate", {})
        if gate.get("passed") is not True:
            errors.append("workbench queue promotion apply gate requires passed mutation gate")
        if gate.get("queue_mutation_authorized") is not True:
            errors.append("workbench queue promotion apply gate requires queue mutation authorization")
        if gate.get("exactly_one_now_before") is not True:
            errors.append("workbench queue promotion apply gate requires exactly one NOW before")
        if gate.get("exactly_one_now_after") is not True:
            errors.append("workbench queue promotion apply gate must preserve exactly one NOW after")
        if gate.get("promoted_now_title") != proposal.get("promote_next_title"):
            errors.append("workbench queue promotion apply gate must promote the proposed NEXT title")
    if not result.get("next_step", {}).get("status"):
        errors.append("workbench queue promotion apply gate must emit next_step.status")
    return errors


def summarize_commander(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision_id": decision.get("decision_id"),
        "decision": decision.get("decision"),
        "recommended_track": decision.get("recommended_track"),
        "risk_level": decision.get("risk_level"),
        "execution_authorization_scope": decision.get("execution_authorization_scope"),
        "requires_jenn_decision": decision.get("requires_jenn_decision"),
        "execution_authorized": decision.get("execution_authorized"),
        "passed": decision.get("passed"),
    }


def summarize_track_preview(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "track_preview_id": preview.get("track_preview_id"),
        "selected_track": preview.get("selected_track"),
        "track_authorized": preview.get("track_authorized"),
        "execution_authorization_scope": preview.get("execution_authorization_scope"),
        "action_type": preview.get("action_type"),
        "preview_only": preview.get("preview_only"),
        "passed": preview.get("passed"),
    }


def build_intake_proposal(
    *,
    proposal_id: str,
    candidate: dict[str, Any],
    normalized_queue: dict[str, Any],
    machine_preview: dict[str, Any],
) -> dict[str, Any]:
    candidate_review = candidate.get("review_gate", {})
    candidate_requires_jenn = candidate_review.get("requires_jenn_decision") is True
    current_queue_blocked = machine_preview.get("blocked") is True
    current_requires_jenn = machine_preview.get("review_gate", {}).get("requires_jenn_decision") is True
    can_apply_after_review = (
        candidate.get("passed") is True
        and candidate.get("blocked") is not True
        and not candidate_requires_jenn
        and normalized_queue.get("passed") is True
        and not current_queue_blocked
    )
    proposed_item = {
        "lane": "NEXT",
        "title": candidate.get("title"),
        "body_lines": [
            f"Source candidate: {candidate.get('candidate_id')}",
            "Source: AGENTS OS Workbench intake proposal",
            "Mode: candidate-to-NEXT proposal only",
            "Boundary: reviewed queue intake gate required before any write",
        ],
    }
    return {
        "schema_version": "agents-os.workbench.intake-proposal.v0.1",
        "proposal_id": proposal_id,
        "preview_only": True,
        "proposal_only": True,
        "source_candidate_id": candidate.get("candidate_id"),
        "target_lane": "NEXT",
        "target_queue_path": normalized_queue.get("source_path"),
        "current_now": machine_preview.get("source_item", {}),
        "current_queue_blocked": current_queue_blocked,
        "current_requires_jenn_decision": current_requires_jenn,
        "candidate_requires_jenn_decision": candidate_requires_jenn,
        "can_apply_after_review": can_apply_after_review,
        "active_queue_modified": False,
        "write_performed": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": bool(candidate_requires_jenn or current_requires_jenn),
        "blocked_reason": None
        if can_apply_after_review
        else (
            "candidate requires Jenn decision"
            if candidate_requires_jenn
            else "current queue stop-state requires Jenn decision"
            if current_queue_blocked or current_requires_jenn
            else "candidate is blocked or queue is invalid"
        ),
        "proposed_queue_item": proposed_item,
        "raw_content_output": False,
        "errors": [],
    }


def validate_intake_proposal(proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if proposal.get("schema_version") != "agents-os.workbench.intake-proposal.v0.1":
        errors.append("intake proposal schema_version is invalid")
    if proposal.get("preview_only") is not True:
        errors.append("intake proposal must be preview_only")
    if proposal.get("proposal_only") is not True:
        errors.append("intake proposal must be proposal_only")
    if proposal.get("target_lane") != "NEXT":
        errors.append("intake proposal must target NEXT")
    for flag in (
        "active_queue_modified",
        "write_performed",
        "queue_write_authorized",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if proposal.get(flag) is not False:
            errors.append(f"intake proposal must keep {flag}=false")
    if proposal.get("requires_nobao_review") is not True:
        errors.append("intake proposal must require Nobao review")
    if proposal.get("current_queue_blocked") is True and proposal.get("can_apply_after_review") is not False:
        errors.append("intake proposal must not be applicable while current queue is blocked")
    if proposal.get("candidate_requires_jenn_decision") is True and proposal.get("requires_jenn_decision") is not True:
        errors.append("intake proposal must propagate candidate Jenn decision requirement")
    item = proposal.get("proposed_queue_item", {})
    if item.get("lane") != "NEXT":
        errors.append("intake proposal item must target NEXT")
    if not item.get("title"):
        errors.append("intake proposal item must include a title")
    if not proposal.get("proposal_id"):
        errors.append("intake proposal must include proposal_id")
    return errors


def accepted_nobao_review_for_intake(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "agents-os.workbench.intake-review.v0.1",
        "review_id": stable_id("INTAKEREVIEW", [proposal.get("proposal_id"), "accepted", "Nobao"]),
        "source_proposal_id": proposal.get("proposal_id"),
        "review_status": "accepted",
        "reviewer": "Nobao",
        "requires_jenn_decision": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
    }


def validate_intake_review(review: dict[str, Any], proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("schema_version") != "agents-os.workbench.intake-review.v0.1":
        errors.append("intake review schema_version is invalid")
    if review.get("review_status") != "accepted":
        errors.append("intake review_status must be accepted")
    if review.get("reviewer") != "Nobao":
        errors.append("intake review reviewer must be Nobao")
    if review.get("source_proposal_id") != proposal.get("proposal_id"):
        errors.append("intake review source_proposal_id must match proposal_id")
    if review.get("requires_jenn_decision") is True:
        errors.append("intake review requiring Jenn cannot authorize queue intake")
    for flag in (
        "queue_write_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
    ):
        if review.get(flag) is not False:
            errors.append(f"intake review must keep {flag}=false")
    return errors


def queue_lane_blocks(queue_text: str, lane: str) -> list[dict[str, str]]:
    in_lane = False
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in queue_text.splitlines():
        if line.strip() == f"## {lane}":
            in_lane = True
            continue
        if in_lane and line.startswith("## "):
            if current:
                current["body"] = "\n".join(current["body_lines"]).strip()
                current.pop("body_lines", None)
                blocks.append(current)
                current = None
            break
        if not in_lane:
            continue
        match = re.match(r"^###\s+([A-Z]+-\d{3}):\s+(.+?)\s*$", line)
        if match:
            if current:
                current["body"] = "\n".join(current["body_lines"]).strip()
                current.pop("body_lines", None)
                blocks.append(current)
            current = {"id": match.group(1), "title": match.group(2), "body_lines": []}
            continue
        if current is not None:
            current["body_lines"].append(line)
    if in_lane and current:
        current["body"] = "\n".join(current["body_lines"]).strip()
        current.pop("body_lines", None)
        blocks.append(current)
    return blocks  # type: ignore[return-value]


def queue_p3_signals(text: str) -> list[str]:
    scan_text = "\n".join(line for line in text.splitlines() if not NEGATED_SIGNAL_CONTEXT.search(line))
    return sorted(signal for signal, pattern in QUEUE_P3_PATTERNS.items() if pattern.search(scan_text))


def proposed_queue_item_text(item: dict[str, Any]) -> str:
    body_lines = item.get("body_lines", [])
    if not isinstance(body_lines, list):
        body_lines = []
    return "\n".join([str(item.get("title", "")), *[str(line) for line in body_lines]])


def format_next_block(item_id: str, title: str, body_lines: list[Any]) -> str:
    body = "\n".join(str(line).strip() for line in body_lines if str(line).strip()).strip()
    return f"### {item_id}: {title}\n\n{body}".strip()


def replace_lane_section(queue_text: str, lane: str, new_body: str) -> str:
    lines = queue_text.splitlines()
    start: int | None = None
    end = len(lines)
    for index, line in enumerate(lines):
        if line.strip() == f"## {lane}":
            start = index
            continue
        if start is not None and index > start and line.startswith("## "):
            end = index
            break
    if start is None:
        raise ValueError(f"queue lane not found: {lane}")
    replacement = [f"## {lane}", "", *new_body.strip().splitlines(), ""]
    return "\n".join(lines[:start] + replacement + lines[end:]).rstrip() + "\n"


def append_closed_entry(queue_text: str, entry: str) -> str:
    lines = queue_text.splitlines()
    closed_start: int | None = None
    for index, line in enumerate(lines):
        if line.strip() == "## CLOSED":
            closed_start = index
            break
    if closed_start is None:
        return queue_text.rstrip() + f"\n\n## CLOSED\n\n```text\n{entry}\n```\n"
    closed_end = len(lines)
    for index in range(closed_start + 1, len(lines)):
        if lines[index].startswith("## "):
            closed_end = index
            break
    fence_indices = [
        index
        for index in range(closed_start + 1, closed_end)
        if lines[index].strip().startswith("```")
    ]
    if len(fence_indices) >= 2:
        insert_at = fence_indices[-1]
        return "\n".join(lines[:insert_at] + [entry] + lines[insert_at:]).rstrip() + "\n"
    return "\n".join(lines[:closed_end] + [entry] + lines[closed_end:]).rstrip() + "\n"


def append_intake_to_queue_text(queue_text: str, proposal: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    now_blocks = queue_lane_blocks(queue_text, "NOW")
    next_blocks = queue_lane_blocks(queue_text, "NEXT")
    if len(now_blocks) != 1:
        raise ValueError(f"expected exactly one NOW before intake append, got {len(now_blocks)}")
    item = proposal.get("proposed_queue_item", {})
    title = str(item.get("title", "")).strip()
    body_lines = item.get("body_lines", [])
    if not isinstance(body_lines, list):
        body_lines = []
    next_indexes: list[int] = []
    for block in next_blocks:
        try:
            next_indexes.append(int(str(block.get("id", "NEXT-000")).split("-", 1)[1]))
        except (IndexError, ValueError):
            next_indexes.append(0)
    new_next_id = f"NEXT-{max(next_indexes, default=0) + 1:03d}"
    next_body_blocks = [
        format_next_block(str(block["id"]), str(block["title"]), [block.get("body", "")])
        for block in next_blocks
    ]
    next_body_blocks.append(format_next_block(new_next_id, title, body_lines))
    updated = replace_lane_section(queue_text, "NEXT", "\n\n".join(next_body_blocks))
    closed_entry = (
        "workbench_reviewed_intake_apply_gate_v0.1: "
        f"appended \"{title}\" to NEXT as {new_next_id}; proposal={proposal.get('proposal_id')}"
    )
    updated = append_closed_entry(updated, closed_entry)
    after_now = queue_lane_blocks(updated, "NOW")
    after_next = queue_lane_blocks(updated, "NEXT")
    return updated, {
        "target_lane": "NEXT",
        "appended_next_id": new_next_id,
        "appended_next_title": title,
        "next_count_before": len(next_blocks),
        "next_count_after": len(after_next),
        "exactly_one_now_before": len(now_blocks) == 1,
        "exactly_one_now_after": len(after_now) == 1,
        "promoted_now": False,
        "closed_entry": closed_entry,
    }


def resolve_queue_apply_path(
    queue_path: Path,
    allowed_root: Path = WORKSPACE_ROOT,
) -> tuple[Path | None, str | None]:
    candidate = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    try:
        resolved = candidate.resolve()
        root = allowed_root.resolve()
    except OSError as exc:
        return None, f"queue path could not be resolved: {exc}"
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, f"queue path must stay under {rel(root)}"
    if resolved.suffix != ".md":
        return None, "queue path must end with .md"
    if any(part in {"state-private", "secrets", "secret", "tokens", "credentials", "cookies"} for part in resolved.parts):
        return None, "queue path contains a protected path segment"
    if not resolved.exists() or not resolved.is_file():
        return None, f"queue path is not a file: {rel(resolved)}"
    return resolved, None


def reviewed_intake_apply_gate(
    proposal: dict[str, Any],
    review: dict[str, Any],
    queue_path: Path,
    *,
    apply: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    errors = validate_intake_proposal(proposal)
    errors.extend(validate_intake_review(review, proposal))
    if proposal.get("passed") is not True:
        errors.append("intake proposal must be passed")
    if proposal.get("can_apply_after_review") is not True:
        errors.append("intake proposal is not applicable after review")
    if proposal.get("current_queue_blocked") is True:
        errors.append("current queue is blocked; intake append cannot write")
    if proposal.get("requires_jenn_decision") is True:
        errors.append("intake proposal requiring Jenn cannot write queue")
    if proposal.get("candidate_requires_jenn_decision") is True:
        errors.append("candidate requiring Jenn cannot write queue")

    item = proposal.get("proposed_queue_item", {})
    signals = queue_p3_signals(proposed_queue_item_text(item))
    if signals:
        errors.append(f"proposed intake queue item contains P3 signals: {','.join(signals)}")

    resolved, path_error = resolve_queue_apply_path(queue_path, allowed_queue_root)
    mutation: dict[str, Any] = {}
    if path_error or resolved is None:
        errors.append(path_error or "queue path is not allowed")
    else:
        target_path = str(proposal.get("target_queue_path", ""))
        if target_path and rel(resolved) != target_path and str(resolved) != target_path:
            errors.append("intake proposal target_queue_path does not match queue_path")
        queue_text = resolved.read_text(encoding="utf-8")
        now_blocks = queue_lane_blocks(queue_text, "NOW")
        next_blocks = queue_lane_blocks(queue_text, "NEXT")
        proposed_title = str(item.get("title", "")).strip()
        if not proposed_title:
            errors.append("proposed intake queue item must include a title")
        if any(block.get("title") == proposed_title for block in now_blocks):
            errors.append("proposed intake queue item already exists in NOW")
        if any(block.get("title") == proposed_title for block in next_blocks):
            errors.append("proposed intake queue item already exists in NEXT")
        if not errors:
            try:
                updated_text, mutation = append_intake_to_queue_text(queue_text, proposal)
                mutation["queue_path"] = rel(resolved)
                if apply:
                    resolved.write_text(updated_text, encoding="utf-8")
            except ValueError as exc:
                errors.append(str(exc))

    can_write = bool(apply and not errors)
    result = {
        "schema_version": "agents-os.workbench.reviewed-intake-apply-gate.v0.1",
        "intake_apply_id": stable_id("INTAKEAPPLY", [proposal.get("proposal_id"), review.get("review_status"), apply]),
        "source_proposal_id": proposal.get("proposal_id"),
        "source_review_status": review.get("review_status"),
        "preview_only": not apply,
        "queue_intake_authorized": not errors,
        "queue_intake_write_authorized": can_write,
        "active_queue_modified": can_write,
        "write_performed": can_write,
        "queue_write_authorized": can_write,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "target_lane": "NEXT",
        "no_p3_intake_guard": not errors,
        "mutation": mutation,
        "errors": errors,
    }
    result_errors = validate_reviewed_intake_apply_gate(result)
    result["errors"] = sorted(set(result["errors"] + result_errors))
    result["passed"] = not result["errors"]
    return result


def validate_reviewed_intake_apply_gate(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.reviewed-intake-apply-gate.v0.1":
        errors.append("reviewed intake apply gate schema_version is invalid")
    if result.get("requires_nobao_review") is not True:
        errors.append("reviewed intake apply gate must require Nobao review")
    if result.get("target_lane") != "NEXT":
        errors.append("reviewed intake apply gate must target NEXT")
    for flag in (
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
    ):
        if result.get(flag) is not False:
            errors.append(f"reviewed intake apply gate must keep {flag}=false")
    if result.get("preview_only") is True:
        for flag in ("queue_intake_write_authorized", "active_queue_modified", "write_performed", "queue_write_authorized"):
            if result.get(flag) is not False:
                errors.append(f"preview intake apply gate must keep {flag}=false")
    if result.get("write_performed") is True:
        for flag in ("queue_intake_write_authorized", "active_queue_modified", "queue_write_authorized"):
            if result.get(flag) is not True:
                errors.append(f"write_performed requires true flag: {flag}")
    mutation = result.get("mutation", {})
    if result.get("queue_intake_authorized") is True:
        if mutation.get("target_lane") != "NEXT":
            errors.append("intake apply gate mutation must target NEXT")
        if mutation.get("exactly_one_now_before") is not True:
            errors.append("intake apply gate requires exactly one NOW before append")
        if mutation.get("exactly_one_now_after") is not True:
            errors.append("intake apply gate must preserve exactly one NOW after append")
        if mutation.get("promoted_now") is not False:
            errors.append("intake apply gate must not promote NOW")
    return errors


def build_record_preview(
    *,
    record_id: str,
    candidate: dict[str, Any],
    normalized_queue: dict[str, Any],
    machine_preview: dict[str, Any],
    commander_decision: dict[str, Any],
    intake_proposal: dict[str, Any],
    track_preview: dict[str, Any],
    track_result: dict[str, Any] | None,
    queue_proposal: dict[str, Any] | None,
    dashboard_summary: dict[str, Any],
    failure_report: dict[str, Any] | None,
    stop_loop: dict[str, Any] | None,
    next_step: dict[str, Any],
) -> dict[str, Any]:
    """Build a replayable cycle record without writing it to disk."""
    return {
        "schema_version": "agents-os.workbench.record-preview.v0.1",
        "record_id": record_id,
        "preview_only": True,
        "record_write_authorized": False,
        "write_performed": False,
        "raw_content_output": False,
        "replay_inputs": {
            "candidate_id": candidate.get("candidate_id"),
            "queue_path": normalized_queue.get("source_path"),
            "source_now_id": machine_preview.get("source_item", {}).get("id"),
            "validation_command_recorded": track_result is not None,
            "raw_intent_included": False,
        },
        "stage_receipts": {
            "task_passed": candidate.get("passed"),
            "queue_passed": normalized_queue.get("passed"),
            "machine_passed": machine_preview.get("passed"),
            "commander_passed": commander_decision.get("passed"),
            "track_preview_passed": track_preview.get("passed"),
            "local_validation_performed": track_result is not None,
            "local_validation_passed": track_result.get("passed") if track_result else None,
            "queue_proposal_present": queue_proposal is not None,
            "queue_proposal_passed": queue_proposal.get("passed") if queue_proposal else None,
            "intake_proposal_present": bool(intake_proposal.get("proposal_id")),
            "intake_can_apply_after_review": intake_proposal.get("can_apply_after_review"),
            "dashboard_passed": dashboard_summary.get("passed"),
            "failure_report_present": failure_report is not None,
            "stop_loop_present": stop_loop is not None,
        },
        "effect_summary": {
            "active_queue_modified": False,
            "queue_promotion_authorized": False,
            "route_auto_selection_authorized": False,
            "execution_authorized": False,
            "provider_call_authorized": False,
            "service_start_authorized": False,
            "external_write_authorized": False,
            "memory_write_authorized": False,
            "runtime_plugin_activation_authorized": False,
            "formal_memory_write_authorized": dashboard_summary.get("formal_memory_write_authorized"),
            "private_memory_raw_read_authorized": dashboard_summary.get("private_memory_raw_read_authorized"),
        },
        "ids": {
            "decision_id": commander_decision.get("decision_id"),
            "intake_proposal_id": intake_proposal.get("proposal_id"),
            "track_preview_id": track_preview.get("track_preview_id"),
            "track_result_id": track_result.get("track_result_id") if track_result else None,
            "queue_proposal_id": queue_proposal.get("proposal_id") if queue_proposal else None,
            "dashboard_id": dashboard_summary.get("dashboard_id"),
            "failure_id": failure_report.get("failure_id") if failure_report else None,
            "stop_loop_id": stop_loop.get("stop_loop_id") if stop_loop else None,
        },
        "next_step": {
            "status": next_step.get("status"),
            "owner": next_step.get("owner"),
            "decision_owner": next_step.get("decision_owner"),
            "requires_jenn_decision": next_step.get("requires_jenn_decision"),
            "instruction": next_step.get("instruction"),
            "accepted_route_ids": next_step.get("accepted_route_ids", []),
            "template_source_path": next_step.get("template_source_path"),
            "exact_confirmation_templates_available": next_step.get("exact_confirmation_templates_available"),
            "route_auto_selection_authorized": next_step.get("route_auto_selection_authorized"),
            "active_queue_mutation_authorized": next_step.get("active_queue_mutation_authorized"),
            "queue_promotion_authorized": next_step.get("queue_promotion_authorized"),
            "execution_authorized": next_step.get("execution_authorized"),
            "write_performed": next_step.get("write_performed"),
            "raw_content_output": next_step.get("raw_content_output"),
        },
    }


def validate_record_preview(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("schema_version") != "agents-os.workbench.record-preview.v0.1":
        errors.append("workbench record schema_version is invalid")
    if record.get("preview_only") is not True:
        errors.append("workbench record must be preview_only")
    for flag in ("record_write_authorized", "write_performed", "raw_content_output"):
        if record.get(flag) is not False:
            errors.append(f"workbench record must keep {flag}=false")
    effects = record.get("effect_summary", {})
    for flag in (
        "active_queue_modified",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "formal_memory_write_authorized",
        "private_memory_raw_read_authorized",
    ):
        if effects.get(flag) is not False:
            errors.append(f"workbench record effect must keep {flag}=false")
    replay = record.get("replay_inputs", {})
    if replay.get("raw_intent_included") is not False:
        errors.append("workbench record must not include raw intent")
    if not record.get("next_step", {}).get("status"):
        errors.append("workbench record must include next_step.status")
    errors.extend(validate_next_user_action_summary("workbench record next_step", record.get("next_step", {})))
    if not record.get("record_id"):
        errors.append("workbench record must include record_id")
    return errors


def resolve_record_path(record_path: Path, allowed_root: Path = DEFAULT_RECORD_ROOT) -> tuple[Path | None, str | None]:
    candidate = record_path if record_path.is_absolute() else WORKSPACE_ROOT / record_path
    try:
        resolved = candidate.resolve()
        root = allowed_root.resolve()
    except OSError as exc:
        return None, f"record path could not be resolved: {exc}"
    try:
        resolved.relative_to(root)
    except ValueError:
        return None, f"record path must stay under {rel(root)}"
    if resolved.suffix != ".json":
        return None, "record path must end with .json"
    if any(part in {"state-private", "secrets", "secret", "tokens", "credentials", "cookies"} for part in resolved.parts):
        return None, "record path contains a protected path segment"
    if not resolved.parent.exists():
        return None, f"record parent does not exist: {rel(resolved.parent)}"
    return resolved, None


def build_record_write_result(
    record: dict[str, Any],
    record_path: Path,
    *,
    apply: bool = False,
    allowed_root: Path = DEFAULT_RECORD_ROOT,
) -> dict[str, Any]:
    errors = validate_record_preview(record)
    resolved, path_error = resolve_record_path(record_path, allowed_root)
    if path_error or resolved is None:
        errors.append(path_error or "record path is not allowed")
    write_performed = False
    if apply and not errors and resolved is not None:
        resolved.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_performed = True
    result = {
        "schema_version": "agents-os.workbench.record-write.v0.1",
        "source_record_id": record.get("record_id"),
        "record_path": rel(resolved) if resolved is not None else str(record_path),
        "preview_only": not apply,
        "record_write_authorized": bool(apply and not errors),
        "write_performed": write_performed,
        "active_queue_modified": False,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "raw_content_output": False,
        "errors": errors,
    }
    validation_errors = validate_record_write_result(result, apply=apply)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_record_write_result(result: dict[str, Any], *, apply: bool) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.record-write.v0.1":
        errors.append("record write result schema_version is invalid")
    if result.get("preview_only") is not (not apply):
        errors.append("record write preview_only does not match apply mode")
    if result.get("write_performed") is not apply and result.get("passed") is not False:
        errors.append("record write_performed does not match apply mode")
    for flag in (
        "active_queue_modified",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"record write must keep {flag}=false")
    if apply and result.get("record_write_authorized") is not True and result.get("passed") is not False:
        errors.append("applied record write must be explicitly authorized")
    if not apply and result.get("record_write_authorized") is not False:
        errors.append("record write preview must not authorize write")
    return errors


def next_step_for(
    *,
    machine_preview: dict[str, Any],
    commander_decision: dict[str, Any],
    track_preview: dict[str, Any],
    track_result: dict[str, Any] | None,
    queue_proposal: dict[str, Any] | None,
) -> dict[str, Any]:
    if machine_preview.get("blocked") is True:
        action = machine_preview.get("next_user_action", {})
        return {
            "status": action.get("status") or "current_queue_blocked",
            "owner": action.get("decision_owner") or "Jenn",
            "decision_owner": action.get("decision_owner") or "Jenn",
            "requires_jenn_decision": action.get("requires_jenn_decision"),
            "reason": "current NOW item is blocked before automatic construction",
            "instruction": action.get("instruction") or "resolve_current_queue_stop",
            "accepted_route_ids": action.get("accepted_route_ids", []),
            "template_source_path": action.get("template_source_path"),
            "exact_confirmation_templates_available": action.get("exact_confirmation_templates_available"),
            "route_auto_selection_authorized": action.get("route_auto_selection_authorized"),
            "active_queue_mutation_authorized": action.get("active_queue_mutation_authorized"),
            "queue_promotion_authorized": action.get("queue_promotion_authorized"),
            "execution_authorized": action.get("execution_authorized"),
            "write_performed": action.get("write_performed"),
            "raw_content_output": action.get("raw_content_output"),
        }
    if commander_decision.get("requires_jenn_decision") is True:
        return {
            "status": "jenn_decision_required",
            "owner": "Jenn",
            "reason": "Commander classified the task as requiring Jenn decision",
            "instruction": "provide explicit current authorization or choose a safer task",
        }
    if track_preview.get("track_authorized") is not True:
        return {
            "status": "nobao_review_required",
            "owner": "Nobao",
            "reason": "Track Selector did not authorize a local-safe track",
            "instruction": "review candidate and clarify route",
        }
    if track_result is None:
        return {
            "status": "ready_for_local_validation",
            "owner": "Nobao",
            "reason": "Local-safe track preview is available but validation was not run",
            "instruction": "run with --run-local-validation",
        }
    if track_result.get("passed") is not True:
        return {
            "status": "stopped_for_review",
            "owner": "Nobao",
            "reason": "Local validation failed",
            "instruction": "inspect failure report before repair or queue proposal",
        }
    if queue_proposal and queue_proposal.get("passed") is True:
        return {
            "status": "review_queue_proposal",
            "owner": "Nobao",
            "reason": "Local validation passed and Queue Manager produced a proposal-only update",
            "instruction": "review proposal before any queue mutation",
        }
    return {
        "status": "review_cycle_output",
        "owner": "Nobao",
        "reason": "Workbench cycle completed without an apply step",
        "instruction": "review output and choose next local action",
    }


def build_cycle(
    intent: str,
    queue_path: Path = DEFAULT_QUEUE,
    *,
    run_local_validation: bool = False,
    validation_command: str = DEFAULT_VALIDATION_COMMAND,
    write_record: bool = False,
    record_path: Path | None = None,
    allowed_record_root: Path = DEFAULT_RECORD_ROOT,
) -> dict[str, Any]:
    producer = import_module(PRODUCER_PATH, "agents_os_task_producer_for_workbench")
    machine = import_module(MACHINE_PATH, "agents_os_machine_for_workbench")
    chain = import_module(CONTROL_CHAIN_PATH, "agents_os_control_chain_for_workbench")
    dashboard = import_module(DASHBOARD_PATH, "agents_os_dashboard_for_workbench")

    candidate = producer.candidate_from_intent(intent)
    candidate_errors = producer.validate_candidate(candidate)
    candidate["passed"] = not candidate_errors
    candidate["errors"] = candidate_errors

    normalized_queue = machine.load_queue(queue_path)
    machine_preview: dict[str, Any] = {}
    if normalized_queue.get("passed") is True:
        machine_preview = machine.build_preview(machine.now_item(normalized_queue))
        machine_preview_errors = machine.validate_preview(machine_preview)
        machine_preview["passed"] = not machine_preview_errors
        machine_preview["errors"] = machine_preview_errors

    commander_decision = chain.build_commander_decision(candidate, machine_preview or None)
    intake_proposal = build_intake_proposal(
        proposal_id=chain.stable_id(
            "INTAKEPROPOSAL",
            [
                candidate.get("candidate_id"),
                normalized_queue.get("source_path"),
                machine_preview.get("source_item", {}),
                machine_preview.get("blocked"),
            ],
        ),
        candidate=candidate,
        normalized_queue=normalized_queue,
        machine_preview=machine_preview,
    )
    intake_errors = validate_intake_proposal(intake_proposal)
    intake_proposal["errors"] = intake_errors
    intake_proposal["passed"] = not intake_errors
    action_type = "run_validation_command" if commander_decision.get("decision") == "route_to_local_executor" else None
    track_preview = chain.build_track_preview(commander_decision, action_type)

    track_result: dict[str, Any] | None = None
    failure_report: dict[str, Any] | None = None
    stop_loop: dict[str, Any] | None = None
    queue_proposal: dict[str, Any] | None = None
    current_queue_blocked = machine_preview.get("blocked") is True
    can_run_local_validation = (
        run_local_validation
        and not current_queue_blocked
        and track_preview.get("track_authorized") is True
        and track_preview.get("selected_track") == "local_executor"
    )
    if can_run_local_validation:
        track_result = chain.local_executor_run(
            track_preview,
            "run_validation_command",
            command=validation_command,
        )
        if track_result.get("passed") is True:
            queue_proposal = chain.queue_update_proposal(track_result, queue_path)
        else:
            failure_report = chain.build_failure_report(track_result)
            stop_loop = chain.build_stop_loop_result(failure_report)

    dashboard_summary = dashboard.build_dashboard_summary(queue_path, run_validations=False)
    next_step = next_step_for(
        machine_preview=machine_preview,
        commander_decision=commander_decision,
        track_preview=track_preview,
        track_result=track_result,
        queue_proposal=queue_proposal,
    )
    workbench_id = chain.stable_id(
        "WORKBENCH",
        [
            intent,
            rel(queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path),
            run_local_validation,
            candidate.get("candidate_id"),
            machine_preview.get("source_item", {}),
            commander_decision.get("decision"),
            track_preview.get("selected_track"),
            next_step,
        ],
    )
    record_preview = build_record_preview(
        record_id=chain.stable_id("WORKBENCHRECORD", [workbench_id, candidate.get("candidate_id"), next_step]),
        candidate=candidate,
        normalized_queue=normalized_queue,
        machine_preview=machine_preview,
        commander_decision=commander_decision,
        intake_proposal=intake_proposal,
        track_preview=track_preview,
        track_result=track_result,
        queue_proposal=queue_proposal,
        dashboard_summary=dashboard_summary,
        failure_report=failure_report,
        stop_loop=stop_loop,
        next_step=next_step,
    )
    record_write: dict[str, Any] | None = None
    if write_record:
        if record_path is None:
            record_path = DEFAULT_RECORD_ROOT / f"{record_preview['record_id'].lower()}.json"
        record_write = build_record_write_result(
            record_preview,
            record_path,
            apply=True,
            allowed_root=allowed_record_root,
        )

    errors = compact_errors(candidate, normalized_queue, machine_preview, commander_decision, track_preview, dashboard_summary)
    errors.extend(f"intake proposal: {error}" for error in intake_proposal.get("errors", []))
    if queue_proposal is not None:
        errors.extend(queue_proposal.get("errors", []))
    if failure_report is not None:
        errors.extend(failure_report.get("errors", []))
    if stop_loop is not None:
        errors.extend(stop_loop.get("errors", []))
    errors.extend(validate_record_preview(record_preview))
    if record_write is not None and record_write.get("passed") is not True:
        errors.extend(f"record write: {error}" for error in record_write.get("errors", []))
    authorization = authorization_defaults()
    authorization_failures = false_flag_failures(authorization)
    if authorization_failures:
        errors.append(f"workbench dangerous authorization flags not false: {','.join(authorization_failures)}")

    result = {
        "schema_version": "agents-os.workbench.cycle.v0.1",
        "workbench_id": workbench_id,
        "preview_first": True,
        "write_performed": False,
        "record_write_performed": record_write.get("write_performed") if record_write else False,
        "active_queue_modified": False,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "authorization": authorization,
        "source": {
            "intent_character_count": len(intent),
            "intent_raw_output": False,
            "queue_path": normalized_queue.get("source_path"),
        },
        "stages": {
            "idea": {"received": bool(intent.strip())},
            "task": summarize_candidate(candidate),
            "queue": {
                "passed": normalized_queue.get("passed"),
                "summary": normalized_queue.get("summary"),
            },
            "intake_proposal": intake_proposal,
            "machine": summarize_machine_preview(machine_preview),
            "judgment": summarize_commander(commander_decision),
            "track_preview": summarize_track_preview(track_preview),
            "local_validation": {
                "requested": run_local_validation,
                "performed": track_result is not None,
                "skipped_reason": None
                if track_result is not None
                else (
                    "current_queue_blocked"
                    if current_queue_blocked and run_local_validation
                    else "not_requested_or_not_authorized"
                ),
                "track_result_id": track_result.get("track_result_id") if track_result else None,
                "passed": track_result.get("passed") if track_result else None,
                "write_performed": track_result.get("write_performed") if track_result else False,
            },
            "queue_proposal": {
                "present": queue_proposal is not None,
                "proposal_id": queue_proposal.get("proposal_id") if queue_proposal else None,
                "proposal_only": queue_proposal.get("proposal_only") if queue_proposal else None,
                "active_queue_modified": queue_proposal.get("active_queue_modified") if queue_proposal else False,
                "close_current_now": queue_proposal.get("close_current_now") if queue_proposal else None,
                "promote_next_title": queue_proposal.get("promote_next_title") if queue_proposal else None,
            },
            "dashboard": {
                "passed": dashboard_summary.get("passed"),
                "now": dashboard_summary.get("queue", {}).get("now", {}),
                "next_user_action": dashboard_summary.get("next_user_action", {}).get("status"),
                "memory_candidate_count": len(dashboard_summary.get("memory_candidates", [])),
                "formal_memory_write_authorized": dashboard_summary.get("formal_memory_write_authorized"),
            },
            "record": record_preview,
            "record_write": record_write
            or {
                "present": False,
                "write_performed": False,
                "record_write_authorized": False,
            },
            "failure": {
                "present": failure_report is not None,
                "category": failure_report.get("category") if failure_report else None,
                "stop_loop_status": stop_loop.get("status") if stop_loop else None,
                "queue_promoted": stop_loop.get("queue_promoted") if stop_loop else False,
            },
            "next_step": next_step,
        },
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_cycle(result)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_cycle(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.cycle.v0.1":
        errors.append("workbench cycle schema_version is invalid")
    if result.get("preview_first") is not True:
        errors.append("workbench must remain preview_first")
    for flag in (
        "write_performed",
        "active_queue_modified",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"workbench must keep {flag}=false")
    failures = false_flag_failures(result.get("authorization", {}))
    if failures:
        errors.append(f"workbench authorization flags not false: {','.join(failures)}")
    stages = result.get("stages", {})
    required_stages = (
        "idea",
        "task",
        "queue",
        "intake_proposal",
        "machine",
        "judgment",
        "track_preview",
        "local_validation",
        "queue_proposal",
        "dashboard",
        "record",
        "record_write",
        "failure",
        "next_step",
    )
    for stage in required_stages:
        if stage not in stages:
            errors.append(f"workbench missing stage: {stage}")
    if stages.get("task", {}).get("execution_authorized") is not False:
        errors.append("task stage must not authorize execution")
    if stages.get("machine", {}).get("execution_authorized") is not False:
        errors.append("machine stage must not authorize execution")
    if stages.get("judgment", {}).get("execution_authorized") is not False:
        errors.append("judgment stage must not authorize execution")
    if stages.get("queue_proposal", {}).get("active_queue_modified") is not False:
        errors.append("queue proposal stage must not mutate active queue")
    intake_errors = validate_intake_proposal(stages.get("intake_proposal", {}))
    errors.extend(f"intake proposal stage: {error}" for error in intake_errors)
    if stages.get("dashboard", {}).get("formal_memory_write_authorized") is not False:
        errors.append("dashboard stage must not authorize formal Memory write")
    record_errors = validate_record_preview(stages.get("record", {}))
    errors.extend(f"record stage: {error}" for error in record_errors)
    record_write = stages.get("record_write", {})
    if record_write.get("write_performed") is True:
        if record_write.get("schema_version") != "agents-os.workbench.record-write.v0.1":
            errors.append("record_write stage schema_version is invalid")
        if record_write.get("active_queue_modified") is not False:
            errors.append("record_write stage must not mutate active queue")
        if result.get("record_write_performed") is not True:
            errors.append("record_write_performed should reflect record_write stage")
    elif result.get("record_write_performed") is not False:
        errors.append("record_write_performed must be false when no record write occurred")
    if stages.get("failure", {}).get("queue_promoted") is not False:
        errors.append("failure stage must not promote queue")
    if not stages.get("next_step", {}).get("status"):
        errors.append("workbench must emit next_step.status")
    errors.extend(validate_next_user_action_summary("workbench cycle next_step", stages.get("next_step", {})))
    errors.extend(
        validate_next_user_action_summary(
            "workbench machine",
            stages.get("machine", {}).get("next_user_action", {}),
        )
    )
    return errors


def build_advance(
    intent: str,
    queue_path: Path = DEFAULT_QUEUE,
    *,
    validation_command: str = DEFAULT_VALIDATION_COMMAND,
    record_root: Path = DEFAULT_RECORD_ROOT,
    apply_intake: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    """Run one bounded local-safe workbench advancement.

    Advance is the one-step workbench entrypoint: it always asks the cycle to
    run authorized local validation and to persist a replayable local record.
    Queue intake remains behind the reviewed apply gate.
    """
    resolved_queue = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    cycle_record_path = record_root / f"{stable_id('CYCLERECORD', [intent, rel(resolved_queue), validation_command]).lower()}.json"
    advance_record_path = record_root / f"{stable_id('ADVANCERECORD', [intent, rel(resolved_queue), validation_command, apply_intake]).lower()}.json"
    cycle = build_cycle(
        intent,
        queue_path,
        run_local_validation=True,
        validation_command=validation_command,
        write_record=True,
        record_path=cycle_record_path,
        allowed_record_root=record_root,
    )
    intake_apply: dict[str, Any] = {
        "present": False,
        "requested": apply_intake,
        "write_performed": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
    }
    if apply_intake:
        proposal = cycle.get("stages", {}).get("intake_proposal", {})
        review = accepted_nobao_review_for_intake(proposal)
        intake_apply = reviewed_intake_apply_gate(
            proposal,
            review,
            queue_path,
            apply=True,
            allowed_queue_root=allowed_queue_root,
        )
        intake_apply["present"] = True
        intake_apply["requested"] = True

    stages = cycle.get("stages", {})
    local_validation = stages.get("local_validation", {})
    track_preview = stages.get("track_preview", {})
    record_write = stages.get("record_write", {})
    errors = []
    if cycle.get("passed") is not True:
        errors.extend(f"cycle: {error}" for error in cycle.get("errors", []))
    if intake_apply.get("present") and intake_apply.get("passed") is not True:
        errors.extend(f"intake apply: {error}" for error in intake_apply.get("errors", []))
    result = {
        "schema_version": "agents-os.workbench.advance.v0.1",
        "advance_id": stable_id(
            "ADVANCE",
            [
                cycle.get("workbench_id"),
                record_write.get("record_path"),
                apply_intake,
                intake_apply.get("intake_apply_id"),
        ],
        ),
        "mode": "local_safe_one_step",
        "preview_first": True,
        "source_cycle_id": cycle.get("workbench_id"),
        "write_performed": False,
        "cycle_record_write_performed": record_write.get("write_performed") is True,
        "advance_record_write_performed": False,
        "record_write_performed": False,
        "active_queue_modified": intake_apply.get("active_queue_modified") is True,
        "queue_write_authorized": intake_apply.get("queue_write_authorized") is True,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "stages": {
            "cycle": {
                "passed": cycle.get("passed"),
                "workbench_id": cycle.get("workbench_id"),
                "next_step": stages.get("next_step", {}),
            },
            "execution": {
                "requested": True,
                "local_safe_execution_performed": local_validation.get("performed") is True,
                "selected_track": track_preview.get("selected_track"),
                "action_type": track_preview.get("action_type"),
                "track_result_id": local_validation.get("track_result_id"),
                "passed": local_validation.get("passed"),
                "execution_authorized": False,
            },
            "verification": {
                "performed": local_validation.get("performed") is True,
                "validation_command_recorded": local_validation.get("performed") is True,
                "passed": local_validation.get("passed"),
            },
            "record": {
                "write_performed": False,
                "record_write_authorized": False,
                "cycle_record_write_performed": record_write.get("write_performed") is True,
                "cycle_record_path": record_write.get("record_path"),
                "advance_record_write_performed": False,
                "advance_record_path": rel(advance_record_path),
                "record_path": rel(advance_record_path),
            },
            "intake_apply": intake_apply,
            "next_step": stages.get("next_step", {}),
        },
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_advance(result, apply_intake=apply_intake, require_advance_record=False)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    if not result["errors"]:
        resolved_record, record_error = resolve_record_path(advance_record_path, record_root)
        if record_error or resolved_record is None:
            result["errors"].append(f"advance record write: {record_error or 'record path is not allowed'}")
        else:
            try:
                result["advance_record_write_performed"] = True
                result["record_write_performed"] = True
                result["stages"]["record"]["write_performed"] = True
                result["stages"]["record"]["record_write_authorized"] = True
                result["stages"]["record"]["advance_record_write_performed"] = True
                result["stages"]["record"]["advance_record_path"] = rel(resolved_record)
                result["stages"]["record"]["record_path"] = rel(resolved_record)
                resolved_record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                result["advance_record_write_performed"] = False
                result["record_write_performed"] = result.get("cycle_record_write_performed") is True
                result["stages"]["record"]["write_performed"] = result.get("cycle_record_write_performed") is True
                result["stages"]["record"]["record_write_authorized"] = False
                result["stages"]["record"]["advance_record_write_performed"] = False
                result["errors"].append(f"advance record write failed: {exc}")
    final_validation_errors = validate_advance(result, apply_intake=apply_intake, require_advance_record=True)
    result["errors"] = sorted(set(result["errors"] + final_validation_errors))
    result["passed"] = not result["errors"]
    if result["advance_record_write_performed"] is True and result["passed"] is True:
        resolved_record, record_error = resolve_record_path(advance_record_path, record_root)
        if record_error or resolved_record is None:
            result["advance_record_write_performed"] = False
            result["record_write_performed"] = result.get("cycle_record_write_performed") is True
            result["stages"]["record"]["advance_record_write_performed"] = False
            result["stages"]["record"]["record_write_authorized"] = False
            result["errors"].append(f"advance record final write: {record_error or 'record path is not allowed'}")
            result["passed"] = False
        else:
            try:
                resolved_record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                result["advance_record_write_performed"] = False
                result["record_write_performed"] = result.get("cycle_record_write_performed") is True
                result["stages"]["record"]["advance_record_write_performed"] = False
                result["stages"]["record"]["record_write_authorized"] = False
                result["errors"].append(f"advance record final write failed: {exc}")
                result["passed"] = False
    return result


def validate_advance(
    result: dict[str, Any],
    *,
    apply_intake: bool,
    require_advance_record: bool = True,
) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.advance.v0.1":
        errors.append("workbench advance schema_version is invalid")
    if result.get("mode") != "local_safe_one_step":
        errors.append("workbench advance mode must be local_safe_one_step")
    if result.get("preview_first") is not True:
        errors.append("workbench advance must remain preview_first")
    for flag in (
        "write_performed",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"workbench advance must keep {flag}=false")
    if result.get("cycle_record_write_performed") is not True:
        errors.append("workbench advance must write a cycle record")
    if require_advance_record and result.get("advance_record_write_performed") is not True:
        errors.append("workbench advance must write an advance record")
    if require_advance_record and result.get("record_write_performed") is not True:
        errors.append("workbench advance must mark local record write performed")
    stages = result.get("stages", {})
    for stage in ("cycle", "execution", "verification", "record", "intake_apply", "next_step"):
        if stage not in stages:
            errors.append(f"workbench advance missing stage: {stage}")
    if stages.get("execution", {}).get("execution_authorized") is not False:
        errors.append("workbench advance execution stage must not authorize dangerous execution")
    record = stages.get("record", {})
    if require_advance_record and record.get("write_performed") is not True:
        errors.append("workbench advance record stage must write")
    if record.get("cycle_record_write_performed") is not True:
        errors.append("workbench advance record stage must write cycle record")
    if require_advance_record and record.get("advance_record_write_performed") is not True:
        errors.append("workbench advance record stage must write advance record")
    if require_advance_record and not record.get("advance_record_path"):
        errors.append("workbench advance record stage must include advance_record_path")
    intake_apply = stages.get("intake_apply", {})
    if apply_intake:
        if intake_apply.get("present") is not True:
            errors.append("workbench advance apply_intake requires intake_apply stage")
        if intake_apply.get("passed") is not True:
            errors.append("workbench advance apply_intake must pass")
        if result.get("active_queue_modified") is not True:
            errors.append("workbench advance apply_intake should mark queue modified")
        if result.get("queue_write_authorized") is not True:
            errors.append("workbench advance apply_intake should authorize queue write")
    else:
        if result.get("active_queue_modified") is not False:
            errors.append("workbench advance without apply_intake must not modify queue")
        if result.get("queue_write_authorized") is not False:
            errors.append("workbench advance without apply_intake must not authorize queue write")
        if intake_apply.get("write_performed") is not False:
            errors.append("workbench advance without apply_intake must not write intake")
    if intake_apply.get("queue_promotion_authorized") is not False:
        errors.append("workbench advance intake must not authorize queue promotion")
    if intake_apply.get("execution_authorized") is not False:
        errors.append("workbench advance intake must not authorize execution")
    if not stages.get("next_step", {}).get("status"):
        errors.append("workbench advance must emit next_step.status")
    return errors


def resolve_record_root(record_root: Path) -> tuple[Path | None, str | None]:
    candidate = record_root if record_root.is_absolute() else WORKSPACE_ROOT / record_root
    try:
        resolved = candidate.resolve()
    except OSError as exc:
        return None, f"record root could not be resolved: {exc}"
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError:
        return None, f"record root must stay under {rel(WORKSPACE_ROOT)}"
    if any(part in {"state-private", "secrets", "secret", "tokens", "credentials", "cookies"} for part in resolved.parts):
        return None, "record root contains a protected path segment"
    if not resolved.exists() or not resolved.is_dir():
        return None, f"record root is not a directory: {rel(resolved)}"
    return resolved, None


def build_status(record_root: Path = DEFAULT_RECORD_ROOT, queue_path: Path = DEFAULT_QUEUE) -> dict[str, Any]:
    errors: list[str] = []
    live_queue = build_live_queue_state(queue_path)
    if live_queue.get("passed") is not True:
        errors.extend(f"live queue: {error}" for error in live_queue.get("errors", []))
    resolved_root, root_error = resolve_record_root(record_root)
    records: list[tuple[int, Path, dict[str, Any]]] = []
    goal_records: list[tuple[int, Path, dict[str, Any]]] = []
    ignored_json_count = 0
    if root_error or resolved_root is None:
        errors.append(root_error or "record root is not allowed")
    else:
        for path in sorted(resolved_root.glob("*.json")):
            try:
                payload = load_json(path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"record read failed: {rel(path)}: {exc}")
                continue
            try:
                mtime_ns = path.stat().st_mtime_ns
            except OSError as exc:
                errors.append(f"record stat failed: {rel(path)}: {exc}")
                continue
            schema = payload.get("schema_version")
            if schema == "agents-os.workbench.advance.v0.1":
                records.append((mtime_ns, path, payload))
            elif schema == "agents-os.workbench.goal-session.v0.1":
                goal_records.append((mtime_ns, path, payload))
            else:
                ignored_json_count += 1

    latest_path: Path | None = None
    latest: dict[str, Any] = {}
    if records:
        _mtime_ns, latest_path, latest = max(records, key=lambda item: (item[0], item[1].name))
    latest_stages = latest.get("stages", {}) if latest else {}
    latest_next_step = latest_stages.get("next_step", {}) if latest else {}
    latest_goal_path: Path | None = None
    latest_goal: dict[str, Any] = {}
    if goal_records:
        _goal_mtime_ns, latest_goal_path, latest_goal = max(goal_records, key=lambda item: (item[0], item[1].name))
    latest_goal_summary = latest_goal.get("run_summary", {}) if latest_goal else {}
    latest_goal_next_step = latest_goal.get("next_step", {}) if latest_goal else {}
    latest_goal_route_choice_readiness = (
        latest_goal.get("route_choice_readiness") or build_route_choice_readiness(latest_goal_next_step)
        if latest_goal
        else {}
    )
    status_next_step = latest_next_step if latest else {
        "status": "no_advance_records",
        "owner": "Nobao",
        "instruction": "run workbench advance to create the first local advance record",
    }
    route_choice_readiness = build_route_choice_readiness(status_next_step)
    live_next_step = live_queue.get("next_step", {})
    status_reconciliation = {
        "schema_version": "agents-os.workbench.status-reconciliation.v0.1",
        "record_next_step_status": status_next_step.get("status"),
        "live_queue_next_step_status": live_next_step.get("status"),
        "record_boundary_may_be_stale": bool(
            latest
            and live_next_step.get("status")
            and status_next_step.get("status") != live_next_step.get("status")
        ),
        "next_action_source": "live_queue"
        if live_next_step.get("status") in {"queue_ready_for_run", "route_choice_required", "jenn_decision_required"}
        else "latest_record",
        "write_performed": False,
    }
    result = {
        "schema_version": "agents-os.workbench.status.v0.1",
        "read_only": True,
        "write_performed": False,
        "live_queue": live_queue,
        "status_reconciliation": status_reconciliation,
        "record_root": rel(resolved_root) if resolved_root is not None else str(record_root),
        "advance_record_count": len(records),
        "goal_session_count": len(goal_records),
        "ignored_json_count": ignored_json_count,
        "latest_present": bool(latest),
        "latest_record_path": rel(latest_path) if latest_path is not None else None,
        "latest_advance_id": latest.get("advance_id") if latest else None,
        "latest_passed": latest.get("passed") if latest else None,
        "latest_mode": latest.get("mode") if latest else None,
        "latest_execution": {
            "local_safe_execution_performed": latest_stages.get("execution", {}).get("local_safe_execution_performed")
            if latest
            else None,
            "selected_track": latest_stages.get("execution", {}).get("selected_track") if latest else None,
            "passed": latest_stages.get("execution", {}).get("passed") if latest else None,
        },
        "latest_verification": {
            "performed": latest_stages.get("verification", {}).get("performed") if latest else None,
            "passed": latest_stages.get("verification", {}).get("passed") if latest else None,
        },
        "latest_record": {
            "record_write_performed": latest.get("record_write_performed") if latest else None,
            "advance_record_write_performed": latest.get("advance_record_write_performed") if latest else None,
            "cycle_record_write_performed": latest.get("cycle_record_write_performed") if latest else None,
            "advance_record_path": latest_stages.get("record", {}).get("advance_record_path") if latest else None,
            "cycle_record_path": latest_stages.get("record", {}).get("cycle_record_path") if latest else None,
        },
        "latest_effects": {
            "active_queue_modified": latest.get("active_queue_modified") if latest else None,
            "queue_write_authorized": latest.get("queue_write_authorized") if latest else None,
            "queue_promotion_authorized": latest.get("queue_promotion_authorized") if latest else None,
            "execution_authorized": latest.get("execution_authorized") if latest else None,
            "provider_call_authorized": latest.get("provider_call_authorized") if latest else None,
            "service_start_authorized": latest.get("service_start_authorized") if latest else None,
            "external_write_authorized": latest.get("external_write_authorized") if latest else None,
            "memory_write_authorized": latest.get("memory_write_authorized") if latest else None,
            "runtime_plugin_activation_authorized": latest.get("runtime_plugin_activation_authorized") if latest else None,
        },
        "latest_goal_session": {
            "present": bool(latest_goal),
            "record_path": rel(latest_goal_path) if latest_goal_path is not None else None,
            "goal_session_id": latest_goal.get("goal_session_id") if latest_goal else None,
            "passed": latest_goal.get("passed") if latest_goal else None,
            "goal_state": latest_goal.get("goal_state") if latest_goal else None,
            "run_id": latest_goal_summary.get("run_id") if latest_goal else None,
            "steps_performed": latest_goal_summary.get("steps_performed") if latest_goal else None,
            "local_safe_execution_count": latest_goal_summary.get("local_safe_execution_count") if latest_goal else None,
            "record_write_count": latest_goal_summary.get("record_write_count") if latest_goal else None,
            "stopped_reason": latest_goal_summary.get("stopped_reason") if latest_goal else None,
            "next_step": latest_goal_next_step,
            "route_choice_readiness": latest_goal_route_choice_readiness,
            "objective_raw_output": latest_goal.get("source", {}).get("objective_raw_output") if latest_goal else None,
            "raw_content_output": latest_goal.get("raw_content_output") if latest_goal else None,
        },
        "route_choice_readiness": route_choice_readiness,
        "next_step": status_next_step,
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_status(result)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_status(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.status.v0.1":
        errors.append("workbench status schema_version is invalid")
    if result.get("read_only") is not True:
        errors.append("workbench status must be read_only")
    if result.get("write_performed") is not False:
        errors.append("workbench status must not write")
    if result.get("raw_content_output") is not False:
        errors.append("workbench status must not output raw record content")
    live_errors = validate_live_queue_state(result.get("live_queue", {}))
    errors.extend(f"live queue: {error}" for error in live_errors)
    reconciliation = result.get("status_reconciliation", {})
    if reconciliation.get("schema_version") != "agents-os.workbench.status-reconciliation.v0.1":
        errors.append("workbench status reconciliation schema_version is invalid")
    if reconciliation.get("write_performed") is not False:
        errors.append("workbench status reconciliation must not write")
    if not reconciliation.get("live_queue_next_step_status"):
        errors.append("workbench status reconciliation must include live queue next step")
    if result.get("advance_record_count", 0) < 0:
        errors.append("workbench status advance_record_count cannot be negative")
    if result.get("goal_session_count", 0) < 0:
        errors.append("workbench status goal_session_count cannot be negative")
    if result.get("latest_present") is True:
        if not result.get("latest_record_path"):
            errors.append("workbench status latest record must include path")
        if not result.get("latest_advance_id"):
            errors.append("workbench status latest record must include advance_id")
        effects = result.get("latest_effects", {})
        for flag in (
            "queue_promotion_authorized",
            "execution_authorized",
            "provider_call_authorized",
            "service_start_authorized",
            "external_write_authorized",
            "memory_write_authorized",
            "runtime_plugin_activation_authorized",
        ):
            if effects.get(flag) is not False:
                errors.append(f"workbench status latest effect must keep {flag}=false")
    goal_session = result.get("latest_goal_session", {})
    if goal_session.get("present") is True:
        if not goal_session.get("record_path"):
            errors.append("workbench status latest goal session must include record_path")
        if not goal_session.get("goal_session_id"):
            errors.append("workbench status latest goal session must include goal_session_id")
        if not goal_session.get("goal_state"):
            errors.append("workbench status latest goal session must include goal_state")
        if not goal_session.get("next_step", {}).get("status"):
            errors.append("workbench status latest goal session must include next_step.status")
        if goal_session.get("objective_raw_output") is not False:
            errors.append("workbench status latest goal session must not expose raw objective")
        if goal_session.get("raw_content_output") is not False:
            errors.append("workbench status latest goal session must not output raw content")
        goal_route_choice_errors = validate_route_choice_readiness(goal_session.get("route_choice_readiness", {}))
        errors.extend(f"workbench status latest goal route choice readiness: {error}" for error in goal_route_choice_errors)
    if not result.get("next_step", {}).get("status"):
        errors.append("workbench status must emit next_step.status")
    route_choice_errors = validate_route_choice_readiness(result.get("route_choice_readiness", {}))
    errors.extend(f"route choice readiness: {error}" for error in route_choice_errors)
    return errors


def selector_candidate_for_now(
    now_title: str,
    evidence_text: str,
    *,
    completed_titles: list[str] | None = None,
) -> dict[str, Any]:
    title_lc = now_title.lower()
    completed = completed_titles or []
    if "active-loop" in title_lc or "codex appserver" in title_lc or "codex-appserver" in title_lc or "message bus" in title_lc:
        title = "AGENTS OS active-loop receipt contract review v0.1"
        goal_delta = "turn the imported Codex-to-Codex loop into a receipt-contract reviewed execution component"
        state_delta = "imported-component -> receipt-contract-ready-for-workbench-review"
        why_next = (
            "The active-loop source is now imported and boundary-checked; the next useful step is to review "
            "the task-packet and receipt contract before any managed run can be considered."
        )
        completion = [
            "receipt schema is present and validated by fast checks",
            "task-packet entry boundary is reviewable",
            "raw observer payload remains outside default records export",
            "workbench remains the authority boundary",
        ]
        validation = [
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = [
            "task packet would require authority outside workbench gate",
            "receipt would include raw broad payloads by default",
            "component would need a managed run before contract review",
        ]
    elif "external git post-push verification receipt" in title_lc:
        title = "AGENTS OS external Git PR review tracking gate v0.1"
        goal_delta = "turn a verified post-push receipt into review-tracked merge readiness without new external writes"
        state_delta = "remote-verified-and-local-scope-known -> pr-review-tracking-ready"
        why_next = (
            "The current external Git item is already in post-push verification; the next useful step is to track "
            "review state and merge readiness without rewinding to command execution."
        )
        completion = [
            "current PR or remote review target is identified",
            "unresolved review comments are classified as actionable or non-actionable",
            "local branch remains aligned with the reviewed head",
            "merge or further external write remains separately gated",
        ]
        validation = [
            "gh pr view --json state,isDraft,mergeable,reviewDecision,headRefOid",
            "git status --short --branch --untracked-files=all",
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = [
            "PR or reviewed remote target cannot be identified",
            "new unresolved actionable review appears",
            "local head differs from reviewed head",
        ]
    elif ("external git" in title_lc or "publication" in title_lc or "pre-push" in title_lc) and external_git_has_post_push_evidence(evidence_text):
        published_ref = external_git_published_branch_ref(evidence_text)
        title = "AGENTS OS external Git post-push verification receipt v0.1"
        goal_delta = "turn a pushed external Git action into a verified receipt with local leftovers classified"
        state_delta = "published-but-unverified -> remote-verified-and-local-scope-known"
        why_next = (
            "Route C has moved from target and pre-push gates into a published remote branch; "
            "the next useful step is to verify remote state, record what was published, "
            "and classify local leftovers before any further external Git work."
        )
        completion = [
            "published remote ref matches the intended local commit or declared PR evidence",
            "published file scope is recorded",
            "remaining local-only files are classified",
            "external-write boundary returns to blocked after receipt",
        ]
        validation = [
            f"git ls-remote origin {published_ref}" if published_ref else "identify and verify the declared pushed branch or PR ref",
            "git status --short --branch --untracked-files=all",
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = [
            "published remote ref does not match local HEAD or declared PR evidence",
            "unexpected file was published",
            "restricted private material appears in published scope",
        ]
    elif (
        "external git" in title_lc
        or "publication" in title_lc
        or "pre-push" in title_lc
    ) and title_is_repeat("AGENTS OS external Git exact pre-push command gate v0.1", completed):
        title = "AGENTS OS external Git command execution authorization gate v0.1"
        goal_delta = "turn an accepted no-write command plan into a Jenn-authorized external Git execution boundary"
        state_delta = "pre-push-plan-accepted -> external-write-execution-gate-ready"
        why_next = (
            "The exact pre-push command gate is already closed, but the current evidence still says no push happened; "
            "the next useful step is a separate Jenn authorization boundary for executing the accepted command plan."
        )
        completion = [
            "accepted command plan is referenced without repeating the pre-push planning task",
            "tracked and untracked scope is rechecked before execution",
            "Jenn external-write authorization remains required",
            "plan must not include force push, tag, release, deploy, or history rewrite",
        ]
        validation = [
            "git status --short --branch --untracked-files=all",
            "git diff --name-status origin/main...HEAD",
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = [
            "accepted command plan is missing or stale",
            "scope changed since the accepted no-write command gate",
            "Jenn external-write execution authorization is missing",
        ]
    elif "external git" in title_lc or "publication" in title_lc or "pre-push" in title_lc:
        title = "AGENTS OS external Git exact pre-push command gate v0.1"
        goal_delta = "turn publication intent into an exact, reviewable command plan before any external Git write"
        state_delta = "target-selected-no-push -> exact-command-gate-ready"
        why_next = (
            "The queue has an external Git target but no non-negated push or PR evidence; "
            "the next useful step is the exact pre-push command gate, not post-push verification."
        )
        completion = [
            "tracked and untracked publication scope is listed",
            "exact external Git command plan is listed for Jenn approval",
            "excluded files and private boundaries are explicit",
            "external-write authority remains false until the separate execution gate",
        ]
        validation = [
            "git status --short --branch --untracked-files=all",
            "git diff --name-status origin/main...HEAD",
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = [
            "scope includes unclassified private or generated files",
            "plan must not include force push, tag, release, deploy, or history rewrite",
            "Jenn gate is missing before external write",
        ]
    elif "memory" in title_lc:
        title = "AGENTS OS Memory candidate review receipt v0.1"
        goal_delta = "turn Memory intent into reviewed candidate facts without performing a formal Memory write"
        state_delta = "memory-intent -> reviewable-memory-candidate"
        why_next = "Memory work must move through candidate review before any formal Memory write is possible."
        completion = [
            "candidate facts are listed without raw private Memory",
            "write authorization remains false",
            "Jenn confirmation text is prepared if needed",
        ]
        validation = [
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = ["candidate requires private raw Memory", "formal Memory write would be needed"]
    elif "provider" in title_lc:
        title = "AGENTS OS provider fake-run boundary receipt v0.1"
        goal_delta = "turn provider execution intent into a fake-run boundary proof before live calls"
        state_delta = "provider-intent -> fake-provider-boundary-verified"
        why_next = "Provider execution design must prove fake-provider boundaries before any live provider call."
        completion = [
            "fake-provider path is described",
            "live provider call remains unauthorized",
            "cost/network/access controls are listed",
        ]
        validation = [
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = ["live provider call would be required", "private access material would be read"]
    else:
        title = "AGENTS OS next evidence review v0.1"
        goal_delta = "turn the current NOW item into evidence for a close, promote, or continue decision"
        state_delta = "current-now-open -> evidence-reviewed-decision-ready"
        why_next = "The current NOW item needs a distinct evidence review before promotion or closure."
        completion = [
            "current evidence is summarized",
            "missing proof is listed",
            "next boundary is explicit",
        ]
        validation = [
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate --level fast",
        ]
        stops = ["review would repeat current NOW", "dangerous authority would be needed"]

    return {
        "title": title,
        "substantive_progress": True,
        "goal_delta": goal_delta,
        "state_delta": state_delta,
        "why_next": why_next,
        "completion_criteria": completion,
        "validation": validation,
        "stop_conditions": stops,
        "blocked_authority": [
            "provider_call",
            "service_start",
            "runtime_plugin_activation",
            "external_write_without_exact_gate",
            "formal_memory_write_without_exact_gate",
            "state_private_read",
            "private_access_material_read",
            "history_rewrite",
            "force_push",
        ],
        "body_lines": [
            f"Why next: {why_next}",
            "Completion criteria:",
            *[f"- {item}" for item in completion],
            "Validation:",
            *[f"- {item}" for item in validation],
            "Stop conditions:",
            *[f"- {item}" for item in stops],
            "Boundary: no provider, Memory, runtime/plugin, private-state, or external-write authority is granted by this candidate.",
        ],
    }


def build_next_step_selector(
    queue_path: Path = DEFAULT_QUEUE,
    record_root: Path = DEFAULT_RECORD_ROOT,
) -> dict[str, Any]:
    """Select a non-repeating NEXT candidate without mutating the queue."""
    errors: list[str] = []
    live_queue = build_live_queue_state(queue_path)
    if live_queue.get("passed") is not True:
        errors.extend(f"live queue: {error}" for error in live_queue.get("errors", []))

    resolved_queue = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    queue_text = ""
    now_blocks: list[dict[str, str]] = []
    next_blocks: list[dict[str, str]] = []
    later_blocks: list[dict[str, str]] = []
    closed_titles: list[str] = []
    try:
        queue_text = resolved_queue.read_text(encoding="utf-8")
        now_blocks = queue_lane_blocks(queue_text, "NOW")
        next_blocks = queue_lane_blocks(queue_text, "NEXT")
        later_blocks = queue_lane_blocks(queue_text, "LATER")
        closed_titles = queue_closed_titles(queue_text)
    except OSError as exc:
        errors.append(f"queue read failed: {exc}")

    now_block = now_blocks[0] if now_blocks else live_queue.get("now", {})
    now_title = str(now_block.get("title", "")).strip()
    now_evidence_text = "\n".join(
        part for part in (str(now_block.get("title", "")), str(now_block.get("body", ""))) if part
    )
    existing_titles = [str(block.get("title", "")) for block in [*now_blocks, *next_blocks, *later_blocks]]
    existing_titles.extend(closed_titles)
    latest_status = build_status(record_root, queue_path)
    if latest_status.get("passed") is not True:
        errors.extend(f"status: {error}" for error in latest_status.get("errors", []))

    candidate: dict[str, Any] | None = None
    selector_state = "candidate_ready"
    if live_queue.get("next_step", {}).get("status") in {"route_choice_required", "jenn_decision_required"}:
        selector_state = "blocked_by_jenn_boundary"
    elif not now_title:
        selector_state = "blocked_missing_now"
        errors.append("selector requires a current NOW title")
    elif not errors:
        candidate = selector_candidate_for_now(now_title, now_evidence_text, completed_titles=closed_titles)
        candidate["candidate_id"] = stable_id("NEXTSELECT", [rel(resolved_queue), now_title, candidate.get("title")])
        repeat = title_is_repeat(str(candidate.get("title", "")), existing_titles)
        candidate["not_repeat_of_now"] = not title_is_repeat(str(candidate.get("title", "")), [now_title])
        candidate["not_repeat_of_queue"] = not repeat
        candidate["p3_signals"] = queue_p3_signals(proposed_queue_item_text(candidate))
        if repeat:
            selector_state = "blocked_repeat_detected"
            errors.append("selector candidate repeats an existing NOW/NEXT/LATER item")
        if candidate["p3_signals"]:
            selector_state = "blocked_p3_signals"
            errors.append(f"selector candidate contains P3 signals: {','.join(candidate['p3_signals'])}")

    validation_plan = {
        "level": "fast",
        "normal_progression": [
            "lightweight checks",
            "selector duplicate and P3 checks",
            "affected-file validation",
            "queue sanity",
            "record",
        ],
        "boundary_before_external_write": [
            "targeted registry validation",
            "relevant tests",
        ],
        "external_write_or_publication": [
            "full docctl",
            "full workbench tests",
            "full audit",
        ],
        "full_validation_required_before_external_write": True,
    }
    result = {
        "schema_version": "agents-os.workbench.next-step-selector.v0.1",
        "mode": "next_step_selector_preview",
        "read_only": True,
        "preview_only": True,
        "write_performed": False,
        "active_queue_modified": False,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "raw_queue_body_output": False,
        "source": {
            "queue_path": rel(resolved_queue),
            "record_root": rel(record_root if record_root.is_absolute() else WORKSPACE_ROOT / record_root),
            "current_now_title": now_title,
            "current_now_evidence_scoped": True,
            "live_queue_next_step": live_queue.get("next_step", {}).get("status"),
            "existing_title_count": len([title for title in existing_titles if title]),
            "closed_title_count": len([title for title in closed_titles if title]),
            "latest_record_next_step": latest_status.get("next_step", {}).get("status"),
        },
        "selector_state": selector_state,
        "candidate_present": candidate is not None and selector_state == "candidate_ready",
        "candidate": candidate or {},
        "validation_plan": validation_plan,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_next_step_selector(result)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_next_step_selector(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.next-step-selector.v0.1":
        errors.append("next-step selector schema_version is invalid")
    for flag in ("read_only", "preview_only"):
        if result.get(flag) is not True:
            errors.append(f"next-step selector must keep {flag}=true")
    for flag in (
        "write_performed",
        "active_queue_modified",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_queue_body_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"next-step selector must keep {flag}=false")
    if result.get("candidate_present") is True:
        candidate = result.get("candidate", {})
        if not candidate.get("title"):
            errors.append("next-step selector candidate must include title")
        if candidate.get("not_repeat_of_now") is not True:
            errors.append("next-step selector candidate must not repeat NOW")
        if candidate.get("not_repeat_of_queue") is not True:
            errors.append("next-step selector candidate must not repeat queue")
        if candidate.get("p3_signals"):
            errors.append("next-step selector candidate must not contain P3 signals")
        for key in (
            "substantive_progress",
            "goal_delta",
            "state_delta",
            "why_next",
            "completion_criteria",
            "validation",
            "stop_conditions",
            "blocked_authority",
        ):
            if not candidate.get(key):
                errors.append(f"next-step selector candidate must include {key}")
        if candidate.get("substantive_progress") is not True:
            errors.append("next-step selector candidate must prove substantive progress")
        if len(candidate.get("completion_criteria", [])) < 2:
            errors.append("next-step selector candidate must include at least two completion criteria")
        if len(candidate.get("validation", [])) < 1:
            errors.append("next-step selector candidate must include validation")
        if len(candidate.get("stop_conditions", [])) < 1:
            errors.append("next-step selector candidate must include stop conditions")
    plan = result.get("validation_plan", {})
    if plan.get("level") != "fast":
        errors.append("next-step selector validation plan must default to fast")
    if plan.get("full_validation_required_before_external_write") is not True:
        errors.append("next-step selector must require full validation before external write")
    return errors


RUN_STOP_STATUSES = {
    "route_choice_required",
    "jenn_decision_required",
    "nobao_review_required",
    "review_queue_proposal",
    "stopped_for_review",
    "current_queue_blocked",
}


def goal_state_for_next_step(next_step: dict[str, Any]) -> str:
    status = next_step.get("status")
    if status in RUN_STOP_STATUSES:
        return "waiting_at_boundary"
    if status == "no_advance_records":
        return "not_started"
    return "ready_for_next_run"


def build_live_queue_state(queue_path: Path = DEFAULT_QUEUE) -> dict[str, Any]:
    """Read the current queue so status can detect stale record boundaries."""
    machine = import_module(MACHINE_PATH, "agents_os_machine_live_queue_for_workbench")
    errors: list[str] = []
    normalized_queue = machine.load_queue(queue_path)
    errors.extend(str(error) for error in normalized_queue.get("parse_errors", []) if error)
    machine_preview: dict[str, Any] = {}
    next_step = {
        "status": "queue_unreadable",
        "owner": "Nobao",
        "instruction": "fix queue parse or path errors before continuing",
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
    }
    if normalized_queue.get("passed") is True:
        try:
            machine_preview = machine.build_preview(machine.now_item(normalized_queue))
            preview_errors = machine.validate_preview(machine_preview)
            machine_preview["passed"] = not preview_errors
            machine_preview["errors"] = preview_errors
            errors.extend(f"machine preview: {error}" for error in preview_errors)
            if machine_preview.get("blocked") is True:
                action = machine_preview.get("next_user_action", {})
                status = action.get("status")
                if status == "route_choice_required":
                    next_step = {
                        "status": "route_choice_required",
                        "owner": "Jenn",
                        "decision_owner": "Jenn",
                        "requires_jenn_decision": True,
                        "instruction": action.get("instruction") or "choose_one_route_id",
                        "accepted_route_ids": action.get("accepted_route_ids", []),
                        "template_source_path": action.get("template_source_path"),
                        "exact_confirmation_templates_available": action.get("exact_confirmation_templates_available"),
                        "route_auto_selection_authorized": False,
                        "active_queue_mutation_authorized": False,
                        "queue_promotion_authorized": False,
                        "execution_authorized": False,
                        "write_performed": False,
                        "raw_content_output": False,
                    }
                else:
                    next_step = {
                        "status": "jenn_decision_required",
                        "owner": "Jenn",
                        "decision_owner": "Jenn",
                        "requires_jenn_decision": True,
                        "instruction": "review current NOW denied signals before continuing",
                        "denied_signals": machine_preview.get("denied_signals", []),
                        "active_queue_mutation_authorized": False,
                        "queue_promotion_authorized": False,
                        "execution_authorized": False,
                        "write_performed": False,
                    }
            else:
                next_step = {
                    "status": "queue_ready_for_run",
                    "owner": "Nobao",
                    "instruction": "run workbench advance/run/goal against the current queue",
                    "active_queue_mutation_authorized": False,
                    "queue_promotion_authorized": False,
                    "execution_authorized": False,
                    "write_performed": False,
                }
        except (KeyError, ValueError) as exc:
            errors.append(f"live queue preview failed: {exc}")

    result = {
        "schema_version": "agents-os.workbench.live-queue-state.v0.1",
        "read_only": True,
        "write_performed": False,
        "queue_path": normalized_queue.get("source_path") or rel(queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path),
        "queue_passed": normalized_queue.get("passed"),
        "summary": normalized_queue.get("summary", {}),
        "now": machine_preview.get("source_item", {}) if machine_preview else {},
        "blocked": machine_preview.get("blocked") if machine_preview else None,
        "actionable": machine_preview.get("actionable") if machine_preview else None,
        "denied_signals": machine_preview.get("denied_signals", []) if machine_preview else [],
        "next_step": next_step,
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_live_queue_state(result)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_live_queue_state(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.live-queue-state.v0.1":
        errors.append("live queue state schema_version is invalid")
    if result.get("read_only") is not True:
        errors.append("live queue state must be read_only")
    if result.get("write_performed") is not False:
        errors.append("live queue state must not write")
    if result.get("raw_content_output") is not False:
        errors.append("live queue state must not output raw content")
    if not result.get("next_step", {}).get("status"):
        errors.append("live queue state must emit next_step.status")
    for flag in ("active_queue_mutation_authorized", "queue_promotion_authorized", "execution_authorized", "write_performed"):
        if result.get("next_step", {}).get(flag) is not False:
            errors.append(f"live queue next_step must keep {flag}=false")
    errors.extend(validate_next_user_action_summary("live queue next_step", result.get("next_step", {})))
    return errors


def current_now_internal_intent(queue_path: Path = DEFAULT_QUEUE) -> tuple[str | None, dict[str, Any], list[str]]:
    machine = import_module(MACHINE_PATH, "agents_os_machine_current_now_for_workbench")
    normalized_queue = machine.load_queue(queue_path)
    errors = [str(error) for error in normalized_queue.get("parse_errors", []) if error]
    if normalized_queue.get("passed") is not True:
        return None, {}, errors or ["queue did not pass normalization"]
    try:
        item = machine.now_item(normalized_queue)
    except (KeyError, ValueError) as exc:
        return None, {}, [f"current NOW read failed: {exc}"]
    title = str(item.get("title", "")).strip()
    continue_context = (
        "Workbench continue context: process the current NOW item as a local "
        "validation, report, receipt, and review task."
    )
    intent = "\n\n".join(part for part in (title, continue_context) if part)
    if not intent:
        return None, item, ["current NOW item is empty"]
    return intent, item, []


def build_continue_current(
    queue_path: Path = DEFAULT_QUEUE,
    *,
    validation_command: str = DEFAULT_VALIDATION_COMMAND,
    record_root: Path = DEFAULT_RECORD_ROOT,
    max_steps: int = 1,
    apply_intake: bool = False,
    apply_completion_promotion: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    """Continue from the current live NOW item until the next boundary."""
    live_queue = build_live_queue_state(queue_path)
    errors: list[str] = []
    if live_queue.get("passed") is not True:
        errors.extend(f"live queue: {error}" for error in live_queue.get("errors", []))
    live_next_step = live_queue.get("next_step", {})
    intent: str | None = None
    now_item_payload: dict[str, Any] = {}
    run: dict[str, Any] | None = None
    completion_promotion: dict[str, Any] = {
        "present": False,
        "requested": apply_completion_promotion,
        "write_performed": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
    }
    if not errors and live_next_step.get("status") == "queue_ready_for_run":
        intent, now_item_payload, intent_errors = current_now_internal_intent(queue_path)
        errors.extend(intent_errors)
        if intent and not errors:
            run = build_run(
                intent,
                queue_path,
                validation_command=validation_command,
                record_root=record_root,
                max_steps=max_steps,
                apply_intake=apply_intake,
                allowed_queue_root=allowed_queue_root,
            )
            if run.get("passed") is not True:
                errors.extend(f"run: {error}" for error in run.get("errors", []))
            if apply_completion_promotion:
                can_promote_after_completion = (
                    run.get("passed") is True
                    and run.get("local_safe_execution_count", 0) >= 1
                    and run.get("record_write_count", 0) >= 1
                    and run.get("stopped_reason") == "review_queue_proposal"
                    and run.get("next_step", {}).get("status") == "review_queue_proposal"
                )
                if can_promote_after_completion:
                    completion_promotion = build_queue_promotion_apply_gate(
                        queue_path,
                        apply=True,
                        allowed_queue_root=allowed_queue_root,
                    )
                    completion_promotion["present"] = True
                    completion_promotion["requested"] = True
                    if completion_promotion.get("passed") is not True:
                        errors.extend(
                            f"completion promotion: {error}"
                            for error in completion_promotion.get("errors", [])
                        )
                else:
                    errors.append("completion promotion requires a passed local validation run stopped at review_queue_proposal")

    run_summary = {
        "present": run is not None,
        "run_id": run.get("run_id") if run else None,
        "passed": run.get("passed") if run else None,
        "steps_performed": run.get("steps_performed") if run else 0,
        "local_safe_execution_count": run.get("local_safe_execution_count") if run else 0,
        "record_write_count": run.get("record_write_count") if run else 0,
        "stopped_reason": run.get("stopped_reason") if run else live_next_step.get("status"),
    }
    post_promotion_status: dict[str, Any] | None = None
    if completion_promotion.get("write_performed") is True:
        post_promotion_status = build_status(record_root, queue_path)
        if post_promotion_status.get("passed") is not True:
            errors.extend(f"post promotion status: {error}" for error in post_promotion_status.get("errors", []))
    next_step = run.get("next_step") if run else live_next_step
    if completion_promotion.get("write_performed") is True:
        next_step = {
            "status": "completion_promotion_applied_continue_ready",
            "owner": "Nobao",
            "instruction": "continue current queue again when ready",
            "active_queue_mutation_authorized": True,
            "queue_promotion_authorized": True,
            "execution_authorized": False,
            "write_performed": True,
        }
    result = {
        "schema_version": "agents-os.workbench.continue-current.v0.1",
        "mode": "queue_driven_continue_until_boundary",
        "preview_first": True,
        "source": {
            "queue_path": live_queue.get("queue_path"),
            "current_now_id": (now_item_payload or live_queue.get("now", {})).get("id"),
            "current_now_title": (now_item_payload or live_queue.get("now", {})).get("title"),
            "derived_intent_character_count": len(intent) if intent else 0,
            "derived_intent_raw_output": False,
            "raw_queue_body_output": False,
        },
        "live_queue": live_queue,
        "run": run,
        "run_summary": run_summary,
        "completion_promotion": completion_promotion,
        "post_promotion_status": post_promotion_status,
        "next_step": next_step,
        "write_performed": False,
        "active_queue_modified": (
            completion_promotion.get("active_queue_modified") is True
            or (run.get("active_queue_modified") if run else False)
        ),
        "queue_write_authorized": (
            completion_promotion.get("queue_write_authorized") is True
            or (run.get("queue_write_authorized") if run else False)
        ),
        "queue_promotion_authorized": completion_promotion.get("queue_promotion_authorized") is True,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_continue_current(
        result,
        apply_intake=apply_intake,
        apply_completion_promotion=apply_completion_promotion,
    )
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_continue_current(
    result: dict[str, Any],
    *,
    apply_intake: bool,
    apply_completion_promotion: bool = False,
) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.continue-current.v0.1":
        errors.append("continue current schema_version is invalid")
    if result.get("mode") != "queue_driven_continue_until_boundary":
        errors.append("continue current mode is invalid")
    if result.get("preview_first") is not True:
        errors.append("continue current must remain preview_first")
    source = result.get("source", {})
    if source.get("derived_intent_raw_output") is not False:
        errors.append("continue current must not output derived raw intent")
    if source.get("raw_queue_body_output") is not False:
        errors.append("continue current must not output raw queue body")
    live_errors = validate_live_queue_state(result.get("live_queue", {}))
    errors.extend(f"continue current live queue: {error}" for error in live_errors)
    for flag in (
        "write_performed",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"continue current must keep {flag}=false")
    if not apply_intake and not apply_completion_promotion:
        if result.get("active_queue_modified") is not False:
            errors.append("continue current without apply_intake or completion promotion must not modify queue")
        if result.get("queue_write_authorized") is not False:
            errors.append("continue current without apply_intake or completion promotion must not authorize queue write")
    completion_promotion = result.get("completion_promotion", {})
    if completion_promotion.get("requested") is not apply_completion_promotion:
        errors.append("continue current completion promotion requested flag mismatch")
    if not apply_completion_promotion:
        if result.get("queue_promotion_authorized") is not False:
            errors.append("continue current without completion promotion must not authorize queue promotion")
        if completion_promotion.get("write_performed") is not False:
            errors.append("continue current without completion promotion must not write promotion")
    else:
        if completion_promotion.get("present") is not True:
            errors.append("continue current completion promotion should be present when requested")
        if completion_promotion.get("passed") is not True:
            errors.append("continue current completion promotion must pass when requested")
        else:
            if completion_promotion.get("write_performed") is not True:
                errors.append("continue current completion promotion must write when requested")
            if result.get("queue_promotion_authorized") is not True:
                errors.append("continue current completion promotion must authorize reviewed queue promotion")
            if result.get("active_queue_modified") is not True:
                errors.append("continue current completion promotion must modify queue")
            post_promotion_status = result.get("post_promotion_status") or {}
            if post_promotion_status.get("live_queue", {}).get("next_step", {}).get("status") != "queue_ready_for_run":
                errors.append("continue current completion promotion should leave live queue ready for another run")
    if completion_promotion.get("execution_authorized") is not False:
        errors.append("continue current completion promotion must not authorize execution")
    live_status = result.get("live_queue", {}).get("next_step", {}).get("status")
    run = result.get("run")
    if live_status == "queue_ready_for_run":
        if source.get("derived_intent_character_count", 0) <= 0:
            errors.append("continue current ready queue must derive a NOW intent")
        if not isinstance(run, dict) or run.get("schema_version") != "agents-os.workbench.run.v0.1":
            errors.append("continue current ready queue must include a run payload")
        elif run.get("passed") is not True:
            errors.append("continue current run payload must pass")
    elif run is not None:
        errors.append("continue current must not run when live queue is at a boundary")
    if not result.get("next_step", {}).get("status"):
        errors.append("continue current must emit next_step.status")
    return errors


def build_continue_loop(
    queue_path: Path = DEFAULT_QUEUE,
    *,
    validation_command: str = DEFAULT_VALIDATION_COMMAND,
    record_root: Path = DEFAULT_RECORD_ROOT,
    max_cycles: int = 2,
    apply_completion_promotion: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    """Run queue-driven continue cycles until a boundary or max cycle count."""
    errors: list[str] = []
    if max_cycles < 1:
        errors.append("continue loop max_cycles must be at least 1")
    if max_cycles > 5:
        errors.append("continue loop max_cycles must not exceed 5")

    cycles: list[dict[str, Any]] = []
    local_safe_execution_count = 0
    record_write_count = 0
    completion_promotion_count = 0
    active_queue_modified = False
    queue_write_authorized = False
    queue_promotion_authorized = False
    stopped_reason = "not_started"
    final_next_step: dict[str, Any] = {
        "status": "not_started",
        "owner": "Nobao",
        "instruction": "start continue loop",
    }

    if not errors:
        for index in range(max_cycles):
            live_queue = build_live_queue_state(queue_path)
            if live_queue.get("passed") is not True:
                errors.extend(f"cycle {index + 1} live queue: {error}" for error in live_queue.get("errors", []))
                stopped_reason = "live_queue_failed"
                final_next_step = live_queue.get("next_step", {})
                break
            live_next_step = live_queue.get("next_step", {})
            if live_next_step.get("status") != "queue_ready_for_run":
                stopped_reason = live_next_step.get("status") or "live_queue_boundary"
                final_next_step = live_next_step
                cycles.append(
                    {
                        "cycle_index": index + 1,
                        "performed": False,
                        "reason": stopped_reason,
                        "live_queue_next_step": live_next_step,
                    }
                )
                break

            next_count = int(live_queue.get("summary", {}).get("next_count") or 0)
            request_completion = bool(apply_completion_promotion and next_count > 0)
            current = build_continue_current(
                queue_path,
                validation_command=validation_command,
                record_root=record_root,
                max_steps=1,
                apply_completion_promotion=request_completion,
                allowed_queue_root=allowed_queue_root,
            )
            cycle = {
                "cycle_index": index + 1,
                "performed": True,
                "continue_id": current.get("run_summary", {}).get("run_id"),
                "passed": current.get("passed"),
                "source_now_title": current.get("source", {}).get("current_now_title"),
                "live_queue_next_step_before": live_next_step.get("status"),
                "next_count_before": next_count,
                "completion_promotion_requested": request_completion,
                "completion_promotion_write_performed": current.get("completion_promotion", {}).get("write_performed"),
                "local_safe_execution_count": current.get("run_summary", {}).get("local_safe_execution_count"),
                "record_write_count": current.get("run_summary", {}).get("record_write_count"),
                "next_step": current.get("next_step", {}),
                "errors": current.get("errors", []),
            }
            cycles.append(cycle)
            if current.get("passed") is not True:
                errors.extend(f"cycle {index + 1}: {error}" for error in current.get("errors", []))
                stopped_reason = "continue_failed"
                final_next_step = current.get("next_step", {})
                break
            local_safe_execution_count += int(current.get("run_summary", {}).get("local_safe_execution_count") or 0)
            record_write_count += int(current.get("run_summary", {}).get("record_write_count") or 0)
            if current.get("completion_promotion", {}).get("write_performed") is True:
                completion_promotion_count += 1
            active_queue_modified = active_queue_modified or current.get("active_queue_modified") is True
            queue_write_authorized = queue_write_authorized or current.get("queue_write_authorized") is True
            queue_promotion_authorized = queue_promotion_authorized or current.get("queue_promotion_authorized") is True
            final_next_step = current.get("next_step", {})
            if current.get("completion_promotion", {}).get("write_performed") is True:
                stopped_reason = "max_cycles_reached"
                continue
            stopped_reason = current.get("next_step", {}).get("status") or "continue_boundary"
            break

    final_status = build_status(record_root, queue_path)
    if final_status.get("passed") is not True:
        errors.extend(f"final status: {error}" for error in final_status.get("errors", []))

    result = {
        "schema_version": "agents-os.workbench.continue-loop.v0.1",
        "mode": "queue_driven_continue_loop_until_boundary",
        "preview_first": True,
        "requested_max_cycles": max_cycles,
        "cycles_performed": sum(1 for cycle in cycles if cycle.get("performed") is True),
        "local_safe_execution_count": local_safe_execution_count,
        "record_write_count": record_write_count,
        "completion_promotion_count": completion_promotion_count,
        "stopped_reason": stopped_reason,
        "cycles": cycles,
        "final_status": {
            "passed": final_status.get("passed"),
            "live_queue_next_step": final_status.get("live_queue", {}).get("next_step", {}),
            "advance_record_count": final_status.get("advance_record_count"),
            "latest_advance_id": final_status.get("latest_advance_id"),
        },
        "next_step": final_next_step,
        "write_performed": False,
        "active_queue_modified": active_queue_modified,
        "queue_write_authorized": queue_write_authorized,
        "queue_promotion_authorized": queue_promotion_authorized,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_continue_loop(result, apply_completion_promotion=apply_completion_promotion)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_continue_loop(result: dict[str, Any], *, apply_completion_promotion: bool) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.continue-loop.v0.1":
        errors.append("continue loop schema_version is invalid")
    if result.get("mode") != "queue_driven_continue_loop_until_boundary":
        errors.append("continue loop mode is invalid")
    if result.get("preview_first") is not True:
        errors.append("continue loop must remain preview_first")
    if result.get("cycles_performed", 0) > result.get("requested_max_cycles", 0):
        errors.append("continue loop cannot exceed requested_max_cycles")
    for flag in (
        "write_performed",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"continue loop must keep {flag}=false")
    if not apply_completion_promotion:
        if result.get("active_queue_modified") is not False:
            errors.append("continue loop without completion promotion must not modify queue")
        if result.get("queue_write_authorized") is not False:
            errors.append("continue loop without completion promotion must not authorize queue write")
        if result.get("queue_promotion_authorized") is not False:
            errors.append("continue loop without completion promotion must not authorize queue promotion")
    if result.get("record_write_count", 0) < 1 and result.get("cycles_performed", 0) > 0:
        errors.append("continue loop performed cycles must write records")
    if not result.get("next_step", {}).get("status"):
        errors.append("continue loop must emit next_step.status")
    for cycle in result.get("cycles", []):
        if cycle.get("performed") is True:
            if cycle.get("passed") is not True:
                errors.append(f"continue loop cycle {cycle.get('cycle_index')} must pass")
            if cycle.get("local_safe_execution_count", 0) < 1:
                errors.append(f"continue loop cycle {cycle.get('cycle_index')} must execute local validation")
            if cycle.get("record_write_count", 0) < 1:
                errors.append(f"continue loop cycle {cycle.get('cycle_index')} must write a record")
    return errors


def build_run(
    intent: str,
    queue_path: Path = DEFAULT_QUEUE,
    *,
    validation_command: str = DEFAULT_VALIDATION_COMMAND,
    record_root: Path = DEFAULT_RECORD_ROOT,
    max_steps: int = 1,
    apply_intake: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    initial_status = build_status(record_root, queue_path)
    errors: list[str] = []
    if initial_status.get("passed") is not True:
        errors.extend(f"initial status: {error}" for error in initial_status.get("errors", []))
    if max_steps < 1:
        errors.append("run max_steps must be at least 1")
    if max_steps > 5:
        errors.append("run max_steps must not exceed 5")

    steps: list[dict[str, Any]] = []
    active_queue_modified = False
    queue_write_authorized = False
    local_safe_execution_count = 0
    record_write_count = 0
    stopped_reason = "not_started"
    final_next_step: dict[str, Any] = initial_status.get("next_step", {})

    if not errors:
        for index in range(max_steps):
            advance = build_advance(
                intent,
                queue_path,
                validation_command=validation_command,
                record_root=record_root,
                apply_intake=apply_intake,
                allowed_queue_root=allowed_queue_root,
            )
            advance_next_step = advance.get("stages", {}).get("next_step", {})
            step = {
                "step_index": index + 1,
                "advance_id": advance.get("advance_id"),
                "passed": advance.get("passed"),
                "record_write_performed": advance.get("record_write_performed"),
                "local_safe_execution_performed": advance.get("stages", {}).get("execution", {}).get("local_safe_execution_performed"),
                "verification_performed": advance.get("stages", {}).get("verification", {}).get("performed"),
                "verification_passed": advance.get("stages", {}).get("verification", {}).get("passed"),
                "active_queue_modified": advance.get("active_queue_modified"),
                "queue_write_authorized": advance.get("queue_write_authorized"),
                "queue_promotion_authorized": advance.get("queue_promotion_authorized"),
                "execution_authorized": advance.get("execution_authorized"),
                "provider_call_authorized": advance.get("provider_call_authorized"),
                "service_start_authorized": advance.get("service_start_authorized"),
                "external_write_authorized": advance.get("external_write_authorized"),
                "memory_write_authorized": advance.get("memory_write_authorized"),
                "runtime_plugin_activation_authorized": advance.get("runtime_plugin_activation_authorized"),
                "next_step": advance_next_step,
                "errors": advance.get("errors", []),
            }
            steps.append(step)
            final_next_step = advance_next_step
            active_queue_modified = active_queue_modified or advance.get("active_queue_modified") is True
            queue_write_authorized = queue_write_authorized or advance.get("queue_write_authorized") is True
            if step["local_safe_execution_performed"] is True:
                local_safe_execution_count += 1
            if step["record_write_performed"] is True:
                record_write_count += 1
            if advance.get("passed") is not True:
                errors.extend(f"advance step {index + 1}: {error}" for error in advance.get("errors", []))
                stopped_reason = "advance_failed"
                break
            status_value = advance_next_step.get("status")
            if status_value in RUN_STOP_STATUSES:
                stopped_reason = status_value
                break
            stopped_reason = "max_steps_reached"

    final_status = build_status(record_root, queue_path)
    if final_status.get("passed") is not True:
        errors.extend(f"final status: {error}" for error in final_status.get("errors", []))

    result = {
        "schema_version": "agents-os.workbench.run.v0.1",
        "run_id": stable_id(
            "RUN",
            [
                intent,
                rel(queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path),
                validation_command,
                record_root.as_posix(),
                max_steps,
                apply_intake,
                [step.get("advance_id") for step in steps],
            ],
        ),
        "mode": "automatic_until_boundary",
        "preview_first": True,
        "requested_max_steps": max_steps,
        "steps_performed": len(steps),
        "local_safe_execution_count": local_safe_execution_count,
        "record_write_count": record_write_count,
        "stopped_reason": stopped_reason,
        "initial_status": {
            "passed": initial_status.get("passed"),
            "advance_record_count": initial_status.get("advance_record_count"),
            "next_step": initial_status.get("next_step", {}),
        },
        "final_status": {
            "passed": final_status.get("passed"),
            "advance_record_count": final_status.get("advance_record_count"),
            "latest_advance_id": final_status.get("latest_advance_id"),
            "next_step": final_status.get("next_step", {}),
        },
        "steps": steps,
        "next_step": final_next_step,
        "write_performed": False,
        "active_queue_modified": active_queue_modified,
        "queue_write_authorized": queue_write_authorized,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_run(result, apply_intake=apply_intake)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_run(result: dict[str, Any], *, apply_intake: bool) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.run.v0.1":
        errors.append("workbench run schema_version is invalid")
    if result.get("mode") != "automatic_until_boundary":
        errors.append("workbench run mode must be automatic_until_boundary")
    if result.get("preview_first") is not True:
        errors.append("workbench run must remain preview_first")
    if result.get("steps_performed", 0) < 1:
        errors.append("workbench run must perform at least one step")
    if result.get("steps_performed", 0) > result.get("requested_max_steps", 0):
        errors.append("workbench run cannot exceed requested_max_steps")
    for flag in (
        "write_performed",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"workbench run must keep {flag}=false")
    if not apply_intake:
        if result.get("active_queue_modified") is not False:
            errors.append("workbench run without apply_intake must not modify queue")
        if result.get("queue_write_authorized") is not False:
            errors.append("workbench run without apply_intake must not authorize queue write")
    if result.get("record_write_count", 0) < 1:
        errors.append("workbench run must write at least one local record")
    for step in result.get("steps", []):
        if step.get("queue_promotion_authorized") is not False:
            errors.append("workbench run step must not authorize queue promotion")
        if step.get("execution_authorized") is not False:
            errors.append("workbench run step must not authorize dangerous execution")
        if step.get("provider_call_authorized") is not False:
            errors.append("workbench run step must not authorize provider call")
        if step.get("service_start_authorized") is not False:
            errors.append("workbench run step must not authorize service start")
        if step.get("external_write_authorized") is not False:
            errors.append("workbench run step must not authorize external write")
        if step.get("memory_write_authorized") is not False:
            errors.append("workbench run step must not authorize Memory write")
        if step.get("runtime_plugin_activation_authorized") is not False:
            errors.append("workbench run step must not authorize runtime/plugin activation")
        if not step.get("next_step", {}).get("status"):
            errors.append("workbench run step must emit next_step.status")
    if not result.get("next_step", {}).get("status"):
        errors.append("workbench run must emit next_step.status")
    return errors


def build_goal_session(
    objective: str,
    queue_path: Path = DEFAULT_QUEUE,
    *,
    validation_command: str = DEFAULT_VALIDATION_COMMAND,
    record_root: Path = DEFAULT_RECORD_ROOT,
    max_steps: int = 1,
    apply_intake: bool = False,
    allowed_queue_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    """Enter a long-running goal and advance it until the next boundary."""
    run = build_run(
        objective,
        queue_path,
        validation_command=validation_command,
        record_root=record_root,
        max_steps=max_steps,
        apply_intake=apply_intake,
        allowed_queue_root=allowed_queue_root,
    )
    resolved_queue = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    goal_session_id = stable_id(
        "GOALSESSION",
        [
            objective,
            rel(resolved_queue),
            validation_command,
            record_root.as_posix(),
            max_steps,
            apply_intake,
            run.get("run_id"),
        ],
    )
    session_record_path = record_root / f"{goal_session_id.lower()}.json"
    next_step = run.get("next_step", {})
    route_choice_readiness = build_route_choice_readiness(next_step)
    result = {
        "schema_version": "agents-os.workbench.goal-session.v0.1",
        "goal_session_id": goal_session_id,
        "mode": "goal_to_automatic_until_boundary",
        "preview_first": True,
        "source": {
            "objective_character_count": len(objective),
            "objective_raw_output": False,
            "queue_path": rel(resolved_queue),
        },
        "goal_state": goal_state_for_next_step(next_step),
        "run": run,
        "run_summary": {
            "run_id": run.get("run_id"),
            "passed": run.get("passed"),
            "mode": run.get("mode"),
            "steps_performed": run.get("steps_performed"),
            "local_safe_execution_count": run.get("local_safe_execution_count"),
            "record_write_count": run.get("record_write_count"),
            "stopped_reason": run.get("stopped_reason"),
        },
        "route_choice_readiness": route_choice_readiness,
        "record": {
            "write_performed": False,
            "record_write_authorized": False,
            "record_path": rel(session_record_path),
        },
        "next_step": next_step,
        "write_performed": False,
        "active_queue_modified": run.get("active_queue_modified"),
        "queue_write_authorized": run.get("queue_write_authorized"),
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "raw_content_output": False,
        "errors": [],
    }
    if run.get("passed") is not True:
        result["errors"].extend(f"run: {error}" for error in run.get("errors", []))
    if route_choice_readiness.get("passed") is not True:
        result["errors"].extend(f"route choice readiness: {error}" for error in route_choice_readiness.get("errors", []))
    result["errors"].extend(validate_goal_session(result, apply_intake=apply_intake, require_goal_record=False))
    result["errors"] = sorted(set(result["errors"]))
    if not result["errors"]:
        resolved_record, record_error = resolve_record_path(session_record_path, record_root)
        if record_error or resolved_record is None:
            result["errors"].append(f"goal session record write: {record_error or 'record path is not allowed'}")
        else:
            try:
                result["record"]["write_performed"] = True
                result["record"]["record_write_authorized"] = True
                result["record"]["record_path"] = rel(resolved_record)
                resolved_record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                result["record"]["write_performed"] = False
                result["record"]["record_write_authorized"] = False
                result["errors"].append(f"goal session record write failed: {exc}")
    result["errors"] = sorted(set(result["errors"] + validate_goal_session(result, apply_intake=apply_intake)))
    result["passed"] = not result["errors"]
    if result["passed"] and result["record"]["write_performed"] is True:
        resolved_record, record_error = resolve_record_path(Path(result["record"]["record_path"]), record_root)
        if record_error or resolved_record is None:
            result["record"]["write_performed"] = False
            result["record"]["record_write_authorized"] = False
            result["errors"].append(f"goal session record final write: {record_error or 'record path is not allowed'}")
            result["passed"] = False
        else:
            try:
                resolved_record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                result["record"]["write_performed"] = False
                result["record"]["record_write_authorized"] = False
                result["errors"].append(f"goal session record final write failed: {exc}")
                result["passed"] = False
    return result


def validate_goal_session(
    result: dict[str, Any],
    *,
    apply_intake: bool,
    require_goal_record: bool = True,
) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.workbench.goal-session.v0.1":
        errors.append("workbench goal session schema_version is invalid")
    if result.get("mode") != "goal_to_automatic_until_boundary":
        errors.append("workbench goal session mode is invalid")
    if result.get("preview_first") is not True:
        errors.append("workbench goal session must remain preview_first")
    source = result.get("source", {})
    if source.get("objective_character_count", 0) <= 0:
        errors.append("workbench goal session must receive a non-empty objective")
    if source.get("objective_raw_output") is not False:
        errors.append("workbench goal session must not output raw objective text")
    run = result.get("run", {})
    if run.get("schema_version") != "agents-os.workbench.run.v0.1":
        errors.append("workbench goal session must include a run payload")
    if run.get("passed") is not True:
        errors.append("workbench goal session run must pass")
    if result.get("goal_state") != goal_state_for_next_step(result.get("next_step", {})):
        errors.append("workbench goal session goal_state does not match next_step")
    record = result.get("record", {})
    if require_goal_record:
        if record.get("write_performed") is not True:
            errors.append("workbench goal session must write a local goal record")
        if record.get("record_write_authorized") is not True:
            errors.append("workbench goal session record write must be authorized")
        if not record.get("record_path"):
            errors.append("workbench goal session record path is required")
    for flag in (
        "write_performed",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"workbench goal session must keep {flag}=false")
    if not apply_intake:
        if result.get("active_queue_modified") is not False:
            errors.append("workbench goal session without apply_intake must not modify queue")
        if result.get("queue_write_authorized") is not False:
            errors.append("workbench goal session without apply_intake must not authorize queue write")
    if not result.get("next_step", {}).get("status"):
        errors.append("workbench goal session must emit next_step.status")
    route_choice_errors = validate_route_choice_readiness(result.get("route_choice_readiness", {}))
    errors.extend(f"route choice readiness: {error}" for error in route_choice_errors)
    return errors


def fixture_queue_text(title: str = "Write local governance report") -> str:
    return f"""# workbench fixture queue

## NOW

### NOW-001: {title}

Run local validation and prepare proposal-only queue output.

## NEXT

### NEXT-001: Safe follow-up task

Write local governance report.

## LATER

### LATER-001: Later task

Wait.

## BLOCKED

```text
provider_calls: blocked until explicit provider boundary
```

## CLOSED

```text
old_task: closed
```
"""


def fixture_loop_queue_text() -> str:
    return """# workbench loop fixture queue

## NOW

### NOW-001: Write local governance report

Run local validation and prepare proposal-only queue output.

## NEXT

### NEXT-001: Safe follow-up task

Write local governance report.

### NEXT-002: Second safe follow-up task

Write local governance report.

## LATER

### LATER-001: Later task

Wait.

## BLOCKED

```text
provider_calls: blocked until explicit provider boundary
```

## CLOSED

```text
old_task: closed
```
"""


def fixture_route_stop_queue_text() -> str:
    return """# workbench route stop fixture queue

## NOW

### NOW-001: No Active Automatic Construction Item

Waiting for Jenn route selection.

## NEXT

_No active NEXT items._

## LATER

## BLOCKED

```text
provider_calls: blocked until explicit provider boundary
```

## CLOSED

```text
old_task: closed
```
"""


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("default_mode") != "cycle_preview":
        errors.append("manifest default_mode must be cycle_preview")
    if "goal" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include goal")
    if "continue" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include continue")
    if "loop" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include loop")
    if "audit" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include audit")
    if "select-next-step" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include select-next-step")
    if "route-choice-preview" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include route-choice-preview")
    if "route-choice-apply-gate" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include route-choice-apply-gate")
    if "queue-promotion-apply-gate" not in manifest.get("allowed_modes", []):
        errors.append("manifest allowed_modes must include queue-promotion-apply-gate")
    if "goal_session" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include goal_session")
    if "route_choice_preview" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include route_choice_preview")
    if "route_choice_apply_gate" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include route_choice_apply_gate")
    if "queue_promotion_apply_gate" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include queue_promotion_apply_gate")
    if "live_queue_status" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include live_queue_status")
    if "status_reconciliation" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include status_reconciliation")
    if "continue_current" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include continue_current")
    if "continue_loop" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include continue_loop")
    if "completion_promotion_apply_gate" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include completion_promotion_apply_gate")
    if "completion_audit" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include completion_audit")
    if "next_step_selector" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include next_step_selector")
    if "fast_validation" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include fast_validation")
    if "targeted_validation" not in manifest.get("loop_stages", []):
        errors.append("manifest loop_stages must include targeted_validation")
    defaults = manifest.get("dangerous_authorization_defaults", {})
    failures = false_flag_failures(defaults)
    if failures:
        errors.append(f"manifest dangerous authorization defaults not false: {','.join(failures)}")
    return errors


def validate_workbench() -> dict[str, Any]:
    started_at = time.monotonic()
    errors = validate_manifest(load_json(MANIFEST_PATH))
    fast_validation = validate_workbench_fast()
    if fast_validation.get("passed") is not True:
        errors.extend(f"fast validation: {error}" for error in fast_validation.get("errors", []))

    stopped_cycle: dict[str, Any] = {}
    safe_cycle: dict[str, Any] = {}
    provider_cycle: dict[str, Any] = {}
    recorded_cycle: dict[str, Any] = {}
    blocked_record_cycle: dict[str, Any] = {}
    intake_preview: dict[str, Any] = {}
    intake_apply: dict[str, Any] = {}
    blocked_provider_intake: dict[str, Any] = {}
    blocked_p3_intake: dict[str, Any] = {}
    stopped_advance: dict[str, Any] = {}
    safe_advance: dict[str, Any] = {}
    advance_with_intake: dict[str, Any] = {}
    provider_advance: dict[str, Any] = {}
    record_file_written = False
    record_payload_matches = False
    safe_advance_record_payload_matches = False
    safe_advance_record_final_passed = False
    safe_advance_cycle_record_written = False
    advance_with_intake_record_captures_intake = False
    empty_status: dict[str, Any] = {}
    safe_status: dict[str, Any] = {}
    status_after_intake: dict[str, Any] = {}
    stopped_run: dict[str, Any] = {}
    safe_run: dict[str, Any] = {}
    run_with_intake: dict[str, Any] = {}
    stopped_goal: dict[str, Any] = {}
    safe_goal: dict[str, Any] = {}
    route_choice_preview: dict[str, Any] = {}
    route_choice_apply_preview: dict[str, Any] = {}
    route_choice_apply: dict[str, Any] = {}
    queue_promotion_preview: dict[str, Any] = {}
    queue_promotion_apply: dict[str, Any] = {}
    route_promotion_status: dict[str, Any] = {}
    route_promotion_continue: dict[str, Any] = {}
    continue_with_completion: dict[str, Any] = {}
    continue_loop: dict[str, Any] = {}
    continue_completion_queue_promoted = False
    continue_loop_queue_promoted_second = False
    route_promotion_queue_contains_promoted_now = False
    temp_cleaned = False
    fixture_validation_command = "python3 --version"
    docctl_probe: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="agents-os-workbench-test-", dir=WORKSPACE_ROOT) as temp_dir:
        queue_path = Path(temp_dir) / "queue.md"
        queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        stopped_queue_path = Path(temp_dir) / "stopped-queue.md"
        stopped_queue_path.write_text(fixture_route_stop_queue_text(), encoding="utf-8")
        advance_record_root = Path(temp_dir) / "advance-records"
        advance_record_root.mkdir()
        route_continue_record_root = Path(temp_dir) / "route-continue-records"
        route_continue_record_root.mkdir()
        empty_status = build_status(advance_record_root)
        stopped_cycle = build_cycle(
            "Build AGENTS OS into a local automatic workbench.",
            stopped_queue_path,
            run_local_validation=True,
            validation_command=fixture_validation_command,
        )
        safe_cycle = build_cycle(
            "Write local governance report and run docctl validation.",
            queue_path,
            run_local_validation=True,
            validation_command=fixture_validation_command,
        )
        provider_cycle = build_cycle(
            "Call provider and start service.",
            queue_path,
            run_local_validation=True,
            validation_command=fixture_validation_command,
        )
        intake_review = accepted_nobao_review_for_intake(safe_cycle.get("stages", {}).get("intake_proposal", {}))
        intake_preview = reviewed_intake_apply_gate(
            safe_cycle.get("stages", {}).get("intake_proposal", {}),
            intake_review,
            queue_path,
            apply=False,
            allowed_queue_root=Path(temp_dir),
        )
        intake_apply = reviewed_intake_apply_gate(
            safe_cycle.get("stages", {}).get("intake_proposal", {}),
            intake_review,
            queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        provider_review = accepted_nobao_review_for_intake(provider_cycle.get("stages", {}).get("intake_proposal", {}))
        blocked_provider_intake = reviewed_intake_apply_gate(
            provider_cycle.get("stages", {}).get("intake_proposal", {}),
            provider_review,
            queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        stopped_advance = build_advance(
            "Build AGENTS OS into a local automatic workbench.",
            stopped_queue_path,
            validation_command=fixture_validation_command,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        stopped_run = build_run(
            "Build AGENTS OS into a local automatic workbench.",
            stopped_queue_path,
            validation_command=fixture_validation_command,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        stopped_goal = build_goal_session(
            "Build AGENTS OS into a local automatic workbench.",
            stopped_queue_path,
            validation_command=fixture_validation_command,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        advance_queue_path = Path(temp_dir) / "advance-queue.md"
        advance_queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        safe_advance = build_advance(
            "Write local governance report and run docctl validation.",
            advance_queue_path,
            validation_command=fixture_validation_command,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        run_queue_path = Path(temp_dir) / "run-queue.md"
        run_queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        safe_run = build_run(
            "Write local governance report and run docctl validation.",
            run_queue_path,
            validation_command="python3 --version",
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        goal_queue_path = Path(temp_dir) / "goal-queue.md"
        goal_queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        safe_goal = build_goal_session(
            "Write local governance report and run docctl validation.",
            goal_queue_path,
            validation_command="python3 --version",
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        route_choice_queue_path = Path(temp_dir) / "route-choice-queue.md"
        route_choice_queue_path.write_text(fixture_route_stop_queue_text(), encoding="utf-8")
        route_choice_text = (
            "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
            "先准备 formal Memory candidate gate v0.1；只做候选和确认模型，不写正式 Memory，\n"
            "不读 private raw Memory，不读 state-private/，并保留 receipt/review/validation。"
        )
        route_choice_preview = build_route_choice_preview(route_choice_text, route_choice_queue_path)
        route_apply_queue_path = Path(temp_dir) / "route-apply-queue.md"
        route_apply_queue_path.write_text(fixture_route_stop_queue_text(), encoding="utf-8")
        route_choice_apply_preview = build_route_choice_apply_gate(
            route_choice_text,
            route_apply_queue_path,
            apply=False,
            allowed_queue_root=Path(temp_dir),
        )
        route_choice_apply = build_route_choice_apply_gate(
            route_choice_text,
            route_apply_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        queue_promotion_preview = build_queue_promotion_apply_gate(
            route_apply_queue_path,
            apply=False,
            allowed_queue_root=Path(temp_dir),
        )
        queue_promotion_apply = build_queue_promotion_apply_gate(
            route_apply_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        route_promotion_queue_contains_promoted_now = (
            "### NOW-001: AGENTS OS formal Memory candidate gate v0.1"
            in route_apply_queue_path.read_text(encoding="utf-8")
        )
        route_promotion_status = build_status(advance_record_root, route_apply_queue_path)
        route_promotion_continue = build_continue_current(
            route_apply_queue_path,
            validation_command="python3 --version",
            record_root=route_continue_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        continue_completion_queue_path = Path(temp_dir) / "continue-completion-queue.md"
        continue_completion_queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        continue_completion_record_root = Path(temp_dir) / "continue-completion-records"
        continue_completion_record_root.mkdir()
        continue_with_completion = build_continue_current(
            continue_completion_queue_path,
            validation_command="python3 --version",
            record_root=continue_completion_record_root,
            apply_completion_promotion=True,
            allowed_queue_root=Path(temp_dir),
        )
        continue_completion_queue_promoted = (
            "### NOW-001: Safe follow-up task"
            in continue_completion_queue_path.read_text(encoding="utf-8")
        )
        continue_loop_queue_path = Path(temp_dir) / "continue-loop-queue.md"
        continue_loop_queue_path.write_text(fixture_loop_queue_text(), encoding="utf-8")
        continue_loop_record_root = Path(temp_dir) / "continue-loop-records"
        continue_loop_record_root.mkdir()
        continue_loop = build_continue_loop(
            continue_loop_queue_path,
            validation_command="python3 --version",
            record_root=continue_loop_record_root,
            max_cycles=2,
            apply_completion_promotion=True,
            allowed_queue_root=Path(temp_dir),
        )
        continue_loop_queue_promoted_second = (
            "### NOW-001: Second safe follow-up task"
            in continue_loop_queue_path.read_text(encoding="utf-8")
        )
        safe_status = build_status(advance_record_root)
        advance_apply_queue_path = Path(temp_dir) / "advance-apply-queue.md"
        advance_apply_queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        advance_with_intake = build_advance(
            "Write local governance report and run docctl validation.",
            advance_apply_queue_path,
            validation_command=fixture_validation_command,
            record_root=advance_record_root,
            apply_intake=True,
            allowed_queue_root=Path(temp_dir),
        )
        run_apply_queue_path = Path(temp_dir) / "run-apply-queue.md"
        run_apply_queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        run_with_intake = build_run(
            "Write local governance report and run docctl validation.",
            run_apply_queue_path,
            validation_command=fixture_validation_command,
            record_root=advance_record_root,
            apply_intake=True,
            allowed_queue_root=Path(temp_dir),
        )
        status_after_intake = build_status(advance_record_root)
        safe_advance_record_name = Path(
            safe_advance.get("stages", {}).get("record", {}).get("record_path", "")
        ).name
        safe_advance_record_path = advance_record_root / safe_advance_record_name
        if safe_advance_record_name and safe_advance_record_path.exists() and safe_advance_record_path.is_file():
            safe_advance_payload = load_json(safe_advance_record_path)
            safe_advance_record_payload_matches = (
                safe_advance_payload.get("schema_version") == "agents-os.workbench.advance.v0.1"
                and safe_advance_payload.get("advance_id") == safe_advance.get("advance_id")
            )
            safe_advance_record_final_passed = safe_advance_payload.get("passed") is True
        safe_advance_cycle_record_name = Path(
            safe_advance.get("stages", {}).get("record", {}).get("cycle_record_path", "")
        ).name
        safe_advance_cycle_record_path = advance_record_root / safe_advance_cycle_record_name
        safe_advance_cycle_record_written = (
            bool(safe_advance_cycle_record_name)
            and safe_advance_cycle_record_path.exists()
            and safe_advance_cycle_record_path.is_file()
        )
        advance_with_intake_record_name = Path(
            advance_with_intake.get("stages", {}).get("record", {}).get("record_path", "")
        ).name
        advance_with_intake_record_path = advance_record_root / advance_with_intake_record_name
        if advance_with_intake_record_name and advance_with_intake_record_path.exists() and advance_with_intake_record_path.is_file():
            advance_with_intake_payload = load_json(advance_with_intake_record_path)
            advance_with_intake_record_captures_intake = (
                advance_with_intake_payload.get("stages", {}).get("intake_apply", {}).get("write_performed") is True
            )
        provider_advance = build_advance(
            "Call provider and start service.",
            queue_path,
            validation_command=fixture_validation_command,
            record_root=advance_record_root,
            allowed_queue_root=Path(temp_dir),
        )
        p3_queue_path = Path(temp_dir) / "p3-queue.md"
        p3_queue_path.write_text(fixture_queue_text(), encoding="utf-8")
        p3_cycle = build_cycle(
            "Write local governance report and run docctl validation.",
            p3_queue_path,
            run_local_validation=True,
            validation_command=fixture_validation_command,
        )
        p3_proposal = dict(p3_cycle.get("stages", {}).get("intake_proposal", {}))
        p3_item = dict(p3_proposal.get("proposed_queue_item", {}))
        p3_item["title"] = "Publish report to GitHub release"
        p3_proposal["proposed_queue_item"] = p3_item
        p3_review = accepted_nobao_review_for_intake(p3_proposal)
        blocked_p3_intake = reviewed_intake_apply_gate(
            p3_proposal,
            p3_review,
            p3_queue_path,
            apply=True,
            allowed_queue_root=Path(temp_dir),
        )
        record_path = Path(temp_dir) / "records" / "safe-cycle-record.json"
        record_path.parent.mkdir()
        recorded_cycle = build_cycle(
            "Write local governance report and run docctl validation.",
            queue_path,
            run_local_validation=True,
            validation_command=fixture_validation_command,
            write_record=True,
            record_path=record_path,
            allowed_record_root=record_path.parent,
        )
        blocked_record_cycle = build_cycle(
            "Write local governance report and run docctl validation.",
            queue_path,
            run_local_validation=True,
            validation_command=fixture_validation_command,
            write_record=True,
            record_path=Path(temp_dir) / "outside-record.json",
            allowed_record_root=record_path.parent,
        )
        record_file_written = record_path.exists()
        if record_file_written:
            recorded_payload = load_json(record_path)
            record_payload_matches = (
                recorded_payload.get("record_id")
                == recorded_cycle.get("stages", {}).get("record", {}).get("record_id")
            )
    temp_cleaned = "temp_dir" in locals() and not Path(temp_dir).exists()
    docctl_probe = run_validation_probe(
        [
            sys.executable,
            "control-plane/registry/docctl.py",
            "status",
        ],
        timeout_seconds=600,
    )

    if safe_cycle.get("passed") is not True:
        errors.extend(f"safe cycle: {error}" for error in safe_cycle.get("errors", []))
    if safe_cycle.get("stages", {}).get("local_validation", {}).get("performed") is not True:
        errors.append("safe cycle should perform local validation")
    if safe_cycle.get("stages", {}).get("local_validation", {}).get("passed") is not True:
        errors.append("safe cycle local validation should pass")
    if safe_cycle.get("stages", {}).get("queue_proposal", {}).get("proposal_only") is not True:
        errors.append("safe cycle should produce proposal-only queue output")
    if safe_cycle.get("stages", {}).get("intake_proposal", {}).get("can_apply_after_review") is not True:
        errors.append("safe cycle intake should be applicable after review")
    if safe_cycle.get("stages", {}).get("intake_proposal", {}).get("active_queue_modified") is not False:
        errors.append("safe cycle intake must not mutate queue")
    if safe_cycle.get("stages", {}).get("record", {}).get("stage_receipts", {}).get("queue_proposal_present") is not True:
        errors.append("safe cycle record should capture queue proposal presence")
    if safe_cycle.get("stages", {}).get("record", {}).get("write_performed") is not False:
        errors.append("safe cycle record must not write")
    if safe_cycle.get("stages", {}).get("next_step", {}).get("status") != "review_queue_proposal":
        errors.append("safe cycle should end at review_queue_proposal")

    if provider_cycle.get("passed") is not True:
        errors.extend(f"provider cycle: {error}" for error in provider_cycle.get("errors", []))
    if provider_cycle.get("stages", {}).get("judgment", {}).get("decision") != "stop_needs_jenn_decision":
        errors.append("provider cycle should stop for Jenn decision")
    if provider_cycle.get("stages", {}).get("intake_proposal", {}).get("candidate_requires_jenn_decision") is not True:
        errors.append("provider cycle intake should require Jenn decision")
    if provider_cycle.get("stages", {}).get("intake_proposal", {}).get("can_apply_after_review") is not False:
        errors.append("provider cycle intake must not be applicable")
    if provider_cycle.get("stages", {}).get("local_validation", {}).get("performed") is not False:
        errors.append("provider cycle must not run local validation")
    if intake_preview.get("passed") is not True:
        errors.extend(f"intake preview: {error}" for error in intake_preview.get("errors", []))
    if intake_preview.get("write_performed") is not False:
        errors.append("intake preview must not write")
    if intake_preview.get("queue_write_authorized") is not False:
        errors.append("intake preview must not authorize queue write")
    if intake_apply.get("passed") is not True:
        errors.extend(f"intake apply: {error}" for error in intake_apply.get("errors", []))
    if intake_apply.get("write_performed") is not True:
        errors.append("intake apply should write fixture queue")
    if intake_apply.get("queue_promotion_authorized") is not False:
        errors.append("intake apply must not authorize queue promotion")
    if intake_apply.get("execution_authorized") is not False:
        errors.append("intake apply must not authorize execution")
    if blocked_provider_intake.get("passed") is not False:
        errors.append("provider intake apply should fail")
    if blocked_provider_intake.get("write_performed") is not False:
        errors.append("provider intake apply must not write")
    if blocked_p3_intake.get("passed") is not False:
        errors.append("P3 intake apply should fail")
    if blocked_p3_intake.get("write_performed") is not False:
        errors.append("P3 intake apply must not write")
    if stopped_cycle.get("passed") is not True:
        errors.extend(f"stopped cycle: {error}" for error in stopped_cycle.get("errors", []))
    if stopped_cycle.get("stages", {}).get("next_step", {}).get("status") != "route_choice_required":
        errors.append("stopped cycle should report route_choice_required")
    if stopped_cycle.get("stages", {}).get("next_step", {}).get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("stopped cycle should expose route choices A-E")
    if stopped_cycle.get("stages", {}).get("next_step", {}).get("exact_confirmation_templates_available") is not True:
        errors.append("stopped cycle should expose confirmation template availability")
    if stopped_cycle.get("stages", {}).get("next_step", {}).get("route_auto_selection_authorized") is not False:
        errors.append("stopped cycle must not authorize route auto-selection")
    if stopped_cycle.get("stages", {}).get("local_validation", {}).get("performed") is not False:
        errors.append("stopped cycle must not run local validation while NOW is blocked")
    if stopped_advance.get("passed") is not True:
        errors.extend(f"stopped advance: {error}" for error in stopped_advance.get("errors", []))
    if stopped_advance.get("stages", {}).get("execution", {}).get("local_safe_execution_performed") is not False:
        errors.append("stopped advance must not perform local-safe execution")
    if stopped_advance.get("stages", {}).get("next_step", {}).get("status") != "route_choice_required":
        errors.append("stopped advance should report route_choice_required")
    if stopped_advance.get("record_write_performed") is not True:
        errors.append("stopped advance should write a local record")
    if stopped_run.get("passed") is not True:
        errors.extend(f"stopped run: {error}" for error in stopped_run.get("errors", []))
    if stopped_run.get("next_step", {}).get("status") != "route_choice_required":
        errors.append("stopped run should stop at route_choice_required")
    if stopped_run.get("local_safe_execution_count") != 0:
        errors.append("stopped run must not perform local-safe execution")
    if stopped_run.get("record_write_count") != 1:
        errors.append("stopped run should write exactly one record")
    if stopped_goal.get("passed") is not True:
        errors.extend(f"stopped goal: {error}" for error in stopped_goal.get("errors", []))
    if stopped_goal.get("next_step", {}).get("status") != "route_choice_required":
        errors.append("stopped goal should stop at route_choice_required")
    if stopped_goal.get("goal_state") != "waiting_at_boundary":
        errors.append("stopped goal should wait at boundary")
    if stopped_goal.get("record", {}).get("write_performed") is not True:
        errors.append("stopped goal should write a goal session record")
    if stopped_goal.get("route_choice_readiness", {}).get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("stopped goal should surface route choices A-E")
    if stopped_goal.get("route_choice_readiness", {}).get("option_count") != 5:
        errors.append("stopped goal should surface five route options")
    if stopped_goal.get("route_choice_readiness", {}).get("raw_template_output") is not False:
        errors.append("stopped goal must not output raw route templates")
    if empty_status.get("passed") is not True:
        errors.extend(f"empty status: {error}" for error in empty_status.get("errors", []))
    if empty_status.get("next_step", {}).get("status") != "no_advance_records":
        errors.append("empty status should report no_advance_records")
    if empty_status.get("goal_session_count") != 0:
        errors.append("empty status should report no goal sessions")
    if safe_advance.get("passed") is not True:
        errors.extend(f"safe advance: {error}" for error in safe_advance.get("errors", []))
    if safe_advance.get("stages", {}).get("execution", {}).get("local_safe_execution_performed") is not True:
        errors.append("safe advance should perform local-safe execution")
    if safe_advance.get("stages", {}).get("verification", {}).get("passed") is not True:
        errors.append("safe advance verification should pass")
    if safe_advance.get("record_write_performed") is not True:
        errors.append("safe advance should write a local record")
    if safe_advance.get("advance_record_write_performed") is not True:
        errors.append("safe advance should write an advance record")
    if not safe_advance_record_payload_matches:
        errors.append("safe advance record file should contain matching advance payload")
    if not safe_advance_record_final_passed:
        errors.append("safe advance record file should include final passed=true")
    if not safe_advance_cycle_record_written:
        errors.append("safe advance should also write a cycle record")
    if safe_advance.get("active_queue_modified") is not False:
        errors.append("safe advance without apply_intake must not mutate queue")
    if safe_run.get("passed") is not True:
        errors.extend(f"safe run: {error}" for error in safe_run.get("errors", []))
    if safe_run.get("local_safe_execution_count") != 1:
        errors.append("safe run should perform one local-safe execution")
    if safe_run.get("next_step", {}).get("status") != "review_queue_proposal":
        errors.append("safe run should stop at review_queue_proposal")
    if safe_run.get("active_queue_modified") is not False:
        errors.append("safe run without apply_intake must not modify queue")
    if safe_goal.get("passed") is not True:
        errors.extend(f"safe goal: {error}" for error in safe_goal.get("errors", []))
    if safe_goal.get("run_summary", {}).get("local_safe_execution_count") != 1:
        errors.append("safe goal should perform one local-safe execution")
    if safe_goal.get("next_step", {}).get("status") != "review_queue_proposal":
        errors.append("safe goal should stop at review_queue_proposal")
    if safe_goal.get("record", {}).get("write_performed") is not True:
        errors.append("safe goal should write a goal session record")
    if safe_goal.get("route_choice_readiness", {}).get("present") is not False:
        errors.append("safe goal should not surface route choice readiness")
    if safe_status.get("passed") is not True:
        errors.extend(f"safe status: {error}" for error in safe_status.get("errors", []))
    if safe_status.get("latest_advance_id") != safe_goal.get("run", {}).get("steps", [{}])[-1].get("advance_id"):
        errors.append("safe status should report safe goal advance as latest")
    if safe_status.get("next_step", {}).get("status") != "review_queue_proposal":
        errors.append("safe status should surface review_queue_proposal")
    if safe_status.get("write_performed") is not False:
        errors.append("safe status must not write")
    if safe_status.get("goal_session_count") != 2:
        errors.append("safe status should count stopped and safe goal sessions")
    if safe_status.get("latest_goal_session", {}).get("goal_session_id") != safe_goal.get("goal_session_id"):
        errors.append("safe status should surface latest goal session id")
    if safe_status.get("latest_goal_session", {}).get("goal_state") != "waiting_at_boundary":
        errors.append("safe status should surface latest goal state")
    if safe_status.get("latest_goal_session", {}).get("next_step", {}).get("status") != "review_queue_proposal":
        errors.append("safe status should surface latest goal next step")
    if safe_status.get("latest_goal_session", {}).get("objective_raw_output") is not False:
        errors.append("safe status must not expose raw goal objective")
    if safe_status.get("route_choice_readiness", {}).get("present") is not False:
        errors.append("safe status should not surface route choice readiness for safe latest advance")
    if route_choice_preview.get("passed") is not True:
        errors.extend(f"route choice preview: {error}" for error in route_choice_preview.get("errors", []))
    if route_choice_preview.get("bundle", {}).get("selected_route_id") != "B":
        errors.append("route choice preview should select route B")
    if route_choice_preview.get("bundle", {}).get("can_apply_with_separate_apply_gate") is not True:
        errors.append("route choice preview should reach separate apply gate readiness")
    if route_choice_preview.get("confirmation_text_included") is not False:
        errors.append("route choice preview must not include confirmation text")
    if route_choice_preview.get("active_queue_modified") is not False:
        errors.append("route choice preview must not modify queue")
    if route_choice_preview.get("execution_authorized") is not False:
        errors.append("route choice preview must not authorize execution")
    if route_choice_apply_preview.get("passed") is not True:
        errors.extend(f"route choice apply preview: {error}" for error in route_choice_apply_preview.get("errors", []))
    if route_choice_apply_preview.get("write_performed") is not False:
        errors.append("route choice apply preview must not write")
    if route_choice_apply_preview.get("queue_write_authorized") is not False:
        errors.append("route choice apply preview must not authorize queue write")
    if route_choice_apply.get("passed") is not True:
        errors.extend(f"route choice apply: {error}" for error in route_choice_apply.get("errors", []))
    if route_choice_apply.get("write_performed") is not True:
        errors.append("route choice apply should write fixture queue")
    if route_choice_apply.get("apply_gate", {}).get("appended_next_title") != "AGENTS OS formal Memory candidate gate v0.1":
        errors.append("route choice apply should append formal Memory first safe package")
    if route_choice_apply.get("queue_promotion_authorized") is not False:
        errors.append("route choice apply must not authorize queue promotion")
    if route_choice_apply.get("execution_authorized") is not False:
        errors.append("route choice apply must not authorize execution")
    if queue_promotion_preview.get("passed") is not True:
        errors.extend(f"queue promotion preview: {error}" for error in queue_promotion_preview.get("errors", []))
    if queue_promotion_preview.get("write_performed") is not False:
        errors.append("queue promotion preview must not write")
    if queue_promotion_preview.get("queue_write_authorized") is not False:
        errors.append("queue promotion preview must not authorize queue write")
    if queue_promotion_apply.get("passed") is not True:
        errors.extend(f"queue promotion apply: {error}" for error in queue_promotion_apply.get("errors", []))
    if queue_promotion_apply.get("write_performed") is not True:
        errors.append("queue promotion apply should write fixture queue")
    if queue_promotion_apply.get("queue_promotion_authorized") is not True:
        errors.append("queue promotion apply should authorize reviewed queue promotion")
    if queue_promotion_apply.get("mutation_gate", {}).get("promoted_now_title") != "AGENTS OS formal Memory candidate gate v0.1":
        errors.append("queue promotion apply should promote formal Memory first safe package")
    if queue_promotion_apply.get("execution_authorized") is not False:
        errors.append("queue promotion apply must not authorize execution")
    if not route_promotion_queue_contains_promoted_now:
        errors.append("queue promotion apply should move route package into NOW")
    if route_promotion_status.get("passed") is not True:
        errors.extend(f"route promotion status: {error}" for error in route_promotion_status.get("errors", []))
    if route_promotion_status.get("live_queue", {}).get("next_step", {}).get("status") != "queue_ready_for_run":
        errors.append("route promotion status should report live queue ready for run")
    if route_promotion_status.get("status_reconciliation", {}).get("record_boundary_may_be_stale") is not True:
        errors.append("route promotion status should detect stale record boundary after queue promotion")
    if route_promotion_continue.get("passed") is not True:
        errors.extend(f"route promotion continue: {error}" for error in route_promotion_continue.get("errors", []))
    if route_promotion_continue.get("run_summary", {}).get("local_safe_execution_count") != 1:
        errors.append("route promotion continue should execute current NOW once")
    if route_promotion_continue.get("run_summary", {}).get("record_write_count") != 1:
        errors.append("route promotion continue should write one run record")
    if route_promotion_continue.get("source", {}).get("derived_intent_raw_output") is not False:
        errors.append("route promotion continue must not output derived raw intent")
    if route_promotion_continue.get("next_step", {}).get("status") != "review_queue_proposal":
        errors.append("route promotion continue should stop at review_queue_proposal")
    if continue_with_completion.get("passed") is not True:
        errors.extend(f"continue with completion promotion: {error}" for error in continue_with_completion.get("errors", []))
    if continue_with_completion.get("run_summary", {}).get("local_safe_execution_count") != 1:
        errors.append("continue with completion promotion should execute current NOW once")
    if continue_with_completion.get("completion_promotion", {}).get("write_performed") is not True:
        errors.append("continue with completion promotion should write reviewed queue promotion")
    if continue_with_completion.get("queue_promotion_authorized") is not True:
        errors.append("continue with completion promotion should authorize reviewed queue promotion")
    if continue_with_completion.get("execution_authorized") is not False:
        errors.append("continue with completion promotion must not authorize execution")
    if not continue_completion_queue_promoted:
        errors.append("continue with completion promotion should promote safe follow-up to NOW")
    if continue_with_completion.get("next_step", {}).get("status") != "completion_promotion_applied_continue_ready":
        errors.append("continue with completion promotion should report continue-ready next step")
    if continue_loop.get("passed") is not True:
        errors.extend(f"continue loop: {error}" for error in continue_loop.get("errors", []))
    if continue_loop.get("cycles_performed") != 2:
        errors.append("continue loop should perform two cycles")
    if continue_loop.get("local_safe_execution_count") != 2:
        errors.append("continue loop should execute two local validations")
    if continue_loop.get("record_write_count") != 2:
        errors.append("continue loop should write two records")
    if continue_loop.get("completion_promotion_count") != 2:
        errors.append("continue loop should apply two completion promotions")
    if continue_loop.get("stopped_reason") != "max_cycles_reached":
        errors.append("continue loop should stop at max_cycles_reached")
    if continue_loop.get("execution_authorized") is not False:
        errors.append("continue loop must not authorize execution")
    if not continue_loop_queue_promoted_second:
        errors.append("continue loop should promote second safe follow-up to NOW")
    if advance_with_intake.get("passed") is not True:
        errors.extend(f"advance with intake: {error}" for error in advance_with_intake.get("errors", []))
    if advance_with_intake.get("stages", {}).get("intake_apply", {}).get("write_performed") is not True:
        errors.append("advance with intake should write fixture NEXT")
    if not advance_with_intake_record_captures_intake:
        errors.append("advance with intake record should capture intake write")
    if advance_with_intake.get("queue_promotion_authorized") is not False:
        errors.append("advance with intake must not authorize queue promotion")
    if run_with_intake.get("passed") is not True:
        errors.extend(f"run with intake: {error}" for error in run_with_intake.get("errors", []))
    if run_with_intake.get("active_queue_modified") is not True:
        errors.append("run with intake should modify fixture queue")
    if run_with_intake.get("queue_promotion_authorized") is not False:
        errors.append("run with intake must not authorize queue promotion")
    if run_with_intake.get("local_safe_execution_count") != 1:
        errors.append("run with intake should perform one local-safe execution")
    if status_after_intake.get("passed") is not True:
        errors.extend(f"status after intake: {error}" for error in status_after_intake.get("errors", []))
    if status_after_intake.get("latest_advance_id") != run_with_intake.get("steps", [{}])[-1].get("advance_id"):
        errors.append("status after intake should report run with intake as latest")
    if status_after_intake.get("latest_effects", {}).get("active_queue_modified") is not True:
        errors.append("status after intake should surface active queue modification in fixture")
    if status_after_intake.get("latest_effects", {}).get("queue_promotion_authorized") is not False:
        errors.append("status after intake must keep queue promotion false")
    if status_after_intake.get("goal_session_count") != 2:
        errors.append("status after intake should preserve goal session count")
    if status_after_intake.get("latest_goal_session", {}).get("goal_session_id") != safe_goal.get("goal_session_id"):
        errors.append("status after intake should preserve latest goal session summary")
    if provider_advance.get("passed") is not True:
        errors.extend(f"provider advance: {error}" for error in provider_advance.get("errors", []))
    if provider_advance.get("stages", {}).get("execution", {}).get("local_safe_execution_performed") is not False:
        errors.append("provider advance must not perform local-safe execution")
    if provider_advance.get("stages", {}).get("next_step", {}).get("status") != "jenn_decision_required":
        errors.append("provider advance should require Jenn decision")
    if recorded_cycle.get("passed") is not True:
        errors.extend(f"recorded cycle: {error}" for error in recorded_cycle.get("errors", []))
    if recorded_cycle.get("stages", {}).get("record_write", {}).get("write_performed") is not True:
        errors.append("recorded cycle should write record under allowed root")
    if not record_file_written:
        errors.append("recorded cycle record file does not exist")
    elif not record_payload_matches:
        errors.append("recorded cycle file should contain the cycle record preview")
    if blocked_record_cycle.get("passed") is not False:
        errors.append("blocked record cycle should fail when record path is outside allowed root")
    if blocked_record_cycle.get("stages", {}).get("record_write", {}).get("write_performed") is not False:
        errors.append("blocked record cycle must not write outside allowed root")

    if not temp_cleaned:
        errors.append("temporary workbench fixture directory was not cleaned")

    result = {
        "schema_version": "agents-os.workbench.validation.v0.1",
        "level": "full",
        "mode": "full_validation",
        "passed": not errors,
        "errors": errors,
        "fast_validation": {
            "passed": fast_validation.get("passed"),
            "selector_state": fast_validation.get("next_step_selector", {}).get("selector_state"),
            "selector_candidate_title": fast_validation.get("next_step_selector", {}).get("candidate_title"),
            "selected_checks": fast_validation.get("selected_checks", []),
            "skipped_full_checks": fast_validation.get("skipped_full_checks", []),
        },
        "docctl_probe": docctl_probe,
        "stopped_cycle": {
            "passed": stopped_cycle.get("passed"),
            "next_step": stopped_cycle.get("stages", {}).get("next_step", {}),
            "local_validation_performed": stopped_cycle.get("stages", {}).get("local_validation", {}).get("performed"),
        },
        "safe_cycle": {
            "passed": safe_cycle.get("passed"),
            "decision": safe_cycle.get("stages", {}).get("judgment", {}).get("decision"),
            "track": safe_cycle.get("stages", {}).get("track_preview", {}).get("selected_track"),
            "local_validation_performed": safe_cycle.get("stages", {}).get("local_validation", {}).get("performed"),
            "queue_proposal_present": safe_cycle.get("stages", {}).get("queue_proposal", {}).get("present"),
            "intake_can_apply_after_review": safe_cycle.get("stages", {}).get("intake_proposal", {}).get("can_apply_after_review"),
            "record_present": bool(safe_cycle.get("stages", {}).get("record", {}).get("record_id")),
            "next_step": safe_cycle.get("stages", {}).get("next_step", {}),
        },
        "recorded_cycle": {
            "passed": recorded_cycle.get("passed"),
            "record_write_performed": recorded_cycle.get("stages", {}).get("record_write", {}).get("write_performed"),
            "record_path": recorded_cycle.get("stages", {}).get("record_write", {}).get("record_path"),
        },
        "intake_apply_gate": {
            "preview_passed": intake_preview.get("passed"),
            "preview_write_performed": intake_preview.get("write_performed"),
            "apply_passed": intake_apply.get("passed"),
            "apply_write_performed": intake_apply.get("write_performed"),
            "provider_blocked": blocked_provider_intake.get("passed") is False,
            "p3_blocked": blocked_p3_intake.get("passed") is False,
        },
        "stopped_advance": {
            "passed": stopped_advance.get("passed"),
            "local_safe_execution_performed": stopped_advance.get("stages", {}).get("execution", {}).get("local_safe_execution_performed"),
            "record_write_performed": stopped_advance.get("record_write_performed"),
            "next_step": stopped_advance.get("stages", {}).get("next_step", {}),
        },
        "safe_advance": {
            "passed": safe_advance.get("passed"),
            "local_safe_execution_performed": safe_advance.get("stages", {}).get("execution", {}).get("local_safe_execution_performed"),
            "verification_passed": safe_advance.get("stages", {}).get("verification", {}).get("passed"),
            "record_write_performed": safe_advance.get("record_write_performed"),
            "advance_record_write_performed": safe_advance.get("advance_record_write_performed"),
            "advance_record_payload_matches": safe_advance_record_payload_matches,
            "advance_record_final_passed": safe_advance_record_final_passed,
            "cycle_record_written": safe_advance_cycle_record_written,
            "active_queue_modified": safe_advance.get("active_queue_modified"),
            "next_step": safe_advance.get("stages", {}).get("next_step", {}),
        },
        "advance_with_intake": {
            "passed": advance_with_intake.get("passed"),
            "intake_write_performed": advance_with_intake.get("stages", {}).get("intake_apply", {}).get("write_performed"),
            "record_captures_intake_write": advance_with_intake_record_captures_intake,
            "queue_promotion_authorized": advance_with_intake.get("queue_promotion_authorized"),
        },
        "status": {
            "empty_next_step": empty_status.get("next_step", {}).get("status"),
            "safe_latest_advance_id_matches": safe_status.get("latest_advance_id")
            == safe_goal.get("run", {}).get("steps", [{}])[-1].get("advance_id"),
            "safe_next_step": safe_status.get("next_step", {}).get("status"),
            "safe_goal_session_count": safe_status.get("goal_session_count"),
            "safe_latest_goal_session_id": safe_status.get("latest_goal_session", {}).get("goal_session_id"),
            "safe_latest_goal_state": safe_status.get("latest_goal_session", {}).get("goal_state"),
            "after_intake_latest_advance_id_matches": status_after_intake.get("latest_advance_id") == run_with_intake.get("steps", [{}])[-1].get("advance_id"),
            "after_intake_active_queue_modified": status_after_intake.get("latest_effects", {}).get("active_queue_modified"),
            "after_intake_goal_session_count": status_after_intake.get("goal_session_count"),
            "write_performed": status_after_intake.get("write_performed"),
        },
        "run": {
            "stopped_next_step": stopped_run.get("next_step", {}).get("status"),
            "stopped_local_safe_execution_count": stopped_run.get("local_safe_execution_count"),
            "safe_next_step": safe_run.get("next_step", {}).get("status"),
            "safe_local_safe_execution_count": safe_run.get("local_safe_execution_count"),
            "with_intake_active_queue_modified": run_with_intake.get("active_queue_modified"),
            "with_intake_queue_promotion_authorized": run_with_intake.get("queue_promotion_authorized"),
        },
        "goal": {
            "stopped_next_step": stopped_goal.get("next_step", {}).get("status"),
            "stopped_goal_state": stopped_goal.get("goal_state"),
            "stopped_record_write_performed": stopped_goal.get("record", {}).get("write_performed"),
            "safe_next_step": safe_goal.get("next_step", {}).get("status"),
            "safe_local_safe_execution_count": safe_goal.get("run_summary", {}).get("local_safe_execution_count"),
            "safe_record_write_performed": safe_goal.get("record", {}).get("write_performed"),
        },
        "route_choice_preview": {
            "passed": route_choice_preview.get("passed"),
            "selected_route_id": route_choice_preview.get("bundle", {}).get("selected_route_id"),
            "can_apply_with_separate_apply_gate": route_choice_preview.get("bundle", {}).get("can_apply_with_separate_apply_gate"),
            "active_queue_modified": route_choice_preview.get("active_queue_modified"),
            "execution_authorized": route_choice_preview.get("execution_authorized"),
        },
        "route_choice_apply_gate": {
            "preview_passed": route_choice_apply_preview.get("passed"),
            "preview_write_performed": route_choice_apply_preview.get("write_performed"),
            "apply_passed": route_choice_apply.get("passed"),
            "apply_write_performed": route_choice_apply.get("write_performed"),
            "apply_appended_next_title": route_choice_apply.get("apply_gate", {}).get("appended_next_title"),
            "queue_promotion_authorized": route_choice_apply.get("queue_promotion_authorized"),
            "execution_authorized": route_choice_apply.get("execution_authorized"),
        },
        "queue_promotion_apply_gate": {
            "preview_passed": queue_promotion_preview.get("passed"),
            "preview_write_performed": queue_promotion_preview.get("write_performed"),
            "apply_passed": queue_promotion_apply.get("passed"),
            "apply_write_performed": queue_promotion_apply.get("write_performed"),
            "apply_promoted_now_title": queue_promotion_apply.get("mutation_gate", {}).get("promoted_now_title"),
            "queue_promotion_authorized": queue_promotion_apply.get("queue_promotion_authorized"),
            "execution_authorized": queue_promotion_apply.get("execution_authorized"),
            "promoted_now_present": route_promotion_queue_contains_promoted_now,
            "live_status_next_step": route_promotion_status.get("live_queue", {}).get("next_step", {}).get("status"),
            "record_boundary_may_be_stale": route_promotion_status.get("status_reconciliation", {}).get("record_boundary_may_be_stale"),
        },
        "continue_current": {
            "passed": route_promotion_continue.get("passed"),
            "source_now_title": route_promotion_continue.get("source", {}).get("current_now_title"),
            "local_safe_execution_count": route_promotion_continue.get("run_summary", {}).get("local_safe_execution_count"),
            "record_write_count": route_promotion_continue.get("run_summary", {}).get("record_write_count"),
            "next_step": route_promotion_continue.get("next_step", {}),
            "completion_promotion_write_performed": continue_with_completion.get("completion_promotion", {}).get("write_performed"),
            "completion_promotion_next_step": continue_with_completion.get("next_step", {}).get("status"),
        },
        "continue_loop": {
            "passed": continue_loop.get("passed"),
            "cycles_performed": continue_loop.get("cycles_performed"),
            "local_safe_execution_count": continue_loop.get("local_safe_execution_count"),
            "record_write_count": continue_loop.get("record_write_count"),
            "completion_promotion_count": continue_loop.get("completion_promotion_count"),
            "stopped_reason": continue_loop.get("stopped_reason"),
        },
        "provider_advance": {
            "passed": provider_advance.get("passed"),
            "local_safe_execution_performed": provider_advance.get("stages", {}).get("execution", {}).get("local_safe_execution_performed"),
            "next_step": provider_advance.get("stages", {}).get("next_step", {}),
        },
        "blocked_record_cycle": {
            "passed": blocked_record_cycle.get("passed"),
            "record_write_performed": blocked_record_cycle.get("stages", {}).get("record_write", {}).get("write_performed"),
        },
        "provider_cycle": {
            "passed": provider_cycle.get("passed"),
            "decision": provider_cycle.get("stages", {}).get("judgment", {}).get("decision"),
            "local_validation_performed": provider_cycle.get("stages", {}).get("local_validation", {}).get("performed"),
            "next_step": provider_cycle.get("stages", {}).get("next_step", {}),
        },
        "temporary_fixture_cleaned": temp_cleaned,
    }
    return apply_docctl_release_gate(
        attach_validation_metadata(result, "full", started_at, required_level="full"),
        docctl_probe,
    )


def audit_item(requirement_id: str, description: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "description": description,
        "passed": passed,
        "evidence": evidence,
    }


def run_validation_probe(command: list[str], timeout_seconds: int = 30) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=WORKSPACE_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        return {
            "command": " ".join(command),
            "returncode": completed.returncode,
            "passed": completed.returncode == 0,
            "stdout_character_count": len(completed.stdout),
            "stderr_character_count": len(completed.stderr),
            "raw_output_included": False,
        }
    except subprocess.TimeoutExpired:
        return {
            "command": " ".join(command),
            "returncode": None,
            "passed": False,
            "timeout_seconds": timeout_seconds,
            "raw_output_included": False,
            "error": "timeout",
        }


def validate_codex_active_loop_import() -> dict[str, Any]:
    required_files = [
        CODEX_ACTIVE_LOOP_ROOT / "README.md",
        CODEX_ACTIVE_LOOP_ROOT / "BOUNDARY.md",
        CODEX_ACTIVE_LOOP_ROOT / "WORKBENCH_INTEGRATION.md",
        CODEX_ACTIVE_LOOP_ROOT / "schemas" / "agents-os" / "active-loop-receipt.v0.1.schema.json",
        CODEX_ACTIVE_LOOP_ROOT / "package.json",
        CODEX_ACTIVE_LOOP_ROOT / "package-lock.json",
        CODEX_ACTIVE_LOOP_ROOT / "tsconfig.json",
        CODEX_ACTIVE_LOOP_ROOT / "vitest.config.ts",
    ]
    required_dirs = [
        CODEX_ACTIVE_LOOP_ROOT / "src",
        CODEX_ACTIVE_LOOP_ROOT / "schemas",
        CODEX_ACTIVE_LOOP_ROOT / "tests",
        CODEX_ACTIVE_LOOP_ROOT / "docs",
        CODEX_ACTIVE_LOOP_ROOT / "data" / "synthetic-workspace",
    ]
    forbidden_paths = [
        CODEX_ACTIVE_LOOP_ROOT / "archive",
    ]
    ignored_runtime_paths = [
        CODEX_ACTIVE_LOOP_ROOT / "node_modules",
        CODEX_ACTIVE_LOOP_ROOT / "dist",
        CODEX_ACTIVE_LOOP_ROOT / "data" / "message-logs",
        CODEX_ACTIVE_LOOP_ROOT / "data" / "observer",
        CODEX_ACTIVE_LOOP_ROOT / "data" / "reports",
        CODEX_ACTIVE_LOOP_ROOT / "data" / "receipts",
    ]
    errors: list[str] = []
    missing_required = [rel(path) for path in [*required_files, *required_dirs] if not path.exists()]
    if missing_required:
        errors.append(f"codex active-loop missing required import paths: {', '.join(missing_required)}")
    present_forbidden = [rel(path) for path in forbidden_paths if path.exists()]
    if present_forbidden:
        errors.append(f"codex active-loop forbidden import paths present: {', '.join(present_forbidden)}")
    present_runtime_paths = [path for path in ignored_runtime_paths if path.exists()]
    unignored_runtime_paths: list[str] = []
    for path in present_runtime_paths:
        check_ignore = subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=WORKSPACE_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if check_ignore.returncode != 0:
            unignored_runtime_paths.append(rel(path))
    if unignored_runtime_paths:
        errors.append(f"codex active-loop runtime paths must be gitignored: {', '.join(unignored_runtime_paths)}")

    package_name = None
    try:
        package_name = load_json(CODEX_ACTIVE_LOOP_ROOT / "package.json").get("name")
    except Exception as exc:
        errors.append(f"codex active-loop package.json is not readable JSON: {exc}")
    if package_name != "codex-appserver-active-loop":
        errors.append("codex active-loop package name must be codex-appserver-active-loop")

    receipt_schema: dict[str, Any] = {}
    try:
        receipt_schema = load_json(CODEX_ACTIVE_LOOP_ROOT / "schemas" / "agents-os" / "active-loop-receipt.v0.1.schema.json")
    except Exception as exc:
        errors.append(f"codex active-loop receipt schema is not readable JSON: {exc}")
    if receipt_schema.get("title") != "AGENTS OS Codex Active Loop Receipt v0.1":
        errors.append("codex active-loop receipt schema title is invalid")
    receipt_required = set(receipt_schema.get("required", []))
    for key in ("schema_version", "task_id", "run_id", "roles_used", "message_count", "review_decision", "validation", "boundaries"):
        if key not in receipt_required:
            errors.append(f"codex active-loop receipt schema must require {key}")

    boundary_text = ""
    try:
        boundary_text = (CODEX_ACTIVE_LOOP_ROOT / "BOUNDARY.md").read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"codex active-loop BOUNDARY.md is not readable: {exc}")
    for phrase in (
        "does not grant authority",
        "AGENTS.md interpretation authority",
        "Jenn gate bypass",
        "provider gate bypass",
        "Memory gate bypass",
        "external-write gate bypass",
    ):
        if phrase not in boundary_text:
            errors.append(f"codex active-loop boundary must mention: {phrase}")

    return {
        "schema_version": "agents-os.workbench.codex-active-loop-import.v0.1",
        "passed": not errors,
        "errors": errors,
        "component_root": rel(CODEX_ACTIVE_LOOP_ROOT),
        "required_path_count": len(required_files) + len(required_dirs),
        "missing_required": missing_required,
        "forbidden_path_count": len(present_forbidden),
        "forbidden_paths_present": present_forbidden,
        "ignored_runtime_path_count": len(present_runtime_paths),
        "unignored_runtime_paths_present": unignored_runtime_paths,
        "package_name": package_name,
        "source_import_clean": not present_forbidden and not unignored_runtime_paths,
    }


def validate_workbench_fast() -> dict[str, Any]:
    started_at = time.monotonic()
    errors = validate_manifest(load_json(MANIFEST_PATH))
    codex_active_loop_import = validate_codex_active_loop_import()
    if codex_active_loop_import.get("passed") is not True:
        errors.extend(f"codex active-loop import: {error}" for error in codex_active_loop_import.get("errors", []))
    selector: dict[str, Any] = {}
    duplicate_selector: dict[str, Any] = {}
    safe_cycle: dict[str, Any] = {}
    live_status: dict[str, Any] = {}
    py_compile = run_validation_probe(
        [
            sys.executable,
            "-m",
            "py_compile",
            str(WORKBENCH_DIR / "workbench.py"),
            str(WORKBENCH_DIR / "test-workbench.py"),
        ],
        timeout_seconds=15,
    )
    if py_compile.get("passed") is not True:
        errors.append("fast validation py_compile failed")
    temp_cleaned = False
    with tempfile.TemporaryDirectory(prefix="agents-os-workbench-fast-", dir=WORKSPACE_ROOT) as temp_dir:
        queue_path = Path(temp_dir) / "queue.md"
        queue_path.write_text(fixture_queue_text("AGENTS OS external Git publication target gate v0.1"), encoding="utf-8")
        duplicate_queue_path = Path(temp_dir) / "duplicate-queue.md"
        duplicate_queue_path.write_text(
            fixture_queue_text("AGENTS OS external Git exact pre-push command gate v0.1"),
            encoding="utf-8",
        )
        record_root = Path(temp_dir) / "records"
        record_root.mkdir()
        live_status = build_live_queue_state(queue_path)
        selector = build_next_step_selector(queue_path, record_root)
        duplicate_selector = build_next_step_selector(duplicate_queue_path, record_root)
        safe_cycle = build_cycle(
            "Write local governance report and run fast validation.",
            queue_path,
            run_local_validation=True,
            validation_command="python3 --version",
        )
        if live_status.get("passed") is not True:
            errors.extend(f"fast live queue: {error}" for error in live_status.get("errors", []))
        if selector.get("passed") is not True or selector.get("candidate_present") is not True:
            errors.extend(f"fast selector: {error}" for error in selector.get("errors", []))
        if selector.get("candidate", {}).get("not_repeat_of_now") is not True:
            errors.append("fast selector must prove candidate is not NOW repeat")
        if selector.get("candidate", {}).get("substantive_progress") is not True:
            errors.append("fast selector must prove substantive progress")
        if not selector.get("candidate", {}).get("goal_delta"):
            errors.append("fast selector must describe goal delta")
        if duplicate_selector.get("selector_state") != "blocked_repeat_detected":
            errors.append("fast selector must block same-title queue repeats")
        if safe_cycle.get("passed") is not True:
            errors.extend(f"fast safe cycle: {error}" for error in safe_cycle.get("errors", []))
    temp_cleaned = not Path(temp_dir).exists()
    if not temp_cleaned:
        errors.append("fast validation temporary fixture directory was not cleaned")

    result = {
        "schema_version": "agents-os.workbench.validation.v0.1",
        "level": "fast",
        "mode": "fast_validation",
        "passed": not errors,
        "errors": errors,
        "selected_checks": [
            "manifest",
            "py_compile",
            "live_queue_state",
            "next_step_selector",
            "duplicate_selector_guard",
            "codex_active_loop_import_boundary",
            "local_safe_cycle_with_python_version",
            "temporary_fixture_cleanup",
        ],
        "skipped_full_checks": [
            "docctl status",
            "full fixture suite",
            "completion audit",
        ],
        "full_validation_required_before_external_write": True,
        "codex_active_loop_import": codex_active_loop_import,
        "py_compile": py_compile,
        "live_queue": {
            "passed": live_status.get("passed"),
            "next_step": live_status.get("next_step", {}),
        },
        "next_step_selector": {
            "passed": selector.get("passed"),
            "selector_state": selector.get("selector_state"),
            "candidate_title": selector.get("candidate", {}).get("title"),
            "not_repeat_of_now": selector.get("candidate", {}).get("not_repeat_of_now"),
            "not_repeat_of_queue": selector.get("candidate", {}).get("not_repeat_of_queue"),
            "substantive_progress": selector.get("candidate", {}).get("substantive_progress"),
            "goal_delta": selector.get("candidate", {}).get("goal_delta"),
        },
        "duplicate_selector": {
            "passed": duplicate_selector.get("passed"),
            "selector_state": duplicate_selector.get("selector_state"),
        },
        "safe_cycle": {
            "passed": safe_cycle.get("passed"),
            "local_validation_performed": safe_cycle.get("stages", {}).get("local_validation", {}).get("performed"),
            "local_validation_passed": safe_cycle.get("stages", {}).get("local_validation", {}).get("passed"),
        },
        "temporary_fixture_cleaned": temp_cleaned,
    }
    return attach_validation_metadata(result, "fast", started_at, required_level="fast")


def validate_workbench_targeted() -> dict[str, Any]:
    started_at = time.monotonic()
    fast = validate_workbench_fast()
    errors = list(fast.get("errors", []))
    probes = [
        run_validation_probe(
            [
                sys.executable,
                "control-plane/registry/validate-document-registry.py",
                "control-plane/registry/drafts/document-registry.v0.1.example.yaml",
            ],
            timeout_seconds=60,
        ),
        run_validation_probe(
            [
                sys.executable,
                "control-plane/registry/validate-federated-document-registry.py",
                "control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml",
            ],
            timeout_seconds=60,
        ),
    ]
    for probe in probes:
        if probe.get("passed") is not True:
            errors.append(f"targeted validation failed: {probe.get('command')}")
    result = {
        "schema_version": "agents-os.workbench.validation.v0.1",
        "level": "targeted",
        "mode": "targeted_validation",
        "passed": not errors,
        "errors": errors,
        "fast_validation": fast,
        "targeted_probes": probes,
        "selected_checks": [
            *fast.get("selected_checks", []),
            "document registry validator",
            "federated document registry validator",
        ],
        "skipped_full_checks": [
            "docctl status",
            "full fixture suite",
            "completion audit",
        ],
        "full_validation_required_before_external_write": True,
    }
    return attach_validation_metadata(result, "targeted", started_at, required_level="targeted")


def validate_workbench_by_level(level: str = "full") -> dict[str, Any]:
    if level == "fast":
        return validate_workbench_fast()
    if level == "targeted":
        return validate_workbench_targeted()
    if level == "full":
        result = validate_workbench()
        result["level"] = "full"
        result["mode"] = "full_validation"
        result["selected_checks"] = [
            "manifest",
            "full fixture suite",
            "route choice gates",
            "queue promotion gates",
            "continue loop",
            "docctl-backed validation",
        ]
        return result
    return {
        "schema_version": "agents-os.workbench.validation.v0.1",
        "level": level,
        "mode": "invalid_validation_level",
        "passed": False,
        "errors": [f"unknown validation level: {level}"],
    }


def build_completion_audit(
    record_root: Path = DEFAULT_RECORD_ROOT,
    queue_path: Path = DEFAULT_QUEUE,
    validation_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit whether the workbench satisfies the requested objective."""
    errors: list[str] = []
    manifest = load_json(MANIFEST_PATH)
    manifest_errors = validate_manifest(manifest)
    validation = validation_result if validation_result is not None else validate_workbench_by_level("full")
    status = build_status(record_root, queue_path)
    if manifest_errors:
        errors.extend(f"manifest: {error}" for error in manifest_errors)
    if validation.get("passed") is not True:
        errors.extend(f"validation: {error}" for error in validation.get("errors", []))
    if status.get("passed") is not True:
        errors.extend(f"status: {error}" for error in status.get("errors", []))

    allowed_modes = set(manifest.get("allowed_modes", []))
    loop_stages = set(manifest.get("loop_stages", []))
    validation_commands = manifest.get("validation_commands", [])
    requirements = [
        audit_item(
            "idea_to_task",
            "Idea text can become a candidate task and intake proposal.",
            validation.get("safe_cycle", {}).get("passed") is True
            and validation.get("safe_cycle", {}).get("intake_can_apply_after_review") is True
            and {"cycle", "advance"}.issubset(allowed_modes),
            {
                "safe_cycle_passed": validation.get("safe_cycle", {}).get("passed"),
                "intake_can_apply_after_review": validation.get("safe_cycle", {}).get("intake_can_apply_after_review"),
                "allowed_modes": sorted(allowed_modes),
            },
        ),
        audit_item(
            "task_to_queue",
            "Reviewed task intake can append safe candidates to NEXT without promoting or executing.",
            validation.get("intake_apply_gate", {}).get("apply_write_performed") is True
            and validation.get("intake_apply_gate", {}).get("provider_blocked") is True
            and validation.get("intake_apply_gate", {}).get("p3_blocked") is True,
            {
                "intake_apply_gate": validation.get("intake_apply_gate", {}),
                "loop_stage_present": "intake_apply_gate" in loop_stages,
            },
        ),
        audit_item(
            "queue_to_judgment",
            "The workbench reads the live queue, distinguishes ready queues from protected boundaries, and reconciles stale records.",
            status.get("live_queue", {}).get("passed") is True
            and bool(status.get("live_queue", {}).get("next_step", {}).get("status"))
            and "live_queue_status" in loop_stages
            and "status_reconciliation" in loop_stages,
            {
                "live_queue_next_step": status.get("live_queue", {}).get("next_step", {}).get("status"),
                "status_reconciliation": status.get("status_reconciliation", {}),
            },
        ),
        audit_item(
            "judgment_to_execution",
            "Queue-ready tasks can route through Commander/Track Selector to local-safe execution while provider/P3 tasks stop.",
            validation.get("safe_advance", {}).get("local_safe_execution_performed") is True
            and validation.get("provider_advance", {}).get("local_safe_execution_performed") is False,
            {
                "safe_advance": validation.get("safe_advance", {}),
                "provider_advance": validation.get("provider_advance", {}),
            },
        ),
        audit_item(
            "execution_to_verification",
            "Local-safe execution records verification results.",
            validation.get("safe_advance", {}).get("verification_passed") is True
            and validation.get("run", {}).get("safe_local_safe_execution_count") == 1,
            {
                "safe_advance_verification_passed": validation.get("safe_advance", {}).get("verification_passed"),
                "safe_run": validation.get("run", {}),
            },
        ),
        audit_item(
            "verification_to_record",
            "Cycle, advance, run, and goal paths write replayable local records.",
            validation.get("safe_advance", {}).get("record_write_performed") is True
            and validation.get("safe_advance", {}).get("advance_record_payload_matches") is True
            and validation.get("goal", {}).get("safe_record_write_performed") is True,
            {
                "safe_advance": validation.get("safe_advance", {}),
                "goal": validation.get("goal", {}),
                "record_root": status.get("record_root"),
            },
        ),
        audit_item(
            "record_to_next_step",
            "Status and goal summaries expose the next boundary without raw objective or record output.",
            bool(status.get("next_step", {}).get("status"))
            and validation.get("status", {}).get("safe_goal_session_count", 0) >= 1
            and validation.get("status", {}).get("safe_next_step") == "review_queue_proposal"
            and status.get("raw_content_output") is False,
            {
                "status_next_step": status.get("next_step", {}),
                "latest_goal_session": status.get("latest_goal_session", {}),
                "fixture_status": validation.get("status", {}),
            },
        ),
        audit_item(
            "route_boundary_flow",
            "Jenn route choice can be previewed, adopted into NEXT, promoted to NOW, and then continued without raw confirmation/template output.",
            validation.get("route_choice_preview", {}).get("selected_route_id") == "B"
            and validation.get("route_choice_apply_gate", {}).get("apply_write_performed") is True
            and validation.get("queue_promotion_apply_gate", {}).get("apply_write_performed") is True
            and validation.get("continue_current", {}).get("local_safe_execution_count") == 1,
            {
                "route_choice_preview": validation.get("route_choice_preview", {}),
                "route_choice_apply_gate": validation.get("route_choice_apply_gate", {}),
                "queue_promotion_apply_gate": validation.get("queue_promotion_apply_gate", {}),
                "continue_current": validation.get("continue_current", {}),
            },
        ),
        audit_item(
            "multi_turn_loop",
            "The workbench can run multiple current-NOW cycles with reviewed completion promotion.",
            validation.get("continue_loop", {}).get("cycles_performed") == 2
            and validation.get("continue_loop", {}).get("local_safe_execution_count") == 2
            and validation.get("continue_loop", {}).get("completion_promotion_count") == 2,
            {
                "continue_loop": validation.get("continue_loop", {}),
                "loop_mode_present": "loop" in allowed_modes,
            },
        ),
        audit_item(
            "dangerous_boundaries",
            "Provider, external write, runtime/plugin, formal Memory, route auto-selection, and unauthorized queue mutation remain blocked by default.",
            not false_flag_failures(manifest.get("dangerous_authorization_defaults", {}))
            and validation.get("provider_advance", {}).get("local_safe_execution_performed") is False
            and status.get("live_queue", {}).get("next_step", {}).get("execution_authorized") is False
            and status.get("latest_effects", {}).get("execution_authorized") is not True
            and status.get("latest_effects", {}).get("provider_call_authorized") is not True
            and status.get("latest_effects", {}).get("memory_write_authorized") is not True
            and status.get("latest_effects", {}).get("external_write_authorized") is not True
            and status.get("latest_effects", {}).get("runtime_plugin_activation_authorized") is not True,
            {
                "dangerous_authorization_defaults": manifest.get("dangerous_authorization_defaults", {}),
                "provider_advance": validation.get("provider_advance", {}),
                "live_queue_next_step": status.get("live_queue", {}).get("next_step", {}),
                "latest_effects": status.get("latest_effects", {}),
            },
        ),
        audit_item(
            "verification_surface",
            "The workbench has executable validation commands and the fixture suite covers CLI surfaces.",
            "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/test-workbench.py" in validation_commands
            and "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/test-workbench.py --full" in validation_commands
            and "PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-workbench/workbench.py validate" in validation_commands,
            {
                "validation_commands": validation_commands,
                "test_case_count": 20,
            },
        ),
    ]
    failed = [item for item in requirements if item.get("passed") is not True]
    result = {
        "schema_version": "agents-os.workbench.completion-audit.v0.1",
        "objective": "idea -> task -> queue -> judgment -> execution -> verification -> record -> next step",
        "read_only": True,
        "write_performed": False,
        "manifest_passed": not manifest_errors,
        "validation_passed": validation.get("passed") is True,
        "validation_evidence_supplied": validation_result is not None,
        "validation_level": validation.get("level"),
        "validation_duration_seconds": validation.get("duration_seconds"),
        "docctl_release_gate": validation.get("docctl_release_gate", {}),
        "release_blocked_by_docctl": validation.get("release_blocked_by_docctl"),
        "status_passed": status.get("passed") is True,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "failed_requirement_ids": [item["requirement_id"] for item in failed],
        "real_queue_boundary": {
            "status": status.get("live_queue", {}).get("next_step", {}).get("status"),
            "handled": status.get("live_queue", {}).get("next_step", {}).get("status")
            in {"queue_ready_for_run", "route_choice_required", "jenn_decision_required"},
            "execution_authorized": status.get("live_queue", {}).get("next_step", {}).get("execution_authorized"),
            "write_performed": status.get("live_queue", {}).get("next_step", {}).get("write_performed"),
        },
        "raw_content_output": False,
        "errors": sorted(set(errors)),
    }
    result["passed"] = not result["errors"] and not failed
    return result


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def print_validation_text(result: dict[str, Any]) -> None:
    if result.get("level") in {"fast", "targeted"}:
        print("AGENTS OS Workbench validation")
        print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"Level: {result.get('level')}")
        print(f"Mode: {result.get('mode')}")
        print(f"Selected checks: {', '.join(result.get('selected_checks', []))}")
        print(f"Skipped full checks: {', '.join(result.get('skipped_full_checks', []))}")
        print(f"Full validation before external write: {result.get('full_validation_required_before_external_write')}")
        selector = result.get("next_step_selector") or result.get("fast_validation", {}).get("next_step_selector", {})
        if selector:
            print(f"Selector state: {selector.get('selector_state')}")
            print(f"Selector candidate: {selector.get('candidate_title')}")
        for error in result.get("errors", []):
            print(f"- {error}")
        return
    print("AGENTS OS Workbench validation")
    print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"Level: {result.get('level', 'full')}")
    print(f"Fast validation passed: {result.get('fast_validation', {}).get('passed')}")
    print(f"Fast selector state: {result.get('fast_validation', {}).get('selector_state')}")
    print(f"Stopped cycle next step: {result['stopped_cycle']['next_step'].get('status')}")
    print(f"Safe cycle decision: {result['safe_cycle']['decision']}")
    print(f"Safe cycle validation performed: {result['safe_cycle']['local_validation_performed']}")
    print(f"Safe cycle intake applicable: {result['safe_cycle']['intake_can_apply_after_review']}")
    print(f"Safe cycle record present: {result['safe_cycle']['record_present']}")
    print(f"Intake apply gate write performed: {result['intake_apply_gate']['apply_write_performed']}")
    print(f"Intake apply gate provider blocked: {result['intake_apply_gate']['provider_blocked']}")
    print(f"Intake apply gate P3 blocked: {result['intake_apply_gate']['p3_blocked']}")
    print(f"Safe advance execution performed: {result['safe_advance']['local_safe_execution_performed']}")
    print(f"Safe advance record write performed: {result['safe_advance']['record_write_performed']}")
    print(f"Advance with intake write performed: {result['advance_with_intake']['intake_write_performed']}")
    print(f"Status safe next step: {result['status']['safe_next_step']}")
    print(f"Status safe goal sessions: {result['status']['safe_goal_session_count']}")
    print(f"Status after intake active queue modified: {result['status']['after_intake_active_queue_modified']}")
    print(f"Safe run next step: {result['run']['safe_next_step']}")
    print(f"Run with intake active queue modified: {result['run']['with_intake_active_queue_modified']}")
    print(f"Stopped goal state: {result['goal']['stopped_goal_state']}")
    print(f"Safe goal next step: {result['goal']['safe_next_step']}")
    print(f"Route choice preview selected: {result['route_choice_preview']['selected_route_id']}")
    print(f"Route choice apply write performed: {result['route_choice_apply_gate']['apply_write_performed']}")
    print(f"Queue promotion apply write performed: {result['queue_promotion_apply_gate']['apply_write_performed']}")
    print(f"Queue promotion live next step: {result['queue_promotion_apply_gate']['live_status_next_step']}")
    print(f"Continue current executions: {result['continue_current']['local_safe_execution_count']}")
    print(f"Continue completion promotion write performed: {result['continue_current']['completion_promotion_write_performed']}")
    print(f"Continue loop cycles performed: {result['continue_loop']['cycles_performed']}")
    print(f"Stopped advance next step: {result['stopped_advance']['next_step'].get('status')}")
    print(f"Recorded cycle write performed: {result['recorded_cycle']['record_write_performed']}")
    print(f"Safe cycle next step: {result['safe_cycle']['next_step'].get('status')}")
    print(f"Provider cycle decision: {result['provider_cycle']['decision']}")
    print(f"Temporary fixture cleaned: {result['temporary_fixture_cleaned']}")
    if result["errors"]:
        print("Errors:")
        for error in result["errors"]:
            print(f"- {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENTS OS preview-first workbench loop.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    cycle_parser = subparsers.add_parser("cycle", help="Run one idea-to-next-step workbench cycle.")
    cycle_parser.add_argument("--intent", required=True, help="Explicit idea or local task intent.")
    cycle_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    cycle_parser.add_argument("--run-local-validation", action="store_true", help="Run local-safe validation when authorized.")
    cycle_parser.add_argument("--validation-command", default=DEFAULT_VALIDATION_COMMAND, help="Local-safe python3 validation command.")
    cycle_parser.add_argument("--write-record", action="store_true", help="Write the cycle record JSON under the workbench records root.")
    cycle_parser.add_argument("--record-path", default=None, help="Record JSON path; must stay under execution/agents-os-workbench/records.")
    cycle_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    advance_parser = subparsers.add_parser("advance", help="Run one bounded local-safe advance step and write a local record.")
    advance_parser.add_argument("--intent", required=True, help="Explicit idea or local task intent.")
    advance_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    advance_parser.add_argument("--validation-command", default=DEFAULT_VALIDATION_COMMAND, help="Local-safe python3 validation command.")
    advance_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root for local advance records.")
    advance_parser.add_argument("--apply-intake", action="store_true", help="Apply reviewed candidate-to-NEXT intake to the supplied queue.")
    advance_parser.add_argument("--allowed-queue-root", default=str(WORKSPACE_ROOT), help="Boundary root for explicit intake apply.")
    advance_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    status_parser = subparsers.add_parser("status", help="Read latest workbench advance record and next step.")
    status_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root to inspect.")
    status_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path for live status.")
    status_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    run_parser = subparsers.add_parser("run", help="Advance automatically until a review or decision boundary.")
    run_parser.add_argument("--intent", required=True, help="Explicit idea or local task intent.")
    run_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    run_parser.add_argument("--validation-command", default=DEFAULT_VALIDATION_COMMAND, help="Local-safe python3 validation command.")
    run_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root for local run records.")
    run_parser.add_argument("--max-steps", type=int, default=1, help="Maximum local-safe advance steps, capped at 5.")
    run_parser.add_argument("--apply-intake", action="store_true", help="Apply reviewed candidate-to-NEXT intake to the supplied queue.")
    run_parser.add_argument("--allowed-queue-root", default=str(WORKSPACE_ROOT), help="Boundary root for explicit intake apply.")
    run_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    continue_parser = subparsers.add_parser("continue", help="Continue from the current live NOW item until a boundary.")
    continue_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    continue_parser.add_argument("--validation-command", default=DEFAULT_VALIDATION_COMMAND, help="Local-safe python3 validation command.")
    continue_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root for local continue records.")
    continue_parser.add_argument("--max-steps", type=int, default=1, help="Maximum local-safe advance steps, capped at 5.")
    continue_parser.add_argument("--apply-intake", action="store_true", help="Apply reviewed candidate-to-NEXT intake to the supplied queue.")
    continue_parser.add_argument("--apply-completion-promotion", action="store_true", help="After a successful local run, apply reviewed close-NOW/promote-NEXT.")
    continue_parser.add_argument("--allowed-queue-root", default=str(WORKSPACE_ROOT), help="Boundary root for explicit intake apply.")
    continue_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    loop_parser = subparsers.add_parser("loop", help="Run queue-driven continue cycles until a boundary or cycle limit.")
    loop_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    loop_parser.add_argument("--validation-command", default=DEFAULT_VALIDATION_COMMAND, help="Local-safe python3 validation command.")
    loop_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root for local loop records.")
    loop_parser.add_argument("--max-cycles", type=int, default=2, help="Maximum continue cycles, capped at 5.")
    loop_parser.add_argument("--apply-completion-promotion", action="store_true", help="After each successful local run with NEXT available, apply reviewed close-NOW/promote-NEXT.")
    loop_parser.add_argument("--allowed-queue-root", default=str(WORKSPACE_ROOT), help="Boundary root for explicit completion promotion.")
    loop_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    goal_parser = subparsers.add_parser("goal", help="Enter a long-running objective and advance until a boundary.")
    goal_parser.add_argument("--objective", required=True, help="Goal objective text, such as a /goal payload.")
    goal_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    goal_parser.add_argument("--validation-command", default=DEFAULT_VALIDATION_COMMAND, help="Local-safe python3 validation command.")
    goal_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root for local goal and run records.")
    goal_parser.add_argument("--max-steps", type=int, default=1, help="Maximum local-safe advance steps, capped at 5.")
    goal_parser.add_argument("--apply-intake", action="store_true", help="Apply reviewed candidate-to-NEXT intake to the supplied queue.")
    goal_parser.add_argument("--allowed-queue-root", default=str(WORKSPACE_ROOT), help="Boundary root for explicit intake apply.")
    goal_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    route_preview_parser = subparsers.add_parser("route-choice-preview", help="Preview Jenn route confirmation without applying it.")
    route_preview_parser.add_argument("--confirmation-text", required=True, help="Exact Jenn route confirmation text.")
    route_preview_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    route_preview_parser.add_argument("--source", default=str(DEFAULT_ROUTE_SELECTION_PACKAGE), help="Route selection package Markdown path.")
    route_preview_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    route_apply_parser = subparsers.add_parser("route-choice-apply-gate", help="Preview or apply reviewed route adoption into a queue.")
    route_apply_parser.add_argument("--confirmation-text", required=True, help="Exact Jenn route confirmation text.")
    route_apply_parser.add_argument("--queue", required=True, help="Queue Markdown path to preview or apply.")
    route_apply_parser.add_argument("--source", default=str(DEFAULT_ROUTE_SELECTION_PACKAGE), help="Route selection package Markdown path.")
    route_apply_parser.add_argument("--apply", action="store_true", help="Actually append the route package to NEXT after review gates pass.")
    route_apply_parser.add_argument("--allowed-queue-root", default=str(WORKSPACE_ROOT), help="Boundary root for explicit route apply.")
    route_apply_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    queue_promotion_parser = subparsers.add_parser("queue-promotion-apply-gate", help="Preview or apply reviewed NEXT-to-NOW queue promotion.")
    queue_promotion_parser.add_argument("--queue", required=True, help="Queue Markdown path to preview or apply.")
    queue_promotion_parser.add_argument("--apply", action="store_true", help="Actually promote the first NEXT item to NOW after review gates pass.")
    queue_promotion_parser.add_argument("--allowed-queue-root", default=str(WORKSPACE_ROOT), help="Boundary root for explicit queue promotion.")
    queue_promotion_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    validate_parser = subparsers.add_parser("validate", help="Run workbench self-validation.")
    validate_parser.add_argument("--level", choices=VALIDATION_LEVELS, default="full", help="Validation level: fast, targeted, or full.")
    validate_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    selector_parser = subparsers.add_parser("select-next-step", help="Preview the next non-repeating NEXT candidate.")
    selector_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path.")
    selector_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root to inspect.")
    selector_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    audit_parser = subparsers.add_parser("audit", help="Audit workbench completion against the objective chain.")
    audit_parser.add_argument("--record-root", default=str(DEFAULT_RECORD_ROOT), help="Record root to inspect.")
    audit_parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Active Work Queue Markdown path for live audit.")
    audit_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    args = parser.parse_args()

    if args.command == "cycle":
        result = build_cycle(
            args.intent,
            Path(args.queue),
            run_local_validation=args.run_local_validation,
            validation_command=args.validation_command,
            write_record=args.write_record,
            record_path=Path(args.record_path) if args.record_path else None,
        )
        if args.json:
            print_json(result)
        else:
            stages = result["stages"]
            print("AGENTS OS Workbench cycle")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Task: {stages['task'].get('title')}")
            print(f"NOW: {stages['machine'].get('source_item', {}).get('title')}")
            print(f"Decision: {stages['judgment'].get('decision')}")
            print(f"Track: {stages['track_preview'].get('selected_track')}")
            print(f"Local validation performed: {stages['local_validation'].get('performed')}")
            print(f"Intake proposal applicable: {stages['intake_proposal'].get('can_apply_after_review')}")
            print(f"Queue proposal present: {stages['queue_proposal'].get('present')}")
            print(f"Record present: {bool(stages['record'].get('record_id'))}")
            print(f"Record write performed: {stages['record_write'].get('write_performed')}")
            print(f"Next step: {stages['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "advance":
        result = build_advance(
            args.intent,
            Path(args.queue),
            validation_command=args.validation_command,
            record_root=Path(args.record_root),
            apply_intake=args.apply_intake,
            allowed_queue_root=Path(args.allowed_queue_root),
        )
        if args.json:
            print_json(result)
        else:
            stages = result["stages"]
            print("AGENTS OS Workbench advance")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Mode: {result['mode']}")
            print(f"Local-safe execution performed: {stages['execution'].get('local_safe_execution_performed')}")
            print(f"Verification passed: {stages['verification'].get('passed')}")
            print(f"Record write performed: {stages['record'].get('write_performed')}")
            print(f"Intake apply write performed: {stages['intake_apply'].get('write_performed')}")
            print(f"Next step: {stages['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "status":
        result = build_status(Path(args.record_root), Path(args.queue))
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Workbench status")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Record root: {result['record_root']}")
            print(f"Live queue next step: {result['live_queue'].get('next_step', {}).get('status')}")
            print(f"Record boundary may be stale: {result['status_reconciliation'].get('record_boundary_may_be_stale')}")
            print(f"Advance records: {result['advance_record_count']}")
            print(f"Goal sessions: {result['goal_session_count']}")
            print(f"Latest present: {result['latest_present']}")
            print(f"Latest passed: {result['latest_passed']}")
            print(f"Local-safe execution performed: {result['latest_execution'].get('local_safe_execution_performed')}")
            print(f"Verification passed: {result['latest_verification'].get('passed')}")
            print(f"Latest goal state: {result['latest_goal_session'].get('goal_state')}")
            print(f"Route choice options ready: {result['route_choice_readiness'].get('option_count')}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "select-next-step":
        result = build_next_step_selector(Path(args.queue), Path(args.record_root))
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Workbench next-step selector")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Selector state: {result.get('selector_state')}")
            print(f"Current NOW: {result['source'].get('current_now_title')}")
            print(f"Candidate present: {result.get('candidate_present')}")
            print(f"Candidate: {result.get('candidate', {}).get('title')}")
            print(f"Fast validation required: {result.get('validation_plan', {}).get('level')}")
            print(f"Full validation before external write: {result.get('validation_plan', {}).get('full_validation_required_before_external_write')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "run":
        result = build_run(
            args.intent,
            Path(args.queue),
            validation_command=args.validation_command,
            record_root=Path(args.record_root),
            max_steps=args.max_steps,
            apply_intake=args.apply_intake,
            allowed_queue_root=Path(args.allowed_queue_root),
        )
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Workbench run")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Mode: {result['mode']}")
            print(f"Steps performed: {result['steps_performed']}")
            print(f"Local-safe executions: {result['local_safe_execution_count']}")
            print(f"Records written: {result['record_write_count']}")
            print(f"Stopped reason: {result['stopped_reason']}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "continue":
        result = build_continue_current(
            Path(args.queue),
            validation_command=args.validation_command,
            record_root=Path(args.record_root),
            max_steps=args.max_steps,
            apply_intake=args.apply_intake,
            apply_completion_promotion=args.apply_completion_promotion,
            allowed_queue_root=Path(args.allowed_queue_root),
        )
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Workbench continue")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Mode: {result['mode']}")
            print(f"Current NOW: {result['source'].get('current_now_title')}")
            print(f"Live queue next step: {result['live_queue'].get('next_step', {}).get('status')}")
            print(f"Steps performed: {result['run_summary'].get('steps_performed')}")
            print(f"Local-safe executions: {result['run_summary'].get('local_safe_execution_count')}")
            print(f"Records written: {result['run_summary'].get('record_write_count')}")
            print(f"Completion promotion write performed: {result['completion_promotion'].get('write_performed')}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "loop":
        result = build_continue_loop(
            Path(args.queue),
            validation_command=args.validation_command,
            record_root=Path(args.record_root),
            max_cycles=args.max_cycles,
            apply_completion_promotion=args.apply_completion_promotion,
            allowed_queue_root=Path(args.allowed_queue_root),
        )
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Workbench loop")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Mode: {result['mode']}")
            print(f"Cycles performed: {result['cycles_performed']}")
            print(f"Local-safe executions: {result['local_safe_execution_count']}")
            print(f"Records written: {result['record_write_count']}")
            print(f"Completion promotions: {result['completion_promotion_count']}")
            print(f"Stopped reason: {result['stopped_reason']}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "goal":
        result = build_goal_session(
            args.objective,
            Path(args.queue),
            validation_command=args.validation_command,
            record_root=Path(args.record_root),
            max_steps=args.max_steps,
            apply_intake=args.apply_intake,
            allowed_queue_root=Path(args.allowed_queue_root),
        )
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Workbench goal")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Mode: {result['mode']}")
            print(f"Goal state: {result['goal_state']}")
            print(f"Steps performed: {result['run_summary'].get('steps_performed')}")
            print(f"Local-safe executions: {result['run_summary'].get('local_safe_execution_count')}")
            print(f"Records written: {result['run_summary'].get('record_write_count')}")
            print(f"Stopped reason: {result['run_summary'].get('stopped_reason')}")
            print(f"Goal record written: {result['record'].get('write_performed')}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "route-choice-preview":
        result = build_route_choice_preview(
            args.confirmation_text,
            Path(args.queue),
            source=Path(args.source),
        )
        if args.json:
            print_json(result)
        else:
            bundle = result["bundle"]
            print("AGENTS OS Workbench route choice preview")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Selected route: {bundle.get('selected_route_id')}")
            print(f"First safe package: {bundle.get('selected_first_safe_package')}")
            print(f"Proposed NEXT: {bundle.get('proposed_next_title')}")
            print(f"Separate apply gate ready: {bundle.get('can_apply_with_separate_apply_gate')}")
            print(f"Active queue modified: {result.get('active_queue_modified')}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "route-choice-apply-gate":
        result = build_route_choice_apply_gate(
            args.confirmation_text,
            Path(args.queue),
            source=Path(args.source),
            apply=args.apply,
            allowed_queue_root=Path(args.allowed_queue_root),
        )
        if args.json:
            print_json(result)
        else:
            route = result["route"]
            gate = result["apply_gate"]
            print("AGENTS OS Workbench route choice apply gate")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Selected route: {route.get('selected_route_id')}")
            print(f"First safe package: {route.get('selected_first_safe_package')}")
            print(f"Preview only: {result.get('preview_only')}")
            print(f"Queue adoption authorized: {gate.get('queue_adoption_authorized')}")
            print(f"Write performed: {result.get('write_performed')}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "queue-promotion-apply-gate":
        result = build_queue_promotion_apply_gate(
            Path(args.queue),
            apply=args.apply,
            allowed_queue_root=Path(args.allowed_queue_root),
        )
        if args.json:
            print_json(result)
        else:
            gate = result["mutation_gate"]
            print("AGENTS OS Workbench queue promotion apply gate")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Promote NEXT: {result['queue_before'].get('promote_next_title')}")
            print(f"Preview only: {result.get('preview_only')}")
            print(f"Queue mutation authorized: {gate.get('queue_mutation_authorized')}")
            print(f"Write performed: {result.get('write_performed')}")
            print(f"Next step: {result['next_step'].get('status')}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    if args.command == "validate":
        result = validate_workbench_by_level(args.level)
        if args.json:
            print_json(result)
        else:
            print_validation_text(result)
        return 0 if result["passed"] else 1

    if args.command == "audit":
        result = build_completion_audit(Path(args.record_root), Path(args.queue))
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Workbench completion audit")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Requirements: {result['requirement_count']}")
            print(f"Failed requirements: {','.join(result['failed_requirement_ids']) or 'none'}")
            print(f"Real queue boundary: {result['real_queue_boundary'].get('status')}")
            for item in result.get("requirements", []):
                print(f"- {item['requirement_id']}: {'PASS' if item['passed'] else 'FAIL'}")
            for error in result.get("errors", []):
                print(f"- {error}")
        return 0 if result["passed"] else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
