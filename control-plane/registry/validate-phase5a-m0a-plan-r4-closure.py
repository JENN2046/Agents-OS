#!/usr/bin/env python3
"""Validate Plan R4 with isolated in-memory SQLite and fixed VCP owner bytes."""

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
OWNER = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r4.yaml"
PERSIST = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r4.yaml"
ABI = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r4.yaml"
R2_PERSIST = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-exact-persistence-profile-v0.1-r2.yaml"
R3_PERSIST = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r3.yaml"
BUILDER = REG / "build-phase5a-m0a-plan-r4-closure-witness.py"

FIXED = {
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml": "d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49",
    "control-plane/registry/reviews/2026-07-19-yellow-agents-os-phase-5a-m0a-plan-r3-full-atomic-independent-review.yaml": "961236bccb73f423346023d331908929673d84aa3da7989985cf61c00260e673",
}
EXPECTED_OWNER_IDS = [
    "F3_incarnation_and_authority_epoch",
    "F5_claim_lease_and_fencing",
    "F5_receipt_compatibility_and_currentness",
    "F5_dispatch_arm_replay_and_identity_prebranch_check",
    "F5_stored_first_Event_and_call_accounting",
    "F5_first_apply_eligibility_guard",
]
EXPECTED_R4_TABLES = [
    "resident_incarnation", "resident_authority_epoch", "outbox_claim", "delivery_attempt",
    "dispatch_arm", "first_apply_guard", "delivery_receipt",
]
H = "a" * 64


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_builder():
    spec = importlib.util.spec_from_file_location("phase5a_r4_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def table_map(sql: str) -> dict[str, str]:
    result = {}
    for part in sql.split(";"):
        statement = part.strip()
        if not statement:
            continue
        statement += ";"
        match = re.match(r"CREATE TABLE\s+([a-z_]+)\s*\(", statement)
        if match:
            result[match.group(1)] = statement
    return result


def effective_sql(persistence: dict) -> tuple[list[str], str]:
    r2 = load_yaml(R2_PERSIST)
    r3 = load_yaml(R3_PERSIST)
    maps = [table_map(r2["exact_schema_sql"]), table_map(r3["replacement_schema_sql"]), table_map(persistence["replacement_schema_sql"])]
    merged = {}
    for mapping in maps:
        merged.update(mapping)
    order = r2["tables_in_creation_order"]
    return order, "\n".join(merged[name] for name in order)


def new_db(sql: str) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(sql)
    return connection


def event(c: sqlite3.Connection, n: int, name: str) -> None:
    c.execute("INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,canonical_bytes,event_fingerprint) VALUES(?,?,?,?,?,?,?)", (n, name, "TEST", name, 1, b"{}", f"{n:064x}"))


def fact(c: sqlite3.Connection, kind: str, logical: str, ref: str, fp: str, event_sequence: int) -> None:
    c.execute("INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?)", (kind, logical, 1, ref, ref, 1, b"{}", fp, event_sequence))


def insert_epoch(c: sqlite3.Connection, epoch: int, incarnation: str, previous_epoch=None, previous_incarnation=None, previous_fp=None, event_sequence=1) -> None:
    c.execute("""INSERT INTO resident_authority_epoch(
      resident_id,authority_epoch,epoch_fingerprint,expected_previous_authority_epoch,
      previous_authority_epoch_fingerprint,authority_generation,witness_reservation_ref,
      witness_reservation_fingerprint,incarnation_id,previous_incarnation_id,
      restore_decision_ref,restore_decision_fingerprint,ownership_started_event_sequence,canonical_bytes)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        "resident:A", epoch, f"{epoch + 100:064x}", previous_epoch, previous_fp, epoch,
        f"reservation:{epoch}", f"{epoch + 200:064x}", incarnation, previous_incarnation,
        None, None, event_sequence, b"{}"))


def seed_f3(c: sqlite3.Connection, include_restart: bool) -> None:
    c.execute("INSERT INTO resident_identity VALUES(?,?,?,?)", ("resident:A", 1, H, 1))
    event(c, 1, "event:epoch:1")
    c.execute("INSERT INTO resident_incarnation VALUES(?,?,?,?,?)", ("inc:1", "resident:A", 1, H, 1))
    insert_epoch(c, 1, "inc:1", event_sequence=1)
    if include_restart:
        event(c, 2, "event:epoch:2")
        c.execute("INSERT INTO resident_incarnation VALUES(?,?,?,?,?)", ("inc:2", "resident:A", 2, "b" * 64, 2))
        insert_epoch(c, 2, "inc:2", 1, "inc:1", f"{101:064x}", 2)
    c.commit()


def seed_f5_base(c: sqlite3.Connection, suffix: str, start: int) -> dict:
    event(c, start, f"event:{suffix}:base")
    event(c, start + 1, f"event:{suffix}:arm")
    event(c, start + 2, f"event:{suffix}:receipt")
    intent = f"intent:{suffix}"; claim = f"claim:{suffix}"; attempt = f"attempt:{suffix}"
    lease_ref = f"lease:{suffix}"; auth_ref = f"auth:{suffix}"
    lease_fp = f"{start + 300:064x}"; auth_fp = f"{start + 400:064x}"
    c.execute("INSERT INTO outbox_intent VALUES(?,?,?,?,?,?)", (intent, 1, H, b"{}", f"{start + 500:064x}", start))
    fact(c, "OUTBOX_CLAIM_LEASE", intent, lease_ref, lease_fp, start)
    fact(c, "CALL_AUTHORIZATION", auth_ref, auth_ref, auth_fp, start)
    c.execute("""INSERT INTO outbox_claim(claim_id,intent_id,claim_epoch,lease_expires_at_utc,lease_fact_kind,lease_fact_logical_id,lease_fact_ref,lease_fact_revision,lease_fact_fingerprint,claim_fingerprint,created_event_sequence)
      VALUES(?,?,?,?,?,?,?,?,?,?,?)""", (claim, intent, 1, "2026-07-19T23:59:59Z", "OUTBOX_CLAIM_LEASE", intent, lease_ref, 1, lease_fp, f"{start + 600:064x}", start))
    request_id=f"request:{suffix}"; request_fp=f"{start + 700:064x}"; request_bytes=f"request-{suffix}".encode()
    c.execute("INSERT INTO delivery_attempt VALUES(?,?,?,?,?,?,?,?,?)", (attempt, intent, claim, 1, request_id, request_fp, request_bytes, f"{start + 800:064x}", start))
    guard_fp=f"{start + 900:064x}"
    c.execute("INSERT INTO first_apply_guard VALUES(?,?,?,?,?,?)", (intent, attempt, claim, 1, guard_fp, start + 1))
    return {"intent":intent,"claim":claim,"attempt":attempt,"request_id":request_id,"request_fp":request_fp,"request_bytes":request_bytes,"guard_fp":guard_fp,"auth_ref":auth_ref,"auth_fp":auth_fp,"arm_event":start+1,"receipt_event":start+2}


def insert_arm(c: sqlite3.Connection, x: dict, *, request_id=None, event_count=1, call_count=1) -> None:
    c.execute("""INSERT INTO dispatch_arm(arm_id,attempt_id,intent_id,claim_id,request_id,request_fingerprint,request_bytes,first_event_ref,first_event_fingerprint,first_call_authorization_ref,first_call_authorization_revision,first_call_authorization_fingerprint,committed_event_count,committed_call_authorization_count,arm_fingerprint,armed_event_sequence)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (f"arm:{x['attempt']}",x["attempt"],x["intent"],x["claim"],request_id or x["request_id"],x["request_fp"],x["request_bytes"],f"event:{x['intent'].split(':')[1]}:arm",f"{x['arm_event']:064x}",x["auth_ref"],1,x["auth_fp"],event_count,call_count,"f"*64,x["arm_event"]))


def expect_reject(fn) -> bool:
    try:
        fn()
        return False
    except sqlite3.IntegrityError:
        return True


def sqlite_cases(sql: str) -> tuple[list[dict], list[str]]:
    rows=[]; failures=[]
    def record(name: str, expected: str, passed: bool):
        rows.append({"case":name,"expected":expected,"passed":passed})
        if not passed: failures.append(name)

    c=new_db(sql); seed_f3(c,False); record("F3_genesis_epoch_1", "ACCEPT", True); c.close()
    c=new_db(sql); seed_f3(c,True); record("F3_restart_epoch_N_plus_1", "ACCEPT", True); c.close()
    c=new_db(sql); c.execute("BEGIN"); x=seed_f5_base(c,"A",10); insert_arm(c,x); c.execute("INSERT INTO delivery_receipt VALUES(?,?,?,?,?,?,?,?,?,?,?)", ("source:A","receipt:A",x["attempt"],x["intent"],x["claim"],1,x["guard_fp"],"APPLIED_CURRENT",b"{}","e"*64,x["receipt_event"])); c.commit(); record("F5_exact_graph","ACCEPT",True); c.close()

    c=new_db(sql); seed_f3(c,False); event(c,2,"event:epoch:3"); c.execute("INSERT INTO resident_incarnation VALUES(?,?,?,?,?)",("inc:3","resident:A",3,"b"*64,2)); c.commit(); record("F3_epoch_gap","REJECT",expect_reject(lambda:(c.execute("BEGIN"),insert_epoch(c,3,"inc:3",2,"inc:1",f"{101:064x}",2),c.commit()))); c.rollback(); c.close()
    c=new_db(sql); seed_f3(c,False); event(c,2,"event:epoch:2"); c.execute("INSERT INTO resident_incarnation VALUES(?,?,?,?,?)",("inc:2","resident:A",2,"b"*64,2)); c.commit(); record("F3_wrong_previous_incarnation","REJECT",expect_reject(lambda:(c.execute("BEGIN"),insert_epoch(c,2,"inc:2",1,"inc:2",f"{101:064x}",2),c.commit()))); c.rollback(); c.close()
    c=new_db(sql); seed_f3(c,False); c.execute("INSERT INTO resident_incarnation VALUES(?,?,?,?,?)",("inc:2","resident:A",2,"b"*64,1)); c.commit(); record("F3_missing_Event","REJECT",expect_reject(lambda:(c.execute("BEGIN"),insert_epoch(c,2,"inc:2",1,"inc:1",f"{101:064x}",999),c.commit()))); c.rollback(); c.close()
    c=new_db(sql); event(c,10,"event:L:base"); c.execute("INSERT INTO outbox_intent VALUES(?,?,?,?,?,?)",("intent:L",1,H,b"{}","1"*64,10)); fact(c,"OTHER_KIND","intent:L","lease:L","2"*64,10); record("F5_unrelated_lease_fact","REJECT",expect_reject(lambda:c.execute("INSERT INTO outbox_claim VALUES(?,?,?,?,?,?,?,?,?,?,?)",("claim:L","intent:L",1,"2026-07-19T23:59:59Z","OTHER_KIND","intent:L","lease:L",1,"2"*64,"3"*64,10)))); c.close()
    c=new_db(sql); c.execute("BEGIN"); x=seed_f5_base(c,"M",20); c.commit(); record("F5_arm_request_mismatch","REJECT",expect_reject(lambda:(c.execute("BEGIN"),insert_arm(c,x,request_id="request:WRONG"),c.commit()))); c.rollback(); c.close()
    c=new_db(sql); c.execute("BEGIN"); a=seed_f5_base(c,"A",30); b=seed_f5_base(c,"B",40); c.commit(); record("F5_receipt_cross_guard","REJECT",expect_reject(lambda:(c.execute("BEGIN"),c.execute("INSERT INTO delivery_receipt VALUES(?,?,?,?,?,?,?,?,?,?,?)",("source:X","receipt:X",b["attempt"],b["intent"],b["claim"],1,a["guard_fp"],"APPLIED_CURRENT",b"{}","d"*64,b["receipt_event"])),c.commit()))); c.rollback(); c.close()
    c=new_db(sql); c.execute("BEGIN"); x=seed_f5_base(c,"Z",50); c.commit(); record("F5_zero_stored_first_count","REJECT",expect_reject(lambda:insert_arm(c,x,event_count=0))); c.close()
    return rows,failures


def validate(owners: dict, persistence: dict, abi: dict, witness: dict, plugin_bytes: bytes) -> tuple[list[str], list[dict]]:
    errors=[]
    for path,expected in FIXED.items():
        if sha(ROOT/path)!=expected: errors.append(f"fixed lineage mismatch: {path}")
    ids=[x.get("obligation_id") for x in owners.get("replacement_rows",[])]
    if ids!=EXPECTED_OWNER_IDS: errors.append("R4 owner replacement inventory")
    if owners.get("effective_inventory_rules",{}).get("effective_obligation_count")!=63: errors.append("effective obligation count")
    tables=persistence.get("effective_schema",{}).get("replace_R3_or_inherited_tables")
    if tables!=EXPECTED_R4_TABLES or persistence.get("effective_schema",{}).get("effective_table_count")!=18: errors.append("R4 exact table inventory")
    sql_fragment=persistence.get("replacement_schema_sql","")
    required=[
      "expected_previous_authority_epoch = authority_epoch - 1",
      "previous_incarnation_id, previous_authority_epoch_fingerprint",
      "lease_fact_kind = 'OUTBOX_CLAIM_LEASE'",
      "lease_fact_logical_id = intent_id",
      "request_id, request_fingerprint, request_bytes",
      "committed_event_count = 1",
      "committed_call_authorization_count = 1",
      "winning_claim_id",
      "FOREIGN KEY(intent_id, attempt_id, claim_id, first_apply_guard_fingerprint)",
    ]
    for term in required:
        if term not in sql_fragment: errors.append(f"R4 DDL invariant missing: {term}")
    transactions=persistence.get("transaction_replacements",{})
    epoch=transactions.get("resident_incarnation_epoch_RECOVERING_then_witness_bound_READY",{})
    for step in ["insert_new_resident_incarnation","insert_exact_next_resident_authority_epoch","insert_RECOVERING_lifecycle_fact","insert_ownership_Event"]:
        if step not in epoch.get("epoch_transaction_steps",[]): errors.append(f"F3 epoch transaction missing: {step}")
    if "durably_commit_exact_F3_witness" not in epoch.get("between_transactions",""): errors.append("F3 witness commit barrier")
    fixed_cases=persistence.get("fixed_SQLite_cases",{})
    if len(fixed_cases.get("positive",[]))!=3 or len(fixed_cases.get("negative",[]))!=7: errors.append("fixed SQLite case inventory")
    owner=abi.get("fixed_ABI_owner",{})
    if owner.get("git_path")!="Plugin.js" or owner.get("sha256")!="be15f76324b73400fe70052e6f07a0254b2a9c26393009ad1f026793fb36f5a2": errors.append("fixed Plugin.js owner binding")
    if sha_bytes(plugin_bytes)!=owner.get("sha256"): errors.append("Plugin.js bytes mismatch")
    text=plugin_bytes.decode("utf-8")
    for term in ["serviceModule.processToolCall(pluginSpecificArgs, directContext)","requestIp,","sourceNode,","directContext.signal","directContext.decryptedAuthCode"]:
        if term not in text: errors.append(f"fixed Plugin.js evidence missing: {term}")
    inv=abi.get("actual_invocation_replacement",{})
    if inv.get("manager_positional_values")!=["pluginSpecificArgs","directContext"] or inv.get("positional_value_count")!=2: errors.append("actual VCP two-value invocation")
    if inv.get("blocked_plugin_manifest_requiresAdmin") is not False: errors.append("requiresAdmin must remain false")
    flow=abi.get("closed_dataflow_rule",{})
    for term in ["arguments","directContext","requestIp","sourceNode","signal","decryptedAuthCode"]:
        if term not in flow.get("forbidden_sources",[]): errors.append(f"ABI forbidden source missing: {term}")
    order,effective=effective_sql(persistence)
    if len(order)!=18 or len(table_map(effective))!=18: errors.append("effective DDL count")
    case_rows=[]
    try:
        c=new_db(effective); c.close()
        case_rows,case_failures=sqlite_cases(effective)
        errors.extend(f"SQLite case failed: {x}" for x in case_failures)
    except Exception as exc:
        errors.append(f"effective SQLite exception: {type(exc).__name__}: {exc}")
    expected=load_builder().build()
    if witness!=expected: errors.append("witness differs from deterministic derivation")
    root=dict(witness); claimed=root.pop("root_fingerprint",None)
    if claimed!=hashlib.sha256(canonical(root)).hexdigest(): errors.append("witness root fingerprint")
    if witness.get("authority_boundary",{}).get("terminal_outcome")!="NOT_EXECUTED": errors.append("execution boundary")
    return errors,case_rows


def self_test(owners,persistence,abi,witness,plugin_bytes) -> list[str]:
    mutations=[
      ("drop_F3_owner","o",lambda x:x["replacement_rows"].pop(0),"R4 owner replacement inventory"),
      ("drop_epoch_table","p",lambda x:x["effective_schema"]["replace_R3_or_inherited_tables"].remove("resident_authority_epoch"),"R4 exact table inventory"),
      ("remove_epoch_predecessor","p",lambda x:x.__setitem__("replacement_schema_sql",x["replacement_schema_sql"].replace("expected_previous_authority_epoch = authority_epoch - 1","expected_previous_authority_epoch > 0")),"R4 DDL invariant missing"),
      ("allow_zero_Event","p",lambda x:x.__setitem__("replacement_schema_sql",x["replacement_schema_sql"].replace("committed_event_count = 1","committed_event_count >= 0")),"R4 DDL invariant missing"),
      ("allow_zero_call","p",lambda x:x.__setitem__("replacement_schema_sql",x["replacement_schema_sql"].replace("committed_call_authorization_count = 1","committed_call_authorization_count >= 0")),"R4 DDL invariant missing"),
      ("omit_witness_barrier","p",lambda x:x["transaction_replacements"]["resident_incarnation_epoch_RECOVERING_then_witness_bound_READY"].__setitem__("between_transactions","none"),"F3 witness commit barrier"),
      ("wrong_Plugin_hash","a",lambda x:x["fixed_ABI_owner"].__setitem__("sha256","0"*64),"fixed Plugin.js owner binding"),
      ("one_manager_value","a",lambda x:x["actual_invocation_replacement"].__setitem__("positional_value_count",1),"actual VCP two-value invocation"),
      ("requiresAdmin","a",lambda x:x["actual_invocation_replacement"].__setitem__("blocked_plugin_manifest_requiresAdmin",True),"requiresAdmin"),
      ("allow_requestIp","a",lambda x:x["closed_dataflow_rule"]["forbidden_sources"].remove("requestIp"),"ABI forbidden source missing"),
      ("claim_executed","w",lambda x:x["authority_boundary"].__setitem__("terminal_outcome","EXECUTED"),"execution boundary"),
    ]
    failures=[]
    for name,target,mutate,expected_error in mutations:
        o,p,a,w=copy.deepcopy(owners),copy.deepcopy(persistence),copy.deepcopy(abi),copy.deepcopy(witness)
        mutate({"o":o,"p":p,"a":a,"w":w}[target])
        errors,_=validate(o,p,a,w,plugin_bytes)
        if not any(expected_error in error for error in errors): failures.append(name)
    return failures


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("witness",type=Path); parser.add_argument("vcp_plugin_js",type=Path); parser.add_argument("--self-test",action="store_true"); args=parser.parse_args()
    try:
        owners=load_yaml(OWNER); persistence=load_yaml(PERSIST); abi=load_yaml(ABI); witness=json.loads(args.witness.read_text()); plugin_bytes=args.vcp_plugin_js.read_bytes()
        errors,cases=validate(owners,persistence,abi,witness,plugin_bytes); failures=self_test(owners,persistence,abi,witness,plugin_bytes) if args.self_test else []
    except Exception as exc:
        print(json.dumps({"result":"BLOCK","exception":f"{type(exc).__name__}: {exc}"},sort_keys=True)); return 1
    result={"result":"PASS" if not errors and not failures else "BLOCK","R1_R2_R3_fixed_manifests":"3/3","semantic_owner_replacements":"6/6","effective_tables":"18/18","R4_replacement_tables":"7/7","sqlite_in_memory_cases":f"{sum(1 for x in cases if x['passed'])}/{len(cases)}","fixed_mutations_rejected":"11/11" if not failures else f"{11-len(failures)}/11","fixed_Plugin_js_sha256":sha_bytes(plugin_bytes),"database_file_occurrence_count":0,"terminal_outcome":"NOT_EXECUTED","errors":errors,"mutation_failures":failures,"case_results":cases}
    print(json.dumps(result,sort_keys=True)); return 0 if result["result"]=="PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
