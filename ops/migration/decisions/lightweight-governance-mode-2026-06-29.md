# Lightweight Governance Mode - 2026-06-29

Status: active decision.

Decision:
`LIGHTWEIGHT_GOVERNANCE_MODE_ADOPTED_FOR_FUTURE_GATES`.

This decision changes the default migration/runtime validation rhythm from a
heavy per-gate evidence stack to a lighter operating mode. The goal is to keep
safety and traceability without letting governance become the work.

## Why This Changes

The earlier phases proved the control plane can produce detailed plan,
preflight, evidence, receipt, and closeout records. That is useful for high-risk
gates, but it is too heavy as the default.

Going forward, AGENTS OS should move faster by using lightweight records for
low-risk local gates and reserving heavy ceremony for genuinely dangerous
surfaces.

## New Default Rhythm

For ordinary low-risk local gates, use:

| Artifact | Purpose |
| --- | --- |
| Gate Card | One short section or file stating exact scope, allowed action, disallowed action, and stop conditions. |
| Run Receipt | Command/result/hash/risk note after execution. |
| Phase Rollup | One phase-level summary that closes multiple lightweight gates together. |

Do not create separate per-gate plan, preflight receipt, evidence, receipt, and
closeout files unless the gate is escalated.

## Lightweight Gate Rules

A gate may use lightweight mode when all are true:

- local only
- exact command or exact read boundary is known
- selected files or test names are narrow
- no real credentials
- no network, remote, deploy, release, or sync
- no broad formatting or broad generated-file rewrite
- no destructive operation outside known temp paths
- no unresolved selected-source drift

For these gates, the Run Receipt is enough evidence if it records:

- exact command or exact read boundary
- result summary
- key source hashes or selected-source stability note
- working tree note when relevant
- limits explicitly not granted

## Escalation Rules

Use the heavier flow only when a gate touches one or more of these:

- real Codex CLI execution
- network, remote agent, sync, deploy, release, or publishing
- credentials, env files, tokens, auth stores, or secret-bearing logs
- workspace-write execution
- recursive delete or cleanup outside a generated temp directory
- dependency install, upgrade, audit, or lockfile rewrite
- broad `npm test`, broad package scripts, smoke, canary, or e2e suites
- unclear source drift in selected files
- any operation where rollback would be non-trivial

Heavy flow may still use:

- explicit authorization plan
- preflight receipt
- evidence file
- execution receipt
- closeout receipt

But that is no longer the default.

## Naming Guidance

Prefer fewer files:

```text
ops/migration/receipts/<phase>-<gate>-run-receipt-YYYY-MM-DD.md
ops/migration/receipts/<phase>-rollup-receipt-YYYY-MM-DD.md
```

Only create separate plans or inventories when they add real clarity.

## Boundary

This decision does not weaken safety gates. It only reduces repeated paperwork
for gates that are already local, narrow, reversible, and low-risk.

Previously created heavy artifacts remain valid historical evidence. Future
gates should follow this lightweight mode unless an escalation rule applies.

## Result

Future AGENTS OS migration/runtime gates default to lightweight governance.

Marker:

```text
LIGHTWEIGHT_GOVERNANCE_MODE_ADOPTED_FOR_FUTURE_GATES
```
