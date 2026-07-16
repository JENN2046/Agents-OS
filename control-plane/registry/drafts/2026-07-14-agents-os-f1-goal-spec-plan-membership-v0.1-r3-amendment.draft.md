# AGENTS OS F1 Goal Specification / Plan Membership v0.1 R3 Amendment

```yaml
document_type: blocking_amendment
acceptance_unit_id: F1_GOAL_SPECIFICATION_SUCCESS_CRITERIA_PLAN_MEMBERSHIP_V0_1_R3_ATOMIC_BUNDLE
project: AGENTS OS
version: v0.1-r3
date: 2026-07-14
owner: Jenn
agent_steward: Nobao
status: proposed_final_draft
implementation_authorized: false
runtime_activation_authorized: false
```

## 1. Scope and composition

This amendment resolves only `F1-R2-IR-B01` and `F1-R2-IR-B02` from the fixed
R2 independent review.

```yaml
R1_subject_sha256: 08dcc4cd2c6662e1f408cecb4f51107e50ad15e236b2ec965b898619324aecb8
R2_amendment_sha256: 081732383e50773052503a07314d37982a9e1023759582e59a9ed4a3724617bb
R2_independent_review:
  path: control-plane/registry/reviews/2026-07-14-yellow-agents-os-f1-r2-atomic-bundle-independent-review.yaml
  sha256: b95d819a05366e1dd513e4afeb2b7b361118a4e1df2a7da47dbca2d494a23cf3
  result: BLOCK
```

The composed R3 contract is, in precedence order:

```text
R3 amendment
over R2 amendment
over R1 subject
```

Only clauses explicitly replaced here change. Historical subjects and reviews
remain unmodified.

## 2. Exact carry-forward predecessor

This section replaces R2 Sections 2.2 and 2.5 only where they define
`CARRY_FORWARD` source identity and eligibility.

### 2.1 Full source binding

Every `CARRY_FORWARD` Event must contain:

```yaml
SourceCriterionDecisionBinding:
  goal_id:
  goal_spec_revision:
  criterion_id:
  criterion_revision:
  current_decision_event_id:
  decision_reducer_contract_version: success-criterion-decision-reducer.v0.1
  current_decision_fingerprint: FingerprintEnvelope
  evidence_currentness_fingerprint: FingerprintEnvelope
  reducer_based_on_event_sequence:
```

The target Event also binds:

```yaml
target_goal_id:
target_goal_spec_revision:
target_criterion_id:
target_criterion_revision:
criterion_projection_contract_version: criterion-carry-forward-projection.v0.1
source_criterion_projection_fingerprint: FingerprintEnvelope
target_criterion_projection_fingerprint: FingerprintEnvelope
```

A source Event ID without this complete tuple is invalid for carry-forward.

### 2.2 One predecessor relation

For target tuple:

```text
T = (goal_id, target_goal_spec_revision, criterion_id,
     target_criterion_revision)
```

the only eligible source tuple is computed as follows:

```text
1. target_goal_spec_revision must be greater than 1.
2. Load the immediately preceding GoalSpecRevision in the same accepted lineage:
     source_goal_spec_revision = target_goal_spec_revision - 1.
3. That exact source spec must reference the same criterion_id.
4. Its referenced criterion_revision is source_criterion_revision.
5. source_criterion_revision must equal target_criterion_revision
   or target_criterion_revision - 1.
6. If it equals target_criterion_revision - 1, criterion revisions must be
   positive and consecutive.
7. The source tuple is exactly:
     (goal_id, source_goal_spec_revision, criterion_id,
      source_criterion_revision).
```

If the immediately preceding spec does not reference the criterion, if either
revision skips, if the Goal lineage differs, or if the criterion was retired and
later reintroduced, there is no eligible predecessor. The target requires a new
`DECIDE`; an older head cannot be carried across the gap.

This one relation covers:

```text
new GoalSpec revision with unchanged criterion revision
new GoalSpec revision with the criterion advanced by exactly one revision
reopen carry-forward into the immediately next GoalSpec revision
```

### 2.3 Exact latest head

The source binding must equal the valid current reducer head for the eligible
source tuple after consuming every applicable Event through
`reducer_based_on_event_sequence` and immediately before the target Event.

```text
source reducer version mismatch -> reject
source Event is not exact latest head -> reject
source fingerprint mismatch -> reject
source evidence currentness mismatch -> reject
source decision INDETERMINATE or revoked -> reject
branch, skip, or older eligible-looking Event -> reject
```

The target tuple must have no prior head. `prior_decision_event_id` remains null;
the source is named only by `SourceCriterionDecisionBinding`. The target
`CARRY_FORWARD` Event becomes the first head of the target tuple.

The carried decision value is exactly the source head's `SATISFIED` or
`UNSATISFIED` value. It cannot be changed by `CARRY_FORWARD`; changing the value
requires a new authoritative `DECIDE` for the target tuple instead.

## 3. Typed semantic projections

This section replaces every untyped use of `semantic fingerprint` in R2
Sections 2.5 and 6.2. Rust never decides natural-language semantic equivalence.

### 3.1 Common rule

Both projections use the R2 `FingerprintEnvelope` and
`f1-canonical-json.v0.1`. Equality means:

```text
same projection contract version
same SHA-256 algorithm
same exact lowercase digest
```

No fuzzy match, model judgment, embedding similarity, Unicode-insensitive
paraphrase, or author assertion is allowed. Any ambiguity fails closed.

### 3.2 CriterionCarryForwardProjection

```yaml
CriterionCarryForwardProjection:
  projection_contract_version: criterion-carry-forward-projection.v0.1
  included_fields:
    goal_id:
    criterion_id:
    criterion_summary:
    required:
    evaluation_mode:
    decision_authority:
    evidence_expectation_refs: []
    deterministic_policy_ref: null | ref
  fingerprint: FingerprintEnvelope
```

The projection excludes:

```text
goal_spec_revision
criterion_revision
created_by_actor_ref
created_at_event_sequence
authority_basis_ref
supersedes_criterion_revision
replaces_criterion_ids
the source value's canonical_fingerprint field
presentation metadata
```

Carry-forward requires exact source and target projection fingerprint equality.
Even a wording-only `criterion_summary` change makes the fingerprints different;
the authority must create a new decision rather than asking Rust to infer that
the meaning stayed the same.

### 3.3 GoalSpecReopenProjection

```yaml
GoalSpecReopenProjection:
  projection_contract_version: goal-spec-reopen-projection.v0.1
  included_fields:
    goal_id:
    goal_kind:
    parent_binding: null | ParentGoalBinding
    intent_summary:
    scope_summary:
    in_scope: []
    out_of_scope: []
    constraint_refs: []
    success_criterion_refs: []
    unresolved_question_refs: []
    completeness:
  fingerprint: FingerprintEnvelope
```

The projection excludes:

```text
goal_spec_revision
authority_basis_ref
created_by_actor_ref
created_at_event_sequence
supersedes_goal_spec_revision
the source value's canonical_fingerprint field
reopen Event provenance
presentation metadata
```

`REOPEN_CARRY_FORWARD` requires exact equality between the closed source spec
projection and the new target spec projection. The reopen Event binds:

```yaml
goal_spec_reopen_projection_contract_version: goal-spec-reopen-projection.v0.1
source_goal_spec_revision:
target_goal_spec_revision:
source_goal_spec_reopen_fingerprint: FingerprintEnvelope
target_goal_spec_reopen_fingerprint: FingerprintEnvelope
```

Any included-field change requires `REOPEN_REVISED`. `REOPEN_REVISED` then uses
the normal current authority rules and does not carry criterion decisions
automatically.

### 3.4 Replay and recovery

Recovery recomputes each projection from the exact bound revision value and
compares the full envelope. Unknown projection version, missing field, unknown
field in canonical input, digest mismatch, absent eligible predecessor, or
inconsistent source tuple fails closed to `INDETERMINATE` and prohibits achieved
closure. Recovery never substitutes a full-record fingerprint for either typed
projection.

## 4. Findings disposition

| Finding | Disposition | R3 section |
|---|---|---|
| F1-R2-IR-B01 / F1-IR-B01 | exact predecessor tuple, immediate lineage relation, and latest-head binding | 2 |
| F1-R2-IR-B02 / F1-IR-B03 | versioned typed field projections with exact digest equality | 3 |

The five findings already confirmed resolved by the R2 independent review stay
resolved and are not redesigned here.

## 5. R3 acceptance unit

```yaml
acceptance_unit_id: F1_GOAL_SPECIFICATION_SUCCESS_CRITERIA_PLAN_MEMBERSHIP_V0_1_R3_ATOMIC_BUNDLE
subjects:
  - path: control-plane/registry/drafts/2026-07-14-agents-os-goal-specification-success-criteria-plan-membership-v0.1.draft.md
    sha256: 08dcc4cd2c6662e1f408cecb4f51107e50ad15e236b2ec965b898619324aecb8
  - path: control-plane/registry/drafts/2026-07-14-agents-os-f1-goal-spec-plan-membership-v0.1-r2-amendment.draft.md
    sha256: 081732383e50773052503a07314d37982a9e1023759582e59a9ed4a3724617bb
  - path: control-plane/registry/drafts/2026-07-14-agents-os-f1-goal-spec-plan-membership-v0.1-r3-amendment.draft.md
    sha256: populated_after_author_closeout
partial_acceptance: forbidden
acceptance_authority: Jenn
fresh_hash_bound_independent_review_required: true
implementation_authority_by_acceptance: false
runtime_activation_authority_by_acceptance: false
F2_start_by_acceptance: false
```
