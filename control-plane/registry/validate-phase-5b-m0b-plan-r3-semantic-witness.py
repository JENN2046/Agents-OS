#!/usr/bin/env python3
"""Validate M0-B Plan R3 semantics independently of the fixed fixture seal."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "control-plane/registry/build-phase-5b-m0b-plan-r3-semantic-witness.py"
DRAFT = ROOT / "control-plane/registry/drafts"
ABI_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r3-sealed-abi-f3-shape-profile-v0.1.yaml"
SCHEMA_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r3-candidate-schema-profile-v0.1.yaml"
VALIDATION_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r3-semantic-validation-profile-v0.1.yaml"
DOMAIN = "PHASE_5B_M0B_PLAN_R3_SYNTHETIC_NONAUTHORITY"
MAX_SAFE = 9_007_199_254_740_991
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def jcs(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else jcs(value)).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"profile must be object: {path}")
    return value


def load_builder():
    spec = importlib.util.spec_from_file_location("m0b_r3_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def strict_json(path: Path) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in rows:
            if key in out:
                raise ValueError(f"duplicate JSON key: {key}")
            out[key] = value
        return out

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(f"nonfinite: {x}")))
    if not isinstance(value, dict):
        raise ValueError("fixture root must be object")
    return value


def exact_fields(value: Any, expected: list[str] | set[str]) -> bool:
    return isinstance(value, dict) and set(value) == set(expected)


def positive(value: Any) -> bool:
    return type(value) is int and 0 < value <= MAX_SAFE


def sha(value: Any) -> bool:
    return isinstance(value, str) and bool(SHA_RE.fullmatch(value))


def stable_ref(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and unicodedata.normalize("NFC", value) == value


def rust_array(text: str, name: str) -> list[str]:
    match = re.search(rf"const\s+{re.escape(name)}\s*:\s*\[&str;\s*\d+\]\s*=\s*\[(.*?)\];", text, re.S)
    if not match:
        raise ValueError(f"missing Rust array {name}")
    return re.findall(r'"([^"]+)"', match.group(1))


def rust_bytes(text: str, name: str) -> bytes:
    match = re.search(rf"const\s+{re.escape(name)}\s*:\s*&\[u8\]\s*=\s*br#\"(.*?)\"#;", text, re.S)
    if not match:
        raise ValueError(f"missing Rust byte string {name}")
    return match.group(1).encode()


def request_frame_fields(text: str) -> list[str]:
    match = re.search(r"pub fn parse_request\(.*?value\.require_exact_fields\(&\[(.*?)\]\)\?;", text, re.S)
    if not match:
        raise ValueError("missing parse_request exact field inventory")
    return re.findall(r'"([^"]+)"', match.group(1))


def add(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def validate_semantics(fixture: dict[str, Any], *, check_source_files: bool = True) -> list[str]:
    """Return semantic errors. Exact equality with the author fixture is never used."""
    errors: list[str] = []
    abi = load_yaml(ABI_PROFILE)
    schema_profile = load_yaml(SCHEMA_PROFILE)
    validation_profile = load_yaml(VALIDATION_PROFILE)
    root_fields = ["schema_version", "domain", "profile_fingerprints", "sealed_source_fingerprints", "source_facts", "owners", "candidates", "history", "handoff", "F3", "schema", "crash_states", "boundary", "validation_catalog", "root_fingerprint"]
    add(errors, exact_fields(fixture, root_fields), "ROOT_SCHEMA_INVALID")
    if not exact_fields(fixture, root_fields):
        return sorted(set(errors))
    add(errors, fixture["schema_version"] == "agents-os.m0b-r3-semantic-witness.v0.1" and fixture["domain"] == DOMAIN, "ROOT_DOMAIN_INVALID")

    expected_profile_fps = {"abi": digest(ABI_PROFILE.read_bytes()), "schema": digest(SCHEMA_PROFILE.read_bytes()), "validation": digest(VALIDATION_PROFILE.read_bytes())}
    add(errors, fixture["profile_fingerprints"] == expected_profile_fps, "PROFILE_FINGERPRINT_MISMATCH")
    facts = fixture["source_facts"]
    fact_fields = ["public_NAPI_methods", "command_fields", "assertion_fields", "request_fields", "current_command_type_ids", "prospective_command_type_currently_accepted", "command_request_schema_sha256"]
    add(errors, exact_fields(facts, fact_fields), "SOURCE_FACT_SCHEMA_INVALID")
    if check_source_files:
        source_hashes: dict[str, str] = {}
        try:
            paths = abi["sealed_sources"]
            lib = (ROOT / paths["lib_rs"]).read_text(encoding="utf-8")
            intake = (ROOT / paths["command_intake_rs"]).read_text(encoding="utf-8")
            frame = (ROOT / paths["napi_frame_rs"]).read_text(encoding="utf-8")
            for path in paths.values():
                source_hashes[path] = digest((ROOT / path).read_bytes())
            derived_methods = re.findall(r'#\[napi\(js_name\s*=\s*"([^"]+)"\)\]\s*pub\s+fn\s+\w+', lib)
            derived_command_fields = rust_array(intake, "COMMAND_FIELDS")
            derived_assertion_fields = rust_array(intake, "ASSERTION_FIELDS")
            derived_types = rust_array(intake, "COMMAND_TYPE_IDS")
            derived_request_fields = request_frame_fields(frame)
            request_schema_hash = digest(rust_bytes(frame, "COMMAND_REQUEST_SCHEMA"))
        except (OSError, ValueError) as exc:
            errors.append(f"SEALED_SOURCE_UNAVAILABLE:{type(exc).__name__}")
        else:
            add(errors, fixture["sealed_source_fingerprints"] == source_hashes, "SEALED_SOURCE_FINGERPRINT_MISMATCH")
            add(errors, derived_methods == abi["public_NAPI"]["exact_methods"] == facts["public_NAPI_methods"], "ABI_METHOD_INVENTORY_MISMATCH")
            add(errors, derived_command_fields == abi["sealed_F3_shapes"]["command_exact_fields"] == facts["command_fields"], "F3_COMMAND_SOURCE_SHAPE_MISMATCH")
            add(errors, derived_assertion_fields == abi["sealed_F3_shapes"]["authentication_assertion_exact_fields"] == facts["assertion_fields"], "F3_ASSERTION_SOURCE_SHAPE_MISMATCH")
            add(errors, derived_types == facts["current_command_type_ids"], "F3_COMMAND_TYPE_SOURCE_MISMATCH")
            add(errors, derived_request_fields == abi["sealed_F3_shapes"]["NAPI_request_frame_exact_fields"] == facts["request_fields"], "NAPI_REQUEST_SHAPE_INVALID")
            add(errors, request_schema_hash == facts["command_request_schema_sha256"], "F3_REQUEST_SCHEMA_SOURCE_MISMATCH")
    add(errors, facts.get("request_fields") == abi["sealed_F3_shapes"]["NAPI_request_frame_exact_fields"], "NAPI_REQUEST_SHAPE_INVALID")
    add(errors, facts.get("prospective_command_type_currently_accepted") is False and abi["prospective_command_delta"]["command_type_id"] not in facts.get("current_command_type_ids", []), "PROSPECTIVE_TYPE_STATUS_INVALID")

    owners = fixture["owners"]
    add(errors, exact_fields(owners, ["F7", "F8", "F3"]), "OWNER_SET_INVALID")
    expected_results = {"F7": "CURRENT_ACCEPTED", "F8": "CANDIDATE_FORMED", "F3": "READY"}
    if isinstance(owners, dict):
        for key, expected_result in expected_results.items():
            row = owners.get(key)
            fields = ["owner", "commitment_ref", "commitment_revision", "issued_event_sequence", "result", "current_head", "commitment_fingerprint"]
            if not exact_fields(row, fields):
                errors.append("OWNER_SCHEMA_INVALID")
                continue
            add(errors, row["owner"] == key and row["result"] == expected_result and row["current_head"] is True, "OWNER_RESULT_NOT_ACCEPTABLE")
            add(errors, positive(row["commitment_revision"]) and positive(row["issued_event_sequence"]), "POSITIVE_SAFE_INTEGER_REQUIRED")
            unsigned = {k: v for k, v in row.items() if k != "commitment_fingerprint"}
            add(errors, row["commitment_fingerprint"] == digest(["agents-os.m0b.owner-commitment.v0.1", unsigned]), "OWNER_FINGERPRINT_INVALID")

    candidates = fixture["candidates"]
    add(errors, isinstance(candidates, list) and len(candidates) == 3, "CANDIDATE_INVENTORY_INVALID")
    by_ref: dict[str, dict[str, Any]] = {}
    candidate_fields = ["candidate_id", "candidate_revision", "candidate_ref", "semantic_class", "source_ref", "source_revision", "source_fingerprint", "payload_commitment", "predecessor_candidate_revision", "predecessor_candidate_ref", "predecessor_candidate_fingerprint", "created_event_sequence", "candidate_fingerprint"]
    if isinstance(candidates, list):
        for index, row in enumerate(candidates):
            if not exact_fields(row, candidate_fields):
                errors.append("CANDIDATE_SCHEMA_INVALID")
                continue
            add(errors, all(stable_ref(row[x]) for x in ("candidate_id", "candidate_ref", "source_ref")), "STABLE_REF_REQUIRED")
            add(errors, positive(row["candidate_revision"]) and positive(row["source_revision"]) and positive(row["created_event_sequence"]), "POSITIVE_SAFE_INTEGER_REQUIRED")
            add(errors, all(sha(row[x]) for x in ("source_fingerprint", "payload_commitment", "candidate_fingerprint")), "LOWERCASE_SHA256_REQUIRED")
            expected_class = "LIFE_STREAM_CANDIDATE" if index == 0 else "INTENT_CANDIDATE"
            add(errors, row["semantic_class"] == expected_class, "CANDIDATE_SEMANTIC_CLASS_INVALID")
            add(errors, row["candidate_ref"] == f"candidate:SYNTHETIC_TEST:{row['candidate_id']}:{row['candidate_revision']}", "CANDIDATE_REF_INVALID")
            unsigned = {k: v for k, v in row.items() if k != "candidate_fingerprint"}
            add(errors, row["candidate_fingerprint"] == digest(["agents-os.m0b.home-candidate.v0.1", unsigned]), "CANDIDATE_FINGERPRINT_INVALID")
            by_ref[row["candidate_ref"]] = row
        for row in candidates:
            if not isinstance(row, dict) or "candidate_revision" not in row:
                continue
            pred_tuple = (row.get("predecessor_candidate_revision"), row.get("predecessor_candidate_ref"), row.get("predecessor_candidate_fingerprint"))
            if row["candidate_revision"] == 1:
                add(errors, pred_tuple == (None, None, None), "CANDIDATE_PREDECESSOR_INVALID")
            else:
                pred = by_ref.get(row.get("predecessor_candidate_ref"))
                valid = pred is not None and pred.get("candidate_id") == row.get("candidate_id") and pred.get("candidate_revision") == row.get("candidate_revision") - 1 and row.get("predecessor_candidate_revision") == pred.get("candidate_revision") and row.get("predecessor_candidate_fingerprint") == pred.get("candidate_fingerprint")
                add(errors, valid, "CANDIDATE_PREDECESSOR_INVALID")

    history = fixture["history"]
    history_fields = ["ordered_candidate_refs", "ordered_candidate_fingerprints", "selected_candidate_ref", "selected_candidate_revision", "selected_candidate_fingerprint", "history_fingerprint"]
    add(errors, exact_fields(history, history_fields), "HISTORY_SCHEMA_INVALID")
    selected = None
    if exact_fields(history, history_fields) and isinstance(candidates, list):
        add(errors, history["ordered_candidate_refs"] == [x.get("candidate_ref") for x in candidates] and history["ordered_candidate_fingerprints"] == [x.get("candidate_fingerprint") for x in candidates], "CANDIDATE_HISTORY_INVALID")
        selected = by_ref.get(history["selected_candidate_ref"])
        add(errors, selected is not None and selected.get("candidate_revision") == history["selected_candidate_revision"] and selected.get("candidate_fingerprint") == history["selected_candidate_fingerprint"], "CANDIDATE_HISTORY_INVALID")
        unsigned = {k: v for k, v in history.items() if k != "history_fingerprint"}
        add(errors, history["history_fingerprint"] == digest(["agents-os.m0b.candidate-history.v0.1", unsigned]), "HISTORY_FINGERPRINT_INVALID")

    handoff = fixture["handoff"]
    handoff_fields = ["handoff_ref", "handoff_revision", "intent_candidate_id", "intent_candidate_revision", "intent_candidate_ref", "intent_candidate_fingerprint", "owner_commitment_set_fingerprint", "canonical_candidate_history_fingerprint", "minimum_trusted_event_sequence", "handoff_fingerprint"]
    add(errors, exact_fields(handoff, handoff_fields), "HANDOFF_SCHEMA_INVALID")
    if exact_fields(handoff, handoff_fields):
        add(errors, handoff["handoff_revision"] == 1, "HANDOFF_REVISION_INVALID")
        add(errors, selected is not None and (handoff["intent_candidate_id"], handoff["intent_candidate_revision"], handoff["intent_candidate_ref"], handoff["intent_candidate_fingerprint"]) == (selected.get("candidate_id"), selected.get("candidate_revision"), selected.get("candidate_ref"), selected.get("candidate_fingerprint")), "HANDOFF_CANDIDATE_INVALID")
        expected_owner_set = digest(["agents-os.m0b.owner-commitment-set.v0.1", [owners[x]["commitment_fingerprint"] for x in ("F7", "F8")]]) if exact_fields(owners, ["F7", "F8", "F3"]) else None
        add(errors, handoff["owner_commitment_set_fingerprint"] == expected_owner_set, "HANDOFF_OWNER_SET_INVALID")
        add(errors, handoff["canonical_candidate_history_fingerprint"] == history.get("history_fingerprint"), "HANDOFF_HISTORY_INVALID")
        add(errors, selected is not None and positive(handoff["minimum_trusted_event_sequence"]) and handoff["minimum_trusted_event_sequence"] >= selected.get("created_event_sequence", MAX_SAFE + 1), "HANDOFF_WATERMARK_STALE")
        unsigned = {k: v for k, v in handoff.items() if k != "handoff_fingerprint"}
        add(errors, handoff["handoff_fingerprint"] == digest(["agents-os.m0b.f8-handoff.v0.1", unsigned]), "HANDOFF_FINGERPRINT_INVALID")

    f3 = fixture["F3"]
    f3_fields = ["payload", "command", "authentication_assertion", "submission", "request", "request_fingerprint", "replay"]
    add(errors, exact_fields(f3, f3_fields), "F3_SCHEMA_INVALID")
    if exact_fields(f3, f3_fields):
        payload = f3["payload"]
        command = f3["command"]
        assertion = f3["authentication_assertion"]
        submission = f3["submission"]
        request = f3["request"]
        expected_payload_fields = abi["prospective_command_delta"]["payload_exact_fields"]
        add(errors, exact_fields(payload, expected_payload_fields), "F3_PAYLOAD_SHAPE_INVALID")
        add(errors, exact_fields(command, abi["sealed_F3_shapes"]["command_exact_fields"]), "F3_COMMAND_SHAPE_INVALID")
        add(errors, exact_fields(assertion, abi["sealed_F3_shapes"]["authentication_assertion_exact_fields"]), "F3_ASSERTION_SHAPE_INVALID")
        add(errors, exact_fields(submission, abi["sealed_F3_shapes"]["submission_exact_fields"]), "F3_SUBMISSION_SHAPE_INVALID")
        add(errors, exact_fields(request, abi["sealed_F3_shapes"]["NAPI_request_frame_exact_fields"]), "NAPI_REQUEST_SHAPE_INVALID")
        if exact_fields(payload, expected_payload_fields) and exact_fields(handoff, handoff_fields):
            expected_payload = {
                "schema_version": abi["prospective_command_delta"]["payload_schema_version"], "handoff_candidate_ref": handoff["handoff_ref"], "handoff_candidate_revision": handoff["handoff_revision"], "handoff_candidate_fingerprint": handoff["handoff_fingerprint"], "intent_candidate_ref": handoff["intent_candidate_ref"], "intent_candidate_revision": handoff["intent_candidate_revision"], "intent_candidate_fingerprint": handoff["intent_candidate_fingerprint"], "owner_commitment_set_fingerprint": handoff["owner_commitment_set_fingerprint"], "canonical_candidate_history_fingerprint": handoff["canonical_candidate_history_fingerprint"], "minimum_trusted_event_sequence": handoff["minimum_trusted_event_sequence"],
            }
            add(errors, payload == expected_payload, "F3_PAYLOAD_BINDING_INVALID")
        if isinstance(command, dict):
            expected_command_id = "command:SYNTHETIC_TEST:home-intent:" + digest(["agents-os.m0b.home-intent-command-id.v0.1", payload])
            add(errors, command.get("command_id") == expected_command_id and command.get("command_payload") == payload and command.get("command_type_id") == abi["prospective_command_delta"]["command_type_id"] and command.get("command_type_revision") == 1 and command.get("environment") == "SYNTHETIC_TEST" and command.get("interface_version") == abi["sealed_F3_shapes"]["command_interface_version"], "F3_COMMAND_DERIVATION_INVALID")
            command_fp = digest(command)
        else:
            expected_command_id, command_fp = None, None
        if isinstance(assertion, dict):
            add(errors, assertion.get("command_fingerprint") == command_fp and assertion.get("assertion_ref") == f"assertion:SYNTHETIC_TEST:{expected_command_id}" and assertion.get("interface_version") == abi["sealed_F3_shapes"]["assertion_interface_version"], "F3_ASSERTION_BINDING_INVALID")
        add(errors, submission == {"authentication_assertion": assertion, "canonical_command": command}, "F3_SUBMISSION_BINDING_INVALID")
        if isinstance(request, dict):
            add(errors, request.get("interface_version") == abi["sealed_F3_shapes"]["request_interface_version"] and request.get("method_id") == "execute_command" and request.get("payload") == submission and request.get("payload_schema_ref") == abi["sealed_F3_shapes"]["request_schema_ref"] and request.get("payload_schema_sha256") == facts.get("command_request_schema_sha256") and request.get("request_id") == expected_command_id, "NAPI_REQUEST_DERIVATION_INVALID")
            expected_request_fp = digest(request)
            add(errors, f3["request_fingerprint"] == expected_request_fp, "NAPI_REQUEST_FINGERPRINT_INVALID")
            replay = f3["replay"]
            if isinstance(replay, dict):
                add(errors, replay.get("command_id") == expected_command_id and replay.get("request_fingerprint") == expected_request_fp and replay.get("request_bytes_fingerprint") == digest(jcs(request)), "REPLAY_IDENTITY_INVALID")
                add(errors, sha(replay.get("first_response_fingerprint")), "LOWERCASE_SHA256_REQUIRED")
                add(errors, replay.get("first_event_count") == 1 and replay.get("first_external_call_count") == 0 and replay.get("additional_event_count_on_replay") == 0 and replay.get("additional_external_call_count_on_replay") == 0, "REPLAY_ACCOUNTING_INVALID")

    schema = fixture["schema"]
    schema_fields = ["parent_table", "parent_primary_key", "parent_unique_keys", "parent_column_profiles", "composite_foreign_keys", "child_column_profiles"]
    add(errors, exact_fields(schema, schema_fields), "SCHEMA_INVENTORY_INVALID")
    if exact_fields(schema, schema_fields):
        exact_key = schema_profile["candidate_revision"]["exact_composite_unique_key"]
        add(errors, exact_key in schema["parent_unique_keys"], "COMPOSITE_FOREIGN_KEY_UNCOVERED")
        for fk in schema["composite_foreign_keys"] if isinstance(schema["composite_foreign_keys"], list) else []:
            covered = fk.get("parent_table") == schema["parent_table"] and fk.get("parent_columns") in [schema["parent_primary_key"], *schema["parent_unique_keys"]] and len(fk.get("child_columns", [])) == len(fk.get("parent_columns", []))
            add(errors, covered, "COMPOSITE_FOREIGN_KEY_UNCOVERED")
            if covered:
                child_profiles = schema["child_column_profiles"].get(fk["child_table"], {})
                for child, parent in zip(fk["child_columns"], fk["parent_columns"]):
                    cp = child_profiles.get(child, {})
                    pp = schema["parent_column_profiles"].get(parent, {})
                    add(errors, cp.get("storage_class") == pp.get("storage_class") and cp.get("collation", "BINARY") == pp.get("collation", "BINARY"), "COMPOSITE_FOREIGN_KEY_TYPE_MISMATCH")

    crash = fixture["crash_states"]
    expected_crash = {"F3_precommit": (False, "none"), "candidate_postcommit": (True, "exact_candidate_Event_head_once"), "handoff_precommit": (False, "none")}
    add(errors, isinstance(crash, list) and {x.get("id") for x in crash if isinstance(x, dict)} == set(expected_crash), "CRASH_INVENTORY_INVALID")
    if isinstance(crash, list):
        for row in crash:
            if isinstance(row, dict) and row.get("id") in expected_crash:
                add(errors, (row.get("committed"), row.get("visible_rows_after_restart")) == expected_crash[row["id"]], "CRASH_PROJECTION_INVALID")
    boundary = fixture["boundary"]
    add(errors, boundary == {"plan_only": True, "runtime_usable": False, "implementation_authorized": False, "database_created": False, "real_occurrence_count": 0, "terminal_outcome": "NOT_ACTIVATED"}, "BOUNDARY_EXPANSION")
    add(errors, fixture["validation_catalog"] == validation_profile["R2_regression_catalog"]["required_case_ids"], "REGRESSION_CATALOG_INVALID")
    unsigned_root = {k: v for k, v in fixture.items() if k != "root_fingerprint"}
    add(errors, fixture["root_fingerprint"] == digest(["agents-os.m0b.r3.semantic-witness-root.v0.1", unsigned_root]), "ROOT_FINGERPRINT_INVALID")
    return sorted(set(errors))


def validate_fixed_fixture(fixture: dict[str, Any]) -> list[str]:
    expected = load_builder().build_fixture()
    return [] if fixture == expected else ["FIXED_FIXTURE_SEAL_MISMATCH"]


def resign(fixture: dict[str, Any]) -> None:
    """Propagate every derived commitment while preserving mutated semantic claims."""
    owners = fixture["owners"]
    for row in owners.values():
        row["commitment_fingerprint"] = digest(["agents-os.m0b.owner-commitment.v0.1", {k: v for k, v in row.items() if k != "commitment_fingerprint"}])
    candidates = fixture["candidates"]
    old_by_ref = {row["candidate_ref"]: row["candidate_fingerprint"] for row in candidates}
    new_by_ref: dict[str, str] = {}
    for row in candidates:
        if row.get("source_ref") in new_by_ref:
            row["source_fingerprint"] = new_by_ref[row["source_ref"]]
        if row.get("predecessor_candidate_ref") in new_by_ref:
            row["predecessor_candidate_fingerprint"] = new_by_ref[row["predecessor_candidate_ref"]]
        row["candidate_fingerprint"] = digest(["agents-os.m0b.home-candidate.v0.1", {k: v for k, v in row.items() if k != "candidate_fingerprint"}])
        new_by_ref[row["candidate_ref"]] = row["candidate_fingerprint"]
    history = fixture["history"]
    history["ordered_candidate_refs"] = [x["candidate_ref"] for x in candidates]
    history["ordered_candidate_fingerprints"] = [x["candidate_fingerprint"] for x in candidates]
    selected = candidates[-1]
    history["selected_candidate_ref"] = selected["candidate_ref"]
    history["selected_candidate_revision"] = selected["candidate_revision"]
    history["selected_candidate_fingerprint"] = selected["candidate_fingerprint"]
    history["history_fingerprint"] = digest(["agents-os.m0b.candidate-history.v0.1", {k: v for k, v in history.items() if k != "history_fingerprint"}])
    handoff = fixture["handoff"]
    handoff.update({"intent_candidate_id": selected["candidate_id"], "intent_candidate_revision": selected["candidate_revision"], "intent_candidate_ref": selected["candidate_ref"], "intent_candidate_fingerprint": selected["candidate_fingerprint"], "owner_commitment_set_fingerprint": digest(["agents-os.m0b.owner-commitment-set.v0.1", [owners[x]["commitment_fingerprint"] for x in ("F7", "F8")]]), "canonical_candidate_history_fingerprint": history["history_fingerprint"]})
    handoff["handoff_fingerprint"] = digest(["agents-os.m0b.f8-handoff.v0.1", {k: v for k, v in handoff.items() if k != "handoff_fingerprint"}])
    abi = load_yaml(ABI_PROFILE)
    payload = fixture["F3"]["payload"]
    payload.update({"handoff_candidate_ref": handoff["handoff_ref"], "handoff_candidate_revision": handoff["handoff_revision"], "handoff_candidate_fingerprint": handoff["handoff_fingerprint"], "intent_candidate_ref": selected["candidate_ref"], "intent_candidate_revision": selected["candidate_revision"], "intent_candidate_fingerprint": selected["candidate_fingerprint"], "owner_commitment_set_fingerprint": handoff["owner_commitment_set_fingerprint"], "canonical_candidate_history_fingerprint": history["history_fingerprint"], "minimum_trusted_event_sequence": handoff["minimum_trusted_event_sequence"]})
    command = fixture["F3"]["command"]
    command["command_payload"] = payload
    command["command_id"] = "command:SYNTHETIC_TEST:home-intent:" + digest(["agents-os.m0b.home-intent-command-id.v0.1", payload])
    assertion = fixture["F3"]["authentication_assertion"]
    assertion["command_fingerprint"] = digest(command)
    assertion["assertion_ref"] = f"assertion:SYNTHETIC_TEST:{command['command_id']}"
    fixture["F3"]["submission"] = {"authentication_assertion": assertion, "canonical_command": command}
    request = fixture["F3"]["request"]
    request["payload"] = fixture["F3"]["submission"]
    request["request_id"] = command["command_id"]
    fixture["F3"]["request_fingerprint"] = digest(request)
    replay = fixture["F3"]["replay"]
    replay["command_id"] = command["command_id"]
    replay["request_fingerprint"] = digest(request)
    replay["request_bytes_fingerprint"] = digest(jcs(request))
    fixture["root_fingerprint"] = digest(["agents-os.m0b.r3.semantic-witness-root.v0.1", {k: v for k, v in fixture.items() if k != "root_fingerprint"}])


def attack_cases(base: dict[str, Any]) -> list[tuple[str, str, Callable[[dict[str, Any]], None]]]:
    def crash(case_id: str, committed: bool | None = None, visible: str | None = None) -> Callable[[dict[str, Any]], None]:
        def mutate(f: dict[str, Any]) -> None:
            row = next(x for x in f["crash_states"] if x["id"] == case_id)
            if committed is not None:
                row["committed"] = committed
            if visible is not None:
                row["visible_rows_after_restart"] = visible
        return mutate
    return [
        ("PHASE5B_PLAN_R2_IR_CASE_001", "OWNER_RESULT_NOT_ACCEPTABLE", lambda f: f["owners"]["F8"].update(result="REJECTED")),
        ("PHASE5B_PLAN_R2_IR_CASE_002", "OWNER_RESULT_NOT_ACCEPTABLE", lambda f: f["owners"]["F7"].update(result="INDETERMINATE")),
        ("PHASE5B_PLAN_R2_IR_CASE_003", "OWNER_RESULT_NOT_ACCEPTABLE", lambda f: f["owners"]["F3"].update(result="REJECTED")),
        ("PHASE5B_PLAN_R2_IR_CASE_004", "CANDIDATE_SEMANTIC_CLASS_INVALID", lambda f: f["candidates"][0].update(semantic_class="MEMORY_CANDIDATE")),
        ("PHASE5B_PLAN_R2_IR_CASE_005", "CANDIDATE_SEMANTIC_CLASS_INVALID", lambda f: f["candidates"][-1].update(semantic_class="MEMORY_CANDIDATE")),
        ("PHASE5B_PLAN_R2_IR_CASE_006", "POSITIVE_SAFE_INTEGER_REQUIRED", lambda f: f["candidates"][0].update(source_revision=0)),
        ("PHASE5B_PLAN_R2_IR_CASE_007", "POSITIVE_SAFE_INTEGER_REQUIRED", lambda f: f["candidates"][0].update(created_event_sequence=0)),
        ("PHASE5B_PLAN_R2_IR_CASE_008", "CANDIDATE_PREDECESSOR_INVALID", lambda f: f["candidates"][-1].update(predecessor_candidate_revision=1, predecessor_candidate_ref=f["candidates"][0]["candidate_ref"], predecessor_candidate_fingerprint=f["candidates"][0]["candidate_fingerprint"])),
        ("PHASE5B_PLAN_R2_IR_CASE_009", "HANDOFF_WATERMARK_STALE", lambda f: f["handoff"].update(minimum_trusted_event_sequence=21)),
        ("PHASE5B_PLAN_R2_IR_CASE_010", "HANDOFF_REVISION_INVALID", lambda f: f["handoff"].update(handoff_revision=2)),
        ("PHASE5B_PLAN_R2_IR_CASE_011", "LOWERCASE_SHA256_REQUIRED", lambda f: f["F3"]["replay"].update(first_response_fingerprint="not-a-sha256")),
        ("PHASE5B_PLAN_R2_IR_CASE_012", "CRASH_PROJECTION_INVALID", crash("F3_precommit", visible="partial_inbox_only")),
        ("PHASE5B_PLAN_R2_IR_CASE_013", "CRASH_PROJECTION_INVALID", crash("candidate_postcommit", committed=False)),
        ("PHASE5B_PLAN_R2_IR_CASE_014", "CRASH_PROJECTION_INVALID", crash("handoff_precommit", committed=True)),
    ]


def run_regressions(base: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for case_id, target, mutate in attack_cases(base):
        fixture = copy.deepcopy(base)
        mutate(fixture)
        resign(fixture)
        errors = validate_semantics(fixture)
        seal = validate_fixed_fixture(fixture)
        passed = target in errors and errors != ["FIXED_FIXTURE_SEAL_MISMATCH"] and seal == ["FIXED_FIXTURE_SEAL_MISMATCH"]
        rows.append({"case_id": case_id, "target_error": target, "semantic_errors": errors, "fixed_seal_errors": seal, "target_semantic_rejection": passed, "seal_only": not errors})
        if not passed:
            failures.append(f"{case_id}:{target}")
    return rows, failures


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} FIXTURE.json", file=sys.stderr)
        return 2
    try:
        fixture = strict_json(Path(sys.argv[1]))
        semantic = validate_semantics(fixture)
        seal = validate_fixed_fixture(fixture)
        rows, regression_failures = run_regressions(fixture)
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 1
    result = {
        "result": "PASS" if not semantic and not seal and not regression_failures else "BLOCK",
        "semantic_errors": semantic,
        "fixed_fixture_errors": seal,
        "R2_regressions": {"executed": len(rows), "target_semantic_rejected": sum(x["target_semantic_rejection"] for x in rows), "seal_only_rejections": sum(x["seal_only"] for x in rows), "failures": regression_failures},
        "positive_controls": {"separate_genesis": fixture.get("candidates", [{}, {}])[0].get("predecessor_candidate_ref") is None and fixture.get("candidates", [{}, {}])[1].get("predecessor_candidate_ref") is None, "same_identity_revision_advance": fixture.get("candidates", [{}, {}, {}])[2].get("predecessor_candidate_ref") == fixture.get("candidates", [{}, {}])[1].get("candidate_ref"), "semantic_validator_independent_of_fixture_seal": True},
        "terminal_outcome": fixture.get("boundary", {}).get("terminal_outcome"),
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
