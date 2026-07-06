# Phase 9 Typecheck Support Gate Plan - 2026-06-29

Status: plan only; no typecheck, build, npm script, test, smoke, canary,
runtime, router, loader, consumer integration, dependency install, dependency
audit, source edit, network, remote, sync, deploy, or workspace mutation has
been executed.

This document plans a Phase 9 supporting static compile gate. It identifies the
future typecheck command candidate and its boundary. It does not authorize or
execute the command.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | Phase 9 scope authority. |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | `e19e4755cf98f34a25fa4a2d7f4c46644703cfd38651540ad1c49236d69d7dc5` | Behavior gate planning authority. |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-review-closeout-receipt-2026-06-29.md` | `530cd5915e5f0b1c0872e6a75e4c9f4a87c3c2e5abd67cc0f82caebbe42b5bd0` | Confirms first runtime/router exact-run is closed. |
| `ops/migration/plans/phase-9-loader-behavior-narrow-plan-2026-06-29.md` | `620182a55ff73d4951947b75be46e72b850ab5c3d59fe44533e3db567a4b1e9d` | Confirms loader track is narrowed but not executed. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Static script and dependency surface. |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | Locked local dependency surface. |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | TypeScript project scope. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-typecheck-support-gate-plan-2026-06-29.md` | absent |
| `ops/migration/plans/phase-9-typecheck-support-exact-run-authorization-plan-2026-06-29.md` | absent |

Observed local tool surface:

| Tool | Observation | Use |
| --- | --- | --- |
| `governance/codex-router/node_modules/.bin/tsc` | exists; symbolic link; mode `777`; target `../typescript/bin/tsc` | Candidate direct local TypeScript compiler entrypoint for a future gate. |

Workspace Git state: `/home/jenn/AGENTS_OS_Workspace` is not a Git repository.

## Static Command Surface

`package.json` exposes:

| Script | Static command | Decision |
| --- | --- | --- |
| `build` | `tsc -p tsconfig.json` | Defer; build may emit to `dist` because `tsconfig.json` has `outDir: "dist"`. |
| `typecheck` | `tsc -p tsconfig.json --noEmit` | Candidate behavior-support gate, preferably run through the direct local binary instead of `npm run`. |
| `test` | `tsx --test tests/*.test.ts` | Too broad for this support gate. |
| `governance`, `validate:*`, `smoke:*`, `canary:*`, `evidence:collect` | `tsx ...` scripts | Not part of typecheck support. |

`tsconfig.json` includes:

- `packages/**/*.ts`
- `scripts/**/*.ts`
- `tests/**/*.ts`

So a future typecheck would cover more than the two tests already executed and
more than the narrowed loader candidate. This is useful as a compile-health
support gate, but it must not be framed as runtime, loader, router, or consumer
behavior acceptance.

## Candidate Future Command

Future direct-command candidate:

```text
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

Future working directory:

```text
governance/codex-router
```

Why direct binary instead of `npm run typecheck`:

- It avoids npm script wrapper behavior.
- It matches the static `typecheck` script while keeping the exact command
  visible.
- `--noEmit` prevents `dist` writes.
- It stays local to the checked-in project dependency surface.

## Future Preflight Requirements

Before executing the typecheck candidate, a future authorization/preflight
package must confirm:

- this typecheck support gate plan hash is stable
- Phase 9 scope plan hash is stable
- Phase 9 runtime/router/loader/consumer gate plan hash is stable
- first runtime/router exact-run review closeout hash is stable
- loader narrow plan hash is stable
- `package.json`, `package-lock.json`, and `tsconfig.json` hashes are stable
- `governance/codex-router/node_modules/.bin/tsc` exists and resolves to the
  local `typescript` package entrypoint
- future authorization, evidence, and receipt targets are absent
- the future command is exactly the direct `tsc --noEmit` command above
- no npm command, build, test, loader command, smoke, canary, install, audit,
  network, remote, or workspace-write command is bundled into the same run
- no command has been executed yet

## Future Evidence Targets

If continued, create a command-specific authorization plan such as:

| Future target | Purpose |
| --- | --- |
| `ops/migration/plans/phase-9-typecheck-support-exact-run-authorization-plan-2026-06-29.md` | Select exact direct `tsc --noEmit` command, preflight, evidence targets, output policy, and acceptance boundary. |

Future execution evidence and receipts must be named separately by that
authorization plan. This plan does not create those execution targets.

## Output And Redaction Policy

Future typecheck evidence must:

- record command, working directory, exit code, and duration
- summarize pass/fail status before diagnostics
- include only diagnostics needed to understand failure
- redact private paths, credentials, env values, token-like values, and
  secret-like strings if any appear
- avoid broad logs or package-manager output
- state that the run is a static compile support gate, not behavior acceptance

## Acceptance Boundary

The maximum possible result from a future passing typecheck is:

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

Stop before any typecheck execution if:

- any required input hash drifts
- future plan/evidence/receipt targets already exist
- `tsc` is missing or resolves outside the local project dependency surface
- the command would emit files, run build, run `npm`, run tests, run smoke,
  run canary, install dependencies, audit dependencies, contact network/remote,
  or mutate workspace state
- output handling would expose credentials, env values, token-like strings,
  private paths, or broad logs
- the result would be framed as runtime/router/loader/consumer acceptance

## Result

The Phase 9 typecheck support gate is planned but not executed. The next safe
step for this track is a command-specific exact-run authorization plan for the
direct local `tsc --noEmit` command.

Marker:

```text
PHASE_9_TYPECHECK_SUPPORT_GATE_PLAN_CREATED_NO_EXECUTION
```
