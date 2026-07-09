# CEA-031: Record-Only / Observe-Only Mode

Status: DONE

Created: 2026-07-08T19:43:16+08:00

Completed: 2026-07-08T12:05:29.8069742Z

Depends on: CEA-030 DONE

Taskbook: `data/jobs/cea-031-record-only-observe-only-mode.taskbook.json`

Source plan: `docs/MESSAGE_BUS_DELIVERY_LEDGER_PLAN.md`

## Mission

Add a safe observe-only Message Bus mode for practical trials where traffic is
validated, recorded, and audited without claiming that live downstream routing or
resume happened.

## Scope

- add a distinct observe-only or record-only mode
- validate accepted envelopes through the same delivery-integrity checks
- write ledger and snapshot evidence for observed traffic
- use a distinct status such as `OBSERVED` or `DRY_ROUTE_RECORDED`
- ensure observe-only mode never reports live route/resume as completed
- add tests that prove observe-only mode records without live route overclaim

## Non-Goals

- do not add fuzzy duplicate advisory
- do not add persistent storage
- do not perform real managed Worker/Reviewer execution
- do not unlock Phase 8 direct real-repository managed runs
- do not add governance or AGENTS.md interpretation to Message Bus
- do not use `ROUTED` for traffic that was only observed

## Mode Behavior

```text
normal:
  capture, validate, route, reply, resume

observe_only:
  capture, validate, ledger, audit
  do not resume or perform live downstream routing
```

## Required Behavior

- observe-only mode records accepted envelopes
- observe-only mode still rejects malformed, duplicate, or cross-wired traffic
- observe-only mode preserves `payload_hash` and `delivery_fingerprint`
- observe-only mode is visible in ledger and snapshot output
- reports and snapshots clearly label observed traffic

## Acceptance

- observed messages do not claim live routing
- observed replies do not claim live resume
- malformed or duplicate observed traffic is rejected
- single-flight ordering remains enforced unless explicitly changed by a future
  task
- snapshot and ledger views can separate observed traffic from real routed
  traffic
- existing normal channel flows remain green

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

- `data/reports/cea-031_record_only_observe_only_mode.json`
- `data/receipts/2026-07-08-cea-031-record-only-observe-only-mode.receipt.md`

Do not create completion evidence before implementation and validation pass.
