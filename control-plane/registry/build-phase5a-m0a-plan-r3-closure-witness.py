#!/usr/bin/env python3
"""Build the deterministic Phase 5A M0-A plan R3 closure witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "control-plane/registry"
PATHS = {
    "amendment": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-plan-v0.1-r3-amendment.draft.md",
    "semantic_owner_corrections": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r3.yaml",
    "persistence_transaction_corrections": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r3.yaml",
    "materialization_ABI_corrections": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r3.yaml",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def build() -> dict:
    owners = yaml.safe_load(PATHS["semantic_owner_corrections"].read_text())
    persistence = yaml.safe_load(PATHS["persistence_transaction_corrections"].read_text())
    materialization = yaml.safe_load(PATHS["materialization_ABI_corrections"].read_text())
    replacement_tables = persistence["effective_schema"]["replacement_tables"]
    inherited_tables = persistence["effective_schema"]["inherited_tables"]
    transactions = persistence["effective_transaction_owners"]
    witness = {
        "schema_version": "agents-os.m0a-plan-r3-closure-witness.v0.1",
        "review_unit": "PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R3_ATOMIC_BUNDLE",
        "environment": "SYNTHETIC_PLAN_VALIDATION",
        "subject_hashes": {name: sha(path) for name, path in PATHS.items()},
        "semantic_owner_closure": {
            "replacement_count": len(owners["replacement_rows"]),
            "replacement_ID_fingerprint": hashlib.sha256(canonical([x["obligation_id"] for x in owners["replacement_rows"]])).hexdigest(),
            "effective_obligation_count": owners["effective_inventory_rules"]["effective_obligation_count"],
            "added_obligations": owners["effective_inventory_rules"]["add_obligation_ids"],
            "removed_obligations": owners["effective_inventory_rules"]["remove_obligation_ids"],
        },
        "persistence_closure": {
            "effective_table_count": persistence["effective_schema"]["effective_table_count"],
            "replacement_table_count": len(replacement_tables),
            "inherited_table_count": len(inherited_tables),
            "effective_table_fingerprint": hashlib.sha256(canonical(sorted(replacement_tables + inherited_tables))).hexdigest(),
            "transaction_owner_count": len(transactions),
            "transaction_fingerprint": hashlib.sha256(canonical(transactions)).hexdigest(),
            "fixed_negative_count": len(persistence["fixed_negative_cases"]),
        },
        "materialization_closure": {
            "source_and_installed_preimage_identical_required": materialization["digest_replacement"]["equality"]["compared_preimages_must_be_byte_identical"],
            "package_manifest_excluded_from_both": materialization["digest_replacement"]["package_manifest"]["excluded_from_both_tree_digests"],
            "module_export_count": len(materialization["direct_ABI_replacement"]["plugin_module"]["exact_exports_in_order"]),
            "processToolCall_argument_count": materialization["direct_ABI_replacement"]["plugin_module"]["signatures"]["processToolCall"]["argument_count"],
            "materialization_fingerprint": hashlib.sha256(canonical(materialization)).hexdigest(),
        },
        "authority_boundary": {
            "implementation_authorized": False,
            "database_creation_authorized": False,
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
