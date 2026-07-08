#!/usr/bin/env python3
"""Fixture tests for PR risk review helper."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType


ROOT = Path(__file__).resolve().parent


def load_review() -> ModuleType:
    module_path = ROOT / "pr-risk-review.py"
    spec = importlib.util.spec_from_file_location("pr_risk_review", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def surface_ids(result: dict) -> set[str]:
    return {surface["surface_id"] for surface in result.get("risk_surfaces", [])}


def main() -> int:
    review = load_review()
    failures: list[str] = []

    runtime = review.classify_paths(
        [
            "execution/codex-appserver-active-loop/package.json",
            "execution/codex-appserver-active-loop/src/bridge/repo_snapshot.ts",
        ],
        include_content=False,
    )
    check(runtime["proof_matrix_required"] is True, "runtime paths should require proof matrix", failures)
    check(
        "runtime_provenance_package_file_set" in surface_ids(runtime),
        "runtime paths should trigger runtime provenance surface",
        failures,
    )
    runtime_surface = next(
        surface for surface in runtime["risk_surfaces"] if surface["surface_id"] == "runtime_provenance_package_file_set"
    )
    check(
        "extra installed-only runtime file" in runtime_surface["negative_cases"],
        "runtime surface should require extra installed-only negative case",
        failures,
    )

    gate = review.classify_paths(
        [
            "control-plane/registry/docctl.py",
            "control-plane/registry/validate-document-registry.py",
            "ops/validation/validate-workspace.sh",
        ],
        include_content=False,
    )
    check("readiness_gate" in surface_ids(gate), "validator/docctl paths should trigger readiness gate surface", failures)
    check(
        "status_enum_operator_contract" in surface_ids(gate),
        "docctl/status paths should trigger status contract surface",
        failures,
    )

    auth_redaction = review.classify_paths(
        ["execution/runner/auth_proxy.py", "execution/runner/redaction_policy.py"],
        include_content=False,
    )
    check(
        "public_endpoint_oauth_auth_routing" in surface_ids(auth_redaction),
        "auth path should trigger public endpoint/auth surface",
        failures,
    )
    check(
        "redaction_secret_handling" in surface_ids(auth_redaction),
        "redaction path should trigger secret handling surface",
        failures,
    )

    docs_only = review.classify_paths(
        ["ops/records/colameta-pr-retrospectives/2026-07-09-pr12-installed-only-runtime-file-detection.md"],
        include_content=False,
    )
    check(docs_only["proof_matrix_required"] is False, "docs-only retrospective path should not require proof matrix", failures)

    cli_json = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pr-risk-review.py"),
            "--paths",
            "execution/codex-appserver-active-loop/package.json",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_json.returncode == 0, "CLI JSON should pass without strict mode", failures)
    try:
        cli_payload = json.loads(cli_json.stdout)
    except json.JSONDecodeError:
        cli_payload = {}
        failures.append("CLI JSON should parse")
    check(cli_payload.get("proof_matrix_required") is True, "CLI JSON should report proof matrix requirement", failures)

    cli_strict = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pr-risk-review.py"),
            "--paths",
            "execution/codex-appserver-active-loop/package.json",
            "--strict",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_strict.returncode == 1, "CLI strict mode should fail when proof matrix is required", failures)

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        handle.write('password = "should-not-be-read"\n')
        outside_path = handle.name
    try:
        cli_absolute = subprocess.run(
            [
                sys.executable,
                str(ROOT / "pr-risk-review.py"),
                "--paths",
                outside_path,
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        Path(outside_path).unlink(missing_ok=True)
    check(cli_absolute.returncode == 2, "CLI should reject absolute paths", failures)
    try:
        absolute_payload = json.loads(cli_absolute.stdout)
    except json.JSONDecodeError:
        absolute_payload = {}
        failures.append("CLI absolute path JSON should parse")
    check(absolute_payload.get("path_input_valid") is False, "absolute path should be invalid", failures)
    check(absolute_payload.get("risk_surface_count") == 0, "absolute path should not be content-scanned", failures)

    cli_traversal = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pr-risk-review.py"),
            "--paths",
            "../outside.py",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_traversal.returncode == 2, "CLI should reject parent traversal paths", failures)
    try:
        traversal_payload = json.loads(cli_traversal.stdout)
    except json.JSONDecodeError:
        traversal_payload = {}
        failures.append("CLI traversal JSON should parse")
    check(traversal_payload.get("path_input_valid") is False, "parent traversal path should be invalid", failures)

    denied_private = review.classify_paths(
        ["state-private/probe.py", "Credentials/helper.py", ".ENV.local"],
        include_content=True,
    )
    check(denied_private["path_input_valid"] is False, "private and credential paths should be invalid", failures)
    check(denied_private["invalid_path_count"] == 3, "all private path fixtures should be rejected", failures)
    check(denied_private["risk_surface_count"] == 0, "private paths should not be content-scanned", failures)

    cli_missing_base = subprocess.run(
        [
            sys.executable,
            str(ROOT / "pr-risk-review.py"),
            "--base",
            "refs/heads/__missing_pr_risk_review_base__",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    check(cli_missing_base.returncode == 2, "CLI should fail when branch diff discovery fails", failures)
    try:
        missing_base_payload = json.loads(cli_missing_base.stdout)
    except json.JSONDecodeError:
        missing_base_payload = {}
        failures.append("CLI missing base JSON should parse")
    check(
        missing_base_payload.get("git_discovery_valid") is False,
        "missing base should mark git discovery invalid",
        failures,
    )
    check(missing_base_payload.get("git_error_count") == 1, "missing base should report one git error", failures)

    option_base_output = Path("/tmp/pr-risk-review-should-not-write")
    option_base_output.unlink(missing_ok=True)
    try:
        cli_option_base = subprocess.run(
            [
                sys.executable,
                str(ROOT / "pr-risk-review.py"),
                "--base=--output=/tmp/pr-risk-review-should-not-write",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        check(cli_option_base.returncode == 2, "CLI should reject option-style base refs", failures)
        check(
            not option_base_output.exists(),
            "option-style base ref should not create files through git diff",
            failures,
        )
    finally:
        option_base_output.unlink(missing_ok=True)

    denied_secret_files = review.classify_paths(
        [
            "credentials.json",
            "application_default_credentials.json",
            "token.json",
            "prod-token.json",
            "prod-token.py",
            "api_key.txt",
            "cookies.txt",
            "secret_redaction.json",
            "secret.yaml",
            "config.env",
            ".envrc",
            ".envlocal",
            "private.pem",
            "deploy.key",
            "id_rsa",
            "id_ed25519",
        ],
        include_content=True,
    )
    check(denied_secret_files["path_input_valid"] is False, "secret-like filenames should be invalid", failures)
    check(
        denied_secret_files["invalid_path_count"] == 16,
        "all secret-like filename fixtures should be rejected",
        failures,
    )
    check(denied_secret_files["risk_surface_count"] == 0, "secret-like filenames should not be content-scanned", failures)
    check(
        all(item.get("path") == "[redacted]" for item in denied_secret_files["invalid_paths"]),
        "invalid protected paths should be redacted",
        failures,
    )

    denied_secret_dirs = review.classify_paths(
        [
            "secret/foo.py",
            "tokens/session.py",
            "cookies/session.py",
            ".env/settings.py",
            ".env.local/config.json",
            "config.env/settings.py",
        ],
        include_content=True,
    )
    check(denied_secret_dirs["path_input_valid"] is False, "secret and env directories should be invalid", failures)
    check(denied_secret_dirs["invalid_path_count"] == 6, "all secret directory fixtures should be rejected", failures)
    check(denied_secret_dirs["risk_surface_count"] == 0, "secret directories should not be content-scanned", failures)

    denied_private_classes = review.classify_paths(
        [
            "browser profiles/profile.json",
            "provider raw response/response.json",
            "private memory raw text/memory.py",
            "raw logs/run.log",
        ],
        include_content=True,
    )
    check(denied_private_classes["path_input_valid"] is False, "private path classes should be invalid", failures)
    check(
        denied_private_classes["invalid_path_count"] == 4,
        "all private path class fixtures should be rejected",
        failures,
    )
    check(
        denied_private_classes["risk_surface_count"] == 0,
        "private path classes should not be content-scanned",
        failures,
    )

    denied_secret_dir_variants = review.classify_paths(
        [
            "prod-secrets/config.yaml",
            "tokens-backup/session.yaml",
            "customer_credentials/data.py",
            "cookies-backup/session.yaml",
        ],
        include_content=True,
    )
    check(
        denied_secret_dir_variants["path_input_valid"] is False,
        "secret-like directory components should be invalid",
        failures,
    )
    check(
        denied_secret_dir_variants["invalid_path_count"] == 4,
        "all secret-like directory component fixtures should be rejected",
        failures,
    )
    check(
        denied_secret_dir_variants["risk_surface_count"] == 0,
        "secret-like directories should not be content-scanned",
        failures,
    )

    allowed_templates = review.classify_paths(
        ["config.env.example", ".env.example", "private.pem.template"],
        include_content=False,
    )
    check(allowed_templates["path_input_valid"] is True, "template filenames should remain valid", failures)

    legitimate_secret_handling_code = review.classify_paths(
        ["ops/validation/validate-no-secrets.sh", "control-plane/review/token_redaction.py"],
        include_content=False,
    )
    check(
        legitimate_secret_handling_code["path_input_valid"] is True,
        "legitimate secret-handling code paths should stay valid",
        failures,
    )
    check(
        "redaction_secret_handling" in surface_ids(legitimate_secret_handling_code),
        "legitimate secret-handling code paths should classify as redaction risk",
        failures,
    )

    original_workspace_root = review.WORKSPACE_ROOT
    with tempfile.TemporaryDirectory() as temp_repo:
        temp_root = Path(temp_repo)
        subprocess.run(["git", "init"], cwd=temp_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=temp_root, check=True)
        subprocess.run(["git", "config", "user.name", "PR Risk Test"], cwd=temp_root, check=True)
        (temp_root / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=temp_root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=temp_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        quoted_path_dir = temp_root / "state-private"
        quoted_path_dir.mkdir()
        (quoted_path_dir / "foo\nbar.py").write_text("# should not be scanned\n", encoding="utf-8")
        try:
            review.WORKSPACE_ROOT = temp_root
            git_discovery = review.run_git_changed_paths("HEAD")
            discovered = review.classify_paths(git_discovery["paths"], include_content=True)
        finally:
            review.WORKSPACE_ROOT = original_workspace_root
        check(
            discovered["path_input_valid"] is False,
            "git discovery should reject protected paths with escaped characters",
            failures,
        )
        check(
            discovered["invalid_path_count"] >= 1,
            "git discovery should report protected escaped path as invalid",
            failures,
        )

    original_workspace_root = review.WORKSPACE_ROOT
    with tempfile.TemporaryDirectory() as temp_repo:
        temp_root = Path(temp_repo)
        subprocess.run(["git", "init"], cwd=temp_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=temp_root, check=True)
        subprocess.run(["git", "config", "user.name", "PR Risk Test"], cwd=temp_root, check=True)
        probe = temp_root / "probe.py"
        probe.write_text("# safe base\n", encoding="utf-8")
        subprocess.run(["git", "add", "probe.py"], cwd=temp_root, check=True)
        subprocess.run(["git", "commit", "-m", "fixture"], cwd=temp_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        probe.write_text('password = "staged-risk"\n', encoding="utf-8")
        subprocess.run(["git", "add", "probe.py"], cwd=temp_root, check=True)
        probe.write_text("# safe worktree\n", encoding="utf-8")
        try:
            review.WORKSPACE_ROOT = temp_root
            staged_discovery = review.run_git_changed_paths("HEAD")
            staged_result = review.classify_paths(staged_discovery["paths"], include_content=True)
        finally:
            review.WORKSPACE_ROOT = original_workspace_root
        check(
            "redaction_secret_handling" in surface_ids(staged_result),
            "staged blob content should be scanned even when worktree content is safe",
            failures,
        )

    original_workspace_root = review.WORKSPACE_ROOT
    with tempfile.TemporaryDirectory() as temp_workspace:
        temp_root = Path(temp_workspace)
        private_dir = temp_root / "state-private"
        private_dir.mkdir()
        (private_dir / "probe.py").write_text('password = "should-not-be-read"\n', encoding="utf-8")
        (temp_root / "review-link").symlink_to(private_dir, target_is_directory=True)
        try:
            review.WORKSPACE_ROOT = temp_root
            symlinked_dir_result = review.classify_paths(
                ["review-link/probe.py"],
                include_content=True,
            )
        finally:
            review.WORKSPACE_ROOT = original_workspace_root
        check(
            symlinked_dir_result["risk_surface_count"] == 0,
            "files under symlinked directories should not be content-scanned",
            failures,
        )

    symlink_probe = ROOT / "__pr_risk_review_symlink_probe.py"
    symlink_target: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
            handle.write('password = "should-not-be-read"\n')
            symlink_target = Path(handle.name)
        if symlink_probe.exists() or symlink_probe.is_symlink():
            symlink_probe.unlink()
        symlink_probe.symlink_to(symlink_target)
        symlink_result = review.classify_paths(
            ["control-plane/review/__pr_risk_review_symlink_probe.py"],
            include_content=True,
        )
        check(
            symlink_result["risk_surface_count"] == 0,
            "symlinked files should not be content-scanned",
            failures,
        )
    except (OSError, NotImplementedError) as exc:
        failures.append(f"symlink fixture could not run: {exc}")
    finally:
        if symlink_probe.exists() or symlink_probe.is_symlink():
            symlink_probe.unlink()
        if symlink_target is not None:
            symlink_target.unlink(missing_ok=True)

    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"cases=20 failures={len(failures)}")
        return 1

    print("PASS runtime provenance risk fixture")
    print("PASS readiness/status risk fixture")
    print("PASS auth/redaction risk fixture")
    print("PASS docs-only no-risk fixture")
    print("PASS CLI JSON fixture")
    print("PASS CLI strict fixture")
    print("PASS CLI absolute path rejection fixture")
    print("PASS CLI parent traversal rejection fixture")
    print("PASS private path rejection fixture")
    print("PASS git discovery failure fixture")
    print("PASS option-style base rejection fixture")
    print("PASS secret-like filename rejection fixture")
    print("PASS protected secret directory rejection fixture")
    print("PASS private path class rejection fixture")
    print("PASS secret-like directory component rejection fixture")
    print("PASS allowed template filename fixture")
    print("PASS legitimate secret-handling path fixture")
    print("PASS NUL-separated git path discovery fixture")
    print("PASS staged blob content fixture")
    print("PASS symlink content-scan rejection fixture")
    print("cases=20 failures=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
