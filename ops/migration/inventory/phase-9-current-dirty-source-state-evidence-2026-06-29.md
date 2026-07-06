# Phase 9 Current Dirty Source State Evidence - 2026-06-29

Status: evidence only; no source edit, revert, test, typecheck, build, npm
script, smoke, canary, dependency install, dependency audit, network, remote,
sync, deploy, or workspace mutation was performed by this evidence step.

This evidence records the current dirty source state observed after the Phase 9
loader exact-run and typecheck support exact-run closeouts.

## Inputs

| Input | SHA-256 | Use |
| --- | --- | --- |
| `ops/migration/receipts/rules-assets-phase-9-loader-behavior-narrow-exact-run-review-closeout-receipt-2026-06-29.md` | `8b076dd38551b5cab5163a1478ce1ecb50c51ce479f7deb52694490f0088ac49` | Last closed loader exact-run gate. |
| `ops/migration/receipts/rules-assets-phase-9-typecheck-support-exact-run-review-closeout-receipt-2026-06-29.md` | `719cc84ac36f89bacacbf8122cb07d3ae173df57707d907ac22899854f86fbb8` | Last closed typecheck support gate. |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-9-current-dirty-source-state-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-9-current-dirty-source-state-readiness-receipt-2026-06-29.md` | absent |
| `ops/migration/plans/phase-9-current-source-revalidation-plan-2026-06-29.md` | absent |

## Current Git Status

`governance/codex-router` currently reports:

```text
 M packages/desktop-live-adapter/src/index.ts
 M tests/desktop-live-adapter-governance.test.ts
```

Diff summary:

```text
packages/desktop-live-adapter/src/index.ts    | 103 ++++++++++++-
tests/desktop-live-adapter-governance.test.ts | 206 ++++++++++++++++++++++++++
2 files changed, 305 insertions(+), 4 deletions(-)
```

## Current Vs HEAD Hashes

| File | HEAD SHA-256 | Current SHA-256 |
| --- | --- | --- |
| `governance/codex-router/packages/desktop-live-adapter/src/index.ts` | `1eebb1893cbb508c229b407349433c8a7dd39a66e9fe1b941f7238b06f0da3eb` | `c28819e9df08e3774aa2c51fd87f88ff2b439db4cb5fe95c86b4da3532e36f66` |
| `governance/codex-router/tests/desktop-live-adapter-governance.test.ts` | `5709839ac69e73b5abdbd1dc793fe396139d623ae83aedd0950eeb686f98adcc` | `7f9ab9d905294d51854de8fe0db5372201d771eec2cda685f3c193d366ba173c` |

## Observed Change Shape

`packages/desktop-live-adapter/src/index.ts` current diff appears to:

- add optional `observationBus`, `governanceState`, and `onGovernanceUpdate`
  fields to `RunDesktopTaskInput`, `ResumeDesktopTaskInput`, and internal host
  dispatch execution inputs
- pass those fields through to `executeDesktopPlan`
- add `applyHostDispatchFailureToGovernance`
- add `createHostDispatchErrorClass`
- route failed host dispatch blocking reasons through recovery governance when
  governance is produced

`tests/desktop-live-adapter-governance.test.ts` current diff appears to:

- import `EventEmitter`
- import `runDesktopTask`
- add fake codex-cli stream/child helpers
- add three new governance tests:
  - `governance: codex-cli host dispatch failure appends anomaly and calls onGovernanceUpdate`
  - `governance: codex-cli host dispatch third failure triggers recovery result`
  - `governance: successful codex-cli host dispatch does not trigger governance updates`

## Static Checks

| Check | Result |
| --- | --- |
| `git diff --check` for the two modified files | PASS; no whitespace error reported. |
| Added-line scan for write/delete, network, env, credentials, npm test, direct `child_process`, dependency install, and secret-like names | No direct high-risk command or credential pattern observed in added lines. |
| Added-line scan for execution-adjacent terms | Observed fake `spawn` injection, `EventEmitter`, fake streams, and `observationBus`; these are expected test surfaces for a future narrow revalidation. |

## Evidence Boundary

This evidence confirms only the current dirty source state and static diff
shape. It does not validate the dirty source behavior or compile health.

Prior Phase 9 closeouts remain historical for the source state they recorded,
but future source-related gates must use the current hashes above or stop.

## Result

Current dirty source state has been recorded. The next safe step is a
current-source revalidation plan that treats the dirty source hashes as the new
preflight inputs.

Marker:

```text
PHASE_9_CURRENT_DIRTY_SOURCE_STATE_EVIDENCE_RECORDED_NO_VALIDATION
```
