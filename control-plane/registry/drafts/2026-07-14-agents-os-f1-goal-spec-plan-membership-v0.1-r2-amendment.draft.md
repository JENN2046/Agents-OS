# AGENTS OS F1 Goal Specification / Plan Membership v0.1 R2 Amendment

```yaml
document_type: blocking_amendment
acceptance_unit_id: F1_GOAL_SPECIFICATION_SUCCESS_CRITERIA_PLAN_MEMBERSHIP_V0_1_R2_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r2
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
```

## 1. Amendment scope and precedence

This amendment resolves the findings in the fixed R1 independent review. It
does not edit or erase the R1 subject or review artifact.

```yaml
R1_subject:
  path: control-plane/registry/drafts/2026-07-14-agents-os-goal-specification-success-criteria-plan-membership-v0.1.draft.md
  sha256: 08dcc4cd2c6662e1f408cecb4f51107e50ad15e236b2ec965b898619324aecb8
R1_independent_review:
  path: control-plane/registry/reviews/2026-07-14-yellow-agents-os-f1-goal-spec-plan-membership-v0.1-independent-review.yaml
  sha256: b5ce737eeec248063be4b6eb15d56676dbfa2ee7aebfe28f20efbf6a473c8df8
  result: BLOCK
```

The composed R2 contract is:

```text
R1 exact subject
+ this exact amendment
```

Where this amendment names a replacement rule, it replaces the corresponding
R1 clause. All other R1 clauses remain in force. Neither file is accepted until
Jenn accepts the exact atomic bundle after a new independent review.

Replace the first sentence of R1 Section 1 with:

```text
This document proposes the contract for the first Phase 4 foundation contract
unit. F1 closes only through a separate exact hash-bound Jenn acceptance
decision.
```

## 2. Total SuccessCriterionDecision reducer

This section replaces the under-specified reduction and currentness rules in R1
Sections 7.3, 7.4, 13.1, 13.2, and 15 wherever they conflict.

### 2.1 Reducer identity and input

```yaml
SuccessCriterionDecisionReducer:
  reducer_contract_version: success-criterion-decision-reducer.v0.1
  event_order: ascending_global_event_sequence
  same_event_sequence_for_distinct_events: invalid_ledger_state
  output:
    assessment: SATISFIED | UNSATISFIED | INDETERMINATE
    current_decision_event_id: null | event_id
    current_decision_fingerprint: null | FingerprintEnvelope
    evidence_currentness_fingerprint: null | FingerprintEnvelope
    reason_codes: []
    based_on_event_sequence:
```

The reducer consumes the complete immutable Event set for the exact tuple:

```text
goal_id
goal_spec_revision
criterion_id
criterion_revision
```

It never scans natural-language Memory, UI state, cached projections, or later
criterion revisions to guess a decision.

### 2.2 Decision operations

Every decision Event contains:

```yaml
SuccessCriterionDecisionEventValue:
  operation: DECIDE | SUPERSEDE | REVOKE | CARRY_FORWARD
  goal_id:
  goal_spec_revision:
  criterion_id:
  criterion_revision:
  decision: SATISFIED | UNSATISFIED | INDETERMINATE
  prior_decision_event_id: null | event_id
  authority_mode: JENN | NOBAO | RUST_POLICY
  actor_or_policy_ref:
  authority_basis_ref:
  evidence_currentness_snapshot:
  source_decision_event_id: optional
  event_id:
  event_sequence:
```

Rules:

```text
The first valid event uses DECIDE with prior_decision_event_id = null, or uses
  CARRY_FORWARD with prior_decision_event_id = null and a valid
  source_decision_event_id from the immediately preceding revision tuple.
Every later operation must name the one current head as prior_decision_event_id.
SUPERSEDE installs its supplied decision as the new head.
REVOKE installs an INDETERMINATE head; it never falls back to an older decision.
CARRY_FORWARD is valid only under Section 2.5 and installs a new head for the
  new exact revision tuple.
DECIDE after a current head exists is rejected; use SUPERSEDE.
An event that branches from a non-head, skips a head, repeats event_id, uses an
  invalid authority, or conflicts at one event sequence makes the affected
  reducer output INDETERMINATE and fences achieved closure.
```

The Rust single writer allocates one globally unique `event_sequence` per Event.
Recovery finding two distinct Events at one sequence is corruption, not a
tie-break opportunity.

### 2.3 Authority validation

Authority is checked as of the decision Event and against the exact criterion
revision:

```text
JENN -> authenticated Jenn actor and criterion decision_authority JENN
NOBAO -> authenticated Nobao actor and criterion decision_authority NOBAO
RUST_POLICY -> exact accepted policy ID and revision named by the criterion,
  deterministic input contract available, and policy not revoked
```

An authority change creates a new criterion revision. It never retroactively
makes an old Event valid for a new revision.

### 2.4 Evidence currentness

```yaml
EvidenceCurrentnessSnapshot:
  snapshot_contract_version: criterion-evidence-currentness.v0.1
  evidence_items:
    - evidence_ref:
      owner_contract_id:
      owner_contract_revision:
      owner_fact_revision:
      currentness: CURRENT | STALE | INDETERMINATE | TIMELESS
      assessed_at_event_sequence:
  snapshot_fingerprint: FingerprintEnvelope
```

Each evidence owner contract decides its own currentness. `TIMELESS` is allowed
only when that contract explicitly declares immutable evidence reusable across
time. Missing owner contract, unknown version, inaccessible required evidence,
`STALE`, conflicting evidence, or `INDETERMINATE` makes the criterion result
`INDETERMINATE`. A model assertion cannot declare evidence current.

When an evidence owner's current canonical revision changes after the decision,
Rust recomputes currentness. The old Event remains history, but it loses current
closure authority unless the owner contract proves compatibility.

### 2.5 Carry-forward

There is no implicit carry-forward. `CARRY_FORWARD` requires:

```text
same stable criterion_id
new criterion_revision and Goal spec revision are current
criterion_summary semantic fingerprint unchanged
evaluation_mode unchanged
decision_authority unchanged
evidence_expectation_refs unchanged
deterministic_policy_ref unchanged when applicable
source decision is the valid current head of the immediately preceding
  criterion revision
new actor or policy has current authority
new EvidenceCurrentnessSnapshot is CURRENT or entirely TIMELESS
```

Any failed condition rejects carry-forward and yields no current decision for
the new tuple.

### 2.6 Total reduction

For the exact tuple, reduction is deterministic:

```text
no valid head
  -> INDETERMINATE + CURRENT_REQUIRED_FACT_MISSING

one valid head with decision UNSATISFIED
  -> UNSATISFIED

one valid head with decision INDETERMINATE or REVOKE
  -> INDETERMINATE

one valid SATISFIED head and all required evidence CURRENT or TIMELESS
  -> SATISFIED

invalid chain, unknown reducer version, authority conflict, evidence conflict,
or corrupted Event order
  -> INDETERMINATE + CANONICAL_FACT_RECONCILIATION_REQUIRED
```

Every possible ledger state therefore has one fail-closed output.

### 2.7 Closure binding

R1 `GoalClosureBasis` additionally requires:

```yaml
criterion_decision_reducer_version: success-criterion-decision-reducer.v0.1
criterion_decision_bindings:
  - criterion_id:
    criterion_revision:
    current_decision_event_id:
    current_decision_fingerprint:
    evidence_currentness_fingerprint:
    reducer_based_on_event_sequence:
```

Achieved closure rejects a null head, non-current evidence, unknown reducer,
or any result other than `SATISFIED`.

## 3. Parent alignment gate for Subgoals

This section replaces R1 Section 6.4's transition effect and adds mandatory
Subgoal gates to Sections 6.5, 13.1, 13.2, and 13.3.

### 3.1 Synchronous assessment

```yaml
SubgoalParentAlignmentAssessment:
  assessment_contract_version: subgoal-parent-alignment.v0.1
  subgoal_id:
  subgoal_spec_revision:
  parent_goal_id:
  bound_parent_goal_spec_revision:
  current_parent_goal_spec_revision:
  parent_criterion_bindings: []
  delegation_basis_ref:
  delegation_currentness: CURRENT | REVOKED | INDETERMINATE
  ancestry_fingerprint: FingerprintEnvelope
  assessment: CURRENT | REVIEW_REQUIRED | INDETERMINATE
  reason_codes: []
  based_on_event_sequence:
```

The synchronous gate reads the current parent spec, every bound parent
criterion revision, current delegation fact, and the full current Goal ancestry.
It rejects self-binding and cycles. Cached projection output is diagnostic only.

```text
all exact bindings current, delegation CURRENT, and ancestry acyclic
  -> CURRENT

parent or criterion revision advanced with a valid review path
  -> REVIEW_REQUIRED

missing fact, revoked delegation, unknown contract, cycle, or conflicting
ancestry
  -> INDETERMINATE
```

### 3.2 Lifecycle and closure gates

`READY`, `ACTIVE`, `COMPLETION_REVIEW`, and `CLOSED + ACHIEVED` require
`SubgoalParentAlignmentAssessment = CURRENT` in the same consistent read set.

While alignment is `REVIEW_REQUIRED` or `INDETERMINATE`:

```text
CLARIFYING and PAUSED remain allowed.
Nobao may close ABANDONED or SUPERSEDED with reason and current authority.
Nobao may not close ACHIEVED or UNACHIEVABLE.
Jenn may close any non-achieved outcome through explicit root authority, reason,
  and exact stale-binding disclosure.
```

Nobao ends the review condition only by a new Subgoal spec revision that binds
the exact current parent direction and passes the synchronous assessment. Merely
closing the Subgoal does not make alignment current.

### 3.3 Closure binding

Subgoal `GoalClosureBasis` additionally binds:

```yaml
parent_alignment:
  assessment_contract_version: subgoal-parent-alignment.v0.1
  parent_goal_id:
  parent_goal_spec_revision:
  parent_criterion_bindings: []
  delegation_basis_ref:
  delegation_fact_revision:
  ancestry_fingerprint:
  assessment: CURRENT | REVIEW_REQUIRED | INDETERMINATE
  based_on_event_sequence:
```

`ACHIEVED`, and `UNACHIEVABLE` when decided by Nobao, require the bound value
`CURRENT`. `ABANDONED` or `SUPERSEDED` while stale binds the actual non-current
assessment and the required stale-binding disclosure. Jenn's root-authority
non-achieved closure also binds the actual assessment; it never rewrites it to
`CURRENT`. Top-level Goals bind `parent_alignment: NOT_APPLICABLE`.

## 4. Fingerprint Canonicalization v0.1

This section replaces R1 Section 15's incomplete canonicalization rules.

### 4.1 Fingerprint envelope

Every F1 canonical fingerprint stored or bound for recovery is:

```yaml
FingerprintEnvelope:
  algorithm: SHA-256
  canonicalization_contract_version: f1-canonical-json.v0.1
  digest_lowercase_hex:
```

Unknown algorithm or canonicalization version fails closed. A bare digest is
not a valid F1 recovery fingerprint.

### 4.2 Scalar and object normalization

`f1-canonical-json.v0.1` uses RFC 8785 JSON Canonicalization Scheme, restricted
to integers and finite schema-defined values. Before JCS serialization:

```text
strings -> Unicode NFC; NUL and unpaired surrogate rejected
identifiers and enums -> exact case-sensitive schema value
timestamps -> represented only by integer UTC milliseconds or Event sequence
optional absent field -> omitted; explicit null only where schema permits null
object keys -> exact schema names; unknown keys rejected for canonical input
numbers -> signed or unsigned integers within the owning field range
float, NaN, Infinity, locale formatting, and insignificant whitespace -> rejected
```

The digest input is the entire normalized value excluding its own fingerprint
envelope.

### 4.3 Reference sort keys

Compound refs use these exact tuples, compared element by element as NFC UTF-8
byte strings for strings and ascending integers for revisions:

```text
Goal ref:                 (goal_id, goal_spec_revision)
Criterion ref:            (criterion_id, criterion_revision)
Plan ref:                 (plan_id, plan_revision)
Membership ref:           (membership_id, membership_revision)
Route ref:                (criterion_id, criterion_revision,
                           route_group_id, route_group_revision)
Frontier member ref:      (frontier_member_id, frontier_member_revision)
Decision ref:             (criterion_id, criterion_revision, event_sequence,
                           decision_event_id)
Evidence ref:             (owner_contract_id, owner_contract_revision,
                           owner_fact_revision, evidence_ref)
Challenge ref:            (challenge_ref)
Artifact or opaque ref:   (ref_type, ref_id, ref_revision_or_zero)
Task ref:                 (task_id)
Event ref:                (event_sequence, event_id)
```

Two values with the same declared unique tuple but different remaining bytes are
a conflict and are rejected; they are not deduplicated.

### 4.4 Array catalog

Arrays are semantic sets unless explicitly listed as semantic sequences:

| Field family | Semantics | Canonical order / rule |
|---|---|---|
| `in_scope`, `out_of_scope` | set | NFC UTF-8 byte lexical; exact duplicate reject |
| `constraint_refs`, `unresolved_question_refs`, `basis_refs`, `root_reason_refs` | set | opaque-ref tuple |
| `success_criterion_refs`, `parent_criterion_refs`, `criterion_bindings` | set | criterion-ref tuple |
| `evidence_expectation_refs`, `evidence_refs`, `replacement_evidence_refs` | set | evidence-ref tuple |
| `membership_refs`, `supplemental_plan_membership_refs`, all membership change sets | set | membership-ref tuple |
| `criterion_route_refs`, `selected_route_refs` | set | route-ref tuple |
| `frontier_member_refs` | set | frontier-member-ref tuple |
| `superseded_challenge_refs`, `open_challenge_refs` | set | challenge-ref tuple |
| `replaces_criterion_ids`, `task_ids`, `counting_task_ids` | set | NFC UTF-8 byte lexical ID |
| `replaced_membership_pairs` | set of ordered pairs | old membership tuple, then new membership tuple |
| `criterion_decision_refs`, `criterion_decision_bindings` | set | decision-ref tuple |
| `evidence_items` | set | evidence-ref tuple |
| `reason_codes` and other closed enum-code lists | set | NFC UTF-8 byte lexical enum value |
| `task_completion_refs` | set | `(task_id, completion_epoch, completion_ref_id)` |
| `completion_assurance_versions` | set | `(completion_ref_id, assurance_version, fence_generation)` |
| reducer Event input | sequence | strictly ascending unique global event_sequence |

Within `change_summary`, added, removed, carried-forward, and replaced arrays are
separate sets and must also satisfy the role-partition rules in Section 5.
Arrays introduced by a later F1 revision are rejected under
`f1-canonical-json.v0.1` until that revision declares their semantics and
advances the canonicalization contract version.

## 5. Total plan membership partition

This section replaces conflicting R1 Sections 8.1, 9.1, 9.5, 10.1, 10.2, and
12.1.

### 5.1 Revised roles

```text
SELECTED_CRITERION_ROUTE
UNSELECTED_ALTERNATIVE_ROUTE
SUPPLEMENTAL_PLAN_WORK
DECOMPOSITION_CONTAINER
```

`membership_refs` is the exact authoritative set of every current membership in
the plan snapshot. Each ref appears exactly once.

### 5.2 Role invariants

```text
SELECTED_CRITERION_ROUTE
  -> non-null criterion and route bindings
  -> bound route selected_for_current_plan = true
  -> exactly one TASK_PLAN_MEMBERSHIP frontier member points back to this exact
     membership ref
  -> membership is a plan-wide leaf

UNSELECTED_ALTERNATIVE_ROUTE
  -> non-null criterion and route bindings
  -> bound route selected_for_current_plan = false
  -> exactly one TASK_PLAN_MEMBERSHIP frontier member points back to this exact
     membership ref
  -> membership is a plan-wide leaf

SUPPLEMENTAL_PLAN_WORK
  -> null criterion and route bindings
  -> no frontier member points to it
  -> exact membership ref appears once in supplemental_plan_membership_refs
  -> membership is a plan-wide leaf

DECOMPOSITION_CONTAINER
  -> has at least one current child membership
  -> never appears as a frontier member or progress counting member
  -> if criterion route lineage, both bindings are non-null
  -> if supplemental lineage, both bindings are null and the exact ref appears
     once in supplemental_plan_membership_refs
```

No membership may satisfy more than one role. Every supplemental ref resolves
to a supplemental-lineage membership, and every supplemental-lineage membership
appears in the supplemental set. No route-bound membership appears there.

### 5.3 Bidirectional route coverage

For every `TASK_PLAN_MEMBERSHIP` frontier member, exactly one membership exists
with the same Goal, spec, plan, criterion, route, frontier member, and Task
bindings. For every selected or unselected leaf route membership, exactly one
frontier member points back.

`CURRENT_CRITERION_DECISION` members contain no membership ref. Direct-decision
routes contain exactly one such member and no Task member.

Orphan, duplicate, multiply classified, cross-route, or multiply referenced
memberships reject the entire plan revision transaction.

### 5.4 Plan-wide Task leaf reduction

Leaf/container classification is reduced across all current memberships with
the same `task_id` in one Goal plan:

```text
task_has_child = any current child membership names any membership of task_id

task_has_child = true
  -> every membership for task_id must be DECOMPOSITION_CONTAINER
  -> task_id is excluded from progress and route frontier support

task_has_child = false
  -> no membership for task_id may be DECOMPOSITION_CONTAINER
  -> each membership uses one of the three leaf roles
```

For one `task_id`, all non-null parent membership refs must resolve to the same
parent `task_id`; mixing null and non-null parentage or naming different parent
Tasks is rejected. Parent-child cycles are rejected after Task-level
normalization.

Children inherit the parent's exact criterion/route lineage or exact
supplemental lineage. A Task may have multiple leaf memberships in one Goal,
but all must agree that it is a leaf. Progress deduplicates by `task_id`; route
support still validates every exact membership ref.

## 6. Closed Goal amendment and reopen currentness

This section replaces ambiguity in R1 Sections 7.5, 13.4, 15, and 16.

### 6.1 Closed Goal immutability

While `goal_lifecycle = CLOSED`:

```text
ReviseGoalSpec rejected
ReviseGoalPlan rejected
RecordCriterionDecision rejected for current operational authority
historical evidence and challenge Events may still append without changing
  current spec, plan, lifecycle, outcome, or closure basis
```

A factual correction to historical metadata uses a typed correction Event that
points to the original fact. It never overwrites the fact or changes current
Goal meaning.

### 6.2 Explicit reopen

Top-level reopen authority is Jenn. Subgoal reopen authority is Nobao within a
current parent alignment, or Jenn.

One reopen transaction:

```text
binds the exact prior closure Event and immutable GoalClosureBasis
sets lifecycle to CLARIFYING, READY, or ACTIVE according to current completeness
and authority; sets outcome to null
appends a new GoalSpecRevision marked REOPEN_CARRY_FORWARD or REOPEN_REVISED
never reuses the closed revision as the new current revision
either appends an explicit new GoalPlanRevision or sets the current plan pointer
to null with reason
marks every prior criterion decision non-current for the new spec revision
preserves all prior challenges and closure history
sets achieved closure eligibility false
appends one reopen Event and updates Current State atomically
```

`REOPEN_CARRY_FORWARD` requires semantic fingerprint equality and current
authority but still advances the spec revision. Plan carry-forward similarly
creates a new plan and membership revision set; it never makes the old closed
plan current by pointer reuse.

New criterion decisions use Section 2, including explicit `CARRY_FORWARD` when
eligible. Prior closure evidence can be referenced as evidence, but it is not
automatically current proof for re-closure.

### 6.3 Re-closure

Re-closure uses only the new current spec, plan, memberships, reducer heads,
assurance versions, parent alignment when applicable, and a new closure basis.
The prior closure basis remains immutable historical provenance.

## 7. Findings disposition

| Finding | Disposition | R2 section |
|---|---|---|
| F1-IR-B01 | resolved by total versioned criterion decision reducer | 2 |
| F1-IR-B02 | resolved by synchronous Subgoal parent alignment gate | 3 |
| F1-IR-B03 | resolved by complete versioned fingerprint rules | 4 |
| F1-IR-M01 | resolved by total membership partition and bidirectional coverage | 5.1-5.3 |
| F1-IR-M02 | resolved by plan-wide Task leaf reduction | 5.4 |
| F1-IR-M03 | resolved by closed-Goal immutability and explicit reopen rebinding | 6 |
| F1-IR-N01 | resolved by replacement authority wording | 1 |

## 8. R2 acceptance unit

```yaml
acceptance_unit_id: F1_GOAL_SPECIFICATION_SUCCESS_CRITERIA_PLAN_MEMBERSHIP_V0_1_R2_ATOMIC_BUNDLE
subjects:
  - path: control-plane/registry/drafts/2026-07-14-agents-os-goal-specification-success-criteria-plan-membership-v0.1.draft.md
    sha256: 08dcc4cd2c6662e1f408cecb4f51107e50ad15e236b2ec965b898619324aecb8
  - path: control-plane/registry/drafts/2026-07-14-agents-os-f1-goal-spec-plan-membership-v0.1-r2-amendment.draft.md
    sha256: populated_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
new_hash_bound_independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
F2_start_by_acceptance: false
```
