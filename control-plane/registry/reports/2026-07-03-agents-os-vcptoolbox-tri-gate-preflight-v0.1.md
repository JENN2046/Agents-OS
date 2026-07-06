# AGENTS OS VCPToolBox tri-gate preflight v0.1

Date: 2026-07-03
Status: passed_no_run
Scope: read-only preflight for VCPToolBox active config, dependency/build, and plugin-risk gates.

## Gate Result

```text
schema_version=agents-os.vcptoolbox.tri_gate_preflight.result.v0.1
passed=true
gate_status=passed_no_run
read_only=true
summary_only=true
active_config_write_authorized=false
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
```

Passing this preflight means the three gate surfaces are classified. It does not
authorize config creation, dependency install, plugin changes, plugin execution,
provider calls, Memory writes, or VCPToolBox startup.

## Source Baseline

```text
source_remote=https://github.com/lioensky/VCPToolBox
source_branch=main
source_head=49e72d92d29e48184b6a7e73098131cc416b53db
source_git_status_clean=true
worktree_file_count=2821
active_env_count=0
active_config_env_count=0
credential_file_count=0
key_material_count=0
```

## Gate A: Active Config

Template metadata:

```text
config.env.example_key_count=173
tag-processor-config.env.example_key_count=7
plugin_config_template_count=41
plugin_config_key_count=331
```

Heuristic key classification by key name:

```text
secret_like_key_count=60
url_or_port_key_count=32
path_or_file_key_count=25
model_or_embedding_key_count=55
feature_or_debug_key_count=33
other_key_count=280
```

High-confidence secret-bearing key names include:

```text
AdminPassword
AGNES_API_KEY
AGNES_VIDEO_API_KEY
ANYSEARCH_API_KEY
API_KEY
API_Key
BILIBILI_COOKIE
Bridge_Access_Token
BRIDGE_UPSTREAM_KEY
DEEPWIKI_GITHUB_TOKEN
DEEPWIKI_GITLAB_TOKEN
FETCH_COOKIES
FETCH_COOKIES_RAW
File_Key
FORUM_API_KEY
GeminiImageKey
Gotify_App_Token
Image_Key
JINA_API_KEY
Key
NEWAPI_MONITOR_ACCESS_TOKEN
OPENAI_API_KEY
OPENCODE_API_KEY
SILICONFLOW_API_KEY
TavilyKey
VCP_Key
VOLCENGINE_API_KEY
WeatherKey
ZIMAGE_API_KEY
```

Notes:

- The `secret_like` classifier intentionally overmatches names containing
  `TOKEN`, so fields such as `MaxTokens` require manual review.
- Active config creation remains blocked.
- Secret values must be supplied only through a future secret-safe flow and
  must not be printed in chat, reports, receipts, reviews, logs, or raw outputs.

Gate A result:

```text
active_config_ready=false
active_config_write_authorized=false
next_required_confirmation=active config plan with secret-safe value handling
```

## Gate B: Dependency / Build

Package metadata:

```text
node_package_count=10
root_node_dependency_count=53
lock_file_count=9
requirements_txt_count=6
cargo_toml_count=15
root_python_requirements_exists=true
rust_vexus_cargo_exists=true
```

Script class counts:

```text
runtime_start=4
install_or_build=6
test=4
other=11
```

Dependency/build surfaces observed:

```text
root package scripts include start/start:admin/start:all/build:admin/test
AdminPanel-Vue scripts include dev/build/preview/test/lint
rust-vexus-lite scripts include napi build
Python requirements exist at root and plugin paths
Cargo projects exist for rust-vexus-lite, CodeSearcher, DailyNoteSearcher, PaperReader, and installer source
```

Gate B result:

```text
dependency_build_ready=false
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
next_required_confirmation=dependency install/build plan with exact commands and expected writes
```

## Gate C: Plugin Risk

Manifest metadata:

```text
plugin_records=83
plugin_manifest_parse_errors=0
posture_counts=block_for_first_startup:28,candidate_allow_no_provider:22,keep_blocked:20,review_before_allow:13
risk_counts=bridge_or_browser:6,external_or_provider_capable:24,lower_initial_risk:1,runtime_child_process:55,startup_loaded_direct:27,system_or_plugin_admin:6
```

Recommended first-startup posture:

```text
block_for_first_startup=28
keep_blocked=20
review_before_allow=13
candidate_allow_no_provider=22
```

Enabled plugins recommended to block for first startup:

```text
AgnesGen
AgnesVideoGen
AnySearch
BilibiliFetch
ChromeBridge
ServerCodeSearcher
DailyNoteSearcher
DeepWikiVCP
DynamicToolBridge
FlashDeepSearch
GPTImageGen
GeminiImageGen
ImageServer
ImageProcessor
LinuxShellExecutor
PluginManager
ServerPowerShellExecutor
QwenImageGen
SkillBridge
TavilySearch
UrlFetch
VCPBridgeServer
ServerSearchController
VCPToolBridge
VSearch
Wan2.1VideoGen
WeatherReporter
ZImageTurboGen
```

Already-blocked plugins should remain blocked for first startup:

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

Gate C result:

```text
plugin_risk_ready=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
next_required_confirmation=plugin startup posture plan with exact manifest changes or no-change strategy
```

## Combined Conclusion

```text
runtime_start_ready=false
active_config_gate_passed_for_planning=true
dependency_build_gate_passed_for_planning=true
plugin_risk_gate_passed_for_planning=true
startup_authorized=false
next_required_confirmation=VCPToolBox first-start posture plan v0.1
```

Recommended next local step:

```text
Prepare AGENTS OS VCPToolBox first-start posture plan v0.1 confirmation package.
```

That plan should decide:

```text
whether to create a sanitized local config template plan without values
whether to install dependencies later and by which exact commands
whether plugin risk is handled by manifest changes, environment gates, or no-start policy
whether first startup should be main-only, admin-only, or still blocked
```

## Validation

```text
validate-document-registry PASS documents=164 pass=164 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=206 scanned_files=253 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_clean=True
active_config_write_authorized=false
dependency_install_authorized=false
build_authorized=false
test_execution_authorized=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
```
