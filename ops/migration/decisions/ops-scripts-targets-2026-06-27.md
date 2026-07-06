# Ops Scripts Target Decision - 2026-06-27

Status: target-placement decision only，非迁移授权。

This decision record separates validation scripts, maintenance/sync scripts,
and deferred-execution scripts from the Windows reference root. It does not
authorize copying, moving, deleting, executing, pushing, syncing, merging,
changing executable bits, or changing source assets.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Ops script target placement and execution handling |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source area reviewed | `A:\AGENTS_OS_Workspace\ops\scripts` |
| Assets included | `README.AGENTS_OS.md`, `sync-upstream-vcp.sh`, `validate-domain-bridges.sh`, `validate-execution-profiles.sh`, `validate-extension-manifests.sh`, `validate-no-secrets.sh`, `validate-policy-packs.sh`, `validate-vcp-runtime.sh`, `validate-workspace.sh` |
| Assets excluded | Runbooks, prompts, templates, private state, runtime repositories |
| Evidence used | Source file content read, keyword scan for git/remote/destructive/runtime/secret signals, WSL target directory check, `ops/README.md`, runbook target decision |
| Migration performed | No |
| Script execution performed | No |

## Grouping Decision

| Group | Planning target | Handling rule |
| --- | --- | --- |
| Validation script candidates | `ops/validation/` | May be migrated only after syntax check, path review, and non-secret-output review. |
| Maintenance/sync scripts | `ops/maintenance/` | Keep separate from validation; treat as restricted helper/reference until remote and branch actions are separately approved. |
| Deferred-execution scripts | `ops/validation/drafts/` or no active target until rewritten | Preserve only as draft/reference if needed; do not make executable or active during rules migration. |

This is a planning split for the current migration, not a permanent category
system. Future scripts should be placed by actual behavior and risk.

## File Decisions

| Source file | Target for planning | Handling decision | Reason |
| --- | --- | --- | --- |
| `A:\AGENTS_OS_Workspace\ops\scripts\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/README.md` and, if needed, `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/README.md` | Rewrite or split into target-native README files. | The README describes validation and reporting scripts, but also lists the sync helper. WSL already separates `ops/validation` and `ops/maintenance`, so a single copied README would blur ownership. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-no-secrets.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-no-secrets.sh` | Validation candidate after syntax-only check and output review. | The script performs a path-only suspicious-file scan and states that it does not print secret values. It still scans from `.` and must be reviewed before execution. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-extension-manifests.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-extension-manifests.sh` | Validation candidate after path review. | The script checks extension-like directories under `./extensions` for manifests. It matches the WSL extensions layout in broad shape but must be reviewed against current extension paths. |
| `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/sync-upstream-vcp.sh` | Maintenance/sync script; keep restricted and do not execute without a separate approval packet. | The script prints a guarded manual procedure, but that procedure includes `git fetch`, `git pull`, branch creation, and merge commands. It belongs with maintenance, not validation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-domain-bridges.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/drafts/validate-domain-bridges.sh` | Deferred-execution draft. | The script is a placeholder that only prints a future validation topic. It should not be treated as a real validator. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-execution-profiles.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/drafts/validate-execution-profiles.sh` | Deferred-execution draft. | The script is a placeholder and references future schema validation for `execution/execution-profiles/*.yaml`. It needs actual schema and target review. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-policy-packs.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/drafts/validate-policy-packs.sh` | Deferred-execution draft. | The script is a placeholder and references future schema validation for `governance/policy-packs/*.yaml`. It needs actual schema and target review. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-vcp-runtime.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/drafts/validate-vcp-runtime.sh` or future runtime-specific validator | Deferred execution until runtime migration and git-output policy are settled. | The script checks `runtime/VCPToolBox` and runs read-only `git -C` status/branch commands if a repo exists. It is runtime-adjacent and should wait for runtime target reconciliation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` | No active target until rewritten; possible future `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-workspace.sh` | Rewrite required before migration. | The script checks old root paths such as `AGENTS_OS/README.AGENTS_OS.md`, root `WORKSPACE_REGISTRY.yaml`, and root `SECURITY_BOUNDARIES.md`, which conflict with current WSL target decisions. |

## Risk Evidence

| Source file | Observed signal | Decision impact |
| --- | --- | --- |
| `validate-no-secrets.sh` | Scans `.env`, `config.env`, key, token, and credential-like filenames; says it prints paths only. | Candidate validator, but output must remain path-only and no file contents may be printed. |
| `validate-extension-manifests.sh` | Uses `find ./extensions` and manifest checks. | Candidate validator after WSL extension path review. |
| `sync-upstream-vcp.sh` | Contains remote/sync procedure text: `git fetch`, `git pull`, branch creation, merge. | Maintenance/sync only; not validation and not execution authorization. |
| `validate-vcp-runtime.sh` | Uses `runtime/VCPToolBox` and `git -C ... status/branch`. | Defer until runtime migration and git-output expectations are clear. |
| `validate-workspace.sh` | Requires old `AGENTS_OS/...` and root registry/security files. | Rewrite before use; do not copy as active validator. |
| Placeholder validators | Print TODO-style messages only. | Keep as drafts/reference, not active validators. |

## Directory Decisions

| Target directory | Decision | Notes |
| --- | --- | --- |
| `ops/validation/` | Use for reviewed validation scripts. | Existing directory. Do not populate until Phase 2. |
| `ops/validation/drafts/` | Use only if draft validators are preserved during Phase 2. | Draft scripts must not be executable by default. |
| `ops/maintenance/` | Use for reviewed maintenance helpers. | Existing directory. Remote/sync helpers stay here, not under validation. |
| `ops/scripts/` | Do not recreate as the canonical WSL target for this batch. | WSL already has clearer `validation` and `maintenance` surfaces. |

## Required Review Before Phase 2 Copy

| Asset | Required review |
| --- | --- |
| Script README | Split validation and maintenance guidance; remove any implication that scripts may run by default. |
| `validate-no-secrets.sh` | Syntax-only check; confirm no file-content printing; confirm examples/templates are ignored correctly in WSL layout. |
| `validate-extension-manifests.sh` | Syntax-only check; verify `./extensions` path and extension naming rules; decide whether placeholder directories should be skipped. |
| `sync-upstream-vcp.sh` | Decide whether to keep as a non-executable printed reference, rewrite as a runbook, or defer entirely. |
| Placeholder validators | Replace placeholders with real validators or keep them under drafts only. |
| `validate-vcp-runtime.sh` | Wait for runtime migration decision and define read-only git output policy. |
| `validate-workspace.sh` | Rewrite against WSL target decisions before any migration. |

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Copy all scripts into `ops/validation/` | Rejected | Sync and runtime/git-adjacent scripts are not ordinary validation. |
| Recreate Windows `ops/scripts/` as canonical WSL layout | Rejected | WSL already separates validation from maintenance. |
| Treat placeholder scripts as active validators | Rejected | They only print TODO text and would create false confidence. |
| Treat `sync-upstream-vcp.sh` as safe because it only prints commands | Rejected | The commands it prints are remote/branch-sensitive; its purpose is maintenance/sync. |
| Copy `validate-workspace.sh` as-is | Rejected | It encodes old `AGENTS_OS/` and root-file assumptions that conflict with current target decisions. |
| Make migrated scripts executable by default | Rejected | Executable bits and script execution require a later scoped validation plan. |

## Phase 2 Stop Conditions

- Do not execute any source or migrated script during migration.
- Do not run `git fetch`, `git pull`, branch creation, merge, push, release, or
  deploy from any script without separate explicit approval.
- Do not print secret values or file contents from secret-like files.
- Do not make scripts executable by default.
- Do not copy old path assumptions as active validators.
- Do not create target directories or copy files until Phase 2.

## Related Documents

- `../inventory/rules-assets-inventory-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `runbooks-targets-2026-06-27.md`
- `templates-targets-2026-06-27.md`
- `workspace-registry-security-boundaries-targets-2026-06-27.md`
