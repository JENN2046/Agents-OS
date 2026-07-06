# AGENTS OS Governance Friction Fix Receipt v0.1

Status: accepted
Date: 2026-07-06
Owner: Jenn
Agent steward: Nobao
Scope: local fix for review findings after Git baseline

## Result

- Clarified that Red `workspace-write` means external runner / executor workspace-write, not ordinary scoped local file edits.
- Added root `README.md` and `WORKSPACE_MANIFEST.md` as lightweight orientation documents.
- Moved the root-level reading notes draft to `labs/agents-os-reading-notes-draft.md` and marked it historical, not active authority.
- Updated `CURRENT_STATE.md` handoff wording after Git baseline completion.
- Registered the new/relocated governance documents and this evidence in the document registry.

## Boundaries

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
