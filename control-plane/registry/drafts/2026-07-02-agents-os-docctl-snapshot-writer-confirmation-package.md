# AGENTS OS docctl snapshot writer Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for a future local `docctl`
snapshot writer that records document-governance doctor/score summaries for
`docctl trend`.

This package is not execution authorization by itself. It is the narrow
confirmation material for a future local write-capable implementation step.

## Current Facts

Document Governance 9.5 local checks are clean:

```text
docctl doctor PASS
docctl score PASS score=100 eligible_95=True
```

`docctl trend` is implemented and read-only, but currently has no local
snapshot history:

```text
docctl trend PASS
trend_status=insufficient_snapshots
snapshots_found=0
```

The current deferred write boundary remains active:

```text
snapshot writing is out of scope until Jenn confirms implementation
apply-fix is out of scope
service start is out of scope
executor run is out of scope
provider call is out of scope
external writes are out of scope
```

## What The Future Step Would Implement

If Jenn later confirms execution, the implementation target is a local
snapshot-writing command that writes one reviewed local JSON snapshot under the
declared snapshot directory:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py snapshot
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py snapshot --json
```

Default snapshot directory:

```text
control-plane/registry/reports/docctl-snapshots/
```

The snapshot writer may read only the same declared local inputs already used
by `docctl doctor`, `docctl score`, and `docctl trend`. It must not read target
document contents, secrets, private state, raw logs, provider raw responses, or
runtime/auth configuration.

## Snapshot Shape

Each future snapshot should be rebuildable governance evidence, not authority
data.

Minimum JSON fields:

```text
schema_version
created_at
workspace_root
federated_registry
doctor_summary
score_summary
trend_context
source_commands
write_scope
write_performed=true
external_write_performed=false
provider_call_performed=false
formal_memory_registration=not_performed
```

The snapshot must not include raw registry contents, raw logs, secrets,
tokens, cookies, credentials, private memory, provider raw responses, or full
document text.

## Expected Local Implementation Writes

If Jenn later confirms implementation, expected writes are limited to:

```text
control-plane/registry/docctl.py
control-plane/registry/test-docctl-snapshot.py
control-plane/registry/README.md
control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
control-plane/registry/reports/docctl-snapshots/
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-snapshot-writer-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-snapshot-writer-v0.1.review.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

The registry writes are only to keep local document governance validation clean
after new test, snapshot-report, and evidence files are created.

## What The Future Command Must Not Do

`docctl snapshot` must not:

```text
write outside control-plane/registry/reports/docctl-snapshots/
overwrite an existing snapshot without separate confirmation
modify registries directly
modify source documents
create repair patches
implement or run apply-fix
write formal AGENTS OS Memory
read state-private/
read or expose secrets/tokens/cookies/credentials
read provider raw responses
read raw logs
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

If a snapshot path is protected, outside the workspace, or already exists, the
future command must stop before writing and report a blocked result.

## Preflight Before Implementation

Before implementing the future command, check:

```text
1. docctl doctor is clean.
2. docctl score is 9.5 eligible or the snapshot command reports non-eligible state explicitly.
3. docctl trend remains read-only.
4. path_boundary.py blocks protected/P3 paths.
5. The implementation does not add apply-fix.
6. The implementation does not add service, executor, provider, auth, runtime, or Memory behavior.
7. New fixture tests cover clean snapshot creation in a temp directory, existing-file block, protected snapshot dir block, and JSON output.
```

If any preflight check differs from this package, stop and prepare a revised
confirmation package.

## Reporting Boundary

The future implementation report may print:

```text
files changed
snapshot path
validation commands
doctor/score/trend status
write_performed=true for snapshot file only
external_write_performed=false
provider_call_performed=false
```

It must not print raw secrets, tokens, cookies, credentials, private memory,
provider raw responses, auth config, unrelated ColaMeta runtime content, raw
logs, or full snapshot contents if future snapshots include more than summary
metadata.

## Validation After Future Implementation

After confirmed implementation, run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-snapshot.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py snapshot --json
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

Manual checks:

```text
exactly one expected local snapshot is created
snapshot path is under control-plane/registry/reports/docctl-snapshots/
snapshot contains summary metadata only
no apply-fix command is implemented
no service was started
no executor ran
no provider call happened
.colameta/memory.md remains empty
```

## Exact Confirmation Text

To execute the future snapshot writer implementation, use this exact
confirmation shape:

```text
确认执行 AGENTS OS docctl snapshot writer v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内实现本地 docctl snapshot writer，
只允许修改：

- control-plane/registry/docctl.py
- control-plane/registry/test-docctl-snapshot.py
- control-plane/registry/README.md
- control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
- control-plane/registry/reports/docctl-snapshots/
- 对应本地 receipt/review evidence
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

docctl snapshot 只能读取已声明的本地 registry/doctor/score/trend 输入，
只能在 control-plane/registry/reports/docctl-snapshots/ 下写入一个本地
summary snapshot。snapshot 不得包含 raw registry content、raw logs、secret、
token、cookie、credential、private memory、provider raw response 或全文档内容。

不允许实现 apply-fix，不允许执行修复写入，不允许创建 repair patch，
不启动服务、不跑 executor、不做 provider call、不改 auth/token/cookie/session、
不改 provider/runtime 配置、不写正式 Memory、不读 state-private/、
不读取或输出 secrets/token/cookie/provider raw response/private memory/log raw
content、不修改 WORKSPACE_REGISTRY.yaml、不修改 .colameta/plan.json、
不修改 .colameta/state.json、不写 .colameta/memory.md 内容、不做外部写入、
不 commit/push/tag/deploy/publish、不做 bulk move/delete/rename。
```

If Jenn confirms with materially different text, use the newer explicit
confirmation as the active boundary.
