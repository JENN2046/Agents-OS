# Message Bus Delivery Ledger Plan

This document is a forward plan, not a completion report.

It records the next direction for the Codex-to-Codex Message Bus after the
CEA-028 channel freeze and the current project direction update. The bus remains
an agent-to-agent communication order layer inside Codex: it passes information
between registered Codex agents, prevents duplicate handling, and keeps
conversations and task flows ordered and non-conflicting.

## Planning Basis

The current Message Bus already provides a deterministic delivery state machine:

- message capture
- route marking
- reply capture
- reply correlation
- duplicate `message_id` rejection
- duplicate reply rejection
- `conversation_id` and `correlation_id` matching
- inverted `from` / `to` reply matching
- TTL expiration
- max-round blocking
- audit events and message snapshots

The next work should build on that foundation instead of replacing it.

OneRing is useful as an implementation reference for ledger, isolation,
snapshot, record-only, and conservative failure patterns. It should not be
copied as a routing model. Its fuzzy diff ideas belong in advisory and audit
surfaces, not in the Message Bus delivery decision path.

## Non-Goals

This plan does not make Message Bus a governance layer.

Message Bus must not decide:

- role authority
- Commander authority
- workspace permissions
- real repository access
- write permission
- commit / push / deploy / release policy
- secrets policy
- AGENTS.md interpretation

This plan also does not unlock Phase 8 direct real-repository managed
Worker/Reviewer runs. Phase 8 remains blocked unless the App Server schema
exposes `readableRoots` or an equivalent restricted readable-root capability.

## CEA-029: Agent Message Delivery Ledger Contract

Taskbook:

- `docs/CEA-029_AGENT_MESSAGE_DELIVERY_LEDGER_CONTRACT.md`
- `data/jobs/cea-029-agent-message-delivery-ledger-contract.taskbook.json`

Goal: make delivery integrity explicit as a ledger contract while preserving the
existing deterministic Message Bus state machine.

Scope:

- add a `MessageLedgerStore` abstraction
- keep the default implementation in memory
- record message, reply, route, and conversation state through the store
- add stable `payload_hash` and `delivery_fingerprint` fields
- include registered thread identity in ledger records when routing is involved
- document exact idempotency and ordering rules
- add tests for the delivery ledger contract

Recommended fields:

```text
message_id
reply_to
conversation_id
correlation_id
from
to
fromThreadId
toThreadId
kind
state
round
payload_hash
delivery_fingerprint
created_at
routed_at
replied_at
expired_at
failed_at
failure_reason
```

Idempotency rules:

- one `message_id` can be accepted only once
- one `reply_to` can receive only one reply
- one `conversation_id` cannot reuse a `correlation_id`
- a reply must match the original message `conversation_id`
- a reply must match the original message `correlation_id`
- a reply must invert the original message `from` / `to`
- expired, blocked, failed, or done conversations must reject new traffic

Ordering rule:

- default mode should be single-flight per conversation
- a conversation should not accept a new outbound message while a previous
  message in the same conversation is still captured or routed and has not yet
  been replied, expired, failed, or blocked
- future parallel conversation support must be explicit and separately tested

Payload exposure rule:

- Message Bus may validate and route raw payloads internally
- ledger and external review packages should prefer `payload_hash` and
  `delivery_fingerprint`
- raw payloads should not be copied into broad evidence packages by default

Acceptance:

- duplicate `message_id` is rejected
- duplicate reply to the same `reply_to` is rejected
- wrong `conversation_id` reply is rejected
- wrong `correlation_id` reply is rejected
- wrong reply direction is rejected
- new message before the previous in-conversation message closes is rejected
- expired message reply is rejected
- blocked/done conversation traffic is rejected
- ledger snapshot can reconstruct accepted messages, replies, route state, and
  rejection reasons without relying on raw payload exposure

## CEA-030: Conversation Snapshot and Idempotency Guard

Taskbook:

- `docs/CEA-030_CONVERSATION_SNAPSHOT_AND_IDEMPOTENCY_GUARD.md`
- `data/jobs/cea-030-conversation-snapshot-and-idempotency-guard.taskbook.json`

Goal: add a compact conversation snapshot that helps audit and validate delivery
order.

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
state
timestamp
```

Uses:

- fast duplicate checks
- round-order review
- cross-role traffic review
- evidence package summaries
- recovery and audit displays

Non-goals:

- do not merge conversations by content similarity
- do not repair IDs automatically
- do not infer routing targets from fuzzy content matches

## CEA-031: Record-Only / Observe-Only Mode

Taskbook:

- `docs/CEA-031_RECORD_ONLY_OBSERVE_ONLY_MODE.md`
- `data/jobs/cea-031-record-only-observe-only-mode.taskbook.json`

Goal: support safe practical trials where Message Bus validates and records
traffic without claiming that live downstream execution happened.

Mode behavior:

```text
normal:
  capture, validate, route, reply, resume

observe_only:
  capture, validate, ledger, audit
  do not resume or perform live downstream routing
```

Audit status must not overclaim. Observed traffic should use a distinct state
such as `OBSERVED` or `DRY_ROUTE_RECORDED`, not `ROUTED`.

Uses:

- WRE dry-runs
- Commander route review
- external audit demonstrations
- Phase 8 gated rehearsals while direct real-repository managed runs remain
  blocked

Acceptance:

- observe-only mode records accepted envelopes
- observe-only mode still rejects malformed, duplicate, or cross-wired traffic
- observe-only mode does not claim live route/resume
- reports and snapshots clearly label observed traffic

## CEA-032: Fuzzy Duplicate Advisory

Taskbook:

- `docs/CEA-032_FUZZY_DUPLICATE_ADVISORY.md`
- `data/jobs/cea-032-fuzzy-duplicate-advisory.taskbook.json`

Goal: learn from fuzzy diff patterns without using them for delivery decisions.

Fuzzy advisory may flag suspected near-duplicates:

```json
{
  "suspected_near_duplicate": true,
  "similarity": 0.94,
  "compared_with": "msg_worker_003",
  "action_taken": "NONE"
}
```

Allowed uses:

- Commander review of possibly repeated task instructions
- audit hints
- receipt/report near-duplicate summaries
- context ledger cleanup suggestions

Hard limits:

- fuzzy advisory must not route messages
- fuzzy advisory must not reject messages
- fuzzy advisory must not merge conversations
- fuzzy advisory must not repair `message_id`, `reply_to`, `conversation_id`, or
  `correlation_id`
- fuzzy advisory must not grant authority or change workspace permissions

## CEA-033: Append-Only Persistent Ledger Pilot

Taskbook:

- `docs/CEA-033_APPEND_ONLY_PERSISTENT_LEDGER_PILOT.md`
- `data/jobs/cea-033-append-only-persistent-ledger-pilot.taskbook.json`

Goal: pilot durable ledger storage after the store contract is stable.

Preferred order:

1. JSONL append-only ledger
2. SQLite indexed ledger only if query volume and durability needs justify it

JSONL is preferred first because it matches the project's current evidence and
review-package style. SQLite can be evaluated later for long-running or
high-query workloads.

Acceptance:

- append-only records preserve event order
- persisted records exclude secrets and private state
- persisted records can reconstruct conversation summaries
- external review packages can include manifest/hash summaries without raw
  payload expansion by default

## CEA-035: Human Conversation Observer Window

Taskbook:

- `docs/CEA-035_HUMAN_CONVERSATION_OBSERVER_WINDOW.md`
- `data/jobs/cea-035-human-conversation-observer-window.taskbook.json`

Goal: add a local human observer window so the Commander can inspect how Codex
agents talk to each other.

This task intentionally permits raw dialogue content to be displayed in a local
Commander observer surface. That permission is limited to the observer window:
raw dialogue content must not become the default payload for external review
packages, governance decisions, AGENTS.md interpretation, or workspace
permissions.

Preferred first cut:

- CLI transcript viewer for existing `data/message-logs/*.json` files
- static local HTML timeline output

Visual direction:

- selected direction: calm timeline-card UI based on the rendered Direction C
  concept
- background: dynamic black starfield, subtle and low contrast
- starfield animation must remain behind the content and must not reduce
  transcript readability
- left navigation groups logs by project folder
- clicking a project folder reveals that project's thread queue
- selecting a thread opens a center timeline
- center timeline uses compact cards like the Commander reference screenshot,
  with time, role, state/category label, title, and dialogue excerpt
- raw dialogue content is visible in the local observer, but external review
  package defaults remain hash/manifest oriented

Acceptance:

- local Commander can view agent message and reply content
- transcript shows route identity, delivery state, timestamps, and `reply_to`
  relationships
- project folder navigation opens thread queues
- center transcript uses timeline-style cards for agent dialogue events
- transcript can filter by `conversation_id`
- observer does not mutate Message Bus state, perform live routing, or resume
  agents
- external review package defaults remain hash/manifest oriented unless a later
  task explicitly scopes raw transcript export

## CEA-034: Message Bus Line Closeout and Readiness Matrix

Taskbook:

- `docs/CEA-034_MESSAGE_BUS_LINE_CLOSEOUT_READINESS_MATRIX.md`
- `data/jobs/cea-034-message-bus-line-closeout-readiness-matrix.taskbook.json`

Goal: close out the Message Bus engineering enhancement line after CEA-029
through CEA-033 and CEA-035 with a readiness matrix.

The closeout should state what is complete, what is usable, what remains
blocked, and what is outside Message Bus responsibility. It must preserve the
boundary that Message Bus is communication-order infrastructure and delivery
integrity only. It must not claim governance ownership, AGENTS.md
interpretation, production readiness, or Phase 8 direct real-repository unlock.

## CEA-036: Live Conversation Observer Tail

Taskbook:

- `docs/CEA-036_LIVE_CONVERSATION_OBSERVER_TAIL.md`
- `data/jobs/cea-036-live-conversation-observer-tail.taskbook.json`

Goal: upgrade the CEA-035 observer from static replay to a local live-tail view.

This is a post-closeout follow-up after CEA-034. It should add a `--watch` or
equivalent mode to `npm run channel:observe` so the Commander can watch Codex
agent conversation events appear as the message log grows. It must remain a
local-only read-only observer and must not route, resume, approve, reject, or
mutate messages.

Preferred command:

```bash
npm run channel:observe -- --watch
```

Required boundary:

- local-only
- read-only
- no governance
- no agent resume
- no route mutation
- no external review package raw payload by default
- no Phase 8 direct real-repository unlock

## Recommended Execution Order

```text
CEA-029  Agent Message Delivery Ledger Contract
CEA-030  Conversation Snapshot and Idempotency Guard
CEA-031  Record-Only / Observe-Only Mode
CEA-032  Fuzzy Duplicate Advisory
CEA-033  Append-Only Persistent Ledger Pilot
CEA-035  Human Conversation Observer Window
CEA-034  Message Bus Line Closeout and Readiness Matrix
CEA-036  Live Conversation Observer Tail
```

CEA-029 and CEA-030 are complete. The next executable implementation task is
CEA-031 unless Commander explicitly chooses the observer line. CEA-034 has been
closed out. CEA-036 is a post-closeout follow-up opened because the static
observer does not provide real-time tailing.
