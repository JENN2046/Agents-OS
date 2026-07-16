# AGENTS OS | Life-Core Authority and Gap Map v0.1

```yaml
document_type: authority_and_gap_map
project: AGENTS OS
phase: Home Domain Phase 1A
version: v0.1
date: 2026-07-13
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
gate: G1A
implementation_authorized: false
runtime_activation_authorized: false
Phase_1B_started: false
```

## 1. Purpose

This document answers four factual questions before Home Domain direction work:

```text
What life-core authority already exists?
Which fact classes already have one authority?
Which current files only describe direction or interpretation?
Which unresolved foundations block M0, and which also block Home Direction?
```

It does not create a Home Domain schema, a second ledger, a runtime service, a
memory store, or a new permission system.

## 2. Review Boundary

The review used only current workspace governance, registered life-core policy,
accepted architecture, and registered role-interpretation material. It did not
read:

```text
state-private/
private raw memory
secret, token, cookie, credential, or provider configuration
provider raw responses
runtime databases or database dumps
unregistered personal records
```

Primary inputs:

```text
AGENTS.md
CURRENT_STATE.md
control-plane/registry/drafts/2026-07-13-agents-os-home-domain-construction-roadmap-r3.draft.md
control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
control-plane/registry/decisions/2026-07-12-agents-os-vcp-high-privilege-architecture-v0.1.md
control-plane/policies/life-core/README.md
control-plane/policies/life-core/policy-index.json
control-plane/policies/life-core/*.md
labs/nobao-local-resident-role-prompt-v0.3-draft.md
labs/nobao-active-prompt-v0.1-draft.md
```

## 3. Authority Vocabulary

This map uses the following distinctions:

| Term | Meaning |
|---|---|
| Semantic authority | Defines what a fact means and what it may affect. |
| Canonical writer | The only component or actor allowed to establish the current fact. |
| Reporter | May report an observation but cannot establish the canonical fact. |
| Logical storage authority | The domain responsible for persistence and lifecycle. |
| Physical location | A verified present location. If not established, it is `UNRESOLVED`. |
| Projection | Rebuildable read-only view that cannot become a writer. |
| Candidate | Non-canonical proposal awaiting an explicit decision or gate. |

The required operating rule is:

```text
Single Authority Per Fact Class
+ explicit reporters
+ derived read-only projections
```

It does not require one database for all facts.

## 4. Current Authority Layers

### 4.1 Root operating authority

The root `AGENTS.md` is the current workspace execution contract. It defines:

```text
Jenn P0 final authority
Nobao construction authority under Jenn
P3 hard stops
Green / Yellow / Red execution lanes
private raw memory and secret denials
current Git and delivery boundaries
```

Older life-core permission language remains useful as policy history and
semantic input, but it does not override the current root execution contract.

### 4.2 Accepted architecture authority

The accepted Resident and VCP high-privilege decisions establish:

```text
VCPToolBox as the first backend body and resident host
VCPChat as desktop frontend and controlled desktop host
VCPMobile as mobile frontend and controlled device host
Nobao as the unique resident coordinator
AGENTSOSResident as the future deterministic continuity service
one canonical GlobalTaskLedger for Orchestrator facts
one authority per fact class
VCP native memory as memory-content lifecycle authority
governed memory bridge as memory-access governance boundary
execution hosts as reporters of their real process and device facts
```

These decisions define architecture. They do not prove that the described Rust
core, database, identity service, permit verifier, or memory bridge exists and
is active today.

### 4.3 Current life-core policy authority

The registered local modules establish current semantic boundaries for:

```text
root principles
house rules
memory governance
resident membership and rooms
permission and activation boundaries
runtime/body separation
growth
Presence and sensing
```

Their local files are current policy-facing mirrors. The Notion page recorded
in their metadata is an upstream knowledge source, but an unseen or later
Notion change is not automatically current workspace authority. It must be
imported, reviewed, versioned, and registered before local execution may rely on
it.

### 4.4 Interpretive identity material

The root `AGENTS.md` is Nobao's active workspace operating contract. The files
under `labs/` are identity, tone, and governance interpretation. They explain
Nobao but do not independently activate permissions, establish runtime identity
facts, or override root governance.

## 5. Domain Authority Findings

### 5.1 Identity

Established:

```text
Jenn owns final identity confirmation.
Nobao is the unique long-lived resident coordinator.
Model calls and sessions are not Nobao's identity body.
Identity continuity must survive model, session, and body replacement.
Root AGENTS.md is the current operating contract for Nobao in this workspace.
```

Not established:

```text
canonical stable identity record schema
identity revision and supersession protocol
authenticated binding from actor identity to model/session/host
deterministic recovery source for identity continuity
current physical identity store inside AGENTSOSResident
```

The accepted Resident architecture assigns these future deterministic duties to
`AGENTSOSResident`, but implementation has not started. Therefore it is wrong to
claim that a live Resident database currently owns identity facts.

### 5.2 Relationship

Established:

```text
relationship meaning is separate from authority
closeness does not expand permission
subjective relationship feeling is not another Agent's formal memory
formal relationship changes require visibility, review, and dispute/pause rights
Jenn retains final authority over root relationship governance
```

Not established:

```text
canonical relationship fact writer
relationship record revision schema
affected-Agent authentication and acknowledgement method
formal relationship persistence location
relationship repair and retirement reducer
```

The A2A policy file is active as a registered document while its own semantic
status remains `pending_formal_memory_registration`. Document activity and
formal relationship-memory status are different facts.

### 5.3 Presence and sensing

Established:

```text
Presence is not monitoring.
Seeing is not recording.
Memory must be chosen.
S1 and S2 are the initial safe direction.
S3 to S5 require explicit consent and authorization formats.
S6 is proposal-only and default forbidden.
VCPChat and VCPMobile report their own current surface/device facts.
```

Not established:

```text
canonical PresenceConsent record writer
consent revision, expiry, revocation, and scope binding
current Presence mode state machine
retention enforcement
cross-device consent binding
Resident acceptance of authenticated device sensing reports
```

The current policy separates formal Presence governance from sensing details
that still require patching. A general Presence policy is not a concrete consent
instance and is not proof that sensing is active.

### 5.4 Session and Life Stream

Established:

```text
Session is temporary context, not long-term memory.
Ordinary conversation must not automatically become Goal, Task, or Memory.
Frontend or session hosts may hold transient interaction state.
Session content cannot directly write Orchestrator canonical state.
```

Not established:

```text
Session ownership contract across VCPChat, VCPMobile, and VCPToolBox
retention and deletion policy for session content
Life Stream canonical name and minimum contract
Life Stream candidate writer and persistence authority
candidate promotion, discard, and expiry rules
```

`Life Stream` remains a future lightweight semantic space. Phase 1A does not
create it as a new canonical object.

### 5.5 Memory and meaning

Established:

```text
VCP native memory owns memory content and memory lifecycle.
Memory access permission and low-disclosure evidence belong to a governed bridge.
Agent self memory is not community consensus.
Session, receipt, review, and draft are not automatically formal Memory.
private raw memory is denied to this review and ordinary workspace operations.
Jenn retains final authority for personal long-term memory and root memory changes.
```

Not established:

```text
exact governed memory bridge implementation owner
authenticated memory-read and memory-write command contract
scope, sensitivity, provenance, currentness, retention, and deletion schema
Memory Candidate promotion decision reducer
contradiction and supersession reducer
portable export boundary for selected memory
```

The architectural owner is known, but Phase 1A did not inspect private content
or a live memory database. Content existence and quality are therefore not
asserted.

### 5.6 Intent and authorized action

Established:

```text
an intent candidate is not an authorized command
Home semantics cannot directly write Task or Goal state
authorized action must cross the Orchestrator command boundary
Rust remains the future canonical writer for Orchestrator state
relationship, memory, and Presence do not grant execution permission
```

Not established:

```text
Intent Candidate minimum contract
actor identity and delegation contract
authenticated command envelope
Home-to-Orchestrator command translation authority
rejection and acknowledgement semantics
binding from Jenn/Nobao authority to a concrete Command
```

### 5.7 Reflection and growth

Established:

```text
growth begins as evidence-backed candidates
one failure cannot permanently rewrite personality or policy
growth cannot expand permission
accepted learning must remain explainable, revisable, and reviewable
```

Not established:

```text
canonical GrowthEvent writer
accepted-learning decision authority by learning class
behavior policy revision and rollback contract
verification horizon and supersession semantics
```

### 5.8 Agent community

Established:

```text
Nobao is the sole resident coordinator.
Long-lived Domain Agents are allowed within charters.
Temporary Workers are task-scoped and do not gain persistent global authority.
No Agent other than the canonical writer may directly modify global Task state.
```

Not established:

```text
stable Domain Agent identity and charter schema
delegation and return contract
shared-memory visibility boundary
handoff, pause, retirement, and restoration protocol
authenticated disagreement and Council decision boundary
```

## 6. Conflict Inventory

| ID | Observed conflict or tension | Current disposition |
|---|---|---|
| LC-C01 | `standing-authorization.md` says active pilot until 2026-07-07, which is expired on 2026-07-13. | Treat it as expired historical pilot authority. Root `AGENTS.md` governs current local execution. It grants no present A3a authority. |
| LC-C02 | Life-core README calls Notion upstream source of truth, while local work must follow current registered contracts. | Notion is upstream knowledge provenance, not an automatically live execution authority. Only imported, reviewed, versioned local material is current for workspace action. |
| LC-C03 | Document Registry marks A2A policy `active`, while the policy says `pending_formal_memory_registration`. | `active` describes document lifecycle. It does not mean the relationship protocol has completed formal Memory registration. |
| LC-C04 | Presence mirror says formal Presence governance exists, while sensing still needs patches. | Separate policy authority from concrete consent instances and sensing runtime contracts. No sensing activation is inferred. |
| LC-C05 | Accepted Resident architecture assigns identity continuity to `AGENTSOSResident`, while implementation is not started. | Treat it as accepted target authority, not a current physical store or running writer. |
| LC-C06 | Life-core A0-A4 permission language overlaps current P0-P3 and Green/Yellow/Red rules. | Root `AGENTS.md` is current execution authority. Life-core levels remain semantic/history input until a dedicated reconciliation contract supersedes them. |
| LC-C07 | Labs role charter is detailed identity material, but it is still a draft. | Root `AGENTS.md` is active operating authority. Labs files are interpretive references only. |
| LC-C08 | VCP native memory is named as content authority, while raw private memory is unreadable in this phase. | Authority can be established without inspecting content. No claim is made about live contents, completeness, or quality. |

No conflict above requires changing the accepted Resident or Scheduling
subjects to continue Home Direction work.

## 7. Duplication Inventory

| ID | Duplicated area | Risk | Required future treatment |
|---|---|---|---|
| LC-D01 | Root principles appear in Notion mirror, split modules, root AGENTS, and role charter. | Silent drift between identity meaning and execution rules. | Keep one current semantic policy index and mark mirrors/charters by role and revision. |
| LC-D02 | Permission semantics appear in life-core A0-A4, root P0-P3, and Green/Yellow/Red. | Different agents may apply different gates. | Produce a compatibility map; do not create a third permission model. |
| LC-D03 | Memory rules appear in the local mirror, module, root AGENTS, and accepted architecture. | Content authority, access authority, and formal Memory may be conflated. | Freeze a minimum Memory/Session/Artifact boundary before M0-B. |
| LC-D04 | Presence appears in mirror, module, role language, VCPMobile direction, and roadmap. | Presence may be mistaken for sensing activation. | Separate policy, consent instance, device report, recording, retention, and memory promotion facts. |
| LC-D05 | Nobao identity appears in root AGENTS, labs charter, active-prompt draft, and Resident architecture. | A draft prompt may be mistaken for canonical identity or permission. | Bind stable identity facts separately from narrative, prompt, model, and session. |

## 8. Unresolved Foundation List

### 8.1 Blocking for Home Direction

```yaml
unresolved_blocking_for_home_direction: []
```

The current sources are sufficient to define Home Domain responsibilities,
negative boundaries, portability requirements, and interfaces without inventing
runtime facts.

### 8.2 Blocking for M0

```yaml
unresolved_blocking_for_M0:
  - id: HD-M0-01
    contract: Actor Identity and Delegation v0.1
    reason: no authenticated binding between Jenn, Nobao, Domain Agent, Worker, session, and host

  - id: HD-M0-02
    contract: Resident Identity Continuity Minimum v0.1
    reason: accepted target authority exists but canonical record, revision, recovery, and singleton ownership are not specified

  - id: HD-M0-03
    contract: Memory Session Artifact Boundary Minimum v0.1
    reason: content, access, retention, promotion, deletion, and evidence authority are not yet closed

  - id: HD-M0-04
    contract: Governed Memory Access v0.1
    reason: governed bridge identity, authenticated request, denial, and low-disclosure evidence contract are unresolved

  - id: HD-M0-05
    contract: Home-to-Orchestrator Minimum Interface v0.1
    reason: intent candidate cannot yet be deterministically translated into an authenticated Command

  - id: HD-M0-06
    contract: Presence Consent and Device Observation Minimum v0.1
    reason: policy exists but concrete consent, revocation, device-report authentication, and retention facts are unresolved

  - id: HD-M0-07
    contract: Relationship Fact Minimum v0.1
    reason: formal relationship writer, affected-party acknowledgement, revision, and dispute semantics are unresolved
```

`HD-M0-06` and `HD-M0-07` may be excluded from M0-A if M0-A contains no
Presence or relationship mutation. They remain required before the relevant
M0-B behavior is claimed.

## 9. G1A Result

```yaml
G1A:
  result: PASS_WITH_GAPS
  home_domain_drafting_allowed: true
  unresolved_blocking_for_home_direction: []
  unresolved_blocking_for_M0:
    - HD-M0-01
    - HD-M0-02
    - HD-M0-03
    - HD-M0-04
    - HD-M0-05
    - HD-M0-06
    - HD-M0-07
  implementation_authorized: false
  runtime_activation_authorized: false
```

Reduction rationale:

```text
The gaps prevent M0 implementation readiness.
They do not prevent upper-level Home Domain direction work.
Phase 1B may begin only through its separately recorded transition.
```

## 10. Non-Authorization

This map does not authorize:

```text
Phase 1B automatic start
runtime or database work
private memory reads or migration
Presence or sensing activation
provider, plugin, service, device, or executor calls
identity, relationship, or formal Memory mutation
commit or push
```

