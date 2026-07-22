#!/usr/bin/env python3
"""Build the deterministic synthetic Phase 5C M0-C planning witness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "control-plane/registry/drafts/2026-07-22-agents-os-phase-5c-m0c-offline-plugin-packaging-build-profile-v0.1-r1.yaml"


def canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).rstrip(b"\n")).hexdigest()


def case(case_id: str, **changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "case_id": case_id,
        "environment": "SYNTHETIC_TEST",
        "source_sealed": True,
        "package_inventory_exact": True,
        "manifest_state": "BLOCKED",
        "host_contract_exact": True,
        "temporary_staging_only": True,
        "public_napi_method_count": 5,
        "vcptoolbox_write_count": 0,
        "runtime_activation_count": 0,
        "real_occurrence_count": 0,
    }
    row.update(changes)
    favorable = (
        row["environment"] == "SYNTHETIC_TEST"
        and row["source_sealed"] is True
        and row["package_inventory_exact"] is True
        and row["manifest_state"] == "BLOCKED"
        and row["host_contract_exact"] is True
        and row["temporary_staging_only"] is True
        and row["public_napi_method_count"] == 5
        and row["vcptoolbox_write_count"] == 0
        and row["runtime_activation_count"] == 0
        and row["real_occurrence_count"] == 0
    )
    row["derived_result"] = "PACKAGE_COMPATIBLE_PREVIEW" if favorable else "BLOCKED"
    row["row_fingerprint"] = digest(row)
    return row


def build() -> dict[str, object]:
    cases = [
        case("C01_BASELINE"),
        case("C02_ENABLED_MANIFEST", manifest_state="ENABLED"),
        case("C03_UNSEALED_SOURCE", source_sealed=False),
        case("C04_EXTRA_FILE", package_inventory_exact=False),
        case("C05_HOST_MISMATCH", host_contract_exact=False),
        case("C06_CALLER_STAGING", temporary_staging_only=False),
        case("C07_NAPI_EXPANSION", public_napi_method_count=6),
        case("C08_VCP_WRITE", vcptoolbox_write_count=1),
        case("C09_RUNTIME", runtime_activation_count=1),
        case("C10_REAL_OCCURRENCE", real_occurrence_count=1),
        case("C11_PRODUCTION_ENV", environment="PRODUCTION"),
    ]
    body: dict[str, object] = {
        "schema_version": "agents-os.m0c-plan-witness.v0.1-r1",
        "profile_sha256": hashlib.sha256(PROFILE.read_bytes()).hexdigest(),
        "sealed_host_input_count": 7,
        "public_napi_methods": [
            "execute_command",
            "execute_query",
            "claim_outbox",
            "acknowledge_outbox",
            "reconcile",
        ],
        "cases": cases,
        "terminal_outcome": "NOT_ACTIVATED",
    }
    body["root_fingerprint"] = digest(body)
    return body


def main() -> int:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    payload = canonical(build())
    if output:
        output.write_bytes(payload)
    else:
        sys.stdout.buffer.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
