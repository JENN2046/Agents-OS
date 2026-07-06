# AGENTS OS VCPToolBox first-start posture plan v0.1

Status: `draft`
Date: 2026-07-03
Owner: Jenn
Agent steward: Nobao
Scope: decide the VCPToolBox first-start posture after source, startup, and tri-gate preflight.

This plan does not authorize active config creation, dependency install, build,
test, plugin manifest changes, plugin execution, service start, provider calls,
Memory writes, or external writes.

## Current Position

The source and no-run control plane are ready for planning, not for startup.

```text
source_git_status_clean=true
startup_preflight_passed=true
tri_gate_preflight_passed=true
runtime_start_ready=false
startup_authorized=false
active_config_write_authorized=false
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
```

## Posture Decision

First-start posture is:

```text
posture=no_start_until_three_followup_plans
main_service_start=blocked
admin_service_start=blocked
dependency_install=blocked
active_config_creation=blocked
plugin_manifest_changes=blocked
provider_calls=blocked
memory_writes=blocked
```

Reason:

```text
active config has secret-bearing fields
dependency/build spans Node, Python, Rust/N-API, Vue, and plugin-level packages
plugin surface includes enabled shell/system, bridge/browser, provider/search/image/video, and direct service plugins
startup initializes managers, service plugins, static plugins, and Python prewarm behavior
```

## Track A: Config Plan

Decision:

```text
next_config_action=prepare_sanitized_active_config_plan
active_config_creation_now=false
secret_value_collection_now=false
```

The next config plan should classify:

```text
required_non_secret_defaults
required_secret_values
optional_secret_values
provider_disabled_defaults
admin_required_values
port_and_localhost_defaults
paths_that_must_remain_inside_runtime_or_explicit_workspace_dirs
```

The config plan must not include values for secrets, tokens, cookies, provider
keys, admin passwords, or private paths.

Expected future artifact:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-active-config-plan-v0.1.md
```

## Track B: Dependency / Build Plan

Decision:

```text
next_dependency_action=prepare_dependency_build_execution_plan
dependency_install_now=false
build_now=false
test_now=false
```

The next dependency plan should separate:

```text
root Node dependencies
AdminPanel Vue dependencies
root Python requirements
plugin Python requirements
Rust/N-API build requirements
plugin-level Node packages
lockfile-present packages
networked installs
native builds
runtime-start scripts
test scripts
```

No dependency command should run until the plan names exact commands, exact
working directories, expected writes, network/cache behavior, and rollback.

Candidate command classes for later review only:

```text
root npm ci/install class
AdminPanel-Vue npm ci/install class
Python requirements install class
rust-vexus-lite napi build class
plugin package install class
```

Expected future artifact:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-dependency-build-plan-v0.1.md
```

## Track C: Plugin Startup Posture Plan

Decision:

```text
next_plugin_action=prepare_plugin_startup_posture_preview
plugin_manifest_changes_now=false
plugin_execution_now=false
```

The next plugin plan should create a preview-only startup posture:

```text
keep_blocked=already blocked plugins remain blocked
block_for_first_startup=enabled high-risk plugins proposed for temporary block
review_before_allow=direct/service/preprocessor plugins requiring manual review
candidate_allow_no_provider=lower-risk plugins that may be candidates only after config/dependency gates
```

The preview must not rename or edit any `plugin-manifest.json` or
`plugin-manifest.json.block` file. Actual plugin state changes require a later
exact confirmation with file-by-file operations and rollback.

Initial high-risk enabled plugins from the tri-gate report:

```text
AgnesGen
AgnesVideoGen
AnySearch
BilibiliFetch
ChromeBridge
ServerCodeSearcher
DailyNoteSearcher
DeepWikiVCP
DynamicToolBridge
FlashDeepSearch
GPTImageGen
GeminiImageGen
ImageServer
ImageProcessor
LinuxShellExecutor
PluginManager
ServerPowerShellExecutor
QwenImageGen
SkillBridge
TavilySearch
UrlFetch
VCPBridgeServer
ServerSearchController
VCPToolBridge
VSearch
Wan2.1VideoGen
WeatherReporter
ZImageTurboGen
```

Expected future artifact:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-plugin-startup-posture-preview-v0.1.md
```

## First Start Not Yet Authorized

First startup remains blocked until all of these exist:

```text
active_config_plan accepted
dependency_build_plan accepted
plugin_startup_posture_preview accepted
exact active config write confirmation, if config is to be written
exact dependency install/build confirmation, if dependencies are to be installed
exact plugin manifest change confirmation, if plugin posture requires changes
exact service start confirmation, if startup is still desired
```

## Recommended Next Step

Prepare one combined no-run planning package:

```text
AGENTS OS VCPToolBox first-start followup planning package v0.1
```

It should authorize only:

```text
active config plan report
dependency/build plan report
plugin startup posture preview report
receipt/review evidence
registry updates to keep docctl clean
```

It must not authorize:

```text
creating active config
installing dependencies
building
testing
changing plugin manifests
running plugins
starting services
calling providers
writing Memory
```

## Exact Confirmation Text

Jenn may authorize the future followup planning package with:

```text
确认执行 AGENTS OS VCPToolBox first-start followup planning package v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内准备 VCPToolBox 首启前的三个只读计划：
active config plan、dependency/build plan、plugin startup posture preview。

允许读取 runtime/VCPToolBox 的 source metadata、config template key names、
package dependency/script metadata、plugin manifest metadata、startup preflight report、
tri-gate preflight report、docctl status 和 docctl doctor。

允许写入：
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-active-config-plan-v0.1.md
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-dependency-build-plan-v0.1.md
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-plugin-startup-posture-preview-v0.1.md
- 对应本地 receipt/review evidence
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

所有计划必须保持 active_config_write_authorized=false、
dependency_install_authorized=false、build_authorized=false、
test_execution_authorized=false、plugin_manifest_write_authorized=false、
plugin_execution_authorized=false、service_start_authorized=false、
provider_call_authorized=false、memory_write_authorized=false、
external_write_authorized=false。

不创建或修改 .env/.env.*、config.env、plugin config.env、credentials、tokens、cookies，
不安装依赖，不执行 npm/yarn/pnpm/pip/cargo/napi 命令，不 build，不 test，
不修改 plugin manifest，不运行插件，不启动 VCPToolBox，不运行 server.js/adminServer.js/Plugin.js，
不做 provider call，不改 auth/token/cookie/session，不改 provider/runtime 配置，
不读取或输出 secrets/token/cookie/private memory/provider raw response/log raw content，
不读 state-private/，不写正式 AGENTS OS Memory，不修改 WORKSPACE_REGISTRY.yaml，
不做外部写入，不 commit/push/tag/deploy/publish，不做 bulk move/delete/rename/overwrite。
```

## Validation

```text
validate-document-registry PASS documents=167 pass=167 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=209 scanned_files=256 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_clean=True
active_config_created=false
dependency_install_performed=false
build_or_test_performed=false
plugin_manifest_modified=false
plugin_execution_performed=false
service_started=false
provider_call_performed=false
```
