# Phase 8 Package Lock Static Review Plan

Date: 2026-06-29

Status: plan only.

This document plans a static lockfile review gate for
`governance/codex-router/package-lock.json`. It may compare the lockfile to the
same package's `package.json` manifest, but it must not install dependencies,
run npm scripts, execute tests, run builds, run typechecks, contact registries,
or perform network/remote actions.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-closeout-receipt-2026-06-28.md` | `aef1ce3fb26e5ef983a0d5a97b82eaef10d267d3a81ba76ac78a77010057dfeb` | Confirms the YAML semantic track closed with no static FAIL results and behavior gates deferred. |
| `ops/migration/receipts/rules-assets-phase-8-runtime-loader-behavior-validation-preflight-receipt-2026-06-28.md` | `ed60695d396ecc5b9b9d4c14e7f87dc8611fcdfc44c817f3d6424dbaeab85f99` | Confirms behavior validation remains stopped at an execution gate. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Manifest used only for static dependency alignment. |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | Exact lockfile to review. |

## Current File Metadata

| Path | Type | Mode | Size | Lines |
| --- | --- | --- | --- | --- |
| `governance/codex-router/package.json` | regular file | `644` | `1517` bytes | `35` |
| `governance/codex-router/package-lock.json` | regular file | `644` | `18677` bytes | `618` |

## Future Targets

| Future target | Intended purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-preflight-receipt-2026-06-29.md` | Confirm input hashes, target absence, file caps, and parser boundary. |
| `ops/migration/inventory/phase-8-package-lock-static-review-evidence-2026-06-29.md` | Record static lockfile parse and manifest alignment evidence. |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-evidence-receipt-2026-06-29.md` | Record evidence counts, warnings, and limits. |
| `ops/migration/receipts/rules-assets-phase-8-package-lock-static-review-closeout-receipt-2026-06-29.md` | Close the static lockfile review track without dependency/runtime acceptance. |

## Review Boundary

The future evidence step may:

- parse `package-lock.json` as JSON
- parse `package.json` as JSON
- inspect top-level lockfile fields and root package metadata
- compare manifest dependency keys to lockfile root dependency keys
- count package entries and dependency classes
- check that package entries have static integrity/resolved/version fields when
  present and applicable
- redact registry URLs or token-like values in output

The future evidence step must not:

- run `npm install`, `npm ci`, `npm audit`, `npm ls`, `npm test`, or any npm
  script
- install, update, prune, normalize, or rewrite dependencies
- contact npm registries or any network service
- execute package code
- evaluate runtime, router, loader, or consumer behavior
- modify `package.json`, `package-lock.json`, `node_modules`, or any lockfile

## Rule Classes

| Rule class | Purpose | Planned result level |
| --- | --- | --- |
| `L1_JSON_PARSE` | Confirm manifest and lockfile parse as JSON. | FAIL on parse error. |
| `L2_LOCKFILE_SCHEMA` | Confirm lockfile has expected top-level lockfile structure. | FAIL on missing/wrong type for required static fields. |
| `L3_MANIFEST_LOCK_ALIGNMENT` | Confirm root lockfile dependency keys align with manifest dependency/devDependency keys. | FAIL on missing manifest dependency in root lockfile; WARN on extra root lockfile dependency if explainable only by lockfile internals. |
| `L4_PACKAGE_ENTRY_STATIC_SHAPE` | Confirm package entries are maps and important scalar fields have expected static types when present. | FAIL on wrong required type; WARN on optional missing metadata. |
| `L5_INTEGRITY_AND_RESOLVED_REDACTION` | Check whether package entries contain static integrity/resolved metadata without disclosing sensitive URL-like values. | WARN on missing integrity/resolved metadata; FAIL on strict live-secret token shapes. |
| `L6_SCRIPT_EXECUTION_GUARD` | Confirm evidence wording does not imply package scripts or dependency behavior were executed. | FAIL if evidence claims install/runtime/test/build acceptance. |

## Future Preflight Requirements

The next preflight must confirm:

- this plan hash
- all input hashes are stable
- all future targets are absent
- `package.json` and `package-lock.json` remain regular files with mode `644`
- `package-lock.json` remains under `64 KiB` and `1000` lines
- local JSON parsing is available
- static review will not execute npm, package scripts, dependency code,
  validators, tests, builds, typechecks, router, runtime, loader, sync, deploy,
  network, or remote actions

## Stop Conditions

Stop if:

- any input hash drifts
- any future target already exists
- either JSON file fails to parse
- `package-lock.json` exceeds the admitted cap
- evidence collection would require reading outside the two exact files
- evidence collection would require executing npm, package code, package scripts,
  validators, tests, builds, typechecks, sync, deploy, network, or remote actions
- evidence would disclose token-like registry credentials or secret-like scalar
  values

## Acceptance Boundary

This plan can support only static lockfile evidence. It cannot grant:

- dependency install/update/prune authorization
- dependency vulnerability or freshness acceptance
- npm registry acceptance
- package script execution
- runtime behavior acceptance
- router behavior acceptance
- loader behavior acceptance
- consumer integration acceptance
- migration, rewrite, normalization, or lockfile edit authorization

## Result

Package lock static review planning is complete. The next safe step is a
preflight receipt that confirms hashes, target absence, file caps, parser
availability, and no-execution boundaries before collecting evidence.

Marker:

```text
PHASE_8_PACKAGE_LOCK_STATIC_REVIEW_PLAN_CREATED_NO_EXECUTION
```
