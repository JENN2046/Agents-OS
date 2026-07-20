# AGENTS OS Active Work Queue v8.8

Date: 2026-07-20
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-20-agents-os-active-work-queue-v8.7.md`

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
WP0_source_payload_commit: 313aebfe8f12f131bb5c661dd8926df23052491f
WP0_package_manifest_commit: c93e295461a8100debbfb4042d09bc05dc2d2ae0
WP0_content_tree_sha256: a7a3145e4267064c02b3c80fd9f13b9f3eb3ba3dfaf48793dbcb89afe2124fe8
WP0_package_manifest_sha256: 4f95b1bd4056deaba15b38701f4dda7bd09f871a5b87ad050a2cfbf7a8f35327
WP0_closeout_receipt_sha256: 4fb1806d31c26aba6ef778957b88a2d3664e6631b02ab671a5442a73917f66e5
current_work_package: WP1_CANONICAL_PRIMITIVES
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

### NOW-001: Phase 5A M0-A WP1 Canonical primitives

Implement only the frozen canonical primitive layer under
`extensions/agents-os-resident/src/canonical/` and its directly owned tests:
strict UTF-8 JSON decoding, duplicate-key rejection, NFC validation, JSON safe
integers, JCS bytes and SHA-256 fingerprints.

The implementation must consume the frozen F1-F6 canonical vectors and remain
independent of SQLite, Resident lifecycle, Command admission, Host dispatch,
providers, private Memory and runtime activation.

## NEXT

```text
WP1_fixed_F1_F6_canonical_vectors_PASS=advance_to_WP2_RESIDENT_OWNERSHIP
WP1_failure=repair_inside_frozen_WP1_scope
scope_expansion=stop_for_new_Jenn_decision
```

## BLOCKED

```text
WP2_before_WP1_PASS=forbidden
SQLite_schema_or_database_creation_in_WP1=forbidden
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
active_work_queue_v8_7=superseded_historical_bytes_preserved
```

This queue authorizes only sequential local implementation inside the frozen
M0-A scope. It does not authorize implementation delivery, runtime activation
or any real effect.
