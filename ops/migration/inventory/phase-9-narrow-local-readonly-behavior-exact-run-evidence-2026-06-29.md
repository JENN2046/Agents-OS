# Phase 9 Narrow Local Readonly Behavior Exact-Run Evidence - 2026-06-29

Status: evidence collected.

Scope: narrow local readonly behavior exact-run for selected runtime-control and
routing-engine tests in `governance/codex-router`.

No npm script, broad `npm test`, build, typecheck, validator, smoke, canary,
loader behavior command, consumer integration command, dependency install,
dependency audit, sync, deploy, network, or remote action was executed.

## Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-preflight-receipt-2026-06-29.md` | `2cd8b0000bf14dc2b215a77964e3764aa8d35e34616fa00c78a73a5688d0ae8b` | stable before and after execution |
| `ops/migration/plans/phase-9-narrow-local-readonly-behavior-exact-run-authorization-plan-2026-06-29.md` | `647e7b4e0802c22a0496608a4f1677889d0c859d51fad000f29e04c68945390f` | stable |
| `governance/codex-router/tests/runtime-control.test.ts` | `2e08cbd8afd960dab83b38a8301abebb35c811a195376871db7f85dca462a93a` | stable after execution |
| `governance/codex-router/tests/routing-engine.test.ts` | `faa8ca1e49f9a9a62ec5f2b1014bb07165aefbda510347b4abfbac10c67a81fd` | stable after execution |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable after execution |

## Executed Command

Working directory:

```text
/home/jenn/AGENTS_OS_Workspace/governance/codex-router
```

Command:

```text
./node_modules/.bin/tsx --test tests/runtime-control.test.ts tests/routing-engine.test.ts
```

## Execution Result

| Item | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP version | `13` |
| TAP test count | `5` |
| TAP pass count | `5` |
| TAP fail count | `0` |
| TAP cancelled count | `0` |
| TAP skipped count | `0` |
| TAP todo count | `0` |
| TAP reported duration | `819.106512 ms` |
| Codex tool wall time | approximately `2.2 s` |

Note: the shell wrapper attempted to print custom `__EXIT_CODE` and
`__DURATION_MS` markers, but those marker variables were not reliable in the
PowerShell-to-WSL wrapper output. The authoritative execution status for this
evidence is the tool exit code `0` plus the TAP summary above.

## Passing Subtests

| Subtest | Result |
| --- | --- |
| routing engine covers read-only and small edit tasks | PASS |
| routing engine respects low-risk taskClassHint when text is neutral | PASS |
| routing engine covers engineering, high-risk, and release tasks | PASS |
| routing engine fails closed when a task class host route is missing | PASS |
| runtime control upgrades codex spark to gpt-5.4-mini before larger models | PASS |

## Post-Execution State

| Check | Result |
| --- | --- |
| `governance/codex-router` git status | clean |
| workspace root git status | root is not a Git repository |
| selected test hashes | unchanged |
| `routing-policy.yaml` hash | unchanged |
| source edits | none observed |

## Acceptance Boundary

This evidence supports:

```text
LOCAL_READONLY_RUNTIME_ROUTER_BEHAVIOR_EVIDENCE_COLLECTED_WITH_LIMITS
```

It does not grant:

- loader behavior acceptance
- consumer integration acceptance
- governance router full acceptance
- package script acceptance
- broad `npm test` acceptance
- build/typecheck acceptance
- dependency installability/security/freshness acceptance
- smoke/canary/workspace-write/telemetry acceptance
- network, remote, sync, deploy, branch, release, or operational acceptance

## Result

The narrow local readonly runtime/router exact-run completed successfully with
5 passing tests and 0 failures.

Marker:

```text
PHASE_9_NARROW_LOCAL_READONLY_BEHAVIOR_EXACT_RUN_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
