# AGENTS OS VCPToolBox Rust toolchain setup Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-03
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact boundary for a future workspace-local Rust toolchain setup for VCPToolBox.

This package does not install Rust, run dependency installation, run build
commands, modify the dependency/build plan, start VCPToolBox, or call providers.
It only defines a future explicit setup gate.

## Current Facts

The Rust toolchain availability gate completed:

```text
availability_gate=control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-rust-toolchain-availability-gate-v0.1.md
availability_gate_status=completed_unavailable
rustup_available=false
cargo_available=false
rustc_available=false
dependency_build_resume_ready=false
recommended_next_route=prepare_rust_toolchain_setup_confirmation_package
alternative_route=prepare_node_admin_only_dependency_build_plan_revision
```

The dependency/build exact execution gate remains blocked:

```text
dependency_build_gate=control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-dependency-build-exact-execution-gate-v0.1.md
dependency_build_gate_status=blocked_missing_cargo
first_failed_command=command -v cargo
dependency_install_performed=false
build_performed=false
```

## Source Reference

The future setup route is based on the official Rustup installation guidance:

```text
rustup_book=https://rust-lang.github.io/rustup/installation/other.html
rustup_shell_entrypoint=https://sh.rustup.rs
```

The official Unix method downloads `https://sh.rustup.rs` and runs it through
`sh`. This AGENTS OS setup package narrows that method to workspace-local
`CARGO_HOME` and `RUSTUP_HOME` paths and uses `--no-modify-path`.

## Setup Strategy

Use workspace-local Rust tooling for VCPToolBox:

```text
CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo
RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup
rustup_init_script=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init/rustup-init.sh
profile=minimal
default_toolchain=stable
modify_path=false
```

Reason:

```text
avoid_global_home_toolchain_modification=true
avoid_shell_profile_modification=true
keep_expected_writes_inside_runtime_vcptoolbox_cache=true
keep_followup_build_requires_explicit_local_rust_path=true
```

The prior dependency/build gate cannot simply resume unchanged after this
workspace-local setup, because it checked `command -v cargo` on the ambient
`PATH`. A future dependency/build resume gate must explicitly use:

```text
PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo/bin:$PATH
CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo
RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup
```

## Proposed Future Allowed Commands

The future setup gate may execute only these commands, in order, stopping on
first failure:

```text
mkdir -p /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo
mkdir -p /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup
mkdir -p /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init/rustup-init.sh
chmod 700 /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init/rustup-init.sh
CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup sh /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init/rustup-init.sh -y --no-modify-path --profile minimal --default-toolchain stable
CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo/bin:$PATH rustup --version
CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo/bin:$PATH cargo --version
CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo/bin:$PATH rustc --version
```

No other installer command, package manager command, build command, or test
command is authorized by this package.

## Expected Future Writes

Allowed local writes:

```text
runtime/VCPToolBox/.cache/cargo/
runtime/VCPToolBox/.cache/rustup/
runtime/VCPToolBox/.cache/rustup-init/
```

Expected network reads:

```text
https://sh.rustup.rs
Rust toolchain artifacts fetched by rustup for stable minimal profile
```

The future setup gate must not write:

```text
~/.cargo/
~/.rustup/
~/.profile
~/.bashrc
~/.zshrc
/usr/
/usr/local/
system package database
```

## Required Future Output Shape

The future setup report must include:

```text
schema_version
gate_status
network_download_performed
rustup_init_download_status
rustup_install_status
rustup_available_workspace_local
cargo_available_workspace_local
rustc_available_workspace_local
rustup_version_summary
cargo_version_summary
rustc_version_summary
workspace_local_cargo_home
workspace_local_rustup_home
global_home_toolchain_modified=false
shell_profile_modified=false
system_package_manager_used=false
dependency_install_performed=false
build_performed=false
test_execution_performed=false
plugin_execution_performed=false
service_started=false
provider_call_performed=false
rollback_performed=false
recommended_next_route
```

Recommended next route must be:

```text
prepare_dependency_build_local_rust_resume_gate
```

## Required Future Validation

The future setup gate must validate:

```text
workspace-local rustup binary exists
workspace-local cargo binary exists
workspace-local rustc command works through workspace-local PATH
RUSTUP_HOME is under runtime/VCPToolBox/.cache/rustup
CARGO_HOME is under runtime/VCPToolBox/.cache/cargo
no ~/.cargo write is reported
no ~/.rustup write is reported
no shell profile modification is reported
no dependency install ran
no build ran
no test ran
no service process detected
docctl status PASS
docctl doctor PASS
document registry validator PASS
federated document registry validator PASS
```

## Required Future Rollback Model

The future setup gate does not authorize rollback.

Rollback would require a separate exact confirmation because it would delete a
generated local toolchain tree:

```text
runtime/VCPToolBox/.cache/cargo/
runtime/VCPToolBox/.cache/rustup/
runtime/VCPToolBox/.cache/rustup-init/
```

```text
rollback_authorized=false
bulk_delete_authorized=false
```

## Forbidden Behavior

The future Rust toolchain setup gate must not:

```text
run apt/snap/brew/pacman/dnf/yum
use sudo
write system package database
modify PATH globally
modify shell profiles
write ~/.cargo
write ~/.rustup
install plugin-level dependencies
run npm/yarn/pnpm/pip/cargo/napi dependency or build commands outside the exact setup commands
run VCPToolBox dependency/build
run tests
modify dependency/build plan
create or modify .env/.env.* or plugin config.env
read or output config.env values
read or output secrets/token/cookie/private Memory/provider raw response/log raw content
modify plugin manifests
run plugins
start VCPToolBox
run server.js/adminServer.js/Plugin.js
call providers
read state-private/
write formal AGENTS OS Memory
modify WORKSPACE_REGISTRY.yaml
perform rollback/cleanup/bulk move/delete/rename/overwrite
commit/push/tag/deploy/publish
```

If any forbidden behavior becomes necessary, stop and prepare a new
confirmation package.

## Exact Confirmation Text

Jenn may authorize the future Rust toolchain setup gate by sending exactly:

```text
确认执行 AGENTS OS VCPToolBox Rust toolchain setup v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内执行一次 workspace-local Rust toolchain
setup gate。

允许按顺序执行以下 exact commands，必须在失败时停止：

1. mkdir -p /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo
2. mkdir -p /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup
3. mkdir -p /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init
4. curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init/rustup-init.sh
5. chmod 700 /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init/rustup-init.sh
6. CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup sh /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup-init/rustup-init.sh -y --no-modify-path --profile minimal --default-toolchain stable
7. CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo/bin:$PATH rustup --version
8. CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo/bin:$PATH cargo --version
9. CARGO_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo RUSTUP_HOME=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/rustup PATH=/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox/.cache/cargo/bin:$PATH rustc --version

允许 network read/download：
- https://sh.rustup.rs
- Rust toolchain artifacts fetched by rustup for stable minimal profile

允许写入：
- runtime/VCPToolBox/.cache/cargo/
- runtime/VCPToolBox/.cache/rustup/
- runtime/VCPToolBox/.cache/rustup-init/
- control-plane/registry/reports/2026-07-03-agents-os-vcptoolbox-rust-toolchain-setup-v0.1.md
- control-plane/registry/receipts/2026-07-03-yellow-agents-os-vcptoolbox-rust-toolchain-setup-v0.1.md
- control-plane/registry/reviews/2026-07-03-yellow-agents-os-vcptoolbox-rust-toolchain-setup-v0.1.review.md
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

必须保持：
global_home_toolchain_write_authorized=false
shell_profile_write_authorized=false
system_package_manager_authorized=false
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
rollback_authorized=false

不运行 apt/snap/brew/pacman/dnf/yum，不使用 sudo，不写 system package database，
不修改全局 PATH，不修改 shell profile，不写 ~/.cargo，不写 ~/.rustup，
不执行 VCPToolBox dependency/build，不运行 npm/yarn/pnpm/pip/cargo/napi dependency
or build commands outside the exact setup commands，不 test，
不修改 dependency/build plan，不创建或修改 .env/.env.*、plugin config.env、
credentials、tokens、cookies，
不读取或输出 config.env values、secrets/token/cookie/private memory/provider raw
response/log raw content，
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
validate-document-registry=PASS documents=193 pass=193 warn=0 fail=0
validate-federated-document-registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_doctor=PASS registries=3 documents=235 scanned_files=282 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl_status=PASS score=100 eligible_95=True warn=0 fail=0
dependency_or_build_or_toolchain_outputs_created=false
vcptoolbox_git_source_changes=false
active_config_values_read=false
toolchain_install_performed=false
dependency_install_performed=false
build_performed=false
service_started=false
provider_call_performed=false
```
