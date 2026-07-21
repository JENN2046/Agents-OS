# AGENTS OS Active Work Queue v12.1

Date: 2026-07-21
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-21-agents-os-active-work-queue-v12.0.md`

## Current Facts

```yaml
Phase_5B_started: true
Phase_5B_mode: M0B_IMPLEMENTATION_STARTED_WP0_ACTIVE
Phase_5B_plan_status: ACCEPTED_FROZEN_DURABLE_ON_MAIN
Phase_5B_plan_acceptance_unit: PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R5_ATOMIC_BUNDLE
Phase_5B_plan_subject_count: 18
Phase_5B_plan_manifest_sha256: bfacffcb1446bc122a7f933ffbbf9ea71628f4cd044977c29fa0f98adc85b721
Phase_5B_plan_independent_review_sha256: 3ba6a750a14fe0a457414c52babdd8cf51d549d723d4420e8febf69c1cbfca7f
Phase_5B_plan_freeze_decision_sha256: a8fb172347d2291e8141a2da4369f2e861ad3566d68214f678367b9cd863951d
Phase_5B_plan_mainline_integration_commit: d494f6399337ab918cccee6183646916d594ef2a
Phase_5B_plan_durability_projection_commit: f5633b442b571d4b1bc61839b91c65e3b8319fa8
Phase_5B_plan_Git_objects_on_main: true
Phase_5B_plan_mainline_integrated: true
Phase_5B_plan_durability_complete: true
Phase_5B_plan_accepted: true
Phase_5B_plan_frozen: true
Phase_5B_plan_revisions_stopped: true
requires_R6: false
Phase_5B_implementation_started: true
implementation_authorized: true
implementation_start_decision_sha256: 75dfbea4f6543e55038533a8e63ec9889ae42284c23bd8e747cf8da7be866ea8
implementation_branch: agent/phase-5b-m0b-implementation
current_work_package: WP0_M0B_EXTENSION_SKELETON
WP0_start_authorized: true
WP1_through_WP7_started: false
VCPToolBox_change_or_start_authorized: false
plugin_enablement_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
real_Session_content_access_authorized: false
private_raw_memory_access_authorized: false
provider_sensing_or_real_effect_authorized: false
```

## NOW

### NOW-001: Implement Phase 5B M0-B WP0 extension skeleton

```text
requires_jenn_decision=false
execution_authorized=true
```

Create only the fixed Home module/test layout and schema v2 migration stub
under `extensions/agents-os-resident/`. Preserve inherited dependency locks,
the existing five-method N-API surface and every Phase 5A behavior. Do not
implement WP1 reducers or later Home semantics in WP0.

## NEXT

```text
WP0_PASS_COMPLETE=WP1_SESSION_NONPROMOTION_BOUNDARY_ELIGIBLE
WP0_FAIL=repair_inside_frozen_scope
skip_or_parallel_advancement=forbidden
```

## BLOCKED

```text
WP1_through_WP7_before_direct_predecessor_gate=forbidden
new_dependency_or_toolchain_change=forbidden
new_NAPI_method_or_JavaScript_surface=forbidden
VCPToolBox_change_start_or_plugin_enablement=forbidden
production_or_existing_database_use=forbidden
runtime_auth_provider_real_Session_private_Memory_sensing_or_real_effect=forbidden
push_PR_merge_tag_release_deploy_or_publish=forbidden
```

## CLOSED

```text
Plan_R5_independent_review=PASS_NO_BLOCKER_COMPLETE
Jenn_Plan_R5_atomic_freeze_decision=ACCEPTED_COMPLETE
Phase_5B_M0B_plan=ACCEPTED_FROZEN_DURABLE_ON_MAIN
Jenn_Phase_5B_M0B_implementation_start_decision=ACCEPTED
active_work_queue_v12_0=superseded_historical_bytes_preserved
```

This queue authorizes only WP0 local construction and deterministic offline
validation. It does not authorize VCPToolBox, plugin, runtime, authentication,
provider, Memory, sensing or real effect work.
