# Phase 8 Routing Policy YAML Read/Parse Closeout Receipt

Date: 2026-06-28

Status: closed.

Decision: `ROUTING_POLICY_YAML_PARSE_ONLY_CLOSED_ACCEPTED_WITH_LIMITS`.

This receipt closes the Phase 8 file-specific YAML read/parse track for
`governance/codex-router/routing-policy.yaml`. It accepts only local bounded
YAML parse-only evidence. It does not grant YAML semantic acceptance, router
behavior acceptance, runtime acceptance, loader acceptance, or consumer
integration acceptance.

## Inputs Reviewed

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-8-routing-policy-yaml-read-parse-gate-plan-2026-06-28.md` | `e81d9b304aeac5298a61b6703cd8282ea92a7f9b5775949dad02d0303baf009b` | stable |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-preflight-receipt-2026-06-28.md` | `4acb630b26aaedce72706b146aff60c977e765af12e5781d7dae2dd46913e5b6` | stable |
| `ops/migration/inventory/phase-8-routing-policy-yaml-read-parse-evidence-2026-06-28.md` | `76ffaa19bb41aeec7b139dbcca9fb6de73e1d8d04c202a84bc799851a33aa618` | stable |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-evidence-receipt-2026-06-28.md` | `33b8e27e664566dd8dc6a2ca7392f08c6d35e3daf25dd73d2f874d69196bfcde` | stable |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-routing-policy-yaml-read-parse-closeout-receipt-2026-06-28.md` | absent before creation |

## Three-Way Review

| Source | Expected | Observed | Result |
| --- | --- | --- | --- |
| Gate plan | Exact-file bounded read and YAML parse-only evidence for `routing-policy.yaml` | Evidence used the exact path only and stayed under cap | aligned |
| Preflight receipt | Confirm hashes, target absence, file cap, parser availability, and no-execution boundary | All recorded before evidence collection | aligned |
| Evidence + evidence receipt | Record parse status, structure summary, redacted secret-like review, and limits | Parse status PASS; top-level structure recorded; strict live-secret shapes 0; limits carried forward | aligned |

## Accepted With Limits

| Topic | Accepted result | Limit |
| --- | --- | --- |
| `routing-policy.yaml` YAML syntax parse | PASS | Parse-only; no semantic acceptance. |
| File cap | PASS | Exact file only; no sibling files or hidden files. |
| Structure inventory | PASS | Structural evidence only; no behavior acceptance. |
| Redacted secret-like review | PASS_STATIC_REDACTED | Not a full secret audit; no scalar values disclosed. |

## Deferred Gates

- YAML semantic evaluation against an explicit rule plan.
- Governance router behavior validation.
- Runtime behavior validation.
- Loader behavior validation.
- Package script, validator, build, typecheck, test, canary, sync, deploy,
  network, or remote execution.
- Lockfile-specific review for `governance/codex-router/package-lock.json`.
- Revised-cap or section-scoped Markdown gates for `AGENTS.md`,
  `PROJECT_CONTINUE_ANCHOR.md`, and `README.md`.
- Full consumer integration validation.

## Not Granted

- migration, rewrite, normalization, or policy edits
- YAML semantic acceptance
- router/runtime/loader behavior acceptance
- consumer integration acceptance
- execution authorization of any command
- remote, network, sync, deploy, or external action

## Result

The Phase 8 routing policy YAML read/parse track is closed as parse-only
evidence accepted with limits. Remaining Phase 8 work must proceed through
separate gates for YAML semantic evaluation, lockfile review, deferred Markdown
review, or command-specific behavior validation.

Marker:

```text
PHASE_8_ROUTING_POLICY_YAML_READ_PARSE_CLOSED_PARSE_ONLY_NO_ROUTER_ACCEPTANCE
```
