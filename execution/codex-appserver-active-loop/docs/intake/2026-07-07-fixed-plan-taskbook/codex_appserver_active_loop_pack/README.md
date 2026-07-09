# Codex App Server Active Event Loop｜修复后落地包

生成日期：2026-07-07

## 目标

在只有 ChatGPT Pro、暂不使用 Workspace Agents API / Responses API / 浏览器自动化的现实条件下，构建一个本地 **Codex App Server Active Event Loop**：

```text
Codex Worker Thread
  ↔
Jenn Bridge Orchestrator
  ↔
Codex Reviewer / Review Thread
```

核心目标是让本地 Codex 在执行过程中主动提出问题，由本地 Bridge 自动路由给 Reviewer Codex，再把 Reviewer 的结构化结论回填给 Worker，使 Worker 继续推进。

## 包内文件

```text
00_EXECUTIVE_DECISION.md        总结论与路线判断
01_MASTER_PLAN.md               实现目标总计划书
02_PHASE_PLANS.md               分阶段计划书
03_CODEX_EXECUTION_TASKBOOK.md  可直接交给 Codex 的完整执行任务书
04_ACCEPTANCE_CRITERIA.md       验收标准
05_SECURITY_BOUNDARIES.md       安全边界与禁止项
06_EVENT_CONTRACT.md            事件契约与状态机
07_SELF_REVIEW.md               两轮修复后的自审查
08_ROUNDTABLE_REVIEW.md         多角色圆桌审查
09_CODEX_HANDOFF_PROMPT.md      给 Codex 的压缩版执行入口
10_SOURCE_NOTES.md              官方资料来源说明
MANIFEST.json                   文件清单
```

## 使用顺序

1. 先读 `00_EXECUTIVE_DECISION.md`。
2. 再读 `01_MASTER_PLAN.md` 和 `02_PHASE_PLANS.md`。
3. 把 `03_CODEX_EXECUTION_TASKBOOK.md` 交给本地 Codex 执行。
4. 执行前确认 `05_SECURITY_BOUNDARIES.md`。
5. 执行后用 `04_ACCEPTANCE_CRITERIA.md` 验收。

## 最重要的边界

MVP 只做：

```text
stdio transport
real codex app-server smoke
synthetic workspace
readOnly restricted sandbox
Worker → Reviewer → Worker 自动闭环
```

MVP 不做：

```text
Workspace Agents API
Responses API
浏览器自动化 ChatGPT
WebSocket transport
thread/shellCommand
command/exec
process/*
full_access / dangerFullAccess
真实仓库写入
commit / push / deploy / release
```
