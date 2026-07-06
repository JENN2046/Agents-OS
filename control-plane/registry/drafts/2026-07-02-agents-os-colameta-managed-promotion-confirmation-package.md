# AGENTS OS ColaMeta Managed Promotion Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for moving AGENTS OS from ColaMeta
`source-only` to a narrow ColaMeta `managed` Runner project for the Document
Governance 9.5 route.

Jenn has confirmed the direction: AGENTS OS will enter managed promotion.

This package is still not execution authorization by itself. It is the final
scope confirmation material before writing `.colameta/` Runner state.

## Current Facts

ColaMeta registry:

```text
project_name: AGENTS_OS_Workspace
project_root: /home/jenn/AGENTS_OS_Workspace
project_mode: source-only
```

Stable ColaMeta service:

```text
stable runtime dir: /home/jenn/tools/colameta
stable Web: http://127.0.0.1:8801 healthy
stable MCP: http://127.0.0.1:8766/mcp healthy
external_connector: unverified
```

Current connector tool from this Codex session:

```text
HTTP 401
code: token_expired
```

AGENTS OS root:

```text
/home/jenn/AGENTS_OS_Workspace/.colameta does not exist
/home/jenn/AGENTS_OS_Workspace/.gitignore does not exist
/home/jenn/AGENTS_OS_Workspace is not a git repository
```

Prepared Runner plan draft:

```text
control-plane/registry/drafts/2026-07-02-document-governance-9.5-colameta-runner-plan.draft.json
ColaMeta PlanLoader/Linter: loader_valid=True versions=7 lint_status=passed blocking=0 warnings=0
```

## Decision Direction

Confirmed direction:

```text
Promote AGENTS_OS_Workspace to a narrow ColaMeta managed Runner project using
the already validated 9.5 Runner plan draft.
```

Remaining decision:

```text
Confirm the exact local write scope, timing, fallback path, rollback boundary,
and validation commands.
```

Do not use broad promotion:

```text
Do not run a broad automatic `colameta add ... managed` flow without reviewing
the files it creates.
```

## What Managed Promotion Would Write

If Jenn confirms the promotion, the expected local writes are limited to:

```text
.colameta/
.colameta/plan.json
.colameta/state.json
.colameta/todolist.json
.colameta/decisions.json
.colameta/memory.md
.colameta/prompts/
.colameta/runtime/
.colameta/runtime/plan-previews/
.colameta/logs/
.colameta/reports/
.colameta/audits/
.colameta/plan-patches/
.gitignore
```

Important note:

```text
.colameta/memory.md must be created empty only.
No AGENTS OS formal Memory content may be registered, imported, summarized, or
written during promotion.
```

The `.gitignore` write, if needed, should only add the ColaMeta local/private
runtime block.

## What It Must Not Do

Promotion does not authorize:

```text
starting ColaMeta service
changing auth or connector token
reading token/config/log raw content
running executor
running provider calls
modifying WORKSPACE_REGISTRY.yaml
writing formal AGENTS OS Memory content
reading state-private/
external writes
commit / push / tag
release / deploy / publish
Delivery State accepted
ReviewDecision
GateEvent
bulk move / delete / rename
```

## Preflight Before Any Promotion

Before promotion, check:

```text
1. .colameta still does not exist, or Jenn explicitly accepts overwrite/merge handling.
2. .gitignore still does not exist, or any existing file is reviewed before patching.
3. Runner plan draft still passes ColaMeta PlanLoader/Linter.
4. document registry and doctor are clean.
5. The current connector token_expired state is acknowledged.
6. Jenn confirms whether local fallback is allowed if the connector remains expired.
```

If any preflight check differs from this package, stop and prepare a new
confirmation package.

## Rollback Plan

Rollback is a separate local write action. Do not run it unless Jenn confirms
rollback after seeing the actual promotion result.

Expected rollback scope if promotion created only expected files:

```text
remove .colameta/
remove the ColaMeta local/private runtime block from .gitignore
remove .gitignore only if it was created solely by the promotion and contains
no other content
```

Rollback must not:

```text
delete unrelated files
use git reset --hard
use git clean -fd
touch state-private/
touch WORKSPACE_REGISTRY.yaml
touch external systems
```

## Validation After Promotion

After a confirmed promotion, run:

```text
PYTHONPATH=/home/jenn/tools/colameta python3 -c "import json; from runner.plan_loader import PlanLoader; from runner.plan_standards_linter import PlanStandardsLinter; path='.colameta/plan.json'; data=json.load(open(path, encoding='utf-8')); lint=PlanStandardsLinter().lint_plan_data(data, project_root='/home/jenn/AGENTS_OS_Workspace'); plan=PlanLoader().load_plan(path); PlanLoader().validate_plan(plan); print('loader_valid=True versions={} lint_status={} blocking={} warnings={}'.format(len(plan.versions), lint.get('status'), lint.get('blocking_issue_count'), lint.get('warning_count')))"
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

Manual checks:

```text
.colameta/plan.json exists and matches the validated 9.5 Runner plan shape
.colameta/memory.md is empty
no runtime service was started
no executor ran
no auth/provider/runtime config changed
no external write happened
```

## Exact Confirmation Text

To execute managed promotion, use this exact confirmation shape:

```text
确认执行 AGENTS OS ColaMeta managed promotion v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 创建窄范围 ColaMeta Runner 文件：
.colameta/plan.json、.colameta/state.json、.colameta/todolist.json、
.colameta/decisions.json、空的 .colameta/memory.md、.colameta/prompts/、
.colameta/runtime/、.colameta/logs/、.colameta/reports/、
.colameta/audits/、.colameta/plan-patches/，以及必要的 .gitignore
ColaMeta local/private runtime block。

使用 control-plane/registry/drafts/2026-07-02-document-governance-9.5-colameta-runner-plan.draft.json
作为 plan 来源。

不启动服务、不改 auth/token、不跑 executor、不做 provider 调用、不 commit/push/tag、
不发布、不部署、不写正式 AGENTS OS Memory 内容、不读 state-private/、
不改 WORKSPACE_REGISTRY.yaml、不做外部写入。
```

Until Jenn confirms this exact execution scope, AGENTS OS remains ColaMeta
`source-only` even though the direction is now decided.
