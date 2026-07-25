# AGENTS OS Phase 5D M0-D Minimum Exact Host Smoke Gate 2 Decision Package v0.1

Date: 2026-07-25
Owner: Jenn
Agent steward: Nobao
Status: `READY_FOR_JENN_GATE_2_DECISION`
Automatic merge: `false`

## 1. Decision-ready closeout

The frozen candidate's Fresh Independent Actual Closeout Review returned
`PASS_NO_BLOCKER`. Gate 1 was consumed exactly once under the runner's permanent
claim semantics, a terminal success receipt exists, cleanup is clean, and the
fixed quarantine root is absent.

This package prepares Jenn's Gate 2 decision. It does not itself authorize or
perform a commit, push, pull request, merge, release, deploy, publish, tag,
history rewrite, another Host smoke, or any replay.

```yaml
candidate_commit: 4690ce291d45339f5dbe71a793662e051629d558
candidate_parent: 310a7358f96b6749f0c31dd3e39517c9df87c50c
candidate_delta: 4_A_0_NON_A
actual_result: HOST_SMOKE_CANDIDATE_OBSERVED
actual_failure: null
cleanup_status: CLEAN
owned_temporary_residue_count: 0
Gate_1_consumed: true
Gate_1_retry_authorized: false
Gate_2_mainline_merge_authorized: false
```

## 2. Hash-bound evidence

```yaml
frozen_candidate_review:
  path: control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3-r5-fresh-independent-review-closure.json
  sha256: 85db40073e42625f79bf20076728e97256ecc2ac5eb188e81fb2f12f36556b61
Gate_1_decision:
  path: control-plane/registry/decisions/2026-07-25-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate1-decision-v0.3.json
  sha256: 3ed0c05d30af4866f26b5b4e386efa4b9b71988bc8c7549fd0ce806119022d12
Gate_1_claim:
  path: control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-gate1-consumed-v0.3.json
  sha256: 7fbab37aa21dd90657cffe9b8d83dd845a0d632638e8082f51a0cf9afaf1af69
terminal_receipt:
  path: control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3.json
  sha256: e4a5b7cff752d95c4891ba966d1aa6df5d17f609659e5fc0df4637dcfdb8035c
fresh_actual_closeout_review:
  path: control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3-r5-actual-closeout-fresh-independent-review.json
  sha256: 2e63d87301b7f23c2d933d9412756576dbb78fbab55bb03f233537b750bd4873
  result: PASS_NO_BLOCKER
  reviewer_materialization_check: RECORD_MATCH
```

The candidate remains bound to these committed artifact hashes:

```yaml
plan_sha256: e7bdc6dc34fad8fb431aee440d9ea3e3ad9cd286e4a45e15c30419d57e83bd59
correction_yaml_sha256: e6a6958c1f69ee6181c3f94093da18575a6cfa4f52920800187ff5a771d0d8fc
runner_sha256: 5301d36548dae2357a2e58615bcc60d0eac256223b838e5a26ec5d0892082c74
tests_sha256: 19a0b95bef69980b4388496edad12ed8325a55eec8920a89fba574a59191338f
```

## 3. What the actual closeout proves

The terminal receipt and fresh closeout review confirm:

- the allowed lifecycle was exactly
  `loadPlugins -> initialize -> shutdownAllPlugins -> shutdown -> cleanup`;
- only `AGENTSOSResident` was discovered;
- initialize returned `{initialized:false}` and shutdown returned
  `{shutdown:true}`;
- `processToolCall`, native-addon, child-process, provider/network, database and
  private-memory counters were all zero;
- the sealed Host commit, tree, blob and blob SHA matched;
- bwrap ran once, the fixed seccomp/network boundary was attested, wrapper error
  was null, canonical Host root modification was false, cleanup was `CLEAN`,
  and owned residue was zero; and
- the permanent claim and terminal receipt both block replay before another
  smoke can start.

AF_UNIX `EPERM` remains corroborating evidence only. `packet_count:0` is not a
packet-capture claim. `--share-net` means a shared network namespace; the
network boundary rests on fixed seccomp, FD attestation, bwrap and the Node
permission model.

This closeout is not production readiness, runtime activation, provider
readiness, or authorization for another Host action.

## 4. Mainline delivery surface

The reviewed candidate delta is not the complete mainline delivery delta.
Observed local refs at package preparation were:

```yaml
local_main: be0206cfa925c7c1afa2f0987d19ebcbcbdad3d4
observed_origin_main: 5d66dbd608a031c1b6db3a7bcac9ca25b5491f31
implementation_line: 310a7358f96b6749f0c31dd3e39517c9df87c50c
candidate: 4690ce291d45339f5dbe71a793662e051629d558
local_main_to_candidate: 20_commits_fast_forward
observed_origin_main_to_candidate: 15_commits_fast_forward
implementation_line_to_candidate: 1_commit_fast_forward
```

The candidate commit contains only the four frozen additions. The Gate 1
decision, claim, receipt, frozen review, actual closeout review and this package
are currently local untracked evidence and are not contained in the candidate
commit. Therefore a direct merge of only `4690ce2...` would omit the closeout
evidence, while describing the full mainline operation as a four-file merge
would understate its history surface.

Gate 2 outcome A must use a new scoped delivery branch descended from the
candidate. It must preserve the candidate commit and blobs unchanged, add the
exact evidence above, add only the necessary Gate 2 decision/delivery records
and governance projections, and bind the final delivery head with a complete
manifest and current-head review.

## 5. Preconditions for any Gate 2 delivery

All of the following must hold immediately before any push, pull request or
merge:

1. Recompute every hash in Section 2 and confirm the candidate ref still points
   to `4690ce291d45339f5dbe71a793662e051629d558`.
2. Confirm the claim and receipt remain regular canonical files, mode `0600`,
   retry remains forbidden, and the quarantine root remains absent.
3. Build the delivery branch in a clean dedicated worktree without switching,
   stashing, resetting, overwriting or mixing Jenn's current dirty worktree.
4. Refresh the approved private remote state. Review the complete current
   `origin/main..final_head` commit and file surface, not only the candidate's
   four additions. Any base movement or unexpected divergence requires a fresh
   final-head review.
5. Confirm the delivery history and diff contain no secrets, credentials,
   tokens, cookies, private raw memory, provider raw response, raw logs,
   private-only links, cache, runtime state or unrelated user work.
6. Confirm no push or merge triggers production deployment, release, package
   publication, paid provider calls, notifications or another real effect.
7. Use a task branch and pull request targeting `main`; do not directly push to
   `main`. Force push, tag, history rewrite and branch-protection bypass remain
   forbidden.
8. Before merge, require terminal-successful configured checks, a current-head
   self-review, all required reviews and approvals satisfied at that current
   final head, no changes-requested decision, no actionable unresolved review
   thread, clean mergeability and exact final-head/manifest/hash agreement.
9. Use the repository's normal merge method. After merge, verify the merge
   commit and mainline objects from the remote and create a bounded durability
   receipt. No later phase or runtime action starts automatically.

Any failed or unverifiable precondition stops the delivery before merge.

## 6. Jenn decision surface

Jenn may choose exactly one outcome.

### A. Authorize scoped Gate 2 delivery and conditional mainline merge

Exact decision text:

```text
我确认接受 MEHS-V0.3 R5 frozen candidate
4690ce291d45339f5dbe71a793662e051629d558 的 Actual Host Smoke closeout。

我确认 Gate 1 terminal receipt
control-plane/registry/receipts/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3.json
的 SHA-256 为
e4a5b7cff752d95c4891ba966d1aa6df5d17f609659e5fc0df4637dcfdb8035c，
结果为 HOST_SMOKE_CANDIDATE_OBSERVED、failure=null、cleanup=CLEAN、
owned residue=0；Gate 1 已永久消费且不得 replay。

我确认 Fresh Independent Actual Closeout Review
control-plane/registry/reviews/2026-07-25-yellow-agents-os-phase-5d-m0d-minimum-exact-host-smoke-v0.3-r5-actual-closeout-fresh-independent-review.json
的 SHA-256 为
2e63d87301b7f23c2d933d9412756576dbb78fbab55bb03f233537b750bd4873，
结论为 PASS_NO_BLOCKER。

我授权为该固定 candidate 创建一个新的 scoped closeout delivery branch，
精确纳入 hash-bound Gate 1 decision、claim、receipt、frozen review、actual closeout
review、Gate 2 decision record、decision package，以及必要且受审的 Registry、
CURRENT_STATE、queue 与 durability projections。不得修改或重写 frozen candidate
commit 或其四个 blobs，不得混入当前工作树的其他修改或未跟踪内容。

我理解 candidate 相对 implementation line 是 1 commit / 4 additions，但在本 package
准备时相对 local main 是 20 commits、相对 observed origin/main 是 15 commits。
必须刷新 approved private origin，并审查完整 current origin/main..final_head history、
diff、manifest 与 prohibited-content 风险；不得把 mainline delivery 描述为仅四个文件。

只有在本 package Section 5 的全部 preconditions 成立时，才授权 precise commit、
push scoped task branch、创建或更新以 main 为 target 的 PR、持续跟踪 CI 与 review、
修复仅限本范围的 actionable feedback，并在 current final head 再审通过、checks
terminal-successful、所有 required reviews/approvals 在该 current final head 已满足、
无 changes requested、无 actionable unresolved threads、mergeability clean、不会触发
deploy/release/publish/provider/effect 时，使用 repository normal merge method 合并该 PR。

本授权禁止 direct push to main、force push、tag、history rewrite、branch-protection
bypass、claim/receipt 删除或改写、actual replay、processToolCall、native/N-API、
runtime activation、provider、database、production authentication、private Memory、
state-private、sensing、recording、release、deploy 或 publish。任何绑定、remote、
history、review、CI 或 effect precondition 不成立都必须在 merge 前 fail closed。

merge 成功后只可核验 remote mainline objects、创建 bounded durability receipt 并更新
必要 projections；不得自动开始下一阶段或任何 runtime/effect 工作。
```

Outcome A is the only outcome that authorizes a future scoped Git delivery loop
and conditional merge. It does not cause an automatic merge merely by existing
in this package.

### B. Revise

Jenn may identify an exact correction to the closeout evidence, delivery scope
or preconditions. The candidate, Gate 1 decision, permanent claim, terminal
receipt and completed independent reviews remain immutable. No merge occurs.

### C. Hold or reject

Retain the current state:

```yaml
Gate_1_consumed: true
Gate_1_retry_authorized: false
Gate_2_mainline_merge_authorized: false
commit_push_PR_merge_authorized: false
```

No evidence is deleted and no later phase starts.

## 7. Retained prohibitions

Until Jenn selects outcome A with current exact authorization, commit, push,
pull request creation/update, mainline merge and post-merge projection work
remain unauthorized for this Gate 2 scope.

Regardless of outcome, another actual smoke, claim or receipt deletion,
`processToolCall`, native/N-API, runtime activation, provider, database,
production authentication, private raw Memory, `state-private`, sensing,
recording, release, deploy, publish, tag, force push and history rewrite remain
outside this decision.
