# Phase 2 Batch 8 Candidate Selection - 2026-06-28

Status: candidate selection only; no migration performed.

Notice: This document selects the next Phase 2 batch candidate after Batch 7.
It is not migration authorization, not authorization to execute validation
scripts, not authorization to change executable bits, not authorization to create
remote workflows, and not authorization for branch, push, release, deploy,
secret, private-state, log, cache, or runtime actions.

## Candidate Question

Choose the safer next Batch 8 direction after prompt catalogs:

1. Validation execution authorization template.
2. Maintenance/sync helper planning.
3. Workspace validator rewrite planning.
4. Runtime/git-adjacent validator policy.

## Current Context

| Item | Current state |
| --- | --- |
| Batch 6 validation scripts | Completed and three-way reviewed. |
| Batch 6 execution posture | Scripts are placed under `ops/validation/`, not executable by default, and not authorized for execution. |
| Batch 7 prompt catalogs | Completed and three-way reviewed. |
| Existing execution boundary | `ops/validation/README.md` says invocation requires separate explicit validation approval. |
| Existing required approval fields | Scope, working directory, expected output, full-path reporting, failure handling, and receipt location. |
| Direct Windows source artifact | No direct Windows source file selected for this template. |
| Current repository state | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Candidate A - Validation Execution Authorization Template

| Item | Value |
| --- | --- |
| Candidate name | Validation execution authorization template |
| Recommended target family | `control-plane/templates/validation/` |
| Recommended target file | `control-plane/templates/validation/validation-execution-authorization.template.md` |
| Purpose | Reusable request/approval template for a specific, scoped validation-script run. |
| Source basis | Batch 6 plan, Batch 6 receipt, `ops/validation/README.md`, and existing template-library rules. |
| Handling limit | New local control-plane template, not a migrated Windows source file and not standing execution permission. |
| Risk | Low as a template; medium if misunderstood as permission to run scripts. |

### Placement Rationale

| Option | Decision | Reason |
| --- | --- | --- |
| `control-plane/templates/validation/` | Selected | The asset is a reusable template. Keeping it in the template library makes clear that a blank template is not an operational run instruction. |
| `ops/validation/` | Not selected for the template source | This directory holds actual validation scripts and their README. Placing the template beside scripts could blur "request/approval form" with "run instructions." |
| `ops/maintenance/` | Rejected | The target is not a maintenance or sync helper. |
| `governance/` | Rejected for this batch | The template supports a future approval packet, but it is not itself a canonical governance authority or security boundary. |

### Required Template Content

The future template should require a filled instance to state:

| Required field | Purpose |
| --- | --- |
| Validation purpose | Why the run is needed. |
| Script path | The exact migrated script planned for execution. |
| Working directory | The exact directory from which the script would run. |
| Scope | Files, directories, or asset family being checked. |
| Expected output | Whether the expected report is counts, redacted summary, or full paths. |
| Full-path disclosure | Whether full paths may be shown in chat, receipts, or docs. |
| Failure handling | Whether failures stop the calling task. |
| Receipt location | Where the execution receipt would be written if the run is approved. |
| Stop conditions | Conditions that cancel execution before or during the run. |

The blank template must say that only a filled instance with explicit human
approval for that exact run can authorize execution.

## Candidate B - Maintenance/Sync Helper Planning

| Item | Value |
| --- | --- |
| Candidate name | Maintenance/sync helper planning |
| Possible target family | `ops/maintenance/` |
| Related source | `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` |
| Reason to defer | The helper is remote/branch-sensitive and contains fetch, pull, branch, checkout, and merge procedure text. |
| Risk | High unless handled as restricted reference or a separate approval packet. |

## Candidate C - Workspace Validator Rewrite Planning

| Item | Value |
| --- | --- |
| Candidate name | Workspace validator rewrite planning |
| Possible target family | `ops/validation/validate-workspace.sh` or draft documentation first |
| Related source | `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` |
| Reason to defer | The source checks old `AGENTS_OS/` and root registry/security paths that conflict with current WSL target decisions. |
| Risk | Medium; rewrite could accidentally encode the wrong authority paths. |

## Candidate D - Runtime/Git-Adjacent Validator Policy

| Item | Value |
| --- | --- |
| Candidate name | Runtime/git-adjacent validator policy |
| Possible target family | Future runtime-specific validation policy or draft validator |
| Related source | `A:\AGENTS_OS_Workspace\ops\scripts\validate-vcp-runtime.sh` |
| Reason to defer | Runtime migration and git-output policy are not settled. |
| Risk | Medium-high because it is runtime-adjacent and reads nested Git state. |

## Comparison

| Criterion | Execution authorization template | Maintenance/sync planning | Workspace validator rewrite | Runtime/git policy |
| --- | --- | --- | --- | --- |
| Directly closes Batch 6 open boundary | Yes | No | Partly | Partly |
| Local and reversible | Yes | Yes as planning only | Yes as planning only | Yes as planning only |
| Requires script execution | No | No | No | No |
| Requires remote action | No | No, but topic is remote-adjacent | No | No |
| Has current target clarity | Yes, if treated as template-library asset | Partial | Partial | No |
| Best immediate next step | Yes | No | No | No |

## Selection

Selected Batch 8 candidate:

```text
Validation execution authorization template
```

Recommended target placement:

```text
control-plane/templates/validation/validation-execution-authorization.template.md
```

Reason:

Batch 6 deliberately placed validation scripts without granting execution
permission. A dedicated authorization template is the smallest local follow-up
that makes future validation runs auditable without running scripts now, changing
file modes, or creating remote side effects.

## Batch 8 Guardrails

- Do not execute source or migrated validation scripts.
- Do not make scripts executable.
- Do not include copy-ready script invocation examples in the candidate
  selection or future template.
- Do not treat a blank template as approval.
- Do not allow a filled template to authorize more than one exact scoped run.
- Do not authorize full path disclosure by default; require an explicit choice.
- Do not print secret values or file contents.
- Do not run remote, branch, push, release, deploy, network, destructive, copy,
  move, or sync actions.
- Do not create maintenance/sync helpers, workspace validators, runtime
  validators, draft validators, or receipts in this candidate-selection step.

## Suggested Batch 8 Patch Plan Scope

Recommended next plan file:

```text
ops/migration/plans/phase-2-batch-8-validation-execution-authorization-template-patch-plan-2026-06-28.md
```

Recommended planned target:

```text
control-plane/templates/validation/validation-execution-authorization.template.md
```

The next patch plan should decide whether to update the template-library index
in the same batch or keep Batch 8 to a single template file plus receipt.

## Preflight Needed Before Patch Plan

| Check | Reason |
| --- | --- |
| Reconfirm recommended target file is absent. | Avoid overwriting user-owned work. |
| Reconfirm `control-plane/templates/validation/` is absent or empty. | Avoid mixing with unreviewed local files. |
| Re-read `ops/validation/README.md`. | Template fields must match the current execution boundary. |
| Re-read Batch 6 plan and receipt. | Preserve the no-execution, no-chmod, path-output, and receipt rules. |
| Re-read `control-plane/templates/README.md`. | Template placement must follow the placeholder-only template-library rules. |
| Live-secret pattern scan on the future draft. | Ensure no secret-like examples enter the template. |
| Authority-risk wording scan on the future draft. | Ensure the template cannot be read as standing execution permission. |
| Remote/destructive command scan on the future draft. | Ensure it contains no real run commands or remote workflow steps. |

## Related Documents

- `../plans/phase-2-batch-6-validation-scripts-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md`
- `../plans/phase-2-batch-7-candidate-selection-2026-06-28.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/templates-targets-2026-06-27.md`
- `../../validation/README.md`
- `../../../control-plane/templates/README.md`
