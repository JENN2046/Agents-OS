# Runbook: Onboard New Agent

Status: ordinary runbook guidance. This document is not authorization to
activate an agent identity, grant permissions, or access private state.

Source reference:

```text
A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\onboard-new-agent.md
```

Canonical security authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Required Planning Artifacts

```text
identity page
room or workspace context
Agent file
capability card
memory rules
permissions
review path
```

## Placement Rule

Agent-pack placement is pending a separate extension-assets migration decision.

Do not present this historical source path as current WSL truth:

```text
extensions/Jenn-VCP-Extensions/agent-packs/
```

Do not convert this observed WSL extension root into a final agent-pack target
in this batch:

```text
extensions/vcp-toolbox-jenn/
```

## Private State

Private state remains governed by:

```text
state-private/
governance/SECURITY_BOUNDARIES.md
```

This runbook may mention private state only as a boundary. It does not authorize
copying, reading, exporting, summarizing, or moving private state.

## Procedure

1. Draft the agent identity and purpose.
2. Record the intended room or workspace context.
3. Draft the capability card and requested permissions.
4. Define memory rules without copying private memory content.
5. Record review requirements and approval gates.
6. Wait for a separate extension-assets decision before choosing final package
   placement.

## Forbidden

```text
self-expansion of permissions
unreviewed access to secrets
unreviewed private-state access
modifying another Agent identity without gate
activation without explicit approval
```
