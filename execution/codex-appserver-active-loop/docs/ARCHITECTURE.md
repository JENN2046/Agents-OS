# Architecture

## Purpose

This project is a local MVP for a Codex App Server active event loop. The loop will use `codex app-server` through stdio JSON-RPC to coordinate a Worker thread, a Reviewer thread, and a local Bridge.

## App Server First

The MVP uses App Server because the taskbook requires the installed local Codex runtime as the integration surface. Workspace Agents API, Responses API, browser automation, and WebSocket transport are outside the authorized MVP boundary.

## Stdio First

Stdio is the first transport because it keeps the App Server local, process-scoped, and easier to validate. WebSocket is deferred until the stdio loop, schema handling, state machine, and safety gates have passed the MVP smoke.

## Responsibilities

- Worker: runs under read-only sandboxing and emits structured `NEED_REVIEWER` and `DONE` payloads.
- Reviewer: reviews the Worker payload under read-only sandboxing and emits structured `REVIEWER_DECISION`.
- Bridge: starts sessions, routes events, validates structured outputs, enforces policy, writes local jobs/events/receipts/reports, and blocks on unsafe or unknown requests.

Current Codex App Server generated types do not expose `readableRoots` or an equivalent restricted readable-root field. The MVP therefore proves the synthetic loop under `readOnly` plus `cwd`, but it does not prove safe real-repository read boundaries. Phase 8 remains blocked unless a future schema exposes restricted readable roots or a separate authorization accepts a weaker cwd-scoped read-only pilot.

## Event Flow

The intended MVP flow is:

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
```

Every implemented transition must be written to `data/events/<job_id>.events.jsonl`.

## Synthetic Workspace First

The synthetic workspace is first because real repository access is forbidden for MVP smoke. It gives the Worker and Reviewer harmless files while proving the event loop, output schemas, and policy boundaries.

## Safe Snapshot Path

While restricted readable roots are unavailable in the generated App Server schema, real project review must use a Bridge-owned snapshot layer. The Bridge exporter reads an approved source root through an allowlist, skips denied paths and sensitive content patterns, writes a snapshot manifest plus exclusion report, and only then may a managed Worker/Reviewer use the snapshot root as `cwd`.

Direct real repository Worker/Reviewer sessions remain blocked.

## Context Ledger Path

CEA-012 adds a record-only context ledger for Codex coordination metadata. It is
separate from the App Server JSON-RPC control plane and the safe snapshot data
plane.

The ledger records task, source, role, session, timestamp, content hash,
artifact reference, and snapshot reference metadata. It does not store raw
message content and does not inject ledger history into managed Worker or
Reviewer contexts.

This gives the Commander/Bridge line an auditable timeline for retries,
deduplication, review requests, and receipt binding while preserving the CEA-011
rule that managed sessions operate from snapshot artifacts rather than the real
repository.

## Context Promotion Gate

CEA-013 adds a gate between ledger metadata and any future Worker/Reviewer
prompt use. The gate queries record-only ledger entries and writes a context
promotion packet. Packets are blocked by default.

Commander or Reviewer approval can mark a packet as approved for explicit
packet-only use, but automatic injection remains disabled. Worker self-promotion
is rejected. This keeps the control plane auditable while preventing ledger
history from silently becoming model context.

## Promotion Approval Receipt

CEA-014 stores the approval as a separate receipt. The receipt binds to the
blocked source packet by hash, records Commander or Reviewer approval metadata,
and preserves the rule that approval means packet-only eligibility rather than
automatic context injection.

## Prompt Packet Compiler

CEA-015 compiles an approved packet into a dry-run prompt annex. The compiler
uses only packet metadata and approval receipt metadata. It does not read
artifact contents and does not launch managed sessions.

The annex is the first artifact that is shaped for future Worker consumption,
but it remains a preview until a later snapshot-bound Worker pilot explicitly
uses it.

## Snapshot-Bound Worker Prep

CEA-016 prepares the Worker pilot by validating the snapshot manifest, prompt
annex, and `cwd` policy. It writes a prep-only Worker plan with read-only
sandboxing and snapshot-root `cwd`.

The prep step intentionally does not call App Server. It creates the auditable
launch plan that a later live Worker pilot can consume.

## Live Snapshot Worker Run

The CEA-016 live Worker command consumes the prep plan and starts exactly one
managed Worker thread. The App Server process itself is also started from the
snapshot root, so both process cwd and Worker cwd avoid the real repository.

The live run does not start Reviewer. It validates that the Worker can complete
a structured `DONE` turn under read-only, network-off sandboxing.

## Live Snapshot Reviewer Run

CEA-017 consumes the CEA-016 Worker DONE report and starts one managed Reviewer
thread from the same snapshot root. The Reviewer returns structured
`REVIEWER_DECISION` and does not inspect the real repository.

## End-to-End Safe Review Loop

CEA-018 composes the full safe chain into one command. The Bridge exports a
fresh snapshot, records context metadata, promotes and approves a packet,
compiles a prompt annex, starts a snapshot-bound Worker, then starts a
snapshot-bound Reviewer in the same App Server process.

The command proves the operational loop while preserving the separation between
real repository reads, snapshot artifacts, and managed Codex sessions.
