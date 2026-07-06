# Phase 10 Local MCP Runtime Readiness Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the narrow local Agent OS MCP runtime exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-10-local-mcp-runtime-readiness-plan-2026-06-29.md` | `7c93d6480974c89ddbd7b1c81f0b8e24d80844a720d8d7e9fb69a48e69262cf3` | stable |
| `ops/migration/receipts/rules-assets-phase-10-local-mcp-runtime-readiness-preflight-receipt-2026-06-29.md` | `c72a11e921706d7e11db93517e2d8f64e5fddf509aeb80cdb96d7da60706c738` | stable |
| `governance/codex-router/tests/agent-os-mcp-local-runtime.test.ts` | `5051b4ba568108a8ba6e0e3d311120b51befbf7ecdc61cc19bf0d09279655fef` | stable after execution |

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
./node_modules/.bin/tsx --test --test-name-pattern '^(Agent OS MCP local runtime blocks mutating task creation by default|Agent OS MCP local runtime creates a governed run and provider plan without execution|Agent OS MCP local runtime consumes approval permits into a planned provider plan)$' tests/agent-os-mcp-local-runtime.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `19` |
| TAP selected pass | `3` |
| TAP fail | `0` |
| TAP skipped | `16` |
| TAP todo | `0` |
| TAP duration | `905.459033 ms` |
| Codex tool wall time | approximately `2.5 s` |

Selected passing tests:

- `Agent OS MCP local runtime blocks mutating task creation by default`
- `Agent OS MCP local runtime creates a governed run and provider plan without execution`
- `Agent OS MCP local runtime consumes approval permits into a planned provider plan`

## Evidence Boundary

This run confirms only:

- the selected local MCP runtime tests pass
- default mutation blocking works for the selected surface
- governed run/provider-plan creation works in memory without real provider
  execution for the selected surface
- approval permit consumption into a planned provider plan works for the
  selected surface
- non-selected tests were skipped by the named-test pattern
- the run did not dirty `governance/codex-router`

This run does not grant:

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

The Phase 10 local MCP runtime readiness exact-run completed with exit code `0`
and TAP `3` selected pass / `0` fail / `16` skipped.

Marker:

```text
PHASE_10_LOCAL_MCP_RUNTIME_READINESS_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
