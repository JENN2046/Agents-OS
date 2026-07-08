#!/usr/bin/env python3
"""Fixture tests for read-only docctl trend."""

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
    if path.exists():
        shutil.rmtree(path)


def make_fixture(docctl: ModuleType) -> tuple[Path, Path, Path]:
    fixture_root = ROOT / ".tmp-docctl-trend-fixture"
    remove_path(fixture_root)
    rel = fixture_root.relative_to(docctl.WORKSPACE_ROOT).as_posix()
    write_text(fixture_root / "README.md", "# Fixture\n")
    write_text(fixture_root / "reviews" / "fixture.review.md", "# Review\n")
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
          - id: fixture-document-registry
            title: Fixture Document Registry
            doc_type: registry
            status: active
            scope: fixture
            canonical_path: {rel}/drafts/document-registry.yaml
            owner:
              human: Jenn
              agent_steward: Nobao
            source_of_truth: {rel}/drafts/document-registry.yaml
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
          - id: fixture-federated-registry
            title: Fixture Federated Registry
            doc_type: registry
            status: active
            scope: fixture
            canonical_path: {rel}/federated.yaml
            owner:
              human: Jenn
              agent_steward: Nobao
            source_of_truth: {rel}/federated.yaml
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
          - id: fixture-review
            title: Fixture Review
            doc_type: review
            status: active
            scope: fixture
            canonical_path: {rel}/reviews/fixture.review.md
            owner:
              human: Jenn
              agent_steward: Nobao
            source_of_truth: {rel}/reviews/fixture.review.md
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
            expected_document_count: 4
            authority: example only, not active workspace authority
            security_boundary:
              - no secrets
            validation:
              notes:
                - fixture
        """,
    )
    snapshot_dir = fixture_root / "snapshots"
    return fixture_root, fixture_root / "federated.yaml", snapshot_dir


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []
    fixture_root = ROOT / ".tmp-docctl-trend-fixture"
    snapshot_dir = ROOT / ".tmp-docctl-trend-snapshots"
    remove_path(fixture_root)
    remove_path(snapshot_dir)

    try:
        _, federated_registry, fixture_snapshot_dir = make_fixture(docctl)
        current = docctl.trend(federated_registry, fixture_snapshot_dir)
        check(current["passed"], "current trend should pass", failures)
        check(current["trend_status"] in {"ready", "insufficient_snapshots"}, "trend should report a status", failures)
        check(current["warnings"]["snapshot_write_performed"] is False, "trend should not write snapshots", failures)

        fixture_snapshot_dir.mkdir(parents=True)
        (fixture_snapshot_dir / "2026-07-01.json").write_text(
            json.dumps(
                {
                    "date": "2026-07-01",
                    "doctor_summary": {
                        "documents": 1,
                        "scanned_files": 2,
                        "known_external_scope_files": 0,
                        "archived_files": 0,
                        "unregistered_files": 1,
                        "warn": 1,
                        "fail": 0,
                    },
                }
            ),
            encoding="utf-8",
        )
        with_snapshot = docctl.trend(federated_registry, fixture_snapshot_dir)
        check(with_snapshot["passed"], "trend with snapshot should pass", failures)
        check(with_snapshot["snapshots_found"] == 1, "trend should find one snapshot", failures)
        check(with_snapshot["no_regression_from_latest"] is True, "current clean baseline should not regress from warning snapshot", failures)

        protected = docctl.trend(federated_registry, Path("state-private/snapshots"))
        check(not protected["passed"], "protected snapshot dir should fail", failures)
        check(
            any(finding["rule_id"] == "DOCCTL-TREND-BLOCKED" for finding in protected["findings"]),
            "protected snapshot dir should trigger DOCCTL-TREND-BLOCKED",
            failures,
        )

        cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "trend",
                str(federated_registry),
                "--snapshot-dir",
                str(fixture_snapshot_dir),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_result.returncode == 0, "trend CLI should pass on current registry", failures)
        try:
            cli_data = json.loads(cli_result.stdout)
        except json.JSONDecodeError:
            cli_data = {}
            failures.append("trend CLI should emit JSON")
        check(cli_data.get("warnings", {}).get("snapshot_write_performed") is False, "trend CLI should not write snapshots", failures)
    finally:
        remove_path(fixture_root)
        remove_path(snapshot_dir)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=4 failures={len(failures)}")
        return 1

    print("PASS current trend fixture")
    print("PASS existing snapshot fixture")
    print("PASS protected snapshot dir fixture")
    print("PASS trend CLI fixture")
    print("cases=4 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
