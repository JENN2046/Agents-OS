# AGENTS OS | Construction Readiness Review v0.1

```yaml
document_type: ConstructionReadinessReview
project: AGENTS OS
phase: Phase 3
gate: G3
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: completed_pending_Jenn_governance_decision
G3_result: NOT_READY
implementation_authorized: false
runtime_activation_authorized: false
Phase_4_started: false
```

## 1. Review Purpose

This review determines what must be closed before the first mock-only runtime
slice. It does not design final schemas, implement Rust, create a database,
start VCPToolBox, or grant Phase 4 authority.

Fixed authority inputs include the accepted R3 roadmap, the accepted
Foundational Direction, the Phase 1A gap inventory, the Home Fact Authority
Matrix, the Home Direction, the Resident architecture, the VCP high-privilege
architecture, and the frozen Scheduling / Time / Capacity v0.1 bundle.

## 2. Executive Result

```yaml
review_outputs_complete: true
foundation_dependency_graph_complete: true
M0_A_scope_complete: true
M0_B_scope_complete: true
deferred_scope_complete: true
hard_stop_list_complete: true
validation_plan_complete: true

G3:
  result: NOT_READY
  blocker_count: 1
  technical_direction_rejected: false
  implementation_authorized: false
```

The architecture is sufficiently clear to plan contract closure. G3 cannot
truthfully return `READY_FOR_M0_CONTRACT_CLOSURE`, however, because accepted R3
requires every M0 gap to be resolved by an accepted contract or explicitly
excluded before G3 becomes ready, while Phase 4 is the phase that accepts those
contracts. This is a phase-transition cycle, not an implementation failure.

## 3. Blocking Finding

### G3-GOV-01 | Contract-closure transition is circular

```text
R3 G3 rule:
  all M0 gaps require accepted contracts or explicit exclusion before READY

R3 Phase 4 rule:
  foundation contracts are closed after G3

Consequence:
  required contracts cannot be accepted through Phase 4 until G3 is ready,
  but G3 cannot be ready until those Phase 4 contracts are accepted.
```

Required correction is a new amendment or decision record. The accepted R3
bytes must not be edited.

Recommended amendment:

```yaml
G3:
  ready_name: READY_FOR_FOUNDATION_CONTRACT_CLOSURE
  ready_requires:
    - every HD-M0 gap mapped to a declared contract acceptance unit
      or an explicit M0 exclusion
    - dependency graph complete
    - M0-A and M0-B scopes complete
    - hard stops and validation plan complete
  does_not_require:
    - contracts_already_accepted
  phase_gate_is_authorization: false

post_contract_gate:
  gate_id: G4_CONSTRUCTION_AUTHORIZATION_READINESS
  requires:
    - every contract required by the selected M0 slice accepted
    - every exclusion scope and expiry validated
    - implementation plan and test plan current
  implementation_still_requires_separate_Jenn_authorization: true
```

Rejected workaround: accept contracts outside Phase 4 while Phase 3 remains
open. That would obscure phase ownership and make later audit trails ambiguous.

## 4. Foundation Contract Dependency Graph

The R3 labels `F1` through `F8` were provisional. This review records the
readiness graph below as a proposal for the future amendment decision; it does
not accept any contract.

| Unit | Contract or atomic bundle | Depends on | Covers | Required before |
|---|---|---|---|---|
| F1 | Goal Specification / Success Criteria / Plan Membership | accepted Resident architecture | canonical Goal and plan membership facts | M0-A |
| F2 | Actor Identity / Delegation | accepted Foundational Direction | `HD-M0-01` | all authenticated M0 commands |
| F3 | Resident Singleton / N-API / Identity Continuity atomic bundle | F2 | `HD-M0-02`; single process authority, ledger-thread and connection ownership | M0-A |
| F4 | TaskPermit / Host Authentication | F1, F2, F3 | authenticated host enforcement and revocation | M0-A effect admission |
| F5 | Outbox Delivery / Recovery | F3, F4 | claim, lease, retry, dead-letter, reconciliation | M0-A crash recovery |
| F6 | Validation Requirement Current Decision | F1, F3 | deterministic current Validation decision and Task completion eligibility | M0-A completion boundary |
| F7 | Home Minimum Semantics + Memory / Session / Artifact Boundary atomic bundle | F2, accepted Home Direction | `HD-M0-03`; candidates, promotion, retention and low-disclosure refs | M0-B |
| F8 | Governed Memory Access | F2, F7 | `HD-M0-04`; bridge identity, denial and low-disclosure evidence | before any real memory integration |
| F9 | Home-to-Orchestrator Minimum Interface | F1, F2, F3, F4, F7 | `HD-M0-05`; authenticated intent-to-Command handoff | M0-B |
| F10 | Presence Consent and Device Observation | F2, F4, F7 | `HD-M0-06`; sensing, recording, retention and revocation | before any Presence/device sensing slice |
| F11 | Relationship Fact Minimum | F2, F7 | `HD-M0-07`; formal writer, acknowledgement, revision and dispute | before formal relationship mutation |

Deterministic closure order:

```text
F1 + F2
-> F3
-> F4
-> F5 + F6
-> F7
-> F9

Deferred branches:
F7 -> F8
F2 + F4 + F7 -> F10
F2 + F7 -> F11
```

`F3` and `F7` are explicit atomic bundles because accepting only one half would
create an authority gap: singleton ownership without identity continuity, or
Home candidates without their data-boundary contract.

## 5. Gap Disposition

| Gap | Disposition for current M0 | Closure |
|---|---|---|
| HD-M0-01 | REQUIRED | F2 |
| HD-M0-02 | REQUIRED | F3 atomic bundle |
| HD-M0-03 | REQUIRED_FOR_M0_B | F7 atomic bundle |
| HD-M0-04 | EXCLUDED_FROM_M0_A_AND_M0_B | F8 before real memory reads/writes |
| HD-M0-05 | REQUIRED_FOR_M0_B | F9 |
| HD-M0-06 | EXCLUDED_FROM_M0_A_AND_M0_B | F10 before sensing, recording, or device observation |
| HD-M0-07 | EXCLUDED_FROM_M0_A_AND_M0_B | F11 before formal relationship mutation |

Exclusion means the capability is absent and tested as absent. It does not
mean the requirement is resolved, waived forever, or permitted without its
contract.

## 6. M0-A Scope | Deterministic Orchestrator Core

M0-A contains only:

```text
one mock-only AGENTSOSResident instance
Rust canonical writer behind a JavaScript N-API shell
temporary isolated SQLite database
Current State + Event + Inbox + Outbox transaction boundary
synthetic actor and host identities
authenticated Command acceptance and illegal Command rejection
mock host dispatch
UNKNOWN on ambiguous effect outcome
no automatic retry from UNKNOWN
crash-window replay and idempotent recovery
minimum Task completion boundary using frozen Validation decisions
```

M0-A excludes Home candidates, Memory, Presence, relationship mutation, real
providers, real secrets, active host identity, production databases, devices,
VCPMobile, audio, and runtime activation.

M0-A required contracts: `F1` through `F6`.

## 7. M0-B Scope | Home-to-Action Boundary

M0-B begins only after M0-A is `PASS` and Jenn separately authorizes M0-B.

```text
synthetic Session input
-> remain ephemeral or discard
-> explicitly proposed Life Stream candidate
-> optional synthetic Memory Candidate without formal Memory write
-> explicit intent
-> authenticated Orchestrator Command through F9
```

M0-B must prove:

```text
ordinary conversation creates no Goal or Task
Session creates no candidate automatically
Memory Candidate creates no formal Memory
relationship context grants no authority
Home Domain cannot write canonical Task state
private content does not enter Ledger evidence
```

M0-B required contracts: accepted M0-A set plus `F7` and `F9`.

## 8. Deferred Scope

```yaml
deferred_until_F8:
  - real VCP native memory read or write
  - private-memory migration

deferred_until_F10:
  - microphone or system-audio sensing
  - recording or retention
  - screen, camera, location, sensor, or device observation
  - Mobile or Audio Presence

deferred_until_F11:
  - formal relationship creation, mutation, assurance, or dispute reducer

later_than_M0:
  - Resource-constrained Scheduling v0.2
  - preemptive scheduling
  - complex solver
  - real provider and paid execution
  - production database
  - continuous sensing and AR
  - complete Agent society runtime
```

## 9. Hard Stops

```text
no Phase 4 start until Jenn resolves G3-GOV-01
no contract is accepted merely by appearing in this graph
no implementation before required contracts and a separate Jenn authorization
no runtime source or VCPToolBox core change in Phase 3
no database creation or migration
no service, plugin, provider, executor, or device activation
no production keys, active Jenn credentials, or active host identity
no private raw memory, state-private, secret, or provider raw response access
no Presence, sensing, recording, retention, or formal Memory mutation
no modification of accepted R3, Foundational Direction, or review bytes
```

## 10. Validation Plan

### Contract closure validation

```text
fixed subject hash before and after independent review
one canonical writer per fact class
no permission inheritance from relationship or capability
negative-path and denial semantics
explicit acceptance unit and dependency fingerprints
Jenn acceptance record for every contract or declared atomic bundle
Registry, federated Registry and CURRENT_STATE zero-regression checks
```

### M0-A validation scenarios

```text
two Resident instances race -> exactly one canonical owner
non-ledger thread write -> rejected
duplicate Command -> idempotent first result
same command_id with different payload -> protocol conflict
transaction crash windows -> Current State / Event / Inbox / Outbox remain atomic
mock host accepted then lost -> UNKNOWN
UNKNOWN -> no automatic retry
stale permit, host identity or fence -> rejected
restart -> recovery is repeatable and creates no duplicate effect
Validation disagreement -> deterministic current decision only
```

### M0-B validation scenarios

```text
ordinary Session -> no automatic candidate, Memory, Goal or Task
candidate rejection/discard -> no retained authority
Memory Candidate -> no formal Memory write
relationship claim -> no permission expansion
Home direct Task write attempt -> rejected
authorized intent -> exactly one authenticated Command
Artifact/private content -> low-disclosure reference only in Ledger
Presence/device API -> unavailable in this slice
```

## 11. Final G3 Reduction

```yaml
all_outputs_present: true
all_HD_M0_gaps_mapped_or_explicitly_excluded: true
required_contracts_already_accepted: false
R3_current_READY_condition_satisfied: false

G3:
  result: NOT_READY
  blocker:
    - G3-GOV-01
  phase_gate_is_authorization: false
  Phase_4_started: false
  implementation_authorized: false
  runtime_activation_authorized: false

next_decision_surface:
  authority: Jenn
  recommended_action: ACCEPT_MINIMUM_G3_GATE_AMENDMENT_V0_1
```

The recommended amendment changes only phase-gate semantics. It does not accept
F1-F11, start Phase 4, authorize implementation, or activate runtime.
