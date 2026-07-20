# AGENTS OS Phase 5A M0-A Implementation Start Decision Package v0.1

Date: 2026-07-20
Status: `READY_FOR_JENN_EXPLICIT_IMPLEMENTATION_START_DECISION`
Owner: Jenn
Agent steward: Nobao

## 1. Decision-ready result

The frozen Phase 5A M0-A plan is durable on private `main`, and the final
implementation-start precondition has passed.

```yaml
preflight_result: PASS
sealed_VCPToolBox_git_objects: 7/7_MATCH
sealed_commit_is_ancestor_of_current_remote_main: true
plan_manifest_inputs_on_main: 227/227_MATCH
frozen_plan_subjects_on_main: 55/55_MATCH
plan_validators: R5_R6_R7_R8_PASS_NO_BLOCKER
builder_byte_reproduction: 3/3_PASS
implementation_start_gate: SATISFIED_FOR_JENN_DECISION
automatic_start: forbidden
Phase_5A_implementation_started: false
implementation_authorized: false
```

Preflight evidence:

```text
control-plane/registry/reports/2026-07-20-agents-os-phase-5a-m0a-implementation-start-preflight-v0.1.yaml
SHA-256 34d5e7d4d96aebf90e989f36b4fea76a6b59a4f882ad5ec49bca2be722882344
```

The preflight used a fresh no-checkout `blob:none` bare verifier against
`https://github.com/lioensky/VCPToolBox`. It proved that commit
`555b3b538f6eb736e530c2912de678c5941f9985` is an ancestor of current remote
`main` at `ee2c3a8d90223c920d0e04d38d008c34ac1a3194`, and that all seven declared
paths are exact Git blobs in the sealed commit tree. Each blob OID and complete
file SHA-256 matched the R8 manifest in both the existing object database and
the fresh remote verifier.

The dirty `runtime/VCPToolBox` worktree was not used as evidence, read as an
implementation source, modified, fetched, checked out, reset or cleaned.

## 2. Frozen authority bindings

```yaml
acceptance_unit: PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R8_ATOMIC_BUNDLE
subject_count: 55
partial_interpretation: forbidden
precedence:
  - R8_explicit_replacements
  - R7_all_other_clauses
  - R6_all_other_clauses
  - R5_all_other_clauses
  - R4_all_other_clauses
  - R3_all_other_clauses
  - R2_all_other_clauses
  - R1_all_other_clauses
```

Canonical bindings:

```text
manifest:
  control-plane/registry/reports/2026-07-20-agents-os-phase-5a-m0a-plan-r8-atomic-independent-review-package-v0.1.manifest.yaml
  SHA-256 f6b00bb0a19bb464122d44839e4f8987b0a68aea0794d0a36e9e29bec1de96b3

independent review:
  control-plane/registry/reviews/2026-07-20-yellow-agents-os-phase-5a-m0a-plan-r8-full-atomic-independent-review.yaml
  SHA-256 c4ee54e47287a8fb17a131663409ea261748e6c5ee0b1577f65975a066aa7cf7

plan freeze decision:
  control-plane/registry/decisions/2026-07-20-agents-os-phase-5a-m0a-plan-r8-atomic-freeze-decision-v0.1.yaml
  SHA-256 db3aad1623a62ddab3735a086e4af6773cfd1b71103a43030ab01be010688e1e

plan mainline integration:
  PR #19 merge commit 35639321aa76a77c57713a54c9753102f1b8fea9

durability projection integration:
  PR #20 merge commit 710ad9b01a4ae9eb28972d40dae24e0cc12cc652
```

## 3. Exact implementation scope if Jenn chooses A

Choosing A starts only the frozen Phase 5A M0-A deterministic orchestrator
implementation. Source authority remains:

```text
extensions/agents-os-resident/
```

Implementation proceeds in the frozen order:

```text
WP0 Reproducible skeleton
-> WP1 Canonical primitives
-> WP2 Resident ownership
-> WP3 Ledger v1
-> WP4 Command boundary
-> WP5 Permit and Outbox
-> WP6 Validation completion
-> WP7 Integrated M0-A witness
```

WP0 may start immediately after the decision record is written. WP1-WP7 may
start only after the immediately preceding work package passes its frozen
advancement condition. Failure is repaired within the effective R1-R8 scope;
it does not authorize skipping, widening or substituting a work package.

The implementation decision may authorize only:

- a new local AGENTS OS implementation task branch and scoped local commits;
- source and tests under `extensions/agents-os-resident/`;
- the exact project-local toolchain and pinned dependencies declared by the
  effective R1-R8 Build Profile;
- deterministic Rust, JavaScript and N-API implementation and offline builds;
- one test-created temporary isolated SQLite database and its synthetic test
  writes, recovery tests and deletion, with no existing or production database;
- a new clean linked VCPToolBox worktree fixed at
  `555b3b538f6eb736e530c2912de678c5941f9985` for compatibility tests;
- materialization of the Jenn-owned package into that clean worktree only as
  `Plugin/AGENTSOSResident/` with `plugin-manifest.json.block`;
- mock-only Host, Outbox, receipt and recovery testing using `SYNTHETIC_TEST`;
- deterministic evidence, validation reports and scoped governance receipts.

The clean compatibility worktree is disposable installation evidence, not a
new source of truth. Its VCPToolBox core diff must remain zero. The existing
dirty `runtime/VCPToolBox` worktree and all of its local changes, blocked
manifests, runtime data and configuration remain untouched.

## 4. Boundaries that remain forbidden after A

Choosing A does not authorize:

- modifying `server.js`, `Plugin.js`, root package metadata, routes, modules,
  existing plugins or active VCPToolBox configuration;
- enabling `plugin-manifest.json`, starting VCPToolBox or activating a plugin;
- using an existing, production, user-owned or non-temporary database;
- production authentication, credentials, keys, cookies or cryptography;
- private raw Memory, `state-private/`, provider raw responses or raw logs;
- real Task, Command, Host, Resident, provider, sensing, recording or effect;
- network listener, HTTP, gRPC, sidecar, external Rust daemon, Tokio, second
  supervisor, second ledger writer or second SQLite connection;
- public API or MCP expansion, Phase 5B, production migration or runtime
  integration;
- pushing to `JENN2046/VCPToolBox` or publishing any VCPToolBox fork;
- pushing the implementation branch, opening or merging an implementation PR,
  tag, release, deploy or package publish without its later delivery gate;
- external Codex runner or other autonomous external executor invocation.

Synthetic fixtures and successful tests remain runtime-unusable. No work may
reinterpret relationship, trust, urgency, Actor class or Task label as
permission, and the implementation may consume but not recreate the frozen
F1-F8 authorities.

## 5. Required start closeout after A

If Jenn chooses A, create only the minimal start closeout before source work:

```text
immutable implementation-start decision record
Active Work Queue and CURRENT_STATE projection to WP0
Document/Federated Registry projection
one implementation-start receipt
new local implementation task branch from verified main
```

The start closeout must preserve this package, the preflight evidence and all
55 frozen plan subjects. It must not itself install dependencies, create the
SQLite file, create implementation source, materialize the plugin or start any
runtime. Those actions begin only after the closeout projects A as current.

## 6. Jenn decision surface

Jenn may choose exactly one outcome.

### A. Start the frozen Phase 5A M0-A implementation

Exact decision text:

```text
我确认启动 AGENTS OS Phase 5A M0-A Deterministic Orchestrator Core 的实现，
实现权威严格绑定已冻结的完整原子单元
PHASE_5A_M0A_PLAN_BUILD_PROFILE_V0_1_R8_ATOMIC_BUNDLE。

我确认该单元仅由 manifest
control-plane/registry/reports/2026-07-20-agents-os-phase-5a-m0a-plan-r8-atomic-independent-review-package-v0.1.manifest.yaml
中列明的 R1-R8 共 55 个 subjects 构成；manifest SHA-256 为
f6b00bb0a19bb464122d44839e4f8987b0a68aea0794d0a36e9e29bec1de96b3，
并按 R8 explicit replacements、R7 all other clauses、R6 all other clauses、
R5 all other clauses、R4 all other clauses、R3 all other clauses、R2 all other
clauses、R1 all other clauses 的顺序解释。禁止部分解释、替换或扩张。

我确认 independent review SHA-256 为
c4ee54e47287a8fb17a131663409ea261748e6c5ee0b1577f65975a066aa7cf7，
plan freeze decision SHA-256 为
db3aad1623a62ddab3735a086e4af6773cfd1b71103a43030ab01be010688e1e，
plan mainline merge commit 为
35639321aa76a77c57713a54c9753102f1b8fea9，durability projection merge commit 为
710ad9b01a4ae9eb28972d40dae24e0cc12cc652。

我确认 implementation-start preflight
control-plane/registry/reports/2026-07-20-agents-os-phase-5a-m0a-implementation-start-preflight-v0.1.yaml
的 SHA-256 为
34d5e7d4d96aebf90e989f36b4fea76a6b59a4f882ad5ec49bca2be722882344，
结论为 PASS。该证据确认 lioensky/VCPToolBox commit
555b3b538f6eb736e530c2912de678c5941f9985 属于当前远端 main 的祖先历史，
其 tree 为 fd82d403e79f36f749eb7f555b4736eae3eacdff，且 manifest 声明的
7 个 sealed Git blobs 全部完成 path、mode、blob OID、完整字节与 SHA-256 核验。

本决定授权在新的本地 AGENTS OS task branch 中，以
extensions/agents-os-resident/ 为唯一 source authority，依次实施 WP0-WP7。
WP0 可在 start closeout 完成后开始；WP1-WP7 只有在直接前序 work package 的
冻结 advancement condition 通过后才可继续，不得跳过、并行越级或扩张范围。

本决定授权冻结 Build Profile 精确列明的 project-local toolchain 与 pinned
dependencies、Rust / JavaScript / N-API 源码和离线构建、SYNTHETIC_TEST mock、
以及仅位于 test-created temporary isolated directory 的单一 SQLite 数据库文件
创建、写入、恢复测试和删除。禁止使用任何已有、生产、用户所有或非临时数据库。

本决定授权创建固定在 VCPToolBox commit
555b3b538f6eb736e530c2912de678c5941f9985 的全新 clean linked worktree，仅用于
compatibility tests，并仅把 Jenn-owned package materialize 到
Plugin/AGENTSOSResident/，且只能使用 plugin-manifest.json.block。VCPToolBox core
diff 必须为 zero；现有 runtime/VCPToolBox 脏工作树及其本地修改、运行数据、配置和
blocked manifests 必须保持不读、不改、不清理、不覆盖。

本决定不授权修改 VCPToolBox core、启用插件、启动 VCPToolBox、runtime activation、
production authentication、credential、key、cookie、private raw Memory、
state-private、provider raw response，以及冻结本地实现与 SYNTHETIC_TEST 范围之外的
真实 Task / Command / Host / Resident、sensing、recording、provider、device、file、
process 或 physical effect、network listener、
HTTP、gRPC、sidecar、external Rust daemon、Tokio、第二 writer、第二 SQLite
connection、public API、MCP、Phase 5B、production migration、向 VCPToolBox fork
push、implementation branch push、PR、merge、tag、release、deploy、publish 或外部
Codex / executor runner。

请先创建不可变 implementation-start decision record，并只完成必要的 Active Work
Queue、CURRENT_STATE、Document/Federated Registry 与 start receipt 投影；该 closeout
本身不得安装依赖、创建实现源码或数据库、materialize plugin 或启动 runtime。完成
closeout 后才可从 WP0 开始自动推进，并在每个冻结 advancement condition 前后留下
可复核证据。
```

### B. Defer or revise the start scope

Jenn may defer implementation or identify an exact scope correction. No
implementation-start decision record is created, and the system remains at
this gate. Any plan-semantic change requires a new reviewed revision; it cannot
be applied inside the start decision.

### C. Reject implementation start

Jenn may reject implementation start. The frozen plan remains historical
governance authority, but no implementation source, dependency installation,
database file, clean worktree or plugin materialization is authorized.

## 7. Stop state

This package and its preflight evidence do not start implementation. Until
Jenn executes A exactly:

```yaml
Phase_5A_implementation_started: false
implementation_authorized: false
dependency_installation_authorized: false
database_creation_or_write_authorized: false
clean_VCPToolBox_worktree_creation_authorized: false
plugin_materialization_authorized: false
VCPToolBox_change_or_start_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
private_raw_memory_or_state_private_access_authorized: false
provider_sensing_recording_or_real_effect_authorized: false
```
