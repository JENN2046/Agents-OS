# AGENTS OS Documentation Governance v0.1 Draft

Status: `draft_not_active`
Date: 2026-06-30
Scope: future large-scale AGENTS OS documentation governance

## 一句话

Documentation Governance 是 AGENTS OS 的“文档家政系统”。

它解决的不是“写不写文档”，而是：

```text
文档太多以后，怎么找得到？
怎么知道哪份是真的？
怎么知道谁负责？
怎么知道有没有过期？
怎么知道草案有没有被当成正式文件？
怎么让工具和 Agent 都能读懂？
```

## 为什么现在需要

未来 AGENTS OS 会有很多项目、工具、Agent、流程、插件、运行时、记忆协议、业务系统和历史材料。

如果没有文档治理，文档量越大，问题越明显：

```text
同一件事有三份说明，不知道哪份是准的。
旧文档没有废弃标记，被新 agent 误用。
草案被当成 active。
README 太长，找不到真正入口。
项目很多，但没有 owner。
文档过期了没人知道。
文档里混进 secret、private memory 或 provider raw response。
```

所以 AGENTS OS 需要一套面向超大文档量的本地治理规则。

## 不是什么

Documentation Governance 不是：

- 不是写作风格美化指南。
- 不是让所有文档都变复杂。
- 不是要求每个小说明都走重流程。
- 不是秘密、私密记忆、provider 原始响应的存放处。
- 不是外部发布流程。
- 不是正式 Memory 注册流程。
- 不是替 Jenn 做最终判断。

它是本地文档生命周期、入口、状态、归属和检查规则。

## 参考原则

这份草案吸收几类成熟做法：

```text
文档分型：教程、怎么做、参考、解释，不混成一团。
docs-as-code：文档像代码一样有路径、owner、review、检查。
目录/元数据：文档必须能被 catalog 或 registry 找到。
模板化：常见文档用模板，减少每次从零写。
新鲜度：重要文档要有 last_reviewed / review_by。
```

## 文档分型

AGENTS OS 文档先分成这些类型：

```text
index
overview
tutorial
how_to
runbook
reference
explanation
decision_record
policy
registry
contract
schema
template
example
receipt
review
incident_review
archive_note
```

大白话：

- `index`：入口地图，告诉人去哪里。
- `overview`：整体说明。
- `tutorial`：带学习顺序的入门教程。
- `how_to`：一步一步怎么做。
- `runbook`：遇到某类操作怎么跑。
- `reference`：查字段、命令、接口、规则。
- `explanation`：解释为什么。
- `decision_record`：记录为什么这样决定。
- `policy`：规则。
- `registry`：名册。
- `contract`：接口约定。
- `schema`：机器结构。
- `template`：模板。
- `example`：样例，不能当 active。
- `receipt`：做事收据。
- `review`：复核记录。
- `incident_review`：误判/事故复盘。
- `archive_note`：历史归档说明。

## 文档状态

建议 v0.1 使用这些状态：

```text
draft
review_needed
active
accepted
superseded
deprecated
archived
example
blocked
```

状态解释：

- `draft`：草案，不生效。
- `review_needed`：能看，但需要复核。
- `active`：当前默认使用。
- `accepted`：已接受的 decision 或结论。
- `superseded`：被新文档替代。
- `deprecated`：不推荐再用，但还未归档。
- `archived`：历史参考。
- `example`：样例，不能当规则。
- `blocked`：被红线或风险挡住。

## 文档层级

为了未来超大规模，文档要分层：

```text
L0 workspace map
L1 domain/project index
L2 system/component docs
L3 operation docs
L4 evidence docs
L5 archive docs
```

大白话：

- `L0`：整个 AGENTS OS 的总地图。
- `L1`：某个项目/领域入口。
- `L2`：某个系统或组件的说明。
- `L3`：具体怎么操作。
- `L4`：收据、复核、验证、decision。
- `L5`：历史档案。

## 文档元数据

重要文档必须在开头写最小元数据：

```yaml
Doc ID:
Status:
Doc Type:
Scope:
Owner:
Agent steward:
Canonical path:
Last reviewed:
Review by:
Source of truth:
Supersedes:
Superseded by:
Related:
Security boundary:
```

小文档可以不写完整 front matter，但至少要能从目录、文件名、父 README 判断：

```text
它是什么
是不是 active
归谁管
能不能被当成规则用
```

## 目录规则

每个大目录至少要有一个 `README.md`，说明：

```text
这个目录放什么
不能放什么
active 文件在哪里
draft 在哪里
example 在哪里
receipt/review 在哪里
谁负责
怎么验证
```

每个复杂项目建议有：

```text
README.md
docs/
docs/index.md
docs/decisions/
docs/runbooks/
docs/reference/
docs/examples/
docs/archive/
receipts/
reviews/
```

但小项目不要强制过度拆分。

## Canonical Source 规则

同一件事只能有一个 canonical source。

如果有旧文档，旧文档必须标：

```text
superseded_by: <new path>
```

如果有摘要，摘要必须指向源文档：

```text
source_of_truth: <canonical path>
```

不允许三份文档都看起来像正式版本。

## 文档生命周期

默认路线：

```text
draft
-> review_needed
-> active / accepted
-> superseded / deprecated
-> archived
```

不是所有文档都要走全流程。

轻量规则：

```text
小说明：直接 active，但要在 README 里有入口。
治理规则：draft -> review -> active。
重要决定：draft -> accepted。
样例：example，不升 active。
收据/复核：evidence，不当规则。
历史材料：archive，只读参考。
```

## 文档新鲜度

文档按重要性分三档：

```text
critical
important
ordinary
```

建议回看节奏：

```text
critical：每次相关边界变化时回看。
important：每 3-6 个月或连续使用 3 次后回看。
ordinary：需要时回看。
```

过期信号：

```text
引用的路径不存在。
命令跑不通。
状态和 README 冲突。
被新 decision 替代。
Jenn 纠偏过。
Agent 误用过。
```

## 文档索引

未来文档量很大时，不能靠 `find` 乱搜。

建议有两类索引：

```text
人读索引：README.md / docs/index.md
机器索引：document registry YAML/JSON
```

每个文档对象可以登记为：

```yaml
id:
title:
doc_type:
status:
scope:
canonical_path:
owner:
agent_steward:
source_of_truth:
supersedes:
superseded_by:
related:
last_reviewed:
review_by:
security_boundary:
validation:
```

## 文档体检

未来应该有 Documentation Scorecard。

第一版检查：

```text
DOC-001: active 文档缺 owner -> FAIL
DOC-002: active 文档缺 status -> FAIL
DOC-003: active 文档缺 canonical path -> FAIL
DOC-004: draft/example 被描述成 active -> FAIL
DOC-005: superseded 文档缺 superseded_by -> WARN
DOC-006: 文档引用不存在路径 -> WARN/FAIL
DOC-007: 重要文档缺 last_reviewed -> WARN
DOC-008: 文档含 secret-like pattern -> FAIL
DOC-009: 文档放错目录 -> WARN
DOC-010: README 没说明目录边界 -> WARN
```

## 超大规模策略

当文档非常庞大时，用这几个策略控住：

### 1. 分区

```text
control-plane docs
runtime docs
project docs
tool docs
agent docs
memory docs
archive docs
evidence docs
```

### 2. 分热度

```text
hot：常用 active 文档
warm：偶尔查的 reference
cold：历史但未归档
archive：只读历史
```

### 3. 分入口

```text
每个大区只维护一个主入口。
主入口不要写成百科全书，只负责导航。
```

### 4. 分责任

```text
每个 active 文档必须有 owner。
owner 可以是 Jenn / Nobao / Project Agent / specific project steward。
```

### 5. 分证据

```text
决策看 decisions/
做事看 receipts/
复核看 reviews/
操作看 runbooks/
规则看 policy/
接口看 contracts/
```

## 命名规则

建议：

```text
active 指南：UPPER_SNAKE.md 或 clear-name.md
decision：YYYY-MM-DD-short-name.md
draft：name-v0.1-draft.md 或 YYYY-MM-DD-name.draft.md
receipt：YYYY-MM-DD-scope-action.md
review：YYYY-MM-DD-scope-action.review.md
example：YYYY-MM-DD-example-name.md 或 name.example.yaml
archive：保留原名，加 archive note
```

## 引用规则

文档里引用其他文档时：

```text
优先引用 canonical path。
不要只写“看上面那个文件”。
不要引用 state-private、secret、private memory raw text。
引用 draft 时要写明是 draft。
引用 example 时要写明不能当 active。
```

## 安全边界

任何文档都不能包含：

```text
密钥
token
cookie
private key
真实 .env 内容
私密记忆原文
provider 原始响应
数据库 dump
浏览器登录状态
个人身份文件
```

如果文档需要说明这些东西，只能写：

```text
变量名
占位符
路径级别边界
安全预案
```

不能写真实值。

## 和现有 AGENTS OS 治理的关系

```text
Golden Paths：告诉文档治理相关动作怎么走。
Decision Records：记录文档规则为什么变化。
Scorecard：检查治理对象。
Documentation Governance：检查和组织大量文档。
Receipts/Reviews：证明文档治理动作发生过、被看过。
```

## v0.1 落地建议

先不要全工作区扫描。

第一阶段只做：

```text
1. 把本草案保留为 draft。
2. 做一个 document-record YAML 样例。
3. 后续选 control-plane/registry 作为试点。
4. 给 registry 目录文档做第一轮 document scorecard。
5. 稳定后再扩展到 control-plane/task-envelope。
6. 最后再扩展到全 workspace。
```

## Jenn 需要确认前，不做什么

```text
不创建全工作区 document registry。
不批量移动/重命名文档。
不批量改 front matter。
不扫描敏感目录。
不读取 state-private。
不写外部平台。
不把这份草案当 active。
```

## v0.2 试点实现

2026-07-01 已先在 `control-plane/registry` 做一个小试点：

```text
document-registry.v0.1.example.yaml：登记这一区域的关键文档。
documentation-scorecard-v0.1-draft.md：定义文档体检规则。
validate-document-registry.py：只读检查 document registry。
test-document-registry-validator.py：跑 fixture 测试。
templates/docs/：放常见文档模板。
```

这个试点仍然不做：

```text
不创建全工作区 document registry。
不创建数据库。
不创建向量索引。
不批量移动/重命名文档。
不扫描敏感目录。
不读取 state-private。
不把草案或 example 当 active authority。
```

## Pilot 2：task-envelope

2026-07-01 扩展到第二个真实目录：

```text
control-plane/task-envelope/drafts/document-registry.v0.1.example.yaml
```

这次试点验证的是：

```text
同一套 Document Registry + Documentation Scorecard + validator
能不能检查另一个真实 control-plane 子系统。
```

边界仍然不变：

```text
不做全 workspace document map。
不创建数据库。
不创建向量索引。
不扫描敏感目录。
不读取 state-private。
不把 pilot registry 当 active authority。
```

## Pilot 3：life-core

2026-07-01 扩展到规则核心目录：

```text
control-plane/policies/life-core/drafts/document-registry.v0.1.example.yaml
```

这次试点验证的是：

```text
Document Registry 能不能覆盖 AGENTS OS 的核心规则文档，
包括 policy modules、policy-index、policy-router、rules、fixtures、tests、receipts、reviews。
```

边界仍然不变：

```text
不做全 workspace document map。
不创建数据库。
不创建向量索引。
不扫描敏感目录。
不读取 state-private。
不把 pilot registry 当 active authority。
不通过文档治理改变 life-core 权限本身。
```

## Step 4：Federated Document Registry

三个目录级 pilot 通过后，2026-07-01 进入第 4 步：

```text
control-plane/registry/drafts/federated-document-registry-v0.1-draft.md
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
control-plane/registry/validate-federated-document-registry.py
```

第 4 步的思路：

```text
每个大目录有自己的 document-registry.v0.1.example.yaml。
中央 federation 只登记这些目录级 registry。
validator 只检查 federation 里明确列出的 registry。
```

这一步仍然不做：

```text
不做全 workspace document map。
不创建数据库。
不创建搜索索引。
不创建向量索引。
不扫描敏感目录。
不读取 state-private。
不把 federation 当 active authority。
```

## 当前状态

```text
draft_not_active
已有 control-plane/registry 小试点、control-plane/task-envelope Pilot 2、control-plane/policies/life-core Pilot 3、Federated Document Registry Step 4
```
