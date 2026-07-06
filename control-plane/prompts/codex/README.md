# Codex Prompt Catalog

Status: Codex prompt catalog. Guidance only; not authorization to change active
Codex behavior, execute work, modify repositories, or run prompts.

Source reference:

```text
A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\codex\README.AGENTS_OS.md
```

Canonical security authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Purpose

This catalog records Codex prompt planning areas for repository audit,
extraction, synchronization review, validation review, and execution review.
It does not contain active Codex prompt files.

## Listed Prompt Names

The source README listed these names, but the files were not observed during
inventory:

```text
CODEX_MASTER_PROMPT.md
CODEX_REPO_AUDITOR.md
CODEX_EXTENSION_EXTRACTOR.md
CODEX_VCP_SYNC_AUDITOR.md
CODEX_NO_SECRET_RULES.md
```

They are preserved only in:

```text
../reference/legacy-listed-prompts.md
```

Do not create these files from catalog names alone.

## Codex Authority Boundary

This catalog does not override active Codex instructions, checked-in
`AGENTS.md`, governance gates, security boundaries, or the current user task.

Codex prompt catalogs must not authorize:

```text
secret access
secret disclosure
direct main modification
background execution
unreviewed push
release
deploy
remote writes
branch movement
destructive actions
```

Codex work remains audit-first unless a specific local action is explicitly
authorized. High-risk actions must stop for review and receipt.

## Validation Boundary

Validation script invocation requires separate explicit approval.

This catalog intentionally does not include copy-ready validation commands.

## Owner

```text
Human owner: Jenn
Catalog reviewer: Codex Runtime Operator / Review Agent
Review required: yes
```
