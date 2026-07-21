# AGENTS OS Phase 5B M0-B WP5 F3 Synthetic Intake Closeout v0.1

Date: 2026-07-22
Lane: Yellow bounded implementation batch
Result: PASS
Owner: Jenn
Agent steward: Nobao

## Result

WP5 adds the exact implementation-only `M0_SYNTHETIC_SUBMIT_HOME_INTENT`
definition and adapts the fixed WP4 candidate through the existing
`execute_command` frame. F3 alone authenticates, writes and replays the
Command; Home has no ledger writer.

```yaml
source_payload_commit: 42442c556cb8c1df26cb74b1c647ed8251a22dcb
package_manifest_commit: 5e784c649f293f575911671fb6187e8479f1ae6a
content_tree_sha256: d3c7bc8292e80a151cb1f0203e5c702b78ff52222c46fcfed1cdfd74ac6e1820
package_manifest_sha256: 8316ee36a91471a5d2d4150535288e38ac1057e9a4a529c511abef7be50021ea
cargo_check_locked_offline: PASS
cargo_test_locked_offline: 68/68_PASS
synthetic_m0b_tests: 24/24_PASS
new_WP5_test_cases: 3/3_PASS
F3_terminal_outcomes: COMMITTED_REJECTED_INDETERMINATE
exact_replay: PASS_ZERO_ADDITION
invalid_input: REJECTED_ZERO_WRITE
Home_direct_Command_write: false
external_call_count: 0
runtime_usable: false
active_schema_version: 1
public_NAPI_methods: 5/5_UNCHANGED
active_work_queue: control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v12.7.md
active_work_queue_sha256: 852e4161d05b2b88a85d2b47ae3f3573207ac1c0a930e9654c2bbd0e2dd99538
active_queue_parser: PASS_EXACTLY_ONE_NOW
document_registry: 1321/1321_PASS
federated_registry: 3/3_PASS
machine_tests: 16/16_PASS
dashboard_tests: 17/17_PASS
control_chain_tests: 30/30_PASS
workbench_fast_tests: 10/10_PASS
consumer_default_equals_explicit_v12_7: 4/4_PASS
governance_validation: PASS
```

The fixed M0-A integrated root remains unchanged. No VCPToolBox, runtime,
production database, private Memory, real Session, provider, sensing or real
effect was used. WP6 is the next direct package.
