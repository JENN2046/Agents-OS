# Phase 9 Loader Behavior Narrow Exact-Run Receipt - 2026-06-29

Status: completed; PASS with limits.

Decision:
`PHASE_9_LOADER_BEHAVIOR_NARROW_EXACT_RUN_COMPLETED_PASS_WITH_LIMITS`.

This receipt records the result of the authorized Phase 9 loader behavior narrow
exact-run. It accepts only limited local loader base behavior evidence.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-loader-behavior-narrow-exact-run-authorization-plan-2026-06-29.md` | `084b454045e1695182bef045ccf80b74d52d40a9ededad20f5112580ef61f956` | stable |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-preflight-receipt-2026-06-29.md` | `52be7fa208df1ab21f293e150a18993ac58de15de357cfdc56212c0bfd3b7d34` | stable |
| `ops/migration/inventory/phase-9-loader-behavior-narrow-exact-run-evidence-2026-06-29.md` | `072064fef03b5e2668d84378995f09562184c4bc8c6a5c5754fca00c94565b13` | created |
| `governance/codex-router/tests/desktop-live-adapter.test.ts` | `7e3daae27d57a0e2e5be5f2ea6c4a53e9cb2bcebbca706ac03d4a667d728eaa9` | stable after execution |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status after execution: clean.

## Command Result

Command executed from `governance/codex-router`:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(desktop live adapter does not execute blocked runner results|desktop live adapter executes primitives sequentially when handlers exist|desktop live adapter normalizes raw handler output into typed envelopes)$' tests/desktop-live-adapter.test.ts
```

Result:

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `22` |
| TAP pass | `3` |
| TAP fail | `0` |
| TAP skipped | `19` |
| TAP todo | `0` |
| TAP duration | `832.094532 ms` |

Selected passing tests:

- `desktop live adapter does not execute blocked runner results`
- `desktop live adapter executes primitives sequentially when handlers exist`
- `desktop live adapter normalizes raw handler output into typed envelopes`

## Acceptance Granted

Granted:

```text
LOCAL_READONLY_LOADER_BASE_BEHAVIOR_EVIDENCE_COLLECTED_WITH_LIMITS
```

Meaning:

- the selected local loader base behavior tests passed
- the run was limited to a named-test pattern in
  `tests/desktop-live-adapter.test.ts`
- non-selected tests were skipped by the runner
- no source hash drift was observed after execution
- no dirty git status was observed in `governance/codex-router` after execution

## Not Granted

This receipt does not grant:

- full loader acceptance
- host-client acceptance
- host-dispatcher acceptance
- provider acceptance
- live-host acceptance
- telemetry/audit acceptance
- consumer integration acceptance
- package script acceptance
- broad `npm test` acceptance
- build/typecheck acceptance
- dependency installability/security/freshness acceptance
- remote, network, registry, sync, deploy, canary, smoke, or workspace-write
  acceptance

## Deferred Gates

Still deferred:

- loader exact-run three-way closeout
- typecheck support exact-run authorization/preflight/execution
- broader loader/host/provider behavior gates
- consumer/runtime integration gates
- broad package script and `npm test` gates

## Result

The Phase 9 loader behavior narrow exact-run completed successfully and grants
only limited local loader base behavior evidence acceptance.

Marker:

```text
PHASE_9_LOADER_BEHAVIOR_NARROW_EXACT_RUN_COMPLETED_PASS_WITH_LIMITS
```
