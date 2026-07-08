# CEA-030: Conversation Snapshot and Idempotency Guard

Status: READY

Created: 2026-07-08T19:43:16+08:00

Depends on: CEA-029 DONE

Taskbook: `data/jobs/cea-030-conversation-snapshot-and-idempotency-guard.taskbook.json`

Source plan: `docs/MESSAGE_BUS_DELIVERY_LEDGER_PLAN.md`

## Mission

Add a compact conversation snapshot layer that helps audit, validate, and
reconstruct Message Bus delivery order without relying on raw payload exposure.

## Scope

- add a conversation delivery snapshot view
- retain recent delivery trail records per conversation
- expose deterministic snapshot fields for messages, replies, routes, and
  conversation state
- strengthen idempotency audit checks using exact ledger identity
- add focused tests for snapshot reconstruction and ordered delivery review
- update Message Bus and event-contract documentation only as needed

## Non-Goals

- do not add fuzzy duplicate advisory
- do not add observe-only mode
- do not add persistent storage
- do not merge conversations by content similarity
- do not repair message IDs automatically
- do not infer routing targets from fuzzy content matches
- do not change governance, role authority, workspace policy, or AGENTS.md
  interpretation
- do not unlock Phase 8 direct real-repository managed runs

## Snapshot Fields

The snapshot should retain the recent delivery trail for each conversation:

```text
round
message_id
reply_to
conversation_id
correlation_id
from
to
fromThreadId
toThreadId
payload_hash
delivery_fingerprint
state
timestamp
reason
```

## Required Behavior

- snapshot output is deterministic
- snapshot output excludes raw payload copies by default
- accepted messages and replies are reconstructable from ledger records
- route identity can be reviewed through `fromThreadId` and `toThreadId`
- rejected, expired, failed, blocked, and done states are visible in audit view
- single-flight ordering remains enforced from CEA-029

## Acceptance

- a two-round conversation snapshot shows ordered message and reply trail
- a multi-role conversation snapshot preserves Worker / Reviewer / Verifier
  route identity
- duplicate and rejected traffic appears as audit state without raw payload
  expansion
- snapshot can explain why a message was blocked, expired, failed, or rejected
- snapshot fields match the CEA-029 ledger contract
- existing channel smoke, multiturn, and multirole behavior stays green

## Validation

Required:

```bash
npm run build
npm run test:unit
npm run channel:smoke
npm run channel:multiturn
npm run channel:multirole
```

Recommended:

```bash
npm run validate
```

## Evidence To Produce

On completion, produce a report and receipt only after implementation and
validation actually happen:

- `data/reports/cea-030_conversation_snapshot_and_idempotency_guard.json`
- `data/receipts/2026-07-08-cea-030-conversation-snapshot-and-idempotency-guard.receipt.md`

Do not create completion evidence before implementation and validation pass.
