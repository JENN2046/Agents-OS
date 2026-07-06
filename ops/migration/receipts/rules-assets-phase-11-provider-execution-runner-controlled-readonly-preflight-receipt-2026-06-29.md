# Phase 11 Provider Execution Runner Controlled Read-Only Preflight Receipt - 2026-06-29

Status: PASS_WITH_NOTE; preflight only; no test, typecheck, build, npm script,
smoke, canary, dependency install, dependency audit, source edit, revert,
network, remote, sync, deploy, workspace mutation, or real Codex CLI execution
has been executed by this receipt.

Decision:
`PHASE_11_PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_PREFLIGHT_PASS_WITH_NOTE_NO_EXECUTION`.

## Inputs Checked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-11-provider-execution-runner-controlled-readonly-plan-2026-06-29.md` | `24c037b56bb7684836f1e32861e438309655720e7c87d7d1f80eac9c57e73182` | stable after plan repair |
| `ops/migration/receipts/rules-assets-phase-11-file-provider-manifest-store-persistence-review-closeout-receipt-2026-06-29.md` | `1b907c7613dfbc3be2ff1a31f6324bf595b4739f48916934c4958406c79ec7b9` | stable |
| `governance/codex-router/tests/host-dispatcher.test.ts` | `43986b46e0ed8d9b616b8d29ec35bfd88c6bd8349d4eee6a84a5358685f6ceac` | stable |
| `governance/codex-router/packages/host-dispatcher/src/index.ts` | `176fdfe0f05e2a8b34f820657f4014d5bd4cb3f981c0bf2bfb69a98608853db0` | stable |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable |
| `governance/codex-router/packages/codex-cli-host/src/index.ts` | `fa8d4e3e08cd8d654a13589dc7d89274c082b5ef576fa6ec2e20312165f25383` | stable |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | stable |
| `governance/codex-router/packages/desktop-decision-runner/src/index.ts` | `e785d1b5e48b5335657f039a5e32b2302c7bcc149cee13c112fca00546dfa833` | stable |
| `governance/codex-router/packages/policy-config/src/index.ts` | `d30d2f23e6ab5ee6785130da77b4fa4c5965e1106673a95425c2412e15bb9598` | stable |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-11-provider-execution-runner-controlled-readonly-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-receipt-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-review-closeout-receipt-2026-06-29.md` | absent |

Current `governance/codex-router` HEAD:

```text
c7f39cbff5fb7847796916945faff11ade3d9adc
```

Working tree note:

- selected source files have no uncommitted diff
- unrelated state-sync files under `.agent_board/` and `docs/current/` are dirty
  and are outside this gate

## Exact Command Confirmed

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(host dispatcher dispatches ready read-only runner results through provider permits|host dispatcher validates provider registry selection before read-only runner dispatch|host dispatcher formal read-only dispatch requires registry and metadata before spawn|host dispatcher formal read-only dispatch executes only through guarded fake spawner|host dispatcher dry-runs read-only runner provider dispatch without spawn)$' tests/host-dispatcher.test.ts
```

Working directory:

```text
governance/codex-router
```

Local runner:

| Tool | Observation | Result |
| --- | --- | --- |
| `governance/codex-router/node_modules/.bin/tsx` | exists; symbolic link; mode `777`; target `../tsx/dist/cli.mjs` | PASS |

## Static Safety Check

| Surface | Finding | Result |
| --- | --- | --- |
| named-test pattern | Matches exactly five selected tests at lines `363`, `391`, `417`, `468`, and `503`. | PASS |
| selected test bodies | No filesystem write, network, env credential read, real process spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in lines `363-514`. | PASS |
| selected helper lines | No filesystem write, network, env credential read, real process spawn, exec, dependency install/audit, smoke, canary, or repository-root mutation pattern observed in helper lines `714-1140`. | PASS_WITH_NOTE |
| fake spawner | The formal dispatch success path uses an injected in-memory fake child, not a real CLI process. | PASS_WITH_NOTE |
| `auth` / secret-like terms | `authAvailable: true` is static runner preflight input; `secret` and `OPENAI_API_KEY` are static negative sanitization assertions only. | PASS_WITH_NOTE |

## Preflight Result

PASS_WITH_NOTE.

The next execution gate may run only the exact command listed above. The maximum
possible acceptance remains controlled local read-only evidence, not real Codex
CLI execution acceptance.

Marker:

```text
PHASE_11_PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_PREFLIGHT_PASS_WITH_NOTE_NO_EXECUTION
```
