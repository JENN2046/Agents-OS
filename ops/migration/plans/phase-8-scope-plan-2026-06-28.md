# Phase 8 Scope Plan

Date: 2026-06-28

Status: plan only.

This document opens Phase 8 after Phase 7 closed the static read-only
runtime/loader boundary evidence track. Phase 8 handles deferred parser/semantic,
behavior, and integration gates without treating Phase 7 static evidence as
runtime or loader acceptance.

## Inputs Rechecked Before Plan Creation

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-phase-7-closeout-receipt-2026-06-28.md` | `2a9884d9e23ca865155883d4313773682c317649789c51b45f8cdadc2d10fcfb` | Confirms Phase 7 closed static read-only boundary evidence only. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-content-read-evidence-review-closeout-receipt-2026-06-28.md` | `a364279d65fc813f33082e354274cd5de9575b602d830ea7d3439e6ba1e81dff` | Confirms limited content-read evidence was accepted only as static boundary evidence. |
| `ops/migration/inventory/phase-7-runtime-loader-limited-content-read-evidence-2026-06-28.md` | `cae14ba07918d251130514dba0da47a33da69f3ab8d8b3ba3f9002e6d8cf1138` | Provides bounded static content-read evidence. |
| `ops/migration/receipts/rules-assets-phase-7-runtime-loader-limited-content-read-evidence-receipt-2026-06-28.md` | `a52b8e1688553d5f6613d78508ffaf49c23249a1175fda9649af89222538c8e3` | Confirms bounded content-read collection boundaries. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-8-scope-plan-2026-06-28.md` | absent |
| `ops/migration/plans/phase-8-parser-semantic-review-gate-plan-2026-06-28.md` | absent |
| `ops/migration/receipts/rules-assets-phase-8-parser-semantic-review-preflight-receipt-2026-06-28.md` | absent |

## Phase 8 Goal

Phase 8 should turn Phase 7 static evidence into carefully staged next gates:

- parser/semantic review gates for already read or deferred files
- runtime/loader behavior validation planning gates
- governance router behavior validation planning gates
- consumer integration validation planning gates

Phase 8 must not upgrade static evidence into behavior acceptance.

## First Track Choice

| Candidate track | Risk | Decision |
| --- | --- | --- |
| Parser/semantic review gate | Lower than behavior execution; can be planned and preflighted without running code. | Start here. |
| Runtime/loader behavior validation gate | Higher; may require executing scripts or runtime/loader code. | Plan later, stop before execution. |
| Governance router behavior validation gate | Higher; may require test/build/script execution. | Plan later, stop before execution. |
| Consumer integration validation gate | Higher; may require broader cross-surface checks. | Plan later. |

## Phase 8 Operating Boundary

Allowed automatically:

- planning-only documents
- preflights that read existing receipts/plans/evidence
- local read-only file inspection
- local parsing of already allowlisted files when a parser/semantic gate has a
  plan and preflight
- closeout receipts that do not execute code or modify source assets

Not automatic:

- executing runtime, loader, tests, builds, package scripts, validators, sync, or
  deploy commands
- remote or network actions
- modifying runtime, router, extension, execution, or governance source assets
- accepting runtime/loader/router behavior
- accepting full consumer integration
- writing secrets or changing env files

## Phase 8 First Gate

The first gate is:

`phase-8-parser-semantic-review-gate-plan-2026-06-28.md`

It should decide:

- which already-read static evidence can be semantically reviewed from evidence
  only
- which files require structured parsing
- which deferred files remain out of scope
- which parsing actions are safe local read-only actions
- which semantic conclusions are allowed and which remain deferred

## Deferred Gates Carried Into Phase 8

- Revised-cap or section-scoped read planning for `governance/codex-router/AGENTS.md`.
- Revised-cap or section-scoped read planning for `governance/codex-router/PROJECT_CONTINUE_ANCHOR.md`.
- Revised-cap or section-scoped read planning for `governance/codex-router/README.md`.
- YAML-specific read/parse authorization for `governance/codex-router/routing-policy.yaml`.
- Lockfile-specific gate for `governance/codex-router/package-lock.json`.
- Runtime/loader behavior validation.
- Governance router behavioral validation.
- Full consumer integration validation.
- Any package script, build, typecheck, test, sync, deploy, network, or remote action.

## Acceptance Boundary

Phase 8 planning can admit parser/semantic evidence or behavior validation plans.
It cannot by itself grant:

- parse or semantic acceptance
- runtime behavior acceptance
- loader behavior acceptance
- governance router acceptance
- package script execution
- build/typecheck/test execution
- full consumer integration acceptance
- migration, rewrite, or normalization authorization

## Result

Phase 8 is opened. The first safe track is parser/semantic review planning and
preflight, while behavior execution and integration validation remain deferred.

Marker:

```text
PHASE_8_SCOPE_PLAN_CREATED_PARSER_SEMANTIC_REVIEW_FIRST_NO_EXECUTION
```
