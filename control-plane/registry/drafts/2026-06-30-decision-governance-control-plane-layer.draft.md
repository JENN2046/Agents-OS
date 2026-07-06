# Decision Record: AGENTS OS Governance Control-Plane Layer

Decision ID: `decision-governance-control-plane-layer-2026-06-30`
Status: `draft`
Date: 2026-06-30
Scope: `control-plane/registry/`
Owner: Jenn
Agent steward: Nobao

Promotion note:

```text
Jenn accepted this decision for local governance control-plane scope on
2026-06-30. The accepted copy is:
control-plane/registry/decisions/2026-06-30-governance-control-plane-layer.md

This draft is retained as the historical source.
```

## 一句话

AGENTS OS 需要一层本地治理 control-plane，把规则、路线、检查器、证据和回看对象登记清楚。

## 背景

AGENTS OS 已经从愿景进入本地可执行雏形。

当前已经有：

```text
life-core
policy-router
progressive-workflow
task-envelope
task-envelope validator
task-envelope loop runner
governance registry draft
golden paths draft
decision record template draft
governance scorecard draft
governance scorecard validator
```

如果继续只靠文件目录和聊天记忆，后面会越来越难看清：

```text
哪些是 active？
哪些只是 draft？
哪些能自动改？
哪些必须 Jenn 确认？
哪些最近验证过？
某个规则为什么变成这样？
```

所以需要一层本地治理 control-plane，把这些东西登记、检查、留痕、回看。

## 目标

```text
1. 让治理部件有名册，不靠猜。
2. 让常见事情有路线，不每次重想。
3. 让重要决定有原因，不只留下结果。
4. 让治理对象能被本地检查器检查。
5. 保持草案和 active 的边界清楚。
```

## 不解决什么

```text
1. 不授权外部写入。
2. 不授权 runtime/provider/plugin 调用。
3. 不注册正式 Memory。
4. 不改 Jenn 身份、关系、家规或生命内核。
5. 不把草案自动升成 active。
```

## 看过的选择

### 方案 A：继续只用普通文档和 receipt

好处：

- 很快。
- 文件少。
- 不需要新结构。

坏处：

- 越做越难知道哪些规则正在生效。
- 草案、样例、active 容易混在一起。
- 后续 agent 只能靠读全文判断，容易误判。
- 很难做机器检查。

### 方案 B：直接把 Governance Registry 做成 active authority data

好处：

- 结构一步到位。
- 后续可以直接引用。

坏处：

- 太快。
- 容易把草案误认为正式规则。
- 可能让 registry 看起来像授权系统。
- 需要 Jenn 明确确认，不适合自动推进。

### 方案 C：先做本地草案层，再逐步用检查器验证

好处：

- 能推进。
- 不直接生效。
- 能留下 receipt/review。
- 能用 scorecard validator 先检查结构。
- 给 Jenn 留出回看和确认空间。

坏处：

- 多一层 draft 文件。
- 还需要后续决定哪些内容能升 active。

## 最终决定

```text
先采用方案 C。

Governance Registry、Golden Paths、Decision Record、Scorecard 先作为本地草案层运行。
Scorecard validator 可以作为本地只读检查器使用。
任何草案升 active 之前，需要单独 decision record、review 和 Jenn 明确确认。
```

## 为什么这样定

```text
AGENTS OS 现在最需要的是“能跑起来，但不越界”。

只写愿景太慢。
直接变正式太快。
先用草案 + 检查器 + receipt + review，是中间路线。

这样 Nobao 可以继续建设，Jenn 也能看见系统怎么长出来。
```

## 会改变什么

```text
1. 后续新增治理部件时，优先登记进 Governance Registry 草案。
2. 常见治理动作优先参考 Golden Paths 草案。
3. 重要治理变化优先写 Decision Record 草案。
4. Registry 对象可以用 Scorecard validator 做本地结构检查。
5. receipt/review 继续作为证据链。
```

## 不会改变什么

```text
1. Jenn 仍是最终决策者。
2. P3 Hard Stop 不变。
3. 草案不会自动变 active。
4. Registry 不授权外部写入。
5. Scorecard 不授权执行。
6. 不碰密钥、私密记忆、provider 原始响应。
7. 不注册正式 Memory。
8. 不调用 runtime/provider/plugin。
```

## 颜色区判断

```text
绿色区：
- 读取这些草案。
- 跑本地 scorecard validator。
- 补 receipt/review。

黄色区：
- 修改草案结构。
- 新增 registry 对象。
- 调整 scorecard 规则。
- 准备草案升 active 的 decision record。

红色区：
- 未经 Jenn 确认把草案升 active。
- 用 registry 或 scorecard 授权外部写入。
- 用草案绕过 P3、秘密、私密记忆、provider 原始响应、正式 Memory。
```

## 风险

```text
1. 文件增多后，Jenn 可能觉得治理层太重。
2. 草案和 active 的边界如果写不清，后续 agent 可能误用。
3. Scorecard validator 只能检查结构，不能证明语义完全正确。
4. 如果每个小改动都写 decision record，会拖慢建设。
```

## 验证方式

```text
1. 跑 Governance Registry scorecard validator。
2. 跑 scorecard validator fixture tests。
3. 跑 task-envelope loop fixture tests。
4. 跑 life-core policy-router fixture tests。
5. 检查 draft decision 被登记为 draft，而不是 accepted。
```

## 回看条件

```text
1. Jenn 纠偏一次。
2. 草案准备升 active。
3. Governance Registry 对象超过 12 个。
4. Scorecard validator 出现误判。
5. 有 agent 把 draft 当 active 使用。
6. 连续 3 次使用这套流程后。
```

## 证据链接

```text
Task envelope: not created for this small local draft step
Receipt: control-plane/registry/receipts/2026-06-30-yellow-first-decision-record-draft.md
Review: control-plane/registry/reviews/2026-06-30-yellow-first-decision-record-draft.review.md
Validation: scorecard validator, scorecard tests, task-envelope loop tests, policy-router tests
```

## 当前结论

`draft`
