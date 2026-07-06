# AGENTS OS Queue Manager Reviewed Mutation Gate v0.1 Receipt

Status: accepted
Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Scope: local implementation of reviewed queue mutation gate

## Result

- Added reviewed queue mutation schema and validation.
- Added accepted Nobao review requirement.
- Added exactly-one-NOW guard.
- Added P3 NEXT promotion guard.
- Added queue mutation preview mode.
- Added fixture-only apply test for workspace-local queue mutation.
- Kept auto-promote unauthorized.
- Advanced Active Work Queue to the failure handling stage.

## Boundaries

- Live Active Work Queue was not mutated by the Queue Manager code path.
- No auto-promote was authorized.
- No provider call, service start, runtime/plugin activation, external write,
  formal Memory write, or real executor run was performed.
- No `state-private/` content was read.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  response, active runtime config values, or raw logs were read or output.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/test-control-chain.py
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-control-chain/control_chain.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/test-machine.py
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-task-producer/test-producer.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```
