# Phase 10 Provider Registry / Selection Behavior Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans the Phase 10 provider registry / selection behavior gate.
It selects a narrow local named-test subset from `provider-registry.test.ts`
instead of running the full provider registry suite.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-10-scope-plan-2026-06-29.md` | `71713e6b1f5f43475d48a77698fd26dca79ae0bee925ca81191fbb5c3f59509f` | Phase 10 scope authority. |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-review-closeout-receipt-2026-06-29.md` | `797c5127b56012b2b536f43f7c35da7dda7c993469d957680a2f1e82df8f4f02` | Prior Phase 10 host-dispatcher/provider behavior closeout. |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | Selected test file. |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | Provider registry implementation. |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | Provider manifest/hash implementation. |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | Codex CLI provider manifest source. |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | Provider grant and routing decision schemas used by selected tests. |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | Sandbox profile schema used by selected tests. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-10-provider-registry-selection-behavior-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-10-provider-registry-selection-behavior-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` status at plan creation: clean.

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry read-only catalog registers codex-cli manifest|provider-registry read-only catalog gets provider by id|provider-registry read-only catalog lists all and enabled providers|provider-registry read-only catalog rejects duplicate providers|provider-registry read-only catalog excludes disabled provider from listEnabled|provider-registry read-only catalog snapshot is stable and sanitized|provider-registry read-only catalog manifest hash changes when manifest changes|provider-registry selection selects codex-cli by providerId|provider-registry selection rejects missing providers|provider-registry selection rejects disabled provider by default|provider-registry selection can read disabled provider when enabled is not required|provider-registry selection rejects kind mismatch|provider-registry selection rejects manifest hash mismatch|provider-registry selection rejects missing capabilities|provider-registry selection rejects unsupported side effects|provider-registry selection accepts supported side effects|provider-registry selection rejects unsupported sandbox|provider-registry selection accepts supported read-only sandbox|provider-registry selection selects provider for grant|provider-registry selection selects provider for routing decision|provider-registry selection rejects routing decisions without provider grants|provider-registry selection rejects routing decision manifest mismatch|provider-registry selection rejects provider grant manifest mismatch|provider-registry selection result is sanitized|provider-registry routing decision selection result is sanitized)$' tests/provider-registry.test.ts
```

Future working directory:

```text
governance/codex-router
```

## Why This Scope

- It covers the read-only catalog surface for registering, listing, hashing, and
  sanitizing provider metadata.
- It covers provider selection fail-closed behavior for missing, disabled, kind
  mismatch, manifest hash mismatch, missing capability, unsupported side effect,
  and unsupported sandbox cases.
- It covers successful read-only codex-cli selection by provider id, grant, and
  routing decision.
- It covers sanitized selection result output.
- It excludes later registry mutation API tests, remote auth tests, Codex CLI
  execution-disablement tests, and file provider manifest store tests.

The selected tests use in-memory registry/catalog/selection surfaces. They must
not be treated as real provider execution, real Codex CLI execution, manifest
store persistence, remote auth, or broad package acceptance.

## Future Preflight Requirements

Before execution, confirm:

- this plan hash is stable
- prior Phase 10 closeout hash is stable
- selected test and implementation hashes are stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the named-test pattern matches exactly the 25 selected tests
- selected test lines still avoid filesystem writes, network, remote,
  dependency install/audit, real CLI execution, smoke, canary, and
  repository-root mutation
- any observed secret-like terms are static negative assertions only
- no command has been executed yet

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
PROVIDER_REGISTRY_SELECTION_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
```

It cannot by itself grant:

- full provider registry acceptance
- file provider manifest store persistence acceptance
- remote auth provider acceptance
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

Phase 10 provider registry / selection behavior is planned but not executed by
this plan. The next safe step is a PASS/FAIL preflight receipt for the exact
command above.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_SELECTION_BEHAVIOR_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
