# AGENTS OS VCPToolBox active config exact write gate Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-03
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact boundary for a future VCPToolBox active config write gate.

This package does not authorize creating or modifying active config. It only
defines the future exact gate that must be explicitly confirmed before
`runtime/VCPToolBox/config.env` or related active config files may be written.

## Current Facts

VCPToolBox source is present as a local upstream-trackable runtime checkout:

```text
path=runtime/VCPToolBox
repo=https://github.com/lioensky/VCPToolBox
branch=main
head=49e72d92d29e48184b6a7e73098131cc416b53db
source_git_status_clean=true
```

The active config plan is complete and no-run:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-active-config-plan-v0.1.md
config.env.example_key_count=173
tag-processor-config.env.example_key_count=7
plugin_config_template_count=41
plugin_config_key_count=331
total_template_key_count=511
active_config_creation_now=false
```

Current active config state from no-run planning:

```text
active_env_count=0
active_config_env_count=0
credential_file_count=0
key_material_count=0
```

## Gate Purpose

The future active config exact write gate should answer, before writing:

```text
Which exact active config files will be created?
Do the target files already exist?
Which template files are the source?
Which key classes are secret-bearing and must remain blank or secret-safe?
Which provider, external, browser bridge, and shell/system features remain disabled?
Which local-only defaults are acceptable?
Which validation commands prove shape without printing values?
Which rollback action removes only files created by this gate?
```

Passing this gate must not imply VCPToolBox startup readiness.

## Proposed Future Write Scope

The future gate may authorize only these active config write targets:

```text
runtime/VCPToolBox/config.env
runtime/VCPToolBox/tag-processor-config.env
```

The future gate may write these governance evidence files:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-active-config-exact-write-gate-v0.1.md
control-plane/registry/receipts/2026-07-03-yellow-agents-os-vcptoolbox-active-config-exact-write-gate-v0.1.md
control-plane/registry/reviews/2026-07-03-yellow-agents-os-vcptoolbox-active-config-exact-write-gate-v0.1.review.md
```

The future gate must stop without writing if either target active config file
already exists, unless Jenn provides a later overwrite-specific confirmation.

## Proposed Future Input Scope

The future gate may read:

```text
runtime/VCPToolBox/config.env.example
runtime/VCPToolBox/tag-processor-config.env.example
runtime/VCPToolBox/package.json
git metadata for runtime/VCPToolBox
docctl status / doctor summaries
```

The future gate may read template keys and template defaults only to materialize
the active files. It must not print full config file bodies, secret values,
token values, cookie values, credentials, provider raw responses, private Memory
content, or raw log content.

Plugin config files are out of scope for this gate:

```text
runtime/VCPToolBox/Plugin/**/config.env
```

Plugin active config requires a later plugin-specific confirmation package.

## Secret-Safe Materialization Rules

The future gate must classify keys by name before writing.

Secret-bearing or secret-adjacent key classes:

```text
API_KEY
*_API_KEY
*_API_Key
*TOKEN*
*COOKIE*
*PASSWORD*
*SECRET*
*CREDENTIAL*
*PRIVATE*
*_GITHUB_TOKEN
*_GITLAB_TOKEN
AdminPassword
Bridge_Access_Token
```

Rules:

```text
secret_values_must_not_be_requested_in_chat=true
secret_values_must_not_be_printed=true
secret_values_must_not_be_written_from_memory=true
secret_values_must_not_be_in_receipt_or_review=true
provider_keys_default_blank=true
cookie_values_default_blank=true
admin_password_default_blank_until_secret_safe_flow=true
```

For non-secret keys, the future gate may use template defaults only when they do
not enable external/provider behavior. If a value would enable external calls,
provider calls, browser bridge behavior, shell/system execution, or remote write
surfaces, it must be disabled or left blank unless a later exact confirmation
authorizes it.

## Required Future Output Shape

The future active config exact write gate report must include summary only:

```text
schema_version
gate_status
write_performed
target_files_created
target_preexisted
template_files_read
keys_seen_count
keys_written_count
secret_like_keys_blank_count
provider_keys_blank_count
local_default_count
disabled_external_feature_count
active_config_write_authorized
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
rollback_required
validation_summary
```

The report must not include full config bodies or values.

## Required Future Validation

The future gate must validate without printing config values:

```text
runtime/VCPToolBox git status is clean before write
target config files do not already exist before write
target config files exist after write
target file permissions are ordinary local file permissions
expected key count is present by key name only
secret-like keys are blank or placeholder-only by count, not by value output
provider/external startup remains disabled by policy summary
VCPToolBox service is not running
no package install/build/test command ran
no plugin entrypoint ran
no provider call occurred
docctl status PASS
docctl doctor PASS
document registry validator PASS
federated document registry validator PASS
```

## Required Future Rollback

Because this gate would create active config, rollback must be exact:

```text
rollback_allowed_only_for_files_created_by_this_gate=true
rollback_targets=runtime/VCPToolBox/config.env,runtime/VCPToolBox/tag-processor-config.env
overwrite_rollback_authorized=false
bulk_delete_authorized=false
```

If either target existed before the gate, rollback must not delete or overwrite
it. Stop and prepare a new Jenn-confirmed plan.

## Forbidden Behavior

The future active config exact write gate must not:

```text
create or modify .env / .env.* files
create or modify plugin config.env files
overwrite existing active config
write secret/token/cookie/provider key values
request secrets in chat
read secrets/token/cookie/private Memory/provider raw response/log raw content
modify provider/runtime code
modify plugin manifests
install dependencies
run npm/yarn/pnpm/pip/cargo/napi commands
build
test
run plugins
start VCPToolBox
run server.js/adminServer.js/Plugin.js
call providers
read state-private/
write formal AGENTS OS Memory
modify WORKSPACE_REGISTRY.yaml
perform external writes
commit/push/tag/deploy/publish
perform bulk move/delete/rename/overwrite
```

If any forbidden behavior becomes necessary, stop and prepare a new
confirmation package.

## Exact Confirmation Text

Jenn may authorize the future active config exact write gate by sending exactly:

```text
确认执行 AGENTS OS VCPToolBox active config exact write gate v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内执行一次 VCPToolBox active config exact
write gate。

允许读取：
- runtime/VCPToolBox/config.env.example
- runtime/VCPToolBox/tag-processor-config.env.example
- runtime/VCPToolBox/package.json
- runtime/VCPToolBox 的 git metadata
- docctl status 和 docctl doctor summary

允许只在目标文件不存在时创建：
- runtime/VCPToolBox/config.env
- runtime/VCPToolBox/tag-processor-config.env

允许写入：
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-active-config-exact-write-gate-v0.1.md
- control-plane/registry/receipts/2026-07-03-yellow-agents-os-vcptoolbox-active-config-exact-write-gate-v0.1.md
- control-plane/registry/reviews/2026-07-03-yellow-agents-os-vcptoolbox-active-config-exact-write-gate-v0.1.review.md
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

active config 写入必须采用 secret-safe materialization：
- secret/token/cookie/password/API key/provider key/admin password 字段不得从聊天、
  Memory、日志或任何未授权来源取值；
- 这些字段只能留空或写入非敏感占位值；
- 不得输出完整 config 内容，不得输出 secret-like 字段值；
- provider/external/browser bridge/shell-system/plugin execution 相关功能保持禁用或空值；
- 如果目标文件已存在，必须停止，不得 overwrite。

必须保持：
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false

不创建或修改 .env/.env.*、plugin config.env、credentials、tokens、cookies，
不安装依赖，不执行 npm/yarn/pnpm/pip/cargo/napi 命令，不 build，不 test，
不修改 plugin manifest，不运行插件，不启动 VCPToolBox，不运行
server.js/adminServer.js/Plugin.js，
不做 provider call，不改 auth/token/cookie/session，不改 provider/runtime 代码，
不读取或输出 secrets/token/cookie/private memory/provider raw response/log raw content，
不读 state-private/，不写正式 AGENTS OS Memory，不修改 WORKSPACE_REGISTRY.yaml，
不做外部写入，不 commit/push/tag/deploy/publish，不做 bulk move/delete/rename/
overwrite。
```

## Validation For This Package

```text
validation_status=passed
validate-document-registry PASS documents=175 pass=175 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=217 scanned_files=264 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_clean=True
active_config_created=false
active_config_modified=false
```
