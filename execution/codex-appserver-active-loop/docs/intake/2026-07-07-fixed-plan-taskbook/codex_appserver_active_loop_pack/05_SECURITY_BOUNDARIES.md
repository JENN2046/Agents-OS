# 05｜Security Boundaries

## 1. Boundary Model

There are two different permission layers:

| Layer | Permission |
|---|---|
| Implementation agent | May write only inside target project repo |
| Managed Worker / Reviewer sessions | Must default to readOnly restricted synthetic workspace |

Do not mix these layers.

## 2. Implementation Write Boundary

Allowed path:

```text
A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
```

Forbidden:

```text
A:\AGENTS_OS_Workspace root
VCPToolBox
codex-router
codex-memory
Photo_Studio_OS
state-private
user profile directories
global Codex config
system config
```

## 3. Managed Runtime Boundary

MVP managed sessions must use:

```json
{
  "type": "readOnly",
  "access": {
    "type": "restricted",
    "includePlatformDefaults": true,
    "readableRoots": ["<project>/data/synthetic-workspace"]
  }
}
```

No unrestricted read roots.

## 4. Denied Paths

Any path containing these terms must be rejected:

```text
.env
secrets
credentials
tokens
cookies
.ssh
state-private
```

## 5. Forbidden Actions

```text
push
deploy
release
tag
commit
read secrets
read env values
read credentials
read browser cookies
read SSH keys
modify outside target project repo
```

## 6. Forbidden APIs / Methods

```text
Workspace Agents API
Responses API
browser automation
WebSocket transport in MVP
thread/shellCommand
command/exec
command/exec/write
process/*
dangerFullAccess
full_access
capabilities.experimentalApi=true
```

## 7. Why `thread/shellCommand` Is Forbidden

`thread/shellCommand` runs outside the sandbox with full access and does not inherit thread sandbox policy. That makes it incompatible with the MVP boundary.

## 8. Why `command/exec` Is Forbidden

The MVP tests the App Server event loop, not general shell execution. `command/exec` adds unnecessary execution surface and should be excluded until there is a separate command policy.

## 9. Why WebSocket Is Deferred

WebSocket transport is not needed for MVP. It adds network exposure and authentication concerns. stdio is sufficient to prove the event loop.

## 10. Approval Policy

Default server-request behavior:

```text
known safe request → handle
file change request → decline in MVP
unknown request → decline if possible, otherwise BLOCK
write request → decline in MVP
human-level request → HUMAN_GATE_REQUIRED
```

## 11. Secrets Rule

Do not print, store, summarize, hash, or transform secret values. Secret-like paths must be rejected before file read.
