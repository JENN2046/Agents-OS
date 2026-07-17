# AGENTS OS F5 Outbox Delivery and Recovery v0.1 R7 Amendment

Date: 2026-07-17  
Status: fixed subject candidate for fresh full atomic independent review  
Owner: Jenn  
Agent steward: Nobao

## 1. Scope and precedence

R7 replaces only the serialized integer-type validation rules for F5 count
fields. Effective precedence is:

```text
R7 explicit replacement
→ R6 other explicit replacements
→ R5 other explicit replacements
→ R4 other explicit replacements
→ R3 other explicit replacements
→ R2 other explicit replacements
→ R1 all other clauses
```

R7 does not change any receipt replay, arm identity, first-apply result,
accounting value, delivery state, transition, retry, provider or authority
semantic.

## 2. Exact JSON integer rule

Every Event, call-authorization and other count field MUST be validated before
its value is used by an equality, mapping, reducer, fingerprint trust decision
or fixed assertion.

The accepted value profile is:

```yaml
json_scalar_type: integer
boolean_is_integer: false
float_is_integer: false
minimum: 0
maximum: 9007199254740991
```

Equivalent implementation predicates MAY differ, but the result MUST equal:

```text
exact_integer(value)
= JSON type is integer
  AND JSON type is not boolean
  AND 0 <= value <= 9007199254740991
```

In Python proof code the exact predicate is `type(value) is int`; `isinstance`
alone is insufficient because `bool` is an `int` subclass.

## 3. Closed count inventory

For the R6 fixed witness, the R7 proof inventory contains exactly 37 count
occurrences:

```text
20  arm_guard_cases[*].derived Event/call delta and total fields
 6  stored_arm_state committed Event/call count fields
 7  assertions count fields
 4  summary count fields
--
37  total
```

Exactly 34 of those occurrences have a fixed value of zero or one. Every one
of the 37 occurrences MUST reject a fully re-signed boolean substitution.
This includes `false` substituted for zero, `true` substituted for one, and a
boolean substituted for any other integer count.

The closed patterns are:

```yaml
stored_arm_state:
  - committed_event_count
  - committed_call_authorization_count

derived:
  - modeled_event_delta
  - modeled_call_authorization_delta
  - total_event_count
  - total_call_authorization_count

assertions:
  - accepted_real_handoff_count
  - claim_event_count
  - armed_dispatch_count
  - runtime_consumable_count
  - external_effect_count
  - provider_call_count
  - raw_secret_count

summary:
  - arm_guard_case_count
  - first_apply_case_count
  - adversarial_case_count
  - real_effect_count
```

The canonical request-payload integers remain governed by the R4 exact
`safe_int` checks and are not replaced by this amendment.

## 4. Required derivation behavior

The R6 first-apply outputs remain exactly:

```text
NO_EXISTING_ARM + ELIGIBLE_PROOF_PRECONDITION
→ APPLIED / ARMED_FIRST_APPLY / 1 Event / 1 call

NO_EXISTING_ARM + NOT_ELIGIBLE
→ REJECTED / FIRST_APPLY_NOT_ELIGIBLE / 0 Event / 0 call
```

Exact replay, changed bytes and lookup-indeterminate behavior remain unchanged.
R7 changes only whether a serialized value is a well-typed input to those
already-fixed rules.

## 5. Mandatory negative proof

The R7 validator MUST:

1. discover the 37 count occurrences from the fixed R6 fixture;
2. require an exact path/value inventory match in the R7 fixture;
3. replace each occurrence individually with a JSON boolean;
4. recompute the affected section and root fingerprints;
5. reject all 37 fully re-signed instances before accepting any count
   equality or fixed mapping;
6. reproduce the R6 independent review's four-field mutation in
   `FIRST_APPLY_1_ELIGIBLE`, replacing all four derived count values with
   `true`, and reject it.

A digest match is not a substitute for exact scalar-type validation.

## 6. Boundary preservation

R7 is a synthetic, nonauthority proof overlay. It MUST remain:

```yaml
environment: SYNTHETIC_TEST
authority_eligible: false
runtime_consumable: false
recovery_importable: false
accepted_real_handoff_count: 0
claim_event_count: 0
armed_dispatch_count: 0
external_effect_count: 0
provider_call_count: 0
raw_secret_count: 0
terminal_outcome: NOT_EXECUTED
```

R7 does not create or recompute F1/F2/F3/F4 authority, classify any Actor or
Task, create a permission level, authorize a real handoff, or start F6.

## 7. Stop rule

Fresh full atomic review of R1-R7 is required. `PASS_NO_BLOCKER` stops F5
revision and prepares only a Jenn-owned freeze-decision surface. A later R8 is
not preplanned and requires a new independently reproducible security
counterexample. Implementation-profile questions do not trigger R8.

## 8. Non-authorization

This amendment authorizes no F5 acceptance/freeze, F6, implementation,
database, runtime activation, production authentication, provider/service,
real handoff/dispatch/effect, Git delivery, release, deployment, publication,
formal Memory or private raw memory access.
