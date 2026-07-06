# AGENTS OS Machine Skeleton v0.1

This directory contains the first local AGENTS OS machine skeleton.

It is a preview-only control machine. It reads the Active Work Queue, confirms
the single `NOW` item, emits a normalized queue model, and derives a temporary
task-envelope preview for validation.

It is not an executor, service, provider adapter, Memory writer, VCPToolBox
starter, ColaMeta runner, or task producer.

## Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py inspect-queue --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py preview-now --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/test-machine.py
```

## Review Rule

All machine outputs are preview/draft until reviewed.

```text
machine_generated=true
status=preview_or_draft
requires_nobao_review=true
review_status=pending
execution_authorized=false
```

Machine self-check is necessary but never sufficient for execution. Nobao may
accept low-risk local work. Jenn must decide P3, provider, runtime/plugin,
external write, Memory, Git push/tag/release/deploy/history rewrite, identity,
and direction changes.

## Boundaries

The skeleton must keep these capabilities disabled:

```text
provider_call_authorized=false
service_start_authorized=false
executor_run_authorized=false
external_write_authorized=false
memory_write_authorized=false
runtime_plugin_activation_authorized=false
```

The Markdown task-envelope preview is generated only as a temporary validation
artifact and is deleted after validation. The JSON preview output is the
authoritative machine output.
