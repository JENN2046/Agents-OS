# docctl Operations Runbook v0.1

Status: `active_local_runbook`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: local operation of AGENTS OS document-governance `docctl` commands.
Source of truth: this file.
Review by:
`control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-docctl-operations-runbook-v0.1.review.md`

This runbook is local operating guidance. It does not authorize external
writes, provider calls, service starts, executor runs, formal Memory
registration, protected path reads, bulk moves/deletes/renames, or automatic
repair writes.

## Purpose

Use this runbook when checking or advancing AGENTS OS document governance.

The goal is to keep the 9.5 body operable:

```text
doctor tells whether the declared document-governance scope is clean
status gives a pulse across the current body
score states 9.5 eligibility
trend compares current health against local summary snapshots
snapshot records reviewed local trend history only after confirmation
plan-fix proposes repair routes without applying them
```

## Command Map

```text
doctor   read-only declared-scope health check
status   read-only pulse over doctor, score, trend, and plan-fix
score    read-only 9.5 eligibility check
trend    read-only comparison against existing local snapshots
snapshot local summary write; explicit confirmation required
plan-fix dry-run repair proposal only
apply-fix not implemented and not authorized
```

Run commands from the workspace root:

```text
/home/jenn/AGENTS_OS_Workspace
```

Use:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py <command>
```

## Green / Yellow / Red Operating Table

Green zone:

```text
docctl doctor
docctl status
docctl score
docctl trend
docctl plan-fix
registry validators
fixture tests
receipt/review evidence writes after confirmed local governance work
```

Yellow zone:

```text
local registry metadata updates
new local runbooks or governance docs
new local receipt/review evidence
docctl snapshot after explicit confirmation
```

Red stop:

```text
apply-fix implementation
repair writes without confirmation
protected path reads
state-private/ reads
secrets/tokens/cookies/credentials/private memory/provider raw response reads
auth/provider/runtime configuration changes
service start
executor run
provider call
external writes
commit / push / tag / deploy / release / publish
bulk move / delete / rename
```

## Read-Only Daily Pulse

For a normal health check, run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
```

Expected healthy result:

```text
Status: PASS
Read only: True
Would write: False
Score: score=100 eligible_95=True
Trend: status=ready
Plan fix: status=no_action_needed
```

If `status` fails, do not jump to writes. Run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
```

Then prepare a narrow confirmation package before any local write.

## Before Local Write

Before any local governance write, check:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
```

Proceed only if:

```text
the target file is inside the workspace
the target file is not protected
the write is scoped to the confirmed task
the write does not alter auth/provider/runtime configuration
the write does not require provider calls or executor runs
the write can leave local receipt/review evidence
```

If a write is needed to fix a document-governance issue, first run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
```

`plan-fix` may propose a route. It must not be treated as permission to write.

## After Local Write

After a confirmed local governance write, leave:

```text
receipt
review
registry entry for every new governed source file
federated expected_document_count update if needed
validation summary
```

Then run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
```

For docctl behavior changes, also run the relevant fixture test file.

## Snapshot Cadence

`docctl snapshot` is a local write-capable command. Do not run it as part of a
routine pulse.

Snapshot is appropriate only after explicit confirmation when:

```text
doctor is clean
score is 9.5 eligible or the non-eligible state is intentionally being recorded
trend needs a reviewed baseline point
the snapshot output path is under control-plane/registry/reports/docctl-snapshots/
the output file does not already exist
```

Snapshot output must remain summary-only:

```text
raw_registry_content_included=false
raw_logs_included=false
full_document_text_included=false
secrets_included=false
provider_raw_response_included=false
```

## Plan-Fix Dry-Run Route

Use `plan-fix` when `doctor` or `status` reports a problem:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix --json
```

Interpretation:

```text
no_action_needed      no repair proposal required
proposals_ready       prepare a confirmation package before any write
blocked               stop at boundary review
```

`plan-fix` must remain:

```text
dry_run=true
would_write=false
write_performed=false
patch_created=false
snapshot_write_performed=false
apply_fix_implemented=false
```

## P3 Hard Stops

Stop before content reading or writing if the action touches:

```text
state-private/
.env or credential files
secrets/tokens/cookies/credentials
private raw memory
provider raw responses
raw logs that may contain secrets or provider output
auth/provider/runtime configuration
global runtime behavior files without explicit current authorization
external irreversible writes
release/deploy/publish/tag/force-push/history rewrite
bulk delete/move/rename
```

For P3a, prepare a preflight report and request explicit confirmation.
For P3b, proposal only; do not execute.

## Evidence Checklist

For each local governance construction step, record:

```text
what changed
what did not change
scope and boundary
validation results
remaining risk
next recommended action
```

Use local evidence paths:

```text
control-plane/registry/receipts/
control-plane/registry/reviews/
```

Do not write formal AGENTS OS Memory unless Jenn explicitly enters the Memory
confirmation path.

## Validation Checklist

Minimum closeout for a document-governance change:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
```

When the change touches score or trend behavior:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend
```

When the change touches a docctl command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/test-docctl-<command>.py
```

## Escalation And Stop Rules

Continue automatically when:

```text
the work is local
the boundary is clear
the file scope is confirmed
validation failures are local and diagnosable
the next action is read-only or an already confirmed local documentation write
```

Stop and ask Jenn when:

```text
the next action is outside the confirmed scope
the action would modify auth/provider/runtime configuration
the action would start a service or run an executor
the action would call a provider
the action would write a snapshot without explicit confirmation
the action would implement or run apply-fix
the action would touch P3/P3b material
the action would overwrite unclear user work
```

## Current Known Healthy Shape

At v0.1 creation, the expected healthy body is:

```text
docctl doctor PASS
docctl status PASS
docctl score PASS score=100 eligible_95=True
docctl trend PASS trend_status=ready snapshots_found=1
docctl plan-fix PASS plan_status=no_action_needed
```

If this shape changes, update the relevant receipt/review evidence and keep the
registry clean.
