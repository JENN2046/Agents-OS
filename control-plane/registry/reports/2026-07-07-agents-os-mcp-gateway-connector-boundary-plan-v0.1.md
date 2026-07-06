# AGENTS OS MCP Gateway And Connector Boundary Plan v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local control-plane boundary plan for MCP gateway and connector work before provider/host dispatcher mapping

## Boundary

This plan used only current governance evidence, historical migration evidence,
and local control-plane references.

It did not inspect or modify auth/token/cookie/session files, start MCP or
ColaMeta services, perform live connector calls, perform provider calls, run a
real executor, mutate connector auth, read `state-private/`, read secrets,
read provider raw responses, read raw logs, write formal Memory, write external
systems, push, tag, deploy, release, publish, or perform bulk
move/delete/rename.

## Source Evidence

```text
governance/automation/AGENTS_OS_AUTOMATION_RULEBOOK.md
control-plane/registry/reports/2026-07-06-agents-os-future-plan-intake-and-reality-freeze-v0.1.md
control-plane/registry/reports/2026-07-07-agents-os-migration-plan-distillation-v0.1.md
control-plane/registry/reports/2026-07-07-agents-os-colameta-executor-inventory-readiness-map-v0.1.md
ops/migration/plans/phase-10-local-mcp-runtime-readiness-plan-2026-06-29.md
ops/migration/inventory/phase-10-local-mcp-runtime-readiness-evidence-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-preflight-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-receipt-2026-06-29.md
ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-review-closeout-receipt-2026-06-29.md
control-plane/registry/receipts/2026-07-02-yellow-agents-os-colameta-global-registry-mode-update-confirmation-package.md
```

## MCP Gateway Boundary Summary

The current MCP gateway route is a control-plane boundary, not a runtime grant.

```text
current_gateway_status=planned_boundary_only
historical_local_mcp_runtime_evidence=PASS_WITH_LIMITS
historical_selected_tests=3_pass_0_fail_16_skipped
historical_runtime_mode=in_memory_only
real_mcp_server_acceptance=false
real_provider_execution_acceptance=false
live_connector_acceptance=false
public_mcp_expansion_authorized=false
provider_host_dispatcher_acceptance=false
```

Applicable automation rulebook reading:

```text
MCP-like public shape can be Green only for small additive control-plane contract work.
Multi-file schema/public contract changes are Yellow.
Public MCP expansion is Red.
Execution harness/provider adapter work defaults to dry-run or fake-provider.
Real execution, provider calls, and external runner/executor workspace-write runs are Red.
```

## Connector Auth Boundary

Connector auth is outside this boundary plan.

```text
auth_token_cookie_session_inspected=false
auth_token_cookie_session_modified=false
browser_login_state_modified=false
connector_auth_repair_authorized=false
connector_auth_bypass_authorized=false
live_connector_call_performed=false
connector_external_write_performed=false
```

Known connector state:

```text
previous_colameta_connector_result=token_expired
connector_state_trusted_for_execution=false
connector_state_can_be_used_as_readiness_proof=false
```

The `token_expired` state is a blocker for connector use, not a task to repair
or bypass inside this plan.

## Allowed Readonly Connector Checks

Allowed in this boundary class:

```text
read existing local governance evidence
read local non-secret connector boundary reports
read local MCP/runtime plan/evidence/receipt/review summaries
read local source code references that do not expose auth or provider raw content
summarize previous connector error codes only when no token/header/cookie is printed
run docctl/registry/machine validation
```

Not allowed in this boundary class:

```text
read auth/token/cookie/session/config raw files
print connector headers, cookies, tokens, or raw auth payloads
modify connector auth state
modify browser login state
start an MCP server
start ColaMeta service
call a live connector requiring auth
call a provider
write to an external system
execute host/provider dispatcher behavior
```

## Provider Call Separation

MCP gateway readiness, connector availability, and provider execution are
separate gates.

```text
connector_metadata_check != provider_call
MCP_contract_shape != live_MCP_server_acceptance
in_memory_MCP_runtime_test != real_provider_execution
provider_plan_created != provider_execution_performed
connector_login_success != permission_to_use_provider
provider_registry_static_map != provider_runtime_execution
```

Provider/host dispatcher work may proceed next only as a static behavior map.
It must not read provider credentials, mutate provider/runtime configuration,
call providers, start live hosts, or execute dispatcher routes.

## Future Gate Sequence

```text
1. MCP Gateway And Connector Boundary Plan
   status: this document
   mode: static boundary plan only

2. Provider / Host Dispatcher Static Behavior Map
   mode: static historical/code/evidence map only
   blocked: provider call, auth read/write, live host, dispatcher execution

3. Connector Metadata Smoke Gate
   mode: future exact gate only
   allowed only if it names exact connector tool, exact output redaction, no auth mutation, and no external write

4. MCP Gateway Contract Draft
   mode: schema/contract/control-plane artifact
   public expansion remains Red unless separately authorized

5. Fake-Provider Or Dry-Run MCP Runtime Gate
   mode: local fake-provider/dry-run only
   no live provider, no external write

6. Real Connector Or Provider Gate
   mode: separate Red/P3 gate
   requires exact Jenn authorization, auth boundary, redaction boundary, rollback/evidence, and stop conditions
```

## Blocked Operations

```text
mcp_service_start_authorized=false
connector_live_auth_call_authorized=false
connector_auth_write_authorized=false
provider_call_authorized=false
provider_runtime_config_write_authorized=false
host_dispatcher_execution_authorized=false
external_write_authorized=false
memory_write_authorized=false
formal_memory_write_authorized=false
state_private_read_authorized=false
raw_log_output_authorized=false
provider_raw_response_output_authorized=false
secret_token_cookie_output_authorized=false
```

## Queue Decision

This closes the current `NOW` item as a boundary plan. The next safe queue item
is:

```text
Provider / Host Dispatcher Static Behavior Map
```

Reason:

```text
MCP/connector boundaries are explicit.
Provider calls and live connector work remain blocked.
The next useful step is to preserve historical provider/host dispatcher knowledge as a static map before any runtime gate.
```
