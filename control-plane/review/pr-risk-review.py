#!/usr/bin/env python3
"""Classify PR risk surfaces before opening a pull request.

This is a read-only helper. It does not write files, call providers, push, or
open PRs. It turns changed paths into a proof checklist so gate-like PRs do not
depend on reviewer memory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from pathlib import PurePosixPath
import re
import subprocess
import sys
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]

RISK_SURFACES: dict[str, dict[str, Any]] = {
    "runtime_provenance_package_file_set": {
        "label": "runtime provenance / package file set",
        "path_patterns": [
            r"(^|/)runtime/",
            r"(^|/)execution/.*runtime",
            r"(^|/)execution/.*/package\.json$",
            r"(^|/)execution/.*/package-lock\.json$",
            r"(^|/)src/generated/",
            r"(^|/)schemas/appserver/",
        ],
        "content_patterns": [
            r"\bpackage\b",
            r"\binstalled\b",
            r"\bruntime\b",
            r"\bhash\b",
            r"\bfingerprint\b",
        ],
        "proof_obligations": [
            "expected file set equals actual installable/runtime file set",
            "extra installed-only runtime files are rejected",
            "shared files hash-match or content-match",
            "dirty or unavailable source evidence blocks ready status",
        ],
        "negative_cases": [
            "missing expected runtime file",
            "extra installed-only runtime file",
            "content mismatch",
            "stale metadata with matching expected files",
        ],
    },
    "readiness_gate": {
        "label": "readiness gate",
        "path_patterns": [
            r"gate",
            r"preflight",
            r"readiness",
            r"validator",
            r"validate-.*\.py$",
            r"docctl\.py$",
        ],
        "content_patterns": [
            r"\bready\b",
            r"\bpassed\b",
            r"\bvalidated\b",
            r"\bpreflight\b",
            r"\bgate\b",
        ],
        "proof_obligations": [
            "all positive statuses have explicit evidence",
            "fallback branches have their own blockers and tests",
            "unavailable evidence fails closed",
        ],
        "negative_cases": [
            "unavailable evidence",
            "stale but superficially matching metadata",
            "fallback path without proof",
        ],
    },
    "public_endpoint_oauth_auth_routing": {
        "label": "public endpoint / OAuth / auth routing",
        "path_patterns": [
            r"auth",
            r"oauth",
            r"endpoint",
            r"public",
            r"proxy",
            r"gateway",
        ],
        "content_patterns": [
            r"\boauth\b",
            r"\bauthorization\b",
            r"\bpublic url\b",
            r"\bendpoint\b",
            r"\bproxy\b",
            r"\bloopback\b",
            r"\bmulticast\b",
        ],
        "proof_obligations": [
            "canonical public URL and connected peer/DNS evidence match",
            "self-reference spellings are normalized and rejected",
            "private, loopback, multicast, and split-horizon targets are blocked",
        ],
        "negative_cases": [
            "equivalent but differently spelled self-reference",
            "non-public address class",
            "proxy/environment interference",
            "oversized candidate list",
        ],
    },
    "redaction_secret_handling": {
        "label": "redaction / secret handling",
        "path_patterns": [
            r"redact",
            r"secret",
            r"token",
            r"credential",
            r"cookie",
            r"\.env",
        ],
        "content_patterns": [
            r"\bredact",
            r"\bsecret\b",
            r"\btoken\b",
            r"\bcredential\b",
            r"\bcookie\b",
            r"\bapi[_-]?key\b",
            r"\bpassword\b",
        ],
        "proof_obligations": [
            "secret-like values are redacted before printing or returning errors",
            "early returns preserve redaction",
            "private-state and credential paths remain blocked",
        ],
        "negative_cases": [
            "secret-like value reaches stderr/stdout",
            "redaction skipped on early return",
            "private-state path included in output",
        ],
    },
    "status_enum_operator_contract": {
        "label": "status enum / operator contract",
        "path_patterns": [
            r"docctl\.py$",
            r"status",
            r"state",
            r"contract",
            r"schema",
        ],
        "content_patterns": [
            r"\bstatus\b",
            r"\bstate\b",
            r"\bready\b",
            r"\bblocked\b",
            r"\bmatch\b",
            r"\bverified\b",
        ],
        "proof_obligations": [
            "status fields are treated as public operator contract",
            "negative cases assert behavior and status value",
            "positive status cannot be emitted with absent evidence",
        ],
        "negative_cases": [
            "failure behavior with success-like status",
            "blocked state missing from output",
            "ambiguous status on unavailable evidence",
        ],
    },
}

CONTENT_SCAN_SUFFIXES = {
    ".json",
    ".js",
    ".jsx",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}


def invalid_path(reason: str, path: str) -> dict[str, str]:
    return {"path": path, "reason": reason}


def normalize_changed_path(path: str) -> tuple[str | None, dict[str, str] | None]:
    raw = path.strip()
    if not raw:
        return None, invalid_path("empty path", path)
    normalized = raw.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", normalized):
        return None, invalid_path("absolute paths are not allowed", path)
    candidate_path = PurePosixPath(normalized)
    if candidate_path.is_absolute():
        return None, invalid_path("absolute paths are not allowed", path)
    if ".." in candidate_path.parts:
        return None, invalid_path("parent traversal is not allowed", path)
    return str(candidate_path), None


def split_changed_paths(paths: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    valid_paths: list[str] = []
    invalid_paths: list[dict[str, str]] = []
    for path in paths:
        normalized, invalid = normalize_changed_path(path)
        if invalid is not None:
            invalid_paths.append(invalid)
            continue
        if normalized is not None:
            valid_paths.append(normalized)
    return sorted(set(valid_paths)), invalid_paths


def run_git_changed_paths(base: str) -> list[str]:
    commands = [
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        ["git", "diff", "--name-only"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    paths: list[str] = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=WORKSPACE_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if completed.returncode == 0:
            paths.extend(line.strip() for line in completed.stdout.splitlines() if line.strip())
    return sorted(set(paths))


def read_changed_text(path: str, max_bytes: int = 20000) -> str:
    normalized, invalid = normalize_changed_path(path)
    if invalid is not None or normalized is None:
        return ""
    candidate = WORKSPACE_ROOT / normalized
    if not candidate.is_file():
        return ""
    if candidate.suffix.lower() not in CONTENT_SCAN_SUFFIXES:
        return ""
    try:
        candidate.resolve().relative_to(WORKSPACE_ROOT.resolve())
    except (OSError, ValueError):
        return ""
    try:
        return candidate.read_text(encoding="utf-8", errors="ignore")[:max_bytes]
    except OSError:
        return ""


def matches_any(patterns: list[str], value: str) -> bool:
    return any(re.search(pattern, value, re.I) for pattern in patterns)


def classify_paths(paths: list[str], *, include_content: bool = True) -> dict[str, Any]:
    paths, invalid_paths = split_changed_paths(paths)
    surfaces: dict[str, dict[str, Any]] = {}
    for path in paths:
        path_text = path.replace("\\", "/")
        content = read_changed_text(path) if include_content else ""
        for surface_id, rule in RISK_SURFACES.items():
            path_hit = matches_any(rule["path_patterns"], path_text)
            content_hit = bool(content) and matches_any(rule["content_patterns"], content)
            if not path_hit and not content_hit:
                continue
            surface = surfaces.setdefault(
                surface_id,
                {
                    "surface_id": surface_id,
                    "label": rule["label"],
                    "matched_paths": [],
                    "match_reasons": [],
                    "proof_obligations": rule["proof_obligations"],
                    "negative_cases": rule["negative_cases"],
                },
            )
            if path not in surface["matched_paths"]:
                surface["matched_paths"].append(path)
            reason = "path" if path_hit else "content"
            if reason not in surface["match_reasons"]:
                surface["match_reasons"].append(reason)

    risk_surfaces = sorted(surfaces.values(), key=lambda item: item["surface_id"])
    return {
        "schema_version": "agents-os.pr-risk-review.v0.1",
        "read_only": True,
        "write_performed": False,
        "path_input_valid": not invalid_paths,
        "invalid_path_count": len(invalid_paths),
        "invalid_paths": invalid_paths,
        "changed_path_count": len(paths),
        "changed_paths": paths,
        "risk_surface_count": len(risk_surfaces),
        "risk_surfaces": risk_surfaces,
        "proof_matrix_required": bool(risk_surfaces),
        "required_pr_body_sections": required_pr_body_sections(bool(risk_surfaces)),
        "review_rule": "Ask whether any unproven state can still make the gate report ready.",
    }


def required_pr_body_sections(required: bool) -> list[str]:
    if not required:
        return []
    return [
        "Risk surface",
        "Invariant",
        "Evidence required",
        "Negative cases",
        "Status fields tested",
    ]


def format_text(result: dict[str, Any]) -> str:
    lines = [
        "PR risk review",
        f"Changed paths: {result['changed_path_count']}",
        f"Risk surfaces: {result['risk_surface_count']}",
        f"Proof matrix required: {result['proof_matrix_required']}",
    ]
    if not result["path_input_valid"]:
        lines.append("Path input valid: False")
        lines.append("Invalid paths:")
        for invalid in result["invalid_paths"]:
            lines.append(f"- {invalid['path']}: {invalid['reason']}")
        return "\n".join(lines)
    if not result["risk_surfaces"]:
        lines.append("Risk surface: none")
        return "\n".join(lines)

    for surface in result["risk_surfaces"]:
        lines.append("")
        lines.append(f"- {surface['label']} ({surface['surface_id']})")
        lines.append(f"  matched_paths: {', '.join(surface['matched_paths'][:8])}")
        lines.append("  proof_obligations:")
        for obligation in surface["proof_obligations"]:
            lines.append(f"    - {obligation}")
        lines.append("  negative_cases:")
        for negative in surface["negative_cases"]:
            lines.append(f"    - {negative}")

    lines.append("")
    lines.append("Required PR body sections:")
    for section in result["required_pr_body_sections"]:
        lines.append(f"- {section}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review changed paths for PR gate risk surfaces.")
    parser.add_argument("--base", default="main", help="Base ref for git changed path discovery.")
    parser.add_argument("--paths", nargs="*", help="Explicit changed paths; skips git discovery.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    parser.add_argument("--strict", action="store_true", help="Return 1 when a proof matrix is required.")
    args = parser.parse_args()

    paths = sorted(set(args.paths if args.paths is not None else run_git_changed_paths(args.base)))
    result = classify_paths(paths)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text(result))
    if not result["path_input_valid"]:
        return 2
    return 1 if args.strict and result["proof_matrix_required"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
