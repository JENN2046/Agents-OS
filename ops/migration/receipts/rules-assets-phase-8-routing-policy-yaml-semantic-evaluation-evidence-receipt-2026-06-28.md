# Phase 8 Routing Policy YAML Semantic Evaluation Evidence Receipt

Date: 2026-06-29

Status: evidence receipt created.

Decision: `YAML_SEMANTIC_EVALUATION_EVIDENCE_RECEIVED_STATIC_ONLY_NO_FAIL`.

This receipt records the static semantic evaluation evidence for
`governance/codex-router/routing-policy.yaml`. It accepts the evidence as
static parsed-object rule evidence only. It does not grant router behavior,
runtime, loader, or consumer acceptance.

## Inputs Reviewed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-routing-policy-yaml-semantic-evaluation-plan-2026-06-28.md` | `ef1e5bed91f06a54d6223edd2e81bf4d88b1c06bb6f85015d39fe8216cd4c281` | stable |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-preflight-receipt-2026-06-28.md` | `a79d52df4add819ce2cec50832ff9c5efa29a25b8d6d55eea53d3662daf4dde8` | stable |
| `ops/migration/inventory/phase-8-routing-policy-yaml-semantic-evaluation-evidence-2026-06-28.md` | `0784055dd23fb0f943cf422fc0a6b934c539204807567af7555c76deab79a74f` | stable |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-evidence-receipt-2026-06-28.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-semantic-evaluation-closeout-receipt-2026-06-28.md` | absent |

## Evidence Received

| Evidence item | Result |
| --- | --- |
| Parse status | PASS |
| Static semantic rule count | 11 |
| PASS count | 8 |
| WARN count | 3 |
| FAIL count | 0 |
| Rule-level DEFERRED count | 0 |
| Rule-level NOT_EVALUATED count | 0 |

## Warnings Carried Forward

| Rule | Warning |
| --- | --- |
| `S7_RISK_ORDERING_STATIC_ONLY` | Static profile order is visible, but executable ordering semantics are not accepted from YAML alone. |
| `S8_REDACTED_SECRET_SHAPE_RECHECK` | Strict live-secret shapes are 0; broad keyword-only redacted hits remain at two line numbers. |
| `S10_SCALAR_DOMAIN_SANITY` | `policyVersion`, `rolloutMode`, and model availability domains remain outside this YAML-only authority. |

## Limits Carried Forward

- This receipt accepts evidence only as static semantic evidence.
- It does not authorize edits to `routing-policy.yaml`.
- It does not authorize YAML migration, rewrite, or normalization.
- It does not grant router/runtime/loader behavior acceptance.
- It does not grant consumer integration acceptance.
- It does not authorize package scripts, validators, tests, builds, typechecks,
  canaries, sync, deploy, network, or remote actions.

## Result

Semantic evaluation evidence is received with `0` FAIL results and 3 warnings
carried forward. The next safe step is a closeout receipt for this static YAML
semantic evaluation track.

Marker:

```text
PHASE_8_ROUTING_POLICY_YAML_SEMANTIC_EVALUATION_EVIDENCE_RECEIPT_CREATED_STATIC_ONLY_NO_FAIL
```
