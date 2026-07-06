#!/usr/bin/env python3
"""Fixture tests for read-only docctl doctor."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import textwrap
from types import ModuleType


ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = ROOT.parents[1]


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


def finding_ids(result: dict) -> set[str]:
    return {finding["rule_id"] for finding in result.get("findings", [])}


def finding_messages(result: dict, rule_id: str) -> list[str]:
    return [
        str(finding.get("message") or "")
        for finding in result.get("findings", [])
        if finding.get("rule_id") == rule_id
    ]


def make_fixture() -> tuple[Path, Path]:
    fixture_root = ROOT / ".tmp-docctl-fixture"
    if fixture_root.exists():
        shutil.rmtree(fixture_root)

    write_text(
        fixture_root / "README.md",
        "# Fixture\n\nLocal fixture file.\n",
    )
    write_text(
        fixture_root / "extra.md",
        "# Extra\n\nUnregistered fixture file.\n",
    )
    write_text(
        fixture_root / "known.md",
        "# Known\n\nKnown external-scope fixture file.\n",
    )
    write_text(
        fixture_root / "archived.md",
        "# Archived\n\nArchived fixture file.\n",
    )
    write_text(
        fixture_root / "archive-notes" / "fixture-archive-note.md",
        f"""
        # Archive Note: Fixture

        ## Archived Files

        - `{fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/archived.md`
        """,
    )
    write_text(
        fixture_root / "reviews" / "fixture.review.md",
        "# Fixture Review\n",
    )
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
            canonical_path: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/README.md
            owner:
              human: Jenn
              agent_steward: Nobao
            source_of_truth: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/README.md
            supersedes: []
            superseded_by: null
            related: []
            last_reviewed: 2026-07-01
            review_by: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/reviews/fixture.review.md
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
            directory_root: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}
            registry_path: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/drafts/document-registry.yaml
            owner:
              human: Jenn
              agent_steward: Nobao
            validator: control-plane/registry/validate-document-registry.py
            expected_document_count: 1
            authority: example only, not active workspace authority
            scope: fixture
            known_external_scope:
              - path: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/known.md
                classification: known_external_scope
                reason: handled by another local governance route
                review_trigger:
                  - fixture changes
            archive_notes:
              - path: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/archive-notes/fixture-archive-note.md
                classification: historical_archive
                safe_use: fixture historical context only
                replacement:
                  - {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/README.md
                review_trigger:
                  - fixture changes
            last_review: {fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/reviews/fixture.review.md
            security_boundary:
              - no secrets
            validation:
              notes:
                - fixture
        """,
    )
    return fixture_root, fixture_root / "federated.yaml"


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []
    fixture_root, federated_path = make_fixture()

    try:
        result = docctl.doctor(federated_path)
        check(result["passed"], "fixture doctor should pass without hard failures", failures)
        check("DOCCTL-UNREGISTERED" in finding_ids(result), "unregistered source file should warn", failures)
        check(
            "DOCCTL-KNOWN-EXTERNAL-SCOPE" in finding_ids(result),
            "known external scope should be reported as info",
            failures,
        )
        check(
            result["registries"][0]["known_external_scope_files"] == 1,
            "known external scope should count one fixture file",
            failures,
        )
        check(
            not any("known.md" in message for message in finding_messages(result, "DOCCTL-UNREGISTERED")),
            "known external scope should not appear in unregistered findings",
            failures,
        )
        check(
            "DOCCTL-ARCHIVED" in finding_ids(result),
            "archive note should be reported as info",
            failures,
        )
        check(
            result["registries"][0]["archived_files"] == 1,
            "archive note should count one fixture file",
            failures,
        )
        check(
            not any("archived.md" in message for message in finding_messages(result, "DOCCTL-UNREGISTERED")),
            "archive note file target should not appear in unregistered findings",
            failures,
        )

        count_text = (fixture_root / "federated.yaml").read_text(encoding="utf-8")
        (fixture_root / "federated.yaml").write_text(
            count_text.replace("expected_document_count: 1", "expected_document_count: 99"),
            encoding="utf-8",
        )
        count_result = docctl.doctor(federated_path)
        check(not count_result["passed"], "count mismatch should fail doctor", failures)
        check("DOCCTL-COUNT" in finding_ids(count_result), "count mismatch should trigger DOCCTL-COUNT", failures)

        fixture_root, federated_path = make_fixture()
        review_path = fixture_root / "reviews" / "fixture.review.md"
        review_path.unlink()
        review_result = docctl.doctor(federated_path)
        check(not review_result["passed"], "missing review reference should fail doctor", failures)
        check(
            "DOCCTL-MISSING-RECEIPT-REVIEW" in finding_ids(review_result),
            "missing review should trigger DOCCTL-MISSING-RECEIPT-REVIEW",
            failures,
        )

        fixture_root, federated_path = make_fixture()
        registry_path = fixture_root / "drafts" / "document-registry.yaml"
        registry_text = registry_path.read_text(encoding="utf-8")
        registry_path.write_text(
            registry_text.replace(
                f"{fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/README.md",
                "state-private/fixture.md",
                1,
            ),
            encoding="utf-8",
        )
        protected_result = docctl.doctor(federated_path)
        check(not protected_result["passed"], "protected registered path should fail doctor", failures)
        check("DOCCTL-PROTECTED" in finding_ids(protected_result), "protected path should trigger DOCCTL-PROTECTED", failures)

        fixture_root, federated_path = make_fixture()
        federation_path = fixture_root / "federated.yaml"
        federation_text = federation_path.read_text(encoding="utf-8")
        federation_path.write_text(
            federation_text.replace(
                f"{fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/known.md",
                "state-private/known.md",
            ),
            encoding="utf-8",
        )
        protected_known_result = docctl.doctor(federated_path)
        check(
            not protected_known_result["passed"],
            "protected known_external_scope path should fail doctor",
            failures,
        )
        check(
            "DOCCTL-PROTECTED" in finding_ids(protected_known_result),
            "protected known_external_scope should trigger DOCCTL-PROTECTED",
            failures,
        )

        fixture_root, federated_path = make_fixture()
        archive_note_path = fixture_root / "archive-notes" / "fixture-archive-note.md"
        archive_note_text = archive_note_path.read_text(encoding="utf-8")
        archive_note_path.write_text(
            archive_note_text.replace(
                f"{fixture_root.relative_to(WORKSPACE_ROOT).as_posix()}/archived.md",
                "state-private/archived.md",
            ),
            encoding="utf-8",
        )
        protected_archive_result = docctl.doctor(federated_path)
        check(
            not protected_archive_result["passed"],
            "protected archive note path should fail doctor",
            failures,
        )
        check(
            "DOCCTL-PROTECTED" in finding_ids(protected_archive_result),
            "protected archive note path should trigger DOCCTL-PROTECTED",
            failures,
        )
    finally:
        if fixture_root.exists():
            shutil.rmtree(fixture_root)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=8 failures={len(failures)}")
        return 1

    print("PASS unregistered source warning fixture")
    print("PASS known external scope fixture")
    print("PASS archive note fixture")
    print("PASS count mismatch fixture")
    print("PASS missing review reference fixture")
    print("PASS protected path fixture")
    print("PASS protected known external scope fixture")
    print("PASS protected archive note path fixture")
    print("cases=8 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
