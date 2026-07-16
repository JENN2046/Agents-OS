# AGENTS OS Goal Specification / Success Criteria / Plan Membership v0.1

```yaml
document_type: foundation_contract
acceptance_unit_id: F1
project: AGENTS OS
version: v0.1
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
pending: hash_bound_independent_review_and_Jenn_acceptance
implementation_authorized: false
runtime_activation_authorized: false
database_change_authorized: false
```

## 1. Status and authority

This document closes the first Phase 4 foundation contract unit:

```text
F1 Goal Specification / Success Criteria / Plan Membership
```

It specializes, but does not replace, the accepted Resident architecture. If
this draft conflicts with an accepted or frozen input before Jenn accepts F1,
the accepted or frozen input wins and the conflict is a review finding.

This contract does not:

```text
accept itself
authorize implementation
create a database or migration
start F2
add a sixth formal core object
modify Goal, Task, Run, Validation, or Event lifecycle contracts
change Task Dependency v0.1
change frozen Scheduling / Time / Capacity v0.1
```

The formal core objects remain:

```text
Goal
Task
Run
Validation
Event
```

Records named in this contract are immutable revision values, Event payloads,
current-state projections, or read-only derived projections. They are not new
formal core objects.

## 2. Problem being closed

The accepted architecture already establishes Goal lifecycle, Jenn and Nobao
authority, plan progress, Critical Work Frontier, Task Dependency, and Goal
closure assurance. It does not yet define the deterministic contract for:

```text
which Goal specification revision is current
which success criteria belong to that revision
how a criterion retains identity across revisions
which plan revision is current
which Task belongs to which Goal, criterion, and route
how plan membership is added, removed, replaced, or decomposed
how shared Task membership remains compatible with Task Dependency v0.1
which exact facts a Goal completion decision must bind
```

Without F1, downstream contracts can mention a Goal or membership but cannot
prove that they read the same current specification and plan.

## 3. Inherited invariants

F1 inherits these rules without amendment:

```text
Jenn owns final top-level Goal change, closure, outcome, and reopen authority.
Nobao may clarify and plan a top-level Goal but may not lower or replace its
  success criteria without Jenn's decision.
Nobao may create, maintain, and close Subgoals within the accepted parent
  direction.
Goal lifecycle and outcome remain separate.
Plan progress measures current plan completion, not Goal success.
Run success does not complete Task.
Task completion does not satisfy a Goal criterion by itself.
Plan progress 100% does not close Goal.
Goal closure never trusts an asynchronous projection.
Home Domain, Memory, UI, planner, host, Worker, and Domain Agent are not
  canonical Goal or plan writers.
Rust remains the canonical Orchestrator writer.
Current State and immutable Event are written in the same transaction.
```

## 4. Fact authority

| Fact class | Semantic decision authority | Canonical writer | Proposal-only actors |
|---|---|---|---|
| top-level Goal intent, boundary, and success criteria | Jenn | Resident Rust core | Nobao, Domain Agent |
| top-level implementation plan and route selection within unchanged criteria | Jenn or Nobao | Resident Rust core | Domain Agent, Worker, planner |
| Subgoal intent, boundary, criteria, and plan within parent direction | Nobao; Jenn may override | Resident Rust core | Domain Agent, Worker |
| Goal specification current pointer | authority-checked Command | Resident Rust core | none |
| Goal plan current pointer and membership | authority-checked Command | Resident Rust core | planner and UI may propose only |
| Task lifecycle | inherited Task authority | Resident Rust core | F1 never writes it indirectly |
| criterion assessment proposal | Nobao or an allowed deterministic policy | Resident Rust core as Event fact | Domain Agent, Validator |
| top-level achieved decision | Jenn only | Resident Rust core | Nobao submits completion review |
| Subgoal achieved decision | Nobao; Jenn may override | Resident Rust core | Domain Agent |
| plan progress and Goal support | none; derived | Rust projection | UI reads only |

Authority and relationship remain separate. A close relationship, a model
identity, Memory content, or a Domain Agent role does not grant Goal mutation
authority.

## 5. Identity and revision model

### 5.1 Stable identities

```yaml
stable_identities:
  goal_id: stable_for_the_whole_Goal_lifetime
  criterion_id: stable_for_one_semantic_success_criterion_lineage
  plan_id: stable_for_one_Goal_plan_lineage
  membership_id: stable_for_one_Task_membership_lineage_within_one_Goal
  route_group_id: stable_for_one_alternative_route_lineage
  frontier_member_id: stable_for_one_member_lineage_inside_one_route_group
```

An ID is never reassigned to a different semantic subject. Replacement creates
a new ID and records the replaced ID. A corrected description of the same
subject keeps the stable ID and advances its revision.

### 5.2 Revision rules

```text
GoalSpecRevision is monotonic per goal_id.
SuccessCriterion revision is monotonic per criterion_id.
GoalPlanRevision is monotonic per goal_id and plan_id.
GoalPlanMembership revision is monotonic per membership_id.
Route group revision is monotonic per route_group_id.
Frontier member revision is monotonic per frontier_member_id.
```

Every accepted mutation appends immutable values and an Event. Old revisions
are never edited or deleted. Current pointers are canonical Current State and
may change only in the same transaction as the corresponding Event.

Revision numbers are positive integers. The first revision is `1`; a new
revision is exactly the current revision plus one. Gaps, caller-selected
revision numbers, and revision rollback are rejected.

### 5.3 Aggregate compare-and-set

Every mutating Command must bind:

```yaml
command_id:
actor_context_ref:
goal_id:
expected_goal_aggregate_version:
expected_goal_spec_revision: optional
expected_goal_plan_revision: optional
operation:
reason:
```

Rust verifies identity, authority, current pointers, and expected aggregate
version in one transaction. A stale Command fails without partial mutation.
Idempotent replay of the same `command_id` returns the original committed
result; reuse with different bytes is rejected.

## 6. GoalSpecRevision

### 6.1 Contract shape

```yaml
GoalSpecRevision:
  goal_id:
  goal_spec_revision:
  goal_kind: TOP_LEVEL | SUBGOAL
  parent_binding: null | ParentGoalBinding

  intent_summary:
  scope_summary:
  in_scope: []
  out_of_scope: []
  constraint_refs: []
  success_criterion_refs: []
  unresolved_question_refs: []

  completeness: CLARIFYING | COMPLETE
  authority_basis_ref:
  created_by_actor_ref:
  created_at_event_sequence:
  supersedes_goal_spec_revision: null | integer
  canonical_fingerprint:
  sensitivity: LOW_DISCLOSURE_LEDGER_FACTS_ONLY
```

This is a contract shape, not an implementation schema.

### 6.2 Low-disclosure boundary

Ledger fields contain the minimum operational meaning required to govern the
Goal. Raw private conversation, private Memory, secret material, provider raw
response, and long sensitive narrative are forbidden.

Rich or sensitive material stays with its governed owner and is referenced by
typed low-disclosure `ArtifactRef` or Memory handle. A reference never grants
read authority.

### 6.3 Completeness

`CLARIFYING` is valid when the Goal is still being made precise. It may contain
unresolved questions and an incomplete criterion set.

`COMPLETE` requires:

```text
nonempty intent_summary
an explicit in-scope / out-of-scope boundary, even when either list is empty
at least one current required success criterion
no unresolved question marked blocking for Goal readiness
valid authority basis
valid parent binding for a Subgoal
```

The Goal lifecycle gate is:

```text
GoalSpecRevision.completeness != COMPLETE
  -> Goal may remain CLARIFYING
  -> READY / ACTIVE / COMPLETION_REVIEW / CLOSED + ACHIEVED rejected

GoalSpecRevision.completeness == COMPLETE
  -> completeness alone does not change lifecycle
```

### 6.4 ParentGoalBinding

```yaml
ParentGoalBinding:
  parent_goal_id:
  parent_goal_spec_revision:
  parent_criterion_refs: []
  delegation_basis_ref:
```

A Subgoal must bind one current parent Goal and the parent direction it serves.
It cannot bind itself or form an ancestor cycle. A parent spec revision does not
silently rewrite the Subgoal. Rust derives `PARENT_ALIGNMENT_REVIEW_REQUIRED`
until Nobao carries forward, revises, supersedes, or closes the Subgoal under
current authority.

This review requirement does not automatically change either Goal lifecycle or
outcome and does not grant the child authority over the parent.

### 6.5 Spec mutation authority

Top-level Goal:

```text
Nobao may create and revise CLARIFYING material as a proposal-backed revision.
Jenn's explicit expression is required to establish or change the COMPLETE
  intent, scope boundary, constraints, or success criterion set. When Jenn's
  current expression is already clear, it is the authority basis and Nobao may
  register it directly without manufacturing an additional confirmation step.
Nobao may normalize wording without semantic change only when the Command binds
  the Jenn-authorized semantic basis and Rust records NORMALIZATION_ONLY.
Any ambiguity about semantic equivalence fails closed to Jenn review.
```

Subgoal:

```text
Nobao may create and revise the complete specification within the bound parent
  direction.
A change that expands beyond, contradicts, or replaces the parent direction is
  rejected and requires a parent Goal amendment by the proper authority.
```

Jenn may override or amend any Goal through a new revision and Event. Historical
bytes remain unchanged.

## 7. SuccessCriterion

### 7.1 Contract shape

```yaml
SuccessCriterionRevision:
  goal_id:
  criterion_id:
  criterion_revision:
  criterion_summary:
  required: true | false
  evaluation_mode: HUMAN_JUDGMENT | DETERMINISTIC_POLICY
  decision_authority: JENN | NOBAO | RUST_POLICY
  evidence_expectation_refs: []
  deterministic_policy_ref: optional
  authority_basis_ref:
  created_by_actor_ref:
  created_at_event_sequence:
  supersedes_criterion_revision: null | integer
  replaces_criterion_ids: []
  canonical_fingerprint:
```

The current criterion set is the exact normalized, duplicate-free set
referenced by the current `GoalSpecRevision`, sorted by stable `criterion_id`
for fingerprinting. Presentation order, when needed, is separate non-authority
metadata. A criterion not carried forward is historical; it is not deleted.

### 7.2 Authority constraints

```text
TOP_LEVEL + HUMAN_JUDGMENT
  -> decision_authority = JENN

SUBGOAL + HUMAN_JUDGMENT
  -> decision_authority = NOBAO unless Jenn explicitly retains the decision

DETERMINISTIC_POLICY
  -> policy must be accepted, versioned, current, and explicitly named in the
     criterion revision
  -> absence, incompatibility, or conflicting evidence produces INDETERMINATE
  -> no hidden heuristic or model judgment may impersonate RUST_POLICY
```

Nobao and Domain Agents may submit evidence-backed assessment proposals. A
proposal is not the authoritative current decision.

### 7.3 Current criterion decision

Criterion satisfaction is not stored as a mutable boolean on the criterion.
It is reduced from immutable decision Events against the current criterion
revision:

```yaml
SuccessCriterionDecisionValue:
  goal_id:
  goal_spec_revision:
  criterion_id:
  criterion_revision:
  decision: SATISFIED | UNSATISFIED | INDETERMINATE
  decision_authority:
  actor_or_policy_ref:
  evidence_refs: []
  based_on_plan_revision: optional
  based_on_event_sequence:
  decision_event_id:
```

Currentness requires exact Goal spec and criterion revisions plus current
evidence under the criterion's evaluation contract. A spec or criterion change
does not rewrite an old decision. Rust recomputes the projection and returns
`INDETERMINATE` until a compatible carry-forward rule or a new decision exists.

### 7.4 Top-level completion review

Nobao may record an evidence-backed proposal that a top-level criterion appears
satisfied and may move an eligible Goal to `COMPLETION_REVIEW`. That proposal
does not become a Jenn-authoritative `SATISFIED` decision.

`CLOSED + ACHIEVED` for a top-level Goal requires Jenn's Command. The same Rust
transaction must either:

```text
verify current Jenn-authoritative SATISFIED decisions for every required
  criterion
```

or:

```text
append Jenn-authoritative SATISFIED decisions for the exact current criterion
  revisions as part of the close decision
```

No model, UI, projection, Task completion, or plan percentage may synthesize
Jenn's decision.

### 7.5 Criterion change effects

A criterion revision or set change:

```text
creates a new GoalSpecRevision
never mutates old criterion or decision Events
invalidates current closure eligibility until current decisions and route
  support are rebuilt
may require a new GoalPlanRevision
does not automatically reopen a closed Goal
does not automatically reopen, cancel, or fail any Task
does not silently erase an open closure evidence challenge
```

Changing, removing, weakening, or replacing a required top-level criterion is a
Jenn-only semantic decision. A plan revision cannot perform it indirectly.

## 8. GoalPlanRevision

### 8.1 Full-snapshot rule

Each plan revision is a complete immutable snapshot of the current plan, not a
delta that requires guessing prior membership.

```yaml
GoalPlanRevision:
  goal_id:
  goal_spec_revision:
  plan_id:
  plan_revision:
  membership_refs: []
  criterion_route_refs: []
  supplemental_plan_membership_refs: []
  superseded_challenge_refs: []
  replacement_evidence_refs: []
  change_summary:
    added_membership_refs: []
    removed_membership_refs: []
    replaced_membership_pairs: []
    carried_forward_membership_refs: []
  reason:
  authority_basis_ref:
  created_by_actor_ref:
  created_at_event_sequence:
  supersedes_plan_revision: null | integer
  canonical_fingerprint:
```

One Goal receives at most one `plan_id` in v0.1, allocated with its first plan
revision and retained for all later revisions. A plan is current only because
the Goal current pointer names its exact revision; no mutable or embedded status
field establishes currentness.

### 8.2 Plan existence

A `CLARIFYING` or `READY` Goal may have no current plan. An `ACTIVE` Goal may
temporarily have no usable plan, but health then reports the existing
`CURRENT_PLAN_UNAVAILABLE` evidence gap. Absence does not authorize invention of
work.

No current plan or no progress-eligible Task yields:

```text
plan_progress = null
```

not a fabricated `0%`.

### 8.3 Plan authority

```text
Jenn or Nobao may revise an implementation plan when the Goal specification is
  unchanged.
Nobao may revise a Subgoal plan within the parent binding.
Domain Agents, Workers, planner, Dashboard, VCPChat, and VCPMobile may submit
  proposals only.
A plan Command that semantically changes Goal scope or criteria is rejected and
  redirected to Goal spec authority.
```

## 9. GoalPlanMembership

### 9.1 Contract shape

```yaml
GoalPlanMembershipRevision:
  membership_id:
  membership_revision:
  goal_id:
  goal_spec_revision:
  plan_id:
  plan_revision:
  task_id:

  criterion_binding: null | CriterionBinding
  route_binding: null | RouteBinding
  parent_membership_ref: optional
  plan_role: SELECTED_CRITERION_ROUTE | UNSELECTED_ALTERNATIVE_ROUTE | SUPPLEMENTAL_PLAN_WORK

  authority_basis_ref:
  created_by_actor_ref:
  created_at_event_sequence:
  supersedes_membership_revision: null | integer
  canonical_fingerprint:
```

```yaml
CriterionBinding:
  criterion_id:
  criterion_revision:

RouteBinding:
  route_group_id:
  route_group_revision:
  frontier_member_id:
  frontier_member_revision:
```

One membership belongs to exactly one Goal and one Task. A `membership_id` may
not be moved to another Goal or Task. Replacing the Task creates a new
membership lineage and records the old/new pair in the plan revision.

### 9.2 Membership currentness

A membership is current only when it is referenced by the current full-snapshot
plan revision and all of these bindings match:

```text
goal_id
goal_spec_revision
plan_id and plan_revision
criterion_id and criterion_revision when present
route group and frontier member revisions when present
task_id
```

There is no direct `add_member`, `remove_member`, or `set_member_current`
mutation. Adding, removing, replacing, rebinding, or decomposing a member
requires a new `GoalPlanRevision` in one transaction.

### 9.3 Carry-forward

An unchanged membership may be carried forward by reference only if its full
semantic binding remains valid for the new plan revision under an explicit
compatibility rule. Because the membership value binds `plan_revision`, normal
carry-forward creates the next membership revision with the same stable
`membership_id` and records `supersedes_membership_revision`.

Rust computes the normalized membership and plan fingerprints. Caller digests
are hints only.

### 9.4 Removal and replacement

Removing a membership:

```text
does not delete or cancel the Task
does not change Task lifecycle
does not erase Task history, Validation, completion refs, or Events
does not resolve an assurance challenge by omission
does remove the Task from this Goal's current plan projection after commit
```

A `CANCELLED` Task remains in the current plan until a new plan revision
explicitly removes or replaces its membership and states the success-criterion
impact.

If a current Dependency commitment, snapshot, completion support, or unresolved
challenge references the membership, the plan revision must explicitly carry
forward, replace, or supersede the reference using the accepted dependency and
closure-assurance rules. Missing treatment fails closed.

### 9.5 Decomposition and leaf identity

Task parentage alone does not silently change plan counting. A plan revision
expresses decomposition by giving child memberships a `parent_membership_ref`.

For the current plan:

```text
a current membership with at least one current child membership is a container
a current membership with no current child membership is a leaf
the same Task cannot be both a counted parent and counted child
parent/child cycles are rejected
```

A child membership must remain inside the same Goal and either the same
criterion route as its parent or the same supplemental-work lineage. Mixing a
selected parent with unselected-alternative children, or crossing route groups
through parentage, is rejected.

Removing all children does not revive the parent as counted work unless the new
plan revision explicitly carries the parent as progress-eligible current work.

## 10. Criterion routes

### 10.1 Route expression

F1 preserves the accepted expression:

```text
criterion
  -> ANY_OF route_groups

route_group
  -> ALL_OF frontier_members
```

Route and member values are embedded versioned plan values, not new formal
objects.

```yaml
CriterionRouteRevision:
  goal_id:
  goal_spec_revision:
  criterion_id:
  criterion_revision:
  route_group_id:
  route_group_revision:
  route_kind: TASK_BACKED | DIRECT_CRITERION_DECISION
  frontier_member_refs: []
  selected_for_current_plan: true | false
  authority_basis_ref:
  canonical_fingerprint:
```

```yaml
FrontierMemberRevision:
  frontier_member_id:
  frontier_member_revision:
  member_kind: TASK_PLAN_MEMBERSHIP | CURRENT_CRITERION_DECISION
  membership_ref: optional
  criterion_decision_binding: optional
  canonical_fingerprint:
```

### 10.2 Selected route

Every current required criterion that is not authoritatively satisfied should
have at least one route group. Missing or incomplete mapping produces the
accepted Goal Health evidence-gap semantics; it does not invent a route.

At most one route group per criterion is selected in one current plan revision.
Changing selection requires a new plan revision. Rust never automatically
chooses the fastest, cheapest, or easiest alternative.

For `TASK_BACKED`:

```text
frontier_member_refs must be nonempty
every member must resolve to a current Task plan membership for the same Goal,
  criterion, route group, and revision
selected route members use plan_role SELECTED_CRITERION_ROUTE
unselected route members use plan_role UNSELECTED_ALTERNATIVE_ROUTE
```

For `DIRECT_CRITERION_DECISION`:

```text
the route has exactly one CURRENT_CRITERION_DECISION member
it contains no Task membership
it is satisfied only by a current authoritative SATISFIED criterion decision
it does not create plan progress by itself
```

This supports a genuine human acceptance criterion without manufacturing a
fake Task solely to make the graph nonempty.

### 10.3 Route switching

Switching from one alternative to another:

```text
creates a new plan revision
records old and new route refs
updates membership roles through new membership revisions
does not cancel old Tasks automatically
does not clear old completion challenges
recomputes Priority context for affected Task memberships
recomputes health and time projections from the new current facts
```

## 11. Shared Task semantics

F1 does not assume one Task can serve only one Goal.

```text
standalone Task
  -> zero current Goal memberships

single-Goal Task
  -> one or more current membership lineages whose distinct goal_id set has
     exactly one member

shared Task
  -> current memberships in more than one Goal
```

Plan progress counts a shared Task independently in each Goal whose current
plan includes it. This is a statement about each Goal's plan, not duplicated
execution.

F1 does not weaken Task Dependency v0.1:

```text
any Task that is an endpoint of a current dependency spec, snapshot, binding,
or commitment may not receive a second current Goal membership
legacy discovery of such sharing remains fail-closed and INDETERMINATE
shared work that needs dependencies uses Goal-specific wrapper or replacement
Tasks through a new plan revision
cross-Goal dependency remains excluded
```

For this guard, Goal-sharing cardinality is the number of distinct current
`goal_id` values, not the number of route or criterion membership rows inside
one Goal. Multiple same-Goal bindings remain subject to the dependency
contract's exact stable membership-ref checks.

A membership Command must synchronously check these constraints before commit.

## 12. Plan progress

### 12.1 Counting set

For one current Goal plan, the progress counting set is the deduplicated set of
`task_id` values whose current membership is:

```text
a leaf
and plan_role is SELECTED_CRITERION_ROUTE or SUPPLEMENTAL_PLAN_WORK
```

`UNSELECTED_ALTERNATIVE_ROUTE` is excluded from progress. The same Task used by
two selected criteria inside one Goal is counted once, not twice.

```text
completed = number of counting-set Tasks in DONE
total = number of counting-set Tasks
percent = floor(completed * 100 / total)
```

Only `DONE` counts as completed. If `total == 0`, the projection is `null`.
Only `completed == total` may display `100%`.

### 12.2 Projection

```yaml
GoalPlanProgressProjection:
  goal_id:
  goal_spec_revision:
  plan_id:
  plan_revision:
  completed:
  total:
  percent: null | integer
  active:
  verifying:
  blocked:
  counting_task_ids: []
  based_on_event_sequence:
```

The projection is read-only and rebuildable. It never grants closure,
admission, Priority, permit, or execution authority.

### 12.3 Revision effects

Progress may decrease after an honest plan revision. It is not frozen or
smoothed. A dependency assurance challenge does not alter the percentage;
it alters member support and closure eligibility.

## 13. Completion eligibility and closure

### 13.1 Synchronous gate

`CLOSED + ACHIEVED` uses a synchronous Rust gate over one consistent current
fact set. It does not trust Dashboard, planner, cached projection, model output,
or a previously computed percentage.

The gate binds:

```yaml
GoalClosureBasis:
  goal_id:
  goal_aggregate_version:
  goal_spec_revision:
  criterion_decision_refs: []
  plan_id:
  plan_revision:
  selected_route_refs: []
  current_membership_refs: []
  task_completion_refs: []
  completion_assurance_versions: []
  dependency_closure_fingerprint:
  open_challenge_refs: []
  closure_policy_revision:
  decision_event_sequence:
```

### 13.2 Achieved gate

All conditions are required:

```text
GoalSpecRevision is current and COMPLETE.
Every current required criterion has a current authoritative SATISFIED decision.
Every current required criterion has a current selected route.
Every selected TASK_BACKED route member is a current membership and its Task is
  DONE.
Every bound completion ref and pinned dependency ancestry is CONFIRMED.
Every selected DIRECT_CRITERION_DECISION route binds the same current
  authoritative SATISFIED decision.
No unresolved GoalClosureEvidenceChallenge affects the closure basis.
Goal lifecycle transition and actor authority are valid.
Top-level Goal actor is Jenn; Subgoal actor is Nobao or Jenn.
```

`plan_progress == 100%` is neither necessary for a plan containing only direct
criterion decisions nor sufficient for any Goal. For a Task-backed selected
plan, incomplete progress necessarily fails the achieved gate.

### 13.3 Non-achieved closure

`ABANDONED`, `UNACHIEVABLE`, and `SUPERSEDED` do not require satisfied criteria
or 100% progress. They still require valid actor authority, a reason, exact
current Goal spec binding, and an immutable Event. `SUPERSEDED` also requires a
replacement Goal ref.

Top-level authority remains Jenn. Subgoal authority remains Nobao or Jenn.

### 13.4 Post-closure change

A later completion assurance challenge does not automatically reopen a closed
Goal or rewrite its outcome. The historical closure basis remains immutable and
the closure evidence review remains visible. Jenn decides top-level reopen or
amendment; Nobao handles Subgoals within inherited authority.

## 14. Atomic command effects

### 14.1 Create Goal

One transaction creates:

```text
Goal current state
GoalSpecRevision 1
criterion revisions referenced by spec revision 1
optional GoalPlanRevision 1 and membership revisions
immutable Event
current pointers
```

If any validation fails, none are committed.

### 14.2 Revise Goal specification

One transaction:

```text
checks actor and aggregate CAS
appends changed criterion revisions
appends the complete new GoalSpecRevision
updates the current spec pointer
appends Event
marks incompatible plan / criterion decisions / closure eligibility stale by
  deterministic reduction
```

It does not silently mutate the current plan. If spec and plan must change
atomically to avoid an invalid intermediate state, one declared compound
Command may append both revisions in the same transaction; both complete
snapshots and both authority checks remain mandatory.

### 14.3 Revise Goal plan

One transaction:

```text
checks actor, Goal spec, aggregate CAS, Task identities, dependency-sharing
  constraints, route completeness, membership lineage, and challenge treatment
appends the complete new plan revision and all changed embedded revisions
updates the current plan pointer
appends Event
```

It does not create, cancel, reopen, complete, or reprioritize a Task unless a
separately authorized compound Command names those effects and each inherited
gate passes. Ordinary plan revision has no such implicit effects.

## 15. Currentness and fingerprints

Canonical fingerprints use a versioned canonicalization contract:

```text
encoding: UTF-8 canonical JSON
object keys: lexical order
arrays: stable business-key order defined by the contract
duplicates: reject
numbers: integers only
digest: SHA-256 lowercase hex
input: ledger-safe IDs, revisions, enums, and allowed low-disclosure digests
```

Forbidden fingerprint input:

```text
raw Artifact bytes
raw prompt or conversation
private Memory
secret or credential
provider raw response
caller-computed authority assertion
```

At minimum, these changes invalidate dependent currentness:

| Change | Required effect |
|---|---|
| current Goal spec revision | criterion decisions, plan compatibility, health, Priority context, and closure re-evaluate |
| current criterion revision or set | route mapping and closure re-evaluate |
| current plan revision | progress, membership support, route selection, scheduling inputs, and closure re-evaluate |
| affected membership revision | Task Priority context and any bound dependency or support gate re-evaluate |
| completion assurance version | member support and closure re-evaluate; progress unchanged |
| unrelated Goal or membership | no effect on this Goal's fingerprints |

Fail-closed means `STALE`, `REVIEW_REQUIRED`, `INDETERMINATE`, or gate rejection
according to the owning accepted contract. It never means automatic Task or Goal
failure.

## 16. Recovery and replay

On startup, before new permit or closure authority is available, Rust must be
able to verify:

```text
one current GoalSpecRevision pointer per Goal
zero or one current GoalPlanRevision pointer per Goal
monotonic revisions with no conflicting identity reuse
Current State aggregate version and last Event alignment
plan and membership fingerprints
criterion, route, and membership referential integrity
dependency-sharing restrictions
closure basis and open challenge visibility
```

Missing Event, pointer mismatch, duplicate current revision, fingerprint
mismatch, unknown contract version, or broken membership reference fails closed
for affected mutations and closure. Recovery does not repair by inventing facts
or deleting history. Reconciliation appends new Events under a separately
authorized path.

Projections may be discarded and rebuilt. Canonical revision values and Events
may not.

## 17. Rejected designs and anti-patterns

F1 rejects:

```text
mutable goal.success_criteria JSON overwritten in place
mutable task.goal_id as the only membership fact
deleting a Task from a list to hide cancellation or challenge
using plan percentage as Goal success
allowing a planner or UI to choose a route by writing Current State
letting a model declare Jenn's top-level criterion satisfied
using relationship or Memory as authority
copying raw private content into Goal ledger fields
changing a criterion through a plan revision
reusing membership_id for a replacement Task
counting the same Task twice inside one Goal progress projection
counting unselected alternative work as required current progress
automatically cancelling old-route Tasks after route switching
allowing shared dependency endpoints contrary to Task Dependency v0.1
trusting an asynchronous projection for Goal closure
editing a closed Goal's historical closure basis
```

## 18. Required implementation tests

Acceptance of F1 does not authorize these tests to be implemented. A future
authorized implementation must cover at least:

```text
GoalSpec and plan revision monotonicity, CAS, idempotency, and immutable history
TOP_LEVEL versus SUBGOAL authority positive and negative paths
CLARIFYING incomplete spec cannot become READY or ACHIEVED
top-level semantic criterion change without Jenn is rejected
Subgoal parent cycle and out-of-scope expansion are rejected
criterion identity carry-forward, replacement, retirement, and stale decision
HUMAN_JUDGMENT and DETERMINISTIC_POLICY fail-closed behavior
Nobao proposal cannot impersonate Jenn satisfaction
full-snapshot plan with explicit added, removed, replaced, and carried-forward
membership ID cannot move to another Goal or Task
membership add/remove only through a new plan revision
decomposition leaf counting and parent/child cycle rejection
selected, unselected, supplemental, and duplicate Task progress counting
zero Task plan returns null progress
100% progress does not close Goal
direct criterion route creates no fake progress
route switch leaves old Task lifecycle unchanged
shared Task progress per Goal and deduplication inside one Goal
shared dependency endpoint rejection and legacy fail-closed behavior
CANCELLED Task remains until explicit plan revision
plan revision cannot erase closure challenge by omission
completion assurance challenge leaves progress unchanged and closes eligibility
top-level achieved closure requires Jenn and exact current criterion decisions
Subgoal closure requires Nobao or Jenn
non-achieved closure does not require 100% but requires authority and reason
post-closure challenge does not auto reopen
crash replay at every Current State plus Event transaction boundary
fingerprint normalization, duplicate rejection, and unknown-version fail closed
raw private content, secret, provider output, and caller authority excluded
```

## 19. Downstream contract handoff

F1 provides stable inputs to:

```text
F4 TaskPermit / Host Authentication
F6 Validation Requirement Current Decision
F9 Home-to-Orchestrator Minimum Interface
Task Priority context
Task Dependency membership gates
Scheduling and time projections
Goal Health, progress, support, and closure
```

F1 intentionally does not define:

```text
actor authentication or delegation tokens -> F2
Resident singleton or N-API ownership -> F3
permit signing or host identity -> F4
Validation Requirement current decision reducer -> F6
Home intent-to-Command interface -> F9
database tables, indexes, or migration
runtime activation
```

## 20. Acceptance unit

F1 is one acceptance unit:

```yaml
acceptance_unit_id: F1_GOAL_SPECIFICATION_SUCCESS_CRITERIA_PLAN_MEMBERSHIP_V0_1
subjects:
  - this_exact_document_sha256_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
next_contract_start_by_acceptance: false
```

Jenn may accept, accept with a separately hash-bound amendment, request
revision, or reject. Even after acceptance, F2 requires its own explicit start
under the one-contract-at-a-time Phase 4 rule.
