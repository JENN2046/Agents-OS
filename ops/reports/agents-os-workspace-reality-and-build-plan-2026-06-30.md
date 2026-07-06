# AGENTS OS Workspace Reality And Build Plan

Date: 2026-06-30
Author: Nobao / Codex
Scope: Notion read + local read-only survey + one authorized local planning document
Status: planning_report

## 0. Boundary

This document is the only local write in this task.

No Notion page was created or updated. No Memory entry was written. No validation
script was run. No runtime, extension, domain, private state, archive, git branch,
remote, provider, secret, or config was modified.

Denied or avoided in this pass:

```text
state-private/
archive/ as execution root
.env / .env.*
config.env
secret / token / cookie / credential material
provider/auth configuration
VCPToolBox real probe
VCP plugin/provider execution
validation script execution
git push / tag / release / deploy
```

## 1. Notion Reading Summary

Primary source:

- AGENTS OS | Life Core v0.1:
  [private Notion page URL redacted in Git copy]

Active directory sources read in this pass included:

- Root: life manifestation, house rules, memory rules, formal memory index,
  dual-foundation positioning.
- Governance: agent onboarding, room maintenance, permission v0.2, Presence
  Permission, sensing levels S0-S6, Activation Package, Activation example.
- Interface and Growth: Cockpit, Cockpit cards, VCP thought-cluster access,
  Agent growth mechanism.
- Loop: first loop design, Loop 001 record, Loop 001 receipt.
- Runtime: VCPToolBox position, access boundary, read-only experiment design,
  A0 target adjustment, VCPChat review/position, VCP Agent runtime model,
  AGENTS OS x VCP reuse matrix.
- Members: identity/room templates, Nobao identity and room, Memory Agent room,
  Review Agent room, Project Agent room, first resident-agent record,
  Agent-to-Agent relation format and life protocol.
- Vision and safety holding: long-term cross-device vision and mother-page
  child-page holding zone.

Core Notion conclusions:

```text
AGENTS OS is first a home and community, not a tool platform.
VCPToolBox is the engineering body and runtime foundation, not the life
foundation.
VCPChat is the visible interface layer, not the home itself.
Agent growth = memory absorbed + thought clusters adjusted + behavior policy
verified.
Loop 001 is already closed and proves the small evidence loop works.
Next runtime direction is A0/read-only target and object-list preparation, not
real probe.
```

## 2. Workspace Reality Report

Canonical root:

```text
/home/jenn/AGENTS_OS_Workspace
```

The Windows/A-drive root is reference/archive storage, not canonical execution
root.

Observed top-level structure:

```text
control-plane/   present; contracts, registry, runbooks, prompts, templates
governance/      present; SECURITY_BOUNDARIES.md and codex-router repo
execution/       scaffold directories; currently empty
runtime/         only README.md; VCPToolBox not present locally
extensions/      vcp-toolbox-jenn directory exists but is empty
domains/         Photo_Studio_OS directory exists but is empty
labs/            agent-image-lab directory exists but is empty
memory/          codex-memory directory exists but is empty
ops/             migration plans, receipts, inventory, validation candidates
state-private/   exists; denied by default; not inspected
archive/         exists; historical read-only reference by default
```

Git reality:

```text
workspace root: not a git repository
governance/codex-router: git repository
codex-router branch: main
codex-router status: aligned with origin/main, no short-status changes reported
codex-router latest commit: f04b369 Add runtime governance operator actions
```

PowerShell Git over the WSL UNC path reported `dubious ownership`; WSL Git was
used for read-only status instead. No global git config was changed.

Important local facts:

```text
control-plane/registry/WORKSPACE_REGISTRY.yaml is active authority registry.
Registry URLs are metadata only and do not authorize fetch, clone, push, release,
deploy, validation execution, or permission expansion.
ops/validation scripts are reviewed candidates only; their existence is not
execution authorization.
AGENTS_OS_READING_NOTES_DRAFT.md already contains extensive prior reading notes.
ops/reports/ was empty before this planning report.
```

## 3. Gap Analysis

1. Vision and governance are richer than the local engineering body.

The Notion system has life core, permissions, presence, sensing, resident-agent
rooms, Loop 001, and runtime access strategy. Locally, most target runtime,
extension, domain, lab, memory, and execution directories are placeholders.

2. The control plane exists, but the AGENTS OS contracts are still thin.

The registry, runbooks, templates, and extension manifest schema exist. Missing
or not yet materialized are local first-class schemas for TaskEnvelope, Receipt,
Capability Card, Agent Room, Presence Permission, Growth Event, Behavior Policy,
and Growth Verification.

3. `codex-router` is the strongest local codebase.

It already contains packages for routing, risk, task graph, validation, provider
execution, controlled read-only behavior, and governance observations. It should
be treated as the current engineering spine of the governance layer, but not as
the whole AGENTS OS.

4. Runtime A0 work has not yet locally started.

Notion says the next allowed direction is target/object-list preparation before
Probe Plan. Locally `runtime/VCPToolBox` is absent, and registry remote URLs do
not authorize cloning or fetching.

5. The first resident agents exist in Notion, not as local operating artifacts.

Nobao, Memory Agent, Review Agent, and Project Agent have rooms and duties in
Notion. Locally, their roles are represented indirectly through AGENTS.md,
reading notes, runbooks, and conventions, not through stable local agent cards,
schemas, or room mirrors.

6. Validation exists as design, not as a current execution lane.

`ops/validation` has candidates and strong safety text. The next step is not
"run everything"; it is to decide exact scope, expected output, redaction, and
receipt location before any script invocation.

## 4. Build Principle

AGENTS OS should now move from "more philosophy" to "local seed with traceable
small loops."

The correct near-term shape:

```text
Notion = living constitution, memory, and long-form governance.
Workspace = local seed, contracts, receipts, code, and verification.
codex-router = current governance engine candidate.
VCPToolBox = future runtime body, approached through A0 object-list first.
VCPChat = future interface layer, approached after Cockpit card contracts exist.
```

Do not let runtime define the life core. Do not let life core remain only in
Notion.

## 5. Proposed Roadmap

### Phase A: Stabilize Local Reality Map

Goal: make the current local state easy to see without scanning the whole
workspace every time.

Recommended outputs:

```text
ops/reports/current-workspace-state-YYYY-MM-DD.md
ops/reports/current-open-gaps-YYYY-MM-DD.md
control-plane/registry/WORKSPACE_REGISTRY.yaml review notes
```

Rules:

```text
No private-state read.
No archive execution.
No validation script run unless separately authorized.
No remote fetch/clone.
```

### Phase B: Materialize Core Contracts

Goal: turn Notion governance into small, local, reviewable schemas.

Candidate contract set:

```text
TaskEnvelope
Receipt
CapabilityCard
AgentIdentityCard
AgentRoomCard
ActivationPackage
StandingAuthorization
PresencePermission
SensingLevel
GrowthEvent
BehaviorPolicyCandidate
GrowthVerification
```

Recommended location:

```text
control-plane/contracts/
```

Rule: start with schema drafts and examples using fake/sample data only.

### Phase C: Localize The Four Foundation Agents

Goal: give Nobao, Memory Agent, Review Agent, and Project Agent local operating
cards without activating new runtime identities.

Recommended outputs:

```text
control-plane/prompts/agents/README.md updates or agent-card drafts
control-plane/contracts/agent-card examples
ops/reports/foundation-agent-localization-plan-YYYY-MM-DD.md
```

Boundary:

```text
This is documentation and contract work only.
Do not choose final extension/agent-pack placement yet.
Do not read or write private memory.
Do not grant new permissions.
```

### Phase D: Prepare VCPToolBox A0 Target/Object List

Goal: follow the Notion-approved sequence before any real runtime probe.

Allowed first artifact:

```text
VCPToolBox A0 target and object list
```

It should answer:

```text
what public objects would be read
why each object matters to AGENTS OS
which objects are explicitly excluded
stop conditions
review questions
receipt template
```

Not allowed yet:

```text
clone/fetch VCPToolBox
scan real runtime content
run VCPToolBox
call plugins/providers
read config/env/private memory
generate Public Capability Map as if probe happened
```

### Phase E: Use codex-router As Governance Spine Candidate

Goal: map local AGENTS OS permission and evidence concepts to the existing
`codex-router` architecture.

Candidate mapping:

```text
Permission v0.2        -> risk / approval / provider execution policy
Activation Package     -> task envelope + permit + execution profile
Receipt                -> audit/evidence artifact
Review Agent           -> validation arbiter / governance observation
Project Agent          -> task graph / run-manager / route state
Memory Agent           -> evidence and state-sync records
```

Boundary:

```text
Do not modify codex-router on main.
Any implementation uses a branch and repository reality check.
Runtime-governance changes need tests.
```

### Phase F: Cockpit MVP As Data, Then Interface

Goal: build the Cockpit as seven data cards before building UI.

First local MVP:

```text
HouseStatusCard
CurrentThreadCard
ActiveAgentCard
CouncilItemCard
ActivationRequestCard
RiskSignalCard
NextStepCard
```

Recommended flow:

```text
schema draft -> fake example -> report rendering -> later UI
```

Do not begin with VCPChat/VCPDesktop execution.

### Phase G: Controlled Validation Lane

Goal: make validation usable without turning it into hidden execution.

Before any validation script run, write or ask for:

```text
scope
working directory
expected output
redaction policy
failure behavior
receipt location
```

First likely validation candidates after separate authorization:

```text
validate-workspace.sh
validate-extension-manifests.sh only after extension manifests exist
validate-no-secrets.sh with redacted/count output policy
```

## 6. First Three Recommended Actions

1. Create a local current-state report.

Purpose: record the actual state found here: root not git, codex-router present,
target runtime/domain/extension dirs empty, validation deferred, private-state
denied.

2. Draft the first local contract schemas.

Start with `Receipt`, `CapabilityCard`, and `TaskEnvelope`, because they connect
Loop 001, VCPToolBox A0 planning, and codex-router.

3. Draft the VCPToolBox A0 target/object list.

This is the next Notion-compatible runtime move. It is still pre-probe and
read-only planning, not runtime inspection.

## 7. Explicit Non-Goals For The Next Step

```text
Do not clone or fetch VCPToolBox without separate authorization.
Do not run validation scripts without separate exact authorization.
Do not activate extension loading.
Do not create agent-pack placement as if final.
Do not touch state-private.
Do not update Notion unless Jenn asks for Notion write.
Do not use archive as execution root.
Do not turn Cockpit into UI before data cards exist.
Do not let codex-router become the whole AGENTS OS.
```

## 8. Open Questions For Jenn

These are not blockers for documentation work, but they decide later execution:

```text
Should the workspace root itself become a git repository, or remain a meta
workspace containing nested repos?

Should VCPToolBox be cloned fresh into runtime/VCPToolBox, or should an existing
local/A-drive reference be inspected first under a separate read-only
authorization?

Should local AGENTS OS contracts be written as JSON Schema first, Markdown
contracts first, or both in parallel?

Should Cockpit MVP start as Markdown/YAML data cards, or as a tiny local static
viewer after card schemas exist?
```

## 9. Receipt

```text
authorization_scope: Jenn allowed one planning document to be written after
  Notion read and workspace survey.
files_created:
  - ops/reports/agents-os-workspace-reality-and-build-plan-2026-06-30.md
files_changed_existing: none
notion_writes: none
private_state_access: none
validation_run: none
git_operations: read-only status/log/remote checks only
remaining_risk:
  - Not all archive/superseded Notion pages were individually fetched.
  - Local workspace survey stayed shallow and avoided private/high-risk areas.
  - No validator was executed, by design.
rollback_path:
  - delete this planning report if Jenn decides it should not remain.
```
