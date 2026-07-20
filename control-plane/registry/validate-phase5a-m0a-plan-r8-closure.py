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
R7_VALIDATOR = ROOT / "control-plane/registry/validate-phase5a-m0a-plan-r7-closure.py"
R7_OWNER = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r7.yaml"
R8_PERSISTENCE = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-persistence-ownership-event-closure-v0.1-r8.yaml"
R6_ABI = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r6.yaml"
R6_TOTALITY = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-structured-input-totality-corrections-v0.1-r6.yaml"
R8_CONTRACT = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-closed-key-contract-v0.1-r8.yaml"
R8_BUILDER = ROOT / "control-plane/registry/build-phase5a-m0a-plan-r8-closure-witness.py"

EXPECTED_SOURCE_ALIASES = [
    "semantic_owner_R7", "persistence_ownership_R8", "materialization_ABI_R6",
    "structured_input_totality_R6", "boundary_contract_R8", "witness_boundary_R8",
]
EXPECTED_SEALED_HASHES = {
    "semantic_owner_R7": "52fd5aad32d2ce7a31a918101191e03a6d2f9e5a93cac1581bb52ff0e11cf7a9",
    "persistence_ownership_R8": "9a2eef546f4e73981dd0229a840f178b9a810640a40ab0fc415084dba3116146",
    "materialization_ABI_R6": "5032f8963a386d0312f69e5a210dfc1723d16f61d6c8ecd2ce96200ef7e15b0e",
    "structured_input_totality_R6": "14d52344c0adedbc9cc5209bf6d531d2ff2e70c49021b16134eaeb2b8a3f0660",
}
EXPECTED_KEY_ROW_COUNT = 232
EXPECTED_KEY_INVENTORY_SHA256 = "b0e6e94a83b9ad13917abf2e9dacb8397735e89ca29c642a990a9f26a03d84fb"
FIXED_HASHES = {
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-atomic-independent-review-package-v0.1.manifest.yaml": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r3-atomic-independent-review-package-v0.1.manifest.yaml": "d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r4-atomic-independent-review-package-v0.1.manifest.yaml": "0803bd3e90a0652f1e0cc97b9a4168185df37cd9c76506746796e6096d3dbe58",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r5-atomic-independent-review-package-v0.1.manifest.yaml": "e26d5e1fa35a6bb69ae26747580e066d58eed5ab9a55371ecce35a991c337fa3",
    "control-plane/registry/reports/2026-07-19-agents-os-phase-5a-m0a-plan-r6-atomic-independent-review-package-v0.1.manifest.yaml": "98a6f73bf96fdbd168169173c42a9a57eafe81151d27b88820534467dc4a2167",
    "control-plane/registry/reports/2026-07-20-agents-os-phase-5a-m0a-plan-r7-atomic-independent-review-package-v0.1.manifest.yaml": "d929a86317ecd2d9140645f1c1c8dd267cb982acfda3aa2a7830415a5917e299",
    "control-plane/registry/reviews/2026-07-20-yellow-agents-os-phase-5a-m0a-plan-r7-full-atomic-independent-review.yaml": "5daeec19f0c50e5d87df4577043b27ae447e01fe643e2aa0850ade99c104fc18",
    "control-plane/registry/reviews/2026-07-20-agents-os-phase-5a-m0a-plan-r7-codex-independent-case-results.json": "89ab92f9312a3f75c90d1d918a9b3dc2837cb31851c5e038f26bca5871dcda3b",
    "control-plane/registry/reviews/2026-07-20-yellow-agents-os-phase-5a-m0a-plan-r7-finding-disposition-v0.1.yaml": "81a8461ca44274e54e2f90e8bd636436e01c2cb5b5f1abbe5ba9faac2242e979",
    "control-plane/registry/decisions/2026-07-20-agents-os-phase-5a-m0a-plan-r8-narrow-closure-start-decision-v0.1.yaml": "73f22e8dfafe4d4ddbe42567f0485ab581b8fdcc3f4dbab7238b46be040eed77",
    "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r7.yaml": EXPECTED_SEALED_HASHES["semantic_owner_R7"],
    "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-persistence-ownership-event-closure-v0.1-r8.yaml": EXPECTED_SEALED_HASHES["persistence_ownership_R8"],
    "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r6.yaml": EXPECTED_SEALED_HASHES["materialization_ABI_R6"],
    "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-structured-input-totality-corrections-v0.1-r6.yaml": EXPECTED_SEALED_HASHES["structured_input_totality_R6"],
    "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-closed-key-contract-v0.1-r8.yaml": "b2156a4ec134a01c8f6bb0956ff8c70976425f3bb02a7569207f4a3a1c76c1b0",
    "control-plane/registry/build-phase5a-m0a-plan-r8-closure-witness.py": "5476e3bd1c12029b55e0f283a633e6f1d4564464c26c841fefb4aebd90de63f9",
}


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
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)
    if not isinstance(value, dict):
        raise ValueError(f"root mapping required: {path}")
    return value


def pairs_no_duplicate(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs_no_duplicate,
                       parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)))
    if not isinstance(value, dict):
        raise ValueError("root mapping required")
    return value


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


def expected_boundary_seed() -> dict:
    return {
        "JavaScript_implementation_created": False,
        "VCPToolBox_modified": False,
        "database_file_created": False,
        "dependency_installation_authorized": False,
        "implementation_authorized": False,
        "plan_frozen": False,
        "plugin_enabled": False,
        "private_Memory_read": False,
        "production_authentication_authorized": False,
        "provider_called": False,
        "real_effect_occurrence_count": 0,
        "runtime_usable": False,
        "sensing_started": False,
        "terminal_outcome": "NOT_EXECUTED",
    }


def source_paths() -> dict[str, Path]:
    return {
        "semantic_owner_R7": R7_OWNER,
        "persistence_ownership_R8": R8_PERSISTENCE,
        "materialization_ABI_R6": R6_ABI,
        "structured_input_totality_R6": R6_TOTALITY,
    }


def source_documents(builder, contract: dict, boundary: dict) -> list[tuple[str, dict]]:
    return [
        ("semantic_owner_R7", load_yaml(R7_OWNER)),
        ("persistence_ownership_R8", load_yaml(R8_PERSISTENCE)),
        ("materialization_ABI_R6", load_yaml(R6_ABI)),
        ("structured_input_totality_R6", load_yaml(R6_TOTALITY)),
        ("boundary_contract_R8", contract),
        ("witness_boundary_R8", boundary),
    ]


def closed_key_errors(builder, contract: dict, witness: dict) -> tuple[list[str], list[dict]]:
    errors = []
    if contract.get("profile_id") != "PHASE_5A_M0A_CLOSED_KEY_CONTRACT_R8":
        errors.append("R8 closed-key profile id")
    if contract.get("source_aliases_in_order") != EXPECTED_SOURCE_ALIASES:
        errors.append("R8 source alias inventory")
    expected_modes = {
        "semantic_owner_R7": "CONTENT_SEALED_AND_COMPLETE_KEY_PATH_INVENTORIED",
        "persistence_ownership_R8": "CONTENT_SEALED_AND_COMPLETE_KEY_PATH_INVENTORIED",
        "materialization_ABI_R6": "CONTENT_SEALED_AND_COMPLETE_KEY_PATH_INVENTORIED",
        "structured_input_totality_R6": "CONTENT_SEALED_AND_COMPLETE_KEY_PATH_INVENTORIED",
        "boundary_contract_R8": "EXACT_CLOSED_OBJECT_AND_COMPLETE_KEY_PATH_INVENTORIED",
        "witness_boundary_R8": "EXACT_CLOSED_OBJECT_AND_COMPLETE_KEY_PATH_INVENTORIED",
    }
    if contract.get("coverage_modes") != expected_modes:
        errors.append("R8 coverage modes")
    if contract.get("sealed_source_commitments") != EXPECTED_SEALED_HASHES:
        errors.append("R8 sealed source commitments")
    for alias, path in source_paths().items():
        if sha(path) != EXPECTED_SEALED_HASHES[alias]:
            errors.append(f"sealed source bytes: {alias}")
    inventory_contract = contract.get("complete_key_path_contract", {})
    if inventory_contract.get("expected_row_count") != EXPECTED_KEY_ROW_COUNT:
        errors.append("R8 expected key row count")
    if inventory_contract.get("expected_inventory_sha256") != EXPECTED_KEY_INVENTORY_SHA256:
        errors.append("R8 expected key inventory digest")
    boundary = witness.get("boundary")
    if boundary != expected_boundary_seed():
        errors.append("R8 exact witness boundary")
        boundary = expected_boundary_seed()
    sources = source_documents(builder, contract, boundary)
    if [alias for alias, _doc in sources] != EXPECTED_SOURCE_ALIASES:
        errors.append("R8 resolved source order")
    rows = builder.collect_key_rows(sources)
    digest = sha_bytes(canonical(rows))
    if len(rows) != EXPECTED_KEY_ROW_COUNT:
        errors.append("R8 derived key row count")
    if digest != EXPECTED_KEY_INVENTORY_SHA256:
        errors.append("R8 derived key inventory digest")
    if witness.get("complete_key_path_inventory") != {
        "row_count": len(rows), "rows": rows, "inventory_sha256": digest,
    }:
        errors.append("R8 witness key inventory")
    expected_profile_fingerprints = {
        alias: sha(path) for alias, path in source_paths().items()
    }
    expected_profile_fingerprints["boundary_contract_R8"] = sha(R8_CONTRACT)
    if witness.get("profile_fingerprints") != expected_profile_fingerprints:
        errors.append("R8 profile fingerprints")
    return errors, rows


def setup_sqlite(r7, r6, r5):
    return r7.setup_sqlite(r6, r5)


def ownership_event_tuple(connection: sqlite3.Connection):
    return connection.execute(
        """SELECT e.event_sequence,e.event_id,e.event_fingerprint,e.event_kind,e.aggregate_ref,e.aggregate_revision
        FROM resident_authority_epoch a JOIN event e
        ON (a.ownership_event_sequence,a.ownership_event_id,a.ownership_event_fingerprint)
         = (e.event_sequence,e.event_id,e.event_fingerprint)
        WHERE a.resident_id='resident:A' AND a.authority_epoch=1"""
    ).fetchone()


def insert_recovering(r5, connection: sqlite3.Connection, fact_sequence: int = 1,
                      pointer_sequence: int = 1, canonical_form: bool = True,
                      with_pointer: bool = True):
    if fact_sequence == 2 or pointer_sequence == 2:
        if connection.execute("SELECT COUNT(*) FROM event WHERE event_sequence=2").fetchone()[0] == 0:
            r5.event(connection, 2, "event:f3-recovering:resident:A:1", "RESIDENT_RECOVERING", "resident:A", 1, f"{2:064x}")
    value = {"authority_epoch": 1, "lifecycle": "RECOVERING", "resident_id": "resident:A"}
    raw = canonical(value)
    if not canonical_form:
        raw = b'{"authority_epoch": 1, "lifecycle":"RECOVERING","resident_id":"resident:A"}'
    fingerprint = sha_bytes(raw)
    connection.execute(
        """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,
        canonical_bytes,fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?)""",
        ("RESIDENT_LIFECYCLE", "resident:A", 1, "resident-lifecycle:resident:A:1", "resident:A", 1,
         raw, fingerprint, fact_sequence),
    )
    if with_pointer:
        connection.execute("INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)",
                           ("RESIDENT_LIFECYCLE", "resident:A", 1, "resident-lifecycle:resident:A:1",
                            fingerprint, 1, pointer_sequence))
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
    raw = canonical(decoded); fingerprint = sha_bytes(raw)
    if connection.execute("SELECT COUNT(*) FROM event WHERE event_sequence=2").fetchone()[0] == 0:
        r5.event(connection, 2, "event:f3-witness:resident:A:1", "F3_WITNESS_COMMITTED", "resident:A", 1, f"{2:064x}")
        witness_sequence = 2
    else:
        r5.event(connection, 3, "event:f3-witness:resident:A:1", "F3_WITNESS_COMMITTED", "resident:A", 1, f"{3:064x}")
        witness_sequence = 3
    connection.execute(
        """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,
        canonical_bytes,fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?)""",
        ("F3_WITNESS_COMMIT", "resident:A", 1, "witness-commit:reservation:1", "reservation:1", 1,
         raw, fingerprint, witness_sequence),
    )
    connection.execute("INSERT INTO current_fact_pointer VALUES(?,?,?,?,?,?,?)",
                       ("F3_WITNESS_COMMIT", "resident:A", 1, "witness-commit:reservation:1",
                        fingerprint, 1, witness_sequence))


def seed_transition_prestate(r7, r6, r5, fact_sequence: int = 1, pointer_sequence: int = 1,
                             canonical_recovering: bool = True, with_pointer: bool = True):
    connection = setup_sqlite(r7, r6, r5)
    r5.seed_resident(connection)
    r5.add_incarnation_epoch(connection, 1, "inc:1", 1)
    raw, fingerprint = insert_recovering(r5, connection, fact_sequence, pointer_sequence,
                                         canonical_recovering, with_pointer)
    insert_witness(r5, connection)
    connection.commit()
    return connection, raw, fingerprint


def lifecycle_current(connection: sqlite3.Connection):
    return connection.execute(
        """SELECT f.fact_revision,f.fact_ref,f.canonical_bytes,f.fact_fingerprint,
        f.predecessor_fact_revision,f.predecessor_fact_ref,f.predecessor_fact_fingerprint,
        f.created_event_sequence,p.current_fact_revision,p.current_fact_ref,p.current_fact_fingerprint,
        p.pointer_version,p.updated_event_sequence
        FROM current_fact_pointer p JOIN canonical_fact f
        ON (p.fact_kind,p.logical_id,p.current_fact_revision,p.current_fact_ref,p.current_fact_fingerprint)
         = (f.fact_kind,f.logical_id,f.fact_revision,f.fact_ref,f.fact_fingerprint)
        WHERE p.fact_kind='RESIDENT_LIFECYCLE' AND p.logical_id='resident:A'"""
    ).fetchone()


def valid_recovering(connection: sqlite3.Connection, row) -> bool:
    owner = ownership_event_tuple(connection)
    if owner != (1, "event:f3-ownership:resident:A:1", f"{1:064x}",
                 "RESIDENT_OWNERSHIP_STARTED", "resident:A", 1):
        return False
    if not row or row[0] != 1 or row[1] != "resident-lifecycle:resident:A:1":
        return False
    expected = {"authority_epoch": 1, "lifecycle": "RECOVERING", "resident_id": "resident:A"}
    try:
        decoded = json.loads(row[2].decode("utf-8"), object_pairs_hook=pairs_no_duplicate,
                             parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    return (
        decoded == expected and canonical(decoded) == row[2] and sha_bytes(row[2]) == row[3]
        and row[4:7] == (None, None, None)
        and row[7] == owner[0]
        and row[8:11] == (1, row[1], row[3])
        and row[11] == 1
        and row[12] == owner[0]
    )


def commit_ready(r7, r6, r5, connection: sqlite3.Connection) -> bool:
    prior_owner = ownership_event_tuple(connection)
    if not r6.witness_tuple(connection, "resident:A")[0] or not valid_recovering(connection, lifecycle_current(connection)):
        return False
    try:
        connection.execute("BEGIN IMMEDIATE")
        if ownership_event_tuple(connection) != prior_owner:
            connection.rollback(); return False
        if not r6.witness_tuple(connection, "resident:A")[0]:
            connection.rollback(); return False
        prior = lifecycle_current(connection)
        if not valid_recovering(connection, prior):
            connection.rollback(); return False
        ready = {"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"}
        raw = canonical(ready); fingerprint = sha_bytes(raw)
        next_sequence = connection.execute("SELECT MAX(event_sequence)+1 FROM event").fetchone()[0]
        r5.event(connection, next_sequence, "event:f3-ready:resident:A:1", "RESIDENT_READY", "resident:A", 2, f"{next_sequence:064x}")
        connection.execute(
            """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,
            canonical_bytes,fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,
            predecessor_fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("RESIDENT_LIFECYCLE", "resident:A", 2, "resident-lifecycle:resident:A:2", "resident:A", 1,
             raw, fingerprint, 1, prior[1], prior[3], next_sequence),
        )
        cursor = connection.execute(
            """UPDATE current_fact_pointer SET current_fact_revision=2,current_fact_ref=?,current_fact_fingerprint=?,
            pointer_version=pointer_version+1,updated_event_sequence=? WHERE fact_kind='RESIDENT_LIFECYCLE'
            AND logical_id='resident:A' AND current_fact_revision=1 AND current_fact_ref=?
            AND current_fact_fingerprint=? AND updated_event_sequence=?""",
            ("resident-lifecycle:resident:A:2", fingerprint, next_sequence, prior[1], prior[3], prior_owner[0]),
        )
        if cursor.rowcount != 1:
            connection.rollback(); return False
        connection.commit()
    except sqlite3.Error:
        connection.rollback(); return False
    row = lifecycle_current(connection)
    return bool(row and row[0] == 2 and row[1] == "resident-lifecycle:resident:A:2" and row[4:7] == (1, prior[1], prior[3]))


def sqlite_cases(r7, r6, r5) -> tuple[list[dict], list[str]]:
    rows = []; failures = []
    def record(name: str, expected: str, passed: bool):
        rows.append({"case": name, "expected": expected, "passed": bool(passed)})
        if not passed:
            failures.append(name)

    c, _raw, prior_fp = seed_transition_prestate(r7, r6, r5)
    record("ownership_Event_sequence_1_binds_RECOVERING_fact_and_pointer", "ACCEPT", valid_recovering(c, lifecycle_current(c)))
    record("valid_sequence_1_prestate_commits_READY_revision_2", "ACCEPT", commit_ready(r7, r6, r5, c))
    current = lifecycle_current(c)
    record("READY_revision_2_has_exact_RECOVERING_revision_1_predecessor", "ACCEPT",
           current is not None and current[4:7] == (1, "resident-lifecycle:resident:A:1", prior_fp))
    pointer = c.execute("SELECT current_fact_revision,pointer_version FROM current_fact_pointer WHERE fact_kind='RESIDENT_LIFECYCLE'").fetchone()
    record("current_pointer_advances_revision_1_to_revision_2", "ACCEPT", pointer == (2, 2)); c.close()

    for name, fact_seq, pointer_seq in [
        ("RECOVERING_fact_and_pointer_sequence_2_substitution", 2, 2),
        ("RECOVERING_fact_sequence_2_pointer_sequence_1", 2, 1),
        ("RECOVERING_fact_sequence_1_pointer_sequence_2", 1, 2),
    ]:
        c, _raw, _fp = seed_transition_prestate(r7, r6, r5, fact_seq, pointer_seq)
        record(name, "BLOCK", not valid_recovering(c, lifecycle_current(c)) and not commit_ready(r7, r6, r5, c)); c.close()

    c = setup_sqlite(r7, r6, r5); r5.seed_resident(c); r5.add_incarnation_epoch(c, 1, "inc:1", 1); insert_witness(r5, c); c.commit()
    before = c.total_changes
    record("direct_READY_revision_1_from_empty_history", "BLOCK", not commit_ready(r7, r6, r5, c) and c.total_changes == before); c.close()

    c, _raw, _fp = seed_transition_prestate(r7, r6, r5, with_pointer=False)
    record("stale_lifecycle_pointer", "BLOCK", not commit_ready(r7, r6, r5, c)); c.close()

    c, _raw, _fp = seed_transition_prestate(r7, r6, r5, canonical_recovering=False)
    record("noncanonical_RECOVERING_bytes", "BLOCK", not commit_ready(r7, r6, r5, c)); c.close()

    c, _raw, prior_fp = seed_transition_prestate(r7, r6, r5)
    try:
        c.execute("BEGIN IMMEDIATE")
        r5.event(c, 3, "event:f3-ready:wrong", "RESIDENT_READY", "resident:A", 2, f"{3:064x}")
        c.execute(
            """INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,
            canonical_bytes,fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,
            predecessor_fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("RESIDENT_LIFECYCLE", "resident:A", 2, "resident-lifecycle:resident:A:2", "resident:A", 1,
             canonical({"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"}), "f" * 64,
             1, "resident-lifecycle:WRONG", prior_fp, 3),
        )
        c.commit(); rejected = False
    except sqlite3.IntegrityError:
        c.rollback(); rejected = True
    record("wrong_predecessor_tuple", "BLOCK", rejected); c.close()

    c, _raw, _fp = seed_transition_prestate(r7, r6, r5); commit_ready(r7, r6, r5, c)
    try:
        c.execute("""INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,
                  canonical_bytes,fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,
                  predecessor_fact_fingerprint,created_event_sequence)
                  SELECT fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,canonical_bytes,
                  fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,predecessor_fact_fingerprint,
                  created_event_sequence FROM canonical_fact WHERE fact_kind='RESIDENT_LIFECYCLE' AND fact_revision=2""")
        c.commit(); rejected = False
    except sqlite3.IntegrityError:
        c.rollback(); rejected = True
    record("duplicate_READY_revision_2", "BLOCK", rejected); c.close()

    c, _raw, prior_fp = seed_transition_prestate(r7, r6, r5)
    try:
        c.execute("BEGIN IMMEDIATE")
        ready_raw = canonical({"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"})
        ready_fp = sha_bytes(ready_raw)
        r5.event(c, 3, "event:f3-ready:resident:A:1", "RESIDENT_READY", "resident:A", 2, f"{3:064x}")
        c.execute("""INSERT INTO canonical_fact(fact_kind,logical_id,fact_revision,fact_ref,subject_ref,subject_revision,
                  canonical_bytes,fact_fingerprint,predecessor_fact_revision,predecessor_fact_ref,
                  predecessor_fact_fingerprint,created_event_sequence) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                  ("RESIDENT_LIFECYCLE", "resident:A", 2, "resident-lifecycle:resident:A:2", "resident:A", 1,
                   ready_raw, ready_fp, 1, "resident-lifecycle:resident:A:1", prior_fp, 3))
        c.execute("UPDATE current_fact_pointer SET current_fact_revision=2,current_fact_ref=?,current_fact_fingerprint=?,pointer_version=2,updated_event_sequence=3 WHERE fact_kind='RESIDENT_LIFECYCLE'",
                  ("resident-lifecycle:resident:A:2", ready_fp))
        raise RuntimeError("synthetic crash before commit")
    except RuntimeError:
        c.rollback()
    preserved = lifecycle_current(c)
    counts = (c.execute("SELECT COUNT(*) FROM event WHERE event_id='event:f3-ready:resident:A:1'").fetchone()[0],
              c.execute("SELECT COUNT(*) FROM canonical_fact WHERE fact_kind='RESIDENT_LIFECYCLE' AND fact_revision=2").fetchone()[0])
    record("READY_Event_fact_pointer_rollback_all_or_zero", "BLOCK",
           preserved is not None and preserved[0] == 1 and preserved[7] == 1 and preserved[12] == 1 and counts == (0, 0)); c.close()
    return rows, failures


def closed_key_self_test(builder, contract: dict) -> tuple[int, list[str]]:
    baseline_boundary = expected_boundary_seed()
    baseline_sources = source_documents(builder, contract, baseline_boundary)
    baseline_rows = builder.collect_key_rows(baseline_sources)
    baseline_objects = {alias: copy.deepcopy(document) for alias, document in baseline_sources}
    failures = []

    def rejected(mutated_sources: list[tuple[str, dict]]) -> bool:
        if [alias for alias, _doc in mutated_sources] != EXPECTED_SOURCE_ALIASES:
            return True
        if any(document != baseline_objects[alias] for alias, document in mutated_sources):
            return True
        rows = builder.collect_key_rows(mutated_sources)
        return rows != baseline_rows or sha_bytes(canonical(rows)) != EXPECTED_KEY_INVENTORY_SHA256

    mutations = []
    a = copy.deepcopy(baseline_sources); a[0][1]["implementation_frozen"] = True; mutations.append(("implementation_frozen", a))
    a = copy.deepcopy(baseline_sources); a[0][1]["neutral_unknown_key"] = False; mutations.append(("unknown_neutral_key", a))
    a = copy.deepcopy(baseline_sources); a[0][1].pop("runtime_usable"); mutations.append(("removed_key", a))
    a = copy.deepcopy(baseline_sources); a[0][1]["runtime_available"] = a[0][1].pop("runtime_usable"); mutations.append(("renamed_key", a))
    a = copy.deepcopy(baseline_sources); a[0][1]["runtime_usable"] = True; mutations.append(("changed_value_same_path", a))
    a = copy.deepcopy(baseline_sources); a[0], a[1] = a[1], a[0]; mutations.append(("reordered_source_alias", a))
    for name, mutated in mutations:
        if not rejected(mutated):
            failures.append(name)
    return len(mutations), failures


def validate(witness: dict):
    errors = []
    for rel, expected in FIXED_HASHES.items():
        if sha(ROOT / rel) != expected:
            errors.append(f"fixed hash mismatch: {rel}")
    contract = load_yaml(R8_CONTRACT)
    persistence = load_yaml(R8_PERSISTENCE)
    if persistence.get("profile_id") != "PHASE_5A_M0A_PERSISTENCE_OWNERSHIP_EVENT_CLOSURE_R8":
        errors.append("R8 persistence profile")
    if persistence.get("effective_schema", {}).get("inherited_R7_table_count") != 18:
        errors.append("R8 inherited table count")
    builder = load_module("phase5a_r8_builder_for_validator", R8_BUILDER)
    if witness != builder.build():
        errors.append("witness not exact builder object")
    closed_errors, key_rows = closed_key_errors(builder, contract, witness)
    errors.extend(closed_errors)
    r7 = load_module("phase5a_r7_for_r8", R7_VALIDATOR)
    r6 = load_module("phase5a_r6_for_r8", r7.R6_VALIDATOR)
    r5 = load_module("phase5a_r5_for_r8", r6.R5_VALIDATOR)
    sql_rows, sql_failures = sqlite_cases(r7, r6, r5)
    errors.extend(f"SQLite case: {name}" for name in sql_failures)
    return errors, key_rows, sql_rows, builder, contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("witness")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        witness = load_json(Path(args.witness))
        errors, key_rows, sql_rows, builder, contract = validate(witness)
        mutation_count = 0; mutation_failures = []
        if args.self_test:
            mutation_count, mutation_failures = closed_key_self_test(builder, contract)
            errors.extend(f"self-test: {name}" for name in mutation_failures)
        output = {
            "result": "PASS_NO_BLOCKER" if not errors else "BLOCK",
            "errors": errors,
            "complete_key_path_rows": f"{len(key_rows)}/{EXPECTED_KEY_ROW_COUNT}",
            "complete_key_path_inventory_sha256": EXPECTED_KEY_INVENTORY_SHA256,
            "SQLite_cases": f"{sum(row['passed'] for row in sql_rows)}/{len(sql_rows)}",
            "fixed_case_count": 6 + len(sql_rows),
            "self_test_mutations": mutation_count,
            "self_test_failures": mutation_failures,
            "effective_tables": "18/18",
            "database_file_occurrence_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if not errors else 1
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "errors": [f"stable malformed-input block: {type(exc).__name__}: {exc}"],
                          "terminal_outcome": "NOT_EXECUTED"}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
