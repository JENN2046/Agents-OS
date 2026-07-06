# Phase 2 Batch 6 Validation Scripts Patch Plan - 2026-06-28

Status: patch plan only; no migration performed.

Notice: This document plans the validation-scripts patch. It is not migration
authorization, not authorization to copy files yet, not authorization to execute
source or migrated scripts, not authorization to change executable bits, and not
authorization for remote, sync, branch, push, release, or deploy actions.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 6 |
| Batch name | Validation scripts |
| Windows reference root | `A:\AGENTS_OS_Workspace` |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Source directory | `A:\AGENTS_OS_Workspace\ops\scripts` |
| Target directory | `/home/jenn/AGENTS_OS_Workspace/ops/validation/` |
| Included asset type | Reviewed validation README and low-risk validation scripts |
| Excluded asset types | Maintenance/sync helpers, runtime/git-adjacent validators, workspace validators needing rewrite, placeholder validators, prompts, templates, runbooks, private state, logs, cache, runtime artifacts |
| Migration performed | No |
| Script execution performed | No |
| Syntax-only parse performed | Yes, for the two candidate scripts only |

## Candidate Selection

| Candidate | Source file | Planned target | Decision |
| --- | --- | --- | --- |
| Validation README | `A:\AGENTS_OS_Workspace\ops\scripts\README.AGENTS_OS.md` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/README.md` | Include as rewritten target-native validation README. |
| No-secret path scanner | `A:\AGENTS_OS_Workspace\ops\scripts\validate-no-secrets.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-no-secrets.sh` | Include after preserving path-only output and no-content-printing rule. |
| Extension manifest validator | `A:\AGENTS_OS_Workspace\ops\scripts\validate-extension-manifests.sh` | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-extension-manifests.sh` | Include after preserving WSL `./extensions` review scope and no remote actions. |

## Source Evidence

| Source file | Size | SHA-256 | Batch handling |
| --- | ---: | --- | --- |
| `A:\AGENTS_OS_Workspace\ops\scripts\README.AGENTS_OS.md` | 775 bytes | `a921d82bee2f2fb475685eafe0e6617a67e70c02e6f8920778c03f8469930e7d` | Rewrite as `ops/validation/README.md`; do not preserve source validation commands as default execution instructions. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-no-secrets.sh` | 822 bytes | `2f1fa527100bb353a7702994135ec8388142137308306b649de38ead8318fe56` | Candidate active validator; syntax-only parse passed; output must remain path-only. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-extension-manifests.sh` | 1539 bytes | `4fe3d5db2576c1f3cd43c341c1e37b3a65d28d9c1d38cafe7f43b8afbe4822e5` | Candidate active validator; syntax-only parse passed; scans `./extensions` only. |

## Plan-Level Checks Already Performed

| Check | Result |
| --- | --- |
| Source file listing | `A:\AGENTS_OS_Workspace\ops\scripts` contains README, sync helper, two active validation candidates, placeholder validators, runtime validator, and workspace validator. |
| Target absence check | `ops/validation/README.md`, `ops/validation/validate-no-secrets.sh`, and `ops/validation/validate-extension-manifests.sh` were absent during planning. |
| Syntax-only parse | `bash -n` passed for `validate-no-secrets.sh` and `validate-extension-manifests.sh`. This parsed syntax only and did not execute script logic. |
| Live-secret scan | No live-secret patterns found in the source README or the two candidate scripts. |
| Output policy scan | Candidate scripts use `find` but do not use common file-content printing tools such as `cat`, `sed`, `awk`, `head`, `tail`, `less`, or `more`. |
| Remote git command scan | No `git fetch`, `git pull`, `git push`, `git merge`, `git checkout`, `git branch`, or `git remote` commands found in the two candidate scripts. |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Use existing directory | `/home/jenn/AGENTS_OS_Workspace/ops/validation/` | Target home for reviewed validation scripts. |

Do not create `ops/scripts/` as a canonical WSL target in this batch.

## Planned File Changes

| Action | Target file | Source file | Handling |
| --- | --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/ops/validation/README.md` | `A:\AGENTS_OS_Workspace\ops\scripts\README.AGENTS_OS.md` | Rewrite as validation-only README. Remove sync helper from validation list and state that scripts are not run by default. |
| Create | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-no-secrets.sh` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-no-secrets.sh` | Adapt conservatively as a non-executable-by-default path-only scanner. Do not print file contents or secret values. |
| Create | `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-extension-manifests.sh` | `A:\AGENTS_OS_Workspace\ops\scripts\validate-extension-manifests.sh` | Adapt conservatively as a non-executable-by-default extension manifest checker scoped to `./extensions`. |

No existing target file is planned to be modified in this batch.

## Explicitly Skipped Files

| Skipped source or target | Reason |
| --- | --- |
| `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` | Maintenance/sync helper containing printed `git fetch`, `git pull`, branch, checkout, and merge procedure; not validation. |
| `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/sync-upstream-vcp.sh` | Reserved for a later restricted maintenance/helper batch; not created here. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-domain-bridges.sh` | Placeholder validator; should not become active validation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-execution-profiles.sh` | Placeholder/future schema validator; should not become active validation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-policy-packs.sh` | Placeholder/future schema validator; should not become active validation. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-vcp-runtime.sh` | Runtime/git-adjacent validator; waits for runtime migration and git-output policy. |
| `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` | Requires rewrite because it checks old `AGENTS_OS/` and root registry/security paths. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/drafts/` | Draft validators are not created in this active validation batch. |
| Private state, logs, cache, runtime output, active config | Outside validation-script migration scope. |

## Required Rewrites And Alignment

| Topic | Target handling | Reason |
| --- | --- | --- |
| Source README filename | Rewrite `README.AGENTS_OS.md` as `README.md`. | Target directory uses local README naming. |
| Source README script list | List only `validate-no-secrets.sh` and `validate-extension-manifests.sh` as included active validation candidates. | Avoid implying skipped scripts were migrated. |
| Source README validation command | Do not preserve `./validate-no-secrets.sh` as a default run instruction, and do not include copy-ready invocation commands in the target README. | Scripts are not run by default and executable bits are not changed. |
| Execution posture | State that scripts are local, read-only/path-only where applicable, and require an explicit scoped validation action before use. | Prevent migration from becoming execution authorization. |
| Executable bits | Do not run `chmod` and do not rely on executable bits. | Batch 6 is a file-placement patch only. |
| No-secret scanner output | Preserve path-only output; do not print file contents or secret values. | Keeps the validator useful without exposing secrets. |
| No-secret scanner scope | Keep examples/templates excluded and record that path-only output may include sensitive filenames if later run. Do not copy full path output into receipts or public docs without separate approval. | Even path names can be sensitive; execution requires separate approval. |
| Extension manifest validator scope | Preserve workspace-relative `./extensions` scope and placeholder-directory skips. Do not narrow the script to `extensions/vcp-toolbox-jenn/` in this batch. | The observed WSL extension root is not a final extension-assets placement decision. |
| Remote actions | Keep scripts free of fetch, pull, push, merge, checkout, branch movement, release, deploy, or network actions. | Validation scripts must stay local and non-remote. |

## Strict Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm source candidates exist | Check the source README and two candidate scripts. | All three source files exist and hashes match this plan. |
| Reconfirm target files are absent | Check the three planned files under `ops/validation/`. | None of the three target files exists before patch. |
| Reconfirm skipped targets are absent | Check maintenance, draft, runtime, and workspace validator targets. | Skipped targets are not accidentally created by this batch. |
| Syntax-only parse | Run `bash -n` on the two source candidate scripts only. | Syntax parse succeeds without executing script logic. |
| Live-secret pattern scan | Scan source candidates and target drafts. | No real secret, token, credential, password, private endpoint, or private account value is present. |
| Output policy scan | Search target drafts for content-printing commands and secret-value printing. | Target validators print status and paths only; no file contents or secret values. |
| Remote/sync command scan | Search target drafts for remote, branch, merge, release, deploy, network, and destructive commands. | No remote/sync/destructive command appears in active validation scripts. |
| Executable-bit check | Inspect target file modes after creation. | No script is made executable by this batch. |

## Planned Content Rules

- Target files must live under `ops/validation/`.
- Target scripts must be non-executable by default.
- Target scripts must not be executed during migration.
- Target README must not imply validation scripts are safe to run by default.
- Target README must not list sync, runtime, workspace-rewrite, or placeholder
  validators as included active scripts.
- Target no-secret scanner must not print secret values or file contents.
- Target extension manifest validator must not perform remote, branch, release,
  deploy, or network actions.
- Target files must not create or modify active config, private state, logs,
  cache, runtime output, registry authority, runbooks, templates, or prompts.

## Post-Patch Validation Plan

| Validation | Command or method | Notes |
| --- | --- | --- |
| Target file existence check | Confirm the three planned files exist under `ops/validation/`. | No extra validation scripts should be created. |
| Excluded target absence check | Confirm maintenance, draft, runtime, and workspace validator targets remain absent. | Skipped script families remain deferred. |
| Syntax-only parse | Run `bash -n` on the two migrated target scripts. | Syntax-only parse, not script execution. |
| Executable-bit check | Inspect target file modes. | Scripts should not be executable by default. |
| Live-secret pattern scan | Scan target README, target scripts, and receipt. | No live-secret pattern should be present. |
| Output policy check | Inspect target scripts for file-content printing or secret-value output. | `validate-no-secrets.sh` remains path-only. |
| Remote/sync command check | Search target scripts for remote, branch, release, deploy, network, and destructive commands. | Active validation scripts remain local and non-remote. |
| Diff or content review | Inspect created files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run source or migrated scripts as functional tests in this batch.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md
```

The receipt should record:

- Exact authorization wording.
- Source files read.
- Source files skipped.
- Target files created.
- Syntax-only parse result.
- Output policy review.
- Executable-bit status.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If the validation-scripts patch is later applied and must be rolled back,
remove only the files created by that patch after confirming no later user work
depends on them:

```text
ops/validation/README.md
ops/validation/validate-no-secrets.sh
ops/validation/validate-extension-manifests.sh
ops/migration/receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md
```

Do not remove `ops/validation/`, `ops/maintenance/`, existing migration
documents, receipts, reports, or any source files under `A:\AGENTS_OS_Workspace`.

## Closed Wording Rules Before Authorization

| Item | Closed rule |
| --- | --- |
| Invocation wording | Target README must not include copy-ready command examples for running validation scripts. It must say invocation is deferred until a separate explicit validation approval. |
| No-secret scanner path-output sensitivity | Target README and receipt must state that path-only output can still reveal sensitive filenames. Scripts may remain path-only, but future receipts or reports should prefer counts/redacted summaries unless the user separately approves full path disclosure. |
| Extension manifest scope | Target script must preserve workspace-relative `./extensions` scope. It must not narrow to `extensions/vcp-toolbox-jenn/` or treat that observed directory as the final extension-assets target in this batch. |

## Related Documents

- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../plans/phase-1-summary-and-phase-2-entry-criteria-2026-06-27.md`
- `../plans/rules-assets-migration-plan-2026-06-27.md`
- `../decisions/runbooks-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
