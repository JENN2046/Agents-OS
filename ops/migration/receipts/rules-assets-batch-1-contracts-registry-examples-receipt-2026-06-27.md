# Batch 1 Receipt: Contracts And Registry Examples

Status: completed local documentation patch.

Notice: This receipt records an authorized Batch 1 local patch. It is not a
general migration authorization, not an active registry authorization, and not
authorization to normalize extension paths.

## Authorization Wording

User requested:

```text
做 Batch 1 补丁的最后一道只读检查：secret-like 名称扫描 + README 脚本引用审查，然后再创建 5 个目标文件。
```

User then requested:

```text
补一份 Batch 1 receipt，记录本次创建的 5 个文件、验证结果和未验证项。
```

## Source Files Read

| Source file | Use |
| --- | --- |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\jenn-extension.manifest.schema.json` | Source for target extension manifest schema. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\contracts\README.AGENTS_OS.md` | Source for target contracts README rewrite. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\README.AGENTS_OS.md` | Source for target registry README rewrite. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\extensions.example.yaml` | Source for target example extension registry file. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\registry\protected-paths.example.yaml` | Source for target example protected-path file. |
| `ops/migration/plans/phase-2-batch-1-contracts-registry-examples-patch-plan-2026-06-27.md` | Batch 1 scope and receipt requirements. |

## Target Directories Created

| Target directory | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/` | Target-native registry guidance directory. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/` | Keeps example registry files below, but separate from, future authoritative registry files. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/` | Stores local migration patch receipts. |

## Target Files Created

| Target file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/jenn-extension.manifest.schema.json` | Copied schema content after JSON parse. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/README.md` | Rewritten as target-native README; old validator commands downgraded to future validation references. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/README.md` | Rewritten as target-native README; example files separated from active registry authority. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/extensions.example.yaml` | Source values preserved; comments added to mark historical/unverified paths. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/protected-paths.example.yaml` | Source values preserved; comments added to mark example-only, non-active protection status. |

## Receipt File Created

| Receipt file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-1-contracts-registry-examples-receipt-2026-06-27.md` | Receipt for this Batch 1 patch. |

## Files Explicitly Skipped

| Skipped file or family | Reason |
| --- | --- |
| `WORKSPACE_REGISTRY.yaml` | Reserved for a later registry authority batch. |
| `control-plane/registry/WORKSPACE_REGISTRY.yaml` | Not part of Batch 1. |
| `control-plane/registry/extensions.yaml` | Active registry file not authorized by Batch 1. |
| `control-plane/registry/protected-paths.yaml` | Active protected-path registry not authorized by Batch 1. |
| Prompts, runbooks, templates, scripts, private state | Explicitly outside Batch 1 scope. |
| Extension path normalization | Deferred to a later extension-asset migration decision batch. |

## Validation Run

| Check | Result |
| --- | --- |
| Target pre-existence check before patch | All 5 planned target files were absent before creation. |
| Source existence check | All 3 source machine-readable files existed. |
| Source JSON parse | `jenn-extension.manifest.schema.json` parsed successfully. |
| Source YAML parse | `extensions.example.yaml` and `protected-paths.example.yaml` parsed successfully. |
| Secret-like name scan before patch | No real secret values observed; matches were policy text, schema field names, or generic terms. |
| README script reference review | Old `../../ops/scripts/*.sh` command references were identified and downgraded in target README files. |
| Target file list check | Exactly the 5 planned Batch 1 target files were created under `control-plane/contracts` and `control-plane/registry`. |
| Target JSON parse | Target schema parsed successfully with `$id` `jenn.agents-os.extension.v1`. |
| Target YAML parse | Target example YAML files parsed successfully. |
| YAML value comparison | Target YAML data values matched source YAML data values; added comments did not alter values. |
| Active registry absence check | `WORKSPACE_REGISTRY.yaml`, `extensions.yaml`, and `protected-paths.yaml` were not created under `control-plane/registry`. |
| README active command scan | No old `../../ops/scripts/*.sh` runnable command references remained in target README files. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Repository-level `git diff` or `git status` validation | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |
| Source or migrated validator scripts | Batch 1 plan says not to run migrated or source validator scripts in this batch. |
| Extension path existence validation | Extension path normalization and reconciliation are deferred to a later extension-asset migration decision batch. |
| Active registry validation | No active registry file was created in Batch 1. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Example paths may be stale historical Windows-era paths. | Target example files keep source values and mark paths historical/unverified. |
| README validation references are not executable commands yet. | They are written as future validation references only. |
| Workspace root has no Git diff surface. | Validation relied on explicit file existence, parse checks, and content scans. |
| Active registry authority is still unresolved for later batches. | Batch 1 did not create active registry files. |

## Rollback Path

If this Batch 1 patch must be rolled back, remove only the files created by this
receipt after confirming no later user work depends on them:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/jenn-extension.manifest.schema.json
/home/jenn/AGENTS_OS_Workspace/control-plane/contracts/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/registry/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/extensions.example.yaml
/home/jenn/AGENTS_OS_Workspace/control-plane/registry/examples/protected-paths.example.yaml
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-1-contracts-registry-examples-receipt-2026-06-27.md
```

Do not remove directories if they later contain unrelated user work.
