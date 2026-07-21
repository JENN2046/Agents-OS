# AGENTS OS Active Work Queue v12.8

Date: 2026-07-22
Status: ACTIVE
Owner: Jenn
Agent steward: Nobao
Supersedes: `control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v12.7.md`

## Current Facts

```yaml
Phase_5B_started: true
Phase_5B_mode: M0B_IMPLEMENTATION_WP6_COMPLETE_WP7_ELIGIBLE
implementation_branch: agent/phase-5b-m0b-implementation
automatic_implementation_delivery_authorization_sha256: 4345a546bbbe78814ccc3f5bd18672ec6507d07322abbffe898ae9bd600b43db
WP0_through_WP5_status: PASS_COMPLETE
WP6_status: PASS_COMPLETE
WP6_source_commit: 11924a0f8d2721153511833c9cbcd7a0eea95501
WP6_package_manifest_commit: 6d5ee2c6dad40996ce6046e6801c5493a0ec52b4
WP6_content_tree_sha256: a132a6f6370b5875d94608f140157f902de6b338a46f28f559afb93329f016a9
WP6_package_manifest_sha256: f69aab0df51c68391abcd01c4b2ba1e4a53ee8f95cb5cae45e31af6a36d3b5c0
WP6_schema_transition: v1_TO_v2_SYNTHETIC_TEST_ONLY
WP6_total_Rust_tests: 73/73_PASS
WP6_synthetic_m0b_tests: 26/26_PASS
WP6_crash_matrix_tests: 6/6_PASS
WP6_quick_check: PASS
WP6_foreign_key_check: EMPTY
WP6_raw_content_scan: EMPTY
WP6_disposable_synthetic_database_cleaned: true
WP6_public_NAPI_methods: 5/5_UNCHANGED
current_work_package: WP7_INTEGRATED_M0B_WITNESS
WP7_start_condition_satisfied: true
WP7_started: false
VCPToolBox_change_or_start_authorized: false
runtime_activation_authorized: false
production_or_existing_database_authorized: false
real_Session_private_Memory_provider_sensing_or_effect_authorized: false
```

## NOW

### NOW-001: Build WP7 integrated M0-B witness

```text
requires_jenn_decision=false
execution_authorized=true
```

WP7 must run the complete synthetic branch tree twice on clean disposable
databases and once across restart. The canonical rows, Events and root hashes
must be deterministic; replay must add zero candidate, handoff or Command rows.

## NEXT

```text
WP7_PASS_COMPLETE=PHASE_5B_M0B_IMPLEMENTATION_CLOSEOUT_ELIGIBLE
WP7_FAIL=repair_inside_frozen_scope
skip_or_parallel_advancement=forbidden
```

## BLOCKED

```text
implementation_closeout_before_WP7_gate=forbidden
automatic_candidate_handoff_or_Command_retry=forbidden
existing_production_or_private_database_open=forbidden
new_NAPI_method_dependency_or_JavaScript_surface=forbidden
VCPToolBox_change_start_or_plugin_enablement=forbidden
runtime_auth_provider_private_Memory_sensing_or_real_effect=forbidden
release_deploy_publish_force_push_tag_history_rewrite=forbidden
```

## CLOSED

```text
Phase_5B_M0B_plan=ACCEPTED_FROZEN_DURABLE_ON_MAIN
Jenn_automatic_implementation_delivery_authorization=ACCEPTED
WP0_through_WP6=PASS_COMPLETE
active_work_queue_v12_7=superseded_historical_bytes_preserved
```

This queue keeps WP7 synthetic-only, deterministic and runtime-unusable.
