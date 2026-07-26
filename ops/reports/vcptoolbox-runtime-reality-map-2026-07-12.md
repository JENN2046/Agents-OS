# VCPToolBox Runtime Reality Map and AGENTS OS Integration Plan

```yaml
document: VCPToolBox Runtime Reality Map and AGENTS OS Integration Plan
version: v0.1
date: 2026-07-12
status: FINDINGS_ONLY
scope: /home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox
method: source-first read-only audit with bounded local validation
runtime_activation: not_performed
provider_execution: not_performed
private_memory_read: not_performed
active_config_read: not_performed
```

## 1. 这份报告回答什么

这份报告不是复述 VCPToolBox 的 README，也不是按 AGENTS OS 的愿景替它安排一个理想位置。

它要回答四个现实问题：

1. 当前这份 VCPToolBox 到底是什么，真实代码已经做到什么。
2. 它现在怎样启动、怎样调用模型和工具、怎样管理插件、Agent、任务、记忆与分布式节点。
3. 哪些能力可以成为 AGENTS OS 的身体，哪些边界目前不能信任。
4. 下一阶段怎样接入、收口、验证和逐步启用，而不是再次增加一套未经验证的架构。

本轮只做了源码、仓库状态、依赖、测试、原生模块与静态安全路径核验。为了不跨越安全边界，本轮明确没有：

- 读取 `config.env`、`.env`、真实凭据、Token、Cookie 或 provider 配置。
- 读取 `state-private/`、真实私人记忆、真实任务内容、原始日志或 provider raw response。
- 启动 VCPToolBox 服务、管理后台、浏览器桥、邮件、Shell、PowerShell 或分布式节点。
- 调用真实模型、Embedding、Rerank、邮件、浏览器、外部 Codex CLI 或其他付费 provider。
- 修改 VCPToolBox 的源码、插件清单、隔离状态或 Git 状态。

因此，本文对“源码有什么能力”和“代码边界有什么问题”可以给出明确判断；对“Jenn 当前实际配置启用了什么”和“真实数据上运行是否正确”只标记为未知，不能伪装成已经验证。

## 2. 证据等级

本文使用五种证据等级，避免把文档、代码和运行事实混在一起：

| 等级 | 含义 | 可以得出什么结论 |
|---|---|---|
| `SOURCE_PROVEN` | 当前源码、manifest、依赖或 Git 状态直接证明 | 可以确认代码路径、默认行为、当前工作树事实 |
| `LOCAL_VALIDATED` | 在不启动服务、不读取敏感配置的条件下完成本地验证 | 可以确认语法、局部测试、依赖树或原生绑定可加载 |
| `CONFIG_DEPENDENT` | 行为取决于未读取的活动配置 | 只能说明能力和风险存在，不能说明当前已实际开启 |
| `RUNTIME_UNVERIFIED` | 必须启动服务、调用 provider 或使用真实数据才可确认 | 不得报告为可用、稳定或安全 |
| `DOC_CLAIM` | 只出现在 README、说明或宣传文本 | 只能作为设计意图，不能当作当前事实 |

后文没有特别标注时，“存在”表示源码存在，不表示生产可用。

## 3. 一句话结论

**VCPToolBox 不是纸面项目。它是一套真实、庞大、能力密集的本地 Agent 运行时，已经包含模型入口、文本工具协议、插件宿主、Agent 协作、浏览器、Shell、文件、邮件、分布式节点、热冷记忆、向量索引和管理界面。**

但同样必须直说：

**它目前是一个高权限的大型共同信任域，不是 AGENTS OS 已经可以无条件依赖的权限内核、全局任务总账、可靠执行状态机或安全沙箱。**

大白话说：

> VCPToolBox 确实可以成为 AGENTS OS 的身体和记忆器官，但现在不能再让这具身体同时扮演宪法、门卫、法院、总账和审计员。

AGENTS OS 下一阶段不该重写 VCPToolBox，也不该一次性恢复全部插件。正确路线是：

1. 先保住当前隔离现场。
2. 在 VCPToolBox 外面建立一个真正的 AGENTS OS 权限与调用边界。
3. 逐项核验能力，以最小权限重新启用。
4. 把记忆智能留给 VCPToolBox，把记忆访问许可和低披露证据交给治理桥。
5. 把全局任务总账、permit、lease、幂等和 crash recovery 放在 VCPToolBox 之外的治理与状态层。

## 4. 当前仓库现实快照

审查对象：

```text
/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox
branch: main
HEAD: 555b3b5
partial clone: blob:none
```

### 4.1 当前工作树不是普通干净 main

使用默认会折叠未跟踪目录的 `git status --short` 视图，当前工作树共有 137 个状态项：

| 类型 | 数量 | 说明 |
|---|---:|---|
| tracked plugin manifests deleted | 63 | 原 manifest 从工作树移除 |
| matching untracked `.block` manifests | 63 | 相应插件被本地阻断 |
| tracked binary modifications | 2 | 涉及 DailyNoteSearcher native binary 与 UserAuth `code.bin` |
| untracked paths in collapsed view | 72 | 包含上述 `.block` 和其他本地状态/构建目录 |

如果使用 `git status --porcelain=v1 -uall` 展开所有未跟踪文件，当前会得到 1,449 条状态，其中 1,384 条为未跟踪文件。本文没有读取这些未跟踪文件的内容；这个数字只说明当前 checkout 还包含大量缓存、构建结果或本地运行材料，137 是便于观察边界的折叠视图，不是全部文件数。

这里不能简单写成“仓库脏了”。更准确的说法是：

- 当前工作树承载了一次尚未固化的插件隔离现场。
- 这个现场很可能是有意收缩运行面，而不是随机损坏。
- 任何 `reset`、`clean`、覆盖式同步或重新 checkout 都可能恢复大量高权限插件或丢失用户现场。
- 当前隔离依赖未提交的文件改名，不是可靠的长期策略，也不能被新 clone 自动继承。

**结论：当前工作树必须先被当作受保护现场，不能做批量清理、还原或插件恢复。**

### 4.2 插件状态发生了根本变化

当前本地共识别到 85 个插件目录/manifest：

| 视图 | enabled | blocked | 解释 |
|---|---:|---:|---|
| 当前工作树 | 2 | 83 | 大部分插件已进入隔离状态 |
| `HEAD 555b3b5` 基线 | 65 | 20 | main 的提交基线默认暴露面大得多 |

当前仅启用：

- `ToolCallRecordQuery`
- `VCPTimeLine`

这不等于当前系统已经形成一个可工作的最小集：

- `ToolCallRecordQuery` 涉及工具调用记录，天然属于隐私敏感查询面。
- `VCPTimeLine` 依赖 RAG/ContextBridge 相关链路，而其依赖处于阻断状态。
- “manifest 未被阻断”只说明被发现，不说明依赖、配置、provider 和安全边界均已满足。

`HEAD` 中原本阻断的 20 个插件为：

```text
AgentDream
AnimeFinder
ArxivDailyPapers
ComfyUIGen
CrossRefDailyPapers
DailyHot
DailyNotePanelRouter
FileListGenerator
FileTreeGenerator
LinuxLogMonitor
LinuxLogMonitorServer
NCBIDatasets
PaperReader
RiverTestPlugin
SSHManagerService
SnowBridge
VCPForumOnline
VCPForumOnlinePatrol
WeatherInfoNow
ZImageGen2
```

### 4.3 代码规模说明它是实物，但规模不是成熟度

对 tracked source 的保守统计：

| 语言 | 文件数 | 行数 |
|---|---:|---:|
| JavaScript | 450 | 142,853 |
| MJS | 9 | 4,508 |
| Python | 61 | 17,681 |
| Rust | 93 | 30,872 |
| Vue | 116 | 64,886 |
| TypeScript | 152 | 27,299 |

这些数字证明它不是一个只有 README 和 demo 的壳。但代码量不能证明：

- 权限边界正确。
- 任务执行可靠。
- 插件互相隔离。
- 记忆数据合规。
- crash recovery 完整。
- README 中的性能和稳定性承诺成立。

### 4.4 版本信号不统一

- 根 package 是 `vcptoolbox@1.0.0`。
- README 使用 VCP 1.1 的叙述。
- 仓库 tag 和独立插件又有其他版本序列。

当前没有一个可直接作为 AGENTS OS 集成合同的统一版本信号。下一阶段必须用 commit SHA、协议版本和 capability catalog 锁定，不应只写“VCP 1.1”。

## 5. VCPToolBox 实际是什么

从源码看，VCPToolBox 同时承担了至少九类职责：

| 层 | 已存在的真实能力 | 当前判断 |
|---|---|---|
| API gateway | OpenAI 风格 chat、embedding、special model 转发 | 真实存在，认证顺序有关键问题 |
| Prompt runtime | system prompt 组装、Agent/persona、占位符和上下文注入 | 真实存在，权限和 prompt 内容混合 |
| Tool protocol | 解析 `<<<[TOOL_REQUEST]>>>`、并发执行、回灌结果 | 真实存在，不是结构化 capability protocol |
| Plugin host | static、preprocessor、sync、async、service、hybrid service | 真实存在，默认是共同信任域 |
| Agent runtime | AgentAssistant、委托、会话、归档 | 真实存在，状态主要在内存且完成由文本声明 |
| Task runtime | 文件任务、node-schedule、VCPTaskAssistant | 真实存在，不具备总账级语义 |
| Memory runtime | DailyNote、RAGDiary、TagMemo、LightMemo、TDB、Vexus | 真实而且很深，是最有战略价值的部分之一 |
| External I/O | 文件、Shell、PowerShell、浏览器、邮件、远程节点 | 真实存在，权限极高 |
| Operator UI | admin panel、Vue 管理界面、WebSocket | 真实存在，不能等同于安全控制面 |

它的正确产品分类不是“小工具箱”。更接近：

```text
monolithic local agent runtime
+ plugin and tool operating environment
+ memory intelligence substrate
+ external I/O host
+ operator console
+ distributed capability bridge
```

这也解释了为什么它对 AGENTS OS 很重要：很多 AGENTS OS 想要的能力，在这里已经有真实实现，不值得重写。

也解释了为什么不能直接全开：上述职责在同一个 Node 进程、同一套环境变量、同一个共享 Key 和同一套 prompt/tool 通道内高度耦合。

## 6. 启动与运行链

### 6.1 启动顺序

`server.js` 的主要启动链可以概括为：

```text
load config.env
  -> initialize tool call store
  -> initialize hot KnowledgeBaseManager
  -> optional TDBKnowledge
  -> initialize dynamic tool registry
  -> discover/load plugins and plugin routes
  -> initialize plugin services
  -> background Python prewarm
  -> initialize task scheduler
  -> initialize Agent / TVS / toolbox / SarPrompt
  -> initialize semantic router
  -> listen
  -> initialize WebSocket and FileFetcher after listen
```

现实含义：

- `server.js` 在 import 时就加载活动配置，因此本轮没有通过 `require(server.js)` 做探测。
- 部分静态插件行为和 Python prewarm 是 fire-and-forget，不能把“HTTP 已 listen”报告成“所有运行组件已 ready”。
- WebSocket 与 FileFetcher 在 listen 后才初始化，ready 语义还需要明确合同。
- 热记忆初始化可能扫描日记、切块并调用 embedding provider，启动本身可能包含数据外发。

### 6.2 关闭链比很多实验项目完整，但还不是可靠任务恢复

源码有 graceful shutdown：

- 停止接收新请求。
- 等待或中止部分活动工作。
- 关闭 scheduler、WebSocket、插件和存储。
- 为部分资源提供 drain/abort 路径。

这是正面工程事实。但它不等于：

- 外部副作用可以回滚。
- 所有 Axios/provider 请求都能取消。
- 任务能从 durable checkpoint 恢复。
- 插件 monkey patch 和监听器都被完全撤销。
- crash 后不会重复执行。

还存在 KnowledgeBaseManager 可能经 PluginManager 和 server 两条路径重复 shutdown 的迹象，需要真实生命周期测试。

## 7. API、认证与网络边界

### 7.1 网络默认面

源码中的主服务与 admin 服务使用 `app.listen(port)`，没有明确传入 host。Node 默认会监听全部可用接口，而日志文本中的 `localhost` 不能改变这一事实。

同时存在：

- `trust proxy = true`
- CORS `*`
- 最高 300 MB 的全局 body limit
- 主 API 的共享 Bearer `Key`
- admin 的 Basic auth/cookie

admin cookie 为 HttpOnly、SameSite Strict，在 HTTPS 时才使用 Secure；但 cookie 内容是 Basic credential 的 base64 表示，不应被视作独立短期会话凭据。

### 7.2 Critical: special model router 在 Bearer middleware 之前

`routes/specialModelRouter.js` 对 image chat/embedding 等请求做 provider 转发，并使用服务器侧配置的上游 API key。

但 `server.js` 当前先挂载该 router，再挂载通用 Bearer 认证；router 本身没有独立认证。

现实风险：

- 只要路由白名单/模型配置满足，未通过主 Bearer 的请求可能消耗服务器 provider 权限。
- 这不是“配置写错才危险”，而是认证顺序本身错误。

必须先修复和写负面测试，不能靠部署人员记住网络隔离。

### 7.3 Critical: plugin callback 无签名，先写文件后验证插件

`/plugin-callback/:pluginName/:taskId` 被排除在 Bearer 认证之外，也没有回调签名、nonce 或一次性 token。

当前逻辑在确认插件/任务是否合法之前，先把请求 JSON 写入 `VCPAsyncResults`。同时：

- path 参数没有严格字符白名单。
- 使用全局大 body limit。
- 没有证明写入是原子的。
- 没有证明回调与原始任务、插件实例和 actor 被绑定。

这形成伪造回调、磁盘消耗、路径构造和任务结果污染风险。路径穿越是否能通过具体 Express 解码方式触发仍需专门负面测试，但代码当前没有应有的防御。

### 7.4 High: schedule task 使用未验证 task ID 构造文件路径

`/v1/schedule_task` 受 Bearer 保护，但 `task_id` 被用于 `path.join`，没有看到严格的 ID schema、canonical path containment、原子创建或幂等冲突规则。

持有共享 Key 的任何调用者不应因此自动获得任意路径写入能力。

### 7.5 High: `trust proxy = true` 放大 IP 伪造问题

IP 黑名单、异常检测、FileFetcher 的来源映射等逻辑依赖请求 IP。直接暴露服务时，客户端可以通过 `X-Forwarded-For` 影响这些判断。

正确做法不是简单关闭所有 proxy 支持，而是：

- 默认 loopback bind。
- 明确可信反向代理 CIDR。
- 只在经过可信代理时接受 forwarded headers。
- 安全判断不要只依赖可伪造的 IP。

## 8. 工具调用协议现实

### 8.1 真正执行的是文本标记，不是原生 tool call 权限模型

VCPToolBox 的核心执行协议是模型文本中的：

```text
<<<[TOOL_REQUEST]>>>
...
<<<[END_TOOL_REQUEST]>>>
```

源码会解析这些文本块、查找插件、执行工具，再把结果作为带 `VCP_TOOL_PAYLOAD` 标记的 `role:user` 消息注回对话。

上游原生 `tool_calls` 主要被识别为“模型并非只输出 reasoning”，没有成为 VCPToolBox 的主要结构化执行入口。

这意味着：

- 工具请求与普通生成文本共享通道。
- prompt injection 和边界标记逃逸必须被当作执行安全问题。
- capability、actor、task、permit、idempotency 并没有被协议强制绑定。
- 工具结果作为用户消息回灌，会与真实用户输入、外部网页/邮件内容混在同一推理空间。

### 8.2 同一轮工具调用并发，但没有依赖和事务语义

普通工具请求会通过 `Promise.all` 并发执行。默认最大工具循环约为 5。

源码没有提供通用的：

- 工具依赖图。
- 幂等 key。
- 外部写副作用去重。
- 分布式事务。
- compensating action。
- “前一个工具成功后才能执行后一个”的强约束。

因此它适合能力编排，不适合直接承担 AGENTS OS 的可靠工作流状态机。

### 8.3 结果保护默认不能当作安全边界

工具结果/隐私 guard 默认关闭且存在 fail-open 路径。工具调用记录存储默认也可能关闭；启用后会把参数和结果写入 SQLite。

AGENTS OS 不能假设“系统会自动脱敏”。应在 VCPToolBox 外层调用网关实施：

- 请求字段最小化。
- 结果 schema。
- secret/private-memory redaction。
- 最大体积。
- 数据分类。
- 低披露审计事件。

### 8.4 流式错误语义不稳定

部分上游错误可以被包装成 HTTP 200 的 SSE 文本内容。对于调用者来说，“HTTP 成功”不等于模型或工具执行成功。

AGENTS OS adapter 必须解析终止事件和结构化 error，不能只看 status code。

## 9. 插件系统现实

### 9.1 插件类型很完整

已实现的插件类型包括：

- `static`
- `messagePreprocessor`
- `synchronous`
- `asynchronous`
- `service`
- `hybridservice`

插件可以：

- 作为 child process 通过 stdio 运行。
- 作为 direct module 在主进程运行。
- 注册 HTTP route。
- 连接 WebSocket/distributed server。
- 注入 prompt placeholder。
- 修改消息和上下文。
- 调用其他插件或被其他插件桥接。

这套宿主能力本身是 VCPToolBox 最有价值的资产之一。

### 9.2 但插件不是隔离单元

child process 使用 `shell:true` 启动并继承根 `process.env`。direct plugin 与主服务器处于同一进程和同一环境。

因此当前安全模型实质是：

```text
enabled plugin == trusted code inside one secret-bearing runtime domain
```

manifest 不是 sandbox。`requiresAdmin` 也不是通用 OS 权限边界。

任何恢复启用的插件都可能接触：

- provider/API 环境变量。
- VCP shared Key。
- 文件/图片服务 key。
- 进程、网络和文件系统。
- 主进程对象或其他插件状态。

### 9.3 manifest default 没有被统一落实

`PluginManager` 的配置读取主要从插件专用/global env 取值；没有看到通用逻辑自动应用 manifest 中声明的 `default`。

这会产生危险差异：

- 开发者以为 manifest `default: false` 会禁用。
- 运行代码收到的却可能是 `undefined`。
- 如果插件用 `value === false` 判断，`undefined` 会进入启用分支。

`VCPToolBridge` 就有这种 fail-open 迹象。

必须把“manifest schema、默认值解析、最终 effective config”做成集中合同和测试。

### 9.4 `requiresAdmin` 不是中央强制授权

当前实现更接近：

- stdio 插件得到 `DECRYPTED_AUTH_CODE`。
- direct 插件得到 `context.decryptedAuthCode`。
- 是否比较、比较哪个参数、什么时候要求，由插件自己实现。

这不是中央 capability permit。它无法证明：

- Jenn 当前明确批准了这次操作。
- 批准绑定了具体 task、工具、参数和期限。
- 一个插件不能忘记检查。
- 模型不能自己拿到 code 后自批。

### 9.5 plugin watcher 不是当前可靠热更新合同

源码中存在 manifest watcher 能力，但主启动链没有看到稳定调用。实际管理更依赖 admin reload。

因此“改 manifest 后会自动可靠生效”不能作为运维假设。

## 10. 当前授权码模型为何不能承接 P3

`Plugin/UserAuth/auth.js` 生成六位数字，并把一种基于括号计数的 base64 混淆结果写入 `code.bin`。系统 prompt 可以通过 `{{USER_AUTH_CODE}}` 获得明文授权码。

`modules/captchaDecoder.js` 做的是 base64 解码和符号计数，不是密码学保护。

核心问题不是六码太短，而是信任方向错误：

> 如果模型能从 system prompt 直接获得授权码，模型就可能在工具参数里自行提交授权码。此时它证明的是“模型看见了一个字符串”，不是“Jenn 对这次具体操作做了当前授权”。

因此：

- 现有 code 只能视作旧插件兼容机制。
- `doubleConfirm: true` 只是模型可填写的布尔值，不是人类确认。
- AGENTS OS 的 Red/P3 permit 必须在模型上下文之外产生。
- permit 必须绑定 actor、task、capability、参数摘要、过期时间、使用次数和审计事件。
- P3b 类行为仍然不能通过 permit 放开。

## 11. 高权限能力逐项判断

### 11.1 FileOperator: 默认边界接近主机文件系统

`ServerFileOperator` 在 `ALLOWED_DIRECTORIES` 为空时允许全部操作。绝对路径读取和 FileInfo 还有显式的 allow 行为。

现有路径判断主要使用字符串前缀，未形成可靠的：

- `realpath` canonicalization。
- 路径分隔符边界。
- symlink escape 防御。
- 按 operation 分开的 read/write/delete/move ACL。
- secret/private-memory denylist。

它在 `HEAD` 基线中启用，当前被阻断。当前阻断是正确的。

**重新启用前的最低条件：默认拒绝、按 operation allowlist、realpath containment、symlink 负面测试、敏感目录硬拒绝、外部写 permit。**

### 11.2 PowerShell: `requiresAdmin` 不等于每次执行都确认

`ServerPowerShellExecutor` 使用可配置的 forbidden/auth-required 字符串列表。只有命令匹配 `AUTH_REQUIRED_COMMANDS` 时才会要求 code。

如果列表为空或不完整，任意 PowerShell 命令可能不经过 code。它同时继承根环境变量并返回完整输出。

必须把它视作 unrestricted host executor，不是普通工具。

### 11.3 LinuxShell: 默认 backend 源码值是 `none`

LinuxShell 提供 Docker、Firejail、Bubblewrap 等可选 backend，这是有价值的实现。但源码默认 `SANDBOX_BACKEND=none`，此时本质是：

```text
/bin/bash -c + ulimit
```

所谓 sanitized environment 只删除少数 IPC 变量，保留大量 root env。`env`/`printenv` 被视作读取类命令，`cat` 的允许范围又覆盖 `/home`，因此默认策略可能直接暴露 active config 和凭据。

本轮没有读取实际 backend 配置，所以不能说 Jenn 当前运行时一定是 `none`；但源码默认和 fail-open 风险已经足以阻止直接启用。

### 11.4 AICodeWorker: 模式名称不是操作系统权限

AICodeWorker 提供 analyze、patch、write 等模式，但这些主要体现在 prompt 文本。实际 CLI 路径会使用 `--dangerously-skip-permissions`。

还观察到：

- cwd/projectPath 做 allowed-root 检查，但任务中引用的路径和 attachment 不形成同等边界。
- child process 仍继承大量环境变量。
- job args 文件保存完整任务内容；redaction 主要作用在返回输出/日志。
- `killResidualOpencode()` 会按进程名终止整个系统的 opencode，而不是只管理自身子进程。
- query/cancel 的 `jobId` 未看到严格 schema 和 canonical containment。

它可以作为 executor adapter 的底层能力，但不能直接成为受控执行宿主。

### 11.5 ChromeBridge: 浏览器 Agent 身份可由客户端自报

浏览器扩展拥有 `<all_urls>`、scripting、debugger 等高权限，可在 main world 执行 JavaScript、读取 CDP response body、处理 Cookie 和站点存储。

managed browser 路径有独立 token 和 profile，这是正确方向。但当前客户端可以自报 `clientKind: agent` 获得更高权限；共享 VCP Key 的持有者可能模拟 Agent。

此外 managed runtime payload 包含 VCP Key 和 token，并落入本地 token/config/profile 文件。扩展配置还存在 web-accessible 暴露设计，必须做真实浏览器边界审计。

重新启用前必须改成服务器签发的不可伪造 client identity，而不是客户端声明。

### 11.6 ImageFileServer: URL key、IP 锁定和文件边界都需重做

Image/File key 被放入 URL，system prompt 还可以替换 `{{Image_Key}}`。这会让 key 进入：

- 模型上下文。
- conversation/history。
- 日志与错误信息。
- referrer、proxy 和缓存。

同时，监控逻辑先于认证并依赖全局 `trust proxy`，攻击者可尝试用伪造 IP 触发共享 SecurityManager 锁定。静态文件服务没有证明常量 `MAX_FILE_SIZE` 被执行，也没有完整 realpath/symlink containment。

### 11.7 VCPClawMail: 邮件同时是外部写和不可信输入

该插件可以发送、回复、移动/删除邮件，属于真实外部副作用。源码没有中央人类 permit、收件人 allowlist 或账号 allowlist。

更危险的是输入面：

- 邮件 sender、subject、preview 会被自动注入 system prompt 和缓存。
- 邮件正文、附件会进入 AgentAssistant。
- 依赖 delimiter 和“不要听恶意邮件指令”的提示不能形成 prompt injection 边界。
- `file://` attachment 能形成主机文件外发路径。
- URL attachment/body fetch 可能形成 SSRF 和内网访问。
- incoming attachment 在解析 PDF/doc/xlsx 前缺少统一体积边界。
- 处理标记早于完整 dispatch，临时失败可能永久跳过。

这个插件必须同时按“高风险外部写”和“高风险不可信输入”治理。

### 11.8 VCPToolBridge: 远端能力桥当前是黑名单思路

VCPToolBridge 通过 monkey patch 分布式 WebSocket handler，把本地工具暴露给远端。默认更接近 blacklist export，而不是 capability allowlist。

结合 manifest default 未统一应用，`Bridge_Enabled` 缺失时存在 fail-open 风险。共享 VCP Key 只是传输认证，不能替代逐工具 permit。

shutdown 也没有完全证明 patch、listener 和 pending map 都被恢复/取消。

在 AGENTS OS 中，桥必须由明确 allowlist、独立 token、短期 session、调用 envelope 和结果审计驱动。

## 12. 分布式与 WebSocket 边界

VCPToolBox 的 WebSocket 可以承载：

- VCPLog
- VCPInfo
- DistributedServer
- Chrome
- AdminPanel

这些角色共用一个放在 URL 中的 VCP Key。现实问题：

- URL credential 容易进入 proxy/access log、历史和诊断信息。
- 角色之间没有独立的最小权限 credential。
- 认证客户端可能参与 approval response 等敏感路径。
- distributed registrant 可以提供 tool manifests/placeholders，扩大本地 prompt 和能力面。
- pending distributed call 主要在内存，缺少持久化 retry、idempotency、cancel recovery。

FileFetcher 还支持 `file://`：

- 本地文件存在时直接提供给插件，没有中央文件 allowlist。
- 本地缺失时，依据请求 IP 到 distributed server 的映射，请求远端取文件。
- 在 `trust proxy=true` 下，IP 关联也需要防伪造验证。
- 缓存没有看到完整的容量、TTL 和清理合同。

分布式功能是真实资产，但当前更适合受信实验网络，不适合作为默认 AGENTS OS capability fabric。

## 13. Agent 与任务状态现实

### 13.1 taskScheduler 是文件调度器，不是 canonical ledger

当前 scheduler 组合：

- filesystem task files。
- `node-schedule`。
- in-memory jobs。

它能在启动时发现过期 pending task 并立即执行，也能在完成后记录结果。但当前语义存在：

- 完整 args/result/error stack 可能未脱敏持久化。
- 无 durable execution state machine。
- 无通用 lease/lease expiry。
- 无 idempotency key。
- crash 发生在外部副作用之后、状态写入之前时可能重复执行。
- task 文件最终删除，历史与当前事实边界不稳定。
- shutdown 取消计划任务，不等于取消活动外部调用。
- init 中 mkdir/scan 异步链与 watcher 之间有启动竞态迹象。

它可以保留为 VCP 内部轻量 scheduler，但不能拥有 AGENTS OS 全局任务生命周期。

### 13.2 VCPTaskAssistant 有工作流能力，但没有总账可靠性

它已经具备计划任务、Agent 任务、状态记录、超时和重试相关逻辑。但源码现实包括：

- `task-center-data.json` 是活动状态，本轮未读取。
- 保存非原子，错误被吞掉，写入没有统一串行化。
- initialize 启动 promise 但接口本身不是可靠 awaited readiness。
- manual trigger 没有始终服从 enabled flags。
- 10 分钟 stale-running 重置可能与仍在运行的 sequential Agent 重叠。
- `Promise.race` 超时不会真正取消 AgentAssistant。
- 无 durable lease、idempotency 和完整 catch-up 语义。

结论同样明确：可作为 VCP 内部工作流和 UI 能力，不能作为 AGENTS OS 总账。

### 13.3 AgentAssistant 是会话/委托运行器，不是可靠 executor

AgentAssistant 会嵌套调用 `/v1/chat`，管理内存会话、委托状态和归档。

当前边界：

- session ID 可由调用者提供，未形成 owner/actor 绑定。
- 临时工具列表主要是 prompt 描述，不是 capability ACL。
- 委托完成依赖模型文本中的 `[[TaskComplete]]` / `[[TaskFailed]]`。
- 没有对产物、diff、测试或副作用做结构化完成验证。
- cancel 是 cooperative，不保证中止进行中的 Axios/provider 调用。
- 活动状态主要在内存，归档包含完整任务和报告。
- 某些失败路径可能重复发 callback。
- 知道 task ID 的调用者可能查询归档，缺少所有权边界。

它适合做 Agent conversation/delegation host，不适合直接宣告“任务已完成”。

## 14. 记忆系统深描

VCPToolBox 的记忆能力不是装饰。它是这套代码里最深、最有独立价值、也最需要谨慎接入的部分。

### 14.1 实际记忆层次

```text
DailyNote .md/.txt source
  -> chunking / tags / metadata
  -> SQLite full chunks and vectors
  -> Vexus native vector index
  -> hot retrieval / TagMemo / RAGDiary / LightMemo
  -> optional TDB cold store
  -> timeline / dream / persona / folding derived products
```

合理的事实分类应是：

| 数据 | 推荐事实地位 |
|---|---|
| 原始 DailyNote/显式记忆内容 | source fact，需明确 owner 和写入许可 |
| SQLite chunks/vectors/tags | derived state，可重建但敏感度不降低 |
| Vexus index | derived index，可重建 |
| timeline/summary/persona axes | model-derived interpretation，不是原始事实 |
| tool/Agent archive | execution evidence，需最小披露和保留策略 |

### 14.2 Hot KnowledgeBaseManager 启动就可能产生外发

Hot KnowledgeBaseManager：

- 强依赖 `rust-vexus-lite`。
- 读取 DailyNote `.md/.txt`。
- 将 chunks、vectors、tags 以明文形式存入 SQLite。
- 使用 Vexus 作为派生索引。
- 默认可能进行初始 full scan。
- watcher 可在文件变化后重新切块、打标签并调用 embedding provider。

embedding 请求会发送完整文本。默认并发约 5，没有看到一致的 timeout/abort；provider 错误日志还可能包含 raw response 片段。

现实含义：启动 VCPToolBox 不只是“开一个本地端口”，还可能自动扫描和外发记忆内容。AGENTS OS 必须把 memory egress 当作独立 permit，不允许用“服务启动许可”顺带覆盖。

### 14.3 TDB 冷存储队列反而更接近可靠工程

可选 TDBKnowledge 默认关闭。其 SQLite ingest queue 具备 retry 和 stale recovery，持久性比 hot embedding queue 和通用 task scheduler 更强。

但它仍会在 full scan/ingest 中把 chunks 送往 embedding provider。可靠队列不等于隐私许可。

### 14.4 RAGDiary 没有用户级记忆授权

RAGDiary 会：

- 根据特定用户字符串触发日记行为。
- 对 user/AI 文本做 embedding。
- 读取选中日记片段。
- 在 AIMemo/rerank 路径把内容送往外部模型。

目前没有清晰的 per-user、per-agent、per-notebook 授权层。任何持有 API Key 的调用者不应自动拥有全部记忆检索权。

### 14.5 TagMemo 是真实派生引擎，但不是同步事实源

TagMemo 的刷新存在延迟和内存队列。它适合做检索增强和派生结构，不适合被 Dashboard 或治理层当作立即一致的 source of truth。

### 14.6 OneRing 更接近实验层

OneRing 自身 README 和代码都显示实验/骨架属性：

- per-agent SQLite 保存原始 user/assistant 对话。
- agent name 构造路径时缺少充分 containment。
- summary 会把原始 conversation 发给模型。
- 生成事实缺少 provenance 和反证机制。

不能因为位于 VCP memory 体系中就默认提升为正式长期记忆。

### 14.7 VCPTimeLine 有“派生内容回写源记忆”的闭环风险

VCPTimeLine 会读取记忆、调用模型生成月度内容，再写入 DailyNote 源目录。新生成内容随后又可能被重新索引和检索。

这会形成：

```text
raw memory
  -> model interpretation
  -> write back as note
  -> reindex as if source content
  -> influence future interpretation
```

如果没有 provenance、derived 标签、回滚和 source/interpretation 隔离，模型幻觉会自我强化。

当前它虽然是仅有的两个未阻断插件之一，但依赖链并不完整，且不应该在真实记忆上直接验证。

### 14.8 DailyNote 的路由不是授权

maid/folder routing 解决“写到哪里”，不解决“谁可以读写”。当前还存在：

- fallback search/update 可能越过 owner-disallowed directory 的意图。
- create collision race。
- update 非原子且无通用 backup。
- `file://` 内容可被复制进 web-served 目录，形成主机文件外发路径。
- TagMaster 可能把完整 note 发给外部 provider。

DailyNoteManager 有正面实现：部分 path containment、原子新文件和进程内队列。但 organize 等跨步骤操作仍缺少事务/回滚。

### 14.9 AgentDream 目前是 proposal 生成，不是审批工作流

AgentDream 有 proposal 写入，但 approve/reject 尚未形成完整实现。它还支持 file URL，缺少充分 containment 时可把任意主机内容复制进 dream logs。

### 14.10 ContextFoldingV2 会外发历史对话

它会把较旧 assistant output 发送给 summary provider，并对 conversation 做 embedding。pending queue 主要在内存，SQLite pending entry 没有看到完整 startup recovery；active Axios 也不一定在 shutdown 时取消。

摘要只做结构校验，不能保证事实正确。

### 14.11 OpenHerPersona 当前实现与测试已经分叉

当前 OpenHerPersona：

- 主要存 hashes 和派生 axis scores，而非原始 message。
- 会把最近最多约 4k 文本送去 embedding。
- 队列在内存中，拥塞时丢弃最旧项，shutdown 不保证 drain。
- caller attribution 可被伪造。
- reset/save_config 可通过工具调用触发。
- legacy state 默认 drop 行为具有破坏性。

现有测试针对已经移除的旧实现，不能作为当前证据。涉及心理/性别等启发式轴也只能视作实验 telemetry，不能写成用户事实。

### 14.12 LightMemo 有跨域检索扩大风险

LightMemo 使用 folder `LIKE` 等宽泛匹配，`search_all` 可绕过局部 scope，缺少独立 auth。rerank 会把命中记忆送往外部 provider。

### 14.13 记忆系统最终判断

VCP native memory 可以继续拥有：

- 记忆智能。
- DailyNote 等原生内容生命周期。
- chunk、tag、vector、timeline 等派生引擎。
- native vector index 和 retrieval runtime。

但它不应独自拥有：

- 谁可以读哪段记忆。
- 哪些内容允许外发给哪个 provider。
- 哪个 Agent/任务获得了什么范围的记忆。
- 派生结论是否可晋升为事实。
- 低披露审计和跨系统 provenance。

这些应由 `codex-memory`/AGENTS OS memory governance bridge 约束。

## 15. 依赖、原生模块、测试与 CI 现实

### 15.1 依赖可以解析，但缺少工程门槛

- 根 package 声明 53 个 dependencies。
- 没有 devDependencies。
- 没有 Node engine 约束。
- `npm ls --depth=0` 通过，但存在一个 extraneous `@emnapi/runtime@1.11.2`。
- 当前环境 Node `v22.23.1`、Linux x64、N-API 10。

依赖树可解析只说明当前 checkout 的 `node_modules` 基本闭合，不说明 clean install、跨平台和供应链风险已验证。

### 15.2 `rust-vexus-lite` 真实可加载

本轮在不读取真实记忆的条件下加载了 Linux x64 GNU native binding：

- `.node` 文件是有效 ELF。
- 常规动态库依赖可解析。
- 成功导出 `VexusIndex` 和 `VexusWatcher`。

这是 `LOCAL_VALIDATED`，只证明 binding 在当前机器可加载，不证明索引正确性、并发一致性、性能或真实记忆兼容性。

### 15.3 根测试命令实际上不存在

`npm test` 固定输出 `Error: no test specified` 并失败。

真正发现的测试/fixture 很少：

- dynamic tool registry test。
- 已过时的 OpenHerPersona test。
- sample Jest file。
- Vexus smoke script。
- 少量 JSON fixtures。

本轮验证结果：

| 验证 | 结果 |
|---|---|
| `node --test tests/dynamicToolRegistry.test.js` | PASS, 24/24 |
| 17 个核心 JS 文件 `node --check` | PASS |
| `npm ls --depth=0` | PASS with one extraneous package |
| native Vexus binding load | PASS |
| `npm test` | FAIL, package script is placeholder |
| OpenHerPersona old test | NOT RUN, test会触碰活动派生状态且与当前实现分叉 |

### 15.4 CI 只安装依赖，不验证系统

`.github/workflows/ci.yml` 当前主要执行 `npm ci`，并构建/发布 Docker image。没有看到 CI 强制执行：

- unit/integration tests。
- lint/typecheck。
- auth negative tests。
- path traversal tests。
- plugin isolation tests。
- memory egress tests。
- crash recovery tests。

tag `v*` 还会触发 Docker Hub publish。任何对 workflow/tag/release 的修改都属于独立高风险范围，本报告不执行。

VCPToolBox 自身 `AGENTS.md` 也写明缺少正式测试并依赖生产验证。这是当前成熟度事实，不是可以继续生产试错的理由。

## 16. README 愿景与源码现实对照

| README/文档方向 | 源码现实 | 判断 |
|---|---|---|
| 成熟稳定、7x24 运行 | 有 graceful shutdown 和大量真实实现，但根测试为空、CI 不跑测试 | `DOC_CLAIM`, 未被工程门槛证明 |
| 300+ 官方插件 | 当前 checkout 识别到 85 个插件目录/manifest | 生态口径可能更大，本地事实不支持 300+ |
| O(1)、毫秒级记忆 | 有 Vexus native index 和派生索引 | 算法/性能指标未 benchmark |
| 全插件类型分布式 | 有 distributed server、manifest 注册、bridge | 安全、恢复、幂等和全部插件兼容未端到端验证 |
| 统一事实时间线 | 有 VCPTimeLine 与 DailyNote 回写 | 没有 canonical event ledger；派生内容会混入 source |
| 原子同步与恢复 | 个别子系统有原子写/队列恢复 | 不是全系统性质，scheduler/Agent/bridge 多处不满足 |
| 智能体自治 | Agent、task、tool loop 均真实存在 | 完成状态主要信任模型文本，缺少独立验证与 permit |

正确态度不是否认 README，而是把它降级为产品愿景。工程决策只接受源码、测试和可重复运行证据。

## 17. 风险优先级

### P0: 接入前必须处理

| ID | 问题 | 直接影响 |
|---|---|---|
| VCP-P0-01 | special model router 位于主 Bearer auth 之前 | 未认证 provider 消耗/数据外发 |
| VCP-P0-02 | plugin callback 无签名且先写文件 | 伪造结果、磁盘/路径风险、任务污染 |
| VCP-P0-03 | shared secret-bearing process/env，无插件隔离 | 任一启用插件可扩大为主机/凭据权限 |
| VCP-P0-04 | UserAuth code 可进入模型 prompt | 不能证明 Jenn 当前授权，P3 失效 |
| VCP-P0-05 | FileOperator/Shell/PowerShell/AICodeWorker 默认边界不足 | 主机任意读写执行和 secret 外泄 |
| VCP-P0-06 | memory startup/检索可能自动外发原始文本 | 私人记忆越界 |
| VCP-P0-07 | 当前插件隔离只存在于未提交工作树 | reset/clone 可意外恢复高权限面 |

### P1: 首批受控运行前必须处理

| ID | 问题 | 直接影响 |
|---|---|---|
| VCP-P1-01 | all-interface bind、CORS `*`、`trust proxy=true` | 网络暴露和身份/IP 伪造 |
| VCP-P1-02 | URL 中传递 WebSocket/Image/File key | credential 泄漏到日志/历史/上下文 |
| VCP-P1-03 | schedule task ID/path 和 callback ID 缺少 schema | 路径与状态污染 |
| VCP-P1-04 | manifest default 不统一，部分插件 fail-open | 配置意图与运行结果不一致 |
| VCP-P1-05 | tool text protocol 无 capability/actor/permit 绑定 | prompt injection 进入执行链 |
| VCP-P1-06 | browser agent 身份由客户端声明 | 共享 Key 持有者提权 |
| VCP-P1-07 | mail/file URL fetch 缺少强 allowlist | SSRF、文件外发、恶意邮件驱动外部写 |
| VCP-P1-08 | scheduler/Agent 无 durable lease/idempotency | crash 后重复副作用 |

### P2: 扩大使用前必须处理

| ID | 问题 | 直接影响 |
|---|---|---|
| VCP-P2-01 | root test 空、CI 只 `npm ci` | 回归无法被阻断 |
| VCP-P2-02 | readiness 与 listen 混淆 | 误报可用、启动竞态 |
| VCP-P2-03 | distributed pending/cancel/retry 在内存 | 节点断连后状态不可靠 |
| VCP-P2-04 | derived memory 可回写 source 且缺 provenance | 幻觉自我强化 |
| VCP-P2-05 | 日志/SQLite/任务归档可能存 raw args/results | 长期隐私与 secret 残留 |
| VCP-P2-06 | 版本、协议和 capability 无统一锁定 | 集成漂移 |

## 18. 成熟度判断

评分只用于判断下一步，不代表产品价值高低。

| 维度 | 现实等级 | 说明 |
|---|---|---|
| 功能深度 | 高 | 真实实现多，尤其插件和记忆系统 |
| 架构清晰度 | 中 | 子系统可辨认，但职责耦合在单体运行时 |
| 插件生态 | 中高 | 本地 85 个插件，能力广，合同不统一 |
| 记忆智能 | 高潜力 | hot/cold/native/RAG/tag/timeline 齐全 |
| 权限模型 | 低 | shared Key、prompt code、plugin-local checks |
| 进程隔离 | 低 | direct same-process，child inherit env，默认无 sandbox |
| 任务可靠性 | 低中 | 有 scheduler/queue，但缺 lease/idempotency/canonical ledger |
| 可测试性 | 低 | 根测试为空、CI 不执行测试、部分测试已分叉 |
| 可观测性 | 中 | 日志、tool record、admin 存在，但隐私和结构化事件不足 |
| crash recovery | 低中 | 个别 TDB 子系统较好，全局不成立 |
| AGENTS OS 直接接入 readiness | 不通过 | 必须先有外部网关、隔离、permit 与测试 |

## 19. AGENTS OS 中的正确定位

### 19.1 推荐职责

```text
AGENTS OS
  global goals, governance and shared operating model

codex-router candidate
  policy / protocol / decision / permit / routing / lease / recovery

Codex host or ColaMeta executor
  actual bounded execution process and execution session

VCPToolBox
  runtime body / plugin host / memory intelligence / external capability host

codex-memory
  governed memory access / disclosure minimization / evidence bridge

Workbench
  operator facade / workflow shell / compatibility adapter

Dashboard
  derived read-only projection
```

这不是把 VCPToolBox降级。相反，这是让它保留最难重写、最有价值的能力，同时卸掉它目前没有可靠实现的治理责任。

### 19.2 每类事实的推荐单一权威

| 事实类别 | 推荐权威写入者 | VCPToolBox 的位置 |
|---|---|---|
| AGENTS OS 全局 Task ID 和生命周期 | 经过 benchmark 决定的 canonical task ledger | 读取任务 envelope，回传投影事件 |
| policy、permit、route、lease、recovery | `codex-router` 候选 | 执行已授权 capability，不自批 |
| 实际进程/session 状态 | Codex host、ColaMeta executor 或 VCP host | VCP拥有其自身进程事实 |
| VCP plugin lifecycle/effective config | VCPToolBox | 权威，但需向外发布低披露状态 |
| 原生记忆内容和生命周期 | VCP native memory | 权威内容层 |
| chunks/vectors/index | VCP native memory | 可重建派生状态，不是 source fact |
| 记忆访问许可和 disclosure evidence | `codex-memory`/AGENTS memory governance | VCP只执行带范围的读写请求 |
| ColaMeta plan version | ColaMeta | 不由 VCP 改写 |
| artifact 与 validation result | 执行宿主产生，canonical ledger 引用 | VCP可产生 artifact，不单方面宣告全局完成 |
| Dashboard/Workbench 状态 | 只读 projection | 不回写 source fact |

### 19.3 明确不能让 VCPToolBox 拥有的四件事

1. **不能拥有 Jenn 的 P3 授权。** 模型 prompt 中的六码不是人类 permit。
2. **不能拥有全局任务总账。** 当前 scheduler 和 Agent state 不具备所需可靠性。
3. **不能让插件 manifest 等于权限。** enable 只代表代码加载，不代表能力被批准。
4. **不能把派生记忆写成原始事实。** timeline、summary、persona 必须带 provenance。

## 20. 下一阶段完整计划

计划按“通过门槛再进入下一阶段”推进，不按乐观日期强行推进。任何阶段都不以文档数量作为完成标准。

### Phase 0: 保护现场并冻结扩张

**目标：确保我们不会在理解和治理之前意外恢复高权限面。**

动作：

1. 保留当前 83 个 blocked 插件状态，不 bulk enable。
2. 对 63 个 manifest 删除和 `.block` 对应关系生成只读 inventory。
3. 固化当前 branch、HEAD、文件状态和 hash 清单，不复制真实配置/状态内容。
4. 明确 2 个当前 enabled 插件不代表 ready；在测试 profile 之前不启动真实 memory/provider 链。
5. 为 VCPToolBox 建立 `current checkout` 与 `HEAD baseline` 两个视图，Dashboard 不得混淆。
6. 暂停新增 plugin family、auth code 变体、parallel scheduler 和新 memory schema。

交付物：

```text
VCP Plugin Isolation Inventory v0.1
VCP Capability and Risk Catalog v0.1
VCP Current-vs-HEAD Baseline Snapshot v0.1
```

通过门槛：

- 每个插件有稳定 ID、manifest 状态、Git 状态、side effect 分类和依赖。
- 没有读取或记录 active secrets/private memory。
- 任意 clone/reset 不会被误认为保留了当前隔离策略。

### Phase 1: 先封住网络和认证漏洞

**目标：即使某个路由或插件写错，也不能从默认网络面直接扩大。**

动作：

1. 主服务、admin、image/file、WS 默认只 bind loopback。
2. 把 special model router 移到统一 auth 后，或为其增加等价独立 auth。
3. callback 改为短期签名 token，绑定 plugin、task、attempt、body hash 和 expiry。
4. callback 在验证通过后才原子写入；使用固定 schema 和小 body limit。
5. `task_id`、`pluginName`、`jobId` 统一采用严格 ID grammar，禁止路径字符。
6. 对所有 path 做 `realpath`/canonical containment 和 symlink negative test。
7. `trust proxy` 改成可信 proxy CIDR，不再使用全局 boolean true。
8. CORS 改为明确 origin allowlist。
9. WebSocket 不再把 shared key 放在 URL；使用 header/subprotocol 或短期握手票据。
10. admin cookie 改为独立随机 session，不保存可复用 Basic credential。

必须新增的负面测试：

- 未认证 special route 返回 401/403，且 provider adapter 未被调用。
- 伪造/过期/replay callback 被拒绝且不落盘。
- encoded slash、`..`、symlink 和 Unicode path confusion 被拒绝。
- spoofed `X-Forwarded-For` 不改变安全主体。
- 跨 origin admin/API 调用被拒绝。

通过门槛：

- loopback profile 下端口不对 LAN 暴露。
- 所有 provider-consuming route 都由同一授权模型覆盖。
- auth negative suite 在 CI 中强制运行。

### Phase 2: 建立 AGENTS OS VCP Gateway

**目标：把 VCPToolBox 从“拿到共享 Key 就能用很多能力”改成“每次只执行被授予的那一个能力”。**

先做外部 adapter，不先大改 VCP 核心。请求 envelope 至少包含：

```yaml
protocol_version: agents-os-vcp/0.1
request_id: immutable
task_id: canonical
attempt: integer
actor_id: authenticated
session_id: bound
capability_id: exact
operation: exact
arguments: schema_validated
arguments_digest: sha256
idempotency_key: stable
permit_id: optional_for_green_required_for_red
permit_expiry: timestamp
memory_scope: explicit
network_scope: explicit
workspace_scope: explicit
result_policy: schema_and_redaction
```

网关职责：

1. 根据 capability catalog 判定 Green/Yellow/Red/P3b。
2. 校验 actor、task、session 和 permit 绑定。
3. 对参数做 schema、路径、host、recipient 和体积限制。
4. 为插件生成最小环境变量，不继承根 env。
5. 生成短期、单次、不可被模型读取的 execution token。
6. 强制 timeout、cancel、max output 和 redaction。
7. 发出结构化 start/progress/result/error/cancel event。
8. 以 `idempotency_key` 阻止重复外部副作用。
9. 不把 raw secret、raw private memory 或 provider response 写入 event ledger。

通过门槛：

- VCPToolBox 无法自行签发 Red permit。
- 插件只能看到该次调用需要的环境变量。
- 重放同一外部写请求不会重复产生副作用。
- P3b 内容在 adapter 和 VCP 两侧都硬拒绝。

### Phase 3: 逐个收口高权限插件

**目标：不按插件名信任，只按 capability 重新授权。**

优先顺序：

1. 只读 status/metadata，不读取 env、raw config、logs、memory。
2. disposable workspace 内的文件只读。
3. disposable workspace 内的原子文件写入。
4. synthetic memory corpus 检索。
5. 受限 browser observation。
6. sandboxed code execution。
7. 真实外部写，最后处理且始终需要精确 permit。

插件最低改造：

| 插件/能力 | 必须完成 |
|---|---|
| FileOperator | default deny、operation ACL、realpath、symlink test、sensitive hard deny |
| LinuxShell | 默认真实 sandbox、空白 env allowlist、无 network、只挂载任务 workspace |
| PowerShell | Windows job/container 边界、每次 capability permit、输出脱敏 |
| AICodeWorker | mode 变成 OS enforcement、去除 unrestricted skip、子进程 ownership、job ID schema |
| ChromeBridge | server-signed client identity、managed-only high privilege、per-origin capability |
| ImageFileServer | bearer/header ticket、非 URL key、realpath、size/MIME/SVG policy |
| VCPClawMail | account/recipient allowlist、send/reply permit、URL/file deny-by-default、prompt isolation |
| VCPToolBridge | fail-closed、exact allowlist、独立 token、rate limit、patch teardown |

通过门槛：

- 每个重新启用插件都有独立 threat model、negative tests 和 rollback。
- 一个插件被攻破不能读取 root env 或调用未授权工具。
- 当前 blocked 状态只在门槛通过后逐个改变，不成批恢复。

### Phase 4: 建立记忆治理桥

**目标：保留 VCP 的记忆智能，同时阻止默认全量读取和静默外发。**

动作：

1. 先建立完全 synthetic、可丢弃的记忆 corpus。
2. 将 memory source、derived chunk、vector、summary、timeline 分层标记。
3. 每个检索请求必须声明 owner、agent、task、notebook/folder scope 和 purpose。
4. provider egress 单独授权；服务启动不隐含 embedding/rerank 许可。
5. 支持 local/no-egress embedding profile，先验证本地链。
6. 对发往 provider 的文本做 data classification、最小化和可追溯摘要。
7. timeline/summary/persona 写回时强制 `derived` provenance，不允许伪装成原始事实。
8. 为 derived state 建 rebuild/rollback；原始 source 不被自动覆盖。
9. `codex-memory` 提供低披露访问证据，不复制 raw memory。
10. 定义 retention、删除传播、索引重建和 provider failure 行为。

必须验证的场景：

- 未授权 Agent 无法跨 folder/notebook 搜索。
- `search_all` 不能绕过 scope。
- provider 被禁用时，启动和本地检索不会偷偷外发。
- summary/timeline 错误可以撤回且不污染 source。
- 删除 source 后，SQLite/Vexus/TDB 派生状态最终一致删除。
- shutdown/restart 不丢失待处理状态，也不重复外发。

通过门槛：

- synthetic corpus 端到端通过。
- 真实记忆仍未启用，直到 Jenn 对明确范围做当前授权。
- 记忆审计只记录范围、摘要和结果，不记录 raw private content。

### Phase 5: 把任务可靠性移出 VCP 内部假设

**目标：VCP 能执行任务，但不能独自决定 AGENTS OS 任务事实。**

动作：

1. 选择一个现有 store 作为 canonical global task ledger，不新建平行数据库。
2. ledger 分配 Task ID、attempt、event sequence 和 idempotency key。
3. `codex-router` 候选负责 permit、lease、renew、expiry、retry 和 recovery policy。
4. VCP scheduler/AgentAssistant 通过 adapter 接受 task envelope。
5. VCP 只回传事实事件，不直接把 `[[TaskComplete]]` 晋升为全局完成。
6. 执行宿主必须附带 artifact、diff、test/validation result 或明确 `NO_ARTIFACT`。
7. crash 模拟覆盖“副作用已发生但完成事件未写入”。
8. Dashboard/Workbench 只读 projection，不回写 source state。

通过门槛：

- 同一 Task ID 只有一个 authoritative lifecycle。
- VCP restart 后不会重复外部写。
- lease 过期和 worker 失联可诊断、可恢复。
- Agent 文本声明与验证结果冲突时，以验证事实为准。

### Phase 6: 建立真实测试与 CI 门槛

**目标：不再以“生产跑过”替代回归验证。**

测试层：

```text
L0 manifest/schema/config-default tests
L1 pure unit tests
L2 auth/path/env isolation negative tests
L3 plugin contract tests with fake providers
L4 disposable runtime integration tests
L5 crash/restart/idempotency tests
L6 synthetic memory end-to-end tests
L7 manually authorized external-effect canary
```

CI 最低要求：

- `npm test` 成为真实入口。
- lint/typecheck 或至少 deterministic syntax check。
- Linux x64 native binding smoke。
- fake provider server，禁止真实付费调用。
- secret scanner 只扫描受控代码/fixture，不读取 active config。
- path traversal、SSRF、prompt injection、env isolation 回归集。
- Docker build 只在测试通过后进行。
- publish 与普通 CI 分离，tag 不自动绕过人工 release gate。

通过门槛：

- 关键安全负面测试失败时 CI 必须失败。
- clean checkout 可重复安装和测试。
- 测试不读取真实记忆、凭据或 active state。

### Phase 7: 分级启用而不是“一键恢复”

建议运行 profile：

| Profile | 能力 | 禁止项 |
|---|---|---|
| P0 Structural | manifest、schema、status、fake provider | 无插件副作用、无真实数据 |
| P1 Observe | 低披露健康状态、受控 metadata | env、raw config、raw logs、memory、network write |
| P2 Memory Lab | synthetic corpus、本地 embedding/retrieval | 真实记忆、外部 provider |
| P3 Workspace Lab | disposable workspace 内 bounded read/write | home-wide access、外网、真实外部写 |
| P4 Controlled Runtime | 通过 catalog 的选定插件 | 未列出的 capability |
| P5 External Effect | 单次邮件/浏览器/外部写 canary | 无精确当前 permit 的任何副作用 |

每次晋级需要：

- capability list。
- effective config diff，不含 secret value。
- tests/negative tests。
- rollback。
- 观察窗口和失败判据。
- Jenn 当前授权，仅当触及 P3 时。

### Phase 8: 三任务 benchmark 与 ADR

完成上述最低边界后，用完全相同的三个 Green Lane 任务比较：

1. Workbench 路径。
2. `codex-router` + Codex host 路径。
3. canonical ledger + VCP Gateway + VCPToolBox 路径。
4. ColaMeta managed executor 路径可作为额外执行宿主对照，不让 plan version 混入总账。

任务选择：

- 只读 repo inventory。
- disposable workspace 内确定性文本变换和验证。
- synthetic memory corpus 的 scoped retrieval。

测量：

- intake latency。
- 是否自动推进。
- 是否只有一个任务状态事实。
- crash 后是否恢复。
- rerun 是否幂等。
- 是否重复执行。
- 人工确认次数。
- 产生多少治理文件。
- 失败是否可诊断。
- artifact/validation 是否能被 Dashboard 正确读取。
- 是否发生未声明的 network、memory 或 file access。

最后才冻结：

```text
ADR - AGENTS OS Kernel, VCP Runtime Body, Execution Host and State Authority
```

ADR 必须基于 benchmark 结果，不根据项目体量或愿景投票。

## 21. 现在最该做的十件事

按实际优先级压缩成大白话：

1. **别恢复插件。** 当前 83 个 blocked 先保住。
2. **别启动真实记忆链。** 启动可能扫描并外发文本。
3. **先堵路由认证。** special router 和 callback 是最先修的洞。
4. **把服务默认锁在本机。** loopback、可信 proxy、CORS allowlist。
5. **做插件能力清单。** 不再用“启用/禁用”代替权限判断。
6. **做 VCP Gateway。** 让每次调用绑定 task、actor、capability、permit 和 idempotency。
7. **切断插件继承全部环境变量。** 每个插件只拿到自己必需的值。
8. **用假数据重建测试。** 先 synthetic memory 和 disposable workspace，不碰真实记忆。
9. **总账放外面。** VCP scheduler 继续做内部调度，不当 AGENTS OS 事实中心。
10. **逐个放行。** 每个插件过 threat model、负面测试和 rollback 后再启用。

## 22. 明确的非目标

下一阶段不要做：

- 不重写一套新的 VCPToolBox。
- 不把 Workbench 升格成 runtime kernel。
- 不把 `codex-router` 未经 benchmark 就宣布为全部 runtime 的所有者。
- 不新建第五套/第六套 task database。
- 不用更多 receipt、review、gate 文档代替代码边界。
- 不在真实记忆上边开发边试。
- 不用共享六码模拟 Jenn 的 P3 授权。
- 不按 README 的 300+ 插件目标追求恢复数量。
- 不先做移动端、音频、Presence 或展示层扩张。
- 不通过 `reset`、`clean` 或覆盖同步处理当前 VCP 工作树。

## 23. 待验证未知项

以下事实本轮有意没有读取或执行：

- 当前 `config.env` 实际 bind host、sandbox backend、provider、memory path 和 feature flags。
- 当前 admin、VCP、Image、File、browser、distributed credential 的状态。
- 实际 DailyNote、SQLite、Vexus、TDB 数据量和内容。
- 当前 `VCPTaskAssistant/task-center-data.json` 的任务状态。
- 当前 bridge/browser active config 和 managed profile 内容。
- 真正服务启动后的端口、ready、shutdown 和资源泄漏表现。
- provider latency、费用、embedding/rerank 数据范围。
- browser、mail、Shell、PowerShell 在真实环境中的行为。
- Vexus 真实 corpus 的正确性、召回率和并发性能。
- README 性能指标和 7x24 稳定性。

这些不是遗漏，而是下一阶段按 profile 和授权逐项验证的边界。

## 24. 主要源码证据索引

启动/API/认证：

```text
runtime/VCPToolBox/server.js
runtime/VCPToolBox/routes/specialModelRouter.js
runtime/VCPToolBox/adminServer.js
runtime/VCPToolBox/modules/captchaDecoder.js
```

插件与工具执行：

```text
runtime/VCPToolBox/Plugin.js
runtime/VCPToolBox/Plugin/PluginManager/PluginManager.js
runtime/VCPToolBox/modules/vcpLoop/toolExecutor.js
runtime/VCPToolBox/modules/vcpLoop/toolCallParser.js
runtime/VCPToolBox/modules/toolCallRecordStore.js
runtime/VCPToolBox/modules/toolApprovalManager.js
runtime/VCPToolBox/WebSocketServer.js
runtime/VCPToolBox/FileFetcherServer.js
```

任务与 Agent：

```text
runtime/VCPToolBox/routes/taskScheduler.js
runtime/VCPToolBox/Plugin/VCPTaskAssistant/
runtime/VCPToolBox/Plugin/AgentAssistant/
```

记忆与知识：

```text
runtime/VCPToolBox/KnowledgeBaseManager.js
runtime/VCPToolBox/TDBKnowledge.js
runtime/VCPToolBox/Plugin/DailyNote/
runtime/VCPToolBox/Plugin/DailyNoteManager/
runtime/VCPToolBox/Plugin/RAGDiaryPlugin/
runtime/VCPToolBox/TagMemoEngine.js
runtime/VCPToolBox/Plugin/LightMemo/
runtime/VCPToolBox/Plugin/OneRing/
runtime/VCPToolBox/Plugin/VCPTimeLine/
runtime/VCPToolBox/Plugin/AgentDream/
runtime/VCPToolBox/Plugin/ContextFoldingV2/
runtime/VCPToolBox/Plugin/OpenHerPersona/
runtime/VCPToolBox/rust-vexus-lite/
```

高权限能力：

```text
runtime/VCPToolBox/Plugin/FileOperator/
runtime/VCPToolBox/Plugin/PowerShellExecutor/
runtime/VCPToolBox/Plugin/LinuxShellExecutor/
runtime/VCPToolBox/Plugin/AICodeWorker/
runtime/VCPToolBox/Plugin/ChromeBridge/
runtime/VCPToolBox/Plugin/ImageFileServer/
runtime/VCPToolBox/Plugin/VCPClawMail/
runtime/VCPToolBox/Plugin/VCPToolBridge/
runtime/VCPToolBox/Plugin/UserAuth/
```

工程基线：

```text
runtime/VCPToolBox/package.json
runtime/VCPToolBox/package-lock.json
runtime/VCPToolBox/.github/workflows/ci.yml
runtime/VCPToolBox/tests/
runtime/VCPToolBox/AGENTS.md
runtime/VCPToolBox/README.md
```

### 24.1 P0 结论的源码锚点

以下行号固定对应本报告审查的 `HEAD 555b3b5` 与当前工作树；后续 main 变化时应按 commit 对照，不应机械沿用行号。

| 结论 | 源码锚点 |
|---|---|
| special router 先于通用 Bearer auth 挂载 | `server.js:639-641`；通用 Bearer skip/check 在 `server.js:862-872` |
| special router 使用服务器 provider key 转发 | `routes/specialModelRouter.js:68-100`、`121-146` |
| callback 跳过 Bearer | `server.js:862-865` |
| callback 先写文件、后检查 plugin | `server.js:1460-1485` |
| schedule task ID 直接参与路径构造和写入 | `server.js:989-1022` |
| 主服务没有显式 host bind | `server.js:1670` |
| 主服务 `trust proxy=true`、CORS `*` | `server.js:547-548` |
| admin 同样 `trust proxy=true`、CORS `*`，且无显式 host bind | `adminServer.js:46-47`、`664` |
| manifest config 缺值时跳过，没有应用 schema default | `Plugin.js:94-128` |
| static/stdio plugin 继承完整 `process.env` 并使用 `shell:true` | `Plugin.js:238-251`、`1235-1236`、`1326` |
| `requiresAdmin` 向 direct/child plugin 提供解码 code | `Plugin.js:1090-1097`、`1251-1260` |
| VCPToolBridge 对缺失 `Bridge_Enabled` 使用非 false 即启用语义 | `Plugin/VCPToolBridge/index.js:41`、`63`、`105`、`144` |
| AICodeWorker 三种模式允许 `--dangerously-skip-permissions` | `Plugin/AICodeWorker/AICodeWorker.js:631`、`692-738` |

## 25. 最终判断

```yaml
project_reality:
  real_runtime: true
  feature_depth: high
  memory_value: high
  direct_agents_os_readiness: false
  current_isolation_should_be_preserved: true

recommended_role:
  runtime_body: true
  plugin_host: true
  memory_intelligence_owner: true
  governed_memory_access_owner: false
  global_task_ledger_owner: false
  p3_permission_authority: false
  secure_executor_by_default: false

next_decision:
  build_external_gateway_first: true
  fix_network_and_auth_first: true
  use_synthetic_data_first: true
  reactivate_plugins_incrementally: true
  benchmark_before_adr: true
```

最后用一句最朴素的话收住：

> 我们已经找到了一具真正能承载 AGENTS OS 的身体，但这具身体现在神经、记忆、权限和工具还缠在一起。下一阶段不是继续给它加器官，而是先把门禁、神经传导、记忆权限和任务事实分清，然后一项一项让它醒过来。
