#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r7.yaml"
PERSISTENCE = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-persistence-ownership-event-closure-v0.1-r8.yaml"
ABI = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r6.yaml"
TOTALITY = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-structured-input-totality-corrections-v0.1-r6.yaml"
CONTRACT = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-closed-key-contract-v0.1-r8.yaml"


class DuplicateKeyError(ValueError):
    pass


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise DuplicateKeyError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(path: Path) -> dict:
    value = yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)
    if not isinstance(value, dict):
        raise ValueError(f"root mapping required: {path}")
    return value


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pointer_token(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def walk_key_paths(value: object, pointer: str = ""):
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{pointer}/{pointer_token(key)}"
            yield child, key
            yield from walk_key_paths(value[key], child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk_key_paths(item, f"{pointer}/{index}")


def boundary_seed() -> dict:
    return {
        "JavaScript_implementation_created": False,
        "VCPToolBox_modified": False,
        "database_file_created": False,
        "dependency_installation_authorized": False,
        "implementation_authorized": False,
        "plan_frozen": False,
        "plugin_enabled": False,
        "private_Memory_read": False,
        "production_authentication_authorized": False,
        "provider_called": False,
        "real_effect_occurrence_count": 0,
        "runtime_usable": False,
        "sensing_started": False,
        "terminal_outcome": "NOT_EXECUTED",
    }


def source_documents() -> list[tuple[str, dict]]:
    return [
        ("semantic_owner_R7", load_yaml(OWNER)),
        ("persistence_ownership_R8", load_yaml(PERSISTENCE)),
        ("materialization_ABI_R6", load_yaml(ABI)),
        ("structured_input_totality_R6", load_yaml(TOTALITY)),
        ("boundary_contract_R8", load_yaml(CONTRACT)),
        ("witness_boundary_R8", boundary_seed()),
    ]


def collect_key_rows(sources: list[tuple[str, dict]]) -> list[dict]:
    rows = []
    for alias, document in sources:
        rows.extend({"source": alias, "pointer": pointer, "key": key} for pointer, key in walk_key_paths(document))
    source_order = {alias: index for index, (alias, _document) in enumerate(sources)}
    return sorted(rows, key=lambda row: (source_order[row["source"]], row["pointer"].encode("utf-8")))


def build() -> dict:
    contract = load_yaml(CONTRACT)
    sources = source_documents()
    rows = collect_key_rows(sources)
    key_inventory_sha256 = hashlib.sha256(canonical(rows)).hexdigest()
    recovering = {"authority_epoch": 1, "lifecycle": "RECOVERING", "resident_id": "resident:A"}
    ready = {"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"}
    ownership_event = {
        "aggregate_ref": "resident:A",
        "aggregate_revision": 1,
        "event_fingerprint": f"{1:064x}",
        "event_id": "event:f3-ownership:resident:A:1",
        "event_kind": "RESIDENT_OWNERSHIP_STARTED",
        "event_sequence": 1,
    }
    return {
        "schema_version": "agents-os.phase5a-m0a-plan-r8-closure-witness.v0.1",
        "review_unit": "PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R8_ATOMIC_BUNDLE",
        "precedence": [
            "R8_explicit_replacements", "R7_all_other_clauses", "R6_all_other_clauses",
            "R5_all_other_clauses", "R4_all_other_clauses", "R3_all_other_clauses",
            "R2_all_other_clauses", "R1_all_other_clauses",
        ],
        "profile_fingerprints": {
            "semantic_owner_R7": sha(OWNER),
            "persistence_ownership_R8": sha(PERSISTENCE),
            "materialization_ABI_R6": sha(ABI),
            "structured_input_totality_R6": sha(TOTALITY),
            "boundary_contract_R8": sha(CONTRACT),
        },
        "sealed_source_commitments": contract["sealed_source_commitments"],
        "complete_key_path_inventory": {
            "row_count": len(rows),
            "rows": rows,
            "inventory_sha256": key_inventory_sha256,
        },
        "f3_transition": {
            "resident_id": "resident:A",
            "authority_epoch": 1,
            "ownership_event": ownership_event,
            "prestate": {
                "state": "RECOVERING",
                "revision": 1,
                "fact_ref": "resident-lifecycle:resident:A:1",
                "canonical_bytes_utf8": canonical(recovering).decode("utf-8"),
                "fingerprint": hashlib.sha256(canonical(recovering)).hexdigest(),
                "fact_created_event_sequence": 1,
                "pointer_revision": 1,
                "pointer_updated_event_sequence": 1,
            },
            "poststate": {
                "state": "READY",
                "revision": 2,
                "fact_ref": "resident-lifecycle:resident:A:2",
                "canonical_bytes_utf8": canonical(ready).decode("utf-8"),
                "fingerprint": hashlib.sha256(canonical(ready)).hexdigest(),
                "created_event_sequence": 3,
                "predecessor_revision": 1,
                "predecessor_ref": "resident-lifecycle:resident:A:1",
                "predecessor_fingerprint": hashlib.sha256(canonical(recovering)).hexdigest(),
                "pointer_revision": 2,
                "pointer_updated_event_sequence": 3,
            },
            "atomic_writes": ["RESIDENT_READY_Event", "READY_revision_2_fact", "lifecycle_pointer_1_to_2"],
            "rollback_preserves_revision": 1,
            "sequence_2_RECOVERING_prestate": "BLOCK",
            "direct_READY_revision_1_from_empty_history": "BLOCK",
        },
        "expected_case_counts": {"closed_key": 6, "SQLite": 13, "total": 19},
        "boundary": boundary_seed(),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} OUTPUT", file=sys.stderr)
        return 2
    Path(sys.argv[1]).write_bytes(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
