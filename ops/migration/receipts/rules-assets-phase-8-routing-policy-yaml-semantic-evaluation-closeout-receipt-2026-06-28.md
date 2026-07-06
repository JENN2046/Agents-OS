# Phase 8 Routing Policy YAML Semantic Evaluation Closeout Receipt

Date: 2026-06-29

Status: closed.

Decision: `STATIC_YAML_SEMANTIC_EVALUATION_CLOSED_NO_FAIL_WITH_WARNINGS`.

This receipt closes the Phase 8 static YAML semantic evaluation track for
`governance/codex-router/routing-policy.yaml`. It accepts only static semantic
evidence with warnings. It does not grant router behavior, runtime, loader, or
consumer integration acceptance.

## Inputs Reviewed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-routing-policy-yaml-semantic-evaluation-plan-2026-06-28.md` | `ef1e5bed91f06a54d6223edd2e81bf4d88b1c06bb6f85015d39fe8216cd4c281` | stable |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-preflight-receipt-2026-06-28.md` | `a79d52df4add819ce2cec50832ff9c5efa29a25b8d6d55eea53d3662daf4dde8` | stable |
| `ops/migration/inventory/phase-8-routing-policy-yaml-semantic-evaluation-evidence-2026-06-28.md` | `0784055dd23fb0f943cf422fc0a6b934c539204807567af7555c76deab79a74f` | stable |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-evidence-receipt-2026-06-28.md` | `7ae878bffb9ec60f025a0b4d39e29c1975260b0d546157ff8f5843aca9dc189b` | stable |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-closeout-receipt-2026-06-28.md` | absent before creation |

## Three-Way Review

| Source | Expected | Observed | Result |
| --- | --- | --- | --- |
| Semantic evaluation plan | Evaluate S1-S11 statically, exact-file only, no execution | Evidence evaluated S1-S11 from parsed YAML object only | aligned |
| Preflight receipt | Confirm input hashes, target absence, file cap, parser availability, no-execution boundary | All recorded before evidence collection | aligned |
| Evidence + evidence receipt | Record PASS/WARN/FAIL counts and carry warnings forward | 8 PASS, 3 WARN, 0 FAIL; warnings carried forward | aligned |

## Accepted With Limits

| Topic | Accepted result | Limit |
| --- | --- | --- |
| Static YAML semantic evaluation | CLOSED_NO_FAIL_WITH_WARNINGS | Static parsed-object evidence only. |
| Required schema and profile alignment | PASS | No runtime routing behavior acceptance. |
| Reference and preset mapping integrity | PASS | Local YAML references only; no source-code behavior acceptance. |
| Threshold/range and nested schema checks | PASS | Static numeric/string/boolean checks only. |
| Protection coverage checks | PASS | Static array/string uniqueness checks only. |
| Warning handling | WARNINGS_CARRIED_FORWARD | Warnings are not waived. |

## Warnings Carried Forward

| Rule | Warning |
| --- | --- |
| `S7_RISK_ORDERING_STATIC_ONLY` | Static profile order is observed, but executable ordering semantics are not declared in YAML. |
| `S8_REDACTED_SECRET_SHAPE_RECHECK` | Strict live-secret shapes are 0; broad keyword-only redacted hits remain at two line numbers. |
| `S10_SCALAR_DOMAIN_SANITY` | `policyVersion`, `rolloutMode`, and external model availability domains need separate authority/source/runtime evidence. |

## Deferred Gates

- Governance router behavior validation.
- Runtime behavior validation.
- Loader behavior validation.
- Consumer integration validation.
- Model/source authority validation for model identifiers and external model
  availability.
- Rollout/version domain authority validation.
- Lockfile-specific review for `governance/codex-router/package-lock.json`.
- Revised-cap or section-scoped Markdown gates for `AGENTS.md`,
  `PROJECT_CONTINUE_ANCHOR.md`, and `README.md`.
- Any package script, validator, build, typecheck, test, canary, sync, deploy,
  network, or remote execution.

## Not Granted

- migration, rewrite, normalization, or policy edits
- router behavior acceptance
- runtime behavior acceptance
- loader behavior acceptance
- consumer integration acceptance
- command execution authorization
- remote, network, sync, deploy, or external action

## Result

The Phase 8 routing policy YAML semantic evaluation track is closed with no
static FAIL results and three warnings carried forward. The strongest accepted
state is static YAML semantic evidence accepted with warnings, while runtime,
router, loader, and full consumer behavior remain deferred.

Marker:

```text
PHASE_8_ROUTING_POLICY_YAML_SEMANTIC_EVALUATION_CLOSED_NO_FAIL_WITH_WARNINGS_NO_EXECUTION
```
