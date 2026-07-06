# Phase 8 Package Lock Static Review Evidence

Date: 2026-06-29

Status: evidence collected.

Scope: static review of `governance/codex-router/package-lock.json` with
`governance/codex-router/package.json` used only for manifest/lockfile
alignment.

No npm commands, package scripts, dependency installation, validators, tests,
builds, typechecks, router code, runtime, loader, sync, deploy, network, or
remote actions were executed.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-package-lock-static-review-plan-2026-06-29.md` | `4867d18e7a41eba713c9ce2039a35c51108f99f9e1e51f09d19e822706f697b0` | stable |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-preflight-receipt-2026-06-29.md` | pending at collection start | created before this evidence |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | parsed |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | parsed and reviewed |

## Evaluation Method

| Item | Result |
| --- | --- |
| Parser | local Node JSON parser |
| Manifest parse status | PASS |
| Lockfile parse status | PASS |
| Evaluation type | static parsed-object review |
| Rule count | 6 |
| Output policy | redacted; registry URLs not printed; token-like values not disclosed |

## Result Counts

| Result | Count |
| --- | --- |
| PASS | 6 |
| WARN | 0 |
| FAIL | 0 |
| DEFERRED | 0 rule-level results |
| NOT_EVALUATED | 0 rule-level results |

## Rule Results

| Rule | Result | Evidence summary |
| --- | --- | --- |
| `L1_JSON_PARSE` | PASS | Manifest and lockfile parse as JSON. |
| `L2_LOCKFILE_SCHEMA` | PASS | Lockfile has expected top-level static structure, `lockfileVersion` 3, and 37 package entries. |
| `L3_MANIFEST_LOCK_ALIGNMENT` | PASS | Manifest dependency/devDependency keys and name/version align with the lockfile root package. |
| `L4_PACKAGE_ENTRY_STATIC_SHAPE` | PASS | Package entries satisfy static map/scalar shape checks. |
| `L5_INTEGRITY_AND_RESOLVED_REDACTION` | PASS | Package entries include integrity/resolved metadata where expected; strict token shapes are 0. |
| `L6_SCRIPT_EXECUTION_GUARD` | PASS | Evidence remains static-only and does not claim npm/script/dependency/runtime acceptance. |

## Manifest/Lock Alignment Evidence

| Manifest field | Manifest keys | Lockfile root keys | Result |
| --- | --- | --- | --- |
| `dependencies` | `yaml`, `zod` | `yaml`, `zod` | PASS |
| `devDependencies` | `@types/node`, `tsx`, `typescript` | `@types/node`, `tsx`, `typescript` | PASS |

Name/version alignment result: PASS.

## Static Metadata Evidence

| Item | Result |
| --- | --- |
| Package entry count | 37 |
| Missing required static package-entry shape issues | 0 |
| Missing integrity/resolved metadata warnings | 0 |
| Strict `sk-...` token shape count | 0 |
| Strict `Bearer ...` token shape count | 0 |
| Strict registry auth token shape count | 0 |
| Distinct resolved registry hosts | 1 redacted host class recorded: `registry.npmmirror.com` |

## Not Evaluated

- dependency vulnerability status
- dependency freshness or upgrade availability
- npm registry trust
- package installability
- runtime behavior
- router behavior
- loader behavior
- consumer integration
- package scripts, validators, tests, builds, typechecks, canaries, sync, deploy,
  network, or remote actions

## Result

Static package-lock review completed with `0` WARN and `0` FAIL results. This
does not grant dependency, npm, runtime, router, loader, or consumer acceptance.

Marker:

```text
PHASE_8_PACKAGE_LOCK_STATIC_REVIEW_EVIDENCE_COLLECTED_STATIC_ONLY_NO_EXECUTION
```
