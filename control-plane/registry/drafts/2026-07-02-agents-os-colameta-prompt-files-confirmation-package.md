# AGENTS OS ColaMeta Prompt Files Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for generating the seven
workspace-local ColaMeta Runner prompt files required by the Document
Governance 9.5 Runner plan.

This package is not execution authorization by itself. It is the narrow scope
confirmation material for creating prompt files only.

## Current Facts

Workspace-local Runner state exists:

```text
/home/jenn/AGENTS_OS_Workspace/.colameta/plan.json
/home/jenn/AGENTS_OS_Workspace/.colameta/state.json
/home/jenn/AGENTS_OS_Workspace/.colameta/todolist.json
/home/jenn/AGENTS_OS_Workspace/.colameta/decisions.json
/home/jenn/AGENTS_OS_Workspace/.colameta/memory.md
```

Prompt directory state:

```text
/home/jenn/AGENTS_OS_Workspace/.colameta/prompts/ exists
/home/jenn/AGENTS_OS_Workspace/.colameta/prompts/ contains no prompt files
```

Runner plan prompt targets:

```text
.colameta/prompts/dg95-stage-0.md
.colameta/prompts/dg95-stage-1.md
.colameta/prompts/dg95-stage-2.md
.colameta/prompts/dg95-stage-3.md
.colameta/prompts/dg95-stage-4.md
.colameta/prompts/dg95-stage-5.md
.colameta/prompts/dg95-stage-6.md
```

Previous non-blocking ColaMeta import-preview warnings:

```text
prompt_file_missing_on_disk_at_1
prompt_file_missing_on_disk_at_2
prompt_file_missing_on_disk_at_3
prompt_file_missing_on_disk_at_4
prompt_file_missing_on_disk_at_5
prompt_file_missing_on_disk_at_6
prompt_file_missing_on_disk_at_7
```

ColaMeta connector status from the latest connector-only test:

```text
HTTP 401
code: token_expired
```

The prompt files are still absent even though the current local
PlanLoader/Linter check passes. The connector state is acknowledged and is not
required for this local prompt file step.

## What This Step Would Write

If Jenn confirms this package, expected writes are limited to:

```text
.colameta/prompts/dg95-stage-0.md
.colameta/prompts/dg95-stage-1.md
.colameta/prompts/dg95-stage-2.md
.colameta/prompts/dg95-stage-3.md
.colameta/prompts/dg95-stage-4.md
.colameta/prompts/dg95-stage-5.md
.colameta/prompts/dg95-stage-6.md
control-plane/registry/receipts/2026-07-02-yellow-agents-os-colameta-prompt-files-generation-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-agents-os-colameta-prompt-files-generation-v0.1.review.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

The registry writes are only to keep document governance validation clean after
the new receipt/review evidence files are created.

## Prompt File Content Boundary

Each prompt file should be a bounded task prompt for exactly one 9.5 stage.
Each prompt should include:

```text
stage objective
allowed local write scope
explicit forbidden actions
expected deliverables
validation commands
receipt/review evidence requirement
stop conditions
```

Prompt files must not contain:

```text
secrets / tokens / cookies / credentials
private raw memory
provider raw responses
auth or connector instructions
production deployment instructions
release or package publish instructions
commands that bypass Jenn confirmation
executor-run authorization
```

## What It Must Not Do

This step does not authorize:

```text
starting ColaMeta service
changing auth/token/cookie/session state
modifying provider or runtime configuration
running ColaMeta executor
making provider calls
modifying /home/jenn/.config/colameta/project-registry.json
modifying WORKSPACE_REGISTRY.yaml
writing formal AGENTS OS Memory content
reading state-private/
reading or exposing logs/token/config raw content
external writes
commit / push / tag
release / deploy / publish
Delivery State accepted
ReviewDecision
GateEvent
bulk move / delete / rename
```

## Preflight Before Prompt Generation

Before generating prompt files, check:

```text
1. .colameta/plan.json still has seven enabled versions.
2. The seven prompt_file paths still point under .colameta/prompts/.
3. None of the target prompt files already exists unless Jenn confirms overwrite handling.
4. .colameta/memory.md is still empty.
5. No executor has run.
6. The connector token_expired state is acknowledged but not used.
```

If any preflight check differs from this package, stop and prepare a revised
confirmation package.

## Rollback Boundary

Rollback is a separate local write action. Do not run it unless Jenn confirms
rollback after seeing the actual prompt generation result.

Expected rollback scope if the prompt generation step created only expected
files:

```text
remove .colameta/prompts/dg95-stage-0.md
remove .colameta/prompts/dg95-stage-1.md
remove .colameta/prompts/dg95-stage-2.md
remove .colameta/prompts/dg95-stage-3.md
remove .colameta/prompts/dg95-stage-4.md
remove .colameta/prompts/dg95-stage-5.md
remove .colameta/prompts/dg95-stage-6.md
remove the prompt generation receipt/review registry entries
```

Rollback must not:

```text
delete .colameta/plan.json
delete .colameta/state.json
delete .colameta/memory.md
use git reset --hard
use git clean -fd
touch state-private/
touch WORKSPACE_REGISTRY.yaml
touch /home/jenn/.config/colameta/project-registry.json
touch external systems
```

## Validation After Prompt Generation

After confirmed prompt generation, run:

```text
PYTHONPATH=/home/jenn/tools/colameta python3 -c "import json; from runner.plan_loader import PlanLoader; from runner.plan_standards_linter import PlanStandardsLinter; path='.colameta/plan.json'; data=json.load(open(path, encoding='utf-8')); lint=PlanStandardsLinter().lint_plan_data(data, project_root='/home/jenn/AGENTS_OS_Workspace'); plan=PlanLoader().load_plan(path); PlanLoader().validate_plan(plan); print('loader_valid=True versions={} lint_status={} blocking={} warnings={}'.format(len(plan.versions), lint.get('status'), lint.get('blocking_issue_count'), lint.get('warning_count')))"
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

Manual checks:

```text
all seven prompt files exist
ColaMeta prompt_file_missing_on_disk warnings are zero
.colameta/memory.md remains empty
no executor ran
no service was started
no auth/provider/runtime config changed
no external write happened
```

## Exact Confirmation Text

To execute prompt file generation, use this exact confirmation shape:

```text
确认执行 AGENTS OS ColaMeta prompt files generation v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace/.colameta/prompts/ 创建 7 个
workspace-local prompt files：
dg95-stage-0.md、dg95-stage-1.md、dg95-stage-2.md、dg95-stage-3.md、
dg95-stage-4.md、dg95-stage-5.md、dg95-stage-6.md。

允许为这次 prompt generation 写入对应 receipt/review evidence，并只为保持
docctl doctor clean 而更新 document registry 和 federated document registry。

不启动服务、不改 auth/token/cookie/session、不改 provider/runtime 配置、
不跑 executor、不做 provider 调用、不修改 /home/jenn/.config/colameta/project-registry.json、
不改 WORKSPACE_REGISTRY.yaml、不写正式 AGENTS OS Memory 内容、不读 state-private/、
不读或输出 logs/token/config raw content、不做外部写入、不 commit/push/tag、
不发布、不部署、不做 bulk move/delete/rename。
```

Until Jenn confirms this exact execution scope, the seven prompt files remain
missing and no executor workflow may run.
