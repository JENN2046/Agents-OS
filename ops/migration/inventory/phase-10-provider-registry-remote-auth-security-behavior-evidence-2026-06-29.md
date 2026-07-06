# Phase 10 Provider Registry Remote-Auth / Security Behavior Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the narrow Phase 10 provider registry remote-auth /
security behavior exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-remote-auth-security-behavior-plan-2026-06-29.md` | `1753c1ad6886cab5f64a718f6a15c0988b049bce533519c48c23ad7f5ed40e3c` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-preflight-receipt-2026-06-29.md` | `50484667c541560be393beec66f4e8d83ce932f89d2edcec899c8621aefd8eea` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable after execution |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable after execution |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable after execution |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable after execution |
| `governance/codex-router/packages/protocol-a2a/src/index.ts` | `7f14c27e6c052235cfcb2a265ff0567b85decd95c489d15ba52899d3f66b2626` | stable after execution |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | stable after execution |
| `governance/codex-router/packages/kernel-contracts/test-fixtures/valid-agent-manifest.ts` | `333ce1b2e968775b9c006f3face65977600a5e8717cd940847dee07ce42b0aa0` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-10-provider-registry-remote-auth-security-behavior-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-review-closeout-receipt-2026-06-29.md` | absent |

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
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry rejects remote agents without explicit authSchemes|provider-registry rejects anonymous remote agent auth schemes case-insensitively|provider-registry rejects anonymous auth declared only on provider manifest|provider-registry accepts Codex CLI provider while execution remains disabled|provider-registry rejects manifests without securityBoundary)$' tests/provider-registry.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `43` |
| TAP selected pass | `5` |
| TAP fail | `0` |
| TAP skipped | `38` |
| TAP todo | `0` |
| TAP duration | `651.394857 ms` |
| Codex tool wall time | approximately `1.6 s` |

Selected passing tests:

- `provider-registry rejects remote agents without explicit authSchemes`
- `provider-registry rejects anonymous remote agent auth schemes case-insensitively`
- `provider-registry rejects anonymous auth declared only on provider manifest`
- `provider-registry accepts Codex CLI provider while execution remains disabled`
- `provider-registry rejects manifests without securityBoundary`

## Evidence Boundary

This run confirms only:

- selected local remote-agent auth rejection tests passed
- selected anonymous auth rejection tests passed
- selected missing security boundary rejection test passed
- selected Codex CLI provider registration with disabled execution test passed
- non-selected tests were skipped by the named-test pattern
- the run did not dirty `governance/codex-router`

This run does not grant:

- full provider registry acceptance
- file provider manifest store persistence acceptance
- full provider acceptance
- real Codex CLI execution acceptance
- remote agent execution acceptance
- formal read-only integration execution acceptance
- consumer/runtime full acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

The Phase 10 provider registry remote-auth / security behavior exact-run
completed with exit code `0` and TAP `5` selected pass / `0` fail / `38`
skipped.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_BEHAVIOR_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
