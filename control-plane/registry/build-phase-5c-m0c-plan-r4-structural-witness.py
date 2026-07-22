#!/usr/bin/env python3
"""Build the deterministic Phase 5C M0-C Plan R4 structural witness."""

from __future__ import annotations

from pathlib import Path
import sys

import phase5c_m0c_r4_structural_core as core


def build() -> dict[str, object]:
    profile = core.load_profile()
    members = core.derive_synthetic_members(profile)
    archive_bytes = core.encode_exact_ustar(profile, members)
    body: dict[str, object] = {
        "schema_version": "agents-os.m0c-plan-structural-witness.v0.1-r4",
        "environment": "SYNTHETIC_TEST",
        "archive_profile_sha256": core.sha256_file(core.ARCHIVE_PROFILE),
        "synthetic_archive": {
            "members": members,
            "member_manifest_sha256": core.sha256_bytes(
                core.canonical([core.member_projection(row) for row in members])
            ),
            "archive_bytes_b64": core.b64(archive_bytes),
            "archive_sha256": core.sha256_bytes(archive_bytes),
            "archive_byte_length": len(archive_bytes),
        },
        "output_request": {"caller_output_path": None},
        "lifecycle_execution_proofs": core.run_lifecycle_proofs(profile, archive_bytes),
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
