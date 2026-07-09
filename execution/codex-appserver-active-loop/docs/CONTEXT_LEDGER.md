# Codex Context Ledger

CEA-012 adds a record-only context ledger for Codex coordination metadata.

The ledger is not a memory injector. It records enough metadata to audit and
deduplicate Commander, Bridge, Worker, and Reviewer coordination without
persisting raw prompts, raw model responses, private state, or repository
contents.

## Boundary

- Ledger entries are `record_only`.
- `autoInject` is always `false`.
- `contextPatch` is always `disabled`.
- Raw message content is hashed and discarded before persistence.
- Durable records may contain artifact references, snapshot IDs, timestamps,
  roles, sources, sessions, tags, and byte counts.
- Managed Worker and Reviewer sessions must not read the real repository through
  the ledger.
- Phase 8 direct real repository review remains `BLOCKED` while App Server schema
  lacks restricted readable roots.

## Entry Shape

```json
{
  "ledgerVersion": 1,
  "taskId": "cea-012-context-ledger-20260707000000",
  "eventId": "cea-012-context-ledger-20260707000000:001-opened",
  "eventType": "TASK_OPENED",
  "at": "2026-07-07T00:00:00.000Z",
  "agentId": "commander",
  "role": "commander",
  "source": "codex-desktop",
  "frontendOrSession": "current-thread",
  "contentHash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "contentBytes": 62,
  "artifactRef": "docs/CONTEXT_LEDGER.md",
  "snapshotId": "cea-011-safe-snapshot-20260707080426",
  "visibility": "record_only",
  "autoInject": false,
  "contextPatch": "disabled",
  "tags": ["cea-012", "record_only"]
}
```

Allowed event types:

- `TASK_OPENED`
- `MESSAGE_RECORDED`
- `SNAPSHOT_BOUND`
- `REVIEW_REQUESTED`
- `FINDING_RECORDED`
- `RECEIPT_BOUND`
- `TASK_CLOSED`
- `BLOCKED`

Allowed roles:

- `commander`
- `bridge`
- `worker`
- `reviewer`
- `user`
- `system`

## Storage

The pilot store writes JSONL files under:

```text
data/context-ledger/<task_id>.context.jsonl
```

Each line must pass strict validation before append and after read. Unknown
fields are rejected, including raw-content fields such as `content`, `message`,
`prompt`, `response`, and `text`.

## Deduplication

Duplicate detection is metadata based:

- same `agentId`
- same `role`
- same `source`
- same `frontendOrSession`
- same `contentHash`

This supports retry/edit detection without storing the original text.

## Pilot Command

```bash
npm run context:pilot
```

The pilot writes a five-entry record-only ledger and reports the generated
ledger path, entry count, snapshot reference, and disabled injection boundary.

## Promotion

CEA-013 adds a separate promotion gate. Ledger records do not become Worker or
Reviewer context by themselves. A promotion packet must be created, remain
blocked by default, and receive Commander or Reviewer approval before explicit
packet-only use is allowed.

See `docs/CONTEXT_PROMOTION_GATE.md`.
