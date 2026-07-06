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
provider_host_dispatcher_static_behavior_map_exists=true
provider_host_dispatcher_static_behavior_map_validation=PASS
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

The provider / host dispatcher static behavior mapping has been preserved as a
static control-plane map. The workspace now has a preview-only Machine Skeleton,
preview-only Task Producer Skeleton, Commander-first Control Chain, reviewed
queue mutation gate, failure handling stop loop, dashboard / Memory candidate
layer, a safe `ops/migration/` distillation, a ColaMeta executor
inventory/readiness map, an MCP gateway / connector boundary plan, and a
provider / host dispatcher static behavior map.

ColaMeta local readiness is clean for summary-only preview, but real executor,
service startup, provider calls, Memory writes, and applying runtime preview
payloads remain blocked. MCP/connector boundaries are explicit. Provider and
host dispatcher behavior knowledge is static-only and does not carry forward
runtime/provider execution authorization.

The current blocker is root private Git history risk before any external Git
publication, hosted backup, mirror, or PR from the root workspace repository.

## Queue Decision

Only one item may occupy `NOW`.

Historical plans and receipts are source material, not live tasks. VCPToolBox is
paused. External Git publication is blocked. Provider and plugin activation are
blocked. ColaMeta readiness and MCP boundary evidence do not carry forward
runtime/provider/executor authorization.

## NOW

### NOW-001: Root Private History Review Or History-Scrub Gate

Goal: review root Git history publication risk and decide whether external
publication needs a no-push private-history review, a history-scrub plan, or a
local-only policy.

Required output:

```text
root_private_history_risk_summary
tracked_sensitive_pattern_scan
git_history_publication_blocker_map
history_scrub_option_set
no_external_push_guard
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
git_push_authorized=false
history_rewrite_authorized=false
tag_release_deploy_publish_authorized=false
memory_write_authorized=false
runtime_plugin_activation_authorized=false
auto_promote_authorized=false
bulk_move_delete_rename_authorized=false
private_state_read_authorized=false
secret_raw_read_authorized=false
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
inspect only safe Git metadata, tracked file paths, and redacted working-tree content where needed
do not read state-private
do not read or print raw secrets/token/cookie/credential/private memory/provider raw response/log content
do not print private Notion page URLs or private page contents if found
do not push, tag, release, deploy, publish, or perform external writes
do not rewrite history, reset hard, clean, bulk delete, or destructively scrub without a separate exact gate
produce blocker map and option set only
do not read private state
docctl status remains PASS
docctl doctor remains PASS
```

## NEXT

```text
No active NEXT items.
```

## LATER

### LATER-001: VCPToolBox Runtime Recovery Or Controlled First-Use

Keep paused until Jenn chooses runtime work again. Any restart must begin from
the existing cold audit and first-start boundary reports.

### LATER-002: Formal Memory Loop

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
provider_host_dispatcher_static_behavior_map_v0.1: closed for static provider registry and host dispatcher evidence map; provider calls, provider execution, host dispatcher execution, registry/config mutation, real spawn, service start, executor run, and external writes remain unauthorized
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

The next construction batch should implement the smallest possible root private
history review or history-scrub gate from `NOW-001`.

Do not read `state-private/`; do not read or print raw secrets, tokens, cookies,
credentials, private raw memory, provider raw responses, raw logs, private
Notion page contents, or private page URLs; do not push, tag, release, deploy,
publish, externally write, rewrite history, reset hard, clean, bulk delete, or
destructively scrub without a separate exact gate. Keep provider calls, service
starts, executor runs, host dispatcher execution, provider registry/config
mutation, and VCPToolBox/runtime/plugin activation blocked.
