# Phase 9 Loader Behavior Narrow Plan - 2026-06-29

Status: plan only; no loader test, npm script, build, typecheck, smoke,
canary, runtime, router, consumer integration, source edit, dependency install,
network, remote, telemetry upload, sync, deploy, or workspace mutation has been
executed.

This document narrows the next Phase 9 loader/adapter behavior candidate after
the first local runtime/router exact-run closed. It records candidate screening
and chooses the next planning step. It does not authorize or execute any loader
behavior command.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | Phase 9 scope authority. |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | `e19e4755cf98f34a25fa4a2d7f4c46644703cfd38651540ad1c49236d69d7dc5` | Runtime/router/loader/consumer gate planning authority. |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-review-closeout-receipt-2026-06-29.md` | `530cd5915e5f0b1c0872e6a75e4c9f4a87c3c2e5abd67cc0f82caebbe42b5bd0` | Confirms first runtime/router exact-run is closed with loader still deferred. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Static command surface only. |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | Static TypeScript project scope only. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-loader-behavior-narrow-plan-2026-06-29.md` | absent |
| `ops/migration/plans/phase-9-loader-behavior-narrow-exact-run-authorization-plan-2026-06-29.md` | absent |
| `ops/migration/plans/phase-9-typecheck-support-gate-plan-2026-06-29.md` | absent |

Workspace Git state: `/home/jenn/AGENTS_OS_Workspace` is not a Git repository.

## Candidate Surface Observed

Static file-name and test-name screening found the following loader,
host, adapter, and provider-adjacent tests:

| Candidate | SHA-256 | Mode / size | Observed first tests | Decision |
| --- | --- | --- | --- | --- |
| `governance/codex-router/tests/desktop-live-adapter.test.ts` | `7e3daae27d57a0e2e5be5f2ea6c4a53e9cb2bcebbca706ac03d4a667d728eaa9` | `644`, regular file, `32078` bytes | `desktop live adapter does not execute blocked runner results`; `desktop live adapter executes primitives sequentially when handlers exist`; `desktop live adapter normalizes raw handler output into typed envelopes` | Primary narrow planning candidate. |
| `governance/codex-router/tests/desktop-live-adapter-governance.test.ts` | `5709839ac69e73b5abdbd1dc793fe396139d623ae83aedd0950eeb686f98adcc` | `644`, regular file, `26706` bytes | governance missing-handler, failure-envelope, thrown-handler, strike-count, and step-back cases | Secondary candidate after the base adapter path is narrowed. |
| `governance/codex-router/tests/desktop-host-client.test.ts` | `de331b755208f092ca6ec1691b4e31752d6b66bfdb1df57f65583785eadf0954` | `644`, regular file, `14554` bytes | real host bindings, memory recall, checkpoint lookup, telemetry gate behavior | Defer; host-client surface is closer to consumer integration. |
| `governance/codex-router/tests/host-dispatcher.test.ts` | `ccde8afb72c51aafe0dce7feaacc19aa0baef0814d3f612adb9d95b02f79003f` | `644`, regular file, `32517` bytes | codex-cli routing, provider permits, fake in-memory execution, dry run, workspace-write rejection | Defer; broader dispatch/provider surface. |
| `governance/codex-router/tests/codex-desktop-live-host.test.ts` | `b33be6db1f152de822e70be17b97dc9117c10695331df4993b154ca3bcd31af6` | `644`, regular file, `40893` bytes | live host bundle, directive resolvers, memory operations, preflight, current host object | Defer; broad live-host integration surface. |

The observed loader/host package-name surface includes:

- `governance/codex-router/packages/desktop-live-adapter`
- `governance/codex-router/packages/desktop-live-adapter` adjacent governance tests
- `governance/codex-router/packages/desktop-host-client`
- `governance/codex-router/packages/host-dispatcher`
- `governance/codex-router/packages/codex-desktop-live-host`
- provider and registry adjacent packages such as `provider-core`,
  `provider-execution-runner`, `provider-registry`, and `providers`

## Static Risk Notes

Text-level screening of the five candidate test files observed:

| Signal | Observed note | Treatment |
| --- | --- | --- |
| `spawn_agent` literals and handlers | Present in adapter, governance, host-client, and dispatcher tests as in-memory primitive names or fake handlers. | Not treated as OS child-process execution by itself, but exact selected sections must be rescanned before execution. |
| `spawn` literals | Present in later `desktop-live-adapter.test.ts` sections around codex-cli dispatch simulation. | Avoid later dispatch sections for the first loader exact-run. |
| secret-like fixture strings | Present as redaction fixtures such as `payload-secret`, `raw-token`, and `raw-secret-token`. | Allowed only as test fixture evidence if redacted in receipts; do not print broad raw logs. |
| telemetry / audit terms | Present in adapter, governance, host-client, and live-host tests. | Keep output redacted/counts-first; do not grant telemetry acceptance. |
| `npm test` string literals | Present in broad live-host tests. | Exclude broad live-host tests from the first loader exact-run. |
| host / provider / workspace-write terms | Present in dispatcher and host-client surfaces. | Defer until after base loader behavior and typecheck support gates. |

No loader command has been executed by this plan.

## Narrow Loader Decision

Recommended next track:

```text
PHASE_9_LOADER_BEHAVIOR_NARROW_EXACT_RUN_AUTHORIZATION_PLANNING
```

Decision:

Plan the first loader exact-run around a small named-test subset from
`tests/desktop-live-adapter.test.ts`, not the whole loader/host/dispatcher test
family and not `npm test`.

Initial named-test candidates for the next authorization plan:

- `desktop live adapter does not execute blocked runner results`
- `desktop live adapter executes primitives sequentially when handlers exist`
- `desktop live adapter normalizes raw handler output into typed envelopes`

Rationale:

- These are the earliest base adapter behavior tests in the primary candidate
  file.
- They exercise blocked-runner handling, sequential primitive handler dispatch,
  and typed envelope normalization.
- They avoid later sections that mention codex-cli dispatch, spawn simulation,
  broad live-host wiring, consumer integration, and host/provider acceptance.
- They keep loader behavior separate from telemetry acceptance, host-client
  acceptance, provider acceptance, and consumer integration acceptance.

The next authorization plan must verify whether the local `tsx --test` runner
supports a safe named-test pattern for this subset. If exact named-test
selection cannot be made without ambiguity, the future plan must either choose
a smaller explicitly reviewed command surface or stop before execution.

## Future Preflight Requirements

Before any loader exact-run, a future preflight/authorization package must
confirm:

- this loader narrow plan hash is stable
- Phase 9 scope plan hash is stable
- Phase 9 runtime/router/loader/consumer gate plan hash is stable
- first runtime/router exact-run review closeout hash is stable
- selected test file hash is stable
- `governance/codex-router/node_modules/.bin/tsx` exists and is local
- future evidence and receipt targets are absent
- selected named-test lines and surrounding helper sections are reread within a
  bounded range
- selected sections still avoid filesystem writes/deletes, network/remote
  calls, env/credential reads, dependency install/audit, telemetry upload,
  broad tree scans, and source mutation
- redaction covers secret-like fixture strings and private path leakage
- the future command is exact, local, and does not use `npm test`
- no loader command has been executed yet

## Future Evidence Targets

If continued, create a command-specific authorization plan such as:

| Future target | Purpose |
| --- | --- |
| `ops/migration/plans/phase-9-loader-behavior-narrow-exact-run-authorization-plan-2026-06-29.md` | Select the exact loader named-test subset, command, preflight, evidence targets, redaction policy, and acceptance boundary. |

Future execution evidence and receipts must be named separately by that
authorization plan. This plan does not create those execution targets.

## Acceptance Boundary

The maximum possible result from the future first loader exact-run is:

```text
LOCAL_READONLY_LOADER_BASE_BEHAVIOR_EVIDENCE_COLLECTED_WITH_LIMITS
```

It cannot by itself grant:

- full loader acceptance
- host-client acceptance
- host-dispatcher acceptance
- provider acceptance
- consumer integration acceptance
- live-host acceptance
- telemetry/audit acceptance
- package script acceptance
- broad `npm test` acceptance
- build/typecheck acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, canary, smoke, or workspace-write acceptance

## Stop Conditions

Stop before any loader execution if:

- any required input hash drifts
- future plan/evidence/receipt targets already exist
- selected named-test targeting cannot be expressed exactly
- selected sections drift or include writes, deletes, network, remote, env,
  credential, dependency install/audit, telemetry upload, broad tree scan, or
  source mutation behavior
- the command would execute `npm test`, all tests, broad live-host tests,
  provider/dispatcher acceptance tests, or consumer integration tests
- output handling would expose secret-like fixture strings, credentials, env
  values, private paths, or broad logs
- the result would be framed as full loader/consumer/runtime/router acceptance

## Result

The loader behavior track is narrowed to a future command-specific exact-run
authorization plan for a small named-test subset in
`tests/desktop-live-adapter.test.ts`. No loader behavior command has been
executed.

Marker:

```text
PHASE_9_LOADER_BEHAVIOR_NARROW_PLAN_CREATED_EXACT_RUN_AUTHORIZATION_NEXT_NO_EXECUTION
```
