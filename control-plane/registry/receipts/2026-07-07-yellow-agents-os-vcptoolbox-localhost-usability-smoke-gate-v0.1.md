# Receipt: AGENTS OS VCPToolBox Localhost Usability Smoke Gate v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Risk class: yellow

## Completed

- Started VCPToolBox main `server.js` on localhost only.
- Started VCPToolBox independent `adminServer.js` on localhost only.
- Kept all plugin manifests disabled.
- Used dummy environment values and a temporary cwd.
- Verified unauthenticated main service behavior.
- Verified AdminPanel login page and static entry behavior.
- Verified login verification and authenticated check paths using a temporary
  cookie jar.
- Stopped both processes and confirmed ports were released.

## Result Summary

```text
localhost_usability_smoke=PASS
node_used=v22.23.1
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
plugin_activation_performed=false
provider_call_performed=false
core_file_edit_performed=false
```

## Not Performed

- No provider call.
- No plugin execution.
- No plugin activation.
- No VCPToolBox core file edit.
- No `.env`, `config.env`, credential, token, cookie, auth, provider, or runtime
  configuration modification.
- No active config values, cookie contents, raw logs, secrets, tokens,
  credentials, private memory, or provider raw responses were read or output.
- No `state-private/` read.
- No formal AGENTS OS Memory write.
- No external write, push, tag, release, deploy, publish, history rewrite,
  reset, clean, bulk delete, bulk move, bulk rename, overwrite, or destructive
  cleanup.

## Validation

```text
main_error_log_count=0
admin_error_log_count=0
main_plugin_manifest_log_count=0
admin_plugin_manifest_log_count=0
ports_after_stop=0
control_chain_test=PASS cases=30 failures=0
control_chain_validate=PASS
machine_test=PASS cases=16 failures=0
machine_validate=PASS closed_count=40 actionable=true
dashboard_test=PASS cases=17 failures=0
dashboard_validate=PASS
validate-document-registry=PASS documents=361 pass=361 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_status=PASS documents=403 score=100
docctl_doctor=PASS registries=3 documents=403 scanned_files=424 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
git_diff_check=PASS
strict_secret_scan_hits=0
```

## Result

Accepted. VCPToolBox is locally startable and AdminPanel-login-smoke usable
under the no-plugin/no-provider boundary.
