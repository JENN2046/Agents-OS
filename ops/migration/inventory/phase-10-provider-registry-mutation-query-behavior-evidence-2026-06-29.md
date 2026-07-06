# Phase 10 Provider Registry Mutation / Query Behavior Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the narrow Phase 10 provider registry mutation / query
behavior exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-mutation-query-behavior-plan-2026-06-29.md` | `36d31391834e2097b34d98dda98268b7d6f87089159285ca25c77f89480f01be` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-preflight-receipt-2026-06-29.md` | `b407bab954b117bde2fe9aa0166b683d770976f9776dde25acb7b4eda095d963` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable after execution |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable after execution |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable after execution |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable after execution |
| `governance/codex-router/packages/protocol-mcp/src/index.ts` | `2c9e944323ef658b249a95a93a8f955ec5085f58c29047f1e4293288451fc368` | stable after execution |
| `governance/codex-router/packages/protocol-a2a/src/index.ts` | `7f14c27e6c052235cfcb2a265ff0567b85decd95c489d15ba52899d3f66b2626` | stable after execution |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | stable after execution |
| `governance/codex-router/packages/kernel-contracts/test-fixtures/valid-agent-manifest.ts` | `333ce1b2e968775b9c006f3face65977600a5e8717cd940847dee07ce42b0aa0` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-10-provider-registry-mutation-query-behavior-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status after execution: clean.

Current `governance/codex-router` HEAD:

```text
88b84c66e7c815ca5797507c9e957cf5ad38eba2
```

## Command Executed

Working directory:

```text
governance/codex-router
```

Command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry registers, gets, lists, and unregisters providers|provider-registry rejects duplicate provider ids|provider-registry rejects manifest kind mismatches with provider interface|provider-registry rejects mismatched provider manifests|provider-registry excludes disabled providers from automatic selection|provider-registry queries providers by kind|provider-registry queries providers by sideEffectClass|provider-registry queries providers by sandbox support)$' tests/provider-registry.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `43` |
| TAP selected pass | `8` |
| TAP fail | `0` |
| TAP skipped | `35` |
| TAP todo | `0` |
| TAP duration | `684.54989 ms` |
| Codex tool wall time | approximately `1.6 s` |

Selected passing tests:

- `provider-registry registers, gets, lists, and unregisters providers`
- `provider-registry rejects duplicate provider ids`
- `provider-registry rejects manifest kind mismatches with provider interface`
- `provider-registry rejects mismatched provider manifests`
- `provider-registry excludes disabled providers from automatic selection`
- `provider-registry queries providers by kind`
- `provider-registry queries providers by sideEffectClass`
- `provider-registry queries providers by sandbox support`

## Evidence Boundary

This run confirms only:

- selected in-memory provider registry mutation/query tests passed
- selected duplicate and manifest mismatch rejection paths passed
- selected disabled provider filtering and query paths passed
- non-selected tests were skipped by the named-test pattern
- the run did not dirty `governance/codex-router`

This run does not grant:

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

The Phase 10 provider registry mutation / query behavior exact-run completed
with exit code `0` and TAP `8` selected pass / `0` fail / `35` skipped.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_MUTATION_QUERY_BEHAVIOR_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
