#!/usr/bin/env python3
"""Validate an AGENTS OS Federated Document Registry YAML file.

This is a local read-only checker. It validates a registry-of-registries and
then validates only the directory document registries explicitly listed there.
It does not scan the full workspace, build an index database, write external
systems, call providers, or grant authority.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

REGISTRY_DIR = Path(__file__).resolve().parent
if str(REGISTRY_DIR) not in sys.path:
    sys.path.insert(0, str(REGISTRY_DIR))

from path_boundary import is_protected_path as boundary_is_protected_path
from path_boundary import is_under_workspace as boundary_is_under_workspace
from path_boundary import preflight_target as boundary_preflight_target
from path_boundary import safe_resolve


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = REGISTRY_DIR / "drafts" / "federated-document-registry.v0.1.example.yaml"
DOCUMENT_VALIDATOR_PATH = REGISTRY_DIR / "validate-document-registry.py"

ALLOWED_STATUSES = {"draft", "pilot", "example", "active", "archived", "blocked"}

SECRET_PATTERNS = {
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    "openai_like_secret_key": re.compile(r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{20,}"),
    "aws_access_key_like": re.compile(r"(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])"),
}


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - depends on local environment.
        raise RuntimeError(f"YAML parser unavailable: {exc}") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("Federated registry YAML root must be a mapping.")
    return data


def load_document_validator() -> Any:
    spec = importlib.util.spec_from_file_location("document_registry_validator", DOCUMENT_VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load document registry validator: {DOCUMENT_VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def to_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {to_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(to_text(item) for item in value)
    if value is None:
        return ""
    return str(value)


def has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def add_finding(findings: list[dict[str, str]], rule_id: str, level: str, message: str) -> None:
    findings.append({"rule_id": rule_id, "level": level, "message": message})


def is_protected_path(path_value: Any) -> bool:
    return boundary_is_protected_path(path_value)


def resolve_workspace_path(path_value: Any) -> tuple[Path | None, str | None]:
    if not has_value(path_value):
        return None, None
    path = Path(str(path_value))
    if path.is_absolute():
        return safe_resolve(path)
    return safe_resolve(WORKSPACE_ROOT / path)


def is_under_workspace(path: Path) -> bool:
    return boundary_is_under_workspace(path, WORKSPACE_ROOT)


def validate_path(
    path_value: Any,
    findings: list[dict[str, str]],
    rule_id: str,
    label: str,
    must_be_dir: bool = False,
) -> Path | None:
    if not has_value(path_value):
        add_finding(findings, rule_id, "fail", f"{label} is missing")
        return None
    if is_protected_path(path_value):
        add_finding(findings, rule_id, "fail", f"{label} points to protected path: {path_value}")
        return None

    resolved, resolve_error = resolve_workspace_path(path_value)
    if resolve_error:
        add_finding(findings, rule_id, "fail", f"{label} could not be resolved: {resolve_error}")
        return None
    if resolved is None:
        add_finding(findings, rule_id, "fail", f"{label} could not be resolved")
        return None
    if is_protected_path(resolved):
        add_finding(findings, rule_id, "fail", f"{label} resolves to protected path: {path_value}")
        return None
    if not is_under_workspace(resolved):
        add_finding(findings, rule_id, "fail", f"{label} points outside workspace: {path_value}")
        return None
    if not resolved.exists():
        add_finding(findings, rule_id, "fail", f"{label} does not exist: {path_value}")
        return None
    if must_be_dir and not resolved.is_dir():
        add_finding(findings, rule_id, "fail", f"{label} is not a directory: {path_value}")
        return None
    if not must_be_dir and not resolved.is_file():
        add_finding(findings, rule_id, "fail", f"{label} is not a file: {path_value}")
        return None
    return resolved


def secret_pattern_hits(text: str) -> list[str]:
    return [pattern_id for pattern_id, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def claims_active_authority(entry: dict[str, Any]) -> bool:
    text = to_text(entry).lower()
    red_flags = ("active authority", "active workspace authority", "active authority data")
    safe_phrases = ("not active", "not active authority", "not active authority data")
    return any(flag in text for flag in red_flags) and not any(safe in text for safe in safe_phrases)


def validate_document_registry_path(
    registry_path: Path,
    expected_document_count: Any,
    document_validator: Any,
    findings: list[dict[str, str]],
) -> None:
    try:
        data = document_validator.load_yaml(registry_path)
        result = document_validator.validate_registry(data)
    except Exception as exc:
        add_finding(findings, "FDR-008", "fail", f"document registry validation raised error: {exc}")
        return

    if not result.get("passed"):
        add_finding(findings, "FDR-008", "fail", "document registry validator did not pass")

    if has_value(expected_document_count):
        actual_count = result.get("summary", {}).get("checked_documents")
        try:
            expected_count = int(expected_document_count)
            checked_count = int(actual_count)
        except (TypeError, ValueError):
            add_finding(
                findings,
                "FDR-009",
                "fail",
                f"expected_document_count must be an integer: {expected_document_count}",
            )
            return

        if expected_count != checked_count:
            add_finding(
                findings,
                "FDR-009",
                "fail",
                f"expected_document_count mismatch: expected {expected_count} got {checked_count}",
            )


def registered_document_paths_from_registry(registry_path: Path) -> set[str]:
    try:
        data = load_yaml(registry_path)
    except Exception:
        return set()

    documents = data.get("documents")
    if not isinstance(documents, list):
        return set()

    paths: set[str] = set()
    for doc in documents:
        if not isinstance(doc, dict):
            continue
        for field in ("canonical_path", "source_of_truth"):
            value = doc.get(field)
            if has_value(value):
                resolved, resolve_error = resolve_workspace_path(value)
                if not resolve_error and resolved and is_under_workspace(resolved):
                    try:
                        paths.add(resolved.relative_to(WORKSPACE_ROOT).as_posix())
                    except ValueError:
                        pass
    return paths


def iter_exception_entries(value: Any) -> list[Any]:
    if not has_value(value):
        return []
    return value if isinstance(value, list) else [value]


def validate_known_external_scope_entries(
    entry: dict[str, Any],
    findings: list[dict[str, str]],
    directory_root: Path | None,
    registered_paths: set[str],
) -> None:
    for index, known_entry in enumerate(iter_exception_entries(entry.get("known_external_scope"))):
        label = f"known_external_scope[{index}]"
        if not isinstance(known_entry, dict):
            add_finding(findings, "FDR-017", "fail", f"{label} must be a mapping")
            continue

        path_value = known_entry.get("path")
        known_path = validate_path(path_value, findings, "FDR-017", f"{label}.path")
        if not has_value(known_entry.get("reason")):
            add_finding(findings, "FDR-017", "fail", f"{label} is missing reason")
        if not has_value(known_entry.get("review_trigger")):
            add_finding(findings, "FDR-017", "fail", f"{label} is missing review_trigger")

        if known_path is not None and directory_root is not None:
            try:
                known_path.relative_to(directory_root)
            except ValueError:
                add_finding(
                    findings,
                    "FDR-017",
                    "fail",
                    f"{label}.path is outside directory_root: {path_value}",
                )

        if known_path is not None:
            try:
                normalized = known_path.relative_to(WORKSPACE_ROOT).as_posix()
            except ValueError:
                normalized = ""
            if normalized in registered_paths:
                add_finding(
                    findings,
                    "FDR-019",
                    "fail",
                    f"{label}.path is already registered and cannot be hidden as known_external_scope: {path_value}",
                )


def validate_archive_note_entries(entry: dict[str, Any], findings: list[dict[str, str]]) -> None:
    for index, archive_entry in enumerate(iter_exception_entries(entry.get("archive_notes"))):
        label = f"archive_notes[{index}]"
        if not isinstance(archive_entry, dict):
            add_finding(findings, "FDR-018", "fail", f"{label} must be a mapping")
            continue

        validate_path(archive_entry.get("path"), findings, "FDR-018", f"{label}.path")
        if not has_value(archive_entry.get("safe_use")):
            add_finding(findings, "FDR-018", "fail", f"{label} is missing safe_use")
        if not has_value(archive_entry.get("review_trigger")):
            add_finding(findings, "FDR-018", "fail", f"{label} is missing review_trigger")
        if not has_value(archive_entry.get("replacement")) and not has_value(archive_entry.get("no_replacement_reason")):
            add_finding(
                findings,
                "FDR-018",
                "fail",
                f"{label} is missing replacement or no_replacement_reason",
            )


def validate_registry_entry(entry: Any, index: int, document_validator: Any) -> dict[str, Any]:
    registry_id = f"registry[{index}]"
    findings: list[dict[str, str]] = []

    if not isinstance(entry, dict):
        return {
            "id": registry_id,
            "status": "FAIL",
            "registry_path": "",
            "findings": [
                {
                    "rule_id": "FDR-000",
                    "level": "fail",
                    "message": "registry entry must be a mapping",
                }
            ],
        }

    registry_id = str(entry.get("id") or registry_id)
    status = str(entry.get("status") or "")

    if not has_value(entry.get("id")):
        add_finding(findings, "FDR-001", "fail", "registry entry is missing id")

    if not has_value(entry.get("registry_path")):
        add_finding(findings, "FDR-002", "fail", "registry entry is missing registry_path")

    if not has_value(status):
        add_finding(findings, "FDR-004", "fail", "registry entry is missing status")
    elif status not in ALLOWED_STATUSES:
        add_finding(findings, "FDR-004", "fail", f"registry status is not allowed: {status}")

    if not has_value(entry.get("owner")):
        add_finding(findings, "FDR-005", "fail", "registry entry is missing owner")

    directory_root = validate_path(
        entry.get("directory_root"),
        findings,
        "FDR-006",
        "directory_root",
        must_be_dir=True,
    )
    registry_path = validate_path(
        entry.get("registry_path"),
        findings,
        "FDR-003",
        "registry_path",
    )

    if directory_root is not None and registry_path is not None:
        try:
            registry_path.relative_to(directory_root)
        except ValueError:
            add_finding(
                findings,
                "FDR-007",
                "fail",
                f"registry_path is not under directory_root: {entry.get('registry_path')}",
            )

    if has_value(entry.get("validator")):
        validate_path(entry.get("validator"), findings, "FDR-012", "validator")

    if has_value(entry.get("coverage_checker")):
        validate_path(entry.get("coverage_checker"), findings, "FDR-013", "coverage_checker")

    if status in {"draft", "pilot", "example"} and claims_active_authority(entry):
        add_finding(findings, "FDR-014", "fail", "draft/pilot/example appears to claim active authority")

    for pattern_id in secret_pattern_hits(to_text(entry)):
        add_finding(findings, "FDR-015", "fail", f"secret-like pattern found: {pattern_id}")

    if not has_value(entry.get("security_boundary")):
        add_finding(findings, "FDR-016", "warn", "registry entry is missing security_boundary")

    if registry_path is not None:
        validate_document_registry_path(
            registry_path,
            entry.get("expected_document_count"),
            document_validator,
            findings,
        )
        registered_paths = registered_document_paths_from_registry(registry_path)
    else:
        registered_paths = set()

    validate_known_external_scope_entries(entry, findings, directory_root, registered_paths)
    validate_archive_note_entries(entry, findings)

    levels = {finding["level"] for finding in findings}
    if "fail" in levels:
        result_status = "FAIL"
    elif "warn" in levels:
        result_status = "WARN"
    else:
        result_status = "PASS"

    return {
        "id": registry_id,
        "status": result_status,
        "registry_path": str(entry.get("registry_path") or ""),
        "findings": findings,
    }


def validate_federation(data: dict[str, Any], document_validator: Any | None = None) -> dict[str, Any]:
    document_validator = document_validator or load_document_validator()
    registry_findings: list[dict[str, str]] = []
    registries = data.get("registries")

    metadata = {key: value for key, value in data.items() if key != "registries"}
    for pattern_id in secret_pattern_hits(to_text(metadata)):
        add_finding(
            registry_findings,
            "FDR-015",
            "fail",
            f"secret-like pattern found in federation metadata: {pattern_id}",
        )

    if not isinstance(registries, list):
        registries = []
        add_finding(registry_findings, "FDR-ROOT", "fail", "federated registry is missing registries list")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for entry in registries:
        if not isinstance(entry, dict):
            continue
        entry_id = str(entry.get("id") or "")
        registry_path = str(entry.get("registry_path") or "")
        if entry_id:
            if entry_id in seen_ids:
                add_finding(registry_findings, "FDR-010", "fail", f"duplicate registry id: {entry_id}")
            seen_ids.add(entry_id)
        if registry_path:
            if registry_path in seen_paths:
                add_finding(registry_findings, "FDR-011", "fail", f"duplicate registry_path: {registry_path}")
            seen_paths.add(registry_path)

    registry_results = [
        validate_registry_entry(entry, index, document_validator)
        for index, entry in enumerate(registries)
    ]
    summary = {
        "checked_registries": len(registry_results),
        "pass": sum(1 for item in registry_results if item["status"] == "PASS"),
        "warn": sum(1 for item in registry_results if item["status"] == "WARN"),
        "fail": sum(1 for item in registry_results if item["status"] == "FAIL"),
    }
    passed = summary["fail"] == 0 and not any(
        finding["level"] == "fail" for finding in registry_findings
    )

    return {
        "schema_version": "agents-os.federated-document-registry.result.v0.1",
        "passed": passed,
        "summary": summary,
        "registry_findings": registry_findings,
        "registries": registry_results,
        "warnings": {
            "checker_is_read_only": True,
            "only_listed_registries_checked": True,
            "full_workspace_scan_performed": False,
            "database_or_vector_index_created": False,
            "authority_granted": False,
            "external_write_performed": False,
            "runtime_execution_performed": False,
            "formal_memory_registration": "not_performed",
        },
    }


def invalid_target_result(target: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema_version": "agents-os.federated-document-registry.result.v0.1",
        "passed": False,
        "summary": {
            "checked_registries": 0,
            "pass": 0,
            "warn": 0,
            "fail": 0,
        },
        "registry_findings": findings,
        "registries": [],
        "warnings": {
            "checker_is_read_only": True,
            "target_read_performed": False,
            "only_listed_registries_checked": False,
            "full_workspace_scan_performed": False,
            "database_or_vector_index_created": False,
            "authority_granted": False,
            "external_write_performed": False,
            "runtime_execution_performed": False,
            "formal_memory_registration": "not_performed",
        },
        "target": str(target),
    }


def preflight_target(target: Path) -> list[dict[str, str]]:
    return boundary_preflight_target(target, WORKSPACE_ROOT, "FDR-TARGET")


def format_text(result: dict[str, Any], target: Path) -> str:
    summary = result["summary"]
    lines = [
        f"Federated document registry: {target}",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        (
            "Summary: "
            f"registries={summary['checked_registries']} "
            f"pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}"
        ),
    ]
    if result["registry_findings"]:
        lines.append("")
        lines.append("Federation Findings:")
        for finding in result["registry_findings"]:
            lines.append(f"- {finding['rule_id']} {finding['level'].upper()}: {finding['message']}")

    lines.append("")
    lines.append("Registry Findings:")
    for item in result["registries"]:
        lines.append(f"- {item['id']}: {item['status']}")
        for finding in item["findings"]:
            lines.append(
                f"  - {finding['rule_id']} {finding['level'].upper()}: {finding['message']}"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local AGENTS OS Federated Document Registry YAML file.")
    parser.add_argument(
        "target",
        nargs="?",
        default=str(DEFAULT_TARGET),
        help="Federated Document Registry YAML file.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    target = Path(args.target)
    target_findings = preflight_target(target)
    if target_findings:
        result = invalid_target_result(target, target_findings)
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_text(result, target))
        return 1

    resolved_target, resolve_error = safe_resolve(target)
    if resolve_error or resolved_target is None:
        result = invalid_target_result(
            target,
            [
                {
                    "rule_id": "FDR-TARGET",
                    "level": "fail",
                    "message": f"target could not be resolved: {resolve_error or target}",
                }
            ],
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(format_text(result, target))
        return 1

    data = load_yaml(resolved_target)
    result = validate_federation(data)
    result["target"] = str(resolved_target)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result, resolved_target))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
