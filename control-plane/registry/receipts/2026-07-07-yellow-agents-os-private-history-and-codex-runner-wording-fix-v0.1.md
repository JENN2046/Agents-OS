# AGENTS OS Private History And Codex Runner Wording Fix Receipt v0.1

Status: accepted
Date: 2026-07-07
Owner: Jenn
Agent steward: Nobao
Scope: local governance fix for private Git history boundary and Codex runner wording

## Result

- Redacted Notion page URLs from current tracked Git files.
- Marked the root Git repository private-local by default because local history has contained private Notion page URLs and working synthesis material.
- Added a no-external-push boundary until a separate private-history review or history-scrub gate is authorized.
- Narrowed `real Codex CLI execution` wording to external Codex CLI subprocess / autonomous Codex runner invocation.

## Boundaries

- No Git history rewrite was performed.
- No remote was added and no push was performed.
- No `state-private/` content was read.
- No VCPToolBox source or active config was modified.
- No secrets, tokens, cookies, credentials, private raw memory, provider raw response, active runtime config values, or raw logs were read or output.
- No service, executor, provider call, deploy, release, publish, tag, push, or destructive cleanup was performed.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
```
