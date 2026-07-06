# Phase 2 Batch 1 Patch Plan - Contracts And Registry Examples - 2026-06-27

Status: patch plan only，非迁移授权。

This document defines the proposed local patch for Phase 2 Batch 1. It lists
the exact directories and files that a later authorized patch would create or
rewrite. It does not authorize copying, moving, deleting, executing scripts,
changing executable bits, pushing, syncing, merging, or changing source assets.

## Batch Scope

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 1 |
| Batch name | Contracts and registry examples |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Included source areas | `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts`, `A:\AGENTS_OS_Workspace\AGENTS_OS\registry` |
| Included asset types | One extension manifest schema, two target-native README files, two registry example files |
| Excluded asset types | `WORKSPACE_REGISTRY.yaml`, `SECURITY_BOUNDARIES.md`, prompts, runbooks, templates, scripts, private state |
| Migration performed | No |
| Validation executed | No |

## Current Target Status

| Target path | Current status |
| --- | --- |
| `control-plane/contracts/` | Exists. |
| `control-plane/contracts/jenn-extension.manifest.schema.json` | Not observed. |
| `control-plane/contracts/README.md` | Not observed. |
| `control-plane/registry/` | Not observed. |
| `control-plane/registry/README.md` | Not observed. |
| `control-plane/registry/examples/` | Not observed. |
| `control-plane/registry/examples/extensions.example.yaml` | Not observed. |
| `control-plane/registry/examples/protected-paths.example.yaml` | Not observed. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Not observed; explicitly excluded from this batch. |

## Proposed Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/` | Required target directory for registry README and examples. |
| Create directory | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/` | Keeps example registry files below the future canonical registry location. |

No new `control-plane/contracts/` directory is needed because it already exists.

## Proposed File Changes

| Action | Target file | Source file | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/jenn-extension.manifest.schema.json` | `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\jenn-extension.manifest.schema.json` | Copy content only after JSON parse succeeds and no secret-like example values are found. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/README.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\README.AGENTS_OS.md` | Rewrite/adapt as target-native README; remove or qualify validation script references that are not migrated yet. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/README.md` | `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\README.AGENTS_OS.md` | Rewrite/adapt as target-native README; clarify examples vs authoritative registry files. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/extensions.example.yaml` | `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\extensions.example.yaml` | Copy or lightly normalize as example-only material; mark historical paths as unverified if not updated. |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/protected-paths.example.yaml` | `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\protected-paths.example.yaml` | Copy or lightly normalize as example-only material; do not treat as active protection registry. |

No existing target file is planned to be modified in this batch.

## Explicitly Out Of Scope

| Path or asset | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml` | Reserved for a later registry/security authority batch. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/WORKSPACE_REGISTRY.yaml` | Future canonical registry target, but not part of Batch 1. |
| `A:\AGENTS_OS_Workspace\SECURITY_BOUNDARIES.md` | Reserved for a later registry/security authority batch. |
| Any `ops/scripts` file | Scripts require separate execution-safety review. |
| Any prompt, runbook, or template | Covered by later batches. |
| `state-private/` | Denied by default and not part of this migration stream. |

## Pre-Patch Checks Required

Before any later implementation patch, perform these checks:

| Check | Purpose |
| --- | --- |
| Reconfirm source file existence and size. | Ensure the Windows reference files have not changed unexpectedly. |
| Reconfirm target file nonexistence. | Avoid overwriting user-owned work. |
| Parse `jenn-extension.manifest.schema.json` as JSON. | Ensure schema syntax is valid before copy. |
| Parse the two `.example.yaml` files as YAML where tooling is available. | Ensure examples are structurally readable before copy. |
| Path scan proposed target content for `.env`, `secret`, `token`, `credential`, `cache`, `logs`, `node_modules`, `.venv`, `dist`, `build`, and `tmp`. | Prevent obvious forbidden or runtime artifacts from entering the batch. |
| Review README references to validation scripts. | Avoid documenting scripts as available before script migration. |
| Review registry example paths. | Avoid presenting stale `extensions/Jenn-VCP-Extensions/...` paths as verified WSL paths. |

## Planned Content Rules

- Target README files must use `README.md`, not `README.AGENTS_OS.md`.
- Registry example files must remain under `control-plane/registry/examples/`.
- Registry examples must be clearly marked as examples, not active registry
  state.
- Batch 1 must not create `extensions.yaml`, `protected-paths.yaml`, or
  `WORKSPACE_REGISTRY.yaml`.
- Batch 1 must not run any validator script.
- Batch 1 must not create executable files.

## Post-Patch Validation Plan

If this patch is later authorized and applied, run only local, read-only or
syntax-level validation:

| Validation | Command or method | Notes |
| --- | --- | --- |
| Inspect target file list | `find control-plane/contracts control-plane/registry -maxdepth 4 -type f -print` | Confirm only planned files were created. |
| JSON syntax check | Parse `control-plane/contracts/jenn-extension.manifest.schema.json` with an available JSON parser. | Use local parser only. |
| YAML syntax check | Parse registry example YAML files if a local YAML parser is available. | Skip with note if no parser is available. |
| Forbidden-name scan | Search planned target paths and content for secret/runtime names listed above. | Do not read or print any real secret file. |
| Diff review | Inspect the local patch. | Confirm no unrelated files changed. |

Do not run migrated or source validator scripts in Batch 1.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-1-contracts-registry-examples-receipt-2026-06-27.md
```

The receipt should record:

- Exact authorization wording.
- Source files read.
- Target directories created.
- Target files created.
- Files explicitly skipped.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Plan

Because this batch should only create new target directories and files, rollback
should be possible by removing the newly added Batch 1 files and any empty
directories created only for this batch:

```text
control-plane/contracts/jenn-extension.manifest.schema.json
control-plane/contracts/README.md
control-plane/registry/README.md
control-plane/registry/examples/extensions.example.yaml
control-plane/registry/examples/protected-paths.example.yaml
control-plane/registry/examples/
control-plane/registry/
```

Rollback must not remove directories that later contain unrelated user work.

## Hard Rule Before Implementation

Registry example files must preserve source values, add comments only to mark
historical or unverified paths, and defer path normalization to a later
extension-asset migration decision batch.

## Related Documents

- `phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `rules-assets-migration-plan-2026-06-27.md`
- `../decisions/control-plane-assets-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../inventory/rules-assets-inventory-2026-06-27.md`
