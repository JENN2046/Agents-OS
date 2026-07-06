# Rules Assets Inventory - 2026-06-27

Status: Phase 0 read-only inventory，非迁移授权。

This document records a shallow, read-only inventory of rules and control-plane
asset candidates from the Windows reference root. It does not authorize copying,
moving, deleting, executing, syncing, pushing, or changing source assets.

## Method

- Inspected file metadata only: path, size, and modified time.
- Did not deeply read candidate file contents.
- Did not inspect `state-private/`.
- Did not execute shell scripts.
- Did not copy any source file into the WSL target tree.
- Checked WSL target-side directory shape only for likely landing areas.

## Source Scope

| Source area | Files observed | Directories observed | Evidence |
| --- | ---: | ---: | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS` | 14 | 6 | `Get-ChildItem -Recurse -File` metadata |
| `A:\AGENTS_OS_Workspace\templates` | 5 | 0 | `Get-ChildItem -Recurse -File` metadata |
| `A:\AGENTS_OS_Workspace\ops\scripts` | 9 | 0 | `Get-ChildItem -Recurse -File` metadata |
| `A:\AGENTS_OS_Workspace` root selected files | 2 | n/a | `Get-Item` metadata for registry/security files |

Total candidate files observed: 30.

## Target-Side Facts

| WSL path | Observed fact | Migration impact |
| --- | --- | --- |
| `control-plane/` | Exists with `contracts`, `policies`, `schemas`, and `task-envelope` directories. | Suitable broad landing area, but missing some planned subdirectories. |
| `control-plane/registry` | Not observed. | Needs Phase 1 target decision before registry copy. |
| `control-plane/runbooks` | Not observed. | Needs Phase 1 target decision before runbook copy. |
| `control-plane/prompts` | Not observed. | Needs Phase 1 sensitivity/freshness review before prompt copy. |
| `extensions/` | Exists with `vcp-toolbox-jenn`. | Template assets may belong here only after ownership review. |
| `ops/validation` | Exists. | Candidate landing area for validation scripts after script safety review. |
| `ops/maintenance` | Exists. | Candidate landing area for maintenance scripts after script safety review. |
| WSL root `WORKSPACE_REGISTRY.yaml` | Not observed. | Root placement is available but not yet decided. |
| WSL root `SECURITY_BOUNDARIES.md` | Not observed. | Root placement is available but not yet decided. |
| `governance/SECURITY_BOUNDARIES.md` | Not observed. | Governance placement is available but not yet decided. |

## Sensitive Name Scan

| Pattern | Hit | Initial reading |
| --- | --- | --- |
| `.env` | `A:\AGENTS_OS_Workspace\templates\config.env.example.template` | Example template only by filename, but must be reviewed before migration. |
| `secret` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-no-secrets.sh` | Security validation script by filename, but must not be executed or copied without review. |

No candidate path matched `token`, `credential`, `cache`, `logs`, `node_modules`,
`.venv`, `dist`, `build`, or `tmp` in the source-scope metadata scan.

## File Inventory

Labels:

- `可迁候选`: Looks like a rules/control-plane asset from metadata and path, but still requires a later migration patch.
- `需审`: Needs content, target ownership, freshness, or naming review before copying.
- `暂缓`: Execution, sync, sensitive-name, or runtime-adjacent risk is high enough to defer.

| Label | Source file | Size | Modified | Proposed WSL target area | Evidence and reason |
| --- | --- | ---: | --- | --- | --- |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\README.AGENTS_OS.md` | 1107 | 2026-06-08 23:09:39 +08:00 | `control-plane/` | Root overview may need merge/rename against existing `control-plane/README.md`. |
| `可迁候选` | `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\jenn-extension.manifest.schema.json` | 987 | 2026-06-08 23:09:39 +08:00 | `control-plane/contracts/` | Schema asset; target directory already exists. |
| `可迁候选` | `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\README.AGENTS_OS.md` | 1058 | 2026-06-08 23:09:39 +08:00 | `control-plane/contracts/` | Contract documentation; target directory already exists. |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\README.AGENTS_OS.md` | 819 | 2026-06-08 23:09:39 +08:00 | `control-plane/prompts/` | Prompt assets need freshness and sensitivity review; target directory not observed. |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\agents\README.AGENTS_OS.md` | 865 | 2026-06-08 23:09:39 +08:00 | `control-plane/prompts/agents/` | Prompt guidance needs content review before becoming canonical. |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts\codex\README.AGENTS_OS.md` | 951 | 2026-06-08 23:09:39 +08:00 | `control-plane/prompts/codex/` | Codex-specific prompt guidance may overlap current global rules. |
| `可迁候选` | `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\extensions.example.yaml` | 538 | 2026-06-08 23:09:39 +08:00 | `control-plane/registry/` | Example registry asset; target directory needs Phase 1 decision. |
| `可迁候选` | `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\protected-paths.example.yaml` | 638 | 2026-06-08 23:09:39 +08:00 | `control-plane/registry/` | Example protected-path asset; target directory needs Phase 1 decision. |
| `可迁候选` | `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\README.AGENTS_OS.md` | 1016 | 2026-06-08 23:09:39 +08:00 | `control-plane/registry/` | Registry documentation; target directory needs Phase 1 decision. |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\add-new-extension.md` | 511 | 2026-06-08 23:09:39 +08:00 | `control-plane/runbooks/` or `ops/migration/decisions/` | Runbook content needs topic placement review. |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\onboard-new-agent.md` | 426 | 2026-06-08 23:09:39 +08:00 | `control-plane/runbooks/` | Agent onboarding guidance may overlap global/project rules. |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\README.AGENTS_OS.md` | 918 | 2026-06-08 23:09:39 +08:00 | `control-plane/runbooks/` | Runbook index should be reconciled with current migration docs. |
| `需审` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\run-codex-task.md` | 362 | 2026-06-08 23:09:39 +08:00 | `control-plane/runbooks/` | Execution guidance requires current Codex behavior review. |
| `暂缓` | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\upstream-sync-vcptoolbox.md` | 904 | 2026-06-08 23:09:39 +08:00 | `ops/maintenance/` or reference only | Upstream sync topic may imply remote or branch-sensitive behavior. |
| `暂缓` | `A:\AGENTS_OS_Workspace\templates\config.env.example.template` | 169 | 2026-06-08 23:09:39 +08:00 | `control-plane/templates/` or `extensions/templates/` | `.env` name hit; must be reviewed and sanitized before migration. |
| `可迁候选` | `A:\AGENTS_OS_Workspace\templates\jenn-extension.manifest.example.json` | 1216 | 2026-06-08 23:09:39 +08:00 | `extensions/templates/` or `control-plane/templates/` | Example manifest pairs with extension schema; target ownership still needs decision. |
| `需审` | `A:\AGENTS_OS_Workspace\templates\README.AGENTS_OS.md` | 222 | 2026-06-08 23:09:39 +08:00 | `control-plane/templates/` | Template overview should be merged with final target README. |
| `需审` | `A:\AGENTS_OS_Workspace\templates\README.template.md` | 793 | 2026-06-08 23:09:39 +08:00 | `control-plane/templates/` or `extensions/templates/` | Template type and ownership not yet decided. |
| `需审` | `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | 499 | 2026-06-08 23:09:39 +08:00 | `control-plane/templates/` or `governance/` | Security template needs review against canonical security boundaries. |
| `需审` | `A:\AGENTS_OS_Workspace\ops\scripts\README.AGENTS_OS.md` | 775 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` or `ops/maintenance/` | Script index needs split by validation vs maintenance ownership. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` | 439 | 2026-06-08 23:09:39 +08:00 | `ops/maintenance/` or reference only | Sync script may have remote/branch side effects; do not migrate before review. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-domain-bridges.sh` | 138 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` | Script behavior and path assumptions not reviewed. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-execution-profiles.sh` | 157 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` | Script behavior and path assumptions not reviewed. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-extension-manifests.sh` | 1539 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` | Script behavior, dependencies, and path assumptions not reviewed. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-no-secrets.sh` | 822 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` | `secret` name hit is likely intentional, but script needs safety review. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-policy-packs.sh` | 146 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` | Script behavior and path assumptions not reviewed. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-vcp-runtime.sh` | 359 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` or reference only | Runtime-adjacent validation should not be part of rules migration without review. |
| `暂缓` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` | 648 | 2026-06-08 23:09:39 +08:00 | `ops/validation/` | Script behavior and path assumptions not reviewed. |
| `需审` | `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml` | 3074 | 2026-06-08 23:09:39 +08:00 | WSL root or `control-plane/registry/` | Registry placement needs Phase 1 authority decision; no WSL copy observed. |
| `需审` | `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | 1832 | 2026-06-08 23:09:39 +08:00 | WSL root or `governance/` | Security boundary should remain prominent; target placement needs decision. |

## Initial Totals

| Label | Count | Meaning |
| --- | ---: | --- |
| `可迁候选` | 6 | Looks safe enough to prepare for Phase 1 target decisions. |
| `需审` | 14 | Needs content, freshness, target, or naming review before copy. |
| `暂缓` | 10 | Should not move until script, sync, env, or runtime-adjacent risks are resolved. |

## Phase 1 Decision Queue

1. Decide whether `WORKSPACE_REGISTRY.yaml` belongs at WSL root, under
   `control-plane/registry/`, or both with one canonical source.
2. Decide whether `SECURITY_BOUNDARIES.md` belongs at WSL root, under
   `governance/`, or both with one canonical source.
3. Decide whether `README.AGENTS_OS.md` files should be copied as-is, renamed,
   or merged into existing target READMEs.
4. Review prompt assets before any migration because prompt guidance can become
   behavioral authority.
5. Review templates before migration, especially the `.env` example template.
6. Review shell scripts separately and treat them as code, not passive docs.

## Stop Conditions For Phase 2

- Do not copy any `暂缓` item without a separate script/template/security review.
- Do not execute any source or migrated script.
- Do not create target directories until Phase 1 has decided ownership.
- Do not treat `可迁候选` as authorization to migrate.
- Do not migrate anything from `state-private/`, generated outputs, caches,
  logs, dependency directories, or runtime databases.

## Related Documents

- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `roots-inventory-2026-06-27.md`
- `../decisions/source-path-reconciliation-2026-06-27.md`
- `../decisions/target-layer-reconciliation-2026-06-27.md`
