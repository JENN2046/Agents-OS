# Phase 10 Host-Dispatcher / Provider Behavior Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans the Phase 10 host-dispatcher/provider broader behavior gate.
It selects a first narrow named-test subset from `host-dispatcher.test.ts`
instead of running broad host/provider suites.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-10-scope-plan-2026-06-29.md` | `71713e6b1f5f43475d48a77698fd26dca79ae0bee925ca81191fbb5c3f59509f` | Phase 10 scope authority. |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-review-closeout-receipt-2026-06-29.md` | `69ea0a336072ef38f23457cbb9e251429cc8a6a337b8b283a9ea4887a1e4bd88` | Prior Phase 10 readiness closeout. |
| `ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-review-closeout-receipt-2026-06-29.md` | `7e82253bcd9ee9644f10ff2c319af5f3a4225c121da94f85323127c69fdb260d` | Prior Phase 10 local MCP runtime closeout. |
| `governance/codex-router/tests/host-dispatcher.test.ts` | `ccde8afb72c51aafe0dce7feaacc19aa0baef0814d3f612adb9d95b02f79003f` | Selected test file. |
| `governance/codex-router/packages/host-dispatcher/src/index.ts` | `cd6bbe27b19637eee7473617bba4d78ed72dd824466ef8a2294d9748505ef971` | Host dispatcher implementation. |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | Codex CLI provider implementation. |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | Provider permit/core implementation. |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | Provider registry implementation. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Local policy read by selected tests. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-10-host-dispatcher-provider-behavior-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-10-host-dispatcher-provider-behavior-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` status at plan creation: clean.

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(host dispatcher blocks codex-cli routing without verified runner result|host dispatcher allows codex-cli routing with ready runner result|host dispatcher builds codex-cli plan from verified runner result only|host dispatcher preserves ready desktop routing|host dispatcher read-only provider dispatch creates permit and uses fake in-memory execution|host dispatcher read-only provider dry run does not spawn|host dispatcher rejects workspace-write provider dispatch before spawn|host dispatcher rejects invalid provider plans before permit issuance)$' tests/host-dispatcher.test.ts
```

Future working directory:

```text
governance/codex-router
```

## Why This Scope

- It covers host dispatch fail-closed behavior before verified runner result.
- It checks codex-cli routing uses verified runner result as authority.
- It checks desktop routing does not invoke codex-cli dispatch.
- It checks read-only provider permit/dispatch behavior.
- It checks dry-run and workspace-write/invalid-plan rejection before spawn.
- It avoids the later formal read-only, registry selection, and broader provider
  execution tests until a separate gate.

The selected tests use injected/fake spawn functions and in-memory provider
surfaces. They must not be treated as real Codex CLI execution acceptance.

## Future Preflight Requirements

Before execution, confirm:

- this plan hash is stable
- prior Phase 10 closeout hashes are stable
- selected test and implementation hashes are stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the named-test pattern matches exactly the eight selected tests
- selected test lines still avoid filesystem writes, network, remote,
  dependency install/audit, real CLI execution, smoke, canary, and
  repository-root mutation
- any observed `spawn` is injected/fake and scoped to the test
- no command has been executed yet

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
HOST_DISPATCHER_PROVIDER_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
```

It cannot by itself grant:

- full host-dispatcher acceptance
- full provider acceptance
- real Codex CLI execution acceptance
- formal read-only integration execution acceptance
- consumer/runtime full acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

Phase 10 host-dispatcher/provider behavior is planned but not executed by this
plan. The next safe step is a PASS/FAIL preflight receipt for the exact command
above.

Marker:

```text
PHASE_10_HOST_DISPATCHER_PROVIDER_BEHAVIOR_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
