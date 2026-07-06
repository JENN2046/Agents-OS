#!/usr/bin/env python3
"""Validate an AGENTS OS governance registry YAML file.

This is a local scorecard checker. It reads registry YAML, checks object
metadata and boundary fields, then reports PASS/WARN/FAIL findings. It does
not execute registry objects or grant authority.
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

ALLOWED_STATUSES = {
    "active",
    "accepted",
    "draft",
    "example",
    "review_needed",
    "blocked",
    "deprecated",
    "archived",
    "rejected",
    "superseded",
}

ALLOWED_TYPES = {
    "policy_module",
    "router",
    "workflow",
    "task_envelope",
    "validator",
    "loop_runner",
    "registry",
    "receipt_set",
    "review_set",
    "runbook",
    "boundary_doc",
    "decision_record",
    "golden_path",
    "scorecard",
}

SCRIPT_TYPES = {"router", "validator", "loop_runner", "scorecard"}
BOUNDARY_TERMS = {
    "permission",
    "authority",
    "external",
    "runtime",
    "provider",
    "memory",
    "identity",
    "relation",
    "p3",
    "权限",
    "外部",
    "运行时",
    "记忆",
    "身份",
    "关系",
}

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
        raise ValueError("Registry YAML root must be a mapping.")
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


def contains_any(value: Any, terms: set[str]) -> bool:
    text = to_text(value).lower()
    return any(term.lower() in text for term in terms)


def authority_says_not_active(authority: Any) -> bool:
    text = to_text(authority).lower()
    return any(
        phrase in text
        for phrase in [
            "not active",
            "draft",
            "example",
            "not active authority",
            "not active enforcement",
            "not active data",
        ]
    )


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


def is_protected_path(path_value: Any) -> bool:
    return boundary_is_protected_path(path_value)


def is_under_workspace(path: Path) -> bool:
    return boundary_is_under_workspace(path, WORKSPACE_ROOT)


def validate_object(obj: Any, index: int) -> dict[str, Any]:
    object_id = f"object[{index}]"
    findings: list[dict[str, str]] = []

    if not isinstance(obj, dict):
        return {
            "id": object_id,
            "status": "FAIL",
            "findings": [
                {
                    "rule_id": "SC-000",
                    "level": "fail",
                    "message": "registry object must be a mapping",
                }
            ],
        }

    object_id = str(obj.get("id") or object_id)
    object_type = obj.get("type")
    status = obj.get("status")

    if not has_value(obj.get("id")):
        add_finding(findings, "SC-001", "fail", "object is missing id")

    if not has_value(object_type):
        add_finding(findings, "SC-002", "fail", "object is missing type")
    elif str(object_type) not in ALLOWED_TYPES:
        add_finding(findings, "SC-002A", "warn", f"object type is not in known list: {object_type}")

    if not has_value(status):
        add_finding(findings, "SC-003", "fail", "object is missing status")
    elif str(status) not in ALLOWED_STATUSES:
        add_finding(findings, "SC-004", "fail", f"status is not allowed: {status}")

    if str(status) == "active" and not has_value(obj.get("owner")):
        add_finding(findings, "SC-005", "fail", "active object is missing owner")

    if str(status) == "active" and not has_value(obj.get("authority")):
        add_finding(findings, "SC-006", "fail", "active object is missing authority")

    if not has_value(obj.get("red_zone")):
        add_finding(findings, "SC-007", "fail", "object is missing red_zone")

    path_text = str(obj.get("path", ""))
    needs_validation = str(object_type) in SCRIPT_TYPES or path_text.endswith(".py")
    if needs_validation and not has_value(obj.get("validation")):
        add_finding(findings, "SC-008", "warn", "script-like object is missing validation")

    boundary_related = contains_any(
        {
            "scope": obj.get("scope"),
            "authority": obj.get("authority"),
            "yellow_zone": obj.get("yellow_zone"),
            "red_zone": obj.get("red_zone"),
        },
        BOUNDARY_TERMS,
    )
    if boundary_related and not has_value(obj.get("last_review")):
        add_finding(findings, "SC-009", "fail", "boundary-related object is missing last_review")

    if str(status) in {"draft", "example"} and contains_any(obj.get("authority"), {"active"}):
        if not authority_says_not_active(obj.get("authority")):
            add_finding(
                findings,
                "SC-010",
                "fail",
                "draft/example authority appears to describe active authority",
            )

    if str(status) == "example" and contains_any(obj, {"active authority", "active data"}):
        if not authority_says_not_active(obj.get("authority")):
            add_finding(findings, "SC-011", "fail", "example appears to describe active authority")

    object_text = to_text(obj)
    for pattern_id, pattern in SECRET_PATTERNS.items():
        if pattern.search(object_text):
            add_finding(findings, "SC-012", "fail", f"secret-like pattern found: {pattern_id}")

    unsafe_authority_text = " ".join(
        [
            to_text(obj.get("authority")),
            to_text(obj.get("outputs")),
            to_text(obj.get("green_zone")),
        ]
    ).lower()
    if "authorize external write" in unsafe_authority_text or "authorize external writes" in unsafe_authority_text:
        add_finding(findings, "SC-013", "fail", "object appears to authorize external writes")

    if "bypass jenn" in unsafe_authority_text or "bypass p3" in unsafe_authority_text:
        add_finding(findings, "SC-014", "fail", "object appears to authorize bypassing Jenn or P3")

    if not has_value(obj.get("last_receipt")):
        add_finding(findings, "SC-015", "warn", "object is missing last_receipt")

    if boundary_related and not has_value(obj.get("last_review")):
        add_finding(findings, "SC-016", "warn", "boundary-related object is missing last_review")

    levels = {finding["level"] for finding in findings}
    if "fail" in levels:
        result_status = "FAIL"
    elif "warn" in levels:
        result_status = "WARN"
    else:
        result_status = "PASS"

    return {
        "id": object_id,
        "status": result_status,
        "findings": findings,
    }


def validate_registry(data: dict[str, Any]) -> dict[str, Any]:
    objects = data.get("objects")
    registry_findings: list[dict[str, str]] = []

    if not isinstance(objects, list):
        objects = []
        add_finding(registry_findings, "SC-ROOT", "fail", "registry is missing objects list")

    object_results = [validate_object(obj, index) for index, obj in enumerate(objects)]

    summary = {
        "checked_objects": len(object_results),
        "pass": sum(1 for item in object_results if item["status"] == "PASS"),
        "warn": sum(1 for item in object_results if item["status"] == "WARN"),
        "fail": sum(1 for item in object_results if item["status"] == "FAIL"),
    }
    passed = summary["fail"] == 0 and not any(
        finding["level"] == "fail" for finding in registry_findings
    )

    return {
        "schema_version": "agents-os.governance-scorecard.result.v0.1",
        "passed": passed,
        "summary": summary,
        "registry_findings": registry_findings,
        "objects": object_results,
        "warnings": {
            "scorecard_is_read_only": True,
            "authority_granted": False,
            "external_write_performed": False,
            "runtime_execution_performed": False,
            "formal_memory_registration": "not_performed",
        },
    }


def invalid_target_result(target: Path, findings: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schema_version": "agents-os.governance-scorecard.result.v0.1",
        "passed": False,
        "summary": {
            "checked_objects": 0,
            "pass": 0,
            "warn": 0,
            "fail": 0,
        },
        "registry_findings": findings,
        "objects": [],
        "warnings": {
            "scorecard_is_read_only": True,
            "target_read_performed": False,
            "authority_granted": False,
            "external_write_performed": False,
            "runtime_execution_performed": False,
            "formal_memory_registration": "not_performed",
        },
        "target": str(target),
    }


def preflight_target(target: Path) -> list[dict[str, str]]:
    return boundary_preflight_target(target, WORKSPACE_ROOT, "SC-TARGET")


def format_text(result: dict[str, Any], target: Path) -> str:
    summary = result["summary"]
    lines = [
        f"Governance registry: {target}",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        (
            "Summary: "
            f"objects={summary['checked_objects']} "
            f"pass={summary['pass']} warn={summary['warn']} fail={summary['fail']}"
        ),
    ]

    if result["registry_findings"]:
        lines.append("")
        lines.append("Registry Findings:")
        for finding in result["registry_findings"]:
            lines.append(f"- {finding['rule_id']} {finding['level'].upper()}: {finding['message']}")

    lines.append("")
    lines.append("Object Findings:")
    for item in result["objects"]:
        lines.append(f"- {item['id']}: {item['status']}")
        for finding in item["findings"]:
            lines.append(
                f"  - {finding['rule_id']} {finding['level'].upper()}: {finding['message']}"
            )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local AGENTS OS governance registry YAML file.")
    parser.add_argument(
        "target",
        nargs="?",
        default=str(Path(__file__).resolve().parent / "drafts" / "agents-os-governance-registry.v0.1.example.yaml"),
        help="Governance registry YAML file to validate.",
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
                    "rule_id": "SC-TARGET",
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
