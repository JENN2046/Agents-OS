# Event Contract

## Worker NEED_REVIEWER

```json
{
  "type": "NEED_REVIEWER",
  "problem_type": "architecture",
  "question": "string",
  "evidence": ["string"],
  "proposed_options": ["string"],
  "recommended_next_action": "string"
}
```

Allowed `problem_type` values are `architecture`, `policy`, `test_failure`, `diff_review`, and `unclear_intent`.

## Reviewer REVIEWER_DECISION

```json
{
  "type": "REVIEWER_DECISION",
  "decision": "continue",
  "reason": "string",
  "next_instruction": "string",
  "constraints": ["string"],
  "evidence_used": ["string"]
}
```

Allowed `decision` values are `continue`, `revise`, `block`, and `request_human_gate`.

## Worker DONE

```json
{
  "type": "DONE",
  "summary": "string",
  "evidence": ["string"]
}
```

## BLOCKED

```json
{
  "type": "BLOCKED",
  "reason": "string",
  "evidence": ["string"]
}
```

## Codex-to-Codex MESSAGE_TO_CODEX

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

## Codex-to-Codex CODEX_MESSAGE_REPLY

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

Bridge must reject replies whose `reply_to`, `conversation_id`,
`correlation_id`, or inverted `from` / `to` endpoints do not match the captured
original message.

Allowed outbound message `kind` values are `question`, `answer`,
`request_review`, `request_verification`, `request_decision`, `decision`,
`notice`, `status`, `block_notice`, `clarification`, and `block`.

Allowed reply `kind` values use the same generic kind set.

Codex peer roles are safe routing labels, not authority definitions. Examples
include `worker`, `reviewer`, `verifier`, `planner`, `executor`, `auditor`, and
`critic`.

`CODEX_MESSAGE_REPLY payload.decision` is a non-empty string. The channel does
not interpret whether it means approve, block, write, deploy, or release.

CEA-024 requires runtime validators to reject malformed payloads before they
enter the message bus.

## Codex-to-Codex Message State

Captured outbound messages record:

```json
{
  "state": "CAPTURED",
  "created_at": "2026-07-08T00:00:00.000Z",
  "expires_at": "2026-07-08T00:05:00.000Z",
  "payload_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "delivery_fingerprint": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
}
```

Allowed message states:

- `CAPTURED`
- `ROUTED`
- `REPLIED`
- `OBSERVED`
- `EXPIRED`
- `FAILED`

Replies must arrive before `expires_at`; late replies are rejected and the
original message is marked `EXPIRED`.

## Codex-to-Codex Delivery Status

Delivery status names are role-neutral:

- `MESSAGE_ROUTED`
- `REPLY_ROUTED`

Observe-only delivery status names are dry-run evidence only:

- `DRY_ROUTE_RECORDED`
- `DRY_REPLY_RECORDED`

Direction must be read from `from`, `to`, `fromThreadId`, `toThreadId`,
`messageId`, `replyTo`, `conversationId`, and `correlationId`.

## Codex-to-Codex Round Guard

Conversation route state records:

```json
{
  "conversation_id": "conv_channel_001",
  "round_count": 1,
  "max_rounds": 3,
  "message_ids": ["msg_worker_001"],
  "reply_ids": ["msg_reviewer_001"],
  "status": "ACTIVE"
}
```

Each completed Worker -> Reviewer -> Worker cycle increments `round_count`.
When `round_count` reaches `max_rounds`, further outbound routing is blocked
with `CONVERSATION_BLOCKED`.

CEA-025 adds the two-round state proof:

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

Round state rules:

- `round_count` increments only after a valid reply is routed back to the originator.
- outbound messages in the same conversation must use distinct `message_id` values.
- outbound messages in the same conversation must use distinct `correlation_id` values.
- default conversation mode is single-flight.
- a new outbound message in the same conversation is rejected while a previous
  message is still `CAPTURED` or `ROUTED`.
- replies must use the matching round's `reply_to`, `conversation_id`, and `correlation_id`.
- Messages after `DONE` are rejected.
- Replies after `BLOCKED` are rejected.

## CEA-029 Message Delivery Ledger

CEA-029 adds an in-memory `MessageLedgerStore` contract. The ledger mirrors the
frozen channel event model into record-only delivery entries. It is designed for
auditing idempotency and ordering without relying on raw payload exposure.

Ledger entries may include:

```json
{
  "kind": "ROUTE",
  "at": "2026-07-08T00:00:00.000Z",
  "message_id": "msg_worker_001",
  "reply_to": "msg_worker_000",
  "conversation_id": "conv_channel_001",
  "correlation_id": "corr_channel_001",
  "from": "worker",
  "to": "reviewer",
  "fromThreadId": "thread_worker_001",
  "toThreadId": "thread_reviewer_001",
  "message_kind": "question",
  "state": "ROUTED",
  "round": 1,
  "round_count": 0,
  "max_rounds": 3,
  "payload_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "delivery_fingerprint": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
}
```

Ledger `kind` values:

- `MESSAGE`
- `ROUTE`
- `REPLY`
- `REJECTION`
- `CONVERSATION`

Ledger records must not store raw payload text. External review packages should
prefer `payload_hash`, `delivery_fingerprint`, route ids, thread ids, state,
round counters, and rejection reasons.

The ledger is still transport evidence only. It does not interpret role
authority, Commander authority, AGENTS.md, workspace policy, approval policy,
or real repository access policy.

## CEA-030 Conversation Snapshot

CEA-030 derives a compact conversation snapshot from the CEA-029 ledger. The
snapshot is a read-only audit view for delivery order, idempotency checks,
cross-role route review, and evidence package summaries.

Conversation snapshots may include:

```json
{
  "conversation_id": "conv_channel_001",
  "status": "ACTIVE",
  "round_count": 2,
  "max_rounds": 3,
  "trail": [
    {
      "round": 1,
      "message_id": "msg_worker_001",
      "reply_to": null,
      "conversation_id": "conv_channel_001",
      "correlation_id": "corr_channel_001",
      "from": "worker",
      "to": "reviewer",
      "fromThreadId": "thread_worker_001",
      "toThreadId": "thread_reviewer_001",
      "payload_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
      "state": "ROUTED",
      "timestamp": "2026-07-08T00:00:00.000Z"
    }
  ],
  "idempotency": {
    "accepted_message_ids": ["msg_worker_001", "msg_reviewer_001"],
    "reply_to_ids": ["msg_worker_001"],
    "correlation_ids": ["corr_channel_001"],
    "duplicate_message_ids": [],
    "duplicate_reply_to_ids": [],
    "duplicate_correlation_ids": [],
    "idempotency_ok": true,
    "ordering_ok": true,
    "guard_ok": true
  }
}
```

Conversation snapshots must not store raw payload text. They also must not merge
conversations by content similarity, repair ids automatically, infer route
targets from fuzzy content, or interpret role / workspace authority.

## CEA-031 Observe-Only Message Events

CEA-031 adds observe-only Message Bus mode for record-only practical trials.
Observed traffic is validated and recorded, but it must not claim live route or
live resume.

Observed message events use:

```json
{
  "event": "MESSAGE_OBSERVED",
  "message_id": "msg_worker_001",
  "conversation_id": "conv_channel_001",
  "correlation_id": "corr_channel_001",
  "from": "worker",
  "to": "reviewer",
  "fromThreadId": "thread_worker_001",
  "toThreadId": "thread_reviewer_001",
  "state": "OBSERVED",
  "payload_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "delivery_fingerprint": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
}
```

Observed replies use:

```json
{
  "event": "REPLY_OBSERVED",
  "message_id": "msg_reviewer_001",
  "reply_to": "msg_worker_001",
  "conversation_id": "conv_channel_001",
  "correlation_id": "corr_channel_001",
  "from": "reviewer",
  "to": "worker",
  "fromThreadId": "thread_reviewer_001",
  "toThreadId": "thread_worker_001",
  "state": "OBSERVED",
  "payload_hash": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
  "delivery_fingerprint": "sha256:3333333333333333333333333333333333333333333333333333333333333333"
}
```

Observe-only traffic must not emit `MESSAGE_ROUTED`, `REPLY_ROUTED`, or
`WORKER_RESUMED`. Snapshots and reports must distinguish `OBSERVED` traffic from
live routed traffic.

## CEA-032 Fuzzy Duplicate Advisory

Fuzzy duplicate advisory is optional audit metadata outside the delivery
decision path.

```json
{
  "suspected_near_duplicate": true,
  "similarity": 0.94,
  "compared_with": "msg_worker_003",
  "message_id": "msg_worker_004",
  "payload_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "compared_with_payload_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "candidate_count": 3,
  "threshold": 0.8,
  "action_taken": "NONE",
  "authority": "ADVISORY_ONLY"
}
```

Advisory output must not contain raw payload text and must not change Message
Bus state transitions. It must not route, reject, merge, repair ids, infer
authority, or change workspace permissions.

## CEA-033 Append-Only Persistent Ledger

CEA-033 adds a JSONL persistent implementation of the CEA-029
`MessageLedgerStore` contract.

Persistent ledger files use:

```text
<approved-ledger-root>/<ledger_id>.ledger.jsonl
```

Each line is a sanitized `MessageLedgerEntry` JSON object. Supported persisted
ledger `kind` values remain:

- `MESSAGE`
- `ROUTE`
- `REPLY`
- `REJECTION`
- `CONVERSATION`

The JSONL store preserves append order and can reconstruct the standard
`MessageLedgerSnapshot`, including conversation snapshots derived by
`buildConversationSnapshot()`.

Persistent records may include:

```json
{
  "entry_id": "sha256:4444444444444444444444444444444444444444444444444444444444444444",
  "kind": "MESSAGE",
  "at": "2026-07-08T00:00:00.000Z",
  "message_id": "msg_worker_001",
  "conversation_id": "conv_channel_001",
  "correlation_id": "corr_channel_001",
  "from": "worker",
  "to": "reviewer",
  "state": "CAPTURED",
  "payload_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "delivery_fingerprint": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
}
```

Persistent ledger records must not store raw payload text, secrets, private
state, raw logs, provider payloads, cookies, credentials, tokens, or environment
variables. Review surfaces should prefer ids, states, hashes, delivery
fingerprints, round counters, and rejection reasons.

Append failures must not be silently ignored. The current pilot reports a clear
`failed to append message ledger entry` error before accepting the record into
the store's in-memory view.

## CEA-035 Human Conversation Observer

CEA-035 adds a local-only read observer for selected Codex channel logs. It is
not a channel event source and does not mutate Message Bus state.

CLI:

```bash
npm run channel:observe -- --log data/message-logs/<job_id>.json --format html
```

The observer reads local message logs and, when available, the companion report
with the same `job_id`. It may display raw dialogue content to the local
Commander in the generated observer view, but that permission is limited to this
local observer surface.

Observer output metadata:

```json
{
  "result": "PASS",
  "task_id": "CEA-035",
  "observer_surface": "LOCAL_ONLY_COMMANDER_VIEW",
  "selected_job_id": "cea-026-multirole-20260708122934",
  "companion_report_found": true,
  "html_output": "data/observer/cea-026-multirole-20260708122934.html",
  "cards": 6,
  "boundary": {
    "raw_dialogue_content": "DISPLAY_ALLOWED_IN_OBSERVER_ONLY",
    "external_review_package_raw_payload": "DEFAULT_DENY",
    "message_bus_mutation": "NOT_USED",
    "live_routing_or_resume": "NOT_USED"
  }
}
```

The observer must not approve, route, reject, resume, merge, repair ids, infer
authority, interpret AGENTS.md, change workspace permissions, or unlock Phase 8.
External review packages remain hash/manifest oriented unless a later task
explicitly scopes raw transcript export.

## Codex-to-Codex Message Event Log

CEA-024 writes append-only message events to:

```text
data/message-logs/<job_id>.messages.jsonl
```

Each line is a complete JSON object:

```json
{
  "event": "MESSAGE_ROUTED",
  "job_id": "cea-023-codex-channel-20260708000000",
  "round": 1,
  "message_id": "msg_worker_001",
  "conversation_id": "conv_channel_001",
  "correlation_id": "corr_channel_001",
  "from": "worker",
  "to": "reviewer",
  "timestamp": "2026-07-08T00:00:00.000Z"
}
```

Frozen message event names:

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

CEA-028 freezes the current emitted channel event set. The channel event model
is communication-only: capture, route, reply, expire, reject, block an
over-round conversation, resume the originator, and mark channel completion. It
does not add thread lifecycle events or governance events.

Message events must not contain secrets, environment variables, tokens, cookies,
credentials, or raw private-state content.

## CEA-025 Multi-turn Dialogue Event Sequence

`npm run channel:multiturn` writes:

```text
data/message-logs/<job_id>.messages.jsonl
```

Required event sequence:

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

CEA-025 proves two-round Worker <-> Reviewer dialogue over the hardened CEA-024
bus. It does not prove multi-role dialogue, real repository readiness,
workspace write readiness, Workspace Agents API integration, Responses API
integration, or production readiness.

## CEA-026 Multi-role Codex Channel

`npm run channel:multirole` proves controlled synthetic routing across:

- Worker
- Reviewer
- Verifier

Required route sequence:

```text
Worker -> Reviewer -> Worker -> Verifier -> Worker -> DONE
```

Required append-only message event sequence:

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

Each route event records role and thread identity through `from`, `to`,
`fromThreadId`, and `toThreadId`.

Role registry rules:

- role is unique
- thread id is unique
- active role is required for routing
- inactive roles cannot receive messages
- missing registered roles are rejected by router lookup
- unsafe role label syntax is rejected

CEA-026 proves Worker / Reviewer / Verifier channel routing. It does not prove
production readiness, real repository readiness, workspace write readiness,
AGENTS OS integration, VCPToolBox integration, ChatGPT web integration,
Workspace Agents API integration, or Responses API integration.

## CEA-027 Channel Minimalism

The message bus is not a governance layer. It treats roles as registered
routing identities.

The channel owns:

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

The channel does not own:

- role duties
- role authority
- Commander authority
- workspace permissions
- real repository access
- write permissions
- commit / push / deploy / release policy
- secrets policy
- AGENTS.md content

Project-specific role duties and authority are delegated to AGENTS.md and
working context. Codex runtime executes work under AGENTS.md, current working
context, and active sandbox / approval settings. Bridge observes and routes.

## CEA-028 Channel Freeze And Closeout

The Codex-to-Codex Message Bus is a minimal communication channel. It only
transmits, routes, correlates, and records messages. It does not implement
governance, role authority, workspace policy, or AGENTS.md interpretation.

- CEA-023 proved single-turn communication.
- CEA-024 hardened delivery integrity.
- CEA-025 proved multi-turn communication.
- CEA-026 proved multi-role routing identities.
- CEA-027 froze channel minimalism and AGENTS.md delegation.
- CEA-028 freezes the communication channel as complete for the current line.

Governance events are not part of the channel event contract. Role approval,
Commander authorization, workspace-write approval, human-owner approval, deploy
approval, and similar policy decisions belong outside the communication channel.

Message Bus transmits information.
It does not interpret authority.

## MVP Turn Constraints

Smoke Worker and Reviewer turns must use:

- `cwd`: `data/synthetic-workspace`
- `sandboxPolicy`: `{ "type": "readOnly", "networkAccess": false }`
- intended readable root: synthetic workspace only
- no real repository path

The current generated schema does not provide a `readableRoots` field, so `cwd` must not be described as a true restricted readable-root boundary.

## State Transition Event

Transition events are written as JSONL records:

```json
{
  "jobId": "job-id",
  "type": "STATE_TRANSITION",
  "at": "2026-07-07T00:00:00.000Z",
  "state": "CREATED",
  "payload": {
    "from": "CREATED",
    "to": "APP_SERVER_STARTED",
    "reason": "string"
  }
}
```

## Receipt

Receipts are Markdown files under `data/receipts/<job_id>.receipt.md` and must summarize job id, final state, validation, artifacts, boundary flags, and known risks without secrets or raw private state.

## Context Ledger Event

CEA-012 context ledger records are JSONL metadata entries. They are not model
context injections and must not store raw prompts or raw model responses.

```json
{
  "ledgerVersion": 1,
  "taskId": "cea-012-context-ledger-20260707000000",
  "eventId": "cea-012-context-ledger-20260707000000:001-opened",
  "eventType": "MESSAGE_RECORDED",
  "at": "2026-07-07T00:00:00.000Z",
  "agentId": "worker",
  "role": "worker",
  "source": "app-server-jsonrpc",
  "frontendOrSession": "thread-id",
  "contentHash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "contentBytes": 42,
  "artifactRef": "data/reports/example.json",
  "snapshotId": "cea-011-safe-snapshot-20260707080426",
  "visibility": "record_only",
  "autoInject": false,
  "contextPatch": "disabled",
  "tags": ["record_only"]
}
```

Required boundary flags:

- `visibility`: `record_only`
- `autoInject`: `false`
- `contextPatch`: `disabled`
- raw content fields are rejected
- artifact references must point to approved evidence or snapshot surfaces

## Context Promotion Packet

CEA-013 promotion packets are metadata-only files derived from ledger queries.
They are blocked by default.

```json
{
  "packetVersion": 1,
  "packetId": "cea-013-context-packet-20260707000000",
  "sourceLedgerTaskId": "cea-012-context-ledger-20260707000000",
  "status": "BLOCKED_BY_DEFAULT",
  "workerPromptUse": "BLOCKED",
  "autoInject": false,
  "rawContentIncluded": false,
  "entryRefs": [],
  "artifactRefs": [],
  "snapshotIds": [],
  "boundary": {
    "approvalRequired": true,
    "defaultDecision": "BLOCKED_BY_DEFAULT",
    "autoInjection": "DISABLED",
    "directRealRepo": "BLOCKED",
    "workerCwd": "SNAPSHOT_ONLY"
  }
}
```

Only Commander or Reviewer approval can change `workerPromptUse` to
`APPROVED_PACKET_ONLY`. Approval does not enable automatic injection.

## Promotion Approval Receipt

CEA-014 approval receipts bind a Commander or Reviewer approval to a source
context packet hash. They are required before a packet can be compiled into a
prompt annex.

Required boundary flags:

- `statusBefore`: `BLOCKED_BY_DEFAULT`
- `statusAfter`: `APPROVED_FOR_PACKET_USE`
- `workerPromptUseAfter`: `APPROVED_PACKET_ONLY`
- `autoInjection`: `DISABLED`
- `contextPatch`: `DISABLED`
- `directRealRepo`: `BLOCKED`
- Worker approval is rejected

## Prompt Annex

CEA-015 prompt annex previews are metadata-only dry-run artifacts. They require
a valid CEA-014 approval receipt bound to the source CEA-013 packet hash.

Required boundary flags:

- `mode`: `DRY_RUN`
- `workerPromptUse`: `APPROVED_PACKET_ONLY`
- `autoInject`: `false`
- `rawContentIncluded`: `false`
- `managedSessionStarted`: `false`
- `directRealRepo`: `BLOCKED`

## Snapshot-Bound Worker Plan

CEA-016 Worker plans are prep-only artifacts. They validate the CEA-011 snapshot
manifest and CEA-015 prompt annex before a future managed Worker session can be
started.

Required boundary flags:

- `mode`: `PREP_ONLY`
- `sandboxPolicy`: `{ "type": "readOnly", "networkAccess": false }`
- `workerCwdPolicy`: `SNAPSHOT_ONLY`
- `managedWorkerStarted`: `false`
- `managedReviewerStarted`: `false`
- `directRealRepo`: `BLOCKED`

## Live Snapshot Worker Run

CEA-016 live Worker run starts one managed Worker thread from the prep plan.
The App Server process cwd, Worker thread cwd, and Worker turn cwd must all be
the generated snapshot root.

Required live boundary flags:

- `app_server_process_cwd_snapshot`: `YES`
- `worker_thread_cwd_snapshot`: `YES`
- `worker_turn_cwd_snapshot`: `YES`
- `sandbox_read_only_network_off`: `YES`
- `managed_worker_started`: `STARTED`
- `managed_reviewer_started`: `NOT_STARTED`
- `direct_real_repo`: `BLOCKED`

## Live Snapshot Reviewer Run

CEA-017 live Reviewer run starts one managed Reviewer thread from the same
snapshot-bound prep plan and reviews CEA-016 Worker DONE evidence.

Required live boundary flags:

- `app_server_process_cwd_snapshot`: `YES`
- `reviewer_thread_cwd_snapshot`: `YES`
- `reviewer_turn_cwd_snapshot`: `YES`
- `sandbox_read_only_network_off`: `YES`
- `managed_worker_evidence_used`: `YES`
- `managed_reviewer_started`: `STARTED`
- `direct_real_repo`: `BLOCKED`

## End-to-End Safe Review Loop

CEA-018 report records the full chain:

- snapshot manifest and exclusions
- context ledger
- promotion packet
- approval receipt
- prompt annex
- Worker `DONE`
- Reviewer `REVIEWER_DECISION`
- boundary summary

Required final boundary flags:

- `bridge_exporter_read_source`: `YES`
- `app_server_process_cwd_snapshot`: `YES`
- `worker_thread_cwd_snapshot`: `YES`
- `reviewer_thread_cwd_snapshot`: `YES`
- `managed_worker_started`: `STARTED`
- `managed_reviewer_started`: `STARTED`
- `direct_real_repo`: `BLOCKED`

## Codex-to-Codex Channel Smoke

CEA-023 is not a snapshot flow. It starts synthetic Worker and Reviewer threads
and validates a routed message exchange. CEA-024 hardens that route without
changing the synthetic-workspace boundary. CEA-025 then validates a two-round
dialogue, and CEA-026 validates a three-role route on the same boundary:

- Worker emits `MESSAGE_TO_CODEX`
- Bridge captures and routes it to Reviewer
- Reviewer emits `CODEX_MESSAGE_REPLY`
- Bridge correlates `reply_to`, `conversation_id`, and `correlation_id`
- Bridge returns the reply to Worker
- Worker resumes and emits `DONE`
- strict runtime payload validation is active
- timeout and max-round guards are configured
- append-only message event logging is active
- round 1 and round 2 preserve one `conversation_id`
- each round uses distinct `message_id`, `reply_to`, and `correlation_id`
- Worker emits `DONE` after the second reply
- Verifier has a distinct active thread
- Worker -> Verifier and Verifier -> Worker preserve role and thread identity

Required boundary flags:

- `snapshot_required`: `FALSE`
- `app_server_process_cwd`: `SYNTHETIC_WORKSPACE`
- `worker_thread_cwd`: `SYNTHETIC_WORKSPACE`
- `reviewer_thread_cwd`: `SYNTHETIC_WORKSPACE`
- `verifier_thread_cwd`: `SYNTHETIC_WORKSPACE`
- `workspace_agents_api`: `NOT_USED`
- `responses_api`: `NOT_USED`
- `websocket`: `NOT_USED`
- `thread_shell_command`: `NOT_USED`
- `command_exec`: `NOT_USED`
- `real_repo_direct_cwd`: `NOT_USED`
