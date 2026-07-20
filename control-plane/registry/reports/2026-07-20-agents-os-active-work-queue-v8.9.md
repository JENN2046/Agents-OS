# AGENTS OS Active Work Queue v8.9

Date: 2026-07-20
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-20-agents-os-active-work-queue-v8.8.md`

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
implementation_branch: agent/phase-5a-m0a-wp0
WP0_status: PASS_COMPLETE
WP1_status: PASS_COMPLETE
WP1_source_commit: b5abb6af8d038b46d2380c9340f2033945054feb
WP1_content_tree_sha256: f5e1e90e0f2deb9ed11442421fa28871832f700ac8937f9fb57c9f30282af971
WP1_package_manifest_sha256: ce63edf10a02106fb48886ef9db31da552a3939d67fea431757abd6b5910a087
WP1_closeout_receipt_sha256: 09d989b456eca841717f6a764c26f3b40438d767aca9f6ec4f7e9ab88105a301
current_work_package: WP2_RESIDENT_OWNERSHIP
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

### NOW-001: Phase 5A M0-A WP2 Resident ownership

Implement only the frozen Resident ownership boundary under
`extensions/agents-os-resident/src/resident/`: one OS-exclusive lock, stable
synthetic Resident identity, immutable incarnation and contiguous authority
epoch ownership, one Rust ledger thread, one authoritative SQLite connection
and deterministic cleanup/join behavior.

All database activity must use a per-test temporary synthetic directory. WP2
may establish ownership and connection lifecycle only; the closed ledger v1
schema, reducers, Command admission and runtime plugin activation remain out of
scope.

## NEXT

```text
WP2_dual_start_and_wrong_thread_tests_PASS=advance_to_WP3_LEDGER_V1
WP2_failure=repair_inside_frozen_WP2_scope
scope_expansion=stop_for_new_Jenn_decision
```

## BLOCKED

```text
WP3_before_WP2_PASS=forbidden
ledger_v1_schema_or_reducer_implementation_in_WP2=forbidden
second_SQLite_connection_or_writer=forbidden
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
WP0_REPRODUCIBLE_SKELETON=PASS_COMPLETE
WP1_CANONICAL_PRIMITIVES=PASS_COMPLETE
active_work_queue_v8_8=superseded_historical_bytes_preserved
```

This queue authorizes only sequential local implementation inside the frozen
M0-A scope. It does not authorize implementation delivery, runtime activation
or any real effect.
