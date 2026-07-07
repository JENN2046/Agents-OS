# Review: AGENTS OS VCPToolBox Localhost Usability Smoke Gate v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Risk class: yellow

## Review Result

Accepted.

The smoke gate is valid because it checked the real two-process local topology:
main service on `18740` and AdminPanel on `18741`. It kept plugins disabled,
used dummy environment values, avoided raw logs and active config values, and
did not call provider, plugin, runtime config, or external HTTP routes.

## Evidence Checked

```text
main_ready=1
admin_ready=1
main_verify_login_code=200
admin_verify_login_code=200
main_check_auth_authed=200
admin_check_auth_authed=200
admin_panel_authed_code=200
admin_index_authed_code=200
main_admin_redirect_code=302
main_admin_redirect_location=127.0.0.1:18741/AdminPanel/
ports_after_stop=0
```

## Boundary Review

```text
localhost_only=true
plugins_disabled=true
plugin_activation_performed=false
plugin_execution_performed=false
provider_call_performed=false
external_http_performed=false
active_config_values_output=false
cookie_content_output=false
raw_log_output=false
core_file_edit_performed=false
formal_memory_write_performed=false
external_write_performed=false
```

## Residual Risk

- VCPToolBox is only proven under dummy env and plugins-disabled mode.
- Provider-backed chat and plugin-backed tools remain untested and unauthorized.
- Real active runtime config was not used as a values source.
- Long-running service behavior was not tested.
- The runtime checkout remains dirty because plugin manifests are disabled and
  prior generated/runtime artifacts remain present.

## Validation

```text
control_chain_test=PASS cases=30 failures=0
control_chain_validate=PASS
machine_test=PASS cases=16 failures=0
machine_validate=PASS closed_count=40 actionable=true
dashboard_test=PASS cases=17 failures=0
dashboard_validate=PASS now=AGENTS OS VCPToolBox controlled local-use handoff gate v0.1
validate-document-registry=PASS documents=361 pass=361 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_status=PASS documents=403 score=100
docctl_doctor=PASS registries=3 documents=403 scanned_files=424 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
git_diff_check=PASS
strict_secret_scan_hits=0
```

## Next Gate

```text
next_gate=AGENTS OS VCPToolBox controlled local-use handoff gate v0.1
```

The next gate should package the current safe run shape for Jenn: how to launch
main plus AdminPanel locally, what remains disabled, and which future branch is
needed before provider or selective plugin use.

## Decision

Accepted. VCPToolBox is locally smoke-usable in no-plugin/no-provider mode, but
not yet restored to full provider/plugin operation.
