#!/usr/bin/env python3
"""Run a local AGENTS OS task-envelope preflight loop.

The loop reads one task envelope, extracts its policy-router action, runs the
life-core policy router, runs the task-envelope validator, and writes a local
receipt. It does not execute the task described by the envelope.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from datetime import date
from pathlib import Path
from types import ModuleType
from typing import Any


TASK_DIR = Path(__file__).resolve().parent
POLICY_ROOT = TASK_DIR.parent / "policies" / "life-core"

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
    re.compile(r"(?<![A-Za-z0-9_])sk-[A-Za-z0-9_-]{8,}"),
]


def load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def redact_sensitive(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return redact_sensitive(value)
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize(item) for key, item in value.items()}
    return value


def extract_code_block_after(text: str, marker: str) -> str:
    marker_index = text.find(marker)
    if marker_index == -1:
        return ""

    fence_start = text.find("```", marker_index)
    if fence_start == -1:
        return ""

    content_start = text.find("\n", fence_start)
    if content_start == -1:
        return ""

    fence_end = text.find("```", content_start + 1)
    if fence_end == -1:
        return ""

    return text[content_start + 1 : fence_end].strip()


def extract_action(text: str) -> str:
    action = extract_code_block_after(text, "行动描述：")
    placeholders = (
        "",
        "填写：",
        "填写给 policy-router 的一句话：",
    )
    if action in placeholders or action.startswith("填写"):
        return ""
    return action


def selected_options(text: str, options: list[str]) -> list[str]:
    return [option for option in options if f"[x] {option}" in text]


def route_missing_action() -> dict[str, Any]:
    return {
        "router_id": "life-core.policy-router.v0.1",
        "schema_version": "life-core.policy-router.result.v0.1",
        "action": "",
        "decision": "needs_classification",
        "permission_level": "unknown",
        "confidence": "low",
        "reason": "No usable action description was found in the task envelope.",
        "required_modules": ["permission-levels.md", "evidence-levels.md"],
        "required_evidence": ["manual_review_note"],
        "denied_boundaries": ["self_authorization"],
        "next_steps": [
            "Fill the policy-router action description.",
            "Run this task-envelope loop again before execution.",
        ],
        "matched_rules": [],
        "warnings": {
            "missing_modules": [],
            "router_is_read_only": True,
            "formal_memory_registration": "not_performed",
        },
    }


def gate_from_results(
    validation_result: dict[str, Any],
    router_result: dict[str, Any],
) -> dict[str, str]:
    decision = str(router_result.get("decision", "needs_classification"))
    permission = str(router_result.get("permission_level", "unknown"))

    if validation_result["forbidden_hits"] or validation_result["forbidden_pattern_hits"]:
        return {
            "status": "FORBIDDEN",
            "gate": "禁止",
            "color_zone": "红色区",
            "automation": "不能做，只能写边界说明或预案。",
        }

    if decision in {"blocked", "proposal_only"}:
        return {
            "status": "FORBIDDEN",
            "gate": "禁止",
            "color_zone": "红色区",
            "automation": "不能执行，只能写边界说明或安全预案。",
        }

    if decision == "needs_activation":
        return {
            "status": "NEEDS_JENN_CONFIRMATION",
            "gate": "需要 Jenn 明确确认",
            "color_zone": "红色区",
            "automation": "停止执行，先准备 preflight report 或 Activation package。",
        }

    if not validation_result["passed"]:
        return {
            "status": "NEEDS_ENVELOPE_FIX",
            "gate": "需要补齐做事单",
            "color_zone": "黄色区",
            "automation": "先补齐做事单结构，再重新预检。",
        }

    if decision == "allowed":
        return {
            "status": "ALLOW",
            "gate": "允许",
            "color_zone": "绿色区",
            "automation": "可以在做事单写明的本地安全范围内自动推进。",
        }

    if decision == "needs_classification" and permission == "yellow_zone_draft":
        return {
            "status": "DRAFT_ONLY",
            "gate": "需要草案",
            "color_zone": "黄色区",
            "automation": "只能做本地草案、收据和必要复核，不能当作正式生效。",
        }

    if decision == "needs_classification":
        return {
            "status": "NEEDS_REVIEW",
            "gate": "需要复核",
            "color_zone": "黄色区",
            "automation": "先人工复核边界，不能自动执行。",
        }

    return {
        "status": "NEEDS_REVIEW",
        "gate": "需要复核",
        "color_zone": "黄色区",
        "automation": "路由结果不在已知门类里，先复核再继续。",
    }


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return slug or "task-envelope"


def unique_receipt_path(receipt_dir: Path, target: Path, run_date: str) -> Path:
    slug = slugify(target.stem)
    base = receipt_dir / f"{run_date}-task-envelope-loop-{slug}.md"
    if not base.exists():
        return base

    for index in range(2, 1000):
        candidate = receipt_dir / f"{run_date}-task-envelope-loop-{slug}-{index}.md"
        if not candidate.exists():
            return candidate

    raise RuntimeError(f"Unable to find an unused receipt path in {receipt_dir}")


def format_markdown_receipt(result: dict[str, Any]) -> str:
    validation = result["validation"]
    router = result["router"]
    gate = result["gate"]
    target = result["target"]
    selected = result["envelope_selected"]
    receipt_slug = slugify(Path(target).stem)

    lines = [
        "# Task Envelope Loop Receipt",
        "",
        f"Receipt ID: `task-envelope-loop-{result['run_date']}-{receipt_slug}`",
        f"Date: {result['run_date']}",
        "Executor: local task-envelope loop",
        "Classification: `A2_local_control_plane_check`",
        f"Target: `{target}`",
        "",
        "## Action",
        "",
        "```text",
        result["action"] or "No usable action description found.",
        "```",
        "",
        "## Gate Result",
        "",
        f"- Status: `{gate['status']}`",
        f"- Gate: {gate['gate']}",
        f"- Routed color zone: {gate['color_zone']}",
        f"- Automation: {gate['automation']}",
        "",
        "## Envelope Signals",
        "",
        f"- Selected color zone: {', '.join(selected['color_zones']) or 'none'}",
        f"- Selected automation: {', '.join(selected['automation']) or 'none'}",
        "",
        "## Policy Router",
        "",
        f"- Decision: `{router['decision']}`",
        f"- Permission: `{router['permission_level']}`",
        f"- Confidence: `{router['confidence']}`",
        f"- Reason: {router['reason']}",
        "",
        "Required evidence:",
    ]
    lines.extend(f"- `{item}`" for item in router.get("required_evidence", []))
    lines.append("")
    lines.append("Denied boundaries:")
    lines.extend(f"- `{item}`" for item in router.get("denied_boundaries", []))
    lines.extend(
        [
            "",
            "## Validator",
            "",
            f"- Status: `{'PASS' if validation['passed'] else 'FAIL'}`",
            f"- Missing required text: `{len(validation['missing_required_text'])}`",
            f"- Missing required groups: `{len(validation['missing_required_groups'])}`",
            f"- Warnings: `{len(validation['warnings'])}`",
            f"- Forbidden text hits: `{len(validation['forbidden_hits'])}`",
            f"- Forbidden pattern hits: `{len(validation['forbidden_pattern_hits'])}`",
            "",
            "## Boundary",
            "",
            "- This loop did not execute the task in the envelope.",
            "- This loop did not write to external systems.",
            "- This loop did not call runtime, provider, plugin, or paid services.",
            "- This loop did not register formal Memory.",
            "- This loop generated only this local receipt.",
            "",
            "## Continuation",
            "",
            "`COMPLETED`",
        ]
    )
    return "\n".join(lines) + "\n"


def write_receipt(result: dict[str, Any], receipt_dir: Path) -> Path:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    target = Path(result["target"])
    receipt_path = unique_receipt_path(receipt_dir, target, result["run_date"])
    receipt_path.write_text(format_markdown_receipt(result), encoding="utf-8")
    return receipt_path


def run_loop(
    target: Path,
    *,
    rules_path: Path | None = None,
    policy_root: Path | None = None,
    receipt_dir: Path | None = None,
    write_local_receipt: bool = True,
    run_date: str | None = None,
) -> dict[str, Any]:
    target = target.resolve()
    rules_path = rules_path.resolve() if rules_path else TASK_DIR / "validation-rules.json"
    policy_root = policy_root.resolve() if policy_root else POLICY_ROOT
    receipt_dir = receipt_dir.resolve() if receipt_dir else TASK_DIR / "receipts"
    run_date = run_date or date.today().isoformat()

    validator = load_module("task_envelope_validator", TASK_DIR / "validate-task-envelope.py")
    router = load_module("life_core_policy_router", policy_root / "policy-router.py")

    rules = validator.load_json(rules_path)
    text = validator.read_text(target)
    validation_result = validator.validate(text, rules)
    action = extract_action(text)
    router_result = router.route_action(action, policy_root) if action else route_missing_action()
    gate = gate_from_results(validation_result, router_result)

    result: dict[str, Any] = {
        "schema_version": "agents-os.task-envelope.loop.result.v0.1",
        "run_date": run_date,
        "target": str(target),
        "rules": str(rules_path),
        "policy_root": str(policy_root),
        "action": redact_sensitive(action),
        "gate": gate,
        "router": sanitize(router_result),
        "validation": sanitize(validation_result),
        "envelope_selected": {
            "color_zones": selected_options(text, ["绿色区", "黄色区", "红色区"]),
            "automation": selected_options(
                text,
                [
                    "可以自动做",
                    "只能做本地草案",
                    "需要复核后再继续",
                    "需要 Jenn 明确确认",
                    "不能做，只能写预案",
                ],
            ),
        },
        "receipt": None,
    }

    if write_local_receipt:
        result["receipt"] = str(write_receipt(result, receipt_dir))

    return result


def format_text(result: dict[str, Any]) -> str:
    gate = result["gate"]
    router = result["router"]
    validation = result["validation"]
    lines = [
        f"Task envelope: {result['target']}",
        f"Status: {gate['status']}",
        f"Gate: {gate['gate']}",
        f"Routed color zone: {gate['color_zone']}",
        f"Automation: {gate['automation']}",
        f"Validator: {'PASS' if validation['passed'] else 'FAIL'}",
        f"Policy router: {router['decision']} / {router['permission_level']}",
        f"Action: {result['action'] or 'No usable action description found.'}",
        f"Receipt: {result['receipt'] or 'not written'}",
    ]

    if validation["missing_required_groups"]:
        lines.append("")
        lines.append("Missing Required Groups:")
        for group in validation["missing_required_groups"]:
            lines.append(f"- {group['id']}: {group['description']}")

    if validation["forbidden_hits"] or validation["forbidden_pattern_hits"]:
        lines.append("")
        lines.append("Forbidden Signals:")
        for item in validation["forbidden_hits"]:
            lines.append(f"- text: {item}")
        for item in validation["forbidden_pattern_hits"]:
            lines.append(f"- pattern: {item}")

    if router.get("next_steps"):
        lines.append("")
        lines.append("Next Steps:")
        lines.extend(f"- {item}" for item in router["next_steps"])

    return "\n".join(lines)


def exit_code(result: dict[str, Any]) -> int:
    status = result["gate"]["status"]
    if status in {"ALLOW", "DRAFT_ONLY"}:
        return 0
    if status in {"NEEDS_REVIEW", "NEEDS_JENN_CONFIRMATION"}:
        return 2
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run policy-router + task-envelope validation and write a local receipt."
    )
    parser.add_argument("target", help="Markdown task envelope to check.")
    parser.add_argument(
        "--rules",
        default=None,
        help="Validation rules JSON. Defaults to validation-rules.json next to this script.",
    )
    parser.add_argument(
        "--policy-root",
        default=None,
        help="Life-core policy root. Defaults to ../policies/life-core.",
    )
    parser.add_argument(
        "--receipt-dir",
        default=None,
        help="Receipt directory. Defaults to task-envelope/receipts.",
    )
    parser.add_argument("--date", default=None, help="Receipt date, YYYY-MM-DD.")
    parser.add_argument("--no-receipt", action="store_true", help="Do not write a receipt.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()

    result = run_loop(
        Path(args.target),
        rules_path=Path(args.rules) if args.rules else None,
        policy_root=Path(args.policy_root) if args.policy_root else None,
        receipt_dir=Path(args.receipt_dir) if args.receipt_dir else None,
        write_local_receipt=not args.no_receipt,
        run_date=args.date,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))

    return exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
