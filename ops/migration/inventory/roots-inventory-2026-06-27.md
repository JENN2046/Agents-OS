# Roots Inventory - 2026-06-27

Status: 只读清点证据，非迁移授权。

This inventory records shallow root-level evidence for the Windows reference
root and the canonical WSL root. It does not authorize copying, moving,
deleting, executing, pushing, syncing, or changing any project.

## Scope

| Item | Value |
| --- | --- |
| Date | 2026-06-27 |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Inspection depth | Root-level listing plus shallow `.git` discovery to depth 4; nested `.bha\local` regression repository signals were excluded |
| Private state review | Not performed |
| Project source review | Not performed |
| Remote or side-effectful actions | Not performed |

## Evidence Summary

| Check | Evidence |
| --- | --- |
| Windows root exists | `Test-Path A:\AGENTS_OS_Workspace` returned `True`. |
| WSL root exists | `Test-Path \\wsl.localhost\Ubuntu-24.04\home\jenn\AGENTS_OS_Workspace` returned `True`. |
| Directory principles match | `A:\AGENTS_OS_Workspace\DIRECTORY_PRINCIPLES_V1_1.md` and WSL `_DIRECTORY_PRINCIPLES.md` both have SHA256 `6E781C3AEDBD1A797CD2EE22C2DEACA55F52942CD96512DD6AD6D88C62B53BD3`. |
| Canonical root declaration | WSL `_MIGRATION_MAP.md` declares `/home/jenn/AGENTS_OS_Workspace` as canonical WSL root and `A:\AGENTS_OS_Workspace` as Windows reference root. |
| Migration status | WSL `_MIGRATION_MAP.md` records multiple repo mappings as `pending`. |
| Shallow Windows repo signal | Depth-4 `.git` discovery found multiple repositories under the Windows root. |
| Shallow WSL repo signal | Depth-4 `.git` discovery found `governance/codex-router/.git` under the WSL root. |

## Windows Reference Root Inventory

Root path: `A:\AGENTS_OS_Workspace`

### Top-Level Directories

| Directory | Last observed role |
| --- | --- |
| `AGENTS_OS/` | Control-plane style root with contracts, prompts, registry, and runbooks. |
| `archive/` | Historical archive area. |
| `domains/` | Domain systems and related project groups. |
| `execution/` | Harness, checkpoints, runners, bridges, and receipts. |
| `extensions/` | Jenn extension standards, templates, and extension packs. |
| `governance/` | Governance projects and policy/gate areas. |
| `ops/` | Validation, reports, scripts, and release-readiness material. |
| `runtime/` | Runtime projects, VCP variants, worktrees, evidence, and local-state-related material. |
| `state-private/` | Private state boundary; not inspected deeply. |
| `templates/` | Reusable template material. |

### Top-Level Files

| File | Evidence note |
| --- | --- |
| `.gitignore` | Present at root. |
| `AGENTS.md` | Present at root. |
| `CODEX_TASK_RENAME_READMES.md` | Present at root. |
| `DIRECTORY_PRINCIPLES.md` | Present at root. |
| `DIRECTORY_PRINCIPLES_V1_1.md` | Present at root and hash-matched with WSL `_DIRECTORY_PRINCIPLES.md`. |
| `FILE_MANIFEST.md` | Present at root. |
| `README.AGENTS_OS.md` | Present at root. |
| `SECURITY_BOUNDARIES.md` | Present at root. |
| `WORKSPACE_REGISTRY.yaml` | Present at root. |

### Shallow Git Repositories Observed

The following `.git` directories were observed under the Windows reference root
with shallow discovery. This is a repo signal only; no repository status or
branch validation was performed for this inventory.

| Repository signal |
| --- |
| `A:\AGENTS_OS_Workspace\domains\agent-image-lab\agent-image-lab-v0.2\.git` |
| `A:\AGENTS_OS_Workspace\domains\agent-image-lab\repo\agent-image-lab\.git` |
| `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS\.git` |
| `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS\Photo_Studio_OS_Backend\.git` |
| `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS\Photo_Studio_OS_Control\.git` |
| `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS\Photo_Studio_OS_Frontend\.git` |
| `A:\AGENTS_OS_Workspace\execution\Codex_Autonomous_Work_Harness\.git` |
| `A:\AGENTS_OS_Workspace\governance\Bounded-High-Autonomy\.git` |
| `A:\AGENTS_OS_Workspace\governance\codex-router\repo\.git` |
| `A:\AGENTS_OS_Workspace\runtime\VCPChat\.git` |
| `A:\AGENTS_OS_Workspace\runtime\VCPChatUP\.git` |
| `A:\AGENTS_OS_Workspace\runtime\VCPToolBox-JENN-Extensions\.git` |
| `A:\AGENTS_OS_Workspace\runtime\VCPToolBox\.git` |
| `A:\AGENTS_OS_Workspace\runtime\worktrees\colameta-dev\.git` |

## Canonical WSL Root Inventory

Root path: `/home/jenn/AGENTS_OS_Workspace`

### Top-Level Directories

| Directory | Last observed role |
| --- | --- |
| `archive/` | Canonical archive structure, including migration/archive categories. |
| `control-plane/` | New control-plane layer for contracts, policies, schemas, and task envelopes. |
| `domains/` | Target layer for domain systems. |
| `execution/` | Target layer for bridges, harness, providers, and workers. |
| `extensions/` | Target layer for Jenn/VCP userland extensions. |
| `governance/` | Target layer for governance projects; currently includes active `codex-router`. |
| `labs/` | Target layer for experimental systems such as `agent-image-lab`. |
| `memory/` | Target layer for memory system code. |
| `ops/` | Operational reports, validation, receipts, maintenance, dry-runs, and migration control. |
| `runtime/` | Target layer for upstream-trackable runtime core. |
| `state-private/` | Private state boundary; not inspected deeply. |

### Top-Level Files

| File | Evidence note |
| --- | --- |
| `_DIRECTORY_PRINCIPLES.md` | Present at root and hash-matched with Windows `DIRECTORY_PRINCIPLES_V1_1.md`. |
| `_MIGRATION_MAP.md` | Present at root and declares canonical/reference roots plus pending repo mappings. |
| `_ROOT_POLICY.md` | Present at root and declares WSL canonical execution root policy. |

### Shallow Git Repositories Observed

The following `.git` directory was observed under the WSL root with shallow
discovery. This is a repo signal only; no additional repository status was
recorded in this inventory.

| Repository signal |
| --- |
| `/home/jenn/AGENTS_OS_Workspace/governance/codex-router/.git` |

## Migration Map Signals

The WSL `_MIGRATION_MAP.md` currently records these source-to-target mappings as
`pending`. These are recorded as map evidence only; entries with source or
target conflicts require reconciliation before any migration plan can rely on
them.

| Windows source | WSL target | Status |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\governance\codex-router\repo` | `/home/jenn/AGENTS_OS_Workspace/governance/codex-router` | `pending` |
| `A:\Bounded High Autonomy` | `/home/jenn/AGENTS_OS_Workspace/governance/Bounded-High-Autonomy` | `pending` |
| `A:\Codex_Autonomous_Work_Harness` | `/home/jenn/AGENTS_OS_Workspace/governance/Codex_Autonomous_Work_Harness` | `pending` |
| `A:\AGENTS_OS_Workspace\runtime\VCPToolBox` | `/home/jenn/AGENTS_OS_Workspace/runtime/VCPToolBox` | `pending` |
| `A:\AGENTS_OS_Workspace\runtime\VCPToolBox-JENN-Extensions` | `/home/jenn/AGENTS_OS_Workspace/extensions/vcp-toolbox-jenn` | `pending` |
| `A:\AGENTS_OS_Workspace\runtime\VCPToolBox-JENN-LocalState` | `/home/jenn/AGENTS_OS_Workspace/state-private/VCPToolBox-JENN-LocalState` | `pending` |
| `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS_Control` | `/home/jenn/AGENTS_OS_Workspace/domains/Photo_Studio_OS` | `pending` |
| `A:\AGENTS_OS_Workspace\labs\agent-image-lab` | `/home/jenn/AGENTS_OS_Workspace/labs/agent-image-lab` | `pending` |
| `A:\AGENTS_OS_Workspace\memory\codex-memory` | `/home/jenn/AGENTS_OS_Workspace/memory/codex-memory` | `pending` |

## Reconciliation Notes

The following conflicts were found between the migration map, shallow repository
signals, and candidate-table assumptions:

| Item | Conflict | Required resolution |
| --- | --- | --- |
| `Bounded-High-Autonomy` | Migration map source is `A:\Bounded High Autonomy`, while shallow repo discovery observed `A:\AGENTS_OS_Workspace\governance\Bounded-High-Autonomy\.git`. | Decide which path is the authoritative source before planning. |
| `Codex_Autonomous_Work_Harness` | Migration map source is `A:\Codex_Autonomous_Work_Harness` and target is under `governance/`; shallow repo discovery observed `A:\AGENTS_OS_Workspace\execution\Codex_Autonomous_Work_Harness\.git`. | Source path resolved to `A:\AGENTS_OS_Workspace\execution\Codex_Autonomous_Work_Harness`; target layer resolved to `governance/` based on its current rules, gates, validation rails, and operating-guidance role. |
| `Photo_Studio_OS` | Migration map names `Photo_Studio_OS_Control` as the source, while shallow repo discovery observed an aggregate `Photo_Studio_OS` repo plus Backend, Control, and Frontend repos. | Decide whether the migration source is the aggregate repo, Control only, or a multi-repo layout. |
| `codex-memory` | Migration map source is `A:\AGENTS_OS_Workspace\memory\codex-memory`, while an additional path check observed `A:\codex-memory`; `A:\AGENTS_OS_Workspace\memory` was not present in the root-level check. | Decide the authoritative source path before planning. |

Resolution record:

- `../decisions/source-path-reconciliation-2026-06-27.md`
- `../decisions/target-layer-reconciliation-2026-06-27.md`

## Interpretation

- The Windows root is the fuller historical/reference workspace.
- The WSL root is the canonical execution root and has the cleaner target
  architecture.
- Directory principles are synchronized between the roots, but project content
  is not fully migrated.
- The migration map still records key project mappings as pending.
- `state-private/` exists on both sides and remains outside this inventory's
  read scope.

## Open Questions

- Which Windows repositories are still active sources of truth?
- Which Windows repositories should be freshly cloned into WSL instead of copied?
- Which evidence, backup, and worktree directories should remain Windows-only
  reference material?
- Which root-level Windows files should become canonical WSL control-plane or
  governance documents?
- What validation should be required before each `pending` mapping can become
  `complete`?
