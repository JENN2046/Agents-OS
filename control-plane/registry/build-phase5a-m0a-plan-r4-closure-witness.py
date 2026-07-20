#!/usr/bin/env python3
"""Build the deterministic Phase 5A M0-A Plan R4 closure witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "control-plane/registry"
PATHS = {
    "amendment": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-plan-v0.1-r4-amendment.draft.md",
    "semantic_owner_corrections": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r4.yaml",
    "persistence_transaction_corrections": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r4.yaml",
    "materialization_ABI_corrections": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r4.yaml",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def build() -> dict:
    owners = yaml.safe_load(PATHS["semantic_owner_corrections"].read_text())
    persistence = yaml.safe_load(PATHS["persistence_transaction_corrections"].read_text())
    abi = yaml.safe_load(PATHS["materialization_ABI_corrections"].read_text())
    witness = {
        "schema_version": "agents-os.m0a-plan-r4-closure-witness.v0.1",
        "review_unit": "PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R4_ATOMIC_BUNDLE",
        "environment": "SYNTHETIC_PLAN_VALIDATION",
        "subject_hashes": {name: sha(path) for name, path in PATHS.items()},
        "immutable_lineage": {
            "R1_manifest_sha256": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
            "R2_manifest_sha256": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
            "R3_manifest_sha256": "d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49",
            "R1_R2_R3_subject_count": 18,
        },
        "semantic_owner_closure": {
            "replacement_count": len(owners["replacement_rows"]),
            "replacement_ID_fingerprint": hashlib.sha256(canonical([x["obligation_id"] for x in owners["replacement_rows"]])).hexdigest(),
            "effective_obligation_count": owners["effective_inventory_rules"]["effective_obligation_count"],
        },
        "persistence_closure": {
            "effective_table_count": persistence["effective_schema"]["effective_table_count"],
            "R4_replacement_table_count": len(persistence["effective_schema"]["replace_R3_or_inherited_tables"]),
            "R4_replacement_table_fingerprint": hashlib.sha256(canonical(persistence["effective_schema"]["replace_R3_or_inherited_tables"])).hexdigest(),
            "fixed_SQLite_positive_count": len(persistence["fixed_SQLite_cases"]["positive"]),
            "fixed_SQLite_negative_count": len(persistence["fixed_SQLite_cases"]["negative"]),
            "transaction_fingerprint": hashlib.sha256(canonical(persistence["transaction_replacements"])).hexdigest(),
        },
        "ABI_closure": {
            "fixed_owner_path": abi["fixed_ABI_owner"]["git_path"],
            "fixed_owner_sha256": abi["fixed_ABI_owner"]["sha256"],
            "actual_manager_value_count": abi["actual_invocation_replacement"]["positional_value_count"],
            "formal_business_argument_count": abi["actual_invocation_replacement"]["module_business_signature"]["formal_business_argument_count"],
            "forbidden_source_count": len(abi["closed_dataflow_rule"]["forbidden_sources"]),
            "ABI_fingerprint": hashlib.sha256(canonical(abi)).hexdigest(),
        },
        "authority_boundary": {
            "implementation_authorized": False,
            "database_file_created": False,
            "VCPToolBox_change_authorized": False,
            "runtime_activation_authorized": False,
            "terminal_outcome": "NOT_EXECUTED",
        },
    }
    witness["root_fingerprint"] = hashlib.sha256(canonical(witness)).hexdigest()
    return witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_bytes(json.dumps(build(), ensure_ascii=False, sort_keys=True, indent=2).encode() + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
