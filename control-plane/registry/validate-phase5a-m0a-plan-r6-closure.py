#!/usr/bin/env python3
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
R5_VALIDATOR = ROOT / "control-plane/registry/validate-phase5a-m0a-plan-r5-closure.py"
R5_PERSIST = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r5.yaml"
R6_OWNER = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r6.yaml"
R6_PERSIST = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r6.yaml"
R6_ABI = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r6.yaml"
R6_TOTALITY = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-structured-input-totality-corrections-v0.1-r6.yaml"
R6_BUILDER = ROOT / "control-plane/registry/build-phase5a-m0a-plan-r6-closure-witness.py"

FIXED_HASHES = {
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml": "d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml": "0803bd3e90a0652f1e0cc97b9a4168185df37cd9c76506746796e6096d3dbe58",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r5-atomic-independent-review-package-v0.1.manifest.yaml": "e26d5e1fa35a6bb69ae26747580e066d58eed5ab9a55371ecce35a991c337fa3",
    "control-plane/registry/decisions/2026-07-19-agents-os-phase-5a-m0a-plan-r6-narrow-closure-start-decision-v0.1.yaml": "e7fa64d934e6c2f58275f9ef013c60aea98cab1fcb9495177b6eb46022ff8a33",
}
H = "a" * 64


class DuplicateKeyError(ValueError):
    pass


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DuplicateKeyError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml_strict(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def loads_json_strict(data: bytes | str):
    text = data.decode("utf-8") if isinstance(data, bytes) else data
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


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


def effective_sql(persistence: dict) -> tuple[list[str], str, str]:
    r5 = load_module("phase5a_r5_for_r6", R5_VALIDATOR)
    order, r5_sql = r5.effective_sql(load_yaml_strict(R5_PERSIST))
    merged = table_map(r5_sql)
    merged.update(table_map(persistence["replacement_schema_sql"]))
    return order, "\n".join(merged[name] for name in order), persistence["immutable_trigger_sql"]


def new_db(sql: str, triggers: str) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.executescript(sql)
    connection.executescript(triggers)
    return connection


def expect_integrity_error(fn) -> bool:
    try:
        fn()
        return False
    except sqlite3.IntegrityError:
        return True


def insert_exact_witness(r5, c: sqlite3.Connection, decoded: dict, raw: bytes | None = None, fingerprint: str | None = None) -> None:
    payload = canonical(decoded) if raw is None else raw
    fp = sha_bytes(payload) if fingerprint is None else fingerprint
    r5.event(c, 2, "event:f3-witness:resident:A:1", "F3_WITNESS_COMMITTED", "resident:A", 1, f"{2:064x}")
    c.execute(
        """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,created_event_sequence)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        ("F3_WITNESS_COMMIT", "resident:A", 1, "witness-commit:reservation:1", "reservation:1", 1, payload, fp, 2),
    )
    c.execute("INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)", ("F3_WITNESS_COMMIT", "resident:A", 1, "witness-commit:reservation:1", fp, 1, 2))


def witness_tuple(c: sqlite3.Connection, resident: str) -> tuple[bool, dict | None]:
    epoch = c.execute(
        """SELECT authority_epoch,incarnation_id,epoch_fingerprint,witness_reservation_ref,
        witness_reservation_fingerprint,ownership_event_sequence,ownership_event_id,ownership_event_fingerprint
        FROM resident_authority_epoch WHERE resident_id=? ORDER BY authority_epoch DESC LIMIT 1""", (resident,)
    ).fetchone()
    if not epoch:
        return False, None
    fact = c.execute(
        """SELECT f.subject_ref,f.subject_revision,f.canonical_bytes,f.fact_fingerprint,f.created_event_sequence
        FROM current_fact_pointer p JOIN canonical_fact f
        ON (p.fact_kind,p.logical_id,p.current_fact_revision,p.current_fact_ref,p.current_fact_fingerprint)
         = (f.fact_kind,f.logical_id,f.fact_revision,f.fact_ref,f.fact_fingerprint)
        WHERE p.fact_kind='F3_WITNESS_COMMIT' AND p.logical_id=?""", (resident,)
    ).fetchone()
    if not fact:
        return False, None
    authority_epoch, incarnation, epoch_fp, reservation, reservation_fp, owner_seq, owner_id, owner_fp = epoch
    subject, subject_revision, raw, fact_fp, created_seq = fact
    try:
        decoded = loads_json_strict(raw)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False, None
    expected = {
        "authority_epoch": authority_epoch,
        "epoch_fingerprint": epoch_fp,
        "incarnation_id": incarnation,
        "ownership_event_fingerprint": owner_fp,
        "ownership_event_id": owner_id,
        "ownership_event_sequence": owner_seq,
        "resident_id": resident,
        "witness_reservation_fingerprint": reservation_fp,
        "witness_reservation_ref": reservation,
    }
    valid = (
        decoded == expected and canonical(decoded) == raw and sha_bytes(raw) == fact_fp
        and subject == reservation and subject_revision == authority_epoch and created_seq >= owner_seq
    )
    return valid, expected if valid else None


def commit_ready(r5, c: sqlite3.Connection, resident: str) -> bool:
    valid, expected = witness_tuple(c, resident)
    if not valid or expected is None:
        return False
    seq = c.execute("SELECT MAX(event_sequence)+1 FROM event").fetchone()[0]
    event_id = f"event:f3-ready:{resident}:{expected['authority_epoch']}"
    event_fp = f"{seq:064x}"
    r5.event(c, seq, event_id, "RESIDENT_READY", resident, expected["authority_epoch"], event_fp)
    payload = canonical({"authority_epoch": expected["authority_epoch"], "lifecycle": "READY", "resident_id": resident})
    fp = sha_bytes(payload)
    c.execute(
        """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,created_event_sequence)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        ("RESIDENT_LIFECYCLE", resident, 1, f"resident-lifecycle:{resident}:1", resident, expected["authority_epoch"], payload, fp, seq),
    )
    c.execute("INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)", ("RESIDENT_LIFECYCLE", resident, 1, f"resident-lifecycle:{resident}:1", fp, 1, seq))
    c.commit()
    return c.execute("SELECT current_fact_revision FROM current_fact_pointer WHERE fact_kind='RESIDENT_LIFECYCLE' AND logical_id=?", (resident,)).fetchone() == (1,)


def insert_arm(c: sqlite3.Connection, x: dict, subject_ref: str | None = None, subject_revision: int | None = None) -> None:
    values = (
        x["arm"], x["attempt"], x["intent"], x["claim"], 1, x["request_id"], x["request_fp"], x["request_bytes"],
        x["event_seq"], x["event_ref"], x["event_fp"], "F5_DISPATCH_ARMED", x["intent"], 1,
        "F5_CALL_AUTHORIZATION", x["intent"], x["auth_ref"], 1, x["auth_fp"],
        subject_ref or x["attempt"], subject_revision or 1, 1, 1, "f" * 64, x["event_seq"],
    )
    c.execute("""INSERT INTO dispatch_arm(
      arm_id,attempt_id,intent_id,claim_id,attempt_revision,request_id,request_fingerprint,request_bytes,
      first_event_sequence,first_event_ref,first_event_fingerprint,first_event_kind,first_event_aggregate_ref,first_event_aggregate_revision,
      first_call_authorization_kind,first_call_authorization_logical_id,first_call_authorization_ref,first_call_authorization_revision,
      first_call_authorization_fingerprint,first_call_authorization_subject_ref,first_call_authorization_subject_revision,
      committed_event_count,committed_call_authorization_count,arm_fingerprint,armed_event_sequence)
      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)


def replay_snapshot(c: sqlite3.Connection, arm: str) -> tuple[tuple, tuple[int, int]]:
    row = c.execute("""SELECT first_event_sequence,first_event_ref,first_event_fingerprint,
      first_call_authorization_kind,first_call_authorization_logical_id,first_call_authorization_ref,
      first_call_authorization_revision,first_call_authorization_fingerprint,
      first_call_authorization_subject_ref,first_call_authorization_subject_revision
      FROM dispatch_arm WHERE arm_id=?""", (arm,)).fetchone()
    counts = (
        c.execute("SELECT COUNT(*) FROM event").fetchone()[0],
        c.execute("SELECT COUNT(*) FROM canonical_fact WHERE fact_kind='F5_CALL_AUTHORIZATION'").fetchone()[0],
    )
    return row, counts


TOKEN = re.compile(r"(?P<WS>\s+)|(?P<STRING>'(?:\\.|[^'\\])*')|(?P<ELLIPSIS>\.\.\.)|(?P<IDENT>[A-Za-z_$][A-Za-z0-9_$]*)|(?P<PUNCT>[{}()\[\].,:;=])")


def lex(source: str) -> list[str]:
    tokens = []; pos = 0
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
        self.tokens = lex(source); self.i = 0

    def take(self, expected: str):
        actual = self.tokens[self.i] if self.i < len(self.tokens) else "EOF"
        if actual != expected:
            raise ValueError(f"expected {expected}, got {actual}")
        self.i += 1

    def object_return(self, key: str, value: str):
        self.take("return"); self.take("{"); self.take(key); self.take(":"); self.take(value); self.take("}"); self.take(";")

    def program(self) -> dict:
        self.take("'use strict'"); self.take(";")
        self.take("async"); self.take("function"); self.take("initialize"); self.take("("); self.take("config"); self.take(","); self.take("dependencies"); self.take(")"); self.take("{")
        self.object_return("initialized", "false"); self.take("}")
        self.take("function"); self.take("projectArgs"); self.take("("); self.take("args"); self.take(")"); self.take("{"); self.take("return"); self.take("{")
        for index, field in enumerate(["commandRef", "commandFingerprint", "payload"]):
            if index: self.take(",")
            self.take(field); self.take(":"); self.take("args"); self.take("."); self.take(field)
        self.take("}"); self.take(";"); self.take("}")
        self.take("async"); self.take("function"); self.take("processToolCall"); self.take("("); self.take("args"); self.take(")"); self.take("{")
        self.take("const"); self.take("nativeFrame"); self.take("="); self.take("projectArgs"); self.take("("); self.take("args"); self.take(")"); self.take(";")
        self.take("return"); self.take("residentNative"); self.take("."); self.take("execute_command"); self.take("("); self.take("nativeFrame"); self.take(")"); self.take(";"); self.take("}")
        self.take("async"); self.take("function"); self.take("shutdown"); self.take("("); self.take(")"); self.take("{")
        self.object_return("shutdown", "true"); self.take("}")
        self.take("module"); self.take("."); self.take("exports"); self.take("="); self.take("{"); self.take("initialize"); self.take(","); self.take("processToolCall"); self.take(","); self.take("shutdown"); self.take("}"); self.take(";")
        if self.i != len(self.tokens): raise ValueError("trailing syntax")
        return {"exports": ["initialize", "processToolCall", "shutdown"], "native_method": "execute_command", "projected_fields": ["commandRef", "commandFingerprint", "payload"]}


def ast_accepts(source: str) -> bool:
    try:
        return ClosedParser(source).program() == {"exports": ["initialize", "processToolCall", "shutdown"], "native_method": "execute_command", "projected_fields": ["commandRef", "commandFingerprint", "payload"]}
    except ValueError:
        return False


def source_cases(source: str) -> tuple[list[dict], list[str]]:
    variants = {
        "residentNative_process_sixth_method": source.replace("execute_command", "process"),
        "missing_initialize_export": source.replace("initialize, processToolCall, shutdown", "processToolCall, shutdown"),
        "missing_shutdown_export": source.replace("initialize, processToolCall, shutdown", "initialize, processToolCall"),
        "reordered_exports": source.replace("initialize, processToolCall, shutdown", "processToolCall, initialize, shutdown"),
        "second_processToolCall_parameter": source.replace("processToolCall(args)", "processToolCall(args, context)"),
        "arguments_access": source.replace("args.commandRef", "arguments[0].commandRef"),
        "context_alias": source.replace("const nativeFrame", "const context = args;\n  const nativeFrame"),
        "object_spread": source.replace("commandRef: args.commandRef,", "...args,"),
        "computed_property": source.replace("commandRef: args.commandRef", "[commandRef]: args.commandRef"),
        "helper_call": source.replace("args.payload", "sanitize(args.payload)"),
        "extra_native_argument": source.replace("execute_command(nativeFrame)", "execute_command(nativeFrame, args)"),
        "runtime_start_in_initialize": source.replace("return { initialized: false };", "startRuntime(); return { initialized: false };"),
        "forwarded_initialize_input": source.replace("initialized: false", "initialized: config"),
        "extra_export": source.replace("initialize, processToolCall, shutdown", "initialize, processToolCall, shutdown, debug"),
    }
    rows = [{"case": "exact_inherited_ABI_wrapper", "expected": "ACCEPT", "passed": ast_accepts(source)}]
    rows.extend({"case": name, "expected": "BLOCK", "passed": not ast_accepts(value)} for name, value in variants.items())
    return rows, [row["case"] for row in rows if not row["passed"]]


def sqlite_cases(sql: str, triggers: str, witness: dict) -> tuple[list[dict], list[str]]:
    r5 = load_module("phase5a_r5_helpers_for_r6", R5_VALIDATOR)
    rows = []; failures = []
    def record(name: str, expected: str, passed: bool):
        rows.append({"case": name, "expected": expected, "passed": bool(passed)})
        if not passed: failures.append(name)

    decoded = witness["f3_witness_commit"]["decoded"]
    c = new_db(sql, triggers); r5.seed_resident(c); r5.add_incarnation_epoch(c, 1, "inc:1", 1); insert_exact_witness(r5, c, decoded); c.commit()
    record("F3_exact_witness_bytes_tuple_RECOVERING_to_READY", "ACCEPT", commit_ready(r5, c, "resident:A")); c.close()

    c = new_db(sql, triggers); r5.seed_resident(c); r5.add_incarnation_epoch(c, 1, "inc:1", 1); insert_exact_witness(r5, c, decoded, fingerprint="f"*64); c.commit()
    record("F3_witness_bad_digest", "REJECT", not witness_tuple(c, "resident:A")[0]); c.close()

    bad = dict(decoded); bad["witness_reservation_fingerprint"] = "b"*64
    c = new_db(sql, triggers); r5.seed_resident(c); r5.add_incarnation_epoch(c, 1, "inc:1", 1); insert_exact_witness(r5, c, bad); c.commit()
    record("F3_witness_tuple_substitution", "REJECT", not witness_tuple(c, "resident:A")[0]); c.close()

    raw = canonical(decoded)[:-1] + b',"resident_id":"resident:A"}'
    c = new_db(sql, triggers); r5.seed_resident(c); r5.add_incarnation_epoch(c, 1, "inc:1", 1); insert_exact_witness(r5, c, decoded, raw=raw); c.commit()
    record("F3_witness_duplicate_key", "REJECT", not witness_tuple(c, "resident:A")[0]); c.close()

    c = new_db(sql, triggers); x = r5.seed_f5(c, "A", 10); insert_arm(c, x); c.commit(); first, before = replay_snapshot(c, x["arm"]); second, after = replay_snapshot(c, x["arm"])
    record("F5_exact_subject_bound_first_apply", "ACCEPT", first[8:] == (x["attempt"], 1))
    record("F5_exact_replay_zero_additions", "ACCEPT", first == second and before == after); c.close()

    c = new_db(sql, triggers); x = r5.seed_f5(c, "B", 20)
    record("F5_authorization_subject_ref_substitution", "REJECT", expect_integrity_error(lambda: (insert_arm(c, x, subject_ref="attempt:DIFFERENT"), c.commit()))); c.close()
    c = new_db(sql, triggers); x = r5.seed_f5(c, "C", 30)
    record("F5_authorization_subject_revision_substitution", "REJECT", expect_integrity_error(lambda: (insert_arm(c, x, subject_revision=7), c.commit()))); c.close()
    c = new_db(sql, triggers); x = r5.seed_f5(c, "D", 40); insert_arm(c, x); c.commit(); stored, _ = replay_snapshot(c, x["arm"])
    substituted = stored[:8] + ("attempt:DIFFERENT", 7)
    record("F5_replay_identity_substitution", "REJECT", substituted != stored); c.close()

    c = new_db(sql, triggers); r5.event(c, 1, "event:immut", "TEST", "logical:A", 1, "1"*64); r5.fact(c, "TEST_FACT", "logical:A", 1, "fact:A", "subject:A", 1, "2"*64, 1)
    c.execute("INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)", ("TEST_FACT", "logical:A", 1, "fact:A", "2"*64, 1, 1)); c.commit()
    record("canonical_fact_same_revision_update", "REJECT", expect_integrity_error(lambda: c.execute("UPDATE canonical_fact SET subject_ref='subject:B' WHERE fact_kind='TEST_FACT'")))
    c.rollback(); c.execute("BEGIN IMMEDIATE")
    coordinated = expect_integrity_error(lambda: (c.execute("UPDATE canonical_fact SET fact_ref='fact:B' WHERE fact_kind='TEST_FACT'"), c.execute("UPDATE current_fact_pointer SET current_fact_ref='fact:B' WHERE fact_kind='TEST_FACT'"), c.commit()))
    c.rollback(); record("canonical_fact_coordinated_pointer_update", "REJECT", coordinated)
    record("canonical_fact_delete", "REJECT", expect_integrity_error(lambda: c.execute("DELETE FROM canonical_fact WHERE fact_kind='TEST_FACT'"))); c.rollback()
    payload = b'{}'; r5.event(c, 2, "event:immut:2", "TEST", "logical:A", 2, "3"*64)
    c.execute("""INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", ("TEST_FACT","logical:A",2,"fact:B","subject:A",1,payload,"4"*64,1,"fact:A","2"*64,2)); c.commit()
    record("canonical_fact_append_revision_two", "ACCEPT", c.execute("SELECT COUNT(*) FROM canonical_fact WHERE fact_kind='TEST_FACT'").fetchone() == (2,)); c.close()
    return rows, failures


def input_cases() -> tuple[list[dict], list[str]]:
    tests = [
        ("unique_YAML", "ACCEPT", lambda: yaml.load("a: 1\nb: 2\n", Loader=StrictSafeLoader) == {"a": 1, "b": 2}),
        ("unique_JSON", "ACCEPT", lambda: loads_json_strict('{"a":1,"b":2}') == {"a": 1, "b": 2}),
        ("duplicate_YAML_schema_version", "BLOCK", lambda: yaml.load("schema_version: a\nschema_version: b\n", Loader=StrictSafeLoader)),
        ("duplicate_YAML_implementation_authorized", "BLOCK", lambda: yaml.load("implementation_authorized: false\nimplementation_authorized: true\n", Loader=StrictSafeLoader)),
        ("duplicate_JSON_schema_version", "BLOCK", lambda: loads_json_strict('{"schema_version":"a","schema_version":"b"}')),
        ("duplicate_JSON_nested_authorization", "BLOCK", lambda: loads_json_strict('{"x":{"authorized":false,"authorized":true}}')),
        ("JSON_NaN", "BLOCK", lambda: loads_json_strict('{"value":NaN}')),
    ]
    rows=[]; failures=[]
    for name, expected, fn in tests:
        if expected == "ACCEPT":
            try: passed = bool(fn())
            except Exception: passed = False
        else:
            try: fn(); passed = False
            except (DuplicateKeyError, ValueError, yaml.YAMLError, json.JSONDecodeError): passed = True
        rows.append({"case": name, "expected": expected, "passed": passed})
        if not passed: failures.append(name)
    return rows, failures


def boundary_errors(owner: dict, persistence: dict, abi: dict, totality: dict, witness: dict) -> list[str]:
    errors=[]
    checks = [
        ("owner.runtime_usable", owner.get("runtime_usable")), ("owner.implementation_authorized", owner.get("implementation_authorized")),
        ("persistence.runtime_usable", persistence.get("runtime_usable")), ("persistence.implementation_authorized", persistence.get("implementation_authorized")),
        ("abi.runtime_usable", abi.get("runtime_usable")), ("abi.implementation_authorized", abi.get("implementation_authorized")),
        ("abi.VCPToolBox_modified", abi.get("governance",{}).get("VCPToolBox_modified")), ("abi.JavaScript_implementation_created", abi.get("governance",{}).get("JavaScript_implementation_created")),
        ("abi.plugin_enabled", abi.get("governance",{}).get("plugin_enabled")),
        ("totality.runtime_usable", totality.get("runtime_usable")), ("totality.implementation_authorized", totality.get("implementation_authorized")),
        ("persistence.database_file_created", persistence.get("governance",{}).get("database_file_created")),
        ("totality.database_file_created", totality.get("governance",{}).get("database_file_created")), ("totality.VCPToolBox_modified", totality.get("governance",{}).get("VCPToolBox_modified")),
        ("totality.plugin_enabled", totality.get("governance",{}).get("plugin_enabled")), ("totality.provider_called", totality.get("governance",{}).get("provider_called")),
        ("totality.private_Memory_read", totality.get("governance",{}).get("private_Memory_read")), ("totality.sensing_started", totality.get("governance",{}).get("sensing_started")),
    ]
    for name, value in checks:
        if type(value) is not bool or value is not False: errors.append(name)
    for name, value in witness.get("boundary",{}).items():
        if name == "real_effect_occurrence_count":
            if type(value) is not int or value != 0: errors.append(f"witness.{name}")
        elif name == "terminal_outcome":
            if value != "NOT_EXECUTED": errors.append(f"witness.{name}")
        elif type(value) is not bool or value is not False: errors.append(f"witness.{name}")
    if totality.get("governance",{}).get("real_effect_occurrence_count") != 0: errors.append("totality.real_effect_occurrence_count")
    return errors


def validate(owner: dict, persistence: dict, abi: dict, totality: dict, witness: dict, source: bytes) -> tuple[list[str], dict]:
    errors=[]
    for rel, expected in FIXED_HASHES.items():
        if sha(ROOT / rel) != expected: errors.append(f"fixed hash mismatch: {rel}")
    builder = load_module("phase5a_r6_builder_for_validator", R6_BUILDER)
    if witness != builder.build(): errors.append("witness not byte-derived builder object")
    if owner.get("profile_id") != "PHASE_5A_M0A_SEMANTIC_OWNER_CORRECTIONS_R6": errors.append("owner profile")
    if [row.get("obligation_id") for row in owner.get("replacement_rows",[])] != ["F3_incarnation_and_authority_epoch","F5_stored_first_Event_and_call_accounting","external_materialization"]: errors.append("owner inventory")
    if persistence.get("effective_schema",{}).get("replace_R5_or_inherited_tables") != ["canonical_fact","dispatch_arm"]: errors.append("replacement tables")
    if abi.get("effective_ABI_replacement",{}).get("exact_exports_in_order") != ["initialize","processToolCall","shutdown"]: errors.append("ABI exports")
    if abi.get("effective_ABI_replacement",{}).get("processToolCall",{}).get("native_method") != "execute_command": errors.append("ABI native method")
    if sha_bytes(source) != abi.get("fixed_future_wrapper",{}).get("sha256"): errors.append("source SHA")
    if not ast_accepts(source.decode("utf-8")): errors.append("source AST")
    errors.extend(boundary_errors(owner,persistence,abi,totality,witness))
    try:
        order, sql, triggers = effective_sql(persistence)
        c = new_db(sql,triggers); c.close()
    except (sqlite3.Error, KeyError, ValueError) as exc:
        errors.append(f"effective DDL: {exc}"); order=[]; sql=""; triggers=""
    sql_rows=[]; sql_fail=["DDL"] if not sql else []
    if sql:
        sql_rows, sql_fail = sqlite_cases(sql,triggers,witness)
        errors.extend(f"SQLite case: {name}" for name in sql_fail)
    source_rows, source_fail = source_cases(source.decode("utf-8")); errors.extend(f"source case: {name}" for name in source_fail)
    input_rows, input_fail = input_cases(); errors.extend(f"input case: {name}" for name in input_fail)
    evidence = {"effective_tables": len(order), "sqlite_cases": sql_rows, "source_cases": source_rows, "input_cases": input_rows}
    return errors, evidence


def self_test(owner: dict, persistence: dict, abi: dict, totality: dict, witness: dict, source: bytes) -> tuple[int,list[str]]:
    failures=[]; count=0
    mutations=[]
    for profile_name, path in [("owner",["runtime_usable"]),("persistence",["implementation_authorized"]),("abi",["runtime_usable"]),("totality",["implementation_authorized"])]:
        mutations.append((profile_name,path,True))
    mutations.extend([("abi",["governance","VCPToolBox_modified"],True),("abi",["governance","JavaScript_implementation_created"],True),("totality",["governance","provider_called"],True),("witness",["boundary","real_effect_occurrence_count"],1)])
    originals={"owner":owner,"persistence":persistence,"abi":abi,"totality":totality,"witness":witness}
    for name,path,value in mutations:
        copies={key:copy.deepcopy(item) for key,item in originals.items()}; target=copies[name]
        for key in path[:-1]: target=target[key]
        target[path[-1]]=value; count+=1
        if not boundary_errors(copies["owner"],copies["persistence"],copies["abi"],copies["totality"],copies["witness"]): failures.append(f"boundary:{name}:{'.'.join(path)}")
    count += 1
    if ast_accepts(source.decode().replace("execute_command","process")): failures.append("sixth native method")
    count += 2
    try: yaml.load("a: 1\na: 2\n", Loader=StrictSafeLoader); failures.append("duplicate YAML")
    except DuplicateKeyError: pass
    try: loads_json_strict('{"a":1,"a":2}'); failures.append("duplicate JSON")
    except DuplicateKeyError: pass
    return count, failures


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("witness"); parser.add_argument("source"); parser.add_argument("--self-test",action="store_true"); args=parser.parse_args()
    try:
        owner=load_yaml_strict(R6_OWNER); persistence=load_yaml_strict(R6_PERSIST); abi=load_yaml_strict(R6_ABI); totality=load_yaml_strict(R6_TOTALITY)
        witness=loads_json_strict(Path(args.witness).read_bytes()); source=Path(args.source).read_bytes()
        errors,evidence=validate(owner,persistence,abi,totality,witness,source)
        mutations=0; mutation_failures=[]
        if args.self_test: mutations,mutation_failures=self_test(owner,persistence,abi,totality,witness,source); errors.extend(f"self-test: {x}" for x in mutation_failures)
        output={"result":"PASS_NO_BLOCKER" if not errors else "BLOCK","errors":errors,"effective_tables":f"{evidence['effective_tables']}/18","SQLite_cases":f"{sum(r['passed'] for r in evidence['sqlite_cases'])}/{len(evidence['sqlite_cases'])}","JavaScript_AST_cases":f"{sum(r['passed'] for r in evidence['source_cases'])}/{len(evidence['source_cases'])}","structured_input_cases":f"{sum(r['passed'] for r in evidence['input_cases'])}/{len(evidence['input_cases'])}","fixed_case_count":len(evidence['sqlite_cases'])+len(evidence['source_cases'])+len(evidence['input_cases']),"self_test_mutations":mutations,"self_test_failures":mutation_failures,"database_file_occurrence_count":0,"terminal_outcome":"NOT_EXECUTED"}
        print(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2)); return 0 if not errors else 1
    except Exception as exc:
        print(json.dumps({"result":"BLOCK","errors":[f"stable malformed-input block: {type(exc).__name__}: {exc}"],"terminal_outcome":"NOT_EXECUTED"},sort_keys=True)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
