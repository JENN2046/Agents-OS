# Phase 7 Runtime/Loader Top-Level Name Allowlist Evidence

Date: 2026-06-28

Status: collected.

This evidence records redacted max-depth-one top-level name evidence for four
authorized parent directories. The collection was limited to immediate child
basenames only.

No child entries were stat'ed. No child count was collected. No recursive paths
were collected. No files were opened. No runtime, loader, validator, script,
package-manager, sync, deploy, network, or remote command was executed.

## Authorization

User request:

> 授权 top-level name allowlist evidence collection，只做四个父目录的 max-depth-one 名称采集，红acted 输出，不做 child count、不 stat 子项。

Allowed in this step:

- collect max-depth-one top-level basenames under four authorized parent
  directories
- redact secret-like, env-like, credential-like, private-state-like, cache-like,
  log-like, database-like, or generated-private-artifact-like names before
  writing evidence
- create this evidence file and a matching receipt

Not allowed in this step:

- collect child counts
- stat child entries
- collect child type, mode, size, hash, owner, group, inode, mtime, or ctime
- collect recursive paths
- read files inside candidate parent directories
- follow symlinks
- execute validators, runtime, loaders, scripts, package managers, sync, deploy,
  network, or remote commands
- grant runtime behavior, loader behavior, extension execution, governance router,
  or full consumer integration acceptance

## Input Stability

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-top-level-name-allowlist-plan-2026-06-28.md` | `1500c8ba152c7b002aba924b4fddabc4168c8dd2e6e67ed744dc88ca5b158f82` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-preflight-receipt-2026-06-28.md` | `489be996ddbe543a619a0507090595f0842e93d2d39b17aca61167e32a80575c` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-review-closeout-receipt-2026-06-28.md` | `ac12010eed36f895c501db3980759f26ad13c7aac92f448f9c9f97e563d8b536` | stable |
| `ops/migration/inventory/phase-7-runtime-loader-directory-boundary-metadata-evidence-2026-06-28.md` | `2d979a408a513f001081235497bbcdb4f18a776b1b9304a85cf349e554555eae` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-receipt-2026-06-28.md` | `69ae9ae80de22bcd1a8d4f10a0ee8972d93e8193ecf9b9af5a1d04e7c27a40c9` | stable |

## Evidence Boundary

| Boundary | Result |
| --- | --- |
| Four authorized parent directories only | PASS |
| Max-depth-one basenames only | PASS |
| Deterministic lexical ordering | PASS |
| Per-parent row cap enforced at first `200` names | PASS |
| Raw secret-like/env-like/private-state-like/cache-like/log-like/database-like names redacted before writing evidence | PASS |
| No child count collected | PASS |
| No child stat performed by evidence command | PASS |
| No recursive paths collected | PASS |
| No file content read | PASS |
| No symlink target followed | PASS |
| No runtime/loader/validator/script execution | PASS |

## Parent Listing Status

| Parent directory | Status |
| --- | --- |
| `runtime/` | Top-level name rows emitted; row cap not reached. |
| `extensions/vcp-toolbox-jenn/` | No top-level name rows emitted; row cap not reached. This is not a child-count authorization. |
| `execution/` | Top-level name rows emitted; row cap not reached. |
| `governance/codex-router/` | Top-level name rows emitted; row cap not reached. |

## Redacted Top-Level Name Evidence

| Candidate ID | Parent directory | Top-level name | Name disposition | Name risk class | Notes |
| --- | --- | --- | --- | --- | --- |
| `runtime-root` | `runtime/` | `README.md` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `execution-root` | `execution/` | `bridges` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `execution-root` | `execution/` | `harness` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `execution-root` | `execution/` | `providers` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `execution-root` | `execution/` | `README.md` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `execution-root` | `execution/` | `workers` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.agent_board` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.agents` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.codex` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.git` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.github` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.gitignore` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.test-checkpoint-ledger` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.test-delegation-store-missing` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.test-exec-observation` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `.test-task-graph-store-missing` | `recorded` | `hidden` | Hidden top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `AGENTS.md` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `dist` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `docs` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `node_modules` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `package-lock.json` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `package.json` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `packages` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `PROJECT_CONTINUE_ANCHOR.md` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `README.AGENTS_OS.md` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `README.md` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `routing-policy.yaml` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `scripts` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `tests` | `recorded` | `normal` | Top-level name only; content not inspected. |
| `governance-router` | `governance/codex-router/` | `tsconfig.json` | `recorded` | `normal` | Top-level name only; content not inspected. |

No redaction was required by the configured name-risk patterns.

## Evidence Interpretation

| Parent directory | Interpretation |
| --- | --- |
| `runtime/` | Name evidence shows only the top-level README marker within the authorized output shape. This does not prove runtime implementation layout. |
| `extensions/vcp-toolbox-jenn/` | No name rows were emitted within the authorized output shape. This does not prove absence of future extension assets beyond this specific listing moment. |
| `execution/` | Name evidence shows top-level execution-area labels for bridges, harness, providers, workers, and README. This supports later planning, not execution acceptance. |
| `governance/codex-router/` | Name evidence shows a governance-adjacent project-like top-level surface, including hidden control names, package files, docs, scripts, tests, and routing policy. This supports governance-sensitive planning only, not router acceptance. |

## Not Verified

- Child counts were not collected.
- Child entries were not stat'ed.
- Child types, modes, sizes, hashes, owners, and timestamps were not collected.
- Nested paths were not listed.
- File contents were not read.
- Symlink targets were not followed.
- Runtime, loader, extension, execution, governance-router, and consumer behavior
  were not inspected or executed.
- Full consumer integration was not verified.

## Result

Top-level name allowlist evidence was collected for the four authorized parent
directories inside the configured boundaries. The result is static name evidence
only and does not authorize content reads, child metadata collection, execution,
or runtime/loader acceptance.

Marker:

```text
PHASE_7_RUNTIME_LOADER_TOP_LEVEL_NAME_ALLOWLIST_EVIDENCE_COLLECTED_REDACTED_MAX_DEPTH_ONE_NO_CHILD_STAT
```
