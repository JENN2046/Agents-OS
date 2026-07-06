# Batch 2 Receipt: Ordinary Templates

Status: completed local documentation/template patch.

Notice: This receipt records an authorized Batch 2 local patch. It is not a
general migration authorization, not authorization for env templates, not
authorization for security templates, not authorization for runbooks, and not
authorization to create active config or registry files.

## Authorization Wording

User requested:

```text
授权执行 Batch 2 补丁：创建 3 个 ordinary templates 目标文件，并在完成后补 Batch 2 receipt。
```

## Source Files Read

| Source file | Use |
| --- | --- |
| `A:\AGENTS_OS_Workspace\templates\README.AGENTS_OS.md` | Source for target template-library README rewrite. |
| `A:\AGENTS_OS_Workspace\templates\README.template.md` | Source for target common README template. |
| `A:\AGENTS_OS_Workspace\templates\jenn-extension.manifest.example.json` | Source for target extension manifest example template. |
| `control-plane/contracts/jenn-extension.manifest.schema.json` | Required-field reference from Batch 1. |
| `ops/migration/plans/phase-2-batch-2-ordinary-templates-patch-plan-2026-06-27.md` | Batch 2 scope, checks, and receipt requirements. |

## Target Directories Created

| Target directory | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/` | Target-native ordinary template library. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/` | Holds generic reusable templates. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/` | Holds extension manifest/example templates. |

## Target Files Created

| Target file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md` | Rewritten as target-native ordinary-template library README. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/README.template.md` | Adapted from source; old `AGENTS_OS` layer wording replaced with current WSL layout wording. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/jenn-extension.manifest.example.json` | Source JSON values preserved after parse and required-field check. |

## Receipt File Created

| Receipt file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-2-ordinary-templates-receipt-2026-06-27.md` | Receipt for this Batch 2 patch. |

## Files Explicitly Skipped

| Skipped file or family | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\templates\config.env.example.template` | Deferred to a later env-template batch after placeholder-only review. |
| `control-plane/templates/env/config.env.example.template` | Not part of ordinary templates Batch 2. |
| `A:\AGENTS_OS_Workspace\templates\SECURITY.template.md` | Deferred until aligned with `governance/SECURITY_BOUNDARIES.md`. |
| `control-plane/templates/security/SECURITY.template.md` | Not part of ordinary templates Batch 2. |
| `A:\AGENTS_OS_Workspace\AGENTS_OS\runbooks/*` | Runbooks require a separate stale-path and authorization wording review. |
| Validator scripts | Scripts are outside this batch and were not run. |
| Active config, active registry, extension packages, private state | Outside ordinary template scope. |

## Validation Run

| Check | Result |
| --- | --- |
| Target pre-existence check before patch | All 3 planned target files were absent before creation. |
| Source existence check | All 3 selected source files existed and sizes were recorded. |
| Source manifest JSON parse | `jenn-extension.manifest.example.json` parsed successfully. |
| Required-field check | All 7 Batch 1 schema required fields were present: `schemaVersion`, `id`, `name`, `type`, `entrypoints`, `permissions`, `secretPolicy`. |
| Source live-secret pattern scan | No live-secret patterns were found. |
| Target file list check | Exactly the 3 planned template files exist under `control-plane/templates`. |
| Target manifest JSON parse | Target manifest example parsed successfully. |
| Target required-field check | All 7 required fields remained present. |
| Manifest value comparison | Target manifest JSON data matched source manifest JSON data. |
| Excluded target absence check | Env template, security template, and runbook targets were not created. |
| Old layer wording check | `AGENTS_OS` wording was absent from target ordinary template files. |
| README active command scan | No old validator-script or bash command references were present in target README/template files. |
| Target live-secret pattern scan | No live-secret patterns were found. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Full JSON Schema validation | Batch 2 required a JSON parse and required-field check; full schema validation was not required for this patch. |
| Source or migrated validator scripts | Batch 2 plan says not to run validator scripts in this batch. |
| Env template validation | Env templates were excluded from Batch 2. |
| Security template validation | Security templates were excluded from Batch 2. |
| Runbook validation | Runbooks were excluded from Batch 2. |
| Repository-level `git diff` or `git status` validation | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Manifest example is only checked for parse and required fields, not full schema semantics. | Keep it example-only and validate more deeply before adoption by an extension package. |
| Template README wording may need future tuning as the workspace taxonomy evolves. | Target wording avoids old `AGENTS_OS` layer language and uses current top-level WSL layout labels. |
| Env and security template work remains undone. | Both families are explicitly deferred to later dedicated batches. |
| Workspace root has no Git diff surface. | Validation relied on file existence, parse checks, direct content scans, and explicit excluded-target checks. |

## Rollback Path

If this Batch 2 patch must be rolled back, remove only the files created by
this receipt after confirming no later user work depends on them:

```text
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/common/README.template.md
/home/jenn/AGENTS_OS_Workspace/control-plane/templates/extensions/jenn-extension.manifest.example.json
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-2-ordinary-templates-receipt-2026-06-27.md
```

Do not remove directories if they later contain unrelated user work.
