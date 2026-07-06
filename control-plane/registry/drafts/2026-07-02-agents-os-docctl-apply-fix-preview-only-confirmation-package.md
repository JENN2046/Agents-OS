# AGENTS OS docctl apply-fix preview-only Confirmation Package

Status: `confirmation_package_draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: confirm the exact execution boundary for a future local `docctl
apply-fix --preview` implementation. The future preview command would turn
`plan-fix` proposals into reviewable read-only previews without writing files.

This package is not execution authorization by itself. It is the narrow
confirmation material for a future read-only preview implementation step.

## Current Facts

Document Governance 9.5 has a clean local control-plane body:

```text
docctl doctor PASS
docctl status PASS
docctl score PASS score=100 eligible_95=True
docctl trend PASS snapshots_found=1 no_regression_from_latest=True
docctl plan-fix PASS plan_status=no_action_needed
```

Current apply-fix boundary:

```text
apply-fix is not implemented
apply-fix execution is not authorized
repair writes are not authorized
repair patch creation is not authorized
snapshot writes are separate and require explicit confirmation
```

Existing design gate:

```text
control-plane/registry/drafts/2026-07-02-agents-os-docctl-apply-fix-design-gate-v0.1.md
```

## What Preview-Only Means

Future `apply-fix --preview` may only produce a read-only, bounded preview from
an existing `plan-fix` proposal.

It must not:

```text
write registry files
write source documents
write snapshots
create repair patch files
apply repairs
modify docctl state
start services
run executors
call providers
write external systems
```

Preview output is explanation, not permission. A later execution path, if ever
allowed, must still require a separate exact confirmation.

## What The Future Step Would Implement

If Jenn later confirms execution, the implementation target is a read-only
preview surface, likely shaped as:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview <proposal-id>
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview <proposal-id> --json
```

The future command may read the same declared registry inputs used by
`plan-fix`. It must not read target document contents unless the path is already
safe, local, non-protected, and required for the preview class. It must never
read secrets, state-private, private raw memory, provider raw responses, raw
logs, auth/provider/runtime configuration, or `.colameta/memory.md` content.

## Expected Preview Shape

Minimum preview fields:

```text
schema_version
passed
preview_only=true
dry_run=true
would_write=false
write_performed=false
patch_created=false
snapshot_write_performed=false
proposal_id
proposal_category
affected_path
repair_class
allowed_for_preview
execution_authorized=false
required_confirmation
validation_commands
evidence_required
blocked_reasons
warnings
```

Text output should make the boundary obvious:

```text
Preview only: True
Would write: False
Patch created: False
Execution authorized: False
```

## Allowed Preview Inputs

Future preview may only accept proposals produced by:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix --json
```

Allowed proposal categories for preview discussion:

```text
fix_expected_document_count
register_missing_document
add_missing_review_link
repair_broken_reference
manual_review_required
no_action_needed
```

Allowed preview does not mean allowed execution. It only means the proposal can
be summarized for review.

## Forbidden Preview Behavior

Future preview must not:

```text
create patch files
emit full file contents
emit raw registry content
emit raw logs
emit secrets/tokens/cookies/credentials
emit private raw memory
emit provider raw responses
emit auth/provider/runtime config
write formal Memory
write .colameta/memory.md content
write .colameta/plan.json
write .colameta/state.json
modify WORKSPACE_REGISTRY.yaml
perform external writes
```

If a proposal touches protected/P3 material, the preview must stop with a
blocked result and must not inspect content.

## Expected Local Implementation Writes

If Jenn later confirms preview-only implementation, expected writes are limited
to:

```text
control-plane/registry/docctl.py
control-plane/registry/test-docctl-apply-fix-preview.py
control-plane/registry/README.md
control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-apply-fix-preview-only-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-apply-fix-preview-only-v0.1.review.md
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

The registry writes are only to keep local document governance validation clean
after new test and evidence files are created.

## What The Future Preview Step Must Not Do

The future preview implementation must not:

```text
execute repair writes
create repair patches
write snapshots
modify registry data as part of preview
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

If the preview implementation would need any behavior outside this package,
stop and prepare a revised confirmation package.

## Preflight Before Future Preview Implementation

Before implementing preview-only behavior, check:

```text
1. docctl status is clean.
2. docctl doctor is clean.
3. docctl score remains 9.5 eligible.
4. docctl trend can read existing snapshots without writing.
5. docctl plan-fix remains dry-run only.
6. apply-fix execution remains not implemented and not authorized.
7. The design gate remains reviewed.
8. Preview tests cover clean no-action, proposal preview, protected proposal block, and JSON output.
```

## Validation After Future Preview Implementation

After confirmed preview-only implementation, run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-apply-fix-preview.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview PF-0001
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview PF-0001 --json
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
```

Manual checks:

```text
write_performed=false
patch_created=false
snapshot_write_performed=false
execution_authorized=false
no repair patch file exists
no snapshot file is created
no service was started
no executor ran
no provider call happened
.colameta/memory.md remains empty
```

## Exact Confirmation Text

To execute the future preview-only implementation step, use this exact
confirmation shape:

```text
确认执行 AGENTS OS docctl apply-fix preview-only v0.1。
允许在 /home/jenn/AGENTS_OS_Workspace 内实现未来 apply-fix 的只读 preview 模式，
只允许修改：

- control-plane/registry/docctl.py
- control-plane/registry/test-docctl-apply-fix-preview.py
- control-plane/registry/README.md
- control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
- 对应本地 receipt/review evidence
- 只为保持 docctl doctor clean 而更新 document registry 和 federated document registry

apply-fix --preview 只能从 plan-fix proposal 生成只读预览；必须保持
write_performed=false、patch_created=false、snapshot_write_performed=false、
execution_authorized=false。不允许执行修复写入，不允许创建 repair patch，
不允许修改 registry，不允许写 snapshot。真实 apply-fix 执行仍不授权。

不执行修复写入、不创建 repair patch、不写 snapshot、不启动服务、不跑 executor、
不做 provider call、不改 auth/token/cookie/session、不改 provider/runtime 配置、
不写正式 Memory、不读 state-private/、不读取或输出 secrets/token/cookie/provider
raw response/private memory/log raw content、不修改 WORKSPACE_REGISTRY.yaml、
不修改 .colameta/plan.json、不修改 .colameta/state.json、
不写 .colameta/memory.md 内容、不做外部写入、不 commit/push/tag/deploy/publish、
不做 bulk move/delete/rename。
```

If Jenn confirms with materially different text, use the newer explicit
confirmation as the active boundary.
