#!/usr/bin/env python3
"""Read-only document governance helper.

`docctl doctor` checks the local Document Registry federation. It reports
missing registrations, broken references, count drift, validator failures, and
protected path mistakes. It does not modify files or execute arbitrary registry
commands.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

REGISTRY_DIR = Path(__file__).resolve().parent
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from path_boundary import is_protected_path, is_under_workspace, safe_resolve


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FEDERATED_REGISTRY = REGISTRY_DIR / "drafts" / "federated-document-registry.v0.1.example.yaml"
DEFAULT_TREND_SNAPSHOT_DIR = REGISTRY_DIR / "reports" / "docctl-snapshots"
DOCUMENT_VALIDATOR = REGISTRY_DIR / "validate-document-registry.py"
FEDERATED_VALIDATOR = REGISTRY_DIR / "validate-federated-document-registry.py"

SOURCE_SUFFIXES = {".md", ".markdown", ".yaml", ".yml", ".json", ".py"}
SKIP_DIRS = {
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "cache",
    "dist",
    "node_modules",
    "venv",
}
PATH_TOKEN_PATTERN = re.compile(r"`([^`]+)`")

IGNORED_SUFFIXES = {".pyc", ".pyo", ".log", ".sqlite", ".db", ".tmp", ".cache"}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - depends on local environment.
        raise RuntimeError(f"YAML parser unavailable: {exc}") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def add_finding(
    findings: list[dict[str, str]],
    rule_id: str,
    level: str,
    owner: str,
    message: str,
) -> None:
    findings.append(
        {
            "rule_id": rule_id,
            "level": level,
            "owner": owner,
            "message": message,
        }
    )


def workspace_display(path: Path) -> str:
    try:
        return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_workspace_path(path_value: Any) -> tuple[Path | None, str | None]:
    if not has_value(path_value):
        return None, None
    path = Path(str(path_value))
    if path.is_absolute():
        return safe_resolve(path)
    return safe_resolve(WORKSPACE_ROOT / path)


def normalized_registry_path(path_value: Any) -> str | None:
    resolved, resolve_error = resolve_workspace_path(path_value)
    if resolve_error or resolved is None:
        return None
    if not is_under_workspace(resolved, WORKSPACE_ROOT):
        return None
    return workspace_display(resolved)


def iter_path_values(value: Any) -> list[str]:
    if not has_value(value):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if has_value(item)]
    return []


def check_path_value(
    findings: list[dict[str, str]],
    owner: str,
    field: str,
    path_value: Any,
    *,
    required: bool = False,
    receipt_review_only: bool = False,
) -> Path | None:
    if not has_value(path_value):
        if required:
            add_finding(findings, "DOCCTL-MISSING-PATH", "fail", owner, f"{field} is missing")
        return None

    if is_protected_path(path_value):
        add_finding(
            findings,
            "DOCCTL-PROTECTED",
            "fail",
            owner,
            f"{field} points to protected path: {path_value}",
        )
        return None

    resolved, resolve_error = resolve_workspace_path(path_value)
    if resolve_error:
        add_finding(
            findings,
            "DOCCTL-PATH-RESOLVE",
            "fail",
            owner,
            f"{field} could not be resolved: {resolve_error}",
        )
        return None
    if resolved is None:
        return None

    if is_protected_path(resolved):
        add_finding(
            findings,
            "DOCCTL-PROTECTED",
            "fail",
            owner,
            f"{field} resolves to protected path: {path_value}",
        )
        return None

    if not is_under_workspace(resolved, WORKSPACE_ROOT):
        add_finding(
            findings,
            "DOCCTL-OUTSIDE",
            "fail",
            owner,
            f"{field} points outside workspace: {path_value}",
        )
        return None

    if not resolved.exists():
        rule_id = "DOCCTL-MISSING-RECEIPT-REVIEW" if receipt_review_only else "DOCCTL-MISSING-FILE"
        add_finding(findings, rule_id, "fail", owner, f"{field} does not exist: {path_value}")
        return None

    return resolved


def is_receipt_or_review_path(path_value: str) -> bool:
    text = path_value.replace("\\", "/")
    return "/receipts/" in text or "/reviews/" in text


def run_validator(script: Path, target: Path) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, str(script), str(target), "--json"]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    payload: dict[str, Any]
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {}
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "passed": bool(payload.get("passed")) and completed.returncode == 0,
        "summary": payload.get("summary", {}),
        "json_parsed": bool(payload),
        "stderr": completed.stderr.strip(),
    }


def scan_source_files(directory_root: Path) -> set[str]:
    files: set[str] = set()
    if not directory_root.exists() or not directory_root.is_dir():
        return files

    for current_root, dirnames, filenames in os.walk(directory_root):
        current_path = Path(current_root)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in SKIP_DIRS
            and not dirname.startswith(".tmp-")
            and not is_protected_path(current_path / dirname)
        ]

        if is_protected_path(current_path):
            continue

        for filename in filenames:
            if filename.startswith(".tmp-"):
                continue
            path = current_path / filename
            if path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            if is_protected_path(path):
                continue
            files.add(workspace_display(path))
    return files


def registered_source_paths(documents: list[Any]) -> set[str]:
    paths: set[str] = set()
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        for field in ("canonical_path", "source_of_truth"):
            normalized = normalized_registry_path(doc.get(field))
            if normalized:
                paths.add(normalized)
    return paths


def known_external_scope_paths(
    findings: list[dict[str, str]],
    registry_id: str,
    directory_root: Path,
    known_external_scope: Any,
) -> set[str]:
    paths: set[str] = set()
    if not has_value(known_external_scope):
        return paths

    entries = known_external_scope if isinstance(known_external_scope, list) else [known_external_scope]
    for index, entry in enumerate(entries):
        owner = f"{registry_id}:known_external_scope[{index}]"
        path_value = entry.get("path") if isinstance(entry, dict) else entry
        resolved = check_path_value(
            findings,
            owner,
            "known_external_scope.path",
            path_value,
            required=True,
        )
        if resolved is None:
            continue

        try:
            resolved.relative_to(directory_root)
        except ValueError:
            add_finding(
                findings,
                "DOCCTL-KNOWN-SCOPE",
                "fail",
                owner,
                f"known_external_scope path is outside directory_root: {path_value}",
            )
            continue

        paths.add(workspace_display(resolved))

    return paths


def extract_archive_note_path_values(text: str) -> list[str]:
    values: list[str] = []
    for token in PATH_TOKEN_PATTERN.findall(text):
        if "/" not in token:
            continue
        if Path(token).suffix.lower() not in SOURCE_SUFFIXES:
            continue
        values.append(token)
    return values


def archived_paths_from_notes(
    findings: list[dict[str, str]],
    registry_id: str,
    archive_notes: Any,
) -> set[str]:
    paths: set[str] = set()
    if not has_value(archive_notes):
        return paths

    entries = archive_notes if isinstance(archive_notes, list) else [archive_notes]
    for index, entry in enumerate(entries):
        owner = f"{registry_id}:archive_notes[{index}]"
        note_path_value = entry.get("path") if isinstance(entry, dict) else entry
        note_path = check_path_value(
            findings,
            owner,
            "archive_notes.path",
            note_path_value,
            required=True,
        )
        if note_path is None:
            continue

        try:
            note_text = note_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            add_finding(
                findings,
                "DOCCTL-ARCHIVE-NOTE",
                "fail",
                owner,
                f"archive note could not be read: {note_path_value}: {exc}",
            )
            continue

        for path_value in extract_archive_note_path_values(note_text):
            archived_path = check_path_value(
                findings,
                owner,
                "archive_note.archived_file",
                path_value,
                required=True,
            )
            if archived_path is None or archived_path == note_path:
                continue
            paths.add(workspace_display(archived_path))

    return paths


def check_document_registry(
    findings: list[dict[str, str]],
    registry_id: str,
    registry_path: Path,
    directory_root: Path,
    expected_document_count: Any,
    validator_run: dict[str, Any],
    known_external_scope: Any = None,
    archive_notes: Any = None,
) -> dict[str, Any]:
    result = {
        "registry_id": registry_id,
        "registry_path": workspace_display(registry_path),
        "documents": 0,
        "scanned_files": 0,
        "unregistered_files": 0,
        "known_external_scope_files": 0,
        "archived_files": 0,
        "validator": validator_run,
    }

    try:
        data = load_yaml(registry_path)
    except Exception as exc:
        add_finding(findings, "DOCCTL-REGISTRY-LOAD", "fail", registry_id, f"registry could not be loaded: {exc}")
        return result

    documents = data.get("documents")
    if not isinstance(documents, list):
        add_finding(findings, "DOCCTL-REGISTRY-SHAPE", "fail", registry_id, "documents root is not a list")
        return result

    result["documents"] = len(documents)

    try:
        expected_count = int(expected_document_count)
    except (TypeError, ValueError):
        add_finding(
            findings,
            "DOCCTL-COUNT",
            "fail",
            registry_id,
            f"expected_document_count is not an integer: {expected_document_count}",
        )
        expected_count = None

    actual_count = validator_run.get("summary", {}).get("checked_documents", len(documents))
    try:
        actual_count_int = int(actual_count)
    except (TypeError, ValueError):
        actual_count_int = len(documents)

    if expected_count is not None and expected_count != actual_count_int:
        add_finding(
            findings,
            "DOCCTL-COUNT",
            "fail",
            registry_id,
            f"expected_document_count mismatch: expected {expected_count} got {actual_count_int}",
        )

    registered_paths = registered_source_paths(documents)
    for index, doc in enumerate(documents):
        if not isinstance(doc, dict):
            add_finding(findings, "DOCCTL-DOCUMENT-SHAPE", "fail", registry_id, f"document[{index}] is not a mapping")
            continue
        owner = str(doc.get("id") or f"{registry_id}:document[{index}]")
        check_path_value(findings, owner, "canonical_path", doc.get("canonical_path"), required=True)
        check_path_value(findings, owner, "source_of_truth", doc.get("source_of_truth"), required=True)
        check_path_value(
            findings,
            owner,
            "review_by",
            doc.get("review_by"),
            receipt_review_only=True,
        )
        for field in ("supersedes", "superseded_by", "related"):
            for path_value in iter_path_values(doc.get(field)):
                check_path_value(
                    findings,
                    owner,
                    field,
                    path_value,
                    receipt_review_only=is_receipt_or_review_path(path_value),
                )

    scanned_files = scan_source_files(directory_root)
    result["scanned_files"] = len(scanned_files)
    known_paths = known_external_scope_paths(
        findings,
        registry_id,
        directory_root,
        known_external_scope,
    )
    known_scoped = sorted((scanned_files - registered_paths) & known_paths)
    result["known_external_scope_files"] = len(known_scoped)
    for path in known_scoped:
        add_finding(
            findings,
            "DOCCTL-KNOWN-EXTERNAL-SCOPE",
            "info",
            registry_id,
            f"source file is known external scope: {path}",
        )

    archive_paths = archived_paths_from_notes(
        findings,
        registry_id,
        archive_notes,
    )
    archived_scoped = sorted((scanned_files - registered_paths - known_paths) & archive_paths)
    result["archived_files"] = len(archived_scoped)
    if archived_scoped:
        add_finding(
            findings,
            "DOCCTL-ARCHIVED",
            "info",
            registry_id,
            f"archive notes cover {len(archived_scoped)} historical files",
        )

    unregistered = sorted(scanned_files - registered_paths - known_paths - archive_paths)
    result["unregistered_files"] = len(unregistered)
    for path in unregistered:
        add_finding(
            findings,
            "DOCCTL-UNREGISTERED",
            "warn",
            registry_id,
            f"source file is not registered: {path}",
        )

    return result


def doctor(federated_registry: Path = DEFAULT_FEDERATED_REGISTRY) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    registry_results: list[dict[str, Any]] = []

    federated_path = check_path_value(
        findings,
        "federated-document-registry",
        "target",
        federated_registry,
        required=True,
    )
    if federated_path is None:
        return build_result(federated_registry, findings, registry_results, {})

    federated_validator = run_validator(FEDERATED_VALIDATOR, federated_path)
    if not federated_validator["passed"]:
        add_finding(
            findings,
            "DOCCTL-VALIDATOR",
            "fail",
            "federated-document-registry",
            "federated validator failed or did not emit passing JSON",
        )

    try:
        federation = load_yaml(federated_path)
    except Exception as exc:
        add_finding(findings, "DOCCTL-FEDERATION-LOAD", "fail", "federated-document-registry", str(exc))
        return build_result(federated_path, findings, registry_results, federated_validator)

    registries = federation.get("registries")
    if not isinstance(registries, list):
        add_finding(findings, "DOCCTL-FEDERATION-SHAPE", "fail", "federated-document-registry", "registries root is not a list")
        return build_result(federated_path, findings, registry_results, federated_validator)

    for index, entry in enumerate(registries):
        if not isinstance(entry, dict):
            add_finding(findings, "DOCCTL-FEDERATION-SHAPE", "fail", f"registry[{index}]", "registry entry is not a mapping")
            continue

        registry_id = str(entry.get("id") or f"registry[{index}]")
        registry_path = check_path_value(findings, registry_id, "registry_path", entry.get("registry_path"), required=True)
        directory_root = check_path_value(findings, registry_id, "directory_root", entry.get("directory_root"), required=True)
        check_path_value(findings, registry_id, "validator", entry.get("validator"), required=True)
        check_path_value(findings, registry_id, "coverage_checker", entry.get("coverage_checker"))
        check_path_value(
            findings,
            registry_id,
            "last_receipt",
            entry.get("last_receipt"),
            receipt_review_only=True,
        )
        check_path_value(
            findings,
            registry_id,
            "last_review",
            entry.get("last_review"),
            receipt_review_only=True,
        )

        if registry_path is None or directory_root is None:
            continue

        document_validator = run_validator(DOCUMENT_VALIDATOR, registry_path)
        if not document_validator["passed"]:
            add_finding(
                findings,
                "DOCCTL-VALIDATOR",
                "fail",
                registry_id,
                "document registry validator failed or did not emit passing JSON",
            )

        registry_results.append(
            check_document_registry(
                findings,
                registry_id,
                registry_path,
                directory_root,
                entry.get("expected_document_count"),
                document_validator,
                entry.get("known_external_scope"),
                entry.get("archive_notes"),
            )
        )

    return build_result(federated_path, findings, registry_results, federated_validator)


def intake_finding(rule_id: str, level: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "level": level, "message": message}


def resolve_intake_target(target: Path) -> tuple[Path | None, list[dict[str, str]], bool]:
    findings: list[dict[str, str]] = []

    if is_protected_path(target):
        findings.append(intake_finding("DOCCTL-INTAKE-BLOCKED", "fail", f"target points to protected path: {target}"))
        return None, findings, False

    candidate = target if target.is_absolute() else WORKSPACE_ROOT / target
    resolved, resolve_error = safe_resolve(candidate)
    if resolve_error:
        findings.append(intake_finding("DOCCTL-INTAKE-BLOCKED", "fail", f"target could not be resolved: {resolve_error}"))
        return None, findings, False
    if resolved is None:
        findings.append(intake_finding("DOCCTL-INTAKE-BLOCKED", "fail", f"target could not be resolved: {target}"))
        return None, findings, False

    if is_protected_path(resolved):
        findings.append(intake_finding("DOCCTL-INTAKE-BLOCKED", "fail", f"target resolves to protected path: {target}"))
        return None, findings, False
    if not is_under_workspace(resolved, WORKSPACE_ROOT):
        findings.append(intake_finding("DOCCTL-INTAKE-BLOCKED", "fail", f"target points outside workspace: {target}"))
        return None, findings, False
    if not resolved.exists():
        findings.append(intake_finding("DOCCTL-INTAKE-BLOCKED", "fail", f"target does not exist: {target}"))
        return None, findings, False
    if not resolved.is_file():
        findings.append(intake_finding("DOCCTL-INTAKE-BLOCKED", "fail", f"target is not a file: {target}"))
        return None, findings, False

    return resolved, findings, False


def collect_intake_context(federated_registry: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    context: dict[str, Any] = {
        "registered_paths": set(),
        "known_external_scope_paths": set(),
        "archive_note_paths": set(),
        "directory_roots": [],
    }

    federated_path = check_path_value(
        [],
        "federated-document-registry",
        "target",
        federated_registry,
        required=True,
    )
    if federated_path is None:
        findings.append(intake_finding("DOCCTL-INTAKE-CONTEXT", "fail", "federated registry could not be loaded"))
        return context

    try:
        federation = load_yaml(federated_path)
    except Exception as exc:
        findings.append(intake_finding("DOCCTL-INTAKE-CONTEXT", "fail", f"federated registry could not be loaded: {exc}"))
        return context

    registries = federation.get("registries")
    if not isinstance(registries, list):
        findings.append(intake_finding("DOCCTL-INTAKE-CONTEXT", "fail", "federated registry registries root is not a list"))
        return context

    for entry in registries:
        if not isinstance(entry, dict):
            continue

        directory_root_value = entry.get("directory_root")
        directory_root_resolved, directory_root_error = resolve_workspace_path(directory_root_value)
        if directory_root_error or directory_root_resolved is None:
            continue
        if is_under_workspace(directory_root_resolved, WORKSPACE_ROOT):
            context["directory_roots"].append(directory_root_resolved)

        registry_path_resolved, registry_path_error = resolve_workspace_path(entry.get("registry_path"))
        if registry_path_error or registry_path_resolved is None or is_protected_path(registry_path_resolved):
            continue
        if not is_under_workspace(registry_path_resolved, WORKSPACE_ROOT) or not registry_path_resolved.exists():
            continue

        try:
            registry_data = load_yaml(registry_path_resolved)
        except Exception:
            continue
        documents = registry_data.get("documents")
        if isinstance(documents, list):
            context["registered_paths"].update(registered_source_paths(documents))

        known_entries = entry.get("known_external_scope")
        if has_value(known_entries):
            entries = known_entries if isinstance(known_entries, list) else [known_entries]
            for known_entry in entries:
                path_value = known_entry.get("path") if isinstance(known_entry, dict) else known_entry
                normalized = normalized_registry_path(path_value)
                if normalized:
                    context["known_external_scope_paths"].add(normalized)

        archive_entries = entry.get("archive_notes")
        if has_value(archive_entries):
            entries = archive_entries if isinstance(archive_entries, list) else [archive_entries]
            for archive_entry in entries:
                path_value = archive_entry.get("path") if isinstance(archive_entry, dict) else archive_entry
                normalized = normalized_registry_path(path_value)
                if normalized:
                    context["archive_note_paths"].add(normalized)

    return context


def is_under_any(path: Path, roots: list[Path]) -> bool:
    return any(is_under_workspace(path, root) for root in roots)


def classify_intake_target(resolved: Path, context: dict[str, Any]) -> dict[str, Any]:
    relative_path = workspace_display(resolved)
    suffix = resolved.suffix.lower()

    if relative_path in context["registered_paths"]:
        return {
            "classification": "registered_current",
            "reason": "target already appears as a registered canonical/source path",
            "expected_intake_route": "no registry write needed",
        }
    if relative_path in context["known_external_scope_paths"]:
        return {
            "classification": "known_external_scope",
            "reason": "target is already declared as known external scope",
            "expected_intake_route": "review existing federation entry if this changes",
        }
    if relative_path in context["archive_note_paths"] or "/archive-notes/" in relative_path:
        return {
            "classification": "archive_note",
            "reason": "target is an archive note or an existing archive-note path",
            "expected_intake_route": "ensure archive note explains why archived, replacement, safe use, and review trigger",
        }
    if suffix in IGNORED_SUFFIXES or suffix not in SOURCE_SUFFIXES:
        return {
            "classification": "ignored_by_rule",
            "reason": f"unsupported or generated-file suffix: {suffix or '<none>'}",
            "rule": "docctl.intake.source_suffix",
            "review_trigger": "source suffix allowlist changes",
            "expected_intake_route": "do not register unless the suffix becomes governed source",
        }
    if "/receipts/" in relative_path or "/reviews/" in relative_path:
        return {
            "classification": "register",
            "reason": "target is governance evidence under a declared registry root",
            "expected_intake_route": "register as receipt or review in the directory-owned Document Registry",
        }
    if "/templates/" in relative_path:
        return {
            "classification": "template",
            "reason": "target is a template under a declared registry root",
            "expected_intake_route": "register as doc_type=template with active/draft boundary language",
        }
    if "/examples/" in relative_path:
        return {
            "classification": "example",
            "reason": "target is an example under a declared registry root",
            "expected_intake_route": "register as doc_type=example or equivalent non-authority record",
        }
    if "/drafts/" in relative_path:
        return {
            "classification": "draft",
            "reason": "target is a draft under a declared registry root",
            "expected_intake_route": "register as status=draft or status=example depending on authority",
        }
    if is_under_any(resolved, context["directory_roots"]):
        return {
            "classification": "register",
            "reason": "target is an unregistered governed source file under a declared registry root",
            "expected_intake_route": "register in the directory-owned Document Registry",
        }
    return {
        "classification": "future_backlog",
        "reason": "target is safe local source but outside the declared Federated Document Registry roots",
        "owner": "Jenn / Nobao",
        "review_trigger": "scope expansion or new directory-owned registry",
        "expected_intake_route": "create or select a directory-owned registry before registration",
    }


def intake(target: Path, federated_registry: Path = DEFAULT_FEDERATED_REGISTRY) -> dict[str, Any]:
    resolved, findings, target_read_performed = resolve_intake_target(target)
    if resolved is None:
        return {
            "schema_version": "agents-os.docctl.intake.result.v0.1",
            "passed": False,
            "target": str(target),
            "resolved_target": None,
            "classification": "blocked",
            "dry_run": True,
            "would_write": False,
            "findings": findings,
            "recommendation": "blocked before content reading",
            "warnings": {
                "intake_is_dry_run": True,
                "target_read_performed": target_read_performed,
                "registry_write_performed": False,
                "external_write_performed": False,
                "provider_call_performed": False,
            },
        }

    context = collect_intake_context(federated_registry, findings)
    route = classify_intake_target(resolved, context)
    passed = not any(finding["level"] == "fail" for finding in findings)
    return {
        "schema_version": "agents-os.docctl.intake.result.v0.1",
        "passed": passed,
        "target": str(target),
        "resolved_target": workspace_display(resolved),
        "classification": route["classification"],
        "dry_run": True,
        "would_write": False,
        "reason": route["reason"],
        "expected_intake_route": route["expected_intake_route"],
        "rule": route.get("rule"),
        "owner": route.get("owner"),
        "review_trigger": route.get("review_trigger"),
        "findings": findings,
        "recommendation": "review the dry-run route before making any registry change",
        "warnings": {
            "intake_is_dry_run": True,
            "target_read_performed": target_read_performed,
            "registry_write_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
        },
    }


def format_intake_text(result: dict[str, Any]) -> str:
    lines = [
        f"docctl intake: {result['target']}",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Classification: {result['classification']}",
        f"Dry run: {result['dry_run']}",
        f"Would write: {result['would_write']}",
    ]
    if result.get("resolved_target"):
        lines.append(f"Resolved target: {result['resolved_target']}")
    if result.get("reason"):
        lines.append(f"Reason: {result['reason']}")
    if result.get("expected_intake_route"):
        lines.append(f"Expected route: {result['expected_intake_route']}")
    if result.get("review_trigger"):
        lines.append(f"Review trigger: {result['review_trigger']}")
    if result.get("findings"):
        lines.append("")
        lines.append("Findings:")
        for finding in result["findings"]:
            lines.append(f"- {finding['level'].upper()} {finding['rule_id']}: {finding['message']}")
    return "\n".join(lines)


def resolve_impact_target(target: Path) -> tuple[str | None, dict[str, str] | None]:
    if is_protected_path(target):
        return None, {
            "rule_id": "DOCCTL-IMPACT-BLOCKED",
            "level": "fail",
            "message": f"target points to protected path: {target}",
        }

    candidate = target if target.is_absolute() else WORKSPACE_ROOT / target
    resolved, resolve_error = safe_resolve(candidate)
    if resolve_error:
        return None, {
            "rule_id": "DOCCTL-IMPACT-BLOCKED",
            "level": "fail",
            "message": f"target could not be resolved: {resolve_error}",
        }
    if resolved is None:
        return None, {
            "rule_id": "DOCCTL-IMPACT-BLOCKED",
            "level": "fail",
            "message": f"target could not be resolved: {target}",
        }
    if is_protected_path(resolved):
        return None, {
            "rule_id": "DOCCTL-IMPACT-BLOCKED",
            "level": "fail",
            "message": f"target resolves to protected path: {target}",
        }
    if not is_under_workspace(resolved, WORKSPACE_ROOT):
        return None, {
            "rule_id": "DOCCTL-IMPACT-BLOCKED",
            "level": "fail",
            "message": f"target points outside workspace: {target}",
        }
    return workspace_display(resolved), None


def collect_impact_context(federated_registry: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    context: dict[str, Any] = {"documents": [], "registries": []}
    federated_path = check_path_value(
        [],
        "federated-document-registry",
        "target",
        federated_registry,
        required=True,
    )
    if federated_path is None:
        findings.append(intake_finding("DOCCTL-IMPACT-CONTEXT", "fail", "federated registry could not be loaded"))
        return context

    try:
        federation = load_yaml(federated_path)
    except Exception as exc:
        findings.append(intake_finding("DOCCTL-IMPACT-CONTEXT", "fail", f"federated registry could not be loaded: {exc}"))
        return context

    registries = federation.get("registries")
    if not isinstance(registries, list):
        findings.append(intake_finding("DOCCTL-IMPACT-CONTEXT", "fail", "federated registry registries root is not a list"))
        return context

    for entry in registries:
        if not isinstance(entry, dict):
            continue
        registry_id = str(entry.get("id") or "")
        registry_path_normalized = normalized_registry_path(entry.get("registry_path"))
        if registry_path_normalized:
            context["registries"].append(
                {
                    "id": registry_id,
                    "registry_path": registry_path_normalized,
                }
            )

        registry_path_resolved, registry_path_error = resolve_workspace_path(entry.get("registry_path"))
        if registry_path_error or registry_path_resolved is None or not registry_path_resolved.exists():
            continue
        if is_protected_path(registry_path_resolved) or not is_under_workspace(registry_path_resolved, WORKSPACE_ROOT):
            continue

        try:
            registry_data = load_yaml(registry_path_resolved)
        except Exception:
            continue
        documents = registry_data.get("documents")
        if not isinstance(documents, list):
            continue

        for doc in documents:
            if not isinstance(doc, dict):
                continue
            paths: set[str] = set()
            for field in ("canonical_path", "source_of_truth", "review_by"):
                normalized = normalized_registry_path(doc.get(field))
                if normalized:
                    paths.add(normalized)
            for field in ("supersedes", "superseded_by", "related"):
                for path_value in iter_path_values(doc.get(field)):
                    normalized = normalized_registry_path(path_value)
                    if normalized:
                        paths.add(normalized)
            context["documents"].append(
                {
                    "id": str(doc.get("id") or ""),
                    "title": str(doc.get("title") or ""),
                    "status": str(doc.get("status") or ""),
                    "doc_type": str(doc.get("doc_type") or ""),
                    "registry_id": registry_id,
                    "paths": sorted(paths),
                }
            )
    return context


def impact(targets: list[Path], federated_registry: Path = DEFAULT_FEDERATED_REGISTRY) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    context = collect_impact_context(federated_registry, findings)
    target_results: list[dict[str, Any]] = []

    for target in targets:
        normalized, finding = resolve_impact_target(target)
        if finding is not None:
            target_results.append(
                {
                    "target": str(target),
                    "resolved_target": None,
                    "blocked": True,
                    "affected_documents": [],
                    "affected_registries": [],
                }
            )
            findings.append(finding)
            continue

        affected_documents = [
            {
                "id": doc["id"],
                "title": doc["title"],
                "status": doc["status"],
                "doc_type": doc["doc_type"],
                "registry_id": doc["registry_id"],
            }
            for doc in context["documents"]
            if normalized in doc["paths"]
        ]
        affected_registries = [
            registry
            for registry in context["registries"]
            if normalized == registry["registry_path"]
        ]
        target_results.append(
            {
                "target": str(target),
                "resolved_target": normalized,
                "blocked": False,
                "affected_documents": affected_documents,
                "affected_registries": affected_registries,
            }
        )

    return {
        "schema_version": "agents-os.docctl.impact.result.v0.1",
        "passed": not any(finding["level"] == "fail" for finding in findings),
        "dry_run": True,
        "would_write": False,
        "targets": target_results,
        "findings": findings,
        "warnings": {
            "impact_is_read_only": True,
            "target_content_read_performed": False,
            "registry_write_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
        },
    }


def format_impact_text(result: dict[str, Any]) -> str:
    lines = [
        "docctl impact",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Dry run: {result['dry_run']}",
        f"Would write: {result['would_write']}",
    ]
    for item in result["targets"]:
        lines.append("")
        lines.append(f"Target: {item['target']}")
        if item.get("resolved_target"):
            lines.append(f"Resolved target: {item['resolved_target']}")
        lines.append(f"Blocked: {item['blocked']}")
        lines.append(f"Affected documents: {len(item['affected_documents'])}")
        for doc in item["affected_documents"]:
            lines.append(f"- {doc['id']} ({doc['status']}, {doc['doc_type']}, {doc['registry_id']})")
        lines.append(f"Affected registries: {len(item['affected_registries'])}")
        for registry in item["affected_registries"]:
            lines.append(f"- {registry['id']}")
    if result.get("findings"):
        lines.append("")
        lines.append("Findings:")
        for finding in result["findings"]:
            lines.append(f"- {finding['level'].upper()} {finding['rule_id']}: {finding['message']}")
    return "\n".join(lines)


def score(
    federated_registry: Path = DEFAULT_FEDERATED_REGISTRY,
    doctor_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doctor_reused = doctor_result is not None
    doctor_result = doctor_result if doctor_result is not None else doctor(federated_registry)
    summary = doctor_result.get("summary", {})
    fail_count = int(summary.get("fail", 0))
    warn_count = int(summary.get("warn", 0))
    unregistered_count = int(summary.get("unregistered_files", 0))

    hard_gates = []
    if fail_count > 0:
        hard_gates.append({"gate": "fail", "count": fail_count, "reason": "doctor reported failures"})
    if unregistered_count > 0:
        hard_gates.append(
            {
                "gate": "unregistered",
                "count": unregistered_count,
                "reason": "unregistered current files block 9.5 eligibility",
            }
        )
    if warn_count > 0:
        hard_gates.append(
            {
                "gate": "blocking_warn",
                "count": warn_count,
                "reason": "doctor warnings are blocking until classified",
            }
        )

    deductions: list[dict[str, Any]] = []
    if fail_count:
        deductions.append({"points": 40, "reason": "doctor failures present"})
    if unregistered_count:
        deductions.append({"points": 30, "reason": "unregistered files present"})
    if warn_count:
        deductions.append({"points": 10, "reason": "blocking warnings present"})

    score_value = max(0, 100 - sum(int(item["points"]) for item in deductions))
    eligible_95 = score_value >= 95 and not hard_gates
    return {
        "schema_version": "agents-os.docctl.score.result.v0.1",
        "passed": bool(doctor_result.get("passed")) and eligible_95,
        "score": score_value,
        "eligible_95": eligible_95,
        "hard_gates": hard_gates,
        "blocking_warn": warn_count,
        "advisory_warn": 0,
        "deductions": deductions,
        "doctor_summary": summary,
        "doctor_passed": bool(doctor_result.get("passed")),
        "doctor_result_reused": doctor_reused,
        "warnings": {
            "score_is_read_only": True,
            "doctor_is_source": True,
            "registry_write_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
        },
    }


def format_score_text(result: dict[str, Any]) -> str:
    lines = [
        "docctl score",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Score: {result['score']}",
        f"Eligible 9.5: {result['eligible_95']}",
        f"Blocking warnings: {result['blocking_warn']}",
        f"Advisory warnings: {result['advisory_warn']}",
        f"Hard gates: {len(result['hard_gates'])}",
    ]
    for gate in result["hard_gates"]:
        lines.append(f"- {gate['gate']}: count={gate['count']} reason={gate['reason']}")
    if result["deductions"]:
        lines.append("Deductions:")
        for item in result["deductions"]:
            lines.append(f"- {item['points']} points: {item['reason']}")
    return "\n".join(lines)


def resolve_snapshot_dir(snapshot_dir: Path) -> tuple[Path | None, list[dict[str, str]]]:
    if is_protected_path(snapshot_dir):
        return None, [intake_finding("DOCCTL-TREND-BLOCKED", "fail", f"snapshot_dir points to protected path: {snapshot_dir}")]
    candidate = snapshot_dir if snapshot_dir.is_absolute() else WORKSPACE_ROOT / snapshot_dir
    resolved, resolve_error = safe_resolve(candidate)
    if resolve_error:
        return None, [intake_finding("DOCCTL-TREND-BLOCKED", "fail", f"snapshot_dir could not be resolved: {resolve_error}")]
    if resolved is None:
        return None, [intake_finding("DOCCTL-TREND-BLOCKED", "fail", f"snapshot_dir could not be resolved: {snapshot_dir}")]
    if is_protected_path(resolved):
        return None, [intake_finding("DOCCTL-TREND-BLOCKED", "fail", f"snapshot_dir resolves to protected path: {snapshot_dir}")]
    if not is_under_workspace(resolved, WORKSPACE_ROOT):
        return None, [intake_finding("DOCCTL-TREND-BLOCKED", "fail", f"snapshot_dir points outside workspace: {snapshot_dir}")]
    if resolved.exists() and not resolved.is_dir():
        return None, [intake_finding("DOCCTL-TREND-BLOCKED", "fail", f"snapshot_dir is not a directory: {snapshot_dir}")]
    return resolved, []


def load_trend_snapshots(snapshot_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    snapshots: list[dict[str, Any]] = []
    if not snapshot_dir.exists():
        return snapshots, findings

    for path in sorted(snapshot_dir.glob("*.json")):
        if is_protected_path(path):
            findings.append(intake_finding("DOCCTL-TREND-BLOCKED", "fail", f"snapshot path is protected: {path}"))
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            findings.append(intake_finding("DOCCTL-TREND-SNAPSHOT", "fail", f"snapshot could not be read: {path}: {exc}"))
            continue
        summary = payload.get("doctor_summary") if isinstance(payload, dict) else None
        if not isinstance(summary, dict):
            summary = payload.get("summary") if isinstance(payload, dict) else None
        if not isinstance(summary, dict):
            findings.append(intake_finding("DOCCTL-TREND-SNAPSHOT", "fail", f"snapshot missing doctor summary: {path}"))
            continue
        snapshots.append(
            {
                "path": workspace_display(path),
                "date": payload.get("date") or payload.get("created_at") or path.stem,
                "doctor_summary": summary,
            }
        )
    return snapshots, findings


def trend(
    federated_registry: Path = DEFAULT_FEDERATED_REGISTRY,
    snapshot_dir: Path = DEFAULT_TREND_SNAPSHOT_DIR,
    doctor_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doctor_reused = doctor_result is not None
    findings: list[dict[str, str]] = []
    resolved_snapshot_dir, snapshot_findings = resolve_snapshot_dir(snapshot_dir)
    findings.extend(snapshot_findings)

    current_doctor = doctor_result if doctor_result is not None else doctor(federated_registry)
    snapshots: list[dict[str, Any]] = []
    if resolved_snapshot_dir is not None:
        snapshots, load_findings = load_trend_snapshots(resolved_snapshot_dir)
        findings.extend(load_findings)

    current_summary = current_doctor.get("summary", {})
    latest_snapshot = snapshots[-1] if snapshots else None
    no_regression = None
    if latest_snapshot:
        previous = latest_snapshot["doctor_summary"]
        no_regression = (
            int(current_summary.get("unregistered_files", 0)) <= int(previous.get("unregistered_files", 0))
            and int(current_summary.get("warn", 0)) <= int(previous.get("warn", 0))
            and int(current_summary.get("fail", 0)) <= int(previous.get("fail", 0))
        )

    trend_status = "ready" if snapshots else "insufficient_snapshots"
    return {
        "schema_version": "agents-os.docctl.trend.result.v0.1",
        "passed": current_doctor.get("passed", False) and not any(finding["level"] == "fail" for finding in findings),
        "trend_status": trend_status,
        "snapshot_dir": workspace_display(resolved_snapshot_dir) if resolved_snapshot_dir else str(snapshot_dir),
        "snapshots_found": len(snapshots),
        "current_doctor_summary": current_summary,
        "doctor_result_reused": doctor_reused,
        "latest_snapshot": latest_snapshot,
        "no_regression_from_latest": no_regression,
        "known_archive_current": {
            "known_external_scope": current_summary.get("known_external_scope_files", 0),
            "archived": current_summary.get("archived_files", 0),
        },
        "findings": findings,
        "warnings": {
            "trend_is_read_only": True,
            "snapshot_write_performed": False,
            "registry_write_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
        },
    }


def format_trend_text(result: dict[str, Any]) -> str:
    lines = [
        "docctl trend",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Trend status: {result['trend_status']}",
        f"Snapshots found: {result['snapshots_found']}",
        f"Snapshot dir: {result['snapshot_dir']}",
        f"No regression from latest: {result['no_regression_from_latest']}",
    ]
    summary = result.get("current_doctor_summary", {})
    lines.append(
        "Current: "
        f"documents={summary.get('documents')} "
        f"unregistered={summary.get('unregistered_files')} "
        f"warn={summary.get('warn')} fail={summary.get('fail')} "
        f"known={summary.get('known_external_scope_files')} archived={summary.get('archived_files')}"
    )
    if result.get("findings"):
        lines.append("")
        lines.append("Findings:")
        for finding in result["findings"]:
            lines.append(f"- {finding['level'].upper()} {finding['rule_id']}: {finding['message']}")
    return "\n".join(lines)


def snapshot_finding(rule_id: str, level: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "level": level, "message": message}


def generated_snapshot_name(now: datetime | None = None) -> str:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-docctl-summary.json"


def resolve_snapshot_output(
    snapshot_dir: Path,
    output: Path | None = None,
) -> tuple[Path | None, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []
    resolved_dir, dir_findings = resolve_snapshot_dir(snapshot_dir)
    findings.extend(dir_findings)
    if resolved_dir is None:
        return None, findings

    output_candidate = output if output is not None else snapshot_dir / generated_snapshot_name()
    if is_protected_path(output_candidate):
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output points to protected path: {output_candidate}")
        )
        return None, findings

    if output_candidate.is_absolute():
        output_path = output_candidate
    else:
        output_path = WORKSPACE_ROOT / output_candidate

    resolved_output, output_error = safe_resolve(output_path)
    if output_error:
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output could not be resolved: {output_error}")
        )
        return None, findings
    if resolved_output is None:
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output could not be resolved: {output_candidate}")
        )
        return None, findings
    if is_protected_path(resolved_output):
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output resolves to protected path: {output_candidate}")
        )
        return None, findings
    if not is_under_workspace(resolved_output, WORKSPACE_ROOT):
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output points outside workspace: {output_candidate}")
        )
        return None, findings
    if not is_under_workspace(resolved_output, resolved_dir):
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output is outside snapshot_dir: {output_candidate}")
        )
        return None, findings
    if resolved_output.suffix.lower() != ".json":
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output must be a JSON file: {output_candidate}")
        )
        return None, findings
    if resolved_output.exists():
        findings.append(
            snapshot_finding("DOCCTL-SNAPSHOT-BLOCKED", "fail", f"output already exists: {workspace_display(resolved_output)}")
        )
        return None, findings

    return resolved_output, findings


def build_snapshot_payload(
    federated_registry: Path,
    snapshot_dir: Path,
) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    doctor_result = doctor(federated_registry)
    score_result = score(federated_registry, doctor_result=doctor_result)
    trend_result = trend(federated_registry, snapshot_dir, doctor_result=doctor_result)

    doctor_summary = doctor_result.get("summary", {})
    score_summary = {
        "score": score_result.get("score"),
        "eligible_95": score_result.get("eligible_95"),
        "blocking_warn": score_result.get("blocking_warn"),
        "advisory_warn": score_result.get("advisory_warn"),
        "hard_gates": len(score_result.get("hard_gates", [])),
        "doctor_passed": score_result.get("doctor_passed"),
    }
    trend_context = {
        "trend_status_before_write": trend_result.get("trend_status"),
        "snapshots_found_before_write": trend_result.get("snapshots_found"),
        "no_regression_from_latest_before_write": trend_result.get("no_regression_from_latest"),
    }

    return {
        "schema_version": "agents-os.docctl.snapshot.v0.1",
        "created_at": created_at,
        "workspace_root": str(WORKSPACE_ROOT),
        "federated_registry": workspace_display(
            federated_registry if federated_registry.is_absolute() else WORKSPACE_ROOT / federated_registry
        ),
        "doctor_summary": doctor_summary,
        "score_summary": score_summary,
        "trend_context": trend_context,
        "source_commands": [
            "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor",
            "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score",
            "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend",
        ],
        "docctl_index": {
            "doctor_invocations": 1,
            "doctor_reused_by": ["score", "trend"],
            "persistent_cache_write_performed": False,
        },
        "write_scope": {
            "snapshot_dir": workspace_display(
                snapshot_dir if snapshot_dir.is_absolute() else WORKSPACE_ROOT / snapshot_dir
            ),
            "summary_only": True,
            "raw_registry_content_included": False,
            "raw_logs_included": False,
            "full_document_text_included": False,
            "secrets_included": False,
            "provider_raw_response_included": False,
        },
        "write_performed": True,
        "external_write_performed": False,
        "provider_call_performed": False,
        "formal_memory_registration": "not_performed",
    }


def snapshot(
    federated_registry: Path = DEFAULT_FEDERATED_REGISTRY,
    snapshot_dir: Path = DEFAULT_TREND_SNAPSHOT_DIR,
    output: Path | None = None,
) -> dict[str, Any]:
    output_path, findings = resolve_snapshot_output(snapshot_dir, output)
    if output_path is None:
        return {
            "schema_version": "agents-os.docctl.snapshot.result.v0.1",
            "passed": False,
            "snapshot_path": None,
            "write_performed": False,
            "findings": findings,
            "warnings": {
                "snapshot_writer": True,
                "registry_write_performed": False,
                "external_write_performed": False,
                "provider_call_performed": False,
                "formal_memory_registration": "not_performed",
                "apply_fix_implemented": False,
            },
        }

    payload = build_snapshot_payload(federated_registry, snapshot_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "schema_version": "agents-os.docctl.snapshot.result.v0.1",
        "passed": True,
        "snapshot_path": workspace_display(output_path),
        "write_performed": True,
        "doctor_summary": payload["doctor_summary"],
        "score_summary": payload["score_summary"],
        "trend_context": payload["trend_context"],
        "findings": findings,
        "warnings": {
            "snapshot_writer": True,
            "summary_only": True,
            "raw_registry_content_included": False,
            "raw_logs_included": False,
            "full_document_text_included": False,
            "secrets_included": False,
            "provider_raw_response_included": False,
            "registry_write_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
            "formal_memory_registration": "not_performed",
            "apply_fix_implemented": False,
        },
    }


def format_snapshot_text(result: dict[str, Any]) -> str:
    lines = [
        "docctl snapshot",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Snapshot path: {result['snapshot_path']}",
        f"Write performed: {result['write_performed']}",
    ]
    summary = result.get("doctor_summary") or {}
    if summary:
        lines.append(
            "Doctor: "
            f"documents={summary.get('documents')} "
            f"unregistered={summary.get('unregistered_files')} "
            f"warn={summary.get('warn')} fail={summary.get('fail')}"
        )
    score_summary = result.get("score_summary") or {}
    if score_summary:
        lines.append(
            "Score: "
            f"score={score_summary.get('score')} "
            f"eligible_95={score_summary.get('eligible_95')} "
            f"hard_gates={score_summary.get('hard_gates')}"
        )
    if result.get("findings"):
        lines.append("")
        lines.append("Findings:")
        for finding in result["findings"]:
            lines.append(f"- {finding['level'].upper()} {finding['rule_id']}: {finding['message']}")
    return "\n".join(lines)


PLAN_FIX_VALIDATION_COMMANDS = [
    "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor",
    "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score",
    "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml",
    "PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml",
]


def extract_path_after_marker(message: str, marker: str) -> str | None:
    if marker not in message:
        return None
    return message.split(marker, 1)[1].strip()


def build_plan_fix_proposal(
    index: int,
    category: str,
    affected_path: str,
    reason: str,
    suggested_action: str,
    risk_level: str,
    required_confirmation: str,
    evidence_required: str,
) -> dict[str, Any]:
    return {
        "id": f"PF-{index:04d}",
        "category": category,
        "affected_path": affected_path,
        "reason": reason,
        "suggested_action": suggested_action,
        "risk_level": risk_level,
        "required_confirmation": required_confirmation,
        "validation_commands": PLAN_FIX_VALIDATION_COMMANDS,
        "evidence_required": evidence_required,
        "write_performed": False,
    }


def plan_fix_proposal_for_finding(
    index: int,
    finding: dict[str, str],
    registry_paths: dict[str, str],
    target: str,
) -> dict[str, Any] | None:
    rule_id = finding.get("rule_id", "")
    level = finding.get("level", "")
    owner = finding.get("owner", "")
    message = finding.get("message", "")

    if level == "info":
        return None

    if rule_id == "DOCCTL-UNREGISTERED":
        affected_path = extract_path_after_marker(message, "source file is not registered: ") or owner or target
        return build_plan_fix_proposal(
            index,
            "register_missing_document",
            affected_path,
            message,
            "Run docctl intake for this path, then prepare a reviewed registry entry or explicit classification.",
            "yellow",
            "Jenn confirmation for local registry metadata and evidence writes",
            "receipt/review for the registry or classification update",
        )

    if rule_id == "DOCCTL-COUNT":
        return build_plan_fix_proposal(
            index,
            "fix_expected_document_count",
            registry_paths.get(owner, owner or target),
            message,
            "Review the child registry count and update expected_document_count only if the document set is correct.",
            "yellow",
            "Jenn confirmation for federated registry metadata write",
            "receipt/review explaining the count change",
        )

    if rule_id in {"DOCCTL-PROTECTED", "DOCCTL-OUTSIDE", "DOCCTL-PATH-RESOLVE"}:
        return build_plan_fix_proposal(
            index,
            "blocked_protected_path",
            owner or target,
            message,
            "Do not repair automatically. Replace the protected/outside path with a safe local reference only after review.",
            "red",
            "P3 boundary review; proposal only",
            "manual review before any path change",
        )

    if rule_id in {"DOCCTL-MISSING-RECEIPT-REVIEW", "DOCCTL-MISSING-PATH"} or "review_by" in message:
        return build_plan_fix_proposal(
            index,
            "add_missing_review_link",
            owner or target,
            message,
            "Prepare or restore the required review/receipt reference, then validate registry links.",
            "yellow",
            "Jenn confirmation for local evidence or registry metadata write",
            "receipt/review for the evidence-link repair",
        )

    if rule_id in {"DOCCTL-MISSING-FILE", "DOCCTL-VALIDATOR", "DOCCTL-REGISTRY-LOAD", "DOCCTL-FEDERATION-LOAD"}:
        return build_plan_fix_proposal(
            index,
            "repair_broken_reference",
            registry_paths.get(owner, owner or target),
            message,
            "Inspect the broken local reference and prepare a narrow metadata or file restoration plan.",
            "yellow",
            "Jenn confirmation for any local write",
            "receipt/review for the reference repair",
        )

    return build_plan_fix_proposal(
        index,
        "manual_review_required",
        registry_paths.get(owner, owner or target),
        message,
        "Review this finding and create a narrower confirmation package before any write.",
        "yellow",
        "Jenn confirmation after manual review",
        "receipt/review for the selected repair route",
    )


def plan_fix(
    federated_registry: Path = DEFAULT_FEDERATED_REGISTRY,
    doctor_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    doctor_reused = doctor_result is not None
    doctor_result = doctor_result if doctor_result is not None else doctor(federated_registry)
    target = str(federated_registry)
    registry_paths = {
        item.get("registry_id", ""): item.get("registry_path", "")
        for item in doctor_result.get("registries", [])
        if isinstance(item, dict)
    }
    proposals: list[dict[str, Any]] = []
    for finding in doctor_result.get("findings", []):
        proposal = plan_fix_proposal_for_finding(
            len(proposals) + 1,
            finding,
            registry_paths,
            target,
        )
        if proposal is not None:
            proposals.append(proposal)

    blocked = any(proposal["category"] == "blocked_protected_path" for proposal in proposals)
    if not proposals:
        proposals.append(
            build_plan_fix_proposal(
                1,
                "no_action_needed",
                workspace_display(Path(federated_registry)) if Path(federated_registry).is_absolute() else str(federated_registry),
                "doctor reported no warn/fail findings that require repair planning",
                "No repair proposal is needed for the current declared governance scope.",
                "green",
                "none",
                "none",
            )
        )

    if blocked:
        plan_status = "blocked"
    elif proposals and proposals[0]["category"] == "no_action_needed" and len(proposals) == 1:
        plan_status = "no_action_needed"
    else:
        plan_status = "proposals_ready"

    return {
        "schema_version": "agents-os.docctl.plan_fix.result.v0.1",
        "passed": not blocked,
        "plan_status": plan_status,
        "dry_run": True,
        "would_write": False,
        "write_performed": False,
        "patch_created": False,
        "snapshot_write_performed": False,
        "proposal_count": len(proposals),
        "proposals": proposals,
        "doctor_passed": bool(doctor_result.get("passed")),
        "doctor_summary": doctor_result.get("summary", {}),
        "doctor_result_reused": doctor_reused,
        "findings": doctor_result.get("findings", []),
        "warnings": {
            "plan_fix_is_dry_run": True,
            "write_performed": False,
            "patch_created": False,
            "snapshot_write_performed": False,
            "registry_write_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
            "formal_memory_registration": "not_performed",
            "apply_fix_implemented": False,
        },
    }


def format_plan_fix_text(result: dict[str, Any]) -> str:
    lines = [
        "docctl plan-fix",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Plan status: {result['plan_status']}",
        f"Dry run: {result['dry_run']}",
        f"Would write: {result['would_write']}",
        f"Write performed: {result['write_performed']}",
        f"Patch created: {result['patch_created']}",
        f"Snapshot write performed: {result['snapshot_write_performed']}",
        f"Doctor passed: {result['doctor_passed']}",
        f"Proposals: {result['proposal_count']}",
    ]
    for proposal in result["proposals"]:
        lines.append(
            f"- {proposal['id']} {proposal['category']} "
            f"risk={proposal['risk_level']} path={proposal['affected_path']}"
        )
        lines.append(f"  Reason: {proposal['reason']}")
        lines.append(f"  Suggested action: {proposal['suggested_action']}")
        lines.append(f"  Required confirmation: {proposal['required_confirmation']}")
    return "\n".join(lines)


def apply_fix_preview(proposal_id: str, federated_registry: Path = DEFAULT_FEDERATED_REGISTRY) -> dict[str, Any]:
    plan_result = plan_fix(federated_registry)
    proposals = [
        proposal
        for proposal in plan_result.get("proposals", [])
        if isinstance(proposal, dict)
    ]
    selected = next((proposal for proposal in proposals if proposal.get("id") == proposal_id), None)
    findings: list[dict[str, str]] = []

    if selected is None:
        findings.append(
            intake_finding(
                "DOCCTL-APPLY-FIX-PREVIEW",
                "fail",
                f"plan-fix proposal id was not found: {proposal_id}",
            )
        )
        preview_status = "proposal_not_found"
        allowed_for_preview = False
        blocked_reasons = [finding["message"] for finding in findings]
    else:
        preview_status = (
            "blocked"
            if plan_result.get("plan_status") == "blocked" or selected.get("category") == "blocked_protected_path"
            else str(plan_result.get("plan_status") or "preview_ready")
        )
        allowed_for_preview = preview_status != "blocked"
        blocked_reasons = [selected.get("reason", "blocked plan-fix proposal")] if not allowed_for_preview else []
        if not allowed_for_preview:
            findings.append(
                intake_finding(
                    "DOCCTL-APPLY-FIX-PREVIEW",
                    "fail",
                    f"plan-fix proposal is blocked and cannot be previewed for execution: {proposal_id}",
                )
            )

    passed = bool(selected is not None and allowed_for_preview)
    proposal_summary = None
    if selected is not None:
        proposal_summary = {
            "proposal_id": selected.get("id"),
            "proposal_category": selected.get("category"),
            "repair_class": selected.get("category"),
            "affected_path": selected.get("affected_path"),
            "risk_level": selected.get("risk_level"),
            "reason": selected.get("reason"),
            "suggested_action": selected.get("suggested_action"),
            "required_confirmation": selected.get("required_confirmation"),
            "validation_commands": selected.get("validation_commands", []),
            "evidence_required": selected.get("evidence_required"),
            "write_performed": False,
        }

    return {
        "schema_version": "agents-os.docctl.apply_fix.preview.result.v0.1",
        "passed": passed,
        "preview_status": preview_status,
        "proposal_id": proposal_id,
        "preview_only": True,
        "dry_run": True,
        "would_write": False,
        "write_performed": False,
        "patch_created": False,
        "snapshot_write_performed": False,
        "execution_authorized": False,
        "registry_write_performed": False,
        "external_write_performed": False,
        "provider_call_performed": False,
        "formal_memory_registration": "not_performed",
        "apply_fix_execution_implemented": False,
        "apply_fix_execution_authorized": False,
        "allowed_for_preview": allowed_for_preview,
        "blocked_reasons": blocked_reasons,
        "proposal": proposal_summary,
        "plan_fix": {
            "plan_status": plan_result.get("plan_status"),
            "proposal_count": plan_result.get("proposal_count"),
            "doctor_passed": plan_result.get("doctor_passed"),
            "dry_run": plan_result.get("dry_run"),
            "would_write": plan_result.get("would_write"),
            "write_performed": plan_result.get("write_performed"),
            "patch_created": plan_result.get("patch_created"),
            "snapshot_write_performed": plan_result.get("snapshot_write_performed"),
        },
        "findings": findings,
        "warnings": {
            "apply_fix_preview_is_read_only": True,
            "plan_fix_is_dry_run": True,
            "write_performed": False,
            "patch_created": False,
            "snapshot_write_performed": False,
            "registry_write_performed": False,
            "external_write_performed": False,
            "provider_call_performed": False,
            "formal_memory_registration": "not_performed",
            "execution_authorized": False,
            "apply_fix_execution_implemented": False,
            "apply_fix_execution_authorized": False,
        },
    }


def format_apply_fix_preview_text(result: dict[str, Any]) -> str:
    lines = [
        "docctl apply-fix --preview",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Preview status: {result['preview_status']}",
        f"Proposal id: {result['proposal_id']}",
        f"Preview only: {result['preview_only']}",
        f"Dry run: {result['dry_run']}",
        f"Would write: {result['would_write']}",
        f"Write performed: {result['write_performed']}",
        f"Patch created: {result['patch_created']}",
        f"Snapshot write performed: {result['snapshot_write_performed']}",
        f"Execution authorized: {result['execution_authorized']}",
        f"Registry write performed: {result['registry_write_performed']}",
    ]
    proposal = result.get("proposal")
    if isinstance(proposal, dict):
        lines.extend(
            [
                "",
                (
                    f"Proposal: {proposal.get('proposal_id')} "
                    f"{proposal.get('proposal_category')} "
                    f"risk={proposal.get('risk_level')} "
                    f"path={proposal.get('affected_path')}"
                ),
                f"Reason: {proposal.get('reason')}",
                f"Suggested action: {proposal.get('suggested_action')}",
                f"Required confirmation: {proposal.get('required_confirmation')}",
                f"Evidence required: {proposal.get('evidence_required')}",
            ]
        )
    if result.get("blocked_reasons"):
        lines.append("")
        lines.append("Blocked reasons:")
        for reason in result["blocked_reasons"]:
            lines.append(f"- {reason}")
    if result.get("findings"):
        lines.append("")
        lines.append("Findings:")
        for finding in result["findings"]:
            lines.append(f"- {finding['level'].upper()} {finding['rule_id']}: {finding['message']}")
    return "\n".join(lines)


def status_next_action(
    doctor_result: dict[str, Any],
    score_result: dict[str, Any],
    trend_result: dict[str, Any],
    plan_fix_result: dict[str, Any],
) -> str:
    if not doctor_result.get("passed"):
        return "review doctor findings and use docctl plan-fix dry-run before any repair write"
    if plan_fix_result.get("plan_status") == "blocked":
        return "stop at boundary review; do not repair protected or outside paths automatically"
    if plan_fix_result.get("plan_status") == "proposals_ready":
        return "review plan-fix proposals and prepare a narrow confirmation package for any write"
    if not score_result.get("eligible_95"):
        return "review score hard gates before claiming 9.5 eligibility"
    if trend_result.get("no_regression_from_latest") is False:
        return "review trend regression before making further governance changes"
    if trend_result.get("trend_status") == "insufficient_snapshots":
        return "create a reviewed summary snapshot only after explicit confirmation"
    return "no immediate repair needed; maintain review and snapshot cadence"


def status(
    federated_registry: Path = DEFAULT_FEDERATED_REGISTRY,
    snapshot_dir: Path = DEFAULT_TREND_SNAPSHOT_DIR,
) -> dict[str, Any]:
    doctor_result = doctor(federated_registry)
    score_result = score(federated_registry, doctor_result=doctor_result)
    trend_result = trend(federated_registry, snapshot_dir, doctor_result=doctor_result)
    plan_fix_result = plan_fix(federated_registry, doctor_result=doctor_result)
    latest_snapshot = trend_result.get("latest_snapshot") or {}
    proposal_categories = [
        str(proposal.get("category"))
        for proposal in plan_fix_result.get("proposals", [])
        if isinstance(proposal, dict)
    ]
    component_findings = {
        "doctor": len(doctor_result.get("findings", [])),
        "trend": len(trend_result.get("findings", [])),
        "plan_fix": len(plan_fix_result.get("findings", [])),
    }
    next_action = status_next_action(
        doctor_result,
        score_result,
        trend_result,
        plan_fix_result,
    )

    return {
        "schema_version": "agents-os.docctl.status.result.v0.1",
        "passed": bool(doctor_result.get("passed"))
        and bool(score_result.get("passed"))
        and bool(trend_result.get("passed"))
        and bool(plan_fix_result.get("passed")),
        "target": workspace_display(Path(federated_registry)) if Path(federated_registry).is_absolute() else str(federated_registry),
        "snapshot_dir": trend_result.get("snapshot_dir"),
        "read_only": True,
        "would_write": False,
        "doctor": {
            "passed": bool(doctor_result.get("passed")),
            "summary": doctor_result.get("summary", {}),
        },
        "score": {
            "passed": bool(score_result.get("passed")),
            "score": score_result.get("score"),
            "eligible_95": score_result.get("eligible_95"),
            "blocking_warn": score_result.get("blocking_warn"),
            "advisory_warn": score_result.get("advisory_warn"),
            "hard_gates": len(score_result.get("hard_gates", [])),
        },
        "trend": {
            "passed": bool(trend_result.get("passed")),
            "trend_status": trend_result.get("trend_status"),
            "snapshots_found": trend_result.get("snapshots_found"),
            "latest_snapshot_path": latest_snapshot.get("path") if isinstance(latest_snapshot, dict) else None,
            "no_regression_from_latest": trend_result.get("no_regression_from_latest"),
        },
        "plan_fix": {
            "passed": bool(plan_fix_result.get("passed")),
            "plan_status": plan_fix_result.get("plan_status"),
            "proposal_count": plan_fix_result.get("proposal_count"),
            "proposal_categories": proposal_categories,
        },
        "component_findings": component_findings,
        "docctl_index": {
            "doctor_invocations": 1,
            "doctor_reused_by": ["score", "trend", "plan_fix"],
            "persistent_cache_write_performed": False,
            "read_only_index": True,
        },
        "next_recommended_action": next_action,
        "warnings": {
            "status_is_read_only": True,
            "write_performed": False,
            "snapshot_write_performed": False,
            "registry_write_performed": False,
            "external_write_performed": False,
            "runtime_execution_performed": False,
            "provider_call_performed": False,
            "formal_memory_registration": "not_performed",
            "apply_fix_implemented": False,
            "snapshot_writer_called": False,
            "raw_logs_included": False,
            "provider_raw_response_included": False,
        },
    }


def format_status_text(result: dict[str, Any]) -> str:
    doctor_summary = result.get("doctor", {}).get("summary", {})
    score_summary = result.get("score", {})
    trend_summary = result.get("trend", {})
    plan_summary = result.get("plan_fix", {})
    docctl_index = result.get("docctl_index", {})
    lines = [
        "docctl status",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        f"Read only: {result['read_only']}",
        f"Would write: {result['would_write']}",
        (
            "Doctor: "
            f"registries={doctor_summary.get('registries')} "
            f"documents={doctor_summary.get('documents')} "
            f"unregistered={doctor_summary.get('unregistered_files')} "
            f"warn={doctor_summary.get('warn')} fail={doctor_summary.get('fail')}"
        ),
        (
            "Score: "
            f"score={score_summary.get('score')} "
            f"eligible_95={score_summary.get('eligible_95')} "
            f"hard_gates={score_summary.get('hard_gates')}"
        ),
        (
            "Trend: "
            f"status={trend_summary.get('trend_status')} "
            f"snapshots={trend_summary.get('snapshots_found')} "
            f"no_regression={trend_summary.get('no_regression_from_latest')}"
        ),
        f"Latest snapshot: {trend_summary.get('latest_snapshot_path')}",
        (
            "Plan fix: "
            f"status={plan_summary.get('plan_status')} "
            f"proposals={plan_summary.get('proposal_count')}"
        ),
        (
            "Index: "
            f"doctor_invocations={docctl_index.get('doctor_invocations')} "
            f"reused_by={','.join(docctl_index.get('doctor_reused_by', []))}"
        ),
        f"Next: {result['next_recommended_action']}",
    ]
    return "\n".join(lines)


def build_result(
    federated_registry: Path,
    findings: list[dict[str, str]],
    registry_results: list[dict[str, Any]],
    federated_validator: dict[str, Any],
) -> dict[str, Any]:
    fail_count = sum(1 for finding in findings if finding["level"] == "fail")
    warn_count = sum(1 for finding in findings if finding["level"] == "warn")
    return {
        "schema_version": "agents-os.docctl.doctor.result.v0.1",
        "passed": fail_count == 0,
        "target": workspace_display(federated_registry),
        "summary": {
            "registries": len(registry_results),
            "documents": sum(int(item.get("documents", 0)) for item in registry_results),
            "scanned_files": sum(int(item.get("scanned_files", 0)) for item in registry_results),
            "known_external_scope_files": sum(
                int(item.get("known_external_scope_files", 0)) for item in registry_results
            ),
            "archived_files": sum(int(item.get("archived_files", 0)) for item in registry_results),
            "unregistered_files": sum(int(item.get("unregistered_files", 0)) for item in registry_results),
            "fail": fail_count,
            "warn": warn_count,
        },
        "findings": findings,
        "validator_runs": {
            "federated": federated_validator,
            "document_registries": {
                item["registry_id"]: item["validator"] for item in registry_results
            },
        },
        "registries": registry_results,
        "warnings": {
            "doctor_is_read_only": True,
            "full_workspace_scan_performed": False,
            "external_write_performed": False,
            "runtime_execution_performed": False,
            "provider_call_performed": False,
            "formal_memory_registration": "not_performed",
        },
    }


def format_text(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"docctl doctor: {result['target']}",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        (
            "Summary: "
            f"registries={summary['registries']} "
            f"documents={summary['documents']} "
            f"scanned_files={summary['scanned_files']} "
            f"known_external_scope={summary['known_external_scope_files']} "
            f"archived={summary['archived_files']} "
            f"unregistered={summary['unregistered_files']} "
            f"warn={summary['warn']} fail={summary['fail']}"
        ),
    ]

    if result["findings"]:
        lines.append("")
        lines.append("Findings:")
        for finding in result["findings"]:
            lines.append(
                f"- {finding['level'].upper()} {finding['rule_id']} "
                f"{finding['owner']}: {finding['message']}"
            )

    lines.append("")
    lines.append("Validator Runs:")
    federated = result["validator_runs"].get("federated") or {}
    if federated:
        lines.append(f"- federated: {'PASS' if federated.get('passed') else 'FAIL'}")
    for registry_id, run in result["validator_runs"].get("document_registries", {}).items():
        lines.append(f"- {registry_id}: {'PASS' if run.get('passed') else 'FAIL'}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="AGENTS OS document governance helper.")
    subparsers = parser.add_subparsers(dest="command")

    doctor_parser = subparsers.add_parser("doctor", help="Run read-only document governance checks.")
    doctor_parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to inspect.",
    )
    doctor_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    intake_parser = subparsers.add_parser("intake", help="Dry-run route a document path before registration.")
    intake_parser.add_argument("target", help="Local file path to route.")
    intake_parser.add_argument(
        "--federated-registry",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to use for routing context.",
    )
    intake_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    impact_parser = subparsers.add_parser("impact", help="Read-only impact view for changed local paths.")
    impact_parser.add_argument("targets", nargs="+", help="Changed local file paths to inspect.")
    impact_parser.add_argument(
        "--federated-registry",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to use for impact context.",
    )
    impact_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    score_parser = subparsers.add_parser("score", help="Read-only document-governance score.")
    score_parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to score.",
    )
    score_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    trend_parser = subparsers.add_parser("trend", help="Read-only trend view over existing local snapshots.")
    trend_parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to inspect.",
    )
    trend_parser.add_argument(
        "--snapshot-dir",
        default=str(DEFAULT_TREND_SNAPSHOT_DIR),
        help="Existing snapshot directory to read. Missing directory is allowed.",
    )
    trend_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    snapshot_parser = subparsers.add_parser("snapshot", help="Write one local summary snapshot for docctl trend.")
    snapshot_parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to snapshot.",
    )
    snapshot_parser.add_argument(
        "--snapshot-dir",
        default=str(DEFAULT_TREND_SNAPSHOT_DIR),
        help="Snapshot directory to write under.",
    )
    snapshot_parser.add_argument(
        "--output",
        help="Exact snapshot JSON path. Must be under snapshot-dir and must not already exist.",
    )
    snapshot_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    status_parser = subparsers.add_parser("status", help="Read-only document governance pulse.")
    status_parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to inspect.",
    )
    status_parser.add_argument(
        "--snapshot-dir",
        default=str(DEFAULT_TREND_SNAPSHOT_DIR),
        help="Existing snapshot directory to read. Missing directory is allowed.",
    )
    status_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    plan_fix_parser = subparsers.add_parser("plan-fix", help="Dry-run repair proposal planning.")
    plan_fix_parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to inspect.",
    )
    plan_fix_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    apply_fix_parser = subparsers.add_parser(
        "apply-fix",
        help="Read-only preview of one plan-fix proposal. Execution is not implemented.",
    )
    apply_fix_parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_FEDERATED_REGISTRY),
        help="Federated Document Registry YAML to inspect.",
    )
    apply_fix_parser.add_argument(
        "--preview",
        required=True,
        help="Plan-fix proposal id to preview. Preview only; no writes.",
    )
    apply_fix_parser.add_argument("--json", action="store_true", help="Emit JSON output.")

    args = parser.parse_args()
    if args.command == "doctor":
        result = doctor(Path(args.target))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_text(result))
        return 0 if result["passed"] else 1

    if args.command == "intake":
        result = intake(Path(args.target), Path(args.federated_registry))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_intake_text(result))
        return 0 if result["passed"] else 1

    if args.command == "impact":
        result = impact([Path(target) for target in args.targets], Path(args.federated_registry))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_impact_text(result))
        return 0 if result["passed"] else 1

    if args.command == "score":
        result = score(Path(args.target))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_score_text(result))
        return 0 if result["passed"] else 1

    if args.command == "trend":
        result = trend(Path(args.target), Path(args.snapshot_dir))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_trend_text(result))
        return 0 if result["passed"] else 1

    if args.command == "snapshot":
        output = Path(args.output) if args.output else None
        result = snapshot(Path(args.target), Path(args.snapshot_dir), output)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_snapshot_text(result))
        return 0 if result["passed"] else 1

    if args.command == "status":
        result = status(Path(args.target), Path(args.snapshot_dir))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_status_text(result))
        return 0 if result["passed"] else 1

    if args.command == "plan-fix":
        result = plan_fix(Path(args.target))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_plan_fix_text(result))
        return 0 if result["passed"] else 1

    if args.command == "apply-fix":
        result = apply_fix_preview(args.preview, Path(args.target))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_apply_fix_preview_text(result))
        return 0 if result["passed"] else 1

    if args.command is None:
        parser.print_help()
        return 2
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
