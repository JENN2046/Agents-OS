# Promotion Approval Receipt

CEA-014 makes context promotion approval auditable.

A context packet can move from `BLOCKED_BY_DEFAULT` toward explicit
packet-only use only when a Commander or Reviewer approval receipt is written.
The original blocked packet is not overwritten. The receipt binds to the packet
by `packetId` and a SHA-256 hash of the source packet.

## Boundary

- Only `commander` and `reviewer` may approve.
- Worker self-approval is rejected.
- Approval changes intended use to `APPROVED_PACKET_ONLY`.
- Approval does not enable automatic context injection.
- Approval does not enable context patching.
- Approval does not permit direct real repository access.
- Approval receipts are metadata-only and must not contain raw prompts, raw
  responses, private state, secrets, or repository content.

## Receipt Shape

```json
{
  "receiptVersion": 1,
  "receiptId": "cea-014-promotion-approval-20260707000000",
  "packetId": "cea-013-context-packet-20260707000000",
  "sourcePacketHash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "statusBefore": "BLOCKED_BY_DEFAULT",
  "statusAfter": "APPROVED_FOR_PACKET_USE",
  "workerPromptUseAfter": "APPROVED_PACKET_ONLY",
  "approvedByRole": "reviewer",
  "approvedByAgentId": "reviewer-id",
  "reason": "metadata-only packet is scoped",
  "evidence": ["docs/CONTEXT_PROMOTION_GATE.md"],
  "approvalHash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "boundary": {
    "approvalReceiptRequired": true,
    "autoInjection": "DISABLED",
    "rawContentIncluded": false,
    "contextPatch": "DISABLED",
    "directRealRepo": "BLOCKED",
    "workerCwd": "SNAPSHOT_ONLY"
  }
}
```

## Storage

Approval receipts are written under:

```text
data/context-approvals/<receipt_id>.approval.json
```

## Pilot Command

```bash
npm run context:approve
```

The pilot reads the CEA-013 blocked packet and writes a Reviewer approval receipt
for packet-only use. It does not start managed Worker or Reviewer sessions.

## Prompt Annex Use

CEA-015 consumes the approval receipt to build a dry-run prompt annex. The
compiler must verify the receipt against the source packet hash before writing
any annex.
