# AGENTS OS | Home Domain and Construction Roadmap R2

```yaml
document_type: master_roadmap
project: AGENTS OS
version: R2
date: 2026-07-13
owner: Jenn
agent_steward: Nobao

status: proposed_final_draft_pending_final_review
current_implementation_authority: false
phase_gate_is_authorization: false
M0_requires_separate_Jenn_authorization: true
runtime_activation_authorized: false
```

## 1. Current Construction Judgment

AGENTS OS already has a comparatively mature action and governance spine:

```text
Goal
-> Plan
-> Task
-> Selection
-> Admission
-> Run
-> Validation
-> Completion
-> Recovery
```

The next phase does not replace that structure. It completes the life and
community direction:

```text
Identity
Relationship
Intent / Life Stream
Memory and Meaning
Presence and Attention
Reflection and Growth
Agent Community
Portability
```

The following is the logical architecture view, not a process, database, or
deployment containment diagram:

```text
AGENTS OS
├── Home Domain
│   └── life semantics, relationship, memory, presence, and continuity boundary
│
├── Orchestrator
│   └── Goal, Task, Run, Validation, Scheduling, and Recovery
│
├── Authority / Control Boundary
│   └── identity authority, policy, permit, and host enforcement
│
└── Capability Body
    └── VCPToolBox, Codex, VCPChat, VCPMobile, and execution hosts
```

The accepted deployment topology remains:

```text
VCPToolBox
├── AGENTSOSResident
│   ├── Home Domain logical bounded context
│   ├── Orchestrator
│   └── Authority / Control functions
└── VCP capability and runtime services

VCPChat / VCPMobile / Codex / other execution hosts
└── governed interaction or capability surfaces connected to the Resident
```

The `Authority / Control Boundary` is a logical authority boundary. It does not
declare a fourth resident, process, database, sidecar, or independent runtime.
Under the accepted architecture, its deterministic canonical duties are
expected to be implemented through the single `AGENTSOSResident` Rust core and
the required host-side enforcement points, subject to future accepted contracts.

Mandatory distinctions:

```text
Home Domain != Authority / Control Boundary
Home Domain != executable runtime kernel
Home Domain != permit issuer
Home Domain != Task canonical writer
Home Domain != second ledger
```

"Home Kernel" is retained only as a vision name. Its formal technical
classification is:

```text
logical bounded context
```

## 2. Authority Inheritance Order

Home Domain must not reinvent a parallel set of life principles.

When conflicts occur, use this order:

```text
1. Jenn's current explicit decision
2. higher-priority instructions and the root AGENTS.md operating contract
3. accepted and frozen architecture decisions
4. currently effective life-core policies
5. current source mirrors and interpretive role charters
6. historical mirrors, labs material, and superseded drafts
```

Jenn's current decision has final authority. When it changes accepted or frozen
architecture, the durable change must be materialized as a new amendment or
decision record. Previously reviewed subject bytes remain immutable historical
evidence and must not be silently rewritten.

The Home Domain Architecture Direction exists to:

```text
synthesize current life principles
define module boundaries
establish a fact-authority map
identify unresolved design gaps
map future contracts
```

It is not:

```text
a new policy engine
a new database
a second runtime
a second permission system
an implicit replacement for current life-core policy
```

## 3. Phase 0 | Qualified Freeze Closeout

### Current State

Based on the 2026-07-13 Codex read-only verification:

```yaml
phase: QUALIFIED_COMPLETE
verified_git_ref: e2edc240fd95ae5e42063874ba4d5ba424e8b4fc
verified_at: 2026-07-13T21:28:47+08:00

remote_merge_verified: true
main_origin_ahead_behind: "0/0"
tracked_tree_clean: true
unrelated_untracked_inventory_present: true
freeze_hash_verified: true

populated_workspace_validation:
  result: PASS
  document_registry: "387/387"
  docctl_doctor:
    documents: 429
    failures: 0

clean_checkout_validation:
  result: PARTIAL_NO_NEW_REGRESSION
  inherited_broken_references_present: true
  qualification_record: control-plane/registry/reviews/2026-07-13-agents-os-scheduling-time-capacity-clean-checkout-validation-qualification-v0.1.yaml

ci_status: NOT_CONFIGURED
```

The roadmap must not claim:

```text
the entire worktree is clean
the clean checkout has zero warnings
CI passed
```

Existing untracked paths and historical clean-checkout debt do not block Home
Domain documentation work, but must continue to be reported truthfully.

### G0 Result

```yaml
G0:
  result: COMPLETED_WITH_KNOWN_REPOSITORY_DEBT
  implementation_authorized: false
```

## 4. Phase 1A | Existing Life-Core Authority and Gap Map

### Objective

Before writing the Home Domain direction, determine what the existing life
principles already define and who owns each fact class.

### Outputs

```text
Life-Core Authority and Gap Map v0.1
Home Fact Authority Matrix v0.1
Conflict / duplication inventory
Unresolved foundation list
```

### Required Fact Distinctions

```text
stable identity facts
identity narrative and self-interpretation

formal relationship facts
subjective relationship memory

Presence consent
current device sensing state

Session content
Life Stream candidate

Memory content
Memory access authority

Intent candidate
authorized Orchestrator Command
```

For every fact class, record:

```text
semantic meaning
unique canonical writer
which actors may only report facts
logical storage authority
current physical location, only when already established
whether it may trigger action
whether Jenn retains final authority
```

Physical storage that is not already established must be marked `UNRESOLVED` or
`DEFERRED`, not invented during Phase 1A.

Anything that cannot be established from current authority files is marked:

```text
UNRESOLVED_BLOCKING_FOR_M0
```

Phase 1A may list candidate options separately, but must not present an option
as a current fact.

### G1A

```yaml
result:
  - PASS
  - PASS_WITH_GAPS
  - BLOCK

implementation_authorized: false
```

## 5. Phase 1B | Home Domain Architecture Direction

### Prerequisite

Phase 1A is complete and its normative input artifacts have fixed bytes and
SHA-256 digests.

### Objective

Create the upper-level Home Domain architecture direction and define:

```text
why it exists
which current policies it inherits
what it owns
what it does not own
how it connects to the Orchestrator
how it remains separate from the Authority / Control Boundary
which questions remain unresolved
```

### Core Domains

```text
Identity continuity
Relationship and trust
Intent / Life Stream
Memory and meaning
Presence and attention
Reflection and growth
Agent community
Portability and replaceable body
```

### Four Data Boundaries

```text
Ledger
  -> verifiable runtime and governance facts

Memory
  -> selected semantic continuity

Artifact
  -> content, files, and evidence

Session
  -> temporary conversation, work, and presence context
```

These are logical data-authority categories, not a requirement for one physical
database per category. Every fact class still requires one canonical writer.

### G1B

```yaml
result:
  - PROPOSED_FINAL_DRAFT
  - REVISION_REQUIRED
  - BLOCK

acceptance_authority: Jenn
implementation_authorized: false
```

## 6. Phase 1C | Hash-Bound Independent Review

### Author and Reviewer Separation

```text
Author run
-> self-review and revision
-> fix subject bytes
-> calculate SHA-256
-> finish author run

Fresh independent reviewer run
-> read only the fixed subject and explicit allowlist
-> do not read the author's scratchpad
-> verify every normative input hash
-> review the fixed subject hash
-> generate the review artifact
```

Completing the main document and review in one continuous Codex run is only:

```text
SELF_REVIEW
```

It is not an independent review.

The review artifact records at least:

```yaml
reviewer_identity:
review_run_id:
review_started_at:
review_completed_at:

subject:
  path:
  sha256:

normative_inputs:
  - path:
    sha256:
    role:

input_allowlist: []
review_result:
blockers: []
major_findings: []
minor_findings: []
```

Review result semantics:

```text
PASS_NO_BLOCKER
  -> the reviewed subject hash may proceed to Jenn's decision surface

PASS_WITH_AMENDMENTS
  -> the current subject hash may not proceed to acceptance
  -> amendments create new subject bytes and a new SHA-256
  -> the revised subject requires a new independent review

BLOCK
  -> the current subject may not proceed
```

### G1C

```yaml
result:
  - PASS_NO_BLOCKER
  - PASS_WITH_AMENDMENTS
  - BLOCK

implementation_authorized: false
```

## 7. Phase 2 | Foundational Direction Final Review and Jenn Decision

Review these together:

```text
Home Domain
Orchestrator
Authority / Control Boundary
Capability Body
Ledger / Memory / Artifact / Session
VCPToolBox first-body boundary
Nobao identity continuity
portability
```

The independent final review must answer:

```text
Does AGENTS OS remain a community home?
Does it automatically turn life into tasks?
Has a second fact authority appeared?
Can relationship bypass permission?
Does Presence drift into continuous sensing?
Does Memory drift into permanent retention of everything?
Has VCPToolBox become an irreplaceable life identity?
```

An independent review does not accept the direction. It only prepares Jenn's
decision surface.

```text
Independent final review
-> PASS_NO_BLOCKER

Jenn decision
-> ACCEPT | REVISE | REJECT
```

An acceptance must use an independent decision record that binds exact reviewed
bytes:

```yaml
decision_authority: Jenn
home_direction_sha256:
authority_map_sha256:
independent_review_sha256:
implementation_authorized: false
runtime_activation_authorized: false
```

### G2

```yaml
review_result:
  - PASS_NO_BLOCKER
  - REVISION_REQUIRED
  - BLOCK

Jenn_decision:
  - ACCEPT
  - REVISE
  - REJECT
  - NOT_YET_MADE

implementation_authorized: false
```

## 8. Phase 3 | Construction Readiness Review

The purpose is not to authorize construction. It is to determine what remains
missing before construction can begin.

Outputs:

```text
foundation contract dependency graph
M0-A scope
M0-B scope
deferred scope
hard-stop list
validation plan
```

Expected foundation contracts:

```text
Goal Specification / Plan Membership
Actor Identity / Delegation
Resident Singleton / N-API Execution Model
TaskPermit / Host Authentication
Outbox Delivery / Recovery
Validation Requirement Decision
Home Domain minimum semantic boundaries
Home-to-Orchestrator minimum interface
```

Every `UNRESOLVED_BLOCKING_FOR_M0` entry from Phase 1A must be resolved by an
accepted contract or explicitly excluded from M0 before G3 may return ready.

### G3

```yaml
result:
  - READY_FOR_M0_CONTRACT_CLOSURE
  - NOT_READY

phase_gate_is_authorization: false
```

## 9. Phase 4 | Foundation Contract Closure

Contracts advance by dependency rather than document count. The labels below
are provisional identifiers, not a frozen execution order:

```text
F1 Goal Specification / Plan Membership
F2 Actor Identity / Delegation
F3 Resident Singleton / N-API Execution Model
F4 TaskPermit / Host Authentication
F5 Outbox Delivery / Recovery
F6 Validation Requirement Decision
F7 Home Domain Minimum Semantics
F8 Home-to-Orchestrator Minimum Interface
```

```yaml
contract_order: provisional_pending_Phase_3_dependency_graph
each_contract_requires_separate_Jenn_acceptance: true
implementation_authorized: false
```

## 10. Phase 5A | M0 Deterministic Orchestrator Core

M0-A verifies only:

```text
Resident singleton
Rust canonical writer
SQLite atomic state / Event / Inbox / Outbox
authenticated Command boundary
illegal Command rejection
mock host
UNKNOWN
no automatic retry
crash recovery
```

It explicitly does not implement:

```text
Life Stream
Memory Candidate
Presence
Audio
Mobile
real provider
```

### M0 Isolation Boundary

```yaml
M0_data_boundary:
  fixtures: synthetic_or_explicitly_sanitized_only
  private_raw_memory: forbidden
  existing_VCP_memory_store_write: forbidden
  existing_task_database_write: forbidden
  database: temporary_isolated_test_database_only
  active_runtime_configuration_read_or_write: forbidden
  provider_calls: forbidden
  runtime_activation: forbidden
```

### Gate

```yaml
M0_A:
  result:
    - PASS
    - PASS_WITH_GAPS
    - FAIL

  implementation_requires_separate_Jenn_authorization: true
  runtime_activation_authorized: false
```

## 11. Phase 5B | M0 Home-to-Action Boundary

M0-B begins only after M0-A is `PASS` and Jenn separately authorizes the M0-B
implementation scope.

It verifies this non-automatic branching model:

```text
Session content
├── ephemeral_only / discard
├── remain_in_session
└── explicitly proposed Life Stream candidate
    ├── observe without promotion
    ├── discard
    ├── propose optional Memory Candidate
    └── propose authorized intent
        └── authenticated Orchestrator Command
```

No arrow above grants authority merely because content exists. An intent becomes
an Orchestrator Command only through the accepted Home-to-Orchestrator contract
and its current actor, scope, permission, and authentication rules.

M0-B must prove:

```text
ordinary conversation does not automatically become a Goal
ordinary thought does not automatically become a Task
Session content does not automatically become a Life Stream candidate
Memory Candidate does not automatically become long-term memory
relationship does not expand permission
Home Domain does not directly write Task state
```

The M0 isolation boundary from Phase 5A applies unchanged to M0-B. No real
private conversation, raw private memory, existing VCP memory store, existing
task database, provider, active runtime configuration, or runtime activation is
used.

Only:

```text
M0-A PASS
+
M0-B PASS
```

may be called:

```text
M0_PASS
```

## 12. Phase 6 | Evidence-Driven Amendments

Implementation evidence may trigger:

```text
architecture amendment
policy revision
schema simplification
timeout benchmark revision
projection removal
transaction-boundary correction
```

Frozen subject bytes must not be modified to conceal the change.

## 13. Deferred Routes

```text
Resource-constrained Scheduling v0.2
preemptive scheduling
complete Agent society runtime
Mobile / Audio Presence implementation
continuous sensing
AR
real private-memory migration
real provider
complex solver
```

Headphone and mobile remain long-term priority experience directions, but are not
normative inputs to the current Home Domain architecture contract.

## 14. Current Decision Surface

This R2 document closes only the five blocking findings from the R1 roadmap
review and the minimum consistency changes needed to keep those fixes coherent.

```yaml
roadmap_status: proposed_final_draft_pending_final_review
architecture_direction_rejected: false
independent_final_review_completed: false
Jenn_acceptance_decision_made: false
implementation_authorized: false
runtime_activation_authorized: false
database_change_authorized: false
provider_execution_authorized: false
```

The next permitted action is a hash-bound independent final review of this fixed
R2 subject and its explicitly listed normative inputs. Acceptance, contract
implementation, runtime changes, database creation, service startup, provider
execution, and runtime activation remain unauthorized.
