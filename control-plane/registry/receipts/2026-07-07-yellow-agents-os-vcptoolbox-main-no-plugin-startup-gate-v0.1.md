# Receipt: AGENTS OS VCPToolBox Main No-Plugin Startup Gate v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Risk class: yellow

## Completed

- Disabled all currently enabled VCPToolBox plugin manifests by renaming
  `plugin-manifest.json` to `plugin-manifest.json.block`.
- Confirmed enabled plugin manifests dropped from 63 to 0.
- Confirmed blocked plugin manifests are now 83.
- Diagnosed the clean-environment Node mismatch and used the current Node 22
  binary for the accepted observation.
- Started main `server.js` on localhost only.
- Performed unauthenticated localhost HTTP checks.
- Stopped the process and confirmed ports were released.
- Wrote local governance evidence.

## Result Summary

```text
main_no_plugin_startup_gate=PASS
node_used=v22.23.1
enabled_manifest_count_after=0
blocked_manifest_count_after=83
main_server_listened=true
GET / status=401
GET /AdminPanel/ status=302
GET /admin_api/check-auth status=401
post_stop_listener_present=false
plugin_activation_performed=false
provider_call_performed=false
core_file_edit_performed=false
```

## Not Performed

- No provider call.
- No plugin execution.
- No plugin activation; only Jenn-authorized manifest disabling was performed.
- No VCPToolBox core file edit.
- No `.env`, `config.env`, credential, token, cookie, auth, provider, or runtime
  configuration modification.
- No active config values, raw logs, secrets, tokens, cookies, credentials,
  private memory, or provider raw responses were read or output.
- No `state-private/` read.
- No formal AGENTS OS Memory write.
- No external write, push, tag, release, deploy, publish, history rewrite,
  reset, clean, bulk delete, bulk move, bulk rename, overwrite, or destructive
  cleanup.

## Validation

```text
enabled_manifest_count=0
blocked_manifest_count=83
main_ready=1
root_http_code=401
admin_http_code=302
check_auth_http_code=401
error_log_count=0
ports_after_stop=0
control_chain_test=PASS cases=30 failures=0
control_chain_validate=PASS
machine_test=PASS cases=16 failures=0
machine_validate=PASS closed_count=39 actionable=true
dashboard_test=PASS cases=17 failures=0
dashboard_validate=PASS
validate-document-registry=PASS documents=358 pass=358 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_status=PASS documents=400 score=100
docctl_doctor=PASS registries=3 documents=400 scanned_files=421 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
git_diff_check=PASS
strict_secret_scan_hits=0
```

## Result

Accepted. Main localhost startup is no longer blocked by the earlier plugin
surface, but normal VCPToolBox use is not yet proven.
