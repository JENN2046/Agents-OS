# Source To Local Requirements

Date: 2026-06-30
Status: requirements_map_v0.1_adjusted_2026-06-30

## 0. Purpose

This file maps Notion AGENTS OS concepts and local workspace facts to local
landing requirements.

It is not an implementation spec. It is the requirement source map for the
future implementation plan.

## 1. Source Map

### Life Core

Source:

```text
AGENTS OS | Life Core v0.1
https://app.notion.com/p/376ee4ca933c8150baaad57ae9c19396
```

Local requirement:

```text
Every local contract and runtime plan must preserve the idea that Agent is a
resident subject with identity, memory, relation, responsibility, and boundary.
```

Local artifacts needed:

```text
AgentIdentityCard
AgentRoomCard
RelationshipCard
ResponsibilityLedger fields
```

### House Rules

Source:

```text
AGENTS OS House Rules v0.1
```

Local requirement:

```text
No local plan may hide failure, fake validation, fake memory write, fake
authorization, or secret exposure.
```

Local artifacts needed:

```text
Receipt
ReviewResult
FailureCode
StopCondition
```

### Permission v0.2

Source:

```text
AGENTS OS Permission and Authorization Design v0.2
```

Local requirement:

```text
A0/A1/A2/A3a/A3b/A3c/A4 must appear in local plans and contracts as explicit
permission levels, not vague risk language.
```

Local artifacts needed:

```text
PermissionLevel enum
StandingAuthorization
ActivationPackage
TrustBudget
ReceiptRequirement
```

### Presence Permission And Sensing

Source:

```text
Presence Permission v0.1
Sensing Levels S0-S6 v0.1
```

Local requirement:

```text
Presence and sensing must not be implemented as default device access. They must
be represented as planned permissions, consent logs, and stop conditions before
any runtime feature exists.
```

Local artifacts needed:

```text
PresencePermissionCard
SensingLevelPolicy
ConsentLog placeholder contract
NoMemory / Off / Pause states
```

### Memory Rules

Source:

```text
AGENTS OS dedicated memory rules v0.1
Formal community memory index v0.1
```

Local requirement:

```text
Local memory work must distinguish self_record, proposed, official,
pending_review, deprecated, and superseded states.
```

Local artifacts needed:

```text
MemoryRecordStatus
MemoryRegistrationProposal
MemoryReviewGate
FormalMemoryIndexMirror plan
```

### Resident Agents

Source:

```text
Nobao room and identity
Memory Agent room
Review Agent room
Project Agent room
First resident-agent record
```

Local requirement:

```text
The four foundation agents must become local planning roles before becoming
runtime agents.
```

Local artifacts needed:

```text
foundation-agent-card drafts
role-to-workstream map
agent-to-agent relation-card examples
```

### Loop 001

Source:

```text
First real loop design v0.1
Loop 001 running record
Receipt | Loop 001
```

Local requirement:

```text
The local workspace must reuse the loop grammar: proposal, scope, authorization,
execution boundary, receipt, memory decision, review, closeout.
```

Local artifacts needed:

```text
LoopPlan
LoopScope
LoopReceipt
LoopCloseout
```

### Cockpit

Source:

```text
AGENTS OS Cockpit v0.1
Cockpit data cards v0.1
```

Local requirement:

```text
Build the Cockpit first as data cards and source references, not as a UI or
VCPChat widget.
```

Local artifacts needed:

```text
HouseStatusCard
CurrentThreadCard
ActiveAgentCard
CouncilItemCard
ActivationRequestCard
RiskSignalCard
NextStepCard
```

### VCPToolBox And Runtime

Source:

```text
AGENTS OS dual foundation v0.1
VCPToolBox position v0.2
VCPToolBox capability boundary v0.1
VCPToolBox read-only experiment design v0.1
VCPToolBox A0 target adjustment v0.1
```

Local requirement:

```text
First runtime landing step is target/object-list planning only. No clone, probe,
plugin call, provider call, shell, config read, or private memory read is implied.
```

Local artifacts needed:

```text
VCPToolBoxA0TargetObjectList
ExcludedObjectList
ReadonlyProbePlan later
CapabilityCard later
```

### VCPChat

Source:

```text
VCPChat capability review v0.1
VCPChat position definition v0.1
```

Local requirement:

```text
Treat VCPChat as future interface layer. Do not start with desktop widgets,
Canvas execution, HTML/JS execution, or memory edits.
```

Local artifacts needed:

```text
Cockpit card data model
Interface boundary note
Future UI prototype authorization plan
```

### Growth

Source:

```text
Agent growth mechanism v0.1
VCP thought-cluster access v0.1
```

Local requirement:

```text
Growth must become a verifiable chain, not just more memory.
```

Local artifacts needed:

```text
GrowthEvent
BehaviorPolicyCandidate
ThoughtClusterPatchProposal
GrowthVerification
```

## 2. Local Workspace Requirements

From local files:

```text
_ROOT_POLICY.md
_DIRECTORY_PRINCIPLES.md
_MIGRATION_MAP.md
AGENTS.md
governance/SECURITY_BOUNDARIES.md
control-plane/registry/WORKSPACE_REGISTRY.yaml
control-plane/runbooks/*.md
ops/validation/README.md
governance/codex-router/AGENTS.md
```

Local requirements:

```text
Use WSL canonical root.
Do not treat Windows reference root as execution root.
Do not read state-private by default.
Do not execute archive.
Do not treat registry URL metadata as remote action authorization.
Do not run validation scripts without exact scoped authorization.
Do not work directly on codex-router main for implementation.
Keep runtime core upstream-trackable.
Keep Jenn extensions outside runtime core.
Keep private memory out of memory/ code directory.
Treat ops/migration as historical evidence and not as the live state authority.
Use project-local state cards plus a global project index for future work.
Separate codex-router validated source commit from state-only descendant head.
Treat validation scripts and package scripts as future gated actions, not
default checks.
```

## 3. Requirement Priorities

Priority order:

```text
P0 boundary and reality
P1 project index and state-card surface
P2 registry / migration-map reconciliation
P3 minimal contracts and local roles
P4 codex-router alignment
P5 runtime source-boundary and VCPToolBox A0 object-list
P6 Cockpit data cards
P7 validation lane
P8 first local loop
P9 runtime/interface implementation later
```

## 4. Traceability Rule

Every future task should state:

```text
Notion source concept
local file target
permission level
deliverable
acceptance evidence
receipt requirement
```
