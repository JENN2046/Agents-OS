#!/usr/bin/env python3
"""Fixture tests for read-only docctl status pulse."""

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


def make_fixture(docctl: ModuleType) -> tuple[Path, Path, Path]:
    fixture_root = ROOT / ".tmp-docctl-status-fixture"
    remove_path(fixture_root)
    rel = fixture_root.relative_to(docctl.WORKSPACE_ROOT).as_posix()
    write_text(fixture_root / "README.md", "# Fixture\n\nActive fixture with active, draft, and example boundary language.\n")
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
          - id: fixture-snapshot
            title: Fixture Snapshot
            doc_type: receipt
            status: active
            scope: fixture
            canonical_path: {rel}/snapshots/2026-07-01.json
            owner:
              human: Jenn
              agent_steward: Nobao
            source_of_truth: {rel}/snapshots/2026-07-01.json
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
            expected_document_count: 5
            authority: example only, not active workspace authority
            security_boundary:
              - no secrets
            validation:
              notes:
                - fixture
        """,
    )
    snapshot_dir = fixture_root / "snapshots"
    write_text(
        snapshot_dir / "2026-07-01.json",
        json.dumps(
            {
                "date": "2026-07-01",
                "doctor_summary": {
                    "documents": 1,
                    "scanned_files": 2,
                    "known_external_scope_files": 0,
                    "archived_files": 0,
                    "unregistered_files": 0,
                    "warn": 0,
                    "fail": 0,
                },
            }
        ),
    )
    return fixture_root, fixture_root / "federated.yaml", snapshot_dir


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []
    fixture_root = ROOT / ".tmp-docctl-status-fixture"
    missing_snapshot_dir = ROOT / ".tmp-docctl-status-missing-snapshots"
    remove_path(fixture_root)
    remove_path(missing_snapshot_dir)

    try:
        _, federated_registry, snapshot_dir = make_fixture(docctl)
        original_doctor = docctl.doctor
        doctor_call_count = {"count": 0}

        def counting_doctor(*args, **kwargs):
            doctor_call_count["count"] += 1
            return original_doctor(*args, **kwargs)

        docctl.doctor = counting_doctor
        current = docctl.status(federated_registry, snapshot_dir)
        check(doctor_call_count["count"] == 1, "status should call doctor once and reuse the result", failures)
        check(current["passed"], "fixture status should pass", failures)
        check(current["read_only"] is True, "status should be read-only", failures)
        check(current["would_write"] is False, "status should not write", failures)
        check(current["score"]["score"] == 100, "fixture score should be 100", failures)
        check(current["score"]["eligible_95"] is True, "fixture status should be 9.5 eligible", failures)
        check(current["trend"]["snapshots_found"] == 1, "fixture status should see one snapshot", failures)
        check(current["plan_fix"]["plan_status"] == "no_action_needed", "fixture status should need no repair", failures)
        check(current["docctl_index"]["doctor_invocations"] == 1, "status should report one doctor invocation", failures)
        check(
            current["docctl_index"]["doctor_reused_by"] == ["score", "trend", "plan_fix"],
            "status should report doctor reuse targets",
            failures,
        )
        check(current["warnings"]["snapshot_writer_called"] is False, "status should not call snapshot writer", failures)
        check(current["warnings"]["registry_write_performed"] is False, "status should not write registries", failures)

        doctor_call_count["count"] = 0
        no_snapshot = docctl.status(federated_registry, missing_snapshot_dir)
        check(doctor_call_count["count"] == 1, "missing snapshot status should call doctor once", failures)
        check(no_snapshot["passed"], "missing snapshot dir should not fail status", failures)
        check(no_snapshot["trend"]["trend_status"] == "insufficient_snapshots", "missing snapshot dir should be insufficient", failures)
        check(no_snapshot["trend"]["snapshots_found"] == 0, "missing snapshot dir should have zero snapshots", failures)
        check(not missing_snapshot_dir.exists(), "status should not create missing snapshot dir", failures)
        check("snapshot" in no_snapshot["next_recommended_action"], "missing snapshot dir should recommend reviewed snapshot", failures)

        doctor_call_count["count"] = 0
        protected = docctl.status(Path("state-private/federated.yaml"))
        check(doctor_call_count["count"] == 1, "protected status should call doctor once", failures)
        check(not protected["passed"], "protected target should fail status", failures)
        check(protected["plan_fix"]["plan_status"] == "blocked", "protected target should block plan-fix", failures)
        check(protected["warnings"]["write_performed"] is False, "protected status should not write", failures)

        cli_json = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "status",
                str(federated_registry),
                "--snapshot-dir",
                str(snapshot_dir),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_json.returncode == 0, "status CLI JSON should pass on fixture registry", failures)
        try:
            cli_data = json.loads(cli_json.stdout)
        except json.JSONDecodeError:
            cli_data = {}
            failures.append("status CLI should emit JSON")
        check(cli_data.get("warnings", {}).get("snapshot_write_performed") is False, "status CLI should not write snapshot", failures)
        check(cli_data.get("warnings", {}).get("apply_fix_implemented") is False, "status CLI should not implement apply-fix", failures)
        check(cli_data.get("docctl_index", {}).get("doctor_invocations") == 1, "status CLI should report indexed doctor reuse", failures)

        cli_text = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "status",
                str(federated_registry),
                "--snapshot-dir",
                str(snapshot_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_text.returncode == 0, "status CLI text should pass on fixture registry", failures)
        check("docctl status" in cli_text.stdout, "status CLI text should identify command", failures)
        check("Would write: False" in cli_text.stdout, "status CLI text should report no writes", failures)
    finally:
        remove_path(fixture_root)
        remove_path(missing_snapshot_dir)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=6 failures={len(failures)}")
        return 1

    print("PASS hermetic status fixture")
    print("PASS status doctor index reuse fixture")
    print("PASS missing snapshot dir fixture")
    print("PASS protected target fixture")
    print("PASS status CLI JSON fixture")
    print("PASS status CLI text fixture")
    print("cases=6 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
