#!/usr/bin/env python3
"""Read-only ColaMeta executor preflight gate for AGENTS OS.

This gate validates local readiness for a future executor run. It does not
start services, run executors, call providers, write Memory, or modify runtime
state.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


REGISTRY_DIR = Path(__file__).resolve().parent
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from path_boundary import is_protected_path, is_under_workspace, safe_resolve


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PLAN = WORKSPACE_ROOT / ".colameta" / "plan.json"
DEFAULT_PROMPT_DIR = WORKSPACE_ROOT / ".colameta" / "prompts"
DEFAULT_MEMORY = WORKSPACE_ROOT / ".colameta" / "memory.md"
DEFAULT_DOCCTL = REGISTRY_DIR / "docctl.py"
DEFAULT_COLAMETA_TOOLS = Path(os.environ.get("COLAMETA_TOOLS_PATH", "/home/jenn/tools/colameta"))

ALLOWED_WRITE_CLASSES = [
    ".colameta/reports/",
    ".colameta/runtime/plan-previews/",
    ".colameta/audits/",
    ".colameta/logs/ only if non-secret and not printed raw",
    "control-plane/registry/receipts/",
    "control-plane/registry/reviews/",
    "document registry metadata only to keep docctl doctor clean",
]

FORBIDDEN_WRITE_CLASSES = [
    ".colameta/plan.json",
    ".colameta/state.json",
    ".colameta/memory.md content",
    "auth/token/cookie/session files",
    "provider/runtime configuration",
    "state-private/",
    "WORKSPACE_REGISTRY.yaml",
    "formal Memory",
    "external systems",
]


def finding(rule_id: str, level: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "level": level, "message": message}


def workspace_display(path: Path) -> str:
    try:
        return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_workspace_file(path: Path, rule_id: str) -> tuple[Path | None, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    if is_protected_path(path):
        findings.append(finding(rule_id, "fail", f"path points to protected path: {path}"))
        return None, findings

    candidate = path if path.is_absolute() else WORKSPACE_ROOT / path
    resolved, resolve_error = safe_resolve(candidate)
    if resolve_error:
        findings.append(finding(rule_id, "fail", f"path could not be resolved: {resolve_error}"))
        return None, findings
    if resolved is None:
        findings.append(finding(rule_id, "fail", f"path could not be resolved: {path}"))
        return None, findings
    if is_protected_path(resolved):
        findings.append(finding(rule_id, "fail", f"path resolves to protected path: {path}"))
        return None, findings
    if not is_under_workspace(resolved, WORKSPACE_ROOT):
        findings.append(finding(rule_id, "fail", f"path points outside workspace: {path}"))
        return None, findings
    if not resolved.exists():
        findings.append(finding(rule_id, "fail", f"path does not exist: {workspace_display(resolved)}"))
        return None, findings
    if not resolved.is_file():
        findings.append(finding(rule_id, "fail", f"path is not a file: {workspace_display(resolved)}"))
        return None, findings
    return resolved, findings


def collect_prompt_files(value: Any) -> list[str]:
    prompt_files: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "prompt_file" and isinstance(item, str):
                prompt_files.append(item)
            else:
                prompt_files.extend(collect_prompt_files(item))
    elif isinstance(value, list):
        for item in value:
            prompt_files.extend(collect_prompt_files(item))
    return prompt_files


def load_colameta_classes(tools_path: Path) -> tuple[Any, Any, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    if is_protected_path(tools_path):
        findings.append(finding("COLAMETA-PREFLIGHT-TOOLS", "fail", f"tools path is protected: {tools_path}"))
        return None, None, findings
    if not tools_path.exists() or not tools_path.is_dir():
        findings.append(finding("COLAMETA-PREFLIGHT-TOOLS", "fail", f"tools path is unavailable: {tools_path}"))
        return None, None, findings
    if str(tools_path) not in sys.path:
        sys.path.insert(0, str(tools_path))
    try:
        from runner.plan_loader import PlanLoader
        from runner.plan_standards_linter import PlanStandardsLinter
    except Exception as exc:  # pragma: no cover - depends on local ColaMeta installation.
        findings.append(finding("COLAMETA-PREFLIGHT-TOOLS", "fail", f"ColaMeta imports failed: {type(exc).__name__}"))
        return None, None, findings
    return PlanLoader, PlanStandardsLinter, findings


def prompt_summary(prompt_files: list[str], prompt_dir: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    resolved_prompt_dir, dir_error = safe_resolve(prompt_dir)
    if dir_error or resolved_prompt_dir is None or not resolved_prompt_dir.exists():
        findings.append(finding("COLAMETA-PREFLIGHT-PROMPTS", "fail", "prompt directory is unavailable"))
        resolved_prompt_dir = prompt_dir

    prompt_names: list[str] = []
    missing: list[str] = []
    outside: list[str] = []
    protected: list[str] = []

    for prompt_file in prompt_files:
        prompt_path = Path(prompt_file)
        candidate = prompt_path if prompt_path.is_absolute() else WORKSPACE_ROOT / prompt_path
        resolved, resolve_error = safe_resolve(candidate)
        prompt_name = prompt_path.name
        prompt_names.append(prompt_name)
        if resolve_error or resolved is None:
            missing.append(prompt_name)
            continue
        if is_protected_path(resolved):
            protected.append(prompt_name)
            continue
        if not is_under_workspace(resolved, WORKSPACE_ROOT):
            outside.append(prompt_name)
            continue
        try:
            resolved.relative_to(resolved_prompt_dir)
        except ValueError:
            outside.append(prompt_name)
            continue
        if not resolved.exists() or not resolved.is_file():
            missing.append(prompt_name)

    if missing:
        findings.append(finding("COLAMETA-PREFLIGHT-PROMPTS", "fail", f"prompt files missing: {','.join(sorted(missing))}"))
    if outside:
        findings.append(finding("COLAMETA-PREFLIGHT-PROMPTS", "fail", f"prompt files outside prompt directory: {','.join(sorted(outside))}"))
    if protected:
        findings.append(finding("COLAMETA-PREFLIGHT-PROMPTS", "fail", f"prompt files protected: {','.join(sorted(protected))}"))

    unique_names = sorted(set(prompt_names))
    return (
        {
            "expected_count": len(prompt_files),
            "present_count": len(prompt_files) - len(set(missing)),
            "missing_count": len(set(missing)),
            "outside_count": len(set(outside)),
            "protected_count": len(set(protected)),
            "prompt_file_names": unique_names,
            "paths_under_prompt_dir": not outside and not protected,
            "raw_prompt_content_read": False,
        },
        findings,
    )


def docctl_status_summary(docctl_path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resolved, findings = resolve_workspace_file(docctl_path, "COLAMETA-PREFLIGHT-DOCCTL")
    if resolved is None:
        return {"status_passed": False}, findings
    run = subprocess.run(
        [sys.executable, str(resolved), "status", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if run.returncode != 0:
        return (
            {
                "status_passed": False,
                "returncode": run.returncode,
            },
            [finding("COLAMETA-PREFLIGHT-DOCCTL", "fail", "docctl status did not pass")],
        )
    try:
        payload = json.loads(run.stdout)
    except json.JSONDecodeError:
        return {"status_passed": False}, [finding("COLAMETA-PREFLIGHT-DOCCTL", "fail", "docctl status JSON could not be parsed")]

    doctor = payload.get("doctor", {}) if isinstance(payload, dict) else {}
    score = payload.get("score", {}) if isinstance(payload, dict) else {}
    trend = payload.get("trend", {}) if isinstance(payload, dict) else {}
    plan_fix = payload.get("plan_fix", {}) if isinstance(payload, dict) else {}
    summary = doctor.get("summary", {}) if isinstance(doctor, dict) else {}

    return (
        {
            "status_passed": bool(payload.get("passed")),
            "read_only": bool(payload.get("read_only")),
            "would_write": bool(payload.get("would_write")),
            "documents": summary.get("documents"),
            "unregistered": summary.get("unregistered_files"),
            "warn": summary.get("warn"),
            "fail": summary.get("fail"),
            "score": score.get("score") if isinstance(score, dict) else None,
            "eligible_95": score.get("eligible_95") if isinstance(score, dict) else None,
            "trend_status": trend.get("trend_status") if isinstance(trend, dict) else None,
            "plan_status": plan_fix.get("plan_status") if isinstance(plan_fix, dict) else None,
            "raw_docctl_output_exposed": False,
        },
        [],
    )


def memory_summary(memory_path: Path) -> tuple[dict[str, Any], list[dict[str, str]]]:
    resolved, findings = resolve_workspace_file(memory_path, "COLAMETA-PREFLIGHT-MEMORY")
    if resolved is None:
        return {"path": workspace_display(memory_path), "byte_count": None, "empty": False, "content_read": False}, findings
    byte_count = resolved.stat().st_size
    if byte_count != 0:
        findings.append(finding("COLAMETA-PREFLIGHT-MEMORY", "fail", ".colameta/memory.md is not empty"))
    return {
        "path": workspace_display(resolved),
        "byte_count": byte_count,
        "empty": byte_count == 0,
        "content_read": False,
    }, findings


def preflight(
    plan_path: Path = DEFAULT_PLAN,
    prompt_dir: Path = DEFAULT_PROMPT_DIR,
    memory_path: Path = DEFAULT_MEMORY,
    docctl_path: Path = DEFAULT_DOCCTL,
    colameta_tools_path: Path = DEFAULT_COLAMETA_TOOLS,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    PlanLoader, PlanStandardsLinter, tool_findings = load_colameta_classes(colameta_tools_path)
    findings.extend(tool_findings)

    resolved_plan, plan_findings = resolve_workspace_file(plan_path, "COLAMETA-PREFLIGHT-PLAN")
    findings.extend(plan_findings)

    plan_summary: dict[str, Any] = {
        "plan_loader_valid": False,
        "lint_status": None,
        "blocking_issue_count": None,
        "warning_count": None,
        "version_count": 0,
        "raw_plan_output_performed": False,
    }
    prompts = {
        "expected_count": 0,
        "present_count": 0,
        "missing_count": 0,
        "outside_count": 0,
        "protected_count": 0,
        "prompt_file_names": [],
        "paths_under_prompt_dir": False,
        "raw_prompt_content_read": False,
    }

    if resolved_plan is not None and PlanLoader is not None and PlanStandardsLinter is not None:
        try:
            with resolved_plan.open("r", encoding="utf-8") as handle:
                plan_data = json.load(handle)
            lint = PlanStandardsLinter().lint_plan_data(plan_data, project_root=str(WORKSPACE_ROOT))
            plan = PlanLoader().load_plan(str(resolved_plan))
            PlanLoader().validate_plan(plan)
            prompt_files = collect_prompt_files(plan_data)
            prompts, prompt_findings = prompt_summary(prompt_files, prompt_dir)
            findings.extend(prompt_findings)
            plan_summary = {
                "plan_loader_valid": True,
                "lint_status": lint.get("status"),
                "blocking_issue_count": lint.get("blocking_issue_count"),
                "warning_count": lint.get("warning_count"),
                "version_count": len(getattr(plan, "versions", [])),
                "raw_plan_output_performed": False,
            }
            if lint.get("status") != "passed" or lint.get("blocking_issue_count") or lint.get("warning_count"):
                findings.append(finding("COLAMETA-PREFLIGHT-LINT", "fail", "ColaMeta plan lint is not clean"))
        except Exception as exc:
            findings.append(finding("COLAMETA-PREFLIGHT-PLAN", "fail", f"plan validation failed: {type(exc).__name__}"))

    docctl, docctl_findings = docctl_status_summary(docctl_path)
    findings.extend(docctl_findings)
    if not docctl.get("status_passed"):
        findings.append(finding("COLAMETA-PREFLIGHT-DOCCTL", "fail", "docctl status is not clean"))

    memory, memory_findings = memory_summary(memory_path)
    findings.extend(memory_findings)

    failed = any(item.get("level") == "fail" for item in findings)
    return {
        "schema_version": "agents-os.colameta.executor_preflight.result.v0.1",
        "passed": not failed,
        "gate_status": "passed" if not failed else "failed",
        "read_only": True,
        "summary_only": True,
        "executor_authorized": False,
        "service_start_authorized": False,
        "provider_call_authorized": False,
        "memory_write_authorized": False,
        "external_write_authorized": False,
        "plan": plan_summary,
        "prompts": prompts,
        "docctl": docctl,
        "memory": memory,
        "allowed_write_classes": ALLOWED_WRITE_CLASSES,
        "forbidden_write_classes": FORBIDDEN_WRITE_CLASSES,
        "findings": findings,
        "warnings": {
            "service_started": False,
            "executor_ran": False,
            "provider_call_performed": False,
            "auth_token_cookie_session_modified": False,
            "provider_runtime_config_modified": False,
            "colameta_plan_modified": False,
            "colameta_state_modified": False,
            "colameta_memory_content_written": False,
            "formal_memory_written": False,
            "state_private_read": False,
            "raw_logs_output": False,
            "provider_raw_response_output": False,
            "secret_token_cookie_output": False,
            "workspace_registry_modified": False,
            "external_write_performed": False,
        },
    }


def format_text(result: dict[str, Any]) -> str:
    plan = result.get("plan", {})
    prompts = result.get("prompts", {})
    docctl = result.get("docctl", {})
    memory = result.get("memory", {})
    lines = [
        "ColaMeta executor preflight gate",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Gate status: {result['gate_status']}",
        f"Read only: {result['read_only']}",
        f"Summary only: {result['summary_only']}",
        f"Executor authorized: {result['executor_authorized']}",
        f"Service start authorized: {result['service_start_authorized']}",
        f"Provider call authorized: {result['provider_call_authorized']}",
        f"Memory write authorized: {result['memory_write_authorized']}",
        f"External write authorized: {result['external_write_authorized']}",
        (
            "Plan: "
            f"loader_valid={plan.get('plan_loader_valid')} "
            f"versions={plan.get('version_count')} "
            f"lint_status={plan.get('lint_status')} "
            f"blocking={plan.get('blocking_issue_count')} "
            f"warnings={plan.get('warning_count')}"
        ),
        (
            "Prompts: "
            f"expected={prompts.get('expected_count')} "
            f"present={prompts.get('present_count')} "
            f"missing={prompts.get('missing_count')} "
            f"under_prompt_dir={prompts.get('paths_under_prompt_dir')}"
        ),
        (
            "Docctl: "
            f"status_passed={docctl.get('status_passed')} "
            f"documents={docctl.get('documents')} "
            f"unregistered={docctl.get('unregistered')} "
            f"warn={docctl.get('warn')} fail={docctl.get('fail')} "
            f"score={docctl.get('score')}"
        ),
        f"Memory: bytes={memory.get('byte_count')} empty={memory.get('empty')} content_read={memory.get('content_read')}",
    ]
    if result.get("findings"):
        lines.append("")
        lines.append("Findings:")
        for item in result["findings"]:
            lines.append(f"- {item['level'].upper()} {item['rule_id']}: {item['message']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only ColaMeta executor preflight gate.")
    parser.add_argument("--plan", default=str(DEFAULT_PLAN), help="Workspace-local ColaMeta plan path.")
    parser.add_argument("--json", action="store_true", help="Emit summary-only JSON output.")
    args = parser.parse_args()

    result = preflight(Path(args.plan))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
