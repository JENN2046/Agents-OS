# Phase 10 Provider Registry Mutation / Query Behavior Receipt - 2026-06-29

Status: completed; PASS with limits.

Decision:
`PHASE_10_PROVIDER_REGISTRY_MUTATION_QUERY_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS`.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-mutation-query-behavior-plan-2026-06-29.md` | `36d31391834e2097b34d98dda98268b7d6f87089159285ca25c77f89480f01be` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-mutation-query-behavior-preflight-receipt-2026-06-29.md` | `b407bab954b117bde2fe9aa0166b683d770976f9776dde25acb7b4eda095d963` | stable |
| `ops/migration/inventory/phase-10-provider-registry-mutation-query-behavior-evidence-2026-06-29.md` | `fd5068a3874389184f4b86e6d520d43735c9e0088b3a7cd411ab1ef733f1d242` | created |

`governance/codex-router` git status after execution: clean.

## Command Result

Command executed from `governance/codex-router`:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry registers, gets, lists, and unregisters providers|provider-registry rejects duplicate provider ids|provider-registry rejects manifest kind mismatches with provider interface|provider-registry rejects mismatched provider manifests|provider-registry excludes disabled providers from automatic selection|provider-registry queries providers by kind|provider-registry queries providers by sideEffectClass|provider-registry queries providers by sandbox support)$' tests/provider-registry.test.ts
```

Result:

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `43` |
| TAP selected pass | `8` |
| TAP fail | `0` |
| TAP skipped | `35` |
| TAP duration | `684.54989 ms` |

## Acceptance Granted

Granted:

```text
PROVIDER_REGISTRY_MUTATION_QUERY_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
```

Meaning:

- selected in-memory provider registry mutation/query tests passed
- selected duplicate and manifest mismatch rejection paths passed
- selected disabled provider filtering and query paths passed
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

The Phase 10 provider registry mutation / query behavior gate completed
successfully and grants only narrow local behavior evidence acceptance.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_MUTATION_QUERY_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS
```
