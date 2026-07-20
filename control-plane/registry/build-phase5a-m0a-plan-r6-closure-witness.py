#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
R6_OWNER = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r6.yaml"
R6_PERSIST = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r6.yaml"
R6_ABI = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r6.yaml"
R6_TOTALITY = ROOT / "control-plane/registry/drafts/2026-07-19-agents-os-phase-5a-m0a-structured-input-totality-corrections-v0.1-r6.yaml"
R6_SOURCE = ROOT / "control-plane/registry/examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-inherited-abi-wrapper-v0.1.js"


class DuplicateKeyError(ValueError):
    pass


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: StrictSafeLoader, node: yaml.MappingNode, deep: bool = False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DuplicateKeyError(f"duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


StrictSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml_strict(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build() -> dict:
    owner = load_yaml_strict(R6_OWNER)
    persistence = load_yaml_strict(R6_PERSIST)
    abi = load_yaml_strict(R6_ABI)
    totality = load_yaml_strict(R6_TOTALITY)
    witness_commit = {
        "authority_epoch": 1,
        "epoch_fingerprint": f"{201:064x}",
        "incarnation_id": "inc:1",
        "ownership_event_fingerprint": f"{1:064x}",
        "ownership_event_id": "event:f3-ownership:resident:A:1",
        "ownership_event_sequence": 1,
        "resident_id": "resident:A",
        "witness_reservation_fingerprint": f"{301:064x}",
        "witness_reservation_ref": "reservation:1",
    }
    witness_bytes = canonical(witness_commit)
    return {
        "schema_version": "agents-os.phase5a-m0a-plan-r6-closure-witness.v0.1",
        "review_unit": "PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R6_ATOMIC_BUNDLE",
        "precedence": ["R6_explicit_replacements", "R5_all_other_clauses", "R4_all_other_clauses", "R3_all_other_clauses", "R2_all_other_clauses", "R1_all_other_clauses"],
        "profile_fingerprints": {
            "semantic_owner": sha(R6_OWNER),
            "persistence": sha(R6_PERSIST),
            "materialization_ABI": sha(R6_ABI),
            "structured_input_totality": sha(R6_TOTALITY),
            "safe_wrapper": sha(R6_SOURCE),
        },
        "semantic_owner_replacements": [row["obligation_id"] for row in owner["replacement_rows"]],
        "effective_schema": {
            "table_count": persistence["effective_schema"]["effective_table_count"],
            "replacement_tables": persistence["effective_schema"]["replace_R5_or_inherited_tables"],
            "immutable_triggers": ["canonical_fact_no_update", "canonical_fact_no_delete"],
        },
        "f3_witness_commit": {
            "decoded": witness_commit,
            "canonical_bytes_utf8": witness_bytes.decode("utf-8"),
            "fingerprint": hashlib.sha256(witness_bytes).hexdigest(),
            "result": "READY_ELIGIBLE",
        },
        "f5_replay": {
            "authorization_subject_ref": "attempt:A",
            "authorization_subject_revision": 1,
            "returned_identity_field_count": len(persistence["transaction_replacements"]["F5_first_apply_and_exact_replay"]["returned_identity_fields"]),
            "before_counts": {"Event": 2, "call_authorization": 1},
            "after_counts": {"Event": 2, "call_authorization": 1},
            "additional_counts": {"Event": 0, "call_authorization": 0},
        },
        "abi": {
            "source_sha256": abi["fixed_future_wrapper"]["sha256"],
            "exports": abi["effective_ABI_replacement"]["exact_exports_in_order"],
            "native_method": abi["effective_ABI_replacement"]["processToolCall"]["native_method"],
            "source_case_count": len(abi["fixed_source_cases"]["positive"]) + len(abi["fixed_source_cases"]["negative"]),
        },
        "structured_input": {
            "YAML_duplicate_result": totality["loader_contract"]["YAML"]["duplicate_mapping_key_result"],
            "JSON_duplicate_result": totality["loader_contract"]["JSON"]["duplicate_object_key_result"],
            "last_key_wins": "forbidden",
        },
        "expected_case_counts": {"SQLite": 13, "JavaScript_AST": 15, "structured_input": 7, "total": 35},
        "boundary": {
            "runtime_usable": False,
            "implementation_authorized": False,
            "database_file_created": False,
            "VCPToolBox_modified": False,
            "JavaScript_implementation_created": False,
            "plugin_enabled": False,
            "provider_called": False,
            "private_Memory_read": False,
            "sensing_started": False,
            "real_effect_occurrence_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        },
    }


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {Path(sys.argv[0]).name} OUTPUT", file=sys.stderr)
        return 2
    Path(sys.argv[1]).write_bytes(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
