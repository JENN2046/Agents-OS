# Phase 10 Provider Registry Remote-Auth / Security Behavior Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans the Phase 10 provider registry remote-auth / security
behavior gate. It selects a narrow local named-test subset from
`provider-registry.test.ts` after the provider registry mutation / query gate.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-review-closeout-receipt-2026-06-29.md` | `c436cb1c23928f07787e16289efcf5f5e0978744995f534ea6deced40cba9e5d` | Prior Phase 10 provider registry mutation / query closeout. |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | Selected test file. |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | Provider registry implementation. |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | Provider manifest/hash implementation. |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | Codex CLI provider source. |
| `governance/codex-router/packages/protocol-a2a/src/index.ts` | `7f14c27e6c052235cfcb2a265ff0567b85decd95c489d15ba52899d3f66b2626` | A2A remote agent provider skeleton source. |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | Manifest schema source. |
| `governance/codex-router/packages/kernel-contracts/test-fixtures/valid-agent-manifest.ts` | `333ce1b2e968775b9c006f3face65977600a5e8717cd940847dee07ce42b0aa0` | Static A2A test fixture. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-10-provider-registry-remote-auth-security-behavior-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-10-provider-registry-remote-auth-security-behavior-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` status at plan creation: clean.

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry rejects remote agents without explicit authSchemes|provider-registry rejects anonymous remote agent auth schemes case-insensitively|provider-registry rejects anonymous auth declared only on provider manifest|provider-registry accepts Codex CLI provider while execution remains disabled|provider-registry rejects manifests without securityBoundary)$' tests/provider-registry.test.ts
```

Future working directory:

```text
governance/codex-router
```

## Why This Scope

- It covers remote-agent registration fail-closed behavior when auth schemes are
  missing.
- It covers anonymous remote-agent auth rejection across several static shapes.
- It covers anonymous auth rejection when the unsafe value appears only on the
  provider object manifest.
- It covers Codex CLI provider registration while execution remains disabled.
- It covers manifest rejection when `securityBoundary` is missing.
- It excludes file provider manifest store tests and any broad package script.

The selected tests construct local provider skeletons and call the Codex CLI
provider only far enough to assert the default disabled-execution error. They
must not be treated as remote execution, network behavior, real Codex CLI
execution, file persistence, or broad provider acceptance.

## Future Preflight Requirements

Before execution, confirm:

- this plan hash is stable
- prior Phase 10 provider registry mutation / query closeout hash is stable
- selected test and implementation hashes are stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the named-test pattern matches exactly the five selected tests
- selected test bodies and required helper lines still avoid filesystem writes,
  network, env credential reads, dependency install/audit, real CLI execution,
  smoke, canary, and repository-root mutation
- observed `auth` / `anonymous` terms are test data and rejection assertions only
- no command has been executed yet

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
```

It cannot by itself grant:

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

Phase 10 provider registry remote-auth / security behavior is planned but not
executed by this plan. The next safe step is a PASS/FAIL preflight receipt for
the exact command above.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_BEHAVIOR_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
