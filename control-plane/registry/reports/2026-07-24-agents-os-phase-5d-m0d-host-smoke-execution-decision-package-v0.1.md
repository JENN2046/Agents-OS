# AGENTS OS Phase 5D M0-D Host Smoke Execution Decision Package v0.1

Date: 2026-07-24
Status: PREPARED_FOR_JENN_DECISION — ACTUAL_HOST_SMOKE_NOT_YET_ELIGIBLE
Owner: Jenn
Agent steward: Nobao

## 1. Decision purpose

This package is the current decision surface after the completed Phase 5D
M0-D offline implementation closeout. It does not authorize a Host action by
being created or read. Its purpose is to distinguish the completed offline
preflight from a separately authorized, exact, reversible Host smoke.

## 2. Bound evidence

```yaml
frozen_plan_manifest_sha256: f8c4dc55df8c7110462d1ec117856df275edaf654ab057f083ce1817f7bbb061
frozen_independent_review_sha256: 902a9fd3686cfbe95693e272df329282f3b33d44ebb1285edfc37bc3ebf8b068
frozen_atomic_freeze_decision_sha256: 08da0e6ee8b93e994ef3b259b45d9f81b7e1fa443b947ccadedc8c2436a9ee31
implementation_start_decision_sha256: be265db9a8352d404e00e57f9ae9333567639d5d213bdf566280c8f35282385a
implementation_closeout_receipt_sha256: ba83d70c5b9230c725a2077c10ae547415a7729187a7f08ae3028e24f4b5f2d0
sealed_VCPToolBox_commit: 555b3b538f6eb736e530c2912de678c5941f9985
sealed_VCPToolBox_tree: fd82d403e79f36f749eb7f555b4736eae3eacdff
sealed_Host_commitments: 7/7_STATIC_TUPLE_MATCH
offline_terminal_result: QUARANTINED_HOST_SMOKE_PREFLIGHT_READY
offline_terminal_outcome: NOT_EXECUTED
```

The closed offline harness preserved `plugin-manifest.json.block`, used only
newly created harness-owned temporary roots, and left no retained archive or
quarantine residue. It did not create or inspect a VCPToolBox worktree, deliver
a package, enable or load a plugin, call a Host lifecycle method, or load native
code.

## 3. What the frozen plan permits a future smoke to mean

The frozen Phase 5D plan fixes only this prospective lifecycle shape:

```text
Host discovery
-> initialize
-> exact inert result {"initialized": false}
-> shutdown
-> exact inert result {"shutdown": true}
-> cleanup
```

`processToolCall`, every native/N-API method, all command execution, database
activity, provider activity, private Memory access, sensing, recording, and any
real effect are outside the prospective smoke.

## 4. Why actual Host smoke is not yet decision-eligible

The plan deliberately requires a later **hash-bound Host lifecycle argument
contract**. It does not define the Host discovery selector, the exact lifecycle
argument bytes, the Host API version/binding, or the immutable owner-issued
contract that would make those inputs safe to consume.

The following execution inputs are therefore absent and must fail closed:

```yaml
hash_bound_Host_lifecycle_contract: MISSING
exact_Host_discovery_contract: MISSING
exact_initialize_argument_contract: MISSING
exact_shutdown_argument_contract: MISSING
quarantine_delivery_and_enabled_manifest_contract: MISSING
rollback_and_cleanup_receipt_contract_for_real_Host_run: MISSING
actual_Host_smoke_execution_authorized: false
```

Neither the source hashes nor the offline positive result may substitute for
these missing contracts. Inventing them inside this package would create a
parallel Host authority and violate the frozen Plan.

## 5. Boundaries retained

```yaml
VCPToolBox_worktree_read_write_clone_checkout_or_start: false
archive_delivery_or_installation: false
enabled_manifest_plugin_discovery_or_loading: false
Host_lifecycle_invocation: false
processToolCall_native_addon_or_NAPI: false
runtime_service_database_dependency_provider_or_production_authentication: false
private_Memory_state_private_sensing_recording_or_real_effect: false
Git_push_PR_merge_release_deploy_publish_tag_or_force_push: false
```

## 6. Jenn decision surface

### A. Start the missing Host-lifecycle contract closure only

Exact decision text:

```text
我确认启动一个窄范围的 Phase 5D M0-D Host lifecycle contract closure。
它只可制作并审查 hash-bound Host discovery、initialize、shutdown、quarantine
delivery/cleanup 的精确合同与决策包；不得创建或读取 VCPToolBox worktree，不得 delivery、
enabled manifest、plugin discovery/loading、Host lifecycle、processToolCall、native/N-API、
runtime、database、dependency、provider、production authentication、private Memory、
state-private、sensing、recording 或真实 effect。

该 closure 完成后必须停在 Fresh Full Atomic Independent Review；不得自动授权或执行
Host smoke。
```

Choosing A starts no Host action. It opens only the missing contract-closure
work needed before a future actual-execution decision can be honestly formed.

### B. Do not start

Keep the current state:

```yaml
Phase_5D_status: M0D_OFFLINE_IMPLEMENTATION_COMPLETE_AWAITING_JENN_HOST_SMOKE_EXECUTION_DECISION
actual_Host_smoke_execution_authorized: false
```

### C. Provide a separately accepted Host lifecycle contract

If an exact Host-owned lifecycle contract already exists elsewhere, Jenn may
provide its canonical path, immutable revision and SHA-256 for a new preflight.
No authority is inferred from a name, a source tree, or a conversational
description alone.

## 7. No state transition from this package

This package does not create a decision record, alter the active queue, update
the Registry, or start a worktree. Until Jenn chooses A with the exact text or
supplies a separately accepted contract under C, the active queue remains the
v17.1 Jenn-only stop state.
