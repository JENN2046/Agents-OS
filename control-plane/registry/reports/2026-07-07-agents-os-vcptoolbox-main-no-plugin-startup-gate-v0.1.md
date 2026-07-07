# AGENTS OS VCPToolBox Main No-Plugin Startup Gate v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Scope: localhost-only VCPToolBox main startup observation with all plugin manifests disabled

## Summary

Jenn authorized direct plugin disabling. The gate disabled all enabled
`runtime/VCPToolBox/Plugin/*/plugin-manifest.json` files by renaming them to
`plugin-manifest.json.block`, then started main `server.js` under a bounded
localhost-only, no-provider observation.

No VCPToolBox core runtime source file was edited. No active config values or
raw logs were output.

## Runtime State

```text
vcptoolbox_checkout=runtime/VCPToolBox
vcptoolbox_git_dirty_before=true
vcptoolbox_git_dirty_after=true
plugin_manifest_disable_performed=true
enabled_manifest_count_before=63
enabled_manifest_count_after=0
blocked_manifest_count_after=83
core_entrypoint_file_edit_performed=false
provider_runtime_config_modified=false
active_config_values_read_or_output=false
raw_log_output=false
raw_log_retained=false
```

The runtime checkout remains dirty because plugin manifests are now disabled
and because pre-existing generated/runtime files remain present. This batch did
not revert or overwrite those pre-existing runtime files.

## Startup Observation

The first diagnostic attempt intentionally used a clean environment. It exposed
that `env -i` resolved `node` to `/bin/node v18.19.1`, while the installed
`better-sqlite3` native addon was built for Node ABI 127. The accepted
observation therefore used the current Node binary:

```text
node_used=v22.23.1
node_module_abi=127
wrong_node_version_probe=detected_and_corrected
```

Main `server.js` was then launched from a temporary cwd with dummy environment
values. The local runtime `config.env` was not used as the source of values.

```text
main_server_start_attempted=true
main_server_listened=true
process_alive_after_local_probes=true
post_stop_listener_present=false
enabled_manifest_count=0
blocked_manifest_count=83
loaded_manifest_log_count=0
error_log_count=0
```

Only localhost HTTP checks were performed:

```text
GET / status=401
GET /AdminPanel/ status=302
GET /admin_api/check-auth status=401
```

The `401` and `302` results are expected for an unauthenticated localhost
probe. They prove the main server accepted local requests without requiring
provider or plugin activation.

## Result

```text
main_no_plugin_startup_gate=PASS
main_service_localhost_observation=PASS
plugin_manifests_enabled=0
plugin_activation_performed=false
plugin_execution_performed=false
provider_call_performed=false
external_http_performed=false
formal_memory_write_performed=false
core_file_edit_performed=false
runtime_config_value_output_performed=false
next_gate=AGENTS OS VCPToolBox localhost usability smoke gate v0.1
```

## Boundary

```text
localhost_only=true
service_start_scope=main_server_timeboxed_observation
plugin_manifest_disable_authorized=true
plugin_activation_authorized=false
plugin_execution_authorized=false
provider_call_authorized=false
external_write_authorized=false
runtime_config_write_authorized=false
runtime_config_value_output_authorized=false
secret_raw_read_authorized=false
state_private_read_authorized=false
formal_memory_write_authorized=false
git_push_authorized=false
tag_release_deploy_publish_authorized=false
history_rewrite_authorized=false
core_file_edit_authorized=false
```

## Validation

```text
enabled_manifest_count=0
blocked_manifest_count=83
ports_18740_18741_before=free
ports_18740_18741_after=free
node_version_for_startup=v22.23.1
main_ready=1
root_http_code=401
admin_http_code=302
check_auth_http_code=401
error_log_count=0
```

Governance validation:

```text
control_chain_test=PASS cases=30 failures=0
control_chain_validate=PASS
machine_test=PASS cases=16 failures=0
machine_validate=PASS closed_count=39 actionable=true next_user_action.status=none
dashboard_test=PASS cases=17 failures=0
dashboard_validate=PASS now=AGENTS OS VCPToolBox localhost usability smoke gate v0.1
validate-document-registry=PASS documents=358 pass=358 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_status=PASS documents=400 score=100
docctl_doctor=PASS registries=3 documents=400 scanned_files=421 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
git_diff_check=PASS
strict_secret_scan_hits=0
```

## Decision

Accepted. VCPToolBox main `server.js` can start locally when all plugin
manifests are disabled and the correct Node 22 runtime is used. This does not
prove provider-backed use, plugin-backed use, real user workflow success, or
runtime config readiness.
