# Multi-Project Governance Mode - 2026-06-29

Status: active decision.

Decision:
`MULTI_PROJECT_GOVERNANCE_MODE_ADOPTED_GLOBAL_INDEX_PROJECT_CARDS`.

This decision changes AGENTS OS governance from a single global receipt ledger
into a multi-project operating model. Global governance should not carry every
project's detailed receipts. Each project owns its local state card; the global
layer keeps only an index and risk summary.

## Why This Changes

The earlier migration phases used a single global chain of plans, evidence, and
receipts. That was useful while stabilizing the control plane, but it does not
scale once multiple projects are active at the same time.

When many projects move independently, a branch change or validation result in
one project must not be mistaken for the state of the whole AGENTS OS
workspace.

## New Governance Shape

Use three layers:

| Layer | Owns | Does Not Own |
| --- | --- | --- |
| Global governance | Workspace-wide safety rules, escalation rules, project index, cross-project risk summary. | Per-project detailed receipts, every branch/hash/test result. |
| Project governance | Current branch, current goal, selected source hashes, latest validation, open risks, next gate. | Other projects' state. |
| Gate records | Small local run receipts for a specific project/gate. | Global workspace truth. |

## Global Layer

The global layer should answer:

- what projects exist
- which projects are active, paused, archived, or reference-only
- what each active project is generally doing
- which projects currently have unresolved high-risk gates
- where to find each project's state card

The global layer should not store every detailed receipt from every project.

## Project State Card

Each active project should maintain one compact state card, preferably at one of:

```text
<project>/AGENTS_OS_STATE.md
<project>/ops/STATE.md
<project>/docs/current/CURRENT_STATE.md
```

The state card should record:

- project name
- authority path
- current branch or non-git status
- current goal
- latest meaningful validation
- open risks
- next gate
- whether lightweight or escalated governance applies

The card should be short enough to read quickly.

## Global Project Index

The global workspace may maintain a lightweight index such as:

```text
ops/migration/project-index.md
```

The index should include only:

- project path
- status
- state card path
- current risk level
- last reviewed date
- next action headline

It should link to project-local state rather than copying all details.

## Receipt Ownership

Going forward:

- project-specific receipts should live near the project when possible
- global receipts are reserved for workspace-wide decisions or cross-project
  gates
- old global receipts remain valid historical migration evidence
- new low-risk project gates should follow lightweight governance mode

## Escalation

Escalate from project-local governance to global governance only when:

- a decision affects multiple projects
- a shared rule, registry, template, or provider changes
- a project needs cross-project dependency or ownership changes
- a gate touches credentials, network, deploy, release, publishing, remote
  agents, or workspace-wide mutation
- a project state card reports unresolved high risk

## Boundary

This decision does not remove safety. It reduces coupling.

The global layer remains responsible for safety policy and cross-project
visibility. Individual projects remain responsible for their own working state
and evidence.

## Relationship To Lightweight Governance

This decision depends on:

```text
ops/migration/decisions/lightweight-governance-mode-2026-06-29.md
```

Lightweight governance defines how small gates are recorded. Multi-project
governance defines where those records live and how they roll up.

## Result

Future AGENTS OS work defaults to project-local state cards plus a global
project index and risk summary.

Marker:

```text
MULTI_PROJECT_GOVERNANCE_MODE_ADOPTED_GLOBAL_INDEX_PROJECT_CARDS
```
