#!/usr/bin/env python3
"""Build the deterministic Phase 5C M0-C Plan R3 structural witness.

The builder executes only the declared synthetic temporary-root lifecycle proof.
It does not create an installable package, modify an extension, or access a
runtime, database, provider, VCPToolBox, private Memory, sensor, or effect.
"""

from __future__ import annotations

from pathlib import Path
import sys

import phase5c_m0c_r3_structural_core as core


def build() -> dict[str, object]:
    archive_profile, source_profile = core.load_profiles()
    members = core.derive_synthetic_members(archive_profile)
    archive_bytes = core.encode_exact_ustar(members)
    body: dict[str, object] = {
        "schema_version": "agents-os.m0c-plan-structural-witness.v0.1-r3",
        "environment": "SYNTHETIC_TEST",
        "archive_profile_sha256": core.sha256_file(core.ARCHIVE_PROFILE),
        "source_inventory_profile_sha256": core.sha256_file(core.SOURCE_PROFILE),
        "source_commitment": core.source_commitment(source_profile),
        "sealed_host_contract": archive_profile["sealed_host_contract"],
        "source_inventory": source_profile["records"],
        "archive_member_inventory": core.derive_archive_members(
            source_profile["records"], archive_profile["archive_encoding"]["root_prefix"]
        ),
        "manifest_evidence": {
            "blocked_manifest_b64": core.b64(core.BLOCKED_MANIFEST.read_bytes()),
            "enabled_manifest_paths": [],
        },
        "entrypoint": {"source_b64": core.b64(core.ENTRYPOINT.read_bytes())},
        "native_napi_methods": archive_profile["entrypoint_contract"]["native_NAPI_methods"],
        "synthetic_archive": {
            "members": members,
            "member_manifest_sha256": core.sha256_bytes(
                core.canonical([core.member_manifest_projection(row) for row in members])
            ),
            "archive_bytes_b64": core.b64(archive_bytes),
            "archive_sha256": core.sha256_bytes(archive_bytes),
            "archive_byte_length": len(archive_bytes),
        },
        "output_request": {"caller_output_path": None},
        "lifecycle_execution_proofs": core.run_lifecycle_proofs(archive_profile, archive_bytes),
        "terminal_outcome": "NOT_ACTIVATED",
    }
    body["root_fingerprint"] = core.sha256_bytes(core.canonical(body))
    return body


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    payload = core.canonical(build()) + b"\n"
    if output is None:
        sys.stdout.buffer.write(payload)
    else:
        output.write_bytes(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
