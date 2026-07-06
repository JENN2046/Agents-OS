# Phase 10 Provider Registry Mutation / Query Behavior Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans the Phase 10 provider registry mutation / query behavior
gate. It selects a narrow local named-test subset from
`provider-registry.test.ts` after the provider registry / selection gate.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-review-closeout-receipt-2026-06-29.md` | `b51657f39fc7b37db3b922ef5cb4df3756aa54060d4743d5a6da683a5b323f57` | Prior Phase 10 provider registry / selection closeout. |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | Selected test file. |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | Provider registry implementation. |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | Provider manifest/hash implementation. |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | Codex CLI provider source. |
| `governance/codex-router/packages/protocol-mcp/src/index.ts` | `2c9e944323ef658b249a95a93a8f955ec5085f58c29047f1e4293288451fc368` | MCP tool provider skeleton source. |
| `governance/codex-router/packages/protocol-a2a/src/index.ts` | `7f14c27e6c052235cfcb2a265ff0567b85decd95c489d15ba52899d3f66b2626` | A2A remote agent provider skeleton source. |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | Sandbox and manifest schema source. |
| `governance/codex-router/packages/kernel-contracts/test-fixtures/valid-agent-manifest.ts` | `333ce1b2e968775b9c006f3face65977600a5e8717cd940847dee07ce42b0aa0` | Static test fixture for disabled A2A provider data. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-10-provider-registry-mutation-query-behavior-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-10-provider-registry-mutation-query-behavior-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` status at plan creation: clean.

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry registers, gets, lists, and unregisters providers|provider-registry rejects duplicate provider ids|provider-registry rejects manifest kind mismatches with provider interface|provider-registry rejects mismatched provider manifests|provider-registry excludes disabled providers from automatic selection|provider-registry queries providers by kind|provider-registry queries providers by sideEffectClass|provider-registry queries providers by sandbox support)$' tests/provider-registry.test.ts
```

Future working directory:

```text
governance/codex-router
```

## Why This Scope

- It covers in-memory provider registration, lookup, listing, and unregistering.
- It covers duplicate provider rejection and manifest/provider mismatch rejection.
- It covers disabled provider exclusion from automatic selection.
- It covers query surfaces by provider kind, side effect class, and sandbox
  support.
- It excludes remote auth tests, execution-disablement tests, security-boundary
  tests, and file provider manifest store tests.

The selected tests may construct local MCP and A2A provider skeleton objects as
test data. They must not be treated as remote execution, MCP process launch, A2A
network behavior, file manifest store persistence, or real provider execution
acceptance.

## Future Preflight Requirements

Before execution, confirm:

- this plan hash is stable
- prior Phase 10 provider registry / selection closeout hash is stable
- selected test and implementation hashes are stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the named-test pattern matches exactly the eight selected tests
- selected test bodies and required helper lines still avoid filesystem writes,
  network, env credential reads, dependency install/audit, real CLI execution,
  smoke, canary, and repository-root mutation
- no command has been executed yet

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
PROVIDER_REGISTRY_MUTATION_QUERY_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
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

Phase 10 provider registry mutation / query behavior is planned but not executed
by this plan. The next safe step is a PASS/FAIL preflight receipt for the exact
command above.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_MUTATION_QUERY_BEHAVIOR_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
