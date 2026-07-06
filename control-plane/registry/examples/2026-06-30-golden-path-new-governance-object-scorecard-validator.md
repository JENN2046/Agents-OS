# Golden Path Example: New Governance Object - Scorecard Validator

Example ID: `golden-path-new-governance-object-scorecard-validator-2026-06-30`
Status: `completed_example`
Date: 2026-06-30
Golden Path: `路线 1：新增治理部件`
Target Object: `governance-registry-scorecard-validator`

## 这张样例是干嘛的

这是一条真实 Golden Path 样例。

它拿已经完成的 `Governance Registry Scorecard Validator` 回放一遍
`Golden Paths` 里的“路线 1：新增治理部件”，检查这条路线是不是能真的指导一次本地治理建设。

这不是 active authority。它只是一个可回看的样例。

## 目标对象

```text
id: governance-registry-scorecard-validator
name: Governance Registry Scorecard Validator
type: validator
status: active
path: control-plane/registry/validate-governance-registry.py
```

## 为什么选它做样例

```text
它是一个真实新增过的治理部件。
它有脚本。
它有测试。
它已经登记进 Governance Registry 草案。
它有 receipt 和 review。
它能被 scorecard validator 反过来检查。
```

## 路线 1 标准步骤回放

### 1. 写一句话说明这个部件解决什么问题

```text
它检查 Governance Registry 里的治理对象有没有基础治理字段和红线边界。
```

结果：`passed`

证据：

```text
control-plane/registry/validate-governance-registry.py
control-plane/registry/reviews/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.review.md
```

### 2. 判断它是绿色、黄色还是红色

```text
A2 / 绿色区本地建设。
```

原因：

```text
只读本地 YAML。
只输出 PASS/WARN/FAIL。
不执行 registry 对象。
不写外部系统。
不调用 runtime/provider/plugin。
不读取密钥、私密记忆、provider 原始响应。
```

结果：`passed`

证据：

```text
control-plane/registry/receipts/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.md
```

### 3. 如果是黄色，先放 drafts/，不要直接 active

```text
这个目标对象不是治理规则草案，而是本地只读检查器。
它作为 active local checker 登记，但它没有授权能力。
```

结果：`not_applicable_but_boundary_clear`

证据：

```text
authority: read-only local checker, not authorization
```

### 4. 写清楚它不是什么，避免误用

```text
它不是授权系统。
它不是最终裁判。
它不执行 registry 对象。
它不授权外部写入、runtime、provider 或正式 Memory。
```

结果：`passed`

证据：

```text
control-plane/registry/README.md
control-plane/registry/reviews/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.review.md
```

### 5. 写清楚 owner、scope、authority、green/yellow/red zone

登记内容：

```text
owner: Jenn / Nobao
scope: local structure and boundary checks for Governance Registry YAML
authority: read-only local checker, not authorization
green_zone: validate local registry YAML, run local fixture tests
yellow_zone: change scorecard rules with receipt and review, add fixture cases
red_zone: execute registry objects, grant external write authority, grant runtime/provider permission, ignore secret-like findings
```

结果：`passed`

证据：

```text
control-plane/registry/drafts/agents-os-governance-registry.v0.1.example.yaml
```

### 6. 如果它会被机器使用，准备最小 example 或 fixture

已准备：

```text
test-governance-registry-validator.py
```

fixture 覆盖：

```text
正常 registry 样例
缺字段的坏样例
secret-like 样例
```

结果：`passed`

证据：

```text
control-plane/registry/test-governance-registry-validator.py
```

### 7. 留 receipt

结果：`passed`

证据：

```text
control-plane/registry/receipts/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.md
```

### 8. 如果边界有变化，留 review

结果：`passed`

证据：

```text
control-plane/registry/reviews/2026-06-30-a2-governance-registry-scorecard-validator-v0.1.review.md
```

### 9. 跑最近的本地验证

本次样例验证使用：

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/task-envelope/test-task-envelope-loop.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/policies/life-core/test-policy-router.py
```

结果：`passed`

### 10. 把结果写回 receipt

目标对象自己的 receipt 已完成。

本次 Golden Path 样例也有单独 receipt：

```text
control-plane/registry/receipts/2026-06-30-a2-golden-path-example-scorecard-validator.md
```

结果：`passed`

## 停止条件检查

```text
读取密钥：没有
读取私密记忆：没有
读取 provider 原始响应：没有
写外部平台：没有
runtime/provider/plugin 调用：没有
把草案直接升 active：没有
改 Jenn 身份、关系、家规、生命内核：没有
```

## 样例结论

```text
路线 1 可以用于检查一个真实新增治理部件是否完整。
这条路线没有替代 Jenn，也没有授权任何外部动作。
它的价值是把“新增治理部件”这件事变成可检查的步骤。
```

## 大白话复述

```text
这条样例说明：
我们不是又写了一个空流程。
我们拿一个真实做过的检查器，把 Golden Path 从头到尾对了一遍。
结果显示：它有说明、有边界、有 owner、有登记、有测试、有 receipt、有 review。
所以 Golden Paths 可以开始作为 AGENTS OS 本地建设的路线图草案来试用。
```
