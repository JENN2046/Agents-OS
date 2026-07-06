# Phase 10 Provider Registry / Selection Behavior Preflight Receipt - 2026-06-29

Status: PASS; preflight only; no test, typecheck, build, npm script, smoke,
canary, dependency install, dependency audit, source edit, revert, network,
remote, sync, deploy, or workspace mutation has been executed by this receipt.

Decision:
`PHASE_10_PROVIDER_REGISTRY_SELECTION_BEHAVIOR_PREFLIGHT_PASS_NO_EXECUTION`.

## Inputs Checked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-selection-behavior-plan-2026-06-29.md` | `b9227c80e19febacedf9817a4de3494ed0c458937d06f4b55d952874ccedfdcc` | stable |
| `ops/migration/plans/phase-10-scope-plan-2026-06-29.md` | `71713e6b1f5f43475d48a77698fd26dca79ae0bee925ca81191fbb5c3f59509f` | stable |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-review-closeout-receipt-2026-06-29.md` | `797c5127b56012b2b536f43f7c35da7dda7c993469d957680a2f1e82df8f4f02` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | stable |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-10-provider-registry-selection-behavior-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status at preflight: clean.

## Exact Command Confirmed

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry read-only catalog registers codex-cli manifest|provider-registry read-only catalog gets provider by id|provider-registry read-only catalog lists all and enabled providers|provider-registry read-only catalog rejects duplicate providers|provider-registry read-only catalog excludes disabled provider from listEnabled|provider-registry read-only catalog snapshot is stable and sanitized|provider-registry read-only catalog manifest hash changes when manifest changes|provider-registry selection selects codex-cli by providerId|provider-registry selection rejects missing providers|provider-registry selection rejects disabled provider by default|provider-registry selection can read disabled provider when enabled is not required|provider-registry selection rejects kind mismatch|provider-registry selection rejects manifest hash mismatch|provider-registry selection rejects missing capabilities|provider-registry selection rejects unsupported side effects|provider-registry selection accepts supported side effects|provider-registry selection rejects unsupported sandbox|provider-registry selection accepts supported read-only sandbox|provider-registry selection selects provider for grant|provider-registry selection selects provider for routing decision|provider-registry selection rejects routing decisions without provider grants|provider-registry selection rejects routing decision manifest mismatch|provider-registry selection rejects provider grant manifest mismatch|provider-registry selection result is sanitized|provider-registry routing decision selection result is sanitized)$' tests/provider-registry.test.ts
```

Working directory:

```text
governance/codex-router
```

Local runner:

| Tool | Observation | Result |
| --- | --- | --- |
| `governance/codex-router/node_modules/.bin/tsx` | exists; symbolic link; mode `777`; target `../tsx/dist/cli.mjs` | PASS |

## Static Safety Check

| Surface | Finding | Result |
| --- | --- | --- |
| named-test pattern | Matches exactly 25 selected tests at lines `46`, `69`, `80`, `101`, `114`, `129`, `156`, `168`, `179`, `192`, `210`, `226`, `239`, `250`, `263`, `276`, `287`, `304`, `320`, `329`, `341`, `352`, `363`, `375`, and `394`. | PASS |
| selected test bodies | No filesystem write, network, env credential read, spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in lines `46-416`. | PASS |
| selected helper lines | No filesystem write, network, env credential read, spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in required helper lines `846-922`. | PASS |
| secret-like strings | Observed only in static negative sanitization assertions such as `serialized.includes("secret") === false` and `serialized.includes("OPENAI_API_KEY") === false`. | PASS_WITH_NOTE |
| excluded tests | Later registry mutation, remote auth, execution-disablement, and file manifest store tests remain outside the named-test pattern. | PASS |

## Preflight Result

PASS.

The next execution gate may run only the exact command listed above.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_SELECTION_BEHAVIOR_PREFLIGHT_PASS_NO_EXECUTION
```
