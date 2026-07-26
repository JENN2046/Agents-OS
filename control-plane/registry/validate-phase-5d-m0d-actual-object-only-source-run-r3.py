#!/usr/bin/env python3
"""Offline validator for the narrow Phase 5D object-only source-run R3 bundle."""

from __future__ import annotations

import argparse
import ast
from contextlib import redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import runpy
import shutil
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
        "ACTUAL_DENIAL_RESULT",
        "def _actual_denial_document",
        "def deny_actual",
        "return deny_actual()",
        "\"actual_mode_entered\": False",
        "\"actual_object_only_source_run_authorized\": False",
        "\"authenticated_external_decision_present\": False",
        "\"receipt_write_attempted\": False",
        "\"run_root_created\": False",
        "\"VCPToolBox_Git_command_count\": 0",
        "exec(compile(source",
        "signal.SIG_BLOCK, CATCHABLE_SIGNALS",
        "def success_exit",
        "def _commit_receipt_atomically",
        "rename_receipt_noreplace(parent_fd, temp_name, target_name)",
        "fsync_receipt_parent_fd(parent_fd)",
        "def _load_fixed_fixture",
        "CHECKOUT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]",
        "_read_regular_checkout_file(FIXTURE_RELATIVE, \"fixture\")",
        "mode.add_argument(\"--fixture\", action=\"store_true\")",
        "os.O_RDONLY | os.O_NOFOLLOW",
    ):
        if required not in source:
            errors.append(f"runner:SOURCE_BINDING:{required}")
    for forbidden in (
        "EXPECTED_REVIEW_MANIFEST_SHA256",
        "def _verify_bound_manifest",
        "def run_actual",
    ):
        if forbidden in source:
            errors.append(f"runner:LIVE_ACTUAL_OR_SELF_HASH_CYCLE:{forbidden}")
    if "runpy" in source:
        errors.append("runner:TOP_LEVEL_DYNAMIC_SCANNER_LOAD")
    if "sha256(sources[SCANNER_RECORD_ID]).hexdigest()" in source:
        errors.append("runner:TAUTOLOGICAL_SCANNER_DIGEST")
    if "_write_exclusive(RECEIPT_TARGET" in source:
        errors.append("runner:NONTRANSACTIONAL_RECEIPT_WRITE")
    tree = ast.parse(source)
    denial = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "deny_actual"
        ),
        None,
    )
    if denial is None:
        errors.append("runner:ACTUAL_DENIAL_FUNCTION_MISSING")
    else:
        dangerous = {
            "_assert_preconditions",
            "_create_owned_root",
            "_load_verified_scanner",
            "_run_exact_inventory",
            "_write_receipt",
            "_commit_receipt_atomically",
            "subprocess",
        }
        called = {
            node.func.id
            for node in ast.walk(denial)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        if called & dangerous:
            errors.append("runner:ACTUAL_DENIAL_HAS_EFFECT_CALL")
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
    expected_denial = {
        "result": RUNNER["ACTUAL_DENIAL_RESULT"],
        "actual_mode_entered": False,
        "actual_object_only_source_run_authorized": False,
        "authenticated_external_decision_present": False,
        "receipt_write_attempted": False,
        "run_root_created": False,
        "VCPToolBox_Git_command_count": 0,
    }
    if RUNNER["_actual_denial_document"]() != expected_denial:
        failures.append("actual_denial_document_mismatch")
    guarded_helpers = (
        "_assert_preconditions",
        "_create_owned_root",
        "_load_verified_scanner",
        "_run_exact_inventory",
        "_write_receipt",
        "_commit_receipt_atomically",
    )
    originals = {name: RUNNER[name] for name in guarded_helpers}

    def unexpected_effect(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("actual denial attempted an effect")

    for name in guarded_helpers:
        RUNNER[name] = unexpected_effect
    denial_output = io.StringIO()
    try:
        with redirect_stdout(denial_output):
            denial_status = RUNNER["deny_actual"]()
    except AssertionError:
        failures.append("actual_denial_attempted_effect")
        denial_status = 0
    finally:
        RUNNER.update(originals)
    try:
        emitted_denial = json.loads(denial_output.getvalue(), object_pairs_hook=_no_duplicates)
    except (json.JSONDecodeError, ValueError):
        emitted_denial = None
    if denial_status != 1 or emitted_denial != expected_denial:
        failures.append("actual_denial_output_mismatch")

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
        runner_self_test = _subprocess([sys.executable, str(RUNNER_PATH), "--self-test"])
        if (
            runner_self_test.returncode != 0
            or b'"result": "PASS"' not in runner_self_test.stdout
        ):
            failures.append("runner_self_test_failed")

        checkout_root = Path(directory) / "portable-checkout"
        checkout_registry = checkout_root / "control-plane" / "registry"
        checkout_examples = checkout_registry / "examples"
        checkout_examples.mkdir(parents=True)
        checkout_runner = checkout_registry / RUNNER_PATH.name
        checkout_fixture = checkout_examples / RUNNER["FIXTURE_RELATIVE"].split("/")[-1]
        shutil.copyfile(RUNNER_PATH, checkout_runner)
        shutil.copyfile(ROOT / RUNNER["FIXTURE_RELATIVE"].removeprefix("control-plane/registry/"), checkout_fixture)
        portable = subprocess.run(
            [sys.executable, str(checkout_runner), "--fixture"],
            cwd=checkout_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if portable.returncode != 0 or b'"result": "PASS_NO_BLOCKER"' not in portable.stdout:
            failures.append("portable_checkout_fixture_failed")

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
    print(json.dumps({"result": "PASS" if not failures else "BLOCKED", "cases": len(cases) + 9, "failures": failures}, sort_keys=True))
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
