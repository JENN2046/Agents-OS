# 01｜Master Plan：Codex App Server Active Event Loop

## 1. 实现目标

构建一个本地 Codex-native 主动双向对话系统：

```text
Worker Codex：负责执行任务
Reviewer Codex：负责审查、架构判断、下一步决策
Jenn Bridge：负责事件路由、状态机、权限门、日志和回填
```

该系统不依赖 Workspace Agents API、Responses API 或浏览器自动化。

## 2. 设计原则

### 2.1 本地优先

所有 MVP 逻辑在本机运行：

```text
local codex app-server
local bridge
local synthetic workspace
local event store
local receipt store
```

### 2.2 stdio 优先

MVP 使用：

```text
codex app-server --listen stdio://
```

不使用 WebSocket。WebSocket 只有在后续版本需要 UI 或远程控制面时再评估。

### 2.3 结构化优先

Smoke test 不依赖模型自由文本。Worker 和 Reviewer 必须使用 `outputSchema` 返回结构化 JSON。

### 2.4 权限先于能力

任何执行能力都必须先过权限门：

```text
readOnly restricted
synthetic workspace only
no full access
no shellCommand
no command/exec
no push/deploy/release
```

### 2.5 先 synthetic，再真实仓库

MVP 不接真实仓库。只有 synthetic workspace 验证通过后，才进入真实仓库 read-only 审查阶段。

## 3. 总体架构

```text
┌─────────────────────────────────────────────┐
│ Jenn Bridge Orchestrator                    │
│                                             │
│  ┌──────────────┐   ┌─────────────────────┐ │
│  │ AppServer    │   │ State Machine        │ │
│  │ JSON-RPC     │   │ CREATED/RUNNING/...  │ │
│  │ Client       │   └─────────────────────┘ │
│  └──────┬───────┘                           │
│         │                                   │
│  ┌──────▼───────┐   ┌─────────────────────┐ │
│  │ Event Router │   │ Policy Gate          │ │
│  │ notifications│   │ deny/allow decisions │ │
│  │ server reqs  │   └─────────────────────┘ │
│  └──────┬───────┘                           │
│         │                                   │
│  ┌──────▼───────┐   ┌─────────────────────┐ │
│  │ Job Store    │   │ Event Store          │ │
│  │ jobs.json    │   │ events.jsonl         │ │
│  └──────────────┘   └─────────────────────┘ │
└─────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ codex app-server                            │
│  - Worker thread                            │
│  - Reviewer thread                          │
│  - optional detached review thread          │
└─────────────────────────────────────────────┘
```

## 4. 总阶段

| 阶段 | 名称 | 目标 |
|---:|---|---|
| Phase 0 | Reality Calibration | 确认本机 App Server 可用，生成 schema |
| Phase 1 | App Server Client | 实现 stdio JSON-RPC client |
| Phase 2 | Synthetic Workspace | 建立无害测试工作区 |
| Phase 3 | Worker Loop | Worker 结构化输出 NEED_REVIEWER |
| Phase 4 | Reviewer Loop | Reviewer 结构化输出 REVIEWER_DECISION |
| Phase 5 | Resume Loop | Bridge 自动回填 Worker |
| Phase 6 | Approval Handling | 接入 server request / approval 默认拒绝 |
| Phase 7 | Receipts & Audit | 输出日志、receipt、验收报告 |
| Phase 8 | Read-only Real Repo Pilot | synthetic 通过后才允许真实仓库只读试点 |

## 5. 非目标

MVP 不实现：

```text
ChatGPT Workspace Agent
OpenAI Responses API
ChatGPT browser automation
MCP connector
Secure MCP Tunnel
WebSocket UI
真实仓库写入
commit/push/deploy/release
长期后台守护进程
```

## 6. 预期结果

MVP 完成后，我们将拥有一个最小但真实的本地 agent runtime loop：

```text
Worker 遇到问题
Bridge 自动识别
Reviewer 自动判断
Bridge 自动回填
Worker 自动继续
```

这就是后续 AGENTS OS 自动推进能力的底层最小闭环。
