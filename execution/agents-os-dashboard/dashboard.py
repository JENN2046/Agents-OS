#!/usr/bin/env python3
"""Preview-only AGENTS OS dashboard.

The dashboard summarizes the current queue, last closed work, local validation
status, open blockers, last failure evidence, and candidate Memory entries. It
does not mutate the queue, write formal Memory, start services, call providers,
or read private state.
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
from typing import Any


DASHBOARD_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = DASHBOARD_DIR.parents[1]
REGISTRY_DIR = WORKSPACE_ROOT / "control-plane" / "registry"
MACHINE_PATH = WORKSPACE_ROOT / "execution" / "agents-os-machine" / "machine.py"
DEFAULT_QUEUE = WORKSPACE_ROOT / "control-plane" / "registry" / "reports" / "2026-07-18-agents-os-active-work-queue-v4.2.md"
ROUTE_SELECTION_PACKAGE = REGISTRY_DIR / "reports" / "2026-07-07-agents-os-next-route-selection-package-v0.1.md"
ROUTE_CHOICE_QUEUE_PROPOSAL_REPORT = REGISTRY_DIR / "reports" / "2026-07-07-agents-os-control-chain-route-choice-queue-proposal-v0.1.md"
ROUTE_ADOPTION_BUNDLE_REPORT = REGISTRY_DIR / "reports" / "2026-07-07-agents-os-control-chain-route-choice-adoption-bundle-preview-v0.1.md"
ROUTE_ADOPTION_PREVIEW_REPORT = REGISTRY_DIR / "reports" / "2026-07-07-agents-os-control-chain-reviewed-route-adoption-preview-v0.1.md"
ROUTE_ADOPTION_APPLY_GATE_REPORT = REGISTRY_DIR / "reports" / "2026-07-07-agents-os-control-chain-reviewed-route-adoption-apply-gate-v0.1.md"
DOCCTL = REGISTRY_DIR / "docctl.py"
MANIFEST_PATH = DASHBOARD_DIR / "dashboard-manifest.json"
SCHEMAS_PATH = DASHBOARD_DIR / "dashboard.schemas.json"

DANGEROUS_AUTHORIZATION_FLAGS = (
    "provider_call_authorized",
    "service_start_authorized",
    "executor_run_authorized",
    "external_write_authorized",
    "memory_write_authorized",
    "formal_memory_write_authorized",
    "private_memory_raw_read_authorized",
    "runtime_plugin_activation_authorized",
    "active_queue_mutation_authorized",
    "route_auto_selection_authorized",
    "queue_promotion_authorized",
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def load_machine() -> Any:
    spec = importlib.util.spec_from_file_location("agents_os_machine_for_dashboard", MACHINE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load machine module from {MACHINE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return str(path)


def stable_id(prefix: str, payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return f"{prefix}-{hashlib.sha256(encoded).hexdigest()[:10].upper()}"


def schema_required(schema_name: str) -> list[str]:
    schemas = load_json(SCHEMAS_PATH)
    required = schemas.get(schema_name, {}).get("required", [])
    if not isinstance(required, list):
        return []
    return [str(item) for item in required]


def authorization_defaults() -> dict[str, bool]:
    return {flag: False for flag in DANGEROUS_AUTHORIZATION_FLAGS}


def false_flag_failures(value: dict[str, Any], flags: tuple[str, ...] = DANGEROUS_AUTHORIZATION_FLAGS) -> list[str]:
    return [flag for flag in flags if value.get(flag) is not False]


def run_local_command(args: list[str]) -> dict[str, Any]:
    run = subprocess.run(args, cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": run.returncode,
        "stdout": run.stdout,
        "stderr": run.stderr,
    }


def parse_docctl_status(stdout: str, returncode: int) -> dict[str, Any]:
    status_match = re.search(r"^Status:\s+(\S+)", stdout, re.M)
    doctor_match = re.search(r"Doctor:\s+registries=(\d+)\s+documents=(\d+)\s+unregistered=(\d+)\s+warn=(\d+)\s+fail=(\d+)", stdout)
    score_match = re.search(r"Score:\s+score=(\d+)\s+eligible_95=(\w+)\s+hard_gates=(\d+)", stdout)
    trend_match = re.search(r"Trend:\s+status=(\S+)\s+snapshots=(\d+)\s+no_regression=(\w+)", stdout)
    return {
        "command": "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status",
        "returncode": returncode,
        "status": status_match.group(1) if status_match else "UNKNOWN",
        "read_only": "Read only: True" in stdout,
        "would_write": "Would write: True" in stdout,
        "doctor": {
            "registries": int(doctor_match.group(1)) if doctor_match else None,
            "documents": int(doctor_match.group(2)) if doctor_match else None,
            "unregistered": int(doctor_match.group(3)) if doctor_match else None,
            "warn": int(doctor_match.group(4)) if doctor_match else None,
            "fail": int(doctor_match.group(5)) if doctor_match else None,
        },
        "score": {
            "score": int(score_match.group(1)) if score_match else None,
            "eligible_95": score_match.group(2) == "True" if score_match else None,
            "hard_gates": int(score_match.group(3)) if score_match else None,
        },
        "trend": {
            "status": trend_match.group(1) if trend_match else None,
            "snapshots": int(trend_match.group(2)) if trend_match else None,
            "no_regression": trend_match.group(3) == "True" if trend_match else None,
        },
        "raw_output_included": False,
    }


def parse_docctl_doctor(stdout: str, returncode: int) -> dict[str, Any]:
    status_match = re.search(r"^Status:\s+(\S+)", stdout, re.M)
    summary_match = re.search(
        r"Summary:\s+registries=(\d+)\s+documents=(\d+)\s+scanned_files=(\d+)\s+known_external_scope=(\d+)\s+archived=(\d+)\s+unregistered=(\d+)\s+warn=(\d+)\s+fail=(\d+)",
        stdout,
    )
    return {
        "command": "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor",
        "returncode": returncode,
        "status": status_match.group(1) if status_match else "UNKNOWN",
        "summary": {
            "registries": int(summary_match.group(1)) if summary_match else None,
            "documents": int(summary_match.group(2)) if summary_match else None,
            "scanned_files": int(summary_match.group(3)) if summary_match else None,
            "known_external_scope": int(summary_match.group(4)) if summary_match else None,
            "archived": int(summary_match.group(5)) if summary_match else None,
            "unregistered": int(summary_match.group(6)) if summary_match else None,
            "warn": int(summary_match.group(7)) if summary_match else None,
            "fail": int(summary_match.group(8)) if summary_match else None,
        },
        "raw_output_included": False,
    }


def validation_status(run_validations: bool = True) -> dict[str, Any]:
    if not run_validations:
        return {
            "checked": False,
            "passed": None,
            "docctl_status": None,
            "docctl_doctor": None,
            "commands": [],
        }
    status_run = run_local_command(["python3", str(DOCCTL.relative_to(WORKSPACE_ROOT)), "status"])
    doctor_run = run_local_command(["python3", str(DOCCTL.relative_to(WORKSPACE_ROOT)), "doctor"])
    status = parse_docctl_status(status_run["stdout"], status_run["returncode"])
    doctor = parse_docctl_doctor(doctor_run["stdout"], doctor_run["returncode"])
    passed = (
        status_run["returncode"] == 0
        and doctor_run["returncode"] == 0
        and status.get("status") == "PASS"
        and doctor.get("status") == "PASS"
    )
    return {
        "checked": True,
        "passed": passed,
        "docctl_status": status,
        "docctl_doctor": doctor,
        "commands": [status["command"], doctor["command"]],
    }


def latest_closed_entry(normalized_queue: dict[str, Any]) -> dict[str, Any]:
    entries = normalized_queue.get("closed_entries", [])
    if not entries:
        return {"status": "none", "text": None, "source": "CLOSED"}
    latest = entries[-1]
    return {
        "status": "present",
        "id": latest.get("id"),
        "text": latest.get("text"),
        "source": "CLOSED",
    }


def open_blockers(normalized_queue: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": entry.get("id"),
            "text": entry.get("text"),
            "source": "BLOCKED",
        }
        for entry in normalized_queue.get("blocked_entries", [])
    ]


def first_item_title(normalized_queue: dict[str, Any], lane: str) -> str | None:
    items = normalized_queue.get("lanes", {}).get(lane, [])
    if not items:
        return None
    return str(items[0].get("title"))


def parse_route_options(path: Path = ROUTE_SELECTION_PACKAGE) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    options: list[dict[str, Any]] = []
    sections = re.split(r"(?m)^### Option ", text)
    for section in sections[1:]:
        header_match = re.match(r"([A-Z]):\s+(.+?)\s*$", section.splitlines()[0])
        if not header_match:
            continue
        first_safe_match = re.search(
            r"First safe package:\s*\n\s*```text\s*\n(.+?)\n```",
            section,
            re.S,
        )
        must_keep_match = re.search(
            r"Must keep:\s*\n\s*```text\s*\n(.+?)\n```",
            section,
            re.S,
        )
        options.append(
            {
                "option_id": header_match.group(1),
                "title": header_match.group(2).strip(),
                "first_safe_package": first_safe_match.group(1).strip() if first_safe_match else None,
                "must_keep": [
                    line.strip()
                    for line in (must_keep_match.group(1).splitlines() if must_keep_match else [])
                    if line.strip()
                ],
            }
        )
    return options


def route_selection_status(normalized_queue: dict[str, Any]) -> dict[str, Any]:
    now_title = first_item_title(normalized_queue, "NOW")
    awaiting_selection = now_title == "No Active Automatic Construction Item"
    options = parse_route_options()
    return {
        "schema_version": "agents-os.dashboard.route-selection.v0.1",
        "status": "awaiting_jenn_selection" if awaiting_selection else "not_active",
        "package_path": rel(ROUTE_SELECTION_PACKAGE),
        "package_exists": ROUTE_SELECTION_PACKAGE.exists(),
        "requires_jenn_decision": awaiting_selection,
        "route_auto_selection_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "option_count": len(options),
        "options": options,
        "raw_content_output": False,
    }


def next_user_action_status(route_selection: dict[str, Any], normalized_queue: dict[str, Any]) -> dict[str, Any]:
    route_ids = [
        str(option.get("option_id"))
        for option in route_selection.get("options", [])
        if option.get("option_id")
    ]
    awaiting_selection = route_selection.get("status") == "awaiting_jenn_selection"
    now_items = normalized_queue.get("lanes", {}).get("NOW", [])
    now_denied_signals = now_items[0].get("denied_signals", []) if now_items else []
    governance_decision_required = "jenn_decision_required" in now_denied_signals
    status = "none"
    instruction = None
    if awaiting_selection:
        status = "route_choice_required"
        instruction = "choose_one_route_id"
    elif governance_decision_required:
        status = "governance_decision_required"
        instruction = "follow_current_queue_decision_gate"
    requires_jenn_decision = awaiting_selection or governance_decision_required
    return {
        "schema_version": "agents-os.dashboard.next-user-action.v0.1",
        "status": status,
        "decision_owner": "Jenn" if requires_jenn_decision else None,
        "requires_jenn_decision": requires_jenn_decision,
        "instruction": instruction,
        "accepted_route_ids": route_ids if awaiting_selection else [],
        "template_source_path": rel(ROUTE_SELECTION_PACKAGE),
        "exact_confirmation_templates_available": awaiting_selection and ROUTE_SELECTION_PACKAGE.exists() and bool(route_ids),
        "template_section": "Exact Confirmation Text Templates" if awaiting_selection else None,
        "route_auto_selection_authorized": False,
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
        "raw_content_output": False,
    }


def route_adoption_gate_status(normalized_queue: dict[str, Any]) -> dict[str, Any]:
    queue_summary = normalized_queue.get("summary", {})
    now_title = first_item_title(normalized_queue, "NOW")
    awaiting_selection = now_title == "No Active Automatic Construction Item"
    required_gates = {
        "route_choice_queue_proposal": {
            "path": rel(ROUTE_CHOICE_QUEUE_PROPOSAL_REPORT),
            "exists": ROUTE_CHOICE_QUEUE_PROPOSAL_REPORT.exists(),
        },
        "reviewed_route_adoption_preview": {
            "path": rel(ROUTE_ADOPTION_PREVIEW_REPORT),
            "exists": ROUTE_ADOPTION_PREVIEW_REPORT.exists(),
        },
        "reviewed_route_adoption_apply_gate": {
            "path": rel(ROUTE_ADOPTION_APPLY_GATE_REPORT),
            "exists": ROUTE_ADOPTION_APPLY_GATE_REPORT.exists(),
        },
    }
    all_gates_present = all(gate["exists"] for gate in required_gates.values())
    can_apply_now = False
    return {
        "schema_version": "agents-os.dashboard.route-adoption-gate.v0.1",
        "status": "waiting_for_jenn_route_choice" if awaiting_selection else "not_active",
        "required_gates": required_gates,
        "all_required_gates_present": all_gates_present,
        "future_apply_gate_available": all_gates_present,
        "can_apply_now": can_apply_now,
        "current_next_count": queue_summary.get("next_count"),
        "requires_jenn_decision": awaiting_selection,
        "route_auto_selection_authorized": False,
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
        "raw_content_output": False,
    }


def route_choice_adoption_bundle_status(normalized_queue: dict[str, Any]) -> dict[str, Any]:
    now_title = first_item_title(normalized_queue, "NOW")
    awaiting_selection = now_title == "No Active Automatic Construction Item"
    bundle_available = ROUTE_ADOPTION_BUNDLE_REPORT.exists()
    return {
        "schema_version": "agents-os.dashboard.route-choice-adoption-bundle.v0.1",
        "status": "waiting_for_jenn_route_choice" if awaiting_selection else "not_active",
        "bundle_preview_path": rel(ROUTE_ADOPTION_BUNDLE_REPORT),
        "bundle_preview_exists": bundle_available,
        "bundle_preview_available": bundle_available,
        "requires_jenn_decision": awaiting_selection,
        "can_apply_now": False,
        "preview_only": True,
        "read_only": True,
        "confirmation_text_included": False,
        "raw_confirmation_text_output": False,
        "raw_template_output": False,
        "route_auto_selection_authorized": False,
        "active_queue_mutation_authorized": False,
        "queue_promotion_authorized": False,
        "route_adoption_authorized": False,
        "execution_authorized": False,
        "write_performed": False,
        "raw_content_output": False,
    }


def classify_failure_evidence(path: Path, title: str) -> str:
    lowered = f"{path.name}\n{title}".lower()
    if "failure-handling-stop-loop" in lowered or "failure handling stop loop" in lowered:
        return "implementation_report"
    if "failure report" in lowered or "incident" in lowered:
        return "failure_event"
    return "unknown_failure_reference"


def markdown_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines()[:40]:
            if line.startswith("# "):
                return line[2:].strip()
    except UnicodeDecodeError:
        return ""
    return ""


def last_failure_evidence() -> dict[str, Any]:
    reports = sorted((REGISTRY_DIR / "reports").glob("*failure*.md"))
    candidates = []
    for path in reports:
        title = markdown_title(path)
        kind = classify_failure_evidence(path, title)
        candidates.append({"path": rel(path), "title": title, "kind": kind})
    events = [candidate for candidate in candidates if candidate["kind"] == "failure_event"]
    if events:
        latest = events[-1]
        return {
            "status": "present",
            "path": latest["path"],
            "title": latest["title"],
            "evidence_kind": latest["kind"],
            "raw_content_output": False,
        }
    return {
        "status": "none",
        "reason": "no concrete failure event report found",
        "non_event_failure_documents": candidates,
        "raw_content_output": False,
    }


def memory_candidate(source: str, title: str, text: str, rationale: str, stability: str) -> dict[str, Any]:
    candidate = {
        "schema_version": "agents-os.dashboard.memory-candidate.v0.1",
        "candidate_id": stable_id("MEMCAND", [source, title, text]),
        "candidate_only": True,
        "source": source,
        "title": title,
        "candidate_text": text,
        "rationale": rationale,
        "stability": stability,
        "formal_memory_write_authorized": False,
        "memory_write_performed": False,
        "private_memory_raw_read": False,
        "requires_jenn_confirmation": True,
        "recommended_action": "review_or_discard",
    }
    errors = validate_memory_candidate(candidate)
    candidate["passed"] = not errors
    candidate["errors"] = errors
    return candidate


def build_memory_candidates(normalized_queue: dict[str, Any], validation: dict[str, Any]) -> list[dict[str, Any]]:
    now_title = first_item_title(normalized_queue, "NOW") or "unknown"
    candidates = [
        memory_candidate(
            "active_work_queue.NOW",
            "Current AGENTS OS NOW",
            f"Current AGENTS OS NOW is {now_title}.",
            "Useful handoff state if Jenn explicitly chooses a Memory entry point.",
            "medium",
        )
    ]
    if validation.get("passed") is True:
        score = validation.get("docctl_status", {}).get("score", {}).get("score")
        candidates.append(
            memory_candidate(
                "docctl.status",
                "Document governance validation state",
                f"docctl status is PASS with score {score}.",
                "Stable enough to consider as a governance health memory candidate only after review.",
                "medium",
            )
        )
    blockers = open_blockers(normalized_queue)
    if blockers:
        candidates.append(
            memory_candidate(
                "active_work_queue.BLOCKED",
                "Open AGENTS OS blockers",
                f"Open blockers count is {len(blockers)}; formal Memory remains blocked until Jenn chooses an entry point.",
                "Highlights persistent boundaries without writing Memory.",
                "medium",
            )
        )
    return candidates


def build_dashboard_summary(queue_path: Path = DEFAULT_QUEUE, *, run_validations: bool = True) -> dict[str, Any]:
    machine = load_machine()
    normalized_queue = machine.load_queue(queue_path)
    validation = validation_status(run_validations=run_validations)
    authorization = authorization_defaults()
    blockers = open_blockers(normalized_queue)
    last_completed = latest_closed_entry(normalized_queue)
    last_failure = last_failure_evidence()
    memory_candidates = build_memory_candidates(normalized_queue, validation)
    now_title = first_item_title(normalized_queue, "NOW")
    route_selection = route_selection_status(normalized_queue)
    next_user_action = next_user_action_status(route_selection, normalized_queue)
    route_adoption_gate = route_adoption_gate_status(normalized_queue)
    route_choice_adoption_bundle = route_choice_adoption_bundle_status(normalized_queue)
    queue_summary = {
        "source_path": normalized_queue.get("source_path"),
        "passed": normalized_queue.get("passed"),
        "summary": normalized_queue.get("summary"),
        "now": {
            "title": now_title,
            "id": normalized_queue.get("lanes", {}).get("NOW", [{}])[0].get("id")
            if normalized_queue.get("lanes", {}).get("NOW")
            else None,
        },
        "next_title": first_item_title(normalized_queue, "NEXT"),
    }
    summary = {
        "schema_version": "agents-os.dashboard.summary.v0.1",
        "dashboard_id": stable_id(
            "DASHBOARD",
            [
                queue_summary,
                route_selection,
                next_user_action,
                route_adoption_gate,
                route_choice_adoption_bundle,
                validation.get("passed"),
                last_completed,
                last_failure,
            ],
        ),
        "preview_only": True,
        "read_only": True,
        "write_performed": False,
        "execution_authorized": False,
        "authorization": authorization,
        "queue": queue_summary,
        "last_completed": last_completed,
        "last_failure": last_failure,
        "route_selection": route_selection,
        "next_user_action": next_user_action,
        "route_adoption_gate": route_adoption_gate,
        "route_choice_adoption_bundle": route_choice_adoption_bundle,
        "validation_status": validation,
        "open_blockers": blockers,
        "memory_candidates": memory_candidates,
        "formal_memory_write_authorized": False,
        "private_memory_raw_read_authorized": False,
        "errors": list(normalized_queue.get("parse_errors", [])),
    }
    errors = validate_dashboard_summary(summary)
    summary["passed"] = not errors
    summary["errors"] = sorted(set(summary["errors"] + errors))
    return summary


def validate_memory_candidate(candidate: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("memory_candidate") if field not in candidate]
    if candidate.get("candidate_only") is not True:
        errors.append("memory candidate must remain candidate_only")
    if candidate.get("formal_memory_write_authorized") is not False:
        errors.append("memory candidate must not authorize formal Memory write")
    if candidate.get("memory_write_performed") is not False:
        errors.append("memory candidate must not perform Memory write")
    if candidate.get("private_memory_raw_read") is not False:
        errors.append("memory candidate must not read private raw Memory")
    if candidate.get("requires_jenn_confirmation") is not True:
        errors.append("memory candidate must require Jenn confirmation")
    return errors


def validate_dashboard_summary(summary: dict[str, Any]) -> list[str]:
    errors = [f"missing required field: {field}" for field in schema_required("dashboard_summary") if field not in summary]
    if summary.get("preview_only") is not True:
        errors.append("dashboard summary must be preview_only")
    if summary.get("read_only") is not True:
        errors.append("dashboard summary must be read_only")
    if summary.get("write_performed") is not False:
        errors.append("dashboard summary must not write")
    if summary.get("execution_authorized") is not False:
        errors.append("dashboard summary must not authorize execution")
    if summary.get("formal_memory_write_authorized") is not False:
        errors.append("dashboard summary must not authorize formal Memory write")
    if summary.get("private_memory_raw_read_authorized") is not False:
        errors.append("dashboard summary must not authorize private raw Memory read")
    authorization_failures = false_flag_failures(summary.get("authorization", {}))
    if authorization_failures:
        errors.append(f"dashboard dangerous authorization flags not false: {','.join(authorization_failures)}")
    if summary.get("queue", {}).get("passed") is not True:
        errors.append("dashboard queue summary did not pass")
    route_selection = summary.get("route_selection", {})
    if route_selection.get("route_auto_selection_authorized") is not False:
        errors.append("dashboard route selection must not authorize route auto-selection")
    if route_selection.get("queue_promotion_authorized") is not False:
        errors.append("dashboard route selection must not authorize queue promotion")
    if route_selection.get("execution_authorized") is not False:
        errors.append("dashboard route selection must not authorize execution")
    if route_selection.get("status") == "awaiting_jenn_selection":
        if route_selection.get("requires_jenn_decision") is not True:
            errors.append("dashboard route selection stop-state must require Jenn decision")
        if route_selection.get("option_count", 0) < 1:
            errors.append("dashboard route selection stop-state should surface options")
    next_user_action = summary.get("next_user_action", {})
    for flag in (
        "route_auto_selection_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "write_performed",
    ):
        if next_user_action.get(flag) is not False:
            errors.append(f"dashboard next user action must not authorize {flag}")
    if route_selection.get("status") == "awaiting_jenn_selection":
        if next_user_action.get("status") != "route_choice_required":
            errors.append("dashboard next user action must require route choice during stop-state")
        if next_user_action.get("decision_owner") != "Jenn":
            errors.append("dashboard next user action decision owner must be Jenn")
        if next_user_action.get("requires_jenn_decision") is not True:
            errors.append("dashboard next user action must require Jenn decision")
        route_option_ids = [option.get("option_id") for option in route_selection.get("options", [])]
        if next_user_action.get("accepted_route_ids") != route_option_ids:
            errors.append("dashboard next user action route ids must match route selection options")
        if next_user_action.get("exact_confirmation_templates_available") is not True:
            errors.append("dashboard next user action should point to available confirmation templates")
    elif next_user_action.get("status") == "governance_decision_required":
        if next_user_action.get("decision_owner") != "Jenn":
            errors.append("dashboard governance decision owner must be Jenn")
        if next_user_action.get("requires_jenn_decision") is not True:
            errors.append("dashboard governance decision must require Jenn")
        if next_user_action.get("accepted_route_ids"):
            errors.append("dashboard generic governance decision must not surface route ids")
        if next_user_action.get("exact_confirmation_templates_available") is not False:
            errors.append("dashboard generic governance decision must not claim route confirmation templates")
    route_adoption_gate = summary.get("route_adoption_gate", {})
    for flag in (
        "route_auto_selection_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "execution_authorized",
        "write_performed",
    ):
        if route_adoption_gate.get(flag) is not False:
            errors.append(f"dashboard route adoption gate must not authorize {flag}")
    if route_adoption_gate.get("status") == "waiting_for_jenn_route_choice":
        if route_adoption_gate.get("requires_jenn_decision") is not True:
            errors.append("dashboard route adoption gate wait-state must require Jenn decision")
        if route_adoption_gate.get("can_apply_now") is not False:
            errors.append("dashboard route adoption gate must not be directly applicable before Jenn route choice")
        if route_adoption_gate.get("all_required_gates_present") is not True:
            errors.append("dashboard route adoption gate should surface all required gates")
    route_choice_adoption_bundle = summary.get("route_choice_adoption_bundle", {})
    for flag in (
        "route_auto_selection_authorized",
        "active_queue_mutation_authorized",
        "queue_promotion_authorized",
        "route_adoption_authorized",
        "execution_authorized",
        "write_performed",
        "confirmation_text_included",
        "raw_confirmation_text_output",
        "raw_template_output",
        "raw_content_output",
    ):
        if route_choice_adoption_bundle.get(flag) is not False:
            errors.append(f"dashboard route choice adoption bundle must not authorize {flag}")
    if route_choice_adoption_bundle.get("status") == "waiting_for_jenn_route_choice":
        if route_choice_adoption_bundle.get("requires_jenn_decision") is not True:
            errors.append("dashboard route choice adoption bundle wait-state must require Jenn decision")
        if route_choice_adoption_bundle.get("bundle_preview_available") is not True:
            errors.append("dashboard route choice adoption bundle should surface available bundle preview")
        if route_choice_adoption_bundle.get("can_apply_now") is not False:
            errors.append("dashboard route choice adoption bundle must not apply before Jenn route choice")
    if route_choice_adoption_bundle.get("preview_only") is not True:
        errors.append("dashboard route choice adoption bundle must be preview_only")
    if route_choice_adoption_bundle.get("read_only") is not True:
        errors.append("dashboard route choice adoption bundle must be read_only")
    validation = summary.get("validation_status", {})
    if validation.get("checked") is True and validation.get("passed") is not True:
        errors.append("dashboard validation status did not pass")
    for candidate in summary.get("memory_candidates", []):
        candidate_errors = validate_memory_candidate(candidate)
        errors.extend(f"{candidate.get('candidate_id', 'memory_candidate')}: {error}" for error in candidate_errors)
    return errors


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("default_mode") != "summary_preview":
        errors.append("manifest default_mode must be summary_preview")
    defaults = manifest.get("authorization_defaults", {})
    failures = false_flag_failures(defaults)
    if failures:
        errors.append(f"manifest authorization defaults not false: {','.join(failures)}")
    memory_defaults = manifest.get("memory_candidate_defaults", {})
    if memory_defaults.get("candidate_only") is not True:
        errors.append("manifest memory candidate default must be candidate_only")
    for flag in ("formal_memory_write_authorized", "memory_write_performed", "private_memory_raw_read"):
        if memory_defaults.get(flag) is not False:
            errors.append(f"manifest memory candidate default must not enable {flag}")
    if memory_defaults.get("requires_jenn_confirmation") is not True:
        errors.append("manifest memory candidates must require Jenn confirmation")
    return errors


def validate_dashboard(run_validations: bool = True) -> dict[str, Any]:
    manifest_errors = validate_manifest(load_json(MANIFEST_PATH))
    summary = build_dashboard_summary(run_validations=run_validations)
    errors = list(manifest_errors)
    if not summary.get("passed"):
        errors.extend(summary.get("errors", []))
    return {
        "schema_version": "agents-os.dashboard.validation.v0.1",
        "passed": not errors,
        "errors": errors,
        "summary_passed": summary.get("passed"),
        "now": summary.get("queue", {}).get("now", {}),
        "route_selection": summary.get("route_selection", {}),
        "next_user_action": summary.get("next_user_action", {}),
        "route_adoption_gate": summary.get("route_adoption_gate", {}),
        "route_choice_adoption_bundle": summary.get("route_choice_adoption_bundle", {}),
        "last_completed": summary.get("last_completed", {}),
        "last_failure": summary.get("last_failure", {}),
        "validation_status": {
            "checked": summary.get("validation_status", {}).get("checked"),
            "passed": summary.get("validation_status", {}).get("passed"),
        },
        "memory_candidate_count": len(summary.get("memory_candidates", [])),
        "formal_memory_write_authorized": summary.get("formal_memory_write_authorized"),
        "private_memory_raw_read_authorized": summary.get("private_memory_raw_read_authorized"),
    }


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENTS OS preview-only dashboard.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary")
    summary_parser.add_argument("--queue", default=str(DEFAULT_QUEUE))
    summary_parser.add_argument("--no-validation", action="store_true")
    summary_parser.add_argument("--json", action="store_true")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--no-validation", action="store_true")
    validate_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "summary":
        result = build_dashboard_summary(Path(args.queue), run_validations=not args.no_validation)
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Dashboard summary")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"NOW: {result['queue']['now']['title']}")
            print(f"Route selection: {result['route_selection']['status']} options={result['route_selection']['option_count']}")
            print(f"Next user action: {result['next_user_action']['status']}")
            print(f"Route adoption gate: {result['route_adoption_gate']['status']}")
            print(f"Route adoption bundle: {result['route_choice_adoption_bundle']['status']}")
            print(f"Last completed: {result['last_completed'].get('text')}")
            print(f"Last failure: {result['last_failure'].get('status')}")
            print(f"Memory candidates: {len(result['memory_candidates'])}")
        return 0 if result["passed"] else 1

    if args.command == "validate":
        result = validate_dashboard(run_validations=not args.no_validation)
        if args.json:
            print_json(result)
        else:
            print("AGENTS OS Dashboard validation")
            print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
            print(f"NOW: {result['now'].get('title')}")
            print(f"Route selection: {result['route_selection'].get('status')}")
            print(f"Next user action: {result['next_user_action'].get('status')}")
            print(f"Route adoption gate: {result['route_adoption_gate'].get('status')}")
            print(f"Route adoption bundle: {result['route_choice_adoption_bundle'].get('status')}")
            print(f"Memory candidates: {result['memory_candidate_count']}")
            if result["errors"]:
                print("Errors:")
                for error in result["errors"]:
                    print(f"- {error}")
        return 0 if result["passed"] else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
