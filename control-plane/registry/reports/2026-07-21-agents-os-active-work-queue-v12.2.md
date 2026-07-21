# AGENTS OS Active Work Queue v12.2

Date: 2026-07-21
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-21-agents-os-active-work-queue-v12.1.md`

## Current Facts

```yaml
Phase_5B_started: true
Phase_5B_mode: M0B_IMPLEMENTATION_WP0_COMPLETE_WP1_ELIGIBLE
Phase_5B_plan_status: ACCEPTED_FROZEN_DURABLE_ON_MAIN
Phase_5B_plan_acceptance_unit: PHASE_5B_M0B_PLAN_BUILD_PROFILE_V0_1_R5_ATOMIC_BUNDLE
Phase_5B_plan_manifest_sha256: bfacffcb1446bc122a7f933ffbbf9ea71628f4cd044977c29fa0f98adc85b721
Phase_5B_implementation_start_decision_sha256: 75dfbea4f6543e55038533a8e63ec9889ae42284c23bd8e747cf8da7be866ea8
Phase_5B_implementation_started: true
implementation_authorized: true
implementation_branch: agent/phase-5b-m0b-implementation
WP0_status: PASS_COMPLETE
WP0_source_commit: a5a4503d2da59d092c1b1d0be0231ba2c2a739a1
WP0_package_manifest_commit: 6a3b242f63c0fcab909f0b14c2225a7c9261da34
WP0_content_tree_sha256: 4a07003c50939d60809fd5418df4142d648a4e3743a4d3039dd235d396184268
WP0_package_manifest_sha256: 54abc1756b9870eeea8b3f2bca8657914d6ff2563c266dcb9804a11626c8bf9c
WP0_fixed_module_layout: PASS
WP0_inherited_locks_unchanged: true
WP0_schema_v2_stub_inert: true
WP0_five_method_NAPI_surface_unchanged: true
WP0_Phase_5A_tests: 44/44_PASS
WP0_M0B_tests: 3/3_PASS
current_work_package: WP1_SESSION_NONPROMOTION_BOUNDARY
WP1_start_condition_satisfied: true
WP1_started: false
WP2_through_WP7_started: false
VCPToolBox_change_or_start_authorized: false
runtime_activation_authorized: false
production_or_existing_database_authorized: false
real_Session_private_Memory_provider_sensing_or_effect_authorized: false
```

## NOW

### NOW-001: Begin WP1 synthetic observation nonpromotion boundary

```text
requires_jenn_decision=false
execution_authorized=true
```

WP1 may implement only closed synthetic observation decoding and the
`EPHEMERAL_ONLY`, `DISCARD` and `REMAIN_IN_SESSION` nonpromotion reducers. All
three outcomes must write zero canonical candidate, Event, pointer, Inbox or
Outbox rows, and raw-content-shaped input must fail closed.

## NEXT

```text
WP1_PASS_COMPLETE=WP2_F7_CANDIDATE_REVISIONS_ELIGIBLE
WP1_FAIL=repair_inside_frozen_scope
skip_or_parallel_advancement=forbidden
```

## BLOCKED

```text
WP2_through_WP7_before_direct_predecessor_gate=forbidden
real_Session_content_or_private_Memory=forbidden
canonical_write_from_nonpromotion_branch=forbidden
new_dependency_NAPI_method_or_JavaScript_surface=forbidden
VCPToolBox_change_start_or_plugin_enablement=forbidden
production_or_existing_database_use=forbidden
runtime_auth_provider_sensing_or_real_effect=forbidden
push_PR_merge_tag_release_deploy_or_publish=forbidden
```

## CLOSED

```text
Phase_5B_M0B_plan=ACCEPTED_FROZEN_DURABLE_ON_MAIN
Jenn_Phase_5B_M0B_implementation_start_decision=ACCEPTED
WP0_M0B_EXTENSION_SKELETON=PASS_COMPLETE
active_work_queue_v12_1=superseded_historical_bytes_preserved
```

This queue keeps the implementation synthetic-only and runtime-unusable.
