# Phase 8 Package Lock Static Review Closeout Receipt

Date: 2026-06-29

Status: closed.

Decision: `PACKAGE_LOCK_STATIC_REVIEW_CLOSED_NO_WARN_NO_FAIL`.

This receipt closes the Phase 8 static lockfile review track for
`governance/codex-router/package-lock.json`. It accepts only static
manifest/lockfile evidence. It does not grant dependency installability,
dependency security, npm registry, router behavior, runtime, loader, or consumer
integration acceptance.

## Inputs Reviewed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-package-lock-static-review-plan-2026-06-29.md` | `4867d18e7a41eba713c9ce2039a35c51108f99f9e1e51f09d19e822706f697b0` | stable |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-preflight-receipt-2026-06-29.md` | `c9586cc3704272332d6c4661ff5b55a9bb9a5be161beee02ea1da11e476bde36` | stable |
| `ops/migration/inventory/phase-8-package-lock-static-review-evidence-2026-06-29.md` | `06b0fa54d49f193cbeb711e5aa3898634529dd4e08cc11fc28b0746cdcc67c00` | stable |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-evidence-receipt-2026-06-29.md` | `dd1dbd34ebb5d84c03efcc474508e170ae76ddf7a7e64cb7fc24ea9f96695bc7` | stable |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-closeout-receipt-2026-06-29.md` | absent before creation |

## Three-Way Review

| Source | Expected | Observed | Result |
| --- | --- | --- | --- |
| Static review plan | Exact manifest + lockfile parse, static alignment, no npm execution | Evidence parsed only the two exact files and did not execute npm or scripts | aligned |
| Preflight receipt | Confirm hashes, target absence, file caps, parser availability, and no-execution boundary | All recorded before evidence collection | aligned |
| Evidence + evidence receipt | Record rule counts and limits | 6 PASS, 0 WARN, 0 FAIL; limits carried forward | aligned |

## Accepted With Limits

| Topic | Accepted result | Limit |
| --- | --- | --- |
| Manifest JSON parse | PASS | Static parse only. |
| Lockfile JSON parse | PASS | Static parse only. |
| Manifest/lockfile dependency-key alignment | PASS | No installability or registry acceptance. |
| Package entry static shape | PASS | No package code execution. |
| Integrity/resolved redacted static check | PASS | Not a vulnerability, freshness, or supply-chain audit. |
| Execution guard | PASS | No npm/script/runtime behavior acceptance. |

## Deferred Gates

- npm installability validation.
- dependency vulnerability or freshness review.
- npm registry trust or network-based audit.
- package script, validator, build, typecheck, test, canary, sync, deploy,
  network, or remote execution.
- Governance router behavior validation.
- Runtime behavior validation.
- Loader behavior validation.
- Consumer integration validation.
- Model/source authority validation and rollout/version domain validation.
- Revised-cap or section-scoped Markdown gates for `AGENTS.md`,
  `PROJECT_CONTINUE_ANCHOR.md`, and `README.md`.

## Not Granted

- edits to `package.json` or `package-lock.json`
- dependency install, update, prune, audit, or registry access
- package script execution
- dependency security acceptance
- dependency freshness acceptance
- router behavior acceptance
- runtime behavior acceptance
- loader behavior acceptance
- consumer integration acceptance
- migration, rewrite, normalization, or lockfile edit authorization

## Result

The Phase 8 package-lock static review track is closed with no WARN and no FAIL
results. The strongest accepted state is static manifest/lockfile evidence
accepted, while dependency runtime behavior, npm registry behavior, router,
runtime, loader, and consumer validation remain deferred.

Marker:

```text
PHASE_8_PACKAGE_LOCK_STATIC_REVIEW_CLOSED_NO_WARN_NO_FAIL_NO_EXECUTION
```
