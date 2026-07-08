# AGENTS OS VCPToolBox Body Understanding v0.1

Date: 2026-07-07

Owner: Jenn

Agent steward: Nobao

Status: accepted local understanding report

Scope: record Nobao's source-level understanding of VCPToolBox as the AGENTS OS runtime body

## Scope

This report records a read-only source and documentation review of
`runtime/VCPToolBox` after Jenn clarified that VCPToolBox should be understood
as the body of AGENTS OS, not merely as an external toolbox or dependency.

The review covered:

- root and nested `AGENTS.md` boundaries in `runtime/VCPToolBox`
- `server.js`, `Plugin.js`, `WebSocketServer.js`, and `KnowledgeBaseManager.js`
- `modules/chatCompletionHandler.js`, `modules/messageProcessor.js`, model
  routing, VCP loop, tool parser, tool executor, and final context store
- `routes/taskScheduler.js`, `routes/protocolBridge.js`,
  `routes/specialModelRouter.js`, and selected `routes/admin/` control routes
- Agent role files in `Agent/`
- memory, agent, task, bridge, tavern, persona, shell, file, and code-worker
  plugin source or manifest metadata
- existing VCPToolBox reports and integration contract under
  `control-plane/registry/reports/`

## Explicit Non-Actions

- No VCPToolBox service was started.
- No `server.js`, `adminServer.js`, `Plugin.js`, plugin, executor, build, test,
  provider, or browser command was run.
- No plugin was enabled.
- No provider call was made.
- No active `config.env`, `.env`, credential, token, cookie, private memory,
  provider raw response, or raw log content was read or output.
- No `state-private/` content was read.
- No VCPToolBox source, runtime config, plugin manifest, runtime state, or
  formal AGENTS OS Memory content was modified.

## Core Correction

The correct AGENTS OS framing is:

```text
AGENTS_OS=spirit/control_plane/meaning_and_governance
VCPToolBox=body/runtime/organs/actions/memory_interfaces
```

VCPToolBox is not a small tool adapter. It is a local agent runtime body with
its own reflexes, memory surfaces, model routing, protocol bridges, admin
control plane, plugin muscles, WebSocket senses, task scheduler, and multi-Agent
identity layer.

The useful question is therefore not "should AGENTS OS deploy VCPToolBox as a
dependency?" The useful question is:

```text
how_should_AGENTS_OS_govern_this_body_so_it_can_move_without_becoming_ungoverned
```

## Body Map

### Spine

`server.js` is the runtime spine. It loads environment configuration, mounts
routes, installs authentication, initializes managers, loads plugins, starts the
main HTTP server, then connects WebSocket and file-fetcher surfaces.

The startup chain is not just server boot. It establishes the body order:

```text
config -> agents/toolboxes/TVS/SAR -> model/router state -> knowledge base ->
plugin manager -> static/service plugins -> task scheduler -> WebSocket/log
surface
```

### Brainstem

`modules/chatCompletionHandler.js` is the central brainstem. It takes incoming
chat requests and turns them into the final model-facing context:

- applies model redirect and semantic model routing
- handles VCP tool forbidden flags
- runs `VCPTavern` before variable expansion
- resolves Agent, Toolbox, TVS, SAR, static plugin, dynamic tool, and media
  placeholders
- runs message preprocessors
- records final context snapshots
- forwards to upstream provider
- hands responses to stream or non-stream VCP loop handlers

This means VCPToolBox participates in what the model sees before the provider
call. It is not only an after-the-fact tool executor.

### Reflex Arc

The VCP tool mechanism is a custom protocol, not OpenAI function calling.

The model emits blocks shaped like:

```text
<<<[TOOL_REQUEST]>>>
tool_name: ...
...
<<<[END_TOOL_REQUEST]>>>
```

`toolCallParser` parses those blocks, `toolExecutor` resolves `river`, `vref`,
`timely_contact`, tool password, and plugin routing, and the stream/non-stream
handlers feed a `VCP_TOOL_PAYLOAD` back into the model loop.

This is a real reflex arc:

```text
model output -> tool parse -> plugin execution -> tool payload -> model loop
```

The loop has bounded iterations, but once relevant plugins are enabled the loop
can cause real filesystem, process, browser, network, memory, and task effects.

### Memory And Nervous System

VCPToolBox contains several memory organs:

- `KnowledgeBaseManager` watches DailyNote roots, builds SQLite/vector/Rust
  indexes, embeds chunks, tags content, and performs semantic search.
- `RAGDiaryPlugin` injects diary and knowledge context, manages embedding
  caches, FoldingStore, tag boost, geodesic search, AIMemo, and metadata chains.
- `LightMemo` provides hybrid memory and knowledge retrieval.
- `DailyNote` and `DailyNoteManager` create, update, organize, and associate
  diary files.
- `OneRing` records and optionally injects cross-frontend per-Agent continuity.
- `ContextFoldingV2` uses stored vectors and summaries to fold low-relevance
  assistant history.
- `finalContextStore` keeps the latest assembled final contexts for AdminPanel
  inspection.

These are not ordinary logs. They are persistent or semi-persistent memory
interfaces and must be governed as memory surfaces.

### Agent Layer

The `Agent/` files are not decorative prompt skins. They define identity,
memory binding, tool access, role behavior, and relation to the VCP body.

Observed roles include:

- Nova as a main/home Agent with broad multimodal, memory, search, file,
  contact, and media capabilities.
- Weiming as a research/analysis Agent.
- MemoMaster as a memory custodian.
- Metis as a cognitive architecture and semantic-cluster advisor.
- Aemeath and Hornet as embodied character agents.
- ThemeMaidCoco as theme and visual maker.
- DreamNova as dream-state Agent.

`AgentAssistant` then turns Agents into communicable actors: it supports
session history, direct agent contact, async delegation, timed contact,
heartbeat, cancellation, callback, archival report, and score updates.

### Task And Future-Wakeup Layer

`VCPTaskAssistant` and `routes/taskScheduler.js` let the system schedule future
tool calls. The scheduler watches `VCPTimedContacts`, executes stored tool calls
through `pluginManager.processToolCall`, writes results under
`VCPTimedResults`, and broadcasts status.

This means VCPToolBox can be awakened by files and timers, not only by live user
requests. AGENTS OS must treat scheduled tasks as body movement.

### Senses And Bridges

The body has multiple sensory and bridge surfaces:

- `/v1/chat/completions`
- `/v1/chatvcp/completions`
- `/v1/responses`
- `/v1/messages`
- Gemini-compatible generate routes
- WebSocket clients for VCPLog, VCPInfo, distributed servers, Chrome observer,
  Chrome control, and AdminPanel
- `VCPBridgeServer` as an optional prompt-hijack/protocol proxy with profiles

VCPToolBox can therefore sit between many clients and providers, not just
between AGENTS OS and one local API.

### Admin Cortex

AdminPanel is a high-trust owner console. It can:

- read and write main runtime config
- read and write plugin config
- toggle plugin manifests
- edit plugin descriptions and tool list behavior
- update dynamic tool config
- trigger RAG training
- manage agents, TVS, schedules, bridge profiles, OneRing config, and plugin
  store operations
- restart the server

AdminPanel should be treated as a surgical control surface for the body, not as
ordinary UI.

### Plugin Muscles

The plugin inventory currently shows:

```text
total_plugin_manifests=83
enabled_plugin_manifests=0
blocked_plugin_manifests=83
synchronous=41
hybridservice=17
static=13
service=6
messagePreprocessor=4
asynchronous=2
```

High-impact blocked organs include:

- `LinuxShellExecutor`
- `ServerPowerShellExecutor`
- `FileOperator` / `ServerFileOperator`
- `AICodeWorker`
- `ChromeBridge`
- `SSHManagerService`
- `PluginManager`
- `VCPBridgeServer`
- `AgentAssistant`
- `VCPTaskAssistant`
- `RAGDiaryPlugin`
- `LightMemo`
- `DailyNote`
- `DailyNoteManager`
- `OneRing`
- `ContextFoldingV2`
- `OpenHerPersona`
- `VCPTavern`

The current all-blocked posture is a useful safe default. The future work is
not bulk enablement; it is organ-by-organ activation.

## AGENTS OS Integration Meaning

VCPToolBox gives AGENTS OS a local body with:

- action
- perception
- memory
- interface bridges
- agent ecology
- runtime UI
- tool muscles
- task reflexes

AGENTS OS gives VCPToolBox:

- purpose
- governance
- task selection
- boundary control
- evidence
- review
- long-term construction direction

The integration target is:

```text
AGENTS_OS_decides_what_should_happen
VCPToolBox_provides_the_body_that_can_make_it_happen
```

The failure mode to avoid is:

```text
VCPToolBox_moves_before_AGENTS_OS_has_decided_and_bounded_the_movement
```

## Current Local Posture

Current verified source-level posture:

```text
runtime_path=runtime/VCPToolBox
source_checkout_present=true
plugin_manifests_total=83
plugin_manifests_enabled=0
plugin_manifests_blocked=83
service_started_in_this_review=false
provider_call_performed=false
plugin_execution_performed=false
active_config_values_read=false
state_private_read=false
```

Prior local reports record that source deployment, dependency/build work, and
no-plugin localhost smoke gates have already been explored. This report does
not replace those reports. It updates Nobao's mental model of what VCPToolBox
is.

## Governance Consequences

### Treat VCPToolBox As A Runtime Body

Runtime work should use body vocabulary:

```text
spine=startup_chain
brainstem=context_and_model_pipeline
nerves=memory_and_context
muscles=plugins
senses=HTTP_WebSocket_bridge_surfaces
reflexes=tool_loop_and_scheduler
cortex=AdminPanel
identity_layer=Agent_files_and_AgentAssistant
```

This vocabulary helps prevent treating high-impact plugin enablement as a
small dependency toggle.

### Keep The First Living Path Narrow

The next runtime activation path should stay narrow:

```text
localhost_only=true
plugins_enabled=0_by_default
provider_backed_use=false_by_default
admin_panel=owner_console_only
memory_write=false_until_explicit_memory_gate
scheduled_task_execution=false_until_task_gate
```

### Activate Organs One By One

Recommended activation order:

1. Spine: main/admin localhost start and stop are stable.
2. Cortex: AdminPanel reachable only as local owner console.
3. Brainstem: no-plugin context path understood and observable.
4. Memory read surfaces: RAG/LightMemo/DailyNote read posture.
5. Memory write surfaces: DailyNote/OneRing writes under explicit policy.
6. Agent communication: AgentAssistant without shell/file/browser muscles.
7. Low-risk tools: read-only local helpers first.
8. High-risk muscles: File/Shell/AICodeWorker/browser/SSH only after separate
   gates.

### Do Not Confuse Provider Calls With Body Startup

VCPToolBox can start without proving provider-backed usefulness. Provider use is
a separate boundary because it can spend quota, send context outward, and turn
local memory or tool results into upstream payloads.

## Open Questions

- Which Agent should be AGENTS OS's first primary runtime identity inside
  VCPToolBox: Nova, Nobao-specific Agent, or a new AGENTS OS executor Agent?
- Should OneRing become the continuity layer for AGENTS OS Agents, or remain
  VCP-native until a formal Memory bridge exists?
- Should DailyNote become AGENTS OS formal memory, or remain a local runtime
  memory substrate under separate governance?
- Which first tool muscle is valuable enough to enable: read-only file view,
  LightMemo, AgentAssistant, or VCPBridgeServer?
- Should AdminPanel be used by Nobao operationally, or only by Jenn as owner
  console?

## Working Conclusion

VCPToolBox is suitable as AGENTS OS's body, but only if AGENTS OS treats it as a
body with organs, reflexes, and memory, not as a flat list of tools.

The next useful work is not broad deployment. The next useful work is a narrow
body activation route that keeps the current all-plugin-disabled safety posture
while proving the spine, cortex, and brainstem can be observed and controlled.
