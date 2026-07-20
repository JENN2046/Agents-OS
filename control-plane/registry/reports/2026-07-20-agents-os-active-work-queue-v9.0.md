# AGENTS OS Active Work Queue v9.0

Date: 2026-07-20
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-20-agents-os-active-work-queue-v8.9.md`

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
WP2_status: PASS_COMPLETE
WP2_source_commit: a1824a8863dc11d7bb3067e94fdd9703d3cf5c5e
WP2_package_manifest_commit: bd35e517c424d66aedfd41b9151b8696ee9483f1
WP2_content_tree_sha256: cc6af0a1ba38ce501de4ff6c3d5b2b7788b186a9dd81060c9e963d149d5bf658
WP2_package_manifest_sha256: 38f7ec261b7b5e0911742d41717fe24b47165bf7747c66d43c53ea57cf1cb4a3
WP2_closeout_receipt_sha256: 698601ac5ab17225fb90e804774b7c274727e5951012bea1a9035060efc84cf2
current_work_package: WP3_LEDGER_V1
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

### NOW-001: Phase 5A M0-A WP3 Ledger v1

Implement only the frozen exhaustive ledger v1 persistence boundary under
`extensions/agents-os-resident/src/ledger/`: schema metadata, the exact 18
tables, immutable history enforcement, current pointers, Event, Inbox, replay
index and transaction/CAS primitives owned by the single WP2 ledger thread and
connection.

All database activity must use a per-test temporary synthetic directory. WP3
may implement storage and transaction integrity only; the N-API Command
boundary, reducer admission, mock Host dispatch and runtime plugin activation
remain out of scope.

## NEXT

```text
WP3_transaction_and_integrity_tests_PASS=advance_to_WP4_COMMAND_BOUNDARY
WP3_failure=repair_inside_frozen_WP3_scope
scope_expansion=stop_for_new_Jenn_decision
```

## BLOCKED

```text
WP4_before_WP3_PASS=forbidden
NAPI_or_Command_admission_in_WP3=forbidden
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
WP2_RESIDENT_OWNERSHIP=PASS_COMPLETE
active_work_queue_v8_9=superseded_historical_bytes_preserved
```

This queue authorizes only sequential local implementation inside the frozen
M0-A scope. It does not authorize implementation delivery, runtime activation
or any real effect.
