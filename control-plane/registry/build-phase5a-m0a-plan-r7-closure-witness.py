#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
OWNER = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r7.yaml"
PERSISTENCE = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r7.yaml"
ABI = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r6.yaml"
TOTALITY = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-structured-input-totality-corrections-v0.1-r6.yaml"
BOUNDARY = ROOT / "control-plane/registry/drafts/2026-07-20-agents-os-phase-5a-m0a-boundary-inventory-v0.1-r7.yaml"


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
    return yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pointer_token(value: object) -> str:
    return str(value).replace("~", "~0").replace("/", "~1")


def walk(value: object, pointer: str = ""):
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{pointer}/{pointer_token(key)}"
            yield child, key, value[key]
            yield from walk(value[key], child)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child = f"{pointer}/{index}"
            yield from walk(item, child)


def collect_boundary_rows(sources: list[tuple[str, dict]], contract: dict) -> list[dict]:
    false_keys = set(contract["strict_false_boolean_keys"])
    true_keys = set(contract["strict_true_boolean_keys"])
    zero_keys = set(contract["strict_zero_integer_keys"])
    exact_strings = contract["exact_string_values"]
    rows = []
    for source_alias, document in sources:
        for pointer, key, value in walk(document):
            if key in false_keys:
                rows.append({"source": source_alias, "pointer": pointer, "key": key, "expected_type": "boolean", "expected_value": False, "observed_value": value})
            elif key in true_keys:
                rows.append({"source": source_alias, "pointer": pointer, "key": key, "expected_type": "boolean", "expected_value": True, "observed_value": value})
            elif key in zero_keys:
                rows.append({"source": source_alias, "pointer": pointer, "key": key, "expected_type": "integer", "expected_value": 0, "observed_value": value})
            elif key in exact_strings:
                rows.append({"source": source_alias, "pointer": pointer, "key": key, "expected_type": "string", "expected_value": exact_strings[key], "observed_value": value})
    return sorted(rows, key=lambda row: (row["source"], row["pointer"].encode("utf-8")))


def build() -> dict:
    owner = load_yaml(OWNER)
    persistence = load_yaml(PERSISTENCE)
    abi = load_yaml(ABI)
    totality = load_yaml(TOTALITY)
    boundary = load_yaml(BOUNDARY)
    witness_boundary = {
        "plan_frozen": False,
        "runtime_usable": False,
        "implementation_authorized": False,
        "dependency_installation_authorized": False,
        "database_file_created": False,
        "VCPToolBox_modified": False,
        "JavaScript_implementation_created": False,
        "plugin_enabled": False,
        "production_authentication_authorized": False,
        "provider_called": False,
        "private_Memory_read": False,
        "sensing_started": False,
        "real_effect_occurrence_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }
    sources = [
        ("semantic_owner_R7", owner),
        ("persistence_R7", persistence),
        ("materialization_ABI_R6", abi),
        ("structured_input_totality_R6", totality),
        ("boundary_inventory_R7", boundary),
        ("witness_boundary_R7", witness_boundary),
    ]
    rows = collect_boundary_rows(sources, boundary["closed_key_contract"])
    row_commitments = [{key: row[key] for key in ("source", "pointer", "key", "expected_type", "expected_value")} for row in rows]
    recovering = {"authority_epoch": 1, "lifecycle": "RECOVERING", "resident_id": "resident:A"}
    ready = {"authority_epoch": 1, "lifecycle": "READY", "resident_id": "resident:A"}
    return {
        "schema_version": "agents-os.phase5a-m0a-plan-r7-closure-witness.v0.1",
        "review_unit": "PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R7_ATOMIC_BUNDLE",
        "precedence": ["R7_explicit_replacements", "R6_all_other_clauses", "R5_all_other_clauses", "R4_all_other_clauses", "R3_all_other_clauses", "R2_all_other_clauses", "R1_all_other_clauses"],
        "profile_fingerprints": {
            "semantic_owner_R7": sha(OWNER),
            "persistence_R7": sha(PERSISTENCE),
            "materialization_ABI_R6": sha(ABI),
            "structured_input_totality_R6": sha(TOTALITY),
            "boundary_inventory_R7": sha(BOUNDARY),
        },
        "boundary_inventory": {
            "row_count": len(rows),
            "rows": row_commitments,
            "inventory_sha256": hashlib.sha256(canonical(row_commitments)).hexdigest(),
        },
        "f3_transition": {
            "resident_id": "resident:A",
            "authority_epoch": 1,
            "prestate": {
                "state": "RECOVERING",
                "revision": 1,
                "fact_ref": "resident-lifecycle:resident:A:1",
                "canonical_bytes_utf8": canonical(recovering).decode("utf-8"),
                "fingerprint": hashlib.sha256(canonical(recovering)).hexdigest(),
                "pointer_revision": 1,
            },
            "poststate": {
                "state": "READY",
                "revision": 2,
                "fact_ref": "resident-lifecycle:resident:A:2",
                "canonical_bytes_utf8": canonical(ready).decode("utf-8"),
                "fingerprint": hashlib.sha256(canonical(ready)).hexdigest(),
                "predecessor_revision": 1,
                "predecessor_ref": "resident-lifecycle:resident:A:1",
                "predecessor_fingerprint": hashlib.sha256(canonical(recovering)).hexdigest(),
                "pointer_revision": 2,
            },
            "atomic_writes": ["RESIDENT_READY_Event", "READY_revision_2_fact", "lifecycle_pointer_1_to_2"],
            "rollback_preserves_revision": 1,
            "direct_READY_revision_1_from_empty_history": "BLOCK",
        },
        "expected_case_counts": {"boundary": len(rows) + 6, "SQLite": 9, "total": len(rows) + 15},
        "boundary": witness_boundary,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} OUTPUT", file=sys.stderr)
        return 2
    Path(sys.argv[1]).write_bytes(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
