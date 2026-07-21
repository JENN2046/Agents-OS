#!/usr/bin/env python3
"""Build the R1+R2+R3+R4 hash-bound manifest and safe offline ZIP."""

from __future__ import annotations

import argparse
import copy
import hashlib
import zipfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml"
MANIFEST = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml"
REPORT = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r4-atomic-independent-review-package-v0.1.md"
RECEIPT = ROOT / "control-plane/registry/receipts/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r4-author-package-fixed-v0.1.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(role: str, path: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": path, "sha256": sha(ROOT / path)}
    row.update(extra)
    return row


def build_manifest() -> dict[str, Any]:
    base = yaml.safe_load(BASE.read_text(encoding="utf-8"))
    doc = copy.deepcopy(base)
    doc["package_id"] = "agents-os-phase-5b-m0b-plan-r4-atomic-independent-review-package-v0.1"
    unit = doc["review_unit"]
    unit["id"] = "PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R4_ATOMIC_BUNDLE"
    unit["subject_count"] = 16
    unit["precedence"] = ["R4_explicit_replacements", "R3_all_other_clauses", "R2_all_other_clauses", "R1_all_other_clauses"]
    subjects = [
        ("R4_amendment", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-plan-r4-amendment-v0.1.md"),
        ("R4_sealed_F3_identity_binding", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-sealed-f3-identity-binding-profile-v0.1.yaml"),
        ("R4_candidate_uniqueness", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-candidate-uniqueness-profile-v0.1.yaml"),
        ("R4_composite_FK_inventory", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-composite-fk-inventory-profile-v0.1.yaml"),
    ]
    for role, path in subjects:
        unit["subjects"].append({"ordinal": len(unit["subjects"]) + 1, **entry(role, path)})
    authorities = [
        ("immutable_R3_manifest", str(BASE.relative_to(ROOT))),
        ("immutable_R3_independent_review", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r3-full-atomic-independent-review.yaml"),
        ("immutable_R3_case_results", "control-plane/registry/reviews/2026-07-21-agents-os-phase-5b-m0b-plan-r3-independent-case-results.json"),
        ("immutable_R3_finding_disposition", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r3-finding-disposition-v0.1.yaml"),
        ("Jenn_R4_start_decision", "control-plane/registry/decisions/2026-07-21-agents-os-phase-5b-m0b-plan-r4-narrow-closure-start-decision-v0.1.yaml"),
    ]
    doc["authority_inputs"].extend(entry(role, path) for role, path in authorities)
    evidence = [
        ("R4_closure_witness_builder", "control-plane/registry/build-phase-5b-m0b-plan-r4-closure-witness.py", {"may_substitute_for_independent_judgment": False}),
        ("R4_closure_witness", "control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r4-closure-witness-v0.1.json", {"runtime_usable": False}),
        ("R4_closure_validator", "control-plane/registry/validate-phase-5b-m0b-plan-r4-closure-witness.py", {"may_substitute_for_independent_judgment": False}),
        ("R4_author_self_review_not_independent", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r4-author-self-review-v0.1.yaml", {"result": "PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW", "may_substitute_for_independent_judgment": False}),
        ("R4_review_package_builder", "control-plane/registry/build-phase-5b-m0b-plan-r4-review-package.py", {"may_substitute_for_independent_judgment": False}),
    ]
    doc["author_evidence"].extend(entry(role, path, **extra) for role, path, extra in evidence)
    doc["declared_subject_count"] = len(unit["subjects"])
    doc["declared_authority_input_count"] = len(doc["authority_inputs"])
    doc["declared_author_evidence_count"] = len(doc["author_evidence"])
    doc["declared_total_input_count"] = doc["declared_subject_count"] + doc["declared_authority_input_count"] + doc["declared_author_evidence_count"]
    doc["validator_commands"] = list(base["validator_commands"]) + [
        "python3 -c \"import pathlib,yaml; [yaml.safe_load(pathlib.Path(p).read_text()) for p in ['control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-sealed-f3-identity-binding-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-candidate-uniqueness-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-composite-fk-inventory-profile-v0.1.yaml','control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r4-author-self-review-v0.1.yaml']]\"",
        "python3 control-plane/registry/validate-phase-5b-m0b-plan-r4-closure-witness.py control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r4-closure-witness-v0.1.json",
        "sh -c 't=$(mktemp); python3 control-plane/registry/build-phase-5b-m0b-plan-r4-closure-witness.py \"$t\" >/dev/null && cmp \"$t\" control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r4-closure-witness-v0.1.json; r=$?; rm -f \"$t\"; exit $r'",
        "python3 -c \"from pathlib import Path; ps=[Path(p) for p in ['control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-plan-r4-amendment-v0.1.md','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-sealed-f3-identity-binding-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-candidate-uniqueness-profile-v0.1.yaml','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r4-composite-fk-inventory-profile-v0.1.yaml','control-plane/registry/build-phase-5b-m0b-plan-r4-closure-witness.py','control-plane/registry/validate-phase-5b-m0b-plan-r4-closure-witness.py']]; bad=[(str(p),i+1) for p in ps for i,line in enumerate(p.read_text().splitlines()) if line.rstrip()!=line]; assert not bad,bad\"",
    ]
    doc["required_review_questions"] = [
        "all_87_declared_inputs_match_and_are_fully_read",
        "all_16_subjects_form_one_complete_nonpartial_plan",
        "R1_R2_R3_fixed_lineage_remains_immutable",
        "all_six_identity_and_authentication_values_are_derived_from_sealed_command_intake",
        "candidate_primary_keys_refs_history_refs_and_genesis_identities_are_unique",
        "selected_candidate_resolves_exactly_once_without_map_overwrite",
        "composite_FK_inventory_is_exact_ordered_complete_and_duplicate_free",
        "all_ten_R3_favorable_invalid_paths_are_target_semantic_rejections_not_seal_only",
        "no_implementation_runtime_database_provider_private_Memory_sensing_or_effect_occurs",
    ]
    doc["independent_adversarial_minimum"] = [
        "rewrite_each_of_the_six_F3_identity_or_authentication_values_and_fully_resign",
        "rewrite_the_derived_binding_and_graph_together_without_changing_sealed_source",
        "duplicate_candidate_PK_ref_or_history_identity_and_fully_resign",
        "create_ambiguous_selected_candidate_resolution",
        "remove_duplicate_substitute_add_or_reorder_composite_FK_entries",
        "retain_parent_unique_key_while_removing_all_FKs",
        "set_any_implementation_runtime_database_VCPToolBox_private_Memory_provider_sensing_or_effect_authority_true",
    ]
    doc["required_output_contract"]["must_report"] = ["reviewer_identity_and_independence_basis", "exact_manifest_and_archive_sha256", "all_87_hashes_and_full_reads", "sixteen_subject_hashes_and_atomicity", "sixteen_validator_commands_and_results", "blocker_major_minor_counts", "independent_fully_resigned_attack_count", "ten_R3_regression_target_semantic_rejection_count", "fixture_seal_only_rejection_count", "favorable_invalid_path_count", "legal_input_over_rejection_count", "implementation_impossibility_count", "second_permission_identity_Task_Command_or_effect_authority_count", "automatic_implementation_start_count", "requires_R5"]
    doc["required_output_contract"]["no_finding_rule"] = "PASS_NO_BLOCKER is permitted only when all 87 bytes bind, all sixteen commands pass, all three R3 findings close independently, all ten fixed cases receive target-semantic rejection with the byte seal separate, and no blocker remains."
    doc["presentation"]["report_path"] = str(REPORT.relative_to(ROOT))
    doc["decision_gate"].update({"package_ready": True, "independent_review_started": False, "plan_freeze_ready": False, "authority_after_pass": "Jenn_only"})
    doc["non_authorization"].update({"independent_review_result_created": False, "Phase_5B_plan_frozen": False, "Phase_5B_implementation_started": False, "implementation_authorized": False})
    return doc


def archive_paths(doc: dict[str, Any]) -> list[str]:
    paths = [x["path"] for x in doc["review_unit"]["subjects"]]
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
