# Phase 2 Batch 3 Env Template Patch Plan - 2026-06-27

Status: patch plan only; no migration performed.

Notice: This document lists the intended Batch 3 env-template patch and its
strict preflight checks. It is not migration authorization, not authorization
to copy files yet, and not authorization to create or modify any active
env/config file.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 3 |
| Batch name | Env template |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Included source area | `A:\AGENTS_OS_Workspace\templates` |
| Included asset types | One env example template only |
| Excluded asset types | Active env files, active config files, security templates, runbooks, scripts, registry files, extension packages, private state, logs, cache, runtime artifacts |
| Migration performed | No |
| Validation executed | No patch validation yet |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/` | Isolated target directory for sanitized env example templates. |

Do not create any active env/config filename in this batch.

## Planned File Changes

| Action | Target file | Source file | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env.example.template` | `A:\AGENTS_OS_Workspace\templates\config.env.example.template` | Preserve as example-only `.template` file after strict live-secret and placeholder-only review. |

No existing target file is planned to be modified in this batch.

## Explicitly Out Of Scope

| Path or asset | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/.env` | Active env filename; forbidden in this batch. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/.env.example` | Not the approved target filename for this batch. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env` | Active config-style filename; forbidden in this batch. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env.example` | Not the approved target filename for this batch. |
| `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | Reserved for a later security-template batch. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\*` | Reserved for a later runbook batch. |
| Any source or migrated validator script | Scripts are outside this batch and must not be run here. |
| Any active config, active registry, extension package, private state, logs, cache, or runtime artifact | Outside env-template scope and higher risk. |

## Strict Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm source file exists | Check `A:\AGENTS_OS_Workspace\templates\config.env.example.template`. | Source file exists and size is recorded. |
| Reconfirm target file is absent | Check `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env.example.template`. | Target file does not exist. |
| Reconfirm target directory state | Check `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/`. | Directory may be absent or empty; stop if it contains unrelated user work that could be affected. |
| Reconfirm forbidden env/config targets are absent or untouched | Check `.env`, `.env.example`, `config.env`, and `config.env.example` under the target env directory. | None are created or modified by this batch. |
| Live-secret pattern scan | Scan source for real-looking API keys, tokens, passwords, credentials, private endpoints, and provider key patterns. | No live-secret pattern is found. |
| Placeholder-only assignment review | Inspect every non-comment assignment. | Every variable name is prefixed with `EXAMPLE_` and every value is example-only or placeholder-only. |
| Active-config promotion review | Inspect filename and target path. | Filename remains exactly `config.env.example.template`; no `.env`, `.env.example`, `config.env`, or `config.env.example` target is introduced. |
| Example-only comment review | Inspect source and planned target header. | File clearly says it is example-only and must not contain real secrets. |
| Secret wording review | Inspect any token/secret words. | Matches are labels or placeholders only, not live values. |

## Planned Content Rules

- Target filename must remain `config.env.example.template`.
- Target file must stay under `control-plane/templates/env/`.
- Target file must remain example-only and must not be loaded as active local
  configuration.
- Variable names must remain `EXAMPLE_*`.
- Values must remain placeholders or invalid/example values.
- Do not create `.env`, `.env.example`, `config.env`, or `config.env.example`.
- Do not copy security templates, runbooks, scripts, registry files, extension
  packages, private state, logs, cache, or runtime artifacts.
- Do not run validator scripts.

## Post-Patch Validation Plan

| Validation | Command or method | Notes |
| --- | --- | --- |
| Target file list check | Inspect `control-plane/templates/env` after patch. | Confirm only `config.env.example.template` was created there. |
| Forbidden env/config absence check | Check `.env`, `.env.example`, `config.env`, and `config.env.example`. | Confirm no active env/config filename exists. |
| Content equality or controlled-comment check | Compare source and target content. | Source values should be preserved unless only example-only comments are added. |
| Placeholder-only check | Inspect non-comment assignments. | Confirm all variable names remain `EXAMPLE_*`. |
| Live-secret pattern scan | Scan target content. | No live-secret pattern should be present. |
| Diff or content review | Inspect changed files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run source or migrated validator scripts in Batch 3.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-3-env-template-receipt-2026-06-27.md
```

The receipt should record:

- Exact authorization wording.
- Source file read.
- Target directory created.
- Target file created.
- Files explicitly skipped.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If Batch 3 is later applied and must be rolled back, remove only the file
created by that patch after confirming no later user work depends on it:

```text
control-plane/templates/env/config.env.example.template
```

Rollback must not remove directories that later contain unrelated user work.

## Stop Conditions

- Stop if the selected source file is missing.
- Stop if the planned target file already exists.
- Stop if the target env directory contains unrelated user work that would be
  affected.
- Stop if any active env/config filename would be created or modified.
- Stop if any real secret, token, key, credential, password, private endpoint,
  or private account value is found.
- Stop if any non-comment assignment is not clearly example-only.
- Stop if the filename would be changed away from `config.env.example.template`.
- Stop before copying security templates, runbooks, scripts, active config,
  registry files, extension packages, private state, logs, cache, or runtime
  artifacts.

## Related Documents

- `phase-2-batch-3-env-template-candidate-selection-2026-06-27.md`
- `phase-2-batch-2-ordinary-templates-patch-plan-2026-06-27.md`
- `phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `../decisions/templates-targets-2026-06-27.md`
- `../receipts/rules-assets-batch-2-ordinary-templates-receipt-2026-06-27.md`
