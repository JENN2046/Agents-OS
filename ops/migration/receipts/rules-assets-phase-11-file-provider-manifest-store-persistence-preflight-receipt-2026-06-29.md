# Phase 11 File Provider Manifest Store Persistence Preflight Receipt - 2026-06-29

Status: PASS; preflight only; no test, typecheck, build, npm script, smoke,
canary, dependency install, dependency audit, source edit, revert, network,
remote, sync, deploy, workspace mutation, or file-store persistence run has been
executed by this receipt.

Decision:
`PHASE_11_FILE_PROVIDER_MANIFEST_STORE_PERSISTENCE_PREFLIGHT_PASS_NO_EXECUTION`.

## Inputs Checked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-11-file-provider-manifest-store-persistence-exact-run-authorization-plan-2026-06-29.md` | `48fab9084c94e6115fac222937c8940ac78a469ec34ba1e8bad3912a0c7567ec` | stable |
| `ops/migration/receipts/rules-assets-phase-10-closeout-receipt-2026-06-29.md` | `492e3947526a8ac38321a43700307c21829a99bfd9d5ac6eab8a4e165910884e` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-11-file-provider-manifest-store-persistence-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status at preflight: clean.

Current `governance/codex-router` HEAD:

```text
88b84c66e7c815ca5797507c9e957cf5ad38eba2
```

## Exact Command Confirmed

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(file provider manifest store persists provider metadata across instances|file provider manifest store rejects duplicates and persists deletes|file provider manifest store refuses mutations while another lock is present|file provider manifest store does not remove a fresh lock during stale cleanup|file provider manifest store does not remove a stale-looking lock owned by a live process)$' tests/provider-registry.test.ts
```

Working directory:

```text
governance/codex-router
```

Local runner:

| Tool | Observation | Result |
| --- | --- | --- |
| `governance/codex-router/node_modules/.bin/tsx` | exists; symbolic link; mode `777`; target `../tsx/dist/cli.mjs` | PASS |

Local OS temp directory observed:

```text
/tmp
```

## Static Safety Check

| Surface | Finding | Result |
| --- | --- | --- |
| named-test pattern | Matches exactly five selected tests at lines `648`, `690`, `712`, `740`, and `767`. | PASS |
| test temp root | Selected tests create temp directories with `mkdtemp(join(tmpdir(), "codex-router-provider-registry-"))`. | PASS |
| test writes | Selected tests write only lock files under `baseDir` / `lockPath`. | PASS_WITH_NOTE |
| test cleanup | Selected tests call `rm(baseDir, { recursive: true, force: true })` in `finally`. | PASS_WITH_AUTH_REQUIRED |
| implementation writes | `FileSystemProviderManifestStore` resolves the passed `baseDir`, writes state/lock/temp files under it, renames temp state into `provider-manifests.json`, and unlinks lock files. | PASS_WITH_AUTH_REQUIRED |
| external effects | No network, env credential read, spawn, exec, dependency install/audit, smoke, canary, deploy, sync, release, or repository-root mutation pattern observed in the selected test body. | PASS |

## Preflight Result

PASS, but exact-run remains gated.

The next execution gate may run only the exact command listed above, and only
after explicit authorization, because it intentionally writes temporary files
and recursively removes generated temp directories under:

```text
/tmp/codex-router-provider-registry-*
```

Marker:

```text
PHASE_11_FILE_PROVIDER_MANIFEST_STORE_PERSISTENCE_PREFLIGHT_PASS_NO_EXECUTION
```
