# AGENTS OS ColaMeta executor first-run dry-run Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact boundary for a future ColaMeta executor first-run
dry-run / plan-preview step for AGENTS OS. This package does not authorize
starting services, running executors, provider calls, Memory writes, or runtime
state changes.

This package is not execution authorization by itself. It defines the future
first-run dry-run boundary that must be separately confirmed before any dry-run
executor action is attempted.

## Current Facts

Workspace-local ColaMeta Runner state is ready for a gated next step:

```text
ColaMeta executor preflight gate PASS
ColaMeta PlanLoader/Linter PASS loader_valid=True versions=7 lint_status=passed blocking=0 warnings=0
prompt_files=7
.colameta/memory.md bytes=0
docctl status PASS
```

Relevant local evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-agents-os-colameta-runner-readiness-pulse-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-agents-os-colameta-runner-readiness-pulse-v0.1.review.md
control-plane/registry/receipts/2026-07-02-yellow-agents-os-colameta-executor-preflight-gate-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-agents-os-colameta-executor-preflight-gate-v0.1.review.md
```

## Future Dry-Run Purpose

The future first-run dry-run should prove that ColaMeta can prepare a local
executor plan-preview without provider calls, Memory writes, runtime changes,
or irreversible effects.

It should answer:

```text
Can the local runner resolve the selected plan version set?
Can it produce a summary-only local execution preview?
Are expected local outputs known before execution?
Are provider and Memory boundaries still closed?
Are stop conditions and rollback paths explicit?
Can evidence be produced without exposing raw plan, raw logs, secrets, or private data?
```

The future dry-run must not become an implicit real executor run.

## Allowed Future Inputs

A future first-run dry-run may only use:

```text
.colameta/plan.json as validated by PlanLoader
.colameta/prompts/dg95-stage-0.md through dg95-stage-6.md by path reference
read-only colameta-executor-preflight output
docctl status / doctor summaries
the explicit dry-run confirmation text from Jenn
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

Prompt bodies may only be used by the future dry-run if the dry-run tool
requires them for local preview assembly and must not be printed raw in
evidence.

## Allowed Future Outputs

A future first-run dry-run may only produce summary-only local preview outputs,
after separate exact confirmation, under these candidate paths:

```text
.colameta/runtime/plan-previews/
.colameta/reports/
.colameta/audits/
control-plane/registry/receipts/
control-plane/registry/reviews/
```

Output must include explicit flags:

```text
dry_run=true
plan_preview_only=true
service_started=false
executor_real_run=false
provider_call_performed=false
memory_write_performed=false
colameta_plan_modified=false
colameta_state_modified=false
colameta_memory_content_written=false
external_write_performed=false
```

It must not include raw provider responses, raw logs, raw private Memory, raw
secrets/tokens/cookies, or full `.colameta/plan.json` content.

## Forbidden Future Behavior

Future first-run dry-run must not:

```text
start ColaMeta service
perform a real executor run
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

If a dry-run tool requires any forbidden behavior, stop and prepare a new
confirmation package.

## Provider Call Boundary

Default provider boundary:

```text
provider_call_authorized=false
provider_call_performed=false
provider_raw_response_read_or_output=false
unauthorized_paid_provider_call=false
```

Any future provider call requires a separate exact confirmation naming provider
surface, purpose, input class, output class, cost boundary, redaction boundary,
evidence path, and stop condition. This first-run dry-run route should fail
closed if provider authorization is unclear.

## Memory Boundary

Default Memory boundary:

```text
memory_write_authorized=false
memory_write_performed=false
formal_memory_registration=not_performed
.colameta/memory.md_write_authorized=false
private_memory_raw_read_or_output=false
```

The future dry-run may report `.colameta/memory.md` byte count only. It must
not print Memory content.

## Failure Handling

If the future dry-run fails:

```text
do not retry with broader scope
do not run real executor
do not call provider
do not write Memory
do not alter plan/state
do not attempt automatic repair
leave only the separately confirmed dry-run evidence
report the failure by rule id and summary
prepare a revised confirmation package if scope changes
```

## Rollback Requirements

Rollback is separate local write work and must require Jenn confirmation.

If a future dry-run creates only the expected local preview outputs, rollback
may discuss removing only:

```text
the specific .colameta/runtime/plan-previews/ files created by that dry-run
the specific .colameta/reports/ files created by that dry-run
the specific .colameta/audits/ files created by that dry-run
the specific receipt/review evidence for that dry-run
the corresponding document registry entries created only for that dry-run
```

Rollback must not:

```text
use git reset --hard
use git clean -fd
bulk delete
touch .colameta/plan.json
touch .colameta/state.json
touch .colameta/memory.md
touch state-private/
touch WORKSPACE_REGISTRY.yaml
touch external systems
```

## Evidence Requirements

Future dry-run evidence must include:

```text
receipt
review
preflight gate result summary
dry-run output path summary
explicit no-service/no-real-executor/no-provider/no-Memory boundary statement
docctl doctor result
ColaMeta PlanLoader/Linter summary
prompt file count summary
rollback scope summary
```

Evidence must not include raw plan content, prompt bodies, raw logs, secrets,
tokens, cookies, private Memory, provider raw responses, or runtime config.

## Validation Requirements

After any future confirmed dry-run, run only safe local validation:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/colameta-executor-preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

Manual checks:

```text
service was not started
real executor did not run
provider call did not happen
.colameta/plan.json unchanged
.colameta/state.json unchanged
.colameta/memory.md content unchanged
no state-private/ access
no external write
```

## Exact Confirmation Text

To execute a future first-run dry-run, use this exact confirmation shape:

```text
确认执行 AGENTS OS ColaMeta executor first-run dry-run v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内执行一次本地 ColaMeta executor dry-run / plan-preview，
只允许生成明确列出的本地 dry-run preview/report/audit/evidence 文件，
并只为保持 docctl doctor clean 而更新 document registry 和 federated document registry。

first-run dry-run 必须保持 dry_run=true、plan_preview_only=true、
service_started=false、executor_real_run=false、provider_call_performed=false、
memory_write_performed=false、colameta_plan_modified=false、
colameta_state_modified=false、colameta_memory_content_written=false、
external_write_performed=false。

不启动服务、不做真实 executor run、不做 provider call、
不改 auth/token/cookie/session、不改 provider/runtime 配置、
不修改 .colameta/plan.json、不修改 .colameta/state.json、
不写 .colameta/memory.md 内容、不写正式 Memory、不读 state-private/、
不读取或输出 secrets/token/cookie/provider raw response/private memory/log raw content、
不修改 WORKSPACE_REGISTRY.yaml、不做外部写入、不 commit/push/tag/deploy/publish、
不做 bulk move/delete/rename。
```
