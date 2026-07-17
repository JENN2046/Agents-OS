# AGENTS OS F5 Outbox Delivery / Recovery v0.1 R6 Amendment

Date: 2026-07-17  
Status: fixed candidate for fresh full atomic hash-bound independent review  
Owner: Jenn  
Agent steward: Nobao

## 1. Atomic Scope And Precedence

R6 closes exactly
`F5_R5_BLOCKER_001_FIRST_APPLY_ELIGIBILITY_REDUCTION_REGRESSION`.

```text
R6 explicit replacement
→ R5 other explicit replacements
→ R4 other explicit replacements
→ R3 other explicit replacements
→ R2 other explicit replacements
→ R1 all other clauses
```

R1-R5 subjects, manifests and reviews remain immutable. R6 does not change
receipt replay, add a delivery state, receipt type, retry model, authority,
runtime path, provider protocol, implementation profile or F6 semantic.

## 2. First-Apply Eligibility Total Reducer

R6 restores and freezes the R4 first-apply guard.

After canonical request parsing, invocation binding, stored/submitted request
identity equality and replay-relation derivation:

```text
NO_EXISTING_ARM + ELIGIBLE_PROOF_PRECONDITION
  → result=APPLIED
  → primary_reason=ARMED_FIRST_APPLY
  → modeled_event_delta=1
  → modeled_call_authorization_delta=1
  → total_event_count=1
  → total_call_authorization_count=1

NO_EXISTING_ARM + NOT_ELIGIBLE
  → result=REJECTED
  → primary_reason=FIRST_APPLY_NOT_ELIGIBLE
  → modeled_event_delta=0
  → modeled_call_authorization_delta=0
  → total_event_count=0
  → total_call_authorization_count=0
```

No other relation may use `first_apply_eligibility` to alter its fixed replay
result. `EXACT_DUPLICATE`, `CHANGED_BYTES_SAME_IDENTITY` and
`LOOKUP_INDETERMINATE` preserve their R4/R5 outcomes and stored-first totals.

The eligibility value is raw input to the deterministic reducer. It is not an
authority level, Actor/Task classification, caller-provided result or evidence
that can independently authorize a call.

## 3. Required Re-Signed Counterexample

Starting from the eligible first-apply fixture row:

1. change only `first_apply_eligibility` to `NOT_ELIGIBLE`;
2. preserve derived `APPLIED / ARMED_FIRST_APPLY / 1 Event / 1 call`;
3. recompute the arm section and root fingerprints.

The R6 validator MUST reject. The fixed R5 reviewer rendered-counterexample
SHA-256 is:

```text
c797d18dc819ec2818f30bcddd583a14bedf80e8757925d97135ace5cfeef114
```

The inverse mutation—changing the fixed NOT_ELIGIBLE row to eligible while
preserving the rejected result—MUST also reject.

## 4. Fixed R6 Constructive Surface

```text
control-plane/registry/drafts/2026-07-17-agents-os-f5-outbox-delivery-recovery-v0.1-r6-amendment.draft.md
control-plane/registry/build-f5-r6-first-apply-eligibility-guard.py
control-plane/registry/examples/2026-07-17-agents-os-f5-r6-first-apply-eligibility-guard-v0.1.json
control-plane/registry/validate-f5-r6-first-apply-eligibility-guard.py
```

The fixture is synthetic, nonauthority, non-runtime-consumable and
non-recovery-importable. It models no accepted real handoff, claim Event,
armed dispatch, runtime action, external effect or provider call.

## 5. Acceptance Candidate Gate

```yaml
eligible_first_apply: APPLIED_ONE_EVENT_ONE_CALL
not_eligible_first_apply: REJECTED_ZERO_EVENT_ZERO_CALL
exact_R5_counterexample_rejected: true
inverse_eligibility_mutation_rejected: true
R1_R2_R3_R4_R5_validators_pass: true
R6_builder_fixture_byte_equal: true
fresh_full_atomic_review: PASS_NO_BLOCKER
```

`PASS_NO_BLOCKER` stops F5 revision and prepares a Jenn-only atomic freeze
decision surface. It does not itself accept or freeze F5.

## 6. Explicit Non-Authorization

R6 does not authorize F5 acceptance/freeze, F6, implementation, database,
runtime, production authentication, provider/service access, real handoff,
dispatch, physical effect, Git delivery, release, deployment, publication,
formal Memory or private raw memory access.
