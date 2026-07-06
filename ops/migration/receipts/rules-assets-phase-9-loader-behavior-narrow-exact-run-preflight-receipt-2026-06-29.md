# Phase 9 Loader Behavior Narrow Exact-Run Preflight Receipt - 2026-06-29

Status: PASS; preflight only; no loader test, npm script, build, typecheck,
smoke, canary, runtime/router broad test, consumer integration, source edit,
dependency install, dependency audit, network, remote, telemetry upload, sync,
deploy, or workspace mutation has been executed.

Decision:
`PHASE_9_LOADER_BEHAVIOR_NARROW_EXACT_RUN_PREFLIGHT_PASS_NO_EXECUTION`.

This receipt confirms that the planned loader behavior narrow exact-run is ready
for a separately authorized execution step. It does not execute the command.

## Inputs Checked

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | stable |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | `e19e4755cf98f34a25fa4a2d7f4c46644703cfd38651540ad1c49236d69d7dc5` | stable |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-review-closeout-receipt-2026-06-29.md` | `530cd5915e5f0b1c0872e6a75e4c9f4a87c3c2e5abd67cc0f82caebbe42b5bd0` | stable |
| `ops/migration/plans/phase-9-loader-behavior-narrow-plan-2026-06-29.md` | `620182a55ff73d4951947b75be46e72b850ab5c3d59fe44533e3db567a4b1e9d` | stable |
| `ops/migration/plans/phase-9-loader-behavior-narrow-exact-run-authorization-plan-2026-06-29.md` | `084b454045e1695182bef045ccf80b74d52d40a9ededad20f5112580ef61f956` | stable |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable |
| `governance/codex-router/tests/desktop-live-adapter.test.ts` | `7e3daae27d57a0e2e5be5f2ea6c4a53e9cb2bcebbca706ac03d4a667d728eaa9` | stable |

Imported implementation files checked:

| Implementation file | SHA-256 | Result |
| --- | --- | --- |
| `governance/codex-router/packages/policy-config/src/index.ts` | `d30d2f23e6ab5ee6785130da77b4fa4c5965e1106673a95425c2412e15bb9598` | stable |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | stable |
| `governance/codex-router/packages/desktop-decision-runner/src/index.ts` | `e785d1b5e48b5335657f039a5e32b2302c7bcc149cee13c112fca00546dfa833` | stable |
| `governance/codex-router/packages/desktop-live-adapter/src/index.ts` | `1eebb1893cbb508c229b407349433c8a7dd39a66e9fe1b941f7238b06f0da3eb` | stable |
| `governance/codex-router/packages/execution-observation/src/index.ts` | `5cad01f0b9f8bb7bead197124df7e242e4f370e116a3464322815d62c67082e9` | stable |
| `governance/codex-router/packages/codex-desktop-bindings/src/index.ts` | `05b743b9393659cd7ef6ac9fb406ecb568cbcf25353495175a16d4b11271b19a` | stable |
| `governance/codex-router/packages/state-manager/src/index.ts` | `b47a609ddf8ace133089c812d8562ab9bcb4ef4fa4c6fda4fb5064d3ba9caf3b` | stable |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-preflight-receipt-2026-06-29.md` | absent before creation |
| `ops/migration/inventory/phase-9-loader-behavior-narrow-exact-run-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-receipt-2026-06-29.md` | absent |

`governance/codex-router` git status: clean.

## Exact Command Confirmed

Future command authorized for the next execution gate:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(desktop live adapter does not execute blocked runner results|desktop live adapter executes primitives sequentially when handlers exist|desktop live adapter normalizes raw handler output into typed envelopes)$' tests/desktop-live-adapter.test.ts
```

Future working directory:

```text
governance/codex-router
```

Local runner check:

| Tool | Observation | Result |
| --- | --- | --- |
| `governance/codex-router/node_modules/.bin/tsx` | exists; symbolic link; mode `777`; target `../tsx/dist/cli.mjs` | PASS |

## Static Named-Test Check

The planned test-name pattern matched exactly three test declarations:

| Line | Matched test |
| --- | --- |
| `136` | `desktop live adapter does not execute blocked runner results` |
| `175` | `desktop live adapter executes primitives sequentially when handlers exist` |
| `204` | `desktop live adapter normalizes raw handler output into typed envelopes` |

The next test after the selected set begins with:

```text
desktop live adapter redacts already-shaped shell command envelopes
```

That adjacent redaction-fixture test is excluded from the selected pattern.

## Static Risk Check

| Surface | Finding | Result |
| --- | --- | --- |
| selected test bodies | No write/delete, network/remote, env/credential, dependency install/audit, telemetry upload, source mutation, or live host binding calls found. | PASS |
| selected blocked-runner test | Contains `availableTools: ["shell_command"]` as decision input text; no `shell_command` handler is supplied and the test asserts no primitive handler runs. | PASS_WITH_NOTE |
| helper/import area | Contains imported recording helpers not used by the three selected tests. | PASS_WITH_NOTE |
| policy loader | `loadPolicyFromFile` reads the local `routing-policy.yaml` through `readFile(path, "utf8")`. | PASS_ALLOWED_LOCAL_READ |
| desktop live adapter persistence paths | Implementation has conditional `auditStore`, `checkpointStore`, `memoryAdapter`, and `observationBus` hooks; selected tests do not pass those stores. `persistAudit` returns when no `auditStore` is supplied. | PASS_WITH_NOTE |

No stop condition was triggered by static preflight.

## Preflight Result

PASS.

The next execution gate may run only the exact command listed above, from the
listed working directory, and must create:

| Future target | Purpose |
| --- | --- |
| `ops/migration/inventory/phase-9-loader-behavior-narrow-exact-run-evidence-2026-06-29.md` | Redacted command output and selected test result evidence. |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-receipt-2026-06-29.md` | Execution receipt and acceptance boundary. |

## Limits Carried Forward

This preflight does not grant:

- loader execution result
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

## Stop Conditions For Execution Gate

Stop before execution if:

- any input hash drifts
- execution evidence or receipt targets already exist
- `tsx` is missing or resolves outside the local project dependency surface
- the command differs from the exact command in this receipt
- the named-test pattern would execute any test outside the three selected test
  names
- output handling would expose credentials, env values, token-like strings,
  private paths, or broad raw logs
- the result would be framed as full loader/runtime/router/consumer acceptance

## Result

The Phase 9 loader behavior narrow exact-run preflight is PASS. No loader test
command has been executed.

Marker:

```text
PHASE_9_LOADER_BEHAVIOR_NARROW_EXACT_RUN_PREFLIGHT_PASS_NO_EXECUTION
```
