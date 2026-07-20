# AGENTS OS Active Work Queue v8.7

Date: 2026-07-20
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-20-agents-os-active-work-queue-v8.6.md`

## Current Facts

```yaml
Phase_5A_started: true
Phase_5A_mode: M0A_IMPLEMENTATION
Phase_5A_plan_status: ACCEPTED_FROZEN_DURABLE_ON_MAIN
Phase_5A_plan_acceptance_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R8_ATOMIC_BUNDLE
Phase_5A_plan_manifest_sha256: f6b00bb0a19bb464122d44839e4f8987b0a68aea0794d0a36e9e29bec1de96b3
Phase_5A_implementation_start_decision_sha256: def97074d4e87931f945701d612d4bd3da4727c5a92e842ceb8aaeffef9bf7b3
Phase_5A_implementation_started: true
implementation_authorized: true
current_work_package: WP0_REPRODUCIBLE_SKELETON
source_authority_root: extensions/agents-os-resident
dependency_installation_authorized: exact_project_local_pinned_only
temporary_synthetic_SQLite_authorized: true
clean_VCPToolBox_linked_worktree_authorized: true
blocked_plugin_materialization_authorized: true
VCPToolBox_core_change_authorized: false
VCPToolBox_start_authorized: false
plugin_enablement_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
provider_sensing_or_real_effect_authorized: false
implementation_push_PR_merge_authorized: false
```

## NOW

### NOW-001: Phase 5A M0-A WP0 Reproducible skeleton

Create the frozen external package skeleton under
`extensions/agents-os-resident/` on a dedicated local implementation branch.
WP0 is limited to deterministic package layout, exact project-local toolchain
and lock declarations, blocked install manifest, package manifest and
source/install tree fingerprint reproduction.

The existing dirty `runtime/VCPToolBox` worktree remains untouched. Any future
compatibility materialization must use a new clean linked worktree at
`555b3b538f6eb736e530c2912de678c5941f9985`, must retain
`plugin-manifest.json.block`, and must produce zero VCPToolBox core diff.

## NEXT

```text
WP0_all_frozen_exit_conditions_PASS=advance_to_WP1_CANONICAL_PRIMITIVES
WP0_failure=repair_inside_frozen_WP0_scope
scope_expansion=stop_for_new_Jenn_decision
```

## BLOCKED

```text
WP1_before_WP0_PASS=forbidden
VCPToolBox_core_change_or_existing_dirty_worktree_use=forbidden
VCPToolBox_start_or_plugin_enablement=forbidden
production_or_existing_database=forbidden
runtime_auth_private_Memory_provider_sensing_or_real_effect=forbidden
implementation_branch_push_PR_merge=forbidden
Phase_5B_release_deploy_publish=forbidden
```

## CLOSED

```text
Phase_5A_plan_R8_atomic_freeze=COMPLETE
Phase_5A_plan_Git_durability=COMPLETE
implementation_start_preflight=PASS
Jenn_implementation_start_decision=ACCEPTED
active_work_queue_v8_6=superseded_historical_bytes_preserved
```

This queue authorizes only sequential local implementation inside the frozen
M0-A scope. It does not authorize runtime activation or any real effect.
