#!/usr/bin/env python3
"""AGENTS OS commander-first control chain.

This module wires the first commander decision layer, track selector, shared
track result contract, ColaMeta readiness reconciliation, local-safe executor
actions, and queue proposal-only manager. It does not call providers, start
services, activate plugins/runtimes, write formal Memory, or mutate the Active
Work Queue.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
from typing import Any


CONTROL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = CONTROL_DIR.parents[1]
REGISTRY_DIR = WORKSPACE_ROOT / "control-plane" / "registry"
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from path_boundary import is_protected_path, is_under_workspace, safe_resolve

SCHEMAS_PATH = CONTROL_DIR / "control-chain.schemas.json"
MANIFEST_PATH = CONTROL_DIR / "control-chain-manifest.json"
DEFAULT_QUEUE = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-23-agents-os-active-work-queue-v16.8.md"
ROUTE_SELECTION_PACKAGE = REGISTRY_DIR / "reports" / "2026-07-07-agents-os-next-route-selection-package-v0.1.md"
COLAMETA_PREFLIGHT = REGISTRY_DIR / "colameta-executor-preflight.py"
DOCCTL = REGISTRY_DIR / "docctl.py"
TASK_PRODUCER = WORKSPACE_ROOT / "execution" / "agents-os-task-producer" / "producer.py"
MACHINE = WORKSPACE_ROOT / "execution" / "agents-os-machine" / "machine.py"
DASHBOARD = WORKSPACE_ROOT / "execution" / "agents-os-dashboard" / "dashboard.py"

DECISIONS = (
    "route_to_colameta",
    "route_to_local_executor",
    "stop_needs_nobao_review",
    "stop_needs_jenn_decision",
    "reject_as_out_of_scope",
)
TRACKS = ("colameta", "local_executor", "stop")
AUTHORIZATION_SCOPES = ("none", "local_safe_only", "blocked_requires_jenn")
FAILURE_CATEGORIES = (
    "validation_failed",
    "scope_violation",
    "protected_path_detected",
    "dirty_worktree_conflict",
    "unknown_action_type",
    "p3_signal_detected",
    "executor_output_invalid",
)
LOCAL_SAFE_ACTIONS = (
    "write_governance_doc",
    "write_receipt_review_report",
    "update_current_state",
    "run_validation_command",
)
FORBIDDEN_ACTIONS = (
    "update_active_queue",
    "provider_call",
    "service_start",
    "runtime_plugin_activation",
    "external_write",
    "formal_memory_write",
    "state_private_read",
    "auth_provider_runtime_config_change",
    "destructive_git_or_filesystem_operation",
)
JENN_SIGNALS = {
    "provider_call",
    "service_start",
    "executor_run",
    "external_write",
    "database_write",
    "memory_write",
    "runtime_plugin_activation",
    "state_private",
    "auth_or_secret_config",
    "git_release_boundary",
    "route_selection_required",
    "route_auto_selection",
}
QUEUE_SIGNALS = {"queue_write", "queue_promotion"}
GLOBAL_BLOCKED_CAPABILITIES = [
    "route_auto_selection",
    "queue_write",
    "queue_promotion",
    "provider_call",
    "service_start",
    "runtime_plugin_activation",
    "external_write",
    "formal_memory_write",
    "state_private_read",
    "auth_provider_runtime_config_change",
    "destructive_git_or_filesystem_operation",
]
ROUTE_CHOICE_PROPOSAL_BLOCKED_CAPABILITIES = sorted(
    set(
        GLOBAL_BLOCKED_CAPABILITIES
        + [
            "workspace_route_state_write",
            "active_queue_write",
            "route_adoption",
            "route_execution",
        ]
    )
)
NEXT_USER_ACTION_FALSE_FLAGS = (
    "route_auto_selection_authorized",
    "active_queue_mutation_authorized",
    "queue_promotion_authorized",
    "execution_authorized",
    "write_performed",
    "raw_content_output",
)
ROUTE_CHOICE_TEMPLATE_COVERAGE_FALSE_FLAGS = (
    "workspace_route_state_modified",
    "active_queue_modified",
    "queue_write_authorized",
    "queue_promotion_authorized",
    "route_auto_selection_authorized",
    "execution_authorized",
    "provider_call_authorized",
    "service_start_authorized",
    "executor_run_authorized",
    "external_write_authorized",
    "memory_write_authorized",
    "runtime_plugin_activation_authorized",
    "plugin_execution_authorized",
    "raw_template_output",
    "confirmation_text_included",
)
ROUTE_CHOICE_E2E_FALSE_FLAGS = (
    "active_queue_modified",
    "real_queue_write_performed",
    "queue_write_authorized",
    "queue_promotion_authorized",
    "route_selected",
    "route_auto_selection_authorized",
    "route_adoption_authorized",
    "execution_authorized",
    "provider_call_authorized",
    "service_start_authorized",
    "executor_run_authorized",
    "external_write_authorized",
    "memory_write_authorized",
    "runtime_plugin_activation_authorized",
    "plugin_execution_authorized",
    "raw_confirmation_text_output",
    "raw_template_output",
)
REPAIR_POLICY = {
    "validation_failed": {"repair_attempt_allowed": True, "max_repair_attempts": 1},
    "scope_violation": {"repair_attempt_allowed": False, "max_repair_attempts": 0},
    "protected_path_detected": {"repair_attempt_allowed": False, "max_repair_attempts": 0},
    "dirty_worktree_conflict": {"repair_attempt_allowed": False, "max_repair_attempts": 0},
    "unknown_action_type": {"repair_attempt_allowed": False, "max_repair_attempts": 0},
    "p3_signal_detected": {"repair_attempt_allowed": False, "max_repair_attempts": 0},
    "executor_output_invalid": {"repair_attempt_allowed": False, "max_repair_attempts": 0},
}

COLAMETA_PATTERNS = re.compile(r"\b(colameta|executor readiness|plan reconciliation|runner metadata|prompt files?)\b", re.I)
LOCAL_PATTERNS = re.compile(
    r"\b(governance|document|registry|receipt|review|report|current_state|docctl|validation|local file|markdown)\b",
    re.I,
)
NEGATED_SIGNAL_CONTEXT = re.compile(
    r"\b(no|do not|does not|cannot|can't|must not|blocked actions?|blocked until|forbidden|denied)\b",
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
}
FAILURE_PATTERNS = {
    "protected_path_detected": re.compile(r"\b(protected path|state-private/|secrets?/|tokens?/|cookies?|credentials?)\b", re.I),
    "dirty_worktree_conflict": re.compile(r"\bdirty (tracked )?worktree|uncommitted changes?|would overwrite\b", re.I),
    "scope_violation": re.compile(r"\boutside workspace|scope violation|out of scope|target path is outside\b", re.I),
    "unknown_action_type": re.compile(r"\b(action_type is not allowed|unknown action|unsupported action)\b", re.I),
    "p3_signal_detected": re.compile(
        r"\b(provider_call|provider call|service_start|service start|runtime_plugin_activation|external_write|formal_memory_write|auth_provider_runtime_config_change|destructive_git_or_filesystem_operation|force push|deploy|publish|release)\b",
        re.I,
    ),
    "executor_output_invalid": re.compile(r"\b(missing required field|invalid schema|schema_version is invalid|executor output invalid)\b", re.I),
    "validation_failed": re.compile(r"\b(validation command failed|returncode|validation failed|did not pass)\b", re.I),
}


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


def source_text(candidate: dict[str, Any]) -> str:
    return "\n".join(
        str(candidate.get(key, ""))
        for key in ("title", "summary")
    )


def false_flag_failures(value: dict[str, Any], flags: list[str]) -> list[str]:
    return [flag for flag in flags if value.get(flag) is not False]


def schema_required(schema_name: str) -> list[str]:
    schemas = load_json(SCHEMAS_PATH)
    required = schemas.get(schema_name, {}).get("required", [])
    if not isinstance(required, list):
        return []
    return [str(item) for item in required]


def validate_candidate_input(candidate: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if candidate.get("schema_version") != "agents-os.task-producer.candidate-task.v0.1":
        errors.append("candidate schema_version is invalid")
    if candidate.get("producer_generated") is not True:
        errors.append("candidate.producer_generated must be true")
    review = candidate.get("review_gate", {})
    if review.get("requires_nobao_review") is not True:
        errors.append("candidate must require Nobao review")
    if review.get("execution_authorized") is not False:
        errors.append("candidate review gate must not authorize execution")
    authorization_failures = false_flag_failures(
        candidate.get("authorization", {}),
        [
            "queue_write_authorized",
            "execution_authorized",
            "provider_call_authorized",
            "service_start_authorized",
            "executor_run_authorized",
            "external_write_authorized",
            "memory_write_authorized",
            "runtime_plugin_activation_authorized",
            "plugin_execution_authorized",
            "route_auto_selection_authorized",
        ],
    )
    if authorization_failures:
        errors.append(f"candidate dangerous authorization flags not false: {','.join(authorization_failures)}")
    effect_failures = false_flag_failures(
        candidate.get("execution_effect", {}),
        [
            "write_performed",
            "execution_authorized",
            "service_started",
            "executor_run_performed",
            "provider_call_performed",
            "external_write_performed",
            "memory_write_performed",
            "runtime_plugin_activation_performed",
            "plugin_execution_performed",
        ],
    )
    if effect_failures:
        errors.append(f"candidate execution effect flags not false: {','.join(effect_failures)}")
    return errors


def validate_machine_preview(preview: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if preview.get("schema_version") != "agents-os.machine.preview.v0.1":
        errors.append("machine preview schema_version is invalid")
    if preview.get("preview_only") is not True:
        errors.append("machine preview must be preview_only")
    if preview.get("execution_authorized") is not False:
        errors.append("machine preview must not authorize execution")
    review = preview.get("review_gate", {})
    if review.get("requires_nobao_review") is not True:
        errors.append("machine preview must require Nobao review")
    if review.get("execution_authorized") is not False:
        errors.append("machine preview review gate must not authorize execution")
    failures = false_flag_failures(
        preview.get("authorization", {}),
        [
            "provider_call_authorized",
            "service_start_authorized",
            "executor_run_authorized",
            "external_write_authorized",
            "memory_write_authorized",
            "runtime_plugin_activation_authorized",
        ],
    )
    if failures:
        errors.append(f"machine preview authorization flags not false: {','.join(failures)}")
    return errors


def is_route_option_candidate(candidate: dict[str, Any]) -> bool:
    source = candidate.get("source", {})
    source_facts = candidate.get("source_facts", {})
    return (
        source.get("kind") == "route_selection_option"
        or source_facts.get("route_option_id") is not None
    )


def classify_candidate(candidate: dict[str, Any], input_errors: list[str]) -> tuple[str, str, str, bool, str, list[str]]:
    risk_signals = set(str(item) for item in candidate.get("risk_signals", []) if item)
    text = source_text(candidate)
    if input_errors:
        return (
            "reject_as_out_of_scope",
            "stop",
            "none",
            False,
            "invalid",
            ["candidate_or_machine_input_invalid"],
        )
    if is_route_option_candidate(candidate):
        return (
            "stop_needs_jenn_decision",
            "stop",
            "blocked_requires_jenn",
            True,
            "red",
            sorted(risk_signals | {"route_selection_required", "route_auto_selection"}),
        )
    if risk_signals & JENN_SIGNALS or candidate.get("review_gate", {}).get("requires_jenn_decision") is True:
        return (
            "stop_needs_jenn_decision",
            "stop",
            "blocked_requires_jenn",
            True,
            "red",
            sorted(risk_signals & JENN_SIGNALS) or ["jenn_decision_required"],
        )
    if risk_signals & QUEUE_SIGNALS:
        return (
            "stop_needs_nobao_review",
            "stop",
            "none",
            False,
            "yellow",
            sorted(risk_signals & QUEUE_SIGNALS),
        )
    if COLAMETA_PATTERNS.search(text):
        return ("route_to_colameta", "colameta", "none", False, "yellow", [])
    if LOCAL_PATTERNS.search(text):
        return ("route_to_local_executor", "local_executor", "local_safe_only", False, "green", [])
    return ("stop_needs_nobao_review", "stop", "none", False, "yellow", ["unclear_task_route"])


def build_commander_decision(candidate: dict[str, Any], machine_preview: dict[str, Any] | None = None) -> dict[str, Any]:
    input_errors = validate_candidate_input(candidate)
    if machine_preview is not None:
        input_errors.extend(validate_machine_preview(machine_preview))
    decision, track, scope, requires_jenn, risk_level, blocked = classify_candidate(candidate, input_errors)
    reason = "candidate routed by commander"
    if input_errors:
        reason = "; ".join(input_errors)
    elif decision.startswith("stop"):
        reason = "candidate requires review before track routing"
    elif decision == "route_to_colameta":
        reason = "candidate matches ColaMeta readiness or runner metadata route"
    elif decision == "route_to_local_executor":
        reason = "candidate matches local governance or validation route"
    result = {
        "schema_version": "agents-os.commander.decision.v0.1",
        "decision_id": stable_id("DECISION", [candidate.get("candidate_id"), decision, track, scope, blocked]),
        "source_candidate_id": candidate.get("candidate_id"),
        "source_machine_preview_id": (
            machine_preview.get("source_item", {}).get("id") if isinstance(machine_preview, dict) else None
        ),
        "decision": decision,
        "recommended_track": track,
        "risk_level": risk_level,
        "execution_authorization_scope": scope,
        "requires_nobao_review": True,
        "requires_jenn_decision": requires_jenn,
        "reason": reason,
        "blocked_capabilities": sorted(set(GLOBAL_BLOCKED_CAPABILITIES + blocked)),
        "validation_required": ["docctl status", "docctl doctor"],
        "evidence_required": ["report", "receipt", "review", "validation_summary"],
        "input_errors": input_errors,
        "execution_authorized": False,
    }
    errors = validate_commander_decision(result)
    result["passed"] = not errors
    result["errors"] = errors
    return result


def validate_commander_decision(decision: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("commander_decision") if field not in decision]
    if decision.get("decision") not in DECISIONS:
        errors.append(f"invalid decision: {decision.get('decision')}")
    if decision.get("recommended_track") not in TRACKS:
        errors.append(f"invalid recommended_track: {decision.get('recommended_track')}")
    if decision.get("execution_authorization_scope") not in AUTHORIZATION_SCOPES:
        errors.append(f"invalid execution_authorization_scope: {decision.get('execution_authorization_scope')}")
    if decision.get("execution_authorized") is not False:
        errors.append("Commander output must not directly authorize execution")
    if decision.get("requires_nobao_review") is not True:
        errors.append("Commander output must require Nobao review")
    if decision.get("requires_jenn_decision") and decision.get("execution_authorization_scope") != "blocked_requires_jenn":
        errors.append("Jenn decision outputs must use blocked_requires_jenn")
    if decision.get("decision") == "route_to_local_executor" and decision.get("execution_authorization_scope") != "local_safe_only":
        errors.append("local executor route must use local_safe_only")
    if decision.get("decision") == "route_to_colameta" and decision.get("execution_authorization_scope") != "none":
        errors.append("ColaMeta route must remain preview-only with scope none")
    return errors


def build_track_preview(decision: dict[str, Any], action_type: str | None = None) -> dict[str, Any]:
    errors = validate_commander_decision(decision)
    selected_track = "stop"
    track_authorized = False
    required_inputs: list[str] = []
    expected_outputs: list[str] = []
    validation_commands = ["PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status"]
    preview_errors: list[str] = []

    if errors:
        preview_errors.extend(errors)
    elif decision.get("requires_jenn_decision") or decision.get("execution_authorization_scope") == "blocked_requires_jenn":
        preview_errors.append("Commander decision requires Jenn; selector cannot route")
    elif decision.get("decision") == "route_to_colameta":
        selected_track = "colameta"
        track_authorized = True
        required_inputs = [".colameta/plan.json", ".colameta/prompts/", ".colameta/state.json metadata"]
        expected_outputs = ["colameta_readiness_report", "track_result.json", "receipt", "review"]
    elif decision.get("decision") == "route_to_local_executor":
        selected_track = "local_executor"
        track_authorized = decision.get("execution_authorization_scope") == "local_safe_only"
        required_inputs = ["target_paths", "action_type", "validation_commands", "evidence_required"]
        expected_outputs = ["track_result.json", "validation_summary", "evidence_paths"]
        if action_type and action_type not in LOCAL_SAFE_ACTIONS:
            preview_errors.append(f"action_type is not local-safe: {action_type}")
    else:
        preview_errors.append("Commander decision did not route to an executable track")

    result = {
        "schema_version": "agents-os.track-selector.preview.v0.1",
        "track_preview_id": stable_id("TRACKPREVIEW", [decision.get("decision_id"), selected_track, action_type]),
        "source_decision_id": decision.get("decision_id"),
        "selected_track": selected_track,
        "preview_only": True,
        "track_authorized": bool(track_authorized and not preview_errors),
        "execution_authorization_scope": decision.get("execution_authorization_scope", "none"),
        "action_type": action_type,
        "required_inputs": required_inputs,
        "expected_outputs": expected_outputs,
        "validation_commands": validation_commands,
        "blocked_capabilities": decision.get("blocked_capabilities", GLOBAL_BLOCKED_CAPABILITIES),
        "errors": preview_errors,
    }
    result_errors = validate_track_preview(result)
    result["passed"] = not result_errors
    result["errors"] = sorted(set(result["errors"] + result_errors))
    return result


def validate_track_preview(preview: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("track_preview") if field not in preview]
    if preview.get("selected_track") not in TRACKS:
        errors.append(f"invalid selected_track: {preview.get('selected_track')}")
    if preview.get("preview_only") is not True:
        errors.append("track preview must be preview_only")
    if preview.get("execution_authorization_scope") not in AUTHORIZATION_SCOPES:
        errors.append(f"invalid execution_authorization_scope: {preview.get('execution_authorization_scope')}")
    if preview.get("selected_track") == "local_executor" and preview.get("execution_authorization_scope") != "local_safe_only":
        errors.append("local_executor preview requires local_safe_only")
    if preview.get("selected_track") == "colameta" and preview.get("execution_authorization_scope") != "none":
        errors.append("ColaMeta preview must keep authorization scope none")
    if preview.get("track_authorized") is True and preview.get("selected_track") == "stop":
        errors.append("stop track cannot be authorized")
    return errors


def import_module(path: Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def next_user_action_summary(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": action.get("status"),
        "decision_owner": action.get("decision_owner"),
        "requires_jenn_decision": action.get("requires_jenn_decision"),
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


def validate_next_user_action(prefix: str, action: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for flag in NEXT_USER_ACTION_FALSE_FLAGS:
        if action.get(flag) is not False:
            errors.append(f"{prefix} next_user_action must keep {flag}=false")
    if action.get("status") == "route_choice_required":
        if action.get("decision_owner") != "Jenn":
            errors.append(f"{prefix} next_user_action decision_owner must be Jenn")
        if action.get("requires_jenn_decision") is not True:
            errors.append(f"{prefix} next_user_action must require Jenn decision")
        if not action.get("accepted_route_ids"):
            errors.append(f"{prefix} next_user_action must include accepted route ids")
        if action.get("exact_confirmation_templates_available") is not True:
            errors.append(f"{prefix} next_user_action must point to available confirmation templates")
    return errors


def route_choice_handoff_reconciliation(queue_path: Path = DEFAULT_QUEUE) -> dict[str, Any]:
    errors: list[str] = []
    source_queue = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    machine_preview: dict[str, Any] = {}
    dashboard_summary: dict[str, Any] = {}

    try:
        machine = import_module(MACHINE, "agents_os_machine_for_control_chain")
        normalized = machine.load_queue(source_queue)
        if normalized.get("passed") is not True:
            errors.extend(f"machine queue: {error}" for error in normalized.get("parse_errors", []))
        else:
            machine_preview = machine.build_preview(machine.now_item(normalized))
            errors.extend(f"machine preview: {error}" for error in machine.validate_preview(machine_preview))
    except Exception as exc:  # pragma: no cover - surfaced as validation error
        errors.append(f"Machine handoff read failed: {exc}")

    try:
        dashboard = import_module(DASHBOARD, "agents_os_dashboard_for_control_chain")
        dashboard_summary = dashboard.build_dashboard_summary(source_queue, run_validations=False)
        if dashboard_summary.get("passed") is not True:
            errors.extend(f"dashboard summary: {error}" for error in dashboard_summary.get("errors", []))
    except Exception as exc:  # pragma: no cover - surfaced as validation error
        errors.append(f"Dashboard handoff read failed: {exc}")

    machine_action = machine_preview.get("next_user_action", {}) if machine_preview else {}
    dashboard_action = dashboard_summary.get("next_user_action", {}) if dashboard_summary else {}
    errors.extend(validate_next_user_action("machine", machine_action))
    errors.extend(validate_next_user_action("dashboard", dashboard_action))

    comparable_fields = (
        "status",
        "decision_owner",
        "requires_jenn_decision",
        "accepted_route_ids",
        "template_source_path",
        "exact_confirmation_templates_available",
    )
    for field in comparable_fields:
        if machine_action.get(field) != dashboard_action.get(field):
            errors.append(f"Machine/Dashboard next_user_action mismatch: {field}")

    route_choice_required = (
        machine_action.get("status") == "route_choice_required"
        and dashboard_action.get("status") == "route_choice_required"
    )
    result = {
        "schema_version": "agents-os.control-chain.route-choice-handoff-reconciliation.v0.1",
        "preview_only": True,
        "read_only": True,
        "source_queue_path": rel(source_queue),
        "machine_source_item": machine_preview.get("source_item", {}),
        "machine_next_user_action": next_user_action_summary(machine_action),
        "dashboard_next_user_action": next_user_action_summary(dashboard_action),
        "aligned": not errors,
        "route_choice_required": route_choice_required,
        "decision_owner": "Jenn" if route_choice_required and not errors else None,
        "accepted_route_ids": machine_action.get("accepted_route_ids", []) if route_choice_required else [],
        "route_auto_selection_authorized": False,
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
        "raw_content_output": False,
        "errors": errors,
    }
    result_errors = validate_route_choice_handoff_reconciliation(result)
    result["passed"] = not result_errors
    result["errors"] = sorted(set(result["errors"] + result_errors))
    result["aligned"] = not result["errors"]
    return result


def validate_route_choice_handoff_reconciliation(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.control-chain.route-choice-handoff-reconciliation.v0.1":
        errors.append("route choice handoff reconciliation schema_version is invalid")
    if result.get("preview_only") is not True:
        errors.append("route choice handoff reconciliation must be preview_only")
    if result.get("read_only") is not True:
        errors.append("route choice handoff reconciliation must be read_only")
    for flag in (
        "route_auto_selection_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "write_performed",
        "raw_content_output",
    ):
        if result.get(flag) is not False:
            errors.append(f"route choice handoff reconciliation must keep {flag}=false")
    if result.get("route_choice_required") is True:
        if result.get("decision_owner") != "Jenn":
            errors.append("route choice handoff reconciliation decision owner must be Jenn")
        if result.get("aligned") is not True:
            errors.append("route choice handoff reconciliation must be aligned")
        if result.get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
            errors.append("route choice handoff reconciliation accepted route ids must be A-E")
    return errors


def route_choice_template_readiness(source: Path = ROUTE_SELECTION_PACKAGE) -> dict[str, Any]:
    errors: list[str] = []
    coverage: dict[str, Any] = {}
    try:
        producer = import_module(TASK_PRODUCER, "agents_os_task_producer_template_readiness_for_control_chain")
        coverage = producer.route_choice_template_coverage(source)
        coverage_errors = producer.validate_route_choice_template_coverage(coverage)
        errors.extend(f"Task Producer template coverage: {error}" for error in coverage_errors)
        if coverage.get("passed") is not True:
            errors.extend(f"Task Producer template coverage error: {error}" for error in coverage.get("errors", []))
    except Exception as exc:  # pragma: no cover - surfaced as validation error
        errors.append(f"Task Producer route-choice template coverage failed: {exc}")

    false_flag_failures = [
        flag
        for flag in ROUTE_CHOICE_TEMPLATE_COVERAGE_FALSE_FLAGS
        if coverage.get(flag) is not False
    ]
    if false_flag_failures:
        errors.append(f"route choice template readiness flags not false: {','.join(false_flag_failures)}")

    result = {
        "schema_version": "agents-os.control-chain.route-choice-template-readiness.v0.1",
        "preview_only": True,
        "read_only": True,
        "source_path": coverage.get("source_path", rel(source)),
        "task_producer_coverage_schema": coverage.get("schema_version"),
        "task_producer_coverage_passed": coverage.get("passed"),
        "accepted_route_ids": coverage.get("accepted_route_ids", []),
        "template_count": coverage.get("template_count"),
        "templates_checked": coverage.get("templates_checked"),
        "parsed_route_ids": coverage.get("parsed_route_ids", []),
        "placeholder_goal_blocked": coverage.get("placeholder_goal_blocked"),
        "concrete_new_route_fixture_passed": coverage.get("concrete_new_route_fixture_passed"),
        "workspace_route_state_modified": False,
        "active_queue_modified": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "executor_run_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "plugin_execution_authorized": False,
        "raw_template_output": False,
        "confirmation_text_included": False,
        "errors": errors,
    }
    validation_errors = validate_route_choice_template_readiness(result)
    result["errors"] = sorted(set(errors + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_route_choice_template_readiness(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.control-chain.route-choice-template-readiness.v0.1":
        errors.append("route choice template readiness schema_version is invalid")
    if result.get("preview_only") is not True:
        errors.append("route choice template readiness must be preview_only")
    if result.get("read_only") is not True:
        errors.append("route choice template readiness must be read_only")
    if result.get("task_producer_coverage_schema") != "agents-os.task-producer.route-choice-template-coverage.v0.1":
        errors.append("route choice template readiness must use Task Producer coverage schema")
    if result.get("task_producer_coverage_passed") is not True:
        errors.append("Task Producer route choice template coverage must pass")
    if result.get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice template readiness accepted_route_ids must be A-E")
    if result.get("parsed_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice template readiness parsed_route_ids must be A-E")
    if result.get("template_count") != 5:
        errors.append("route choice template readiness template_count must be 5")
    if result.get("templates_checked") != 5:
        errors.append("route choice template readiness templates_checked must be 5")
    if result.get("placeholder_goal_blocked") is not True:
        errors.append("route choice template readiness must preserve Template E placeholder block")
    if result.get("concrete_new_route_fixture_passed") is not True:
        errors.append("route choice template readiness must prove concrete option E fixture")
    for flag in ROUTE_CHOICE_TEMPLATE_COVERAGE_FALSE_FLAGS:
        if result.get(flag) is not False:
            errors.append(f"route choice template readiness must keep {flag}=false")
    return errors


def route_choice_confirmation_fixture(producer: Any, option_id: str) -> str:
    titles_by_option = {value: key for key, value in producer.ROUTE_CHOICE_TITLES.items()}
    title = titles_by_option[option_id]
    if option_id == "E":
        return (
            f"确认选择 AGENTS OS 下一路线：{title}。\n"
            "路线目标是：端到端预览链路 fixture 验证。"
        )
    return (
        f"确认选择 AGENTS OS 下一路线：{title}。\n"
        "这是端到端预览 fixture；不写真实队列、不推广 NOW、不执行。"
    )


def route_choice_fixture_queue_text() -> str:
    return """# route choice readiness fixture queue

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


def accepted_nobao_review_for(proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "agents-os.queue-manager.review.v0.1",
        "source_proposal_id": proposal.get("proposal_id"),
        "review_status": "accepted",
        "reviewer": "Nobao",
        "requires_jenn_decision": False,
    }


def route_choice_end_to_end_readiness(source: Path = ROUTE_SELECTION_PACKAGE) -> dict[str, Any]:
    errors: list[str] = []
    route_results: list[dict[str, Any]] = []
    route_ids: list[str] = []
    temporary_fixture_write_performed = False
    temporary_fixture_cleaned = False
    fixture_queue_unchanged = True
    temp_dir_path: Path | None = None

    try:
        producer = import_module(TASK_PRODUCER, "agents_os_task_producer_e2e_readiness_for_control_chain")
        route_ids = list(producer.ROUTE_OPTIONS)
        initial_queue_text = route_choice_fixture_queue_text()
        with tempfile.TemporaryDirectory(prefix="agents-os-route-choice-e2e-", dir=WORKSPACE_ROOT) as temp_dir:
            temp_dir_path = Path(temp_dir)
            fixture_queue = temp_dir_path / "route-choice-readiness-queue.md"
            fixture_queue.write_text(initial_queue_text, encoding="utf-8")
            temporary_fixture_write_performed = True
            initial_hash = hashlib.sha256(initial_queue_text.encode("utf-8")).hexdigest()

            for option_id in route_ids:
                stage_errors: list[str] = []
                confirmation_text = route_choice_confirmation_fixture(producer, option_id)
                preview = producer.route_choice_preview(confirmation_text, source)
                preview_errors = validate_route_choice_preview(preview)
                stage_errors.extend(f"preview: {error}" for error in preview_errors)

                proposal = route_choice_queue_proposal(preview)
                stage_errors.extend(f"proposal: {error}" for error in proposal.get("errors", []))

                review = accepted_nobao_review_for(proposal)
                adoption_preview = reviewed_route_adoption_preview(proposal, review, fixture_queue)
                stage_errors.extend(f"adoption preview: {error}" for error in adoption_preview.get("errors", []))

                apply_preview = reviewed_route_adoption_apply_gate(proposal, review, fixture_queue, apply=False)
                stage_errors.extend(f"apply gate preview: {error}" for error in apply_preview.get("errors", []))

                current_hash = hashlib.sha256(fixture_queue.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                route_queue_unchanged = current_hash == initial_hash
                if not route_queue_unchanged:
                    stage_errors.append("fixture queue changed during preview")
                    fixture_queue_unchanged = False

                false_flag_failures: list[str] = []
                false_flag_failures.extend(f"preview.{flag}" for flag in producer.route_choice_preview_false_flags(preview))
                for label, value, flags in (
                    (
                        "proposal",
                        proposal,
                        (
                            "route_adoption_authorized",
                            "workspace_route_state_modified",
                            "active_queue_modified",
                            "write_performed",
                            "queue_write_authorized",
                            "queue_promotion_authorized",
                            "execution_authorized",
                        ),
                    ),
                    (
                        "adoption_preview",
                        adoption_preview,
                        (
                            "route_adoption_authorized",
                            "workspace_route_state_modified",
                            "active_queue_modified",
                            "write_performed",
                            "queue_write_authorized",
                            "queue_promotion_authorized",
                            "execution_authorized",
                        ),
                    ),
                    (
                        "apply_gate_preview",
                        apply_preview,
                        (
                            "route_adoption_authorized",
                            "workspace_route_state_modified",
                            "active_queue_modified",
                            "write_performed",
                            "queue_write_authorized",
                            "queue_promotion_authorized",
                            "execution_authorized",
                        ),
                    ),
                ):
                    false_flag_failures.extend(f"{label}.{flag}" for flag in flags if value.get(flag) is not False)
                if false_flag_failures:
                    stage_errors.append(f"false flags failed: {','.join(false_flag_failures)}")

                selected = preview.get("selected_option", {})
                route_result = {
                    "option_id": option_id,
                    "selected_option_id": selected.get("option_id"),
                    "route_goal_present": bool(selected.get("route_goal")),
                    "route_choice_preview_passed": preview.get("passed") is True and not preview_errors,
                    "route_choice_queue_proposal_passed": proposal.get("passed") is True,
                    "reviewed_route_adoption_preview_passed": adoption_preview.get("passed") is True,
                    "reviewed_route_adoption_apply_preview_passed": apply_preview.get("passed") is True,
                    "queue_adoption_preview_authorized": apply_preview.get("queue_adoption_authorized") is True,
                    "route_adoption_authorized": apply_preview.get("route_adoption_authorized"),
                    "proposed_next_title": proposal.get("proposed_queue_item", {}).get("title"),
                    "fixture_queue_unchanged": route_queue_unchanged,
                    "confirmation_text_included": preview.get("confirmation_text_included"),
                    "raw_confirmation_text_output": False,
                    "raw_template_output": False,
                    "false_flag_failures": false_flag_failures,
                    "errors": sorted(set(stage_errors)),
                    "passed": not stage_errors,
                }
                if not route_result["passed"]:
                    errors.append(f"route {option_id} end-to-end readiness failed")
                route_results.append(route_result)
        temporary_fixture_cleaned = temp_dir_path is not None and not temp_dir_path.exists()
    except Exception as exc:  # pragma: no cover - surfaced as validation error
        errors.append(f"route choice end-to-end readiness failed: {exc}")

    stage_counts = {
        "route_choice_preview_passed": sum(1 for item in route_results if item.get("route_choice_preview_passed") is True),
        "route_choice_queue_proposal_passed": sum(1 for item in route_results if item.get("route_choice_queue_proposal_passed") is True),
        "reviewed_route_adoption_preview_passed": sum(1 for item in route_results if item.get("reviewed_route_adoption_preview_passed") is True),
        "reviewed_route_adoption_apply_preview_passed": sum(1 for item in route_results if item.get("reviewed_route_adoption_apply_preview_passed") is True),
        "queue_adoption_preview_authorized": sum(1 for item in route_results if item.get("queue_adoption_preview_authorized") is True),
    }
    passed_route_ids = [item["option_id"] for item in route_results if item.get("passed") is True]
    result = {
        "schema_version": "agents-os.control-chain.route-choice-end-to-end-readiness.v0.1",
        "preview_only": True,
        "fixture_only": True,
        "source_path": rel(source),
        "active_queue_path": rel(DEFAULT_QUEUE),
        "accepted_route_ids": route_ids,
        "checked_route_ids": route_ids,
        "passed_route_ids": passed_route_ids,
        "route_count": len(route_results),
        "stage_counts": stage_counts,
        "route_results": route_results,
        "temporary_fixture_write_performed": temporary_fixture_write_performed,
        "temporary_fixture_cleaned": temporary_fixture_cleaned,
        "fixture_queue_unchanged": fixture_queue_unchanged,
        "active_queue_modified": False,
        "real_queue_write_performed": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "route_selected": False,
        "route_auto_selection_authorized": False,
        "route_adoption_authorized": False,
        "execution_authorized": False,
        "provider_call_authorized": False,
        "service_start_authorized": False,
        "executor_run_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "runtime_plugin_activation_authorized": False,
        "plugin_execution_authorized": False,
        "raw_confirmation_text_output": False,
        "raw_template_output": False,
        "errors": errors,
    }
    validation_errors = validate_route_choice_end_to_end_readiness(result)
    result["errors"] = sorted(set(errors + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_route_choice_end_to_end_readiness(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.control-chain.route-choice-end-to-end-readiness.v0.1":
        errors.append("route choice end-to-end readiness schema_version is invalid")
    if result.get("preview_only") is not True:
        errors.append("route choice end-to-end readiness must be preview_only")
    if result.get("fixture_only") is not True:
        errors.append("route choice end-to-end readiness must be fixture_only")
    if result.get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice end-to-end readiness accepted_route_ids must be A-E")
    if result.get("checked_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice end-to-end readiness checked_route_ids must be A-E")
    if result.get("passed_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice end-to-end readiness passed_route_ids must be A-E")
    if result.get("route_count") != 5:
        errors.append("route choice end-to-end readiness route_count must be 5")
    if result.get("temporary_fixture_write_performed") is not True:
        errors.append("route choice end-to-end readiness must record temporary fixture write")
    if result.get("temporary_fixture_cleaned") is not True:
        errors.append("route choice end-to-end readiness must clean temporary fixture")
    if result.get("fixture_queue_unchanged") is not True:
        errors.append("route choice end-to-end readiness fixture queue must remain unchanged")
    for flag in ROUTE_CHOICE_E2E_FALSE_FLAGS:
        if result.get(flag) is not False:
            errors.append(f"route choice end-to-end readiness must keep {flag}=false")
    stage_counts = result.get("stage_counts", {})
    for stage in (
        "route_choice_preview_passed",
        "route_choice_queue_proposal_passed",
        "reviewed_route_adoption_preview_passed",
        "reviewed_route_adoption_apply_preview_passed",
        "queue_adoption_preview_authorized",
    ):
        if stage_counts.get(stage) != 5:
            errors.append(f"route choice end-to-end readiness {stage} count must be 5")
    for item in result.get("route_results", []):
        option_id = item.get("option_id")
        if item.get("selected_option_id") != option_id:
            errors.append(f"route {option_id} selected_option_id mismatch")
        if item.get("passed") is not True:
            errors.append(f"route {option_id} did not pass readiness")
        if item.get("fixture_queue_unchanged") is not True:
            errors.append(f"route {option_id} changed fixture queue")
        if item.get("confirmation_text_included") is not False:
            errors.append(f"route {option_id} included raw confirmation text")
        if item.get("raw_confirmation_text_output") is not False:
            errors.append(f"route {option_id} output raw confirmation text")
        if item.get("raw_template_output") is not False:
            errors.append(f"route {option_id} output raw template")
        if item.get("false_flag_failures"):
            errors.append(f"route {option_id} has false flag failures")
        for stage in (
            "route_choice_preview_passed",
            "route_choice_queue_proposal_passed",
            "reviewed_route_adoption_preview_passed",
            "reviewed_route_adoption_apply_preview_passed",
            "queue_adoption_preview_authorized",
        ):
            if item.get(stage) is not True:
                errors.append(f"route {option_id} {stage} must be true")
        if item.get("route_adoption_authorized") is not False:
            errors.append(f"route {option_id} must not authorize route adoption in preview")
        if option_id == "E" and item.get("route_goal_present") is not True:
            errors.append("route E fixture must include concrete route goal")
    return errors


def route_choice_adoption_bundle_preview(
    confirmation_text: str,
    queue_path: Path = DEFAULT_QUEUE,
    source: Path = ROUTE_SELECTION_PACKAGE,
    *,
    fixture_only: bool = False,
) -> dict[str, Any]:
    errors: list[str] = []
    producer = import_module(TASK_PRODUCER, "agents_os_task_producer_adoption_bundle_for_control_chain")

    route_preview = producer.route_choice_preview(confirmation_text, source)
    route_preview_errors = validate_route_choice_preview(route_preview)
    errors.extend(f"route choice preview: {error}" for error in route_preview_errors)

    proposal = route_choice_queue_proposal(route_preview)
    errors.extend(f"route choice proposal: {error}" for error in proposal.get("errors", []))

    review = accepted_nobao_review_for(proposal)
    adoption_preview = reviewed_route_adoption_preview(proposal, review, queue_path)
    errors.extend(f"reviewed route adoption preview: {error}" for error in adoption_preview.get("errors", []))

    apply_preview = reviewed_route_adoption_apply_gate(proposal, review, queue_path, apply=False)
    errors.extend(f"reviewed route adoption apply preview: {error}" for error in apply_preview.get("errors", []))

    selected = route_preview.get("selected_option", {}) if isinstance(route_preview, dict) else {}
    item = proposal.get("proposed_queue_item", {}) if isinstance(proposal, dict) else {}
    result = {
        "schema_version": "agents-os.control-chain.route-choice-adoption-bundle-preview.v0.1",
        "preview_only": True,
        "fixture_only": fixture_only,
        "source_path": rel(source),
        "queue_path": rel(queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path),
        "input_character_count": len(confirmation_text),
        "confirmation_text_included": False,
        "raw_confirmation_text_output": False,
        "raw_template_output": False,
        "route_choice_preview_passed": route_preview.get("passed") is True and not route_preview_errors,
        "route_choice_detected": route_preview.get("route_choice_detected") is True,
        "selected_route_id": selected.get("option_id"),
        "selected_route_title": selected.get("title"),
        "selected_first_safe_package": selected.get("first_safe_package"),
        "route_goal_present": bool(selected.get("route_goal")),
        "queue_proposal_passed": proposal.get("passed") is True,
        "proposal_id": proposal.get("proposal_id"),
        "proposed_next_title": item.get("title"),
        "review_object_generated": True,
        "review_status": review.get("review_status"),
        "reviewer": review.get("reviewer"),
        "review_requires_jenn_decision": review.get("requires_jenn_decision"),
        "reviewed_route_adoption_preview_passed": adoption_preview.get("passed") is True,
        "reviewed_route_adoption_apply_preview_passed": apply_preview.get("passed") is True,
        "can_apply_with_separate_apply_gate": apply_preview.get("queue_adoption_authorized") is True,
        "real_queue_write_performed": False,
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
        "plugin_execution_authorized": False,
        "next_required_gate": "reviewed-route-adoption-apply-gate with explicit apply authorization after Jenn route choice review",
        "errors": sorted(set(errors)),
    }
    validation_errors = validate_route_choice_adoption_bundle_preview(result)
    result["errors"] = sorted(set(result["errors"] + validation_errors))
    result["passed"] = not result["errors"]
    return result


def validate_route_choice_adoption_bundle_preview(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if result.get("schema_version") != "agents-os.control-chain.route-choice-adoption-bundle-preview.v0.1":
        errors.append("route choice adoption bundle preview schema_version is invalid")
    if result.get("preview_only") is not True:
        errors.append("route choice adoption bundle preview must be preview_only")
    if result.get("confirmation_text_included") is not False:
        errors.append("route choice adoption bundle preview must not include confirmation text")
    if result.get("raw_confirmation_text_output") is not False:
        errors.append("route choice adoption bundle preview must not output raw confirmation text")
    if result.get("raw_template_output") is not False:
        errors.append("route choice adoption bundle preview must not output raw template text")
    for flag in (
        "real_queue_write_performed",
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
        "plugin_execution_authorized",
    ):
        if result.get(flag) is not False:
            errors.append(f"route choice adoption bundle preview must keep {flag}=false")
    if not result.get("errors"):
        if result.get("route_choice_preview_passed") is not True:
            errors.append("route choice adoption bundle preview requires passing route choice preview")
        if result.get("route_choice_detected") is not True:
            errors.append("route choice adoption bundle preview must detect route choice")
        if result.get("selected_route_id") not in ["A", "B", "C", "D", "E"]:
            errors.append("route choice adoption bundle preview selected_route_id must be A-E")
        if not result.get("selected_first_safe_package"):
            errors.append("route choice adoption bundle preview must include first safe package")
        if result.get("queue_proposal_passed") is not True:
            errors.append("route choice adoption bundle preview requires passing queue proposal")
        if not result.get("proposed_next_title"):
            errors.append("route choice adoption bundle preview must include proposed NEXT title")
        if result.get("review_object_generated") is not True:
            errors.append("route choice adoption bundle preview must generate review object")
        if result.get("review_status") != "accepted":
            errors.append("route choice adoption bundle preview review_status must be accepted")
        if result.get("reviewer") != "Nobao":
            errors.append("route choice adoption bundle preview reviewer must be Nobao")
        if result.get("review_requires_jenn_decision") is not False:
            errors.append("route choice adoption bundle preview review must not require Jenn decision")
        if result.get("reviewed_route_adoption_preview_passed") is not True:
            errors.append("route choice adoption bundle preview requires passing adoption preview")
        if result.get("reviewed_route_adoption_apply_preview_passed") is not True:
            errors.append("route choice adoption bundle preview requires passing apply-gate preview")
        if result.get("can_apply_with_separate_apply_gate") is not True:
            errors.append("route choice adoption bundle preview must identify separate apply gate availability")
    return errors


def metadata_for_json(path: Path, list_keys: tuple[str, ...]) -> dict[str, Any]:
    resolved, error = safe_resolve(path)
    if error or resolved is None or not resolved.exists() or not resolved.is_file():
        return {"path": rel(path), "exists": False}
    data = load_json(resolved)
    return {
        "path": rel(resolved),
        "exists": True,
        "object_keys": sorted(data.keys()),
        "list_counts": {key: len(data.get(key, [])) for key in list_keys if isinstance(data.get(key), list)},
        "raw_content_output": False,
    }


def prior_colameta_evidence() -> dict[str, Any]:
    paths = [
        WORKSPACE_ROOT / ".colameta/runtime/plan-previews/2026-07-02-agents-os-colameta-first-run-dry-run-preview-v0.1.json",
        WORKSPACE_ROOT / ".colameta/reports/2026-07-02-agents-os-colameta-first-run-dry-run-report-v0.1.md",
        WORKSPACE_ROOT / ".colameta/audits/2026-07-02-agents-os-colameta-first-run-dry-run-audit-v0.1.md",
    ]
    return {
        "expected_count": len(paths),
        "present_count": sum(1 for path in paths if path.exists()),
        "paths": [rel(path) for path in paths if path.exists()],
        "raw_content_read": False,
    }


def colameta_readiness(track_preview: dict[str, Any]) -> dict[str, Any]:
    preview_errors = validate_track_preview(track_preview)
    errors = list(preview_errors)
    if track_preview.get("selected_track") != "colameta":
        errors.append("track preview is not for ColaMeta")
    if track_preview.get("track_authorized") is not True:
        errors.append("track preview is not authorized")
    preflight_result: dict[str, Any] = {}
    if not errors:
        preflight = import_module(COLAMETA_PREFLIGHT, "colameta_executor_preflight")
        preflight_result = preflight.preflight()
        if not preflight_result.get("passed"):
            errors.append("ColaMeta preflight did not pass")
    readiness = {
        "preflight": {
            "passed": preflight_result.get("passed"),
            "gate_status": preflight_result.get("gate_status"),
            "read_only": preflight_result.get("read_only"),
            "summary_only": preflight_result.get("summary_only"),
            "plan": preflight_result.get("plan", {}),
            "prompts": preflight_result.get("prompts", {}),
            "memory": preflight_result.get("memory", {}),
            "docctl": preflight_result.get("docctl", {}),
        },
        "state": metadata_for_json(WORKSPACE_ROOT / ".colameta/state.json", ("versions",)),
        "todolist": metadata_for_json(WORKSPACE_ROOT / ".colameta/todolist.json", ("items",)),
        "decisions": metadata_for_json(WORKSPACE_ROOT / ".colameta/decisions.json", ("decisions",)),
        "prior_dry_run_evidence": prior_colameta_evidence(),
    }
    result = {
        "schema_version": "agents-os.control-chain.track-result.v0.1",
        "track_result_id": stable_id("TRACKRESULT", [track_preview.get("track_preview_id"), readiness]),
        "selected_track": "colameta",
        "source_decision_id": track_preview.get("source_decision_id"),
        "source_track_preview_id": track_preview.get("track_preview_id"),
        "preview_only": True,
        "write_performed": False,
        "execution_performed": False,
        "validation_passed": not errors,
        "evidence_paths": [],
        "blocked_capabilities": track_preview.get("blocked_capabilities", GLOBAL_BLOCKED_CAPABILITIES),
        "errors": errors,
        "effects": {
            "executor_real_run": False,
            "service_started": False,
            "provider_call_performed": False,
            "memory_write_performed": False,
            "colameta_plan_modified": False,
            "colameta_state_modified": False,
            "colameta_memory_content_written": False,
            "external_write_performed": False,
        },
        "colameta_readiness": readiness,
    }
    result_errors = validate_track_result(result)
    result["passed"] = not result_errors
    result["errors"] = sorted(set(result["errors"] + result_errors))
    return result


def git_status_short() -> list[str]:
    run = subprocess.run(["git", "status", "--short"], cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=False)
    if run.returncode != 0:
        return ["git status failed"]
    return [line for line in run.stdout.splitlines() if line.strip()]


def command_is_safe_validation(command: str) -> tuple[bool, str]:
    forbidden = [";", "&&", "||", "|", "`", "$(", ">", "<"]
    if any(token in command for token in forbidden):
        return False, "validation command contains shell control characters"
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return False, f"validation command parse failed: {exc}"
    if not parts:
        return False, "validation command is empty"
    if parts[0].endswith("="):
        return False, "environment assignment without command is not allowed"
    if parts[0] == "PYTHONDONTWRITEBYTECODE=1":
        parts = parts[1:]
    if not parts or parts[0] != "python3":
        return False, "only python3 validation commands are allowed in v0.1"
    return True, ""


def target_write_allowed(path: Path, action_type: str) -> tuple[Path | None, str | None]:
    if action_type not in LOCAL_SAFE_ACTIONS or action_type == "run_validation_command":
        return None, "action type does not write a target path"
    if is_protected_path(path):
        return None, f"target path is protected: {path}"
    candidate = path if path.is_absolute() else WORKSPACE_ROOT / path
    resolved, resolve_error = safe_resolve(candidate)
    if resolve_error:
        return None, f"target path could not be resolved: {resolve_error}"
    if resolved is None:
        return None, f"target path could not be resolved: {path}"
    if is_protected_path(resolved):
        return None, f"target path resolves to protected path: {path}"
    if not is_under_workspace(resolved, WORKSPACE_ROOT):
        return None, f"target path is outside workspace: {path}"
    if action_type == "update_current_state":
        expected = (WORKSPACE_ROOT / "CURRENT_STATE.md").resolve()
        if resolved != expected:
            return None, "update_current_state may only target CURRENT_STATE.md"
    else:
        allowed_roots = [
            REGISTRY_DIR / "reports",
            REGISTRY_DIR / "receipts",
            REGISTRY_DIR / "reviews",
            REGISTRY_DIR / "drafts",
        ]
        if not any(is_under(resolved, root.resolve()) for root in allowed_roots):
            return None, "governance writes must stay under registry reports/receipts/reviews/drafts"
    if not resolved.parent.exists():
        return None, f"target parent does not exist: {rel(resolved.parent)}"
    return resolved, None


def local_executor_run(
    track_preview: dict[str, Any],
    action_type: str,
    *,
    target_path: Path | None = None,
    content: str | None = None,
    command: str | None = None,
    perform_write: bool = True,
) -> dict[str, Any]:
    errors = validate_track_preview(track_preview)
    if track_preview.get("selected_track") != "local_executor":
        errors.append("track preview is not for local executor")
    if track_preview.get("execution_authorization_scope") != "local_safe_only":
        errors.append("local executor requires local_safe_only scope")
    if track_preview.get("track_authorized") is not True:
        errors.append("track preview is not authorized")
    if action_type in FORBIDDEN_ACTIONS or action_type not in LOCAL_SAFE_ACTIONS:
        errors.append(f"action_type is not allowed: {action_type}")

    status_before = git_status_short()
    if action_type != "run_validation_command" and status_before:
        errors.append("dirty tracked worktree before local executor action")

    validation_details: dict[str, Any] = {}
    write_performed = False
    execution_performed = False

    if not errors and action_type == "run_validation_command":
        if command is None:
            errors.append("validation command is required")
        else:
            safe, reason = command_is_safe_validation(command)
            if not safe:
                errors.append(reason)
            else:
                parts = shlex.split(command)
                if parts and parts[0] == "PYTHONDONTWRITEBYTECODE=1":
                    parts = parts[1:]
                run = subprocess.run(parts, cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=False)
                execution_performed = True
                validation_details = {
                    "command": command,
                    "returncode": run.returncode,
                    "stdout_excerpt": run.stdout.strip()[:200],
                    "stderr_excerpt": run.stderr.strip()[:200],
                }
                if run.returncode != 0:
                    errors.append("validation command failed")

    if not errors and action_type != "run_validation_command":
        if target_path is None or content is None:
            errors.append("target_path and content are required for write actions")
        else:
            resolved, path_error = target_write_allowed(target_path, action_type)
            if path_error or resolved is None:
                errors.append(path_error or "target path not allowed")
            else:
                if perform_write:
                    resolved.write_text(content, encoding="utf-8")
                    write_performed = True
                execution_performed = True

    result = {
        "schema_version": "agents-os.control-chain.track-result.v0.1",
        "track_result_id": stable_id("TRACKRESULT", [track_preview.get("track_preview_id"), action_type, errors]),
        "selected_track": "local_executor",
        "source_decision_id": track_preview.get("source_decision_id"),
        "source_track_preview_id": track_preview.get("track_preview_id"),
        "preview_only": False,
        "write_performed": write_performed,
        "execution_performed": execution_performed,
        "validation_passed": not errors,
        "evidence_paths": [],
        "blocked_capabilities": track_preview.get("blocked_capabilities", GLOBAL_BLOCKED_CAPABILITIES),
        "errors": errors,
        "effects": {
            "provider_call_performed": False,
            "service_started": False,
            "runtime_plugin_activation_performed": False,
            "external_write_performed": False,
            "formal_memory_written": False,
            "state_private_read": False,
            "active_queue_modified": False,
        },
        "validation_details": validation_details,
    }
    result_errors = validate_track_result(result)
    result["passed"] = not result_errors
    result["errors"] = sorted(set(result["errors"] + result_errors))
    return result


def validate_track_result(result: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("track_result") if field not in result]
    if result.get("selected_track") not in ("colameta", "local_executor"):
        errors.append(f"invalid selected_track: {result.get('selected_track')}")
    if result.get("selected_track") == "colameta":
        if result.get("preview_only") is not True:
            errors.append("ColaMeta result must remain preview_only")
        if result.get("execution_performed") is not False:
            errors.append("ColaMeta result must not perform execution")
    if result.get("write_performed") is not False and result.get("selected_track") != "local_executor":
        errors.append("only local executor may perform local writes")
    effects = result.get("effects", {})
    for flag in (
        "provider_call_performed",
        "service_started",
        "external_write_performed",
        "state_private_read",
    ):
        if effects.get(flag) is True:
            errors.append(f"forbidden effect performed: {flag}")
    return errors


def source_identifier(source_payload: dict[str, Any]) -> str | None:
    for key in (
        "track_result_id",
        "mutation_id",
        "proposal_id",
        "track_preview_id",
        "decision_id",
        "candidate_id",
    ):
        value = source_payload.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def failure_source_kind(source_payload: dict[str, Any], context: dict[str, Any] | None = None) -> str:
    if context and context.get("source_kind"):
        return str(context["source_kind"])
    schema_version = source_payload.get("schema_version")
    if schema_version:
        return str(schema_version)
    return "unknown"


def failure_scan_text(
    source_payload: dict[str, Any],
    context: dict[str, Any] | None,
    validation_errors: list[str],
) -> str:
    text_parts = [
        failure_source_kind(source_payload, context),
        str(source_identifier(source_payload) or ""),
        "\n".join(str(error) for error in source_payload.get("errors", []) if error),
        "\n".join(validation_errors),
        str(source_payload.get("selected_track", "")),
        str(source_payload.get("action_type", "")),
    ]
    if context:
        text_parts.extend(
            str(context.get(key, ""))
            for key in ("error", "reason", "category_hint", "source_kind")
        )
    return "\n".join(text_parts)


def track_result_schema_errors(source_payload: dict[str, Any]) -> list[str]:
    if source_payload.get("schema_version") != "agents-os.control-chain.track-result.v0.1":
        return []
    return validate_track_result(source_payload)


def classify_failure(source_payload: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Classify a failed control-chain output without retrying or repairing."""
    validation_errors = track_result_schema_errors(source_payload)
    scan_text = failure_scan_text(source_payload, context, validation_errors)
    hinted = str((context or {}).get("category_hint", ""))

    category = "validation_failed"
    if hinted in FAILURE_CATEGORIES:
        category = hinted
    elif validation_errors:
        category = "executor_output_invalid"
    elif FAILURE_PATTERNS["protected_path_detected"].search(scan_text):
        category = "protected_path_detected"
    elif FAILURE_PATTERNS["dirty_worktree_conflict"].search(scan_text):
        category = "dirty_worktree_conflict"
    elif FAILURE_PATTERNS["scope_violation"].search(scan_text):
        category = "scope_violation"
    elif FAILURE_PATTERNS["p3_signal_detected"].search(scan_text):
        category = "p3_signal_detected"
    elif FAILURE_PATTERNS["unknown_action_type"].search(scan_text):
        category = "unknown_action_type"
    elif FAILURE_PATTERNS["executor_output_invalid"].search(scan_text):
        category = "executor_output_invalid"
    elif (
        source_payload.get("validation_passed") is False
        or source_payload.get("passed") is False
        or FAILURE_PATTERNS["validation_failed"].search(scan_text)
    ):
        category = "validation_failed"

    policy = REPAIR_POLICY[category]
    severity = "red" if category in {"protected_path_detected", "p3_signal_detected"} else "yellow"
    requires_jenn = category in {"protected_path_detected", "p3_signal_detected"}
    return {
        "category": category,
        "severity": severity,
        "repair_attempt_allowed": policy["repair_attempt_allowed"],
        "max_repair_attempts": policy["max_repair_attempts"],
        "requires_jenn_decision": requires_jenn,
        "classification_errors": validation_errors,
    }


def build_failure_report(source_payload: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    classification = classify_failure(source_payload, context)
    source_id = source_identifier(source_payload)
    failure = {
        "schema_version": "agents-os.failure.report.v0.1",
        "failure_id": stable_id(
            "FAILURE",
            [
                failure_source_kind(source_payload, context),
                source_id,
                classification["category"],
                source_payload.get("errors", []),
            ],
        ),
        "source_kind": failure_source_kind(source_payload, context),
        "source_id": source_id,
        "category": classification["category"],
        "severity": classification["severity"],
        "repair_attempt_allowed": classification["repair_attempt_allowed"],
        "max_repair_attempts": classification["max_repair_attempts"],
        "repair_attempts_performed": 0,
        "queue_promotion_allowed": False,
        "silent_retry_authorized": False,
        "destructive_cleanup_authorized": False,
        "provider_call_authorized": False,
        "external_write_authorized": False,
        "memory_write_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": classification["requires_jenn_decision"],
        "evidence_required": ["failure_report", "review", "validation_summary"],
        "source_errors": [str(error) for error in source_payload.get("errors", []) if error],
        "classification_errors": classification["classification_errors"],
        "raw_content_output": False,
    }
    errors = validate_failure_report(failure)
    failure["passed"] = not errors
    failure["errors"] = errors
    return failure


def validate_failure_report(report: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("failure_report") if field not in report]
    category = report.get("category")
    if category not in FAILURE_CATEGORIES:
        errors.append(f"invalid failure category: {category}")
    if report.get("queue_promotion_allowed") is not False:
        errors.append("failure report must not allow queue promotion")
    if report.get("silent_retry_authorized") is not False:
        errors.append("failure report must not authorize silent retry")
    if report.get("destructive_cleanup_authorized") is not False:
        errors.append("failure report must not authorize destructive cleanup")
    for flag in ("provider_call_authorized", "external_write_authorized", "memory_write_authorized"):
        if report.get(flag) is not False:
            errors.append(f"failure report must not authorize {flag}")
    if report.get("requires_nobao_review") is not True:
        errors.append("failure report must require Nobao review")
    if category in REPAIR_POLICY:
        policy = REPAIR_POLICY[category]
        if report.get("repair_attempt_allowed") is not policy["repair_attempt_allowed"]:
            errors.append("failure report repair policy does not match category")
        if report.get("max_repair_attempts") != policy["max_repair_attempts"]:
            errors.append("failure report max repair attempts does not match category")
    if report.get("repair_attempts_performed") != 0:
        errors.append("failure report must not perform repair attempts")
    return errors


def build_stop_loop_result(failure_report: dict[str, Any]) -> dict[str, Any]:
    errors = validate_failure_report(failure_report)
    result = {
        "schema_version": "agents-os.stop-loop.result.v0.1",
        "stop_loop_id": stable_id("STOPLOOP", [failure_report.get("failure_id"), failure_report.get("category")]),
        "source_failure_id": failure_report.get("failure_id"),
        "status": "stopped_for_review",
        "queue_promoted": False,
        "repair_attempt_performed": False,
        "silent_retry_performed": False,
        "destructive_cleanup_performed": False,
        "provider_call_performed": False,
        "external_write_performed": False,
        "memory_write_performed": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": failure_report.get("requires_jenn_decision") is True,
        "evidence_required": ["failure_report", "review", "validation_summary"],
        "errors": errors,
    }
    result_errors = validate_stop_loop_result(result)
    result["passed"] = not result_errors
    result["errors"] = sorted(set(result["errors"] + result_errors))
    return result


def validate_stop_loop_result(result: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("stop_loop_result") if field not in result]
    if result.get("status") != "stopped_for_review":
        errors.append("stop loop must stop for review")
    for flag in (
        "queue_promoted",
        "repair_attempt_performed",
        "silent_retry_performed",
        "destructive_cleanup_performed",
        "provider_call_performed",
        "external_write_performed",
        "memory_write_performed",
    ):
        if result.get(flag) is not False:
            errors.append(f"stop loop forbidden effect performed: {flag}")
    if result.get("requires_nobao_review") is not True:
        errors.append("stop loop must require Nobao review")
    return errors


def first_next_title(queue_text: str) -> str | None:
    in_next = False
    for line in queue_text.splitlines():
        if line.strip() == "## NEXT":
            in_next = True
            continue
        if in_next and line.startswith("## "):
            return None
        if in_next:
            match = re.match(r"^###\s+NEXT-\d{3}:\s+(.+?)\s*$", line)
            if match:
                return match.group(1)
    return None


def queue_update_proposal(track_result: dict[str, Any], queue_path: Path = DEFAULT_QUEUE) -> dict[str, Any]:
    errors = validate_track_result(track_result)
    queue_text = queue_path.read_text(encoding="utf-8") if queue_path.exists() else ""
    proposed_next = first_next_title(queue_text)
    can_close_now = track_result.get("validation_passed") is True and not errors
    proposal = {
        "schema_version": "agents-os.queue-manager.proposal.v0.1",
        "proposal_id": stable_id("QUEUEPROPOSAL", [track_result.get("track_result_id"), proposed_next, can_close_now]),
        "source_track_result_id": track_result.get("track_result_id"),
        "proposal_only": True,
        "active_queue_modified": False,
        "write_performed": False,
        "close_current_now": bool(can_close_now),
        "promote_next_title": proposed_next if can_close_now else None,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "blocked_reason": None if can_close_now else "track result is not validated",
        "errors": errors,
    }
    proposal_errors = validate_queue_proposal(proposal)
    proposal["passed"] = not proposal_errors
    proposal["errors"] = sorted(set(proposal["errors"] + proposal_errors))
    return proposal


def validate_queue_proposal(proposal: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("queue_proposal") if field not in proposal]
    if proposal.get("proposal_only") is not True:
        errors.append("queue proposal must remain proposal_only")
    if proposal.get("active_queue_modified") is not False:
        errors.append("queue proposal must not modify active queue")
    if proposal.get("write_performed") is not False:
        errors.append("queue proposal must not perform writes")
    if proposal.get("requires_nobao_review") is not True:
        errors.append("queue proposal must require Nobao review")
    return errors


def validate_route_choice_preview(preview: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if preview.get("schema_version") != "agents-os.task-producer.route-choice-preview.v0.1":
        errors.append("route choice preview schema_version is invalid")
    if preview.get("passed") is not True:
        errors.append("route choice preview must be passed")
    if preview.get("preview_only") is not True:
        errors.append("route choice preview must be preview_only")
    if preview.get("confirmation_text_included") is not False:
        errors.append("route choice preview must not include raw confirmation text")
    if preview.get("route_choice_detected") is not True:
        errors.append("route choice preview must detect a route choice")
    selected = preview.get("selected_option", {})
    if not selected.get("option_id") or not selected.get("first_safe_package"):
        errors.append("route choice preview must include selected option id and first safe package")
    for flag in (
        "workspace_route_state_modified",
        "active_queue_modified",
        "queue_write_authorized",
        "queue_promotion_authorized",
        "route_auto_selection_authorized",
        "execution_authorized",
        "provider_call_authorized",
        "service_start_authorized",
        "executor_run_authorized",
        "external_write_authorized",
        "memory_write_authorized",
        "runtime_plugin_activation_authorized",
        "plugin_execution_authorized",
    ):
        if preview.get(flag) is not False:
            errors.append(f"route choice preview flag must be false: {flag}")
    return errors


def route_choice_queue_proposal(preview: dict[str, Any]) -> dict[str, Any]:
    errors = validate_route_choice_preview(preview)
    selected = preview.get("selected_option", {}) if isinstance(preview, dict) else {}
    option_id = selected.get("option_id")
    first_safe_package = selected.get("first_safe_package")
    route_title = selected.get("title")
    must_keep = selected.get("must_keep", [])
    proposed_queue_item = {
        "lane": "NEXT",
        "title": first_safe_package,
        "body_lines": [
            f"Route option: {option_id} - {route_title}",
            "Source: explicit Jenn route-choice preview",
            "Mode: prepare first safe package only",
            "Boundary: queue adoption requires separate reviewed mutation gate",
        ]
        + [f"Must keep: {item}" for item in must_keep if item],
    }
    proposal = {
        "schema_version": "agents-os.queue-manager.route-choice-proposal.v0.1",
        "proposal_id": stable_id("ROUTEQUEUEPROPOSAL", [option_id, first_safe_package, must_keep]),
        "source_route_choice_option_id": option_id,
        "source_route_choice_preview_schema": preview.get("schema_version"),
        "proposal_only": True,
        "preview_only": True,
        "route_choice_detected": preview.get("route_choice_detected") is True,
        "route_adoption_authorized": False,
        "workspace_route_state_modified": False,
        "active_queue_modified": False,
        "write_performed": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "proposed_queue_item": proposed_queue_item,
        "blocked_capabilities": ROUTE_CHOICE_PROPOSAL_BLOCKED_CAPABILITIES,
        "evidence_required": ["route_choice_preview", "queue_proposal_review", "validation_summary"],
        "errors": errors,
    }
    proposal_errors = validate_route_choice_queue_proposal(proposal)
    all_errors = sorted(set(proposal["errors"] + proposal_errors))
    proposal["passed"] = not all_errors
    proposal["errors"] = all_errors
    return proposal


def validate_route_choice_queue_proposal(proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if proposal.get("schema_version") != "agents-os.queue-manager.route-choice-proposal.v0.1":
        errors.append("route choice queue proposal schema_version is invalid")
    for flag in (
        "proposal_only",
        "preview_only",
        "route_choice_detected",
        "requires_nobao_review",
    ):
        if proposal.get(flag) is not True:
            errors.append(f"route choice queue proposal flag must be true: {flag}")
    for flag in (
        "route_adoption_authorized",
        "workspace_route_state_modified",
        "active_queue_modified",
        "write_performed",
        "queue_write_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
    ):
        if proposal.get(flag) is not False:
            errors.append(f"route choice queue proposal flag must be false: {flag}")
    item = proposal.get("proposed_queue_item", {})
    if item.get("lane") != "NEXT":
        errors.append("route choice queue proposal must propose NEXT lane")
    if not item.get("title"):
        errors.append("route choice queue proposal must include proposed item title")
    if proposal.get("source_route_choice_option_id") not in {"A", "B", "C", "D", "E"}:
        errors.append(f"invalid route option id: {proposal.get('source_route_choice_option_id')}")
    return errors


def proposed_queue_item_text(item: dict[str, Any]) -> str:
    body_lines = item.get("body_lines", [])
    if not isinstance(body_lines, list):
        body_lines = []
    return "\n".join([str(item.get("title", "")), *[str(line) for line in body_lines]])


def reviewed_route_adoption_preview(
    proposal: dict[str, Any],
    review: dict[str, Any],
    queue_path: Path = DEFAULT_QUEUE,
) -> dict[str, Any]:
    errors = validate_route_choice_queue_proposal(proposal)
    if proposal.get("passed") is not True:
        errors.append("route choice queue proposal must be passed")
    errors.extend(validate_queue_review(review, proposal))
    if is_protected_path(queue_path):
        errors.append(f"queue path is protected: {queue_path}")

    candidate = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    resolved, resolve_error = safe_resolve(candidate)
    mutation_preview: dict[str, Any] = {}
    if resolve_error or resolved is None:
        errors.append(f"queue path could not be resolved: {resolve_error or queue_path}")
    elif not is_under_workspace(resolved, WORKSPACE_ROOT):
        errors.append(f"queue path is outside workspace: {queue_path}")
    elif not resolved.exists() or not resolved.is_file():
        errors.append(f"queue path is not a file: {rel(resolved)}")
    else:
        queue_text = resolved.read_text(encoding="utf-8")
        now_blocks = queue_lane_blocks(queue_text, "NOW")
        next_blocks = queue_lane_blocks(queue_text, "NEXT")
        item = proposal.get("proposed_queue_item", {})
        signals = queue_p3_signals(proposed_queue_item_text(item))
        if len(now_blocks) != 1:
            errors.append(f"expected exactly one NOW before route adoption preview, got {len(now_blocks)}")
        if signals:
            errors.append(f"proposed route queue item contains P3 signals: {','.join(signals)}")
        mutation_preview = {
            "queue_path": rel(resolved),
            "target_lane": "NEXT",
            "would_append_next_title": item.get("title"),
            "would_append_next_body_lines": item.get("body_lines", []),
            "next_count_before": len(next_blocks),
            "next_count_after_preview": len(next_blocks) + 1 if not errors else None,
            "exactly_one_now_before": len(now_blocks) == 1,
            "would_leave_now_unchanged": True,
            "would_promote_now": False,
        }

    result = {
        "schema_version": "agents-os.queue-manager.reviewed-route-adoption-preview.v0.1",
        "preview_id": stable_id(
            "ROUTEADOPTIONPREVIEW",
            [proposal.get("proposal_id"), review.get("review_status"), queue_path.as_posix()],
        ),
        "source_proposal_id": proposal.get("proposal_id"),
        "source_review_status": review.get("review_status"),
        "preview_only": True,
        "queue_mutation_preview_authorized": not errors,
        "route_adoption_authorized": False,
        "workspace_route_state_modified": False,
        "active_queue_modified": False,
        "write_performed": False,
        "queue_write_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "mutation_preview": mutation_preview,
        "blocked_capabilities": ROUTE_CHOICE_PROPOSAL_BLOCKED_CAPABILITIES,
        "errors": errors,
    }
    result_errors = validate_reviewed_route_adoption_preview(result)
    all_errors = sorted(set(result["errors"] + result_errors))
    result["passed"] = not all_errors
    result["errors"] = all_errors
    return result


def validate_reviewed_route_adoption_preview(result: dict[str, Any]) -> list[str]:
    errors = [
        f"missing required field: {field}"
        for field in schema_required("reviewed_route_adoption_preview")
        if field not in result
    ]
    if result.get("schema_version") != "agents-os.queue-manager.reviewed-route-adoption-preview.v0.1":
        errors.append("reviewed route adoption preview schema_version is invalid")
    if result.get("preview_only") is not True:
        errors.append("reviewed route adoption preview must be preview_only")
    if result.get("requires_nobao_review") is not True:
        errors.append("reviewed route adoption preview must require Nobao review")
    for flag in (
        "route_adoption_authorized",
        "workspace_route_state_modified",
        "active_queue_modified",
        "write_performed",
        "queue_write_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
    ):
        if result.get(flag) is not False:
            errors.append(f"reviewed route adoption preview flag must be false: {flag}")
    mutation_preview = result.get("mutation_preview", {})
    if result.get("queue_mutation_preview_authorized") is True:
        if mutation_preview.get("target_lane") != "NEXT":
            errors.append("route adoption preview must target NEXT")
        if mutation_preview.get("exactly_one_now_before") is not True:
            errors.append("route adoption preview requires exactly one NOW before preview")
        if mutation_preview.get("would_leave_now_unchanged") is not True:
            errors.append("route adoption preview must leave NOW unchanged")
        if mutation_preview.get("would_promote_now") is not False:
            errors.append("route adoption preview must not promote NOW")
        if not mutation_preview.get("would_append_next_title"):
            errors.append("route adoption preview must include NEXT append title")
    return errors


def format_next_block(item_id: str, title: str, body_lines: list[Any]) -> str:
    body = "\n".join(str(line).strip() for line in body_lines if str(line).strip()).strip()
    return f"### {item_id}: {title}\n\n{body}".strip()


def append_route_adoption_to_queue_text(queue_text: str, proposal: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    now_blocks = queue_lane_blocks(queue_text, "NOW")
    next_blocks = queue_lane_blocks(queue_text, "NEXT")
    if len(now_blocks) != 1:
        raise ValueError(f"expected exactly one NOW before route adoption, got {len(now_blocks)}")
    old_now = now_blocks[0]
    item = proposal.get("proposed_queue_item", {})
    title = str(item.get("title", "")).strip()
    body_lines = item.get("body_lines", [])
    if not isinstance(body_lines, list):
        body_lines = []
    next_indexes = []
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
        "control_chain_reviewed_route_adoption_apply_gate_v0.1: "
        f"appended \"{title}\" to NEXT as {new_next_id}; proposal={proposal.get('proposal_id')}"
    )
    updated = append_closed_entry(updated, closed_entry)
    after_now = queue_lane_blocks(updated, "NOW")
    after_next = queue_lane_blocks(updated, "NEXT")
    return updated, {
        "queue_path": None,
        "target_lane": "NEXT",
        "appended_next_id": new_next_id,
        "appended_next_title": title,
        "next_count_before": len(next_blocks),
        "next_count_after": len(after_next),
        "exactly_one_now_before": len(now_blocks) == 1,
        "exactly_one_now_after": len(after_now) == 1,
        "left_now_unchanged": after_now[0].get("title") == old_now.get("title") if after_now else False,
        "promoted_now": False,
        "closed_entry": closed_entry,
    }


def reviewed_route_adoption_apply_gate(
    proposal: dict[str, Any],
    review: dict[str, Any],
    queue_path: Path,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    errors = validate_route_choice_queue_proposal(proposal)
    if proposal.get("passed") is not True:
        errors.append("route choice queue proposal must be passed")
    errors.extend(validate_queue_review(review, proposal))
    if proposal.get("requires_jenn_decision") is True:
        errors.append("proposal requiring Jenn cannot adopt route")
    if is_protected_path(queue_path):
        errors.append(f"queue path is protected: {queue_path}")

    candidate = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    resolved, resolve_error = safe_resolve(candidate)
    mutation: dict[str, Any] = {}
    if resolve_error or resolved is None:
        errors.append(f"queue path could not be resolved: {resolve_error or queue_path}")
    elif not is_under_workspace(resolved, WORKSPACE_ROOT):
        errors.append(f"queue path is outside workspace: {queue_path}")
    elif not resolved.exists() or not resolved.is_file():
        errors.append(f"queue path is not a file: {rel(resolved)}")
    else:
        queue_text = resolved.read_text(encoding="utf-8")
        now_blocks = queue_lane_blocks(queue_text, "NOW")
        next_blocks = queue_lane_blocks(queue_text, "NEXT")
        item = proposal.get("proposed_queue_item", {})
        signals = queue_p3_signals(proposed_queue_item_text(item))
        if len(now_blocks) != 1:
            errors.append(f"expected exactly one NOW before route adoption, got {len(now_blocks)}")
        if signals:
            errors.append(f"proposed route queue item contains P3 signals: {','.join(signals)}")
        proposed_title = str(item.get("title", "")).strip()
        if any(block.get("title") == proposed_title for block in next_blocks):
            errors.append("proposed route queue item already exists in NEXT")
        if not errors:
            try:
                updated_text, mutation = append_route_adoption_to_queue_text(queue_text, proposal)
                mutation["queue_path"] = rel(resolved)
                if apply:
                    resolved.write_text(updated_text, encoding="utf-8")
            except ValueError as exc:
                errors.append(str(exc))

    can_apply = bool(apply and not errors)
    result = {
        "schema_version": "agents-os.queue-manager.reviewed-route-adoption-apply-gate.v0.1",
        "adoption_id": stable_id("ROUTEADOPTIONAPPLY", [proposal.get("proposal_id"), review.get("review_status"), apply]),
        "source_proposal_id": proposal.get("proposal_id"),
        "source_review_status": review.get("review_status"),
        "preview_only": not apply,
        "queue_adoption_authorized": not errors,
        "route_adoption_authorized": can_apply,
        "workspace_route_state_modified": can_apply,
        "active_queue_modified": can_apply,
        "write_performed": can_apply,
        "queue_write_authorized": can_apply,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "no_p3_route_adoption_guard": not errors,
        "mutation": mutation,
        "blocked_capabilities": ROUTE_CHOICE_PROPOSAL_BLOCKED_CAPABILITIES,
        "errors": errors,
    }
    result_errors = validate_reviewed_route_adoption_apply_gate(result)
    all_errors = sorted(set(result["errors"] + result_errors))
    result["passed"] = not all_errors
    result["errors"] = all_errors
    return result


def validate_reviewed_route_adoption_apply_gate(result: dict[str, Any]) -> list[str]:
    errors = [
        f"missing required field: {field}"
        for field in schema_required("reviewed_route_adoption_apply_gate")
        if field not in result
    ]
    if result.get("schema_version") != "agents-os.queue-manager.reviewed-route-adoption-apply-gate.v0.1":
        errors.append("reviewed route adoption apply gate schema_version is invalid")
    if result.get("requires_nobao_review") is not True:
        errors.append("reviewed route adoption apply gate must require Nobao review")
    for flag in ("queue_promotion_authorized", "execution_authorized"):
        if result.get(flag) is not False:
            errors.append(f"reviewed route adoption apply gate flag must be false: {flag}")
    if result.get("preview_only") is True:
        for flag in (
            "route_adoption_authorized",
            "workspace_route_state_modified",
            "active_queue_modified",
            "write_performed",
            "queue_write_authorized",
        ):
            if result.get(flag) is not False:
                errors.append(f"preview route adoption apply gate flag must be false: {flag}")
    if result.get("write_performed") is True:
        for flag in (
            "route_adoption_authorized",
            "workspace_route_state_modified",
            "active_queue_modified",
            "queue_write_authorized",
        ):
            if result.get(flag) is not True:
                errors.append(f"write_performed requires true flag: {flag}")
    mutation = result.get("mutation", {})
    if result.get("queue_adoption_authorized") is True:
        if mutation.get("target_lane") != "NEXT":
            errors.append("route adoption apply gate must target NEXT")
        if mutation.get("exactly_one_now_before") is not True:
            errors.append("route adoption apply gate requires exactly one NOW before adoption")
        if mutation.get("exactly_one_now_after") is not True:
            errors.append("route adoption apply gate must preserve exactly one NOW after adoption")
        if mutation.get("left_now_unchanged") is not True:
            errors.append("route adoption apply gate must leave NOW unchanged")
        if mutation.get("promoted_now") is not False:
            errors.append("route adoption apply gate must not promote NOW")
        if not mutation.get("appended_next_title"):
            errors.append("route adoption apply gate must include appended NEXT title")
        if result.get("no_p3_route_adoption_guard") is not True:
            errors.append("route adoption apply gate must keep no-P3 guard true when authorized")
    return errors


def queue_lane_blocks(queue_text: str, lane: str) -> list[dict[str, str]]:
    in_lane = False
    blocks: list[dict[str, str]] = []
    current: dict[str, Any] | None = None
    for line in queue_text.splitlines():
        if line.strip() == f"## {lane}":
            in_lane = True
            continue
        if in_lane and line.startswith("## "):
            if current:
                current["body"] = "\n".join(current["body_lines"]).strip()
                current.pop("body_lines", None)
                blocks.append(current)  # type: ignore[arg-type]
                current = None
            break
        if not in_lane:
            continue
        match = re.match(r"^###\s+([A-Z]+-\d{3}):\s+(.+?)\s*$", line)
        if match:
            if current:
                current["body"] = "\n".join(current["body_lines"]).strip()
                current.pop("body_lines", None)
                blocks.append(current)  # type: ignore[arg-type]
            current = {"id": match.group(1), "title": match.group(2), "body_lines": []}
            continue
        if current is not None:
            current["body_lines"].append(line)
    if in_lane and current:
        current["body"] = "\n".join(current["body_lines"]).strip()
        current.pop("body_lines", None)
        blocks.append(current)  # type: ignore[arg-type]
    return blocks


def queue_p3_signals(text: str) -> list[str]:
    scan_text = "\n".join(
        line for line in text.splitlines() if not NEGATED_SIGNAL_CONTEXT.search(line)
    )
    return sorted(signal for signal, pattern in QUEUE_P3_PATTERNS.items() if pattern.search(scan_text))


def validate_queue_review(review: dict[str, Any], proposal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if review.get("schema_version") != "agents-os.queue-manager.review.v0.1":
        errors.append("review schema_version is invalid")
    if review.get("review_status") != "accepted":
        errors.append("review_status must be accepted")
    if review.get("reviewer") != "Nobao":
        errors.append("reviewer must be Nobao")
    if review.get("source_proposal_id") != proposal.get("proposal_id"):
        errors.append("review source_proposal_id must match proposal_id")
    if review.get("requires_jenn_decision") is True:
        errors.append("review requiring Jenn cannot authorize queue mutation")
    return errors


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


def mutate_queue_text(queue_text: str, proposal: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    now_blocks = queue_lane_blocks(queue_text, "NOW")
    next_blocks = queue_lane_blocks(queue_text, "NEXT")
    if len(now_blocks) != 1:
        raise ValueError(f"expected exactly one NOW before mutation, got {len(now_blocks)}")
    if not next_blocks:
        raise ValueError("cannot promote NEXT because no NEXT item exists")
    promoted = next_blocks[0]
    old_now = now_blocks[0]
    promoted_body = f"### NOW-001: {promoted['title']}\n\n{promoted.get('body', '').strip()}".strip()
    remaining_next = []
    for block in next_blocks[1:]:
        remaining_next.append(f"### {block['id']}: {block['title']}\n\n{block.get('body', '').strip()}".strip())
    next_body = "\n\n".join(remaining_next) if remaining_next else "_No active NEXT items._"
    updated = replace_lane_section(queue_text, "NOW", promoted_body)
    updated = replace_lane_section(updated, "NEXT", next_body)
    closed_entry = (
        "queue_manager_reviewed_mutation_v0.1: "
        f"closed NOW \"{old_now['title']}\"; promoted \"{promoted['title']}\"; proposal={proposal.get('proposal_id')}"
    )
    updated = append_closed_entry(updated, closed_entry)
    after_now = queue_lane_blocks(updated, "NOW")
    return updated, {
        "closed_now_title": old_now["title"],
        "promoted_now_title": promoted["title"],
        "exactly_one_now_after": len(after_now) == 1,
        "closed_entry": closed_entry,
    }


def reviewed_queue_mutation(
    proposal: dict[str, Any],
    review: dict[str, Any],
    queue_path: Path,
    *,
    apply: bool = False,
) -> dict[str, Any]:
    errors = validate_queue_proposal(proposal)
    errors.extend(validate_queue_review(review, proposal))
    if proposal.get("close_current_now") is not True:
        errors.append("proposal does not close current NOW")
    if proposal.get("promote_next_title") in (None, ""):
        errors.append("proposal does not identify NEXT promotion target")
    if proposal.get("requires_jenn_decision") is True:
        errors.append("proposal requiring Jenn cannot mutate queue")
    if is_protected_path(queue_path):
        errors.append(f"queue path is protected: {queue_path}")

    candidate = queue_path if queue_path.is_absolute() else WORKSPACE_ROOT / queue_path
    resolved, resolve_error = safe_resolve(candidate)
    queue_text = ""
    mutation: dict[str, Any] = {}
    if resolve_error or resolved is None:
        errors.append(f"queue path could not be resolved: {resolve_error or queue_path}")
    elif not is_under_workspace(resolved, WORKSPACE_ROOT):
        errors.append(f"queue path is outside workspace: {queue_path}")
    elif not resolved.exists() or not resolved.is_file():
        errors.append(f"queue path is not a file: {rel(resolved)}")
    else:
        queue_text = resolved.read_text(encoding="utf-8")
        now_blocks = queue_lane_blocks(queue_text, "NOW")
        next_blocks = queue_lane_blocks(queue_text, "NEXT")
        if len(now_blocks) != 1:
            errors.append(f"expected exactly one NOW before mutation, got {len(now_blocks)}")
        if not next_blocks:
            errors.append("no NEXT item available to promote")
        else:
            target_text = f"{next_blocks[0].get('title', '')}\n{next_blocks[0].get('body', '')}"
            signals = queue_p3_signals(target_text)
            if signals:
                errors.append(f"NEXT promotion target contains P3 signals: {','.join(signals)}")
            if proposal.get("promote_next_title") != next_blocks[0].get("title"):
                errors.append("proposal promote_next_title does not match first NEXT item")
        if not errors:
            try:
                updated_text, mutation = mutate_queue_text(queue_text, proposal)
                mutation["exactly_one_now_before"] = len(now_blocks) == 1
                mutation["queue_path"] = rel(resolved)
                if apply:
                    resolved.write_text(updated_text, encoding="utf-8")
            except ValueError as exc:
                errors.append(str(exc))

    result = {
        "schema_version": "agents-os.queue-manager.reviewed-mutation.v0.1",
        "mutation_id": stable_id("QUEUEMUTATION", [proposal.get("proposal_id"), review.get("review_status"), apply]),
        "source_proposal_id": proposal.get("proposal_id"),
        "source_review_status": review.get("review_status"),
        "preview_only": not apply,
        "queue_mutation_authorized": not errors,
        "active_queue_modified": bool(apply and not errors),
        "write_performed": bool(apply and not errors),
        "auto_promote_authorized": False,
        "requires_nobao_review": True,
        "requires_jenn_decision": False,
        "no_p3_auto_promote_guard": not errors,
        "mutation": mutation,
        "errors": errors,
    }
    result_errors = validate_reviewed_queue_mutation(result)
    result["passed"] = not result_errors
    result["errors"] = sorted(set(result["errors"] + result_errors))
    return result


def validate_reviewed_queue_mutation(result: dict[str, Any]) -> list[str]:
    errors = [
        f"missing required field: {field}"
        for field in schema_required("reviewed_queue_mutation")
        if field not in result
    ]
    if result.get("auto_promote_authorized") is not False:
        errors.append("reviewed mutation gate must not authorize auto-promote")
    if result.get("requires_nobao_review") is not True:
        errors.append("reviewed mutation gate must require Nobao review")
    if result.get("preview_only") is True and result.get("active_queue_modified") is not False:
        errors.append("preview mutation must not modify active queue")
    if result.get("write_performed") is True and result.get("active_queue_modified") is not True:
        errors.append("write_performed requires active_queue_modified")
    mutation = result.get("mutation", {})
    if result.get("queue_mutation_authorized") is True and mutation.get("exactly_one_now_after") is not True:
        errors.append("authorized mutation must preserve exactly one NOW")
    return errors


def validate_control_chain(run_colameta: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    local_candidate = {
        "schema_version": "agents-os.task-producer.candidate-task.v0.1",
        "candidate_id": "CANDIDATE-LOCAL",
        "producer_generated": True,
        "title": "Write governance report",
        "summary": "Write local governance report and run docctl validation.",
        "risk_signals": [],
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
            "requires_jenn_decision": False,
            "execution_authorized": False,
        },
    }
    colameta_candidate = dict(local_candidate, candidate_id="CANDIDATE-COLAMETA", title="ColaMeta Executor Readiness Reconciliation", summary="Run ColaMeta executor readiness reconciliation.")
    provider_candidate = dict(local_candidate, candidate_id="CANDIDATE-PROVIDER", title="Call provider", summary="Call provider and start service.", risk_signals=["provider_call", "service_start"])
    provider_candidate["review_gate"] = dict(provider_candidate["review_gate"], requires_jenn_decision=True)

    local_decision = build_commander_decision(local_candidate)
    colameta_decision = build_commander_decision(colameta_candidate)
    provider_decision = build_commander_decision(provider_candidate)
    route_option_candidate: dict[str, Any] | None = None
    route_option_decision: dict[str, Any] | None = None
    route_option_preview: dict[str, Any] | None = None
    route_choice_preview_payload: dict[str, Any] | None = None
    route_choice_proposal: dict[str, Any] | None = None
    route_adoption_preview: dict[str, Any] | None = None
    route_handoff_reconciliation = route_choice_handoff_reconciliation(DEFAULT_QUEUE)
    route_template_readiness = route_choice_template_readiness(ROUTE_SELECTION_PACKAGE)
    route_e2e_readiness = route_choice_end_to_end_readiness(ROUTE_SELECTION_PACKAGE)
    route_adoption_bundle_preview = route_choice_adoption_bundle_preview(
        "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
        "这是 validation fixture；不写真实队列、不推广 NOW、不执行。",
        DEFAULT_QUEUE,
        ROUTE_SELECTION_PACKAGE,
        fixture_only=True,
    )
    if route_handoff_reconciliation.get("passed") is not True:
        errors.append("route choice handoff reconciliation did not pass")
    if route_handoff_reconciliation.get("aligned") is not True:
        errors.append("route choice handoff reconciliation is not aligned")
    if route_handoff_reconciliation.get("route_choice_required") is True:
        if route_handoff_reconciliation.get("decision_owner") != "Jenn":
            errors.append("route choice handoff reconciliation did not preserve Jenn decision owner")
        if route_handoff_reconciliation.get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
            errors.append("route choice handoff reconciliation did not preserve route choices A-E")
    else:
        if route_handoff_reconciliation.get("decision_owner") is not None:
            errors.append("inactive route choice handoff should not preserve a decision owner")
        if route_handoff_reconciliation.get("accepted_route_ids") not in ([], None):
            errors.append("inactive route choice handoff should not preserve accepted route ids")
    for flag in (
        "route_auto_selection_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "write_performed",
    ):
        if route_handoff_reconciliation.get(flag) is not False:
            errors.append(f"route choice handoff reconciliation authorized {flag}")
    if route_template_readiness.get("passed") is not True:
        errors.append("route choice template readiness did not pass")
    if route_template_readiness.get("task_producer_coverage_passed") is not True:
        errors.append("Task Producer route choice template coverage did not pass")
    if route_template_readiness.get("accepted_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice template readiness accepted route ids are not A-E")
    if route_template_readiness.get("parsed_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice template readiness did not prove A-E parsing")
    if route_template_readiness.get("placeholder_goal_blocked") is not True:
        errors.append("route choice template readiness did not reject Template E placeholder")
    if route_template_readiness.get("concrete_new_route_fixture_passed") is not True:
        errors.append("route choice template readiness did not prove concrete option E fixture")
    for flag in ROUTE_CHOICE_TEMPLATE_COVERAGE_FALSE_FLAGS:
        if route_template_readiness.get(flag) is not False:
            errors.append(f"route choice template readiness authorized {flag}")
    if route_e2e_readiness.get("passed") is not True:
        errors.append("route choice end-to-end readiness did not pass")
    if route_e2e_readiness.get("passed_route_ids") != ["A", "B", "C", "D", "E"]:
        errors.append("route choice end-to-end readiness did not pass A-E")
    if route_e2e_readiness.get("temporary_fixture_cleaned") is not True:
        errors.append("route choice end-to-end readiness did not clean temporary fixture")
    if route_e2e_readiness.get("fixture_queue_unchanged") is not True:
        errors.append("route choice end-to-end readiness changed fixture queue")
    for flag in ROUTE_CHOICE_E2E_FALSE_FLAGS:
        if route_e2e_readiness.get(flag) is not False:
            errors.append(f"route choice end-to-end readiness authorized {flag}")
    if route_adoption_bundle_preview.get("passed") is not True:
        errors.append("route choice adoption bundle preview did not pass")
    if route_adoption_bundle_preview.get("selected_route_id") != "B":
        errors.append("route choice adoption bundle preview fixture did not select route B")
    if route_adoption_bundle_preview.get("can_apply_with_separate_apply_gate") is not True:
        errors.append("route choice adoption bundle preview did not reach separate apply gate readiness")
    for flag in (
        "real_queue_write_performed",
        "workspace_route_state_modified",
        "active_queue_modified",
        "write_performed",
        "queue_write_authorized",
        "queue_promotion_authorized",
        "route_adoption_authorized",
        "execution_authorized",
        "raw_confirmation_text_output",
        "raw_template_output",
    ):
        if route_adoption_bundle_preview.get(flag) is not False:
            errors.append(f"route choice adoption bundle preview authorized {flag}")
    try:
        producer = import_module(TASK_PRODUCER, "agents_os_task_producer_for_control_chain")
        route_option_candidate = producer.candidate_from_route_option("A")
        route_choice_preview_payload = producer.route_choice_preview(
            "确认选择 AGENTS OS 下一路线：Formal Memory Loop。\n"
            "先准备 formal Memory candidate gate v0.1；只做候选和确认模型，不写正式 Memory。"
        )
    except Exception as exc:  # pragma: no cover - surfaced as validation error
        errors.append(f"Task Producer import failed: {exc}")
    if route_option_candidate is not None:
        if route_option_candidate.get("schema_version") != "agents-os.task-producer.candidate-task.v0.1":
            errors.append("route option candidate preflight failed")
        else:
            route_option_decision = build_commander_decision(route_option_candidate)
            route_option_preview = build_track_preview(route_option_decision)
            if route_option_decision.get("decision") != "stop_needs_jenn_decision":
                errors.append("route option candidate did not stop for Jenn")
            if route_option_decision.get("execution_authorization_scope") != "blocked_requires_jenn":
                errors.append("route option candidate did not use blocked_requires_jenn")
            if route_option_decision.get("requires_jenn_decision") is not True:
                errors.append("route option candidate did not require Jenn decision")
            if route_option_decision.get("execution_authorized") is not False:
                errors.append("route option candidate authorized execution")
            if "route_selection_required" not in route_option_decision.get("blocked_capabilities", []):
                errors.append("route option candidate did not block route_selection_required")
            if route_option_preview.get("track_authorized") is not False:
                errors.append("route option preview elevated authorization")
    if route_choice_preview_payload is not None:
        route_choice_proposal = route_choice_queue_proposal(route_choice_preview_payload)
        if route_choice_proposal.get("passed") is not True:
            errors.append("route choice queue proposal did not pass")
        if route_choice_proposal.get("proposal_only") is not True:
            errors.append("route choice queue proposal is not proposal-only")
        if route_choice_proposal.get("active_queue_modified") is not False:
            errors.append("route choice queue proposal modified active queue")
        if route_choice_proposal.get("queue_write_authorized") is not False:
            errors.append("route choice queue proposal authorized queue write")
        if route_choice_proposal.get("queue_promotion_authorized") is not False:
            errors.append("route choice queue proposal authorized queue promotion")
        if route_choice_proposal.get("execution_authorized") is not False:
            errors.append("route choice queue proposal authorized execution")
        route_review = {
            "schema_version": "agents-os.queue-manager.review.v0.1",
            "source_proposal_id": route_choice_proposal.get("proposal_id"),
            "review_status": "accepted",
            "reviewer": "Nobao",
            "requires_jenn_decision": False,
        }
        route_adoption_preview = reviewed_route_adoption_preview(route_choice_proposal, route_review, DEFAULT_QUEUE)
        if route_adoption_preview.get("passed") is not True:
            errors.append("reviewed route adoption preview did not pass")
        if route_adoption_preview.get("preview_only") is not True:
            errors.append("reviewed route adoption preview is not preview-only")
        if route_adoption_preview.get("active_queue_modified") is not False:
            errors.append("reviewed route adoption preview modified active queue")
        if route_adoption_preview.get("queue_write_authorized") is not False:
            errors.append("reviewed route adoption preview authorized queue write")
        if route_adoption_preview.get("execution_authorized") is not False:
            errors.append("reviewed route adoption preview authorized execution")
    if local_decision.get("decision") != "route_to_local_executor" or local_decision.get("execution_authorization_scope") != "local_safe_only":
        errors.append("local candidate did not route to local executor")
    if colameta_decision.get("decision") != "route_to_colameta" or colameta_decision.get("execution_authorization_scope") != "none":
        errors.append("ColaMeta candidate did not route to ColaMeta preview")
    if provider_decision.get("decision") != "stop_needs_jenn_decision" or provider_decision.get("execution_authorization_scope") != "blocked_requires_jenn":
        errors.append("provider candidate did not stop for Jenn")

    local_preview = build_track_preview(local_decision, "run_validation_command")
    blocked_preview = build_track_preview(provider_decision)
    if local_preview.get("selected_track") != "local_executor" or local_preview.get("track_authorized") is not True:
        errors.append("local track preview did not authorize local executor")
    if blocked_preview.get("track_authorized") is not False:
        errors.append("blocked track preview elevated authorization")

    local_result = local_executor_run(local_preview, "run_validation_command", command="python3 --version")
    if not local_result.get("passed") or local_result.get("validation_passed") is not True:
        errors.append("local validation command did not pass")
    forbidden_result = local_executor_run(local_preview, "provider_call")
    if forbidden_result.get("validation_passed") is not False:
        errors.append("forbidden local executor action was not blocked")
    failing_result = local_executor_run(
        local_preview,
        "run_validation_command",
        command="python3 execution/agents-os-control-chain/does-not-exist.py",
    )
    failure_report = build_failure_report(failing_result)
    stop_loop = build_stop_loop_result(failure_report)
    failure_queue_proposal = queue_update_proposal(failing_result)
    if failure_report.get("category") != "validation_failed":
        errors.append("validation failure was not classified as validation_failed")
    if failure_report.get("silent_retry_authorized") is not False:
        errors.append("failure report authorized silent retry")
    if stop_loop.get("status") != "stopped_for_review":
        errors.append("stop loop did not stop for review")
    if stop_loop.get("queue_promoted") is not False:
        errors.append("stop loop promoted queue on failure")
    if failure_queue_proposal.get("close_current_now") is not False:
        errors.append("queue proposal closed NOW on failed validation")
    proposal = queue_update_proposal(local_result)
    if proposal.get("active_queue_modified") is not False or proposal.get("proposal_only") is not True:
        errors.append("queue proposal mutated queue")
    reviewed_preview: dict[str, Any] | None = None
    reviewed_apply: dict[str, Any] | None = None
    route_adoption_apply_preview: dict[str, Any] | None = None
    route_adoption_apply: dict[str, Any] | None = None
    with tempfile.TemporaryDirectory(prefix="agents-os-queue-gate-", dir=WORKSPACE_ROOT) as temp_dir:
        queue_fixture = Path(temp_dir) / "queue.md"
        queue_fixture.write_text(
            """# fixture queue

## NOW

### NOW-001: Completed task

Done.

## NEXT

### NEXT-001: Safe next task

Write local governance report.

### NEXT-002: Later task

Wait.

## LATER

## BLOCKED

```text
provider_calls: blocked
```

## CLOSED

```text
old_task: closed
```
""",
            encoding="utf-8",
        )
        fixture_proposal = queue_update_proposal(local_result, queue_fixture)
        review = {
            "schema_version": "agents-os.queue-manager.review.v0.1",
            "source_proposal_id": fixture_proposal.get("proposal_id"),
            "review_status": "accepted",
            "reviewer": "Nobao",
            "requires_jenn_decision": False,
        }
        reviewed_preview = reviewed_queue_mutation(fixture_proposal, review, queue_fixture)
        reviewed_apply = reviewed_queue_mutation(fixture_proposal, review, queue_fixture, apply=True)
        mutated_text = queue_fixture.read_text(encoding="utf-8")
        if reviewed_preview.get("active_queue_modified") is not False or reviewed_preview.get("preview_only") is not True:
            errors.append("reviewed queue mutation preview modified queue")
        if reviewed_apply.get("active_queue_modified") is not True or reviewed_apply.get("write_performed") is not True:
            errors.append("reviewed queue mutation apply did not mutate fixture queue")
        if "### NOW-001: Safe next task" not in mutated_text:
            errors.append("reviewed queue mutation did not promote safe NEXT in fixture")
        rejected_review = dict(review, review_status="pending")
        rejected = reviewed_queue_mutation(fixture_proposal, rejected_review, queue_fixture)
        if rejected.get("queue_mutation_authorized") is not False:
            errors.append("pending review authorized queue mutation")
        p3_queue = Path(temp_dir) / "p3-queue.md"
        p3_queue.write_text(
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
        p3_proposal = queue_update_proposal(local_result, p3_queue)
        p3_review = dict(review, source_proposal_id=p3_proposal.get("proposal_id"))
        p3_mutation = reviewed_queue_mutation(p3_proposal, p3_review, p3_queue)
        if p3_mutation.get("queue_mutation_authorized") is not False:
            errors.append("P3 NEXT target authorized queue mutation")
        route_apply_queue = Path(temp_dir) / "route-adoption-queue.md"
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
        route_apply_queue.write_text(route_apply_queue_text, encoding="utf-8")
        route_apply_review = {
            "schema_version": "agents-os.queue-manager.review.v0.1",
            "source_proposal_id": route_choice_proposal.get("proposal_id") if route_choice_proposal else None,
            "review_status": "accepted",
            "reviewer": "Nobao",
            "requires_jenn_decision": False,
        }
        if route_choice_proposal:
            route_adoption_apply_preview = reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_apply_review,
                route_apply_queue,
            )
            route_adoption_apply = reviewed_route_adoption_apply_gate(
                route_choice_proposal,
                route_apply_review,
                route_apply_queue,
                apply=True,
            )
            route_apply_text = route_apply_queue.read_text(encoding="utf-8")
            if route_adoption_apply_preview.get("active_queue_modified") is not False:
                errors.append("route adoption apply preview modified queue")
            if route_adoption_apply_preview.get("queue_write_authorized") is not False:
                errors.append("route adoption apply preview authorized queue write")
            if route_adoption_apply.get("active_queue_modified") is not True:
                errors.append("route adoption apply gate did not mutate fixture queue")
            if route_adoption_apply.get("queue_promotion_authorized") is not False:
                errors.append("route adoption apply gate authorized queue promotion")
            if route_adoption_apply.get("execution_authorized") is not False:
                errors.append("route adoption apply gate authorized execution")
            if "### NOW-001: No Active Automatic Construction Item" not in route_apply_text:
                errors.append("route adoption apply gate changed NOW in fixture")
            if "### NEXT-001: AGENTS OS formal Memory candidate gate v0.1" not in route_apply_text:
                errors.append("route adoption apply gate did not append route to NEXT in fixture")
            duplicate_apply = reviewed_route_adoption_apply_gate(route_choice_proposal, route_apply_review, route_apply_queue)
            if duplicate_apply.get("passed") is not False:
                errors.append("duplicate route adoption passed")
            if duplicate_apply.get("queue_adoption_authorized") is not False:
                errors.append("duplicate route adoption authorized")
            p3_route_proposal = json.loads(json.dumps(route_choice_proposal))
            p3_route_proposal["proposal_id"] = stable_id("ROUTEQUEUEPROPOSALP3", ["provider", "service"])
            p3_route_proposal["proposed_queue_item"] = {
                "lane": "NEXT",
                "title": "Call provider",
                "body_lines": ["Call provider and start service."],
            }
            p3_route_review = dict(route_apply_review, source_proposal_id=p3_route_proposal["proposal_id"])
            p3_route_apply = reviewed_route_adoption_apply_gate(p3_route_proposal, p3_route_review, route_apply_queue)
            if p3_route_apply.get("passed") is not False:
                errors.append("P3 route adoption passed")
            if p3_route_apply.get("queue_adoption_authorized") is not False:
                errors.append("P3 route adoption authorized")

    colameta_result: dict[str, Any] | None = None
    if run_colameta:
        colameta_preview = build_track_preview(colameta_decision)
        colameta_result = colameta_readiness(colameta_preview)
        if not colameta_result.get("passed"):
            errors.append("ColaMeta readiness did not pass")

    return {
        "schema_version": "agents-os.control-chain.validation.v0.1",
        "passed": not errors,
        "errors": errors,
        "commander": {
            "local_decision": local_decision.get("decision"),
            "colameta_decision": colameta_decision.get("decision"),
            "provider_decision": provider_decision.get("decision"),
            "route_option_decision": route_option_decision.get("decision") if route_option_decision else None,
        },
        "track_selector": {
            "local_track_authorized": local_preview.get("track_authorized"),
            "blocked_track_authorized": blocked_preview.get("track_authorized"),
            "route_option_track_authorized": route_option_preview.get("track_authorized") if route_option_preview else None,
        },
        "route_option_candidate": {
            "checked": route_option_candidate is not None,
            "present": route_option_candidate.get("schema_version") == "agents-os.task-producer.candidate-task.v0.1"
            if route_option_candidate
            else False,
            "decision": route_option_decision.get("decision") if route_option_decision else None,
            "requires_jenn_decision": route_option_decision.get("requires_jenn_decision") if route_option_decision else None,
            "execution_authorization_scope": route_option_decision.get("execution_authorization_scope")
            if route_option_decision
            else None,
            "execution_authorized": route_option_decision.get("execution_authorized") if route_option_decision else None,
            "track_authorized": route_option_preview.get("track_authorized") if route_option_preview else None,
        },
        "route_choice_handoff": {
            "passed": route_handoff_reconciliation.get("passed"),
            "aligned": route_handoff_reconciliation.get("aligned"),
            "route_choice_required": route_handoff_reconciliation.get("route_choice_required"),
            "decision_owner": route_handoff_reconciliation.get("decision_owner"),
            "accepted_route_ids": route_handoff_reconciliation.get("accepted_route_ids"),
            "active_queue_mutation_authorized": route_handoff_reconciliation.get("active_queue_mutation_authorized"),
            "queue_promotion_authorized": route_handoff_reconciliation.get("queue_promotion_authorized"),
            "execution_authorized": route_handoff_reconciliation.get("execution_authorized"),
        },
        "route_choice_template_readiness": {
            "passed": route_template_readiness.get("passed"),
            "task_producer_coverage_passed": route_template_readiness.get("task_producer_coverage_passed"),
            "accepted_route_ids": route_template_readiness.get("accepted_route_ids"),
            "parsed_route_ids": route_template_readiness.get("parsed_route_ids"),
            "template_count": route_template_readiness.get("template_count"),
            "templates_checked": route_template_readiness.get("templates_checked"),
            "placeholder_goal_blocked": route_template_readiness.get("placeholder_goal_blocked"),
            "concrete_new_route_fixture_passed": route_template_readiness.get("concrete_new_route_fixture_passed"),
            "active_queue_modified": route_template_readiness.get("active_queue_modified"),
            "queue_promotion_authorized": route_template_readiness.get("queue_promotion_authorized"),
            "execution_authorized": route_template_readiness.get("execution_authorized"),
            "raw_template_output": route_template_readiness.get("raw_template_output"),
        },
        "route_choice_end_to_end_readiness": {
            "passed": route_e2e_readiness.get("passed"),
            "checked_route_ids": route_e2e_readiness.get("checked_route_ids"),
            "passed_route_ids": route_e2e_readiness.get("passed_route_ids"),
            "route_count": route_e2e_readiness.get("route_count"),
            "stage_counts": route_e2e_readiness.get("stage_counts"),
            "temporary_fixture_cleaned": route_e2e_readiness.get("temporary_fixture_cleaned"),
            "fixture_queue_unchanged": route_e2e_readiness.get("fixture_queue_unchanged"),
            "active_queue_modified": route_e2e_readiness.get("active_queue_modified"),
            "real_queue_write_performed": route_e2e_readiness.get("real_queue_write_performed"),
            "route_selected": route_e2e_readiness.get("route_selected"),
            "route_adoption_authorized": route_e2e_readiness.get("route_adoption_authorized"),
            "execution_authorized": route_e2e_readiness.get("execution_authorized"),
            "raw_confirmation_text_output": route_e2e_readiness.get("raw_confirmation_text_output"),
            "raw_template_output": route_e2e_readiness.get("raw_template_output"),
        },
        "route_choice_adoption_bundle_preview": {
            "passed": route_adoption_bundle_preview.get("passed"),
            "fixture_only": route_adoption_bundle_preview.get("fixture_only"),
            "selected_route_id": route_adoption_bundle_preview.get("selected_route_id"),
            "proposed_next_title": route_adoption_bundle_preview.get("proposed_next_title"),
            "queue_proposal_passed": route_adoption_bundle_preview.get("queue_proposal_passed"),
            "review_object_generated": route_adoption_bundle_preview.get("review_object_generated"),
            "reviewed_route_adoption_preview_passed": route_adoption_bundle_preview.get("reviewed_route_adoption_preview_passed"),
            "reviewed_route_adoption_apply_preview_passed": route_adoption_bundle_preview.get("reviewed_route_adoption_apply_preview_passed"),
            "can_apply_with_separate_apply_gate": route_adoption_bundle_preview.get("can_apply_with_separate_apply_gate"),
            "real_queue_write_performed": route_adoption_bundle_preview.get("real_queue_write_performed"),
            "active_queue_modified": route_adoption_bundle_preview.get("active_queue_modified"),
            "route_adoption_authorized": route_adoption_bundle_preview.get("route_adoption_authorized"),
            "execution_authorized": route_adoption_bundle_preview.get("execution_authorized"),
            "raw_confirmation_text_output": route_adoption_bundle_preview.get("raw_confirmation_text_output"),
            "raw_template_output": route_adoption_bundle_preview.get("raw_template_output"),
        },
        "local_executor": {
            "validation_passed": local_result.get("validation_passed"),
            "forbidden_blocked": forbidden_result.get("validation_passed") is False,
        },
        "queue_manager": {
            "proposal_only": proposal.get("proposal_only"),
            "active_queue_modified": proposal.get("active_queue_modified"),
            "reviewed_preview_passed": reviewed_preview.get("passed") if reviewed_preview else None,
            "reviewed_apply_fixture_modified": reviewed_apply.get("active_queue_modified") if reviewed_apply else None,
            "route_choice_proposal_passed": route_choice_proposal.get("passed") if route_choice_proposal else None,
            "route_choice_proposal_only": route_choice_proposal.get("proposal_only") if route_choice_proposal else None,
            "route_choice_proposal_active_queue_modified": route_choice_proposal.get("active_queue_modified")
            if route_choice_proposal
            else None,
            "route_choice_proposal_execution_authorized": route_choice_proposal.get("execution_authorized")
            if route_choice_proposal
            else None,
            "reviewed_route_adoption_preview_passed": route_adoption_preview.get("passed")
            if route_adoption_preview
            else None,
            "reviewed_route_adoption_preview_active_queue_modified": route_adoption_preview.get("active_queue_modified")
            if route_adoption_preview
            else None,
            "reviewed_route_adoption_preview_execution_authorized": route_adoption_preview.get("execution_authorized")
            if route_adoption_preview
            else None,
            "reviewed_route_adoption_apply_preview_passed": route_adoption_apply_preview.get("passed")
            if route_adoption_apply_preview
            else None,
            "reviewed_route_adoption_apply_fixture_modified": route_adoption_apply.get("active_queue_modified")
            if route_adoption_apply
            else None,
            "reviewed_route_adoption_apply_execution_authorized": route_adoption_apply.get("execution_authorized")
            if route_adoption_apply
            else None,
        },
        "failure_handling": {
            "category": failure_report.get("category"),
            "repair_attempt_allowed": failure_report.get("repair_attempt_allowed"),
            "silent_retry_authorized": failure_report.get("silent_retry_authorized"),
            "stop_status": stop_loop.get("status"),
            "queue_promoted": stop_loop.get("queue_promoted"),
            "failed_queue_close_now": failure_queue_proposal.get("close_current_now"),
        },
        "colameta": {
            "checked": run_colameta,
            "passed": colameta_result.get("passed") if colameta_result else None,
        },
    }


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENTS OS commander-first control chain.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    decide_parser = subparsers.add_parser("decide")
    decide_parser.add_argument("--candidate-json", required=True)
    decide_parser.add_argument("--machine-preview-json")
    decide_parser.add_argument("--json", action="store_true")

    select_parser = subparsers.add_parser("select")
    select_parser.add_argument("--decision-json", required=True)
    select_parser.add_argument("--action-type")
    select_parser.add_argument("--json", action="store_true")

    cola_parser = subparsers.add_parser("colameta-readiness")
    cola_parser.add_argument("--track-preview-json", required=True)
    cola_parser.add_argument("--json", action="store_true")

    local_parser = subparsers.add_parser("local-exec")
    local_parser.add_argument("--track-preview-json", required=True)
    local_parser.add_argument("--action-type", required=True)
    local_parser.add_argument("--command", dest="validation_command")
    local_parser.add_argument("--target-path")
    local_parser.add_argument("--content")
    local_parser.add_argument("--json", action="store_true")

    queue_parser = subparsers.add_parser("queue-proposal")
    queue_parser.add_argument("--track-result-json", required=True)
    queue_parser.add_argument("--json", action="store_true")

    route_choice_queue_parser = subparsers.add_parser("route-choice-queue-proposal")
    route_choice_queue_parser.add_argument("--route-choice-preview-json", required=True)
    route_choice_queue_parser.add_argument("--json", action="store_true")

    route_adoption_bundle_parser = subparsers.add_parser("route-choice-adoption-bundle-preview")
    route_adoption_bundle_parser.add_argument("--confirmation-text", required=True)
    route_adoption_bundle_parser.add_argument("--source", default=str(ROUTE_SELECTION_PACKAGE))
    route_adoption_bundle_parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    route_adoption_bundle_parser.add_argument("--json", action="store_true")

    route_adoption_parser = subparsers.add_parser("reviewed-route-adoption-preview")
    route_adoption_parser.add_argument("--proposal-json", required=True)
    route_adoption_parser.add_argument("--review-json", required=True)
    route_adoption_parser.add_argument("--queue", required=True)
    route_adoption_parser.add_argument("--json", action="store_true")

    route_adoption_apply_parser = subparsers.add_parser("reviewed-route-adoption-apply-gate")
    route_adoption_apply_parser.add_argument("--proposal-json", required=True)
    route_adoption_apply_parser.add_argument("--review-json", required=True)
    route_adoption_apply_parser.add_argument("--queue", required=True)
    route_adoption_apply_parser.add_argument("--apply", action="store_true")
    route_adoption_apply_parser.add_argument("--json", action="store_true")

    handoff_parser = subparsers.add_parser("route-choice-handoff-reconciliation")
    handoff_parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    handoff_parser.add_argument("--json", action="store_true")

    template_readiness_parser = subparsers.add_parser("route-choice-template-readiness")
    template_readiness_parser.add_argument("--source", default=str(ROUTE_SELECTION_PACKAGE))
    template_readiness_parser.add_argument("--json", action="store_true")

    e2e_readiness_parser = subparsers.add_parser("route-choice-end-to-end-readiness")
    e2e_readiness_parser.add_argument("--source", default=str(ROUTE_SELECTION_PACKAGE))
    e2e_readiness_parser.add_argument("--json", action="store_true")

    reviewed_queue_parser = subparsers.add_parser("queue-reviewed-mutation")
    reviewed_queue_parser.add_argument("--proposal-json", required=True)
    reviewed_queue_parser.add_argument("--review-json", required=True)
    reviewed_queue_parser.add_argument("--queue", required=True)
    reviewed_queue_parser.add_argument("--apply", action="store_true")
    reviewed_queue_parser.add_argument("--json", action="store_true")

    failure_parser = subparsers.add_parser("failure-report")
    failure_parser.add_argument("--source-json", required=True)
    failure_parser.add_argument("--json", action="store_true")

    stop_loop_parser = subparsers.add_parser("stop-loop")
    stop_loop_parser.add_argument("--failure-report-json", required=True)
    stop_loop_parser.add_argument("--json", action="store_true")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "decide":
        candidate = load_json(Path(args.candidate_json))
        machine_preview = load_json(Path(args.machine_preview_json)) if args.machine_preview_json else None
        result = build_commander_decision(candidate, machine_preview)
        if args.json:
            print_json(result)
        else:
            print(f"Commander decision: {result['decision']} track={result['recommended_track']} scope={result['execution_authorization_scope']}")
        return 0 if result["passed"] else 1

    if args.command == "select":
        result = build_track_preview(load_json(Path(args.decision_json)), args.action_type)
        if args.json:
            print_json(result)
        else:
            print(f"Track preview: {result['selected_track']} authorized={result['track_authorized']}")
        return 0 if result["passed"] else 1

    if args.command == "colameta-readiness":
        result = colameta_readiness(load_json(Path(args.track_preview_json)))
        if args.json:
            print_json(result)
        else:
            print(f"ColaMeta readiness: {'PASS' if result['passed'] else 'FAIL'}")
        return 0 if result["passed"] else 1

    if args.command == "local-exec":
        result = local_executor_run(
            load_json(Path(args.track_preview_json)),
            args.action_type,
            target_path=Path(args.target_path) if args.target_path else None,
            content=args.content,
            command=args.validation_command,
        )
        if args.json:
            print_json(result)
        else:
            print(f"Local executor result: {'PASS' if result['passed'] else 'FAIL'}")
        return 0 if result["passed"] else 1

    if args.command == "queue-proposal":
        result = queue_update_proposal(load_json(Path(args.track_result_json)))
        if args.json:
            print_json(result)
        else:
            print(f"Queue proposal: proposal_only={result['proposal_only']} close_now={result['close_current_now']}")
        return 0 if result["passed"] else 1

    if args.command == "route-choice-queue-proposal":
        result = route_choice_queue_proposal(load_json(Path(args.route_choice_preview_json)))
        if args.json:
            print_json(result)
        else:
            item = result.get("proposed_queue_item", {})
            print(
                "Route choice queue proposal: "
                f"proposal_only={result['proposal_only']} "
                f"lane={item.get('lane')} "
                f"title={item.get('title')}"
            )
        return 0 if result["passed"] else 1

    if args.command == "route-choice-adoption-bundle-preview":
        result = route_choice_adoption_bundle_preview(
            args.confirmation_text,
            Path(args.queue),
            Path(args.source),
        )
        if args.json:
            print_json(result)
        else:
            print("Route choice adoption bundle preview")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Selected route: {result.get('selected_route_id')}")
            print(f"Proposed NEXT: {result.get('proposed_next_title')}")
            print(f"Separate apply gate ready: {result.get('can_apply_with_separate_apply_gate')}")
            print(f"Active queue modified: {result.get('active_queue_modified')}")
            print(f"Execution authorized: {result.get('execution_authorized')}")
        return 0 if result["passed"] else 1

    if args.command == "reviewed-route-adoption-preview":
        result = reviewed_route_adoption_preview(
            load_json(Path(args.proposal_json)),
            load_json(Path(args.review_json)),
            Path(args.queue),
        )
        if args.json:
            print_json(result)
        else:
            preview = result.get("mutation_preview", {})
            print(
                "Reviewed route adoption preview: "
                f"authorized={result['queue_mutation_preview_authorized']} "
                f"modified={result['active_queue_modified']} "
                f"would_append={preview.get('would_append_next_title')}"
            )
        return 0 if result["passed"] else 1

    if args.command == "reviewed-route-adoption-apply-gate":
        result = reviewed_route_adoption_apply_gate(
            load_json(Path(args.proposal_json)),
            load_json(Path(args.review_json)),
            Path(args.queue),
            apply=args.apply,
        )
        if args.json:
            print_json(result)
        else:
            mutation = result.get("mutation", {})
            print(
                "Reviewed route adoption apply gate: "
                f"authorized={result['queue_adoption_authorized']} "
                f"modified={result['active_queue_modified']} "
                f"appended={mutation.get('appended_next_title')}"
            )
        return 0 if result["passed"] else 1

    if args.command == "route-choice-handoff-reconciliation":
        result = route_choice_handoff_reconciliation(Path(args.queue))
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS route choice handoff reconciliation")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Aligned: {result['aligned']}")
            print(f"Route choice required: {result['route_choice_required']}")
            print(f"Decision owner: {result['decision_owner']}")
        return 0 if result["passed"] else 1

    if args.command == "route-choice-template-readiness":
        result = route_choice_template_readiness(Path(args.source))
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS route choice template readiness")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Template count: {result['template_count']}")
            print(f"Parsed route ids: {','.join(result.get('parsed_route_ids', []))}")
            print(f"Template E placeholder blocked: {result['placeholder_goal_blocked']}")
            print(f"Execution authorized: {result['execution_authorized']}")
        return 0 if result["passed"] else 1

    if args.command == "route-choice-end-to-end-readiness":
        result = route_choice_end_to_end_readiness(Path(args.source))
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS route choice end-to-end readiness")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Checked route ids: {','.join(result.get('checked_route_ids', []))}")
            print(f"Passed route ids: {','.join(result.get('passed_route_ids', []))}")
            print(f"Temporary fixture cleaned: {result['temporary_fixture_cleaned']}")
            print(f"Active queue modified: {result['active_queue_modified']}")
            print(f"Execution authorized: {result['execution_authorized']}")
        return 0 if result["passed"] else 1

    if args.command == "queue-reviewed-mutation":
        result = reviewed_queue_mutation(
            load_json(Path(args.proposal_json)),
            load_json(Path(args.review_json)),
            Path(args.queue),
            apply=args.apply,
        )
        if args.json:
            print_json(result)
        else:
            print(
                "Reviewed queue mutation: "
                f"authorized={result['queue_mutation_authorized']} "
                f"modified={result['active_queue_modified']}"
            )
        return 0 if result["passed"] else 1

    if args.command == "failure-report":
        result = build_failure_report(load_json(Path(args.source_json)))
        if args.json:
            print_json(result)
        else:
            print(
                "Failure report: "
                f"category={result['category']} "
                f"silent_retry_authorized={result['silent_retry_authorized']}"
            )
        return 0 if result["passed"] else 1

    if args.command == "stop-loop":
        result = build_stop_loop_result(load_json(Path(args.failure_report_json)))
        if args.json:
            print_json(result)
        else:
            print(
                "Stop loop: "
                f"status={result['status']} "
                f"queue_promoted={result['queue_promoted']}"
            )
        return 0 if result["passed"] else 1

    if args.command == "validate":
        result = validate_control_chain()
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Control Chain validation")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"Commander: {result['commander']}")
            print(f"Track selector: {result['track_selector']}")
            print(f"Local executor: {result['local_executor']}")
            print(f"Queue manager: {result['queue_manager']}")
            print(f"Failure handling: {result['failure_handling']}")
            print(f"ColaMeta: {result['colameta']}")
            if result["errors"]:
                print("Errors:")
                for error in result["errors"]:
                    print(f"- {error}")
        return 0 if result["passed"] else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
