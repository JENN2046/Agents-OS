# Phase 2 Remaining Scope And Closeout Plan - 2026-06-28

Status: closeout planning only; no validation executed and no migration patch
performed.

Notice: This plan records the remaining Phase 2 rules-asset scope after Batch
12. It is not authorization to execute validation scripts, not authorization to
create maintenance/sync helpers, not authorization to change executable bits,
and not authorization for remote, branch, release, deploy, secret,
private-state, log, cache, runtime, or project-repository migration actions.

## Current Position

Phase 0 and Phase 1 are complete for the rules-asset control-plane migration.
Phase 2 has completed the main low-risk rules-asset migration surface through
Batch 12.

The original high-level plan still names:

- Phase 3: local and narrow validation
- Phase 4: final receipt

This closeout plan does not enter Phase 3 or Phase 4. It prepares the decision
boundary for when Phase 2 can be declared ready for those phases.

## Completed Phase 2 Batches

| Batch | Area | Receipt |
| --- | --- | --- |
| Batch 1 | Contracts and registry examples | `rules-assets-batch-1-contracts-registry-examples-receipt-2026-06-27.md` |
| Batch 2 | Ordinary templates | `rules-assets-batch-2-ordinary-templates-receipt-2026-06-27.md` |
| Batch 3 | Env example template | `rules-assets-batch-3-env-template-receipt-2026-06-27.md` |
| Batch 4a | Security boundary authority | `rules-assets-batch-4-security-boundary-authority-receipt-2026-06-28.md` |
| Batch 4b | Security template | `rules-assets-batch-4-security-template-receipt-2026-06-28.md` |
| Batch 5 | Ordinary runbooks | `rules-assets-batch-5-ordinary-runbooks-receipt-2026-06-28.md` |
| Batch 6 | Validation script files | `rules-assets-batch-6-validation-scripts-receipt-2026-06-28.md` |
| Batch 7 | Prompt catalogs | `rules-assets-batch-7-prompt-catalogs-receipt-2026-06-28.md` |
| Batch 8 | Validation execution authorization template | `rules-assets-batch-8-validation-execution-authorization-template-receipt-2026-06-28.md` |
| Batch 9 | Workspace validator rewrite | `rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md` |
| Batch 10 | Registry authority | `rules-assets-batch-10-registry-authority-receipt-2026-06-28.md` |
| Batch 11 | Registry consumer/readiness evidence | `rules-assets-batch-11-registry-consumer-readiness-receipt-2026-06-28.md` |
| Batch 12 | Consumer alignment | `rules-assets-batch-12-consumer-alignment-receipt-2026-06-28.md` |

## Closeout Judgment

Phase 2 can be considered closeout-ready for the original low-risk rules-asset
scope if the user accepts that the following items are intentionally deferred:

| Item | Closeout classification | Reason |
| --- | --- | --- |
| Validation script execution | Defer to Phase 3 or exact-run authorization | Batch 8 created an authorization template, but no run has been approved. |
| Workspace validator runtime behavior | Defer to Phase 3 or exact-run authorization | Batch 12 aligned static path classification; script execution remains unverified. |
| Shell syntax-only reparse after Batch 12 | Optional Phase 3 preflight | Syntax-only parsing is lower risk than execution, but it is still a validation step outside this planning-only closeout. |
| Maintenance/sync helper | Defer to separate restricted maintenance project | Source procedure is remote and branch adjacent. |
| Runtime/git-adjacent validators | Defer until runtime migration and git-output policy exist | These validators touch runtime or repository state assumptions. |
| Prompt/governance/extension-loader consumer integration | Defer to later consumer integration review | Batch 11 classified several consumers as declaration-only. |
| Registry entry updates | Defer to separate registry-entry patch plans | Batch 12 clarified registry data exists, but changing entries needs its own authorization. |
| Extension path normalization from example registry data | Defer to extension-asset migration decision | Batch 1 intentionally kept example source values and deferred normalization. |
| Project repository migration | Out of Phase 2 rules-asset scope | Runtime, domain, memory, and project repos require their own migration tracks. |

## Remaining Work Categories

### Must Do Before Phase 2 Closeout

| Work | Planned output | Notes |
| --- | --- | --- |
| Closeout readiness evidence | `ops/migration/inventory/phase-2-closeout-readiness-evidence-2026-06-28.md` | Static evidence only; list completed receipts, deferred items, and no-go boundaries. |
| Phase 2 closeout receipt | `ops/migration/receipts/rules-assets-phase-2-closeout-receipt-2026-06-28.md` | Records the closeout evidence creation and what remains unvalidated. |

These can be performed as a final Phase 2 closeout batch without executing
validators or changing migrated assets.

### Optional Before Phase 3

| Work | Handling |
| --- | --- |
| Syntax-only parse of `ops/validation/validate-workspace.sh` after Batch 12 | Request explicit validation authorization, or include in Phase 3 plan. |
| Static command-risk scan over all migrated rules assets | Can be planned as Phase 3 local validation. |
| Static secret-like scan over all migrated rules assets | Can be planned as Phase 3 local validation; do not read secret files. |

### Explicitly Deferred Beyond Phase 2

| Work | Handling |
| --- | --- |
| `ops/maintenance/sync-upstream-vcp.sh` | Restricted maintenance/sync planning only; no helper creation by default. |
| Runtime project validators | Wait for runtime migration strategy. |
| Prompt activation or behavior authority | Requires separate prompt authority review; catalogs are not active prompts. |
| Extension loader or governance consumer integration | Requires direct consumer implementation evidence. |
| Registry entry changes | Requires specific registry-entry patch plan and receipt. |
| Runtime/domain/memory/project repository migration | Separate migration program, not a rules-asset closeout item. |

## Automatic Progress Boundary

Safe automatic next step:

```text
Create Phase 2 closeout readiness evidence and a closeout receipt only.
```

That step may:

- read existing Phase 2 plans and receipts
- list completed batches
- list deferred items
- confirm deferred high-risk targets remain absent
- scan the new closeout evidence and receipt for secret-like and command-risk
  text

That step must not:

- execute validators
- run shell syntax parsing unless explicitly authorized as validation
- create maintenance/sync helpers
- change executable bits
- modify migrated rule assets
- modify registry data
- touch runtime, domain, memory, private-state, cache, log, or project-repo
  content
- perform remote, branch, push, merge, release, deploy, copy, move, or sync
  actions

## Proposed Phase 3 Entry Criteria

Before Phase 3 validation begins, require a separate plan that names:

| Criterion | Required decision |
| --- | --- |
| Validation scope | Which files or directories are scanned. |
| Script handling | Whether syntax-only parsing is allowed, and which scripts are covered. |
| Execution boundary | Whether any script may be executed; default is no. |
| Secret handling | What patterns are scanned without reading real secret files. |
| Output handling | Whether path names may be printed and how sensitive paths are summarized. |
| Stop conditions | What findings stop validation and require user review. |

## Proposed Phase 4 Entry Criteria

Before Phase 4 final receipt begins, require:

| Criterion | Required state |
| --- | --- |
| Phase 2 closeout evidence | Exists and records deferred scope. |
| Phase 3 validation status | Completed, skipped by decision, or explicitly deferred. |
| Receipts index | Batch receipts and closeout receipt are listed. |
| Remaining risks | Deferred work is named without being silently promoted. |
| Rollback posture | Local file rollback boundaries are documented. |

## Recommendation

Proceed with one final Phase 2 closeout batch:

```text
phase-2-closeout-readiness-evidence + rules-assets-phase-2-closeout-receipt
```

Then stop before Phase 3 validation unless the user explicitly authorizes the
validation scope.
