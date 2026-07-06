"""Shared path-boundary helpers for local registry validators.

This module only checks local path boundaries. It does not read files, parse
YAML, create result payloads, grant authority, or own validator domain rules.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Collection


DEFAULT_PROTECTED_PARTS = frozenset(
    {
        "state-private",
        "secret",
        "secrets",
        "credentials",
        "tokens",
        "cookies",
        "browser profiles",
        "private memory raw text",
        "provider raw response",
    }
)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _finding(rule_id: str, message: str) -> dict[str, str]:
    return {"rule_id": rule_id, "level": "fail", "message": message}


def safe_resolve(path: Path) -> tuple[Path | None, str | None]:
    try:
        return path.resolve(), None
    except (OSError, RuntimeError) as exc:
        return None, str(exc)


def is_protected_path(
    path_value: Any,
    protected_parts: Collection[str] = DEFAULT_PROTECTED_PARTS,
) -> bool:
    if not _has_value(path_value):
        return False

    text = str(path_value).replace("\\", "/").lower()
    parts = [part.lower() for part in Path(str(path_value)).parts]

    if ".env" in parts or any(part.startswith(".env.") for part in parts):
        return True
    if text.endswith("/.env") or "/.env." in text or text.startswith(".env"):
        return True
    return any(part in protected_parts for part in parts) or any(
        protected in text for protected in protected_parts
    )


def is_under_workspace(path: Path, workspace_root: Path) -> bool:
    try:
        path.relative_to(workspace_root)
    except ValueError:
        return False
    return True


def preflight_target(
    target: Path,
    workspace_root: Path,
    rule_id: str,
    protected_parts: Collection[str] = DEFAULT_PROTECTED_PARTS,
) -> list[dict[str, str]]:
    if is_protected_path(target, protected_parts):
        return [_finding(rule_id, f"target points to protected path: {target}")]

    resolved, resolve_error = safe_resolve(target)
    if resolve_error:
        return [_finding(rule_id, f"target could not be resolved: {resolve_error}")]
    if resolved is None:
        return [_finding(rule_id, f"target could not be resolved: {target}")]

    if is_protected_path(resolved, protected_parts):
        return [_finding(rule_id, f"target resolves to protected path: {target}")]

    if not is_under_workspace(resolved, workspace_root):
        return [_finding(rule_id, f"target points outside workspace: {target}")]

    if not resolved.exists():
        return [_finding(rule_id, f"target does not exist: {target}")]

    if not resolved.is_file():
        return [_finding(rule_id, f"target is not a file: {target}")]

    return []
