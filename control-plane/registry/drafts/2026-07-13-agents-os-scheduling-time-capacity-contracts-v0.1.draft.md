# AGENTS OS Scheduling, Time, and Capacity Contracts v0.1

```yaml
draft_id: agents-os-scheduling-time-capacity-contracts-v0.1
date: 2026-07-13
status: r1_proposed_final_draft
acceptance_status: pending_Jenn_freeze_decision
revision: R1
owner: Jenn
agent_steward: Nobao
acceptance_unit:
  id: R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE
  members:
    - this document Sections 3-9
    - control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md Section 2.1 pending R1 amendment overlay
  partial_freeze_permitted: false
inherits:
  - control-plane/registry/decisions/2026-07-12-agents-os-resident-operating-architecture-v0.1.md
accepted_parent_contract: Task Scheduling Architecture Boundary v0.1
proposed_for_acceptance:
  - Scheduling Work Request and Enforcement Profile v0.1
  - SchedulePlanProjection v0.1
  - Duration Estimate v0.1
  - Calendar v0.1
  - Capacity v0.1
  - Eligibility and Effective Ordering v0.1
  - Atomic Admission and Recovery v0.1
  - Time Critical Path v0.1
separate_draft_not_proposed_for_acceptance:
  - contract: Resource-constrained Scheduling v0.2
    source: control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md
proposed_parent_amendments:
  - Calendar new-start authority terminology
  - Deadline hard new-start-authority cutoff terminology
  - RUN_ATTEMPTS settlement at positive execution evidence
  - immutable complete RUN_ATTEMPTS Budget authority binding
  - semantic forecast fingerprints separated from read and storage identity
implementation_authorized: false
runtime_execution_authorized: false
runtime_source_change_authorized: false
database_creation_authorized: false
active_config_access_authorized: false
secret_access_authorized: false
provider_execution_authorized: false
independent_review_evidence:
  review_artifact_ref: control-plane/registry/reviews/2026-07-13-yellow-agents-os-scheduling-time-capacity-package-v0.1.review.yaml
  subject_hash_embedded_in_subject: false
  hash_and_results_owned_by_review_artifact: true
```

## 1. Review Status

This package is the R1 closure pass requested by Jenn after an external review found five acceptance blockers in the
earlier proposed-final draft. R1 preserves the accepted `Task Scheduling Architecture Boundary v0.1`; it does not add
runtime features or implementation authority.

Only the parent boundary is already accepted. Sections 3-9 v0.1 contracts remain:

```text
R1_PROPOSED_FINAL_DRAFT
PENDING_JENN_FREEZE_DECISION
NOT_IMPLEMENTATION_AUTHORITY
```

The proposed v0.1 contracts and the parent Section 2.1 overlay form one
`R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE`. Jenn may freeze that complete bundle, require an amendment to any member, or reject
the bundle without disturbing the already accepted parent boundary. This revision cannot freeze selected Sections or
activate only part of the overlay: doing so would leave incompatible Calendar, Deadline, host-start, or RUN_ATTEMPTS
semantics simultaneously authoritative. The bundle never includes the separately stored Resource Scheduling v0.2
design referenced in Section 10.

## 2. Inherited Invariants

Every proposed contract below must preserve:

```text
Goal / Task / Run / Validation / Event remain the only formal core objects
Rust core remains the only canonical state writer
Schedule planning and selection never grant execution authority
Task state remains reducer-derived; direct set_state remains forbidden
one Task has at most one nonterminal execution Run
Run success does not complete Task
all required Validation decisions still gate Task DONE
Task completion does not automatically complete Goal
Goal closure remains separate from plan_progress and scheduling forecast
Critical Work Frontier remains logical Goal-health structure, not a time path
Task Dependency v0.1 remains same-Goal, ALL_OF, PINNED_DONE_EVENT
Priority remains a Task-owned base service class, not a permit
Deadline remains an absolute UTC constraint, not a schedule estimate
Budget remains a consumable ceiling, not Capacity
UNKNOWN remains fail-closed and cannot auto-retry
normal scheduling remains NON_PREEMPTIVE
control / recovery work remains outside ordinary effective-order competition
host-side acceptance and external effects remain outside the original admission transaction;
Rust records canonical acceptance in a later SQLite transaction
P3, TaskPermit, host fencing, secret, provider, and private-memory boundaries remain unchanged
```

No section may silently create a new Goal plan member, Task Dependency edge, Validation Requirement, Budget,
Deadline, permission, provider authority, or Goal success criterion.

## 3. Shared Contract Rules

### 3.1 Object boundary

The following names are versioned embedded values, infrastructure records, policies, or derived projections. They do
not become additional formal core objects:

```text
DurationEstimateRevision
DurationTimingMeasurementPolicyRevision
DurationRemainingProjection
ActiveWorkSpan
TaskScheduleShapeAssessment
DependencyPlanningBasisSnapshot
TaskForecastBoundarySnapshot
CalendarRevision
CalendarBindingRevision
CalendarBindingGateState
CalendarWindowMaterialization
CalendarWakeRecord
PlanningCalendarResolutionSnapshot
CapacityPoolRevision
HostCapacityDomainRevision
HostCapacityOffer
CapacityRequestSetRevision
CapacityClaim
HostCapacityAllocationReceipt
HostWorkAcceptanceFact
HostWorkStartDispositionFact
SchedulingWorkRequestRevision
RunAttemptsBudgetAuthorityBinding
TaskSchedulingScopeAssignmentRevision
SchedulingEnforcementProfileRevision
SchedulingEligibilityAssessment
SchedulingPolicyRevision
JennFocusDirective
TemporaryExpediteDirective
FairnessAccountAssignmentRevision
SchedulingServiceCharge
SchedulingServiceProjection
SchedulingBackoffProjection
AdmissionHandoffRecord
SchedulePlanProjection
DeadlineUrgencyAssessment
TimeProjectionCurrentnessPolicyRevision
TimeCriticalPathProjection
```

Their canonical lifecycle facts are represented through the existing `Event` object. Rebuildable projections may be
deleted and regenerated without creating Run, permit, Outbox, Task transition, or external side effect.

### 3.2 Integer and time rules

```text
all duration, instant, quantity, counter, weight, and revision fields use integers
all canonical instants use UTC epoch milliseconds
local civil time is retained only where Calendar semantics require it
floating-point comparison is forbidden in gates and deterministic ordering
negative duration and negative capacity are invalid
unknown is explicit; it is never encoded as zero
```

### 3.3 Revision and currentness

Every immutable revision has a stable identity, monotonic revision, creator authority, creation Event, semantic
fingerprint, and explicit binding to the Task / Goal / host / policy revisions that define its meaning.

A record must declare exactly one of the following result semantics. The categories are not interchangeable.

```yaml
ANALYTICAL_PROJECTION:
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment:
  reason_codes: []
  basis:
    based_on_event_sequence:
    policy_revision_refs: []
    input_revision_refs: []
    input_fingerprint:
  computed_at_utc_ms:
  time_bearing_fields_when_applicable:
    forecast_as_of_utc_ms:
    valid_until_utc_ms:
    time_currentness_policy_revision:

OPERATIONAL_REDUCER_VIEW:
  reducer_currentness: CURRENT | REBUILD_REQUIRED | REBUILDING | INDETERMINATE
  reduced_through_event_sequence:
  reducer_contract_version:
  policy_revision_refs: []
  input_fingerprint:
  reduced_at_utc_ms:
  next_time_transition_utc_ms: optional

SYNCHRONOUS_ASSESSMENT:
  reuse_scope: SAME_CONSISTENT_READ_SET_ONLY
  evaluated_at_utc_ms:
  read_event_sequence:
  policy_revision_refs: []
  input_revision_refs: []
  input_fingerprint:
  outcome:
```

The classification is fixed:

| Result semantics | v0.1 records |
|---|---|
| `ANALYTICAL_PROJECTION` | `TaskScheduleShapeAssessment`, `DurationRemainingProjection`, `DurationOutcomeProjection`, `DurationCalibrationProjection`, `PlanningCalendarResolutionSnapshot`, `SchedulePlanProjection`, `DeadlineUrgencyAssessment`, `TimeCriticalPathProjection` |
| `OPERATIONAL_REDUCER_VIEW` | `DurationEstimateAssessment`, `CalendarBindingGateState`, `SchedulingEligibilityAssessment`, `SchedulingServiceProjection`, `SchedulingBackoffProjection` |
| `SYNCHRONOUS_ASSESSMENT` | `CalendarAdmissionAssessment` and transaction-local Calendar / Capacity / Dependency admission evaluations |
| not a derived result | immutable revisions, directives, Facts, Events, commitment / selection snapshots, and domain-specific materialization caches |

`CURRENT` for an analytical projection means every relevant input still matches; unrelated Events do not stale it.
A time-bearing analytical projection may remain `CURRENT` only while trusted Rust `now < valid_until_utc_ms`.
`coverage` describes whether the requested analytical scope was fully evaluated. A complete, known negative result such
as `ROUTE_UNAVAILABLE` may have `coverage=COMPLETE`; `AVAILABLE` requires `coverage=COMPLETE`, while
`INDETERMINATE` cannot claim complete coverage.

An operational reducer view does not use analytical `coverage`. A canonical decision may consume it only when its
reducer has reached the transaction's consistent Event sequence and its policy / input fingerprint still matches.
Otherwise Rust rebuilds or recomputes it, or fails the normal lane closed. A synchronous assessment never declares
itself reusable `CURRENT`; after its consistent read set ends it is historical diagnostic evidence only.

Immutable revisions, Facts, Events, snapshots, and materialization caches do not acquire a generic freshness envelope.
Their owning contracts define identity, integrity, supersession, expiry, range coverage, and acceptance. A validator
rejects a record that mixes result-semantics envelopes or relies on a field its declared category does not provide.

`STALE`, `PARTIAL`, `UNAVAILABLE`, `INDETERMINATE`, `REBUILD_REQUIRED`, and `REBUILDING` never grant execution
authority. Missing scheduling evidence does not by itself change Task state or Goal Health.

Analytical and rebuildable semantic fingerprints identify domain meaning, not where or when a row happened to be
read or materialized. Unless a narrower owning contract explicitly names an immutable source Event as a domain input,
the following fields are audit / CAS / storage identity and are excluded from semantic, input, constraint-owner
partition, and projection-basis fingerprints:

```text
row, snapshot, assessment, and projection IDs
task_aggregate_version or another aggregate version used only for CAS / audit
based_on_event_sequence, read_event_sequence, and reduced_through_event_sequence read / reducer watermarks
computed_at_utc_ms, reduced_at_utc_ms, evaluated_at_utc_ms, and other materialization timestamps
```

An immutable source Event ID / sequence enters a fingerprint only through an explicitly named source fact, current
pointer, transition, or evidence reference. Rebuilding byte-identical semantic inputs at another read barrier must
produce the same semantic fingerprint; changing a relevant source fact, revision, state, phase, release boundary,
policy, or evidence reference must change it. Audit envelopes retain their watermarks and timestamps, but those fields
cannot manufacture staleness by themselves.

### 3.4 Dependency planning basis and SchedulePlanProjection v0.1

`DependencyPlanningBasisSnapshot` is a read-only embedded input shared by SchedulePlan and Time Critical Path. It does
not create a Dependency edge, PinnedDoneBinding, completion assurance, impact resolution, Task state, or formal object.

```yaml
DependencyPlanningBasisSnapshot:
  schema_version: dependency-planning-basis.v0.1
  scope_fingerprint:
  task_work_boundaries:
    - task_id:
      lifecycle_generation:
      completion_epoch:
      role: CURRENT_ROUTE_MEMBER | DEPENDENCY_ANCESTOR
      disposition: ACTIVE_CURRENT_LIFECYCLE | CONFIRMED_CURRENT_COMPLETION | UNUSABLE_CURRENT_COMPLETION
      current_completion_ref_id: optional
      assurance_version: optional
      fence_generation: optional
      effective_assurance: CONFIRMED | CHALLENGED | INVALIDATED | INDETERMINATE | optional
  dependency_assessments:
    - dependent_task_id:
      mode: PRECOMMIT_NEW_BINDING | POSTCOMMIT_EXISTING_BINDING
      freshness: CURRENT | STALE | EVALUATING
      outcome: SATISFIED | WAITING | INTERVENTION_REQUIRED | INDETERMINATE
      dependency_revision:
      dependency_set_snapshot_id: optional
      dependency_input_fingerprint:
      assessed_at_event_sequence:
      edge_dispositions:
        - edge_id:
          prerequisite_task_id:
          disposition: FUTURE_ACTIVITY_REQUIRED | CURRENT_COMPLETION_BOUNDARY | PINNED_COMPLETION_BOUNDARY | INTERVENTION_REQUIRED | INDETERMINATE
          pinned_done_binding_id: optional
          completion_ref_id: optional
          assurance_version: optional
          fence_generation: optional
          effective_assurance: CONFIRMED | CHALLENGED | INVALIDATED | INDETERMINATE | optional
  effective_closure:
    dependency_closure_snapshot_id: optional
    completion_refs:
      - completion_ref_id:
        assurance_version:
        fence_generation:
    impact_resolution_refs:
      - impact_resolution_id:
        impact_review_completion_ref_id:
        assurance_version:
        fence_generation:
        resolution_fingerprint:
    unaffected_resolution_cut_refs:
      - unaffected_cut_id:
        exact_upstream_ref_ids: []
        assurance_version:
        fence_generation:
        expires_at_utc_ms: optional
        cut_fingerprint:
    dependency_closure_fingerprint:
    reducer_contract_version:
    policy_bundle_revision:
  next_assurance_expiry_utc_ms: optional
  based_on_event_sequence:
  input_fingerprint:
```

The deterministic reduction is:

```text
current route member DONE + exact current completion ref + effective closure CONFIRMED
  -> CONFIRMED_CURRENT_COMPLETION
  -> zero remaining active Duration for that route member

PRECOMMIT source nonterminal and normally completable
  -> FUTURE_ACTIVITY_REQUIRED
  -> include the source current lifecycle work in the network

PRECOMMIT source current DONE + exact current completion ref + effective closure CONFIRMED
  -> CURRENT_COMPLETION_BOUNDARY
  -> zero historical predecessor boundary

POSTCOMMIT exact PinnedDoneBinding + effective historical closure CONFIRMED
  -> PINNED_COMPLETION_BOUNDARY
  -> zero historical predecessor boundary even when the source later reopened

PRESERVED
  -> may support an existing POSTCOMMIT binding only after effective closure returns to CONFIRMED
  -> never creates a new PRECOMMIT binding

current valid UNAFFECTED provenance cut
  -> participates in the effective closure and fingerprint
  -> only the precisely cut upstream branch is excluded

CHALLENGED with a current impact-review / remediation path and no valid UNAFFECTED cut
  -> INTERVENTION_REQUIRED
  -> affected downstream aggregate finish is absent; unaffected entries may remain PARTIAL

CHALLENGED without a current resolution path, expired assurance evidence, or missing closure fact
  -> INDETERMINATE

effective required completion ref INVALIDATED without a current cut or explicit replacement
  -> ROUTE_UNAVAILABLE with complete negative evidence
  -> Time Critical Path does not declare Goal BLOCKED

effective assurance INDETERMINATE
  -> INDETERMINATE
```

Source current Task state and a pinned historical completion boundary are separate facts. If a reopened source is also
an explicit current route member, its current work may appear as its own network node while an already committed
consumer continues to use a distinct confirmed historical boundary. No planner may collapse those two meanings.

#### Task forecast boundary

Remaining active Duration does not establish when active work may resume or when the Task completion envelope may be
reduced to `DONE`. `TaskForecastBoundarySnapshot` is a non-formal, read-only embedded input shared by SchedulePlan and
Time Critical Path. It creates no wake, Task transition, condition satisfaction, Deadline, Dependency, permit, or
execution authority.

```yaml
TaskForecastBoundarySnapshot:
  schema_version: task-forecast-boundary.v0.1
  snapshot_id:
  task_id:
  lifecycle_generation:
  completion_epoch:
  task_aggregate_version:
  task_state:
  phase_checkpoint:
  forecast_constraint_owner_partition:
    partition_contract_version: task-forecast-constraint-owner-partition.v0.1
    complete_current_constraint_refs:
      active_work_hold_refs: []
      pending_completion_condition_refs: []
      duration_excluded_wait_reason_refs: []
    owners:
      dependency_geometry:
        active_work_hold_refs: []
        dependency_planning_basis_refs: []
        dependency_planning_basis_set_fingerprint: optional
      active_duration_geometry:
        pending_completion_condition_refs: []
        duration_estimate_revision_id: optional
        duration_context_fingerprint: optional
        duration_remaining_projection_ref: optional
        duration_remaining_projection_fingerprint: optional
        validation_work_scope_fingerprint: optional
        completion_envelope_fingerprint: optional
      active_work_release:
        active_work_hold_refs: []
      completion_release:
        pending_completion_condition_refs: []
        duration_excluded_wait_reason_refs: []
    coverage: COMPLETE | INDETERMINATE
    partition_fingerprint:
  active_work_release:
    outcome: NOT_APPLICABLE | DELEGATED_TO_DEPENDENCY_GEOMETRY | RELEASED_NOW | RELEASED_AT_KNOWN_UTC | UNAVAILABLE | INDETERMINATE
    released_at_utc_ms: optional
    owned_active_work_hold_refs: []
    canonical_condition_refs: []
    wait_reason_refs: []
    pause_or_block_refs: []
    evidence_refs: []
  completion_release:
    outcome: NOT_APPLICABLE | NO_ADDITIONAL_DELAY | RELEASED_AT_KNOWN_UTC | UNAVAILABLE | INDETERMINATE
    released_at_utc_ms: optional
    pending_completion_condition_refs: []
    duration_excluded_wait_reason_refs: []
    evidence_refs: []
  zero_remaining_basis_alignment:
    classification: NOT_ZERO_REMAINING | MATCHED | MISMATCH | INDETERMINATE
    duration_estimate_revision_id: optional
    zero_remaining_basis_fingerprint: optional
  next_time_transition_or_expiry_utc_ms: optional
  based_on_event_sequence:
  input_revision_refs: []
  input_fingerprint:
```

Every `*_refs` list inside `forecast_constraint_owner_partition` contains the same strict embedded reference shape;
an owner list repeats the byte-identical reference from the complete current set rather than inventing a shorter alias:

```yaml
ForecastConstraintRef:
  constraint_ref_id:
  constraint_revision:
  constraint_kind: ACTIVE_WORK_HOLD | PENDING_COMPLETION_CONDITION | DURATION_EXCLUDED_WAIT
  source_contract_ref:
  source_scope_fingerprint:
  constraint_currentness_fingerprint:
  source_current_pointer_event_sequence:
```

`source_current_pointer_event_sequence` is the immutable domain Event sequence that established this exact current
constraint pointer. It is not the projection's read barrier, reducer watermark, or rebuild sequence.

Lists use the fixed ascending tuple `(constraint_kind ordinal, constraint_ref_id canonical bytes,
constraint_revision)`. Duplicate tuple keys or two payloads under one tuple key are a partition conflict. The partition
fingerprint covers the Task/lifecycle/completion epoch, complete sorted reference sets, every sorted owner set, every
Dependency and Duration owner-basis ref/fingerprint, and the partition contract version. It excludes `snapshot_id`,
`task_aggregate_version`, `based_on_event_sequence`, and materialization time. The snapshot `input_fingerprint` covers
Task state and phase, the canonical constraint refs and owner partition, exact Dependency / Duration bases, release
outcomes and instants, zero-basis alignment, evidence/currentness refs, the next transition or expiry, and the relevant
contract/policy revisions; it has the same storage-identity and read-watermark exclusions.

The reducer is exact:

```text
confirmed current or pinned completion boundary
  -> forecast_constraint_owner_partition coverage COMPLETE with every owner set empty
  -> active_work_release NOT_APPLICABLE
  -> completion_release NOT_APPLICABLE

current Task has no current unsatisfied active-work hold in the complete constraint set
  -> active_work_release RELEASED_NOW

dependency_geometry owner set is nonempty, every current active-work hold is owned by dependency geometry, and there is
no independently owned active-work hold
  -> active_work_release DELEGATED_TO_DEPENDENCY_GEOMETRY
  -> this is a neutral planning constraint, not a claim that the Task wake condition is currently satisfied

active_work_release owner set is nonempty and all of its holds name canonical condition contracts whose current facts
deterministically establish a future UTC release instant
  -> active_work_release RELEASED_AT_KNOWN_UTC at that checked instant

complete current evidence shows an independently owned external, manual, or otherwise unscheduled active-work release
condition
  -> active_work_release UNAVAILABLE

release condition truth, ownership, revision, or time cannot be reconciled
  -> active_work_release INDETERMINATE

active_duration_geometry owner set is nonempty, every current pending completion condition is exactly covered by active
Duration geometry, and there is no independently owned pending completion condition or Duration-excluded completion wait
  -> completion_release NO_ADDITIONAL_DELAY
  -> this does not claim that a Duration-covered condition is already satisfied

no current pending completion condition and no Duration-excluded completion wait
  -> completion_release NO_ADDITIONAL_DELAY

completion_release owner set is nonempty and every independently owned pending completion condition and excluded wait
has one canonical deterministic future UTC satisfaction instant
  -> completion_release RELEASED_AT_KNOWN_UTC at their checked maximum

complete current evidence contains an independently owned external, manual, or otherwise unscheduled completion release
  -> completion_release UNAVAILABLE

completion condition truth, scope, revision, or time cannot be reconciled
  -> completion_release INDETERMINATE
```

The owner partition is a total, mutually exclusive reduction over exact current canonical references, not a planner
annotation. Its invariants are:

```text
complete_current_constraint_refs
  = the complete canonical current set of active-work holds, pending completion conditions, and
    Duration-excluded completion waits for this Task lifecycle / completion epoch

dependency_geometry.active_work_hold_refs
  -> exact subset of active-work holds already represented by the bound current DependencyPlanningBasisSnapshot set
  -> every ref binds the matching Dependency assessment mode, revision, input fingerprint, and wake-condition identity
  -> when nonempty, dependency_planning_basis_refs and dependency_planning_basis_set_fingerprint are required

active_duration_geometry.pending_completion_condition_refs
  -> exact subset whose remaining active execution, Validation, HUMAN_ACCEPTANCE handling, remediation, or rework is
     already covered by the bound CURRENT + AVAILABLE DurationRemainingProjection
  -> the estimate/context, Validation work scope, completion envelope, and remaining-Duration fingerprints must all match
  -> when nonempty, every active-duration basis field is required

active_work_release owner
  -> owns only active-work holds not owned by dependency geometry
  -> exactly equals active_work_release.owned_active_work_hold_refs

completion_release owner
  -> owns only pending completion conditions not owned by active Duration geometry, plus every Duration-excluded
     completion wait
  -> exactly equals completion_release.pending_completion_condition_refs and
     completion_release.duration_excluded_wait_reason_refs by kind

union of the four owner sets by canonical constraint kind
  = complete_current_constraint_refs

intersection of any two owner sets
  = empty
```

A bare Task state, Requirement label, projected predecessor finish, estimate prose, or UI grouping cannot assign an
owner. Missing refs, duplicate ownership, kind mismatch, incomplete current-set coverage, a stale or mismatched
Dependency planning basis, or a Duration / Validation / completion-envelope fingerprint mismatch makes
`coverage=INDETERMINATE`. In that case both release outcomes are `INDETERMINATE`, the partition fingerprint records the
failed exact input set, and no aggregate `TASK_DONE` finish may be emitted. A projection never turns a delegated
Dependency wait into a wake Fact or treats a Duration-covered completion condition as already passed.

For `ZERO_ACTIVE_WORK_PROVEN`, the canonical sorted
`completion_release` owner sets must exactly match the corresponding `pending_completion_condition_refs` and
`duration_excluded_wait_reason_refs` lists in `zero_remaining_basis`, and the `active_duration_geometry` owner set must
be empty. Otherwise alignment is `MISMATCH` and no aggregate `TASK_DONE` finish is emitted. Unknown, omitted, duplicated,
or unmatched references are never treated as an empty list.

`RELEASED_AT_KNOWN_UTC` is legal only when a canonical condition contract already defines that instant and Rust can
bind its exact revision and current fact. A timer, projection refresh, UI countdown, or Calendar wake cannot satisfy
the condition or change Task state. `next_time_transition_or_expiry_utc_ms` only bounds projection currentness; after
that instant Rust must reduce a new boundary snapshot from current facts.

`SchedulePlanProjection` is the concrete read model for resource-unconstrained time forecasting. R1 removes effective
ordering, admission Calendar status, and Capacity observation from this projection; those already belong to
Eligibility, service, backoff, selection, Calendar assessment, and Capacity views.

```yaml
SchedulePlanProjection:
  projection_id:
  projection_contract_version: schedule-time-forecast.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  planning_mode: RESOURCE_UNCONSTRAINED_EARLIEST_TIME
  scope:
    mode: GLOBAL_CURRENT_WORK | GOAL_ROUTE_SCENARIO
    goal_id: optional
    goal_plan_revision: optional
    route_scenario_fingerprint: optional
  horizon_start_utc_ms:
  horizon_end_utc_ms:
  duration_scenarios: [OPTIMISTIC, MOST_LIKELY, PESSIMISTIC]
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE | ROUTE_UNAVAILABLE
  reason_codes: []
  forecast_as_of_utc_ms:
  valid_until_utc_ms:
  time_currentness_policy_revision:
  next_recompute_reasons: []
  basis:
    task_refs: []
    plan_membership_refs: []
    route_scenario_ref: optional
    dependency_planning_bases: []
    derived_remaining_duration_refs: []
    task_forecast_boundary_snapshots: []
    forecast_constraint_owner_partition_fingerprints: []
    planning_calendar_resolution_snapshots: []
    rolling_horizon_policy_revision:
    algorithm_revision:
    based_on_event_sequence:
    input_fingerprint:
  entries:
    - task_id:
      work_request_id: optional
      work_request_revision: optional
      route_scope: COMMON_TO_ALL_VIABLE_ROUTES | EXPLICIT_ROUTE_SCENARIO | ROUTE_DECISION_REQUIRED | NOT_GOAL_ROUTED
      forecast_status: FORECASTABLE | WAITING_DEPENDENCY_RESOLUTION | WAITING_ACTIVE_WORK_RELEASE | WAITING_COMPLETION_RELEASE | WAITING_PLANNING_CALENDAR | ROUTE_DECISION_REQUIRED | ROUTE_UNAVAILABLE | PARTIAL_INPUT | INDETERMINATE
      forecast_completion_semantics: TASK_DONE
      task_forecast_boundary_ref:
      task_forecast_boundary_fingerprint:
      forecast_constraint_owner_partition_fingerprint:
      active_work_release_outcome: NOT_APPLICABLE | DELEGATED_TO_DEPENDENCY_GEOMETRY | RELEASED_NOW | RELEASED_AT_KNOWN_UTC | UNAVAILABLE | INDETERMINATE
      completion_release_outcome: NOT_APPLICABLE | NO_ADDITIONAL_DELAY | RELEASED_AT_KNOWN_UTC | UNAVAILABLE | INDETERMINATE
      earliest_resource_unconstrained_start_utc_ms: optional
      earliest_resource_unconstrained_active_finish_by_scenario: {}
      earliest_resource_unconstrained_finish_by_scenario: {}
      planning_calendar_resolution_id: optional
      planning_calendar_resolution_fingerprint: optional
      dependency_planning_basis_fingerprint:
      derived_remaining_duration_fingerprint: optional
      reason_codes: []
  outside_horizon_task_ids: []
  computed_at_utc_ms:
```

`SchedulePlanProjection.basis.input_fingerprint` covers the complete semantic Task / plan / route membership,
Dependency assurance basis, remaining-Duration basis, Task forecast-boundary and owner-partition basis, planning
Calendar resolution, horizon, algorithm, and policy revisions. It excludes `projection_id`, every embedded snapshot or
projection row ID when a semantic fingerprint is already bound, aggregate CAS versions, read/reducer watermarks, and
materialization timestamps. Those fields remain audit evidence only.

The projection may forecast only work common to every viable current route, work under an explicit Jenn / Nobao
planning route scenario, and non-routed standalone work. Alternative-route work without a route decision is shown as
`ROUTE_DECISION_REQUIRED`; Rust never chooses the fastest `ANY_OF` route.

Its geometry uses only Task work boundaries, Dependency planning bases, derived remaining Duration, planning Calendar,
Task forecast boundaries, route membership, horizon, and algorithm policy. It contains no Priority, Focus, expedite,
Deadline urgency, fairness, backoff, admission Calendar, Capacity, Eligibility, enforcement profile, selection, claim,
or Run authority.

For each current-lifecycle work node and Duration scenario, the forecast is reduced as follows:

```text
dependency_ready_at = max(horizon_start, every required predecessor TASK_DONE finish)

active_work_release RELEASED_NOW
  -> independent_active_release_at = forecast_as_of_utc_ms

active_work_release DELEGATED_TO_DEPENDENCY_GEOMETRY
  -> there is no independent active-release instant
  -> the exact dependency_ready_at is the only release contribution from the delegated Dependency holds

active_work_release RELEASED_AT_KNOWN_UTC
  -> independent_active_release_at = released_at_utc_ms

active_work_release UNAVAILABLE / INDETERMINATE
  -> no active-work start, active finish, or TASK_DONE finish

active_start_boundary
  = max(
      dependency_ready_at,
      independent_active_release_at when present
    )

positive remaining active Duration
  -> active_start = next allowed planning Calendar instant at or after active_start_boundary
  -> active_finish = Calendar.add_active_duration(active_start, selected remaining Duration)

zero remaining active Duration
  -> active_start = active_start_boundary
  -> active_finish = active_start_boundary
  -> Calendar does not invent work merely to move a zero-length boundary

completion_release NO_ADDITIONAL_DELAY
  -> TASK_DONE finish = active_finish
  -> every Duration-owned completion condition remains forecast through active_finish, not silently treated as passed

completion_release RELEASED_AT_KNOWN_UTC
  -> TASK_DONE finish = max(active_finish, released_at_utc_ms)

completion_release UNAVAILABLE / INDETERMINATE or zero-basis alignment MISMATCH / INDETERMINATE
  -> active finish may remain diagnostic
  -> aggregate TASK_DONE finish is absent

forecast_constraint_owner_partition coverage INDETERMINATE, incomplete union, duplicate owner, kind mismatch, or basis
mismatch
  -> no active start, active finish, or aggregate TASK_DONE finish
  -> entry forecast_status INDETERMINATE
```

A `WAITING`, `PAUSED`, or unresolved `BLOCKED` Task with `0/0/0` remaining Duration therefore cannot be forecast as
immediately `TASK_DONE` unless its exact active-work and completion-release boundaries justify that result. A known
active finish is not silently relabeled as Task completion.

SchedulePlan entry `reason_codes` uses the same exact boundary distinctions as Section 9.7:
`TASK_RELEASE_TIME_UNKNOWN`, `TASK_ACTIVE_WORK_RELEASE_INDETERMINATE`, `TASK_COMPLETION_RELEASE_UNKNOWN`,
`TASK_COMPLETION_RELEASE_INDETERMINATE`, `ZERO_DURATION_BOUNDARY_MISMATCH`, and
`ACTIVE_DURATION_OBSERVATION_STALE`, plus the forecast-constraint partition reason codes. An unavailable release uses a
`WAITING_*_RELEASE` status with no unjustified aggregate finish; irreconcilable ownership evidence uses
`INDETERMINATE`.

```text
SchedulePlan pure time forecast
  -> may feed DeadlineUrgencyAssessment
  -> may not read DeadlineUrgencyAssessment or effective ordering

Eligibility / service / backoff / TaskPrioritySelectionSnapshot
  -> own current ordering and selection evidence
  -> may read exact DeadlineUrgencyAssessment
  -> do not rewrite SchedulePlan

CalendarAdmissionAssessment / Capacity views
  -> point-in-time diagnostics
  -> do not enter SchedulePlan geometry or currentness

Dashboard / VCPChat / VCPMobile
  -> may compose these independent read surfaces
  -> cannot persist the composition as admission authority
```

Selection always recomputes current Eligibility and ordering. A stale SchedulePlan cannot admit, delay, preempt, or
dispatch work. The default rolling horizon remains in SchedulingPolicyRevision. Work outside the horizon remains in
the canonical plan and is listed in `outside_horizon_task_ids`; it is never deleted or treated complete.

Event-backed input changes make the projection immediately `STALE`. While TimeAuthority is trusted, it may remain
`CURRENT` only while Rust `now < valid_until_utc_ms`. The validity boundary is the checked minimum of the next relevant
planning Calendar transition, planning Calendar materialization coverage end, rolling-horizon end, policy maximum age,
Dependency assurance / resolution expiry, Task forecast boundary transition / expiry, and every referenced
DurationRemainingProjection validity boundary. Any referenced remaining-Duration frontier, assessment, validity, or
fingerprint change and any Task forecast boundary input, complete constraint set, owner assignment, owner-basis
fingerprint, partition fingerprint, or release fingerprint change stales the projection through its Event-backed input
basis. Deadline,
admission Calendar, Capacity, Focus, expedite, aging, service, and backoff changes do not stale pure time geometry.

Rust rechecks the full basis fingerprint before accepting a compute result. Input change during computation discards
the result or stores it as historical `STALE` only.
### 3.5 SchedulingWorkRequestRevision

`work_request_id` is never a caller-invented correlation string. It identifies an immutable Task-owned scheduling
envelope accepted by Rust.

```yaml
SchedulingWorkRequestRevision:
  schema_version: scheduling-work-request.v0.1
  work_request_id:
  work_request_revision:
  supersedes_revision_id: optional
  task_id:
  lifecycle_generation:
  work_subject_kind: EXECUTION_RUN | EFFECTFUL_VALIDATION_RUN
  run_purpose: TASK_EXECUTION | EFFECTFUL_VALIDATION
  task_spec_revision:
  phase_checkpoint:
  enforcement_scope_key:
  enforcement_scope_assignment_revision:
  enforcement_scope_assignment_fingerprint:
  execution_scope:
    requested_effect_scope_fingerprint:
    required_capability_profile_ref:
    capacity_request_set_id:
    capacity_request_revision:
  candidate_binding:
    mode: NONE_EXPECTED | REJECT_FOR_NEW_EXECUTION | PRESERVE_FOR_EFFECTFUL_VALIDATION
    result_revision: optional
    current_candidate_commitment_id: optional
    validation_set_snapshot_id: optional
    validation_requirement_id: optional
    validation_requirement_revision: optional
    validator_execution_contract_revision: optional
  created_by: Jenn | Nobao | RUST_POLICY
  authority_basis_refs: []
  reason:
  created_at_utc_ms:
  effective_from_event_sequence:
  context_fingerprint:
  semantic_fingerprint:
```

Rules:

```text
EXECUTION_RUN
  -> NONE_EXPECTED when no candidate exists
  -> REJECT_FOR_NEW_EXECUTION when an authorized rerun intentionally discards the current candidate
  -> cannot use PRESERVE_FOR_EFFECTFUL_VALIDATION

EFFECTFUL_VALIDATION_RUN
  -> requires a current candidate, result revision, frozen Validation Set, and exact Requirement revision
  -> requires PRESERVE_FOR_EFFECTFUL_VALIDATION
  -> cannot change candidate result or execution effect scope
  -> effect scope, capability profile, and Capacity request derive from the Requirement's validator-execution contract
```

Jenn or Nobao may create normal execution requests within their existing Task authority. Effectful Validation requests
are created by Rust from the current candidate and accepted Requirement after an authorized Jenn / Nobao attempt
command; Validator, Worker, host, UI, and planner can only propose.

The attempt command authorizes starting the exact current Requirement; it cannot override effect scope, capability,
Capacity, host class, or validator contract. If the Requirement revision lacks a versioned validator-execution
contract, Rust cannot form an effectful work request. Changing any of those fields requires a new/revised Requirement
through the already frozen Validation Set/commitment process, not an ad hoc attempt parameter.

`RUST_POLICY` is not general intent-creation authority. It may create a revision only from a registered deterministic
policy transition whose input already contains a current Jenn / Nobao-authorized Task execution intent, or from the
effectful Validation derivation above. The policy ID, revision, source command, and authority chain must appear in
`authority_basis_refs`. A timer, projection, Priority change, host offer, or solver result cannot originate a work
request.

The request becomes stale when Task lifecycle generation, Task spec, enforcement-scope assignment, bound candidate /
result, Validation Set, Requirement, effect scope, capability profile, or Capacity request changes. Priority, schedule
projection, and current Capacity availability do not rewrite it. Selection, backoff, admission, Run, permit, and Outbox must bind both
`work_request_id` and `work_request_revision`.

The caller never chooses `enforcement_scope_key`. Rust copies it from the exact current assignment:

```yaml
TaskSchedulingScopeAssignmentRevision:
  schema_version: task-scheduling-scope-assignment.v0.1
  assignment_id:
  task_id:
  assignment_revision:
  supersedes_revision_id: optional
  task_spec_revision:
  domain_contract_revision_refs: []
  enforcement_scope_key:
  derivation_policy_revision:
  derived_by: RUST_POLICY
  authority_basis_refs: []
  effective_from_event_sequence:
  semantic_fingerprint:
```

Rust derives the key from the canonical Task/domain assignment and a registered policy. Jenn may reassign it. Nobao
may accept a policy-derived assignment within her current Task/domain authority only when the key is unchanged, or
when every current profile for both old and new keys is all-SHADOW. If any subject/subsystem on the old key is
ENFORCING or SUSPENDED, every cross-key reassignment is Jenn-only in v0.1; Rust does not improvise a partial order over
modes, pool allowlists, or contract versions. A change requires normal Task-spec quiescence/CAS, fences old unaccepted
work requests and permits, and cannot alter an accepted Run. Missing or ambiguous assignment is indeterminate, never a
caller-selected `SHADOW` fallback.

### 3.6 SchedulingEnforcementProfileRevision

Architecture acceptance, code availability, shadow evaluation, and behavior cutover are separate facts. Each immutable
work request belongs to one explicit enforcement scope; the current profile for that scope decides which new
scheduling contracts are diagnostic and which are active gates.

```yaml
SchedulingEnforcementProfileRevision:
  schema_version: scheduling-enforcement-profile.v0.1
  profile_id:
  enforcement_scope_key:
  profile_revision:
  supersedes_revision_id: optional
  work_subject_kind: EXECUTION_RUN | EFFECTFUL_VALIDATION_RUN
  atomic_admission_contract_version:
  host_acceptance_contract_version:
  modes:
    normal_selection: SHADOW | ENFORCING | SUSPENDED_FAIL_CLOSED
    admission_calendar: SHADOW | ENFORCING | SUSPENDED_FAIL_CLOSED
    capacity_admission: SHADOW | ENFORCING | SUSPENDED_FAIL_CLOSED
  capacity_pool_allowlist:
    - pool_id:
      pool_revision:
      capacity_domain_id:
      capacity_domain_revision:
      capacity_accounting_key_digest:
      capability_fingerprint:
      host_watchdog_contract_version:
  capacity_pool_allowlist_fingerprint:
  activation_precondition_evidence_refs: []
  recovery_test_evidence_refs: []
  decided_by: Jenn
  reason:
  effective_from_event_sequence:
  cutover_event_id:
  semantic_fingerprint:
```

There is exactly one current profile per `(enforcement_scope_key, work_subject_kind)`. Scope keys are canonical
Task/domain assignment keys, never caller-provided wildcards. Profiles cannot overlap because each work request names
exactly one key. `capacity_pool_allowlist` must be nonempty when Capacity is `ENFORCING`, and every admitted pool must
be current, recovered, and listed.

The allowlist binds exact revisions and fingerprints, not only pool IDs. Any pool/domain/capability/watchdog revision
change quarantines that entry for new admission and requires a new Jenn profile revision or a future explicitly
accepted compatibility-recertification contract. A `NOBAO_MANAGED` pool revision never silently inherits Jenn's old
cutover authority.

If Calendar or Capacity mode is `ENFORCING`, normal selection must also be `ENFORCING`, both contract-version fields
must name supported active reducers, and the exact recovery evidence must pass. For
`EFFECTFUL_VALIDATION_RUN`, the activated versions must include the candidate-preserving Validation attempt and
host-start disposition protocol. An unsupported combination rejects the whole profile revision; it never partially
activates.

```text
SHADOW
  -> compute and compare diagnostics
  -> cannot deny legacy selection/admission, issue a new fence, create CapacityClaim, or alter permit authority

ENFORCING
  -> the owning synchronous reducer applies the contract and fails closed on missing / indeterminate required facts

SUSPENDED_FAIL_CLOSED
  -> no new normal selection or admission for this exact scope
  -> Fact / Receipt, stop, fence, UNKNOWN reconciliation, finalizer, and local recovery remain live
```

Only Jenn can move a subsystem into or out of `ENFORCING` or `SUSPENDED_FAIL_CLOSED`. The transition is an explicit
Event-backed revision, never inferred from document acceptance, schema presence, a feature flag in JavaScript, or a
projection. A profile change fences not-yet-accepted authority for that scope but never preempts an accepted Run.

Implementation migration must atomically install explicit `SHADOW` baseline profiles and the capability-cutover Event
before any new reducer consults them. After that cutover, a missing, duplicated, unsupported, or stale profile is
`INDETERMINATE`, not an implicit mode. Eligibility, selection, admission, permit, Outbox, host acceptance, and recovery
bind the current profile revision and recheck it at their synchronous boundaries.

### 3.7 TimeProjectionCurrentnessPolicyRevision

Time-bearing projections use one visible policy rather than the phrase “status time changed.”

```yaml
TimeProjectionCurrentnessPolicyRevision:
  schema_version: time-projection-currentness-policy.v0.1
  policy_id: agents-os-time-projection-currentness
  policy_revision:
  schedule_plan_max_age_ms: 60000
  time_critical_path_max_age_ms: 60000
  time_critical_path_analysis_horizon_ms: 31536000000
  deadline_urgency_max_age_ms: 60000
  parameter_value_classes:
    JENN_POLICY:
      - schedule_plan_max_age_ms
      - time_critical_path_max_age_ms
      - time_critical_path_analysis_horizon_ms
      - deadline_urgency_max_age_ms
  benchmark_evidence_refs: []
  time_authority_policy_revision:
  decided_by: Jenn
  effective_from_event_sequence:
  semantic_fingerprint:
```

All maximum ages and the analysis horizon are positive checked integers. For each projection, Rust computes
`max_age_boundary = checked(forecast_as_of_utc_ms + applicable_max_age_ms)` and takes the earliest applicable boundary
named by that projection contract. `valid_until_utc_ms` is exclusive. A missing policy or uncertain time is
indeterminate; a UI refresh loop, timer, or scheduler callback cannot extend validity. These values are visible Jenn
planning/currentness policy, not a hard real-time guarantee, SLA, polling requirement, execution authority, or hidden
benchmark result. Implementation must either support the accepted horizon and expiry math or report the policy
unsupported; it cannot silently shorten or extend them.

## 4. Duration Estimate v0.1

### 4.1 Decision and meaning

Duration Estimate is a Task-owned immutable planning input. It estimates:

```text
how much active completion time this Task still needs
from its current canonical work position
until its Task completion envelope can be satisfied
```

It includes remaining Task execution, required Validation work, HUMAN_ACCEPTANCE handling time, and currently known
remediation / rework represented by the three-point range. It does not multiply Duration by an assumed future failure
or retry probability. It excludes:

```text
predecessor wait
ordinary queue wait
Capacity contention
Calendar closed time
PAUSED / WAITING time
UNKNOWN reconciliation
Deadline slack
Budget wait
downstream Task
Goal completion review and Goal closure
```

Waiting for Jenn to become available is Calendar / scheduling time. Jenn's actual attention spent on the acceptance is
active completion time.

Duration is not Task state, Deadline, `WALL_CLOCK_MS` Budget, Calendar, Capacity, Run timeout, lease, permit, progress,
or completion fact.

### 4.2 Record boundary

```text
DurationEstimateRevision
  -> Task-owned immutable contract row

DurationEstimateAssessment
  -> operational currentness reducer view

DurationRemainingProjection
  -> analytical projection from one estimate baseline plus compatible cumulative timing

DurationTimingFact
  -> host / Run / Validation measurement accepted as Event-backed fact

DurationOutcomeProjection / DurationCalibrationProjection
  -> derived, read-only, rebuildable
```

None is a formal core object. v0.1 rejects parallel canonical Goal, Run, or Validation estimates. Goal time derives
from the Task network; Run and Validation timing are observations only.

### 4.3 DurationEstimateRevision

```yaml
DurationEstimateRevision:
  schema_version: duration-estimate.v0.1
  duration_estimate_id:
  task_id:
  lifecycle_generation:
  completion_epoch:
  duration_revision:
  supersedes_revision_id: optional
  target: TASK_REMAINING_COMPLETION_ACTIVE_TIME
  unit: MILLISECOND
  execution_assumption: SERIAL_SINGLE_ACTIVE_LANE_V0_1
  schedule_shape_assessment_ref:
  three_point:
    optimistic_ms:
    most_likely_ms:
    pessimistic_ms:
    semantics: SCENARIO_RANGE_NOT_BOUND_NOT_QUANTILE
  remaining_active_work_classification: ACTIVE_WORK_MAY_REMAIN | ZERO_ACTIVE_WORK_PROVEN
  zero_remaining_basis: # required only for ZERO_ACTIVE_WORK_PROVEN
    pending_completion_condition_refs: []
    duration_excluded_wait_reason_refs: []
    validation_scope_fingerprint:
    completion_envelope_fingerprint:
    evidence_refs: []
    decided_at_event_sequence:
  observed_context:
    observed_task_aggregate_version:
    task_spec_revision:
    result_revision: optional
    current_candidate_commitment_id: optional
    phase_checkpoint:
    validation_scope_mode: DRAFT_REQUIREMENTS | FROZEN_VALIDATION_SET
    validation_set_snapshot_id: optional
    validation_work_scope_fingerprint:
    work_position_event_sequence:
    observation_baseline:
      baseline_event_sequence:
      span_frontier:
        - active_work_span_id:
          measurement_sequence:
          cumulative_active_ms:
          coverage_fingerprint:
      cumulative_active_ms_at_baseline:
      baseline_fingerprint:
  context_fingerprint_contract: duration-context.v0.1
  context_fingerprint:
  estimation_policy_revision: duration-estimate.v0.1
  estimate_method: EXPERT_JUDGMENT | DECOMPOSITION | ANALOGY | EMPIRICAL_CLASS
  evidence_grade: ROUGH | BASIS_SUPPORTED | EMPIRICALLY_CALIBRATED
  basis_refs: []
  assumption_refs: []
  assumption_digest:
  authority_mode: NOBAO_MANAGED | JENN_LOCKED
  decided_by:
  reason:
  created_at_utc_ms:
  effective_from_event_sequence:
  semantic_fingerprint:
```

`duration_estimate_id` is stable per Task. Revisions are append-only.

```text
0 <= optimistic_ms <= most_likely_ms <= pessimistic_ms
```

All three values may be zero only when `remaining_active_work_classification=ZERO_ACTIVE_WORK_PROVEN`, the positive
`zero_remaining_basis` is complete, and no remaining execution, Validation, human handling, remediation, or rework is
known. Missing, unknown, unmeasured, or unreconciled work is never encoded as zero. Zero Duration does not complete the
Task, satisfy Dependency, establish a release instant, or bypass a pending completion condition. Rust accepts integers
only and rejects float, NaN, Infinity, overflow, implicit day/week units, and negative values.

`observed_task_aggregate_version` is CAS and audit evidence only. It is excluded from the duration context fingerprint,
so an unrelated Priority revision does not stale the estimate.

### 4.4 Three-point uncertainty

```text
optimistic_ms
  -> credible favorable case under the current scope
  -> not a theoretical minimum or guarantee

most_likely_ms
  -> single most plausible current case
  -> not a mean, median, commitment, or SLA

pessimistic_ms
  -> credible unfavorable current case
  -> not an absolute upper bound or HARD_CAP
```

They are scenarios, not probability quantiles. `evidence_grade` is evidence maturity, not success probability.

Every projection must explicitly select exactly one:

```text
OPTIMISTIC
MOST_LIKELY
PESSIMISTIC
```

v0.1 forbids PERT `(O + 4M + P) / 6`, hidden model weights, or any average presented as canonical expected duration.

#### Task schedule shape

`SERIAL_SINGLE_ACTIVE_LANE_V0_1` is verified by Rust; it is not a free-form estimator claim.

```yaml
TaskScheduleShapeAssessment:
  schema_version: task-schedule-shape-assessment.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  task_id:
  lifecycle_generation:
  completion_epoch:
  outcome: SINGLE_SERIAL_CALENDAR | COMPOSITE_UNSUPPORTED | INDETERMINATE
  execution_and_validation_scope_refs: []
  effective_planning_calendar_fingerprint: optional
  capacity_profile_fingerprints: []
  overlap_assessment: PROVEN_SERIAL | POSSIBLE_OVERLAP | INDETERMINATE
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE
  reason_codes: []
  basis:
    based_on_event_sequence:
    policy_revision_refs: []
    input_revision_refs: []
    input_fingerprint:
  computed_at_utc_ms:
```

Different execution and Validation Calendars, different required capacity profiles, parallel required work lanes, or
work whose non-overlap cannot be proved produce `COMPOSITE_UNSUPPORTED` or `INDETERMINATE`. Duration may remain a
human planning note, but Time Critical Path must mark the affected calculation `PARTIAL` or `UNAVAILABLE`; a future
Resource Scheduling contract must inherit the same rejection and may not squeeze composite work into one serial
Calendar.

### 4.5 Currentness

```yaml
DurationEstimateAssessment:
  schema_version: duration-estimate-assessment.v0.1
  result_semantics: OPERATIONAL_REDUCER_VIEW
  applicability: APPLICABLE | NOT_APPLICABLE
  reducer_currentness: CURRENT | REBUILD_REQUIRED | REBUILDING | INDETERMINATE
  outcome: AVAILABLE | UNAVAILABLE | INDETERMINATE
  current_revision_id: optional
  reason_codes: []
  reduced_through_event_sequence:
  reducer_contract_version: duration-estimate-currentness.v0.1
  policy_revision_refs: []
  current_context_fingerprint:
  input_fingerprint:
  reduced_at_utc_ms:
```

```text
DONE / FAILED / CANCELLED
  -> NOT_APPLICABLE

no accepted revision
  -> APPLICABLE + UNAVAILABLE

exact duration context matches
  -> APPLICABLE + reducer CURRENT + AVAILABLE

revision exists but context changed
  -> APPLICABLE + reducer CURRENT + UNAVAILABLE + ESTIMATE_CONTEXT_STALE

reducer has not reached the consistent Event sequence or its stored fingerprint is invalid
  -> APPLICABLE + REBUILD_REQUIRED / REBUILDING + UNAVAILABLE

policy, fingerprint, or baseline cannot be reconciled
  -> APPLICABLE + INDETERMINATE
```

The estimate becomes stale when any duration-relevant fact changes:

```text
lifecycle_generation or completion_epoch
Task spec or result revision
candidate identity or phase checkpoint
draft / frozen Validation work scope
Run / Validation failure or rework fact changing remaining work
execution assumption or estimation policy compatibility
```

These facts alone do not stale intrinsic Duration:

```text
Priority, Deadline, Budget, or Dependency revision
Goal membership or plan revision
Calendar, Capacity, or schedule projection
ordinary WAITING / BLOCKED / PAUSED
wall-clock passage when no active-observation freshness contract expires
new compatible PARTIAL or COMPLETE cumulative timing observation by itself
unrelated Task changes
```

If one of them also changes the actual Task completion scope, the scope fingerprint controls.

A Duration revision increments Task aggregate version, duration revision, and Event sequence. It does not increment
task spec, result, Validation, Dependency, Priority, or Goal plan revision; change Task state; revoke permit; or
preempt an active Run.

### 4.6 Derived remaining Duration

Time forecasts consume `DurationRemainingProjection`, not the raw estimate triple. The projection advances from the
immutable estimate baseline using each unique compatible ActiveWorkSpan once.

#### Timing measurement policy

An open `ActiveWorkSpan` makes the remaining-Duration result time-bearing because active work may continue after the
latest cumulative observation. The immutable estimate remains current, but a derived remaining value may be used only
inside a bounded observation-silence window selected by an explicit policy revision.

```yaml
DurationTimingMeasurementPolicyRevision:
  schema_version: duration-timing-measurement-policy.v0.1
  policy_id: agents-os-duration-timing-measurement
  policy_revision:
  partial_observation_max_silence_ms:
  complete_observation_required: true
  open_span_expiry_semantics: EXCLUSIVE_FROM_LATEST_ACCEPTED_OBSERVATION_OR_SPAN_OPEN
  parameter_value_classes:
    PROVISIONAL_BENCHMARK_REQUIRED:
      - partial_observation_max_silence_ms
  benchmark_status: REQUIRED_NOT_COMPLETE | PARTIAL | SUPPORTED
  benchmark_evidence_refs: []
  benchmark_environment_fingerprint:
  time_authority_policy_revision:
  decided_by: Jenn
  effective_from_event_sequence:
  semantic_fingerprint:
```

`partial_observation_max_silence_ms` is a positive checked integer in each accepted policy revision. Its schema is
acceptable in v0.1, but no concrete millisecond value is frozen as an engineering fact by this architecture review.
The value remains `PROVISIONAL_BENCHMARK_REQUIRED` until benchmark evidence names the actual VCPToolBox / host
environment and supports it. Before a supported future activation profile binds such a revision, an open-span
remaining Duration is unavailable for activation use; no implementation may invent a default.

#### Remaining projection

```yaml
DurationRemainingProjection:
  schema_version: duration-remaining.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  task_id:
  lifecycle_generation:
  completion_epoch:
  estimate_revision_id:
  estimate_baseline_fingerprint:
  observation_frontier:
    latest_compatible_observation_refs: []
    observed_active_delta_ms:
    frontier_fingerprint:
  observation_currentness:
    status: NOT_TIME_BEARING | CURRENT | STALE | INDETERMINATE
    measurement_policy_revision:
    open_active_work_span_refs: []
    observation_anchor_kind: NONE | SPAN_OPEN_EVENT | LATEST_COMPATIBLE_TIMING_FACT
    observation_anchor_event_sequence: optional
    measured_through_observation_ref: optional
    latest_observation_accepted_at_utc_ms: optional
    next_observation_due_utc_ms: optional
  remaining_three_point:
    optimistic_ms: optional
    most_likely_ms: optional
    pessimistic_ms: optional
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE
  reason_codes: []
  forecast_as_of_utc_ms: optional
  valid_until_utc_ms: optional
  time_currentness_policy_revision: optional
  basis:
    based_on_event_sequence:
    policy_revision_refs: []
    input_revision_refs: []
    input_fingerprint:
  computed_at_utc_ms:
```

```text
delta = latest compatible cumulative active total - frozen baseline active total
remaining_i = max(0, estimate_i - delta)

compatible PARTIAL cumulative observation
  -> advances the observation frontier
  -> does not stale the immutable estimate

Task / result / Validation / remediation / phase work-position semantic change
  -> stales the estimate and its remaining projection

delta >= pessimistic_ms while Task remains nonterminal and zero work is not positively proven
  -> UNAVAILABLE + ESTIMATE_RANGE_EXHAUSTED
  -> no schedulable zero triple
  -> retain the immutable estimate as evidence, but require a new explicit estimate revision before remaining Duration
     can become AVAILABLE again

new estimate revision
  -> starts from the latest accepted compatible observation frontier

no open ActiveWorkSpan
  -> observation_currentness NOT_TIME_BEARING
  -> forecast_as_of, valid_until, and time_currentness_policy_revision are absent

one valid open ActiveWorkSpan with a trusted observation anchor
  -> observation_currentness CURRENT while trusted now < next_observation_due_utc_ms
  -> forecast_as_of_utc_ms is the sampled trusted Rust time
  -> valid_until_utc_ms = next_observation_due_utc_ms
  -> time_currentness_policy_revision binds the exact DurationTimingMeasurementPolicyRevision

trusted now >= next_observation_due_utc_ms
  -> freshness STALE + assessment UNAVAILABLE + ACTIVE_OBSERVATION_STALE
  -> retain the last measured value as historical evidence, but do not extrapolate it

missing policy, uncertain time, missing anchor, or irreconcilable open-span state
  -> observation_currentness INDETERMINATE
  -> assessment INDETERMINATE
```

Lower cumulative values, incompatible counter epochs, overlap ambiguity, missing baseline facts, or arithmetic
overflow make the remaining projection `INDETERMINATE`. Reporting cadence is a registered measurement-policy choice;
the final COMPLETE observation is mandatory. A compatible PARTIAL cumulative fact advances the derived frontier and
starts a new bounded silence window without changing or staling the immutable estimate. A PARTIAL fact may provide
complete cumulative coverage through its authenticated measurement instant even though the span itself remains open;
gaps in requested prefix coverage remain `coverage=PARTIAL` and are never extrapolated. High-frequency receipts cannot
create authority, mutate Task state, or silently change the estimate.

### 4.7 Authority and commands

```text
Jenn
  -> create, revise, retire, lock, and unlock any nonterminal Task Duration

Nobao
  -> maintain NOBAO_MANAGED Duration autonomously
  -> cannot modify or retire JENN_LOCKED revision

Domain Agent
  -> proposal only

Worker / executor / Validator / planner / UI
  -> proposal or timing Fact only
  -> cannot move the current pointer

execution host
  -> low-disclosure timing Receipt only

Rust core
  -> sole schema, revision, CAS, fingerprint, currentness, and observation authority
```

```text
CreateDurationEstimate
ReviseDurationEstimate
RetireDurationEstimate
LockDurationEstimate
UnlockDurationEstimate
AcceptDurationEstimateProposal
```

### 4.8 Actual timing facts

The canonical counting unit is a physical `ActiveWorkSpan`, not a Run or Validation attempt. Run and Validation
records may reference the same span; that span is counted once.

```yaml
ActiveWorkSpan:
  schema_version: active-work-span.v0.1
  active_work_span_id:
  task_id:
  lifecycle_generation:
  completion_epoch:
  task_completion_lane_id:
  measurement_clock_session:
  counter_epoch:
  covered_subject_refs: []
  measurement_policy_revision:
  source_id:
  source_fence_epoch: optional
  opened_at_event_sequence:
  semantic_fingerprint:
```

One span represents one non-overlapping interval on the declared serial Task completion lane. `covered_subject_refs`
may contain a Run, one or more Validation attempts, or both; references do not create additional counted time. The
span identity row is immutable. Cumulative observations and closure are append-only `DurationTimingFact` Events; Rust
never updates elapsed time in the identity row. At most one open span may exist per Task/lifecycle/completion/lane.

Rust alone allocates the stable span ID and lane ID. For effectful work it opens the span in the same transaction that
accepts `HostWorkStartDispositionFact(STARTED)`; for Rust-supervised non-effectful/HUMAN_ACCEPTANCE work it opens from
the corresponding canonical start command. A partial unique index permits one open span per
`(task_id, lifecycle_generation, completion_epoch, task_completion_lane_id)`. A new span cannot open until the prior
span has a COMPLETE closure Fact or an explicit indeterminate reconciliation outcome.

The authoritative elapsed measure is a monotonic counter within one `measurement_clock_session + counter_epoch`, not
the optional UTC interval. Terminal Run/Validation or supervised-stop acceptance appends the final COMPLETE fact and
closes the span. Restart reconstructs open/closed state, maximum sequence, counter epoch, and subject bindings from
Events before accepting another span. Multiple open IDs, counter reset without epoch, or any inability to prove serial
closure becomes `INDETERMINATE`; Rust never guesses that differently named spans were non-overlapping.

```yaml
DurationTimingFact:
  schema_version: duration-timing-fact.v0.1
  observation_id:
  receipt_id:
  task_id:
  active_work_span_id:
  task_completion_lane_id:
  measurement_clock_session:
  counter_epoch:
  covered_subject_refs: []
  lifecycle_generation:
  completion_epoch:
  execution_epoch: optional
  host_fence_epoch: optional
  measurement_kind: ACTIVE_ELAPSED_CUMULATIVE_MS
  cumulative_active_ms:
  measurement_sequence:
  coverage: PARTIAL | COMPLETE
  observed_active_interval_start_utc_ms: optional
  observed_active_interval_end_utc_ms: optional
  source: RUST_SUPERVISED_MONOTONIC | TRUSTED_HOST_RECEIPT
  measurement_policy_revision:
  source_id:
  coverage_fingerprint:
  accepted_at_event_sequence:
  accepted_at_utc_ms:
```

For the same span, clock session, counter epoch, and measurement policy, `measurement_sequence` and
`cumulative_active_ms` must be monotonic.
Duplicate receipts are idempotent. A lower cumulative value, overlapping incompatible source, or changed coverage
fingerprint is rejected or reconciled; it is never subtracted silently.

The span, every accepted Fact for that span, and its current remaining projection bind the same exact
`DurationTimingMeasurementPolicyRevision`. A policy change does not reinterpret old observation cadence. If an open
span cannot be closed or reconciled under its bound policy, its remaining projection is `INDETERMINATE`; Rust does not
move it to a newer silence value merely to extend validity.

`accepted_at_event_sequence` and `accepted_at_utc_ms` come from the canonical Rust Event envelope, not the host or
caller. For an open span with no accepted timing Fact yet, the trusted UTC instant of its opening Event is the
observation anchor. The checked exclusive due instant is that anchor plus the policy's
`partial_observation_max_silence_ms`; later compatible PARTIAL facts move the anchor forward, while duplicate or
rejected receipts do not.

A cumulative measurement of zero is valid when it is an authenticated measurement. It never means missing evidence,
unknown remaining work, or a zero Duration estimate.

Rust sums only unique, complete, mutually non-overlapping spans under the same Task, lifecycle generation, completion
epoch, serial lane, and compatible measurement policy. The same span referenced by Run and Validation counts once.
Parallel spans, clock-session ambiguity, counter reset without a new epoch, or overlap that cannot be proved absent
make the outcome `INDETERMINATE`; v0.1 does not guess a union duration.

Actual time cannot be guessed from:

```text
client wall-clock
Agent self-report
Task created_at to DONE
provider latency logs
Deadline
WALL_CLOCK_MS Budget
```

### 4.9 Outcome and learning

After Task completion, Rust may derive:

```yaml
DurationOutcomeProjection:
  schema_version: duration-outcome.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  task_id:
  lifecycle_generation:
  completion_epoch:
  compared_estimate_revision_id:
  estimate_baseline_fingerprint:
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE
  actual_active_ms_after_estimate_baseline: optional
  included_observation_ids: []
  included_active_work_span_ids: []
  relation: BELOW_OPTIMISTIC | WITHIN_OPTIMISTIC_TO_MOST_LIKELY | WITHIN_MOST_LIKELY_TO_PESSIMISTIC | ABOVE_PESSIMISTIC
  measurement_policy_revision:
  reason_codes: []
  basis:
    based_on_event_sequence:
    policy_revision_refs: []
    input_revision_refs: []
    input_fingerprint:
  computed_at_utc_ms:
```

For each unique span, the latest compatible cumulative observation is used once. Complete Task actual time is the
checked integer sum of complete, proven non-overlapping span totals. Partial coverage remains `PARTIAL`; overlap,
counter, or clock ambiguity is `INDETERMINATE`. Neither is extrapolated.

The comparison covers active time after the exact estimate baseline; an estimate created midway through a Task is not
compared with the Task's full-lifecycle active time. Actual time above pessimistic is retained exactly. Timing facts do
not complete Run, Validation, or Task; settle
Budget; or automatically modify the current estimate.

Learning is limited to:

```text
derive calibration projection from complete compatible low-disclosure observations
cite historical observation or calibration as basis_refs for a new explicit revision
```

Hidden model training, silent outlier deletion, automatic current-estimate mutation, and Worker self-approval are
forbidden in v0.1.

When calibration is materialized, it uses the same analytical contract rather than an ad hoc counter:

```yaml
DurationCalibrationProjection:
  schema_version: duration-calibration.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  calibration_scope_fingerprint:
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE
  reason_codes: []
  complete_outcome_refs: []
  excluded_outcome_refs: []
  low_disclosure_aggregate:
    sample_count:
    signed_error_sum_ms:
    absolute_error_sum_ms:
  basis:
    based_on_event_sequence:
    policy_revision_refs: []
    input_revision_refs: []
    input_fingerprint:
  computed_at_utc_ms:
```

It is read-only evidence for a later explicit estimate revision. It cannot train a hidden model, choose a replacement
estimate, expose raw timing history, or become an execution gate.

### 4.10 Failure, recovery, and rejected complexity

Reason codes:

```text
NO_CURRENT_ESTIMATE
ESTIMATE_CONTEXT_STALE
ESTIMATE_POLICY_UNAVAILABLE
TASK_SCOPE_CHANGED
COMPLETION_ENVELOPE_CHANGED
VALIDATION_WORK_SCOPE_CHANGED
WORK_POSITION_CHANGED
BASIS_EVIDENCE_MISSING
OBSERVATION_COVERAGE_INCOMPLETE
OBSERVATION_POLICY_MISMATCH
OBSERVATION_POLICY_UNAVAILABLE
OBSERVATION_TIME_AUTHORITY_UNCERTAIN
ACTIVE_OBSERVATION_STALE
ESTIMATE_RANGE_EXHAUSTED
UNSUPPORTED_COMPOSITE_ACTIVITY
ACTIVE_WORK_SPAN_OVERLAP
ACTIVE_WORK_COUNTER_EPOCH_AMBIGUOUS
ACTIVE_WORK_CLOCK_SESSION_AMBIGUOUS
```

Missing, stale, or indeterminate Duration only makes Schedule / TimeCriticalPath projections PARTIAL or UNAVAILABLE.
It does not change selection eligibility, Critical Work Frontier, Goal Health, progress, closure, or otherwise legal
non-time admission.

Recovery validates revision monotonicity, current pointer, Task envelope, fingerprint, span identity, serial-lane
non-overlap, counter epochs, observation deduplication, and measurement policy. Inconsistency becomes
`INDETERMINATE`; no value is guessed. Projection rebuild creates no Event,
Run, permit, BudgetReservation, CapacityClaim, Outbox, or Task mutation.

v0.1 rejects:

```text
probability distribution, Monte Carlo, correlation matrix, numeric confidence percentage
time-based percent_complete
Goal / Run / Validation parallel canonical Duration
internal segment DAG or multiple serial Calendars
resource scaling or parallel-shortening formula
preemptive Duration
wall-clock difference as active work
automatic ML update
Duration as not_before, Deadline, Budget, permit, or execution gate
```

## 5. Calendar v0.1

### 5.1 Decision

Calendar is a versioned availability contract. It answers when work may be planned and, only when explicitly bound for
admission, when Rust may commit a new one-time host start authority. It does not attest the remote physical start time.

```text
Calendar closed
  != Deadline reached
  != Task FAILED / BLOCKED / CANCELLED
  != active Run must stop

Calendar open
  != Task eligible
  != Capacity available
  != permit granted
  != Run authorized
```

Calendar is not Duration, Priority, Task recurrence, timer, reminder, or completion evidence.

### 5.2 CalendarRevision

```yaml
CalendarRevision:
  schema_version: calendar.v0.1
  calendar_id:
  calendar_revision:
  supersedes_revision_id: optional
  timezone:
    iana_tzid:
    tzdb_release:
    tzdb_digest:
  effective_local_date_from: ASCII_YYYY-MM-DD
  effective_local_date_until_exclusive: optional_ASCII_YYYY-MM-DD
  weekly_windows:
    - rule_id:
      weekdays: [MON, TUE, WED, THU, FRI, SAT, SUN]
      start_local_second: 0..86399
      end_local_second: 0..86399
      end_day_offset: 0 | 1
  inclusions:
    - exception_id:
      local_start: ASCII_YYYY-MM-DDTHH:MM:SS
      local_end: ASCII_YYYY-MM-DDTHH:MM:SS
      reason:
  exclusions:
    - exception_id:
      local_start: ASCII_YYYY-MM-DDTHH:MM:SS
      local_end: ASCII_YYYY-MM-DDTHH:MM:SS
      reason:
  authority_mode: JENN_LOCKED | NOBAO_MANAGED
  created_by:
  reason:
  effective_from_event_sequence:
  source_artifact_ref: optional
  reducer_version:
  semantic_fingerprint:
```

Rules:

```text
all intervals are [start, end)
end_day_offset * 86400 + end_local_second must be greater than start_local_second
one weekly window may not exceed 24 hours
inclusions are unioned with base windows; exclusions are subtracted last
exclusion wins over inclusion
overlapping or adjacent UTC segments normalize into one segment
an empty base week is valid and means closed by default
there is no hidden weekday or 09:00-17:00 default
leap-second arithmetic is not supported
local date/time uses proleptic Gregorian years 0001..9999, ASCII digits, fixed width, and second precision
local date/time contains no UTC offset, zone abbreviation, fractional second, locale text, or Unicode alternative
exception local_end must be later than local_start and no exception interval may exceed 366 local days in v0.1
the exact canonical ASCII encodings participate in semantic_fingerprint
```

`iana_tzid` must exist in the Rust-registered IANA tzdb bundle. JavaScript, clients, UI, and execution hosts cannot
supply private timezone rules.

v0.1 freezes:

```text
DST gap policy: NO_SYNTHETIC_INSTANT
DST fold policy: MATCH_BOTH_INSTANTS
```

A nonexistent local instant is not shifted. A repeated local interval matches both real UTC occurrences. Membership
is defined by taking each real UTC instant, converting it through the revision-pinned tzdb into one local civil tuple,
and testing that tuple against the normalized local `[start, end)` rules. Thus a gap has no real instant to match and
both fold instants independently match the same local tuple. Implementations may materialize transitions for speed but
must produce this result. This does not create two Tasks or Runs; it only evaluates availability at real instants.

### 5.3 CalendarBindingRevision

```yaml
CalendarBindingRevision:
  schema_version: calendar-binding.v0.1
  binding_id:
  binding_revision:
  supersedes_revision_id: optional
  scope: SYSTEM | GOAL | TASK | CAPACITY_POOL
  scope_id:
  purpose: PLANNING_WORK_TIME | NEW_START_AUTHORITY_ALLOWED
  calendar_id:
  calendar_revision:
  authority_mode: JENN_LOCKED | NOBAO_MANAGED
  created_by:
  reason:
  effective_from_event_sequence:
  initial_gate_generation:
  semantic_fingerprint:
```

Host online status, VCPMobile background survival, current executor process health, and actual free slots are Capacity
offers, not Calendar facts. A pool Calendar expresses declared availability windows; the host must still submit a
fresh Capacity offer.

Revision rows never mutate to record later status. `CURRENT`, `SUPERSEDED`, and `RETIRED` are reduced from the
canonical current pointer plus append-only activation, supersession, and retirement Events. A retirement Event names
the exact revision and advances its binding fence when admission purpose applies.

Admission transition state is a Rust-owned Current State row updated with its Event in one transaction:

```yaml
CalendarBindingGateState:
  schema_version: calendar-binding-gate-state.v0.1
  result_semantics: OPERATIONAL_REDUCER_VIEW
  binding_id:
  binding_revision:
  binding_gate_generation:
  current_outcome: OPEN | CLOSED | INDETERMINATE
  current_occurrence_key: optional
  time_policy_revision:
  reducer_currentness: CURRENT | REBUILD_REQUIRED | REBUILDING | INDETERMINATE
  reduced_through_event_sequence:
  reducer_contract_version: calendar-binding-gate-state.v0.1
  policy_revision_refs: []
  input_fingerprint:
  reduced_at_utc_ms:
  next_time_transition_utc_ms: optional
```

The immutable binding supplies `initial_gate_generation`. Every revision/retirement, occurrence-key change,
time-policy/clock-session change, or `current_outcome` change creates an Event and atomically replaces Gate State with
a strictly larger generation. This includes entering or leaving `INDETERMINATE`; an old permit can never revive when
time becomes trusted again. Recovery rebuilds and verifies the row from Events before normal admission. Permit vectors
reference Gate State, never a mutated revision row.

### 5.4 Planning Calendar resolution

All time-bearing projections use the same embedded provenance contract:

```yaml
PlanningCalendarResolutionSnapshot:
  schema_version: planning-calendar-resolution.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  resolution_id:
  task_id:
  lifecycle_generation:
  resolution_mode: RESOURCE_UNCONSTRAINED | EXPLICIT_POOL_ASSIGNMENT
  task_binding_revisions: []
  goal_binding_revisions: []
  system_binding_revisions: []
  capacity_request_set_revision: optional
  compatible_pool_set_fingerprint: optional
  selected_pool_revision_refs: []
  pool_calendar_binding_revisions: []
  resolved_calendar_revisions: []
  tzdb_bindings: []
  materialization_fingerprints: []
  coverage_start_utc_ms:
  coverage_end_utc_ms:
  resolution_policy_revision:
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE
  reason_codes: []
  basis:
    based_on_event_sequence:
    policy_revision_refs: []
    input_revision_refs: []
    input_fingerprint:
  computed_at_utc_ms:
  forecast_as_of_utc_ms:
  valid_until_utc_ms:
  time_currentness_policy_revision:
```

`SchedulePlanProjection` and `TimeCriticalPathProjection` embed or reference this exact schema; the separately deferred
Resource Scheduling v0.2 draft must do the same. A bare Calendar ID or ad hoc fingerprint is insufficient.
Resource-unconstrained mode records the compatible pool set without choosing a fastest pool. Explicit-pool mode
records the exact proposed pool revisions. Any listed revision, pool set, tzdb, materialization coverage, policy, or
event basis change stales the owning projection.

For a Task-level planning forecast:

```text
exactly one current direct Task PLANNING_WORK_TIME binding
  -> use it

multiple same-scope bindings with the same normalized Calendar fingerprint
  -> canonicalize the sorted binding revisions and use the shared result

multiple same-scope bindings with different normalized Calendar fingerprints
  -> PLANNING_CALENDAR_AMBIGUOUS

otherwise exactly one nearest current Goal-ancestor binding
  -> use it

same-level Goal bindings disagree
  -> PLANNING_CALENDAR_AMBIGUOUS

otherwise current SYSTEM planning binding
  -> use it

still absent
  -> planning time unavailable
  -> non-time execution is not blocked
```

Once a planning projection assigns a Capacity pool, the pool's current planning Calendar is intersected with the Task
planning Calendar. An unassigned alternative host cannot be silently used to widen the result.

Time Critical Path is resource-unconstrained and normally has no pool assignment. It may include a pool Calendar only
when the Capacity request pins one host / pool, or every compatible current pool has the same normalized planning
Calendar fingerprint. Different compatible pool Calendars produce `PLANNING_CALENDAR_AMBIGUOUS`; Rust does not choose
the fastest host. Only the separately deferred Resource Scheduling v0.2 design may propose an explicit assignment.

The same one-or-identical rule applies independently at SYSTEM, Goal ancestry, Task, and selected-pool scope. Two
different current planning bindings are never resolved by creation time, source order, or a fastest-window heuristic.

### 5.5 Admission Calendar resolution

`NEW_START_AUTHORITY_ALLOWED` is a synchronous host-acceptance constraint only when the exact work request's current profile has
`admission_calendar=ENFORCING`:

```text
intersect every current SYSTEM binding
intersect every applicable Goal-ancestry binding
intersect every current Task binding
intersect every selected Capacity-pool binding
```

No admission binding means Calendar imposes no start-authority restriction. A declared binding whose revision, tzdb,
currentness, or time authority cannot be verified produces `INDETERMINATE` and fails closed for a new authority commit.

```yaml
CalendarAdmissionAssessment:
  schema_version: calendar-admission-assessment.v0.1
  result_semantics: SYNCHRONOUS_ASSESSMENT
  reuse_scope: SAME_CONSISTENT_READ_SET_ONLY
  task_id:
  work_request_id:
  work_request_revision:
  evaluated_at_utc_ms:
  time_policy_revision:
  source_binding_revisions: []
  source_calendar_revisions: []
  tzdb_bindings: []
  outcome: OPEN | CLOSED | INDETERMINATE
  effective_open_from_utc_ms: optional
  effective_open_until_utc_ms: optional
  calendar_start_authority_fence:
    bindings:
      - binding_id:
        binding_revision:
        binding_gate_generation:
        active_occurrence_key: optional
    aggregate_fingerprint:
  reason_codes: []
  read_event_sequence:
  policy_revision_refs: []
  input_revision_refs: []
  input_fingerprint:
```

The assessment is reusable only inside its original consistent read set and is diagnostic afterward. In an ENFORCING scope, `create_run`, permit issuance, Outbox claim,
dispatch authorization, effectful Validation admission, host-acceptance reconciliation, and startup recovery must
synchronously recompute the applicable Calendar gate from canonical definitions using one Rust wall-clock sample.

In a SHADOW scope, Calendar definitions, materialization, and shared binding generations continue to be recorded for
diagnostics and for other ENFORCING scopes, but they cannot deny this work, enter its permit as start authority, or
reject host acceptance. `SUSPENDED_FAIL_CLOSED` is rejected earlier by the enforcement profile.

Run and permit bind the following authority only in an ENFORCING Calendar scope:

```yaml
calendar_authority_binding:
  source_binding_revisions: []
  source_calendar_revisions: []
  tzdb_bindings: []
  effective_open_from_utc_ms:
  effective_open_until_utc_ms:
  calendar_start_authority_fence:
    bindings:
      - binding_id:
        binding_revision:
        binding_gate_generation:
        active_occurrence_key: optional
    aggregate_fingerprint:
  time_policy_revision:
```

`now == open_from` is open. `now == open_until` is closed.

`create_run` inside a window does not grant start authority. Rust must commit a matching current
`HostWorkAcceptanceFact(ACCEPTED)` before the window closes. That commit grants one bounded start authority and moves
the Run to `LEASED`; it does not prove actual process or effect start. A host timestamp cannot retroactively establish
Calendar compliance.

```text
host definitely did not receive committed start authority
  -> Run may become REJECTED

canonical acceptance may have committed and host launch disposition is unknown
  -> Run becomes UNKNOWN
  -> no automatic retry

canonical host acceptance committed inside the window
  -> later ordinary Calendar close does not revoke the bounded authority
  -> actual STARTED may follow only before start_authority_expires_at_utc_ms and all dynamic guards
  -> Calendar close alone does not stop an already STARTED Run
```

Calendar revision applies only from its Event sequence forward. Each admission binding owns a monotonic
`binding_gate_generation`. Revision, retirement, occurrence-key change, time-policy/clock-session change, or any
outcome transition including entry to or recovery from `INDETERMINATE` advances that generation. A permit
binds the complete sorted fence vector; any current mismatch permanently removes new-start authority from an
unaccepted permit. Rust need not fan out a generation update to every descendant Task. A fence change does not stop
an already STARTED Run by itself, but it prevents a not-yet-accepted permit from gaining authority. Once acceptance is
committed, an ordinary Calendar close, occurrence change, or Calendar binding-generation advance cannot revoke that
historical authority. Only its bounded expiry and non-Calendar active-stop / Control Intent / UNKNOWN / host-session /
permit / Dependency / effect-scope revocation guards decide whether physical launch remains legal.

### 5.6 CalendarWindowMaterialization

```yaml
CalendarWindowMaterialization:
  schema_version: calendar-materialization.v0.1
  projection_id:
  calendar_id:
  calendar_revision:
  tzdb_release:
  tzdb_digest:
  reducer_version:
  coverage_start_utc_ms:
  coverage_end_utc_ms:
  windows:
    - occurrence_key:
      segment_ordinal:
      start_utc_ms:
      end_utc_ms:
      source_rule_refs: []
  input_fingerprint:
  based_on_event_sequence:
  materialized_at_utc_ms:
```

Materialization is rebuildable and has no authority. `occurrence_key` derives from the Calendar revision, source rule,
local anchor date, and segment ordinal. It must not expose private calendar titles or raw event contents.

Rolling planning may use it only when the current projection completely covers the horizon. Admission never guesses
from a short horizon: Rust computes `now` and the next transition from the canonical Calendar and bound tzdb, or returns
`INDETERMINATE`.

An OS tzdb update cannot mutate an old Calendar revision. `RebaseCalendarTzdb` creates a new revision. Historical
materializations remain diagnostic projections only; historical admission proof comes from the Run / permit Calendar
snapshot and canonical `HostWorkAcceptanceFact` Event. If the bound tzdb is unavailable for a new gate calculation,
admission fails closed.

Full RFC 5545 recurrence, cron, recurring Task creation, and external-calendar bidirectional sync are outside v0.1.
An external calendar can submit a low-disclosure proposal, but only an accepted canonical command creates a revision or
binding.

### 5.7 Durable Calendar wake

```yaml
CalendarWakeRecord:
  schema_version: calendar-wake.v0.1
  wake_id:
  binding_id:
  binding_revision:
  wake_kind: WINDOW_OPEN | WINDOW_CLOSE | MATERIALIZATION_REFRESH
  due_at_utc_ms:
  binding_gate_generation:
  status: PENDING | FIRED | SUPERSEDED
  idempotency_key:
  created_event_sequence:
  fired_event_sequence: optional
```

The wake record, current state, and Event are written in one SQLite transaction.

```text
setTimeout / node-schedule / VCP scheduler
  -> wake hint only

CalendarWakeRecord + Calendar / Event facts
  -> due, missed-wake, and recovery authority
```

A wake only asks Rust to re-evaluate. It never creates Run, Task, permit, Deadline, or side effect. Duplicate wakes are
idempotent. A revision supersedes old wakes atomically.

Startup processes `due_at <= now` before normal selection. A missed historical occurrence is never backfilled. Rust
evaluates the Calendar at current trusted time, so the current result may be `OPEN` or `CLOSED`. Before dispatch
reopens, Rust must process every due transition in order or produce the equivalent deterministic fence-vector
advancement that makes every pre-recovery start authority stale. The system never manufactures historical Runs or
catch-up execution.

When time authority is `UNCERTAIN`:

```text
planning -> unavailable or stale
new admission -> INDETERMINATE and fail closed
wake -> do not invent a FIRED instant
active Run -> Calendar does not stop it
```

### 5.8 Authority and invariants

```text
Jenn
  -> may create, revise, retire, or lock any Calendar and binding

Nobao
  -> may manage NOBAO_MANAGED Calendar contracts
  -> may add stricter admission bindings
  -> may not loosen or retire JENN_LOCKED bindings

Domain Agent / UI
  -> proposal only unless an explicit narrow planning authority exists

execution host
  -> does not own Calendar truth
  -> reports dynamic availability through Capacity

Rust core
  -> sole revision, resolution, tzdb-validation, materialization-acceptance,
     admission-assessment, gate-generation, and wake writer
```

```text
Calendar is not Deadline
Calendar is not Capacity
Calendar is not timer
Calendar open does not grant execution
Calendar close does not revoke already committed bounded start authority or stop an already STARTED Run
Materialization never grants authority
tzdb never drifts silently
durable wake never executes work
```

## 6. Capacity v0.1

### 6.1 Decision and v0.1 scope

Capacity expresses how many concurrent work positions a registered execution host currently offers. It is not Budget,
permission, Priority, Calendar, Deadline, Duration, or provider quota.

```text
Budget available != Capacity available
Capacity available != Budget allowed
Capacity available != capability matched
Capacity available != permit valid
Capacity available != P3 satisfied
```

v0.1 supports integer slots only:

```text
EXECUTION_SLOT
NAMED_EXCLUSIVE_SLOT
```

CPU millicores, RAM, GPU topology, affinity, bin packing, autoscaling, and distributed cluster scheduling are rejected
from v0.1. Rate limits, token ceilings, money, and cumulative wall-clock remain Budget or provider-policy facts.

### 6.2 CapacityPoolRevision

Before a pool can exist, Rust must accept one low-disclosure host inventory domain:

```yaml
HostCapacityDomainRevision:
  schema_version: host-capacity-domain.v0.1
  capacity_domain_id:
  domain_revision:
  supersedes_revision_id: optional
  host_id:
  host_registration_revision:
  resource_class: EXECUTION_SLOT | NAMED_EXCLUSIVE_SLOT
  physical_inventory_key_digest:
  maximum_physical_units:
  attesting_adapter_id:
  attesting_adapter_revision:
  authority_mode: JENN_LOCKED | NOBAO_MANAGED
  created_by:
  effective_from_event_sequence:
  semantic_fingerprint:
```

The allowlisted Rust host adapter derives `physical_inventory_key_digest` from its stable local inventory identity;
the host caller cannot submit an arbitrary alias. Rust enforces one current domain per
`(host_id, physical_inventory_key_digest)` and checked total pool ceilings no greater than
`maximum_physical_units`. Raw device IDs or private host inventory are never stored. A remote adapter that cannot
attest non-overlap is not Capacity-admission capable and remains shadow-only.

v0.1 deliberately avoids arbitrary overlapping sets:

```text
EXECUTION_SLOT
  -> exactly one current aggregate domain per host
  -> it contains every executor slot that host offers to AGENTS OS

NAMED_EXCLUSIVE_SLOT
  -> exactly one physical unit per domain
  -> maximum_physical_units = 1
  -> adapter derives a stable single-resource digest
```

Multiple aggregate execution domains or multi-unit named domains are invalid in v0.1. A future partition registry
would require independently verifiable disjoint-set attestations; a digest of an arbitrary set is insufficient.

Revising a domain must preserve `capacity_domain_id`, host, resource class, and
`physical_inventory_key_digest`. A domain/pool cannot retire, rebind, or replace its accounting key while any
`CLAIMED`, `ALLOCATED`, `RELEASING`, or `UNKNOWN` claim may occupy it. Introducing a genuinely new physical inventory
key requires a new fenced host session and proof that the old key has zero occupancy; otherwise both keys are
quarantined. Recovery counts historical-revision occupancy before enabling the current pool.

```yaml
CapacityPoolRevision:
  schema_version: capacity-pool.v0.1
  pool_id:
  pool_revision:
  host_id:
  capacity_domain_id:
  capacity_domain_revision:
  capacity_accounting_key_digest:
  resource_class: EXECUTION_SLOT | NAMED_EXCLUSIVE_SLOT
  unit: SLOT
  policy_ceiling_units:
  max_offer_ttl_ms:
  claim_lease_ms:
  allocation_lease_ms:
  parameter_value_classes:
    PROVISIONAL_BENCHMARK_REQUIRED:
      - max_offer_ttl_ms
      - claim_lease_ms
      - allocation_lease_ms
  benchmark_evidence_refs: []
  measured_environment_fingerprint:
  host_watchdog_contract_version:
  capability_profile_ref:
  enabled: boolean
  authority_mode: JENN_LOCKED | NOBAO_MANAGED
  created_by:
  reason:
  effective_from_event_sequence:
  semantic_fingerprint:
```

```text
policy_ceiling_units is a nonnegative integer
max_offer_ttl_ms, claim_lease_ms, and allocation_lease_ms are positive integers
all three timing values remain activation-blocked until the current pool revision binds host-adapter benchmark evidence
NAMED_EXCLUSIVE_SLOT has a stable low-disclosure capability profile and ceiling 1
one pool belongs to one concrete host in v0.1
at most one enabled current pool may exist for one `(host_id, capacity_domain_id)`
every concrete host-local unit belongs to exactly one registered capacity domain
two domains may not describe overlapping physical inventory
pool revision is not a host offer
slot units cannot convert into money, token, Duration, or Priority
every offered unit in one pool must satisfy the entire capability_profile_ref (homogeneous intersection semantics)
capability union across heterogeneous slots is forbidden
```

If a host's execution slots are heterogeneous, v0.1 may offer only the safely homogeneous subset represented by its
single aggregate EXECUTION_SLOT pool. Other units remain shadow-only or appear as genuinely separate one-unit
`NAMED_EXCLUSIVE_SLOT` resources where that model is accurate. General capability-partitioned execution pools are
deferred to the disjoint-partition v0.2+ contract; Rust never treats a union profile as if every unit had every
capability.

Static availability uses a `CAPACITY_POOL` Calendar binding. Dynamic online state and free-unit declarations still
require a fresh HostCapacityOffer.

### 6.3 CapacityRequestSetRevision

```yaml
CapacityRequestSetRevision:
  schema_version: capacity-request-set.v0.1
  request_set_id:
  request_revision:
  task_id:
  work_subject_kind: TASK_EXECUTION | VALIDATION_REQUIREMENT
  work_subject_id:
  task_spec_revision:
  validation_requirement_revision: optional
  requirements:
    - requirement_id:
      resource_class: EXECUTION_SLOT | NAMED_EXCLUSIVE_SLOT
      units:
      capability_profile_ref:
      host_binding: ANY_COMPATIBLE | PINNED_HOST
      pinned_host_id: optional
  composition: ALL_OF
  created_by:
  reason:
  effective_from_event_sequence:
  semantic_fingerprint:
```

All `units` are positive integers. Every ordinary effectful host Run requests at least one `EXECUTION_SLOT`.

`TASK_EXECUTION` revision follows Task-spec mutation, quiescence, CAS, and fencing. `VALIDATION_REQUIREMENT` revision
binds the exact Requirement revision. Neither can rewrite an active Run's request or allocation.

Pure ledger reducer work, Fact / Receipt acceptance, database recovery, non-effectful deterministic Validation, and
HUMAN_ACCEPTANCE do not fabricate ordinary executor claims.

### 6.4 HostCapacityOffer

```yaml
HostCapacityOffer:
  schema_version: host-capacity-offer.v0.1
  offer_id:
  pool_id:
  pool_revision:
  host_id:
  capacity_domain_id:
  capacity_domain_revision:
  capacity_accounting_key_digest:
  host_session_id:
  host_fence_epoch:
  offer_generation:
  state: ACCEPTING | DRAINING | UNAVAILABLE
  offered_units:
  offered_ttl_ms:
  capability_fingerprint:
  host_observed_at: optional_non_authoritative
  accepted_at_utc_ms:
  expires_at_utc_ms:
  authentication_ref:
  receipt_id:
```

Rust computes `expires_at_utc_ms` from ledger acceptance time and a policy-bounded positive TTL. Host, VCPChat,
VCPMobile, and JavaScript clocks do not decide freshness.

`offered_units` means the pool's total units currently made available to AGENTS OS after subtracting host-local work
outside AGENTS OS, but before subtracting any current ledger `CapacityClaim`. It is not a report of remaining free
units after claims. This definition prevents the accounting formula from deducting current claims twice.

`offered_ttl_ms` may not exceed the current pool `max_offer_ttl_ms`. For one pool / session, a higher accepted
`offer_generation` supersedes the lower generation; duplicate generation with a different payload is a protocol
conflict.

```text
effective_offered_units = min(policy_ceiling_units, current fresh offered_units)

missing / expired / wrong-session / wrong-fence offer
  -> no new claim

DRAINING
  -> no new claim

UNAVAILABLE
  -> no new claim
```

An offer is willingness evidence only. It is not an allocation, permit, capability authorization, host acceptance, or
execution result. A suspended or disconnected VCPMobile session cannot keep offering from historical uptime.

### 6.5 CapacityClaim and host allocation receipt

```yaml
CapacityClaim:
  schema_version: capacity-claim.v0.1
  claim_id:
  claim_set_id:
  owner_kind: RUN
  owner_id:
  task_id:
  run_id:
  work_request_id:
  work_request_revision:
  enforcement_scope_assignment_revision:
  enforcement_profile_revision:
  capacity_pool_allowlist_fingerprint:
  request_set_id:
  request_revision:
  requirement_id:
  pool_id:
  pool_revision:
  capacity_domain_id:
  capacity_domain_revision:
  capacity_accounting_key_digest:
  host_id:
  units:
  offer_id:
  offer_generation:
  host_session_id:
  host_fence_epoch:
  claim_generation:
  claim_lease_generation:
  allocation_lease_generation: optional
  status: CLAIMED | ALLOCATED | RELEASING | RELEASED | EXPIRED | UNKNOWN
  claim_lease_expires_at_utc_ms:
  allocation_lease_expires_at_utc_ms: optional
  permit_id:
  outbox_intent_id:
  idempotency_key:
  created_event_sequence:
  updated_event_sequence:
```

Every v0.1 claim belongs to one Run, exact work-request revision, Task-owned request set, and permit. Caller-selected
or control-work claims are invalid.

```yaml
HostCapacityAllocationReceipt:
  schema_version: host-capacity-allocation-receipt.v0.1
  receipt_id:
  claim_set_id:
  host_id:
  host_session_id:
  host_fence_epoch:
  claims:
    - claim_id:
      pool_id:
      pool_revision:
      offer_generation:
      claim_generation:
      units:
  fact: ACQUIRED | RENEWED | RELEASED | REJECTED_NOT_ACQUIRED
  acquired_state: # required only for ACQUIRED
    allocation_id:
    allocation_generation:
    allocation_lease_generation:
    allocation_lease_policy_revision:
    host_watchdog_generation:
    host_watchdog_policy_ttl_ms:
    host_watchdog_armed_before_send: boolean
    local_allocation_handle_digest:
  renewed_state: # required only for RENEWED
    allocation_id:
    allocation_generation:
    previous_allocation_lease_generation:
    new_allocation_lease_generation:
    allocation_lease_policy_revision:
    previous_host_watchdog_generation:
    new_host_watchdog_generation:
    host_watchdog_policy_ttl_ms:
    candidate_watchdog_armed_before_send: boolean
    old_watchdog_not_fired: true
    local_allocation_handle_digest:
  released_state: # required only for RELEASED
    allocation_id:
    allocation_generation:
    last_allocation_lease_generation:
    last_host_watchdog_generation:
    release_generation:
    local_allocation_handle_digest:
    no_member_remains_allocated: true
  rejection_state: # required only for REJECTED_NOT_ACQUIRED
    rejection_generation:
    reason_code:
    no_member_acquired: true
  host_observed_at: optional_non_authoritative
  accepted_at_utc_ms:
```

The payload is a four-way tagged union. Each fact requires exactly its same-named state branch and forbids all three
others. `RENEWED` alone requires proof that the old watchdog has not fired and a newly armed candidate watchdog.
`RELEASED` binds the last known generations and release proof but creates no new lease/watchdog; it remains legal after
watchdog expiry. `REJECTED_NOT_ACQUIRED` forbids every allocation/lease/watchdog/handle field and proves no member of
the complete current claim set was acquired. An acquired-then-aborted allocation can only close with `RELEASED`, never
`REJECTED_NOT_ACQUIRED`. Invalid branch combinations are protocol conflicts.

The host owns its local slots. Rust accepts only a low-disclosure receipt matching the complete current claim set,
every generation, session, fence, permit, and unit count. Partial claim-set acquisition is rejected and reconciled as
UNKNOWN unless the host proves no member was acquired.

For an ordinary Run, the claim set moves and releases as one accounting unit. A partial or contradictory member state
causes the entire set to become UNKNOWN until authoritative reconciliation.

```text
CLAIMED -> ALLOCATED | RELEASING | RELEASED | EXPIRED | UNKNOWN
ALLOCATED -> RELEASING | RELEASED | UNKNOWN
RELEASING -> RELEASED | UNKNOWN
UNKNOWN -> ALLOCATED | RELEASED only through authoritative reconciliation Fact
RELEASED / EXPIRED -> closed to normal commands
```

`EXPIRED` is legal only when the Outbox was never claimed or dispatched and host allocation is proven impossible.
Once dispatch may have occurred, lease expiry produces `UNKNOWN`, not release.

`CLAIMED -> RELEASING` is legal only when Rust has a complete authenticated `ACQUIRED` proposal, canonical work
acceptance was rejected, execution absence is proven, and the idempotent release finalizer is created in the same
transaction. Without that complete branch proof, the claim set becomes `UNKNOWN`; generic commands cannot select
`RELEASING`.

`CLAIMED`, `ALLOCATED`, `RELEASING`, and `UNKNOWN` consume full units. `RELEASED` and `EXPIRED` consume zero.

`RELEASED` and `EXPIRED` are not evidence sinks. A contradictory authenticated current-generation host Fact is
always appended, creates `CapacityTerminalContradiction`, quarantines the complete claim-set units, changes affected
pool accounting to `INDETERMINATE`, and never revives the old permit. If the associated Run is nonterminal and its
execution outcome is unresolved, the ordinary contradiction path makes it `UNKNOWN`. If the Run is already terminal,
its terminal state remains immutable; a positive-execution contradiction follows Section 8.6 late-effect
reconciliation, challenges affected completion support, and must not reopen the Run merely because Capacity evidence
arrived late.

### 6.6 Admission accounting

Let:

```text
E = effective_offered_units
O = units charged to all current v0.1 Run claims
```

Because `E` is total AGENTS OS-offered capacity before ledger claims, `O` is subtracted exactly once by the inequality
below.

Admission uses:

```text
ordinary:
  O + requested <= E
```

Accounting and the inequalities are evaluated per stable `(host_id, capacity_accounting_key_digest)`, which equals
the domain's `physical_inventory_key_digest`, not per replaceable domain ID. Claims from every historical revision,
including `UNKNOWN`, remain charged to that same key. Because v0.1 permits only one enabled current pool per domain, a
host cannot offer one physical unit through two pools and have it counted twice.

If a later pool revision or offer makes `O > E`, the pool projection becomes `OVERALLOCATED` and refuses new
claims. It does not preempt active work.

Planning and selection may observe Capacity but cannot create a claim, consume units, or promise later availability.

Every `ALL_OF` requirement for an ordinary Run is resolved in the same `create_run` SQLite transaction:

```text
revalidate Task / Dependency / Validation / Deadline / Budget / authorization / P3
revalidate request revision
select compatible concrete pool and fresh host offer
check Calendar, session, fence, capability, and accounting formula
create every required CapacityClaim
resolve the exact phase-correct commitment: allocate when required or reuse the immutable snapshot unchanged
create BudgetReservation, Run, Event, permit, and Outbox; include a newly allocated commitment in the same transaction
commit once
```

Any failed requirement rolls back the entire transaction. No partial claim set or half-Run remains. Pool choice is an
admission binding, not a second selection record.

All requirements for one Run must resolve to the same concrete host and host session in v0.1. Cross-host atomic claim
sets are rejected rather than approximated with a distributed transaction.

Host / pool choice uses deterministic first-fit only: pinned host first when required, otherwise canonical
`(host_id, pool_id, pool_revision)` byte order, selecting the first single-host combination satisfying the whole
request set. Load optimization belongs to Resource-constrained Scheduling v0.2.

Permit binds:

```yaml
capacity_authority_binding:
  work_request_id:
  work_request_revision:
  request_set_id:
  request_revision:
  claim_set_id:
  claims:
    - claim_id:
      claim_generation:
      pool_id:
      pool_revision:
      units:
      offer_id:
      offer_generation:
      host_session_id:
      host_fence_epoch:
      claim_lease_expires_at_utc_ms:
      claim_lease_generation:
      allocation_lease_policy_ms:
```

### 6.7 External host boundary

SQLite `CLAIMED` is not host allocation. Before any side effect, the host must:

```text
validate permit, Run epoch, every claim generation, session, fence, and lease
atomically acquire the complete local claim set using claim_set_id as idempotency key
return one all-or-none ACQUIRED receipt
return a matching HostWorkAcceptanceFact proposal
wait for Rust's committed acceptance acknowledgement
```

An `ACQUIRED` allocation receipt alone proves only host-local slot preparation. It never establishes canonical host
acceptance, actual Run start, Calendar start-authority compliance, or `RUN_ATTEMPTS` consumption. When Capacity enforcement applies,
an `ACCEPTED HostWorkAcceptanceFact` must reference the exact complete `ACQUIRED` receipt. Rust accepts both in one
SQLite transaction; only that transaction may move the claim set to `ALLOCATED`, advance the Run to `LEASED`, and
establish Calendar-compliant one-time start authority. The `RUN_ATTEMPTS` reservation remains `RESERVED` until
positive execution evidence commits.

The host performs no effectful work until it receives the committed acceptance acknowledgement. A lost
acknowledgement is queried by stable idempotency key. If execution may have begun before the Rust transaction can be
proved committed, the Run and complete claim set become `UNKNOWN`; no retry is inferred from a missing acknowledgement.

The acceptance transaction is the lease-authority handoff:

```text
CLAIMED before canonical acceptance
  -> claim lease controls dispatch/start preparation

HostWorkAccepted transaction
  -> consume the permit's one-time acceptance authority
  -> establish one bounded one-time start authority
  -> close claim-lease dispatch authority
  -> create allocation_lease_generation = 1 from Rust transaction time
  -> bind the allocation lease to the Run and complete claim set

ALLOCATED / RELEASING after acceptance
  -> allocation lease alone controls continued host-local occupancy and liveness
```

The Run stores the current allocation authority binding. Allocation renewal updates that binding and claim-set rows in
one Rust transaction; it does not reissue the consumed start permit or grant a new effect scope. The host adapter must
fail closed against new side effects and initiate its registered stop behavior when its signed allocation lease
expires. Rust treats an unconfirmed stop or release as `UNKNOWN` and never makes the units reusable from time alone.

The host does not compare its untrusted wall clock with Rust UTC. Its registered adapter uses a local monotonic
watchdog:

```text
initial ACQUIRED proposal
  -> arm provisional watchdog before sending, for no more than allocation_lease_ms
  -> Rust acceptance ack may activate or shorten that watchdog, never restart a full TTL

renewal proposal
  -> arm a candidate watchdog from the local monotonic send instant
  -> keep the old watchdog authoritative until Rust commits and acknowledges RENEWED
  -> on ack, switch to the candidate deadline; never compute a fresh TTL from ack receipt time

canonical Rust expiry or host monotonic watchdog, whichever is reached first
  -> stop new side effects and enter registered stop / release reconciliation
```

Because the host starts counting no later than Rust receipt acceptance, its deadline is never later than Rust's
checked UTC expiry for the same TTL. Monotonic-clock reset, process/session replacement, missing ack, or expired
provisional watchdog fails closed and requires a new fenced session; it cannot extend a lease. The signed protocol
binds watchdog contract version, generation, and TTL without making host wall time canonical.

```yaml
run_allocation_authority_binding:
  claim_set_id:
  allocation_id:
  allocation_generation:
  allocation_lease_generation:
  allocation_lease_policy_revision:
  allocation_lease_expires_at_utc_ms:
  host_session_id:
  host_fence_epoch:
  accepted_allocation_receipt_id:
```

```text
host explicitly rejects and proves no execution
  -> Run may become REJECTED
  -> complete claim set RELEASED only from a matching all-or-none REJECTED_NOT_ACQUIRED receipt proving never acquired,
     or a matching RELEASED receipt proving a prepared allocation was released
  -> otherwise claim set remains RELEASING or UNKNOWN and consumes full units

execution / effect occurrence cannot be determined
  -> Run and complete claim set UNKNOWN
  -> full units remain occupied
  -> no automatic retry

execution absence is proven but allocation release cannot be determined
  -> Run remains REJECTED
  -> complete claim set becomes RELEASING or UNKNOWN and consumes full units
  -> no capacity reuse until authoritative release
```

Offer expiry does not release an `ALLOCATED` claim. Claim lease, allocation lease, Run lease, permit expiry, Calendar,
Deadline, and BudgetReservation are distinct contracts.

### 6.8 Control / recovery boundary

v0.1 does not create CapacityClaims for `CONTROL_RECOVERY` and has no `control_reserved_units`. This is deliberate:
control work would otherwise require a second owner lifecycle, acceptance/start Fact family, permit, Budget, UNKNOWN,
and recovery contract that is not yet frozen.

Fact / Receipt acceptance, SQLite integrity repair, local fence persistence, UNKNOWN reconciliation, stop-intent
Outbox creation/dispatch, and pure ledger finalizers remain Capacity-independent. Registered host safety stop/status
channels also remain governed by their existing Control Intent and host contracts rather than pretending to consume a
normal executor slot. Therefore ordinary Capacity damage cannot deadlock the minimum local control path.

Any future recovery action that genuinely needs a contested executor slot is deferred to a separate
`Control Capacity Admission v0.2+` contract with its own policy, owner identity, permit, host acceptance/start,
idempotency, Budget, UNKNOWN, release, and recovery tests. Caller-declared control claims are rejected in v0.1.

### 6.9 Lease, fence, time, and revision

```text
claim renewal
  -> same owner, pool, units, host, and effect scope only
  -> allowed only when the complete claim set and Outbox prove no payload was ever dispatched
  -> recheck Run, permit, offer, session, and fence
  -> increment claim_lease_generation and compute expiry from Rust acceptance time
  -> for an ordinary Run, atomically reissue the permit binding the new lease generation / expiry
  -> require the same current pool revision and ENFORCING profile allowlist entry
  -> cannot enlarge units or pass the policy maximum

allocation renewal
  -> authenticated RENEWED receipt from current host session and matching allocation / claim generations only
  -> allowed only after STARTED for RUNNING / WAITING active work; forbidden while Run is LEASED
  -> increment allocation_lease_generation and compute expiry from Rust receipt-acceptance time
  -> require trusted now strictly before current allocation expiry and proof the old host watchdog has not fired
  -> use the historical allocation-lease policy revision bound at HostWorkAccepted
  -> cannot change local handle digest, units, owner, or effect scope

host fence changes
  -> old offer, unaccepted claim, permit, and allocation receipt lose current authority
  -> if old host stop is unknown, claim becomes UNKNOWN

pool capacity decreases
  -> may produce OVERALLOCATED
  -> does not cancel active Run

pool drain / disable
  -> blocks new ordinary admission
  -> is not an active-stop command
```

Rust computes `claim_lease_expires_at_utc_ms` from transaction time and the claim-bound pool revision that is current
and allowlisted before acceptance. It computes initial and renewed `allocation_lease_expires_at_utc_ms` from
transaction time and the Run-bound historical `allocation_lease_policy_revision`. Host timestamps never extend a
lease. A claim renewal must commit before its current expiry. Once send may have occurred, Rust cannot change claim generation or reissue start
authority; it must await acceptance, a complete rejection/release proof, or UNKNOWN reconciliation. A late or
contradictory renewal enters reconciliation and cannot revive dispatch authority.

Allocation and watchdog generations advance by exact CAS `current + 1`. A RENEWED receipt arriving at/after canonical
expiry, after the old monotonic watchdog fired, with uncertain Rust time, or from a different policy revision cannot
renew or restore effect authority; it enters explicit reconciliation and normally leaves the allocation `UNKNOWN`
until a new fenced session proves state. Later pool revisions never silently lengthen or shorten an accepted Run's
lease. v0.1 has no compatible-policy substitution; Jenn must stop/reconcile or wait for release before new policy
applies.

An expired unallocated claim follows `ExpireUndispatchedClaimSet` only when non-dispatch is proven; otherwise it is
`UNKNOWN`. An expired `ALLOCATED` or `RELEASING` lease is never silently `RELEASED`: absent an authoritative current
release/reconciliation Fact, the complete set becomes `UNKNOWN` and keeps consuming units.

A new pool revision governs new claims. A not-yet-accepted claim bound to a superseded or disabled pool loses start
authority and is finalized as definitely unused or `UNKNOWN` according to dispatch evidence. An already accepted Run
keeps its exact historical pool/domain allocation until authoritative release; revision, drain, or lower ceiling does
not preempt it, and those units remain in domain accounting.

When time authority is `UNCERTAIN`, Rust creates no new claim and performs no automatic UTC-expiry release. Existing
claims continue to consume units pending trusted time or host reconciliation.

### 6.10 Recovery

Before ordinary selection and permit issuance, startup must:

```text
1. validate pool, request, offer, claim, allocation receipt, Event, and current pointers
2. raise resident / local host fence; require fresh remote VCPChat / VCPMobile sessions
3. rebuild O and UNKNOWN counters for every pool/accounting key
4. detect duplicate claims, invalid units, ceiling violations, generation mismatch, and partial ALL_OF sets
5. expire only CLAIMED work proven never to have left the ledger
6. change possibly dispatched work without authoritative receipt to UNKNOWN
7. restore ALLOCATED only from a matching current host receipt
8. keep offer expiry separate from allocation release
9. block new claims under OVERALLOCATED or accounting mismatch
10. complete the recovery read barrier and accept fresh offers before ordinary admission
```

Recovery is idempotent and cannot duplicate claim, generation, Run, Event, permit, Outbox, or allocation. Late receipts
remain history but an old session or generation cannot advance current work.

For an undispatched complete claim set, Rust uses one `ExpireUndispatchedClaimSet` transaction:

```text
prove the complete claim set never left the ledger
mark every member EXPIRED
revoke and fence the permit
supersede the Outbox intent
set the Run REJECTED
release every definitely-unused BudgetReservation
append one Event and re-evaluate the Task
```

If the proof is incomplete, the Run, complete claim set, and affected Budget consumption become `UNKNOWN`; units and
reservations remain charged. After known host completion, an atomic release finalizer binds the release receipt, moves
the complete set through `RELEASING` to `RELEASED`, settles/releases only resource-accounting records, and appends the
Event. `RELEASED` proves resource release only; it cannot advance Run or Validation. A transaction may also consume an
independent authoritative execution/Validation receipt, but that receipt owns the business transition. Without a valid
release receipt, claims remain `RELEASING` or `UNKNOWN` and consume units.

Capacity enforcement activation is owned by the current `SchedulingEnforcementProfileRevision` for the exact work
request scope. Only its explicit pool allowlist is eligible. A listed pool becomes admission-ready only after its own
accounting recovery and a fresh offer. Offline, legacy, or `UNKNOWN` pools remain quarantined and cannot be selected,
but do not block unrelated recovered profiles/pools. Legacy active or `UNKNOWN` work blocks every pool whose units it
may still occupy; Rust creates no synthetic allocation.

### 6.11 Authority and invariants

```text
Jenn
  -> may enable / disable pools, set ceiling, and lock policy

Nobao
  -> may manage NOBAO_MANAGED pools and Task requests
  -> cannot forge offer / allocation / capability or bypass Budget / P3

execution host
  -> reports only its own session offer and allocation / release facts
  -> cannot create ledger claim or write Task state

UI / Domain Agent / Worker / solver
  -> proposal only; cannot create a CapacityClaim or alter pool accounting

Rust core
  -> sole pool-currentness, offer-acceptance, claim, count, OVERALLOCATED,
     lease / fence, permit-binding, and recovery ledger authority
```

```text
Capacity is not Budget or capability
Offer is not allocation
Claim is not host acceptance
Selection consumes no Capacity
ordinary claims and Run are locally atomic
external allocation is outside SQLite atomicity
UNKNOWN consumes full units
v0.1 CapacityClaim owner is always a Run
minimum control / recovery path is Capacity-independent
Capacity change does not preempt active Run
```

## 7. Eligibility and Effective Ordering v0.1

### 7.1 Decision

Eligibility and ordering are two separate Rust reductions:

```text
hard eligibility first
then deterministic weighted service ordering among eligible work
then immutable selection evidence
then a separate synchronous admission transaction
```

No score, Priority, focus directive, expedite, aging, deadline forecast, Goal route, fairness debt, or solver output can
turn ineligible work into eligible work.

Only `normal_selection=ENFORCING` may create a canonical admission-usable
`TaskPrioritySelectionSnapshot`. `SHADOW` runs the reducer into a separately labelled rebuildable comparison
projection and cannot be consumed by admission or service accounting. `SUSPENDED_FAIL_CLOSED` creates no new normal
selection. Existing control and recovery routes remain governed by their own contracts.

### 7.2 Work subject and lanes

```yaml
work_subject_kind:
  - EXECUTION_RUN
  - EFFECTFUL_VALIDATION_RUN

lane:
  - NORMAL
  - CONTROL_RECOVERY
```

`CONTROL_RECOVERY` does not use ordinary Priority or fairness. It is limited to the already accepted Fact / Receipt,
UNKNOWN reconciliation, stop / fence, Control Intent finalizer, lease / crash recovery, and ledger-integrity paths.
Ordinary work cannot declare itself control work. This scheduling lane creates no v0.1 CapacityClaim; Section 6.8
keeps the minimum control path Capacity-independent.

Until a separate Validation Execution Admission contract has both been accepted and activated by an explicit cutover
Event, every `EFFECTFUL_VALIDATION_RUN` must bind a Run created by `create_run`. Pure ledger Validation,
non-effectful deterministic review, and HUMAN_ACCEPTANCE do not use ordinary executor scheduling.

### 7.3 SchedulingEligibilityAssessment

```yaml
SchedulingEligibilityAssessment:
  schema_version: scheduling-eligibility.v0.1
  result_semantics: OPERATIONAL_REDUCER_VIEW
  assessment_id:
  work_request_id:
  work_request_revision:
  enforcement_scope_key:
  enforcement_scope_assignment_revision:
  enforcement_scope_assignment_fingerprint:
  work_subject_kind: EXECUTION_RUN | EFFECTFUL_VALIDATION_RUN
  task_id:
  task_aggregate_version:
  lifecycle_generation:
  execution_epoch_observed:
  validation_requirement_ref: optional
  reducer_currentness: CURRENT | REBUILD_REQUIRED | REBUILDING | INDETERMINATE
  outcome: ELIGIBLE | INELIGIBLE | INDETERMINATE
  preselection_status: CANDIDATE | SUPPRESSED_BY_ACTIVE_BACKOFF
  reason_codes: []
  eligibility_episode_id: optional
  eligible_since_event_sequence: optional
  eligible_since_utc_ms: optional
  observed_refs:
    task_state:
    enforcement_profile_revision:
    enforcement_scope_assignment_revision:
    enforcement_scope_assignment_fingerprint:
    priority_revision:
    dependency_revision:
    dependency_assessment:
      assessment_mode:
      freshness:
      outcome:
      input_fingerprint:
      based_on_event_sequence:
    deadline_revisions: []
    budget_revisions: []
    calendar_revisions: []
    calendar_start_authority_fence:
      bindings: []
      aggregate_fingerprint:
    capacity_pool_revisions: []
    host_offer_refs:
      - offer_id:
        offer_generation:
        host_session_id:
        host_fence_epoch:
        expires_at_utc_ms:
    authorization_policy_revision:
    permit_prerequisite_fingerprint:
    host_fence_epoch:
    scheduling_backoff_ref: optional
  input_fingerprint:
  reduced_through_event_sequence:
  reducer_contract_version: scheduling-eligibility.v0.1
  policy_revision_refs: []
  reduced_at_utc_ms:
  next_time_transition_utc_ms: optional
```

This assessment is a derived projection. A transition into or out of continuous eligibility appends a compact
`TaskSchedulingEligibilityChanged` Event so the eligibility episode and aging basis can be rebuilt deterministically.
The Event does not change Task lifecycle state.

An active `SchedulingBackoffProjection` does not claim that the Task is semantically ineligible. It sets
`preselection_status=SUPPRESSED_BY_ACTIVE_BACKOFF`; only `CURRENT + ELIGIBLE + CANDIDATE` work enters the candidate
set. The exact backoff revision, expiry, and input fingerprint are bound into selection evidence. Uncertain time makes
the suppression indeterminate and prevents autonomous normal selection for that request.

### 7.4 Hard eligibility reason registry

v0.1 accepts only the following scheduling reason codes:

```text
# CONFIRMED_DENY, canonical order
TASK_TERMINAL
TASK_PAUSED
TASK_BLOCKED
WAIT_CONDITION_NOT_SATISFIED
NONTERMINAL_EXECUTION_RUN_EXISTS
NONTERMINAL_VALIDATION_EXISTS
CONTROL_INTENT_ACTIVE
UNKNOWN_OR_UNRECONCILED_EFFECT
DEPENDENCY_UNSATISFIED_CONFIRMED
DEADLINE_NEW_START_AUTHORITY_PROHIBITED
HARD_BUDGET_RESERVATION_UNAVAILABLE
ADMISSION_CALENDAR_CLOSED
CAPACITY_CURRENTLY_UNAVAILABLE
AUTHORIZATION_PREREQUISITE_MISSING
POLICY_DENIED
HOST_CAPABILITY_MISSING_CONFIRMED
TASK_COMMITMENT_NOT_FORMABLE
ENFORCEMENT_PROFILE_SUSPENDED
WORK_REQUEST_STALE

# INDETERMINATE_EVIDENCE, canonical order
WAIT_CONDITION_INDETERMINATE
DEPENDENCY_ASSESSMENT_INDETERMINATE
DEADLINE_TIME_AUTHORITY_UNCERTAIN
BUDGET_ACCOUNTING_INDETERMINATE
ADMISSION_CALENDAR_INDETERMINATE
CAPACITY_FACT_INDETERMINATE
AUTHORIZATION_ASSESSMENT_INDETERMINATE
POLICY_ASSESSMENT_INDETERMINATE
HOST_CAPABILITY_STALE_OR_INDETERMINATE
TASK_COMMITMENT_ASSESSMENT_INDETERMINATE
ENFORCEMENT_PROFILE_INDETERMINATE
SCOPE_ASSIGNMENT_INDETERMINATE
SELECTION_POLICY_UNAVAILABLE
```

The registry order above is the canonical reason order; comments are categories, not emitted codes. Rust deduplicates
and emits all applicable reasons in this order. Outcome reduction is fixed:

```text
one or more independently sufficient CONFIRMED_DENY reasons
  -> INELIGIBLE, even if a separate gate is indeterminate

no CONFIRMED_DENY and one or more INDETERMINATE_EVIDENCE reasons
  -> INDETERMINATE

no reasons
  -> ELIGIBLE
```

A stale observation cannot be promoted to a confirmed deny. The assessment records enough source refs to distinguish
“known missing/closed/exhausted” from “could not establish current truth.” Unknown codes, duplicate codes, a code in
the wrong category, or an outcome inconsistent with this reduction are rejected.

Rules:

```text
Task terminal, PAUSED, unresolved BLOCKED, active Control Intent, UNKNOWN, or a nonterminal Run is ineligible
WAITING is eligible only after its canonical wake condition is satisfied in the same consistent read
ACTIVE without a Run is eligible only when its activity contract permits dispatching
VERIFYING + EXECUTION_RUN is eligible only with an authorized `REJECT_FOR_NEW_EXECUTION` work request and every rerun guard
VERIFYING + EFFECTFUL_VALIDATION_RUN is eligible only with `PRESERVE_FOR_EFFECTFUL_VALIDATION` bound to the exact current candidate and Requirement
Dependency must be CURRENT + SATISFIED with the complete pinned closure CONFIRMED
all applicable Hard Deadlines and HARD_CAP Budgets must allow admission
admission Calendar and Capacity may deny only when their exact enforcement-profile mode is ENFORCING
SHADOW Calendar / Capacity results are diagnostic and cannot make outcome INELIGIBLE or INDETERMINATE
SUSPENDED_FAIL_CLOSED suppresses new normal work only for its exact scope
P3 and permit prerequisites must be satisfiable; selection does not require a TaskPermit that is created only later
Priority REVIEW_REQUIRED uses its accepted NORMAL fallback and does not make the Task ineligible
Soft Deadline miss, SOFT_TARGET Budget excess, missing Duration, or missing advisory forecast is not an eligibility deny
```

An eligibility reason is scheduling evidence only. A single capacity race, closed calendar window, or rejected
selection does not directly set Task `WAITING / BLOCKED / FAILED`. A Task enters `WAITING` only through its existing
state reducer with an explicit wake condition, owner, timeout policy, and review boundary.

### 7.5 SchedulingPolicyRevision

```yaml
SchedulingPolicyRevision:
  schema_version: scheduling-policy.v0.1
  policy_id: agents-os-normal-scheduling
  revision:
  service_epoch:
  virtual_service_arithmetic: U128_BE_V1
  band_stride_scale: 48
  rolling_horizon_ms: 604800000
  service_band_weights:
    FOCUS: 16
    URGENT: 12
    HIGH: 8
    NORMAL: 4
    LOW: 2
    BACKGROUND: 1
  fairness_account_weight: 1
  fairness_account_stride: 1
  new_or_reactivated_placement: MAX_STORED_SYSTEM_AND_INHERITED_LINEAGE_FLOOR
  service_charge_boundary: SUCCESSFUL_LOCAL_ADMISSION
  aging_quantum_ms: 1800000
  max_aging_promotions: 2
  max_consecutive_focus_or_urgent: 6
  max_consecutive_non_background: 16
  focus_max_ttl_ms: 86400000
  expedite_max_ttl_ms: 14400000
  expedite_max_successful_admissions: 1
  selection_backoff_base_ms: 1000
  selection_backoff_max_ms: 60000
  selection_handoff_ttl_ms: 5000
  local_handoff_claim_lease_ms: 1000
  host_start_grace_ms: 10000
  max_open_normal_selections_global: 1 # v0.1 constant
  parameter_value_classes:
    JENN_POLICY:
      - rolling_horizon_ms
      - service_band_weights
      - aging_quantum_ms
      - max_aging_promotions
      - max_consecutive_focus_or_urgent
      - max_consecutive_non_background
      - focus_max_ttl_ms
      - expedite_max_ttl_ms
      - expedite_max_successful_admissions
      - max_open_normal_selections_global
    PROVISIONAL_BENCHMARK_REQUIRED:
      - selection_backoff_base_ms
      - selection_backoff_max_ms
      - selection_handoff_ttl_ms
      - local_handoff_claim_lease_ms
      - host_start_grace_ms
  benchmark_evidence_refs: []
  policy_fingerprint:
  accepted_by: Jenn
  accepted_event_id:
```

Policy values are scheduling mechanics, not numeric Task Priority. A policy revision does not automatically start a
new service epoch. Only a Jenn-authorized `FairnessServiceEpochStarted` Event may change the epoch, and it is required
only when weight, stride, arithmetic, or fairness-identity semantics change. Backoff, TTL, or other unrelated policy
revision must preserve the current epoch and cannot reset service history. No revision rewrites historical selection,
Task Priority, Goal plan, or active Run.

`FairnessServiceEpochStarted` is an exact payload in the existing immutable Event log, not a new formal object:

```yaml
FairnessServiceEpochStarted:
  schema_version: fairness-service-epoch-started.v0.1
  event_id:
  service_epoch:
  service_epoch_generation:
  previous_service_epoch: required_except_INITIAL_BOOTSTRAP
  previous_service_epoch_generation: required_except_INITIAL_BOOTSTRAP
  scheduling_policy_revision:
  scheduling_policy_fingerprint:
  transition_reason: INITIAL_BOOTSTRAP | SERVICE_WEIGHT_OR_STRIDE_CHANGE | ARITHMETIC_CHANGE | FAIRNESS_IDENTITY_SEMANTICS_CHANGE | JENN_AUTHORIZED_REBASE
  arithmetic: U128_BE_V1
  initialization_mode: RESET_ALL_WITHIN_NEW_EPOCH_TO_ZERO
  initial_band_system_pass: 0
  initial_account_system_pass: 0
  initial_entity_pass: 0
  initial_consecutive_focus_or_urgent: 0
  initial_consecutive_non_background: 0
  current_eligible_lineage_set_fingerprint:
  assignment_rederivation_fingerprint:
  lineage_floor_initialization_fingerprint:
  lineage_head_rederivation_fingerprint:
  backlog_episode_rederivation_fingerprint:
  authorized_by: Jenn
  authorization_ref:
  event_sequence:
  committed_at_utc_ms:
  semantic_fingerprint:
```

`service_epoch_generation` is a checked monotonic integer and `service_epoch` is unique. The first epoch requires
`INITIAL_BOOTSTRAP` and forbids both previous-epoch fields. Every later epoch requires both previous fields to name the
single current epoch. An unrelated policy change cannot emit this Event. `JENN_AUTHORIZED_REBASE` is an explicit Jenn
rebase, never a reducer-selected repair or an Agent shortcut.

The Event, zero-valued Current State pass rows and counters, one assignment per current eligible work request,
zero-valued lineage floors, one canonical head/band per eligible lineage, and the new epoch's backlog-episode
rederivation commit in one Rust transaction. For every band, account, and lineage in the new epoch, stored, system,
and lineage-floor pass begins at zero; no old-epoch pass participates in a new-epoch comparison. Because the reset
applies to the entire new epoch at one Event boundary, no newly joined Goal or changed shared-account hash gets a
private zero-based catch-up advantage. Every nonempty semantic band/account backlog in the new epoch starts its new
episode at this Event's sequence; empty accounts have no open episode.

Normal selection remains closed until `SchedulingServiceProjection` is `CURRENT` through this Event and proves the
complete assignment, lineage-floor, lineage-head, and backlog rederivations match the Event fingerprints. An incomplete, duplicate,
out-of-order, unsupported, or overflowed epoch transition makes normal selection
`SELECTION_POLICY_UNAVAILABLE`; control and recovery remain available. Historical selections, charges, assignments,
and episodes retain their old epoch and can never be replayed as current new-epoch authority.

All virtual passes are checked nonnegative `u128`. SQLite stores one fixed 16-byte unsigned big-endian encoding;
Event / JSON uses canonical decimal ASCII. Each positive band weight must divide `band_stride_scale`, and
`band_stride = band_stride_scale / weight`. Float, locale conversion, signed SQLite coercion, overflow, unsupported
encoding, or a missing explicit service epoch makes normal selection `SELECTION_POLICY_UNAVAILABLE`; control and
recovery remain available.

`PROVISIONAL_BENCHMARK_REQUIRED` values are schema-valid candidate defaults, not activation-ready facts. The affected
subsystem cannot enter `ENFORCING` until a current policy revision binds benchmark evidence for its measured runtime /
host environment and Jenn accepts that revision. `JENN_POLICY` values remain Jenn product choices; benchmark may test
supportability but cannot silently choose a different value.

If the stored policy is unsupported, Rust uses the existing safe Priority fallback, refuses autonomous normal
selection, and keeps control / recovery paths available. It does not improvise comparator rules.

### 7.6 Focus, expedite, urgency, aging, and service band

#### Jenn focus

`JennFocusDirective` is an Event-backed operational record, not a core object. Only Jenn may create, revise, renew, or
revoke it. v0.1 supports preference only, never hard exclusion.

```yaml
JennFocusDirective:
  directive_id:
  directive_revision:
  supersedes_revision_id: optional
  scope_kind: GOAL | TASK_SET
  scope_ids: []
  mode: PREFER
  status: ACTIVE | REVOKED
  created_at_utc_ms:
  expires_at_utc_ms:
  reason:
  created_event_id:
  revoked_event_id: optional
  semantic_fingerprint:
```

`expires_at_utc_ms` is required and may not exceed the policy maximum. Expiry removes the scheduling boost but does
not modify Task Priority or state.

Renewal, scope change, expiry change, and revocation each create a new immutable revision; revocation is a current
`REVOKED` revision rather than mutation of the old row. Rust maintains one current revision per directive ID. A boost
requires the exact current ACTIVE revision, trusted `now < expires_at_utc_ms`, and matching semantic fingerprint.

At every head, selection, and admission boundary, Rust derives the complete applicable Focus set for the exact Task
lifecycle. References are sorted by `(directive_id canonical UTF-8 bytes, directive_revision)` and their complete-set
fingerprint is an ordering input. Effective Focus is the logical OR of every current applicable revision; no arbitrary
single directive becomes the authority. Adding, revising, revoking, expiring, or removing any applicable revision
changes the set fingerprint even when another overlapping Focus keeps the effective result true. Every known expiry is
retained as a recomputation boundary; a reducer may prove that the effective OR remains true after one member expires,
but it may not omit that member or extend currentness from a chosen later expiry.

#### Temporary expedite

Jenn or Nobao may create a `TemporaryExpediteDirective` for one Task. Nobao may do so only inside an already accepted
Goal / Task scope. It expires at the earlier of its required timestamp or one successful admission.

```yaml
TemporaryExpediteDirective:
  directive_id:
  task_id:
  lifecycle_generation:
  work_request_id:
  work_request_revision:
  created_by: Jenn | Nobao
  reason:
  created_at_utc_ms:
  expires_at_utc_ms:
  max_successful_admissions: 1
  created_event_id:
  revoked_event_id: optional
  semantic_fingerprint:
```

It grants no permission, does not bypass a gate, does not preempt active work, and cannot be renewed by a Worker or
executor.

Rust likewise derives the complete current applicable Expedite set for the exact
`(task_id, lifecycle_generation, work_request_id, work_request_revision)`, sorted by
`(directive_id canonical UTF-8 bytes, created_event_id canonical UTF-8 bytes)`. Effective expedite is the logical OR of
that set. A successful local admission atomically consumes every still-current applicable directive that was bound by
the rechecked selection; one directive cannot remain to grant a second boost merely because another overlapping
directive was chosen as a display ref. A directive created, revoked, expired, consumed, or replaced after selection
changes the complete-set fingerprint and requires a fresh head/selection reduction. Duplicate command replay resolves
to the same directive identity and cannot manufacture another admission allowance.

When Rust time authority is uncertain, Focus and expedite currentness become INDETERMINATE and grant no new boost;
Rust does not invent an expiry instant. Their historical Events remain unchanged until trusted time returns.

#### Deadline urgency

Deadline urgency is derived only from a CURRENT compatible Task `TASK_DONE` SchedulePlan forecast, an exact-semantics
TimeCriticalPath diagnostic, or an actual current Soft Deadline miss:

```text
OVERDUE_SOFT
NEGATIVE_MARGIN
ZERO_MARGIN
TIGHT_POSITIVE_MARGIN
POSITIVE_MARGIN
UNKNOWN
NO_COMPATIBLE_COMPLETION_TARGET
```

The fixed lower-is-more-urgent ordinal is:

```text
0 OVERDUE_SOFT
1 NEGATIVE_MARGIN
2 ZERO_MARGIN
3 TIGHT_POSITIVE_MARGIN
4 POSITIVE_MARGIN
5 UNKNOWN
6 NO_COMPATIBLE_COMPLETION_TARGET
```

```yaml
DeadlineUrgencyAssessment:
  schema_version: deadline-urgency-assessment.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  assessment_id:
  work_request_id:
  work_request_revision:
  deadline_id:
  deadline_revision:
  deadline_scope: TASK | GOAL
  deadline_target_utc_ms:
  basis_kind: FORECAST | ACTUAL_SOFT_MISS
  required_completion_semantics: TASK_DONE | GOAL_CLOSED_ACHIEVED
  forecast_completion_semantics: optional # FORECAST only: TASK_DONE | GOAL_CLOSED_ACHIEVED | ROUTE_SCENARIO_WORK_COMPLETE
  compatibility: optional # FORECAST only: EXACT | LOWER_BOUND_ONLY | INCOMPATIBLE | INDETERMINATE
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | UNAVAILABLE | INDETERMINATE
  reason_codes: []
  route_scenario_fingerprint: optional # FORECAST only
  most_likely_forecast_ref: optional # FORECAST only
  pessimistic_forecast_ref: optional # FORECAST only
  most_likely_finish_utc_ms: optional # FORECAST only
  pessimistic_finish_utc_ms: optional # FORECAST only
  most_likely_margin_ms: optional # FORECAST only
  pessimistic_margin_ms: optional # FORECAST only
  actual_soft_miss_basis: # required only for ACTUAL_SOFT_MISS
    soft_completion_target_missed_event_id:
    soft_completion_target_missed_event_sequence:
    current_deadline_pointer_revision:
    scope_current_state_ref:
    scope_current_state_fingerprint:
    scope_completion_status: CURRENTLY_INCOMPLETE
  urgency: OVERDUE_SOFT | NEGATIVE_MARGIN | ZERO_MARGIN | TIGHT_POSITIVE_MARGIN | POSITIVE_MARGIN | UNKNOWN | NO_COMPATIBLE_COMPLETION_TARGET
  forecast_as_of_utc_ms: optional # required for FORECAST; absent for ACTUAL_SOFT_MISS
  valid_until_utc_ms: optional # required for FORECAST; absent for ACTUAL_SOFT_MISS
  time_currentness_policy_revision: optional # required for FORECAST; absent for ACTUAL_SOFT_MISS
  basis:
    source_forecast_refs: optional # required for FORECAST; absent for ACTUAL_SOFT_MISS
    deadline_event_sequence:
    based_on_event_sequence:
    policy_revision_refs: []
    input_revision_refs: []
    input_fingerprint:
  computed_at_utc_ms:
```

For `FORECAST`, `DeadlineUrgencyAssessment.basis.input_fingerprint` binds the exact compatible Deadline revision,
current source-forecast semantic fingerprints, route/completion semantics, currentness policy, and relevant source
Event refs. For `ACTUAL_SOFT_MISS`, it binds the immutable miss Event and current Deadline/scope pointers. In both
branches, assessment IDs, source row IDs, aggregate CAS versions, read/reducer watermarks, and materialization
timestamps are excluded under Section 3.3.

Forecast urgency compares Calendar-aware completion instants, never wall-clock margin against active Duration:

```text
actual current Soft Deadline miss                       -> OVERDUE_SOFT
MOST_LIKELY finish > compatible target                 -> NEGATIVE_MARGIN
MOST_LIKELY finish == compatible target                -> ZERO_MARGIN
MOST_LIKELY finish < target and PESSIMISTIC >= target  -> TIGHT_POSITIVE_MARGIN
PESSIMISTIC finish < compatible target                 -> POSITIVE_MARGIN
```

`DeadlineUrgencyAssessment` is a strict tagged union:

```text
basis_kind FORECAST
  -> actual_soft_miss_basis is absent
  -> forecast_completion_semantics and compatibility are required
  -> exact source forecast refs and the applicable finish / margin fields are required
  -> forecast_as_of_utc_ms, valid_until_utc_ms, and time_currentness_policy_revision are required

basis_kind ACTUAL_SOFT_MISS
  -> only an exact canonical SoftCompletionTargetMissed Event for the same current Deadline revision is legal
  -> actual_soft_miss_basis is required
  -> urgency = OVERDUE_SOFT, coverage = COMPLETE, and assessment = AVAILABLE
  -> forecast_completion_semantics, compatibility, route / forecast refs, finish / margin fields,
     forecast_as_of_utc_ms, valid_until_utc_ms, and time_currentness_policy_revision are absent
  -> the result is Event-backed and non-time-bearing
```

For `ACTUAL_SOFT_MISS`, Rust must verify that the missed Event names the exact current Deadline revision, the bound
Task / Goal current-state reference and fingerprint still match, and the owning scope remains currently incomplete.
Deadline revision or retirement, Task / Goal lifecycle or completion change, work-request supersession, or a changed
scope-currentness fingerprint immediately makes the assessment `STALE`. The historical miss Event remains immutable,
but it cannot keep a completed, superseded, or no-longer-applicable work request urgent. Wall-clock passage alone does
not expire or refresh this branch, and no max-age timer can replace its Event-backed currentness checks.

A Task Deadline uses a Task-local `TASK_DONE` forecast, including for standalone Tasks and Tasks outside a current
Goal finish-driving subgraph. A Goal Deadline requires a `GOAL_CLOSED_ACHIEVED` forecast. v0.1 does not model Goal
closure duration, so `ROUTE_SCENARIO_WORK_COMPLETE` is only `LOWER_BOUND_ONLY` and grants no Goal Deadline urgency;
pre-miss Goal urgency remains `UNKNOWN`. Actual Goal Soft Deadline miss remains `OVERDUE_SOFT` under the accepted
Deadline contract.

Only `CURRENT + COMPLETE + compatibility=EXACT` `FORECAST` evidence may produce a pre-miss urgency rank. Its exclusive
`valid_until_utc_ms` is the checked minimum of every source forecast's own validity, the still-future Deadline
transition, and `forecast_as_of + deadline_urgency_max_age_ms`. A source becoming stale immediately stales the urgency;
recomputing a later max-age cannot extend an expired source. At the Deadline boundary the old forecast branch becomes
stale. A later `OVERDUE_SOFT` assessment must be rebuilt as `ACTUAL_SOFT_MISS` from the canonical current
`SoftCompletionTargetMissed` Event; the already-crossed boundary is evidence, not a new `valid_until` candidate.
`FORECAST` is illegal when `forecast_as_of_utc_ms >= deadline_target_utc_ms`. If the boundary has been crossed but the
current miss Event cannot yet be established because Deadline reduction, scope currentness, or time authority is
unavailable, the result is `UNAVAILABLE` or `INDETERMINATE` and receives no urgency promotion; Rust does not preserve
the expired forecast rank.

`UNKNOWN` and `NO_COMPATIBLE_COMPLETION_TARGET` receive no urgency promotion. Forecast lateness remains distinct from an actual
Deadline Event and does not create Goal Health reason codes by itself. A route-level margin affects a Task only when
that Task is in the CURRENT finish-driving subgraph for every currently viable route scenario affected by the same
Deadline, or Jenn / Nobao has already recorded an explicit current planning-route choice. Scheduling cannot create that
route choice merely to obtain an urgency boost.

Scheduling never chooses one Deadline assessment from an unordered set. For the exact work request, Rust first derives
the complete applicable Deadline set from the Task's own current Deadline and every current Goal Deadline whose route
relevance satisfies the rule above. Assessment references are sorted by:

```text
deadline_scope ordinal: TASK=0, GOAL=1
deadline_id canonical UTF-8 bytes
deadline_revision
assessment_id canonical UTF-8 bytes
```

The complete set, every assessment input fingerprint/currentness/validity boundary, and an
`applicable_deadline_urgency_set_fingerprint` are shared inputs to service-band, lineage-head, selection-validity, and
admission recheck. The effective scheduling urgency is reduced exactly as follows:

```text
complete applicable set cannot be established
  -> UNKNOWN; no urgency promotion

one or more CURRENT current-scope ACTUAL_SOFT_MISS assessments
  -> OVERDUE_SOFT

otherwise any applicable assessment is missing, STALE, EVALUATING, UNAVAILABLE, INDETERMINATE, or not exact-semantics
  -> UNKNOWN; no urgency promotion

otherwise one or more CURRENT + COMPLETE + AVAILABLE exact assessments
  -> choose the lowest fixed urgency ordinal

complete set exists but none has a compatible completion target
  -> NO_COMPATIBLE_COMPLETION_TARGET
```

When several exact assessments have the winning ordinal, the diagnostic driver is the lowest tuple
`(urgency_ordinal, deadline_target_utc_ms, deadline_scope_ordinal, deadline_id bytes, deadline_revision, assessment_id
bytes)`. The driver is evidence only; the complete set remains the currentness authority. A non-driver assessment
change can therefore stale or recompute ordering, and a shared Task cannot obtain a different band from insertion order
or a conveniently selected Goal.

#### Aging

Aging uses continuous eligible time under a trusted Rust UTC clock. Each complete `aging_quantum_ms` promotes the
service band by one level, capped at `HIGH`; aging can never manufacture `URGENT` or `FOCUS`. When eligibility ends,
the episode closes. A later episode starts from zero. Time authority uncertainty freezes aging at its last trusted
value rather than guessing.

#### Service band derivation

```text
active Jenn focus                                  -> FOCUS
current temporary expedite                         -> URGENT
OVERDUE_SOFT / NEGATIVE / ZERO / TIGHT margin      -> URGENT
otherwise base Priority + bounded aging            -> HIGH | NORMAL | LOW | BACKGROUND
```

The first two rows use the complete-set OR reductions above; the Deadline row uses the complete applicable assessment
reduction, not one assessment pointer. Precedence is exactly Focus, then expedite, then effective Deadline urgency,
then base Priority plus aging. This derivation never writes `base_priority_class`.

### 7.7 Cross-Goal fairness and virtual service

Every eligible Task lifecycle belongs to one deterministic fairness lineage and exactly one current fairness account.
Each current eligible work request has its own assignment evidence, but all requests in the same lineage share one
service history, one account, one canonical head, and one effective service band at a decision boundary. Neither
caller, host, Agent, UI, nor work-request producer may choose any of those identities.

```text
fairness_lineage_id
  = sha256(canonical-CBOR(
      "fairness-lineage.v0.1",
      task_id,
      lifecycle_generation
    ))

one current Goal binding
  -> goal/<goal_id>

no Goal binding
  -> standalone/<task_id>

multiple current Goal bindings
  -> shared/<sha256(canonical_sorted_goal_ids)>
```

All execution and effectful Validation work requests for the same Task lifecycle share the lineage. One lineage is one
fairness share regardless of its sibling-request count; duplicate, revised, execution, and effectful Validation
requests cannot buy additional service shares or enter another band in parallel. v0.1 gives every account weight `1`.
A future Goal service-weight contract requires Jenn review.

`FairnessAccountAssignmentRevision` is an Event-backed infrastructure record, not a formal object:

```yaml
FairnessAccountAssignmentRevision:
  schema_version: fairness-account-assignment.v0.1
  assignment_id:
  assignment_revision:
  service_epoch:
  fairness_lineage_id:
  lineage_assignment_generation:
  work_request_id:
  work_request_revision:
  eligibility_episode_id:
  task_id:
  lifecycle_generation:
  work_subject_kind: EXECUTION_RUN | EFFECTFUL_VALIDATION_RUN
  validation_requirement_ref: optional
  account_kind: GOAL | STANDALONE | SHARED
  fairness_account_id:
  canonical_goal_ids: []
  goal_binding_fingerprint:
  assignment_transition_flags: []
  supersedes_assignment_id: optional
  predecessor_fairness_account_id: optional
  lineage_service_floor_before_by_band: {}
  source_account_effective_pass_by_band: {}
  target_account_system_pass_by_band: {}
  target_account_stored_pass_by_band: {}
  target_account_pass_after_by_band: {}
  lineage_service_floor_after_by_band: {}
  assignment_event_id:
  semantic_fingerprint:
```

For every current eligible work-request revision, Rust requires exactly one current assignment under the unique key
`(service_epoch, fairness_lineage_id, work_request_id, work_request_revision)`. It also permits at most one current
assignment for `(service_epoch, fairness_lineage_id, work_request_id)`, so a superseded request revision cannot remain
current beside its replacement. All current assignments in one lineage must have the same
`lineage_assignment_generation`, account kind, account ID, canonical Goal IDs, and Goal-binding fingerprint. The
complete current sibling-assignment set fingerprint lives in `SchedulingServiceProjection`, not inside immutable
per-request assignments; adding or removing a sibling therefore does not rewrite unaffected assignment history.
Missing, duplicate, or conflicting sibling assignments make the service projection `INDETERMINATE` and close normal
selection.

`assignment_transition_flags` is a nonempty, deduplicated list in this fixed order:

```text
0 FIRST_LINEAGE_ASSIGNMENT
1 ADD_SIBLING_REQUEST
2 WORK_REQUEST_REVISION
3 ELIGIBILITY_RESTART
4 ACCOUNT_REKEY
```

Rust derives every applicable flag from the exact before/after assignment, work-request, eligibility-episode, and Goal
binding facts. `FIRST_LINEAGE_ASSIGNMENT` is exclusive and legal only when no lineage floor or prior assignment exists
in the service epoch. The other flags may coexist: for example, a revised request may re-enter eligibility while the
Task moves to another Goal account in the same transaction. Missing, extra, duplicated, reordered, or caller-selected
flags make the assignment invalid; no implementation may choose one primary origin and discard the other lower bounds.

Eligibility restart or work-request revision closes only the affected assignment and creates an immutable superseding
revision. A Goal-membership change re-keys every current sibling assignment in one transaction and advances their
shared `lineage_assignment_generation`; a partially re-keyed lineage is illegal. An additional sibling request
inherits the current account and lineage floor and does not create a new share. Rust derives every account from
canonical Goal bindings.

All pass values below are checked `u128` values for the same service epoch and band. Define:

```text
target_account_effective_before
  = max(
      target_account_stored_pass if present else target_account_system_pass,
      target_account_system_pass
    )

source_account_effective_before
  = max(
      source_account_stored_pass if present else source_account_system_pass,
      source_account_system_pass
    )
```

The exact lineage-floor transitions are defined by lower-bound contribution, so compound transitions remain
deterministic:

```text
first lineage assignment in the service epoch:
  lineage_floor_after
    = target_account_effective_before

additional sibling assignment, with continuous eligibility and no account change:
  lineage_floor_after
    = existing lineage_floor

work-request revision, with continuous eligibility and no account change:
  lineage_floor_after
    = existing lineage_floor

eligibility restart:
  lineage_floor_after
    = max(
        existing lineage_floor,
        target_account_effective_before
      )

account re-key, merge, or split:
  lineage_floor_after
    = max(
        existing lineage_floor,
        source_account_effective_before,
        target_account_effective_before
      )

compound assignment transition:
  required_lower_bounds
    = existing lineage floor when one exists
      + target account effective pass when ELIGIBILITY_RESTART or ACCOUNT_REKEY applies
      + source account effective pass when ACCOUNT_REKEY applies
  lineage_floor_after
    = max(every required lower bound)

successful admission charge:
  lineage_floor_after
    = max(
        lineage_floor_before,
        account_effective_pass_before,
        account_pass_after
      )
```

For a first assignment, the absent prior/source values are omitted rather than encoded as a misleading zero. For an
additional sibling or a continuous same-account work-request revision, every before/after floor map must equal the
current lineage floor byte-for-byte unless another simultaneously required flag contributes a greater lower bound.
`ACCOUNT_REKEY` is mandatory whenever the account ID, account kind, canonical Goal set, or Goal-binding fingerprint
changes; `ELIGIBILITY_RESTART` is mandatory only after a real closed eligibility episode, not for an immutable request
revision inside one continuous episode. Assignment or re-key also sets the target account's stored pass to
`max(target_account_stored_pass if present else target_account_system_pass, lineage_floor_after)` and then recomputes
the monotonic account-system floor. Thus a newly created Goal account starts at current system service, while a
previously served lineage cannot erase its debt by changing Goal membership, shared-account hash, work request, or
eligibility episode. A charge advances only the selected lineage floor; sibling requests share that updated floor and
do not receive separate charges. Historical assignments, floors, and charges remain immutable.

#### Canonical lineage head and service-band Events

At every scheduling decision boundary, Rust derives exactly one canonical head from the complete current eligible
request set of each lineage. The fixed ascending head tuple is:

```text
service_band_ordinal
deadline_urgency_ordinal
critical_frontier_relevance_ordinal
eligible_since_utc_ms
eligible_since_event_sequence
work_request_id canonical UTF-8 bytes
work_request_revision
```

Every tuple field uses the exact currentness and enum rules already defined in this contract. In particular, forecast
Deadline urgency participates only while its `FORECAST` branch is current; a current Event-backed `ACTUAL_SOFT_MISS`
uses its `ACTUAL_SOFT_MISS` branch; stale, unavailable, or indeterminate urgency receives no promotion. If Rust cannot
establish the complete eligible sibling set, an assignment, or any non-neutralizable head input, the lineage head and
service projection become `INDETERMINATE`; it does not select a convenient sibling.

Only the canonical head contributes the lineage once to semantic backlog and only in the head's effective service
band and shared fairness account. Non-head siblings are retained in the lineage input fingerprint for audit and
invalidation, but never enter another band/account active set. If the head has active work-request backoff, its whole
lineage is temporarily nonselectable; a sibling cannot bypass the head. This suppression does not remove the head
from semantic backlog or reset its account backlog episode.

Every initial head, head replacement, head-comparator input change, effective-band change, account re-key, eligible-set
change, or transition to/from no eligible head is recorded as an exact payload in the existing immutable Event log:

```yaml
SchedulingLineageHeadBandChanged:
  schema_version: scheduling-lineage-head-band-changed.v0.1
  event_id:
  transition_id:
  idempotency_key:
  service_epoch:
  scheduling_policy_revision:
  fairness_lineage_id:
  task_id:
  lifecycle_generation:
  lineage_head_generation:
  change_flags: []
  cause_codes: []
  trigger_flags: []
  materialization_context: LIVE | RECOVERY_CATCH_UP
  trigger_event_ids: []
  old_head:
    presence: ABSENT | PRESENT
    work_request_id: required_when_PRESENT
    work_request_revision: required_when_PRESENT
    assignment_id: required_when_PRESENT
    assignment_revision: required_when_PRESENT
    fairness_account_id: required_when_PRESENT
    effective_service_band: required_when_PRESENT
    head_comparator_key: required_when_PRESENT
  new_head:
    presence: ABSENT | PRESENT
    work_request_id: required_when_PRESENT
    work_request_revision: required_when_PRESENT
    assignment_id: required_when_PRESENT
    assignment_revision: required_when_PRESENT
    fairness_account_id: required_when_PRESENT
    effective_service_band: required_when_PRESENT
    head_comparator_key: required_when_PRESENT
  eligible_request_set_fingerprint_before:
  eligible_request_set_fingerprint_after:
  lineage_head_fingerprint_before: optional
  lineage_head_fingerprint_after: optional
  source_backlog_episode_ref: optional
  target_backlog_episode_ref: optional
  effective_at_utc_ms:
  materialized_at_utc_ms:
  time_authority_policy_revision:
  next_head_or_band_transition_utc_ms: optional
  boundary_batch_id:
  boundary_batch_ordinal:
  boundary_batch_size:
  boundary_batch_anchor_event_sequence:
  boundary_batch_final_event_sequence:
  pre_complete_semantic_backlogged_set_fingerprint:
  final_complete_semantic_backlogged_set_fingerprint:
  boundary_batch_fingerprint:
  input_event_sequence:
  event_sequence:
  semantic_fingerprint:
```

Exactly one `old_head.presence` / `new_head.presence` may be `ABSENT` for entry/exit; both cannot be `ABSENT`. Every
field marked `required_when_PRESENT` is absent when that branch is `ABSENT`. A fact-driven change commits
the source fact reduction, this Event, lineage-head Current State, and old/new semantic backlog migration in the same
Rust transaction.

`change_flags` is a nonempty, deduplicated list mechanically derived from the exact old/new state in this order:

```text
0 HEAD_PRESENCE_CHANGED
1 ELIGIBLE_REQUEST_SET_CHANGED
2 HEAD_IDENTITY_CHANGED
3 HEAD_COMPARATOR_INPUT_CHANGED
4 EFFECTIVE_BAND_CHANGED
5 ACCOUNT_BINDING_CHANGED
```

The flags use these exact predicates:

```text
HEAD_PRESENCE_CHANGED
  <=> old_head.presence != new_head.presence

ELIGIBLE_REQUEST_SET_CHANGED
  <=> eligible_request_set_fingerprint_before != eligible_request_set_fingerprint_after

HEAD_IDENTITY_CHANGED
  <=> both heads are PRESENT and their
      (work_request_id, work_request_revision, assignment_id, assignment_revision) tuples differ

HEAD_COMPARATOR_INPUT_CHANGED
  <=> both heads are PRESENT and their normalized head_comparator_key values differ

EFFECTIVE_BAND_CHANGED
  <=> both heads are PRESENT and their effective_service_band values differ

ACCOUNT_BINDING_CHANGED
  <=> both heads are PRESENT and their fairness_account_id values differ
```

Thus an initial/exit transition uses `HEAD_PRESENCE_CHANGED` plus
`ELIGIBLE_REQUEST_SET_CHANGED` when its exact set fingerprint also changed; absent-side sentinels do not manufacture the
four PRESENT-only flags. A comparator-only change is legal and requires `HEAD_COMPARATOR_INPUT_CHANGED`, including a
change in effective Deadline urgency, critical-frontier rank, eligible-since evidence, or the complete
Focus/Expedite/Deadline input sets. Every true predicate is present and every false predicate absent; no primary reason
or precedence may hide a simultaneous difference. Both heads absent remains illegal.

`trigger_flags` is a nonempty, deduplicated list in fixed order `FACT_EVENT`, `TIME_BOUNDARY`.
`FACT_EVENT` is present exactly when the sorted `trigger_event_ids` set is nonempty. `TIME_BOUNDARY` is present exactly
when one or more already-contracted time inputs became due at `effective_at_utc_ms`. Both are present when one atomic
boundary batch reduces fact and due-time transitions together. `materialization_context` records whether that same
canonical reduction occurred in normal live processing or recovery catch-up; it is not a competing trigger and cannot
replace either flag. Recovery replay of an already materialized Event emits nothing, while recovery catch-up uses the
same semantic trigger predicates as live materialization.

The deterministic transition identity is:

```text
transition_id
  = sha256(canonical-CBOR(
      "scheduling-lineage-head-band-transition.v0.1",
      service_epoch,
      fairness_lineage_id,
      lineage_head_generation,
      effective_at_utc_ms,
      lineage_head_fingerprint_before or "ABSENT",
      lineage_head_fingerprint_after or "ABSENT",
      change_flags,
      trigger_flags,
      boundary_batch_id,
      boundary_batch_fingerprint,
      input_event_sequence
    ))

idempotency_key
  = "scheduling-lineage-head-band.v0.1/" + transition_id
```

Rust enforces uniqueness for both fields. Exact replay returns the existing Event; the same key with a different
canonical payload makes the service projection `INDETERMINATE` and closes normal selection. Because change and trigger
flags participate in transition identity, a reducer cannot emit the same logical transition key with an arbitrarily
different single-cause label.

`lineage_head_generation` starts at `1` for the first head Event in a service epoch and increments by exactly one for
each later Event for that lineage. If the fully reduced before/after head, band, account, and eligible-request-set
fingerprints are identical, Rust emits no Event and does not advance the generation.

`cause_codes` is a deduplicated ascending list under this fixed ordinal:

```text
0 ELIGIBLE_REQUEST_SET_CHANGED
1 ACCOUNT_BINDING_CHANGED
2 PRIORITY_OR_FRONTIER_CHANGED
3 FOCUS_CURRENTNESS_CHANGED
4 EXPEDITE_CURRENTNESS_CHANGED
5 DEADLINE_URGENCY_CURRENTNESS_CHANGED
6 AGING_QUANTUM_REACHED
7 SCHEDULING_POLICY_CHANGED
8 RECOVERY_REDERIVATION
```

A time-only change is materialized before selection and again before admission. Rust processes missed boundary
instants in ascending `effective_at_utc_ms` order. At one instant it atomically reduces every owning
fact/currentness transition due at that instant, canonicalizes its cause codes and flags by their fixed ordinals,
freezes the complete pre-boundary service state, derives the complete final post-boundary state, and then emits at most
one resulting head/band Event per affected lineage in ascending canonical `fairness_lineage_id` bytes. Catch-up
ordering is only `(effective_at_utc_ms, fairness_lineage_id bytes)`; cause order cannot create an intermediate semantic
state or affect lineage order.

```text
boundary_batch_id
  = sha256(canonical-CBOR(
      "scheduling-lineage-boundary-batch.v0.1",
      service_epoch,
      effective_at_utc_ms,
      input_event_sequence,
      materialization_context,
      sorted affected fairness_lineage_ids,
      sorted trigger refs,
      sorted cause_codes,
      sorted change_flags and trigger_flags by lineage,
      pre_complete_semantic_backlogged_set_fingerprint,
      final_complete_semantic_backlogged_set_fingerprint
    ))
```

Every Event in the batch binds the same ID/fingerprint, size, anchor/final Event sequences, and complete endpoint
fingerprints; `boundary_batch_ordinal` is its zero-based position in the sorted lineage order. Event sequences are
allocated together in the transaction. `boundary_batch_anchor_event_sequence` is the minimum and
`boundary_batch_final_event_sequence` the maximum sequence allocated to the batch. The lineage Events provide ordered
audit facts, but no intermediate per-Event set is allowed to open/close an episode or advance a system floor. The
materialization context, sorted trigger refs, cause codes, flags, pre-state, and complete final state form
`boundary_batch_fingerprint`, making the batch
idempotent across retry and recovery. `effective_at_utc_ms` records the theoretical boundary; Event sequence remains
canonical authority and catch-up never retroactively changes an earlier selection or charge.

Time-driven boundaries include the next aging quantum, Focus/expedite expiry, exact `FORECAST` urgency expiry or
Deadline transition, and any other already-contracted input expiry that can change the head tuple or effective band.
The Event reducer computes the next boundary from the complete eligible sibling set. If trusted time, a required wake,
or the complete transition input is unavailable, normal selection remains closed with
`SELECTION_POLICY_UNAVAILABLE`; Rust never silently leaves an old band current. Recovery replays these Events first,
then uses trusted current time to materialize any due catch-up Events before reopening normal selection.

Deleting, rebuilding, or temporarily failing to load a rebuildable analytical cache is not a business cause code and
cannot by itself emit this Event. Rust must reproduce the required normalized input from the same canonical basis or
keep the service projection `INDETERMINATE` until that input is current. A cache rebuilt from the same input
fingerprint must reproduce the same head/band state without advancing generation, backlog age, pass, or Event
sequence.

`SchedulingServiceProjection` is an operational reducer view rebuilt from explicit service-epoch, assignment, and
lineage-head/band and successful-admission charge Events:

```yaml
SchedulingServiceProjection:
  schema_version: scheduling-service-pass.v0.1
  result_semantics: OPERATIONAL_REDUCER_VIEW
  service_epoch:
  service_epoch_generation:
  epoch_start_event_id:
  epoch_start_event_sequence:
  epoch_initialization_mode: RESET_ALL_WITHIN_NEW_EPOCH_TO_ZERO
  scheduling_policy_revision:
  arithmetic: U128_BE_V1
  band_system_pass:
  band_pass_by_band: {}
  account_system_pass_by_band: {}
  account_pass_by_band: {}
  band_admitted_counts: {} # diagnostic only
  account_admitted_counts_by_band: {} # diagnostic only
  consecutive_focus_or_urgent:
  consecutive_non_background:
  lineage_service_floor_by_band:
    "<fairness_lineage_id>": {}
  lineage_head_state:
    "<fairness_lineage_id>":
      lineage_head_generation:
      status: CURRENT | INDETERMINATE
      fairness_account_id:
      lineage_assignment_generation:
      current_eligible_assignment_refs: []
      current_eligible_request_set_fingerprint:
      canonical_head_assignment_ref: required_when_CURRENT
      canonical_head_work_request_ref: required_when_CURRENT
      effective_service_band: required_when_CURRENT
      head_comparator_key: required_when_CURRENT
      lineage_head_event_id: required_when_CURRENT
      lineage_head_event_sequence: required_when_CURRENT
      lineage_head_fingerprint: required_when_CURRENT
      next_head_or_band_transition_utc_ms: optional
  backlog_episode_state_by_band_account:
    "<service_band>/<fairness_account_id>":
      episode_id:
      episode_generation:
      status: BACKLOGGED | EMPTY
      backlogged_since_event_sequence: required_when_BACKLOGGED
      opened_by_event_id: required_when_BACKLOGGED
      closed_at_event_sequence: required_when_EMPTY
      current_eligible_lineage_refs: []
      current_head_work_request_refs: []
      current_head_assignment_revision_refs: []
      current_eligible_request_set_fingerprints: []
      semantic_backlogged_set_fingerprint:
      last_reduced_event_sequence:
  complete_lineage_head_set_fingerprint:
  complete_semantic_backlogged_set_fingerprint:
  reducer_currentness: CURRENT | REBUILD_REQUIRED | REBUILDING | INDETERMINATE
  reduced_through_event_sequence:
  reducer_contract_version: scheduling-service-pass.v0.1
  policy_revision_refs: []
  input_fingerprint:
  reduced_at_utc_ms:
  next_time_transition_utc_ms: optional
```

Raw admitted counts are diagnostics only. They never enter the comparator.

For backlog age, `semantic backlogged` has one narrow meaning: a lineage with a `CURRENT` canonical head in the same
service epoch whose exact head work request has reducer `CURRENT` and outcome `ELIGIBLE`, whether its preselection
status is `CANDIDATE` or `SUPPRESSED_BY_ACTIVE_BACKOFF`. Temporary `SchedulingBackoffProjection`, an OPEN handoff, or
another transient selection suppression changes the selectable set but does not remove the head lineage from this
semantic backlog. The service reducer maintains one deterministic episode per
`(service_epoch, effective_service_band, fairness_account_id)`:

```text
semantic set EMPTY -> NONEMPTY
  -> open the next checked episode_generation
  -> episode_id = sha256(canonical-CBOR(
       "fairness-backlog-episode.v0.1",
       service_epoch,
       service_band,
       fairness_account_id,
       episode_generation,
       triggering_event_sequence))
  -> backlogged_since_event_sequence = triggering_event_sequence

semantic set remains NONEMPTY
  -> preserve episode_id, generation, and backlogged_since_event_sequence
  -> update only current refs and set fingerprint

semantic set NONEMPTY -> EMPTY
  -> close at the triggering Event sequence
  -> clear backlogged_since from current comparator input

semantic set remains EMPTY
  -> no episode opens and no age accumulates
```

An eligibility restart after an actually empty account opens a new episode. A sibling-request revision, head change,
or eligibility restart while another head lineage keeps the band/account nonempty preserves the account episode.
Backoff expiry or clear only changes the selectable set and therefore cannot fabricate a younger backlog episode.

A boundary batch removes every affected lineage from its source set and adds every affected lineage to its target set
before any backlog episode or system floor is reduced. For each band/account, episode transition compares only the
complete pre-batch set with the complete final post-batch set:

```text
EMPTY -> NONEMPTY
  -> open at boundary_batch_anchor_event_sequence

NONEMPTY -> NONEMPTY
  -> preserve the existing episode exactly, including during swaps and cycles

NONEMPTY -> EMPTY
  -> close at boundary_batch_final_event_sequence

EMPTY -> EMPTY
  -> remain empty
```

The same endpoint rule governs monotonic band/account system-floor recomputation. Thus two lineages swapping
band/accounts, a multi-lineage cycle, or a merge/split cannot manufacture a transient EMPTY state, younger backlog
age, idle credit, or an intermediate system-pass advance from per-lineage Event ordering. The transaction advances
each affected lineage head generation and both complete head/backlog fingerprints once. A sibling can never remain in
the source band after the complete batch commits.

Assignment re-key, split, and merge update all sibling assignments, the exact lineage floor maps, lineage head, and
source/target backlog sets atomically. A same-account sibling assignment revision changes refs and the eligible-set/head
fingerprints but not the account episode unless it actually changes the canonical head band. At a new service epoch,
old assignments, floors, heads, and episodes remain historical; every eligible request is reassigned, each lineage
head is rederived, each lineage floor starts at zero, and every nonempty new-epoch band/account opens at the
`FairnessServiceEpochStarted` sequence as specified above.

The complete selectable-set fingerprint is computed synchronously at selection and admission from canonical semantic
heads after active-backoff and OPEN-handoff suppression; it is bound in selection/charge evidence, not stored as a
long-lived time-bearing field in `SchedulingServiceProjection`. Every active account's comparator age still comes
from its open semantic backlog episode. Missing sibling assignment, conflicting sibling account, missing head Event,
head/eligible-set mismatch, stale due transition, impossible episode transition, service-floor decrease, or a current
selectable account without one BACKLOGGED episode makes the service projection `INDETERMINATE` and closes normal
selection.

A successful local admission writes one `SchedulingServiceCharge` payload into the existing Event object. It is not a
new formal object:

```yaml
SchedulingServiceCharge:
  schema_version: scheduling-service-charge.v0.1
  charge_id:
  idempotency_key: service_epoch/selection_id/admission_event_id
  service_epoch:
  scheduling_policy_revision:
  selection_id:
  admission_event_id:
  run_id:
  service_band:
  band_weight:
  band_stride:
  band_system_pass_before:
  band_stored_pass_before:
  band_effective_pass_before:
  band_pass_after:
  band_system_pass_after:
  fairness_assignment_id:
  fairness_assignment_revision:
  fairness_lineage_id:
  fairness_account_id:
  account_stride:
  account_system_pass_before:
  account_stored_pass_before:
  account_lineage_floor_before:
  account_effective_pass_before:
  account_pass_after:
  account_system_pass_after:
  lineage_service_floor_before:
  lineage_service_floor_after:
  lineage_head_generation:
  lineage_head_fingerprint:
  lineage_eligible_request_set_fingerprint:
  backlog_episode_id:
  backlog_episode_generation:
  account_backlogged_since_event_sequence:
  pre_semantic_backlogged_set_fingerprint:
  pre_selectable_set_fingerprint:
  pre_complete_lineage_head_set_fingerprint:
  post_semantic_backlogged_set_fingerprint:
  post_selectable_set_fingerprint:
  post_complete_lineage_head_set_fingerprint:
  focus_directive_set_fingerprint:
  expedite_directive_set_fingerprint:
  deadline_urgency_set_fingerprint:
  consumed_expedite_directive_refs: []
  post_expedite_directive_set_fingerprint:
  consecutive_focus_or_urgent_before:
  consecutive_focus_or_urgent_after:
  consecutive_non_background_before:
  consecutive_non_background_after:
```

The charge's lineage floor must equal the successful-admission formula above. The Current State pass/floor/head rows,
charge Event, admission Event, Run, permit, reservations, claims, consumption of every bound current applicable
Expedite directive, sibling-assignment eligibility reduction, and Outbox are committed in the same successful
local-admission transaction. Because one new nonterminal Run makes the Task
lifecycle ineligible, all sibling assignments leave current semantic backlog atomically; no sibling remains available
for a second share. Technical rollback writes no charge or floor change. A later host rejection does not reverse the
service charge because the work already received admission service. This charge is independent of `RUN_ATTEMPTS`
Budget consumption.

### 7.8 Deterministic selection algorithm

Before comparing anything, Rust materializes every due lineage head/band transition and proves the complete
lineage-head set `CURRENT`. Selection then forms the complete current selectable candidate set from canonical heads
whose exact assessment is `CURRENT + ELIGIBLE + CANDIDATE`, after head backoff and OPEN-handoff suppression.
Non-head sibling requests never enter this set. Inactive bands and accounts do not participate in a minimum and never
accumulate idle credit. Head backoff suppresses that lineage without resetting the separate semantic backlog episode
defined in Section 7.7.

```text
1. Derive exactly one `starvation_guard_outcome` from the pre-admission counters and complete selectable set, in this
   precedence order:
   - `BACKGROUND_FORCED` when `consecutive_non_background >= max_consecutive_non_background` and a selectable
     BACKGROUND candidate exists; allowed band is BACKGROUND only
   - otherwise `NON_FOCUS_OR_URGENT_FORCED` when
     `consecutive_focus_or_urgent >= max_consecutive_focus_or_urgent` and a selectable non-FOCUS/non-URGENT candidate
     exists; allowed bands exclude FOCUS and URGENT
   - otherwise `NONE`; all selectable bands remain allowed

2. For every allowed active band:
     band_effective_pass
       = max(stored_band_pass or band_system_pass, band_system_pass)
   choose the lowest:
     band_effective_pass
     fixed band ordinal

3. For every active fairness account inside the chosen band:
     account_lineage_floor
       = maximum current lineage_service_floor for the band across canonical heads in that account
     account_effective_pass
       = max(
           stored_account_pass or account_system_pass,
           account_system_pass,
           account_lineage_floor
         )
   choose the lowest:
     account_effective_pass
     account_backlogged_since_event_sequence
     canonical fairness_account_id bytes

4. Inside the account, compare only canonical lineage heads:
     deadline_urgency_rank
     critical_frontier_relevance
     eligible_since_utc_ms
     eligible_since_event_sequence
     task_id
     work_request_id

5. Persist one TaskPrioritySelectionSnapshot and AdmissionHandoffRecord. Bind the selected lineage head generation,
   complete eligible sibling-set fingerprint, complete lineage-head-set fingerprint, complete applicable
   Focus/Expedite/Deadline-urgency sets and their fingerprints, and earliest transition across the complete semantic
   lineage set.
   Selection records proposed pass changes but does not advance service.

6. Successful local admission first materializes every now-due head/band transition, then rechecks service epoch,
   policy, all selected-lineage sibling assignments, canonical head, the complete Focus/Expedite/Deadline-urgency input
   sets, backlog episode, complete head/semantic/selectable sets, system/entity/lineage-floor passes, counters, and
   service-state fingerprint in the admission transaction.
   Any mismatch consumes/supersedes the selection and requires a fresh selection.

7. Successful local admission applies:
     selected_band_pass_after
       = checked(band_effective_pass + band_stride_scale / band_weight)
     selected_account_pass_after
       = checked(account_effective_pass + fairness_account_stride)
     selected_lineage_floor_after
       = max(
           selected_lineage_floor_before,
           account_effective_pass,
           selected_account_pass_after
         )

8. Reduce every sibling assignment out of current eligibility because the admitted Run makes the Task lifecycle
   ineligible. Recompute the complete post-admission lineage-head, semantic backlog, backlog episodes, and selectable
   sets using the same transaction facts.
   For each affected layer:
     active set nonempty
       -> system_pass_after = max(system_pass_before, minimum active effective pass after charge)
     active set empty
       -> system_pass_after = max(system_pass_before, selected_pass_after)
   Every stored and system pass is monotonic.

9. Update the two bounded counters from the admitted service band only:
     admitted FOCUS or URGENT
       -> consecutive_focus_or_urgent_after = min(before + 1, max_consecutive_focus_or_urgent)
     admitted other band
       -> consecutive_focus_or_urgent_after = 0
     admitted non-BACKGROUND
       -> consecutive_non_background_after = min(before + 1, max_consecutive_non_background)
     admitted BACKGROUND
       -> consecutive_non_background_after = 0
```

The post-admission sets, sibling reduction, and minimum cannot be omitted: admission may change Budget, Capacity, Run,
expedite, and eligibility facts. Omitting them would recreate a selectable sibling, stale minimums, false backlog age,
and idle credit. Counters change
only in the same successful local-admission transaction as `SchedulingServiceCharge`; rejected admission, technical
rollback, host rejection, backoff, or projection rebuild changes neither counter. Counter arithmetic is checked `u64`
and the policy-threshold cap prevents overflow. A service epoch starts both counters at zero.

Every comparison is ascending under these fixed encodings:

```text
service-band ordinal:
  FOCUS=0, URGENT=1, HIGH=2, NORMAL=3, LOW=4, BACKGROUND=5

deadline urgency ordinal:
  OVERDUE_SOFT=0, NEGATIVE_MARGIN=1, ZERO_MARGIN=2,
  TIGHT_POSITIVE_MARGIN=3, POSITIVE_MARGIN=4, UNKNOWN=5,
  NO_COMPATIBLE_COMPLETION_TARGET=6

critical-frontier relevance ordinal:
  ALL_REMAINING_ROUTES=0, SOME_REMAINING_ROUTES=1,
  UNKNOWN=2, NOT_CURRENT_FRONTIER=3

identities:
  canonical stored UTF-8 bytes only;
  locale, case folding, display labels, and database collation are forbidden

starvation-guard outcome:
  NONE=0, NON_FOCUS_OR_URGENT_FORCED=1, BACKGROUND_FORCED=2
```

`critical_frontier_relevance` is derived only from a COMPLETE current Critical Work Frontier. Unknown or incomplete
frontier evidence receives the neutral `UNKNOWN` rank. Scheduling cannot choose an `ANY_OF` route or create a
Dependency to improve the rank.

A business rejection creates bounded backoff for the exact head work request and temporarily suppresses its lineage;
it does not promote a sibling to bypass that backoff. Rejected selection, technical rollback, or an admission
transaction that does not commit consumes no service or lineage-floor change.
### 7.9 TaskPrioritySelectionSnapshot compatible extension

The existing canonical name is retained. New selections use:

```yaml
TaskPrioritySelectionSnapshot:
  selection_schema_version: task-scheduling-selection.v0.1
  selection_id:
  admission_handoff_id:
  work_request_id:
  work_request_revision:
  work_subject_kind: EXECUTION_RUN | EFFECTFUL_VALIDATION_RUN
  lane: NORMAL
  task_id:
  task_aggregate_version_observed:
  lifecycle_generation:
  priority_id:
  priority_revision:
  priority_policy_version:
  declared_class:
  context_status:
  scheduling_class:
  priority_context_fingerprint:
  dependency_revision_observed:
  dependency_set_snapshot_id: optional
  dependency_assessment_mode:
  dependency_assessment_freshness:
  dependency_assessment_outcome:
  dependency_input_fingerprint:
  scheduling_policy_revision:
  enforcement_scope_key:
  enforcement_profile_revision:
  enforcement_scope_assignment_revision:
  enforcement_scope_assignment_fingerprint:
  service_epoch:
  eligibility_assessment_id: diagnostic_optional
  eligibility_input_fingerprint:
  eligibility_episode_id:
  eligibility_observed_snapshot:
    task_state:
    task_aggregate_version:
    enforcement_profile_revision:
    enforcement_scope_assignment_revision:
    enforcement_scope_assignment_fingerprint:
    dependency_revision:
    dependency_assessment_mode:
    dependency_assessment_freshness:
    dependency_assessment_outcome:
    dependency_input_fingerprint:
    deadline_revisions: []
    budget_revisions: []
    calendar_start_authority_fence:
      bindings: []
      aggregate_fingerprint:
    capacity_pool_revisions: []
    host_offer_refs: []
    authorization_policy_revision:
    permit_prerequisite_fingerprint:
    host_fence_epoch:
    observed_event_sequence:
  scheduling_backoff_ref: optional
  scheduling_backoff_input_fingerprint: optional
  service_arithmetic: U128_BE_V1
  service_band:
  band_weight:
  band_stride:
  band_system_pass_before:
  band_stored_pass_before:
  band_effective_pass_before:
  proposed_band_pass_after:
  fairness_assignment_id:
  fairness_assignment_revision:
  fairness_assignment_fingerprint:
  fairness_lineage_id:
  lineage_assignment_generation:
  current_eligible_assignment_refs: []
  current_eligible_request_set_fingerprint:
  lineage_head_generation:
  lineage_head_event_id:
  lineage_head_event_sequence:
  lineage_head_fingerprint:
  complete_lineage_head_set_fingerprint:
  fairness_account_id:
  account_backlog_episode_id:
  account_backlog_episode_generation:
  account_backlogged_since_event_sequence:
  account_system_pass_before:
  account_stored_pass_before:
  account_lineage_floor_before:
  account_effective_pass_before:
  proposed_account_pass_after:
  lineage_service_floor_before:
  proposed_lineage_service_floor_after:
  semantic_backlogged_set_fingerprint:
  selectable_set_fingerprint:
  complete_lineage_transition_set_fingerprint:
  earliest_lineage_head_or_band_transition_utc_ms: optional
  earliest_selectable_set_transition_utc_ms: optional
  service_state_event_sequence:
  service_state_fingerprint:
  focus_directive_refs: []
  focus_directive_set_fingerprint:
  effective_focus: ACTIVE | INACTIVE | INDETERMINATE
  expedite_directive_refs: []
  expedite_directive_set_fingerprint:
  effective_expedite: ACTIVE | INACTIVE | INDETERMINATE
  deadline_urgency_assessment_refs: []
  applicable_deadline_urgency_set_fingerprint:
  deadline_urgency:
  deadline_urgency_driver_ref: optional
  critical_frontier_relevance:
  critical_frontier_basis_ref: optional
  time_critical_path_ref: optional
  schedule_plan_projection_ref: optional
  calendar_revision_refs: []
  capacity_pool_revision_refs: []
  host_offer_refs: []
  stable_comparator_key:
    encoding_contract: scheduling-comparator-tuple.v0.1
    starvation_guard_outcome: NONE | NON_FOCUS_OR_URGENT_FORCED | BACKGROUND_FORCED
    band_effective_pass_u128_be_hex:
    service_band_ordinal:
    account_effective_pass_u128_be_hex:
    account_backlogged_since_event_sequence:
    fairness_account_id_utf8_hex:
    deadline_urgency_ordinal:
    critical_frontier_relevance_ordinal:
    eligible_since_utc_ms:
    eligible_since_event_sequence:
    task_id_utf8_hex:
    work_request_id_utf8_hex:
  selection_input_fingerprint:
  selected_at_utc_ms:
  selected_at_event_sequence:
  selection_valid_until_utc_ms:
```

Historical snapshots without `selection_schema_version` remain historical `priority-selection.v0.1` evidence and may
not be used for new admission after the explicit scheduling-contract cutover Event.

`eligibility_assessment_id` is only a diagnostic pointer because the assessment projection is rebuildable. The
immutable selection embeds the normalized canonical observations used by the reducer, so later projection deletion or
rebuild cannot erase why that selection was made.

Selection disposition is derived from append-only Events:

```text
OPEN -> ADMITTED | REJECTED | SUPERSEDED
```

One `selection_id` may produce at most one business admission outcome. A technical rollback may retry the same command
idempotently because no outcome committed. A current-fact rejection consumes the selection and requires a new one.

Rust enforces partial unique indexes allowing at most one `OPEN` selection for one
`(work_request_id, work_request_revision)` and, more importantly, one `(task_id, lifecycle_generation)`. A Task with a
current OPEN selection is excluded as a whole from new candidate sets even when it has a rerun request and several
effectful Requirement requests. This preserves the one-nonterminal-Run boundary and prevents duplicate requests from
buying extra scheduling weight.

v0.1 additionally serializes the tiny local selection-to-admission handoff globally:
`max_open_normal_selections_global=1`. Rust does not create the next OPEN normal selection until the prior handoff is
`FINALIZED` or `SUPERSEDED`. Actual Runs remain concurrent; only the local choose/admit decision is serialized. This
ensures every next virtual-service decision observes the prior admission's committed service charge instead of
issuing a batch against the same pass snapshot. Batched provisional charges are deferred to a later contract.
Rust rejects any v0.1 policy revision whose value is not exactly `1`.

```yaml
AdmissionHandoffRecord:
  schema_version: admission-handoff.v0.1
  handoff_id:
  selection_id:
  work_request_id:
  work_request_revision:
  deterministic_admission_command_id:
  status: PENDING | CLAIMED | FINALIZED | SUPERSEDED
  local_claim_generation:
  local_claim_expires_at_utc_ms: optional
  selection_valid_until_utc_ms:
  created_event_sequence:
  updated_event_sequence:
```

The handoff is local durable work, not Run authority or an external Outbox. A local claim may be safely reclaimed after
lease loss because it invokes the same idempotent admission command and has not itself crossed an external boundary.
Admission outcome finalizes the handoff in the admission transaction. A relevant fact/work-request/profile change or
trusted expiry atomically supersedes both the OPEN selection and handoff before reselection. If time is uncertain, Rust
does not guess expiry; synchronous admission still rechecks every current fact. Recovery restores current handoffs,
replays only the same idempotent command when still current, and supersedes stale ones. Global “delete all OPEN” is not
the normal cleanup mechanism.

Rust computes `selection_valid_until_utc_ms` as the exclusive checked minimum of:

```text
selected_at_utc_ms + selection_handoff_ttl_ms
earliest known head/band transition across the complete current semantic lineage set
earliest active-head backoff expiry or other known transition that can change the complete selectable set
every member transition/expiry in the complete bound Focus and Expedite sets
every time-bearing validity/Deadline boundary in the complete bound Deadline-urgency assessment set
Hard Deadline boundary
Calendar window end only when Calendar is ENFORCING
Host offer expiry only when Capacity is ENFORCING
```

The complete-lineage transition fingerprint binds every input used to derive those first two transition minima, not
only the selected request. A missing, indeterminate, already-due, or unrepresentable required transition closes normal
selection instead of producing a longer validity. SHADOW observations remain in diagnostics but cannot shorten
canonical selection validity. Rust computes a local handoff claim expiry from Rust claim-transaction time plus
`local_handoff_claim_lease_ms`, capped by selection validity. Both policy values are positive integers. The local claim
lease controls only which Rust worker owns the handoff; renewal never extends selection validity or admission
authority.

### 7.10 What ordering cannot do

```text
cannot change Task state or Priority
cannot create or modify Goal plan or Dependency
cannot reserve Budget or Capacity
cannot sign or revive permit
cannot write Outbox
cannot preempt active Run
cannot convert forecast into Deadline fact
cannot classify Goal BLOCKED
cannot delay control / recovery work
```

## 8. Atomic Admission and Recovery v0.1

### 8.1 Decision and scope

`create_run` remains the ordinary execution admission boundary. For a scope with
`normal_selection=ENFORCING`, every normal autonomous admission uses `AdmitSelectedWork` and references one OPEN
`TaskPrioritySelectionSnapshot` with current work-request identity. A Jenn direct execution request in that scope
still passes through Rust selection evidence; it is not a state-writing bypass.

For `normal_selection=SHADOW`, the pre-cutover accepted legacy admission path remains in force and continues to obey
its existing Task, Dependency, Deadline, Budget, permit, host, P3, and recovery contracts. The new reducer writes only
a separately labelled shadow comparison; it cannot supply legacy admission evidence. In one scope, the current
profile selects exactly one path: no command may mix legacy admission with this draft's selection, Calendar fence, or
Capacity claim. The profile cutover atomically disables new legacy normal admission before enabling
`AdmitSelectedWork`. `SUSPENDED_FAIL_CLOSED` permits neither path.

The local atomicity promise covers one Rust-owned SQLite write transaction only. It does not include JavaScript
dispatch, host acceptance, provider response, network delivery, or external side effect.

### 8.2 AdmitSelectedWork command

```yaml
AdmitSelectedWork:
  schema_version: admit-selected-work.v0.1
  command_id:
  actor:
  selection_id:
  work_request_id:
  work_request_revision:
  task_id:
  expected_task_aggregate_version:
  expected_lifecycle_generation:
  work_subject_kind: EXECUTION_RUN | EFFECTFUL_VALIDATION_RUN
```

`CONTROL_RECOVERY` commands use their existing explicit command types and do not fabricate this normal selection.

The command carries no caller-selected candidate disposition, effect scope, Capacity request, or host-pool override.
Rust reads all of them from the exact immutable `SchedulingWorkRequestRevision` bound by the selection. Any redundant
transport hint must byte-for-byte match that revision and is discarded before the domain command. Concrete host and
pool choice remains Rust's deterministic first-fit admission derivation.

### 8.3 Synchronous admission read set

The transaction uses one Rust UTC `now` and a consistent current read set. It must:

```text
deduplicate Inbox command_id and canonical payload hash
verify selection OPEN, exact immutable work-request revision, Task identity, generation, and selection input fingerprint
verify trusted now is strictly before selection_valid_until_utc_ms and the handoff is current PENDING/CLAIMED generation
verify the exact current SchedulingEnforcementProfileRevision and its subsystem modes
materialize due Deadline, admission-Calendar, and scheduling lineage-head/band facts before deciding
verify the exact service epoch, scheduling policy, complete selected-lineage sibling assignments, canonical head,
complete applicable Focus/Expedite/Deadline-urgency sets, current band/account/system/lineage-floor passes, complete
lineage-head/semantic/selectable-set derivations, and service-state fingerprint; reject overflow or any mismatch
re-run Task lifecycle and one-nonterminal-Run guards
re-run active Validation, Control Intent, UNKNOWN, and unresolved-effect guards
freeze or read the current Validation Set and Dependency Set at the accepted commitment boundary
recompute CURRENT + SATISFIED dependency closure with all completion assurance CONFIRMED
re-check all applicable Hard Deadlines and current Rust time authority
re-check every applicable Budget envelope and dimension; enforce HARD_CAP rejection and recompute all reservation amounts
when Calendar mode is ENFORCING, re-check all required admission Calendars and fence vectors
when Capacity mode is ENFORCING, re-check allowlisted pools, host offers, existing claims, fence generations, and requested units
re-check current authorization, P3, policy, capability, permit prerequisites, and host capability
re-check candidate disposition authority
```

Planning projections, old Eligibility assessments, and the selection snapshot are diagnostic inputs only. They do not
replace this read set.

### 8.4 Successful local transaction

`RunAttemptsBudgetAuthorityBinding` is an immutable infrastructure record, not a new formal core object. It preserves
the complete budget authority that applied when one Run was admitted, so recovery can distinguish "not applicable"
from "the expected reservation row is missing":

```yaml
RunAttemptsBudgetAuthorityBinding:
  schema_version: run-attempts-budget-authority-binding.v0.1
  binding_id:
  run_id:
  task_id:
  lifecycle_generation:
  completion_epoch:
  execution_epoch:
  work_request_id:
  work_request_revision:
  task_commitment_snapshot_id:
  members:
    - budget_scope: TASK | GOAL
      budget_scope_id:
      budget_envelope_id:
      budget_envelope_revision:
      budget_reservation_id:
      dimension: RUN_ATTEMPTS
      reserved_units: 1
  member_set_fingerprint:
  authority_binding_fingerprint:
  admission_event_id:
```

The member list is complete for every Task- and Goal-scoped `RUN_ATTEMPTS` Budget envelope applicable to that exact
admission. It is sorted by `(budget_scope ordinal TASK=0 GOAL=1, budget_scope_id canonical UTF-8 bytes,
budget_envelope_id canonical UTF-8 bytes, budget_envelope_revision, budget_reservation_id canonical UTF-8 bytes)`.
Duplicate scope/envelope revisions, duplicate reservation IDs, zero members when an applicable envelope exists, or a
current applicable envelope missing from the derived set rejects admission.

The fingerprints are exact:

```text
member_set_fingerprint
  = sha256(canonical-CBOR(
      "run-attempts-budget-authority-members.v0.1",
      sorted complete members
    ))

authority_binding_fingerprint
  = sha256(canonical-CBOR(
      "run-attempts-budget-authority-binding.v0.1",
      binding_id,
      run_id,
      task_id,
      lifecycle_generation,
      completion_epoch,
      execution_epoch,
      work_request_id,
      work_request_revision,
      task_commitment_snapshot_id,
      member_set_fingerprint
    ))
```

`admission_event_id` is an immutable cross-reference but is excluded from these fingerprints to avoid a circular
Event/binding digest. There is exactly one binding per `(run_id, execution_epoch)`. The binding references the exact
reusable immutable TaskCommitmentSnapshot through `task_commitment_snapshot_id`; that snapshot never carries a
Run-specific reverse binding and is not mutated or superseded merely because a Run is admitted. The complete
`BudgetReservation` member set, Run, TaskPermit, admission Event, and Outbox intent all carry the same binding ID,
authority fingerprint, and member-set fingerprint and are committed or rolled back together. Every member reservation
also carries the binding ID and authority fingerprint. No scan of current envelopes or surviving reservation rows may
later substitute for this admitted authority set.

If every gate passes, the same transaction performs all applicable steps:

```text
1. allocate or reuse the phase-correct TaskCommitmentSnapshot
2. apply the exact candidate disposition: clear only an authorized execution rerun, preserve effectful Validation candidate
3. allocate the stable Run ID and increment execution_epoch exactly once
4. derive the complete applicable RUN_ATTEMPTS authority member set, allocate its reservation IDs, reserve one unit in
   every applicable Task/Goal envelope, and persist the immutable RunAttemptsBudgetAuthorityBinding; reserve all other
   applicable Budget dimensions; only HARD_CAP shortage rejects, while SOFT_TARGET excess remains risk
5. when Capacity mode is ENFORCING, acquire every required canonical CapacityClaim as one all-or-nothing set
6. create Run QUEUED with purpose EXECUTION or EFFECTFUL_VALIDATION
7. for EFFECTFUL_VALIDATION, bind the Run to the exact candidate, Validation Set, Requirement, and future attempt identity
8. issue the TaskPermit bound to commitment, Dependency, Deadline, Budget authority binding, Capacity, host, policy, and fences
9. append admission and selection-disposition Events bound to the Budget authority binding
10. append exactly one SchedulingServiceCharge Event and atomically advance monotonic band/account/system and selected
    lineage-floor passes from the rechecked service state; reduce all sibling assignments from semantic eligibility,
    consume every rechecked current applicable Expedite directive bound by the selection, clear the admitted lineage
    head, and update the complete head/backlog/selectable and directive-set fingerprints
11. write one stable-idempotency-key Outbox dispatch intent bound to the Budget authority binding
12. update Current State and commit
```

Run, every BudgetReservation, permit, Event, and Outbox bind:

```yaml
scheduling_enforcement_binding:
  enforcement_scope_key:
  enforcement_profile_revision:
  normal_selection_mode: ENFORCING
  admission_calendar_mode: SHADOW | ENFORCING
  capacity_admission_mode: SHADOW | ENFORCING
  capacity_pool_allowlist_fingerprint: optional
  run_attempts_budget_authority_binding_id:
  run_attempts_budget_authority_binding_fingerprint:
  expected_run_attempts_reservation_set_fingerprint:
```

`SUSPENDED_FAIL_CLOSED` cannot reach this transaction. A `SHADOW` subsystem contributes diagnostic refs only: it
cannot create a deny, authoritative Calendar fence, or CapacityClaim. Profile revision change before canonical host
acceptance invalidates the unaccepted start authority and forces current reconciliation.

For an effectful Validation Run, step 7 allocates one stable `validation_attempt_id` and stores it on the Run binding,
but creates no Validation attempt row yet. The ID is deterministically derived under a ledger namespace from the
immutable Run ID, lifecycle generation, completion epoch, Validation Set snapshot, and Requirement revision. Rust
enforces unique `(run_id, validation_requirement_revision)` and `validation_attempt_id` indexes. Command or Fact
replay can therefore return the same attempt and cannot create a second one.

The accepted Budget v0.1 behavior remains authoritative. `SOFT_TARGET` reservations are required for accurate
`consumed + reserved` risk even though they never become a hard gate. Capacity steps become active only after an
explicit Capacity cutover Event names the applicable pool/work-class scope; accepting this document alone does not
activate enforcement. No CapacityClaim, SchedulingServiceCharge, or pass update may survive a failed transaction.

`Run QUEUED` means the ledger admitted a dispatch intent. It does not prove host acceptance or execution.

### 8.5 Rejection and conflict

```text
business gate rejection
  -> persist Inbox rejection and SelectionAdmissionRejected Event
  -> consume the selection
  -> persist only the exact fence / blocker / backoff allowed by its owning contract
  -> create no Run, permit, BudgetReservation, CapacityClaim, or Outbox

SQLite / CAS / BUSY_SNAPSHOT technical conflict
  -> roll back everything
  -> do not consume selection
  -> retry the same command idempotently with a fresh transaction
```

`SelectionAdmissionRejected` is an exact payload in the existing Event object:

```yaml
SelectionAdmissionRejected:
  schema_version: selection-admission-rejected.v0.1
  event_id:
  command_id:
  selection_id:
  handoff_id:
  work_request_id:
  work_request_revision:
  task_id:
  lifecycle_generation:
  reason_codes: []
  reason_set_fingerprint:
  primary_reason_code:
  backoff_reason_codes: []
  backoff_reason_set_fingerprint: optional
  still_current_for_reselection: boolean
  rejection_input_fingerprint:
  event_sequence:
  committed_at_utc_ms:
  semantic_fingerprint:
```

Rust emits every independently applicable reason, deduplicated in this fixed order:

```text
0  SELECTION_INPUT_STALE
1  HANDOFF_STALE
2  WORK_REQUEST_STALE
3  ENFORCEMENT_PROFILE_CHANGED
4  SERVICE_STATE_CHANGED
5  TASK_LIFECYCLE_OR_ACTIVE_WORK_CHANGED
6  VALIDATION_OR_COMMITMENT_CHANGED
7  UNKNOWN_OR_UNRECONCILED_EFFECT
8  DEPENDENCY_GATE_NOT_SATISFIED
9  DEADLINE_NEW_START_AUTHORITY_PROHIBITED
10 DEADLINE_TIME_AUTHORITY_UNCERTAIN
11 HARD_BUDGET_RESERVATION_UNAVAILABLE
12 BUDGET_ACCOUNTING_INDETERMINATE
13 ADMISSION_CALENDAR_CLOSED
14 ADMISSION_CALENDAR_INDETERMINATE
15 CAPACITY_CURRENTLY_UNAVAILABLE
16 CAPACITY_FACT_INDETERMINATE
17 AUTHORIZATION_PREREQUISITE_MISSING
18 AUTHORIZATION_ASSESSMENT_INDETERMINATE
19 POLICY_OR_P3_DENIED
20 HOST_CAPABILITY_MISSING_OR_STALE
21 CANDIDATE_DISPOSITION_INVALID
```

The reducer evaluates one fixed normalized gate vector in that same registry order from the single consistent read set;
early return after the first failure is forbidden. A gate whose subject is structurally inapplicable because an earlier
identity/version guard failed has the canonical internal outcome `NOT_APPLICABLE_DUE_TO_UPSTREAM_GUARD` and contributes
no second reason. A gate that is applicable but cannot establish its required fact contributes the corresponding
`*_INDETERMINATE`, stale, or missing reason above. `rejection_input_fingerprint` covers every gate outcome, including
PASS and canonical NOT_APPLICABLE outcomes, so two evaluation orders cannot produce different complete reason sets.

`primary_reason_code` is the first member under this registry and is diagnostic only. The fixed backoff-eligible subset
is `DEPENDENCY_GATE_NOT_SATISFIED`, `DEADLINE_TIME_AUTHORITY_UNCERTAIN`,
`HARD_BUDGET_RESERVATION_UNAVAILABLE`, `BUDGET_ACCOUNTING_INDETERMINATE`, `ADMISSION_CALENDAR_CLOSED`,
`ADMISSION_CALENDAR_INDETERMINATE`, `CAPACITY_CURRENTLY_UNAVAILABLE`, `CAPACITY_FACT_INDETERMINATE`,
`AUTHORIZATION_ASSESSMENT_INDETERMINATE`, and `HOST_CAPABILITY_MISSING_OR_STALE`. `backoff_reason_codes` is the
ordered intersection; it cannot contain another code. A backoff may be created only when this intersection is nonempty
and the exact work-request revision remains semantically current for reselection. Stale selection/handoff/service
evidence is superseded and freshly reduced without manufacturing backoff. Unknown, duplicated, reordered, omitted, or
outcome-inconsistent reasons are a protocol conflict.

Admission rejection does not make Task `FAILED`, does not create a failed Run, and does not prove Goal `BLOCKED`.

### 8.6 Host dispatch, start authority, and actual STARTED

After the local admission commit:

```text
Node dispatcher claims Outbox with the current permit and fence checks
host performs local permit / capability / availability / idempotency gate
host proposes HostWorkAcceptanceFact
Rust commits ACCEPTED or REJECTED
host waits for the committed acceptance Event acknowledgement
only an ACCEPTED acknowledgement grants one bounded start authority
host later reports actual STARTED or proves no execution
```

Outbox `ACKED` is transport receipt only. It is neither host acceptance nor actual start.

```yaml
HostWorkAcceptanceFact:
  schema_version: host-work-acceptance.v0.1
  receipt_id:
  fact: ACCEPTED | REJECTED
  run_id:
  work_request_id:
  work_request_revision:
  enforcement_profile_revision:
  task_id:
  lifecycle_generation:
  completion_epoch:
  execution_epoch:
  run_purpose: TASK_EXECUTION | EFFECTFUL_VALIDATION
  validation_attempt_id: required_for_EFFECTFUL_VALIDATION
  task_commitment_snapshot_id:
  dependency_set_snapshot_id:
  dependency_authority_binding_fingerprint:
  effect_scope_fingerprint:
  authority_bundle_fingerprint:
  permit_id:
  outbox_intent_id:
  host_id:
  host_session_id:
  host_fence_epoch:
  acceptance_state: # required only for ACCEPTED
    start_authority_kind: ONE_TIME_AFTER_COMMITTED_ACK
    capacity_disposition: NOT_APPLICABLE | ACQUIRED_BOUND
    capacity_claim_set_id: optional
    capacity_allocation_receipt_id: optional
    allocation_lease_generation: optional
    allocation_lease_policy_revision: optional
    allocation_lease_expires_at_utc_ms: optional
    host_watchdog_generation: optional
    start_grace_expires_at_utc_ms:
    start_authority_expires_at_utc_ms:
    start_grace_policy_revision:
    effective_active_stop_cutoff_utc_ms: optional
  rejection_state: # required only for REJECTED
    no_execution_proven: true
    capacity_disposition: NOT_APPLICABLE | NOT_ACQUIRED_PROVEN | RELEASED_RECEIPT_BOUND | ACQUIRED_ABORT_RELEASE_PENDING | INDETERMINATE
    capacity_claim_set_id: optional
    capacity_allocation_receipt_id: optional
    capacity_release_receipt_id: optional
  host_observed_at: optional_non_authoritative
  fact_committed_at_utc_ms:
```

```yaml
HostWorkStartDispositionFact:
  schema_version: host-work-start-disposition.v0.1
  receipt_id:
  fact: STARTED | REJECTED
  run_id:
  task_id:
  work_request_id:
  work_request_revision:
  enforcement_profile_revision:
  lifecycle_generation:
  completion_epoch:
  execution_epoch:
  run_purpose: TASK_EXECUTION | EFFECTFUL_VALIDATION
  validation_attempt_id: required_for_EFFECTFUL_VALIDATION
  task_commitment_snapshot_id:
  dependency_set_snapshot_id:
  dependency_authority_binding_fingerprint:
  effect_scope_fingerprint:
  authority_bundle_fingerprint:
  permit_id:
  host_id:
  host_session_id:
  host_fence_epoch:
  acceptance_receipt_id:
  acceptance_event_id:
  started_state: # required only for STARTED
    no_execution_proven: false
    capacity_disposition: NOT_APPLICABLE | ALLOCATION_CONTINUES
    capacity_claim_set_id: optional
    capacity_allocation_receipt_id: optional
    allocation_lease_generation: optional
    allocation_lease_policy_revision: optional
    allocation_lease_expires_at_utc_ms: optional
    host_watchdog_generation: optional
    start_authority_expires_at_utc_ms:
  rejected_state: # required only for REJECTED
    no_execution_proven: true
    allocation_release_disposition: NOT_APPLICABLE | RELEASED_RECEIPT_BOUND | RELEASE_PENDING | INDETERMINATE
    capacity_claim_set_id: optional
    capacity_allocation_receipt_id: optional
    capacity_release_receipt_id: optional
  host_observed_at: optional_non_authoritative
  fact_committed_at_utc_ms:
```

Both payloads are strict tagged unions. `ACCEPTED` requires only `acceptance_state`; acceptance `REJECTED` requires
only `rejection_state`. `STARTED` requires only `started_state`; start `REJECTED` requires only `rejected_state`.
Any enum/branch mismatch, `ACCEPTED + no_execution_proven`, `STARTED + release disposition`, or field from the other
branch is a protocol conflict and cannot mutate Run, Validation, Capacity, or Budget.

`fact_committed_at_utc_ms` is Rust transaction time, never a host timestamp. For `ACCEPTED`, Rust requires the exact
current Deadline start-authority gate, permit, host fence, authority bundle, and, when Calendar is ENFORCING, complete
`calendar_start_authority_fence`. With Capacity SHADOW, acceptance uses `NOT_APPLICABLE` and forbids every
Capacity/lease/watchdog field. With Capacity ENFORCING, Rust accepts the exact complete `ACQUIRED` allocation receipt
and `HostWorkAcceptanceFact` in one transaction.

For acceptance `REJECTED`, execution absence must be proven. Capacity is reusable only with the complete current
`REJECTED_NOT_ACQUIRED` or `RELEASED` receipt. A prepared `ACQUIRED` allocation whose later authority gate closes
moves to `RELEASING` and remains occupied until a matching release receipt. If effect occurrence is uncertain, the Run,
claim set, and affected Budget follow `UNKNOWN`.

For `ACCEPTED`, Rust computes:

```text
start_grace_expires_at_utc_ms
  = checked(fact_committed_at_utc_ms + host_start_grace_ms)

start_authority_expires_at_utc_ms
  = min(
      start_grace_expires_at_utc_ms,
      allocation_lease_expires_at_utc_ms when Capacity is ENFORCING,
      effective_active_stop_cutoff_utc_ms when present
    )
```

Ordinary Calendar close and `HARD_NEW_START_AUTHORITY_CUTOFF` do not enter this minimum: they prevent a new authority
commit but do not revoke authority already committed before their boundary. Active-stop cutoff, Control Intent,
UNKNOWN, host/session change, non-Calendar permit / Dependency / effect-scope revocation, and watchdog expiry can block
launch earlier. An ordinary `calendar_start_authority_fence` generation change after acceptance is historical audit
evidence, not a post-acceptance revocation. Allocation renewal is forbidden while the Run is `LEASED`, so no renewal
can extend pre-start authority.

The host arms a provisional monotonic watchdog before proposing acceptance and activates, but never restarts, it after
the committed acknowledgement. `STARTED` must bind the exact `acceptance_event_id` returned by that acknowledgement.
Rust accepts `STARTED` only with trusted `now < start_authority_expires_at_utc_ms`, matching current non-Calendar
generations and all dynamic revocation guards, and before either host watchdog fires. It verifies the exact historical
Calendar/Deadline acceptance evidence but does not re-run an ordinary close or new-start cutoff against an authority
already committed before that boundary.

Here, “current non-Calendar generations” is limited to generations whose accepted contracts can revoke an unlaunched
effect: host session/fence, Control Intent, UNKNOWN/no-new-Run fence, Dependency/effect-scope/permit revocation,
allocation/watchdog authority, and `HARD_ACTIVE_EXECUTION_STOP_CUTOFF`. It does not mean that an ordinary later
SchedulingEnforcementProfileRevision, CapacityPoolRevision, Calendar revision/occurrence change, or
`HARD_NEW_START_AUTHORITY_CUTOFF` revision revokes a bounded authority already committed under its exact historical
profile/pool/calendar/deadline binding. Such a later revision blocks new acceptance; stopping or preventing launch of
the accepted authority requires one of the explicit dynamic revocation contracts above. The historical profile and
pool fingerprints remain mandatory audit/binding evidence and are never silently rebound to current revisions.

```text
HostWorkAcceptanceFact ACCEPTED
  -> Run QUEUED -> LEASED
  -> complete Capacity claim set may become ALLOCATED
  -> effectful Validation attempt may become PENDING under Section 8.7
  -> one-time start authority is established
  -> every Task/Goal RUN_ATTEMPTS reservation bound at admission remains RESERVED
  -> does not prove actual process or effect start

HostWorkStartDispositionFact STARTED
  -> Run LEASED -> RUNNING
  -> bound Validation PENDING -> RUNNING
  -> every bound RUN_ATTEMPTS reservation RESERVED or reconciled UNKNOWN -> SETTLED exactly once
  -> Capacity ENFORCING requires ALLOCATION_CONTINUES
  -> opens the matching ActiveWorkSpan

stronger authenticated terminal execution Fact for the same epoch
  -> may settle RUN_ATTEMPTS exactly once when STARTED Fact was lost
  -> must still reconcile Run / Validation / effect history

HostWorkStartDispositionFact REJECTED + no_execution_proven=true
  -> Run LEASED -> REJECTED
  -> bound Validation PENDING -> CANCELLED
  -> every bound RUN_ATTEMPTS reservation RESERVED -> RELEASED
  -> other definitely unused Budget reservations finalize
  -> Capacity independently becomes RELEASED, RELEASING, or UNKNOWN from its own receipt evidence

possible launch or conflicting execution evidence
  -> Run UNKNOWN
  -> existing Validation INCONCLUSIVE
  -> every unsettled bound RUN_ATTEMPTS reservation becomes UNKNOWN unless stronger positive execution evidence already settled it
  -> Capacity and affected unsettled Budget remain fully occupied
  -> no automatic retry, release, or reuse
```

Budget usage accounting is monotonic and evidence-based. The normal reservation path is:

```text
create_run
  -> reserve exactly 1 RUN_ATTEMPTS unit in every applicable Task and Goal Budget envelope

HostWorkAccepted
  -> keep the complete bound reservation set RESERVED

positive execution evidence
  -> SETTLE every reservation in the complete bound set exactly once

authoritative no-execution proof
  -> RELEASE every reservation in the complete bound set even when Capacity release remains RELEASING or UNKNOWN

possible execution
  -> every unsettled bound reservation becomes UNKNOWN and retains full occupancy
  -> later positive evidence may reconcile to SETTLED
  -> later authoritative no-execution proof may reconcile to RELEASED only through UNKNOWN authority
```

`RELEASED` is not an evidence sink. If a later authenticated same-execution-epoch `STARTED` Fact or stronger terminal
execution Fact proves that the same Run actually executed after its bound `RUN_ATTEMPTS` reservation set was released, Rust
must account for the real use. The previously terminal `REJECTED` Run is not reopened as `UNKNOWN`, `RUNNING`, or any
other nonterminal state. Instead, Rust appends the positive Fact, compensates Budget, contradicts the earlier
no-execution assurance, and opens an independent late-effect reconciliation in one correction transaction. The
reconciliation uses the existing control / recovery and unresolved-effect paths; neither record is a new formal
object:

```yaml
RunAttemptsReleaseContradictedByPositiveExecution:
  schema_version: run-attempts-release-contradicted-by-positive-execution.v0.1
  contradiction_id:
  accounting_idempotency_key: run_id/execution_epoch/run_attempts_budget_authority_binding_fingerprint
  positive_evidence_dedup_key: run_id/execution_epoch/positive_execution_fact_id
  run_id:
  task_id:
  lifecycle_generation:
  completion_epoch:
  execution_epoch:
  work_request_id:
  work_request_revision:
  host_id:
  host_session_id:
  host_fence_epoch:
  run_attempts_budget_authority_binding_id:
  run_attempts_budget_authority_binding_fingerprint:
  expected_run_attempts_reservation_set_fingerprint:
  observed_run_attempts_reservation_set_fingerprint:
  budget_correction_outcome: COMPLETE | INDETERMINATE
  run_attempts_budget_corrections: # required complete set only for COMPLETE; absent for INDETERMINATE
    - budget_scope: TASK | GOAL
      budget_scope_id:
      budget_envelope_id:
      budget_envelope_revision:
      budget_reservation_id:
      dimension: RUN_ATTEMPTS
      release_event_id:
      release_evidence_ref:
      previous_reservation_status: RELEASED
      corrected_reservation_status: SETTLED
      compensating_usage_units: 1
  budget_correction_gap_refs: # required nonempty only for INDETERMINATE; absent for COMPLETE
    - gap_kind: AUTHORITY_BINDING | EXPECTED_RESERVATION | RELEASE_EVENT | RESERVATION_STATUS_CONFLICT
      budget_scope: TASK | GOAL | optional
      budget_scope_id: optional
      reference_id:
      observed_fingerprint: optional
  run_attempts_budget_correction_set_fingerprint:
  positive_execution_fact_kind: HOST_WORK_START_DISPOSITION_STARTED | AUTHENTICATED_TERMINAL_EXECUTION
  positive_execution_fact_id:
  positive_execution_fact_fingerprint:
  prior_run_terminal_state: REJECTED
  run_terminal_state_after_correction: REJECTED
  prior_no_execution_assurance_disposition: CONTRADICTED
  late_execution_observation: STARTED_POSSIBLY_ACTIVE | TERMINAL_EXECUTION_PROVEN
  late_effect_reconciliation_id:
  late_effect_reconciliation_opened: true
  no_new_run_fence_generation:
  successor_scan:
    scanned_through_event_sequence:
    task_aggregate_version:
    later_execution_epochs:
      - run_id:
        execution_epoch:
        run_state:
        run_object_version:
        disposition: NO_ACTION_TERMINAL_REVIEW | FENCE_BEFORE_DISPATCH | STOP_QUERY_RECONCILE | UNKNOWN_RECONCILIATION
        current_candidate_commitment_id: optional
        result_revision: optional
        validation_attempt_refs: []
    current_candidate_commitment_id: optional
    current_result_revision: optional
    current_validation_attempt_refs: []
    scan_fingerprint:
  task_projection_disposition: ACTIVE_RECONCILIATION | BLOCKED_UNRESOLVED_EFFECT | TERMINAL_UNCHANGED_ASSURANCE_CHALLENGED
  capacity_claim_set_id: optional
  capacity_reconciliation_disposition: NOT_APPLICABLE | RETAIN_FULL_OCCUPANCY | TERMINAL_CONTRADICTION_QUARANTINE
  incident_disposition: QUARANTINED_NO_AUTOMATIC_RETRY
  event_id:
  event_sequence:
  committed_at_utc_ms:
  semantic_fingerprint:
```

The correction is accepted only when every Run, work-request, execution epoch, host session/fence, effect scope, and
positive-Fact identity matches the exact historical attempt and the authenticated Fact proves real execution rather
than merely replaying an old command or permit. The expected reservation set comes only from the immutable
`RunAttemptsBudgetAuthorityBinding` committed with that Run, never from current envelope revisions, surviving
reservation rows, a reconstructed "applicable now" query, or their union. Its ID, authority fingerprint, and member-set
fingerprint must byte-for-byte match the copies bound to the original Run, permit, admission
Event, Outbox, and every observed member reservation. It contains exactly one `RUN_ATTEMPTS` reservation for every
Task/Goal Budget envelope that applied to the admission. Entries are sorted by:

```text
budget_scope ordinal: TASK=0, GOAL=1
budget_scope_id canonical UTF-8 bytes
budget_envelope_id canonical UTF-8 bytes
budget_envelope_revision
budget_reservation_id canonical UTF-8 bytes
```

The correction fingerprint uses one strict tagged-union formula for both outcomes:

```text
run_attempts_budget_correction_set_fingerprint
  = sha256(canonical-CBOR(
      "run-attempts-budget-correction-set.v0.1",
      budget_correction_outcome,
      run_id,
      execution_epoch,
      run_attempts_budget_authority_binding_id,
      run_attempts_budget_authority_binding_fingerprint,
      expected_run_attempts_reservation_set_fingerprint,
      observed_run_attempts_reservation_set_fingerprint,
      COMPLETE ? sorted run_attempts_budget_corrections : sorted budget_correction_gap_refs
    ))
```

The fingerprint field itself is never an input. Both tagged branches require the observed-set fingerprint. It is
computed with the exact `run-attempts-budget-authority-members.v0.1` member-set formula after projecting every observed
historical reservation to the authority member shape; release/status evidence stays in the correction or gap payload,
not in this membership fingerprint. `COMPLETE` therefore requires byte equality between observed and expected member-set
fingerprints. For `INDETERMINATE`, the observed fingerprint covers only the canonical discoverable member projections,
while the correction fingerprint separately binds the complete canonical gaps.

For `COMPLETE`, the observed set must match the expected fingerprint exactly, every member must bind the same Run and
execution epoch plus its immutable release Event, `budget_correction_gap_refs` is empty, and every entry has the fixed
`RELEASED -> SETTLED / 1 unit` payload. A duplicate/missing envelope, reservation, release Event, scope, or mismatched
status makes the outcome `INDETERMINATE`; Rust never silently corrects only the discoverable subset. Expired or violated
authority does not erase real usage: Rust records the existing authority-violation evidence when applicable, while
never reviving that authority.

The outcome is a strict tagged union. `COMPLETE` requires the nonempty complete correction list and forbids gap refs.
`INDETERMINATE` requires nonempty gap refs sorted by fixed gap-kind ordinal
`AUTHORITY_BINDING, EXPECTED_RESERVATION, RELEASE_EVENT, RESERVATION_STATUS_CONFLICT`, then budget-scope ordinal
`TASK, GOAL, absent`, scope-ID bytes, and reference-ID bytes; it forbids `run_attempts_budget_corrections`. Its observed
set fingerprint covers every discoverable historical member projection; the correction-set fingerprint covers the
outcome, authority/expected/observed fingerprints, correction list or gap refs, Run, and execution epoch. A branch
mismatch or a different payload under the same accounting key is a ledger-integrity conflict.

Missing, duplicated, conflicting, or corrupt `RunAttemptsBudgetAuthorityBinding` identity or payload always yields
`INDETERMINATE`; Rust may not infer completeness from the rows that remain. The fail-closed affected-scope set is the
union of every scope named by the immutable expected binding and every scope named by an observed conflicting payload.
If the binding itself is missing or cannot be authenticated, Rust uses only independently authentic admission Event,
Run, permit, Outbox, and reservation cross-references to enumerate reconstructable affected
scopes, marks every such scope indeterminate, fences the Task, and performs no Budget compensation until the exact
binding is recovered or repaired through an explicit reconciliation fact. Absence of a reconstructable Goal scope is
not evidence that no Goal envelope applied.

For a `COMPLETE` set, the same transaction:

```text
append the immutable positive execution Fact and contradiction Event
change every exact bound RUN_ATTEMPTS reservation RELEASED -> SETTLED exactly once
add exactly one compensating consumed unit to each bound Budget envelope, even if this exposes over-consumption
mark the exact no-execution assurance contradicted without deleting or rewriting its historical Event
keep the old Run terminal REJECTED; never transition it back to UNKNOWN, RUNNING, or another nonterminal state
open one idempotent late-effect reconciliation and preserve the actual execution / effect history
when the late Fact is STARTED without terminal proof, commit the durable addressable stop/query intents for that exact
  historical host execution regardless of whether a successor exists
atomically raise the Task no-new-Run fence and scan every later execution epoch, Run, candidate, result, and Validation
  attempt through the correction transaction's Event sequence
fence every successor Run before another effect; for QUEUED work supersede unsent Outbox / permit only when no dispatch
  is proven, otherwise enter the existing UNKNOWN query path
for LEASED / RUNNING / WAITING or possibly dispatched successor work, create or reuse the existing PAUSE Control Intent,
  commit durable addressable stop/query intents, and reconcile effects without changing the old REJECTED Run; external
  control dispatch occurs only after commit and is replayed idempotently by recovery
keep every terminal successor Run immutable, but quarantine its candidate, result, evidence, and Validation completion
  eligibility until overlap and effect influence are resolved
if the successor scan finds more than one later nonterminal execution Run, treat it as a ledger-integrity conflict,
  fence and stop/query every such Run, keep completion quarantined, and keep normal admission closed
when there is no successor, still retain the no-new-Run fence and complete the late-effect reconciliation
for a nonterminal Task, apply the existing unresolved-effect completion block without manufacturing PASS, candidate
  adoption, or retry
if the Task was already DONE / FAILED / CANCELLED, preserve that terminal state, challenge any completion assurance or
  current candidate/result support affected by the contradiction, and require the ordinary explicit reopen authority
  rather than automatically reopening the Task
quarantine this Run / host-session / effect lineage from automatic retry
retain any nonterminal Capacity claim at full occupancy
if its Capacity claim was RELEASED or EXPIRED, emit the existing CapacityTerminalContradiction and quarantine the
  complete claim-set units with pool accounting INDETERMINATE
close new admission for any now-overconsumed or indeterminate affected Budget scope until reconciliation
never revive the old permit, start authority, Run lease, or Validation attempt
```

For `INDETERMINATE`, Rust still appends the authenticated positive Fact, contradiction Event, no-new-Run fence,
successor scan, late-effect reconciliation, stop/query/quarantine dispositions, and no-execution-assurance
contradiction in one transaction. It changes no Budget reservation and adds no partial consumed amount. Every
scope in the fail-closed affected-scope union and the Task's Budget authority projection becomes `INDETERMINATE`; new
admission under those scopes fails closed. Recovery must reconstruct the exact historical authority binding and complete sorted set
before an existing reconciliation resolution Event with the same `accounting_idempotency_key` may atomically perform
the complete correction. That resolution does not create a second contradiction, execution attempt, or late-effect
reconciliation.

Task projection remains deterministic without weakening the one-nonterminal-execution-Run invariant. Terminal-state
preservation has first priority; every ACTIVE / BLOCKED branch below applies only to a nonterminal Task:

```text
Task was already DONE / FAILED / CANCELLED when the contradiction arrived
  -> preserve the terminal Task state; do not automatically reopen it
  -> challenge affected completion assurance and candidate / result / Validation support
  -> withhold Goal / dependency closure support and result reuse under the existing assurance rules until reconciliation

nonterminal Task and one later QUEUED / LEASED / RUNNING / WAITING successor exists
  -> that successor remains the only nonterminal execution Run
  -> Task remains ACTIVE while its stop / query / effect reconciliation is unfinished

nonterminal Task and late STARTED says the old physical execution may still be active, with no current UNKNOWN or
nonterminal successor determining Task state
  -> old Run remains terminal REJECTED
  -> Task uses the already accepted bounded ACTIVE coordination form with
     activity_kind = COORDINATING
     coordination_subtype = LATE_EFFECT_RECONCILIATION
     coordination context binding the reconciliation ID, next action, owner, and activity deadline
  -> stop / query / effect reconciliation proceeds through CONTROL_RECOVERY

the narrow ACTIVE coordination branch does not override the existing current-Run UNKNOWN -> Task BLOCKED rule

no physical execution remains active, but effect influence or successor result eligibility is unresolved, and Task is
nonterminal
  -> Task becomes BLOCKED through its existing unresolved-effect blocking context

late terminal execution Fact and all affected effects are fully reconciled
  -> remove the reconciliation activity / blocker through its resolution Event
  -> re-run the ordinary Task / candidate / Validation reducer; do not infer READY, VERIFYING, DONE, or retry
```

The original release and Run-terminal Events remain immutable; a complete contradiction/resolution explains why every
bound Budget reservation is `SETTLED`, while an indeterminate one keeps the affected Budget projections fail-closed.
The former no-execution assurance no longer has current decision authority in either case. Accounting is idempotent by
the Run/execution epoch, immutable Budget authority binding, complete sorted reservation/release set, and accounting
idempotency key, not by the number of corroborating positive Facts.
Duplicate or later stronger positive evidence for the same execution epoch attaches to the existing reconciliation and
cannot add a second unit to any envelope, contradiction, fence generation, stop intent, or successor disposition. Once this correction settles the real attempt, later
no-execution evidence cannot release it again. Contradictory identity or generation evidence is retained as incident
evidence but cannot mutate Budget. No branch creates a new Run, automatically retries either attempt, revives the old
permit, or lets a terminal successor's candidate / result / Validation complete the Task before reconciliation.

Run identity and `attempt_number` are historical attempt-record identity; they are not proof of Budget consumption.
Repeated accept/no-launch failures belong to host reliability, backoff, and circuit-breaking evidence rather than
being mislabeled as executed attempts.

Before local launch and when Rust accepts `STARTED`, host and Rust recheck current host fence, Control Intent, UNKNOWN,
effect scope, allocation/watchdog state, and `HARD_ACTIVE_EXECUTION_STOP_CUTOFF`. A host timestamp cannot retroactively
establish Calendar or Deadline compliance. v0.1 intentionally gates the Rust-committed start authority because an
asynchronous host timestamp cannot reliably prove remote physical start against UTC.

The host performs no effectful work before the committed acceptance acknowledgement. If actual launch may have
occurred but the disposition cannot be reconciled, the Run becomes `UNKNOWN`. When Rust time authority is uncertain it
cannot accept `STARTED`, decide that authority expired, or release by UTC. The host monotonic watchdog still blocks new
effects at its conservative boundary.

UI and adapters must render `LEASED` as "start authority granted; actual start unconfirmed", never "running" or
"already started".
### 8.7 Effectful Validation binding

An effectful Validation uses a Run with `run_purpose = EFFECTFUL_VALIDATION`.

Admission is allowed only from the exact current candidate under `PRESERVE_FOR_EFFECTFUL_VALIDATION`. It preserves
the result revision, candidate commitment, frozen Validation Set, and Requirement revision. It never clears or
supersedes the candidate merely because Validation needs an executor.

```text
local admission commit
  -> create Run QUEUED bound to the candidate and Requirement
  -> do not yet create a PENDING / RUNNING Validation attempt
  -> Task projects ACTIVE because a nonterminal Run exists
  -> preserve phase_checkpoint = VERIFYING

canonical HostWorkAccepted commit
  -> require matching Run, permit, work request, candidate, Requirement, and complete Capacity evidence when applicable
  -> atomically create exactly one Validation attempt in PENDING using the Run-reserved attempt identity
  -> bind attempt_id, Run, candidate, evidence scope, and allocation receipt

canonical HostWorkStartDisposition STARTED commit
  -> require the committed acceptance acknowledgement and exact same generations
  -> atomically advance Run LEASED -> RUNNING and Validation PENDING -> RUNNING

host rejection with no execution proven
  -> create no Validation attempt
  -> reject Run and return the Task to VERIFYING from its checkpoint after resource finalization

start rejection after canonical acceptance, with no execution proven
  -> requires `HostWorkStartDispositionFact(REJECTED, no_execution_proven=true)`
  -> atomically make Run REJECTED and the existing PENDING Validation CANCELLED
  -> release RUN_ATTEMPTS from RESERVED, and finalize other definitely unused Budget reservations
  -> release Capacity only with a matching RELEASED receipt; otherwise keep the claim set RELEASING
  -> Capacity release status does not delay evidence-backed RUN_ATTEMPTS release
```

```text
Run success
  -> only proves the execution attempt returned successfully
  -> does not make Validation PASSED

Validation decision
  -> still requires the Validator contract, evidence integrity, Requirement revision, input fingerprint, and currentness
```

The Validation attempt and Run retain separate state machines and identifiers. Their binding prevents a provider or
external-host Validation from bypassing Run, Budget, Capacity, permit, Deadline, UNKNOWN, and recovery contracts.

Terminal coupling is deliberately one-way and conservative:

```text
Run SUCCEEDED
  -> Validation remains RUNNING until the Validator accepts evidence and decides it

Run FAILED or TIMED_OUT
  -> bound Validation becomes ERROR, never FAILED/PASSED by inference

Run CANCELLED
  -> bound Validation becomes CANCELLED

Run UNKNOWN or acceptance uncertainty
  -> if an attempt exists, Validation becomes INCONCLUSIVE; no Validation UNKNOWN state is added
  -> no attempt exists if canonical HostWorkAccepted was never committed
  -> Task follows the accepted UNKNOWN reducer into BLOCKED while retaining VERIFYING checkpoint
  -> no new attempt, candidate discard, automatic retry, or Requirement waiver
```

After the Run and Validation are in known terminal states, resources are finalized, and no other blocker exists, the
Task reducer returns the Task to `VERIFYING` using the preserved phase checkpoint unless all required current
Validations now qualify it for `DONE`. A Run failure never directly makes the Task `FAILED`. Late facts are appended
and reconciled against the bound generations; they cannot revive a terminal attempt, reuse an old permit, or silently
replace the candidate.

### 8.8 Selection charging and backoff

Only a successful local admission commits one service charge and advances the service-band and fairness-account
passes. A later host rejection does not reverse that scheduling charge. `RUN_ATTEMPTS` remains an independent Budget
dimension and settles only when canonical positive execution evidence proves that the Run actually started.

An eligible current-fact rejection creates a bounded `SchedulingBackoffProjection` for the exact work request only
under the Section 8.5 backoff subset:

```yaml
SchedulingBackoffProjection:
  schema_version: scheduling-backoff.v0.1
  result_semantics: OPERATIONAL_REDUCER_VIEW
  work_request_id:
  work_request_revision:
  task_id:
  lifecycle_generation:
  source_rejection_event_id:
  reason_codes: []
  reason_set_fingerprint:
  primary_reason_code:
  backoff_reason_codes: []
  backoff_reason_set_fingerprint:
  consecutive_same_reason_set_rejections:
  not_before_reselection_utc_ms:
  scheduling_policy_revision:
  reducer_currentness: CURRENT | REBUILD_REQUIRED | REBUILDING | INDETERMINATE
  reduced_through_event_sequence:
  reducer_contract_version: scheduling-backoff.v0.1
  policy_revision_refs: []
  input_fingerprint:
  reduced_at_utc_ms:
  next_time_transition_utc_ms: optional
```

```text
base = selection_backoff_base_ms
exponent = max(0, consecutive_same_reason_set_rejections - 1)
next = min(base * 2^exponent, selection_backoff_max_ms)
```

“Same reason” means byte-identical complete `reason_codes`, `reason_set_fingerprint`, `backoff_reason_codes`, and
`backoff_reason_set_fingerprint`; the primary display reason alone never increments the counter. Rust performs the
multiplication with checked integers and a capped exponent. A revision to any fact bound by the complete rejection set
invalidates the old backoff and forces a new current reduction; if one reason disappears while another remains, the
old reason-set episode does not continue under the new set. Backoff is a reselection throttle, not Task WAITING state,
Deadline, or retry authority. Selection must observe the current exact work-request revision and active backoff as
defined in Section 7.3; a projection that is missing, stale, or bound to another revision cannot be used to suppress or
permit selection. SQLite/CAS technical rollback creates neither rejection Event nor backoff.

### 8.9 Recovery order

Resident startup keeps normal selection and admission closed until:

```text
1. validate schema, Event sequence, immutable rows, and Current State pointers
2. raise host fence epoch
3. restore Deadline, Dependency, permit, and completion-assurance fences
4. supersede legacy-schema, stale, or expired OPEN selections; restore current v0.1 handoffs and their claim generations
5. scan Run, Validation, RunAttemptsBudgetAuthorityBinding, BudgetReservation, CapacityClaim, Outbox,
   HostWorkAcceptance, HostWorkStartDisposition,
   `RunAttemptsReleaseContradictedByPositiveExecution`, every open late-effect reconciliation, all later execution
   epochs, current candidate/result/Validation bindings, start-grace, and effectful Validation attempt facts together
6. for each admitted Run, verify the one immutable authority binding and all cross-bound copies before using any
   RUN_ATTEMPTS reservation state; for each late-positive contradiction, verify the old Run stayed terminal REJECTED,
   derive the expected set only from that binding, compare the complete reservation/release set, replay the no-new-Run fence, rebuild the exact successor
   scan, and restore every required stop/query/quarantine disposition before normal work; an incomplete correction set
   keeps every affected Budget scope INDETERMINATE and normal admission closed
7. release only records whose dispatch is proven never to have left the ledger
8. mark possibly dispatched or possibly accepted work UNKNOWN; do not infer release from lease expiry
9. restore Control Intent, stop / fence, finalizer, late-effect activity/blocking context, and effect reconciliation
10. replay `FairnessServiceEpochStarted`, every per-request `FairnessAccountAssignmentRevision`,
    `SchedulingLineageHeadBandChanged`, and `SchedulingServiceCharge` Event; validate the epoch Event's all-zero
    pass/floor initialization and complete eligible-lineage fingerprint; deterministically rebuild per-request
    assignment uniqueness, fixed assignment-transition flags and compound floor lower bounds, sibling account
    consistency, lineage floors, canonical heads/bands, complete Focus/Expedite/Deadline-urgency input sets, every
    semantic backlog episode, complete rejection reason-set/backoff identity, and selectable set across sibling
    add/remove/revision, eligibility restart, re-key, merge, split, charge, and backoff; reject any partial sibling
    re-key, duplicate/missing assignment, multiple-band lineage,
    head/eligible-set mismatch, episode discontinuity, old-epoch comparison, pass/floor/counter discontinuity,
    duplicate charge, divergent payload under one transition ID/idempotency key, lineage conflict,
    set-fingerprint mismatch, or checked-integer overflow
11. restore durable due facts, scheduling backoff, and missed wake requests; with trusted time, materialize missed
    lineage head/band boundaries in `(effective_at_utc_ms, fairness_lineage_id bytes)` order after atomically reducing
    all same-instant causes and their fixed change/trigger flags; reduce episode/backlog/system-floor state only from
    each boundary batch's complete pre-set and final post-set before normal selection may reopen;
    without trusted time, keep the service projection `INDETERMINATE`
12. execute the recovery read barrier and repeat if relevant versions changed
13. confirm the minimum control / recovery path is operational
14. reopen safe Outbox claims and only then permit new normal selection / admission for Tasks without a late-effect fence
15. rebuild dependency assurance and impact-cut inputs, Task forecast boundary snapshots, Duration remaining
    projections, pure SchedulePlan, TimeCriticalPath, and Deadline urgency in dependency order without side effects;
    add ResourceSchedule only after its separate v0.2 acceptance and implementation activation
```

Recovery replays a still-current handoff only through its original deterministic admission command and completes those
handoffs before opening new normal selection. If admission observes expiry before a delayed cleanup wake, the same
transaction supersedes selection and handoff, rejects that command, and leaves the Task eligible for a fresh selection.

### 8.10 Crash-window table

| Crash window | Required result |
|---|---|
| Before SQLite commit | No admission fact exists; safe idempotent retry. |
| After commit, before Outbox claim | Run remains QUEUED; dispatch may proceed only after all current gates revalidate. |
| After Outbox dispatcher claim, before send, send status provably false | Release only the Outbox dispatcher lease; preserve the CapacityClaim and current permit, then safely re-claim the same Outbox intent. |
| Send may have occurred, no host Fact | Run / Capacity / Budget become UNKNOWN; no automatic retry. |
| Host accepted, Fact not committed | Query by stable idempotency key when supported; otherwise UNKNOWN. |
| HostWorkAccepted committed, StartDisposition missing, trusted now before authority expiry | Keep Run LEASED, Validation PENDING, allocation occupied, and RUN_ATTEMPTS RESERVED; query the stable ID. |
| Start authority elapsed and host proves no launch | Commit REJECTED, cancel PENDING Validation, release RUN_ATTEMPTS, and run the Capacity release finalizer independently. |
| Start may have occurred or disposition conflicts | Run UNKNOWN, existing Validation INCONCLUSIVE, allocation occupied/UNKNOWN, and RUN_ATTEMPTS becomes UNKNOWN unless stronger positive execution evidence already settled it. |
| Positive execution evidence arrives after RUN_ATTEMPTS was RELEASED | Derive the expected set only from the immutable `RunAttemptsBudgetAuthorityBinding`, append `RunAttemptsReleaseContradictedByPositiveExecution`, atomically compensate the complete sorted Run-bound Task/Goal reservation set RELEASED -> SETTLED once per envelope, contradict no-execution assurance, keep the old Run terminal REJECTED, fence new Run creation, scan all later epochs/candidates/results/Validations, and open independent late-effect reconciliation. A missing binding/member performs no partial Budget mutation and keeps the expected-plus-observed affected scopes INDETERMINATE. |
| Crash after contradiction commit, before a required stop/query is dispatched | Recovery replays the durable no-new-Run fence and same idempotent reconciliation; it does not reopen the old Run, duplicate Budget use, create a Run, or clear successor quarantine. |
| Late STARTED indicates the old physical execution may still be active | Keep the old Run terminal REJECTED, stop/query that exact historical execution through CONTROL_RECOVERY, and keep a nonterminal Task ACTIVE through a current nonterminal successor or bounded `COORDINATING / LATE_EFFECT_RECONCILIATION` activity until physical execution is known terminal. |
| A later QUEUED successor exists | Fence it in the correction transaction; supersede permit/Outbox and reject only when no dispatch is proven, otherwise use UNKNOWN query/reconciliation. |
| A later LEASED/RUNNING/WAITING successor exists | Preserve it as the only nonterminal Run, immediately fence effects, create/reuse PAUSE, stop/query/reconcile it, and keep a nonterminal Task ACTIVE until it is terminal; an already terminal Task stays terminal. |
| A later terminal successor or current candidate/result/Validation exists | Preserve historical terminal facts but quarantine candidate, result, evidence, and completion eligibility until overlap/effect influence is resolved. |
| No successor exists | Keep the no-new-Run fence and reconcile the late execution/effects; when nothing may remain active, unresolved influence projects a nonterminal Task BLOCKED rather than authorizing retry, while an already terminal Task stays terminal with affected assurance/support challenged. |
| Terminal receipt committed, settlement transaction interrupted | Idempotently settle or release from the committed receipt; never duplicate usage. |
| Capacity or Deadline revision races admission | Rust single-writer order decides; losing transaction rolls back and re-evaluates. |
| Task completion races admission | Same Task CAS permits exactly one result; no DONE Task with a new Run. |

### 8.11 Final admission invariants

```text
selection is single-use evidence, not authority
local admission is all-or-nothing
host acceptance is explicit and post-commit
transport ACK is not acceptance
capacity allocation is not permission
effectful Validation cannot bypass Run admission
UNKNOWN retains reservations and forbids auto-retry
host rejection does not fail Task
recovery never revives old selection or permit
late-positive correction never reopens a terminal REJECTED Run or creates a second nonterminal Run
late-positive correction never automatically reopens a terminal Task
late-effect reconciliation fences every later epoch before candidate, result, or Validation completion can advance Task
control / recovery remains live before normal admission reopens
```

## 9. Time Critical Path v0.1

### 9.1 Decision and acceptance dependency

This contract can be accepted only together with or after Duration Estimate v0.1 and Calendar v0.1.

`TimeCriticalPathProjection` is a Rust-derived read-only diagnosis from a current Goal plan, Task Dependency, Duration,
and Calendar. It is not a formal object, Critical Work Frontier, Goal route decision, Priority, Deadline, permit, or
scheduling authority.

v0.1 supports only:

```text
precedence longest-path
resource unconstrained
finish-to-start
zero lag
non-preemptive Task activity
```

### 9.2 Analysis target and route scenario

The only target is:

```text
ROUTE_SCENARIO_WORK_COMPLETE
```

It means the necessary Task work in the supplied analysis route scenario is projected complete. It does not mean Goal
`CLOSED + ACHIEVED`, Jenn completion review complete, Goal criteria accepted, or dependency completion assurance
finally confirmed for closure.

The route scenario is an embedded analysis request and never modifies the canonical Goal plan:

```yaml
route_scenario:
  criterion_route_bindings:
    - criterion_id:
      criterion_revision:
      route_group_id:
      route_group_revision:
  route_scenario_fingerprint:
```

Every current unsatisfied required criterion must bind exactly one current route group. Rust does not automatically
choose the fastest `ANY_OF` route and does not make a product decision for Jenn or Nobao.

### 9.3 TimeCriticalPathProjection

```yaml
TimeCriticalPathProjection:
  projection_id:
  projection_contract_version: time-critical-path.v0.1
  result_semantics: ANALYTICAL_PROJECTION
  analysis_kind: CALENDAR_AWARE_PRECEDENCE_FINISH_DRIVING_SUBGRAPH
  canonical_result_kind: FINISH_DRIVING_SUBGRAPH
  resource_model: UNCONSTRAINED
  capacity_contention: IGNORED
  goal_id:
  goal_plan_revision:
  target_kind: ROUTE_SCENARIO_WORK_COMPLETE
  route_scenario:
    criterion_route_bindings: []
    route_scenario_fingerprint:
  duration_scenario: OPTIMISTIC | MOST_LIKELY | PESSIMISTIC
  time_policy_revision:
  analysis_horizon_start_utc_ms:
  analysis_horizon_end_utc_ms:
  analysis_horizon_policy_revision:
  forecast_as_of_utc_ms:
  valid_until_utc_ms:
  time_currentness_policy_revision:
  next_recompute_reasons: []
  applicability: APPLICABLE | NOT_APPLICABLE
  freshness: CURRENT | STALE | EVALUATING
  coverage: UNAVAILABLE | PARTIAL | COMPLETE
  assessment: AVAILABLE | PARTIAL | UNAVAILABLE | INDETERMINATE | ROUTE_UNAVAILABLE | MODEL_INVALID | NOT_APPLICABLE
  reason_codes: []
  basis:
    plan_membership_refs: []
    route_scenario_ref:
    dependency_planning_bases: []
    deadline_revision_refs: []
    task_envelopes:
      - task_id:
        lifecycle_generation:
        completion_epoch:
        task_state:
        phase_checkpoint:
        task_work_boundary: ACTIVE_CURRENT_LIFECYCLE | CONFIRMED_CURRENT_COMPLETION | UNUSABLE_CURRENT_COMPLETION
        current_completion_ref_id: optional
        completion_assurance_version: optional
        completion_fence_generation: optional
        derived_remaining_duration_ref: optional
        derived_remaining_duration_fingerprint: optional
        derived_remaining_duration_valid_until_utc_ms: optional
        task_forecast_boundary_ref:
        task_forecast_boundary_fingerprint:
        forecast_constraint_owner_partition_fingerprint:
        active_work_release_outcome: NOT_APPLICABLE | DELEGATED_TO_DEPENDENCY_GEOMETRY | RELEASED_NOW | RELEASED_AT_KNOWN_UTC | UNAVAILABLE | INDETERMINATE
        completion_release_outcome: NOT_APPLICABLE | NO_ADDITIONAL_DELAY | RELEASED_AT_KNOWN_UTC | UNAVAILABLE | INDETERMINATE
        zero_remaining_basis_alignment: NOT_ZERO_REMAINING | MATCHED | MISMATCH | INDETERMINATE
        task_schedule_shape_assessment_ref:
        planning_calendar_resolution_ref:
        planning_calendar_resolution_fingerprint:
    assurance_expiry_refs: []
    algorithm_revision:
    policy_revision_refs: []
    input_revision_refs: []
    based_on_event_sequence:
    input_fingerprint:
  result:
    projected_target_finish_utc_ms: optional
    remaining_wall_span_ms: optional
    task_timings:
      - task_id:
        earliest_start_utc_ms:
        earliest_active_finish_utc_ms:
        earliest_finish_utc_ms:
        duration_value_ms:
        duration_scenario:
        planning_calendar_resolution_fingerprint:
    driving_subgraph:
      nodes: []
      edges:
        - from:
          to:
          kind: TASK_DEPENDENCY | TASK_RELEASE_BOUNDARY | COMPLETION_RELEASE_BOUNDARY | CALENDAR_AVAILABILITY | VIRTUAL_START | VIRTUAL_FINISH
          constraint_ref: optional
    representative_paths: []
    path_enumeration:
      status: COMPLETE | TRUNCATED | NOT_AVAILABLE
      emitted_count:
      total_count_if_known: optional
    deadline_diagnostics:
      - deadline_id:
        deadline_revision:
        deadline_scope: TASK | GOAL
        required_completion_semantics: TASK_DONE | GOAL_CLOSED_ACHIEVED
        forecast_completion_semantics: TASK_DONE | ROUTE_SCENARIO_WORK_COMPLETE
        compatibility: EXACT | LOWER_BOUND_ONLY | INCOMPATIBLE | INDETERMINATE
        projected_margin_ms: optional
        relation: BEFORE | AT_OR_AFTER | LOWER_BOUND_ONLY | UNKNOWN
  computed_at_utc_ms:
```

`TimeCriticalPathProjection.basis.input_fingerprint` covers the complete semantic Goal-plan and route scenario,
Dependency assurance/impact basis, Task state and phase, remaining-Duration basis, Task forecast-boundary and
owner-partition basis, planning Calendar resolutions, Deadline diagnostics, horizon, algorithm, and policy revisions.
It excludes `projection_id`, embedded row/snapshot IDs when their semantic fingerprints are bound, aggregate CAS
versions, read/reducer watermarks, and materialization timestamps. SchedulePlan and Time Critical Path therefore derive
byte-identical owner-partition fingerprints from byte-identical semantic inputs even when rebuilt at different read
barriers.

Projection edges and virtual nodes are not Task Dependency and cannot write `TaskDependencySpecRevision`.

### 9.4 Applicability and network membership

v0.1 current analysis applies only to an `ACTIVE` Goal with a current plan and the accepted target kind. A non-ACTIVE
Goal is `NOT_APPLICABLE`; v0.1 does not disguise lifecycle as a time-health problem.

The network includes:

```text
all current necessary leaf Tasks in the bound route groups
+ all current Task Dependency ancestry of those Tasks
```

Task state alone never proves a satisfied time boundary. Only a route member with
`CONFIRMED_CURRENT_COMPLETION`, or a dependency edge reduced to `CURRENT_COMPLETION_BOUNDARY` or
`PINNED_COMPLETION_BOUNDARY` by the exact current `DependencyPlanningBasisSnapshot`, contributes zero remaining
Duration. A reopened source may still satisfy an existing POSTCOMMIT consumer through its confirmed pinned historical
boundary while its current lifecycle appears separately when it is itself a route member.

`CHALLENGED` assurance cannot produce an aggregate `AVAILABLE` finish. A precisely proven unaffected fragment may be
reported `PARTIAL` without an aggregate finish; otherwise the result is `INDETERMINATE`. An effective required
`INVALIDATED` completion without a current UNAFFECTED cut or explicit replacement makes that route scenario
`ROUTE_UNAVAILABLE`. Time Critical Path does not convert that fact into Goal `BLOCKED`. A required FAILED / CANCELLED
current Task without a replacement likewise makes the time analysis unavailable; Critical Work Frontier, not Time
Critical Path, decides whether the Goal has a logical success route.

Every `ACTIVE_CURRENT_LIFECYCLE` node also requires one exact `TaskForecastBoundarySnapshot`. A release boundary is
not inferred from Task state, Duration, Calendar availability, Deadline, or absence of a Run. Complete evidence that a
release is external or unscheduled yields an unavailable aggregate; irreconcilable release evidence yields an
indeterminate aggregate. Neither case permits Time Critical Path to announce Goal `BLOCKED`.

The snapshot's `forecast_constraint_owner_partition` must be `COMPLETE`, must bind the exact same Dependency planning
basis and Duration remaining inputs carried by the Task envelope, and must be byte-identical by partition fingerprint
to any SchedulePlan input for the same Task, lifecycle, completion epoch, and route scenario. Neither projection requires
the other to exist or reads the other's result; both independently consume the same partition contract and exact inputs.
Dependency-owned waits contribute only through Dependency edges; Duration-owned completion conditions contribute only
through active Duration. Time Critical Path never adds either as an independent release edge.

### 9.5 Currentness

Any relevant change makes the old projection STALE:

```text
Goal plan or route membership revision
route scenario fingerprint
Task lifecycle generation, completion epoch, state, or phase
DependencySpecRevision
Dependency planning basis mode, outcome, assurance version, fence generation, impact-resolution cut, closure
fingerprint, reducer/policy revision, or assurance expiry
Task work-boundary classification
derived remaining Duration revision, frontier, assessment, or input fingerprint
Duration observation validity or measurement-policy revision
Task forecast boundary state, complete constraint refs, owner assignment, owner-basis fingerprint, partition fingerprint,
release outcome, condition refs, next transition / expiry, or input fingerprint
planning Calendar revision or tzdb binding
Deadline revision used by deadline diagnostics
algorithm revision
```

Time passage uses the shared validity contract instead of making the projection stale every millisecond:

```text
event-backed input revision changes -> immediately STALE
trusted now < valid_until_utc_ms     -> may remain CURRENT
trusted now >= valid_until_utc_ms    -> STALE
time authority uncertain            -> INDETERMINATE
```

`valid_until_utc_ms` is the checked minimum of the next relevant Calendar transition, still-future compatible Deadline
transition, materialization coverage end, analysis horizon end, policy maximum age, Dependency assurance / impact-cut
expiry, Task forecast boundary transition / expiry, and open-span DurationRemainingProjection validity. A Deadline
transition participates in this minimum only when `forecast_as_of_utc_ms < deadline_at_utc_ms`. Crossing it makes the
old projection stale; a projection recomputed at or after the boundary binds the current Deadline revision and
diagnostic inputs but never reuses that past instant as a new validity boundary. Every Dependency planning basis,
remaining-Duration input, Task forecast boundary, forecast-constraint owner partition, and planning Calendar resolution
field participates in the input fingerprint and stale decision.

`analysis_horizon_start_utc_ms = forecast_as_of_utc_ms` and the exclusive end is checked start plus the policy's
`time_critical_path_analysis_horizon_ms` (proposed as 365 days). Calendar expansion and every Task finish must fit
inside that horizon for COMPLETE coverage. Work extending beyond it is `PARTIAL` with
`CALENDAR_EXPANSION_INCOMPLETE`; Rust does not extrapolate a target finish.

Base Priority, Budget amount, permit identity, ordinary selection, and unrelated Goal / Task changes do not alter
longest-path geometry. They may affect real execution but do not enter this model.

Rust rechecks the input fingerprint before accepting a compute result. Input change during computation discards the
result or stores it as historical STALE only.

### 9.6 Deterministic algorithm

```text
1. Sample one trusted Rust status time.
2. Verify the route scenario covers every unsatisfied required criterion.
3. Reduce one exact current DependencyPlanningBasisSnapshot for the route and required dependency ancestry.
4. Reject self-edge, duplicate, cycle, missing Task, out-of-scope edge, or inconsistent planning basis.
5. Assign zero only to CONFIRMED_CURRENT_COMPLETION, CURRENT_COMPLETION_BOUNDARY, or
   PINNED_COMPLETION_BOUNDARY; never infer zero from Task DONE alone.
6. Include FUTURE_ACTIVITY_REQUIRED source current-lifecycle work in the DAG and read one exact CURRENT + AVAILABLE
   DurationRemainingProjection scenario and one exact matching TaskForecastBoundarySnapshot with a COMPLETE,
   mutually-exclusive owner partition for each active work node.
7. Stop aggregate finish production for CHALLENGED / INDETERMINATE assurance, and return ROUTE_UNAVAILABLE for an
   effective INVALIDATED required boundary without a current cut or replacement.
8. Verify every Task schedule shape is SINGLE_SERIAL_CALENDAR; otherwise mark the relevant result partial or unavailable.
9. Reject aggregate timing when the owner partition is incomplete, duplicated, kind-invalid, or basis-mismatched, when a
   Task release boundary is unavailable / indeterminate, or when the zero-Duration basis does not exactly align with the
   boundary snapshot; an active-work fragment may remain PARTIAL without TASK_DONE.
10. Resolve and record the complete current planning Calendar provenance for each Task.
11. Connect Tasks without predecessors to a virtual start.
12. `active_start_boundary = max(predecessor TASK_DONE finish, independently owned active-work release instant when
    present, horizon start)`. A `DELEGATED_TO_DEPENDENCY_GEOMETRY` release adds no second instant or edge.
13. For positive remaining Duration, move the boundary to the next allowed Task Calendar instant and derive
    `active_finish = Calendar.add_active_duration(active_start, selected Duration scenario)`; for zero remaining active
    Duration, active start and active finish both equal the unrepositioned boundary.
14. For `NO_ADDITIONAL_DELAY`, Task finish equals active finish and Duration-owned completion conditions remain covered
    by that active finish. For a known independently owned completion release, Task finish is the checked maximum of
    active finish and that release instant. Otherwise omit aggregate Task finish.
15. Represent only independently owned binding release or completion boundaries with `TASK_RELEASE_BOUNDARY` or
    `COMPLETION_RELEASE_BOUNDARY`, and Calendar movement with `CALENDAR_AVAILABILITY`; delegated Dependency waits remain
    represented only by `TASK_DEPENDENCY` edges.
16. Connect only Tasks with justified TASK_DONE finishes to virtual finish; target finish is their maximum only when
    the complete required network has justified finishes.
17. Trace every predecessor, release, completion, or Calendar constraint that determined a start / finish; retain all
    equal branches.
18. Emit the driving subgraph and bounded representative-path enumeration.
19. Derive valid_until and recheck the complete input fingerprint before persistence.
```

Different Task Calendars make a simple `total_float == 0` label easy to misstate. v0.1 therefore treats the canonical
output as the finish-driving subgraph. It does not claim authoritative total float or a unique path. Enumeration limits
must be explicit and `TRUNCATED` cannot be displayed as complete.

OPTIMISTIC, MOST_LIKELY, and PESSIMISTIC scenarios run separately. One path cannot mix scenario values, and the three
results are not probability bounds.

### 9.7 Missing evidence and failure semantics

Reason codes:

```text
ROUTE_SCENARIO_MISSING
ROUTE_SCENARIO_INCOMPLETE
PLAN_MEMBERSHIP_INCOMPLETE
REQUIRED_TASK_TERMINAL
DEPENDENCY_GRAPH_INVALID
DEPENDENCY_ASSURANCE_CHALLENGED
DEPENDENCY_ASSURANCE_INVALIDATED
DEPENDENCY_ASSURANCE_INDETERMINATE
DEPENDENCY_ASSURANCE_EXPIRED
DEPENDENCY_IMPACT_CUT_STALE
DEPENDENCY_PLANNING_BASIS_INCONSISTENT
FORECAST_CONSTRAINT_PARTITION_INCOMPLETE
FORECAST_CONSTRAINT_OWNER_CONFLICT
FORECAST_CONSTRAINT_BASIS_MISMATCH
DURATION_MISSING
DURATION_STALE
DURATION_INDETERMINATE
DURATION_RANGE_EXHAUSTED
CALENDAR_MISSING
CALENDAR_STALE
CALENDAR_EXPANSION_INCOMPLETE
PLANNING_CALENDAR_AMBIGUOUS
UNSUPPORTED_COMPOSITE_ACTIVITY
TASK_RELEASE_TIME_UNKNOWN
TASK_ACTIVE_WORK_RELEASE_INDETERMINATE
TASK_COMPLETION_RELEASE_UNKNOWN
TASK_COMPLETION_RELEASE_INDETERMINATE
ZERO_DURATION_BOUNDARY_MISMATCH
ACTIVE_DURATION_OBSERVATION_STALE
TIME_AUTHORITY_UNCERTAIN
INPUT_CHANGED_DURING_COMPUTE
ALGORITHM_UNAVAILABLE
PATH_ENUMERATION_TRUNCATED
```

`TASK_RELEASE_TIME_UNKNOWN` is the complete-evidence unavailable case for active-work release;
`TASK_ACTIVE_WORK_RELEASE_INDETERMINATE` is reserved for irreconcilable active-work release evidence.
`TASK_COMPLETION_RELEASE_UNKNOWN` and `TASK_COMPLETION_RELEASE_INDETERMINATE` make the same distinction after active
work. `ACTIVE_DURATION_OBSERVATION_STALE` is emitted when the bound remaining-Duration input exceeded its open-span
silence boundary; it cannot be downgraded to a generic missing Duration.

`FORECAST_CONSTRAINT_PARTITION_INCOMPLETE` means the reducer cannot establish the complete current hold/condition/wait
reference set. `FORECAST_CONSTRAINT_OWNER_CONFLICT` means a ref is missing from all owners, assigned more than once, or
assigned to an owner incompatible with its canonical kind. `FORECAST_CONSTRAINT_BASIS_MISMATCH` means a Dependency- or
Duration-owned ref does not match the exact current planning basis, Requirement / Validation scope, completion envelope,
or Duration fingerprint. Each produces `INDETERMINATE` with no aggregate Task or route finish; none may be downgraded to
a generic unknown release.

```text
confirmed unaffected fragment exists but aggregate finish is not justified -> PARTIAL, aggregate finish absent
effective required completion INVALIDATED with complete negative evidence -> ROUTE_UNAVAILABLE + COMPLETE
route / network / status origin cannot be established -> UNAVAILABLE
time, policy, or fact cannot be reconciled -> INDETERMINATE
cycle, illegal edge, overflow, or model-contract violation -> MODEL_INVALID
```

Only `CURRENT + AVAILABLE` may be presented as the current finish-driving subgraph. UI and reports must not call it a
unique critical path. `PARTIAL` never presents its known fragment as a complete network.

Deadline comparison requires exact completion semantics. A Task timing may compare to that Task's `TASK_DONE`
Deadline. `ROUTE_SCENARIO_WORK_COMPLETE` compared with a Goal `GOAL_CLOSED_ACHIEVED` Deadline is
`LOWER_BOUND_ONLY`: it has no margin and grants no urgency. Projected lateness remains diagnostic only and does not
generate `SoftCompletionTargetMissed`, DeadlineReached, Task blocker, or Goal Health reason.

### 9.8 Authority, recovery, and invariants

```text
Jenn / Nobao
  -> request a route-scenario analysis

Domain Agent / UI / external planner
  -> proposal or query only

Rust core
  -> sole currentness, input-fingerprint, algorithm, and persisted-projection acceptance authority
```

Recovery completes Task, Dependency, Deadline, UNKNOWN, Control Intent, and Event read barriers before rebuilding the
projection. Old projection never regains execution authority. Missing projection does not block Resident readiness or
ordinary safe work.

```text
Time Critical Path is not Critical Work Frontier
Time Critical Path does not select ANY_OF route
Time Critical Path does not change plan_progress or Goal closure
Time Critical Path does not change Priority, Task state, Dependency, Validation, Deadline, or Budget
Time Critical Path ignores Capacity, fairness, queue, and resource contention
Time Critical Path counts each current forecast constraint through exactly one owner geometry
Time Critical Path never duplicates a Dependency-owned wait or treats a Duration-owned condition as already satisfied
Time Critical Path creates no Run, permit, reservation, claim, or Outbox
```

v0.1 rejects:

```text
resource leveling, critical chain, and Capacity-aware path
Monte Carlo, criticality index, and completion probability
cross-Goal / shared-endpoint Dependency
FOLLOW_CURRENT / result Dependency
start-to-start, finish-to-finish, lead, or lag
automatic fastest ANY_OF route choice
arbitrary date-constraint injection
authoritative total float / free float / near-critical threshold
internal Task phase DAG
Goal closure prediction
```

## 10. Resource-constrained Scheduling v0.2 External Draft

The separately retained v0.2 design draft and its current validation cases are preserved in this independent file:

```text
control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md
```

That file is `PRESERVED_DESIGN_DRAFT_NOT_PROPOSED_FOR_ACCEPTANCE` with deferred known gaps. It is excluded from the
v0.1 acceptance subject; a review artifact
may hash it separately only to verify split integrity and non-acceptance boundaries. It grants no implementation or
execution authority and may evolve without changing the accepted meaning of v0.1. No v0.1 reducer,
registry consumer, or runtime may auto-import it merely because this reference exists. Its metadata records
`semantic_contract_reconstruction`: the pre-split draft had no retained byte-for-byte backup, so the independent file
was reconstructed from reviewed schemas and rules rather than falsely described as exact-byte preservation.

## 11. Cross-Contract Authority Matrix

| Fact class | Decision / reporter authority | Canonical writer | Boundary |
|---|---|---|---|
| Goal / Task lifecycle | Existing Jenn / Nobao contract | Rust core | Scheduling cannot direct-write it. |
| DurationEstimateRevision | Jenn or Nobao under authority mode | Rust core | Task-owned immutable input; Worker proposal only. |
| DurationTimingMeasurementPolicyRevision | Jenn | Rust core | Observation-silence parameters remain provisional and benchmark-required; no hidden default. |
| ActiveWorkSpan / DurationTimingFact | Rust-supervised timer or trusted host / Validator receipt | Rust core | Unique physical span counts once across Run and Validation; no automatic estimate update. |
| Duration assessment / outcome / calibration | Deterministic policy | Rust core derived projection | Read-only and rebuildable. |
| CalendarRevision / CalendarBindingRevision | Jenn or Nobao under authority mode | Rust core | Host and UI cannot define timezone truth. |
| CalendarBindingGateState | Deterministic Calendar/time reducer | Rust core | Current State + Event transaction; every outcome/time-policy transition advances generation. |
| PlanningCalendarResolutionSnapshot | Deterministic resolution policy | Rust core derived projection | Shared read-only provenance contract; no admission authority. |
| IANA tzdb bundle identity | Pinned implementation package | Rust core validates | OS tzdb does not silently replace it. |
| Calendar materialization / wake | Deterministic Calendar policy | Rust core | Timer only wakes; materialization does not gate by itself. |
| HostCapacityDomainRevision | Jenn/Nobao registration under allowlisted host-adapter attestation | Rust core | Stable physical accounting key; arbitrary host alias is rejected. |
| CapacityPoolRevision | Jenn or Nobao under authority mode | Rust core | One concrete host per pool in v0.1. |
| CapacityRequestSetRevision | Jenn / Nobao in Task or Requirement scope | Rust core | ALL_OF integer requests; no active-Run rewrite. |
| HostCapacityOffer | Corresponding authenticated host session | Rust core accepts | Offer is not claim or allocation. |
| Host local slot | Corresponding execution host | Host local gate | Ledger cannot fake external allocation. |
| HostCapacityAllocationReceipt | Corresponding authenticated host session | Rust core accepts | Complete claim-set fact only. |
| CapacityClaim / pool accounting | Deterministic admission / recovery policy | Rust core | UNKNOWN consumes full units. |
| SchedulingWorkRequestRevision | Jenn / Nobao authority or narrowly registered Rust derivation | Rust core | Immutable intent envelope; projection and host cannot originate it. |
| TaskSchedulingScopeAssignmentRevision | Registered Rust derivation; Jenn controls cross-key enforcement moves | Rust core | Caller cannot choose SHADOW/enforcement scope. |
| SchedulingEnforcementProfileRevision | Jenn | Rust core | Acceptance is not activation; exact scope/revisions only. |
| SchedulingPolicyRevision | Jenn | Rust core | Numeric mechanics are not numeric Task Priority. |
| TimeProjectionCurrentnessPolicyRevision | Jenn | Rust core | Visible max ages/horizon; no timer gains authority. |
| JennFocusDirective | Jenn | Rust core | Preference only, bounded by expiry. |
| TemporaryExpediteDirective | Jenn or scoped Nobao | Rust core | One admission or expiry; no permission. |
| Eligibility assessment / episode | Deterministic current-fact policy | Rust core | Does not set Task state. |
| DeadlineUrgencyAssessment | Deterministic exact-semantics forecast / current Soft-miss reduction | Rust core derived projection | Actual miss is Event-backed and non-time-bearing; Goal route-work lower bound grants no Goal Deadline urgency. |
| Fairness assignment / virtual service / backoff | Explicit epoch, assignment, successful-admission charge, and rejection Events | Rust core records Events and rebuilds reducer views | New or reactivated accounts inherit a current virtual-service floor; not Budget, quota, or Task WAITING. |
| TaskPrioritySelectionSnapshot | Deterministic selection policy | Rust core | Single canonical selection evidence; no authority. |
| AdmissionHandoffRecord | Deterministic Rust local reducer | Rust core | Durable idempotent local handoff only; not Run/Outbox/external authority. |
| RunAttemptsBudgetAuthorityBinding | Deterministic admission Budget authority derivation | Rust core | Immutable complete Task/Goal RUN_ATTEMPTS member set committed with the Run; recovery never infers it from surviving rows. |
| BudgetReservation | Existing Budget v0.1 policy | Rust core | Separate from CapacityClaim; RUN_ATTEMPTS members cross-bind the immutable authority binding. |
| Admission / commitment / Run / permit / Event / Outbox | Existing contracts plus accepted admission policy | Rust core | One local SQLite transaction. |
| HostWorkAcceptanceFact | Corresponding authenticated host proposes; Rust verifies | Rust core accepts | With Capacity, accepted atomically with complete ACQUIRED allocation receipt. |
| HostWorkStartDispositionFact | Corresponding authenticated current host proposes; Rust verifies | Rust core accepts | Exact epochs/commitment/dependency/fence; effectful attempt ID mandatory. |
| Actual process, session, and side effect | Corresponding execution host | Host reports; Rust accepts Fact | Outside SQLite transaction. |
| DependencyPlanningBasisSnapshot | Deterministic Dependency assurance reducer | Rust core embedded read snapshot | Binds assurance, fence, impact cut, and closure currentness; creates no Dependency or completion fact. |
| TaskForecastBoundarySnapshot | Deterministic Task condition/release reducer | Rust core embedded read snapshot | Partitions every current constraint exactly once across Dependency geometry, active Duration geometry, active-work release, or completion release; cannot wake or transition Task. |
| DurationRemainingProjection | Deterministic estimate/timing reducer | Rust core derived projection | Read-only remaining active-time input; does not complete Task. |
| SchedulePlanProjection | Deterministic rolling-plan policy | Rust core derived projection | Pure resource-unconstrained time forecast; no ordering, Capacity, or admission authority. |
| TimeCriticalPathProjection | Deterministic Rust algorithm | Rust core derived projection | Resource-unconstrained and route-scenario scoped. |
| ResourceScheduleProjection and v0.2 support records | Separate external v0.2 draft | Not active | Excluded from v0.1 acceptance; unavailable until separate acceptance and implementation. |

External planner, solver, VCPChat, VCPMobile, Workbench, ColaMeta, codex-router adapter, Domain Agent, Worker, and UI are
never direct writers of the above canonical ledger facts.

## 12. Recovery and Migration Compatibility

### 12.1 Acceptance is not activation

Jenn's future acceptance of this document would accept architecture semantics only. It would still not authorize
runtime source edits, SQLite migration, host registration, service startup, active config access, provider execution,
or real external work.

Future implementation must be staged:

```text
1. schema and reducer support plus explicit SHADOW baseline profiles, with all new enforcement disabled
2. read-only Duration / Calendar / Capacity fact intake and projection shadowing
3. host pool / offer / request preparation with no dispatch authority
4. shadow Eligibility and ordering comparison against existing behavior
5. crash / recovery and negative-path validation
6. Jenn-issued SchedulingEnforcementProfileRevision cutover for each exact selection scope
7. Jenn-issued profile cutover for each exact Calendar / Capacity scope and pool allowlist
8. ResourceSchedule v0.2 remains disabled until separately accepted
```

No feature enables itself merely because rows or projections exist.

### 12.2 Existing data

```text
Task without DurationEstimateRevision
  -> Duration UNAVAILABLE
  -> time projections PARTIAL / UNAVAILABLE
  -> otherwise legal execution remains possible

no NEW_START_AUTHORITY_ALLOWED Calendar binding
  -> Calendar imposes no admission restriction
  -> this is explicit absence of a constraint, not a hidden always-open Calendar row

declared Calendar binding with missing definition / tzdb
  -> INDETERMINATE and fail closed for new start-authority commitment

Task / Validation work without accepted CapacityRequestSetRevision after Capacity enforcement cutover
  -> new effectful admission denied
  -> no hidden one-slot default

historical TaskPrioritySelectionSnapshot without selection_schema_version
  -> historical evidence only
  -> cannot support new admission after selection-policy cutover

missing or ambiguous SchedulingEnforcementProfileRevision after capability cutover
  -> INDETERMINATE for that exact scope
  -> no implicit SHADOW or ENFORCING default
```

Capacity enforcement cannot cut over until every in-scope effectful work request has an explicit enforcement key and
request contract, and every allowlisted target pool has a current Calendar posture, capability profile, offer protocol,
fence, accounting recovery, and recovery test. One profile's cutover cannot activate or block a different profile.

### 12.3 Active work at cutover

Cutover is evaluated per exact profile scope and subsystem, not as one global switch:

```text
normal selection
  -> settle/supersede legacy OPEN selection and local scheduler handoff for that scope
  -> active accepted Runs do not by themselves block selection cutover

admission Calendar
  -> fence every not-yet-committed host start authority in scope
  -> already accepted Run retains its historical start authority

Capacity
  -> recover only the allowlisted accounting keys and every legacy occupancy that may consume them
  -> prove exact request/claim/allocation or quarantine the affected key
  -> no synthetic allocation and no requirement that unrelated pools be online

effectful Validation or new host acceptance/start protocol
  -> prefer quiescence
  -> otherwise migrate exact Task/Run/permit/host/epoch/commitment/dependency/Budget/effect facts
  -> missing proof becomes UNKNOWN for that work, not a global block
```

No active Run is silently assigned a synthetic allocation or declared stopped. “Grandfathered” means only that a
canonical pre-cutover acceptance keeps its already-earned start authority; it does not invent Capacity evidence.
Uncertain work blocks only every pool/accounting key or scope it may actually occupy.

### 12.4 Ordering and compatibility

New scheduling selections use `task-scheduling-selection.v0.1`. Rust keeps old selection Events immutable and adds no
backfilled claim of fairness, Calendar, Capacity, or Duration evidence.

Adapters may translate old Workbench, ColaMeta, or codex-router queue facts into proposals or read-only views. They may
not import queue status, lease, Priority, or scheduler state as canonical AGENTS OS Task / Run / Capacity truth.

Policy revisions are explicit and append-only. Unsupported policy prevents autonomous normal selection while keeping
Fact / Receipt, fence, UNKNOWN reconciliation, finalizer, and ledger recovery available.

### 12.5 Integrated recovery sequence

```text
1. validate SQLite schema, migrations, Event sequence, immutable rows, and current pointers
2. raise resident and local host fences; require new remote host sessions
3. recover Task / Run / Validation / Dependency completion assurance, impact cuts, Deadline, every immutable
   RunAttemptsBudgetAuthorityBinding and its cross-bound BudgetReservation set, and Budget authority; a missing or
   corrupt binding keeps the Task and affected scopes fail closed
4. recover Calendar definitions, bindings, tzdb identities, gate generations, and due wakes
5. recover Capacity pools, requests, offers, complete claim sets, host receipts, and accounting
6. classify every possibly dispatched or possibly accepted effect as UNKNOWN until reconciled
7. recover Control Intent, stop / fence, finalizer, and minimum control path
8. replay the exact service-epoch Event, all-zero epoch initialization, fairness assignments, semantic backlog
   episodes, selectable sets, starvation counters, and service-charge Events; reject episode/pass/counter/lineage/charge
   corruption or any old-epoch comparison; restore current handoffs and rebuild service / backoff reducer views
9. rebuild Duration assessment and cumulative ActiveWorkSpan frontiers
10. execute a recovery read barrier; repeat when relevant versions change
11. rebuild DurationRemainingProjection, exact TaskForecastBoundary owner partitions, pure SchedulePlan,
    TimeCriticalPath, and Deadline urgency in dependency order
12. accept fresh host offers and safely reopen current Outbox claims
13. reopen ordinary selection/admission independently for each recovered ENFORCING profile; leave other scopes quarantined
```

`ResourceScheduleProjection v0.2` is not rebuilt or treated as available until its separate contract acceptance and
implementation activation. One recovered profile never waits for an unrelated offline or quarantined profile.

Projection rebuild never creates Event, Task transition, Run, Validation attempt, permit, BudgetReservation,
CapacityClaim, Outbox, or external side effect.

### 12.6 Parent-decision synchronization after acceptance

If Jenn accepts the v0.1 contracts, the resident operating architecture must be amended consistently in:

```text
metadata / amendments and accepted scope
Section 6.4.2 Critical Work Frontier separation
Section 10.3 Task projection revision pointers
Section 10.5 create_run and effectful Validation binding
Section 10.10 deferred list
Section 10.11 RUN_ATTEMPTS settlement boundary
Section 10.12 Calendar versus Deadline and host acceptance
Section 10.13.8 selection schema compatibility
Section 10.13.12 effective ordering
Section 10.14 dependency gate read set
Section 11 Run host-acceptance semantics
Section 12 Validation attempt / Run binding
Section 14 Inbox / Outbox and dispatch recovery
Section 15.2 Rust responsibility
Section 17 startup / shutdown / durable wake recovery
Section 19 authority matrix
Section 22 remaining undecided items
Section 23 tests
Section 25 architecture snapshot
CURRENT_STATE.md and document registry
```

Resource-constrained Scheduling v0.2 remains in Section 22 even if Jenn accepts its design direction; its runtime and
contract status stay deferred until the listed prerequisites and a separate acceptance review are complete.

## 13. Required Test Matrix

### 13.1 Shared boundaries

- Reject every direct Task-state write from planner, scheduler, host, UI, Agent, or solver.
- Prove all new revisions are immutable, monotonic, idempotent, and CAS-protected.
- Prove same command ID and same payload returns the first result; different payload is a protocol conflict.
- Reject float, overflow, negative quantity, unknown enum, unsupported policy, and noncanonical fingerprint.
- Delete and rebuild every derived projection without Event, Run, permit, claim, Outbox, or state mutation.
- Reject secret, token, cookie, raw private memory, prompt, provider response, or raw log in any new fingerprint or Event.
- Prove schedule, Duration, Calendar, and Capacity revisions never change `plan_progress` or Goal closure.
- Prove missing scheduling evidence does not make a logically COMPLETE Critical Work Frontier incomplete.
- Prove rolling horizon never adds, removes, completes, or hides canonical Goal plan work.
- Prove route-decision-required work receives no global ordinal and planner never chooses ANY_OF route.
- Prove SchedulePlan earliest time never creates durable wake, not_before gate, Deadline, claim, selection, or Run.
- Prove a WAITING, PAUSED, or unresolved BLOCKED Task with `0/0/0` Duration and no deterministic current release
  boundary has no aggregate `TASK_DONE` finish; its known active-work fragment, if any, remains explicitly partial.
- Prove SchedulePlan start uses the checked maximum of predecessor finish and the exact active-work release boundary,
  and Task finish additionally waits for the exact completion-release boundary.
- Prove the forecast-geometry owner partition covers every current hold/condition component exactly once, binds the
  exact Dependency and Duration fingerprints, and becomes INDETERMINATE on omission, duplication, or ref mismatch.
- For `A -> B` where B waits only on the PRECOMMIT Dependency, forecast B from A's justified `TASK_DONE` finish without
  satisfying B's wake, changing B's Task state, or relabeling the Dependency wait as `RELEASED_NOW`.
- For Dependency wait plus an independent external hold, delegate only the Dependency component to Dependency geometry
  and withhold B's aggregate finish on the external hold; do not count either component twice.
- A required Validation or HUMAN_ACCEPTANCE active-work component already covered by remaining Duration must permit an
  exact `TASK_DONE` forecast when no independent completion release remains; an uncovered Requirement must fail closed.
- `ZERO_ACTIVE_WORK_PROVEN` must not assign a still-required active-work Requirement to Duration geometry, and recovery
  must reproduce the same complete owner partition and fingerprint independent of insertion order.
- Rebuild byte-identical Task forecast semantics with a different snapshot ID, Task aggregate CAS version, read Event
  sequence, computed time, or an unrelated Priority/Budget Event; the owner-partition, boundary, SchedulePlan, Time
  Critical Path, and Deadline-urgency semantic/input fingerprints must remain byte-identical and CURRENT.
- Change a relevant Task state/phase, source-current-pointer Event, constraint revision, owner assignment, Dependency or
  Duration basis, release outcome/instant, zero-basis alignment, or policy revision; the affected semantic fingerprint
  must change and every dependent analytical projection must become STALE.
- Prove projection refresh, Calendar wake, or passage of a projected release instant cannot satisfy a Task condition or
  create a Task transition.
- Prove stale SchedulePlan cannot delay or authorize current selection.
- Prove selection, backoff, admission, Run, permit, claim, Outbox, and host acceptance bind the same immutable work-request revision.
- Reject `RUST_POLICY` work-request creation without a registered derivation and existing Jenn / Nobao authority chain.
- SHADOW Calendar / Capacity / selection must produce diagnostics only and must not deny, claim, fence, or create admission-usable selection evidence.
- Only Jenn's explicit current enforcement-profile revision may enter ENFORCING; profile overlap, absence, or ambiguity must fail the exact scope closed after capability cutover.
- Profile change must fence unaccepted authority without preempting an accepted Run or blocking unrelated scopes.

### 13.2 Duration

- Missing estimate must remain UNAVAILABLE; zero, historical mean, or hidden default is forbidden.
- Reject `optimistic > most_likely`, `most_likely > pessimistic`, negative, float, and overflow.
- Accept `0/0/0` only with `ZERO_ACTIVE_WORK_PROVEN` and complete positive basis evidence; reject missing, unknown,
  unmeasured, or merely nonterminal work encoded as zero.
- Task spec, result, Validation scope, lifecycle generation, completion epoch, or work-position change must stale old Duration.
- Priority, Deadline, Budget, Dependency, Calendar, Capacity, or unrelated plan change alone must not stale intrinsic Duration.
- `observed_task_aggregate_version` must not enter the duration context fingerprint.
- Compatible cumulative PARTIAL timing must advance DurationRemainingProjection without staling the immutable estimate;
  semantic work-position or scope change must stale the estimate.
- For an open ActiveWorkSpan, require an exact measurement-policy revision, trusted observation anchor,
  `next_observation_due_utc_ms`, and matching exclusive `valid_until_utc_ms`.
- A compatible PARTIAL cumulative Fact must move the derived observation frontier and silence boundary without changing
  the immutable estimate; duplicate or rejected Facts must move neither.
- At or after the open-span silence boundary, DurationRemainingProjection must be STALE + UNAVAILABLE with
  `ACTIVE_OBSERVATION_STALE`; it must not extrapolate elapsed active work or invent a replacement estimate.
- With no open span, DurationRemainingProjection must be `NOT_TIME_BEARING` and must not invent a synthetic expiry.
- Reject a missing, nonpositive, overflowed, or unsupported observation-silence policy; concrete timing constants remain
  `PROVISIONAL_BENCHMARK_REQUIRED` until environment-bound evidence supports them.
- When observed delta exhausts the pessimistic estimate and zero remaining is not proven, derived remaining Duration
  must become UNAVAILABLE with `ESTIMATE_RANGE_EXHAUSTED`, never a schedulable `0/0/0`.
- Reject lower cumulative measurement, duplicate sequence with different payload, and incompatible coverage fingerprint.
- Count the latest compatible cumulative observation for each unique ActiveWorkSpan exactly once even when Run and Validation both reference it.
- Parallel or unprovably overlapping spans, counter-epoch ambiguity, and clock-session ambiguity must be INDETERMINATE.
- Different required Calendars, capacity profiles, or overlapping lanes must fail `SINGLE_SERIAL_CALENDAR` applicability.
- Incomplete observation coverage must remain PARTIAL and must not be extrapolated.
- Preserve actual time above pessimistic without truncation or outlier deletion.
- Worker, planner, UI, and host cannot move the current Duration pointer.
- Nobao cannot alter a `JENN_LOCKED` Duration.
- Duration revision cannot change Task state, active Run, permit, progress, or Goal closure.
- Timing Fact cannot complete Run / Validation / Task or settle `WALL_CLOCK_MS` Budget.
- Old-generation timing Fact remains history and cannot change current Duration.
- Hidden ML update or automatic current-estimate replacement must be rejected.

### 13.3 Calendar

- Reject unknown IANA tzid, mismatched tzdb digest, and client-supplied timezone rules.
- Reject noncanonical local date/time encoding, offsets/fractions, invalid Gregorian values, and overlong exception intervals.
- OS tzdb update must not change an old Calendar revision.
- DST gap must create no synthetic instant; fold must evaluate both real instants.
- Exclusion must win over inclusion; overlapping and adjacent UTC segments must normalize deterministically.
- Cross-midnight weekly windows must preserve `[start, end)` semantics.
- `now == open_from` must be OPEN and `now == open_until` CLOSED.
- Missing planning Calendar must make the forecast unavailable without blocking otherwise legal execution.
- Declared admission binding with unavailable tzdb or definition must fail closed.
- Multiple incompatible Goal or compatible-pool planning Calendars must produce ambiguity, not fastest-host selection.
- All SYSTEM, Goal, Task, and selected-pool admission bindings must intersect.
- OPEN at selection and CLOSED at admission must reject the old selection.
- Calendar revision after Run creation but before host acceptance must fence old start authority.
- Any one changed SYSTEM / Goal / Task / pool binding generation must invalidate the complete old Calendar fence vector.
- Entering/leaving INDETERMINATE, time-policy/session change, or occurrence-key change must advance Gate State and never revive an old permit.
- Canonical host start-authority commitment inside the window remains boundedly usable after ordinary Calendar close;
  it must not be rendered as actual STARTED until the separate disposition Fact is committed.
- Calendar close must not create Deadline miss, Task FAILED, or Goal BLOCKED.
- Materialization outside its horizon cannot guess OPEN.
- Duplicate wake cannot create duplicate Event, Run, permit, or selection.
- Missed wake must recover from `CalendarWakeRecord`; current evaluation may be OPEN or CLOSED and must not manufacture a historical Run.
- `projected_start_at` cannot become durable wake authority.
- Time authority uncertainty must prevent new admission without stopping an active Run.
- External calendar import cannot become canonical binding without an authorized command.

### 13.4 Capacity

- Budget available with no fresh Capacity offer must reject admission.
- Capacity available with Budget, Dependency, permit, Calendar, or P3 denial must reject admission.
- Planning and selection cannot decrement units or create claim.
- Two concurrent admissions for the last ordinary slot must permit exactly one local transaction.
- Offered units above pool ceiling must be capped.
- `offered_units` must be total AGENTS OS-offered units before ledger claims; accounting must subtract claims exactly once.
- Overlapping physical inventory across two enabled host capacity domains must be rejected; one domain cannot have two enabled current pools.
- Enforce one aggregate EXECUTION_SLOT domain per host and one physical unit per NAMED_EXCLUSIVE_SLOT domain.
- Historical/UNKNOWN claims must remain charged by stable host/accounting-key digest across domain revisions; occupied keys cannot retire/rebind.
- Reject stale offer, old session, old fence, incompatible capability, or disabled pool.
- Every offered unit must satisfy the full homogeneous pool capability profile; heterogeneous union counting is rejected.
- DRAINING pool cannot accept ordinary claim.
- `NAMED_EXCLUSIVE_SLOT` must remain ceiling one and cannot be shared.
- Every v0.1 Run claim set must resolve to one concrete host session.
- Any failed ALL_OF requirement must roll back the complete claim set and Run.
- Host must acquire the complete claim set atomically; partial receipt must become UNKNOWN unless no allocation is proven.
- ACQUIRED allocation receipt alone must not start Run or consume RUN_ATTEMPTS.
- Reject every allocation receipt tagged-union branch mismatch; REJECTED_NOT_ACQUIRED must contain no allocation handle/lease, and late RELEASED must remain legal after watchdog expiry.
- With Capacity enforced, allocation receipt and HostWorkAcceptanceFact must commit together before claims become ALLOCATED.
- Reject every v0.1 CapacityClaim whose owner is not a Run or whose request is not the exact Task work request.
- CONTROL_RECOVERY scheduling may not fabricate a CapacityClaim; the minimum control path remains Capacity-independent.
- Future Control Capacity Admission must remain disabled until its separate v0.2+ contract is accepted and activated.
- Claim proven never dispatched may EXPIRE; possibly dispatched claim must become UNKNOWN.
- UNKNOWN claim set must consume full units and cannot auto-release or retry.
- Duplicate allocation / release receipt must be idempotent.
- Claim and allocation renewal must use monotonic lease generations and Rust transaction time; expiry cannot silently release possibly allocated work.
- Claim renewal after possible dispatch and allocation renewal at/after expiry or watchdog fire must be rejected into reconciliation, never revive authority.
- Allocation renewal must retain the Run-bound historical lease-policy revision; later pool policy cannot silently change it.
- Old generation or host-fence receipt remains history without advancing current Run.
- Host rejection may release Capacity only with a complete REJECTED_NOT_ACQUIRED receipt proving never acquired or a complete RELEASED receipt; no-execution proof alone is insufficient.
- A prepared ACQUIRED allocation followed by gate rejection must stay RELEASING until a matching RELEASED receipt; no-execution proof alone cannot free units.
- CLAIMED may enter RELEASING only with complete ACQUIRED evidence, proven no execution, and an atomically created release finalizer.
- Offer expiry cannot release an ALLOCATED claim.
- Capacity reduction below active claims must produce OVERALLOCATED without preemption.
- Pool drain / disable cannot cancel an accepted Run.
- Time uncertainty cannot expire or release claim automatically.
- VCPMobile disconnect or new session must invalidate historical offers for new claims.
- Recovery must rebuild claim counts and fences before accepting fresh offer or admission.
- `ExpireUndispatchedClaimSet` must atomically close Run, permit, Outbox, claims, Budget reservations, Event, and Task reevaluation.
- Contradictory current-generation Fact after RELEASED / EXPIRED must quarantine units; it makes a nonterminal Run
  with unresolved execution outcome UNKNOWN, while a terminal Run stays terminal and uses the Section 8.6
  late-effect/assurance reconciliation path.
- One offline or legacy pool must not block cutover of an unrelated recovered pool/work-class scope.
- Capacity-accounting corruption must not block Fact / Receipt intake and pure ledger recovery.

### 13.5 Eligibility and ordering

- An ineligible Task cannot become eligible through Priority, focus, expedite, aging, deadline forecast, or fairness.
- Terminal, PAUSED, unresolved BLOCKED, active Control Intent, UNKNOWN, or nonterminal Run must be ineligible.
- WAITING can enter candidates only when its exact canonical wake condition is satisfied.
- VERIFYING rerun requires candidate disposition and all existing rerun guards.
- Priority `REVIEW_REQUIRED` must use NORMAL fallback without blocking eligibility.
- Missing Duration or advisory projection cannot deny otherwise legal eligibility.
- Soft Deadline miss and SOFT_TARGET Budget excess cannot act as a hard eligibility gate.
- Eligibility transition must create a rebuildable episode without changing Task state.
- Time uncertainty must freeze aging rather than invent elapsed eligible time.
- Aging can promote only to HIGH, never URGENT or FOCUS, and cannot modify base Priority.
- Only Jenn can create Focus; expired Focus must lose boost without changing Task.
- Nobao expedite must be in scope, expire, and be consumed after one successful admission.
- Focus and expedite cannot grant permission or preempt active Run.
- Task Deadline urgency requires a CURRENT exact `TASK_DONE` forecast; Goal route-work lower bound grants no Goal Deadline urgency.
- TIGHT urgency must compare MOST_LIKELY and PESSIMISTIC Calendar-aware finishes, not wall margin against active Duration.
- Forecast margin cannot become an actual Deadline Event or Goal Health reason.
- `ACTUAL_SOFT_MISS` urgency must bind the exact current `SoftCompletionTargetMissed` Event and current incomplete scope,
  remain non-time-bearing, and contain none of the FORECAST-only compatibility, finish, margin, or validity fields.
- Deadline revision / retirement, scope completion or lifecycle change, work-request supersession, or current-state
  fingerprint change must stale `ACTUAL_SOFT_MISS`; the immutable historical miss cannot keep current work urgent.
- At or after a Soft Deadline boundary, an expired FORECAST rank must not survive while the current miss Event is absent
  or indeterminate, and that gap receives no urgency promotion.
- Shared Task must charge one deterministic shared fairness account, not every Goal.
- Every current eligible execution/effectful-Validation work-request revision must have exactly one assignment; all
  sibling assignments must bind one lineage generation/account, while the complete sibling-set fingerprint remains in
  the service projection rather than forcing immutable unaffected assignments to be rewritten.
- A lineage with several sibling requests must contribute exactly one canonical head to exactly one effective band;
  request insertion order, duplicated requests, and request-specific expedite cannot place sibling shares in other
  active bands.
- Complete applicable Focus, expedite, and Deadline-urgency input sets must be insertion-order independent. Focus and
  expedite use exact OR aggregation; effective urgency uses the fixed ordinal and canonical driver tie-break. Missing or
  indeterminate set completeness grants no boost, and one successful admission consumes every effective matching
  expedite directive in the bound set exactly once.
- Active backoff on the canonical head must suppress the whole lineage without allowing sibling bypass and without
  closing/reopening its semantic backlog episode.
- Fact-driven or time-driven head/band changes must append one deterministic `SchedulingLineageHeadBandChanged` Event,
  bind the exact deterministic transition ID/idempotency key, reduce simultaneous cause codes without intermediate
  Events, migrate source/target backlog sets in the same transaction, and replay to the same head generation, episode
  refs, and fingerprints after restart.
- Head/band change and trigger flags must be mechanically derived, nonempty, deduplicated, and fixed-order. Test a
  comparator-only change with the same head/band/account, and a same-instant FACT + TIME + RECOVERY batch with several
  simultaneous before/after differences; retry must reproduce one byte-identical payload.
- A same-boundary two-way band/account swap, three-lineage cycle, many-to-one, and one-to-many migration must reduce
  backlog episodes only from complete batch endpoints. No per-lineage intermediate state may fabricate EMPTY,
  close/reopen an episode, or reset age; recovery and insertion-order permutations must reproduce the same anchors.
- A delayed wake across multiple aging/expiry boundaries must catch up in canonical boundary order before selection or
  admission; time uncertainty, a missing boundary input, or an unmaterialized due transition must close normal
  selection rather than preserve the stale band.
- Selection validity must include the earliest head/band and selectable-set transition across the complete semantic
  lineage set; a nonselected lineage becoming more urgent or leaving backoff before admission must supersede the old
  selection.
- First lineage assignment must use the target account effective pass; eligibility restart must preserve the greater
  prior/target floor; re-key must preserve the greater prior/source/target floor; successful charge must advance the
  selected lineage floor through `account_pass_after`. Any floor decrease or zero reset in one service epoch must fail
  normal selection closed.
- Assignment transition flags must cover revision-only, revision + restart, revision + re-key, and sibling-add + re-key
  combinations. Same-account continuous revision preserves the floor byte-for-byte; every compound transition takes
  the checked maximum of all applicable lower bounds and replays independently of trigger order.
- Admission of one head must atomically charge once, advance its lineage floor once, remove all sibling assignments
  from current semantic eligibility, and leave no sibling selectable for a second Run.
- New, reactivated, or re-keyed fairness accounts must inherit at least the exact target/system and applicable lineage
  virtual-service floors and must not gain a zero-based catch-up burst.
- First service epoch must use `INITIAL_BOOTSTRAP`; every later epoch must bind the exact prior monotonic generation,
  Jenn authorization, allowed reason, current eligible-lineage fingerprint, and
  `RESET_ALL_WITHIN_NEW_EPOCH_TO_ZERO` initialization.
- A service-epoch transition must reset every band/account/entity pass and both starvation counters together, never
  compare old-epoch pass, and keep normal selection closed until assignment and backlog rederivation is CURRENT.
- Unrelated backoff/TTL/policy revision must not start a service epoch or reset pass, counters, or backlog age.
- Semantic backlog EMPTY -> NONEMPTY must open one deterministic account episode; while nonempty it must preserve its
  first Event sequence across work-request revision, another lineage's eligibility restart, and temporary backoff.
- Semantic backlog NONEMPTY -> EMPTY must close the episode; a later true restart must use the next generation and a
  new start Event sequence.
- Assignment re-key/merge/split must atomically preserve a nonempty target episode, open an empty target at the
  assignment Event, and close a source only when no lineage remains.
- Backoff must change only the selectable-set fingerprint; it cannot close or reopen the semantic backlog episode or
  cause a non-head sibling to become a separate share.
- Recovery must rederive the same per-request assignment uniqueness, lineage floors, canonical heads/bands, backlog
  episode IDs, generations, start sequences, refs, and fingerprints independent of insertion order; any partial
  sibling re-key, multiple-band lineage, discontinuity, or selectable account without an open episode must fail normal
  selection closed.
- Band and account selection must use checked canonical `u128` pass arithmetic with deterministic tie-breaks; float,
  signed coercion, overflow, pass decrease, duplicate charge, or broken lineage must fail normal selection closed.
- Successful local admission must atomically commit exactly one SchedulingServiceCharge and matching pass updates;
  technical rollback commits neither, and later host rejection cannot reverse the charge.
- `BACKGROUND_FORCED` has precedence and must select BACKGROUND at the configured non-background streak when one is
  selectable; otherwise `NON_FOCUS_OR_URGENT_FORCED` must select a nonfocus/nonurgent band at its configured streak.
- A successful admission must update the exact bounded starvation counters once; rejection, rollback, host rejection,
  backoff, and projection rebuild must not update them.
- Stable comparator must produce the same selection across restart and insertion-order variation.
- v0.1 must reject max_open_normal_selections_global other than 1 and must finalize/supersede the current handoff before selecting again.
- Every urgency, frontier, and service-band enum ordinal and raw identity byte direction must match the frozen tuple contract.
- Active backoff must suppress the exact work-request revision before selection and must be embedded in selection evidence.
- Rebuild or deletion of Eligibility projection must not erase the immutable selection's normalized observed facts.
- Selection cannot create BudgetReservation, CapacityClaim, permit, Run, or Outbox.
- One selection may have one business outcome; technical rollback must not consume it.
- Enforce at most one OPEN selection globally, per Task lifecycle, and per work-request revision; recovery replays only its same deterministic handoff command.
- Historical unversioned selection cannot support new admission after cutover.
- Rejected selection must not consume successful-admission fairness service.
- Unsupported scheduling policy must stop autonomous normal selection but leave control / recovery available.

### 13.6 Admission and recovery

- `create_run` must recheck every current Task, Dependency, Deadline, Budget, Calendar, Capacity, authorization, and host fact.
- Current fact change after selection must reject stale admission even when projection still says eligible.
- Successful local admission must atomically resolve the exact phase-correct commitment, allocating it when required
  or reusing the immutable snapshot unchanged, and create reservations, complete claim set, Run, Event, permit, and
  Outbox. A newly allocated commitment participates in that transaction; a reused commitment receives no write.
- Successful local admission must also create exactly one immutable `RunAttemptsBudgetAuthorityBinding` containing the
  complete sorted Task/Goal RUN_ATTEMPTS member set; it must reference the exact reusable commitment snapshot, while
  its ID and fingerprints match every bound reservation, Run, permit, admission Event, and Outbox or the whole
  transaction rolls back. The immutable commitment snapshot must not acquire a Run-specific reverse binding.
- Business rejection must create none of those partial records.
- SQLite / CAS rollback must not consume selection and must be idempotently retryable.
- In an ENFORCING selection scope, normal autonomous admission without one OPEN current selection must be rejected.
- Admission at/after selection_valid_until or with a stale handoff claim generation must supersede the handoff and reselect.
- In SHADOW, legacy admission must never consume the new diagnostic comparison; cutover must atomically disable legacy before enabling AdmitSelectedWork.
- Jenn direct execution must still produce Rust selection evidence and cannot direct-write Run.
- Before separate Validation admission acceptance, effectful Validation without a `create_run` Run must be rejected.
- Effectful Validation admission must preserve the candidate and bind a QUEUED Run without prematurely creating an attempt.
- HostWorkAccepted must atomically create the bound Validation attempt PENDING; StartDisposition STARTED advances it to RUNNING; rejection before acceptance creates no attempt.
- StartDisposition REJECTED must require no-execution proof and atomically close the LEASED Run and PENDING
  Validation, release evidence-backed RUN_ATTEMPTS and definitely unused Budget, and start the independent Capacity
  finalizer. Without a complete current `REJECTED_NOT_ACQUIRED` or `RELEASED` receipt, Capacity must remain
  `RELEASING` or `UNKNOWN` at full occupancy rather than being atomically closed by no-execution proof.
- Fact replay must resolve the Run-reserved stable Validation attempt ID and cannot create a second attempt.
- Effectful Run FAILED/TIMED_OUT must make Validation ERROR, CANCELLED must make it CANCELLED, and UNKNOWN must make an existing Validation INCONCLUSIVE and forbid retry.
- Run SUCCEEDED cannot make Validation PASSED.
- Outbox ACK cannot become HostWorkAccepted.
- Host acceptance must match Run, permit, claim set, Calendar, Deadline, session, and fence.
- With Capacity enforced, HostWorkAcceptanceFact and the exact complete ACQUIRED allocation receipt must be accepted in one transaction.
- Reject every Host acceptance/start tagged-union branch mismatch, including ACCEPTED+no-execution and STARTED+release.
- STARTED under Capacity must bind ALLOCATION_CONTINUES and commit before min(start grace, allocation expiry); LEASED allocation renewal is forbidden.
- Host rejection before possible execution may produce Run REJECTED, but claims release only with complete never-acquired or released allocation evidence.
- Post-acceptance no-launch proof must release every bound RESERVED RUN_ATTEMPTS reservation even when Capacity remains
  RELEASING pending its independent release receipt.
- Host acceptance or possible side effect ambiguity must produce UNKNOWN and retain full reservations / units.
- `RUN_ATTEMPTS` settlement starts only at canonical STARTED or stronger positive execution evidence, not
  HostWorkAccepted, Outbox ACK, allocation, or a definitely unexecuted rejected Run.
- StartDisposition uncertainty must move every unsettled bound RUN_ATTEMPTS reservation to UNKNOWN; later authoritative
  positive or no-execution evidence may reconcile the complete set exactly once to SETTLED or RELEASED.
- Authenticated same-execution-epoch positive execution evidence after RUN_ATTEMPTS was RELEASED must append
  `RunAttemptsReleaseContradictedByPositiveExecution`, atomically compensate the complete canonical set of Task and all
  applicable Goal reservations RELEASED -> SETTLED, add one consumed unit to each bound envelope exactly once,
  contradict the prior no-execution assurance, and keep the old Run terminal REJECTED.
- Test Task-only, Task + one Goal, and Task + multiple Goal RUN_ATTEMPTS correction sets under shuffled input, duplicate
  Facts, crash replay, and resulting over-cap. A missing or conflicting set member must allow the real positive Fact to
  remain evidence but must perform no partial Budget correction, mark accounting INDETERMINATE, and close every affected
  Budget scope to new admission.
- Delete or corrupt one reservation row while retaining the original authority binding; recovery and late-positive
  correction must detect the exact missing member, compensate nothing, and fail closed every scope in the immutable
  expected set plus any observed conflicting scope.
- Delete, duplicate, or corrupt the authority binding itself while retaining different subsets of Run,
  permit, Event, Outbox, and reservation cross-references; no surviving-row scan may self-certify a complete set,
  compensation remains all-or-nothing, the Task stays fenced, and every independently reconstructable affected scope
  stays closed until explicit repair.
- Crash and replay before/after authority-binding commit, contradiction commit, and correction resolution must preserve
  one binding identity, one exact expected-set fingerprint, one correction fingerprint, and at most one consumed unit
  per applicable envelope.
- Late-positive correction must atomically raise the no-new-Run fence and scan every later execution epoch plus current
  candidate, result, and Validation completion binding before committing.
- With no successor, late STARTED must open bounded `activity_kind=COORDINATING` activity with
  `coordination_subtype=LATE_EFFECT_RECONCILIATION`, reconciliation ID, owner, next action, and activity deadline;
  stop/query the historical execution, forbid a new Run, and move a nonterminal Task to unresolved-effect BLOCKED only
  after no physical execution may remain. This narrow ACTIVE branch must not override current Run UNKNOWN -> Task
  BLOCKED.
- A later QUEUED successor must be fenced before dispatch; it may become REJECTED only with proof it never left the
  ledger, otherwise it follows UNKNOWN reconciliation without reopening the old Run.
- A later LEASED, RUNNING, or WAITING successor must remain the only nonterminal execution Run, receive immediate
  fence/PAUSE/stop/query/reconciliation, and keep Task ACTIVE until its physical execution is known terminal.
- A later terminal successor and every associated candidate, result, evidence, and Validation completion decision must
  remain immutable but quarantined until overlap and late-effect influence are resolved.
- A late authenticated terminal execution Fact must use the same Budget correction and successor scan but must not
  fabricate an active old Run; unresolved effect influence still blocks candidate/Validation/Task completion.
- If the Task was already DONE, FAILED, or CANCELLED, late-positive correction must preserve that terminal state, must
  not automatically reopen it, and must challenge affected completion assurance and Goal/dependency support until the
  ordinary reconciliation and explicit reopen rules permit a later decision.
- Duplicate late-positive evidence or crash replay must not add a second consumed unit in any envelope, reconciliation, fence
  generation, stop intent, successor disposition, or state transition. Obsolete or mismatched evidence must not mutate
  Budget, and later no-execution evidence must not release a compensating SETTLED attempt.
- A later stronger positive Fact for the same execution epoch must enrich the existing reconciliation without creating a
  second contradiction Event or Budget compensation for the same complete released reservation set.
- Every late-positive branch must preserve at most one nonterminal execution Run, create no Run, authorize no automatic
  retry, and restore the same Task activity/blocking projection after recovery.
- STARTED must commit before nonrenewable start grace with trusted time; grace expiry proof/uncertainty must follow the exact REJECTED/UNKNOWN branches.
- Host timestamp cannot retroactively prove start before Calendar or Deadline boundary.
- Business rejection must persist the complete fixed-order rejection-reason set and fingerprint. Backoff identity uses
  the exact eligible subset, not check order or a caller-selected reason; technical rollback creates no backoff.
- Simultaneous Calendar + Capacity + Deadline failures, reversed evaluation order, duplicate reasons, and one reason
  clearing while another remains must produce the specified deterministic rejection/backoff result.
- Backoff must be checked-integer, bounded, reason-set-specific, and cleared only by a relevant bound fact revision.
- Backoff cannot set Task WAITING or authorize retry.
- SOFT_TARGET as well as HARD_CAP Budget dimensions must receive reservations; only HARD_CAP shortage may reject.
- Crash before commit must leave no admission; crash after commit before claim must leave recoverable QUEUED work.
- Possible send without Fact must become UNKNOWN; no automatic redispatch.
- Terminal receipt settlement must be idempotent across a settlement crash.
- Task completion racing admission must allow exactly one CAS result.
- Recovery must supersede old OPEN selections and never revive old permit.
- Normal admission must remain closed until control path and read barrier are operational.
- Recovery projection rebuild must produce no external or canonical execution side effect.

### 13.7 Time Critical Path

- Duration or Calendar missing must prevent a CURRENT AVAILABLE path.
- Missing route scenario or an uncovered required criterion must not trigger fastest-route auto-selection.
- Dependency cycle, self-edge, duplicate, missing Task, or overflow must be MODEL_INVALID.
- Projection read must never create PinnedDoneBinding or Dependency edge.
- Task DONE alone must never imply zero: only confirmed current completion or an effective confirmed current/pinned
  completion boundary may contribute zero remaining Duration.
- Every current-lifecycle node must bind the exact TaskForecastBoundarySnapshot; state, condition, release instant,
  zero-basis alignment, or boundary fingerprint change must stale the projection.
- `ZERO_ACTIVE_WORK_PROVEN` must require an exact set match between the estimate's pending/excluded refs and the Task
  forecast boundary; mismatch or indeterminate alignment must omit aggregate `TASK_DONE` finish.
- Unknown/indeterminate active-work release must omit start, active finish, and Task finish. Unknown/indeterminate
  completion release may retain a diagnostic active finish but must omit Task finish and route aggregate finish.
- A deterministic known release must enter the driving subgraph with `TASK_RELEASE_BOUNDARY` or
  `COMPLETION_RELEASE_BOUNDARY`; zero active Duration must not be moved to a later Calendar instant.
- Assurance-only version, fence, impact-cut, closure-fingerprint, or expiry changes must stale the projection even when
  Task state and DependencySpecRevision did not change.
- POSTCOMMIT PRESERVED with a current confirmed historical ref may retain its pinned zero boundary; PRECOMMIT may not
  bind that reopened historical ref.
- CHALLENGED assurance cannot produce an AVAILABLE aggregate finish; effective INVALIDATED required completion without
  a current cut/replacement must produce ROUTE_UNAVAILABLE rather than Goal BLOCKED.
- Required FAILED / CANCELLED Task without replacement must make time analysis unavailable.
- Parallel equal driving branches must all remain in the driving subgraph.
- Truncated representative-path enumeration must say TRUNCATED.
- Priority, Budget, fairness, queue, and Capacity must not enter path weight.
- Projected Deadline overrun must not create DeadlineReached, Soft miss, blocker, or Goal Health reason.
- `plan_progress = 100%` must not predict Goal closure.
- Time-path absence cannot alter Critical Work Frontier completeness.
- Input change during compute cannot produce CURRENT projection.
- Time authority uncertainty cannot invent status origin.
- Time projection must remain current only before its deterministic `valid_until`; a still-future Calendar or Deadline
  transition must stale the old projection at its boundary without a new domain Event.
- TimeCriticalPath recomputed at or after a Deadline boundary must not reuse that past instant as `valid_until`; only a
  strictly future applicable Deadline transition may bound the new projection.
- Time projection validity must not outlive any bound Task release transition/expiry or open-span remaining-Duration
  observation boundary.
- Capacity request, compatible-pool set, pool binding, tzdb, or Calendar materialization change must stale old Calendar resolution.
- Goal Deadline comparison against route-work completion must be LOWER_BOUND_ONLY with no margin or urgency.
- FORECAST Deadline urgency validity must not outlive any source forecast, still-future Deadline transition, or
  currentness-policy max age; ACTUAL_SOFT_MISS must instead use Event-backed non-time-bearing currentness.
- Standalone Task Deadline must have a Task-local `TASK_DONE` forecast path.
- UI must call the canonical result a finish-driving subgraph, not a unique critical path.
- OPTIMISTIC / MOST_LIKELY / PESSIMISTIC paths cannot mix values.
- Recovery rebuild cannot create Event, Run, permit, claim, or Outbox.

### 13.8 Resource-constrained v0.2 external draft

The v0.2-only validation cases moved with the design to
`control-plane/registry/drafts/2026-07-13-agents-os-resource-constrained-scheduling-v0.2.draft.md`. They are not v0.1
acceptance tests and cannot authorize implementation.

### 13.9 Cross-contract races

- Registry and acceptance-state validation must reject every partial freeze of this revision: Sections 3-9 and the
  parent Section 2.1 R1 overlay become accepted together or remain non-authoritative together. Resource Scheduling v0.2
  remains outside that atomic bundle.
- Calendar close and Capacity claim race must be resolved by one Rust writer with no claim surviving failed admission.
- Budget and Capacity last-unit races must be all-or-nothing across every applicable envelope and pool.
- Duration revision during time-path compute must stale or discard the result without affecting active Run.
- Capacity offer expiry between selection and admission must reject the old selection basis.
- Pool revision after local admission but before host acceptance must obey the bound fence and UNKNOWN rules.
- Deadline stop must remain executable even when ordinary Capacity is saturated.
- Fact / Receipt acceptance and UNKNOWN reconciliation must not be blocked by normal eligibility or fairness.
- Schedule policy revision must not rewrite old selection or active Run.
- Restore from backup must not treat stale materialization, offer, selection, or projection as current authority.
- Repeated full recovery must not duplicate revision, Event, wake, claim, Run, permit, or Outbox.

## 14. Jenn Final Review Surface

### 14.1 Proposed disposition

The acceptance decision is atomic for this revision:

```text
R1_V0_1_ATOMIC_ACCEPTANCE_BUNDLE
  = Sections 3-9 below
  + the parent architecture Section 2.1 pending R1 amendment overlay
```

The rows remain separate review surfaces, but none is independently freezable under this revision. A required change
to any row returns the whole bundle to amendment; it never creates a partially authoritative combination.

| Contract | Proposed bundle disposition |
|---|---|
| Scheduling Work Request and Enforcement Profile v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| SchedulePlanProjection v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| Duration Estimate v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| Calendar v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| Capacity v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| Eligibility and Effective Ordering v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE`; constants still require Jenn review |
| Atomic Admission and Recovery v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| Time Critical Path v0.1 | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| Parent architecture Section 2.1 R1 overlay | `MEMBER_OF_ATOMIC_ACCEPTANCE_BUNDLE` |
| Resource-constrained Scheduling v0.2 | `RETAIN_AS_PRESERVED_DESIGN_DRAFT_NOT_PROPOSED_FOR_ACCEPTANCE` |

### 14.2 Decisions with the highest behavioral impact

Jenn's review should focus first on these choices:

```text
1. Duration means remaining active completion time, not wall-clock time to DONE.
2. Duration uses explicit optimistic / most-likely / pessimistic scenarios and no hidden expected value.
3. Calendar v0.1 supports weekly windows and explicit exceptions, not recurring Task creation.
4. DST gaps create no synthetic instant; folds match both real instants.
5. Admission Calendars intersect SYSTEM + Goal + Task + selected Capacity-pool constraints.
6. Calendar close prevents a new start-authority commitment but does not revoke an already committed bounded
   authority or stop an already STARTED Run.
7. Capacity v0.1 uses integer slots, stable physical accounting keys, one concrete host per pool, and one host per Run claim set.
8. UNKNOWN Capacity consumes full units and cannot auto-release.
9. v0.1 creates CapacityClaims only for Runs; Control Capacity Admission is deferred and the minimum control path is Capacity-independent.
10. Scheduling uses weighted service bands plus explicit starvation guards, not strict Priority starvation.
11. Jenn focus is preferred, time-bounded, and never a hard exclusion.
12. Nobao expedite is scoped and lasts for one successful admission or a bounded TTL.
13. Selection is single-use evidence; only current synchronous admission creates Run authority.
14. Effectful Validation binds a Run and cannot bypass Budget / Capacity / permit / recovery.
15. HostWorkAccepted, not Outbox ACK or host timestamp, establishes bounded Calendar/Deadline start authority while
    RUN_ATTEMPTS remains RESERVED.
16. Actual STARTED or stronger positive execution evidence settles RUN_ATTEMPTS; authoritative no-launch proof releases
    it, while possible execution makes it UNKNOWN. Late positive evidence after release creates the exact compensating
    settlement/incident Event, quarantines the contradiction, and never authorizes retry.
17. Time Critical Path v0.1 is a resource-unconstrained finish-driving subgraph, not Critical Work Frontier.
18. v0.1 does not claim authoritative total float or automatically choose the fastest Goal route.
19. Resource-constrained solver output remains a separately deferred v0.2 draft with no execution authority.
20. SchedulePlan v0.1 is a bounded pure resource-unconstrained time forecast; ordering, admission status, and Capacity
    observation remain separate surfaces.
21. SHADOW, ENFORCING, and runtime cutover are explicit per-scope facts; accepting this document activates nothing.
```

### 14.3 Scheduling parameter status for v0.1

```yaml
rolling_horizon_ms: 604800000
service_band_weights:
  FOCUS: 16
  URGENT: 12
  HIGH: 8
  NORMAL: 4
  LOW: 2
  BACKGROUND: 1
aging_quantum_ms: 1800000
max_aging_promotions: 2
max_consecutive_focus_or_urgent: 6
max_consecutive_non_background: 16
focus_max_ttl_ms: 86400000
expedite_max_ttl_ms: 14400000
expedite_max_successful_admissions: 1
selection_backoff_base_ms: 1000
selection_backoff_max_ms: 60000
selection_handoff_ttl_ms: 5000
local_handoff_claim_lease_ms: 1000
host_start_grace_ms: 10000
max_open_normal_selections_global: 1
schedule_plan_max_age_ms: 60000
time_critical_path_max_age_ms: 60000
deadline_urgency_max_age_ms: 60000
time_critical_path_analysis_horizon_ms: 31536000000
capacity_max_offer_ttl_ms: PER_POOL_REVISION_CANDIDATE
capacity_claim_lease_ms: PER_POOL_REVISION_CANDIDATE
capacity_allocation_lease_ms: PER_POOL_REVISION_CANDIDATE

parameter_value_classes:
  JENN_POLICY:
    - rolling_horizon_ms
    - service_band_weights
    - aging_quantum_ms
    - max_aging_promotions
    - max_consecutive_focus_or_urgent
    - max_consecutive_non_background
    - focus_max_ttl_ms
    - expedite_max_ttl_ms
    - expedite_max_successful_admissions
    - max_open_normal_selections_global
    - schedule_plan_max_age_ms
    - time_critical_path_max_age_ms
    - deadline_urgency_max_age_ms
    - time_critical_path_analysis_horizon_ms
  PROVISIONAL_BENCHMARK_REQUIRED:
    - selection_backoff_base_ms
    - selection_backoff_max_ms
    - selection_handoff_ttl_ms
    - local_handoff_claim_lease_ms
    - host_start_grace_ms
    - capacity_max_offer_ttl_ms
    - capacity_claim_lease_ms
    - capacity_allocation_lease_ms
```

The listed numbers are visible candidate values, not one undifferentiated set of frozen engineering facts.
`JENN_POLICY` values are explicit product/currentness choices. Every `PROVISIONAL_BENCHMARK_REQUIRED` value remains
activation-blocked until a measured-environment fingerprint, benchmark protocol, result ArtifactRef, and Jenn-accepted
policy or pool revision bind it. Schema acceptance alone cannot promote a provisional value or let implementation
invent an alternative.

### 14.4 Recommended final review result

The independent R1 review may recommend the following disposition, but only Jenn can freeze it:

```yaml
v0_1_contracts:
  package_status: PENDING_JENN_FREEZE_DECISION
  review_target: READY_FOR_JENN_FREEZE_DECISION

v0_2_contracts:
  ResourceConstrainedScheduling:
    design_direction: PRESERVED_DRAFT_WITH_DEFERRED_KNOWN_GAPS
    contract_status: PRESERVED_DESIGN_DRAFT_NOT_PROPOSED_FOR_ACCEPTANCE
    implementation_status: NOT_AUTHORIZED

parent_boundary: PRESERVED
runtime_or_database_implementation_authority: NOT_GRANTED
```

### 14.5 What acceptance still would not authorize

Even an unqualified architecture acceptance would not authorize:

```text
editing VCPToolBox / VCPChat / VCPMobile runtime source
creating or migrating the real SQLite ledger
starting a service or activating a plugin
reading active runtime config, secret, token, cookie, credential, or private raw memory
calling a provider, executor, external Codex CLI, or real host
creating a production Calendar or importing private calendar data
registering real host Capacity offers
dispatching a Run or Validation
enabling solver or admission enforcement
deploying, releasing, pushing, merging, tagging, or publishing
```
