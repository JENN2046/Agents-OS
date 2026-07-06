# Validation Execution Authorization Template

Status: template only. A blank template is not approval.

Purpose:
- Capture the information needed before one exact validation-script run can be
  explicitly approved.
- Keep validation execution separate from script placement, template creation,
  and migration planning.

Authority boundary:
- This template does not authorize script execution by itself.
- A filled template does not authorize script execution by itself.
- Execution requires separate explicit human approval for the exact run named in
  the filled template.
- Any later approval is limited to one exact scoped run.
- This template does not authorize executable-bit changes, remote actions,
  branch movement, release, deploy, network actions, destructive actions, secret
  access, private-state access, log harvesting, cache harvesting, or runtime
  actions.

## Fill Before Approval

| Field | Required value |
| --- | --- |
| Validation purpose | `<why this validation is needed>` |
| Proposed script path | `<migrated validation script path>` |
| Proposed working directory | `<directory where the validation would run>` |
| Scope | `<files, directories, or asset family to check>` |
| Expected output | `<counts only, redacted summary, or full paths>` |
| Full-path disclosure | `<no by default; yes only if explicitly approved>` |
| Failure handling | `<whether failures stop the calling task>` |
| Receipt location | `<where the execution receipt would be written>` |
| Stop conditions | `<conditions that cancel the run>` |

## Required Human Approval

Before any validation script runs, the human approval must name:

- the exact script path
- the exact working directory
- the exact scope
- the expected output handling
- whether full paths may be disclosed
- the receipt location

Do not treat general phrases such as "continue", "go ahead", or "run checks" as
approval for validation-script execution unless the exact run details above are
also explicit.

## Default Output Rules

- Prefer counts or redacted summaries.
- Do not print secret values.
- Do not print file contents from secret-like files.
- Do not disclose full paths unless explicitly approved.
- Do not copy raw scanner output into receipts or reports when a summary is
  enough.

## Stop Conditions

Cancel the proposed run if:

- the script path differs from the approved path
- the working directory differs from the approved directory
- the scope is broader than the approved scope
- the requested output would reveal full paths without approval
- the script would require executable-bit changes
- the script or wrapper would perform remote, branch, release, deploy, network,
  destructive, copy, move, or sync actions
- the run would read private state, logs, cache, runtime output, or active local
  configuration outside the approved scope

## Receipt Requirements

If an approved validation run later happens, its receipt should record:

- exact human authorization wording
- script path
- working directory
- approved scope
- output handling
- summarized result
- failures or warnings
- validation not run
- remaining risks

The receipt should avoid raw full-path output unless full-path disclosure was
explicitly approved.
