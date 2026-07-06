# AGENTS OS Decision Record Template v0.1 Draft

Status: `draft_not_active`
Date: 2026-06-30
Scope: local AGENTS OS governance decisions

Promotion note:

```text
Jenn promoted this template to active local use on 2026-06-30.
Active guidance:
control-plane/registry/DECISION_RECORDS.md

Active template:
control-plane/registry/templates/decision-record-template-v0.1.md

This draft is retained as historical source material.
```

## 一句话

Decision Record 是 AGENTS OS 的“为什么这样定”的记录。

它回答的不是“做了什么”，而是：

```text
当时为什么要这样决定？
看过哪些选择？
最后选了什么？
代价是什么？
以后怎么回看？
```

## 和现有文件的区别

```text
task-envelope：做事前先讲清楚。
receipt：做完以后留脚印。
review：复核这件事有没有问题。
decision record：记录为什么制度或方向这样变。
```

## 什么时候需要 Decision Record

这些情况建议写：

- 草案要升成 active。
- 绿色区 / 黄色区 / 红色区边界要变。
- `policy-router` 决策逻辑要明显改变。
- `task-envelope` 结构要明显改变。
- registry schema 要改变。
- 新增长期治理部件。
- Jenn 纠偏后，需要把原因留给以后看。
- 一件事会影响 Agent 身份、关系、责任边界、家规、生命内核。

这些情况不一定需要：

- 小错字。
- 小 README 补充。
- 单次本地验证。
- 不改变规则的普通 receipt。

## 文件命名建议

```text
control-plane/registry/decisions/YYYY-MM-DD-decision-short-name.md
```

如果还只是草案：

```text
control-plane/registry/drafts/YYYY-MM-DD-decision-short-name.draft.md
```

## 模板

复制下面这一段使用。

````markdown
# Decision Record: <title>

Decision ID: `<id>`
Status: `draft | accepted | superseded | rejected`
Date: YYYY-MM-DD
Scope: `<local scope>`
Owner: Jenn
Agent steward: Nobao

## 一句话

<用一句大白话说这个决定是什么。>

## 背景

<为什么现在需要决定？之前哪里不清楚？哪里卡住？>

## 目标

```text
1.
2.
3.
```

## 不解决什么

```text
1.
2.
3.
```

## 看过的选择

### 方案 A：<name>

好处：

- 

坏处：

- 

### 方案 B：<name>

好处：

- 

坏处：

- 

## 最终决定

```text
<最后选择什么。>
```

## 为什么这样定

```text
<用大白话解释原因。>
```

## 会改变什么

```text
<哪些文件、流程、检查器、registry 状态会变。>
```

## 不会改变什么

```text
<哪些边界不变，尤其 P3、秘密、外部写入、正式 Memory。>
```

## 颜色区判断

```text
绿色区：
黄色区：
红色区：
```

## 风险

```text
1.
2.
3.
```

## 验证方式

```text
1.
2.
3.
```

## 回看条件

```text
什么时候要回来重看这个决定？
例如：误判 1 次、Jenn 纠偏 1 次、连续使用 3 次、测试失败。
```

## 证据链接

```text
Task envelope:
Receipt:
Review:
Validation:
```

## 当前结论

`draft | accepted | rejected | superseded`
````

## 状态值

```text
draft：还在草案，不生效。
accepted：已经接受，可以作为本地依据。
rejected：看过但不采用。
superseded：被新决定替代。
```

## 硬边界

Decision Record 不能用来绕过：

- Jenn 的最终判断。
- P3 Hard Stop。
- 密钥 / token / cookie 边界。
- 私密记忆原文边界。
- provider 原始响应边界。
- 外部写入确认。
- runtime/provider/plugin 执行确认。
- 正式 Memory 注册流程。

## v0.1 通过标准

一个 Decision Record 至少要让人看懂：

```text
为什么要决定
决定了什么
没决定什么
风险是什么
怎么验证
什么时候回看
```

## 当前状态

This file is a draft template. It does not create active decisions.
