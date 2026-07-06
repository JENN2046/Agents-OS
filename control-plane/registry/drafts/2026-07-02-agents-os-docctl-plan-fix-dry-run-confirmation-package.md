# AGENTS OS docctl plan-fix dry-run Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for designing and implementing a
read-only `docctl plan-fix` dry-run command for AGENTS OS document governance.

This package is not execution authorization by itself. It is the narrow
confirmation material for a future local implementation step.

## Current Facts

Document Governance 9.5 local implementation is clean through Stage 6:

```text
docctl doctor PASS
docctl score PASS score=100 eligible_95=True
docctl trend PASS trend_status=insufficient_snapshots
```

The current deferred write boundary remains active:

```text
apply-fix is out of scope
snapshot writing is out of scope
service start is out of scope
executor run is out of scope
provider call is out of scope
external writes are out of scope
```

`plan-fix` is the next safe design step because it can explain potential repair
actions without performing them.

## What The Future Step Would Implement

If Jenn later confirms execution, the implementation target is a dry-run
command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix --json
```

The command may read the same declared local inputs already used by `docctl
doctor` and produce a repair proposal only.

Allowed proposal categories:

```text
register_missing_document
classify_known_external_scope
classify_archive_note
fix_expected_document_count
repair_broken_reference
add_missing_review_link
blocked_protected_path
manual_review_required
no_action_needed
```

The proposal must include:

```text
affected_path
reason
suggested_action
risk_level
required_confirmation
validation_commands
evidence_required
write_performed=false
```

## Expected Local Implementation Writes

If Jenn later confirms implementation, expected writes are limited to:

```text
control-plane/registry/docctl.py
control-plane/registry/test-docctl-plan-fix.py
control-plane/registry/README.md
control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-plan-fix-dry-run-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-plan-fix-dry-run-v0.1.review.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

The registry writes are only to keep local document governance validation clean
after new test and evidence files are created.

## What The Future Command Must Not Do

`docctl plan-fix` must not:

```text
modify files
create patches
apply repairs
write snapshots
write registries
write receipts or reviews
write formal AGENTS OS Memory
read state-private/
read or expose secrets/tokens/cookies/credentials
read provider raw responses
modify auth/token/cookie/session state
modify provider/runtime configuration
start ColaMeta service
run ColaMeta executor
make provider calls
perform external writes
commit / push / tag
release / deploy / publish
bulk move / delete / rename
```

If a finding would require any write action, `plan-fix` may only report the
needed future confirmation scope. It must not perform the write.

## Preflight Before Implementation

Before implementing the future command, check:

```text
1. docctl doctor is clean or its findings are explainable.
2. docctl score hard gates are clear or their failures are used only as test fixtures.
3. path_boundary.py still blocks protected/P3 paths.
4. The implementation does not add snapshot writing.
5. The implementation does not add apply-fix.
6. The implementation does not add service, executor, provider, auth, runtime, or Memory behavior.
7. New fixture tests cover clean state, unregistered file, expected count mismatch, protected path, and JSON output.
```

If any preflight check differs from this package, stop and prepare a revised
confirmation package.

## Reporting Boundary

The future implementation report may print:

```text
files changed
validation commands
plan-fix proposal category counts
write_performed=false
doctor/score status
```

It must not print raw secrets, tokens, cookies, credentials, private memory,
provider raw responses, auth config, unrelated ColaMeta runtime content, or raw
logs.

## Validation After Future Implementation

After confirmed implementation, run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-plan-fix.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix --json
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

Manual checks:

```text
plan-fix output says write_performed=false
no apply-fix command exists unless separately confirmed
no snapshot file was created
no service was started
no executor ran
no provider call happened
.colameta/memory.md remains empty
```

## Exact Confirmation Text

To execute the future dry-run implementation, use this exact confirmation
shape:

```text
确认执行 AGENTS OS docctl plan-fix dry-run v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内实现只读/干跑的
docctl plan-fix 命令，只允许修改：

- control-plane/registry/docctl.py
- control-plane/registry/test-docctl-plan-fix.py
- control-plane/registry/README.md
- control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
- 对应本地 receipt/review evidence
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

docctl plan-fix 只能读取已声明的本地 registry/doctor 输入并输出 repair
proposal；必须是 dry-run，必须报告 write_performed=false。

不允许实现 apply-fix，不允许执行任何修复写入，不允许创建 patch 或 snapshot，
不启动服务、不跑 executor、不做 provider call、不改 auth/token/cookie/session、
不改 provider/runtime 配置、不写正式 Memory、不读 state-private/、
不读取或输出 secrets/token/cookie/provider raw response/private memory/log raw
content、不修改 WORKSPACE_REGISTRY.yaml、不修改 .colameta/plan.json、
不修改 .colameta/state.json、不写 .colameta/memory.md 内容、不做外部写入、
不 commit/push/tag/deploy/publish、不做 bulk move/delete/rename。
```

If Jenn confirms with materially different text, use the newer explicit
confirmation as the active boundary.
