#!/usr/bin/env python3
"""Fixture tests for read-only docctl trend."""

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
    snapshot_dir = ROOT / ".tmp-docctl-trend-snapshots"
    remove_path(snapshot_dir)

    try:
        current = docctl.trend()
        check(current["passed"], "current trend should pass", failures)
        check(current["trend_status"] in {"ready", "insufficient_snapshots"}, "trend should report a status", failures)
        check(current["warnings"]["snapshot_write_performed"] is False, "trend should not write snapshots", failures)

        snapshot_dir.mkdir(parents=True)
        (snapshot_dir / "2026-07-01.json").write_text(
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
        with_snapshot = docctl.trend(snapshot_dir=snapshot_dir)
        check(with_snapshot["passed"], "trend with snapshot should pass", failures)
        check(with_snapshot["snapshots_found"] == 1, "trend should find one snapshot", failures)
        check(with_snapshot["no_regression_from_latest"] is True, "current clean baseline should not regress from warning snapshot", failures)

        protected = docctl.trend(snapshot_dir=Path("state-private/snapshots"))
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
