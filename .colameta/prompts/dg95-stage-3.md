# Document Governance 9.5 - Stage 3 Prompt

Version: `dg95.3`
Name: `Stage 3: Exception Governance For known/archive`

## Objective

Make `known_external_scope` and `archive_note` entries reviewable so they cannot
hide ordinary backlog.

## Allowed Local Write Scope

```text
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
control-plane/registry/validate-federated-document-registry.py
control-plane/registry/test-federated-document-registry-validator.py
control-plane/registry/archive-notes/2026-07-01-grouped-historical-document-governance-backlog.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-3-exception-governance.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-3-exception-governance.review.md
```

## Forbidden Actions

```text
Do not read or modify .env files, secrets, credentials, tokens, cookies, or state-private/.
Do not read or summarize private memory raw text or provider raw responses.
Do not modify auth, provider, runtime, or WORKSPACE_REGISTRY.yaml configuration.
Do not modify .colameta/memory.md, .colameta/runtime/, or .colameta/logs/.
Do not use known_external_scope or archive_note to hide ordinary current documents.
Do not start ColaMeta service.
Do not make provider calls.
Do not perform external writes.
Do not commit, push, tag, release, deploy, publish, or perform bulk move/delete/rename.
```

## Expected Deliverables

```text
known_external_scope requirements for reason, governing route or owner, and review trigger
archive_note requirements for why archived, replacement or no-replacement reason, safe use, and review trigger
fixtures proving protected/P3 exception paths fail
fixtures proving ordinary current documents cannot be hidden as exceptions
receipt and review evidence for Stage 3
```

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-federated-document-registry-validator.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Receipt And Review Requirement

Leave or update:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-3-exception-governance.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-3-exception-governance.review.md
```

## Stop Conditions

```text
Stop if the change would expand known_external_scope automatically.
Stop if protected/P3 paths would be read before blocking.
Stop if validation fails and the fix would exceed the allowed local write scope.
Stop before any service, provider, external write, or git operation.
```
