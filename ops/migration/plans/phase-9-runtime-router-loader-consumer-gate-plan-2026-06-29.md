# Phase 9 Runtime / Router / Loader / Consumer Gate Plan - 2026-06-29

Status: plan only; no runtime execution, loader execution, router behavior
validation, consumer integration validation, npm command, package script, test,
build, typecheck, dependency install, dependency audit, source edit, sync,
deploy, network, or remote action has been performed.

This document plans the first Phase 9 behavior-gate package after Phase 9 scope
opened. It classifies available command and test surfaces and chooses the next
safe gate to plan. It does not authorize or execute any command.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | Phase 9 scope authority. |
| `ops/migration/receipts/rules-assets-phase-8-closeout-receipt-2026-06-29.md` | `fee71fe1ef444aa220d0de4a2c41d002446a517002b832910f04e523da662289` | Carries runtime/router/loader/consumer gates into Phase 9. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Script and dependency surface inventory only. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Static router policy authority from Phase 8. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-runtime-router-loader-consumer-gate-plan-receipt-2026-06-29.md` | absent |

Workspace Git state: `/home/jenn/AGENTS_OS_Workspace` is not a Git repository.

## Observed Command Surface

Static `package.json` script keys and commands were read but not executed:

| Script | Static command | Phase 9 risk class |
| --- | --- | --- |
| `build` | `tsc -p tsconfig.json` | local compile; no behavior acceptance by itself |
| `governance` | `tsx scripts/run-governance-check.ts` | behavior-like governance check; requires exact authorization |
| `validate:daily` | `tsx scripts/run-governance-check.ts tier daily` | behavior-like governance check; requires exact authorization |
| `validate:pr` | `tsx scripts/run-governance-check.ts tier pr` | behavior-like governance check; requires exact authorization |
| `validate:release` | `tsx scripts/run-governance-check.ts tier release` | behavior-like governance check; requires exact authorization |
| `model:check` | `tsx scripts/check-codex-cli-models.ts` | model/source authority adjacent; may depend on environment or external model assumptions |
| `preflight:codex-cli-env` | `tsx scripts/run-codex-cli-environment-preflight.ts` | environment-sensitive; requires redaction policy |
| `smoke:contract` | `tsx scripts/run-codex-cli-contract-smoke.ts` | possible first smoke candidate after script-content review |
| `smoke:readonly:real` | `tsx scripts/run-codex-cli-real-readonly-smoke.ts` | real readonly smoke; higher sensitivity |
| `smoke:telemetry` | `tsx scripts/run-codex-cli-readonly-smoke-telemetry.ts` | telemetry-sensitive |
| `smoke:workspace-write:telemetry` | `tsx scripts/run-codex-cli-workspace-write-smoke-telemetry.ts` | write/telemetry-sensitive; not first |
| `canary` | `tsx scripts/run-canary-test.ts` | canary behavior; requires command-specific gate |
| `canary:write` | `tsx scripts/run-canary-test.ts --risk medium` | write-risk; not first |
| `canary:external` | `tsx scripts/run-canary-test.ts --risk high` | external/high-risk; not first |
| `evidence:collect` | `tsx scripts/collect-evidence.ts` | evidence collector; may read broad surfaces |
| `typecheck` | `tsc -p tsconfig.json --noEmit` | local static compile; useful support gate but not behavior acceptance |
| `test` | `tsx --test tests/*.test.ts` | broad test execution; too broad as first exact-run |

## Observed File Surface

Static file-name inventory only:

- `governance/codex-router/scripts/` contains many targeted governance,
  smoke, canary, provider, readonly, workspace-write, state-sync, and audit
  scripts.
- `governance/codex-router/tests/` contains broad package, runtime, router,
  provider, loader, governance, smoke, and acceptance-style tests.
- `governance/codex-router/packages/` contains runtime/router/loader/consumer
  adjacent packages including `runtime-control`, `routing-engine`,
  `desktop-live-adapter`, `provider-execution-runner`,
  `execution-observation`, `validation-arbiter`, and related packages.

No script body, test body, package implementation body, private state, logs,
caches, active env files, credentials, or broad project tree content is accepted
by this plan as behavior evidence.

## Gate Classification

| Gate family | Candidate surfaces | Current decision |
| --- | --- | --- |
| Runtime behavior | `runtime-control`, `run-manager`, `execution-*`, local tests | Plan exact-run authorization after reading exact candidate test/script bodies. |
| Loader behavior | `desktop-live-adapter`, provider/host packages, loader-adjacent tests | Plan narrow test/script candidate after content risk scan. |
| Governance router behavior | `routing-engine`, `strategy-router`, `routing-policy.yaml`, router tests/scripts | Plan static content risk scan before any exact run. |
| Consumer integration | `agent-os-cli`, `agent-os-sdk`, `desktop-*`, provider integration tests | Defer until runtime/router/loader gates are clearer. |
| Package scripts | `governance`, `validate:*`, `smoke:*`, `canary:*`, `test`, `typecheck` | No execution in this plan; command-specific authorization required. |
| Dependency install/audit | `package-lock.json`, `node_modules`, npm registry | Not part of this behavior gate; separate dependency track. |

## First Behavior-Gate Decision

Recommended next track:

```text
PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_AUTHORIZATION_PLANNING
```

Decision:

Start with a narrow local readonly behavior exact-run authorization plan, not a
broad `npm test`, not canary, not workspace-write smoke, and not external or
network-adjacent commands.

Rationale:

- Phase 8 already proved static YAML and lockfile health.
- Phase 9 needs behavior evidence, but broad test/script execution would mix too
  many surfaces at once.
- Local readonly tests or contract smoke are the best candidates, but their
  script/test bodies must be scanned first for writes, network, env/credential
  access, workspace mutation, remote calls, or broad filesystem reads.
- `typecheck` can be a supporting compile gate, but it is not runtime/router
  behavior acceptance by itself.

## Candidate Exact-Run Surfaces For Future Planning

These are candidates only. They are not authorized commands.

| Candidate | Why considered | Risk notes |
| --- | --- | --- |
| Narrow local test subset around `routing-engine.test.ts` and `runtime-control.test.ts` | Directly targets router/runtime behavior names. | Must inspect test bodies for side effects before execution. |
| Narrow local test subset around `desktop-live-adapter*.test.ts` | Loader/adapter-adjacent behavior. | Could touch desktop/live surfaces; requires content scan. |
| `smoke:contract` script | Contract smoke may be narrower than real/canary smoke. | Must inspect script body; may still touch Codex CLI surfaces. |
| `governance` or `validate:pr` | Governance behavior check is central. | May be broader than first gate; inspect script body first. |
| `typecheck` | Local compile sanity. | Useful prerequisite, but not behavior acceptance. |

## Future Preflight Requirements

Before any exact-run authorization, the next preflight/plan must confirm:

- Phase 9 scope plan hash is stable
- this behavior gate plan hash is stable
- Phase 8 closeout receipt hash is stable
- exact command candidate is named, including working directory
- exact files/scripts/tests to be read before execution are named
- candidate script/test bodies are scanned for:
  - filesystem writes or deletes
  - network or remote calls
  - env/credential access
  - private-state, logs, caches, active env files, or broad project tree reads
  - package install, npm audit, or registry access
  - workspace mutation or telemetry upload
- output redaction policy is specified
- failure policy is specified
- receipt/evidence target paths are absent
- no command has been executed yet

## Required Output Policy For Future Execution

Any future exact-run evidence must:

- capture command, working directory, exit code, and duration
- redact env values, tokens, credentials, private paths if needed, and any
  secret-like values
- record counts and PASS/FAIL summaries before raw logs
- avoid printing broad logs unless needed for failure diagnosis
- state explicitly whether the command grants behavior acceptance or only
  evidence toward a later acceptance gate

## Stop Conditions

Stop and require a separate command-specific authorization before:

- executing any npm command, package script, validator, test, build, typecheck,
  smoke, canary, runtime, loader, router, or consumer integration command
- running commands that may write workspace files or telemetry
- running commands that may contact a network, remote, registry, external model,
  or live CLI service
- changing executable bits
- editing source assets, manifests, lockfiles, registry files, runtime files,
  router files, consumers, prompts, templates, or env files
- reading private-state, logs, caches, active env files, credentials, or broad
  project trees
- claiming runtime/router/loader/consumer behavior acceptance from plan-only or
  static evidence

## Planned Future Output

If continued, create a command-specific authorization plan such as:

| Output | Purpose |
| --- | --- |
| `ops/migration/plans/phase-9-narrow-local-readonly-behavior-exact-run-authorization-plan-2026-06-29.md` | Select one narrow local readonly candidate, define preflight, redaction, execution, evidence, and acceptance boundary. |

## Result

Phase 9 runtime/router/loader/consumer behavior gate planning is complete. The
next safe step is a narrow local readonly behavior exact-run authorization plan
that still stops before execution.

Marker:

```text
PHASE_9_RUNTIME_ROUTER_LOADER_CONSUMER_GATE_PLAN_CREATED_NARROW_READONLY_AUTHORIZATION_NEXT_NO_EXECUTION
```
