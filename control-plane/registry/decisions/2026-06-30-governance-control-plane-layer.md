# Decision Record: AGENTS OS Governance Control-Plane Layer

Decision ID: `decision-governance-control-plane-layer-2026-06-30`
Status: `accepted`
Date: 2026-06-30
Scope: `control-plane/registry/`
Owner: Jenn
Agent steward: Nobao
Accepted by: Jenn confirmation in current Codex thread

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
golden paths
decision record template
governance scorecard
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

坏处：

- 越做越难知道哪些规则正在生效。
- 草案、样例、active 容易混在一起。
- 很难做机器检查。

### 方案 B：直接把 Governance Registry 做成 active authority data

好处：

- 结构一步到位。

坏处：

- 太快。
- 容易把草案误认为正式规则。
- 可能让 registry 看起来像授权系统。

### 方案 C：先做本地草案层，再逐步用检查器验证

好处：

- 能推进。
- 不直接生效。
- 能留下 receipt/review。
- 能用 scorecard validator 先检查结构。
- 给 Jenn 留出回看和确认空间。

坏处：

- 多一层 draft 文件。
- 后续还要决定哪些内容能升 active。

## 最终决定

```text
采用方案 C，并将其中成熟部分升为本地 active guidance/check。

Golden Paths 成为本地默认路线参考。
Decision Record Template 成为本地默认决策记录模板。
Governance Scorecard + Validator 成为本地默认 registry 体检流程。
Governance Registry YAML example 暂不升 active，继续作为 draft example。
```

## 为什么这样定

```text
AGENTS OS 现在最需要的是“能跑起来，但不越界”。

只写愿景太慢。
直接把所有 registry data 变正式太快。
先把路线、记录模板、体检检查器变成本地默认用法，是中间路线。
```

## 会改变什么

```text
1. 后续新增治理部件时，默认参考 Golden Paths。
2. 重要治理变化默认使用 Decision Record。
3. Registry 对象默认用 Scorecard Validator 做本地结构检查。
4. receipt/review 继续作为证据链。
```

## 不会改变什么

```text
1. Jenn 仍是最终决策者。
2. P3 Hard Stop 不变。
3. Registry 不授权外部写入。
4. Scorecard 不授权执行。
5. 不碰密钥、私密记忆、provider 原始响应。
6. 不注册正式 Memory。
7. 不调用 runtime/provider/plugin。
8. 不修改 WORKSPACE_REGISTRY.yaml。
```

## 颜色区判断

```text
绿色区：
- 读取 active guidance。
- 跑本地 scorecard validator。
- 补 receipt/review。

黄色区：
- 修改 active guidance。
- 新增 registry 对象。
- 调整 scorecard 规则。
- 准备新的 active-promotion。

红色区：
- 未经 Jenn 确认把 draft registry data 升 active。
- 用 registry 或 scorecard 授权外部写入。
- 用 governance guidance 绕过 P3、秘密、私密记忆、provider 原始响应、正式 Memory。
```

## 风险

```text
1. active 文件增多后，control-plane 可能显得更重。
2. active / draft 标注如果不清，未来 agent 可能误用。
3. Scorecard Validator 只能检查结构，不能证明语义完全正确。
4. Decision Record 不能被滥用到每个小改动，否则会拖慢建设。
```

## 验证方式

```text
1. 跑 Governance Registry scorecard validator。
2. 跑 scorecard validator fixture tests。
3. 跑 task-envelope loop fixture tests。
4. 跑 life-core policy-router fixture tests。
5. 检查 WORKSPACE_REGISTRY.yaml 未被修改。
```

## 回看条件

```text
1. Jenn 纠偏一次。
2. Governance Registry 对象超过 12 个。
3. Scorecard validator 出现误判。
4. 有 agent 把 draft 当 active 使用。
5. 连续 3 次使用 active guidance 后。
```

## 证据链接

```text
Confirmation package: control-plane/registry/drafts/2026-06-30-governance-drafts-active-confirmation-package.md
Receipt: control-plane/registry/receipts/2026-06-30-a3c-governance-active-promotion.md
Review: control-plane/registry/reviews/2026-06-30-a3c-governance-active-promotion.review.md
Validation: scorecard validator, scorecard tests, task-envelope loop tests, policy-router tests
```

## 当前结论

`accepted`
