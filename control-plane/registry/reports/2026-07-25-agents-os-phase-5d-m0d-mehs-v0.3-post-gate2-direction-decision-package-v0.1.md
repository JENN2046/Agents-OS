# AGENTS OS Phase 5D M0-D MEHS v0.3 Post-Gate-2 Direction Decision Package v0.1

Date: 2026-07-25
Owner: Jenn
Agent steward: Nobao
Status: `READY_FOR_JENN_POST_GATE_2_DIRECTION_DECISION`
Recommended outcome: `A_TERMINAL_CLOSE_AND_RETURN_TO_ROUTE_SELECTION`
Automatic Gate 3 or later-phase start: `false`

## 1. Decision-ready state

MEHS v0.3 has completed the exact bounded lifecycle for which it was created:
the frozen candidate passed fresh independent review, Gate 1 was consumed once,
the one authorized actual Host smoke returned
`HOST_SMOKE_CANDIDATE_OBSERVED`, fresh actual closeout review returned
`PASS_NO_BLOCKER`, Gate 2 was normally merged through PR #34, and the
post-merge durability projection was normally merged through PR #35.

```yaml
frozen_candidate: 4690ce291d45339f5dbe71a793662e051629d558
frozen_candidate_parent: 310a7358f96b6749f0c31dd3e39517c9df87c50c
candidate_is_origin_main_ancestor: true
Gate_1_consumed: true
Gate_1_retry_authorized: false
actual_result: HOST_SMOKE_CANDIDATE_OBSERVED
actual_failure: null
cleanup_status: CLEAN
owned_temporary_residue_count: 0
Gate_2_PR: 34
Gate_2_reviewed_head: 799fd235b4ebf43c51d76f7bb55459223ed78cd3
Gate_2_merge_commit: 40139fe21f676e70ff22c70b416dd896fdf83e7e
postmerge_projection_PR: 35
postmerge_projection_head: 660e47328284b5926abd6c2ce87de0085973ba4e
postmerge_projection_merge_commit: 96e07d937ee3fad6c7240ec058ecb46784f60e5a
observed_origin_main: 96e07d937ee3fad6c7240ec058ecb46784f60e5a
MEHS_v0_3_terminal_close_selected: false
new_MEHS_or_later_phase_selected: false
execution_authorized: false
```

This package is a direction surface only. It does not select an outcome,
materialize Jenn's decision, update the active queue, authorize Git delivery,
or execute any Host, runtime, provider, database, Memory or real-effect action.

## 2. Hash-bound evidence

### Frozen candidate bytes

```yaml
plan:
  path: control-plane/registry/drafts/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-plan-v0.3.json
  sha256: e7bdc6dc34fad8fb431aee440d9ea3e3ad9cd286e4a45e15c30419d57e83bd59
correction:
  path: control-plane/registry/reviews/2026-07-25-agents-os-phase-5d-m0d-r4-disposition-clean-correction-v0.1.yaml
  sha256: e6a6958c1f69ee6181c3f94093da18575a6cfa4f52920800187ff5a771d0d8fc
runner:
  path: execution/agents-os-phase5d-host-smoke/one-shot-host-smoke.mjs
  sha256: 5301d36548dae2357a2e58615bcc60d0eac256223b838e5a26ec5d0892082c74
tests:
  path: execution/agents-os-phase5d-host-smoke/one-shot-host-smoke.test.mjs
  sha256: 19a0b95bef69980b4388496edad12ed8325a55eec8920a89fba574a59191338f
```

### Gate and closeout evidence

```yaml
frozen_candidate_review:
  path: control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3-r5-fresh-independent-review-closure.json
  sha256: 85db40073e42625f79bf20076728e97256ecc2ac5eb188e81fb2f12f36556b61
  result: PASS_NO_BLOCKER
Gate_1_decision:
  path: control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate1-decision-v0.3.json
  sha256: 3ed0c05d30af4866f26b5b4e386efa4b9b71988bc8c7549fd0ce806119022d12
Gate_1_claim:
  path: control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate1-consumed-v0.3.json
  sha256: 7fbab37aa21dd90657cffe9b8d83dd845a0d632638e8082f51a0cf9afaf1af69
terminal_receipt:
  path: control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3.json
  sha256: e4a5b7cff752d95c4891ba966d1aa6df5d17f609659e5fc0df4637dcfdb8035c
  result: HOST_SMOKE_CANDIDATE_OBSERVED
fresh_actual_closeout_review:
  path: control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3-r5-actual-closeout-fresh-independent-review.json
  sha256: 2e63d87301b7f23c2d933d9412756576dbb78fbab55bb03f233537b750bd4873
  result: PASS_NO_BLOCKER
Gate_2_decision_package:
  path: control-plane/registry/reports/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate2-decision-package-v0.1.md
  sha256: c6167c4e1d6176960a8f3acfe571213d5bec3085dfb4735a94e0bf3a178399d1
Gate_2_decision_record:
  path: control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate2-mainline-merge-decision-v0.1.yaml
  sha256: f90fad11ec2b37582a7f15ae592c75943d0d52cae37bd67a7853cf6163121d3a
Gate_2_delivery_manifest:
  path: control-plane/registry/reports/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate2-delivery-manifest-v0.1.yaml
  sha256: 7c5b8cf29e2f4ab34e04d7c9c608492a70cbfe80c16becc16d40a71263062633
postmerge_durability_receipt:
  path: control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-mehs-gate2-postmerge-durability-closeout-v0.1.md
  sha256: fd19cc90f3080f7ac13c151a3b872d7ac857dc8f2c03f2ff5c7c339990a4f143
```

### Post-merge projection and pending decision-record durability

```yaml
active_queue:
  path: control-plane/registry/reports/2026-07-25-agents-os-active-work-queue-v17.6-gate2.md
  sha256: 7523923609fb24a7902f29d58f78a8458e59c7f58fc98e359824d2945680e4a7
CURRENT_STATE:
  path: CURRENT_STATE.md
  sha256: ab05b10857d170389fc3f3ee262417fe151f4235fa15328ad5f70285e493b9e6
PR_35_merge_decision_record:
  path: control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-mehs-gate2-postmerge-projection-pr35-mainline-merge-decision-v0.1.yaml
  sha256: f84cf645542791d8bff4bfe34ddcaa0371f8ffe054c9294a613cad6f31cb5586
  bytes_created_before_merge: true
  merge_result: PR_35_MERGED_AS_96e07d937ee3fad6c7240ec058ecb46784f60e5a
  durable_on_origin_main: false
```

The PR #35 merge decision record is immutable pre-merge evidence. Its
`accepted_pending_single_normal_merge` status truthfully describes the moment
at which it was created and must not be edited after the fact. Any selected
governance closeout should preserve those exact bytes and record the completed
merge in a separate successor receipt or decision result.

## 3. What Gate 2 closes

The evidence supports the following bounded conclusion:

- the exact frozen candidate was independently reviewed and observed once;
- the sealed Host discovered only `AGENTSOSResident`;
- the allowed lifecycle stayed at
  `loadPlugins -> initialize -> shutdownAllPlugins -> shutdown -> cleanup`;
- initialize and shutdown returned the exact inert values;
- `processToolCall`, native/N-API, child-process, provider/network, database and
  private-Memory counters remained zero;
- the Gate 1 claim is permanent, replay is forbidden, cleanup was `CLEAN`, and
  owned residue was zero; and
- the reviewed candidate, Gate evidence and post-merge durability projection
  are integrated on `main`.

Therefore the narrow MEHS v0.3 objective is complete. Repeating the smoke would
not strengthen this one-shot result; it would violate the permanent claim
contract.

## 4. What Gate 2 does not create

No accepted artifact defines a Gate 3 objective, threat model, acceptance unit
or execution contract. `Gate 3` is therefore not a valid automatic successor
name and cannot inherit authority from Gate 1 or Gate 2.

The completed evidence is not:

```text
runtime activation
plugin enablement
processToolCall or native/N-API acceptance
provider, database or production-authentication readiness
private Memory or state-private access
continuous Host operation
release, deployment or publication readiness
a second actual-smoke authorization
```

Any future capability in one of those areas is a new scope. It requires a new
objective, explicit allowed and forbidden surfaces, a new threat model,
synthetic/offline gates where possible, fresh independent review, and a new
Jenn decision. It must not mutate the frozen candidate, claim, terminal receipt
or completed reviews.

## 5. Direction judgment

Outcome A is recommended because MEHS v0.3 has achieved its exact purpose with
no open blocker, the one-shot gate cannot be repeated, and no accepted Gate 3
contract exists. Terminally closing this line keeps the evidence durable while
returning broader construction direction to Jenn.

Outcome B is available if Jenn wants to extract architecture or governance
amendment candidates from the observed evidence before choosing a broader
route. It remains assessment-only.

Outcome C is available if Jenn already has a concrete new Host/capability goal.
It creates a separate intake; it does not extend MEHS v0.3 by implication.

Outcome D preserves the current stop-state.

## 6. Jenn decision surface

Jenn may choose exactly one outcome. The same Jenn message must explicitly bind
this package path and its externally computed current SHA-256; an outcome body
without that binding is incomplete and authorizes nothing.

### Outcome A — Terminally close MEHS v0.3 and return to route selection

Recommended outcome body, valid only with the same-message package path/SHA
binding:

```text
我选择 MEHS-V0.3 Post-Gate-2 Direction Decision Package v0.1 的 Outcome A。

我确认 MEHS-V0.3 在 frozen candidate
4690ce291d45339f5dbe71a793662e051629d558 的一次性 actual Host observation、
Fresh Independent Actual Closeout Review、Gate 2 PR #34 mainline merge，以及
PR #35 post-merge durability projection merge 后终止关闭。

我确认 Gate 1 已永久消费、retry=false；不得删除、回滚、替换 claim/receipt，
不得 replay --actual，也不存在自动 Gate 3 或自动 later-phase start。

我授权下一步仅在 clean dedicated worktree 中建立 hash-bound immutable
post-Gate-2 direction decision record，并准备 bounded local governance closeout
candidate：精确纳入 PR #35 merge decision record
f84cf645542791d8bff4bfe34ddcaa0371f8ffe054c9294a613cad6f31cb5586，
以单独 successor evidence 记录 PR #35 已 merge 为
96e07d937ee3fad6c7240ec058ecb46784f60e5a，并把 CURRENT_STATE、Registry、
default pointers 与 active queue 投影到 MEHS-V0.3 terminally closed、
No Active Automatic MEHS Item、awaiting Jenn route selection。

本选择只授权上述本地治理 closeout candidate 与精确 local commit；不授权 push、
PR、merge、direct push to main、Gate 1 replay、Host 或 VCPToolBox Git、
processToolCall、native/N-API、runtime、provider、database、private Memory、
state-private、release、deploy、publish、tag、force push、history rewrite 或新阶段启动。

任何 candidate、evidence、origin/main、package bytes 或历史绑定变化都必须
fail closed；不得覆盖、stash、reset 或改变 canonical root 现有工作树修改。
```

### Outcome B — Evidence-driven amendment assessment only

Outcome body, valid only with the same-message package path/SHA binding:

```text
我选择 MEHS-V0.3 Post-Gate-2 Direction Decision Package v0.1 的 Outcome B。

保持 MEHS-V0.3 frozen candidate、Gate 1 claim/receipt、Gate 2 evidence 与 mainline
objects 不变。下一步只准备一个 hash-bound、read-only、proposal-only 的
evidence-driven amendment assessment，列出本次一次性 Host observation 对
architecture、contract、validator 与 future threat model 的可复用结论、无需修改项
和候选修订项。

本选择不启动 Phase 6、Gate 3 或任何实现；不授权 --actual replay、Host 或
VCPToolBox Git、processToolCall、native/N-API、runtime、provider、database、
private Memory、state-private、Git delivery、merge、release、deploy、publish、
tag、force push 或 history rewrite。assessment 完成并独立复核后，仍需 Jenn
另行决定是否采纳任何 amendment。
```

### Outcome C — Create a separate new-capability intake

This template is not valid until Jenn replaces the placeholder with one
concrete objective:

```text
我选择 MEHS-V0.3 Post-Gate-2 Direction Decision Package v0.1 的 Outcome C。
新的独立 capability proposal 目标是：<Jenn 填写一个精确目标>。

MEHS-V0.3 保持 terminal evidence，不作为自动 Gate 3 延伸。下一步只准备新的
scope intake、threat model、allowed/forbidden surface、acceptance unit、synthetic/
offline validation ladder 与 fresh independent review plan；不实施、不执行、不
启用 runtime，不进行 Host/VCPToolBox Git、provider、database、private Memory、
state-private、release、deploy、publish 或 mainline merge。
```

If the objective is missing, ambiguous or includes an immediate real effect,
Outcome C fails closed and no intake is promoted.

### Outcome D — Hold

Outcome body, valid only with the same-message package path/SHA binding:

```text
我选择 MEHS-V0.3 Post-Gate-2 Direction Decision Package v0.1 的 Outcome D。
保持当前 post-Gate-2 stop-state，不关闭为新路线、不创建 Gate 3、不启动任何
construction、execution、Git delivery、runtime、provider、database、Memory、
release、deploy 或 publish 工作。Gate 1 继续保持永久 consumed、retry=false。
```

## 7. Selection and materialization rules

1. Jenn's choice must bind the exact bytes and SHA-256 of this package.
2. Before materializing Outcomes A–C, recompute every selected evidence hash,
   confirm the candidate remains an ancestor of current `origin/main`, and
   refresh the remote base.
3. Any changed evidence, rewritten history, unexpected remote movement or
   prohibited-content finding requires a new reviewed package or a new Jenn
   decision; prior text does not float to changed bytes.
4. Work must use a clean dedicated worktree. Canonical-root tracked and
   untracked work is outside the subject and must not be overwritten, stashed,
   reset, cleaned or mixed into the change.
5. This package's existence, review or local commit does not select an outcome.
6. A direction decision does not itself authorize Git publication or mainline
   merge unless its exact selected text says so. None of the outcomes above
   authorizes a push, PR or merge.

## 8. Retained prohibitions

```yaml
Gate_1_claim_delete_replace_or_rollback: forbidden
actual_replay_or_second_claim: forbidden
automatic_Gate_3_or_later_phase: forbidden
Host_or_VCPToolBox_Git: unauthorized
processToolCall_native_addon_or_NAPI: unauthorized
runtime_service_provider_or_network_effect: unauthorized
database_or_production_authentication: unauthorized
private_Memory_or_state_private: forbidden
sensing_recording_or_real_effect: unauthorized
direct_push_to_main: forbidden
push_PR_or_merge_by_this_package: unauthorized
release_deploy_package_publish_tag_force_push_history_rewrite: forbidden
canonical_root_dirty_work_overwrite_stash_reset_or_clean: forbidden
```
