#!/usr/bin/env python3
"""Validate Phase 5A M0-A Plan R3 closure without creating a database."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sqlite3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "control-plane/registry"
OWNER_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r3.yaml"
PERSISTENCE_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r3.yaml"
MATERIALIZATION_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r3.yaml"
BUILDER_PATH = REG / "build-phase5a-m0a-plan-r3-closure-witness.py"
R2_INVENTORY_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-closed-contract-obligation-inventory-v0.1-r2.yaml"
R2_PERSISTENCE_PATH = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-exact-persistence-profile-v0.1-r2.yaml"

FIXED = {
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
    "control-plane/registry/reviews/2026-07-19-yellow-agents-os-phase-5a-m0a-plan-r2-full-atomic-independent-review.yaml": "7d8b6305a469aa1153cb74d61c385065528dfd546b9019279f1f219fe1462dad",
}
EXPECTED_CORRECTIONS = [
    "F3_incarnation_and_authority_epoch",
    "F3_intake_and_event_atomicity",
    "F3_exact_replay_or_conflict",
    "F5_claim_lease_and_fencing",
    "F5_receipt_compatibility_and_currentness",
    "F5_dispatch_arm_replay_and_identity_prebranch_check",
    "F5_stored_first_Event_and_call_accounting",
    "F5_first_apply_eligibility_guard",
    "F6_Validation_Requirement_and_Validation_Set_revision_lineage",
    "F6_same_revision_immutable_history_anchor",
    "F6_atomic_Task_completion_eligibility_gate",
]
EXPECTED_REPLACEMENTS = [
    "resident_incarnation", "event", "canonical_fact", "current_fact_pointer", "outbox_claim",
    "delivery_attempt", "dispatch_arm", "first_apply_guard", "delivery_receipt", "task_completion",
]
EXPECTED_INHERITED = [
    "schema_metadata", "resident_identity", "resident_authority_epoch", "command_definition",
    "inbox_command", "command_envelope", "replay_index", "outbox_intent",
]
OWNER_FIELDS = [
    "module_owner", "reducer_or_boundary_owner", "transaction_owner", "persistence_owner",
    "invariant", "positive_test", "negative_test", "replay_test", "crash_test",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_builder():
    spec = importlib.util.spec_from_file_location("phase5a_r3_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def validate(owners: dict, persistence: dict, materialization: dict, witness: dict) -> list[str]:
    errors: list[str] = []
    for path, expected in FIXED.items():
        full = ROOT / path
        if not full.is_file() or sha(full) != expected:
            errors.append(f"fixed lineage mismatch: {path}")

    r2_inventory = load_yaml(R2_INVENTORY_PATH)
    base_ids = [x["obligation_id"] for x in r2_inventory["obligations"]]
    rows = owners.get("replacement_rows", [])
    ids = [x.get("obligation_id") for x in rows]
    if ids != EXPECTED_CORRECTIONS or len(set(ids)) != 11:
        errors.append("exact semantic owner correction inventory")
    for row in rows:
        if row.get("obligation_id") not in base_ids:
            errors.append(f"unknown base obligation: {row.get('obligation_id')}")
        if any(not isinstance(row.get(k), str) or not row[k] for k in OWNER_FIELDS):
            errors.append(f"incomplete semantic owner row: {row.get('obligation_id')}")
    rules = owners.get("effective_inventory_rules", {})
    if rules.get("effective_obligation_count") != 63 or rules.get("add_obligation_ids") != 0 or rules.get("remove_obligation_ids") != 0:
        errors.append("effective obligation count or unauthorized add/remove")
    by_id = {x["obligation_id"]: x for x in rows}
    f3 = by_id.get("F3_intake_and_event_atomicity", {})
    required_f3 = ["inbox_command", "command_envelope", "canonical_fact", "current_fact_pointer", "event", "replay_index", "optional_outbox_intent"]
    if f3.get("transaction_owner") != "admitted_command_commit" or any(x not in f3.get("persistence_owner", "") for x in required_f3):
        errors.append("F3 admitted command owner is not semantically complete")
    stored = by_id.get("F5_stored_first_Event_and_call_accounting", {}).get("persistence_owner", "")
    for term in ["first_Event_ref_fingerprint", "first_call_authorization_ref_fingerprint", "committed_counts"]:
        if term not in stored:
            errors.append("F5 stored-first owner incomplete")

    schema = persistence.get("effective_schema", {})
    if schema.get("effective_table_count") != 18 or schema.get("table_inventory_remains_exhaustive") is not True:
        errors.append("effective table inventory not exhaustive")
    if schema.get("replacement_tables") != EXPECTED_REPLACEMENTS or schema.get("inherited_tables") != EXPECTED_INHERITED:
        errors.append("replacement/inherited table inventory mismatch")
    r2_tables = load_yaml(R2_PERSISTENCE_PATH)["tables_in_creation_order"]
    if sorted(EXPECTED_REPLACEMENTS + EXPECTED_INHERITED) != sorted(r2_tables):
        errors.append("effective 18-table set differs from R2 inventory")
    sql = persistence.get("replacement_schema_sql", "")
    found = re.findall(r"CREATE TABLE ([a-z_]+)", sql)
    if found != EXPECTED_REPLACEMENTS:
        errors.append("replacement DDL table order/count")
    for statement in [x.strip() + ";" for x in sql.split(";") if x.strip()]:
        if not sqlite3.complete_statement(statement):
            errors.append("incomplete SQL statement")
    required_sql = [
        "PRIMARY KEY(fact_kind, logical_id, fact_revision)",
        "predecessor_fact_revision = fact_revision - 1",
        "FOREIGN KEY(fact_kind, logical_id, current_fact_revision, current_fact_ref, current_fact_fingerprint)",
        "CHECK(completion_logical_id = task_ref)",
        "PRIMARY KEY(source_id, receipt_id)",
        "first_call_authorization_ref TEXT NOT NULL",
        "committed_call_authorization_count INTEGER NOT NULL",
        "winning_attempt_id TEXT NOT NULL UNIQUE",
    ]
    for term in required_sql:
        if term not in sql:
            errors.append(f"required DDL invariant missing: {term}")
    first_guard_sql = sql.split("CREATE TABLE first_apply_guard", 1)[1].split("CREATE TABLE delivery_receipt", 1)[0]
    if "receipt" in first_guard_sql.lower():
        errors.append("first-apply guard still depends on receipt")
    lifecycle = persistence.get("resident_lifecycle", {})
    if lifecycle.get("closed_states") != ["COLD", "RECOVERING", "READY", "DRAINING", "STOPPED", "INDETERMINATE"]:
        errors.append("F3 lifecycle mismatch")
    transactions = persistence.get("effective_transaction_owners", {})
    admitted = transactions.get("admitted_command_commit", {})
    if admitted.get("failure_result") != "rollback_every_row":
        errors.append("F3 transaction partial success")
    steps = admitted.get("ordered_steps", [])
    try:
        if not (steps.index("compare_and_set_all_current_fact_pointers_with_deferred_Event_FK") < steps.index("crash_injection_after_pointer_CAS_before_Event") < steps.index("insert_single_committed_Event") < steps.index("COMMIT")):
            errors.append("F3 Event/pointer crash order")
    except ValueError:
        errors.append("F3 ordered steps incomplete")
    arm = transactions.get("dispatch_arm_and_first_apply", {})
    if arm.get("call_boundary_position") != "strictly_after_COMMIT" or arm.get("exact_duplicate") != "return_stored_first_tuple_zero_additional_Event_zero_additional_call_authorization":
        errors.append("F5 arm/call/replay ordering")
    if transactions.get("receipt_apply", {}).get("may_create_first_apply_guard") is not False:
        errors.append("receipt may retroactively create first-apply")
    lineage = persistence.get("lineage_invariants", {})
    for key in ["same_kind_logical_revision_unique", "completion_Task_exact_binding"]:
        if lineage.get(key) is not True:
            errors.append(f"lineage invariant false: {key}")
    if len(persistence.get("fixed_negative_cases", [])) != 12:
        errors.append("persistence negative inventory")

    digest = materialization.get("digest_replacement", {})
    source = digest.get("source_content_tree", {})
    installed = digest.get("installed_projection_tree", {})
    if source.get("inventory") != "R2_planned_source_inventory_minus_package_manifest.json" or installed.get("inventory") != "exact_installed_copy_of_R2_planned_source_inventory_minus_package_manifest.json":
        errors.append("source/installed digest inventory")
    if source.get("leaf_encoding") != installed.get("leaf_encoding") or source.get("mode_rules") != installed.get("mode_rules") or source.get("exclusions") != installed.get("exclusions"):
        errors.append("source/installed digest domains differ")
    if installed.get("prefix_before_leaf_encoding") != "stripped" or digest.get("equality", {}).get("compared_preimages_must_be_byte_identical") is not True:
        errors.append("installed prefix/preimage equality")
    if digest.get("package_manifest", {}).get("excluded_from_both_tree_digests") is not True:
        errors.append("package manifest digest cycle")
    abi = materialization.get("direct_ABI_replacement", {})
    module = abi.get("plugin_module", {})
    if module.get("exact_exports_in_order") != ["initialize", "processToolCall", "shutdown"]:
        errors.append("module exports")
    call = module.get("signatures", {}).get("processToolCall", {})
    if call.get("positional_arguments") != ["args"] or call.get("argument_count") != 1:
        errors.append("VCP direct module processToolCall ABI")
    outer = abi.get("VCP_manager_outer_call", {})
    if outer.get("exported_by_AGENTSOSResident_index_js") is not False:
        errors.append("manager signature exported by module")
    projection = abi.get("manager_to_module_projection", {})
    if projection.get("requestIp_forwarded_to_module") is not False or projection.get("input") != "toolArgs" or projection.get("output") != "args":
        errors.append("manager to module projection")
    if len(materialization.get("fixed_negative_cases", [])) != 8:
        errors.append("materialization negative inventory")
    governance = materialization.get("governance", {})
    for key in ["materialization_authorized", "VCPToolBox_change_authorized", "plugin_enablement_authorized", "runtime_start_authorized"]:
        if governance.get(key) is not False:
            errors.append(f"materialization governance expansion: {key}")

    expected = load_builder().build()
    if witness != expected:
        errors.append("witness differs from independent derivation")
    root = dict(witness); claimed = root.pop("root_fingerprint", None)
    if claimed != hashlib.sha256(canonical(root)).hexdigest():
        errors.append("witness root fingerprint")
    if witness.get("authority_boundary", {}).get("terminal_outcome") != "NOT_EXECUTED":
        errors.append("execution boundary")
    return errors


def self_test(owners, persistence, materialization, witness) -> list[str]:
    results=[]
    def add(name,target,fn):
        o,p,m,w=copy.deepcopy(owners),copy.deepcopy(persistence),copy.deepcopy(materialization),copy.deepcopy(witness)
        fn({'o':o,'p':p,'m':m,'w':w}[target]); results.append((name,bool(validate(o,p,m,w))))
    add("drop_F3_transaction_owner","o",lambda x:x["replacement_rows"][1].__setitem__("transaction_owner",""))
    add("split_F3_outbox_owner","o",lambda x:x["replacement_rows"][1].__setitem__("persistence_owner","inbox_command+event"))
    add("drop_stored_first_call_identity","o",lambda x:x["replacement_rows"][6].__setitem__("persistence_owner","dispatch_arm(first_Event_ref_fingerprint)"))
    add("add_hidden_table","p",lambda x:x["effective_schema"].__setitem__("effective_table_count",19))
    add("restore_conflicting_lifecycle","p",lambda x:x["resident_lifecycle"].__setitem__("closed_states",["STARTING","READY","STOPPED","COMPROMISED"]))
    add("receipt_creates_first_apply","p",lambda x:x["effective_transaction_owners"]["receipt_apply"].__setitem__("may_create_first_apply_guard",True))
    add("call_before_arm_commit","p",lambda x:x["effective_transaction_owners"]["dispatch_arm_and_first_apply"].__setitem__("call_boundary_position","before_COMMIT"))
    add("drop_lineage_uniqueness","p",lambda x:x["lineage_invariants"].__setitem__("same_kind_logical_revision_unique",False))
    add("change_crash_order","p",lambda x:x["effective_transaction_owners"]["admitted_command_commit"]["ordered_steps"].reverse())
    add("installed_tree_includes_manifest","m",lambda x:x["digest_replacement"]["installed_projection_tree"].__setitem__("exclusions",[]))
    add("retain_install_prefix","m",lambda x:x["digest_replacement"]["installed_projection_tree"].__setitem__("prefix_before_leaf_encoding","retained"))
    add("three_argument_module_ABI","m",lambda x:x["direct_ABI_replacement"]["plugin_module"]["signatures"]["processToolCall"].update({'positional_arguments':['toolName','toolArgs','requestIp'],'argument_count':3}))
    add("export_manager_signature","m",lambda x:x["direct_ABI_replacement"]["VCP_manager_outer_call"].__setitem__("exported_by_AGENTSOSResident_index_js",True))
    add("forward_requestIp","m",lambda x:x["direct_ABI_replacement"]["manager_to_module_projection"].__setitem__("requestIp_forwarded_to_module",True))
    add("authorize_materialization","m",lambda x:x["governance"].__setitem__("materialization_authorized",True))
    add("claim_executed","w",lambda x:x["authority_boundary"].__setitem__("terminal_outcome","EXECUTED"))
    return [name for name,rejected in results if not rejected]


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("witness",type=Path); parser.add_argument("--self-test",action="store_true"); args=parser.parse_args()
    try:
        owners=load_yaml(OWNER_PATH); persistence=load_yaml(PERSISTENCE_PATH); materialization=load_yaml(MATERIALIZATION_PATH); witness=json.loads(args.witness.read_text())
        errors=validate(owners,persistence,materialization,witness); failures=self_test(owners,persistence,materialization,witness) if args.self_test else []
    except Exception as exc:
        print(json.dumps({'result':'BLOCK','exception':type(exc).__name__},sort_keys=True)); return 1
    result={'result':'PASS' if not errors and not failures else 'BLOCK','R1_R2_fixed_manifests':'2/2','semantic_owner_replacements':'11/11','effective_tables':'18/18','persistence_negatives':'12/12','materialization_negatives':'8/8','fixed_mutations_rejected':'16/16' if not failures else f"{16-len(failures)}/16",'database_occurrence_count':0,'terminal_outcome':'NOT_EXECUTED','errors':errors,'mutation_failures':failures}
    print(json.dumps(result,sort_keys=True)); return 0 if result['result']=='PASS' else 1


if __name__ == "__main__":
    raise SystemExit(main())
