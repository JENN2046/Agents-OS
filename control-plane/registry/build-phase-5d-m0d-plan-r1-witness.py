#!/usr/bin/env python3
"""Build the deterministic synthetic Phase 5D M0-D Plan R1 witness."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml


PROFILE_PATH = Path(
    "control-plane/registry/drafts/"
    "2026-07-23-agents-os-phase-5d-m0d-quarantined-host-smoke-build-profile-v0.1-r1.yaml"
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def build(profile: dict[str, object]) -> dict[str, object]:
    baseline = profile["baseline"]
    quarantine = profile["quarantine_contract"]
    smoke = profile["future_smoke_contract"]
    state_machine = profile["state_machine"]
    commitments = profile["sealed_host_commitments"]
    return {
        "authorization": profile["authorization"],
        "baseline": {
            "VCPToolBox_sealed_commit": baseline["VCPToolBox_sealed_commit"],
            "VCPToolBox_sealed_tree": baseline["VCPToolBox_sealed_tree"],
            "baseline_main_commit": baseline["baseline_main_commit"],
            "blocked_plugin_manifest_sha256": baseline["blocked_plugin_manifest_sha256"],
            "inert_commonjs_entrypoint_sha256": baseline[
                "inert_commonjs_entrypoint_sha256"
            ],
            "package_manifest_sha256": baseline["package_manifest_sha256"],
            "repository": baseline["repository"],
            "source_payload_commit": baseline["source_payload_commit"],
            "source_root": baseline["source_root"],
        },
        "claimed_decision": smoke["current_plan_result"],
        "environment": "SYNTHETIC_PLAN_ONLY",
        "quarantine_contract": {
            "caller_selected_source_host_output_manifest_or_config_path": quarantine[
                "caller_selected_source_host_output_manifest_or_config_path"
            ],
            "environment": quarantine["environment"],
            "existing_root_or_residue": quarantine["existing_root_or_residue"],
            "transient_enabled_manifest": quarantine["transient_enabled_manifest"],
            "workspace_enabled_manifest": quarantine["workspace_enabled_manifest"],
        },
        "real_occurrence_count": 0,
        "runtime_usable": False,
        "schema_version": "agents-os.m0d-synthetic-plan-witness.v0.1",
        "sealed_host_commitments": commitments,
        "sealed_host_commitments_sha256": hashlib.sha256(
            canonical_bytes(commitments)
        ).hexdigest(),
        "smoke_contract": {
            "expected_initialize_result": smoke["expected_initialize_result"],
            "expected_shutdown_result": smoke["expected_shutdown_result"],
            "host_lifecycle_argument_contract": smoke[
                "host_lifecycle_argument_contract"
            ],
            "lifecycle_methods_allowed_only": smoke[
                "lifecycle_methods_allowed_only"
            ],
            "native_NAPI_methods_allowed": smoke["native_NAPI_methods_allowed"],
            "processToolCall_or_native_addon_load": smoke[
                "processToolCall_or_native_addon_load"
            ],
        },
        "state_machine": {
            "allowed_sequence": state_machine["allowed_sequence"],
            "current_terminal_state": state_machine["current_terminal_state"],
            "observed_sequence": ["NOT_STARTED"],
        },
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} OUTPUT_PATH", file=sys.stderr)
        return 2
    profile = yaml.safe_load(PROFILE_PATH.read_text(encoding="utf-8"))
    output = Path(argv[1])
    output.write_text(
        json.dumps(build(profile), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
