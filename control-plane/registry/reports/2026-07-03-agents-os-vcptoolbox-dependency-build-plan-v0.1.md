# AGENTS OS VCPToolBox dependency/build plan v0.1

Date: 2026-07-03
Status: completed_no_run
Scope: future dependency and build execution plan for VCPToolBox.

This report is a planning artifact only. It does not install dependencies, run
builds, run tests, run package scripts, start services, or execute plugin
entrypoints.

## Authorization State

```text
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
```

## Inputs Reviewed

```text
source_remote=https://github.com/lioensky/VCPToolBox
source_branch=main
source_head=49e72d92d29e48184b6a7e73098131cc416b53db
source_git_status_clean=true
startup_preflight_gate=passed_no_run
tri_gate_preflight=passed_no_run
first_start_posture=no_start_until_three_followup_plans
```

Only package metadata, script names, dependency counts, lockfile presence, and
requirements/Cargo file presence were reviewed. No install, build, test, service
start, plugin run, provider call, or external write was performed.

## Dependency Surface

Tri-gate baseline:

```text
node_package_count=10
root_node_dependency_count=53
lock_file_count=9
requirements_txt_count=6
cargo_toml_count=15
root_python_requirements_exists=true
rust_vexus_cargo_exists=true
runtime_start_script_count=4
install_or_build_script_count=6
test_script_count=4
```

Followup package metadata:

```text
package_json_count=10
node_lock_file_count=6
requirements_txt_count=6
cargo_toml_count=15
runtime_start_script_count=4
install_or_build_script_count=7
test_script_count=4
other_script_count=10
```

Package script-name inventory:

```text
AdminPanel-Vue/package.json scripts=build,build:no-type-check,dev,lint,lint:fix,lint:typography,preview,test,test:watch deps=12 devDeps=13
Plugin/ComfyUIGen/package.json scripts=none deps=2 devDeps=0
Plugin/DeepWikiVCP/package.json scripts=none deps=0 devDeps=0
Plugin/DoubaoGen/package.json scripts=none deps=0 devDeps=0
Plugin/FluxGen/package.json scripts=build,inspector,prepare,prepublishOnly,watch deps=2 devDeps=2
Plugin/GPTImageGen/package.json scripts=none deps=0 devDeps=0
Plugin/VCPClawMail/package.json scripts=inspect:sdk,install:plugin deps=8 devDeps=0
Plugin/VSearch/package.json scripts=test deps=4 devDeps=0
package.json scripts=build:admin,start,start:admin,start:all,test deps=53 devDeps=0
rust-vexus-lite/package.json scripts=artifacts,build,build:debug deps=0 devDeps=1
```

## Future Execution Route

Future dependency/build work should be split into separate confirmations. This
plan names the route, not authorization to run it.

Stage D0: environment and cache preflight.

```text
goal=confirm tool versions, disk paths, and cache behavior
commands_allowed_now=false
future_commands_to_review=node --version, npm --version, python3 --version, cargo --version
expected_writes=none
```

Stage D1: root Node dependency install.

```text
working_directory=runtime/VCPToolBox
future_command_class=npm ci or npm install, exact command to be confirmed later
expected_writes_if_later_authorized=node_modules and npm cache
lockfile_modification_allowed=false unless explicitly confirmed
current_dependency_install_authorized=false
```

Stage D2: AdminPanel Vue dependency/build path.

```text
working_directory=runtime/VCPToolBox/AdminPanel-Vue
future_install_command_class=npm ci or npm install, exact command to be confirmed later
future_build_command_class=npm run build, exact command to be confirmed later
expected_writes_if_later_authorized=node_modules and build output
current_build_authorized=false
```

Stage D3: Python requirements.

```text
working_directories=root and plugin requirement paths
future_command_class=python environment creation plus pip install, exact paths to be confirmed later
expected_writes_if_later_authorized=local virtual environment and pip cache
current_python_install_authorized=false
```

Stage D4: Rust/N-API build path.

```text
working_directory=runtime/VCPToolBox/rust-vexus-lite
future_command_class=npm script / cargo / napi build, exact command to be confirmed later
expected_writes_if_later_authorized=target artifacts and package artifacts
current_native_build_authorized=false
```

Stage D5: plugin-level packages.

```text
working_directories=plugin package directories only after plugin posture is accepted
future_command_class=plugin-level npm install/build commands, exact command to be confirmed later
provider_plugin_packages_default=blocked
current_plugin_package_install_authorized=false
```

Stage D6: tests.

```text
test_execution_authorized=false
future_test_scope=only tests proven not to start services, call providers, run plugins, or read secrets
provider_call_allowed=false
service_start_allowed=false
```

## Rollback Requirements For Future Execution

Any future install/build confirmation must name rollback rules before execution.

```text
rollback_for_node_modules=explicit path-by-path cleanup confirmation required
rollback_for_build_outputs=explicit path-by-path cleanup confirmation required
rollback_for_virtualenv=explicit path confirmation required
rollback_for_cargo_target=explicit path confirmation required
bulk_delete_authorized_now=false
```

## First-Start Dependency Posture

```text
dependency_install_ready=false
build_ready=false
test_ready=false
first_start_dependency_gate=blocked
next_required_confirmation=dependency/build execution preflight with exact commands and expected writes
```

## Validation

```text
validation_status=passed
validate-document-registry PASS documents=172 pass=172 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=214 scanned_files=261 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_clean=True
active_config_created=false
dependency_install_performed=false
build_or_test_performed=false
plugin_manifest_modified=false
plugin_execution_performed=false
service_started=false
provider_call_performed=false
memory_write_performed=false
external_write_performed=false
```
