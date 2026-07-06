# Phase 7 Runtime/Loader Top-Level Name Allowlist Evidence Receipt

Date: 2026-06-28

Status: completed.

This receipt records the authorized top-level name allowlist evidence collection
for four parent directories.

## Authorization

User request:

> 授权 top-level name allowlist evidence collection，只做四个父目录的 max-depth-one 名称采集，红acted 输出，不做 child count、不 stat 子项。

## Created Files

| File | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-7-runtime-loader-top-level-name-allowlist-evidence-2026-06-28.md` | Redacted max-depth-one top-level name evidence for four authorized parent directories. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-evidence-receipt-2026-06-28.md` | This receipt. |

Both targets were absent before creation.

## Inputs Used

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-7-runtime-loader-top-level-name-allowlist-plan-2026-06-28.md` | `1500c8ba152c7b002aba924b4fddabc4168c8dd2e6e67ed744dc88ca5b158f82` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-top-level-name-allowlist-preflight-receipt-2026-06-28.md` | `489be996ddbe543a619a0507090595f0842e93d2d39b17aca61167e32a80575c` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-review-closeout-receipt-2026-06-28.md` | `ac12010eed36f895c501db3980759f26ad13c7aac92f448f9c9f97e563d8b536` | stable |
| `ops/migration/inventory/phase-7-runtime-loader-directory-boundary-metadata-evidence-2026-06-28.md` | `2d979a408a513f001081235497bbcdb4f18a776b1b9304a85cf349e554555eae` | stable |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-directory-boundary-metadata-evidence-receipt-2026-06-28.md` | `69ae9ae80de22bcd1a8d4f10a0ee8972d93e8193ecf9b9af5a1d04e7c27a40c9` | stable |

## Boundary Compliance

| Boundary | Result |
| --- | --- |
| Four authorized parent directories only | PASS |
| Max-depth-one basenames only | PASS |
| Redacted output policy applied before evidence write | PASS |
| Per-parent row cap enforced | PASS |
| No child count collected | PASS |
| No child stat performed by evidence command | PASS |
| No child type/mode/size/hash/owner/timestamp collected | PASS |
| No recursive path listing | PASS |
| No file content read | PASS |
| No symlink target followed | PASS |
| No validator/script/runtime/loader execution | PASS |
| No remote/sync/deploy/network command | PASS |

## Evidence Summary

- `runtime/` emitted top-level name evidence within the authorized output shape.
- `extensions/vcp-toolbox-jenn/` emitted no top-level name rows within the
  authorized output shape; this is not a child-count authorization.
- `execution/` emitted top-level name evidence within the authorized output
  shape.
- `governance/codex-router/` emitted top-level name evidence within the
  authorized output shape, including hidden-name risk classification.
- No redaction was required by the configured name-risk patterns.
- No row cap was reached.

## Not Granted

- child count authorization
- child stat authorization
- child metadata authorization
- directory content-read authorization
- file content-read authorization
- runtime behavior acceptance
- loader behavior acceptance
- extension execution acceptance
- governance router acceptance
- full consumer integration acceptance
- migration or normalization authorization

## Not Verified

- Child entry metadata was not collected.
- Nested paths were not listed.
- File contents were not opened.
- Symlink targets were not followed.
- Runtime, loader, extension, execution, governance-router, and consumer behavior
  were not inspected or executed.

## Result

Top-level name allowlist evidence collection is complete for the four authorized
parent directories. The result is redacted static name evidence only.

Marker:

```text
PHASE_7_RUNTIME_LOADER_TOP_LEVEL_NAME_ALLOWLIST_EVIDENCE_RECEIPT_CREATED_REDACTED_MAX_DEPTH_ONE_NO_CHILD_STAT
```
