# Phase 7 Runtime/Loader Directory Boundary Plan

Date: 2026-06-28

Status: plan only.

This document plans the next Phase 7 directory-boundary gate for runtime,
extension, execution, and governance-adjacent areas. It names candidate
directories, future metadata fields, exclusions, and stop conditions.

It does not collect directory metadata, list child entries, read file contents,
follow references, execute scripts, or grant runtime/loader acceptance.

## Authorization

User request:

> 创建 phase-7-runtime-loader-directory-boundary-plan-2026-06-28.md，只规划候选目录、metadata 字段、排除项和停止条件。

Allowed in this step:

- create this planning-only document
- use existing Tier B closeout/evidence receipts as inputs
- define candidate directories, future metadata fields, exclusions, and stop
  conditions

Not allowed in this step:

- collect fresh metadata for candidate directories
- list directory children
- count directory children
- compute recursive size or tree hashes
- read files inside candidate directories
- follow symlinks, imports, README references, manifests, route files, or package
  references
- execute validators, runtime, loaders, scripts, package managers, or sync
  commands
- modify registry, consumers, runtime, extensions, execution, or governance
- grant runtime behavior, loader behavior, extension execution, or full consumer
  integration acceptance

## Inputs Rechecked Before Plan Creation

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-tier-b-narrow-text-read-evidence-review-closeout-receipt-2026-06-28.md` | `013bc44c18ea7b598bd23004de50ea87924916c95f8951ee58bb77ed95c73f50` | Admits directory-boundary planning with strict limits. |
| `ops/migration/inventory/phase-7-runtime-loader-tier-b-narrow-text-read-evidence-2026-06-28.md` | `ac43eb994cfaf4bafb2277e40be3d95ce3330237a8562768f41577f61900c20a` | Provides README evidence for runtime, extension, execution, and governance separation. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-tier-b-narrow-text-read-evidence-receipt-2026-06-28.md` | `94d3cfc014e61654526adef7a32f5f12eec12f447899e1956b2ad1a955301697` | Confirms Tier B evidence was collected inside the approved README read window. |
| `ops/migration/plans/phase-7-runtime-loader-tier-b-narrow-text-read-plan-2026-06-28.md` | `427f672fa63c5ed70fe5def0d068794937bd55a35d2df81f08649ee76293e0dd` | Defines the Tier B read boundaries that this plan inherits. |

Target absence confirmed before creation:

| Future target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-directory-boundary-plan-2026-06-28.md` | absent |
| `ops/migration/inventory/phase-7-runtime-loader-directory-boundary-metadata-evidence-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-receipt-2026-06-28.md` | absent |

## Candidate Directories

The next gate may plan metadata-only checks for these candidate paths only:

| Candidate directory | Planned boundary role | Source of candidacy | Future metadata status |
| --- | --- | --- | --- |
| `runtime/` | Runtime root boundary. | Tier B evidence says runtime cores belong in the runtime area and excludes private extensions, private state, secrets, and runtime cache. | Eligible for future path-only metadata preflight/evidence. |
| `extensions/vcp-toolbox-jenn/` | Jenn-owned extension package boundary. | Tier A metadata recorded it as a present directory; Tier B evidence says extension packages belong in the extension area. | Eligible for future path-only metadata preflight/evidence. |
| `execution/` | Execution root boundary for harnesses, workers, provider adapters, and bridges. | Tier B evidence says execution assets belong in the execution area and excludes top-level governance rules. | Eligible for future path-only metadata preflight/evidence. |
| `governance/codex-router/` | Governance-adjacent router boundary, treated as boundary-sensitive. | Tier A metadata recorded it as a present directory; Tier B evidence reinforces that governance rules must not be silently folded into execution. | Eligible for future path-only metadata preflight/evidence only. |

No candidate above is authorized for content inspection by this plan.

## Planned Metadata Fields For A Future Evidence Step

A later separately authorized metadata evidence step may collect only these
fields for each candidate path:

| Field | Purpose | Boundary |
| --- | --- | --- |
| Candidate ID | Stable label for the evidence row. | Derived from this plan, not from directory content. |
| Candidate path | Exact relative path from workspace root. | Must match one of the four paths in this plan exactly. |
| Planned boundary role | Runtime, extension, execution, or governance-adjacent. | Derived from this plan and Tier B closeout only. |
| Existence state | Whether the exact candidate path exists. | Check exact path only; do not inspect children. |
| Path type | Directory, file, symlink, missing, or other. | Use path metadata only. If not a directory, stop that candidate. |
| Mode | Permission mode for the exact path. | No owner, group, inode, mtime, or recursive permission scan. |
| Indirect path flag | Whether the candidate itself is a symlink or indirect path. | If indirect, stop before resolving or following it. |
| Workspace containment | Whether the exact non-indirect path remains under `/home/jenn/AGENTS_OS_Workspace`. | Do not follow indirect paths to prove containment. |
| Metadata result | PASS, WARN, FAIL, or DEFERRED for the exact candidate path. | Must not imply content acceptance or behavior acceptance. |
| Notes | Concise boundary note. | No child names, no file names, no secret-like values, no full command output. |

Forbidden metadata fields:

- child entry names
- child entry count
- recursive tree
- recursive size
- file hashes below the directory
- directory package or manifest contents
- README contents
- script names
- route names
- module names
- owner/group/inode/device details
- mtime/ctime history
- cache/private-state contents

## Exclusions

| Excluded path or class | Reason |
| --- | --- |
| `runtime/VCPToolBox/*` | Earlier metadata recorded these planned paths as missing; path reconciliation is required before any deeper planning or inspection. |
| `extensions/` root | This plan scopes the already identified extension package directory, not the whole extension root. |
| Children of `extensions/vcp-toolbox-jenn/` | Child listing/content reads require a later allowlist plan. |
| Children of `governance/codex-router/` | Governance-adjacent reads require a later allowlist plan and must not be treated as execution inspection. |
| Children of `runtime/` | Runtime child discovery is not authorized by this planning step. |
| Children of `execution/` | Execution child discovery is not authorized by this planning step. |
| Any `.env`, secret, cache, private state, log, database, or credential file | Out of scope and must not be recorded. |
| Any symlink or indirect path target | Stop before following; indirect targets are not part of this boundary plan. |
| Any referenced file from README, manifest, package config, route table, import, or script | References are not followable in this gate. |
| Any command that executes runtime, loader, validator, package manager, sync, deploy, or network behavior | Execution is outside this gate. |

## Future Metadata Evidence Preflight

Before any metadata evidence is collected, a future preflight must confirm:

| Check | Required result |
| --- | --- |
| This directory-boundary plan hash | Stable from plan creation. |
| Tier B closeout hash | Stable at `013bc44c18ea7b598bd23004de50ea87924916c95f8951ee58bb77ed95c73f50`. |
| Tier B evidence hash | Stable at `ac43eb994cfaf4bafb2277e40be3d95ce3330237a8562768f41577f61900c20a`. |
| Future metadata evidence target | Absent before creation. |
| Future metadata receipt target | Absent before creation. |
| Candidate set | Exactly the four paths in this plan; no additions. |
| Command boundary | Exact-path metadata only, with no child listing and no content read. |
| Redaction boundary | No secret-like value, private path expansion, or raw command dump may be written. |

If any required result fails, directory metadata evidence collection is not
admitted.

## Stop Conditions

Stop before or during a future metadata evidence step if:

- this plan hash drifts
- Tier B closeout or evidence hashes drift
- a future evidence or receipt target already exists
- a candidate path is not one of the four exact paths in this plan
- the check would list child entries or count children
- the check would read file contents
- the check would follow a symlink or indirect path
- the check would traverse outside `/home/jenn/AGENTS_OS_Workspace`
- the check would expose secrets, cache, private state, logs, database files, or
  credential material
- the check would execute runtime, loader, validator, package-manager, sync,
  deploy, network, or remote commands
- a candidate path is missing or not a directory and the next action would try to
  infer children anyway
- governance-adjacent paths are treated as execution assets without a separate
  boundary decision

## Future Outputs

If separately authorized after preflight, the next metadata-only gate may create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-7-runtime-loader-directory-boundary-metadata-evidence-2026-06-28.md` | Exact-path metadata evidence for the four candidate directories only. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-receipt-2026-06-28.md` | Receipt recording preflight, exact metadata collected, deferred items, and stop-condition compliance. |

This plan does not authorize either output by itself.

## Acceptance Boundary

This plan can only support a future directory-boundary metadata gate.

It cannot grant:

- directory content-read authorization
- child listing authorization
- runtime behavior acceptance
- loader behavior acceptance
- extension execution acceptance
- governance router acceptance
- validator/script execution authorization
- full consumer integration acceptance
- migration, rewrite, or normalization authorization

## Result

Directory-boundary planning is complete for four candidate paths. The next safe
step is a separate formal preflight for exact-path metadata-only evidence.

Marker:

```text
PHASE_7_RUNTIME_LOADER_DIRECTORY_BOUNDARY_PLAN_CREATED_NO_DIRECTORY_METADATA_COLLECTION
```
