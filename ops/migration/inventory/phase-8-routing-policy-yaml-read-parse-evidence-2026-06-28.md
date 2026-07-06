# Phase 8 Routing Policy YAML Read/Parse Evidence

Date: 2026-06-28

Status: evidence collected.

Scope: exact-file bounded read and YAML parse-only evidence for
`governance/codex-router/routing-policy.yaml`.

No router code, runtime, loader, package scripts, tests, builds, typechecks,
validators, sync, deploy, network, or remote actions were executed.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-routing-policy-yaml-read-parse-gate-plan-2026-06-28.md` | `e81d9b304aeac5298a61b6703cd8282ea92a7f9b5775949dad02d0303baf009b` | stable at preflight |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-preflight-receipt-2026-06-28.md` | pending at collection start | created before this evidence |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | parsed |

## File Facts

| Path | Type | Mode | Size | `wc -l` |
| --- | --- | --- | --- | --- |
| `governance/codex-router/routing-policy.yaml` | regular file | `644` | `6318` bytes | `254` |

Result: file stayed within the admitted `16 KiB` / `300` line cap.

## Parse Evidence

| Check | Result |
| --- | --- |
| Local parser | Node `yaml` package |
| Parse status | PASS |
| Parsed top-level type | object/map |
| Top-level key count | 12 |

Top-level keys observed:

- `policyVersion`
- `rolloutMode`
- `models`
- `toolPolicies`
- `executionProfiles`
- `hostRoutes`
- `approvalRules`
- `escalationRules`
- `memoryHealth`
- `telemetryAlerts`
- `telemetryAlertDeliveryAlerts`
- `telemetryAlertDeliveryWindow`

## Structure Summary

| Section | Evidence |
| --- | --- |
| `models` | map with 5 profile keys: `read_only`, `small_edit`, `engineering`, `high_risk`, `release_external_action` |
| `toolPolicies` | map with the same 5 profile keys |
| `executionProfiles` | map with the same 5 profile keys |
| `hostRoutes` | map with the same 5 profile keys |
| `approvalRules.protectedBranches` | array length 2 |
| `approvalRules.protectedKeywords` | array length 8 |
| `approvalRules.protectedToolAccess` | array length 1 |
| `escalationRules` | map with keys `failureThreshold`, `contextPressureThreshold`, `highRiskSticky` |
| `memoryHealth.packByToolAccess` | map with keys `read_only`, `local_write`, `engineering_write`, `protected_remote` |
| `memoryHealth.packs` | map with keys `read_only`, `local_write`, `engineering`, `release` |
| `telemetryAlerts.presetByToolAccess` | map with keys `read_only`, `local_write`, `engineering_write`, `protected_remote` |
| `telemetryAlerts.presets` | map with keys `read_only`, `local_write`, `engineering`, `release` |
| `telemetryAlertDeliveryAlerts.presetByToolAccess` | map with keys `read_only`, `local_write`, `engineering_write`, `protected_remote` |
| `telemetryAlertDeliveryAlerts.presets` | map with keys `read_only`, `local_write`, `engineering`, `release` |
| `telemetryAlertDeliveryWindow` | map with keys `defaultPreset`, `presetByToolAccess`, `presets` |

## Redacted Secret-Like Review

This evidence did not print YAML scalar values except non-secret structural
labels and map keys.

| Scan | Result |
| --- | --- |
| Broad secret-like keyword scan | 2 redacted line hits |
| Strict `sk-...` long token shape | 0 |
| Strict `Bearer ...` token shape | 0 |
| Strict secret/token/password/credential/api-key assignment shape | 0 |

Broad-scan notes:

- line 19 matched an overly broad `sk-` detector and was treated as a redacted
  non-acceptance note, not live-secret evidence
- line 35 matched the literal policy keyword `secret` inside a protected keyword
  list, not a secret value

## Not Evaluated

- YAML semantic correctness
- policy behavior
- router behavior
- runtime behavior
- loader behavior
- consumer integration
- package scripts, tests, builds, typechecks, validators, canaries, sync, deploy,
  network, or remote actions
- sibling files, lockfiles, source code, hidden files, or deferred Markdown files

## Result

`governance/codex-router/routing-policy.yaml` passed exact-file bounded local
YAML parse-only evidence collection. This does not grant router, runtime,
loader, or consumer acceptance.

Marker:

```text
PHASE_8_ROUTING_POLICY_YAML_READ_PARSE_EVIDENCE_COLLECTED_PARSE_ONLY_NO_EXECUTION
```
