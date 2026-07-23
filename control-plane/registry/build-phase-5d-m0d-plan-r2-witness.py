#!/usr/bin/env python3
"""Build the deterministic synthetic witness for the Phase 5D M0-D R2 plan."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


VALIDATOR_PATH = Path(__file__).with_name("validate-phase-5d-m0d-plan-r2-witness.py")


def load_validator() -> object:
    spec = importlib.util.spec_from_file_location("phase5d_r2_validator", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load R2 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} OUTPUT_PATH", file=sys.stderr)
        return 2
    validator = load_validator()
    plan, plan_errors = validator.load_plan(validator.PLAN_PATH)
    profile, profile_errors = validator.load_profile(validator.PROFILE_PATH)
    errors = plan_errors + profile_errors
    if plan is None or profile is None or errors:
        print(json.dumps({"errors": errors or ["immutable input unavailable"]}, sort_keys=True), file=sys.stderr)
        return 1
    payload = validator.expected_witness(profile)
    output = Path(argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "sha256": validator.sha256_bytes(output.read_bytes())}, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
