# Snapshot Review Package Publisher

CEA-021 publishes a compact closure package for Commander or external review.

## Command

```bash
npm run review-package:publish
```

## Included Content

The package is intentionally narrow. The zip contains only:

- a package `MANIFEST.json`
- CEA-018 snapshot manifest
- CEA-018 snapshot exclusion report
- CEA-018 report and receipt
- CEA-019 report and receipt
- CEA-020 report and receipt

## Excluded Content

The publisher must not include:

- event logs
- context ledger rows
- context packets
- approval receipt internals beyond the CEA report references
- prompt annexes
- Worker plans
- snapshot source files
- `node_modules`, `dist`, `.git`, `.env`, `state-private`, secrets, tokens, or cookies

## Outputs

- `data/review-packages/snapshot-review-closure-<timestamp>/`
- `data/review-packages/snapshot-review-closure-<timestamp>/codex-appserver-active-loop-snapshot-review-closure-<timestamp>.zip`
- `data/reports/cea-021_snapshot_review_package_publisher.json`
- `data/receipts/<date>-cea-021-snapshot-review-package-publisher.receipt.md`

The publisher is offline. It does not start App Server, managed Worker,
managed Reviewer, Phase 8 real-repository sessions, or App Server command APIs.
