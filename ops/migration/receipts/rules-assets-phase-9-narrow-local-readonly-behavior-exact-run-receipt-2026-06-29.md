# Phase 9 Narrow Local Readonly Behavior Exact-Run Receipt - 2026-06-29

Status: completed.

Decision:
`PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_COMPLETED_PASS_WITH_LIMITS`.

This receipt records the completed narrow local readonly exact-run for selected
runtime-control and routing-engine tests. It grants only limited local behavior
evidence for these selected tests and does not grant loader, consumer, package
script, dependency, remote, or full runtime/router acceptance.

## Inputs Reviewed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-narrow-local-readonly-behavior-exact-run-authorization-plan-2026-06-29.md` | `647e7b4e0802c22a0496608a4f1677889d0c859d51fad000f29e04c68945390f` | stable |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-preflight-receipt-2026-06-29.md` | `2cd8b0000bf14dc2b215a77964e3764aa8d35e34616fa00c78a73a5688d0ae8b` | stable |
| `ops/migration/inventory/phase-9-narrow-local-readonly-behavior-exact-run-evidence-2026-06-29.md` | `c76ccb30cc10cf0a7885b3b9caf7b740121bee469870e8af8e0226c14b25437a` | stable |
| `governance/codex-router/tests/runtime-control.test.ts` | `2e08cbd8afd960dab83b38a8301abebb35c811a195376871db7f85dca462a93a` | stable after execution |
| `governance/codex-router/tests/routing-engine.test.ts` | `faa8ca1e49f9a9a62ec5f2b1014bb07165aefbda510347b4abfbac10c67a81fd` | stable after execution |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-receipt-2026-06-29.md` | absent before creation |

## Command Recorded

Working directory:

```text
/home/jenn/AGENTS_OS_Workspace/governance/codex-router
```

Command:

```text
./node_modules/.bin/tsx --test tests/runtime-control.test.ts tests/routing-engine.test.ts
```

## Execution Result

| Item | Result |
| --- | --- |
| Exit code | `0` |
| Tests | `5` |
| Pass | `5` |
| Fail | `0` |
| Cancelled | `0` |
| Skipped | `0` |
| Todo | `0` |
| TAP reported duration | `819.106512 ms` |
| Source file changes | none observed |
| `governance/codex-router` git status | clean |

## Accepted With Limits

| Area | Accepted result | Limit |
| --- | --- | --- |
| `runtime-control.test.ts` | PASS | Local selected unit behavior only. |
| `routing-engine.test.ts` | PASS | Local routing-engine behavior against local `routing-policy.yaml` only. |
| Runtime/router behavior evidence | collected with limits | Not full runtime/router acceptance. |
| Loader behavior | not evaluated | Still deferred. |
| Consumer integration | not evaluated | Still deferred. |
| Package scripts and broad `npm test` | not executed | Still deferred. |

## Not Granted

- loader behavior acceptance
- consumer integration acceptance
- governance router full acceptance
- broad runtime acceptance
- package script acceptance
- broad `npm test` acceptance
- build/typecheck acceptance
- dependency installability/security/freshness acceptance
- smoke/canary/workspace-write/telemetry acceptance
- network, remote, sync, deploy, branch, release, or operational acceptance
- source, manifest, lockfile, registry, runtime, router, loader, consumer,
  prompt, template, or env edits

## Next Gates

Recommended next options:

| Next gate | Reason |
| --- | --- |
| Three-way closeout for this exact-run | Confirm authorization plan, preflight receipt, evidence, and execution receipt align. |
| Loader behavior narrow plan | Loader behavior remains deferred. |
| Consumer integration planning | Should wait until at least one loader/router behavior gate is clearer. |
| Typecheck support gate | Useful support evidence, but not behavior acceptance. |

## Result

The Phase 9 narrow local readonly behavior exact-run completed successfully with
5 passing tests and 0 failures. The result is accepted only as limited local
runtime/router behavior evidence.

Marker:

```text
PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_COMPLETED_PASS_WITH_LIMITS
```
