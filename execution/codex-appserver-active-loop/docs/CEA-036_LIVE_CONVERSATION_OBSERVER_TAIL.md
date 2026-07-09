# CEA-036: Live Conversation Observer Tail

Status: DONE

Created: 2026-07-08T20:47:54+08:00

Completed: 2026-07-08T21:04:58.1278087+08:00

Depends on: CEA-035 DONE

Post-closeout follow-up after: CEA-034 DONE

Taskbook: `data/jobs/cea-036-live-conversation-observer-tail.taskbook.json`

Source observer task: `docs/CEA-035_HUMAN_CONVERSATION_OBSERVER_WINDOW.md`

## Mission

Upgrade the local Commander observer from static replay to a live read-only tail
view so the Commander can watch Codex agent conversation events appear as the
message log grows.

## Scope

- add a `--watch` or equivalent live-tail mode to `npm run channel:observe`
- monitor the selected or latest `data/message-logs/*.jsonl` / `.json` source
  without mutating it
- append newly observed message, reply, route, rejection, expiration, blocked,
  observed, and done events to the transcript view
- expose a visible live/paused/stale status in the observer
- keep project folder navigation, thread queue navigation, conversation filters,
  role filters, state filters, and raw-content toggle
- preserve the CEA-035 visual direction: calm timeline-card UI with dynamic
  black starfield background
- ensure the live observer stays local-only and read-only

## Non-Goals

- do not add message approval, routing, rejection, resume, or mutation controls
- do not make Message Bus a governance layer
- do not infer authority from live dialogue content
- do not include raw dialogue content in external review packages by default
- do not expose secrets or private-state contents
- do not unlock Phase 8 direct real-repository managed runs
- do not introduce remote hosting, public network exposure, or production
  deployment
- do not perform commit, push, deploy, release, or tag actions

## Live Behavior

Preferred command shape:

```bash
npm run channel:observe -- --watch
```

Useful options:

```bash
npm run channel:observe -- --watch --log data/message-logs/<job>.json
npm run channel:observe -- --watch --conversation <conversation_id>
npm run channel:observe -- --watch --role worker
npm run channel:observe -- --watch --state ROUTED
```

The first implementation may use one of these safe local approaches:

- regenerate static HTML on file change and auto-refresh the page
- write a local JSON snapshot that the HTML page polls
- use a local-only read-only server with Server-Sent Events if the implementation
  remains simple and scoped

Avoid WebSocket control channels, remote access, or any route/resume mutation
surface.

## Display Requirements

- show live status: `LIVE`, `PAUSED`, `STALE`, or `ERROR`
- append new timeline cards without losing current filters
- preserve scroll position unless auto-scroll is enabled
- make new cards visually noticeable without noisy animation
- show when a watched log is rotated, missing, or replaced
- show raw dialogue content only inside the local observer surface
- keep metadata and route identity inspectable for newly appended events

## Safety Boundary

The live observer is still only a view.

It may:

- read selected local message logs
- render local CLI/HTML output
- display raw dialogue content to the local Commander
- show route metadata and delivery state

It must not:

- mutate Message Bus state
- send messages
- approve messages
- resume agents
- route replies
- write external review packages with raw payload content by default
- access secret/private-state contents

## Acceptance

- `npm run channel:observe -- --watch` starts a local live-tail observer mode
- new message log entries appear in the observer without manually rerunning the
  command
- live mode preserves project folder navigation and thread queue selection
- live mode preserves conversation, role, and state filters
- live mode distinguishes routed, observed, rejected, expired, failed, blocked,
  and done states when present
- live mode remains read-only and does not route, resume, approve, or mutate
  messages
- raw dialogue content remains limited to the local observer surface
- static observer behavior from CEA-035 remains green

## Validation

Required:

```bash
npm run build
npm run test:unit
npm run channel:observe
```

Recommended:

```bash
npm run channel:smoke
npm run channel:multiturn
npm run channel:multirole
npm run validate
```

## Evidence To Produce

On completion, produce a report and receipt only after implementation and
validation actually happen:

- `data/reports/cea-036_live_conversation_observer_tail.json`
- `data/receipts/2026-07-08-cea-036-live-conversation-observer-tail.receipt.md`

Do not create completion evidence before implementation and validation pass.

## Completion Summary

CEA-036 upgraded the local Commander observer with a live-tail mode while
preserving the static CEA-035 observer.

Implemented:

- `npm run channel:observe -- --watch`
- `--watch --once` for deterministic validation without leaving a tail process
  running
- read-only polling of selected or latest `.json` / `.messages.jsonl` message
  logs
- local `.live.html` output with auto-refresh metadata
- local `.live.json` snapshot output for the current observer model
- visible live status: `LIVE`, `PAUSED`, `STALE`, or `ERROR`
- watched path, snapshot path, source size, missing-source, and replaced-source
  metadata
- raw-content toggle with local-only raw dialogue display
- auto-scroll toggle while preserving scroll position by default
- state counts for routed, observed, rejected, expired, failed, blocked, and
  done states when present
- preservation of project folder navigation, thread queue navigation,
  conversation filters, role filters, state filters, and the CEA-035 static
  observer path

Boundaries kept:

- observer mode: LOCAL_ONLY_READ_ONLY_LIVE_TAIL
- Message Bus mutation: NOT_USED
- route decision, approval, and resume controls: NOT_USED
- governance and `AGENTS.md` interpretation: OUT_OF_SCOPE
- raw dialogue copied into broad evidence package: false
- Phase 8 direct real repository: BLOCKED

## Completion Evidence

- `data/observer/cea-026-multirole-20260708125856.live.html`
- `data/observer/cea-026-multirole-20260708125856.live.json`
- `data/message-logs/cea-036-live-tail-validation-20260708210437.messages.jsonl`
- `data/observer/cea-036-live-tail-validation-20260708210437.live.html`
- `data/observer/cea-036-live-tail-validation-20260708210437.live.json`
- `data/reports/cea-036_live_conversation_observer_tail.json`
- `data/receipts/2026-07-08-cea-036-live-conversation-observer-tail.receipt.md`

## Validation Result

- `npm run build`: PASS
- `npm run test:unit`: PASS, 27 files / 139 tests
- `npm run channel:observe`: PASS, static CEA-035 replay preserved
- `npm run channel:observe -- --watch --once --log data/message-logs/cea-026-multirole-20260708125856.messages.jsonl --poll_ms 500 --stale_ms 999999999`: PASS, generated live HTML and live JSON
- live-tail growth validation: PASS, one watch process observed synthetic log
  growth from 1 card to 2 cards without manual rerun
- `npm run channel:smoke`: PASS, `cea-023-codex-channel-20260708125801`
- `npm run channel:multiturn`: PASS, `cea-025-multiturn-20260708125821`
- `npm run channel:multirole`: PASS, `cea-026-multirole-20260708125856`
- `npm run validate`: PASS, includes `cea-007-real-smoke-20260708125927`
