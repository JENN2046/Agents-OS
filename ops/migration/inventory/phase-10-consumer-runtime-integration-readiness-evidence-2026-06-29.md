# Phase 10 Consumer Runtime Integration Readiness Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the first Phase 10 consumer/runtime integration readiness
exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-consumer-runtime-integration-readiness-plan-2026-06-29.md` | `7d88f36d7342c3b7b8e16a3f56a3613a409a4191f1c28423ab834f9cba936c9a` | stable |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-preflight-receipt-2026-06-29.md` | `a2c595cf4bfda1b3e72f2513c8a65924d88ca3add90502fd6f8ca6d8005ec30f` | stable |
| `governance/codex-router/tests/formal-readonly-cli-integration-readiness.test.ts` | `967440de0f7f37dac57cb1e8e616beeeb8a50f7fe0507cc7bbe7b39eab2f77e7` | stable after execution |
| `governance/codex-router/scripts/run-formal-readonly-cli-integration-readiness.ts` | `f16eff5de444d877b62136e9c3659e5eec2c86f682fa4d0ac08a44f1b8b82bdb` | stable after execution |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-10-consumer-runtime-integration-readiness-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status after execution: clean.

Current `governance/codex-router` HEAD:

```text
88b84c66e7c815ca5797507c9e957cf5ad38eba2
```

## Command Executed

Working directory:

```text
governance/codex-router
```

Command:

```text
./node_modules/.bin/tsx --test tests/formal-readonly-cli-integration-readiness.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `4` |
| TAP pass | `4` |
| TAP fail | `0` |
| TAP skipped | `0` |
| TAP todo | `0` |
| TAP duration | `410.55172 ms` |
| Codex tool wall time | approximately `1.3 s` |

Passed tests:

- `formal read-only CLI integration readiness passes with local preflight evidence`
- `formal read-only CLI integration readiness blocks stale guard evidence`
- `formal read-only CLI integration readiness blocks broadened provider source`
- `formal read-only CLI integration readiness writer persists sanitized json`

## Evidence Boundary

This run confirms only:

- local formal read-only CLI integration readiness review behavior passed
- stale/broadened evidence blocking behavior passed
- sanitized JSON writer behavior passed in a temp directory
- the run did not dirty `governance/codex-router`

This run does not grant:

- formal integration execution authorization
- real Codex CLI execution acceptance
- consumer/runtime full acceptance
- host/provider/live-host full acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

The Phase 10 consumer/runtime integration readiness exact-run completed with
exit code `0` and TAP `4` pass / `0` fail.

Marker:

```text
PHASE_10_CONSUMER_RUNTIME_INTEGRATION_READINESS_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
