# Phase 8 Routing Policy YAML Semantic Evaluation Evidence

Date: 2026-06-29

Status: evidence collected.

Scope: exact-file static semantic evaluation for
`governance/codex-router/routing-policy.yaml`, following
`phase-8-routing-policy-yaml-semantic-evaluation-plan-2026-06-28.md`.

No router code, runtime, loader, package scripts, tests, builds, typechecks,
validators, sync, deploy, network, or remote actions were executed.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-routing-policy-yaml-semantic-evaluation-plan-2026-06-28.md` | `ef1e5bed91f06a54d6223edd2e81bf4d88b1c06bb6f85015d39fe8216cd4c281` | stable |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-preflight-receipt-2026-06-28.md` | `a79d52df4add819ce2cec50832ff9c5efa29a25b8d6d55eea53d3662daf4dde8` | stable |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | parsed and evaluated |

## Evaluation Method

| Item | Result |
| --- | --- |
| Parser | local Node `yaml` package |
| Parse status | PASS |
| Evaluation type | static parsed-object rule evaluation |
| Rule count | 11 |
| Output policy | redacted; no secret-like scalar values printed |

## Result Counts

| Result | Count |
| --- | --- |
| PASS | 8 |
| WARN | 3 |
| FAIL | 0 |
| DEFERRED | 0 rule-level results; 5 model-availability notes deferred inside `S10` |
| NOT_EVALUATED | 0 rule-level results |

## Rule Results

| Rule | Result | Evidence summary |
| --- | --- | --- |
| `S1_REQUIRED_SCHEMA` | PASS | Required top-level sections and expected types are present. |
| `S2_PROFILE_SET_ALIGNMENT` | PASS | `models`, `toolPolicies`, `executionProfiles`, and `hostRoutes` share the same 5 profile keys. |
| `S3_REFERENCE_INTEGRITY` | PASS | Declared memory pack and telemetry preset references resolve locally. |
| `S4_THRESHOLD_TYPES_AND_RANGES` | PASS | Threshold, count, rate, window, and boolean guard fields satisfy static type/range checks. |
| `S5_PROTECTION_COVERAGE` | PASS | Protected branch/keyword/tool-access arrays are non-empty string arrays with non-empty trimmed unique items. |
| `S6_PRESET_MAPPING_INTEGRITY` | PASS | Pack and preset mappings resolve to declared pack/preset maps. |
| `S7_RISK_ORDERING_STATIC_ONLY` | WARN | Expected low-to-high profile order is observed, but ordering semantics are not declared in YAML and are not accepted as behavior. |
| `S8_REDACTED_SECRET_SHAPE_RECHECK` | WARN | Strict live-secret shapes are 0; broad keyword-only hits remain redacted warnings at lines 19 and 35. |
| `S9_BEHAVIOR_CLAIM_GUARD` | PASS | Evidence remains static-only and does not claim router/runtime/loader acceptance. |
| `S10_SCALAR_DOMAIN_SANITY` | WARN | Required scalars are non-empty; `policyVersion` and `rolloutMode` domains are undeclared in this YAML-only gate; 5 model availability checks remain deferred. |
| `S11_NESTED_PACK_PRESET_SCHEMA` | PASS | Memory packs and telemetry presets satisfy planned nested schema checks. |

## Profile Alignment Evidence

The following profile key set was observed across `models`, `toolPolicies`,
`executionProfiles`, and `hostRoutes`:

- `read_only`
- `small_edit`
- `engineering`
- `high_risk`
- `release_external_action`

Result: profile key sets align. This does not grant runtime routing behavior
acceptance.

## Reference Integrity Evidence

| Mapping family | Result |
| --- | --- |
| `memoryHealth.packByToolAccess.*` to `memoryHealth.packs` | PASS |
| `memoryHealth.defaultPack` to `memoryHealth.packs` | PASS |
| `telemetryAlerts.presetByToolAccess.*` to `telemetryAlerts.presets` | PASS |
| `telemetryAlerts.defaultPreset` to `telemetryAlerts.presets` | PASS |
| `telemetryAlertDeliveryAlerts.presetByToolAccess.*` to `telemetryAlertDeliveryAlerts.presets` | PASS |
| `telemetryAlertDeliveryAlerts.defaultPreset` to `telemetryAlertDeliveryAlerts.presets` | PASS |
| `telemetryAlertDeliveryWindow.presetByToolAccess.*` to `telemetryAlertDeliveryWindow.presets` | PASS |
| `telemetryAlertDeliveryWindow.defaultPreset` to `telemetryAlertDeliveryWindow.presets` | PASS |

## Warning Notes

| Warning | Reason |
| --- | --- |
| `S7_RISK_ORDERING_STATIC_ONLY` | Static profile order is visible, but YAML alone does not declare executable routing precedence. |
| `S8_REDACTED_SECRET_SHAPE_RECHECK` | Broad keyword-only hits remain at two redacted line numbers; strict token/assignment shapes are 0. |
| `S10_SCALAR_DOMAIN_SANITY` | Domain validity for `policyVersion`, `rolloutMode`, and external model availability needs separate authority or runtime/source evidence. |

## Not Granted

- YAML policy edit authorization
- YAML migration, rewrite, or normalization
- router behavior acceptance
- runtime behavior acceptance
- loader behavior acceptance
- consumer integration acceptance
- package script execution
- validators, tests, builds, typechecks, canaries, sync, deploy, network, or
  remote actions

## Result

Static YAML semantic evaluation completed with `0` FAIL results. The strongest
supported result is static semantic acceptance with warnings and runtime/router
behavior deferred.

Marker:

```text
PHASE_8_ROUTING_POLICY_YAML_SEMANTIC_EVALUATION_EVIDENCE_COLLECTED_STATIC_ONLY_NO_EXECUTION
```
