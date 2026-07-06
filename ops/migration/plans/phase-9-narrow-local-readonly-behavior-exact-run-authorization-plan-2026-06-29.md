# Phase 9 Narrow Local Readonly Behavior Exact-Run Authorization Plan - 2026-06-29

Status: authorization plan only; no command, npm script, test, build, typecheck,
validator, smoke, canary, runtime, loader, router, consumer integration, sync,
deploy, network, or remote action has been executed.

This document selects one narrow local readonly behavior exact-run candidate for
future authorization. It records the candidate screening and defines the
preflight, command, evidence, output policy, and acceptance boundary. It does
not execute the candidate command.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | Phase 9 scope authority. |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | `e19e4755cf98f34a25fa4a2d7f4c46644703cfd38651540ad1c49236d69d7dc5` | Behavior gate planning authority. |
| `ops/migration/receipts/rules-assets-phase-8-closeout-receipt-2026-06-29.md` | `fee71fe1ef444aa220d0de4a2c41d002446a517002b832910f04e523da662289` | Carries runtime/router/loader/consumer gates into Phase 9. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Static command surface. |
| `governance/codex-router/tests/runtime-control.test.ts` | `2e08cbd8afd960dab83b38a8301abebb35c811a195376871db7f85dca462a93a` | Selected narrow runtime behavior test. |
| `governance/codex-router/tests/routing-engine.test.ts` | `faa8ca1e49f9a9a62ec5f2b1014bb07165aefbda510347b4abfbac10c67a81fd` | Selected narrow router behavior test. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Local policy file read by `routing-engine.test.ts`. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-narrow-local-readonly-behavior-exact-run-authorization-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-9-narrow-local-readonly-behavior-exact-run-risk-scan-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-receipt-2026-06-29.md` | absent |

Workspace Git state: `/home/jenn/AGENTS_OS_Workspace` is not a Git repository.

## Candidate Screening

| Candidate | Screening result | Decision |
| --- | --- | --- |
| `tests/runtime-control.test.ts` | Tiny local unit test; imports `upgradeModel`; no filesystem write, network, env, child-process, or credential keyword hits in risk scan. | Selected. |
| `tests/routing-engine.test.ts` | Local router behavior test; reads local `routing-policy.yaml`; no filesystem write, network, env, child-process, or credential keyword hits in risk scan. | Selected. |
| `tests/strategy-router.test.ts` | Local static behavior-style test; no high-risk keyword hits observed, but less directly tied to Phase 8 routing policy closure. | Keep as later candidate. |
| `tests/preflight.test.ts` | Local preflight behavior test; useful but more governance/preflight-specific than first runtime/router candidate. | Keep as later candidate. |
| `scripts/run-codex-cli-contract-smoke.ts` | Risk scan found `process.env`, `mkdir`, and `writeFile`; writes an evidence file. | Exclude from first readonly exact-run. |

## Selected Exact-Run Candidate

Future command candidate:

```text
./node_modules/.bin/tsx --test tests/runtime-control.test.ts tests/routing-engine.test.ts
```

Future working directory:

```text
governance/codex-router
```

Why this candidate:

- It is narrower than `npm test`.
- It avoids npm script wrappers.
- It avoids canary, smoke, workspace-write, telemetry, external, and registry
  surfaces.
- It exercises runtime-control and routing-engine behavior against the local
  static routing policy without accepting loader or consumer integration.

## Future Preflight Requirements

Before executing the candidate, a future preflight receipt must confirm:

- this authorization plan hash is stable
- Phase 9 scope plan hash is stable
- Phase 9 behavior gate plan hash is stable
- Phase 8 closeout receipt hash is stable
- selected test file hashes are stable
- `routing-policy.yaml` hash is stable
- `governance/codex-router/node_modules/.bin/tsx` exists and is local
- execution evidence and receipt targets are absent
- selected test bodies still have no filesystem write/delete, network, remote,
  env/credential, child-process, install/audit, telemetry upload, or broad tree
  scan signals
- command is exactly the selected command above, from the selected working
  directory
- no command has been executed yet

## Future Evidence Targets

If separately authorized after preflight, create:

| Future target | Purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-preflight-receipt-2026-06-29.md` | Confirm exact command, hashes, risk scan, and target absence before execution. |
| `ops/migration/inventory/phase-9-narrow-local-readonly-behavior-exact-run-evidence-2026-06-29.md` | Record command, working directory, exit code, duration, redacted output summary, and test counts. |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-receipt-2026-06-29.md` | Record execution result and limits. |

## Output And Redaction Policy

Future exact-run evidence must:

- record command and working directory
- record exit code and duration
- summarize pass/fail counts before logs
- redact token-like strings, credentials, env values, and private-state paths if
  any appear
- avoid broad raw log inclusion unless needed to diagnose failure
- explicitly state whether the run is evidence-only or grants a narrow local
  behavior acceptance

## Acceptance Boundary

If the future exact-run passes, the maximum possible immediate result is:

```text
LOCAL_READONLY_RUNTIME_ROUTER_BEHAVIOR_EVIDENCE_COLLECTED_WITH_LIMITS
```

It cannot by itself grant:

- loader behavior acceptance
- consumer integration acceptance
- governance router full acceptance
- package script acceptance
- `npm test` acceptance
- build/typecheck acceptance
- dependency installability/security/freshness acceptance
- remote, network, telemetry, canary, workspace-write, sync, or deploy
  acceptance

## Stop Conditions

Stop before execution if:

- any input hash drifts
- future evidence/receipt targets already exist
- selected tests or `routing-policy.yaml` drift
- `tsx` is missing or resolves outside the local project dependency surface
- the risk scan finds write/delete, network/remote, env/credential,
  child-process, telemetry upload, install/audit, or broad tree-scan behavior
- the command differs from the selected command
- output handling would expose secrets or private state
- the result would be framed as full runtime/router/loader/consumer acceptance

## Result

The first Phase 9 narrow local readonly behavior exact-run candidate is planned
but not executed. The next safe step is a formal preflight receipt for this
exact command.

Marker:

```text
PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_AUTHORIZATION_PLAN_CREATED_NO_EXECUTION
```
