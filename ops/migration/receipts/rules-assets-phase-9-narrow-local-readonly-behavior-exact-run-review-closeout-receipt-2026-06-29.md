# Phase 9 Narrow Local Readonly Behavior Exact-Run Review Closeout Receipt - 2026-06-29

Status: closed.

Decision:
`PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_THREE_WAY_REVIEW_CONSISTENT_CLOSED`.

This receipt closes the three-way review for the Phase 9 narrow local readonly
behavior exact-run. It confirms that the authorization plan, preflight receipt,
execution evidence, and execution receipt are aligned. It does not expand the
accepted result beyond limited local runtime/router behavior evidence.

## Inputs Reviewed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-narrow-local-readonly-behavior-exact-run-authorization-plan-2026-06-29.md` | `647e7b4e0802c22a0496608a4f1677889d0c859d51fad000f29e04c68945390f` | stable |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-preflight-receipt-2026-06-29.md` | `2cd8b0000bf14dc2b215a77964e3764aa8d35e34616fa00c78a73a5688d0ae8b` | stable |
| `ops/migration/inventory/phase-9-narrow-local-readonly-behavior-exact-run-evidence-2026-06-29.md` | `c76ccb30cc10cf0a7885b3b9caf7b740121bee469870e8af8e0226c14b25437a` | stable |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-receipt-2026-06-29.md` | `b0585bf05051b84d0d02b81428c581bcd5a4ec7c616d27128e83b141d248fca7` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-review-closeout-receipt-2026-06-29.md` | absent before creation |

`governance/codex-router` git status: clean.

## Three-Way Review

| Source | Expected | Observed | Result |
| --- | --- | --- | --- |
| Authorization plan | Select exact local readonly command and stop before execution. | Command fixed to `./node_modules/.bin/tsx --test tests/runtime-control.test.ts tests/routing-engine.test.ts`. | aligned |
| Preflight receipt | Confirm hashes, local `tsx`, risk scan, target absence, and no execution. | Preflight PASS; execution still blocked at that point. | aligned |
| Execution evidence | Record command, exit code, TAP summary, file stability, and limits. | Exit code 0; 5 pass; 0 fail; source hashes unchanged. | aligned |
| Execution receipt | Accept only limited local runtime/router behavior evidence. | Receipt limits remain narrow and carry loader/consumer/package-script gates forward. | aligned |

## Accepted With Limits

| Area | Accepted result | Limit |
| --- | --- | --- |
| `runtime-control.test.ts` | PASS | Selected local unit behavior only. |
| `routing-engine.test.ts` | PASS | Selected local routing-engine behavior against local `routing-policy.yaml` only. |
| Runtime/router evidence | accepted with limits | Not full runtime/router acceptance. |
| Loader behavior | deferred | Not evaluated. |
| Consumer integration | deferred | Not evaluated. |
| Broad package/test/script behavior | deferred | `npm test`, package scripts, build, typecheck, smoke, and canary were not executed. |

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

## Result

The Phase 9 narrow local readonly behavior exact-run is reviewed and closed as
consistent. The strongest accepted result remains limited local runtime/router
behavior evidence with loader and consumer gates deferred.

Marker:

```text
PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_THREE_WAY_REVIEW_CONSISTENT_CLOSED
```
