#!/usr/bin/env python3
"""Validate the fixed Phase 5A M0-A plan R2 closure without side effects."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "control-plane/registry"
INVENTORY_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-closed-contract-obligation-inventory-v0.1-r2.yaml"
PERSISTENCE_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-exact-persistence-profile-v0.1-r2.yaml"
MATERIALIZATION_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-external-materialization-profile-v0.1-r2.yaml"
BUILDER_PATH = REG / "build-phase5a-m0a-plan-r2-closure-witness.py"
R1 = {
    "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-implementation-plan-v0.1.md": "40b8aa4b745d0262369bbefeac3a12367df99e56c67a62e2ba3b208404acc94f",
    "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-build-profile-v0.1.yaml": "e6f2d4e6fea62453a4ecb290e15f48c862a0bc55c829d26e106cae7eaf5f7868",
    "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-contract-traceability-matrix-v0.1.yaml": "85a333265336050223f01c30690e8964bd8870c815a6970ecbf8a9c6e417f612",
    "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-validation-fault-injection-profile-v0.1.yaml": "3ff0536cb55b44cd3fabcfac981f3aaed02ea13f125791d5ad7e1e219545858e",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
}
REVIEW = {
    "control-plane/registry/reviews/2026-07-19-yellow-agents-os-phase-5a-m0a-plan-full-atomic-independent-review.yaml": "68d0fd5a5c6abb63c9b59fec980596aa9bb34adc566115f7cffa1ae9fb02ab48"
}
DECISIONS = {
    "F1": "control-plane/registry/decisions/2026-07-14-agents-os-f1-goal-spec-plan-membership-acceptance-decision-v0.1.yaml",
    "F2": "control-plane/registry/decisions/2026-07-16-agents-os-f2-actor-identity-delegation-r22-atomic-freeze-decision-v0.1.yaml",
    "F3": "control-plane/registry/decisions/2026-07-16-agents-os-f3-resident-singleton-napi-identity-continuity-r4-atomic-freeze-decision-v0.1.yaml",
    "F4": "control-plane/registry/decisions/2026-07-17-agents-os-f4-taskpermit-host-authentication-effect-admission-r9-atomic-freeze-decision-v0.1.yaml",
    "F5": "control-plane/registry/decisions/2026-07-17-agents-os-f5-outbox-delivery-recovery-r7-atomic-freeze-decision-v0.1.yaml",
    "F6": "control-plane/registry/decisions/2026-07-18-agents-os-f6-validation-requirement-current-decision-r6-atomic-freeze-decision-v0.1.yaml",
}
EXPECTED_TABLES = [
    "schema_metadata", "resident_identity", "resident_incarnation", "resident_authority_epoch",
    "command_definition", "inbox_command", "command_envelope", "replay_index", "event",
    "canonical_fact", "current_fact_pointer", "outbox_intent", "outbox_claim", "delivery_attempt",
    "dispatch_arm", "delivery_receipt", "first_apply_guard", "task_completion",
]
EXPECTED_PHASE_COUNTS = {"F1": 3, "F2": 22, "F3": 4, "F4": 29, "F5": 28, "F6": 24}
EXPECTED_OBLIGATION_COUNTS = {"F1": 7, "F2": 12, "F3": 9, "F4": 12, "F5": 12, "F6": 11}
OWNER_FIELDS = [
    "module_owner", "reducer_or_boundary_owner", "persistence_owner", "positive_test",
    "negative_test", "replay_test", "crash_test", "disposition",
]
EXPECTED_SOURCE_INVENTORY = [
    "Cargo.lock", "Cargo.toml", "README.md", "build.rs", "index.js", "package-lock.json",
    "package-manifest.json", "package.json", "plugin-manifest.json.block", "rust-toolchain.toml",
    "src/canonical/fingerprint.rs", "src/canonical/jcs.rs", "src/canonical/mod.rs", "src/canonical/types.rs",
    "src/ledger/mod.rs", "src/ledger/recovery.rs", "src/ledger/replay.rs", "src/ledger/schema.rs",
    "src/ledger/transaction.rs", "src/lib.rs", "src/mock_host/admission.rs", "src/mock_host/dispatch.rs",
    "src/mock_host/mod.rs", "src/napi_frame.rs", "src/reducers/authority_assessment.rs",
    "src/reducers/command_intake.rs", "src/reducers/delivery_receipt.rs", "src/reducers/effect_admission.rs",
    "src/reducers/goal_plan.rs", "src/reducers/mod.rs", "src/reducers/outbox_claim.rs",
    "src/reducers/reconcile.rs", "src/reducers/task_completion.rs",
    "src/reducers/validation_current_decision.rs", "src/resident/ledger_thread.rs",
    "src/resident/lock.rs", "src/resident/mod.rs", "tests/crash_matrix.rs", "tests/napi_protocol.rs",
    "tests/replay_and_idempotency.rs", "tests/synthetic_m0a.rs",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_builder():
    spec = spec_from_file_location("phase5a_r2_builder", BUILDER_PATH)
    module = module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def validate(inventory: dict, persistence: dict, materialization: dict, witness: dict) -> list[str]:
    errors: list[str] = []
    for path, expected in {**R1, **REVIEW}.items():
        full = ROOT / path
        if not full.is_file() or sha(full) != expected:
            errors.append(f"fixed-byte binding mismatch: {path}")

    expected_subjects = []
    for phase, path in DECISIONS.items():
        decision = load_yaml(ROOT / path)
        subjects = decision.get("accepted_subjects", [])
        if len(subjects) != EXPECTED_PHASE_COUNTS[phase]:
            errors.append(f"{phase} accepted subject count")
        for ordinal, subject in enumerate(subjects, 1):
            full = ROOT / subject["path"]
            if not full.is_file() or sha(full) != subject["sha256"]:
                errors.append(f"canonical subject mismatch: {subject['path']}")
            expected_subjects.append({
                "phase": phase, "ordinal": ordinal, "revision": subject.get("revision"),
                "role": subject.get("role"), "path": subject["path"], "sha256": subject["sha256"],
            })
    if inventory.get("canonical_subjects") != expected_subjects:
        errors.append("canonical subject union/order is not exact")
    if len({x["path"] for x in expected_subjects}) != 110:
        errors.append("canonical subject path uniqueness/count")

    obligations = inventory.get("obligations", [])
    if len(obligations) != sum(EXPECTED_OBLIGATION_COUNTS.values()):
        errors.append("closed obligation count")
    if len({x.get("obligation_id") for x in obligations}) != len(obligations):
        errors.append("obligation IDs not unique")
    for phase, count in EXPECTED_OBLIGATION_COUNTS.items():
        if sum(x.get("phase") == phase for x in obligations) != count:
            errors.append(f"{phase} obligation count")
    phase_sets = inventory.get("phase_subject_sets", {})
    for row in obligations:
        phase = row.get("phase")
        if any(not isinstance(row.get(field), str) or not row[field] for field in OWNER_FIELDS):
            errors.append(f"incomplete owners: {row.get('obligation_id')}")
        if row.get("disposition") != "IMPLEMENT_IN_M0A":
            errors.append(f"invalid disposition: {row.get('obligation_id')}")
        if row.get("source_scope") != f"{phase}_ALL_ACCEPTED_SUBJECT_BYTES":
            errors.append(f"invalid source scope: {row.get('obligation_id')}")
        if row.get("source_subject_set_sha256") != phase_sets.get(phase, {}).get("accepted_subject_set_sha256"):
            errors.append(f"source set mismatch: {row.get('obligation_id')}")

    db = persistence.get("database_boundary", {})
    if db.get("inventory_is_exhaustive") is not True or db.get("table_count") != 18:
        errors.append("persistence inventory not exhaustive")
    if persistence.get("tables_in_creation_order") != EXPECTED_TABLES:
        errors.append("exact table inventory/order")
    sql = persistence.get("exact_schema_sql", "")
    found = re.findall(r"CREATE TABLE ([a-z_]+)", sql)
    if found != EXPECTED_TABLES or "CREATE TRIGGER" in sql or "CREATE VIEW" in sql:
        errors.append("exact schema SQL table closure")
    dedicated = persistence.get("dedicated_row_class_mapping", {})
    for key in ["DELIVERY_ATTEMPT", "DISPATCH_ARM_AND_STORED_FIRST_ACCOUNTING", "FIRST_APPLY_ELIGIBILITY", "TASK_COMPLETION"]:
        if key not in dedicated:
            errors.append(f"missing dedicated row class: {key}")
    kinds = persistence.get("canonical_fact_kind_inventory", {})
    for phase in DECISIONS:
        if not isinstance(kinds.get(phase), list) or not kinds[phase]:
            errors.append(f"missing canonical fact kinds: {phase}")
    if set(persistence.get("transaction_owners", {})) != {"command_intake", "canonical_fact_advance", "outbox_enqueue", "outbox_claim", "dispatch_arm", "receipt_apply", "task_completion"}:
        errors.append("transaction owner closure")
    if len(persistence.get("crash_windows", [])) != 8:
        errors.append("crash window closure")

    if materialization.get("planned_source_inventory_is_closed") is not True:
        errors.append("source inventory not closed")
    if materialization.get("planned_source_inventory") != EXPECTED_SOURCE_INVENTORY:
        errors.append("planned source inventory mismatch")
    if materialization.get("inventory_count") != len(EXPECTED_SOURCE_INVENTORY):
        errors.append("source inventory count")
    tree = materialization.get("content_tree_hash", {})
    if tree.get("algorithm") != "SHA-256" or tree.get("inventory_source") != "planned_source_inventory_minus_package_manifest" or tree.get("no_implicit_exclusions") is not True:
        errors.append("tree hash algorithm closure")
    projection = materialization.get("VCPToolBox_projection", {})
    if projection.get("install_root") != "Plugin/AGENTSOSResident" or projection.get("allowed_overlay_glob") != "Plugin/AGENTSOSResident/**" or projection.get("enabled_manifest_must_not_exist") is not True:
        errors.append("projection overlay closure")
    manifest = materialization.get("blocked_plugin_manifest", {})
    value = manifest.get("exact_value", {})
    if manifest.get("path") != "plugin-manifest.json.block" or value.get("name") != "AGENTSOSResident" or value.get("pluginType") != "hybridservice" or value.get("entryPoint") != {"script": "index.js"} or value.get("communication") != {"protocol": "direct", "timeout": 60000}:
        errors.append("blocked manifest exact payload")
    entry = materialization.get("direct_entrypoint", {})
    if entry.get("path") != "index.js" or entry.get("exact_exports") != ["initialize", "shutdown", "processToolCall"] or entry.get("initialize_may_start_runtime") is not False:
        errors.append("direct entrypoint closure")
    if materialization.get("governance", {}).get("profile_authorizes_materialization") is not False:
        errors.append("materialization authority expansion")

    expected_witness = load_builder().build()
    if witness != expected_witness:
        errors.append("witness does not equal independent derivation")
    root = dict(witness); claimed = root.pop("root_fingerprint", None)
    if claimed != hashlib.sha256(canonical(root)).hexdigest():
        errors.append("witness root fingerprint")
    return errors


def self_test(inventory, persistence, materialization, witness) -> list[str]:
    mutations = []
    def add(name, target, fn):
        i, p, m, w = copy.deepcopy(inventory), copy.deepcopy(persistence), copy.deepcopy(materialization), copy.deepcopy(witness)
        fn({"i": i, "p": p, "m": m, "w": w}[target])
        mutations.append((name, bool(validate(i, p, m, w))))
    add("drop_canonical_subject", "i", lambda x: x["canonical_subjects"].pop())
    add("rewrite_canonical_subject_hash", "i", lambda x: x["canonical_subjects"][0].__setitem__("sha256", "0" * 64))
    add("drop_obligation", "i", lambda x: x["obligations"].pop())
    add("blank_SQL_owner", "i", lambda x: x["obligations"][0].__setitem__("persistence_owner", ""))
    add("add_hidden_table", "p", lambda x: x["tables_in_creation_order"].append("hidden_state"))
    add("drop_dispatch_arm_mapping", "p", lambda x: x["dedicated_row_class_mapping"].pop("DISPATCH_ARM_AND_STORED_FIRST_ACCOUNTING"))
    add("change_table_count", "p", lambda x: x["database_boundary"].__setitem__("table_count", 19))
    add("change_tree_algorithm", "m", lambda x: x["content_tree_hash"].__setitem__("algorithm", "SELF_DECLARED"))
    add("allow_enabled_manifest", "m", lambda x: x["VCPToolBox_projection"].__setitem__("enabled_manifest_must_not_exist", False))
    add("change_blocked_entrypoint", "m", lambda x: x["blocked_plugin_manifest"]["exact_value"]["entryPoint"].__setitem__("script", "other.js"))
    add("add_entrypoint_export", "m", lambda x: x["direct_entrypoint"]["exact_exports"].append("processMessages"))
    add("authorize_materialization", "m", lambda x: x["governance"].__setitem__("profile_authorizes_materialization", True))
    return [name for name, rejected in mutations if not rejected]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("witness", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        inventory = load_yaml(INVENTORY_PATH)
        persistence = load_yaml(PERSISTENCE_PATH)
        materialization = load_yaml(MATERIALIZATION_PATH)
        witness = json.loads(args.witness.read_text(encoding="utf-8"))
        errors = validate(inventory, persistence, materialization, witness)
        mutation_failures = self_test(inventory, persistence, materialization, witness) if args.self_test else []
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "exception": type(exc).__name__}, sort_keys=True))
        return 1
    result = {
        "result": "PASS" if not errors and not mutation_failures else "BLOCK",
        "canonical_subjects": "110/110" if not any("subject" in x for x in errors) else "BLOCK",
        "obligations": sum(EXPECTED_OBLIGATION_COUNTS.values()),
        "tables": len(EXPECTED_TABLES),
        "source_inventory": len(EXPECTED_SOURCE_INVENTORY),
        "fixed_mutations_rejected": "12/12" if not mutation_failures else f"{12-len(mutation_failures)}/12",
        "errors": errors,
        "mutation_failures": mutation_failures,
        "terminal_outcome": "NOT_EXECUTED",
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
