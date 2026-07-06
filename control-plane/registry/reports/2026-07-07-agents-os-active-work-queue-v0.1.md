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
task_producer_route_option_intake_exists=true
task_producer_route_option_intake_validation=PASS
task_producer_route_choice_preview_exists=true
task_producer_route_choice_preview_validation=PASS
control_chain_exists=true
control_chain_validation=PASS
control_chain_route_choice_queue_proposal_exists=true
control_chain_route_choice_queue_proposal_validation=PASS
control_chain_reviewed_route_adoption_preview_exists=true
control_chain_reviewed_route_adoption_preview_validation=PASS
control_chain_reviewed_route_adoption_apply_gate_exists=true
control_chain_reviewed_route_adoption_apply_gate_validation=PASS
reviewed_queue_mutation_gate_exists=true
reviewed_queue_mutation_gate_validation=PASS
failure_handling_stop_loop_exists=true
failure_handling_stop_loop_validation=PASS
dashboard_memory_candidate_layer_exists=true
dashboard_memory_candidate_layer_validation=PASS
dashboard_route_options_visibility_exists=true
dashboard_route_options_visibility_validation=PASS
dashboard_route_adoption_gate_readiness_exists=true
dashboard_route_adoption_gate_readiness_validation=PASS
dashboard_route_choice_handoff_exists=true
dashboard_route_choice_handoff_validation=PASS
migration_plan_distillation_exists=true
migration_plan_distillation_validation=PASS
colameta_executor_inventory_readiness_map_exists=true
colameta_executor_inventory_readiness_map_validation=PASS
mcp_gateway_connector_boundary_plan_exists=true
mcp_gateway_connector_boundary_plan_validation=PASS
provider_host_dispatcher_static_behavior_map_exists=true
provider_host_dispatcher_static_behavior_map_validation=PASS
root_private_history_review_gate_exists=true
root_private_history_review_gate_validation=PASS
route_selection_checkpoint_exists=true
route_selection_checkpoint_validation=PASS
machine_route_selection_stop_guard_exists=true
machine_route_selection_stop_guard_validation=PASS
machine_next_user_action_handoff_exists=true
machine_next_user_action_handoff_validation=PASS
next_route_selection_package_exists=true
next_route_selection_package_validation=PASS
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

The Task Producer can now generate blocked candidate previews from route
options A-E without selecting a route, writing the queue, promoting to NOW, or
authorizing execution.

The Task Producer can also preview explicit Jenn route-choice confirmation text
without writing workspace route state, mutating the Active Work Queue, promoting
to NOW, or authorizing execution.

The Control Chain now recognizes those route-option candidates as an explicit
Jenn-decision stop gate. Commander returns `stop_needs_jenn_decision` and Track
Selector keeps `track_authorized=false`, so route selection cannot silently turn
into queue promotion or execution.

The Control Chain can now create a preview-only `NEXT` queue proposal from a
Task Producer route-choice preview. This produces review material only; it does
not write route state, mutate the Active Work Queue, promote to NOW, or
authorize execution.

The Control Chain can also inspect an accepted Nobao review and produce a
reviewed route adoption preview. It can show the future `NEXT` append, while
keeping Active Work Queue mutation, route adoption, queue promotion, and
execution unauthorized.

The Control Chain now has an explicit reviewed route adoption apply gate. It
can append a reviewed route to `NEXT` only when `--apply` is supplied, while
keeping queue promotion and execution unauthorized. This work did not apply it
to the real Active Work Queue.

The Dashboard now also surfaces the route-selection package as structured
preview-only options while keeping route auto-selection, queue promotion, and
execution authorization false.

The Dashboard now also surfaces route adoption gate readiness. It reports that
the proposal, preview, and apply gate evidence exist, while keeping
`can_apply_now=false`, Active Work Queue mutation, queue promotion, and
execution unauthorized.

ColaMeta local readiness is clean for summary-only preview, but real executor,
service startup, provider calls, Memory writes, and applying runtime preview
payloads remain blocked. MCP/connector boundaries are explicit. Provider and
host dispatcher behavior knowledge is static-only and does not carry forward
runtime/provider execution authorization.

The root private-history review gate has run as a no-push local review. Current
scans found no Notion-domain or common token-shape path-level hits in current
HEAD or reachable root Git history. No history scrub is indicated by the current
scan.

External publication remains blocked until Jenn chooses a target and a separate
exact external-write gate exists. The route-selection checkpoint records that no
new route should start automatically after the current governance sequence.
The Machine now treats this stop-state as non-actionable and requiring Jenn
route selection before execution. Machine preview now also carries a
`next_user_action` handoff with Jenn as decision owner, accepted route ids A-E,
and no route auto-selection, active queue mutation, queue promotion, execution,
write, or raw content output. The next route selection package now preserves the
route options and exact confirmation templates without selecting any route.
The Task Producer route-choice preview can parse a future explicit Jenn
selection text, but it still does not adopt the route into workspace state or
mutate the queue.
The Control Chain route-option stop gate keeps the same boundary after Task
Producer candidate generation: route options can be inspected, but not selected,
promoted, routed, or executed.
The Control Chain route-choice queue proposal gate adds the next review layer:
a selected route preview can become a proposed `NEXT` item, but only as
proposal-only JSON and not as a queue write.
The reviewed route adoption preview adds the accepted-review layer, but still
stops before any file write.
The reviewed route adoption apply gate adds the explicit future write gate, but
the current queue remains in stop-state with no selected route.
The Dashboard route adoption gate readiness card makes that future gate visible
without changing queue state.

The Dashboard now also emits a `next_user_action` handoff during the stop-state.
It points to Jenn as the decision owner, lists accepted route ids A-E, and
points to the route-selection confirmation template source without printing the
template body, selecting a route, mutating the queue, promoting an item, or
authorizing execution.

## Queue Decision

Only one item may occupy `NOW`.

Historical plans and receipts are source material, not live tasks. VCPToolBox is
paused. External Git publication is blocked. Provider and plugin activation are
blocked. ColaMeta readiness and MCP boundary evidence do not carry forward
runtime/provider/executor authorization.

## NOW

### NOW-001: No Active Automatic Construction Item

Goal: hold the queue after closing the current autonomous governance sequence
and wait for Jenn to choose the next construction route.

Required output:

```text
route_selection_options
blocked_without_jenn_direction
no_auto_runtime_or_provider_guard
no_auto_memory_or_external_write_guard
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
do not infer a new construction route without Jenn direction
do not start VCPToolBox, MCP, ColaMeta, live host, or provider services
do not run executor or host dispatcher routes
do not perform provider calls
do not write formal Memory
do not push or externally write
do not rewrite history or scrub without a separate exact gate
do not read state-private
do not read or print raw secrets/token/cookie/credential/private memory/provider raw response/log content
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
task_producer_route_option_intake_v0.1: closed for candidate-only route option intake; route selection, queue write, queue promotion, and execution remain unauthorized
task_producer_route_choice_preview_v0.1: closed for preview-only explicit route-choice intake; route state, queue write, queue promotion, and execution remain unauthorized
control_chain_v0.1: closed for commander-first dual-track skeleton; queue remains proposal-only
control_chain_route_choice_queue_proposal_v0.1: closed for preview-only route-choice queue proposal; route adoption, queue write, queue promotion, and execution remain unauthorized
control_chain_reviewed_route_adoption_preview_v0.1: closed for reviewed route adoption preview; active queue write, route adoption, queue promotion, and execution remain unauthorized
control_chain_reviewed_route_adoption_apply_gate_v0.1: closed for explicit reviewed route adoption apply gate; no real route selected or adopted, queue promotion and execution remain unauthorized
queue_manager_reviewed_mutation_gate_v0.1: closed for accepted-review mutation gate; auto-promote remains unauthorized
failure_handling_stop_loop_v0.1: closed for failure report and stop-loop baseline; real repair execution remains unauthorized
dashboard_memory_candidate_layer_v0.1: closed for preview-only state visibility and Memory candidate baseline; formal Memory write remains unauthorized
dashboard_route_options_visibility_v0.1: closed for preview-only route selection visibility; route auto-selection, queue promotion, and execution remain unauthorized
migration_plan_distillation_v0.1: closed for safe summary of historical migration material; no historical runtime/provider/executor permission carried forward
colameta_executor_inventory_readiness_map_v0.1: closed for summary-only local executor inventory and readiness map; real executor, service start, provider calls, Memory writes, and runtime preview apply remain unauthorized
mcp_gateway_connector_boundary_plan_v0.1: closed for static MCP/connector boundary plan; live connector calls, auth mutation, MCP service start, provider calls, and external writes remain unauthorized
provider_host_dispatcher_static_behavior_map_v0.1: closed for static provider registry and host dispatcher evidence map; provider calls, provider execution, host dispatcher execution, registry/config mutation, real spawn, service start, executor run, and external writes remain unauthorized
root_private_history_review_gate_v0.1: closed for no-push root private-history pattern review; no history scrub indicated, but external publication still requires a separate target-specific external-write gate
dashboard_route_adoption_gate_readiness_v0.1: closed for preview-only route adoption gate readiness visibility; active queue mutation, queue promotion, and execution remain unauthorized
dashboard_route_choice_handoff_v0.1: closed for preview-only next_user_action handoff; Jenn remains the route decision owner, active queue mutation, queue promotion, and execution remain unauthorized
machine_next_user_action_handoff_v0.1: closed for preview-only machine next_user_action handoff; Jenn remains the route decision owner, route auto-selection, active queue mutation, queue promotion, and execution remain unauthorized
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

The next construction batch should not infer a new route automatically. Jenn can
choose one of these routes:

```text
VCPToolBox Runtime Recovery Or Controlled First-Use
Formal Memory Loop
External Git Publication Exact Gate
Provider Execution Design Gate
New AGENTS OS construction route
```

This route-selection checkpoint is now recorded as the active stop-state
artifact. It does not choose any route and does not authorize runtime,
provider, Memory, or external-write work. Machine preview must report this
stop-state as `blocked=true`, `actionable=false`, and
`requires_jenn_decision=true`.

Jenn can use
`control-plane/registry/reports/2026-07-07-agents-os-next-route-selection-package-v0.1.md`
as the route selection packet. It is evidence only and does not grant execution
authority until Jenn sends a current explicit route selection.

Until Jenn chooses, do not read `state-private/`; do not read or print raw
secrets, tokens, cookies, credentials, private raw memory, provider raw
responses, raw logs, private Notion page contents, or private page URLs; do not
push, tag, release, deploy, publish, externally write, rewrite history, reset
hard, clean, bulk delete, or destructively scrub. Keep provider calls, service
starts, executor runs, host dispatcher execution, provider registry/config
mutation, and VCPToolBox/runtime/plugin activation blocked.
