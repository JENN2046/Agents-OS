# Rules Assets Migration Plan - 2026-06-27

Status: planning only，非迁移授权。

This plan prepares the low-risk rules and control-plane asset migration from
the Windows reference root into the canonical WSL root. It does not authorize
copying, moving, deleting, executing, pushing, syncing, or changing source
projects.

## Goal

Establish the WSL `control-plane/`, `governance/`, `extensions/`, and `ops/`
documentation surfaces before migrating heavier repositories. The intended
result is a clearer canonical rule surface, not a bulk copy of the Windows
workspace.

## Scope

| Source | Proposed WSL target | Plan label | Notes |
| --- | --- | --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts` | `control-plane/contracts` | plan | Schema and contract material. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\registry` | `control-plane/registry` | plan | Registry examples and protected-path examples. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks` | `control-plane/runbooks` or `ops/migration/decisions` by topic | plan | Runbooks need topic review before placement. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\prompts` | `control-plane/prompts` | plan | Prompt assets need sensitivity and freshness review. |
| `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml` | WSL root or `control-plane/registry/WORKSPACE_REGISTRY.yaml` | plan | Prefer canonical registry copy after path reconciliation. |
| `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | WSL root or `governance/SECURITY_BOUNDARIES.md` | plan | Safety boundary material; should remain prominent. |
| `A:\AGENTS_OS_Workspace\templates` | `control-plane/templates` or `extensions/templates` by template type | plan | Do not copy templates until target ownership is clear. |
| `A:\AGENTS_OS_Workspace\ops\scripts` | `ops/validation` or `ops/maintenance` | plan | Scripts likely need Linux path adaptation and shell safety review. |

## Non-Goals

- Do not migrate runtime projects such as `VCPToolBox`.
- Do not migrate domain systems such as `Photo_Studio_OS`.
- Do not migrate memory systems such as `codex-memory`.
- Do not inspect or migrate `state-private/`.
- Do not copy `.env`, secrets, tokens, logs, caches, local databases, or runtime
  output.
- Do not rewrite `_MIGRATION_MAP.md` in this plan.
- Do not execute migrated scripts during planning.
- Do not push, tag, release, deploy, or write to any remote.

## Existing Evidence

| Evidence | Source |
| --- | --- |
| WSL is canonical execution root; Windows is reference root. | `_ROOT_POLICY.md`, `_MIGRATION_MAP.md` |
| Directory principles match between Windows and WSL. | `roots-inventory-2026-06-27.md` |
| A Windows `AGENTS_OS/` control-plane-like tree exists. | Shallow root inventory |
| WSL `control-plane/` exists with `contracts`, `policies`, `schemas`, and `task-envelope`. | Shallow root inventory |
| Root-level Windows registry/security/template/script assets exist. | Shallow source inspection |

## Proposed Sequence

### Phase 0 - Preflight Inventory

Create a read-only file inventory for the rules assets only.

Planned output:

```text
ops/migration/inventory/rules-assets-inventory-2026-06-27.md
```

Required checks:

- List files under `A:\AGENTS_OS_Workspace\AGENTS_OS` without reading secret
  locations.
- List files under `A:\AGENTS_OS_Workspace\templates`.
- List files under `A:\AGENTS_OS_Workspace\ops\scripts`.
- Record file names, sizes, modified times, and proposed target area.
- Mark files that require content review before migration.

Stop if:

- Any source path unexpectedly contains real `.env`, secret, credential,
  private memory, or local runtime data.
- A candidate is not clearly a rules/control-plane asset.

### Phase 1 - Target Ownership Decisions

Decide target placement before copying content.

Planned outputs:

```text
ops/migration/decisions/control-plane-assets-targets-2026-06-27.md
ops/migration/decisions/rules-templates-targets-2026-06-27.md
ops/migration/decisions/ops-scripts-targets-2026-06-27.md
```

Decision questions:

- Should `WORKSPACE_REGISTRY.yaml` live at WSL root, under
  `control-plane/registry`, or both with one canonical source?
- Should `SECURITY_BOUNDARIES.md` live at WSL root, under `governance/`, or
  both with one canonical source?
- Which templates are control-plane templates, extension templates, or obsolete
  templates?
- Which Windows shell scripts are portable enough for WSL, and which should be
  rewritten rather than copied?

Stop if:

- A target path would blur control-plane, governance, extension, and ops
  ownership.
- A script requires Windows-only behavior that should not become canonical in
  WSL.

### Phase 2 - Draft Migration Patch

Prepare a minimal local docs/config patch after Phase 0 and Phase 1 are
accepted.

Allowed changes in this future phase:

- Add selected docs, schemas, registry examples, templates, or scripts to WSL.
- Preserve source attribution and reference path.
- Add README notes explaining whether the migrated file is canonical,
  reference-only, or pending validation.

Forbidden changes in this future phase:

- Bulk-copy entire directories without review.
- Copy generated output, caches, logs, env files, or private state.
- Make scripts executable by default without review.
- Update remote repositories or branches.

### Phase 3 - Validation

Validation should remain local and narrow.

Required validation:

- Inspect generated diffs.
- Run a filename/path sanity check for forbidden names:
  `.env`, `secret`, `token`, `credential`, `cache`, `logs`, `node_modules`,
  `.venv`, `dist`, `build`, `tmp`.
- For shell scripts, run syntax-only checks where available.
- Confirm migrated README files state their role and boundaries.

Suggested checks:

```powershell
Get-ChildItem -Recurse <target-path> | Select-Object FullName,Length,LastWriteTime
```

```bash
find <target-path> -maxdepth 4 -type f -print
```

Do not run migrated scripts as functional tests until a separate execution-safe
validation plan exists.

### Phase 4 - Receipt

After any actual migration, create a receipt.

Planned output:

```text
ops/migration/receipts/rules-assets-migration-receipt-YYYY-MM-DD.md
```

Receipt should include:

- Source paths used.
- Target paths written.
- Files intentionally skipped.
- Secret/private-state checks performed.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Open Risks

| Risk | Mitigation |
| --- | --- |
| Old Windows docs may be stale. | Inventory first, then decision docs before copying. |
| Root-level docs may conflict with WSL `_ROOT_POLICY.md`. | Treat WSL root policy as authority. |
| Templates may encode old paths or names. | Review and normalize before migration. |
| Shell scripts may assume Windows paths or old layout. | Port deliberately; do not execute by default. |
| Registry examples may overstate active projects. | Mark examples as examples unless verified current. |

## Recommended Next Step

Create the Phase 0 inventory:

```text
ops/migration/inventory/rules-assets-inventory-2026-06-27.md
```

That inventory should still be read-only and should not copy or modify source
assets.

## Related Documents

- `../README.md`
- `../inventory/roots-inventory-2026-06-27.md`
- `../candidates/migration-candidates-2026-06-27.md`
- `../decisions/source-path-reconciliation-2026-06-27.md`
- `../decisions/target-layer-reconciliation-2026-06-27.md`

