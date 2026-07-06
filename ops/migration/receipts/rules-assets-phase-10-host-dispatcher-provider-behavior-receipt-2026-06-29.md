# Phase 10 Host-Dispatcher / Provider Behavior Receipt - 2026-06-29

Status: completed; PASS with limits.

Decision:
`PHASE_10_HOST_DISPATCHER_PROVIDER_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS`.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-host-dispatcher-provider-behavior-plan-2026-06-29.md` | `feb00859a9752d65f7e2830c2362e4faa1f50f2634bce7a10f74c075c500ec84` | stable |
| `ops/migration/receipts/rules-assets-phase-10-host-dispatcher-provider-behavior-preflight-receipt-2026-06-29.md` | `3281c82c0bf455cd577cb8c4c94c830143a307a6a001d7742ad63d53e22b7034` | stable |
| `ops/migration/inventory/phase-10-host-dispatcher-provider-behavior-evidence-2026-06-29.md` | `92e6a92742aba244c0f709e08b5dcfb353e060916952407139a1eb348445eeb0` | created |

`governance/codex-router` git status after execution: clean.

## Command Result

Command executed from `governance/codex-router`:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(host dispatcher blocks codex-cli routing without verified runner result|host dispatcher allows codex-cli routing with ready runner result|host dispatcher builds codex-cli plan from verified runner result only|host dispatcher preserves ready desktop routing|host dispatcher read-only provider dispatch creates permit and uses fake in-memory execution|host dispatcher read-only provider dry run does not spawn|host dispatcher rejects workspace-write provider dispatch before spawn|host dispatcher rejects invalid provider plans before permit issuance)$' tests/host-dispatcher.test.ts
```

Result:

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `19` |
| TAP selected pass | `8` |
| TAP fail | `0` |
| TAP skipped | `11` |
| TAP duration | `873.715559 ms` |

## Acceptance Granted

Granted:

```text
HOST_DISPATCHER_PROVIDER_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
```

Meaning:

- selected host-dispatcher and read-only provider local behavior tests passed
- selected fail-closed paths rejected before spawn
- non-selected tests were skipped
- no dirty git status was observed after execution

## Not Granted

This receipt does not grant:

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

The Phase 10 host-dispatcher/provider behavior gate completed successfully and
grants only narrow local behavior evidence acceptance.

Marker:

```text
PHASE_10_HOST_DISPATCHER_PROVIDER_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS
```
