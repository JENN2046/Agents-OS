# Phase 2 Batch 4 Security Template Patch Plan - 2026-06-28

Status: patch plan only; no migration performed.

Notice: This document plans the security-template patch now that
`governance/SECURITY_BOUNDARIES.md` exists. It is not migration authorization,
not authorization to copy files yet, and not authorization to modify the
canonical security-boundary authority.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 4 |
| Batch name | Security template |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Included source file | `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` |
| Included target file | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md` |
| Required authority file | `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` |
| Included asset type | Reusable project/repo security document template |
| Excluded asset types | Security-boundary authority files, runbooks, scripts, registry files, active config, private state, logs, cache, runtime artifacts |
| Migration performed | No |
| Validation executed | No patch validation yet |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/` | Isolated target directory for reusable security document templates. |

Do not create or modify `governance/SECURITY_BOUNDARIES.md` in this batch.

## Planned File Changes

| Action | Target file | Source file | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md` | `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | Rewrite/adapt as a reusable security template that defers to `governance/SECURITY_BOUNDARIES.md` and does not become authority. |

No existing target file is planned to be modified in this batch.

## Required Alignment

| Topic | Target handling | Reason |
| --- | --- | --- |
| Authority role | State that this is a template and that `governance/SECURITY_BOUNDARIES.md` is the canonical authority. | Prevent template/authority confusion. |
| Default mode | Preserve read-only unless explicitly authorized. | Matches source template and governance boundary posture. |
| Forbidden actions | Preserve conservative defaults and point to governance for complete hard stops. | Avoid weakening security or duplicating a drifting hard-stop list. |
| Allowed config examples | Keep `.env.example`, `config.env.example`, `*.template`, `*.example` as examples only. | Matches governance authority while avoiding active config approval. |
| Forbidden config examples | Include `.env`, `.env.*`, `config.env`, tokens, API keys, private credentials, and point to governance for the full protected list. | Keeps the template aligned with authority without becoming a duplicate authority file. |
| Private state | Mention that private state is governed by `governance/SECURITY_BOUNDARIES.md`. | Source template omits this but authority includes it. |
| High-risk paths | Do not duplicate the full high-risk path list in the template. | Prevent drift; point users to governance authority. |
| Approval | Preserve explicit approval and receipt requirement for high-risk actions. | Matches source template and workspace policy. |

## Explicitly Out Of Scope

| Path or asset | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` | Existing canonical authority; not modified by this template batch. |
| `/home/jenn/AGENTS_OS_Workspace/SECURITY_BOUNDARIES.md` | Root duplicate is not allowed. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/policies/SECURITY_BOUNDARIES.md` | Control-plane duplicate is not allowed. |
| Env templates | Already handled by Batch 3. |
| Runbooks | Reserved for a later runbook batch. |
| Validator scripts | Scripts require separate syntax, path, output, and execution-safety review. |
| Active config, registry files, extension packages, private state, logs, cache, runtime artifacts | Outside security-template scope. |

## Strict Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm source template exists | Check `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md`. | Source template exists and size is recorded. |
| Reconfirm target template is absent | Check `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md`. | Target template does not exist. |
| Reconfirm authority file exists | Check `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md`. | Authority file exists and is not modified by this batch. |
| Reconfirm duplicate authority paths are absent | Check root and `control-plane/policies/` duplicate paths. | No duplicate security-boundary authority file exists or is created. |
| Compare config wording with authority | Inspect allowed/protected file patterns in the template and authority. | Target template remains aligned and defers to governance for the full protected list. |
| Check template non-authority wording | Inspect target draft title/scope. | Target clearly says it is a template, not canonical authority. |
| Avoid high-risk path duplication | Inspect target draft. | Target points to governance authority instead of copying a full high-risk path list. |
| Live-secret pattern scan | Scan source and target draft. | No real secret, token, credential, password, private endpoint, or private account value is present. |

## Planned Content Rules

- Target file must live at `control-plane/templates/security/SECURITY.template.md`.
- Target file must state that it is a reusable project/repo template.
- Target file must state that `governance/SECURITY_BOUNDARIES.md` is the
  canonical workspace security-boundary authority.
- Target file must not be placed under `governance/`.
- Target file must not duplicate root or control-plane security-boundary
  authority files.
- Target file must not create or authorize active config files.
- Target file must not copy private state, logs, cache, runtime artifacts, or
  extension package material.
- Do not run validator scripts in this batch.

## Post-Patch Validation Plan

| Validation | Command or method | Notes |
| --- | --- | --- |
| Target file existence check | Confirm `control-plane/templates/security/SECURITY.template.md` exists after patch. | It should be the only file created in `control-plane/templates/security/`. |
| Authority file unchanged check | Inspect `governance/SECURITY_BOUNDARIES.md` path and modification scope by direct review. | No content change is planned there. |
| Duplicate authority absence check | Check root and `control-plane/policies/` duplicate paths. | Confirm no duplicate authority file exists. |
| Non-authority wording check | Search target for template/authority wording. | Confirm template defers to governance authority. |
| Config wording check | Inspect allowed/forbidden config examples. | Confirm active config remains forbidden and template examples remain examples only. |
| High-risk path duplication check | Search target for high-risk path list entries. | Prefer no full copied high-risk list; point to governance authority instead. |
| Live-secret pattern scan | Scan target content. | No live-secret pattern should be present. |
| Diff or content review | Inspect changed files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run source or migrated validator scripts in this batch.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-4-security-template-receipt-2026-06-28.md
```

The receipt should record:

- Exact authorization wording.
- Source file read.
- Authority file checked.
- Target directory created.
- Target file created.
- Files explicitly skipped.
- Alignment performed.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If the security-template patch is later applied and must be rolled back, remove
only the file created by that patch after confirming no later user work depends
on it:

```text
control-plane/templates/security/SECURITY.template.md
```

Rollback must not remove `control-plane/templates/`, existing ordinary/env
templates, or `governance/SECURITY_BOUNDARIES.md`.

## Stop Conditions

- Stop if the source template is missing.
- Stop if `governance/SECURITY_BOUNDARIES.md` is missing.
- Stop if the target template already exists.
- Stop if root or control-plane duplicate authority files appear.
- Stop if the target draft presents itself as canonical authority.
- Stop if the target draft weakens governance security boundaries.
- Stop if the target draft contains real secrets, tokens, credentials,
  passwords, private endpoints, or private account values.
- Stop before modifying `governance/SECURITY_BOUNDARIES.md`.
- Stop before copying runbooks, scripts, registry files, active config, private
  state, logs, cache, runtime artifacts, or extension packages.

## Related Documents

- `phase-2-batch-4-security-template-alignment-2026-06-28.md`
- `phase-2-batch-4-security-boundary-authority-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-4-security-boundary-authority-receipt-2026-06-28.md`
- `../decisions/templates-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
