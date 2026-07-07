# AGENTS OS VCPToolBox Localhost Usability Smoke Gate v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Scope: localhost-only VCPToolBox main plus AdminPanel usability smoke with plugins disabled

## Summary

The current `NOW` item was executed as a bounded localhost usability smoke.

Both VCPToolBox processes were started with the current Node v22 runtime, dummy
environment values, a temporary cwd, and all plugin manifests disabled. The
smoke checked that the main service, independent AdminPanel service, redirect
path, login verification path, authenticated check path, and AdminPanel static
entry can respond locally.

No provider route, plugin route, runtime config route, raw log route, or
external HTTP route was called.

## Runtime State

```text
vcptoolbox_checkout=runtime/VCPToolBox
node_used=v22.23.1
main_port=18740
admin_port=18741
enabled_manifest_count=0
blocked_manifest_count=83
core_file_edit_performed=false
active_config_values_read_or_output=false
raw_log_output=false
raw_log_retained=false
```

## Localhost Smoke

Both processes listened and stayed alive through the local probes:

```text
main_ready=1
admin_ready=1
main_alive_after_ready=true
admin_alive_after_ready=true
ports_after_stop=0
```

Unauthenticated and authenticated local checks:

```text
main_root_code=401
main_check_auth_unauth=401
main_verify_login_code=200
main_check_auth_authed=200
main_admin_redirect_code=302
main_admin_redirect_location=127.0.0.1:18741/AdminPanel/
admin_login_code=200
admin_root_redirect_code=302
admin_verify_login_code=200
admin_check_auth_authed=200
admin_panel_authed_code=200
admin_index_authed_code=200
```

The cookie jar used for the login check was temporary and deleted. Cookie
contents were not output.

Sanitized log counters:

```text
main_plugin_manifest_log_count=0
admin_plugin_manifest_log_count=0
main_error_log_count=0
admin_error_log_count=0
admin_listen_log_count=1
```

## Result

```text
localhost_usability_smoke=PASS
main_service_localhost=PASS
admin_panel_localhost=PASS
login_verification_path=PASS
authenticated_check_path=PASS
admin_static_entry=PASS
provider_call_performed=false
plugin_execution_performed=false
plugin_activation_performed=false
core_file_edit_performed=false
external_http_performed=false
formal_memory_write_performed=false
```

## Boundary

```text
localhost_only=true
service_start_scope=timeboxed_main_and_admin_smoke
plugins_disabled=true
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
main_ready=1
admin_ready=1
main_verify_login_code=200
admin_verify_login_code=200
main_check_auth_authed=200
admin_check_auth_authed=200
admin_panel_authed_code=200
admin_index_authed_code=200
ports_after_stop=0
main_error_log_count=0
admin_error_log_count=0
```

Governance validation:

```text
control_chain_test=PASS cases=30 failures=0
control_chain_validate=PASS
machine_test=PASS cases=16 failures=0
machine_validate=PASS closed_count=40 actionable=true next_user_action.status=none
dashboard_test=PASS cases=17 failures=0
dashboard_validate=PASS now=AGENTS OS VCPToolBox controlled local-use handoff gate v0.1
validate-document-registry=PASS documents=361 pass=361 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_status=PASS documents=403 score=100
docctl_doctor=PASS registries=3 documents=403 scanned_files=424 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
git_diff_check=PASS
strict_secret_scan_hits=0
```

## Decision

Accepted. VCPToolBox can run locally as a no-plugin/no-provider main plus
AdminPanel pair and can complete a basic authenticated localhost UI smoke.

This still does not prove provider-backed chat, plugin-backed tools, real
runtime config readiness, or long-running operation. The next safe gate is a
controlled local-use handoff that keeps plugins disabled unless Jenn chooses a
selective plugin restore route.
