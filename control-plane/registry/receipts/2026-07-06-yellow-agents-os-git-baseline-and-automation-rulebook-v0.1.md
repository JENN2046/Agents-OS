# AGENTS OS Git Baseline And Automation Rulebook Receipt v0.1

Status: accepted
Date: 2026-07-06
Owner: Jenn
Agent steward: Nobao
Scope: local governance baseline and prohibited-first automation rule update

## Result

- Implemented the prohibited-first automation wording in the root `AGENTS.md`.
- Updated `governance/automation/AGENTS_OS_AUTOMATION_RULEBOOK.md` so safe local work defaults to `inspect -> act -> validate -> report`.
- Expanded root `.gitignore` to keep private state, runtime source checkouts, dependency/build outputs, caches, logs, databases, and secret/auth/provider files out of the local Git baseline.
- Updated `CURRENT_STATE.md` to record the local Git baseline and the simplified automation model.
- Initialized the root workspace as a local Git repository and created a scoped first commit.

## Boundaries

- `runtime/VCPToolBox` was not modified.
- `state-private/` was not read.
- Secrets, tokens, cookies, credentials, private raw memory, provider raw responses, and raw logs were not read or output.
- No `.env`, `config.env`, auth, provider, or runtime configuration was read or modified.
- No service was started.
- No executor, plugin, provider call, deploy, release, publish, tag, push, or destructive cleanup was performed.
- `git add .` was not used for the baseline.

## Validation

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
```

## Evidence

- Receipt: `control-plane/registry/receipts/2026-07-06-yellow-agents-os-git-baseline-and-automation-rulebook-v0.1.md`
- Review: `control-plane/registry/reviews/2026-07-06-yellow-agents-os-git-baseline-and-automation-rulebook-v0.1.review.md`
