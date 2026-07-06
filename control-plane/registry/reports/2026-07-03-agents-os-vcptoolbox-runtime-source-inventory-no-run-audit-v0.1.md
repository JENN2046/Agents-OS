# AGENTS OS VCPToolBox runtime source inventory / no-run audit v0.1

Date: 2026-07-03
Status: accepted
Scope: no-run inventory of VCPToolBox runtime source entrypoints, configuration surface, plugin surface, and future startup gate.

## Boundary

This audit was source-only and no-run. It did not start VCPToolBox, run
`server.js`, run `adminServer.js`, run `Plugin.js`, execute routes/modules,
install dependencies, run build scripts, run tests, call plugins, call
providers, read active secrets, read active `config.env`, read `state-private/`,
read raw logs, write formal Memory, modify runtime configuration, or perform
external writes.

Active env/config files were absent from the worktree:

```text
worktree_file_count=2821
active_env_count=0
active_config_env_count=0
secret_like_count=0
key_material_count=0
```

## Source Inventory

Repository source checkout:

```text
path=runtime/VCPToolBox
repo=https://github.com/lioensky/VCPToolBox
branch=main
head=49e72d92d29e48184b6a7e73098131cc416b53db
```

Important local instruction files:

```text
runtime/VCPToolBox/AGENTS.md
runtime/VCPToolBox/Plugin/AGENTS.md
runtime/VCPToolBox/modules/AGENTS.md
runtime/VCPToolBox/routes/AGENTS.md
runtime/VCPToolBox/rust-vexus-lite/AGENTS.md
```

Primary entrypoints observed:

```text
runtime/VCPToolBox/server.js
runtime/VCPToolBox/adminServer.js
runtime/VCPToolBox/Plugin.js
runtime/VCPToolBox/WebSocketServer.js
runtime/VCPToolBox/FileFetcherServer.js
runtime/VCPToolBox/KnowledgeBaseManager.js
```

Package script surface:

```text
runtime/VCPToolBox/package.json scripts=test,start,start:admin,start:all,build:admin
runtime/VCPToolBox/AdminPanel-Vue/package.json scripts=dev,build,build:no-type-check,preview,test,test:watch,lint,lint:typography,lint:fix
runtime/VCPToolBox/rust-vexus-lite/package.json scripts=build,build:debug,artifacts
```

No package script was executed during this audit.

## Entrypoint Surface

`server.js` is the main runtime entrypoint. Static source inspection shows:

- Loads environment from `config.env`.
- Creates an Express app and mounts special model, admin, protocol bridge, chat, tool, callback, and forum routes.
- Requires configured main API values before useful runtime behavior.
- Authenticates non-admin API paths with bearer-style runtime key handling.
- Protects `/admin_api` and `/AdminPanel` through admin auth.
- Initializes knowledge managers before loading plugins.
- Loads plugins through `PluginManager.loadPlugins()`.
- Initializes service plugins and mounts namespaced plugin routes under `/api/plugins/<name>`.
- Initializes static plugins and prewarms Python plugins before accepting traffic.
- Starts HTTP listener only after startup initialization completes.
- Initializes WebSocket and file fetcher services after `app.listen`.

`adminServer.js` is a separate admin-panel process. Static source inspection shows:

- Loads environment from `config.env`.
- Starts on `PORT + 1`.
- Serves AdminPanel assets.
- Protects admin routes with admin auth.
- Proxies or handles selected `/admin_api` routes.
- Includes routes for config/file/RAG/toolbox/agent/TVS/schedule/cache/log/admin operations.
- Forwards selected restart and training requests to the main process.

`Plugin.js` is the plugin lifecycle controller. Static source inspection shows:

- Discovers plugin folders by manifest.
- Reads plugin-specific `config.env` at runtime if present.
- Loads direct service/preprocessor modules with `require()`.
- Initializes direct modules and injects runtime dependencies.
- Executes stdio plugins by building an environment and spawning the configured entrypoint at runtime.
- Can inject additional runtime-only auth, image/file service, SSH manager, log monitor, and async callback environment variables.
- Mounts service plugin API routes under `/api/plugins/<pluginName>` when declared.

## Configuration Surface

Configuration is template-only in the source checkout. Active config was not
landed.

Template inventory:

```text
root_config_template=runtime/VCPToolBox/config.env.example
root_config_key_count=173
tag_processor_config_template=runtime/VCPToolBox/tag-processor-config.env.example
tag_processor_config_key_count=7
plugin_config_env_example_count=41
plugin_active_config_env_count=0
```

Observed configuration categories:

- Main upstream API endpoint and model/provider routing.
- Runtime ports, request retries, loop limits, and timezone.
- Admin username/password and panel behavior.
- API keys and runtime bearer keys.
- Image/file service keys.
- Role divider, detector, and placeholder behavior.
- Chat/debug logging behavior.
- NewAPI monitor settings.
- Multimodal and special model routing.
- Knowledge base, vector DB, Rust write lease, and TDB cold knowledge settings.
- Distributed music sync, callbacks, and plugin-specific settings.

Future startup must not create active `.env`, `config.env`, plugin
`config.env`, credentials, tokens, or cookies without a dedicated configuration
gate.

## Plugin Surface

Manifest inventory:

```text
manifest_count=83
manifest_parse_errors=0
enabled_plugin_count=63
blocked_plugin_count=20
plugin_type_counts=asynchronous:2, hybridservice:17, messagePreprocessor:4, service:6, static:13, synchronous:41
communication_counts=direct:27, process_stdio:1, stdio:54, unknown:1
entry_type_counts=command:1, executable:2, nodejs:53, python:4, unknown:23
```

Enabled plugin sample includes:

```text
AICodeWorker, AgentAssistant, AgentMessage, AgnesGen, AgnesVideoGen, AnySearch,
ArtistMatcher, BilibiliFetch, CapturePreprocessor, ChromeBridge,
ServerCodeSearcher, ContextFoldingV2, DailyNoteManager, ImageServer,
LinuxShellExecutor, PluginManager, ServerPowerShellExecutor, RAGDiaryPlugin,
SkillBridge, TavilySearch, UserAuth, VCPBridgeServer, VCPLog, VCPToolBridge,
VSearch
```

Risk-relevant plugin classes:

- `stdio` plugins can spawn child processes at runtime.
- `direct` service/hybrid/messagePreprocessor plugins can be required and initialized during startup.
- `service` and `hybridservice` plugins may mount API routes.
- Python plugins are prewarmed during startup.
- Shell executor plugins exist in the enabled set and must be gated before runtime execution.
- Search, browser, image/video generation, monitor, SSH, and bridge plugins imply external, local system, or provider/tool boundaries.

## Route And Write Surface

Route declaration inventory:

```text
route_verb_counts=DELETE:9, GET:84, PATCH:2, POST:75, PUT:5
admin_route_modules=29
public_route_modules=5
```

Important route families:

- `/v1/chat/completions`, `/v1/chatvcp/completions`, protocol bridge, and special model forwarding.
- `/v1/models`, `/v1/schedule_task`, `/v1/interrupt`, `/v1/human/tool`.
- `/plugin-callback/:pluginName/:taskId`.
- `/admin_api/*` for config, plugin, RAG, toolbox, agents, TVS, schedules, cache, logs, system, semantic router, and server controls.
- `/api/plugins/<pluginName>` for service plugin routes.

Static source scan found runtime write and process-control surfaces:

- Runtime directory creation and JSON writes for Agent, TVS, blacklist, async results, timed contacts, and chat logs.
- Admin routes that write config, plugin manifests/config, schedules, cache, RAG/theme/config, agents, toolbox, TVS, final context, and media/emoji data.
- Admin plugin store paths that can download/extract/install plugins and run dependency installation.
- Restart paths that can call `process.exit`.
- External HTTP/fetch paths for upstream model APIs, NewAPI monitor, special model routing, protocol bridge, and admin AI chat.

These are not problems by themselves, but they mean startup must be treated as
runtime execution, not as ordinary source inspection.

## Future Startup Gate

Before any VCPToolBox service start, require a dedicated confirmation package
and a gate with these minimum checks:

1. Scope gate
   - Exact command to run.
   - Exact working directory.
   - Exact ports.
   - No `start:all` unless both main and admin process are explicitly authorized.

2. Config gate
   - Explicit permission to create active config files.
   - Active config generated from templates, not copied from private state.
   - No secret value displayed in chat, logs, receipts, or reviews.
   - Provider/API keys and admin credentials handled through a separate secret-safe flow.

3. Dependency gate
   - Explicit permission before `npm install`, Python install, Rust/N-API build, Docker build, or plugin dependency install.
   - No package publish, release, deploy, or external service write.

4. Plugin gate
   - Initial run should disable or block shell/system executor, plugin store install, SSH/log monitor, browser bridge, provider-heavy image/video/search plugins unless separately approved.
   - Service plugin API route mounting must be inventoried before exposure.
   - Stdio/direct plugin execution must be treated as runtime execution.

5. Network/provider gate
   - No provider call during startup unless a specific provider-call trial is approved.
   - Any external HTTP route must remain untriggered during startup smoke unless explicitly tested.

6. Data/write gate
   - Startup write directories must be listed and constrained.
   - No writes to `state-private/`.
   - No formal AGENTS OS Memory writes.
   - No raw log harvesting or provider raw response collection.

7. Validation gate
   - First allowed startup should be localhost-only and time-boxed.
   - Capture sanitized health summary only.
   - Stop process after smoke if authorized.
   - Write receipt/review evidence with no raw secrets, tokens, cookies, provider raw responses, or private memory.

## Go / No-Go

Current status:

```text
source_inventory_done=True
runtime_start_ready=False
config_gate_required=True
dependency_gate_required=True
plugin_gate_required=True
provider_gate_required=True
memory_gate_required=True
```

Recommendation:

```text
Next safe step: prepare AGENTS OS VCPToolBox startup preflight gate v0.1 confirmation package.
Do not start VCPToolBox yet.
Do not install dependencies yet.
Do not create active config yet.
```

## Validation

```text
nested_agents_files=5
package_metadata_read=True
package_scripts_executed=0
entrypoint_files_observed=6
plugin_manifest_count=83
plugin_manifest_parse_errors=0
enabled_plugin_count=63
blocked_plugin_count=20
plugin_active_config_env_count=0
plugin_config_env_example_count=41
route_verb_counts=DELETE:9,GET:84,PATCH:2,POST:75,PUT:5
active_env_count=0
active_config_env_count=0
secret_like_count=0
key_material_count=0
validate-document-registry PASS documents=152 pass=152 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=194 scanned_files=241 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
```
