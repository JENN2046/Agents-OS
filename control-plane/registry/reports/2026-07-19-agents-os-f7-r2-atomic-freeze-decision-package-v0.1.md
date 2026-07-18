# AGENTS OS F7 R2 Atomic Freeze Decision Package v0.1

Date: 2026-07-19  
Status: `READY_FOR_JENN_ATOMIC_DECISION`  
Owner: Jenn  
Agent steward: Nobao

## 1. Decision-ready result

The fresh full atomic hash-bound independent review returned
`PASS_NO_BLOCKER` for the complete R1-R2 F7 contract bundle.

```yaml
review_result: PASS_NO_BLOCKER
blocker_count: 0
major_count: 0
minor_count: 0
unresolved_contract_ambiguity_count: 0
requires_R3: false
F7_atomic_freeze_gate: SATISFIED_FOR_JENN_DECISION
automatic_acceptance: forbidden
F7_accepted: false
F7_frozen: false
F8_started: false
```

Independent review:

```text
control-plane/registry/reviews/2026-07-19-yellow-agents-os-f7-r2-codex-external-independent-review.yaml
SHA-256 79d84b9231490d61a93c88574d2e6be6ef25a128f407c9c9c81a63136fb44647
bytes 5973
encoding ASCII with LF line endings
```

The reviewer recomputed all 44 manifest-bound hashes, fully read all eight
subjects and 35 authority inputs, reproduced both fixture byte streams, ran
both fixed validators and independently executed fourteen fully re-signed
attacks. All fourteen attacks were rejected by their intended semantic or
boundary checks. No blocker, major, minor or unresolved ambiguity remained.

The review environment blocked only trailing cleanup of temporary files under
`/tmp`. The byte generation and comparison steps passed, and no review subject
or workspace object was modified by that limitation.

## 2. Atomic acceptance unit

```yaml
id: F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R2_ATOMIC_BUNDLE
atomic: true
partial_acceptance: forbidden
subject_count: 8
precedence:
  - R2_explicit_replacements
  - R1_all_other_clauses
```

Canonical manifest:

```text
control-plane/registry/reports/2026-07-19-agents-os-f7-r2-atomic-independent-review-package-v0.1.manifest.yaml
SHA-256 d2fc34cd8df70d1a960e373606f6c53468e6020b8a8087b551561ebf6a032d35
```

The eight subjects are exactly the R1 and R2 contract/amendment,
deterministic builder, synthetic fixture and offline semantic validator
quartets listed in that manifest. Only those fixed subject bytes, interpreted
under the declared precedence, form the acceptance unit.

The manifest, author self-review, independent reviews, decision package,
dispositions, receipts, queues and future implementations are evidence or
governance projections, not acceptance subjects.

## 3. Freeze meaning

Acceptance freezes the F7 minimum Home Domain semantics under R1-R2
precedence, including:

```text
the closed twenty-class semantic inventory and exact authority profiles;
the separation of upstream facts, Home candidates, policy authority, deferred owners and projections;
immutable Home candidate revision envelopes and same-revision non-resigning;
the nonpromotion reducer, reason precedence and exact allowed candidate formations;
the mandatory rejection and deferral boundaries for identity, relationship, Session, Memory, Task, Command, sensing and policy;
the separation of presence policy, consent and physical sensing state;
the rule that relationship, narrative, trust or subjective memory cannot expand authority;
the exact ordered twenty-case decision inventory and its complete raw-input and derived-decision anchors;
the synthetic, nonauthority, nonruntime and non-effectful HD-M0 proof boundary.
```

No R3 is required for the reviewed F7 semantic core. Any future semantic
change requires a new revision, fresh full atomic review and a new Jenn
decision. Partial acceptance or in-place repair is forbidden.

The frozen result does not create a Home service, Memory, Task, Command,
relationship, identity fact, consent, sensing state, policy revision or
external effect.

## 4. Explicit non-authorization

Accepting and freezing F7 does not:

- start F8;
- authorize implementation in Rust, Python, JavaScript or another language;
- create or mutate a Home fact, candidate, Memory, Task, Command,
  relationship, identity, consent, sensing state, policy revision, database
  row or provider record;
- read private raw Memory or start sensing, recording, a Resident, Worker,
  Host, executor, runtime, service, transport, provider, process, device,
  file or physical effect;
- authorize runtime activation, production authentication, credentials, keys,
  cryptography, provider calls, public API, MCP expansion or external effects;
- authorize commit, push, PR, merge, tag, release, deploy, publish or
  production delivery;
- treat a synthetic fixture, validator PASS, review or decision package as
  runtime authority.

F8, every implementation/runtime profile and every real Home, Memory, sensing
or effect path remain separate Jenn-owned gates.

## 5. Required closeout after acceptance

If Jenn chooses A, the closeout may create only:

```text
one immutable acceptance/freeze decision record binding the manifest and review SHA-256 values
Document Registry and CURRENT_STATE projections
one active-queue reconciliation
one closeout receipt
full manifest, review and subject hash re-verification
local governance validation
```

The closeout must not start F8 or perform implementation, runtime, database,
authentication, provider, sensing, recording, private raw Memory access, real
effect, commit, push, PR, merge, release, deploy, publish or tag actions.

## 6. Jenn decision surface

Jenn may choose exactly one outcome.

### A. Accept and freeze

Exact decision text:

```text
我确认接受并冻结 AGENTS OS F7 Home Domain Minimum Semantics v0.1 的完整原子单元
F7_HOME_DOMAIN_MINIMUM_SEMANTICS_V0_1_R2_ATOMIC_BUNDLE。

接受对象仅为 manifest
control-plane/registry/reports/2026-07-19-agents-os-f7-r2-atomic-independent-review-package-v0.1.manifest.yaml
中列明的 R1-R2 共 8 个 subjects，并按 R2 explicit replacements、R1 all
other clauses 的顺序解释；该 manifest 的 SHA-256 为
d2fc34cd8df70d1a960e373606f6c53468e6020b8a8087b551561ebf6a032d35。

我确认 fresh full atomic independent review
control-plane/registry/reviews/2026-07-19-yellow-agents-os-f7-r2-codex-external-independent-review.yaml
的 SHA-256 为
79d84b9231490d61a93c88574d2e6be6ef25a128f407c9c9c81a63136fb44647，
结论为 PASS_NO_BLOCKER，requires_R3=false。

我确认本次冻结的是 F7 R1-R2 的 Home Domain minimum semantics、二十类
semantic class 与 authority profile、immutable candidate revision、nonpromotion
reducer、relationship/presence/session/Memory/Task/Command/sensing/policy
边界，以及固定有序的二十案例证明目录；不是 implementation、runtime、
production readiness、真实 Home、Memory、Task、Command、relationship、
consent、sensing、recording、provider call 或 physical effect。

禁止部分接受。manifest、self-review、independent review、decision package、
disposition、receipt 与 queue 均不属于接受对象。

本决定不启动 F8，不授权 implementation、Rust、Python、JavaScript、database、
index、cache、queue、transport、Resident、Worker、Host、executor、validator、
runtime activation、production authentication、credential、key、cryptography、
private raw Memory access、sensing、recording、service、provider、device、file、
process、physical effect、public API、MCP、commit、push、PR、merge、tag、
release、deploy 或 publish。请据此创建不可变 acceptance/freeze decision
record，并只做必要的 Document Registry、CURRENT_STATE、Active Work Queue、
receipt 与 validation 投影更新。
```

### B. Revise

Jenn may identify one or more exact findings. The eight fixed subjects and
independent review remain immutable; a revision starts R3 and a fresh review
from zero. Partial repair or partial acceptance is forbidden.

### C. Reject

Jenn may reject the bundle. No acceptance or freeze record is created. F7
remains started but not accepted or frozen, and F8 remains unstarted.

## 7. Reproduction

Before closeout, recompute the manifest SHA-256, all 44 bound input hashes, all
eight subject hashes and the independent-review SHA-256. Any mismatch
invalidates this decision surface and requires a stop.
