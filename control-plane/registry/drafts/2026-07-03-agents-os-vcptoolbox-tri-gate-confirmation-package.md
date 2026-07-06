# AGENTS OS VCPToolBox tri-gate Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-03
Owner: Jenn
Agent steward: Nobao
Scope: define the next three VCPToolBox gates before any startup attempt.

This package covers:

```text
Gate A: active config gate
Gate B: dependency/build gate
Gate C: plugin-risk gate
```

It does not authorize creating active config, installing dependencies, building,
testing, changing plugin state, starting VCPToolBox, calling providers, or
writing Memory.

## Current Facts

The latest startup preflight gate passed as a no-run gate:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-startup-preflight-gate-v0.1.md
passed=true
gate_status=passed_no_run
runtime_start_ready=false
startup_authorized=false
service_start_authorized=false
dependency_install_authorized=false
plugin_execution_authorized=false
provider_call_authorized=false
runtime_config_write_authorized=false
```

Relevant source facts:

```text
runtime/VCPToolBox source_git_status_clean=True
active_env_count=0
active_config_env_count=0
credential_file_count=0
key_material_count=0
plugin_manifest_count=83
enabled_plugin_count=63
blocked_plugin_count=20
route_verb_counts=DELETE:9,GET:84,PATCH:2,POST:75,PUT:5
```

## Gate A: Active Config Gate

Purpose:

```text
Classify config requirements before any active config is created.
Separate non-secret defaults from secret-bearing fields.
Define where active config may be created later, if Jenn confirms it.
Keep all secret values out of chat, receipts, reviews, logs, and reports.
```

Allowed in the future Gate A preflight:

```text
read config.env.example key names
read tag-processor-config.env.example key names
read plugin config.env.example key names
classify keys as required/optional/secret-like/non-secret
produce a summary-only config plan under control-plane/registry/reports/
write receipt/review evidence
update registries only to keep docctl clean
```

Forbidden in Gate A preflight:

```text
create config.env
create .env or .env.*
create plugin config.env
write credentials, tokens, cookies, API keys, or provider config
read existing private configs or state-private/
print, summarize, copy, or transform secret values
```

Any later active config creation requires a separate exact confirmation and a
secret-safe flow.

## Gate B: Dependency / Build Gate

Purpose:

```text
Classify dependency and build requirements before any install/build command runs.
Separate metadata inspection from networked install or native build.
Define allowed package managers, working directories, lockfile behavior, cache behavior, and rollback expectations.
```

Allowed in the future Gate B preflight:

```text
read package.json script names and dependency names
read package-lock/Cargo metadata if present
summarize install/build commands without executing them
classify commands as local-only, networked, native-build, test, or runtime-start
produce a dependency/build plan under control-plane/registry/reports/
write receipt/review evidence
update registries only to keep docctl clean
```

Forbidden in Gate B preflight:

```text
npm install
yarn install
pnpm install
pip install
cargo build
napi build
npm run build
npm test
vite dev/preview
docker build
docker-compose
package publish
release/deploy
external write
```

Any later install/build requires separate confirmation naming exact commands,
working directories, expected writes, network/cost boundary, and rollback.

## Gate C: Plugin-Risk Gate

Purpose:

```text
Classify enabled plugins before startup.
Define an initial startup-safe plugin posture without changing plugin files yet.
Separate plugin manifest analysis from plugin execution.
```

Allowed in the future Gate C preflight:

```text
read plugin-manifest.json and plugin-manifest.json.block metadata
classify plugins by type, communication protocol, entrypoint type, and risk class
produce startup allowlist/blocklist recommendations as a report
write receipt/review evidence
update registries only to keep docctl clean
```

Forbidden in Gate C preflight:

```text
run plugin entrypoints
rename plugin-manifest.json
rename plugin-manifest.json.block
edit plugin manifests
create plugin config.env
execute shell/system plugins
execute browser bridge plugins
execute provider/search/image/video plugins
install plugins through pluginStore
```

Any later plugin state change requires separate confirmation naming exact
plugin directories, exact manifest rename/edit operations, and rollback.

## Combined Gate Output

A future combined tri-gate preflight must output summary-only fields:

```text
schema_version
passed
gate_status
read_only=true
summary_only=true
active_config_write_authorized=false
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
config_key_summary
dependency_build_summary
plugin_risk_summary
stop_conditions
next_required_confirmation
```

## Stop Conditions

Stop if any future tri-gate preflight finds:

```text
secret value required for progress
active config creation required for progress
dependency install required for progress
native build required for progress
plugin state change required for progress
provider call required for progress
service start required for progress
state-private read required for progress
```

In those cases, write only the allowed evidence and prepare a narrower
confirmation package.

## Exact Confirmation Text

Jenn may authorize the future tri-gate preflight with:

```text
确认执行 AGENTS OS VCPToolBox tri-gate preflight v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内执行一次只读 VCPToolBox active config /
dependency-build / plugin-risk 三门预检。

允许读取 runtime/VCPToolBox 的 source metadata、config templates key names、
package dependency/script metadata、plugin manifest metadata、startup preflight
report、docctl status 和 docctl doctor。

允许写入：
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-tri-gate-preflight-v0.1.md
- control-plane/registry/receipts/2026-07-03-yellow-agents-os-vcptoolbox-tri-gate-preflight-v0.1.md
- control-plane/registry/reviews/2026-07-03-yellow-agents-os-vcptoolbox-tri-gate-preflight-v0.1.review.md
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

tri-gate preflight 必须保持 active_config_write_authorized=false、
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

## Validation For This Package

```text
validate-document-registry PASS documents=161 pass=161 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=203 scanned_files=250 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
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
