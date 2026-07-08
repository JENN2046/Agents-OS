# CEA-033: Append-Only Persistent Ledger Pilot

Status: DONE

Created: 2026-07-08T19:43:16+08:00

Completed: 2026-07-08T12:20:20.7787547Z

Depends on: CEA-031 DONE

Recommended after: CEA-032

Taskbook: `data/jobs/cea-033-append-only-persistent-ledger-pilot.taskbook.json`

Source plan: `docs/MESSAGE_BUS_DELIVERY_LEDGER_PLAN.md`

## Mission

Pilot durable append-only Message Bus ledger storage after the in-memory ledger,
snapshot, and observe-only surfaces are stable.

## Scope

- add a JSONL append-only ledger store pilot
- preserve event order
- exclude secrets and private state
- persist hash/fingerprint summaries instead of raw payload expansion by
  default
- make persisted records reconstruct conversation summaries
- keep SQLite evaluation as a future option, not the first implementation

## Non-Goals

- do not introduce SQLite unless this task is explicitly revised
- do not store secrets, private state, raw logs, or raw provider payloads
- do not broaden review packages to include raw message payloads by default
- do not change Message Bus governance boundaries
- do not unlock Phase 8 direct real-repository managed runs
- do not perform commit, push, deploy, release, or tag actions

## Preferred Order

1. JSONL append-only ledger
2. SQLite indexed ledger only if query volume and durability needs justify it

JSONL is preferred first because it matches the project's current evidence and
review-package style. SQLite can be evaluated later for long-running or
high-query workloads.

## Required Behavior

- append-only records preserve write order
- persisted records can reconstruct accepted and rejected delivery summaries
- persisted records include `payload_hash` and `delivery_fingerprint`
- persisted records do not require raw payload expansion for audit summaries
- write paths are scoped to approved project evidence surfaces

## Acceptance

- JSONL store can append message, route, reply, rejection, and conversation
  records
- persisted records can reconstruct a conversation summary
- persisted records exclude raw payload copies by default
- malformed or duplicate traffic is still rejected by the exact delivery rules
- persistent store failure fails closed or reports a clear error
- existing in-memory store behavior remains green

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

- `data/reports/cea-033_append_only_persistent_ledger_pilot.json`
- `data/receipts/2026-07-08-cea-033-append-only-persistent-ledger-pilot.receipt.md`

Do not create completion evidence before implementation and validation pass.

## Completion Summary

CEA-033 implemented a JSONL append-only persistent ledger pilot for the Message
Bus delivery ledger.

Implemented:

- `JsonlMessageLedgerStore`
- `createJsonlMessageLedgerStore(rootDir, ledgerId)`
- append-only `<ledger_id>.ledger.jsonl` file writes
- persisted snapshot reconstruction from JSONL
- shared `createMessageLedgerSnapshot()` helper for in-memory and JSONL stores
- sanitization to the known `MessageLedgerEntry` metadata fields
- unit coverage for append order, raw-payload exclusion, conversation snapshot
  reconstruction, unsafe ledger ids, and clear append failure errors

Boundaries kept:

- SQLite: OUT_OF_SCOPE
- raw payload expansion: DEFAULT_DENY
- secrets/private state: NOT_USED
- governance and AGENTS.md interpretation: OUT_OF_SCOPE
- Phase 8 direct real repository: BLOCKED
- commit / push / deploy / release / tag: NOT_USED

## Completion Evidence

- `data/reports/cea-033_append_only_persistent_ledger_pilot.json`
- `data/receipts/2026-07-08-cea-033-append-only-persistent-ledger-pilot.receipt.md`

## Validation Result

- `npm run build`: PASS
- `npm run test:unit`: PASS, 26 files / 136 tests
- `npm run channel:smoke`: PASS, `cea-023-codex-channel-20260708121829`
- `npm run channel:multiturn`: PASS, `cea-025-multiturn-20260708121848`
- `npm run channel:multirole`: PASS, `cea-026-multirole-20260708121914`
- `npm run validate`: PASS, includes `cea-007-real-smoke-20260708121948`
