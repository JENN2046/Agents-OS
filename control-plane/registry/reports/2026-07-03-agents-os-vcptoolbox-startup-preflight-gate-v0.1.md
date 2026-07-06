# AGENTS OS VCPToolBox startup preflight gate v0.1

Date: 2026-07-03
Status: passed_no_run
Scope: read-only startup preflight gate for VCPToolBox source checkout.

## Gate Result

```text
schema_version=agents-os.vcptoolbox.startup_preflight.result.v0.1
passed=true
gate_status=passed_no_run
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
```

This gate passing means the source is inspectable and the next gates are clear.
It does not mean VCPToolBox is ready to start.

## Source Checkout

```text
source_checkout_present=true
source_remote=https://github.com/lioensky/VCPToolBox
source_branch=main
source_head=49e72d92d29e48184b6a7e73098131cc416b53db
source_git_status_clean=true
worktree_file_count=2821
```

Required startup entrypoints are present:

```text
server.js_exists=true
adminServer.js_exists=true
Plugin.js_exists=true
WebSocketServer.js_exists=true
FileFetcherServer.js_exists=true
KnowledgeBaseManager.js_exists=true
package.json_exists=true
config.env.example_exists=true
```

## Config Boundary

```text
active_env_count=0
active_config_env_count=0
credential_file_count=0
key_material_count=0
root_config_template_key_count=173
tag_processor_config_template_key_count=7
plugin_active_config_env_count=0
plugin_config_env_example_count=41
```

Future startup still requires a separate active configuration gate before any
`.env`, `config.env`, credentials, tokens, cookies, or provider/runtime config
files are created or modified.

## Package Script Surface

No script was executed. Script names only:

```text
runtime/VCPToolBox/package.json scripts=test,start,start:admin,start:all,build:admin
runtime/VCPToolBox/AdminPanel-Vue/package.json scripts=dev,build,build:no-type-check,preview,test,test:watch,lint,lint:typography,lint:fix
runtime/VCPToolBox/rust-vexus-lite/package.json scripts=build,build:debug,artifacts
```

Future startup still requires a dependency/build gate before any
`npm`, `yarn`, `pnpm`, `pip`, `cargo`, or `napi` command is run.

## Plugin Surface

```text
plugin_manifest_count=83
plugin_manifest_parse_errors=0
state_counts=blocked:20,enabled:63
plugin_type_counts=asynchronous:2,hybridservice:17,messagePreprocessor:4,service:6,static:13,synchronous:41
communication_counts=direct:27,process_stdio:1,stdio:54,unknown:1
entry_type_counts=command:1,executable:2,nodejs:53,python:4,unknown:23
```

High-risk plugin classes observed:

```text
LinuxShellExecutor enabled hybridservice direct nodejs
ServerPowerShellExecutor enabled synchronous stdio nodejs
SSHManagerService blocked service direct nodejs
LinuxLogMonitor blocked hybridservice direct nodejs
LinuxLogMonitorServer blocked service direct nodejs
ChromeBridge enabled hybridservice direct unknown
PluginManager enabled hybridservice direct nodejs
VCPBridgeServer enabled service direct unknown
VCPToolBridge enabled hybridservice direct unknown
TavilySearch enabled synchronous stdio nodejs
UrlFetch enabled synchronous stdio nodejs
GPTImageGen enabled synchronous stdio nodejs
GeminiImageGen enabled synchronous stdio nodejs
FluxGen enabled synchronous stdio nodejs
QwenImageGen enabled synchronous stdio nodejs
NanoBananaGen2 enabled synchronous stdio nodejs
ZImageTurboGen enabled synchronous stdio nodejs
AgnesVideoGen enabled asynchronous stdio nodejs
```

Future startup still requires a plugin gate. Initial startup should not enable
shell/system executor, plugin-store install, SSH/log monitor, browser bridge,
or provider-heavy image/video/search plugins without separate confirmation.

## Route, Write, And Provider Surface

```text
route_verb_counts=DELETE:9,GET:84,PATCH:2,POST:75,PUT:5
route_files_with_handlers=33
admin_route_modules=29
public_route_modules=4
surface_scan_line_count=139
surface_files_with_hits=27
surface_counts=writeFile:43,appendFile:2,unlink:12,rm(:11,rename:8,mkdir:36,createWriteStream:1,process.exit:10,spawn(:1,exec(:3,http.request:4,fetch(:8
```

High-hit files:

```text
runtime/VCPToolBox/server.js hits=19
runtime/VCPToolBox/routes/admin/pluginStore.js hits=18
runtime/VCPToolBox/routes/admin/emojis.js hits=17
runtime/VCPToolBox/routes/forumApi.js hits=9
runtime/VCPToolBox/routes/admin/dream.js hits=8
runtime/VCPToolBox/routes/admin/toolbox.js hits=7
runtime/VCPToolBox/adminServer.js hits=6
runtime/VCPToolBox/routes/admin/plugins.js hits=6
runtime/VCPToolBox/routes/taskScheduler.js hits=6
```

Future startup still requires explicit handling of local write paths, restart
paths, plugin store install paths, and external HTTP/provider-capable paths.

## Stop Conditions

Stop before startup if any of these are true:

```text
active_config_required_without_confirmation=true
dependency_install_required_without_confirmation=true
enabled_high_risk_plugins_not_gated=true
provider_or_external_http_test_requested_without_confirmation=true
runtime_write_paths_not_declared=true
admin_port_or_main_port_unclear=true
secret_handling_flow_unclear=true
```

Current gate conclusion:

```text
runtime_start_ready=false
next_required_confirmation=VCPToolBox active config and dependency preflight gate
```

## Validation

```text
validate-document-registry PASS documents=158 pass=158 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=200 scanned_files=247 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_clean=True
startup_authorized=false
service_start_authorized=false
plugin_execution_authorized=false
provider_call_authorized=false
memory_write_authorized=false
runtime_config_write_authorized=false
```
