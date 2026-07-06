#!/usr/bin/env python3
"""Fixture tests for dry-run docctl intake."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_docctl() -> ModuleType:
    module_path = ROOT / "docctl.py"
    spec = importlib.util.spec_from_file_location("docctl", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load docctl from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def main() -> int:
    docctl = load_docctl()
    workspace_root = docctl.WORKSPACE_ROOT
    failures: list[str] = []
    fixture_root = ROOT / ".tmp-docctl-intake-fixture"
    remove_path(fixture_root)

    try:
        registered = docctl.intake(Path("control-plane/registry/README.md"))
        check(registered["passed"], "registered path should pass intake", failures)
        check(
            registered["classification"] == "registered_current",
            "registered path should classify as registered_current",
            failures,
        )
        check(registered["warnings"]["target_read_performed"] is False, "intake should not read target contents", failures)
        check(registered["would_write"] is False, "intake should not write", failures)

        draft_path = fixture_root / "drafts" / "intake-fixture-draft.md"
        write_text(draft_path, "# Draft Fixture\n")
        draft = docctl.intake(draft_path)
        check(draft["passed"], "draft path should pass intake", failures)
        check(draft["classification"] == "draft", "draft path should classify as draft", failures)

        template_path = fixture_root / "templates" / "intake-fixture-template.md"
        write_text(template_path, "# Template Fixture\n")
        template = docctl.intake(template_path)
        check(template["passed"], "template path should pass intake", failures)
        check(template["classification"] == "template", "template path should classify as template", failures)

        archive_note_path = fixture_root / "archive-notes" / "intake-fixture-archive-note.md"
        write_text(archive_note_path, "# Archive Note Fixture\n")
        archive_note = docctl.intake(archive_note_path)
        check(archive_note["passed"], "archive note path should pass intake", failures)
        check(
            archive_note["classification"] == "archive_note",
            "archive note path should classify as archive_note",
            failures,
        )

        ignored_path = fixture_root / "drafts" / "intake-fixture.bin"
        write_text(ignored_path, "generated")
        ignored = docctl.intake(ignored_path)
        check(ignored["passed"], "ignored suffix path should pass intake as dry-run", failures)
        check(
            ignored["classification"] == "ignored_by_rule",
            "ignored suffix path should classify as ignored_by_rule",
            failures,
        )
        check(hasattr(docctl, "intake"), "docctl should expose intake function", failures)

        backlog_path = workspace_root / "domains" / "intake-fixture.md"
        write_text(backlog_path, "# Future Backlog Fixture\n")
        backlog = docctl.intake(backlog_path)
        check(backlog["passed"], "safe outside-scope path should pass intake as dry-run", failures)
        check(
            backlog["classification"] == "future_backlog",
            "safe outside-scope path should classify as future_backlog",
            failures,
        )
        check(hasattr(docctl, "format_intake_text"), "docctl should expose intake formatter", failures)
        remove_path(backlog_path)

        protected = docctl.intake(Path("state-private/intake-fixture.md"))
        check(not protected["passed"], "protected path should fail intake", failures)
        check(protected["classification"] == "blocked", "protected path should classify as blocked", failures)
        check(
            protected["warnings"]["target_read_performed"] is False,
            "protected path should be blocked before content reading",
            failures,
        )

        outside = docctl.intake(Path("/etc/hosts"))
        check(not outside["passed"], "outside path should fail intake", failures)
        check(outside["classification"] == "blocked", "outside path should classify as blocked", failures)

        outside_link = ROOT / ".tmp-docctl-intake-outside-link.md"
        remove_path(outside_link)
        try:
            outside_link.symlink_to(Path("/etc/hosts"))
            outside_symlink = docctl.intake(outside_link)
            check(not outside_symlink["passed"], "outside symlink should fail intake", failures)
            check(
                outside_symlink["classification"] == "blocked",
                "outside symlink should classify as blocked",
                failures,
            )
        finally:
            remove_path(outside_link)

        cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "intake",
                "state-private/intake-fixture.md",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_result.returncode == 1, "protected intake CLI should return failure", failures)
        try:
            cli_data = json.loads(cli_result.stdout)
        except json.JSONDecodeError:
            cli_data = {}
            failures.append("protected intake CLI should emit JSON")
        check(cli_data.get("classification") == "blocked", "protected intake CLI should classify blocked", failures)
        check(
            cli_data.get("warnings", {}).get("target_read_performed") is False,
            "protected intake CLI should not read target",
            failures,
        )
    finally:
        remove_path(fixture_root)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=10 failures={len(failures)}")
        return 1

    print("PASS registered path fixture")
    print("PASS draft route fixture")
    print("PASS template route fixture")
    print("PASS archive note route fixture")
    print("PASS ignored_by_rule fixture")
    print("PASS future_backlog fixture")
    print("PASS protected path fixture")
    print("PASS outside path fixture")
    print("PASS outside symlink fixture")
    print("PASS protected CLI fixture")
    print("cases=10 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
