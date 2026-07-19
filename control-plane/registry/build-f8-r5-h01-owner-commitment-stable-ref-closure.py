#!/usr/bin/env python3
"""Build the deterministic synthetic F8 R5 H01 owner-binding witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DOMAIN = "agents-os:f8-r5-h01-owner-commitment-stable-ref-closure:v0.1"
R2_FIXTURE_SHA256 = "36d60ffc0ff0b184c7d306b6293601a3661a22affe1cab8b00da609cb280f501"
R2_H01_ROW_FINGERPRINT = "867b7f110b5ee7c34c314850f20ff488a8574c77164ded7d06736b6b3b085787"
CONSUMER_FIELDS = [
    "assessment_id",
    "expected_assessment_revision",
    "expected_assessment_fingerprint",
    "owner_commitment_ref",
    "expected_owner_commitment_revision",
    "expected_owner_commitment_fingerprint",
]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def plain_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def signed(tag: str, row: dict[str, Any], field: str = "row_fingerprint") -> dict[str, Any]:
    result = dict(row)
    result[field] = digest(tag, row)
    return result


def locate_h01(r2_fixture: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in r2_fixture["handoff_cases"] if row.get("case_id") == "H01"]
    if len(rows) != 1:
        raise ValueError("R2 fixture must contain exactly one H01")
    row = rows[0]
    if row.get("row_fingerprint") != R2_H01_ROW_FINGERPRINT:
        raise ValueError("R2 H01 fingerprint mismatch")
    return row


def owner_source_records(h01: dict[str, Any], r2_fixture: dict[str, Any]) -> list[dict[str, Any]]:
    assessments = {row["assessment_id"]: row for row in r2_fixture["upstream_assessments"]}
    records: list[dict[str, Any]] = []
    for role, consumer in sorted(h01["raw_input"]["assessment_consumers"].items()):
        if consumer["assessment_id"] is None:
            continue
        assessment = assessments[consumer["assessment_id"]]
        issued_event = {
            "owner_contract": assessment["owner_contract"],
            "role": role,
            "assessment_id": consumer["assessment_id"],
            "assessment_revision": consumer["expected_assessment_revision"],
            "issued_event_ref": f"synthetic://{assessment['owner_contract'].lower()}/event/r5-h01-{role}-commitment",
            "issued_event_sequence": 100,
        }
        base = {
            "role": role,
            "owner_contract": assessment["owner_contract"],
            "commitment_ref": f"synthetic://{assessment['owner_contract'].lower()}/assessment-commitment/r5-h01-{role}@1",
            "commitment_revision": 1,
            "assessment_id": consumer["assessment_id"],
            "assessment_revision": consumer["expected_assessment_revision"],
            "assessment_fingerprint": consumer["expected_assessment_fingerprint"],
            "issued_event_ref": issued_event["issued_event_ref"],
            "issued_event_sequence": issued_event["issued_event_sequence"],
            "issued_event_fingerprint": digest(DOMAIN + ":owner-issued-event", issued_event),
        }
        records.append(signed(DOMAIN + ":trusted-owner-commitment", base, "commitment_fingerprint"))
    return records


def upgraded_consumers(h01: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_role = {record["role"]: record for record in records}
    result: dict[str, dict[str, Any]] = {}
    for role, consumer in sorted(h01["raw_input"]["assessment_consumers"].items()):
        first_three = {
            "assessment_id": consumer["assessment_id"],
            "expected_assessment_revision": consumer["expected_assessment_revision"],
            "expected_assessment_fingerprint": consumer["expected_assessment_fingerprint"],
        }
        if consumer["assessment_id"] is None:
            result[role] = {**first_three, **{
                "owner_commitment_ref": None,
                "expected_owner_commitment_revision": None,
                "expected_owner_commitment_fingerprint": None,
            }}
            continue
        record = by_role[role]
        result[role] = {**first_three, **{
            "owner_commitment_ref": record["commitment_ref"],
            "expected_owner_commitment_revision": record["commitment_revision"],
            "expected_owner_commitment_fingerprint": record["commitment_fingerprint"],
        }}
    return result


def resolution_rows(
    upgraded: dict[str, dict[str, Any]], records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_role = {record["role"]: record for record in records}
    rows: list[dict[str, Any]] = []
    for role, consumer in sorted(upgraded.items()):
        if consumer["assessment_id"] is None:
            rows.append(signed(DOMAIN + ":owner-resolution", {
                "role": role,
                "consumer": consumer,
                "resolved_commitment_ref": None,
                "resolved_commitment_revision": None,
                "resolved_commitment_fingerprint": None,
                "resolution": "OPTIONAL_ALL_NULL_NO_LOOKUP",
                "owner_lookup_performed": False,
            }))
            continue
        record = by_role[role]
        rows.append(signed(DOMAIN + ":owner-resolution", {
            "role": role,
            "consumer": consumer,
            "resolved_commitment_ref": record["commitment_ref"],
            "resolved_commitment_revision": record["commitment_revision"],
            "resolved_commitment_fingerprint": record["commitment_fingerprint"],
            "resolution": "EXACT_TRUSTED_OWNER_COMMITMENT",
            "owner_lookup_performed": True,
        }))
    return rows


def build_fixture(r2_fixture: dict[str, Any]) -> dict[str, Any]:
    h01 = locate_h01(r2_fixture)
    records = owner_source_records(h01, r2_fixture)
    upgraded = upgraded_consumers(h01, records)
    resolutions = resolution_rows(upgraded, records)
    source_consumers = h01["raw_input"]["assessment_consumers"]
    downprojected = {
        role: {key: consumer[key] for key in CONSUMER_FIELDS[:3]}
        for role, consumer in upgraded.items()
    }
    trusted_anchor = digest(DOMAIN + ":trusted-owner-source-anchor", records)

    schema_inventory = [
        signed(DOMAIN + ":schema", {
            "schema_id": "TrustedH01OwnerCommitmentV0_1R5",
            "fields": [
                "role", "owner_contract", "commitment_ref", "commitment_revision",
                "assessment_id", "assessment_revision", "assessment_fingerprint",
                "issued_event_ref", "issued_event_sequence", "issued_event_fingerprint",
                "commitment_fingerprint",
            ],
            "closed": True,
        }, "schema_fingerprint"),
        signed(DOMAIN + ":schema", {
            "schema_id": "H01OwnerCommitmentResolutionV0_1R5",
            "fields": [
                "role", "consumer", "resolved_commitment_ref",
                "resolved_commitment_revision", "resolved_commitment_fingerprint",
                "resolution", "owner_lookup_performed", "row_fingerprint",
            ],
            "closed": True,
        }, "schema_fingerprint"),
        signed(DOMAIN + ":schema", {
            "schema_id": "MergedR2R3R4H01DerivationV0_1R5",
            "fields": [
                "source_case_id", "source_row_fingerprint",
                "source_raw_input_fingerprint", "source_consumer_inventory_fingerprint",
                "trusted_owner_source_anchor", "upgraded_consumers",
                "owner_commitment_resolutions",
                "downprojected_consumer_inventory_fingerprint", "derived_decision",
                "row_fingerprint",
            ],
            "closed": True,
        }, "schema_fingerprint"),
    ]

    derived_decision = h01["claimed_decision"]
    merged_case = signed(DOMAIN + ":merged-H01-derivation", {
        "source_case_id": "H01",
        "source_row_fingerprint": h01["row_fingerprint"],
        "source_raw_input_fingerprint": plain_sha(h01["raw_input"]),
        "source_consumer_inventory_fingerprint": plain_sha(source_consumers),
        "trusted_owner_source_anchor": trusted_anchor,
        "upgraded_consumers": upgraded,
        "owner_commitment_resolutions": resolutions,
        "downprojected_consumer_inventory_fingerprint": plain_sha(downprojected),
        "derived_decision": derived_decision,
    })

    stable_ref_vectors = [
        signed(DOMAIN + ":stable-ref-vector", {
            "case_id": "SR-NFC-INTERNAL-SPACE",
            "input_kind": "LITERAL",
            "literal_value": "synthetic://owner commitment/h01",
            "codepoints": None,
            "expected_valid": True,
        }),
        signed(DOMAIN + ":stable-ref-vector", {
            "case_id": "SR-NON-NFC-CODEPOINTS",
            "input_kind": "CODEPOINTS",
            "literal_value": None,
            "codepoints": [115, 121, 110, 116, 104, 101, 116, 105, 99, 58, 47, 47, 99, 97, 102, 101, 769],
            "expected_valid": False,
        }),
    ]

    boundary = {
        "runtime_usable_count": 0,
        "real_Home_count": 0,
        "real_Command_count": 0,
        "task_write_count": 0,
        "database_write_count": 0,
        "provider_call_count": 0,
        "production_authentication_count": 0,
        "private_Memory_read_count": 0,
        "sensing_or_recording_count": 0,
        "external_effect_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }

    fixture = {
        "schema_version": "agents-os.f8-r5-h01-owner-commitment-stable-ref-closure-witness.v0.1",
        "contract_id": "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R5",
        "environment": "SYNTHETIC_TEST",
        "runtime_usable": False,
        "domain_tag": DOMAIN,
        "schema_inventory": schema_inventory,
        "trusted_H01_owner_commitment_source": records,
        "merged_H01_derivation_cases": [merged_case],
        "stable_ref_vectors": stable_ref_vectors,
        "boundary_assertions": boundary,
    }
    section_names = [
        "schema_inventory",
        "trusted_H01_owner_commitment_source",
        "merged_H01_derivation_cases",
        "stable_ref_vectors",
        "boundary_assertions",
    ]
    fixture["section_fingerprints"] = {
        name: digest(DOMAIN + ":section:" + name, fixture[name]) for name in section_names
    }
    fixture["root_fingerprint"] = digest(DOMAIN + ":root", fixture)
    return fixture


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r2-fixture",
        default="control-plane/registry/examples/2026-07-19-agents-os-f8-r2-evidence-currentness-schema-closure-v0.1.json",
    )
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = Path(args.r2_fixture)
    if hashlib.sha256(source.read_bytes()).hexdigest() != R2_FIXTURE_SHA256:
        raise SystemExit("R2 fixture hash mismatch")
    r2_fixture = json.loads(source.read_text(encoding="utf-8"))
    output = Path(args.output)
    output.write_text(
        json.dumps(build_fixture(r2_fixture), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
