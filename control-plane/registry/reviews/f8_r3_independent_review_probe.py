#!/usr/bin/env python3
"""Independent F8 R3 coordinated re-signing probe.

The probe reads a supplied F8 R3 review ZIP, safely extracts it, imports the
package-local R3 validator as fixed review subject, and applies independent
mutations to deep copies of the R3 fixture. It never edits the review package.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
from typing import Any
import zipfile


FAVORABLE_RESULTS = {"CANDIDATE_FORMED", "ACKNOWLEDGED_COMMITTED"}
FAIL_CLOSED_RESULTS = {
    "REJECTED", "INDETERMINATE", "ACKNOWLEDGED_INDETERMINATE",
    "ACKNOWLEDGED_REJECTED", "NOT_SUBMITTED",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_extract(zip_path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(zip_path) as archive:
        seen: set[str] = set()
        for info in archive.infolist():
            name = info.filename
            pure = PurePosixPath(name)
            mode = (info.external_attr >> 16) & 0o170000
            if (
                name in seen
                or pure.is_absolute()
                or any(part in {"", ".."} for part in pure.parts)
                or "\\" in name
                or mode == stat.S_IFLNK
            ):
                raise ValueError(f"unsafe ZIP entry: {name!r}")
            seen.add(name)
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        archive.extractall(destination)
    package = destination / "F8-R3-review-package"
    if not package.is_dir():
        raise ValueError("package root missing")
    return package


def load_validator(package: Path):
    path = package / "validator" / "validate-f8-r3-witness.py"
    spec = importlib.util.spec_from_file_location("f8_r3_validator_subject", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load R3 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Runner:
    def __init__(self, validator: Any, fixture: dict[str, Any]):
        self.v = validator
        self.base = fixture
        self.records: list[dict[str, Any]] = []

    def assessment(self, fixture: dict[str, Any], assessment_id: str) -> dict[str, Any]:
        return next(
            row for row in fixture["owner_assessments"]
            if row["assessment_id"] == assessment_id
        )

    def commitment(self, fixture: dict[str, Any], assessment_id: str) -> dict[str, Any]:
        return next(
            row for row in fixture["owner_assessment_revision_commitments"]
            if row["assessment_id"] == assessment_id
        )

    def consumers(self, fixture: dict[str, Any]):
        for case in fixture.get("candidate_formation_cases", []):
            yield case["assessment_consumer"]
        for case in fixture.get("acknowledgement_cases", []):
            yield case["raw_input"]["F3_outcome_consumer"]

    def recompute_commitment(self, row: dict[str, Any]) -> None:
        v = self.v
        row["issued_event_fingerprint"] = v.digest(
            v.DOMAIN + ":owner-event",
            {
                "owner_contract": row["owner_contract"],
                "assessment_id": row["assessment_id"],
                "assessment_revision": row["assessment_revision"],
                "assessment_fingerprint": row["assessment_fingerprint"],
                "event_ref": row["issued_event_ref"],
                "event_sequence": row["issued_event_sequence"],
            },
        )
        row["commitment_fingerprint"] = v.digest(
            v.DOMAIN + ":owner-commitment",
            v.without(row, "commitment_fingerprint"),
        )

    def propagate_assessment_and_commitment(
        self,
        fixture: dict[str, Any],
        assessment_id: str,
        assessment_mutator=None,
        commitment_mutator=None,
    ) -> None:
        v = self.v
        assessment = self.assessment(fixture, assessment_id)
        if assessment_mutator is not None:
            assessment_mutator(assessment)
        assessment["row_fingerprint"] = v.digest(
            v.DOMAIN + ":assessment",
            v.without(assessment, "row_fingerprint"),
        )
        commitment = self.commitment(fixture, assessment_id)
        commitment["assessment_fingerprint"] = assessment["row_fingerprint"]
        if commitment_mutator is not None:
            commitment_mutator(commitment)
        self.recompute_commitment(commitment)
        for binding in self.consumers(fixture):
            if binding.get("assessment_id") == assessment_id:
                binding.update(
                    {
                        "expected_assessment_revision": assessment["assessment_revision"],
                        "expected_assessment_fingerprint": assessment["row_fingerprint"],
                        "owner_commitment_ref": commitment["commitment_ref"],
                        "expected_owner_commitment_revision": commitment["commitment_revision"],
                        "expected_owner_commitment_fingerprint": commitment[
                            "commitment_fingerprint"
                        ],
                    }
                )
        v.resign_fixture(fixture)

    def outer_resign(self, fixture: dict[str, Any]) -> None:
        """Recompute outer commitments without auto-repairing malformed fields."""
        v = self.v
        for row in fixture.get("schema_inventory", []):
            if isinstance(row, dict) and "row_fingerprint" in row:
                row["row_fingerprint"] = v.digest(
                    v.DOMAIN + ":schema-profile", v.without(row, "row_fingerprint")
                )
        for row in fixture.get("owner_assessments", []):
            if isinstance(row, dict) and "row_fingerprint" in row:
                row["row_fingerprint"] = v.digest(
                    v.DOMAIN + ":assessment", v.without(row, "row_fingerprint")
                )
        for row in fixture.get("owner_assessment_revision_commitments", []):
            if isinstance(row, dict) and "commitment_fingerprint" in row:
                row["commitment_fingerprint"] = v.digest(
                    v.DOMAIN + ":owner-commitment",
                    v.without(row, "commitment_fingerprint"),
                )
        for row in fixture.get("canonical_candidate_history", []):
            if isinstance(row, dict) and "candidate_fingerprint" in row:
                row["candidate_fingerprint"] = v.digest(
                    v.DOMAIN + ":candidate-history",
                    v.without(row, "candidate_fingerprint"),
                )
        for case in fixture.get("candidate_formation_cases", []):
            if isinstance(case, dict) and "row_fingerprint" in case:
                case["row_fingerprint"] = v.digest(
                    v.DOMAIN + ":formation-case", v.without(case, "row_fingerprint")
                )
        for case in fixture.get("acknowledgement_cases", []):
            if isinstance(case, dict) and "row_fingerprint" in case:
                case["row_fingerprint"] = v.digest(
                    v.DOMAIN + ":ack-case", v.without(case, "row_fingerprint")
                )
        sections = fixture.get("section_fingerprints")
        if isinstance(sections, dict):
            for name in v.SECTION_NAMES:
                if name in fixture:
                    sections[name] = v.digest(
                        v.DOMAIN + ":section:" + name, fixture[name]
                    )
        if "root_fingerprint" in fixture:
            body = copy.deepcopy(fixture)
            body.pop("root_fingerprint")
            fixture["root_fingerprint"] = v.digest(v.DOMAIN + ":root", body)

    @staticmethod
    def target_result(fixture: dict[str, Any], target: str | None) -> str | None:
        if target is None:
            return None
        kind, case_id = target.split(":", 1)
        rows = (
            fixture["candidate_formation_cases"]
            if kind == "formation"
            else fixture["acknowledgement_cases"]
        )
        row = next(case for case in rows if case["case_id"] == case_id)
        return row["claimed_decision"]["result"]

    def record(
        self,
        attack_id: str,
        title: str,
        fixture: dict[str, Any],
        *,
        expectation: str,
        target: str | None = None,
        expected_error: str | None = None,
        category: str = "attack",
        dependency_propagation: str = "all intended dependent fingerprints re-signed",
        notes: str = "",
    ) -> None:
        exception = None
        try:
            errors = self.v.validate_fixture(
                fixture, enforce_inventory_anchors=False
            )
        except Exception as exc:  # must never happen for a passing probe
            errors = []
            exception = f"{type(exc).__name__}: {exc}"
        valid = not errors and exception is None
        target_result = self.target_result(fixture, target)
        target_favorable = target_result in FAVORABLE_RESULTS

        if expectation == "REJECT_GRAPH":
            passed = (
                not valid
                and exception is None
                and (
                    expected_error is None
                    or any(expected_error in error for error in errors)
                )
            )
        elif expectation == "ACCEPT_FAIL_CLOSED":
            passed = valid and target_result in FAIL_CLOSED_RESULTS
        elif expectation == "ACCEPT_FAVORABLE":
            passed = valid and target_result in FAVORABLE_RESULTS
        elif expectation == "ACCEPT_VALID":
            passed = valid
        elif expectation == "NORMATIVE_ACCEPT_FAIL_CLOSED":
            passed = valid and target_result in FAIL_CLOSED_RESULTS
        else:
            raise ValueError(expectation)

        favorable_invalid = (
            valid
            and target_favorable
            and expectation not in {"ACCEPT_FAVORABLE", "ACCEPT_VALID"}
        )
        contract_mismatch = (
            expectation == "NORMATIVE_ACCEPT_FAIL_CLOSED" and not passed
        )
        self.records.append(
            {
                "attack_id": attack_id,
                "title": title,
                "category": category,
                "expectation": expectation,
                "target": target,
                "target_result": target_result,
                "accepted_by_validator": valid,
                "target_favorable": target_favorable,
                "favorable_invalid_path": favorable_invalid,
                "contract_mismatch": contract_mismatch,
                "passed": passed,
                "expected_error": expected_error,
                "errors": errors,
                "exception": exception,
                "dependency_propagation": dependency_propagation,
                "notes": notes,
            }
        )

    def null_consumer(self) -> dict[str, None]:
        return {key: None for key in self.v.CONSUMER_FIELDS}

    def run(self) -> list[dict[str, Any]]:
        v = self.v
        b = self.base

        # A01: row rewrite with immutable commitment left untouched.
        f = copy.deepcopy(b)
        row = self.assessment(f, "A-F7-STALE")
        row["result"] = "CURRENT_ACCEPTED"
        row["is_current_head"] = True
        row["row_fingerprint"] = v.digest(
            v.DOMAIN + ":assessment", v.without(row, "row_fingerprint")
        )
        for binding in self.consumers(f):
            if binding.get("assessment_id") == "A-F7-STALE":
                binding["expected_assessment_fingerprint"] = row["row_fingerprint"]
        v.resign_fixture(f)
        self.record(
            "A01", "same-revision F7 row rewrite with consumer propagation",
            f, expectation="ACCEPT_FAIL_CLOSED", target="formation:CF02",
            expected_error="OWNER_COMMITMENT_ASSESSMENT_MISMATCH",
        )

        # A02: row and owner commitment fully rewritten.
        f = copy.deepcopy(b)
        self.propagate_assessment_and_commitment(
            f, "A-F7-STALE",
            assessment_mutator=lambda r: (
                r.__setitem__("result", "CURRENT_ACCEPTED"),
                r.__setitem__("is_current_head", True),
            ),
        )
        self.record(
            "A02", "same-revision F7 row and owner commitment full rewrite",
            f, expectation="REJECT_GRAPH", target="formation:CF02",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        # A03/A04: equivalent F3 outcome attacks.
        f = copy.deepcopy(b)
        row = self.assessment(f, "A-F3-INDETERMINATE")
        row["result"] = "SYNTHETIC_TEST_COMMITTED"
        row["row_fingerprint"] = v.digest(
            v.DOMAIN + ":assessment", v.without(row, "row_fingerprint")
        )
        for binding in self.consumers(f):
            if binding.get("assessment_id") == "A-F3-INDETERMINATE":
                binding["expected_assessment_fingerprint"] = row["row_fingerprint"]
        v.resign_fixture(f)
        self.record(
            "A03", "same-revision F3 outcome rewrite with consumer propagation",
            f, expectation="ACCEPT_FAIL_CLOSED", target="ack:ACK04",
            expected_error="OWNER_COMMITMENT_ASSESSMENT_MISMATCH",
        )

        f = copy.deepcopy(b)
        self.propagate_assessment_and_commitment(
            f, "A-F3-INDETERMINATE",
            assessment_mutator=lambda r: r.__setitem__(
                "result", "SYNTHETIC_TEST_COMMITTED"
            ),
        )
        self.record(
            "A04", "same-revision F3 outcome and owner commitment full rewrite",
            f, expectation="REJECT_GRAPH", target="ack:ACK04",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        # A05-A09: commitment substitutions and caller-created source record.
        f = copy.deepcopy(b)
        commitment = self.commitment(f, "A-F3-EQUAL")
        commitment["commitment_ref"] = "synthetic://attacker/commitment/equal@1"
        self.recompute_commitment(commitment)
        for binding in self.consumers(f):
            if binding.get("assessment_id") == "A-F3-EQUAL":
                binding["owner_commitment_ref"] = commitment["commitment_ref"]
                binding["expected_owner_commitment_fingerprint"] = commitment[
                    "commitment_fingerprint"
                ]
        v.resign_fixture(f)
        self.record(
            "A05", "owner commitment ref substitution",
            f, expectation="REJECT_GRAPH", target="ack:ACK01",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        f = copy.deepcopy(b)
        commitment = self.commitment(f, "A-F3-EQUAL")
        commitment["commitment_revision"] = 2
        commitment["predecessor_commitment_ref"] = "synthetic://attacker/previous@1"
        commitment["predecessor_commitment_fingerprint"] = "1" * 64
        self.recompute_commitment(commitment)
        for binding in self.consumers(f):
            if binding.get("assessment_id") == "A-F3-EQUAL":
                binding["expected_owner_commitment_revision"] = 2
                binding["expected_owner_commitment_fingerprint"] = commitment[
                    "commitment_fingerprint"
                ]
        v.resign_fixture(f)
        self.record(
            "A06", "owner commitment revision/predecessor substitution",
            f, expectation="REJECT_GRAPH", target="ack:ACK01",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        f = copy.deepcopy(b)
        commitment = self.commitment(f, "A-F3-EQUAL")
        commitment["issued_event_ref"] = "synthetic://attacker/event/777"
        commitment["issued_event_sequence"] = 777
        self.recompute_commitment(commitment)
        for binding in self.consumers(f):
            if binding.get("assessment_id") == "A-F3-EQUAL":
                binding["expected_owner_commitment_fingerprint"] = commitment[
                    "commitment_fingerprint"
                ]
        v.resign_fixture(f)
        self.record(
            "A07", "owner Event commitment substitution",
            f, expectation="REJECT_GRAPH", target="ack:ACK01",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        f = copy.deepcopy(b)
        assessment = self.assessment(f, "A-F3-EQUAL")
        commitment = self.commitment(f, "A-F3-INDETERMINATE")
        commitment["assessment_id"] = assessment["assessment_id"]
        commitment["assessment_revision"] = assessment["assessment_revision"]
        commitment["assessment_fingerprint"] = assessment["row_fingerprint"]
        self.recompute_commitment(commitment)
        binding = f["acknowledgement_cases"][3]["raw_input"]["F3_outcome_consumer"]
        binding.update(
            {
                "assessment_id": assessment["assessment_id"],
                "expected_assessment_revision": assessment["assessment_revision"],
                "expected_assessment_fingerprint": assessment["row_fingerprint"],
                "owner_commitment_ref": commitment["commitment_ref"],
                "expected_owner_commitment_revision": commitment["commitment_revision"],
                "expected_owner_commitment_fingerprint": commitment[
                    "commitment_fingerprint"
                ],
            }
        )
        v.resign_fixture(f)
        self.record(
            "A08", "owner commitment rebound to another assessment",
            f, expectation="REJECT_GRAPH", target="ack:ACK04",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        f = copy.deepcopy(b)
        assessment = self.assessment(f, "A-F3-EQUAL")
        new_commitment = v.owner_commitment(assessment)
        new_commitment["commitment_ref"] = (
            "synthetic://attacker/assessment-commitment/new@1"
        )
        self.recompute_commitment(new_commitment)
        old = self.commitment(f, "A-F3-EQUAL")
        index = f["owner_assessment_revision_commitments"].index(old)
        f["owner_assessment_revision_commitments"][index] = new_commitment
        for binding in self.consumers(f):
            if binding.get("assessment_id") == "A-F3-EQUAL":
                binding["owner_commitment_ref"] = new_commitment["commitment_ref"]
                binding["expected_owner_commitment_fingerprint"] = new_commitment[
                    "commitment_fingerprint"
                ]
        v.resign_fixture(f)
        self.record(
            "A09", "caller-created commitment absent from trusted owner source",
            f, expectation="REJECT_GRAPH", target="ack:ACK01",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        # A10: independently reconstruct phantom input against absent history.
        f = copy.deepcopy(b)
        source = f["acknowledgement_cases"][4]["raw_input"]
        f["acknowledgement_cases"][0]["raw_input"] = copy.deepcopy(source)
        f["acknowledgement_cases"][0]["claimed_decision"] = v.derive_ack(
            f["acknowledgement_cases"][0]["raw_input"],
            f["owner_assessments"],
            f["owner_assessment_revision_commitments"],
            f["canonical_candidate_history"],
        )
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A10", "candidate absent from canonical history",
            f, expectation="ACCEPT_FAIL_CLOSED", target="ack:ACK01",
        )

        # A11: add phantom candidate and propagate all dependent evidence.
        f = copy.deepcopy(b)
        phantom = {
            "candidate_id": "synthetic://f8/handoff-candidate/phantom",
            "candidate_ref": "synthetic://f8/handoff-candidate/phantom@9",
            "candidate_revision": 9,
            "predecessor_ref": f["canonical_candidate_history"][-1]["candidate_ref"],
            "predecessor_fingerprint": f["canonical_candidate_history"][-1][
                "candidate_fingerprint"
            ],
            "runtime_usable": False,
            "command_authority": False,
        }
        phantom = v.signed(
            v.DOMAIN + ":candidate-history", phantom, "candidate_fingerprint"
        )
        f["canonical_candidate_history"].append(phantom)
        assessment = self.assessment(f, "A-F3-PHANTOM")
        assessment["subject_fingerprint"] = phantom["candidate_fingerprint"]
        assessment["context_fingerprint"] = v.candidate_context(
            phantom["candidate_ref"], 9, phantom["candidate_fingerprint"]
        )
        assessment["row_fingerprint"] = v.digest(
            v.DOMAIN + ":assessment", v.without(assessment, "row_fingerprint")
        )
        commitment = self.commitment(f, "A-F3-PHANTOM")
        commitment["assessment_fingerprint"] = assessment["row_fingerprint"]
        self.recompute_commitment(commitment)
        raw = f["acknowledgement_cases"][4]["raw_input"]
        raw["handoff_candidate_fingerprint"] = phantom["candidate_fingerprint"]
        raw["F3_outcome_consumer"]["expected_assessment_fingerprint"] = assessment[
            "row_fingerprint"
        ]
        raw["F3_outcome_consumer"][
            "expected_owner_commitment_fingerprint"
        ] = commitment["commitment_fingerprint"]
        v.resign_fixture(f)
        self.record(
            "A11", "phantom candidate added to caller graph with full propagation",
            f, expectation="REJECT_GRAPH", target="ack:ACK05",
            expected_error="trusted source mismatch",
        )

        # A12: rewrite canonical candidate and all F3 dependencies.
        f = copy.deepcopy(b)
        candidate = f["canonical_candidate_history"][1]
        candidate["candidate_id"] = "synthetic://f8/handoff-candidate/attacker"
        v.resign_fixture(f, derive_decisions=False)
        candidate_fingerprint = f["canonical_candidate_history"][1][
            "candidate_fingerprint"
        ]
        for assessment in f["owner_assessments"]:
            if (
                assessment["assessment_kind"] == "F3_INTAKE_OUTCOME"
                and assessment["subject_ref"] == candidate["candidate_ref"]
            ):
                assessment["subject_fingerprint"] = candidate_fingerprint
                assessment["context_fingerprint"] = v.candidate_context(
                    candidate["candidate_ref"],
                    candidate["candidate_revision"],
                    candidate_fingerprint,
                )
                assessment["row_fingerprint"] = v.digest(
                    v.DOMAIN + ":assessment",
                    v.without(assessment, "row_fingerprint"),
                )
                commitment = self.commitment(f, assessment["assessment_id"])
                commitment["assessment_fingerprint"] = assessment["row_fingerprint"]
                self.recompute_commitment(commitment)
                for binding in self.consumers(f):
                    if binding.get("assessment_id") == assessment["assessment_id"]:
                        binding["expected_assessment_fingerprint"] = assessment[
                            "row_fingerprint"
                        ]
                        binding[
                            "expected_owner_commitment_fingerprint"
                        ] = commitment["commitment_fingerprint"]
        for case in f["acknowledgement_cases"]:
            raw = case["raw_input"]
            if (
                raw["handoff_candidate_ref"] == candidate["candidate_ref"]
                and raw["handoff_candidate_revision"] == 2
            ):
                raw["handoff_candidate_fingerprint"] = candidate_fingerprint
        v.resign_fixture(f)
        self.record(
            "A12", "canonical candidate rewritten with all F3 dependencies",
            f, expectation="REJECT_GRAPH", target="ack:ACK01",
            expected_error="canonical candidate history: trusted source mismatch",
        )

        # A13/A14: candidate tuple substitutions remain valid inputs but fail closed.
        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["raw_input"][
            "handoff_candidate_revision"
        ] = 999
        v.resign_fixture(f)
        self.record(
            "A13", "acknowledgement candidate revision substitution",
            f, expectation="ACCEPT_FAIL_CLOSED", target="ack:ACK01",
        )

        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["raw_input"][
            "handoff_candidate_fingerprint"
        ] = "f" * 64
        v.resign_fixture(f)
        self.record(
            "A14", "acknowledgement candidate fingerprint substitution",
            f, expectation="ACCEPT_FAIL_CLOSED", target="ack:ACK01",
        )

        # A15: context and owner evidence fully self-signed.
        f = copy.deepcopy(b)
        self.propagate_assessment_and_commitment(
            f, "A-F3-EQUAL",
            assessment_mutator=lambda row: row.__setitem__(
                "context_fingerprint", "a" * 64
            ),
        )
        self.record(
            "A15", "acknowledgement context changed with matching self-signed owner evidence",
            f, expectation="REJECT_GRAPH", target="ack:ACK01",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        # A16/A17 positive watermark controls; A18 lower watermark attack.
        f = copy.deepcopy(b)
        f["acknowledgement_cases"][1]["raw_input"][
            "minimum_trusted_event_sequence"
        ] = 301
        v.resign_fixture(f)
        self.record(
            "A16", "watermark equality positive control",
            f, expectation="ACCEPT_FAVORABLE", target="ack:ACK02",
            category="positive_control",
        )

        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["raw_input"][
            "minimum_trusted_event_sequence"
        ] = 99
        v.resign_fixture(f)
        self.record(
            "A17", "owner watermark higher than minimum positive control",
            f, expectation="ACCEPT_FAVORABLE", target="ack:ACK01",
            category="positive_control",
        )

        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["raw_input"][
            "minimum_trusted_event_sequence"
        ] = 101
        v.resign_fixture(f)
        self.record(
            "A18", "owner watermark lower than minimum",
            f, expectation="ACCEPT_FAIL_CLOSED", target="ack:ACK01",
        )

        # A19: old R2 field name.
        f = copy.deepcopy(b)
        raw = f["acknowledgement_cases"][0]["raw_input"]
        raw["trusted_event_sequence"] = raw.pop("minimum_trusted_event_sequence")
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A19", "old trusted_event_sequence field substitution",
            f, expectation="REJECT_GRAPH",
            expected_error="exact field inventory mismatch",
        )

        # A20-A23: owner source inventory mutations and order controls.
        f = copy.deepcopy(b)
        f["owner_assessment_revision_commitments"].pop()
        v.resign_fixture(f)
        self.record(
            "A20", "trusted owner commitment deleted",
            f, expectation="REJECT_GRAPH",
            expected_error="trusted source inventory mismatch",
        )

        f = copy.deepcopy(b)
        extra = copy.deepcopy(f["owner_assessment_revision_commitments"][0])
        extra["commitment_ref"] = "synthetic://attacker/extra@1"
        self.recompute_commitment(extra)
        f["owner_assessment_revision_commitments"].append(extra)
        v.resign_fixture(f)
        self.record(
            "A21", "caller owner commitment added",
            f, expectation="REJECT_GRAPH",
            expected_error="trusted source inventory mismatch",
        )

        f = copy.deepcopy(b)
        f["owner_assessment_revision_commitments"].reverse()
        v.resign_fixture(f)
        self.record(
            "A22", "owner commitment rows reversed",
            f, expectation="ACCEPT_VALID", category="positive_control",
            notes="Owner source resolution is by commitment_ref; list order is nonnormative.",
        )

        f = copy.deepcopy(b)
        f["owner_assessment_revision_commitments"][0], f[
            "owner_assessment_revision_commitments"
        ][1] = (
            f["owner_assessment_revision_commitments"][1],
            f["owner_assessment_revision_commitments"][0],
        )
        v.resign_fixture(f)
        self.record(
            "A23", "two owner commitment rows swapped",
            f, expectation="ACCEPT_VALID", category="positive_control",
            notes="Owner source resolution is by commitment_ref; list order is nonnormative.",
        )

        # A24-A27: candidate source inventory.
        f = copy.deepcopy(b)
        f["canonical_candidate_history"].pop()
        v.resign_fixture(f)
        self.record(
            "A24", "canonical candidate history row deleted",
            f, expectation="REJECT_GRAPH",
            expected_error="trusted source mismatch",
        )

        f = copy.deepcopy(b)
        extra = copy.deepcopy(f["canonical_candidate_history"][-1])
        extra["candidate_ref"] = "synthetic://f8/handoff-candidate/001@3"
        extra["candidate_revision"] = 3
        extra["predecessor_ref"] = f["canonical_candidate_history"][-1][
            "candidate_ref"
        ]
        extra["predecessor_fingerprint"] = f["canonical_candidate_history"][-1][
            "candidate_fingerprint"
        ]
        extra["candidate_fingerprint"] = v.digest(
            v.DOMAIN + ":candidate-history",
            v.without(extra, "candidate_fingerprint"),
        )
        f["canonical_candidate_history"].append(extra)
        v.resign_fixture(f)
        self.record(
            "A25", "canonical candidate history row added",
            f, expectation="REJECT_GRAPH",
            expected_error="trusted source mismatch",
        )

        f = copy.deepcopy(b)
        f["canonical_candidate_history"].reverse()
        v.resign_fixture(f)
        self.record(
            "A26", "canonical candidate history reordered",
            f, expectation="REJECT_GRAPH",
            expected_error="revision sequence mismatch",
        )

        f = copy.deepcopy(b)
        f["canonical_candidate_history"][1][
            "candidate_ref"
        ] = "synthetic://attacker/candidate@2"
        v.resign_fixture(f)
        self.record(
            "A27", "canonical candidate ref substituted",
            f, expectation="REJECT_GRAPH",
            expected_error="trusted source mismatch",
        )

        # A28-A35: schema and cross-field attacks.
        f = copy.deepcopy(b)
        f["owner_assessment_revision_commitments"][0]["unknown"] = 0
        v.resign_fixture(f)
        self.record(
            "A28", "unknown owner commitment field",
            f, expectation="REJECT_GRAPH",
            expected_error="exact field inventory mismatch",
        )

        f = copy.deepcopy(b)
        del f["owner_assessment_revision_commitments"][0]["issued_event_ref"]
        self.outer_resign(f)
        self.record(
            "A29", "missing owner commitment field",
            f, expectation="REJECT_GRAPH",
            expected_error="exact field inventory mismatch",
        )

        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["raw_input"][
            "minimum_trusted_event_sequence"
        ] = True
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A30", "integer-as-boolean watermark",
            f, expectation="REJECT_GRAPH",
            expected_error="positive revision/watermark required",
        )

        f = copy.deepcopy(b)
        f["owner_assessments"][0]["assessment_revision"] = 1.0
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A31", "float assessment revision",
            f, expectation="REJECT_GRAPH",
            expected_error="floats forbidden",
        )

        f = copy.deepcopy(b)
        f["owner_assessments"][0]["assessment_id"] = ""
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A32", "empty stable_ref",
            f, expectation="REJECT_GRAPH",
            expected_error="invalid or duplicate assessment_id",
        )

        f = copy.deepcopy(b)
        f["owner_assessments"][0]["result"] = "OWNER_MADE_UP"
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A33", "unknown owner result enum",
            f, expectation="REJECT_GRAPH",
            expected_error="owner/kind/result mismatch",
        )

        f = copy.deepcopy(b)
        commitment = f["owner_assessment_revision_commitments"][0]
        commitment["predecessor_commitment_ref"] = "synthetic://attacker/previous"
        commitment["predecessor_commitment_fingerprint"] = "0" * 64
        v.resign_fixture(f)
        self.record(
            "A34", "revision-one commitment predecessor contradiction",
            f, expectation="REJECT_GRAPH",
            expected_error="revision one predecessor must be null",
        )

        f = copy.deepcopy(b)
        f["canonical_candidate_history"][1][
            "predecessor_fingerprint"
        ] = "0" * 64
        self.outer_resign(f)
        self.record(
            "A35", "candidate predecessor contradiction",
            f, expectation="REJECT_GRAPH",
            expected_error="predecessor mismatch",
        )

        # A36-A48: authority and real-occurrence boundary attacks.
        f = copy.deepcopy(b)
        f["runtime_usable"] = True
        v.resign_fixture(f)
        self.record(
            "A36", "root runtime usability elevated",
            f, expectation="REJECT_GRAPH",
            expected_error="runtime_usable must be false",
        )

        f = copy.deepcopy(b)
        f["canonical_candidate_history"][1]["command_authority"] = True
        v.resign_fixture(f)
        self.record(
            "A37", "candidate Command authority elevated",
            f, expectation="REJECT_GRAPH",
            expected_error="authority/runtime must be false",
        )

        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["claimed_decision"][
            "task_write_authority"
        ] = True
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A38", "acknowledgement Task-write authority elevated",
            f, expectation="REJECT_GRAPH",
            expected_error="must be false",
        )

        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["claimed_decision"][
            "effect_authority"
        ] = True
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A39", "acknowledgement effect authority elevated",
            f, expectation="REJECT_GRAPH",
            expected_error="must be false",
        )

        boundary_fields = [
            "runtime_activation_count",
            "database_write_count",
            "provider_call_count",
            "private_memory_read_count",
            "sensing_or_recording_count",
            "external_effect_count",
            "production_auth_count",
            "real_command_count",
            "real_task_write_count",
        ]
        for number, field in enumerate(boundary_fields, 40):
            f = copy.deepcopy(b)
            f["boundary_assertions"][field] = 1
            v.resign_fixture(f)
            self.record(
                f"A{number:02d}", f"nonzero {field}",
                f, expectation="REJECT_GRAPH",
                expected_error="must be integer zero",
            )

        # A49/A52 expose the normative all-null consumer contradiction.
        f = copy.deepcopy(b)
        f["candidate_formation_cases"][0][
            "assessment_consumer"
        ] = self.null_consumer()
        f["candidate_formation_cases"][0]["claimed_decision"] = {
            "result": "INDETERMINATE",
            "primary_reason": "F3_OUTCOME_MISSING",
            "command_authority": False,
            "task_write_authority": False,
            "effect_authority": False,
            "runtime_usable": False,
        }
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A49", "all-six-null formation consumer required by R3",
            f, expectation="NORMATIVE_ACCEPT_FAIL_CLOSED",
            target="formation:CF01",
            notes=(
                "R3 amendment section 3 says all six fields may be null. "
                "The reducer derives INDETERMINATE, but validate_consumer rejects the tuple."
            ),
        )

        f = copy.deepcopy(b)
        f["candidate_formation_cases"][0]["assessment_consumer"][
            "owner_commitment_ref"
        ] = None
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A50", "partially-null consumer",
            f, expectation="REJECT_GRAPH",
            expected_error="stable_ref required",
        )

        f = copy.deepcopy(b)
        binding = f["acknowledgement_cases"][0]["raw_input"][
            "F3_outcome_consumer"
        ]
        binding["expected_owner_commitment_fingerprint"] = "f" * 64
        v.resign_fixture(f)
        self.record(
            "A51", "consumer owner commitment fingerprint substitution",
            f, expectation="ACCEPT_FAIL_CLOSED", target="ack:ACK01",
        )

        f = copy.deepcopy(b)
        f["acknowledgement_cases"][0]["raw_input"][
            "F3_outcome_consumer"
        ] = self.null_consumer()
        f["acknowledgement_cases"][0]["claimed_decision"] = {
            "result": "ACKNOWLEDGED_INDETERMINATE",
            "primary_reason": "F3_OUTCOME_MISSING",
            "command_authority": False,
            "task_write_authority": False,
            "effect_authority": False,
            "runtime_usable": False,
        }
        v.resign_fixture(f, derive_decisions=False)
        self.record(
            "A52", "all-six-null acknowledgement consumer required by R3",
            f, expectation="NORMATIVE_ACCEPT_FAIL_CLOSED",
            target="ack:ACK01",
            notes=(
                "R3 amendment section 3 says all six fields may be null. "
                "The reducer derives ACKNOWLEDGED_INDETERMINATE, but "
                "validate_consumer rejects the tuple."
            ),
        )

        f = copy.deepcopy(b)
        commitment = self.commitment(f, "A-F3-EQUAL")
        commitment["owner_contract"] = "F7"
        self.recompute_commitment(commitment)
        for binding in self.consumers(f):
            if binding.get("assessment_id") == "A-F3-EQUAL":
                binding["expected_owner_commitment_fingerprint"] = commitment[
                    "commitment_fingerprint"
                ]
        v.resign_fixture(f)
        self.record(
            "A53", "owner commitment rebound to another owner contract",
            f, expectation="REJECT_GRAPH", target="ack:ACK01",
            expected_error="OWNER_COMMITMENT_NOT_TRUSTED",
        )

        return self.records


def parser_probes(validator: Any) -> list[dict[str, Any]]:
    probes = [
        ("P01", '{"a":1,"a":2}', "duplicate JSON key"),
        ("P02", '{"a":NaN}', "NaN"),
        ("P03", '{"a":Infinity}', "Infinity"),
        ("P04", '{"a":1.5}', "float"),
    ]
    results = []
    for probe_id, text, title in probes:
        rejected = False
        error = None
        try:
            value = json.loads(
                text,
                object_pairs_hook=validator.reject_duplicate_pairs,
                parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)),
            )
            errors: list[str] = []
            validator.validate_json_value(value, "$", errors)
            rejected = bool(errors)
            if errors:
                error = errors[0]
        except Exception as exc:
            rejected = True
            error = type(exc).__name__
        results.append(
            {
                "probe_id": probe_id,
                "title": title,
                "rejected": rejected,
                "error": error,
                "passed": rejected,
            }
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="f8-r3-independent-probe-") as temp:
        package = safe_extract(args.zip_path, Path(temp))
        validator = load_validator(package)
        fixture = validator.load_json_strict(
            package / "fixture" / "F8-R3-synthetic-witness.json"
        )
        base_errors = validator.validate_fixture(fixture)
        if base_errors:
            raise RuntimeError(f"base fixture invalid: {base_errors[:5]}")
        records = Runner(validator, fixture).run()
        parsers = parser_probes(validator)

    positive_controls = sum(
        row["category"] == "positive_control" for row in records
    )
    attack_count = len(records) - positive_controls
    favorable_invalid = sum(row["favorable_invalid_path"] for row in records)
    contract_mismatches = [row for row in records if row["contract_mismatch"]]
    unexpected = [
        row for row in records
        if not row["passed"] and not row["contract_mismatch"]
    ]
    result = {
        "schema_version": "agents-os.f8-r3-independent-attack-results.v0.1",
        "review_unit": "F8_HOME_TO_ORCHESTRATOR_MINIMUM_INTERFACE_V0_1_R3_ATOMIC_BUNDLE",
        "zip_sha256": sha256_file(args.zip_path),
        "summary": {
            "coordinated_probe_count": len(records),
            "independent_fully_resigned_attack_count": attack_count,
            "positive_control_count": positive_controls,
            "parser_probe_count": len(parsers),
            "favorable_invalid_path_count": favorable_invalid,
            "contract_mismatch_probe_count": len(contract_mismatches),
            "unexpected_probe_failure_count": len(unexpected),
            "uncaught_exception_count": sum(
                row["exception"] is not None for row in records
            ),
            "semantic_blockers_closed": (
                favorable_invalid == 0 and not unexpected
            ),
            "new_contract_mismatch_found": bool(contract_mismatches),
        },
        "attacks": records,
        "parser_probes": parsers,
    }
    encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
