#!/usr/bin/env python3
"""Independent Section-10 validator for the F4 R9 synthetic non-authority witness.

This module intentionally does not import the fixture builder, the historical
R9 validator, or any F1/F2/F3 reducer. It independently validates the complete
Section-10 inventory, synthetic fingerprints, symbols, evidence DAG, owner
receipts, narrowing intersection, canonical-currentness snapshot, non-authority
witness, and fully re-signed negative mutations.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


HERE = Path(__file__).resolve().parent
DEFAULT = HERE / "examples" / "2026-07-16-agents-os-f4-r9-synthetic-nonauthority-m0a-witness-v0.1.json"
ROOT_SCHEMA_VERSION = "agents-os.f4-r9-synthetic-nonauthority-m0a.v0.1"
CONTRACT_VERSION = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R9_ATOMIC_BUNDLE"
SYNTHETIC_NAMESPACE = "synthetic-f4-r9"
SYNTHETIC_REF_PREFIX = SYNTHETIC_NAMESPACE + ":"
SYNTHETIC_FP_DOMAIN = "agents-os.f4-r9-synthetic-witness.v0.1"
MAX_SAFE_INTEGER = 9_007_199_254_740_991
HASH_RE = re.compile(r"^[0-9a-f]{64}$")


class Reject(AssertionError):
    """Deterministic validation rejection with a stable rule identifier."""

    def __init__(self, rule: str, detail: str):
        super().__init__(f"{rule}: {detail}")
        self.rule = rule
        self.detail = detail


def need(condition: bool, rule: str, detail: str) -> None:
    if not condition:
        raise Reject(rule, detail)


def _reject_float(raw: str) -> Any:
    raise Reject("JSON_NUMBER", f"floating-point number forbidden: {raw}")


def _reject_constant(raw: str) -> Any:
    raise Reject("JSON_NUMBER", f"non-JSON numeric constant forbidden: {raw}")


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        need(key not in result, "JSON_DUPLICATE_KEY", repr(key))
        result[key] = value
    return result


def lexical(value: Any, pointer: str = "") -> None:
    where = pointer or "/"
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        need(0 <= value <= MAX_SAFE_INTEGER, "JSON_INTEGER", where)
        return
    need(not isinstance(value, float), "JSON_NUMBER", where)
    if isinstance(value, str):
        need(unicodedata.normalize("NFC", value) == value, "JSON_NFC", where)
        need("\x00" not in value and value == value.strip(), "JSON_STRING", where)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            lexical(item, f"{pointer}/{index}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lexical(key, f"{pointer}/<key>")
            lexical(item, f"{pointer}/{escape_pointer(key)}")
        return
    raise Reject("JSON_TYPE", f"{where}: {type(value).__name__}")


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise Reject("FIXTURE_MISSING", str(path)) from exc
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Reject("JSON_UTF8", str(exc)) from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise Reject("JSON_PARSE", str(exc)) from exc
    need(isinstance(value, dict), "ROOT_TYPE", "root must be an object")
    lexical(value)
    return value, raw


def jcs(value: Any) -> bytes:
    """Canonical bytes for the no-float, safe-integer JSON subset."""
    lexical(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(jcs(value)).hexdigest()


def escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def is_hash(value: Any) -> bool:
    return isinstance(value, str) and HASH_RE.fullmatch(value) is not None


def is_ref(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value.encode("utf-8")) <= 512


def is_posint(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= MAX_SAFE_INTEGER


def is_nonneg(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= MAX_SAFE_INTEGER


def enum(*values: Any) -> Callable[[Any], bool]:
    return lambda value: any(type(value) is type(item) and value == item for item in values)


def list_of(predicate: Callable[[Any], bool]) -> Callable[[Any], bool]:
    return lambda value: isinstance(value, list) and all(predicate(item) for item in value)


def sorted_unique_strings(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) for item in value)
        and value == sorted(value, key=lambda item: item.encode("utf-8"))
        and len(value) == len(set(value))
    )


ANY: Callable[[Any], bool] = lambda _value: True
HASH = is_hash
REF = is_ref
POS = is_posint
NN = is_nonneg
BOOL = lambda value: isinstance(value, bool)
STR = lambda value: isinstance(value, str)
SREFS = lambda value: sorted_unique_strings(value) and all(is_ref(item) for item in value)


@dataclass(frozen=True)
class Field:
    name: str
    check: Callable[[Any], bool] = ANY


@dataclass(frozen=True)
class Profile:
    name: str
    interface: str | None
    fields: tuple[Field, ...]
    fingerprint_field: str | None = "canonical_fingerprint"
    registry_kind: str = "NORMATIVE"


def inferred_check(name: str) -> Callable[[Any], bool]:
    if name.endswith("_fingerprint") or name.endswith("_sha256"):
        return HASH
    if name.endswith("_refs"):
        return list_of(REF)
    if name.endswith("_ref") or name.endswith("_id"):
        return REF
    if name.endswith("_revision") or name.endswith("_ordinal"):
        return POS
    if name.endswith("_event_sequence") or name.endswith("_utc_ms") or name.endswith("_count"):
        return NN
    if name.endswith("_eligible") or name.endswith("_consumable") or name.endswith("_importable") or name.endswith("_allowed"):
        return BOOL
    return ANY


def fields(spec: str, checks: Mapping[str, Callable[[Any], bool]] | None = None) -> tuple[Field, ...]:
    table = checks or {}
    return tuple(Field(name, table.get(name, inferred_check(name))) for name in spec.split())


NORMATIVE_SCHEMAS: dict[str, Profile] = {}
WRAPPER_SCHEMAS: dict[str, Profile] = {}


def add_normative(
    name: str,
    interface: str,
    spec: str,
    checks: Mapping[str, Callable[[Any], bool]] | None = None,
    registry_kind: str = "SECTION10",
) -> None:
    NORMATIVE_SCHEMAS[name] = Profile(
        name, interface, fields(spec, checks), registry_kind=registry_kind
    )


def add_wrapper(
    name: str,
    spec: str,
    checks: Mapping[str, Callable[[Any], bool]] | None = None,
    fingerprint_field: str | None = None,
) -> None:
    WRAPPER_SCHEMAS[name] = Profile(
        name, None, fields(spec, checks), fingerprint_field, "WRAPPER"
    )


add_normative(
    "UpstreamAuthorityAssessmentReceiptV0_1R9",
    "agents-os.upstream-authority-assessment-receipt.v0.1-r9",
    "interface_version receipt_ref receipt_revision role owner_phase owner_contract_ref owner_contract_fingerprint owner_result_profile_ref owner_result_profile_fingerprint responsibility_route assessment_schema_name assessment_ref assessment_fingerprint subject_schema_name subject_ref subject_revision subject_fingerprint owner_result owner_head_event_sequence assessed_at_event_sequence resolved_at_watermark_event_sequence owner_currentness authority_atom_set_mode authority_atoms authority_atom_set_fingerprint environment authority_eligible",
    {
        "role": enum("F1_TASK_SCOPE", "F2_ACTOR_BINDING", "F2_RESPONSIBILITY", "F2_DELEGATION", "F3_COMMAND"),
        "owner_phase": enum("F1", "F2", "F3"),
        "responsibility_route": enum("NOT_APPLICABLE", "DIRECT_RESPONSIBILITY", "DELEGATED_RESPONSIBILITY"),
        "owner_currentness": enum("CURRENT", "STALE", "INDETERMINATE"),
        "authority_atom_set_mode": enum("GATE_ONLY", "OWNER_ISSUED_ATOM_SET"),
        "authority_atoms": list_of(lambda value: isinstance(value, dict)),
        "environment": enum("NON_PRODUCTION_REVIEW", "SYNTHETIC_TEST", "PRODUCTION"),
        "authority_eligible": BOOL,
    },
)
add_normative(
    "AuthorityInputCurrentnessObservationV0_1R9",
    "agents-os.authority-input-currentness-observation.v0.1-r9",
    "interface_version observation_ref input_kind input_ref input_fingerprint canonical_writer_ref canonical_writer_fingerprint canonical_latest_pointer_ref observed_latest_input_ref observed_latest_input_fingerprint observed_owner_head_event_sequence observed_latest_pointer_revision observed_at_event_sequence observation_result environment authority_eligible",
    {
        "input_kind": enum(
            "OPERATION_REGISTRY", "RESOURCE_KIND_REGISTRY", "EFFECT_CONSTRAINT",
            "OWNER_RECEIPT", "SCOPE_NARROWING_RECEIPT", "PBL_ASSESSMENT",
            "AUTHORIZATION_POLICY_ASSESSMENT", "JENN_EXACT_DECISION",
        ),
        "observation_result": enum("CURRENT", "STALE", "INDETERMINATE"),
        "environment": enum("NON_PRODUCTION_REVIEW", "SYNTHETIC_TEST", "PRODUCTION"),
        "authority_eligible": BOOL,
    },
)
add_normative(
    "FinalAdmissionCurrentnessSnapshotV0_1R9",
    "agents-os.final-admission-currentness-snapshot.v0.1-r9",
    "interface_version snapshot_ref required_input_roles required_input_set_basis_refs required_input_set_basis_fingerprints required_input_set_basis_fingerprint present_input_refs missing_required_input_roles observation_refs observation_fingerprints observed_writer_head_event_sequences observation_set_fingerprint final_transaction_ref final_transaction_fingerprint transaction_binding_rule final_snapshot_event_sequence snapshot_result environment authority_eligible",
    {
        "required_input_roles": SREFS,
        "required_input_set_basis_refs": SREFS,
        "required_input_set_basis_fingerprints": list_of(HASH),
        "present_input_refs": SREFS,
        "missing_required_input_roles": SREFS,
        "observation_refs": list_of(REF),
        "observation_fingerprints": list_of(HASH),
        "observed_writer_head_event_sequences": list_of(NN),
        "transaction_binding_rule": enum("EXACT_SAME_TRANSACTION"),
        "snapshot_result": enum("CURRENT", "STALE", "INDETERMINATE", "NOT_AUTHORITY_ELIGIBLE"),
        "environment": enum("NON_PRODUCTION_REVIEW", "SYNTHETIC_TEST", "PRODUCTION"),
        "authority_eligible": BOOL,
    },
)
add_normative(
    "ProspectiveF3InterfaceRequirementV0_1R9",
    "agents-os.prospective-f3-interface-requirement.v0.1-r9",
    "interface_version requirement_ref owner required_interface_kind required_effect_authority_atom_schema_fingerprint required_intake_result status usable_in_runtime synthetic_fixture_only authority_eligible",
    {
        "owner": enum("F3"),
        "required_interface_kind": enum("CLOSED_EFFECT_INTENT_COMMAND_TYPE"),
        "required_intake_result": enum("COMMITTED"),
        "status": enum("UNACCEPTED_DOWNSTREAM_REQUIREMENT"),
        "usable_in_runtime": BOOL,
        "synthetic_fixture_only": BOOL,
        "authority_eligible": BOOL,
    },
)
add_normative(
    "EffectConstraintV0_1R9",
    "agents-os.effect-constraint.v0.1-r9",
    "interface_version constraint_ref payload_schema_fingerprint external_effect_allowed provider_call_allowed raw_secret_allowed requires_human_presence not_before_utc_ms expires_at_utc_ms",
    {
        "external_effect_allowed": BOOL,
        "provider_call_allowed": BOOL,
        "raw_secret_allowed": BOOL,
        "requires_human_presence": BOOL,
    },
)
add_normative(
    "EffectAuthorityAtomV0_1R9",
    "agents-os.effect-authority-atom.v0.1-r9",
    "interface_version atom_ref operation_registry_ref operation_registry_fingerprint operation_kind resource_kind_registry_ref resource_kind_registry_fingerprint resource_kind resource_ref constraint_ref constraint_fingerprint authority_tuple_fingerprint",
)
add_normative(
    "EffectScopeNarrowingReceiptV0_1R9",
    "agents-os.effect-scope-narrowing-receipt.v0.1-r9",
    "interface_version receipt_ref receipt_revision role owner_kind source_contract_ref source_contract_fingerprint source_input_ref source_input_fingerprint source_result_profile_ref source_result_profile_fingerprint source_result authority_atoms authority_atom_set_fingerprint owner_head_event_sequence evaluated_at_event_sequence resolved_at_watermark_event_sequence environment authority_eligible",
    {
        "role": enum("POLICY_SCOPE", "HOST_CAPABILITY_RESOURCE_SCOPE", "JENN_EXACT_DECISION_SCOPE"),
        "owner_kind": enum("POLICY_CANONICAL_WRITER", "HOST_TRUST_CANONICAL_WRITER", "JENN_DECISION_CANONICAL_WRITER"),
        "source_result": enum("CURRENT_SCOPE_CONSTRAINT"),
        "authority_atoms": list_of(lambda value: isinstance(value, dict)),
        "environment": enum("NON_PRODUCTION_REVIEW", "SYNTHETIC_TEST", "PRODUCTION"),
        "authority_eligible": BOOL,
    },
)
add_normative(
    "F4SyntheticExactEffectScopeV0_1R9",
    "agents-os.f4-synthetic-exact-effect-scope.v0.1-r9",
    "interface_version scope_ref effect_authority_atom_ref effect_authority_atom_fingerprint effect_authority_tuple_fingerprint environment authority_eligible",
    {
        "environment": enum("SYNTHETIC_TEST"),
        "authority_eligible": BOOL,
    },
)
add_normative(
    "SyntheticAuthorityIntersectionAssessmentV0_1R9",
    "agents-os.synthetic-authority-intersection-assessment.v0.1-r9",
    "interface_version assessment_ref required_scope_roles present_scope_roles missing_scope_roles source_receipt_refs source_receipt_fingerprints source_atom_set_fingerprints intersection_tuple_fingerprints intersection_set_fingerprint result environment authority_eligible",
    {
        "required_scope_roles": SREFS,
        "present_scope_roles": SREFS,
        "missing_scope_roles": SREFS,
        "source_receipt_refs": list_of(REF),
        "source_receipt_fingerprints": list_of(HASH),
        "source_atom_set_fingerprints": list_of(HASH),
        "intersection_tuple_fingerprints": list_of(HASH),
        "result": enum("NOT_AUTHORITY_ELIGIBLE"),
        "environment": enum("SYNTHETIC_TEST"),
        "authority_eligible": BOOL,
    },
)
add_normative(
    "ProhibitedBoundaryAssessmentV0_1R9Final",
    "agents-os.prohibited-boundary-assessment.v0.1-r9-final",
    "interface_version assessment_ref exact_effect_scope_ref exact_effect_scope_fingerprint prohibited_behavior_list_revision evaluated_rule_set_fingerprint matched_rule_ids evaluation_result evaluated_at_event_sequence",
    {
        "prohibited_behavior_list_revision": REF,
        "matched_rule_ids": SREFS,
        "evaluation_result": enum("PROHIBITED_MATCH", "NO_PROHIBITED_MATCH", "INDETERMINATE"),
    },
)
add_normative(
    "EffectAuthorizationPolicyAssessmentV0_1R9",
    "agents-os.effect-authorization-policy-assessment.v0.1-r9",
    "interface_version assessment_ref exact_effect_scope_ref exact_effect_scope_fingerprint policy_bundle_revision authorization_requirement assessed_at_event_sequence result",
    {
        "policy_bundle_revision": REF,
        "authorization_requirement": enum("NO_SEPARATE_JENN_AUTHORIZATION_REQUIRED", "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED"),
        "result": enum("CURRENT", "STALE", "INDETERMINATE"),
    },
)
add_normative(
    "F4SyntheticHandoffConstructibilityWitnessV0_1R9",
    "agents-os.f4-synthetic-handoff-constructibility-witness.v0.1-r9",
    "interface_version witness_ref witness_namespace environment fingerprint_domain prospective_f3_requirement_ref prospective_f3_requirement_fingerprint hypothetical_effect_atom_ref hypothetical_effect_atom_fingerprint intersection_assessment_ref intersection_assessment_fingerprint currentness_snapshot_ref currentness_snapshot_fingerprint reducer_trace_fingerprint claim_state authority_eligible runtime_consumable recovery_importable physical_effect_boundary terminal_outcome external_effect_count provider_call_count raw_secret_count",
    {
        "witness_namespace": enum("synthetic-f4-r9"),
        "environment": enum("SYNTHETIC_TEST"),
        "fingerprint_domain": enum(SYNTHETIC_FP_DOMAIN),
        "claim_state": enum("FIXTURE_ONLY"),
        "authority_eligible": BOOL,
        "runtime_consumable": BOOL,
        "recovery_importable": BOOL,
        "physical_effect_boundary": enum("NOT_EXECUTABLE"),
        "terminal_outcome": enum("NOT_EXECUTED"),
    },
)

# Section-8 structural schemas retained by the Section-10 fixture profile.
add_normative(
    "CanonicalSymbolBindingV0_1R9",
    "agents-os.canonical-symbol-binding.v0.1-r9",
    "interface_version symbol_ref target_exact_schema_name target_fingerprint target_inventory_pointer",
    registry_kind="NORMATIVE",
)
add_normative(
    "CrossObjectSymbolTableV0_1R9",
    "agents-os.cross-object-symbol-table.v0.1-r9",
    "interface_version bindings binding_set_fingerprint",
    {"bindings": list_of(lambda value: isinstance(value, dict))},
    registry_kind="NORMATIVE",
)

add_wrapper(
    "F4R9SyntheticNonAuthorityRoot",
    "schema_version contract_version object_store canonical_symbol_table nodes schema_inventory assertions",
    {
        "object_store": list_of(lambda value: isinstance(value, dict)),
        "canonical_symbol_table": lambda value: isinstance(value, dict),
        "nodes": list_of(lambda value: isinstance(value, dict)),
        "schema_inventory": list_of(lambda value: isinstance(value, dict)),
        "assertions": lambda value: isinstance(value, dict),
    },
)
add_wrapper(
    "ObjectStoreEntryV0_1R9",
    "object_key exact_schema_name object",
    {"object": lambda value: isinstance(value, dict)},
)
add_wrapper(
    "EvidenceNodeV0_1R9",
    "ordinal kind object_pointer object_fingerprint depends_on_ordinals",
    {"ordinal": POS, "object_pointer": REF, "object_fingerprint": HASH, "depends_on_ordinals": list_of(POS), "node_fingerprint": HASH},
    fingerprint_field="node_fingerprint",
)
add_wrapper(
    "SchemaInventoryEntryV0_1R9",
    "json_pointer exact_schema_name interface_version fingerprint_field ordered_field_names registry_kind",
    {
        "interface_version": lambda value: value is None or isinstance(value, str),
        "fingerprint_field": lambda value: value is None or isinstance(value, str),
        "ordered_field_names": list_of(STR),
        "registry_kind": enum("NORMATIVE", "WRAPPER"),
    },
)
add_wrapper(
    "SyntheticAssertionsV0_1R9",
    "accepted_handoff_count synthetic_constructibility_witness_count runtime_consumable_count external_effect_count provider_call_count raw_secret_count terminal_outcome",
    {"terminal_outcome": enum("NOT_EXECUTED")},
)


EFFECT_ATOM_SCHEMA_PROFILE_DESCRIPTOR: dict[str, Any] = {
    "interface_version": "agents-os.effect-authority-atom.v0.1-r9",
    "ordered_field_names": [
        "interface_version", "atom_ref", "operation_registry_ref",
        "operation_registry_fingerprint", "operation_kind",
        "resource_kind_registry_ref", "resource_kind_registry_fingerprint",
        "resource_kind", "resource_ref", "constraint_ref", "constraint_fingerprint",
        "authority_tuple_fingerprint", "canonical_fingerprint",
    ],
    "field_types": {
        "interface_version": "closed_literal",
        "atom_ref": "stable_ref",
        "operation_registry_ref": "stable_ref",
        "operation_registry_fingerprint": "lowercase_sha256",
        "operation_kind": "closed_operation",
        "resource_kind_registry_ref": "stable_ref",
        "resource_kind_registry_fingerprint": "lowercase_sha256",
        "resource_kind": "closed_resource_kind",
        "resource_ref": "stable_ref",
        "constraint_ref": "stable_ref",
        "constraint_fingerprint": "lowercase_sha256",
        "authority_tuple_fingerprint": "lowercase_sha256",
        "canonical_fingerprint": "lowercase_sha256",
    },
    "closed_enums": {
        "interface_version": ["agents-os.effect-authority-atom.v0.1-r9"],
        "synthetic_operation_kind": ["F4_M0_SYNTHETIC_NOOP"],
        "synthetic_resource_kind": ["SYNTHETIC_M0_RESOURCE"],
    },
    "vocabulary_requirements": {
        "operation_kind": [
            "operation_registry_ref", "operation_registry_fingerprint",
            "canonical_current_resolution_required",
        ],
        "resource_kind": [
            "resource_kind_registry_ref", "resource_kind_registry_fingerprint",
            "canonical_current_resolution_required",
        ],
    },
    "nullability": "none",
    "canonical_fingerprint_rule": [
        SYNTHETIC_FP_DOMAIN,
        "schema",
        "EffectAuthorityAtomV0_1R9",
        "ordered_values_excluding_canonical_fingerprint",
    ],
    "authority_tuple_fingerprint_rule": [
        SYNTHETIC_FP_DOMAIN,
        "authority-tuple",
        "operation_registry_fingerprint",
        "operation_kind",
        "resource_kind_registry_fingerprint",
        "resource_kind",
        "resource_ref",
        "constraint_fingerprint",
    ],
    "prospective_production_canonical_fingerprint_rule": [
        "agents-os.effect-authority-atom.v0.1-r9",
        "ordered_values_excluding_canonical_fingerprint",
    ],
    "prospective_production_tuple_fingerprint_rule": [
        "agents-os.effect-authority-tuple.v0.1-r9",
        "operation_registry_fingerprint",
        "operation_kind",
        "resource_kind_registry_fingerprint",
        "resource_kind",
        "resource_ref",
        "constraint_fingerprint",
    ],
    "domain_rule": "SYNTHETIC_TEST_ONLY_NOT_PRODUCTION_AUTHORITY",
}


OWNER_RESULT_PROFILE_MATRIX: list[list[Any]] = [
    ["F1_TASK_SCOPE", "F1", "TASK_SCOPE_CURRENT", ["NOT_APPLICABLE"]],
    ["F2_ACTOR_BINDING", "F2", "BINDING_CURRENT", ["NOT_APPLICABLE"]],
    [
        "F2_RESPONSIBILITY", "F2", "RESPONSIBILITY_CURRENT",
        ["DELEGATED_RESPONSIBILITY", "DIRECT_RESPONSIBILITY"],
    ],
    ["F2_DELEGATION", "F2", "DELEGATION_CURRENT", ["NOT_APPLICABLE"]],
    ["F3_COMMAND", "F3", "COMMAND_COMMITTED_CURRENT", ["NOT_APPLICABLE"]],
]

NARROWING_RESULT_PROFILE_MATRIX: list[list[str]] = [
    ["POLICY_SCOPE", "POLICY_CANONICAL_WRITER"],
    ["HOST_CAPABILITY_RESOURCE_SCOPE", "HOST_TRUST_CANONICAL_WRITER"],
    ["JENN_EXACT_DECISION_SCOPE", "JENN_DECISION_CANONICAL_WRITER"],
]


def synthetic_fingerprint(schema: str, values: Sequence[Any]) -> str:
    return digest([SYNTHETIC_FP_DOMAIN, "schema", schema, *values])


def field_names(profile: Profile) -> list[str]:
    result = [field.name for field in profile.fields]
    if profile.fingerprint_field is not None:
        result.append(profile.fingerprint_field)
    return result


def expected_fingerprint(obj: Mapping[str, Any], profile: Profile) -> str:
    return synthetic_fingerprint(profile.name, [obj[field.name] for field in profile.fields])


def walk_dicts(value: Any, pointer: str = "") -> Sequence[tuple[str, dict[str, Any]]]:
    result: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        result.append((pointer, value))
        for key, child in value.items():
            child_pointer = pointer + "/" + escape_pointer(key)
            result.extend(walk_dicts(child, child_pointer))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            result.extend(walk_dicts(child, pointer + f"/{index}"))
    return result


def pointer_get(root: Any, pointer: str) -> Any:
    if pointer in {"", "/"}:
        return root
    need(pointer.startswith("/"), "JSON_POINTER", pointer)
    current = root
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            need(token.isdigit(), "JSON_POINTER", pointer)
            index = int(token)
            need(index < len(current), "JSON_POINTER", pointer)
            current = current[index]
        else:
            need(isinstance(current, dict) and token in current, "JSON_POINTER", pointer)
            current = current[token]
    return current


def classify(obj: Mapping[str, Any], pointer: str) -> Profile:
    candidates: list[Profile] = []
    for profile in (*NORMATIVE_SCHEMAS.values(), *WRAPPER_SCHEMAS.values()):
        if list(obj) != field_names(profile):
            continue
        if profile.interface is not None and obj.get("interface_version") != profile.interface:
            continue
        candidates.append(profile)
    need(len(candidates) == 1, "UNKNOWN_OR_SHADOW_OBJECT", f"{pointer or '/'}: keys={list(obj)!r}")
    profile = candidates[0]
    for field in profile.fields:
        need(field.check(obj[field.name]), "SCHEMA_FIELD_TYPE", f"{pointer or '/'}:{profile.name}.{field.name}")
    if profile.fingerprint_field is not None:
        need(is_hash(obj[profile.fingerprint_field]), "SCHEMA_FIELD_TYPE", f"{pointer or '/'}:{profile.fingerprint_field}")
    return profile


def discover(root: Mapping[str, Any]) -> list[tuple[str, Profile, dict[str, Any]]]:
    discovered: list[tuple[str, Profile, dict[str, Any]]] = []
    for pointer, obj in walk_dicts(root):
        if pointer == "/schema_inventory" or pointer.startswith("/schema_inventory/"):
            continue
        profile = classify(obj, pointer)
        discovered.append((pointer or "/", profile, obj))
    return discovered


def validate_root_header(root: Mapping[str, Any]) -> None:
    expected = [field.name for field in WRAPPER_SCHEMAS["F4R9SyntheticNonAuthorityRoot"].fields]
    need(list(root) == expected, "ROOT_FIELD_ORDER", repr(list(root)))
    need(root["schema_version"] == ROOT_SCHEMA_VERSION, "ROOT_SCHEMA_VERSION", repr(root["schema_version"]))
    need(root["contract_version"] == CONTRACT_VERSION, "ROOT_CONTRACT_VERSION", repr(root["contract_version"]))


def validate_inventory(
    root: Mapping[str, Any], discovered: Sequence[tuple[str, Profile, dict[str, Any]]]
) -> dict[str, Profile]:
    inventory = root["schema_inventory"]
    need(isinstance(inventory, list), "INVENTORY_TYPE", "schema_inventory")
    expected = [
        {
            "json_pointer": pointer,
            "exact_schema_name": profile.name,
            "interface_version": profile.interface,
            "fingerprint_field": profile.fingerprint_field,
            "ordered_field_names": field_names(profile),
            "registry_kind": profile.registry_kind,
        }
        for pointer, profile, _obj in discovered
    ]
    need(inventory == expected, "INVENTORY_COMPLETE_EXACT", f"expected {len(expected)} rows, got {len(inventory)}")
    need(len({row["json_pointer"] for row in inventory}) == len(inventory), "INVENTORY_POINTER_UNIQUE", "duplicate pointer")
    return {pointer: profile for pointer, profile, _obj in discovered}


def validate_normative_fingerprints(
    discovered: Sequence[tuple[str, Profile, dict[str, Any]]]
) -> int:
    count = 0
    for pointer, profile, obj in discovered:
        if profile.registry_kind not in {"SECTION10", "NORMATIVE"}:
            continue
        need(
            obj[profile.fingerprint_field] == expected_fingerprint(obj, profile),
            "SYNTHETIC_FINGERPRINT",
            f"{pointer}:{profile.name}",
        )
        count += 1
    return count


IDENTITY_FIELDS: dict[str, str] = {
    "UpstreamAuthorityAssessmentReceiptV0_1R9": "receipt_ref",
    "AuthorityInputCurrentnessObservationV0_1R9": "observation_ref",
    "FinalAdmissionCurrentnessSnapshotV0_1R9": "snapshot_ref",
    "ProspectiveF3InterfaceRequirementV0_1R9": "requirement_ref",
    "EffectConstraintV0_1R9": "constraint_ref",
    "EffectAuthorityAtomV0_1R9": "atom_ref",
    "F4SyntheticExactEffectScopeV0_1R9": "scope_ref",
    "EffectScopeNarrowingReceiptV0_1R9": "receipt_ref",
    "SyntheticAuthorityIntersectionAssessmentV0_1R9": "assessment_ref",
    "ProhibitedBoundaryAssessmentV0_1R9Final": "assessment_ref",
    "EffectAuthorizationPolicyAssessmentV0_1R9": "assessment_ref",
    "F4SyntheticHandoffConstructibilityWitnessV0_1R9": "witness_ref",
}


def store_index(
    root: Mapping[str, Any], inventory: Mapping[str, Profile]
) -> tuple[list[dict[str, Any]], dict[str, tuple[str, Profile, dict[str, Any]]]]:
    entries = root["object_store"]
    need(isinstance(entries, list) and entries, "OBJECT_STORE", "must be non-empty")
    symbols: dict[str, tuple[str, Profile, dict[str, Any]]] = {}
    keys: set[str] = set()
    for index, entry in enumerate(entries):
        pointer = f"/object_store/{index}/object"
        need(entry["object_key"] not in keys, "OBJECT_KEY_UNIQUE", entry["object_key"])
        keys.add(entry["object_key"])
        need(pointer in inventory, "OBJECT_STORE_INVENTORY", pointer)
        profile = inventory[pointer]
        need(profile.registry_kind == "SECTION10" and profile.name in IDENTITY_FIELDS, "OBJECT_STORE_SCHEMA", profile.name)
        need(entry["exact_schema_name"] == profile.name, "OBJECT_STORE_SCHEMA", pointer)
        obj = entry["object"]
        identity = obj[IDENTITY_FIELDS[profile.name]]
        need(isinstance(identity, str) and identity.startswith(SYNTHETIC_REF_PREFIX), "SYNTHETIC_NAMESPACE", identity)
        need(identity not in symbols, "SYMBOL_DUPLICATE", identity)
        symbols[identity] = (pointer, profile, obj)
    return entries, symbols


def validate_symbols(
    root: Mapping[str, Any], inventory: Mapping[str, Profile]
) -> dict[str, tuple[str, Profile, dict[str, Any]]]:
    _entries, symbols = store_index(root, inventory)
    table = root["canonical_symbol_table"]
    bindings = table["bindings"]
    need(
        [binding["symbol_ref"] for binding in bindings]
        == sorted(symbols, key=lambda item: item.encode("utf-8")),
        "SYMBOL_ORDER_AND_COMPLETENESS",
        "binding refs",
    )
    need(len(bindings) == len(symbols), "SYMBOL_ORDER_AND_COMPLETENESS", "binding count")
    target_pointers: set[str] = set()
    for binding in bindings:
        symbol = binding["symbol_ref"]
        need(symbol in symbols, "SYMBOL_UNKNOWN", symbol)
        pointer, profile, obj = symbols[symbol]
        need(binding["target_inventory_pointer"] == pointer, "SYMBOL_TARGET_POINTER", symbol)
        need(binding["target_exact_schema_name"] == profile.name, "SYMBOL_TARGET_SCHEMA", symbol)
        need(binding["target_fingerprint"] == obj[profile.fingerprint_field], "SYMBOL_TARGET_FINGERPRINT", symbol)
        need(pointer not in target_pointers, "SYMBOL_TARGET_ALIAS", pointer)
        target_pointers.add(pointer)
    binding_fps = [binding["canonical_fingerprint"] for binding in bindings]
    need(
        table["binding_set_fingerprint"]
        == digest([SYNTHETIC_FP_DOMAIN, "symbol-set", binding_fps]),
        "SYMBOL_SET_FINGERPRINT",
        "canonical_symbol_table",
    )
    return symbols


def validate_dag(root: Mapping[str, Any], inventory: Mapping[str, Profile]) -> int:
    entries = root["object_store"]
    nodes = root["nodes"]
    need(len(nodes) == len(entries), "DAG_NODE_COUNT", f"{len(nodes)}/{len(entries)}")
    node_fps: list[str] = []
    pointers: set[str] = set()
    for index, node in enumerate(nodes):
        ordinal = index + 1
        pointer = f"/object_store/{index}/object"
        profile = inventory[pointer]
        obj = entries[index]["object"]
        deps = node["depends_on_ordinals"]
        need(node["ordinal"] == ordinal, "DAG_ORDINAL", str(ordinal))
        need(node["kind"] == profile.name, "DAG_KIND", pointer)
        need(node["object_pointer"] == pointer, "DAG_OBJECT_POINTER", pointer)
        need(pointer not in pointers, "DAG_OBJECT_DUPLICATE", pointer)
        pointers.add(pointer)
        need(node["object_fingerprint"] == obj[profile.fingerprint_field], "DAG_OBJECT_FINGERPRINT", pointer)
        need(deps == sorted(set(deps)) and all(dep < ordinal for dep in deps), "DAG_TOPOLOGY", pointer)
        dep_fps = [node_fps[dep - 1] for dep in deps]
        expected = digest(
            [SYNTHETIC_FP_DOMAIN, "evidence-node", ordinal, profile.name, pointer, node["object_fingerprint"], dep_fps]
        )
        need(node["node_fingerprint"] == expected, "DAG_NODE_FINGERPRINT", pointer)
        node_fps.append(expected)
    return len(nodes)


def walk_scalars(value: Any, pointer: str = "") -> Sequence[tuple[str, str, Any]]:
    result: list[tuple[str, str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = pointer + "/" + escape_pointer(key)
            if isinstance(child, (dict, list)):
                result.extend(walk_scalars(child, child_pointer))
            else:
                result.append((child_pointer, key, child))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_pointer = pointer + f"/{index}"
            if isinstance(child, (dict, list)):
                result.extend(walk_scalars(child, child_pointer))
            else:
                result.append((child_pointer, "", child))
    return result


EXPECTED_STORE: tuple[tuple[str, str], ...] = (
    ("prospective-f3", "ProspectiveF3InterfaceRequirementV0_1R9"),
    ("constraint", "EffectConstraintV0_1R9"),
    ("atom", "EffectAuthorityAtomV0_1R9"),
    ("scope", "F4SyntheticExactEffectScopeV0_1R9"),
    ("currentness-operation_registry", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("currentness-resource_kind_registry", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("currentness-effect_constraint", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("receipt-f1_task_scope", "UpstreamAuthorityAssessmentReceiptV0_1R9"),
    ("currentness-f1_task_scope", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("receipt-f2_actor_binding", "UpstreamAuthorityAssessmentReceiptV0_1R9"),
    ("currentness-f2_actor_binding", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("receipt-f2_responsibility", "UpstreamAuthorityAssessmentReceiptV0_1R9"),
    ("currentness-f2_responsibility", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("pbl", "ProhibitedBoundaryAssessmentV0_1R9Final"),
    ("currentness-pbl", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("policy", "EffectAuthorizationPolicyAssessmentV0_1R9"),
    ("currentness-policy", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("narrowing-host_capability_resource_scope", "EffectScopeNarrowingReceiptV0_1R9"),
    ("currentness-narrowing-host_capability_resource_scope", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("narrowing-policy_scope", "EffectScopeNarrowingReceiptV0_1R9"),
    ("currentness-narrowing-policy_scope", "AuthorityInputCurrentnessObservationV0_1R9"),
    ("intersection", "SyntheticAuthorityIntersectionAssessmentV0_1R9"),
    ("currentness-snapshot", "FinalAdmissionCurrentnessSnapshotV0_1R9"),
    ("witness", "F4SyntheticHandoffConstructibilityWitnessV0_1R9"),
)


def validate_closed_surface(root: Mapping[str, Any]) -> None:
    actual = tuple(
        (entry["object_key"], entry["exact_schema_name"])
        for entry in root["object_store"]
    )
    need(actual == EXPECTED_STORE, "CLOSED_OBJECT_STORE", repr(actual))
    committed_paths = [
        pointer for pointer, _key, value in walk_scalars(root) if value == "COMMITTED"
    ]
    need(
        committed_paths == ["/object_store/0/object/required_intake_result"],
        "PROSPECTIVE_COMMITTED_ONLY",
        repr(committed_paths),
    )
    forbidden_labels = {
        "GREEN", "YELLOW", "RED", "P0", "P1", "P2", "P3",
        "TRUSTED", "URGENT", "HIGH_TRUST", "PRODUCTION",
    }
    for pointer, key, value in walk_scalars(root):
        if isinstance(value, str):
            need(value not in forbidden_labels, "AMBIENT_AUTHORITY_LABEL", f"{pointer}:{value}")
            need(not value.startswith("production:"), "SYNTHETIC_DOMAIN_ONLY", f"{pointer}:{value}")
        if key.endswith("_ref") and isinstance(value, str):
            need(value.startswith(SYNTHETIC_REF_PREFIX), "SYNTHETIC_DOMAIN_ONLY", f"{pointer}:{value}")
        if key.endswith("_refs") and isinstance(value, list):
            need(all(item.startswith(SYNTHETIC_REF_PREFIX) for item in value), "SYNTHETIC_DOMAIN_ONLY", pointer)
    forbidden_schemas = {
        "AuthorityAtomProjectionV0_1R9",
        "TaskPermitV0_1R9",
        "TaskPermitIssuanceFactV0_1R9",
        "HostWorkAcceptanceFactV0_1R9",
        "HostWorkStartDispositionFactV0_1R9",
        "F4AcceptedEffectHandoffV0_1R9",
    }
    need(
        not any(entry["exact_schema_name"] in forbidden_schemas for entry in root["object_store"]),
        "FORBIDDEN_AUTHORITY_SURFACE",
        "native/projection/operational object",
    )


def _rows(root: Mapping[str, Any], schema: str) -> list[dict[str, Any]]:
    return [
        entry["object"] for entry in root["object_store"]
        if entry["exact_schema_name"] == schema
    ]


def _one(root: Mapping[str, Any], schema: str) -> dict[str, Any]:
    rows = _rows(root, schema)
    need(len(rows) == 1, "SCHEMA_CARDINALITY", f"{schema}:{len(rows)}")
    return rows[0]


def resolve_pair(
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
    ref: str,
    fingerprint: str,
    expected_schemas: set[str],
    rule: str,
) -> dict[str, Any]:
    need(ref in symbols, rule, f"unresolved:{ref}")
    _pointer, profile, obj = symbols[ref]
    need(profile.name in expected_schemas, rule, f"{ref}:{profile.name}")
    need(obj[profile.fingerprint_field] == fingerprint, rule, f"fingerprint:{ref}")
    return obj


def synthetic_leaf(label: str) -> str:
    return digest([SYNTHETIC_FP_DOMAIN, "leaf", label])


def tuple_fingerprint(atom: Mapping[str, Any]) -> str:
    return digest(
        [
            SYNTHETIC_FP_DOMAIN,
            "authority-tuple",
            atom["operation_registry_fingerprint"],
            atom["operation_kind"],
            atom["resource_kind_registry_fingerprint"],
            atom["resource_kind"],
            atom["resource_ref"],
            atom["constraint_fingerprint"],
        ]
    )


def atom_set_fingerprint(atoms: Sequence[Mapping[str, Any]]) -> str:
    tuple_fps = sorted(
        (atom["authority_tuple_fingerprint"] for atom in atoms),
        key=lambda value: value.encode("utf-8"),
    )
    need(len(tuple_fps) == len(set(tuple_fps)), "ATOM_SET_DUPLICATE", repr(tuple_fps))
    return digest([SYNTHETIC_FP_DOMAIN, "owner-issued-atom-set", tuple_fps])


def validate_constraint_atom_scope(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    constraint = _one(root, "EffectConstraintV0_1R9")
    atom = _one(root, "EffectAuthorityAtomV0_1R9")
    scope = _one(root, "F4SyntheticExactEffectScopeV0_1R9")
    need(
        not constraint["external_effect_allowed"]
        and not constraint["provider_call_allowed"]
        and not constraint["raw_secret_allowed"],
        "SYNTHETIC_CONSTRAINT_NO_EFFECT",
        "effect/provider/secret",
    )
    need(
        constraint["payload_schema_fingerprint"] == synthetic_leaf("payload:empty-object"),
        "SYNTHETIC_CONSTRAINT_PAYLOAD",
        constraint["constraint_ref"],
    )
    need(
        constraint["not_before_utc_ms"] < constraint["expires_at_utc_ms"],
        "CONSTRAINT_TIME_WINDOW",
        "not_before < expires",
    )
    forbidden_atom_values = {"*", "ANY", "WILDCARD", "GREEN", "YELLOW", "RED"}
    need(
        atom["operation_kind"] not in forbidden_atom_values
        and atom["resource_kind"] not in forbidden_atom_values
        and atom["resource_ref"] not in forbidden_atom_values,
        "ATOM_CLOSED_TUPLE",
        "wildcard/ambient component",
    )
    need(
        atom["operation_registry_ref"] == f"{SYNTHETIC_REF_PREFIX}operation-registry:v1"
        and atom["operation_registry_fingerprint"] == synthetic_leaf("operation-registry:v1")
        and atom["operation_kind"] == "F4_M0_SYNTHETIC_NOOP",
        "ATOM_OPERATION_REGISTRY",
        atom["atom_ref"],
    )
    need(
        atom["resource_kind_registry_ref"] == f"{SYNTHETIC_REF_PREFIX}resource-kind-registry:v1"
        and atom["resource_kind_registry_fingerprint"] == synthetic_leaf("resource-kind-registry:v1")
        and atom["resource_kind"] == "SYNTHETIC_M0_RESOURCE",
        "ATOM_RESOURCE_REGISTRY",
        atom["atom_ref"],
    )
    resolved_constraint = resolve_pair(
        symbols,
        atom["constraint_ref"],
        atom["constraint_fingerprint"],
        {"EffectConstraintV0_1R9"},
        "ATOM_CONSTRAINT_RESOLUTION",
    )
    need(resolved_constraint is constraint, "ATOM_CONSTRAINT_RESOLUTION", "non-canonical constraint")
    need(atom["authority_tuple_fingerprint"] == tuple_fingerprint(atom), "ATOM_TUPLE_FINGERPRINT", atom["atom_ref"])
    resolved_atom = resolve_pair(
        symbols,
        scope["effect_authority_atom_ref"],
        scope["effect_authority_atom_fingerprint"],
        {"EffectAuthorityAtomV0_1R9"},
        "SCOPE_ATOM_RESOLUTION",
    )
    need(resolved_atom is atom, "SCOPE_ATOM_RESOLUTION", "non-canonical atom")
    need(
        scope["effect_authority_tuple_fingerprint"] == atom["authority_tuple_fingerprint"],
        "SCOPE_TUPLE_BINDING",
        scope["scope_ref"],
    )
    need(
        scope["environment"] == "SYNTHETIC_TEST" and not scope["authority_eligible"],
        "SYNTHETIC_SCOPE_BOUNDARY",
        scope["scope_ref"],
    )
    return constraint, atom, scope


RECEIPT_SPECS: dict[str, tuple[str, str, str, str]] = {
    "F1_TASK_SCOPE": ("F1", "TASK_SCOPE_CURRENT", "OWNER_ISSUED_ATOM_SET", "NOT_APPLICABLE"),
    "F2_ACTOR_BINDING": ("F2", "BINDING_CURRENT", "GATE_ONLY", "NOT_APPLICABLE"),
    "F2_RESPONSIBILITY": ("F2", "RESPONSIBILITY_CURRENT", "OWNER_ISSUED_ATOM_SET", "DELEGATED_RESPONSIBILITY"),
}


def validate_receipts(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
    canonical_atom: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    receipts = _rows(root, "UpstreamAuthorityAssessmentReceiptV0_1R9")
    by_role = {receipt["role"]: receipt for receipt in receipts}
    need(len(by_role) == len(receipts), "RECEIPT_ROLE_DUPLICATE", repr([r["role"] for r in receipts]))
    need(set(by_role) == set(RECEIPT_SPECS), "RECEIPT_REQUIRED_ROLES", repr(set(by_role)))
    for role, (owner, result, mode, route) in RECEIPT_SPECS.items():
        receipt = by_role[role]
        need(receipt["receipt_revision"] == 1, "RECEIPT_REVISION", role)
        need(receipt["owner_phase"] == owner, "RECEIPT_OWNER", role)
        need(receipt["owner_result"] == result, "RECEIPT_OWNER_RESULT", role)
        need(receipt["responsibility_route"] == route, "RECEIPT_RESPONSIBILITY_ROUTE", role)
        need(receipt["authority_atom_set_mode"] == mode, "RECEIPT_ATOM_SET_MODE", role)
        need(receipt["owner_currentness"] == "CURRENT", "RECEIPT_CURRENTNESS", role)
        need(
            receipt["owner_head_event_sequence"]
            <= receipt["assessed_at_event_sequence"]
            <= receipt["resolved_at_watermark_event_sequence"],
            "RECEIPT_WATERMARK_ORDER",
            role,
        )
        need(
            receipt["environment"] == "SYNTHETIC_TEST"
            and not receipt["authority_eligible"],
            "SYNTHETIC_RECEIPT_BOUNDARY",
            role,
        )
        need(
            receipt["owner_contract_ref"] == f"{SYNTHETIC_REF_PREFIX}owner-contract:{owner.lower()}"
            and receipt["owner_contract_fingerprint"] == synthetic_leaf(f"{owner}:contract"),
            "RECEIPT_OWNER_CONTRACT",
            role,
        )
        need(
            receipt["owner_result_profile_ref"]
            == f"{SYNTHETIC_REF_PREFIX}owner-result-profile:normalized-v1"
            and receipt["owner_result_profile_fingerprint"]
            == digest([SYNTHETIC_FP_DOMAIN, "owner-result-profile", OWNER_RESULT_PROFILE_MATRIX]),
            "RECEIPT_RESULT_PROFILE",
            role,
        )
        need(
            receipt["assessment_schema_name"] == f"SYNTHETIC_{role}_ASSESSMENT"
            and receipt["subject_schema_name"] == f"SYNTHETIC_{role}_SUBJECT",
            "RECEIPT_OWNER_SCHEMA_PROFILE",
            role,
        )
        need(
            receipt["assessment_ref"] == f"{SYNTHETIC_REF_PREFIX}assessment:{role.lower()}"
            and receipt["assessment_fingerprint"] == synthetic_leaf(f"{role}:assessment")
            and receipt["subject_ref"] == f"{SYNTHETIC_REF_PREFIX}subject:{role.lower()}"
            and receipt["subject_revision"] == 1
            and receipt["subject_fingerprint"] == synthetic_leaf(f"{role}:subject"),
            "RECEIPT_SUBJECT_ASSESSMENT_BINDING",
            role,
        )
        atoms = receipt["authority_atoms"]
        if mode == "GATE_ONLY":
            need(atoms == [], "GATE_ONLY_EMPTY_ATOMS", role)
        else:
            need(len(atoms) == 1, "SCOPE_RECEIPT_ATOM_COUNT", role)
        need(
            receipt["authority_atom_set_fingerprint"] == atom_set_fingerprint(atoms),
            "RECEIPT_ATOM_SET_FINGERPRINT",
            role,
        )
        for embedded in atoms:
            need(embedded["authority_tuple_fingerprint"] == tuple_fingerprint(embedded), "ATOM_TUPLE_FINGERPRINT", role)
            target = resolve_pair(
                symbols,
                embedded["atom_ref"],
                embedded["canonical_fingerprint"],
                {"EffectAuthorityAtomV0_1R9"},
                "OWNER_ATOM_RESOLUTION",
            )
            need(target == embedded == canonical_atom, "OWNER_ATOM_EXACT_COPY", role)
    return by_role


NARROWING_SPECS: dict[str, str] = {
    "HOST_CAPABILITY_RESOURCE_SCOPE": "HOST_TRUST_CANONICAL_WRITER",
    "POLICY_SCOPE": "POLICY_CANONICAL_WRITER",
}


def validate_narrowing_receipts(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
    canonical_atom: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    rows = _rows(root, "EffectScopeNarrowingReceiptV0_1R9")
    by_role = {row["role"]: row for row in rows}
    need(len(by_role) == len(rows), "NARROWING_ROLE_DUPLICATE", repr([row["role"] for row in rows]))
    need(set(by_role) == set(NARROWING_SPECS), "NARROWING_REQUIRED_ROLES", repr(set(by_role)))
    profile_fp = digest(
        [
            SYNTHETIC_FP_DOMAIN,
            "narrowing-result-profile",
            NARROWING_RESULT_PROFILE_MATRIX,
            "CURRENT_SCOPE_CONSTRAINT",
        ]
    )
    for role, owner_kind in NARROWING_SPECS.items():
        row = by_role[role]
        label = role.lower()
        need(row["receipt_revision"] == 1, "NARROWING_REVISION", role)
        need(row["owner_kind"] == owner_kind, "NARROWING_OWNER", role)
        need(row["source_result"] == "CURRENT_SCOPE_CONSTRAINT", "NARROWING_RESULT", role)
        need(
            row["source_contract_ref"] == f"{SYNTHETIC_REF_PREFIX}narrowing-contract:{label}"
            and row["source_contract_fingerprint"] == synthetic_leaf(f"narrowing-contract:{label}"),
            "NARROWING_SOURCE_CONTRACT",
            role,
        )
        need(
            row["source_result_profile_ref"] == f"{SYNTHETIC_REF_PREFIX}narrowing-result-profile:v1"
            and row["source_result_profile_fingerprint"] == profile_fp,
            "NARROWING_RESULT_PROFILE",
            role,
        )
        if role == "POLICY_SCOPE":
            resolved = resolve_pair(
                symbols,
                row["source_input_ref"],
                row["source_input_fingerprint"],
                {"EffectAuthorizationPolicyAssessmentV0_1R9"},
                "NARROWING_SOURCE_INPUT",
            )
            need(resolved is policy, "NARROWING_SOURCE_INPUT", role)
        else:
            need(
                row["source_input_ref"] == f"{SYNTHETIC_REF_PREFIX}host-scope-assessment:m0-a"
                and row["source_input_fingerprint"] == synthetic_leaf("host-scope-assessment:m0-a"),
                "NARROWING_SOURCE_INPUT",
                role,
            )
        need(
            row["owner_head_event_sequence"]
            <= row["evaluated_at_event_sequence"]
            <= row["resolved_at_watermark_event_sequence"],
            "NARROWING_WATERMARK_ORDER",
            role,
        )
        need(
            row["environment"] == "SYNTHETIC_TEST" and not row["authority_eligible"],
            "SYNTHETIC_NARROWING_BOUNDARY",
            role,
        )
        atoms = row["authority_atoms"]
        need(len(atoms) == 1, "NARROWING_ATOM_COUNT", role)
        need(row["authority_atom_set_fingerprint"] == atom_set_fingerprint(atoms), "NARROWING_ATOM_SET_FINGERPRINT", role)
        embedded = atoms[0]
        need(embedded["authority_tuple_fingerprint"] == tuple_fingerprint(embedded), "ATOM_TUPLE_FINGERPRINT", role)
        target = resolve_pair(
            symbols,
            embedded["atom_ref"],
            embedded["canonical_fingerprint"],
            {"EffectAuthorityAtomV0_1R9"},
            "NARROWING_ATOM_RESOLUTION",
        )
        need(target == embedded == canonical_atom, "NARROWING_ATOM_EXACT_COPY", role)
    return by_role


def validate_currentness_observations(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
    receipts: Mapping[str, dict[str, Any]],
    narrowings: Mapping[str, dict[str, Any]],
    pbl: Mapping[str, Any],
    policy: Mapping[str, Any],
    atom: Mapping[str, Any],
    constraint: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    observations = _rows(root, "AuthorityInputCurrentnessObservationV0_1R9")
    expected_inputs: dict[str, tuple[str, Mapping[str, Any] | None, str, int, int]] = {}
    receipt_ordinals = {"F1_TASK_SCOPE": 1, "F2_ACTOR_BINDING": 2, "F2_RESPONSIBILITY": 3}
    for role, receipt in receipts.items():
        expected_inputs[receipt["receipt_ref"]] = (
            "OWNER_RECEIPT", receipt, receipt["canonical_fingerprint"],
            receipt["owner_head_event_sequence"], receipt_ordinals[role],
        )
    expected_inputs[pbl["assessment_ref"]] = (
        "PBL_ASSESSMENT", pbl, pbl["canonical_fingerprint"],
        pbl["evaluated_at_event_sequence"], 4,
    )
    expected_inputs[policy["assessment_ref"]] = (
        "AUTHORIZATION_POLICY_ASSESSMENT", policy, policy["canonical_fingerprint"],
        policy["assessed_at_event_sequence"], 5,
    )
    narrowing_ordinals = {"HOST_CAPABILITY_RESOURCE_SCOPE": 6, "POLICY_SCOPE": 7}
    for role, narrowing in narrowings.items():
        expected_inputs[narrowing["receipt_ref"]] = (
            "SCOPE_NARROWING_RECEIPT", narrowing, narrowing["canonical_fingerprint"],
            narrowing["owner_head_event_sequence"], narrowing_ordinals[role],
        )
    expected_inputs[atom["operation_registry_ref"]] = (
        "OPERATION_REGISTRY", None, atom["operation_registry_fingerprint"], 40, 8
    )
    expected_inputs[atom["resource_kind_registry_ref"]] = (
        "RESOURCE_KIND_REGISTRY", None, atom["resource_kind_registry_fingerprint"], 40, 9
    )
    expected_inputs[constraint["constraint_ref"]] = (
        "EFFECT_CONSTRAINT", constraint, constraint["canonical_fingerprint"], 40, 10
    )
    by_input = {observation["input_ref"]: observation for observation in observations}
    need(len(by_input) == len(observations), "CURRENTNESS_INPUT_DUPLICATE", "input_ref")
    need(set(by_input) == set(expected_inputs), "CURRENTNESS_REQUIRED_INPUTS", repr(set(by_input)))
    for input_ref, (kind, input_obj, input_fp, owner_head, ordinal) in expected_inputs.items():
        observation = by_input[input_ref]
        need(observation["input_fingerprint"] == input_fp, "CURRENTNESS_INPUT_RESOLUTION", input_ref)
        if input_obj is not None:
            resolved = resolve_pair(
                symbols,
                observation["input_ref"],
                observation["input_fingerprint"],
                {
                    "UpstreamAuthorityAssessmentReceiptV0_1R9",
                    "ProhibitedBoundaryAssessmentV0_1R9Final",
                    "EffectAuthorizationPolicyAssessmentV0_1R9",
                    "EffectScopeNarrowingReceiptV0_1R9",
                    "EffectConstraintV0_1R9",
                },
                "CURRENTNESS_INPUT_RESOLUTION",
            )
            need(resolved is input_obj, "CURRENTNESS_INPUT_RESOLUTION", input_ref)
        need(observation["input_kind"] == kind, "CURRENTNESS_INPUT_KIND", input_ref)
        label = f"{kind.lower()}:{ordinal}"
        need(
            observation["observation_ref"] == f"{SYNTHETIC_REF_PREFIX}currentness:{label}"
            and observation["canonical_writer_ref"]
            == f"{SYNTHETIC_REF_PREFIX}canonical-writer:{label}"
            and observation["canonical_writer_fingerprint"]
            == synthetic_leaf(f"canonical-writer:{label}")
            and observation["canonical_latest_pointer_ref"]
            == f"{SYNTHETIC_REF_PREFIX}latest-pointer:{label}",
            "CURRENTNESS_CANONICAL_WRITER",
            input_ref,
        )
        need(
            observation["observed_latest_input_ref"] == input_ref
            and observation["observed_latest_input_fingerprint"] == observation["input_fingerprint"],
            "CURRENTNESS_LATEST_POINTER",
            input_ref,
        )
        need(
            observation["observed_owner_head_event_sequence"] == owner_head
            and observation["observed_at_event_sequence"] == 60 + ordinal,
            "CURRENTNESS_WRITER_HEAD",
            input_ref,
        )
        need(observation["observed_latest_pointer_revision"] == 1, "CURRENTNESS_POINTER_REVISION", input_ref)
        need(observation["observation_result"] == "CURRENT", "CURRENTNESS_FAIL_CLOSED", input_ref)
        need(
            observation["environment"] == "SYNTHETIC_TEST"
            and not observation["authority_eligible"],
            "SYNTHETIC_CURRENTNESS_BOUNDARY",
            input_ref,
        )
    need(
        not any(observation["input_kind"] == "JENN_EXACT_DECISION" for observation in observations),
        "SYNTHETIC_JENN_DECISION_FORBIDDEN",
        "fixture has no Jenn decision",
    )
    return by_input


def validate_currentness_snapshot(
    root: Mapping[str, Any],
    observations: Mapping[str, dict[str, Any]],
    missing_required_roles: Sequence[str],
    atom: Mapping[str, Any],
    scope: Mapping[str, Any],
    receipts: Mapping[str, dict[str, Any]],
    pbl: Mapping[str, Any],
    policy: Mapping[str, Any],
    intersection: Mapping[str, Any],
) -> dict[str, Any]:
    snapshot = _one(root, "FinalAdmissionCurrentnessSnapshotV0_1R9")
    ordered_inputs = sorted(observations, key=lambda value: value.encode("utf-8"))
    ordered_observations = [observations[input_ref] for input_ref in ordered_inputs]
    expected_missing = sorted(
        {*missing_required_roles, "JENN_EXACT_DECISION"},
        key=lambda value: value.encode("utf-8"),
    )
    required_roles = [
        "AUTHORIZATION_POLICY_ASSESSMENT",
        "EFFECT_CONSTRAINT",
        "F1_TASK_SCOPE",
        "F2_ACTOR_BINDING",
        "F2_DELEGATION",
        "F2_RESPONSIBILITY",
        "F3_COMMAND",
        "HOST_CAPABILITY_RESOURCE_SCOPE",
        "JENN_EXACT_DECISION",
        "JENN_EXACT_DECISION_SCOPE",
        "OPERATION_REGISTRY",
        "PBL_ASSESSMENT",
        "POLICY_SCOPE",
        "RESOURCE_KIND_REGISTRY",
    ]
    need(snapshot["required_input_roles"] == required_roles, "SNAPSHOT_REQUIRED_ROLES", repr(snapshot["required_input_roles"]))
    basis_pairs = sorted(
        [
            (atom["atom_ref"], atom["canonical_fingerprint"]),
            (scope["scope_ref"], scope["canonical_fingerprint"]),
            (
                receipts["F2_RESPONSIBILITY"]["receipt_ref"],
                receipts["F2_RESPONSIBILITY"]["canonical_fingerprint"],
            ),
            (pbl["assessment_ref"], pbl["canonical_fingerprint"]),
            (policy["assessment_ref"], policy["canonical_fingerprint"]),
            (intersection["assessment_ref"], intersection["canonical_fingerprint"]),
        ],
        key=lambda item: item[0].encode("utf-8"),
    )
    basis_refs = [item[0] for item in basis_pairs]
    basis_fps = [item[1] for item in basis_pairs]
    need(
        snapshot["required_input_set_basis_refs"] == basis_refs
        and snapshot["required_input_set_basis_fingerprints"] == basis_fps,
        "SNAPSHOT_REQUIRED_BASIS",
        snapshot["snapshot_ref"],
    )
    need(
        snapshot["required_input_set_basis_fingerprint"]
        == digest([SYNTHETIC_FP_DOMAIN, "required-input-basis", required_roles, basis_refs, basis_fps]),
        "SNAPSHOT_REQUIRED_BASIS_FINGERPRINT",
        snapshot["snapshot_ref"],
    )
    need(snapshot["present_input_refs"] == ordered_inputs, "SNAPSHOT_PRESENT_INPUTS", repr(snapshot["present_input_refs"]))
    need(snapshot["missing_required_input_roles"] == expected_missing, "SNAPSHOT_MISSING_INPUTS", repr(snapshot["missing_required_input_roles"]))
    observation_refs = [item["observation_ref"] for item in ordered_observations]
    observation_fps = [item["canonical_fingerprint"] for item in ordered_observations]
    heads = [item["observed_owner_head_event_sequence"] for item in ordered_observations]
    need(
        snapshot["observation_refs"] == observation_refs
        and snapshot["observation_fingerprints"] == observation_fps
        and snapshot["observed_writer_head_event_sequences"] == heads,
        "SNAPSHOT_PARALLEL_OBSERVATIONS",
        snapshot["snapshot_ref"],
    )
    need(
        snapshot["observation_set_fingerprint"]
        == digest(
            [
                SYNTHETIC_FP_DOMAIN,
                "observation-set",
                ordered_inputs,
                expected_missing,
                observation_refs,
                observation_fps,
                heads,
            ]
        ),
        "SNAPSHOT_OBSERVATION_SET_FINGERPRINT",
        snapshot["snapshot_ref"],
    )
    need(
        snapshot["final_transaction_ref"] == f"{SYNTHETIC_REF_PREFIX}final-transaction:m0-a"
        and snapshot["final_transaction_fingerprint"]
        == digest(
            [
                SYNTHETIC_FP_DOMAIN,
                "final-transaction",
                snapshot["final_transaction_ref"],
                snapshot["required_input_set_basis_fingerprint"],
                snapshot["observation_set_fingerprint"],
                snapshot["final_snapshot_event_sequence"],
            ]
        )
        and snapshot["transaction_binding_rule"] == "EXACT_SAME_TRANSACTION",
        "SNAPSHOT_TRANSACTION_BINDING",
        snapshot["snapshot_ref"],
    )
    need(
        all(item["observed_at_event_sequence"] <= snapshot["final_snapshot_event_sequence"] for item in ordered_observations),
        "SNAPSHOT_EVENT_ORDER",
        snapshot["snapshot_ref"],
    )
    need(
        snapshot["snapshot_result"] == "NOT_AUTHORITY_ELIGIBLE"
        and snapshot["environment"] == "SYNTHETIC_TEST"
        and not snapshot["authority_eligible"],
        "SYNTHETIC_SNAPSHOT_BOUNDARY",
        snapshot["snapshot_ref"],
    )
    return snapshot


def validate_prospective(root: Mapping[str, Any]) -> dict[str, Any]:
    prospective = _one(root, "ProspectiveF3InterfaceRequirementV0_1R9")
    expected_profile_fp = digest(
        [SYNTHETIC_FP_DOMAIN, "schema-profile", EFFECT_ATOM_SCHEMA_PROFILE_DESCRIPTOR]
    )
    need(prospective["owner"] == "F3", "PROSPECTIVE_OWNER", prospective["owner"])
    need(
        prospective["required_interface_kind"] == "CLOSED_EFFECT_INTENT_COMMAND_TYPE"
        and prospective["required_intake_result"] == "COMMITTED",
        "PROSPECTIVE_INTERFACE",
        prospective["requirement_ref"],
    )
    need(
        prospective["required_effect_authority_atom_schema_fingerprint"] == expected_profile_fp,
        "PROSPECTIVE_SCHEMA_PROFILE",
        prospective["requirement_ref"],
    )
    need(
        prospective["status"] == "UNACCEPTED_DOWNSTREAM_REQUIREMENT"
        and not prospective["usable_in_runtime"]
        and prospective["synthetic_fixture_only"]
        and not prospective["authority_eligible"],
        "PROSPECTIVE_NONAUTHORITY",
        prospective["requirement_ref"],
    )
    return prospective


def validate_governance_scope(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
    scope: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    pbl = _one(root, "ProhibitedBoundaryAssessmentV0_1R9Final")
    policy = _one(root, "EffectAuthorizationPolicyAssessmentV0_1R9")
    for obj, rule in ((pbl, "PBL_SCOPE_BINDING"), (policy, "POLICY_SCOPE_BINDING")):
        resolved = resolve_pair(
            symbols,
            obj["exact_effect_scope_ref"],
            obj["exact_effect_scope_fingerprint"],
            {"F4SyntheticExactEffectScopeV0_1R9"},
            rule,
        )
        need(resolved is scope, rule, "non-canonical scope")
    need(
        pbl["evaluation_result"] == "NO_PROHIBITED_MATCH"
        and pbl["matched_rule_ids"] == [],
        "PBL_VETO_ONLY",
        pbl["assessment_ref"],
    )
    need(
        pbl["prohibited_behavior_list_revision"] == f"{SYNTHETIC_REF_PREFIX}pbl:revision:1"
        and pbl["evaluated_rule_set_fingerprint"] == synthetic_leaf("pbl:complete-rule-set"),
        "PBL_RULE_SET_BINDING",
        pbl["assessment_ref"],
    )
    need(
        policy["authorization_requirement"] == "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED"
        and policy["result"] == "CURRENT",
        "POLICY_INDEPENDENT_REQUIREMENT",
        policy["assessment_ref"],
    )
    need(
        policy["policy_bundle_revision"] == f"{SYNTHETIC_REF_PREFIX}policy:revision:1",
        "POLICY_BUNDLE_BINDING",
        policy["assessment_ref"],
    )
    return pbl, policy


def validate_intersection(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
    receipts: Mapping[str, dict[str, Any]],
    narrowings: Mapping[str, dict[str, Any]],
    canonical_atom: Mapping[str, Any],
) -> dict[str, Any]:
    assessment = _one(root, "SyntheticAuthorityIntersectionAssessmentV0_1R9")
    required = [
        "F1_TASK_SCOPE",
        "F2_DELEGATION",
        "F2_RESPONSIBILITY",
        "F3_COMMAND",
        "HOST_CAPABILITY_RESOURCE_SCOPE",
        "JENN_EXACT_DECISION_SCOPE",
        "POLICY_SCOPE",
    ]
    present = [
        "F1_TASK_SCOPE",
        "F2_RESPONSIBILITY",
        "HOST_CAPABILITY_RESOURCE_SCOPE",
        "POLICY_SCOPE",
    ]
    missing = ["F2_DELEGATION", "F3_COMMAND", "JENN_EXACT_DECISION_SCOPE"]
    need(assessment["required_scope_roles"] == required, "INTERSECTION_REQUIRED_ROLES", repr(assessment["required_scope_roles"]))
    need(assessment["present_scope_roles"] == present, "INTERSECTION_PRESENT_ROLES", repr(assessment["present_scope_roles"]))
    need(assessment["missing_scope_roles"] == missing, "INTERSECTION_MISSING_ROLES", repr(assessment["missing_scope_roles"]))
    scope_receipts = {
        "F1_TASK_SCOPE": receipts["F1_TASK_SCOPE"],
        "F2_RESPONSIBILITY": receipts["F2_RESPONSIBILITY"],
        **narrowings,
    }
    source_receipts: list[dict[str, Any]] = []
    for index, role in enumerate(present):
        receipt = resolve_pair(
            symbols,
            assessment["source_receipt_refs"][index],
            assessment["source_receipt_fingerprints"][index],
            {"UpstreamAuthorityAssessmentReceiptV0_1R9", "EffectScopeNarrowingReceiptV0_1R9"},
            "INTERSECTION_SOURCE_RESOLUTION",
        )
        need(receipt is scope_receipts[role], "INTERSECTION_SOURCE_ROLE_ORDER", role)
        need(
            assessment["source_atom_set_fingerprints"][index]
            == receipt["authority_atom_set_fingerprint"],
            "INTERSECTION_SOURCE_ATOM_SET",
            role,
        )
        source_receipts.append(receipt)
    need(
        len(assessment["source_receipt_refs"])
        == len(assessment["source_receipt_fingerprints"])
        == len(assessment["source_atom_set_fingerprints"])
        == len(present),
        "INTERSECTION_SOURCE_PARALLEL_ARRAYS",
        "length",
    )
    tuple_sets = [
        {atom["authority_tuple_fingerprint"] for atom in receipt["authority_atoms"]}
        for receipt in source_receipts
    ]
    exact_intersection = sorted(set.intersection(*tuple_sets), key=lambda value: value.encode("utf-8"))
    need(
        assessment["intersection_tuple_fingerprints"] == exact_intersection,
        "ATOMIC_TUPLE_INTERSECTION",
        repr(exact_intersection),
    )
    need(
        assessment["intersection_set_fingerprint"]
        == digest([SYNTHETIC_FP_DOMAIN, "intersection-set", exact_intersection]),
        "INTERSECTION_SET_FINGERPRINT",
        assessment["assessment_ref"],
    )
    need(
        canonical_atom["authority_tuple_fingerprint"] in exact_intersection,
        "HYPOTHETICAL_ATOM_INTERSECTION",
        canonical_atom["atom_ref"],
    )
    need(
        assessment["result"] == "NOT_AUTHORITY_ELIGIBLE"
        and assessment["environment"] == "SYNTHETIC_TEST"
        and not assessment["authority_eligible"],
        "INTERSECTION_NONAUTHORITY",
        assessment["assessment_ref"],
    )
    return assessment


def validate_witness_and_assertions(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
    prospective: Mapping[str, Any],
    atom: Mapping[str, Any],
    intersection: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    receipts: Mapping[str, dict[str, Any]],
    narrowings: Mapping[str, dict[str, Any]],
    observations: Mapping[str, dict[str, Any]],
    pbl: Mapping[str, Any],
    policy: Mapping[str, Any],
) -> dict[str, Any]:
    witness = _one(root, "F4SyntheticHandoffConstructibilityWitnessV0_1R9")
    for ref_field, fp_field, schema, target, rule in (
        ("prospective_f3_requirement_ref", "prospective_f3_requirement_fingerprint", "ProspectiveF3InterfaceRequirementV0_1R9", prospective, "WITNESS_PROSPECTIVE_BINDING"),
        ("hypothetical_effect_atom_ref", "hypothetical_effect_atom_fingerprint", "EffectAuthorityAtomV0_1R9", atom, "WITNESS_ATOM_BINDING"),
        ("intersection_assessment_ref", "intersection_assessment_fingerprint", "SyntheticAuthorityIntersectionAssessmentV0_1R9", intersection, "WITNESS_INTERSECTION_BINDING"),
        ("currentness_snapshot_ref", "currentness_snapshot_fingerprint", "FinalAdmissionCurrentnessSnapshotV0_1R9", snapshot, "WITNESS_SNAPSHOT_BINDING"),
    ):
        resolved = resolve_pair(symbols, witness[ref_field], witness[fp_field], {schema}, rule)
        need(resolved is target, rule, "non-canonical target")
    receipt_order = ["F1_TASK_SCOPE", "F2_ACTOR_BINDING", "F2_RESPONSIBILITY"]
    narrowing_order = ["HOST_CAPABILITY_RESOURCE_SCOPE", "POLICY_SCOPE"]
    constraint = _one(root, "EffectConstraintV0_1R9")
    foundational_refs = [
        atom["operation_registry_ref"],
        atom["resource_kind_registry_ref"],
        constraint["constraint_ref"],
    ]
    expected_trace = digest(
        [
            SYNTHETIC_FP_DOMAIN,
            "reducer-trace",
            [observations[ref]["canonical_fingerprint"] for ref in foundational_refs],
            [receipts[role]["canonical_fingerprint"] for role in receipt_order],
            [observations[receipts[role]["receipt_ref"]]["canonical_fingerprint"] for role in receipt_order],
            [narrowings[role]["canonical_fingerprint"] for role in narrowing_order],
            [observations[narrowings[role]["receipt_ref"]]["canonical_fingerprint"] for role in narrowing_order],
            intersection["canonical_fingerprint"],
            snapshot["canonical_fingerprint"],
            pbl["canonical_fingerprint"],
            observations[pbl["assessment_ref"]]["canonical_fingerprint"],
            policy["canonical_fingerprint"],
            observations[policy["assessment_ref"]]["canonical_fingerprint"],
            prospective["canonical_fingerprint"],
            "NOT_AUTHORITY_ELIGIBLE",
        ]
    )
    need(witness["reducer_trace_fingerprint"] == expected_trace, "WITNESS_REDUCER_TRACE", witness["witness_ref"])
    need(
        witness["witness_namespace"] == SYNTHETIC_NAMESPACE
        and witness["environment"] == "SYNTHETIC_TEST"
        and witness["fingerprint_domain"] == SYNTHETIC_FP_DOMAIN
        and witness["claim_state"] == "FIXTURE_ONLY"
        and not witness["authority_eligible"]
        and not witness["runtime_consumable"]
        and not witness["recovery_importable"]
        and witness["physical_effect_boundary"] == "NOT_EXECUTABLE"
        and witness["terminal_outcome"] == "NOT_EXECUTED",
        "SYNTHETIC_WITNESS_BOUNDARY",
        witness["witness_ref"],
    )
    for field in ("external_effect_count", "provider_call_count", "raw_secret_count"):
        need(witness[field] == 0, "ZERO_EFFECT", f"witness.{field}")
    expected_assertions = {
        "accepted_handoff_count": 0,
        "synthetic_constructibility_witness_count": 1,
        "runtime_consumable_count": 0,
        "external_effect_count": 0,
        "provider_call_count": 0,
        "raw_secret_count": 0,
        "terminal_outcome": "NOT_EXECUTED",
    }
    need(root["assertions"] == expected_assertions, "ASSERTIONS_EXACT", repr(root["assertions"]))
    return witness


def validate_exact_dag_dependencies(root: Mapping[str, Any]) -> None:
    key_ordinals = {
        entry["object_key"]: index for index, entry in enumerate(root["object_store"], 1)
    }
    dependency_keys: dict[str, list[str]] = {
        "atom": ["constraint"],
        "scope": ["atom"],
        "currentness-operation_registry": ["atom"],
        "currentness-resource_kind_registry": ["atom"],
        "currentness-effect_constraint": ["constraint"],
        "receipt-f1_task_scope": ["atom"],
        "receipt-f2_responsibility": ["atom"],
        "currentness-f1_task_scope": ["receipt-f1_task_scope"],
        "currentness-f2_actor_binding": ["receipt-f2_actor_binding"],
        "currentness-f2_responsibility": ["receipt-f2_responsibility"],
        "pbl": ["scope"],
        "currentness-pbl": ["pbl"],
        "policy": ["scope"],
        "currentness-policy": ["policy"],
        "narrowing-host_capability_resource_scope": ["atom"],
        "currentness-narrowing-host_capability_resource_scope": [
            "narrowing-host_capability_resource_scope"
        ],
        "narrowing-policy_scope": ["atom", "policy"],
        "currentness-narrowing-policy_scope": ["narrowing-policy_scope"],
        "intersection": [
            "receipt-f1_task_scope",
            "receipt-f2_responsibility",
            "narrowing-host_capability_resource_scope",
            "narrowing-policy_scope",
        ],
        "currentness-snapshot": [
            "atom",
            "scope",
            "receipt-f2_responsibility",
            "pbl",
            "policy",
            "intersection",
            "currentness-operation_registry",
            "currentness-resource_kind_registry",
            "currentness-effect_constraint",
            "currentness-f1_task_scope",
            "currentness-f2_actor_binding",
            "currentness-f2_responsibility",
            "currentness-pbl",
            "currentness-policy",
            "currentness-narrowing-host_capability_resource_scope",
            "currentness-narrowing-policy_scope",
        ],
        "witness": [
            "prospective-f3", "atom", "scope",
            "currentness-operation_registry", "currentness-resource_kind_registry",
            "currentness-effect_constraint",
            "receipt-f1_task_scope", "receipt-f2_actor_binding", "receipt-f2_responsibility",
            "currentness-f1_task_scope", "currentness-f2_actor_binding", "currentness-f2_responsibility",
            "intersection", "pbl", "currentness-pbl", "policy", "currentness-policy",
            "narrowing-host_capability_resource_scope",
            "currentness-narrowing-host_capability_resource_scope",
            "narrowing-policy_scope", "currentness-narrowing-policy_scope",
            "currentness-snapshot",
        ],
    }
    for entry, node in zip(root["object_store"], root["nodes"], strict=True):
        expected = sorted(key_ordinals[key] for key in dependency_keys.get(entry["object_key"], []))
        need(node["depends_on_ordinals"] == expected, "DAG_DIRECT_EVIDENCE", entry["object_key"])


def validate_semantics(
    root: Mapping[str, Any],
    symbols: Mapping[str, tuple[str, Profile, dict[str, Any]]],
) -> dict[str, Any]:
    validate_closed_surface(root)
    constraint, atom, scope = validate_constraint_atom_scope(root, symbols)
    receipts = validate_receipts(root, symbols, atom)
    prospective = validate_prospective(root)
    pbl, policy = validate_governance_scope(root, symbols, scope)
    narrowings = validate_narrowing_receipts(root, symbols, atom, policy)
    observations = validate_currentness_observations(
        root, symbols, receipts, narrowings, pbl, policy, atom, constraint
    )
    intersection = validate_intersection(root, symbols, receipts, narrowings, atom)
    snapshot = validate_currentness_snapshot(
        root, observations, intersection["missing_scope_roles"], atom, scope,
        receipts, pbl, policy, intersection
    )
    witness = validate_witness_and_assertions(
        root, symbols, prospective, atom, intersection, snapshot, receipts,
        narrowings, observations, pbl, policy
    )
    validate_exact_dag_dependencies(root)
    return {
        "receipt_count": len(receipts),
        "currentness_observation_count": len(observations),
        "narrowing_receipt_count": len(narrowings),
        "intersection_tuple_count": len(intersection["intersection_tuple_fingerprints"]),
        "accepted_handoff_count": root["assertions"]["accepted_handoff_count"],
        "runtime_consumable_count": root["assertions"]["runtime_consumable_count"],
        "external_effect_count": witness["external_effect_count"],
        "provider_call_count": witness["provider_call_count"],
        "raw_secret_count": witness["raw_secret_count"],
        "terminal_outcome": witness["terminal_outcome"],
    }


def validate_fixture(root: dict[str, Any], raw: bytes | None = None) -> dict[str, Any]:
    """Validate the generic closed inventory, symbol, fingerprint, and DAG layers."""
    validate_root_header(root)
    discovered = discover(root)
    inventory = validate_inventory(root, discovered)
    fingerprint_count = validate_normative_fingerprints(discovered)
    symbols = validate_symbols(root, inventory)
    node_count = validate_dag(root, inventory)
    semantic_summary = validate_semantics(root, symbols)
    result: dict[str, Any] = {
        "result": "PASS_NO_BLOCKER",
        "contract_version": CONTRACT_VERSION,
        "registered_normative_schema_count": len(NORMATIVE_SCHEMAS),
        "registered_wrapper_schema_count": len(WRAPPER_SCHEMAS),
        "schema_occurrences_verified": len(discovered),
        "normative_fingerprints_verified": fingerprint_count,
        "symbols_verified": len(symbols),
        "dag_nodes_verified": node_count,
        "fixture_canonical_sha256": digest(root),
    }
    result.update(semantic_summary)
    if raw is not None:
        result["fixture_file_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def _resign_all(root: dict[str, Any]) -> None:
    """Re-sign all known synthetic layers without repairing semantic claims."""
    section_rows = [
        row for row in root["schema_inventory"]
        if row["registry_kind"] == "SECTION10"
        and row["exact_schema_name"] in NORMATIVE_SCHEMAS
    ]
    section_rows.sort(key=lambda row: row["json_pointer"].count("/"), reverse=True)
    for row in section_rows:
        profile = NORMATIVE_SCHEMAS[row["exact_schema_name"]]
        try:
            obj = pointer_get(root, row["json_pointer"])
        except Reject:
            continue
        if isinstance(obj, dict) and list(obj) == field_names(profile):
            obj[profile.fingerprint_field] = expected_fingerprint(obj, profile)

    table = root["canonical_symbol_table"]
    rebuilt: list[dict[str, Any]] = []
    for index, entry in enumerate(root["object_store"]):
        schema = entry["exact_schema_name"]
        if schema not in IDENTITY_FIELDS or schema not in NORMATIVE_SCHEMAS:
            continue
        profile = NORMATIVE_SCHEMAS[schema]
        obj = entry["object"]
        binding_profile = NORMATIVE_SCHEMAS["CanonicalSymbolBindingV0_1R9"]
        binding: dict[str, Any] = {
            "interface_version": binding_profile.interface,
            "symbol_ref": obj[IDENTITY_FIELDS[schema]],
            "target_exact_schema_name": schema,
            "target_fingerprint": obj[profile.fingerprint_field],
            "target_inventory_pointer": f"/object_store/{index}/object",
        }
        binding["canonical_fingerprint"] = expected_fingerprint(binding, binding_profile)
        rebuilt.append(binding)
    rebuilt.sort(key=lambda binding: binding["symbol_ref"].encode("utf-8"))
    table["bindings"] = rebuilt
    table["binding_set_fingerprint"] = digest(
        [SYNTHETIC_FP_DOMAIN, "symbol-set", [item["canonical_fingerprint"] for item in rebuilt]]
    )
    table["canonical_fingerprint"] = expected_fingerprint(
        table, NORMATIVE_SCHEMAS["CrossObjectSymbolTableV0_1R9"]
    )

    nodes = root["nodes"]
    node_fps: list[str] = []
    for node in nodes:
        target = pointer_get(root, node["object_pointer"])
        profile = NORMATIVE_SCHEMAS[node["kind"]]
        node["object_fingerprint"] = target[profile.fingerprint_field]
        deps = [node_fps[ordinal - 1] for ordinal in node["depends_on_ordinals"]]
        node["node_fingerprint"] = digest(
            [
                SYNTHETIC_FP_DOMAIN,
                "evidence-node",
                node["ordinal"],
                node["kind"],
                node["object_pointer"],
                node["object_fingerprint"],
                deps,
            ]
        )
        node_fps.append(node["node_fingerprint"])


def _role_row(root: Mapping[str, Any], role: str) -> dict[str, Any]:
    return next(row for row in _rows(root, "UpstreamAuthorityAssessmentReceiptV0_1R9") if row["role"] == role)


def _narrowing_row(root: Mapping[str, Any], role: str) -> dict[str, Any]:
    return next(row for row in _rows(root, "EffectScopeNarrowingReceiptV0_1R9") if row["role"] == role)


def _observation(root: Mapping[str, Any], *, kind: str | None = None, input_ref: str | None = None) -> dict[str, Any]:
    rows = _rows(root, "AuthorityInputCurrentnessObservationV0_1R9")
    return next(
        row for row in rows
        if (kind is None or row["input_kind"] == kind)
        and (input_ref is None or row["input_ref"] == input_ref)
    )


def run_mutations(root: dict[str, Any]) -> int:
    Case = tuple[str, Callable[[dict[str, Any]], None], set[str]]

    def signed(callback: Callable[[dict[str, Any]], None]) -> Callable[[dict[str, Any]], None]:
        def apply(candidate: dict[str, Any]) -> None:
            callback(candidate)
            _resign_all(candidate)
        return apply

    def set_owner_result(candidate: dict[str, Any]) -> None:
        _role_row(candidate, "F2_ACTOR_BINDING")["owner_result"] = "ACTIVE"

    def binding_indeterminate(candidate: dict[str, Any]) -> None:
        _role_row(candidate, "F2_ACTOR_BINDING")["owner_currentness"] = "INDETERMINATE"

    def stale_receipt(candidate: dict[str, Any]) -> None:
        _role_row(candidate, "F1_TASK_SCOPE")["owner_currentness"] = "STALE"

    def prospective_accepted(candidate: dict[str, Any]) -> None:
        _one(candidate, "ProspectiveF3InterfaceRequirementV0_1R9")["status"] = "ACCEPTED"

    def prospective_committed(candidate: dict[str, Any]) -> None:
        _one(candidate, "ProspectiveF3InterfaceRequirementV0_1R9")["status"] = "COMMITTED"

    def prospective_runtime(candidate: dict[str, Any]) -> None:
        _one(candidate, "ProspectiveF3InterfaceRequirementV0_1R9")["usable_in_runtime"] = True

    def prospective_profile(candidate: dict[str, Any]) -> None:
        _one(candidate, "ProspectiveF3InterfaceRequirementV0_1R9")["required_effect_authority_atom_schema_fingerprint"] = "9" * 64

    def production_receipt(candidate: dict[str, Any]) -> None:
        _role_row(candidate, "F1_TASK_SCOPE")["environment"] = "PRODUCTION"

    def synthetic_receipt_authority(candidate: dict[str, Any]) -> None:
        _role_row(candidate, "F1_TASK_SCOPE")["authority_eligible"] = True

    def witness_recovery(candidate: dict[str, Any]) -> None:
        _one(candidate, "F4SyntheticHandoffConstructibilityWitnessV0_1R9")["recovery_importable"] = True

    def witness_runtime(candidate: dict[str, Any]) -> None:
        _one(candidate, "F4SyntheticHandoffConstructibilityWitnessV0_1R9")["runtime_consumable"] = True

    def atom_set_mismatch(candidate: dict[str, Any]) -> None:
        _role_row(candidate, "F1_TASK_SCOPE")["authority_atom_set_fingerprint"] = "8" * 64

    def owner_atom_augmentation(candidate: dict[str, Any]) -> None:
        receipt = _role_row(candidate, "F1_TASK_SCOPE")
        atom = receipt["authority_atoms"][0]
        atom["resource_ref"] = f"{SYNTHETIC_REF_PREFIX}resource:b"
        atom["authority_tuple_fingerprint"] = tuple_fingerprint(atom)
        receipt["authority_atom_set_fingerprint"] = atom_set_fingerprint(receipt["authority_atoms"])

    def narrowing_atom_augmentation(candidate: dict[str, Any]) -> None:
        receipt = _narrowing_row(candidate, "HOST_CAPABILITY_RESOURCE_SCOPE")
        atom = receipt["authority_atoms"][0]
        atom["operation_kind"] = "F4_M0_SYNTHETIC_OTHER"
        atom["authority_tuple_fingerprint"] = tuple_fingerprint(atom)
        receipt["authority_atom_set_fingerprint"] = atom_set_fingerprint(receipt["authority_atoms"])

    def cartesian_cross_pair(candidate: dict[str, Any]) -> None:
        first = _role_row(candidate, "F1_TASK_SCOPE")
        second = _role_row(candidate, "F2_RESPONSIBILITY")
        first_atom = first["authority_atoms"][0]
        second_atom = second["authority_atoms"][0]
        first_atom["operation_kind"] = "F4_M0_SYNTHETIC_READ"
        second_atom["resource_ref"] = f"{SYNTHETIC_REF_PREFIX}resource:b"
        first_atom["authority_tuple_fingerprint"] = tuple_fingerprint(first_atom)
        second_atom["authority_tuple_fingerprint"] = tuple_fingerprint(second_atom)
        first["authority_atom_set_fingerprint"] = atom_set_fingerprint(first["authority_atoms"])
        second["authority_atom_set_fingerprint"] = atom_set_fingerprint(second["authority_atoms"])

    def missing_host_narrowing(candidate: dict[str, Any]) -> None:
        row = _narrowing_row(candidate, "HOST_CAPABILITY_RESOURCE_SCOPE")
        row["role"] = "JENN_EXACT_DECISION_SCOPE"
        row["owner_kind"] = "JENN_DECISION_CANONICAL_WRITER"

    def stale_foundational(candidate: dict[str, Any]) -> None:
        _observation(candidate, kind="OPERATION_REGISTRY")["observation_result"] = "STALE"

    def unknown_foundational(candidate: dict[str, Any]) -> None:
        _observation(candidate, kind="RESOURCE_KIND_REGISTRY")["observation_result"] = "INDETERMINATE"

    def stale_constraint(candidate: dict[str, Any]) -> None:
        _observation(candidate, kind="EFFECT_CONSTRAINT")["observation_result"] = "STALE"

    def latest_pointer_mismatch(candidate: dict[str, Any]) -> None:
        _observation(candidate, kind="OPERATION_REGISTRY")["observed_latest_input_fingerprint"] = "7" * 64

    def writer_head_advanced(candidate: dict[str, Any]) -> None:
        _observation(candidate, kind="RESOURCE_KIND_REGISTRY")["observed_owner_head_event_sequence"] = 41

    def pbl_scope_mismatch(candidate: dict[str, Any]) -> None:
        pbl = _one(candidate, "ProhibitedBoundaryAssessmentV0_1R9Final")
        atom = _one(candidate, "EffectAuthorityAtomV0_1R9")
        pbl["exact_effect_scope_ref"] = atom["atom_ref"]
        pbl["exact_effect_scope_fingerprint"] = atom["canonical_fingerprint"]

    def pbl_indeterminate(candidate: dict[str, Any]) -> None:
        _one(candidate, "ProhibitedBoundaryAssessmentV0_1R9Final")["evaluation_result"] = "INDETERMINATE"

    def policy_stale(candidate: dict[str, Any]) -> None:
        _one(candidate, "EffectAuthorizationPolicyAssessmentV0_1R9")["result"] = "STALE"

    def missing_upstream_claimed_authority(candidate: dict[str, Any]) -> None:
        _one(candidate, "SyntheticAuthorityIntersectionAssessmentV0_1R9")["authority_eligible"] = True

    def missing_jenn_claimed_current(candidate: dict[str, Any]) -> None:
        _one(candidate, "FinalAdmissionCurrentnessSnapshotV0_1R9")["snapshot_result"] = "CURRENT"

    def responsibility_route_change(candidate: dict[str, Any]) -> None:
        _role_row(candidate, "F2_RESPONSIBILITY")["responsibility_route"] = "DIRECT_RESPONSIBILITY"

    def ambient_green(candidate: dict[str, Any]) -> None:
        _one(candidate, "EffectAuthorityAtomV0_1R9")["operation_kind"] = "GREEN"

    def ambient_trusted(candidate: dict[str, Any]) -> None:
        _one(candidate, "EffectAuthorityAtomV0_1R9")["operation_kind"] = "TRUSTED"

    def ambient_urgent(candidate: dict[str, Any]) -> None:
        _one(candidate, "EffectAuthorityAtomV0_1R9")["operation_kind"] = "URGENT"

    def ambient_p3(candidate: dict[str, Any]) -> None:
        _one(candidate, "EffectAuthorityAtomV0_1R9")["operation_kind"] = "P3"

    def jenn_scope_resource_mismatch(candidate: dict[str, Any]) -> None:
        row = _narrowing_row(candidate, "HOST_CAPABILITY_RESOURCE_SCOPE")
        row["source_input_ref"] = f"{SYNTHETIC_REF_PREFIX}jenn-decision:resource-a"
        row["source_input_fingerprint"] = synthetic_leaf("jenn-decision:resource-a")
        atom = row["authority_atoms"][0]
        atom["resource_ref"] = f"{SYNTHETIC_REF_PREFIX}resource:b"
        atom["authority_tuple_fingerprint"] = tuple_fingerprint(atom)
        row["authority_atom_set_fingerprint"] = atom_set_fingerprint(row["authority_atoms"])

    def snapshot_basis_removed(candidate: dict[str, Any]) -> None:
        snapshot = _one(candidate, "FinalAdmissionCurrentnessSnapshotV0_1R9")
        snapshot["required_input_set_basis_refs"].pop()
        snapshot["required_input_set_basis_fingerprints"].pop()

    def transaction_split(candidate: dict[str, Any]) -> None:
        snapshot = _one(candidate, "FinalAdmissionCurrentnessSnapshotV0_1R9")
        snapshot["final_transaction_ref"] += ":split"

    def witness_effect(candidate: dict[str, Any]) -> None:
        _one(candidate, "F4SyntheticHandoffConstructibilityWitnessV0_1R9")["external_effect_count"] = 1

    def assertion_effect(candidate: dict[str, Any]) -> None:
        candidate["assertions"]["external_effect_count"] = 1

    def snapshot_missing_basis_edge(candidate: dict[str, Any]) -> None:
        atom_ordinal = next(
            index for index, entry in enumerate(candidate["object_store"], 1)
            if entry["object_key"] == "atom"
        )
        snapshot_node = next(
            node for node in candidate["nodes"]
            if node["kind"] == "FinalAdmissionCurrentnessSnapshotV0_1R9"
        )
        snapshot_node["depends_on_ordinals"].remove(atom_ordinal)

    cases: list[Case] = [
        ("actor_active_inference", signed(set_owner_result), {"RECEIPT_OWNER_RESULT"}),
        ("binding_indeterminate", signed(binding_indeterminate), {"RECEIPT_CURRENTNESS"}),
        ("stale_owner_receipt", signed(stale_receipt), {"RECEIPT_CURRENTNESS"}),
        ("prospective_accepted", signed(prospective_accepted), {"SCHEMA_FIELD_TYPE"}),
        ("prospective_committed_object", signed(prospective_committed), {"SCHEMA_FIELD_TYPE"}),
        ("prospective_runtime", signed(prospective_runtime), {"PROSPECTIVE_NONAUTHORITY"}),
        ("prospective_schema_profile", signed(prospective_profile), {"PROSPECTIVE_SCHEMA_PROFILE"}),
        ("synthetic_to_production", signed(production_receipt), {"AMBIENT_AUTHORITY_LABEL"}),
        ("synthetic_receipt_authority", signed(synthetic_receipt_authority), {"SYNTHETIC_RECEIPT_BOUNDARY"}),
        ("witness_recovery", signed(witness_recovery), {"SYNTHETIC_WITNESS_BOUNDARY"}),
        ("witness_runtime", signed(witness_runtime), {"SYNTHETIC_WITNESS_BOUNDARY"}),
        ("owner_atom_set_mismatch", signed(atom_set_mismatch), {"RECEIPT_ATOM_SET_FINGERPRINT"}),
        ("owner_atom_augmentation", signed(owner_atom_augmentation), {"OWNER_ATOM_RESOLUTION", "OWNER_ATOM_EXACT_COPY"}),
        ("narrowing_atom_augmentation", signed(narrowing_atom_augmentation), {"NARROWING_ATOM_RESOLUTION", "NARROWING_ATOM_EXACT_COPY"}),
        ("cartesian_cross_pair", signed(cartesian_cross_pair), {"OWNER_ATOM_RESOLUTION", "OWNER_ATOM_EXACT_COPY", "ATOMIC_TUPLE_INTERSECTION"}),
        ("missing_host_narrowing", signed(missing_host_narrowing), {"NARROWING_REQUIRED_ROLES"}),
        ("operation_registry_stale", signed(stale_foundational), {"CURRENTNESS_FAIL_CLOSED"}),
        ("resource_registry_unknown", signed(unknown_foundational), {"CURRENTNESS_FAIL_CLOSED"}),
        ("constraint_stale", signed(stale_constraint), {"CURRENTNESS_FAIL_CLOSED"}),
        ("latest_pointer_mismatch", signed(latest_pointer_mismatch), {"CURRENTNESS_LATEST_POINTER"}),
        ("writer_head_advanced", signed(writer_head_advanced), {"CURRENTNESS_WRITER_HEAD"}),
        ("pbl_scope_mismatch", signed(pbl_scope_mismatch), {"PBL_SCOPE_BINDING"}),
        ("pbl_indeterminate", signed(pbl_indeterminate), {"PBL_VETO_ONLY"}),
        ("policy_stale", signed(policy_stale), {"POLICY_INDEPENDENT_REQUIREMENT"}),
        ("missing_upstream_claimed_authority", signed(missing_upstream_claimed_authority), {"INTERSECTION_NONAUTHORITY"}),
        ("missing_jenn_claimed_current", signed(missing_jenn_claimed_current), {"SYNTHETIC_SNAPSHOT_BOUNDARY"}),
        ("responsibility_route_change", signed(responsibility_route_change), {"RECEIPT_RESPONSIBILITY_ROUTE"}),
        ("ambient_green_authority", signed(ambient_green), {"AMBIENT_AUTHORITY_LABEL"}),
        ("ambient_trust_authority", signed(ambient_trusted), {"AMBIENT_AUTHORITY_LABEL"}),
        ("ambient_urgency_authority", signed(ambient_urgent), {"AMBIENT_AUTHORITY_LABEL"}),
        ("ambient_p3_authority", signed(ambient_p3), {"AMBIENT_AUTHORITY_LABEL"}),
        ("jenn_scope_resource_mismatch", signed(jenn_scope_resource_mismatch), {"NARROWING_SOURCE_INPUT"}),
        ("snapshot_basis_removed", signed(snapshot_basis_removed), {"SNAPSHOT_REQUIRED_BASIS"}),
        ("transaction_split", signed(transaction_split), {"SNAPSHOT_TRANSACTION_BINDING"}),
        ("snapshot_missing_basis_edge", signed(snapshot_missing_basis_edge), {"DAG_DIRECT_EVIDENCE"}),
        ("nonzero_witness_effect", signed(witness_effect), {"ZERO_EFFECT"}),
        ("nonzero_assertion_effect", signed(assertion_effect), {"ASSERTIONS_EXACT"}),
    ]
    need(len(cases) >= 14, "MUTATION_FAMILY_COUNT", str(len(cases)))
    rejected = 0
    shallow_rules = {
        "SYNTHETIC_FINGERPRINT", "SYMBOL_SET_FINGERPRINT", "DAG_NODE_FINGERPRINT",
        "DAG_OBJECT_FINGERPRINT", "SYMBOL_TARGET_FINGERPRINT",
    }
    for name, mutate, expected_rules in cases:
        candidate = copy.deepcopy(root)
        try:
            mutate(candidate)
            validate_fixture(candidate)
        except Reject as exc:
            need(exc.rule not in shallow_rules, "MUTATION_SHALLOW_REJECTION", f"{name}:{exc}")
            need(exc.rule in expected_rules, "MUTATION_WRONG_RULE", f"{name}: expected {sorted(expected_rules)}, got {exc.rule}")
            rejected += 1
        else:
            raise Reject("MUTATION_ACCEPTED", name)
    need(rejected == len(cases), "MUTATION_REJECTION_COUNT", f"{rejected}/{len(cases)}")
    return rejected


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the F4 R9 Section-10 synthetic non-authority M0-A witness."
    )
    parser.add_argument("fixture", nargs="?", type=Path, default=DEFAULT)
    parser.add_argument("--skip-mutations", action="store_true")
    args = parser.parse_args(argv)
    try:
        root, raw = load(args.fixture)
        summary = validate_fixture(root, raw)
        summary["negative_mutations_rejected"] = (
            0 if args.skip_mutations else run_mutations(root)
        )
    except (Reject, OSError, KeyError, IndexError, StopIteration, TypeError, ValueError) as exc:
        reason = str(exc)
        print(json.dumps({"result": "BLOCK", "reason": reason}, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
