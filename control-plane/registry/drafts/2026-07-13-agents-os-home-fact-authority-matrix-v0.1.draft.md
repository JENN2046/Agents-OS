# AGENTS OS | Home Fact Authority Matrix v0.1

```yaml
document_type: fact_authority_matrix
project: AGENTS OS
phase: Home Domain Phase 1A
version: v0.1
date: 2026-07-13
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
```

## 1. Reading Rules

This matrix records current authority, not desired implementation. Values mean:

```text
ESTABLISHED
  current authority is supported by accepted or current registered material

TARGET_ACCEPTED_NOT_IMPLEMENTED
  architecture owner is accepted, but no live implementation is claimed

UNRESOLVED
  current sources do not establish one writer or physical location

CANDIDATE_ONLY
  the object or fact may be proposed but is not canonical
```

`Trigger action` means whether the fact alone may cause an Orchestrator or
external action. Almost all Home facts require a separate authorized Command.

## 2. Required Fact Classes

| ID | Fact class and meaning | Canonical writer | Reporters only | Logical storage authority | Current physical location | Trigger action alone | Jenn final authority | Status / gap |
|---|---|---|---|---|---|---|---|---|
| HF-01 | Stable identity facts: identity ID, identity revision, active/retired state | Jenn confirms root identity; future deterministic writes assigned to `AGENTSOSResident` Authority/Control functions | model sessions, prompts, hosts, Agents | Root governance plus future Resident identity authority | Root `AGENTS.md` and accepted decisions establish meaning; runtime record is `UNRESOLVED` | No | Yes | `TARGET_ACCEPTED_NOT_IMPLEMENTED`; `HD-M0-01`, `HD-M0-02` |
| HF-02 | Identity narrative and self-interpretation | The identified Agent may author `self_record`; Jenn accepts root identity changes | model/session may propose narrative | Selected Memory or identity charter, not Task Ledger | Root AGENTS is active contract; labs charter is interpretive draft; memory location `UNRESOLVED` | No | Yes for root identity | Narrative must not overwrite HF-01 |
| HF-03 | Formal relationship fact: recognized relation, scope, revision, dispute state | `UNRESOLVED`; future writer must require affected-party visibility and Jenn authority where root governance changes | involved Agents may propose, acknowledge, dispute, or pause | Formal relationship governance memory, separate from permission | Policy files exist; concrete canonical store `UNRESOLVED` | No | Yes for formal/root relation | `HD-M0-07` |
| HF-04 | Subjective relationship memory: one Agent's own feeling or interpretation | The identified Agent as `self_record`, subject to memory governance | other Agents may respond but cannot rewrite it | Agent specialized memory | `UNRESOLVED`; private contents not inspected | No | Yes for personal retention/official promotion | Must not become another Agent's formal memory |
| HF-05 | Presence policy: allowed semantic levels and hard boundaries | Jenn through accepted/registered governance process | Agents and devices may propose policy change | Governance policy | `control-plane/policies/life-core/presence-and-sensing.md` | No | Yes | `ESTABLISHED` as policy only |
| HF-06 | Presence consent instance: who, surface, scope, level, duration, revocation, retention | Jenn or authenticated consent authority acting from Jenn's explicit choice; exact writer `UNRESOLVED` | UI/device may report consent interaction | Future Presence consent authority, not Memory or Task Ledger | `UNRESOLVED` | No, it only permits bounded observation | Yes | `HD-M0-06` |
| HF-07 | Current device sensing state: sensor/mode actually active on a device | Corresponding authenticated execution host for physical fact; future Resident accepts and versions report | VCPChat/VCPMobile UI projections | Host operational state; accepted version/ref in Resident when implemented | VCPChat/VCPMobile runtime is the architectural host; current AGENTS OS record `UNRESOLVED` | No | Jenn may disable/revoke | `TARGET_ACCEPTED_NOT_IMPLEMENTED`; `HD-M0-06` |
| HF-08 | Session content: temporary conversation and current working context | Session host for transient content | participating models/Agents | Session authority, not Memory and not GlobalTaskLedger | Concrete cross-surface contract `UNRESOLVED` | No | Yes for retention and use | `HD-M0-03` |
| HF-09 | Life Stream candidate: non-task thought, open thread, observation, or possible future intent | Candidate creator only; no canonical fact writer established | Jenn, Nobao, Domain Agents may propose | Future Home Domain candidate space | `UNRESOLVED`; object name and storage not frozen | No | Yes for promotion/discard | `CANDIDATE_ONLY`; required before M0-B |
| HF-10 | Memory content: selected semantic continuity item and lifecycle | VCP native memory runtime | Agents and tools may propose or query through governance | VCP native memory | Architectural authority established; live contents/location not inspected | No | Yes for personal long-term memory and root changes | `TARGET_ACCEPTED_NOT_IMPLEMENTED` for AGENTS OS integration; `HD-M0-03` |
| HF-11 | Memory access authority: who may read/write which memory scope | Governed memory bridge; exact issuer/verifier `UNRESOLVED` | VCP native memory reports availability/result | Governed bridge plus low-disclosure audit evidence | `UNRESOLVED` | No | Yes | `HD-M0-04` |
| HF-12 | Memory Candidate: proposed memory not yet accepted | Candidate proposer; promotion decision remains separate | Session/Home/Agent may submit candidate | Candidate space, not official Memory | `UNRESOLVED` | No | Yes for personal/formal promotion | `CANDIDATE_ONLY`; `HD-M0-03` |
| HF-13 | Intent candidate: a possible request to act | Jenn or Nobao may form a candidate within their authority; exact Home writer `UNRESOLVED` | Session, Memory, or Agent may supply context only | Home Domain candidate space | `UNRESOLVED` | No | Yes for Jenn-only scope | `CANDIDATE_ONLY`; `HD-M0-05` |
| HF-14 | Authorized Orchestrator Command: authenticated request for canonical action | Authorized actor creates command; future Rust core validates and accepts/rejects it | Home Domain, UI, Agent, and host may submit but cannot self-accept | Orchestrator Inbox/Event authority | Accepted target is `AGENTSOSResident`; implementation not started | Yes, only after authentication and admission | Yes for Jenn-only actions | `HD-M0-01`, `HD-M0-05` |

## 3. Additional Foundation Facts

| ID | Fact class and meaning | Canonical writer | Reporters only | Logical storage authority | Current physical location | Trigger action alone | Jenn final authority | Status / gap |
|---|---|---|---|---|---|---|---|---|
| HF-15 | Growth Event: observed action/outcome proposed for learning | Event observer may report; accepted event writer `UNRESOLVED` | Agents, Review, Validation | Project or specialized memory candidate space | `UNRESOLVED` | No | Yes for formal promotion | Candidate only; no personality mutation |
| HF-16 | Accepted learning or behavior-policy revision | Jenn or delegated policy authority after evidence/review; exact class rules `UNRESOLVED` | reflection systems may propose | Versioned policy or selected Memory | Current policy files exist; reducer `UNRESOLVED` | No direct execution; affects later decisions after acceptance | Yes | Must be reversible and supersedable |
| HF-17 | Agent role charter | Jenn for root/long-lived role; delegated scope may propose revisions | Agent may self-interpret and propose | Governance/identity charter | Root AGENTS active; labs charter draft; Domain Agent charters not established | No | Yes | Stable identity facts must remain separate |
| HF-18 | Agent room or member state | Future resident/member authority `UNRESOLVED` | Agent may report status | Home Domain member/room state, not Task Ledger | Policy exists; runtime state `UNRESOLVED` | No | Yes for create/pause/archive/restore boundaries | M0-B or later |
| HF-19 | Capability declaration: what a host can potentially do | Corresponding host reports; Authority Kernel accepts/version-binds declaration | plugins, UI, device adapters | Capability Body/host registry | Runtime projects exist; canonical AGENTS OS binding not implemented | No | Jenn controls enablement boundaries | Capability is not permission |
| HF-20 | Task/Goal/Run/Validation canonical fact | `AGENTSOSResident` Rust core, except Jenn/Nobao command authority as already accepted | Home Domain, hosts, Agents, UI | Canonical GlobalTaskLedger | Accepted architecture; implementation not started | Through formal Command only | Yes according to accepted Goal authority | Home Domain must never become a second writer |
| HF-21 | Artifact bytes and retention | Corresponding storage authority | Agent/Task/Memory may reference through `ArtifactRef` | Artifact store | Per-artifact physical location; no universal store established | No | Yes where personal/private | Artifact is not Session, Memory, or Ledger state |
| HF-22 | Home projection or dashboard view | No canonical writer; deterministic projection builder only | all canonical authorities provide bounded inputs | Rebuildable read model | Workbench/Dashboard are current candidates | No | No independent authority | Projection must never write source facts |

## 4. Cross-Fact Invariants

```text
HF-02 cannot overwrite HF-01.
HF-04 cannot establish HF-03.
HF-05 does not create HF-06.
HF-06 does not prove HF-07 is active.
HF-07 does not authorize recording or HF-10 memory creation.
HF-08 does not automatically become HF-09, HF-10, HF-12, HF-13, or HF-20.
HF-09 and HF-12 remain candidates until their own decision path succeeds.
HF-10 content authority does not grant HF-11 access authority.
HF-13 cannot trigger action until it becomes a valid HF-14 Command.
HF-15 cannot directly create HF-16.
HF-19 capability never implies permit or HF-14 authorization.
HF-22 is read-only and rebuildable.
```

## 5. G1A Matrix Conclusion

```yaml
required_fact_distinctions_covered: true
single_authority_claims_supported_only_where_established: true
future_physical_storage_invented: false
second_task_ledger_created: false
private_raw_memory_read: false
unresolved_blocking_for_home_direction: []
unresolved_blocking_for_M0:
  - HD-M0-01
  - HD-M0-02
  - HD-M0-03
  - HD-M0-04
  - HD-M0-05
  - HD-M0-06
  - HD-M0-07
G1A_result: PASS_WITH_GAPS
home_domain_drafting_allowed: true
implementation_authorized: false
runtime_activation_authorized: false
```

