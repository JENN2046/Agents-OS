# AGENTS OS Phase 5B M0-B PR #26 Review Fixes v0.1

Date: 2026-07-22
Lane: Yellow bounded PR feedback repair
Result: PASS_FOR_CURRENT_HEAD_REREVIEW
Owner: Jenn
Agent steward: Nobao

## Result

Both Codex Review P1 threads on reviewed head
`3ffecfc9a9090ddbc593aa22364c7ef1e4c255c3` were reproduced and repaired inside
the frozen F3/Home Intent replay and currentness boundary.

```yaml
PR_number: 26
review_thread_count: 2
review_threads:
  - PRRT_kwDOSxA_XM6SriZx
  - PRRT_kwDOSxA_XM6SriZ5
source_fix_commit: 8e479e58115d5faac0789c77f58e6fadffc7c63a
package_reseal_commit: c4717fd5a5092008bd6d143b434fee62de25bb37
content_tree_sha256: 88e93001ffaa1d375a76ae264aff2a8bf41f532a9c359baaf6fba99b3c4958a6
package_manifest_sha256: 232dc2a25712ee1dc8004d7f2eb319be254298937c780f5b88bb52456ff87a0a
exact_replay_before_mutable_currentness_recheck: true
watermark_semantics: current_event_sequence_GTE_minimum_trusted_event_sequence
new_regression_tests: 2/2_PASS
cargo_check: PASS
cargo_test: 76/76_PASS
synthetic_m0b_tests: 29/29_PASS
crash_matrix_tests: 6/6_PASS
integrated_witness_root: 81bb0e8a7bc3e389b8220efef5def05a2d891e44b3fe2a1515ffbc0e56324a80
public_NAPI_methods: 5/5_UNCHANGED
dependency_changes: 0
VCPToolBox_core_changes: 0
real_occurrence_count: 0
active_queue_parser: PASS_EXACTLY_ONE_NOW
document_registry: 1329/1329_PASS
federated_registry: 3/3_PASS
machine_tests: 16/16_PASS
dashboard_tests: 17/17_PASS
control_chain_tests: 30/30_PASS
workbench_fast_tests: 10/10_PASS
consumer_default_equals_explicit_v13_1: 4/4_PASS
active_work_queue: control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v13.1.md
active_work_queue_sha256: 377041ec94a7817891f6af56cdb4b2827e1b3b59b849279b29a09e1baff7d7a3
```

The first fix returns the immutable stored first response for an exact replay
before re-evaluating later mutable candidate currentness. The second keeps the
current candidate revision/ref/fingerprint exact while treating the trusted
Event sequence as the lower bound defined by the frozen handoff contract.

No public interface, permission, identity, database schema, dependency,
VCPToolBox, runtime, provider, Memory, sensing or effect boundary changed.
