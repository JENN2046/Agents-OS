# AGENTS OS Phase 5D M0-D Execution-Admission Materialization Preflight Decision Package v0.1

Date: 2026-07-24
Owner: Jenn
Agent steward: Nobao
Status: `READY_FOR_JENN_EXECUTION_ADMISSION_MATERIALIZATION_PREFLIGHT_DECISION`
Terminal outcome: `NOT_EXECUTED`

## 1. Purpose

This package fills the one remaining **non-lifecycle** condition before a later
actual Host-smoke decision can be made: materialize and inspect a newly owned,
one-time quarantine candidate without calling a Host lifecycle method. It is
not an actual Host-smoke execution decision and it does not authorize plugin
discovery, loading, initialization, shutdown, `processToolCall`, native/N-API,
runtime, database, provider or any real effect.

The package may be consumed only by Jenn's current explicit Section 6 A
confirmation. Reading or preparing it does not create a worktree or quarantine
root and does not access VCPToolBox beyond the already-bound source-preflight
facts below.

## 2. Immutable facts consumed

```yaml
frozen_adapter_binding_closure:
  freeze_decision:
    path: control-plane/registry/decisions/2026-07-24-agents-os-phase-5d-m0d-host-smoke-adapter-binding-r2-atomic-freeze-decision-v0.1.yaml
    sha256: ba24dd3a7e13d04fd23fc688f9a5a1d941d50daa352ac7cb6cbf6f26f36eb46c
  manifest:
    path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-host-smoke-adapter-binding-r2-atomic-independent-review-package-v0.1.manifest.yaml
    sha256: 422c97bae3c23db8c18860e3779b3c0b016bb382f1732a134f9757619caefa5f
  independent_review:
    path: control-plane/registry/reviews/2026-07-24-yellow-agents-os-phase-5d-m0d-host-smoke-adapter-binding-r2-full-atomic-independent-review.yaml
    sha256: b406dfa76047d6d580327ae5ccfd36695c3ea53885a1a14da4e742b2ba5f6fc1
    result: PASS_NO_BLOCKER
frozen_lifecycle_closure:
  freeze_decision:
    path: control-plane/registry/decisions/2026-07-24-agents-os-phase-5d-m0d-host-lifecycle-contract-closure-r1-atomic-freeze-decision-v0.1.yaml
    sha256: 1d1185bfa10e4bdde8e820386da6971d6e7a3bd44feb245de6c4bb6e389a970f
sealed_source_preflight:
  path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-host-smoke-source-preflight-v0.1.md
  sha256: 3a420c5ff995fc28839ba2340d69a23501bf9bd517d77ef552a9217cdfa14a3d
  result: PASS_SOURCE_INTEGRITY_AND_STATIC_API_SHAPE
historical_blocked_actual_execution_package:
  path: control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-actual-host-smoke-execution-decision-package-v0.2.md
  sha256: 82d2d2d49e25e652c6b35f853fa7a0767f14290f99dbc20f8819eedc93b15627
  status: BLOCKED_NOT_EXECUTION_ELIGIBLE
sealed_Host:
  canonical_root: /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox
  commit: 555b3b538f6eb736e530c2912de678c5941f9985
  tree: fd82d403e79f36f749eb7f555b4736eae3eacdff
  frozen_object_tuple_count: 7
inert_payload:
  entrypoint_path: extensions/agents-os-resident/index.js
  entrypoint_sha256: 51190bacd5ff8e394731e5a83d72ba99c7a249136c51797f50e847fff7fda6ec
  blocked_manifest_path: extensions/agents-os-resident/plugin-manifest.json.block
  blocked_manifest_sha256: 25a6084a0ecd2500e89075ed2ad502e791d95352b2638540b8c0aa1563ce8cc0
```

## 3. Why this preflight is required

The two frozen closures define the required shape, but correctly refuse to
invent the real owner-issued evidence. The old v0.2 package remains blocked
because the following evidence does not yet exist:

```yaml
new_owned_quarantine_root: MISSING
complete_Host_module_and_dependency_inventory: MISSING
materialized_two-file_inert_payload_digest: MISSING
transient_enabled_manifest_location_and_bytes: MISSING
cleanup_finalizer_and_post_cleanup_residue_observation: MISSING
actual_Host_lifecycle_selector_argument_and_return_evidence: MISSING
```

This package may create the first five items as evidence candidates, but it
must stop before the sixth. Its output can support a later exact Host lifecycle
decision; it cannot be promoted into that decision by itself.

## 4. Exact bounded preflight

If Jenn selects Section 6 A, the run has exactly one allowed materialization
attempt. All paths below are literal, must be absent before the run, and must be
reported without substituting caller-provided paths:

```yaml
run_id: PHASE5D_M0D_EXECUTION_ADMISSION_MATERIALIZATION_PREFLIGHT_20260724_V0_1
worktree_path: /tmp/agents-os-phase5d-m0d-source-555b3b538f6e
quarantine_root: /tmp/agents-os-phase5d-m0d-quarantine-555b3b538f6e
required_preexistence:
  canonical_root_must_exist: true
  worktree_path_must_not_exist: true
  quarantine_root_must_not_exist: true
  existing_path_result: BLOCKED_PREEXISTING_OR_UNOWNED_PATH
```

### 4.1 Allowed operations, in order

1. Verify only the canonical root's Git object membership for commit
   `555b3b538f6eb736e530c2912de678c5941f9985`; do not read the original
   worktree's uncommitted contents or configuration.
2. Create exactly one detached worktree at `worktree_path`, checked out at that
   commit. Verify its `HEAD`, tree, clean status and the seven sealed object
   tuples before any other source read.
3. Enumerate Git-tracked regular-file paths at that detached commit. Any path
   matching a protected name (`.env`, `.env.*`, `config.env`, `*.pem`, `*.key`,
   `credentials`, `tokens`, `cookies`, `secret`, `secrets`, `state-private`)
   stops the preflight before content is read. Directory and file names may be
   recorded only as an inventory rejection reason, never as raw content.
4. Read only non-protected, Git-tracked source and manifest bytes required to
   derive the static module/dependency inventory. If a dependency cannot be
   resolved from those bytes without environment, installed dependency,
   credential, configuration or network access, return
   `BLOCKED_HERMETIC_DEPENDENCY_INVENTORY_UNAVAILABLE`.
5. Create exactly one new quarantine root at `quarantine_root`. Materialize
   only these two files beneath it, preserving their bytes exactly:

   ```text
   Plugin/AGENTSOSResident/index.js
   Plugin/AGENTSOSResident/plugin-manifest.json
   ```

   The source files are the two immutable `inert_payload` inputs above. The
   manifest may exist only inside this new quarantine root; it must not be
   written to AGENTS OS, the canonical VCPToolBox root or any ordinary Host
   plugin directory.
6. Hash, enumerate and permission-check the two materialized files. Record the
   candidate root, inventory, exact byte hashes, finalizer order and residue
   observation as preflight evidence only.
7. Do not instantiate `PluginManager`, call `loadPlugins`, `initialize`,
   `shutdownAllPlugins`, `shutdown`, `processToolCall`, native/N-API or any
   runtime/service/database/provider/authentication interface.
8. Run the owned-root cleanup finalizer. It may remove only the two literal
   newly-created paths above after their ownership marker and run ID match.
   Remove the detached worktree using the canonical Git worktree mechanism.
   Observe and record that both literal paths no longer exist. Any cleanup
   failure, residual path, path substitution or missing ownership marker is
   `BLOCKED_CLEANUP_OR_RESIDUE_UNVERIFIED`.

### 4.2 Required fail-closed outcomes

```yaml
unexpected_Git_head_tree_or_sealed_blob: BLOCKED_SEALED_SOURCE_MISMATCH
preexisting_or_unowned_worktree_or_quarantine_path: BLOCKED_PREEXISTING_OR_UNOWNED_PATH
protected_or_unreadable_source_path: BLOCKED_PROTECTED_OR_UNREADABLE_SOURCE
incomplete_or_environment_dependent_inventory: BLOCKED_HERMETIC_DEPENDENCY_INVENTORY_UNAVAILABLE
payload_or_manifest_hash_or_inventory_mismatch: BLOCKED_INERT_PAYLOAD_MISMATCH
any_Host_lifecycle_or_runtime_attempt: BLOCKED_OUT_OF_SCOPE_HOST_OPERATION
cleanup_or_residue_failure: BLOCKED_CLEANUP_OR_RESIDUE_UNVERIFIED
all_preflight_facts_present: PREFLIGHT_EVIDENCE_CANDIDATE_ONLY
```

`PREFLIGHT_EVIDENCE_CANDIDATE_ONLY` is not an actual Host authorization. It
must be reviewed and bound into a later, separately current Jenn decision that
names the exact lifecycle calls and expected observations.

## 5. Explicit exclusions

The preflight may not modify the canonical VCPToolBox worktree or AGENTS OS
source files. It may not deliver an archive, enable a plugin outside the
quarantine root, invoke discovery/loading/lifecycle methods, start a runtime,
install dependencies, read credentials or active configuration, access private
Memory/state-private, call a provider, sense, record, create a database, or
produce a real effect. It may not commit, push, create a PR, merge, release,
deploy, publish, tag, force push or start a later phase.

## 6. Jenn decision surface

Jenn may choose exactly one outcome.

### A. Authorize one execution-admission materialization preflight

Exact decision text:

```text
我确认执行 AGENTS OS Phase 5D M0-D Execution-Admission Materialization
Preflight Decision Package v0.1 第 4 节所定义的一次性预检。

我只授权在 canonical VCPToolBox root
/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox 上，以 commit
555b3b538f6eb736e530c2912de678c5941f9985 创建并清理一个全新的 detached
worktree，以及在两个 package 指定的、预先不存在的 /tmp 路径创建并清理 quarantine
root；只可静态生成 hermetic inventory、物化并哈希两文件 inert payload、记录 cleanup
residue evidence。

我确认本次绝不授权 PluginManager、loadPlugins、initialize、shutdownAllPlugins、
shutdown、quarantine Host lifecycle、processToolCall、native/N-API、runtime、database、
provider、authentication、private Memory、state-private、sensing、recording 或任何真实
effect。若任一 preflight 条件、hash、inventory、ownership 或 cleanup observation 不满足，
必须 fail closed、清理已拥有的临时路径并停止。

本决定不授权 commit、push、PR、merge、release、deploy、publish、tag 或后续实际 Host
smoke。预检结束后必须形成 receipt 并停在新的 Jenn-only actual Host lifecycle execution
decision 门。
```

### B. Do not start

Retain the current frozen R2 state and `NOT_EXECUTED`. No worktree, quarantine
root, payload materialization or Host operation may occur.

## 7. Package preparation validation

Before Jenn's decision, recompute all six immutable fact hashes in Section 2,
parse this Markdown's fenced YAML facts, verify the literal path policy and
confirm `Host_operation_count=0`. Any mismatch leaves this package unconsumed
and the current state unchanged.
