# AGENTS OS Migration Control

Status: 只读初评，非迁移授权。

This folder is the migration control surface for moving AGENTS OS workspace
assets from the Windows reference root into the canonical WSL root.

It does not authorize copying, deleting, rewriting, pushing, syncing, or
executing any project. Every migration action still requires a separate scoped
plan, validation path, and explicit approval when it crosses a write, remote,
private-state, or execution boundary.

## Roots

| Role | Path |
| --- | --- |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Windows reference root | `A:\AGENTS_OS_Workspace` |

## Purpose

- Track migration candidates.
- Separate observed facts from assumptions.
- Record migration decisions before moving files.
- Keep receipts for completed migration steps.
- Prevent archive, runtime, private state, and execution assets from being
  mixed into the canonical root without review.

## Planned Layout

Only directories that already contain documents are materialized right now.
Other directories below are planned control surfaces and should be created when
their first document is added.

| Directory | Purpose |
| --- | --- |
| `inventory/` | Read-only inventories of roots, projects, repositories, and notable assets. |
| `candidates/` | Candidate tables with `迁移`, `归档`, `保留参考`, or `暂缓` labels. |
| `plans/` | Scoped migration plans prepared before any write action. |
| `decisions/` | Rationale for migrate/archive/reference/defer decisions. |
| `receipts/` | Validation and closeout records after completed migration actions. |

## Boundaries

- `state-private/` is denied by default and must not be inventoried deeply
  without explicit authorization.
- Secrets, tokens, real env files, private memory, local databases, and runtime
  cache must not be copied into source repositories.
- `archive/` and Windows reference roots are not execution roots.
- Worktrees, backups, generated outputs, `node_modules`, `.venv`, `dist`,
  `build`, cache, logs, and local runtime artifacts are not migration sources
  unless a later plan explicitly says otherwise.
- Git remote writes, pushes, PRs, releases, deploys, branch deletion, and
  history rewrites are out of scope for this folder unless separately approved.

## Current Documents

- `inventory/roots-inventory-2026-06-27.md`
- `inventory/rules-assets-inventory-2026-06-27.md`
- `candidates/migration-candidates-2026-06-27.md`
- `decisions/control-plane-assets-targets-2026-06-27.md`
- `decisions/ops-scripts-targets-2026-06-27.md`
- `decisions/prompts-targets-2026-06-27.md`
- `decisions/runbooks-targets-2026-06-27.md`
- `decisions/source-path-reconciliation-2026-06-27.md`
- `decisions/target-layer-reconciliation-2026-06-27.md`
- `decisions/templates-targets-2026-06-27.md`
- `decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `plans/phase-2-batch-1-contracts-registry-examples-patch-plan-2026-06-27.md`
- `plans/phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `plans/rules-assets-migration-plan-2026-06-27.md`
