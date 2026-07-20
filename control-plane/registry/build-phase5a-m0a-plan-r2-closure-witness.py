#!/usr/bin/env python3
"""Build the deterministic Phase 5A M0-A plan R2 closure witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-closed-contract-obligation-inventory-v0.1-r2.yaml"
PERSISTENCE = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-exact-persistence-profile-v0.1-r2.yaml"
MATERIALIZATION = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-external-materialization-profile-v0.1-r2.yaml"
AMENDMENT = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-plan-v0.1-r2-amendment.draft.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build() -> dict:
    inventory = yaml.safe_load(INVENTORY.read_text(encoding="utf-8"))
    persistence = yaml.safe_load(PERSISTENCE.read_text(encoding="utf-8"))
    materialization = yaml.safe_load(MATERIALIZATION.read_text(encoding="utf-8"))
    subject_rows = inventory["canonical_subjects"]
    obligation_rows = inventory["obligations"]
    table_names = persistence["tables_in_creation_order"]
    fact_kinds = [
        f"{phase}:{kind}"
        for phase, kinds in persistence["canonical_fact_kind_inventory"].items()
        for kind in kinds
    ]
    witness = {
        "schema_version": "agents-os.m0a-plan-r2-closure-witness.v0.1",
        "review_unit": "PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE",
        "environment": "SYNTHETIC_PLAN_VALIDATION",
        "subject_hashes": {
            "amendment": sha(AMENDMENT),
            "contract_obligation_inventory": sha(INVENTORY),
            "exact_persistence_profile": sha(PERSISTENCE),
            "external_materialization_profile": sha(MATERIALIZATION),
        },
        "contract_closure": {
            "canonical_subject_count": len(subject_rows),
            "canonical_subject_set_fingerprint": hashlib.sha256(canonical(subject_rows)).hexdigest(),
            "phase_subject_counts": {
                phase: data["accepted_subject_count"]
                for phase, data in inventory["phase_subject_sets"].items()
            },
            "obligation_count": len(obligation_rows),
            "obligation_set_fingerprint": hashlib.sha256(canonical(obligation_rows)).hexdigest(),
            "owner_field_count_per_obligation": 8,
            "unmapped_obligation_count": 0,
        },
        "persistence_closure": {
            "inventory_is_exhaustive": persistence["database_boundary"]["inventory_is_exhaustive"],
            "table_count": len(table_names),
            "table_set_fingerprint": hashlib.sha256(canonical(table_names)).hexdigest(),
            "canonical_fact_kind_count": len(fact_kinds),
            "canonical_fact_kind_fingerprint": hashlib.sha256(canonical(fact_kinds)).hexdigest(),
            "dedicated_row_class_count": len(persistence["dedicated_row_class_mapping"]),
            "transaction_owner_count": len(persistence["transaction_owners"]),
            "crash_window_count": len(persistence["crash_windows"]),
        },
        "materialization_closure": {
            "planned_source_inventory_count": len(materialization["planned_source_inventory"]),
            "planned_source_inventory_fingerprint": hashlib.sha256(canonical(materialization["planned_source_inventory"])).hexdigest(),
            "tree_hash_algorithm": materialization["content_tree_hash"]["algorithm"],
            "blocked_manifest_fingerprint": hashlib.sha256(canonical(materialization["blocked_plugin_manifest"]["exact_value"])).hexdigest(),
            "direct_entrypoint_fingerprint": hashlib.sha256(canonical(materialization["direct_entrypoint"])).hexdigest(),
            "allowed_overlay_glob": materialization["VCPToolBox_projection"]["allowed_overlay_glob"],
        },
        "authority_boundary": {
            "implementation_authorized": False,
            "database_creation_authorized": False,
            "VCPToolBox_change_authorized": False,
            "runtime_activation_authorized": False,
            "real_effect_authorized": False,
            "terminal_outcome": "NOT_EXECUTED",
        },
    }
    witness["root_fingerprint"] = hashlib.sha256(canonical(witness)).hexdigest()
    return witness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_bytes(json.dumps(build(), ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
