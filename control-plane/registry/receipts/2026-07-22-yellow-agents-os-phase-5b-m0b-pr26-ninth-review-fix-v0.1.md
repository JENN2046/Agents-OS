# AGENTS OS Phase 5B M0-B PR #26 Ninth Review Fix v0.1

Date: 2026-07-22
Lane: Yellow bounded PR feedback repair
Result: PASS_FOR_CURRENT_HEAD_REREVIEW
Owner: Jenn
Agent steward: Nobao

## Result

The Codex review of `a5289423765ea68630452a206668505e742ad874`
found one in-scope P2 defect. Handoff exact replay matched immutable bytes but
did not include the caller-supplied `intent_candidate_id` in its lookup.

The replay lookup now binds handoff ID, revision and intent candidate identity
before returning `ExactReplay`. A byte-identical retry with the wrong intent ID
fails without adding any ledger row, while valid delayed replay remains stable.

```yaml
PR_number: 26
review_thread: PRRT_kwDOSxA_XM6SuJLG
reviewed_head: a5289423765ea68630452a206668505e742ad874
source_fix_commit: e7268b156d73b57323ef612032e4fd18b36bead9
package_reseal_commit: fd8d08cdd9e01c83bceffc025613558e27f96970
content_tree_sha256: d98d73848bc986fd26d4b48419a938c3eb5aa81b5c4945fb9a93a066419aafed
package_manifest_sha256: b30b455cee6313b3c4c6fa0883865ec4ea45e3854d7453cbc651e77a2e83df23
handoff_replay_intent_identity_binding: PASS
wrong_intent_identity_replay: REJECTED_ZERO_ADDITION
valid_delayed_replay: EXACT_REPLAY
cargo_check: PASS
cargo_test: 83/83_PASS
synthetic_m0b_tests: 33/33_PASS
crash_matrix_tests: 6/6_PASS
integrated_witness_root: 81bb0e8a7bc3e389b8220efef5def05a2d891e44b3fe2a1515ffbc0e56324a80
public_NAPI_methods: 5/5_UNCHANGED
dependency_changes: 0
VCPToolBox_core_changes: 0
real_occurrence_count: 0
active_queue_parser: PASS_EXACTLY_ONE_NOW
document_registry: 1345/1345_PASS
federated_registry: 3/3_PASS
machine_tests: 16/16_PASS
dashboard_tests: 17/17_PASS
control_chain_tests: 30/30_PASS
workbench_fast_tests: 10/10_PASS
consumer_default_equals_explicit_v13_9: 4/4_PASS
active_work_queue: control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v13.9.md
active_work_queue_sha256: ddb09a7380664d4d9ad929c80b4f9120ec64a06d2ed646a48f0a82fba0518dde
```

No public method, permission, identity, database schema, dependency,
VCPToolBox, runtime, provider, Memory, sensing, effect or later-phase boundary
changed.
