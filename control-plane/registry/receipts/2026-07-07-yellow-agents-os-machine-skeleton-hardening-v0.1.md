# AGENTS OS Machine Skeleton Hardening v0.1 Receipt

Status: accepted
Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Scope: local hardening fixes for Machine Skeleton v0.1

## Result

- Added queue path preflight before Machine reads queue input.
- Blocked protected and outside-workspace queue paths.
- Expanded denied-signal coverage for external write, database write, publish,
  deploy, GitHub, Notion, email, upload, and package publication language.
- Added `actionable` preview semantics.
- Wired `queue-item.schema.json` `required_false` into validation.
- Expanded Machine tests to `cases=12 failures=0`.

## Boundaries

- No `state-private/` content was read.
- No Task Producer was implemented.
- No Active Work Queue mutation was performed.
- No service, executor, provider call, runtime/plugin activation, VCPToolBox
  activation, external write, formal Memory write, Git push/tag/release/deploy,
  publish, or history rewrite was performed.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw
  response, active runtime config values, or raw logs were read or output.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/test-machine.py
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py validate
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py --queue state-private/queue.md inspect-queue --json
PYTHONDONTWRITEBYTECODE=1 python3 execution/agents-os-machine/machine.py --queue /tmp/queue.md inspect-queue --json
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```
