# AGENTS OS VCPToolBox plugin startup posture preview v0.1

Date: 2026-07-03
Status: completed_no_run
Scope: preview-only plugin posture for a future VCPToolBox first startup.

This report is a preview only. It does not modify `plugin-manifest.json`,
`plugin-manifest.json.block`, plugin config, active config, package files, or
runtime state. It does not run plugins or start VCPToolBox.

## Authorization State

```text
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

## Inputs Reviewed

```text
source_remote=https://github.com/lioensky/VCPToolBox
source_branch=main
source_head=49e72d92d29e48184b6a7e73098131cc416b53db
source_git_status_clean=true
startup_preflight_gate=passed_no_run
tri_gate_preflight=passed_no_run
first_start_posture=no_start_until_three_followup_plans
```

Only plugin manifest metadata was reviewed. No plugin manifest was modified,
no plugin entrypoint was executed, and no provider call was performed.

## Tri-Gate Baseline

```text
plugin_records=83
plugin_manifest_parse_errors=0
posture_counts=block_for_first_startup:28,candidate_allow_no_provider:22,keep_blocked:20,review_before_allow:13
risk_counts=bridge_or_browser:6,external_or_provider_capable:24,lower_initial_risk:1,runtime_child_process:55,startup_loaded_direct:27,system_or_plugin_admin:6
```

Followup file-level preview observed 84 manifest files. The tri-gate record
count remains the baseline for this planning package; the file-level preview is
used only to shape the future review route.

## First-Startup Preview Posture

First startup should not run with the current enabled plugin surface.

```text
plugin_startup_ready=false
plugin_manifest_write_authorized=false
plugin_execution_authorized=false
service_start_authorized=false
provider_call_authorized=false
```

### Keep Blocked

Already-blocked plugins should remain blocked for first startup.

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

### Block For First Startup

Enabled high-risk plugins should be temporarily blocked before a future first
startup, but no manifest change is authorized by this preview.

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

### Review Before Allow

The following plugin names need manual review before they can be treated as
first-start candidates. This list is preview-only and may need adjustment after
manifest-by-manifest review.

```text
DailyNoteManager
ForumLister
PluginManager
ScheduleManager
ThoughtClusterManager
VCPForum
```

### Candidate Allow, No Provider

These names appear lower risk in the followup preview, but they are not
authorized to run. They remain candidates only after active config,
dependency/build, and plugin manifest gates are accepted.

```text
AICodeWorker
AgentAssistant
AgentMessage
ArtistMatcher
ContextFoldingV2
DMXDoubaoGen
DailyNote
DigitalOracle
DoubaoGen
EmojiListGenerator
FluxGen
LightMemo
MagiAgent
NanoBananaGen2
OneRing
OpenHerPersona
RAGDiaryPlugin
ScheduleBriefing
SciCalculator
SemanticGroupEditor
ServerFileOperator
ServerPluginSourceViewer
TarotDivination
TimedTaskQuery
UserAuth
VCPClawMail
VCPLog
VCPTaskAssistant
VCPTavern
```

Provider, browser bridge, shell/system, search/fetch, image/video generation,
forum/network, and plugin-management surfaces remain blocked until Jenn approves
an exact file-by-file manifest change package.

## Future Manifest Change Gate

Any future plugin posture change must be a separate confirmation package.

```text
required_inputs=accepted active config plan, accepted dependency/build plan, accepted plugin posture preview
required_operations=file-by-file manifest rename or edit list
required_rollback=file-by-file reverse operations
required_validation=manifest count, blocked/enabled count, docctl doctor, no service running
bulk_move_or_rename_authorized_now=false
plugin_manifest_write_authorized_now=false
```

## First-Start Plugin Posture

```text
plugin_startup_posture=not_ready
recommended_first_start=do_not_start
next_required_confirmation=plugin manifest change plan, if first startup remains desired
```

## Validation

```text
validation_status=passed
validate-document-registry PASS documents=172 pass=172 warn=0 fail=0
validate-federated-document-registry PASS registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=214 scanned_files=261 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
docctl status PASS score=100 eligible_95=True warn=0 fail=0
vcptoolbox_git_status_clean=True
active_config_created=false
dependency_install_performed=false
build_or_test_performed=false
plugin_manifest_modified=false
plugin_execution_performed=false
service_started=false
provider_call_performed=false
memory_write_performed=false
external_write_performed=false
```
