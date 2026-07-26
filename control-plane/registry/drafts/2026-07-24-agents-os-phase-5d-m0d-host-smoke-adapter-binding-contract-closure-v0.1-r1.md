# Phase 5D M0-D Host-Smoke Adapter-Binding Contract Closure v0.1 R1

```yaml
schema_version: agents-os.phase5d.m0d.host-smoke-adapter-binding-closure.v0.1-r1
contract_id: PHASE_5D_M0D_HOST_SMOKE_ADAPTER_BINDING_CLOSURE_V0_1_R1
status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
owner: Jenn
agent_steward: Nobao
atomic: true
partial_acceptance: forbidden
runtime_usable: false
actual_Host_smoke_execution_authorized: false
Host_operation_count: 0
terminal_outcome: NOT_EXECUTED
```

## 1. Purpose

This closure fixes the exact **admission shape** for a future Host-smoke
execution adapter. It does not create an adapter, a worktree, a delivered
payload, an enabled manifest, a Host call, or a runtime.

The closure exists because the sealed `PluginManager.loadPlugins()` operation is
not an inert discovery probe: it can read enabled manifests and configuration,
require modules, and call `initialize()`. A future Host smoke may consume only
a separately accepted, owner-issued adapter-binding contract that makes this
whole transitive surface hermetic.

## 2. Immutable inputs already verified

```yaml
sealed_Host:
  commit: 555b3b538f6eb736e530c2912de678c5941f9985
  tree: fd82d403e79f36f749eb7f555b4736eae3eacdff
  source_preflight_sha256: 3a420c5ff995fc28839ba2340d69a23501bf9bd517d77ef552a9217cdfa14a3d
  frozen_object_tuple_count: 7
inert_payload:
  entrypoint_path: extensions/agents-os-resident/index.js
  entrypoint_sha256: 51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec
  blocked_manifest_path: extensions/agents-os-resident/plugin-manifest.json.block
  blocked_manifest_sha256: 25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0
```

These facts prove source identity only. They do not close Host dependency
resolution, plugin discovery, delivery, enablement, or lifecycle authority.

## 3. Future owner-issued adapter-binding contract

One future immutable owner-issued contract must contain the following exact
sections. Every section carries `ref`, a positive `revision`, and a lowercase
64-hex `sha256`; every reference is NFC, nonempty, and belongs to the same
contract revision. Synthetic-shape fixtures additionally require each declared
fingerprint to equal SHA-256 of its declared synthetic reference bytes; a
caller-provided independent fingerprint is not accepted.

All boolean fields in the profile and fixture use strict JSON booleans. Every
revision, byte count, ordinal, and Host-operation count uses a strict JSON
integer in its declared range. `0`, `1`, `0.0`, and `1.0` may not stand in for
boolean or integer values outside their declared type.
All mapping keys are strict JSON strings; duplicate or non-string YAML/JSON
mapping keys are malformed input and fail closed.

```yaml
required_sections_in_order:
  - hermetic_quarantine_root
  - Host_module_and_dependency_inventory
  - inert_payload
  - transient_enabled_manifest
  - host_discovery
  - initialize
  - shutdown
  - quarantine_cleanup
```

### 3.1 Hermetic quarantine root

The contract must bind a new, one-time, agent-owned root below a defined
temporary parent. It must not reuse the canonical Host worktree, a caller path,
or a pre-existing directory. It must include exact creation, ownership,
permission, and final residue-observation rules.

### 3.2 Complete Host module and dependency inventory

The contract must enumerate every source module, native module, package and
runtime dependency resolved by the selected Host adapter invocation. Each row
must include its kind, logical path or package coordinate, immutable source
identity, SHA-256, and resolution order. Unknown, wildcard, environment-derived,
or transitive-but-unlisted dependencies block the run.

The seven sealed Host rows are necessary anchors, not a complete dependency
inventory. A caller cannot assert that a list is complete; the future owner
contract must prove the closed list at its exact Host revision.

### 3.3 Only allowlisted inert payload

The future payload may contain only these two prospective files:

```text
Plugin/AGENTSOSResident/index.js
Plugin/AGENTSOSResident/plugin-manifest.json
```

`index.js` must match the frozen inert-entrypoint SHA-256. The enabled manifest
may exist only inside the future owned quarantine root and only for the bounded
run. It may never appear in the AGENTS OS workspace or the ordinary Host
worktree.

The exact UTF-8 byte payload for that prospective enabled manifest is the
already blocked manifest bytes, with only its future filename changing:

```yaml
target_relative_path: Plugin/AGENTSOSResident/plugin-manifest.json
byte_count: 413
sha256: 25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0
base64: eyJhdXRob3IiOiJKZW5uIiwiY2FwYWJpbGl0aWVzIjp7Imludm9jYXRpb25Db21tYW5kcyI6W10sInN5c3RlbVByb21wdFBsYWNlaG9sZGVycyI6W119LCJjb21tdW5pY2F0aW9uIjp7InByb3RvY29sIjoiZGlyZWN0IiwidGltZW91dCI6NjAwMDB9LCJkZXNjcmlwdGlvbiI6IlN5bnRoZXRpYy1vbmx5IGJsb2NrZWQgUGhhc2UgNUEgTTAtQSByZXNpZGVudDsgbm90IHJ1bnRpbWUgdXNhYmxlLiIsImRpc3BsYXlOYW1lIjoiQUdFTlRTIE9TIFJlc2lkZW50IChCbG9ja2VkIE0wLUEpIiwiZW50cnlQb2ludCI6eyJzY3JpcHQiOiJpbmRleC5qcyJ9LCJtYW5pZmVzdFZlcnNpb24iOiIxLjAuMCIsIm5hbWUiOiJBR0VOVFNPU1Jlc2lkZW50IiwicGx1Z2luVHlwZSI6Imh5YnJpZHNlcnZpY2UiLCJ2ZXJzaW9uIjoiMC4wLjAtbTBhIn0=
materialized_in_this_closure: false
```

The payload's exported `processToolCall()` is not admitted. Its native-addon
path remains forbidden even when the selected smoke sequence does not call it.

### 3.4 Exact lifecycle binding

The future owner contract must bind exact selector, argument bytes, return
bytes, observation source, and stop condition for each operation:

```yaml
host_discovery:
  required: exact_Host_owned_selector_and_closed_plugin_population
initialize:
  required: exact_selector_and_argument_bytes
  expected_return: {initialized: false}
shutdown:
  required: exact_selector_and_argument_bytes
  expected_return: {shutdown: true}
quarantine_cleanup:
  required: exact_finalizer_and_post_cleanup_residue_observation
```

No selector is currently admitted. In particular, the names `loadPlugins` and
`shutdownAllPlugins` are source observations, not authority to call them.

## 4. Closed current result reducer

```yaml
MISSING_owner_contract_or_any_required_section: BLOCKED_MISSING_OWNER_ISSUED_ADAPTER_BINDING
MISSING_or_unsealed_dependency_inventory: BLOCKED_HERMETIC_DEPENDENCY_INVENTORY_UNAVAILABLE
synthetic_complete_shape_only: SYNTHETIC_ADAPTER_BINDING_SHAPE_VALIDATED
all_other_inputs: BLOCKED
```

`SYNTHETIC_ADAPTER_BINDING_SHAPE_VALIDATED` has no runtime authority. It may not
be used as Host evidence, delivery approval, enablement approval, or an actual
execution decision.

## 5. Boundary and stop rule

This R1 may create only this contract, its evidence profile, synthetic fixture,
offline validator, author self-review, and hash-bound independent-review
package. It must stop at Fresh Full Atomic Independent Review.

```yaml
VCPToolBox_worktree_read_write_clone_checkout_or_start: forbidden
archive_delivery_or_installation: forbidden
enabled_manifest_plugin_discovery_loading_or_Host_lifecycle: forbidden
processToolCall_native_addon_NAPI_runtime_database_dependency_install: forbidden
provider_production_authentication_private_Memory_state_private_sensing_recording_or_effect: forbidden
actual_Host_smoke_execution: forbidden
```
