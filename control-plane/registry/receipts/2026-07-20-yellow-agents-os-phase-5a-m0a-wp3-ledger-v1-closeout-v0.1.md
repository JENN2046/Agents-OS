# AGENTS OS Phase 5A M0-A WP3 Ledger v1 Closeout v0.1

Date: 2026-07-20
Lane: Yellow bounded implementation batch
Result: PASS
Owner: Jenn
Agent steward: Nobao

## Scope

WP3 implemented only the frozen ledger v1 persistence boundary under
`extensions/agents-os-resident/`:

```text
exact 18-table SQLite STRICT inventory
schema_metadata plus compiled sqlite_schema fingerprint seal
the exact two R6 canonical_fact immutable-history triggers
Event predecessor and monotonic sequence checks
canonical fact lineage and current-pointer compare-and-set
BEGIN IMMEDIATE atomic fact/pointer/Event transaction
crash injection after pointer CAS and before Event
Inbox exact request identity and replay observation
all authoritative operations on the one WP2 Rust ledger thread and connection
```

All database files were created under per-test temporary synthetic directories
and removed by test cleanup. WP3 did not implement a N-API method, admit a
Command, run a reducer, materialize or enable a plugin, or access a real runtime.

## Bound implementation

```yaml
WP3_source_commit: dbccc5147b6ac3bd89da0e6b8c540270d9fa886e
WP3_package_manifest_commit: 79e0ac1105fb37ed8ba196a7f4c488e079f101e9
WP3_source_commit_bound_by_manifest: dbccc5147b6ac3bd89da0e6b8c540270d9fa886e
WP3_source_commit_payload: 40/40_BYTE_EQUAL
WP3_content_tree_sha256: 17897f62dc884896f490dea9b13840785013fa208d0fd0eade50a1c678507d6a
WP3_package_manifest_sha256: 9440959c28091eec7544d2701bd07ef7ae8be72a076280dd5ad07096826a3d7f
WP3_planned_source_inventory: 41/41_MATCH
SQLite_schema_version: 1
SQLite_schema_fingerprint: 0c5a61574a891c7cee0559f18c4bc45f70c6f24a91b65e0b826c9fd15e779f48
SQLite_table_inventory: 18/18_MATCH
SQLite_trigger_inventory: 2/2_MATCH
```

The manifest-binding commit `4f2909b8b73e763ef992535f0106669611692a5c`
temporarily retained a trailing LF. No history rewrite was performed; the
follow-up manifest commit above removed that byte and is the sole current WP3
manifest binding.

## Validation

```yaml
rust_toolchain: 1.96.1
rustfmt_check: PASS
cargo_test_locked:
  result: PASS
  full_unit_tests: 17/17
  WP3_tests: 5/5
clippy_all_targets_locked_D_warnings: PASS
cargo_release_build_locked: PASS
schema_empty_to_v1: PASS
schema_idempotent_reopen_verification: PASS
schema_unversioned_nonempty_database: REJECTED
schema_post_initialization_inventory_drift: REJECTED
canonical_fact_update: REJECTED_AS_IMMUTABLE
canonical_fact_delete: REJECTED_AS_IMMUTABLE
request_exact_retry: RESOLVED_WITHOUT_NEW_INBOX_ROW
request_identity_substitution: REJECTED_BEFORE_WRITE
pointer_stale_CAS: REJECTED_AND_ROLLED_BACK
crash_after_pointer_CAS_before_Event: ZERO_PARTIAL_ROWS
Event_fact_pointer_committed_counts: 2_2_1
authoritative_SQLite_connections: 1
attached_databases: 1
Rust_ledger_writers: 1
temporary_target_directory_committed: false
SQLite_database_committed: false
native_binary_committed: false
```

## Boundary review

```yaml
NAPI_method_added_or_executed: false
Command_admitted: false
reducer_implemented_or_executed: false
VCPToolBox_core_changed_or_started: false
plugin_materialized_or_enabled: false
runtime_activated: false
production_authentication_used: false
private_Memory_read: false
provider_or_sensing_used: false
real_effect_occurrence_count: 0
implementation_push_PR_merge_performed: false
```

## Advancement

```yaml
WP3_status: PASS_COMPLETE
WP3_transaction_and_integrity_tests_PASS: true
WP4_start_condition_satisfied: true
next_work_package: WP4_COMMAND_BOUNDARY
```

WP4 remains limited to the frozen five-method N-API Command boundary,
synthetic principal verification, registry and intake dispositions, and its
Node ABI / illegal-input / replay exit tests. WP5 and later work packages
remain blocked by their direct predecessor gates.
