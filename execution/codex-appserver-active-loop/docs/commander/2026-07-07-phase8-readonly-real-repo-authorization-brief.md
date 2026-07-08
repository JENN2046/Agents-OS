# Phase 8 Read-only Real Repo Pilot Authorization Brief

date: 2026-07-07
status: AUTHORIZATION_PACKAGE_PREPARED
execution_status: NOT_STARTED
gate: PHASE8_READONLY_REAL_REPO_PILOT

## Purpose

Open a new authorization package for Phase 8: a read-only pilot against a real project target after the synthetic Worker -> Reviewer -> Worker MVP has passed.

This brief does not start Phase 8. It defines the scope, safety gates, task sequence, evidence requirements, and explicit authorization needed before any real project pilot begins.

## Prior Evidence

- CEA-001 through CEA-008 are marked `DONE`.
- CEA-008 result is `PASS`.
- MVP final state is `DONE`.
- Real App Server smoke result is `PASS`.
- Phase 8 is currently `GATED_NOT_STARTED`.
- Forbidden API and delivery flags are recorded as `NOT_USED`.

Evidence files:

- `data/jobs/commander_task_queue_2026-07-07.json`
- `data/reports/cea-008_commander_closeout_review.json`
- `data/reports/final_report.json`
- `data/receipts/2026-07-07-cea-008-commander-closeout-review.receipt.md`

## Proposed Pilot Target

Default candidate target:

```text
A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
```

Scope:

- Read-only self-review of the Codex App Server Active Event Loop project.
- Review implementation, receipts, reports, tests, smoke evidence, and security boundaries.
- Do not modify files.
- Do not access other AGENTS OS repositories.

If the target directory is not a git repository, the pilot remains a read-only project self-review. Git metadata is not required for the pilot. No other repository becomes authorized by fallback.

## Known Denylist Filename Hits

The target project contains generated App Server schema/type filenames and dependency type filenames that include denylist terms such as `tokens` or `cookies`.

These are path-level findings, not secret values. Their contents were not read while preparing this authorization package.

Phase 8 must not read these files. The preflight may list the paths and then exclude them from managed review:

```text
dist/src/generated/appserver/v2/ChatgptAuthTokensRefreshParams.js
dist/src/generated/appserver/v2/ChatgptAuthTokensRefreshReason.js
dist/src/generated/appserver/v2/ChatgptAuthTokensRefreshResponse.js
node_modules/undici-types/cookies.d.ts
schemas/appserver/ChatgptAuthTokensRefreshParams.json
schemas/appserver/ChatgptAuthTokensRefreshResponse.json
src/generated/appserver/v2/ChatgptAuthTokensRefreshParams.ts
src/generated/appserver/v2/ChatgptAuthTokensRefreshReason.ts
src/generated/appserver/v2/ChatgptAuthTokensRefreshResponse.ts
```

If excluding these paths prevents a meaningful read-only pilot, Phase 8 must return `BLOCK` and request a narrower target or an explicit revised policy.

## Explicitly Not Authorized

- VCPToolBox review or access.
- codex-router review or access.
- Bounded-High-Autonomy review or access.
- Photo Studio review or access.
- `state-private/` access.
- Secret, credential, token, cookie, SSH key, or `.env` reads.
- File writes during the pilot.
- Commit, push, deploy, release, tag, or history rewrite.
- Workspace Agents API.
- Responses API.
- Browser automation against ChatGPT.
- WebSocket transport.
- `thread/shellCommand`.
- `command/exec` or `command/exec/write`.
- `process/*`.
- `full_access` or `dangerFullAccess`.
- `capabilities.experimentalApi=true`.

## Managed Session Boundary

Any managed Worker or Reviewer session used for Phase 8 must run with:

```json
{
  "type": "readOnly",
  "access": {
    "type": "restricted",
    "includePlatformDefaults": true,
    "readableRoots": [
      "A:\\AGENTS_OS_Workspace\\governance\\codex-appserver-active-loop\\repo"
    ]
  }
}
```

The implementation agent may prepare authorization documents inside the target project. The managed Phase 8 pilot may only read the approved target root after explicit activation.

## Stop Conditions

Return `BLOCK` immediately if:

- The pilot needs any target outside the approved root.
- A secret-like path must be read.
- A write is required.
- A forbidden App Server method appears necessary.
- WebSocket or experimental API support appears necessary.
- App Server cannot run without broader permissions.
- Any evidence file contradicts CEA-008 `PASS`.
- The reviewer cannot determine whether the pilot remained read-only.

## Phase 8 Task Sequence

### P8-001: Authorization Confirmation

status: AWAITING_EXPLICIT_AUTHORIZATION

Confirm the exact target root, scope, and read-only mode before execution.

### P8-002: Read-only Preflight

status: BLOCKED_UNTIL_P8-001

Validate that the approved target exists, contains expected Phase 0-7 evidence, has no required secret reads, excludes known denylist filename hits from content reads, and can be reviewed without writing.

### P8-003: Real Project Read-only Worker Review

status: BLOCKED_UNTIL_P8-002

Use the App Server loop to run a read-only Worker review against the approved target. The Worker must output structured review findings or `DONE` under schema.

### P8-004: Reviewer Decision

status: BLOCKED_UNTIL_P8-003

Route Worker findings to Reviewer for structured decision: `continue`, `revise`, `block`, or `request_human_gate`.

### P8-005: Receipt And Commander Closeout

status: BLOCKED_UNTIL_P8-004

Write Phase 8 job, event log, receipt, and closeout report. Confirm no writes to reviewed target occurred except approved evidence under this project if explicitly scoped.

## Acceptance Criteria

- Approved target root is explicit.
- Managed sessions are read-only and restricted.
- No secrets are read.
- Known denylist filename hits are skipped for content reads.
- No file modifications occur during the pilot review.
- No forbidden APIs or methods are used.
- Event log and receipt are created.
- Reviewer decision is structured and recorded.
- Phase 8 final state is one of `DONE`, `BLOCKED`, or `HUMAN_GATE_REQUIRED`.

## Activation Requirement

Phase 8 remains not started until Jenn explicitly authorizes the pilot execution with the target and scope.

Smallest safe activation phrase:

```text
启动 Phase 8 read-only pilot，目标仅限 A:\AGENTS_OS_Workspace\governance\codex-appserver-active-loop\repo
```

Without that activation, the only authorized work is maintaining this authorization package.
