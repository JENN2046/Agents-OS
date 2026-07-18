# AGENTS OS F7 Home Domain Minimum Semantics Start Receipt v0.1

Date: 2026-07-18
Mode: Yellow Work Batch
Result: `PASS`
Owner: Jenn
Agent steward: Nobao

## Authority

Jenn explicitly instructed:

```text
启动 F7
```

The instruction starts F7 Home Domain Minimum Semantics contract closure only.
It does not accept or freeze an F7 subject and does not authorize F8,
implementation, runtime, database, authentication, provider execution, sensing,
recording, private raw Memory access, real Home data or external effect.

## Fixed start surface

```yaml
F7_start_decision: control-plane/registry/decisions/2026-07-18-agents-os-f7-home-domain-minimum-semantics-start-decision-v0.1.yaml
F7_start_decision_sha256: a4188f28d2bac61111a78824e39d4b5d060bb3926013b658b4cbfe70c579a068
active_work_queue: control-plane/registry/reports/2026-07-18-agents-os-active-work-queue-v4.3.md
active_work_queue_sha256: ccf09cf9e9b2c59ce1975a4da6fcf6d050c0b6083dcdd0b359ad3760cdc790e4
bound_path_hashes: 29/29_MATCH
F6_manifest_sha256: 519939e743457773476ed1915781c314046f790ec1322361d4df42c47fd5dd9f
F6_freeze_decision_sha256: 6bbe48030f6a739d683253f40b4ae122671ac801761eb7a752215c1b84920890
F6_mainline_integration_merge_commit: d41c94ba7d61f7513b2e90c658e3970a81ea20ab
F6_mainline_durability_completion_commit: 5373b5a8deca7c868ff13a5948c62d2b9356389d
```

## Boundary

```yaml
F7_started: true
F7_accepted: false
F7_frozen: false
F8_started: false
implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
database_change_authorized: false
service_start_authorized: false
provider_execution_authorized: false
private_raw_memory_access_authorized: false
sensing_or_recording_authorized: false
real_Home_or_Memory_mutation_authorized: false
real_effect_execution_authorized: false
```

F7 remains a logical bounded-context contract. It may define minimum semantic
fact classes and nonpromotion rules, but it may not create a second permission
system, identity authority, ledger, Task writer or Home runtime.
