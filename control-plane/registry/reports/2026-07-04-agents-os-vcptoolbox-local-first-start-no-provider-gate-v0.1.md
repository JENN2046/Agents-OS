# AGENTS OS VCPToolBox local first-start no-provider gate v0.1

Date: 2026-07-04
Status: completed_with_warning
Lane: Yellow Work Batch
Scope: localhost-only first-start observation without provider call or plugin activation.

## Boundary

This gate did not start VCPToolBox main `server.js` because direct main startup
would call plugin load, service initialization, static plugin initialization,
and Python plugin prewarm paths.

This gate did not run `Plugin.js`, plugin entrypoints, tests, provider calls,
external HTTP checks, or real executor paths.

This gate did not create or modify `.env`, `.env.*`, plugin `config.env`,
credentials, tokens, cookies, provider/runtime configuration, formal AGENTS OS
Memory, `WORKSPACE_REGISTRY.yaml`, or `state-private/`.

This gate did not read or output config values, secrets, tokens, cookies,
private Memory content, provider raw responses, or raw logs.

## Startup Target

Main service startup status:

```text
main_server_start_attempted=false
main_server_block_reason=server.js initializes plugin load/services/static/prewarm paths during startup
plugin_activation_prevented=true
provider_call_prevented=true
```

Admin service startup observation:

```text
admin_server_start_attempted=true
admin_server_started=true
admin_server_stopped=true
admin_server_host=127.0.0.1
admin_server_port=18741
main_port_dummy=18740
```

The admin process was launched from a workspace-local cache directory with
dummy environment values and a one-shot localhost listen wrapper. The wrapper
kept a port-only listen call bound to `127.0.0.1`.

The admin process uses a mock plugin manager for admin reload hooks; no real
plugin activation was performed in this gate.

## Local Checks

Only local HTTP checks against `127.0.0.1` were performed:

```text
GET /AdminPanel/login.html status=200 content_type=text/html
GET /AdminPanel/ status=200 content_type=text/html
GET /admin_api/check-auth status=401 content_type=application/json
```

Process and port cleanup:

```text
localhost_listener_observed=true
listener_address=127.0.0.1:18741
process_stopped=true
post_stop_listener_present=false
post_stop_admin_process_present=false
```

## Warning

The admin process reached listening state, but one admin module failed to load
because the `better-sqlite3` native binding was unavailable. This is consistent
with the current dependency policy: dependency installs were run with
`--ignore-scripts`, so native addon postinstall/build hooks were not executed.

Observed impact:

```text
better_sqlite3_native_binding_available=false
emojis_admin_module_loaded=false
admin_server_listening_despite_warning=true
```

## Result

```text
local_first_start_no_provider_gate=completed_with_warning
localhost_only=true
service_started=true
service_stopped=true
main_server_started=false
admin_server_started=true
plugin_activation_performed=false
provider_call_performed=false
external_http_performed=false
config_secret_read_or_output=false
runtime_source_modified=false
formal_memory_write_performed=false
```

## Remaining Work

Two safe next routes are available:

```text
native_addon_build_batch=build the missing better-sqlite3 binding under a bounded dependency/native-addon gate
main_no_plugin_start_gate=add or use a no-plugin/no-provider startup flag or shim before main server first-start
```

The next main-service first-start should not run direct `server.js` until the
plugin activation path is explicitly disabled or gated.

## Validation

```text
validation_status=passed
validate-document-registry=PASS documents=199 pass=199 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_doctor=PASS registries=3 documents=241 scanned_files=288 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl_status=PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_source_changes=false
post_stop_listener_present=false
post_stop_admin_process_present=false
```
