# Prompt Catalogs

Status: prompt catalog index. Guidance only; not authorization to activate,
install, source, import, apply, or execute any prompt.

Source reference:

```text
A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\README.AGENTS_OS.md
```

Canonical security authority:

```text
governance/SECURITY_BOUNDARIES.md
```

## Purpose

This directory catalogs reusable prompt guidance for agents, Codex, reviewers,
and operators. It is an index and planning surface, not an active prompt
registry and not behavior authority.

## Included Catalog Files

```text
agents/README.md
codex/README.md
reference/legacy-listed-prompts.md
```

## Not Included In This Batch

```text
review/
templates/
active prompt files
private prompts
private memory
AGENTS overrides
runtime prompts
extension-specific prompt assets
```

`review/` and `templates/` were listed in the source README but were not
observed as source directories. Do not create them from names alone.

## Authority Boundary

Prompt catalogs do not override:

```text
current system, developer, or user instructions
checked-in AGENTS.md files
_ROOT_POLICY.md
_DIRECTORY_PRINCIPLES.md
governance/SECURITY_BOUNDARIES.md
explicit task authorization
```

Prompt catalogs must not authorize:

```text
secret access
secret printing
push
release
deploy
branch movement
direct main modification
background execution
hidden network activity
bypassing approval
permission self-expansion
private-state access
```

## Validation Boundary

Validation script invocation requires separate explicit approval.

This catalog intentionally does not include copy-ready validation commands.

## Review Boundary

Any future prompt file, prompt activation package, private prompt, memory prompt,
or behavior-changing instruction requires its own scoped review, authorization,
and receipt.
