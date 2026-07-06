#!/usr/bin/env python3
"""Fixture tests for dry-run docctl plan-fix."""

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


def make_fixture(docctl: ModuleType, *, count: int = 1, extra: bool = False) -> Path:
    fixture_root = ROOT / ".tmp-docctl-plan-fix-fixture"
    remove_path(fixture_root)
    rel = fixture_root.relative_to(docctl.WORKSPACE_ROOT).as_posix()
    write_text(fixture_root / "README.md", "# Fixture\n")
    write_text(fixture_root / "reviews" / "fixture.review.md", "# Review\n")
    if extra:
        write_text(fixture_root / "extra.md", "# Extra\n")
    write_text(
        fixture_root / "drafts" / "document-registry.yaml",
        f"""
        schema_version: agents-os.document-registry.v0.1-draft
        status: draft_example_not_active
        documents:
          - id: fixture-readme
            title: Fixture README
            doc_type: index
            status: active
            scope: fixture
            canonical_path: {rel}/README.md
            owner:
              human: Jenn
              agent_steward: Nobao
            source_of_truth: {rel}/README.md
            supersedes: []
            superseded_by: null
            related: []
            last_reviewed: 2026-07-02
            review_by: {rel}/reviews/fixture.review.md
            freshness:
              level: ordinary
              review_trigger:
                - fixture changes
            security_boundary:
              - no secrets
            validation:
              notes:
                - fixture
        """,
    )
    write_text(
        fixture_root / "federated.yaml",
        f"""
        schema_version: agents-os.federated-document-registry.v0.1-draft
        status: draft_example_not_active
        registries:
          - id: fixture-registry
            title: Fixture Registry
            status: pilot
            directory_root: {rel}
            registry_path: {rel}/drafts/document-registry.yaml
            owner:
              human: Jenn
              agent_steward: Nobao
            validator: control-plane/registry/validate-document-registry.py
            expected_document_count: {count}
            authority: example only, not active workspace authority
            security_boundary:
              - no secrets
            validation:
              notes:
                - fixture
        """,
    )
    return fixture_root / "federated.yaml"


def has_category(result: dict[str, object], category: str) -> bool:
    proposals = result.get("proposals")
    if not isinstance(proposals, list):
        return False
    return any(isinstance(item, dict) and item.get("category") == category for item in proposals)


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []
    fixture_root = ROOT / ".tmp-docctl-plan-fix-fixture"
    remove_path(fixture_root)

    try:
        current = docctl.plan_fix()
        check(current["passed"], "current plan-fix should pass", failures)
        check(current["dry_run"] is True, "plan-fix should be dry-run", failures)
        check(current["write_performed"] is False, "plan-fix should not write", failures)
        check(current["patch_created"] is False, "plan-fix should not create a patch", failures)
        check(has_category(current, "no_action_needed"), "clean current state should need no action", failures)

        unregistered_fixture = make_fixture(docctl, extra=True)
        unregistered = docctl.plan_fix(unregistered_fixture)
        check(unregistered["passed"], "unregistered fixture should still produce a proposal", failures)
        check(
            has_category(unregistered, "register_missing_document"),
            "unregistered fixture should propose register_missing_document",
            failures,
        )
        check(unregistered["write_performed"] is False, "unregistered proposal should not write", failures)

        mismatch_fixture = make_fixture(docctl, count=99)
        mismatch = docctl.plan_fix(mismatch_fixture)
        check(mismatch["passed"], "count mismatch fixture should still produce a proposal", failures)
        check(
            has_category(mismatch, "fix_expected_document_count"),
            "count mismatch should propose fix_expected_document_count",
            failures,
        )

        protected = docctl.plan_fix(Path("state-private/federated.yaml"))
        check(not protected["passed"], "protected target should block plan-fix", failures)
        check(
            has_category(protected, "blocked_protected_path"),
            "protected target should propose blocked_protected_path",
            failures,
        )
        check(protected["write_performed"] is False, "protected target should not write", failures)

        cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "plan-fix",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_result.returncode == 0, "plan-fix CLI should pass on current registry", failures)
        try:
            cli_data = json.loads(cli_result.stdout)
        except json.JSONDecodeError:
            cli_data = {}
            failures.append("plan-fix CLI should emit JSON")
        check(cli_data.get("write_performed") is False, "plan-fix CLI should report write_performed=false", failures)
        check(cli_data.get("warnings", {}).get("apply_fix_implemented") is False, "plan-fix should not implement apply-fix", failures)
    finally:
        remove_path(fixture_root)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=5 failures={len(failures)}")
        return 1

    print("PASS current no-action fixture")
    print("PASS unregistered proposal fixture")
    print("PASS count mismatch proposal fixture")
    print("PASS protected target fixture")
    print("PASS plan-fix CLI fixture")
    print("cases=5 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
