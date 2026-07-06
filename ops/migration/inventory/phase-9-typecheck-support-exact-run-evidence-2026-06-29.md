# Phase 9 Typecheck Support Exact-Run Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the exact local TypeScript compile check authorized by the
Phase 9 typecheck support exact-run authorization plan and preflight receipt.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-typecheck-support-exact-run-authorization-plan-2026-06-29.md` | `bf490cd0f33b4cc0761aab4e2ef22fb4efb7649c9e3a8c0086e6494371c93f43` | stable |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-preflight-receipt-2026-06-29.md` | `fd248747d71dbb04a99037bebdbb5bcbf3169d7f044946af87411733059ef02d` | stable |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable after execution |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | stable after execution |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-9-typecheck-support-exact-run-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status after execution: clean.

Note: `governance/codex-router/dist/` exists. This evidence does not evaluate
whether that directory pre-existed. The executed command used `--noEmit`, and no
tracked git change was observed after execution.

## Command Executed

Working directory:

```text
governance/codex-router
```

Command:

```text
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| Diagnostics output | empty |
| TypeScript compile result | PASS |
| Codex tool wall time | approximately `9.2 s` |

## Evidence Boundary

This run confirms only:

- the direct local TypeScript compile check completed with exit code `0`
- no TypeScript diagnostics were printed
- `package.json`, `package-lock.json`, and `tsconfig.json` hashes remained
  stable after execution
- `governance/codex-router` git status remained clean after execution

This run does not confirm:

- runtime behavior acceptance
- router behavior acceptance
- loader behavior acceptance
- consumer integration acceptance
- host/provider/live-host acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, telemetry, sync, deploy, or workspace-write acceptance
- generated artifact cleanliness beyond the observed clean git status

## Result

The Phase 9 typecheck support exact-run completed with exit code `0` and no
diagnostics.

Marker:

```text
PHASE_9_TYPECHECK_SUPPORT_EXACT_RUN_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
