# Phase 7 Runtime/Loader Limited File-Read Allowlist Plan

Date: 2026-06-28

Status: plan only.

This document plans a future limited file-level read allowlist gate based on
previous top-level name evidence. It defines candidate files, required future
metadata/type preflight, read caps, red lines, and stop conditions.

It does not stat candidate names, confirm they are files, read file contents,
parse configs, execute scripts, inspect child metadata, recurse into
directories, or grant runtime/loader acceptance.

## Authorization

User request:

> 下一步创建 phase-7-runtime-loader-limited-file-read-allowlist-plan-2026-06-28.md，只规划候选文件、未来 metadata/type preflight、读取上限、红线和停止条件。

Allowed in this step:

- create this planning-only document
- use existing top-level name evidence and closeout receipts as inputs
- define candidate files, future metadata/type preflight, future read caps, red
  lines, and stop conditions

Not allowed in this step:

- stat candidate paths
- confirm candidate paths are regular files
- read candidate file contents
- parse JSON, YAML, Markdown, lockfiles, manifests, or package configs
- read hidden surfaces, generated artifacts, dependency directories, scripts, or
  nested paths
- execute validators, runtime, loaders, package managers, scripts, sync, deploy,
  network, or remote commands
- modify registry, consumers, runtime, extensions, execution, or governance
- grant runtime behavior, loader behavior, extension execution, governance router,
  or full consumer integration acceptance

## Inputs Rechecked Before Plan Creation

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-evidence-review-closeout-receipt-2026-06-28.md` | `acedac5e738504d3734bbae2063ec62284564d8ea83c3b4b6704f49ab9d0fe23` | Admits limited file-level read allowlist planning with strict limits. |
| `ops/migration/inventory/phase-7-runtime-loader-top-level-name-allowlist-evidence-2026-06-28.md` | `6c390ae726cf85e8f081491fd8d6b53c86b7e895afbb8a8e0da6f5472049f197` | Provides max-depth-one name evidence. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-evidence-receipt-2026-06-28.md` | `7d47ad583c8a3403eaab3760cf38d1239dcb5777696c473af25211155244da45` | Confirms name evidence was collected without child stat, child count, or content reads. |
| `ops/migration/plans/phase-7-runtime-loader-top-level-name-allowlist-plan-2026-06-28.md` | `1500c8ba152c7b002aba924b4fddabc4168c8dd2e6e67ed744dc88ca5b158f82` | Defines the name allowlist boundary inherited by this plan. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-preflight-receipt-2026-06-28.md` | `489be996ddbe543a619a0507090595f0842e93d2d39b17aca61167e32a80575c` | Confirms the name allowlist preflight. |

Target absence confirmed before creation:

| Future target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-limited-file-read-allowlist-plan-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-preflight-receipt-2026-06-28.md` | absent |
| `ops/migration/inventory/phase-7-runtime-loader-limited-file-read-allowlist-metadata-evidence-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-evidence-receipt-2026-06-28.md` | absent |

## Candidate File Allowlist

The paths below are name-derived planning candidates only. They are not verified
file facts until a future metadata/type preflight confirms exact path, path
type, mode, hash, size, and indirect-path state.

| Candidate path | Class | Source signal | Future planning status |
| --- | --- | --- | --- |
| `runtime/README.md` | Runtime Markdown | Runtime root README name appeared in top-level name evidence. | Eligible for future metadata/type preflight. |
| `execution/README.md` | Execution Markdown | Execution root README name appeared in top-level name evidence. | Eligible for future metadata/type preflight. |
| `governance/codex-router/AGENTS.md` | Governance instruction Markdown | Governance-adjacent agent instruction name appeared in top-level name evidence. | Eligible for future metadata/type preflight with authority caution. |
| `governance/codex-router/PROJECT_CONTINUE_ANCHOR.md` | Governance continuation Markdown | Governance-adjacent continuation anchor name appeared in top-level name evidence. | Eligible for future metadata/type preflight with authority caution. |
| `governance/codex-router/README.AGENTS_OS.md` | Governance AGENTS OS Markdown | Governance-adjacent AGENTS OS README name appeared in top-level name evidence. | Eligible for future metadata/type preflight with authority caution. |
| `governance/codex-router/README.md` | Governance Markdown | Governance-adjacent README name appeared in top-level name evidence. | Eligible for future metadata/type preflight with authority caution. |
| `governance/codex-router/routing-policy.yaml` | Governance policy YAML | Governance-adjacent routing policy name appeared in top-level name evidence. | Eligible for future metadata/type preflight; content read and semantic review must remain separate. |
| `governance/codex-router/package.json` | Package manifest JSON | Package manifest name appeared in top-level name evidence. | Eligible for future metadata/type preflight; script execution forbidden. |
| `governance/codex-router/tsconfig.json` | TypeScript config JSON | TypeScript config name appeared in top-level name evidence. | Eligible for future metadata/type preflight; build/typecheck execution forbidden. |
| `governance/codex-router/package-lock.json` | Lockfile JSON | Lockfile name appeared in top-level name evidence. | Metadata/type preflight candidate only; content read requires a later lockfile-specific gate. |

No other file path is in scope for this plan.

## Deferred Names And Exclusions

| Name or group | Decision | Reason |
| --- | --- | --- |
| `execution/bridges`, `execution/harness`, `execution/providers`, `execution/workers` | `DEFERRED_DIRECTORY_OR_CONTAINER` | These names were not verified as files and should be handled by a separate execution directory/container boundary plan. |
| `governance/codex-router/dist`, `docs`, `node_modules`, `packages`, `scripts`, `tests` | `DEFERRED_DIRECTORY_OR_HIGH_VOLUME_SURFACE` | Generated, dependency, documentation tree, script, package, or test surfaces require separate directory/file boundary planning. |
| Hidden names under `governance/codex-router/` | `DEFERRED_HIDDEN_SURFACE` | Hidden control surfaces require a separate hidden-surface gate before metadata or reads. |
| `extensions/vcp-toolbox-jenn/` | `NO_FILE_CANDIDATES_FROM_CURRENT_NAME_EVIDENCE` | The name evidence emitted no file-like candidate rows for this parent. |
| Any `.env`, secret, credential, private-state, cache, log, database, or generated private artifact name | `EXCLUDED` | Sensitive or private surfaces are outside this gate. |

## Future Metadata/Type Preflight

Before any file content read is considered, a future separately authorized
metadata/type preflight must confirm:

| Check | Required result |
| --- | --- |
| This plan hash | Stable from plan creation. |
| Top-level name evidence review closeout hash | Stable at `acedac5e738504d3734bbae2063ec62284564d8ea83c3b4b6704f49ab9d0fe23`. |
| Top-level name evidence hash | Stable at `6c390ae726cf85e8f081491fd8d6b53c86b7e895afbb8a8e0da6f5472049f197`. |
| Top-level name evidence receipt hash | Stable at `7d47ad583c8a3403eaab3760cf38d1239dcb5777696c473af25211155244da45`. |
| Future metadata evidence target | Absent before creation. |
| Future metadata receipt target | Absent before creation. |
| Candidate set | Exactly the candidate paths in this plan; no additions. |
| Exact path existence | Candidate exists at the exact relative path. |
| Path type | Candidate is a regular file. |
| Indirect path state | Candidate is not a symlink, junction, mount, or indirect path. |
| Mode | Record exact file mode. |
| SHA-256 | Record exact file hash before any content read planning proceeds. |
| Size | Record byte size for cap feasibility. |
| Line count | Record line count for text candidates only, without printing content. |
| Encoding/readability | Confirm text readability for text candidates, without printing content. |

If any candidate fails metadata/type preflight, it must be marked `DEFERRED` or
`FAILED_PREFLIGHT` and excluded from any later content-read authorization.

## Future Metadata Evidence Fields

A future metadata/type evidence step may collect only:

| Field | Purpose |
| --- | --- |
| Candidate path | Exact relative path from this plan. |
| Candidate class | Class from this plan. |
| Existence | Whether the exact path exists. |
| Path type | Regular file, directory, symlink, missing, or other. |
| Mode | Exact file mode. |
| SHA-256 | Exact file hash if regular non-indirect file. |
| Size bytes | Exact size for cap feasibility. |
| Line count | Text line count for text candidates only. |
| Indirect path marker | Whether the candidate is indirect. |
| Preflight result | PASS, WARN, FAIL, or DEFERRED. |
| Notes | Bounded note without file content. |

Forbidden metadata evidence fields:

- file contents
- parsed JSON/YAML values
- script commands
- dependency lists
- route lists
- hidden-surface contents
- owner/group/inode/device details
- mtime/ctime history
- nested path listings
- raw command dumps
- secret-like values

## Future Read Caps

Content reads remain not admitted by this plan. If later authorized after a
successful metadata/type preflight, the future content-read plan should use
these maximum caps:

| Candidate class | Candidate paths | Future maximum read cap |
| --- | --- | --- |
| Runtime/Execution Markdown | `runtime/README.md`, `execution/README.md` | At most first `160` lines and at most `32 KiB` per file. |
| Governance Markdown | `governance/codex-router/AGENTS.md`, `PROJECT_CONTINUE_ANCHOR.md`, `README.AGENTS_OS.md`, `README.md` | At most first `200` lines and at most `48 KiB` per file, with authority-risk labels. |
| Governance policy YAML | `governance/codex-router/routing-policy.yaml` | At most first `200` lines and at most `48 KiB`; parse/semantic review must be a separate gate. |
| Small JSON config | `governance/codex-router/package.json`, `tsconfig.json` | At most first `200` lines and at most `48 KiB`; script/build execution forbidden. |
| Lockfile JSON | `governance/codex-router/package-lock.json` | Metadata/type preflight only in this track; content read requires a later lockfile-specific plan. |

If a file exceeds the class cap, a future content-read evidence step must stop
for that file and record `READ_LIMIT_EXCEEDED` without reading beyond the cap.

## Red Lines

The future metadata/type preflight or any later content-read plan must stop or
defer when these conditions appear:

| Red line | Required handling |
| --- | --- |
| Input hash drift | Stop before metadata collection. |
| Candidate set expands or changes | Stop before metadata collection. |
| Candidate path is missing | Mark candidate `DEFERRED_MISSING`; do not infer alternatives. |
| Candidate path is not a regular file | Mark candidate `DEFERRED_NOT_REGULAR_FILE`; do not read. |
| Candidate path is indirect | Mark candidate `DEFERRED_INDIRECT_PATH`; do not follow. |
| Candidate is hidden, generated, dependency, cache, log, private-state, database, env, or secret-like | Exclude from this gate. |
| Metadata check would recurse or list sibling/child paths | Stop with `RECURSION_NOT_AUTHORIZED`. |
| Metadata check would parse or print content | Stop with `CONTENT_NOT_AUTHORIZED`. |
| Candidate content may contain credentials, tokens, private URLs, raw env values, or secrets | Future read plan must require redaction before evidence writes. |
| Package manifest contains scripts | Do not execute or summarize commands as authorization. |
| Routing policy appears authoritative | Record only after a later content-read review; do not grant router acceptance. |
| Lockfile is large or generated | Keep content read deferred unless a lockfile-specific plan is authorized. |
| Any requested action would run validators, builds, package managers, runtime, loader, sync, deploy, network, or remote commands | Stop and require separate authorization. |

## Stop Conditions

Stop before a future metadata/type preflight if:

- this plan hash drifts
- required input hashes drift
- future metadata evidence or receipt targets already exist
- candidate set differs from this plan
- exact-path metadata cannot be collected without reading content
- candidate metadata would require recursion or sibling listing
- candidate is not a regular non-indirect file
- candidate falls into an excluded hidden/generated/private/cache/log/db/env/secret
  surface
- evidence cannot avoid raw command dumps and secret-like values
- the user request expands from planning into reading content without a separate
  preflight and authorization

Stop before a future content-read step if:

- metadata/type preflight has not passed for that candidate
- file size or line count exceeds the planned cap
- redaction cannot be applied before evidence is written
- content read would require parsing, executing, importing, installing, building,
  syncing, or network access
- content read would imply runtime/loader/router/consumer acceptance

## Future Outputs

If separately authorized, the next metadata/type gate may create:

| Output | Purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-preflight-receipt-2026-06-28.md` | Preflight receipt confirming plan/input stability, target absence, and candidate set stability before metadata collection. |
| `ops/migration/inventory/phase-7-runtime-loader-limited-file-read-allowlist-metadata-evidence-2026-06-28.md` | Exact-path metadata/type evidence for candidate files only. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-file-read-allowlist-metadata-evidence-receipt-2026-06-28.md` | Receipt recording metadata evidence boundaries, pass/defer results, and unverified items. |

This plan does not authorize these outputs by itself.

## Acceptance Boundary

This plan can only support a future metadata/type preflight and evidence gate.

It cannot grant:

- direct file metadata collection without a separate preflight and authorization
- direct file content read authorization
- parse or semantic acceptance
- package script execution
- build/typecheck/test execution
- runtime behavior acceptance
- loader behavior acceptance
- extension execution acceptance
- governance router acceptance
- full consumer integration acceptance
- migration, rewrite, or normalization authorization

## Result

Limited file-level read allowlist planning is complete for name-derived candidate
files. The next safe step is a separate formal metadata/type preflight that
confirms plan/input stability, target absence, exact candidate set, and command
boundaries before any file metadata is collected.

Marker:

```text
PHASE_7_RUNTIME_LOADER_LIMITED_FILE_READ_ALLOWLIST_PLAN_CREATED_NO_FILE_METADATA_OR_CONTENT_READ
```
