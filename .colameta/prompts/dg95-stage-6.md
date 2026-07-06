# Document Governance 9.5 - Stage 6 Prompt

Version: `dg95.6`
Name: `Stage 6: docctl trend`

## Objective

Add a read-only trend view over existing local snapshots so baseline drift
becomes visible over time.

## Allowed Local Write Scope

```text
control-plane/registry/docctl.py
control-plane/registry/test-docctl-trend.py
control-plane/registry/README.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-6-docctl-trend.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-6-docctl-trend.review.md
```

## Forbidden Actions

```text
Do not read or modify .env files, secrets, credentials, tokens, cookies, or state-private/.
Do not read or summarize private memory raw text or provider raw responses.
Do not modify auth, provider, runtime, or WORKSPACE_REGISTRY.yaml configuration.
Do not modify .colameta/memory.md, .colameta/runtime/, or .colameta/logs/.
Do not write snapshots as part of trend.
Do not start ColaMeta service.
Do not make provider calls.
Do not perform external writes.
Do not commit, push, tag, release, deploy, publish, or perform bulk move/delete/rename.
```

## Expected Deliverables

```text
read-only docctl trend view over existing snapshots
visibility for known/archive growth
four-week no-regression view when enough snapshots exist
tests for read-only trend behavior
README usage note
receipt and review evidence for Stage 6
```

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-trend.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Receipt And Review Requirement

Leave or update:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-6-docctl-trend.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-6-docctl-trend.review.md
```

## Stop Conditions

```text
Stop if trend would need to write snapshots.
Stop if trend would need provider calls, external state, or protected/P3 reads.
Stop if validation fails and the fix would exceed the allowed local write scope.
Stop before any service, provider, external write, or git operation.
```
