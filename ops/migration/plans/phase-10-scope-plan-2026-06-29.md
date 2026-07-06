# Phase 10 Scope Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document opens Phase 10 after the limited Phase 9 local validation
closeout. Phase 10 focuses on consumer/runtime integration readiness and then
broader host/provider behavior gates, while continuing to keep package scripts,
real smoke, canary, remote, deploy, and dependency gates separate.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-closeout-receipt-2026-06-29.md` | `bb42ff255eb132ae38b835196b4a52422ec1e4406d5bd102629a8ef6d42fc348` | Phase 9 limited closeout authority. |
| `ops/migration/plans/phase-9-closeout-readiness-plan-2026-06-29.md` | `764090f15b77635c2deabf1f50d49b630fe439bbb5c4af2a894f9d74a7cc9f7e` | Phase 9 gates carried forward. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-10-scope-plan-2026-06-29.md` | absent |
| `ops/migration/plans/phase-10-consumer-runtime-integration-readiness-plan-2026-06-29.md` | absent |

`governance/codex-router` status at scope check: clean.

Current `governance/codex-router` HEAD:

```text
88b84c66e7c815ca5797507c9e957cf5ad38eba2
```

## Phase 10 Goal

Phase 10 should convert Phase 9's narrow local evidence into carefully scoped
consumer/runtime readiness evidence.

The first track should be:

```text
PHASE_10_CONSUMER_RUNTIME_INTEGRATION_READINESS
```

This track should start with static/narrow local tests and avoid broad command
surfaces until a preflight proves them safe.

## Candidate Tracks

| Track | Candidate surfaces | Phase 10 decision |
| --- | --- | --- |
| Consumer/runtime integration readiness | `formal-readonly-cli-integration-readiness.test.ts`, `readonly-formal-integration-readiness-matrix-audit.test.ts`, local runtime/consumer tests | Start here. |
| Host/provider broader behavior | `host-dispatcher.test.ts`, `provider-*.test.ts`, `desktop-host-client.test.ts` | Later in Phase 10 after readiness evidence. |
| Broad package test | `npm test` / `tsx --test tests/*.test.ts` | Defer; too broad for first Phase 10 gate. |
| Smoke/canary | `smoke:*`, `canary:*` scripts | Defer to separate explicit gate. |
| Dependency/security/freshness | install/audit/registry surfaces | Defer to dependency track. |
| Actual workspace state-sync write | repository-root state-sync write behavior | Defer to separate workspace-write gate. |
| Remote/release/deploy/sync | remote or external operations | Out of scope for local Phase 10 opening. |

## First Gate Requirements

The first Phase 10 gate must:

- name exact candidate files and commands
- confirm target evidence/receipt files are absent
- check that selected tests avoid network, real CLI, env credentials, dependency
  install/audit, repository-root writes, remote, deploy, smoke, and canary
  behavior
- use direct local binaries rather than npm scripts
- produce evidence and receipts with explicit acceptance boundaries
- avoid claiming full consumer/runtime acceptance from narrow tests

## Result

Phase 10 is opened. The next safe step is a consumer/runtime integration
readiness plan that chooses one narrow local readiness exact-run candidate.

Marker:

```text
PHASE_10_SCOPE_PLAN_CREATED_CONSUMER_RUNTIME_READINESS_FIRST
```
