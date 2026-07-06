# Review, Receipt, And Validation Plan

Date: 2026-06-30
Status: evidence_plan_v0.1_adjusted_2026-06-30

## 0. Purpose

This file defines how future AGENTS OS local landing work should prove itself.

It does not run validation.

## 1. Receipt Levels

Use four levels:

```text
R0 note
  For read-only findings and planning notes.

R1 report receipt
  For local planning/report documents.

R2 patch receipt
  For local documentation or contract patches.

R3 execution receipt
  For validation runs, runtime probes, code changes, or any action with side
  effects.
```

## 2. Minimum Receipt Fields

```text
receipt_id:
date:
agent:
authorization_scope:
permission_level:
task:
files_created:
files_changed:
files_intentionally_skipped:
notion_writes:
memory_writes:
private_state_access:
commands_run:
validation_run:
result:
remaining_risk:
rollback_path:
next_review:
```

## 3. Review Gates

### Nobao Review

Checks:

```text
Does the work preserve AGENTS OS as home/community?
Does it avoid reducing Agent to tool?
Does it avoid over-structuring?
Does it preserve Jenn as root authority but not only center?
```

### Memory Agent Review

Checks:

```text
Is source clear?
Is status official/proposed/self_record/pending_review/deprecated/superseded?
Does it avoid fake Memory write?
Does it avoid private memory exposure?
```

### Review Agent Review

Checks:

```text
Is permission level correct?
Are stop conditions clear?
Are secrets/private state avoided?
Are side effects authorized?
Is receipt sufficient?
Is validation overclaimed?
```

### Project Agent Review

Checks:

```text
Does this serve current AGENTS OS local landing route?
Is the next step small enough?
Are dependencies clear?
Is the task count controlled?
```

## 4. Validation Planning

Candidate scripts exist:

```text
ops/validation/validate-workspace.sh
ops/validation/validate-extension-manifests.sh
ops/validation/validate-no-secrets.sh
```

They are not authorized by existence.

Before any future validation run, require:

```text
exact command:
working_directory:
scope:
expected_output:
redaction_policy:
failure_behavior:
receipt_location:
allowed_to_print_paths: yes/no
allowed_to_print_values: no
```

## 4A. Lightweight And Multi-Project Evidence Mode

Active local decisions:

```text
ops/migration/decisions/lightweight-governance-mode-2026-06-29.md
ops/migration/decisions/multi-project-governance-mode-2026-06-29.md
```

Future low-risk local gates should prefer:

```text
Gate Card
Run Receipt
Phase Rollup
```

Future multi-project work should prefer:

```text
global project index
project-local state card
project-local gate receipt
global risk summary only when cross-project risk exists
```

Do not copy every project receipt into the global layer. Do not use old heavy
receipt volume as proof that a current project state is already legible.

## 5. Validation Claims

Allowed claim examples:

```text
file exists
markdown headings present
schema JSON parsed
targeted test passed
typecheck passed
workspace validator ran with redacted output
```

Forbidden overclaims:

```text
validated AGENTS OS
safe for runtime
no secrets anywhere
production safe
VCPToolBox ready
Cockpit implemented
Memory registered
```

unless the exact evidence truly proves the claim.

## 6. Closeout Template

```text
closeout_id:
task_id:
objective:
requirements:
evidence:
validation:
not_validated:
risks:
decision: complete / continue / blocked
next:
```

## 7. First Future Review Package

After this plan package, the first future review package should likely be:

```text
07-local-reality-adjustment-2026-06-30.md
global project index plan
project state-card candidates
registry/migration-map reconciliation note
Receipt contract draft
TaskEnvelope contract draft
CapabilityCard contract draft
```

Review questions:

```text
Do these contracts preserve Notion intent?
Do they fit local directory principles?
Do they avoid private state?
Do they give codex-router something useful to align with?
```
