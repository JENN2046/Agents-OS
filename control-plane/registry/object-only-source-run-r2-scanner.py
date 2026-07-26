#!/usr/bin/env python3
"""Closed, NUL-safe protected-name scanner for Phase 5D M0-D R2.

This module is intentionally inert on import.  It accepts a bytes stream
provided by the R2 runner after a name-only Git tree listing; it never invokes
Git, opens a repository, emits a path, or reads a blob.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import sys
from typing import Final


EXPECTED_PROTECTED_PATHS: Final[tuple[bytes, ...]] = (
    b"Plugin/CodeSearcher/config.env",
    b"Plugin/DailyNote/config.env",
    b"Plugin/FileOperator/config.env",
    b"Plugin/LinuxShellExecutor/config.env",
    b"Plugin/MagiAgent/config.env",
    b"Plugin/NCBIDatasets/config.env",
    b"Plugin/PowerShellExecutor/config.env",
)
EXPECTED_PROTECTED_INVENTORY_SHA256: Final[str] = (
    "52349f79221f041a48134331666315686ed6185b0838c56c13b1e9ed3b247011"
)


class ScannerBlocked(ValueError):
    """A deliberately non-descriptive fail-closed scanner result."""


@dataclass(frozen=True)
class ScanResult:
    protected_name_count: int
    protected_name_inventory_preimage_sha256: str


def _is_protected_path(path: bytes) -> bool:
    if not path or path.startswith(b"/") or b"\x00" in path:
        return True
    components = path.split(b"/")
    if any(component in {b"", b".", b".."} for component in components):
        return True
    basename = components[-1]
    if basename == b".env" or basename.startswith(b".env."):
        return True
    if basename == b"config.env" or basename.endswith(b".pem") or basename.endswith(b".key"):
        return True
    return any(
        component in {b"credentials", b"tokens", b"cookies", b"secret", b"secrets", b"state-private"}
        for component in components
    )


def scan_name_only_stream(stream: bytes) -> ScanResult:
    """Validate a complete NUL-delimited tree-name stream without emitting it."""

    if type(stream) is not bytes or not stream.endswith(b"\x00"):
        raise ScannerBlocked("BLOCKED_PROTECTED_PATH_INVENTORY_MISMATCH")
    names = tuple(stream[:-1].split(b"\x00"))
    if any(not name for name in names) or len(names) != len(set(names)):
        raise ScannerBlocked("BLOCKED_PROTECTED_PATH_INVENTORY_MISMATCH")
    protected = tuple(name for name in names if _is_protected_path(name))
    if protected != EXPECTED_PROTECTED_PATHS:
        raise ScannerBlocked("BLOCKED_PROTECTED_PATH_INVENTORY_MISMATCH")
    digest = sha256(b"".join(name + b"\n" for name in protected)).hexdigest()
    if digest != EXPECTED_PROTECTED_INVENTORY_SHA256:
        raise ScannerBlocked("BLOCKED_PROTECTED_PATH_INVENTORY_MISMATCH")
    return ScanResult(
        protected_name_count=len(protected),
        protected_name_inventory_preimage_sha256=digest,
    )


def self_test() -> int:
    baseline = (
        b"AGENTS.md\x00"
        + b"Plugin/AGENTS.md\x00"
        + b"\x00".join(EXPECTED_PROTECTED_PATHS)
        + b"\x00docs/PLUGIN_ECOSYSTEM.md\x00"
    )
    cases = {
        "baseline": (baseline, True),
        "extra_protected": (baseline + b".env\x00", False),
        "swapped_protected": (
            b"AGENTS.md\x00"
            + EXPECTED_PROTECTED_PATHS[1]
            + b"\x00"
            + EXPECTED_PROTECTED_PATHS[0]
            + b"\x00"
            + b"\x00".join(EXPECTED_PROTECTED_PATHS[2:])
            + b"\x00",
            False,
        ),
        "missing_terminator": (baseline[:-1], False),
        "duplicate": (baseline + b"AGENTS.md\x00", False),
    }
    failures: list[str] = []
    for name, (stream, should_pass) in cases.items():
        try:
            result = scan_name_only_stream(stream)
            passed = result.protected_name_count == 7
        except ScannerBlocked:
            passed = False
        if passed is not should_pass:
            failures.append(name)
    print(json.dumps({"result": "PASS" if not failures else "BLOCKED", "cases": len(cases), "failures": failures}, sort_keys=True))
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("--self-test is the only standalone mode; the runner imports this module")
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
