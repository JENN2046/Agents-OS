# AGENTS OS docctl apply-fix design gate Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for a future local `docctl`
apply-fix design gate. The design gate would define safety requirements before
any future write-capable `apply-fix` tool is implemented.

This package is not execution authorization by itself. It is the narrow
confirmation material for a future local design documentation step.

## Current Facts

Document Governance 9.5 has a clean local control-plane body:

```text
docctl doctor PASS
docctl status PASS
docctl score PASS score=100 eligible_95=True
docctl trend PASS snapshots_found=1 no_regression_from_latest=True
docctl plan-fix PASS plan_status=no_action_needed
```

Current repair boundary:

```text
apply-fix is not implemented
apply-fix is not authorized
plan-fix is dry-run only
snapshot is a separate explicit-confirmation local write
repair writes require separate explicit confirmation
```

Current local runbook:

```text
control-plane/registry/runbooks/docctl-operations-runbook-v0.1.md
```

## Why A Design Gate Exists

`apply-fix` would be a write-capable repair tool. It must not appear as a
small convenience command without first making its boundary reviewable.

The design gate must decide what future `apply-fix` is allowed to propose,
what it must never touch, how confirmation works, what evidence is required,
and how validation proves the workspace stayed clean.

## What The Future Step Would Create

If Jenn later confirms execution, the future step would create one local
design-gate document:

```text
control-plane/registry/drafts/2026-07-02-agents-os-docctl-apply-fix-design-gate-v0.1.md
```

That future document would be design only. It must not implement code, modify
`docctl.py`, execute repairs, create repair patches, write snapshots, run
executors, call providers, or register formal Memory.

## Expected Future Design Gate Shape

Minimum sections:

```text
Purpose
Non-goals
Current allowed commands
Candidate repair classes
Forbidden repair classes
Confirmation model
Patch and preview model
Rollback and evidence model
Validation model
P3 and P3b stop rules
Future implementation preflight
Implementation-not-authorized statement
```

## Candidate Repair Classes For Future Review

The design gate may discuss candidate repair classes. Discussion does not
authorize implementation or execution.

Candidate low-risk classes:

```text
fix expected_document_count after validators prove the child registry count
add registry metadata for an already confirmed local evidence file
add registry metadata for an already confirmed local runbook or draft
repair a broken review_by link only when the referenced local review exists
normalize a registry path only when old and new paths resolve to the same safe local file
```

Each candidate class must require:

```text
plan-fix proposal source
explicit Jenn confirmation
bounded file allowlist
receipt/review evidence
registry validation
docctl doctor/status closeout
```

## Forbidden Future Repair Classes

The design gate must forbid automatic repair for:

```text
protected paths
state-private/
secrets/tokens/cookies/credentials
private raw memory
provider raw responses
raw logs
auth/provider/runtime configuration
WORKSPACE_REGISTRY.yaml authority changes
.colameta/plan.json
.colameta/state.json
.colameta/memory.md content
external writes
service starts
executor runs
provider calls
snapshot writes
archive promotion to active guidance
bulk move/delete/rename
history rewrite, tag, deploy, release, publish, force push
```

The design gate must also forbid any repair that requires reading sensitive
content before deciding whether the action is safe.

## Confirmation Model

Future `apply-fix` work must have at least two gates:

```text
1. design gate confirmation
2. implementation confirmation
```

Implementation confirmation must still not imply execution confirmation.

Future execution confirmation, if ever allowed, must name:

```text
exact repair class
exact input plan-fix proposal id
exact writable paths
expected generated evidence
validation commands
rollback route
```

## Expected Local Writes For The Future Design Gate

If Jenn later confirms the design gate step, expected writes are limited to:

```text
control-plane/registry/drafts/2026-07-02-agents-os-docctl-apply-fix-design-gate-v0.1.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-apply-fix-design-gate-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-apply-fix-design-gate-v0.1.review.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

The registry writes are only to keep local document governance validation clean
after the design-gate document and evidence files are created.

## What The Future Design Gate Step Must Not Do

The future design gate step must not:

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

If the design gate would need any behavior outside this package, stop and
prepare a revised confirmation package.

## Preflight Before Future Design Gate

Before creating the future design gate, check:

```text
1. docctl status is clean.
2. docctl doctor is clean.
3. docctl score remains 9.5 eligible.
4. docctl trend can read existing snapshots without writing.
5. docctl plan-fix remains dry-run only.
6. docctl snapshot remains separate from apply-fix.
7. apply-fix remains not implemented.
8. The future design-gate path is under the workspace and not protected.
```

## Validation After Future Design Gate

After confirmed design-gate documentation, run:

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
apply-fix is still not implemented
docctl.py behavior did not change
no repair patch was created
no snapshot file was written
no service was started
no executor ran
no provider call happened
.colameta/memory.md remains empty
```

## Exact Confirmation Text

To execute the future design-gate documentation step, use this exact
confirmation shape:

```text
确认执行 AGENTS OS docctl apply-fix design gate v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内创建未来 apply-fix 的本地设计门文档，
只允许修改：

- control-plane/registry/drafts/2026-07-02-agents-os-docctl-apply-fix-design-gate-v0.1.md
- 对应本地 receipt/review evidence
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

design gate 只能定义未来 apply-fix 的安全边界、候选修复类别、禁止修复类别、
确认模型、回滚/evidence/validation 要求；不得实现 apply-fix，不得修改
docctl.py 行为，不得执行任何修复写入。

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
