# AGENTS OS Decision Records v0.1

Status: `active_local_guidance`
Date: 2026-06-30
Scope: local AGENTS OS governance decisions
Accepted by: Jenn confirmation in current Codex thread

## 一句话

Decision Record 记录“为什么这样定”。

它不替代 task-envelope、receipt 或 review：

```text
task-envelope：做事前先讲清楚。
receipt：做完以后留脚印。
review：复核这件事有没有问题。
decision record：记录为什么制度或方向这样变。
```

## 什么时候需要

默认需要 Decision Record：

- 草案要升成 active。
- 绿色区 / 黄色区 / 红色区边界要变。
- `policy-router` 决策逻辑要明显改变。
- `task-envelope` 结构要明显改变。
- registry schema 要改变。
- 新增长期治理部件。
- Jenn 纠偏后，需要把原因留给以后看。
- 一件事会影响 Agent 身份、关系、责任边界、家规、生命内核。

默认不需要：

- 小错字。
- 小 README 补充。
- 单次本地验证。
- 不改变规则的普通 receipt。

## 默认位置

Accepted decisions:

```text
control-plane/registry/decisions/YYYY-MM-DD-short-name.md
```

Draft decisions:

```text
control-plane/registry/drafts/YYYY-MM-DD-short-name.draft.md
```

Template:

```text
control-plane/registry/templates/decision-record-template-v0.1.md
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

## 已接受的第一条 Decision Record

```text
control-plane/registry/decisions/2026-06-30-governance-control-plane-layer.md
```
