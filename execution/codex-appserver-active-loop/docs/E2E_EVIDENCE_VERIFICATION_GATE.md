# E2E Evidence Verification Gate

CEA-019 verifies the latest CEA-018 evidence without starting new App Server,
Worker, or Reviewer sessions.

## Command

```bash
npm run safe-review:verify
```

## Checks

- CEA-018 report result is `PASS`.
- Worker output is structured `DONE`.
- Reviewer output is structured `REVIEWER_DECISION` with `decision=continue`.
- App Server, Worker, and Reviewer cwd boundary summary is snapshot-only.
- Phase 8 direct real repository access remains `BLOCKED`.
- Policy decision count is zero.
- All CEA-018 artifacts exist.
- Snapshot manifest includes no forbidden `.git`, `node_modules`, `dist`,
  `state-private`, `.env`, `config.env`, or `secrets` paths.
- Events contain snapshot export, Worker and Reviewer thread/turn start,
  Worker and Reviewer turn completion, structured output parsing, report write,
  and receipt write.
- Stderr event summaries do not carry `hasError=true`.

## Outputs

- `data/reports/cea-019_e2e_evidence_verification_gate.json`
- `data/receipts/2026-07-07-cea-019-e2e-evidence-verification-gate.receipt.md`

The verifier is an offline evidence gate. It does not authorize direct real
repository managed sessions and does not weaken the Phase 8 readable-root block.
