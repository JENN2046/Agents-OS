# Phase 10 Provider Registry Mutation / Query Behavior Preflight Receipt - 2026-06-29

Status: PASS; preflight only; no test, typecheck, build, npm script, smoke,
canary, dependency install, dependency audit, source edit, revert, network,
remote, sync, deploy, or workspace mutation has been executed by this receipt.

Decision:
`PHASE_10_PROVIDER_REGISTRY_MUTATION_QUERY_BEHAVIOR_PREFLIGHT_PASS_NO_EXECUTION`.

## Inputs Checked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-mutation-query-behavior-plan-2026-06-29.md` | `36d31391834e2097b34d98dda98268b7d6f87089159285ca25c77f89480f01be` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-review-closeout-receipt-2026-06-29.md` | `b51657f39fc7b37db3b922ef5cb4df3756aa54060d4743d5a6da683a5b323f57` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable |
| `governance/codex-router/packages/protocol-mcp/src/index.ts` | `2c9e944323ef658b249a95a93a8f955ec5085f58c29047f1e4293288451fc368` | stable |
| `governance/codex-router/packages/protocol-a2a/src/index.ts` | `7f14c27e6c052235cfcb2a265ff0567b85decd95c489d15ba52899d3f66b2626` | stable |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | stable |
| `governance/codex-router/packages/kernel-contracts/test-fixtures/valid-agent-manifest.ts` | `333ce1b2e968775b9c006f3face65977600a5e8717cd940847dee07ce42b0aa0` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-10-provider-registry-mutation-query-behavior-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status at preflight: clean.

## Exact Command Confirmed

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry registers, gets, lists, and unregisters providers|provider-registry rejects duplicate provider ids|provider-registry rejects manifest kind mismatches with provider interface|provider-registry rejects mismatched provider manifests|provider-registry excludes disabled providers from automatic selection|provider-registry queries providers by kind|provider-registry queries providers by sideEffectClass|provider-registry queries providers by sandbox support)$' tests/provider-registry.test.ts
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
| named-test pattern | Matches exactly eight selected tests at lines `417`, `444`, `456`, `470`, `492`, `511`, `523`, and `542`. | PASS |
| selected test bodies | No filesystem write, network, env credential read, spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in lines `417-554`. | PASS |
| selected helper lines | No filesystem write, network, env credential read, spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in required helper lines `795-844`. | PASS |
| remote-like fixture | A2A provider skeleton is constructed only as disabled local test data; no network or remote execution is invoked. | PASS_WITH_NOTE |
| excluded tests | Remote auth, execution-disablement, security-boundary, and file manifest store tests remain outside the named-test pattern. | PASS |

## Preflight Result

PASS.

The next execution gate may run only the exact command listed above.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_MUTATION_QUERY_BEHAVIOR_PREFLIGHT_PASS_NO_EXECUTION
```
