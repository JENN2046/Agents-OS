# Phase 9 Loader Behavior Narrow Exact-Run Authorization Plan - 2026-06-29

Status: authorization plan only; no loader test, npm script, build, typecheck,
smoke, canary, runtime/router broad test, consumer integration, source edit,
dependency install, dependency audit, network, remote, telemetry upload, sync,
deploy, or workspace mutation has been executed.

This document authorizes a future narrow loader behavior exact-run candidate.
It fixes the working directory, exact command, named-test filter, evidence
targets, redaction policy, acceptance boundary, and stop conditions. It does
not execute the command.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/plans/phase-9-scope-plan-2026-06-29.md` | `65a6305993cc7eecf59f6912c9d63965d71c36f589732ab27cbf1e624eced8fa` | Phase 9 scope authority. |
| `ops/migration/plans/phase-9-runtime-router-loader-consumer-gate-plan-2026-06-29.md` | `e19e4755cf98f34a25fa4a2d7f4c46644703cfd38651540ad1c49236d69d7dc5` | Behavior gate planning authority. |
| `ops/migration/receipts/rules-assets-phase-9-narrow-local-readonly-behavior-exact-run-review-closeout-receipt-2026-06-29.md` | `530cd5915e5f0b1c0872e6a75e4c9f4a87c3c2e5abd67cc0f82caebbe42b5bd0` | Confirms first runtime/router exact-run is closed with loader still deferred. |
| `ops/migration/plans/phase-9-loader-behavior-narrow-plan-2026-06-29.md` | `620182a55ff73d4951947b75be46e72b850ab5c3d59fe44533e3db567a4b1e9d` | Loader narrow planning authority. |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | Static command surface. |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | Local policy file read by selected helper path. |
| `governance/codex-router/tests/desktop-live-adapter.test.ts` | `7e3daae27d57a0e2e5be5f2ea6c4a53e9cb2bcebbca706ac03d4a667d728eaa9` | Selected loader-adapter test file. |

Imported implementation files observed during planning:

| Implementation file | SHA-256 | Boundary note |
| --- | --- | --- |
| `governance/codex-router/packages/policy-config/src/index.ts` | `d30d2f23e6ab5ee6785130da77b4fa4c5965e1106673a95425c2412e15bb9598` | Reads the local policy file through `readFile(path, "utf8")`. |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | Contract parsing support. |
| `governance/codex-router/packages/desktop-decision-runner/src/index.ts` | `e785d1b5e48b5335657f039a5e32b2302c7bcc149cee13c112fca00546dfa833` | Produces local runner decisions used by test helpers. |
| `governance/codex-router/packages/desktop-live-adapter/src/index.ts` | `1eebb1893cbb508c229b407349433c8a7dd39a66e9fe1b941f7238b06f0da3eb` | Executes the selected in-memory primitive handlers. |
| `governance/codex-router/packages/execution-observation/src/index.ts` | `5cad01f0b9f8bb7bead197124df7e242e4f370e116a3464322815d62c67082e9` | Imported by the file but not part of the selected assertions. |
| `governance/codex-router/packages/codex-desktop-bindings/src/index.ts` | `05b743b9393659cd7ef6ac9fb406ecb568cbcf25353495175a16d4b11271b19a` | Imported by the file but not part of the selected assertions. |
| `governance/codex-router/packages/state-manager/src/index.ts` | `b47a609ddf8ace133089c812d8562ab9bcb4ef4fa4c6fda4fb5064d3ba9caf3b` | Type/governance support import. |

Target absence confirmed before creation:

| Target | State before this plan |
| --- | --- |
| `ops/migration/plans/phase-9-loader-behavior-narrow-exact-run-authorization-plan-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-preflight-receipt-2026-06-29.md` | absent |
| `ops/migration/inventory/phase-9-loader-behavior-narrow-exact-run-evidence-2026-06-29.md` | absent |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-receipt-2026-06-29.md` | absent |

Observed local runner surface:

| Tool | Observation |
| --- | --- |
| `governance/codex-router/node_modules/.bin/tsx` | exists; symbolic link; mode `777`; target `../tsx/dist/cli.mjs` |

Workspace Git state: `/home/jenn/AGENTS_OS_Workspace` is not a Git repository.

## Selected Named Tests

The future exact-run is limited to these named tests in
`tests/desktop-live-adapter.test.ts`:

| Line | Test name | Why selected |
| --- | --- | --- |
| `136` | `desktop live adapter does not execute blocked runner results` | Exercises blocked runner result behavior and confirms no primitive handler is called. |
| `175` | `desktop live adapter executes primitives sequentially when handlers exist` | Exercises in-memory handler ordering for `read_thread_terminal`, `spawn_agent`, and `wait_agent`. |
| `204` | `desktop live adapter normalizes raw handler output into typed envelopes` | Exercises typed envelope normalization for in-memory handler outputs. |

Known boundary:

- The test-name filter limits which test bodies should run.
- The full test module is still loaded, so top-level imports, constants,
  helper definitions, and test registration are in scope.
- The test immediately after the selected set starts at line `233` and contains
  secret-redaction fixture strings. That test is intentionally excluded from
  the selected named-test pattern.

## Selected Exact-Run Candidate

Future command candidate:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(desktop live adapter does not execute blocked runner results|desktop live adapter executes primitives sequentially when handlers exist|desktop live adapter normalizes raw handler output into typed envelopes)$' tests/desktop-live-adapter.test.ts
```

Future working directory:

```text
governance/codex-router
```

Allowed local behavior for this candidate:

- load the selected test module
- load local imported TypeScript modules through the local `tsx` runner
- read local `routing-policy.yaml` through `loadPolicyFromFile`
- execute only the three selected named test bodies
- call in-memory primitive handlers supplied by the selected tests
- create in-memory `auditEvents` arrays returned by `executeDesktopPlan`
- use fixed test timestamps and fixed synthetic task envelopes

Not allowed in this candidate:

- `npm test` or any npm script
- broad `tests/*.test.ts` execution
- whole loader/host/dispatcher/live-host test families
- workspace writes, source edits, generated output, dependency installs, or
  lockfile changes
- network, remote, registry, telemetry upload, sync, deploy, canary, smoke, or
  external model calls
- live Codex Desktop host bindings
- persistent audit, checkpoint, memory, telemetry, or observation stores
- consumer integration acceptance

## Planning Evidence Notes

Bounded text review of the selected file showed:

- the selected helper path reads `routing-policy.yaml`
- selected test bodies use in-memory handlers only
- selected tests do not pass `auditStore`, `checkpointStore`, `memoryAdapter`,
  `telemetryStore`, or `observationBus`
- `persistAudit` returns immediately when no `auditStore` is supplied
- `maybePersistExecutionCheckpoint` records only when a `checkpointStore` or
  `memoryAdapter` is supplied
- text-level scan of lines `1-230` found `audit` wording only in the selected
  assertion against the returned `auditEvents` array

Imported implementation files contain telemetry/audit terminology. That is
not an acceptance result; the future preflight must keep telemetry/audit
acceptance out of scope.

## Future Preflight Requirements

Before executing the selected command, create a preflight receipt confirming:

- this authorization plan hash is stable
- Phase 9 scope plan hash is stable
- Phase 9 runtime/router/loader/consumer gate plan hash is stable
- first runtime/router exact-run review closeout hash is stable
- loader narrow plan hash is stable
- `package.json`, `routing-policy.yaml`, selected test file, and listed
  imported implementation file hashes are stable
- `governance/codex-router/node_modules/.bin/tsx` still exists and resolves to
  the local `tsx` package entrypoint
- future evidence and execution receipt targets are absent
- the exact command matches the command in this plan
- the named-test pattern still selects only the three listed test names
- bounded rescans of the selected test lines and helper/import area still avoid
  write/delete, network/remote, env/credential, dependency install/audit,
  telemetry upload, broad tree scan, source mutation, and live host binding
  behavior
- no loader exact-run command has been executed yet

## Future Evidence Targets

If separately authorized after preflight, create:

| Future target | Purpose |
| --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-preflight-receipt-2026-06-29.md` | Confirm hashes, exact command, named-test pattern, local runner, risk scan, target absence, and no execution before the run. |
| `ops/migration/inventory/phase-9-loader-behavior-narrow-exact-run-evidence-2026-06-29.md` | Record command, working directory, exit code, duration, redacted TAP summary, selected test count, and limits. |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-receipt-2026-06-29.md` | Record execution result and acceptance boundary. |

## Output And Redaction Policy

Future exact-run evidence must:

- record command and working directory
- record exit code and duration
- summarize selected/pass/fail counts before logs
- redact credential-like values, env values, token-like strings, private paths,
  and secret-like fixture strings if any appear
- avoid broad raw log inclusion unless needed to diagnose failure
- explicitly state whether the result is evidence-only or grants narrow local
  loader behavior evidence acceptance

## Acceptance Boundary

If the future exact-run passes, the maximum possible immediate result is:

```text
LOCAL_READONLY_LOADER_BASE_BEHAVIOR_EVIDENCE_COLLECTED_WITH_LIMITS
```

It cannot by itself grant:

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

## Stop Conditions

Stop before execution if:

- any required input hash drifts
- future evidence/receipt targets already exist
- `tsx` is missing or resolves outside the local project dependency surface
- the named-test pattern would execute any test outside the three selected test
  names
- selected lines or helper/import surfaces drift into write/delete,
  network/remote, env/credential, dependency install/audit, telemetry upload,
  broad tree scan, source mutation, persistent store, or live host behavior
- the command would run `npm test`, all tests, broad loader/host/dispatcher
  tests, smoke, canary, build, typecheck, or consumer integration
- output handling would expose secrets, env values, token-like strings, private
  paths, or broad raw logs
- the result would be framed as full loader/runtime/router/consumer acceptance

## Result

The Phase 9 loader behavior narrow exact-run is authorized for future preflight
only. The selected command is fixed, but no loader test command has been
executed by this plan.

Marker:

```text
PHASE_9_LOADER_BEHAVIOR_NARROW_EXACT_RUN_AUTHORIZATION_PLAN_CREATED_NO_EXECUTION
```
