#!/usr/bin/env python3
"""Fixture tests for read-only docctl impact."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
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


def affected_ids(result: dict) -> set[str]:
    ids: set[str] = set()
    for target in result.get("targets", []):
        ids.update(doc.get("id") for doc in target.get("affected_documents", []))
    return ids


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []

    readme = docctl.impact([Path("control-plane/registry/README.md")])
    check(readme["passed"], "README impact should pass", failures)
    check(readme["warnings"]["target_content_read_performed"] is False, "impact should not read target contents", failures)
    check(readme["would_write"] is False, "impact should not write", failures)
    check("registry-readme" in affected_ids(readme), "README should affect registry-readme", failures)

    registry_yaml = docctl.impact([Path("control-plane/registry/drafts/document-registry.v0.1.example.yaml")])
    check(registry_yaml["passed"], "registry YAML impact should pass", failures)
    check(
        any(item.get("id") == "registry-document-registry" for item in registry_yaml["targets"][0]["affected_registries"]),
        "registry YAML should affect registry-document-registry",
        failures,
    )

    review = docctl.impact([Path("control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-3-exception-governance.review.md")])
    check(review["passed"], "review impact should pass", failures)
    check(
        "document-governance-9.5-stage-3-exception-governance-review" in affected_ids(review),
        "review path should affect its review document",
        failures,
    )

    no_match = docctl.impact([Path("control-plane/registry/no-such-future.md")])
    check(no_match["passed"], "safe no-match path should pass", failures)
    check(no_match["targets"][0]["affected_documents"] == [], "safe no-match path should affect no documents", failures)

    protected = docctl.impact([Path("state-private/impact.md")])
    check(not protected["passed"], "protected impact path should fail", failures)
    check(protected["targets"][0]["blocked"], "protected impact path should be blocked", failures)

    outside = docctl.impact([Path("/etc/hosts")])
    check(not outside["passed"], "outside impact path should fail", failures)
    check(outside["targets"][0]["blocked"], "outside impact path should be blocked", failures)

    cli_result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "docctl.py"),
            "impact",
            "state-private/impact.md",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_result.returncode == 1, "protected impact CLI should return failure", failures)
    try:
        cli_data = json.loads(cli_result.stdout)
    except json.JSONDecodeError:
        cli_data = {}
        failures.append("protected impact CLI should emit JSON")
    check(cli_data.get("targets", [{}])[0].get("blocked") is True, "protected impact CLI should block target", failures)
    check(
        cli_data.get("warnings", {}).get("target_content_read_performed") is False,
        "protected impact CLI should not read target contents",
        failures,
    )

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=7 failures={len(failures)}")
        return 1

    print("PASS README impact fixture")
    print("PASS registry YAML impact fixture")
    print("PASS review impact fixture")
    print("PASS no-match impact fixture")
    print("PASS protected impact fixture")
    print("PASS outside impact fixture")
    print("PASS protected impact CLI fixture")
    print("cases=7 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
