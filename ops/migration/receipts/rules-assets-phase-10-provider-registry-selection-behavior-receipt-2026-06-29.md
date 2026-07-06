# Phase 10 Provider Registry / Selection Behavior Receipt - 2026-06-29

Status: completed; PASS with limits.

Decision:
`PHASE_10_PROVIDER_REGISTRY_SELECTION_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS`.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-selection-behavior-plan-2026-06-29.md` | `b9227c80e19febacedf9817a4de3494ed0c458937d06f4b55d952874ccedfdcc` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-selection-behavior-preflight-receipt-2026-06-29.md` | `2b291dc92dae88a9795ae5f4182845ab00b9b16a981dca9f9967480db3495f94` | stable |
| `ops/migration/inventory/phase-10-provider-registry-selection-behavior-evidence-2026-06-29.md` | `92e890ec78f70852aaf97f2cc576540b3f3222bd8753e298994955179ba18460` | created |

`governance/codex-router` git status after execution: clean.

## Command Result

Command executed from `governance/codex-router`:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry read-only catalog registers codex-cli manifest|provider-registry read-only catalog gets provider by id|provider-registry read-only catalog lists all and enabled providers|provider-registry read-only catalog rejects duplicate providers|provider-registry read-only catalog excludes disabled provider from listEnabled|provider-registry read-only catalog snapshot is stable and sanitized|provider-registry read-only catalog manifest hash changes when manifest changes|provider-registry selection selects codex-cli by providerId|provider-registry selection rejects missing providers|provider-registry selection rejects disabled provider by default|provider-registry selection can read disabled provider when enabled is not required|provider-registry selection rejects kind mismatch|provider-registry selection rejects manifest hash mismatch|provider-registry selection rejects missing capabilities|provider-registry selection rejects unsupported side effects|provider-registry selection accepts supported side effects|provider-registry selection rejects unsupported sandbox|provider-registry selection accepts supported read-only sandbox|provider-registry selection selects provider for grant|provider-registry selection selects provider for routing decision|provider-registry selection rejects routing decisions without provider grants|provider-registry selection rejects routing decision manifest mismatch|provider-registry selection rejects provider grant manifest mismatch|provider-registry selection result is sanitized|provider-registry routing decision selection result is sanitized)$' tests/provider-registry.test.ts
```

Result:

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `43` |
| TAP selected pass | `25` |
| TAP fail | `0` |
| TAP skipped | `18` |
| TAP duration | `754.12826 ms` |

## Acceptance Granted

Granted:

```text
PROVIDER_REGISTRY_SELECTION_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
```

Meaning:

- selected provider registry catalog and selection local behavior tests passed
- selected read-only codex-cli provider selection and fail-closed paths passed
- selected grant/routing decision selection and sanitization checks passed
- non-selected tests were skipped
- no dirty git status was observed after execution

## Not Granted

This receipt does not grant:

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

The Phase 10 provider registry / selection behavior gate completed successfully
and grants only narrow local behavior evidence acceptance.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_SELECTION_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS
```
