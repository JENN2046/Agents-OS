# Phase 11 Provider Execution Runner Controlled Read-Only Evidence - 2026-06-29

Status: executed; PASS with limits.

This evidence records the Phase 11 provider execution runner controlled
read-only exact-run.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-11-provider-execution-runner-controlled-readonly-plan-2026-06-29.md` | `24c037b56bb7684836f1e32861e438309655720e7c87d7d1f80eac9c57e73182` | stable |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-preflight-receipt-2026-06-29.md` | `de87530e9a06783b55407c8ac669f93230c8a57566f70a6697c24e74772da6ab` | stable |
| `governance/codex-router/tests/host-dispatcher.test.ts` | `43986b46e0ed8d9b616b8d29ec35bfd88c6bd8349d4eee6a84a5358685f6ceac` | stable after execution |
| `governance/codex-router/packages/host-dispatcher/src/index.ts` | `176fdfe0f05e2a8b34f820657f4014d5bd4cb3f981c0bf2bfb69a98608853db0` | stable after execution |
| `governance/codex-router/packages/providers/codex-cli/src/index.ts` | `7805ddeeb235f0ee9a803cd146488f483641a6474162ca4ca8425f54dc115487` | stable after execution |
| `governance/codex-router/packages/provider-core/src/index.ts` | `e60969b505c18857d7405f51c4d0d44d95343f373d861b3f2031a10925347fef` | stable after execution |
| `governance/codex-router/packages/provider-registry/src/index.ts` | `c761c97aa4bb8367f5624dd43101d90d624813403473ce910d1f8cc181ad9a86` | stable after execution |
| `governance/codex-router/packages/codex-cli-host/src/index.ts` | `fa8d4e3e08cd8d654a13589dc7d89274c082b5ef576fa6ec2e20312165f25383` | stable after execution |
| `governance/codex-router/packages/contracts/src/index.ts` | `7268d7778c45934cfcd624f2987adc390256d4f928defa1acf159f283d2dc9da` | stable after execution |
| `governance/codex-router/packages/desktop-decision-runner/src/index.ts` | `e785d1b5e48b5335657f039a5e32b2302c7bcc149cee13c112fca00546dfa833` | stable after execution |
| `governance/codex-router/packages/policy-config/src/index.ts` | `d30d2f23e6ab5ee6785130da77b4fa4c5965e1106673a95425c2412e15bb9598` | stable after execution |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-11-provider-execution-runner-controlled-readonly-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-11-provider-execution-runner-controlled-readonly-review-closeout-receipt-2026-06-29.md` | absent |

Preflight `governance/codex-router` HEAD:

```text
c7f39cbff5fb7847796916945faff11ade3d9adc
```

Post-execution `governance/codex-router` HEAD:

```text
bed92be781d2a0e8eee2356d8bb068c018802dca
```

HEAD movement note:

- `bed92be` is a docs/state-only commit: `docs(state): record opaque host dispatch normalization`
- selected source file hashes remained stable
- selected source files had no uncommitted diff after execution

## Command Executed

Working directory:

```text
governance/codex-router
```

Command:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(host dispatcher dispatches ready read-only runner results through provider permits|host dispatcher validates provider registry selection before read-only runner dispatch|host dispatcher formal read-only dispatch requires registry and metadata before spawn|host dispatcher formal read-only dispatch executes only through guarded fake spawner|host dispatcher dry-runs read-only runner provider dispatch without spawn)$' tests/host-dispatcher.test.ts
```

## Result Summary

| Field | Result |
| --- | --- |
| Tool exit code | `0` |
| TAP tests | `21` |
| TAP selected pass | `5` |
| TAP fail | `0` |
| TAP skipped | `16` |
| TAP todo | `0` |
| TAP duration | `821.60233 ms` |
| Codex tool wall time | approximately `1.7 s` |

Selected passing tests:

- `host dispatcher dispatches ready read-only runner results through provider permits`
- `host dispatcher validates provider registry selection before read-only runner dispatch`
- `host dispatcher formal read-only dispatch requires registry and metadata before spawn`
- `host dispatcher formal read-only dispatch executes only through guarded fake spawner`
- `host dispatcher dry-runs read-only runner provider dispatch without spawn`

## Evidence Boundary

This run confirms only:

- selected read-only runner result to provider permit dispatch tests passed
- selected provider registry selection before runner dispatch passed
- selected formal read-only metadata/registry pre-spawn gates passed
- selected guarded fake-spawner formal dispatch passed
- selected read-only provider dry-run without spawn passed
- non-selected tests were skipped by the named-test pattern

This run does not grant:

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

The Phase 11 provider execution runner controlled read-only exact-run completed
with exit code `0` and TAP `5` selected pass / `0` fail / `16` skipped.

Marker:

```text
PHASE_11_PROVIDER_EXECUTION_RUNNER_CONTROLLED_READONLY_EVIDENCE_COLLECTED_PASS_WITH_LIMITS
```
