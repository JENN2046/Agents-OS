# AGENTS OS F6 Validation Requirement Current Decision Start Receipt v0.1

Date: 2026-07-17
Mode: Yellow Work Batch
Result: `PASS`
Owner: Jenn
Agent steward: Nobao

## Authority

Jenn explicitly instructed:

```text
启动 F6 Validation Requirement Current Decision Contract Closure。
```

The instruction starts F6 semantic contract closure only. It does not accept or
freeze an F6 subject and does not authorize implementation, runtime, database,
authentication, provider execution, real Validation, real Task completion or
external effect.

## Fixed Start Surface

```yaml
F6_start_decision: control-plane/registry/decisions/2026-07-17-agents-os-f6-validation-requirement-current-decision-start-decision-v0.1.yaml
F6_start_decision_sha256: 335c838830fce9d6f48dedfcdd5bd07c2be5eacba1a3ec61962305fccae6f30f
active_work_queue: control-plane/registry/reports/2026-07-17-agents-os-active-work-queue-v2.6.md
active_work_queue_sha256: 656a847cf1b051c1ba8e03ccb12430ea4812856291537da078a6eb38821c71b4
F5_freeze_decision_sha256: 73270ad50c639be792f252e55befcf93c3dcc3edfffc74cb11c7c0fd212d7dbb
F5_manifest_sha256: 2c867bcab4810f5625caa3cb7a649209e19fc53eab34d6ba16737dcce8d14031
F5_independent_review_sha256: edcfb8cb4e2d8ff1cabe8a5e1ffaaacf44ed1844eb32444497851f2b5c03f334
F5_mainline_integration_merge_commit: 57523eea7cc6bf0579eebb250dfdbaa6e110e706
F5_mainline_durability_completion_commit: f1c5f6e2d99217a43cede082bedb75b4fc31e8e7
```

## Scope Materialized

- Immutable Jenn-owned F6 Start Decision.
- Active Work Queue v2.6, superseding v2.5 without rewriting history.
- `CURRENT_STATE.md`, Document Registry and federated registry projections.
- Four real default queue consumers moved from v2.5 to v2.6.
- Dashboard expectation updated from the completed Jenn start gate to active F6
  local contract closure.

## Validation

```text
13/13 start-decision path hashes match
F5 integration and durability commits exist and the final tree matches
default consumer output equals explicit v2.6 output
Machine tests pass
Dashboard tests pass after registry projection
Control Chain tests pass
Workbench tests pass
docctl status and doctor pass with zero unregistered documents
git diff --check passes
```

Final results:

```text
start_decision_path_hashes=13/13 PASS
F5_mainline_commit_and_tree_bindings=PASS
default_equals_explicit_v2.6=4/4 PASS
Machine=16/16 PASS
Dashboard=17/17 PASS
Control_Chain=30/30 PASS
Workbench=10/10 PASS
Document_Registry=786/786 PASS
Federated_Registry=3/3 PASS
docctl_status=PASS
docctl_doctor=PASS
unregistered_documents=0
git_diff_check=PASS
```

## Boundary

```yaml
F6_started: true
F6_accepted: false
F6_frozen: false
F7_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
database_change_authorized: false
service_start_authorized: false
provider_execution_authorized: false
real_Task_Run_Validation_mutation_authorized: false
real_effect_execution_authorized: false
```
