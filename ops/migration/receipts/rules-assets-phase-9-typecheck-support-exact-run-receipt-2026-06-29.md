# Phase 9 Typecheck Support Exact-Run Receipt - 2026-06-29

Status: completed; PASS with limits.

Decision:
`PHASE_9_TYPECHECK_SUPPORT_EXACT_RUN_COMPLETED_PASS_WITH_LIMITS`.

This receipt records the result of the authorized Phase 9 typecheck support
exact-run. It accepts only limited local static TypeScript compile support
evidence.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-typecheck-support-exact-run-authorization-plan-2026-06-29.md` | `bf490cd0f33b4cc0761aab4e2ef22fb4efb7649c9e3a8c0086e6494371c93f43` | stable |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-preflight-receipt-2026-06-29.md` | `fd248747d71dbb04a99037bebdbb5bcbf3169d7f044946af87411733059ef02d` | stable |
| `ops/migration/inventory/phase-9-typecheck-support-exact-run-evidence-2026-06-29.md` | `f1a68180825dc1c42f2ba7e818a9a5ac008dcca42b9301a28c4deff3f862217c` | created |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable after execution |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | stable after execution |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status after execution: clean.

## Command Result

Command executed from `governance/codex-router`:

```text
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

Result:

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| Diagnostics output | empty |
| Codex tool wall time | approximately `9.2 s` |

## Acceptance Granted

Granted:

```text
LOCAL_STATIC_TYPESCRIPT_COMPILE_SUPPORT_EVIDENCE_COLLECTED_WITH_LIMITS
```

Meaning:

- the local direct `tsc --noEmit` command completed successfully
- no TypeScript diagnostics were emitted
- no tracked git change was observed in `governance/codex-router` after
  execution
- the result is static compile support evidence only

## Not Granted

This receipt does not grant:

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

## Deferred Gates

Still deferred:

- typecheck exact-run three-way closeout
- broader loader/host/provider behavior gates
- consumer/runtime integration gates
- broad package script and `npm test` gates
- smoke/canary/package-script gates

## Result

The Phase 9 typecheck support exact-run completed successfully and grants only
limited local static TypeScript compile support evidence.

Marker:

```text
PHASE_9_TYPECHECK_SUPPORT_EXACT_RUN_COMPLETED_PASS_WITH_LIMITS
```
