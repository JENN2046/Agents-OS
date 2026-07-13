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

## 已接受的 Decision Records

```text
control-plane/registry/decisions/2026-06-30-governance-control-plane-layer.md
control-plane/registry/decisions/2026-07-03-three-lane-execution-model-v0.1.md
control-plane/registry/decisions/2026-07-05-agents-os-root-agents-engineering-absorption-v0.1.md
control-plane/registry/decisions/2026-07-05-agents-os-automation-uplift-v0.1.md
control-plane/registry/decisions/2026-07-12-agents-os-vcp-high-privilege-architecture-v0.1.md
control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
control-plane/registry/decisions/2026-07-13-agents-os-r1-scheduling-freeze-decision-v0.1.yaml
control-plane/registry/decisions/2026-07-13-agents-os-scheduling-time-capacity-v0.1-accepted-materialization.md
```

其中，当前 AGENTS OS 未来运行方式的综合入口是：

```text
control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
```

该综合决议在 2026-07-13 接受并冻结 `Task Scheduling Architecture Boundary v0.1`。由该边界展开出的
完整 v0.1 合同包已完成 R1 收口并通过 hash-bound 独立终审，随后由 Jenn 以独立不可变记录正式原子冻结：

```text
control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md
control-plane/registry/decisions/2026-07-13-agents-os-r1-scheduling-freeze-decision-v0.1.yaml
control-plane/registry/decisions/2026-07-13-agents-os-scheduling-time-capacity-v0.1-accepted-materialization.md
control-plane/registry/reviews/2026-07-13-agents-os-scheduling-time-capacity-clean-checkout-validation-qualification-v0.1.yaml
```

接受单位是不可拆分的 `R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE`：草案 Sections 3-9 加父架构 Section 2.1 R1
overlay，禁止 partial freeze。冻结记录绑定两份受审 subject 的精确 SHA-256；受审文件不因冻结而修改。
父架构 Section 2.1 overlay 已随整包生效。Resource-constrained Scheduling v0.2 仍是独立保存的设计草案，
仍有待未来单独解决的已知缺口，不包含在整包接受语义中：

```text
control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md
```

原 R1 review 中的 `384/384`、score `100` 和 zero-warning 字段只代表冻结前完整本地 workspace，不能作为
clean committed tree 的零警告证据。独立 qualification record 将 committed-tree repository validation 标为
`PARTIAL_WITH_PREEXISTING_BROKEN_REFERENCES`；这不改变语义终审结论，但降低并限定了可引用的验证证据强度。

本次冻结只接受架构语义，不授权实现、Rust runtime 建设、数据库变更、服务启动、provider/executor 调用或
runtime activation。

VCP 高权限、设备身份、TaskPermit 和 host enforcement 的专项依据是：

```text
control-plane/registry/decisions/2026-07-12-agents-os-vcp-high-privilege-architecture-v0.1.md
```
