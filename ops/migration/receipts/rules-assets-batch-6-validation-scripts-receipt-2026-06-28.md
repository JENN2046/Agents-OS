# Batch 6 Receipt: Validation Scripts

Status: completed local validation-scripts patch.

Execution date: 2026-06-28.

Notice: This receipt records an authorized Batch 6 local validation-script file
placement patch. It is not a general migration authorization, not authorization
to execute source or migrated scripts, not authorization to change executable
bits, not authorization to create maintenance/sync helpers, and not
authorization for remote, branch, push, release, deploy, secret, private-state,
log, cache, or runtime actions.

## Authorization Wording

User requested:

```text
授权执行 Batch 6 补丁：创建 3 个 ops/validation/ 目标文件，并补 Batch 6 receipt。
```

## Source Files Read

| Source file | SHA-256 | Handling |
| --- | --- | --- |
| `A:\AGENTS_OS_Workspace\ops\scripts\README.AGENTS_OS.md` | `a921d82bee2f2fb475685eafe0e6617a67e70c02e6f8920778c03f8469930e7d` | Adapted as target-native validation README. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-no-secrets.sh` | `2f1fa527100bb353a7702994135ec8388142137308306b649de38ead8318fe56` | Adapted as non-executable-by-default path-only scanner. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-extension-manifests.sh` | `4fe3d5db2576c1f3cd43c341c1e37b3a65d28d9c1d38cafe7f43b8afbe4822e5` | Adapted as non-executable-by-default extension manifest checker scoped to `./extensions`. |

All three included source hashes matched the Batch 6 patch plan immediately
before target creation.

## Source Files Skipped

| Skipped source or family | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` | Maintenance/sync helper containing remote and branch-sensitive procedure text. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-domain-bridges.sh` | Placeholder validator; not active validation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-execution-profiles.sh` | Placeholder/future schema validator; not active validation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-policy-packs.sh` | Placeholder/future schema validator; not active validation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-vcp-runtime.sh` | Runtime/git-adjacent validator; waits for runtime migration and git-output policy. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` | Requires rewrite because it checks old `AGENTS_OS/` and root registry/security paths. |

## Target Files Created

| Target file | Handling |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/README.md` | Created as validation-only README with no copy-ready invocation commands. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-no-secrets.sh` | Created as non-executable-by-default path-only suspicious-file scanner. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-extension-manifests.sh` | Created as non-executable-by-default extension manifest checker preserving `./extensions` scope. |
| `/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md` | Created as receipt for this local patch. |

## Targets Explicitly Not Created

| Target | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/sync-upstream-vcp.sh` | Maintenance/sync helper excluded from validation batch. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-workspace.sh` | Requires rewrite before migration. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-vcp-runtime.sh` | Runtime/git-adjacent and deferred. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/drafts/` | Draft validators not created in this active validation batch. |

## Closed Wording Rules Applied

| Rule | Result |
| --- | --- |
| Invocation wording | Target README avoids copy-ready command examples and says invocation requires separate explicit validation approval. |
| Path-output sensitivity | Target README states path-only output can still reveal sensitive filenames and future reports should prefer counts or redacted summaries unless full path disclosure is separately approved. |
| Extension manifest scope | Target script preserves workspace-relative `./extensions` scope and does not narrow to `extensions/vcp-toolbox-jenn/`. |

## Validation Run

| Check | Result |
| --- | --- |
| Pre-existing target check | Three target files and this receipt were absent before creation. |
| Source hash check | Three included source hashes matched the Batch 6 patch plan. |
| Target file list check | `ops/validation/` contains `README.md`, `validate-no-secrets.sh`, and `validate-extension-manifests.sh` from this batch. |
| Skipped target absence check | Maintenance, workspace, runtime, and draft validator targets were not created. |
| Syntax-only parse | `bash -n` passed for both migrated target scripts. This did not execute script logic. |
| Executable-bit check | Target files were `644`; scripts were not made executable by this batch. |
| Live-secret pattern scan | No live-secret patterns were found in the target README or target scripts. |
| Output policy scan | Target scripts did not contain common file-content printing tools such as `cat`, `sed`, `awk`, `head`, `tail`, `less`, `more`, `xxd`, or `base64`. |
| Remote/network/destructive scan | Target scripts did not contain remote git, network, destructive, copy, or move commands. |

## Validation Not Run

| Not run | Reason |
| --- | --- |
| Source script functional execution | Batch 6 plan forbids executing source scripts during migration. |
| Migrated script functional execution | Batch 6 plan forbids executing migrated scripts during migration. |
| Maintenance/sync validation | Maintenance helpers are outside this validation batch. |
| Runtime validator validation | Runtime/git-adjacent validator remains deferred. |
| Workspace validator validation | Workspace validator requires rewrite against WSL target decisions. |
| Repository-level `git diff` or `git status` validation | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Remaining Risks

| Risk | Current mitigation |
| --- | --- |
| Path-only output can still reveal sensitive filenames. | Target README warns about path-output sensitivity and recommends counts/redacted summaries unless full path disclosure is separately approved. |
| Scripts may be mistaken as runnable by default. | Target README and this receipt state that invocation requires separate explicit validation approval; executable bits were not changed. |
| Extension manifest scope may need future narrowing. | Target script preserves `./extensions`; extension-assets placement remains a separate decision. |
| Workspace root has no Git diff surface. | Validation relied on file existence checks, source hashes, syntax-only parsing, mode checks, direct content checks, and pattern scans. |

## Rollback Path

If this Batch 6 validation-scripts patch must be rolled back, remove only the
files created by this receipt after confirming no later user work depends on
them:

```text
/home/jenn/AGENTS_OS_Workspace/ops/validation/README.md
/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-no-secrets.sh
/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-extension-manifests.sh
/home/jenn/AGENTS_OS_Workspace/ops/migration/receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md
```

Do not remove `ops/validation/`, `ops/maintenance/`, existing migration
documents, receipts, reports, or any source files under `A:\AGENTS_OS_Workspace`.
