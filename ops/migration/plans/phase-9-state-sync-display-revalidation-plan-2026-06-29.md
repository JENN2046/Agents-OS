# Phase 9 State-Sync Display Revalidation Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans a narrow revalidation gate for the state-sync display source
and test surface observed during the prior current-source revalidation gate.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-current-source-revalidation-review-closeout-receipt-2026-06-29.md` | `08ac955b5a05ead17e2855222046d90bda38c7f3a3cc6abbf2a5f0b49ec4cc16` | Prior gate closeout. |
| `governance/codex-router/scripts/sync-state-sync-display.ts` | `6a062ae14ddcba045897947f69ba6655c47d9113facfb33d6d0b6f4b2ed7bf9f` | State-sync display implementation under validation; matches current `HEAD`. |
| `governance/codex-router/tests/state-sync-display-sync.test.ts` | `d32561ca397905e8f65314add0937ac153158b0e1694c58a10aa455f0f3df6bd` | State-sync display test under validation; matches current `HEAD`. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Static command surface. |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | Locked local dependency surface. |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | TypeScript project scope. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-state-sync-display-revalidation-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-state-sync-display-revalidation-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-9-state-sync-display-revalidation-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-state-sync-display-revalidation-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-state-sync-display-revalidation-review-closeout-receipt-2026-06-29.md` | absent |

## Planned Exact Command

```text
./node_modules/.bin/tsx --test tests/state-sync-display-sync.test.ts
```

Working directory:

```text
governance/codex-router
```

## Static Safety Notes

The test imports `mkdtemp`, `mkdir`, `readFile`, and `writeFile` from
`node:fs/promises`, but the reviewed setup creates a temporary working
directory with `mkdtemp(join(tmpdir(), ...))` and calls `syncStateSyncDisplay`
against that temp directory. The planned command does not run the actual
workspace state-sync script against the repository root.

The implementation under test can write files relative to a supplied `cwd`.
For this test command, that `cwd` is generated under the system temp directory.

## Future Preflight Requirements

Before execution, a preflight receipt must confirm:

- this plan hash is stable
- implementation and test hashes are stable and match current `HEAD`
- `package.json`, `package-lock.json`, and `tsconfig.json` hashes are stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the command matches the exact command above
- reviewed test setup still uses temp directories, not repository root
- no command has been executed yet

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
STATE_SYNC_DISPLAY_LOCAL_TEMP_DIR_TEST_REVALIDATION_PASS_WITH_LIMITS
```

It cannot by itself grant:

- whole-tree acceptance
- actual workspace state-sync write acceptance
- package script acceptance
- broad `npm test` acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

State-sync display revalidation is planned but not executed by this plan. The
next safe step is a PASS/FAIL preflight receipt for the exact command above.

Marker:

```text
PHASE_9_STATE_SYNC_DISPLAY_REVALIDATION_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
