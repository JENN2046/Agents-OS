#!/usr/bin/env python3
"""Validate an AGENTS OS task envelope markdown file.

This is a local structure checker. It reads markdown and JSON rules, then
reports missing sections or warning signals. It does not execute the task.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate(text: str, rules: dict[str, Any]) -> dict[str, Any]:
    missing_required = [
        item for item in rules.get("required_text", []) if item not in text
    ]

    missing_groups: list[dict[str, str]] = []
    for group in rules.get("required_any_groups", []):
        if not any(option in text for option in group.get("any_of", [])):
            missing_groups.append(
                {
                    "id": str(group.get("id", "")),
                    "description": str(group.get("description", "")),
                }
            )

    warnings: list[dict[str, Any]] = []
    for warning in rules.get("warning_if_missing", []):
        missing_terms = [
            term for term in warning.get("terms", []) if term not in text
        ]
        if missing_terms:
            warnings.append(
                {
                    "id": warning.get("id", ""),
                    "description": warning.get("description", ""),
                    "missing_terms": missing_terms,
                }
            )

    forbidden_hits = [
        item for item in rules.get("forbidden_text", []) if item in text
    ]
    forbidden_pattern_hits: list[str] = []
    for item in rules.get("forbidden_patterns", []):
        pattern = str(item.get("pattern", ""))
        if pattern and re.search(pattern, text):
            forbidden_pattern_hits.append(str(item.get("id", "unnamed_pattern")))

    passed = (
        not missing_required
        and not missing_groups
        and not forbidden_hits
        and not forbidden_pattern_hits
    )
    return {
        "passed": passed,
        "missing_required_text": missing_required,
        "missing_required_groups": missing_groups,
        "warnings": warnings,
        "forbidden_hits": forbidden_hits,
        "forbidden_pattern_hits": forbidden_pattern_hits,
    }


def format_text(result: dict[str, Any], target: Path) -> str:
    lines = [
        f"Task envelope: {target}",
        f"Status: {'PASS' if result['passed'] else 'FAIL'}",
    ]

    if result["missing_required_text"]:
        lines.append("")
        lines.append("Missing Required Text:")
        lines.extend(f"- {item}" for item in result["missing_required_text"])

    if result["missing_required_groups"]:
        lines.append("")
        lines.append("Missing Required Groups:")
        for group in result["missing_required_groups"]:
            lines.append(f"- {group['id']}: {group['description']}")

    if result["forbidden_hits"]:
        lines.append("")
        lines.append("Forbidden Text Hits:")
        lines.extend(f"- {item}" for item in result["forbidden_hits"])

    if result["forbidden_pattern_hits"]:
        lines.append("")
        lines.append("Forbidden Pattern Hits:")
        lines.extend(f"- {item}" for item in result["forbidden_pattern_hits"])

    if result["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        for warning in result["warnings"]:
            terms = ", ".join(warning["missing_terms"])
            lines.append(f"- {warning['id']}: missing {terms}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a local AGENTS OS task envelope.")
    parser.add_argument("target", help="Markdown task envelope to validate.")
    parser.add_argument(
        "--rules",
        default=None,
        help="Validation rules JSON. Defaults to validation-rules.json next to this script.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    target = Path(args.target).resolve()
    rules_path = Path(args.rules).resolve() if args.rules else script_dir / "validation-rules.json"

    rules = load_json(rules_path)
    text = read_text(target)
    result = validate(text, rules)
    result["target"] = str(target)
    result["rules"] = str(rules_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result, target))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
