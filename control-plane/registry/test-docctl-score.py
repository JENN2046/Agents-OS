#!/usr/bin/env python3
"""Fixture tests for read-only docctl score."""

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


def make_fixture(docctl: ModuleType, *, count: int = 4, extra: bool = False) -> Path:
    fixture_root = ROOT / ".tmp-docctl-score-fixture"
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


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []
    fixture_root = ROOT / ".tmp-docctl-score-fixture"
    remove_path(fixture_root)

    try:
        clean_fixture = make_fixture(docctl)
        current = docctl.score(clean_fixture)
        check(current["passed"], "current score should pass", failures)
        check(current["score"] >= 95, "current score should be at least 95", failures)
        check(current["eligible_95"], "current score should be 9.5 eligible", failures)

        warning_fixture = make_fixture(docctl, extra=True)
        warning_score = docctl.score(warning_fixture)
        check(not warning_score["passed"], "unregistered fixture should fail score gate", failures)
        check(
            any(gate["gate"] == "unregistered" for gate in warning_score["hard_gates"]),
            "unregistered fixture should trigger hard gate",
            failures,
        )

        mismatch_fixture = make_fixture(docctl, count=99)
        mismatch_score = docctl.score(mismatch_fixture)
        check(not mismatch_score["passed"], "count mismatch fixture should fail score", failures)
        check(any(gate["gate"] == "fail" for gate in mismatch_score["hard_gates"]), "count mismatch should trigger fail gate", failures)

        protected_score = docctl.score(Path("state-private/federated.yaml"))
        check(not protected_score["passed"], "protected score target should fail", failures)
        check(any(gate["gate"] == "fail" for gate in protected_score["hard_gates"]), "protected target should trigger fail gate", failures)

        cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "score",
                str(make_fixture(docctl)),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_result.returncode == 0, "score CLI should pass on current registry", failures)
        try:
            cli_data = json.loads(cli_result.stdout)
        except json.JSONDecodeError:
            cli_data = {}
            failures.append("score CLI should emit JSON")
        check(cli_data.get("eligible_95") is True, "score CLI should report eligible_95", failures)
    finally:
        remove_path(fixture_root)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=5 failures={len(failures)}")
        return 1

    print("PASS current score fixture")
    print("PASS unregistered hard gate fixture")
    print("PASS count mismatch hard gate fixture")
    print("PASS protected target score fixture")
    print("PASS score CLI fixture")
    print("cases=5 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
