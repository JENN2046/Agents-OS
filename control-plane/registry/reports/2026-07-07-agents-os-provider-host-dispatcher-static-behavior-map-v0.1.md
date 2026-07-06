# AGENTS OS Provider / Host Dispatcher Static Behavior Map v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: static control-plane map of historical provider registry and host dispatcher evidence

## Purpose

This report preserves the useful provider registry and host dispatcher behavior
knowledge from historical `ops/migration/` evidence as a static control-plane
map.

It is not runtime authorization, provider execution authorization, service
startup authorization, connector authorization, provider registry mutation, or
provider/runtime configuration.

## Boundary

- No `state-private/` content was read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  responses, active runtime config values, raw logs, auth files, or session files
  were read or output.
- No service was started.
- No executor was run.
- No host dispatcher route was executed.
- No provider call was performed.
- No provider registry or provider/runtime configuration was modified.
- No MCP, ColaMeta, live host, provider service, plugin, or VCPToolBox runtime
  was started or activated.
- No external write, push, tag, release, deploy, publish, history rewrite, bulk
  move, delete, rename, overwrite, or formal Memory write was performed.

## Source Evidence

Historical evidence and receipts used:

```text
ops/migration/inventory/phase-10-host-dispatcher-provider-behavior-evidence-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-review-closeout-receipt-2026-06-29.md
ops/migration/inventory/phase-10-provider-registry-selection-behavior-evidence-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-review-closeout-receipt-2026-06-29.md
ops/migration/inventory/phase-10-provider-registry-mutation-query-behavior-evidence-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-review-closeout-receipt-2026-06-29.md
ops/migration/inventory/phase-10-provider-registry-remote-auth-security-behavior-evidence-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-review-closeout-receipt-2026-06-29.md
ops/migration/inventory/phase-11-file-provider-manifest-store-persistence-evidence-2026-06-29.md
ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-review-closeout-receipt-2026-06-29.md
ops/migration/inventory/phase-11-provider-execution-runner-controlled-readonly-evidence-2026-06-29.md
ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-review-closeout-receipt-2026-06-29.md
```

Current governance references used:

```text
CURRENT_STATE.md
control-plane/registry/reports/2026-07-07-agents-os-active-work-queue-v0.1.md
```

## provider_host_static_surface_summary

```text
host_dispatcher_provider_behavior=8 selected pass / 0 fail / 11 skipped
provider_registry_selection_behavior=25 selected pass / 0 fail / 18 skipped
provider_registry_mutation_query_behavior=8 selected pass / 0 fail / 35 skipped
provider_registry_remote_auth_security_behavior=5 selected pass / 0 fail / 38 skipped
file_provider_manifest_store_persistence=5 selected pass / 0 fail / 38 skipped
provider_execution_runner_controlled_readonly=5 selected pass / 0 fail / 16 skipped
```

All source gates were accepted only with narrow local limits. None granted full
provider registry acceptance, full provider execution acceptance, real Codex CLI
execution acceptance, remote agent execution acceptance, network acceptance,
workspace-write acceptance, deploy/release/publish acceptance, or external write
acceptance.

## provider_registry_behavior_evidence_map

### Selection

Historical selection evidence confirms local provider registry behavior for:

- registering and reading a read-only `codex-cli` manifest;
- listing all providers and enabled providers;
- excluding disabled providers from automatic selection;
- rejecting missing providers, disabled providers by default, kind mismatch,
  manifest hash mismatch, missing capabilities, unsupported side effects, and
  unsupported sandbox;
- accepting supported side effects and read-only sandbox;
- selecting providers for grants and routing decisions;
- rejecting routing decisions without provider grants;
- rejecting routing decision and provider grant manifest mismatch;
- sanitizing selection and routing-decision selection results.

This proves static selection and fail-closed behavior only. It does not prove
real provider execution.

### Mutation / Query

Historical mutation/query evidence confirms local in-memory behavior for:

- register, get, list, and unregister operations;
- duplicate provider id rejection;
- manifest kind mismatch rejection;
- provider/manifest mismatch rejection;
- disabled provider filtering;
- provider queries by kind, side effect class, and sandbox support.

This proves local mutation/query semantics for the tested registry surface. It
does not authorize mutating the current provider registry or provider/runtime
configuration.

### Remote Auth / Security

Historical remote-auth/security evidence confirms local fail-closed behavior:

- remote agents without explicit `authSchemes` are rejected;
- anonymous remote agent auth schemes are rejected case-insensitively;
- anonymous auth declared only on a provider manifest is rejected;
- manifests without `securityBoundary` are rejected;
- `codex-cli` provider registration can be accepted while execution remains
  disabled.

This proves static manifest/auth boundary validation. It does not authorize
reading auth files, changing auth configuration, performing connector auth
flows, executing remote agents, or calling providers.

### File Provider Manifest Store

Historical file-backed manifest store evidence confirms temp-backed local
persistence behavior for:

- provider metadata persistence across store instances;
- duplicate rejection and delete persistence;
- mutation refusal while another lock is present;
- fresh-lock preservation during stale cleanup;
- live-process stale-looking lock preservation.

This proves narrow temp-backed persistence behavior only. It does not authorize
modifying the active provider registry, active runtime config, auth state, or
current workspace provider metadata.

## host_dispatcher_boundary_map

Historical host dispatcher evidence confirms local behavior for:

- blocking `codex-cli` routing without a verified runner result;
- allowing `codex-cli` routing with a ready runner result;
- building a `codex-cli` plan only from a verified runner result;
- preserving ready desktop routing;
- creating a read-only provider permit with fake in-memory execution;
- dry-running read-only provider dispatch without spawn;
- rejecting workspace-write provider dispatch before spawn;
- rejecting invalid provider plans before permit issuance.

Provider execution runner controlled read-only evidence further confirms:

- dispatching ready read-only runner results through provider permits;
- validating provider registry selection before read-only runner dispatch;
- requiring registry and metadata before formal read-only dispatch spawn;
- executing formal read-only dispatch only through a guarded fake spawner;
- dry-running read-only runner provider dispatch without spawn.

This proves the host dispatcher can be constrained around verified runner
results, registry selection, metadata gates, permits, dry-run mode, and guarded
fake-spawner behavior. It does not authorize live host startup, real route
execution, real process spawn, provider calls, workspace-write dispatch, remote
execution, or provider-backed runtime work.

## provider_execution_separation

AGENTS OS should keep these separations explicit:

```text
provider_registry_static_catalog != provider_execution
provider_selection_result != provider_call
provider_grant_or_permit != external invocation
host_dispatcher_plan != host_dispatcher_route_execution
dry_run_preview != real spawn
guarded_fake_spawner != production spawner
read_only_runner_result != full provider execution
file_manifest_store_test != active provider registry mutation
remote_auth_manifest_validation != connector login or remote agent execution
```

The safe current use of this map is governance memory for future gate design.
It is not an execution bridge.

## forbidden_auth_provider_execution_guard

Current guard values:

```text
auth_token_cookie_session_read_authorized=false
auth_token_cookie_session_write_authorized=false
provider_registry_write_authorized=false
provider_runtime_config_write_authorized=false
provider_call_authorized=false
provider_execution_authorized=false
remote_agent_execution_authorized=false
host_dispatcher_execution_authorized=false
live_host_start_authorized=false
real_process_spawn_authorized=false
workspace_write_dispatch_authorized=false
service_start_authorized=false
executor_run_authorized=false
external_write_authorized=false
formal_memory_write_authorized=false
```

Any future task that changes one of these values must be a separate gate with
explicit scope, exact inputs, exact commands, expected outputs, rollback policy,
and reviewable evidence.

## future_provider_execution_gate_sequence

Recommended future sequence:

1. `provider-execution-design-gate`: define allowed provider execution classes,
   denied classes, auth boundary, runtime config boundary, evidence shape, and
   rollback rules. No execution.
2. `provider-registry-active-config-review`: inspect only safe metadata and
   active config shape, without reading secret values or modifying config.
3. `provider-execution-preview-gate`: create a local preview from a provider
   plan with `execution_authorized=false` and `provider_call_authorized=false`.
4. `host-dispatcher-fake-spawn-gate`: run only fake-spawner or dry-run tests
   proving fail-closed behavior in the current tree.
5. `provider-readonly-local-dry-run-gate`: if Jenn chooses, run an exact local
   read-only dry-run with no provider call, no auth mutation, no service start,
   no workspace-write, and no external write.
6. `connector-auth-smoke-preflight`: proposal-only unless Jenn grants a narrow
   connector/auth smoke boundary; must not expose tokens, cookies, headers, or
   provider raw responses.
7. `real-provider-execution-red-gate`: explicit Jenn authorization only; must
   define provider, command, auth handling, cost/network boundary, outputs,
   rollback, evidence, and abort criteria.

## receipt_review_pattern

Every future provider/host gate should leave:

- a report or plan describing the exact boundary and source facts;
- a receipt recording commands, outputs in summary form, and denied authority;
- a review confirming the evidence did not expand permissions;
- registry updates only when needed to keep `docctl doctor` clean;
- `docctl status` and `docctl doctor` validation.

## Decision

The Provider / Host Dispatcher Static Behavior Map is accepted as a local
governance map.

It closes the current queue item by preserving historical provider/host
knowledge without carrying forward runtime, provider, host, connector, service,
executor, Memory, or external-write authorization.

The next active route is `Root Private History Review Or History-Scrub Gate`,
because external Git publication remains blocked until root private history risk
is reviewed or a history-scrub path is chosen.
