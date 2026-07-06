# Document Governance 9.5 - Stage 4 Prompt

Version: `dg95.4`
Name: `Stage 4: docctl impact`

## Objective

Add a read-only impact view that lists which registry documents are affected by
changed paths.

## Allowed Local Write Scope

```text
control-plane/registry/docctl.py
control-plane/registry/test-docctl-impact.py
control-plane/registry/README.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-4-docctl-impact.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-4-docctl-impact.review.md
```

## Forbidden Actions

```text
Do not read or modify .env files, secrets, credentials, tokens, cookies, or state-private/.
Do not read or summarize private memory raw text or provider raw responses.
Do not modify auth, provider, runtime, or WORKSPACE_REGISTRY.yaml configuration.
Do not modify .colameta/memory.md, .colameta/runtime/, or .colameta/logs/.
Do not write impact results to registry files.
Do not start ColaMeta service.
Do not make provider calls.
Do not perform external writes.
Do not commit, push, tag, release, deploy, publish, or perform bulk move/delete/rename.
```

## Expected Deliverables

```text
read-only docctl impact view
affected-document mapping for changed registry and evidence paths
protected/P3 changed path blocking
JSON output suitable for future scoring
tests for path impact behavior
README usage note
receipt and review evidence for Stage 4
```

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-impact.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
```

## Receipt And Review Requirement

Leave or update:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-4-docctl-impact.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-4-docctl-impact.review.md
```

## Stop Conditions

```text
Stop if impact would write files or mutate registries.
Stop if impact would read protected/P3 file contents.
Stop if validation fails and the fix would exceed the allowed local write scope.
Stop before any service, provider, external write, or git operation.
```
