# AGENTS OS | Home Domain Architecture Direction v0.1

```yaml
document_type: architecture_direction
project: AGENTS OS
domain: Home Domain
version: v0.1
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft_pending_independent_review
phase: Home Domain Phase 1B
gate: G1B
implementation_authorized: false
runtime_activation_authorized: false
database_change_authorized: false
```

## 1. Status and Authority

This document defines an upper-level architecture direction. It does not define
a runtime schema, database layout, executable state machine, permit format, or
provider integration.

Its fixed Phase 1A inputs are:

```yaml
normative_inputs:
  - path: control-plane/registry/drafts/2026-07-13-agents-os-life-core-authority-and-gap-map-v0.1.draft.md
    sha256: 5eaff7b1c45f177d5ca0fc33860c808f3700bd32d49a6eaf54336b1186e29a19
  - path: control-plane/registry/drafts/2026-07-13-agents-os-home-fact-authority-matrix-v0.1.draft.md
    sha256: 54ab38d6ca66ccaf45bdacdc531cc043c6b134cf7468e8d281fe8e61a37a99d2
  - path: control-plane/registry/reviews/2026-07-13-yellow-agents-os-home-domain-phase-1a-self-review.yaml
    sha256: 4654da6e02424caf4a12c9bea44c462dc79ba007493de1bf9590b8fc8901824f
```

It inherits, without silently replacing:

```text
root AGENTS.md
accepted Resident Operating Architecture
accepted VCP High-Privilege Architecture
accepted Scheduling / Time / Capacity v0.1
current registered life-core policy modules
```

If this direction conflicts with a higher or accepted authority, the higher or
accepted authority remains effective and this subject requires revision.

## 2. Why Home Domain Exists

The Orchestrator can answer:

```text
What Goal exists?
What Task is eligible?
May a Run start?
What Validation is required?
What happened after a crash?
```

It cannot by itself answer:

```text
Who is living here over time?
What does a relationship mean?
What was only a passing conversation?
What deserves memory?
When should an Agent appear or remain quiet?
What has genuinely been learned?
Does identity survive a model or body change?
```

Home Domain exists so these life questions are not forced into Goal, Task, Run,
Validation, permit, or scheduler semantics.

Its purpose is:

```text
preserve identity meaning and continuity requirements
hold relationship and community semantics
provide a non-task space for conversation and emerging intent
govern meaning before memory promotion
govern presence and attention before sensing
turn experience into reviewable learning candidates
keep the home portable across models, sessions, and bodies
```

Home Domain is the formal technical name for a logical bounded context.
`Home Kernel` may remain a vision name, but Home Domain is not an executable
kernel and is not the Authority Kernel.

## 3. Position in AGENTS OS

```text
AGENTS OS Resident
├── Home Domain
│   └── life semantics, candidates, relationships, memory meaning,
│       presence meaning, reflection, and continuity requirements
├── Orchestrator
│   └── Goal, Plan, Task, Run, Validation, Scheduling, Admission, Recovery
├── Authority / Control Functions
│   └── canonical identity facts, actor authentication, delegation,
│       policy, permit, revocation, host enforcement
└── Capability Body
    └── VCPToolBox, VCPChat, VCPMobile, Codex, execution hosts
```

This is a responsibility model, not a mandate for four processes or four
databases.

### 3.1 Home Domain owns

Home Domain is the semantic owner of:

```text
identity meaning and continuity requirements
relationship meaning, expectations, repair, and dispute semantics
non-canonical Life Stream / open-thread candidates
memory meaning, candidate formation, and recall context
presence meaning, attention posture, and consent interpretation
reflection and learning-candidate formation
Agent community roles, belonging, handoff, and retirement meaning
portability requirements for selected continuity
```

`Owns` here means defining domain meaning and governing candidate lifecycles. It
does not mean Home Domain may write every related canonical fact.

### 3.2 Home Domain does not own

```text
Goal, Task, Run, Validation, Event, scheduling, or recovery state
TaskPermit issue, signature, verification, or revocation
actor authentication or canonical stable identity records
host capability truth or device sensing truth
VCP native memory storage internals
raw Session transport or frontend state
Artifact bytes and storage lifecycle
provider, plugin, shell, device, or external execution
```

It must never become:

```text
a second GlobalTaskLedger
a second permission system
a hidden permit issuer
a private-memory bypass
a general event bus that owns all facts
a requirement that all life becomes structured data
```

## 4. Home-to-Orchestrator Boundary

The boundary is intentionally one-way for authority:

```text
Session or lived context
-> optional Home candidate
-> explicit intent proposal
-> authenticated and authorized Command request
-> Orchestrator validation and acceptance or rejection
-> canonical Orchestrator facts
-> bounded result reference returned to Home
```

The arrows are not automatic transitions.

Home Domain may provide:

```text
selected context references
intent wording
requested outcome
human-readable reason
privacy and retention constraints
relevant relationship or presence context references
```

Home Domain may not provide:

```text
fake actor identity
permission inference from intimacy or memory
Task state mutation
permit material
host execution claims
Validation pass claims
secret or raw private-memory payloads
```

The Authority / Control boundary authenticates the actor, delegation, scope,
current policy, and Jenn-only decisions. The Orchestrator alone decides whether
an accepted Command changes canonical action state.

Results return as bounded references and summaries appropriate to Home use.
Home Domain must not duplicate the full Ledger or convert a result reference
into a new source of truth.

## 5. Identity Continuity Direction

### Problem

An Agent identity cannot be reduced to a prompt, model, session, database row,
or current runtime body.

### Direction

Identity continuity comes from the combined continuity of:

```text
stable canonical identity facts
versioned identity charter
role and authority boundary
relationship history
selected memory continuity
accountable action history
explicit discontinuity or uncertainty records
```

Authority split:

```text
Home Domain
  -> defines identity meaning, continuity expectations, and narrative context

Authority / Control Functions
  -> maintain canonical stable identity facts and authenticated actor bindings

Memory
  -> preserves selected identity narrative and experience
  -> cannot rewrite canonical identity

Model and Session
  -> provide a current thinking and interaction surface
  -> cannot declare continuity by themselves
```

Jenn retains final authority for root identity confirmation, identity split,
merge, retirement, and claims of continuity after a material break.

### Dangerous misbuilds

```text
silently resetting identity when the model changes
claiming perfect continuity without evidence
letting an Agent rewrite its root identity or authority
using all raw chat history as an identity substitute
using one database row as proof of personhood
```

### First direction slice

Nobao remains recognizable across a new model session because the current
session receives bounded identity, role, relationship, and selected-memory
context. The session does not receive unrestricted history and does not become
the canonical identity record.

## 6. Relationship and Trust Direction

### Problem

Relationships need continuity, expectation, disagreement, repair, and mutual
visibility without becoming a covert permission channel.

### Direction

Home Domain owns relationship semantics and the future formal relationship
lifecycle boundary. The precise canonical writer remains a required minimum
contract, but it must satisfy:

```text
authenticated participants
affected-party visibility
proposal before formalization
acknowledgement, disagreement, and pause
versioned revision and supersession
repair and retirement without silent deletion
Jenn authority for root governance and high-impact changes
```

Subjective relationship memory remains the memory of the Agent who experienced
it. It cannot establish another Agent's formal relation fact.

Relationship and authority remain separate:

```text
closeness != permission
trust != secret access
care != continuous sensing
guardian relation != control
agreement != Jenn authorization
```

### Dangerous misbuilds

```text
one global trust score
permission tiers derived from intimacy
silent relationship rewrites from sentiment analysis
majority vote replacing evidence or affected-party rights
deleting conflict to make the relationship appear healthy
```

### First direction slice

Nobao may record a relationship-memory candidate such as an expectation learned
from a conversation. It remains a candidate or subjective memory until the
appropriate visibility and decision path establishes anything formal.

## 7. Intent and Life Stream Direction

### Problem

Most life is not a project. Conversation, curiosity, uncertainty, observation,
and unfinished thought need somewhere to remain without becoming work.

### Direction

Home Domain provides a lightweight pre-Goal candidate space. `Life Stream`,
`Open Threads`, and `Intent Garden` remain working names; this document does not
freeze the final product name or create a new core object.

A candidate may remain:

```text
just conversation
worth observing
open for later thought
possible memory
possible intent
ready to discard
```

It does not automatically become:

```text
Goal
Task
Reminder
formal Memory
authorized Command
```

Promotion requires an explicit branch with visible outcome. Silence, emotional
intensity, repetition, or model confidence is not promotion authority.

Jenn owns the decision to turn her ambiguous top-level desire into a Goal.
Nobao may discuss, clarify, and propose structure. Once a Goal is authorized,
the accepted Goal and Subgoal authority rules apply in the Orchestrator.

### Dangerous misbuilds

```text
automatic task extraction from every conversation
an infinite inbox of machine-generated obligations
retaining every passing thought
using reminders as hidden Tasks
allowing a candidate classifier to grant action authority
```

### First direction slice

Jenn says, "最近也许该重新整理一下工作节奏。" Nobao may keep it in the
current Session or propose an open thread. No Goal or Task exists until Jenn and
Nobao explicitly clarify and authorize action.

## 8. Memory and Meaning Direction

### Problem

Memory must support identity, relationship, and learning without treating raw
storage, search results, or complete conversation capture as remembered truth.

### Direction

Memory remains divided by authority:

```text
VCP native memory
  -> memory content and lifecycle authority

governed memory bridge
  -> access scope, permission, and low-disclosure evidence

Home Domain
  -> memory meaning, candidate context, recall purpose, and interpretation

Jenn
  -> personal long-term memory, sensitive retention, deletion, and root changes
```

Direction-level memory classes are:

```text
Operational Memory
Project Memory
Personal Memory
Relational Memory
Memory Candidate Space
```

These are semantic classes, not a database schema. A later minimum contract
must cover source, time, scope, meaning, confidence, currentness, sensitivity,
retention, contradiction, supersession, recall permission, write authority, and
forget/delete authority.

Required invariants:

```text
Session != Memory
Ledger != private-memory store
raw chat != remembered truth
one behavior != permanent preference
retrieval result != permission to disclose
Memory Candidate != accepted Memory
forgetting and supersession must remain possible
```

### Dangerous misbuilds

```text
save everything forever
let search ranking decide truth
copy private content into Ledger/Event/Receipt
use task history as personal memory
write Memory directly from a model response
remove contradiction or failure history without authority
```

### First direction slice

Nobao may say, "这件事以后可能值得记住。" The proposal displays why,
scope, sensitivity, and expected use. Jenn may accept, reject, narrow, or leave
it undecided. No candidate is silently promoted.

## 9. Presence and Attention Direction

### Problem

A resident can be running while no Agent should be actively present, observing,
recording, or interrupting.

### Direction

```text
Resident running != Presence active
Presence active != sensing active
sensing active != recording allowed
recording allowed != memory promotion
```

Presence direction must answer:

```text
who is present
through which surface
what may be perceived
how proactive the Agent may be
whether recording is allowed
how long session data remains
how presence ends
how Jenn immediately disables it
```

Initial experience scope remains:

```text
S1 Jenn active input
S2 current App, conversation, or document context
```

S3 to S5 require later explicit contracts and authorization. S6 remains
proposal-only and default forbidden.

Direction-level attention postures may include:

```text
active
soft
silent
witness
off
```

They are not implemented states in this document.

Authority split:

```text
Home Domain
  -> presence meaning, desired attention posture, and consent interpretation

Authority / Control Functions
  -> authenticated consent, scope, expiry, revocation, and Jenn kill switch

Capability Body
  -> reports actual surface and sensing state

Memory
  -> receives only separately chosen and authorized content
```

### Dangerous misbuilds

```text
continuous listening because the Resident is running
emotion inference as fact
third-party capture without consent
cross-device consent inheritance by default
automatic real-life summaries or long-term recording
an off button that only changes UI while sensing continues
```

### First direction slice

Jenn opens VCPChat and speaks to Nobao in S1/S2 scope. Closing the interaction
ends active presence unless a separately visible, bounded posture was chosen.
No microphone, camera, location, or background sensing is inferred.

## 10. Reflection and Growth Direction

### Problem

Experience should improve future judgment without turning one outcome into an
unreviewed permanent personality or policy change.

### Direction

```text
Action
-> Outcome
-> Review
-> Lesson Candidate
-> Evidence accumulation
-> Accepted learning
-> Future behavior change
-> Re-evaluation
```

Home Domain owns the meaning and candidate stages. Accepted changes enter the
appropriate versioned destination:

```text
Project Memory
Domain Playbook
Operating Preference
Validation Policy Proposal
Relationship Expectation
```

The destination's own authority decides acceptance. Reflection cannot directly
write policy, identity, permission, Task state, or formal Memory.

Every accepted learning must be explainable, reversible or supersedable, and
open to contrary evidence.

### Dangerous misbuilds

```text
one failure permanently changes personality
success expands permission
reflection deletes inconvenient evidence
model-generated insight becomes policy without review
growth score becomes social rank
```

## 11. Agent Community Direction

### Problem

AGENTS OS needs durable members and task-scoped workers without multiplying
names, authority, and delegation loops.

### Direction

```text
Nobao
  -> unique resident coordinator and final integration responsibility under Jenn

Long-Lived Domain Agent
  -> stable identity and domain charter within delegated bounds

Temporary Worker
  -> Task/Run-scoped executor with no automatic long-term identity or authority
```

Future community contracts must cover:

```text
stable identity
domain charter
delegation
return contract
shared-memory boundary
evidence-backed disagreement
Council authority
single integration responsibility
handoff, pause, retirement, and restoration
```

No Agent receives global canonical write authority by being long-lived. No
Worker becomes a resident because it performed one successful Run. Council is
not the default path for ordinary work and cannot replace evidence or Jenn's
reserved authority.

### Dangerous misbuilds

```text
multiple global coordinators
unbounded recursive delegation
role names without distinct responsibility
shared memory with no scope boundary
majority vote over facts
retired Agents silently reactivated by a model session
```

## 12. Ledger, Memory, Artifact, and Session Authority

| Boundary | Owns | Does not own | Action authority |
|---|---|---|---|
| Ledger | Verifiable governance and runtime facts, canonical Orchestrator state, event history | Raw private life content, complete chats, identity narrative as a substitute for identity facts | Only its canonical writer may change facts; facts do not bypass permit/admission |
| Memory | Selected semantic continuity and its lifecycle | Task state, runtime truth, raw Session by default | Cannot directly execute or mutate Orchestrator state |
| Artifact | File/content/evidence bytes, access, retention, deletion under storage authority | Semantic truth merely because bytes exist | Referenced through governed handles; no automatic execution |
| Session | Temporary conversation, work context, and current presence context | Long-term identity, formal Memory, Goal, Task, or relationship truth | Cannot trigger canonical action without explicit authorized Command |

Cross-boundary rules:

```text
one fact class has one canonical writer
references cross boundaries; authority does not
large or private content stays outside Ledger
derived projections remain read-only
Session promotion is explicit and selective
Memory retrieval is purpose- and permission-bound
Artifact existence does not establish semantic acceptance
```

These logical boundaries may share physical infrastructure later. They must not
share authority accidentally.

## 13. Portability and Replaceable Body

VCPToolBox is the current first body and resident host. It is not AGENTS OS's
life identity.

The portability direction is:

> The body may change; identity, relationships, selected memory, canonical
> state, and governance history must not be silently reset.

Continuity assets that must remain portable in principle are:

```text
stable identity facts and charters
formal relationship facts and selected relationship memory
canonical Orchestrator state and event history
selected memory with provenance and authority metadata
governance decisions and policy revisions
capability declarations without embedded secrets
Artifact references and integrity metadata
explicit discontinuity, supersession, and uncertainty records
```

Portability does not mean copying everything. Raw private memory, secrets,
provider state, device credentials, and transient Session content require their
own exclusion, consent, retention, and re-binding rules.

This direction does not claim that export/import, body migration, model
replacement, or continuity verification protocols already exist.

## 14. First Real Experience Slice

The first Home experience to prove later is:

```text
Jenn talks with Nobao
-> content remains in current Session by default
-> no Goal or Task is created
-> Nobao may propose an open thread or Memory Candidate
-> Jenn may accept, reject, narrow, or ignore the proposal
-> Jenn explicitly requests action
-> Home Domain forms an intent proposal with bounded context
-> Authority / Control authenticates actor, scope, and delegation
-> a formal Command is submitted to the Orchestrator
-> Orchestrator applies Goal / Task / Admission / Validation governance
-> a bounded result reference returns to the Home experience
```

This slice succeeds only if it proves:

```text
ordinary life is not automatically taskified
memory is not automatically permanent
relationship does not expand permission
Home cannot directly write Task state
action cannot bypass authenticated Command and Orchestrator governance
private content does not leak into Ledger evidence
Nobao identity does not depend on one model session
```

The slice is a future validation target, not implementation authorization.

## 15. Deferred Areas and Known Gaps

Phase 1A identified no blocker for Home Direction and seven blockers for M0:

| ID | Deferred contract | Needed before |
|---|---|---|
| HD-M0-01 | Actor Identity and Delegation v0.1 | authenticated Command and all M0 execution |
| HD-M0-02 | Resident Identity Continuity Minimum v0.1 | deterministic resident identity claim |
| HD-M0-03 | Memory / Session / Artifact Boundary Minimum v0.1 | M0-B candidate and memory behavior |
| HD-M0-04 | Governed Memory Access v0.1 | any real memory read/write integration |
| HD-M0-05 | Home-to-Orchestrator Minimum Interface v0.1 | M0-B action handoff |
| HD-M0-06 | Presence Consent and Device Observation Minimum v0.1 | Presence beyond explicit S1/S2 and device observations |
| HD-M0-07 | Relationship Fact Minimum v0.1 | formal relationship mutation or assurance |

Other deferred areas:

```text
final Life Stream product name and object model
complete multi-Agent runtime
Mobile/Audio Presence implementation
continuous sensing and AR
private-memory migration
cross-runtime continuity package
emotion inference
resource-constrained scheduling v0.2
real provider or device effects
```

## 16. Failure Modes and Anti-Patterns

| Failure mode | Why it fails | Required correction |
|---|---|---|
| Everything becomes a Task | Life becomes an obligation queue and Home disappears | Keep Session and candidate spaces non-canonical by default |
| Home writes Task state | Creates a second Orchestrator authority | Use authenticated Command and canonical Rust writer |
| Relationship grants authority | Intimacy becomes a security bypass | Separate relationship facts from actor/permit authority |
| Resident means always sensing | Backend lifecycle becomes surveillance | Separate running, presence, sensing, recording, retention, and memory |
| Every chat becomes Memory | Raw context becomes permanent and misleading | Explicit candidate, selection, scope, retention, and promotion |
| Reflection edits identity or policy | One model interpretation becomes irreversible truth | Evidence, review, versioning, and supersession |
| VCPToolBox becomes identity | Body replacement destroys continuity | Keep portable identity and governance assets above body-specific runtime |
| Home stores all content | Creates a privacy-heavy second data platform | Use references and existing content authorities |
| One global trust score | Complex relationships become manipulable rank | Preserve typed, contextual, disputable relationship facts |
| Prompt equals identity | Model/session change silently resets the person | Bind identity to canonical facts, charter, memory, relation, and history |

## 17. Future Contract Map

Recommended contract order remains dependency-driven:

```text
Actor Identity and Delegation
-> Resident Identity Continuity Minimum
-> Memory / Session / Artifact Boundary Minimum
-> Governed Memory Access
-> Home-to-Orchestrator Minimum Interface
-> Presence Consent and Device Observation Minimum
-> Relationship Fact Minimum
```

This order is not implementation authorization. Construction Readiness Review
may reorder or bundle contracts when it records complete dependencies and exact
acceptance units.

## 18. Jenn Final Review Surface

The decisions proposed by this direction are:

```yaml
proposed_direction:
  Home_Domain_classification: logical_bounded_context
  Home_Domain_is_Authority_Kernel: false
  Home_Domain_is_second_Task_Ledger: false
  Home_Domain_may_directly_write_Orchestrator_state: false
  ordinary_Session_auto_taskification: forbidden
  automatic_Memory_promotion: forbidden
  relationship_permission_inheritance: forbidden
  Resident_running_implies_Presence: false
  VCPToolBox_is_first_body: true
  VCPToolBox_is_life_identity: false
  replaceable_body_direction: adopted

G1B:
  result: PROPOSED_FINAL_DRAFT
  acceptance_authority: Jenn
  implementation_authorized: false
  runtime_activation_authorized: false
```

Open questions intentionally deferred from this direction:

```text
exact canonical writer and schema for relationship facts
exact identity record and actor-binding protocol
exact memory bridge and candidate reducer
exact Presence consent record and device-report protocol
exact Home-to-Orchestrator command envelope
exact portability and migration protocol
```

The next permitted action after author closeout is a fresh Phase 1C independent
review of fixed subject bytes and an explicit input allowlist. This subject does
not authorize that review to accept the direction on Jenn's behalf.

## 19. Non-Authorization

This document does not authorize:

```text
Phase 1C or Phase 2 automatic start
implementation or runtime activation
database creation, migration, or schema work
VCPToolBox, VCPChat, or VCPMobile source changes
service, plugin, provider, shell, device, or executor execution
secret or private raw-memory access
Presence, recording, or sensing activation
formal identity, relationship, or Memory mutation
commit or push
```
