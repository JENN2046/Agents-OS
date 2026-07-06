# AGENTS OS Workspace Manifest

Status: active orientation
Date: 2026-07-06
Owner: Jenn
Agent steward: Nobao

## Canonical Root

```text
/home/jenn/AGENTS_OS_Workspace
```

Linux paths are canonical for execution, validation, Git, and local runtime
work. Windows paths are reference or transfer surfaces unless Jenn explicitly
chooses otherwise.

## Directory Map

```text
control-plane/  protocols, contracts, schemas, validators, policies, task envelopes
governance/     safety, authorization, automation rules, hard gates
execution/      future harnesses, workers, provider adapters, sandbox launchers
runtime/        upstream-trackable runtime cores; high caution
extensions/     Jenn-owned external capabilities
domains/        business/domain systems with real-world boundaries
labs/           drafts, experiments, working syntheses
memory/         memory system code/protocols/tests; no raw private memory reads
ops/            validation, reports, receipts, migration notes, maintenance
archive/        historical read-only reference by default
state-private/  denied by default
```

## Safe Entry Files

```text
AGENTS.md
CURRENT_STATE.md
README.md
WORKSPACE_MANIFEST.md
governance/automation/AGENTS_OS_AUTOMATION_RULEBOOK.md
governance/SECURITY_BOUNDARIES.md
```

## Denied By Default

```text
state-private/
active .env / config.env values
secrets / tokens / cookies / credentials
private raw memory
provider raw response
raw logs that may contain sensitive content
```

## Runtime Note

`runtime/VCPToolBox` is a private local runtime body under separate boundary
review. Do not treat it as ready for provider/plugin/autonomous use without the
current VCPToolBox first-use posture checks.

## Git Outbound Boundary

The root Git repository is private-local by default. Its local history has
contained private Notion page URLs and working synthesis material. External
push, remote publication, mirror, backup-to-hosted-Git, or PR creation from this
root repo requires a separate private-history review or history-scrub gate with
Jenn's current authorization.
