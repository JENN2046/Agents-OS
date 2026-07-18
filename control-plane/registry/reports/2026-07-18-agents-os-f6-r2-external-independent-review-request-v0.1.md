# AGENTS OS F6 R2 External Independent Review Request v0.1

Date: 2026-07-18  
Applicant: Jenn  
Review type: Fresh Full Atomic Hash-Bound Independent Review  
Review unit: `F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R2_ATOMIC_BUNDLE`

## 1. Request

请对随本申请附上的 F6 R2 固定文件执行一次从零开始的、完整的、原子
的、哈希绑定的独立审查。

本次审查只能得出以下两种结果之一：

```yaml
result: PASS_NO_BLOCKER
```

或：

```yaml
result: BLOCK
```

禁止部分审查、部分接受、条件性冻结，或仅依据作者 validator / 作者自审
给出通过结论。审查者不得修改任何固定 subject、manifest 或作者证据。

## 2. Canonical binding

```yaml
review_unit: F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R2_ATOMIC_BUNDLE
atomic: true
partial_review: forbidden

subjects:
  R1_immutable: 4
  R2_new: 4
  total: 8

inputs:
  subjects: 8
  authority_inputs: 21
  author_evidence: 1
  declared_total: 30

canonical_manifest:
  path: control-plane/registry/reports/2026-07-17-agents-os-f6-r2-atomic-independent-review-package-v0.1.manifest.yaml
  sha256: ba0cd9b5b21b3bb6c2792aba55b4c6534e7d59bd145fc60952916bfc5ea0d7a3

review_instructions:
  path: control-plane/registry/reports/2026-07-18-agents-os-f6-r2-atomic-independent-review-package-v0.1.md
  sha256: 8d4db801b0e5221cf56cdca842886832094b414f83627fb5eef85ffb9ce7b693
```

本申请书只是审查委托说明，不属于 30 个 hash-bound inputs，也不改变
review unit。

## 3. Independence declaration required

请在报告中明确声明：

```yaml
reviewer:
  identity: <reviewer identity>
  independence_basis:
    - not_the_F6_R2_author_run
    - reviewed_fixed_uploaded_bytes
    - did_not_modify_subjects_or_manifest
    - did_not_treat_author_self_review_as_independent_judgment
```

如果审查者参与过 F6 R2 四个新 subjects 的作者构建、修改或自审，请停止
并披露该事实，不得签发独立结论。

## 4. Attachment completeness gate

请先计算 canonical manifest 自身 SHA-256，再按 manifest 独立重算并核对：

```yaml
manifest_sha256_verified: true
subject_hashes_verified: 8/8
authority_input_hashes_verified: 21/21
author_evidence_hashes_verified: 1/1
all_declared_input_hashes_verified: 30/30
subjects_fully_read: 8/8
authority_inputs_fully_read: 21/21
```

任何 mandatory input 缺失、不可读取或哈希不一致，都不能产生正式语义
PASS。请返回：

```yaml
result: BLOCK
block_reason: PACKAGE_INCOMPLETE_OR_HASH_MISMATCH
```

不要使用工作区中同名但未被 manifest 绑定的替代文件。

## 5. Required fixed-command reproduction

请逐字执行 manifest 中的四个 `validator_commands`，并分别记录退出状态和
结果：

```yaml
fixed_commands:
  R1_validator: PASS_or_FAIL
  R1_builder_fixture_byte_equality: PASS_or_FAIL
  R2_validator: PASS_or_FAIL
  R2_builder_fixture_byte_equality: PASS_or_FAIL
  passed: <n>/4
```

固定命令全部通过只是必要条件，不足以单独支持独立 PASS。

## 6. Required semantic determinations

请独立确认以下结论由原始对象关系推导，而不是依赖作者预填结论：

1. 十个 normative schemas 都有闭合字段集合、类型、enum、nullable、整数
   范围、canonical instance 和完整 cross-field matrix。
2. `PASSED` 只能在 exact current Validation authority 和 exact assessed
   evidence set 成立时产生。
3. Requirement attempt 与 completion barrier 使用完全相同的 Task
   candidate 和 dependency context。
4. Task `VERIFYING` 来自 exact current F1 owner assessment，而不是调用方
   可自行提供的字符串。
5. 所有 owner assessment 都消费 exact subject ref、revision、fingerprint、
   current head 和 observation barrier。
6. Requirement predecessor、provenance、Command、Event 和来源 authority 图
   闭合；branch、gap、cycle、缺失 predecessor 或错误来源均 fail closed。
7. Jenn waiver 绑定 exact immutable Jenn decision、Requirement revision、
   Command、Event、waivability、有效区间和 current owner assessment。
8. 跨对象 Event 顺序完整且可执行验证；任何缺失、冲突或不可比较关系都
   fail closed。
9. `evidence_refs` 等于被本次 attempt 实际验证的 sorted unique exact
   evidence set；不得增加未评估 evidence。
10. Carry-forward 只能直接回到 original fresh `PASSED` attempt，不能形成
    carry-forward 链式来源。
11. Effectful Requirement 必须绑定 exact F5 subject；`APPLIED_CURRENT` 只
    是 supporting evidence，不能直接创建 Validation `PASSED`。
12. Completion eligibility 在同一 barrier 上重新确认 candidate、
    dependencies、Requirement Set、nonterminal counts、F5 blocker 和 guard
    assessment；任一变化都停止完成。
13. Synthetic evidence 和 prospective interfaces 不可成为 runtime 或
    production authority。
14. F6 不重新实现 F1/F2/F3/F5，也不创建第二权限、身份、完成或 effect
    authority。

## 7. Independent coordinated consistency probes

除固定 validator 中已有用例外，请独立构造并实际执行完整传播所有相关
引用与摘要的协调一致性样例。至少覆盖：

1. 同时替换 candidate、dependency、attempt 和 completion assessment，
   检查 context 已改变时是否仍可能得到 `ELIGIBLE`。
2. 同时替换 Jenn decision、Command、Event、waiver 和 owner assessment，
   检查 waiver 是否仍精确绑定其根权威。
3. 修改 Requirement predecessor / provenance 图，并同步更新所有依赖
   reference 和 fingerprint，分别覆盖 branch、gap、cycle 与错误来源。
4. 对 evidence 做增加、删除、重复和重排，同时同步 evidence-set
   fingerprint 与 assessment，确认 exact set 约束仍成立。
5. 修改 carry-forward original root 或 effectful F5 delivery subject，并
   保持表面 result 标签不变，确认 reducer 仍从真实关系得出结论。
6. 构造 decision output 的 cross-field 矛盾并同步更新 section/root 摘要，
   确认 closed output matrix 拒绝该组合。

每个样例都应记录：

```yaml
- id: <stable id>
  objects_changed: []
  dependent_refs_and_fingerprints_propagated: true
  execution_completed_without_exception: true
  expected_result: REJECT
  actual_result: REJECT_or_ACCEPT
  rejection_layer: <target semantic rule>
  rejected_only_because_of_stale_outer_hash: false
```

不得把以下情况计作语义拒绝成功：

- dependent reference 或 fingerprint 未同步传播；
- mutation / probe 本身执行异常；
- fixture 中预填 expected value 没有同步；
- 仅因陈旧外层摘要先失败，而目标语义规则从未被执行。

## 8. Count reporting rule

请分开报告三个固定计数：

```yaml
rejection_accounting:
  R1_fixed_mutations:
    executed: 32
    rejected: 32
  R1_independent_regressions:
    executed: 18
    rejected: 18
  R2_additional_negatives:
    executed: 12
    rejected: 12
  fixed_total:
    executed: 62
    rejected: 62
```

作者输出中的：

```text
total_R2_mutations_rejected = 30
```

只表示 `18 + 12`，不是全量拒绝总数。请勿把 `30` 描述为全部执行数。
独立 reviewer 新增的 coordinated probes 应另行计数，不能混入固定 `62`。

## 9. Finding requirements

若结果为 `BLOCK`，每个 finding 必须包含：

```yaml
- id: F6-R2-IR-<severity><number>
  severity: blocker_or_major_or_minor
  affected_subjects: []
  rule_violated: <exact contract rule>
  reproducible_input_difference: <concise description>
  dependent_updates_completed: true
  observed_result: <actual result>
  required_correction: <narrow correction>
  scope_limit: <what must not be added>
```

实现偏好、数据库布局、Rust/JavaScript 模块、性能、provider transport、
生产 authentication 或 F7 设计不能仅因尚未实现而成为 F6 blocker。只有
新的、独立的、可复现的合同安全或确定性反例才可要求 R3。

## 10. Required final report format

请返回一份完整 YAML 或 Markdown 内嵌 YAML，建议文件名：

```text
2026-07-18-yellow-agents-os-f6-r2-full-atomic-independent-review.yaml
```

最低结构：

```yaml
schema_version: agents-os.hash-bound-independent-review.v0.1

reviewer:
  identity: <identity>
  independence_basis: []

review_unit:
  id: F6_VALIDATION_REQUIREMENT_CURRENT_DECISION_V0_1_R2_ATOMIC_BUNDLE
  atomic: true
  partial_review: forbidden
  subject_count: 8

package_integrity:
  manifest_sha256: ba0cd9b5b21b3bb6c2792aba55b4c6534e7d59bd145fc60952916bfc5ea0d7a3
  manifest_sha256_verified: true_or_false
  hashes_verified: 30/30
  subjects_fully_read: 8/8
  authority_inputs_fully_read: 21/21
  author_evidence_fully_read: 1/1

fixed_commands:
  passed: 4/4

rejection_accounting:
  R1_fixed_mutations: {executed: 32, rejected: 32}
  R1_independent_regressions: {executed: 18, rejected: 18}
  R2_additional_negatives: {executed: 12, rejected: 12}
  fixed_total: {executed: 62, rejected: 62}
  independent_coordinated_probes:
    executed: <n>
    rejected: <n>
    unexpectedly_accepted: <n>
    execution_exceptions: 0

result: PASS_NO_BLOCKER_or_BLOCK
findings:
  blocker: <n>
  major: <n>
  minor: <n>
  unresolved: <n>

requires_R3: true_or_false
F6_acceptance_ready: true_or_false
F6_accepted: false
F6_frozen: false
F7_started: false

implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
database_service_provider_or_effect_authorized: false
Git_delivery_authorized: false
```

如果 `PASS_NO_BLOCKER`，请明确：该结果只使 F6 R2 八 subject 原子 bundle
具备提交 Jenn 冻结裁决的资格；它不自动接受或冻结 F6，也不启动 F7。

## 11. Files Jenn should attach

请附上：

1. 本申请书；
2. 第 2 节列出的 review instructions；
3. canonical manifest；
4. manifest `review_unit.subjects` 中的 8 个文件；
5. manifest `authority_inputs` 中的 21 个文件；
6. manifest `author_evidence` 中的 1 个文件。

如果使用 ZIP，请保留 manifest 中的相对路径，避免重命名；ZIP 哈希可以
作为传输完整性的附加证据，但不能替代 manifest 内 30 个逐文件哈希。

禁止附加 secrets、credentials、真实密钥、token、cookie、生产配置、
原始 provider 响应、`state-private/`、`memory/`、`ops/reports/` 或
`execution/agents-os-workbench/records/` 内容。

## 12. Current non-authorization state

```yaml
independent_review_result: NOT_RUN
F6_acceptance_ready: false
F6_accepted: false
F6_frozen: false
F7_started: false

implementation_authorized: false
runtime_activation_authorized: false
production_authentication_authorized: false
database_change_authorized: false
service_start_authorized: false
provider_execution_authorized: false
real_Task_Run_Validation_Event_waiver_completion_mutation_authorized: false
Git_delivery_authorized: false
```
