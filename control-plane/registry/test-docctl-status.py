#!/usr/bin/env python3
"""Fixture tests for read-only docctl status pulse."""

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
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def main() -> int:
    docctl = load_docctl()
    failures: list[str] = []
    missing_snapshot_dir = ROOT / ".tmp-docctl-status-missing-snapshots"
    remove_path(missing_snapshot_dir)

    try:
        current = docctl.status()
        check(current["passed"], "current status should pass", failures)
        check(current["read_only"] is True, "status should be read-only", failures)
        check(current["would_write"] is False, "status should not write", failures)
        check(current["score"]["score"] == 100, "current score should be 100", failures)
        check(current["score"]["eligible_95"] is True, "current status should be 9.5 eligible", failures)
        check(current["trend"]["snapshots_found"] >= 1, "current status should see at least one snapshot", failures)
        check(current["plan_fix"]["plan_status"] == "no_action_needed", "current status should need no repair", failures)
        check(current["warnings"]["snapshot_writer_called"] is False, "status should not call snapshot writer", failures)
        check(current["warnings"]["registry_write_performed"] is False, "status should not write registries", failures)

        no_snapshot = docctl.status(snapshot_dir=missing_snapshot_dir)
        check(no_snapshot["passed"], "missing snapshot dir should not fail status", failures)
        check(no_snapshot["trend"]["trend_status"] == "insufficient_snapshots", "missing snapshot dir should be insufficient", failures)
        check(no_snapshot["trend"]["snapshots_found"] == 0, "missing snapshot dir should have zero snapshots", failures)
        check(not missing_snapshot_dir.exists(), "status should not create missing snapshot dir", failures)
        check("snapshot" in no_snapshot["next_recommended_action"], "missing snapshot dir should recommend reviewed snapshot", failures)

        protected = docctl.status(Path("state-private/federated.yaml"))
        check(not protected["passed"], "protected target should fail status", failures)
        check(protected["plan_fix"]["plan_status"] == "blocked", "protected target should block plan-fix", failures)
        check(protected["warnings"]["write_performed"] is False, "protected status should not write", failures)

        cli_json = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "status",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_json.returncode == 0, "status CLI JSON should pass on current registry", failures)
        try:
            cli_data = json.loads(cli_json.stdout)
        except json.JSONDecodeError:
            cli_data = {}
            failures.append("status CLI should emit JSON")
        check(cli_data.get("warnings", {}).get("snapshot_write_performed") is False, "status CLI should not write snapshot", failures)
        check(cli_data.get("warnings", {}).get("apply_fix_implemented") is False, "status CLI should not implement apply-fix", failures)

        cli_text = subprocess.run(
            [
                sys.executable,
                str(ROOT / "docctl.py"),
                "status",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_text.returncode == 0, "status CLI text should pass on current registry", failures)
        check("docctl status" in cli_text.stdout, "status CLI text should identify command", failures)
        check("Would write: False" in cli_text.stdout, "status CLI text should report no writes", failures)
    finally:
        remove_path(missing_snapshot_dir)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=5 failures={len(failures)}")
        return 1

    print("PASS current status fixture")
    print("PASS missing snapshot dir fixture")
    print("PASS protected target fixture")
    print("PASS status CLI JSON fixture")
    print("PASS status CLI text fixture")
    print("cases=5 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
