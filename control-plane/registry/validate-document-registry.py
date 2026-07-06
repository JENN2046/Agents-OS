#!/usr/bin/env python3
"""Validate an AGENTS OS document registry YAML file.

This is a local read-only checker. It reads a document registry, checks the
records and the listed safe paths, then reports PASS/WARN/FAIL findings. It
does not scan the whole workspace, execute registered documents, create an
index database, write external systems, or grant authority.
"""

from __future__ import annotations

import argparse
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

ALLOWED_DOC_TYPES = {
    "index",
    "overview",
    "tutorial",
    "how_to",
    "runbook",
    "reference",
    "explanation",
    "decision_record",
    "policy",
    "registry",
    "contract",
    "schema",
    "template",
    "example",
    "receipt",
    "review",
    "incident_review",
    "archive_note",
}

ALLOWED_STATUSES = {
    "draft",
    "review_needed",
    "active",
    "accepted",
    "superseded",
    "deprecated",
    "archived",
    "example",
    "blocked",
}

ACTIVE_STATUSES = {"active", "accepted"}

REQUIRED_VALUE_FIELDS_BY_STATUS = {
    status: {
        "title",
        "scope",
        "owner",
        "canonical_path",
        "source_of_truth",
        "last_reviewed",
        "review_by",
        "freshness",
        "security_boundary",
        "validation",
    }
    for status in ALLOWED_STATUSES
}

REQUIRED_KEY_FIELDS_BY_STATUS = {
    status: {"supersedes", "superseded_by", "related"}
    for status in ALLOWED_STATUSES
}

ALLOWED_LIFECYCLE_TRANSITIONS = {
    ("draft", "review_needed"),
    ("draft", "active"),
    ("draft", "accepted"),
    ("draft", "archived"),
    ("review_needed", "draft"),
    ("review_needed", "active"),
    ("review_needed", "accepted"),
    ("active", "superseded"),
    ("active", "deprecated"),
    ("active", "archived"),
    ("accepted", "superseded"),
    ("accepted", "deprecated"),
    ("accepted", "archived"),
    ("deprecated", "superseded"),
    ("deprecated", "archived"),
    ("superseded", "archived"),
    ("example", "example"),
    ("blocked", "draft"),
    ("blocked", "archived"),
}

SECRET_PATTERNS = {
    "private_key_block": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE),
    "openai_like_secret_key": re.compile(r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{20,}"),
    "aws_access_key_like": re.compile(r"(?<![A-Z0-9])AKIA[A-Z0-9]{16}(?![A-Z0-9])"),
}

README_BOUNDARY_TERMS = ("active", "draft", "example")


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception as exc:  # pragma: no cover - depends on local environment.
        raise RuntimeError(f"YAML parser unavailable: {exc}") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError("Document registry YAML root must be a mapping.")
    return data


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


def add_finding(
    findings: list[dict[str, str]],
    rule_id: str,
    level: str,
    message: str,
) -> None:
    findings.append(
        {
            "rule_id": rule_id,
            "level": level,
            "message": message,
        }
    )


def resolve_workspace_path(path_value: Any) -> tuple[Path | None, str | None]:
    if not has_value(path_value):
        return None, None

    path = Path(str(path_value))
    if path.is_absolute():
        return safe_resolve(path)
    return safe_resolve(WORKSPACE_ROOT / path)


def is_protected_path(path_value: Any) -> bool:
    return boundary_is_protected_path(path_value)


def path_exists(path_value: Any) -> bool:
    resolved, resolve_error = resolve_workspace_path(path_value)
    if resolve_error:
        return False
    return bool(resolved and resolved.exists())


def is_under_workspace(path: Path) -> bool:
    return boundary_is_under_workspace(path, WORKSPACE_ROOT)


def validate_path_reference(
    path_value: Any,
    findings: list[dict[str, str]],
    protected_rule_id: str,
    missing_rule_id: str,
    missing_level: str,
    label: str,
) -> Path | None:
    if not has_value(path_value):
        return None

    if is_protected_path(path_value):
        add_finding(findings, protected_rule_id, "fail", f"{label} points to protected path: {path_value}")
        return None

    resolved, resolve_error = resolve_workspace_path(path_value)
    if resolve_error:
        add_finding(findings, protected_rule_id, "fail", f"{label} could not be resolved: {resolve_error}")
        return None
    if resolved is None:
        return None

    if is_protected_path(resolved):
        add_finding(findings, protected_rule_id, "fail", f"{label} resolves to protected path: {path_value}")
        return None

    if not is_under_workspace(resolved):
        add_finding(findings, protected_rule_id, "fail", f"{label} points outside workspace: {path_value}")
        return None

    if not resolved.exists():
        add_finding(findings, missing_rule_id, missing_level, f"{label} does not exist: {path_value}")
        return None

    return resolved


def secret_pattern_hits(text: str) -> list[str]:
    return [pattern_id for pattern_id, pattern in SECRET_PATTERNS.items() if pattern.search(text)]


def wording_claims_active_authority(record: dict[str, Any]) -> bool:
    text = to_text(record).lower()
    red_flags = (
        "active authority",
        "active local authority",
        "active authority data",
        "生效规则",
        "正式生效",
        "正式规则",
    )
    safe_phrases = (
        "not active authority",
        "not active authority data",
        "not active registry data",
        "不是 active",
        "不能当 active",
        "not active",
    )
    return any(flag in text for flag in red_flags) and not any(
        safe_phrase in text for safe_phrase in safe_phrases
    )


def validate_required_field_matrix(doc: dict[str, Any], status: str, findings: list[dict[str, str]]) -> None:
    """Validate the explicit Stage 1 field matrix.

    Some lifecycle fields are required as keys but may intentionally be null or
    empty, for example `superseded_by` on current documents and `related` on
    standalone documents.
    """

    value_fields = REQUIRED_VALUE_FIELDS_BY_STATUS.get(status, set())
    key_fields = REQUIRED_KEY_FIELDS_BY_STATUS.get(status, set())

    missing_values = sorted(field for field in value_fields if not has_value(doc.get(field)))
    missing_keys = sorted(field for field in key_fields if field not in doc)

    if missing_values or missing_keys:
        missing = ", ".join(missing_values + missing_keys)
        add_finding(findings, "DOC-019", "fail", f"required metadata is missing: {missing}")


def validate_lifecycle_transition(doc: dict[str, Any], status: str, findings: list[dict[str, str]]) -> None:
    transition = doc.get("lifecycle_transition")
    if transition is None:
        return
    if not isinstance(transition, dict):
        add_finding(findings, "DOC-020", "fail", "lifecycle_transition must be a mapping")
        return

    from_status = str(transition.get("from") or "")
    to_status = str(transition.get("to") or status)
    if from_status not in ALLOWED_STATUSES:
        add_finding(findings, "DOC-020", "fail", f"lifecycle_transition.from is not allowed: {from_status}")
        return
    if to_status not in ALLOWED_STATUSES:
        add_finding(findings, "DOC-020", "fail", f"lifecycle_transition.to is not allowed: {to_status}")
        return
    if to_status != status:
        add_finding(
            findings,
            "DOC-020",
            "fail",
            f"lifecycle_transition.to must match document status: {to_status} != {status}",
        )
        return
    if (from_status, to_status) not in ALLOWED_LIFECYCLE_TRANSITIONS:
        add_finding(
            findings,
            "DOC-020",
            "fail",
            f"lifecycle transition is not allowed: {from_status} -> {to_status}",
        )


def read_safe_text(
    path_value: Any,
    findings: list[dict[str, str]],
    protected_rule_id: str,
    missing_rule_id: str,
    missing_level: str,
    label: str,
) -> str:
    resolved = validate_path_reference(
        path_value,
        findings,
        protected_rule_id,
        missing_rule_id,
        missing_level,
        label,
    )
    if resolved is None:
        return ""

    if not resolved.is_file():
        return ""

    try:
        return resolved.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        add_finding(findings, missing_rule_id, "warn", f"{label} could not be read: {path_value}: {exc}")
        return ""


def validate_document(doc: Any, index: int) -> dict[str, Any]:
    document_id = f"document[{index}]"
    findings: list[dict[str, str]] = []

    if not isinstance(doc, dict):
        return {
            "id": document_id,
            "status": "FAIL",
            "findings": [
                {
                    "rule_id": "DOC-000",
                    "level": "fail",
                    "message": "document record must be a mapping",
                }
            ],
        }

    document_id = str(doc.get("id") or document_id)
    doc_type = doc.get("doc_type")
    status = str(doc.get("status") or "")

    if not has_value(doc.get("id")):
        add_finding(findings, "DOC-001", "fail", "document is missing id")

    if not has_value(doc_type):
        add_finding(findings, "DOC-002", "fail", "document is missing doc_type")
    elif str(doc_type) not in ALLOWED_DOC_TYPES:
        add_finding(findings, "DOC-003", "fail", f"doc_type is not allowed: {doc_type}")

    if not has_value(doc.get("status")):
        add_finding(findings, "DOC-004", "fail", "document is missing status")
    elif status not in ALLOWED_STATUSES:
        add_finding(findings, "DOC-004", "fail", f"status is not allowed: {status}")
    else:
        validate_required_field_matrix(doc, status, findings)
        validate_lifecycle_transition(doc, status, findings)

    if status in ACTIVE_STATUSES and not has_value(doc.get("owner")):
        add_finding(findings, "DOC-005", "fail", "active/accepted document is missing owner")

    canonical_path = doc.get("canonical_path")
    if status in ACTIVE_STATUSES and not has_value(canonical_path):
        add_finding(findings, "DOC-006", "fail", "active/accepted document is missing canonical_path")

    canonical_text = ""
    if has_value(canonical_path):
        canonical_text = read_safe_text(
            canonical_path,
            findings,
            "DOC-017",
            "DOC-007",
            "fail",
            "canonical_path",
        )

    source_of_truth = doc.get("source_of_truth")
    source_text = ""
    if has_value(source_of_truth):
        source_text = read_safe_text(
            source_of_truth,
            findings,
            "DOC-018",
            "DOC-008",
            "fail" if status in ACTIVE_STATUSES else "warn",
            "source_of_truth",
        )
    elif status in ACTIVE_STATUSES:
        add_finding(findings, "DOC-008", "fail", "active/accepted document is missing source_of_truth")

    if status in {"draft", "example"} and wording_claims_active_authority(doc):
        add_finding(findings, "DOC-009", "fail", "draft/example appears to claim active authority")

    if status == "superseded" and not has_value(doc.get("superseded_by")):
        add_finding(findings, "DOC-010", "warn", "superseded document is missing superseded_by")

    related = doc.get("related") or []
    if isinstance(related, str):
        related = [related]
    if isinstance(related, list):
        for related_path in related:
            if has_value(related_path):
                validate_path_reference(
                    related_path,
                    findings,
                    "DOC-011",
                    "DOC-011",
                    "warn",
                    "related",
                )

    if status in ACTIVE_STATUSES and not has_value(doc.get("last_reviewed")):
        add_finding(findings, "DOC-012", "fail", "active/accepted document is missing last_reviewed")

    if status in ACTIVE_STATUSES and not has_value(doc.get("review_by")):
        add_finding(findings, "DOC-013", "fail", "active/accepted document is missing review_by")

    checked_text = to_text(doc)
    if canonical_text:
        checked_text = f"{checked_text}\n{canonical_text}"
    if source_text:
        checked_text = f"{checked_text}\n{source_text}"
    for pattern_id in secret_pattern_hits(checked_text):
        add_finding(findings, "DOC-014", "fail", f"secret-like pattern found: {pattern_id}")

    if not has_value(doc.get("security_boundary")):
        add_finding(findings, "DOC-015", "warn", "document is missing security_boundary")

    if str(doc_type) == "index" and str(canonical_path).endswith("README.md") and canonical_text:
        lowered = canonical_text.lower()
        missing_terms = [term for term in README_BOUNDARY_TERMS if term not in lowered]
        if missing_terms:
            add_finding(
                findings,
                "DOC-016",
                "warn",
                f"README is missing active/draft/example boundary language: {', '.join(missing_terms)}",
            )

    levels = {finding["level"] for finding in findings}
    if "fail" in levels:
        result_status = "FAIL"
    elif "warn" in levels:
        result_status = "WARN"
    else:
        result_status = "PASS"

    return {
        "id": document_id,
        "status": result_status,
        "findings": findings,
    }


def validate_registry(data: dict[str, Any]) -> dict[str, Any]:
    registry_findings: list[dict[str, str]] = []
    documents = data.get("documents")

    if not isinstance(documents, list):
        documents = []
        add_finding(registry_findings, "DOC-ROOT", "fail", "registry is missing documents list")

    document_results = [validate_document(doc, index) for index, doc in enumerate(documents)]
    summary = {
        "checked_documents": len(document_results),
        "pass": sum(1 for item in document_results if item["status"] == "PASS"),
        "warn": sum(1 for item in document_results if item["status"] == "WARN"),
        "fail": sum(1 for item in document_results if item["status"] == "FAIL"),
    }
    passed = summary["fail"] == 0 and not any(
        finding["level"] == "fail" for finding in registry_findings
    )

    return {
        "schema_version": "agents-os.documentation-scorecard.result.v0.1",
        "passed": passed,
        "summary": summary,
        "registry_findings": registry_findings,
        "documents": document_results,
        "warnings": {
            "checker_is_read_only": True,
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
        "schema_version": "agents-os.documentation-scorecard.result.v0.1",
        "passed": False,
        "summary": {
            "checked_documents": 0,
            "pass": 0,
            "warn": 0,
            "fail": 0,
        },
        "registry_findings": findings,
        "documents": [],
        "warnings": {
            "checker_is_read_only": True,
            "target_read_performed": False,
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
    return boundary_preflight_target(target, WORKSPACE_ROOT, "DOC-TARGET")


def format_text(result: dict[str, Any], target: Path) -> str:
    summary = result["summary"]
    lines = [
        f"Document registry: {target}",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        (
            "Summary: "
            f"documents={summary['checked_documents']} "
            f"pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}"
        ),
    ]

    if result["registry_findings"]:
        lines.append("")
        lines.append("Registry Findings:")
        for finding in result["registry_findings"]:
            lines.append(f"- {finding['rule_id']} {finding['level'].upper()}: {finding['message']}")

    lines.append("")
    lines.append("Document Findings:")
    for item in result["documents"]:
        lines.append(f"- {item['id']}: {item['status']}")
        for finding in item["findings"]:
            lines.append(
                f"  - {finding['rule_id']} {finding['level'].upper()}: {finding['message']}"
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local AGENTS OS document registry YAML file.")
    parser.add_argument(
        "target",
        nargs="?",
        default=str(Path(__file__).resolve().parent / "drafts" / "document-registry.v0.1.example.yaml"),
        help="Document registry YAML file to validate.",
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
                    "rule_id": "DOC-TARGET",
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
    result = validate_registry(data)
    result["target"] = str(resolved_target)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result, resolved_target))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
