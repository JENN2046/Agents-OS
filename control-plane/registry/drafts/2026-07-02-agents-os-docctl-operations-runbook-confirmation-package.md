# AGENTS OS docctl operations runbook Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for a future local `docctl`
operations runbook that explains how to operate doctor, status, score, trend,
snapshot, and plan-fix without crossing P3 boundaries.

This package is not execution authorization by itself. It is the narrow
confirmation material for a future local documentation step.

## Current Facts

Document Governance 9.5 has a local control-plane body:

```text
docctl doctor
docctl status
docctl score
docctl trend
docctl snapshot
docctl plan-fix
```

Current local health before this package:

```text
docctl doctor PASS
docctl status PASS
docctl score PASS score=100 eligible_95=True
docctl trend PASS snapshots_found=1 no_regression_from_latest=True
docctl plan-fix PASS plan_status=no_action_needed
```

Current deferred repair boundary remains active:

```text
apply-fix is out of scope
repair writes are out of scope
service start is out of scope
executor run is out of scope
provider call is out of scope
external writes are out of scope
formal Memory registration is out of scope
```

## What The Future Step Would Create

If Jenn later confirms execution, the implementation target is one local
operations runbook:

```text
control-plane/registry/runbooks/docctl-operations-runbook-v0.1.md
```

The runbook should turn the current tool body into a repeatable operating
path. It should explain:

```text
when to run doctor
when to run status
when to run score
when to run trend
when snapshot requires explicit confirmation
when plan-fix may be used as dry-run only
what evidence to leave after local governance work
which P3/P3b boundaries stop execution
what next-step decision table to use after each result
```

The future runbook is documentation only. It must not implement code,
execute repairs, create snapshots, run executors, call providers, or register
formal Memory.

## Expected Future Runbook Shape

Minimum sections:

```text
Purpose
Command map
Green / yellow / red operating table
Read-only daily pulse
Before local write
After local write
Snapshot cadence
Plan-fix dry-run route
P3 hard stops
Evidence checklist
Validation checklist
Escalation and stop rules
```

Command classification:

```text
doctor: read-only
status: read-only
score: read-only
trend: read-only
plan-fix: dry-run proposal only
snapshot: local write-capable, requires explicit confirmation
apply-fix: not implemented and not authorized
```

## Expected Local Implementation Writes

If Jenn later confirms implementation, expected writes are limited to:

```text
control-plane/registry/runbooks/docctl-operations-runbook-v0.1.md
control-plane/registry/README.md
control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-docctl-operations-runbook-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-docctl-operations-runbook-v0.1.review.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

The registry writes are only to keep local document governance validation clean
after the runbook and evidence files are created.

## What The Future Step Must Not Do

The future runbook implementation must not:

```text
implement apply-fix
modify docctl.py behavior
execute repair writes
create repair patches
write snapshots
start ColaMeta service
run ColaMeta executor
make provider calls
modify auth/token/cookie/session state
modify provider/runtime configuration
write formal AGENTS OS Memory
read state-private/
read or expose secrets/tokens/cookies/credentials
read provider raw responses
read private raw memory
read raw logs
modify WORKSPACE_REGISTRY.yaml
modify .colameta/plan.json
modify .colameta/state.json
write .colameta/memory.md content
perform external writes
commit / push / tag
release / deploy / publish
bulk move / delete / rename
```

If the runbook would need any behavior outside this package, stop and prepare a
revised confirmation package.

## Preflight Before Future Implementation

Before creating the future runbook, check:

```text
1. docctl status is clean.
2. docctl doctor is clean.
3. docctl score remains 9.5 eligible.
4. docctl trend can read existing snapshots without writing.
5. plan-fix remains dry-run only.
6. snapshot remains separate from ordinary read-only status checks.
7. apply-fix remains not implemented.
8. The future runbook path is under the workspace and not protected.
```

## Reporting Boundary

The future implementation report may print:

```text
files changed
runbook path
validation commands
doctor/status/score/trend/plan-fix status
write_performed=false except the confirmed local documentation/evidence files
external_write_performed=false
provider_call_performed=false
formal_memory_registration=not_performed
```

It must not print raw secrets, tokens, cookies, credentials, private memory,
provider raw responses, auth config, unrelated ColaMeta runtime content, raw
logs, or full private state.

## Validation After Future Implementation

After confirmed implementation, run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

Manual checks:

```text
runbook exists under control-plane/registry/runbooks/
runbook does not authorize apply-fix
runbook keeps snapshot as explicit-confirmation write
runbook keeps plan-fix dry-run only
no service was started
no executor ran
no provider call happened
.colameta/memory.md remains empty
```

## Exact Confirmation Text

To execute the future runbook implementation, use this exact confirmation
shape:

```text
确认执行 AGENTS OS docctl operations runbook v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内创建本地 docctl operations runbook，
只允许修改：

- control-plane/registry/runbooks/docctl-operations-runbook-v0.1.md
- control-plane/registry/README.md
- control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
- 对应本地 receipt/review evidence
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

runbook 只能整理 doctor/status/score/trend/snapshot/plan-fix 的本地操作流程、
边界、验证和 evidence 要求。snapshot 必须保持显式确认写入；plan-fix 必须
保持 dry-run；apply-fix 不得实现或授权。

不实现 apply-fix、不修改 docctl.py 行为、不执行修复写入、不创建 repair patch、
不写 snapshot、不启动服务、不跑 executor、不做 provider call、
不改 auth/token/cookie/session、不改 provider/runtime 配置、不写正式 Memory、
不读 state-private/、不读取或输出 secrets/token/cookie/provider raw response/private
memory/log raw content、不修改 WORKSPACE_REGISTRY.yaml、不修改 .colameta/plan.json、
不修改 .colameta/state.json、不写 .colameta/memory.md 内容、不做外部写入、
不 commit/push/tag/deploy/publish、不做 bulk move/delete/rename。
```

If Jenn confirms with materially different text, use the newer explicit
confirmation as the active boundary.
