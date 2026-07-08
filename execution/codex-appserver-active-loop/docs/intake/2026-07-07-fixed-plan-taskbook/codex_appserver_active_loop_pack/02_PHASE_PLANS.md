# 02｜Phase Plans：分阶段计划书

## Phase 0｜Reality Calibration

### 目标

确认本机可以运行 `codex app-server`，并生成当前 Codex 版本对应的 TypeScript / JSON Schema。

### 执行任务

1. 检查 `codex` 是否在 PATH。
2. 检查 `codex --version`。
3. 尝试启动 `codex app-server`。
4. 通过 stdio 发送 `initialize`。
5. 发送 `initialized` notification。
6. 执行：

```bash
codex app-server generate-ts --out ./src/generated/appserver
codex app-server generate-json-schema --out ./schemas/appserver
```

7. 记录结果到 `data/reports/phase0_reality_calibration.json`。

### 验收标准

```yaml
phase0_acceptance:
  codex_found: true
  appserver_started: true
  initialize_success: true
  initialized_sent: true
  ts_schema_generated: true
  json_schema_generated: true
  no_experimental_api: true
```

### BLOCK 条件

- `codex` 不存在。
- `codex app-server` 无法启动。
- schema 生成失败。
- 必须开启 `capabilities.experimentalApi=true` 才能继续。

---

## Phase 1｜App Server JSON-RPC Client

### 目标

实现一个最小 JSON-RPC client，支持 stdio transport。

### 执行任务

1. 创建 `src/appserver/jsonrpc.ts`。
2. 创建 `src/appserver/transport_stdio.ts`。
3. 创建 `src/appserver/client.ts`。
4. 支持 request / response / notification / server-request 四类消息。
5. 支持 request id 追踪。
6. 支持超时和 clean shutdown。
7. 所有 raw event 写入 JSONL。

### 验收标准

```yaml
phase1_acceptance:
  stdio_transport_only: true
  request_response_supported: true
  notification_supported: true
  server_request_supported: true
  raw_event_log_written: true
  clean_shutdown: true
```

---

## Phase 2｜Synthetic Workspace

### 目标

创建一个无害工作区，用于第一次闭环验证。

### 目录

```text
data/synthetic-workspace/
  README.md
  sample.txt
  src/example.ts
```

### 执行任务

1. 创建 synthetic workspace。
2. 内容必须无 secrets。
3. 不指向真实仓库。
4. 只允许 readOnly restricted 读取该目录。

### 验收标准

```yaml
phase2_acceptance:
  synthetic_workspace_created: true
  no_real_repo_used: true
  no_secret_like_files: true
  read_only_restricted_root: data/synthetic-workspace
```

---

## Phase 3｜Worker Loop

### 目标

创建 Worker thread，并让 Worker 在 synthetic workspace 中输出结构化 `NEED_REVIEWER`。

### 执行任务

1. 调用 `thread/start`。
2. 调用 `turn/start`。
3. 设置：
   - `cwd = data/synthetic-workspace`
   - `sandboxPolicy.type = readOnly`
   - restricted readableRoots = synthetic workspace
   - `approvalPolicy` 选择保守值
   - `outputSchema` 强制返回 `NEED_REVIEWER`
4. Bridge 捕获结构化输出。
5. 状态进入 `NEED_REVIEWER`。

### 验收标准

```yaml
phase3_acceptance:
  worker_thread_started: true
  worker_turn_started: true
  output_schema_used: true
  need_reviewer_detected: true
  state_transition: NEED_REVIEWER
```

---

## Phase 4｜Reviewer Loop

### 目标

创建 Reviewer thread，并让 Reviewer 返回结构化 `REVIEWER_DECISION`。

### 执行任务

1. 创建 Reviewer thread。
2. 将 Worker 的 `NEED_REVIEWER` 包装为 Reviewer 输入。
3. 设置 readOnly restricted sandbox。
4. 设置 `outputSchema` 强制返回 `REVIEWER_DECISION`。
5. Bridge 验证 decision 是否合法。
6. 状态进入 `REVIEW_RECEIVED`。

### 验收标准

```yaml
phase4_acceptance:
  reviewer_thread_started: true
  reviewer_turn_started: true
  reviewer_output_schema_used: true
  reviewer_decision_valid: true
  state_transition: REVIEW_RECEIVED
```

---

## Phase 5｜Resume Worker

### 目标

Bridge 自动把 Reviewer 结论回填给 Worker，Worker 输出 `DONE`。

### 执行任务

1. 生成 `REVIEWER_DECISION_RECEIVED` 回填消息。
2. 如果 Worker idle：使用 `turn/start`。
3. 如果 Worker active：仅在确认 active turn id 后使用 `turn/steer`。
4. Worker 输出 `DONE`。
5. 状态进入 `DONE`。

### 验收标准

```yaml
phase5_acceptance:
  reviewer_decision_injected: true
  worker_resumed: true
  done_detected: true
  state_transition: DONE
```

---

## Phase 6｜Approval Handling

### 目标

实现 server-initiated request 默认安全处理。

### 执行任务

1. 识别 App Server 主动发起的 request。
2. 对未知 request：
   - 记录事件；
   - 如需要 decision，默认 decline；
   - 否则进入 BLOCK。
3. 对 `item/fileChange/requestApproval`：
   - readOnly 下自动 decline；
   - secrets/path denylist 自动 decline；
   - 需要人工权限时进入 HUMAN_GATE_REQUIRED。
4. 不调用 `thread/shellCommand`、`command/exec`、`process/*`。

### 验收标准

```yaml
phase6_acceptance:
  server_request_handler: true
  unknown_request_decline_or_block: true
  file_change_read_only_declined: true
  denied_paths_declined: true
  forbidden_methods_not_called: true
```

---

## Phase 7｜Receipts & Audit

### 目标

生成可审计产物。

### 执行任务

1. 为每个 job 写入：
   - `job.json`
   - `events.jsonl`
   - `receipt.md`
2. receipt 包含：
   - result
   - timeline
   - state transitions
   - policy decisions
   - Worker output summary
   - Reviewer decision
   - forbidden actions used/not used
3. 输出 final report。

### 验收标准

```yaml
phase7_acceptance:
  job_json_created: true
  events_jsonl_created: true
  receipt_md_created: true
  policy_summary_present: true
  final_report_present: true
```

---

## Phase 8｜Read-only Real Repo Pilot

### 前置条件

只有 Phase 0-7 全部 PASS 后才允许进入。

### 目标

对一个真实仓库做只读审查，不写文件。

### 默认候选

```text
codex-appserver-active-loop repo self-review
```

不要直接接入 VCPToolBox、codex-router、codex-memory、Photo_Studio_OS。

### 验收标准

```yaml
phase8_acceptance:
  synthetic_loop_passed_before_real_repo: true
  real_repo_read_only: true
  no_file_changes: true
  no_secrets_read: true
  receipt_generated: true
```
