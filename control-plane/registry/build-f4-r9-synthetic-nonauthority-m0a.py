#!/usr/bin/env python3
"""Build the F4 R9 Section-10 synthetic non-authority M0-A fixture.

This builder is offline and generative only.  It deliberately emits no native
F1/F2/F3 object, no accepted/committed F3 object, no TaskPermit, and no
operational accepted-handoff object.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = (
    HERE
    / "examples"
    / "2026-07-16-agents-os-f4-r9-synthetic-nonauthority-m0a-witness-v0.1.json"
)
CONTRACT = "F4_TASKPERMIT_HOST_AUTHENTICATION_EFFECT_ADMISSION_V0_1_R9_ATOMIC_BUNDLE"
ROOT_SCHEMA = "agents-os.f4-r9-synthetic-nonauthority-m0a.v0.1"
SYNTHETIC_NAMESPACE = "synthetic-f4-r9"
SYNTHETIC_WITNESS_DOMAIN = "agents-os.f4-r9-synthetic-witness.v0.1"


def canonical_bytes(value: Any) -> bytes:
    def walk(item: Any) -> None:
        if isinstance(item, float):
            raise ValueError("float is not canonical")
        if isinstance(item, str):
            if unicodedata.normalize("NFC", item) != item or item != item.strip() or "\0" in item:
                raise ValueError("non-canonical string")
        elif isinstance(item, list):
            for child in item:
                walk(child)
        elif isinstance(item, dict):
            for key, child in item.items():
                walk(key)
                walk(child)

    walk(value)
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def synthetic_leaf(label: str) -> str:
    return digest([SYNTHETIC_WITNESS_DOMAIN, "leaf", label])


def fields(text: str) -> list[str]:
    return text.split()


def spec(
    interface: str | None,
    ordered_fields: list[str],
    fingerprint_field: str | None,
    registry_kind: str,
) -> dict[str, Any]:
    return {
        "interface_version": interface,
        "fields": ordered_fields,
        "fingerprint_field": fingerprint_field,
        "registry_kind": registry_kind,
    }


SECTION10_SCHEMAS: dict[str, dict[str, Any]] = {
    "UpstreamAuthorityAssessmentReceiptV0_1R9": spec(
        "agents-os.upstream-authority-assessment-receipt.v0.1-r9",
        fields("interface_version receipt_ref receipt_revision role owner_phase owner_contract_ref owner_contract_fingerprint owner_result_profile_ref owner_result_profile_fingerprint responsibility_route assessment_schema_name assessment_ref assessment_fingerprint subject_schema_name subject_ref subject_revision subject_fingerprint owner_result owner_head_event_sequence assessed_at_event_sequence resolved_at_watermark_event_sequence owner_currentness authority_atom_set_mode authority_atoms authority_atom_set_fingerprint environment authority_eligible canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "AuthorityInputCurrentnessObservationV0_1R9": spec(
        "agents-os.authority-input-currentness-observation.v0.1-r9",
        fields("interface_version observation_ref input_kind input_ref input_fingerprint canonical_writer_ref canonical_writer_fingerprint canonical_latest_pointer_ref observed_latest_input_ref observed_latest_input_fingerprint observed_owner_head_event_sequence observed_latest_pointer_revision observed_at_event_sequence observation_result environment authority_eligible canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "FinalAdmissionCurrentnessSnapshotV0_1R9": spec(
        "agents-os.final-admission-currentness-snapshot.v0.1-r9",
        fields("interface_version snapshot_ref required_input_roles required_input_set_basis_refs required_input_set_basis_fingerprints required_input_set_basis_fingerprint present_input_refs missing_required_input_roles observation_refs observation_fingerprints observed_writer_head_event_sequences observation_set_fingerprint final_transaction_ref final_transaction_fingerprint transaction_binding_rule final_snapshot_event_sequence snapshot_result environment authority_eligible canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "ProspectiveF3InterfaceRequirementV0_1R9": spec(
        "agents-os.prospective-f3-interface-requirement.v0.1-r9",
        fields("interface_version requirement_ref owner required_interface_kind required_effect_authority_atom_schema_fingerprint required_intake_result status usable_in_runtime synthetic_fixture_only authority_eligible canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "EffectConstraintV0_1R9": spec(
        "agents-os.effect-constraint.v0.1-r9",
        fields("interface_version constraint_ref payload_schema_fingerprint external_effect_allowed provider_call_allowed raw_secret_allowed requires_human_presence not_before_utc_ms expires_at_utc_ms canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "EffectAuthorityAtomV0_1R9": spec(
        "agents-os.effect-authority-atom.v0.1-r9",
        fields("interface_version atom_ref operation_registry_ref operation_registry_fingerprint operation_kind resource_kind_registry_ref resource_kind_registry_fingerprint resource_kind resource_ref constraint_ref constraint_fingerprint authority_tuple_fingerprint canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "F4SyntheticExactEffectScopeV0_1R9": spec(
        "agents-os.f4-synthetic-exact-effect-scope.v0.1-r9",
        fields("interface_version scope_ref effect_authority_atom_ref effect_authority_atom_fingerprint effect_authority_tuple_fingerprint environment authority_eligible canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "SyntheticAuthorityIntersectionAssessmentV0_1R9": spec(
        "agents-os.synthetic-authority-intersection-assessment.v0.1-r9",
        fields("interface_version assessment_ref required_scope_roles present_scope_roles missing_scope_roles source_receipt_refs source_receipt_fingerprints source_atom_set_fingerprints intersection_tuple_fingerprints intersection_set_fingerprint result environment authority_eligible canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "EffectScopeNarrowingReceiptV0_1R9": spec(
        "agents-os.effect-scope-narrowing-receipt.v0.1-r9",
        fields("interface_version receipt_ref receipt_revision role owner_kind source_contract_ref source_contract_fingerprint source_input_ref source_input_fingerprint source_result_profile_ref source_result_profile_fingerprint source_result authority_atoms authority_atom_set_fingerprint owner_head_event_sequence evaluated_at_event_sequence resolved_at_watermark_event_sequence environment authority_eligible canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "ProhibitedBoundaryAssessmentV0_1R9Final": spec(
        "agents-os.prohibited-boundary-assessment.v0.1-r9-final",
        fields("interface_version assessment_ref exact_effect_scope_ref exact_effect_scope_fingerprint prohibited_behavior_list_revision evaluated_rule_set_fingerprint matched_rule_ids evaluation_result evaluated_at_event_sequence canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "EffectAuthorizationPolicyAssessmentV0_1R9": spec(
        "agents-os.effect-authorization-policy-assessment.v0.1-r9",
        fields("interface_version assessment_ref exact_effect_scope_ref exact_effect_scope_fingerprint policy_bundle_revision authorization_requirement assessed_at_event_sequence result canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
    "F4SyntheticHandoffConstructibilityWitnessV0_1R9": spec(
        "agents-os.f4-synthetic-handoff-constructibility-witness.v0.1-r9",
        fields("interface_version witness_ref witness_namespace environment fingerprint_domain prospective_f3_requirement_ref prospective_f3_requirement_fingerprint hypothetical_effect_atom_ref hypothetical_effect_atom_fingerprint intersection_assessment_ref intersection_assessment_fingerprint currentness_snapshot_ref currentness_snapshot_fingerprint reducer_trace_fingerprint claim_state authority_eligible runtime_consumable recovery_importable physical_effect_boundary terminal_outcome external_effect_count provider_call_count raw_secret_count canonical_fingerprint"),
        "canonical_fingerprint",
        "SECTION10",
    ),
}


WRAPPER_SCHEMAS: dict[str, dict[str, Any]] = {
    "F4R9SyntheticNonAuthorityRoot": spec(
        None,
        fields("schema_version contract_version object_store canonical_symbol_table nodes schema_inventory assertions"),
        None,
        "WRAPPER",
    ),
    "ObjectStoreEntryV0_1R9": spec(
        None,
        fields("object_key exact_schema_name object"),
        None,
        "WRAPPER",
    ),
    "CanonicalSymbolBindingV0_1R9": spec(
        "agents-os.canonical-symbol-binding.v0.1-r9",
        fields("interface_version symbol_ref target_exact_schema_name target_fingerprint target_inventory_pointer canonical_fingerprint"),
        "canonical_fingerprint",
        "NORMATIVE",
    ),
    "CrossObjectSymbolTableV0_1R9": spec(
        "agents-os.cross-object-symbol-table.v0.1-r9",
        fields("interface_version bindings binding_set_fingerprint canonical_fingerprint"),
        "canonical_fingerprint",
        "NORMATIVE",
    ),
    "EvidenceNodeV0_1R9": spec(
        None,
        fields("ordinal kind object_pointer object_fingerprint depends_on_ordinals node_fingerprint"),
        "node_fingerprint",
        "WRAPPER",
    ),
    "SchemaInventoryEntryV0_1R9": spec(
        None,
        fields("json_pointer exact_schema_name interface_version fingerprint_field ordered_field_names registry_kind"),
        None,
        "WRAPPER",
    ),
    "SyntheticAssertionsV0_1R9": spec(
        None,
        fields("accepted_handoff_count synthetic_constructibility_witness_count runtime_consumable_count external_effect_count provider_call_count raw_secret_count terminal_outcome"),
        None,
        "WRAPPER",
    ),
}


ALL_SCHEMAS = {**SECTION10_SCHEMAS, **WRAPPER_SCHEMAS}


EFFECT_ATOM_SCHEMA_PROFILE_DESCRIPTOR = {
    "interface_version": "agents-os.effect-authority-atom.v0.1-r9",
    "ordered_field_names": SECTION10_SCHEMAS["EffectAuthorityAtomV0_1R9"]["fields"],
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
        "operation_kind": ["operation_registry_ref", "operation_registry_fingerprint", "canonical_current_resolution_required"],
        "resource_kind": ["resource_kind_registry_ref", "resource_kind_registry_fingerprint", "canonical_current_resolution_required"],
    },
    "nullability": "none",
    "canonical_fingerprint_rule": [
        SYNTHETIC_WITNESS_DOMAIN,
        "schema",
        "EffectAuthorityAtomV0_1R9",
        "ordered_values_excluding_canonical_fingerprint",
    ],
    "authority_tuple_fingerprint_rule": [
        SYNTHETIC_WITNESS_DOMAIN,
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

OWNER_RESULT_PROFILE_MATRIX = [
    ["F1_TASK_SCOPE", "F1", "TASK_SCOPE_CURRENT", ["NOT_APPLICABLE"]],
    ["F2_ACTOR_BINDING", "F2", "BINDING_CURRENT", ["NOT_APPLICABLE"]],
    [
        "F2_RESPONSIBILITY",
        "F2",
        "RESPONSIBILITY_CURRENT",
        ["DELEGATED_RESPONSIBILITY", "DIRECT_RESPONSIBILITY"],
    ],
    ["F2_DELEGATION", "F2", "DELEGATION_CURRENT", ["NOT_APPLICABLE"]],
    ["F3_COMMAND", "F3", "COMMAND_COMMITTED_CURRENT", ["NOT_APPLICABLE"]],
]


def fp(schema: str, obj: dict[str, Any]) -> str:
    profile = ALL_SCHEMAS[schema]
    fp_field = profile["fingerprint_field"]
    values = [obj[name] for name in profile["fields"] if name != fp_field]
    return digest([SYNTHETIC_WITNESS_DOMAIN, "schema", schema, *values])


def stamp(schema: str, values: dict[str, Any]) -> dict[str, Any]:
    profile = ALL_SCHEMAS[schema]
    fp_field = profile["fingerprint_field"]
    expected = [name for name in profile["fields"] if name != fp_field]
    if list(values) != expected:
        raise ValueError(f"{schema} field order mismatch: {list(values)!r} != {expected!r}")
    result = copy.deepcopy(values)
    if fp_field:
        result[fp_field] = fp(schema, result)
    return result


class Assembler:
    def __init__(self) -> None:
        self.root: dict[str, Any] = {
            "schema_version": ROOT_SCHEMA,
            "contract_version": CONTRACT,
            "object_store": [],
            "canonical_symbol_table": {},
            "nodes": [],
            "schema_inventory": [],
            "assertions": {
                "accepted_handoff_count": 0,
                "synthetic_constructibility_witness_count": 1,
                "runtime_consumable_count": 0,
                "external_effect_count": 0,
                "provider_call_count": 0,
                "raw_secret_count": 0,
                "terminal_outcome": "NOT_EXECUTED",
            },
        }
        self.symbols: dict[str, tuple[str, str, dict[str, Any]]] = {}

    def put(self, key: str, schema: str, obj: dict[str, Any], symbol_ref: str) -> None:
        index = len(self.root["object_store"])
        self.root["object_store"].append(
            {"object_key": key, "exact_schema_name": schema, "object": obj}
        )
        if symbol_ref in self.symbols:
            raise ValueError(f"duplicate symbol: {symbol_ref}")
        self.symbols[symbol_ref] = (f"/object_store/{index}/object", schema, obj)


def atom_set_fingerprint(atoms: list[dict[str, Any]]) -> str:
    tuple_fingerprints = sorted(
        {atom["authority_tuple_fingerprint"] for atom in atoms},
        key=lambda value: value.encode("utf-8"),
    )
    if len(tuple_fingerprints) != len(atoms):
        raise ValueError("duplicate authority tuple")
    return digest([SYNTHETIC_WITNESS_DOMAIN, "owner-issued-atom-set", tuple_fingerprints])


def make_receipt(
    role: str,
    owner: str,
    ordinal: int,
    atoms: list[dict[str, Any]],
) -> dict[str, Any]:
    prefix = f"{SYNTHETIC_NAMESPACE}:receipt:{role.lower()}"
    result_by_role = {
        "F1_TASK_SCOPE": "TASK_SCOPE_CURRENT",
        "F2_ACTOR_BINDING": "BINDING_CURRENT",
        "F2_RESPONSIBILITY": "RESPONSIBILITY_CURRENT",
    }
    mode = "GATE_ONLY" if role == "F2_ACTOR_BINDING" else "OWNER_ISSUED_ATOM_SET"
    responsibility_route = (
        "DELEGATED_RESPONSIBILITY" if role == "F2_RESPONSIBILITY" else "NOT_APPLICABLE"
    )
    if mode == "GATE_ONLY" and atoms:
        raise ValueError("gate-only receipt cannot contain authority atoms")
    if mode == "OWNER_ISSUED_ATOM_SET" and not atoms:
        raise ValueError("scope-bearing receipt requires authority atoms")
    return stamp(
        "UpstreamAuthorityAssessmentReceiptV0_1R9",
        {
            "interface_version": "agents-os.upstream-authority-assessment-receipt.v0.1-r9",
            "receipt_ref": prefix,
            "receipt_revision": 1,
            "role": role,
            "owner_phase": owner,
            "owner_contract_ref": f"{SYNTHETIC_NAMESPACE}:owner-contract:{owner.lower()}",
            "owner_contract_fingerprint": synthetic_leaf(f"{owner}:contract"),
            "owner_result_profile_ref": f"{SYNTHETIC_NAMESPACE}:owner-result-profile:normalized-v1",
            "owner_result_profile_fingerprint": digest(
                [SYNTHETIC_WITNESS_DOMAIN, "owner-result-profile", OWNER_RESULT_PROFILE_MATRIX]
            ),
            "responsibility_route": responsibility_route,
            "assessment_schema_name": f"SYNTHETIC_{role}_ASSESSMENT",
            "assessment_ref": f"{SYNTHETIC_NAMESPACE}:assessment:{role.lower()}",
            "assessment_fingerprint": synthetic_leaf(f"{role}:assessment"),
            "subject_schema_name": f"SYNTHETIC_{role}_SUBJECT",
            "subject_ref": f"{SYNTHETIC_NAMESPACE}:subject:{role.lower()}",
            "subject_revision": 1,
            "subject_fingerprint": synthetic_leaf(f"{role}:subject"),
            "owner_result": result_by_role[role],
            "owner_head_event_sequence": 10 + ordinal,
            "assessed_at_event_sequence": 20 + ordinal,
            "resolved_at_watermark_event_sequence": 30 + ordinal,
            "owner_currentness": "CURRENT",
            "authority_atom_set_mode": mode,
            "authority_atoms": copy.deepcopy(atoms),
            "authority_atom_set_fingerprint": atom_set_fingerprint(atoms),
            "environment": "SYNTHETIC_TEST",
            "authority_eligible": False,
        },
    )


def make_currentness_observation(
    input_kind: str,
    input_ref: str,
    input_fingerprint: str,
    owner_head: int,
    ordinal: int,
) -> dict[str, Any]:
    label = f"{input_kind.lower()}:{ordinal}"
    return stamp(
        "AuthorityInputCurrentnessObservationV0_1R9",
        {
            "interface_version": "agents-os.authority-input-currentness-observation.v0.1-r9",
            "observation_ref": f"{SYNTHETIC_NAMESPACE}:currentness:{label}",
            "input_kind": input_kind,
            "input_ref": input_ref,
            "input_fingerprint": input_fingerprint,
            "canonical_writer_ref": f"{SYNTHETIC_NAMESPACE}:canonical-writer:{label}",
            "canonical_writer_fingerprint": synthetic_leaf(f"canonical-writer:{label}"),
            "canonical_latest_pointer_ref": f"{SYNTHETIC_NAMESPACE}:latest-pointer:{label}",
            "observed_latest_input_ref": input_ref,
            "observed_latest_input_fingerprint": input_fingerprint,
            "observed_owner_head_event_sequence": owner_head,
            "observed_latest_pointer_revision": 1,
            "observed_at_event_sequence": 60 + ordinal,
            "observation_result": "CURRENT",
            "environment": "SYNTHETIC_TEST",
            "authority_eligible": False,
        },
    )


def make_narrowing_receipt(
    role: str,
    owner_kind: str,
    source_input_ref: str,
    source_input_fingerprint: str,
    atoms: list[dict[str, Any]],
    ordinal: int,
) -> dict[str, Any]:
    label = role.lower()
    return stamp(
        "EffectScopeNarrowingReceiptV0_1R9",
        {
            "interface_version": "agents-os.effect-scope-narrowing-receipt.v0.1-r9",
            "receipt_ref": f"{SYNTHETIC_NAMESPACE}:narrowing:{label}",
            "receipt_revision": 1,
            "role": role,
            "owner_kind": owner_kind,
            "source_contract_ref": f"{SYNTHETIC_NAMESPACE}:narrowing-contract:{label}",
            "source_contract_fingerprint": synthetic_leaf(f"narrowing-contract:{label}"),
            "source_input_ref": source_input_ref,
            "source_input_fingerprint": source_input_fingerprint,
            "source_result_profile_ref": f"{SYNTHETIC_NAMESPACE}:narrowing-result-profile:v1",
            "source_result_profile_fingerprint": digest(
                [
                    SYNTHETIC_WITNESS_DOMAIN,
                    "narrowing-result-profile",
                    [
                        ["POLICY_SCOPE", "POLICY_CANONICAL_WRITER"],
                        ["HOST_CAPABILITY_RESOURCE_SCOPE", "HOST_TRUST_CANONICAL_WRITER"],
                        ["JENN_EXACT_DECISION_SCOPE", "JENN_DECISION_CANONICAL_WRITER"],
                    ],
                    "CURRENT_SCOPE_CONSTRAINT",
                ]
            ),
            "source_result": "CURRENT_SCOPE_CONSTRAINT",
            "authority_atoms": copy.deepcopy(atoms),
            "authority_atom_set_fingerprint": atom_set_fingerprint(atoms),
            "owner_head_event_sequence": 40 + ordinal,
            "evaluated_at_event_sequence": 50 + ordinal,
            "resolved_at_watermark_event_sequence": 60 + ordinal,
            "environment": "SYNTHETIC_TEST",
            "authority_eligible": False,
        },
    )


def make_currentness_snapshot(
    observations: list[dict[str, Any]],
    missing_required_input_roles: list[str],
    required_input_roles: list[str],
    basis_pairs: list[tuple[str, str]],
) -> dict[str, Any]:
    ordered = sorted(observations, key=lambda item: item["input_ref"].encode("utf-8"))
    present_input_refs = [item["input_ref"] for item in ordered]
    observation_refs = [item["observation_ref"] for item in ordered]
    observation_fingerprints = [item["canonical_fingerprint"] for item in ordered]
    heads = [item["observed_owner_head_event_sequence"] for item in ordered]
    ordered_basis = sorted(basis_pairs, key=lambda item: item[0].encode("utf-8"))
    basis_refs = [item[0] for item in ordered_basis]
    basis_fingerprints = [item[1] for item in ordered_basis]
    basis_fingerprint = digest(
        [
            SYNTHETIC_WITNESS_DOMAIN,
            "required-input-basis",
            required_input_roles,
            basis_refs,
            basis_fingerprints,
        ]
    )
    observation_set_fingerprint = digest(
        [
            SYNTHETIC_WITNESS_DOMAIN,
            "observation-set",
            present_input_refs,
            missing_required_input_roles,
            observation_refs,
            observation_fingerprints,
            heads,
        ]
    )
    final_transaction_ref = f"{SYNTHETIC_NAMESPACE}:final-transaction:m0-a"
    final_transaction_fingerprint = digest(
        [
            SYNTHETIC_WITNESS_DOMAIN,
            "final-transaction",
            final_transaction_ref,
            basis_fingerprint,
            observation_set_fingerprint,
            100,
        ]
    )
    return stamp(
        "FinalAdmissionCurrentnessSnapshotV0_1R9",
        {
            "interface_version": "agents-os.final-admission-currentness-snapshot.v0.1-r9",
            "snapshot_ref": f"{SYNTHETIC_NAMESPACE}:currentness-snapshot:m0-a",
            "required_input_roles": required_input_roles,
            "required_input_set_basis_refs": basis_refs,
            "required_input_set_basis_fingerprints": basis_fingerprints,
            "required_input_set_basis_fingerprint": basis_fingerprint,
            "present_input_refs": present_input_refs,
            "missing_required_input_roles": missing_required_input_roles,
            "observation_refs": observation_refs,
            "observation_fingerprints": observation_fingerprints,
            "observed_writer_head_event_sequences": heads,
            "observation_set_fingerprint": observation_set_fingerprint,
            "final_transaction_ref": final_transaction_ref,
            "final_transaction_fingerprint": final_transaction_fingerprint,
            "transaction_binding_rule": "EXACT_SAME_TRANSACTION",
            "final_snapshot_event_sequence": 100,
            "snapshot_result": "NOT_AUTHORITY_ELIGIBLE",
            "environment": "SYNTHETIC_TEST",
            "authority_eligible": False,
        },
    )


def build_fixture() -> dict[str, Any]:
    a = Assembler()

    atom_schema_fingerprint = digest(
        [SYNTHETIC_WITNESS_DOMAIN, "schema-profile", EFFECT_ATOM_SCHEMA_PROFILE_DESCRIPTOR]
    )
    prospective = stamp(
        "ProspectiveF3InterfaceRequirementV0_1R9",
        {
            "interface_version": "agents-os.prospective-f3-interface-requirement.v0.1-r9",
            "requirement_ref": f"{SYNTHETIC_NAMESPACE}:prospective-f3:closed-effect-intent-command",
            "owner": "F3",
            "required_interface_kind": "CLOSED_EFFECT_INTENT_COMMAND_TYPE",
            "required_effect_authority_atom_schema_fingerprint": atom_schema_fingerprint,
            "required_intake_result": "COMMITTED",
            "status": "UNACCEPTED_DOWNSTREAM_REQUIREMENT",
            "usable_in_runtime": False,
            "synthetic_fixture_only": True,
            "authority_eligible": False,
        },
    )
    a.put("prospective-f3", "ProspectiveF3InterfaceRequirementV0_1R9", prospective, prospective["requirement_ref"])

    constraint = stamp(
        "EffectConstraintV0_1R9",
        {
            "interface_version": "agents-os.effect-constraint.v0.1-r9",
            "constraint_ref": f"{SYNTHETIC_NAMESPACE}:constraint:no-effect",
            "payload_schema_fingerprint": synthetic_leaf("payload:empty-object"),
            "external_effect_allowed": False,
            "provider_call_allowed": False,
            "raw_secret_allowed": False,
            "requires_human_presence": False,
            "not_before_utc_ms": 1000,
            "expires_at_utc_ms": 5000,
        },
    )
    a.put("constraint", "EffectConstraintV0_1R9", constraint, constraint["constraint_ref"])

    authority_tuple_fingerprint = digest(
        [
            SYNTHETIC_WITNESS_DOMAIN,
            "authority-tuple",
            synthetic_leaf("operation-registry:v1"),
            "F4_M0_SYNTHETIC_NOOP",
            synthetic_leaf("resource-kind-registry:v1"),
            "SYNTHETIC_M0_RESOURCE",
            f"{SYNTHETIC_NAMESPACE}:resource:a",
            constraint["canonical_fingerprint"],
        ]
    )
    atom = stamp(
        "EffectAuthorityAtomV0_1R9",
        {
            "interface_version": "agents-os.effect-authority-atom.v0.1-r9",
            "atom_ref": f"{SYNTHETIC_NAMESPACE}:atom:noop:resource-a",
            "operation_registry_ref": f"{SYNTHETIC_NAMESPACE}:operation-registry:v1",
            "operation_registry_fingerprint": synthetic_leaf("operation-registry:v1"),
            "operation_kind": "F4_M0_SYNTHETIC_NOOP",
            "resource_kind_registry_ref": f"{SYNTHETIC_NAMESPACE}:resource-kind-registry:v1",
            "resource_kind_registry_fingerprint": synthetic_leaf("resource-kind-registry:v1"),
            "resource_kind": "SYNTHETIC_M0_RESOURCE",
            "resource_ref": f"{SYNTHETIC_NAMESPACE}:resource:a",
            "constraint_ref": constraint["constraint_ref"],
            "constraint_fingerprint": constraint["canonical_fingerprint"],
            "authority_tuple_fingerprint": authority_tuple_fingerprint,
        },
    )
    a.put("atom", "EffectAuthorityAtomV0_1R9", atom, atom["atom_ref"])

    scope = stamp(
        "F4SyntheticExactEffectScopeV0_1R9",
        {
            "interface_version": "agents-os.f4-synthetic-exact-effect-scope.v0.1-r9",
            "scope_ref": f"{SYNTHETIC_NAMESPACE}:scope:m0-a",
            "effect_authority_atom_ref": atom["atom_ref"],
            "effect_authority_atom_fingerprint": atom["canonical_fingerprint"],
            "effect_authority_tuple_fingerprint": atom["authority_tuple_fingerprint"],
            "environment": "SYNTHETIC_TEST",
            "authority_eligible": False,
        },
    )
    a.put("scope", "F4SyntheticExactEffectScopeV0_1R9", scope, scope["scope_ref"])

    foundational_currentness: dict[str, dict[str, Any]] = {}
    foundational_inputs = [
        (
            "OPERATION_REGISTRY",
            atom["operation_registry_ref"],
            atom["operation_registry_fingerprint"],
            40,
            8,
        ),
        (
            "RESOURCE_KIND_REGISTRY",
            atom["resource_kind_registry_ref"],
            atom["resource_kind_registry_fingerprint"],
            40,
            9,
        ),
        (
            "EFFECT_CONSTRAINT",
            constraint["constraint_ref"],
            constraint["canonical_fingerprint"],
            40,
            10,
        ),
    ]
    for kind, input_ref, input_fp, owner_head, ordinal in foundational_inputs:
        observation = make_currentness_observation(
            kind,
            input_ref,
            input_fp,
            owner_head,
            ordinal,
        )
        foundational_currentness[kind] = observation
        a.put(
            f"currentness-{kind.lower()}",
            "AuthorityInputCurrentnessObservationV0_1R9",
            observation,
            observation["observation_ref"],
        )

    receipts: dict[str, dict[str, Any]] = {}
    receipt_currentness: dict[str, dict[str, Any]] = {}
    for ordinal, (role, owner) in enumerate(
        (("F1_TASK_SCOPE", "F1"), ("F2_ACTOR_BINDING", "F2"), ("F2_RESPONSIBILITY", "F2")),
        1,
    ):
        receipt_atoms = [] if role == "F2_ACTOR_BINDING" else [copy.deepcopy(atom)]
        receipt = make_receipt(role, owner, ordinal, receipt_atoms)
        receipts[role] = receipt
        a.put(f"receipt-{role.lower()}", "UpstreamAuthorityAssessmentReceiptV0_1R9", receipt, receipt["receipt_ref"])
        observation = make_currentness_observation(
            "OWNER_RECEIPT",
            receipt["receipt_ref"],
            receipt["canonical_fingerprint"],
            receipt["owner_head_event_sequence"],
            ordinal,
        )
        receipt_currentness[role] = observation
        a.put(
            f"currentness-{role.lower()}",
            "AuthorityInputCurrentnessObservationV0_1R9",
            observation,
            observation["observation_ref"],
        )

    pbl = stamp(
        "ProhibitedBoundaryAssessmentV0_1R9Final",
        {
            "interface_version": "agents-os.prohibited-boundary-assessment.v0.1-r9-final",
            "assessment_ref": f"{SYNTHETIC_NAMESPACE}:pbl-assessment:m0-a",
            "exact_effect_scope_ref": scope["scope_ref"],
            "exact_effect_scope_fingerprint": scope["canonical_fingerprint"],
            "prohibited_behavior_list_revision": f"{SYNTHETIC_NAMESPACE}:pbl:revision:1",
            "evaluated_rule_set_fingerprint": synthetic_leaf("pbl:complete-rule-set"),
            "matched_rule_ids": [],
            "evaluation_result": "NO_PROHIBITED_MATCH",
            "evaluated_at_event_sequence": 40,
        },
    )
    a.put("pbl", "ProhibitedBoundaryAssessmentV0_1R9Final", pbl, pbl["assessment_ref"])
    pbl_currentness = make_currentness_observation(
        "PBL_ASSESSMENT",
        pbl["assessment_ref"],
        pbl["canonical_fingerprint"],
        pbl["evaluated_at_event_sequence"],
        4,
    )
    a.put(
        "currentness-pbl",
        "AuthorityInputCurrentnessObservationV0_1R9",
        pbl_currentness,
        pbl_currentness["observation_ref"],
    )

    policy = stamp(
        "EffectAuthorizationPolicyAssessmentV0_1R9",
        {
            "interface_version": "agents-os.effect-authorization-policy-assessment.v0.1-r9",
            "assessment_ref": f"{SYNTHETIC_NAMESPACE}:policy-assessment:m0-a",
            "exact_effect_scope_ref": scope["scope_ref"],
            "exact_effect_scope_fingerprint": scope["canonical_fingerprint"],
            "policy_bundle_revision": f"{SYNTHETIC_NAMESPACE}:policy:revision:1",
            "authorization_requirement": "EXACT_CURRENT_JENN_AUTHORIZATION_REQUIRED",
            "assessed_at_event_sequence": 40,
            "result": "CURRENT",
        },
    )
    a.put("policy", "EffectAuthorizationPolicyAssessmentV0_1R9", policy, policy["assessment_ref"])
    policy_currentness = make_currentness_observation(
        "AUTHORIZATION_POLICY_ASSESSMENT",
        policy["assessment_ref"],
        policy["canonical_fingerprint"],
        policy["assessed_at_event_sequence"],
        5,
    )
    a.put(
        "currentness-policy",
        "AuthorityInputCurrentnessObservationV0_1R9",
        policy_currentness,
        policy_currentness["observation_ref"],
    )

    narrowing_receipts: dict[str, dict[str, Any]] = {}
    narrowing_currentness: dict[str, dict[str, Any]] = {}
    narrowing_inputs = [
        (
            "HOST_CAPABILITY_RESOURCE_SCOPE",
            "HOST_TRUST_CANONICAL_WRITER",
            f"{SYNTHETIC_NAMESPACE}:host-scope-assessment:m0-a",
            synthetic_leaf("host-scope-assessment:m0-a"),
        ),
        (
            "POLICY_SCOPE",
            "POLICY_CANONICAL_WRITER",
            policy["assessment_ref"],
            policy["canonical_fingerprint"],
        ),
    ]
    for ordinal, (role, owner_kind, source_ref, source_fp) in enumerate(
        narrowing_inputs,
        6,
    ):
        narrowing = make_narrowing_receipt(
            role,
            owner_kind,
            source_ref,
            source_fp,
            [copy.deepcopy(atom)],
            ordinal,
        )
        narrowing_receipts[role] = narrowing
        key = role.lower()
        a.put(
            f"narrowing-{key}",
            "EffectScopeNarrowingReceiptV0_1R9",
            narrowing,
            narrowing["receipt_ref"],
        )
        observation = make_currentness_observation(
            "SCOPE_NARROWING_RECEIPT",
            narrowing["receipt_ref"],
            narrowing["canonical_fingerprint"],
            narrowing["owner_head_event_sequence"],
            ordinal,
        )
        narrowing_currentness[role] = observation
        a.put(
            f"currentness-narrowing-{key}",
            "AuthorityInputCurrentnessObservationV0_1R9",
            observation,
            observation["observation_ref"],
        )

    required_scope_roles = [
        "F1_TASK_SCOPE",
        "F2_DELEGATION",
        "F2_RESPONSIBILITY",
        "F3_COMMAND",
        "HOST_CAPABILITY_RESOURCE_SCOPE",
        "JENN_EXACT_DECISION_SCOPE",
        "POLICY_SCOPE",
    ]
    present_scope_roles = [
        "F1_TASK_SCOPE",
        "F2_RESPONSIBILITY",
        "HOST_CAPABILITY_RESOURCE_SCOPE",
        "POLICY_SCOPE",
    ]
    missing_scope_roles = [
        "F2_DELEGATION",
        "F3_COMMAND",
        "JENN_EXACT_DECISION_SCOPE",
    ]
    scope_receipts = {
        "F1_TASK_SCOPE": receipts["F1_TASK_SCOPE"],
        "F2_RESPONSIBILITY": receipts["F2_RESPONSIBILITY"],
        **narrowing_receipts,
    }
    intersection_tuple_fingerprints = [atom["authority_tuple_fingerprint"]]
    intersection = stamp(
        "SyntheticAuthorityIntersectionAssessmentV0_1R9",
        {
            "interface_version": "agents-os.synthetic-authority-intersection-assessment.v0.1-r9",
            "assessment_ref": f"{SYNTHETIC_NAMESPACE}:intersection:m0-a",
            "required_scope_roles": required_scope_roles,
            "present_scope_roles": present_scope_roles,
            "missing_scope_roles": missing_scope_roles,
            "source_receipt_refs": [scope_receipts[role]["receipt_ref"] for role in present_scope_roles],
            "source_receipt_fingerprints": [scope_receipts[role]["canonical_fingerprint"] for role in present_scope_roles],
            "source_atom_set_fingerprints": [scope_receipts[role]["authority_atom_set_fingerprint"] for role in present_scope_roles],
            "intersection_tuple_fingerprints": intersection_tuple_fingerprints,
            "intersection_set_fingerprint": digest(
                [SYNTHETIC_WITNESS_DOMAIN, "intersection-set", intersection_tuple_fingerprints]
            ),
            "result": "NOT_AUTHORITY_ELIGIBLE",
            "environment": "SYNTHETIC_TEST",
            "authority_eligible": False,
        },
    )
    a.put(
        "intersection",
        "SyntheticAuthorityIntersectionAssessmentV0_1R9",
        intersection,
        intersection["assessment_ref"],
    )

    currentness_observations = [
        *foundational_currentness.values(),
        *receipt_currentness.values(),
        pbl_currentness,
        policy_currentness,
        *narrowing_currentness.values(),
    ]
    missing_currentness_roles = sorted(
        [*missing_scope_roles, "JENN_EXACT_DECISION"],
        key=lambda value: value.encode("utf-8"),
    )
    currentness_snapshot = make_currentness_snapshot(
        currentness_observations,
        missing_currentness_roles,
        [
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
        ],
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
    )
    a.put(
        "currentness-snapshot",
        "FinalAdmissionCurrentnessSnapshotV0_1R9",
        currentness_snapshot,
        currentness_snapshot["snapshot_ref"],
    )

    trace_fp = digest(
        [
            SYNTHETIC_WITNESS_DOMAIN,
            "reducer-trace",
            [observation["canonical_fingerprint"] for observation in foundational_currentness.values()],
            [receipt["canonical_fingerprint"] for receipt in receipts.values()],
            [observation["canonical_fingerprint"] for observation in receipt_currentness.values()],
            [receipt["canonical_fingerprint"] for receipt in narrowing_receipts.values()],
            [observation["canonical_fingerprint"] for observation in narrowing_currentness.values()],
            intersection["canonical_fingerprint"],
            currentness_snapshot["canonical_fingerprint"],
            pbl["canonical_fingerprint"],
            pbl_currentness["canonical_fingerprint"],
            policy["canonical_fingerprint"],
            policy_currentness["canonical_fingerprint"],
            prospective["canonical_fingerprint"],
            "NOT_AUTHORITY_ELIGIBLE",
        ]
    )
    witness = stamp(
        "F4SyntheticHandoffConstructibilityWitnessV0_1R9",
        {
            "interface_version": "agents-os.f4-synthetic-handoff-constructibility-witness.v0.1-r9",
            "witness_ref": f"{SYNTHETIC_NAMESPACE}:witness:m0-a",
            "witness_namespace": SYNTHETIC_NAMESPACE,
            "environment": "SYNTHETIC_TEST",
            "fingerprint_domain": SYNTHETIC_WITNESS_DOMAIN,
            "prospective_f3_requirement_ref": prospective["requirement_ref"],
            "prospective_f3_requirement_fingerprint": prospective["canonical_fingerprint"],
            "hypothetical_effect_atom_ref": atom["atom_ref"],
            "hypothetical_effect_atom_fingerprint": atom["canonical_fingerprint"],
            "intersection_assessment_ref": intersection["assessment_ref"],
            "intersection_assessment_fingerprint": intersection["canonical_fingerprint"],
            "currentness_snapshot_ref": currentness_snapshot["snapshot_ref"],
            "currentness_snapshot_fingerprint": currentness_snapshot["canonical_fingerprint"],
            "reducer_trace_fingerprint": trace_fp,
            "claim_state": "FIXTURE_ONLY",
            "authority_eligible": False,
            "runtime_consumable": False,
            "recovery_importable": False,
            "physical_effect_boundary": "NOT_EXECUTABLE",
            "terminal_outcome": "NOT_EXECUTED",
            "external_effect_count": 0,
            "provider_call_count": 0,
            "raw_secret_count": 0,
        },
    )
    a.put("witness", "F4SyntheticHandoffConstructibilityWitnessV0_1R9", witness, witness["witness_ref"])

    finalize(a)
    return a.root


def walk_dicts(value: Any, pointer: str = "") -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        yield pointer, value
        for key, child in value.items():
            yield from walk_dicts(child, pointer + "/" + key.replace("~", "~0").replace("/", "~1"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk_dicts(child, pointer + f"/{index}")


def classify(obj: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    candidates: list[tuple[str, dict[str, Any]]] = []
    for name, profile in ALL_SCHEMAS.items():
        if tuple(obj) != tuple(profile["fields"]):
            continue
        interface = profile["interface_version"]
        if interface is not None and obj.get("interface_version") != interface:
            continue
        candidates.append((name, profile))
    if len(candidates) != 1:
        raise ValueError(f"classification failed: keys={tuple(obj)!r}, candidates={[name for name, _ in candidates]!r}")
    return candidates[0]


def finalize(a: Assembler) -> None:
    bindings: list[dict[str, Any]] = []
    for symbol_ref, (pointer, schema, obj) in sorted(a.symbols.items(), key=lambda item: item[0].encode("utf-8")):
        bindings.append(
            stamp(
                "CanonicalSymbolBindingV0_1R9",
                {
                    "interface_version": "agents-os.canonical-symbol-binding.v0.1-r9",
                    "symbol_ref": symbol_ref,
                    "target_exact_schema_name": schema,
                    "target_fingerprint": obj["canonical_fingerprint"],
                    "target_inventory_pointer": pointer,
                },
            )
        )
    symbol_table = stamp(
        "CrossObjectSymbolTableV0_1R9",
        {
            "interface_version": "agents-os.cross-object-symbol-table.v0.1-r9",
            "bindings": bindings,
            "binding_set_fingerprint": digest(
                [SYNTHETIC_WITNESS_DOMAIN, "symbol-set", [item["canonical_fingerprint"] for item in bindings]]
            ),
        },
    )
    a.root["canonical_symbol_table"] = symbol_table

    key_ordinals = {
        entry["object_key"]: index for index, entry in enumerate(a.root["object_store"], 1)
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
            "prospective-f3",
            "atom",
            "scope",
            "currentness-operation_registry",
            "currentness-resource_kind_registry",
            "currentness-effect_constraint",
            "receipt-f1_task_scope",
            "receipt-f2_actor_binding",
            "receipt-f2_responsibility",
            "currentness-f1_task_scope",
            "currentness-f2_actor_binding",
            "currentness-f2_responsibility",
            "intersection",
            "pbl",
            "currentness-pbl",
            "policy",
            "currentness-policy",
            "narrowing-host_capability_resource_scope",
            "currentness-narrowing-host_capability_resource_scope",
            "narrowing-policy_scope",
            "currentness-narrowing-policy_scope",
            "currentness-snapshot",
        ],
    }
    nodes: list[dict[str, Any]] = []
    node_fps: list[str] = []
    for ordinal, entry in enumerate(a.root["object_store"], 1):
        deps = sorted(key_ordinals[key] for key in dependency_keys.get(entry["object_key"], []))
        dep_fps = [node_fps[index - 1] for index in deps]
        pointer = f"/object_store/{ordinal - 1}/object"
        node_fp = digest(
            [
                SYNTHETIC_WITNESS_DOMAIN,
                "evidence-node",
                ordinal,
                entry["exact_schema_name"],
                pointer,
                entry["object"]["canonical_fingerprint"],
                dep_fps,
            ]
        )
        nodes.append(
            {
                "ordinal": ordinal,
                "kind": entry["exact_schema_name"],
                "object_pointer": pointer,
                "object_fingerprint": entry["object"]["canonical_fingerprint"],
                "depends_on_ordinals": deps,
                "node_fingerprint": node_fp,
            }
        )
        node_fps.append(node_fp)
    a.root["nodes"] = nodes

    discovered: list[tuple[str, str, dict[str, Any]]] = []
    for pointer, obj in walk_dicts(a.root):
        if pointer.startswith("/schema_inventory"):
            continue
        name, profile = classify(obj)
        discovered.append((pointer, name, profile))
    a.root["schema_inventory"] = [
        {
            "json_pointer": pointer or "/",
            "exact_schema_name": name,
            "interface_version": profile["interface_version"],
            "fingerprint_field": profile["fingerprint_field"],
            "ordered_field_names": profile["fields"],
            "registry_kind": profile["registry_kind"],
        }
        for pointer, name, profile in discovered
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    rendered = json.dumps(build_fixture(), ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
