#!/usr/bin/env python3
"""Build the deterministic F7 R2 decision-case inventory witness."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


R1_FIXTURE = Path("control-plane/registry/examples/2026-07-18-agents-os-f7-r1-home-domain-minimum-semantics-v0.1.json")
DEFAULT_OUTPUT = Path("control-plane/registry/examples/2026-07-19-agents-os-f7-r2-decision-case-inventory-closure-v0.1.json")
DOMAIN = "F7_R2_DECISION_CASE_INVENTORY_SYNTHETIC_NONAUTHORITY"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(tag: str, value: Any) -> str:
    return hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def sign_anchor(row: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(row)
    result["anchor_fingerprint"] = digest(DOMAIN + ":case-anchor", result)
    return result


def build_fixture(r1_path: Path = R1_FIXTURE) -> dict[str, Any]:
    r1_bytes = r1_path.read_bytes()
    r1 = json.loads(r1_bytes)
    anchors = []
    for ordinal, case in enumerate(r1["decision_cases"], start=1):
        anchors.append(sign_anchor({
            "ordinal": ordinal,
            "case_id": case["case_id"],
            "raw_input": case["raw_input"],
            "derived_decision": case["claimed_decision"],
            "r1_row_fingerprint": case["row_fingerprint"],
        }))
    fixture: dict[str, Any] = {
        "schema_version": "agents-os.f7-r2-decision-case-inventory-witness.v0.1",
        "amendment_id": "F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R2",
        "environment": "SYNTHETIC_TEST",
        "domain_tag": DOMAIN,
        "runtime_usable": False,
        "r1_fixture_sha256": hashlib.sha256(r1_bytes).hexdigest(),
        "r1_root_fingerprint": r1["root_fingerprint"],
        "decision_case_anchors": anchors,
        "catalog_fingerprint": digest(DOMAIN + ":catalog", anchors),
        "boundary_assertions": {
            "real_home_fact_count": 0,
            "private_raw_memory_count": 0,
            "sensing_or_recording_count": 0,
            "Task_or_Command_mutation_count": 0,
            "database_write_count": 0,
            "provider_call_count": 0,
            "external_effect_count": 0,
            "terminal_outcome": "NOT_EXECUTED",
        },
    }
    fixture["root_fingerprint"] = digest(DOMAIN + ":root", fixture)
    return fixture


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r1-fixture", type=Path, default=R1_FIXTURE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    fixture = build_fixture(args.r1_fixture)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
