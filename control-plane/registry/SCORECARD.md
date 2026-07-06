# AGENTS OS Governance Scorecard v0.1

Status: `active_local_check_guidance`
Date: 2026-06-30
Scope: local AGENTS OS governance object health checks
Accepted by: Jenn confirmation in current Codex thread

## 一句话

Governance Scorecard 是 AGENTS OS 的本地治理体检表。

它检查治理对象有没有基础安全件：

```text
id
type
status
owner
authority
red_zone
validation
evidence
receipt
review
```

## 不授权什么

Scorecard 不授权：

- 外部写入。
- runtime / provider / plugin 调用。
- 正式 Memory 注册。
- 部署、发布、git push。
- 绕过 Jenn、P3、review、task-envelope 或 policy-router。

它只输出 `PASS`、`WARN`、`FAIL`。

## 默认检查命令

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-governance-registry.py
```

Fixture tests:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-governance-registry-validator.py
```

## Document Governance Score

`docctl score` is the versioned read-only score view for the Federated Document
Registry pilot.

Hard gates block 9.5 eligibility:

```text
unregistered_files > 0
doctor fail > 0
blocking_warn > 0
```

Current scoring starts from 100 and records every deduction. A result is
9.5-eligible only when the score is at least 95 and all hard gates are clear.

Commands:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score --json
```

## 什么时候跑

默认在这些时候跑：

- 新增治理对象后。
- 修改 Governance Registry 对象后。
- 草案准备升 active 前。
- 修改 registry schema 后。
- Jenn 纠偏一次后。
- router 或 validator 出现误判后。

## 当前规则

```text
SC-001: 缺 id -> FAIL
SC-002: 缺 type -> FAIL
SC-003: 缺 status -> FAIL
SC-004: status 不是允许值 -> FAIL
SC-005: active 对象缺 owner -> FAIL
SC-006: active 对象缺 authority -> FAIL
SC-007: 缺 red_zone -> FAIL
SC-008: 有脚本但缺 validation -> WARN
SC-009: 有权限边界变化但缺 review -> FAIL
SC-010: draft/example authority 混淆 active -> FAIL
SC-011: example 被描述成 active -> FAIL
SC-012: 出现 secret-like pattern -> FAIL
SC-013: 声称 registry 可以授权外部写入 -> FAIL
SC-014: 声称可以绕过 Jenn 或 P3 -> FAIL
SC-015: 缺 last_receipt -> WARN
SC-016: 缺 last_review 且对象影响边界 -> WARN
```

## 当前 checker

```text
control-plane/registry/validate-governance-registry.py
```

这个 checker 是只读本地检查器，不执行 registry 对象，不授予权限。
