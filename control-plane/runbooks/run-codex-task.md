# Runbook: Run Codex Task

Status: ordinary runbook guidance. This document is procedural guidance, not authorization to execute risky work.

Source reference:

```text
A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\run-codex-task.md
```

Canonical security authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Flow

```text
Task request
↓
Scope and risk classification
↓
Relevant control-plane and governance context
↓
Approval gate for risky actions
↓
Local implementation only when authorized
↓
Validation
↓
Receipt
```

## Default

Codex tasks start as audit-only unless explicitly authorized.

Local documentation patches and other reversible local edits may proceed only
inside the user's scoped authorization. Remote writes, branch movement, release,
deploy, secret access, private-state access, and destructive actions always need
separate explicit approval.

## Forbidden By Default

```text
push
release
deploy
read secrets
modify main
destructive delete
private-state access
self-expansion of permissions
```

## Receipt

For any authorized local patch, leave a receipt or status record that states:

```text
authorization scope
files created or changed
files intentionally skipped
validation run
validation not run
remaining risk
rollback path
```
