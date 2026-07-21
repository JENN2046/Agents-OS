# AGENTS OS Phase 5B M0-B WP0 Extension Skeleton Closeout v0.1

Date: 2026-07-21
Lane: Yellow bounded implementation batch
Result: PASS
Owner: Jenn
Agent steward: Nobao

## Scope

WP0 created the fixed Phase 5B Home module and test layout and declared the
future schema v2 migration surface without activating it. It preserved every
Phase 5A behavior, lockfile, direct dependency and public N-API method.

No WP1 Session reducer, candidate transition, F8 handoff composition, new
Command type or schema migration was implemented. No VCPToolBox file, active
runtime, production database, real Session content, private Memory, provider,
sensing or effect was accessed or changed.

## Bound commits and digests

```yaml
implementation_branch: agent/phase-5b-m0b-implementation
implementation_start_closeout_commit: f47cdcc452975011236e13336ad40d5b621eeb32
source_payload_commit: a5a4503d2da59d092c1b1d0be0231ba2c2a739a1
package_manifest_commit: 6a3b242f63c0fcab909f0b14c2225a7c9261da34
source_root: extensions/agents-os-resident
package_inventory: 46/46_MATCH
content_tree_sha256: 4a07003c50939d60809fd5418df4142d648a4e3743a4d3039dd235d396184268
package_manifest_sha256: 54abc1756b9870eeea8b3f2bca8657914d6ff2563c266dcb9804a11626c8bf9c
blocked_plugin_manifest_sha256: 25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0
direct_entrypoint_sha256: 51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec
active_work_queue:
  path: control-plane/registry/reports/2026-07-21-agents-os-active-work-queue-v12.2.md
  sha256: 523a7337ca9c67f81b10bb2ff407c1be101e93942f887168491ec9bfc393f87c
```

`package-manifest.json` remains canonical JSON without a trailing newline. It
is excluded from the 45-leaf content-tree digest and separately binds the
source payload commit.

## WP0 changes

```yaml
created:
  - extensions/agents-os-resident/src/home/mod.rs
  - extensions/agents-os-resident/src/home/session_boundary.rs
  - extensions/agents-os-resident/src/home/candidate.rs
  - extensions/agents-os-resident/src/home/handoff.rs
  - extensions/agents-os-resident/tests/synthetic_m0b.rs
modified:
  - extensions/agents-os-resident/src/lib.rs
  - extensions/agents-os-resident/src/ledger/schema.rs
  - extensions/agents-os-resident/README.md
  - extensions/agents-os-resident/package-manifest.json
```

The schema v2 declaration is intentionally inert:

```yaml
active_schema_version: 1
declared_target_schema_version: 2
migration_status: WP0_DECLARED_NOT_ACTIVE
migration_SQL: null
```

## Validation

```yaml
rustc: 1.96.1
cargo: 1.96.1
cargo_check_locked_offline: PASS
cargo_metadata_locked_offline: PASS
inherited_Phase_5A_tests: 44/44_PASS
new_WP0_tests: 3/3_PASS
total_Rust_tests: 47/47_PASS
package_manifest_canonical_JSON: PASS
package_inventory: 46/46_MATCH
content_tree_hash_reproduction: PASS
Cargo_lock_unchanged: true
package_lock_unchanged: true
package_json_unchanged: true
index_js_unchanged: true
blocked_plugin_manifest_unchanged: true
public_NAPI_inventory: 5/5_UNCHANGED
forbidden_changed_paths: 0
git_diff_check: PASS
```

The fixed local 1.96.1 toolchain is minimal and has no `rustfmt` component, so
no formatter was installed. The new Rust files compile cleanly and pass the
project's locked offline test suite.

## Advancement

```yaml
WP0_status: PASS_COMPLETE
WP0_fixed_module_and_test_layout: true
WP0_inherited_locks_unchanged: true
WP0_schema_v2_migration_stub_present_and_inert: true
WP0_existing_NAPI_exports_unchanged: true
WP0_Phase_5A_behavior_preserved: true
WP1_start_condition_satisfied: true
next_work_package: WP1_SESSION_NONPROMOTION_BOUNDARY
```
