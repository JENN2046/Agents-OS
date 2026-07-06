# Document Governance 9.5 - Stage 1 Prompt

Version: `dg95.1`
Name: `Stage 1: Registry Schema And Lifecycle Hardening`

## Objective

Make registry fields, lifecycle statuses, transition rules, and migration
behavior stricter before scoring is implemented.

## Allowed Local Write Scope

```text
control-plane/registry/validate-document-registry.py
control-plane/registry/test-document-registry-validator.py
control-plane/registry/drafts/document-registry.v0.1.example.yaml
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-1-schema-lifecycle.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-1-schema-lifecycle.review.md
```

## Forbidden Actions

```text
Do not read or modify .env files, secrets, credentials, tokens, cookies, or state-private/.
Do not read or summarize private memory raw text or provider raw responses.
Do not modify auth, provider, runtime, or WORKSPACE_REGISTRY.yaml configuration.
Do not modify .colameta/memory.md, .colameta/runtime/, or .colameta/logs/.
Do not start ColaMeta service.
Do not make provider calls.
Do not perform external writes.
Do not commit, push, tag, release, deploy, publish, or perform bulk move/delete/rename.
```

## Expected Deliverables

```text
required field matrix for registry records
lifecycle state machine using the current allowed statuses
allowed and blocked transition validation
migration behavior for legacy gaps versus new records
adversarial fixtures for valid and invalid lifecycle transitions
receipt and review evidence for Stage 1
```

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-document-registry-validator.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Receipt And Review Requirement

Leave or update:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-1-schema-lifecycle.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-1-schema-lifecycle.review.md
```

## Stop Conditions

```text
Stop if stricter schema rules would invalidate the current accepted registry without a migration warning path.
Stop if a required action touches a forbidden path or P3 boundary.
Stop if validation fails and the fix would exceed the allowed local write scope.
Stop before any service, provider, external write, or git operation.
```
