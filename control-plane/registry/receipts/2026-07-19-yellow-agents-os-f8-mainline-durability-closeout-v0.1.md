# AGENTS OS F8 Mainline Durability Closeout Receipt v0.1

Date: 2026-07-19
Mode: Yellow Work Batch
Result: `PASS`
Owner: Jenn
Agent steward: Nobao

## Delivery facts

```yaml
repository: JENN2046/Agents-OS
visibility: PRIVATE
base_branch: main
source_branch: agent/f8-home-to-orchestrator-minimum-interface
scoped_commit: fc153556c29f21af264d809874ebc3bcf66f4b6b
pull_request: https://github.com/JENN2046/Agents-OS/pull/17
pull_request_state: MERGED
mainline_integration_merge_commit: 8852d14e6afdfca16e5cc48d446f9a8c85671a43
scoped_file_count: 102
excluded_path_count: 0
```

The scoped commit contains the complete F8 R1-R5 frozen lineage and only its
necessary governance projections. No `memory/**`, `state-private/**`,
`ops/reports/**`, `execution/agents-os-workbench/records/**`, secret,
credential, token, cookie, provider raw response or unrelated local work was
committed.

## Frozen object verification on main

```yaml
manifest:
  path: control-plane/registry/reports/2026-07-19-agents-os-f8-r5-atomic-independent-review-package-v0.1.manifest.yaml
  sha256: c4161d9f4ffaaa094e2aebd9e5697cf40003e35691ca4e2a4de169ba4e83b672
  verified_inputs: 73/73_MATCH
frozen_subjects:
  count: 20
  result: 20/20_MATCH
independent_review:
  path: control-plane/registry/reviews/2026-07-19-yellow-agents-os-f8-r5-nobao-independent-review.yaml
  sha256: 713358f67cd763bf86d6a6d7f36e2ef3befc04f2ee73ee7667e1629ae271353f
  result: PASS_NO_BLOCKER
freeze_decision:
  path: control-plane/registry/decisions/2026-07-19-agents-os-f8-home-to-orchestrator-minimum-interface-r5-atomic-freeze-decision-v0.1.yaml
  sha256: ce35fb0ece80758c9690434ef997efe5fbc01b3482af8228503b2060b70eea6d
  status: ACCEPTED_FROZEN
```

The hashes were recomputed from `origin/main` commit
`8852d14e6afdfca16e5cc48d446f9a8c85671a43`, not from mutable working-tree
bytes.

## Validation

```yaml
commit_tree_manifest_inputs: 73/73_MATCH
commit_tree_frozen_subjects: 20/20_MATCH
fixed_commands_before_delivery: 14/14_PASS
Document_Registry: PASS
Federated_Registry: PASS
Machine_Dashboard_Control_Chain_Workbench: PASS
default_queue_projection: v6.4
excluded_paths_committed: 0
remote_main_contains_scoped_commit: true
local_main_equals_origin_main_before_projection: true
```

`git diff --check` for the original 102-file integration reports historical
Markdown hard-break spaces and EOF blank lines in fixed F8 bytes. Five affected
files are manifest-bound and the freeze decision package is decision-bound.
They were preserved exactly because whitespace normalization would invalidate
the accepted hashes. This is a fixed-byte preservation exception, not a new
post-freeze modification.

## Boundary

```yaml
F8_Git_objects_on_main: true
F8_mainline_integrated: true
F8_durability_complete: true
F8_accepted: true
F8_frozen: true
Phase_5A_started: false
implementation_authorized: false
runtime_activation_authorized: false
database_or_provider_authorized: false
production_authentication_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
real_effect_authorized: false
next_gate: JENN_EXPLICIT_PHASE_5A_START_DECISION
```

This receipt does not start Phase 5A and does not authorize implementation,
runtime, database, provider, authentication, Memory, sensing or effect work.
