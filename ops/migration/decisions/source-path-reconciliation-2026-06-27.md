# Source Path Reconciliation - 2026-06-27

Status: source-path decision only，非迁移授权。

This decision record resolves the authoritative source path for four migration
candidate conflicts found during the shallow inventory review. It does not
authorize copying, moving, deleting, executing, pushing, syncing, or changing
any project.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Source path reconciliation |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Evidence used | Path existence checks, shallow `.git` signals from inventory, `WORKSPACE_REGISTRY.yaml`, and `_MIGRATION_MAP.md` |
| Private state review | Not performed |
| Secret value review | Not performed |
| Project source review | Not performed |

## Decisions

| Item | Authoritative source path for planning | Decision | Rejected or superseded source path | Reason |
| --- | --- | --- | --- | --- |
| `Bounded-High-Autonomy` | `A:\AGENTS_OS_Workspace\governance\Bounded-High-Autonomy` | Use workspace governance path as the source path. | `A:\Bounded High Autonomy` | The workspace governance path exists and had a shallow `.git` signal. The root-level path from `_MIGRATION_MAP.md` did not exist during this check. `WORKSPACE_REGISTRY.yaml` also places `Bounded-High-Autonomy` in the governance layer. |
| `Codex_Autonomous_Work_Harness` | `A:\AGENTS_OS_Workspace\execution\Codex_Autonomous_Work_Harness` | Use workspace execution path as the source path. | `A:\Codex_Autonomous_Work_Harness` | The workspace execution path exists and had a shallow `.git` signal. The root-level path from `_MIGRATION_MAP.md` did not exist during this check. Target-layer placement is resolved separately in `target-layer-reconciliation-2026-06-27.md`. |
| `Photo_Studio_OS` | `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS` | Use the aggregate `Photo_Studio_OS` path as the source path for whole-domain planning. | `A:\AGENTS_OS_Workspace\domains\Photo_Studio_OS_Control` as a whole-domain source | The aggregate path exists, had a shallow `.git` signal, and contains Backend, Control, and Frontend subdirectories. `WORKSPACE_REGISTRY.yaml` names `Photo_Studio_OS` as the domain repository. `Photo_Studio_OS_Control` can still be used for a narrower control-only plan, but it is not the authoritative source for whole-domain migration. |
| `codex-memory` | `A:\codex-memory` | Use the root-level `A:\codex-memory` path as the source path. | `A:\AGENTS_OS_Workspace\memory\codex-memory` | `A:\codex-memory` exists and contains a `.git` directory plus project-like directories. `A:\AGENTS_OS_Workspace\memory` and `A:\AGENTS_OS_Workspace\memory\codex-memory` did not exist during this check. This source also contains env/log/tmp-like material by name, so any later migration plan must exclude secrets and runtime artifacts explicitly. |

## Follow-Up Required

| Item | Remaining decision before migration planning |
| --- | --- |
| `Bounded-High-Autonomy` | Decide clone vs copy strategy and validation command set. |
| `Codex_Autonomous_Work_Harness` | Target layer resolved in `target-layer-reconciliation-2026-06-27.md`; next decide clone vs copy strategy and validation command set. |
| `Photo_Studio_OS` | Decide whole-domain aggregate migration vs staged Backend/Control/Frontend migration. |
| `codex-memory` | Decide sanitized migration strategy that excludes `.env`, logs, temp data, runtime cache, and private/local state. |

## Related Documents

- `../inventory/roots-inventory-2026-06-27.md`
- `../candidates/migration-candidates-2026-06-27.md`
- `target-layer-reconciliation-2026-06-27.md`
