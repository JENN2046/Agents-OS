# Commander Closeout / Readiness Matrix

CEA-022 closes the Commander review chain for CEA-011 through CEA-021.

## Command

```bash
npm run commander:closeout
```

## Purpose

The matrix gives Commander a single final status table:

- which safe snapshot review capabilities are available
- which evidence reports and receipts support each capability
- whether the external review package is available
- why direct real-repository Phase 8 remains blocked
- what exact conditions are required before Phase 8 can be reconsidered

## Status Meaning

- `AVAILABLE`: all required evidence exists, has a pass-like result, and has a receipt.
- `PARTIAL`: evidence exists but at least one required receipt or pass-like result is missing.
- `MISSING`: one or more required evidence reports are absent from the matrix inputs.

## Matrix Scope

The closeout covers:

- CEA-011 safe repo snapshot exporter
- CEA-012 context ledger
- CEA-013 context promotion gate
- CEA-014 promotion approval receipt
- CEA-015 prompt packet compiler
- CEA-016 snapshot-bound Worker prep plus live Worker run
- CEA-017 snapshot-bound Reviewer pilot
- CEA-018 end-to-end safe review loop
- CEA-019 offline evidence verification gate
- CEA-020 Phase 8 schema gate
- CEA-021 snapshot review package publisher

## Phase 8 Rule

Snapshot-bound safe review may be `READY` while direct real-repository managed
sessions remain blocked.

Phase 8 can only be reconsidered when all of these are true:

- App Server generated schema exposes `readableRoots` or an equivalent restricted readable-root field.
- CEA-020 returns an unlock candidate requiring review instead of `BLOCK`.
- Human semantic review confirms the field constrains managed-session readable roots.
- A new explicit Phase 8 authorization package defines target root, readable roots, denylist, evidence location, and stop conditions.
- A dry-run or preflight confirms secrets, `state-private`, `.git`, `node_modules`, `dist`, and denied paths are not readable by managed sessions.

## Outputs

- `data/reports/cea-022_commander_closeout_readiness_matrix.json`
- `data/receipts/<date>-cea-022-commander-closeout-readiness-matrix.receipt.md`

The closeout is offline. It does not start App Server, Worker, Reviewer, shell
command APIs, command execution APIs, or direct real-repository managed sessions.
