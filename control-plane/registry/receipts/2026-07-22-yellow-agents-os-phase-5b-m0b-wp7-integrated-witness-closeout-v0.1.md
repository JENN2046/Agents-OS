# AGENTS OS Phase 5B M0-B WP7 Integrated Witness Closeout v0.1

Date: 2026-07-22
Lane: Yellow bounded implementation batch
Result: PASS
Owner: Jenn
Agent steward: Nobao

## Result

WP7 binds the complete low-disclosure synthetic Home-to-F3 path into one
read-only deterministic witness. Four Session branches, three F7 candidate
classes, one F8 handoff and committed, rejected and indeterminate F3 outcomes
are exercised without any real occurrence or automatic restart promotion.

```yaml
source_payload_commit: e59d638eba11d760807351b5a11eefff711c8626
package_manifest_commit: 9b8da782ea3ea33b0099bd2da73fc8123ade745b
content_tree_sha256: 0d849f6b87c10c2d719ee60611104b798f984fb8d72c979b26642d19de5f169e
package_manifest_sha256: 24b5125957ecc6d4856565c109dc687ea1fb732e9bcaac931f3d9cff63fc9b3e
integrated_witness_root: 81bb0e8a7bc3e389b8220efef5def05a2d891e44b3fe2a1515ffbc0e56324a80
cargo_check: PASS
cargo_test: 74/74_PASS
synthetic_m0b_tests: 27/27_PASS
clean_runs: 2/2_BYTE_IDENTICAL
restart_runs: 1/1_BYTE_IDENTICAL_ZERO_ADDITION
synthetic_session_observations: 4
synthetic_candidate_classes: 3/3
synthetic_F8_handoff_count: 1
synthetic_F3_committed_count: 1
synthetic_F3_rejected_control_count: 1_ZERO_WRITE
synthetic_F3_indeterminate_count: 1_ZERO_EVENT
external_call_count: 0
real_occurrence_count: 0
runtime_usable: false
public_NAPI_methods: 5/5_UNCHANGED
active_queue_parser: PASS_EXACTLY_ONE_NOW
document_registry: 1325/1325_PASS
federated_registry: 3/3_PASS
machine_tests: 16/16_PASS
dashboard_tests: 17/17_PASS
control_chain_tests: 30/30_PASS
workbench_fast_tests: 10/10_PASS
consumer_default_equals_explicit_v12_9: 4/4_PASS
governance_validation: PASS
active_work_queue: control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v12.9.md
active_work_queue_sha256: 26328e3d47b33aad8a37c5a01fbed65f72c1ad0d56ff99a3b1a2a06a4996b789
```

The two clean databases were created in fresh `tempfile` directories and the
restart reopened only the first synthetic fixture. No existing, production or
private database, VCPToolBox source/start, plugin enablement, runtime,
provider, private Memory, real Session, sensing or real effect was used.
Implementation Closeout is the next direct package.
