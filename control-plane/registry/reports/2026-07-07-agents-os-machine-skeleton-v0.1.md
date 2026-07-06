# AGENTS OS Machine Skeleton v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local preview-only control machine for Active Work Queue consumption

## Result

AGENTS OS now has a minimal local machine skeleton at:

```text
execution/agents-os-machine/
```

It can:

```text
inspect Active Work Queue
normalize queue Markdown into JSON
preflight queue input paths before reading
confirm exactly one NOW item
generate NOW preview JSON
mark blocked previews as actionable=false
derive a temporary task-envelope preview
validate the temporary task envelope
run docctl status and doctor
require Nobao review before execution
```

It cannot:

```text
produce new tasks
modify Active Work Queue
promote NEXT to NOW
authorize execution
run executor
start services
call providers
activate runtime or plugins
write formal Memory
read state-private
perform external writes
push/tag/release/deploy/publish
rewrite Git history
```

## Files

```text
execution/agents-os-machine/README.md
execution/agents-os-machine/machine-manifest.json
execution/agents-os-machine/queue-item.schema.json
execution/agents-os-machine/machine.py
execution/agents-os-machine/test-machine.py
```

## Command Surface

```text
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py inspect-queue --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py preview-now --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/test-machine.py
```

## Review Rule

Every machine output remains a preview/draft:

```text
machine_generated=true
status=preview_or_draft
requires_nobao_review=true
review_status=pending
execution_authorized=false
```

Machine self-check is necessary but never sufficient for execution. Nobao may
accept low-risk local work. Jenn remains the required decision point for P3,
provider, runtime/plugin, external write, Memory, Git push/tag/release/deploy,
history rewrite, identity, and direction changes.

## Validation Summary

```text
test-machine: PASS cases=12 failures=0
machine inspect-queue: PASS now=1 next=2 later=4 blocked=6 closed=5
machine preview-now: PASS execution_authorized=false requires_nobao_review=true actionable=true
machine validate: PASS
task-envelope preview temporary file cleaned=true
docctl status: PASS
docctl doctor: PASS
```

## Boundary

No `state-private/` content was read. No secrets, tokens, cookies, credentials,
private raw memory, provider raw response, active runtime config values, or raw
logs were read or output. No service was started. No executor, provider,
VCPToolBox, plugin, external write, Memory write, Git push, tag, release,
deploy, publish, or history rewrite was performed.

## Next

Use the machine to preview the active `NOW` output, then let Nobao review the
preview. Task Producer remains a next-stage candidate after the machine can
stably consume the queue.
