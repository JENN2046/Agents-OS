# 03｜CODEX EXECUTION TASKBOOK｜Codex App Server Active Event Loop MVP

## 0. Role

You are the Codex implementation agent for Jenn’s local AGENTS OS workspace.

You are implementing a local **Codex App Server Active Event Loop MVP**.

This is not:
- a ChatGPT Workspace Agent integration
- a Responses API integration
- browser automation against chatgpt.com
- a public WebSocket server
- a production runtime

The MVP goal is to build a local orchestrator that controls `codex app-server` through stdio JSON-RPC and manages a Worker thread plus a Reviewer thread.

## 1. Target Project Path

Create or use only this project path:

```text
A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
```

If the path does not exist, create it.

## 2. Implementation Permission

The implementation agent may create and modify files **only inside**:

```text
A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
```

Do not modify any other repository, workspace, global config, or user file.

## 3. Managed Runtime Permission

The Active Loop runtime created by this project must start all managed Codex Worker / Reviewer sessions in read-only mode by default.

Managed Worker / Reviewer sessions must use:

```text
sandboxPolicy.type = readOnly
restricted readableRoots
synthetic workspace only in MVP
```

## 4. Hard Boundaries

Do not:

- push
- deploy
- release
- create git tags
- commit unless explicitly asked in a future task
- read secrets
- read `.env` values
- read credentials, tokens, cookies, SSH keys
- modify files outside the target project repo
- call Workspace Agents API
- call Responses API
- automate browser ChatGPT UI
- use WebSocket transport in MVP
- expose non-loopback WebSocket
- set `capabilities.experimentalApi=true`
- call `thread/shellCommand`
- call `command/exec`
- call `command/exec/write`
- call `process/*`
- use `dangerFullAccess`
- use `full_access`
- use unrestricted read roots for managed Worker / Reviewer sessions
- point MVP smoke at real AGENTS OS repositories
- silently skip real app-server smoke

If a required task appears to need any forbidden action, stop and report `BLOCK`.

## 5. Required Project Structure

Create:

```text
src/
  appserver/
    jsonrpc.ts
    transport_stdio.ts
    client.ts
  bridge/
    orchestrator.ts
    event_router.ts
    state_machine.ts
    policy_gate.ts
    prompts.ts
  stores/
    job_store.ts
    event_store.ts
  cli/
    run_mvp.ts
  types/
    events.ts
    jobs.ts
  generated/
    appserver/
schemas/
  appserver/
tests/
  unit/
    jsonrpc.test.ts
    state_machine.test.ts
    policy_gate.test.ts
  smoke/
    appserver_handshake.test.ts
    worker_reviewer_loop.test.ts
docs/
  ARCHITECTURE.md
  SECURITY_BOUNDARIES.md
  EVENT_CONTRACT.md
data/
  synthetic-workspace/
  jobs/
  events/
  receipts/
  reports/
package.json
tsconfig.json
README.md
```

Use TypeScript.

If TypeScript is not viable in the local environment, stop and report `BLOCK` with reason.

## 6. Phase 0｜Reality Calibration

### Tasks

1. Verify `codex` exists on PATH.
2. Verify `codex --version` can run.
3. Verify `codex app-server` can start via stdio.
4. Generate TypeScript schema:

```bash
codex app-server generate-ts --out ./src/generated/appserver
```

5. Generate JSON schema:

```bash
codex app-server generate-json-schema --out ./schemas/appserver
```

6. Start app-server.
7. Send `initialize`.
8. Send `initialized` notification.
9. Record result to:

```text
data/reports/phase0_reality_calibration.json
```

### Failure Rule

Do not skip. If app-server cannot start, return `BLOCK`.

## 7. Phase 1｜JSON-RPC Client

Implement:

### `src/appserver/jsonrpc.ts`

Must provide:
- request id generation
- request message builder
- notification message builder
- response correlation
- error parsing
- JSONL encode/decode

### `src/appserver/transport_stdio.ts`

Must provide:
- spawn `codex app-server`
- write JSONL messages
- read stdout JSONL messages
- read stderr safely without leaking secrets
- timeout handling
- clean shutdown

### `src/appserver/client.ts`

Must provide:
- `initialize()`
- `sendInitialized()`
- `threadStart()`
- `turnStart()`
- `turnSteer()` only if active turn id is known
- `turnInterrupt()`
- `reviewStart()` for later phases, not required in smoke
- generic server-request handler hook
- event subscription / callback mechanism

## 8. Phase 2｜Synthetic Workspace

Create:

```text
data/synthetic-workspace/
  README.md
  sample.txt
  src/example.ts
```

Rules:

- no secrets
- no `.env`
- no credentials
- no tokens
- not a git repo unless needed for harmless review tests
- all smoke tests must set `cwd` to this directory
- all smoke turns must use restricted readableRoots pointing only to this directory

## 9. Event Contract

### Worker output schema

For smoke test, Worker must return exactly:

```json
{
  "type": "NEED_REVIEWER",
  "problem_type": "architecture",
  "question": "string",
  "evidence": ["string"],
  "proposed_options": ["string"],
  "recommended_next_action": "string"
}
```

Allowed `problem_type` values:

```text
architecture
policy
test_failure
diff_review
unclear_intent
```

### Reviewer output schema

Reviewer must return exactly:

```json
{
  "type": "REVIEWER_DECISION",
  "decision": "continue",
  "reason": "string",
  "next_instruction": "string",
  "constraints": ["string"],
  "evidence_used": ["string"]
}
```

Allowed `decision` values:

```text
continue
revise
block
request_human_gate
```

### Worker completion schema

Final Worker turn must return exactly:

```json
{
  "type": "DONE",
  "summary": "string",
  "evidence": ["string"]
}
```

## 10. Phase 3｜Worker Thread

Tasks:

1. Start Worker thread.
2. Start Worker turn with:
   - `cwd = data/synthetic-workspace`
   - readOnly sandbox
   - restricted readableRoots
   - outputSchema for `NEED_REVIEWER`
3. Prompt Worker to inspect synthetic files and emit `NEED_REVIEWER`.
4. Bridge must parse the structured output.
5. State transition: `WORKER_RUNNING → NEED_REVIEWER`.

Do not accept malformed JSON as valid.

## 11. Phase 4｜Reviewer Thread

Tasks:

1. Start Reviewer thread.
2. Start Reviewer turn with:
   - readOnly sandbox
   - restricted readableRoots
   - outputSchema for `REVIEWER_DECISION`
3. Send Worker’s `NEED_REVIEWER` payload as input.
4. Reviewer returns a valid `REVIEWER_DECISION`.
5. State transition: `REVIEWER_RUNNING → REVIEW_RECEIVED`.

Reviewer must not write files.

## 12. Phase 5｜Resume Worker

Tasks:

1. Create a structured `REVIEWER_DECISION_RECEIVED` message.
2. Resume Worker:
   - use `turn/start` if idle
   - use `turn/steer` only if active turn id is known and expectedTurnId matches
3. Ask Worker to return `DONE` using outputSchema.
4. State transition: `CODEX_RESUMED → DONE`.

## 13. Phase 6｜Server Request / Approval Handling

Implement generic server-request handling.

Rules:

- Unknown server request: log and decline if a decision response shape is known; otherwise BLOCK.
- `item/fileChange/requestApproval`: decline in MVP.
- Any path containing denied terms: decline.
- Any request requiring write permission: decline in MVP.
- Any request requiring human gate: state `HUMAN_GATE_REQUIRED`.

Denied path terms:

```text
.env
secrets
credentials
tokens
cookies
.ssh
state-private
```

Forbidden methods must never be called:

```text
thread/shellCommand
command/exec
command/exec/write
process/*
```

## 14. State Machine

Implement:

```text
CREATED
APP_SERVER_STARTED
INITIALIZED
SCHEMA_GENERATED
SYNTHETIC_WORKSPACE_READY
WORKER_THREAD_STARTED
WORKER_RUNNING
NEED_REVIEWER
REVIEWER_THREAD_STARTED
REVIEWER_RUNNING
REVIEW_RECEIVED
CODEX_RESUMED
DONE
BLOCKED
HUMAN_GATE_REQUIRED
FAILED
```

Every transition must be written to:

```text
data/events/<job_id>.events.jsonl
```

## 15. Storage

Use local JSON / JSONL:

```text
data/jobs/<job_id>.json
data/events/<job_id>.events.jsonl
data/receipts/<job_id>.receipt.md
data/reports/final_report.json
```

Do not store:
- bearer tokens
- raw environment variables
- secret values
- cookies
- credential file contents

## 16. Smoke Test

Create a real smoke test:

```bash
npm run smoke
```

The smoke test must:

1. Start real `codex app-server`.
2. Initialize.
3. Send initialized.
4. Generate / confirm schemas.
5. Prepare synthetic workspace.
6. Start Worker thread.
7. Worker emits `NEED_REVIEWER` under outputSchema.
8. Start Reviewer thread.
9. Reviewer emits `REVIEWER_DECISION` under outputSchema.
10. Resume Worker.
11. Worker emits `DONE`.
12. Write event log.
13. Write receipt.
14. Cleanly stop app-server.

The smoke test must fail/BLOCK if:
- `codex` is missing
- app-server cannot start
- schema generation fails
- initialize fails
- thread/start fails
- turn/start fails
- no notifications are received
- structured output is malformed
- Worker does not produce `NEED_REVIEWER`
- Reviewer does not produce `REVIEWER_DECISION`
- Worker does not produce `DONE`
- receipt is missing

Do not silently skip.

## 17. Unit Tests

Create:

```text
tests/unit/jsonrpc.test.ts
tests/unit/state_machine.test.ts
tests/unit/policy_gate.test.ts
```

Unit tests may use mocks.

Smoke tests must use real app-server.

## 18. Documentation

Create:

### `docs/ARCHITECTURE.md`

Must explain:
- why App Server is used
- why stdio is used first
- why WebSocket is deferred
- Worker / Reviewer / Bridge responsibilities
- event flow
- why synthetic workspace is first

### `docs/SECURITY_BOUNDARIES.md`

Must explain:
- implementation write boundary
- managed runtime read-only boundary
- restricted readableRoots
- denied paths
- denied actions
- why `thread/shellCommand`, `command/exec`, `process/*`, `full_access`, and WebSocket are forbidden in MVP

### `docs/EVENT_CONTRACT.md`

Must define:
- Worker NEED_REVIEWER format
- Reviewer REVIEWER_DECISION format
- Worker DONE format
- state transition event format
- receipt format

## 19. Package Scripts

Add scripts:

```json
{
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "npm run test:unit",
    "test:unit": "vitest run tests/unit",
    "smoke": "tsx src/cli/run_mvp.ts",
    "validate": "npm run build && npm run test && npm run smoke"
  }
}
```

Use equivalent tools if Vitest/tsx are not viable, but document why.

## 20. Final Report

After implementation, output:

```yaml
result: PASS | BLOCK
project_path: A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
implemented_files:
  - ...
validation:
  schema_generation: PASS | FAIL
  build: PASS | FAIL
  unit_tests: PASS | FAIL
  smoke: PASS | FAIL
boundaries:
  workspace_agents_api: NOT_USED
  responses_api: NOT_USED
  browser_automation: NOT_USED
  websocket: NOT_USED
  non_loopback_websocket: NOT_USED
  experimental_api: NOT_USED
  thread_shell_command: NOT_USED
  command_exec: NOT_USED
  process_api: NOT_USED
  full_access: NOT_USED
  push_deploy_release: NOT_USED
  real_repo_access: NOT_USED
state_machine:
  final_state: DONE | BLOCKED | FAILED
artifacts:
  job_json: ...
  events_jsonl: ...
  receipt: ...
findings:
  - ...
next_recommended_step:
  - ...
```

## 21. Stop Conditions

Return `BLOCK` immediately if:

- `codex app-server` cannot start
- generated schema commands fail
- any forbidden method appears necessary
- any real repository must be accessed for MVP
- any secret-like path must be read
- any non-target path must be modified
- WebSocket is required
- experimental API is required
- outputSchema is unsupported by installed App Server

## 22. Expected Final Result

A minimal but real local loop:

```text
Worker NEED_REVIEWER
  ↓
Bridge
  ↓
Reviewer REVIEWER_DECISION
  ↓
Bridge
  ↓
Worker DONE
```

All under:

```text
stdio
readOnly restricted
synthetic workspace
no secrets
no writes outside target project repo
```
