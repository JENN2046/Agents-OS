#!/usr/bin/env python3
"""Fixture tests for local docctl snapshot writer."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
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


def remove_path(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []
    snapshot_dir = ROOT / ".tmp-docctl-snapshot-fixture"
    remove_path(snapshot_dir)

    try:
        output = snapshot_dir / "fixture-snapshot.json"
        current = docctl.snapshot(snapshot_dir=snapshot_dir, output=output)
        check(current["passed"], "snapshot should pass in temp snapshot dir", failures)
        check(current["write_performed"] is True, "snapshot should report write_performed=true", failures)
        check(current["snapshot_path"] == output.relative_to(docctl.WORKSPACE_ROOT).as_posix(), "snapshot path should be workspace relative", failures)
        check(output.exists(), "snapshot file should exist", failures)
        payload = json.loads(output.read_text(encoding="utf-8"))
        check(payload.get("schema_version") == "agents-os.docctl.snapshot.v0.1", "snapshot schema should match", failures)
        check(isinstance(payload.get("doctor_summary"), dict), "snapshot should include doctor summary", failures)
        check(isinstance(payload.get("score_summary"), dict), "snapshot should include score summary", failures)
        check(payload.get("write_scope", {}).get("raw_logs_included") is False, "snapshot should not include raw logs", failures)
        check(payload.get("write_scope", {}).get("full_document_text_included") is False, "snapshot should not include full document text", failures)

        existing = docctl.snapshot(snapshot_dir=snapshot_dir, output=output)
        check(not existing["passed"], "existing snapshot output should block overwrite", failures)
        check(existing["write_performed"] is False, "existing output block should not write", failures)
        check(
            any(finding["rule_id"] == "DOCCTL-SNAPSHOT-BLOCKED" for finding in existing["findings"]),
            "existing output should report DOCCTL-SNAPSHOT-BLOCKED",
            failures,
        )

        protected = docctl.snapshot(snapshot_dir=Path("state-private/snapshots"))
        check(not protected["passed"], "protected snapshot dir should fail", failures)
        check(protected["write_performed"] is False, "protected snapshot dir should not write", failures)

        outside_output = docctl.snapshot(snapshot_dir=snapshot_dir, output=Path("/tmp/docctl-snapshot-fixture.json"))
        check(not outside_output["passed"], "outside output should fail", failures)
        check(outside_output["write_performed"] is False, "outside output should not write", failures)

        cli_dir = ROOT / ".tmp-docctl-snapshot-cli"
        remove_path(cli_dir)
        cli_output = cli_dir / "cli-snapshot.json"
        cli_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "snapshot",
                "--snapshot-dir",
                cli_dir.relative_to(docctl.WORKSPACE_ROOT).as_posix(),
                "--output",
                cli_output.relative_to(docctl.WORKSPACE_ROOT).as_posix(),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_result.returncode == 0, "snapshot CLI should pass in temp dir", failures)
        try:
            cli_data = json.loads(cli_result.stdout)
        except json.JSONDecodeError:
            cli_data = {}
            failures.append("snapshot CLI should emit JSON")
        check(cli_data.get("write_performed") is True, "snapshot CLI should report write_performed=true", failures)
        check(cli_data.get("warnings", {}).get("external_write_performed") is False, "snapshot CLI should not report external write", failures)
        remove_path(cli_dir)
    finally:
        remove_path(snapshot_dir)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=5 failures={len(failures)}")
        return 1

    print("PASS snapshot temp write fixture")
    print("PASS existing output block fixture")
    print("PASS protected snapshot dir fixture")
    print("PASS outside output fixture")
    print("PASS snapshot CLI fixture")
    print("cases=5 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
