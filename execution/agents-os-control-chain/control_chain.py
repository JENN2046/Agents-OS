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
from typing import Any


CONTROL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = CONTROL_DIR.parents[1]
REGISTRY_DIR = WORKSPACE_ROOT / "control-plane" / "registry"
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from path_boundary import is_protected_path, is_under_workspace, safe_resolve

SCHEMAS_PATH = CONTROL_DIR / "control-chain.schemas.json"
MANIFEST_PATH = CONTROL_DIR / "control-chain-manifest.json"
DEFAULT_QUEUE = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-07-agents-os-active-work-queue-v0.1.md"
COLAMETA_PREFLIGHT = REGISTRY_DIR / "colameta-executor-preflight.py"
DOCCTL = REGISTRY_DIR / "docctl.py"

DECISIONS = (
    "route_to_colameta",
    "route_to_local_executor",
    "stop_needs_nobao_review",
    "stop_needs_jenn_decision",
    "reject_as_out_of_scope",
)
TRACKS = ("colameta", "local_executor", "stop")
AUTHORIZATION_SCOPES = ("none", "local_safe_only", "blocked_requires_jenn")
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
}
QUEUE_SIGNALS = {"queue_write", "queue_promotion"}
GLOBAL_BLOCKED_CAPABILITIES = [
    "provider_call",
    "service_start",
    "runtime_plugin_activation",
    "external_write",
    "formal_memory_write",
    "state_private_read",
    "auth_provider_runtime_config_change",
    "destructive_git_or_filesystem_operation",
]

COLAMETA_PATTERNS = re.compile(r"\b(colameta|executor readiness|plan reconciliation|runner metadata|prompt files?)\b", re.I)
LOCAL_PATTERNS = re.compile(
    r"\b(governance|document|registry|receipt|review|report|current_state|docctl|validation|local file|markdown)\b",
    re.I,
)


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
    proposal = queue_update_proposal(local_result)
    if proposal.get("active_queue_modified") is not False or proposal.get("proposal_only") is not True:
        errors.append("queue proposal mutated queue")

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
        },
        "track_selector": {
            "local_track_authorized": local_preview.get("track_authorized"),
            "blocked_track_authorized": blocked_preview.get("track_authorized"),
        },
        "local_executor": {
            "validation_passed": local_result.get("validation_passed"),
            "forbidden_blocked": forbidden_result.get("validation_passed") is False,
        },
        "queue_manager": {
            "proposal_only": proposal.get("proposal_only"),
            "active_queue_modified": proposal.get("active_queue_modified"),
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
    local_parser.add_argument("--command")
    local_parser.add_argument("--target-path")
    local_parser.add_argument("--content")
    local_parser.add_argument("--json", action="store_true")

    queue_parser = subparsers.add_parser("queue-proposal")
    queue_parser.add_argument("--track-result-json", required=True)
    queue_parser.add_argument("--json", action="store_true")

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
            command=args.command,
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
            print(f"ColaMeta: {result['colameta']}")
            if result["errors"]:
                print("Errors:")
                for error in result["errors"]:
                    print(f"- {error}")
        return 0 if result["passed"] else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
