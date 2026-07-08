# End-to-End Safe Review Loop

CEA-018 runs the safe review chain as one command:

```text
snapshot export
  -> context ledger
  -> promotion packet
  -> approval receipt
  -> prompt annex
  -> snapshot-bound Worker
  -> snapshot-bound Reviewer
  -> receipt
```

## Command

```bash
npm run safe-review:e2e
```

The command creates a fresh CEA-018 snapshot and then runs Worker and Reviewer in
one App Server process whose process cwd is the snapshot root.

Use the offline CEA-019 verifier after a successful live run:

```bash
npm run safe-review:verify
```

## Boundary

- The real repository is read only by the Bridge snapshot exporter.
- App Server process cwd is the snapshot root.
- Worker thread cwd and turn cwd are the snapshot root.
- Reviewer thread cwd and turn cwd are the snapshot root.
- Sandbox policy is read-only with network disabled.
- Context auto-injection remains disabled.
- Direct real repository managed-session cwd remains blocked.
- No command execution, file writes, secret reads, push, deploy, release, or tag.

## Outputs

The E2E loop writes:

- `data/snapshots/cea-018-safe-snapshot-<timestamp>/`
- `data/context-ledger/cea-018-context-ledger-<timestamp>.context.jsonl`
- `data/context-packets/cea-018-context-packet-<timestamp>.context-packet.json`
- `data/context-approvals/cea-018-promotion-approval-<timestamp>.approval.json`
- `data/prompt-annexes/cea-018-prompt-annex-<timestamp>.prompt-annex.json`
- `data/worker-pilots/cea-018-snapshot-worker-plan-<timestamp>.worker-plan.json`
- `data/events/cea-018-e2e-safe-review-<timestamp>.events.jsonl`
- `data/reports/cea-018_e2e_safe_review_loop.json`
- `data/receipts/2026-07-07-cea-018-e2e-safe-review-loop.receipt.md`

## Success Criteria

- Worker returns structured `DONE`.
- Reviewer returns structured `REVIEWER_DECISION`.
- Reviewer decision is `continue`.
- Policy decision count is zero.
- All managed session cwd values equal the snapshot root.
- Phase 8 direct real repository access remains `BLOCKED`.
