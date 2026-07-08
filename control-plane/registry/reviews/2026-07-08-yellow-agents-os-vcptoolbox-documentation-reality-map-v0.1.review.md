# Review: AGENTS OS VCPToolBox Documentation Reality Map v0.1

Date: 2026-07-08

Zone: yellow

Owner: Jenn

Agent steward: Nobao

## Review Result

Accepted as a local documentation and source-backed runtime reality map.

The report gives AGENTS OS a practical classification layer for VCPToolBox
documentation, dailynote surfaces, and Agent cognitive-route libraries. It does
not authorize VCPToolBox service startup, plugin activation, provider-backed
use, AdminPanel operation, or unrestricted private memory reading.

## Boundary Review

Pass with one caution.

The report does not expose secrets, tokens, cookies, credentials, active runtime
configuration values, provider raw responses, raw logs, or `state-private/`
content.

Caution: one `ExampleMaid` sample diary file was opened to confirm dailynote
format. The content was treated as a format signal, not as AGENTS OS Memory or
runtime instruction. Future work should avoid opening diary-like files unless
they are explicitly reclassified as public research samples.

Jenn later clarified that `前思维簇`, `反思簇`, `逻辑推理簇`, and
`结果辩证簇` are designed Agent cognitive routes rather than private memory.
Reading those four directories is consistent with that current classification.
`Agent/Metis.txt` additionally classifies `陈词总结梳理簇` as part of the
formal thought-cluster structure, so reading it is consistent with the same
cognitive-route boundary.

## Technical Review

The map is consistent with inspected VCPToolBox documentation:

- `README.md`, `VCP.md`, `vcp白皮书V3.md`, and `TECHNICAL_LITE.md` define the
  runtime/body vision and technical map.
- `ARCHITECTURE.md`, `PLUGIN_ECOSYSTEM.md`, `API_ROUTES.md`,
  `CONFIGURATION.md`, and `OPERATIONS.md` provide source-adjacent runtime
  structure.
- `MEMORY_SYSTEM.md`, `TagMemo_Wave_Algorithm_Deep_Dive.md`, and TDB/SQLite
  reports show multiple documentation generations and must be reconciled with
  current source.
- `dailynote/VCP开发` and `dailynote/VCP桌面知识` function as Agent-facing
  operation manuals stored inside memory surfaces.
- `前思维簇`, `逻辑推理簇`, `反思簇`, and `结果辩证簇` form a coherent
  Agent cognition pipeline: intake and boundary-setting, reasoning and
  cross-fusion, reflection and confidence audit, final arbitration and
  recursion.
- `陈词总结梳理簇` completes that pipeline with final language shaping,
  presentation adaptation, cognitive-footprint metadata, final fact/value
  firewall review, and ethical/effectiveness calibration.
- `Agent/` files are role packages, not merely character skins. They bind
  persona, memory indexes, tool placeholders, output protocols, and diary rules.
- `AGENT_AND_TASK_SYSTEM_GUIDE.md` establishes a two-layer runtime split:
  AgentAssistant for identity/context and TaskAssistant for dispatch/schedules.
- plugin documents establish VCP's organ model: manifest-driven stdio plugins,
  async callback placeholders, dynamic prompt injection, admin gating, and
  AI-friendly multimodal `content` array results.
- memory and routing documents show hot memory, cold knowledge, ContextBridge,
  LightMemo routing, and semantic model routing as separate body subsystems.
- still-unclassified diary/test/generated-memory directories remain outside
  ordinary documentation until explicitly classified.

Additional source-backed review:

- `server.js` confirms VCPToolBox boots as a runtime body: memory managers,
  plugin manager, dynamic tool registry, Admin API, schedulers, semantic
  routing, WebSocket, and file fetcher are initialized as one system.
- `ChatCompletionHandler` confirms the safe governance insertion points:
  pre-variable, pre-upstream, pre-tool-execution, post-tool-result, and
  memory-write.
- `ToolCallParser`, `ToolExecutor`, `StreamHandler`, and `NonStreamHandler`
  confirm that VCP uses visible text protocol tool calls, context attachment,
  plugin execution, tool-result injection, and recursive model continuation.
- `Plugin.js` confirms that plugin execution is manifest-driven, approval-aware,
  and privacy-guarded, but also capable of spawning subprocesses and loading
  plugin-local runtime config.
- `RAGDiaryPlugin` confirms that hot memory is an associative cognition layer,
  combining direct diary text, vector RAG, hybrid gating, TDB placeholders,
  meta-thinking, AIMemo, TagMemo, BM25, time decay, rerank/RRF, parent-document
  expansion, and VCPInfo telemetry.
- `KnowledgeBaseManager` and `TDBKnowledge` confirm the split between hot
  `dailynote` memory and cold `knowledge` libraries, with different stores,
  indexing engines, watchers, and operational risks.
- `agentManager`, `AgentAssistant`, and `VCPTaskAssistant` confirm that VCP
  already has role package loading, Agent communication, async delegation, and a
  task producer/scheduler pattern.
- Admin routes confirm that the AdminPanel is a privileged owner console: it
  can read plugin config content for UI, write plugin `config.env`, toggle
  plugin manifests, edit Agent files, change task state, and modify runtime
  routing/tool configs.
- `WebSocketServer` confirms the nervous-system model: VCPLog, VCPInfo,
  DistributedServer, ChromeObserver, ChromeControl, AdminPanel, tool approval
  responses, and distributed tool callbacks share one live runtime channel.
- `OpenHerPersona` source confirms the current personality-axis plugin is a
  pure async observer: it updates local axis/audit state but does not mutate
  prompts, send proactive messages, or write long-term memory.
- `AgentDream` source confirms dream generation is provider-backed and writes
  reviewable dream operation logs; diary merge/delete/insight operations are
  represented as pending-review candidates.
- `OneRing` and `VCPTavern` confirm two different continuity layers:
  cross-frontend Agent timeline and session/time-context injection.
- `dynamicToolRegistry` confirms dynamic tool attention: catalog sync,
  classification cache, light-list plus expanded-description injection, and
  pure-local/provider-backed classification paths.
- `semanticModelRouter` confirms virtual auto-model routing through preset
  resolution, context embedding, route-description embedding, threshold match,
  and fallback candidate chains.
- `ContextFoldingV2` confirms opt-in long-context metabolism: relevance-based
  assistant-block folding, summary-cache use, provider-backed summary
  generation, and FoldingStore mutation.
- `ImageProcessor`, `multiModalConfigStore`, and `FileFetcherServer` confirm
  sensory and distributed-file organs: base64 image/audio/video translation,
  multimodal SQLite cache, hot multimodal config, distributed `file://` fetch,
  and `.file_cache` writes.
- `ToolApprovalManager`, `ToolResultPrivacyGuard`, `Plugin.js`, and VCP loop
  handlers confirm that approval, tool-result privacy sanitization, `river`,
  `vref`, and recursive `<!-- VCP_TOOL_PAYLOAD -->` reinjection already exist
  as runtime mechanisms.
- `AgentAssistant` confirms provider-backed Agent contact, future-contact
  scheduling, temporary/persistent sessions, river/multimodal forwarding,
  injected temporary tool groups, async delegation loops, async result
  persistence, and Agent scoring.
- `VCPTaskAssistant` confirms a standing task producer/scheduler body organ:
  task config in `task-center-data.json`, forum patrol/custom prompt task
  types, interval/once/manual/cron schedules, target Agents, runtime history,
  and dispatch through AgentAssistant.
- `DailyNote`, `DailyNoteManager`, `VCPForum`, and `forumApi` confirm that
  dailynote is not just stored documentation. It includes formal diary writes,
  memory organizing/archival moves, associative memory search, file-backed
  forum posts/replies, and Admin/API edit/delete paths.
- `FileOperator`, `LinuxShellExecutor`, and `ChromeBridge` confirm high-power
  action organs: filesystem mutation, local/SSH command execution, and browser
  observation/control including CDP-level operations.
- `WebSocketServer`, `VCPToolBridge`, and `VCPBridgeServer` confirm distributed
  and external bridge surfaces: remote tool registration/execution, local VCP
  tool export to external clients, and system-prompt/model-routing bridge
  behavior for external CLI/provider entrypoints.

## Residual Risk

- This is a read-only documentation map and does not prove runtime behavior.
- The new source-backed runtime map was produced by static reading, not by
  starting VCPToolBox, enabling plugins, invoking tools, or issuing provider
  calls.
- The dailynote classification is based on names, file metadata, selected
  technical reads, and direct reading of the four reclassified cognitive-route
  directories plus `陈词总结梳理簇`; it is not a complete semantic audit of all
  dailynote content.
- VCPToolBox active config and live service posture remain intentionally
  uninspected in this task.
- The deeper body-organ map remains static/source-backed only. It does not
  mean DynamicToolRegistry, SemanticModelRouter, ContextFoldingV2,
  ImageProcessor, FileFetcherServer, OneRing, AgentDream, or any plugin should
  be activated without a separate AGENTS OS gate.
- Several discovered organs have local mutation surfaces or provider-backed
  paths. Future integration must distinguish pure-local preview, local runtime
  mutation, distributed runtime action, plugin execution, and provider call.
- FileOperator, LinuxShellExecutor, ChromeBridge, VCPToolBridge, and
  VCPBridgeServer are especially sensitive. They should be assumed unsafe for
  unattended AGENTS OS use until a policy bridge maps AGENTS OS boundaries to
  VCP tool approval, plugin allowlists, and explicit Jenn gates.

## Required Next Use

Use this map before any future VCPToolBox memory integration work.

Future dailynote ingestion should start with a file-level classifier and only
promote technical manuals, classified cognitive-route libraries, or explicitly
reclassified samples into AGENTS OS usable knowledge.
