# Document Governance 9.5 - Stage 5 Prompt

Version: `dg95.5`
Name: `Stage 5: docctl score`

## Objective

Add a versioned document-governance score only after schema, lifecycle, intake,
exception, and impact rules are stable.

## Allowed Local Write Scope

```text
control-plane/registry/docctl.py
control-plane/registry/test-docctl-score.py
control-plane/registry/SCORECARD.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-5-docctl-score.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-5-docctl-score.review.md
```

## Forbidden Actions

```text
Do not read or modify .env files, secrets, credentials, tokens, cookies, or state-private/.
Do not read or summarize private memory raw text or provider raw responses.
Do not modify auth, provider, runtime, or WORKSPACE_REGISTRY.yaml configuration.
Do not modify .colameta/memory.md, .colameta/runtime/, or .colameta/logs/.
Do not allow score output to hide hard gate failures.
Do not start ColaMeta service.
Do not make provider calls.
Do not perform external writes.
Do not commit, push, tag, release, deploy, publish, or perform bulk move/delete/rename.
```

## Expected Deliverables

```text
versioned read-only docctl score view
hard gates for unregistered files, failures, and blocking warnings
separation between blocking_warn and advisory_warn
explainable deductions
adversarial fixtures that lower or block the score
SCORECARD.md update
receipt and review evidence for Stage 5
```

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-score.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Receipt And Review Requirement

Leave or update:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-5-docctl-score.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-5-docctl-score.review.md
```

## Stop Conditions

```text
Stop if the score can pass while hard gates fail.
Stop if score requires provider calls, external state, or write actions.
Stop if validation fails and the fix would exceed the allowed local write scope.
Stop before any service, provider, external write, or git operation.
```
