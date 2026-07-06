# Document Governance 9.5 - Stage 2 Prompt

Version: `dg95.2`
Name: `Stage 2: docctl intake`

## Objective

Add a dry-run intake route so new document files receive an explicit route
before they become backlog.

## Allowed Local Write Scope

```text
control-plane/registry/docctl.py
control-plane/registry/test-docctl-intake.py
control-plane/registry/README.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-2-docctl-intake.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-2-docctl-intake.review.md
```

## Forbidden Actions

```text
Do not read or modify .env files, secrets, credentials, tokens, cookies, or state-private/.
Do not read or summarize private memory raw text or provider raw responses.
Do not modify auth, provider, runtime, or WORKSPACE_REGISTRY.yaml configuration.
Do not modify .colameta/memory.md, .colameta/runtime/, or .colameta/logs/.
Do not write registry entries from intake.
Do not move, delete, or rename files.
Do not start ColaMeta service.
Do not make provider calls.
Do not perform external writes.
Do not commit, push, tag, release, deploy, publish, or perform bulk move/delete/rename.
```

## Expected Deliverables

```text
docctl intake command or subcommand that is dry-run only
structured intake classifications for registered, ignored_by_rule, future_backlog, blocked, and unknown paths
protected/P3 path blocking before content reading
tests for dry-run behavior and protected path handling
README usage note
receipt and review evidence for Stage 2
```

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-intake.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-doctor.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Receipt And Review Requirement

Leave or update:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-2-docctl-intake.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-2-docctl-intake.review.md
```

## Stop Conditions

```text
Stop if intake would need to write registry data.
Stop if intake would need to read protected/P3 file contents.
Stop if validation fails and the fix would exceed the allowed local write scope.
Stop before any service, provider, external write, or git operation.
```
