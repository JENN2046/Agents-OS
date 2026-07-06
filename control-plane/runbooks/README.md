# Runbooks

Status: ordinary runbook index. Guidance only; not authorization to execute
work.

Source reference:

```text
A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\README.AGENTS_OS.md
```

Canonical security authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Purpose

Ordinary runbooks describe audit-first procedures for common control-plane work.
They help plan and review work, but they do not authorize remote writes, branch
movement, releases, deployments, secret access, destructive actions, or private
state reads.

## Included Ordinary Runbooks

```text
add-new-extension.md
onboard-new-agent.md
run-codex-task.md
```

## Explicitly Not Included

```text
upstream-sync-vcptoolbox.md
approve-protected-action.md
handle-failed-action.md
```

`upstream-sync-vcptoolbox.md` is remote/sync-sensitive and is reserved for a
separate restricted maintenance-reference batch.

`approve-protected-action.md` and `handle-failed-action.md` were named in the
source README but were not observed as source files during inventory. Do not
create placeholder runbooks for them without a separate source and scope check.

## Default Boundary

All ordinary runbooks are audit-first by default.

Forbidden by default:

```text
secret values
secret reading
one-off hacks without boundary
commands that push/release/deploy by default
destructive recipes
private-state copying
self-expansion of permissions
```

Any permission increase, remote write, release, deploy, branch movement, secret
access, private-state access, or destructive action requires separate explicit
authorization and a receipt.

## Validation

Validation scripts are available as reviewed candidates under `ops/validation/`.
Their presence does not authorize execution.

Relevant candidate paths:

```text
ops/validation/validate-no-secrets.sh
ops/validation/validate-extension-manifests.sh
ops/validation/validate-workspace.sh
```

Do not present these paths as copy-ready commands. Any script invocation
requires separate exact authorization, including scope, working directory,
expected output, failure handling, and receipt location.

## Ownership

```text
Human owner: Jenn
Agent owner: Project Agent
Review required: yes for risky operations
```
