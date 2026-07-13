# AGENTS OS Resource-constrained Scheduling v0.2

```yaml
draft_id: agents-os-resource-constrained-scheduling-v0.2
date: 2026-07-13
status: preserved_design_draft_not_proposed_for_acceptance
acceptance_status: not_proposed
revision: R1-split
owner: Jenn
agent_steward: Nobao
inherits:
  - control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
depends_on_proposed_contracts:
  - control-plane/registry/drafts/2026-07-13-agents-os-scheduling-time-capacity-contracts-v0.1.draft.md
split_from:
  document_id: agents-os-scheduling-time-capacity-contracts-v0.1
  source_heading: Resource-constrained Scheduling v0.2
  preservation: semantic_contract_reconstruction
acceptance_bundle_membership: excluded_from_v0.1
design_readiness: deferred_known_gaps
future_acceptance_review_required: true
implementation_authorized: false
runtime_execution_authorized: false
runtime_source_change_authorized: false
database_creation_authorized: false
solver_activation_authorized: false
active_config_access_authorized: false
secret_access_authorized: false
provider_execution_authorized: false
```

## 1. Status and Prerequisites

This is the independent design artifact referenced by Section 10 of
`AGENTS OS Scheduling, Time, and Capacity Contracts v0.1`. It preserves the separately reviewable
Resource-constrained Scheduling design draft while keeping it outside the v0.1 acceptance subject. It does not claim
that the future v0.2 acceptance blockers or major findings have been resolved.

```text
PRESERVED_DESIGN_DRAFT_NOT_PROPOSED_FOR_ACCEPTANCE
DEFERRED_KNOWN_GAPS
NOT_IMPLEMENTED
NOT_ACTIVATED
NO_EXECUTION_AUTHORITY
EXCLUDED_FROM_V0_1_ACCEPT_ALL
```

Its presence in the workspace does not authorize a solver invocation, runtime import, projection rebuild, Capacity
claim, Run, permit, Outbox dispatch, host call, provider call, database migration, or source change.

Before this contract can be proposed for separate Jenn acceptance, all of the following v0.1 contracts must be
accepted, implemented in their intended layer, and supported by current recovery and negative-path evidence:

```text
Duration Estimate v0.1
Calendar v0.1
Capacity v0.1
Eligibility and Effective Ordering v0.1
Atomic Admission and Recovery v0.1
Time Critical Path v0.1
DependencyPlanningBasisSnapshot and completion-assurance reduction
host start-authority and actual STARTED semantics
```

Future acceptance must name this document revision and its exact externally recorded content digest. Acceptance of
the v0.1 package, a parent decision, a schema stub, or this file path does not accept or activate v0.2.

## 2. Inherited Boundaries

Resource-constrained Scheduling inherits these non-negotiable boundaries:

```text
Goal / Task / Run / Validation / Event remain the only formal core objects
Rust remains the only canonical ledger writer and projection-acceptance authority
planning output is read-only and grants no execution or start authority
Task Dependency remains canonical and cannot be written from a resource-order proposal
Task completion, Goal progress, Goal Health, and Goal closure remain separate
UNKNOWN is fail-closed and cannot be auto-retried or treated as free Capacity
normal execution remains NON_PREEMPTIVE
all real selection, admission, Budget, Capacity, permit, host, and P3 gates remain authoritative
all durations, instants, quantities, counters, and solver values use checked integers
floating-point comparison is forbidden in canonical normalization and gates
```

The v0.1 `DependencyPlanningBasisSnapshot`, `DurationRemainingProjection`,
`PlanningCalendarResolutionSnapshot`, Capacity facts, Deadline facts, active Run facts, and host facts are inputs. This
document cannot weaken, synthesize, repair, waive, or replace them.

## 3. Object Boundary

```text
ResourceScheduleProjection
  -> analytical, derived, read-only, and rebuildable

ResourceOrderArc
  -> solution-specific resource ordering
  -> not Task Dependency

CapacityAllocationSuggestion
  -> embedded proposal
  -> not CapacityClaim, reservation, allocation, lease, or permit

solver proposal and proof
  -> untrusted proposal evidence until exact Rust verification
```

No name above becomes a sixth formal core object.

Three supporting records are required before a solver may run under any future implementation.

```yaml
ResourceMandatoryPresenceSnapshot:
  schema_version: resource-mandatory-presence.v0.2-draft
  snapshot_id:
  planning_scope_fingerprint:
  horizon_start_utc_ms:
  horizon_end_utc_ms:
  tasks:
    - task_id:
      classification: PINNED_ACTIVE | MUST_PLACE_WITHIN_HORIZON | MODEL_WITH_TAIL_ALTERNATIVE | OUTSIDE_HORIZON_BY_LOWER_BOUND
      classification_basis_refs: []
      hard_deadline_refs: []
      dependency_planning_basis_ref:
      resource_unconstrained_earliest_start_utc_ms: optional
  based_on_event_sequence:
  input_fingerprint:
```

```yaml
ResourceObjectivePolicyRevision:
  schema_version: resource-objective-policy.v0.2-draft
  policy_id:
  policy_revision:
  goal_tradeoff_order:
    - goal_id:
      goal_plan_revision:
      ordinal:
  standalone_account_order: CANONICAL_ID_BYTES
  stability_window_ms:
  resource_schedule_max_age_ms: 60000
  time_quantum_ms:
  solver_time_limit_ms:
  parameter_value_classes:
    JENN_POLICY:
      - stability_window_ms
    JENN_POLICY_BOUNDED_BY_BENCHMARK:
      - resource_schedule_max_age_ms
      - time_quantum_ms
    PROVISIONAL_BENCHMARK_REQUIRED:
      - solver_time_limit_ms
  benchmark_evidence_refs: []
  phases:
    - phase: MINIMIZE_EXPLICIT_TAIL
      direction: LEXICOGRAPHIC_MIN
      value_contract: PER_GOAL_REQUIRED_CRITERIA_THEN_TASK_COUNT_THEN_ACTIVE_MS
    - phase: MINIMIZE_ROUTE_WORK_FINISH
      direction: LEXICOGRAPHIC_MIN
      value_contract: ROUTE_SCENARIO_WORK_COMPLETE_BY_GOAL_TRADEOFF_ORDER
    - phase: MINIMIZE_STABILITY_WINDOW_CHURN
      direction: MINIMIZE
      value_contract: CHANGED_ASSIGNMENT_COUNT
    - phase: CANONICAL_ASSIGNMENT_TIE_BREAK
      direction: LEXICOGRAPHIC_MIN
      value_contract: TASK_START_SORTED_FULL_POOL_VECTOR_UTF8_TUPLE
  decided_by: Jenn
  effective_from_event_sequence:
  semantic_fingerprint:
```

```yaml
FutureCapacityAssumptionRevision:
  schema_version: future-capacity-assumption.v0.2-draft
  assumption_id:
  assumption_revision:
  mode: CURRENT_OFFER_WINDOW_ONLY | DECLARED_POOL_CALENDAR_CEILING_WHAT_IF
  exact_pool_revision_refs: []
  capacity_accounting_key_digests: []
  coverage_start_utc_ms:
  coverage_end_utc_ms:
  decided_by: Jenn
  reason:
  effective_from_event_sequence:
  semantic_fingerprint:
```

Rust derives the mandatory-presence snapshot before model construction. Every in-scope Task appears exactly once.
`MUST_PLACE_WITHIN_HORIZON` includes every in-horizon Hard Deadline obligation and cannot use a tail escape.
`OUTSIDE_HORIZON_BY_LOWER_BOUND` requires a proven resource-unconstrained lower bound at or beyond the horizon and no
Hard boundary requiring earlier placement. Every other non-pinned Task has one explicit tail Boolean. Missing or
indeterminate scope, membership, classification, or dependency assurance makes the projection unavailable before model
construction; it is never converted into an optional interval.

Mandatory presence is closed over every unfinished predecessor whose exact current dependency planning disposition is
`FUTURE_ACTIVITY_REQUIRED`. A confirmed `CURRENT_COMPLETION_BOUNDARY` or `PINNED_COMPLETION_BOUNDARY` is a historical
zero boundary, not an unfinished interval. For tail-capable work the model enforces
`present(successor) -> present(predecessor)`, so placing an unfinished predecessor in tail forces each dependent
unfinished successor into tail. No conditional precedence may disappear while its successor remains scheduled.

## 4. ResourceScheduleProjection

```yaml
ResourceScheduleProjection:
  projection_id:
  projection_contract_version: resource-constrained-scheduling.v0.2-draft
  result_semantics: ANALYTICAL_PROJECTION
  analysis_kind: RCPSP_NONPREEMPTIVE
  planning_scope:
    mode: GLOBAL_ACTIVE_SET | ISOLATED_GOAL_WHAT_IF
    goal_contexts:
      - goal_id:
        goal_plan_revision:
        route_scenario_fingerprint:
    horizon_start_utc_ms:
    horizon_end_utc_ms:
    tail_coverage: COMPLETE | PARTIAL
  duration_scenario: OPTIMISTIC | MOST_LIKELY | PESSIMISTIC
  objective_policy_revision:
  mandatory_presence_snapshot_ref:
  future_capacity_assumption_revision_refs: []
  forecast_as_of_utc_ms:
  valid_until_utc_ms:
  time_currentness_policy_revision: ResourceObjectivePolicyRevision
  next_recompute_reasons: []
  basis:
    task_refs: []
    plan_membership_refs: []
    route_scenario_refs: []
    dependency_planning_bases: []
    derived_remaining_duration_refs: []
    task_planning_calendar_resolution_snapshots: []
    calendar_binding_revision_refs: []
    calendar_revision_refs: []
    tzdb_bindings: []
    materialization_fingerprints: []
    capacity_domain_revision_refs: []
    capacity_pool_revision_refs: []
    capacity_request_set_revision_refs: []
    host_offer_refs:
      - offer_id:
        offer_generation:
        host_session_id:
        host_fence_epoch:
        expires_at_utc_ms:
    active_run_and_claim_refs: []
    deadline_revision_refs: []
    start_authority_cutoff_refs: []
    active_stop_cutoff_refs: []
    scheduling_policy_revision:
    objective_policy_revision:
    mandatory_presence_snapshot_ref:
    future_capacity_assumption_revision_refs: []
    policy_revision_refs: []
    input_revision_refs: []
    based_on_event_sequence:
    input_fingerprint:
  solver:
    solver_trust_mode: RUST_CONTROLLED_REGISTERED_ENGINE | EXTERNAL_PROPOSAL
    engine:
    engine_version:
    model_contract_revision:
    seed:
    worker_count: 1
    time_limit_ms:
    time_quantum_ms:
    status: OPTIMAL | FEASIBLE | INFEASIBLE | MODEL_INVALID | UNKNOWN
    time_mapping_policy_revision:
    optimality_proof_ref: optional
    optimality_verifier_id: optional
    optimality_verifier_version: optional
    optimality_verification_result: NOT_PROVIDED | VERIFIED | REJECTED
    objective_phases:
      - phase: MINIMIZE_EXPLICIT_TAIL | MINIMIZE_ROUTE_WORK_FINISH | MINIMIZE_STABILITY_WINDOW_CHURN | CANONICAL_ASSIGNMENT_TIE_BREAK
        direction: MINIMIZE | LEXICOGRAPHIC_MIN
        value_contract:
        solver_status: OPTIMAL | FEASIBLE | INFEASIBLE | UNKNOWN
        value_vector: []
        best_bound: optional
        fixed_prior_phase_values: []
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE | INFEASIBLE | MODEL_INVALID
  reason_codes: []
  assignments:
    - task_id:
      mandatory_presence_classification:
      planned_start_authority_commit_utc_ms:
      modeled_active_start_utc_ms: optional
      planned_finish_utc_ms: optional
      completion_forecast_semantics: ROUTE_WORK_LOWER_BOUND | ROUTE_WORK_FORECAST
      derived_remaining_duration_ref:
      selected_active_duration_ms:
      processing_quanta:
      planned_wall_span_ms: optional
      time_mapping_policy_revision:
      continuous_planning_calendar_segment_ref:
      planning_calendar_resolution_fingerprint:
      dependency_planning_basis_fingerprint:
      capacity_forecast_basis: CURRENT_OFFER_WINDOW | DECLARED_POOL_CALENDAR_CEILING_WHAT_IF
      future_capacity_assumption_revision: optional
      capacity_demands:
        - pool_id:
          pool_revision:
          capacity_accounting_key_digest:
          request_set_id:
          request_revision:
          units:
      source: SOLVER_SUGGESTION
  unscheduled:
    - task_id:
      mandatory_presence_classification:
      reason: OUTSIDE_HORIZON_BY_LOWER_BOUND | EXPLICIT_TAIL_SELECTED | INPUT_MISSING | MODEL_INFEASIBLE | ACTIVE_FACT_UNKNOWN | UNSUPPORTED_COMPOSITE_ACTIVITY | DEPENDENCY_ASSURANCE_UNAVAILABLE
  resource_order_arcs:
    - arc_id:
      from_task_id:
      to_task_id:
      pool_id:
      solution_id:
  resource_driving_graph:
    task_ids: []
    resource_order_arc_ids: []
    bottleneck_pool_ids: []
    semantics: SOLUTION_SPECIFIC_NOT_TRADITIONAL_CRITICAL_PATH
  projected_goal_finishes:
    - goal_id:
      goal_plan_revision:
      route_scenario_fingerprint:
      target_semantics: ROUTE_SCENARIO_WORK_COMPLETE
      completion_forecast_semantics: ROUTE_WORK_LOWER_BOUND | ROUTE_WORK_FORECAST
      capacity_forecast_basis_summary: CURRENT_OFFER_WINDOW_ONLY | INCLUDES_DECLARED_FUTURE_WHAT_IF
      finish_utc_ms: optional
      coverage: COMPLETE | PARTIAL | UNAVAILABLE
      tail_coverage: COMPLETE | PARTIAL
      reason_codes: []
  computed_at_utc_ms:
```

All listed input references are exact revisions or immutable Facts. A bare Task ID, pool ID, Calendar ID, current queue
position, cached availability label, or last successful projection is insufficient. The `basis` and Rust
normalization define the canonical model fingerprint; caller-provided fingerprints are hints only.

## 5. Minimum Supported Problem

v0.2 supports only this minimum problem:

```text
leaf Task intervals
finish-to-start zero-lag Task Dependency
non-preemptive intervals
fixed integer ALL_OF renewable Capacity requests
Capacity 1 for a named exclusive resource
Calendar materialized as bounded [start, end) UTC windows
integer time quantum
one fixed Capacity-demand profile for the whole Task interval
one continuous planning-work Calendar segment containing each complete new Task interval
```

Different execution and Validation Calendars, different required Capacity profiles, an internal parallel lane, or an
unproved non-overlap makes the Task `UNSUPPORTED_COMPOSITE_ACTIVITY`. The affected projection is partial or unavailable.
The solver cannot invent a hidden sub-Task, hidden phase, profile conversion, or internal DAG. Work that must cross a
closed planning-work interval is split, preemptive, or composite and is unsupported in v0.2. A host-accepted active Run
is pinned from real current facts and is not invalidated retroactively by a later Calendar close.

Time mapping is fixed:

```text
origin = horizon_start_utc_ms
duration_q = ceil(duration_ms / quantum_ms)
window_start_q = ceil((window_start_utc_ms - origin) / quantum_ms)
window_end_q = floor((window_end_utc_ms - origin) / quantum_ms)
strict_before_q(cutoff) = ceil((cutoff_utc_ms - origin) / quantum_ms) - 1
utc_authority_commit = checked(origin + start_authority_commit_q * quantum_ms)
utc_modeled_active_start = checked(origin + modeled_active_start_q * quantum_ms)
utc_finish = checked(origin + finish_q * quantum_ms)
```

All subtraction, multiplication, addition, ceil division, and back-conversion use checked integers. Calendar windows
remain `[start, end)`. Active Duration is converted exactly once into `processing_quanta`; it is not first expanded into
wall time and then reused as processing time.

The Deadline constraints use start-authority semantics:

```text
HARD_NEW_START_AUTHORITY_CUTOFF
  -> start_authority_commit_q <= strict_before_q(cutoff)

HARD_ACTIVE_EXECUTION_STOP_CUTOFF
  -> finish_q <= strict_before_q(cutoff)
```

Equality at a strict cutoff is forbidden, and a nonpositive checked delta has no legal quantum. A planned authority
commit is not actual process start. The model also requires
`start_authority_commit_q <= modeled_active_start_q`. Unless a separately accepted host model binds a current bounded
start-grace and launch-latency contract into the solve, `modeled_active_start_utc_ms`, physical finish, and Goal finish
are lower-bound planning diagnostics. A host timestamp cannot retroactively prove start authority or physical start.

Admission Calendar and planning-work Calendar remain separate. Admission Calendar constrains the proposed
start-authority commit instant. The planning-work Calendar constrains the modeled activity interval. An ordinary
Admission Calendar close does not revoke authority already committed under v0.1; an active-stop cutoff and the current
host/permit/fence/watchdog contracts remain authoritative.

## 6. Planning Scope

`GLOBAL_ACTIVE_SET` is the only mode that may describe shared-pool contention as a global forecast. It includes:

```text
all current Goal and standalone work inside the declared horizon that may use an allowlisted shared pool
every explicit current Goal route scenario included in the solve
every mandatory FUTURE_ACTIVITY_REQUIRED predecessor
every active Run and current claim
every UNKNOWN occupancy that may consume an included accounting key
every current mandatory-presence and Hard Deadline obligation
```

The solver cannot choose an `ANY_OF` route. A Goal context must bind one explicit current route scenario covering every
unsatisfied required criterion. Missing route choice makes the affected scope unavailable.

`ISOLATED_GOAL_WHAT_IF` is a labelled counterfactual. It may analyze one Goal while omitting other future Goal work, but
it cannot claim global feasibility or global Capacity availability. It still cannot ignore real active claims or
UNKNOWN occupancy on a shared accounting key. Cross-Goal competition never creates a cross-Goal Task Dependency.

Rolling horizon is a coverage boundary, not a work-deletion or arbitrary optionality rule. Canonical Tasks remain in the
Goal plan. Outside-horizon treatment is allowed only through the mandatory-presence snapshot's proven lower-bound or
explicit tail classification. If complete scope, route, mandatory presence, or shared-pool coverage cannot be
established, the solve stops as `UNAVAILABLE` before model construction.

One concrete current `HostCapacityOffer` does not prove future availability:

```text
CURRENT_OFFER_WINDOW_ONLY
  -> proposed start-authority commit must be strictly before the exact offer expiry
  -> a non-preemptive modeled interval may finish later only under the bound Capacity/host semantics

DECLARED_POOL_CALENDAR_CEILING_WHAT_IF
  -> work after current offer expiry requires an exact Jenn-owned FutureCapacityAssumptionRevision
  -> every affected assignment and Goal finish is visibly labelled as a what-if ceiling
  -> it is never current Capacity evidence or admission authority
```

Without current offer coverage or an explicit accepted future assumption for the exact pool revisions and accounting
keys, an interval cannot be placed. Missing future coverage is not zero Capacity and not solver infeasibility.

## 7. Hard Model and Objective

The hard model contains at least:

```text
active NON_PREEMPTIVE Run exact current activity/remaining-work/claim/pool facts pinned
LEASED start authority and allocation occupancy represented without claiming actual STARTED
UNKNOWN work and claims retain full possible occupancy and are never assigned elsewhere
each present Task receives exactly one allowed assignment satisfying its complete ALL_OF request set
finish-to-start precedence derived from exact DependencyPlanningBasisSnapshot dispositions
present(successor) implies present(FUTURE_ACTIVITY_REQUIRED predecessor)
Capacity cumulative or no-overlap constraint per stable accounting key
the complete modeled activity interval lies inside one continuous planning Calendar segment
the start-authority commit lies inside its applicable admission window and offer/assumption coverage
Hard new-start-authority and active-stop cutoffs use conservative inward quantization
mandatory presence, lower-bound exclusion, and explicit tail constraints
no float, overflow, hidden default, hidden optional interval, or hidden resource conversion
```

Dependency planning assurance is mandatory. A model cannot rely only on `dependency_revision`, a cached `SATISFIED`
label, or Task state. Each exact `DependencyPlanningBasisSnapshot` binds assessment mode and outcome, dependency set,
source lifecycle and completion envelope, PinnedDoneBinding where applicable, completion ref, assurance version, fence
generation, current impact-resolution and UNAFFECTED cuts, closure fingerprint, reducer/policy revisions, Event sequence,
and semantic fingerprint.

```text
FUTURE_ACTIVITY_REQUIRED
  -> unfinished predecessor is a present activity with hard precedence

CURRENT_COMPLETION_BOUNDARY
  -> exact current DONE completion plus current CONFIRMED closure is a zero historical boundary

PINNED_COMPLETION_BOUNDARY
  -> exact immutable pinned DONE Event plus current effective CONFIRMED closure is a zero historical boundary

CHALLENGED / INVALIDATED / INDETERMINATE, stale cut, missing assurance, or missing closure
  -> stop before solve as PARTIAL / UNAVAILABLE / INDETERMINATE according to complete evidence
  -> never treat the predecessor as satisfied or zero
```

An existing POSTCOMMIT consumer may continue to use a separately confirmed pinned historical boundary after its source
reopens. The source's current lifecycle work is a distinct interval only when it is independently in the current route
or scope. The solver cannot collapse those facts or create a new PRECOMMIT binding from `PRESERVED` history.

The objective is lexicographic. Weighted scalarization and hidden default priorities are forbidden:

```text
0. satisfy the complete hard model
1. minimize explicit tail using the Jenn-defined per-Goal criteria, Task-count, and active-ms vectors
2. minimize ROUTE_SCENARIO_WORK_COMPLETE finish in the exact Jenn-declared Goal tradeoff order
3. inside the declared stability window, minimize changed assignment count
4. apply the canonical tie-break over task-id bytes, start quantum, and the full sorted pool-ID UTF-8 byte vector
```

For a global multi-Goal solve, every in-scope Goal has exactly one current ordinal. Missing, duplicated, or stale Goal
tradeoff order makes the projection unavailable. The solver cannot decide which Goal to sacrifice. Phase 2 never uses
Goal `CLOSED + ACHIEVED` semantics, Goal Deadline tardiness, or hidden business value.

Each phase is solved after fixing every prior phase's exact value vector. Overall `OPTIMAL` is valid only when every
phase is `OPTIMAL` and those prior values are demonstrably fixed. An external proposal is at most `FEASIBLE` unless a
content-addressed proof is verified by the exact registered Rust verifier against the engine, model contract, input
fingerprint, phase order, direction, and value contract. An unknown proof or verifier cannot be downgraded into an
optimality claim.

`INFEASIBLE` is accepted only when the complete mandatory hard model was formed and proven unsatisfiable. It does not
set Task `FAILED`, Goal Health `BLOCKED`, Critical Work Frontier, Goal outcome, or Deadline state.

## 8. Scenario Uncertainty

`OPTIMISTIC`, `MOST_LIKELY`, and `PESSIMISTIC` are three independent sibling solves. Each solve uses exactly one current
Duration scenario for every active work interval. A solve cannot mix scenario values.

Different feasibility, assignment, resource order, or finish results produce a `SCENARIO_SENSITIVE` diagnostic with
all three projection refs. The system does not choose an expected case, average the results, attach probability, or
select the fastest scenario. `PESSIMISTIC` remains a credible unfavorable scenario, not a hard upper bound.

## 9. Projection Versus Real Admission

ResourceScheduleProjection and every solver artifact are proposals only. They cannot create, mutate, or authorize:

```text
Goal, Goal plan, route choice, success criterion, Goal Health, progress, or closure
Task state, Task Dependency, PinnedDoneBinding, completion assurance, or impact cut
Task Priority, Deadline, Budget, Validation Requirement, or candidate result
CapacityClaim, host allocation, reservation, lease, or actual free-unit fact
Run, TaskPermit, Calendar authority, start authority, timer, Outbox, or external side effect
```

`ResourceOrderArc` belongs only to one exact solution. It cannot be written into `TaskDependencySpecRevision` or used as
completion provenance. `CapacityAllocationSuggestion` neither reserves nor allocates a unit.

An external solver or planner may submit a proposal but cannot read provider configuration, secrets, raw private
memory, provider responses, or raw logs; write the ledger; or call a host. Rust owns canonical scope normalization,
model construction, checked arithmetic, mandatory presence, input fingerprint, currentness, proof verification, and
persisted projection acceptance.

At execution time, the current chain remains authoritative:

```text
current Eligibility and deterministic selection
-> atomic admission and Budget reservation
-> current Capacity claim
-> Run, permit, and Outbox
-> authenticated host allocation and HostWorkAcceptance
-> committed one-time start authority
-> authenticated actual STARTED or no-execution disposition
```

Every gate rechecks current facts. A projection assignment does not reserve a unit, guarantee host acceptance, prove
physical start, or permit dispatch. If current facts differ, the current gate wins and the projection becomes stale.
No recovery or adapter may redispatch from an old projection.

## 10. Active Work, UNKNOWN, and Currentness

An active Run and its claims are pinned from canonical facts. The solver cannot move, replace, preempt, or reassign
them. A `RUNNING` Run may use one exact current compatible `DurationRemainingProjection` from the projection status time.

A `LEASED` Run proves only that one bounded start authority was committed. It does not prove actual process start. Its
allocation remains occupied, its authority expiry and active-stop boundary remain visible, and an exact processing
finish cannot be claimed until the required start and remaining-work evidence exists. A projection may retain an
unaffected known subset as `PARTIAL`; it cannot call the unknown physical interval complete.

If a Run, effect, allocation, release, or claim is `UNKNOWN`, every Capacity unit and accounting key it may occupy
remains fully occupied. The solver cannot guess a finish, release the units, move the work, or assign those units to
another Task. Uncertainty is limited to the actual pools, accounting keys, or scopes it may occupy; unrelated pools do
not become unavailable.

Future Capacity follows Section 6. A current offer supports a proposed authority commit only before its exclusive
expiry. Work beyond it requires an exact Jenn-owned labelled future assumption. Missing future coverage is
`UNAVAILABLE`; conflicting, stale, or unreconciled coverage is `INDETERMINATE`; neither becomes zero Capacity or
`INFEASIBLE`.

Any relevant semantic input change makes the old projection stale:

```text
Goal plan, membership, or route scenario
Task lifecycle generation, completion epoch, state, current work, active Run, or host-start disposition
Dependency revision, planning-basis mode/outcome, assurance version, fence, impact cut, closure, or expiry
DurationRemaining revision, frontier, assessment, or input fingerprint
Calendar binding, Calendar revision, tzdb, materialization, continuous segment, or admission window
Capacity domain, pool, request, offer, claim, host session, host fence, or active occupancy
Deadline, new-start-authority cutoff, or active-stop cutoff
mandatory-presence snapshot or future-Capacity assumption
objective, solver, time-mapping, horizon, or quantum policy
```

`valid_until_utc_ms` is the checked earliest of every applicable offer expiry, Calendar transition, materialization
coverage end, Deadline boundary, Dependency assurance or impact-cut expiry, future assumption coverage end, horizon
end, and
`forecast_as_of_utc_ms + objective_policy.resource_schedule_max_age_ms`. This document defines no duplicate hidden
Resource max-age policy. Time authority uncertainty makes the result indeterminate.

Rust re-reads the complete Event sequence and input fingerprint before accepting a solver result. A changed input
discards the result or stores it as historical `STALE`; it is never patched incrementally into current truth.

The resource-driving graph is solution-specific. Different feasible solutions, objectives, scenarios, or input
revisions may produce different arcs. It is not TimeCriticalPathProjection, Critical Work Frontier, a canonical
bottleneck fact, or traditional critical-path authority. A partial solve, explicit tail, or incomplete input cannot
emit a complete graph or complete Goal finish.

## 11. Failure, Authority, and Recovery

Result reduction is fixed:

```text
missing or incomplete required input before a valid complete model exists
  -> UNAVAILABLE

known unaffected subset or incomplete tail/horizon coverage
  -> PARTIAL; no complete aggregate finish or complete resource-driving graph

time, fact, assurance, proof, or policy cannot be reconciled
  -> INDETERMINATE

illegal graph, schema, window, demand, objective, overflow, or unsupported model
  -> MODEL_INVALID, or PARTIAL/UNAVAILABLE where the owning contract explicitly requires that result

complete mandatory hard model proven unsatisfiable
  -> INFEASIBLE

solver UNKNOWN
  -> never INFEASIBLE

solver FEASIBLE
  -> never OPTIMAL without exact verified proof
```

Reason codes include at least:

```text
PLANNING_SCOPE_INCOMPLETE
ROUTE_SCENARIO_MISSING
MANDATORY_PRESENCE_INDETERMINATE
DEPENDENCY_PLANNING_BASIS_MISSING
DEPENDENCY_ASSURANCE_CHALLENGED
DEPENDENCY_ASSURANCE_INVALIDATED
DEPENDENCY_ASSURANCE_INDETERMINATE
DEPENDENCY_IMPACT_CUT_STALE
DURATION_MISSING_OR_STALE
CALENDAR_COVERAGE_INCOMPLETE
UNSUPPORTED_COMPOSITE_ACTIVITY
CAPACITY_FACT_MISSING
FUTURE_CAPACITY_COVERAGE_MISSING
ACTIVE_FACT_UNKNOWN
HARD_START_AUTHORITY_CUTOFF_UNSATISFIED
HARD_ACTIVE_STOP_CUTOFF_UNSATISFIED
OBJECTIVE_POLICY_MISSING
SOLVER_POLICY_UNSUPPORTED
INPUT_CHANGED_DURING_SOLVE
EXPLICIT_TAIL_SELECTED
OUTSIDE_HORIZON_BY_LOWER_BOUND
SCENARIO_SENSITIVE
MODEL_INFEASIBLE
MODEL_INVALID
```

Authority is explicit:

```text
Jenn
  -> decide objective order, Goal tradeoff, future what-if assumptions, route/product choices, and any future acceptance

Nobao
  -> request analysis and make ordinary proposals only inside an accepted contract and delegated scope

Domain Agent / UI / external planner / external solver
  -> query or proposal only

authenticated host
  -> report current offers, allocation, occupancy, acceptance, and start facts only

Rust core
  -> sole scope normalization, mandatory-presence, checked model, currentness, fingerprint, proof-verification,
     and persisted-projection acceptance authority
```

No projection failure changes Task state, Goal Health, Critical Work Frontier, Goal plan, or execution authority.

If v0.2 is separately accepted and implemented in the future, recovery must first complete Event integrity, Task and Run
state, Dependency assurance/fence/impact-cut recovery, Duration, Calendar, Capacity, Deadline, host facts, UNKNOWN
reconciliation, and the recovery read barrier. Resource scheduling is rebuilt last from exact current inputs.

Old solver jobs, seeds, proofs, and projections never recover as current authority. Projection deletion or corruption is
handled by side-effect-free rebuild. Unsupported solver/model/policy makes the projection unavailable but cannot block
authoritative control recovery or Resident readiness. Rebuild creates no Event, Task transition, Run, Validation,
CapacityClaim, BudgetReservation, permit, Outbox, host call, or external side effect.

Until separate acceptance and implementation activation, runtime and recovery do not import, rebuild, display as
available, or otherwise consume this design merely because its file exists.

## 12. Rejected v0.2 Complexity

v0.2 rejects:

```text
preemption, splittable Task, checkpoint resume, or Task migration
internal phase DAG, hidden sub-Task, or solver-created Task
multi-mode Duration or resource-scaling tradeoff
sequence-dependent setup, cleanup, travel, or transition time
soft Capacity overbooking
multi-host atomic claim set or solver-created distributed transaction
automatic fastest ANY_OF route or automatic Goal tradeoff
cross-Goal Task Dependency created from resource contention
current HostCapacityOffer extrapolated into arbitrary future Capacity
Monte Carlo, probability, correlation, robust optimization, or critical-chain buffer
plugin-defined hidden objective, hidden weight, or hidden tie-break
unbounded horizon or continuous floating-point time
solver access to provider, secret, private memory, provider response, or raw log
FEASIBLE presented as OPTIMAL or UNKNOWN presented as INFEASIBLE
ResourceDrivingGraph presented as TimeCriticalPathProjection or Critical Work Frontier
solver output used as admission, Priority, Dependency, permit, start authority, or execution truth
```

## 13. Required Validation Matrix

The following are v0.2 design validation cases. They do not authorize implementation or solver activation.

1. Reject v0.2 activation until every listed v0.1 prerequisite is accepted, implemented, and recovery-tested.
2. Prove one Resource assignment creates no CapacityClaim, BudgetReservation, Run, permit, timer, Outbox, or host call.
3. Prove `FEASIBLE != OPTIMAL` and solver `UNKNOWN != INFEASIBLE` in schema, UI, and persisted projection.
4. Prove `INFEASIBLE` cannot set Task `FAILED`, Goal Health `BLOCKED`, Goal outcome, or Critical Work Frontier.
5. Label every one-Goal analysis over a shared pool `ISOLATED_GOAL_WHAT_IF`; never claim global feasibility.
6. Return `UNAVAILABLE` for a global multi-Goal solve without one current accepted complete objective policy.
7. Pin every active Run and exact current claim; reject any proposal that moves, replaces, or preempts it.
8. Retain all possibly occupied UNKNOWN units and reject their reuse by another assignment.
9. Reject any attempt to write a ResourceOrderArc into Task Dependency, Goal plan, Priority, or completion provenance.
10. Run O/M/P as separate complete solves and emit `SCENARIO_SENSITIVE` when feasibility, assignment, or finish differs.
11. Make every listed Task, plan, route, dependency-assurance, Duration, Calendar, Capacity, Deadline, and policy change stale the old projection.
12. Quantize Duration with checked ceil division exactly once; reject overflow and double wall-time conversion.
13. Quantize Calendar window starts upward and ends downward while preserving `[start, end)` semantics.
14. Reject a new interval spanning separate open Calendar segments as unsupported composite/preemptive work.
15. Treat explicit tail or proven outside-horizon work as `PARTIAL`, not model infeasibility or silent omission.
16. Include every in-scope Task exactly once in mandatory presence; never let a Hard Deadline obligation escape through tail.
17. Close hard presence over every unfinished `FUTURE_ACTIVITY_REQUIRED` predecessor and enforce successor-to-predecessor presence.
18. Accept a current HostCapacityOffer only for a proposed start-authority commit strictly before its expiry.
19. Require an exact labelled Jenn-owned future assumption for any proposed authority commit after current offer coverage.
20. Return `UNAVAILABLE` or `INDETERMINATE` before solve for missing, stale, conflicting, or unreconciled future Capacity coverage.
21. Quantize `HARD_NEW_START_AUTHORITY_CUTOFF` against `start_authority_commit_q`; reject equality at the real cutoff.
22. Quantize `HARD_ACTIVE_EXECUTION_STOP_CUTOFF` against finish; reject equality and nonpositive legal span.
23. Prove an authority commit is not actual STARTED; without a bound launch model, label physical finish and Goal finish lower-bound/partial.
24. Reject a host timestamp as retroactive proof of start authority, actual start, Calendar compliance, or Deadline compliance.
25. Require current DependencyPlanningBasis for every edge and work boundary; a bare DependencySpec or cached SATISFIED is insufficient.
26. Keep confirmed current and pinned completion boundaries at zero; never infer zero from Task `DONE` alone.
27. Reject CHALLENGED, INVALIDATED, INDETERMINATE, expired assurance, or stale impact cut as satisfied precedence.
28. Keep a confirmed pinned historical boundary distinct from a reopened source's current-lifecycle work.
29. Treat a proofless external proposal as at most FEASIBLE; accept OPTIMAL only through the exact registered verifier.
30. Require all objective phases OPTIMAL with every prior phase exact value fixed before overall OPTIMAL.
31. Verify optimality proof against exact input digest, engine, model, phase order, direction, value contract, and verifier version.
32. Keep route-work objective and projected finish separate from Goal `CLOSED + ACHIEVED` and Goal Deadline semantics.
33. Use the full canonical sorted pool-ID byte vector in the final tie-break; never only the first pool.
34. Derive `valid_until` as the earliest applicable offer, Calendar, materialization, Deadline, assurance, Duration, assumption, horizon, and max-age boundary.
35. Reject solver output bound to the wrong input fingerprint, Event sequence, engine, model, seed policy, quantum, or objective revision.
36. Mark incompatible internal Calendar, Capacity profile, or parallel-lane work `UNSUPPORTED_COMPOSITE_ACTIVITY` and never invent a hidden phase.
37. Never render ResourceDrivingGraph as TimeCriticalPath, Critical Work Frontier, canonical bottleneck, or execution order.
38. Recheck the complete fingerprint after solve; discard or retain only historical STALE output after a concurrent input change.
39. Rebuild only after authoritative recovery and its read barrier; projection rebuild must have no canonical or external side effect.
40. Prove crash recovery cannot redispatch, reclaim, reserve, or start work from an old ResourceScheduleProjection.

## 14. Final Invariants

```text
ResourceScheduleProjection grants no execution or start authority
assignment is not claim, reservation, allocation, lease, permit, or Run
ResourceOrderArc is not Task Dependency
ResourceDrivingGraph is not TimeCriticalPath or Critical Work Frontier
solver never chooses an ANY_OF route or Goal tradeoff
solver never changes Goal closure, progress, health, Task state, Priority, or Validation
solver never invents preemption, Task split, phase DAG, or future Capacity
projection cannot bypass P3, Budget, Deadline, Calendar, Capacity, permit, host, or UNKNOWN
document acceptance is not implementation or activation
```
