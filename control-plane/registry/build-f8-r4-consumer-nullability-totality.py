#!/usr/bin/env python3
"""Build the deterministic synthetic F8 R4 consumer-totality witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DOMAIN = "agents-os:f8-r4-consumer-nullability-totality:v0.1"
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


def signed(tag: str, row: dict[str, Any], field: str = "row_fingerprint") -> dict[str, Any]:
    result = dict(row)
    result[field] = digest(tag, row)
    return result


def all_null_consumer() -> dict[str, Any]:
    return {field: None for field in CONSUMER_FIELDS}


def owner_commitment_tuple(role: str, assessment: dict[str, Any]) -> dict[str, Any]:
    base = {
        "role": role,
        "assessment_id": assessment["assessment_id"],
        "assessment_revision": assessment["expected_assessment_revision"],
        "assessment_fingerprint": assessment["expected_assessment_fingerprint"],
        "commitment_ref": f"synthetic://owner/{role}/assessment-commitment@1",
        "commitment_revision": 1,
    }
    return {
        "owner_commitment_ref": base["commitment_ref"],
        "expected_owner_commitment_revision": base["commitment_revision"],
        "expected_owner_commitment_fingerprint": digest(DOMAIN + ":owner-commitment", base),
    }


def upgrade_R2_consumer(role: str, value: dict[str, Any]) -> dict[str, Any]:
    first_three = {
        "assessment_id": value["assessment_id"],
        "expected_assessment_revision": value["expected_assessment_revision"],
        "expected_assessment_fingerprint": value["expected_assessment_fingerprint"],
    }
    if all(item is None for item in first_three.values()):
        return all_null_consumer()
    return {**first_three, **owner_commitment_tuple(role, first_three)}


def mixed_consumer(mask: int, base: dict[str, Any]) -> dict[str, Any]:
    return {
        field: None if mask & (1 << index) else base[field]
        for index, field in enumerate(CONSUMER_FIELDS)
    }


def locate_R2_H01(r2_fixture: dict[str, Any]) -> dict[str, Any]:
    rows = [row for row in r2_fixture["handoff_cases"] if row.get("case_id") == "H01"]
    if len(rows) != 1:
        raise ValueError("R2 fixture must contain exactly one H01")
    row = rows[0]
    if row.get("row_fingerprint") != R2_H01_ROW_FINGERPRINT:
        raise ValueError("R2 H01 fingerprint mismatch")
    if row.get("claimed_decision", {}).get("result") != "CANDIDATE_FORMED":
        raise ValueError("R2 H01 must be CANDIDATE_FORMED")
    return row


def build_fixture(r2_fixture: dict[str, Any]) -> dict[str, Any]:
    h01 = locate_R2_H01(r2_fixture)
    source_consumers = h01["raw_input"]["assessment_consumers"]
    upgraded = {
        role: upgrade_R2_consumer(role, value)
        for role, value in sorted(source_consumers.items())
    }
    non_null = upgraded["f7_intent_currentness"]
    null_consumer = all_null_consumer()

    schema_inventory = [
        signed(DOMAIN + ":schema", {
            "schema_id": "AssessmentConsumerV0_1R4",
            "fields": CONSUMER_FIELDS,
            "closed": True,
            "legal_shapes": ["ALL_NULL", "ALL_NON_NULL"],
        }, "schema_fingerprint"),
        signed(DOMAIN + ":schema", {
            "schema_id": "ConsumerResolutionV0_1R4",
            "fields": [
                "assessment", "resolution", "owner_store_lookup_performed",
                "assessment_result_interpreted", "authority_created",
            ],
            "closed": True,
        }, "schema_fingerprint"),
        signed(DOMAIN + ":schema", {
            "schema_id": "InheritedR2H01CompatibilityV0_1R4",
            "fields": [
                "source_case_id", "source_row_fingerprint", "source_result",
                "source_consumer_inventory_fingerprint", "upgraded_consumers",
                "downprojected_consumer_inventory_fingerprint", "claimed_result",
            ],
            "closed": True,
        }, "schema_fingerprint"),
    ]

    positive_shapes = [
        signed(DOMAIN + ":consumer-shape", {
            "case_id": "CS-ALL-NULL",
            "consumer": null_consumer,
            "expected_shape": "ALL_NULL",
            "expected_valid": True,
        }),
        signed(DOMAIN + ":consumer-shape", {
            "case_id": "CS-ALL-NON-NULL",
            "consumer": non_null,
            "expected_shape": "ALL_NON_NULL",
            "expected_valid": True,
        }),
    ]

    mixed_null_cases = [
        signed(DOMAIN + ":mixed-null", {
            "case_id": f"MN-{mask:02d}",
            "null_mask": mask,
            "consumer": mixed_consumer(mask, non_null),
            "expected_shape": "MIXED_NULL_INVALID",
            "expected_valid": False,
        })
        for mask in range(1, 63)
    ]

    formation_case = signed(DOMAIN + ":formation", {
        "case_id": "FORMATION-ALL-NULL",
        "assessment_consumer": null_consumer,
        "minimum_trusted_event_sequence": 100,
        "claimed_decision": {
            "result": "INDETERMINATE",
            "primary_reason": "ASSESSMENT_CONSUMER_UNAVAILABLE",
            "reason_codes": ["ASSESSMENT_CONSUMER_UNAVAILABLE"],
            "runtime_usable": False,
            "command_authority": False,
            "task_write_authority": False,
            "effect_authority": False,
        },
    })

    candidate = signed(DOMAIN + ":candidate", {
        "candidate_ref": "synthetic://f8/r4/candidate/001@1",
        "candidate_revision": 1,
        "runtime_usable": False,
        "command_authority": False,
    }, "candidate_fingerprint")
    acknowledgement_case = signed(DOMAIN + ":acknowledgement", {
        "case_id": "ACK-ALL-NULL",
        "raw_input": {
            "handoff_candidate_ref": candidate["candidate_ref"],
            "handoff_candidate_revision": candidate["candidate_revision"],
            "handoff_candidate_fingerprint": candidate["candidate_fingerprint"],
            "F3_outcome_consumer": null_consumer,
            "minimum_trusted_event_sequence": 100,
        },
        "claimed_decision": {
            "result": "ACKNOWLEDGED_INDETERMINATE",
            "primary_reason": "ASSESSMENT_CONSUMER_UNAVAILABLE",
            "reason_codes": ["ASSESSMENT_CONSUMER_UNAVAILABLE"],
            "runtime_usable": False,
            "command_authority": False,
            "task_write_authority": False,
            "effect_authority": False,
        },
    })

    source_inventory_fp = digest(DOMAIN + ":R2-H01-source-consumers", source_consumers)
    downprojected = {
        role: {key: consumer[key] for key in CONSUMER_FIELDS[:3]}
        for role, consumer in upgraded.items()
    }
    compatibility_case = signed(DOMAIN + ":R2-H01-compatibility", {
        "source_case_id": "H01",
        "source_row_fingerprint": h01["row_fingerprint"],
        "source_result": h01["claimed_decision"]["result"],
        "source_consumer_inventory_fingerprint": source_inventory_fp,
        "upgraded_consumers": upgraded,
        "downprojected_consumer_inventory_fingerprint": digest(
            DOMAIN + ":R2-H01-source-consumers", downprojected
        ),
        "claimed_result": "CANDIDATE_FORMED",
    })

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
        "schema_version": "agents-os.f8-r4-consumer-nullability-totality-witness.v0.1",
        "contract_id": "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R4",
        "environment": "SYNTHETIC_TEST",
        "runtime_usable": False,
        "domain_tag": DOMAIN,
        "schema_inventory": schema_inventory,
        "consumer_shape_positive_cases": positive_shapes,
        "mixed_null_negative_cases": mixed_null_cases,
        "formation_all_null_cases": [formation_case],
        "canonical_candidate_history": [candidate],
        "acknowledgement_all_null_cases": [acknowledgement_case],
        "inherited_R2_H01_compatibility_cases": [compatibility_case],
        "boundary_assertions": boundary,
    }
    section_names = [
        "schema_inventory", "consumer_shape_positive_cases", "mixed_null_negative_cases",
        "formation_all_null_cases", "canonical_candidate_history",
        "acknowledgement_all_null_cases", "inherited_R2_H01_compatibility_cases",
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
    r2_fixture = json.loads(Path(args.r2_fixture).read_text(encoding="utf-8"))
    output = Path(args.output)
    output.write_text(
        json.dumps(build_fixture(r2_fixture), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

