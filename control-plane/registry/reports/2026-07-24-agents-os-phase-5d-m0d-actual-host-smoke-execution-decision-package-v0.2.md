# AGENTS OS Phase 5D M0-D Actual Host-Smoke Execution Decision Package v0.2

Date: 2026-07-24
Owner: Jenn
Agent steward: Nobao
Status: `BLOCKED_NOT_EXECUTION_ELIGIBLE`
Terminal outcome: `NOT_EXECUTED`

## 1. Purpose and predecessor preservation

This is the current decision surface for an eventual **actual** quarantined Host
smoke. It is a successor to the immutable historical package below; it does not
edit, reinterpret, or replay that package's already-consumed Section 6 A.

```yaml
immutable_predecessor:
  path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-host-smoke-execution-decision-package-v0.1.md
  sha256: 98a40879d5c66292c107045c83bba335241b1481df2ffc42eb26b2841ff48ca4
  historical_section_6_A_effect: started_the_now_frozen_evidence-shape_contract_closure_only
  eligible_for_replay_as_actual_Host_smoke: false
```

Creation or reading of this v0.2 package does not authorize Host discovery,
loading, initialization, shutdown, cleanup, `processToolCall`, native/N-API,
runtime, database, provider, authentication, private Memory, sensing, or an
effect.

## 2. Bound evidence

```yaml
frozen_lifecycle_contract:
  path: control-plane/registry/drafts/2026-07-24-agents-os-phase-5d-m0d-host-lifecycle-contract-closure-v0.1-r1.md
  sha256: fb31de51e4a65d9d582416eee5bce36715c11f0710c3222614c148498e951f29
frozen_lifecycle_contract_freeze_decision:
  path: control-plane/registry/decisions/2026-07-24-agents-os-phase-5d-m0d-host-lifecycle-contract-closure-r1-atomic-freeze-decision-v0.1.yaml
  sha256: 1d1185bfa10e4bdde8e820386da6971d6e7a3bd44feb245de6c4bb6e389a970f
source_preflight:
  path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-host-smoke-source-preflight-v0.1.md
  sha256: 3a420c5ff995fc28839ba2340d69a23501bf9bd517d77ef552a9217cdfa14a3d
  result: PASS_SOURCE_INTEGRITY_AND_STATIC_API_SHAPE
sealed_Host_source:
  canonical_root: /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox
  commit: 555b3b538f6eb736e530c2912de678c5941f9985
  tree: fd82d403e79f36f749eb7f555b4736eae3eacdff
  frozen_object_tuples: 7/7_MATCH
inert_plugin_source:
  entrypoint_sha256: 51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec
  blocked_manifest_sha256: 25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0
```

## 3. What the source preflight proves

The seven sealed VCPToolBox objects are present at the required commit and the
static `Plugin.js` syntax parses. The source exposes a `PluginManager` whose
relevant methods have these real meanings:

```text
loadPlugins()
  -> scans the Host Plugin/ directory
  -> reads enabled plugin manifests and possible config.env files
  -> requires direct modules
  -> calls their initialize(...)

shutdownAllPlugins()
  -> shuts down the vector manager and all loaded plugin/service modules
  -> cancels scheduled jobs

processToolCall(...)
  -> execution boundary; forbidden
```

The packaged resident entrypoint has inert `initialize()` and `shutdown()`
return values, but it also exports `processToolCall()`, which reaches a native
addon. The latter remains expressly forbidden and cannot be made safe merely by
choosing not to call it.

## 4. Execution admission is currently incomplete

The frozen lifecycle closure requires one immutable, owner-issued contract with
exact `host_discovery`, `initialize`, `shutdown`, and `quarantine_cleanup`
sections. It additionally requires a separate delivery/enabled-manifest
contract, a real cleanup receipt contract, and a current Jenn execution
decision. Those are not present in the frozen inputs.

The following facts therefore fail closed:

```yaml
owner_issued_exact_Host_selector_and_API_binding: MISSING
owner_issued_initialize_argument_bytes: MISSING
owner_issued_shutdown_argument_bytes: MISSING
owner_issued_quarantine_delivery_and_cleanup_contract: MISSING
hermetic_Host_module_and_dependency_inventory: MISSING
clean_quarantine_Host_root_with_only_allowlisted_enabled_payload: MISSING
real_run_cleanup_observation_contract: MISSING
actual_Host_smoke_execution_eligibility: false
```

In particular, calling `loadPlugins()` against either the ordinary Host root or
a generic detached worktree would not be a minimal smoke: it can discover all
enabled manifests, read their configuration, require unsealed modules, and
initialize them. The frozen seven-object tuple does not seal that transitive
runtime surface.

## 5. Determination

```yaml
actual_Host_smoke_execution_authorized_by_this_package: false
Host_operation_count: 0
runtime_usable: false
terminal_outcome: NOT_EXECUTED
reason: BLOCKED_MISSING_HASH_BOUND_OWNER_ISSUED_EXECUTION_CONTRACT_AND_HERMETIC_QUARANTINE_ADAPTER
```

No exact Host call is supplied here because supplying one without the missing
owner-issued inputs would invent a parallel Host authority. This package is a
successful decision-preparation result, not a failed source preflight.

## 6. Jenn decision surface

### A. Start the narrow Host-smoke adapter-binding closure only

Exact decision text:

```text
我确认启动一个窄范围的 Phase 5D M0-D Host-smoke adapter-binding closure。
它只可定义并审查：一个 hermetic、一次性、quarantine Host root；完整的 Host module
与 dependency inventory；唯一 allowlisted inert payload；transient enabled-manifest 的
精确字节；Host discovery、initialize、shutdown 的精确 selector、参数与预期结果；以及
真实 owned-root cleanup observation/receipt。

不得创建或读取 VCPToolBox worktree，不得 delivery、enabled manifest、plugin discovery/
loading、Host lifecycle、processToolCall、native/N-API、runtime、database、dependency
installation、provider、production authentication、private Memory、state-private、sensing、
recording 或真实 effect。

closure 完成后必须经过 Fresh Full Atomic Independent Review，并停在新的 Jenn-only actual
Host-smoke execution decision；不得自动执行 Host smoke。
```

Choosing A creates no Host worktree and performs no Host action. It only makes
the missing future execution inputs reviewable and hash-bindable.

### B. Do not start

Retain the current state:

```yaml
actual_Host_smoke_execution_authorized: false
terminal_outcome: NOT_EXECUTED
next_gate: JENN_DECISION_ON_ADAPTER_BINDING_CLOSURE_OR_LATER_EXECUTION_PACKAGE
```

## 7. Retained prohibitions

```yaml
original_VCPToolBox_worktree_modification: forbidden
archive_delivery_or_installation: forbidden
plugin_enablement_discovery_loading_or_lifecycle: forbidden
processToolCall_native_addon_NAPI_or_command_execution: forbidden
runtime_service_database_dependency_install_provider_or_production_authentication: forbidden
private_Memory_state_private_sensing_recording_or_real_effect: forbidden
Git_commit_push_PR_merge_release_deploy_publish_tag_or_force_push: forbidden
```
