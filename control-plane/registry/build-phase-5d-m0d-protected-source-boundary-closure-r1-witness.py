#!/usr/bin/env python3
"""Build the synthetic-only Phase 5D protected-source boundary witness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PROTECTED_PATHS = [
    "Plugin/CodeSearcher/config.env",
    "Plugin/DailyNote/config.env",
    "Plugin/FileOperator/config.env",
    "Plugin/LinuxShellExecutor/config.env",
    "Plugin/MagiAgent/config.env",
    "Plugin/NCBIDatasets/config.env",
    "Plugin/PowerShellExecutor/config.env",
]

ALLOWED_BLOBS = [
    {"path": "AGENTS.md", "blob_oid": "28f22b4de495a63f14ede8fe72698278c877cb8d", "sha256": "24b2a4c3e45a98107a726c8dfd80b577846052d49068bb1c13479f872bf0374b"},
    {"path": "Plugin/AGENTS.md", "blob_oid": "c2d23c041033b1f7d46b9dc3bdb2ba738566c872", "sha256": "b060ad148827faa37877deb8b170399a0f00f46bc194797949005c9bb62572d4"},
    {"path": "docs/PLUGIN_ECOSYSTEM.md", "blob_oid": "81dc779453ccf2fb56c1f57d1ecde8ff3ffda506", "sha256": "f806b90c4f7d46bd2113f8b5af9f773adce49b454d615e7b6aa8445663490a65"},
    {"path": "rust-vexus-lite/AGENTS.md", "blob_oid": "0fad4dba9bcbaa2452a362910b01e6275e5c352e", "sha256": "e5e68ad817c4fc7da657ce0d9c131db666eff97888b772ac31b9661210c93494"},
    {"path": "rust-vexus-lite/Cargo.toml", "blob_oid": "3682f96f45c095f85e0f3c93bc2d6c1f21c98dde", "sha256": "01f6f29f824418c58dc1c0a5243df514bd6b2bd5cd6a68de850c13e465e6eea9"},
    {"path": "rust-vexus-lite/package.json", "blob_oid": "232a95ef206e6ffab0cdff959826faaa10f6fedb", "sha256": "c996185f59cc84208077f854077f2f5451368ea9cd05c775ba0b06028fed7f7c"},
    {"path": "Plugin.js", "blob_oid": "5fd77cea37c30ef432f23d9627d05aba862b9744", "sha256": "be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2"},
]


def build_witness() -> dict[str, object]:
    return {
        "schema_version": "agents-os.phase5d.protected-source-boundary.synthetic-witness.v0.1",
        "scope": "SYNTHETIC_OBJECT_ONLY_NO_HOST",
        "sealed_host": {
            "commit": "555b3b538f6eb736e530c2912de678c5941f9985",
            "tree": "fd82d403e79f36f749eb7f555b4736eae3eacdff",
        },
        "protected_path_inventory": [
            {"path": path, "content_read": False, "materialized": False}
            for path in PROTECTED_PATHS
        ],
        "allowed_blob_objects": ALLOWED_BLOBS,
        "operation_sequence": [
            "VERIFY_GIT_OBJECT_MEMBERSHIP",
            "READ_TREE_NAMES_ONLY",
            "ASSERT_PROTECTED_PATHS_UNREAD",
            "READ_ONLY_ALLOWLISTED_BLOBS_BY_EXACT_OID",
            "MATERIALIZE_TWO_INERT_PAYLOAD_FILES_ONLY",
            "OWNED_QUARANTINE_CLEANUP",
        ],
        "forbidden_operations": [
            "git_worktree_add",
            "git_checkout",
            "git_sparse_checkout",
            "git_archive",
            "generic_tree_blob_enumeration",
            "arbitrary_git_show_path",
            "protected_blob_object_lookup",
            "protected_path_content_read",
            "Host_lifecycle_or_plugin_operation",
        ],
        "no_full_worktree_or_checkout": True,
        "host_operation_count": 0,
        "runtime_usable": False,
        "actual_execution_authorized": False,
        "result": "OBJECT_ONLY_PRECHECK_CANDIDATE",
    }


def canonical_bytes() -> bytes:
    return (json.dumps(build_witness(), ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = canonical_bytes()
    if args.output is None:
        print(data.decode("ascii"), end="")
    else:
        args.output.write_bytes(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
