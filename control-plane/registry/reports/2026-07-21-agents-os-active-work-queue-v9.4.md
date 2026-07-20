# AGENTS OS Active Work Queue v9.4

Date: 2026-07-21
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-20-agents-os-active-work-queue-v9.3.md`

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
WP5_status: PASS_COMPLETE
WP6_status: PASS_COMPLETE
WP6_source_commit: ee529abfaeff34a84196f5e493655f45c216cfd5
WP6_package_manifest_commit: 6851df482be825d195de6036016f0a77e59e78a9
WP6_content_tree_sha256: 62e2c6035eac3bfed14d09ec89360e999cc66e6dbcef2f5a1df8a7ed835aedc8
WP6_package_manifest_sha256: 2326bd3cccdf0b4d94a2f67881840ab25fff9cb0c281851b276b3ea6922c23b1
WP6_closeout_receipt_sha256: 7f52b5c2dde758d7a2038de95f4ee6d8cdb0e9d70c268e86dcc3791e14ccbe65
current_work_package: WP7_INTEGRATED_M0A_WITNESS
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

### NOW-001: Phase 5A M0-A WP7 Integrated M0-A Witness

Build only the frozen integrated `SYNTHETIC_TEST` witness under
`extensions/agents-os-resident/`: run the closed synthetic Command sequence for
three synthetic Tasks, bind deterministic Event and root hashes, restart the
single Resident/ledger boundary, and prove exact replay plus byte-identical
clean runs with zero real occurrences.

WP7 may integrate only the already completed WP0-WP6 implementation surfaces.
It must not add a new authority, database schema, N-API method, provider,
runtime activation path, Host dispatch path or production-facing behavior.

## NEXT

```text
WP7_two_clean_runs_byte_identical_restart_replay_and_zero_real_occurrences_PASS=advance_to_PHASE_5A_M0A_IMPLEMENTATION_CLOSEOUT
WP7_failure=repair_inside_frozen_WP7_scope
scope_expansion=stop_for_new_Jenn_decision
```

## BLOCKED

```text
Phase_5A_implementation_closeout_before_WP7_PASS=forbidden
upstream_F1_F2_F3_F4_F5_F6_authority_recomputation=forbidden
second_permission_identity_Task_Command_validation_or_effect_authority=forbidden
physical_or_mock_Host_dispatch=forbidden
second_SQLite_connection_or_writer=forbidden
schema_or_NAPI_method_expansion=forbidden
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
WP5_PERMIT_AND_OUTBOX=PASS_COMPLETE
WP6_VALIDATION_AND_COMPLETION=PASS_COMPLETE
active_work_queue_v9_3=superseded_historical_bytes_preserved
```

This queue authorizes only sequential local implementation inside the frozen
M0-A scope. It does not authorize implementation delivery, runtime activation,
mock or real effect execution, or any provider interaction.
