# VCPChat Runtime Reality Map and AGENTS OS Integration Plan

```yaml
document: VCPChat Runtime Reality Map and AGENTS OS Integration Plan
version: v0.1
date: 2026-07-12
status: FINDINGS_ONLY
scope: /home/jenn/AGENTS_OS_Workspace/runtime/VCPChat
upstream: https://github.com/lioensky/VCPChat
branch: main
head: cfa5883b8373
method: source-first read-only audit with local static checks
runtime_activation: not_performed
distributed_connection: not_performed
provider_execution: not_performed
private_data_read: not_performed
active_config_read: not_performed
runtime_source_modified: false
```

## 1. 这份报告回答什么

这份报告记录 VCPChat 当前源码的真实结构、权限面和 AGENTS OS 接入位置。
它不把 README 的愿景直接当成运行事实，也不因为 VCPChat 是私人桌面客户端就忽略其
真实攻击面。

本轮主要回答：

1. VCPChat 当前到底是聊天客户端、桌面系统，还是执行宿主。
2. Electron renderer、preload、IPC、分布式插件和移动同步之间怎样传递权限。
3. 它为什么会自然形成高权限，以及这些权限当前由什么身份和边界约束。
4. 它在 AGENTS OS 中应该保留什么能力，又不应该成为哪一种权威。
5. 下一阶段应先收口哪些调用链，才能把它作为可信的桌面执行宿主使用。

本轮明确没有：

- 读取 `AppData/settings.json`、`config.env`、`.env` 或任何真实凭据值。
- 读取聊天历史、私人记忆、同步数据、原始日志或 provider raw response。
- 启动 Electron、VCPDistributedServer、VCPMobileSync、RAG Observer 或桌面窗口。
- 执行 Python、PowerShell、PTY Shell、文件工具、桌面遥控或真实 provider 调用。
- 修改 VCPChat 源码、配置、插件状态或 Git 状态。

所以本文能够确认源码中的能力和可达调用链，不能宣称这些能力已在 Jenn 当前设备上
实际启用、已经成功利用或已经通过长期运行验证。

## 2. 证据等级

| 等级 | 含义 |
|---|---|
| `SOURCE_PROVEN` | 当前 commit 的源码、manifest、依赖或 Git 历史直接证明 |
| `STATIC_VALIDATED` | 使用本地只读脚本完成计数、引用或结构核验 |
| `CONFIG_DEPENDENT` | 是否启用取决于未读取的活动配置 |
| `RUNTIME_REQUIRED` | 必须启动应用、连接服务或使用真实设备才能确认 |
| `DOC_CLAIM` | 只代表项目文档中的设计意图，不能单独当作运行事实 |

## 3. 一句话结论

**VCPChat 已经不是普通聊天客户端。它是一套把 AI 对话、桌面 UI、插件、文件、Shell、
Python、同步、RAG、音频和设备控制装进同一个 Electron 产品的高权限桌面执行宿主。**

它与 VCPToolBox 的关系也不是简单前后端：

```text
VCPToolBox
  -> 模型、工具、记忆和分布式控制面

VCPChat
  -> 人类交互面
  -> 本机桌面执行宿主
  -> 分布式插件节点
  -> VCPMobile 同步服务端
  -> AI 可编程桌面与挂件运行面
```

当前最准确的判断是：

```yaml
functional_depth: HIGH
product_scope: VERY_BROAD
privilege_density: VERY_HIGH
desktop_host_value: HIGH
security_readiness_for_ungoverned_use: NOT_READY
agents_os_fit: STRONG_AS_GOVERNED_EXECUTION_HOST
```

大白话说：

> VCPChat 可以成为 AGENTS OS 的眼睛、嘴、手和桌面，但不能同时拿着总钥匙、审批权、
> 全部凭据和全局任务真相。

## 4. 仓库现实快照

```text
canonical path: /home/jenn/AGENTS_OS_Workspace/runtime/VCPChat
upstream:        https://github.com/lioensky/VCPChat.git
branch:          main
HEAD:            cfa5883b8373
latest commit:   心流锁升级到v2.5
commit date:     2026-07-11T23:23:36+08:00
worktree:        clean at audit closeout
package:         vcp-chat-desktop@1.0.0
license:         CC BY-NC-SA 4.0
```

保守静态规模：

```text
tracked files: 779
JavaScript:    266 files / about 202k lines, including bundled or vendored code
Rust:           48 files / about 19.5k lines
Python:         19 files / about 8.3k lines
HTML:           28 files / about 11.5k lines
CSS:            83 files / about 40.5k lines
```

规模证明它是实物，不证明权限隔离、测试覆盖或运行可靠性已经成熟。

根 `package.json` 没有 `test`、`lint` 或 `typecheck` script。当前发现的 CI 主要覆盖
`rust_assistant_engine`，不能代表整个 Electron、IPC、分布式插件、桌面挂件和同步链。

## 5. 它实际由哪些运行面组成

```text
Electron main process
  -> window lifecycle and IPC handlers
  -> AppData and local files
  -> process / Python / system tools
  -> VCP HTTP and WebSocket clients

Role preloads
  -> chatAPI
  -> utilityAPI
  -> desktopAPI
  -> compatibility electronAPI

Renderer surfaces
  -> main chat
  -> desktop
  -> canvas
  -> notes / memo / forum / music / translator / dice
  -> RAG observer and overlay
  -> image and text viewers

VCPDistributedServer
  -> local plugin discovery and execution
  -> registration into VCPToolBox
  -> remote execute_tool handling
  -> local HTTP control routes

VCPMobileSync
  -> mobile WebSocket sync bus
  -> HTTP read/write/delete API
  -> entity, topic, message, avatar and attachment synchronization
```

它的正确分类是：

```text
desktop interaction client
+ privileged local execution host
+ distributed capability node
+ AI-programmable desktop surface
+ mobile synchronization hub
```

## 6. 为什么它必然走向高权限

VCPChat 的高权限不是后期随手加出来的事故，而是产品目标的直接结果。

### 6.1 VCP 的目标是让 AI 直接行动

项目 README 将 VCPChat 定义为打通 AI、UI、App 边界的分布式全栈引擎。`VCP.md`
又明确把模型、工具、记忆组织成闭环，并让模型通过文本协议主动调用工具。

如果桌面端只拥有普通网页权限，这一目标无法成立。文件、Shell、Python、系统工具、
桌面挂件、同步和设备能力因此被逐步纳入同一个产品。

### 6.2 VCPChat 与 VCPToolBox 是同一作者主导的配套系统

Git 历史显示，VCPChat 在 2025-06-16 的 `5297d48` 中正式引入 VCP 分布式服务器。
它没有另建一套低权限协议，而是直接作为 VCPToolBox 的远端能力节点注册工具并接收
`execute_tool`。

### 6.3 后来的权限拆分是产品内部分工，不是零信任重建

2026-04-05 的 `73840d2` 将单一 preload 迁移为 `chat`、`utility`、`desktop` 三个角色。
这是一项真实的隔离改进，但每个角色仍保留大量 IPC，同时继续暴露兼容
`electronAPI`。它降低了误用面，没有把系统改造成任务级 capability 模型。

## 7. 关键权限发现

### F-01 HIGH：role preload 已拆分，但权限集合仍然很宽

主窗口使用：

```text
contextIsolation: true
nodeIntegration: false
preload: preloads/chat.js
```

这是正向基础。静态解析当前三个 `ALLOWED_KEYS` 得到：

| preload | 唯一 API key 数 |
|---|---:|
| `chatAPI` | 163 |
| `utilityAPI` | 180 |
| `desktopAPI` | 59 |
| 三者 union | 319 |
| 三者共同拥有 | 14 |

问题不在于 Electron 完全没有隔离，而在于：

- `utilityAPI` 是许多通用子窗口的默认 preload。
- `utilityAPI` 包含 Python 执行、文件/便签操作、插件 manifest/config 写入和插件启停。
- `chatAPI` 包含 Agent、历史、文件、VCP、Flowlock、桌面推送和系统工具入口。
- `desktopAPI` 包含挂件文件、快捷方式、系统指标、凭据和系统工具入口。
- 三份 preload 继续构造兼容 `electronAPI`；大量 renderer 代码仍使用这个旧名称。

`contextIsolation` 只能隔开 renderer 与 Node 上下文，不能替代 IPC 动作授权。

主要证据：

```text
main.js:310-326
modules/services/preloadPaths.js:3-18
preloads/chat.js:432-604
preloads/utility.js:441-629
preloads/desktop.js:426-493
preload.js:1-2
```

### F-02 CRITICAL：通用 utility 窗口能够提交任意 Python 源码给本机解释器

`main.js` 注册 `execute-python-code`，收到源码字符串后启动：

```text
python -u
```

然后把传入代码写入解释器 stdin。`utilityAPI` 将 `executePythonCode` 放入允许列表，
而 text viewer 会调用它。

这不是错误功能。它是产品有意提供的本机代码执行能力。问题是它当前由窗口角色授权，
没有任务 permit、资源范围、期限、调用次数、工作目录和副作用级别约束。

主要证据：

```text
main.js:1097-1112
preloads/utility.js:297
preloads/utility.js:498
modules/text-viewer.js:1211-1233
```

### F-03 CRITICAL：AI 挂件的“沙箱”不是安全隔离边界

模型输出可以通过 `<<<[DESKTOP_PUSH]>>>` 进入桌面挂件链。挂件管理器会处理 HTML
中的内联脚本和外部脚本。

当前所谓 sandbox 是同一 renderer 中的 IIFE 和 Shadow DOM 包装：

- 包装函数把真实 `window` 作为 `_realWindow` 传入。
- 用户脚本与 `_realWindow` 处于同一词法作用域。
- `window` Proxy 对未特殊处理的属性直接返回真实 window 属性。
- 跨域/CDN script 会被直接创建为普通 `<script src=...>`。
- 本地脚本 fetch 失败时也回退成未包装的普通 script。

因此它可以帮助 DOM 组织和定时器清理，但不能被当作恶意或被注入脚本的安全沙箱。
同时，桌面 CSP 允许 `'unsafe-inline'`，这是为了支持这套可编程挂件模型。

主要证据：

```text
modules/messageRenderer.js:301-302
modules/renderer/streamManager.js:1845-2009
Desktopmodules/core/widgetManager.js:426-625
Desktopmodules/core/widgetManager.js:627-690
Desktopmodules/desktop.html:6-14
Desktopmodules/README.md:216-255
```

### F-04 CRITICAL：桌面 renderer 可取得真实后端凭据材料

`desktop-get-credentials` 从项目 `AppData` 读取 VCP server URL、VCP API key、论坛用户名
和密码，并把这些字段直接返回给 desktop renderer。`desktopAPI` 对该方法开放。

`vcpProxy.js` 随后在 renderer 内缓存并使用这些材料。虽然文档把它称为代理，但凭据
本身已经进入 renderer；再结合上一节的挂件脚本边界，不能把它视为 secret broker。

本轮只读取了源码，**没有读取任何实际凭据值**。

主要证据：

```text
modules/ipc/desktopHandlers.js:1279-1322
preloads/desktop.js:400
preloads/desktop.js:455
Desktopmodules/api/vcpProxy.js:9-40
```

### F-05 CRITICAL：分布式节点把共享 VCP_Key 当作广泛执行信任

VCPDistributedServer 连接 VCPToolBox 时使用：

```text
/vcp-distributed-server/VCP_Key=<key>
```

连接后会注册本地插件，并直接处理主服务器发来的 `execute_tool`。普通插件调用进入
`pluginManager.processToolCall`，没有经过统一、不可绕过的 task permit 或每次动作审批。

当前 checkout 有 25 个可发现的 active plugin manifest，包含：

```text
FileOperator
PowerShellExecutor
OldPowerShellExecutor
PTYShellExecutor
DesktopRemote
ScreenPilot
PluginSourceViewer
VCPMobileSync
```

这说明 `VCP_Key` 不是普通“登录口令”，而接近对整台桌面节点的广泛委托凭据。

主要证据：

```text
VCPDistributedServer/VCPDistributedServer.js:240-265
VCPDistributedServer/VCPDistributedServer.js:575-595
VCPDistributedServer/VCPDistributedServer.js:642
VCPDistributedServer/Plugin.js:178-203
```

### F-06 HIGH：工具注册可能把插件 config.env 内容带入可信网格

分布式插件加载器会读取插件自己的 `config.env`，解析为
`manifest.pluginSpecificEnvConfig`。`getAllPluginManifests()` 返回这些原始 manifest，
`registerTools()` 再把它们作为 JSON 发给 VCPToolBox。

当前源码在这个内部注册路径上没有看到字段级脱敏。正确判断是：

> 敏感插件配置可能在 VCP 可信网格内部传播；这不是已经证明的公网泄漏，但不应继续
> 依赖“节点都可信，所以可以传全部配置”的假设。

本轮没有读取任何 `config.env` 内容。

主要证据：

```text
VCPDistributedServer/Plugin.js:127-138
VCPDistributedServer/Plugin.js:166-168
VCPDistributedServer/VCPDistributedServer.js:301-333
```

### F-07 CRITICAL：内部文件请求允许可信主服务器读取节点本地文件

`internal_request_file` 接受 `file://` URL，转换成本地路径后直接读取文件，并以 Base64
返回。源码没有在这里建立允许根目录、任务资源清单或文件类型限制。

这再次证明当前分布式协议的真实假设是：

```text
已连接的 VCP 主服务器
  == 可以被桌面节点广泛信任的控制者
```

主要证据：

```text
VCPDistributedServer/VCPDistributedServer.js:599-624
```

### F-08 HIGH：移动同步令牌同时覆盖读、写和删除

`VCPMobileSync`：

- WebSocket 绑定 `0.0.0.0`，使用 query token。
- HTTP 允许 `x-sync-token`、query token 或 Bearer token。
- HTTP CORS 为 `*`。
- 同一 token 可以访问同步读取、写入和删除路由。
- 删除实体可能递归移除 Agent 或 Group 的物理目录。

同步实现并非没有工程保护。它已有 ID 清洗、锁、索引、tombstone、hash、幂等和版本
处理。核心缺口是授权粒度和传输信任，不是简单的数据一致性缺失。

主要证据：

```text
VCPDistributedServer/Plugin/VCPMobileSync/transport/websocket.js:41-83
VCPDistributedServer/Plugin/VCPMobileSync/transport/routes.js:41-60
VCPDistributedServer/Plugin/VCPMobileSync/transport/routes.js:260-297
VCPDistributedServer/Plugin/VCPMobileSync/sync/entity.js:663-741
```

### F-09 HIGH：插件管理 UI 能直接改变执行面

utility preload 暴露：

```text
pluginManagerSaveManifest
pluginManagerSaveConfigEnv
pluginManagerSetPluginEnabled
pluginManagerOpenPluginFolder
```

对应 IPC 可以写 `plugin-manifest.json`、写 `config.env`，并通过文件改名启停插件。
这对私人桌面工具很方便，但在 AGENTS OS 中属于权限边界变化，不能只凭“打开的是插件
管理窗口”就获得永久授权。

主要证据：

```text
preloads/utility.js:433-437
preloads/utility.js:617-621
modules/ipc/desktopHandlers.js:2093-2182
```

## 8. 已确认的正向基础

这份报告不把“权限很高”误写成“项目没有安全设计”。当前已有的正向基础包括：

- 主窗口和主要子窗口普遍启用 `contextIsolation` 并关闭 `nodeIntegration`。
- preload 已经按 chat、utility、desktop 拆分，未允许的方法会生成隔离 stub。
- 主窗口阻止直接导航到外部 HTTP(S)，全局新窗口处理器把外链交给系统浏览器。
- 分布式连接有重连、停止和部分资源清理逻辑。
- 移动同步有路径 ID 清洗、锁、hash、tombstone 和幂等结构。
- 桌面挂件有生命周期和定时器回收设计，不只是粗暴拼接 HTML。
- Rust assistant engine 有独立跨平台 CI。
- 项目仍在高频维护，不是冻结的旧 demo。

这些基础足以支持渐进加固，不足以证明可以无治理地加载真实秘密和全部高权限插件。

## 9. AGENTS OS 中的正确定位

### 9.1 应该承担

```text
desktop interaction host
human-facing task and status surface
governed local execution host
AI desktop and widget surface
VCPToolBox desktop capability adapter
VCPMobile synchronization peer
```

### 9.2 不应该承担

```text
AGENTS OS global permission authority
canonical global task ledger
permanent root identity for every Agent
global secret owner
global memory authority
sole audit authority
unscoped remote executor
```

### 9.3 推荐的调用关系

```text
Jenn
  -> AGENTS OS authority policy
    -> task-scoped permit
      -> VCPChat host gate
        -> role IPC / distributed plugin / desktop widget / sync action
          -> result + bounded evidence
```

关键要求是 permit 在真正副作用发生前由 host 强制检查，不能只写进 system prompt。

## 10. 下一阶段计划

### Phase C0：冻结新增高权限面

- 暂停新增通用 IPC、共享 token 角色和远程工具类别。
- 保持 upstream checkout 可追踪，不在未经设计的情况下直接重构全项目。
- 为当前 319 个 role API 建立机器可读 capability inventory。

### Phase C1：收口 renderer 与 secret 边界

- 把 `desktop-get-credentials` 改成 main-process 内部代理，不向 renderer 返回明文材料。
- 把 provider、admin 和 VCP key 访问迁入 secret broker。
- 为 IPC handler 增加 caller role、window identity、action class 和 resource scope 检查。
- 从通用 utility preload 移除任意 Python 和插件配置写入，改成专用窗口或 task permit。

### Phase C2：重做挂件隔离

- 不再把 IIFE、Shadow DOM 或 Proxy 称为安全沙箱。
- AI/远端挂件进入独立 sandboxed renderer、iframe 或独立进程。
- 禁止挂件访问真实 `window.desktopAPI`、`electronAPI` 和凭据。
- 外部 script 使用 allowlist、完整性校验或禁用；不得未包装回退执行。
- 将 widget capability 明确分为只读数据、受控动作和禁止动作。

### Phase C3：建立 VCP distributed host gate

- 共享 `VCP_Key` 只用于迁移期兼容，不再代表全部设备和全部工具权限。
- 每台设备有稳定 identity 和独立凭据。
- 工具注册必须经过 allowlist、schema 校验、签名/来源检查和配置脱敏。
- 每个 `execute_tool` 必须携带 task permit、nonce/idempotency key、期限和资源范围。
- `internal_request_file` 改为显式 artifact handle，不接受任意 `file://` 路径。

### Phase C4：拆分移动同步权限

```text
sync.read
sync.write
sync.delete
sync.attachments
sync.identity
```

- 删除权与普通同步权分离。
- token 不放 query string。
- 只允许 TLS 或明确的私有认证传输层。
- 设备撤销后旧凭据立即失效。

### Phase C5：测试和故障恢复

- 为 preload allowlist、IPC caller checks、widget isolation、tool permits 和 sync scopes 建测试。
- 增加 Electron 主链的 CI，而不是只验证 Rust assistant engine。
- 覆盖重复请求、断线重连、超时、进程崩溃、撤销和错误回执。

### Phase C6：三任务验收

1. 只读查看桌面状态：自动执行，无凭据泄露。
2. 在限定目录创建并读取一个临时文件：可幂等重跑，可追踪资源范围。
3. 发送一次本地通知或受控桌面动作：permit 到期后不能再次调用。

## 11. 当前最终决策

```yaml
component: VCPChat
directory: runtime/VCPChat
role: desktop_interaction_and_governed_execution_host
capability_posture: preserve_high_capability_ceiling
standing_authority_posture: reduce_and_scope
current_integration_status: SOURCE_MAPPED_NOT_TRUSTED_BY_DEFAULT
runtime_activation_authorized_by_this_document: false
secret_access_authorized_by_this_document: false
provider_execution_authorized_by_this_document: false
```

最终判断：

> VCPChat 的价值正来自它拥有真实桌面能力。下一步不是把它削成普通聊天壳，而是把
> “窗口一旦拿到 API 就长期拥有能力”改成“任务拿到有限 permit，host 才执行一次明确
> 动作”。

## 12. 主要证据索引

```text
runtime/VCPChat/README.md
runtime/VCPChat/VCP.md
runtime/VCPChat/package.json
runtime/VCPChat/main.js
runtime/VCPChat/preload.js
runtime/VCPChat/preloads/chat.js
runtime/VCPChat/preloads/utility.js
runtime/VCPChat/preloads/desktop.js
runtime/VCPChat/modules/services/preloadPaths.js
runtime/VCPChat/modules/ipc/desktopHandlers.js
runtime/VCPChat/modules/text-viewer.js
runtime/VCPChat/modules/messageRenderer.js
runtime/VCPChat/modules/renderer/streamManager.js
runtime/VCPChat/Desktopmodules/README.md
runtime/VCPChat/Desktopmodules/desktop.html
runtime/VCPChat/Desktopmodules/core/widgetManager.js
runtime/VCPChat/Desktopmodules/api/vcpProxy.js
runtime/VCPChat/VCPDistributedServer/VCPDistributedServer.js
runtime/VCPChat/VCPDistributedServer/Plugin.js
runtime/VCPChat/VCPDistributedServer/Plugin/VCPMobileSync/transport/websocket.js
runtime/VCPChat/VCPDistributedServer/Plugin/VCPMobileSync/transport/routes.js
runtime/VCPChat/VCPDistributedServer/Plugin/VCPMobileSync/sync/entity.js
```
