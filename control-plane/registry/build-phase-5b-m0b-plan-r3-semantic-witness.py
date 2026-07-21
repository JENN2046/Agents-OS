#!/usr/bin/env python3
"""Build the deterministic, synthetic, runtime-unusable M0-B Plan R3 witness."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "control-plane/registry/drafts"
ABI_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r3-sealed-abi-f3-shape-profile-v0.1.yaml"
SCHEMA_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r3-candidate-schema-profile-v0.1.yaml"
VALIDATION_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r3-semantic-validation-profile-v0.1.yaml"
DOMAIN = "PHASE_5B_M0B_PLAN_R3_SYNTHETIC_NONAUTHORITY"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


def jcs(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else jcs(value)).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"profile must be an object: {path}")
    return value


def source_text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def rust_string_array(text: str, const_name: str) -> list[str]:
    match = re.search(rf"const\s+{re.escape(const_name)}\s*:\s*\[&str;\s*\d+\]\s*=\s*\[(.*?)\];", text, re.S)
    if not match:
        raise ValueError(f"missing Rust array {const_name}")
    return re.findall(r'"([^"]+)"', match.group(1))


def rust_byte_string(text: str, const_name: str) -> bytes:
    match = re.search(rf"const\s+{re.escape(const_name)}\s*:\s*&\[u8\]\s*=\s*br#\"(.*?)\"#;", text, re.S)
    if not match:
        raise ValueError(f"missing Rust byte string {const_name}")
    return match.group(1).encode("utf-8")


def public_napi_methods(text: str) -> list[str]:
    return re.findall(r'#\[napi\(js_name\s*=\s*"([^"]+)"\)\]\s*pub\s+fn\s+\w+', text)


def request_frame_fields(text: str) -> list[str]:
    match = re.search(r"pub fn parse_request\(.*?value\.require_exact_fields\(&\[(.*?)\]\)\?;", text, re.S)
    if not match:
        raise ValueError("missing parse_request exact field inventory")
    return re.findall(r'"([^"]+)"', match.group(1))


def candidate(candidate_id: str, revision: int, semantic_class: str, source_ref: str, source_fingerprint: str,
              event_sequence: int, predecessor: dict[str, Any] | None) -> dict[str, Any]:
    row = {
        "candidate_id": candidate_id,
        "candidate_revision": revision,
        "candidate_ref": f"candidate:SYNTHETIC_TEST:{candidate_id}:{revision}",
        "semantic_class": semantic_class,
        "source_ref": source_ref,
        "source_revision": 1,
        "source_fingerprint": source_fingerprint,
        "payload_commitment": digest([DOMAIN, "payload", candidate_id, revision]),
        "predecessor_candidate_revision": None if predecessor is None else predecessor["candidate_revision"],
        "predecessor_candidate_ref": None if predecessor is None else predecessor["candidate_ref"],
        "predecessor_candidate_fingerprint": None if predecessor is None else predecessor["candidate_fingerprint"],
        "created_event_sequence": event_sequence,
    }
    row["candidate_fingerprint"] = digest(["agents-os.m0b.home-candidate.v0.1", row])
    return row


def owner(owner: str, result: str, sequence: int) -> dict[str, Any]:
    row = {
        "owner": owner,
        "commitment_ref": f"commitment:SYNTHETIC_TEST:{owner.lower()}:1",
        "commitment_revision": 1,
        "issued_event_sequence": sequence,
        "result": result,
        "current_head": True,
    }
    row["commitment_fingerprint"] = digest(["agents-os.m0b.owner-commitment.v0.1", row])
    return row


def build_fixture() -> dict[str, Any]:
    abi = load_yaml(ABI_PROFILE)
    schema_profile = load_yaml(SCHEMA_PROFILE)
    validation = load_yaml(VALIDATION_PROFILE)
    lib_path = abi["sealed_sources"]["lib_rs"]
    intake_path = abi["sealed_sources"]["command_intake_rs"]
    frame_path = abi["sealed_sources"]["napi_frame_rs"]
    lib = source_text(lib_path)
    intake = source_text(intake_path)
    frame = source_text(frame_path)

    methods = public_napi_methods(lib)
    command_fields = rust_string_array(intake, "COMMAND_FIELDS")
    assertion_fields = rust_string_array(intake, "ASSERTION_FIELDS")
    current_types = rust_string_array(intake, "COMMAND_TYPE_IDS")
    request_schema_bytes = rust_byte_string(frame, "COMMAND_REQUEST_SCHEMA")
    request_fields = request_frame_fields(frame)

    owners = {
        "F7": owner("F7", "CURRENT_ACCEPTED", 10),
        "F8": owner("F8", "CANDIDATE_FORMED", 11),
        "F3": owner("F3", "READY", 12),
    }
    life = candidate("life-stream", 1, "LIFE_STREAM_CANDIDATE", "session:SYNTHETIC_TEST:1", digest([DOMAIN, "session"]), 20, None)
    intent1 = candidate("intent", 1, "INTENT_CANDIDATE", life["candidate_ref"], life["candidate_fingerprint"], 21, None)
    intent2 = candidate("intent", 2, "INTENT_CANDIDATE", intent1["candidate_ref"], intent1["candidate_fingerprint"], 22, intent1)
    candidates = [life, intent1, intent2]

    history = {
        "ordered_candidate_refs": [row["candidate_ref"] for row in candidates],
        "ordered_candidate_fingerprints": [row["candidate_fingerprint"] for row in candidates],
        "selected_candidate_ref": intent2["candidate_ref"],
        "selected_candidate_revision": intent2["candidate_revision"],
        "selected_candidate_fingerprint": intent2["candidate_fingerprint"],
    }
    history["history_fingerprint"] = digest(["agents-os.m0b.candidate-history.v0.1", history])
    owner_set = digest(["agents-os.m0b.owner-commitment-set.v0.1", [owners[x]["commitment_fingerprint"] for x in ("F7", "F8")]])
    handoff = {
        "handoff_ref": "handoff:SYNTHETIC_TEST:home-intent:1",
        "handoff_revision": 1,
        "intent_candidate_id": intent2["candidate_id"],
        "intent_candidate_revision": intent2["candidate_revision"],
        "intent_candidate_ref": intent2["candidate_ref"],
        "intent_candidate_fingerprint": intent2["candidate_fingerprint"],
        "owner_commitment_set_fingerprint": owner_set,
        "canonical_candidate_history_fingerprint": history["history_fingerprint"],
        "minimum_trusted_event_sequence": 22,
    }
    handoff["handoff_fingerprint"] = digest(["agents-os.m0b.f8-handoff.v0.1", handoff])

    payload = {
        "schema_version": abi["prospective_command_delta"]["payload_schema_version"],
        "handoff_candidate_ref": handoff["handoff_ref"],
        "handoff_candidate_revision": handoff["handoff_revision"],
        "handoff_candidate_fingerprint": handoff["handoff_fingerprint"],
        "intent_candidate_ref": intent2["candidate_ref"],
        "intent_candidate_revision": intent2["candidate_revision"],
        "intent_candidate_fingerprint": intent2["candidate_fingerprint"],
        "owner_commitment_set_fingerprint": owner_set,
        "canonical_candidate_history_fingerprint": history["history_fingerprint"],
        "minimum_trusted_event_sequence": handoff["minimum_trusted_event_sequence"],
    }
    command_id = "command:SYNTHETIC_TEST:home-intent:" + digest(["agents-os.m0b.home-intent-command-id.v0.1", payload])
    command = {
        "claimed_actor_id": "actor:SYNTHETIC_TEST:jenn",
        "claimed_principal_binding_ref": "binding:SYNTHETIC_TEST:jenn",
        "claimed_principal_id": "principal:SYNTHETIC_TEST:jenn",
        "claimed_principal_revision": 1,
        "command_id": command_id,
        "command_payload": payload,
        "command_type_id": abi["prospective_command_delta"]["command_type_id"],
        "command_type_revision": 1,
        "environment": "SYNTHETIC_TEST",
        "interface_version": abi["sealed_F3_shapes"]["command_interface_version"],
    }
    command_fingerprint = digest(command)
    principal_binding_fingerprint = digest([
        "agents-os.m0a.synthetic-principal-binding.v0.1",
        {"actor_id": "actor:SYNTHETIC_TEST:jenn", "principal_binding_ref": "binding:SYNTHETIC_TEST:jenn", "principal_id": "principal:SYNTHETIC_TEST:jenn", "principal_revision": 1},
    ])
    assertion = {
        "assertion_ref": f"assertion:SYNTHETIC_TEST:{command_id}",
        "command_fingerprint": command_fingerprint,
        "interface_version": abi["sealed_F3_shapes"]["assertion_interface_version"],
        "principal_binding_fingerprint": principal_binding_fingerprint,
        "synthetic_credential_id": "credential:SYNTHETIC_TEST:deterministic",
    }
    submission = {"authentication_assertion": assertion, "canonical_command": command}
    request = {
        "interface_version": abi["sealed_F3_shapes"]["request_interface_version"],
        "method_id": "execute_command",
        "payload": submission,
        "payload_schema_ref": abi["sealed_F3_shapes"]["request_schema_ref"],
        "payload_schema_sha256": digest(request_schema_bytes),
        "request_id": command_id,
    }
    request_fingerprint = digest(request)
    replay = {
        "command_id": command_id,
        "request_fingerprint": request_fingerprint,
        "request_bytes_fingerprint": digest(jcs(request)),
        "first_response_fingerprint": digest([DOMAIN, "first-response"]),
        "first_event_count": 1,
        "first_external_call_count": 0,
        "additional_event_count_on_replay": 0,
        "additional_external_call_count_on_replay": 0,
    }

    schema = {
        "parent_table": "home_candidate_revision",
        "parent_primary_key": schema_profile["candidate_revision"]["primary_key"],
        "parent_unique_keys": [schema_profile["candidate_revision"]["exact_composite_unique_key"]],
        "parent_column_profiles": schema_profile["candidate_revision"]["column_profiles"],
        "composite_foreign_keys": schema_profile["composite_foreign_keys"],
        "child_column_profiles": {
            "home_candidate_revision": {
                "candidate_id": {"storage_class": "TEXT", "collation": "BINARY"},
                "predecessor_candidate_revision": {"storage_class": "INTEGER"},
                "predecessor_candidate_ref": {"storage_class": "TEXT", "collation": "BINARY"},
                "predecessor_candidate_fingerprint": {"storage_class": "TEXT", "collation": "BINARY"},
            },
            "home_candidate_head": {
                "candidate_id": {"storage_class": "TEXT", "collation": "BINARY"},
                "current_candidate_revision": {"storage_class": "INTEGER"},
                "current_candidate_ref": {"storage_class": "TEXT", "collation": "BINARY"},
                "current_candidate_fingerprint": {"storage_class": "TEXT", "collation": "BINARY"},
            },
            "home_handoff_link": {
                "intent_candidate_id": {"storage_class": "TEXT", "collation": "BINARY"},
                "intent_candidate_revision": {"storage_class": "INTEGER"},
                "intent_candidate_ref": {"storage_class": "TEXT", "collation": "BINARY"},
                "intent_candidate_fingerprint": {"storage_class": "TEXT", "collation": "BINARY"},
            },
        },
    }
    crash_states = [
        {"id": "F3_precommit", "transaction": "F3", "committed": False, "visible_rows_after_restart": "none"},
        {"id": "candidate_postcommit", "transaction": "candidate", "committed": True, "visible_rows_after_restart": "exact_candidate_Event_head_once"},
        {"id": "handoff_precommit", "transaction": "handoff", "committed": False, "visible_rows_after_restart": "none"},
    ]
    fixture = {
        "schema_version": "agents-os.m0b-r3-semantic-witness.v0.1",
        "domain": DOMAIN,
        "profile_fingerprints": {"abi": digest(ABI_PROFILE.read_bytes()), "schema": digest(SCHEMA_PROFILE.read_bytes()), "validation": digest(VALIDATION_PROFILE.read_bytes())},
        "sealed_source_fingerprints": {path: digest((ROOT / path).read_bytes()) for path in (lib_path, intake_path, frame_path)},
        "source_facts": {
            "public_NAPI_methods": methods,
            "command_fields": command_fields,
            "assertion_fields": assertion_fields,
            "request_fields": request_fields,
            "current_command_type_ids": current_types,
            "prospective_command_type_currently_accepted": abi["prospective_command_delta"]["command_type_id"] in current_types,
            "command_request_schema_sha256": digest(request_schema_bytes),
        },
        "owners": owners,
        "candidates": candidates,
        "history": history,
        "handoff": handoff,
        "F3": {"payload": payload, "command": command, "authentication_assertion": assertion, "submission": submission, "request": request, "request_fingerprint": request_fingerprint, "replay": replay},
        "schema": schema,
        "crash_states": crash_states,
        "boundary": {"plan_only": True, "runtime_usable": False, "implementation_authorized": False, "database_created": False, "real_occurrence_count": 0, "terminal_outcome": "NOT_ACTIVATED"},
        "validation_catalog": validation["R2_regression_catalog"]["required_case_ids"],
    }
    fixture["root_fingerprint"] = digest(["agents-os.m0b.r3.semantic-witness-root.v0.1", fixture])
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = build_fixture()
    args.output.write_bytes(jcs(fixture) + b"\n")
    print(f"PASS candidates={len(fixture['candidates'])} cases={len(fixture['validation_catalog'])} root={fixture['root_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
