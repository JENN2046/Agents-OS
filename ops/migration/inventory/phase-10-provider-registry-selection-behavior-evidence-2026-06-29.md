# Phase 10 Provider Registry / Selection Behavior Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the narrow Phase 10 provider registry / selection
behavior exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-selection-behavior-plan-2026-06-29.md` | `b9227c80e19febacedf9817a4de3494ed0c458937d06f4b55d952874ccedfdcc` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-preflight-receipt-2026-06-29.md` | `2b291dc92dae88a9795ae5f4182845ab00b9b16a981dca9f9967480db3495f94` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable after execution |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable after execution |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable after execution |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable after execution |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | stable after execution |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-10-provider-registry-selection-behavior-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-review-closeout-receipt-2026-06-29.md` | absent |

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
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry read-only catalog registers codex-cli manifest|provider-registry read-only catalog gets provider by id|provider-registry read-only catalog lists all and enabled providers|provider-registry read-only catalog rejects duplicate providers|provider-registry read-only catalog excludes disabled provider from listEnabled|provider-registry read-only catalog snapshot is stable and sanitized|provider-registry read-only catalog manifest hash changes when manifest changes|provider-registry selection selects codex-cli by providerId|provider-registry selection rejects missing providers|provider-registry selection rejects disabled provider by default|provider-registry selection can read disabled provider when enabled is not required|provider-registry selection rejects kind mismatch|provider-registry selection rejects manifest hash mismatch|provider-registry selection rejects missing capabilities|provider-registry selection rejects unsupported side effects|provider-registry selection accepts supported side effects|provider-registry selection rejects unsupported sandbox|provider-registry selection accepts supported read-only sandbox|provider-registry selection selects provider for grant|provider-registry selection selects provider for routing decision|provider-registry selection rejects routing decisions without provider grants|provider-registry selection rejects routing decision manifest mismatch|provider-registry selection rejects provider grant manifest mismatch|provider-registry selection result is sanitized|provider-registry routing decision selection result is sanitized)$' tests/provider-registry.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `43` |
| TAP selected pass | `25` |
| TAP fail | `0` |
| TAP skipped | `18` |
| TAP todo | `0` |
| TAP duration | `754.12826 ms` |
| Codex tool wall time | approximately `1.7 s` |

Selected passing tests:

- `provider-registry read-only catalog registers codex-cli manifest`
- `provider-registry read-only catalog gets provider by id`
- `provider-registry read-only catalog lists all and enabled providers`
- `provider-registry read-only catalog rejects duplicate providers`
- `provider-registry read-only catalog excludes disabled provider from listEnabled`
- `provider-registry read-only catalog snapshot is stable and sanitized`
- `provider-registry read-only catalog manifest hash changes when manifest changes`
- `provider-registry selection selects codex-cli by providerId`
- `provider-registry selection rejects missing providers`
- `provider-registry selection rejects disabled provider by default`
- `provider-registry selection can read disabled provider when enabled is not required`
- `provider-registry selection rejects kind mismatch`
- `provider-registry selection rejects manifest hash mismatch`
- `provider-registry selection rejects missing capabilities`
- `provider-registry selection rejects unsupported side effects`
- `provider-registry selection accepts supported side effects`
- `provider-registry selection rejects unsupported sandbox`
- `provider-registry selection accepts supported read-only sandbox`
- `provider-registry selection selects provider for grant`
- `provider-registry selection selects provider for routing decision`
- `provider-registry selection rejects routing decisions without provider grants`
- `provider-registry selection rejects routing decision manifest mismatch`
- `provider-registry selection rejects provider grant manifest mismatch`
- `provider-registry selection result is sanitized`
- `provider-registry routing decision selection result is sanitized`

## Evidence Boundary

This run confirms only:

- selected provider registry catalog and selection local behavior tests passed
- selected read-only codex-cli provider selection paths passed
- selected fail-closed provider selection paths passed
- selected grant/routing decision selection paths passed
- selected sanitized result checks passed
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

The Phase 10 provider registry / selection behavior exact-run completed with
exit code `0` and TAP `25` selected pass / `0` fail / `18` skipped.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_SELECTION_BEHAVIOR_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
