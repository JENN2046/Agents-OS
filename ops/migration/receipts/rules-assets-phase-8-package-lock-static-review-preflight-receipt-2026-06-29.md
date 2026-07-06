# Phase 8 Package Lock Static Review Preflight Receipt

Date: 2026-06-29

Status: PASS.

Decision: `PACKAGE_LOCK_STATIC_REVIEW_PREFLIGHT_PASS_STATIC_EVIDENCE_NEXT`.

This receipt confirms that the Phase 8 static lockfile review may proceed for
`governance/codex-router/package-lock.json`, with
`governance/codex-router/package.json` admitted only for manifest/lockfile
alignment. No npm commands, package scripts, tests, builds, typechecks,
validators, installs, sync, deploy, network, or remote actions were executed.

## Inputs Confirmed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-package-lock-static-review-plan-2026-06-29.md` | `4867d18e7a41eba713c9ce2039a35c51108f99f9e1e51f09d19e822706f697b0` | stable |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-closeout-receipt-2026-06-28.md` | `aef1ce3fb26e5ef983a0d5a97b82eaef10d267d3a81ba76ac78a77010057dfeb` | stable |
| `ops/migration/receipts/rules-assets-phase-8-runtime-loader-behavior-validation-preflight-receipt-2026-06-28.md` | `ed60695d396ecc5b9b9d4c14e7f87dc8611fcdfc44c817f3d6424dbaeab85f99` | stable |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | stable |

## Target Absence Confirmed Before Creation

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-8-package-lock-static-review-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-evidence-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-closeout-receipt-2026-06-29.md` | absent |

## File Boundary Check

| Path | Type | Mode | Size | Lines | Result |
| --- | --- | --- | --- | --- | --- |
| `governance/codex-router/package.json` | regular file | `644` | `1517` bytes | `35` | within manifest boundary |
| `governance/codex-router/package-lock.json` | regular file | `644` | `18677` bytes | `618` | within `64 KiB` / `1000` line cap |

## Parser Availability

| Parser | Result |
| --- | --- |
| Local Node JSON parser | `LOCAL_JSON_PARSE_AVAILABLE_BOTH_FILES_PARSE_PASS` |

## Boundary Check

| Boundary | Result |
| --- | --- |
| Static parse of exact manifest and lockfile | allowed for next evidence step |
| Manifest/lockfile dependency-key alignment | allowed for next evidence step |
| npm install/ci/audit/ls/test or package scripts | not performed; not authorized |
| dependency install/update/prune/rewrite | not performed; not authorized |
| router/runtime/loader behavior | not performed; not authorized |
| sync, deploy, network, remote actions | not performed; not authorized |

## Result

Preflight passes for static package-lock review evidence collection.

Marker:

```text
PHASE_8_PACKAGE_LOCK_STATIC_REVIEW_PREFLIGHT_PASS_STATIC_ONLY_NO_EXECUTION
```
