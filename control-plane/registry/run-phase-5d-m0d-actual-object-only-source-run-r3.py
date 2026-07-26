#!/usr/bin/env python3
"""Fail-closed R3 runner for the Phase 5D object-only source run.

Import, --self-test and --fixture are offline-only.  --actual is intentionally
present for a later decision, but is not called while R3 is authored or
reviewed.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import signal
import stat
import subprocess
import sys
from typing import Any, Final


CHECKOUT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT: Final[Path] = Path("/home/jenn/AGENTS_OS_Workspace")
CANONICAL_ROOT: Final[Path] = WORKSPACE_ROOT / "runtime/VCPToolBox"
GIT_DIR: Final[Path] = CANONICAL_ROOT / ".git"
OBJECT_DIRECTORY: Final[Path] = GIT_DIR / "objects"
SEALED_COMMIT: Final[str] = "555b3b538f6eb736e530c2912de678c5941f9985"
SEALED_TREE: Final[str] = "fd82d403e79f36f749eb7f555b4736eae3eacdff"
RUN_ID: Final[str] = "PHASE5D_M0D_ACTUAL_OBJECT_ONLY_SOURCE_RUN_20260725_V0_1"
RUN_ROOT: Final[Path] = Path("/tmp/agents-os-phase5d-m0d-object-only-source-run-555b3b538f6e")
OWNERSHIP_MARKER: Final[Path] = RUN_ROOT / ".agents-os-owner"
TEMPORARY_RESULT: Final[Path] = RUN_ROOT / "result.yaml"
RECEIPT_TARGET: Final[Path] = (
    WORKSPACE_ROOT
    / "control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-actual-object-only-source-run-v0.1.yaml"
)
FIXTURE_RELATIVE: Final[str] = (
    "control-plane/registry/examples/"
    "2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-r3-synthetic-fixture-v0.1.json"
)
REVIEW_MANIFEST_RELATIVE: Final[str] = (
    "control-plane/registry/reports/"
    "2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-r3-atomic-independent-review-package-v0.1.manifest.yaml"
)
REVIEW_UNIT: Final[str] = "PHASE_5D_M0D_ACTUAL_OBJECT_ONLY_SOURCE_RUN_DECISION_PACKAGE_V0_1_R3_ATOMIC_BUNDLE"
SCANNER_RECORD_ID: Final[str] = "R2_scanner_verified_source"
SCANNER_SOURCE_RELATIVE: Final[str] = "control-plane/registry/object-only-source-run-r2-scanner.py"
EXPECTED_PROTECTED_INVENTORY_SHA256: Final[str] = "52349f79221f041a48134331666315686ed6185b0838c56c13b1e9ed3b247011"
TUPLE_SET_PREIMAGE_SHA256: Final[str] = "3c7ce3d7ecb615874288b2a735afae5428d79144c45352bd4dc38084ca1605ce"


@dataclass(frozen=True)
class TupleSpec:
    identifier: str
    path: str
    blob_oid: str
    sha256: str


TUPLES: Final[tuple[TupleSpec, ...]] = (
    TupleSpec("T01", "AGENTS.md", "28f22b4de495a63f14ede8fe72698278c877cb8d", "24b2a4c3e45a98107a726c8dfd80b577846052d49068bb1c13479f872bf0374b"),
    TupleSpec("T02", "Plugin/AGENTS.md", "c2d23c041033b1f7d46b9dc3bdb2ba738566c872", "b060ad148827faa37877deb8b170399a0f00f46bc194797949005c9bb62572d4"),
    TupleSpec("T03", "docs/PLUGIN_ECOSYSTEM.md", "81dc779453ccf2fb56c1f57d1ecde8ff3ffda506", "f806b90c4f7d46bd2113f8b5af9f773adce49b454d615e7b6aa8445663490a65"),
    TupleSpec("T04", "rust-vexus-lite/AGENTS.md", "0fad4dba9bcbaa2452a362910b01e6275e5c352e", "e5e68ad817c4fc7da657ce0d9c131db666eff97888b772ac31b9661210c93494"),
    TupleSpec("T05", "rust-vexus-lite/Cargo.toml", "3682f96f45c095f85e0f3c93bc2d6c1f21c98dde", "01f6f29f824418c58dc1c0a5243df514bd6b2bd5cd6a68de850c13e465e6eea9"),
    TupleSpec("T06", "rust-vexus-lite/package.json", "232a95ef206e6ffab0cdff959826faaa10f6fedb", "c996185f59cc84208077f854077f2f5451368ea9cd05c775ba0b06028fed7f7c"),
    TupleSpec("T07", "Plugin.js", "5fd77cea37c30ef432f23d9627d05aba862b9744", "be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2"),
)
EXPECTED_COMMAND_IDS: Final[tuple[str, ...]] = (
    "G01_COMMIT_EXISTS", "G02_TREE_RESOLVE", "G03_NAME_ONLY_SCAN",
    *(f"{item.identifier}_{phase}" for item in TUPLES for phase in ("RESOLVE", "TYPE", "DIGEST")),
)
assert len(EXPECTED_COMMAND_IDS) == 24

# Paths and identities are closed here; hashes remain in the R3 manifest to
# avoid a source/manifest self-hash cycle and are verified before actual mode.
EXPECTED_REVIEW_RECORDS: Final[dict[str, tuple[tuple[str, str], ...]]] = {
    "subjects": (
        ("R3_amendment", "control-plane/registry/drafts/2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-r3-amendment-v0.1.md"),
        ("R3_successor_decision_package", "control-plane/registry/reports/2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-decision-package-v0.3.md"),
        ("R3_runner", "control-plane/registry/run-phase-5d-m0d-actual-object-only-source-run-r3.py"),
        ("R3_fixture_builder", "control-plane/registry/build-phase-5d-m0d-actual-object-only-source-run-r3-fixture.py"),
        ("R3_synthetic_fixture", FIXTURE_RELATIVE),
        ("R3_validator", "control-plane/registry/validate-phase-5d-m0d-actual-object-only-source-run-r3.py"),
        ("R3_inherited_review_package_builder", "control-plane/registry/build-phase-5d-m0d-actual-object-only-source-run-r2-review-package.py"),
    ),
    "authority_inputs": (
        ("R2_manifest", "control-plane/registry/reports/2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-r2-atomic-independent-review-package-v0.1.manifest.yaml"),
        ("R2_independent_review", "control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-actual-object-only-source-run-r2-full-atomic-independent-review.yaml"),
        (SCANNER_RECORD_ID, SCANNER_SOURCE_RELATIVE),
        ("R3_narrow_start_decision", "control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-actual-object-only-source-run-r3-narrow-correction-start-decision-v0.1.yaml"),
        ("protected_source_boundary_freeze_decision", "control-plane/registry/decisions/2026-07-24-agents-os-phase-5d-m0d-protected-source-boundary-closure-r1-atomic-freeze-decision-v0.1.yaml"),
        ("protected_source_boundary_contract", "control-plane/registry/drafts/2026-07-24-agents-os-phase-5d-m0d-protected-source-boundary-closure-v0.1-r1.md"),
        ("current_stop_queue", "control-plane/registry/reports/2026-07-24-agents-os-active-work-queue-v18.7.md"),
    ),
    "author_evidence": (
        ("R3_author_self_review", "control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-actual-object-only-source-run-r3-author-self-review.yaml"),
    ),
}
EXPECTED_REVIEW_RECORD_COUNT: Final[int] = sum(len(items) for items in EXPECTED_REVIEW_RECORDS.values())
PROTECTED_PARTS: Final[frozenset[str]] = frozenset({"state-private", "secrets", "secret", "credentials", "tokens", "cookies"})
CATCHABLE_SIGNALS: Final[frozenset[int]] = frozenset({signal.SIGINT, signal.SIGTERM, signal.SIGHUP})
MARKER_BYTES: Final[bytes] = b"run_id=PHASE5D_M0D_ACTUAL_OBJECT_ONLY_SOURCE_RUN_20260725_V0_1\nsealed_commit=555b3b538f6eb736e530c2912de678c5941f9985\n"
TEMPORARY_RESULT_BYTES: Final[bytes] = b"status: IN_PROGRESS\nsource_bytes_persisted: false\n"


class Blocked(RuntimeError):
    def __init__(self, result: str, phase: str) -> None:
        super().__init__(result)
        self.result = result
        self.phase = phase


@dataclass
class RunState:
    command_ids: list[str] = field(default_factory=list)
    root_created: bool = False
    protected_name_count: int = 0
    allowlisted_blob_content_reads: int = 0
    cleanup_status: str = "NOT_STARTED"
    result: str = "BLOCKED_INTERNAL_UNINITIALIZED"
    failure_phase: str | None = "preflight"


def git_environment() -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin", "HOME": "/nonexistent", "LC_ALL": "C",
        "GIT_DIR": str(GIT_DIR), "GIT_OBJECT_DIRECTORY": str(OBJECT_DIRECTORY),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": "", "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat",
    }


def _reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _safe_relative(value: Any) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("unsafe path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} or part in PROTECTED_PARTS for part in path.parts):
        raise ValueError("unsafe path")
    if path.parts[-1] == ".env" or path.parts[-1].startswith(".env.") or path.parts[-1] == "config.env":
        raise ValueError("unsafe path")
    return path.as_posix()


def _read_regular_root_file(root_path: Path, relative: str, phase: str) -> bytes:
    try:
        safe = _safe_relative(relative)
        root = root_path.resolve(strict=True)
        if root != root_path:
            raise ValueError("workspace realpath")
        candidate = root.joinpath(*PurePosixPath(safe).parts)
        direct = os.lstat(candidate)
        resolved = candidate.resolve(strict=True)
        if stat.S_ISLNK(direct.st_mode) or not stat.S_ISREG(direct.st_mode) or resolved != candidate:
            raise ValueError("workspace source shape")
        descriptor = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW)
    except (OSError, ValueError) as exc:
        raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", phase) from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", phase)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        os.close(descriptor)


def _read_regular_workspace_file(relative: str, phase: str) -> bytes:
    return _read_regular_root_file(WORKSPACE_ROOT, relative, phase)


def _read_regular_checkout_file(relative: str, phase: str) -> bytes:
    return _read_regular_root_file(CHECKOUT_ROOT, relative, phase)


def _valid_sha256(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _parse_bound_manifest(raw: bytes) -> tuple[tuple[dict[str, str], ...], str]:
    document = json.loads(raw.decode("utf-8"), object_pairs_hook=_reject_duplicate_json_keys)
    if type(document) is not dict or set(document) != {"schema_version", "review_unit", "atomic", "partial_review", "subjects", "authority_inputs", "author_evidence", "fixed_commands"}:
        raise ValueError("manifest keys")
    if document["schema_version"] != "agents-os.hash-bound-independent-review-package.v0.1" or document["review_unit"] != REVIEW_UNIT or document["atomic"] is not True or document["partial_review"] != "forbidden":
        raise ValueError("manifest shape")
    if type(document["fixed_commands"]) is not list or len(document["fixed_commands"]) != 7 or any(type(value) is not str or not value for value in document["fixed_commands"]):
        raise ValueError("manifest commands")
    records: list[dict[str, str]] = []
    successor_digest: str | None = None
    for group, expected in EXPECTED_REVIEW_RECORDS.items():
        entries = document[group]
        if type(entries) is not list or len(entries) != len(expected):
            raise ValueError("manifest count")
        for entry, (identifier, path) in zip(entries, expected, strict=True):
            if type(entry) is not dict or set(entry) != {"id", "path", "sha256"}:
                raise ValueError("manifest record keys")
            if entry["id"] != identifier or entry["path"] != path or not _valid_sha256(entry["sha256"]):
                raise ValueError("manifest record")
            records.append(entry)
            if identifier == "R3_successor_decision_package":
                successor_digest = entry["sha256"]
    if len(records) != EXPECTED_REVIEW_RECORD_COUNT or len({entry["path"] for entry in records}) != len(records) or successor_digest is None:
        raise ValueError("manifest inventory")
    return tuple(records), successor_digest


def _verify_bound_manifest() -> tuple[dict[str, bytes], str]:
    try:
        records, successor_digest = _parse_bound_manifest(_read_regular_workspace_file(REVIEW_MANIFEST_RELATIVE, "manifest"))
        sources = {entry["id"]: _read_regular_workspace_file(entry["path"], "manifest_source") for entry in records}
    except (Blocked, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", "manifest") from exc
    for entry in records:
        if sha256(sources[entry["id"]]).hexdigest() != entry["sha256"]:
            raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", "manifest_hash")
    return sources, successor_digest


def _load_verified_scanner(source: bytes, expected_digest: str) -> dict[str, Any]:
    if sha256(source).hexdigest() != expected_digest:
        raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", "scanner_digest")
    namespace: dict[str, Any] = {"__name__": "agents_os_r3_verified_scanner", "__file__": str(WORKSPACE_ROOT / SCANNER_SOURCE_RELATIVE)}
    try:
        exec(compile(source, namespace["__file__"], "exec"), namespace, namespace)
    except Exception as exc:
        raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", "scanner_load") from exc
    if not callable(namespace.get("scan_name_only_stream")) or not isinstance(namespace.get("EXPECTED_PROTECTED_INVENTORY_SHA256"), str):
        raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", "scanner_shape")
    if namespace["EXPECTED_PROTECTED_INVENTORY_SHA256"] != EXPECTED_PROTECTED_INVENTORY_SHA256:
        raise Blocked("BLOCKED_REVIEW_BINDING_MISMATCH", "scanner_inventory")
    return namespace


def _lstat(path: Path, phase: str) -> os.stat_result:
    try:
        return os.lstat(path)
    except OSError as exc:
        raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", phase) from exc


def _require_directory(path: Path, phase: str, exact_realpath: bool = False) -> None:
    item = _lstat(path, phase)
    if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
        raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", phase)
    if exact_realpath and path.resolve(strict=True) != path:
        raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", phase)


def _require_absent(path: Path, phase: str) -> None:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", phase) from exc
    raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", phase)


def _assert_preconditions() -> None:
    if Path.cwd().resolve() != WORKSPACE_ROOT:
        raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", "working_directory")
    _require_directory(CANONICAL_ROOT, "canonical_root", exact_realpath=True)
    _require_directory(GIT_DIR, "git_directory")
    _require_directory(OBJECT_DIRECTORY, "object_directory")
    info = OBJECT_DIRECTORY / "info"
    if info.exists():
        _require_directory(info, "object_info")
    _require_absent(info / "alternates", "alternates")
    _require_directory(RUN_ROOT.parent, "temporary_parent")
    _require_absent(RUN_ROOT, "run_root")
    current = WORKSPACE_ROOT
    _require_directory(current, "workspace_root", exact_realpath=True)
    for part in RECEIPT_TARGET.relative_to(WORKSPACE_ROOT).parent.parts:
        current = current / part
        _require_directory(current, "receipt_parent")
    _require_absent(RECEIPT_TARGET, "receipt_target")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(signal, "pthread_sigmask") or not hasattr(signal, "sigpending"):
        raise Blocked("BLOCKED_LOCAL_TOOLING_UNAVAILABLE", "platform")


def _write_exclusive(path: Path, content: bytes, phase: str) -> None:
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    except OSError as exc:
        raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", phase) from exc
    try:
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise Blocked("BLOCKED_RECEIPT_WRITE_UNVERIFIED", phase)
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _create_owned_root(state: RunState) -> None:
    try:
        os.mkdir(RUN_ROOT, 0o700)
    except OSError as exc:
        raise Blocked("BLOCKED_PREEXISTING_OR_UNOWNED_PATH", "run_root_create") from exc
    state.root_created = True
    _write_exclusive(OWNERSHIP_MARKER, MARKER_BYTES, "ownership_marker")
    _write_exclusive(TEMPORARY_RESULT, TEMPORARY_RESULT_BYTES, "temporary_result")


def _finalize_owned_root(state: RunState) -> str:
    if not state.root_created:
        return "NOT_CREATED"
    try:
        descriptor = os.open(OWNERSHIP_MARKER, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            if os.read(descriptor, len(MARKER_BYTES) + 1) != MARKER_BYTES:
                return "RESIDUE_UNVERIFIED"
        finally:
            os.close(descriptor)
        if not stat.S_ISREG(_lstat(TEMPORARY_RESULT, "temporary_result").st_mode):
            return "RESIDUE_UNVERIFIED"
        os.unlink(TEMPORARY_RESULT)
        os.unlink(OWNERSHIP_MARKER)
        os.rmdir(RUN_ROOT)
        try:
            os.lstat(RUN_ROOT)
        except FileNotFoundError:
            return "CLEAN"
    except (Blocked, OSError):
        pass
    return "RESIDUE_UNVERIFIED"


def _git_scalar(state: RunState, identifier: str, arguments: list[str], phase: str) -> str:
    try:
        completed = subprocess.run(["git", f"--git-dir={GIT_DIR}", *arguments], cwd=WORKSPACE_ROOT, env=git_environment(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    except OSError as exc:
        raise Blocked("BLOCKED_LOCAL_TOOLING_UNAVAILABLE", phase) from exc
    state.command_ids.append(identifier)
    if completed.returncode != 0:
        raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", phase)
    try:
        return completed.stdout.decode("ascii", "strict").strip()
    except UnicodeDecodeError as exc:
        raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", phase) from exc


def _git_name_stream(state: RunState) -> bytes:
    try:
        completed = subprocess.run(["git", f"--git-dir={GIT_DIR}", "ls-tree", "-r", "--name-only", "-z", SEALED_COMMIT, "--"], cwd=WORKSPACE_ROOT, env=git_environment(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    except OSError as exc:
        raise Blocked("BLOCKED_LOCAL_TOOLING_UNAVAILABLE", "name_only_scan") from exc
    state.command_ids.append("G03_NAME_ONLY_SCAN")
    if completed.returncode != 0:
        raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", "name_only_scan")
    return completed.stdout


def _git_digest(state: RunState, item: TupleSpec) -> str:
    try:
        child = subprocess.Popen(["git", f"--git-dir={GIT_DIR}", "cat-file", "blob", item.blob_oid], cwd=WORKSPACE_ROOT, env=git_environment(), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError as exc:
        raise Blocked("BLOCKED_LOCAL_TOOLING_UNAVAILABLE", f"{item.identifier}_digest") from exc
    assert child.stdout is not None
    digest = sha256()
    try:
        for chunk in iter(lambda: child.stdout.read(65536), b""):
            digest.update(chunk)
    finally:
        child.stdout.close()
    state.command_ids.append(f"{item.identifier}_DIGEST")
    if child.wait() != 0:
        raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", f"{item.identifier}_digest")
    return digest.hexdigest()


def _run_exact_inventory(state: RunState, scanner: dict[str, Any]) -> None:
    if _git_scalar(state, "G01_COMMIT_EXISTS", ["cat-file", "-e", f"{SEALED_COMMIT}^{{commit}}"], "commit_exists"):
        raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", "commit_exists_output")
    if _git_scalar(state, "G02_TREE_RESOLVE", ["rev-parse", f"{SEALED_COMMIT}^{{tree}}"], "tree_resolve") != SEALED_TREE:
        raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", "tree_resolve")
    try:
        scan = scanner["scan_name_only_stream"](_git_name_stream(state))
    except Exception as exc:
        raise Blocked("BLOCKED_PROTECTED_PATH_INVENTORY_MISMATCH", "name_only_scan") from exc
    state.protected_name_count = scan.protected_name_count
    for item in TUPLES:
        if _git_scalar(state, f"{item.identifier}_RESOLVE", ["rev-parse", f"{SEALED_COMMIT}:{item.path}"], f"{item.identifier}_resolve") != item.blob_oid:
            raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", f"{item.identifier}_resolve")
        if _git_scalar(state, f"{item.identifier}_TYPE", ["cat-file", "-t", item.blob_oid], f"{item.identifier}_type") != "blob":
            raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", f"{item.identifier}_type")
        if _git_digest(state, item) != item.sha256:
            raise Blocked("BLOCKED_SEALED_SOURCE_OR_TUPLE_MISMATCH", f"{item.identifier}_digest")
        state.allowlisted_blob_content_reads += 1
    if tuple(state.command_ids) != EXPECTED_COMMAND_IDS:
        raise Blocked("BLOCKED_UNAUTHORIZED_OR_NONHERMETIC_GIT_OPERATION", "command_inventory")


class SignalGuard:
    def __init__(self) -> None:
        self.previous_mask: set[int] | None = None

    def enter(self) -> None:
        self.previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, CATCHABLE_SIGNALS)

    def has_pending(self) -> bool:
        return bool(signal.sigpending() & CATCHABLE_SIGNALS)

    def restore_failure_mask(self) -> None:
        if self.previous_mask is not None:
            signal.pthread_sigmask(signal.SIG_SETMASK, self.previous_mask)

    def success_exit(self) -> None:
        # Catchable signals remain blocked.  There is no post-receipt unmasking
        # interval in which a pending SIGTERM can contradict a success receipt.
        os._exit(0)


def _receipt_bytes(state: RunState, package_sha256: str) -> bytes:
    values = {
        "schema_version": "agents-os.phase5d.actual-object-only-source-run-receipt.v0.1",
        "run_id": RUN_ID, "package_sha256": package_sha256,
        "sealed_commit": SEALED_COMMIT, "sealed_tree": SEALED_TREE,
        "tuple_set_preimage_sha256": TUPLE_SET_PREIMAGE_SHA256, "tuple_count": len(TUPLES),
        "protected_name_inventory_preimage_sha256": EXPECTED_PROTECTED_INVENTORY_SHA256,
        "protected_name_count": state.protected_name_count, "protected_blob_content_reads": 0,
        "allowlisted_blob_content_reads": state.allowlisted_blob_content_reads,
        "Git_command_count": len(state.command_ids), "Host_operation_count": 0,
        "worktree_created": False, "payload_files_created": 0,
        "stdout_bytes_emitted": 0, "stderr_bytes_emitted": 0,
        "cleanup_status": state.cleanup_status, "result": state.result,
        "failure_phase": state.failure_phase,
    }
    return json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _write_receipt(state: RunState, package_sha256: str) -> None:
    _write_exclusive(RECEIPT_TARGET, _receipt_bytes(state, package_sha256), "receipt")


def run_actual() -> int:
    state = RunState()
    package_sha256 = "UNAVAILABLE"
    guard = SignalGuard()
    try:
        guard.enter()
        sources, package_sha256 = _verify_bound_manifest()
        _assert_preconditions()
        _create_owned_root(state)
        scanner = _load_verified_scanner(sources[SCANNER_RECORD_ID], sha256(sources[SCANNER_RECORD_ID]).hexdigest())
        _run_exact_inventory(state, scanner)
        if guard.has_pending():
            raise Blocked("BLOCKED_INTERRUPTED_OR_SIGNALLED", "pending_signal_before_terminal_commit")
        state.result = "OBJECT_ONLY_SOURCE_RUN_EVIDENCE_CANDIDATE_ONLY"
        state.failure_phase = None
    except Blocked as exc:
        state.result, state.failure_phase = exc.result, exc.phase
    except Exception:
        state.result, state.failure_phase = "BLOCKED_UNEXPECTED_RUNNER_FAILURE", "runner"
    finally:
        state.cleanup_status = _finalize_owned_root(state)
        if state.cleanup_status not in {"CLEAN", "NOT_CREATED"}:
            state.result, state.failure_phase = "BLOCKED_CLEANUP_OR_RESIDUE_UNVERIFIED", "finalizer"
        if state.result == "OBJECT_ONLY_SOURCE_RUN_EVIDENCE_CANDIDATE_ONLY" and guard.has_pending():
            state.result, state.failure_phase = "BLOCKED_INTERRUPTED_OR_SIGNALLED", "pending_signal_terminal_commit"
        try:
            _write_receipt(state, package_sha256)
        except Exception:
            state.result, state.failure_phase = "BLOCKED_RECEIPT_WRITE_UNVERIFIED", "receipt"
        if state.result == "OBJECT_ONLY_SOURCE_RUN_EVIDENCE_CANDIDATE_ONLY":
            guard.success_exit()
        guard.restore_failure_mask()
    return 1


def synthetic_fixture() -> dict[str, Any]:
    return {
        "schema_version": "agents-os.phase5d.actual-object-only-source-run-r3.synthetic-fixture.v0.1",
        "run_id": RUN_ID,
        "environment": git_environment(),
        "review_binding": {"manifest_relative": REVIEW_MANIFEST_RELATIVE, "review_unit": REVIEW_UNIT, "record_count": EXPECTED_REVIEW_RECORD_COUNT, "scanner_executes_after_hash_verification": True},
        "fixture_input": {"mode_has_no_path_argument": True, "relative": FIXTURE_RELATIVE, "regular_realpath_nofollow": True},
        "signal_terminal_commit": {"catchable_signals_masked_for_full_run": True, "pending_checked_before_success_receipt": True, "success_exit_without_unmask": True},
        "command_ids": list(EXPECTED_COMMAND_IDS),
        "expected_success": {"result": "OBJECT_ONLY_SOURCE_RUN_EVIDENCE_CANDIDATE_ONLY", "Git_command_count": 24, "protected_blob_content_reads": 0, "allowlisted_blob_content_reads": 7, "Host_operation_count": 0, "cleanup_status": "CLEAN", "worktree_created": False},
    }


def validate_synthetic_fixture(document: Any) -> list[str]:
    expected = synthetic_fixture()
    return [] if document == expected else ["fixture:EXACT_MISMATCH"]


def _load_fixed_fixture() -> Any:
    try:
        return json.loads(_read_regular_checkout_file(FIXTURE_RELATIVE, "fixture").decode("utf-8"), object_pairs_hook=_reject_duplicate_json_keys)
    except (Blocked, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise Blocked("BLOCKED_FIXED_FIXTURE_INPUT", "fixture") from exc


def self_test() -> int:
    baseline = synthetic_fixture()
    cases: list[tuple[str, Any, bool]] = [("baseline", baseline, True)]
    for name, mutate in (
        ("replace_objects", lambda item: item["environment"].__setitem__("GIT_NO_REPLACE_OBJECTS", "0")),
        ("scanner_before_verify", lambda item: item["review_binding"].__setitem__("scanner_executes_after_hash_verification", False)),
        ("fixture_path", lambda item: item["fixture_input"].__setitem__("mode_has_no_path_argument", False)),
        ("terminal_unmask", lambda item: item["signal_terminal_commit"].__setitem__("success_exit_without_unmask", False)),
        ("extra_command", lambda item: item["command_ids"].append("EXTRA")),
    ):
        mutated = copy.deepcopy(baseline)
        mutate(mutated)
        cases.append((name, mutated, False))
    failures = [name for name, document, accepted in cases if (not validate_synthetic_fixture(document)) is not accepted]
    evil = b"raise RuntimeError('top-level side effect must not run')\n"
    try:
        _load_verified_scanner(evil, "0" * 64)
        failures.append("substituted_scanner")
    except Blocked:
        pass
    try:
        _safe_relative("state-private/forbidden.json")
        failures.append("protected_path")
    except ValueError:
        pass
    print(json.dumps({"result": "PASS" if not failures else "BLOCKED", "cases": len(cases) + 2, "failures": failures}, sort_keys=True))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--fixture", action="store_true")
    mode.add_argument("--actual", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.fixture:
        try:
            errors = validate_synthetic_fixture(_load_fixed_fixture())
        except Blocked:
            errors = ["fixture:BLOCKED"]
        print(json.dumps({"result": "PASS_NO_BLOCKER" if not errors else "BLOCKED", "errors": errors}, sort_keys=True))
        return 0 if not errors else 1
    return run_actual()


if __name__ == "__main__":
    raise SystemExit(main())
