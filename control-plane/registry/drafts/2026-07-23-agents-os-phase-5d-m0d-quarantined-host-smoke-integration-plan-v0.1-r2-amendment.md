# AGENTS OS Phase 5D M0-D Quarantined Host Smoke Integration Plan v0.1 R2

```yaml
schema_version: agents-os.phase5d.m0d.plan.v0.1-r2
plan_id: PHASE_5D_M0D_QUARANTINED_HOST_SMOKE_INTEGRATION_PLAN_V0_1_R2
date: '2026-07-23'
status: FIXED_FOR_FRESH_FULL_ATOMIC_INDEPENDENT_REVIEW
acceptance_unit: PHASE_5D_M0D_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE
partial_acceptance: forbidden
precedence:
  - R2_explicit_replacements
  - R1_all_other_clauses
current_boundary:
  current_plan_authoring_only: true
  Host_worktree_read_or_write: forbidden
  archive_delivery_or_installation: forbidden
  plugin_enablement_or_Host_loading: forbidden
  processToolCall_or_native_addon_load: forbidden
  native_NAPI_invocation: forbidden
  runtime_database_provider_private_Memory_sensing_or_effect: forbidden
  implementation_authorized: false
  runtime_usable: false
  terminal_outcome: NOT_EXECUTED
future_smoke_interface:
  future_lifecycle_methods_only: [initialize, shutdown]
  future_initialize_result: {initialized: false}
  future_shutdown_result: {shutdown: true}
  Host_lifecycle_argument_contract: future_hash_bound_Host_contract_required
  future_Host_discovery_or_lifecycle: separately_Jenn_authorized_only
```

## R2 purpose

R2 does not redesign the smoke. It closes exactly the R1 review findings:

1. the source payload, extension bytes, sealed Host commit/tree and seven Host
   commitment rows must resolve to fixed immutable values, not merely valid
   hexadecimal syntax;
2. the favorable offline preflight result must be bound to this exact Plan's
   present boundary and must not survive text that claims Host, plugin, native
   or runtime execution is currently authorized; and
3. the Plan/profile parser must reject duplicate YAML keys and require the
   exact R2 schema/profile identity constants.

## Current action boundary

This remains a **planning-only** correction. It does not create, inspect, clone
or start VCPToolBox. It does not deliver an archive, enable or discover a
plugin, invoke `initialize`, `shutdown`, `processToolCall` or any N-API method,
load native code, start a runtime or service, create/access a database, read
private Memory, use a provider, sense, record or cause an effect.

The favorable R2 synthetic result means only that the exact Plan/profile can be
reviewed as a future preflight candidate. It never means a Host action occurred
or is authorized. Any current claim otherwise is invalid and must produce
`BLOCKED` in the offline validator.

## R2 replacement rules

The R2 validator must consume the exact bytes of this amendment and compare its
canonical header and SHA-256 against immutable R2 constants. It must consume an
exact source/Host/extension anchor based on the already sealed Phase 5C lineage.
It must reject coherent re-signing of the R2 profile, witness, manifest or
package when those changes substitute any anchored source fact or relax this
current boundary.

R1's two subjects, manifest, author evidence, independent review, case results
and finding disposition remain immutable historical evidence. R2 adds no
permission, identity, Task, Command, Host or effect authority.

## Stop rule

R2 stops at `PHASE_5D_M0D_PLAN_R2_FRESH_FULL_ATOMIC_HASH_BOUND_INDEPENDENT_REVIEW`.
`PASS_NO_BLOCKER` would only open a separate Jenn plan-freeze decision. It does
not authorize implementation, delivery, VCPToolBox access, plugin enablement,
Host loading, native loading or runtime activation.
