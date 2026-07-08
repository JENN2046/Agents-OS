# AGENTS OS VCPToolBox Documentation Reality Map v0.1

Date: 2026-07-08

Owner: Jenn

Agent steward: Nobao

Status: accepted local reality map

Scope: classify VCPToolBox documentation and dailynote knowledge surfaces for AGENTS OS integration

## Purpose

This map records the current read-only understanding of VCPToolBox documentation
surfaces after Jenn asked Nobao to continue learning VCPToolBox through its
documentation and dailynote materials.

The goal is not to promote every VCPToolBox document into AGENTS OS authority.
The goal is to separate:

- current code-backed runtime facts
- newer product and architecture intent
- historical or stale documentation
- dailynote knowledge-library material
- Agent cognitive-route material
- diary-like or private memory surfaces that must not be treated as ordinary docs

## Explicit Non-Actions

- No VCPToolBox service was started.
- No plugin was enabled.
- No plugin was executed.
- No provider call was made.
- No active `config.env`, `.env`, credential, token, cookie, provider raw
  response, raw log content, or `state-private/` content was read.
- No VCPToolBox source, plugin manifest, runtime state, or formal AGENTS OS
  Memory content was modified.
- No external write, commit, push, tag, deploy, publish, or release was
  performed.

## Reality Classes

### Class A: Current Code-Backed Runtime Facts

Use these as high-confidence runtime maps, then verify against source before
changing behavior:

- `runtime/VCPToolBox/README.md`
- `runtime/VCPToolBox/docs/TECHNICAL_LITE.md`
- `runtime/VCPToolBox/docs/ARCHITECTURE.md`
- `runtime/VCPToolBox/docs/PLUGIN_ECOSYSTEM.md`
- `runtime/VCPToolBox/docs/API_ROUTES.md`
- `runtime/VCPToolBox/docs/CONFIGURATION.md`
- `runtime/VCPToolBox/docs/OPERATIONS.md`
- `runtime/VCPToolBox/docs/SEMANTIC_MODEL_ROUTER.md`
- `runtime/VCPToolBox/docs/CONTEXT_BRIDGE.md`
- selected plugin README files, especially:
  - `Plugin/AgentAssistant/README.md`
  - `Plugin/OneRing/README.md`
  - `Plugin/OpenHerPersona/README.md`
  - `Plugin/AgentDream/README.md`
  - `Plugin/VCPBridgeServer/README.md`
  - `Plugin/VCPTavern/README.md`

Current confirmed local metadata:

```text
VCPToolBox latest local commit: 49e72d92d29e48184b6a7e73098131cc416b53db
Commit date: 2026-07-03 17:48:31 +0800
Commit subject: Merge pull request #395 from XiaoHeiGe527/fix/aicodeworker-critical-bugs
Plugin manifest files observed: 83
Current local posture: plugin manifests are blocked as .block files
```

## Class B: Product Vision And Runtime Philosophy

Use these to understand intent, not as direct implementation authority:

- `runtime/VCPToolBox/VCP.md`
- `runtime/VCPToolBox/docs/vcp白皮书V3.md`
- `runtime/VCPToolBox/docs/TagMemo_Wave_Algorithm_Deep_Dive.md`

These documents describe VCPToolBox as an AGI runtime rather than a normal
Agent framework. The useful AGENTS OS interpretation is:

```text
AGENTS_OS = spirit / governance / task production / review chain
VCPToolBox = body / runtime / organs / tools / senses / memory interfaces
```

The vision is valuable, but it must be grounded by source and local state
before activation.

## Class C: Historical Or Stale Snapshot Material

`runtime/VCPToolBox/docs/DOCUMENTATION_INDEX.md` states that the full panorama
document set was generated for a `2026-02-13` code snapshot. Many docs were
copied or refreshed in the local checkout on `2026-07-03`, but internal content
can still describe older behavior.

Known drift examples:

- `MEMORY_SYSTEM.md` describes TagMemo V3.7 and says some V4/V5 features are
  planned.
- Later documents describe TagMemo V8.3/V8.4, TDB cold knowledge, and SQLite
  lease redesign.
- The documentation index reports a historical plugin count that differs from
  the current local 83 manifest files.

Rule: when docs disagree, prefer current code and narrowly scoped validation.

## Class D: Dailynote Knowledge-Library Surface

`runtime/VCPToolBox/dailynote/` is not one uniform kind of content. It contains
knowledge-library documents, Agent cognitive-route documents, and Agent
memory/diary material.

Observed top-level dailynote layout:

```text
DailyNoteCreateHere.txt
ExampleMaid/
VCP开发/
VCP桌面知识/
VCP论坛/
前思维簇/
反思簇/
可可的知识/
已整理/
测试思维簇/
结果辩证簇/
逻辑推理簇/
陈词总结梳理簇/
```

Observed file counts:

```text
ExampleMaid: 1
VCP开发: 3
VCP桌面知识: 7
VCP论坛: 0
前思维簇: 6
反思簇: 5
可可的知识: 2
已整理: 1
测试思维簇: 1
结果辩证簇: 6
逻辑推理簇: 8
陈词总结梳理簇: 7
root marker file: 1
total files observed: 48
```

### Dailynote Technical Knowledge Read

The following dailynote files were read because their paths and content indicate
technical knowledge or public sample material rather than private operational
memory:

- `dailynote/VCP开发/插件开发指令集.txt`
- `dailynote/VCP开发/静态插件折叠协议开发手册.md`
- `dailynote/VCP桌面知识/使用示例.txt`
- `dailynote/VCP桌面知识/分布式操作.txt`
- `dailynote/VCP桌面知识/桌面图标与启动API指南.txt`
- `dailynote/VCP桌面知识/桌面基础api.txt`
- `dailynote/可可的知识/CSS动画知识库.txt`
- `dailynote/ExampleMaid/2025.04.25.txt` as a sample diary format check

Findings:

- `VCP开发` acts like an in-memory plugin development handbook for Agents.
  It teaches plugin creation, manifest/config writing, escaped file writing,
  static plugin behavior, and the fold protocol.
- `VCP桌面知识` acts like a VCPDesktop operation manual for Agents. It explains
  `DESKTOP_PUSH`, widget creation, `vcpAPI`, `musicAPI`, `window.VCPDesktop`,
  launcher APIs, VChat app IDs, system tools, and widget sandbox APIs.
- `可可的知识` contains UI/CSS animation recipes for VCPChat themes and message
  effects.
- `ExampleMaid` confirmed that at least some dailynote files are true diary
  entries. This reinforces that dailynote cannot be treated as an ordinary docs
  directory.

## Class E: Agent Cognitive-Route Library

Jenn explicitly reclassified the following directories as Agent thought-route
design material rather than private memory:

- `前思维簇`
- `反思簇`
- `逻辑推理簇`
- `结果辩证簇`

`Agent/Metis.txt` also lists `陈词总结梳理簇` as part of the formal thought
cluster structure. It was therefore read as the same cognitive-route class.

These directories were directly read after classification. Current
understanding:

- `前思维簇` is the intake and pre-thinking layer. It classifies user intent,
  separates factual/logical work from value/insight work, builds context and
  boundaries, plans tool usage, and defines a dual-track cognitive firewall.
- `逻辑推理簇` is the reasoning layer. It contains dialectical reasoning,
  dynamic problem decomposition, first-principles and analogy routes,
  hypothesis testing, stakeholder/game analysis, high-entanglement cross-track
  fusion, information-gain weighting, and a specialized Chinese homophone-pun
  route.
- `反思簇` is the audit layer. It stress-tests assumptions, checks prompt and
  route quality, validates consistency, quantifies uncertainty, and performs
  value/ethics review.
- `结果辩证簇` is the final arbitration layer. It decides whether to release,
  patch, recurse, or ask the user, and it defines immune-memory style rules for
  avoiding repeated cognitive failure modes.
- `陈词总结梳理簇` is the final presentation and output-governance layer. It
  converts approved conclusions into user-facing language, adapts output to
  device/context, preserves fact/value separation through a cognitive firewall,
  records cognitive-footprint metadata, performs final ethical/effectiveness
  calibration, and can package results into knowledge crystals.

AGENTS OS interpretation:

```text
前思维簇 = intake / framing / tool planning / cognitive firewall
逻辑推理簇 = reasoning / controlled cross-fusion / information gain
反思簇 = red-team review / confidence audit / value audit
结果辩证簇 = final arbitration / recursion / user handoff / immune rules
陈词总结梳理簇 = final expression / presentation adaptation / output audit
```

This is not ordinary runtime documentation, but it is not private diary content
either. It is a modular Agent cognition design library. It can inform AGENTS OS
Machine, Task Producer, review chain, and memory-surface governance after being
translated into typed route cards or operating rules.

Important boundary:

These files describe intended Agent cognitive routes. They should not be
blindly promoted into always-on execution authority. AGENTS OS should absorb
them through a reviewable route-card layer that preserves:

- fact/logical track versus value/insight track separation
- controlled crossover only for high-entanglement problems
- confidence and uncertainty labels
- explicit final arbitration before action
- user handoff when recursion cost or action risk exceeds autonomous scope

## Class F: Diary-Like Or Still-Unclassified Memory Surfaces

The following dailynote directories must remain private-memory surfaces unless
Jenn explicitly reclassifies a specific file or subset as a public research
sample:

- `已整理`
- `测试思维簇`
- any other diary-like or thought-cluster file

Reason:

These names and dailynote semantics still indicate possible Agent diary,
generated memory, test-memory, or derived material. They are not equivalent to
source documentation until classified.

Update: after reading `Agent/Metis.txt`, `陈词总结梳理簇` is classified under
Class E as a formal cognitive-route cluster rather than a private diary
surface.

## Class G: Agent Role Packages

`runtime/VCPToolBox/Agent/` was directly read. It contains role prompt packages
rather than ordinary UI skins.

Observed Agent files:

- `Aemeath.txt`
- `DreamNova.txt`
- `Hornet.txt`
- `MemoMaster.txt`
- `Metis.txt`
- `Nova.txt`
- `ThemeMaidCoco.txt`
- `Weiming.txt`

Common structure:

- role identity and behavior contract
- memory index bindings through `TagMemo` / diary placeholders
- tool surface bindings through placeholder variables
- output rendering, emoji, music, file, media, search, memory, or forum
  capability references
- diary-writing or memory-update rules

Important Agent roles:

- `Nova` is a general VCP maid/test Agent with memory, forum, file/media/search,
  DeepWiki, and VCP development documentation access.
- `MemoMaster` is a specialized memory-governance Agent for scanning,
  organizing, event tracking, and deep cleaning diary memory. Its rules include
  non-deletion, traceability, uncertainty handoff, emotional-memory exemption,
  milestone exemption, and batch limits.
- `Metis` is the cognitive-architecture steward for thought clusters. It maps
  semantic tokens to clusters, checks redundancy/conflict/isolation/overload,
  and proposes merge/split/health-check operations while keeping final
  decisions with the owner or higher coordinator.
- `ThemeMaidCoco` is a specialized VChat theme authoring Agent.
- `Weiming` is a research/writing Agent with dialectical and first-principles
  investigation style.
- `Aemeath`, `Hornet`, and `DreamNova` show that VCP Agent packages can combine
  fictional identity, affective style, memory, tools, and persistent context.

AGENTS OS interpretation:

```text
VCP Agent package = identity + memory bindings + tool bindings + output style + diary/update protocol
```

This makes VCPToolBox materially more than a tool host. It already has a
runtime pattern for embodied Agent personas and specialized background roles.

## Class H: Multi-Agent Dispatch And Runtime Organs

`docs/AGENT_AND_TASK_SYSTEM_GUIDE.md` defines two major runtime layers:

- `AgentAssistant` (AA): identity/personality, conversation context window,
  hot reload, model binding, max tokens, temperature, global prompts.
- `TaskAssistant` (FA): task scheduling and dispatch, including forum patrol,
  custom prompts, interval/cron/once/manual schedules, target Agents, injected
  tools, temporary-contact mode, and execution history.

AGENTS OS mapping:

```text
AgentAssistant = role registry / living role runtime
TaskAssistant = task producer / scheduler / dispatch layer
```

The plugin development notes define the body-organ mechanism:

- synchronous plugins run as subprocesses through stdio
- asynchronous plugins return a placeholder and later callback with results
- `plugin-manifest.json` is the organ manifest
- `invocationCommands.description` is the organ instruction exposed to Agents
- plugin descriptions are injected through placeholders such as
  `{{VCPSciCalculator}}`
- batch tool calls use numbered suffixes like `command1`, `filePath1`
- admin-risk tools can require VCP Auth verification
- AI-friendly tool results should use OpenAI-style `content` arrays to avoid
  JSON escaping damage and support multimodal outputs

AGENTS OS interpretation:

```text
plugin manifest = organ registry entry
invocationCommands = affordance grammar
Agent prompt placeholder = organ attachment point
async placeholder/callback = long-running organ nerve loop
```

## Class I: Memory, Knowledge, Context, And Model Routing

The memory documents show a three-part memory body:

1. Hot memory:
   - `dailynote/`
   - TagMemo
   - Agent diary, reflection, collaboration, and work memory
   - optimized for association, reasoning, recall, and identity continuity
2. Cold knowledge:
   - `knowledge/`
   - `TDBKnowledge.js`
   - TriviumDB `.tdb` libraries
   - optimized for manuals, papers, private data, large factual corpora, and
     source-grounded retrieval
3. Retrieval router:
   - `LightMemo`
   - routes normal memory retrieval versus `[知识库]` cold-knowledge retrieval
   - supports BM25/BM25+, RAG, TagMemo, rerank, and cold-knowledge result
     formatting

`ContextBridge` exposes a read-only context-vector interface for other plugins:

- current conversation aggregate vectors
- semantic segments
- logic-depth and semantic-width metrics
- cached embedding helpers
- text sanitization and vector math

`Semantic Model Router` uses context vectors and route descriptions to pick a
real backend model behind a virtual model such as `VCPModelAuto`, then builds a
failover chain.

AGENTS OS interpretation:

```text
TagMemo hot memory = lived memory / associative cortex
TDB cold knowledge = document library / factual archive
LightMemo = retrieval traffic controller
ContextBridge = read-only context nervous system
Semantic Model Router = task-sensitive model dispatch
```

This gives AGENTS OS a concrete body integration target: not just "call VCP as
a tool", but connect governance and task production to VCP's role registry,
plugin organs, memory layers, context bridge, and dispatch loop.

## Class J: Source-Backed Deep Runtime Map

This section records the deeper source-read pass completed after the initial
documentation map. It should be treated as higher confidence than product
vision text, while still not authorizing service startup or plugin activation.

### Startup Spine

`server.js` starts the body in this order:

- initialize `KnowledgeBaseManager`
- initialize `TDBKnowledgeManager`
- inject both managers into `PluginManager`
- initialize `dynamicToolRegistry`
- load plugin manifests
- attach WebSocket functions and initialize service plugins
- mount Admin API and forum routes
- inject dependencies into message preprocessors and services
- initialize static plugins and prewarm Python plugins
- initialize task scheduler
- initialize model redirect, semantic model router, `agentManager`,
  TVS/toolbox/SAR prompt managers
- start HTTP listener, WebSocket server, and file fetcher server

AGENTS OS interpretation:

```text
VCP startup = memory managers -> plugin organs -> admin/control routes -> schedulers -> network nerves
```

### Chat Completion Spine

`ChatCompletionHandler` is the primary request spine for
`/v1/chat/completions` and `/v1/chatvcp/completions`.

Observed stages:

- prune context by token limit
- apply model redirect unless the request targets semantic routing
- detect `[[VCPToolUse=Forbidden]]`
- detect media placeholders
- run priority `VCPTavern`
- run semantic model routing
- apply model-specific thinking control
- force multimodal-to-text where needed
- replace Agent/toolbox variables sequentially
- run media processor and remaining preprocessors
- run detectors and optional role divider
- capture OneRing metadata and final context
- call upstream OpenAI-compatible backend
- delegate final handling to stream or non-stream handler

AGENTS OS governance insertion points:

```text
pre-variable -> pre-upstream -> pre-tool-execution -> post-tool-result -> memory-write
```

### Tool Loop

VCP tool calls are not OpenAI function calling. They are parsed from visible
model output using:

```text
<<<[TOOL_REQUEST]>>>
field:「始」value「末」
<<<[END_TOOL_REQUEST]>>>
```

`ToolCallParser` ignores `<think>...</think>`, supports fuzzy marker matching,
and parses special fields including `archery`, `ink`, `river`, and `vref`.

`ToolExecutor` can attach contextual payloads:

- `river=full`: full multimodal context
- `river=text`: text-only context
- `river=last:N`: recent text messages
- `river=semantic:N`: semantically selected messages
- `vref`: relevant diary files as local file references
- `timely_contact`: schedules a future tool call

`StreamHandler` and `NonStreamHandler` collect the model response, parse tool
requests from visible content, execute tools, inject results back as
`<!-- VCP_TOOL_PAYLOAD -->`, optionally refresh RAG blocks, and recurse until
no tools remain or max depth is reached.

AGENTS OS interpretation:

```text
VCP tool loop = visible text protocol + context attachment + plugin execution + recursive model continuation
```

### Plugin Organ Manager

`Plugin.js` is the organ manager. It loads manifests, blocked manifests,
plugin-local config, service modules, message preprocessors, static
placeholders, distributed tools, admin approval, and result privacy filtering.

Key observed mechanics:

- disabled plugins use `plugin-manifest.json.block`
- loaded plugins can be `static`, `messagePreprocessor`, `synchronous`,
  `asynchronous`, `service`, or `hybridservice`
- plugin `config.env` is loaded by the runtime but was not read in this task
- plugins can receive injected managers such as RAG, TDB, ContextBridge,
  VectorDB, WebSocket, and admin auth context
- `processToolCall()` applies tool approval before dispatch
- local plugins can receive fetched `file://` arguments
- stdio plugins run in plugin cwd with merged environment
- hybrid services can receive direct `processToolCall`
- tool results are passed through `toolResultPrivacyGuard`

AGENTS OS interpretation:

```text
PluginManager = organ loader + nerve router + approval gate + privacy guard
```

### Hot Memory And RAG Spine

`RAGDiaryPlugin` is not a simple diary searcher. It is the hot-memory and
thought-route injection engine.

Observed stages:

- fast-path direct text diary placeholders
- update context vectors with optional no-provider cache reuse
- sync context into `FoldingStore`
- identify system or privileged user carriers
- detect RAG, direct diary, hybrid diary, TDB, AIMemo, and meta-thinking
  placeholders
- build query vector from last real user message and last assistant message
- resolve hard/soft ghost tags from AI anchors
- process meta-thinking, RAG, direct text, hybrid, cold knowledge, and AIMemo
  requests concurrently

Core RAG suffixes and retrieval modes observed:

- direct diary text: `{{...日记本}}`
- vector RAG: `[[...日记本]]`
- threshold-gated full/direct text: `<<...日记本>>`
- threshold-gated RAG: `《《...日记本》》`
- meta thinking: `[[VCP元思考...]]`
- cold knowledge: `[[...知识库]]` and `《《...知识库》》`
- modifiers include `::Time`, `::Group`, `::Rerank`, `::Rerank+`,
  `::BM25`, `::BM25+`, `::TagMemo`, `::TagMemo+`, `::TimeDecay`,
  `::Truncate`, `::Expand`, `::Associate`, `::Base64Memo`, and AIMemo modes

Post-retrieval governance:

- deduplicate against current context
- apply Time/TimeDecay
- apply BM25 sparse recall where requested
- apply TagMemo vector boost and geodesic rerank
- apply Rerank/RRF
- optionally append recent continuity chunks
- optionally discover associative co-occurrence
- optionally expand parent documents
- broadcast sanitized retrieval details through VCPInfo
- cache results

AGENTS OS interpretation:

```text
RAGDiaryPlugin = associative cortex + thought-route loader + retrieval telemetry producer
```

### ContextBridge And No-Provider Boundary

`RAGDiaryPlugin.getContextBridge()` exposes a frozen interface for other
plugins:

- aggregated assistant/user vectors
- history vectors
- semantic context segments
- logic-depth and semantic-width metrics
- text sanitizer
- cosine similarity, weighted average, average vector
- embedding cache lookup
- optional `embedText` / `embedBatch`
- `FoldingStore` access

Important boundary:

`embedText` and `embedBatch` can trigger embedding API calls on cache miss.
AGENTS OS no-provider use must default to cache-only functions such as
`getEmbeddingFromCache` or explicit dry-run/preview modes.

### Memory Storage Split

Hot memory:

- `KnowledgeBaseManager.js`
- root default `dailynote/`
- store default `VectorStore/`
- SQLite metadata and chunks
- Rust `VexusIndex`
- TagMemo engine
- RAG parameter watcher
- Rust write lease to avoid SQLite WAL contention
- file watcher and batch index/update/delete queues

Cold knowledge:

- `TDBKnowledge.js`
- root default `knowledge/`
- store default `VectorStoreTDB/`
- TriviumDB `.tdb` libraries
- document/chunk graph links
- hybrid BM25 + vector + graph expansion
- optional parent document expansion
- library-level idle unload

AGENTS OS interpretation:

```text
hot memory = lived, associative, identity-bearing recall
cold knowledge = low-frequency, source-like library retrieval
```

### Agent And Task Spine

`agentManager` hot-loads `Agent/*.txt|*.md` role packages through
`agent_map.json`, tracks available Agent files, and caches prompts.

`AgentAssistant` provides Agent-to-Agent communication and async delegation:

- loads Agent definitions from `Plugin/AgentAssistant/config.json`
- supports temporary contact and persistent session context
- supports future contact through scheduler API
- supports async delegation with bounded rounds, heartbeat delays,
  cancellation, completion/failure markers, score updates, and archived
  reports
- calls local VCP `/v1/chat/completions`, therefore it is provider-backed

`VCPTaskAssistant` is a task producer and scheduler:

- stores task-center data
- supports interval, once, cron, and manual schedules
- supports forum patrol and custom prompt tasks
- dispatches by direct `AgentAssistant.processToolCall`
- records runtime and history

AGENTS OS interpretation:

```text
AgentManager = role package registry
AgentAssistant = Agent communication bus
VCPTaskAssistant = task producer / scheduler
```

### Admin And Runtime Control Surface

Admin API mounts many control modules: system, logs, config, plugins, agents,
RAG, task assistant, dynamic tools, semantic router, daily notes, plugin store,
multimodal config, and more.

Important source-backed risk facts:

- `/plugins` reads and returns plugin `config.env` content for Admin UI.
- `/plugins/:pluginName/config` writes plugin `config.env`.
- `/plugins/:pluginName/toggle` enables or disables plugins by renaming
  `plugin-manifest.json` and `.block`.
- Agent routes can create and write Agent files and save `agent_map.json`.
- TaskAssistant routes can create/update/delete/trigger tasks.
- Semantic-router and dynamic-tools routes can write routing and tool-selection
  configs.

AGENTS OS interpretation:

```text
AdminPanel = owner console, not an autonomous Agent control API by default
```

The Admin surface is powerful enough to mutate runtime identity, plugin
activation, provider routing, memory/knowledge content, and scheduler behavior.
Future AGENTS OS integration should treat Admin writes as gated operations, not
ordinary automation.

### WebSocket Nerves And Human Approval

`WebSocketServer.js` defines distinct client types:

- `VCPLog`
- `VCPInfo`
- `DistributedServer`
- `ChromeObserver`
- `ChromeControl`
- `AdminPanel`

It handles:

- VCPLog and VCPInfo broadcast
- distributed tool registration and execution
- distributed callback persistence
- Chrome observer/control relay
- AdminPanel connection tracking
- tool approval responses
- VCPLog replay/offline delivery

Tool approval is routed through WebSocket: the runtime broadcasts
`tool_approval_request`; the UI can respond with `tool_approval_response`; then
`PluginManager.handleApprovalResponse()` continues or rejects the pending tool.

AGENTS OS interpretation:

```text
WebSocketServer = runtime nervous system + observer channel + approval return path
```

### Dynamic Tool Selection And Model Routing

`modules/dynamicToolRegistry.js` confirms that VCPToolBox does not rely only on
a static tool prompt. It builds a runtime catalog from PluginManager manifests,
persists lightweight plugin records in `ToolConfigs/dynamic_tool_catalog.json`,
persists classifications in `ToolConfigs/dynamic_tool_categories.json`, and
then uses `{{VCPDynamicTools}}` to show:

- a light list of available tools
- expanded usage only for matched tools
- explicit tool/category directives
- pinned/manual description overrides
- distributed-tool history compaction

The registry can classify tools through three layers:

1. small-model classification when configured
2. RAG embedding similarity classification when available
3. keyword fallback classification

Important source-backed boundary:

```text
dynamic tool catalog sync = local mutation
small-model classification = provider-backed unless explicitly disabled
embedding classification = may be provider-backed on cache miss
keyword fallback = pure local
```

`modules/semanticModelRouter.js` confirms the model-routing body part:
`VCPModelAuto` is a virtual model name that resolves to a preset. The router
embeds the latest real user message plus latest assistant context, compares it
against route descriptions by cosine similarity, and returns an ordered
candidate chain: semantic hit, default model, then fallback models.

AGENTS OS interpretation:

```text
DynamicToolRegistry = tool-muscle attention selector
SemanticModelRouter = model-organ selector
```

Future AGENTS OS integration should split these features into:

- pure-local preview: catalog read, keyword fallback, no provider call
- provider-backed classification/routing: explicit gate
- runtime mutation: explicit config/write gate

### Context Folding, Timeline, And Tool-Result Recursion

`Plugin/ContextFoldingV2/ContextFoldingV2.js` confirms that context folding is
an opt-in message preprocessor activated by `[[ContextFoldingV2]]` or
`{{ContextFoldingV2}}`. It identifies older assistant blocks, builds a context
vector from the latest real user/assistant material, computes a dynamic
threshold, and either:

- keeps relevant old assistant content
- replaces low-relevance content with a stored summary when ready
- queues asynchronous summary generation when no summary exists

Its embedding path first tries exact/fuzzy cache reuse, then may call
`ContextBridge.embedText`. Its summary path calls a chat-completions API through
configured `API_URL` and `API_Key`.

Boundary:

```text
folding by existing summary/cache = local/context mutation
embedding on cache miss = provider-backed
summary generation = provider-backed
summary store update = local memory/cache mutation
```

`Plugin/OneRing/OneRing.js` confirms the unified timeline body part. It
records true user/assistant turns into Agent-specific SQLite timelines,
patches cross-frontend context when allowed, strips its own tail markers before
folding, and avoids recording reasoning content. `Plugin/VCPTavern` provides a
separate time/session injection path.

`modules/vcpLoop/toolExecutor.js`, `streamHandler.js`, and
`nonStreamHandler.js` confirm the recursive tool loop:

1. visible tool-call blocks are parsed from model output
2. `river` may attach conversation context to a tool call
3. `vref` may attach semantically related `file://` diary references
4. tool results are injected back as `<!-- VCP_TOOL_PAYLOAD -->`
5. the model is called again with the tool payload

AGENTS OS interpretation:

```text
OneRing = cross-frontend lived timeline
ContextFoldingV2 = long-context metabolism
river/vref/tool payload = tool-call bloodstream
```

These are powerful body functions. They must not be treated as ordinary prompt
formatting because they can decide what memory/context/file references flow
into a tool or back into the next model call.

### Multimodal, File Transfer, And Approval Boundary

`Plugin/ImageProcessor/image-processor.js` confirms that VCPToolBox can
translate base64 `image`, `audio`, and `video` data into text before upstream
model calls. It stores multimodal descriptions in
`Plugin/ImageProcessor/multimodal_cache.sqlite` and wraps results inside
`<VCP_MULTIMODAL_INFO>`. The runtime config source is
`modules/multiModalConfigStore.js`, where `multimodal-config.json` takes
priority over env-derived defaults and hot-reloads through a watcher.

Boundary:

```text
multimodal cache hit = local read
multimodal cache write = local runtime memory/cache mutation
multimodal translation miss = provider-backed
multimodal-config write = runtime config mutation
```

`FileFetcherServer.js` confirms that `file://` is also a distributed-file
transport protocol. If a local file URL is missing, VCPToolBox can request the
file from a known distributed server over WebSocket and cache it locally under
`.file_cache`.

Boundary:

```text
local file existence check = local read
distributed file fetch = distributed runtime action
file cache write = local runtime cache mutation
file URL passed to plugins = file-access capability
```

`modules/toolApprovalManager.js`, `modules/toolResultPrivacyGuard.js`, and
`Plugin.js` confirm that VCPToolBox already has a human-in-the-loop approval
surface and a tool-result privacy sanitizer. Approval can require manual
permission by tool or command, support timeout and silent rejection, and return
approval responses through WebSocket. The privacy sanitizer can mask sensitive
keys and high-confidence token patterns, while preserving data base64 URIs, but
its default configuration is disabled.

AGENTS OS interpretation:

```text
ToolApprovalManager = existing runtime approval organ
ToolResultPrivacyGuard = existing result-sanitization organ, not yet enough by default
FileFetcherServer = distributed file nerve
ImageProcessor = sensory translation organ
```

For AGENTS OS, the important conclusion is direct:

```text
VCPToolBox already has many body organs.
The missing layer is not capability.
The missing layer is a consistent AGENTS OS contract over which organs may
activate automatically, which require Jenn approval, and which are forbidden.
```

### AgentAssistant And TaskAssistant

`Plugin/AgentAssistant/AgentAssistant.js` confirms that AgentAssistant is a
real Agent-to-Agent communication organ, not only a prompt template.

Observed mechanics:

- loads Agent definitions from plugin-local `config.json`
- maintains per-Agent/per-session short-term conversation context with TTL
- supports temporary contact that skips stored session history
- attaches `river_context` as text and multimodal parts
- supports `inject_tools` as a temporary system-prompt tool group
- supports `timely_contact` by calling the local scheduler endpoint
- supports async delegation with `[[TaskComplete]]`, `[[TaskFailed]]`, and
  `[[NextHeartbeat::seconds]]`
- persists async results through `VCPAsyncResults` and `file/document/AgentTask`
- awards Agent points into `agent_scores.json`
- calls local `/v1/chat/completions`, so actual Agent contact is
  provider-backed

Boundary:

```text
AgentAssistant immediate contact = provider-backed Agent execution
AgentAssistant future contact = scheduler write + future provider-backed execution
AgentAssistant delegation = background Agent loop + async result persistence
AgentAssistant config migration/score write = local runtime mutation
```

`Plugin/VCPTaskAssistant/vcp-task-assistant.js` confirms that TaskAssistant is
already a task producer / scheduler prototype:

- state file: `Plugin/VCPTaskAssistant/task-center-data.json`
- task types: `forum_patrol`, `custom_prompt`
- schedules: `interval`, `once`, `manual`, `cron`
- targets: one or more Agents, including random selection patterns
- dispatch: direct `AgentAssistant.processToolCall`
- history: bounded execution records
- scheduler rebuild on config/task changes
- manual trigger, create/update/delete task, global enable switch

AGENTS OS interpretation:

```text
AgentAssistant = embodied Agent contact / delegation organ
VCPTaskAssistant = already-existing Task Producer body organ
```

The AGENTS OS Machine/Task Producer plan should not ignore this. The more
accurate route is to wrap VCPTaskAssistant with AGENTS OS task contracts,
review rules, evidence, and activation gates.

### Diary, Forum, And Memory Write Surfaces

`Plugin/DailyNote/dailynote.js` confirms that DailyNote is a formal memory
writer:

- writes new diary files under `dailynote/<folder>/`
- supports explicit `folder` or `[folder]maid` routing
- requires `Tag:` either in content or a separate field
- optional TagMaster can call a model to generate tags
- converts local `file://` images/files into served URLs by copying them into
  `image/dailynote` or `file/dailynote`
- enforces path containment under the dailynote root
- ignores selected folders such as `MusicDiary`

`Plugin/DailyNoteManager/daily-note-manager.js` confirms three higher-order
memory operations:

- `list`: reads diary files in a folder/date range and returns full content
- `organize`: creates a new organized diary, then moves source files to
  `已整理`
- `associate`: uses AssociativeDiscovery to find semantically related diary
  files with optional folder range, score threshold, and TagMemo boost

Boundary:

```text
DailyNote create/update = formal memory write
DailyNote local file conversion = local file read + public served copy write
DailyNote TagMaster = provider-backed tag generation
DailyNoteManager list = private memory read unless folder is classified
DailyNoteManager organize = memory write + archive/move
DailyNoteManager associate = memory search over indexed diary corpus
```

`Plugin/VCPForum/VCPForum.js`, `routes/forumApi.js`, and
`Plugin/VCPTaskAssistant/lib/forum-engine.js` confirm that `dailynote/VCP论坛`
is a file-backed Agent social space:

- posts are Markdown files named by board/title/author/timestamp/UID
- replies append structured floors to the same file
- Admin/API routes can list, read, reply, edit, and delete posts/floors
- locking, input limits, UID validation, symlink checks, max file size, and
  floor limits are present in the API route
- the Agent tool can read posts and convert HTTP images to base64 for AI
- TaskAssistant forum patrol samples forum posts and dispatches Agents

AGENTS OS interpretation:

```text
DailyNote = memory write organ
DailyNoteManager = memory maintenance / archive organ
VCPForum = Agent social memory surface
Forum patrol = scheduled Agent social activity
```

These surfaces should be integrated through an AGENTS OS memory-surface gate,
not treated as ordinary docs.

### Action Organs: File, Shell, Browser

`Plugin/FileOperator/FileOperator.js` confirms that FileOperator is the broad
filesystem action organ. It supports reading, writing, appending, editing,
diff-apply, copying, moving, renaming, deleting, listing, searching,
downloading, canvas creation, and history updates.

Important source-backed details:

- `ALLOWED_DIRECTORIES` can constrain operations, but if it is empty the plugin
  allows all paths.
- when `ALLOWED_DIRECTORIES` is set, `ReadFile` and `FileInfo` still have a
  read-only absolute-path bypass.
- write-like operations check `isPathAllowed`.
- `WriteFile` avoids overwriting by choosing a unique path.
- `EditFile`, `ApplyDiff`, `MoveFile`, `DeleteFile`, and `UpdateHistory` are
  direct mutation surfaces.

`Plugin/LinuxShellExecutor/LinuxShellExecutor.js` confirms a full command
execution organ:

- local and SSH execution
- whitelist, graylist, blacklist, security-level, AST, sandbox, resource-limit,
  and audit layers
- default-template `hosts.json` disables SSH and keeps local-only execution
- detects `sudo`, `su`, `pkexec`, and `doas` before execution
- supports long-running/background commands and log monitor handoff
- supports admin auth-code bypass for unknown/execute commands after checks

`Plugin/ChromeBridge/README.md` and manifest text confirm the browser action
organ:

- live page observation
- open URL, click, type, scroll, query HTML/JS, list/switch/close tabs
- CDP operations including runtime evaluate, DOM queries, network logs,
  response body read, extra headers, user-agent/timezone/locale/device
  overrides, cookies read, and site-data clearing

Boundary:

```text
FileOperator = filesystem action organ
LinuxShellExecutor = command/SSH action organ
ChromeBridge = browser observation/control organ
```

These are not safe autonomous defaults for AGENTS OS. They are powerful
execution organs that require a policy bridge from AGENTS OS red/yellow/green
rules into VCP tool approval, local allowlists, and explicit Jenn gates.

### Bridges, Distributed Tools, And External Export

`WebSocketServer.js` confirms distributed runtime support:

- authenticated WebSocket client types include `VCPLog`, `VCPInfo`,
  `DistributedServer`, `ChromeObserver`, `ChromeControl`, and `AdminPanel`
- distributed servers can register tools
- distributed tool execution sends `execute_tool` to a remote server and waits
  for `tool_result`
- distributed callbacks are persisted under `VCPAsyncResults`
- distributed servers can report IPs and static placeholders
- `FileFetcherServer` can map request IPs back to distributed servers for
  remote file retrieval

`Plugin/VCPToolBridge/index.js` confirms an external tool-export bridge:

- when enabled, it monkey-patches WebSocketServer's distributed-message handler
- exports local VCP tool manifests to external clients
- allows external clients to request `execute_vcp_tool`
- calls `pluginManager.processToolCall(toolName, toolArgs)`
- forwards async status/result events back to the external client

`Plugin/VCPBridgeServer/bridgeserver.js` confirms a separate CLI/provider
bridge:

- runs an independent API proxy server
- supports OpenAI Chat, OpenAI Responses, Anthropic Messages, and Gemini style
  endpoints
- can replace/prepend/append/merge system prompts
- can remap models
- supports multi-profile selection by URL path, header, or model prefix
- hot-reloads bridge config and profiles
- by default can forward to the local VCP main server

AGENTS OS interpretation:

```text
WebSocket distributed tools = remote body extension
VCPToolBridge = exporting VCP organs to external runtimes
VCPBridgeServer = rewriting external model/provider entrypoints
```

These bridges sit at the boundary between AGENTS OS, local runtime, browser,
distributed machines, and provider-facing clients. They should be treated as
runtime/provider configuration surfaces, not ordinary plugins.

## Integration Meaning For AGENTS OS

VCPToolBox dailynote shows that VCP Agents can carry operational handbooks
inside memory surfaces. This is important for AGENTS OS:

```text
AGENTS OS should not only govern code and config.
It must also govern which runtime memory surfaces are allowed to instruct future Agent action.
```

The same dailynote root can contain:

- technical manuals that may safely guide behavior
- sample diary entries
- Agent cognitive-route libraries
- private diary or still-unclassified memory surfaces
- future task or memory content that can influence Agents

Therefore AGENTS OS needs a dailynote classification gate before allowing
VCPToolBox memory content to affect Nobao, Machine, Task Producer, or runtime
actions.

## Safe Future Route

Recommended next route:

1. Build a dailynote classifier map:
   - technical manual
   - public sample
   - private diary
   - Agent cognitive-route library
   - runtime-generated memory
   - unknown
2. Read and summarize technical manual/public sample/cognitive-route-library
   classes when they are relevant and classified.
3. Require explicit file-level or directory-level reclassification before
   reading private diary or unknown raw content.
4. Translate cognitive-route libraries into AGENTS OS route cards before using
   them as operational behavior.
5. When VCPToolBox becomes an AGENTS OS body, route memory ingestion through
   a reviewable memory-surface gate rather than direct free reading.

## Current Judgment

VCPToolBox documentation confirms the body model:

```text
docs and README = body blueprint
plugin manifests = muscle registry
AdminPanel docs = owner console manual
dailynote technical docs = learned body operation memory
dailynote cognitive clusters = Agent thought-route library
dailynote diary/unknown areas = classified before use
```

AGENTS OS should absorb the body blueprint, operation manuals, and cognitive
route library, but should keep diary/unknown memory surfaces behind a
classification gate.

## Current Integration Hypothesis

VCPToolBox already contains five body subsystems that AGENTS OS can integrate
with over time:

1. Agent role packages: embodied personas and specialized background Agents.
2. Plugin organs: manifest-driven local, async, multimodal, and admin-gated
   tool execution.
3. Memory body: hot diary memory, cold knowledge, timeline, tags, and recall
   engines.
4. Cognitive route library: thought clusters that define how Agents should
   intake, reason, reflect, decide, and present.
5. Dispatch nerves: AA/FA task routing, ContextBridge, semantic model router,
   forum/task schedules, and WebSocket/tool approval channels.

The main AGENTS OS work is therefore not to invent a body from zero. It is to
govern VCPToolBox's existing body so that Nobao, Machine, Task Producer, and
future runtime Agents can use it without losing boundaries, provenance, or
reviewability.
