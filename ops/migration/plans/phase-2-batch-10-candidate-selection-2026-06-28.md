# Phase 2 Batch 10 Candidate Selection - 2026-06-28

Status: candidate selection only; no migration performed.

Notice: This document selects the next Phase 2 batch candidate after Batch 9.
It is not migration authorization, not authorization to copy or rewrite
`WORKSPACE_REGISTRY.yaml`, not authorization to create maintenance/sync helpers,
not authorization to execute validation scripts, not authorization to change
executable bits, and not authorization for remote, branch, push, release,
deploy, secret, private-state, log, cache, or runtime actions.

## Candidate Question

Choose the safer next Batch 10 direction:

1. Registry authority migration.
2. Maintenance/sync helper planning.

## Current Context

| Item | Current state |
| --- | --- |
| Registry target decision | `WORKSPACE_REGISTRY.yaml` belongs under `control-plane/registry/`. |
| Registry target file | `control-plane/registry/WORKSPACE_REGISTRY.yaml` is still absent. |
| Registry directory | `control-plane/registry/` exists with README and example files. |
| Batch 9 workspace validator | Completed and three-way reviewed; registry target is currently a deferred warning path. |
| Maintenance/sync helper target | `ops/maintenance/sync-upstream-vcp.sh` is still absent. |
| Current repository state | `/home/jenn/AGENTS_OS_Workspace` is not a Git repository. |

## Candidate A - Registry Authority Migration

| Item | Value |
| --- | --- |
| Candidate name | Registry authority migration |
| Related source | `A:\AGENTS_OS_Workspace\WORKSPACE_REGISTRY.yaml` |
| Planned target | `control-plane/registry/WORKSPACE_REGISTRY.yaml` |
| Source SHA-256 | `4abadb46ce14df8116d1e2205ccda9c66bd61ca84b781a80d1f18e3456c5fc40` |
| Source size | 3074 bytes |
| YAML parse | Passed during candidate selection. |
| Observed structure | Top-level keys: `workspace`, `layers`, `repositories`, `security`; 8 layers; 6 repositories. |
| Candidate handling | Plan a normalized authority migration; do not copy source as-is. |
| Risk | Medium-low as a local data migration; medium if stale paths become authority. |

### Registry Source Evidence

The source registry is structured YAML with workspace metadata, layer metadata,
repository entries, and security defaults. It is not a script and does not
perform remote actions.

Observed risk signals:

| Signal | Impact | Required handling |
| --- | --- | --- |
| Old control-plane layer | Source layer id/path uses old `agents_os` / `AGENTS_OS/`. | Normalize to current `control-plane/` target layout before making it authoritative. |
| Repository and layer authority | Registry will be consumed by validators and governance. | Patch plan must separate verified current paths from historical or unverified entries. |
| Root authority drift | Target decision rejects root `WORKSPACE_REGISTRY.yaml` as authoritative. | Create only under `control-plane/registry/` if later authorized. |
| Security defaults | Source includes forbidden actions such as push, release, deploy, secret printing, env reading, main modification, and destructive delete. | Preserve as policy metadata, not as an execution mechanism. |

## Candidate B - Maintenance/Sync Helper Planning

| Item | Value |
| --- | --- |
| Candidate name | Maintenance/sync helper planning |
| Related source | `A:\AGENTS_OS_Workspace\ops\scripts\sync-upstream-vcp.sh` |
| Possible future target | `ops/maintenance/sync-upstream-vcp.sh` or restricted reference/runbook |
| Source SHA-256 | `5ef54e8130a5d632423ce191b40cffc6da54a0e0ffbd5e813ca3a63ec05c6cd6` |
| Source size | 439 bytes |
| Candidate handling | Defer until a restricted maintenance/sync decision. |
| Risk | High if misunderstood; the source prints remote and branch-sensitive procedure text. |

### Maintenance/Sync Source Evidence

The source helper prints a guarded manual procedure involving remote inspection,
branch inspection, fetches from multiple remotes, merge-base review, checkout,
pull, branch creation, and merge preparation. This candidate-selection document
intentionally does not reproduce that procedure as copy-ready commands.

The source says it does not merge automatically, but the printed procedure is
still remote, branch, checkout, pull, and merge-adjacent. It remains a poor
low-risk next batch compared with a local registry-data patch plan.

## Comparison

| Criterion | Registry authority migration | Maintenance/sync helper planning |
| --- | --- | --- |
| Directly closes current deferred warning | Yes; Batch 9 validator warns on missing registry. | No. |
| Local and reversible | Yes, if patch creates one registry file plus receipt. | Yes as planning only, but topic is remote-adjacent. |
| Requires script execution | No. | No as planning, but future helper is script/procedure-adjacent. |
| Requires remote action | No. | No as planning, but source procedure is remote-adjacent. |
| Main risk | Stale paths becoming authority. | Remote/branch/sync instructions being mistaken as usable. |
| Low-risk next step | Patch plan for normalized registry migration. | Defer. |

## Selection

Selected Batch 10 candidate:

```text
Registry authority migration
```

Reason:

The registry is a local structured data asset with an already-decided authority
target. It closes a current Batch 9 deferred warning and does not require script
execution, remote actions, branch movement, or maintenance procedures. The
maintenance/sync helper remains more sensitive because its source procedure is
remote and branch adjacent.

## Batch 10 Guardrails

- Do not create `control-plane/registry/WORKSPACE_REGISTRY.yaml` during candidate
  selection.
- Do not copy the source registry as-is without a patch plan.
- Do not create a root `WORKSPACE_REGISTRY.yaml`.
- Do not create `ops/maintenance/sync-upstream-vcp.sh`.
- Do not reproduce maintenance/sync procedure text as copy-ready commands.
- Do not run validation scripts.
- Do not run Git, remote, branch, push, release, deploy, network, destructive,
  copy, move, or sync actions.
- Do not print secret values or file contents from secret-like files.
- Do not read private state, logs, cache, runtime output, or active local config.

## Suggested Batch 10 Plan Scope

Recommended next plan file:

```text
ops/migration/plans/phase-2-batch-10-registry-authority-patch-plan-2026-06-28.md
```

Recommended planned target:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml
```

Recommended handling:

- parse source YAML
- normalize old `AGENTS_OS/` control-plane path to `control-plane/`
- preserve security default-forbidden policy metadata
- mark repository paths or URLs as registry metadata, not remote-action
  authorization
- keep root registry absent
- create receipt if later authorized

## Preflight Needed Before Patch Plan

| Check | Reason |
| --- | --- |
| Reconfirm source registry exists and hash matches this selection. | Detect source drift before planning a patch. |
| Parse source registry YAML. | Ensure the source is structurally readable. |
| Reconfirm target registry file is absent. | Avoid overwriting user-owned work. |
| Re-read registry target decision. | Keep authority placement under `control-plane/registry/`. |
| Re-read current `control-plane/registry/README.md`. | Keep examples separate from active registry state. |
| Scan source registry for live-secret patterns. | Avoid promoting secret-like content. |
| Scan planned target draft for stale authority paths. | Prevent old `AGENTS_OS/` and root registry/security assumptions from becoming authoritative. |
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

- `phase-2-batch-9-candidate-selection-2026-06-28.md`
- `phase-2-batch-9-workspace-validator-patch-plan-2026-06-28.md`
- `../receipts/rules-assets-batch-9-workspace-validator-receipt-2026-06-28.md`
- `../decisions/workspace-registry-security-boundaries-targets-2026-06-27.md`
- `../decisions/ops-scripts-targets-2026-06-27.md`
- `../../../control-plane/registry/README.md`
- `../../../ops/validation/validate-workspace.sh`
