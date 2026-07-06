# AGENTS OS VCPToolBox startup preflight gate Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-03
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact boundary for a future VCPToolBox startup preflight gate.

This package does not authorize starting VCPToolBox, installing dependencies,
creating active runtime configuration, running plugins, calling providers, or
writing Memory. It only defines the future preflight gate that must pass before
any later startup discussion can be considered.

## Current Facts

VCPToolBox source is present as a local upstream-trackable runtime core checkout:

```text
path=runtime/VCPToolBox
repo=https://github.com/lioensky/VCPToolBox
branch=main
head=49e72d92d29e48184b6a7e73098131cc416b53db
```

The no-run inventory audit is complete:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-runtime-source-inventory-no-run-audit-v0.1.md
plugin_manifest_count=83
enabled_plugin_count=63
blocked_plugin_count=20
plugin_active_config_env_count=0
route_verb_counts=DELETE:9,GET:84,PATCH:2,POST:75,PUT:5
docctl status PASS score=100
```

VCPToolBox startup is not currently ready:

```text
runtime_start_ready=False
config_gate_required=True
dependency_gate_required=True
plugin_gate_required=True
provider_gate_required=True
memory_gate_required=True
```

## Gate Purpose

The future startup preflight gate should answer, without starting the runtime:

```text
Is the source checkout present and clean?
Are startup entrypoints identified?
Are active config files absent or explicitly authorized?
Are dependency/install/build requirements known but not executed?
Are enabled plugins and high-risk plugin classes summarized?
Are route/write/network/provider surfaces summarized?
Are ports and working directory explicit for any future startup?
Are stop conditions and evidence paths clear?
```

The gate is not a startup command. Passing the gate must not start VCPToolBox
and must not authorize startup by implication.

## Allowed Future Inputs

A future preflight gate may read only source and metadata needed for summary:

```text
runtime/VCPToolBox/AGENTS.md
runtime/VCPToolBox/Plugin/AGENTS.md
runtime/VCPToolBox/modules/AGENTS.md
runtime/VCPToolBox/routes/AGENTS.md
runtime/VCPToolBox/rust-vexus-lite/AGENTS.md
runtime/VCPToolBox/package.json
runtime/VCPToolBox/AdminPanel-Vue/package.json
runtime/VCPToolBox/rust-vexus-lite/package.json
runtime/VCPToolBox/server.js
runtime/VCPToolBox/adminServer.js
runtime/VCPToolBox/Plugin.js
runtime/VCPToolBox/routes/**/*.js
runtime/VCPToolBox/Plugin/**/plugin-manifest.json
runtime/VCPToolBox/Plugin/**/plugin-manifest.json.block
runtime/VCPToolBox/*.example
runtime/VCPToolBox/Plugin/**/config.env.example
git metadata for runtime/VCPToolBox
docctl status / doctor summaries
```

The gate may read template keys and filenames. It must not read or output active
secret/config values.

## Required Checks

A future preflight gate must check:

```text
runtime/VCPToolBox exists
runtime/VCPToolBox git checkout is clean
runtime/VCPToolBox remote matches https://github.com/lioensky/VCPToolBox
startup entrypoints are present
package scripts are summarized but not executed
active .env files are absent unless separately authorized
active config.env files are absent unless separately authorized
credential/token/cookie/key-material paths are absent from worktree
plugin manifests parse successfully
enabled/blocked plugin counts are summarized
high-risk plugin classes are flagged
admin/server route surfaces are summarized
runtime write surfaces are summarized
external HTTP/provider-capable surfaces are summarized
docctl status is PASS
docctl doctor is PASS
```

The output must be summary-only.

## Required Output Shape

A future preflight gate output must include:

```text
schema_version
passed
gate_status
read_only=true
summary_only=true
startup_authorized=false
service_start_authorized=false
admin_service_start_authorized=false
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_execution_authorized=false
provider_call_authorized=false
memory_write_authorized=false
runtime_config_write_authorized=false
external_write_authorized=false
source_checkout_present
source_git_status_clean
active_env_count
active_config_env_count
credential_file_count
key_material_count
package_script_summary
entrypoint_summary
plugin_manifest_summary
route_surface_summary
write_surface_summary
provider_surface_summary
docctl_status_summary
stop_conditions
next_required_confirmation
```

The output must not include secret values, token values, cookie values, active
config content, private Memory, provider raw responses, raw logs, or full source
file bodies.

## Forbidden Behavior

The future preflight gate must not:

```text
start VCPToolBox service
run server.js
run adminServer.js
run Plugin.js
execute routes/modules
execute plugin entrypoints
execute package scripts
install dependencies
run npm/yarn/pnpm install
run pip install
run Rust/N-API build
run tests that may execute runtime/provider behavior
create or modify .env / .env.* files
create or modify active config.env files
modify provider/runtime configuration
modify auth/token/cookie/session state
read or output secrets/token/cookie/private Memory/provider raw response/log raw content
read state-private/
write formal AGENTS OS Memory
modify WORKSPACE_REGISTRY.yaml
commit / push / tag
deploy / release / publish
perform bulk move / delete / rename / overwrite
write external systems
```

If any forbidden behavior is required, stop and prepare a new confirmation
package.

## High-Risk Startup Areas

The future gate must treat these as startup blockers unless separately approved:

```text
runtime/VCPToolBox/server.js
runtime/VCPToolBox/adminServer.js
runtime/VCPToolBox/Plugin.js
runtime/VCPToolBox/routes/admin/pluginStore.js
runtime/VCPToolBox/routes/admin/config.js
runtime/VCPToolBox/routes/admin/plugins.js
runtime/VCPToolBox/Plugin/LinuxShellExecutor/
runtime/VCPToolBox/Plugin/PowerShellExecutor/
runtime/VCPToolBox/Plugin/SSHManagerService/
runtime/VCPToolBox/Plugin/LinuxLogMonitor/
runtime/VCPToolBox/Plugin/LinuxLogMonitorServer/
runtime/VCPToolBox/Plugin/ChromeBridge/
provider-capable image/video/search/browser bridge plugins
```

The exact gate may refine this list by manifest and route summary, but it must
not downgrade these classes without Jenn confirmation.

## Future Allowed Write Classes

The future preflight execution, if separately confirmed, may write only:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-startup-preflight-gate-v0.1.md
control-plane/registry/receipts/2026-07-03-yellow-agents-os-vcptoolbox-startup-preflight-gate-v0.1.md
control-plane/registry/reviews/2026-07-03-yellow-agents-os-vcptoolbox-startup-preflight-gate-v0.1.review.md
Document Registry metadata required to keep docctl doctor clean
Federated Document Registry expected count update required to keep docctl doctor clean
```

It must not modify VCPToolBox source, runtime config, active config files,
auth/token/cookie/session files, state-private, formal Memory, or
`WORKSPACE_REGISTRY.yaml`.

## Failure Handling

If the future preflight fails:

```text
do not start VCPToolBox
do not install dependencies
do not create active config
do not run plugins
do not call providers
do not write Memory
do not broaden scope automatically
write only the confirmed preflight evidence
report failed checks by summary and rule id
prepare a revised confirmation package if scope changes
```

## Exact Confirmation Text

Jenn may authorize the future preflight with:

```text
确认执行 AGENTS OS VCPToolBox startup preflight gate v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内执行一次只读 VCPToolBox startup preflight gate，
只允许读取 runtime/VCPToolBox 的 source metadata、package script metadata、入口文件结构、
配置模板键名、插件 manifest 摘要、route/write/network/provider surface 摘要、git metadata、
docctl status 和 docctl doctor。

允许写入：
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-startup-preflight-gate-v0.1.md
- control-plane/registry/receipts/2026-07-03-yellow-agents-os-vcptoolbox-startup-preflight-gate-v0.1.md
- control-plane/registry/reviews/2026-07-03-yellow-agents-os-vcptoolbox-startup-preflight-gate-v0.1.review.md
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

preflight gate 必须保持 startup_authorized=false、service_start_authorized=false、
admin_service_start_authorized=false、dependency_install_authorized=false、
build_authorized=false、test_execution_authorized=false、
plugin_execution_authorized=false、provider_call_authorized=false、
memory_write_authorized=false、runtime_config_write_authorized=false、
external_write_authorized=false。

不启动 VCPToolBox 服务，不运行 server.js/adminServer.js/Plugin.js，不执行 routes/modules，
不运行插件入口，不安装依赖，不执行 npm/yarn/pnpm/pip/cargo/napi 命令，不执行 build/test，
不做 provider call，不改 auth/token/cookie/session，不改 provider/runtime 配置，
不创建或修改 .env/.env.*、config.env、credentials、tokens、cookies，不读取或输出
secrets/token/cookie/private memory/provider raw response/log raw content，不读 state-private/，
不写正式 AGENTS OS Memory，不修改 WORKSPACE_REGISTRY.yaml，不做外部写入，
不 commit/push/tag/deploy/publish，不做 bulk move/delete/rename/overwrite。
```

## Validation For This Package

```text
validate-document-registry PASS documents=155 pass=155 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=197 scanned_files=244 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_clean=True
service_started=false
runtime_entrypoint_executed=false
plugin_entrypoint_executed=false
dependency_install_performed=false
provider_call_performed=false
active_config_created=false
```
