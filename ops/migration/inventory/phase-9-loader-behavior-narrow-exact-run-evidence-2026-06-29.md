# Phase 9 Loader Behavior Narrow Exact-Run Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the exact local loader behavior command authorized by the
Phase 9 loader behavior narrow exact-run authorization plan and preflight
receipt.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-loader-behavior-narrow-exact-run-authorization-plan-2026-06-29.md` | `084b454045e1695182bef045ccf80b74d52d40a9ededad20f5112580ef61f956` | stable |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-preflight-receipt-2026-06-29.md` | `52be7fa208df1ab21f293e150a18993ac58de15de357cfdc56212c0bfd3b7d34` | stable |
| `governance/codex-router/tests/desktop-live-adapter.test.ts` | `7e3daae27d57a0e2e5be5f2ea6c4a53e9cb2bcebbca706ac03d4a667d728eaa9` | stable after execution |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-9-loader-behavior-narrow-exact-run-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status after execution: clean.

## Command Executed

Working directory:

```text
governance/codex-router
```

Command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(desktop live adapter does not execute blocked runner results|desktop live adapter executes primitives sequentially when handlers exist|desktop live adapter normalizes raw handler output into typed envelopes)$' tests/desktop-live-adapter.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP reported tests | `22` |
| TAP selected pass count | `3` |
| TAP fail count | `0` |
| TAP skipped count | `19` |
| TAP todo count | `0` |
| TAP reported duration | `832.094532 ms` |
| Codex tool wall time | approximately `1.8 s` |

Note: custom shell marker lines printed `__EXIT_CODE=` and
`__DURATION_MS=0` because the PowerShell-to-WSL wrapper consumed shell
variables in the marker expression. They are not used as the source of truth.
The Codex tool exit code and TAP summary are used instead.

## Selected Tests Passed

| TAP index | Test | Result |
| --- | --- | --- |
| `1` | `desktop live adapter does not execute blocked runner results` | pass |
| `2` | `desktop live adapter executes primitives sequentially when handlers exist` | pass |
| `3` | `desktop live adapter normalizes raw handler output into typed envelopes` | pass |

## Skipped Tests

The Node test runner loaded the full module and registered `22` tests. The
`--test-name-pattern` filter skipped `19` non-selected tests with the message
`test name does not match pattern`.

This includes the adjacent redaction-fixture test:

```text
desktop live adapter redacts already-shaped shell command envelopes
```

It was not executed.

## Evidence Boundary

This run confirms only:

- the selected loader base behavior tests pass locally
- the selected named-test pattern selects three passing tests
- unmatched tests are skipped by the test runner
- the selected test file and local routing policy hash remained stable after
  execution
- the `governance/codex-router` git status remained clean after execution

This run does not confirm:

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

## Result

The Phase 9 loader behavior narrow exact-run completed with exit code `0` and
TAP PASS counts for the three selected tests.

Marker:

```text
PHASE_9_LOADER_BEHAVIOR_NARROW_EXACT_RUN_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
