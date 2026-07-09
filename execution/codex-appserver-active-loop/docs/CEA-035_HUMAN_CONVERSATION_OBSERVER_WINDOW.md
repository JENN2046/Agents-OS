# CEA-035: Human Conversation Observer Window

Status: DONE

Created: 2026-07-08T20:02:12+08:00

Completed: 2026-07-08T12:30:46.7803548Z

Depends on: CEA-031 DONE

Recommended after: CEA-033

Taskbook: `data/jobs/cea-035-human-conversation-observer-window.taskbook.json`

Source plan: `docs/MESSAGE_BUS_DELIVERY_LEDGER_PLAN.md`

## Mission

Add a local human observer window that lets the Commander inspect how Codex
agents talk to each other. The window should show conversation content, route
identity, delivery state, and timestamps in a readable dialogue view.

## Scope

- add a local-only human observer surface for agent conversation logs
- show readable message and reply content when explicitly opened by the local
  Commander
- show route metadata such as `conversation_id`, `message_id`, `reply_to`,
  `correlation_id`, `from`, `to`, `fromThreadId`, `toThreadId`, state, round,
  and timestamp
- support filtering by conversation, role, state, and job/log file
- make raw dialogue content visible in the observer window without making raw
  payload exposure the default for external review packages
- clearly distinguish normal routed traffic, observe-only traffic, rejected
  traffic, expired traffic, and blocked traffic

## Non-Goals

- do not make Message Bus a governance layer
- do not let the observer approve, route, reject, or mutate messages
- do not infer authority from dialogue content
- do not expose secrets or private-state contents
- do not include raw dialogue content in external review packages by default
- do not unlock Phase 8 direct real-repository managed runs
- do not perform commit, push, deploy, release, or tag actions

## Display Requirements

The visual direction should follow a timeline-card layout like the Commander
reference screenshot:

- final selected direction: calm timeline-card UI, similar to the rendered
  Direction C concept
- background: dynamic black starfield, subtle and low contrast
- starfield animation must stay behind the content layer and must not reduce
  transcript readability
- timeline cards should sit on dark translucent surfaces with enough contrast
  for long reading sessions
- the left pane groups logs by project folder
- clicking a project folder reveals that project's thread queue
- selecting a thread opens its conversation timeline
- the center pane uses a vertical timeline with compact event cards
- each card shows role icon, time, state/category label, title, and dialogue
  excerpt
- role/state accent colors may be used for scanability, but the view must stay
  an engineering operations tool rather than a decorative landing page
- animation should be lightweight, local, and optional to disable if needed
- the layout should support dense review of many threads without hiding route
  metadata

The observer should show a conversation as a readable transcript:

```text
[2026-07-08T12:00:00.000Z] worker -> reviewer
conversation: conv_001
message: msg_worker_001
state: ROUTED

Question:
Please review this decision point.

Context:
- ...

Expected response:
decision
```

Replies should show their relationship to the original message:

```text
[2026-07-08T12:00:01.000Z] reviewer -> worker
reply_to: msg_worker_001
state: REPLIED

Decision:
continue

Reason:
...

Next instruction:
...
```

## Raw Content Boundary

This task intentionally allows a local human Commander to see dialogue content.
That permission is limited to the observer surface.

Rules:

- raw payload text may be displayed to the local Commander in the observer
  window
- raw payload text must not be copied into broad external review packages by
  default
- raw payload text must not be used to grant authority or workspace permission
- observer output should prefer local files and local UI/CLI surfaces
- secret-like or private-state source paths must remain excluded unless a future
  exact authorization changes that boundary

## Suggested Implementation Options

Acceptable first implementations:

- CLI transcript viewer for existing `data/message-logs/*.json` files
- static local HTML transcript generated from a selected message log
- small local read-only viewer command that renders the conversation transcript

Preferred first cut:

```text
CLI transcript viewer + static HTML timeline output
```

Avoid overbuilding a server or browser automation flow unless a later task
explicitly scopes it.

## Acceptance

- Commander can select an existing message log and view agent dialogue content
- transcript shows message and reply payload content in human-readable form
- transcript shows route metadata and delivery state
- left navigation groups conversations by project folder and opens a thread
  queue on click
- center transcript uses timeline-style cards for agent dialogue events
- transcript distinguishes routed, observed, rejected, expired, failed, blocked,
  and done states when present
- transcript can filter by `conversation_id`
- transcript does not mutate Message Bus state
- transcript does not perform live routing or resume
- transcript does not add governance or AGENTS.md interpretation
- external review package defaults remain hash/manifest oriented unless a later
  task explicitly scopes raw transcript export

## Validation

Required:

```bash
npm run build
npm run test:unit
```

Recommended if the observer reads current channel logs:

```bash
npm run channel:smoke
npm run channel:multiturn
npm run channel:multirole
```

## Evidence To Produce

On completion, produce a report and receipt only after implementation and
validation actually happen:

- `data/reports/cea-035_human_conversation_observer_window.json`
- `data/receipts/2026-07-08-cea-035-human-conversation-observer-window.receipt.md`

Do not create completion evidence before implementation and validation pass.

## Completion Summary

CEA-035 implemented a local-only Commander observer surface for Codex channel
conversation logs.

Implemented:

- `createConversationObserverModel()`
- `renderObserverTranscript()`
- `renderObserverHtml()`
- `npm run channel:observe`
- static HTML output under `data/observer/<job_id>.html`
- automatic latest-log selection
- optional `--log`, `--conversation`, `--role`, `--state`, `--format`, and
  `--out` options
- companion report lookup by `job_id` for local raw dialogue display
- timeline cards with route metadata and state labels
- local secret-like payload key redaction
- tests for dialogue rendering, route metadata, filtering, state
  distinctions, and boundary flags

Boundaries kept:

- observer surface: LOCAL_ONLY_COMMANDER_VIEW
- raw dialogue content: DISPLAY_ALLOWED_IN_OBSERVER_ONLY
- external review package raw payload: DEFAULT_DENY
- Message Bus mutation: NOT_USED
- live routing or resume: NOT_USED
- governance and AGENTS.md interpretation: OUT_OF_SCOPE
- Phase 8 direct real repository: BLOCKED

## Completion Evidence

- `data/observer/cea-026-multirole-20260708122934.html`
- `data/reports/cea-035_human_conversation_observer_window.json`
- `data/receipts/2026-07-08-cea-035-human-conversation-observer-window.receipt.md`

## Validation Result

- `npm run build`: PASS
- `npm run test:unit`: PASS, 27 files / 138 tests
- `npm run channel:observe`: PASS, generated
  `data/observer/cea-026-multirole-20260708122934.html`
- `npm run channel:smoke`: PASS, `cea-023-codex-channel-20260708122847`
- `npm run channel:multiturn`: PASS, `cea-025-multiturn-20260708122906`
- `npm run channel:multirole`: PASS, `cea-026-multirole-20260708122934`
- `npm run validate`: PASS, includes `cea-007-real-smoke-20260708123018`
