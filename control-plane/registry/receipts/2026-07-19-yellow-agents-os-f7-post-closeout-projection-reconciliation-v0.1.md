# AGENTS OS F7 Post-Closeout Projection Reconciliation Receipt v0.1

Date: 2026-07-19
Mode: Yellow Work Batch
Result: `PASS`
Owner: Jenn
Agent steward: Nobao

## Authority and evidence

Jenn explicitly accepted Active Work Queue v4.8 as the legitimate F7
post-closeout projection and superseded strict v4.7 final-tree equality with
projection-aware durability criteria.

```yaml
reconciliation_report:
  path: control-plane/registry/reports/2026-07-19-agents-os-f7-post-closeout-projection-reconciliation-v0.1.yaml
  sha256: 3053099b372dfb5d476e8089c4caa7e6de579c7c1213e09807190d80ed3b8169
  result: PASS
decision:
  path: control-plane/registry/decisions/2026-07-19-agents-os-f7-post-closeout-projection-reconciliation-decision-v0.1.yaml
  sha256: c5b6bca2c16500fb9864a3709c9b3409030d45d7d3a5652b5a878d22174062cc
```

## Exact reconciliation

```yaml
baseline_PR14_merge: e22f356bfff59f817cd74e6fccfe3e80f0b52f01
accepted_post_closeout_projection_commit: 78704d1e6287d1d1893e8aeb5a7aad87086eef64
git_diff_paths: 9
modified_existing_projection_blobs: 7
added_projection_evidence_files: 2
deleted_or_renamed_paths: 0
frozen_subject_blobs_changed: 0
```

The seven existing blob changes were only:

```text
CURRENT_STATE durability and queue projection
Document Registry receipt/queue projection
Federated Registry expected-count projection
Machine default queue v4.7 -> v4.8
Dashboard default queue v4.7 -> v4.8
Control Chain default queue v4.7 -> v4.8
Workbench default queue v4.7 -> v4.8
```

The two additions were the F7 mainline durability receipt and Active Work
Queue v4.8. No F7 subject, contract, builder, fixture, validator, manifest,
independent review or freeze-decision byte changed.

## Validation

```yaml
manifest_inputs: 44/44_MATCH
frozen_subjects_at_baseline: 8/8_MATCH
frozen_subjects_at_accepted_projection: 8/8_MATCH
exact_7_modified_blob_hash_pairs: PASS
exact_2_added_blob_hashes: PASS
consumers_default_equal_explicit_v4_8: 4/4_PASS
Document_Registry: 911/911_PASS
Federated_Registry: 3/3_PASS
excluded_paths_committed: 0
F8_started: false
```

## Reconciled state

```yaml
F7_Git_objects_on_main: true
F7_mainline_integrated: true
F7_post_closeout_projection: v4.8_ACCEPTED
F7_durability_complete: true
F7_strict_v4_7_tree_requirement: SUPERSEDED_BY_PROJECTION_AWARE_CRITERIA
F8_started: false
F8_start_gate: AWAITING_JENN_EXPLICIT_START_DECISION
```

No implementation, runtime, database, provider, sensing, recording, private
raw Memory access, real Home mutation or external effect was authorized or
performed.
