# AGENTS OS VCPToolBox Controlled Local-Use Handoff Gate v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Scope: local handoff for VCPToolBox no-plugin/no-provider use after smoke PASS

## Summary

VCPToolBox has reached a usable local recovery point under a deliberately
limited boundary:

```text
runtime=runtime/VCPToolBox
main_service=server.js on 18740
admin_service=adminServer.js on 18741
node_runtime=v22.23.1
enabled_plugin_manifests=0
blocked_plugin_manifests=83
provider_call_authorized=false
plugin_activation_authorized=false
plugin_execution_authorized=false
```

The previous smoke gate proved that main plus AdminPanel can start locally,
authenticate with dummy values, serve the AdminPanel static entry, and stop
cleanly. This handoff does not start VCPToolBox again. It records how to treat
the current runtime state and which branch must be chosen before expanding use.

## Proven Local Shape

The verified local topology is:

```text
main_port=18740
admin_port=18741
main_to_admin_redirect=127.0.0.1:18741/AdminPanel/
admin_login_page=PASS
admin_verify_login=PASS
admin_check_auth=PASS
admin_static_entry=PASS
ports_released_after_stop=PASS
```

The verified boundary is:

```text
plugins_disabled=true
provider_routes_not_called=true
plugin_routes_not_called=true
runtime_config_routes_not_called=true
raw_log_routes_not_called=true
external_http_routes_not_called=true
cookie_contents_not_output=true
active_config_values_not_output=true
core_file_edit_performed=false
```

## Current Runtime Posture

VCPToolBox is not "fully restored". It is locally usable only in this posture:

```text
local_main_plus_admin_startable=true
admin_panel_login_smoke_usable=true
provider_backed_chat_ready=false
plugin_backed_tools_ready=false
real_active_config_readiness_not_proven=true
long_running_operation_not_proven=true
```

The plugin manifest state is intentionally disabled:

```text
enabled_plugin_manifests=0
blocked_plugin_manifests=83
```

Do not re-enable all plugins as a bulk action. Any plugin restore must be a
separate selective restore gate.

## Safe Local-Use Rules

Allowed without expanding scope:

```text
inspect localhost status
inspect root governance evidence
confirm enabled_plugin_manifests=0
confirm ports 18740/18741 are free before a timeboxed smoke
repeat a timeboxed localhost smoke using dummy values
stop both processes after smoke
record receipt/review evidence
```

Still blocked:

```text
provider call
provider-backed chat
plugin activation
plugin execution
bulk plugin restore
active runtime config value output
auth/token/cookie/session modification
cookie content output
raw log output
state-private read
formal Memory write
external write
push/tag/release/deploy/publish
core file edit
```

## Handoff Command Shape

This handoff does not authorize a long-running service. For a future timeboxed
smoke, the safe command shape must keep:

```text
NODE_ENV=production
PORT=18740
AdminUsername=dummy_local_value
AdminPassword=dummy_local_value
API_URL=http://127.0.0.1:18740/mock
API_Key=dummy
Key=dummy
VCP_Key=dummy
DebugMode=False
CHAT_LOG_ENABLED=false
RAGMemoRefresh=false
VCPToolCode=false
ShowVCP=False
DISTRIBUTED_MUSIC_PLAYLIST_SYNC_ENABLED=false
AGENT_DIR_PATH=<temporary-dir>/agents
TVSTXT_DIR_PATH=<temporary-dir>/tvstxt
KNOWLEDGEBASE_ROOT_PATH=<temporary-dir>/knowledge
TDB_KNOWLEDGE_ROOT_PATH=<temporary-dir>/tdb
```

Use the current Node runtime, not `/bin/node`:

```text
node_version_required=v22.23.1
node_module_abi_required=127
```

Start shape for a smoke only:

```text
node server.js
node adminServer.js
```

Stop both processes after the check. Do not leave a service running as an
accidental deployment.

## Next Branches

Jenn has four practical next choices:

```text
A: Keep VCPToolBox in no-plugin/no-provider local utility mode.
B: Prepare an active config real-local-use gate without outputting config values.
C: Prepare a selective plugin restore gate for a named minimal plugin set.
D: Prepare a provider boundary gate for explicit provider-backed use.
```

Default if Jenn does not choose a branch:

```text
default_next=No Active Automatic Construction Item
reason=provider/plugin/config expansion requires a separate explicit branch
```

## Result

```text
controlled_local_use_handoff=PASS
service_started=false
provider_call_performed=false
plugin_activation_performed=false
plugin_execution_performed=false
runtime_config_value_output_performed=false
cookie_content_output_performed=false
core_file_edit_performed=false
external_write_performed=false
```

## Validation

```text
control_chain_test=PASS cases=30 failures=0
control_chain_validate=PASS
machine_test=PASS cases=16 failures=0
machine_validate=PASS closed_count=41 actionable=true next_user_action.status=none
dashboard_test=PASS cases=17 failures=0
dashboard_validate=PASS now=AGENTS OS VCPToolBox next branch decision checkpoint v0.1
validate-document-registry=PASS documents=364 pass=364 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_status=PASS documents=406 score=100
docctl_doctor=PASS registries=3 documents=406 scanned_files=427 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
git_diff_check=PASS
strict_secret_scan_hits=0
```

## Decision

Accepted. VCPToolBox is now locally recoverable and smoke-usable in
plugins-disabled, no-provider mode. Further expansion requires Jenn to pick a
branch because active config use, plugin restore, and provider use each carry
separate risk.
