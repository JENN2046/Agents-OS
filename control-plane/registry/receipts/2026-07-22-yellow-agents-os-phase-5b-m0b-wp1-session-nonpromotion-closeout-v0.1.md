# AGENTS OS Phase 5B M0-B WP1 Session Nonpromotion Closeout v0.1

Date: 2026-07-22
Lane: Yellow bounded implementation batch
Result: PASS
Owner: Jenn
Agent steward: Nobao

## Scope

WP1 implemented strict canonical decoding for the frozen 12-field synthetic
Session observation envelope and the three nonpromotion paths
`EPHEMERAL_ONLY`, `DISCARD` and `REMAIN_IN_SESSION`.

Every favorable WP1 result is deterministic, runtime-unusable and reports zero
candidate, Event, pointer, Inbox, Outbox, Goal and Task writes. Missing and
unknown branch choices return zero-write `INDETERMINATE`. The fourth closed
choice, `PROPOSE_LIFE_STREAM_CANDIDATE`, is decoded but cannot be reduced by
WP1; its implementation remains owned by WP2.

No ledger API, schema migration, handoff, F3 Command seam, JavaScript, N-API,
VCPToolBox file, active runtime, production database, real Session content,
private Memory, provider, sensing or effect was accessed or changed.

## Bound commits and digests

```yaml
implementation_branch: agent/phase-5b-m0b-implementation
source_payload_commit: f34534f8b1ff1f1bba2caacb5dd54dee9aeeec80
initial_manifest_commit_with_bad_expanded_source_id: acf22ad481f52bb8bd7beb35da1ba2dd93f80eb8
package_manifest_correction_commit: 7398618584ea9dbc0c89d693ac1385d538d21721
source_root: extensions/agents-os-resident
package_inventory: 46/46_MATCH
content_tree_leaf_count: 45
content_tree_sha256: 198839c14e67ac5beb4ffff6f034730e8f1c405209b7928904d3ebbee2a2c202
package_manifest_sha256: 86ae0d3b13ee74e08977d2a1da8b0e3310b27263fc2c32cb143885fe4c70631f
blocked_plugin_manifest_sha256: 25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0
direct_entrypoint_sha256: 51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec
active_work_queue:
  path: control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v12.3.md
  sha256: ce313a269f53cc203dd0057360a8e3564c710e6541ab27dd6de04529699d9d02
```

The package manifest remains canonical one-line JSON without a trailing
newline. It excludes itself from the 45-leaf content-tree digest and separately
binds the exact source payload commit. The first manifest commit used an
incorrect expanded source ID; it was not rewritten. The following narrow
correction commit binds the real source commit and is the only accepted WP1
manifest state.

## WP1 changes

```yaml
modified:
  - extensions/agents-os-resident/src/home/session_boundary.rs
  - extensions/agents-os-resident/src/home/mod.rs
  - extensions/agents-os-resident/tests/synthetic_m0b.rs
  - extensions/agents-os-resident/README.md
  - extensions/agents-os-resident/package-manifest.json
unchanged_boundaries:
  active_schema_version: 1
  public_NAPI_methods: 5/5
  direct_dependencies: unchanged
  Cargo_lock: unchanged
  package_lock: unchanged
  candidate_module_status: WP0_LAYOUT_ONLY
  handoff_module_status: WP0_LAYOUT_ONLY
```

## Validation

```yaml
rustc: 1.96.1
cargo: 1.96.1
cargo_check_locked_offline: PASS
cargo_test_locked_offline: 51/51_PASS
synthetic_m0b_tests: 7/7_PASS
new_WP1_test_cases: 4/4_PASS
three_no_promotion_paths: 3/3_ZERO_WRITE
missing_unknown_choice: 2/2_INDETERMINATE_ZERO_WRITE
candidate_choice_before_WP2: REJECTED_BY_WP1_AFTER_VALID_DECODE
raw_content_unknown_field_probes: REJECTED
strict_JSON_duplicate_float_unsafe_integer_bool_probes: REJECTED
noncanonical_JCS: REJECTED
production_shaped_ref: REJECTED
uppercase_hash_and_zero_revision: REJECTED
failure_payload_echo: ABSENT
package_manifest_canonical_JSON: PASS
package_inventory: 46/46_MATCH
content_tree_hash_reproduction: PASS
git_diff_check: PASS
active_queue_parser: PASS_EXACTLY_ONE_NOW
document_registry: 1312/1312_PASS
federated_registry: 3/3_PASS
machine_tests: 16/16_PASS
dashboard_tests: 17/17_PASS
control_chain_tests: 30/30_PASS
workbench_fast_tests: 10/10_PASS
consumer_default_equals_explicit_v12_3: 4/4_PASS
cargo_clippy: NOT_RUN_TOOL_UNAVAILABLE
rustfmt: NOT_RUN_TOOL_UNAVAILABLE
```

The fixed local Rust 1.96.1 toolchain does not contain `clippy` or `rustfmt`.
No component or dependency was installed. Compilation, the locked offline test
suite and manual diff review all passed.

## Advancement

```yaml
WP1_status: PASS_COMPLETE
WP1_strict_synthetic_decoder: true
WP1_nonpromotion_paths: 3/3_COMPLETE
WP1_canonical_write_count: 0
WP1_authority_created: false
WP1_runtime_usable: false
WP2_start_condition_satisfied: true
next_work_package: WP2_F7_CANDIDATE_REVISIONS
```

This receipt does not authorize a schema migration, F8 handoff, F3 Command,
VCPToolBox change or start, production database, runtime activation, provider,
private Memory, sensing or real effect.
