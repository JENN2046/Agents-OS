#!/usr/bin/env python3
"""Offline semantic validator for the fixed Phase 5B M0-B Plan R2 graph."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[2]
BUILDER_PATH = ROOT / "control-plane/registry/build-phase-5b-m0b-plan-r2-constructive-graph.py"
SOURCE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r2-exact-source-f3-seam-profile-v0.1.yaml"
SCHEMA_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r2-schema-v2-transaction-profile-v0.1.yaml"
GRAPH_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r2-constructive-graph-profile-v0.1.yaml"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


spec = importlib.util.spec_from_file_location("phase5b_m0b_plan_r2_builder", BUILDER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load fixed builder")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class InvalidJson(ValueError):
    pass


def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InvalidJson(f"duplicate key: {key}")
        result[key] = value
    return result


def reject_float(value: str) -> None:
    raise InvalidJson(f"float is forbidden: {value}")


def reject_constant(value: str) -> None:
    raise InvalidJson(f"nonfinite number is forbidden: {value}")


def parse_json(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=pairs_hook,
            parse_float=reject_float,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, InvalidJson, TypeError, ValueError) as exc:
        raise InvalidJson(str(exc)) from exc
    validate_primitive(value)
    if not isinstance(value, dict):
        raise InvalidJson("root must be an object")
    return value


def validate_primitive(value: Any) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not (-MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER):
            raise InvalidJson("integer is outside the JSON safe range")
        return
    if type(value) is str:
        if unicodedata.normalize("NFC", value) != value:
            raise InvalidJson("string is not NFC")
        return
    if type(value) is list:
        for item in value:
            validate_primitive(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or unicodedata.normalize("NFC", key) != key:
                raise InvalidJson("object key must be an NFC string")
            validate_primitive(item)
        return
    raise InvalidJson(f"unsupported JSON value type: {type(value).__name__}")


def exact_fields(value: Any, fields: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = set(value)
    if actual != fields:
        errors.append(f"{label} fields mismatch missing={sorted(fields-actual)} unknown={sorted(actual-fields)}")
        return False
    return True


def load_profile(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"profile root must be object: {path}")
    return value


def sha(value: Any) -> str:
    return builder.digest(value)


def is_hash(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_profiles(errors: list[str]) -> None:
    source = load_profile(SOURCE_PROFILE)
    schema = load_profile(SCHEMA_PROFILE)
    graph = load_profile(GRAPH_PROFILE)

    inventory = source.get("exact_future_source_inventory", {})
    creates = inventory.get("create")
    modifies = inventory.get("modify")
    if not isinstance(creates, list) or len(creates) != 5 or len(set(creates)) != 5:
        errors.append("source create inventory must contain exactly five unique paths")
    if not isinstance(modifies, list) or len(modifies) != 16 or len(set(modifies)) != 16:
        errors.append("source modify inventory must contain exactly sixteen unique paths")
    required_modify = {
        "src/napi_frame.rs",
        "src/reducers/command_intake.rs",
        "src/resident/ledger_thread.rs",
        "src/ledger/replay.rs",
        "src/ledger/recovery.rs",
        "src/ledger/schema.rs",
        "src/ledger/transaction.rs",
    }
    if isinstance(modifies, list) and not required_modify.issubset(modifies):
        errors.append("source modify inventory omits a required closed-seam file")
    if source.get("baseline", {}).get("public_NAPI_methods") != [
        "start_resident", "get_resident_status", "execute_command", "claim_outbox", "reconcile"
    ]:
        errors.append("public NAPI method inventory changed")
    routes = source.get("single_writer_routes", {}).get("routes")
    if not isinstance(routes, list) or len(routes) != 3:
        errors.append("single-writer route inventory must contain exactly three rows")
    elif any(row.get("connection_owner") != "existing_LedgerThread_only" for row in routes):
        errors.append("a source route escapes the existing LedgerThread connection")

    payload = source.get("home_intent_payload", {})
    ordered = payload.get("exact_ordered_fields")
    profiles = payload.get("field_profiles")
    if not isinstance(ordered, list) or len(ordered) != 10 or len(set(ordered)) != 10:
        errors.append("home-intent payload field inventory is not exact")
    if not isinstance(profiles, dict) or set(profiles) != set(ordered or []):
        errors.append("home-intent payload field profiles do not close the exact inventory")
    if payload.get("additional_properties") is not False:
        errors.append("home-intent payload is not closed")

    tables = schema.get("new_tables")
    if not isinstance(tables, dict) or list(tables) != [
        "home_candidate_revision", "home_candidate_head", "home_handoff_link"
    ]:
        errors.append("schema v2 table inventory changed")
    else:
        expected_columns = {
            "home_candidate_revision": 16,
            "home_candidate_head": 7,
            "home_handoff_link": 13,
        }
        for name, count in expected_columns.items():
            columns = tables[name].get("columns")
            if not isinstance(columns, list) or len(columns) != count:
                errors.append(f"{name} exact column count mismatch")
            elif len({row.get('name') for row in columns}) != count:
                errors.append(f"{name} column names are not unique")
            elif any(row.get("nullable") not in (True, False) for row in columns):
                errors.append(f"{name} nullable profiles must be strict booleans")
    if len(schema.get("indexes", [])) != 3 or len(schema.get("immutability_triggers", [])) != 4:
        errors.append("schema index or immutability-trigger inventory changed")
    transition = schema.get("schema_transition", {})
    if transition.get("begin_mode") != "IMMEDIATE" or transition.get("schema_metadata_updated_last") is not True or transition.get("any_failure") != "rollback_all":
        errors.append("schema migration atomicity contract changed")
    if len(schema.get("failpoints", [])) != 11:
        errors.append("crash failpoint inventory must contain exactly eleven rows")

    if len(graph.get("required_node_ids_in_exact_order", [])) != 31:
        errors.append("graph node inventory must contain exactly 31 nodes")
    if len(graph.get("required_edges", [])) != 29:
        errors.append("graph edge inventory must contain exactly 29 edges")
    attacks = graph.get("attack_inventory", {})
    if attacks.get("required_fully_resigned_attacks") != 32 or len(attacks.get("families", [])) != 32:
        errors.append("attack inventory must contain exactly 32 families")


def validate_fixture(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    validate_profiles(errors)
    root_fields = {
        "schema_version", "domain", "profile_fingerprints", "inventories",
        "nodes", "edges", "sections", "counts", "terminal_outcome", "root_fingerprint",
    }
    if not exact_fields(fixture, root_fields, "root", errors):
        return errors
    if fixture.get("schema_version") != "agents-os.m0b-r2-constructive-graph-fixture.v0.1":
        errors.append("fixture schema_version mismatch")
    if fixture.get("domain") != builder.DOMAIN:
        errors.append("fixture domain mismatch")
    if fixture.get("terminal_outcome") != "NOT_ACTIVATED":
        errors.append("fixture terminal outcome must remain NOT_ACTIVATED")

    expected_profile_fingerprints = {
        "source_profile": sha(SOURCE_PROFILE.read_bytes()),
        "schema_profile": sha(SCHEMA_PROFILE.read_bytes()),
        "graph_profile": sha(GRAPH_PROFILE.read_bytes()),
    }
    if fixture.get("profile_fingerprints") != expected_profile_fingerprints:
        errors.append("profile fingerprints are not exact")

    graph = load_profile(GRAPH_PROFILE)
    source = load_profile(SOURCE_PROFILE)
    schema = load_profile(SCHEMA_PROFILE)
    expected_inventories = {
        "source_create": source["exact_future_source_inventory"]["create"],
        "source_modify": source["exact_future_source_inventory"]["modify"],
        "source_forbidden": source["exact_future_source_inventory"]["forbidden_even_after_implementation_start"],
        "public_NAPI_methods": source["baseline"]["public_NAPI_methods"],
        "attack_families": graph["attack_inventory"]["families"],
        "schema_fingerprint": sha([
            "agents-os.m0b.sqlite-schema.v2",
            "0c5a61574a891c7cee0559f18c4bc45f70c6f24a91b65e0b826c9fd15e779f48",
            schema["new_tables"], schema["indexes"], schema["immutability_triggers"],
        ]),
    }
    if fixture.get("inventories") != expected_inventories:
        errors.append("fixture inventories are not exact profile projections")

    nodes = fixture.get("nodes")
    if not isinstance(nodes, list):
        errors.append("nodes must be a list")
        return errors
    node_ids = [row.get("id") for row in nodes if isinstance(row, dict)]
    if node_ids != graph["required_node_ids_in_exact_order"]:
        errors.append("node ID inventory or order mismatch")
    if len(node_ids) != len(set(node_ids)):
        errors.append("node IDs are duplicated")
    node_by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(nodes):
        if not exact_fields(row, {"id", "kind", "payload", "fingerprint"}, f"node[{index}]", errors):
            continue
        expected_fingerprint = sha(["agents-os.m0b.r2.graph-node.v0.1", {"id": row["id"], "kind": row["kind"], "payload": row["payload"]}])
        if row["fingerprint"] != expected_fingerprint:
            errors.append(f"node fingerprint mismatch: {row['id']}")
        node_by_id[row["id"]] = row

    for route_id in ["route:candidate", "route:handoff", "route:f3-home-intent"]:
        row = node_by_id.get(route_id, {}).get("payload", {})
        if row.get("receiver") != "existing_LedgerThread" or row.get("connection_owner") != "existing_LedgerThread_only":
            errors.append(f"single-writer route invalid: {route_id}")
    for owner_id in ["owner:F7-candidate-currentness", "owner:F8-handoff-decision", "owner:F3-command-intake"]:
        row = node_by_id.get(owner_id, {}).get("payload", {})
        if row.get("current_head") is not True or not is_hash(row.get("commitment_fingerprint")):
            errors.append(f"owner commitment invalid: {owner_id}")
        commitment_without = {key: value for key, value in row.items() if key != "commitment_fingerprint"}
        if row.get("commitment_fingerprint") != sha(["agents-os.m0b.owner-commitment.v0.1", commitment_without]):
            errors.append(f"owner commitment fingerprint is not derived: {owner_id}")

    life = node_by_id.get("candidate:life-stream:1", {}).get("payload", {})
    intent = node_by_id.get("candidate:intent:1", {}).get("payload", {})
    history = node_by_id.get("history:home-candidates:1", {}).get("payload", {})
    if life.get("predecessor_ref") is not None or life.get("predecessor_fingerprint") is not None:
        errors.append("life candidate genesis predecessor invalid")
    if intent.get("predecessor_ref") != life.get("candidate_ref") or intent.get("predecessor_fingerprint") != life.get("candidate_fingerprint"):
        errors.append("intent candidate predecessor is not exact")
    if history.get("ordered_candidate_refs") != [life.get("candidate_ref"), intent.get("candidate_ref")]:
        errors.append("candidate history refs are not exact and ordered")
    if history.get("ordered_candidate_fingerprints") != [life.get("candidate_fingerprint"), intent.get("candidate_fingerprint")]:
        errors.append("candidate history fingerprints are not exact and ordered")
    for label, candidate_row in [("life", life), ("intent", intent)]:
        candidate_without = {key: value for key, value in candidate_row.items() if key != "candidate_fingerprint"}
        if candidate_row.get("candidate_fingerprint") != sha(["agents-os.m0b.home-candidate.v0.1", candidate_without]):
            errors.append(f"{label} candidate fingerprint is not derived")
    history_without = {key: value for key, value in history.items() if key != "history_fingerprint"}
    if history.get("history_fingerprint") != sha(["agents-os.m0b.candidate-history.v0.1", history_without]):
        errors.append("candidate history fingerprint is not derived")

    handoff = node_by_id.get("handoff:home-intent:1", {}).get("payload", {})
    payload_row = node_by_id.get("payload:home-intent:1", {}).get("payload", {})
    payload = payload_row.get("canonical_payload", {}) if isinstance(payload_row, dict) else {}
    if handoff.get("intent_candidate_ref") != intent.get("candidate_ref") or handoff.get("intent_candidate_fingerprint") != intent.get("candidate_fingerprint"):
        errors.append("handoff does not bind the exact intent candidate")
    handoff_without = {key: value for key, value in handoff.items() if key != "handoff_fingerprint"}
    if handoff.get("handoff_fingerprint") != sha(["agents-os.m0b.f8-handoff.v0.1", handoff_without]):
        errors.append("handoff fingerprint is not derived")
    handoff_mapping = {
        "handoff_candidate_ref": "handoff_ref",
        "handoff_candidate_revision": "handoff_revision",
        "handoff_candidate_fingerprint": "handoff_fingerprint",
        "intent_candidate_ref": "intent_candidate_ref",
        "intent_candidate_revision": "intent_candidate_revision",
        "intent_candidate_fingerprint": "intent_candidate_fingerprint",
        "owner_commitment_set_fingerprint": "owner_commitment_set_fingerprint",
        "canonical_candidate_history_fingerprint": "canonical_candidate_history_fingerprint",
        "minimum_trusted_event_sequence": "minimum_trusted_event_sequence",
    }
    for payload_key, handoff_key in handoff_mapping.items():
        if payload.get(payload_key) != handoff.get(handoff_key):
            errors.append(f"payload does not bind handoff field: {payload_key}")
    exact_payload_fields = source["home_intent_payload"]["exact_ordered_fields"]
    if set(payload) != set(exact_payload_fields):
        errors.append("payload field inventory is not exact")
    if payload_row.get("payload_fingerprint") != sha(payload):
        errors.append("payload fingerprint is not derived")

    command = node_by_id.get("command:home-intent:1", {}).get("payload", {})
    if command.get("payload_fingerprint") != payload_row.get("payload_fingerprint"):
        errors.append("command payload fingerprint is not exact")
    command_id_digest = sha([
        "agents-os.m0b.home-intent-command-id.v0.1",
        payload.get("handoff_candidate_ref"), payload.get("handoff_candidate_revision"),
        payload.get("handoff_candidate_fingerprint"), payload.get("intent_candidate_ref"),
        payload.get("intent_candidate_revision"), payload.get("intent_candidate_fingerprint"),
        payload.get("owner_commitment_set_fingerprint"),
        payload.get("canonical_candidate_history_fingerprint"),
        payload.get("minimum_trusted_event_sequence"),
    ])
    expected_command_id = f"command:SYNTHETIC_TEST:home-intent:{command_id_digest}"
    if command.get("command_id") != expected_command_id:
        errors.append("command ID is not derived from the exact handoff tuple")
    canonical_command = {
        "command_id": expected_command_id,
        "command_type_id": source["home_intent_payload"]["command_type_id"],
        "command_type_revision": 1,
        "environment": "SYNTHETIC_TEST",
        "command_payload": payload,
    }
    expected_command_fingerprint = sha(canonical_command)
    request = {"method": "execute_command", "request_id": expected_command_id, "payload": canonical_command}
    expected_request_fingerprint = sha(request)
    expected_idempotency = sha([
        "agents-os.m0b.home-intent-idempotency.v0.1",
        expected_command_id,
        expected_request_fingerprint,
    ])
    if command.get("command_fingerprint") != expected_command_fingerprint:
        errors.append("command fingerprint is not derived")
    if command.get("request_fingerprint") != expected_request_fingerprint:
        errors.append("request fingerprint is not derived")
    if command.get("idempotency_key") != expected_idempotency:
        errors.append("idempotency key is not derived")
    replay = node_by_id.get("replay:home-intent:1", {}).get("payload", {})
    if replay.get("command_id") != command.get("command_id") or replay.get("request_fingerprint") != command.get("request_fingerprint"):
        errors.append("replay identity is not exact")
    if replay.get("first_event_count") != 1 or replay.get("first_external_call_count") != 0 or replay.get("additional_event_count_on_replay") != 0 or replay.get("additional_external_call_count_on_replay") != 0:
        errors.append("replay first accounting or additional accounting is invalid")

    edges = fixture.get("edges")
    expected_edges = graph["required_edges"]
    if not isinstance(edges, list) or [(r.get("source"), r.get("target")) for r in edges if isinstance(r, dict)] != [tuple(x) for x in expected_edges]:
        errors.append("edge inventory or order mismatch")
    elif [r.get("ordinal") for r in edges] != list(range(1, len(edges) + 1)):
        errors.append("edge ordinals are not contiguous")
    else:
        for row in edges:
            expected_fingerprint = sha(["agents-os.m0b.r2.graph-edge.v0.1", {"ordinal": row["ordinal"], "source": row["source"], "target": row["target"]}])
            if row.get("fingerprint") != expected_fingerprint:
                errors.append("edge fingerprint mismatch")

    sections = fixture.get("sections")
    if not isinstance(sections, list) or [r.get("name") for r in sections if isinstance(r, dict)] != graph["graph_sections_in_exact_order"]:
        errors.append("section inventory or order mismatch")
    else:
        for row in sections:
            fingerprints = [node_by_id.get(node_id, {}).get("fingerprint") for node_id in row.get("node_ids", [])]
            expected_fingerprint = sha(["agents-os.m0b.r2.graph-section.v0.1", row.get("name"), fingerprints])
            if row.get("fingerprint") != expected_fingerprint:
                errors.append(f"section fingerprint mismatch: {row.get('name')}")

    crash_nodes = [row for row in nodes if isinstance(row, dict) and row.get("kind") == "crash_state"]
    if len(crash_nodes) != 11:
        errors.append("crash-state graph must contain exactly eleven nodes")
    if any(row.get("payload", {}).get("automatic_retry") is not False for row in crash_nodes):
        errors.append("a crash state enables automatic retry")
    boundary = node_by_id.get("boundary:nonauthority", {}).get("payload", {})
    expected_boundary = {
        "implementation_authorized": False,
        "runtime_usable": False,
        "production_compatible": False,
        "real_occurrence_count": 0,
        "second_permission_identity_Task_Command_or_effect_authority_count": 0,
        "writer_thread_count": 1,
        "authoritative_SQLite_connection_count": 1,
        "public_NAPI_method_count": 5,
    }
    if boundary != expected_boundary:
        errors.append("boundary inventory changed")

    counts = fixture.get("counts")
    expected_counts = {"node_count": 31, "edge_count": 29, "section_count": 9, "attack_family_count": 32, "real_occurrence_count": 0}
    if counts != expected_counts:
        errors.append("fixture counts mismatch")
    root_without = {key: value for key, value in fixture.items() if key != "root_fingerprint"}
    expected_root = sha(["agents-os.m0b.r2.constructive-graph-root.v0.1", root_without])
    if fixture.get("root_fingerprint") != expected_root:
        errors.append("root fingerprint mismatch")

    expected_fixture = builder.build_fixture()
    if fixture != expected_fixture:
        errors.append("fixture differs from the independently reconstructed fixed graph")
    return errors


def resign(fixture: dict[str, Any]) -> None:
    node_by_id = {row["id"]: row for row in fixture["nodes"]}
    for row in fixture["nodes"]:
        row["fingerprint"] = sha(["agents-os.m0b.r2.graph-node.v0.1", {"id": row["id"], "kind": row["kind"], "payload": row["payload"]}])
    for row in fixture["edges"]:
        row["fingerprint"] = sha(["agents-os.m0b.r2.graph-edge.v0.1", {"ordinal": row["ordinal"], "source": row["source"], "target": row["target"]}])
    for row in fixture["sections"]:
        row["fingerprint"] = sha(["agents-os.m0b.r2.graph-section.v0.1", row["name"], [node_by_id[x]["fingerprint"] for x in row["node_ids"]]])
    root_without = {key: value for key, value in fixture.items() if key != "root_fingerprint"}
    fixture["root_fingerprint"] = sha(["agents-os.m0b.r2.constructive-graph-root.v0.1", root_without])


def node_payload(fixture: dict[str, Any], node_id: str) -> dict[str, Any]:
    return next(row["payload"] for row in fixture["nodes"] if row["id"] == node_id)


def mutation_functions() -> list[tuple[str, Callable[[dict[str, Any]], None]]]:
    def mutate_inventory(key: str, value: Any) -> Callable[[dict[str, Any]], None]:
        return lambda f: f["inventories"][key].append(value)

    mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("source_inventory_missing_required_file", lambda f: f["inventories"]["source_modify"].remove("src/napi_frame.rs")),
        ("source_inventory_extra_file", mutate_inventory("source_modify", "src/forbidden_extra.rs")),
        ("public_NAPI_method_added", mutate_inventory("public_NAPI_methods", "sixth_method")),
        ("second_writer_thread", lambda f: node_payload(f, "boundary:nonauthority").__setitem__("writer_thread_count", 2)),
        ("second_SQLite_connection", lambda f: node_payload(f, "boundary:nonauthority").__setitem__("authoritative_SQLite_connection_count", 2)),
        ("direct_home_SQL", lambda f: node_payload(f, "route:candidate").__setitem__("connection_owner", "home_module")),
        ("owner_commitment_same_revision_rewrite", lambda f: node_payload(f, "owner:F8-handoff-decision").__setitem__("result", "REJECTED")),
        ("owner_commitment_cross_role_substitution", lambda f: node_payload(f, "owner:F8-handoff-decision").__setitem__("owner", "F3")),
        ("candidate_same_revision_rewrite", lambda f: node_payload(f, "candidate:intent:1").__setitem__("payload_commitment", "0" * 64)),
        ("candidate_predecessor_gap", lambda f: node_payload(f, "candidate:intent:1").__setitem__("predecessor_ref", "candidate:SYNTHETIC_TEST:phantom:1")),
        ("candidate_head_stale_CAS", lambda f: node_payload(f, "transaction:candidate")["preconditions"].append("stale_head_accepted")),
        ("candidate_history_phantom", lambda f: node_payload(f, "history:home-candidates:1")["ordered_candidate_refs"].append("candidate:SYNTHETIC_TEST:phantom:1")),
        ("candidate_history_reorder", lambda f: node_payload(f, "history:home-candidates:1")["ordered_candidate_refs"].reverse()),
        ("handoff_candidate_substitution", lambda f: node_payload(f, "handoff:home-intent:1").__setitem__("intent_candidate_ref", "candidate:SYNTHETIC_TEST:other:1")),
        ("handoff_owner_commitment_substitution", lambda f: node_payload(f, "handoff:home-intent:1").__setitem__("owner_commitment_set_fingerprint", "1" * 64)),
        ("handoff_watermark_stale", lambda f: node_payload(f, "handoff:home-intent:1").__setitem__("minimum_trusted_event_sequence", 1)),
        ("payload_unknown_field", lambda f: node_payload(f, "payload:home-intent:1")["canonical_payload"].__setitem__("unknown", False)),
        ("payload_missing_field", lambda f: node_payload(f, "payload:home-intent:1")["canonical_payload"].pop("handoff_candidate_ref")),
        ("payload_handoff_tuple_mismatch", lambda f: node_payload(f, "payload:home-intent:1")["canonical_payload"].__setitem__("handoff_candidate_revision", 2)),
        ("command_id_not_derived", lambda f: node_payload(f, "command:home-intent:1").__setitem__("command_id", "command:SYNTHETIC_TEST:home-intent:" + "2" * 64)),
        ("request_identity_not_derived", lambda f: node_payload(f, "command:home-intent:1").__setitem__("request_fingerprint", "3" * 64)),
        ("distinct_handoff_same_command_id", lambda f: node_payload(f, "handoff:home-intent:1").__setitem__("handoff_ref", "handoff:SYNTHETIC_TEST:other:1")),
        ("same_command_id_changed_request_bytes", lambda f: node_payload(f, "replay:home-intent:1").__setitem__("request_bytes_fingerprint", "4" * 64)),
        ("F3_first_accounting_changed_on_replay", lambda f: node_payload(f, "replay:home-intent:1").__setitem__("additional_event_count_on_replay", 1)),
        ("schema_unknown_column", lambda f: node_payload(f, "schema:home-candidate-head")["columns"].append({"name": "unknown", "type": "TEXT", "nullable": False})),
        ("schema_missing_constraint", lambda f: node_payload(f, "schema:home-candidate-revision")["checks"].pop()),
        ("schema_fingerprint_not_derived", lambda f: f["inventories"].__setitem__("schema_fingerprint", "5" * 64)),
        ("migration_metadata_updated_first", lambda f: node_payload(f, "transaction:candidate")["ordered_writes"].insert(1, "update_schema_metadata_first")),
        ("candidate_partial_commit_visible", lambda f: node_payload(f, "crash:C2").__setitem__("visible_rows_after_restart", "candidate_visible_without_Event")),
        ("handoff_partial_commit_visible", lambda f: node_payload(f, "crash:H3").__setitem__("visible_rows_after_restart", "handoff_visible_without_Event")),
        ("post_handoff_automatic_F3_retry", lambda f: node_payload(f, "crash:H4").__setitem__("automatic_retry", True)),
        ("synthetic_command_marked_production_usable", lambda f: node_payload(f, "boundary:nonauthority").__setitem__("production_compatible", True)),
    ]
    return mutations


def self_test(fixture: dict[str, Any]) -> tuple[int, list[str]]:
    failures: list[str] = []
    mutations = mutation_functions()
    for name, mutate in mutations:
        candidate = copy.deepcopy(fixture)
        try:
            mutate(candidate)
            resign(candidate)
            if not validate_fixture(candidate):
                failures.append(name)
        except Exception as exc:  # mutation exceptions are failures, never passes
            failures.append(f"{name}:exception:{type(exc).__name__}:{exc}")
    return len(mutations), failures


def parser_self_test(raw: bytes) -> list[str]:
    failures: list[str] = []
    probes = {
        "duplicate_key": b'{"a":1,"a":2}',
        "float": b'{"a":1.5}',
        "NaN": b'{"a":NaN}',
        "non_NFC": '{"a":"e\u0301"}'.encode(),
        "unsafe_integer": b'{"a":9007199254740992}',
    }
    for name, probe in probes.items():
        try:
            parse_json(probe)
        except InvalidJson:
            continue
        failures.append(name)
    try:
        parse_json(raw)
    except InvalidJson as exc:
        failures.append(f"canonical_fixture:{exc}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    raw = args.fixture.read_bytes()
    try:
        fixture = parse_json(raw)
    except InvalidJson as exc:
        print(f"BLOCK parser_error={exc}")
        return 1
    errors = validate_fixture(fixture)
    mutation_count = 0
    mutation_failures: list[str] = []
    parser_failures: list[str] = []
    if args.self_test:
        mutation_count, mutation_failures = self_test(fixture)
        parser_failures = parser_self_test(raw)
    if errors or mutation_failures or parser_failures:
        print("BLOCK")
        for error in errors:
            print(f"error={error}")
        for error in mutation_failures:
            print(f"mutation_failure={error}")
        for error in parser_failures:
            print(f"parser_probe_failure={error}")
        return 1
    print("PASS")
    print(f"node_count={fixture['counts']['node_count']}")
    print(f"edge_count={fixture['counts']['edge_count']}")
    print(f"section_count={fixture['counts']['section_count']}")
    print(f"node_fingerprints_verified={len(fixture['nodes'])}")
    print(f"edge_fingerprints_verified={len(fixture['edges'])}")
    print(f"fully_resigned_mutations_rejected={mutation_count}/{mutation_count}")
    print("parser_probes_rejected=5/5")
    print(f"root_fingerprint={fixture['root_fingerprint']}")
    print(f"terminal_outcome={fixture['terminal_outcome']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
