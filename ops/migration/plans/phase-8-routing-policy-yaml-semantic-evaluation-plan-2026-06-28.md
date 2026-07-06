# Phase 8 Routing Policy YAML Semantic Evaluation Plan

Date: 2026-06-28

Status: plan only.

Revision note: reviewed and tightened on 2026-06-29.

This document plans a semantic evaluation gate for
`governance/codex-router/routing-policy.yaml` after the YAML read/parse-only
track closed. It does not perform semantic evaluation, execute router code,
runtime, loader, package scripts, tests, builds, typechecks, validators, sync,
deploy, network, or remote actions.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-closeout-receipt-2026-06-28.md` | `91b92db8f9f57639ddf2fba352f4b5bd79dbe4b3ccbf0a226dc841a72368dbb4` | Confirms YAML parse-only evidence closed with semantic evaluation deferred. |
| `ops/migration/inventory/phase-8-routing-policy-yaml-read-parse-evidence-2026-06-28.md` | `76ffaa19bb41aeec7b139dbcca9fb6de73e1d8d04c202a84bc799851a33aa618` | Provides parse status, top-level keys, section shapes, and redacted secret-like notes. |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-evidence-receipt-2026-06-28.md` | `33b8e27e664566dd8dc6a2ca7392f08c6d35e3daf25dd73d2f874d69196bfcde` | Confirms parse-only evidence was received without behavior acceptance. |
| `ops/migration/plans/phase-8-routing-policy-yaml-read-parse-gate-plan-2026-06-28.md` | `e81d9b304aeac5298a61b6703cd8282ea92a7f9b5775949dad02d0303baf009b` | Defines exact-file read/parse boundary and no-execution limits. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Exact YAML source to evaluate in a future evidence step. |

## Future Targets

| Future target | Intended purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-preflight-receipt-2026-06-28.md` | Confirm input hashes, target absence, parser availability, and rule boundary before evaluation. |
| `ops/migration/inventory/phase-8-routing-policy-yaml-semantic-evaluation-evidence-2026-06-28.md` | Record rule-by-rule static semantic evaluation evidence. |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-evidence-receipt-2026-06-28.md` | Record evidence creation, pass/warn/fail counts, and limits. |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-closeout-receipt-2026-06-28.md` | Close the semantic evaluation track without router/runtime behavior acceptance. |

## Evaluation Boundary

The future semantic evaluation may:

- parse the exact YAML file locally
- inspect scalar values from the parsed YAML structure
- compute rule results from the parsed object
- redact values for any secret-like keys or token-like shapes
- report PASS, WARN, FAIL, DEFERRED, and NOT_EVALUATED counts

The future semantic evaluation must not:

- execute router code or package scripts
- run validators, tests, builds, typechecks, canaries, sync, deploy, network, or
  remote actions
- read sibling files, source files, lockfiles, hidden files, runtime files, or
  loader files
- modify `routing-policy.yaml`
- normalize or rewrite policy values
- infer runtime behavior from static policy shape

## Rule Classes

| Rule class | Purpose | Planned result level |
| --- | --- | --- |
| `S1_REQUIRED_SCHEMA` | Confirm required top-level sections exist and have expected map/scalar/array shapes. | FAIL if missing or wrong type. |
| `S2_PROFILE_SET_ALIGNMENT` | Confirm `models`, `toolPolicies`, `executionProfiles`, and `hostRoutes` expose the same profile key set. | FAIL on missing/extra profile keys. |
| `S3_REFERENCE_INTEGRITY` | Confirm mapping values point to defined local sections where references are explicit. | FAIL on dangling references; WARN when a reference domain is implied but not formally declared. |
| `S4_THRESHOLD_TYPES_AND_RANGES` | Confirm threshold fields are finite numbers or booleans where expected, and apply static range rules for counts and rates. | FAIL on wrong type, non-finite number, negative count, non-integer count, or rate outside `0..1`; WARN only when the field domain is syntactically valid but not declared by this plan. |
| `S5_PROTECTION_COVERAGE` | Confirm protected branch/keyword/tool-access arrays are arrays of strings with non-empty, trim-stable, unique items. | FAIL on wrong type, empty array, non-string item, or trim-empty item; WARN on duplicate items after trimming. |
| `S6_PRESET_MAPPING_INTEGRITY` | Confirm telemetry and memory mapping values resolve to declared packs/presets. | FAIL on dangling values. |
| `S7_RISK_ORDERING_STATIC_ONLY` | Check whether profile names preserve a static low-to-high order where comparable. | WARN only unless explicit ordering semantics are declared in YAML. |
| `S8_REDACTED_SECRET_SHAPE_RECHECK` | Re-run strict live-secret shape checks while redacting broad keyword hits. | FAIL on strict live-secret shapes; WARN on broad keyword-only hits. |
| `S9_BEHAVIOR_CLAIM_GUARD` | Confirm evidence wording does not upgrade static policy evaluation into behavior acceptance. | FAIL if evidence claims router/runtime/loader acceptance. |
| `S10_SCALAR_DOMAIN_SANITY` | Confirm required scalar values are non-empty strings and check locally declared allowlists when available. | FAIL on missing or empty required scalars; WARN or DEFERRED when a value domain is not declared in this YAML-only plan. |
| `S11_NESTED_PACK_PRESET_SCHEMA` | Confirm declared memory packs and telemetry presets have the expected nested maps and typed leaf fields. | FAIL on missing nested map, empty nested map, wrong leaf type, or invalid count/rate/window range. |

## Planned Required Sections

Future evaluation should treat these sections as required because parse-only
evidence observed them as the top-level policy structure:

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

## Planned Cross-Reference Checks

| Source path | Target domain | Rule |
| --- | --- | --- |
| `memoryHealth.packByToolAccess.*` | `memoryHealth.packs` keys | Every mapped pack must exist. |
| `telemetryAlerts.presetByToolAccess.*` | `telemetryAlerts.presets` keys | Every mapped preset must exist. |
| `telemetryAlertDeliveryAlerts.presetByToolAccess.*` | `telemetryAlertDeliveryAlerts.presets` keys | Every mapped preset must exist. |
| `telemetryAlertDeliveryWindow.presetByToolAccess.*` | `telemetryAlertDeliveryWindow.presets` keys | Every mapped preset must exist. |
| `models` / `toolPolicies` / `executionProfiles` / `hostRoutes` | shared profile set | Profile keys should match exactly unless future evidence identifies an explicit exception. |

## Planned Protection Array Checks

| Path | Static rule | Severity |
| --- | --- | --- |
| `approvalRules.protectedBranches` | Must be a non-empty array of strings. Each item must be unchanged by trim except for allowed surrounding whitespace normalization in evidence, and each trimmed item must be non-empty. | FAIL on missing array, empty array, non-string item, or trim-empty item; WARN on duplicate trimmed values. |
| `approvalRules.protectedKeywords` | Must be a non-empty array of strings. Each trimmed item must be non-empty. | FAIL on missing array, empty array, non-string item, or trim-empty item; WARN on duplicate trimmed values. |
| `approvalRules.protectedToolAccess` | Must be a non-empty array of strings. Each trimmed item must be non-empty. | FAIL on missing array, empty array, non-string item, or trim-empty item; WARN on duplicate trimmed values. |

## Planned Scalar And Threshold Checks

| Field family | Static rule | Severity |
| --- | --- | --- |
| `policyVersion` | Must be a non-empty string. Version format/domain is WARN unless explicitly declared in YAML. | FAIL on missing, non-string, or empty value. |
| `rolloutMode` | Must be a non-empty string. Allowed rollout values are not inferred from router code in this gate. | FAIL on missing, non-string, or empty value; WARN if domain remains undeclared. |
| `models.*` | Each profile value must be a non-empty string. Model identity validity is not accepted without a separate model/source authority gate. | FAIL on missing, non-string, or empty value; DEFERRED for external model availability. |
| `toolPolicies.*` | Each profile value must be a non-empty string and must not claim tool behavior execution. | FAIL on missing, non-string, or empty value. |
| `executionProfiles.*` | Each profile value must be a non-empty string. Runtime behavior remains deferred. | FAIL on missing, non-string, or empty value. |
| `hostRoutes.*` | Each profile value must be a non-empty string. Host routing behavior remains deferred. | FAIL on missing, non-string, or empty value. |
| Count fields such as `failures`, `timeouts`, `retries`, `maxRejectedWrites`, `maxShadowReconcileCount` | Must be finite non-negative integers. | FAIL on negative, fractional, non-finite, or non-number values. |
| Rate fields such as `failureRate`, `timeoutRate`, and per-sink rate thresholds | Must be finite numbers from `0` through `1`, inclusive. | FAIL outside `0..1`, non-finite, or non-number values. |
| Ratio-like pressure fields such as `contextPressureThreshold` | Must be finite numbers from `0` through `1`, inclusive. | FAIL outside `0..1`, non-finite, or non-number values. |
| Generic threshold fields such as `failureThreshold` when no tighter field family applies | Must be finite non-negative numbers. | FAIL on negative, non-finite, or non-number values; WARN if integer-ness is not declared. |
| Boolean guard fields such as `highRiskSticky` | Must be boolean. | FAIL on non-boolean value. |
| Window fields such as `dedupeWindowMs` and `cooldownWindowMs` | Must be finite non-negative integers. | FAIL on negative, fractional, non-finite, or non-number values. |

## Planned Nested Pack And Preset Schema Checks

| Section | Required nested shape | Severity |
| --- | --- | --- |
| `memoryHealth.packs.*` | Each pack must be a map with non-empty `health` and `guidance` maps. | FAIL on missing map, empty map, or wrong type. |
| `memoryHealth.packs.*.health` | Required leaf fields: `overviewUnavailableSeverity`, `codexMcpUnavailableSeverity`, `maxRejectedWrites`, `rejectedWritesSeverity`, `maxShadowReconcileCount`, `shadowReconcileSeverity`, `recallUnavailableSeverity`, `nonActiveRecallSeverity`. Severity fields must be non-empty strings; max count fields must be finite non-negative integers. | FAIL on missing field, wrong type, empty string, or invalid count. |
| `memoryHealth.packs.*.guidance` | Required leaf fields: `memoryRequired`, `resumeExpected`, `telemetryMandatory`, `checkpointFrequency`. Boolean fields must be booleans; `checkpointFrequency` must be a non-empty string. | FAIL on missing field, wrong type, or empty string. |
| `telemetryAlerts.presets.*` | Each preset must be a map with non-empty `warn` and `error` maps. | FAIL on missing map, empty map, or wrong type. |
| `telemetryAlertDeliveryAlerts.presets.*` | Each preset must be a map with non-empty `warn` and `error` maps. | FAIL on missing map, empty map, or wrong type. |
| `telemetryAlerts.presets.*.{warn,error}` and `telemetryAlertDeliveryAlerts.presets.*.{warn,error}` | `totals` and `perSink` are optional nested maps, but if present they must be non-empty maps whose leaf fields obey count/rate rules. | FAIL on wrong type, empty present map, invalid count, or invalid rate. |
| `telemetryAlertDeliveryWindow.presets.*` | Each preset must be a map with `dedupeWindowMs` and `cooldownWindowMs`. | FAIL on missing field, wrong type, negative, fractional, non-finite, or non-number value. |

## Planned Severity Rules

| Severity | Meaning |
| --- | --- |
| PASS | Rule is statically satisfied by the parsed YAML object. |
| WARN | Rule is syntactically satisfiable but semantically incomplete, unusual, or dependent on behavior not evaluated here. |
| FAIL | Rule violates a local static invariant and should block static semantic acceptance. |
| DEFERRED | Rule needs router/runtime/loader execution, source-code behavior, lockfile review, or consumer integration. |
| NOT_EVALUATED | Rule was outside the authorized semantic evaluation scope. |

## Future Preflight Requirements

The next preflight must confirm:

- this plan hash
- all input hashes are stable
- all future targets are absent
- `routing-policy.yaml` hash is stable
- `routing-policy.yaml` remains a regular file with mode `644`
- `routing-policy.yaml` remains under the exact-file cap of `16 KiB` and `300`
  lines
- local YAML parser is available
- semantic evaluation will be exact-file, static, and local only
- output will redact secret-like scalar values
- no router/runtime/loader behavior acceptance will be granted

## Stop Conditions

Stop if:

- any input hash drifts
- any future target already exists
- YAML parser availability cannot be confirmed
- semantic evaluation would require reading files outside
  `governance/codex-router/routing-policy.yaml`
- any rule requires executing router code, runtime, loader, package scripts,
  validators, tests, builds, typechecks, sync, deploy, network, or remote actions
- evidence would disclose secret-like scalar values
- the result would be framed as router, runtime, loader, or consumer acceptance

## Acceptance Boundary

This plan can support only a future static YAML semantic evaluation gate. Even
if all semantic rules return PASS, the strongest possible outcome is:

`STATIC_YAML_SEMANTIC_ACCEPTANCE_WITH_RUNTIME_AND_ROUTER_BEHAVIOR_DEFERRED`.

It cannot grant:

- router behavior acceptance
- runtime behavior acceptance
- loader behavior acceptance
- package script, validator, test, build, typecheck, canary, sync, deploy,
  network, or remote execution
- full consumer integration acceptance
- migration, rewrite, normalization, or policy edit authorization

## Result

YAML semantic evaluation planning is complete. The next safe step is a formal
preflight receipt that confirms hashes, target absence, parser availability,
rule boundaries, and no-execution limits before collecting semantic evidence.

Marker:

```text
PHASE_8_ROUTING_POLICY_YAML_SEMANTIC_EVALUATION_PLAN_CREATED_NO_EVALUATION
```
