#!/usr/bin/env python3
"""Build the synthetic, runtime-unusable Phase 5B Plan R5 witness."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
R4_BUILDER = ROOT / "control-plane/registry/build-phase-5b-m0b-plan-r4-closure-witness.py"
PROFILE = ROOT / "control-plane/registry/drafts/2026-07-21-agents-os-phase-5b-m0b-r5-strict-json-integer-profile-v0.1.yaml"
DOMAIN = "PHASE_5B_M0B_PLAN_R5_SYNTHETIC_NONAUTHORITY"


def jcs(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else jcs(value)).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_profile() -> dict[str, Any]:
    value = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("R5 profile must be an object")
    return value


def observation(site: str, value: Any) -> dict[str, Any]:
    return {
        "site": site,
        "value": value,
        "JSON_category": "integer" if type(value) is int else type(value).__name__,
        "host_type": type(value).__name__,
        "strict_integer_one": type(value) is int and value == 1,
    }


def build_fixture() -> dict[str, Any]:
    r4 = load_module(R4_BUILDER, "phase5b_r4_builder").build_fixture()
    profile = load_profile()
    derived = r4["derived_sealed_binding"]["claimed_principal_revision"]
    consumed = r4["R3_fixture"]["F3"]["command"]["claimed_principal_revision"]
    fixture = {
        "schema_version": "agents-os.m0b-r5-strict-integer-witness.v0.1",
        "domain": DOMAIN,
        "profile_fingerprint": digest(PROFILE.read_bytes()),
        "R4_fixture": r4,
        "strict_integer_observations": [
            observation("R4_fixture.derived_sealed_binding.claimed_principal_revision", derived),
            observation("R4_fixture.R3_fixture.F3.command.claimed_principal_revision", consumed),
        ],
        "fixed_regressions": list(profile["fixed_regressions"]),
        "boundary": {
            "plan_only": True,
            "runtime_usable": False,
            "implementation_authorized": False,
            "database_created": False,
            "real_occurrence_count": 0,
            "terminal_outcome": "NOT_ACTIVATED",
        },
    }
    fixture["root_fingerprint"] = digest(["agents-os.m0b.r5.strict-integer-root.v0.1", fixture])
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    fixture = build_fixture()
    args.output.write_bytes(jcs(fixture) + b"\n")
    print(f"PASS cases={len(fixture['fixed_regressions'])} root={fixture['root_fingerprint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
