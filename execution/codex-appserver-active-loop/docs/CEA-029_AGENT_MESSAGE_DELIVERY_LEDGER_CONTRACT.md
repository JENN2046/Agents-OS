# CEA-029: Agent Message Delivery Ledger Contract

Status: READY

Created: 2026-07-08T18:47:53+08:00

Taskbook: `data/jobs/cea-029-agent-message-delivery-ledger-contract.taskbook.json`

Source plan: `docs/MESSAGE_BUS_DELIVERY_LEDGER_PLAN.md`

## Mission

Make the Codex-to-Codex Message Bus delivery integrity explicit as a ledger
contract while preserving the existing deterministic Message Bus state machine.

The bus remains the agent-to-agent communication order layer inside Codex. Its
job is to pass information between registered Codex agents, prevent duplicate
handling, and keep conversations and task flows ordered and non-conflicting.

## Scope

- add a `MessageLedgerStore` abstraction
- keep the default ledger implementation in memory
- record message, reply, route, and conversation state through the ledger
- add stable `payload_hash` and `delivery_fingerprint` fields
- include registered thread identity in ledger records when routing is involved
- document exact idempotency and ordering rules
- add focused tests for ledger, idempotency, ordering, and thread identity

## Non-Goals

- do not make Message Bus a governance layer
- do not interpret AGENTS.md
- do not unlock Phase 8 direct real-repository managed runs
- do not add fuzzy duplicate advisory
- do not add observe-only mode
- do not add SQLite or persistent storage
- do not modify Commander authority, workspace policy, approval policy, or
  real repository access policy

## Required Contract

Idempotency:

- one `message_id` can be accepted only once
- one `reply_to` can receive only one reply
- one `conversation_id` cannot reuse a `correlation_id`
- a reply must match the original message `conversation_id`
- a reply must match the original message `correlation_id`
- a reply must invert the original message `from` / `to`

Ordering:

- default mode is single-flight per conversation
- a conversation must not accept a new outbound message while a previous message
  in the same conversation is still captured or routed and has not yet been
  replied, expired, failed, or blocked
- future parallel conversation support must be explicit and separately tested

Payload exposure:

- Message Bus may validate and route raw payloads internally
- ledger and external review packages should prefer `payload_hash` and
  `delivery_fingerprint`
- raw payloads should not be copied into broad evidence packages by default

## Suggested Implementation Steps

1. Add `src/stores/message_ledger.ts`.
2. Define `MessageLedgerStore` and an in-memory implementation.
3. Add stable canonical hashing for message and reply payloads.
4. Wire `message_bus.ts` to record through the ledger without changing its
   governance boundary.
5. Extend router/bus records with `fromThreadId` and `toThreadId` when routing
   data is available.
6. Add single-flight conversation rejection.
7. Add focused unit tests.
8. Update `docs/CODEX_CHANNEL_MESSAGE_BUS.md` and `docs/EVENT_CONTRACT.md` only
   as needed to reflect the implemented contract.

## Acceptance

- duplicate `message_id` is rejected
- duplicate reply to the same `reply_to` is rejected
- wrong `conversation_id` reply is rejected
- wrong `correlation_id` reply is rejected
- wrong reply direction is rejected
- new message before the previous in-conversation message closes is rejected
- expired message reply is rejected
- blocked or done conversation traffic is rejected
- ledger snapshot can reconstruct accepted messages, replies, route state, and
  rejection reasons without relying on raw payload exposure
- Message Bus remains outside governance, role authority, workspace policy, and
  AGENTS.md interpretation

## Validation

Required:

```bash
npm run build
npm run test:unit
npm run channel:smoke
npm run channel:multiturn
npm run channel:multirole
```

Recommended if time permits:

```bash
npm run validate
```

## Evidence To Produce

On completion, produce a report and receipt only after implementation and
validation actually happen:

- `data/reports/cea-029_agent_message_delivery_ledger_contract.json`
- `data/receipts/2026-07-08-cea-029-agent-message-delivery-ledger-contract.receipt.md`

Do not create completion evidence before implementation and validation pass.
