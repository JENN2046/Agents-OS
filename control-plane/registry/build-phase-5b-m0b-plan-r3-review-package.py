#!/usr/bin/env python3
"""Build the hash-bound R1+R2+R3 review manifest and safe offline ZIP."""

from __future__ import annotations

import argparse
import copy
import hashlib
import io
import zipfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE_MANIFEST = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml"
MANIFEST = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml"
REPORT = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r3-atomic-independent-review-package-v0.1.md"
RECEIPT = ROOT / "control-plane/registry/receipts/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r3-author-package-fixed-v0.1.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(role: str, path: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": path, "sha256": sha(ROOT / path)}
    row.update(extra)
    return row


def build_manifest() -> dict[str, Any]:
    base = yaml.safe_load(BASE_MANIFEST.read_text(encoding="utf-8"))
    doc = copy.deepcopy(base)
    doc["package_id"] = "agents-os-phase-5b-m0b-plan-r3-atomic-independent-review-package-v0.1"
    unit = doc["review_unit"]
    unit["id"] = "PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R3_ATOMIC_BUNDLE"
    unit["subject_count"] = 12
    unit["precedence"] = ["R3_explicit_replacements", "R2_all_other_clauses", "R1_all_other_clauses"]
    additions = [
        ("R3_amendment", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-plan-r3-amendment-v0.1.md"),
        ("R3_sealed_ABI_F3_shape_profile", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-sealed-abi-f3-shape-profile-v0.1.yaml"),
        ("R3_candidate_schema_profile", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-candidate-schema-profile-v0.1.yaml"),
        ("R3_semantic_validation_profile", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-semantic-validation-profile-v0.1.yaml"),
    ]
    for role, path in additions:
        unit["subjects"].append({"ordinal": len(unit["subjects"]) + 1, **entry(role, path)})
    authority_additions = [
        ("immutable_R2_manifest", str(BASE_MANIFEST.relative_to(ROOT))),
        ("immutable_R2_independent_review", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r2-full-atomic-independent-review.yaml"),
        ("immutable_R2_case_results", "control-plane/registry/reviews/2026-07-21-agents-os-phase-5b-m0b-plan-r2-independent-case-results.json"),
        ("immutable_R2_finding_disposition", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r2-finding-disposition-v0.1.yaml"),
        ("Jenn_R3_start_decision", "control-plane/registry/decisions/2026-07-21-agents-os-phase-5b-m0b-plan-r3-narrow-closure-start-decision-v0.1.yaml"),
    ]
    doc["authority_inputs"].extend(entry(role, path) for role, path in authority_additions)
    evidence_additions = [
        ("R3_deterministic_semantic_witness_builder", "control-plane/registry/build-phase-5b-m0b-plan-r3-semantic-witness.py", {"may_substitute_for_independent_judgment": False}),
        ("R3_synthetic_semantic_witness", "control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r3-semantic-witness-v0.1.json", {"runtime_usable": False}),
        ("R3_offline_semantic_validator", "control-plane/registry/validate-phase-5b-m0b-plan-r3-semantic-witness.py", {"may_substitute_for_independent_judgment": False}),
        ("R3_author_self_review_not_independent", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r3-author-self-review-v0.1.yaml", {"result": "PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW", "may_substitute_for_independent_judgment": False}),
        ("R3_review_package_builder", "control-plane/registry/build-phase-5b-m0b-plan-r3-review-package.py", {"may_substitute_for_independent_judgment": False}),
    ]
    doc["author_evidence"].extend(entry(role, path, **extra) for role, path, extra in evidence_additions)
    doc["declared_subject_count"] = len(unit["subjects"])
    doc["declared_authority_input_count"] = len(doc["authority_inputs"])
    doc["declared_author_evidence_count"] = len(doc["author_evidence"])
    doc["declared_total_input_count"] = sum((doc["declared_subject_count"], doc["declared_authority_input_count"], doc["declared_author_evidence_count"]))
    doc["validator_commands"] = list(base["validator_commands"]) + [
        "python3 -c \"import pathlib,yaml; [yaml.safe_load(pathlib.Path(p).read_text()) for p in ['control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-sealed-abi-f3-shape-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-candidate-schema-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-semantic-validation-profile-v0.1.yaml','control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r3-author-self-review-v0.1.yaml']]\"",
        "python3 control-plane/registry/validate-phase-5b-m0b-plan-r3-semantic-witness.py control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r3-semantic-witness-v0.1.json",
        "sh -c 't=$(mktemp); python3 control-plane/registry/build-phase-5b-m0b-plan-r3-semantic-witness.py \"$t\" >/dev/null && cmp \"$t\" control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r3-semantic-witness-v0.1.json; r=$?; rm -f \"$t\"; exit $r'",
        "python3 -c \"from pathlib import Path; ps=[Path(p) for p in ['control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-plan-r3-amendment-v0.1.md','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-sealed-abi-f3-shape-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-candidate-schema-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r3-semantic-validation-profile-v0.1.yaml','control-plane/registry/build-phase-5b-m0b-plan-r3-semantic-witness.py','control-plane/registry/validate-phase-5b-m0b-plan-r3-semantic-witness.py']]; bad=[(str(p),i+1) for p in ps for i,line in enumerate(p.read_text().splitlines()) if line.rstrip()!=line]; assert not bad,bad\"",
    ]
    doc["required_review_questions"] = [
        "all_73_declared_inputs_match_and_are_fully_read",
        "all_12_subjects_form_one_complete_nonpartial_plan",
        "R1_R2_subjects_manifests_reviews_case_results_and_fixed_commits_remain_immutable",
        "all_five_R2_blockers_are_closed_without_scope_expansion",
        "public_NAPI_inventory_is_derived_from_sealed_lib_rs_and_exact",
        "candidate_genesis_and_same_identity_predecessor_rules_are_constructively_valid",
        "Command_assertion_submission_and_NAPI_request_shapes_match_sealed_F3",
        "prospective_home_intent_type_is_not_misrepresented_as_current_runtime_authority",
        "all_three_composite_FKs_have_exact_implementable_parent_key_coverage",
        "all_14_R2_cases_are_fully_propagated_and_rejected_by_target_semantics_not_fixture_seal",
        "no_implementation_runtime_database_provider_private_Memory_sensing_or_real_effect_occurs",
    ]
    doc["independent_adversarial_minimum"] = [
        "derive_public_NAPI_inventory_directly_from_sealed_source",
        "replace_a_public_method_and_re-sign_without_changing_sealed_source",
        "construct_revision_1_with_any_predecessor_and_revision_2_with_cross_candidate_predecessor",
        "remove_reorder_or_retype_the_composite_parent_unique_key_and_each_FK",
        "replace_the_Command_assertion_submission_or_NAPI_frame_shape_and_fully_propagate",
        "claim_the_prospective_command_type_is_currently_runtime_accepted",
        "replay_all_fourteen_fixed_R2_independent_cases_with_the_fixture_seal_disabled",
        "set_any_implementation_runtime_database_VCPToolBox_private_Memory_provider_sensing_or_effect_authority_true",
    ]
    doc["required_output_contract"]["must_report"] = [
        "reviewer_identity_and_independence_basis", "exact_manifest_path_and_sha256", "archive_sha256_entry_count_safety_and_checksum_results", "all_73_hashes_and_full_reads", "twelve_subject_hashes_and_atomicity", "twelve_validator_commands_and_results", "blocker_major_minor_counts", "finding_ids_with_reproducible_evidence", "independent_fully_resigned_attack_count", "R2_fourteen_case_target_semantic_rejection_count", "fixture_seal_only_rejection_count", "favorable_invalid_path_count", "legal_input_over_rejection_count", "implementation_impossibility_count", "second_permission_identity_Task_Command_or_effect_authority_count", "NAPI_SQLite_writer_or_VCPToolBox_boundary_escape_count", "automatic_implementation_start_count", "requires_R4"
    ]
    doc["required_output_contract"]["no_finding_rule"] = "PASS_NO_BLOCKER is permitted only when every declared byte is available and matched, all twelve commands pass, all five R2 blockers are independently closed, all fourteen R2 cases receive target-semantic rejection with the fixture seal disabled, and no blocker remains."
    doc["presentation"]["report_path"] = str(REPORT.relative_to(ROOT))
    doc["decision_gate"].update({"package_ready": True, "independent_review_started": False, "plan_freeze_ready": False, "authority_after_pass": "Jenn_only"})
    doc["non_authorization"].update({"independent_review_result_created": False, "Phase_5B_plan_frozen": False, "Phase_5B_implementation_started": False, "implementation_authorized": False})
    return doc


def archive_paths(doc: dict[str, Any]) -> list[str]:
    paths = [x["path"] for key in ("subjects",) for x in doc["review_unit"][key]]
    paths += [x["path"] for key in ("authority_inputs", "author_evidence") for x in doc[key]]
    paths += [str(MANIFEST.relative_to(ROOT)), str(REPORT.relative_to(ROOT)), str(RECEIPT.relative_to(ROOT))]
    return paths


def build_archive(doc: dict[str, Any], output: Path) -> None:
    paths = archive_paths(doc)
    archive_map = {path: f"workspace/{path}" for path in paths}
    checksums = {archive_map[path]: sha(ROOT / path) for path in paths}
    manifest_alias = MANIFEST.read_bytes()
    map_bytes = yaml.safe_dump({"schema_version": "agents-os.archive-map.v0.1", "entries": archive_map}, sort_keys=False).encode()
    checksums["MANIFEST.yaml"] = hashlib.sha256(manifest_alias).hexdigest()
    checksums["ARCHIVE_MAP.yaml"] = hashlib.sha256(map_bytes).hexdigest()
    checksum_bytes = "".join(f"{value}  {path}\n" for path, value in sorted(checksums.items())).encode()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in paths:
            zf.writestr(archive_map[path], (ROOT / path).read_bytes())
        zf.writestr("MANIFEST.yaml", manifest_alias)
        zf.writestr("ARCHIVE_MAP.yaml", map_bytes)
        zf.writestr("CHECKSUMS.sha256", checksum_bytes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    doc = build_manifest()
    MANIFEST.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True), encoding="utf-8")
    if args.archive:
        build_archive(doc, args.archive)
        print(f"PASS manifest={sha(MANIFEST)} archive={sha(args.archive)} inputs={doc['declared_total_input_count']}")
    else:
        print(f"PASS manifest={sha(MANIFEST)} inputs={doc['declared_total_input_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
