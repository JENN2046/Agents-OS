#!/usr/bin/env python3
"""Check life-core Document Registry coverage against policy-index.json.

This is a local read-only coverage check. It verifies that every policy module
listed in `policy-index.json` has a matching record in the life-core Document
Registry pilot. It does not scan the full workspace or grant authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_REGISTRY = ROOT / "drafts" / "document-registry.v0.1.example.yaml"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be a mapping: {path}")
    return data


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


def module_files(policy_index: dict[str, Any]) -> set[str]:
    modules = policy_index.get("modules", [])
    files: set[str] = set()
    if not isinstance(modules, list):
        return files
    for module in modules:
        if isinstance(module, dict) and isinstance(module.get("file"), str):
            files.add(module["file"])
    return files


def registry_paths(document_registry: dict[str, Any]) -> set[str]:
    documents = document_registry.get("documents", [])
    paths: set[str] = set()
    if not isinstance(documents, list):
        return paths
    for document in documents:
        if isinstance(document, dict) and isinstance(document.get("canonical_path"), str):
            paths.add(document["canonical_path"])
    return paths


def validate_coverage(policy_index: dict[str, Any], document_registry: dict[str, Any]) -> dict[str, Any]:
    expected = {
        f"control-plane/policies/life-core/{file_name}"
        for file_name in module_files(policy_index)
    }
    actual = registry_paths(document_registry)
    missing = sorted(expected - actual)

    return {
        "schema_version": "agents-os.life-core-document-coverage.result.v0.1",
        "passed": not missing,
        "summary": {
            "expected_policy_modules": len(expected),
            "registered_policy_modules": len(expected & actual),
            "missing_policy_modules": len(missing),
        },
        "missing": missing,
        "warnings": {
            "checker_is_read_only": True,
            "full_workspace_scan_performed": False,
            "authority_granted": False,
        },
    }


def format_text(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
        (
            "Summary: "
            f"expected={summary['expected_policy_modules']} "
            f"registered={summary['registered_policy_modules']} "
            f"missing={summary['missing_policy_modules']}"
        ),
    ]
    if result["missing"]:
        lines.append("")
        lines.append("Missing policy module records:")
        for path in result["missing"]:
            lines.append(f"- {path}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate life-core document registry coverage.")
    parser.add_argument(
        "registry",
        nargs="?",
        default=str(DEFAULT_REGISTRY),
        help="Life-core Document Registry YAML file.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    policy_index = load_json(ROOT / "policy-index.json")
    document_registry = load_yaml(Path(args.registry).resolve())
    result = validate_coverage(policy_index, document_registry)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
