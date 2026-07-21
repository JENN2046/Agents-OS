#!/usr/bin/env python3
"""Validate the three narrow Plan R4 closures and fully re-signed regressions."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

import yaml


ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "control-plane/registry/drafts"
R3_VALIDATOR = ROOT / "control-plane/registry/validate-phase-5b-m0b-plan-r3-semantic-witness.py"
R4_BUILDER = ROOT / "control-plane/registry/build-phase-5b-m0b-plan-r4-closure-witness.py"
IDENTITY_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r4-sealed-f3-identity-binding-profile-v0.1.yaml"
UNIQUE_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r4-candidate-uniqueness-profile-v0.1.yaml"
FK_PROFILE = DRAFT / "2026-07-21-agents-os-phase-5b-m0b-r4-composite-fk-inventory-profile-v0.1.yaml"
SOURCE = ROOT / "extensions/agents-os-resident/src/reducers/command_intake.rs"
DOMAIN = "PHASE_5B_M0B_PLAN_R4_SYNTHETIC_NONAUTHORITY"


def jcs(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else jcs(value)).hexdigest()


def load_yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"profile must be object: {path}")
    return value


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R3 = load_module(R3_VALIDATOR, "phase5b_r3_validator")
R4 = load_module(R4_BUILDER, "phase5b_r4_builder")


def strict_json(path: Path) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in rows:
            if key in out:
                raise ValueError(f"duplicate JSON key: {key}")
            out[key] = value
        return out
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    if not isinstance(value, dict):
        raise ValueError("fixture root must be object")
    return value


def exact_fields(value: Any, fields: list[str]) -> bool:
    return isinstance(value, dict) and set(value) == set(fields)


def add(errors: list[str], condition: bool, code: str) -> None:
    if not condition:
        errors.append(code)


def rust_public_string(text: str, name: str) -> str:
    match = re.search(rf'pub const\s+{re.escape(name)}\s*:\s*&str\s*=\s*"([^"]+)";', text)
    if not match:
        raise ValueError(f"missing sealed constant {name}")
    return match.group(1)


def derive_sealed_binding() -> dict[str, Any]:
    text = SOURCE.read_text(encoding="utf-8")
    actor = rust_public_string(text, "SYNTHETIC_ACTOR_ID")
    principal = rust_public_string(text, "SYNTHETIC_PRINCIPAL_ID")
    binding = rust_public_string(text, "SYNTHETIC_PRINCIPAL_BINDING_REF")
    credential = rust_public_string(text, "SYNTHETIC_CREDENTIAL_ID")
    revision = 1
    return {
        "claimed_actor_id": actor,
        "claimed_principal_id": principal,
        "claimed_principal_revision": revision,
        "claimed_principal_binding_ref": binding,
        "principal_binding_fingerprint": digest(["agents-os.m0a.synthetic-principal-binding.v0.1", {"actor_id": actor, "principal_binding_ref": binding, "principal_id": principal, "principal_revision": revision}]),
        "synthetic_credential_id": credential,
    }


def validate_semantics(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    fields = ["schema_version", "domain", "profile_fingerprints", "sealed_source_fingerprint", "derived_sealed_binding", "R3_fixture", "closure_inventory", "boundary", "root_fingerprint"]
    add(errors, exact_fields(fixture, fields), "R4_ROOT_SCHEMA_INVALID")
    if not exact_fields(fixture, fields):
        return sorted(set(errors))
    add(errors, fixture["schema_version"] == "agents-os.m0b-r4-closure-witness.v0.1" and fixture["domain"] == DOMAIN, "R4_ROOT_DOMAIN_INVALID")
    expected_profiles = {"identity": digest(IDENTITY_PROFILE.read_bytes()), "candidate_uniqueness": digest(UNIQUE_PROFILE.read_bytes()), "composite_FK_inventory": digest(FK_PROFILE.read_bytes())}
    add(errors, fixture["profile_fingerprints"] == expected_profiles, "R4_PROFILE_FINGERPRINT_INVALID")
    add(errors, fixture["sealed_source_fingerprint"] == digest(SOURCE.read_bytes()), "R4_SEALED_SOURCE_FINGERPRINT_INVALID")
    sealed = derive_sealed_binding()
    add(errors, fixture["derived_sealed_binding"] == sealed, "R4_F3_AUTHORITY_BINDING_INVALID")
    inner = fixture["R3_fixture"]
    errors.extend(f"R3::{x}" for x in R3.validate_semantics(inner))
    command = inner.get("F3", {}).get("command", {}) if isinstance(inner, dict) else {}
    assertion = inner.get("F3", {}).get("authentication_assertion", {}) if isinstance(inner, dict) else {}
    actual_binding = {
        "claimed_actor_id": command.get("claimed_actor_id"),
        "claimed_principal_id": command.get("claimed_principal_id"),
        "claimed_principal_revision": command.get("claimed_principal_revision"),
        "claimed_principal_binding_ref": command.get("claimed_principal_binding_ref"),
        "principal_binding_fingerprint": assertion.get("principal_binding_fingerprint"),
        "synthetic_credential_id": assertion.get("synthetic_credential_id"),
    }
    add(errors, actual_binding == sealed, "R4_F3_AUTHORITY_BINDING_INVALID")

    candidates = inner.get("candidates", []) if isinstance(inner, dict) else []
    keys = [[x.get("candidate_id"), x.get("candidate_revision")] for x in candidates if isinstance(x, dict)]
    refs = [x.get("candidate_ref") for x in candidates if isinstance(x, dict)]
    history_refs = inner.get("history", {}).get("ordered_candidate_refs", []) if isinstance(inner, dict) else []
    genesis_ids = [x.get("candidate_id") for x in candidates if isinstance(x, dict) and x.get("candidate_revision") == 1]
    selected_ref = inner.get("history", {}).get("selected_candidate_ref") if isinstance(inner, dict) else None
    uniqueness_valid = len(keys) == len(set(map(tuple, keys))) and len(refs) == len(set(refs)) and len(history_refs) == len(set(history_refs)) and len(genesis_ids) == len(set(genesis_ids)) == 2 and refs.count(selected_ref) == 1
    add(errors, uniqueness_valid, "R4_CANDIDATE_UNIQUENESS_INVALID")

    closure = fixture["closure_inventory"]
    closure_fields = ["candidate_primary_keys", "candidate_refs", "history_refs", "genesis_candidate_ids", "composite_foreign_keys", "fixed_regressions"]
    add(errors, exact_fields(closure, closure_fields), "R4_CLOSURE_INVENTORY_INVALID")
    if exact_fields(closure, closure_fields):
        add(errors, closure["candidate_primary_keys"] == keys and closure["candidate_refs"] == refs and closure["history_refs"] == history_refs and closure["genesis_candidate_ids"] == genesis_ids, "R4_CANDIDATE_INVENTORY_BINDING_INVALID")
        expected_fk = load_yaml(FK_PROFILE)["exact_ordered_inventory"]
        actual_fk = inner.get("schema", {}).get("composite_foreign_keys", []) if isinstance(inner, dict) else []
        add(errors, actual_fk == expected_fk and len({jcs(x) for x in actual_fk}) == 3, "R4_COMPOSITE_FK_INVENTORY_INVALID")
        add(errors, closure["composite_foreign_keys"] == actual_fk == expected_fk, "R4_COMPOSITE_FK_INVENTORY_INVALID")
        expected_cases = load_yaml(IDENTITY_PROFILE)["fixed_regressions"] + load_yaml(UNIQUE_PROFILE)["fixed_regressions"] + load_yaml(FK_PROFILE)["fixed_regressions"]
        add(errors, closure["fixed_regressions"] == expected_cases and len(set(expected_cases)) == 10, "R4_REGRESSION_INVENTORY_INVALID")
    add(errors, fixture["boundary"] == {"plan_only": True, "runtime_usable": False, "implementation_authorized": False, "database_created": False, "real_occurrence_count": 0, "terminal_outcome": "NOT_ACTIVATED"}, "R4_BOUNDARY_EXPANSION")
    unsigned = {k: v for k, v in fixture.items() if k != "root_fingerprint"}
    add(errors, fixture["root_fingerprint"] == digest(["agents-os.m0b.r4.closure-root.v0.1", unsigned]), "R4_ROOT_FINGERPRINT_INVALID")
    return sorted(set(errors))


def validate_fixed_fixture(fixture: dict[str, Any]) -> list[str]:
    return [] if fixture == R4.build_fixture() else ["R4_FIXED_FIXTURE_SEAL_MISMATCH"]


def resign(fixture: dict[str, Any]) -> None:
    R3.resign(fixture["R3_fixture"])
    inner = fixture["R3_fixture"]
    candidates = inner["candidates"]
    fixture["closure_inventory"].update({
        "candidate_primary_keys": [[x["candidate_id"], x["candidate_revision"]] for x in candidates],
        "candidate_refs": [x["candidate_ref"] for x in candidates],
        "history_refs": list(inner["history"]["ordered_candidate_refs"]),
        "genesis_candidate_ids": [x["candidate_id"] for x in candidates if x["candidate_revision"] == 1],
        "composite_foreign_keys": copy.deepcopy(inner["schema"]["composite_foreign_keys"]),
    })
    fixture["root_fingerprint"] = digest(["agents-os.m0b.r4.closure-root.v0.1", {k: v for k, v in fixture.items() if k != "root_fingerprint"}])


def cases() -> list[tuple[str, str, Callable[[dict[str, Any]], None]]]:
    def command(field: str, value: Any) -> Callable[[dict[str, Any]], None]:
        return lambda f: f["R3_fixture"]["F3"]["command"].update({field: value})
    def assertion(field: str, value: Any) -> Callable[[dict[str, Any]], None]:
        return lambda f: f["R3_fixture"]["F3"]["authentication_assertion"].update({field: value})
    def duplicate_candidate(f: dict[str, Any]) -> None:
        life = f["R3_fixture"]["candidates"][0]
        life.update(candidate_id="intent", candidate_revision=1, candidate_ref="candidate:SYNTHETIC_TEST:intent:1")
    def remove_all_fk(f: dict[str, Any]) -> None:
        f["R3_fixture"]["schema"]["composite_foreign_keys"] = []
    def remove_head_fk(f: dict[str, Any]) -> None:
        del f["R3_fixture"]["schema"]["composite_foreign_keys"][1]
    def duplicate_first_fk(f: dict[str, Any]) -> None:
        rows = f["R3_fixture"]["schema"]["composite_foreign_keys"]
        rows[1] = copy.deepcopy(rows[0])
    return [
        ("PHASE5B_PLAN_R3_IR_CASE_004", "R4_CANDIDATE_UNIQUENESS_INVALID", duplicate_candidate),
        ("PHASE5B_PLAN_R3_IR_CASE_005", "R4_F3_AUTHORITY_BINDING_INVALID", command("claimed_actor_id", "actor:SYNTHETIC_TEST:attacker")),
        ("PHASE5B_PLAN_R3_IR_CASE_006", "R4_F3_AUTHORITY_BINDING_INVALID", command("claimed_principal_id", "principal:SYNTHETIC_TEST:attacker")),
        ("PHASE5B_PLAN_R3_IR_CASE_007", "R4_F3_AUTHORITY_BINDING_INVALID", command("claimed_principal_revision", 2)),
        ("PHASE5B_PLAN_R3_IR_CASE_008", "R4_F3_AUTHORITY_BINDING_INVALID", command("claimed_principal_binding_ref", "binding:SYNTHETIC_TEST:attacker")),
        ("PHASE5B_PLAN_R3_IR_CASE_009", "R4_F3_AUTHORITY_BINDING_INVALID", assertion("principal_binding_fingerprint", "0" * 64)),
        ("PHASE5B_PLAN_R3_IR_CASE_010", "R4_F3_AUTHORITY_BINDING_INVALID", assertion("synthetic_credential_id", "credential:SYNTHETIC_TEST:attacker")),
        ("PHASE5B_PLAN_R3_IR_CASE_015", "R4_COMPOSITE_FK_INVENTORY_INVALID", remove_all_fk),
        ("PHASE5B_PLAN_R3_IR_CASE_016", "R4_COMPOSITE_FK_INVENTORY_INVALID", remove_head_fk),
        ("PHASE5B_PLAN_R3_IR_CASE_017", "R4_COMPOSITE_FK_INVENTORY_INVALID", duplicate_first_fk),
    ]


def run_regressions(base: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for case_id, target, mutate in cases():
        fixture = copy.deepcopy(base)
        mutate(fixture)
        resign(fixture)
        errors = validate_semantics(fixture)
        seal = validate_fixed_fixture(fixture)
        passed = target in errors and seal == ["R4_FIXED_FIXTURE_SEAL_MISMATCH"]
        rows.append({"case_id": case_id, "target_error": target, "semantic_errors": errors, "fixed_seal_errors": seal, "target_semantic_rejection": passed, "seal_only": not errors})
        if not passed:
            failures.append(case_id)
    return rows, failures


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} FIXTURE.json", file=sys.stderr)
        return 2
    try:
        fixture = strict_json(Path(sys.argv[1]))
        semantic = validate_semantics(fixture)
        seal = validate_fixed_fixture(fixture)
        rows, failures = run_regressions(fixture)
    except Exception as exc:
        print(json.dumps({"result": "BLOCK", "error": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 1
    result = {"result": "PASS" if not semantic and not seal and not failures else "BLOCK", "semantic_errors": semantic, "fixed_fixture_errors": seal, "R4_regressions": {"executed": len(rows), "target_semantic_rejected": sum(x["target_semantic_rejection"] for x in rows), "seal_only_rejections": sum(x["seal_only"] for x in rows), "failures": failures}, "terminal_outcome": fixture.get("boundary", {}).get("terminal_outcome")}
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
