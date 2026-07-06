# Phase 11 Provider Execution Runner Controlled Read-Only Receipt - 2026-06-29

Status: completed; PASS with limits.

Decision:
`PHASE_11_PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_COMPLETED_PASS_WITH_LIMITS`.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-11-provider-execution-runner-controlled-readonly-plan-2026-06-29.md` | `24c037b56bb7684836f1e32861e438309655720e7c87d7d1f80eac9c57e73182` | stable |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-preflight-receipt-2026-06-29.md` | `de87530e9a06783b55407c8ac669f93230c8a57566f70a6697c24e74772da6ab` | stable |
| `ops/migration/inventory/phase-11-provider-execution-runner-controlled-readonly-evidence-2026-06-29.md` | `ada9cc1adb80712ecf9efd30c08c47bdf46b5f57e43d7470ac883d55d2c3f62d` | created |

Selected source files remained hash-stable after execution. The repository HEAD
advanced from `c7f39cbff5fb7847796916945faff11ade3d9adc` to
`bed92be781d2a0e8eee2356d8bb068c018802dca` due to a docs/state-only commit
outside this gate.

## Command Result

Command executed from `governance/codex-router`:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(host dispatcher dispatches ready read-only runner results through provider permits|host dispatcher validates provider registry selection before read-only runner dispatch|host dispatcher formal read-only dispatch requires registry and metadata before spawn|host dispatcher formal read-only dispatch executes only through guarded fake spawner|host dispatcher dry-runs read-only runner provider dispatch without spawn)$' tests/host-dispatcher.test.ts
```

Result:

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `21` |
| TAP selected pass | `5` |
| TAP fail | `0` |
| TAP skipped | `16` |
| TAP duration | `821.60233 ms` |

## Acceptance Granted

Granted:

```text
PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_EVIDENCE_PASS_WITH_LIMITS
```

Meaning:

- selected read-only runner result to provider permit dispatch tests passed
- selected provider registry selection before dispatch passed
- selected formal read-only pre-spawn and guarded fake-spawner paths passed
- selected dry-run without spawn passed
- non-selected tests were skipped

## Not Granted

This receipt does not grant:

- full provider execution acceptance
- real Codex CLI execution acceptance
- remote agent execution acceptance
- full consumer/runtime integration acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

The Phase 11 provider execution runner controlled read-only gate completed
successfully and grants only controlled local read-only evidence acceptance.

Marker:

```text
PHASE_11_PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_COMPLETED_PASS_WITH_LIMITS
```
