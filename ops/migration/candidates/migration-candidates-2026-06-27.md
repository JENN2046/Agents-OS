# Migration Candidates - 2026-06-27

Status: 只读初评，非迁移授权。

This table is a directory-level and project-level first pass. It is based on
read-only inspection of the Windows reference root and the WSL canonical root.
It does not authorize copying, moving, deleting, executing, pushing, or changing
any project.

## Label Meaning

| Label | Meaning |
| --- | --- |
| `迁移` | Candidate should enter a scoped migration plan. This is not permission to move it yet. |
| `归档` | Candidate should remain historical or be moved only into an archive area. |
| `保留参考` | Candidate should stay available as comparison, evidence, or source material. |
| `暂缓` | Candidate needs more read-only review before any decision. |

## Candidates

| Candidate | Current source | Suggested target | Label | Rationale |
| --- | --- | --- | --- | --- |
| `AGENTS_OS/` control plane | `A:\AGENTS_OS_Workspace\AGENTS_OS` | WSL `control-plane/` | 迁移 | The concept is now represented by `control-plane`; useful contracts, registries, prompts, and runbooks can be split into the new structure. |
| `WORKSPACE_REGISTRY.yaml` | `A:\AGENTS_OS_Workspace` | WSL root or `control-plane/registry` | 迁移 | High-value workspace index; should become part of the canonical root metadata after review. |
| `SECURITY_BOUNDARIES.md` | `A:\AGENTS_OS_Workspace` | WSL root or `governance/` | 迁移 | Long-lived safety boundary material. |
| `templates/` | `A:\AGENTS_OS_Workspace\templates` | WSL `control-plane/` or `extensions/templates` | 迁移 | Reusable assets, but should be cleaned against the newer naming and directory rules. |
| `ops/scripts/` | `A:\AGENTS_OS_Workspace\ops\scripts` | WSL `ops/validation` or `ops/maintenance` | 迁移 | Validation scripts are valuable, but likely need Linux path adaptation. |
| `governance/codex-router/repo` | `A:\AGENTS_OS_Workspace\governance\codex-router\repo` | Already present at WSL `governance/codex-router` | 保留参考 | WSL has the active repo; the Windows copy should remain comparison/history until proven unnecessary. |
| `Bounded-High-Autonomy` | `A:\AGENTS_OS_Workspace\governance\Bounded-High-Autonomy` | WSL `governance/Bounded-High-Autonomy` | 迁移 | Source path reconciled in `../decisions/source-path-reconciliation-2026-06-27.md`; still needs scoped clone/copy and validation plan. |
| `approval-gates` / `policy-packs` | `A:\AGENTS_OS_Workspace\governance` | WSL `governance/` | 迁移 | Governance rule assets that fit the target layer. |
| `audit-policy` / `circuit-breakers` | `A:\AGENTS_OS_Workspace\governance` | WSL `governance/` | 迁移 | Rule assets, pending freshness review. |
| `Codex_Autonomous_Work_Harness` | `A:\AGENTS_OS_Workspace\execution\Codex_Autonomous_Work_Harness` | WSL `governance/Codex_Autonomous_Work_Harness` | 迁移 | Current role is governance-oriented rules, gates, validation rails, and operating guidance. Source path reconciled in `../decisions/source-path-reconciliation-2026-06-27.md`; target layer reconciled in `../decisions/target-layer-reconciliation-2026-06-27.md`. |
| `execution/checkpoints` / `execution/receipts` | `A:\AGENTS_OS_Workspace\execution` | WSL `ops/receipts` or `archive` | 暂缓 | May contain evidence or private traces; needs sensitivity review first. |
| `execution/runners` / `desktop-bridges` | `A:\AGENTS_OS_Workspace\execution` | WSL `execution/` | 暂缓 | Potentially useful, but execution-layer risk is higher than docs or registry assets. |
| `VCPToolBox` | `A:\AGENTS_OS_Workspace\runtime\VCPToolBox` | WSL `runtime/VCPToolBox` | 迁移 | Runtime core should live under the canonical root, preferably through a fresh clone/sync plan rather than bulk copy. |
| `VCPToolBox-JENN-Extensions` | `A:\AGENTS_OS_Workspace\runtime\VCPToolBox-JENN-Extensions` | WSL `extensions/vcp-toolbox-jenn` | 迁移 | Jenn-specific userland capability should move out of core runtime. |
| `VCPToolBox-JENN-LocalState` | `A:\AGENTS_OS_Workspace\runtime\VCPToolBox-JENN-LocalState` | WSL `state-private/VCPToolBox-JENN-LocalState` | 暂缓 | Private/local state boundary; not a normal migration candidate. |
| `VCPToolBox-core-patches` | `A:\AGENTS_OS_Workspace\runtime\VCPToolBox-core-patches` | WSL `runtime/upstream-sync-notes` or `archive` | 保留参考 | Likely upstream patch evidence; should not be mixed directly into core. |
| `upstream-sync-notes` | `A:\AGENTS_OS_Workspace\runtime\upstream-sync-notes` | WSL `runtime/upstream-sync-notes` | 迁移 | Long-term maintenance records for upstream tracking. |
| `VCPChat` | `A:\AGENTS_OS_Workspace\runtime\VCPChat` | To be decided | 暂缓 | Appears to be runtime history or a legacy system; active status is unverified. |
| `VCPChatUP` | `A:\AGENTS_OS_Workspace\runtime\VCPChatUP` | To be decided | 暂缓 | Could be an upstream or upgrade copy; do not migrate blindly. |
| `VCP_CLEAN_CORE_*` | `A:\AGENTS_OS_Workspace\runtime` | WSL `archive/windows-migration` or runtime docs | 保留参考 | Looks like clean-core experiment/evidence material, not a canonical runtime source. |
| `VCPToolBox-clean-core-fs0/fs5a` | `A:\AGENTS_OS_Workspace\runtime` | WSL `archive` | 暂缓 | Multiple variants; needs review for unmerged useful work. |
| `ColaMeta` | `A:\AGENTS_OS_Workspace\runtime\ColaMeta` | To be decided | 暂缓 | Role and target layer were not established in the migration map. |
| `runtime/worktrees` | `A:\AGENTS_OS_Workspace\runtime\worktrees` | Archive only if needed | 归档 | Worktrees should not be treated as canonical project sources. |
| `runtime/evidence` | `A:\AGENTS_OS_Workspace\runtime\evidence` | WSL `ops/reports` or `archive` | 保留参考 | Evidence may be valuable, but it is not an execution project. |
| `Photo_Studio_OS` | `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS` | WSL `domains/Photo_Studio_OS` | 暂缓 | Whole-domain source path reconciled in `../decisions/source-path-reconciliation-2026-06-27.md`; repo layout and staged migration scope still need a decision. |
| `Photo_Studio_OS_Backend/Control/Frontend` | Observed repo signals under `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS\...` plus separate top-level Windows directory names | WSL `domains/Photo_Studio_OS` under a chosen repo layout | 暂缓 | Needs a single-repo vs multi-repo vs aggregate decision before migration. |
| `agent-image-lab` canonical repo | `A:\AGENTS_OS_Workspace\domains\agent-image-lab\repo\agent-image-lab` | WSL `labs/agent-image-lab` | 迁移 | Better fit for `labs` than `domains` based on current directory principles. |
| `agent-image-lab-v0.2` | `A:\AGENTS_OS_Workspace\domains\agent-image-lab` | WSL `labs` or `archive` | 暂缓 | Needs de-duplication against the canonical repo. |
| `agent-image-lab` backup directories | `A:\AGENTS_OS_Workspace\domains\agent-image-lab` | WSL `archive/windows-migration` | 归档 | Backup directories should not enter active project paths. |
| `Jenn-VCP-Extensions` | `A:\AGENTS_OS_Workspace\extensions\Jenn-VCP-Extensions` | WSL `extensions/vcp-toolbox-jenn` | 迁移 | Aligns with the new extension boundary. |
| `extension-standard` | `A:\AGENTS_OS_Workspace\extensions\extension-standard` | WSL `control-plane/contracts` or `extensions` | 迁移 | Standards and manifest material are reusable control-plane assets. |
| `codex-memory` | `A:\codex-memory` | WSL `memory/codex-memory` | 迁移 | Source path reconciled in `../decisions/source-path-reconciliation-2026-06-27.md`; migration plan must explicitly exclude secrets, logs, temp data, cache, and private/local state. |
| `state-private/` | `A:\AGENTS_OS_Workspace\state-private` | WSL `state-private/` | 暂缓 | High-sensitivity area; only explicit scoped authorization can review or move contents. |
| `archive/` | `A:\AGENTS_OS_Workspace\archive` | WSL `archive/windows-migration` | 保留参考 | Useful historical source, but should not be bulk-migrated as active code. |

## Notes

- The WSL root is the canonical execution root.
- The Windows root remains the reference and historical source until each item
  is reviewed.
- A `迁移` label means "prepare a scoped plan", not "move now".
- A `暂缓` label usually means more evidence is needed about sensitivity,
  freshness, duplication, execution risk, or target ownership.
- Source path conflicts for `Bounded-High-Autonomy`,
  `Codex_Autonomous_Work_Harness`, `Photo_Studio_OS`, and `codex-memory` are
  recorded in `../decisions/source-path-reconciliation-2026-06-27.md`.
- `Codex_Autonomous_Work_Harness` target-layer placement is recorded in
  `../decisions/target-layer-reconciliation-2026-06-27.md`.
