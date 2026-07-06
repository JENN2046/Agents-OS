# Phase 9 Narrow Local Readonly Behavior Exact-Run Preflight Receipt - 2026-06-29

Status: PASS; preflight only. No command, npm script, test, build, typecheck,
validator, smoke, canary, runtime, loader, router, consumer integration, sync,
deploy, network, or remote action has been executed.

Decision:
`PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_PREFLIGHT_PASS_READY_FOR_EXPLICIT_EXECUTION`.

This receipt confirms that one narrow local readonly behavior exact-run
candidate is ready for separate explicit execution authorization. It does not
execute the candidate.

## Inputs Rechecked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-narrow-local-readonly-behavior-exact-run-authorization-plan-2026-06-29.md` | `647e7b4e0802c22a0496608a4f1677889d0c859d51fad000f29e04c68945390f` | stable |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | `e19e4755cf98f34a25fa4a2d7f4c46644703cfd38651540ad1c49236d69d7dc5` | stable |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | stable |
| `ops/migration/receipts/rules-assets-phase-8-closeout-receipt-2026-06-29.md` | `fee71fe1ef444aa220d0de4a2c41d002446a517002b832910f04e523da662289` | stable |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable |
| `governance/codex-router/tests/runtime-control.test.ts` | `2e08cbd8afd960dab83b38a8301abebb35c811a195376871db7f85dca462a93a` | stable |
| `governance/codex-router/tests/routing-engine.test.ts` | `faa8ca1e49f9a9a62ec5f2b1014bb07165aefbda510347b4abfbac10c67a81fd` | stable |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable |

## Target Absence Confirmed Before Creation

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-9-narrow-local-readonly-behavior-exact-run-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-receipt-2026-06-29.md` | absent |

Workspace Git state: `/home/jenn/AGENTS_OS_Workspace` is not a Git repository.

## Exact Command Candidate

Future command candidate:

```text
./node_modules/.bin/tsx --test tests/runtime-control.test.ts tests/routing-engine.test.ts
```

Future working directory:

```text
governance/codex-router
```

This preflight does not execute the command.

## Local Tool Boundary

| Item | Result |
| --- | --- |
| `governance/codex-router/node_modules/.bin/tsx` | exists as local symlink |
| resolved target | `/home/jenn/AGENTS_OS_Workspace/governance/codex-router/node_modules/tsx/dist/cli.mjs` |
| resolved target type/mode | regular file, mode `755` |
| selected test files | regular files, mode `644` |
| `routing-policy.yaml` | regular file, mode `644` |

## Risk Scan

Risk scan scope:

- `governance/codex-router/tests/runtime-control.test.ts`
- `governance/codex-router/tests/routing-engine.test.ts`
- limited dependency check for `loadPolicyFromFile` in
  `governance/codex-router/packages/policy-config/src/index.ts`

Risk keyword scan result:

| Risk class | Result |
| --- | --- |
| filesystem write/delete/move/copy/create stream | 0 hits in selected tests |
| network/remote/fetch/http/https | 0 hits in selected tests |
| env/credential/token/secret access | 0 hits in selected tests |
| child process/exec/spawn | 0 hits in selected tests |
| npm install/audit/registry access | 0 hits in selected tests |
| telemetry/upload/workspace-write | 0 hits in selected tests |
| local file read | observed only through `loadPolicyFromFile`, which reads the exact local `routing-policy.yaml` file |

## Boundary Decision

| Boundary | Result |
| --- | --- |
| Narrow local readonly exact-run candidate | PASS_PREFLIGHT |
| Command execution | not performed; requires explicit next authorization |
| Runtime/router behavior evidence | not collected yet |
| Loader behavior acceptance | not granted |
| Consumer integration acceptance | not granted |
| npm script/build/typecheck/test-suite acceptance | not granted |
| dependency install/audit/freshness acceptance | not granted |

## Required Execution Evidence If Authorized Later

If separately authorized, the execution receipt/evidence must record:

- exact command and working directory
- exit code
- duration
- test pass/fail summary
- redacted output summary
- whether result is evidence-only or narrow local behavior acceptance candidate
- no loader, consumer, npm script, dependency install/audit, network, remote, or
  full runtime acceptance unless separately granted

## Stop Conditions

Do not execute if:

- any input hash drifts
- `tsx` resolves outside the local project dependency tree
- selected tests or `routing-policy.yaml` drift
- exact command or working directory changes
- evidence/receipt targets already exist
- a new risk scan reveals write/delete, network/remote, env/credential,
  child-process, telemetry upload, install/audit, or broad project-tree behavior
- output handling would disclose secrets or private state

## Result

Preflight passes for the selected narrow local readonly behavior exact-run
candidate. Execution remains blocked until explicitly authorized.

Marker:

```text
PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_PREFLIGHT_PASS_NO_EXECUTION
```
