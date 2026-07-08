# Commander Review And Tasking

date: 2026-07-07
result: PROCEED_TO_TASKING
implementation_status: NOT_STARTED

## Sources Reviewed

- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/00_EXECUTIVE_DECISION.md`
- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/01_MASTER_PLAN.md`
- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/02_PHASE_PLANS.md`
- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/03_CODEX_EXECUTION_TASKBOOK.md`
- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/04_ACCEPTANCE_CRITERIA.md`
- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/05_SECURITY_BOUNDARIES.md`
- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/06_EVENT_CONTRACT.md`
- `docs/intake/2026-07-07-fixed-plan-taskbook/codex_appserver_active_loop_pack/08_ROUNDTABLE_REVIEW.md`

## Commander Decision

The archived plan is accepted as the active MVP task source.

The authorized implementation scope is:

```text
scaffold + schema generation + real app-server smoke
```

No broader production use, real repository write, commit, push, deploy, release, tag, WebSocket transport, Workspace Agents API, Responses API, browser automation, or unrestricted managed session is authorized.

## Execution Gate

Phase 0 is the hard gate.

Implementation may scaffold the target project, install local Node dependencies, generate schemas, and run the real `codex app-server` handshake and smoke only inside:

```text
A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
```

If `codex app-server`, schema generation, `outputSchema`, or stdio JSON-RPC initialization fails, execution must report `BLOCK` instead of simulating success.

## Primary Risks

1. Local installed Codex App Server schema may differ from the archived assumptions.
2. `outputSchema` support may be missing or shaped differently.
3. Server-initiated request response shapes may need schema-derived handling.
4. Smoke tests can give false confidence if they mock App Server or silently skip.
5. Managed Worker and Reviewer permissions can be confused with the implementation agent permission unless explicitly encoded and tested.

## Commander Rules For Assigned Work

- Write only inside the target project repo.
- Managed Worker and Reviewer sessions must use read-only restricted sandboxing.
- Smoke must use synthetic workspace only.
- Smoke must use real `codex app-server`.
- Unit tests may mock; smoke tests may not mock App Server.
- Unknown server requests must decline if safe to answer, otherwise transition to `BLOCKED`.
- Any secret-like path, real repository access during MVP smoke, forbidden method, or required experimental API is an immediate `BLOCK`.

## Task Assignments

### CEA-001: Project Scaffold

owner_role: Implementation Agent
status: READY

Create the TypeScript project shell, required directories, package scripts, tsconfig, and placeholder docs. Do not implement the full loop yet.

acceptance:

- Required directory structure exists.
- `package.json` includes `build`, `test`, `test:unit`, `smoke`, and `validate`.
- No files are created outside the target project repo.

### CEA-002: Phase 0 Reality Calibration

owner_role: Runtime Integration Agent
status: READY_AFTER_CEA-001

Verify local `codex`, start real `codex app-server`, generate TypeScript and JSON schemas, send `initialize`, send `initialized`, and write `data/reports/phase0_reality_calibration.json`.

acceptance:

- `codex --version` recorded.
- TypeScript and JSON schemas generated from installed Codex.
- App Server initialization succeeds through stdio.
- No `capabilities.experimentalApi=true` is used.

block_if:

- `codex` is missing.
- `codex app-server` cannot start.
- schema generation fails.
- initialization fails.

### CEA-003: JSON-RPC Client And Stdio Transport

owner_role: Runtime Integration Agent
status: READY_AFTER_CEA-002

Implement request/response correlation, notifications, server-request handling hooks, JSONL encoding/decoding, timeouts, stderr sanitization, and clean shutdown.

acceptance:

- Unit tests cover request ids, message builders, response correlation, notifications, server-request classification, and timeout cleanup.
- Forbidden App Server methods are not present in client call surfaces.

### CEA-004: State Machine, Policy Gate, And Stores

owner_role: Safety/State Agent
status: READY_AFTER_CEA-003

Implement state transitions, denied path checks, default decline/block policy, job store, event store, receipt store, and final report structure.

acceptance:

- Invalid state transitions fail closed.
- Denied path terms are blocked before read/write.
- `item/fileChange/requestApproval` declines in MVP.
- Every transition can be written to JSONL.

### CEA-005: Synthetic Workspace And Event Contracts

owner_role: Implementation Agent
status: READY_AFTER_CEA-004

Create the synthetic workspace and encode Worker `NEED_REVIEWER`, Reviewer `REVIEWER_DECISION`, Worker `DONE`, and `BLOCKED` schemas.

acceptance:

- Synthetic workspace contains only harmless sample files.
- No `.env`, credential, token, cookie, SSH, or private-state paths exist.
- Smoke turns use the synthetic workspace as `cwd` and only readable root.

### CEA-006: Worker Reviewer Resume Loop

owner_role: Runtime Integration Agent
status: READY_AFTER_CEA-005

Implement the orchestrator flow: Worker emits `NEED_REVIEWER`, Reviewer emits `REVIEWER_DECISION`, Bridge resumes Worker, Worker emits `DONE`.

acceptance:

- `thread/start` and `turn/start` are used under read-only restricted sandbox.
- `turn/steer` is used only when active turn id is known.
- Malformed structured output is rejected.
- Final state reaches `DONE` only when receipt and event log are written.

### CEA-007: Real Smoke And Final Evidence

owner_role: QA/Verification Agent
status: READY_AFTER_CEA-006

Run `npm run build`, `npm run test`, and `npm run smoke`. Smoke must use real App Server and must not skip.

acceptance:

- `data/jobs/<job_id>.json` exists.
- `data/events/<job_id>.events.jsonl` exists.
- `data/receipts/<job_id>.receipt.md` exists.
- `data/reports/final_report.json` exists.
- Final report records all forbidden APIs as `NOT_USED`.

### CEA-008: Commander Closeout Review

owner_role: Commander/Reviewer
status: READY_AFTER_CEA-007

Review final artifacts against the acceptance criteria and decide whether Phase 8 read-only real repo pilot can be considered later.

acceptance:

- No real repo access occurred during MVP smoke.
- No secrets were read.
- No commit, push, deploy, release, or tag occurred.
- Phase 8 remains blocked until Phase 0-7 are all PASS.

## Current Dispatch

The next executable task is `CEA-001`.

Do not start Phase 8. Do not connect real AGENTS OS repositories. Do not create a commit.
