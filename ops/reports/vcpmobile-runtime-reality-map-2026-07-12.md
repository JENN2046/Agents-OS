# VCPMobile Runtime Reality Map and AGENTS OS Integration Plan

```yaml
document: VCPMobile Runtime Reality Map and AGENTS OS Integration Plan
version: v0.1
date: 2026-07-12
status: FINDINGS_ONLY
scope: /home/jenn/AGENTS_OS_Workspace/runtime/VCPMobile
upstream: https://github.com/MRiecy/VCPMobile
branch: main
head: b386d06a231985777de6038b78350a6801de4498
application_version: 1.1.3
method: source-first read-only audit with remote repository and CI verification
runtime_activation: not_performed
device_execution: not_performed
provider_execution: not_performed
private_data_read: not_performed
active_config_read: not_performed
runtime_source_modified: false
```

## 1. 这份报告回答什么

这份报告记录 VCPMobile 当前源码的真实状态，而不是复述 README，也不因为它属于 VCP
生态就默认它已经适合进入 AGENTS OS 的可信运行链。

它回答六个问题：

1. VCPMobile 当前到底是什么，已有多少真实工程能力。
2. 前端、Tauri、Rust、Kotlin、SQLite 和网络服务之间怎样连接。
3. 哪些窗口、IPC、文件、密钥、同步、传感器和更新路径拥有实际权限。
4. 哪些问题是当前源码直接证明，哪些仍需 Android 真机和运行时验证。
5. 它在 AGENTS OS 中应该承担什么角色，又不应该拥有什么权力。
6. 下一阶段需要按什么顺序收口，达到什么条件后才允许接入真实数据。

本轮明确没有：

- 读取 `.env`、真实 API key、Token、Cookie、provider 配置或活动认证状态。
- 读取聊天数据库、同步日志、缓存、SSE 缓存、私人记忆或 provider raw response。
- 安装依赖、启动 Tauri/Vite、构建 APK、启动 Android Service 或连接真机。
- 调用模型、同步服务器、分布式 VCP、OTA、root shell 或其他外部执行能力。
- 修改 VCPMobile 源码、配置、Git 索引或运行状态。

因此，本文能够确认源码中的能力、默认值、信任边界和可达调用链；不能把静态判断伪装成
已经完成的设备攻击 PoC、网络联调或长期稳定性验证。

## 2. 证据等级

| 等级 | 含义 | 可以得出的结论 |
|---|---|---|
| `SOURCE_PROVEN` | 当前 commit 的源码、manifest、workflow 或依赖直接证明 | 可确认代码路径、默认行为和结构性缺陷 |
| `REPOSITORY_VERIFIED` | 本地 Git 与实际 upstream 状态已核验 | 可确认审查对象、版本和公开 CI 状态 |
| `RUNTIME_REQUIRED` | 必须启动应用、连接真机或服务才能确认 | 不得报告为已复现、已利用或已稳定 |
| `CONFIG_DEPENDENT` | 取决于未读取的活动配置、权限或密钥 | 只能确认能力存在，不能确认当前启用 |
| `DOC_CLAIM` | 只来自 README 或说明文字 | 仅代表意图，不代表当前实现事实 |

风险等级：

```text
CRITICAL  可形成高权限代码执行、可信前端替换或系统性数据完整性破坏
HIGH      可造成敏感数据暴露、越权设备能力、静默数据丢失或显著资源耗尽
MEDIUM    需要额外前提，但会削弱隔离、隐私、恢复能力或运维可信度
LOW       文档、可维护性、供应链卫生或局部工程一致性问题
```

## 3. 最终结论

**VCPMobile 不是一个简单的网页套壳，也不是只完成了界面的原型。**

它已经形成一套真实的移动运行时客户端：

```text
Vue 3 application UI
  -> Tauri v2 WebView and IPC
    -> Rust application services
      -> SQLite / files / HTTP / WebSocket / SSE
        -> Kotlin Android plugin and system services
          -> notifications / sensors / overlay / wake locks / installer / root shell
```

它包含聊天、附件、RAG、同步、移动传感器、分布式工具、通知、浮窗、APK 更新、前端 OTA、
数据库维护和后台保活等真实能力。其功能深度和代码规模都明显超过实验项目。

但当前不能把它视为 AGENTS OS 的可信移动执行节点：

```yaml
functional_depth: HIGH
engineering_depth: HIGH
architecture_cohesion: MEDIUM_HIGH
security_readiness: NOT_READY
privacy_readiness: NOT_READY
sync_reliability: NOT_READY
release_trust: NOT_READY
agents_os_fit: CONDITIONAL
```

最关键的原因不是某一个普通 bug，而是多个权限面目前连成了完整高危链：

```text
远端或模型内容
  -> 未统一净化的 HTML / CSS
  -> CSP 未启用
  -> 应用 WebView 可调用宽泛 IPC
  -> vcp-mobile plugin allow-all
  -> Android 系统能力 / 任意 root command
```

另外，前端 OTA 可以把下载的前端包重新放回保留 IPC 权限的应用 origin，但其下载、签名、
解压和激活边界不足。这等价于给“前端代码安装”授予了接近本地应用代码的权力，却没有匹配
该权力的供应链验证。

大白话判断：

> VCPMobile 已经是一台功能很强的遥控终端，但门、钥匙、更新通道和失败回执还没有分开。
> 它现在适合继续研究和加固，不适合拿真实秘密、私人记忆、Root 权限和主力手机直接压测。

## 4. 仓库现实快照

```text
canonical path: /home/jenn/AGENTS_OS_Workspace/runtime/VCPMobile
upstream:        https://github.com/MRiecy/VCPMobile
branch:          main
HEAD:            b386d06a231985777de6038b78350a6801de4498
upstream state:  main aligned with origin/main at audit time
worktree:        clean at audit closeout
version:         1.1.3
latest commit:   Add permissions for new commands in vcp-mobile plugin
commit date:     2026-07-05T15:35:33+08:00
```

审查时的静态规模约为：

```text
tracked files: about 616
repository size: about 29 MB
Rust: about 35k lines
Vue: about 18k lines
TypeScript: about 12.7k lines
Kotlin: about 6.3k lines
Tauri command registrations: about 119 handler entries
Rust tests: 54 #[test] / #[tokio::test]
TypeScript tests: 23 test/it cases in 8 files
Kotlin tests: 7 @Test cases
```

当前本地没有 `pnpm`、`node_modules` 或 Rust build target，因此本轮没有伪造本地测试
结论。公开 CI 的事实为：

- v1.1.3 release workflow 曾成功完成构建和 APK 签名检查：
  <https://github.com/MRiecy/VCPMobile/actions/runs/28711281724>
- 当前审查 commit 对应的后续 main CI 在 `Android Plugin Unit Tests` 失败：
  <https://github.com/MRiecy/VCPMobile/actions/runs/28734368865>

所以不能把当前 main 报告为完全绿色。

## 5. 目录与 AGENTS OS 角色判断

### 5.1 正确目录

`runtime/VCPMobile` 是正确位置，理由是：

- 它是完整、可独立跟踪 upstream 的运行时客户端，不是 Jenn 自有的单个扩展插件。
- 它包含 Android 原生层、构建链、数据库和后台服务，不适合放进 `extensions/`。
- 它不是实验片段，不适合放进 `labs/`。
- 它会直接承载真实交互和设备权限，必须按 `runtime/` 高谨慎边界管理。

应继续保持：

```text
runtime/VCPMobile/     upstream-trackable source checkout
ops/reports/           AGENTS OS 对它的事实报告、审查和接入计划
control-plane/         未来由 AGENTS OS 定义的 permit / capability 合同
governance/            移动执行权限、秘密、记忆和外部副作用边界
```

不要把 AGENTS OS 的治理文件直接混入 upstream 源码，除非将来明确建立维护分支或 fork。

### 5.2 它应该是什么

推荐角色：

```text
mobile interaction client
constrained edge capability node
notification and presence surface
sensor and device-effect adapter
human approval and status surface
```

它可以负责：

- 向 Jenn 展示对话、任务状态、通知和执行结果。
- 在明确授权下提供移动设备能力，例如位置、剪贴板、通知和文件选择。
- 承载短生命周期的人工批准入口。
- 作为 VCPToolBox、Codex host 或其他 executor 的受限客户端。
- 提供移动端离线缓存与恢复，但不成为全局事实权威。

### 5.3 它不应该是什么

```text
not AGENTS OS kernel
not canonical task ledger
not policy authority
not memory owner
not permit issuer
not trusted arbitrary executor
not root-capability broker
```

VCPMobile 应当消费由治理层签发的短期 capability/permit，并回传低披露结果与可核验状态；
不能由移动端自己决定“有什么权限、是否允许、是否执行成功”。

## 6. 进程、窗口与信任边界

### 6.1 主要运行单元

| 运行单元 | 当前职责 | 主要信任问题 |
|---|---|---|
| Vue WebView | 聊天、设置、附件、更新、同步和设备 UI | 接收远端内容，同时能调用高权限 IPC |
| Rust Tauri process | DB、文件、网络、同步、更新和 plugin bridge | 命令面宽，缺少按窗口最小授权 |
| Kotlin plugin | Android 系统能力与 service | default permission 暴露全部 command |
| `:helper` SSE process | 后台流式请求、缓存、通知、保活 | 非 isolated process，localhost 无认证 |
| local assistant server | 本地 HTTP/WS 辅助界面 | 当前关闭；若恢复会暴露完整 Settings |
| SQLite database | 设置、聊天、同步与索引 | 明文、备份和腐败副本保留问题 |

### 6.2 窗口与 capability

`src-tauri/capabilities/default.json:5-13` 将 capability 应用于：

```text
main
vcp-portal-*
assistant
```

并允许：

```text
vcp-mobile:allow-all
core:webview:allow-create-webview-window
core:window:allow-create
```

`src-tauri/plugins/vcp-mobile/permissions/default.toml` 与 `all.toml` 实际上都允许插件的
全部命令，包括 root command、临时文件、传感器和 wake lock。Kotlin contract test 还把
“default permission 必须包含全部 command”写成了测试约束。

Tauri v2 官方文档说明，应用通过 `invoke_handler` 注册的命令默认可供应用窗口调用，除非用
`AppManifest::commands` 进一步定义命令访问控制：
<https://v2.tauri.app/security/capabilities/>

当前 `src-tauri/build.rs` 只有 `tauri_build::build()`，没有发现该命令级清单。

## 7. 关键发现

### F-01 CRITICAL：远端内容可进入高权限 WebView

证据等级：`SOURCE_PROVEN`

远端、模型和工具内容存在多条原始 HTML 路径：

- `src-tauri/src/vcp_modules/chat/pre_renderer/markdown_parser.rs:928-934`
  保留 `Event::Html` 和 `Event::InlineHtml`。
- `src/core/utils/astRenderer.ts:108-109,166-167` 返回原始 HTML 内容。
- `src/core/utils/astExecutor.ts:332-345,453-463` 将内容写入 `innerHTML`。
- `src/features/chat/MessageRenderer.vue:976` 使用 `v-html`。
- `src/features/chat/blocks/ToolBlock.vue:219-290` 使用 `marked.parse` 和 `v-html`，没有统一
  DOMPurify 边界。
- `src/features/assistant/AssistantMessageCard.vue:117` 存在相同模式；功能当前暂停并不等于
  权限链已经消失。
- `src/features/rag/RagPayloadDetail.vue` 只在部分分支执行 escape。

同时：

- `src-tauri/tauri.conf.json:21-26` 设置 `csp: null`，asset protocol scope 为 `**`。
- `src/core/composables/useMessageStyleInjector.ts:16-55` 将模型控制 CSS 经正则处理后插入
  document head；正则不是 CSS 安全解析器，不能可靠阻止 at-rule、远端资源或 UI redress。
- capability 和 plugin permission 没有按窗口、命令和业务场景拆分。
- `src-tauri/plugins/vcp-mobile/android/src/main/java/com/vcp/mobile/VcpMobilePlugin.kt:767-777`
  把任意命令交给 `Shell.cmd(args.command).exec()`，没有 allowlist 或 permit。

Tauri 官方 CSP 文档明确说明只有配置 CSP 才会启用相应保护，并建议尽量严格：
<https://v2.tauri.app/security/csp/>

源码层面的结论：

```text
renderer compromise
  -> broad Tauri IPC
    -> vcp-mobile plugin commands
      -> Android system effects
        -> arbitrary root command when device/root environment permits
```

本轮没有执行恶意 payload 或 root PoC，所以不能报告为设备上已经成功利用；但修复顺序必须
按完整可达链处理，不能只在某一个 `v-html` 上打补丁。

### F-02 CRITICAL：前端 OTA 缺少可信安装边界

证据等级：`SOURCE_PROVEN`

启动路径会周期性检查前端版本，并可能自动下载和应用：

- `src-tauri/src/vcp_modules/infra/lifecycle_manager.rs:280-369`

主要问题：

1. `src-tauri/src/vcp_modules/updater/frontend_update_manager.rs:267-348` 的下载命令接受
   调用者提供的 URL，没有固定可信 origin、scheme 和严格总大小策略。
2. `verify_unzipped_files` 在 manifest 缺失时返回成功。
3. manifest 与待验证文件来自同一个未签名 ZIP，不能证明发布者身份。
4. `apply_frontend_update` 接受调用者提供的 `zip_path` 和 `version`。
5. 解压使用 `version_dir.join(file_in_zip.name())`，没有 `enclosed_name()` containment。
6. `version` 也直接参与目录拼接，可形成独立的路径逃逸面。
7. ZIP entry 按声明大小读入内存，缺少压缩比、总展开量和文件数限制。
8. `src-tauri/src/vcp_modules/updater/ota_assets.rs:10-40` 把更新内容作为
   `https://tauri.localhost` 的应用资源继续提供，并保留 IPC。
9. `src/main.ts:24-31` 在 Vue mount 后很早就确认启动成功，没有验证核心功能与安全状态。

`.github/workflows/release.yml:169-185` 只把 `dist` 打包上传，没有签名 frontend manifest、
独立信任根、SBOM 或 provenance。

这意味着前端 OTA 不是普通静态资源刷新，而是“安装新的高权限应用前端”。当前设计还存在：

```text
arbitrary download origin
unsigned/self-authenticating package
Zip Slip and version path traversal
zip bomb / disk / memory exhaustion
premature activation confirmation
privileged-origin execution
```

在完成签名、固定 origin、安全解压和原子激活前，AGENTS OS 集成配置应禁用前端 OTA。

### F-03 HIGH：秘密与私人数据以普通应用数据保存

证据等级：`SOURCE_PROVEN`

`src-tauri/src/vcp_modules/infra/settings_manager.rs:17-57` 的 Settings 包含：

```text
vcp_api_key
vcp_log_key
distributed_vcp_key
sync_token
admin_password
file_key
```

`settings_manager.rs:199-215` 将整个 Settings 以 pretty JSON 写入 SQLite；
`settings_manager.rs:135-162` 又把完整对象返回 WebView。

当前没有发现：

```text
SQLCipher
Android Keystore-backed secret separation
Tauri Stronghold
redacted settings DTO
per-secret capability checks
```

数据库位于应用配置/文件目录。Android manifest 没有明确设置 `allowBackup=false` 或数据提取
排除规则。Android 官方文档说明 `android:allowBackup` 默认值为 true，Auto Backup 默认包含
大部分内部应用文件：<https://developer.android.com/identity/data/autobackup>

实际是否上传由 Android 版本、OEM、账户与用户设置决定，但源码中没有建立明确排除边界。

`src-tauri/src/vcp_modules/persistence/db_manager.rs` 的损坏恢复会保留
`.corrupt.<timestamp>` 数据库副本，并删除
WAL/SHM；没有发现腐败副本的生命周期清理。这既可能长期复制敏感数据，也可能丢失最新 WAL
内容。

校正说明：`src/core/stores/settings.ts` 没有把 Settings 持久化到 localStorage。秘密在读取后
存在于 WebView 内存，但没有被该 store 再复制到 localStorage。

### F-04 HIGH：文件边界允许路径逃逸、移动和非预期读取

证据等级：`SOURCE_PROVEN`

主要证据：

- `src-tauri/plugins/vcp-mobile/src/system.rs:502-513` 的 `write_temp_file` 使用
  `cache_dir.join(file_name)`，没有限制绝对路径、`..` 或总大小。
- 删除临时文件只做 lexical `starts_with`，没有 canonicalize 后再验证。
- `src-tauri/src/vcp_modules/infra/file_manager.rs:223-268` 的安全路径允许整个 config、cache、
  attachments、thumbnails 和 multimodal 目录。
- `register_local_file` 只验证 `expected_hash` 格式，没有重新计算文件 hash。
- 目标存在时会删除 source；不存在时会 move/copy 后删除 source。
- `thumbnail_path` 没有经过同等安全路径检查。
- `get_attachment_real_path` 拼接调用者提供的 hash 后只检查文件是否存在。
- `store_file` 允许最高约 100 MB 内容通过 JSON IPC 进入 Rust，远高于前端普通路径。

`src-tauri/src/vcp_modules/infra/high_speed_channel.rs` 使用随机 token 作为返回值，但服务端
没有实际解析和验证 token；同时：

```text
CORS: *
accept arbitrary local socket client
unbounded header accumulation before CRLF
caller-declared body size
no total upload/session quota
```

`src-tauri/src/vcp_modules/infra/vcp_client.rs` 允许前端提供 `vcp_url`、key、messages 和
`local_file` 路径，媒体桥没有统一调用中央 `ensure_safe_path`。若 WebView 已被控制，可尝试
读取并向外发送应用可访问的媒体扩展文件。

文件提取器对顶层文件有约 50 MB 限制，对输出文本有约 1000 万字符限制，这是正向控制；
但 DOCX/PPTX/XLSX 内层 ZIP XML 使用无总展开限制的 `read_to_string`，仍可能在文本上限检查
前触发压缩炸弹式内存占用。

### F-05 HIGH：localhost SSE helper 没有认证与完整资源上限

证据等级：`SOURCE_PROVEN`

`SseProxyService` 运行在单独的 `:helper` process，但没有配置 `isolatedProcess=true`：

- `src-tauri/plugins/vcp-mobile/android/src/main/AndroidManifest.xml:31-38`

正向控制包括：

- service 不导出。
- 监听 `127.0.0.1` 随机端口。
- port 文件位于私有应用目录。
- 单条长度前缀命令限制约 10 MB。

但 TCP 协议本身没有认证：

- `SseProxyService.kt:162-225` 接收本地 JSON command。
- `SseProxyService.kt:258-321` 允许命令提供 URL、headers、body 和 requestId。
- 同一 requestId 可覆盖 map entry，而旧 EventSource 不一定被取消。
- `SseProxyService.kt:425-443` 的 session event buffer 没有事件数或字节数上限。
- 远端读取超时为零，恶意或异常流可以长期占用 session、wake lock、wifi lock 和内存。
- 断线重建内容会明文写入 `cache/sse_cache`，约 24 小时后才清理。
- 后台通知可能展示完整模型回复内容，属于需要明确用户策略的隐私面。

随机端口降低偶然访问概率，但不是认证。具备 INTERNET 权限的本地应用可以扫描 loopback。

### F-06 HIGH：暂停的 local assistant server 不能按原设计恢复

证据等级：`SOURCE_PROVEN`

当前：

- `src-tauri/src/vcp_modules/infra/lifecycle_manager.rs:119-125,424-437` 强制保持 local
  assistant server 关闭。

这是有效的风险收口，本文不把它描述为当前正在监听的漏洞。

但其保留实现若重新启用，会在固定 `127.0.0.1:14202` 提供无认证 HTTP/WebSocket；
`get_initial_config` 会发送完整 Settings，包括密钥。Android 浮窗 WebView 还启用了 JavaScript、
DOM storage、database、`MIXED_CONTENT_ALWAYS_ALLOW` 和剪贴板 bridge。

结论：在完成 session authentication、最小 DTO、origin 绑定和 capability 分离前，不得仅为了
“恢复功能”而重新打开该 server。

### F-07 HIGH：同步取消、错误传播和成功语义不可信

证据等级：`SOURCE_PROVEN`

#### 发送通道所有权错误

`src-tauri/src/vcp_modules/sync/sync_service.rs:190-199` 初始化 `(tx, _rx)` 后立即丢弃
receiver，却把 tx 保存进 `SyncState.ws_sender`。

`start_manual_sync` 在 `sync_service.rs:1475-1510` 为真实 session 创建新的 `(tx, rx)`，但
没有把新 tx 写回 `state.ws_sender`。

结果：

- `stop_sync` 向旧的关闭通道发送 Cancel。
- 连接内层循环只监听真实 session rx。
- atomic flag 主要在外层和重试阶段检查。
- UI 可以显示停止，但传输仍可能持续到网络断开或 session 自行完成。
- topic、agent、avatar、group CRUD 通知也使用旧 sender，实时更新可能丢失。

#### 失败被吞掉

`src-tauri/src/vcp_modules/sync/sync_executor/push_executor.rs` 中：

- agent/group/avatar push 多处忽略 send error 和非 2xx status 后仍返回 `Ok`。
- attachment upload 在非 2xx 时仍可能返回成功。

`diff_handler.rs` 对若干 pull/push/delete 使用 `let _ =`，随后仍减少 pending 计数。

`batch_diff_handler.rs` 会记录单项失败，但仍把 topic 标记为 completed，最终发出完成状态。

因此当前“sync completed”不能证明每个对象和附件都完成，可能发生静默部分丢失。

#### 幂等与冲突语义不足

当前 idempotency key 基于 action、type、id 和当前分钟：

```text
hash(action, entity_type, entity_id, current_minute)
```

它不包含 payload、durable operation ID 或 session ID，并会跨分钟和重启变化。重试无法稳定
识别同一操作，不同内容又可能在同一分钟冲突。

冲突解决主要依赖设备 wall-clock `updated_at`，不是逻辑时钟或服务端序列。时钟偏差和相同
时间戳都可能造成覆盖。

公开 issue #20 还记录了 desktop 端同步数据库未初始化时新 agent/group 保存失败、聊天消息
被跳过的问题：<https://github.com/MRiecy/VCPMobile/issues/20>

该 issue 不能替代对移动客户端缺陷的证明，但说明端到端同步系统目前也未达到可信状态。

### F-08 HIGH：分布式工具在异常场景 fail-open，并存在数据流绕过

证据等级：`SOURCE_PROVEN`

当前源码实际注册 13 个工具，不是 README 所称的 14 个：

- `src-tauri/src/distributed/tools/mod.rs:26-48`

正向控制：

- 首次没有配置文件时，`tool_registry.rs:252-258` 会把全部工具写为 disabled。
- `distributed_enabled` 默认 false。

关键问题：

1. 配置文件存在但 open/read/JSON parse 失败时，disabled set 保持为空，相当于全部启用。
2. `is_enabled` 在 lock poisoning 时返回 true。
3. 保存使用 `File::create` 再写入，不是临时文件 + fsync + atomic rename。
4. 崩溃或截断配置可能使下次启动从“全部关闭”退化为“全部开启”。
5. 旧配置中没有出现的新工具默认启用。
6. `src-tauri/src/distributed/client.rs:370-390` 在检查单项工具开关前启动全部 native sensor
   collection。
7. `SensorStatusManager.kt` 全局启动 location、ambient、motion；有位置权限时可进行 1 秒一次
   的快速定位采样。
8. `MobileStatusSummary` 包含坐标和运动信息，因此关闭 `MobileLocation` 但保留 summary 仍可
   传出位置。
9. 单项 poll interval 当前没有被实际调度采用，placeholder 统一约 30 秒推送。
10. 服务端 execute request 对已启用工具直接执行，没有逐次 permit、expiry、nonce、replay
    protection、idempotency 或人工确认。
11. 连接后会自动请求 ipify 并报告公网 IP。
12. key 位于 WebSocket path，且允许 `ws://`，没有强制 TLS 与设备身份绑定。

剪贴板读取、写入和通知属于真实设备副作用，不应仅依赖本地布尔开关和远端工具名决定。

### F-09 MEDIUM_HIGH：Android 权限与保活设计过于宽泛

证据等级：`SOURCE_PROVEN`

manifest 申请或保留的能力包括：

```text
INTERNET
overlay
legacy storage compatibility
location
APK install
camera
microphone/audio
notifications
foreground services
battery optimization exemption
wake locks
```

`src-tauri/gen/android/app/src/main/AndroidManifest.xml:20-26` 还硬编码
`usesCleartextTraffic=true`，release placeholder 无法把它收紧。

`src/components/layout/PermissionGate.vue` 的 onboarding 强烈引导用户开启通知访问、开机自启、
无限制电池和至少 5 GB 存储。部分状态可以由用户自行勾选确认，不总是由系统权限事实驱动。

通知监听 service 虽然按 Android binding permission 导出，但 callback 当前不处理通知内容，
这是一个正向隐私事实。问题在于产品仍主动要求用户授予广泛、长期和高保活权限，而不是按
实际 capability 延迟申请。

AGENTS OS 生产配置应明确禁止 root 模式，并采用按任务临时授权，而不是首次启动一次性索要
长期权限。

### F-10 MEDIUM_HIGH：日志、缓存与恢复会复制敏感信息

证据等级：`SOURCE_PROVEN`

- VCPLog 后台缓存使用无总量上限的 `Vec<Value>`。
- VCPLog/VCPInfo key 被放进 WebSocket URL path。
- disconnect 路径存在输出完整 URL 的日志语句；当前 release logger 默认过滤到 WARN，因此
  这更接近 debug/配置变化时的潜在泄漏，而不是已证明的 release 日志泄漏。
- sync error body 可能进入持久化同步日志。
- `read_sync_log_file` 可把完整同步日志返回应用 WebView。
- SSE 断线缓存包含完整重建模型回复。
- 腐败数据库恢复保留新的敏感副本。

这些都需要统一的数据分类、redaction、上限、过期和访问 capability，而不是每个模块自行处理。

### F-11 MEDIUM：CI 有覆盖，但安全与供应链门禁不足

证据等级：`SOURCE_PROVEN` + `REPOSITORY_VERIFIED`

`.github/workflows/ci.yml` 已覆盖：

```text
TypeScript typecheck
Vitest
Rust fmt
Rust unit/integration tests
benchmark compilation
clippy
Kotlin plugin tests
```

这是实质工程基础，不应低估。

但当前未发现：

```text
CodeQL or equivalent static security analysis
dependency audit policy
Dependabot/Renovate policy
SBOM
artifact provenance/attestation
frontend OTA signature verification
capability regression tests
XSS / Zip Slip / path traversal negative tests
sync cancellation and partial-failure integration tests
```

`.github/workflows/release.yml` 在 release published 后独立构建，没有在 workflow 内重新执行
完整测试或显式依赖成功 CI。Action 引用主要使用可变 tag，而不是固定 commit SHA。

APK 签名验证是正向控制；但它保护 APK，不保护单独下载并激活的 frontend ZIP。

### F-12 LOW_MEDIUM：文档和脚本存在漂移

证据等级：`SOURCE_PROVEN`

- README 写 14 个分布式工具，源码为 13 个。
- `package.json` 中至少 5 个 script 指向缺失且被忽略的 `scripts/` 文件：
  `io:write`、`io:append`、`memory:refresh`、`dev:android`、`dev:usb`。
- 测试合同把宽泛 default plugin permission 当成正确行为，说明当前安全模型不仅是遗漏，还是
  被测试固化的设计决定。

这类漂移会让后续 AGENTS OS 适配基于错误入口和错误能力数量做规划。

## 8. 已确认的正向基础

这次审查不应得出“全部推倒重写”的结论。以下能力值得保留：

### 8.1 数据层

- SQLite WAL。
- busy timeout 和受限连接池。
- `quick_check`。
- 带 checksum 的 migration。
- FTS 搜索。
- 串行写队列。
- tombstone 和维护任务。
- 数据库损坏检测与自恢复意图。

### 8.2 移动运行能力

- Android plugin 与 Rust/Vue 的真实桥接。
- 独立 helper process 与后台通知设计。
- 附件、媒体、文件提取和上传链。
- 传感器、位置、浮窗、wake lock 和 installer 等真实设备能力。
- 首次分布式工具默认关闭。
- local assistant server 当前硬关闭。
- notification listener 当前不读取通知内容。

### 8.3 工程链

- 多语言 CI。
- Rust、TypeScript、Kotlin 均有测试。
- release APK 有签名与证书验证。
- 代码模块边界总体可辨识，具备逐项加固条件。

正确路线是收窄权限和修正合同，不是重写全部客户端。

## 9. 对前期判断的事实校正

以下结论已经在最终审查中修正，后续文档不得继续使用旧说法：

1. **Update release notes 已经经过 DOMPurify。**
   它不是当前主要 XSS 输入；主要入口在 message/tool/RAG/assistant rendering 和模型 CSS。
2. **Settings store 没有持久化到 localStorage。**
   风险是 SQLite 明文、完整 DTO 和 WebView 内存暴露，不是 Pinia localStorage 复制。
3. **实际注册 13 个 distributed tools。**
   README 的 14 个属于文档漂移。
4. **首次缺少 distributed config 时工具默认关闭。**
   真正问题是读取、解析、锁和旧配置场景下 fail-open。
5. **local assistant server 当前被强制关闭。**
   它是不得原样恢复的潜在能力，不是当前活跃监听事实。
6. **完整 URL 日志不是已证明的 release 常态泄漏。**
   当前 release filter 为 WARN；但 debug、配置变化或未来 logger 调整仍会暴露 URL path key。

## 10. AGENTS OS 接入决策

### 10.1 当前状态

```yaml
placement: runtime/VCPMobile
source_policy: upstream_trackable
integration_status: HOLD_FOR_HARDENING
real_secrets_allowed: false
private_memory_allowed: false
root_allowed: false
primary_phone_allowed: false
frontend_ota_allowed: false
distributed_effects_allowed: false
local_assistant_server_allowed: false
```

### 10.2 目标责任分配

| 事实或能力 | 推荐权威 |
|---|---|
| AGENTS OS 全局任务生命周期 | canonical task ledger，不在 VCPMobile |
| permit、policy、lease、replay protection | AGENTS OS governance/control kernel |
| 实际模型与工具执行 | VCPToolBox、Codex host 或 ColaMeta executor |
| 移动界面与人工批准 | VCPMobile |
| 设备传感器与本地副作用 | VCPMobile adapter，必须受 permit 控制 |
| 记忆内容和生命周期 | VCP native memory owner |
| 记忆访问治理 | codex-memory / governed memory bridge |
| 移动离线缓存 | VCPMobile，可重建且非全局权威 |

### 10.3 未来调用合同

移动设备副作用至少需要：

```yaml
permit_id: globally_unique
task_id: canonical_reference
capability: exact_tool_or_effect
subject: exact_device_identity
issued_by: governance_authority
issued_at: timestamp
expires_at: short_ttl
nonce: replay_protection
input_digest: bounded_payload_hash
scope: least_privilege
human_presence_required: boolean
idempotency_key: durable_operation_id
result_class: success | partial | failed | cancelled | expired
evidence: low_disclosure_receipt
```

VCPMobile 只验证和消费 permit；不能自签发，也不能因为本地设置为 enabled 就替代授权。

## 11. 分阶段整改计划

### Phase M0：隔离和基线冻结

目标：防止在加固前误用高权限路径。

动作：

1. AGENTS OS 接入配置明确禁用 frontend OTA、root command、distributed effects 和 local server。
2. 仅使用模拟数据、无真实密钥的 Android emulator 或专用测试设备。
3. 保持 upstream checkout clean；建立独立 hardening branch/fork 决策。
4. 固化当前 source/CI/manifest 基线和本报告 HEAD。
5. 明确 CC BY-NC-SA 4.0 对 fork、再分发和商业使用的边界。

退出条件：

```text
no real secret
no private memory
no root
no primary phone
no unsigned frontend update
```

### Phase M1：关闭 renderer 到 native 的高危链

动作：

1. 建立唯一 HTML sanitization boundary，覆盖 message、tool、RAG 和 assistant。
2. 禁止模型提供任意 CSS；改用结构化、安全 token 或严格 CSS parser/allowlist。
3. 配置严格 CSP，限制 script、style、connect、img、media 和 frame origin。
4. 使用 Tauri AppManifest command allowlist。
5. capability 按 `main`、portal、assistant 等窗口分开。
6. `default.toml` 改成最小权限；`allow-all` 仅保留为不被生产 capability 引用的开发集合。
7. 从可被 WebView 调用的命令面彻底移除 `run_root_command`。
8. 为每个高风险 IPC 增加 negative-path contract test。

退出条件：

```text
malicious model HTML cannot invoke script or privileged IPC
portal/assistant cannot inherit main authority
root command is unreachable from renderer
strict CSP passes desktop and Android tests
```

### Phase M2：重建 OTA 与发布信任

动作：

1. 在完成新设计前禁用 frontend OTA 自动应用。
2. 固定 HTTPS origin 和证书策略，不接受任意调用者 URL。
3. 使用离线保护的独立签名密钥签署 manifest。
4. manifest 绑定 version、全部文件 hash、总大小、文件数和兼容版本。
5. 使用 `enclosed_name()`，拒绝 absolute、parent、symlink 和特殊 entry。
6. 限制下载大小、单文件大小、总展开量、压缩比、文件数和磁盘余量。
7. staging 解压后验证，再原子切换 active version。
8. 启动确认等待核心 UI、DB、IPC 和安全自检完成。
9. release pipeline 生成 checksum、SBOM、provenance 和签名 evidence。

退出条件：

```text
unsigned/tampered/wrong-origin package rejected
Zip Slip and zip bomb fixtures rejected
activation is atomic and rollback tested
release artifact is traceable to tested source commit
```

### Phase M3：秘密、数据和文件边界

动作：

1. 将 API key、sync token 和 password 迁入 Android Keystore-backed store/Stronghold。
2. Settings API 拆成 public DTO、secret presence 和 gated secret update。
3. 配置 Android backup/data extraction exclusion。
4. 设计数据库加密和密钥恢复方案，避免把 recovery 变成永久不可恢复。
5. 所有文件入口先 canonicalize，再验证 containment。
6. 调用者 hash 必须由 native 重新计算。
7. 文件 move/delete 使用明确 source class 和 capability。
8. 统一 IPC、HTTP、ZIP、XML、附件和 extractor 大小限制。
9. 为 cache、logs、corrupt DB 和 SSE response 建立 retention 和 secure deletion policy。

退出条件：

```text
renderer cannot read raw secret
backup excludes protected data
path traversal fixtures rejected
hash mismatch cannot move/delete source
all untrusted payload paths have bounded memory and disk use
```

### Phase M4：同步正确性

动作：

1. 每个 sync session 拥有唯一 sender/receiver 和 cancellation token。
2. state 只引用当前 active session，结束时按 session ID compare-and-clear。
3. 停止操作必须等待 session 进入 terminal cancelled 状态。
4. 所有 HTTP/WS error 和非 2xx 必须传播到对象级结果。
5. 只有全部要求对象完成时才能报告 completed；部分失败必须报告 partial。
6. 使用 durable operation ID，而不是“当前分钟”生成幂等键。
7. 冲突语义使用服务端 sequence、logical clock 或明确版本向量。
8. pending/completed 状态持久化，支持 crash recovery。
9. 增加 kill、restart、duplicate、reorder、clock skew、network partition 和 attachment failure
   测试。

退出条件：

```text
cancel really stops active transfer
partial failure cannot become completed
retry does not duplicate effects
crash/restart resumes deterministically
two-device conflict tests have explicit outcomes
```

### Phase M5：分布式能力治理

动作：

1. 配置 read/parse/lock/version 错误全部 fail-closed。
2. 配置使用 temp + fsync + atomic rename，并带 schema version。
3. 新工具默认 disabled，必须显式迁移后启用。
4. 只为启用工具启动所需传感器，不全局预采集。
5. summary 不得泄露被单项开关禁止的数据。
6. 尊重每个工具的真实采样间隔和最小数据原则。
7. 强制 `wss://`、设备身份和服务端身份验证。
8. key 不放 URL path。
9. 所有设备副作用验证短期 permit、nonce、scope 和 idempotency。
10. 剪贴板读取、通知、位置和 root 类能力要求明确 human presence policy。

退出条件：

```text
corrupt config disables every effect
disabled sensor is neither sampled nor transmitted
replayed/expired/wrong-device permit rejected
cleartext transport rejected
device effect has deterministic receipt
```

### Phase M6：localhost、后台和 Android 产品边界

动作：

1. SSE helper 使用不可预测 session secret 和 authenticated handshake。
2. 为 session 数、事件数、字节数、持续时间和并发连接设置硬上限。
3. requestId 冲突必须拒绝或先可靠取消旧 session。
4. 默认不把完整模型回复写入持久 cache；需要时使用加密和短 TTL。
5. 通知内容提供敏感内容隐藏策略。
6. local assistant server 如需恢复，使用随机端口、认证 session、最小 DTO 和 isolated capability。
7. 权限按功能延迟申请，UI 状态必须来自系统事实。
8. AGENTS OS profile 禁止 root，并关闭非必要 overlay、autostart 和 unlimited battery 请求。

### Phase M7：验证与有限接入

按以下顺序放行：

```text
static negative tests
unit/integration tests
Android emulator with synthetic data
dedicated non-primary test device
local mock VCP server
network failure and crash campaign
governed permit benchmark
limited real-account canary
```

不得从静态修复直接跳到主力手机和真实私人记忆。

## 12. AGENTS OS 三任务 benchmark

在完成 M1-M5 后，用三个相同的 Green/Yellow 任务验证移动节点：

### Task A：只读状态查看

```text
input: synthetic task status
effect: none
expected: no secret, no sensor, no write, no privileged IPC
```

### Task B：受控设备通知

```text
input: short-lived notification permit
effect: one local notification
expected: exact once, expiry/replay enforced, receipt returned
```

### Task C：受控位置采样

```text
input: one-shot coarse-location permit
effect: one bounded sample
expected: no background continuation, no summary bypass, explicit user-visible state
```

测量：

```text
permit validation latency
human confirmations
duplicate effects
cancel latency
crash recovery
data minimization
receipt correctness
unexpected network calls
battery and memory bounds
diagnostic quality
```

只有三个任务都满足 exact-once/explicit-partial、fail-closed 和最小披露，VCPMobile 才能从
`HOLD_FOR_HARDENING` 进入 `LIMITED_CANARY`。

## 13. 验收矩阵

| 能力 | 当前 | 放行条件 |
|---|---|---|
| 普通聊天 UI | 条件可用 | HTML/CSS 安全边界与严格 CSP |
| Tauri IPC | 不可信宽权限 | command/window least privilege |
| Root command | 禁止 | 不进入 renderer 可达面；AGENTS OS profile 永久关闭 |
| Frontend OTA | 禁止 | 签名、固定 origin、安全解压、原子激活 |
| APK update | 有平台签名保护 | 固定 HTTPS origin、大小与版本策略 |
| Settings/secrets | 禁止真实秘密 | Keystore/Stronghold、脱敏 DTO、备份排除 |
| File bridge | 禁止私人文件 | canonical containment、native hash、配额 |
| Sync | 不可信完成语义 | cancellation、partial result、durable idempotency |
| Distributed tools | 禁止真实副作用 | fail-closed、per-tool collection、permit |
| SSE helper | 仅测试环境 | localhost auth、资源上限、缓存策略 |
| Local assistant server | 保持关闭 | auth、随机 endpoint、最小 capability |
| Primary phone | 禁止 | 完成 M1-M7 和有限 canary |

## 14. 许可证与上游维护边界

仓库 `LICENSE` 为 Creative Commons Attribution-NonCommercial-ShareAlike 4.0
International：

```text
CC BY-NC-SA 4.0
```

源码明确包含 attribution、NonCommercial 和 ShareAlike 条款。本文不提供法律意见，但 AGENTS OS
在以下动作前必须做许可证边界决策：

- 对外分发修改版 APK。
- 将修改后的客户端作为商业产品组成部分。
- 发布 fork 或衍生代码。
- 与其他不同许可证代码形成不可分离组合。

加固阶段建议：

```text
keep upstream remote read-only
maintain a clearly named hardening branch or private patch queue
separate AGENTS OS adapter contracts from upstream source where practical
record upstream commit for every audit and patch set
re-run the high-risk chain review after every upstream rebase
```

## 15. 未验证事项

以下内容不能从本轮静态审查中得出通过结论：

- APK 是否能在 Jenn 的具体 Android 设备正常构建、安装和长期后台运行。
- Android/OEM 对 backup、autostart、battery、overlay 和 notification 的实际行为。
- 当前真实 VCP server、VCPToolBox 或 VCPChat 的协议兼容性。
- 真实同步服务是否对重复、乱序、冲突和部分失败做了额外补偿。
- root command 在具体设备上的可用性和权限范围。
- WebView exploit 是否能在目标 Android WebView 版本稳定复现。
- SSE helper 在长时间真实流量下的内存、磁盘和电量曲线。
- release artifact 与当前本地源码的完整 reproducibility。
- 公开 issue #20 在最新 server/desktop 组合中是否已经被外部组件规避。

这些事项必须在修复 P0/P1 源码边界之后验证，不能通过现在启动真实服务来“证明没问题”。

## 16. 证据索引

核心证据路径：

```text
runtime/VCPMobile/src-tauri/tauri.conf.json
runtime/VCPMobile/src-tauri/build.rs
runtime/VCPMobile/src-tauri/capabilities/default.json
runtime/VCPMobile/src-tauri/plugins/vcp-mobile/permissions/default.toml
runtime/VCPMobile/src-tauri/plugins/vcp-mobile/permissions/all.toml
runtime/VCPMobile/src-tauri/src/lib.rs

runtime/VCPMobile/src/core/utils/astRenderer.ts
runtime/VCPMobile/src/core/utils/astExecutor.ts
runtime/VCPMobile/src/core/composables/useMessageStyleInjector.ts
runtime/VCPMobile/src/features/chat/MessageRenderer.vue
runtime/VCPMobile/src/features/chat/blocks/ToolBlock.vue
runtime/VCPMobile/src/features/rag/RagPayloadDetail.vue
runtime/VCPMobile/src/features/assistant/AssistantMessageCard.vue

runtime/VCPMobile/src-tauri/src/vcp_modules/updater/frontend_update_manager.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/updater/ota_assets.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/infra/lifecycle_manager.rs

runtime/VCPMobile/src-tauri/src/vcp_modules/infra/settings_manager.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/infra/file_manager.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/infra/high_speed_channel.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/infra/file_extractor.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/infra/vcp_client.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/infra/vcp_log_service.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/infra/vcp_info_service.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/persistence/db_manager.rs

runtime/VCPMobile/src-tauri/src/vcp_modules/sync/sync_service.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/sync/sync_executor/push_executor.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/sync/sync_executor/diff_handler.rs
runtime/VCPMobile/src-tauri/src/vcp_modules/sync/sync_executor/batch_diff_handler.rs

runtime/VCPMobile/src-tauri/src/distributed/tool_registry.rs
runtime/VCPMobile/src-tauri/src/distributed/client.rs
runtime/VCPMobile/src-tauri/src/distributed/tools/mod.rs

runtime/VCPMobile/src-tauri/plugins/vcp-mobile/android/src/main/AndroidManifest.xml
runtime/VCPMobile/src-tauri/plugins/vcp-mobile/android/src/main/java/com/vcp/mobile/VcpMobilePlugin.kt
runtime/VCPMobile/src-tauri/plugins/vcp-mobile/android/src/main/java/com/vcp/mobile/SensorStatusManager.kt
runtime/VCPMobile/src-tauri/plugins/vcp-mobile/android/src/main/java/com/vcp/mobile/service/SseProxyService.kt
runtime/VCPMobile/src-tauri/gen/android/app/src/main/AndroidManifest.xml
runtime/VCPMobile/src/components/layout/PermissionGate.vue

runtime/VCPMobile/.github/workflows/ci.yml
runtime/VCPMobile/.github/workflows/release.yml
runtime/VCPMobile/package.json
runtime/VCPMobile/LICENSE
```

外部规范与当前公开证据：

- Tauri capabilities: <https://v2.tauri.app/security/capabilities/>
- Tauri CSP: <https://v2.tauri.app/security/csp/>
- Android Auto Backup: <https://developer.android.com/identity/data/autobackup>
- Current main CI failure: <https://github.com/MRiecy/VCPMobile/actions/runs/28734368865>
- v1.1.3 release workflow: <https://github.com/MRiecy/VCPMobile/actions/runs/28711281724>
- Current sync issue #20: <https://github.com/MRiecy/VCPMobile/issues/20>

## 17. 最终决策记录

```yaml
project: VCPMobile
decision: KEEP_AND_HARDEN
directory: runtime/VCPMobile
role:
  - mobile interaction client
  - constrained edge capability node
  - human approval and notification surface
not_role:
  - AGENTS OS kernel
  - policy authority
  - canonical task ledger
  - memory owner
  - trusted arbitrary executor
current_gate: HOLD_FOR_HARDENING
blocking_findings:
  - renderer_to_privileged_ipc_chain
  - unsigned_and_unsafe_frontend_ota
  - plaintext_and_overexposed_secrets
  - unsafe_file_and_local_service_boundaries
  - sync_false_success_and_cancel_failure
  - distributed_config_fail_open
  - missing_device_effect_permits
  - non_green_current_main_ci
next_required_artifact: VCPMobile Hardening Taskbook v0.1
```

## 18. 收口判断

VCPMobile 值得保留，也值得投入加固。它已经拥有 AGENTS OS 移动端需要的大部分“手脚和感官”，
包括交互、通知、文件、位置、传感器、后台流式连接和设备副作用。

但这些能力当前聚集在同一信任域中：接收远端内容的 WebView、读取完整设置的前端、宽泛 IPC、
Android plugin、frontend OTA 和 root command 之间没有足够强的隔离。

下一阶段不能继续加新移动能力。应先完成：

```text
renderer isolation
capability minimization
OTA trust
secret separation
sync correctness
distributed permits
bounded local services
green release evidence
```

完成这些以后，VCPMobile 才能从“功能强大的 VCP 移动客户端”变成“AGENTS OS 可以信任的受限
移动节点”。
