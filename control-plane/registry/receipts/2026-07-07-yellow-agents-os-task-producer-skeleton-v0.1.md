# AGENTS OS Task Producer Skeleton v0.1 Receipt

Status: accepted
Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Scope: local implementation of preview-only AGENTS OS Task Producer Skeleton

## Result

- Created `execution/agents-os-task-producer/`.
- Implemented producer manifest, candidate task schema, CLI, tests, and README.
- Implemented `from-intent`, `from-review`, and `validate`.
- Kept JSON candidate output as authoritative.
- Required Nobao review for every candidate.
- Required Jenn decision for P3-like risk signals.
- Kept queue write, promotion, execution, provider, service, executor, plugin,
  external write, and Memory authorization false.
- Advanced the Active Work Queue to the next preview-only item after this
  implementation was complete.

## Boundaries

- Task Producer does not write the Active Work Queue.
- Task Producer does not promote `NEXT` to `NOW`.
- Task Producer does not authorize execution.
- No service, executor, provider call, runtime/plugin activation, VCPToolBox
  activation, external write, formal Memory write, Git push/tag/release/deploy,
  publish, or history rewrite was performed.
- No `state-private/` content was read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  response, active runtime config values, or raw logs were read or output.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/test-producer.py
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-intent --intent 'Build local governance task from Jenn intent.' --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py from-review --source control-plane/registry/reports/2026-07-07-agents-os-machine-to-task-producer-queue-transition-v0.1.md --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/producer.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py inspect-queue --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py preview-now --json
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```
