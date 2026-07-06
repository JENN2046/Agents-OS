# Phase 10 Consumer Runtime Integration Readiness Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans the first Phase 10 consumer/runtime integration readiness
gate. It chooses a narrow local formal read-only CLI integration readiness test
surface before broader host/provider/consumer behavior gates.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-10-scope-plan-2026-06-29.md` | `71713e6b1f5f43475d48a77698fd26dca79ae0bee925ca81191fbb5c3f59509f` | Phase 10 scope authority. |
| `ops/migration/receipts/rules-assets-phase-9-closeout-receipt-2026-06-29.md` | `bb42ff255eb132ae38b835196b4a52422ec1e4406d5bd102629a8ef6d42fc348` | Phase 9 limited closeout authority. |
| `governance/codex-router/tests/formal-readonly-cli-integration-readiness.test.ts` | `967440de0f7f37dac57cb1e8e616beeeb8a50f7fe0507cc7bbe7b39eab2f77e7` | Selected exact-run test file. |
| `governance/codex-router/scripts/run-formal-readonly-cli-integration-readiness.ts` | `f16eff5de444d877b62136e9c3659e5eec2c86f682fa4d0ac08a44f1b8b82bdb` | Readiness review implementation under test. |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | Provider guard source read by selected test. |
| `governance/codex-router/docs/evidence/codex-cli-real-readonly-dispatch-acceptance.json` | `d3326cffa8ea1278f7658dce502763859ad649f7b81c9204445f9d67b2a30f54` | Local evidence input. |
| `governance/codex-router/docs/evidence/codex-cli-real-readonly-smoke.json` | `f62b954cfd960a50a3375aeae705bf2c8861c8026f1ef77c1fd3a9c2c754e90c` | Local evidence input. |
| `governance/codex-router/docs/evidence/codex-cli-real-readonly-smoke-authorization-acceptance.json` | `6a67d2ec8ef32aaa015bb5853aa9d056d10d5f757acb69b2d8b2227fa0a0b82e` | Local evidence input. |
| `governance/codex-router/docs/governance/PR_13B_REAL_READONLY_DISPATCH_CONTROL_LOCAL_CLOSEOUT.md` | `0b49df7e14fb3bbbcd47792e4ad794a7af65aaa63d6d5a713b987c81a17824c9` | Local governance evidence input. |
| `governance/codex-router/docs/governance/PR_14A_FORMAL_READONLY_CLI_INTEGRATION_PREFLIGHT.md` | `4cf5eb1a92e3f86961989de0f1a6e98c37e143e5403114c9e6cefa92af612929` | Local governance evidence input. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-10-consumer-runtime-integration-readiness-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-10-consumer-runtime-integration-readiness-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` status at plan creation: clean.

Current `governance/codex-router` HEAD:

```text
88b84c66e7c815ca5797507c9e957cf5ad38eba2
```

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test tests/formal-readonly-cli-integration-readiness.test.ts
```

Future working directory:

```text
governance/codex-router
```

Why this candidate:

- It is directly about formal read-only CLI integration readiness.
- It reads local evidence and provider source only.
- It asserts real Codex CLI calls, provider execute calls, and workspace-write
  execute calls remain `0`.
- Its writer test persists sanitized JSON into a `mkdtemp(tmpdir())` path, not
  repository-root evidence.
- It avoids `npm run`, real smoke, canary, network, remote, deploy, and actual
  CLI execution.

## Future Preflight Requirements

Before execution, create a preflight receipt confirming:

- this plan hash is stable
- Phase 10 scope plan hash is stable
- Phase 9 closeout receipt hash is stable
- selected test, implementation, provider source, and local evidence input
  hashes are stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the exact command matches this plan
- selected test file still uses tempdir for writer persistence
- selected test file still avoids real CLI execution, network, remote, npm
  scripts, dependency install/audit, repository-root writes, smoke, and canary
- no command has been executed yet

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
FORMAL_READONLY_CLI_INTEGRATION_READINESS_LOCAL_EVIDENCE_PASS_WITH_LIMITS
```

It cannot by itself grant:

- formal integration execution authorization
- real Codex CLI execution acceptance
- consumer/runtime full acceptance
- host/provider/live-host full acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

Phase 10 consumer/runtime integration readiness is planned but not executed by
this plan. The next safe step is a PASS/FAIL preflight receipt for the exact
command above.

Marker:

```text
PHASE_10_CONSUMER_RUNTIME_INTEGRATION_READINESS_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
