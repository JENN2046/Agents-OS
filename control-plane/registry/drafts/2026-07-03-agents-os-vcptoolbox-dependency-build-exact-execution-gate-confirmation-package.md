# AGENTS OS VCPToolBox dependency/build exact execution gate Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-03
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact boundary for a future VCPToolBox dependency/build execution gate.

This package does not authorize dependency installation or build execution. It
defines the future exact gate that must be confirmed before running package
manager, native build, or frontend build commands.

## Current Facts

VCPToolBox source is present as a local upstream-trackable runtime checkout:

```text
path=runtime/VCPToolBox
repo=https://github.com/lioensky/VCPToolBox
branch=main
head=49e72d92d29e48184b6a7e73098131cc416b53db
```

Root active config is present from the prior exact gate:

```text
runtime/VCPToolBox/config.env exists=true
runtime/VCPToolBox/tag-processor-config.env exists=true
active_config_shape=PASS
secret_like_nonblank_total=0
```

Dependency/build planning baseline:

```text
control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-dependency-build-plan-v0.1.md
package_json_count=10
node_lock_file_count=6
requirements_txt_count=6
cargo_toml_count=15
root_lock_exists=true
admin_lock_exists=true
rust_vexus_lock_exists=false
```

`runtime/VCPToolBox/AdminPanel-Vue/dist` already exists and contains tracked
build output:

```text
admin_dist_exists=true
admin_dist_tracked_file_count=309
```

This matters because any future admin build may modify tracked files. That is a
local source/build-output change, not a no-op cache write.

## Gate Purpose

The future dependency/build exact execution gate should answer, before running:

```text
Which exact commands will run?
Which working directory will each command use?
Which package registries may be read?
Which local cache paths may be written?
Which build outputs may be created or modified?
Which tracked paths may change?
Which dependency classes remain excluded?
Which rollback actions are safe and exact?
Which validation commands prove no service/plugin/provider execution occurred?
```

Passing this gate must not imply VCPToolBox startup readiness.

## Proposed Future Execution Scope

The future v0.1 gate may execute only the core runtime/Admin/Rust dependency and
build sequence below.

Allowed command classes:

```text
node/npm/python/cargo/rustc version checks
root npm ci with lifecycle scripts ignored
AdminPanel-Vue npm ci with lifecycle scripts ignored
AdminPanel-Vue npm run build
rust-vexus-lite npm install without package-lock modification and with lifecycle scripts ignored
rust-vexus-lite npm run build with local Cargo cache and target paths
```

Excluded command classes:

```text
pip install
python virtualenv creation
plugin-level package install
plugin-level build scripts
test scripts
runtime start scripts
admin start scripts
preview/dev scripts
plugin entrypoint execution
provider calls
```

Python requirements and plugin-level dependencies remain blocked until plugin
startup posture and Python environment strategy are accepted.

## Exact Future Commands

The future gate must run commands one at a time and stop on first failure.

Preflight commands:

```text
command -v node
command -v npm
command -v python3
command -v cargo
command -v rustc
node --version
npm --version
python3 --version
cargo --version
rustc --version
```

Dependency/build commands:

```text
cd /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox
npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm ci --ignore-scripts --no-audit --fund=false

cd /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/AdminPanel-Vue
npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm ci --ignore-scripts --no-audit --fund=false
npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm run build

cd /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/rust-vexus-lite
npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm install --package-lock=false --ignore-scripts --no-audit --fund=false
npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo CARGO_TARGET_DIR=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/rust-vexus-lite/target npm run build
```

The future gate must not substitute `npm install` for locked packages and must
not remove `--ignore-scripts` from install commands without a new confirmation.

## Expected Future Writes

Allowed ignored/cache writes:

```text
runtime/VCPToolBox/node_modules/
runtime/VCPToolBox/AdminPanel-Vue/node_modules/
runtime/VCPToolBox/rust-vexus-lite/node_modules/
runtime/VCPToolBox/.cache/npm/
runtime/VCPToolBox/.cache/cargo/
runtime/VCPToolBox/rust-vexus-lite/target/
```

Allowed tracked or potentially tracked build-output writes:

```text
runtime/VCPToolBox/AdminPanel-Vue/dist/
```

Potential Rust build output must be summarized after execution. If the future
gate creates unexpected tracked or untracked non-ignored paths outside the
allowed paths, it must stop and report them without cleanup.

## Required Future Output Shape

The future execution report must be summary-only:

```text
schema_version
gate_status
dependency_install_performed
build_performed
commands_attempted_count
commands_succeeded_count
first_failed_command
root_npm_ci_status
admin_npm_ci_status
admin_build_status
rust_npm_install_status
rust_build_status
expected_write_paths
unexpected_tracked_changes_count
unexpected_untracked_changes_count
service_start_authorized=false
service_started=false
plugin_execution_authorized=false
plugin_execution_performed=false
provider_call_authorized=false
provider_call_performed=false
test_execution_authorized=false
test_execution_performed=false
memory_write_authorized=false
external_write_authorized=false
validation_summary
```

The report must not include raw install logs, tokens, credentials, package
registry auth configuration, config values, provider raw responses, private
Memory content, or raw log content.

## Required Future Validation

The future gate must validate:

```text
runtime/VCPToolBox git status before execution
active config shape summary without values
node_modules/cache/build paths summarized by existence/count only
AdminPanel-Vue/dist change summary if changed
no .env/.env.* created
no plugin config.env created
no plugin manifest modified
no service process detected
no provider call performed
no tests executed
docctl status PASS
docctl doctor PASS
document registry validator PASS
federated document registry validator PASS
```

## Required Future Rollback Model

The future gate does not authorize rollback by default.

Any rollback after dependency/build execution must be a separate exact
confirmation because it may delete or overwrite large generated directories or
tracked build outputs.

Rollback candidates that require later confirmation:

```text
runtime/VCPToolBox/node_modules/
runtime/VCPToolBox/AdminPanel-Vue/node_modules/
runtime/VCPToolBox/rust-vexus-lite/node_modules/
runtime/VCPToolBox/.cache/npm/
runtime/VCPToolBox/.cache/cargo/
runtime/VCPToolBox/rust-vexus-lite/target/
runtime/VCPToolBox/AdminPanel-Vue/dist/
```

```text
bulk_delete_authorized_now=false
tracked_build_output_revert_authorized_now=false
```

## Forbidden Behavior

The future dependency/build exact execution gate must not:

```text
create or modify .env / .env.* files
create or modify plugin config.env files
read or print config.env values
modify provider/runtime configuration
modify auth/token/cookie/session state
read or output secrets/token/cookie/private Memory/provider raw response/log raw content
run pip install
create Python virtualenv
install plugin-level package dependencies
run plugin-level build scripts
run tests
run dev/preview/start scripts
start VCPToolBox
run server.js/adminServer.js/Plugin.js
execute plugin entrypoints
modify plugin manifests
call providers
read state-private/
write formal AGENTS OS Memory
modify WORKSPACE_REGISTRY.yaml
commit/push/tag/deploy/publish
perform rollback, cleanup, bulk move/delete/rename/overwrite
```

If any forbidden behavior becomes necessary, stop and prepare a new
confirmation package.

## Exact Confirmation Text

Jenn may authorize the future dependency/build exact execution gate by sending
exactly:

```text
确认执行 AGENTS OS VCPToolBox dependency/build exact execution gate v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内执行一次 VCPToolBox core dependency/build
exact execution gate。

允许读取 runtime/VCPToolBox 的 package metadata、lockfile presence、active config
shape summary without values、git metadata、docctl status 和 docctl doctor
summary。

允许执行以下 exact commands，必须逐条执行并在失败时停止：

1. command -v node
2. command -v npm
3. command -v python3
4. command -v cargo
5. command -v rustc
6. node --version
7. npm --version
8. python3 --version
9. cargo --version
10. rustc --version
11. 在 /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox 执行：
    npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm ci --ignore-scripts --no-audit --fund=false
12. 在 /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/AdminPanel-Vue 执行：
    npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm ci --ignore-scripts --no-audit --fund=false
13. 在 /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/AdminPanel-Vue 执行：
    npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm run build
14. 在 /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/rust-vexus-lite 执行：
    npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm npm install --package-lock=false --ignore-scripts --no-audit --fund=false
15. 在 /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/rust-vexus-lite 执行：
    npm_config_cache=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/npm CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo CARGO_TARGET_DIR=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/rust-vexus-lite/target npm run build

允许写入 expected local dependency/build outputs：
- runtime/VCPToolBox/node_modules/
- runtime/VCPToolBox/AdminPanel-Vue/node_modules/
- runtime/VCPToolBox/rust-vexus-lite/node_modules/
- runtime/VCPToolBox/.cache/npm/
- runtime/VCPToolBox/.cache/cargo/
- runtime/VCPToolBox/rust-vexus-lite/target/
- runtime/VCPToolBox/AdminPanel-Vue/dist/

允许写入：
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-dependency-build-exact-execution-gate-v0.1.md
- control-plane/registry/receipts/2026-07-03-yellow-agents-os-vcptoolbox-dependency-build-exact-execution-gate-v0.1.md
- control-plane/registry/reviews/2026-07-03-yellow-agents-os-vcptoolbox-dependency-build-exact-execution-gate-v0.1.review.md
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

必须保持：
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
rollback_authorized=false

不创建或修改 .env/.env.*、plugin config.env、credentials、tokens、cookies，
不读取或输出 config.env values、secrets/token/cookie/private memory/provider raw
response/log raw content，
不运行 pip install，不创建 Python virtualenv，不安装 plugin-level package
dependencies，不运行 plugin-level build scripts，不 test，
不修改 plugin manifest，不运行插件，不启动 VCPToolBox，不运行
server.js/adminServer.js/Plugin.js，
不做 provider call，不改 auth/token/cookie/session，不改 provider/runtime 配置，
不读 state-private/，不写正式 AGENTS OS Memory，不修改 WORKSPACE_REGISTRY.yaml，
不做 rollback/cleanup/bulk move/delete/rename/overwrite，不 commit/push/tag/deploy/
publish。
```

## Validation For This Package

```text
validation_status=passed
validate-document-registry PASS documents=181 pass=181 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=223 scanned_files=270 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_summary=only_ignored_active_config
dependency_install_performed=false
build_performed=false
test_execution_performed=false
service_started=false
provider_call_performed=false
```
