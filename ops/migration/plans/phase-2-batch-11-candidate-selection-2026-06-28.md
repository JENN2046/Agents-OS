# Phase 2 Batch 11 Candidate Selection - 2026-06-28

Status: candidate selection only; no migration performed.

Notice: This document selects the next Phase 2 batch candidate after Batch 10.
It is not migration authorization, not authorization to execute validation
scripts, not authorization to create maintenance/sync helpers, not authorization
to change executable bits, and not authorization for remote, branch, push,
release, deploy, secret, private-state, log, cache, or runtime actions.

## Candidate Question

Choose the safer next Batch 11 direction:

1. Registry consumer/readiness check.
2. Maintenance/sync helper planning.

## Current Context

| Item | Current state |
| --- | --- |
| Registry authority | `control-plane/registry/WORKSPACE_REGISTRY.yaml` now exists after Batch 10. |
| Batch 10 remaining risk | Registry consumer integration was explicitly left for a separate batch. |
| Registry README interface claim | `control-plane/registry/README.md` names ops validators, Codex prompts, extension loader, and governance layer as expected consumers. |
| Workspace validator | `ops/validation/validate-workspace.sh` lists `control-plane/registry/WORKSPACE_REGISTRY.yaml` as a deferred warning path. |
| Maintenance/sync helper target | `ops/maintenance/sync-upstream-vcp.sh` is still absent. |
| Maintenance/sync decision | Existing ops-script decision keeps sync helpers separate from validation and restricted until remote/branch actions are separately approved. |
| Current repository state | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Candidate A - Registry Consumer/Readiness Check

| Item | Value |
| --- | --- |
| Candidate name | Registry consumer/readiness check |
| Related target | `control-plane/registry/WORKSPACE_REGISTRY.yaml` |
| Related surfaces | `control-plane/registry/README.md`, `ops/validation/validate-workspace.sh`, prompt catalogs, governance references, extension-loader references |
| Candidate handling | Plan a docs-only readiness and consumer evidence check before changing consumers. |
| Risk | Low as read-only planning; medium if the check is mistaken for consumer integration or validator execution. |

### Registry Consumer Evidence

Batch 10 made the registry authority file present, but it did not prove that
current consumers are updated, runnable, or integrated. The next safest step is
to map actual and claimed consumers before changing scripts, prompts, loaders,
or governance behavior.

Observed readiness signals:

| Signal | Impact | Required handling |
| --- | --- | --- |
| Registry README claims future/active interface users. | The README may now need reconciliation with Batch 10 reality. | Check wording and identify stale Batch 1-era language without editing during candidate selection. |
| Workspace validator references the registry path as deferred. | Batch 10 may have changed the validator's expected warning behavior. | Inspect only; do not execute the validator without a separate authorization packet. |
| Batch 10 receipt deferred consumer integration. | There is an explicit open item to close. | Plan a bounded readiness report before any consumer patch. |
| Registry is data, not a script. | Readiness mapping can remain local and reversible. | Avoid changing executable bits or running scripts. |

## Candidate B - Maintenance/Sync Helper Planning

| Item | Value |
| --- | --- |
| Candidate name | Maintenance/sync helper planning |
| Related source | `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` |
| Possible future target | `ops/maintenance/sync-upstream-vcp.sh`, restricted reference, or maintenance runbook |
| Candidate handling | Defer until registry readiness is clearer and an approval-packet shape is defined. |
| Risk | High if misunderstood; the source topic is remote, branch, checkout, pull, and merge adjacent. |

### Maintenance/Sync Evidence

The maintenance/sync helper remains a legitimate later candidate, but it is not
the lowest-risk Batch 11 direction. Even planning can accidentally normalize
copy-ready remote or branch instructions if the boundary is not tight. This
candidate should wait until a restricted-reference or approval-packet plan is
explicitly requested.

## Comparison

| Criterion | Registry consumer/readiness check | Maintenance/sync helper planning |
| --- | --- | --- |
| Directly follows Batch 10 | Yes; closes the deferred consumer/readiness question. | Indirect; still a separate maintenance topic. |
| Local and reversible | Yes, as a docs-only evidence plan. | Yes as planning only, but the topic is remote/branch adjacent. |
| Requires script execution | No. | No as planning, but future helper is script/procedure adjacent. |
| Requires remote action | No. | No as planning, but the source procedure is remote adjacent. |
| Main risk | Overstating readiness or silently changing consumers. | Treating sync procedure text as current authorization. |
| Low-risk next step | Patch plan for a registry consumer/readiness evidence check. | Defer. |

## Selection

Selected Batch 11 candidate:

```text
Registry consumer/readiness check
```

Reason:

The registry authority was just created, and the prior receipt explicitly left
consumer integration unverified. A read-only readiness check is the lowest-risk
next move because it maps consumers and stale references without executing
validators, changing scripts, creating sync helpers, or touching remote state.
Maintenance/sync helper planning remains useful, but it is more sensitive
because its source topic is remote and branch adjacent.

## Batch 11 Guardrails

- Do not edit registry consumers during candidate selection.
- Do not execute `ops/validation/validate-workspace.sh` or any other validation
  script.
- Do not create `ops/maintenance/sync-upstream-vcp.sh`.
- Do not reproduce maintenance/sync procedure text as copy-ready commands.
- Do not create root or governance copies of `WORKSPACE_REGISTRY.yaml`.
- Do not change executable bits.
- Do not run Git, remote, branch, push, release, deploy, network, destructive,
  copy, move, or sync actions.
- Do not print secret values or file contents from secret-like files.
- Do not read private state, logs, cache, runtime output, or active local config.

## Suggested Batch 11 Plan Scope

Recommended next plan file:

```text
ops/migration/plans/phase-2-batch-11-registry-consumer-readiness-check-plan-2026-06-28.md
```

Recommended handling:

- inspect references to `WORKSPACE_REGISTRY.yaml` and `control-plane/registry`
  in migrated control-plane, ops, prompt, governance, and extension surfaces
- compare declared consumers in `control-plane/registry/README.md` with observed
  file references
- check whether Batch 10 made any README wording stale
- inspect `ops/validation/validate-workspace.sh` without executing it
- keep the result as evidence and next-step recommendations, not consumer
  integration
- create a receipt only if a later authorized patch creates or updates files

## Preflight Needed Before Patch Plan

| Check | Reason |
| --- | --- |
| Reconfirm Batch 10 registry file exists and hash is stable. | Detect drift before using it as readiness evidence. |
| Re-read Batch 10 receipt. | Preserve the exact deferred consumer-integration boundary. |
| Re-read `control-plane/registry/README.md`. | Identify stale future-authority wording and declared consumers. |
| Re-read `ops/validation/validate-workspace.sh`. | Inspect registry-related behavior without executing the validator. |
| Run reference search for registry path names. | Distinguish actual consumers from aspirational README claims. |
| Scan planned readiness report for live-secret and command-risk text. | Keep the batch documentary and non-executable. |
| Confirm maintenance/sync target remains absent. | Keep remote/branch-sensitive helper deferred. |

## Deferred Candidate

Deferred:

```text
Maintenance/sync helper planning
```

Required before reconsidering:

- decide whether the helper should become a restricted reference, a maintenance
  runbook, or a non-executable helper
- define an approval packet for remote/branch-sensitive operations
- prohibit treating printed procedure text as current authorization
- require explicit remote intent before any fetch, pull, checkout, merge, push,
  release, or deploy action

## Related Documents

- `phase-2-batch-10-candidate-selection-2026-06-28.md`
- `phase-2-batch-10-registry-authority-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-10-registry-authority-receipt-2026-06-28.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../../validation/validate-workspace.sh`
- `../../../control-plane/registry/README.md`
