# Phase 10 Local MCP Runtime Readiness Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, or workspace mutation has been executed by this plan.

This document plans the second Phase 10 readiness gate: a narrow local Agent OS
MCP runtime exact-run using in-memory stores and no real provider execution.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-10-consumer-runtime-integration-readiness-review-closeout-receipt-2026-06-29.md` | `69ea0a336072ef38f23457cbb9e251429cc8a6a337b8b283a9ea4887a1e4bd88` | Previous Phase 10 readiness closeout. |
| `governance/codex-router/tests/agent-os-mcp-local-runtime.test.ts` | `5051b4ba568108a8ba6e0e3d311120b51befbf7ecdc61cc19bf0d09279655fef` | Selected MCP runtime test file. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-10-local-mcp-runtime-readiness-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-10-local-mcp-runtime-readiness-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-review-closeout-receipt-2026-06-29.md` | absent |

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(Agent OS MCP local runtime blocks mutating task creation by default|Agent OS MCP local runtime creates a governed run and provider plan without execution|Agent OS MCP local runtime consumes approval permits into a planned provider plan)$' tests/agent-os-mcp-local-runtime.test.ts
```

Future working directory:

```text
governance/codex-router
```

Selected tests:

- `Agent OS MCP local runtime blocks mutating task creation by default`
- `Agent OS MCP local runtime creates a governed run and provider plan without execution`
- `Agent OS MCP local runtime consumes approval permits into a planned provider plan`

## Why This Scope

- The selected tests use in-memory kernel, plan, approval permit, and provider
  registry stores.
- The selected tests assert `realProviderExecutionInvoked` is false where
  applicable.
- The selected tests exercise consumer/runtime readiness without real MCP server
  connection, real provider execution, network, remote, smoke, or canary.
- The full file is much larger, so this gate intentionally starts with a named
  subset.

## Future Preflight Requirements

Before execution, confirm:

- this plan hash is stable
- previous Phase 10 readiness closeout hash is stable
- selected test file hash is stable
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- named-test pattern matches exactly the three selected tests
- selected test lines still avoid filesystem writes, network, remote,
  dependency install/audit, real provider execution, live MCP server connection,
  smoke, canary, and repository-root mutation
- no command has been executed yet

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
LOCAL_MCP_RUNTIME_IN_MEMORY_READINESS_EVIDENCE_PASS_WITH_LIMITS
```

It cannot by itself grant:

- full MCP runtime acceptance
- real MCP server acceptance
- real provider execution acceptance
- consumer/runtime full acceptance
- host/provider/live-host full acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

Local MCP runtime readiness is planned but not executed by this plan. The next
safe step is a PASS/FAIL preflight receipt for the exact command above.

Marker:

```text
PHASE_10_LOCAL_MCP_RUNTIME_READINESS_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
