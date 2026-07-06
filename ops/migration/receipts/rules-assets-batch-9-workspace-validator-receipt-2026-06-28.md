# Batch 9 Receipt: Workspace Validator

Status: completed local workspace-validator script patch.

Execution date: 2026-06-28.

Notice: This receipt records an authorized Batch 9 local validation-script file
placement patch. It is not a general migration authorization, not authorization
to execute source or migrated validation scripts, not authorization to change
executable bits, not authorization to create maintenance/sync helpers, and not
authorization for remote, branch, push, release, deploy, secret, private-state,
log, cache, or runtime actions.

## Authorization Wording

User requested:

```text
授权执行 Batch 9 补丁：创建 ops/validation/validate-workspace.sh，保持非 executable，并补 Batch 9 receipt。
```

## Plan Followed

| Plan file | SHA-256 | Handling |
| --- | --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/plans/phase-2-batch-9-workspace-validator-patch-plan-2026-06-28.md` | `097fb5a9b41dfaac953bca99915526bfc1a710d7d601b1676dbd6243bf95498f` | Followed the closed behavior rule: current checks are failures; deferred checks are warnings. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/plans/phase-2-batch-9-workspace-validator-rewrite-plan-2026-06-28.md` | `e7a4f9d2f93e63fb8c47a574569d7287bd05f8f4b87573ab789b86a09ec94836` | Used as the old-path to WSL-target mapping. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/plans/phase-2-batch-9-candidate-selection-2026-06-28.md` | `6968c67eb7cb0d939897bc5f6b66d8d15d111dcbee0ee5ae8cfb00bb1f796a98` | Used as the Batch 9 candidate-selection basis. |

## Source Validator

| Source file | SHA-256 | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` | `e3fa994fa659180fae3d9e21d87d3983ca881382b989348d63fe9b6c147a9271` | Rewritten for the current WSL path layout; source script was not executed. |

## Pre-Patch Checks

| Check | Result |
| --- | --- |
| Target script absence | `ops/validation/validate-workspace.sh` was absent before creation. |
| Receipt absence | This receipt file was absent before creation. |
| Maintenance helper absence | `ops/maintenance/sync-upstream-vcp.sh` was absent and outside scope. |
| Source hash check | Source validator hash matched the Batch 9 patch plan. |
| Rewrite plan hash check | Rewrite plan hash matched the Batch 9 patch plan. |
| Current required paths | All 15 current required paths existed before script creation. |
| Workspace Git state | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Target Files Created

| Target file | SHA-256 | Handling |
| --- | --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-workspace.sh` | `daab2f5ebdcb89d52c39f2c4162edf17079ea607d64ddceba6d7155366c3c87f` | Created as non-executable-by-default path-existence validator. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md` | Receipt file; hash verified during closeout scan. | Created as receipt for this local patch. |

## Current Required Paths

The target script treats these as failure-producing required paths:

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

## Deferred Warning Paths

The target script treats these as warning-only deferred paths:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
AGENTS.md
README.md
README.AGENTS_OS.md
```

These paths are not counted as failures by the target script.

## Validation Run

| Check | Result |
| --- | --- |
| Target file existence check | Target script exists at `ops/validation/validate-workspace.sh`. |
| File mode check | Target script is mode `644`; executable bit was not set. |
| Behavior text check | Script contains current required paths and deferred warning paths; current missing paths drive exit `1`, deferred missing paths are warnings. |
| Private-state boundary check | Script references only `state-private/README.md` and does not inspect deeper private paths. |
| Syntax-only parse | `bash -n ops/validation/validate-workspace.sh` passed. This parsed syntax only and did not execute script logic. |
| Live-secret pattern scan | No live-secret patterns were found in the target script before receipt creation; final closeout scan includes this receipt. |
| Command-risk scan | No Git, remote, branch, network, destructive, copy, move, sync, source, self-invocation, or executable-bit commands were found in the target script. |
| Repository-level check | Git diff/status was not available because `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Source validator execution | Batch 9 does not authorize source script execution. |
| Migrated validator execution | Batch 9 does not authorize running `ops/validation/validate-workspace.sh`. |
| Other validation scripts | Outside Batch 9 scope and require separate exact-run approval. |
| Maintenance/sync helper validation | Maintenance/sync helpers remain deferred. |
| Remote, branch, push, release, or deploy checks | Outside Batch 9 scope and not authorized. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Deferred warning paths could be mistaken as failures. | Patch plan, script labels, and this receipt state that deferred paths are warnings only. |
| A future user may run the script without exact approval. | Batch 8 authorization template remains the required path for any future script execution. |
| Path-only output can reveal workspace structure. | Script prints path names only; future execution still requires scoped approval. |
| Workspace root has no Git diff surface. | Validation relied on file existence checks, hashes, syntax-only parsing, mode checks, direct content checks, and pattern scans. |

## Rollback Path

If this Batch 9 patch must be rolled back, remove only the files created by this
batch after confirming no later user work depends on them:

```text
/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-workspace.sh
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md
```

Do not remove `ops/validation/`, existing Batch 6 validators, Batch 8
authorization templates, migration plans, prior receipts, or any source files
under `A:\AGENTS_OS_Workspace`.
