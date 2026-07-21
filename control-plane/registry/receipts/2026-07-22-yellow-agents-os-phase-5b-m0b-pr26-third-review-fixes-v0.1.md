# AGENTS OS Phase 5B M0-B PR #26 Third Review Fixes v0.1

Date: 2026-07-22
Lane: Yellow bounded PR feedback repair
Result: PASS_FOR_CURRENT_HEAD_REREVIEW
Owner: Jenn
Agent steward: Nobao

## Result

The Codex review of `9bd88cc6469b398ab0ae1f29529aa7412fd6f11b`
found two in-scope P2 defects. Exact retry of an immutable candidate revision
still required that revision to remain the current candidate head, while exact
retry of an immutable handoff was checked only after mutable intent-head and
history currentness. Both existing-row paths now resolve byte-identical exact
replay before mutable currentness. Same-revision rewrites remain rejected.

```yaml
PR_number: 26
review_threads:
  - PRRT_kwDOSxA_XM6SsVNl
  - PRRT_kwDOSxA_XM6SsVNp
reviewed_head: 9bd88cc6469b398ab0ae1f29529aa7412fd6f11b
source_fix_commit: eeef4846f01a69bab08aec2ff8d580d5426e5d3c
package_reseal_commit: 038b80e859edcd7fb989ba382908191fdfbf3266
content_tree_sha256: 6a69a2fbb367129073ece6f11d0a2d177b027b5a9be1d18cb2a1ed37e3c8d6ee
package_manifest_sha256: aa4107c802a2460a3d27640cbe37c670af4509354807be6cd31e854243480894
candidate_exact_replay_before_mutable_head_currentness: true
handoff_exact_replay_before_mutable_head_and_history_currentness: true
same_revision_rewrite_rejection_preserved: true
delayed_retry_regression: PASS
cargo_check: PASS
cargo_test: 79/79_PASS
synthetic_m0b_tests: 31/31_PASS
crash_matrix_tests: 6/6_PASS
integrated_witness_root: 81bb0e8a7bc3e389b8220efef5def05a2d891e44b3fe2a1515ffbc0e56324a80
public_NAPI_methods: 5/5_UNCHANGED
dependency_changes: 0
VCPToolBox_core_changes: 0
real_occurrence_count: 0
active_queue_parser: PASS_EXACTLY_ONE_NOW
document_registry: 1333/1333_PASS
federated_registry: 3/3_PASS
machine_tests: 16/16_PASS
dashboard_tests: 17/17_PASS
control_chain_tests: 30/30_PASS
workbench_fast_tests: 10/10_PASS
consumer_default_equals_explicit_v13_3: 4/4_PASS
active_work_queue: control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v13.3.md
active_work_queue_sha256: 421387f1acfd63af678e71b9a5e753e1eca5b8ef17680069cbf31a870b27d645
```

No permission, identity, public interface, database schema, dependency,
VCPToolBox, runtime, provider, Memory, sensing, effect or later-phase boundary
changed.
