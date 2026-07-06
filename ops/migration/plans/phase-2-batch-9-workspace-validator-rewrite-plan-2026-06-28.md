# Phase 2 Batch 9 Workspace Validator Rewrite Plan - 2026-06-28

Status: rewrite plan only; no script created.

Notice: This document maps the old `validate-workspace.sh` path checks to the
current WSL workspace layout. It is not migration authorization, not
authorization to create or rewrite `ops/validation/validate-workspace.sh`, not
authorization to execute validation scripts, not authorization to change
executable bits, and not authorization for remote, branch, push, release,
deploy, secret, private-state, log, cache, or runtime actions.

## Plan Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 9 |
| Batch name | Workspace validator rewrite planning |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source validator | `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` |
| Source SHA-256 | `e3fa994fa659180fae3d9e21d87d3983ca881382b989348d63fe9b6c147a9271` |
| Source size | 648 bytes |
| Candidate target if later authorized | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-workspace.sh` |
| Script created now | No |
| Script execution performed | No |

## Source Required Paths

The source validator currently requires:

```text
README.AGENTS_OS.md
AGENTS.md
SECURITY_BOUNDARIES.md
WORKSPACE_REGISTRY.yaml
AGENTS_OS/README.AGENTS_OS.md
runtime/README.AGENTS_OS.md
governance/README.AGENTS_OS.md
execution/README.AGENTS_OS.md
extensions/README.AGENTS_OS.md
domains/README.AGENTS_OS.md
state-private/README.AGENTS_OS.md
ops/README.AGENTS_OS.md
```

Those paths reflect the Windows reference layout and must not be copied as-is
into the WSL validator.

## Old Path To WSL Target Mapping

| Old source check | WSL rewrite target | Current WSL state | Rewrite handling |
| --- | --- | --- | --- |
| `README.AGENTS_OS.md` | `_ROOT_POLICY.md`, `_DIRECTORY_PRINCIPLES.md`, `_MIGRATION_MAP.md` | All three root bootstrap docs exist. | Replace the old root README check with current root policy/principles/map checks. |
| `AGENTS.md` | No current WSL filesystem target verified. | Root `AGENTS.md` is absent. | Do not require as a workspace file until a local `AGENTS.md` adoption decision exists. |
| `SECURITY_BOUNDARIES.md` | `governance/SECURITY_BOUNDARIES.md` | Exists. | Use governance authority path; do not recreate a root authority copy. |
| `WORKSPACE_REGISTRY.yaml` | `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Absent; registry migration not completed. | Treat as deferred migration-state check, not a current failure. |
| `AGENTS_OS/README.AGENTS_OS.md` | `control-plane/README.md` | Exists. | Map old control-plane layer to current `control-plane/`. |
| `runtime/README.AGENTS_OS.md` | `runtime/README.md` | Exists. | Rename expectation to current README filename. |
| `governance/README.AGENTS_OS.md` | `governance/README.md` | Exists. | Rename expectation to current README filename. |
| `execution/README.AGENTS_OS.md` | `execution/README.md` | Exists. | Rename expectation to current README filename. |
| `extensions/README.AGENTS_OS.md` | `extensions/README.md` | Exists. | Rename expectation to current README filename. |
| `domains/README.AGENTS_OS.md` | `domains/README.md` | Exists. | Rename expectation to current README filename. |
| `state-private/README.AGENTS_OS.md` | `state-private/README.md` | Exists. | Check only the boundary README; do not inspect private contents. |
| `ops/README.AGENTS_OS.md` | `ops/README.md` | Exists. | Rename expectation to current README filename. |

## WSL-Only Additions For Future Validator

These top-level WSL layers exist but were not in the old validator:

| WSL path | Current WSL state | Future validator handling |
| --- | --- | --- |
| `labs/README.md` | Exists. | Include as current layer index check. |
| `memory/README.md` | Exists. | Include as current layer index check. |
| `archive/README.md` | Exists. | Include as current layer index check. |

The old validator should not be the authority for omitting these WSL-only layers.
The directory principles say each first-level directory must have a README.

## Current Checks Suitable For A Future Validator

If a future script patch is authorized, these checks are suitable as current
local path-presence checks:

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

These are path-existence checks only. They do not authorize reading private
state, logs, cache, runtime output, active local config, or secret-like files.

## Deferred Checks

| Future check | Reason to defer | Required before activating |
| --- | --- | --- |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | The authoritative target has been decided, but the canonical registry file has not been migrated. | Complete a scoped registry migration patch and receipt. |
| Root `AGENTS.md` | No current WSL root file exists. | Separate decision to create/adopt a local project `AGENTS.md`, if wanted. |
| Root `README.md` or `README.AGENTS_OS.md` | Current root uses `_ROOT_POLICY.md`, `_DIRECTORY_PRINCIPLES.md`, and `_MIGRATION_MAP.md` instead. | Separate root-index decision if a root README is wanted. |
| Deep private-state checks under `state-private/` | Private state is denied by default. | Separate explicit approval and a redaction policy. |
| Runtime repository internals | Runtime migration and git-output policy are separate topics. | Runtime migration and validator policy decision. |

## Checks That Must Not Be Recreated

| Old pattern | Reason |
| --- | --- |
| Root `SECURITY_BOUNDARIES.md` as authority | The authority is `governance/SECURITY_BOUNDARIES.md`; a root copy would create drift risk. |
| Root `WORKSPACE_REGISTRY.yaml` as authority | The planned authority is `control-plane/registry/WORKSPACE_REGISTRY.yaml`; a root copy would create drift risk. |
| `AGENTS_OS/README.AGENTS_OS.md` | The current WSL control-plane layer is `control-plane/`. |
| Any full `README.AGENTS_OS.md` requirement for current WSL layers | Current WSL layer indexes use `README.md`. |

## Future Script Patch Boundaries

A later script patch, if separately authorized, should:

- create only `ops/validation/validate-workspace.sh`
- keep the script non-executable by default
- perform path-existence checks only
- print missing path names only, not file contents
- not inspect `state-private/` beyond `state-private/README.md`
- not run remote, branch, push, release, deploy, network, destructive, copy,
  move, or sync actions
- not treat deferred registry or local `AGENTS.md` checks as current failures
- produce a receipt if the script file is created

This rewrite plan does not authorize that script patch.

## Preflight Before Any Future Script Patch

| Check | Pass condition |
| --- | --- |
| Source hash check | Source `validate-workspace.sh` still matches `e3fa994fa659180fae3d9e21d87d3983ca881382b989348d63fe9b6c147a9271`. |
| Target absence check | `ops/validation/validate-workspace.sh` is still absent. |
| Maintenance deferral check | `ops/maintenance/sync-upstream-vcp.sh` is still absent and not part of the workspace validator patch. |
| Current path inventory | The current-check list in this plan is rechecked against the WSL root. |
| Deferred path review | Deferred checks are still deferred unless their migration receipts exist. |
| Live-secret scan | Future script draft and receipt contain no live secrets. |
| Command-risk scan | Future script draft contains no remote, branch, network, destructive, copy, move, or sync commands. |
| Execution boundary check | Future patch does not run the script; any later run needs exact explicit approval through the validation authorization template. |

## Related Documents

- `phase-2-batch-9-candidate-selection-2026-06-28.md`
- `phase-2-batch-8-validation-execution-authorization-template-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-8-validation-execution-authorization-template-receipt-2026-06-28.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../decisions/target-layer-reconciliation-2026-06-27.md`
- `../../../_ROOT_POLICY.md`
- `../../../_DIRECTORY_PRINCIPLES.md`
- `../../../_MIGRATION_MAP.md`
