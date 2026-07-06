# Phase 11 File Provider Manifest Store Persistence Exact-Run Authorization Plan - 2026-06-29

Status: authorization plan only; no test, typecheck, build, npm script, smoke,
canary, dependency install, dependency audit, source edit, revert, network,
remote, sync, deploy, workspace mutation, or file-store persistence run has been
executed by this plan.

This document opens Phase 11 for the file provider manifest store persistence
gate carried forward from Phase 10. Unlike the Phase 10 provider registry gates,
this gate intentionally exercises temporary filesystem persistence and cleanup.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-10-closeout-receipt-2026-06-29.md` | `492e3947526a8ac38321a43700307c21829a99bfd9d5ac6eab8a4e165910884e` | Phase 10 closeout authority and carry-forward gate. |
| `ops/migration/plans/phase-10-closeout-readiness-plan-2026-06-29.md` | `1575e6d996d07683a8ded7a23eecd1ae3b9c639ea91a657b91d753710c4e2541` | Phase 10 closeout readiness context. |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | Selected test file. |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | File provider manifest store implementation. |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | Provider manifest/hash implementation. |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | Codex CLI provider fixture source. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-11-file-provider-manifest-store-persistence-exact-run-authorization-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-11-file-provider-manifest-store-persistence-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` status at plan creation: clean.

Current `governance/codex-router` HEAD:

```text
88b84c66e7c815ca5797507c9e957cf5ad38eba2
```

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(file provider manifest store persists provider metadata across instances|file provider manifest store rejects duplicates and persists deletes|file provider manifest store refuses mutations while another lock is present|file provider manifest store does not remove a fresh lock during stale cleanup|file provider manifest store does not remove a stale-looking lock owned by a live process)$' tests/provider-registry.test.ts
```

Future working directory:

```text
governance/codex-router
```

## Filesystem Boundary

The selected tests call:

- `mkdtemp(join(tmpdir(), "codex-router-provider-registry-"))`
- `writeFile(...)` for lock files
- `utimes(...)` for lock timestamp cases
- `readFile(...)` for lock preservation assertions
- `rm(baseDir, { recursive: true, force: true })` in `finally`

The implementation under test may call:

- `mkdirSync(baseDir, { recursive: true })`
- `writeFileSync(...)`
- `renameSync(...)`
- `unlinkSync(...)`
- `readFileSync(...)`

The future exact-run is therefore allowed only to create, mutate, and remove
directories whose path begins with the local OS temp directory plus this exact
prefix:

```text
codex-router-provider-registry-
```

The future run is not authorized to write inside the repository, user home
configuration, workspace roots outside the generated temp directory, network,
remote, deploy, release, or sync targets.

## Why This Scope

- It covers provider manifest persistence across store instances.
- It covers duplicate detection and persisted deletes.
- It covers lock timeout behavior when another lock exists.
- It covers stale-lock safety for fresh-owner and live-process lock files.
- It is the smallest remaining provider registry gate after Phase 10.

## Future Preflight Requirements

Before execution, confirm:

- this plan hash is stable
- Phase 10 closeout receipt hash is stable
- selected test and implementation hashes are stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the named-test pattern matches exactly the five selected tests
- the local temp directory is discoverable
- selected test writes/deletes are limited to `mkdtemp(tmpdir(), "codex-router-provider-registry-")`
- the repository remains clean before execution
- no command has executed the selected tests yet

## Authorization Boundary

This plan does not authorize the exact-run by itself. The future exact-run
requires explicit authorization because it intentionally writes temporary files
and recursively removes generated temp directories.

If the future exact-run is authorized and passes, the maximum possible result is:

```text
FILE_PROVIDER_MANIFEST_STORE_TEMP_PERSISTENCE_EVIDENCE_PASS_WITH_LIMITS
```

It cannot by itself grant:

- full provider registry acceptance
- full provider acceptance
- real Codex CLI execution acceptance
- remote agent execution acceptance
- formal read-only integration execution acceptance
- consumer/runtime full acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

Phase 11 file provider manifest store persistence exact-run is planned but not
executed by this plan. The next safe step is a read-only PASS/FAIL preflight
receipt for the exact command above.

Marker:

```text
PHASE_11_FILE_PROVIDER_MANIFEST_STORE_PERSISTENCE_AUTHORIZATION_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
