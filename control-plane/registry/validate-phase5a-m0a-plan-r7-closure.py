#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
R6_VALIDATOR = ROOT / "control-plane/registry/validate-phase5a-m0a-plan-r6-closure.py"
R6_PERSISTENCE = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r6.yaml"
R7_OWNER = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r7.yaml"
R7_PERSISTENCE = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r7.yaml"
R6_ABI = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r6.yaml"
R6_TOTALITY = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-structured-input-totality-corrections-v0.1-r6.yaml"
R7_BOUNDARY = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-boundary-inventory-v0.1-r7.yaml"
R7_BUILDER = ROOT / "control-plane/registry/build-phase5a-m0a-plan-r7-closure-witness.py"

FIXED_HASHES = {
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml": "d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml": "0803bd3e90a0652f1e0cc97b9a4168185df37cd9c76506746796e6096d3dbe58",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r5-atomic-independent-review-package-v0.1.manifest.yaml": "e26d5e1fa35a6bb69ae26747580e066d58eed5ab9a55371ecce35a991c337fa3",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r6-atomic-independent-review-package-v0.1.manifest.yaml": "98a6f73bf96fdbd168169173c42a9a57eafe81151d27b88820534467dc4a2167",
    "control-plane/registry/reviews/2026-07-20-yellow-agents-os-phase-5a-m0a-plan-r6-full-atomic-independent-review.yaml": "6b6d890d8656e920b564d192eb0fc508c4ecdc2ab6449cec3aa5efa662ea3336",
    "control-plane/registry/reviews/2026-07-20-yellow-agents-os-phase-5a-m0a-plan-r6-finding-disposition-v0.1.yaml": "f0354a9466e098c3c55173c43c68047c427bd5d92eb89486d78f8c72cf49fafd",
    "control-plane/registry/decisions/2026-07-20-agents-os-phase-5a-m0a-plan-r7-narrow-closure-start-decision-v0.1.yaml": "2a2865da0c59b3713719e05ee856a5bbf863f3714fced4ee96496602d197e7e9",
}

EXPECTED_SOURCE_ALIASES = [
    "semantic_owner_R7",
    "persistence_R7",
    "materialization_ABI_R6",
    "structured_input_totality_R6",
    "boundary_inventory_R7",
    "witness_boundary_R7",
]
STRICT_FALSE_KEYS = [
    "runtime_usable", "implementation_authorized", "database_file_created",
    "VCPToolBox_modified", "JavaScript_implementation_created", "plugin_enabled",
    "provider_called", "private_Memory_read", "sensing_started",
    "creates_new_semantic_authority", "recomputes_F3_or_F5_authority",
    "inputs_forwarded", "may_start_runtime", "initialized", "plan_frozen",
    "dependency_installation_authorized", "production_authentication_authorized",
]
STRICT_TRUE_KEYS = ["actual_Plugin_js_owner_remains_R4_hash_bound"]
STRICT_ZERO_KEYS = ["real_effect_occurrence_count"]
EXACT_STRING_VALUES = {"terminal_outcome": "NOT_EXECUTED"}
EXPECTED_BOUNDARY_INVENTORY_SHA256 = "f99df49b82052bd1a515599b5b8e86f45d0428367b100308fa9c7c718c9ff09c"
BOUNDARY_SUFFIXES = (
    "_authorized", "_usable", "_modified", "_created", "_enabled", "_called",
    "_read", "_started", "_allowed", "_permission", "_authority",
)


class DuplicateKeyError(ValueError):
    pass


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise DuplicateKeyError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)


def pairs_no_duplicate(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs_no_duplicate,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def boundary_seed() -> dict:
    return {
        "plan_frozen": False,
        "runtime_usable": False,
        "implementation_authorized": False,
        "dependency_installation_authorized": False,
        "database_file_created": False,
        "VCPToolBox_modified": False,
        "JavaScript_implementation_created": False,
        "plugin_enabled": False,
        "production_authentication_authorized": False,
        "provider_called": False,
        "private_Memory_read": False,
        "sensing_started": False,
        "real_effect_occurrence_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }


def source_documents(owner: dict, persistence: dict, abi: dict, totality: dict, boundary: dict, witness_boundary: dict):
    return [
        ("semantic_owner_R7", owner),
        ("persistence_R7", persistence),
        ("materialization_ABI_R6", abi),
        ("structured_input_totality_R6", totality),
        ("boundary_inventory_R7", boundary),
        ("witness_boundary_R7", witness_boundary),
    ]


def unknown_boundary_paths(builder, sources: list[tuple[str, dict]]) -> list[str]:
    classified = set(STRICT_FALSE_KEYS + STRICT_TRUE_KEYS + STRICT_ZERO_KEYS + list(EXACT_STRING_VALUES))
    errors = []
    for alias, document in sources:
        for pointer, key, _value in builder.walk(document):
            if key in classified:
                continue
            if key.endswith(BOUNDARY_SUFFIXES) or key.endswith("_occurrence_count") or key == "terminal_outcome":
                errors.append(f"{alias}{pointer}")
    return errors


def boundary_errors(builder, owner: dict, persistence: dict, abi: dict, totality: dict, boundary: dict, witness: dict) -> tuple[list[str], list[dict]]:
    errors = []
    contract = boundary.get("closed_key_contract", {})
    expected_contract = {
        "strict_false_boolean_keys": STRICT_FALSE_KEYS,
        "strict_true_boolean_keys": STRICT_TRUE_KEYS,
        "strict_zero_integer_keys": STRICT_ZERO_KEYS,
        "exact_string_values": EXACT_STRING_VALUES,
    }
    if boundary.get("source_aliases_in_order") != EXPECTED_SOURCE_ALIASES:
        errors.append("boundary source aliases")
    if contract != expected_contract:
        errors.append("closed boundary key contract")
    if boundary.get("derivation", {}).get("expected_inventory_sha256") != EXPECTED_BOUNDARY_INVENTORY_SHA256:
        errors.append("profile boundary inventory digest")
    observed_boundary = witness.get("boundary")
    if not isinstance(observed_boundary, dict):
        errors.append("witness boundary object")
        observed_boundary = {}
    sources = source_documents(owner, persistence, abi, totality, boundary, observed_boundary)
    errors.extend(f"unknown boundary key: {path}" for path in unknown_boundary_paths(builder, sources))
    rows = builder.collect_boundary_rows(sources, contract if contract == expected_contract else expected_contract)
    commitments = [{key: row[key] for key in ("source", "pointer", "key", "expected_type", "expected_value")} for row in rows]
    digest = sha_bytes(canonical(commitments))
    if digest != EXPECTED_BOUNDARY_INVENTORY_SHA256:
        errors.append("derived boundary inventory digest")
    if witness.get("boundary_inventory") != {
        "row_count": len(rows), "rows": commitments, "inventory_sha256": digest
    }:
        errors.append("witness boundary inventory")
    for row in rows:
        value = row["observed_value"]
        expected = row["expected_value"]
        if row["expected_type"] == "boolean":
            valid = type(value) is bool and value is expected
        elif row["expected_type"] == "integer":
            valid = type(value) is int and value == expected
        else:
            valid = type(value) is str and value == expected
        if not valid:
            errors.append(f"boundary value: {row['source']}{row['pointer']}")
    if observed_boundary != boundary_seed():
        errors.append("witness boundary exact seed")
    return errors, commitments


def setup_sqlite(r6, r5):
    r6_persistence = load_yaml(R6_PERSISTENCE)
    order, sql, triggers = r6.effective_sql(r6_persistence)
    if len(order) != 18:
        raise ValueError("effective table count")
    return r6.new_db(sql, triggers)


def insert_recovering(r5, connection: sqlite3.Connection, canonical_form: bool = True, with_pointer: bool = True):
    value = {"authority_epoch": 1, "lifecycle": "RECOVERING", "resident_id": "resident:A"}
    raw = canonical(value)
    if not canonical_form:
        raw = b'{"authority_epoch": 1, "lifecycle":"RECOVERING","resident_id":"resident:A"}'
    fingerprint = sha_bytes(raw)
    r5.event(connection, 2, "event:f3-recovering:resident:A:1", "RESIDENT_RECOVERING", "resident:A", 1, f"{2:064x}")
    connection.execute(
        """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,created_event_sequence)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        ("RESIDENT_LIFECYCLE", "resident:A", 1, "resident-lifecycle:resident:A:1", "resident:A", 1, raw, fingerprint, 2),
    )
    if with_pointer:
        connection.execute("INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)",
                           ("RESIDENT_LIFECYCLE", "resident:A", 1, "resident-lifecycle:resident:A:1", fingerprint, 1, 2))
    return raw, fingerprint


def insert_witness(r5, connection: sqlite3.Connection):
    decoded = {
        "authority_epoch": 1,
        "epoch_fingerprint": f"{201:064x}",
        "incarnation_id": "inc:1",
        "ownership_event_fingerprint": f"{1:064x}",
        "ownership_event_id": "event:f3-ownership:resident:A:1",
        "ownership_event_sequence": 1,
        "resident_id": "resident:A",
        "witness_reservation_fingerprint": f"{301:064x}",
        "witness_reservation_ref": "reservation:1",
    }
    raw = canonical(decoded)
    fingerprint = sha_bytes(raw)
    r5.event(connection, 3, "event:f3-witness:resident:A:1", "F3_WITNESS_COMMITTED", "resident:A", 1, f"{3:064x}")
    connection.execute(
        """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,created_event_sequence)
        VALUES(?,?,?,?,?,?,?,?,?)""",
        ("F3_WITNESS_COMMIT", "resident:A", 1, "witness-commit:reservation:1", "reservation:1", 1, raw, fingerprint, 3),
    )
    connection.execute("INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)",
                       ("F3_WITNESS_COMMIT", "resident:A", 1, "witness-commit:reservation:1", fingerprint, 1, 3))


def seed_transition_prestate(r6, r5, canonical_recovering: bool = True, with_pointer: bool = True):
    connection = setup_sqlite(r6, r5)
    r5.seed_resident(connection)
    r5.add_incarnation_epoch(connection, 1, "inc:1", 1)
    raw, fingerprint = insert_recovering(r5, connection, canonical_recovering, with_pointer)
    insert_witness(r5, connection)
    connection.commit()
    return connection, raw, fingerprint


def lifecycle_current(connection: sqlite3.Connection):
    return connection.execute(
        """SELECT f.fact_revision,f.fact_ref,f.canonical_bytes,f.fact_fingerprint,
        f.predecessor_fact_revision,f.predecessor_fact_ref,f.predecessor_fact_fingerprint
        FROM current_fact_pointer p JOIN canonical_fact f
        ON (p.fact_kind,p.logical_id,p.current_fact_revision,p.current_fact_ref,p.current_fact_fingerprint)
         = (f.fact_kind,f.logical_id,f.fact_revision,f.fact_ref,f.fact_fingerprint)
        WHERE p.fact_kind='RESIDENT_LIFECYCLE' AND p.logical_id='resident:A'"""
    ).fetchone()


def valid_recovering(connection: sqlite3.Connection, row) -> bool:
    if not row or row[0] != 1 or row[1] != "resident-lifecycle:resident:A:1":
        return False
    expected = {"authority_epoch": 1, "lifecycle": "RECOVERING", "resident_id": "resident:A"}
    try:
        decoded = json.loads(row[2].decode("utf-8"), object_pairs_hook=pairs_no_duplicate,
                             parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return decoded == expected and canonical(decoded) == row[2] and sha_bytes(row[2]) == row[3] and row[4:] == (None, None, None)


def commit_ready(r6, r5, connection: sqlite3.Connection) -> bool:
    if not r6.witness_tuple(connection, "resident:A")[0] or not valid_recovering(connection, lifecycle_current(connection)):
        return False
    try:
        connection.execute("BEGIN IMMEDIATE")
        if not r6.witness_tuple(connection, "resident:A")[0]:
            connection.rollback(); return False
        prior = lifecycle_current(connection)
        if not valid_recovering(connection, prior):
            connection.rollback(); return False
        ready = {"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"}
        raw = canonical(ready); fingerprint = sha_bytes(raw)
        r5.event(connection, 4, "event:f3-ready:resident:A:1", "RESIDENT_READY", "resident:A", 2, f"{4:064x}")
        connection.execute(
            """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,
            predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("RESIDENT_LIFECYCLE", "resident:A", 2, "resident-lifecycle:resident:A:2", "resident:A", 1,
             raw, fingerprint, 1, prior[1], prior[3], 4),
        )
        cursor = connection.execute(
            """UPDATE current_fact_pointer SET current_fact_revision=2,current_fact_ref=?,current_fact_fingerprint=?,
            pointer_version=pointer_version+1,updated_event_sequence=4
            WHERE fact_kind='RESIDENT_LIFECYCLE' AND logical_id='resident:A'
              AND current_fact_revision=1 AND current_fact_ref=? AND current_fact_fingerprint=?""",
            ("resident-lifecycle:resident:A:2", fingerprint, prior[1], prior[3]),
        )
        if cursor.rowcount != 1:
            connection.rollback(); return False
        connection.commit()
    except sqlite3.Error:
        connection.rollback(); return False
    row = lifecycle_current(connection)
    return bool(row and row[0] == 2 and row[1] == "resident-lifecycle:resident:A:2" and row[4:] == (1, prior[1], prior[3]))


def sqlite_cases(r6, r5) -> tuple[list[dict], list[str]]:
    rows = []
    failures = []
    def record(name: str, expected: str, passed: bool):
        rows.append({"case": name, "expected": expected, "passed": bool(passed)})
        if not passed:
            failures.append(name)

    c, _raw, prior_fp = seed_transition_prestate(r6, r5)
    record("F3_exact_RECOVERING_revision_1_to_READY_revision_2", "ACCEPT", commit_ready(r6, r5, c))
    current = lifecycle_current(c)
    record("F3_READY_revision_2_exact_predecessor", "ACCEPT", current is not None and current[4:] == (1, "resident-lifecycle:resident:A:1", prior_fp))
    pointer = c.execute("SELECT current_fact_revision,pointer_version FROM current_fact_pointer WHERE fact_kind='RESIDENT_LIFECYCLE'").fetchone()
    record("F3_current_pointer_advances_1_to_2", "ACCEPT", pointer == (2, 2)); c.close()

    c = setup_sqlite(r6, r5); r5.seed_resident(c); r5.add_incarnation_epoch(c, 1, "inc:1", 1); insert_witness(r5, c); c.commit()
    before = c.total_changes
    record("F3_direct_READY_revision_1_from_empty_history", "BLOCK", not commit_ready(r6, r5, c) and c.total_changes == before); c.close()

    c, _raw, _fp = seed_transition_prestate(r6, r5, with_pointer=False)
    record("F3_stale_lifecycle_pointer", "BLOCK", not commit_ready(r6, r5, c)); c.close()

    c, _raw, _fp = seed_transition_prestate(r6, r5, canonical_recovering=False)
    record("F3_RECOVERING_noncanonical_bytes", "BLOCK", not commit_ready(r6, r5, c)); c.close()

    c, _raw, prior_fp = seed_transition_prestate(r6, r5)
    try:
        c.execute("BEGIN IMMEDIATE")
        r5.event(c, 4, "event:f3-ready:wrong", "RESIDENT_READY", "resident:A", 2, f"{4:064x}")
        c.execute(
            """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,
            predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("RESIDENT_LIFECYCLE", "resident:A", 2, "resident-lifecycle:resident:A:2", "resident:A", 1,
             canonical({"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"}), "f" * 64,
             1, "resident-lifecycle:WRONG", prior_fp, 4),
        )
        c.commit(); rejected = False
    except sqlite3.IntegrityError:
        c.rollback(); rejected = True
    record("F3_wrong_predecessor_tuple", "BLOCK", rejected); c.close()

    c, _raw, _fp = seed_transition_prestate(r6, r5); commit_ready(r6, r5, c)
    try:
        c.execute("""INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,
                  predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence)
                  SELECT fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,
                  predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence
                  FROM canonical_fact WHERE fact_kind='RESIDENT_LIFECYCLE' AND fact_revision=2""")
        c.commit(); rejected = False
    except sqlite3.IntegrityError:
        c.rollback(); rejected = True
    record("F3_duplicate_READY_revision_2", "BLOCK", rejected); c.close()

    c, _raw, prior_fp = seed_transition_prestate(r6, r5)
    try:
        c.execute("BEGIN IMMEDIATE")
        ready_raw = canonical({"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"})
        ready_fp = sha_bytes(ready_raw)
        r5.event(c, 4, "event:f3-ready:resident:A:1", "RESIDENT_READY", "resident:A", 2, f"{4:064x}")
        c.execute("""INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,fact_fingerprint,
                  predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,created_event_sequence)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                  ("RESIDENT_LIFECYCLE", "resident:A", 2, "resident-lifecycle:resident:A:2", "resident:A", 1,
                   ready_raw, ready_fp, 1, "resident-lifecycle:resident:A:1", prior_fp, 4))
        c.execute("UPDATE current_fact_pointer SET current_fact_revision=2,current_fact_ref=?,current_fact_fingerprint=?,pointer_version=2,updated_event_sequence=4 WHERE fact_kind='RESIDENT_LIFECYCLE'",
                  ("resident-lifecycle:resident:A:2", ready_fp))
        raise RuntimeError("synthetic crash before commit")
    except RuntimeError:
        c.rollback()
    preserved = lifecycle_current(c)
    counts = (c.execute("SELECT COUNT(*) FROM event WHERE event_id='event:f3-ready:resident:A:1'").fetchone()[0],
              c.execute("SELECT COUNT(*) FROM canonical_fact WHERE fact_kind='RESIDENT_LIFECYCLE' AND fact_revision=2").fetchone()[0])
    record("F3_Event_fact_pointer_rollback_all_or_zero", "BLOCK", preserved is not None and preserved[0] == 1 and counts == (0, 0)); c.close()
    return rows, failures


def set_pointer(document: object, pointer: str, value: object):
    tokens = pointer.split("/")[1:]
    target = document
    for token in tokens[:-1]:
        token = token.replace("~1", "/").replace("~0", "~")
        target = target[int(token)] if isinstance(target, list) else target[token]
    final = tokens[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(target, list):
        target[int(final)] = value
    else:
        target[final] = value


def boundary_self_test(builder, owner: dict, persistence: dict, abi: dict, totality: dict, boundary: dict, witness: dict, commitments: list[dict]) -> tuple[int, list[str]]:
    failures = []
    count = 0
    base_sources = source_documents(owner, persistence, abi, totality, boundary, witness["boundary"])
    source_index = {alias: index for index, (alias, _doc) in enumerate(base_sources)}
    for row in commitments:
        copies = [(alias, copy.deepcopy(doc)) for alias, doc in base_sources]
        expected = row["expected_value"]
        replacement = (not expected) if row["expected_type"] == "boolean" else (1 if row["expected_type"] == "integer" else "EXECUTED")
        set_pointer(copies[source_index[row["source"]]][1], row["pointer"], replacement)
        derived = builder.collect_boundary_rows(copies, boundary["closed_key_contract"])
        target = next(item for item in derived if item["source"] == row["source"] and item["pointer"] == row["pointer"])
        count += 1
        valid = (type(target["observed_value"]) is bool and target["observed_value"] is target["expected_value"]) if row["expected_type"] == "boolean" else (
            type(target["observed_value"]) is int and target["observed_value"] == target["expected_value"] if row["expected_type"] == "integer" else
            type(target["observed_value"]) is str and target["observed_value"] == target["expected_value"])
        if valid:
            failures.append(f"boundary favorable mutation accepted: {row['source']}{row['pointer']}")
    extra_tests = [
        ("unknown_authorized_key", lambda docs: docs[0][1].update({"deployment_authorized": False})),
        ("false_key_integer", lambda docs: docs[0][1].update({"runtime_usable": 0})),
        ("zero_key_boolean", lambda docs: docs[5][1].update({"real_effect_occurrence_count": False})),
        ("terminal_changed", lambda docs: docs[5][1].update({"terminal_outcome": "EXECUTED"})),
        ("missing_boundary", lambda docs: docs[0][1].pop("runtime_usable")),
        ("additional_known_boundary", lambda docs: docs[0][1].update({"plugin_enabled": False})),
    ]
    for name, mutate in extra_tests:
        copies = [(alias, copy.deepcopy(doc)) for alias, doc in base_sources]
        mutate(copies); count += 1
        unknown = unknown_boundary_paths(builder, copies)
        rows = builder.collect_boundary_rows(copies, boundary["closed_key_contract"])
        row_commitments = [{key: row[key] for key in ("source", "pointer", "key", "expected_type", "expected_value")} for row in rows]
        semantics_bad = any(
            (row["expected_type"] == "boolean" and (type(row["observed_value"]) is not bool or row["observed_value"] is not row["expected_value"])) or
            (row["expected_type"] == "integer" and (type(row["observed_value"]) is not int or row["observed_value"] != row["expected_value"])) or
            (row["expected_type"] == "string" and (type(row["observed_value"]) is not str or row["observed_value"] != row["expected_value"]))
            for row in rows)
        rejected = bool(unknown or semantics_bad or sha_bytes(canonical(row_commitments)) != EXPECTED_BOUNDARY_INVENTORY_SHA256)
        if not rejected:
            failures.append(name)
    return count, failures


def validate(owner: dict, persistence: dict, abi: dict, totality: dict, boundary: dict, witness: dict):
    errors = []
    for rel, expected in FIXED_HASHES.items():
        if sha(ROOT / rel) != expected:
            errors.append(f"fixed hash mismatch: {rel}")
    if owner.get("profile_id") != "PHASE_5A_M0A_SEMANTIC_OWNER_CORRECTIONS_R7":
        errors.append("R7 owner profile")
    if [row.get("obligation_id") for row in owner.get("replacement_rows", [])] != ["F3_incarnation_and_authority_epoch"]:
        errors.append("R7 owner replacement inventory")
    if persistence.get("profile_id") != "PHASE_5A_M0A_PERSISTENCE_TRANSACTION_CORRECTIONS_R7":
        errors.append("R7 persistence profile")
    if persistence.get("effective_schema", {}).get("effective_table_count") != 18 or persistence.get("effective_schema", {}).get("added_tables") != []:
        errors.append("R7 table inventory")
    builder = load_module("phase5a_r7_builder_for_validator", R7_BUILDER)
    if witness != builder.build():
        errors.append("witness not exact builder object")
    boundary_result, commitments = boundary_errors(builder, owner, persistence, abi, totality, boundary, witness)
    errors.extend(boundary_result)
    r6 = load_module("phase5a_r6_for_r7", R6_VALIDATOR)
    r5 = load_module("phase5a_r5_for_r7", r6.R5_VALIDATOR)
    sql_rows, sql_failures = sqlite_cases(r6, r5)
    errors.extend(f"SQLite case: {name}" for name in sql_failures)
    return errors, commitments, sql_rows, builder


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("witness")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        owner = load_yaml(R7_OWNER); persistence = load_yaml(R7_PERSISTENCE)
        abi = load_yaml(R6_ABI); totality = load_yaml(R6_TOTALITY); boundary = load_yaml(R7_BOUNDARY)
        witness = load_json(Path(args.witness))
        errors, commitments, sql_rows, builder = validate(owner, persistence, abi, totality, boundary, witness)
        mutation_count = 0; mutation_failures = []
        if args.self_test:
            mutation_count, mutation_failures = boundary_self_test(builder, owner, persistence, abi, totality, boundary, witness, commitments)
            errors.extend(f"self-test: {item}" for item in mutation_failures)
        output = {
            "result": "PASS_NO_BLOCKER" if not errors else "BLOCK",
            "errors": errors,
            "boundary_inventory_rows": f"{len(commitments)}/{len(commitments)}",
            "boundary_inventory_sha256": EXPECTED_BOUNDARY_INVENTORY_SHA256,
            "SQLite_cases": f"{sum(row['passed'] for row in sql_rows)}/{len(sql_rows)}",
            "fixed_case_count": len(commitments) + 6 + len(sql_rows),
            "self_test_mutations": mutation_count,
            "self_test_failures": mutation_failures,
            "effective_tables": "18/18",
            "database_file_occurrence_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not errors else 1
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "errors": [f"stable malformed-input block: {type(exc).__name__}: {exc}"], "terminal_outcome": "NOT_EXECUTED"}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
