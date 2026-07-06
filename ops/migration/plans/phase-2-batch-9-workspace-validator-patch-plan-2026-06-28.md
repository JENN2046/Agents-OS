# Phase 2 Batch 9 Workspace Validator Patch Plan - 2026-06-28

Status: patch plan only; no script created.

Notice: This document plans a future workspace validator script patch. It is not
migration authorization, not authorization to create `ops/validation/validate-workspace.sh`
yet, not authorization to execute source or migrated validation scripts, not
authorization to change executable bits, and not authorization for remote,
branch, push, release, deploy, secret, private-state, log, cache, or runtime
actions.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 9 |
| Batch name | Workspace validator |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source validator | `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` |
| Source SHA-256 | `e3fa994fa659180fae3d9e21d87d3983ca881382b989348d63fe9b6c147a9271` |
| Rewrite plan | `ops/migration/plans/phase-2-batch-9-workspace-validator-rewrite-plan-2026-06-28.md` |
| Rewrite plan SHA-256 | `e7a4f9d2f93e63fb8c47a574569d7287bd05f8f4b87573ab789b86a09ec94836` |
| Planned target script | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-workspace.sh` |
| Script created now | No |
| Script execution performed | No |

## Scope Decision: Current-Only vs Current Plus Deferred Warnings

Selected future script behavior:

```text
Current checks are failures; deferred checks are warnings.
```

That means a future authorized script should:

- exit non-zero only when a current required WSL path is missing
- report deferred paths as migration-state warnings
- keep deferred warnings out of the failure count
- avoid treating uncompleted migrations as broken workspace state
- avoid silently forgetting deferred authority items

## Rejected Behavior

| Option | Decision | Reason |
| --- | --- | --- |
| Check only current required paths | Rejected | Too quiet; would hide important deferred items such as the registry and local `AGENTS.md` decision. |
| Treat current paths and deferred paths as failures | Rejected | Too noisy; would fail because known future-migration items are not supposed to exist yet. |
| Preserve old Windows required list as-is | Rejected | Encodes stale `README.AGENTS_OS.md`, root registry, root security, and `AGENTS_OS/` assumptions. |

## Planned Future File Changes

If this patch is later authorized, create exactly:

```text
ops/validation/validate-workspace.sh
ops/migration/receipts/rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md
```

Do not update `ops/validation/README.md` in this batch unless a later review
finds that the README must list the workspace validator. The first script patch
should stay focused.

## Current Required Paths

A future authorized script should treat these as required current WSL paths:

```text
_ROOT_POLICY.md
_DIRECTORY_PRINCIPLES.md
_MIGRATION_MAP.md
control-plane/README.md
runtime/README.md
governance/README.md
governance/SECURITY_BOUNDARIES.md
execution/README.md
extensions/README.md
domains/README.md
state-private/README.md
ops/README.md
labs/README.md
memory/README.md
archive/README.md
```

Planned failure behavior:

- print missing required path names only
- do not print file contents
- exit non-zero if any required current path is missing
- otherwise report required path checks as passed

## Deferred Warning Paths

A future authorized script should report these as warnings only:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
AGENTS.md
README.md
README.AGENTS_OS.md
```

Planned warning behavior:

- label these as deferred migration or deferred adoption checks
- do not include them in the failure count
- do not exit non-zero only because these paths are absent
- do not create these files
- do not make root registry or root security files authoritative

## Paths And Patterns Not To Recreate

| Old or risky pattern | Future handling |
| --- | --- |
| Root `SECURITY_BOUNDARIES.md` | Do not require or recreate; canonical authority is `governance/SECURITY_BOUNDARIES.md`. |
| Root `WORKSPACE_REGISTRY.yaml` | Do not require or recreate; planned authority is `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| `AGENTS_OS/README.AGENTS_OS.md` | Do not require or recreate; WSL control-plane is `control-plane/README.md`. |
| Layer `README.AGENTS_OS.md` files | Do not require for current WSL layers; use layer `README.md` files. |
| Deep `state-private/` checks | Do not inspect private contents; check only `state-private/README.md`. |

## Script Content Constraints

A future script patch must:

- be local and path-presence only
- not read or print file contents
- not print secret values
- not inspect private state beyond `state-private/README.md`
- not run remote, branch, push, release, deploy, network, destructive, copy,
  move, or sync actions
- not run Git commands
- not change executable bits
- not self-invoke or invoke other validation scripts
- be non-executable by default after creation

## Strict Preflight Before Implementation

| Check | Pass condition |
| --- | --- |
| Reconfirm source validator hash | Source `validate-workspace.sh` still matches `e3fa994fa659180fae3d9e21d87d3983ca881382b989348d63fe9b6c147a9271`. |
| Reconfirm rewrite plan hash | Rewrite plan still matches `e7a4f9d2f93e63fb8c47a574569d7287bd05f8f4b87573ab789b86a09ec94836`. |
| Reconfirm target script absence | `ops/validation/validate-workspace.sh` is still absent. |
| Reconfirm receipt absence | Batch 9 receipt is still absent. |
| Reconfirm maintenance helper absence | `ops/maintenance/sync-upstream-vcp.sh` remains absent and outside scope. |
| Reconfirm current required paths | All current required paths listed in this plan exist before script creation. |
| Reconfirm deferred paths | Deferred paths remain absent unless separate receipts prove they were migrated or adopted. |
| Live-secret scan | Future script draft and receipt contain no live secrets. |
| Command-risk scan | Future script draft contains no Git, remote, branch, network, destructive, copy, move, sync, or self-invocation commands. |

## Post-Patch Validation Plan

If later authorized and applied, validate by:

| Validation | Method | Notes |
| --- | --- | --- |
| Target file check | Confirm the target script and receipt exist. | No other files should be created. |
| File mode check | Confirm the script is mode `644` or equivalent non-executable text. | Do not run chmod. |
| Content check | Confirm current paths are failures and deferred paths are warnings. | Review the script text only. |
| Syntax-only parse | Parse the shell script without executing it. | Syntax parse is not script execution. |
| Live-secret scan | Scan target script and receipt. | No live secrets. |
| Command-risk scan | Search target script for Git, remote, branch, network, destructive, copy, move, sync, and self-invocation commands. | None should appear. |
| Script execution | Not run in this patch. | Any later run needs exact explicit approval through the validation authorization template. |

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md
```

The receipt should record:

- exact authorization wording
- source validator hash
- rewrite plan hash
- target script created
- receipt created
- current required paths
- deferred warning paths
- syntax-only parse result
- file mode result
- live-secret scan result
- command-risk scan result
- validation not run
- remaining risks
- rollback path

## Rollback Outline

If the future Batch 9 script patch is later applied and must be rolled back,
remove only files created by that future patch after confirming no later user
work depends on them:

```text
ops/validation/validate-workspace.sh
ops/migration/receipts/rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md
```

Do not remove `ops/validation/`, existing Batch 6 validators, Batch 8
authorization templates, migration plans, prior receipts, or any source files
under `A:\AGENTS_OS_Workspace`.

## Open Items Before Authorization

None for the failure/warning behavior. The rule is closed:

```text
Current checks are failures; deferred checks are warnings.
```

Remaining preflight must still pass before any future script creation.

## Related Documents

- `phase-2-batch-9-candidate-selection-2026-06-28.md`
- `phase-2-batch-9-workspace-validator-rewrite-plan-2026-06-28.md`
- `phase-2-batch-8-validation-execution-authorization-template-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-8-validation-execution-authorization-template-receipt-2026-06-28.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../../../control-plane/templates/validation/validation-execution-authorization.template.md`
