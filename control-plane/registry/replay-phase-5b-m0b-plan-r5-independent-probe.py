#!/usr/bin/env python3
"""Replay the immutable Phase 5B Plan R5 independent probe from any checkout."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import pathlib


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[2]
IMMUTABLE_PROBE = (
    WORKSPACE_ROOT
    / "control-plane/registry/reviews/2026-07-21-agents-os-phase-5b-m0b-plan-r5-independent-probe.py"
)
EXPECTED_RESULTS = (
    WORKSPACE_ROOT
    / "control-plane/registry/reviews/2026-07-21-agents-os-phase-5b-m0b-plan-r5-independent-case-results.json"
)
EXPECTED_PROBE_SHA256 = "91688b7bdc0532929ad96b3519c50dd8ae66c91f59fbee584ac6cd1243a2180b"
FIXED_ROOT_LINE = "ROOT = pathlib.Path('/tmp/phase5b-r5-independent-extract/workspace')"


def main() -> int:
    probe_bytes = IMMUTABLE_PROBE.read_bytes()
    probe_sha256 = hashlib.sha256(probe_bytes).hexdigest()
    if probe_sha256 != EXPECTED_PROBE_SHA256:
        raise SystemExit(
            f"immutable probe hash mismatch: expected {EXPECTED_PROBE_SHA256}, got {probe_sha256}"
        )

    source = probe_bytes.decode("utf-8")
    if source.count(FIXED_ROOT_LINE) != 1:
        raise SystemExit("immutable probe root anchor is missing or ambiguous")
    portable_root_line = f"ROOT = pathlib.Path({str(WORKSPACE_ROOT)!r})"
    replay_source = source.replace(FIXED_ROOT_LINE, portable_root_line, 1)

    output = io.StringIO()
    namespace = {"__name__": "__main__", "__file__": str(IMMUTABLE_PROBE)}
    with contextlib.redirect_stdout(output):
        exec(compile(replay_source, str(IMMUTABLE_PROBE), "exec"), namespace)

    actual = json.loads(output.getvalue())
    expected = json.loads(EXPECTED_RESULTS.read_text(encoding="utf-8"))
    if actual != expected:
        raise SystemExit("portable replay output does not match immutable case results")

    print(
        json.dumps(
            {
                "schema_version": "agents-os.independent-probe-portable-replay.v0.1",
                "result": "PASS",
                "workspace_root": str(WORKSPACE_ROOT),
                "immutable_probe_sha256": probe_sha256,
                "case_result_rows": len(actual["rows"]),
                "case_results_match": True,
            },
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
