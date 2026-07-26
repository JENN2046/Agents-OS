#!/usr/bin/env python3
"""Offline validator for the narrow Phase 5D object-only source-run R3 bundle."""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).parent
RUNNER_PATH = ROOT / "run-phase-5d-m0d-actual-object-only-source-run-r3.py"
RUNNER = runpy.run_path(str(RUNNER_PATH))


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _fixed_fixture() -> Any:
    return json.loads((ROOT / "examples/2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-r3-synthetic-fixture-v0.1.json").read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)


def validate(document: Any) -> list[str]:
    errors = list(RUNNER["validate_synthetic_fixture"](document))
    source = RUNNER_PATH.read_text(encoding="utf-8")
    for required in (
        "def _load_verified_scanner",
        "def _verify_bound_manifest",
        "exec(compile(source",
        "signal.SIG_BLOCK, CATCHABLE_SIGNALS",
        "pending_signal_terminal_commit",
        "guard.success_exit()",
        "def _load_fixed_fixture",
        "mode.add_argument(\"--fixture\", action=\"store_true\")",
        "os.O_RDONLY | os.O_NOFOLLOW",
    ):
        if required not in source:
            errors.append(f"runner:SOURCE_BINDING:{required}")
    if "runpy" in source:
        errors.append("runner:TOP_LEVEL_DYNAMIC_SCANNER_LOAD")
    if source.index("_write_receipt(state, package_sha256)") > source.index("guard.success_exit()"):
        errors.append("runner:SUCCESS_COMMIT_ORDER")
    return errors


def _subprocess(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=ROOT.parent.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def self_test() -> int:
    baseline = _fixed_fixture()
    cases: list[tuple[str, Any, bool]] = [("baseline", baseline, True)]
    for name, mutate in (
        ("replace_objects", lambda item: item["environment"].__setitem__("GIT_NO_REPLACE_OBJECTS", "0")),
        ("scanner_early", lambda item: item["review_binding"].__setitem__("scanner_executes_after_hash_verification", False)),
        ("fixture_path", lambda item: item["fixture_input"].__setitem__("mode_has_no_path_argument", False)),
        ("terminal_unmask", lambda item: item["signal_terminal_commit"].__setitem__("success_exit_without_unmask", False)),
    ):
        mutated = copy.deepcopy(baseline)
        mutate(mutated)
        cases.append((name, mutated, False))
    failures = [name for name, document, should_pass in cases if (not validate(document)) is not should_pass]

    with tempfile.TemporaryDirectory(prefix="agents-os-r3-validator-") as directory:
        marker = Path(directory) / "scanner-side-effect"
        evil = f"from pathlib import Path\nPath({str(marker)!r}).write_text('executed')\n".encode("utf-8")
        try:
            RUNNER["_load_verified_scanner"](evil, "0" * 64)
            failures.append("scanner_substitution_accepted")
        except RUNNER["Blocked"]:
            pass
        if marker.exists():
            failures.append("scanner_top_level_side_effect")

        fixture_link = Path(directory) / "fixture-link.json"
        fixture_link.symlink_to(ROOT / "examples/2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-r3-synthetic-fixture-v0.1.json")
        rejected = _subprocess([sys.executable, str(RUNNER_PATH), "--fixture", str(fixture_link)])
        if rejected.returncode == 0:
            failures.append("caller_fixture_path_accepted")
        valid = _subprocess([sys.executable, str(RUNNER_PATH), "--fixture"])
        if valid.returncode != 0 or b'"result": "PASS_NO_BLOCKER"' not in valid.stdout:
            failures.append("fixed_fixture_failed")

    probe = (
        "import os,runpy,signal;"
        f"r=runpy.run_path({str(RUNNER_PATH)!r});g=r['SignalGuard']();g.enter();"
        "os.kill(os.getpid(),signal.SIGTERM);"
        "assert g.has_pending();os._exit(0)"
    )
    pending = _subprocess([sys.executable, "-c", probe])
    if pending.returncode != 0:
        failures.append("pending_signal_probe")
    direct_exit = (
        "import runpy;"
        f"r=runpy.run_path({str(RUNNER_PATH)!r});g=r['SignalGuard']();g.enter();"
        "assert not g.has_pending();g.success_exit()"
    )
    if _subprocess([sys.executable, "-c", direct_exit]).returncode != 0:
        failures.append("success_exit_probe")
    print(json.dumps({"result": "PASS" if not failures else "BLOCKED", "cases": len(cases) + 5, "failures": failures}, sort_keys=True))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fixture", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    errors = validate(_fixed_fixture())
    print(json.dumps({"result": "PASS_NO_BLOCKER" if not errors else "BLOCKED", "errors": errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
