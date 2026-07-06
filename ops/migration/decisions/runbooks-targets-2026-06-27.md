# Runbooks Target Decision - 2026-06-27

Status: target-placement decision only，非迁移授权。

This decision record separates ordinary rules/procedure runbooks from
remote-sensitive maintenance runbooks. It does not authorize copying, moving,
deleting, executing, pushing, syncing, merging, or changing source assets.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Runbook target placement and handling |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source area reviewed | `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks` |
| Assets included | `README.AGENTS_OS.md`, `add-new-extension.md`, `onboard-new-agent.md`, `run-codex-task.md`, `upstream-sync-vcptoolbox.md` |
| Assets excluded | Prompts, scripts, templates, private state, unobserved runbooks named in README only |
| Evidence used | Source file content read, keyword scan for remote/sync/destructive terms, WSL target directory check, `_DIRECTORY_PRINCIPLES.md`, `ops/README.md`, Phase 0 inventory |
| Migration performed | No |

## Grouping Decision

| Group | Planning target | Handling rule |
| --- | --- | --- |
| Ordinary rules/procedure runbooks | `control-plane/runbooks/` | May become target-native runbooks after path normalization and content review. |
| Remote/sync-sensitive maintenance runbooks | `ops/maintenance/runbooks/` | Keep separate from ordinary runbooks; treat as restricted reference until a separate execution-safe plan exists. |

This is a planning split for the current migration, not a permanent taxonomy.
Future runbooks should be placed by their actual role and risk.

## File Decisions

| Source file | Target for planning | Handling decision | Reason |
| --- | --- | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/README.md` | Rewrite or adapt as the target runbook index. | The file defines runbook purpose, boundaries, interfaces, validation, and ownership. It should become the index for ordinary runbooks, but must not list unobserved files as already present. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\add-new-extension.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/add-new-extension.md` | Phase 2 migration candidate as an ordinary procedure after path and registry references are normalized. | The runbook describes adding an extension and defaults to read-only/no shell/no push/no release/no deploy. It references old registry placement that must be updated before migration. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\onboard-new-agent.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/onboard-new-agent.md` | Phase 2 migration candidate as an ordinary procedure after extension path references are verified. | The runbook describes agent onboarding and keeps private state under `state-private/`. It includes permission and identity boundaries, but does not contain remote commands. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\run-codex-task.md` | `/home/jenn/AGENTS_OS_Workspace/control-plane/runbooks/run-codex-task.md` | Phase 2 migration candidate only after alignment with current governance and Codex operating rules. | The runbook defines an audit-first Codex task flow and forbidden defaults. It should remain procedural guidance, not an execution authorization. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks\upstream-sync-vcptoolbox.md` | `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/runbooks/upstream-sync-vcptoolbox.md` | Defer active migration; preserve only as restricted maintenance reference until separately approved. | The runbook contains `git fetch`, `git pull`, branch creation, merge commands, validation commands, and explicit push authorization language. It is useful, but remote/branch-sensitive. |

## Remote And Risk Evidence

| Source file | Observed signal | Decision impact |
| --- | --- | --- |
| `add-new-extension.md` | Contains `no git push`, `no release`, `no deploy`. | Safe as ordinary guidance after stale path review. |
| `README.AGENTS_OS.md` | Says runbooks are audit-first and push/release/deploy require separate authorization. | Preserve this boundary in the target README. |
| `run-codex-task.md` | Says tasks start audit-only unless explicitly authorized; lists push/release/deploy as forbidden by default. | Keep as guidance; do not treat as authorization to run tasks. |
| `upstream-sync-vcptoolbox.md` | Contains `git fetch`, `git pull`, branch creation, merge, `npm test`, lint/build, and "Do not push until Jenn authorizes." | Isolate under maintenance reference; do not put in ordinary runbooks. |
| `upstream-sync-vcptoolbox.md` | Lists `git reset --hard` and `git clean -fd` under "Never use". | Preserve as a warning if migrated, but do not create an executable checklist from this file alone. |

## Directory Decisions

| Target directory | Decision | Notes |
| --- | --- | --- |
| `control-plane/runbooks/` | Create only during a later approved Phase 2 migration patch. | Ordinary procedure runbooks live here after normalization. |
| `ops/maintenance/runbooks/` | Create only during a later approved Phase 2 migration patch. | Remote/sync-sensitive maintenance references live here. |
| `governance/runbooks/` | Not used for this batch. | These files reference governance, but the current batch is mostly procedure/index material. Future hard-gate policy docs may belong under governance. |

## Required Review Before Phase 2 Copy

| Asset | Required review |
| --- | --- |
| `README.AGENTS_OS.md` | Convert to `README.md`; remove or mark files listed in the source README but not observed in this inventory. |
| `add-new-extension.md` | Update `AGENTS_OS/registry/extensions.yaml` reference to the WSL registry decision path or a future verified registry file. |
| `onboard-new-agent.md` | Verify `extensions/Jenn-VCP-Extensions/agent-packs/` against the WSL extensions target layout. |
| `run-codex-task.md` | Align the flow with current governance decisions and global Codex safety rules; keep audit-first wording. |
| `upstream-sync-vcptoolbox.md` | Rewrite as a preflight/reference document with explicit non-authorization language before any migration; no command execution. |

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Put every runbook under `control-plane/runbooks/` | Rejected | `upstream-sync-vcptoolbox.md` is remote/branch-sensitive and belongs away from ordinary procedural guidance. |
| Put every runbook under `ops/maintenance/runbooks/` | Rejected | Ordinary rule/procedure docs are part of the control-plane surface, not maintenance outputs. |
| Treat `upstream-sync-vcptoolbox.md` as an executable procedure | Rejected | It requires remote and branch-sensitive actions. A document cannot authorize those actions. |
| Preserve `README.AGENTS_OS.md` as canonical target filename | Rejected | WSL target directories use local `README.md`; the old filename should be adapted, not copied as authority. |
| Create placeholder runbooks for files named only in README | Rejected | `approve-protected-action.md` and `handle-failed-action.md` were named in the source README but were not observed as files during this inventory. |

## Phase 2 Stop Conditions

- Do not execute any runbook command during migration.
- Do not run `git fetch`, `git pull`, branch creation, merge, push, release, or
  deploy from a runbook without a separate explicit action approval.
- Do not copy stale path references as canonical facts.
- Do not migrate unobserved runbooks named only in a README.
- Do not create target directories or copy files until Phase 2.

## Related Documents

- `../inventory/rules-assets-inventory-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `control-plane-assets-targets-2026-06-27.md`
- `workspace-registry-security-boundaries-targets-2026-06-27.md`
