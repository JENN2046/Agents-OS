# 00｜Executive Decision

## 结论

这条路线可以继续，且比 Workspace Agents API / Responses API / 浏览器自动化更符合当前 ChatGPT Pro 现实。

最终路线：

```text
Codex App Server
  ↔
Jenn Bridge Orchestrator
  ↔
Worker Thread + Reviewer Thread / Detached Review
```

## 不再走的路线

| 路线 | 本轮结论 | 原因 |
|---|---|---|
| Workspace Agents API | 暂停 | 需要 workspace/admin/token 条件，不符合当前 Pro 现实 |
| Responses API | 暂停 | 属于 API billing 路线，不等同于 Pro 网页订阅 |
| 浏览器自动化 ChatGPT | 不作为主线 | 脆弱、无官方协议、安全和审计边界差 |
| 普通 Codex CLI 输出解析 | 不作为底座 | 不适合稳定事件循环和审批流 |

## 采用路线

使用 Codex App Server 作为事件源和控制接口。Bridge 通过 JSON-RPC 管理：

```text
initialize
initialized
thread/start
turn/start
turn/steer
turn/interrupt
review/start
server request handling
event streaming
```

MVP 仅使用 `stdio` transport，不使用 WebSocket。

## 第一版目标

先证明一件事：

```text
App Server event stream → Bridge → Reviewer → Worker resume
```

成立。

不要一开始接真实项目仓库。先用 synthetic workspace 跑通完整闭环。

## 成功定义

MVP 成功不是“写出一个大系统”，而是：

1. 能启动真实 `codex app-server`。
2. 能完成 JSON-RPC 初始化。
3. 能创建 Worker thread。
4. 能通过 `outputSchema` 让 Worker 产出 `NEED_REVIEWER`。
5. 能创建 Reviewer thread。
6. 能通过 `outputSchema` 让 Reviewer 产出 `REVIEWER_DECISION`。
7. Bridge 能自动把 Reviewer 结论回填 Worker。
8. Worker 能输出 `DONE`。
9. 过程全程有 JSONL event log 和 receipt。
10. 全程不碰真实仓库、不越权、不读 secrets。
