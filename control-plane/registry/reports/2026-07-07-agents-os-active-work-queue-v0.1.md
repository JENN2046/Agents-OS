# AGENTS OS Active Work Queue v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: compress current AGENTS OS routes into one executable local work queue

## Purpose

This file turns the current workspace reality into a single queue for the next
construction step.

It is not a roadmap, vision memo, executor instruction, runtime config, Memory
write, provider prompt, or deployment plan.

## Boundary

- No `state-private/` content was read.
- No secrets, tokens, cookies, credentials, provider raw responses, private raw
  memory, active runtime config values, or raw logs were read or output.
- No service was started.
- No executor was run.
- No provider call was performed.
- No VCPToolBox source, active config, plugin manifest, or runtime state was
  modified.
- No external write, push, tag, release, deploy, publish, history rewrite, bulk
  move, delete, rename, or overwrite was performed.
- `.colameta/memory.md` content was not written and remains outside formal
  Memory.

## Source Facts Used

```text
current_state=present
root_git_baseline=present
root_git_external_push=blocked_until_private_history_review_or_history_scrub
docctl_status=PASS
docctl_doctor=PASS
docctl_score=100
machine_skeleton_exists=true
machine_validation=PASS
task_producer_exists=true
task_producer_validation=PASS
control_chain_exists=true
control_chain_validation=PASS
reviewed_queue_mutation_gate_exists=true
reviewed_queue_mutation_gate_validation=PASS
failure_handling_stop_loop_exists=true
failure_handling_stop_loop_validation=PASS
dashboard_memory_candidate_layer_exists=true
dashboard_memory_candidate_layer_validation=PASS
migration_plan_distillation_exists=true
migration_plan_distillation_validation=PASS
colameta_executor_inventory_readiness_map_exists=true
colameta_executor_inventory_readiness_map_validation=PASS
mcp_gateway_connector_boundary_plan_exists=true
mcp_gateway_connector_boundary_plan_validation=PASS
colameta_plan_exists=true
colameta_plan_versions=7
colameta_prompt_files=7
colameta_todo_items=0
colameta_decision_items=0
colameta_memory_size_bytes=0
ops_migration_files=262
ops_migration_plans=80
ops_migration_receipts=128
vcptoolbox_runtime_source=present_but_paused
```

## Current Diagnosis

The governance layer is no longer the main blocker. It can validate itself,
track local evidence, preserve a Git baseline, and explain hard boundaries.

The current blocker is provider / host dispatcher static behavior mapping. The
workspace now has a preview-only Machine Skeleton, preview-only Task Producer
Skeleton, Commander-first Control Chain, reviewed queue mutation gate, failure
handling stop loop, dashboard / Memory candidate layer, a safe `ops/migration/`
distillation, a ColaMeta executor inventory/readiness map, and an MCP gateway /
connector boundary plan.

ColaMeta local readiness is clean for summary-only preview, but real executor,
service startup, provider calls, Memory writes, and applying runtime preview
payloads remain blocked. MCP/connector boundaries are explicit. The next useful
step is to preserve historical provider registry and host dispatcher knowledge
as a static map before any runtime gate.

## Queue Decision

Only one item may occupy `NOW`.

Historical plans and receipts are source material, not live tasks. VCPToolBox is
paused. External Git publication is blocked. Provider and plugin activation are
blocked. ColaMeta readiness and MCP boundary evidence do not carry forward
runtime/provider/executor authorization.

## NOW

### NOW-001: Provider / Host Dispatcher Static Behavior Map

Goal: preserve the useful historical provider registry and host dispatcher
knowledge as a static control-plane map before any provider/runtime execution
gate.

Required output:

```text
provider_host_static_surface_summary
provider_registry_behavior_evidence_map
host_dispatcher_boundary_map
provider_execution_separation
forbidden_auth_provider_execution_guard
future_provider_execution_gate_sequence
receipt_review_pattern
```

Initial mode:

```text
read_only_or_local_preview=true
execution_authorized=false
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
external_write_authorized=false
memory_write_authorized=false
runtime_plugin_activation_authorized=false
auto_promote_authorized=false
bulk_move_delete_rename_authorized=false
private_state_read_authorized=false
provider_registry_write_authorized=false
provider_runtime_config_write_authorized=false
host_dispatcher_execution_authorized=false
live_host_start_authorized=false
connector_auth_write_authorized=false
provider_call_authorized=false
mcp_service_start_authorized=false
connector_external_write_authorized=false
```

Acceptance:

```text
read only historical provider/host dispatcher plans, evidence, receipts, reviews, and current governance references
do not inspect or modify auth/token/cookie/session files
do not start MCP, ColaMeta, live host, or provider services
do not execute host dispatcher routes
do not perform provider calls
do not mutate provider registry or provider/runtime configuration
separate provider plan/selection/static registry behavior from provider execution
produce a future provider execution gate sequence
do not read private state
docctl status remains PASS
docctl doctor remains PASS
```

## NEXT

```text
Root Private History Review Or History-Scrub Gate
```

## LATER

### LATER-001: Root Private History Review Or History-Scrub Gate

Only needed before any external Git publication, hosted backup, mirror, or PR
from the root workspace repository.

### LATER-002: VCPToolBox Runtime Recovery Or Controlled First-Use

Keep paused until Jenn chooses runtime work again. Any restart must begin from
the existing cold audit and first-start boundary reports.

### LATER-003: Formal Memory Loop

Only after Jenn explicitly chooses a Memory entry point. Do not infer formal
Memory writes from ordinary governance receipts.

## BLOCKED

```text
root_external_push: blocked until private-history review or history-scrub gate
provider_calls: blocked until explicit provider boundary
real_executor_run: blocked until reviewed executor gate after readiness
vcptoolbox_autonomous_or_provider_use: blocked until controlled runtime gate
state_private_reads: blocked by default
formal_memory_write: blocked until explicit Memory entry point
```

## CLOSED

```text
document_governance_9_5_core: closed for immediate repair; maintain cadence
docctl_status_doctor_cleanliness: closed for now; remains recurring validation
root_git_baseline: closed for local baseline
current_tracked_notion_url_redaction: closed for current tree
automation_rulebook_prohibited_first_update: closed for current operating model
machine_skeleton_v0.1: closed for preview-only control machine baseline; maintain review rule
task_producer_skeleton_v0.1: closed for preview-only candidate task production baseline; producer output remains candidate-only
control_chain_v0.1: closed for commander-first dual-track skeleton; queue remains proposal-only
queue_manager_reviewed_mutation_gate_v0.1: closed for accepted-review mutation gate; auto-promote remains unauthorized
failure_handling_stop_loop_v0.1: closed for failure report and stop-loop baseline; real repair execution remains unauthorized
dashboard_memory_candidate_layer_v0.1: closed for preview-only state visibility and Memory candidate baseline; formal Memory write remains unauthorized
migration_plan_distillation_v0.1: closed for safe summary of historical migration material; no historical runtime/provider/executor permission carried forward
colameta_executor_inventory_readiness_map_v0.1: closed for summary-only local executor inventory and readiness map; real executor, service start, provider calls, Memory writes, and runtime preview apply remain unauthorized
mcp_gateway_connector_boundary_plan_v0.1: closed for static MCP/connector boundary plan; live connector calls, auth mutation, MCP service start, provider calls, and external writes remain unauthorized
```

## Machine Input Contract

A future local machine should treat this file as queue input, not as executable
authority.

The machine may parse:

```text
NOW
NEXT
LATER
BLOCKED
CLOSED
acceptance criteria
authorization booleans
validation commands
```

The machine must not infer permission for:

```text
provider calls
service starts
plugin activation
external writes
Git push/tag/release/deploy/publish
history rewrite
formal Memory writes
state-private reads
secrets/auth/provider/runtime config reads or writes
```

## Immediate Construction Instruction

The next construction batch should implement the smallest possible provider /
host dispatcher static behavior map from `NOW-001`.

Do not start MCP, ColaMeta, live host, or provider services; do not execute host
dispatcher routes; do not call providers; do not mutate connector auth,
provider registry, provider/runtime configuration, `.colameta/plan.json`, or
`.colameta/state.json`; do not write `.colameta/memory.md`; do not read private
state; and do not activate VCPToolBox/runtime/plugin work.
