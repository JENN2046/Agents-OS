# Phase 9 Typecheck Support Exact-Run Authorization Plan - 2026-06-29

Status: authorization plan only; no typecheck, build, npm script, test, smoke,
canary, runtime, router, loader, consumer integration, dependency install,
dependency audit, source edit, network, remote, sync, deploy, or workspace
mutation has been executed by this plan.

This document authorizes a future direct local TypeScript compile check as a
Phase 9 support gate. It fixes the working directory, exact command, evidence
targets, output policy, acceptance boundary, and stop conditions. It does not
execute the command.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | Phase 9 scope authority. |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | `e19e4755cf98f34a25fa4a2d7f4c46644703cfd38651540ad1c49236d69d7dc5` | Behavior gate planning authority. |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-review-closeout-receipt-2026-06-29.md` | `530cd5915e5f0b1c0872e6a75e4c9f4a87c3c2e5abd67cc0f82caebbe42b5bd0` | Runtime/router exact-run closeout. |
| `ops/migration/plans/phase-9-loader-behavior-narrow-plan-2026-06-29.md` | `620182a55ff73d4951947b75be46e72b850ab5c3d59fe44533e3db567a4b1e9d` | Loader narrow planning context. |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-review-closeout-receipt-2026-06-29.md` | `8b076dd38551b5cab5163a1478ce1ecb50c51ce479f7deb52694490f0088ac49` | Loader exact-run closeout. |
| `ops/migration/plans/phase-9-typecheck-support-gate-plan-2026-06-29.md` | `c7a26090399dc9db471a259186623cfa0611df1c969867f659ff8342eb9589c7` | Typecheck support planning authority. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Static script and dependency surface. |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | Locked local dependency surface. |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | TypeScript project scope. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-typecheck-support-exact-run-authorization-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-9-typecheck-support-exact-run-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-review-closeout-receipt-2026-06-29.md` | absent |

Observed local runner surface:

| Tool | Observation |
| --- | --- |
| `governance/codex-router/node_modules/.bin/tsc` | exists; symbolic link; mode `777`; target `../typescript/bin/tsc` |

`governance/codex-router` git status: clean.

## Selected Exact-Run Candidate

Future command candidate:

```text
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

Future working directory:

```text
governance/codex-router
```

Why this command:

- it uses the local project TypeScript compiler directly
- it avoids `npm run`, npm script wrappers, install, audit, registry, and
  network surfaces
- `--noEmit` prevents generated `dist` output
- it checks the TypeScript project defined by `tsconfig.json`

## Static Project Scope

The checked `tsconfig.json` includes:

- `packages/**/*.ts`
- `scripts/**/*.ts`
- `tests/**/*.ts`

That means the future typecheck is broader than the previously executed narrow
runtime/router and loader behavior tests. It is useful as a static compile
support gate, but it is not runtime, router, loader, or consumer behavior
acceptance.

## Future Preflight Requirements

Before executing the selected command, create a preflight receipt confirming:

- this authorization plan hash is stable
- Phase 9 scope plan hash is stable
- Phase 9 runtime/router/loader/consumer gate plan hash is stable
- runtime/router exact-run closeout hash is stable
- loader exact-run closeout hash is stable
- typecheck support gate plan hash is stable
- `package.json`, `package-lock.json`, and `tsconfig.json` hashes are stable
- `governance/codex-router/node_modules/.bin/tsc` exists and resolves to the
  local `typescript` package entrypoint
- future evidence and execution receipt targets are absent
- the exact command matches the command in this plan
- no npm command, build, test, smoke, canary, dependency install/audit, network,
  remote, or workspace-write command is bundled into the same run
- no typecheck command has been executed yet

## Future Evidence Targets

If separately continued after preflight, create:

| Future target | Purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-preflight-receipt-2026-06-29.md` | Confirm hashes, exact command, local `tsc`, target absence, and no execution before the run. |
| `ops/migration/inventory/phase-9-typecheck-support-exact-run-evidence-2026-06-29.md` | Record command, working directory, exit code, duration, redacted diagnostics summary, and limits. |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-receipt-2026-06-29.md` | Record execution result and acceptance boundary. |

## Output And Redaction Policy

Future typecheck evidence must:

- record command and working directory
- record exit code and duration
- summarize PASS/FAIL before diagnostics
- include diagnostics only as needed for failure understanding
- redact credentials, env values, token-like strings, private paths, and
  secret-like values if any appear
- avoid broad package-manager logs
- explicitly state that the result is static compile support evidence, not
  runtime/router/loader/consumer behavior acceptance

## Acceptance Boundary

If the future exact-run passes, the maximum possible immediate result is:

```text
LOCAL_STATIC_TYPESCRIPT_COMPILE_SUPPORT_EVIDENCE_COLLECTED_WITH_LIMITS
```

It cannot by itself grant:

- runtime behavior acceptance
- router behavior acceptance
- loader behavior acceptance
- consumer integration acceptance
- host/provider/live-host acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, telemetry, sync, deploy, or workspace-write acceptance

## Stop Conditions

Stop before execution if:

- any required input hash drifts
- future evidence/receipt targets already exist
- `tsc` is missing or resolves outside the local project dependency surface
- the command differs from the exact command in this plan
- the command would emit files, run build, run npm, run tests, run smoke, run
  canary, install dependencies, audit dependencies, contact network/remote, or
  mutate workspace state
- output handling would expose credentials, env values, token-like strings,
  private paths, or broad logs
- the result would be framed as runtime/router/loader/consumer acceptance

## Result

The Phase 9 typecheck support exact-run is authorized for future preflight only.
The selected command is fixed, but no typecheck command has been executed by
this plan.

Marker:

```text
PHASE_9_TYPECHECK_SUPPORT_EXACT_RUN_AUTHORIZATION_PLAN_CREATED_NO_EXECUTION
```
