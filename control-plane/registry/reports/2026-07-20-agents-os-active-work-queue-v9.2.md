# AGENTS OS Active Work Queue v9.2

Date: 2026-07-20
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-20-agents-os-active-work-queue-v9.1.md`

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
WP3_status: PASS_COMPLETE
WP4_status: PASS_COMPLETE
WP4_source_commit: 88334aa2573587902ef25610f7c5541d6dec02f0
WP4_package_manifest_commit: 6690b1c768c9ff59242b0e7307c7a18cdc75d623
WP4_content_tree_sha256: a4d2cc5b25d35fa24061460fb7188336511758548409997f05148531d2f29d17
WP4_package_manifest_sha256: c7f827250e17c7c81f1a88806c842f38851b50c7ddfcffc3944a4f2bb0bb734f
WP4_closeout_receipt_sha256: be420b08ec71546a540b9e8c6a3aa36402c772dbdec40d623ca7698f902b70ae
current_work_package: WP5_PERMIT_AND_OUTBOX
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

### NOW-001: Phase 5A M0-A WP5 Permit and Outbox

Implement only the frozen synthetic F4-to-F5 boundary under
`extensions/agents-os-resident/`: consume hash-bound owner-issued F4
assessments without recomputing upstream authority; validate TaskPermit,
current fences and exact effect scope; create the synthetic Outbox intent; and
implement claim, lease, recovery and exact replay state behind the sole Rust
ledger thread and SQLite connection.

All inputs remain `SYNTHETIC_TEST` and runtime-unusable. WP5 remains inside the
frozen synthetic ledger-only construction boundary. The explicit prohibitions
and later-work-package gates are recorded in `BLOCKED` below.

## NEXT

```text
WP5_permit_fence_claim_replay_and_crash_tests_PASS=advance_to_WP6_VALIDATION_AND_COMPLETION
WP5_failure=repair_inside_frozen_WP5_scope
scope_expansion=stop_for_new_Jenn_decision
```

## BLOCKED

```text
WP6_before_WP5_PASS=forbidden
upstream_F1_F2_F3_F4_authority_recomputation=forbidden
second_permission_identity_Task_or_Command_authority=forbidden
physical_or_mock_Host_dispatch_in_WP5=forbidden
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
WP3_LEDGER_V1=PASS_COMPLETE
WP4_COMMAND_BOUNDARY=PASS_COMPLETE
active_work_queue_v9_1=superseded_historical_bytes_preserved
```

This queue authorizes only sequential local implementation inside the frozen
M0-A scope. It does not authorize implementation delivery, runtime activation,
mock or real effect execution, or any provider interaction.
