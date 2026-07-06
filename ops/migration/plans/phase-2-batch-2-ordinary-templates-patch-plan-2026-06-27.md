# Phase 2 Batch 2 Ordinary Templates Patch Plan - 2026-06-27

Status: patch plan only; no migration performed.

Notice: This document lists the intended Batch 2 ordinary-template patch and
its preflight checks. It is not migration authorization, not authorization to
copy files yet, and not authorization to migrate env templates, security
templates, runbooks, scripts, active config, registry files, or extension
packages.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 2 |
| Batch name | Ordinary templates |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Included source area | `A:\AGENTS_OS_Workspace\templates` |
| Included asset types | Template library README, generic README template, extension manifest example template |
| Excluded asset types | Env templates, security templates, runbooks, scripts, active config, registry files, extension packages, private state |
| Migration performed | No |
| Validation executed | No patch validation yet |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/` | Target-native home for reusable control-plane templates. |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/` | Holds ordinary project or directory templates. |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/` | Holds extension manifest or extension package templates. |

Do not create `control-plane/templates/env/` or
`control-plane/templates/security/` in this batch.

## Planned File Changes

| Action | Target file | Source file | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md` | `A:\AGENTS_OS_Workspace\templates\README.AGENTS_OS.md` | Rewrite/adapt as target-native template-library index; state that Batch 2 covers ordinary templates only. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/README.template.md` | `A:\AGENTS_OS_Workspace\templates\README.template.md` | Preserve template shape and conservative permission defaults; update stale `AGENTS_OS` layer wording to current WSL layout wording. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/jenn-extension.manifest.example.json` | `A:\AGENTS_OS_Workspace\templates\jenn-extension.manifest.example.json` | Copy only after JSON parse, required-field check against the Batch 1 schema, and secret-like value scan. |

No existing target file is planned to be modified in this batch.

## Explicitly Out Of Scope

| Path or asset | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\templates\config.env.example.template` | Deferred to a later env-template batch after placeholder-only review. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/env/config.env.example.template` | Not part of ordinary templates Batch 2. |
| `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | Deferred until aligned with `governance/SECURITY_BOUNDARIES.md`. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md` | Not part of ordinary templates Batch 2. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks/*` | Runbooks require a separate stale-path and authorization wording review. |
| Any source or migrated validator script | Scripts are outside this batch and must not be run here. |
| Any `.env`, `.env.*`, `config.env`, active config, active registry, or private state file | Outside ordinary template scope and higher risk. |

## Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm source files exist | Check all 3 selected source paths. | All selected source files exist and sizes are recorded. |
| Reconfirm target files are absent | Check all 3 planned target paths. | No planned target file already exists. |
| Reconfirm excluded target files are absent or untouched | Check env/security template targets if present. | Batch 2 does not create or modify excluded files. |
| Parse manifest example JSON | Use a local JSON parser. | `jenn-extension.manifest.example.json` parses successfully. |
| Check manifest required fields | Compare example keys with `control-plane/contracts/jenn-extension.manifest.schema.json` required fields. | Required fields are present: `schemaVersion`, `id`, `name`, `type`, `entrypoints`, `permissions`, `secretPolicy`. |
| Scan selected sources for secret-like values | Search selected files for `.env`, `secret`, `token`, `credential`, `password`, `api_key`, private data names, and live-looking values. | Any matches are placeholders, policy text, or conservative permission labels; no real secret values. |
| Review `README.template.md` layer wording | Inspect the layer section. | Old `AGENTS_OS` wording is replaced with current WSL layout wording in the target. |
| Review permission defaults | Inspect template permission table and manifest permissions. | Defaults remain conservative; no push, release, deploy, shell, or write escalation. |
| Review validation wording | Inspect target README/template validation sections. | No unavailable validator script is presented as a current runnable command. |

## Planned Content Rules

- Target README files must use target-native WSL wording.
- Templates must contain placeholders or examples only.
- `README.template.md` may keep a validation section, but command placeholders
  must stay non-executable examples unless separately reviewed.
- The extension manifest example may preserve example IDs and example URLs if
  they remain clearly example-only.
- Permission defaults must stay conservative.
- Batch 2 must not create env or security template targets.
- Batch 2 must not create active config or registry files.
- Batch 2 must not run validator scripts.

## Post-Patch Validation Plan

| Validation | Command or method | Notes |
| --- | --- | --- |
| Target file list check | Inspect `control-plane/templates` after patch. | Confirm only the 3 planned files were created. |
| JSON syntax check | Parse target `jenn-extension.manifest.example.json`. | Use local parser only. |
| Required-field check | Compare target manifest example with Batch 1 schema required fields. | Schema validation library is optional; required-field check is mandatory. |
| Secret-like scan | Search the 3 target files for sensitive names and live-looking values. | Report placeholder/policy matches separately from risks. |
| Excluded-file absence check | Confirm env and security template targets were not created. | Guard against scope drift. |
| Diff or content review | Inspect changed files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run source or migrated validator scripts in Batch 2.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-2-ordinary-templates-receipt-2026-06-27.md
```

The receipt should record:

- Exact authorization wording.
- Source files read.
- Target directories created.
- Target files created.
- Files explicitly skipped.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If Batch 2 is later applied and must be rolled back, remove only the files
created by that patch after confirming no later user work depends on them:

```text
control-plane/templates/README.md
control-plane/templates/common/README.template.md
control-plane/templates/extensions/jenn-extension.manifest.example.json
```

Rollback must not remove directories that later contain unrelated user work.

## Stop Conditions

- Stop if any planned target file already exists.
- Stop if any selected source file is missing.
- Stop if the manifest example JSON does not parse.
- Stop if required manifest fields are missing.
- Stop if selected sources contain real secrets, credentials, private data, or
  live config values.
- Stop before copying env templates, security templates, runbooks, scripts,
  active config, active registry files, or extension packages.
- Stop before running validator scripts.

## Related Documents

- `phase-2-batch-2-candidate-selection-2026-06-27.md`
- `phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `../decisions/templates-targets-2026-06-27.md`
- `../decisions/control-plane-assets-targets-2026-06-27.md`
- `../receipts/rules-assets-batch-1-contracts-registry-examples-receipt-2026-06-27.md`
