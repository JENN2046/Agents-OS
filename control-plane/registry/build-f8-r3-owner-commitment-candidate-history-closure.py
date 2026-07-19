#!/usr/bin/env python3
"""Build the deterministic synthetic F8 R3 closure witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


DOMAIN = "agents-os.f8-r3.owner-commitment-candidate-history.v0.1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991

SCHEMA_FIELDS: dict[str, list[str]] = {
    "OwnerAssessmentV0_1R3": [
        "assessment_id", "assessment_revision", "owner_contract", "assessment_kind",
        "subject_ref", "subject_revision", "subject_fingerprint", "context_fingerprint",
        "result", "based_on_event_sequence", "is_current_head", "row_fingerprint",
    ],
    "OwnerAssessmentRevisionCommitmentV0_1R3": [
        "commitment_ref", "commitment_revision", "owner_contract", "assessment_id",
        "assessment_revision", "assessment_fingerprint", "predecessor_commitment_ref",
        "predecessor_commitment_fingerprint", "issued_event_ref", "issued_event_sequence",
        "issued_event_fingerprint", "commitment_fingerprint",
    ],
    "AssessmentConsumerV0_1R3": [
        "assessment_id", "expected_assessment_revision", "expected_assessment_fingerprint",
        "owner_commitment_ref", "expected_owner_commitment_revision",
        "expected_owner_commitment_fingerprint",
    ],
    "CanonicalCandidateHistoryEntryV0_1R3": [
        "candidate_id", "candidate_ref", "candidate_revision", "predecessor_ref",
        "predecessor_fingerprint", "runtime_usable", "command_authority",
        "candidate_fingerprint",
    ],
    "CandidateFormationCaseV0_1R3": [
        "case_id", "minimum_trusted_event_sequence", "assessment_consumer",
        "claimed_decision", "row_fingerprint",
    ],
    "HomeIntentHandoffAcknowledgementCaseV0_1R3": [
        "case_id", "raw_input", "claimed_decision", "row_fingerprint",
    ],
    "BoundaryAssertionsV0_1R3": [
        "real_command_count", "real_task_write_count", "runtime_activation_count",
        "database_write_count", "provider_call_count", "production_auth_count",
        "private_memory_read_count", "sensing_or_recording_count",
        "external_effect_count", "terminal_outcome",
    ],
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def without(row: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in row.items() if key != field}


def signed(tag: str, row: dict[str, Any], field: str = "row_fingerprint") -> dict[str, Any]:
    result = copy.deepcopy(row)
    result[field] = digest(tag, result)
    return result


def candidate_context(ref: str, revision: int, fingerprint: str) -> str:
    return digest(
        DOMAIN + ":f3-outcome-context",
        {
            "handoff_candidate_ref": ref,
            "handoff_candidate_revision": revision,
            "handoff_candidate_fingerprint": fingerprint,
        },
    )


def assessment(
    assessment_id: str,
    owner: str,
    kind: str,
    subject_ref: str,
    subject_revision: int,
    subject_fingerprint: str,
    result: str,
    *,
    context: str | None = None,
    current: bool = True,
    event_sequence: int = 100,
) -> dict[str, Any]:
    return signed(
        DOMAIN + ":assessment",
        {
            "assessment_id": assessment_id,
            "assessment_revision": 1,
            "owner_contract": owner,
            "assessment_kind": kind,
            "subject_ref": subject_ref,
            "subject_revision": subject_revision,
            "subject_fingerprint": subject_fingerprint,
            "context_fingerprint": context,
            "result": result,
            "based_on_event_sequence": event_sequence,
            "is_current_head": current,
        },
    )


def owner_commitment(row: dict[str, Any]) -> dict[str, Any]:
    owner_slug = row["owner_contract"].lower().replace("_", "-")
    event_ref = f"synthetic://{owner_slug}/event/assessment-{row['assessment_id'].lower()}-r1"
    event_fingerprint = digest(
        DOMAIN + ":owner-event",
        {
            "owner_contract": row["owner_contract"],
            "assessment_id": row["assessment_id"],
            "assessment_revision": row["assessment_revision"],
            "assessment_fingerprint": row["row_fingerprint"],
            "event_ref": event_ref,
            "event_sequence": row["based_on_event_sequence"],
        },
    )
    return signed(
        DOMAIN + ":owner-commitment",
        {
            "commitment_ref": (
                f"synthetic://{owner_slug}/assessment-commitment/"
                f"{row['assessment_id'].lower()}@1"
            ),
            "commitment_revision": 1,
            "owner_contract": row["owner_contract"],
            "assessment_id": row["assessment_id"],
            "assessment_revision": row["assessment_revision"],
            "assessment_fingerprint": row["row_fingerprint"],
            "predecessor_commitment_ref": None,
            "predecessor_commitment_fingerprint": None,
            "issued_event_ref": event_ref,
            "issued_event_sequence": row["based_on_event_sequence"],
            "issued_event_fingerprint": event_fingerprint,
        },
        "commitment_fingerprint",
    )


def commitment_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["commitment_ref"]: row for row in rows}


def assessment_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["assessment_id"]: row for row in rows}


def consumer(row: dict[str, Any], commitments: list[dict[str, Any]]) -> dict[str, Any]:
    commitment = next(
        item for item in commitments
        if item["assessment_id"] == row["assessment_id"]
        and item["assessment_revision"] == row["assessment_revision"]
    )
    return {
        "assessment_id": row["assessment_id"],
        "expected_assessment_revision": row["assessment_revision"],
        "expected_assessment_fingerprint": row["row_fingerprint"],
        "owner_commitment_ref": commitment["commitment_ref"],
        "expected_owner_commitment_revision": commitment["commitment_revision"],
        "expected_owner_commitment_fingerprint": commitment["commitment_fingerprint"],
    }


def make_candidate(revision: int, predecessor: dict[str, Any] | None) -> dict[str, Any]:
    row = {
        "candidate_id": "synthetic://f8/handoff-candidate/001",
        "candidate_ref": f"synthetic://f8/handoff-candidate/001@{revision}",
        "candidate_revision": revision,
        "predecessor_ref": predecessor["candidate_ref"] if predecessor else None,
        "predecessor_fingerprint": predecessor["candidate_fingerprint"] if predecessor else None,
        "runtime_usable": False,
        "command_authority": False,
    }
    return signed(DOMAIN + ":candidate-history", row, "candidate_fingerprint")


def resolve_consumer(
    binding: dict[str, Any],
    assessments: list[dict[str, Any]],
    commitments: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    arow = assessment_index(assessments).get(binding["assessment_id"])
    if arow is None:
        return None, "F3_OUTCOME_MISSING"
    if arow["assessment_revision"] != binding["expected_assessment_revision"]:
        return None, "F3_OUTCOME_REVISION_MISMATCH"
    if arow["row_fingerprint"] != binding["expected_assessment_fingerprint"]:
        return None, "F3_OUTCOME_FINGERPRINT_MISMATCH"
    crow = commitment_index(commitments).get(binding["owner_commitment_ref"])
    if crow is None:
        return None, "OWNER_COMMITMENT_MISSING"
    if crow["commitment_revision"] != binding["expected_owner_commitment_revision"]:
        return None, "OWNER_COMMITMENT_REVISION_MISMATCH"
    if crow["commitment_fingerprint"] != binding["expected_owner_commitment_fingerprint"]:
        return None, "OWNER_COMMITMENT_FINGERPRINT_MISMATCH"
    if (
        crow["owner_contract"] != arow["owner_contract"]
        or crow["assessment_id"] != arow["assessment_id"]
        or crow["assessment_revision"] != arow["assessment_revision"]
        or crow["assessment_fingerprint"] != arow["row_fingerprint"]
    ):
        return None, "OWNER_COMMITMENT_ASSESSMENT_MISMATCH"
    return arow, None


def derive_formation(
    case: dict[str, Any],
    assessments: list[dict[str, Any]],
    commitments: list[dict[str, Any]],
) -> dict[str, Any]:
    row, error = resolve_consumer(case["assessment_consumer"], assessments, commitments)
    if error:
        result, reason = "INDETERMINATE", error
    elif row["owner_contract"] != "F7" or row["assessment_kind"] != "F7_INTENT_CURRENTNESS":
        result, reason = "REJECTED", "OWNER_COMMITMENT_ASSESSMENT_MISMATCH"
    elif row["based_on_event_sequence"] < case["minimum_trusted_event_sequence"]:
        result, reason = "INDETERMINATE", "F3_OUTCOME_WATERMARK_BEHIND"
    elif not row["is_current_head"] or row["result"] != "CURRENT_ACCEPTED":
        result, reason = "REJECTED", "F7_INTENT_NOT_CURRENT"
    else:
        result, reason = "CANDIDATE_FORMED", "VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE"
    return {
        "result": result,
        "primary_reason": reason,
        "command_authority": False,
        "task_write_authority": False,
        "effect_authority": False,
        "runtime_usable": False,
    }


def history_lookup(
    raw: dict[str, Any], history: list[dict[str, Any]]
) -> tuple[dict[str, Any] | None, str | None]:
    matches = [
        row for row in history
        if row["candidate_ref"] == raw["handoff_candidate_ref"]
        and row["candidate_revision"] == raw["handoff_candidate_revision"]
    ]
    if not matches:
        return None, "CANDIDATE_HISTORY_MISSING"
    if len(matches) != 1:
        return None, "CANDIDATE_HISTORY_CONFLICT"
    if matches[0]["candidate_fingerprint"] != raw["handoff_candidate_fingerprint"]:
        return None, "CANDIDATE_HISTORY_FINGERPRINT_MISMATCH"
    return matches[0], None


def derive_ack(
    raw: dict[str, Any],
    assessments: list[dict[str, Any]],
    commitments: list[dict[str, Any]],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate, error = history_lookup(raw, history)
    if error:
        result, reason = "ACKNOWLEDGED_INDETERMINATE", error
    else:
        row, error = resolve_consumer(raw["F3_outcome_consumer"], assessments, commitments)
        if error:
            result, reason = "ACKNOWLEDGED_INDETERMINATE", error
        else:
            expected_context = candidate_context(
                candidate["candidate_ref"],
                candidate["candidate_revision"],
                candidate["candidate_fingerprint"],
            )
            if (
                row["owner_contract"] != "F3"
                or row["assessment_kind"] != "F3_INTAKE_OUTCOME"
                or row["subject_ref"] != candidate["candidate_ref"]
                or row["subject_revision"] != candidate["candidate_revision"]
                or row["subject_fingerprint"] != candidate["candidate_fingerprint"]
                or row["context_fingerprint"] != expected_context
            ):
                result, reason = "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_SUBJECT_MISMATCH"
            elif row["based_on_event_sequence"] < raw["minimum_trusted_event_sequence"]:
                result, reason = "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_WATERMARK_BEHIND"
            elif not row["is_current_head"]:
                result, reason = "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_NOT_CURRENT"
            elif row["result"] == "SYNTHETIC_TEST_COMMITTED":
                result, reason = "ACKNOWLEDGED_COMMITTED", "F3_OWNER_REPORTED_SYNTHETIC_COMMITTED"
            elif row["result"] == "REJECTED":
                result, reason = "ACKNOWLEDGED_REJECTED", "F3_OWNER_REPORTED_REJECTED"
            elif row["result"] == "NOT_SUBMITTED":
                result, reason = "NOT_SUBMITTED", "F3_OWNER_REPORTED_NOT_SUBMITTED"
            else:
                result, reason = "ACKNOWLEDGED_INDETERMINATE", "F3_OWNER_REPORTED_INDETERMINATE"
    return {
        "result": result,
        "primary_reason": reason,
        "command_authority": False,
        "task_write_authority": False,
        "effect_authority": False,
        "runtime_usable": False,
    }


def make_formation_case(
    case_id: str,
    row: dict[str, Any],
    commitments: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    minimum: int = 100,
) -> dict[str, Any]:
    body = {
        "case_id": case_id,
        "minimum_trusted_event_sequence": minimum,
        "assessment_consumer": consumer(row, commitments),
    }
    body["claimed_decision"] = derive_formation(body, assessments, commitments)
    return signed(DOMAIN + ":formation-case", body)


def make_ack_case(
    case_id: str,
    candidate_ref: str,
    candidate_revision: int,
    candidate_fingerprint: str,
    row: dict[str, Any],
    commitments: list[dict[str, Any]],
    assessments: list[dict[str, Any]],
    history: list[dict[str, Any]],
    minimum: int = 100,
) -> dict[str, Any]:
    raw = {
        "handoff_candidate_ref": candidate_ref,
        "handoff_candidate_revision": candidate_revision,
        "handoff_candidate_fingerprint": candidate_fingerprint,
        "minimum_trusted_event_sequence": minimum,
        "F3_outcome_consumer": consumer(row, commitments),
    }
    return signed(
        DOMAIN + ":ack-case",
        {
            "case_id": case_id,
            "raw_input": raw,
            "claimed_decision": derive_ack(raw, assessments, commitments, history),
        },
    )


def build_fixture() -> dict[str, Any]:
    candidate_1 = make_candidate(1, None)
    candidate_2 = make_candidate(2, candidate_1)
    history = [candidate_1, candidate_2]

    intent_ref = "synthetic://f7/intent-candidate/001"
    intent_fp = digest(DOMAIN + ":intent", {"ref": intent_ref, "revision": 2})
    context = candidate_context(
        candidate_2["candidate_ref"], candidate_2["candidate_revision"],
        candidate_2["candidate_fingerprint"],
    )
    phantom_ref = "synthetic://f8/handoff-candidate/phantom@9"
    phantom_fp = digest(DOMAIN + ":phantom-candidate", {"ref": phantom_ref, "revision": 9})
    phantom_context = candidate_context(phantom_ref, 9, phantom_fp)

    assessments = [
        assessment("A-F7-CURRENT", "F7", "F7_INTENT_CURRENTNESS", intent_ref, 2, intent_fp, "CURRENT_ACCEPTED"),
        assessment("A-F7-STALE", "F7", "F7_INTENT_CURRENTNESS", intent_ref, 2, intent_fp, "STALE", current=False),
        assessment("A-F3-EQUAL", "F3", "F3_INTAKE_OUTCOME", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], "SYNTHETIC_TEST_COMMITTED", context=context, event_sequence=100),
        assessment("A-F3-HIGHER", "F3", "F3_INTAKE_OUTCOME", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], "SYNTHETIC_TEST_COMMITTED", context=context, event_sequence=301),
        assessment("A-F3-BEHIND", "F3", "F3_INTAKE_OUTCOME", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], "SYNTHETIC_TEST_COMMITTED", context=context, event_sequence=99),
        assessment("A-F3-INDETERMINATE", "F3", "F3_INTAKE_OUTCOME", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], "INDETERMINATE", context=context, event_sequence=100),
        assessment("A-F3-PHANTOM", "F3", "F3_INTAKE_OUTCOME", phantom_ref, 9, phantom_fp, "SYNTHETIC_TEST_COMMITTED", context=phantom_context, event_sequence=100),
    ]
    commitments = [owner_commitment(row) for row in assessments]
    by_id = assessment_index(assessments)

    formation_cases = [
        make_formation_case("CF01", by_id["A-F7-CURRENT"], commitments, assessments),
        make_formation_case("CF02", by_id["A-F7-STALE"], commitments, assessments),
    ]
    ack_cases = [
        make_ack_case("ACK01", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], by_id["A-F3-EQUAL"], commitments, assessments, history, 100),
        make_ack_case("ACK02", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], by_id["A-F3-HIGHER"], commitments, assessments, history, 100),
        make_ack_case("ACK03", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], by_id["A-F3-BEHIND"], commitments, assessments, history, 100),
        make_ack_case("ACK04", candidate_2["candidate_ref"], 2, candidate_2["candidate_fingerprint"], by_id["A-F3-INDETERMINATE"], commitments, assessments, history, 100),
        make_ack_case("ACK05", phantom_ref, 9, phantom_fp, by_id["A-F3-PHANTOM"], commitments, assessments, history, 100),
        make_ack_case("ACK06", candidate_2["candidate_ref"], 2, "0" * 64, by_id["A-F3-EQUAL"], commitments, assessments, history, 100),
    ]

    schemas = [
        signed(
            DOMAIN + ":schema-profile",
            {
                "schema_name": name,
                "field_names": fields,
                "closed": True,
            },
        )
        for name, fields in SCHEMA_FIELDS.items()
    ]
    boundary = {
        "real_command_count": 0,
        "real_task_write_count": 0,
        "runtime_activation_count": 0,
        "database_write_count": 0,
        "provider_call_count": 0,
        "production_auth_count": 0,
        "private_memory_read_count": 0,
        "sensing_or_recording_count": 0,
        "external_effect_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }
    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f8-r3-owner-commitment-candidate-history-witness.v0.1",
        "contract_id": "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R3_ATOMIC_BUNDLE",
        "domain_tag": DOMAIN,
        "environment": "SYNTHETIC_TEST",
        "runtime_usable": False,
        "schema_inventory": schemas,
        "owner_assessments": assessments,
        "owner_assessment_revision_commitments": commitments,
        "canonical_candidate_history": history,
        "candidate_formation_cases": formation_cases,
        "acknowledgement_cases": ack_cases,
        "boundary_assertions": boundary,
    }
    section_names = [
        "schema_inventory", "owner_assessments",
        "owner_assessment_revision_commitments", "canonical_candidate_history",
        "candidate_formation_cases", "acknowledgement_cases", "boundary_assertions",
    ]
    fixture["section_fingerprints"] = {
        name: digest(DOMAIN + ":section:" + name, fixture[name]) for name in section_names
    }
    fixture["root_fingerprint"] = digest(DOMAIN + ":root", fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="control-plane/registry/examples/2026-07-19-agents-os-f8-r3-owner-commitment-candidate-history-closure-v0.1.json",
    )
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(json.dumps(build_fixture(), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
