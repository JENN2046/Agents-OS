#!/usr/bin/env python3
"""Build the R1–R5 hash-bound manifest and safe offline ZIP."""

from __future__ import annotations

import argparse
import copy
import hashlib
import zipfile
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml"
MANIFEST = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r5-atomic-independent-review-package-v0.1.manifest.yaml"
REPORT = ROOT / "control-plane/registry/reports/2026-07-21-agents-os-phase-5b-m0b-plan-r5-atomic-independent-review-package-v0.1.md"
RECEIPT = ROOT / "control-plane/registry/receipts/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r5-author-package-fixed-v0.1.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(role: str, path: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": path, "sha256": sha(ROOT / path)}
    row.update(extra)
    return row


def build_manifest() -> dict[str, Any]:
    base = yaml.safe_load(BASE.read_text(encoding="utf-8"))
    doc = copy.deepcopy(base)
    doc["package_id"] = "agents-os-phase-5b-m0b-plan-r5-atomic-independent-review-package-v0.1"
    unit = doc["review_unit"]
    unit["id"] = "PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R5_ATOMIC_BUNDLE"
    unit["subject_count"] = 18
    unit["precedence"] = [
        "R5_explicit_replacements",
        "R4_all_other_clauses",
        "R3_all_other_clauses",
        "R2_all_other_clauses",
        "R1_all_other_clauses",
    ]
    subjects = [
        ("R5_amendment", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-plan-r5-amendment-v0.1.md"),
        ("R5_strict_JSON_integer_profile", "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r5-strict-json-integer-profile-v0.1.yaml"),
    ]
    for role, path in subjects:
        unit["subjects"].append({"ordinal": len(unit["subjects"]) + 1, **entry(role, path)})
    authorities = [
        ("immutable_R4_manifest", str(BASE.relative_to(ROOT))),
        ("immutable_R4_independent_review", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r4-full-atomic-independent-review.yaml"),
        ("immutable_R4_case_results", "control-plane/registry/reviews/2026-07-21-agents-os-phase-5b-m0b-plan-r4-independent-case-results.json"),
        ("immutable_R4_finding_disposition", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r4-finding-disposition-v0.1.yaml"),
        ("Jenn_R5_start_decision", "control-plane/registry/decisions/2026-07-21-agents-os-phase-5b-m0b-plan-r5-narrow-closure-start-decision-v0.1.yaml"),
    ]
    doc["authority_inputs"].extend(entry(role, path) for role, path in authorities)
    evidence = [
        ("R5_strict_integer_witness_builder", "control-plane/registry/build-phase-5b-m0b-plan-r5-strict-integer-witness.py", {"may_substitute_for_independent_judgment": False}),
        ("R5_strict_integer_witness", "control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r5-strict-integer-witness-v0.1.json", {"runtime_usable": False}),
        ("R5_strict_integer_validator", "control-plane/registry/validate-phase-5b-m0b-plan-r5-strict-integer-witness.py", {"may_substitute_for_independent_judgment": False}),
        ("R5_author_self_review_not_independent", "control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r5-author-self-review-v0.1.yaml", {"result": "PASS_FOR_HASH_BOUND_INDEPENDENT_REVIEW", "may_substitute_for_independent_judgment": False}),
        ("R5_review_package_builder", "control-plane/registry/build-phase-5b-m0b-plan-r5-review-package.py", {"may_substitute_for_independent_judgment": False}),
    ]
    doc["author_evidence"].extend(entry(role, path, **extra) for role, path, extra in evidence)
    doc["declared_subject_count"] = len(unit["subjects"])
    doc["declared_authority_input_count"] = len(doc["authority_inputs"])
    doc["declared_author_evidence_count"] = len(doc["author_evidence"])
    doc["declared_total_input_count"] = doc["declared_subject_count"] + doc["declared_authority_input_count"] + doc["declared_author_evidence_count"]
    doc["validator_commands"] = list(base["validator_commands"]) + [
        "python3 -c \"import pathlib,yaml; [yaml.safe_load(pathlib.Path(p).read_text()) for p in ['control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r5-strict-json-integer-profile-v0.1.yaml','control-plane/registry/reviews/2026-07-21-yellow-agents-os-phase-5b-m0b-plan-r5-author-self-review-v0.1.yaml']]\"",
        "python3 control-plane/registry/validate-phase-5b-m0b-plan-r5-strict-integer-witness.py control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r5-strict-integer-witness-v0.1.json",
        "sh -c 't=$(mktemp); python3 control-plane/registry/build-phase-5b-m0b-plan-r5-strict-integer-witness.py \"$t\" >/dev/null && cmp \"$t\" control-plane/registry/examples/2026-07-21-agents-os-phase-5b-m0b-plan-r5-strict-integer-witness-v0.1.json; r=$?; rm -f \"$t\"; exit $r'",
        "python3 -c \"from pathlib import Path; ps=[Path(p) for p in ['control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-plan-r5-amendment-v0.1.md','control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r5-strict-json-integer-profile-v0.1.yaml','control-plane/registry/build-phase-5b-m0b-plan-r5-strict-integer-witness.py','control-plane/registry/validate-phase-5b-m0b-plan-r5-strict-integer-witness.py']]; bad=[(str(p),i+1) for p in ps for i,line in enumerate(p.read_text().splitlines()) if line.rstrip()!=line]; assert not bad,bad\"",
    ]
    doc["required_review_questions"] = [
        "all_99_declared_inputs_match_and_are_fully_read",
        "all_18_subjects_form_one_complete_nonpartial_plan",
        "R1_R2_R3_R4_fixed_lineage_remains_immutable",
        "derived_binding_principal_revision_is_exact_JSON_integer_1",
        "consumed_Command_principal_revision_is_exact_JSON_integer_1",
        "boolean_float_and_all_non_integer_forms_are_rejected_without_coercion",
        "all_four_R4_favorable_invalid_paths_are_target_semantic_rejections_not_seal_only",
        "legal_strict_integer_1_is_not_over_rejected",
        "no_implementation_runtime_database_provider_private_Memory_sensing_or_effect_occurs",
    ]
    doc["independent_adversarial_minimum"] = [
        "replace_each_revision_site_with_JSON_true_false_and_fully_resign",
        "replace_each_revision_site_with_1_0_and_exponent_notation_and_fully_resign",
        "replace_both_sites_together_with_equal_but_wrong_JSON_types",
        "exercise_null_string_array_object_zero_negative_other_integer_and_malformed_forms",
        "rewrite_observations_profile_or_wrapper_root_together_without_changing_consumed_values",
        "retain_legal_integer_1_positive_control",
        "set_any_implementation_runtime_database_VCPToolBox_private_Memory_provider_sensing_or_effect_authority_true",
    ]
    doc["required_output_contract"]["must_report"] = [
        "reviewer_identity_and_independence_basis",
        "exact_manifest_and_archive_sha256",
        "all_99_hashes_and_full_reads",
        "eighteen_subject_hashes_and_atomicity",
        "twenty_validator_commands_and_results",
        "blocker_major_minor_counts",
        "independent_fully_resigned_case_count",
        "four_R4_regression_target_semantic_rejection_count",
        "fixture_seal_only_rejection_count",
        "favorable_invalid_path_count",
        "legal_input_over_rejection_count",
        "uncaught_exception_count",
        "implementation_impossibility_count",
        "second_permission_identity_Task_Command_or_effect_authority_count",
        "automatic_implementation_start_count",
        "requires_R6",
    ]
    doc["required_output_contract"]["no_finding_rule"] = (
        "PASS_NO_BLOCKER is permitted only when all 99 bytes bind, all twenty commands pass, "
        "both consumed sites enforce exact JSON integer type and value 1, all four preserved "
        "cases receive target-semantic rejection with the byte seal separate, the legal integer "
        "positive control remains accepted, and no blocker remains."
    )
    doc["presentation"]["report_path"] = str(REPORT.relative_to(ROOT))
    doc["decision_gate"].update({
        "package_ready": True,
        "independent_review_started": False,
        "plan_freeze_ready": False,
        "authority_after_pass": "Jenn_only",
    })
    doc["non_authorization"].update({
        "independent_review_result_created": False,
        "Phase_5B_plan_frozen": False,
        "Phase_5B_implementation_started": False,
        "implementation_authorized": False,
    })
    return doc


def archive_paths(doc: dict[str, Any]) -> list[str]:
    paths = [row["path"] for row in doc["review_unit"]["subjects"]]
    paths += [row["path"] for key in ("authority_inputs", "author_evidence") for row in doc[key]]
    paths += [str(MANIFEST.relative_to(ROOT)), str(REPORT.relative_to(ROOT)), str(RECEIPT.relative_to(ROOT))]
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate archive input path")
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
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in paths:
            archive.writestr(archive_map[path], (ROOT / path).read_bytes())
        archive.writestr("MANIFEST.yaml", manifest_alias)
        archive.writestr("ARCHIVE_MAP.yaml", map_bytes)
        archive.writestr("CHECKSUMS.sha256", checksum_bytes)


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
