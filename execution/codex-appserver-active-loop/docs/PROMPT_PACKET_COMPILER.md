# Prompt Packet Compiler Dry Run

CEA-015 compiles an approved context packet into a Worker prompt annex preview.

The compiler is a dry run. It verifies the CEA-014 approval receipt against the
CEA-013 source packet hash, then writes a metadata-only annex containing artifact
references, snapshot references, entry summaries, and boundary constraints.

## Boundary

- The compiler does not read artifact file contents.
- The compiler does not recover ledger raw content.
- The compiler does not start a managed Worker or Reviewer session.
- The compiler does not enable automatic injection.
- Direct real repository `cwd` remains blocked.
- Future Worker use must remain snapshot-bound.

## Annex Shape

```json
{
  "annexVersion": 1,
  "annexId": "cea-015-prompt-annex-20260707000000",
  "sourcePacketId": "cea-013-context-packet-20260707000000",
  "approvalReceiptId": "cea-014-promotion-approval-20260707000000",
  "mode": "DRY_RUN",
  "intendedAudience": "worker",
  "workerPromptUse": "APPROVED_PACKET_ONLY",
  "autoInject": false,
  "rawContentIncluded": false,
  "artifactRefs": [],
  "snapshotIds": [],
  "entrySummaries": [],
  "constraints": [],
  "boundary": {
    "approvalVerified": true,
    "sourcePacketHashVerified": true,
    "autoInjection": "DISABLED",
    "directRealRepo": "BLOCKED",
    "workerCwd": "SNAPSHOT_ONLY",
    "managedSessionStarted": false
  }
}
```

## Storage

Prompt annex previews are written under:

```text
data/prompt-annexes/<annex_id>.prompt-annex.json
```

## Pilot Command

```bash
npm run context:annex
```

The pilot reads the CEA-013 context packet and CEA-014 approval receipt, verifies
their hash binding, and writes a dry-run annex. It does not launch Codex managed
sessions.

## Worker Prep Use

CEA-016 consumes the annex to build a snapshot-bound Worker plan. The plan must
verify that the annex snapshot ID matches the CEA-011 snapshot manifest before
any future Worker run can be attempted.
