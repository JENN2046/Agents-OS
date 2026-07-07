# AGENTS OS VCPToolBox Runtime Integration Contract v0.1

Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Status: accepted
Scope: define VCPToolBox as an AGENTS OS local runtime substrate, not a full product restoration target

## Contract Purpose

VCPToolBox is integrated into AGENTS OS as a local runtime body:

```text
role=local_runtime_substrate
primary_value=tool_layer_and_runtime_body_for_AGENTS_OS
secondary_value=maintainable_and_rollbackable_local_checkout
full_product_restoration_goal=false
provider_backed_operation_goal=false_by_default
plugin_full_restore_goal=false_by_default
```

This contract narrows the VCPToolBox line to two goals:

```text
goal_5=become_AGENTS_OS_tool_layer_runtime_layer
goal_6=remain_maintainable_and_rollbackable
```

All other recovery work is downgraded to supporting health checks or future
branch-specific work.

## Non-Goals

The VCPToolBox line does not currently pursue:

```text
full VCPToolBox product deployment
full plugin ecosystem restore
provider-backed chat restore
external service exposure
production deployment
long-running unattended service
complete upstream feature validation
bulk plugin enablement
active config value extraction
```

Startup, login, dependency, and AdminPanel checks are health checks only. They
are not the final objective.

## Integration Role

Within AGENTS OS, VCPToolBox may serve as:

```text
local_admin_ui_substrate
local_toolbox_surface
future_selective_plugin_host
future_file_or_knowledge_helper_surface
runtime_body_for_AGENTS_OS_experiments
```

It must not become:

```text
ungoverned provider caller
unbounded plugin execution host
external deployment target by accident
source of formal AGENTS OS Memory
authority over AGENTS OS control-plane decisions
```

## Current Contracted State

Current verified local posture:

```text
runtime_path=runtime/VCPToolBox
node_runtime=v22.23.1
main_service=server.js on 18740
admin_service=adminServer.js on 18741
main_plus_admin_smoke=PASS
admin_login_smoke=PASS
enabled_plugin_manifests=0
blocked_plugin_manifests=83
provider_call_performed=false
plugin_execution_performed=false
```

Current permitted reliance:

```text
AGENTS_OS_may_rely_on=source_checkout_presence
AGENTS_OS_may_rely_on=dependency_build_presence
AGENTS_OS_may_rely_on=no_plugin_local_start_shape
AGENTS_OS_may_rely_on=AdminPanel_smoke_shape
AGENTS_OS_may_rely_on=plugin_disabled_safety_posture
```

AGENTS OS must not yet rely on:

```text
provider_chat_success
plugin_tool_success
real_active_config_readiness
long_running_runtime_stability
external_network_integrations
runtime_as_authoritative_memory
```

## Maintenance Boundary

VCPToolBox must remain separated into these categories:

```text
upstream_trackable_source=runtime/VCPToolBox tracked source files
local_runtime_state=generated files, caches, node_modules, build outputs
private_configuration=config.env, .env, credentials, tokens, cookies
governance_evidence=control-plane/registry reports/receipts/reviews
```

Rules:

```text
do_not_commit_runtime_checkout_into_root=true
do_not_output_active_config_values=true
do_not_read_or_output_secrets=true
do_not_treat_runtime_dirty_state_as_root_dirty_state=true
document_every_boundary_expansion=true
```

## Rollback Boundary

Known safe fallback posture:

```text
plugins_disabled=true
enabled_plugin_manifests=0
provider_call_authorized=false
main_plus_admin_smoke_known_pass=true
long_running_service_left_active=false
```

Safe rollback means:

```text
stop VCPToolBox processes
confirm ports 18740 and 18741 are free
keep plugin manifests blocked
avoid provider calls
avoid active config value output
return to governance evidence trail
```

Rollback does not authorize:

```text
git reset --hard
git clean -fd
bulk delete
bulk plugin rename/restore
provider config mutation
auth/token/cookie/session mutation
```

## Future Expansion Gates

Any expansion must be branch-specific:

```text
branch_A=no_provider_local_utility_mode
branch_B=active_config_real_local_use_gate
branch_C=selective_plugin_restore_gate
branch_D=explicit_provider_backed_use_gate
```

Each branch must keep its own:

```text
scope
allowed_reads
allowed_writes
forbidden_routes
validation
receipt
review
rollback
```

Bulk expansion is not allowed:

```text
restore_all_plugins=false
provider_call_by_default=false
long_running_service_by_default=false
external_exposure_by_default=false
```

## AGENTS OS Interface

The current interface is governance-first:

```text
input=AGENTS OS queue decision or Jenn direct request
execution_mode=local bounded gate
evidence=report receipt review
validation=docctl plus relevant local smoke/check
output=contracted runtime posture, not hidden runtime mutation
```

VCPToolBox does not select AGENTS OS tasks. It can only provide local runtime
capability after AGENTS OS chooses and validates a bounded branch.

## Queue Result

The active queue is closed back to a Jenn-owned selection point:

```text
active_now=No_Active_Automatic_Construction_Item
dashboard_route_selection=awaiting_jenn_selection
dashboard_next_user_action=route_choice_required
dashboard_last_completed=vcptoolbox_runtime_integration_contract_v0.1
machine_actionable=false
machine_execution_authorized=false
```

This means the VCPToolBox recovery lane is complete at the contract layer. It
does not grant the next expansion branch.

## Validation

```text
control_chain_tests=PASS cases=30 failures=0
control_chain_validate=PASS
machine_tests=PASS cases=16 failures=0
machine_validate=PASS closed_count=42 actionable=false
dashboard_tests=PASS cases=17 failures=0
dashboard_validate=PASS now=No Active Automatic Construction Item
document_registry=PASS documents=367 pass=367 warn=0 fail=0
federated_document_registry=PASS registries=3 pass=3 warn=0 fail=0
docctl_status=PASS documents=409 unregistered=0 warn=0 fail=0 score=100
docctl_doctor=PASS documents=409 scanned_files=430 unregistered=0 warn=0 fail=0
```

## Decision

Accepted. VCPToolBox is integrated as an AGENTS OS local runtime substrate with
maintenance and rollback discipline. The VCPToolBox line is not pursuing full
deployment, full plugin restoration, or provider-backed operation by default.

Next expansion requires Jenn to choose a branch.
