# Phase 11 File Provider Manifest Store Persistence Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the authorized Phase 11 file provider manifest store
persistence exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-11-file-provider-manifest-store-persistence-exact-run-authorization-plan-2026-06-29.md` | `48fab9084c94e6115fac222937c8940ac78a469ec34ba1e8bad3912a0c7567ec` | stable |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-preflight-receipt-2026-06-29.md` | `aff1e3909496a4c45f35f7ab3602a3944122b7987c400d3d4d4a1817092cd697` | stable |
| `governance/codex-router/tests/provider-registry.test.ts` | `1172dc2d7aa031cfe736e73fd79c2b29d4e2a409a440f345290f439238d3baad` | stable after execution |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable after execution |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable after execution |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-11-file-provider-manifest-store-persistence-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status after execution: clean.

Current `governance/codex-router` HEAD:

```text
88b84c66e7c815ca5797507c9e957cf5ad38eba2
```

## Temp Boundary Observation

Before execution:

| Prefix | Count |
| --- | --- |
| `/tmp/codex-router-provider-registry-*` | `0` |

After execution:

| Prefix | Count |
| --- | --- |
| `/tmp/codex-router-provider-registry-*` | `0` |

The selected tests intentionally created, wrote, read, and removed temporary
store directories under the authorized `/tmp/codex-router-provider-registry-*`
boundary.

## Command Executed

Working directory:

```text
governance/codex-router
```

Command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(file provider manifest store persists provider metadata across instances|file provider manifest store rejects duplicates and persists deletes|file provider manifest store refuses mutations while another lock is present|file provider manifest store does not remove a fresh lock during stale cleanup|file provider manifest store does not remove a stale-looking lock owned by a live process)$' tests/provider-registry.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `43` |
| TAP selected pass | `5` |
| TAP fail | `0` |
| TAP skipped | `38` |
| TAP todo | `0` |
| TAP duration | `788.475363 ms` |
| Codex tool wall time | approximately `2.0 s` |

Selected passing tests:

- `file provider manifest store persists provider metadata across instances`
- `file provider manifest store rejects duplicates and persists deletes`
- `file provider manifest store refuses mutations while another lock is present`
- `file provider manifest store does not remove a fresh lock during stale cleanup`
- `file provider manifest store does not remove a stale-looking lock owned by a live process`

## Evidence Boundary

This run confirms only:

- selected file provider manifest store persistence tests passed
- selected duplicate/delete persistence tests passed
- selected lock timeout and stale-lock safety tests passed
- non-selected tests were skipped by the named-test pattern
- no leftover `/tmp/codex-router-provider-registry-*` directories were observed
- the run did not dirty `governance/codex-router`

This run does not grant:

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

The Phase 11 file provider manifest store persistence exact-run completed with
exit code `0` and TAP `5` selected pass / `0` fail / `38` skipped.

Marker:

```text
PHASE_11_FILE_PROVIDER_MANIFEST_STORE_PERSISTENCE_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
