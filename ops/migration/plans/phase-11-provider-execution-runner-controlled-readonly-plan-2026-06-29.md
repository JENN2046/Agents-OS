# Phase 11 Provider Execution Runner Controlled Read-Only Plan - 2026-06-29

Status: plan only; no test, typecheck, build, npm script, smoke, canary,
dependency install, dependency audit, source edit, revert, network, remote,
sync, deploy, workspace mutation, or real Codex CLI execution has been executed
by this plan.

This document plans the Phase 11 provider execution runner controlled
read-only gate. It selects a narrow local named-test subset from
`host-dispatcher.test.ts` after the file provider manifest store persistence
gate.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-review-closeout-receipt-2026-06-29.md` | `1b907c7613dfbc3be2ff1a31f6324bf595b4739f48916934c4958406c79ec7b9` | Prior Phase 11 file-store persistence closeout. |
| `governance/codex-router/tests/host-dispatcher.test.ts` | `43986b46e0ed8d9b616b8d29ec35bfd88c6bd8349d4eee6a84a5358685f6ceac` | Selected test file. |
| `governance/codex-router/packages/host-dispatcher/src/index.ts` | `176fdfe0f05e2a8b34f820657f4014d5bd4cb3f981c0bf2bfb69a98608853db0` | Host dispatcher implementation. |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | Codex CLI provider implementation. |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | Provider permit/core implementation. |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | Provider registry implementation. |
| `governance/codex-router/packages/codex-cli-host/src/index.ts` | `fa8d4e3e08cd8d654a13589dc7d89274c082b5ef576fa6ec2e20312165f25383` | Codex CLI host plan/run implementation used behind injected fake spawner. |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | Routing/task envelope contracts. |
| `governance/codex-router/packages/desktop-decision-runner/src/index.ts` | `e785d1b5e48b5335657f039a5e32b2302c7bcc149cee13c112fca00546dfa833` | Read-only runner result generation. |
| `governance/codex-router/packages/policy-config/src/index.ts` | `d30d2f23e6ab5ee6785130da77b4fa4c5965e1106673a95425c2412e15bb9598` | Local policy loader. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Local policy read by selected tests. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-11-provider-execution-runner-controlled-readonly-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-11-provider-execution-runner-controlled-readonly-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-review-closeout-receipt-2026-06-29.md` | absent |

`governance/codex-router` selected source status at plan repair: no diff in
`tests/host-dispatcher.test.ts` or `packages/host-dispatcher/src/index.ts`.
Unrelated state-sync files under `.agent_board/` and `docs/current/` were dirty
and are outside this gate.

Current `governance/codex-router` HEAD:

```text
c7f39cbff5fb7847796916945faff11ade3d9adc
```

## Selected Exact-Run Candidate

Future command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(host dispatcher dispatches ready read-only runner results through provider permits|host dispatcher validates provider registry selection before read-only runner dispatch|host dispatcher formal read-only dispatch requires registry and metadata before spawn|host dispatcher formal read-only dispatch executes only through guarded fake spawner|host dispatcher dry-runs read-only runner provider dispatch without spawn)$' tests/host-dispatcher.test.ts
```

Future working directory:

```text
governance/codex-router
```

## Why This Scope

- It covers ready read-only runner result dispatch through provider permits.
- It covers provider registry selection before read-only runner dispatch.
- It covers formal read-only dispatch fail-closed behavior when registry or
  provider execution metadata is missing before spawn.
- It covers formal read-only dispatch through a guarded injected fake spawner.
- It covers read-only provider dry-run without spawn.
- It excludes later invalid runner/grant/registry matrix tests and all real CLI,
  broad package, smoke, and canary gates.

The selected tests may set `executionMode: "real"` and `realExecutionAllowed:
true` only inside a controlled fake-spawner test path. The spawner is an
in-memory fake child implemented in the test file. This must not be treated as
real Codex CLI execution acceptance.

## Future Preflight Requirements

Before execution, confirm:

- this plan hash is stable
- prior Phase 11 file-store persistence closeout hash is stable
- selected test and implementation hashes are stable
- selected source files have no uncommitted diff
- `node_modules/.bin/tsx` exists and resolves to the local project dependency
  entrypoint
- future evidence/receipt targets are absent
- the named-test pattern matches exactly the five selected tests
- selected test bodies and required helper lines still avoid filesystem writes,
  network, env credential reads, dependency install/audit, real CLI execution,
  smoke, canary, and repository-root mutation
- any observed `secret` / `OPENAI_API_KEY` strings are static negative
  sanitization assertions only

## Repair Note

During preflight, the repository HEAD and selected source hashes were observed
to have moved from the initially drafted plan values. The plan has been repaired
to current local evidence rather than executing against stale hashes. Dirty
state-sync files are treated as an external limitation, not as acceptance
evidence.

## Acceptance Boundary

If the future exact-run passes, the maximum possible result is:

```text
PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_EVIDENCE_PASS_WITH_LIMITS
```

It cannot by itself grant:

- full provider execution acceptance
- real Codex CLI execution acceptance
- remote agent execution acceptance
- full consumer/runtime integration acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- remote, network, sync, deploy, release, or workspace-write acceptance

## Result

Phase 11 provider execution runner controlled read-only behavior is planned but
not executed by this plan. The next safe step is a PASS/FAIL preflight receipt
for the exact command above.

Marker:

```text
PHASE_11_PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_PLAN_CREATED_PREFLIGHT_NEXT_NO_EXECUTION
```
