# AGENTS OS Phase 5D M0-D MEHS v0.3 Post-Gate-2 Closeout PR #36 Mainline Merge Decision Package v0.1

Date: 2026-07-25
Owner: Jenn
Agent steward: Nobao
Status: `READY_FOR_JENN_EXACT_PR36_MAINLINE_MERGE_DECISION`
Recommended outcome: `AUTHORIZE_SINGLE_NORMAL_MERGE_AND_POSTMERGE_DURABILITY_PREPARATION`

## 1. Decision-ready state

Jenn directed Nobao to send local closeout commit `bd41c39…` safely and
independently into mainline durability. That direction authorized the bounded
publication and review work needed to establish PR #36. It preceded the PR
number and current remote state, so it is not treated as floating authorization
to merge an object that had not yet been identified.

The exact delivery object is now stable:

```yaml
repository: JENN2046/Agents-OS
repository_visibility: PRIVATE
PR_number: 36
PR_url: https://github.com/JENN2046/Agents-OS/pull/36
PR_state: OPEN
PR_ready: true
PR_mergeable: true
PR_mergeable_state: CLEAN
origin_main: 96e07d937ee3fad6c7240ec058ecb46784f60e5a
PR_final_head: bd41c39f0aa33221ecab216e04c508117afb6cc5
PR_final_head_parent: 96e07d937ee3fad6c7240ec058ecb46784f60e5a
PR_final_head_tree: f0af0a1d9ac10af8cd1e704561d03d613ae49d2f
PR_commits: 1
PR_changed_paths: 13
PR_added_paths: 5
PR_modified_paths: 8
PR_additions: 893
PR_deletions: 39
merge_method: normal_merge_commit
direct_push_to_main: false
```

## 2. Hash-bound closeout objects

```yaml
post_Gate_2_direction_package:
  path: control-plane/registry/reports/2026-07-25-agents-os-phase-5d-m0d-mehs-v0.3-post-gate2-direction-decision-package-v0.1.md
  sha256: c6160ec82b48264acb457156e01ac19ae45e8827f685c6fa2fb2756bec9295fe
post_Gate_2_outcome_A_decision:
  path: control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-mehs-v0.3-post-gate2-direction-outcome-a-decision-v0.1.yaml
  sha256: 6353a9794d6a599cbe25d2a32b40a692696b256802a3df877cd82fc5cdb0b458
PR_35_premerge_decision:
  path: control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-mehs-gate2-postmerge-projection-pr35-mainline-merge-decision-v0.1.yaml
  sha256: f84cf645542791d8bff4bfe34ddcaa0371f8ffe054c9294a613cad6f31cb5586
PR_35_merge_successor_receipt:
  path: control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-mehs-v0.3-pr35-merge-successor-closeout-v0.1.md
  sha256: f704803179b4cc0ab5839c804a4d385bd1d406e187fe44ef873c287c3f816784
active_queue:
  path: control-plane/registry/reports/2026-07-25-agents-os-active-work-queue-v17.7-mehs-terminal-closeout.md
  sha256: 0ded8fcf3b9048c5e4f49470febf3df0d8b5b5e57eccb746d4625b36d702dcc5
CURRENT_STATE:
  path: CURRENT_STATE.md
  sha256: e4ef83fa93032e98832f41e610b76eab9255c0adc5c0d854db4b056d32c33b85
```

The frozen Gate evidence remains unchanged. Gate 1 is permanently consumed,
retry is false, and this delivery creates no authority to replay `--actual`.

## 3. Independent review and validation

Fresh independent exact-head review returned `PASS_NO_BLOCKER` without
modifying the candidate or interacting with the PR.

```yaml
independent_exact_head_review: PASS_NO_BLOCKER
self_review_comment_id: 5078738114
self_review_result: PASS_NO_BLOCKER
configured_status_checks: 0
configured_workflows: 0
latest_reviews: 0
review_requests: 0
review_comments: 0
unresolved_review_threads: 0
issue_comments: 1
blocking_comments: 0
state_sync_record_present: false
Document_Registry: 1548_DOCUMENTS_0_FAIL
Federated_Registry: 3_OF_3_PASS
Machine_fixtures: 16_CASES_0_FAILURES
Control_Chain_fixtures: 30_CASES_0_FAILURES
Workbench_fast_fixtures: 10_CASES_0_FAILURES
docctl_head: 48_FAIL_0_UNREGISTERED
docctl_base: 48_FAIL_0_UNREGISTERED
Dashboard_head: 17_CASES_2_FAILURES
Dashboard_base: 17_CASES_5_FAILURES
Dashboard_remaining_failures: EXISTING_DOCCTL_HARD_GATE_ONLY
secret_like_patterns: 0
protected_boundary_changed_paths: 0
canonical_root_existing_dirty_hashes_match: 8_OF_8
```

The repository has no `.github/workflows` surface and reports no configured
checks for this PR. The branch-protection/ruleset endpoints are unavailable for
this private repository plan; GitHub's PR state itself reports `CLEAN` and
`MERGEABLE`.

## 4. Merge effect

A normal merge commit would integrate the exact reviewed tree into `main`.
It would not by itself create a new construction route or a reusable merge
authority.

After a successful merge, mainline durability still requires a separate,
bounded projection that:

1. records the exact PR #36 merge commit, parents, tree and remote-main state;
2. preserves this pre-merge decision evidence as immutable historical bytes;
3. keeps MEHS v0.3 terminally closed and Gate 1 replay forbidden;
4. keeps the queue at `No Active Automatic Construction Item`;
5. updates only the required Registry, `CURRENT_STATE` and default-pointer
   projection; and
6. goes through its own task branch, PR, exact-head review and later exact
   merge decision.

The PR #36 authorization cannot be reused for that later projection merge.

## 5. Preconditions

Immediately before any merge:

```text
origin/main must equal 96e07d937ee3fad6c7240ec058ecb46784f60e5a
PR #36 must remain OPEN and ready
PR #36 head must equal bd41c39f0aa33221ecab216e04c508117afb6cc5
PR #36 must remain CLEAN and MERGEABLE
the six bound closeout object SHA-256 values must match
the fresh independent review must remain PASS_NO_BLOCKER
all then-current required checks, reviews and approvals must be satisfied
there must be no blocking comment or unresolved review thread
the remote task branch must equal the reviewed head
canonical-root existing dirty bytes must remain 8/8 exact
the subject worktree must remain clean
no release, deploy, publish or production effect may be triggered
```

Any drift in base, head, tree, evidence, review, history, comments, threads,
checks or canonical-root bindings fails closed and requires a new decision.

## 6. Exact Confirmation Text

Valid only when Jenn sends the complete text below with
`<PACKAGE_SHA256>` replaced by this package's externally computed exact
SHA-256:

```text
我确认以下 PR #36 Mainline Merge Decision Package exact bytes：

control-plane/registry/reports/2026-07-25-agents-os-phase-5d-m0d-mehs-v0.3-post-gate2-closeout-pr36-mainline-merge-decision-package-v0.1.md

SHA-256：
<PACKAGE_SHA256>

我授权仅为 PR #36
https://github.com/JENN2046/Agents-OS/pull/36

建立 hash-bound immutable mainline merge decision record，并仅在：

- origin/main 精确为 96e07d937ee3fad6c7240ec058ecb46784f60e5a；
- PR final head 精确为 bd41c39f0aa33221ecab216e04c508117afb6cc5；
- PR final-head tree 精确为 f0af0a1d9ac10af8cd1e704561d03d613ae49d2f；
- package、Outcome A decision、PR #35 premerge decision、PR #35 successor receipt、
  active queue 与 CURRENT_STATE 的 SHA-256 全部精确匹配本 package；
- fresh independent exact-head review 仍为 PASS_NO_BLOCKER；
- PR 仍为 OPEN、ready、CLEAN、MERGEABLE；
- 当前 required checks、reviews、approvals 全部满足；
- 无 blocking comments 或 unresolved review threads；
- remote task branch 仍精确等于 reviewed head；
- canonical root 现有工作树修改仍为 8/8 exact，且不会被覆盖、stash、reset、
  clean 或改变

时，执行一次 normal merge commit。不得删除 local branch、remote branch 或
/tmp worktree。

合并成功并核验 remote main 后，我授权准备 bounded post-merge durability
projection candidate，并可通过独立 task branch 与 PR 送至下一次 exact merge
decision gate；本授权不自动授权该 projection PR merge。

任何 base、head、tree、证据、history、review、checks、comments、threads 或
canonical-root 状态变化都必须 fail closed，并重新请求决定。

本授权不包含 direct push to main、Gate 1 权限复用、--actual replay、Host 或
VCPToolBox Git、processToolCall、native/N-API、runtime、provider、database、
private Memory、state-private、release、deploy、publish、tag、force push、
history rewrite 或新建设路线启动。
```

## 7. Retained prohibitions

```yaml
direct_push_to_main: forbidden
merge_without_exact_current_binding: forbidden
force_push_tag_release_deploy_publish: forbidden
Gate_1_reuse_or_actual_replay: forbidden
Host_VCPToolBox_runtime_provider_database: unauthorized
private_Memory_or_state_private: forbidden
new_route_auto_selection_or_start: forbidden
canonical_root_overwrite_stash_reset_clean: forbidden
```
