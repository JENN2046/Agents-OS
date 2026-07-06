# Phase 10 Host-Dispatcher / Provider Behavior Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the first narrow Phase 10 host-dispatcher/provider
behavior exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-host-dispatcher-provider-behavior-plan-2026-06-29.md` | `feb00859a9752d65f7e2830c2362e4faa1f50f2634bce7a10f74c075c500ec84` | stable |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-preflight-receipt-2026-06-29.md` | `3281c82c0bf455cd577cb8c4c94c830143a307a6a001d7742ad63d53e22b7034` | stable |
| `governance/codex-router/tests/host-dispatcher.test.ts` | `ccde8afb72c51aafe0dce7feaacc19aa0baef0814d3f612adb9d95b02f79003f` | stable after execution |
| `governance/codex-router/packages/host-dispatcher/src/index.ts` | `cd6bbe27b19637eee7473617bba4d78ed72dd824466ef8a2294d9748505ef971` | stable after execution |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable after execution |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable after execution |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable after execution |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-10-host-dispatcher-provider-behavior-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-review-closeout-receipt-2026-06-29.md` | absent |

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
./node_modules/.bin/tsx --test --test-name-pattern '^(host dispatcher blocks codex-cli routing without verified runner result|host dispatcher allows codex-cli routing with ready runner result|host dispatcher builds codex-cli plan from verified runner result only|host dispatcher preserves ready desktop routing|host dispatcher read-only provider dispatch creates permit and uses fake in-memory execution|host dispatcher read-only provider dry run does not spawn|host dispatcher rejects workspace-write provider dispatch before spawn|host dispatcher rejects invalid provider plans before permit issuance)$' tests/host-dispatcher.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `19` |
| TAP selected pass | `8` |
| TAP fail | `0` |
| TAP skipped | `11` |
| TAP todo | `0` |
| TAP duration | `873.715559 ms` |
| Codex tool wall time | approximately `1.9 s` |

Selected passing tests:

- `host dispatcher blocks codex-cli routing without verified runner result`
- `host dispatcher allows codex-cli routing with ready runner result`
- `host dispatcher builds codex-cli plan from verified runner result only`
- `host dispatcher preserves ready desktop routing`
- `host dispatcher read-only provider dispatch creates permit and uses fake in-memory execution`
- `host dispatcher read-only provider dry run does not spawn`
- `host dispatcher rejects workspace-write provider dispatch before spawn`
- `host dispatcher rejects invalid provider plans before permit issuance`

## Evidence Boundary

This run confirms only:

- selected host-dispatcher local behavior tests passed
- selected read-only provider dispatch and fail-closed tests passed
- selected workspace-write and invalid-plan paths reject before spawn
- non-selected tests were skipped by the named-test pattern
- the run did not dirty `governance/codex-router`

This run does not grant:

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

The Phase 10 host-dispatcher/provider behavior exact-run completed with exit
code `0` and TAP `8` selected pass / `0` fail / `11` skipped.

Marker:

```text
PHASE_10_HOST_DISPATCHER_PROVIDER_BEHAVIOR_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
