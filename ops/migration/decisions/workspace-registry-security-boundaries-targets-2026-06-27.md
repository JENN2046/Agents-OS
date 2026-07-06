# Workspace Registry And Security Boundaries Target Decision - 2026-06-27

Status: target-placement decision only，非迁移授权。

This decision record resolves the authoritative WSL target locations for
`WORKSPACE_REGISTRY.yaml` and `SECURITY_BOUNDARIES.md`. It does not authorize
copying, moving, deleting, executing, pushing, syncing, or changing source
assets.

## Scope

| Item | Value |
| --- | --- |
| Decision type | Target placement reconciliation |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source files reviewed | `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml`, `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` |
| Evidence used | `_ROOT_POLICY.md`, `_MIGRATION_MAP.md`, `_DIRECTORY_PRINCIPLES.md`, `control-plane/README.md`, `governance/README.md`, Phase 0 rules inventory |
| Private state review | Not performed |
| Secret value review | No secret values reviewed; filenames and allowed secret-like patterns were observed in security docs only |
| Migration performed | No |

## Decisions

| Source file | Authoritative WSL target for planning | Decision | Non-authoritative placements | Reason |
| --- | --- | --- | --- | --- |
| `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml` | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/WORKSPACE_REGISTRY.yaml` | Put the canonical registry under `control-plane/registry/`. | WSL root `WORKSPACE_REGISTRY.yaml`; `governance/WORKSPACE_REGISTRY.yaml` | The file is a workspace/layer/repository registry. The WSL principles say the old `AGENTS_OS/` control-plane material is represented by `control-plane/`, and `control-plane/README.md` allows contracts, schemas, policy files, and root rules. It is reference data used by governance, not itself a governance/hard-gate implementation. |
| `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | `/home/jenn/AGENTS_OS_Workspace/governance/SECURITY_BOUNDARIES.md` | Put the canonical safety boundary document under `governance/`. | WSL root `SECURITY_BOUNDARIES.md`; `control-plane/policies/SECURITY_BOUNDARIES.md` | The file defines absolute safety boundaries, private-state boundaries, git boundaries, runtime gates, permission levels, high-risk areas, and risk reporting. The WSL principles define `governance/` as the place for governance, safety, authorization, routing, and hard gates. |

## Root Directory Rule

The WSL root should not hold full duplicate copies of these two files as
authoritative assets.

Allowed later, under a separate scoped edit:

- A short root pointer from `_ROOT_POLICY.md` or another root index to
  `control-plane/registry/WORKSPACE_REGISTRY.yaml`.
- A short root pointer from `_ROOT_POLICY.md` to
  `governance/SECURITY_BOUNDARIES.md`.

Not allowed by this decision:

- Keeping two authoritative copies of the same registry or boundary file.
- Treating the Windows root copy as canonical after migration.
- Creating target directories or copying files without a Phase 2 migration
  patch.

## Content Review Required Before Migration

| File | Required review |
| --- | --- |
| `WORKSPACE_REGISTRY.yaml` | Normalize old `AGENTS_OS/` references to the WSL control-plane layout where appropriate; verify listed repositories and paths against current source-path decisions. |
| `SECURITY_BOUNDARIES.md` | Reconcile high-risk path examples with current target-layer decisions, especially the `Codex_Autonomous_Work_Harness` target under `governance/`. |

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| Make WSL root `WORKSPACE_REGISTRY.yaml` authoritative | Rejected | Root discoverability is useful, but registry ownership belongs with control-plane registry material. A root copy would create drift risk. |
| Put `WORKSPACE_REGISTRY.yaml` under `governance/` | Rejected | Governance may consume registry data, but the file is inventory and layer metadata, not a hard-gate implementation. |
| Make WSL root `SECURITY_BOUNDARIES.md` authoritative | Rejected | Root visibility is useful, but the existing root already has `_ROOT_POLICY.md` as a bootstrap policy. A full duplicate security document at root would create drift risk. |
| Put `SECURITY_BOUNDARIES.md` under `control-plane/policies/` | Rejected | The content is dominated by safety, authorization, hard stops, permission levels, and risk reporting; that belongs with governance. |

## Migration Implications

| Follow-up | Required action |
| --- | --- |
| Target directory creation | Create `control-plane/registry/` only inside a later approved migration patch. |
| Registry migration | Copy or rewrite `WORKSPACE_REGISTRY.yaml` only after content normalization and path verification. |
| Security boundary migration | Copy or rewrite `SECURITY_BOUNDARIES.md` only after stale high-risk paths are reconciled. |
| Root references | Add root pointers only if needed for discoverability, and keep them non-authoritative. |
| Receipts | Any actual migration must produce a receipt with source path, target path, skipped items, and validation. |

## Related Documents

- `../inventory/rules-assets-inventory-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `source-path-reconciliation-2026-06-27.md`
- `target-layer-reconciliation-2026-06-27.md`
