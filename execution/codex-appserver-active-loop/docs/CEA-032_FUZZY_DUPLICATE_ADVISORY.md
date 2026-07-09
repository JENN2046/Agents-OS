# CEA-032: Fuzzy Duplicate Advisory

Status: DONE

Created: 2026-07-08T19:43:16+08:00

Completed: 2026-07-08T12:10:29.9332369Z

Depends on: CEA-031 DONE

Taskbook: `data/jobs/cea-032-fuzzy-duplicate-advisory.taskbook.json`

Source plan: `docs/MESSAGE_BUS_DELIVERY_LEDGER_PLAN.md`

## Mission

Add fuzzy duplicate advisory as an audit hint only. The advisory may help a
Commander notice near-duplicate task content, but it must never decide routing,
rejection, merging, authority, or workspace access.

## Scope

- add a side-channel advisory interface for near-duplicate detection
- compare sanitized/hash-aware message summaries where possible
- emit advisory metadata with `action_taken: "NONE"`
- add tests proving advisory cannot change delivery decisions
- document that fuzzy advisory is outside the delivery decision path

## Non-Goals

- do not route messages based on fuzzy similarity
- do not reject messages based on fuzzy similarity
- do not merge conversations based on fuzzy similarity
- do not repair `message_id`, `reply_to`, `conversation_id`, or
  `correlation_id`
- do not grant authority or change workspace permissions
- do not expose raw payloads broadly by default
- do not add persistent storage unless a later task scopes it

## Advisory Shape

Example:

```json
{
  "suspected_near_duplicate": true,
  "similarity": 0.94,
  "compared_with": "msg_worker_003",
  "action_taken": "NONE"
}
```

## Required Behavior

- advisory output is optional metadata
- advisory output is non-authoritative
- exact delivery checks from CEA-029 and CEA-030 remain the only gate for
  routing and rejection
- `action_taken` must remain `NONE` unless a future task explicitly creates a
  human-review workflow outside the Message Bus delivery path

## Acceptance

- near-duplicate content can produce an advisory hint
- advisory hints do not alter Message Bus state transitions
- advisory hints do not reject or route messages
- advisory hints do not merge conversations
- advisory tests include a high-similarity pair that still routes or rejects
  only according to exact delivery rules
- docs state that fuzzy advisory is a helper, not a traffic controller

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

- `data/reports/cea-032_fuzzy_duplicate_advisory.json`
- `data/receipts/2026-07-08-cea-032-fuzzy-duplicate-advisory.receipt.md`

Do not create completion evidence before implementation and validation pass.
