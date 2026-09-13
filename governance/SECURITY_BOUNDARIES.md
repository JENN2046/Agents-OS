# Security Boundaries

Entry clarification (`2026-09-13.1`): start with [root AGENTS.md](../AGENTS.md).
This file remains the security reference, not a competing operating entry.
Its A0–A4 permission labels are the legacy safety taxonomy; do not equate them
with the A0–A3 automation classes in root section 7. Apply the explicit behavior
and scope constraints, including root sections 2 and 5 and current user limits.
No new standing authorization or security-boundary relaxation is introduced.

This document defines the canonical hard boundaries of AGENTS OS Workspace.

Authoritative location:

```text
governance/SECURITY_BOUNDARIES.md
```

## Absolute Rules

Never commit, expose, print, summarize, or copy real secret values.

Protected secret-like files:

```text
.env
.env.*
config.env
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
credentials.json
token.json
```

Allowed template files:

```text
.env.example
config.env.example
*.template
*.example
```

Allowed template file patterns are examples only. They do not authorize active
local configuration files or real secret values.

## Private State Boundary

Private state belongs in:

```text
state-private/
```

It may contain memory, runtime notes, local audit traces, and project data.

It must not be merged into upstream-tracking code.

## Git Boundary

Default blocked:

```text
git push
git tag
git release
git deploy
git reset --hard
git clean -fd
history rewrite
```

## Runtime Boundary

Execution must pass through:

```text
TaskEnvelope
codex-router
Bounded-High-Autonomy
Approval Gate
Runtime / Extension / Bridge
Audit Event
Receipt
```

## Permission Levels

```text
A0  Read / see
A1  Light self-maintenance
A2  Housekeeping with log / receipt
A3a Low-impact real action under standing authorization
A3b Medium-impact real action under explicit trial authorization
A3c High-impact action with full gate + Jenn confirmation
A4  Forbidden / proposal path only
```

## High-Risk Areas

```text
runtime/VCPToolBox/Plugin.js
runtime/VCPToolBox/adminServer.js
runtime/VCPToolBox/routes/
runtime/VCPToolBox/modules/
runtime/VCPToolBox/AdminPanel-Vue/
state-private/secrets/
state-private/MEMORY.md
domains/Photo_Studio_OS*
governance/Codex_Autonomous_Work_Harness/
governance/Bounded-High-Autonomy/
```

## Report Format For Risk

When risk is found:

```yaml
risk:
  path:
  type:
  severity: low / medium / high / critical
  reason:
  recommended_action:
  stop_required: yes/no
```

If risk is high or critical, stop and report before continuing.
