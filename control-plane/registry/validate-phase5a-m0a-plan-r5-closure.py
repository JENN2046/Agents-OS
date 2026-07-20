#!/usr/bin/env python3
"""Validate Plan R5 with in-memory SQLite and a closed JavaScript AST/dataflow parser."""

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
OWNER = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r5.yaml"
PERSIST = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r5.yaml"
ABI = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r5.yaml"
SAFE_JS = REG / "examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-safe-wrapper-v0.1.js"
BUILDER = REG / "build-phase5a-m0a-plan-r5-closure-witness.py"
R4_VALIDATOR = REG / "validate-phase5a-m0a-plan-r4-closure.py"
R4_PERSIST = REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r4.yaml"
FIXED = {
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml": "d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml": "0803bd3e90a0652f1e0cc97b9a4168185df37cd9c76506746796e6096d3dbe58",
    "control-plane/registry/reviews/2026-07-19-yellow-agents-os-phase-5a-m0a-plan-r4-full-atomic-independent-review.yaml": "38d7000d568c1f97028bc38689960e7026c0f79d07e77944e4d69856e64ee79f",
    "control-plane/registry/reviews/2026-07-19-yellow-agents-os-phase-5a-m0a-plan-r4-finding-disposition-v0.1.yaml": "486a40d2947d9e315e056f1cb205a0c7f7429cdef41f9c13b063c5c014818552",
    "control-plane/registry/decisions/2026-07-19-agents-os-phase-5a-m0a-plan-r5-narrow-closure-start-decision-v0.1.yaml": "b3bd6682050fe76c45d9fcba500653d59a01cd9b2d6f32390d590573f31f945d",
}
H = "a" * 64
EXPECTED_TABLES = ["event", "resident_incarnation", "resident_authority_epoch", "dispatch_arm"]
EXPECTED_OWNER_IDS = ["F3_incarnation_and_authority_epoch", "F5_stored_first_Event_and_call_accounting"]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
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
    r4 = load_module("phase5a_r4_validator_for_r5", R4_VALIDATOR)
    order, r4_sql = r4.effective_sql(load_yaml(R4_PERSIST))
    merged = table_map(r4_sql)
    merged.update(table_map(persistence["replacement_schema_sql"]))
    return order, "\n".join(merged[name] for name in order)


def new_db(sql: str) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(sql)
    return connection


def event(c: sqlite3.Connection, seq: int, event_id: str, kind: str, aggregate: str, revision: int, fp: str) -> None:
    c.execute(
        "INSERT INTO event(event_sequence,event_id,event_kind,aggregate_ref,aggregate_revision,canonical_bytes,event_fingerprint) VALUES(?,?,?,?,?,?,?)",
        (seq, event_id, kind, aggregate, revision, b"{}", fp),
    )


def fact(c: sqlite3.Connection, kind: str, logical: str, revision: int, ref: str, subject: str, subject_revision: int, fp: str, seq: int) -> None:
    c.execute(
        "INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?)",
        (kind, logical, revision, ref, subject, subject_revision, b"{}", fp, seq),
    )


def seed_resident(c: sqlite3.Connection) -> None:
    c.execute("INSERT INTO resident_identity VALUES(?,?,?,?)", ("resident:A", 1, H, 1))


def add_incarnation_epoch(c: sqlite3.Connection, epoch: int, incarnation: str, seq: int, previous: tuple[int, str, str] | None = None) -> None:
    event_id = f"event:f3-ownership:resident:A:{epoch}"
    event_fp = f"{seq:064x}"
    event(c, seq, event_id, "RESIDENT_OWNERSHIP_STARTED", "resident:A", epoch, event_fp)
    c.execute(
        "INSERT INTO resident_incarnation(incarnation_id,resident_id,incarnation_revision,process_nonce_fingerprint,created_event_sequence,created_event_id,created_event_fingerprint,created_event_kind,created_event_aggregate_ref,created_event_aggregate_revision) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (incarnation, "resident:A", epoch, f"{100 + epoch:064x}", seq, event_id, event_fp, "RESIDENT_OWNERSHIP_STARTED", "resident:A", epoch),
    )
    previous_epoch, previous_incarnation, previous_fp = previous or (None, None, None)
    c.execute(
        """INSERT INTO resident_authority_epoch(
        resident_id,authority_epoch,epoch_fingerprint,expected_previous_authority_epoch,
        previous_authority_epoch_fingerprint,authority_generation,witness_reservation_ref,
        witness_reservation_fingerprint,incarnation_id,incarnation_revision,previous_incarnation_id,
        restore_decision_ref,restore_decision_fingerprint,ownership_event_sequence,
        ownership_event_id,ownership_event_fingerprint,ownership_event_kind,
        ownership_event_aggregate_ref,ownership_event_aggregate_revision,canonical_bytes)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("resident:A", epoch, f"{200 + epoch:064x}", previous_epoch, previous_fp, epoch,
         f"reservation:{epoch}", f"{300 + epoch:064x}", incarnation, epoch, previous_incarnation,
         None, None, seq, event_id, event_fp, "RESIDENT_OWNERSHIP_STARTED", "resident:A", epoch, b"{}"),
    )


def add_witness(c: sqlite3.Connection, epoch: int, seq: int) -> None:
    event(c, seq, f"event:f3-witness:resident:A:{epoch}", "F3_WITNESS_COMMITTED", "resident:A", epoch, f"{seq:064x}")
    ref = f"witness-commit:reservation:{epoch}"
    fp = f"{400 + epoch:064x}"
    fact(c, "F3_WITNESS_COMMIT", "resident:A", 1, ref, f"reservation:{epoch}", epoch, fp, seq)
    c.execute(
        "INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)",
        ("F3_WITNESS_COMMIT", "resident:A", 1, ref, fp, 1, seq),
    )


def ready_allowed(c: sqlite3.Connection, resident: str) -> bool:
    row = c.execute(
        "SELECT authority_epoch,incarnation_id,epoch_fingerprint,witness_reservation_ref,ownership_event_sequence,ownership_event_id,ownership_event_fingerprint FROM resident_authority_epoch WHERE resident_id=? ORDER BY authority_epoch DESC LIMIT 1",
        (resident,),
    ).fetchone()
    if not row:
        return False
    epoch, _incarnation, _epoch_fp, reservation, owner_seq, _event_id, _event_fp = row
    witness = c.execute(
        """SELECT f.subject_ref,f.subject_revision,f.created_event_sequence
        FROM current_fact_pointer p JOIN canonical_fact f
        ON (p.fact_kind,p.logical_id,p.current_fact_revision,p.current_fact_ref,p.current_fact_fingerprint)
         = (f.fact_kind,f.logical_id,f.fact_revision,f.fact_ref,f.fact_fingerprint)
        WHERE p.fact_kind='F3_WITNESS_COMMIT' AND p.logical_id=?""",
        (resident,),
    ).fetchone()
    return witness == (reservation, epoch, witness[2]) and witness[2] >= owner_seq if witness else False


def seed_f5(c: sqlite3.Connection, suffix: str, start: int) -> dict:
    intent = f"intent:{suffix}"; claim = f"claim:{suffix}"; attempt = f"attempt:{suffix}"; arm = f"arm:{suffix}"
    event(c, start, f"event:{suffix}:base", "TEST", intent, 1, f"{start:064x}")
    c.execute("INSERT INTO outbox_intent VALUES(?,?,?,?,?,?)", (intent, 1, H, b"{}", f"{start + 1:064x}", start))
    fact(c, "OUTBOX_CLAIM_LEASE", intent, 1, f"lease:{suffix}", intent, 1, f"{start + 2:064x}", start)
    c.execute(
        "INSERT INTO outbox_claim VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (claim, intent, 1, "2026-07-19T23:59:59Z", "OUTBOX_CLAIM_LEASE", intent, f"lease:{suffix}", 1, f"{start + 2:064x}", f"{start + 3:064x}", start),
    )
    request_id = f"request:{suffix}"; request_fp = f"{start + 4:064x}"; request_bytes = f"request-{suffix}".encode()
    c.execute("INSERT INTO delivery_attempt VALUES(?,?,?,?,?,?,?,?,?)", (attempt, intent, claim, 1, request_id, request_fp, request_bytes, f"{start + 5:064x}", start))
    arm_seq = start + 1; arm_event = f"event:f5-dispatch-arm:{arm}"; arm_event_fp = f"{start + 6:064x}"
    event(c, arm_seq, arm_event, "F5_DISPATCH_ARMED", intent, 1, arm_event_fp)
    auth_ref = f"call-auth:{arm}"; auth_fp = f"{start + 7:064x}"
    fact(c, "F5_CALL_AUTHORIZATION", intent, 1, auth_ref, attempt, 1, auth_fp, arm_seq)
    return {"intent": intent, "claim": claim, "attempt": attempt, "arm": arm, "request_id": request_id,
            "request_fp": request_fp, "request_bytes": request_bytes, "event_seq": arm_seq,
            "event_ref": arm_event, "event_fp": arm_event_fp, "auth_ref": auth_ref, "auth_fp": auth_fp}


def insert_arm(c: sqlite3.Connection, x: dict, **overrides) -> None:
    values = {
        "event_seq": x["event_seq"], "event_ref": x["event_ref"], "event_fp": x["event_fp"],
        "event_kind": "F5_DISPATCH_ARMED", "event_aggregate": x["intent"], "event_revision": 1,
        "auth_kind": "F5_CALL_AUTHORIZATION", "auth_logical": x["intent"], "auth_ref": x["auth_ref"],
        "auth_revision": 1, "auth_fp": x["auth_fp"], "event_count": 1, "auth_count": 1,
    }
    values.update(overrides)
    c.execute(
        """INSERT INTO dispatch_arm(
        arm_id,attempt_id,intent_id,claim_id,attempt_revision,request_id,request_fingerprint,request_bytes,
        first_event_sequence,first_event_ref,first_event_fingerprint,first_event_kind,first_event_aggregate_ref,
        first_event_aggregate_revision,first_call_authorization_kind,first_call_authorization_logical_id,
        first_call_authorization_ref,first_call_authorization_revision,first_call_authorization_fingerprint,
        committed_event_count,committed_call_authorization_count,arm_fingerprint,armed_event_sequence)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (x["arm"], x["attempt"], x["intent"], x["claim"], 1, x["request_id"], x["request_fp"], x["request_bytes"],
         values["event_seq"], values["event_ref"], values["event_fp"], values["event_kind"], values["event_aggregate"], values["event_revision"],
         values["auth_kind"], values["auth_logical"], values["auth_ref"], values["auth_revision"], values["auth_fp"],
         values["event_count"], values["auth_count"], "f" * 64, values["event_seq"]),
    )


def expect_reject(fn) -> bool:
    try:
        fn()
        return False
    except sqlite3.IntegrityError:
        return True


TOKEN = re.compile(
    r"(?P<WS>\s+)|(?P<STRING>'(?:\\.|[^'\\])*')|(?P<ELLIPSIS>\.\.\.)|(?P<OPTIONAL>\?\.)|"
    r"(?P<IDENT>[A-Za-z_$][A-Za-z0-9_$]*)|(?P<PUNCT>[{}()\[\].,:;=])"
)


def lex(source: str) -> list[str]:
    tokens = []
    pos = 0
    while pos < len(source):
        match = TOKEN.match(source, pos)
        if not match:
            raise ValueError(f"unsupported token at {pos}")
        pos = match.end()
        if match.lastgroup != "WS":
            tokens.append(match.group())
    return tokens


class ClosedParser:
    def __init__(self, source: str):
        self.tokens = lex(source)
        self.i = 0

    def take(self, expected: str) -> str:
        if self.i >= len(self.tokens) or self.tokens[self.i] != expected:
            actual = self.tokens[self.i] if self.i < len(self.tokens) else "EOF"
            raise ValueError(f"expected {expected}, got {actual}")
        self.i += 1
        return expected

    def program(self) -> dict:
        self.take("'use strict'"); self.take(";")
        self.take("function"); self.take("projectArgs"); self.take("("); self.take("args"); self.take(")"); self.take("{")
        self.take("return"); self.take("{")
        properties = []
        for index, field in enumerate(["commandRef", "commandFingerprint", "payload"]):
            if index:
                self.take(",")
            self.take(field); self.take(":"); self.take("args"); self.take("."); self.take(field)
            properties.append({"key": field, "source": ["args", field], "computed": False})
        self.take("}"); self.take(";"); self.take("}")
        self.take("async"); self.take("function"); self.take("processToolCall"); self.take("("); self.take("args"); self.take(")"); self.take("{")
        self.take("const"); self.take("nativeFrame"); self.take("="); self.take("projectArgs"); self.take("("); self.take("args"); self.take(")"); self.take(";")
        self.take("return"); self.take("residentNative"); self.take("."); self.take("process"); self.take("("); self.take("nativeFrame"); self.take(")"); self.take(";"); self.take("}")
        self.take("module"); self.take("."); self.take("exports"); self.take("="); self.take("{"); self.take("processToolCall"); self.take("}"); self.take(";")
        if self.i != len(self.tokens):
            raise ValueError("trailing syntax")
        return {"type": "Program", "projectArgs": {"params": ["args"], "properties": properties},
                "processToolCall": {"async": True, "params": ["args"], "flow": ["projectArgs(args)", "residentNative.process(nativeFrame)"]},
                "exports": ["processToolCall"]}


def ast_accepts(source: str) -> bool:
    try:
        ast = ClosedParser(source).program()
    except ValueError:
        return False
    return (
        ast["projectArgs"]["params"] == ["args"]
        and [p["key"] for p in ast["projectArgs"]["properties"]] == ["commandRef", "commandFingerprint", "payload"]
        and ast["processToolCall"]["params"] == ["args"]
        and ast["processToolCall"]["flow"] == ["projectArgs(args)", "residentNative.process(nativeFrame)"]
    )


def sqlite_cases(sql: str) -> tuple[list[dict], list[str]]:
    rows = []; failures = []
    def record(name: str, expected: str, passed: bool):
        rows.append({"case": name, "expected": expected, "passed": passed})
        if not passed:
            failures.append(name)

    c = new_db(sql); seed_resident(c); add_incarnation_epoch(c, 1, "inc:1", 1); add_witness(c, 1, 2); c.commit()
    record("F3_exact_ownership_Event_and_witness_READY", "ACCEPT", ready_allowed(c, "resident:A")); c.close()

    c = new_db(sql); seed_resident(c); event(c, 1, "event:f3-ownership:resident:A:1", "OTHER", "resident:A", 1, "1" * 64)
    record("F3_unrelated_Event_tuple", "REJECT", expect_reject(lambda: (
        c.execute("INSERT INTO resident_incarnation VALUES(?,?,?,?,?,?,?,?,?,?)",
                  ("inc:1", "resident:A", 1, H, 1, "event:f3-ownership:resident:A:1", "1" * 64, "RESIDENT_OWNERSHIP_STARTED", "resident:A", 1)),
        c.commit()))); c.close()

    c = new_db(sql); seed_resident(c); add_incarnation_epoch(c, 1, "inc:1", 1); c.commit()
    record("F3_READY_without_exact_witness", "REJECT", not ready_allowed(c, "resident:A")); c.close()

    c = new_db(sql); seed_resident(c); add_incarnation_epoch(c, 1, "inc:1", 1); add_incarnation_epoch(c, 2, "inc:2", 2, (1, "inc:1", f"{201:064x}")); c.commit()
    event(c, 3, "event:f3-ownership:resident:A:3", "RESIDENT_OWNERSHIP_STARTED", "resident:A", 3, "3" * 64)
    record("F3_historical_incarnation_reuse", "REJECT", expect_reject(lambda: c.execute(
        """INSERT INTO resident_authority_epoch(resident_id,authority_epoch,epoch_fingerprint,expected_previous_authority_epoch,previous_authority_epoch_fingerprint,authority_generation,witness_reservation_ref,witness_reservation_fingerprint,incarnation_id,incarnation_revision,previous_incarnation_id,ownership_event_sequence,ownership_event_id,ownership_event_fingerprint,ownership_event_kind,ownership_event_aggregate_ref,ownership_event_aggregate_revision,canonical_bytes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("resident:A", 3, "9"*64, 2, f"{202:064x}", 3, "reservation:3", "8"*64, "inc:1", 1, "inc:2", 3, "event:f3-ownership:resident:A:3", "3"*64, "RESIDENT_OWNERSHIP_STARTED", "resident:A", 3, b"{}")))); c.close()

    c = new_db(sql); x = seed_f5(c, "A", 10); insert_arm(c, x); c.commit()
    stored = c.execute("SELECT first_event_sequence,first_event_ref,first_event_fingerprint,first_call_authorization_kind,first_call_authorization_logical_id,first_call_authorization_ref,first_call_authorization_revision,first_call_authorization_fingerprint,committed_event_count,committed_call_authorization_count FROM dispatch_arm WHERE arm_id=?", (x["arm"],)).fetchone()
    expected = (x["event_seq"], x["event_ref"], x["event_fp"], "F5_CALL_AUTHORIZATION", x["intent"], x["auth_ref"], 1, x["auth_fp"], 1, 1)
    record("F5_exact_first_apply_and_replay", "ACCEPT", stored == expected); c.close()

    c = new_db(sql); x = seed_f5(c, "B", 20); event(c, 22, "event:other", "F5_DISPATCH_ARMED", x["intent"], 1, "b"*64)
    record("F5_unrelated_first_Event", "REJECT", expect_reject(lambda: insert_arm(c, x, event_seq=22, event_ref="event:other", event_fp="b"*64))); c.close()
    c = new_db(sql); x = seed_f5(c, "C", 30)
    record("F5_wrong_call_authorization_kind", "REJECT", expect_reject(lambda: insert_arm(c, x, auth_kind="OTHER"))); c.close()
    c = new_db(sql); x = seed_f5(c, "D", 40)
    record("F5_wrong_call_authorization_logical_id", "REJECT", expect_reject(lambda: insert_arm(c, x, auth_logical="intent:OTHER"))); c.close()
    return rows, failures


def validate(owners: dict, persistence: dict, abi: dict, witness: dict, source_bytes: bytes) -> tuple[list[str], list[dict]]:
    errors = []
    for path, expected in FIXED.items():
        if sha(ROOT / path) != expected:
            errors.append(f"fixed lineage mismatch: {path}")
    if [row.get("obligation_id") for row in owners.get("replacement_rows", [])] != EXPECTED_OWNER_IDS:
        errors.append("R5 owner replacement inventory")
    if witness.get("sections", {}).get("semantic_owner_replacements") != owners.get("replacement_rows"):
        errors.append("witness semantic owner binding")
    if owners.get("effective_inventory_rules", {}).get("effective_obligation_count") != 63:
        errors.append("effective obligation count")
    schema = persistence.get("effective_schema", {})
    if schema.get("effective_table_count") != 18 or schema.get("replace_R4_or_inherited_tables") != EXPECTED_TABLES:
        errors.append("R5 table replacement inventory")
    for term in [
        "UNIQUE(resident_id, incarnation_id)",
        "created_event_id = 'event:f3-ownership:' || resident_id || ':' || incarnation_revision",
        "ownership_event_id = 'event:f3-ownership:' || resident_id || ':' || authority_epoch",
        "first_event_ref = 'event:f5-dispatch-arm:' || arm_id",
        "first_call_authorization_ref = 'call-auth:' || arm_id",
        "first_call_authorization_kind = 'F5_CALL_AUTHORIZATION'",
        "first_call_authorization_logical_id = intent_id",
        "armed_event_sequence = first_event_sequence",
    ]:
        if term not in persistence.get("replacement_schema_sql", ""):
            errors.append(f"R5 DDL invariant missing: {term}")
    transactions = persistence.get("transaction_replacements", {})
    if sorted(transactions) != ["F3_READY_after_witness", "F3_RECOVERING_startup", "F5_first_apply_and_replay"]:
        errors.append("transaction replacement inventory")
    if witness.get("sections", {}).get("persistence", {}).get("transactions") != transactions:
        errors.append("witness transaction binding")
    contract = abi.get("validator_contract", {})
    if contract.get("parser_version") != "agents-os.javascript-closed-subset-ast.v0.1":
        errors.append("parser version")
    if contract.get("allowed_args_fields") != ["commandRef", "commandFingerprint", "payload"]:
        errors.append("args whitelist")
    if any(contract.get(key) != "BLOCK" for key in ["unsupported_syntax_result", "unknown_token_result", "unknown_flow_result", "parse_ambiguity_result"]):
        errors.append("fail-closed parser results")
    if sha_bytes(source_bytes) != abi.get("fixed_future_wrapper", {}).get("sha256"):
        errors.append("safe source hash")
    try:
        source = source_bytes.decode("utf-8")
    except UnicodeDecodeError:
        errors.append("safe source UTF-8")
        source = ""
    if not ast_accepts(source):
        errors.append("safe source AST/dataflow")
    case_rows = []
    for case in witness.get("sections", {}).get("ast_dataflow", {}).get("source_cases", []):
        actual = "ACCEPT" if ast_accepts(case.get("source", "")) else "BLOCK"
        passed = actual == case.get("expected")
        case_rows.append({"case": case.get("case_id"), "expected": case.get("expected"), "actual": actual, "passed": passed})
        if not passed:
            errors.append(f"AST case failed: {case.get('case_id')}")
    order, sql = effective_sql(persistence)
    if len(order) != 18 or len(table_map(sql)) != 18:
        errors.append("effective table count")
    try:
        c = new_db(sql)
        if c.execute("PRAGMA foreign_key_check").fetchall():
            errors.append("effective foreign key check")
        c.close()
        sql_rows, sql_failures = sqlite_cases(sql)
        case_rows.extend(sql_rows)
        errors.extend(f"SQLite case failed: {name}" for name in sql_failures)
    except sqlite3.Error as exc:
        errors.append(f"effective SQLite materialization: {exc}")
    builder = load_module("phase5a_r5_builder_for_validator", BUILDER)
    expected_witness = builder.build()
    if witness != expected_witness:
        errors.append("witness bytes do not equal deterministic builder model")
    return errors, case_rows


def self_test(owners: dict, persistence: dict, abi: dict, witness: dict, source_bytes: bytes) -> list[str]:
    failures = []
    mutations = []
    x = copy.deepcopy(owners); x["replacement_rows"][0]["transaction_owner"] = "caller"; mutations.append(("owner", x, persistence, abi, witness, source_bytes))
    x = copy.deepcopy(persistence); x["effective_schema"]["effective_table_count"] = 19; mutations.append(("table_count", owners, x, abi, witness, source_bytes))
    x = copy.deepcopy(persistence); x["transaction_replacements"]["F3_READY_after_witness"]["resolve_exact_witness"] = "label_only"; mutations.append(("witness_predicate", owners, x, abi, witness, source_bytes))
    x = copy.deepcopy(abi); x["validator_contract"]["unknown_flow_result"] = "ACCEPT"; mutations.append(("fail_open", owners, persistence, x, witness, source_bytes))
    x = copy.deepcopy(abi); x["validator_contract"]["allowed_args_fields"].append("requestIp"); mutations.append(("args_expansion", owners, persistence, x, witness, source_bytes))
    x = copy.deepcopy(witness); x["sections"]["ast_dataflow"]["source_cases"][1]["expected"] = "ACCEPT"; mutations.append(("case_claim", owners, persistence, abi, x, source_bytes))
    mutations.append(("source_second_param", owners, persistence, abi, witness, source_bytes.replace(b"processToolCall(args)", b"processToolCall(args, directContext)")))
    for name, o, p, a, w, s in mutations:
        errors, _ = validate(o, p, a, w, s)
        if not errors:
            failures.append(name)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("witness", type=Path)
    parser.add_argument("index_js", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        witness = json.loads(args.witness.read_text(encoding="utf-8"))
        owners = load_yaml(OWNER); persistence = load_yaml(PERSIST); abi = load_yaml(ABI)
        source_bytes = args.index_js.read_bytes()
        errors, cases = validate(owners, persistence, abi, witness, source_bytes)
        mutation_failures = self_test(owners, persistence, abi, witness, source_bytes) if args.self_test and not errors else []
        errors.extend(f"self-test mutation accepted: {name}" for name in mutation_failures)
    except Exception as exc:
        errors = [f"stable BLOCK: {type(exc).__name__}: {exc}"]
        cases = []; mutation_failures = []
    print(json.dumps({
        "result": "PASS_NO_BLOCKER" if not errors else "BLOCK",
        "errors": errors,
        "effective_table_count": 18 if not errors else None,
        "case_count": len(cases),
        "cases": cases,
        "self_test_mutations": 7 if args.self_test else 0,
        "self_test_failures": mutation_failures,
        "database_file_occurrence_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
