# Document Governance 9.5 - Stage 0 Prompt

Version: `dg95.0`
Name: `Stage 0: Baseline Freeze And Read-Only Contract`

## Objective

Freeze the current document-governance baseline and make the `docctl doctor`
read-only contract explicit before stricter rules are added.

If the Stage 0 deliverables already exist, verify them and make only the
smallest needed update inside the allowed scope.

## Allowed Local Write Scope

```text
control-plane/registry/drafts/2026-07-01-document-governance-9.5-plan.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-0-baseline-freeze.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-0-baseline-freeze.review.md
```

## Forbidden Actions

```text
Do not read or modify .env files, secrets, credentials, tokens, cookies, or state-private/.
Do not read or summarize private memory raw text or provider raw responses.
Do not modify auth, provider, runtime, or WORKSPACE_REGISTRY.yaml configuration.
Do not modify .colameta/memory.md, .colameta/runtime/, or .colameta/logs/.
Do not start ColaMeta service.
Do not run executor workflows.
Do not make provider calls.
Do not perform external writes.
Do not commit, push, tag, release, deploy, publish, or perform bulk move/delete/rename.
```

## Expected Deliverables

```text
baseline freeze note with concrete docctl doctor counts
read-only contract note for docctl doctor
P3 deny gate statement for future docctl commands
plan-fix dry-run-only note and apply-fix deferred note
receipt and review evidence for Stage 0
```

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-doctor.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Receipt And Review Requirement

Leave or update:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-0-baseline-freeze.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-0-baseline-freeze.review.md
```

## Stop Conditions

```text
Stop if a required action touches a forbidden path or P3 boundary.
Stop if docctl doctor is no longer read-only.
Stop if validation fails and the fix would exceed the allowed local write scope.
Stop before any service, executor, provider, external write, or git operation.
```
