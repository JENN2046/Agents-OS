# Phase 10 Provider Registry Remote-Auth / Security Behavior Preflight Receipt - 2026-06-29

Status: PASS; preflight only; no test, typecheck, build, npm script, smoke,
canary, dependency install, dependency audit, source edit, revert, network,
remote, sync, deploy, or workspace mutation has been executed by this receipt.

Decision:
`PHASE_10_PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_BEHAVIOR_PREFLIGHT_PASS_NO_EXECUTION`.

## Inputs Checked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-remote-auth-security-behavior-plan-2026-06-29.md` | `1753c1ad6886cab5f64a718f6a15c0988b049bce533519c48c23ad7f5ed40e3c` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-review-closeout-receipt-2026-06-29.md` | `c436cb1c23928f07787e16289efcf5f5e0978744995f534ea6deced40cba9e5d` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable |
| `governance/codex-router/packages/protocol-a2a/src/index.ts` | `7f14c27e6c052235cfcb2a265ff0567b85decd95c489d15ba52899d3f66b2626` | stable |
| `governance/codex-router/packages/kernel-contracts/src/index.ts` | `fec71b0048da9452b4513c44fd62964e07d25637c69c45e0eac642e08f717ee0` | stable |
| `governance/codex-router/packages/kernel-contracts/test-fixtures/valid-agent-manifest.ts` | `333ce1b2e968775b9c006f3face65977600a5e8717cd940847dee07ce42b0aa0` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-10-provider-registry-remote-auth-security-behavior-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status at preflight: clean.

## Exact Command Confirmed

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry rejects remote agents without explicit authSchemes|provider-registry rejects anonymous remote agent auth schemes case-insensitively|provider-registry rejects anonymous auth declared only on provider manifest|provider-registry accepts Codex CLI provider while execution remains disabled|provider-registry rejects manifests without securityBoundary)$' tests/provider-registry.test.ts
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
| named-test pattern | Matches exactly five selected tests at lines `555`, `571`, `598`, `618`, and `634`. | PASS |
| selected test bodies | No filesystem write, network, env credential read, spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in lines `555-647`. | PASS |
| selected helper lines | No filesystem write, network, env credential read, spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in required helper lines `816-844`. | PASS |
| `auth` / `anonymous` / `remote` terms | Observed only as static test data and rejection assertions for remote-agent registration rules. | PASS_WITH_NOTE |
| Codex CLI execute call | Selected test reaches the default disabled-execution error before any real execution branch. | PASS_WITH_NOTE |
| excluded tests | File manifest store and broad provider registry tests remain outside the named-test pattern. | PASS |

## Preflight Result

PASS.

The next execution gate may run only the exact command listed above.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_BEHAVIOR_PREFLIGHT_PASS_NO_EXECUTION
```
