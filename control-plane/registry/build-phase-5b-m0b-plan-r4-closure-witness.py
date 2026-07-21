#!/usr/bin/env python3
"""Build the synthetic, runtime-unusable Phase 5B Plan R4 closure witness."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DRAFT = ROOT / "control-plane/registry/drafts"
R3_BUILDER = ROOT / "control-plane/registry/build-phase-5b-m0b-plan-r3-semantic-witness.py"
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


def rust_public_string(text: str, name: str) -> str:
    match = re.search(rf'pub const\s+{re.escape(name)}\s*:\s*&str\s*=\s*"([^"]+)";', text)
    if not match:
        raise ValueError(f"missing sealed constant {name}")
    return match.group(1)


def sealed_binding() -> dict[str, Any]:
    text = SOURCE.read_text(encoding="utf-8")
    actor = rust_public_string(text, "SYNTHETIC_ACTOR_ID")
    principal = rust_public_string(text, "SYNTHETIC_PRINCIPAL_ID")
    binding = rust_public_string(text, "SYNTHETIC_PRINCIPAL_BINDING_REF")
    credential = rust_public_string(text, "SYNTHETIC_CREDENTIAL_ID")
    revision = 1
    binding_fingerprint = digest([
        "agents-os.m0a.synthetic-principal-binding.v0.1",
        {"actor_id": actor, "principal_binding_ref": binding, "principal_id": principal, "principal_revision": revision},
    ])
    return {
        "claimed_actor_id": actor,
        "claimed_principal_id": principal,
        "claimed_principal_revision": revision,
        "claimed_principal_binding_ref": binding,
        "principal_binding_fingerprint": binding_fingerprint,
        "synthetic_credential_id": credential,
    }


def build_fixture() -> dict[str, Any]:
    r3 = load_module(R3_BUILDER, "phase5b_r3_builder").build_fixture()
    identity = load_yaml(IDENTITY_PROFILE)
    unique = load_yaml(UNIQUE_PROFILE)
    fk = load_yaml(FK_PROFILE)
    candidates = r3["candidates"]
    fixture = {
        "schema_version": "agents-os.m0b-r4-closure-witness.v0.1",
        "domain": DOMAIN,
        "profile_fingerprints": {
            "identity": digest(IDENTITY_PROFILE.read_bytes()),
            "candidate_uniqueness": digest(UNIQUE_PROFILE.read_bytes()),
            "composite_FK_inventory": digest(FK_PROFILE.read_bytes()),
        },
        "sealed_source_fingerprint": digest(SOURCE.read_bytes()),
        "derived_sealed_binding": sealed_binding(),
        "R3_fixture": r3,
        "closure_inventory": {
            "candidate_primary_keys": [[x["candidate_id"], x["candidate_revision"]] for x in candidates],
            "candidate_refs": [x["candidate_ref"] for x in candidates],
            "history_refs": list(r3["history"]["ordered_candidate_refs"]),
            "genesis_candidate_ids": [x["candidate_id"] for x in candidates if x["candidate_revision"] == 1],
            "composite_foreign_keys": r3["schema"]["composite_foreign_keys"],
            "fixed_regressions": identity["fixed_regressions"] + unique["fixed_regressions"] + fk["fixed_regressions"],
        },
        "boundary": {
            "plan_only": True,
            "runtime_usable": False,
            "implementation_authorized": False,
            "database_created": False,
            "real_occurrence_count": 0,
            "terminal_outcome": "NOT_ACTIVATED",
        },
    }
    fixture["root_fingerprint"] = digest(["agents-os.m0b.r4.closure-root.v0.1", fixture])
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = build_fixture()
    args.output.write_bytes(jcs(fixture) + b"\n")
    print(f"PASS cases={len(fixture['closure_inventory']['fixed_regressions'])} root={fixture['root_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
