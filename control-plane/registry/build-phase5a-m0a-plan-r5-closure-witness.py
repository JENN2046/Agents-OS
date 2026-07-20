#!/usr/bin/env python3
"""Build the deterministic synthetic Plan R5 closure witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "control-plane/registry"
FILES = {
    "amendment": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-plan-v0.1-r5-amendment.draft.md",
    "owners": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-semantic-owner-corrections-v0.1-r5.yaml",
    "persistence": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-persistence-transaction-corrections-v0.1-r5.yaml",
    "abi": REG / "drafts/2026-07-19-agents-os-phase-5a-m0a-materialization-abi-corrections-v0.1-r5.yaml",
    "safe_index_js": REG / "examples/2026-07-19-agents-os-phase-5a-m0a-future-index-js-safe-wrapper-v0.1.js",
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def fingerprint(value: object) -> str:
    return sha_bytes(canonical(value))


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def source_cases(safe_source: str) -> list[dict]:
    negatives = {
        "second_formal_parameter": safe_source.replace("processToolCall(args)", "processToolCall(args, directContext)"),
        "arguments_index_one": safe_source.replace("const nativeFrame = projectArgs(args);", "const nativeFrame = projectArgs(args);\n  const ctx = arguments[1];"),
        "rest_parameter": safe_source.replace("processToolCall(args)", "processToolCall(args, ...rest)"),
        "direct_requestIp": safe_source.replace("payload: args.payload", "payload: args.requestIp"),
        "context_alias": safe_source.replace("const nativeFrame = projectArgs(args);", "const directContext = arguments[1];\n  const nativeFrame = projectArgs(args);"),
        "closure_capture": safe_source.replace("return residentNative.process(nativeFrame);", "const leak = () => arguments[1];\n  return residentNative.process(nativeFrame);"),
        "object_spread": safe_source.replace("payload: args.payload", "...args"),
        "computed_property": safe_source.replace("args.payload", "args['payload']"),
        "helper_call": safe_source.replace("projectArgs(args)", "helper(args)", 1),
        "extra_native_argument": safe_source.replace("residentNative.process(nativeFrame)", "residentNative.process(nativeFrame, arguments[1])"),
        "returned_context": safe_source.replace("return residentNative.process(nativeFrame);", "return arguments[1];"),
        "unsupported_optional_chaining": safe_source.replace("args.payload", "args?.payload"),
    }
    rows = [{"case_id": "exact_safe_wrapper", "expected": "ACCEPT", "source": safe_source}]
    rows.extend({"case_id": name, "expected": "BLOCK", "source": source} for name, source in negatives.items())
    return rows


def build() -> dict:
    owners = load_yaml(FILES["owners"])
    persistence = load_yaml(FILES["persistence"])
    abi = load_yaml(FILES["abi"])
    safe_bytes = FILES["safe_index_js"].read_bytes()
    safe_source = safe_bytes.decode("utf-8")

    sections = {
        "fixed_sources": {
            name: {"path": path.relative_to(ROOT).as_posix(), "sha256": sha_bytes(path.read_bytes())}
            for name, path in FILES.items()
        },
        "lineage": {
            "R1_manifest_sha256": "01900e4bf161d613b4f0928add8c3d35e6b309bacf4379767bf1642e406c91ef",
            "R2_manifest_sha256": "48b5e53032e5d6bf527ff542febf20b4c9e940a6d5ab48c6960eb5bcd2bd0f26",
            "R3_manifest_sha256": "d9af2c8b8f8e469edf64d6897f16e1730d32897a7f9ea1333f1a3b2efb194c49",
            "R4_manifest_sha256": "0803bd3e90a0652f1e0cc97b9a4168185df37cd9c76506746796e6096d3dbe58",
            "R4_review_sha256": "38d7000d568c1f97028bc38689960e7026c0f79d07e77944e4d69856e64ee79f",
        },
        "semantic_owner_replacements": owners["replacement_rows"],
        "persistence": {
            "effective_table_count": persistence["effective_schema"]["effective_table_count"],
            "replacement_tables": persistence["effective_schema"]["replace_R4_or_inherited_tables"],
            "transactions": persistence["transaction_replacements"],
            "fixed_SQLite_cases": persistence["fixed_SQLite_cases"],
        },
        "ast_dataflow": {
            "contract": abi["validator_contract"],
            "safe_source_sha256": sha_bytes(safe_bytes),
            "source_cases": source_cases(safe_source),
        },
        "boundary": {
            "synthetic_only": True,
            "runtime_usable": False,
            "implementation_authorized": False,
            "database_file_occurrence_count": 0,
            "VCPToolBox_change_occurrence_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        },
    }
    section_fingerprints = {name: fingerprint(value) for name, value in sections.items()}
    root = {
        "schema_version": "agents-os.phase5a-m0a-plan-r5-closure-witness.v0.1",
        "review_unit": "PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R5_ATOMIC_BUNDLE",
        "sections": sections,
        "section_fingerprints": section_fingerprints,
    }
    root["root_fingerprint"] = fingerprint(root)
    return root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build(), ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
