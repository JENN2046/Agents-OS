# AGENTS OS Phase 5B M0-B PR #26 Fifth Review Fixes v0.1

Date: 2026-07-22
Lane: Yellow bounded PR feedback repair
Result: PASS_FOR_CURRENT_HEAD_REREVIEW
Owner: Jenn
Agent steward: Nobao

## Result

The Codex review of `0b99310c4c7002cb37c3c2e97742c7e7eea1e3d2`
found two in-scope P2 defects. A schema-valid Home Intent whose exact handoff
source could not be resolved still escaped as a native error, and caller-
supplied materialized candidate history did not revalidate every positive-safe
integer and lowercase SHA-256 evidence field before pure history/handoff use.

The F3-owned ledger path now returns a typed, low-disclosure source rejection
without conflating SQLite or schema failures. Candidate history validation now
reapplies the source revision, Event sequence and evidence-commitment primitive
profiles before accepting materialized candidates.

```yaml
PR_number: 26
review_threads:
  - PRRT_kwDOSxA_XM6Ss-Tb
  - PRRT_kwDOSxA_XM6Ss-Tg
reviewed_head: 0b99310c4c7002cb37c3c2e97742c7e7eea1e3d2
source_fix_commit: 3606494b95797c232d5c033c0bbe426cfc9b2789
package_reseal_commit: 19e41db0976f5700506522659256f2412ac80dd8
content_tree_sha256: f4113388576832eefa37c43d99cdf25ae07c6fd147e7cd7c77074f08b2f3295f
package_manifest_sha256: 7c30a54f78889be8c5e3e6d4e97335d5415de32cb8e09262b6c9ac190fdbf094
unresolved_exact_source_result: INVALID_HOME_INTENT_COMMAND
unresolved_exact_source_native_exception: false
unresolved_exact_source_ledger_additions: 0
low_disclosure_source_echo: false
materialized_candidate_positive_safe_integer_profiles: PASS
materialized_candidate_lowercase_SHA256_profiles: PASS
cargo_check: PASS
cargo_test: 82/82_PASS
synthetic_m0b_tests: 32/32_PASS
crash_matrix_tests: 6/6_PASS
integrated_witness_root: 81bb0e8a7bc3e389b8220efef5def05a2d891e44b3fe2a1515ffbc0e56324a80
public_NAPI_methods: 5/5_UNCHANGED
dependency_changes: 0
VCPToolBox_core_changes: 0
real_occurrence_count: 0
active_queue_parser: PASS_EXACTLY_ONE_NOW
document_registry: 1337/1337_PASS
federated_registry: 3/3_PASS
machine_tests: 16/16_PASS
dashboard_tests: 17/17_PASS
control_chain_tests: 30/30_PASS
workbench_fast_tests: 10/10_PASS
consumer_default_equals_explicit_v13_5: 4/4_PASS
active_work_queue: control-plane/registry/reports/2026-07-22-agents-os-active-work-queue-v13.5.md
active_work_queue_sha256: 71081ef8c30a07d0ee9ce7f53af75f604cea983341d44e71a4865ae7797c7589
```

No public method, permission, identity, database schema, dependency,
VCPToolBox, runtime, provider, Memory, sensing, effect or later-phase boundary
changed.
