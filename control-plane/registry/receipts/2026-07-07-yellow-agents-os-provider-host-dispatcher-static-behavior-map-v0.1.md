# Receipt: AGENTS OS Provider / Host Dispatcher Static Behavior Map v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local static map of provider registry and host dispatcher historical evidence

## Completed

- Created `control-plane/registry/reports/2026-07-07-agents-os-provider-host-dispatcher-static-behavior-map-v0.1.md`.
- Mapped historical Phase 10/11 provider registry, host dispatcher, file
  provider manifest store, and controlled read-only runner evidence.
- Preserved evidence as static governance knowledge only.
- Updated the active queue to close the provider/host static map item and move
  `Root Private History Review Or History-Scrub Gate` into `NOW`.
- Updated `CURRENT_STATE.md` for the new stable fact and next route.
- Updated the local document registry and federated expected document count.

## Source Evidence Summary

```text
host_dispatcher_provider_behavior=8 selected pass / 0 fail / 11 skipped
provider_registry_selection_behavior=25 selected pass / 0 fail / 18 skipped
provider_registry_mutation_query_behavior=8 selected pass / 0 fail / 35 skipped
provider_registry_remote_auth_security_behavior=5 selected pass / 0 fail / 38 skipped
file_provider_manifest_store_persistence=5 selected pass / 0 fail / 38 skipped
provider_execution_runner_controlled_readonly=5 selected pass / 0 fail / 16 skipped
```

## Boundary Kept

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

## Not Performed

- No `state-private/` read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  response, active runtime config value, raw log, auth file, or session file read
  or output.
- No service start.
- No executor run.
- No host dispatcher route execution.
- No provider call.
- No provider registry or provider/runtime config mutation.
- No MCP, ColaMeta, live host, provider service, plugin, or VCPToolBox runtime
  activation.
- No external write, push, tag, release, deploy, publish, history rewrite, bulk
  move/delete/rename/overwrite, or formal Memory write.

## Validation

```text
validate-document-registry=PASS documents=280 pass=280 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl status=PASS score=100 eligible_95=True hard_gates=0
docctl doctor=PASS registries=3 documents=322 scanned_files=343 unregistered=0 warn=0 fail=0
machine preview-now=PASS source_item=Root Private History Review Or History-Scrub Gate execution_authorized=false
```

## Result

Accepted as a Yellow local governance update. The map is static evidence only
and does not grant provider execution, host execution, connector, service,
executor, Memory, runtime, or external-write authority.
