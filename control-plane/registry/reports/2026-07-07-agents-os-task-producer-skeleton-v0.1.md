# AGENTS OS Task Producer Skeleton v0.1

Date: 2026-07-07
Status: accepted
Owner: Jenn
Agent steward: Nobao
Scope: local preview-only candidate task producer for AGENTS OS

## Result

AGENTS OS now has a minimal local Task Producer skeleton at:

```text
execution/agents-os-task-producer/
```

It can:

```text
create candidate task JSON from explicit intent text
create candidate task JSON from allowlisted review/report Markdown files
preflight review/report input paths before reading
block protected paths before content read
mark risky candidates with risk_signals
require Nobao review for every candidate
require Jenn decision for P3-like signals
validate candidate task JSON
run docctl status and doctor
```

It cannot:

```text
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
execution/agents-os-task-producer/README.md
execution/agents-os-task-producer/producer-manifest.json
execution/agents-os-task-producer/candidate-task.schema.json
execution/agents-os-task-producer/producer.py
execution/agents-os-task-producer/test-producer.py
```

## Command Surface

```text
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-intent --intent "Build local governance task" --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-review --source control-plane/registry/reports/2026-07-07-agents-os-machine-to-task-producer-queue-transition-v0.1.md --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/test-producer.py
```

## Review Rule

Every producer output remains candidate-only:

```text
producer_generated=true
status=candidate_preview
requires_nobao_review=true
review_status=pending
execution_authorized=false
queue_write_authorized=false
json_output_authoritative=true
```

Task Producer self-check is necessary but never sufficient for queue adoption
or execution. Nobao may review candidate tasks and perform a separate safe
governance queue update. Jenn remains the required decision point for P3,
provider, runtime/plugin, external write, Memory, Git push/tag/release/deploy,
history rewrite, identity, and direction changes.

## Validation Summary

```text
test-producer: PASS cases=14 failures=0
from-intent preview: PASS blocked=false requires_nobao_review=true execution_authorized=false queue_write=false
from-review preview: PASS source_raw_content_included=false requires_nobao_review=true execution_authorized=false
producer validate: PASS
machine inspect-queue: PASS now=1
machine preview-now: PASS source_item=ColaMeta Executor Readiness Reconciliation actionable=true execution_authorized=false
docctl status: PASS
docctl doctor: PASS
```

## Boundary

No `state-private/` content was read. No secrets, tokens, cookies, credentials,
private raw memory, provider raw response, active runtime config values, or raw
logs were read or output. No service was started. No executor, provider,
VCPToolBox, plugin, external write, formal Memory write, Git push, tag, release,
deploy, publish, or history rewrite was performed.

## Next

Use Machine preview on the new `NOW`: `ColaMeta Executor Readiness
Reconciliation`. Keep it preview-only and metadata-only.
