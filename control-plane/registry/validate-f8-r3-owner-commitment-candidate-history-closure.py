#!/usr/bin/env python3
"""Validate the deterministic synthetic F8 R3 closure witness offline."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
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


SECTION_NAMES = [
    "schema_inventory", "owner_assessments",
    "owner_assessment_revision_commitments", "canonical_candidate_history",
    "candidate_formation_cases", "acknowledgement_cases", "boundary_assertions",
]

ROOT_FIELDS = {
    "schema_version", "contract_id", "domain_tag", "environment", "runtime_usable",
    *SECTION_NAMES, "section_fingerprints", "root_fingerprint",
}

ASSESSMENT_FIELDS = set(SCHEMA_FIELDS["OwnerAssessmentV0_1R3"])
COMMITMENT_FIELDS = set(SCHEMA_FIELDS["OwnerAssessmentRevisionCommitmentV0_1R3"])
CONSUMER_FIELDS = set(SCHEMA_FIELDS["AssessmentConsumerV0_1R3"])
CANDIDATE_FIELDS = set(SCHEMA_FIELDS["CanonicalCandidateHistoryEntryV0_1R3"])
FORMATION_CASE_FIELDS = set(SCHEMA_FIELDS["CandidateFormationCaseV0_1R3"])
ACK_CASE_FIELDS = set(SCHEMA_FIELDS["HomeIntentHandoffAcknowledgementCaseV0_1R3"])
BOUNDARY_FIELDS = set(SCHEMA_FIELDS["BoundaryAssertionsV0_1R3"])
SCHEMA_ROW_FIELDS = {"schema_name", "field_names", "closed", "row_fingerprint"}
FORMATION_DECISION_FIELDS = {
    "result", "primary_reason", "command_authority", "task_write_authority",
    "effect_authority", "runtime_usable",
}
ACK_RAW_FIELDS = {
    "handoff_candidate_ref", "handoff_candidate_revision",
    "handoff_candidate_fingerprint", "minimum_trusted_event_sequence",
    "F3_outcome_consumer",
}
ACK_DECISION_FIELDS = set(FORMATION_DECISION_FIELDS)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OWNER_PROFILES = {
    "F7_INTENT_CURRENTNESS": ("F7", {"CURRENT_ACCEPTED", "STALE", "INDETERMINATE"}),
    "F3_INTAKE_OUTCOME": (
        "F3", {"NOT_SUBMITTED", "SYNTHETIC_TEST_COMMITTED", "REJECTED", "INDETERMINATE"}
    ),
}

# These values represent owner-store facts outside the caller-controlled
# fixture graph. They are synthetic test anchors, never runtime authority.
TRUSTED_OWNER_COMMITMENT_ANCHORS = {
    "synthetic://f3/assessment-commitment/a-f3-behind@1": (
        1, "ec7e6753d5345c57720212c211fbf3f280214a7653f49b89cabbf12e4b6218a4",
        "A-F3-BEHIND", 1, "7bcd99ee82b11c448828b9b44b5150944bfca39ab4e14c09590755e28733fe89",
        "synthetic://f3/event/assessment-a-f3-behind-r1",
        "4dc618244382924393a3d2b4e880b420b484dab7fd51d5f8467c7d1c09a08e91",
    ),
    "synthetic://f3/assessment-commitment/a-f3-equal@1": (
        1, "149c917a83039acb745df16788e62665b83e025b83b9aad10d9227fc35c3189c",
        "A-F3-EQUAL", 1, "2864ed3846104c655c7f333de0e336a8d4c2a8d4af34cd1ae862861a35888164",
        "synthetic://f3/event/assessment-a-f3-equal-r1",
        "074cad6b9f70a8c7859c438af11118c5352458eb86930d3ef9293bad5ff18f2d",
    ),
    "synthetic://f3/assessment-commitment/a-f3-higher@1": (
        1, "5d7c6b251057db9d732ff5a1fe74781de3f11bdc10ae78e554e8d978cdd2fb95",
        "A-F3-HIGHER", 1, "269fb65aaaebb64de2786ae657550887712972b0248dc0bebf5f956c7c432a72",
        "synthetic://f3/event/assessment-a-f3-higher-r1",
        "5cc542dcc41e42c8715526c3de4ae8ebd549a66c8964b697874afa4393873361",
    ),
    "synthetic://f3/assessment-commitment/a-f3-indeterminate@1": (
        1, "984945907dab9be55d47414f3b722c5bea97a104f9b4d90ec8d41a671889180b",
        "A-F3-INDETERMINATE", 1,
        "3c7e3cfdc935e891e0406cda8c990d7968117d49dceff617e4e3a1acb6b6ced7",
        "synthetic://f3/event/assessment-a-f3-indeterminate-r1",
        "b868979671a5236da58db0d8981eaad3f29cb69b4a70095145ed9a27326a80d9",
    ),
    "synthetic://f3/assessment-commitment/a-f3-phantom@1": (
        1, "96519a633f1b0ac244358fb9146a3af2c20c6709163366ad36820d7d6547844d",
        "A-F3-PHANTOM", 1, "0356e1635fb1d9f5c912c510536253fddd950974d52013235bf46db686976481",
        "synthetic://f3/event/assessment-a-f3-phantom-r1",
        "a5653b8c7565e141b26d768450f9844637043a14aa06f0edf16a73087acf147c",
    ),
    "synthetic://f7/assessment-commitment/a-f7-current@1": (
        1, "3b49d8b1897d82d20998c89c98f6e189b38d9facefe94e292808b994b5d2143b",
        "A-F7-CURRENT", 1, "cb762ebbe4ef684c6a2274da0fe4e33db9c30835a9f17cdf32e554a1b996bb4c",
        "synthetic://f7/event/assessment-a-f7-current-r1",
        "8ee2a71bc0dfd494be633ec62ab5aa5f6069635432ced08e944b6e2c6b31baa1",
    ),
    "synthetic://f7/assessment-commitment/a-f7-stale@1": (
        1, "de7b257456b2b0c0c82ddfc54ed06c8d3113f7254b86f6f1ef0fa7190bf36e89",
        "A-F7-STALE", 1, "6df4cc712d0113d2eb7567842c60d958c6fa2439b1b329cb7baefb548ba48f21",
        "synthetic://f7/event/assessment-a-f7-stale-r1",
        "93116a528b187216604cf6ca673e6563d84a032c11665f07e225774d0be1fa0c",
    ),
}

TRUSTED_CANDIDATE_HISTORY_ANCHORS = {
    ("synthetic://f8/handoff-candidate/001@1", 1):
        "e86dae2e491389db4687a298766c5f8993ea206e760c3a28a6661a8709f27381",
    ("synthetic://f8/handoff-candidate/001@2", 2):
        "58e993c20fbf5afb49cb76eadbbf4aabeaf03d55dedc12d58cc48eb929a93540",
}

SECTION_ANCHORS = {
    "acknowledgement_cases": "10859f466dc5b9dc8994379bbf117a1b9c7611579b695f0d71847255cced4046",
    "boundary_assertions": "ac935a85232cc165a59dfac63f02de5970bd4f941b9a61194d34aa380ac5b4b0",
    "candidate_formation_cases": "726e554e3ba646dd9a0370b1f0889ce634bdbe815e8c3f70fea3368505c18167",
    "canonical_candidate_history": "106326ddb869953266a680dc6d997f1511c0170e37cec5aa1ffd83e207fde6c9",
    "owner_assessment_revision_commitments": "5cb83e7ffbd1471cd08d42be21566ae6325bd0fd7e1b957b2bc924e7c6f048b2",
    "owner_assessments": "0d2a397ab4cdeb3142925447c64de188e8814429d607ffed739cd3fcfb4acd8c",
    "schema_inventory": "3b44991104e94a823b65e57f54a9d7f61d8220a42ef2ad7ec478f844aa67d55a",
}


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"invalid constant {value}")),
    )


def valid_hash(value: Any) -> bool:
    return type(value) is str and SHA256_RE.fullmatch(value) is not None


def stable_ref(value: Any) -> bool:
    return type(value) is str and bool(value) and unicodedata.normalize("NFC", value) == value


def positive_int(value: Any) -> bool:
    return type(value) is int and 1 <= value <= MAX_SAFE_INTEGER


def exact_fields(value: Any, fields: set[str], path: str, errors: list[str]) -> bool:
    if type(value) is not dict:
        errors.append(f"{path}: object required")
        return False
    if set(value) != fields:
        errors.append(f"{path}: exact field inventory mismatch")
        return False
    return True


def validate_json_value(value: Any, path: str, errors: list[str]) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            errors.append(f"{path}: integer outside safe range")
        return
    if type(value) is float:
        errors.append(f"{path}: floats forbidden")
        return
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value:
            errors.append(f"{path}: non-NFC string")
        return
    if type(value) is list:
        for index, item in enumerate(value):
            validate_json_value(item, f"{path}[{index}]", errors)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                errors.append(f"{path}: non-string key")
            validate_json_value(item, f"{path}.{key}", errors)
        return
    errors.append(f"{path}: unsupported JSON value")


def validate_consumer(value: Any, path: str, errors: list[str]) -> bool:
    if not exact_fields(value, CONSUMER_FIELDS, path, errors):
        return False
    for key in ["assessment_id", "owner_commitment_ref"]:
        if not stable_ref(value[key]): errors.append(f"{path}.{key}: stable_ref required")
    for key in ["expected_assessment_revision", "expected_owner_commitment_revision"]:
        if not positive_int(value[key]): errors.append(f"{path}.{key}: positive integer required")
    for key in ["expected_assessment_fingerprint", "expected_owner_commitment_fingerprint"]:
        if not valid_hash(value[key]): errors.append(f"{path}.{key}: lowercase SHA-256 required")
    return True


def validate_decision(value: Any, path: str, errors: list[str], *, acknowledgement: bool) -> bool:
    fields = ACK_DECISION_FIELDS if acknowledgement else FORMATION_DECISION_FIELDS
    if not exact_fields(value, fields, path, errors):
        return False
    allowed_results = (
        {"NOT_SUBMITTED", "ACKNOWLEDGED_COMMITTED", "ACKNOWLEDGED_REJECTED", "ACKNOWLEDGED_INDETERMINATE"}
        if acknowledgement else {"CANDIDATE_FORMED", "REJECTED", "INDETERMINATE"}
    )
    if type(value["result"]) is not str or value["result"] not in allowed_results:
        errors.append(f"{path}.result: closed result required")
    if type(value["primary_reason"]) is not str or not value["primary_reason"]:
        errors.append(f"{path}.primary_reason: closed reason string required")
    for key in ["command_authority", "task_write_authority", "effect_authority", "runtime_usable"]:
        if value[key] is not False: errors.append(f"{path}.{key}: must be false")
    return True


def validate_fixture(fixture: Any, *, enforce_inventory_anchors: bool = True) -> list[str]:
    errors: list[str] = []
    validate_json_value(fixture, "$", errors)
    if not exact_fields(fixture, ROOT_FIELDS, "$", errors):
        return errors
    if fixture["schema_version"] != "agents-os.f8-r3-owner-commitment-candidate-history-witness.v0.1": errors.append("schema_version mismatch")
    if fixture["contract_id"] != "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R3_ATOMIC_BUNDLE": errors.append("contract_id mismatch")
    if fixture["domain_tag"] != DOMAIN or fixture["environment"] != "SYNTHETIC_TEST": errors.append("domain/environment mismatch")
    if fixture["runtime_usable"] is not False: errors.append("runtime_usable must be false")

    schemas = fixture["schema_inventory"]
    if type(schemas) is not list or len(schemas) != len(SCHEMA_FIELDS):
        errors.append("schema_inventory: exact schema count mismatch")
        schemas = []
    for index, row in enumerate(schemas):
        path = f"schema_inventory[{index}]"
        if not exact_fields(row, SCHEMA_ROW_FIELDS, path, errors): continue
        expected_name = list(SCHEMA_FIELDS)[index] if index < len(SCHEMA_FIELDS) else None
        if row["schema_name"] != expected_name or row["field_names"] != SCHEMA_FIELDS.get(expected_name, []): errors.append(f"{path}: canonical schema inventory mismatch")
        if row["closed"] is not True: errors.append(f"{path}: closed must be true")
        if row["row_fingerprint"] != digest(DOMAIN + ":schema-profile", without(row, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")

    assessments = fixture["owner_assessments"]
    if type(assessments) is not list or len(assessments) != 7:
        errors.append("owner_assessments: expected seven rows")
        assessments = []
    assessment_ids: set[str] = set()
    for index, row in enumerate(assessments):
        path = f"owner_assessments[{index}]"
        if not exact_fields(row, ASSESSMENT_FIELDS, path, errors): continue
        if not stable_ref(row["assessment_id"]) or row["assessment_id"] in assessment_ids: errors.append(f"{path}: invalid or duplicate assessment_id")
        else: assessment_ids.add(row["assessment_id"])
        for key in ["subject_ref"]:
            if not stable_ref(row[key]): errors.append(f"{path}.{key}: stable_ref required")
        for key in ["assessment_revision", "subject_revision", "based_on_event_sequence"]:
            if not positive_int(row[key]): errors.append(f"{path}.{key}: positive integer required")
        for key in ["subject_fingerprint", "row_fingerprint"]:
            if not valid_hash(row[key]): errors.append(f"{path}.{key}: lowercase SHA-256 required")
        if row["context_fingerprint"] is not None and not valid_hash(row["context_fingerprint"]): errors.append(f"{path}.context_fingerprint: SHA-256 or null required")
        if type(row["is_current_head"]) is not bool: errors.append(f"{path}.is_current_head: strict boolean required")
        profile = OWNER_PROFILES.get(row["assessment_kind"])
        if profile is None or row["owner_contract"] != profile[0] or row["result"] not in profile[1]: errors.append(f"{path}: owner/kind/result mismatch")
        if row["assessment_kind"] == "F3_INTAKE_OUTCOME" and not valid_hash(row["context_fingerprint"]): errors.append(f"{path}: F3 outcome context required")
        if row["assessment_kind"] == "F7_INTENT_CURRENTNESS" and row["context_fingerprint"] is not None: errors.append(f"{path}: F7 context must be null")
        if row["row_fingerprint"] != digest(DOMAIN + ":assessment", without(row, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")

    commitments = fixture["owner_assessment_revision_commitments"]
    if type(commitments) is not list or len(commitments) != 7:
        errors.append("owner commitments: expected seven rows")
        commitments = []
    commitment_refs: set[str] = set()
    for index, row in enumerate(commitments):
        path = f"owner_assessment_revision_commitments[{index}]"
        if not exact_fields(row, COMMITMENT_FIELDS, path, errors): continue
        for key in ["commitment_ref", "assessment_id", "issued_event_ref"]:
            if not stable_ref(row[key]): errors.append(f"{path}.{key}: stable_ref required")
        if row["commitment_ref"] in commitment_refs: errors.append(f"{path}: duplicate commitment_ref")
        else: commitment_refs.add(row["commitment_ref"])
        for key in ["commitment_revision", "assessment_revision", "issued_event_sequence"]:
            if not positive_int(row[key]): errors.append(f"{path}.{key}: positive integer required")
        for key in ["assessment_fingerprint", "issued_event_fingerprint", "commitment_fingerprint"]:
            if not valid_hash(row[key]): errors.append(f"{path}.{key}: lowercase SHA-256 required")
        if row["commitment_revision"] == 1:
            if row["predecessor_commitment_ref"] is not None or row["predecessor_commitment_fingerprint"] is not None: errors.append(f"{path}: revision one predecessor must be null")
        if row["predecessor_commitment_ref"] is not None and not stable_ref(row["predecessor_commitment_ref"]): errors.append(f"{path}: invalid predecessor ref")
        if row["predecessor_commitment_fingerprint"] is not None and not valid_hash(row["predecessor_commitment_fingerprint"]): errors.append(f"{path}: invalid predecessor fingerprint")
        event_expected = digest(DOMAIN + ":owner-event", {
            "owner_contract": row["owner_contract"], "assessment_id": row["assessment_id"],
            "assessment_revision": row["assessment_revision"],
            "assessment_fingerprint": row["assessment_fingerprint"],
            "event_ref": row["issued_event_ref"], "event_sequence": row["issued_event_sequence"],
        })
        if row["issued_event_fingerprint"] != event_expected: errors.append(f"{path}: owner Event fingerprint mismatch")
        if row["commitment_fingerprint"] != digest(DOMAIN + ":owner-commitment", without(row, "commitment_fingerprint")): errors.append(f"{path}: commitment fingerprint mismatch")
        anchor = TRUSTED_OWNER_COMMITMENT_ANCHORS.get(row["commitment_ref"])
        actual_anchor = (
            row["commitment_revision"], row["commitment_fingerprint"], row["assessment_id"],
            row["assessment_revision"], row["assessment_fingerprint"], row["issued_event_ref"],
            row["issued_event_fingerprint"],
        )
        if anchor is None or actual_anchor != anchor: errors.append(f"{path}: OWNER_COMMITMENT_NOT_TRUSTED")
    if set(commitment_refs) != set(TRUSTED_OWNER_COMMITMENT_ANCHORS): errors.append("owner commitments: trusted source inventory mismatch")

    history = fixture["canonical_candidate_history"]
    if type(history) is not list or len(history) != 2:
        errors.append("canonical candidate history: expected two rows")
        history = []
    predecessor: dict[str, Any] | None = None
    actual_candidate_anchors: dict[tuple[str, int], str] = {}
    for index, row in enumerate(history):
        path = f"canonical_candidate_history[{index}]"
        if not exact_fields(row, CANDIDATE_FIELDS, path, errors): continue
        for key in ["candidate_id", "candidate_ref"]:
            if not stable_ref(row[key]): errors.append(f"{path}.{key}: stable_ref required")
        if not positive_int(row["candidate_revision"]): errors.append(f"{path}: positive revision required")
        if row["candidate_revision"] != index + 1: errors.append(f"{path}: revision sequence mismatch")
        if row["runtime_usable"] is not False or row["command_authority"] is not False: errors.append(f"{path}: authority/runtime must be false")
        if not valid_hash(row["candidate_fingerprint"]): errors.append(f"{path}: candidate fingerprint required")
        if predecessor is None:
            if row["predecessor_ref"] is not None or row["predecessor_fingerprint"] is not None: errors.append(f"{path}: first predecessor must be null")
        else:
            if row["candidate_id"] != predecessor["candidate_id"] or row["predecessor_ref"] != predecessor["candidate_ref"] or row["predecessor_fingerprint"] != predecessor["candidate_fingerprint"]: errors.append(f"{path}: predecessor mismatch")
        if row["candidate_fingerprint"] != digest(DOMAIN + ":candidate-history", without(row, "candidate_fingerprint")): errors.append(f"{path}: candidate fingerprint mismatch")
        actual_candidate_anchors[(row["candidate_ref"], row["candidate_revision"])] = row["candidate_fingerprint"]
        predecessor = row
    if actual_candidate_anchors != TRUSTED_CANDIDATE_HISTORY_ANCHORS: errors.append("canonical candidate history: trusted source mismatch")

    formation_cases = fixture["candidate_formation_cases"]
    if type(formation_cases) is not list or len(formation_cases) != 2:
        errors.append("candidate formation cases: expected two rows")
        formation_cases = []
    for index, case in enumerate(formation_cases):
        path = f"candidate_formation_cases[{index}]"
        if not exact_fields(case, FORMATION_CASE_FIELDS, path, errors): continue
        if not stable_ref(case["case_id"]) or not positive_int(case["minimum_trusted_event_sequence"]): errors.append(f"{path}: invalid id or minimum watermark")
        validate_consumer(case["assessment_consumer"], path + ".assessment_consumer", errors)
        validate_decision(case["claimed_decision"], path + ".claimed_decision", errors, acknowledgement=False)
        try:
            if case["claimed_decision"] != derive_formation(case, assessments, commitments): errors.append(f"{path}: formation decision not independently derived")
        except Exception as exc:
            errors.append(f"{path}: stable semantic BLOCK ({type(exc).__name__})")
        if case["row_fingerprint"] != digest(DOMAIN + ":formation-case", without(case, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")

    ack_cases = fixture["acknowledgement_cases"]
    if type(ack_cases) is not list or len(ack_cases) != 6:
        errors.append("acknowledgement cases: expected six rows")
        ack_cases = []
    for index, case in enumerate(ack_cases):
        path = f"acknowledgement_cases[{index}]"
        if not exact_fields(case, ACK_CASE_FIELDS, path, errors): continue
        raw = case["raw_input"]
        if not stable_ref(case["case_id"]): errors.append(f"{path}: stable case id required")
        if exact_fields(raw, ACK_RAW_FIELDS, path + ".raw_input", errors):
            if not stable_ref(raw["handoff_candidate_ref"]): errors.append(f"{path}: candidate ref required")
            if not positive_int(raw["handoff_candidate_revision"]) or not positive_int(raw["minimum_trusted_event_sequence"]): errors.append(f"{path}: positive revision/watermark required")
            if not valid_hash(raw["handoff_candidate_fingerprint"]): errors.append(f"{path}: candidate fingerprint required")
            validate_consumer(raw["F3_outcome_consumer"], path + ".raw_input.F3_outcome_consumer", errors)
        validate_decision(case["claimed_decision"], path + ".claimed_decision", errors, acknowledgement=True)
        try:
            if case["claimed_decision"] != derive_ack(raw, assessments, commitments, history): errors.append(f"{path}: acknowledgement not independently derived")
        except Exception as exc:
            errors.append(f"{path}: stable acknowledgement BLOCK ({type(exc).__name__})")
        if case["row_fingerprint"] != digest(DOMAIN + ":ack-case", without(case, "row_fingerprint")): errors.append(f"{path}: row fingerprint mismatch")

    boundary = fixture["boundary_assertions"]
    if exact_fields(boundary, BOUNDARY_FIELDS, "boundary_assertions", errors):
        for key in BOUNDARY_FIELDS - {"terminal_outcome"}:
            if type(boundary[key]) is not int or boundary[key] != 0: errors.append(f"boundary_assertions.{key}: must be integer zero")
        if boundary["terminal_outcome"] != "NOT_EXECUTED": errors.append("terminal_outcome must be NOT_EXECUTED")

    sections = fixture["section_fingerprints"]
    if type(sections) is not dict or set(sections) != set(SECTION_NAMES):
        errors.append("section_fingerprints: exact inventory mismatch")
    else:
        for name in SECTION_NAMES:
            expected = digest(DOMAIN + ":section:" + name, fixture[name])
            if sections[name] != expected: errors.append(f"section_fingerprints.{name}: mismatch")
            if enforce_inventory_anchors and sections[name] != SECTION_ANCHORS[name]: errors.append(f"section_fingerprints.{name}: fixed inventory anchor mismatch")
    if valid_hash(fixture["root_fingerprint"]):
        body = copy.deepcopy(fixture); body.pop("root_fingerprint")
        if fixture["root_fingerprint"] != digest(DOMAIN + ":root", body): errors.append("root_fingerprint mismatch")
    else:
        errors.append("root_fingerprint invalid")
    return errors


def resign_fixture(fixture: dict[str, Any], *, derive_decisions: bool = True) -> None:
    for row in fixture.get("schema_inventory", []):
        if type(row) is dict: row["row_fingerprint"] = digest(DOMAIN + ":schema-profile", without(row, "row_fingerprint"))
    for row in fixture.get("owner_assessments", []):
        if type(row) is dict: row["row_fingerprint"] = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
    for row in fixture.get("owner_assessment_revision_commitments", []):
        if type(row) is not dict: continue
        row["issued_event_fingerprint"] = digest(DOMAIN + ":owner-event", {
            "owner_contract": row["owner_contract"], "assessment_id": row["assessment_id"],
            "assessment_revision": row["assessment_revision"],
            "assessment_fingerprint": row["assessment_fingerprint"],
            "event_ref": row["issued_event_ref"], "event_sequence": row["issued_event_sequence"],
        })
        row["commitment_fingerprint"] = digest(DOMAIN + ":owner-commitment", without(row, "commitment_fingerprint"))
    history = fixture.get("canonical_candidate_history", [])
    for index, row in enumerate(history):
        if type(row) is not dict: continue
        if index:
            row["predecessor_ref"] = history[index-1].get("candidate_ref")
            row["predecessor_fingerprint"] = history[index-1].get("candidate_fingerprint")
        row["candidate_fingerprint"] = digest(DOMAIN + ":candidate-history", without(row, "candidate_fingerprint"))
    if derive_decisions:
        for case in fixture.get("candidate_formation_cases", []):
            if type(case) is dict:
                case["claimed_decision"] = derive_formation(case, fixture.get("owner_assessments", []), fixture.get("owner_assessment_revision_commitments", []))
        for case in fixture.get("acknowledgement_cases", []):
            if type(case) is dict and type(case.get("raw_input")) is dict:
                case["claimed_decision"] = derive_ack(case["raw_input"], fixture.get("owner_assessments", []), fixture.get("owner_assessment_revision_commitments", []), history)
    for case in fixture.get("candidate_formation_cases", []):
        if type(case) is dict: case["row_fingerprint"] = digest(DOMAIN + ":formation-case", without(case, "row_fingerprint"))
    for case in fixture.get("acknowledgement_cases", []):
        if type(case) is dict: case["row_fingerprint"] = digest(DOMAIN + ":ack-case", without(case, "row_fingerprint"))
    sections = fixture.get("section_fingerprints")
    if type(sections) is dict:
        for name in SECTION_NAMES:
            if name in fixture: sections[name] = digest(DOMAIN + ":section:" + name, fixture[name])
    if "root_fingerprint" in fixture:
        body = copy.deepcopy(fixture); body.pop("root_fingerprint")
        fixture["root_fingerprint"] = digest(DOMAIN + ":root", body)


def run_regressions(fixture: dict[str, Any]) -> tuple[int, int, list[str]]:
    tests: list[tuple[str, dict[str, Any], str]] = []

    def row_by_id(value: dict[str, Any], aid: str) -> dict[str, Any]:
        return next(row for row in value["owner_assessments"] if row["assessment_id"] == aid)

    def commitment_for(value: dict[str, Any], aid: str) -> dict[str, Any]:
        return next(row for row in value["owner_assessment_revision_commitments"] if row["assessment_id"] == aid)

    value = copy.deepcopy(fixture)
    row = row_by_id(value, "A-F7-STALE"); row["result"] = "CURRENT_ACCEPTED"; row["is_current_head"] = True
    row["row_fingerprint"] = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
    case = value["candidate_formation_cases"][1]
    case["assessment_consumer"]["expected_assessment_fingerprint"] = row["row_fingerprint"]
    case["claimed_decision"] = {"result": "CANDIDATE_FORMED", "primary_reason": "VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE", "command_authority": False, "task_write_authority": False, "effect_authority": False, "runtime_usable": False}
    resign_fixture(value, derive_decisions=False)
    tests.append(("same_revision_f7_row_rewrite", value, "formation decision not independently derived"))

    value = copy.deepcopy(fixture)
    row = row_by_id(value, "A-F7-STALE"); row["result"] = "CURRENT_ACCEPTED"; row["is_current_head"] = True
    row["row_fingerprint"] = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
    commit = commitment_for(value, "A-F7-STALE"); commit["assessment_fingerprint"] = row["row_fingerprint"]
    resign_fixture(value)
    case = value["candidate_formation_cases"][1]
    case["assessment_consumer"]["expected_assessment_fingerprint"] = row["row_fingerprint"]
    case["assessment_consumer"]["expected_owner_commitment_fingerprint"] = commit["commitment_fingerprint"]
    resign_fixture(value)
    tests.append(("same_revision_f7_row_and_commitment_rewrite", value, "OWNER_COMMITMENT_NOT_TRUSTED"))

    value = copy.deepcopy(fixture)
    row = row_by_id(value, "A-F3-INDETERMINATE"); row["result"] = "SYNTHETIC_TEST_COMMITTED"
    row["row_fingerprint"] = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
    case = value["acknowledgement_cases"][3]
    case["raw_input"]["F3_outcome_consumer"]["expected_assessment_fingerprint"] = row["row_fingerprint"]
    case["claimed_decision"] = {"result": "ACKNOWLEDGED_COMMITTED", "primary_reason": "F3_OWNER_REPORTED_SYNTHETIC_COMMITTED", "command_authority": False, "task_write_authority": False, "effect_authority": False, "runtime_usable": False}
    resign_fixture(value, derive_decisions=False)
    tests.append(("same_revision_f3_row_rewrite", value, "acknowledgement not independently derived"))

    value = copy.deepcopy(fixture)
    row = row_by_id(value, "A-F3-INDETERMINATE"); row["result"] = "SYNTHETIC_TEST_COMMITTED"
    row["row_fingerprint"] = digest(DOMAIN + ":assessment", without(row, "row_fingerprint"))
    commit = commitment_for(value, "A-F3-INDETERMINATE"); commit["assessment_fingerprint"] = row["row_fingerprint"]
    resign_fixture(value)
    case = value["acknowledgement_cases"][3]
    case["raw_input"]["F3_outcome_consumer"]["expected_assessment_fingerprint"] = row["row_fingerprint"]
    case["raw_input"]["F3_outcome_consumer"]["expected_owner_commitment_fingerprint"] = commit["commitment_fingerprint"]
    resign_fixture(value)
    tests.append(("same_revision_f3_row_and_commitment_rewrite", value, "OWNER_COMMITMENT_NOT_TRUSTED"))

    value = copy.deepcopy(fixture)
    case = value["acknowledgement_cases"][4]
    case["claimed_decision"] = {"result": "ACKNOWLEDGED_COMMITTED", "primary_reason": "F3_OWNER_REPORTED_SYNTHETIC_COMMITTED", "command_authority": False, "task_write_authority": False, "effect_authority": False, "runtime_usable": False}
    resign_fixture(value, derive_decisions=False)
    tests.append(("phantom_candidate_not_in_history", value, "acknowledgement not independently derived"))

    value = copy.deepcopy(fixture)
    phantom = {"candidate_id": "synthetic://f8/handoff-candidate/phantom", "candidate_ref": "synthetic://f8/handoff-candidate/phantom@9", "candidate_revision": 9, "predecessor_ref": value["canonical_candidate_history"][-1]["candidate_ref"], "predecessor_fingerprint": value["canonical_candidate_history"][-1]["candidate_fingerprint"], "runtime_usable": False, "command_authority": False}
    phantom = signed(DOMAIN + ":candidate-history", phantom, "candidate_fingerprint")
    value["canonical_candidate_history"].append(phantom)
    resign_fixture(value)
    tests.append(("phantom_candidate_added_to_history", value, "trusted source mismatch"))

    value = copy.deepcopy(fixture); value["acknowledgement_cases"][0]["raw_input"]["trusted_event_sequence"] = value["acknowledgement_cases"][0]["raw_input"].pop("minimum_trusted_event_sequence"); resign_fixture(value, derive_decisions=False)
    tests.append(("old_watermark_field", value, "exact field inventory mismatch"))
    value = copy.deepcopy(fixture); value["owner_assessment_revision_commitments"][0]["unknown"] = 0; resign_fixture(value)
    tests.append(("unknown_commitment_field", value, "exact field inventory mismatch"))
    value = copy.deepcopy(fixture); value["acknowledgement_cases"][0]["raw_input"]["minimum_trusted_event_sequence"] = True; resign_fixture(value, derive_decisions=False)
    tests.append(("boolean_as_watermark", value, "positive revision/watermark required"))
    value = copy.deepcopy(fixture); value["boundary_assertions"]["external_effect_count"] = 1; resign_fixture(value)
    tests.append(("real_effect_occurrence", value, "must be integer zero"))
    value = copy.deepcopy(fixture); value["owner_assessment_revision_commitments"][0]["commitment_ref"] = "synthetic://attacker/commitment/1"; resign_fixture(value)
    tests.append(("caller_commitment_substitution", value, "OWNER_COMMITMENT_NOT_TRUSTED"))
    value = copy.deepcopy(fixture); value["canonical_candidate_history"][1]["command_authority"] = True; resign_fixture(value)
    tests.append(("candidate_command_authority", value, "authority/runtime must be false"))

    passed = 0
    failures: list[str] = []
    for name, value, target in tests:
        try:
            errors = validate_fixture(value, enforce_inventory_anchors=False)
        except Exception as exc:
            failures.append(f"{name}: exception {type(exc).__name__}")
            continue
        if errors and any(target in error for error in errors):
            passed += 1
        else:
            failures.append(f"{name}: target={target!r} errors={errors[:5]!r}")
    return passed, len(tests), failures


def check_whitespace(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in paths:
        data = path.read_bytes()
        if b"\r" in data: errors.append(f"{path}: CR forbidden")
        if b"\t" in data: errors.append(f"{path}: tabs forbidden")
        if not data.endswith(b"\n") or data.endswith(b"\n\n"): errors.append(f"{path}: exactly one terminal LF required")
        for number, line in enumerate(data.splitlines(), 1):
            if line.endswith((b" ", b"\t")): errors.append(f"{path}:{number}: trailing whitespace")
    return errors


def parser_probes() -> tuple[int, int, list[str]]:
    probes = [
        '{"a":1,"a":2}',
        '{"a":NaN}',
        '{"a":Infinity}',
        '{"a":1.5}',
    ]
    passed = 0
    failures: list[str] = []
    for index, text in enumerate(probes, 1):
        try:
            value = json.loads(text, object_pairs_hook=reject_duplicate_pairs, parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)))
            errors: list[str] = []; validate_json_value(value, "$", errors)
            if errors: passed += 1
            else: failures.append(f"P{index}: accepted")
        except (ValueError, DuplicateKeyError):
            passed += 1
    return passed, len(probes), failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture", nargs="?",
        default="control-plane/registry/examples/2026-07-19-agents-os-f8-r3-owner-commitment-candidate-history-closure-v0.1.json",
    )
    parser.add_argument("--check-whitespace", nargs="+")
    args = parser.parse_args()
    if args.check_whitespace:
        errors = check_whitespace([Path(path) for path in args.check_whitespace])
        print(json.dumps({"result": "PASS" if not errors else "BLOCK", "files_checked": len(args.check_whitespace), "errors": errors}, sort_keys=True))
        return 0 if not errors else 1
    try:
        fixture = load_json_strict(Path(args.fixture))
        errors = validate_fixture(fixture)
        regression_passed, regression_total, regression_failures = run_regressions(fixture) if not errors else (0, 12, ["base fixture invalid"])
        parser_passed, parser_total, parser_failures = parser_probes()
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "stable_error": type(exc).__name__}, sort_keys=True))
        return 1
    all_errors = errors + regression_failures + parser_failures
    result = {
        "result": "PASS" if not all_errors and regression_passed == regression_total and parser_passed == parser_total else "BLOCK",
        "errors": all_errors,
        "schema_profiles_verified": len(fixture.get("schema_inventory", [])),
        "owner_assessments_verified": len(fixture.get("owner_assessments", [])),
        "owner_commitments_verified": len(fixture.get("owner_assessment_revision_commitments", [])),
        "canonical_candidate_history_verified": len(fixture.get("canonical_candidate_history", [])),
        "candidate_formation_cases_verified": len(fixture.get("candidate_formation_cases", [])),
        "acknowledgement_cases_verified": len(fixture.get("acknowledgement_cases", [])),
        "R3_regressions": f"{regression_passed}/{regression_total}_PASS",
        "parser_probes": f"{parser_passed}/{parser_total}_REJECTED",
        "real_command_count": fixture.get("boundary_assertions", {}).get("real_command_count"),
        "provider_call_count": fixture.get("boundary_assertions", {}).get("provider_call_count"),
        "external_effect_count": fixture.get("boundary_assertions", {}).get("external_effect_count"),
        "terminal_outcome": fixture.get("boundary_assertions", {}).get("terminal_outcome"),
        "root_fingerprint": fixture.get("root_fingerprint"),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
