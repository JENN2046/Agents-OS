# Phase 5D M0-D Host-Smoke Adapter-Binding Closure R2 — Revision Totality Amendment v0.1

```yaml
contract_id: PHASE_5D_M0D_HOST_SMOKE_ADAPTER_BINDING_CLOSURE_V0_1_R2
status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
atomic: true
partial_acceptance: forbidden
scope: revision-totality-only
runtime_usable: false
actual_Host_smoke_execution_authorized: false
Host_operation_count: 0
terminal_outcome: NOT_EXECUTED
```

## 1. Immutable R1 lineage and limited replacement

R1's contract, evidence profile, fixture, validator, manifest, author review,
historical independent review, and both R1 dispositions remain immutable. This
amendment is the only R2 semantic replacement and changes only the meaning and
validation of `contract_revision` and every section `revision`.

```yaml
R1_contract_sha256: b6b64375195a0d9f88446a2e010806c3425f007647e785b6f98cd01ee74139ae
R1_profile_sha256: efcbe2afc78e29f549e692a5ae6f96dca9a0512cfd51c8fb7cfb07b85316fc05
R1_fixture_sha256: e1dd4f0812d587c7ccaa4692e69b9a0eeb1e29c17783c696ad9848165693ee1d
R1_validator_sha256: 17c17564e3b94ab7d90ff3a3b0601361948eabd45aec9cbb7b238c647f86fc98
R1_manifest_sha256: 2d18462988425344e1e642b9a47006be1ab6aea9bf103f79d3c5573f28f61499
R1_revision_totality_reproduction_sha256: 4ce823b7526ea8b72bc83402075e54759bc36715391cbe736230aa7cd1e61c54
```

All R1 clauses other than the revision-totality rule remain in force. In
particular, this amendment creates no owner-issued actual Host contract, no
complete real dependency inventory, no quarantine root, no payload, no enabled
manifest, and no Host operation.

## 2. Normative revision-totality rule

`contract_revision` and each of the eight ordered section `revision` values use
a strict JSON integer in the inclusive range `1..9007199254740991`.

For every complete synthetic owner-contract shape:

```text
positive_safe_integer(contract_revision)
AND
for every required section S:
  positive_safe_integer(S.revision)
  AND S.revision == contract_revision
```

There is no normative or validator rule that requires any revision to equal
`1`. `1` is a legal baseline value, not a fixed value.

The following are malformed and must fail closed: zero, negative integers,
integers above `9007199254740991`, floats, booleans, nulls, strings, missing
revision fields, mixed section revisions, and a contract-to-section mismatch.

## 3. Required controls

The R2 fixed fixture and validator must prove all of the following without
materializing a Host-facing object:

```yaml
positive_controls:
  - revision_1_with_all_sections_1
  - revision_2_with_all_sections_2
  - maximum_safe_integer_with_all_sections_equal
negative_controls:
  - contract_revision_differs_from_one_section
  - one_section_differs_from_the_other_sections
  - zero_negative_float_boolean_null_string_and_out_of_range_revision
```

The fixed fixture retains the R1 missing-owner fail-closed control. Every
complete synthetic positive control must still derive only:

```text
SYNTHETIC_ADAPTER_BINDING_SHAPE_VALIDATED
```

That result is non-authoritative and cannot become runtime usable, actual
Host-smoke authorization, an enabled manifest, or a Host action.

## 4. Prohibitions retained exactly

```yaml
VCPToolBox_worktree_read_write_clone_checkout_or_start: forbidden
archive_delivery_or_installation: forbidden
enabled_manifest_plugin_discovery_loading_or_Host_lifecycle: forbidden
processToolCall_native_addon_NAPI_runtime_database_dependency_install: forbidden
provider_production_authentication_private_Memory_state_private_sensing_recording_or_effect: forbidden
Git_delivery: forbidden
actual_Host_smoke_execution: forbidden
```

## 5. Acceptance boundary

R2 may only close the R1 revision-totality blocker. A successful R2 independent
review would not accept or freeze R2, and would not authorize actual Host smoke.
Those require separate current Jenn decisions.
