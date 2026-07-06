# AGENTS OS Governance Scorecard v0.1 Draft

Status: `draft_not_active`
Date: 2026-06-30
Scope: local AGENTS OS governance object health checks

Promotion note:

```text
Jenn promoted this scorecard guidance to active local use on 2026-06-30.
Active file:
control-plane/registry/SCORECARD.md

This draft is retained as historical source material.
```

## 一句话

Governance Scorecard 是 AGENTS OS 的“治理体检表”。

它不判断 Jenn 对不对，也不评价 Nobao 好不好。它只检查治理部件有没有基本安全要素：

```text
有没有 owner
有没有 status
有没有 red_zone
有没有 validation
有没有 receipt
有没有 review
有没有把草案误当正式
有没有碰红线
```

## 不是什么

Scorecard 不是：

- 不是最终裁判。
- 不是授权系统。
- 不是绩效评分。
- 不是自动执行器。
- 不是安全保证书。

它只是一个本地检查草案。

## 检查对象

第一版检查 Governance Registry 里登记的治理对象。

对象可以是：

- policy module
- router
- workflow
- task envelope
- validator
- loop runner
- registry
- runbook
- boundary doc
- decision record
- golden path

## 分数不是重点

v0.1 不追求复杂打分。先用三种结果：

```text
PASS：基本清楚。
WARN：能看，但有缺口。
FAIL：不该继续推进，先补齐或停。
```

## 必检项

每个对象至少检查：

```text
id
type
status
path
owner
scope
authority
red_zone
validation
evidence
```

## 规则草案

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
SC-010: draft 被描述成 active -> FAIL
SC-011: example 被描述成 active -> FAIL
SC-012: 出现 secret/token/private key/provider raw response 标记 -> FAIL
SC-013: 声称 registry 可以授权外部写入 -> FAIL
SC-014: 声称可以绕过 Jenn 或 P3 -> FAIL
SC-015: 缺 last_receipt -> WARN
SC-016: 缺 last_review 且对象影响边界 -> WARN
```

## 建议输出格式

```text
Object: policy-router
Status: PASS
Findings:
- SC-015 WARN: last_receipt points to a directory, not a specific file.
Next:
- Link latest receipt when available.
```

## 最小 YAML 形态

```yaml
schema_version: agents-os.governance-scorecard.v0.1-draft
target_registry: control-plane/registry/drafts/agents-os-governance-registry.v0.1.example.yaml
result:
  checked_objects: 4
  pass: 0
  warn: 0
  fail: 0
rules:
  - id: SC-001
    level: fail
    check: object_has_id
    message: object is missing id
```

## 什么时候跑

建议触发点：

```text
新增治理对象后
草案准备升 active 前
修改 registry schema 后
Jenn 纠偏一次后
router 或 validator 出现误判后
```

## 和 Golden Paths 的关系

Golden Paths 告诉你怎么走。

Scorecard 检查你走完后有没有留下最基本的治理安全件。

大白话：

```text
Golden Paths 是路线图。
Scorecard 是体检表。
```

## 和 Decision Record 的关系

Decision Record 记录为什么这样定。

Scorecard 检查这个决定有没有必要的字段和证据。

大白话：

```text
Decision Record 是理由。
Scorecard 是检查理由有没有写清楚。
```

## v0.1 通过标准

这个草案要算可用，至少满足：

- 能检查 registry 对象有没有基础字段。
- 能发现 draft / active 混淆。
- 能发现缺 red_zone。
- 能发现缺 validation。
- 能发现明显秘密标记。
- 不自动执行任何治理动作。

## 当前状态

This file is the draft source for active local scorecard guidance.

The active guidance is:

```text
control-plane/registry/SCORECARD.md
```

The first local checker exists at:

```text
control-plane/registry/validate-governance-registry.py
```

The checker is read-only. It does not execute registry objects or grant
authority.
