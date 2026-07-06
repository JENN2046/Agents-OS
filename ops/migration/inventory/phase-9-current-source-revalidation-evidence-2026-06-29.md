# Phase 9 Current Source Revalidation Evidence - 2026-06-29

Status: executed; PASS with post-execution drift limits.

This evidence records the exact commands authorized by the Phase 9 current
source revalidation plan and preflight receipt.

## Authorization Inputs

| Input | SHA-256 | Result |
| --- | --- | --- |
| `ops/migration/plans/phase-9-current-source-revalidation-plan-2026-06-29.md` | `6a84b355bcf4774849bb51d259bdaec68cbd22d4a594b9b7dac82fb9d23604df` | stable |
| `ops/migration/receipts/rules-assets-phase-9-current-source-revalidation-preflight-receipt-2026-06-29.md` | `adc1506d2f9f89dd9a9cdf92c240c2d3f552c1572094590e25b493a80008fd3b` | stable |
| `governance/codex-router/packages/desktop-live-adapter/src/index.ts` | `c28819e9df08e3774aa2c51fd87f88ff2b439db4cb5fe95c86b4da3532e36f66` | stable after execution; matches current `HEAD` |
| `governance/codex-router/tests/desktop-live-adapter-governance.test.ts` | `7f9ab9d905294d51854de8fe0db5372201d771eec2cda685f3c193d366ba173c` | stable after execution; matches current `HEAD` |
| `governance/codex-router/package.json` | `1b47d214f9061cdef874a8fe6a8c3793b0192aa2f483cd34cced8cbf7ee52fa0` | stable after execution |
| `governance/codex-router/package-lock.json` | `830567045e78d2c5a46dd433035391c1c21f29a1e7dde83aace0f332ae855f23` | stable after execution |
| `governance/codex-router/tsconfig.json` | `45e1952e19954cd2c20f1c4d590e05984c5fdc80dd4d9e400d3b59ce85b69f33` | stable after execution |
| `governance/codex-router/routing-policy.yaml` | `9767b71709daf4c17544f7e68ea2aab8dc4eef3232df7250dc70e907dba3aa12` | stable after execution |

Target absence confirmed before creation:

| Target | State |
| --- | --- |
| `ops/migration/inventory/phase-9-current-source-revalidation-evidence-2026-06-29.md` | absent before creation |
| `ops/migration/receipts/rules-assets-phase-9-current-source-revalidation-receipt-2026-06-29.md` | absent before evidence creation |
| `ops/migration/receipts/rules-assets-phase-9-current-source-revalidation-review-closeout-receipt-2026-06-29.md` | absent |

## Commands Executed

Working directory for both commands:

```text
governance/codex-router
```

Command A:

```text
./node_modules/.bin/tsc -p tsconfig.json --noEmit
```

Command B:

```text
./node_modules/.bin/tsx --test --test-name-pattern '^(governance: codex-cli host dispatch failure appends anomaly and calls onGovernanceUpdate|governance: codex-cli host dispatch third failure triggers recovery result|governance: successful codex-cli host dispatch does not trigger governance updates)$' tests/desktop-live-adapter-governance.test.ts
```

## Result Summary

| Command | Tool exit code | Summary |
| --- | --- | --- |
| Command A | `0` | TypeScript diagnostics output was empty; Codex tool wall time approximately `9.9 s`. |
| Command B | `0` | TAP reported `16` tests, `3` pass, `0` fail, `13` skipped, `0` todo; TAP duration `768.051294 ms`; Codex tool wall time approximately `1.7 s`. |

Selected Command B tests passed:

- `governance: codex-cli host dispatch failure appends anomaly and calls onGovernanceUpdate`
- `governance: codex-cli host dispatch third failure triggers recovery result`
- `governance: successful codex-cli host dispatch does not trigger governance updates`

## Post-Execution Drift Note

After execution, the validated implementation and governance test files still
matched the hashes above. However, `git status --short` also showed additional
uncommitted changes outside the planned command surface:

```text
 M .agent_board/CHECKPOINT.md
 M .agent_board/HANDOFF.md
 M .agent_board/RUN_STATE.md
 M .agent_board/TASK_QUEUE.md
 M .agent_board/VALIDATION_LOG.md
 M docs/current/CURRENT_STATE.md
 M docs/current/state-sync-record.json
 M scripts/sync-state-sync-display.ts
 M tests/state-sync-display-sync.test.ts
```

The newly observed `scripts/sync-state-sync-display.ts` and
`tests/state-sync-display-sync.test.ts` drift was not part of this plan's named
test surface. This evidence therefore cannot be upgraded into whole-tree current
working-tree acceptance.

## Evidence Boundary

This run confirms only:

- direct `tsc --noEmit` passed at execution time
- the three selected codex-cli host-dispatch governance tests passed
- the validated `desktop-live-adapter` implementation and governance test files
  remained stable after execution

This run does not confirm:

- current whole-tree acceptance after the post-execution state-sync source drift
- state-sync display behavior acceptance
- full loader acceptance
- full host-dispatcher acceptance
- provider acceptance
- live-host acceptance
- telemetry/audit acceptance
- consumer integration acceptance
- package script acceptance
- broad `npm test` acceptance
- smoke/canary acceptance
- dependency installability/security/freshness acceptance
- source edit, revert, merge, release, remote, sync, deploy, or workspace-write
  acceptance

## Result

Current-source revalidation completed for the selected command surface with both
commands passing. Acceptance is limited by post-execution drift outside the
selected command surface.

Marker:

```text
PHASE_9_CURRENT_SOURCE_REVALIDATION_EVIDENCE_COLLECTED_PASS_WITH_POST_EXECUTION_DRIFT_LIMITS
```
