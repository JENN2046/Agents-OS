# Phase 2 Batch 8 Validation Execution Authorization Template Patch Plan - 2026-06-28

Status: patch plan only; no migration performed.

Notice: This document plans the validation execution authorization template
patch. It is not migration authorization, not authorization to create the target
template yet, not authorization to execute source or migrated validation
scripts, not authorization to change executable bits, and not authorization for
remote, branch, push, release, deploy, secret, private-state, log, cache, or
runtime actions.

## Batch Summary

| Item | Value |
| --- | --- |
| Batch | Phase 2 Batch 8 |
| Batch name | Validation execution authorization template |
| Canonical WSL root | `/home/jenn/AGENTS_OS_Workspace` |
| Direct Windows source file | None selected; this is a new local control-plane template based on prior Batch 6/8 decisions. |
| Recommended target family | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/validation/` |
| Included asset type | Reusable template for requesting explicit human approval for one exact scoped validation-script run. |
| Excluded asset types | Script execution, executable-bit changes, maintenance/sync helpers, workspace validator rewrite, runtime/git-adjacent validators, receipts for actual script runs, private state, logs, cache, runtime artifacts |
| Migration performed | No |
| Script execution performed | No |

## Scope Decision: Template Only vs Template Plus Index

Selected Batch 8 patch scope:

```text
Create 1 validation authorization template and update the template-library index.
```

That means an authorized Batch 8 patch should touch exactly these target files:

```text
control-plane/templates/validation/validation-execution-authorization.template.md
control-plane/templates/README.md
```

Reason:

`control-plane/templates/README.md` is the template library index. Creating a
new template without updating the index would leave the authorization template
easy to miss. The current index also still describes env and security templates
as deferred even though those template files now exist, so a narrow index update
will better reflect the current template library without changing any runtime
behavior.

## Rejected Scope

| Rejected option | Decision | Reason |
| --- | --- | --- |
| Create only `validation-execution-authorization.template.md` | Rejected for Batch 8 | Leaves the new template unlisted and preserves stale template-family wording in the index. |
| Update only `control-plane/templates/README.md` | Rejected | Does not close the Batch 6 execution-authorization template gap. |
| Add runnable examples to `ops/validation/README.md` | Rejected | Batch 6 intentionally avoided copy-ready script invocation commands. |
| Place the template under `ops/validation/` | Rejected | `ops/validation/` holds actual validation scripts; the reusable request/approval template belongs in the template library. |
| Create an execution receipt template under `ops/migration/receipts/` | Rejected for this batch | Receipts record completed work. Batch 8 creates a request/approval template, not a completed execution receipt. |

## Source And Decision Evidence

| Evidence file | Observed fact | Batch 8 handling |
| --- | --- | --- |
| `ops/migration/plans/phase-2-batch-8-candidate-selection-2026-06-28.md` | Selects validation execution authorization template and recommends `control-plane/templates/validation/`. | Follow this placement. |
| `ops/migration/plans/phase-2-batch-6-validation-scripts-patch-plan-2026-06-28.md` | Batch 6 forbids script execution, executable-bit changes, and copy-ready invocation wording. | Preserve these boundaries. |
| `ops/migration/receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md` | Batch 6 created validation scripts but did not authorize execution. | Template must require fresh explicit approval for each exact run. |
| `ops/validation/README.md` | Lists required future approval fields: scope, working directory, expected output, full-path reporting, failure handling, and receipt location. | Template must include these fields. |
| `control-plane/templates/README.md` | Defines template-library rules and currently indexes common and extension templates while listing env/security as deferred. | Update as an index only; do not add execution instructions. |

## Current Target State Observed During Planning

| Path | Observed state |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/validation/` | Absent during planning. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/validation/validation-execution-authorization.template.md` | Absent during planning. |
| `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md` | Present; mode `644`; SHA-256 `da4365718cfea8add98ded6e83d1d742b9619595bee55449eed17c1cb7e1a3b7`. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/README.md` | Present; mode `644`; SHA-256 `33442cd137020fc3a0eea31b49297f0184370724944ce8af789ebc0f853c2759`. |

## Planned Directory Changes

| Action | Path | Reason |
| --- | --- | --- |
| Create if still absent | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/validation/` | Target home for reusable validation authorization templates. |

Do not create `ops/validation/templates/`, `ops/maintenance/`, `ops/validation/drafts/`, or any runtime-specific template directory in this batch.

## Planned File Changes

| Action | Target file | Handling |
| --- | --- | --- |
| Create | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/validation/validation-execution-authorization.template.md` | New placeholder-only template for requesting explicit human approval for one exact validation-script run. |
| Update | `/home/jenn/AGENTS_OS_Workspace/control-plane/templates/README.md` | Narrow index update to list the validation template family and align the current template-family list with files already present. |

No source files under `A:\AGENTS_OS_Workspace` are planned to be copied in this batch.

## Required Template Rules

The future template must:

- State that a blank template is not approval.
- State that a filled template is not approval until explicit human approval
  authorizes that exact run.
- Limit any later explicit approval to at most one exact scoped validation run
  per filled instance.
- Require the script path, working directory, scope, expected output, full-path
  disclosure rule, failure handling, receipt location, and stop conditions.
- Default full-path disclosure to no unless explicitly approved.
- Prefer counts or redacted summaries over full path output.
- Prohibit secret value printing and file-content printing.
- Prohibit remote, branch, push, release, deploy, network, destructive, copy,
  move, or sync actions.
- Avoid copy-ready command examples.
- Avoid real secret, token, credential, private endpoint, private account, or
  live environment values.

## Required Index Update Rules

The `control-plane/templates/README.md` update must:

- Register the validation authorization template as a template-library asset.
- State that validation authorization templates are request/approval forms, not
  script execution instructions.
- Preserve the rule that templates contain placeholders or examples only.
- Preserve the rule that templates do not authorize permissions, deployments,
  releases, pushes, registry changes, or script execution by themselves.
- Align the current template-family list with observed files under
  `control-plane/templates/`.
- Keep the edit narrow; do not rewrite unrelated owner, review, or template
  policy sections.

## Explicitly Skipped Files And Actions

| Skipped item | Reason |
| --- | --- |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/README.md` | It already records the execution boundary; Batch 8 should not add runnable commands there. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-no-secrets.sh` | Existing script; not modified, executed, or made executable. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-extension-manifests.sh` | Existing script; not modified, executed, or made executable. |
| `/home/jenn/AGENTS_OS_Workspace/ops/maintenance/sync-upstream-vcp.sh` | Maintenance/sync helper remains deferred. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-workspace.sh` | Workspace validator still requires separate rewrite planning. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/validate-vcp-runtime.sh` | Runtime/git-adjacent validator remains deferred. |
| `/home/jenn/AGENTS_OS_Workspace/ops/validation/drafts/` | Draft validators are outside this batch. |
| Any script execution receipt | No validation script is planned to run in this batch. |

## Strict Preflight Checks Before Implementation

| Check | Method | Pass condition |
| --- | --- | --- |
| Reconfirm target template absence | Check `control-plane/templates/validation/validation-execution-authorization.template.md`. | Target template is still absent before patch. |
| Reconfirm target directory state | Check `control-plane/templates/validation/`. | Directory is absent or empty before patch. |
| Reconfirm index state | Read `control-plane/templates/README.md` and record hash. | No unexpected conflicting local index content. |
| Reconfirm validation boundary | Read `ops/validation/README.md`. | Required authorization fields and no-execution boundary are still present. |
| Reconfirm skipped scripts are untouched | Check modes and existence for Batch 6 validation scripts. | Scripts remain present and not executable by default. |
| Live-secret pattern scan | Scan target draft template and updated index draft. | No live secret, token, credential, password, private endpoint, or private account value. |
| Authority-risk wording scan | Scan target draft template and updated index draft. | No wording can be read as standing permission to run scripts. |
| Command-risk scan | Search target draft template and updated index draft. | No copy-ready script invocation, remote, branch, release, deploy, network, destructive, copy, move, or sync commands. |

## Post-Patch Validation Plan

| Validation | Method | Notes |
| --- | --- | --- |
| Target file existence check | Confirm the planned template exists and no extra files were created. | Only the planned template file should be created under `control-plane/templates/validation/`. |
| Index update check | Confirm `control-plane/templates/README.md` lists validation templates and does not imply execution authorization. | Index update only. |
| Skipped target absence check | Confirm maintenance, workspace, runtime, draft, and execution-receipt targets remain absent. | Deferred script families stay deferred. |
| Live-secret pattern scan | Scan the new template, updated index, and receipt. | No live-secret patterns should be present. |
| Authority-risk wording check | Inspect for standing-approval language. | Blank template and filled template must still require explicit approval. |
| Command-risk scan | Search for copy-ready script invocation and remote/destructive commands. | None should appear. |
| Executable-bit check | Inspect validation scripts and new template mode. | No script is made executable; template should be ordinary `644` text if created by normal patching. |
| Diff or content review | Inspect created/updated files directly. | Repository-level diff may be unavailable because the workspace root is not a Git repository. |

Do not run source or migrated validation scripts as functional tests in this batch.

## Planned Receipt

If this patch is later authorized and applied, create:

```text
ops/migration/receipts/rules-assets-batch-8-validation-execution-authorization-template-receipt-2026-06-28.md
```

The receipt should record:

- Exact authorization wording.
- Files created.
- Files updated.
- Index update scope.
- Template non-authorization wording checks.
- Live-secret scan result.
- Command-risk scan result.
- Validation run.
- Validation not run.
- Remaining risks.
- Rollback path.

## Rollback Outline

If the Batch 8 patch is later applied and must be rolled back, remove only the
template created by Batch 8 and revert only the Batch 8 index lines after
confirming no later user work depends on them:

```text
control-plane/templates/validation/validation-execution-authorization.template.md
control-plane/templates/README.md
ops/migration/receipts/rules-assets-batch-8-validation-execution-authorization-template-receipt-2026-06-28.md
```

Do not remove `control-plane/templates/`, existing env/security/common/extension
templates, `ops/validation/`, validation scripts, prior migration documents, or
any source files under `A:\AGENTS_OS_Workspace`.

## Open Items Before Authorization

None. The scope question is closed for Batch 8:

```text
Create 1 template file and update the template-library index.
```

## Related Documents

- `phase-2-batch-8-candidate-selection-2026-06-28.md`
- `phase-2-batch-6-validation-scripts-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/templates-targets-2026-06-27.md`
- `../../../ops/validation/README.md`
- `../../../control-plane/templates/README.md`
