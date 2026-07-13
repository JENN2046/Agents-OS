# Decision Record: AGENTS OS VCP High-Privilege Architecture v0.1

```yaml
decision_id: decision-agents-os-vcp-high-privilege-architecture-2026-07-12
date: 2026-07-12
status: accepted
implementation_status: not_started
owner: Jenn
agent_steward: Nobao
scope:
  - runtime/VCPToolBox
  - runtime/VCPChat
  - runtime/VCPMobile
decision_source: Jenn requested that the current architecture judgment be recorded
permission_expansion_granted: false
runtime_execution_authorized: false
secret_access_authorized: false
amendments:
  - date: 2026-07-12
    decision: TaskPermit dependency commitment and fence binding synchronized with Task Dependency v0.1
```

## 一句话决议

**对 Jenn 的私人 AGENTS OS，高权限作为能力上限是最优选；高权限作为所有 Agent、设备、
窗口和插件的常驻默认授权，不是最优选。**

采用：

```text
最大能力
+ 最小常驻授权
+ 最大安全自治
+ 任务级临时许可
```

不采用：

```text
永久削弱 VCP 的能力
所有动作都人工确认
共享一个万能身份
拿到一个 Key 就永久拥有整台设备
由某个 VCP 子项目吞并 AGENTS OS 的全局权威
```

## 1. 为什么这个结论适合私人系统

私人系统与企业多租户系统不同：

- 最终 owner 只有 Jenn。
- 目标是长期协作、连续行动和低摩擦自治。
- 本机文件、桌面、手机、记忆和工具确实需要被 Agent 使用。
- 把所有能力永远关在低权限沙箱里，会让 AGENTS OS 只剩对话和建议。

所以能力上限应该高。

但“私人”不等于“没有威胁”。真正需要防的主要不是陌生用户，而是：

```text
模型或网页内容中的 prompt injection
错误或失控的工具调用
插件和依赖供应链问题
设备丢失或旧设备未撤销
共享 token 泄漏
renderer / WebView 内容注入
上游更新引入的权限漂移
Agent 对任务范围的误判
重复执行、超时重试和崩溃恢复造成的二次副作用
跨项目、跨记忆域和跨设备的权限扩散
```

这些风险在只有一个 owner 时仍然存在，并且因为系统权限高，后果可能更大。

## 2. 三个 VCP 项目为什么都设置了高权限

这不是巧合，而是同一技术路线的连续结果。

### VCPToolBox

它把模型、工具、插件、记忆、浏览器、文件、Shell、邮件和分布式节点组织成一个行动
闭环。它的价值就是让 AI 不只回答，还能执行。

### VCPChat

它由 VCPToolBox 同一生态和主要作者发展而来。它不仅消费后端能力，还把桌面、文件、
Shell、Python、挂件、同步和本机插件作为分布式能力交回 VCPToolBox。

### VCPMobile

它由另一作者开发，但源码明确镜像 VCPChat 的分布式协议和 manifest 结构，以零改动
兼容 VCPToolBox。它把手机传感器、通知、剪贴板、后台服务和 Root 相关能力接入同一
网格。

共同设计假设是：

```text
持有 VCP_Key / sync token
  -> 被视为可信节点或同步 peer
  -> 可以注册能力、上报状态、接收请求和跨设备同步
```

因此三个项目形成的是：

```text
single-owner trusted high-privilege device mesh
```

而不是：

```text
zero-trust task-capability system
```

## 3. 决定保留什么，改变什么

| 项目 | 保留 | 必须改变 |
|---|---|---|
| VCPToolBox | 插件、工具、记忆智能、分布式能力和高权限执行能力 | 不再凭共享 Key 获得无范围执行权；不拥有 AGENTS OS 全局许可和总账 |
| VCPChat | 桌面、文件、交互、挂件、同步和本机执行能力 | renderer 不持有真实秘密；IPC 和远程工具受 task permit 约束 |
| VCPMobile | 传感器、通知、设备状态、受控移动动作和必要 Root 能力 | 每设备身份；Root 不成为通用远程工具；同步读写删分权 |
| Agent | 高决策自治、自动完成 Green Lane 工作 | 不常驻持有 Root、万能 token 或全部设备身份 |
| AGENTS OS | 许可、身份、任务范围、撤销、审计和全局目标 | 不重写 VCP 的具体设备能力，不成为第二套笨重插件运行时 |

## 4. 权限层级

```text
P0 Jenn
  permanent root owner
  final direction and irreversible authority

P1 AGENTS OS Authority Kernel
  identity
  policy
  TaskPermit issue / verify / revoke
  Green / Yellow / Red classification
  global task lifecycle authority
  low-disclosure audit reference

P2 Nobao / Agent
  high reasoning and planning autonomy
  automatic Green Lane progress
  no permanent raw root secret

P3 Execution Hosts
  VCPToolBox
  VCPChat
  VCPMobile
  Codex host / ColaMeta executor where applicable

P4 Concrete Capability
  file read/write
  shell command
  desktop action
  notification
  sensor sample
  memory query/write
  sync read/write/delete
```

执行宿主拥有能力，但是否可以在当前任务中使用该能力，由上层 permit 决定。

## 5. 自治与授权必须分开

三个概念不能继续混在一起：

| 概念 | 含义 | AGENTS OS 决策 |
|---|---|---|
| Capability | 系统最多能做什么 | 保持很高 |
| Standing authority | 平时永久拿着什么权力 | 尽量小 |
| Autonomy | 在已授权范围内能否自己推进 | 尽量高 |

所以“减少常驻授权”不等于“降低自治”。

正确体验应该是：

- 安全、可逆、本地、范围清楚的工作自动拿 permit、自动执行、自动验证。
- 有真实副作用但可控的工作按一批 Yellow scope 发有限 permit，不做微确认。
- Root、秘密、删除、发布、外部写和不可逆动作仍停在 Red boundary。

## 6. TaskPermit 最小合同

未来 permit 至少需要表达：

```yaml
permit_id: opaque-id
task_id: canonical-task-id
task_lifecycle_generation: integer
task_completion_epoch: integer
execution_epoch: integer
task_commitment_snapshot_id: opaque-id
dependency_authority_binding:
  dependency_closure_snapshot_id: opaque-id
  completion_refs:
    - completion_ref_id: opaque-id
      assurance_version: integer
      fence_generation: integer
  dependency_closure_fingerprint: opaque-low-disclosure-handle
principal_id: agent-or-operator-id
host_id: concrete-device-or-runtime-id
issuer_id: authority-kernel-identity
policy_bundle_revision: versioned-policy-reference
capabilities:
  - file.read
  - file.write
resources:
  paths:
    - /explicit/allowed/root/**
issued_at: timestamp
expires_at: timestamp
max_invocations: integer
side_effect_class: green | yellow | red
authorization_event_ref: null-or-current-jenn-authorization-event
idempotency_key: opaque-id
requires_human_presence: boolean
secret_handles: []
audit_ref: low-disclosure-reference
signature: detached-or-envelope-signature
```

合同原则：

- permit 只描述授权，不携带真实 secret 值。
- host 必须在副作用发生前验证，不能只靠 prompt 服从。
- 默认拒绝未声明 capability 和资源。
- `red` permit 必须绑定 Jenn 当前、明确、范围完全匹配的 `authorization_event_ref`；Green / Yellow 不得伪造该引用来扩大权限。
- `red` 只承载允许经精确授权执行的 P3a；P3b proposal-only / prohibited 行为永不签发 permit，Jenn authorization Event 也不能把 P3b 变成可执行动作。
- permit issuer、适用 policy revision、authorization scope、有效期或授权 Event 任一无法核验、被撤销或不匹配时失效。
- 超时、撤销、次数耗尽或 task 关闭后立即失效。
- Task commitment、dependency closure、assurance version 或 fence generation 任一不再 current 时立即失效。
- fence 后的旧 permit 永久失效；后续 `PRESERVED`、recovery 或 projection 重建不得令其复活。
- 重试必须绑定同一 idempotency key，避免重复执行。
- 返回结果要区分 `success`、`failed`、`unknown_after_crash` 和 `not_executed`。

host 在副作用发生前必须同步校验 permit 中的 Task generation / epoch、commitment snapshot、全部 dependency
assurance version 和 fence generation；`red` 还必须核验 Jenn authorization Event 的 actor、scope、时效、
policy revision 和撤销状态。无法读取 authority、版本不匹配、fence 状态未知或 verifier 不可用时一律
fail closed；若无法证明动作是否已发生，则进入 `unknown_after_crash`，不得把它降格为普通拒绝或自动重试。

## 7. 每类事实只允许一个权威写入者

本决议不要求把全部状态塞进一个数据库。

采用：

```text
Single Authority Per Fact Class
+ One Canonical Global Task Ledger
+ Derived Read-Only Projections
```

推荐责任：

| 事实类别 | 权威写入者 |
|---|---|
| Jenn 身份和最终所有权 | AGENTS OS root governance |
| 全局任务生命周期 | canonical global task ledger |
| permit、lease、撤销、recovery policy | AGENTS OS authority/control kernel |
| 真实进程与执行会话 | 对应 execution host |
| VCPToolBox 插件运行状态 | VCPToolBox |
| VCPChat 窗口与桌面会话 | VCPChat |
| VCPMobile 设备与传感器状态 | VCPMobile |
| VCP native memory 内容与生命周期 | VCP native memory runtime |
| 记忆访问许可和低披露证据 | governed memory bridge |
| Dashboard / Workbench | read-only projection and operator facade |

## 8. 三个项目的强制边界

### 8.1 VCPToolBox

- 工具注册不得携带未经脱敏的插件配置。
- 分布式节点使用独立 identity，不共享一个万能 VCP key。
- `execute_tool` 在进入插件前验证 permit。
- prompt 中出现工具描述不等于获准执行。
- scheduler、human tool、chat loop 和远程节点不能绕过同一 host gate。
- 记忆智能可以留在 VCP，记忆访问授权不能只由插件自己判断。

### 8.2 VCPChat

- renderer 和挂件不接收真实 provider/admin/VCP secret。
- IIFE、Shadow DOM 和 Proxy 不得命名为安全沙箱。
- 任意 Python、Shell、系统工具、插件配置写入和插件启停必须进入专用 capability。
- `internal_request_file` 改为受 permit 约束的 artifact handle。
- distributed plugin 注册和执行经过 host gate。

### 8.3 VCPMobile

- 每台手机拥有独立、可撤销 identity。
- `sync.read`、`sync.write`、`sync.delete` 分开。
- clipboard、location、notification 等能力逐项启用并由 permit 约束。
- `run_root_command` 不进入通用远程工具目录。
- Root 仅作为设备内部、固定实现的最小能力，不能接受任意远程命令字符串。
- token 不进入 query string；使用认证加密传输或明确的私有安全隧道。

## 9. Green / Yellow / Red 如何落地

### Green

系统自动签发短期 permit，不打断 Jenn：

```text
只读本地状态
限定工作区内的可逆文件修改
确定性验证
无秘密、无外部写、无真实设备副作用的工具调用
```

### Yellow

按任务批量签发，明确资源和期限：

```text
本地构建
限定目录写入
一次设备通知
一次传感器采样
受控插件启用测试
可恢复的同步写入
```

### Red

不自动签发：

```text
任意 Root command
秘密或凭据变更
广泛原始记忆读取
真实外部写
删除或不可逆同步
发布、部署、force push
权限模型本身的绕过或扩张
```

## 10. 实施顺序

### Phase 0：冻结权限面增长

- 暂停新增万能 token、通用 IPC、通用 remote tool 和新的隐式角色。
- 不重置或清理 VCPToolBox 当前插件隔离现场。
- 固化三项目 capability、identity、secret 和 state authority matrix。

### Phase 1：每设备身份

- 为 ToolBox、Chat、Mobile 建独立 device ID 和 credential。
- 支持签发、轮换、撤销和设备丢失处置。
- 保留旧 VCP_Key 兼容适配，但不再扩展其权限。

### Phase 2：TaskPermit 合同与 verifier

- 冻结 permit schema。
- 建本地签发器、验证器和撤销表。
- 先覆盖三个 Green Lane capability，不一次包住全部插件。

### Phase 3：三个 host enforcement point

- VCPToolBox：插件执行前。
- VCPChat：IPC / distributed tool / widget action 前。
- VCPMobile：distributed tool / sync mutation / native effect 前。

任何入口都不能直接绕过 host gate。

### Phase 4：Secret broker

- secret 留在 owner process 或系统安全存储。
- renderer、模型上下文、tool manifest 和 receipt 只拿 opaque handle。
- 删除 VCPChat 向 desktop renderer 返回原始凭据的路径。
- 注册工具前递归脱敏 config 字段。

### Phase 5：同步和传输分权

- 拆分 read/write/delete。
- 停止 query token。
- 加入 TLS、私有隧道或等价认证加密层。
- 验证旧设备撤销和重放拒绝。

### Phase 6：Kill switch、幂等和恢复

- Jenn 可一键撤销全部非本机 permit。
- Agent、host、device 和 capability 可分别停用。
- 外部副作用保存 idempotency key 和结果状态。
- crash 后不把“未知”伪报为“成功”或自动重复执行。

### Phase 7：三任务 benchmark

使用同一组任务验证 ToolBox、Chat 和 Mobile：

1. 只读获取本机或设备状态。
2. 在限定资源内完成一次可逆写入。
3. 完成一次有真实但低影响副作用的动作。

测量：

```text
是否自动前进
是否需要多余人工确认
是否存在多个状态真相
重跑是否幂等
断线和崩溃后是否可诊断
permit 到期或撤销后是否真的失效
秘密是否进入 renderer、prompt、manifest、log 或 receipt
Dashboard 是否只读且显示正确
```

## 11. 明确非目标

- 不把 VCPToolBox、VCPChat 或 VCPMobile 削成只能聊天的低权限壳。
- 不为每次普通本地操作增加确认弹窗。
- 不立即重写 VCP 协议或三个 upstream 项目。
- 不新建一个平行数据库去吞并所有子系统状态。
- 不让 codex-router、Workbench、ColaMeta 或任一 runtime 单独成为 AGENTS OS 本身。
- 不把文档中的权限决议误当成真实 runtime enforcement 已经存在。

## 12. 验收条件

只有同时满足以下条件，才能把 VCP 三项目称为 AGENTS OS 的高权限可信身体：

```text
每设备身份可验证、可轮换、可撤销
每次高影响动作绑定 task permit
host 在副作用前强制验证 permit
effectful permit 绑定 current Task commitment、dependency closure、assurance versions 和 fence generations
Red permit 绑定 Jenn 当前明确授权 Event 与适用 policy revision
renderer 和模型上下文拿不到原始 secret
工具注册不会传播配置秘密
同步读写删已经分权
Root 不接受通用远程命令
重试有幂等，crash 有 unknown 状态和恢复路径
Jenn 有全局 kill switch
三个 Green Lane benchmark 连续通过
```

## 13. 本决议不授权什么

本文件是架构方向记录，不是执行许可。它不授权：

- 读取或修改任何 `.env`、`config.env`、token、cookie、credential 或 provider 配置。
- 启动 VCPToolBox、VCPChat、VCPMobile 或其公开/私有服务。
- 执行 Root、Shell、Python、插件、provider、同步写入或真实设备动作。
- 修改三个 runtime checkout 的源码或插件启用状态。
- 绕过根 `AGENTS.md`、P3、现有安全边界或 Jenn 的当前授权。

## 14. 关联证据

```text
ops/reports/vcptoolbox-runtime-reality-map-2026-07-12.md
ops/reports/vcpchat-runtime-reality-map-2026-07-12.md
ops/reports/vcpmobile-runtime-reality-map-2026-07-12.md
governance/SECURITY_BOUNDARIES.md
control-plane/registry/decisions/2026-07-03-three-lane-execution-model-v0.1.md
control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
```

## 15. 最终记录

```yaml
decision:
  high_capability_ceiling: retain
  permanent_high_authority_for_agents: reject
  task_scoped_temporary_permits: adopt
  safe_local_autonomy: maximize
  per_device_identity: required
  shared_omnipotent_token: migrate_away
  vcp_projects_as_execution_hosts: adopt
  vcp_project_as_agents_os_global_owner: reject
```

最终原则：

> 最大能力，最小常驻授权，最大安全自治。
