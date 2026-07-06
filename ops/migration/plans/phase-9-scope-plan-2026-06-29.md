# Phase 9 Scope Plan - 2026-06-29

Status: plan only; no runtime execution, loader execution, governance router
behavior validation, consumer integration validation, npm command, package
script, test, build, typecheck, dependency install, dependency audit, source
edit, sync, deploy, network, or remote action has been performed.

This document opens Phase 9 after Phase 8 closed only the static
parser/semantic, YAML, and package-lock evidence tracks. Phase 9 is the first
phase that should plan behavior gates, but every behavior gate must still pass
through command-specific preflight and explicit authorization before execution.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-8-closeout-receipt-2026-06-29.md` | `fee71fe1ef444aa220d0de4a2c41d002446a517002b832910f04e523da662289` | Phase 8 closeout authority; carries Phase 9 gates forward. |
| `ops/migration/plans/phase-8-closeout-readiness-plan-2026-06-29.md` | `faabb242c7afd27313deec7cc35de26fcba1f6cf1b8cb9875cbb37eb412c9efe` | Defines Phase 8 readiness and Phase 9 gate inventory. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | absent |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-scope-receipt-2026-06-29.md` | absent |

Workspace Git state: `/home/jenn/AGENTS_OS_Workspace` is not a Git repository.

## Phase 9 Goal

Phase 9 should convert the remaining Phase 8 deferred gates into staged,
command-specific behavior and integration plans without treating static evidence
as behavior acceptance.

Phase 9 should answer:

- which runtime/router/loader/consumer behavior gate is safe to approach first
- what exact command or read boundary each behavior gate would require
- what output redaction and failure policy each command needs
- which gates remain too broad and should stay deferred
- when static documentation authority gaps should be handled before behavior
  execution

## Operating Boundary

Allowed automatically:

- planning-only documents
- preflights that read existing receipts/plans/evidence
- local read-only inspection of already identified files
- static documentation authority planning
- command-specific authorization plans that stop before execution
- closeout receipts for planning/preflight-only gates

Not automatic:

- running runtime, loader, router, validators, npm commands, package scripts,
  tests, builds, typechecks, canaries, sync, deploy, network, or remote actions
- changing executable bits
- modifying source files, manifests, lockfiles, registry files, runtime files,
  router files, consumers, prompts, templates, or env files
- accepting runtime/router/loader/consumer behavior without execution evidence
- reading private-state, logs, caches, active env files, credentials, or broad
  project trees

## Gate Inventory

| Gate | Current authority from Phase 8 | Phase 9 handling |
| --- | --- | --- |
| Runtime behavior | Preflight existed but execution stopped. | Plan exact-run or behavior-test authorization; do not execute yet. |
| Loader behavior | Static boundary evidence only. | Plan narrow loader behavior/read/execute boundary. |
| Governance router behavior | `routing-policy.yaml` has static semantic evidence only. | Plan router behavior authorization around exact command/test surface. |
| Consumer integration | Not activated against runtime/router/loader behavior. | Plan consumer integration evidence after runtime/router/loader gates are clearer. |
| Package scripts/build/typecheck/test | Script names inventoried only. | Plan command-specific gates only when needed. |
| Dependency install/audit/freshness | Lockfile static review only. | Separate dependency/installability track if needed; likely not first. |
| Large Markdown authority files | Deferred in Phase 8. | Low-risk static documentation authority gate candidate. |
| Model/source and rollout/version authority | Deferred by YAML semantic warnings. | Static authority plan before router behavior acceptance if material. |
| Remote/sync/deploy/branch/release | Explicitly outside Phase 8. | Keep separate high-risk operational track. |

## Recommended First Phase 9 Tracks

| Candidate | Risk | Recommendation |
| --- | --- | --- |
| Static documentation authority review for `AGENTS.md`, `PROJECT_CONTINUE_ANCHOR.md`, `README.md` | Low; read-only/static. | Good first track if we want to close authority gaps before behavior. |
| Runtime/router/loader behavior gate planning | Medium; plan-only is safe, execution is gated. | Good first behavior-planning track after scope. |
| Governance router behavior exact-run | Higher; likely package command or test execution. | Do not execute until command-specific authorization exists. |
| Consumer integration validation | Higher; depends on runtime/router/loader behavior. | Plan after behavior surfaces are clearer. |
| Dependency install/audit | Higher; may need npm/network or dependency writes. | Keep separate unless installability becomes blocking. |

## First Track Decision

Recommended first track:

```text
PHASE_9_RUNTIME_ROUTER_LOADER_CONSUMER_GATE_PLANNING_FIRST_NO_EXECUTION
```

Reason:

Phase 8 already closed most static parser/semantic gaps. The biggest remaining
question is how to safely approach behavior validation. A plan-only gate can
name exact future commands, output policy, and stop conditions without executing
anything. Static Markdown authority review remains a low-risk parallel or next
track, but it should not block planning the behavior gates.

## Phase 9 Track 1 Proposed Output

If continued, create:

| Output | Purpose |
| --- | --- |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | Plan the first behavior-gate package across runtime, loader, router, and consumer surfaces; stop before execution. |

The plan should decide:

- which behavior gate is safest to preflight first
- whether any exact command is known from existing package scripts or validators
- what files can be read to identify command surfaces
- what output must be redacted
- what would remain deferred until explicit command authorization

## Phase 9 Closeout Boundary

Phase 9 should not be considered closeable until it has either:

- produced behavior-gate plans and intentionally stopped at command-specific
  authorization, or
- collected explicitly authorized behavior evidence and closed it with limits.

No Phase 9 scope document alone can grant:

- runtime behavior acceptance
- loader behavior acceptance
- governance router behavior acceptance
- consumer integration acceptance
- package script execution
- dependency installability/security/freshness acceptance
- remote or operational acceptance

## Stop Conditions

Stop before:

- executing any command beyond local read-only metadata/hash/search commands
- running npm, package scripts, validators, tests, builds, typechecks, canaries,
  sync, deploy, network, or remote actions
- changing executable bits
- editing runtime/router/loader/consumer/source files
- reading private-state, logs, caches, active env files, credentials, or broad
  project trees
- making behavior acceptance claims from static evidence

## Result

Phase 9 is opened as a behavior-gate planning phase. The recommended next safe
step is a plan-only runtime/router/loader/consumer gate plan that stops before
any command execution.

Marker:

```text
PHASE_9_SCOPE_PLAN_CREATED_BEHAVIOR_GATE_PLANNING_FIRST_NO_EXECUTION
```
