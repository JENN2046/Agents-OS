# AGENTS OS Migration Plan Distillation v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: safe summary of `ops/migration/` historical migration plans, evidence, and surviving local construction tasks

## Boundary

This distillation used only:

```text
ops/migration file names
ops/migration directory counts
top-level Markdown headings
status/next/deferred/closeout signal lines from historical Markdown
current Active Work Queue and CURRENT_STATE
```

It did not bulk move, delete, rename, overwrite, archive, sync, execute,
activate runtimes/plugins, start services, call providers, write formal Memory,
read `state-private/`, read private raw Memory, read secrets/tokens/cookies, or
read provider raw responses.

## Migration Inventory Summary

```text
ops_migration_files=262
candidates=1
decisions=10
inventory=42
plans=80
receipts=128
receipt_closeout_like_files=46
```

Phase distribution by filename:

```text
phase_2=26
phase_3=5
phase_4=25
phase_5=34
phase_6=9
phase_7=32
phase_8=25
phase_9=34
phase_10=33
phase_11=10
unphased_or_batch=29
```

## Closed Evidence

The migration history is not one live plan. It is a chain of closed or limited
evidence packages.

Closed or effectively closed groups:

```text
phase_2_rules_assets_batches:
  contracts/registry examples, templates, env template, security template,
  ordinary runbooks, validation scripts, prompt catalogs, registry authority,
  registry consumer readiness, and consumer alignment have receipts.

phase_3_validation_scope:
  validation scope and closeout evidence exist.

phase_4_registry_and_static_consumer:
  registry semantic rules, YAML parse/evaluation, limited static consumer
  integration, and registry acceptance gates have receipts/closeouts.

phase_5_validation_layer:
  workspace validator, extension manifest validator, and no-secrets validator
  evidence were accepted only with limits and redaction/wrapper notes carried
  forward.

phase_6_consumer_runtime_static_readiness:
  limited static/local readiness was closed, while runtime behavior,
  loader behavior, full consumer acceptance, credential audit, and private-state
  reads were explicitly not granted.

phase_7_runtime_loader_read_boundaries:
  runtime/loader metadata and narrow read evidence were collected with limits.
  Runtime/loader behavior acceptance was not granted.

phase_8_parser_yaml_package_lock_static_review:
  parser/semantic review, routing-policy YAML parse/semantic review, and
  package-lock static review were closed with limits.

phase_9_runtime_router_loader_local_validation:
  selected local readonly behavior, loader behavior, state-sync display,
  typecheck support, and source revalidation gates were closed with limits.

phase_10_mcp_provider_registry_host_dispatcher_readiness:
  local MCP readiness, consumer runtime readiness, provider registry, and
  host-dispatcher/provider behavior evidence were collected with limits.

phase_11_file_provider_and_provider_execution_readonly:
  file provider manifest persistence and provider execution runner controlled
  read-only evidence were collected with limits.
```

## Discarded Or Archived Context

These historical items should not be treated as live tasks or authority:

```text
Windows reference root as execution root:
  historical source/reference only; canonical execution root is WSL.

execution/Codex_Autonomous_Work_Harness:
  historical high-risk execution harness; must not be carried forward as a
  direct runtime without a new gate.

root duplicate WORKSPACE_REGISTRY.yaml / SECURITY_BOUNDARIES.md targets:
  old migration paths risk drift; current AGENTS OS uses active local governance
  and current registry/docctl paths.

maintenance/sync helper:
  historical deferred helper; no sync/push/remote action is authorized.

placeholder validators or scripts:
  historical reference unless current validators/docctl own them.

provider/host/runner exact-run plans:
  historical evidence only; no provider call, service start, or real executor
  run is authorized by this distillation.
```

## Surviving Local Task List

The surviving work should be recast into current AGENTS OS control-plane tasks,
not replayed as historical migration phases.

```text
1. ColaMeta Executor Inventory And Readiness Map
   Purpose: confirm local executor/runner inventory, entrypoints, readiness
   blockers, existing dry-run/preflight evidence, and what remains missing.
   Boundary: read-only/local metadata; no service start, no executor run, no
   provider call, no Memory write.

2. MCP Gateway And Connector Boundary Plan
   Purpose: turn the historical local MCP/runtime readiness work into a modern
   AGENTS OS gateway boundary plan.
   Boundary: design/static summary only; no connector auth mutation, no
   service start, no provider call.

3. Provider / Host Dispatcher Static Behavior Map
   Purpose: preserve the useful Phase 10 provider registry and host dispatcher
   behavioral knowledge as a static control-plane map.
   Boundary: no provider call, no auth/token/session/config reads or writes.

4. Root Private History Review Or History-Scrub Gate
   Purpose: unblock future external Git publication only if Jenn wants it.
   Boundary: no push, tag, release, deploy, history rewrite, or external write.

5. VCPToolBox Runtime Recovery Or Controlled First-Use
   Purpose: keep VCPToolBox runtime work paused but represented as a controlled
   future gate.
   Boundary: no startup, no plugin activation, no provider call unless a
   separate runtime gate authorizes it.

6. Formal Memory Entry Route
   Purpose: convert dashboard Memory candidates into a reviewed Memory entry
   flow only if Jenn chooses a Memory entry point.
   Boundary: no formal Memory write from ordinary receipts or dashboards.
```

## Queue Decision

The next queue item should be:

```text
ColaMeta Executor Inventory And Readiness Map
```

Reason:

```text
CURRENT_STATE still lists executor inventory as unconfirmed.
ColaMeta runner files exist but todolist/decisions are empty.
Provider-backed execution and real executor run remain blocked.
A read-only inventory map is the smallest safe next step before any executor gate.
```

## Validation Summary

```text
migration_distillation_mode=summary_only
bulk_move_delete_rename_performed=false
private_state_read=false
service_started=false
executor_real_run=false
provider_call_performed=false
external_write_performed=false
formal_memory_write_performed=false
```

## Next

Move the Active Work Queue to `ColaMeta Executor Inventory And Readiness Map`.
Keep VCPToolBox, provider-backed work, formal Memory writes, external Git
publication, and real executor runs blocked until their own gates.
