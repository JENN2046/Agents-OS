# AGENTS OS Phase 5D M0-D Implementation Start Decision Package v0.1

Date: 2026-07-24
Status: `READY_FOR_JENN_IMPLEMENTATION_START_DECISION`
Owner: Jenn
Agent steward: Nobao

## 1. Decision-ready result

Phase 5D M0-D Plan R1–R2 is frozen, durable on `main`, and remains a
synthetic, quarantined Host-smoke plan. This package asks only whether to begin
the exact local implementation sequence described below. It does not claim
that a Host action, plugin enablement, native load, runtime, or real smoke has
occurred.

```yaml
preflight_result: PASS
decision_readiness: READY_FOR_JENN_PHASE_5D_M0D_IMPLEMENTATION_START_DECISION
implementation_started: false
implementation_authorized: false
runtime_usable: false
terminal_outcome_before_decision: NOT_EXECUTED
automatic_transition: forbidden
```

Bound preflight:

```text
control-plane/registry/reports/2026-07-24-agents-os-phase-5d-m0d-implementation-start-preflight-v0.1.yaml
SHA-256: 887af67b242af25a8ea7569443d3ff5407253ca71a4106a33097859b88b36fcf
```

## 2. Frozen plan binding

```yaml
acceptance_unit: PHASE_5D_M0D_PLAN_BUILD_PROFILE_V0_1_R2_ATOMIC_BUNDLE
manifest:
  path: control-plane/registry/reports/2026-07-23-agents-os-phase-5d-m0d-plan-r2-atomic-independent-review-package-v0.1.manifest.yaml
  sha256: f8c4dc55df8c7110462d1ec117856df275edaf654ab057f083ce1817f7bbb061
independent_review:
  path: control-plane/registry/reviews/2026-07-23-yellow-agents-os-phase-5d-m0d-plan-r2-full-atomic-independent-review.yaml
  sha256: 902a9fd3686cfbe95693e272df329282f3b33d44ebb1285edfc37bc3ebf8b068
  result: PASS_NO_BLOCKER
freeze_decision:
  path: control-plane/registry/decisions/2026-07-23-agents-os-phase-5d-m0d-plan-r2-atomic-freeze-decision-v0.1.yaml
  sha256: 08da0e6ee8b93e994ef3b259b45d9f81b7e1fa443b947ccadedc8c2436a9ee31
mainline_merge_commit: be0206cfa925c7c1afa2f0987d19ebcbcbdad3d4
current_main_commit: 5d66dbd608a031c1b6db3a7bcac9ca25b5491f31
```

Partial interpretation, frozen-plan mutation, and a new Plan revision are
forbidden.

## 3. What this decision would authorize

If Jenn chooses A, Nobao may start the frozen implementation at WP0 on
`agent/phase-5d-m0d-implementation-start`, then advance only when the direct
predecessor validation passes.

```text
WP0 sealed source and Host-commitment revalidation
WP1 owned quarantine topology and path policy
WP2 blocked-manifest preservation and transient-manifest rule
WP3 inert lifecycle-only smoke contract
WP4 cleanup, rollback, and residue observation
WP5 integrated synthetic preflight witness
```

The implementation may create only:

```text
extensions/agents-os-resident/tools/prepare-quarantined-host-smoke.mjs
extensions/agents-os-resident/tools/validate-quarantined-host-smoke.mjs
extensions/agents-os-resident/fixtures/quarantined-host-smoke-contract.v0.1.json
extensions/agents-os-resident/tests/quarantined-host-smoke.mjs
```

It may modify only:

```text
extensions/agents-os-resident/README.md
extensions/agents-os-resident/package-manifest.json
```

`extensions/agents-os-resident/plugin-manifest.json.block` remains immutable.
Only deterministic local offline validation and newly-created harness-owned
temporary quarantine roots are in scope.

## 4. What remains prohibited

This decision does not authorize:

- VCPToolBox worktree read/write/clone/checkout or any VCPToolBox-core change;
- archive delivery/installation, an enabled manifest, plugin discovery,
  Host loading, `initialize`, `shutdown`, `processToolCall`, native addon or
  N-API invocation;
- runtime/service startup, database access, dependency or lockfile changes,
  provider use, production authentication, or public API/MCP expansion;
- private Memory, `state-private/`, credentials, sensing, recording, or a real
  effect; or
- release, deploy, publish, tag, force push, or a later-phase start.

Any future Host-facing action needs its own current Jenn decision after the
offline implementation evidence exists.

## 5. Preconditions verified without Host access

```yaml
frozen_plan_objects_on_origin_main: 6/6_MATCH
sealed_VCPToolBox_commit: 555b3b538f6eb736e530c2912de678c5941f9985
sealed_VCPToolBox_tree: fd82d403e79f36f749eb7f555b4736eae3eacdff
sealed_host_commitments: 7/7_MATCH_FROM_FROZEN_PROFILE
VCPToolBox_worktree_created_or_inspected: false
archive_delivered_or_installed: false
plugin_enabled_or_Host_loaded: false
lifecycle_or_native_call_invoked: false
current_queue_requires_Jenn_decision: true
```

## 6. Jenn decision surface

### A. Start the frozen offline implementation

Exact decision text:

```text
我确认启动 AGENTS OS Phase 5D M0-D Quarantined Host Smoke Integration 的冻结
offline implementation，严格按 Phase 5D M0-D Implementation Start Decision
Package v0.1 第 3 节的 WP0–WP5 顺序执行，并以每个直接前序验证通过为继续条件。

我确认该启动只授权创建该 package 第 3 节列明的四个 harness 文件，以及修改
extensions/agents-os-resident/README.md 与 package-manifest.json；
plugin-manifest.json.block 必须保持不变。

我确认本决定不授权 VCPToolBox worktree、archive delivery、enabled manifest、plugin
discovery/loading、Host lifecycle、processToolCall、native/N-API、runtime、database、
dependency、provider、production authentication、private Memory、state-private、sensing、
recording、真实 effect、release、deploy、publish、tag、force push 或后续阶段启动。

请创建不可变的 Phase 5D M0-D implementation-start decision record，并只做必要的
CURRENT_STATE、Active Work Queue、Registry、default-pointer 与 start receipt 投影；
然后从 WP0 开始。
```

### B. Do not start

Keep Phase 5D at `AWAITING_JENN_IMPLEMENTATION_START_DECISION`. No source,
Host, runtime, or external action begins.

### C. Revise scope

Jenn may request a narrower or different source-only scope. It creates a new
decision package; it does not mutate the frozen Plan.

## 7. Required closeout if A is chosen

Create one immutable start decision record bound to this package and preflight,
one start receipt, and only the needed `CURRENT_STATE`, Active Work Queue,
Document Registry, Federated Registry, and default-pointer projections. Re-run
the queue and Registry validators before WP0. No Host-facing action belongs to
this closeout.
