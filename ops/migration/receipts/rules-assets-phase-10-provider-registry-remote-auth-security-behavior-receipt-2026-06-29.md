# Phase 10 Provider Registry Remote-Auth / Security Behavior Receipt - 2026-06-29

Status: completed; PASS with limits.

Decision:
`PHASE_10_PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS`.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-provider-registry-remote-auth-security-behavior-plan-2026-06-29.md` | `1753c1ad6886cab5f64a718f6a15c0988b049bce533519c48c23ad7f5ed40e3c` | stable |
| `ops/migration/receipts/rules-assets-phase-10-provider-registry-remote-auth-security-behavior-preflight-receipt-2026-06-29.md` | `50484667c541560be393beec66f4e8d83ce932f89d2edcec899c8621aefd8eea` | stable |
| `ops/migration/inventory/phase-10-provider-registry-remote-auth-security-behavior-evidence-2026-06-29.md` | `7100407e5a15ef542e13189318c0fe0c2b114e57bd13ae15f48df0bfcc008e53` | created |

`governance/codex-router` git status after execution: clean.

## Command Result

Command executed from `governance/codex-router`:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(provider-registry rejects remote agents without explicit authSchemes|provider-registry rejects anonymous remote agent auth schemes case-insensitively|provider-registry rejects anonymous auth declared only on provider manifest|provider-registry accepts Codex CLI provider while execution remains disabled|provider-registry rejects manifests without securityBoundary)$' tests/provider-registry.test.ts
```

Result:

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `43` |
| TAP selected pass | `5` |
| TAP fail | `0` |
| TAP skipped | `38` |
| TAP duration | `651.394857 ms` |

## Acceptance Granted

Granted:

```text
PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_NARROW_LOCAL_BEHAVIOR_EVIDENCE_PASS_WITH_LIMITS
```

Meaning:

- selected local remote-agent auth rejection tests passed
- selected anonymous auth and missing security boundary rejection paths passed
- selected Codex CLI provider registration with disabled execution test passed
- non-selected tests were skipped
- no dirty git status was observed after execution

## Not Granted

This receipt does not grant:

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

The Phase 10 provider registry remote-auth / security behavior gate completed
successfully and grants only narrow local behavior evidence acceptance.

Marker:

```text
PHASE_10_PROVIDER_REGISTRY_REMOTE_AUTH_SECURITY_BEHAVIOR_COMPLETED_PASS_WITH_LIMITS
```
