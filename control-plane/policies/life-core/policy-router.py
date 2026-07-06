#!/usr/bin/env python3
"""Small read-only policy router for AGENTS OS life-core actions.

The router classifies an action description against transparent JSON rules.
It never executes the routed action and never grants authority by itself.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DECISION_RANK = {
    "allowed": 10,
    "needs_classification": 20,
    "needs_activation": 80,
    "blocked": 90,
    "proposal_only": 100,
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def term_in_action(term: str, action: str) -> bool:
    needle = normalize(term)
    if not needle:
        return False
    if any(ord(char) > 127 for char in needle):
        return needle in action
    pattern = r"(?<![a-z0-9_])" + re.escape(needle) + r"(?![a-z0-9_])"
    return re.search(pattern, action) is not None


def rule_matches(rule: dict[str, Any], action: str) -> list[str]:
    matched: list[str] = []
    has_match_clause = False

    for term in rule.get("terms_none", []):
        if term_in_action(str(term), action):
            return []

    for term in rule.get("terms_any", []):
        has_match_clause = True
        if term_in_action(str(term), action):
            matched.append(str(term))

    if rule.get("terms_any") and not matched:
        return []

    for term in rule.get("terms_all", []):
        has_match_clause = True
        if not term_in_action(str(term), action):
            return []
        matched.append(str(term))

    for group in rule.get("terms_all_any", []):
        has_match_clause = True
        group_matches: list[str] = []
        for term in group:
            if term_in_action(str(term), action):
                group_matches.append(str(term))
        if not group_matches:
            return []
        matched.extend(group_matches)

    if not has_match_clause:
        return []

    return unique_keep_order(matched)


def unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def choose_decision(default: dict[str, Any], matches: list[dict[str, Any]]) -> dict[str, Any]:
    if not matches:
        return {
            "matched_rules": [],
            **default,
        }

    sorted_matches = sorted(
        matches,
        key=lambda item: (
            DECISION_RANK.get(str(item.get("decision")), 0),
            int(item.get("priority", 0)),
        ),
        reverse=True,
    )
    primary = sorted_matches[0]
    primary_decision = str(primary.get("decision"))
    primary_rank = DECISION_RANK.get(str(primary.get("decision")), 0)
    if primary_decision == "allowed":
        evidence_matches = [
            match
            for match in sorted_matches
            if str(match.get("decision")) == "allowed"
        ]
    else:
        evidence_matches = [
            match
            for match in sorted_matches
            if DECISION_RANK.get(str(match.get("decision")), 0) >= primary_rank
        ]

    modules: list[str] = []
    evidence: list[str] = []
    denied: list[str] = []
    next_steps: list[str] = []

    for match in evidence_matches:
        modules.extend(match.get("modules", []))
        evidence.extend(match.get("evidence", []))
        denied.extend(match.get("denied_boundaries", []))
        next_steps.extend(match.get("next_steps", []))

    return {
        "decision": primary.get("decision"),
        "permission_level": primary.get("permission_level"),
        "confidence": primary.get("confidence", "medium"),
        "reason": primary.get("reason"),
        "modules": unique_keep_order(modules),
        "evidence": unique_keep_order(evidence),
        "denied_boundaries": unique_keep_order(denied),
        "next_steps": unique_keep_order(next_steps),
        "matched_rules": [
            {
                "id": match.get("id"),
                "decision": match.get("decision"),
                "permission_level": match.get("permission_level"),
                "matched_terms": match.get("matched_terms", []),
            }
            for match in sorted_matches
        ],
    }


def route_action(action: str, root: Path) -> dict[str, Any]:
    rules_path = root / "policy-router.rules.json"
    index_path = root / "policy-index.json"
    rules = load_json(rules_path)
    index = load_json(index_path)
    normalized_action = normalize(action)

    matches: list[dict[str, Any]] = []
    for rule in rules.get("rules", []):
        matched_terms = rule_matches(rule, normalized_action)
        if matched_terms:
            enriched = dict(rule)
            enriched["matched_terms"] = matched_terms
            matches.append(enriched)

    decision = choose_decision(rules["default_decision"], matches)
    default_modules = rules.get("default_modules", [])
    modules = unique_keep_order(default_modules + decision.get("modules", []))

    missing_modules = [
        module for module in modules if not (root / module).exists()
    ]

    return {
        "router_id": index.get("router", {}).get("router_id", "life-core.policy-router.v0.1"),
        "schema_version": "life-core.policy-router.result.v0.1",
        "action": action,
        "decision": decision.get("decision"),
        "permission_level": decision.get("permission_level"),
        "confidence": decision.get("confidence"),
        "reason": decision.get("reason"),
        "required_modules": modules,
        "required_evidence": decision.get("evidence", []),
        "denied_boundaries": decision.get("denied_boundaries", []),
        "next_steps": decision.get("next_steps", []),
        "matched_rules": decision.get("matched_rules", []),
        "warnings": {
            "missing_modules": missing_modules,
            "router_is_read_only": True,
            "formal_memory_registration": "not_performed",
        },
    }


def format_text(result: dict[str, Any]) -> str:
    lines = [
        f"Decision: {result['decision']}",
        f"Permission: {result['permission_level']}",
        f"Confidence: {result['confidence']}",
        f"Reason: {result['reason']}",
        "",
        "Required Modules:",
    ]
    lines.extend(f"- {module}" for module in result["required_modules"])
    lines.append("")
    lines.append("Required Evidence:")
    lines.extend(f"- {item}" for item in result["required_evidence"])
    lines.append("")
    lines.append("Denied Boundaries:")
    lines.extend(f"- {item}" for item in result["denied_boundaries"])
    lines.append("")
    lines.append("Matched Rules:")
    if result["matched_rules"]:
        for rule in result["matched_rules"]:
            terms = ", ".join(rule.get("matched_terms", []))
            lines.append(f"- {rule['id']} ({rule['decision']}, {rule['permission_level']}): {terms}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("Next Steps:")
    lines.extend(f"- {item}" for item in result["next_steps"])
    if result["warnings"]["missing_modules"]:
        lines.append("")
        lines.append("Warnings:")
        for module in result["warnings"]["missing_modules"]:
            lines.append(f"- missing module: {module}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a life-core action without executing it.")
    parser.add_argument("--action", required=True, help="Action description to classify.")
    parser.add_argument("--root", default=None, help="Policy root. Defaults to this script directory.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent
    result = route_action(args.action, root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
