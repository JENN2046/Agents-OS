# Phase 2 Batch 4 Security Boundary Authority Patch Plan - 2026-06-28

Status: patch plan only; no migration performed.

Notice: This document plans the authoritative security-boundary patch for
`governance/SECURITY_BOUNDARIES.md`. It is not migration authorization, not
authorization to copy files yet, not authorization to create duplicate security
authority files, and not authorization to migrate `SECURITY.template.md`.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 4 |
| Batch name | Security boundary authority |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Included source file | `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` |
| Included target file | `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` |
| Included asset type | Canonical workspace security-boundary authority |
| Excluded asset types | Security templates, runbooks, scripts, registry files, active config, private state, logs, cache, runtime artifacts |
| Migration performed | No |
| Validation executed | No patch validation yet |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| None | `/home/jenn/AGENTS_OS_Workspace/governance/` | Directory already exists. |

Do not create root-level or control-plane duplicate security-boundary files.

## Planned File Changes

| Action | Target file | Source file | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` | `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | Rewrite as target-native canonical authority; preserve hard boundaries while reconciling stale high-risk paths. |

No existing target file is planned to be modified in this batch.

## Required Reconciliation

| Source content | Target handling | Reason |
| --- | --- | --- |
| `execution/Codex_Autonomous_Work_Harness/` in high-risk areas | Replace with `governance/Codex_Autonomous_Work_Harness/`. | `target-layer-reconciliation-2026-06-27.md` resolved the harness as rules/governance material. |
| `governance/Bounded-High-Autonomy/` | Preserve. | Already governance-layer material. |
| `runtime/VCPToolBox/...` high-risk paths | Preserve as high-risk examples unless later runtime migration decisions supersede them. | Runtime target planning still uses `runtime/VCPToolBox`. |
| `domains/Photo_Studio_OS*` | Preserve. | Still a domain-level high-risk family. |
| Secret-like file list | Preserve or broaden, but do not weaken. | This is authority text; migration must not reduce secret protection. |
| Allowed template file list | Preserve as template allowances only. | Template allowances do not authorize active config files. |

## Explicitly Out Of Scope

| Path or asset | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/SECURITY_BOUNDARIES.md` | Root duplicate was rejected because it creates drift risk. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/policies/SECURITY_BOUNDARIES.md` | Control-plane placement was rejected; this is governance authority. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/security/SECURITY.template.md` | Security template is a later batch after authority file exists. |
| `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | Template source is not part of this authority patch. |
| `WORKSPACE_REGISTRY.yaml` | Registry authority belongs to a separate registry batch. |
| Runbooks and scripts | They require separate review and must not be executed here. |
| Active config, private state, logs, cache, runtime artifacts | Outside security-boundary authority scope. |

## Strict Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm source file exists | Check `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md`. | Source file exists and size is recorded. |
| Reconfirm target file is absent | Check `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md`. | Target file does not exist. |
| Reconfirm duplicate targets are absent | Check root `SECURITY_BOUNDARIES.md` and `control-plane/policies/SECURITY_BOUNDARIES.md`. | No duplicate authority target exists or is created. |
| Reconfirm governance directory exists | Check `/home/jenn/AGENTS_OS_Workspace/governance/`. | Directory exists and is the planned authority layer. |
| Reconcile high-risk paths | Compare source high-risk list with current target-layer decisions. | `Codex_Autonomous_Work_Harness` appears under `governance/`, not `execution/`, in the target draft. |
| Preserve hard-stop semantics | Review absolute, git, runtime, permission, and risk reporting sections. | Target draft does not weaken source boundaries. |
| Live-secret pattern scan | Scan source and target draft for real secret values. | No real secret, token, credential, password, private endpoint, or private account value is present. |
| Active config review | Inspect protected and allowed file lists. | `.env`, `.env.*`, `config.env`, key files, and credential files remain protected; templates remain examples only. |
| Authority wording review | Inspect title and scope text. | Target states it is the canonical workspace security-boundary authority. |

## Planned Content Rules

- Target file must live at `governance/SECURITY_BOUNDARIES.md`.
- Target file must state it is canonical workspace security-boundary authority.
- Target file must not be placed under root or `control-plane/policies/`.
- Target file must not be confused with `SECURITY.template.md`.
- Hard boundaries must not be weakened from the source.
- High-risk paths must be reconciled with current target-layer decisions.
- `execution/Codex_Autonomous_Work_Harness/` must not be carried forward as
  the target high-risk path.
- Allowed template patterns must not authorize active config files.
- No runbook or script command may be executed in this batch.

## Post-Patch Validation Plan

| Validation | Command or method | Notes |
| --- | --- | --- |
| Target file existence check | Confirm `governance/SECURITY_BOUNDARIES.md` exists after patch. | It should be the only security-boundary authority file created. |
| Duplicate absence check | Check root and `control-plane/policies/` duplicate paths. | Confirm no duplicate authority file exists. |
| High-risk path reconciliation check | Search target for `Codex_Autonomous_Work_Harness`. | Confirm governance path is present and execution path is absent. |
| Source-to-target section review | Compare major sections with source. | Confirm absolute rules, private state, git, runtime, permission levels, high-risk areas, and risk report format remain present. |
| Live-secret pattern scan | Scan target content. | No live-secret pattern should be present. |
| Diff or content review | Inspect changed files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run source or migrated validator scripts in this batch.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-4-security-boundary-authority-receipt-2026-06-28.md
```

The receipt should record:

- Exact authorization wording.
- Source file read.
- Target file created.
- Files explicitly skipped.
- Reconciliation performed.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If Batch 4 authority patch is later applied and must be rolled back, remove
only the file created by that patch after confirming no later user work depends
on it:

```text
governance/SECURITY_BOUNDARIES.md
```

Rollback must not remove `governance/` or unrelated governance files.

## Stop Conditions

- Stop if the source file is missing.
- Stop if `governance/SECURITY_BOUNDARIES.md` already exists.
- Stop if root or control-plane duplicate authority files exist and create
  ambiguity.
- Stop if high-risk path reconciliation is unresolved.
- Stop if the target draft weakens source hard boundaries.
- Stop if the target draft contains real secrets, tokens, credentials,
  passwords, private endpoints, or private account values.
- Stop before creating `SECURITY.template.md`.
- Stop before copying runbooks, scripts, registry files, active config, private
  state, logs, cache, or runtime artifacts.

## Related Documents

- `phase-2-batch-4-security-template-alignment-2026-06-28.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../decisions/target-layer-reconciliation-2026-06-27.md`
- `phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
