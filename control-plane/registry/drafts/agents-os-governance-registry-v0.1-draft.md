# AGENTS OS Governance Registry v0.1 Draft

Status: `draft_not_active`
Date: 2026-06-30
Scope: local AGENTS OS control-plane governance

## 一句话

Governance Registry 是 AGENTS OS 的“治理部件名册”。

它不负责替 Jenn 做决定。它负责把每个治理部件登记清楚：

```text
它是谁
它管什么
谁能改
什么时候要复核
它最近有没有被验证
它不能越过哪些红线
```

## 为什么需要它

现在 AGENTS OS 已经有了这些部件：

- `life-core`
- `policy-router`
- `progressive-workflow`
- `task-envelope`
- `task-envelope validator`
- `task-envelope loop runner`
- `WORKSPACE_REGISTRY.yaml`

如果后面继续增加规则、检查器、Agent 房间、记忆流程、运行时边界，
只靠目录结构会越来越难看清：

- 哪些是正式生效的？
- 哪些只是草案？
- 哪些能自动改？
- 哪些必须 Jenn 确认？
- 哪些最近验证过？
- 哪些文件是证据？

Governance Registry 的作用，就是把这些问题变成一张本地可查的表。

## 不是什么

Governance Registry 不是：

- 不是授权书。
- 不是 Jenn 的替代决策者。
- 不是正式记忆。
- 不是外部写入入口。
- 不是 runtime / provider / plugin 调用许可。
- 不是秘密、token、私密记忆或 provider 原始响应的存放处。

Registry 只能记录治理事实和边界。它不能自动扩大权限。

## 第一版只登记什么

v0.1 先只登记本地 control-plane 里的治理部件。

暂时不登记：

- 真实密钥
- 私密记忆原文
- provider 原始响应
- 外部平台状态
- browser login state
- runtime 执行状态
- 生产部署状态

## 对象类型

第一版建议用这些对象类型：

```text
policy_module
router
workflow
task_envelope
validator
loop_runner
registry
receipt_set
review_set
runbook
boundary_doc
decision_record
golden_path
scorecard
```

大白话：

- `policy_module`：规则模块。
- `router`：判断一件事该走哪条规则的工具。
- `workflow`：做事流程。
- `task_envelope`：做事前填的单子。
- `validator`：检查结构和边界的脚本。
- `loop_runner`：把几个检查串起来的小闭环。
- `registry`：名册本身。
- `receipt_set`：收据集合。
- `review_set`：复核集合。
- `runbook`：操作手册。
- `boundary_doc`：边界说明。
- `decision_record`：记录为什么做某个治理决定。
- `golden_path`：常见事情的标准路线。
- `scorecard`：治理对象的本地体检表。

## 每个对象最少要登记什么

建议 v0.1 每个对象至少有这些字段：

```yaml
id:
name:
type:
status:
path:
owner:
scope:
authority:
green_zone:
yellow_zone:
red_zone:
inputs:
outputs:
depends_on:
evidence:
validation:
last_receipt:
last_review:
notes:
```

字段解释：

- `id`：稳定编号，方便引用。
- `name`：人能看懂的名字。
- `type`：对象类型。
- `status`：现在是 active、draft、example、deprecated，还是 blocked。
- `path`：本地路径。
- `owner`：人类 owner 和 agent steward。
- `scope`：它管什么。
- `authority`：它有没有正式效力。
- `green_zone`：可以自动做的范围。
- `yellow_zone`：只能草案、留痕、复核的范围。
- `red_zone`：不能碰的边界。
- `inputs`：它读什么。
- `outputs`：它产出什么。
- `depends_on`：它依赖哪些治理部件。
- `evidence`：它需要什么证据。
- `validation`：怎么验证它还正常。
- `last_receipt`：最近一次收据。
- `last_review`：最近一次复核。
- `notes`：额外说明。

## 状态值

建议 v0.1 先用这些状态：

```text
active
draft
example
review_needed
blocked
deprecated
archived
```

大白话：

- `active`：现在生效。
- `draft`：草案，不自动生效。
- `example`：样例，不能当真规则。
- `review_needed`：可以看，但改动或使用前要复核。
- `blocked`：被红线或风险挡住。
- `deprecated`：不推荐再用。
- `archived`：历史参考。

## 权限和颜色区

Registry 里不要只写“能不能改”，要写清楚三色区。

示例：

```yaml
green_zone:
  - read file
  - update receipt link after validation
yellow_zone:
  - add new draft entry
  - change validation rule in draft
red_zone:
  - store secret values
  - mark draft as active without review
  - authorize external writes
```

这样以后 agent 不需要猜：

```text
绿色：能直接做。
黄色：能做草案，要留痕，要回看。
红色：停，只能给预案。
```

## 第一批建议登记对象

下面不是正式登记表，只是 v0.1 草案里的第一批候选。

```yaml
objects:
  - id: life-core
    name: Life Core Policy Modules
    type: policy_module
    status: active
    path: control-plane/policies/life-core/
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: AGENTS OS local governance principles, permission model, evidence rules, boundaries.
    authority: local active reference, subject to Jenn authority and P3 hard stop.
    green_zone:
      - read modules
      - update receipts
      - fix small local documentation drift with receipt
    yellow_zone:
      - add draft policy module
      - change workflow language
      - adjust router rules with review
    red_zone:
      - bypass Jenn
      - weaken P3 hard stop
      - mark memory or identity changes as formal without confirmation
    inputs:
      - Jenn current request
      - local AGENTS.md
      - policy module files
    outputs:
      - local policy guidance
      - router inputs
    evidence:
      - receipt
      - review when boundary changes
    validation:
      - python3 control-plane/policies/life-core/test-policy-router.py
    last_receipt: control-plane/policies/life-core/receipts/
    last_review: control-plane/policies/life-core/reviews/

  - id: policy-router
    name: Life Core Policy Router
    type: router
    status: active
    path: control-plane/policies/life-core/policy-router.py
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: read-only local action classification.
    authority: advisory router, not self-authorization.
    green_zone:
      - route local action descriptions
      - run fixture tests
    yellow_zone:
      - change matching rules with receipt and review
      - add new fixture cases
    red_zone:
      - execute routed task
      - grant external write authority
      - grant secret or private-memory access
    inputs:
      - action text
      - policy-router.rules.json
      - policy-index.json
    outputs:
      - decision
      - permission_level
      - evidence
      - denied_boundaries
    evidence:
      - validation_summary
      - receipt for rule changes
    validation:
      - python3 control-plane/policies/life-core/test-policy-router.py
    last_receipt: control-plane/policies/life-core/receipts/
    last_review: control-plane/policies/life-core/reviews/

  - id: task-envelope-system
    name: Task Envelope System
    type: task_envelope
    status: active
    path: control-plane/task-envelope/
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: local pre-action clarity, boundary selection, evidence planning, and result recording.
    authority: local process helper, not final authority.
    green_zone:
      - fill local task envelope
      - validate a filled envelope
      - generate local receipt
    yellow_zone:
      - change template fields
      - change validation rules
      - add automation gates
    red_zone:
      - execute task contents automatically without separate authorization
      - store secrets
      - write external systems
      - register formal memory
    inputs:
      - task envelope markdown
      - validation-rules.json
      - policy-router output
    outputs:
      - validation result
      - gate result
      - local receipt
    evidence:
      - task receipt
      - review for boundary changes
    validation:
      - python3 control-plane/task-envelope/test-task-envelope-loop.py
      - python3 control-plane/task-envelope/validate-task-envelope.py control-plane/task-envelope/examples/2026-06-30-example-local-task-envelope-loop.md
    last_receipt: control-plane/task-envelope/receipts/
    last_review: control-plane/task-envelope/reviews/

  - id: workspace-registry
    name: Workspace Registry
    type: registry
    status: active
    path: control-plane/registry/WORKSPACE_REGISTRY.yaml
    owner:
      human: Jenn
      agent_steward: Project Agent
    scope: workspace layers, repository metadata, and active authority registry facts.
    authority: active local registry data, not remote action authorization.
    green_zone:
      - read registry metadata
      - update documentation around examples or drafts
    yellow_zone:
      - propose new registry entries
      - draft changes to layer or repository metadata
    red_zone:
      - record secret values
      - authorize remote actions
      - expand permissions without review
      - modify active authority data without explicit task scope
    inputs:
      - workspace inventory
      - extension manifests
      - governance decisions
    outputs:
      - machine-readable registry data
      - example material
    evidence:
      - receipt
      - review for permission changes
    validation:
      - YAML syntax check before active changes
    last_receipt: control-plane/registry/receipts/
    last_review: control-plane/registry/reviews/

  - id: governance-golden-paths
    name: AGENTS OS Golden Paths
    type: golden_path
    status: active
    path: control-plane/registry/GOLDEN_PATHS.md
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: standard local routes for common governance work.
    authority: active local guidance, not external or runtime authorization.
    green_zone:
      - read active guidance
      - use as local route reference
    yellow_zone:
      - revise routes
      - add new routes
      - change active guidance with receipt and review
    red_zone:
      - use as permission to bypass P3
      - use as permission for external writes or runtime execution
      - use as permission to bypass Jenn confirmation
    inputs:
      - progressive-workflow
      - task-envelope system
      - governance registry draft
    outputs:
      - standard route draft
    evidence:
      - receipt
      - review before promotion
    validation:
      - confirm draft status and stop conditions are present
    last_receipt: control-plane/registry/receipts/2026-06-30-a3c-governance-active-promotion.md
    last_review: control-plane/registry/reviews/2026-06-30-a3c-governance-active-promotion.review.md

  - id: governance-decision-record-template
    name: AGENTS OS Decision Record Template
    type: decision_record
    status: active
    path: control-plane/registry/templates/decision-record-template-v0.1.md
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: template for recording why governance decisions changed.
    authority: active local template, not final decision authority.
    green_zone:
      - read template
      - use as default template for local governance decisions
    yellow_zone:
      - adjust required sections
      - change template with receipt and review
    red_zone:
      - use decision records to bypass Jenn
      - make P3 changes without current authorization
      - record secrets or private raw memory
    inputs:
      - governance decisions
      - receipts
      - reviews
    outputs:
      - decision record draft
    evidence:
      - receipt
      - review before active use
    validation:
      - confirm template includes context, decision, risk, validation, and review conditions
    last_receipt: control-plane/registry/receipts/2026-06-30-a3c-governance-active-promotion.md
    last_review: control-plane/registry/reviews/2026-06-30-a3c-governance-active-promotion.review.md

  - id: governance-scorecard
    name: AGENTS OS Governance Scorecard
    type: scorecard
    status: active
    path: control-plane/registry/SCORECARD.md
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: basic health checks for registered governance objects.
    authority: active local check guidance, not authorization.
    green_zone:
      - read scorecard guidance
      - run local scorecard validator
    yellow_zone:
      - add scorecard rules
      - change scorecard rules with receipt and review
    red_zone:
      - treat scorecard result as final authority
      - use scorecard to grant external write or runtime permission
      - ignore secret or P3 failures
    inputs:
      - governance registry objects
    outputs:
      - pass/warn/fail findings
    evidence:
      - scorecard result
      - receipt for rule changes
    validation:
      - confirm rules catch missing id, status, red_zone, validation, and secret markers
    last_receipt: control-plane/registry/receipts/2026-06-30-a3c-governance-active-promotion.md
    last_review: control-plane/registry/reviews/2026-06-30-a3c-governance-active-promotion.review.md

  - id: governance-registry-scorecard-validator
    name: Governance Registry Scorecard Validator
    type: validator
    status: active
    path: control-plane/registry/validate-governance-registry.py
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: local structure and boundary checks for Governance Registry YAML.
    authority: read-only local checker, not authorization.
    green_zone:
      - validate local registry YAML
      - run local fixture tests
    yellow_zone:
      - change scorecard rules with receipt and review
      - add new fixture cases
    red_zone:
      - execute registry objects
      - grant external write authority
      - grant runtime or provider permission
      - ignore secret-like findings
    inputs:
      - governance registry YAML
    outputs:
      - pass/warn/fail findings
      - validation summary
    evidence:
      - validation_summary
      - receipt for rule changes
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py
    last_receipt: control-plane/registry/receipts/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.md
    last_review: control-plane/registry/reviews/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.review.md

  - id: decision-governance-control-plane-layer
    name: Governance Control-Plane Layer Decision
    type: decision_record
    status: accepted
    path: control-plane/registry/decisions/2026-06-30-governance-control-plane-layer.md
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: accepted local decision for using Golden Paths, Decision Records, Scorecard, validators, receipts, and reviews as a local governance control-plane layer.
    authority: accepted local governance decision, not external or runtime authorization.
    green_zone:
      - read accepted decision
      - use as context for local governance work
    yellow_zone:
      - supersede decision with new decision record and Jenn confirmation
      - revise related active guidance with receipt and review
    red_zone:
      - treat this decision as external authorization
      - use this decision to bypass Jenn
      - use this decision to weaken P3
      - use this decision to authorize external writes or runtime execution
    inputs:
      - governance registry draft/example
      - golden paths active guidance
      - decision record active template
      - governance scorecard active guidance
      - scorecard validator result
    outputs:
      - accepted decision record
    evidence:
      - receipt
      - review
      - scorecard result
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
    last_receipt: control-plane/registry/receipts/2026-06-30-a3c-governance-active-promotion.md
    last_review: control-plane/registry/reviews/2026-06-30-a3c-governance-active-promotion.review.md

  - id: documentation-governance
    name: AGENTS OS Documentation Governance
    type: boundary_doc
    status: draft
    path: control-plane/registry/drafts/agents-os-documentation-governance-v0.1-draft.md
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: draft governance for future large-scale AGENTS OS documentation lifecycle, ownership, indexing, freshness, canonical sources, and safety boundaries.
    authority: draft guidance only, not active authority.
    green_zone:
      - read draft
      - use as context for local documentation governance planning
    yellow_zone:
      - revise draft
      - run small documentation governance pilot
      - prepare document scorecard validator
    red_zone:
      - treat draft as active
      - bulk move or rename documents without Jenn confirmation
      - scan sensitive directories
      - record secrets, private memory raw text, or provider raw responses
      - authorize external writes or runtime execution
    inputs:
      - active Golden Paths
      - active Decision Records guidance
      - active Scorecard guidance
      - documentation governance research
    outputs:
      - documentation governance draft
      - document-object metadata example
    evidence:
      - receipt
      - review
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py
    last_receipt: control-plane/registry/receipts/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.md
    last_review: control-plane/registry/reviews/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.review.md

  - id: document-registry-example
    name: Document Registry Example
    type: registry
    status: example
    path: control-plane/registry/drafts/document-registry.v0.1.example.yaml
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: draft/example machine-readable document records for the control-plane/registry documentation governance pilot.
    authority: example only, not active authority data.
    green_zone:
      - read example registry
      - use as local fixture for the document registry validator
    yellow_zone:
      - revise example fields with receipt and review
      - add pilot records under control-plane/registry
    red_zone:
      - treat example as active authority data
      - list sensitive paths such as state-private, .env, secrets, private memory raw text, or provider raw responses
      - scan the full workspace
      - authorize external writes or runtime execution
    inputs:
      - control-plane/registry documentation paths
      - documentation governance draft
      - documentation scorecard draft
    outputs:
      - document registry example YAML
    evidence:
      - receipt
      - review
      - document scorecard result
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py
    last_receipt: control-plane/registry/receipts/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.md
    last_review: control-plane/registry/reviews/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.review.md

  - id: documentation-scorecard
    name: AGENTS OS Documentation Scorecard
    type: scorecard
    status: draft
    path: control-plane/registry/drafts/documentation-scorecard-v0.1-draft.md
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: draft health-check rules for document registry records and listed documentation paths.
    authority: draft check guidance only, not active authority.
    green_zone:
      - read draft scorecard
      - use as context for local document registry fixture tests
    yellow_zone:
      - change scorecard rules with receipt and review
      - expand pilot checks after Jenn review
    red_zone:
      - treat draft scorecard as final authority
      - use scorecard to grant external write, runtime, provider, or Memory permission
      - ignore secret-like or protected-path failures
    inputs:
      - document registry records
      - documentation governance draft
    outputs:
      - PASS/WARN/FAIL rule definitions
    evidence:
      - validation summary
      - receipt for rule changes
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
    last_receipt: control-plane/registry/receipts/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.md
    last_review: control-plane/registry/reviews/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.review.md

  - id: document-registry-validator
    name: Document Registry Validator
    type: validator
    status: active
    path: control-plane/registry/validate-document-registry.py
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: local read-only structure, boundary, path, status, freshness, and secret-like checks for Document Registry YAML.
    authority: read-only local checker, not authorization.
    green_zone:
      - validate local document registry YAML
      - run local fixture tests
    yellow_zone:
      - change documentation scorecard rules with receipt and review
      - add new fixture cases
    red_zone:
      - execute registered documents
      - scan the full workspace
      - create database or vector indexes
      - read sensitive paths
      - grant external write, runtime, provider, or Memory authority
      - ignore secret-like findings
    inputs:
      - document registry YAML
      - paths explicitly listed by document registry records
    outputs:
      - pass/warn/fail findings
      - validation summary
    evidence:
      - validation_summary
      - receipt for rule changes
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py
    last_receipt: control-plane/registry/receipts/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.md
    last_review: control-plane/registry/reviews/2026-07-01-yellow-documentation-governance-implementation-v0.1.1.review.md

  - id: task-envelope-document-registry-pilot
    name: Task Envelope Document Registry Pilot
    type: registry
    status: example
    path: control-plane/task-envelope/drafts/document-registry.v0.1.example.yaml
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: Documentation Governance Pilot 2 for task-envelope docs, examples, validator, loop runner, receipts, and reviews.
    authority: example only, not active authority data.
    green_zone:
      - validate the pilot document registry
      - use the result as local evidence for documentation governance expansion
    yellow_zone:
      - revise pilot records with receipt and review
      - expand documentation governance to one adjacent directory after review
    red_zone:
      - treat pilot registry as active workspace authority
      - scan the full workspace
      - list or read state-private, secrets, private memory raw text, or provider raw responses
      - create database/vector index without Jenn confirmation
      - authorize external writes or runtime execution
    inputs:
      - control-plane/task-envelope README
      - task-envelope template, validator, loop runner, tests, examples, receipts, and reviews
      - document-registry-validator
    outputs:
      - task-envelope document registry example YAML
      - pilot receipt
      - pilot review
    evidence:
      - document scorecard result
      - receipt
      - review
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/task-envelope/drafts/document-registry.v0.1.example.yaml
    last_receipt: control-plane/task-envelope/receipts/2026-07-01-yellow-documentation-governance-pilot-2-task-envelope.md
    last_review: control-plane/task-envelope/reviews/2026-07-01-yellow-documentation-governance-pilot-2-task-envelope.review.md

  - id: life-core-document-registry-pilot
    name: Life Core Document Registry Pilot
    type: registry
    status: example
    path: control-plane/policies/life-core/drafts/document-registry.v0.1.example.yaml
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: Documentation Governance Pilot 3 for life-core policy modules, router, rules, fixtures, tests, receipts, and reviews.
    authority: example only, not active authority data.
    green_zone:
      - validate the pilot document registry
      - use the result as local evidence for documentation governance expansion
    yellow_zone:
      - revise pilot records with receipt and review
      - prepare federated document registry design after review
    red_zone:
      - treat pilot registry as active workspace authority
      - scan the full workspace
      - list or read state-private, secrets, private memory raw text, or provider raw responses
      - create database/vector index without Jenn confirmation
      - authorize external writes or runtime execution
      - change life-core policy authority without separate review
    inputs:
      - control-plane/policies/life-core README
      - life-core policy modules, policy index, router, rules, fixtures, tests, receipts, and reviews
      - document-registry-validator
    outputs:
      - life-core document registry example YAML
      - pilot receipt
      - pilot review
    evidence:
      - document scorecard result
      - policy-router test result
      - receipt
      - review
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/policies/life-core/drafts/document-registry.v0.1.example.yaml
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/policies/life-core/validate-document-registry-coverage.py
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/policies/life-core/test-policy-router.py
    last_receipt: control-plane/policies/life-core/receipts/2026-07-01-yellow-documentation-governance-pilot-3-life-core-fix.md
    last_review: control-plane/policies/life-core/reviews/2026-07-01-yellow-documentation-governance-pilot-3-life-core-fix.review.md

  - id: federated-document-registry-draft
    name: Federated Document Registry Draft
    type: boundary_doc
    status: draft
    path: control-plane/registry/drafts/federated-document-registry-v0.1-draft.md
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: Step 4 draft design for registry-of-registries over directory-owned Document Registries.
    authority: draft guidance only, not active authority.
    green_zone:
      - read draft
      - use as context for local federation planning
    yellow_zone:
      - revise federation schema with receipt and review
      - add directory registry pilots after local validation
    red_zone:
      - treat draft as active workspace authority
      - scan the full workspace
      - create database/vector/search index without Jenn confirmation
      - authorize external writes or runtime execution
    inputs:
      - three directory Document Registry pilots
      - document-registry-validator
      - Step 4 documentation governance plan
    outputs:
      - federation draft guidance
    evidence:
      - receipt
      - review
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py
    last_receipt: control-plane/registry/receipts/2026-07-01-yellow-federated-document-registry-step-4-v0.1.md
    last_review: control-plane/registry/reviews/2026-07-01-yellow-federated-document-registry-step-4-v0.1.review.md

  - id: federated-document-registry-example
    name: Federated Document Registry Example
    type: registry
    status: example
    path: control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: Step 4 example registry-of-registries for three directory-owned Document Registry pilots.
    authority: example only, not active authority data.
    green_zone:
      - validate the federation example
      - use as local evidence for federation design
    yellow_zone:
      - revise listed registries with receipt and review
      - add a new directory registry after its own pilot passes
    red_zone:
      - treat example as active workspace authority
      - scan the full workspace
      - list or read state-private, secrets, private memory raw text, or provider raw responses
      - create database/vector/search index without Jenn confirmation
      - authorize external writes or runtime execution
    inputs:
      - control-plane/registry document registry
      - control-plane/task-envelope document registry
      - control-plane/policies/life-core document registry
    outputs:
      - federated document registry example YAML
    evidence:
      - federation validation result
      - receipt
      - review
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py
    last_receipt: control-plane/registry/receipts/2026-07-01-yellow-federated-document-registry-step-4-v0.1.md
    last_review: control-plane/registry/reviews/2026-07-01-yellow-federated-document-registry-step-4-v0.1.review.md

  - id: federated-document-registry-validator
    name: Federated Document Registry Validator
    type: validator
    status: active
    path: control-plane/registry/validate-federated-document-registry.py
    owner:
      human: Jenn
      agent_steward: Nobao
    scope: local read-only checker for Federated Document Registry YAML and explicitly listed directory registries.
    authority: read-only local checker, not authorization.
    green_zone:
      - validate federation YAML
      - run local fixture tests
    yellow_zone:
      - change federation validation rules with receipt and review
      - add new fixture cases
    red_zone:
      - execute registered directory tasks
      - scan the full workspace
      - create database/vector/search index
      - read sensitive paths
      - grant external write, runtime, provider, or Memory authority
    inputs:
      - federated document registry YAML
      - explicitly listed directory document registries
    outputs:
      - pass/warn/fail findings
      - validation summary
    evidence:
      - validation_summary
      - receipt for rule changes
    validation:
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
      - PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py
    last_receipt: control-plane/registry/receipts/2026-07-01-yellow-federated-document-registry-step-4-v0.1.md
    last_review: control-plane/registry/reviews/2026-07-01-yellow-federated-document-registry-step-4-v0.1.review.md
```

## 第一版文件形态建议

不要一上来就改 active registry。

建议先这样放：

```text
control-plane/registry/
  WORKSPACE_REGISTRY.yaml              # 已有，active workspace registry
  drafts/
    agents-os-governance-registry-v0.1-draft.md
    agents-os-governance-registry.v0.1.example.yaml
  receipts/
  reviews/
```

等草案跑过几次后，再决定要不要新增一个 active data file，例如：

```text
control-plane/registry/GOVERNANCE_REGISTRY.yaml
```

## 怎么接入现有闭环

最小接法：

1. 创建或更新治理部件时，先写 task envelope。
2. 用 policy-router 判断动作。
3. 用 task-envelope loop runner 做本地预检。
4. 如果是新增治理部件，把它作为 draft entry 记入 Governance Registry 草案。
5. 如果连续几次使用都稳定，再由 Jenn 决定是否变成 active registry data。

## 最小检查规则

当前已有本地 registry scorecard validator。v0.1 的检查项包括：

- 每个对象必须有 `id`、`type`、`status`、`path`。
- `status: active` 的对象必须有 `owner`、`scope`、`authority`。
- 任何对象都不能包含 secret 值。
- 任何对象都不能声明自己可以绕过 Jenn 或 P3。
- `red_zone` 不能为空。
- 如果对象有脚本，必须写验证方式。
- 如果对象改变权限边界，必须有 review。

## 回看节奏

建议先用轻量节奏：

```text
每新增 3 个治理部件，回看一次 Registry 是否够用。
每发生 1 次红线误判，回看一次红线字段是否清楚。
每发生 1 次 Jenn 纠偏，回看一次 owner / authority / status 字段是否清楚。
```

## v0.1 的通过标准

这个草案要算可用，至少满足：

- 能让 Jenn 一眼看懂“它登记什么”。
- 能登记现有 3-5 个治理部件。
- 能清楚区分 active / draft / example。
- 不把 registry 当成授权系统。
- 不触碰秘密、私密记忆、provider 原始响应、外部写入。
- 能被后续转换成 YAML 或 JSON 检查器。

## 当前结论

Governance Registry 应该作为 AGENTS OS 的下一层 control-plane：

```text
life-core 说明原则
policy-router 判断动作
task-envelope 约束做事
validator 检查结构
loop-runner 串起闭环
governance-registry 登记治理部件和状态
```

这份文件只是草案，不自动生效。
