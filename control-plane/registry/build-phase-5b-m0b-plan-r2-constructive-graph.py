#!/usr/bin/env python3
"""Build the deterministic, synthetic, runtime-unusable M0-B Plan R2 graph."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r2-exact-source-f3-seam-profile-v0.1.yaml"
SCHEMA_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r2-schema-v2-transaction-profile-v0.1.yaml"
GRAPH_PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r2-constructive-graph-profile-v0.1.yaml"
DOMAIN = "PHASE_5B_M0B_PLAN_R2_SYNTHETIC_NONAUTHORITY"


def jcs(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else jcs(value)).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"profile must be an object: {path}")
    return value


def stable(seed: str) -> str:
    return digest([DOMAIN, seed])


def node(node_id: str, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    row = {"id": node_id, "kind": kind, "payload": payload}
    row["fingerprint"] = digest(["agents-os.m0b.r2.graph-node.v0.1", row])
    return row


def candidate(
    candidate_id: str,
    semantic_class: str,
    source_ref: str,
    source_fingerprint: str,
    event_sequence: int,
    predecessor: dict[str, Any] | None,
) -> dict[str, Any]:
    revision = 1
    candidate_ref = f"candidate:SYNTHETIC_TEST:{candidate_id}:{revision}"
    payload = {
        "candidate_id": candidate_id,
        "candidate_revision": revision,
        "candidate_ref": candidate_ref,
        "semantic_class": semantic_class,
        "source_ref": source_ref,
        "source_revision": 1,
        "source_fingerprint": source_fingerprint,
        "payload_commitment": stable(f"payload:{candidate_id}"),
        "predecessor_ref": None if predecessor is None else predecessor["candidate_ref"],
        "predecessor_fingerprint": None if predecessor is None else predecessor["candidate_fingerprint"],
        "created_event_sequence": event_sequence,
    }
    payload["candidate_fingerprint"] = digest(
        ["agents-os.m0b.home-candidate.v0.1", payload]
    )
    return payload


def build_fixture() -> dict[str, Any]:
    source = load_yaml(SOURCE_PROFILE)
    schema = load_yaml(SCHEMA_PROFILE)
    graph = load_yaml(GRAPH_PROFILE)

    routes = [
        node(
            {"FORM_LIFE_STREAM_OR_INTENT_CANDIDATE": "route:candidate", "FORM_F8_HANDOFF_LINK": "route:handoff", "COMMIT_F3_HOME_INTENT_COMMAND": "route:f3-home-intent"}[row["operation"]],
            "source_route",
            row,
        )
        for row in source["single_writer_routes"]["routes"]
        if isinstance(row, dict)
    ]

    owner_rows = []
    owner_specs = [
        ("owner:F7-candidate-currentness", "F7", "CURRENT_ACCEPTED", 10),
        ("owner:F8-handoff-decision", "F8", "CANDIDATE_FORMED", 11),
        ("owner:F3-command-intake", "F3", "READY", 12),
    ]
    for node_id, owner, result, sequence in owner_specs:
        commitment_ref = f"commitment:SYNTHETIC_TEST:{owner.lower()}:1"
        commitment_payload = {
            "owner": owner,
            "commitment_ref": commitment_ref,
            "commitment_revision": 1,
            "issued_event_sequence": sequence,
            "result": result,
            "current_head": True,
        }
        commitment_payload["commitment_fingerprint"] = digest(
            ["agents-os.m0b.owner-commitment.v0.1", commitment_payload]
        )
        owner_rows.append(node(node_id, "owner_commitment", commitment_payload))

    life = candidate(
        "life-stream",
        "LIFE_STREAM_CANDIDATE",
        "session:SYNTHETIC_TEST:1",
        stable("session-observation"),
        20,
        None,
    )
    intent = candidate(
        "intent",
        "INTENT_CANDIDATE",
        life["candidate_ref"],
        life["candidate_fingerprint"],
        21,
        life,
    )
    life_node = node("candidate:life-stream:1", "candidate_revision", life)
    intent_node = node("candidate:intent:1", "candidate_revision", intent)
    history_payload = {
        "ordered_candidate_refs": [life["candidate_ref"], intent["candidate_ref"]],
        "ordered_candidate_fingerprints": [life["candidate_fingerprint"], intent["candidate_fingerprint"]],
        "latest_candidate_ref": intent["candidate_ref"],
        "latest_candidate_fingerprint": intent["candidate_fingerprint"],
    }
    history_payload["history_fingerprint"] = digest(
        ["agents-os.m0b.candidate-history.v0.1", history_payload]
    )
    history_node = node("history:home-candidates:1", "candidate_history", history_payload)

    owner_set_fingerprint = digest(
        [
            "agents-os.m0b.owner-commitment-set.v0.1",
            [row["payload"]["commitment_fingerprint"] for row in owner_rows[:2]],
        ]
    )
    handoff_payload = {
        "handoff_ref": "handoff:SYNTHETIC_TEST:home-intent:1",
        "handoff_revision": 1,
        "intent_candidate_ref": intent["candidate_ref"],
        "intent_candidate_revision": 1,
        "intent_candidate_fingerprint": intent["candidate_fingerprint"],
        "owner_commitment_set_fingerprint": owner_set_fingerprint,
        "canonical_candidate_history_fingerprint": history_payload["history_fingerprint"],
        "minimum_trusted_event_sequence": 21,
    }
    handoff_payload["handoff_fingerprint"] = digest(
        ["agents-os.m0b.f8-handoff.v0.1", handoff_payload]
    )
    handoff_node = node("handoff:home-intent:1", "handoff", handoff_payload)

    payload = {
        "schema_version": source["home_intent_payload"]["schema_version"],
        "handoff_candidate_ref": handoff_payload["handoff_ref"],
        "handoff_candidate_revision": handoff_payload["handoff_revision"],
        "handoff_candidate_fingerprint": handoff_payload["handoff_fingerprint"],
        "intent_candidate_ref": intent["candidate_ref"],
        "intent_candidate_revision": 1,
        "intent_candidate_fingerprint": intent["candidate_fingerprint"],
        "owner_commitment_set_fingerprint": owner_set_fingerprint,
        "canonical_candidate_history_fingerprint": history_payload["history_fingerprint"],
        "minimum_trusted_event_sequence": 21,
    }
    payload_fingerprint = digest(payload)
    payload_node = node(
        "payload:home-intent:1",
        "F3_payload",
        {"canonical_payload": payload, "payload_fingerprint": payload_fingerprint},
    )
    command_id_digest = digest(
        [
            "agents-os.m0b.home-intent-command-id.v0.1",
            payload["handoff_candidate_ref"],
            payload["handoff_candidate_revision"],
            payload["handoff_candidate_fingerprint"],
            payload["intent_candidate_ref"],
            payload["intent_candidate_revision"],
            payload["intent_candidate_fingerprint"],
            payload["owner_commitment_set_fingerprint"],
            payload["canonical_candidate_history_fingerprint"],
            payload["minimum_trusted_event_sequence"],
        ]
    )
    command_id = f"command:SYNTHETIC_TEST:home-intent:{command_id_digest}"
    canonical_command = {
        "command_id": command_id,
        "command_type_id": source["home_intent_payload"]["command_type_id"],
        "command_type_revision": 1,
        "environment": "SYNTHETIC_TEST",
        "command_payload": payload,
    }
    command_fingerprint = digest(canonical_command)
    request = {"method": "execute_command", "request_id": command_id, "payload": canonical_command}
    request_fingerprint = digest(request)
    idempotency_key = digest(
        ["agents-os.m0b.home-intent-idempotency.v0.1", command_id, request_fingerprint]
    )
    command_node = node(
        "command:home-intent:1",
        "F3_command",
        {
            "command_type_id": source["home_intent_payload"]["command_type_id"],
            "command_type_revision": 1,
            "payload_fingerprint": payload_fingerprint,
            "command_id": command_id,
            "command_fingerprint": command_fingerprint,
            "request_fingerprint": request_fingerprint,
            "idempotency_key": idempotency_key,
        },
    )
    replay_node = node(
        "replay:home-intent:1",
        "replay_identity",
        {
            "command_id": command_id,
            "request_fingerprint": request_fingerprint,
            "request_bytes_fingerprint": request_fingerprint,
            "first_response_fingerprint": stable("first-F3-response"),
            "first_event_count": 1,
            "first_external_call_count": 0,
            "additional_event_count_on_replay": 0,
            "additional_external_call_count_on_replay": 0,
        },
    )

    schema_nodes = [
        node(f"schema:{table_name.replace('_', '-')}", "schema_table", table)
        for table_name, table in schema["new_tables"].items()
    ]
    transaction_nodes = [
        node(
            {"commit_home_candidate": "transaction:candidate", "commit_home_handoff": "transaction:handoff", "terminal_F3_home_intent": "transaction:f3-home-intent"}[name],
            "transaction",
            {"name": name, **value},
        )
        for name, value in schema["transactions"].items()
    ]
    crash_nodes = []
    for row in schema["failpoints"]:
        short_id = row["id"].split("_", 1)[0]
        crash_nodes.append(
            node(
                f"crash:{short_id}",
                "crash_state",
                {
                    "transaction": row["transaction"],
                    "failpoint": row["id"],
                    "committed": "after_COMMIT" in row["id"] or "after_F3_COMMIT" in row["id"],
                    "visible_rows_after_restart": row["expected_after_restart"],
                    "automatic_retry": False,
                },
            )
        )
    boundary_node = node(
        "boundary:nonauthority",
        "boundary",
        {
            "implementation_authorized": False,
            "runtime_usable": False,
            "production_compatible": False,
            "real_occurrence_count": 0,
            "second_permission_identity_Task_Command_or_effect_authority_count": 0,
            "writer_thread_count": 1,
            "authoritative_SQLite_connection_count": 1,
            "public_NAPI_method_count": 5,
        },
    )

    nodes = routes + owner_rows + [life_node, intent_node, history_node, handoff_node, payload_node, command_node, replay_node] + schema_nodes + transaction_nodes + crash_nodes + [boundary_node]
    by_id = {row["id"]: row for row in nodes}
    ordered_ids = graph["required_node_ids_in_exact_order"]
    nodes = [by_id[node_id] for node_id in ordered_ids]

    edges = []
    for ordinal, (source_id, target_id) in enumerate(graph["required_edges"], 1):
        edge = {"ordinal": ordinal, "source": source_id, "target": target_id}
        edge["fingerprint"] = digest(["agents-os.m0b.r2.graph-edge.v0.1", edge])
        edges.append(edge)

    section_ids = {
        "source_routes": ordered_ids[0:3],
        "owner_commitments": ordered_ids[3:6],
        "candidate_history": ordered_ids[6:9],
        "handoff": ordered_ids[9:10],
        "F3_command": ordered_ids[10:13],
        "schema_inventory": ordered_ids[13:16],
        "transaction_traces": ordered_ids[16:19],
        "crash_states": ordered_ids[19:30],
        "boundary": ordered_ids[30:31],
    }
    sections = []
    for name in graph["graph_sections_in_exact_order"]:
        row = {"name": name, "node_ids": section_ids[name]}
        row["fingerprint"] = digest(
            ["agents-os.m0b.r2.graph-section.v0.1", name, [by_id[x]["fingerprint"] for x in row["node_ids"]]]
        )
        sections.append(row)

    fixture = {
        "schema_version": "agents-os.m0b-r2-constructive-graph-fixture.v0.1",
        "domain": DOMAIN,
        "profile_fingerprints": {
            "source_profile": digest(SOURCE_PROFILE.read_bytes()),
            "schema_profile": digest(SCHEMA_PROFILE.read_bytes()),
            "graph_profile": digest(GRAPH_PROFILE.read_bytes()),
        },
        "inventories": {
            "source_create": source["exact_future_source_inventory"]["create"],
            "source_modify": source["exact_future_source_inventory"]["modify"],
            "source_forbidden": source["exact_future_source_inventory"]["forbidden_even_after_implementation_start"],
            "public_NAPI_methods": source["baseline"]["public_NAPI_methods"],
            "attack_families": graph["attack_inventory"]["families"],
            "schema_fingerprint": digest(
                [
                    "agents-os.m0b.sqlite-schema.v2",
                    "0c5a61574a891c7cee0559f18c4bc45f70c6f24a91b65e0b826c9fd15e779f48",
                    schema["new_tables"],
                    schema["indexes"],
                    schema["immutability_triggers"],
                ]
            ),
        },
        "nodes": nodes,
        "edges": edges,
        "sections": sections,
        "counts": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "section_count": len(sections),
            "attack_family_count": len(graph["attack_inventory"]["families"]),
            "real_occurrence_count": 0,
        },
        "terminal_outcome": "NOT_ACTIVATED",
    }
    fixture["root_fingerprint"] = digest(
        ["agents-os.m0b.r2.constructive-graph-root.v0.1", fixture]
    )
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = build_fixture()
    args.output.write_bytes(jcs(fixture) + b"\n")
    print(f"PASS nodes={fixture['counts']['node_count']} edges={fixture['counts']['edge_count']} root={fixture['root_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
