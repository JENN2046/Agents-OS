# Phase 2 Batch 9 Candidate Selection - 2026-06-28

Status: candidate selection only; no migration performed.

Notice: This document selects the next Phase 2 batch candidate after Batch 8.
It is not migration authorization, not authorization to copy or rewrite scripts,
not authorization to execute validation scripts, not authorization to create
maintenance/sync helpers, not authorization to change executable bits, and not
authorization for remote, branch, push, release, deploy, secret, private-state,
log, cache, or runtime actions.

## Candidate Question

Choose the safer next Batch 9 direction:

1. Workspace validator rewrite planning.
2. Maintenance/sync helper planning.

## Current Context

| Item | Current state |
| --- | --- |
| Batch 6 validation scripts | Completed and three-way reviewed. |
| Batch 8 validation authorization template | Completed and three-way reviewed. |
| Validation script execution | Still not authorized; exact-run authorization template exists but no run has been approved. |
| `validate-workspace.sh` target | Not created under `ops/validation/`. |
| `sync-upstream-vcp.sh` target | Not created under `ops/maintenance/`. |
| Current repository state | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Candidate A - Workspace Validator Rewrite Planning

| Item | Value |
| --- | --- |
| Candidate name | Workspace validator rewrite planning |
| Related source | `A:\AGENTS_OS_Workspace\ops\scripts\validate-workspace.sh` |
| Possible future target | `ops/validation/validate-workspace.sh` |
| Source SHA-256 | `e3fa994fa659180fae3d9e21d87d3983ca881382b989348d63fe9b6c147a9271` |
| Source size | 648 bytes |
| Candidate handling | Plan the required path rewrite before any script creation. |
| Risk | Medium-low if kept planning-only; medium if turned into an active validator too early. |

### Workspace Validator Source Evidence

The source validator checks old root and old layer paths such as:

```text
README.AGENTS_OS.md
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

Observed WSL evidence during selection:

```text
control-plane/README.md
domains/README.md
execution/README.md
extensions/README.md
governance/README.md
governance/SECURITY_BOUNDARIES.md
labs/README.md
memory/README.md
ops/README.md
runtime/README.md
state-private/README.md
```

Decision evidence already says:

- `SECURITY_BOUNDARIES.md` belongs at `governance/SECURITY_BOUNDARIES.md`.
- `WORKSPACE_REGISTRY.yaml` belongs at
  `control-plane/registry/WORKSPACE_REGISTRY.yaml` when migrated.
- Root duplicate copies should not become authoritative.
- Old `AGENTS_OS/` control-plane material is represented by `control-plane/`.

### Workspace Validator Risk Signals

| Signal | Impact | Required handling |
| --- | --- | --- |
| Old `README.AGENTS_OS.md` paths | Current WSL layer indexes use `README.md`. | Rewrite path expectations before any validator creation. |
| Old root `SECURITY_BOUNDARIES.md` | Current authority is `governance/SECURITY_BOUNDARIES.md`. | Use governance target decision; do not recreate root authority. |
| Old root `WORKSPACE_REGISTRY.yaml` | Registry authority is planned under `control-plane/registry/`. | Treat missing registry as migration-state evidence, not automatic failure, until registry migration exists. |
| Old `AGENTS_OS/` layer | Current WSL control-plane layer is `control-plane/`. | Map old control-plane checks to current target layout. |
| Validation execution | Running any validator requires separate exact-run approval. | Keep Batch 9 to planning only unless later separately authorized. |

## Candidate B - Maintenance/Sync Helper Planning

| Item | Value |
| --- | --- |
| Candidate name | Maintenance/sync helper planning |
| Related source | `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` |
| Possible future target | `ops/maintenance/sync-upstream-vcp.sh` or restricted reference/runbook |
| Source SHA-256 | `5ef54e8130a5d632423ce191b40cffc6da54a0e0ffbd5e813ca3a63ec05c6cd6` |
| Source size | 439 bytes |
| Candidate handling | Defer until a separate restricted maintenance/sync decision. |
| Risk | High if misunderstood; the source prints remote and branch-sensitive commands. |

### Maintenance/Sync Source Evidence

The source helper prints a guarded manual procedure that includes remote
inspection, branch inspection, fetches from multiple remotes, merge-base review,
checkout, pull, branch creation, and merge preparation. This candidate-selection
document intentionally does not reproduce the procedure as copy-ready commands.

The script says it does not merge automatically, but the printed procedure is
still remote, branch, checkout, pull, and merge-adjacent. That makes it a poor
next low-risk batch while validation path rewrites remain unresolved.

## Comparison

| Criterion | Workspace validator rewrite planning | Maintenance/sync helper planning |
| --- | --- | --- |
| Directly improves local validation readiness | Yes | No |
| Requires remote action | No | No as planning, but topic is remote-adjacent |
| Requires branch movement | No | No as planning, but source procedure includes branch movement |
| Can stay planning-only | Yes | Yes |
| Main risk | Wrong authority paths if rewritten too early | Remote/branch/sync instructions could be mistaken as usable |
| Current target clarity | Partial, but enough for a rewrite map | Weak; handling could be helper, reference, or runbook |
| Best low-risk next step | Yes | No |

## Selection

Selected Batch 9 candidate:

```text
Workspace validator rewrite planning
```

Reason:

The workspace validator is local and path-based. Its current problem is stale
layout assumptions, which can be handled safely as a rewrite plan without
creating or running a script. The maintenance/sync helper is more sensitive
because even its printed procedure names remote, checkout, pull, branch, and
merge operations.

## Batch 9 Guardrails

- Do not create `ops/validation/validate-workspace.sh` in the candidate-selection
  step.
- Do not execute source or migrated validation scripts.
- Do not make scripts executable.
- Do not create `ops/maintenance/sync-upstream-vcp.sh`.
- Do not copy remote, branch, checkout, pull, merge, push, release, deploy, or
  sync instructions into runnable form.
- Do not recreate root `SECURITY_BOUNDARIES.md` or root `WORKSPACE_REGISTRY.yaml`
  as authoritative files.
- Do not treat missing future-migration files as current validation failures.
- Do not print secret values or file contents.
- Do not read private state, logs, cache, runtime output, or active local config.

## Suggested Batch 9 Plan Scope

Recommended next plan file:

```text
ops/migration/plans/phase-2-batch-9-workspace-validator-rewrite-plan-2026-06-28.md
```

Recommended content:

- old path to WSL target path mapping
- checks that are valid now
- checks that must wait for registry or future asset migration
- checks that must never recreate root authority files
- no-execution boundary
- preflight required before any future script creation

The next plan should remain a rewrite plan, not a script patch, unless the user
separately asks for a formal patch plan.

## Preflight Needed Before Rewrite Plan

| Check | Reason |
| --- | --- |
| Reconfirm source `validate-workspace.sh` exists and hash matches this selection. | Detect source drift before planning rewrite details. |
| Re-read workspace registry and security target decisions. | Ensure authority paths are not guessed. |
| Re-read current WSL root README inventory. | Build the path map from actual current files. |
| Confirm `ops/validation/validate-workspace.sh` remains absent. | Avoid overwriting user-owned work. |
| Confirm `ops/maintenance/sync-upstream-vcp.sh` remains absent. | Keep maintenance/sync deferred. |
| Scan rewrite plan for live-secret and command-risk wording. | Keep the plan non-executing and non-secret-bearing. |

## Deferred Candidate

Deferred:

```text
Maintenance/sync helper planning
```

Required before reconsidering:

- decide whether the helper should become a restricted reference, a maintenance
  runbook, or a non-executable helper
- define an approval packet for remote/branch-sensitive operations
- prohibit treating printed commands as current authorization
- require explicit remote intent before any fetch, pull, checkout, merge, push,
  release, or deploy action

## Related Documents

- `phase-2-batch-8-candidate-selection-2026-06-28.md`
- `phase-2-batch-8-validation-execution-authorization-template-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-8-validation-execution-authorization-template-receipt-2026-06-28.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../decisions/target-layer-reconciliation-2026-06-27.md`
- `../../../ops/validation/README.md`
- `../../../control-plane/templates/validation/validation-execution-authorization.template.md`
