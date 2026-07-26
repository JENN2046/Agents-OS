#!/usr/bin/env python3
"""Build a deterministic, no-follow R2 review ZIP from one verified snapshot."""

from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
from typing import Any, NamedTuple
import zipfile


WORKSPACE = Path(__file__).resolve().parents[2]
REPORTS_RELATIVE = PurePosixPath("control-plane/registry/reports")
FIXED_ZIP_TIME = (2026, 7, 25, 0, 0, 0)
PROTECTED_PARTS = {
    "state-private",
    "secret",
    "secrets",
    "credential",
    "credentials",
    "token",
    "tokens",
    "cookie",
    "cookies",
}


class FileSnapshot(NamedTuple):
    path: str
    content: bytes
    sha256: str
    device: int
    inode: int


class BoundRecord(NamedTuple):
    identifier: str
    path: str
    sha256: str
    content: bytes


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def safe_relative(value: str) -> PurePosixPath:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError("unsafe path")
    item = PurePosixPath(value)
    if item.is_absolute() or any(part in {"", ".", ".."} for part in item.parts):
        raise ValueError("unsafe path")
    lowered = {part.lower() for part in item.parts}
    if lowered & PROTECTED_PARTS:
        raise ValueError("unsafe path")
    if any(
        part.lower() == ".env"
        or part.lower().startswith(".env.")
        or part.lower() == "config.env"
        for part in item.parts
    ):
        raise ValueError("unsafe path")
    return item


def workspace_relative(path: Path) -> PurePosixPath:
    root = Path(os.path.abspath(WORKSPACE))
    candidate = Path(os.path.abspath(path))
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("workspace escape") from exc
    return safe_relative(relative.as_posix())


def _open_workspace_root() -> int:
    root = Path(os.path.abspath(WORKSPACE))
    try:
        direct = os.lstat(root)
        if (
            stat.S_ISLNK(direct.st_mode)
            or not stat.S_ISDIR(direct.st_mode)
            or root.resolve(strict=True) != root
        ):
            raise ValueError("workspace root shape")
        descriptor = os.open(
            root,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
        )
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            raise ValueError("workspace root descriptor")
        return descriptor
    except OSError as exc:
        raise ValueError("workspace root") from exc


def read_workspace_snapshot(value: str) -> FileSnapshot:
    relative = safe_relative(value)
    descriptor = _open_workspace_root()
    try:
        directory_flags = (
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
        )
        for part in relative.parts[:-1]:
            next_descriptor = os.open(part, directory_flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        file_descriptor = os.open(
            relative.parts[-1],
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=descriptor,
        )
    except OSError as exc:
        try:
            os.close(descriptor)
        except OSError:
            pass
        raise ValueError("workspace source path") from exc
    try:
        before = os.fstat(file_descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise ValueError("workspace source shape")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(file_descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(file_descriptor)
        content = b"".join(chunks)
        if (
            not stat.S_ISREG(after.st_mode)
            or after.st_nlink != 1
            or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
            or before.st_size != after.st_size
            or before.st_mtime_ns != after.st_mtime_ns
            or before.st_ctime_ns != after.st_ctime_ns
            or len(content) != after.st_size
        ):
            raise ValueError("workspace source changed while reading")
        return FileSnapshot(
            path=relative.as_posix(),
            content=content,
            sha256=sha256(content).hexdigest(),
            device=after.st_dev,
            inode=after.st_ino,
        )
    finally:
        os.close(file_descriptor)
        os.close(descriptor)


def load_manifest(path: Path) -> tuple[dict[str, Any], FileSnapshot]:
    relative = workspace_relative(path)
    if relative.parent != REPORTS_RELATIVE:
        raise ValueError("manifest location")
    snapshot = read_workspace_snapshot(relative.as_posix())
    document = json.loads(
        snapshot.content.decode("utf-8"),
        object_pairs_hook=reject_duplicate_json_keys,
    )
    if type(document) is not dict or set(document) != {
        "schema_version",
        "review_unit",
        "atomic",
        "partial_review",
        "subjects",
        "authority_inputs",
        "author_evidence",
        "fixed_commands",
    }:
        raise ValueError("manifest keys")
    if (
        type(document["schema_version"]) is not str
        or not document["schema_version"]
        or type(document["review_unit"]) is not str
        or not document["review_unit"]
        or document["atomic"] is not True
        or document["partial_review"] != "forbidden"
    ):
        raise ValueError("manifest shape")
    for field in ("subjects", "authority_inputs", "author_evidence"):
        if type(document[field]) is not list:
            raise ValueError("manifest list")
    if type(document["fixed_commands"]) is not list or any(
        type(command) is not str or not command
        for command in document["fixed_commands"]
    ):
        raise ValueError("fixed commands")
    return document, snapshot


def valid_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def records(document: dict[str, Any]) -> list[BoundRecord]:
    result: list[BoundRecord] = []
    for group in ("subjects", "authority_inputs", "author_evidence"):
        for item in document[group]:
            if type(item) is not dict or set(item) != {"id", "path", "sha256"}:
                raise ValueError("record keys")
            if (
                type(item["id"]) is not str
                or not item["id"]
                or type(item["path"]) is not str
                or not valid_sha256(item["sha256"])
            ):
                raise ValueError("record type")
            snapshot = read_workspace_snapshot(item["path"])
            if snapshot.sha256 != item["sha256"]:
                raise ValueError("record hash")
            result.append(
                BoundRecord(
                    identifier=item["id"],
                    path=snapshot.path,
                    sha256=snapshot.sha256,
                    content=snapshot.content,
                )
            )
    if len({item.path for item in result}) != len(result):
        raise ValueError("duplicate path")
    if len({item.identifier for item in result}) != len(result):
        raise ValueError("duplicate id")
    return result


def write_entry(archive: zipfile.ZipFile, name: str, content: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = (0o100644 & 0xFFFF) << 16
    archive.writestr(info, content)


def build_archive_bytes(
    manifest_content: bytes,
    checked: list[BoundRecord],
) -> bytes:
    archive_map: list[dict[str, str]] = []
    stream = io.BytesIO()
    with zipfile.ZipFile(
        stream,
        "w",
        compression=zipfile.ZIP_STORED,
        allowZip64=False,
    ) as archive:
        write_entry(archive, "MANIFEST.yaml", manifest_content)
        for item in checked:
            payload_name = f"payload/{item.path}"
            write_entry(archive, payload_name, item.content)
            archive_map.append(
                {
                    "archive_path": payload_name,
                    "path": item.path,
                    "sha256": item.sha256,
                }
            )
        archive_map_bytes = (
            json.dumps(
                archive_map,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("ascii")
        write_entry(archive, "ARCHIVE_MAP.json", archive_map_bytes)
    return stream.getvalue()


def write_output_exclusive(output_path: Path, content: bytes) -> None:
    descriptor: int | None = None
    identity: tuple[int, int] | None = None
    candidate = Path(os.path.abspath(output_path))
    try:
        descriptor = os.open(
            candidate,
            os.O_RDWR
            | os.O_CREAT
            | os.O_EXCL
            | os.O_CLOEXEC
            | os.O_NOFOLLOW,
            0o600,
        )
        os.fchmod(descriptor, 0o600)
        created = os.fstat(descriptor)
        if not stat.S_ISREG(created.st_mode) or created.st_nlink != 1:
            raise OSError("output shape")
        identity = (created.st_dev, created.st_ino)
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("output write made no progress")
            view = view[written:]
        os.ftruncate(descriptor, len(content))
        os.fsync(descriptor)
        before_readback = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
        if (
            (after.st_dev, after.st_ino) != identity
            or after.st_nlink != 1
            or stat.S_IMODE(after.st_mode) != 0o600
            or after.st_size != len(content)
            or before_readback.st_size != after.st_size
            or before_readback.st_mtime_ns != after.st_mtime_ns
            or before_readback.st_ctime_ns != after.st_ctime_ns
            or b"".join(chunks) != content
        ):
            raise OSError("output identity")
        os.close(descriptor)
        descriptor = None
    except Exception:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if identity is not None:
            try:
                current = os.lstat(candidate)
                if (current.st_dev, current.st_ino) == identity:
                    os.unlink(candidate)
            except OSError:
                pass
        raise


def build(manifest_path: Path, output_path: Path) -> None:
    document, manifest_snapshot = load_manifest(manifest_path)
    checked = records(document)
    archive_bytes = build_archive_bytes(manifest_snapshot.content, checked)
    write_output_exclusive(output_path, archive_bytes)


def _fixture_document(path: str, digest_value: str) -> dict[str, Any]:
    return {
        "schema_version": "agents-os.hash-bound-independent-review-package.v0.1",
        "review_unit": "SELF_TEST",
        "atomic": True,
        "partial_review": "forbidden",
        "subjects": [
            {"id": "subject", "path": path, "sha256": digest_value}
        ],
        "authority_inputs": [],
        "author_evidence": [],
        "fixed_commands": ["offline-self-test"],
    }


def self_test() -> int:
    failures: list[str] = []
    cases = 0
    original_workspace = WORKSPACE
    original_write_entry = write_entry
    try:
        with tempfile.TemporaryDirectory(
            prefix="agents-os-r2-review-builder-"
        ) as directory:
            root = Path(directory)
            reports = root / REPORTS_RELATIVE
            examples = root / "control-plane/registry/examples"
            protected = root / "state-private"
            reports.mkdir(parents=True)
            examples.mkdir(parents=True)
            protected.mkdir()
            globals()["WORKSPACE"] = root

            source = examples / "source.txt"
            original_content = b"verified snapshot\n"
            source.write_bytes(original_content)
            relative_source = source.relative_to(root).as_posix()
            document = _fixture_document(
                relative_source,
                sha256(original_content).hexdigest(),
            )
            manifest = reports / "manifest.json"
            manifest_bytes = (
                json.dumps(document, sort_keys=True, separators=(",", ":"))
                + "\n"
            ).encode("utf-8")
            manifest.write_bytes(manifest_bytes)

            baseline_output = root / "baseline.zip"
            try:
                build(manifest, baseline_output)
                with zipfile.ZipFile(baseline_output) as archive:
                    archived_map = json.loads(
                        archive.read("ARCHIVE_MAP.json"),
                        object_pairs_hook=reject_duplicate_json_keys,
                    )
                    if archive.read("MANIFEST.yaml") != manifest_bytes:
                        failures.append("baseline_manifest_bytes")
                    if (
                        archive.read(f"payload/{relative_source}")
                        != original_content
                    ):
                        failures.append("baseline_payload_bytes")
                    if archived_map != [
                        {
                            "archive_path": f"payload/{relative_source}",
                            "path": relative_source,
                            "sha256": sha256(original_content).hexdigest(),
                        }
                    ]:
                        failures.append("baseline_archive_map")
            except Exception:
                failures.append("baseline_build")
            cases += 1

            duplicate_top = reports / "duplicate-top.json"
            duplicate_top.write_bytes(
                manifest_bytes.replace(
                    b'"atomic":true',
                    b'"atomic":false,"atomic":true',
                    1,
                )
            )
            try:
                build(duplicate_top, root / "duplicate-top.zip")
                failures.append("duplicate_top_level_accepted")
            except ValueError:
                pass
            cases += 1

            duplicate_record = reports / "duplicate-record.json"
            duplicate_record.write_bytes(
                manifest_bytes.replace(
                    b'"path":"control-plane/registry/examples/source.txt"',
                    b'"path":"state-private/hidden","path":"control-plane/registry/examples/source.txt"',
                    1,
                )
            )
            try:
                build(duplicate_record, root / "duplicate-record.zip")
                failures.append("duplicate_record_key_accepted")
            except ValueError:
                pass
            cases += 1

            protected_source = protected / "hidden.txt"
            protected_source.write_bytes(b"must not archive\n")
            symlink_source = examples / "linked-source.txt"
            symlink_source.symlink_to(protected_source)
            symlink_document = _fixture_document(
                symlink_source.relative_to(root).as_posix(),
                sha256(protected_source.read_bytes()).hexdigest(),
            )
            symlink_manifest = reports / "symlink.json"
            symlink_manifest.write_text(
                json.dumps(
                    symlink_document,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            symlink_output = root / "symlink.zip"
            try:
                build(symlink_manifest, symlink_output)
                failures.append("symlink_source_accepted")
            except ValueError:
                pass
            if symlink_output.exists():
                failures.append("symlink_output_created")
            cases += 1

            linked_directory = examples / "linked-directory"
            linked_directory.symlink_to(protected, target_is_directory=True)
            intermediate_document = _fixture_document(
                (
                    linked_directory.relative_to(root)
                    / protected_source.name
                ).as_posix(),
                sha256(protected_source.read_bytes()).hexdigest(),
            )
            intermediate_manifest = reports / "intermediate-symlink.json"
            intermediate_manifest.write_text(
                json.dumps(
                    intermediate_document,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            intermediate_output = root / "intermediate-symlink.zip"
            try:
                build(intermediate_manifest, intermediate_output)
                failures.append("intermediate_symlink_accepted")
            except ValueError:
                pass
            if intermediate_output.exists():
                failures.append("intermediate_symlink_output_created")
            cases += 1

            hardlink_source = examples / "hardlink-source.txt"
            os.link(protected_source, hardlink_source)
            hardlink_document = _fixture_document(
                hardlink_source.relative_to(root).as_posix(),
                sha256(protected_source.read_bytes()).hexdigest(),
            )
            hardlink_manifest = reports / "hardlink.json"
            hardlink_manifest.write_text(
                json.dumps(
                    hardlink_document,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
            )
            hardlink_output = root / "hardlink.zip"
            try:
                build(hardlink_manifest, hardlink_output)
                failures.append("hardlink_source_accepted")
            except ValueError:
                pass
            if hardlink_output.exists():
                failures.append("hardlink_output_created")
            cases += 1

            swap_output = root / "swap.zip"
            swap_state = {"performed": False}

            def swap_before_first_archive_entry(
                archive: zipfile.ZipFile,
                name: str,
                content: bytes,
            ) -> None:
                if not swap_state["performed"]:
                    replacement = examples / "replacement.txt"
                    replacement.write_bytes(b"unverified replacement\n")
                    os.replace(replacement, source)
                    swap_state["performed"] = True
                original_write_entry(archive, name, content)

            globals()["write_entry"] = swap_before_first_archive_entry
            try:
                build(manifest, swap_output)
            except Exception:
                failures.append("snapshot_swap_build")
            finally:
                globals()["write_entry"] = original_write_entry
            try:
                with zipfile.ZipFile(swap_output) as archive:
                    archived_payload = archive.read(
                        f"payload/{relative_source}"
                    )
                    archived_map = json.loads(
                        archive.read("ARCHIVE_MAP.json"),
                        object_pairs_hook=reject_duplicate_json_keys,
                    )
                if archived_payload != original_content:
                    failures.append("snapshot_swap_payload")
                if archived_map[0]["sha256"] != sha256(
                    original_content
                ).hexdigest():
                    failures.append("snapshot_swap_map")
                if source.read_bytes() == original_content:
                    failures.append("snapshot_swap_not_injected")
            except Exception:
                failures.append("snapshot_swap_verify")
            cases += 1
    finally:
        globals()["WORKSPACE"] = original_workspace
        globals()["write_entry"] = original_write_entry

    print(
        json.dumps(
            {
                "result": "PASS" if not failures else "BLOCKED",
                "cases": cases,
                "failures": failures,
            },
            sort_keys=True,
        )
    )
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("manifest", type=Path, nargs="?")
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()
    if args.self_test:
        if args.manifest is not None or args.output is not None:
            parser.error("--self-test does not accept manifest/output")
        return self_test()
    if args.manifest is None or args.output is None:
        parser.error("manifest and output are required")
    try:
        build(args.manifest, args.output)
    except (
        OSError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
    ) as exc:
        raise SystemExit(f"BLOCKED:{type(exc).__name__}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
