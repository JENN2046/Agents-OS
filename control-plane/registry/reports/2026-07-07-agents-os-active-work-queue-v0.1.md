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

The current blocker is execution focus. The workspace has multiple valid routes
and a large amount of historical plan material, but it does not yet have a
single machine-readable active queue that a future local machine can consume.

## Queue Decision

Only one item may occupy `NOW`.

Historical plans and receipts are source material, not live tasks. VCPToolBox is
paused. External Git publication is blocked. Provider and plugin activation are
blocked.

## NOW

### NOW-001: Build AGENTS OS Machine Skeleton v0.1

Goal: create a minimal local machine body that can consume this queue and emit
reviewable local task envelopes without provider calls or autonomous runtime
execution.

Required output:

```text
machine_manifest
queue_item_schema
local_task_envelope_adapter
preview_only_runner_stub
validation_command
receipt_review_pattern
```

Initial mode:

```text
read_only_or_local_preview=true
provider_call_authorized=false
service_start_authorized=false
external_write_authorized=false
memory_write_authorized=false
runtime_plugin_activation_authorized=false
```

Acceptance:

```text
machine can list exactly one NOW item
machine can classify NEXT/LATER/BLOCKED/CLOSED items
machine can produce a preview task envelope from NOW-001
machine cannot run providers, services, plugins, external writes, or Memory writes
docctl status remains PASS
docctl doctor remains PASS
```

## NEXT

### NEXT-001: ColaMeta Executor Readiness Reconciliation

Use after the machine skeleton exists.

Purpose: reconcile `.colameta/plan.json`, prompt files, prior dry-run evidence,
and empty todo/decision state into a preview-only executor readiness item.

Blocked actions: real executor run, provider call, service start, Memory write.

### NEXT-002: Migration Plan Distillation Batch

Use after the machine can consume queue items.

Purpose: compress `ops/migration/` historical plans into a short list of
surviving local construction tasks and closed evidence.

Blocked actions: bulk move/delete/rename, external write, private-state read.

## LATER

### LATER-001: Root Private History Review Or History-Scrub Gate

Only needed before any external Git publication, hosted backup, mirror, or PR
from the root workspace repository.

### LATER-002: VCPToolBox Runtime Recovery Or Controlled First-Use

Keep paused until Jenn chooses runtime work again. Any restart must begin from
the existing cold audit and first-start boundary reports.

### LATER-003: AGENTS OS MCP Gateway And Connector Work

Only after the local machine has a queue contract and preview path.

### LATER-004: Formal Memory Loop

Only after Jenn explicitly chooses a Memory entry point. Do not infer formal
Memory writes from ordinary governance receipts.

## BLOCKED

```text
root_external_push: blocked until private-history review or history-scrub gate
provider_calls: blocked until explicit provider boundary
real_executor_run: blocked until machine skeleton and executor readiness pass
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

The next construction batch should build the smallest possible AGENTS OS Machine
Skeleton v0.1 from `NOW-001`.

Do not start with ColaMeta executor, VCPToolBox runtime, external Git, Memory, or
provider integration. Those become useful after the machine has a local queue
contract and preview-only body.
