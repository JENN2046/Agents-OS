# AGENTS OS Next Route Selection Package v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local route-selection package after `No Active Automatic Construction Item`

## Purpose

This package turns the current route-selection stop-state into explicit choices
for Jenn.

It does not choose a route. It does not promote a queue item. It does not
authorize runtime activation, provider calls, executor runs, formal Memory
writes, external writes, Git publication, or destructive cleanup.

## Current Stop-State

```text
active_queue_now=No Active Automatic Construction Item
machine_preview.blocked=true
machine_preview.actionable=false
machine_preview.requires_jenn_decision=true
machine_preview.execution_authorized=false
route_auto_selection_authorized=false
```

The next route must be selected by Jenn before a new construction batch starts.

## Route Options

### Option A: VCPToolBox Runtime Recovery Or Controlled First-Use

Goal: make the local VCPToolBox runtime usable, starting from the existing cold
audit, dependency/build evidence, active config gate, native addon build batch,
and localhost no-provider first-start work.

Good when Jenn wants:

```text
local runtime utility
real localhost startup
VCPToolBox operational recovery
plugin/provider boundary review before use
```

First safe package:

```text
AGENTS OS VCPToolBox controlled recovery restart v0.1
```

Must keep:

```text
localhost_only=true
provider_call_authorized=false
plugin_activation_authorized=false
external_write_authorized=false
secret_raw_read_authorized=false
runtime_config_value_output_authorized=false
```

Primary risk: runtime state, active config, plugin surfaces, logs, and
startup-side effects. This route needs tight no-provider/no-plugin startup
observation and secret-safe log summaries.

### Option B: Formal Memory Loop

Goal: establish a controlled Memory candidate-to-confirmation loop so AGENTS OS
can preserve stable long-term facts without silently writing formal Memory.

Good when Jenn wants:

```text
less repeated context
stable system memory
clear Memory confirmation entry point
candidate review before write
```

First safe package:

```text
AGENTS OS formal Memory candidate gate v0.1
```

Must keep:

```text
formal_memory_write_authorized=false until exact Jenn confirmation
private_raw_memory_read_authorized=false
state_private_read_authorized=false
provider_call_authorized=false
external_write_authorized=false
```

Primary risk: accidental permanent Memory, private raw Memory exposure, or
turning ordinary receipts into memory without Jenn confirmation.

### Option C: External Git Publication Exact Gate

Goal: prepare a target-specific external Git publication path for backup or
collaboration after private-history and remote/branch checks.

Good when Jenn wants:

```text
remote backup
PR workflow
shareable governance baseline
external repository hygiene
```

First safe package:

```text
AGENTS OS external Git publication target gate v0.1
```

Must keep:

```text
git_push_authorized=false until exact target gate
force_push_authorized=false
tag_release_deploy_publish_authorized=false
history_rewrite_authorized=false unless separate scrub gate
secret_raw_read_authorized=false
external_write_authorized=false until exact target gate
```

Primary risk: irreversible external publication of private history, private
URLs, local synthesis material, or unintended remote branch changes.

### Option D: Provider Execution Design Gate

Goal: design a provider execution boundary before any live provider or host
dispatcher execution is allowed.

Good when Jenn wants:

```text
future provider-backed execution
fake-provider harness first
host dispatcher boundary hardening
cost/network/auth controls before real calls
```

First safe package:

```text
AGENTS OS provider execution design gate v0.1
```

Must keep:

```text
provider_call_authorized=false
host_dispatcher_execution_authorized=false
provider_runtime_config_write_authorized=false
provider_raw_response_output_authorized=false
service_start_authorized=false
external_write_authorized=false
```

Primary risk: paid calls, provider credentials/config, raw provider responses,
host process execution, and confusing dry-run readiness with real authorization.

### Option E: New AGENTS OS Construction Route

Goal: open a new route outside the four named options while preserving the
Machine stop guard and P3 boundary.

Good when Jenn wants:

```text
new subsystem
new governance machine feature
new local tool
new product direction
new runtime integration
```

First safe package:

```text
AGENTS OS new construction route intake v0.1
```

Must keep:

```text
route_scope_required=true
route_auto_selection_authorized=false
p3_boundary_inherited=true
provider_call_authorized=false unless separately confirmed
external_write_authorized=false unless separately confirmed
formal_memory_write_authorized=false unless separately confirmed
```

Primary risk: vague scope becoming silent execution authority.

## Exact Confirmation Text Templates

These templates are intentionally not self-executing. Jenn may edit one and send
it as the next instruction.

### Template A

```text
确认选择 AGENTS OS 下一路线：VCPToolBox Runtime Recovery Or Controlled First-Use。
先准备 controlled recovery restart v0.1 的最小本地执行包；保持 localhost-only、
no-provider、no-plugin-activation、no-external-write，并保留 receipt/review/validation。
```

### Template B

```text
确认选择 AGENTS OS 下一路线：Formal Memory Loop。
先准备 formal Memory candidate gate v0.1；只做候选和确认模型，不写正式 Memory，
不读 private raw Memory，不读 state-private/，并保留 receipt/review/validation。
```

### Template C

```text
确认选择 AGENTS OS 下一路线：External Git Publication Exact Gate。
先准备 target-specific publication gate v0.1；不 push、不 tag、不 release、
不 deploy、不 publish、不 rewrite history，并保留 receipt/review/validation。
```

### Template D

```text
确认选择 AGENTS OS 下一路线：Provider Execution Design Gate。
先准备 provider execution design gate v0.1；只做边界和 fake-provider/dry-run 设计，
不做 provider call、不执行 host dispatcher、不改 provider/runtime config，
并保留 receipt/review/validation。
```

### Template E

```text
确认选择 AGENTS OS 下一路线：New AGENTS OS Construction Route。
路线目标是：<Jenn 填写目标>。
先准备 new construction route intake v0.1；不得自动扩大到 provider/runtime/
Memory/external write，并保留 receipt/review/validation。
```

## Selection Rule

Until Jenn selects a route:

```text
NOW remains No Active Automatic Construction Item
Machine preview remains blocked/actionable=false
Nobao does not promote any route to NOW
Task Producer may produce candidates only after explicit route intent
Task Producer may preview explicit Jenn route-choice text without writing queue state
Control Chain may not treat this package as Commander authorization
```

## Boundary Kept

```text
route_auto_selection_authorized=false
queue_promotion_authorized=false
vcptoolbox_start_authorized=false
plugin_activation_authorized=false
executor_run_authorized=false
host_dispatcher_execution_authorized=false
provider_call_authorized=false
formal_memory_write_authorized=false
external_write_authorized=false
git_push_authorized=false
history_rewrite_authorized=false
state_private_read_authorized=false
secret_raw_read_authorized=false
provider_raw_response_output_authorized=false
raw_log_output_authorized=false
```

## Validation Plan

```text
machine preview-now must remain blocked/actionable=false
machine validate must pass
document registry validator must pass
federated document registry validator must pass
docctl status must pass
docctl doctor must pass
```

## Decision

Accepted as a route-selection package. It gives Jenn concrete route choices
without selecting or executing one.
