# AGENTS OS docctl apply-fix Design Gate v0.1

Status: `draft_not_active`
Date: 2026-07-02
Owner: Jenn
Agent steward: Nobao
Scope: design gate for any future write-capable `docctl apply-fix` work.
Source of truth for this draft only: this file.
Review by:
`control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-apply-fix-design-gate-v0.1.review.md`

This design gate is not implementation authorization. It does not authorize
`apply-fix`, repair writes, repair patches, snapshot writes, service starts,
executor runs, provider calls, external writes, formal Memory registration, or
P3 bypass.

## Purpose

`apply-fix` would be the first write-capable repair surface in the `docctl`
document-governance body. Before it can be implemented, AGENTS OS needs a
reviewable safety gate that separates:

```text
proposal
design
implementation
execution
evidence
rollback
```

This document defines the gate. It deliberately does not implement the tool.

## Non-Goals

This design gate does not:

```text
modify docctl.py
implement apply-fix
execute any repair
create a repair patch
write a snapshot
start services
run executors
call providers
write formal Memory
change auth/provider/runtime configuration
authorize external writes
```

## Current Allowed Commands

The current command body stays unchanged:

```text
doctor: read-only declared-scope health check
status: read-only pulse over doctor, score, trend, and plan-fix
score: read-only 9.5 eligibility check
trend: read-only comparison against existing local summary snapshots
snapshot: local summary write only after explicit confirmation
plan-fix: dry-run repair proposal only
apply-fix: not implemented and not authorized
```

`plan-fix` remains the source of candidate repair proposals. A proposal is not
permission to write.

## Design Gate Rule

No future `apply-fix` implementation may begin until all of these are true:

```text
1. This design gate has been reviewed.
2. Jenn confirms a separate implementation package.
3. The implementation package names exact supported repair classes.
4. The implementation package names exact writable paths.
5. The implementation package proves protected/P3 paths are blocked before content reading.
6. The implementation package proves apply-fix cannot call providers, start services, run executors, or write external systems.
7. The implementation package includes fixture tests for every supported repair class and every blocked class.
```

Implementation confirmation still does not authorize execution. Execution
requires a later, narrower confirmation for a specific proposal.

## Candidate Repair Classes

The following classes are candidates for future design review only. They are
not authorized for implementation or execution by this document.

### Expected Count Repair

Candidate:

```text
fix expected_document_count in the Federated Document Registry
```

Minimum conditions:

```text
the child registry validator passes
docctl doctor reports only a count mismatch for the target registry
the new count equals the validated checked_documents value
the writable path is the federated registry draft/example file only
receipt/review evidence is created
doctor/status pass after the write
```

### Confirmed Local Evidence Registration

Candidate:

```text
add Document Registry metadata for a confirmed local receipt/review file
```

Minimum conditions:

```text
the file is inside the declared registry directory root
the file is not protected
the file is already part of a confirmed local governance step
the registry entry points to the same file for canonical_path and source_of_truth
review_by points to an existing local review
doctor/status pass after the write
```

### Confirmed Local Governance Document Registration

Candidate:

```text
add Document Registry metadata for a confirmed local runbook, draft, template, or reference
```

Minimum conditions:

```text
the document is inside the declared registry directory root
the document is not protected
the document's status and authority boundary are explicit
the document has owner, source_of_truth, review_by, freshness, and security_boundary fields
doctor/status pass after the write
```

### Existing Review Link Repair

Candidate:

```text
repair a broken review_by path only when the referenced local review already exists
```

Minimum conditions:

```text
the old link is broken
the new review file exists
the new review file is inside the workspace
the new review file is not protected
the repair does not create a review file
doctor/status pass after the write
```

### Safe Path Normalization

Candidate:

```text
normalize a registry path when old and new forms resolve to the same safe local file
```

Minimum conditions:

```text
safe_resolve proves both forms point to the same file
the file is inside the workspace
the file is not protected
the change does not move, rename, copy, delete, or create files
doctor/status pass after the write
```

## Forbidden Repair Classes

Future `apply-fix` must never repair automatically when the proposed action
touches:

```text
state-private/
.env or credential files
secrets/tokens/cookies/credentials
private raw memory
provider raw responses
raw logs
auth/provider/runtime configuration
WORKSPACE_REGISTRY.yaml authority changes
.colameta/plan.json
.colameta/state.json
.colameta/memory.md content
external systems
service starts
executor runs
provider calls
snapshot writes
archive promotion to active guidance
bulk move/delete/rename
history rewrite
force push
tag
deploy
release
publish
```

Future `apply-fix` must also reject any repair that needs to read sensitive
content before deciding whether the repair is safe.

## Confirmation Model

Future work must use separate confirmations:

```text
design gate confirmation
implementation confirmation
execution confirmation
```

Implementation confirmation must name:

```text
exact repair classes
exact files that may be modified by the implementation work
fixture tests
blocked-path tests
evidence paths
validation commands
```

Execution confirmation must name:

```text
exact plan-fix proposal id
exact repair class
exact writable paths
exact evidence paths
rollback route
validation commands
```

No broad "fix everything" execution is allowed.

## Patch And Preview Model

Future `apply-fix` design should prefer a preview-before-write model:

```text
plan-fix produces proposal
apply-fix --preview produces a bounded patch preview
Jenn confirms exact execution
apply-fix writes only the confirmed patch
validators run
receipt/review evidence records result
```

Preview output must not include secrets, tokens, cookies, private memory,
provider raw responses, raw logs, or protected path content.

Any future patch file must be local, reviewable, and non-authoritative until
explicitly applied under a later confirmation.

## Rollback And Evidence Model

Every future apply-fix execution must leave enough local evidence to understand
and reverse the change manually.

Required evidence:

```text
source plan-fix proposal id
selected repair class
files changed
before/after summary
validation results
rollback note
boundary statement
receipt
review
```

Rollback route must be documented before execution. Destructive rollback
commands such as `git reset --hard` or bulk delete remain outside this design
gate and require separate confirmation.

## Validation Model

Minimum validation after any future apply-fix execution:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-document-registry.py control-plane/registry/drafts/document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/validate-federated-document-registry.py control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py doctor
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
```

If implementation changes command behavior, run the relevant fixture tests for
that command before any execution is considered.

## P3 And P3b Stop Rules

P3a requires a preflight report and explicit current authorization. P3b remains
proposal-only and must not execute.

Future `apply-fix` must stop before content reading for:

```text
protected paths
outside-workspace paths
state-private/
secret-like paths
auth/provider/runtime configuration
private raw memory
provider raw response
```

The stop result must be visible and test-covered.

## Future Implementation Preflight

Before any implementation package for `apply-fix`, verify:

```text
docctl status PASS
docctl doctor PASS
docctl score PASS eligible_95=True
docctl trend PASS
docctl plan-fix remains dry-run only
docctl snapshot remains separate from apply-fix
operations runbook is current
this design gate is reviewed
```

If any check fails, do not implement `apply-fix`. Repair the governance body
through a narrower confirmed route first.

## Implementation-Not-Authorized Statement

This design gate is the end of the current authorization.

The next step, if Jenn chooses to continue, must be a separate confirmation
package for `apply-fix` implementation design. No implementation, execution,
patch creation, or repair write is authorized by this file.
