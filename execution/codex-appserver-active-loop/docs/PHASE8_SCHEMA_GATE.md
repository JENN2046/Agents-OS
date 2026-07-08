# Phase 8 Schema Gate

CEA-020 watches the local generated App Server schema for a real restricted
readable-root boundary.

## Command

```bash
npm run phase8:schema-gate
```

## Unlock Rule

The gate scans generated App Server TypeScript and JSON Schema files for an
explicit readable-root-like session boundary field, such as:

- `readableRoots`
- `restrictedReadableRoots`
- `allowedReadRoots`
- `permittedReadRoots`

The following fields are recorded but do not unlock Phase 8:

- `cwd`
- `readOnly`
- `networkAccess`
- `sandbox`
- `sandboxPolicy`
- `writableRoots`

If no unlock candidate exists, the gate records `phase8_decision=BLOCK`.

If an unlock candidate appears, the gate records `phase8_decision=REVIEW_REQUIRED`.
That is not an automatic authorization to start Phase 8. A human review must
confirm the field semantics and issue a new explicit authorization before any
managed real-repository Worker or Reviewer session starts.

## Outputs

- `data/reports/cea-020_phase8_schema_gate.json`
- `data/receipts/2026-07-07-cea-020-phase8-schema-gate.receipt.md`

The gate is offline. It does not start App Server, Worker, Reviewer, shell
command APIs, or direct real-repository managed sessions.
