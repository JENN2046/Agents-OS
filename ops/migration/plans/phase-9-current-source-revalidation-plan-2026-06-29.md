# Phase 9 Current Source Revalidation Plan - 2026-06-29

Status: plan only; no typecheck, test, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans a narrow revalidation gate for the current
`governance/codex-router` source state. The source files that were dirty in the
previous evidence are now stable at current `HEAD`; remaining uncommitted
changes are non-source state/documentation files carried outside this command
surface.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/inventory/phase-9-current-dirty-source-state-evidence-2026-06-29.md` | `9cb88a7af4cfcbd479f28b2ead33d2fc04720f144e5f0d849b8e5c5d5f1e4e80` | Historical dirty source evidence. |
| `ops/migration/inventory/phase-9-source-state-stability-update-evidence-2026-06-29.md` | `bdbfdb9815ae20b9f1bcc50fec12a49a9d3265dd3a60edea005f2a33f3ca5ef5` | Confirms source files now match current `HEAD`; non-source dirty state remains. |
| `ops/migration/receipts/rules-assets-phase-9-current-dirty-source-state-readiness-receipt-2026-06-29.md` | `9aa96fca409f4e36cdc3ed3808cdda72bd0c9cb4319578e7ced01b2b13d6c3b1` | Readiness decision for this plan. |
| `governance/codex-router/packages/desktop-live-adapter/src/index.ts` | `c28819e9df08e3774aa2c51fd87f88ff2b439db4cb5fe95c86b4da3532e36f66` | Current HEAD implementation under validation. |
| `governance/codex-router/tests/desktop-live-adapter-governance.test.ts` | `7f9ab9d905294d51854de8fe0db5372201d771eec2cda685f3c193d366ba173c` | Current HEAD governance test under validation. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Static command surface. |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | Locked local dependency surface. |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | TypeScript project scope. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Local policy read by selected tests. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-current-source-revalidation-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-current-source-revalidation-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-9-current-source-revalidation-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-current-source-revalidation-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-current-source-revalidation-review-closeout-receipt-2026-06-29.md` | absent |

## Planned Exact Commands

Command A, static compile support:

```text
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

Command B, narrow current-source governance behavior:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(governance: codex-cli host dispatch failure appends anomaly and calls onGovernanceUpdate|governance: codex-cli host dispatch third failure triggers recovery result|governance: successful codex-cli host dispatch does not trigger governance updates)$' tests/desktop-live-adapter-governance.test.ts
```

Working directory for both commands:

```text
governance/codex-router
```

## Why This Scope

- The current implementation change is in `desktop-live-adapter`.
- The current tests add exactly three codex-cli host-dispatch governance cases.
- `tsc --noEmit` checks the current TypeScript tree without generating
  output.
- The named-test exact-run checks the new behavior directly without running the
  full governance test file or broad `npm test`.

## Future Preflight Requirements

Before executing either command, create a preflight receipt confirming:

- this plan hash is stable
- dirty source evidence hash is stable as historical input
- source state stability update evidence hash is stable
- dirty source readiness receipt hash is stable
- current source hashes are stable and match current `HEAD`
- `package.json`, `package-lock.json`, `tsconfig.json`, and
  `routing-policy.yaml` hashes are stable
- `node_modules/.bin/tsc` and `node_modules/.bin/tsx` exist and resolve to local
  project dependency entrypoints
- future evidence and receipt targets are absent
- Command A and Command B match this plan exactly
- the Command B named-test pattern matches exactly the three listed test names
- selected added test code uses fake/injected codex-cli spawn behavior only
- no command has been executed yet

## Output And Redaction Policy

Future evidence must:

- record each command, working directory, exit code, duration, and summary
- record TypeScript diagnostics only if needed
- record TAP pass/fail/skip counts for the selected tests
- redact credentials, env values, token-like strings, private paths, and
  secret-like values if any appear
- state that the result is current source revalidation only

## Acceptance Boundary

If both commands pass, the maximum possible result is:

```text
CURRENT_DIRTY_SOURCE_STATIC_AND_NARROW_GOVERNANCE_REVALIDATION_PASS_WITH_LIMITS
```

It cannot by itself grant:

- full loader acceptance
- full host-dispatcher acceptance
- provider acceptance
- live-host acceptance
- telemetry/audit acceptance
- consumer integration acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- source edit, revert, merge, release, remote, sync, deploy, or workspace-write
  acceptance

## Stop Conditions

Stop before execution if:

- any input hash drifts
- evidence/receipt targets already exist
- `tsc` or `tsx` resolves outside local project dependency surface
- either command differs from the exact commands above
- Command B named-test pattern matches anything outside the three listed tests
- selected test code drifts into real child-process execution, network, env
  credential access, dependency install/audit, source mutation, broad tree scan,
  or telemetry upload
- output handling would expose credentials, env values, token-like strings,
  private paths, or broad logs
- the result would be framed as broader loader/consumer/package acceptance

## Result

Current source revalidation is planned but not executed by this plan. The next
safe step is a PASS/FAIL preflight receipt for Command A and Command B.

Marker:

```text
PHASE_9_CURRENT_SOURCE_REVALIDATION_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
