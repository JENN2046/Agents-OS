# Phase 7 Runtime/Loader Top-Level Name Allowlist Plan

Date: 2026-06-28

Status: plan only.

This document plans a future top-level name allowlist gate for four previously
verified directory-boundary candidates. It defines which parent directories may
be considered, the future evidence output shape, red lines, and stop conditions.

It does not list directory children, count children, read file contents, collect
fresh directory metadata, execute scripts, or grant runtime/loader acceptance.

## Authorization

User request:

> 创建 phase-7-runtime-loader-top-level-name-allowlist-plan-2026-06-28.md，只规划未来允许列哪些目录的 top-level 名称、输出格式、红线和停止条件。

Allowed in this step:

- create this planning-only document
- use existing directory-boundary metadata evidence and closeout receipts as
  inputs
- define future parent directories, output format, red lines, and stop conditions

Not allowed in this step:

- list any top-level child names
- count directory children
- read directory contents beyond already recorded exact-path metadata
- read files inside candidate directories
- follow symlinks, manifests, README references, package configs, route files,
  imports, or scripts
- execute validators, runtime, loaders, scripts, package managers, sync, deploy,
  network, or remote commands
- modify registry, consumers, runtime, extensions, execution, or governance
- grant runtime behavior, loader behavior, extension execution, governance router,
  or full consumer integration acceptance

## Inputs Rechecked Before Plan Creation

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-review-closeout-receipt-2026-06-28.md` | `ac12010eed36f895c501db3980759f26ad13c7aac92f448f9c9f97e563d8b536` | Admits top-level name allowlist planning with strict limits. |
| `ops/migration/inventory/phase-7-runtime-loader-directory-boundary-metadata-evidence-2026-06-28.md` | `2d979a408a513f001081235497bbcdb4f18a776b1b9304a85cf349e554555eae` | Confirms four exact paths exist as direct directories with mode `755` and indirect marker `no`. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-receipt-2026-06-28.md` | `69ae9ae80de22bcd1a8d4f10a0ee8972d93e8193ecf9b9af5a1d04e7c27a40c9` | Confirms metadata evidence was exact-path only and did not list children. |
| `ops/migration/plans/phase-7-runtime-loader-directory-boundary-plan-2026-06-28.md` | `f2f0677a7b9c42db45f17c0fe92d0f5c59e2c8757509bf77a33fb1ca0b1035f5` | Defines the directory-boundary candidates inherited by this plan. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-preflight-receipt-2026-06-28.md` | `c99f2cca0e3f0d7e11e625dcdfbadc1db1c63ce399f2f839fd0994ab008fce6c` | Confirms the prior metadata gate preflight. |

Target absence confirmed before creation:

| Future target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-top-level-name-allowlist-plan-2026-06-28.md` | absent |
| `ops/migration/inventory/phase-7-runtime-loader-top-level-name-allowlist-evidence-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-evidence-receipt-2026-06-28.md` | absent |

## Future Parent Directory Allowlist

A later separately authorized evidence step may list top-level names only under
these exact parent directories:

| Parent directory | Planned boundary role | Future listing status |
| --- | --- | --- |
| `runtime/` | Runtime root boundary. | Eligible for top-level name evidence only. |
| `extensions/vcp-toolbox-jenn/` | Jenn-owned extension package boundary. | Eligible for top-level name evidence only. |
| `execution/` | Execution root boundary for harnesses, workers, provider adapters, and bridges. | Eligible for top-level name evidence only. |
| `governance/codex-router/` | Governance-adjacent router boundary. | Eligible for governance-sensitive top-level name evidence only. |

No other parent directory is in scope. The future evidence step must not expand
from a parent directory into nested paths.

## Future Evidence Output Format

If separately authorized after preflight, top-level name evidence must use a
minimal table with these fields only:

| Field | Meaning | Boundary |
| --- | --- | --- |
| Candidate ID | Stable row group such as `runtime-root`, `extension-package`, `execution-root`, or `governance-router`. | Derived from this plan, not from filesystem contents. |
| Parent directory | One of the four exact parent directories in this plan. | Must not include nested paths. |
| Top-level name | Immediate child basename only, redacted when required. | No slash, no parent path repetition, no nested path. |
| Name disposition | `recorded`, `redacted`, `deferred`, or `stopped`. | Describes how the name was handled, not what the child contains. |
| Name risk class | `normal`, `hidden`, `secret-like`, `private-state-like`, `cache-like`, `log-like`, `env-like`, or `unexpected`. | Derived from the name string only. |
| Notes | Short bounded note. | No file contents, command dumps, owner/group/inode, size, hash, mtime, child count, or nested names. |

Forbidden output fields:

- child count summaries
- recursive paths
- file type for children
- child mode
- child size
- child hash
- child mtime/ctime
- owner/group/inode/device details
- package metadata
- manifest contents
- README contents
- script names with command contents
- route/module contents
- command output dumps
- raw secret-like names

The future evidence should avoid a separate total count. Row count may be
implicit in the table, but no additional child-count metric should be recorded
unless a later plan explicitly authorizes count collection.

## Future Listing Limits

A later evidence step must enforce:

| Limit | Rule |
| --- | --- |
| Parent directories | Exactly the four parent directories in this plan. |
| Depth | Immediate top-level names only; no recursive listing. |
| Per-parent row cap | At most first `200` top-level names per parent directory after deterministic lexical ordering. |
| Name length cap | At most `160` characters per displayed name after redaction. |
| Name bytes | Treat unreadable or non-UTF-8 names as `UNREADABLE_NAME` and stop that name. |
| Redaction | Redact secret-like, env-like, credential-like, private-state-like, cache-like, and log-like names before writing evidence. |
| Symlink behavior | Do not follow symlinks; listing a top-level name does not authorize inspecting its target. |

If a parent directory appears to exceed the per-parent row cap, the future
evidence step must record `ROW_CAP_REACHED` for that parent and stop listing
further names for that parent without recursing.

## Red Lines

The future top-level name evidence step must stop or redact when these
conditions appear:

| Red line | Required handling |
| --- | --- |
| Plan hash or prior closeout/evidence hashes drift | Stop before collecting names. |
| Parent directory set differs from the four exact paths in this plan | Stop before collecting names. |
| A parent path is missing, not a directory, or becomes indirect | Stop for that parent and record only the drift class. |
| Listing would recurse below top level | Stop the expansion and record `RECURSION_NOT_AUTHORIZED`. |
| Listing would require file content reads | Stop and record `CONTENT_READ_NOT_AUTHORIZED`. |
| Listing would collect child type, mode, size, hash, owner, mtime, or child count | Stop and record `METADATA_EXPANSION_NOT_AUTHORIZED`. |
| A top-level name looks secret-like, env-like, credential-like, private-state-like, cache-like, or log-like | Do not record the raw name; record only redacted disposition and risk class. |
| A name contains path separators or cannot be represented as a basename | Stop that name and record `INVALID_BASENAME`. |
| A name is unreadable or unexpectedly encoded | Stop that name and record `UNREADABLE_NAME`. |
| A name indicates runtime cache, private local state, `.env`, secrets, credentials, databases, logs, or generated private artifacts | Redact or defer; do not inspect. |
| A governance-adjacent name appears under `governance/codex-router/` | Record name-only evidence at most; do not classify behavior or grant router acceptance. |
| Future evidence command would print raw command output beyond the planned table | Stop before writing evidence. |

## Future Preflight Required Before Any Name Listing

A later top-level name allowlist preflight must confirm:

| Check | Required result |
| --- | --- |
| This plan hash | Stable from plan creation. |
| Directory-boundary metadata evidence review closeout hash | Stable at `ac12010eed36f895c501db3980759f26ad13c7aac92f448f9c9f97e563d8b536`. |
| Directory-boundary metadata evidence hash | Stable at `2d979a408a513f001081235497bbcdb4f18a776b1b9304a85cf349e554555eae`. |
| Directory-boundary metadata evidence receipt hash | Stable at `69ae9ae80de22bcd1a8d4f10a0ee8972d93e8193ecf9b9af5a1d04e7c27a40c9`. |
| Future name evidence target | Absent before creation. |
| Future name evidence receipt target | Absent before creation. |
| Parent directory set | Exactly the four parent directories in this plan. |
| Command boundary | Name-only, max-depth-one listing; no stat, no child count, no content read, no recursion. |
| Redaction method | Secret-like and private-state-like names must be redacted before evidence is written. |

If any required result fails, top-level name evidence collection is not admitted.

## Future Outputs

If separately authorized after preflight, the next gate may create:

| Output | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-7-runtime-loader-top-level-name-allowlist-evidence-2026-06-28.md` | Redacted top-level name evidence for the four exact parent directories only. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-evidence-receipt-2026-06-28.md` | Receipt recording preflight, listing limits, redactions, deferred names, and boundary compliance. |

This plan does not authorize either output by itself.

## Stop Conditions

Stop before a future top-level name evidence step if:

- this plan changes unexpectedly
- any required prior input hash drifts
- future evidence or receipt targets already exist
- the parent directory set expands, shrinks, or changes
- evidence collection cannot enforce max-depth-one listing
- evidence collection cannot enforce row caps and redaction
- the action would collect child count, child metadata, recursive paths, or file
  content
- the action would follow symlinks
- the action would expose raw secret-like, env-like, credential-like, private
  state, cache, log, database, or generated private artifact names
- the action would execute runtime, loader, validator, package-manager, sync,
  deploy, network, or remote commands
- a requested interpretation tries to upgrade names into behavior acceptance

## Acceptance Boundary

This plan can only support a future static top-level name evidence gate.

It cannot grant:

- direct name-listing authorization without a separate preflight and user
  authorization
- child count authorization
- child metadata authorization
- directory content-read authorization
- file content-read authorization
- runtime behavior acceptance
- loader behavior acceptance
- extension execution acceptance
- governance router acceptance
- full consumer integration acceptance
- migration, rewrite, or normalization authorization

## Result

Top-level name allowlist planning is complete for four parent directories. The
next safe step is a separate formal preflight that confirms this plan hash,
prior input hashes, future output absence, parent set stability, and listing
command boundaries before any name collection occurs.

Marker:

```text
PHASE_7_RUNTIME_LOADER_TOP_LEVEL_NAME_ALLOWLIST_PLAN_CREATED_NO_CHILD_LISTING
```
