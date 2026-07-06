#!/usr/bin/env python3
"""Preview-only AGENTS OS task producer skeleton.

The producer turns explicit intent text or allowlisted review/report documents
into candidate task JSON. It does not modify the Active Work Queue, promote
lanes, authorize execution, start services, call providers, write Memory, or
perform external writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


PRODUCER_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = PRODUCER_DIR.parents[1]
REGISTRY_DIR = WORKSPACE_ROOT / "control-plane" / "registry"
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from path_boundary import preflight_target

MANIFEST_PATH = PRODUCER_DIR / "producer-manifest.json"
SCHEMA_PATH = PRODUCER_DIR / "candidate-task.schema.json"
DOCCTL = WORKSPACE_ROOT / "control-plane" / "registry" / "docctl.py"
DEFAULT_REVIEW_SOURCE = (
    WORKSPACE_ROOT
    / "control-plane"
    / "registry"
    / "reports"
    / "2026-07-07-agents-os-machine-to-task-producer-queue-transition-v0.1.md"
)
DEFAULT_ROUTE_SELECTION_PACKAGE = (
    WORKSPACE_ROOT
    / "control-plane"
    / "registry"
    / "reports"
    / "2026-07-07-agents-os-next-route-selection-package-v0.1.md"
)

LANES = ("NOW", "NEXT", "LATER")
ROUTE_OPTIONS = ("A", "B", "C", "D", "E")
ALLOWED_REVIEW_SOURCE_ROOTS = (
    WORKSPACE_ROOT / "control-plane" / "registry" / "reports",
    WORKSPACE_ROOT / "control-plane" / "registry" / "reviews",
)

DANGEROUS_AUTHORIZATION_FLAGS = (
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
)

QUEUE_EFFECT_FLAGS = (
    "queue_write_authorized",
    "active_queue_modified",
    "promotion_authorized",
)

EXECUTION_EFFECT_FLAGS = (
    "write_performed",
    "execution_authorized",
    "service_started",
    "executor_run_performed",
    "provider_call_performed",
    "external_write_performed",
    "memory_write_performed",
    "runtime_plugin_activation_performed",
    "plugin_execution_performed",
)

DENIED_SIGNAL_PATTERNS = {
    "provider_call": re.compile(r"\b(call|invoke|use|run)\s+(a\s+)?provider\b|\bprovider_call_authorized\s*=\s*true\b", re.I),
    "service_start": re.compile(r"\b(start|launch|run)\s+(a\s+)?service\b|\bservice_start_authorized\s*=\s*true\b", re.I),
    "executor_run": re.compile(r"\b(run|start|launch)\s+(the\s+)?executor\b|\bexecutor_run_authorized\s*=\s*true\b", re.I),
    "external_write": re.compile(
        r"\b(perform|do|make|authorize|execute)\s+(an\s+)?external\s+write\b"
        r"|\b(write|post|send|upload|create|update|publish)\s+(to\s+)?(notion|github|email|mail|slack|discord|external)\b"
        r"|\b(create|update|close|delete)\s+(a\s+)?github\s+(issue|pr|pull request|release)\b"
        r"|\b(send|write)\s+(an\s+)?email\b"
        r"|\bexternal_write_authorized\s*=\s*true\b",
        re.I,
    ),
    "database_write": re.compile(r"\b(database|db)\s+write\b|\b(write|update|delete|insert|migrate)\s+(database|db)\b", re.I),
    "memory_write": re.compile(r"\b(write|update|register)\s+(formal\s+)?memory\b|\bmemory_write_authorized\s*=\s*true\b", re.I),
    "runtime_plugin_activation": re.compile(
        r"\bactivate\s+(plugin|runtime|vcptoolbox|colameta)\b"
        r"|\bruntime_plugin_activation_authorized\s*=\s*true\b"
        r"|\bplugin_execution_authorized\s*=\s*true\b",
        re.I,
    ),
    "queue_write": re.compile(
        r"\b(modify|update|write|edit|mutate)\s+(the\s+)?active\s+work\s+queue\b"
        r"|\bqueue_write_authorized\s*=\s*true\b"
        r"|\bactive_queue_modified\s*=\s*true\b",
        re.I,
    ),
    "queue_promotion": re.compile(
        r"\b(promote|advance|move)\s+.+\s+(to\s+)?NOW\b"
        r"|\bpromotion_authorized\s*=\s*true\b",
        re.I,
    ),
    "state_private": re.compile(r"\bstate-private/", re.I),
    "auth_or_secret_config": re.compile(r"\b(auth|token|cookie|session|credential|secret|provider config|runtime config)\b", re.I),
    "git_release_boundary": re.compile(r"\b(git push|git tag|force push|release|deploy|publish|history rewrite|npm publish|package publish)\b", re.I),
    "route_selection_required": re.compile(
        r"\brequires_jenn_route_choice\s*=\s*true\b"
        r"|\broute_selection_required\s*=\s*true\b"
        r"|\bNo Active Automatic Construction Item\b",
        re.I,
    ),
}

NEGATED_SIGNAL_CONTEXT = re.compile(
    r"\b(no|do not|does not|cannot|can't|must not|must remain false|blocked actions?|blocked until|keep .*blocked|forbidden|denied)\b",
    re.I,
)

JENN_DECISION_SIGNALS = {
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
}

REDACTION_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?i)\b(token|secret|cookie|password|credential)\s*[:=]\s*\S+"),
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


def is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def finding(rule_id: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "level": "fail", "message": message}


def authorization_defaults() -> dict[str, bool]:
    return {flag: False for flag in DANGEROUS_AUTHORIZATION_FLAGS}


def queue_effect_defaults() -> dict[str, bool]:
    return {flag: False for flag in QUEUE_EFFECT_FLAGS}


def execution_effect_defaults() -> dict[str, bool]:
    return {flag: False for flag in EXECUTION_EFFECT_FLAGS}


def redact_sensitive(text: str) -> str:
    redacted = text
    for pattern in REDACTION_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def compact_text(text: str, max_chars: int = 220) -> str:
    compact = re.sub(r"\s+", " ", redact_sensitive(text)).strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


def title_from_text(text: str, default: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return compact_text(stripped, max_chars=96)
    return default


def extract_headings(markdown: str, limit: int = 6) -> list[str]:
    headings: list[str] = []
    for line in markdown.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            headings.append(compact_text(match.group(1), max_chars=120))
        if len(headings) >= limit:
            break
    return headings


def find_denied_signals(text: str) -> list[str]:
    scan_text = "\n".join(
        line for line in text.splitlines() if not NEGATED_SIGNAL_CONTEXT.search(line)
    )
    hits: list[str] = []
    for signal_id, pattern in DENIED_SIGNAL_PATTERNS.items():
        if pattern.search(scan_text):
            hits.append(signal_id)
    return sorted(set(hits))


def review_gate(denied_signals: list[str]) -> dict[str, Any]:
    requires_jenn = bool(set(denied_signals) & JENN_DECISION_SIGNALS)
    if requires_jenn:
        reason = "candidate contains P3 or runtime/provider/external/private-state signal"
    elif denied_signals:
        reason = "candidate contains queue mutation or promotion signal and needs Nobao review"
    else:
        reason = "candidate task must be reviewed before queue adoption"
    return {
        "producer_generated": True,
        "status": "candidate_preview",
        "requires_nobao_review": True,
        "requires_jenn_decision": requires_jenn,
        "review_status": "pending",
        "execution_authorized": False,
        "review_reason": reason,
    }


def stable_candidate_id(kind: str, title: str, summary: str) -> str:
    digest = hashlib.sha256(f"{kind}\n{title}\n{summary}".encode("utf-8")).hexdigest()[:8].upper()
    return f"CANDIDATE-{digest}"


def build_candidate(
    *,
    source_kind: str,
    title: str,
    summary: str,
    proposed_lane: str,
    source_path: Path | None = None,
    source_facts: dict[str, Any] | None = None,
    signal_text: str | None = None,
    candidate_id: str | None = None,
) -> dict[str, Any]:
    denied_signals = find_denied_signals(signal_text or f"{title}\n{summary}")
    return {
        "schema_version": "agents-os.task-producer.candidate-task.v0.1",
        "candidate_id": candidate_id or stable_candidate_id(source_kind, title, summary),
        "producer_generated": True,
        "status": "candidate_preview",
        "proposed_lane": proposed_lane,
        "title": title,
        "summary": summary,
        "source": {
            "kind": source_kind,
            "path": rel(source_path) if source_path else None,
            "raw_content_included": False,
        },
        "source_facts": source_facts or {},
        "risk_signals": denied_signals,
        "blocked": bool(denied_signals),
        "actionable_after_review": not bool(set(denied_signals) & JENN_DECISION_SIGNALS),
        "authorization": authorization_defaults(),
        "queue_effect": queue_effect_defaults(),
        "execution_effect": execution_effect_defaults(),
        "review_gate": review_gate(denied_signals),
        "json_output_authoritative": True,
    }


def candidate_from_intent(intent: str, proposed_lane: str = "NEXT", candidate_id: str | None = None) -> dict[str, Any]:
    title = title_from_text(intent, "Untitled local candidate task")
    summary = compact_text(intent, max_chars=260)
    return build_candidate(
        source_kind="explicit_intent",
        title=title,
        summary=summary,
        proposed_lane=proposed_lane,
        source_facts={
            "input_character_count": len(intent),
            "input_line_count": len(intent.splitlines()),
            "raw_content_included": False,
        },
        signal_text=intent,
        candidate_id=candidate_id,
    )


def resolve_review_source(source: Path) -> tuple[Path | None, list[dict[str, str]]]:
    candidate = source if source.is_absolute() else WORKSPACE_ROOT / source
    findings = preflight_target(candidate, WORKSPACE_ROOT, "TASK-PRODUCER-SOURCE-PATH")
    if findings:
        return None, findings
    resolved = candidate.resolve()
    if resolved.suffix.lower() != ".md":
        return None, [finding("TASK-PRODUCER-SOURCE-TYPE", f"source must be a Markdown file: {source}")]
    if not any(is_under(resolved, root) for root in ALLOWED_REVIEW_SOURCE_ROOTS):
        allowed = ", ".join(rel(root) for root in ALLOWED_REVIEW_SOURCE_ROOTS)
        return None, [finding("TASK-PRODUCER-SOURCE-ALLOWLIST", f"source is outside allowlisted review/report roots: {source}; allowed={allowed}")]
    return resolved, []


def candidate_from_review_source(
    source: Path,
    proposed_lane: str = "NEXT",
    candidate_id: str | None = None,
) -> dict[str, Any]:
    resolved, findings = resolve_review_source(source)
    if findings or resolved is None:
        return {
            "schema_version": "agents-os.task-producer.source-preflight.v0.1",
            "passed": False,
            "source_path": str(source),
            "findings": findings,
            "write_performed": False,
            "queue_write_authorized": False,
            "execution_authorized": False,
        }
    text = resolved.read_text(encoding="utf-8")
    headings = extract_headings(text)
    first_heading = headings[0] if headings else resolved.stem
    title = f"Review follow-up: {first_heading}"
    summary = (
        f"Candidate derived from allowlisted review/report file {rel(resolved)}. "
        f"Raw source body is not included in the output."
    )
    return build_candidate(
        source_kind="allowlisted_review_or_report",
        title=title,
        summary=summary,
        proposed_lane=proposed_lane,
        source_path=resolved,
        source_facts={
            "heading_count": len(headings),
            "headings": headings,
            "line_count": len(text.splitlines()),
            "character_count": len(text),
            "raw_content_included": False,
        },
        signal_text=text,
        candidate_id=candidate_id,
    )


def parse_route_options(markdown: str) -> dict[str, dict[str, Any]]:
    options: dict[str, dict[str, Any]] = {}
    sections = re.split(r"(?m)^### Option ", markdown)
    for section in sections[1:]:
        lines = section.splitlines()
        if not lines:
            continue
        header_match = re.match(r"([A-Z]):\s+(.+?)\s*$", lines[0])
        if not header_match:
            continue
        option_id = header_match.group(1)
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
        options[option_id] = {
            "option_id": option_id,
            "title": compact_text(header_match.group(2), max_chars=120),
            "first_safe_package": compact_text(first_safe_match.group(1), max_chars=160) if first_safe_match else None,
            "must_keep": [
                compact_text(line, max_chars=160)
                for line in (must_keep_match.group(1).splitlines() if must_keep_match else [])
                if line.strip()
            ],
        }
    return options


def route_option_preflight_failure(
    *,
    source: Path,
    option_id: str,
    findings: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "schema_version": "agents-os.task-producer.route-option-preflight.v0.1",
        "passed": False,
        "source_path": str(source),
        "route_option_id": option_id,
        "findings": findings,
        "write_performed": False,
        "queue_write_authorized": False,
        "route_auto_selection_authorized": False,
        "execution_authorized": False,
    }


def candidate_from_route_option(
    option_id: str,
    source: Path = DEFAULT_ROUTE_SELECTION_PACKAGE,
    proposed_lane: str = "NEXT",
    candidate_id: str | None = None,
) -> dict[str, Any]:
    normalized_option_id = option_id.strip().upper()
    resolved, findings = resolve_review_source(source)
    if findings or resolved is None:
        return route_option_preflight_failure(source=source, option_id=normalized_option_id, findings=findings)
    if normalized_option_id not in ROUTE_OPTIONS:
        return route_option_preflight_failure(
            source=source,
            option_id=normalized_option_id,
            findings=[
                finding(
                    "TASK-PRODUCER-ROUTE-OPTION",
                    f"route option must be one of {','.join(ROUTE_OPTIONS)}: {option_id}",
                )
            ],
        )
    text = resolved.read_text(encoding="utf-8")
    options = parse_route_options(text)
    route_option = options.get(normalized_option_id)
    if route_option is None:
        return route_option_preflight_failure(
            source=source,
            option_id=normalized_option_id,
            findings=[
                finding(
                    "TASK-PRODUCER-ROUTE-OPTION-MISSING",
                    f"route option {normalized_option_id} not found in {rel(resolved)}",
                )
            ],
        )
    first_safe_package = route_option.get("first_safe_package") or f"Route option {normalized_option_id}: {route_option['title']}"
    title = f"Route option {normalized_option_id}: {first_safe_package}"
    summary = (
        f"Candidate preview for Jenn-selectable route option {normalized_option_id}: "
        f"{route_option['title']}. This does not select the route, write the queue, "
        "authorize execution, start services, call providers, write Memory, or perform external writes."
    )
    return build_candidate(
        source_kind="route_selection_option",
        title=title,
        summary=summary,
        proposed_lane=proposed_lane,
        source_path=resolved,
        source_facts={
            "route_option_id": normalized_option_id,
            "route_option_title": route_option["title"],
            "first_safe_package": first_safe_package,
            "must_keep": route_option.get("must_keep", []),
            "available_option_count": len(options),
            "route_selected": False,
            "route_auto_selection_authorized": False,
            "queue_promotion_authorized": False,
            "raw_content_included": False,
        },
        signal_text=f"{title}\n{summary}\nrequires_jenn_route_choice=true",
        candidate_id=candidate_id,
    )


def has_false_flags(value: dict[str, Any], flags: Any) -> tuple[bool, list[str]]:
    if not isinstance(flags, list):
        flags = list(flags)
    failures = [str(flag) for flag in flags if value.get(str(flag)) is not False]
    return not failures, failures


def validate_candidate(candidate: dict[str, Any], schema: dict[str, Any] | None = None) -> list[str]:
    schema = schema or load_json(SCHEMA_PATH)
    errors: list[str] = []
    for field in schema.get("required", []):
        if field not in candidate:
            errors.append(f"missing required field: {field}")
    if candidate.get("schema_version") != "agents-os.task-producer.candidate-task.v0.1":
        errors.append("schema_version must be agents-os.task-producer.candidate-task.v0.1")
    if not re.match(r"^CANDIDATE-[A-Z0-9-]+$", str(candidate.get("candidate_id", ""))):
        errors.append("candidate_id must match ^CANDIDATE-[A-Z0-9-]+$")
    if candidate.get("producer_generated") is not True:
        errors.append("producer_generated must be true")
    if candidate.get("status") != "candidate_preview":
        errors.append("status must be candidate_preview")
    if candidate.get("proposed_lane") not in LANES:
        errors.append(f"invalid proposed_lane: {candidate.get('proposed_lane')}")
    if candidate.get("source", {}).get("raw_content_included") is not False:
        errors.append("source.raw_content_included must be false")
    if candidate.get("json_output_authoritative") is not True:
        errors.append("json_output_authoritative must be true")

    properties = schema.get("properties", {})
    for field in ("authorization", "queue_effect", "execution_effect"):
        required_false = properties.get(field, {}).get("required_false", [])
        ok, failures = has_false_flags(candidate.get(field, {}), required_false)
        if not ok:
            errors.append(f"{field} flags not false: {','.join(failures)}")

    review = candidate.get("review_gate", {})
    if review.get("requires_nobao_review") is not True:
        errors.append("review_gate.requires_nobao_review must be true")
    if review.get("review_status") != "pending":
        errors.append("review_gate.review_status must be pending")
    if review.get("execution_authorized") is not False:
        errors.append("review_gate.execution_authorized must be false")

    risk_signals = candidate.get("risk_signals", [])
    if not isinstance(risk_signals, list):
        errors.append("risk_signals must be a list")
    requires_jenn = bool(set(risk_signals) & JENN_DECISION_SIGNALS) if isinstance(risk_signals, list) else False
    if requires_jenn and review.get("requires_jenn_decision") is not True:
        errors.append("P3-like risk signals must require Jenn decision")
    if candidate.get("blocked") and candidate.get("execution_effect", {}).get("execution_authorized") is not False:
        errors.append("blocked candidate must not authorize execution")
    return errors


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("default_mode") != "preview_only_candidate_task_producer":
        errors.append("manifest default_mode must be preview_only_candidate_task_producer")
    defaults = manifest.get("dangerous_authorization_defaults", {})
    ok, failures = has_false_flags(defaults, DANGEROUS_AUTHORIZATION_FLAGS)
    if not ok:
        errors.append(f"manifest dangerous authorization defaults not false: {','.join(failures)}")
    queue_defaults = manifest.get("queue_effect_defaults", {})
    ok, failures = has_false_flags(queue_defaults, QUEUE_EFFECT_FLAGS)
    if not ok:
        errors.append(f"manifest queue effect defaults not false: {','.join(failures)}")
    execution_defaults = manifest.get("execution_effect_defaults", {})
    ok, failures = has_false_flags(execution_defaults, EXECUTION_EFFECT_FLAGS)
    if not ok:
        errors.append(f"manifest execution effect defaults not false: {','.join(failures)}")
    review = manifest.get("review_gate_defaults", {})
    if review.get("requires_nobao_review") is not True:
        errors.append("manifest review_gate_defaults.requires_nobao_review must be true")
    if review.get("execution_authorized") is not False:
        errors.append("manifest review_gate_defaults.execution_authorized must be false")
    return errors


def run_command(command: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(command, capture_output=True, text=True, check=False, env=env)
    return {
        "command": " ".join(command),
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def docctl_json(command: str) -> dict[str, Any]:
    result = run_command([sys.executable, str(DOCCTL), command, "--json"])
    payload: dict[str, Any] | None = None
    if result["stdout"].strip():
        try:
            payload = json.loads(result["stdout"])
        except json.JSONDecodeError:
            payload = None
    return {
        "command": command,
        "returncode": result["returncode"],
        "passed": result["passed"] and bool(payload.get("passed")) if isinstance(payload, dict) else False,
        "json_parsed": payload is not None,
    }


def validate_producer(run_docctl: bool = True) -> dict[str, Any]:
    manifest = load_json(MANIFEST_PATH)
    schema = load_json(SCHEMA_PATH)
    errors: list[str] = []
    errors.extend(validate_manifest(manifest))

    intent_candidate = candidate_from_intent("Build a local governance task from explicit intent.")
    errors.extend(f"intent candidate: {error}" for error in validate_candidate(intent_candidate, schema))

    risky_candidate = candidate_from_intent("Call provider, start service, and write to Notion.")
    errors.extend(f"risky candidate: {error}" for error in validate_candidate(risky_candidate, schema))
    if risky_candidate["review_gate"]["requires_jenn_decision"] is not True:
        errors.append("risky candidate should require Jenn decision")

    review_candidate = candidate_from_review_source(DEFAULT_REVIEW_SOURCE)
    if review_candidate.get("schema_version") == "agents-os.task-producer.source-preflight.v0.1":
        errors.append("default review source preflight failed")
    else:
        errors.extend(f"review candidate: {error}" for error in validate_candidate(review_candidate, schema))

    route_candidates: dict[str, dict[str, Any]] = {}
    for option_id in ROUTE_OPTIONS:
        route_candidate = candidate_from_route_option(option_id)
        route_candidates[option_id] = route_candidate
        if route_candidate.get("schema_version") != "agents-os.task-producer.candidate-task.v0.1":
            errors.append(f"route option {option_id} preflight failed")
            continue
        errors.extend(f"route option {option_id}: {error}" for error in validate_candidate(route_candidate, schema))
        if route_candidate.get("source_facts", {}).get("route_selected") is not False:
            errors.append(f"route option {option_id} must not mark route_selected true")
        if route_candidate.get("authorization", {}).get("route_auto_selection_authorized") is not False:
            errors.append(f"route option {option_id} must not authorize route auto-selection")

    protected_result = candidate_from_review_source(Path("state-private/task.md"))
    if protected_result.get("passed") is not False or not protected_result.get("findings"):
        errors.append("protected source path should fail before read")

    disallowed_result = candidate_from_review_source(Path("AGENTS.md"))
    if disallowed_result.get("passed") is not False or not disallowed_result.get("findings"):
        errors.append("non-allowlisted source path should fail")

    docctl: dict[str, Any] = {}
    if run_docctl:
        status = docctl_json("status")
        doctor = docctl_json("doctor")
        docctl = {"status": status, "doctor": doctor}
        if not status["passed"]:
            errors.append("docctl status failed")
        if not doctor["passed"]:
            errors.append("docctl doctor failed")

    return {
        "schema_version": "agents-os.task-producer.validation.v0.1",
        "passed": not errors,
        "errors": errors,
        "manifest_path": rel(MANIFEST_PATH),
        "schema_path": rel(SCHEMA_PATH),
        "intent_candidate": {
            "present": True,
            "blocked": intent_candidate["blocked"],
            "requires_nobao_review": intent_candidate["review_gate"]["requires_nobao_review"],
            "execution_authorized": intent_candidate["execution_effect"]["execution_authorized"],
        },
        "risky_candidate": {
            "present": True,
            "blocked": risky_candidate["blocked"],
            "risk_signals": risky_candidate["risk_signals"],
            "requires_jenn_decision": risky_candidate["review_gate"]["requires_jenn_decision"],
            "execution_authorized": risky_candidate["execution_effect"]["execution_authorized"],
        },
        "review_candidate": {
            "present": review_candidate.get("schema_version") == "agents-os.task-producer.candidate-task.v0.1",
            "source_path": review_candidate.get("source", {}).get("path"),
            "raw_content_included": review_candidate.get("source", {}).get("raw_content_included"),
        },
        "route_option_candidates": {
            option_id: {
                "present": candidate.get("schema_version") == "agents-os.task-producer.candidate-task.v0.1",
                "title": candidate.get("title"),
                "blocked": candidate.get("blocked"),
                "requires_jenn_decision": candidate.get("review_gate", {}).get("requires_jenn_decision"),
                "route_selected": candidate.get("source_facts", {}).get("route_selected"),
                "route_auto_selection_authorized": candidate.get("authorization", {}).get("route_auto_selection_authorized"),
                "queue_write_authorized": candidate.get("authorization", {}).get("queue_write_authorized"),
                "execution_authorized": candidate.get("execution_effect", {}).get("execution_authorized"),
            }
            for option_id, candidate in route_candidates.items()
        },
        "protected_source_preflight_failed": protected_result.get("passed") is False,
        "disallowed_source_preflight_failed": disallowed_result.get("passed") is False,
        "docctl": docctl,
    }


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def print_validation_text(result: dict[str, Any]) -> None:
    print("AGENTS OS Task Producer Skeleton validation")
    print(f"Status: {'PASS' if result['passed'] else 'FAIL'}")
    print(f"Intent candidate blocked: {result['intent_candidate']['blocked']}")
    print(f"Risky candidate blocked: {result['risky_candidate']['blocked']}")
    print(f"Review candidate source: {result['review_candidate']['source_path']}")
    route_candidates = result.get("route_option_candidates", {})
    if route_candidates:
        print(f"Route option candidates: {len(route_candidates)}")
    if result.get("docctl"):
        print(f"Docctl status: {'PASS' if result['docctl']['status']['passed'] else 'FAIL'}")
        print(f"Docctl doctor: {'PASS' if result['docctl']['doctor']['passed'] else 'FAIL'}")
    if result["errors"]:
        print("")
        print("Errors:")
        for error in result["errors"]:
            print(f"- {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENTS OS preview-only task producer skeleton.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    intent_parser = subparsers.add_parser("from-intent", help="Create candidate task JSON from explicit intent text.")
    intent_parser.add_argument("--intent", required=True, help="Explicit local task intent text.")
    intent_parser.add_argument("--lane", choices=LANES, default="NEXT", help="Proposed lane for the candidate.")
    intent_parser.add_argument("--candidate-id", default=None, help="Optional candidate id.")
    intent_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    review_parser = subparsers.add_parser("from-review", help="Create candidate task JSON from an allowlisted review/report.")
    review_parser.add_argument("--source", required=True, help="Allowlisted Markdown review/report path.")
    review_parser.add_argument("--lane", choices=LANES, default="NEXT", help="Proposed lane for the candidate.")
    review_parser.add_argument("--candidate-id", default=None, help="Optional candidate id.")
    review_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    route_parser = subparsers.add_parser("from-route-option", help="Create candidate task JSON from a Jenn-selectable route option.")
    route_parser.add_argument("--option", choices=ROUTE_OPTIONS, required=True, help="Route option id.")
    route_parser.add_argument("--source", default=str(DEFAULT_ROUTE_SELECTION_PACKAGE), help="Route selection package Markdown path.")
    route_parser.add_argument("--lane", choices=LANES, default="NEXT", help="Proposed lane for the candidate.")
    route_parser.add_argument("--candidate-id", default=None, help="Optional candidate id.")
    route_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    validate_parser = subparsers.add_parser("validate", help="Run producer self-validation.")
    validate_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    args = parser.parse_args()

    if args.command == "from-intent":
        candidate = candidate_from_intent(args.intent, args.lane, args.candidate_id)
        errors = validate_candidate(candidate)
        candidate["passed"] = not errors
        candidate["errors"] = errors
        if args.json:
            print_json(candidate)
        else:
            print(f"Candidate: {candidate['candidate_id']} {candidate['title']}")
            print(f"Status: {'PASS' if candidate['passed'] else 'FAIL'}")
            print(f"Proposed lane: {candidate['proposed_lane']}")
            print(f"Requires Nobao review: {candidate['review_gate']['requires_nobao_review']}")
            print(f"Execution authorized: {candidate['execution_effect']['execution_authorized']}")
        return 0 if candidate["passed"] else 1

    if args.command == "from-review":
        candidate = candidate_from_review_source(Path(args.source), args.lane, args.candidate_id)
        if candidate.get("schema_version") == "agents-os.task-producer.source-preflight.v0.1":
            if args.json:
                print_json(candidate)
            else:
                print("Status: FAIL")
                for item in candidate.get("findings", []):
                    print(f"- {item['message']}")
            return 1
        errors = validate_candidate(candidate)
        candidate["passed"] = not errors
        candidate["errors"] = errors
        if args.json:
            print_json(candidate)
        else:
            print(f"Candidate: {candidate['candidate_id']} {candidate['title']}")
            print(f"Status: {'PASS' if candidate['passed'] else 'FAIL'}")
            print(f"Source: {candidate['source']['path']}")
            print(f"Requires Nobao review: {candidate['review_gate']['requires_nobao_review']}")
            print(f"Execution authorized: {candidate['execution_effect']['execution_authorized']}")
        return 0 if candidate["passed"] else 1

    if args.command == "from-route-option":
        candidate = candidate_from_route_option(args.option, Path(args.source), args.lane, args.candidate_id)
        if candidate.get("schema_version") == "agents-os.task-producer.route-option-preflight.v0.1":
            if args.json:
                print_json(candidate)
            else:
                print("Status: FAIL")
                for item in candidate.get("findings", []):
                    print(f"- {item['message']}")
            return 1
        errors = validate_candidate(candidate)
        candidate["passed"] = not errors
        candidate["errors"] = errors
        if args.json:
            print_json(candidate)
        else:
            print(f"Candidate: {candidate['candidate_id']} {candidate['title']}")
            print(f"Status: {'PASS' if candidate['passed'] else 'FAIL'}")
            print(f"Route selected: {candidate['source_facts']['route_selected']}")
            print(f"Queue write authorized: {candidate['authorization']['queue_write_authorized']}")
            print(f"Execution authorized: {candidate['execution_effect']['execution_authorized']}")
        return 0 if candidate["passed"] else 1

    if args.command == "validate":
        result = validate_producer()
        if args.json:
            print_json(result)
        else:
            print_validation_text(result)
        return 0 if result["passed"] else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
