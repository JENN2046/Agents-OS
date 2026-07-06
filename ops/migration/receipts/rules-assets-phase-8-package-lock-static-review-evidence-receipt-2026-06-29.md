# Phase 8 Package Lock Static Review Evidence Receipt

Date: 2026-06-29

Status: evidence receipt created.

Decision: `PACKAGE_LOCK_STATIC_REVIEW_EVIDENCE_RECEIVED_NO_WARN_NO_FAIL`.

This receipt records the static lockfile review evidence for
`governance/codex-router/package-lock.json`. It accepts the evidence as static
parsed-object lockfile evidence only. It does not grant dependency, npm,
runtime, router, loader, or consumer acceptance.

## Inputs Reviewed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-package-lock-static-review-plan-2026-06-29.md` | `4867d18e7a41eba713c9ce2039a35c51108f99f9e1e51f09d19e822706f697b0` | stable |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-preflight-receipt-2026-06-29.md` | `c9586cc3704272332d6c4661ff5b55a9bb9a5be161beee02ea1da11e476bde36` | stable |
| `ops/migration/inventory/phase-8-package-lock-static-review-evidence-2026-06-29.md` | `06b0fa54d49f193cbeb711e5aa3898634529dd4e08cc11fc28b0746cdcc67c00` | stable |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-evidence-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-closeout-receipt-2026-06-29.md` | absent |

## Evidence Received

| Evidence item | Result |
| --- | --- |
| Manifest JSON parse | PASS |
| Lockfile JSON parse | PASS |
| Static rule count | 6 |
| PASS count | 6 |
| WARN count | 0 |
| FAIL count | 0 |
| Package entry count | 37 |
| Strict token shape count | 0 |

## Limits Carried Forward

- This receipt accepts evidence only as static lockfile evidence.
- It does not authorize edits to `package.json` or `package-lock.json`.
- It does not authorize dependency install, update, prune, audit, or registry
  access.
- It does not grant dependency vulnerability, freshness, or supply-chain
  acceptance.
- It does not grant router/runtime/loader behavior acceptance.
- It does not grant consumer integration acceptance.
- It does not authorize package scripts, validators, tests, builds, typechecks,
  canaries, sync, deploy, network, or remote actions.

## Result

Package lock static review evidence is received with no WARN and no FAIL
results. The next safe step is a closeout receipt for this static lockfile
review track.

Marker:

```text
PHASE_8_PACKAGE_LOCK_STATIC_REVIEW_EVIDENCE_RECEIPT_CREATED_NO_WARN_NO_FAIL_NO_EXECUTION
```
