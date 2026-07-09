# Codex-to-Codex Message Bus

CEA-023 added the missing Codex-to-Codex communication channel. CEA-024
hardens the bus with strict runtime validation, generalized route status,
message TTL, max-round protection, and append-only route events. CEA-025 proves
that the hardened bus can preserve routing integrity across two Worker <->
Reviewer dialogue rounds. CEA-026 proves controlled three-role routing across
Worker, Reviewer, and Verifier Codex threads.
CEA-027 freezes the boundary: the message bus is transport infrastructure, not
a governance layer. CEA-028 freezes the current channel line as a completed
minimal communication channel.
CEA-029 keeps that boundary and adds an in-memory delivery ledger contract for
message/reply/route/conversation integrity. CEA-030 adds compact conversation
snapshots derived from that ledger for delivery-order and idempotency review.
CEA-031 adds observe-only mode for safe practical trials where traffic is
validated, recorded, and audited without claiming live downstream routing or
resume. CEA-032 adds fuzzy duplicate advisory as an audit hint only; it never
routes, rejects, merges, repairs ids, or grants authority.
CEA-033 adds a JSONL append-only persistent ledger pilot so Message Bus delivery
evidence can survive process lifetime without broad raw payload expansion.
CEA-035 adds a local-only Commander observer view for explicitly opened
conversation logs; raw dialogue is visible there only, not in external review
packages by default.

The Codex-to-Codex Message Bus is a minimal communication channel. It only
transmits, routes, correlates, and records messages. It does not implement
governance, role authority, workspace policy, or AGENTS.md interpretation.

## Current Project Direction

The Codex-to-Codex Message Bus is the agent-to-agent communication order layer
inside Codex. Its function and responsibility are to pass information between
Codex agents, prevent duplicate handling, and keep conversations and task flows
ordered and non-conflicting.

This direction keeps the bus focused on delivery integrity:

- deliver each accepted message to the intended registered agent identity
- reject or ignore duplicate message IDs and duplicate replies
- preserve `conversation_id`, `correlation_id`, reply, and round ordering
- prevent Worker / Reviewer / Verifier traffic from crossing wires
- record auditable events and message logs for route, reply, timeout, reject,
  blocked, resumed, and done states
- expose `payload_hash` and `delivery_fingerprint` records for review without
  copying raw payloads into broad evidence packages

The bus remains outside governance. It does not decide who has authority, which
workspace is safe, whether a real repository can be read, or whether an action
can be approved.

Forward plan: `docs/MESSAGE_BUS_DELIVERY_LEDGER_PLAN.md`.

## Command

```bash
npm run channel:smoke
npm run channel:multiturn
npm run channel:multirole
```

## Scope

This is not a snapshot review flow. The smoke does not export a snapshot, review
source code, or touch a real repository cwd.

The channel proves:

- Worker Codex emits `MESSAGE_TO_CODEX`
- Bridge captures and routes the message
- Reviewer Codex emits `CODEX_MESSAGE_REPLY`
- Bridge correlates the reply by `reply_to`, `conversation_id`, and `correlation_id`
- Bridge returns the reply to Worker Codex
- Worker Codex resumes and emits `DONE`

CEA-024 preserves that path and adds guards for malformed messages, duplicate
IDs, invalid targets, mismatched replies, expired messages, and excessive route
rounds.

CEA-025 extends the proof from a single exchange to a two-round dialogue in one
`conversation_id`:

- round 1 Worker `MESSAGE_TO_CODEX`
- round 1 Reviewer `CODEX_MESSAGE_REPLY`
- Worker resumes
- round 2 Worker `MESSAGE_TO_CODEX`
- round 2 Reviewer `CODEX_MESSAGE_REPLY`
- Worker resumes and emits `DONE`

CEA-026 extends the proof to three roles in one controlled synthetic workflow:

- Worker emits `MESSAGE_TO_CODEX` to Reviewer
- Reviewer emits `CODEX_MESSAGE_REPLY` to Worker
- Worker emits `MESSAGE_TO_CODEX` to Verifier
- Verifier emits `CODEX_MESSAGE_REPLY` to Worker
- Worker resumes and emits `DONE`

## Protocol

Worker to Reviewer:

```json
{
  "type": "MESSAGE_TO_CODEX",
  "message_id": "msg_worker_001",
  "correlation_id": "corr_channel_001",
  "conversation_id": "conv_channel_001",
  "from": "worker",
  "to": "reviewer",
  "kind": "question",
  "payload": {
    "question": "Please review this decision point.",
    "context": [],
    "expected_response": "decision"
  }
}
```

Role labels are routing identities. Examples:

- `worker`
- `reviewer`
- `verifier`
- `planner`
- `executor`
- `auditor`
- `critic`

The bus validates role-label syntax only. Registered and active thread lookup is
handled by the router / registry. Project-specific role duties and authority are
delegated to AGENTS.md and working context.

Allowed outbound message `kind` values:

- `question`
- `answer`
- `request_review`
- `request_verification`
- `request_decision`
- `decision`
- `notice`
- `status`
- `block_notice`
- `clarification`
- `block`

Reviewer to Worker:

```json
{
  "type": "CODEX_MESSAGE_REPLY",
  "message_id": "msg_reviewer_001",
  "reply_to": "msg_worker_001",
  "correlation_id": "corr_channel_001",
  "conversation_id": "conv_channel_001",
  "from": "reviewer",
  "to": "worker",
  "kind": "answer",
  "payload": {
    "decision": "continue",
    "reason": "Synthetic channel test is safe.",
    "next_instruction": "Continue and emit DONE."
  }
}
```

Allowed reply `kind` values:

- `question`
- `answer`
- `request_review`
- `request_verification`
- `request_decision`
- `decision`
- `notice`
- `status`
- `block_notice`
- `clarification`
- `block`

Reply `payload.decision` is a non-empty string. The bus does not interpret
whether a decision means approve, block, write, deploy, or release. Bridge
rejects malformed payloads before they enter the message bus.

## Bus State

Outbound messages move through:

- `CAPTURED`
- `ROUTED`
- `REPLIED`
- `EXPIRED`
- `FAILED`

Delivery records use generalized status names:

- `MESSAGE_ROUTED`
- `REPLY_ROUTED`

Observe-only delivery records use dry status names:

- `DRY_ROUTE_RECORDED`
- `DRY_REPLY_RECORDED`

Direction is expressed by `from`, `to`, `fromThreadId`, `toThreadId`,
`messageId`, `replyTo`, `conversationId`, and `correlationId`.

## CEA-029 Delivery Ledger Contract

CEA-029 adds `MessageLedgerStore` as an in-memory delivery integrity ledger.
The ledger records accepted messages, routes, replies, conversation state, and
rejections without storing raw payload content.

Ledger entries include:

- `message_id`
- `reply_to`
- `conversation_id`
- `correlation_id`
- `from`
- `to`
- `fromThreadId`
- `toThreadId`
- `message_kind`
- `state`
- `round`
- `round_count`
- `max_rounds`
- `payload_hash`
- `delivery_fingerprint`
- `failure_reason`

`payload_hash` is a stable SHA-256 hash of the canonical message or reply
payload. `delivery_fingerprint` is a stable SHA-256 hash of delivery identity
fields and the payload hash. External review should prefer these fields over raw
payload expansion.

Idempotency and ordering rules:

- one `message_id` can be accepted only once
- one `reply_to` can receive only one reply
- one `conversation_id` cannot reuse a `correlation_id`
- replies must match the original `conversation_id`
- replies must match the original `correlation_id`
- replies must invert the original `from` / `to`
- default conversation mode is single-flight
- a new outbound message in the same conversation is rejected while a previous
  message is still `CAPTURED` or `ROUTED`
- expired-message replies are rejected
- blocked or done conversation traffic is rejected

The ledger does not add governance. It does not interpret AGENTS.md, role
authority, workspace policy, approval policy, or real repository access policy.

## CEA-030 Conversation Snapshot And Idempotency Guard

CEA-030 derives a compact per-conversation snapshot from the in-memory delivery
ledger. It is a read-only audit view over delivery evidence.

Each conversation snapshot retains a delivery trail with:

- `round`
- `message_id`
- `reply_to`
- `conversation_id`
- `correlation_id`
- `from`
- `to`
- `fromThreadId`
- `toThreadId`
- `payload_hash`
- `state`
- `timestamp`

Snapshots also expose an idempotency guard summary:

- accepted `message_id` values
- accepted `reply_to` values
- accepted outbound `correlation_id` values
- duplicate `message_id`, `reply_to`, and `correlation_id` evidence
- current in-flight message id when one exists
- `idempotency_ok`
- `ordering_ok`
- `guard_ok`

The snapshot helps review duplicate handling, round order, cross-role traffic,
evidence package summaries, and recovery displays. It does not merge
conversations by content similarity, repair ids automatically, infer route
targets from fuzzy content, or interpret authority.

## CEA-031 Record-Only / Observe-Only Mode

CEA-031 adds `observe_only` mode to Message Bus and Router flows.

Normal mode:

```text
capture -> validate -> route -> reply -> resume
```

Observe-only mode:

```text
capture -> validate -> ledger -> audit
```

Observe-only mode records accepted envelopes and route intent, but does not
claim live downstream routing or live resume. It uses:

- `MESSAGE_OBSERVED`
- `REPLY_OBSERVED`
- `DRY_ROUTE_RECORDED`
- `DRY_REPLY_RECORDED`
- ledger / snapshot state `OBSERVED`

Observe-only mode still rejects malformed messages, duplicate ids, duplicate
replies, cross-wired replies, expired messages, blocked conversations, and
single-flight conflicts. A message observed but not yet matched by an observed
reply remains in-flight for ordering purposes.

Observe-only mode must not emit `MESSAGE_ROUTED`, `REPLY_ROUTED`, or
`WORKER_RESUMED` for observed-only traffic. Snapshots and reports must label
observed traffic separately from live routed traffic.

Observe-only mode does not add fuzzy duplicate advisory, persistent storage,
real managed Worker / Reviewer execution, governance, AGENTS.md interpretation,
or Phase 8 direct real-repository access.

## CEA-032 Fuzzy Duplicate Advisory

CEA-032 adds a side-channel advisory helper for near-duplicate review. It is not
part of the Message Bus delivery decision path.

Advisory metadata uses:

```json
{
  "suspected_near_duplicate": true,
  "similarity": 0.94,
  "compared_with": "msg_worker_003",
  "action_taken": "NONE",
  "authority": "ADVISORY_ONLY"
}
```

The advisory compares sanitized, hash-aware summaries of already validated
message envelopes. Its output includes hashes, similarity, and compared ids, but
does not include raw payload text.

Hard limits:

- fuzzy advisory must not route messages
- fuzzy advisory must not reject messages
- fuzzy advisory must not merge conversations
- fuzzy advisory must not repair `message_id`, `reply_to`, `conversation_id`, or
  `correlation_id`
- fuzzy advisory must not grant role authority, Commander authority, workspace
  permissions, or approval
- `action_taken` is always `NONE`

Exact delivery rules from CEA-029 through CEA-031 remain the only Message Bus
gate for duplicate ids, reply integrity, route state, conversation ordering, and
observe-only recording.

## CEA-033 Append-Only Persistent Ledger Pilot

CEA-033 adds `JsonlMessageLedgerStore` as a durable pilot implementation of the
CEA-029 `MessageLedgerStore` contract.

The JSONL ledger writes to:

```text
<approved-ledger-root>/<ledger_id>.ledger.jsonl
```

Each line is one sanitized `MessageLedgerEntry`. Persisted records preserve
append order and include the same delivery evidence surface as the in-memory
ledger:

- `kind`
- `at`
- `message_id`
- `reply_to`
- `conversation_id`
- `correlation_id`
- `from`
- `to`
- `fromThreadId`
- `toThreadId`
- `message_kind`
- `state`
- `round`
- `round_count`
- `max_rounds`
- `payload_hash`
- `delivery_fingerprint`
- `message_ids`
- `reply_ids`
- `failure_reason`

The JSONL store sanitizes entries before writing and reconstructs snapshots with
`createMessageLedgerSnapshot()`. Reviewers can then call
`buildConversationSnapshot()` over the persisted snapshot to inspect delivery
order and idempotency without raw payload expansion.

CEA-033 does not add SQLite, governance, AGENTS.md interpretation, broad review
package raw payload inclusion, or Phase 8 direct real repository access.

JSONL ledger failure handling is fail-closed for the current synchronous pilot:
append failures throw a clear `failed to append message ledger entry` error
instead of silently accepting an unpersisted record.

## CEA-035 Human Conversation Observer Window

CEA-035 adds a local Commander observer surface for selected Codex channel logs.
It is a read-only viewer, not a Message Bus control plane.

Command:

```bash
npm run channel:observe -- --log <message-log-json> --format html
```

Defaults:

- selects the newest `data/message-logs/*.json` when `--log` is omitted
- writes static HTML to `data/observer/<job_id>.html`
- searches `data/reports/*.json` for the same `job_id` to display local raw
  dialogue when the message log itself contains route metadata only

Supported filters:

- `--conversation <conversation_id>`
- `--role <role>`
- `--state <state>`

The observer renders:

- left project group and thread queue navigation
- center timeline cards
- role, timestamp, state/category, title, and dialogue excerpt
- message / reply payload content for local Commander inspection
- route metadata including `conversation_id`, `message_id`, `reply_to`,
  `correlation_id`, `from`, `to`, `fromThreadId`, `toThreadId`, `round`, and
  state
- routed, observed, rejected, expired, failed, blocked, and done states when
  present

Secret-like payload keys are redacted in the viewer. The observer must not
mutate Message Bus state, approve, route, reject, resume agents, infer
authority, interpret AGENTS.md, or unlock Phase 8.

## Timeout

Each captured message records `created_at` and `expires_at`.

Rules:

- replies before `expires_at` may be accepted
- replies at or after `expires_at` are rejected
- expired messages are marked `EXPIRED`
- expiration is recorded as `MESSAGE_EXPIRED`

The current smoke config uses `messageTtlMs=300000`.

## Max Rounds

Each completed Worker -> Reviewer -> Worker route cycle increments
`round_count`.

The MVP default is `maxRounds=3`.

If a conversation reaches `maxRounds`, further outbound routing is blocked with
`CONVERSATION_BLOCKED`.

CEA-025 proves both sides of this guard:

- two rounds under `maxRounds=3` pass
- a fourth attempted round with `maxRounds=3` blocks

Conversation state now records:

```json
{
  "conversation_id": "conv_multiturn_001",
  "round_count": 2,
  "max_rounds": 3,
  "message_ids": ["msg_worker_round_1", "msg_worker_round_2"],
  "reply_ids": ["msg_reviewer_round_1", "msg_reviewer_round_2"],
  "status": "DONE"
}
```

`round_count` increments only after a valid reply is routed back to the
originator.

## CEA-025 Multi-turn Dialogue

Single-turn smoke (`npm run channel:smoke`) proves one Worker -> Reviewer ->
Worker exchange. Multi-turn smoke (`npm run channel:multiturn`) proves two
exchanges in one conversation.

Per-round invariants:

- all messages share one `conversation_id`
- each Worker message has a distinct `message_id`
- each Worker message has a distinct `correlation_id`
- each Reviewer reply has a distinct `message_id`
- each Reviewer reply uses `reply_to` for the matching Worker message
- each Reviewer reply preserves that round's `correlation_id`
- `round_count` reaches `2` without tripping `maxRounds=3`

CEA-025 proves two-round Worker <-> Reviewer dialogue only. It does not prove
multi-role dialogue, real repository readiness, workspace write readiness, or
production readiness.

## CEA-026 Multi-role Codex Channel

Multi-role smoke (`npm run channel:multirole`) proves role-isolated routing
among Worker, Reviewer, and Verifier.

Role labels in this synthetic proof:

- Worker starts both outbound role hops and emits final `DONE`.
- Reviewer reviews the first Worker decision and replies to Worker.
- Verifier verifies the route evidence and replies to Worker.

These labels do not grant authority. They only identify registered threads for
the route proof.

Role registry requirements:

- each role has one distinct active thread
- duplicate roles are rejected
- duplicate thread ids are rejected
- missing registered roles are rejected by router lookup
- unsafe role label syntax is rejected
- inactive roles cannot receive routed messages

Per-role route invariants:

- one `conversation_id` is preserved across all role hops
- Worker -> Reviewer uses `corr_worker_reviewer`
- Worker -> Verifier uses `corr_worker_verifier`
- Reviewer replies only to `msg_worker_to_reviewer`
- Verifier replies only to `msg_worker_to_verifier`
- delivery records preserve `fromThreadId` and `toThreadId`

CEA-026 proves Worker / Reviewer / Verifier channel routing only. It does not
prove production readiness, real repository readiness, workspace write readiness,
AGENTS OS integration, VCPToolBox integration, or ChatGPT web integration.

## CEA-027 Channel Boundary

The message bus is not a governance layer.

It owns:

- envelope validation
- delivery integrity state
- reply correlation
- TTL / timeout
- max-round guard
- append-only message log

Router / registry owns:

- registered routing identity lookup
- active target thread check
- delivery routing between registered active thread identities

It does not own:

- role duties
- role authority
- Commander authority
- workspace permissions
- real repository access
- write permissions
- commit / push / deploy / release policy
- secrets policy
- AGENTS.md content

AGENTS.md owns project-specific role authority. Codex runtime executes work under
AGENTS.md, current working context, and active sandbox / approval settings.
Bridge observes, routes, correlates, and records evidence.

## CEA-028 Channel Freeze And Closeout

The channel only transmits information. It does not decide what the information
authorizes.

- CEA-023 proved single-turn communication.
- CEA-024 hardened delivery integrity.
- CEA-025 proved multi-turn communication.
- CEA-026 proved multi-role routing identities.
- CEA-027 froze channel minimalism and AGENTS.md delegation.
- CEA-028 freezes the communication channel as complete for the current line.

The frozen channel owns send, route, reply, correlate, log, timeout / pending
state, and no-message-mixup behavior. Governance, role authority, workspace
policy, approval policy, and AGENTS.md interpretation remain outside the
channel.

Message Bus transmits information.
It does not interpret authority.

## Append-Only Log

CEA-024 and CEA-025 write route events to:

```text
data/message-logs/<job_id>.messages.jsonl
```

Required event names:

- `MESSAGE_CAPTURED`
- `MESSAGE_ROUTED`
- `MESSAGE_OBSERVED`
- `REPLY_CAPTURED`
- `REPLY_ROUTED`
- `REPLY_OBSERVED`
- `MESSAGE_EXPIRED`
- `MESSAGE_REJECTED`
- `CONVERSATION_BLOCKED`
- `WORKER_RESUMED`
- `CHANNEL_DONE`

CEA-029 does not add new emitted channel event names. It mirrors the frozen
event model into a ledger snapshot with hashes, delivery fingerprints, thread
identity, route state, and rejection reasons.

CEA-030 also does not add new emitted channel event names. It derives compact
conversation snapshots from the CEA-029 ledger.

CEA-031 adds observe-only event names for dry route evidence. Normal channel
smokes continue to emit the live route event sequence only.

CEA-033 does not add channel event names. It adds a persistent ledger storage
surface for the CEA-029 ledger record shape.

Each line is a complete JSON object with safe routing metadata such as
`job_id`, `event`, `timestamp`, `round`, `message_id`, `conversation_id`,
`correlation_id`, `from`, and `to`. Secrets, environment variables, tokens,
cookies, and credentials must not be logged.

CEA-025 expected append-only sequence:

```text
MESSAGE_CAPTURED round 1
MESSAGE_ROUTED round 1
REPLY_CAPTURED round 1
REPLY_ROUTED round 1
WORKER_RESUMED round 1
MESSAGE_CAPTURED round 2
MESSAGE_ROUTED round 2
REPLY_CAPTURED round 2
REPLY_ROUTED round 2
WORKER_RESUMED round 2
CHANNEL_DONE
```

CEA-026 expected append-only sequence:

```text
MESSAGE_CAPTURED worker -> reviewer
MESSAGE_ROUTED worker -> reviewer
REPLY_CAPTURED reviewer -> worker
REPLY_ROUTED reviewer -> worker
WORKER_RESUMED after reviewer
MESSAGE_CAPTURED worker -> verifier
MESSAGE_ROUTED worker -> verifier
REPLY_CAPTURED verifier -> worker
REPLY_ROUTED verifier -> worker
WORKER_RESUMED after verifier
CHANNEL_DONE
```

## Status

This channel is frozen as a hardened synthetic minimal communication channel
with single-turn, two-round, and three-role routing-identity proofs. It is not
production-ready, not a real-repository review runtime, and not a
policy-governed multi-role orchestration layer.

## Boundary

The smoke starts real App Server synthetic channel threads with:

- `cwd`: `data/synthetic-workspace`
- `approvalPolicy`: `never`
- `sandbox`: `read-only`
- `sandboxPolicy`: `{ "type": "readOnly", "networkAccess": false }`

Forbidden surfaces remain unused:

- Workspace Agents API
- Responses API
- browser automation
- WebSocket transport
- `thread/shellCommand`
- `command/exec`
- workspace write through App Server
- direct real repository cwd
- snapshot export

## Outputs

- `data/message-logs/cea-023-codex-channel-<timestamp>.json`
- `data/message-logs/cea-023-codex-channel-<timestamp>.messages.jsonl`
- `data/events/cea-023-codex-channel-<timestamp>.events.jsonl`
- `data/reports/cea-023_codex_to_codex_message_bus_mvp.json`
- `data/receipts/<date>-cea-023-codex-to-codex-message-bus-mvp.receipt.md`
- `data/reports/cea-024_message_bus_hardening.json`
- `data/receipts/2026-07-08-cea-024-message-bus-hardening.receipt.md`
- `data/message-logs/cea-025-multiturn-<timestamp>.json`
- `data/message-logs/cea-025-multiturn-<timestamp>.messages.jsonl`
- `data/events/cea-025-multiturn-<timestamp>.events.jsonl`
- `data/reports/cea-025_multi_turn_codex_dialogue.json`
- `data/receipts/2026-07-08-cea-025-multi-turn-codex-dialogue.receipt.md`
- `data/message-logs/cea-026-multirole-<timestamp>.json`
- `data/message-logs/cea-026-multirole-<timestamp>.messages.jsonl`
- `data/events/cea-026-multirole-<timestamp>.events.jsonl`
- `data/reports/cea-026_multi_role_codex_channel.json`
- `data/receipts/2026-07-08-cea-026-multi-role-codex-channel.receipt.md`
- `data/reports/cea-027_channel_minimalism_agentsmd_delegation.json`
- `data/receipts/2026-07-08-cea-027-channel-minimalism-agentsmd-delegation.receipt.md`
- `data/reports/cea-028_channel_freeze_closeout.json`
- `data/receipts/2026-07-08-cea-028-channel-freeze-closeout.receipt.md`
- `data/reports/channel_freeze_manifest.json`
- `data/reports/cea-029_agent_message_delivery_ledger_contract.json`
- `data/receipts/2026-07-08-cea-029-agent-message-delivery-ledger-contract.receipt.md`
- `data/reports/cea-030_conversation_snapshot_idempotency_guard.json`
- `data/receipts/2026-07-08-cea-030-conversation-snapshot-idempotency-guard.receipt.md`
- `data/reports/cea-031_record_only_observe_only_mode.json`
- `data/receipts/2026-07-08-cea-031-record-only-observe-only-mode.receipt.md`
- `data/reports/cea-032_fuzzy_duplicate_advisory.json`
- `data/receipts/2026-07-08-cea-032-fuzzy-duplicate-advisory.receipt.md`
- `data/reports/cea-033_append_only_persistent_ledger_pilot.json`
- `data/receipts/2026-07-08-cea-033-append-only-persistent-ledger-pilot.receipt.md`
- `data/observer/<job_id>.html`
- `data/reports/cea-035_human_conversation_observer_window.json`
- `data/receipts/2026-07-08-cea-035-human-conversation-observer-window.receipt.md`
