# AGENTS OS Task Producer Skeleton v0.1

This directory contains the first local AGENTS OS Task Producer skeleton.

It is a preview-only candidate task producer. It turns explicit intent text or
allowlisted local review/report documents into candidate task JSON.

It is not a queue writer, queue promoter, executor, service, provider adapter,
Memory writer, VCPToolBox starter, ColaMeta runner, plugin activator, or Git
publisher.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-intent --intent "Build local governance task" --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-review --source control-plane/registry/reports/2026-07-07-agents-os-machine-to-task-producer-queue-transition-v0.1.md --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/test-producer.py
```

## Output Rule

Producer output is candidate JSON only:

```text
producer_generated=true
status=candidate_preview
requires_nobao_review=true
review_status=pending
execution_authorized=false
json_output_authoritative=true
```

The producer never writes the Active Work Queue and never promotes any item to
`NOW`. Nobao may review a candidate and separately decide whether a governance
queue update is safe.

## Boundaries

The skeleton must keep these capabilities disabled:

```text
queue_write_authorized=false
execution_authorized=false
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
external_write_authorized=false
memory_write_authorized=false
runtime_plugin_activation_authorized=false
plugin_execution_authorized=false
```

Review/report input paths are preflighted before read. Protected paths such as
`state-private/`, secrets, credentials, tokens, cookies, `.env`, and files
outside the workspace are blocked before content is read.

Allowlisted file input is limited to Markdown under:

```text
control-plane/registry/reports/
control-plane/registry/reviews/
```

Source body raw content is not included in candidate output. Review/report
candidate output includes only path metadata, headings, counts, risk signals,
and the candidate task fields.
