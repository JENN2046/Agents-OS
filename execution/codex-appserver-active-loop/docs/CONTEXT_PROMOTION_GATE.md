# Context Promotion Gate

CEA-013 adds a promotion gate between the record-only context ledger and any
future Worker or Reviewer prompt use.

The gate turns ledger metadata into a context packet. A packet is blocked by
default and cannot be used in a Worker prompt until a Commander or Reviewer
approval is recorded. Approval does not enable automatic injection; it only marks
the packet as eligible for explicit packet-only use.

## Flow

```text
record-only ledger entries
  -> metadata query
  -> context promotion packet
  -> BLOCKED_BY_DEFAULT
  -> commander/reviewer approval
  -> APPROVED_PACKET_ONLY
```

No step reads or stores raw prompt text, raw model response text, private state,
or real repository contents.

## Query

Promotion queries can match ledger metadata by:

- `taskId`
- `snapshotId`
- `role`
- `tag`
- `artifactRef`
- `contentHash`
- `eventType`

Queries return ledger metadata records only. The original message content is not
recoverable from the ledger.

## Packet Boundary

Context packets contain:

- packet id and source ledger task id
- query metadata
- entry refs
- artifact refs
- snapshot ids
- content hashes and byte counts
- boundary flags
- optional approval record

Context packets must not contain fields named `content`, `raw`, `rawContent`,
`message`, `messages`, `prompt`, `response`, or `text`.

Default packet state:

```json
{
  "status": "BLOCKED_BY_DEFAULT",
  "workerPromptUse": "BLOCKED",
  "autoInject": false,
  "rawContentIncluded": false
}
```

Approved packet state:

```json
{
  "status": "APPROVED_FOR_PACKET_USE",
  "workerPromptUse": "APPROVED_PACKET_ONLY",
  "autoInject": false,
  "rawContentIncluded": false
}
```

Only `commander` and `reviewer` roles can approve promotion. Worker self-promotion
is rejected.

CEA-014 persists this approval as a separate receipt bound to the source packet
hash. The original blocked packet is not overwritten.

## Storage

Pilot packets are written under:

```text
data/context-packets/<packet_id>.context-packet.json
```

## Pilot Command

```bash
npm run context:promote
```

The pilot reads the CEA-012 ledger, builds a blocked-by-default packet, writes it
to `data/context-packets/`, and reports that no approval or managed session was
started.

## Non-Goals

- No automatic memory injection.
- No raw content recovery.
- No direct real repository access.
- No managed Worker/Reviewer turn start.
- No weakening of the CEA-011 safe snapshot boundary.
