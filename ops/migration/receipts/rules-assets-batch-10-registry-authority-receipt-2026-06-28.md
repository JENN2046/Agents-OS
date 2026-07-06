# Batch 10 Receipt: Registry Authority

Status: completed local registry authority patch.

Execution date: 2026-06-28.

Notice: This receipt records an authorized Batch 10 local registry file creation.
It is not a general migration authorization, not authorization to create root
registry copies, not authorization to create maintenance/sync helpers, not
authorization to execute validation scripts, not authorization to change
executable bits, and not authorization for remote, branch, push, release,
deploy, secret, private-state, log, cache, or runtime actions.

## Authorization Wording

User requested:

```text
执行 Batch 10 补丁：创建 control-plane/registry/WORKSPACE_REGISTRY.yaml，按计划规范化，并补 Batch 10 receipt。
```

## Plan Followed

| Plan file | SHA-256 | Handling |
| --- | --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/plans/phase-2-batch-10-registry-authority-patch-plan-2026-06-28.md` | `d3bca3ec6d1b0a62034fcf1800113ca09687a4f93675754c84db90918f5e1e51` | Followed the closed scope: create exactly one authority registry file under `control-plane/registry/`. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/plans/phase-2-batch-10-candidate-selection-2026-06-28.md` | `34171fcab3a7aba33b4d30aebf12d1feef2c52e9d242c3a7bd8d967aca6788ae` | Used as the Batch 10 candidate-selection basis. |

## Source Registry

| Source file | SHA-256 | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml` | `4abadb46ce14df8116d1e2205ccda9c66bd61ca84b781a80d1f18e3456c5fc40` | Parsed as source YAML and normalized for current WSL layout. |

## Pre-Patch Checks

| Check | Result |
| --- | --- |
| Target registry absence | `control-plane/registry/WORKSPACE_REGISTRY.yaml` was absent before creation. |
| Root registry absence | Root `WORKSPACE_REGISTRY.yaml` was absent before creation and remains outside scope. |
| Receipt absence | This receipt file was absent before creation. |
| Maintenance/sync absence | `ops/maintenance/sync-upstream-vcp.sh` was absent and outside scope. |
| Source hash check | Source registry hash matched the Batch 10 patch plan. |
| Source YAML parse | Source registry parsed with `workspace`, `layers`, `repositories`, and `security`; 8 layers; 6 repositories. |
| Workspace Git state | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Target Files Created

| Target file | SHA-256 | Handling |
| --- | --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/WORKSPACE_REGISTRY.yaml` | `874d5098eb068de0933b9451844bb2ae412d66d9f7673d6d41a9cb9cfacb745d` | Created as normalized authority registry. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md` | Receipt file; hash verified during closeout scan. | Created as receipt for this local patch. |

## Normalization Applied

| Source or issue | Target handling |
| --- | --- |
| Old layer id `agents_os` | Replaced with `control_plane`. |
| Old layer path for the control plane | Replaced with `control-plane/`. |
| WSL-only layer `labs/` | Added after confirming `labs/README.md` exists. |
| WSL-only layer `memory/` | Added after confirming `memory/README.md` exists. |
| WSL-only layer `archive/` | Added after confirming `archive/README.md` exists. |
| `agent-image-lab` source layer `domains` | Normalized to `labs` based on `_MIGRATION_MAP.md` and current WSL layout. |
| Repository URLs | Preserved as metadata only. |
| Security `default_forbidden` entries | Preserved as registry policy metadata. |
| Missing repository records | Not added in this batch. |

## Validation Run

| Check | Result |
| --- | --- |
| Target file existence check | Target registry exists at `control-plane/registry/WORKSPACE_REGISTRY.yaml`. |
| File mode check | Target registry is mode `644`. |
| Target YAML parse | Target registry parsed as YAML with `workspace`, `layers`, `repositories`, and `security`. |
| Target structure check | Target registry has 11 layers and 6 repositories. |
| Control-plane normalization check | Target registry has layer id `control_plane` and path `control-plane/`; it does not have layer id `agents_os` or active layer path from the old layout. |
| WSL-only layer check | `labs`, `memory`, and `archive` layer entries are present. |
| Repository normalization check | `agent-image-lab` is under `labs`; repository count remains 6. |
| Remote boundary check | Repository URLs have `url_role: metadata_only`; workspace remote action authorization is false. |
| Security metadata check | Registry authorization flags for remote actions, validation execution, executable-bit changes, and permission expansion are false. |
| Root absence check | Root `WORKSPACE_REGISTRY.yaml` remains absent. |
| Maintenance/sync absence check | `ops/maintenance/sync-upstream-vcp.sh` remains absent. |
| Live-secret pattern scan | No live-secret patterns were found in the target registry before receipt creation; final closeout scan includes this receipt. |
| Command-risk scan | No runnable remote, branch, network, destructive, sync, or validation-script commands were found in the target registry. |
| Repository-level check | Git diff/status was not available because `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Source or migrated validation scripts | Batch 10 does not authorize validation execution. |
| Maintenance/sync helper validation | Maintenance/sync helpers remain deferred. |
| Remote, branch, push, release, or deploy checks | Outside Batch 10 scope and not authorized. |
| Registry consumer integration | This batch creates registry data only; consumer behavior remains separate. |

## Files Not Created

| Path | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/WORKSPACE_REGISTRY.yaml` | Root registry authority was rejected to avoid drift. |
| `/home/jenn/AGENTS_OS_Workspace/governance/WORKSPACE_REGISTRY.yaml` | Registry authority belongs under `control-plane/registry/`. |
| `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/sync-upstream-vcp.sh` | Maintenance/sync helper remains deferred. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Registry may be mistaken as remote-operation authorization. | Target registry marks URLs as metadata and remote action authorization as false. |
| Missing repository records may be assumed complete. | Receipt states that missing repository records were not added in this batch. |
| Registry consumers may need schema or compatibility checks later. | This batch validates YAML structure only; consumer integration is separate. |
| Workspace root has no Git diff surface. | Validation relied on file existence checks, hashes, YAML parsing, mode checks, direct content checks, and pattern scans. |

## Rollback Path

If this Batch 10 registry patch must be rolled back, remove only the files
created by this batch after confirming no later user work depends on them:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/registry/WORKSPACE_REGISTRY.yaml
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md
```

Do not remove `control-plane/registry/`, registry examples, registry README,
validation scripts, prior migration plans, prior receipts, or any source files
under `A:\AGENTS_OS_Workspace`.
