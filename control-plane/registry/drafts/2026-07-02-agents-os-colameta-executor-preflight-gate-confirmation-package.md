# AGENTS OS ColaMeta executor preflight gate Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact boundary for preparing a future ColaMeta executor
preflight gate for AGENTS OS. This package does not authorize starting
services, running executors, provider calls, or Memory writes.

This package is not execution authorization by itself. It defines the gate that
must be satisfied before any later executor run can be considered.

## Current Facts

Workspace-local ColaMeta Runner state exists and is locally ready:

```text
ColaMeta PlanLoader/Linter PASS loader_valid=True versions=7 lint_status=passed blocking=0 warnings=0
prompt_files=7
.colameta/memory.md bytes=0
docctl status PASS
```

The workspace-local prompt files are present:

```text
.colameta/prompts/dg95-stage-0.md
.colameta/prompts/dg95-stage-1.md
.colameta/prompts/dg95-stage-2.md
.colameta/prompts/dg95-stage-3.md
.colameta/prompts/dg95-stage-4.md
.colameta/prompts/dg95-stage-5.md
.colameta/prompts/dg95-stage-6.md
```

Readiness evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-agents-os-colameta-runner-readiness-pulse-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-agents-os-colameta-runner-readiness-pulse-v0.1.review.md
```

## Gate Purpose

The preflight gate is a future safety check before any ColaMeta executor run.
It should answer:

```text
Is the local plan valid?
Are prompt files present?
Is docctl clean?
Is the requested executor scope narrow and reversible?
Are provider, Memory, runtime, and external-write boundaries explicit?
Are expected outputs and evidence paths known before execution?
Are stop conditions clear?
```

The gate is not a runner. Passing the gate does not run the executor and does
not authorize execution.

## Required Input Checks

A future preflight gate must check, without printing raw plan or raw runtime
content:

```text
.colameta/plan.json exists
PlanLoader validates the plan
PlanStandardsLinter status is passed
enabled version count is expected
all referenced prompt files exist under .colameta/prompts/
prompt paths remain inside the workspace
docctl status is PASS
docctl doctor is PASS
.colameta/memory.md remains empty unless Jenn separately authorizes Memory
no protected path or state-private/ path is targeted
no auth/token/cookie/session/provider runtime file is targeted
```

It must not read or output:

```text
secrets / tokens / cookies / credentials
private raw memory
provider raw responses
raw logs
auth/provider/runtime configuration
state-private/
```

## Required Output Checks

A future preflight gate output must be summary-only and include:

```text
schema_version
passed
gate_status
executor_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
plan_loader_valid
lint_status
blocking_issue_count
warning_count
prompt_file_count
docctl_status
allowed_write_classes
forbidden_write_classes
expected_evidence
stop_conditions
```

It must not include full `.colameta/plan.json`, prompt file bodies, logs,
provider responses, secrets, tokens, cookies, private Memory, or runtime config
content.

## Forbidden Behavior

The preflight gate must not:

```text
start ColaMeta service
run ColaMeta executor
make provider calls
modify auth/token/cookie/session state
modify provider/runtime configuration
modify .colameta/plan.json
modify .colameta/state.json
write .colameta/memory.md content
write formal AGENTS OS Memory
read state-private/
read or output raw logs
read or output secrets/token/cookie/provider raw response/private memory
modify WORKSPACE_REGISTRY.yaml
write external systems
commit / push / tag
release / deploy / publish
bulk move / delete / rename
```

If any of these are required, stop and prepare a new confirmation package.

## Allowed Local Write Classes For Future Executor Discussion

The preflight gate itself should be read-only except for its own separately
confirmed evidence.

A later executor run, if separately confirmed, may only discuss these local
write classes:

```text
workspace-local reports under .colameta/reports/
workspace-local plan previews under .colameta/runtime/plan-previews/
workspace-local audits under .colameta/audits/
workspace-local logs only if log content is non-secret and not printed raw
Document Governance receipt/review evidence under control-plane/registry/
Document Registry metadata updates only to keep docctl doctor clean
```

These classes are not authorized by this package. They are candidate categories
for a future exact execution confirmation.

Forbidden local write classes remain:

```text
.colameta/plan.json
.colameta/state.json
.colameta/memory.md content
auth/token/cookie/session files
provider/runtime configuration
state-private/
WORKSPACE_REGISTRY.yaml
formal Memory
repair patches outside an explicitly confirmed scope
```

## Provider Call Boundary

Default provider call boundary:

```text
provider_call_authorized=false
unauthorized_paid_provider_call=false
provider_raw_response_read_or_output=false
```

Any future provider call requires a separate exact confirmation that names:

```text
provider/tool surface
purpose
input class
output class
cost/budget boundary
redaction boundary
evidence path
stop condition
```

The preflight gate must fail closed if provider authorization is unclear.

## Memory Boundary

Default Memory boundary:

```text
memory_write_authorized=false
formal_memory_registration=not_performed
.colameta/memory.md_write_authorized=false
private_memory_raw_read_or_output=false
```

Any future Memory write requires a separate confirmation entry point. The gate
may report whether Memory is empty or non-empty by byte count only; it must not
print Memory content.

## Failure Handling

If a future preflight gate fails:

```text
do not run executor
do not start service
do not call provider
do not write Memory
do not attempt automatic repair
write or update only the separately confirmed preflight evidence
report the blocking check by rule id and summary
prepare a new confirmation package if scope changes
```

Rollback is separate and must not use `git reset --hard`, `git clean -fd`, bulk
delete, or external writes.

## Evidence Requirements

Future preflight work must leave:

```text
receipt
review
validation summary
explicit no-service/no-executor/no-provider/no-Memory boundary statement
docctl doctor result
ColaMeta PlanLoader/Linter summary
prompt file count summary
```

Evidence must not include raw plan content, raw logs, secrets, tokens, cookies,
private Memory, provider raw responses, or runtime config.

## Validation Requirements

After preparing or running a future preflight gate, run only safe local
validation:

```text
PYTHONPATH=/home/jenn/tools/colameta python3 -c "import json; from runner.plan_loader import PlanLoader; from runner.plan_standards_linter import PlanStandardsLinter; path='.colameta/plan.json'; data=json.load(open(path, encoding='utf-8')); lint=PlanStandardsLinter().lint_plan_data(data, project_root='/home/jenn/AGENTS_OS_Workspace'); plan=PlanLoader().load_plan(path); PlanLoader().validate_plan(plan); print('loader_valid=True versions={} lint_status={} blocking={} warnings={}'.format(len(plan.versions), lint.get('status'), lint.get('blocking_issue_count'), lint.get('warning_count')))"
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

Manual checks:

```text
all seven prompt files exist
.colameta/memory.md remains empty unless separately authorized
no service started
no executor ran
no provider call occurred
no auth/provider/runtime config changed
no external write happened
```

## Exact Confirmation Text

To implement a future read-only preflight gate, use this exact confirmation
shape:

```text
确认执行 AGENTS OS ColaMeta executor preflight gate v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内实现只读 ColaMeta executor preflight gate，
只允许修改明确列出的本地 gate 文件、测试、文档、对应 receipt/review evidence，
并只为保持 docctl doctor clean 而更新 document registry 和 federated document registry。

preflight gate 只能执行只读输入检查和 summary-only 输出检查；
必须保持 executor_authorized=false、service_start_authorized=false、
provider_call_authorized=false、memory_write_authorized=false、
external_write_authorized=false。

不启动服务、不跑 executor、不做 provider call、不改 auth/token/cookie/session、
不改 provider/runtime 配置、不修改 .colameta/plan.json、不修改 .colameta/state.json、
不写 .colameta/memory.md 内容、不写正式 Memory、不读 state-private/、
不读取或输出 secrets/token/cookie/provider raw response/private memory/log raw content、
不修改 WORKSPACE_REGISTRY.yaml、不做外部写入、不 commit/push/tag/deploy/publish、
不做 bulk move/delete/rename。
```
