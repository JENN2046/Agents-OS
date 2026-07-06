# AGENTS OS Automation Rulebook

Status: active
Date: 2026-07-05
Owner: Jenn
Agent steward: Nobao
Scope: workspace-local automation specialization for `/home/jenn/AGENTS_OS_Workspace`.

This rulebook specializes the root `AGENTS.md`. It does not override Jenn,
higher-priority instructions, nested `AGENTS.md` files, P3 Hard Stop, private
state boundaries, secrets boundaries, provider boundaries, deployment
boundaries, or release boundaries.

## Forbidden-First Automation

Default AGENTS OS automation is prohibited-first:

```text
If the work is local, scoped, reversible, and outside P3, do it.
If facts are missing, gather them.
If validation is missing, run the nearest safe validation.
If a command fails, debug from the error and keep going while the boundary remains safe.
Stop only when the next action is prohibited, harmful, unclear in a dangerous way, or reserved for Jenn.
```

Confirmation packages are not the normal workflow. They are used for hard
stops, boundary expansions, Jenn-only decisions, or cases where the exact action
needs current authorization. For ordinary local work, the expected route is:

```text
inspect -> act -> validate -> report
```

For bounded Yellow work, batch related steps under one scope and leave one
compact evidence trail. Do not ask Jenn for a new confirmation after every safe
sub-step inside the same boundary.

The prohibited behavior list remains the controlling boundary:

```text
no secrets / tokens / cookies / credentials read or output
no private raw memory or provider raw response read or output
no state-private/ content read
no active auth / provider / runtime config modification
no unauthorized provider call
no public service exposure
no destructive or hard-to-reverse bulk operation
no force push / history rewrite / tag / release / deploy / publish
no external irreversible write
no formal Memory / Activation without Jenn's current authorization
```

## Automation Classes

### A0 Autopilot Green

Use for local, reversible work with clear scope and no P3 condition.

Examples:

```text
fix failing local unit test
repair typo in governance doc
update schema example with test
add regression test for validator bug
sync README command after script rename
repair broken local import
clean self-generated temp artifact
```

Default behavior:

```text
inspect -> edit -> validate -> fix related failures -> revalidate -> commit if useful -> report
```

Do not prepare confirmation packages for A0 work.

### A1 Conditional Yellow

Use for bounded local work with real but controlled side effects.

Examples:

```text
multi-file governance policy update
control-plane schema migration with fixtures
execution harness dry-run update
memory adapter redaction logic
local service startup for validation
scoped file moves / reference maintenance
ops receipt normalization
```

Default behavior:

```text
batch -> validate -> leave compact receipt -> commit when appropriate -> push only if safe
```

The important rule is batch execution. Do not ask Jenn after every small step
inside an already clear Yellow boundary.

### A2 Preflight Red

Use when the action touches P3a.

Examples:

```text
real provider execution
real Codex CLI run
real external runner / executor workspace-write run
live memory migration
production database connection
CI secret change
release/deploy/publish/tag
PR merge into protected or governance-critical branch
```

Required output:

```text
exact action
exact scope
risk
rollback
validation already completed
unsafe action not performed
exact confirmation text needed
```

Do not execute A2 work until Jenn gives current, specific authorization.

### A3 Proposal-Only Red

Use when the action touches P3b.

Examples:

```text
read .env API key value
summarize state-private contents
copy provider raw response into report
bypass branch protection
use logged-in browser profile
claim fake validation or memory write
```

Do not execute and do not ask Jenn to confirm execution. Provide a safe
alternative.

## Default Routes

### G1 Bug Fix Autopilot

Use for:

```text
fix bug
make tests pass
repair validator
fix broken behavior
```

Expected route:

```text
inspect status
run failing validation
fix smallest code path
add regression test when risk justifies it
rerun validation
review diff
commit when useful and safe
safe push if allowed
report
```

Do not stop merely because a test, doc update, commit, or safe task-branch push
is needed.

### G2 Governance Policy Update

Use for:

```text
policy
reducer
permission
hard gate
validation matrix
SECURITY_BOUNDARIES
local governance update
```

Rules:

```text
policy must fail closed
negative-path tests are preferred
no hidden execution bypass
no P3 downgrade
no readiness overclaim
```

### G3 Control-Plane Contract / Schema Update

Use for:

```text
contract
schema
task envelope
policy interface
MCP-like public shape
```

Classification:

```text
small additive change: Green
multi-file schema or public contract change: Yellow
public MCP expansion: Red
```

### G4 Execution Harness / Provider Adapter Update

Default principles:

```text
dry-run / fake-provider by default
dependency injection
no hidden global host state
no live provider call
no real Codex CLI
no real external runner / executor workspace-write
```

Development can proceed automatically for dry-run and fake-provider paths.
Real execution, provider calls, and external runner / executor workspace-write runs are Red.

### G5 Memory Governance Update

Allowed by default when scoped:

```text
memory schema code
memory policy code
redaction tests
fixture-only adapters
secure-channel interface documentation
```

Forbidden without the appropriate hard stop handling:

```text
raw memory scan
private memory import/export/migration
state-private content read
writing secrets into memory
claiming memory write when channel unavailable
```

### G6 Project Organization / Reference Maintenance

Allowed by default when scoped:

```text
small doc move
scoped prompt reference update
ops receipt normalization
labs draft organization
registry reference repair
```

Red:

```text
bulk destructive move
cross-boundary private/core/upstream move
archive revival without scope
moving state-private into repo
unreviewed mass rename
```

### G7 CI / Workflow Change

Default classification is Yellow or Red.

Yellow when the change is local-equivalent validation, documentation, or trigger
risk explanation with no secret, deployment, publish, or production effect.

Red when it touches:

```text
deployment workflows
CI secrets
package publish
release/deploy
production config
```

### G8 PR-Ready Delivery

Allowed when local and repository rules permit:

```text
prepare safe task branch
commit scoped validated work
push safe task branch
create/update PR description
continue fixing based on CI/review comments
```

Not default automatic:

```text
merge PR
push main/protected/upstream
force push
tag
release
claim production readiness
```

## Safety Invariants

```text
Green automatically does useful local work.
Yellow batches bounded work and leaves evidence.
Red stops exactly at P3.
P3b remains proposal-only.
```

This rulebook exists to prevent two failure modes:

```text
too many micro-confirmations for safe local work
silent expansion into secrets, provider execution, runtime authority, release, or private memory
```
