# Document Governance 9.5 Plan

Status: `draft_not_active`
Date: 2026-07-01
Owner: Jenn
Agent steward: Nobao
Scope: AGENTS OS local document-governance improvement plan
Source of truth for this draft only: this file
Review by: `control-plane/registry/reviews/2026-07-01-yellow-document-governance-9.5-plan.review.md`

This is a planning draft, not active authority data. It does not authorize
external writes, runtime/provider calls, formal Memory registration, protected
path reads, bulk moves/deletes, or automatic changes to
`WORKSPACE_REGISTRY.yaml`.

## One Sentence

The path from 8/10 to 9.5/10 is not more documents. It is making document
governance harder to game, easier to enter, safer to automate, and measurable
without losing judgment.

## Current Baseline

Current clean baseline before this plan:

```text
registries=3
documents=102
scanned_files=149
known_external_scope=1
archived=50
unregistered=0
warn=0
fail=0
```

This baseline proves the current skeleton is clean. It does not yet prove the
system will stay clean under large document volume.

## Debate Summary

The support view:

```text
Keep distributed ownership, federated rollup, read-only doctor, local files as
source of truth, archive as explanation, and receipt/review as evidence.
```

The red-team view:

```text
Do not confuse computable with trustworthy. A score can be gamed if schema,
lifecycle, adversarial tests, and exception review are weak.
```

The scale view:

```text
Harden the rules first, then add intake, then exception governance, then impact,
then score, then trend.
```

The security view:

```text
doctor stays permanently read-only. apply-fix is deferred. All P3 boundaries
remain hard stops.
```

## Target Definition

9.5 means:

```text
zero unknowns
zero unregistered current files
zero broken critical links
boundary behavior is reviewable
document impact is calculable
new documents enter through intake
exceptions cannot hide ordinary backlog
history does not pollute active guidance
doctor remains read-only
growth does not erode the baseline
```

This target has two levels.

Vision target:

```text
AGENTS OS should eventually reach zero unknowns across all important local
knowledge.

For important documents, the system should be able to tell:
- where the document is
- who owns it
- whether it is current, draft, archived, superseded, or external scope
- what validates it
- what boundary it must not cross
- what evidence explains its latest accepted state
```

Current implementation target:

```text
Inside the declared governance scope listed by the Federated Document Registry,
doctor must be able to report:

unregistered=0
warn=0
fail=0

Files outside the declared governance scope are not ignored silently. They must
eventually be classified as one of:
- registered current document
- draft/example/template
- known_external_scope
- archive_note
- ignored_by_rule
- future_backlog
```

In plain terms: the final goal can stay ambitious. The current implementation
goal must stay checkable.

`ignored_by_rule` and `future_backlog` are not dumping grounds.

```text
ignored_by_rule must name the rule, path pattern, reason, and review trigger.
future_backlog must name the reason, owner or steward, review trigger, and
expected intake route.

Neither category may cover protected/P3 paths, secrets, private state, provider
raw responses, or ordinary current documents that should be registered.
```

## Non-Negotiable Boundaries

`docctl doctor` remains read-only.

The following must not be automated:

```text
reading or summarizing secrets
reading or summarizing state-private
reading provider raw responses
modifying .env / auth / provider / runtime configuration
modifying WORKSPACE_REGISTRY.yaml root authority structure
formal Memory registration
external writes
deploy / release / publish / tag / force push / merge
bulk move / delete / rename
automatic expansion of known_external_scope
automatic promotion from archive to canonical active document
```

`apply-fix` is deferred. Before it exists, only `plan-fix` may be discussed, and
it must be dry-run only.

## Stage 0: Freeze The Baseline And Read-Only Contract

Goal:

```text
Make the current healthy state reproducible and make the read-only doctor
contract explicit.
```

Minimum deliverables:

```text
baseline review
doctor read-only rule
P3 deny gate statement for future docctl commands
plan-fix/apply-fix deferred note
```

Acceptance:

```text
docctl doctor reproduces the current clean baseline
doctor performs no writes
protected/P3 paths remain blocked
```

### Stage 0 Baseline Freeze Note

Status: `stage_0_local_baseline_frozen`
Date: 2026-07-02

Current doctor baseline:

```text
docctl doctor PASS
registries=3
documents=121
scanned_files=168
known_external_scope=1
archived=50
unregistered=0
warn=0
fail=0
```

Read-only contract:

```text
docctl doctor is a read-only inspection command.
It may read declared federated registry inputs, run fixed local validators, and
report findings.
It must not modify files, create repair patches, change registries, change
runtime/provider/auth configuration, call providers, or write external systems.
```

P3 deny gate for future docctl commands:

```text
Future docctl commands must block protected/P3 paths before content reading.
Protected/P3 paths include state-private/, .env files, secrets, credentials,
tokens, cookies, private memory raw text, provider raw responses, auth/provider
configuration, runtime configuration, and external write targets.
```

Repair command boundary:

```text
plan-fix may only be designed as dry-run proposal output.
apply-fix remains deferred and is not authorized by Stage 0.
Any future write-capable docctl command must be separate from doctor and must
pass its own confirmation gate.
```

Stage 0 evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-0-baseline-freeze.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-0-baseline-freeze.review.md
```

## Stage 1: Registry Schema And Lifecycle Hardening

Goal:

```text
Make registry data stricter before scoring it.
```

Minimum deliverables:

```text
required field matrix
lifecycle state machine
allowed state transitions
known_external_scope requirements
archive_note requirements
schema version and migration rule
adversarial fixture set
```

Required lifecycle statuses:

```text
draft
review_needed
active
accepted
superseded
deprecated
archived
example
blocked
```

Required lifecycle shape:

```text
draft -> review_needed
draft -> active
draft -> accepted
draft -> archived
review_needed -> draft
review_needed -> active
review_needed -> accepted
active -> superseded
active -> deprecated
active -> archived
accepted -> superseded
accepted -> deprecated
accepted -> archived
deprecated -> superseded
deprecated -> archived
superseded -> archived
example -> example
blocked -> draft
blocked -> archived
```

Template documents do not need a separate status named `active template`.
Use:

```text
doc_type=template
status=active
```

Hard rules:

```text
example cannot auto-promote to active
archive cannot auto-promote to canonical
known_external_scope must include reason, owner or governing system, and review trigger
archive_note must include why archived, replacement, safe use, and review trigger
```

Migration rule:

```text
New stricter fields start as warn for existing baseline records.
After the current baseline is backfilled and reviewed, the same missing fields
may be promoted to fail.
New records created after the rule is adopted fail immediately if required
fields are missing.
```

Acceptance:

```text
invalid state transition is detected
duplicate id is detected
orphan reference is detected
broken critical link is detected
fake owner / missing review_by is detected
wrong archive / wrong external scope has a failing fixture
legacy missing exception metadata warns during migration
new missing exception metadata fails after rule adoption
```

## Stage 2: docctl intake

Goal:

```text
Make new-file entry explicit before files become backlog.
```

Command shape:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py intake <path>
```

Output categories:

```text
register
draft
example
template
known_external_scope
archive_note
ignored_by_rule
future_backlog
blocked
```

Category rules:

```text
ignored_by_rule means the file is intentionally out of document governance by a
clear local rule, such as generated cache, dependency output, or explicitly
excluded fixture material.

future_backlog means the file probably belongs to document governance later, but
is not safe or useful to register immediately. It must not be used for ordinary
current documents that can already be registered.
```

Rules:

```text
dry-run only
no registry write
no file move
no sensitive content output
P3/protected path -> blocked
ignored_by_rule requires rule + reason + review trigger
future_backlog requires reason + owner/steward + expected intake route
```

Acceptance:

```text
new safe document receives a route recommendation
new receipt/review receives a route recommendation
archive candidate receives archive_note recommendation
ignored-by-rule candidate explains the rule that excludes it
future backlog candidate explains why it is not registered now
protected target returns blocked
```

## Stage 3: Exception Governance For known/archive

Goal:

```text
Prevent known_external_scope and archive_notes from becoming hiding places.
```

Minimum deliverables:

```text
reason required
owner or governing system required
review trigger required
expiry or review cadence recommended
```

Acceptance:

```text
known_external_scope without reason fails
archive_note without safe use fails
archive_note without replacement or no-replacement reason fails
external scope outside allowed directory fails
```

## Stage 4: docctl impact

Goal:

```text
Make document change impact calculable.
```

Command shape:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py impact --changed <path> [...]
```

Impact sources:

```text
registry related paths
canonical_path / source_of_truth
review_by
archive_notes
known_external_scope
Markdown links
Golden Paths
receipt/review references
```

Acceptance:

```text
changed registry file lists affected registries
changed Golden Path lists related docs and receipts
changed archive note lists archived files and federated entries
changed receipt/review reports evidence impact
```

## Stage 5: docctl score

Goal:

```text
Turn 9.5 into a score only after rules are stable enough to score.
```

Score must include:

```text
versioned rubric
subscores
deduction reasons
repair route
red-line hard gates
warning severity split
```

Hard gates:

```text
P3 violation -> not eligible
doctor not read-only -> not eligible
unregistered > 0 -> not eligible for 9.5
fail > 0 -> not eligible for 9.5
blocking_warn > 0 -> not eligible for 9.5
advisory_warn > 0 -> allowed only with deduction and review route
```

Acceptance:

```text
score >= 95 only when doctor hard gates are clean and schema/lifecycle checks pass
score output explains every deduction
adversarial fixtures lower the score
```

## Stage 6: docctl trend

Goal:

```text
Make regression visible over time.
```

Minimum deliverables:

```text
local baseline snapshots
doctor summary history
score history
known/archive count history
intake coverage history
```

Acceptance:

```text
baseline drift is reported
known/archive growth is visible
4-week no-regression window can be checked locally
trend remains local read-only unless Jenn explicitly authorizes external write
```

## Deferred: apply-fix

`apply-fix` should not be built yet.

Before any apply command is considered, AGENTS OS must have:

```text
stable schema/lifecycle checks
stable intake
stable impact
stable score
stable trend
plan-fix dry-run output
explicit Jenn confirmation for write scope
```

Even then, apply-fix may only cover low-risk, non-P3, reversible registry
metadata edits.

## 9.5 Acceptance Checklist

```text
current doctor baseline: unregistered=0 warn=0 fail=0
future score hard gates: unregistered=0 blocking_warn=0 fail=0
score >= 95
all core documents have owner/status/source_of_truth/review_by/security_boundary
all known_external_scope entries have reason and review trigger
all archive_notes have why/replacement/safe use/review trigger
critical links have zero broken references
intake handles new document paths before registration
impact can list affected docs for changed paths
doctor remains read-only
write tools remain separate and dry-run first
P3 remains a hard stop
baseline has no uncontrolled regression over 4 weeks
```

## Full Implementation Plan Pack

This section turns the stage list into execution plans. It is still a draft. It
does not authorize active promotion, external writes, runtime/provider calls,
formal Memory registration, `WORKSPACE_REGISTRY.yaml` changes, or automatic
repair.

Global rules for every stage:

```text
1. Start with read-only inspection.
2. Keep doctor read-only.
3. Treat protected/P3 paths as blocked.
4. Add fixture tests for every new boundary rule.
5. Do not hide backlog inside known_external_scope, archive_note,
   ignored_by_rule, or future_backlog.
6. Finish each stage with validation, receipt, and review.
7. Keep write-capable commands separate from read-only commands.
8. Do not build apply-fix until every earlier stage is stable.
```

### Stage 0 Implementation Plan

Purpose:

```text
Freeze the current clean baseline and make the read-only contract explicit
before adding stricter rules.
```

Inputs:

```text
control-plane/registry/docctl.py doctor
control-plane/registry/drafts/federated-document-registry.v0.1.example.yaml
current baseline receipt/review
validator-boundary-review-checklist
```

Steps:

```text
1. Record the current doctor summary.
2. Confirm doctor has no write paths.
3. Confirm future docctl commands inherit protected/P3 path blocking.
4. Document that plan-fix is dry-run only and apply-fix is deferred.
5. Add or update tests only if the read-only contract is not already covered.
```

Deliverables:

```text
baseline freeze note
read-only contract note
P3 deny gate statement for future docctl commands
receipt/review for the freeze
```

Validation:

```text
validate-document-registry
validate-federated-document-registry
test-docctl-doctor
docctl doctor
```

Done when:

```text
doctor reproduces the clean baseline
doctor performs no writes
protected/P3 fixtures still fail safely
```

### Stage 1 Implementation Plan

Purpose:

```text
Make registry schema and lifecycle stricter before scoring.
```

Inputs:

```text
current document registry status set
current validator behavior
known_external_scope and archive_note examples
existing adversarial fixtures
```

Steps:

```text
1. Define the field matrix by doc_type and status.
2. Define the lifecycle state machine using the current allowed statuses.
3. Define transition rules and blocked transitions.
4. Define known_external_scope required fields.
5. Define archive_note required fields.
6. Add migration mode:
   - existing baseline gaps start as warn
   - new records fail if required fields are missing
   - reviewed backfill can promote legacy gaps from warn to fail
7. Add adversarial fixtures before relying on the stricter checks.
8. Update validator messages so the repair path is clear.
```

Deliverables:

```text
schema/lifecycle rule section or draft
validator updates for field matrix and lifecycle
fixtures for valid transitions and invalid transitions
fixtures for known_external_scope and archive_note metadata
receipt/review for Stage 1
```

Validation:

```text
validate-document-registry
test-document-registry-validator
validate-federated-document-registry
test-federated-document-registry-validator
docctl doctor
```

Done when:

```text
current baseline still passes
invalid transitions are caught
new missing exception metadata fails
legacy missing exception metadata warns until backfilled
```

### Stage 2 Implementation Plan

Purpose:

```text
Give new files a dry-run intake route before they become hidden backlog.
```

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py intake <path>
```

Steps:

```text
1. Add an intake subcommand that reads one target path.
2. Preflight the target with the shared path-boundary helper.
3. Block protected/P3 paths before content reading.
4. Classify the path into one route:
   - register
   - draft
   - example
   - template
   - known_external_scope
   - archive_note
   - ignored_by_rule
   - future_backlog
   - blocked
5. Return a dry-run recommendation only.
6. Print no sensitive contents.
7. Provide JSON output for testability.
```

Deliverables:

```text
docctl intake dry-run command
classification rules
JSON output shape
fixtures for safe file, receipt/review, archive candidate, ignored_by_rule,
future_backlog, protected path, outside path, and symlink cases
receipt/review for Stage 2
```

Validation:

```text
test-docctl-doctor or a new docctl intake test file
docctl intake fixture commands
validate-document-registry
docctl doctor
```

Done when:

```text
new safe documents receive a route recommendation
protected/P3 paths return blocked
ignored_by_rule and future_backlog explain why they are not registered now
no registry file is modified by intake
```

### Stage 3 Implementation Plan

Purpose:

```text
Make exceptions reviewable so they cannot hide ordinary backlog.
```

Steps:

```text
1. Define required fields for known_external_scope:
   - path
   - classification
   - reason
   - owner or governing_system
   - review_trigger
   - optional review cadence or expiry
2. Define required fields for archive_note:
   - path
   - classification
   - why_archived
   - replacement or no_replacement_reason
   - safe_use
   - review_trigger
3. Backfill current known/archive examples under migration mode.
4. Add validator checks after the backfill path is clear.
5. Add fixtures that prove bad exceptions fail.
```

Deliverables:

```text
exception metadata rules
backfilled known_external_scope entry or explicit migration note
backfilled archive_note metadata or explicit migration note
validator fixtures for missing reason, missing owner/governing system, missing
review trigger, missing safe_use, and invalid outside/protected paths
receipt/review for Stage 3
```

Validation:

```text
validate-federated-document-registry
test-federated-document-registry-validator
docctl doctor
```

Done when:

```text
exceptions are specific and reviewable
ordinary current documents cannot be hidden as exceptions
protected/P3 exception paths fail
```

### Stage 4 Implementation Plan

Purpose:

```text
Show what a document change affects before the change is treated as isolated.
```

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py impact --changed <path> [...]
```

Steps:

```text
1. Read the federated registry.
2. Build a local in-memory graph from registered paths:
   - registry_path
   - canonical_path
   - source_of_truth
   - review_by
   - related
   - archive_notes
   - known_external_scope
   - receipt/review references
3. For each changed path, list direct and likely affected documents.
4. Keep Markdown link scanning narrow and safe.
5. Return text and JSON output.
6. Do not write impact results automatically.
```

Deliverables:

```text
docctl impact dry-run command
impact graph construction
fixtures for registry change, Golden Path change, archive note change,
receipt/review change, missing path, protected path, and outside path
receipt/review for Stage 4
```

Validation:

```text
new docctl impact tests
validate-document-registry
validate-federated-document-registry
docctl doctor
```

Done when:

```text
changed paths report affected registries and documents
impact output is explainable
protected/P3 paths remain blocked
no impact command writes files
```

### Stage 5 Implementation Plan

Purpose:

```text
Turn governance health into a score only after the rules are strong enough.
```

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py score
```

Steps:

```text
1. Define a versioned rubric.
2. Separate hard gates from score deductions.
3. Map validator results into:
   - fail
   - blocking_warn
   - advisory_warn
   - pass
4. Require hard gates to be clean before a 95+ score is possible.
5. Explain every deduction.
6. Include repair routes without applying repairs.
7. Add adversarial fixtures that lower or block the score.
```

Deliverables:

```text
score rubric
docctl score command
JSON score output
fixtures for clean baseline, fail, blocking_warn, advisory_warn, and gamed
metadata
receipt/review for Stage 5
```

Validation:

```text
new docctl score tests
validate-document-registry
validate-federated-document-registry
docctl doctor
```

Done when:

```text
clean baseline can score high
hard gate failures block 9.5
advisory warnings reduce score but do not hide facts
score explains the reason for every deduction
```

### Stage 6 Implementation Plan

Purpose:

```text
Make drift visible over time without turning trend into an unsafe writer.
```

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py trend
```

Steps:

```text
1. Define a local snapshot format for doctor and score summaries.
2. Keep trend read-only: trend reads existing local snapshots only.
3. Treat snapshot creation as a separate yellow-zone local write that needs a
   receipt/review.
4. Compare latest baseline against previous snapshots.
5. Report growth in:
   - documents
   - known_external_scope
   - archive_notes
   - unregistered files
   - fail/blocking_warn/advisory_warn
6. Add a four-week no-regression view once enough snapshots exist.
```

Deliverables:

```text
snapshot format draft
docctl trend read-only command
fixtures for no snapshot, stable history, regression, known/archive growth, and
missing/corrupt snapshot
receipt/review for Stage 6
```

Validation:

```text
new docctl trend tests
docctl doctor
docctl score after Stage 5 exists
validate-document-registry
```

Done when:

```text
trend can report whether the baseline is improving or degrading
trend does not create or modify snapshots
snapshot writing remains separate and reviewable
```

### Stage 1-6 Local Implementation Closeout

Status: `stage_1_to_6_local_implementation_complete`
Date: 2026-07-02

This closeout records local implementation progress only. It does not promote
this draft plan to active authority and does not authorize `apply-fix`, service
start, executor runs, provider calls, external writes, formal Memory writes, or
`WORKSPACE_REGISTRY.yaml` authority changes.

Implemented local capabilities:

```text
Stage 1: strict field matrix and lifecycle transition validation
Stage 2: read-only docctl intake dry-run routing
Stage 3: known_external_scope and archive_note exception governance
Stage 4: read-only docctl impact view
Stage 5: read-only docctl score with 9.5 hard gates
Stage 6: read-only docctl trend over existing local snapshots
```

Current 9.5 local check:

```text
docctl score PASS
score=100
eligible_95=True
blocking_warn=0
advisory_warn=0
hard_gates=0
```

Current governance health:

```text
validate-document-registry PASS checked_documents=99 pass=99 warn=0 fail=0
validate-federated-document-registry PASS checked_registries=3 pass=3 warn=0 fail=0
docctl doctor PASS registries=3 documents=141 scanned_files=188 known_external_scope=1 archived=50 unregistered=0 warn=0 fail=0
```

Stage 1-6 evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-1-schema-lifecycle.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-1-schema-lifecycle.review.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-2-docctl-intake.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-2-docctl-intake.review.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-3-exception-governance.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-3-exception-governance.review.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-4-docctl-impact.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-4-docctl-impact.review.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-5-docctl-score.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-5-docctl-score.review.md
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-stage-6-docctl-trend.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-stage-6-docctl-trend.review.md
```

### Plan-fix Dry-run Implementation Note

Status: `plan_fix_dry_run_v0.1_local_implemented`
Date: 2026-07-02

`docctl plan-fix` now exists as dry-run proposal output only:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py plan-fix --json
```

It may report proposed repair categories, but it must not perform writes:

```text
write_performed=false
patch_created=false
snapshot_write_performed=false
registry_write_performed=false
external_write_performed=false
apply_fix_implemented=false
```

`apply-fix` remains out of scope and is not implemented.

Implementation evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-plan-fix-dry-run-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-plan-fix-dry-run-v0.1.review.md
```

### Snapshot Writer Implementation Note

Status: `snapshot_writer_v0.1_local_implemented`
Date: 2026-07-02

`docctl snapshot` now exists as a local summary snapshot writer for trend
history:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py snapshot
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py snapshot --json
```

Snapshot writes are limited to:

```text
control-plane/registry/reports/docctl-snapshots/
```

Snapshot payloads must stay summary-only:

```text
raw_registry_content_included=false
raw_logs_included=false
full_document_text_included=false
secrets_included=false
provider_raw_response_included=false
```

`apply-fix` remains out of scope and is not implemented.

Implementation evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-snapshot-writer-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-snapshot-writer-v0.1.review.md
```

### Status Pulse Implementation Note

Status: `status_pulse_v0.1_local_implemented`
Date: 2026-07-02

`docctl status` now exists as a read-only pulse over the current document
governance body:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py status --json
```

It summarizes:

```text
doctor summary
score / eligible_95
trend / latest snapshot path
plan-fix proposal status
next recommended action
boundary flags
```

It must not perform writes:

```text
write_performed=false
snapshot_write_performed=false
registry_write_performed=false
external_write_performed=false
snapshot_writer_called=false
apply_fix_implemented=false
```

Implementation evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-status-pulse-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-status-pulse-v0.1.review.md
```

### Operations Runbook Implementation Note

Status: `docctl_operations_runbook_v0.1_local_implemented`
Date: 2026-07-02

The local `docctl` operations runbook now exists:

```text
control-plane/registry/runbooks/docctl-operations-runbook-v0.1.md
```

It turns the current document-governance body into an operating path:

```text
doctor: read-only declared-scope health check
status: read-only governance pulse
score: read-only 9.5 eligibility check
trend: read-only local snapshot comparison
snapshot: local summary write only after explicit confirmation
plan-fix: dry-run repair proposal only
apply-fix: preview-only read-only output exists; repair execution is not implemented or authorized
```

It does not authorize repair writes, snapshot writes, service starts, executor
runs, provider calls, formal Memory registration, external writes, or P3
bypass.

Implementation evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-docctl-operations-runbook-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-docctl-operations-runbook-v0.1.review.md
```

### apply-fix Preview-Only Implementation Note

Status: `docctl_apply_fix_preview_only_v0.1_local_implemented`
Date: 2026-07-02

`docctl apply-fix --preview` now exists as a read-only preview over one
`plan-fix` proposal:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview PF-0001
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/docctl.py apply-fix --preview PF-0001 --json
```

The preview keeps the execution boundary explicit:

```text
preview_only=true
write_performed=false
patch_created=false
snapshot_write_performed=false
execution_authorized=false
registry_write_performed=false
external_write_performed=false
provider_call_performed=false
```

It does not implement real repair execution, create repair patches, write
snapshots, write registries as preview behavior, start services, run executors,
call providers, or register formal Memory.

Implementation evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-document-governance-9.5-apply-fix-preview-only-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-document-governance-9.5-apply-fix-preview-only-v0.1.review.md
```

### ColaMeta Executor Preflight Gate Implementation Note

Status: `colameta_executor_preflight_gate_v0.1_local_implemented`
Date: 2026-07-02

`colameta-executor-preflight.py` now exists as a read-only, summary-only
preflight gate before any future ColaMeta executor run:

```text
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/colameta-executor-preflight.py
PYTHONDONTWRITEBYTECODE=1 python3 control-plane/registry/colameta-executor-preflight.py --json
```

The gate keeps the execution boundary explicit:

```text
executor_authorized=false
service_start_authorized=false
provider_call_authorized=false
memory_write_authorized=false
external_write_authorized=false
```

It checks only local readiness summaries: ColaMeta PlanLoader/Linter status,
prompt file presence, `docctl status`, and `.colameta/memory.md` byte count. It
does not start services, run executors, call providers, write Memory, read
`state-private/`, print raw plan content, print prompt bodies, print raw logs,
or modify `.colameta/plan.json` / `.colameta/state.json`.

Implementation evidence:

```text
control-plane/registry/receipts/2026-07-02-yellow-agents-os-colameta-executor-preflight-gate-v0.1.md
control-plane/registry/reviews/2026-07-02-yellow-agents-os-colameta-executor-preflight-gate-v0.1.review.md
```

### Deferred Write Plan

Write-capable `apply-fix` remains out of scope.

Before any write-capable repair tool exists:

```text
1. Stage 1 through Stage 6 must be stable.
2. plan-fix must exist as dry-run only.
3. Jenn must confirm the exact local write scope.
4. Protected/P3 paths must remain blocked.
5. The tool may only perform low-risk, reversible registry metadata edits.
6. Every write must leave receipt/review evidence.
```

## Recommended Immediate Next Step

After this plan pack is reviewed, start with Stage 1:

```text
Registry Schema And Lifecycle Hardening
```

This should produce a small schema/lifecycle plan and adversarial fixture list
before any scoring tool is implemented.
