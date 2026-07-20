# AGENTS OS Active Work Queue v9.1

Date: 2026-07-20
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-20-agents-os-active-work-queue-v9.0.md`

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
WP3_source_commit: dbccc5147b6ac3bd89da0e6b8c540270d9fa886e
WP3_package_manifest_commit: 79e0ac1105fb37ed8ba196a7f4c488e079f101e9
WP3_content_tree_sha256: 17897f62dc884896f490dea9b13840785013fa208d0fd0eade50a1c678507d6a
WP3_package_manifest_sha256: 9440959c28091eec7544d2701bd07ef7ae8be72a076280dd5ad07096826a3d7f
WP3_closeout_receipt_sha256: 286e6b7261458ae5804f9699e7af98f1099e280a3f6ec45973337253c4917f20
current_work_package: WP4_COMMAND_BOUNDARY
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

### NOW-001: Phase 5A M0-A WP4 Command Boundary

Implement only the frozen five-method N-API boundary under
`extensions/agents-os-resident/`: `execute_command`, `execute_query`,
`claim_outbox`, `acknowledge_outbox`, and `reconcile`; strict canonical F3
request/response frames; synthetic principal verification; closed command
registry and intake dispositions; and the inherited safe CommonJS projection.

All inputs remain synthetic and runtime-unusable. Unknown methods, versions,
schemas, fields, noncanonical JSON, caller-selected native method names, paths,
SQL, callbacks, credentials, provider handles and arbitrary JavaScript objects
must be rejected before ledger access. WP4 may not implement F4 permit
admission, Outbox dispatch, mock Host effects, F6 completion or runtime plugin
activation.

## NEXT

```text
WP4_Node_ABI_illegal_input_and_replay_tests_PASS=advance_to_WP5_PERMIT_AND_OUTBOX
WP4_failure=repair_inside_frozen_WP4_scope
scope_expansion=stop_for_new_Jenn_decision
```

## BLOCKED

```text
WP5_before_WP4_PASS=forbidden
F4_permit_or_Outbox_dispatch_in_WP4=forbidden
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
active_work_queue_v9_0=superseded_historical_bytes_preserved
```

This queue authorizes only sequential local implementation inside the frozen
M0-A scope. It does not authorize implementation delivery, runtime activation
or any real effect.
