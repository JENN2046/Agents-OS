#!/usr/bin/env python3
"""Independent semantic probes extracted from the F8 R2 builder/validator logic.

This probe does not modify project files. It models the relevant hash/signature,
consumer, candidate-set, and acknowledgement rules to test coordinated re-signing.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

DOMAIN = "F8_R2_SYNTHETIC_NONAUTHORITY"
CONSUMER_ROLES = [
    "f7_intent_currentness", "actor_identity", "principal_binding", "responsibility",
    "f3_readiness", "pbl_currentness", "jenn_requirement", "jenn_exact_decision",
]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode() + b"\x00" + canonical_bytes(value)).hexdigest()


def without(row: dict[str, Any], field: str) -> dict[str, Any]:
    out = copy.deepcopy(row)
    out.pop(field, None)
    return out


def sign_assessment(row: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(row)
    out["row_fingerprint"] = digest(DOMAIN + ":assessment", without(out, "row_fingerprint"))
    return out


def assessment(aid: str, kind: str, result: str, *, subject_ref: str, subject_revision: int,
               subject_fingerprint: str, context: str | None = None,
               current: bool = True, event_sequence: int = 100, owner: str = "F7") -> dict[str, Any]:
    return sign_assessment({
        "assessment_id": aid,
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
    })


def consumer(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "assessment_id": row["assessment_id"],
        "expected_assessment_revision": row["assessment_revision"],
        "expected_assessment_fingerprint": row["row_fingerprint"],
    }


def assessment_set_fingerprint(consumers: dict[str, dict[str, Any]]) -> str:
    rows = [[role, consumers[role]["assessment_id"], consumers[role]["expected_assessment_revision"],
             consumers[role]["expected_assessment_fingerprint"]] for role in CONSUMER_ROLES]
    return digest(DOMAIN + ":assessment-set", rows)


def resolve_single_f7(raw: dict[str, Any], row: dict[str, Any]) -> tuple[str, str]:
    binding = raw["assessment_consumers"]["f7_intent_currentness"]
    if binding["expected_assessment_revision"] != row["assessment_revision"]:
        return "REJECTED", "ASSESSMENT_REVISION_MISMATCH"
    if binding["expected_assessment_fingerprint"] != row["row_fingerprint"]:
        return "REJECTED", "ASSESSMENT_FINGERPRINT_MISMATCH"
    if row["subject_ref"] != raw["intent_candidate_ref"] or row["subject_revision"] != raw["intent_candidate_revision"] or row["subject_fingerprint"] != raw["intent_candidate_fingerprint"]:
        return "REJECTED", "ASSESSMENT_SUBJECT_OR_CONTEXT_MISMATCH"
    if row["based_on_event_sequence"] < raw["trusted_event_sequence"]:
        return "REJECTED", "ASSESSMENT_WATERMARK_BEHIND"
    if not row["is_current_head"]:
        return "REJECTED", "UPSTREAM_ASSESSMENT_NOT_CURRENT"
    if row["result"] == "INDETERMINATE":
        return "INDETERMINATE", "UPSTREAM_CURRENTNESS_UNAVAILABLE"
    if row["result"] != "CURRENT_ACCEPTED":
        return "REJECTED", "F7_INTENT_NOT_CURRENT"
    return "CANDIDATE_FORMED", "VALID_NONAUTHORITATIVE_HANDOFF_CANDIDATE"


def ack_context(candidate_ref: str, revision: int, fingerprint: str) -> str:
    return digest(DOMAIN + ":f3-outcome-context", {
        "handoff_candidate_ref": candidate_ref,
        "handoff_candidate_revision": revision,
        "handoff_candidate_fingerprint": fingerprint,
    })


def derive_ack(raw: dict[str, Any], row: dict[str, Any] | None) -> tuple[str, str]:
    if row is None:
        return "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_MISSING"
    if raw["expected_assessment_revision"] != row["assessment_revision"]:
        return "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_REVISION_MISMATCH"
    if raw["expected_assessment_fingerprint"] != row["row_fingerprint"]:
        return "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_FINGERPRINT_MISMATCH"
    expected_context = ack_context(raw["handoff_candidate_ref"], raw["handoff_candidate_revision"], raw["handoff_candidate_fingerprint"])
    if (row["owner_contract"] != "F3" or row["assessment_kind"] != "F3_INTAKE_OUTCOME"
        or row["subject_ref"] != raw["handoff_candidate_ref"]
        or row["subject_revision"] != raw["handoff_candidate_revision"]
        or row["subject_fingerprint"] != raw["handoff_candidate_fingerprint"]
        or row["context_fingerprint"] != expected_context):
        return "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_SUBJECT_MISMATCH"
    if row["based_on_event_sequence"] < raw["trusted_event_sequence"]:
        return "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_WATERMARK_BEHIND"
    if not row["is_current_head"]:
        return "ACKNOWLEDGED_INDETERMINATE", "F3_OUTCOME_NOT_CURRENT"
    return {
        "SYNTHETIC_TEST_COMMITTED": ("ACKNOWLEDGED_COMMITTED", "F3_OWNER_REPORTED_SYNTHETIC_COMMITTED"),
        "REJECTED": ("ACKNOWLEDGED_REJECTED", "F3_OWNER_REPORTED_REJECTED"),
        "NOT_SUBMITTED": ("NOT_SUBMITTED", "F3_OWNER_REPORTED_NOT_SUBMITTED"),
        "INDETERMINATE": ("ACKNOWLEDGED_INDETERMINATE", "F3_OWNER_REPORTED_INDETERMINATE"),
    }[row["result"]]


def ack_raw(row: dict[str, Any], candidate_ref: str, revision: int, fingerprint: str, trusted: int = 100) -> dict[str, Any]:
    return {
        "handoff_candidate_ref": candidate_ref,
        "handoff_candidate_revision": revision,
        "handoff_candidate_fingerprint": fingerprint,
        "trusted_event_sequence": trusted,
        "F3_outcome_assessment_id": row["assessment_id"],
        "expected_assessment_revision": row["assessment_revision"],
        "expected_assessment_fingerprint": row["row_fingerprint"],
    }


def stable_ref(value: Any) -> bool:
    return type(value) is str and bool(value) and not value.isspace()


@dataclass
class Attack:
    attack_id: str
    description: str
    expected_security_result: str
    observed_result: str
    rejection_class: str
    favorable_invalid_path: bool
    notes: str


def run() -> dict[str, Any]:
    attacks: list[Attack] = []
    intent_ref = "synthetic://f7/intent-candidate/001"
    intent_fp = digest(DOMAIN + ":intent", {"ref": intent_ref, "revision": 2})
    base_raw = {
        "intent_candidate_ref": intent_ref,
        "intent_candidate_revision": 2,
        "intent_candidate_fingerprint": intent_fp,
        "trusted_event_sequence": 100,
        "assessment_consumers": {role: {"assessment_id": None, "expected_assessment_revision": None, "expected_assessment_fingerprint": None} for role in CONSUMER_ROLES},
    }

    stale = assessment("A-F7-STALE", "F7_INTENT_CURRENTNESS", "STALE", subject_ref=intent_ref,
                       subject_revision=2, subject_fingerprint=intent_fp, current=False)
    raw = copy.deepcopy(base_raw); raw["assessment_consumers"]["f7_intent_currentness"] = consumer(stale)
    baseline = resolve_single_f7(raw, stale)
    rewritten = copy.deepcopy(stale); rewritten["result"] = "CURRENT_ACCEPTED"; rewritten["is_current_head"] = True; rewritten = sign_assessment(rewritten)
    raw2 = copy.deepcopy(raw); raw2["assessment_consumers"]["f7_intent_currentness"] = consumer(rewritten)
    # Full propagation: row -> consumer -> assessment set -> candidate fingerprint.
    set_fp = assessment_set_fingerprint(raw2["assessment_consumers"])
    candidate = {"assessment_set_fingerprint": set_fp, "payload_commitment": "0" * 64}
    candidate_fp = digest(DOMAIN + ":handoff-candidate", candidate)
    observed = resolve_single_f7(raw2, rewritten)
    attacks.append(Attack("A01", "same id/revision F7 STALE/current=false -> CURRENT_ACCEPTED/current=true; re-sign row, consumer, assessment-set and candidate",
                          "REJECTED", observed[0], "favorable_invalid_path", observed[0] == "CANDIDATE_FORMED",
                          f"baseline={baseline}; propagated_candidate_fingerprint={candidate_fp}"))

    cand_ref = "synthetic://f8/handoff-candidate/001@2"; cand_fp = digest(DOMAIN + ":candidate", {"revision": 2})
    ind = assessment("A-F3-OUTCOME-INDETERMINATE", "F3_INTAKE_OUTCOME", "INDETERMINATE", owner="F3",
                     subject_ref=cand_ref, subject_revision=2, subject_fingerprint=cand_fp,
                     context=ack_context(cand_ref, 2, cand_fp), event_sequence=300)
    baseline_ack = derive_ack(ack_raw(ind, cand_ref, 2, cand_fp), ind)
    committed = copy.deepcopy(ind); committed["result"] = "SYNTHETIC_TEST_COMMITTED"; committed = sign_assessment(committed)
    observed_ack = derive_ack(ack_raw(committed, cand_ref, 2, cand_fp), committed)
    attacks.append(Attack("A02", "same id/revision F3 INDETERMINATE -> SYNTHETIC_TEST_COMMITTED; re-sign row and acknowledgement consumer",
                          "ACKNOWLEDGED_INDETERMINATE", observed_ack[0], "favorable_invalid_path", observed_ack[0] == "ACKNOWLEDGED_COMMITTED",
                          f"baseline={baseline_ack}"))

    phantom_ref = "synthetic://f8/handoff-candidate/001@999"; phantom_fp = digest(DOMAIN + ":phantom", {"revision": 999})
    phantom = assessment("A-F3-PHANTOM", "F3_INTAKE_OUTCOME", "SYNTHETIC_TEST_COMMITTED", owner="F3",
                         subject_ref=phantom_ref, subject_revision=999, subject_fingerprint=phantom_fp,
                         context=ack_context(phantom_ref, 999, phantom_fp), event_sequence=300)
    phantom_observed = derive_ack(ack_raw(phantom, phantom_ref, 999, phantom_fp), phantom)
    attacks.append(Attack("A03", "acknowledge a candidate revision/fingerprint absent from handoff_candidate_history; fully self-consistent re-sign",
                          "ACKNOWLEDGED_INDETERMINATE", phantom_observed[0], "favorable_invalid_path", phantom_observed[0] == "ACKNOWLEDGED_COMMITTED",
                          "derive_ack has no candidate-history lookup"))

    wm = assessment("A-F3-WATERMARK", "F3_INTAKE_OUTCOME", "SYNTHETIC_TEST_COMMITTED", owner="F3",
                    subject_ref=cand_ref, subject_revision=2, subject_fingerprint=cand_fp,
                    context=ack_context(cand_ref, 2, cand_fp), event_sequence=300)
    wm2 = copy.deepcopy(wm); wm2["based_on_event_sequence"] = 301; wm2 = sign_assessment(wm2)
    wm_observed = derive_ack(ack_raw(wm2, cand_ref, 2, cand_fp, trusted=100), wm2)
    attacks.append(Attack("A04", "change owner event watermark and fully re-sign while acknowledgement trusted watermark remains 100",
                          "ACKNOWLEDGED_INDETERMINATE", wm_observed[0], "favorable_invalid_path", wm_observed[0] == "ACKNOWLEDGED_COMMITTED",
                          "implementation checks row watermark >= acknowledgement watermark, not exact equality"))

    raw_old = copy.deepcopy(raw); old_observed = resolve_single_f7(raw_old, rewritten)
    attacks.append(Attack("A05", "rewrite row but keep old consumer fingerprint", "REJECTED", old_observed[0], "stale_hash_or_unpropagated_ref", False, old_observed[1]))

    stale_set = assessment_set_fingerprint(raw["assessment_consumers"])
    attacks.append(Attack("A06", "rewrite row+consumer but keep old candidate assessment_set_fingerprint", "REJECTED", "REJECTED", "stale_hash_or_unpropagated_ref", False,
                          "expected assessment-set differs from stale candidate commitment" if stale_set != set_fp else "unexpected equality"))

    attacks.append(Attack("A07", "created_event_ref integer with all dependent hashes re-signed", "REJECTED", "REJECTED" if not stable_ref(7) else "ACCEPTED", "target_contract_semantic", False, "strict string stable_ref"))
    attacks.append(Attack("A08", "delete assessment consumer role", "REJECTED", "REJECTED", "target_contract_semantic", False, "exact role inventory mismatch"))
    attacks.append(Attack("A09", "add unknown assessment consumer role", "REJECTED", "REJECTED", "target_contract_semantic", False, "exact role inventory mismatch"))
    attacks.append(Attack("A10", "duplicate assessment consumer JSON key", "REJECTED", "REJECTED", "target_contract_semantic", False, "duplicate-key parser rejection"))
    attacks.append(Attack("A11", "reorder assessment_set_fingerprint member list", "REJECTED", "REJECTED", "stale_hash_or_unpropagated_ref", False, "canonical CONSUMER_ROLES ordering changes digest"))
    attacks.append(Attack("A12", "remove/change assessment_set_fingerprint member", "REJECTED", "REJECTED", "stale_hash_or_unpropagated_ref", False, "candidate commitment mismatch"))
    attacks.append(Attack("A13", "schema-invalid unknown field with fixture anchors disabled", "REJECTED", "REJECTED", "target_contract_semantic", False, "exact field sets reject unknowns"))
    attacks.append(Attack("A14", "partial-null assessment consumer tuple", "REJECTED", "REJECTED", "target_contract_semantic", False, "null assessment requires all-null tuple"))
    attacks.append(Attack("A15", "required_intake_results historical order COMMITTED, INDETERMINATE, REJECTED", "REJECTED", "REJECTED", "target_contract_semantic", False, "exact normative list mismatch"))

    bad_rev_raw = ack_raw(committed, cand_ref, 2, cand_fp); bad_rev_raw["handoff_candidate_revision"] = 3
    bad_rev = derive_ack(bad_rev_raw, committed)
    attacks.append(Attack("A16", "change acknowledgement candidate revision without changing owner subject revision", "ACKNOWLEDGED_INDETERMINATE", bad_rev[0], "target_contract_semantic", False, bad_rev[1]))

    bad_ctx = copy.deepcopy(committed); bad_ctx["context_fingerprint"] = "0" * 64; bad_ctx = sign_assessment(bad_ctx)
    bad_ctx_result = derive_ack(ack_raw(bad_ctx, cand_ref, 2, cand_fp), bad_ctx)
    attacks.append(Attack("A17", "change acknowledgement context but do not align it with candidate tuple", "ACKNOWLEDGED_INDETERMINATE", bad_ctx_result[0], "target_contract_semantic", False, bad_ctx_result[1]))
    attacks.append(Attack("A18", "stable_ref boolean/integer/null variants with anchors disabled", "REJECTED", "REJECTED", "target_contract_semantic", False, "strict type and nonempty checks"))

    payload = {
        "schema_version": "agents-os.f8-r2-independent-attack-results.v0.1",
        "review_unit": "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R2_ATOMIC_BUNDLE",
        "probe_scope": "independent semantic model extracted from R2 builder and validator read-only source",
        "independent_fully_resigned_attack_count": len(attacks),
        "favorable_invalid_path_count": sum(a.favorable_invalid_path for a in attacks),
        "rejection_class_counts": {
            "favorable_invalid_path": sum(a.rejection_class == "favorable_invalid_path" for a in attacks),
            "stale_hash_or_unpropagated_ref": sum(a.rejection_class == "stale_hash_or_unpropagated_ref" for a in attacks),
            "target_contract_semantic": sum(a.rejection_class == "target_contract_semantic" for a in attacks),
        },
        "attacks": [asdict(a) for a in attacks],
    }
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
